import StatInference.Matching.WDSM.ProspectiveScoreCellShareConvergence
import StatInference.Matching.WDSM.ProspectiveCountRatioConvergence
import StatInference.Matching.WDSM.DiscreteDoubleScoreApproximateBalancingConvergence

/-!
# Prospective/common-weight count-ratio approximation convergence for WDSM

This module composes the prospective finite count-ratio score-share convergence
bridge with the existing WDSM double-score approximation convergence theorems.
It lets a prospective sampling argument feed ordinary cell-count ratio
convergence directly into PATE/PATT approximation negligibility.
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

theorem tendsto_pateDoubleScoreApprox_error_zero_of_card_ratio_and_envelopes_constant_weight
    (targetSample treatedSample controlSample : Index -> Finset Unit)
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (targetCommonWeight treatedCommonWeight controlCommonWeight :
      Index -> Real)
    (targetOutcomeT targetOutcomeC treatedOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (treatedValue : Index -> TreatedProgCell -> Real)
    (controlValue : Index -> ControlProgCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (treatedEnvelopeLimit controlEnvelopeLimit : Real)
    (hweightTarget : ∀ index, targetCommonWeight index ≠ 0)
    (hweightTreated : ∀ index, treatedCommonWeight index ≠ 0)
    (hweightControl : ∀ index, controlCommonWeight index ≠ 0)
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
          l (nhds 0))
    (hcellControl :
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
          l (nhds 0))
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
  have htreatedL1 :
      Tendsto
        (fun index =>
          l1PATEDoubleScoreShareDistance cells
            (targetSample index) (treatedSample index)
            (fun _unit => targetCommonWeight index)
            (fun _unit => treatedCommonWeight index)
            (propensityScore index) (treatedPrognosticScore index)
            (controlPrognosticScore index))
        l (nhds 0) :=
    tendsto_l1PATEDoubleScoreShareDistance_zero_of_card_ratio_cellwise_constant_weight
      cells targetSample treatedSample targetCommonWeight treatedCommonWeight
      propensityScore treatedPrognosticScore controlPrognosticScore
      hweightTarget hweightTreated hnonemptyTarget hnonemptyTreated
      hcellTreated
  have hcontrolL1 :
      Tendsto
        (fun index =>
          l1PATEDoubleScoreShareDistance cells
            (targetSample index) (controlSample index)
            (fun _unit => targetCommonWeight index)
            (fun _unit => controlCommonWeight index)
            (propensityScore index) (treatedPrognosticScore index)
            (controlPrognosticScore index))
        l (nhds 0) :=
    tendsto_l1PATEDoubleScoreShareDistance_zero_of_card_ratio_cellwise_constant_weight
      cells targetSample controlSample targetCommonWeight controlCommonWeight
      propensityScore treatedPrognosticScore controlPrognosticScore
      hweightTarget hweightControl hnonemptyTarget hnonemptyControl
      hcellControl
  exact tendsto_pateDoubleScoreApprox_error_zero_of_l1_and_envelopes
    targetSample treatedSample controlSample (fun _index => cells)
    (fun index _unit => targetCommonWeight index)
    (fun index _unit => treatedCommonWeight index)
    (fun index _unit => controlCommonWeight index)
    targetOutcomeT targetOutcomeC treatedOutcome controlOutcome
    propensityScore treatedPrognosticScore controlPrognosticScore
    treatedValue controlValue treatedEnvelope controlEnvelope
    treatedEnvelopeLimit controlEnvelopeLimit hcoverTarget hcoverTreated
    hcoverControl hmassTarget hmassTreated hmassControl hscoreMeasTargetT
    hscoreMeasTreated hscoreMeasTargetC hscoreMeasControl htreated_bound
    hcontrol_bound htreatedEnvelope hcontrolEnvelope htreatedL1 hcontrolL1

/--
Direct ordinary PATE approximation convergence from weighted indicator-sum
reference LLNs and ordinary weighted indicator-sum differences.
-/
theorem tendsto_pateDoubleScoreApprox_error_zero_of_weighted_indicator_reference_and_difference_constant_weight
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
    (hnormalizerTarget : ∀ index, targetNormalizer index ≠ 0)
    (hnormalizerTreated : ∀ index, treatedNormalizer index ≠ 0)
    (hnormalizerControl : ∀ index, controlNormalizer index ≠ 0)
    (hweightTarget : ∀ index, targetCommonWeight index ≠ 0)
    (hweightTreated : ∀ index, treatedCommonWeight index ≠ 0)
    (hweightControl : ∀ index, controlCommonWeight index ≠ 0)
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
            (fun _unit => targetNormalizer index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalTreatedIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (treatedSample index)
            (fun _unit => treatedNormalizer index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalControlIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (controlSample index)
            (fun _unit => controlNormalizer index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (hcellTargetTreatedDiffIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (targetSample index)
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
                    (controlPrognosticScore index)) cell))
          l (nhds 0))
    (hcellTargetControlDiffIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (targetSample index)
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
                    (controlPrognosticScore index)) cell))
          l (nhds 0))
    (htotalTargetTreatedDiffIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (targetSample index)
              (fun _unit => targetNormalizer index)
              (fun _unit => (1 : Real)) -
            weightedSampleSum (treatedSample index)
              (fun _unit => treatedNormalizer index)
              (fun _unit => (1 : Real)))
        l (nhds 0))
    (htotalTargetControlDiffIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (targetSample index)
              (fun _unit => targetNormalizer index)
              (fun _unit => (1 : Real)) -
            weightedSampleSum (controlSample index)
              (fun _unit => controlNormalizer index)
              (fun _unit => (1 : Real)))
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
      l (nhds 0) := by
  have htreatedL1 :
      Tendsto
        (fun index =>
          l1PATEDoubleScoreShareDistance cells
            (targetSample index) (treatedSample index)
            (fun _unit => targetCommonWeight index)
            (fun _unit => treatedCommonWeight index)
            (propensityScore index) (treatedPrognosticScore index)
            (controlPrognosticScore index))
        l (nhds 0) :=
    tendsto_l1PATEDoubleScoreShareDistance_zero_of_weighted_indicator_reference_and_difference_constant_weight
      cells targetNormalizer treatedNormalizer targetSample treatedSample
      targetCommonWeight treatedCommonWeight propensityScore
      treatedPrognosticScore controlPrognosticScore cellLimit totalLimit
      hnormalizerTarget hnormalizerTreated hweightTarget hweightTreated
      hnonemptyTarget hnonemptyTreated hcellTreatedIndicator
      htotalTargetIndicator htotalTreatedIndicator
      hcellTargetTreatedDiffIndicator htotalTargetTreatedDiffIndicator
      htotalLimit
  have hcontrolL1 :
      Tendsto
        (fun index =>
          l1PATEDoubleScoreShareDistance cells
            (targetSample index) (controlSample index)
            (fun _unit => targetCommonWeight index)
            (fun _unit => controlCommonWeight index)
            (propensityScore index) (treatedPrognosticScore index)
            (controlPrognosticScore index))
        l (nhds 0) :=
    tendsto_l1PATEDoubleScoreShareDistance_zero_of_weighted_indicator_reference_and_difference_constant_weight
      cells targetNormalizer controlNormalizer targetSample controlSample
      targetCommonWeight controlCommonWeight propensityScore
      treatedPrognosticScore controlPrognosticScore cellLimit totalLimit
      hnormalizerTarget hnormalizerControl hweightTarget hweightControl
      hnonemptyTarget hnonemptyControl hcellControlIndicator
      htotalTargetIndicator htotalControlIndicator
      hcellTargetControlDiffIndicator htotalTargetControlDiffIndicator
      htotalLimit
  exact tendsto_pateDoubleScoreApprox_error_zero_of_l1_and_envelopes
    targetSample treatedSample controlSample (fun _index => cells)
    (fun index _unit => targetCommonWeight index)
    (fun index _unit => treatedCommonWeight index)
    (fun index _unit => controlCommonWeight index)
    targetOutcomeT targetOutcomeC treatedOutcome controlOutcome
    propensityScore treatedPrognosticScore controlPrognosticScore
    treatedValue controlValue treatedEnvelope controlEnvelope
    treatedEnvelopeLimit controlEnvelopeLimit hcoverTarget hcoverTreated
    hcoverControl hmassTarget hmassTreated hmassControl hscoreMeasTargetT
    hscoreMeasTreated hscoreMeasTargetC hscoreMeasControl htreated_bound
    hcontrol_bound htreatedEnvelope hcontrolEnvelope htreatedL1 hcontrolL1

