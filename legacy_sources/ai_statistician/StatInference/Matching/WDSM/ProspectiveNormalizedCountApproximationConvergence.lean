import StatInference.Matching.WDSM.ProspectiveCountRatioConvergence
import StatInference.Matching.WDSM.ProspectiveCountApproximationConvergence
import StatInference.Matching.WDSM.ProspectiveNormalizedCountIndicatorBridge

/-!
# Prospective normalized-count approximation convergence for WDSM

This module composes the deterministic normalized-count ratio layer with the
prospective/common-weight approximation convergence layer.  Its hypotheses are
the natural fixed-cell LLN outputs: normalized cell counts, normalized sample
sizes, and the scaled differences of those normalized counts.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter
open scoped BigOperators

variable {Index Unit PropensityCell TreatedProgCell ControlProgCell PATTProgCell : Type*}
  [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
  [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]
variable {l : Filter Index}

theorem tendsto_pateDoubleScoreApprox_error_zero_of_normalized_counts_and_envelopes_constant_weight
    (targetSample treatedSample controlSample : Index -> Finset Unit)
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (targetCommonWeight treatedCommonWeight controlCommonWeight :
      Index -> Real)
    (targetNormalizer treatedNormalizer controlNormalizer : Index -> Real)
    (targetOutcomeT targetOutcomeC treatedOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (treatedValue : Index -> TreatedProgCell -> Real)
    (controlValue : Index -> ControlProgCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (treatedEnvelopeLimit controlEnvelopeLimit : Real)
    (cellLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (totalLimit : Real)
    (hweightTarget : ∀ index, targetCommonWeight index ≠ 0)
    (hweightTreated : ∀ index, treatedCommonWeight index ≠ 0)
    (hweightControl : ∀ index, controlCommonWeight index ≠ 0)
    (hnormalizerTarget : ∀ index, targetNormalizer index ≠ 0)
    (hnormalizerTreated : ∀ index, treatedNormalizer index ≠ 0)
    (hnormalizerControl : ∀ index, controlNormalizer index ≠ 0)
    (hnonemptyTarget : ∀ index, (targetSample index).Nonempty)
    (hnonemptyTreated : ∀ index, (treatedSample index).Nonempty)
    (hnonemptyControl : ∀ index, (controlSample index).Nonempty)
    (hcoverTarget :
      ∀ index unit, unit ∈ targetSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hcoverTreated :
      ∀ index unit, unit ∈ treatedSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hcoverControl :
      ∀ index unit, unit ∈ controlSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hmassTarget :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (targetSample index)
          (fun _unit => targetCommonWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassTreated :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (treatedSample index)
          (fun _unit => treatedCommonWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (controlSample index)
          (fun _unit => controlCommonWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hcellTarget :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            targetNormalizer index *
              (((targetSample index).filter
                (fun unit =>
                  pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real))
          l (nhds (cellLimit cell)))
    (hcellTreated :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            treatedNormalizer index *
              (((treatedSample index).filter
                (fun unit =>
                  pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real))
          l (nhds (cellLimit cell)))
    (hcellControl :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            controlNormalizer index *
              (((controlSample index).filter
                (fun unit =>
                  pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real))
          l (nhds (cellLimit cell)))
    (htotalTarget :
      Tendsto
        (fun index =>
          targetNormalizer index * ((targetSample index).card : Real))
        l (nhds totalLimit))
    (htotalTreated :
      Tendsto
        (fun index =>
          treatedNormalizer index * ((treatedSample index).card : Real))
        l (nhds totalLimit))
    (htotalControl :
      Tendsto
        (fun index =>
          controlNormalizer index * ((controlSample index).card : Real))
        l (nhds totalLimit))
    (htotalLimit : totalLimit ≠ 0)
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
      ∀ index cell, cell ∈ cells ->
        |treatedCellValueOnPATEDoubleScore (treatedValue index) cell| ≤
          treatedEnvelope index)
    (hcontrol_bound :
      ∀ index cell, cell ∈ cells ->
        |controlCellValueOnPATEDoubleScore (controlValue index) cell| ≤
          controlEnvelope index)
    (htreatedEnvelope :
      Tendsto treatedEnvelope l (nhds treatedEnvelopeLimit))
    (hcontrolEnvelope :
      Tendsto controlEnvelope l (nhds controlEnvelopeLimit)) :
    Tendsto
      (fun index =>
        weightedSampleMeanContrast (targetSample index)
          (fun _unit => targetCommonWeight index) (targetOutcomeT index)
          (targetOutcomeC index) -
        twoArmWeightedMeanContrast (treatedSample index)
          (controlSample index) (fun _unit => treatedCommonWeight index)
          (fun _unit => controlCommonWeight index) (treatedOutcome index)
          (controlOutcome index))
      l (nhds 0) := by
  have htargetTreated :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            (((targetSample index).filter
                  (fun unit =>
                    pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                Real) /
                ((targetSample index).card : Real) -
              (((treatedSample index).filter
                  (fun unit =>
                    pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                Real) /
                ((treatedSample index).card : Real))
          l (nhds 0) := by
    intro cell hmem
    exact
      tendsto_pateDoubleScore_card_ratio_sub_card_ratio_zero_of_normalized_common_limits
        targetNormalizer treatedNormalizer targetSample treatedSample
        propensityScore treatedPrognosticScore controlPrognosticScore cell
        (cellLimit cell) totalLimit hnormalizerTarget hnormalizerTreated
        (hcellTarget cell hmem) (hcellTreated cell hmem) htotalTarget
        htotalTreated htotalLimit
  have htargetControl :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            (((targetSample index).filter
                  (fun unit =>
                    pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                Real) /
                ((targetSample index).card : Real) -
              (((controlSample index).filter
                  (fun unit =>
                    pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                Real) /
                ((controlSample index).card : Real))
          l (nhds 0) := by
    intro cell hmem
    exact
      tendsto_pateDoubleScore_card_ratio_sub_card_ratio_zero_of_normalized_common_limits
        targetNormalizer controlNormalizer targetSample controlSample
        propensityScore treatedPrognosticScore controlPrognosticScore cell
        (cellLimit cell) totalLimit hnormalizerTarget hnormalizerControl
        (hcellTarget cell hmem) (hcellControl cell hmem) htotalTarget
        htotalControl htotalLimit
  exact
    tendsto_pateDoubleScoreApprox_error_zero_of_card_ratio_and_envelopes_constant_weight
      targetSample treatedSample controlSample cells targetCommonWeight
      treatedCommonWeight controlCommonWeight targetOutcomeT targetOutcomeC
      treatedOutcome controlOutcome propensityScore treatedPrognosticScore
      controlPrognosticScore treatedValue controlValue treatedEnvelope
      controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit hweightTarget
      hweightTreated hweightControl hnonemptyTarget hnonemptyTreated
      hnonemptyControl hcoverTarget hcoverTreated hcoverControl hmassTarget
      hmassTreated hmassControl htargetTreated htargetControl
      hscoreMeasTargetT hscoreMeasTreated hscoreMeasTargetC
      hscoreMeasControl htreated_bound hcontrol_bound htreatedEnvelope
      hcontrolEnvelope

theorem tendsto_scaled_pateDoubleScoreApprox_error_zero_of_normalized_counts_and_envelopes_constant_weight
    (scale : Index -> Real)
    (targetSample treatedSample controlSample : Index -> Finset Unit)
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (targetCommonWeight treatedCommonWeight controlCommonWeight :
      Index -> Real)
    (targetNormalizer treatedNormalizer controlNormalizer : Index -> Real)
    (targetOutcomeT targetOutcomeC treatedOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (treatedValue : Index -> TreatedProgCell -> Real)
    (controlValue : Index -> ControlProgCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (treatedEnvelopeLimit controlEnvelopeLimit : Real)
    (cellLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (totalLimit : Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hweightTarget : ∀ index, targetCommonWeight index ≠ 0)
    (hweightTreated : ∀ index, treatedCommonWeight index ≠ 0)
    (hweightControl : ∀ index, controlCommonWeight index ≠ 0)
    (hnormalizerTarget : ∀ index, targetNormalizer index ≠ 0)
    (hnormalizerTreated : ∀ index, treatedNormalizer index ≠ 0)
    (hnormalizerControl : ∀ index, controlNormalizer index ≠ 0)
    (hnonemptyTarget : ∀ index, (targetSample index).Nonempty)
    (hnonemptyTreated : ∀ index, (treatedSample index).Nonempty)
    (hnonemptyControl : ∀ index, (controlSample index).Nonempty)
    (hcoverTarget :
      ∀ index unit, unit ∈ targetSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hcoverTreated :
      ∀ index unit, unit ∈ treatedSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hcoverControl :
      ∀ index unit, unit ∈ controlSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hmassTarget :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (targetSample index)
          (fun _unit => targetCommonWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassTreated :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (treatedSample index)
          (fun _unit => treatedCommonWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (controlSample index)
          (fun _unit => controlCommonWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hcellTreated :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            treatedNormalizer index *
              (((treatedSample index).filter
                (fun unit =>
                  pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real))
          l (nhds (cellLimit cell)))
    (hcellControl :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            controlNormalizer index *
              (((controlSample index).filter
                (fun unit =>
                  pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real))
          l (nhds (cellLimit cell)))
    (htotalTarget :
      Tendsto
        (fun index =>
          targetNormalizer index * ((targetSample index).card : Real))
        l (nhds totalLimit))
    (htotalTreated :
      Tendsto
        (fun index =>
          treatedNormalizer index * ((treatedSample index).card : Real))
        l (nhds totalLimit))
    (htotalControl :
      Tendsto
        (fun index =>
          controlNormalizer index * ((controlSample index).card : Real))
        l (nhds totalLimit))
    (hscaledCellTreated :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (targetNormalizer index *
                  (((targetSample index).filter
                    (fun unit =>
                      pateDoubleScore (propensityScore index)
                        (treatedPrognosticScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                    Real) -
                treatedNormalizer index *
                  (((treatedSample index).filter
                    (fun unit =>
                      pateDoubleScore (propensityScore index)
                        (treatedPrognosticScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                    Real)))
          l (nhds 0))
    (hscaledCellControl :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (targetNormalizer index *
                  (((targetSample index).filter
                    (fun unit =>
                      pateDoubleScore (propensityScore index)
                        (treatedPrognosticScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                    Real) -
                controlNormalizer index *
                  (((controlSample index).filter
                    (fun unit =>
                      pateDoubleScore (propensityScore index)
                        (treatedPrognosticScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                    Real)))
          l (nhds 0))
    (hscaledTotalTreated :
      Tendsto
        (fun index =>
          scale index *
            (targetNormalizer index * ((targetSample index).card : Real) -
              treatedNormalizer index * ((treatedSample index).card : Real)))
        l (nhds 0))
    (hscaledTotalControl :
      Tendsto
        (fun index =>
          scale index *
            (targetNormalizer index * ((targetSample index).card : Real) -
              controlNormalizer index * ((controlSample index).card : Real)))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0)
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
      ∀ index cell, cell ∈ cells ->
        |treatedCellValueOnPATEDoubleScore (treatedValue index) cell| ≤
          treatedEnvelope index)
    (hcontrol_bound :
      ∀ index cell, cell ∈ cells ->
        |controlCellValueOnPATEDoubleScore (controlValue index) cell| ≤
          controlEnvelope index)
    (htreatedEnvelope :
      Tendsto treatedEnvelope l (nhds treatedEnvelopeLimit))
    (hcontrolEnvelope :
      Tendsto controlEnvelope l (nhds controlEnvelopeLimit)) :
    Tendsto
      (fun index =>
        scale index *
          (weightedSampleMeanContrast (targetSample index)
            (fun _unit => targetCommonWeight index) (targetOutcomeT index)
            (targetOutcomeC index) -
          twoArmWeightedMeanContrast (treatedSample index)
            (controlSample index) (fun _unit => treatedCommonWeight index)
            (fun _unit => controlCommonWeight index) (treatedOutcome index)
            (controlOutcome index)))
      l (nhds 0) := by
  have htargetTreated :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              ((((targetSample index).filter
                    (fun unit =>
                      pateDoubleScore (propensityScore index)
                        (treatedPrognosticScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                  Real) /
                  ((targetSample index).card : Real) -
                (((treatedSample index).filter
                    (fun unit =>
                      pateDoubleScore (propensityScore index)
                        (treatedPrognosticScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                  Real) /
                  ((treatedSample index).card : Real)))
          l (nhds 0) := by
    intro cell hmem
    exact
      tendsto_scaled_pateDoubleScore_card_ratio_sub_card_ratio_zero_of_normalized_common_limits
        scale targetNormalizer treatedNormalizer targetSample treatedSample
        propensityScore treatedPrognosticScore controlPrognosticScore cell
        (cellLimit cell) totalLimit hnormalizerTarget hnormalizerTreated
        (hcellTreated cell hmem) htotalTarget htotalTreated
        (hscaledCellTreated cell hmem) hscaledTotalTreated htotalLimit
  have htargetControl :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              ((((targetSample index).filter
                    (fun unit =>
                      pateDoubleScore (propensityScore index)
                        (treatedPrognosticScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                  Real) /
                  ((targetSample index).card : Real) -
                (((controlSample index).filter
                    (fun unit =>
                      pateDoubleScore (propensityScore index)
                        (treatedPrognosticScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                  Real) /
                  ((controlSample index).card : Real)))
          l (nhds 0) := by
    intro cell hmem
    exact
      tendsto_scaled_pateDoubleScore_card_ratio_sub_card_ratio_zero_of_normalized_common_limits
        scale targetNormalizer controlNormalizer targetSample controlSample
        propensityScore treatedPrognosticScore controlPrognosticScore cell
        (cellLimit cell) totalLimit hnormalizerTarget hnormalizerControl
        (hcellControl cell hmem) htotalTarget htotalControl
        (hscaledCellControl cell hmem) hscaledTotalControl htotalLimit
  exact
    tendsto_scaled_pateDoubleScoreApprox_error_zero_of_card_ratio_and_envelopes_constant_weight
      scale targetSample treatedSample controlSample cells targetCommonWeight
      treatedCommonWeight controlCommonWeight targetOutcomeT targetOutcomeC
      treatedOutcome controlOutcome propensityScore treatedPrognosticScore
      controlPrognosticScore treatedValue controlValue treatedEnvelope
      controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit
      hscale_nonneg hweightTarget hweightTreated hweightControl
      hnonemptyTarget hnonemptyTreated hnonemptyControl hcoverTarget
      hcoverTreated hcoverControl hmassTarget hmassTreated hmassControl
      htargetTreated htargetControl hscoreMeasTargetT hscoreMeasTreated
      hscoreMeasTargetC hscoreMeasControl htreated_bound hcontrol_bound
      htreatedEnvelope hcontrolEnvelope

theorem tendsto_scaled_pateDoubleScoreApprox_error_zero_of_indicator_sums_and_envelopes_constant_weight
    (scale : Index -> Real)
    (targetSample treatedSample controlSample : Index -> Finset Unit)
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (targetCommonWeight treatedCommonWeight controlCommonWeight :
      Index -> Real)
    (targetNormalizer treatedNormalizer controlNormalizer : Index -> Real)
    (targetOutcomeT targetOutcomeC treatedOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (treatedValue : Index -> TreatedProgCell -> Real)
    (controlValue : Index -> ControlProgCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (treatedEnvelopeLimit controlEnvelopeLimit : Real)
    (cellLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (totalLimit : Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hweightTarget : ∀ index, targetCommonWeight index ≠ 0)
    (hweightTreated : ∀ index, treatedCommonWeight index ≠ 0)
    (hweightControl : ∀ index, controlCommonWeight index ≠ 0)
    (hnormalizerTarget : ∀ index, targetNormalizer index ≠ 0)
    (hnormalizerTreated : ∀ index, treatedNormalizer index ≠ 0)
    (hnormalizerControl : ∀ index, controlNormalizer index ≠ 0)
    (hnonemptyTarget : ∀ index, (targetSample index).Nonempty)
    (hnonemptyTreated : ∀ index, (treatedSample index).Nonempty)
    (hnonemptyControl : ∀ index, (controlSample index).Nonempty)
    (hcoverTarget :
      ∀ index unit, unit ∈ targetSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hcoverTreated :
      ∀ index unit, unit ∈ treatedSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hcoverControl :
      ∀ index unit, unit ∈ controlSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hmassTarget :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (targetSample index)
          (fun _unit => targetCommonWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassTreated :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (treatedSample index)
          (fun _unit => treatedCommonWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (controlSample index)
          (fun _unit => controlCommonWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hcellTreatedIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (treatedSample index)
              (fun _unit => treatedNormalizer index)
              (scoreCellIndicator
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (cellLimit cell)))
    (hcellControlIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (controlSample index)
              (fun _unit => controlNormalizer index)
              (scoreCellIndicator
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (cellLimit cell)))
    (htotalTargetIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (targetSample index)
            (fun _unit => targetNormalizer index) (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalTreatedIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (treatedSample index)
            (fun _unit => treatedNormalizer index) (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalControlIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (controlSample index)
            (fun _unit => controlNormalizer index) (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (hscaledCellTreatedIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (targetSample index)
                  (fun _unit => targetNormalizer index)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index)) cell) -
                weightedSampleSum (treatedSample index)
                  (fun _unit => treatedNormalizer index)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index)) cell)))
          l (nhds 0))
    (hscaledCellControlIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (targetSample index)
                  (fun _unit => targetNormalizer index)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index)) cell) -
                weightedSampleSum (controlSample index)
                  (fun _unit => controlNormalizer index)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index)) cell)))
          l (nhds 0))
    (hscaledTotalTreatedIndicator :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (targetSample index)
                (fun _unit => targetNormalizer index)
                (fun _unit => (1 : Real)) -
              weightedSampleSum (treatedSample index)
                (fun _unit => treatedNormalizer index)
                (fun _unit => (1 : Real))))
        l (nhds 0))
    (hscaledTotalControlIndicator :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (targetSample index)
                (fun _unit => targetNormalizer index)
                (fun _unit => (1 : Real)) -
              weightedSampleSum (controlSample index)
                (fun _unit => controlNormalizer index)
                (fun _unit => (1 : Real))))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0)
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
      ∀ index cell, cell ∈ cells ->
        |treatedCellValueOnPATEDoubleScore (treatedValue index) cell| ≤
          treatedEnvelope index)
    (hcontrol_bound :
      ∀ index cell, cell ∈ cells ->
        |controlCellValueOnPATEDoubleScore (controlValue index) cell| ≤
          controlEnvelope index)
    (htreatedEnvelope :
      Tendsto treatedEnvelope l (nhds treatedEnvelopeLimit))
    (hcontrolEnvelope :
      Tendsto controlEnvelope l (nhds controlEnvelopeLimit)) :
    Tendsto
      (fun index =>
        scale index *
          (weightedSampleMeanContrast (targetSample index)
            (fun _unit => targetCommonWeight index) (targetOutcomeT index)
            (targetOutcomeC index) -
          twoArmWeightedMeanContrast (treatedSample index)
            (controlSample index) (fun _unit => treatedCommonWeight index)
            (fun _unit => controlCommonWeight index) (treatedOutcome index)
            (controlOutcome index)))
      l (nhds 0) :=
  tendsto_scaled_pateDoubleScoreApprox_error_zero_of_normalized_counts_and_envelopes_constant_weight
    scale targetSample treatedSample controlSample cells targetCommonWeight
    treatedCommonWeight controlCommonWeight targetNormalizer
    treatedNormalizer controlNormalizer targetOutcomeT targetOutcomeC
    treatedOutcome controlOutcome propensityScore treatedPrognosticScore
    controlPrognosticScore treatedValue controlValue treatedEnvelope
    controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit cellLimit
    totalLimit hscale_nonneg hweightTarget hweightTreated hweightControl
    hnormalizerTarget hnormalizerTreated hnormalizerControl
    hnonemptyTarget hnonemptyTreated hnonemptyControl hcoverTarget
    hcoverTreated hcoverControl hmassTarget hmassTreated hmassControl
    (tendsto_all_pate_normalized_cell_counts_of_tendsto_indicators_constant_weight
      treatedSample propensityScore treatedPrognosticScore
      controlPrognosticScore cells treatedNormalizer cellLimit
      hcellTreatedIndicator)
    (tendsto_all_pate_normalized_cell_counts_of_tendsto_indicators_constant_weight
      controlSample propensityScore treatedPrognosticScore
      controlPrognosticScore cells controlNormalizer cellLimit
      hcellControlIndicator)
    (tendsto_normalized_total_count_of_tendsto_weightedSampleSum_one_constant_weight
      targetSample targetNormalizer totalLimit htotalTargetIndicator)
    (tendsto_normalized_total_count_of_tendsto_weightedSampleSum_one_constant_weight
      treatedSample treatedNormalizer totalLimit htotalTreatedIndicator)
    (tendsto_normalized_total_count_of_tendsto_weightedSampleSum_one_constant_weight
      controlSample controlNormalizer totalLimit htotalControlIndicator)
    (tendsto_all_scaled_pate_normalized_cell_count_differences_of_tendsto_indicator_differences_constant_weight
      scale targetSample treatedSample propensityScore treatedPrognosticScore
      controlPrognosticScore cells targetNormalizer treatedNormalizer
      (fun _cell => (0 : Real)) hscaledCellTreatedIndicator)
    (tendsto_all_scaled_pate_normalized_cell_count_differences_of_tendsto_indicator_differences_constant_weight
      scale targetSample controlSample propensityScore treatedPrognosticScore
      controlPrognosticScore cells targetNormalizer controlNormalizer
      (fun _cell => (0 : Real)) hscaledCellControlIndicator)
    (tendsto_scaled_normalized_total_count_difference_of_tendsto_scaled_weightedSampleSum_one_difference_constant_weight
      scale targetSample treatedSample targetNormalizer treatedNormalizer
      (0 : Real) hscaledTotalTreatedIndicator)
    (tendsto_scaled_normalized_total_count_difference_of_tendsto_scaled_weightedSampleSum_one_difference_constant_weight
      scale targetSample controlSample targetNormalizer controlNormalizer
      (0 : Real) hscaledTotalControlIndicator)
    htotalLimit hscoreMeasTargetT hscoreMeasTreated hscoreMeasTargetC
    hscoreMeasControl htreated_bound hcontrol_bound htreatedEnvelope
    hcontrolEnvelope

theorem tendsto_pattDoubleScoreApprox_error_zero_of_normalized_counts_and_envelope_constant_weight
    (targetSample controlSample : Index -> Finset Unit)
    (cells : Finset (PropensityCell × PATTProgCell))
    (targetCommonWeight controlCommonWeight : Index -> Real)
    (targetNormalizer controlNormalizer : Index -> Real)
    (treatedTargetOutcome targetControlOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (controlValue : Index -> PATTProgCell -> Real)
    (controlEnvelope : Index -> Real)
    (controlEnvelopeLimit : Real)
    (cellLimit : PropensityCell × PATTProgCell -> Real)
    (totalLimit : Real)
    (hweightTarget : ∀ index, targetCommonWeight index ≠ 0)
    (hweightControl : ∀ index, controlCommonWeight index ≠ 0)
    (hnormalizerTarget : ∀ index, targetNormalizer index ≠ 0)
    (hnormalizerControl : ∀ index, controlNormalizer index ≠ 0)
    (hnonemptyTarget : ∀ index, (targetSample index).Nonempty)
    (hnonemptyControl : ∀ index, (controlSample index).Nonempty)
    (hcoverTarget :
      ∀ index unit, unit ∈ targetSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hcoverControl :
      ∀ index unit, unit ∈ controlSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hmassTarget :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (targetSample index)
          (fun _unit => targetCommonWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (controlSample index)
          (fun _unit => controlCommonWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hcellTarget :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            targetNormalizer index *
              (((targetSample index).filter
                (fun unit =>
                  pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real))
          l (nhds (cellLimit cell)))
    (hcellControl :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            controlNormalizer index *
              (((controlSample index).filter
                (fun unit =>
                  pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real))
          l (nhds (cellLimit cell)))
    (htotalTarget :
      Tendsto
        (fun index =>
          targetNormalizer index * ((targetSample index).card : Real))
        l (nhds totalLimit))
    (htotalControl :
      Tendsto
        (fun index =>
          controlNormalizer index * ((controlSample index).card : Real))
        l (nhds totalLimit))
    (htotalLimit : totalLimit ≠ 0)
    (hscoreMeasTargetC :
      ∀ index unit, unit ∈ targetSample index ->
        targetControlOutcome index unit =
          controlValue index (controlPrognosticScore index unit))
    (hscoreMeasControl :
      ∀ index unit, unit ∈ controlSample index ->
        controlOutcome index unit =
          controlValue index (controlPrognosticScore index unit))
    (hcontrol_bound :
      ∀ index cell, cell ∈ cells ->
        |controlCellValueOnPATTDoubleScore (controlValue index) cell| ≤
          controlEnvelope index)
    (hcontrolEnvelope :
      Tendsto controlEnvelope l (nhds controlEnvelopeLimit)) :
    Tendsto
      (fun index =>
        weightedSampleMeanContrast (targetSample index)
          (fun _unit => targetCommonWeight index)
          (treatedTargetOutcome index) (targetControlOutcome index) -
        pattWeightedMeanContrast (targetSample index) (controlSample index)
          (fun _unit => targetCommonWeight index)
          (fun _unit => controlCommonWeight index)
          (treatedTargetOutcome index) (controlOutcome index))
      l (nhds 0) := by
  have htargetControl :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            (((targetSample index).filter
                  (fun unit =>
                    pattDoubleScore (propensityScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                Real) /
                ((targetSample index).card : Real) -
              (((controlSample index).filter
                  (fun unit =>
                    pattDoubleScore (propensityScore index)
                      (controlPrognosticScore index) unit = cell)).card :
                Real) /
                ((controlSample index).card : Real))
          l (nhds 0) := by
    intro cell hmem
    exact
      tendsto_pattDoubleScore_card_ratio_sub_card_ratio_zero_of_normalized_common_limits
        targetNormalizer controlNormalizer targetSample controlSample
        propensityScore controlPrognosticScore cell (cellLimit cell)
        totalLimit hnormalizerTarget hnormalizerControl
        (hcellTarget cell hmem) (hcellControl cell hmem) htotalTarget
        htotalControl htotalLimit
  exact
    tendsto_pattDoubleScoreApprox_error_zero_of_card_ratio_and_envelope_constant_weight
      targetSample controlSample cells targetCommonWeight controlCommonWeight
      treatedTargetOutcome targetControlOutcome controlOutcome
      propensityScore controlPrognosticScore controlValue controlEnvelope
      controlEnvelopeLimit hweightTarget hweightControl hnonemptyTarget
      hnonemptyControl hcoverTarget hcoverControl hmassTarget hmassControl
      htargetControl hscoreMeasTargetC hscoreMeasControl hcontrol_bound
      hcontrolEnvelope

theorem tendsto_scaled_pattDoubleScoreApprox_error_zero_of_normalized_counts_and_envelope_constant_weight
    (scale : Index -> Real)
    (targetSample controlSample : Index -> Finset Unit)
    (cells : Finset (PropensityCell × PATTProgCell))
    (targetCommonWeight controlCommonWeight : Index -> Real)
    (targetNormalizer controlNormalizer : Index -> Real)
    (treatedTargetOutcome targetControlOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (controlValue : Index -> PATTProgCell -> Real)
    (controlEnvelope : Index -> Real)
    (controlEnvelopeLimit : Real)
    (cellLimit : PropensityCell × PATTProgCell -> Real)
    (totalLimit : Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hweightTarget : ∀ index, targetCommonWeight index ≠ 0)
    (hweightControl : ∀ index, controlCommonWeight index ≠ 0)
    (hnormalizerTarget : ∀ index, targetNormalizer index ≠ 0)
    (hnormalizerControl : ∀ index, controlNormalizer index ≠ 0)
    (hnonemptyTarget : ∀ index, (targetSample index).Nonempty)
    (hnonemptyControl : ∀ index, (controlSample index).Nonempty)
    (hcoverTarget :
      ∀ index unit, unit ∈ targetSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hcoverControl :
      ∀ index unit, unit ∈ controlSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hmassTarget :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (targetSample index)
          (fun _unit => targetCommonWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (controlSample index)
          (fun _unit => controlCommonWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hcellControl :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            controlNormalizer index *
              (((controlSample index).filter
                (fun unit =>
                  pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real))
          l (nhds (cellLimit cell)))
    (htotalTarget :
      Tendsto
        (fun index =>
          targetNormalizer index * ((targetSample index).card : Real))
        l (nhds totalLimit))
    (htotalControl :
      Tendsto
        (fun index =>
          controlNormalizer index * ((controlSample index).card : Real))
        l (nhds totalLimit))
    (hscaledCellControl :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (targetNormalizer index *
                  (((targetSample index).filter
                    (fun unit =>
                      pattDoubleScore (propensityScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                    Real) -
                controlNormalizer index *
                  (((controlSample index).filter
                    (fun unit =>
                      pattDoubleScore (propensityScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                    Real)))
          l (nhds 0))
    (hscaledTotalControl :
      Tendsto
        (fun index =>
          scale index *
            (targetNormalizer index * ((targetSample index).card : Real) -
              controlNormalizer index * ((controlSample index).card : Real)))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0)
    (hscoreMeasTargetC :
      ∀ index unit, unit ∈ targetSample index ->
        targetControlOutcome index unit =
          controlValue index (controlPrognosticScore index unit))
    (hscoreMeasControl :
      ∀ index unit, unit ∈ controlSample index ->
        controlOutcome index unit =
          controlValue index (controlPrognosticScore index unit))
    (hcontrol_bound :
      ∀ index cell, cell ∈ cells ->
        |controlCellValueOnPATTDoubleScore (controlValue index) cell| ≤
          controlEnvelope index)
    (hcontrolEnvelope :
      Tendsto controlEnvelope l (nhds controlEnvelopeLimit)) :
    Tendsto
      (fun index =>
        scale index *
          (weightedSampleMeanContrast (targetSample index)
            (fun _unit => targetCommonWeight index)
            (treatedTargetOutcome index) (targetControlOutcome index) -
          pattWeightedMeanContrast (targetSample index) (controlSample index)
            (fun _unit => targetCommonWeight index)
            (fun _unit => controlCommonWeight index)
            (treatedTargetOutcome index) (controlOutcome index)))
      l (nhds 0) := by
  have htargetControl :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              ((((targetSample index).filter
                    (fun unit =>
                      pattDoubleScore (propensityScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                  Real) /
                  ((targetSample index).card : Real) -
                (((controlSample index).filter
                    (fun unit =>
                      pattDoubleScore (propensityScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                  Real) /
                  ((controlSample index).card : Real)))
          l (nhds 0) := by
    intro cell hmem
    exact
      tendsto_scaled_pattDoubleScore_card_ratio_sub_card_ratio_zero_of_normalized_common_limits
        scale targetNormalizer controlNormalizer targetSample controlSample
        propensityScore controlPrognosticScore cell (cellLimit cell)
        totalLimit hnormalizerTarget hnormalizerControl
        (hcellControl cell hmem) htotalTarget htotalControl
        (hscaledCellControl cell hmem) hscaledTotalControl htotalLimit
  exact
    tendsto_scaled_pattDoubleScoreApprox_error_zero_of_card_ratio_and_envelope_constant_weight
      scale targetSample controlSample cells targetCommonWeight
      controlCommonWeight treatedTargetOutcome targetControlOutcome
      controlOutcome propensityScore controlPrognosticScore controlValue
      controlEnvelope controlEnvelopeLimit hscale_nonneg hweightTarget
      hweightControl hnonemptyTarget hnonemptyControl hcoverTarget
      hcoverControl hmassTarget hmassControl htargetControl
      hscoreMeasTargetC hscoreMeasControl hcontrol_bound hcontrolEnvelope

/--
PATE approximation convergence at ordinary and scaled rates from normalized
cell-count LLNs, normalized sample-size LLNs, and scaled normalized-count
differences.
-/
theorem tendsto_pateDoubleScoreApprox_error_zero_and_scaled_zero_of_normalized_counts_and_envelopes_constant_weight
    (scale : Index -> Real)
    (targetSample treatedSample controlSample : Index -> Finset Unit)
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (targetCommonWeight treatedCommonWeight controlCommonWeight :
      Index -> Real)
    (targetNormalizer treatedNormalizer controlNormalizer : Index -> Real)
    (targetOutcomeT targetOutcomeC treatedOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (treatedValue : Index -> TreatedProgCell -> Real)
    (controlValue : Index -> ControlProgCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (treatedEnvelopeLimit controlEnvelopeLimit : Real)
    (cellLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (totalLimit : Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hweightTarget : ∀ index, targetCommonWeight index ≠ 0)
    (hweightTreated : ∀ index, treatedCommonWeight index ≠ 0)
    (hweightControl : ∀ index, controlCommonWeight index ≠ 0)
    (hnormalizerTarget : ∀ index, targetNormalizer index ≠ 0)
    (hnormalizerTreated : ∀ index, treatedNormalizer index ≠ 0)
    (hnormalizerControl : ∀ index, controlNormalizer index ≠ 0)
    (hnonemptyTarget : ∀ index, (targetSample index).Nonempty)
    (hnonemptyTreated : ∀ index, (treatedSample index).Nonempty)
    (hnonemptyControl : ∀ index, (controlSample index).Nonempty)
    (hcoverTarget :
      ∀ index unit, unit ∈ targetSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hcoverTreated :
      ∀ index unit, unit ∈ treatedSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hcoverControl :
      ∀ index unit, unit ∈ controlSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hmassTarget :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (targetSample index)
          (fun _unit => targetCommonWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassTreated :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (treatedSample index)
          (fun _unit => treatedCommonWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (controlSample index)
          (fun _unit => controlCommonWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hcellTarget :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            targetNormalizer index *
              (((targetSample index).filter
                (fun unit =>
                  pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real))
          l (nhds (cellLimit cell)))
    (hcellTreated :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            treatedNormalizer index *
              (((treatedSample index).filter
                (fun unit =>
                  pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real))
          l (nhds (cellLimit cell)))
    (hcellControl :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            controlNormalizer index *
              (((controlSample index).filter
                (fun unit =>
                  pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real))
          l (nhds (cellLimit cell)))
    (htotalTarget :
      Tendsto
        (fun index =>
          targetNormalizer index * ((targetSample index).card : Real))
        l (nhds totalLimit))
    (htotalTreated :
      Tendsto
        (fun index =>
          treatedNormalizer index * ((treatedSample index).card : Real))
        l (nhds totalLimit))
    (htotalControl :
      Tendsto
        (fun index =>
          controlNormalizer index * ((controlSample index).card : Real))
        l (nhds totalLimit))
    (hscaledCellTreated :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (targetNormalizer index *
                  (((targetSample index).filter
                    (fun unit =>
                      pateDoubleScore (propensityScore index)
                        (treatedPrognosticScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                    Real) -
                treatedNormalizer index *
                  (((treatedSample index).filter
                    (fun unit =>
                      pateDoubleScore (propensityScore index)
                        (treatedPrognosticScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                    Real)))
          l (nhds 0))
    (hscaledCellControl :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (targetNormalizer index *
                  (((targetSample index).filter
                    (fun unit =>
                      pateDoubleScore (propensityScore index)
                        (treatedPrognosticScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                    Real) -
                controlNormalizer index *
                  (((controlSample index).filter
                    (fun unit =>
                      pateDoubleScore (propensityScore index)
                        (treatedPrognosticScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                    Real)))
          l (nhds 0))
    (hscaledTotalTreated :
      Tendsto
        (fun index =>
          scale index *
            (targetNormalizer index * ((targetSample index).card : Real) -
              treatedNormalizer index * ((treatedSample index).card : Real)))
        l (nhds 0))
    (hscaledTotalControl :
      Tendsto
        (fun index =>
          scale index *
            (targetNormalizer index * ((targetSample index).card : Real) -
              controlNormalizer index * ((controlSample index).card : Real)))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0)
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
      ∀ index cell, cell ∈ cells ->
        |treatedCellValueOnPATEDoubleScore (treatedValue index) cell| ≤
          treatedEnvelope index)
    (hcontrol_bound :
      ∀ index cell, cell ∈ cells ->
        |controlCellValueOnPATEDoubleScore (controlValue index) cell| ≤
          controlEnvelope index)
    (htreatedEnvelope :
      Tendsto treatedEnvelope l (nhds treatedEnvelopeLimit))
    (hcontrolEnvelope :
      Tendsto controlEnvelope l (nhds controlEnvelopeLimit)) :
    Tendsto
        (fun index =>
          weightedSampleMeanContrast (targetSample index)
            (fun _unit => targetCommonWeight index) (targetOutcomeT index)
            (targetOutcomeC index) -
          twoArmWeightedMeanContrast (treatedSample index)
            (controlSample index) (fun _unit => treatedCommonWeight index)
            (fun _unit => controlCommonWeight index) (treatedOutcome index)
            (controlOutcome index))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleMeanContrast (targetSample index)
              (fun _unit => targetCommonWeight index) (targetOutcomeT index)
              (targetOutcomeC index) -
            twoArmWeightedMeanContrast (treatedSample index)
              (controlSample index) (fun _unit => treatedCommonWeight index)
              (fun _unit => controlCommonWeight index) (treatedOutcome index)
              (controlOutcome index)))
        l (nhds 0) := by
  constructor
  · exact
      tendsto_pateDoubleScoreApprox_error_zero_of_normalized_counts_and_envelopes_constant_weight
        targetSample treatedSample controlSample cells targetCommonWeight
        treatedCommonWeight controlCommonWeight targetNormalizer
        treatedNormalizer controlNormalizer targetOutcomeT targetOutcomeC
        treatedOutcome controlOutcome propensityScore treatedPrognosticScore
        controlPrognosticScore treatedValue controlValue treatedEnvelope
        controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit cellLimit
        totalLimit hweightTarget hweightTreated hweightControl
        hnormalizerTarget hnormalizerTreated hnormalizerControl
        hnonemptyTarget hnonemptyTreated hnonemptyControl hcoverTarget
        hcoverTreated hcoverControl hmassTarget hmassTreated hmassControl
        hcellTarget hcellTreated hcellControl htotalTarget htotalTreated
        htotalControl htotalLimit hscoreMeasTargetT hscoreMeasTreated
        hscoreMeasTargetC hscoreMeasControl htreated_bound
        hcontrol_bound htreatedEnvelope hcontrolEnvelope
  · exact
      tendsto_scaled_pateDoubleScoreApprox_error_zero_of_normalized_counts_and_envelopes_constant_weight
        scale targetSample treatedSample controlSample cells targetCommonWeight
        treatedCommonWeight controlCommonWeight targetNormalizer
        treatedNormalizer controlNormalizer targetOutcomeT targetOutcomeC
        treatedOutcome controlOutcome propensityScore treatedPrognosticScore
        controlPrognosticScore treatedValue controlValue treatedEnvelope
        controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit cellLimit
        totalLimit hscale_nonneg hweightTarget hweightTreated hweightControl
        hnormalizerTarget hnormalizerTreated hnormalizerControl
        hnonemptyTarget hnonemptyTreated hnonemptyControl hcoverTarget
        hcoverTreated hcoverControl hmassTarget hmassTreated hmassControl
        hcellTreated hcellControl htotalTarget htotalTreated htotalControl
        hscaledCellTreated hscaledCellControl hscaledTotalTreated
        hscaledTotalControl htotalLimit hscoreMeasTargetT
        hscoreMeasTreated hscoreMeasTargetC hscoreMeasControl
        htreated_bound hcontrol_bound htreatedEnvelope hcontrolEnvelope

/--
PATT approximation convergence at ordinary and scaled rates from normalized
cell-count LLNs, normalized sample-size LLNs, and scaled normalized-count
differences.
-/
theorem tendsto_pattDoubleScoreApprox_error_zero_and_scaled_zero_of_normalized_counts_and_envelope_constant_weight
    (scale : Index -> Real)
    (targetSample controlSample : Index -> Finset Unit)
    (cells : Finset (PropensityCell × PATTProgCell))
    (targetCommonWeight controlCommonWeight : Index -> Real)
    (targetNormalizer controlNormalizer : Index -> Real)
    (treatedTargetOutcome targetControlOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (controlValue : Index -> PATTProgCell -> Real)
    (controlEnvelope : Index -> Real)
    (controlEnvelopeLimit : Real)
    (cellLimit : PropensityCell × PATTProgCell -> Real)
    (totalLimit : Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hweightTarget : ∀ index, targetCommonWeight index ≠ 0)
    (hweightControl : ∀ index, controlCommonWeight index ≠ 0)
    (hnormalizerTarget : ∀ index, targetNormalizer index ≠ 0)
    (hnormalizerControl : ∀ index, controlNormalizer index ≠ 0)
    (hnonemptyTarget : ∀ index, (targetSample index).Nonempty)
    (hnonemptyControl : ∀ index, (controlSample index).Nonempty)
    (hcoverTarget :
      ∀ index unit, unit ∈ targetSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hcoverControl :
      ∀ index unit, unit ∈ controlSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hmassTarget :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (targetSample index)
          (fun _unit => targetCommonWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (controlSample index)
          (fun _unit => controlCommonWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hcellTarget :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            targetNormalizer index *
              (((targetSample index).filter
                (fun unit =>
                  pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real))
          l (nhds (cellLimit cell)))
    (hcellControl :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            controlNormalizer index *
              (((controlSample index).filter
                (fun unit =>
                  pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real))
          l (nhds (cellLimit cell)))
    (htotalTarget :
      Tendsto
        (fun index =>
          targetNormalizer index * ((targetSample index).card : Real))
        l (nhds totalLimit))
    (htotalControl :
      Tendsto
        (fun index =>
          controlNormalizer index * ((controlSample index).card : Real))
        l (nhds totalLimit))
    (hscaledCellControl :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (targetNormalizer index *
                  (((targetSample index).filter
                    (fun unit =>
                      pattDoubleScore (propensityScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                    Real) -
                controlNormalizer index *
                  (((controlSample index).filter
                    (fun unit =>
                      pattDoubleScore (propensityScore index)
                        (controlPrognosticScore index) unit = cell)).card :
                    Real)))
          l (nhds 0))
    (hscaledTotalControl :
      Tendsto
        (fun index =>
          scale index *
            (targetNormalizer index * ((targetSample index).card : Real) -
              controlNormalizer index * ((controlSample index).card : Real)))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0)
    (hscoreMeasTargetC :
      ∀ index unit, unit ∈ targetSample index ->
        targetControlOutcome index unit =
          controlValue index (controlPrognosticScore index unit))
    (hscoreMeasControl :
      ∀ index unit, unit ∈ controlSample index ->
        controlOutcome index unit =
          controlValue index (controlPrognosticScore index unit))
    (hcontrol_bound :
      ∀ index cell, cell ∈ cells ->
        |controlCellValueOnPATTDoubleScore (controlValue index) cell| ≤
          controlEnvelope index)
    (hcontrolEnvelope :
      Tendsto controlEnvelope l (nhds controlEnvelopeLimit)) :
    Tendsto
        (fun index =>
          weightedSampleMeanContrast (targetSample index)
            (fun _unit => targetCommonWeight index)
            (treatedTargetOutcome index) (targetControlOutcome index) -
          pattWeightedMeanContrast (targetSample index) (controlSample index)
            (fun _unit => targetCommonWeight index)
            (fun _unit => controlCommonWeight index)
            (treatedTargetOutcome index) (controlOutcome index))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleMeanContrast (targetSample index)
              (fun _unit => targetCommonWeight index)
              (treatedTargetOutcome index) (targetControlOutcome index) -
            pattWeightedMeanContrast (targetSample index) (controlSample index)
              (fun _unit => targetCommonWeight index)
              (fun _unit => controlCommonWeight index)
              (treatedTargetOutcome index) (controlOutcome index)))
        l (nhds 0) := by
  constructor
  · exact
      tendsto_pattDoubleScoreApprox_error_zero_of_normalized_counts_and_envelope_constant_weight
        targetSample controlSample cells targetCommonWeight
        controlCommonWeight targetNormalizer controlNormalizer
        treatedTargetOutcome targetControlOutcome controlOutcome
        propensityScore controlPrognosticScore controlValue controlEnvelope
        controlEnvelopeLimit cellLimit totalLimit hweightTarget
        hweightControl hnormalizerTarget hnormalizerControl hnonemptyTarget
        hnonemptyControl hcoverTarget hcoverControl hmassTarget hmassControl
        hcellTarget hcellControl htotalTarget htotalControl htotalLimit
        hscoreMeasTargetC hscoreMeasControl hcontrol_bound hcontrolEnvelope
  · exact
      tendsto_scaled_pattDoubleScoreApprox_error_zero_of_normalized_counts_and_envelope_constant_weight
        scale targetSample controlSample cells targetCommonWeight
        controlCommonWeight targetNormalizer controlNormalizer
        treatedTargetOutcome targetControlOutcome controlOutcome
        propensityScore controlPrognosticScore controlValue controlEnvelope
        controlEnvelopeLimit cellLimit totalLimit hscale_nonneg hweightTarget
        hweightControl hnormalizerTarget hnormalizerControl hnonemptyTarget
        hnonemptyControl hcoverTarget hcoverControl hmassTarget hmassControl
        hcellControl htotalTarget htotalControl hscaledCellControl
        hscaledTotalControl htotalLimit hscoreMeasTargetC
        hscoreMeasControl hcontrol_bound hcontrolEnvelope

/--
Paired PATE/PATT approximation convergence at ordinary and scaled rates from
normalized cell-count LLNs, normalized sample-size LLNs, and scaled
normalized-count differences.
-/
theorem tendsto_pate_pattDoubleScoreApprox_error_zero_and_scaled_zero_of_normalized_counts_and_envelopes_constant_weight
    (scale : Index -> Real)
    (pateTargetSample pateTreatedSample pateControlSample :
      Index -> Finset Unit)
    (pattTargetSample pattControlSample : Index -> Finset Unit)
    (pateCells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (pattCells : Finset (PropensityCell × PATTProgCell))
    (pateTargetCommonWeight pateTreatedCommonWeight pateControlCommonWeight :
      Index -> Real)
    (pattTargetCommonWeight pattControlCommonWeight : Index -> Real)
    (pateTargetNormalizer pateTreatedNormalizer pateControlNormalizer :
      Index -> Real)
    (pattTargetNormalizer pattControlNormalizer : Index -> Real)
    (pateTargetOutcomeT pateTargetOutcomeC pateTreatedOutcome
      pateControlOutcome : Index -> Unit -> Real)
    (pattTreatedTargetOutcome pattTargetControlOutcome pattControlOutcome :
      Index -> Unit -> Real)
    (patePropensityScore pattPropensityScore :
      Index -> Unit -> PropensityCell)
    (pateTreatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (pateControlPrognosticScore : Index -> Unit -> ControlProgCell)
    (pattControlPrognosticScore : Index -> Unit -> PATTProgCell)
    (pateTreatedValue : Index -> TreatedProgCell -> Real)
    (pateControlValue : Index -> ControlProgCell -> Real)
    (pattControlValue : Index -> PATTProgCell -> Real)
    (pateTreatedEnvelope pateControlEnvelope pattControlEnvelope :
      Index -> Real)
    (pateTreatedEnvelopeLimit pateControlEnvelopeLimit
      pattControlEnvelopeLimit : Real)
    (pateCellLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (pattCellLimit : PropensityCell × PATTProgCell -> Real)
    (pateTotalLimit pattTotalLimit : Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hpateWeightTarget :
      ∀ index, pateTargetCommonWeight index ≠ 0)
    (hpateWeightTreated :
      ∀ index, pateTreatedCommonWeight index ≠ 0)
    (hpateWeightControl :
      ∀ index, pateControlCommonWeight index ≠ 0)
    (hpattWeightTarget :
      ∀ index, pattTargetCommonWeight index ≠ 0)
    (hpattWeightControl :
      ∀ index, pattControlCommonWeight index ≠ 0)
    (hpateNormalizerTarget :
      ∀ index, pateTargetNormalizer index ≠ 0)
    (hpateNormalizerTreated :
      ∀ index, pateTreatedNormalizer index ≠ 0)
    (hpateNormalizerControl :
      ∀ index, pateControlNormalizer index ≠ 0)
    (hpattNormalizerTarget :
      ∀ index, pattTargetNormalizer index ≠ 0)
    (hpattNormalizerControl :
      ∀ index, pattControlNormalizer index ≠ 0)
    (hpateNonemptyTarget :
      ∀ index, (pateTargetSample index).Nonempty)
    (hpateNonemptyTreated :
      ∀ index, (pateTreatedSample index).Nonempty)
    (hpateNonemptyControl :
      ∀ index, (pateControlSample index).Nonempty)
    (hpattNonemptyTarget :
      ∀ index, (pattTargetSample index).Nonempty)
    (hpattNonemptyControl :
      ∀ index, (pattControlSample index).Nonempty)
    (hpateCoverTarget :
      ∀ index unit, unit ∈ pateTargetSample index ->
        pateDoubleScore (patePropensityScore index)
          (pateTreatedPrognosticScore index)
          (pateControlPrognosticScore index) unit ∈ pateCells)
    (hpateCoverTreated :
      ∀ index unit, unit ∈ pateTreatedSample index ->
        pateDoubleScore (patePropensityScore index)
          (pateTreatedPrognosticScore index)
          (pateControlPrognosticScore index) unit ∈ pateCells)
    (hpateCoverControl :
      ∀ index unit, unit ∈ pateControlSample index ->
        pateDoubleScore (patePropensityScore index)
          (pateTreatedPrognosticScore index)
          (pateControlPrognosticScore index) unit ∈ pateCells)
    (hpattCoverTarget :
      ∀ index unit, unit ∈ pattTargetSample index ->
        pattDoubleScore (pattPropensityScore index)
          (pattControlPrognosticScore index) unit ∈ pattCells)
    (hpattCoverControl :
      ∀ index unit, unit ∈ pattControlSample index ->
        pattDoubleScore (pattPropensityScore index)
          (pattControlPrognosticScore index) unit ∈ pattCells)
    (hpateMassTarget :
      ∀ index cell, cell ∈ pateCells ->
        scoreCellMass (pateTargetSample index)
          (fun _unit => pateTargetCommonWeight index)
          (pateDoubleScore (patePropensityScore index)
            (pateTreatedPrognosticScore index)
            (pateControlPrognosticScore index)) cell ≠ 0)
    (hpateMassTreated :
      ∀ index cell, cell ∈ pateCells ->
        scoreCellMass (pateTreatedSample index)
          (fun _unit => pateTreatedCommonWeight index)
          (pateDoubleScore (patePropensityScore index)
            (pateTreatedPrognosticScore index)
            (pateControlPrognosticScore index)) cell ≠ 0)
    (hpateMassControl :
      ∀ index cell, cell ∈ pateCells ->
        scoreCellMass (pateControlSample index)
          (fun _unit => pateControlCommonWeight index)
          (pateDoubleScore (patePropensityScore index)
            (pateTreatedPrognosticScore index)
            (pateControlPrognosticScore index)) cell ≠ 0)
    (hpattMassTarget :
      ∀ index cell, cell ∈ pattCells ->
        scoreCellMass (pattTargetSample index)
          (fun _unit => pattTargetCommonWeight index)
          (pattDoubleScore (pattPropensityScore index)
            (pattControlPrognosticScore index)) cell ≠ 0)
    (hpattMassControl :
      ∀ index cell, cell ∈ pattCells ->
        scoreCellMass (pattControlSample index)
          (fun _unit => pattControlCommonWeight index)
          (pattDoubleScore (pattPropensityScore index)
            (pattControlPrognosticScore index)) cell ≠ 0)
    (hpateCellTarget :
      ∀ cell, cell ∈ pateCells ->
        Tendsto
          (fun index =>
            pateTargetNormalizer index *
              (((pateTargetSample index).filter
                (fun unit =>
                  pateDoubleScore (patePropensityScore index)
                    (pateTreatedPrognosticScore index)
                    (pateControlPrognosticScore index) unit = cell)).card :
                Real))
          l (nhds (pateCellLimit cell)))
    (hpateCellTreated :
      ∀ cell, cell ∈ pateCells ->
        Tendsto
          (fun index =>
            pateTreatedNormalizer index *
              (((pateTreatedSample index).filter
                (fun unit =>
                  pateDoubleScore (patePropensityScore index)
                    (pateTreatedPrognosticScore index)
                    (pateControlPrognosticScore index) unit = cell)).card :
                Real))
          l (nhds (pateCellLimit cell)))
    (hpateCellControl :
      ∀ cell, cell ∈ pateCells ->
        Tendsto
          (fun index =>
            pateControlNormalizer index *
              (((pateControlSample index).filter
                (fun unit =>
                  pateDoubleScore (patePropensityScore index)
                    (pateTreatedPrognosticScore index)
                    (pateControlPrognosticScore index) unit = cell)).card :
                Real))
          l (nhds (pateCellLimit cell)))
    (hpattCellTarget :
      ∀ cell, cell ∈ pattCells ->
        Tendsto
          (fun index =>
            pattTargetNormalizer index *
              (((pattTargetSample index).filter
                (fun unit =>
                  pattDoubleScore (pattPropensityScore index)
                    (pattControlPrognosticScore index) unit = cell)).card :
                Real))
          l (nhds (pattCellLimit cell)))
    (hpattCellControl :
      ∀ cell, cell ∈ pattCells ->
        Tendsto
          (fun index =>
            pattControlNormalizer index *
              (((pattControlSample index).filter
                (fun unit =>
                  pattDoubleScore (pattPropensityScore index)
                    (pattControlPrognosticScore index) unit = cell)).card :
                Real))
          l (nhds (pattCellLimit cell)))
    (hpateTotalTarget :
      Tendsto
        (fun index =>
          pateTargetNormalizer index * ((pateTargetSample index).card : Real))
        l (nhds pateTotalLimit))
    (hpateTotalTreated :
      Tendsto
        (fun index =>
          pateTreatedNormalizer index *
            ((pateTreatedSample index).card : Real))
        l (nhds pateTotalLimit))
    (hpateTotalControl :
      Tendsto
        (fun index =>
          pateControlNormalizer index *
            ((pateControlSample index).card : Real))
        l (nhds pateTotalLimit))
    (hpattTotalTarget :
      Tendsto
        (fun index =>
          pattTargetNormalizer index * ((pattTargetSample index).card : Real))
        l (nhds pattTotalLimit))
    (hpattTotalControl :
      Tendsto
        (fun index =>
          pattControlNormalizer index *
            ((pattControlSample index).card : Real))
        l (nhds pattTotalLimit))
    (hpateScaledCellTreated :
      ∀ cell, cell ∈ pateCells ->
        Tendsto
          (fun index =>
            scale index *
              (pateTargetNormalizer index *
                  (((pateTargetSample index).filter
                    (fun unit =>
                      pateDoubleScore (patePropensityScore index)
                        (pateTreatedPrognosticScore index)
                        (pateControlPrognosticScore index) unit = cell)).card :
                    Real) -
                pateTreatedNormalizer index *
                  (((pateTreatedSample index).filter
                    (fun unit =>
                      pateDoubleScore (patePropensityScore index)
                        (pateTreatedPrognosticScore index)
                        (pateControlPrognosticScore index) unit = cell)).card :
                    Real)))
          l (nhds 0))
    (hpateScaledCellControl :
      ∀ cell, cell ∈ pateCells ->
        Tendsto
          (fun index =>
            scale index *
              (pateTargetNormalizer index *
                  (((pateTargetSample index).filter
                    (fun unit =>
                      pateDoubleScore (patePropensityScore index)
                        (pateTreatedPrognosticScore index)
                        (pateControlPrognosticScore index) unit = cell)).card :
                    Real) -
                pateControlNormalizer index *
                  (((pateControlSample index).filter
                    (fun unit =>
                      pateDoubleScore (patePropensityScore index)
                        (pateTreatedPrognosticScore index)
                        (pateControlPrognosticScore index) unit = cell)).card :
                    Real)))
          l (nhds 0))
    (hpattScaledCellControl :
      ∀ cell, cell ∈ pattCells ->
        Tendsto
          (fun index =>
            scale index *
              (pattTargetNormalizer index *
                  (((pattTargetSample index).filter
                    (fun unit =>
                      pattDoubleScore (pattPropensityScore index)
                        (pattControlPrognosticScore index) unit = cell)).card :
                    Real) -
                pattControlNormalizer index *
                  (((pattControlSample index).filter
                    (fun unit =>
                      pattDoubleScore (pattPropensityScore index)
                        (pattControlPrognosticScore index) unit = cell)).card :
                    Real)))
          l (nhds 0))
    (hpateScaledTotalTreated :
      Tendsto
        (fun index =>
          scale index *
            (pateTargetNormalizer index *
                ((pateTargetSample index).card : Real) -
              pateTreatedNormalizer index *
                ((pateTreatedSample index).card : Real)))
        l (nhds 0))
    (hpateScaledTotalControl :
      Tendsto
        (fun index =>
          scale index *
            (pateTargetNormalizer index *
                ((pateTargetSample index).card : Real) -
              pateControlNormalizer index *
                ((pateControlSample index).card : Real)))
        l (nhds 0))
    (hpattScaledTotalControl :
      Tendsto
        (fun index =>
          scale index *
            (pattTargetNormalizer index *
                ((pattTargetSample index).card : Real) -
              pattControlNormalizer index *
                ((pattControlSample index).card : Real)))
        l (nhds 0))
    (hpateTotalLimit : pateTotalLimit ≠ 0)
    (hpattTotalLimit : pattTotalLimit ≠ 0)
    (hpateScoreMeasTargetT :
      ∀ index unit, unit ∈ pateTargetSample index ->
        pateTargetOutcomeT index unit =
          pateTreatedValue index (pateTreatedPrognosticScore index unit))
    (hpateScoreMeasTreated :
      ∀ index unit, unit ∈ pateTreatedSample index ->
        pateTreatedOutcome index unit =
          pateTreatedValue index (pateTreatedPrognosticScore index unit))
    (hpateScoreMeasTargetC :
      ∀ index unit, unit ∈ pateTargetSample index ->
        pateTargetOutcomeC index unit =
          pateControlValue index (pateControlPrognosticScore index unit))
    (hpateScoreMeasControl :
      ∀ index unit, unit ∈ pateControlSample index ->
        pateControlOutcome index unit =
          pateControlValue index (pateControlPrognosticScore index unit))
    (hpattScoreMeasTargetC :
      ∀ index unit, unit ∈ pattTargetSample index ->
        pattTargetControlOutcome index unit =
          pattControlValue index (pattControlPrognosticScore index unit))
    (hpattScoreMeasControl :
      ∀ index unit, unit ∈ pattControlSample index ->
        pattControlOutcome index unit =
          pattControlValue index (pattControlPrognosticScore index unit))
    (hpateTreatedBound :
      ∀ index cell, cell ∈ pateCells ->
        |treatedCellValueOnPATEDoubleScore (pateTreatedValue index) cell| ≤
          pateTreatedEnvelope index)
    (hpateControlBound :
      ∀ index cell, cell ∈ pateCells ->
        |controlCellValueOnPATEDoubleScore (pateControlValue index) cell| ≤
          pateControlEnvelope index)
    (hpattControlBound :
      ∀ index cell, cell ∈ pattCells ->
        |controlCellValueOnPATTDoubleScore (pattControlValue index) cell| ≤
          pattControlEnvelope index)
    (hpateTreatedEnvelope :
      Tendsto pateTreatedEnvelope l (nhds pateTreatedEnvelopeLimit))
    (hpateControlEnvelope :
      Tendsto pateControlEnvelope l (nhds pateControlEnvelopeLimit))
    (hpattControlEnvelope :
      Tendsto pattControlEnvelope l (nhds pattControlEnvelopeLimit)) :
    Tendsto
        (fun index =>
          weightedSampleMeanContrast (pateTargetSample index)
            (fun _unit => pateTargetCommonWeight index)
            (pateTargetOutcomeT index) (pateTargetOutcomeC index) -
          twoArmWeightedMeanContrast (pateTreatedSample index)
            (pateControlSample index)
            (fun _unit => pateTreatedCommonWeight index)
            (fun _unit => pateControlCommonWeight index)
            (pateTreatedOutcome index) (pateControlOutcome index))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleMeanContrast (pateTargetSample index)
              (fun _unit => pateTargetCommonWeight index)
              (pateTargetOutcomeT index) (pateTargetOutcomeC index) -
            twoArmWeightedMeanContrast (pateTreatedSample index)
              (pateControlSample index)
              (fun _unit => pateTreatedCommonWeight index)
              (fun _unit => pateControlCommonWeight index)
              (pateTreatedOutcome index) (pateControlOutcome index)))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          weightedSampleMeanContrast (pattTargetSample index)
            (fun _unit => pattTargetCommonWeight index)
            (pattTreatedTargetOutcome index) (pattTargetControlOutcome index) -
          pattWeightedMeanContrast (pattTargetSample index)
            (pattControlSample index)
            (fun _unit => pattTargetCommonWeight index)
            (fun _unit => pattControlCommonWeight index)
            (pattTreatedTargetOutcome index) (pattControlOutcome index))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleMeanContrast (pattTargetSample index)
              (fun _unit => pattTargetCommonWeight index)
              (pattTreatedTargetOutcome index)
              (pattTargetControlOutcome index) -
            pattWeightedMeanContrast (pattTargetSample index)
              (pattControlSample index)
              (fun _unit => pattTargetCommonWeight index)
              (fun _unit => pattControlCommonWeight index)
              (pattTreatedTargetOutcome index) (pattControlOutcome index)))
        l (nhds 0) := by
  have hpate :
      Tendsto
          (fun index =>
            weightedSampleMeanContrast (pateTargetSample index)
              (fun _unit => pateTargetCommonWeight index)
              (pateTargetOutcomeT index) (pateTargetOutcomeC index) -
            twoArmWeightedMeanContrast (pateTreatedSample index)
              (pateControlSample index)
              (fun _unit => pateTreatedCommonWeight index)
              (fun _unit => pateControlCommonWeight index)
              (pateTreatedOutcome index) (pateControlOutcome index))
          l (nhds 0) ∧
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleMeanContrast (pateTargetSample index)
                (fun _unit => pateTargetCommonWeight index)
                (pateTargetOutcomeT index) (pateTargetOutcomeC index) -
              twoArmWeightedMeanContrast (pateTreatedSample index)
                (pateControlSample index)
                (fun _unit => pateTreatedCommonWeight index)
                (fun _unit => pateControlCommonWeight index)
                (pateTreatedOutcome index) (pateControlOutcome index)))
          l (nhds 0) :=
    tendsto_pateDoubleScoreApprox_error_zero_and_scaled_zero_of_normalized_counts_and_envelopes_constant_weight
      scale pateTargetSample pateTreatedSample pateControlSample pateCells
      pateTargetCommonWeight pateTreatedCommonWeight pateControlCommonWeight
      pateTargetNormalizer pateTreatedNormalizer pateControlNormalizer
      pateTargetOutcomeT pateTargetOutcomeC pateTreatedOutcome
      pateControlOutcome patePropensityScore pateTreatedPrognosticScore
      pateControlPrognosticScore pateTreatedValue pateControlValue
      pateTreatedEnvelope pateControlEnvelope pateTreatedEnvelopeLimit
      pateControlEnvelopeLimit pateCellLimit pateTotalLimit hscale_nonneg
      hpateWeightTarget hpateWeightTreated hpateWeightControl
      hpateNormalizerTarget hpateNormalizerTreated hpateNormalizerControl
      hpateNonemptyTarget hpateNonemptyTreated hpateNonemptyControl
      hpateCoverTarget hpateCoverTreated hpateCoverControl
      hpateMassTarget hpateMassTreated hpateMassControl
      hpateCellTarget hpateCellTreated hpateCellControl hpateTotalTarget
      hpateTotalTreated hpateTotalControl hpateScaledCellTreated
      hpateScaledCellControl hpateScaledTotalTreated
      hpateScaledTotalControl hpateTotalLimit hpateScoreMeasTargetT
      hpateScoreMeasTreated hpateScoreMeasTargetC hpateScoreMeasControl
      hpateTreatedBound hpateControlBound hpateTreatedEnvelope
      hpateControlEnvelope
  have hpatt :
      Tendsto
          (fun index =>
            weightedSampleMeanContrast (pattTargetSample index)
              (fun _unit => pattTargetCommonWeight index)
              (pattTreatedTargetOutcome index)
              (pattTargetControlOutcome index) -
            pattWeightedMeanContrast (pattTargetSample index)
              (pattControlSample index)
              (fun _unit => pattTargetCommonWeight index)
              (fun _unit => pattControlCommonWeight index)
              (pattTreatedTargetOutcome index) (pattControlOutcome index))
          l (nhds 0) ∧
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleMeanContrast (pattTargetSample index)
                (fun _unit => pattTargetCommonWeight index)
                (pattTreatedTargetOutcome index)
                (pattTargetControlOutcome index) -
              pattWeightedMeanContrast (pattTargetSample index)
                (pattControlSample index)
                (fun _unit => pattTargetCommonWeight index)
                (fun _unit => pattControlCommonWeight index)
                (pattTreatedTargetOutcome index) (pattControlOutcome index)))
          l (nhds 0) :=
    tendsto_pattDoubleScoreApprox_error_zero_and_scaled_zero_of_normalized_counts_and_envelope_constant_weight
      scale pattTargetSample pattControlSample pattCells
      pattTargetCommonWeight pattControlCommonWeight pattTargetNormalizer
      pattControlNormalizer pattTreatedTargetOutcome pattTargetControlOutcome
      pattControlOutcome pattPropensityScore pattControlPrognosticScore
      pattControlValue pattControlEnvelope pattControlEnvelopeLimit
      pattCellLimit pattTotalLimit hscale_nonneg hpattWeightTarget
      hpattWeightControl hpattNormalizerTarget hpattNormalizerControl
      hpattNonemptyTarget hpattNonemptyControl hpattCoverTarget
      hpattCoverControl hpattMassTarget hpattMassControl hpattCellTarget
      hpattCellControl hpattTotalTarget hpattTotalControl
      hpattScaledCellControl hpattScaledTotalControl hpattTotalLimit
      hpattScoreMeasTargetC hpattScoreMeasControl hpattControlBound
      hpattControlEnvelope
  exact ⟨hpate.1, hpate.2, hpatt.1, hpatt.2⟩

theorem tendsto_scaled_pattDoubleScoreApprox_error_zero_of_indicator_sums_and_envelope_constant_weight
    (scale : Index -> Real)
    (targetSample controlSample : Index -> Finset Unit)
    (cells : Finset (PropensityCell × PATTProgCell))
    (targetCommonWeight controlCommonWeight : Index -> Real)
    (targetNormalizer controlNormalizer : Index -> Real)
    (treatedTargetOutcome targetControlOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (controlValue : Index -> PATTProgCell -> Real)
    (controlEnvelope : Index -> Real)
    (controlEnvelopeLimit : Real)
    (cellLimit : PropensityCell × PATTProgCell -> Real)
    (totalLimit : Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hweightTarget : ∀ index, targetCommonWeight index ≠ 0)
    (hweightControl : ∀ index, controlCommonWeight index ≠ 0)
    (hnormalizerTarget : ∀ index, targetNormalizer index ≠ 0)
    (hnormalizerControl : ∀ index, controlNormalizer index ≠ 0)
    (hnonemptyTarget : ∀ index, (targetSample index).Nonempty)
    (hnonemptyControl : ∀ index, (controlSample index).Nonempty)
    (hcoverTarget :
      ∀ index unit, unit ∈ targetSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hcoverControl :
      ∀ index unit, unit ∈ controlSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hmassTarget :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (targetSample index)
          (fun _unit => targetCommonWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (controlSample index)
          (fun _unit => controlCommonWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hcellControlIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (controlSample index)
              (fun _unit => controlNormalizer index)
              (scoreCellIndicator
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (cellLimit cell)))
    (htotalTargetIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (targetSample index)
            (fun _unit => targetNormalizer index) (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalControlIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (controlSample index)
            (fun _unit => controlNormalizer index) (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (hscaledCellControlIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (targetSample index)
                  (fun _unit => targetNormalizer index)
                  (scoreCellIndicator
                    (pattDoubleScore (propensityScore index)
                      (controlPrognosticScore index)) cell) -
                weightedSampleSum (controlSample index)
                  (fun _unit => controlNormalizer index)
                  (scoreCellIndicator
                    (pattDoubleScore (propensityScore index)
                      (controlPrognosticScore index)) cell)))
          l (nhds 0))
    (hscaledTotalControlIndicator :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (targetSample index)
                (fun _unit => targetNormalizer index)
                (fun _unit => (1 : Real)) -
              weightedSampleSum (controlSample index)
                (fun _unit => controlNormalizer index)
                (fun _unit => (1 : Real))))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0)
    (hscoreMeasTargetC :
      ∀ index unit, unit ∈ targetSample index ->
        targetControlOutcome index unit =
          controlValue index (controlPrognosticScore index unit))
    (hscoreMeasControl :
      ∀ index unit, unit ∈ controlSample index ->
        controlOutcome index unit =
          controlValue index (controlPrognosticScore index unit))
    (hcontrol_bound :
      ∀ index cell, cell ∈ cells ->
        |controlCellValueOnPATTDoubleScore (controlValue index) cell| ≤
          controlEnvelope index)
    (hcontrolEnvelope :
      Tendsto controlEnvelope l (nhds controlEnvelopeLimit)) :
    Tendsto
      (fun index =>
        scale index *
          (weightedSampleMeanContrast (targetSample index)
            (fun _unit => targetCommonWeight index)
            (treatedTargetOutcome index) (targetControlOutcome index) -
          pattWeightedMeanContrast (targetSample index) (controlSample index)
            (fun _unit => targetCommonWeight index)
            (fun _unit => controlCommonWeight index)
            (treatedTargetOutcome index) (controlOutcome index)))
      l (nhds 0) :=
  tendsto_scaled_pattDoubleScoreApprox_error_zero_of_normalized_counts_and_envelope_constant_weight
    scale targetSample controlSample cells targetCommonWeight
    controlCommonWeight targetNormalizer controlNormalizer
    treatedTargetOutcome targetControlOutcome controlOutcome propensityScore
    controlPrognosticScore controlValue controlEnvelope controlEnvelopeLimit
    cellLimit totalLimit hscale_nonneg hweightTarget hweightControl
    hnormalizerTarget hnormalizerControl hnonemptyTarget hnonemptyControl
    hcoverTarget hcoverControl hmassTarget hmassControl
    (tendsto_all_patt_normalized_cell_counts_of_tendsto_indicators_constant_weight
      controlSample propensityScore controlPrognosticScore cells
      controlNormalizer cellLimit hcellControlIndicator)
    (tendsto_normalized_total_count_of_tendsto_weightedSampleSum_one_constant_weight
      targetSample targetNormalizer totalLimit htotalTargetIndicator)
    (tendsto_normalized_total_count_of_tendsto_weightedSampleSum_one_constant_weight
      controlSample controlNormalizer totalLimit htotalControlIndicator)
    (tendsto_all_scaled_patt_normalized_cell_count_differences_of_tendsto_indicator_differences_constant_weight
      scale targetSample controlSample propensityScore controlPrognosticScore
      cells targetNormalizer controlNormalizer (fun _cell => (0 : Real))
      hscaledCellControlIndicator)
    (tendsto_scaled_normalized_total_count_difference_of_tendsto_scaled_weightedSampleSum_one_difference_constant_weight
      scale targetSample controlSample targetNormalizer controlNormalizer
      (0 : Real) hscaledTotalControlIndicator)
    htotalLimit hscoreMeasTargetC hscoreMeasControl hcontrol_bound
    hcontrolEnvelope

theorem tendsto_pateDoubleScoreApprox_error_zero_of_indicator_sums_and_envelopes_constant_weight
    (targetSample treatedSample controlSample : Index -> Finset Unit)
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (targetCommonWeight treatedCommonWeight controlCommonWeight :
      Index -> Real)
    (targetNormalizer treatedNormalizer controlNormalizer : Index -> Real)
    (targetOutcomeT targetOutcomeC treatedOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (treatedValue : Index -> TreatedProgCell -> Real)
    (controlValue : Index -> ControlProgCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (treatedEnvelopeLimit controlEnvelopeLimit : Real)
    (cellLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (totalLimit : Real)
    (hweightTarget : ∀ index, targetCommonWeight index ≠ 0)
    (hweightTreated : ∀ index, treatedCommonWeight index ≠ 0)
    (hweightControl : ∀ index, controlCommonWeight index ≠ 0)
    (hnormalizerTarget : ∀ index, targetNormalizer index ≠ 0)
    (hnormalizerTreated : ∀ index, treatedNormalizer index ≠ 0)
    (hnormalizerControl : ∀ index, controlNormalizer index ≠ 0)
    (hnonemptyTarget : ∀ index, (targetSample index).Nonempty)
    (hnonemptyTreated : ∀ index, (treatedSample index).Nonempty)
    (hnonemptyControl : ∀ index, (controlSample index).Nonempty)
    (hcoverTarget :
      ∀ index unit, unit ∈ targetSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hcoverTreated :
      ∀ index unit, unit ∈ treatedSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hcoverControl :
      ∀ index unit, unit ∈ controlSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hmassTarget :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (targetSample index)
          (fun _unit => targetCommonWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassTreated :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (treatedSample index)
          (fun _unit => treatedCommonWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (controlSample index)
          (fun _unit => controlCommonWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hcellTargetIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (targetSample index)
              (fun _unit => targetNormalizer index)
              (scoreCellIndicator
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (cellLimit cell)))
    (hcellTreatedIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (treatedSample index)
              (fun _unit => treatedNormalizer index)
              (scoreCellIndicator
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (cellLimit cell)))
    (hcellControlIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (controlSample index)
              (fun _unit => controlNormalizer index)
              (scoreCellIndicator
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (cellLimit cell)))
    (htotalTargetIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (targetSample index)
            (fun _unit => targetNormalizer index) (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalTreatedIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (treatedSample index)
            (fun _unit => treatedNormalizer index) (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalControlIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (controlSample index)
            (fun _unit => controlNormalizer index) (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalLimit : totalLimit ≠ 0)
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
      ∀ index cell, cell ∈ cells ->
        |treatedCellValueOnPATEDoubleScore (treatedValue index) cell| ≤
          treatedEnvelope index)
    (hcontrol_bound :
      ∀ index cell, cell ∈ cells ->
        |controlCellValueOnPATEDoubleScore (controlValue index) cell| ≤
          controlEnvelope index)
    (htreatedEnvelope :
      Tendsto treatedEnvelope l (nhds treatedEnvelopeLimit))
    (hcontrolEnvelope :
      Tendsto controlEnvelope l (nhds controlEnvelopeLimit)) :
    Tendsto
      (fun index =>
        weightedSampleMeanContrast (targetSample index)
          (fun _unit => targetCommonWeight index) (targetOutcomeT index)
          (targetOutcomeC index) -
        twoArmWeightedMeanContrast (treatedSample index)
          (controlSample index) (fun _unit => treatedCommonWeight index)
          (fun _unit => controlCommonWeight index) (treatedOutcome index)
          (controlOutcome index))
      l (nhds 0) :=
  tendsto_pateDoubleScoreApprox_error_zero_of_normalized_counts_and_envelopes_constant_weight
    targetSample treatedSample controlSample cells targetCommonWeight
    treatedCommonWeight controlCommonWeight targetNormalizer
    treatedNormalizer controlNormalizer targetOutcomeT targetOutcomeC
    treatedOutcome controlOutcome propensityScore treatedPrognosticScore
    controlPrognosticScore treatedValue controlValue treatedEnvelope
    controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit cellLimit
    totalLimit hweightTarget hweightTreated hweightControl
    hnormalizerTarget hnormalizerTreated hnormalizerControl
    hnonemptyTarget hnonemptyTreated hnonemptyControl hcoverTarget
    hcoverTreated hcoverControl hmassTarget hmassTreated hmassControl
    (tendsto_all_pate_normalized_cell_counts_of_tendsto_indicators_constant_weight
      targetSample propensityScore treatedPrognosticScore
      controlPrognosticScore cells targetNormalizer cellLimit
      hcellTargetIndicator)
    (tendsto_all_pate_normalized_cell_counts_of_tendsto_indicators_constant_weight
      treatedSample propensityScore treatedPrognosticScore
      controlPrognosticScore cells treatedNormalizer cellLimit
      hcellTreatedIndicator)
    (tendsto_all_pate_normalized_cell_counts_of_tendsto_indicators_constant_weight
      controlSample propensityScore treatedPrognosticScore
      controlPrognosticScore cells controlNormalizer cellLimit
      hcellControlIndicator)
    (tendsto_normalized_total_count_of_tendsto_weightedSampleSum_one_constant_weight
      targetSample targetNormalizer totalLimit htotalTargetIndicator)
    (tendsto_normalized_total_count_of_tendsto_weightedSampleSum_one_constant_weight
      treatedSample treatedNormalizer totalLimit htotalTreatedIndicator)
    (tendsto_normalized_total_count_of_tendsto_weightedSampleSum_one_constant_weight
      controlSample controlNormalizer totalLimit htotalControlIndicator)
    htotalLimit hscoreMeasTargetT hscoreMeasTreated hscoreMeasTargetC
    hscoreMeasControl htreated_bound hcontrol_bound htreatedEnvelope
    hcontrolEnvelope

theorem tendsto_pattDoubleScoreApprox_error_zero_of_indicator_sums_and_envelope_constant_weight
    (targetSample controlSample : Index -> Finset Unit)
    (cells : Finset (PropensityCell × PATTProgCell))
    (targetCommonWeight controlCommonWeight : Index -> Real)
    (targetNormalizer controlNormalizer : Index -> Real)
    (treatedTargetOutcome targetControlOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (controlValue : Index -> PATTProgCell -> Real)
    (controlEnvelope : Index -> Real)
    (controlEnvelopeLimit : Real)
    (cellLimit : PropensityCell × PATTProgCell -> Real)
    (totalLimit : Real)
    (hweightTarget : ∀ index, targetCommonWeight index ≠ 0)
    (hweightControl : ∀ index, controlCommonWeight index ≠ 0)
    (hnormalizerTarget : ∀ index, targetNormalizer index ≠ 0)
    (hnormalizerControl : ∀ index, controlNormalizer index ≠ 0)
    (hnonemptyTarget : ∀ index, (targetSample index).Nonempty)
    (hnonemptyControl : ∀ index, (controlSample index).Nonempty)
    (hcoverTarget :
      ∀ index unit, unit ∈ targetSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hcoverControl :
      ∀ index unit, unit ∈ controlSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hmassTarget :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (targetSample index)
          (fun _unit => targetCommonWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (controlSample index)
          (fun _unit => controlCommonWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hcellTargetIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (targetSample index)
              (fun _unit => targetNormalizer index)
              (scoreCellIndicator
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (cellLimit cell)))
    (hcellControlIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (controlSample index)
              (fun _unit => controlNormalizer index)
              (scoreCellIndicator
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (cellLimit cell)))
    (htotalTargetIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (targetSample index)
            (fun _unit => targetNormalizer index) (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalControlIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (controlSample index)
            (fun _unit => controlNormalizer index) (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalLimit : totalLimit ≠ 0)
    (hscoreMeasTargetC :
      ∀ index unit, unit ∈ targetSample index ->
        targetControlOutcome index unit =
          controlValue index (controlPrognosticScore index unit))
    (hscoreMeasControl :
      ∀ index unit, unit ∈ controlSample index ->
        controlOutcome index unit =
          controlValue index (controlPrognosticScore index unit))
    (hcontrol_bound :
      ∀ index cell, cell ∈ cells ->
        |controlCellValueOnPATTDoubleScore (controlValue index) cell| ≤
          controlEnvelope index)
    (hcontrolEnvelope :
      Tendsto controlEnvelope l (nhds controlEnvelopeLimit)) :
    Tendsto
      (fun index =>
        weightedSampleMeanContrast (targetSample index)
          (fun _unit => targetCommonWeight index)
          (treatedTargetOutcome index) (targetControlOutcome index) -
        pattWeightedMeanContrast (targetSample index) (controlSample index)
          (fun _unit => targetCommonWeight index)
          (fun _unit => controlCommonWeight index)
          (treatedTargetOutcome index) (controlOutcome index))
      l (nhds 0) :=
  tendsto_pattDoubleScoreApprox_error_zero_of_normalized_counts_and_envelope_constant_weight
    targetSample controlSample cells targetCommonWeight controlCommonWeight
    targetNormalizer controlNormalizer treatedTargetOutcome
    targetControlOutcome controlOutcome propensityScore
    controlPrognosticScore controlValue controlEnvelope controlEnvelopeLimit
    cellLimit totalLimit hweightTarget hweightControl hnormalizerTarget
    hnormalizerControl hnonemptyTarget hnonemptyControl hcoverTarget
    hcoverControl hmassTarget hmassControl
    (tendsto_all_patt_normalized_cell_counts_of_tendsto_indicators_constant_weight
      targetSample propensityScore controlPrognosticScore cells
      targetNormalizer cellLimit hcellTargetIndicator)
    (tendsto_all_patt_normalized_cell_counts_of_tendsto_indicators_constant_weight
      controlSample propensityScore controlPrognosticScore cells
      controlNormalizer cellLimit hcellControlIndicator)
    (tendsto_normalized_total_count_of_tendsto_weightedSampleSum_one_constant_weight
      targetSample targetNormalizer totalLimit htotalTargetIndicator)
    (tendsto_normalized_total_count_of_tendsto_weightedSampleSum_one_constant_weight
      controlSample controlNormalizer totalLimit htotalControlIndicator)
    htotalLimit hscoreMeasTargetC hscoreMeasControl hcontrol_bound
    hcontrolEnvelope

/--
PATE approximation convergence at ordinary and scaled rates from
weighted indicator-sum LLNs and scaled indicator-sum differences.
-/
theorem tendsto_pateDoubleScoreApprox_error_zero_and_scaled_zero_of_indicator_sums_and_envelopes_constant_weight
    (scale : Index -> Real)
    (targetSample treatedSample controlSample : Index -> Finset Unit)
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (targetCommonWeight treatedCommonWeight controlCommonWeight :
      Index -> Real)
    (targetNormalizer treatedNormalizer controlNormalizer : Index -> Real)
    (targetOutcomeT targetOutcomeC treatedOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (treatedValue : Index -> TreatedProgCell -> Real)
    (controlValue : Index -> ControlProgCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (treatedEnvelopeLimit controlEnvelopeLimit : Real)
    (cellLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (totalLimit : Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hweightTarget : ∀ index, targetCommonWeight index ≠ 0)
    (hweightTreated : ∀ index, treatedCommonWeight index ≠ 0)
    (hweightControl : ∀ index, controlCommonWeight index ≠ 0)
    (hnormalizerTarget : ∀ index, targetNormalizer index ≠ 0)
    (hnormalizerTreated : ∀ index, treatedNormalizer index ≠ 0)
    (hnormalizerControl : ∀ index, controlNormalizer index ≠ 0)
    (hnonemptyTarget : ∀ index, (targetSample index).Nonempty)
    (hnonemptyTreated : ∀ index, (treatedSample index).Nonempty)
    (hnonemptyControl : ∀ index, (controlSample index).Nonempty)
    (hcoverTarget :
      ∀ index unit, unit ∈ targetSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hcoverTreated :
      ∀ index unit, unit ∈ treatedSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hcoverControl :
      ∀ index unit, unit ∈ controlSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hmassTarget :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (targetSample index)
          (fun _unit => targetCommonWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassTreated :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (treatedSample index)
          (fun _unit => treatedCommonWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (controlSample index)
          (fun _unit => controlCommonWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hcellTargetIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (targetSample index)
              (fun _unit => targetNormalizer index)
              (scoreCellIndicator
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (cellLimit cell)))
    (hcellTreatedIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (treatedSample index)
              (fun _unit => treatedNormalizer index)
              (scoreCellIndicator
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (cellLimit cell)))
    (hcellControlIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (controlSample index)
              (fun _unit => controlNormalizer index)
              (scoreCellIndicator
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (cellLimit cell)))
    (htotalTargetIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (targetSample index)
            (fun _unit => targetNormalizer index) (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalTreatedIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (treatedSample index)
            (fun _unit => treatedNormalizer index) (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalControlIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (controlSample index)
            (fun _unit => controlNormalizer index) (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (hscaledCellTreatedIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (targetSample index)
                  (fun _unit => targetNormalizer index)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index)) cell) -
                weightedSampleSum (treatedSample index)
                  (fun _unit => treatedNormalizer index)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index)) cell)))
          l (nhds 0))
    (hscaledCellControlIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (targetSample index)
                  (fun _unit => targetNormalizer index)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index)) cell) -
                weightedSampleSum (controlSample index)
                  (fun _unit => controlNormalizer index)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index)) cell)))
          l (nhds 0))
    (hscaledTotalTreatedIndicator :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (targetSample index)
                (fun _unit => targetNormalizer index)
                (fun _unit => (1 : Real)) -
              weightedSampleSum (treatedSample index)
                (fun _unit => treatedNormalizer index)
                (fun _unit => (1 : Real))))
        l (nhds 0))
    (hscaledTotalControlIndicator :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (targetSample index)
                (fun _unit => targetNormalizer index)
                (fun _unit => (1 : Real)) -
              weightedSampleSum (controlSample index)
                (fun _unit => controlNormalizer index)
                (fun _unit => (1 : Real))))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0)
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
      ∀ index cell, cell ∈ cells ->
        |treatedCellValueOnPATEDoubleScore (treatedValue index) cell| ≤
          treatedEnvelope index)
    (hcontrol_bound :
      ∀ index cell, cell ∈ cells ->
        |controlCellValueOnPATEDoubleScore (controlValue index) cell| ≤
          controlEnvelope index)
    (htreatedEnvelope :
      Tendsto treatedEnvelope l (nhds treatedEnvelopeLimit))
    (hcontrolEnvelope :
      Tendsto controlEnvelope l (nhds controlEnvelopeLimit)) :
    Tendsto
        (fun index =>
          weightedSampleMeanContrast (targetSample index)
            (fun _unit => targetCommonWeight index) (targetOutcomeT index)
            (targetOutcomeC index) -
          twoArmWeightedMeanContrast (treatedSample index)
            (controlSample index) (fun _unit => treatedCommonWeight index)
            (fun _unit => controlCommonWeight index) (treatedOutcome index)
            (controlOutcome index))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleMeanContrast (targetSample index)
              (fun _unit => targetCommonWeight index) (targetOutcomeT index)
              (targetOutcomeC index) -
            twoArmWeightedMeanContrast (treatedSample index)
              (controlSample index) (fun _unit => treatedCommonWeight index)
              (fun _unit => controlCommonWeight index) (treatedOutcome index)
              (controlOutcome index)))
        l (nhds 0) := by
  constructor
  · exact
      tendsto_pateDoubleScoreApprox_error_zero_of_indicator_sums_and_envelopes_constant_weight
        targetSample treatedSample controlSample cells targetCommonWeight
        treatedCommonWeight controlCommonWeight targetNormalizer
        treatedNormalizer controlNormalizer targetOutcomeT targetOutcomeC
        treatedOutcome controlOutcome propensityScore treatedPrognosticScore
        controlPrognosticScore treatedValue controlValue treatedEnvelope
        controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit cellLimit
        totalLimit hweightTarget hweightTreated hweightControl
        hnormalizerTarget hnormalizerTreated hnormalizerControl
        hnonemptyTarget hnonemptyTreated hnonemptyControl hcoverTarget
        hcoverTreated hcoverControl hmassTarget hmassTreated hmassControl
        hcellTargetIndicator hcellTreatedIndicator hcellControlIndicator
        htotalTargetIndicator htotalTreatedIndicator htotalControlIndicator
        htotalLimit hscoreMeasTargetT hscoreMeasTreated hscoreMeasTargetC
        hscoreMeasControl htreated_bound hcontrol_bound htreatedEnvelope
        hcontrolEnvelope
  · exact
      tendsto_scaled_pateDoubleScoreApprox_error_zero_of_indicator_sums_and_envelopes_constant_weight
        scale targetSample treatedSample controlSample cells targetCommonWeight
        treatedCommonWeight controlCommonWeight targetNormalizer
        treatedNormalizer controlNormalizer targetOutcomeT targetOutcomeC
        treatedOutcome controlOutcome propensityScore treatedPrognosticScore
        controlPrognosticScore treatedValue controlValue treatedEnvelope
        controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit cellLimit
        totalLimit hscale_nonneg hweightTarget hweightTreated hweightControl
        hnormalizerTarget hnormalizerTreated hnormalizerControl
        hnonemptyTarget hnonemptyTreated hnonemptyControl hcoverTarget
        hcoverTreated hcoverControl hmassTarget hmassTreated hmassControl
        hcellTreatedIndicator hcellControlIndicator htotalTargetIndicator
        htotalTreatedIndicator htotalControlIndicator
        hscaledCellTreatedIndicator hscaledCellControlIndicator
        hscaledTotalTreatedIndicator hscaledTotalControlIndicator
        htotalLimit hscoreMeasTargetT hscoreMeasTreated hscoreMeasTargetC
        hscoreMeasControl htreated_bound hcontrol_bound htreatedEnvelope
        hcontrolEnvelope

/--
PATT approximation convergence at ordinary and scaled rates from
weighted indicator-sum LLNs and scaled indicator-sum differences.
-/
theorem tendsto_pattDoubleScoreApprox_error_zero_and_scaled_zero_of_indicator_sums_and_envelope_constant_weight
    (scale : Index -> Real)
    (targetSample controlSample : Index -> Finset Unit)
    (cells : Finset (PropensityCell × PATTProgCell))
    (targetCommonWeight controlCommonWeight : Index -> Real)
    (targetNormalizer controlNormalizer : Index -> Real)
    (treatedTargetOutcome targetControlOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (controlValue : Index -> PATTProgCell -> Real)
    (controlEnvelope : Index -> Real)
    (controlEnvelopeLimit : Real)
    (cellLimit : PropensityCell × PATTProgCell -> Real)
    (totalLimit : Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hweightTarget : ∀ index, targetCommonWeight index ≠ 0)
    (hweightControl : ∀ index, controlCommonWeight index ≠ 0)
    (hnormalizerTarget : ∀ index, targetNormalizer index ≠ 0)
    (hnormalizerControl : ∀ index, controlNormalizer index ≠ 0)
    (hnonemptyTarget : ∀ index, (targetSample index).Nonempty)
    (hnonemptyControl : ∀ index, (controlSample index).Nonempty)
    (hcoverTarget :
      ∀ index unit, unit ∈ targetSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hcoverControl :
      ∀ index unit, unit ∈ controlSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hmassTarget :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (targetSample index)
          (fun _unit => targetCommonWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (controlSample index)
          (fun _unit => controlCommonWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hcellTargetIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (targetSample index)
              (fun _unit => targetNormalizer index)
              (scoreCellIndicator
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (cellLimit cell)))
    (hcellControlIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (controlSample index)
              (fun _unit => controlNormalizer index)
              (scoreCellIndicator
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (cellLimit cell)))
    (htotalTargetIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (targetSample index)
            (fun _unit => targetNormalizer index) (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalControlIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (controlSample index)
            (fun _unit => controlNormalizer index) (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (hscaledCellControlIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (targetSample index)
                  (fun _unit => targetNormalizer index)
                  (scoreCellIndicator
                    (pattDoubleScore (propensityScore index)
                      (controlPrognosticScore index)) cell) -
                weightedSampleSum (controlSample index)
                  (fun _unit => controlNormalizer index)
                  (scoreCellIndicator
                    (pattDoubleScore (propensityScore index)
                      (controlPrognosticScore index)) cell)))
          l (nhds 0))
    (hscaledTotalControlIndicator :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (targetSample index)
                (fun _unit => targetNormalizer index)
                (fun _unit => (1 : Real)) -
              weightedSampleSum (controlSample index)
                (fun _unit => controlNormalizer index)
                (fun _unit => (1 : Real))))
        l (nhds 0))
    (htotalLimit : totalLimit ≠ 0)
    (hscoreMeasTargetC :
      ∀ index unit, unit ∈ targetSample index ->
        targetControlOutcome index unit =
          controlValue index (controlPrognosticScore index unit))
    (hscoreMeasControl :
      ∀ index unit, unit ∈ controlSample index ->
        controlOutcome index unit =
          controlValue index (controlPrognosticScore index unit))
    (hcontrol_bound :
      ∀ index cell, cell ∈ cells ->
        |controlCellValueOnPATTDoubleScore (controlValue index) cell| ≤
          controlEnvelope index)
    (hcontrolEnvelope :
      Tendsto controlEnvelope l (nhds controlEnvelopeLimit)) :
    Tendsto
        (fun index =>
          weightedSampleMeanContrast (targetSample index)
            (fun _unit => targetCommonWeight index)
            (treatedTargetOutcome index) (targetControlOutcome index) -
          pattWeightedMeanContrast (targetSample index) (controlSample index)
            (fun _unit => targetCommonWeight index)
            (fun _unit => controlCommonWeight index)
            (treatedTargetOutcome index) (controlOutcome index))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleMeanContrast (targetSample index)
              (fun _unit => targetCommonWeight index)
              (treatedTargetOutcome index) (targetControlOutcome index) -
            pattWeightedMeanContrast (targetSample index) (controlSample index)
              (fun _unit => targetCommonWeight index)
              (fun _unit => controlCommonWeight index)
              (treatedTargetOutcome index) (controlOutcome index)))
        l (nhds 0) := by
  constructor
  · exact
      tendsto_pattDoubleScoreApprox_error_zero_of_indicator_sums_and_envelope_constant_weight
        targetSample controlSample cells targetCommonWeight
        controlCommonWeight targetNormalizer controlNormalizer
        treatedTargetOutcome targetControlOutcome controlOutcome
        propensityScore controlPrognosticScore controlValue controlEnvelope
        controlEnvelopeLimit cellLimit totalLimit hweightTarget
        hweightControl hnormalizerTarget hnormalizerControl hnonemptyTarget
        hnonemptyControl hcoverTarget hcoverControl hmassTarget hmassControl
        hcellTargetIndicator hcellControlIndicator htotalTargetIndicator
        htotalControlIndicator htotalLimit hscoreMeasTargetC
        hscoreMeasControl hcontrol_bound hcontrolEnvelope
  · exact
      tendsto_scaled_pattDoubleScoreApprox_error_zero_of_indicator_sums_and_envelope_constant_weight
        scale targetSample controlSample cells targetCommonWeight
        controlCommonWeight targetNormalizer controlNormalizer
        treatedTargetOutcome targetControlOutcome controlOutcome
        propensityScore controlPrognosticScore controlValue controlEnvelope
        controlEnvelopeLimit cellLimit totalLimit hscale_nonneg hweightTarget
        hweightControl hnormalizerTarget hnormalizerControl hnonemptyTarget
        hnonemptyControl hcoverTarget hcoverControl hmassTarget hmassControl
        hcellControlIndicator htotalTargetIndicator htotalControlIndicator
        hscaledCellControlIndicator hscaledTotalControlIndicator
        htotalLimit hscoreMeasTargetC hscoreMeasControl hcontrol_bound
        hcontrolEnvelope

/--
Paired PATE/PATT approximation convergence at ordinary and scaled rates from
weighted indicator-sum LLNs and scaled indicator-sum differences.
-/
theorem tendsto_pate_pattDoubleScoreApprox_error_zero_and_scaled_zero_of_indicator_sums_and_envelopes_constant_weight
    (scale : Index -> Real)
    (pateTargetSample pateTreatedSample pateControlSample :
      Index -> Finset Unit)
    (pattTargetSample pattControlSample : Index -> Finset Unit)
    (pateCells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (pattCells : Finset (PropensityCell × PATTProgCell))
    (pateTargetCommonWeight pateTreatedCommonWeight pateControlCommonWeight :
      Index -> Real)
    (pattTargetCommonWeight pattControlCommonWeight : Index -> Real)
    (pateTargetNormalizer pateTreatedNormalizer pateControlNormalizer :
      Index -> Real)
    (pattTargetNormalizer pattControlNormalizer : Index -> Real)
    (pateTargetOutcomeT pateTargetOutcomeC pateTreatedOutcome
      pateControlOutcome : Index -> Unit -> Real)
    (pattTreatedTargetOutcome pattTargetControlOutcome pattControlOutcome :
      Index -> Unit -> Real)
    (patePropensityScore pattPropensityScore :
      Index -> Unit -> PropensityCell)
    (pateTreatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (pateControlPrognosticScore : Index -> Unit -> ControlProgCell)
    (pattControlPrognosticScore : Index -> Unit -> PATTProgCell)
    (pateTreatedValue : Index -> TreatedProgCell -> Real)
    (pateControlValue : Index -> ControlProgCell -> Real)
    (pattControlValue : Index -> PATTProgCell -> Real)
    (pateTreatedEnvelope pateControlEnvelope pattControlEnvelope :
      Index -> Real)
    (pateTreatedEnvelopeLimit pateControlEnvelopeLimit
      pattControlEnvelopeLimit : Real)
    (pateCellLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (pattCellLimit : PropensityCell × PATTProgCell -> Real)
    (pateTotalLimit pattTotalLimit : Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hpateWeightTarget :
      ∀ index, pateTargetCommonWeight index ≠ 0)
    (hpateWeightTreated :
      ∀ index, pateTreatedCommonWeight index ≠ 0)
    (hpateWeightControl :
      ∀ index, pateControlCommonWeight index ≠ 0)
    (hpattWeightTarget :
      ∀ index, pattTargetCommonWeight index ≠ 0)
    (hpattWeightControl :
      ∀ index, pattControlCommonWeight index ≠ 0)
    (hpateNormalizerTarget :
      ∀ index, pateTargetNormalizer index ≠ 0)
    (hpateNormalizerTreated :
      ∀ index, pateTreatedNormalizer index ≠ 0)
    (hpateNormalizerControl :
      ∀ index, pateControlNormalizer index ≠ 0)
    (hpattNormalizerTarget :
      ∀ index, pattTargetNormalizer index ≠ 0)
    (hpattNormalizerControl :
      ∀ index, pattControlNormalizer index ≠ 0)
    (hpateNonemptyTarget :
      ∀ index, (pateTargetSample index).Nonempty)
    (hpateNonemptyTreated :
      ∀ index, (pateTreatedSample index).Nonempty)
    (hpateNonemptyControl :
      ∀ index, (pateControlSample index).Nonempty)
    (hpattNonemptyTarget :
      ∀ index, (pattTargetSample index).Nonempty)
    (hpattNonemptyControl :
      ∀ index, (pattControlSample index).Nonempty)
    (hpateCoverTarget :
      ∀ index unit, unit ∈ pateTargetSample index ->
        pateDoubleScore (patePropensityScore index)
          (pateTreatedPrognosticScore index)
          (pateControlPrognosticScore index) unit ∈ pateCells)
    (hpateCoverTreated :
      ∀ index unit, unit ∈ pateTreatedSample index ->
        pateDoubleScore (patePropensityScore index)
          (pateTreatedPrognosticScore index)
          (pateControlPrognosticScore index) unit ∈ pateCells)
    (hpateCoverControl :
      ∀ index unit, unit ∈ pateControlSample index ->
        pateDoubleScore (patePropensityScore index)
          (pateTreatedPrognosticScore index)
          (pateControlPrognosticScore index) unit ∈ pateCells)
    (hpattCoverTarget :
      ∀ index unit, unit ∈ pattTargetSample index ->
        pattDoubleScore (pattPropensityScore index)
          (pattControlPrognosticScore index) unit ∈ pattCells)
    (hpattCoverControl :
      ∀ index unit, unit ∈ pattControlSample index ->
        pattDoubleScore (pattPropensityScore index)
          (pattControlPrognosticScore index) unit ∈ pattCells)
    (hpateMassTarget :
      ∀ index cell, cell ∈ pateCells ->
        scoreCellMass (pateTargetSample index)
          (fun _unit => pateTargetCommonWeight index)
          (pateDoubleScore (patePropensityScore index)
            (pateTreatedPrognosticScore index)
            (pateControlPrognosticScore index)) cell ≠ 0)
    (hpateMassTreated :
      ∀ index cell, cell ∈ pateCells ->
        scoreCellMass (pateTreatedSample index)
          (fun _unit => pateTreatedCommonWeight index)
          (pateDoubleScore (patePropensityScore index)
            (pateTreatedPrognosticScore index)
            (pateControlPrognosticScore index)) cell ≠ 0)
    (hpateMassControl :
      ∀ index cell, cell ∈ pateCells ->
        scoreCellMass (pateControlSample index)
          (fun _unit => pateControlCommonWeight index)
          (pateDoubleScore (patePropensityScore index)
            (pateTreatedPrognosticScore index)
            (pateControlPrognosticScore index)) cell ≠ 0)
    (hpattMassTarget :
      ∀ index cell, cell ∈ pattCells ->
        scoreCellMass (pattTargetSample index)
          (fun _unit => pattTargetCommonWeight index)
          (pattDoubleScore (pattPropensityScore index)
            (pattControlPrognosticScore index)) cell ≠ 0)
    (hpattMassControl :
      ∀ index cell, cell ∈ pattCells ->
        scoreCellMass (pattControlSample index)
          (fun _unit => pattControlCommonWeight index)
          (pattDoubleScore (pattPropensityScore index)
            (pattControlPrognosticScore index)) cell ≠ 0)
    (hpateCellTargetIndicator :
      ∀ cell, cell ∈ pateCells ->
        Tendsto
          (fun index =>
            weightedSampleSum (pateTargetSample index)
              (fun _unit => pateTargetNormalizer index)
              (scoreCellIndicator
                (pateDoubleScore (patePropensityScore index)
                  (pateTreatedPrognosticScore index)
                  (pateControlPrognosticScore index)) cell))
          l (nhds (pateCellLimit cell)))
    (hpateCellTreatedIndicator :
      ∀ cell, cell ∈ pateCells ->
        Tendsto
          (fun index =>
            weightedSampleSum (pateTreatedSample index)
              (fun _unit => pateTreatedNormalizer index)
              (scoreCellIndicator
                (pateDoubleScore (patePropensityScore index)
                  (pateTreatedPrognosticScore index)
                  (pateControlPrognosticScore index)) cell))
          l (nhds (pateCellLimit cell)))
    (hpateCellControlIndicator :
      ∀ cell, cell ∈ pateCells ->
        Tendsto
          (fun index =>
            weightedSampleSum (pateControlSample index)
              (fun _unit => pateControlNormalizer index)
              (scoreCellIndicator
                (pateDoubleScore (patePropensityScore index)
                  (pateTreatedPrognosticScore index)
                  (pateControlPrognosticScore index)) cell))
          l (nhds (pateCellLimit cell)))
    (hpattCellTargetIndicator :
      ∀ cell, cell ∈ pattCells ->
        Tendsto
          (fun index =>
            weightedSampleSum (pattTargetSample index)
              (fun _unit => pattTargetNormalizer index)
              (scoreCellIndicator
                (pattDoubleScore (pattPropensityScore index)
                  (pattControlPrognosticScore index)) cell))
          l (nhds (pattCellLimit cell)))
    (hpattCellControlIndicator :
      ∀ cell, cell ∈ pattCells ->
        Tendsto
          (fun index =>
            weightedSampleSum (pattControlSample index)
              (fun _unit => pattControlNormalizer index)
              (scoreCellIndicator
                (pattDoubleScore (pattPropensityScore index)
                  (pattControlPrognosticScore index)) cell))
          l (nhds (pattCellLimit cell)))
    (hpateTotalTargetIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (pateTargetSample index)
            (fun _unit => pateTargetNormalizer index)
            (fun _unit => (1 : Real)))
        l (nhds pateTotalLimit))
    (hpateTotalTreatedIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (pateTreatedSample index)
            (fun _unit => pateTreatedNormalizer index)
            (fun _unit => (1 : Real)))
        l (nhds pateTotalLimit))
    (hpateTotalControlIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (pateControlSample index)
            (fun _unit => pateControlNormalizer index)
            (fun _unit => (1 : Real)))
        l (nhds pateTotalLimit))
    (hpattTotalTargetIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (pattTargetSample index)
            (fun _unit => pattTargetNormalizer index)
            (fun _unit => (1 : Real)))
        l (nhds pattTotalLimit))
    (hpattTotalControlIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (pattControlSample index)
            (fun _unit => pattControlNormalizer index)
            (fun _unit => (1 : Real)))
        l (nhds pattTotalLimit))
    (hpateScaledCellTreatedIndicator :
      ∀ cell, cell ∈ pateCells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (pateTargetSample index)
                  (fun _unit => pateTargetNormalizer index)
                  (scoreCellIndicator
                    (pateDoubleScore (patePropensityScore index)
                      (pateTreatedPrognosticScore index)
                      (pateControlPrognosticScore index)) cell) -
                weightedSampleSum (pateTreatedSample index)
                  (fun _unit => pateTreatedNormalizer index)
                  (scoreCellIndicator
                    (pateDoubleScore (patePropensityScore index)
                      (pateTreatedPrognosticScore index)
                      (pateControlPrognosticScore index)) cell)))
          l (nhds 0))
    (hpateScaledCellControlIndicator :
      ∀ cell, cell ∈ pateCells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (pateTargetSample index)
                  (fun _unit => pateTargetNormalizer index)
                  (scoreCellIndicator
                    (pateDoubleScore (patePropensityScore index)
                      (pateTreatedPrognosticScore index)
                      (pateControlPrognosticScore index)) cell) -
                weightedSampleSum (pateControlSample index)
                  (fun _unit => pateControlNormalizer index)
                  (scoreCellIndicator
                    (pateDoubleScore (patePropensityScore index)
                      (pateTreatedPrognosticScore index)
                      (pateControlPrognosticScore index)) cell)))
          l (nhds 0))
    (hpattScaledCellControlIndicator :
      ∀ cell, cell ∈ pattCells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (pattTargetSample index)
                  (fun _unit => pattTargetNormalizer index)
                  (scoreCellIndicator
                    (pattDoubleScore (pattPropensityScore index)
                      (pattControlPrognosticScore index)) cell) -
                weightedSampleSum (pattControlSample index)
                  (fun _unit => pattControlNormalizer index)
                  (scoreCellIndicator
                    (pattDoubleScore (pattPropensityScore index)
                      (pattControlPrognosticScore index)) cell)))
          l (nhds 0))
    (hpateScaledTotalTreatedIndicator :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (pateTargetSample index)
                (fun _unit => pateTargetNormalizer index)
                (fun _unit => (1 : Real)) -
              weightedSampleSum (pateTreatedSample index)
                (fun _unit => pateTreatedNormalizer index)
                (fun _unit => (1 : Real))))
        l (nhds 0))
    (hpateScaledTotalControlIndicator :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (pateTargetSample index)
                (fun _unit => pateTargetNormalizer index)
                (fun _unit => (1 : Real)) -
              weightedSampleSum (pateControlSample index)
                (fun _unit => pateControlNormalizer index)
                (fun _unit => (1 : Real))))
        l (nhds 0))
    (hpattScaledTotalControlIndicator :
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (pattTargetSample index)
                (fun _unit => pattTargetNormalizer index)
                (fun _unit => (1 : Real)) -
              weightedSampleSum (pattControlSample index)
                (fun _unit => pattControlNormalizer index)
                (fun _unit => (1 : Real))))
        l (nhds 0))
    (hpateTotalLimit : pateTotalLimit ≠ 0)
    (hpattTotalLimit : pattTotalLimit ≠ 0)
    (hpateScoreMeasTargetT :
      ∀ index unit, unit ∈ pateTargetSample index ->
        pateTargetOutcomeT index unit =
          pateTreatedValue index (pateTreatedPrognosticScore index unit))
    (hpateScoreMeasTreated :
      ∀ index unit, unit ∈ pateTreatedSample index ->
        pateTreatedOutcome index unit =
          pateTreatedValue index (pateTreatedPrognosticScore index unit))
    (hpateScoreMeasTargetC :
      ∀ index unit, unit ∈ pateTargetSample index ->
        pateTargetOutcomeC index unit =
          pateControlValue index (pateControlPrognosticScore index unit))
    (hpateScoreMeasControl :
      ∀ index unit, unit ∈ pateControlSample index ->
        pateControlOutcome index unit =
          pateControlValue index (pateControlPrognosticScore index unit))
    (hpattScoreMeasTargetC :
      ∀ index unit, unit ∈ pattTargetSample index ->
        pattTargetControlOutcome index unit =
          pattControlValue index (pattControlPrognosticScore index unit))
    (hpattScoreMeasControl :
      ∀ index unit, unit ∈ pattControlSample index ->
        pattControlOutcome index unit =
          pattControlValue index (pattControlPrognosticScore index unit))
    (hpateTreatedBound :
      ∀ index cell, cell ∈ pateCells ->
        |treatedCellValueOnPATEDoubleScore (pateTreatedValue index) cell| ≤
          pateTreatedEnvelope index)
    (hpateControlBound :
      ∀ index cell, cell ∈ pateCells ->
        |controlCellValueOnPATEDoubleScore (pateControlValue index) cell| ≤
          pateControlEnvelope index)
    (hpattControlBound :
      ∀ index cell, cell ∈ pattCells ->
        |controlCellValueOnPATTDoubleScore (pattControlValue index) cell| ≤
          pattControlEnvelope index)
    (hpateTreatedEnvelope :
      Tendsto pateTreatedEnvelope l (nhds pateTreatedEnvelopeLimit))
    (hpateControlEnvelope :
      Tendsto pateControlEnvelope l (nhds pateControlEnvelopeLimit))
    (hpattControlEnvelope :
      Tendsto pattControlEnvelope l (nhds pattControlEnvelopeLimit)) :
    Tendsto
        (fun index =>
          weightedSampleMeanContrast (pateTargetSample index)
            (fun _unit => pateTargetCommonWeight index)
            (pateTargetOutcomeT index) (pateTargetOutcomeC index) -
          twoArmWeightedMeanContrast (pateTreatedSample index)
            (pateControlSample index)
            (fun _unit => pateTreatedCommonWeight index)
            (fun _unit => pateControlCommonWeight index)
            (pateTreatedOutcome index) (pateControlOutcome index))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleMeanContrast (pateTargetSample index)
              (fun _unit => pateTargetCommonWeight index)
              (pateTargetOutcomeT index) (pateTargetOutcomeC index) -
            twoArmWeightedMeanContrast (pateTreatedSample index)
              (pateControlSample index)
              (fun _unit => pateTreatedCommonWeight index)
              (fun _unit => pateControlCommonWeight index)
              (pateTreatedOutcome index) (pateControlOutcome index)))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          weightedSampleMeanContrast (pattTargetSample index)
            (fun _unit => pattTargetCommonWeight index)
            (pattTreatedTargetOutcome index) (pattTargetControlOutcome index) -
          pattWeightedMeanContrast (pattTargetSample index)
            (pattControlSample index)
            (fun _unit => pattTargetCommonWeight index)
            (fun _unit => pattControlCommonWeight index)
            (pattTreatedTargetOutcome index) (pattControlOutcome index))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleMeanContrast (pattTargetSample index)
              (fun _unit => pattTargetCommonWeight index)
              (pattTreatedTargetOutcome index)
              (pattTargetControlOutcome index) -
            pattWeightedMeanContrast (pattTargetSample index)
              (pattControlSample index)
              (fun _unit => pattTargetCommonWeight index)
              (fun _unit => pattControlCommonWeight index)
              (pattTreatedTargetOutcome index) (pattControlOutcome index)))
        l (nhds 0) := by
  have hpate :
      Tendsto
          (fun index =>
            weightedSampleMeanContrast (pateTargetSample index)
              (fun _unit => pateTargetCommonWeight index)
              (pateTargetOutcomeT index) (pateTargetOutcomeC index) -
            twoArmWeightedMeanContrast (pateTreatedSample index)
              (pateControlSample index)
              (fun _unit => pateTreatedCommonWeight index)
              (fun _unit => pateControlCommonWeight index)
              (pateTreatedOutcome index) (pateControlOutcome index))
          l (nhds 0) ∧
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleMeanContrast (pateTargetSample index)
                (fun _unit => pateTargetCommonWeight index)
                (pateTargetOutcomeT index) (pateTargetOutcomeC index) -
              twoArmWeightedMeanContrast (pateTreatedSample index)
                (pateControlSample index)
                (fun _unit => pateTreatedCommonWeight index)
                (fun _unit => pateControlCommonWeight index)
                (pateTreatedOutcome index) (pateControlOutcome index)))
          l (nhds 0) :=
    tendsto_pateDoubleScoreApprox_error_zero_and_scaled_zero_of_indicator_sums_and_envelopes_constant_weight
      scale pateTargetSample pateTreatedSample pateControlSample pateCells
      pateTargetCommonWeight pateTreatedCommonWeight pateControlCommonWeight
      pateTargetNormalizer pateTreatedNormalizer pateControlNormalizer
      pateTargetOutcomeT pateTargetOutcomeC pateTreatedOutcome
      pateControlOutcome patePropensityScore pateTreatedPrognosticScore
      pateControlPrognosticScore pateTreatedValue pateControlValue
      pateTreatedEnvelope pateControlEnvelope pateTreatedEnvelopeLimit
      pateControlEnvelopeLimit pateCellLimit pateTotalLimit hscale_nonneg
      hpateWeightTarget hpateWeightTreated hpateWeightControl
      hpateNormalizerTarget hpateNormalizerTreated hpateNormalizerControl
      hpateNonemptyTarget hpateNonemptyTreated hpateNonemptyControl
      hpateCoverTarget hpateCoverTreated hpateCoverControl
      hpateMassTarget hpateMassTreated hpateMassControl
      hpateCellTargetIndicator hpateCellTreatedIndicator
      hpateCellControlIndicator hpateTotalTargetIndicator
      hpateTotalTreatedIndicator hpateTotalControlIndicator
      hpateScaledCellTreatedIndicator hpateScaledCellControlIndicator
      hpateScaledTotalTreatedIndicator hpateScaledTotalControlIndicator
      hpateTotalLimit hpateScoreMeasTargetT hpateScoreMeasTreated
      hpateScoreMeasTargetC hpateScoreMeasControl hpateTreatedBound
      hpateControlBound hpateTreatedEnvelope hpateControlEnvelope
  have hpatt :
      Tendsto
          (fun index =>
            weightedSampleMeanContrast (pattTargetSample index)
              (fun _unit => pattTargetCommonWeight index)
              (pattTreatedTargetOutcome index)
              (pattTargetControlOutcome index) -
            pattWeightedMeanContrast (pattTargetSample index)
              (pattControlSample index)
              (fun _unit => pattTargetCommonWeight index)
              (fun _unit => pattControlCommonWeight index)
              (pattTreatedTargetOutcome index) (pattControlOutcome index))
          l (nhds 0) ∧
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleMeanContrast (pattTargetSample index)
                (fun _unit => pattTargetCommonWeight index)
                (pattTreatedTargetOutcome index)
                (pattTargetControlOutcome index) -
              pattWeightedMeanContrast (pattTargetSample index)
                (pattControlSample index)
                (fun _unit => pattTargetCommonWeight index)
                (fun _unit => pattControlCommonWeight index)
                (pattTreatedTargetOutcome index) (pattControlOutcome index)))
          l (nhds 0) :=
    tendsto_pattDoubleScoreApprox_error_zero_and_scaled_zero_of_indicator_sums_and_envelope_constant_weight
      scale pattTargetSample pattControlSample pattCells
      pattTargetCommonWeight pattControlCommonWeight pattTargetNormalizer
      pattControlNormalizer pattTreatedTargetOutcome pattTargetControlOutcome
      pattControlOutcome pattPropensityScore pattControlPrognosticScore
      pattControlValue pattControlEnvelope pattControlEnvelopeLimit
      pattCellLimit pattTotalLimit hscale_nonneg hpattWeightTarget
      hpattWeightControl hpattNormalizerTarget hpattNormalizerControl
      hpattNonemptyTarget hpattNonemptyControl hpattCoverTarget
      hpattCoverControl hpattMassTarget hpattMassControl
      hpattCellTargetIndicator hpattCellControlIndicator
      hpattTotalTargetIndicator hpattTotalControlIndicator
      hpattScaledCellControlIndicator hpattScaledTotalControlIndicator
      hpattTotalLimit hpattScoreMeasTargetC hpattScoreMeasControl
      hpattControlBound hpattControlEnvelope
  exact ⟨hpate.1, hpate.2, hpatt.1, hpatt.2⟩

end WDSM
end Matching
end StatInference