theorem tendsto_scaled_pateDoubleScoreApprox_error_zero_of_card_ratio_and_envelopes_constant_weight
    (scale : Index -> Real)
    (targetSample treatedSample controlSample : Index -> Finset Unit)
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (targetCommonWeight treatedCommonWeight controlCommonWeight :
      Index -> Real)
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
    (hweightTarget : ∀ index, targetCommonWeight index ≠ 0)
    (hweightTreated : ∀ index, treatedCommonWeight index ≠ 0)
    (hweightControl : ∀ index, controlCommonWeight index ≠ 0)
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
          l (nhds 0))
    (hcellControl :
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
          l (nhds 0))
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
  have htreatedL1 :
      Tendsto
        (fun index =>
          scale index *
            l1PATEDoubleScoreShareDistance cells
              (targetSample index) (treatedSample index)
              (fun _unit => targetCommonWeight index)
              (fun _unit => treatedCommonWeight index)
              (propensityScore index) (treatedPrognosticScore index)
              (controlPrognosticScore index))
        l (nhds 0) :=
    tendsto_scaled_l1PATEDoubleScoreShareDistance_zero_of_card_ratio_cellwise_constant_weight
      cells scale targetSample treatedSample targetCommonWeight
      treatedCommonWeight propensityScore treatedPrognosticScore
      controlPrognosticScore hscale_nonneg hweightTarget hweightTreated
      hnonemptyTarget hnonemptyTreated hcellTreated
  have hcontrolL1 :
      Tendsto
        (fun index =>
          scale index *
            l1PATEDoubleScoreShareDistance cells
              (targetSample index) (controlSample index)
              (fun _unit => targetCommonWeight index)
              (fun _unit => controlCommonWeight index)
              (propensityScore index) (treatedPrognosticScore index)
              (controlPrognosticScore index))
        l (nhds 0) :=
    tendsto_scaled_l1PATEDoubleScoreShareDistance_zero_of_card_ratio_cellwise_constant_weight
      cells scale targetSample controlSample targetCommonWeight
      controlCommonWeight propensityScore treatedPrognosticScore
      controlPrognosticScore hscale_nonneg hweightTarget hweightControl
      hnonemptyTarget hnonemptyControl hcellControl
  exact tendsto_scaled_pateDoubleScoreApprox_error_zero_of_scaled_l1_and_envelopes
    scale targetSample treatedSample controlSample (fun _index => cells)
    (fun index _unit => targetCommonWeight index)
    (fun index _unit => treatedCommonWeight index)
    (fun index _unit => controlCommonWeight index)
    targetOutcomeT targetOutcomeC treatedOutcome controlOutcome
    propensityScore treatedPrognosticScore controlPrognosticScore
    treatedValue controlValue treatedEnvelope controlEnvelope
    treatedEnvelopeLimit controlEnvelopeLimit hscale_nonneg hcoverTarget
    hcoverTreated hcoverControl hmassTarget hmassTreated hmassControl
    hscoreMeasTargetT hscoreMeasTreated hscoreMeasTargetC
    hscoreMeasControl htreated_bound hcontrol_bound htreatedEnvelope
    hcontrolEnvelope htreatedL1 hcontrolL1

/--
Direct scaled PATE approximation convergence from weighted indicator-sum
reference LLNs and scaled weighted indicator-sum differences.
-/
theorem tendsto_scaled_pateDoubleScoreApprox_error_zero_of_weighted_indicator_reference_and_difference_constant_weight
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
    (hnormalizerTarget : ∀ index, targetNormalizer index ≠ 0)
    (hnormalizerTreated : ∀ index, treatedNormalizer index ≠ 0)
    (hnormalizerControl : ∀ index, controlNormalizer index ≠ 0)
    (hweightTarget : ∀ index, targetCommonWeight index ≠ 0)
    (hweightTreated : ∀ index, treatedCommonWeight index ≠ 0)
    (hweightControl : ∀ index, controlCommonWeight index ≠ 0)
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
            (fun _unit => targetNormalizer index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalTreatedIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (treatedSample index)
            (fun _unit => treatedNormalizer index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalControlIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (controlSample index)
            (fun _unit => controlNormalizer index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (hscaledCellTargetTreatedDiffIndicator :
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
    (hscaledCellTargetControlDiffIndicator :
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
    (hscaledTotalTargetTreatedDiffIndicator :
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
    (hscaledTotalTargetControlDiffIndicator :
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
      l (nhds 0) := by
  have htreatedL1 :
      Tendsto
        (fun index =>
          scale index *
            l1PATEDoubleScoreShareDistance cells
              (targetSample index) (treatedSample index)
              (fun _unit => targetCommonWeight index)
              (fun _unit => treatedCommonWeight index)
              (propensityScore index) (treatedPrognosticScore index)
              (controlPrognosticScore index))
        l (nhds 0) :=
    tendsto_scaled_l1PATEDoubleScoreShareDistance_zero_of_weighted_indicator_reference_and_difference_constant_weight
      cells scale targetNormalizer treatedNormalizer targetSample
      treatedSample targetCommonWeight treatedCommonWeight propensityScore
      treatedPrognosticScore controlPrognosticScore cellLimit totalLimit
      hscale_nonneg hnormalizerTarget hnormalizerTreated hweightTarget
      hweightTreated hnonemptyTarget hnonemptyTreated hcellTreatedIndicator
      htotalTargetIndicator htotalTreatedIndicator
      hscaledCellTargetTreatedDiffIndicator
      hscaledTotalTargetTreatedDiffIndicator htotalLimit
  have hcontrolL1 :
      Tendsto
        (fun index =>
          scale index *
            l1PATEDoubleScoreShareDistance cells
              (targetSample index) (controlSample index)
              (fun _unit => targetCommonWeight index)
              (fun _unit => controlCommonWeight index)
              (propensityScore index) (treatedPrognosticScore index)
              (controlPrognosticScore index))
        l (nhds 0) :=
    tendsto_scaled_l1PATEDoubleScoreShareDistance_zero_of_weighted_indicator_reference_and_difference_constant_weight
      cells scale targetNormalizer controlNormalizer targetSample
      controlSample targetCommonWeight controlCommonWeight propensityScore
      treatedPrognosticScore controlPrognosticScore cellLimit totalLimit
      hscale_nonneg hnormalizerTarget hnormalizerControl hweightTarget
      hweightControl hnonemptyTarget hnonemptyControl hcellControlIndicator
      htotalTargetIndicator htotalControlIndicator
      hscaledCellTargetControlDiffIndicator
      hscaledTotalTargetControlDiffIndicator htotalLimit
  exact tendsto_scaled_pateDoubleScoreApprox_error_zero_of_scaled_l1_and_envelopes
    scale targetSample treatedSample controlSample (fun _index => cells)
    (fun index _unit => targetCommonWeight index)
    (fun index _unit => treatedCommonWeight index)
    (fun index _unit => controlCommonWeight index)
    targetOutcomeT targetOutcomeC treatedOutcome controlOutcome
    propensityScore treatedPrognosticScore controlPrognosticScore
    treatedValue controlValue treatedEnvelope controlEnvelope
    treatedEnvelopeLimit controlEnvelopeLimit hscale_nonneg hcoverTarget
    hcoverTreated hcoverControl hmassTarget hmassTreated hmassControl
    hscoreMeasTargetT hscoreMeasTreated hscoreMeasTargetC
    hscoreMeasControl htreated_bound hcontrol_bound htreatedEnvelope
    hcontrolEnvelope htreatedL1 hcontrolL1

/--
Direct PATE approximation convergence at both ordinary and scaled rates from
weighted indicator-sum reference LLNs and weighted indicator-sum differences.
-/
theorem tendsto_pateDoubleScoreApprox_error_zero_and_scaled_zero_of_weighted_indicator_reference_and_difference_constant_weight
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
    (hnormalizerTarget : ∀ index, targetNormalizer index ≠ 0)
    (hnormalizerTreated : ∀ index, treatedNormalizer index ≠ 0)
    (hnormalizerControl : ∀ index, controlNormalizer index ≠ 0)
    (hweightTarget : ∀ index, targetCommonWeight index ≠ 0)
    (hweightTreated : ∀ index, treatedCommonWeight index ≠ 0)
    (hweightControl : ∀ index, controlCommonWeight index ≠ 0)
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
            (fun _unit => targetNormalizer index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalTreatedIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (treatedSample index)
            (fun _unit => treatedNormalizer index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalControlIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (controlSample index)
            (fun _unit => controlNormalizer index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (hcellTargetTreatedDiffIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (targetSample index)
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
                    (controlPrognosticScore index)) cell))
          l (nhds 0))
    (hcellTargetControlDiffIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (targetSample index)
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
                    (controlPrognosticScore index)) cell))
          l (nhds 0))
    (htotalTargetTreatedDiffIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (targetSample index)
              (fun _unit => targetNormalizer index)
              (fun _unit => (1 : Real)) -
            weightedSampleSum (treatedSample index)
              (fun _unit => treatedNormalizer index)
              (fun _unit => (1 : Real)))
        l (nhds 0))
    (htotalTargetControlDiffIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (targetSample index)
              (fun _unit => targetNormalizer index)
              (fun _unit => (1 : Real)) -
            weightedSampleSum (controlSample index)
              (fun _unit => controlNormalizer index)
              (fun _unit => (1 : Real)))
        l (nhds 0))
    (hscaledCellTargetTreatedDiffIndicator :
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
    (hscaledCellTargetControlDiffIndicator :
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
    (hscaledTotalTargetTreatedDiffIndicator :
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
    (hscaledTotalTargetControlDiffIndicator :
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
      tendsto_pateDoubleScoreApprox_error_zero_of_weighted_indicator_reference_and_difference_constant_weight
        targetSample treatedSample controlSample cells targetCommonWeight
        treatedCommonWeight controlCommonWeight targetNormalizer
        treatedNormalizer controlNormalizer targetOutcomeT targetOutcomeC
        treatedOutcome controlOutcome propensityScore treatedPrognosticScore
        controlPrognosticScore treatedValue controlValue treatedEnvelope
        controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit cellLimit
        totalLimit hnormalizerTarget hnormalizerTreated hnormalizerControl
        hweightTarget hweightTreated hweightControl hnonemptyTarget
        hnonemptyTreated hnonemptyControl hcoverTarget hcoverTreated
        hcoverControl hmassTarget hmassTreated hmassControl
        hcellTreatedIndicator hcellControlIndicator htotalTargetIndicator
        htotalTreatedIndicator htotalControlIndicator
        hcellTargetTreatedDiffIndicator hcellTargetControlDiffIndicator
        htotalTargetTreatedDiffIndicator htotalTargetControlDiffIndicator
        htotalLimit hscoreMeasTargetT hscoreMeasTreated hscoreMeasTargetC
        hscoreMeasControl htreated_bound hcontrol_bound htreatedEnvelope
        hcontrolEnvelope
  · exact
      tendsto_scaled_pateDoubleScoreApprox_error_zero_of_weighted_indicator_reference_and_difference_constant_weight
        scale targetSample treatedSample controlSample cells targetCommonWeight
        treatedCommonWeight controlCommonWeight targetNormalizer
        treatedNormalizer controlNormalizer targetOutcomeT targetOutcomeC
        treatedOutcome controlOutcome propensityScore treatedPrognosticScore
        controlPrognosticScore treatedValue controlValue treatedEnvelope
        controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit cellLimit
        totalLimit hscale_nonneg hnormalizerTarget hnormalizerTreated
        hnormalizerControl hweightTarget hweightTreated hweightControl
        hnonemptyTarget hnonemptyTreated hnonemptyControl hcoverTarget
        hcoverTreated hcoverControl hmassTarget hmassTreated hmassControl
        hcellTreatedIndicator hcellControlIndicator htotalTargetIndicator
        htotalTreatedIndicator htotalControlIndicator
        hscaledCellTargetTreatedDiffIndicator
        hscaledCellTargetControlDiffIndicator
        hscaledTotalTargetTreatedDiffIndicator
        hscaledTotalTargetControlDiffIndicator htotalLimit
        hscoreMeasTargetT hscoreMeasTreated hscoreMeasTargetC
        hscoreMeasControl htreated_bound hcontrol_bound htreatedEnvelope
        hcontrolEnvelope

theorem tendsto_pattDoubleScoreApprox_error_zero_of_card_ratio_and_envelope_constant_weight
    (targetSample controlSample : Index -> Finset Unit)
    (cells : Finset (PropensityCell × PATTProgCell))
    (targetCommonWeight controlCommonWeight : Index -> Real)
    (treatedTargetOutcome targetControlOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (controlValue : Index -> PATTProgCell -> Real)
    (controlEnvelope : Index -> Real)
    (controlEnvelopeLimit : Real)
    (hweightTarget : ∀ index, targetCommonWeight index ≠ 0)
    (hweightControl : ∀ index, controlCommonWeight index ≠ 0)
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
          l (nhds 0))
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
  have hcontrolL1 :
      Tendsto
        (fun index =>
          l1PATTDoubleScoreShareDistance cells
            (targetSample index) (controlSample index)
            (fun _unit => targetCommonWeight index)
            (fun _unit => controlCommonWeight index)
            (propensityScore index) (controlPrognosticScore index))
        l (nhds 0) :=
    tendsto_l1PATTDoubleScoreShareDistance_zero_of_card_ratio_cellwise_constant_weight
      cells targetSample controlSample targetCommonWeight controlCommonWeight
      propensityScore controlPrognosticScore hweightTarget hweightControl
      hnonemptyTarget hnonemptyControl hcellControl
  exact tendsto_pattDoubleScoreApprox_error_zero_of_l1_and_envelope
    targetSample controlSample (fun _index => cells)
    (fun index _unit => targetCommonWeight index)
    (fun index _unit => controlCommonWeight index)
    treatedTargetOutcome targetControlOutcome controlOutcome propensityScore
    controlPrognosticScore controlValue controlEnvelope controlEnvelopeLimit
    hcoverTarget hcoverControl hmassTarget hmassControl hscoreMeasTargetC
    hscoreMeasControl hcontrol_bound hcontrolEnvelope hcontrolL1

/--
Direct ordinary PATT approximation convergence from weighted indicator-sum
reference LLNs and ordinary weighted indicator-sum differences.
-/
theorem tendsto_pattDoubleScoreApprox_error_zero_of_weighted_indicator_reference_and_difference_constant_weight
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
    (hnormalizerTarget : ∀ index, targetNormalizer index ≠ 0)
    (hnormalizerControl : ∀ index, controlNormalizer index ≠ 0)
    (hweightTarget : ∀ index, targetCommonWeight index ≠ 0)
    (hweightControl : ∀ index, controlCommonWeight index ≠ 0)
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
            (fun _unit => targetNormalizer index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalControlIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (controlSample index)
            (fun _unit => controlNormalizer index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (hcellTargetControlDiffIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (targetSample index)
                (fun _unit => targetNormalizer index)
                (scoreCellIndicator
                  (pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index)) cell) -
              weightedSampleSum (controlSample index)
                (fun _unit => controlNormalizer index)
                (scoreCellIndicator
                  (pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index)) cell))
          l (nhds 0))
    (htotalTargetControlDiffIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (targetSample index)
              (fun _unit => targetNormalizer index)
              (fun _unit => (1 : Real)) -
            weightedSampleSum (controlSample index)
              (fun _unit => controlNormalizer index)
              (fun _unit => (1 : Real)))
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
      l (nhds 0) := by
  have hcontrolL1 :
      Tendsto
        (fun index =>
          l1PATTDoubleScoreShareDistance cells
            (targetSample index) (controlSample index)
            (fun _unit => targetCommonWeight index)
            (fun _unit => controlCommonWeight index)
            (propensityScore index) (controlPrognosticScore index))
        l (nhds 0) :=
    tendsto_l1PATTDoubleScoreShareDistance_zero_of_weighted_indicator_reference_and_difference_constant_weight
      cells targetNormalizer controlNormalizer targetSample controlSample
      targetCommonWeight controlCommonWeight propensityScore
      controlPrognosticScore cellLimit totalLimit hnormalizerTarget
      hnormalizerControl hweightTarget hweightControl hnonemptyTarget
      hnonemptyControl hcellControlIndicator htotalTargetIndicator
      htotalControlIndicator hcellTargetControlDiffIndicator
      htotalTargetControlDiffIndicator htotalLimit
  exact tendsto_pattDoubleScoreApprox_error_zero_of_l1_and_envelope
    targetSample controlSample (fun _index => cells)
    (fun index _unit => targetCommonWeight index)
    (fun index _unit => controlCommonWeight index)
    treatedTargetOutcome targetControlOutcome controlOutcome propensityScore
    controlPrognosticScore controlValue controlEnvelope controlEnvelopeLimit
    hcoverTarget hcoverControl hmassTarget hmassControl hscoreMeasTargetC
    hscoreMeasControl hcontrol_bound hcontrolEnvelope hcontrolL1

theorem tendsto_scaled_pattDoubleScoreApprox_error_zero_of_card_ratio_and_envelope_constant_weight
    (scale : Index -> Real)
    (targetSample controlSample : Index -> Finset Unit)
    (cells : Finset (PropensityCell × PATTProgCell))
    (targetCommonWeight controlCommonWeight : Index -> Real)
    (treatedTargetOutcome targetControlOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (controlValue : Index -> PATTProgCell -> Real)
    (controlEnvelope : Index -> Real)
    (controlEnvelopeLimit : Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hweightTarget : ∀ index, targetCommonWeight index ≠ 0)
    (hweightControl : ∀ index, controlCommonWeight index ≠ 0)
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
          l (nhds 0))
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
  have hcontrolL1 :
      Tendsto
        (fun index =>
          scale index *
            l1PATTDoubleScoreShareDistance cells
              (targetSample index) (controlSample index)
              (fun _unit => targetCommonWeight index)
              (fun _unit => controlCommonWeight index)
              (propensityScore index) (controlPrognosticScore index))
        l (nhds 0) :=
    tendsto_scaled_l1PATTDoubleScoreShareDistance_zero_of_card_ratio_cellwise_constant_weight
      cells scale targetSample controlSample targetCommonWeight
      controlCommonWeight propensityScore controlPrognosticScore
      hscale_nonneg hweightTarget hweightControl hnonemptyTarget
      hnonemptyControl hcellControl
  exact tendsto_scaled_pattDoubleScoreApprox_error_zero_of_scaled_l1_and_envelope
    scale targetSample controlSample (fun _index => cells)
    (fun index _unit => targetCommonWeight index)
    (fun index _unit => controlCommonWeight index)
    treatedTargetOutcome targetControlOutcome controlOutcome propensityScore
    controlPrognosticScore controlValue controlEnvelope controlEnvelopeLimit
    hscale_nonneg hcoverTarget hcoverControl hmassTarget hmassControl
    hscoreMeasTargetC hscoreMeasControl hcontrol_bound hcontrolEnvelope
    hcontrolL1

/--
Direct scaled PATT approximation convergence from weighted indicator-sum
reference LLNs and scaled weighted indicator-sum differences.
-/
theorem tendsto_scaled_pattDoubleScoreApprox_error_zero_of_weighted_indicator_reference_and_difference_constant_weight
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
    (hnormalizerTarget : ∀ index, targetNormalizer index ≠ 0)
    (hnormalizerControl : ∀ index, controlNormalizer index ≠ 0)
    (hweightTarget : ∀ index, targetCommonWeight index ≠ 0)
    (hweightControl : ∀ index, controlCommonWeight index ≠ 0)
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
            (fun _unit => targetNormalizer index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalControlIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (controlSample index)
            (fun _unit => controlNormalizer index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (hscaledCellTargetControlDiffIndicator :
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
    (hscaledTotalTargetControlDiffIndicator :
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
      l (nhds 0) := by
  have hcontrolL1 :
      Tendsto
        (fun index =>
          scale index *
            l1PATTDoubleScoreShareDistance cells
              (targetSample index) (controlSample index)
              (fun _unit => targetCommonWeight index)
              (fun _unit => controlCommonWeight index)
              (propensityScore index) (controlPrognosticScore index))
        l (nhds 0) :=
    tendsto_scaled_l1PATTDoubleScoreShareDistance_zero_of_weighted_indicator_reference_and_difference_constant_weight
      cells scale targetNormalizer controlNormalizer targetSample
      controlSample targetCommonWeight controlCommonWeight propensityScore
      controlPrognosticScore cellLimit totalLimit hscale_nonneg
      hnormalizerTarget hnormalizerControl hweightTarget hweightControl
      hnonemptyTarget hnonemptyControl hcellControlIndicator
      htotalTargetIndicator htotalControlIndicator
      hscaledCellTargetControlDiffIndicator
      hscaledTotalTargetControlDiffIndicator htotalLimit
  exact tendsto_scaled_pattDoubleScoreApprox_error_zero_of_scaled_l1_and_envelope
    scale targetSample controlSample (fun _index => cells)
    (fun index _unit => targetCommonWeight index)
    (fun index _unit => controlCommonWeight index)
    treatedTargetOutcome targetControlOutcome controlOutcome propensityScore
    controlPrognosticScore controlValue controlEnvelope controlEnvelopeLimit
    hscale_nonneg hcoverTarget hcoverControl hmassTarget hmassControl
    hscoreMeasTargetC hscoreMeasControl hcontrol_bound hcontrolEnvelope
    hcontrolL1

/--
Direct PATT approximation convergence at both ordinary and scaled rates from
weighted indicator-sum reference LLNs and weighted indicator-sum differences.
-/
theorem tendsto_pattDoubleScoreApprox_error_zero_and_scaled_zero_of_weighted_indicator_reference_and_difference_constant_weight
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
    (hnormalizerTarget : ∀ index, targetNormalizer index ≠ 0)
    (hnormalizerControl : ∀ index, controlNormalizer index ≠ 0)
    (hweightTarget : ∀ index, targetCommonWeight index ≠ 0)
    (hweightControl : ∀ index, controlCommonWeight index ≠ 0)
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
            (fun _unit => targetNormalizer index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (htotalControlIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (controlSample index)
            (fun _unit => controlNormalizer index)
            (fun _unit => (1 : Real)))
        l (nhds totalLimit))
    (hcellTargetControlDiffIndicator :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (targetSample index)
                (fun _unit => targetNormalizer index)
                (scoreCellIndicator
                  (pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index)) cell) -
              weightedSampleSum (controlSample index)
                (fun _unit => controlNormalizer index)
                (scoreCellIndicator
                  (pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index)) cell))
          l (nhds 0))
    (htotalTargetControlDiffIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (targetSample index)
              (fun _unit => targetNormalizer index)
              (fun _unit => (1 : Real)) -
            weightedSampleSum (controlSample index)
              (fun _unit => controlNormalizer index)
              (fun _unit => (1 : Real)))
        l (nhds 0))
    (hscaledCellTargetControlDiffIndicator :
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
    (hscaledTotalTargetControlDiffIndicator :
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
            pattWeightedMeanContrast (targetSample index)
              (controlSample index)
              (fun _unit => targetCommonWeight index)
              (fun _unit => controlCommonWeight index)
              (treatedTargetOutcome index) (controlOutcome index)))
        l (nhds 0) := by
  constructor
  · exact
      tendsto_pattDoubleScoreApprox_error_zero_of_weighted_indicator_reference_and_difference_constant_weight
        targetSample controlSample cells targetCommonWeight
        controlCommonWeight targetNormalizer controlNormalizer
        treatedTargetOutcome targetControlOutcome controlOutcome
        propensityScore controlPrognosticScore controlValue controlEnvelope
        controlEnvelopeLimit cellLimit totalLimit hnormalizerTarget
        hnormalizerControl hweightTarget hweightControl hnonemptyTarget
        hnonemptyControl hcoverTarget hcoverControl hmassTarget hmassControl
        hcellControlIndicator htotalTargetIndicator htotalControlIndicator
        hcellTargetControlDiffIndicator htotalTargetControlDiffIndicator
        htotalLimit hscoreMeasTargetC hscoreMeasControl hcontrol_bound
        hcontrolEnvelope
  · exact
      tendsto_scaled_pattDoubleScoreApprox_error_zero_of_weighted_indicator_reference_and_difference_constant_weight
        scale targetSample controlSample cells targetCommonWeight
        controlCommonWeight targetNormalizer controlNormalizer
        treatedTargetOutcome targetControlOutcome controlOutcome
        propensityScore controlPrognosticScore controlValue controlEnvelope
        controlEnvelopeLimit cellLimit totalLimit hscale_nonneg
        hnormalizerTarget hnormalizerControl hweightTarget hweightControl
        hnonemptyTarget hnonemptyControl hcoverTarget hcoverControl
        hmassTarget hmassControl hcellControlIndicator htotalTargetIndicator
        htotalControlIndicator hscaledCellTargetControlDiffIndicator
        hscaledTotalTargetControlDiffIndicator htotalLimit hscoreMeasTargetC
        hscoreMeasControl hcontrol_bound hcontrolEnvelope

/--
Direct paired PATE/PATT approximation convergence at ordinary and scaled rates
from weighted indicator-sum reference LLNs and weighted indicator-sum
differences.
-/
theorem tendsto_pate_pattDoubleScoreApprox_error_zero_and_scaled_zero_of_weighted_indicator_reference_and_difference_constant_weight
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
    (hpateCellTargetTreatedDiffIndicator :
      ∀ cell, cell ∈ pateCells ->
        Tendsto
          (fun index =>
            weightedSampleSum (pateTargetSample index)
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
                    (pateControlPrognosticScore index)) cell))
          l (nhds 0))
    (hpateCellTargetControlDiffIndicator :
      ∀ cell, cell ∈ pateCells ->
        Tendsto
          (fun index =>
            weightedSampleSum (pateTargetSample index)
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
                    (pateControlPrognosticScore index)) cell))
          l (nhds 0))
    (hpattCellTargetControlDiffIndicator :
      ∀ cell, cell ∈ pattCells ->
        Tendsto
          (fun index =>
            weightedSampleSum (pattTargetSample index)
                (fun _unit => pattTargetNormalizer index)
                (scoreCellIndicator
                  (pattDoubleScore (pattPropensityScore index)
                    (pattControlPrognosticScore index)) cell) -
              weightedSampleSum (pattControlSample index)
                (fun _unit => pattControlNormalizer index)
                (scoreCellIndicator
                  (pattDoubleScore (pattPropensityScore index)
                    (pattControlPrognosticScore index)) cell))
          l (nhds 0))
    (hpateTotalTargetTreatedDiffIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (pateTargetSample index)
              (fun _unit => pateTargetNormalizer index)
              (fun _unit => (1 : Real)) -
            weightedSampleSum (pateTreatedSample index)
              (fun _unit => pateTreatedNormalizer index)
              (fun _unit => (1 : Real)))
        l (nhds 0))
    (hpateTotalTargetControlDiffIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (pateTargetSample index)
              (fun _unit => pateTargetNormalizer index)
              (fun _unit => (1 : Real)) -
            weightedSampleSum (pateControlSample index)
              (fun _unit => pateControlNormalizer index)
              (fun _unit => (1 : Real)))
        l (nhds 0))
    (hpattTotalTargetControlDiffIndicator :
      Tendsto
        (fun index =>
          weightedSampleSum (pattTargetSample index)
              (fun _unit => pattTargetNormalizer index)
              (fun _unit => (1 : Real)) -
            weightedSampleSum (pattControlSample index)
              (fun _unit => pattControlNormalizer index)
              (fun _unit => (1 : Real)))
        l (nhds 0))
    (hpateScaledCellTargetTreatedDiffIndicator :
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
    (hpateScaledCellTargetControlDiffIndicator :
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
    (hpattScaledCellTargetControlDiffIndicator :
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
    (hpateScaledTotalTargetTreatedDiffIndicator :
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
    (hpateScaledTotalTargetControlDiffIndicator :
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
    (hpattScaledTotalTargetControlDiffIndicator :
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
    tendsto_pateDoubleScoreApprox_error_zero_and_scaled_zero_of_weighted_indicator_reference_and_difference_constant_weight
      scale pateTargetSample pateTreatedSample pateControlSample pateCells
      pateTargetCommonWeight pateTreatedCommonWeight pateControlCommonWeight
      pateTargetNormalizer pateTreatedNormalizer pateControlNormalizer
      pateTargetOutcomeT pateTargetOutcomeC pateTreatedOutcome
      pateControlOutcome patePropensityScore pateTreatedPrognosticScore
      pateControlPrognosticScore pateTreatedValue pateControlValue
      pateTreatedEnvelope pateControlEnvelope pateTreatedEnvelopeLimit
      pateControlEnvelopeLimit pateCellLimit pateTotalLimit hscale_nonneg
      hpateNormalizerTarget hpateNormalizerTreated hpateNormalizerControl
      hpateWeightTarget hpateWeightTreated hpateWeightControl
      hpateNonemptyTarget hpateNonemptyTreated hpateNonemptyControl
      hpateCoverTarget hpateCoverTreated hpateCoverControl
      hpateMassTarget hpateMassTreated hpateMassControl
      hpateCellTreatedIndicator hpateCellControlIndicator
      hpateTotalTargetIndicator hpateTotalTreatedIndicator
      hpateTotalControlIndicator hpateCellTargetTreatedDiffIndicator
      hpateCellTargetControlDiffIndicator
      hpateTotalTargetTreatedDiffIndicator
      hpateTotalTargetControlDiffIndicator
      hpateScaledCellTargetTreatedDiffIndicator
      hpateScaledCellTargetControlDiffIndicator
      hpateScaledTotalTargetTreatedDiffIndicator
      hpateScaledTotalTargetControlDiffIndicator hpateTotalLimit
      hpateScoreMeasTargetT hpateScoreMeasTreated hpateScoreMeasTargetC
      hpateScoreMeasControl hpateTreatedBound hpateControlBound
      hpateTreatedEnvelope hpateControlEnvelope
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
    tendsto_pattDoubleScoreApprox_error_zero_and_scaled_zero_of_weighted_indicator_reference_and_difference_constant_weight
      scale pattTargetSample pattControlSample pattCells
      pattTargetCommonWeight pattControlCommonWeight pattTargetNormalizer
      pattControlNormalizer pattTreatedTargetOutcome pattTargetControlOutcome
      pattControlOutcome pattPropensityScore pattControlPrognosticScore
      pattControlValue pattControlEnvelope pattControlEnvelopeLimit
      pattCellLimit pattTotalLimit hscale_nonneg hpattNormalizerTarget
      hpattNormalizerControl hpattWeightTarget hpattWeightControl
      hpattNonemptyTarget hpattNonemptyControl hpattCoverTarget
      hpattCoverControl hpattMassTarget hpattMassControl
      hpattCellControlIndicator hpattTotalTargetIndicator
      hpattTotalControlIndicator hpattCellTargetControlDiffIndicator
      hpattTotalTargetControlDiffIndicator
      hpattScaledCellTargetControlDiffIndicator
      hpattScaledTotalTargetControlDiffIndicator hpattTotalLimit
      hpattScoreMeasTargetC hpattScoreMeasControl hpattControlBound
      hpattControlEnvelope
  exact ⟨hpate.1, hpate.2, hpatt.1, hpatt.2⟩

end WDSM
end Matching
end StatInference
