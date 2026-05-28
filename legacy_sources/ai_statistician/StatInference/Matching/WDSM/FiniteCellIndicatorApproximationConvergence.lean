import StatInference.Matching.WDSM.FiniteCellIndicatorMass
import StatInference.Matching.WDSM.FiniteCellMassApproximationConvergence

/-!
# Finite indicator-sum convergence to WDSM approximation convergence

This module composes the bounded score-cell indicator representation with the
finite cell-mass approximation theorems.  The remaining stochastic inputs are
now ordinary weighted sums of real `0/1` indicators, exactly the shape needed
for survey-weighted LLN/CLT or empirical-process ports.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Unit PropensityCell TreatedProgCell ControlProgCell PATTProgCell : Type*}
  [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
  [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]
variable {l : Filter Index}

/--
PATE double-score approximation convergence from convergence of weighted
joint-score indicator sums and envelope convergence.
-/
theorem tendsto_pateDoubleScoreApprox_error_zero_of_indicator_and_envelopes
    (targetSample treatedSample controlSample : Index -> Finset Unit)
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
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
    (massLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
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
        scoreCellMass (targetSample index) (targetWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassTreated :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (treatedSample index) (treatedWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (controlSample index) (controlWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hindicatorTarget :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (targetSample index) (targetWeight index)
              (scoreCellIndicator
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (massLimit cell)))
    (hindicatorTreated :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (treatedSample index) (treatedWeight index)
              (scoreCellIndicator
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (massLimit cell)))
    (hindicatorControl :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (controlSample index) (controlWeight index)
              (scoreCellIndicator
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (massLimit cell)))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
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
          (targetWeight index) (targetOutcomeT index)
          (targetOutcomeC index) -
        twoArmWeightedMeanContrast (treatedSample index)
          (controlSample index) (treatedWeight index)
          (controlWeight index) (treatedOutcome index)
          (controlOutcome index))
      l (nhds 0) := by
  exact tendsto_pateDoubleScoreApprox_error_zero_of_cell_mass_and_envelopes
    targetSample treatedSample controlSample cells targetWeight treatedWeight
    controlWeight targetOutcomeT targetOutcomeC treatedOutcome controlOutcome
    propensityScore treatedPrognosticScore controlPrognosticScore
    treatedValue controlValue treatedEnvelope controlEnvelope
    treatedEnvelopeLimit controlEnvelopeLimit massLimit hcoverTarget
    hcoverTreated hcoverControl hmassTarget hmassTreated hmassControl
    (fun cell hcell =>
      tendsto_pateDoubleScoreCellMass_of_tendsto_indicator
        targetSample targetWeight propensityScore treatedPrognosticScore
        controlPrognosticScore cell (massLimit cell)
        (hindicatorTarget cell hcell))
    (fun cell hcell =>
      tendsto_pateDoubleScoreCellMass_of_tendsto_indicator
        treatedSample treatedWeight propensityScore treatedPrognosticScore
        controlPrognosticScore cell (massLimit cell)
        (hindicatorTreated cell hcell))
    (fun cell hcell =>
      tendsto_pateDoubleScoreCellMass_of_tendsto_indicator
        controlSample controlWeight propensityScore treatedPrognosticScore
        controlPrognosticScore cell (massLimit cell)
        (hindicatorControl cell hcell))
    htotalLimit hscoreMeasTargetT hscoreMeasTreated hscoreMeasTargetC
    hscoreMeasControl htreated_bound hcontrol_bound htreatedEnvelope
    hcontrolEnvelope

/--
PATT double-score approximation convergence from convergence of weighted
joint-score indicator sums and envelope convergence.
-/
theorem tendsto_pattDoubleScoreApprox_error_zero_of_indicator_and_envelope
    (targetSample controlSample : Index -> Finset Unit)
    (cells : Finset (PropensityCell × PATTProgCell))
    (targetWeight controlWeight : Index -> Unit -> Real)
    (treatedTargetOutcome targetControlOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (controlValue : Index -> PATTProgCell -> Real)
    (controlEnvelope : Index -> Real)
    (controlEnvelopeLimit : Real)
    (massLimit : PropensityCell × PATTProgCell -> Real)
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
        scoreCellMass (targetSample index) (targetWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (controlSample index) (controlWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hindicatorTarget :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (targetSample index) (targetWeight index)
              (scoreCellIndicator
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (massLimit cell)))
    (hindicatorControl :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (controlSample index) (controlWeight index)
              (scoreCellIndicator
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (massLimit cell)))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
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
          (targetWeight index) (treatedTargetOutcome index)
          (targetControlOutcome index) -
        pattWeightedMeanContrast (targetSample index) (controlSample index)
          (targetWeight index) (controlWeight index)
          (treatedTargetOutcome index) (controlOutcome index))
      l (nhds 0) := by
  exact tendsto_pattDoubleScoreApprox_error_zero_of_cell_mass_and_envelope
    targetSample controlSample cells targetWeight controlWeight
    treatedTargetOutcome targetControlOutcome controlOutcome propensityScore
    controlPrognosticScore controlValue controlEnvelope controlEnvelopeLimit
    massLimit hcoverTarget hcoverControl hmassTarget hmassControl
    (fun cell hcell =>
      tendsto_pattDoubleScoreCellMass_of_tendsto_indicator
        targetSample targetWeight propensityScore controlPrognosticScore
        cell (massLimit cell) (hindicatorTarget cell hcell))
    (fun cell hcell =>
      tendsto_pattDoubleScoreCellMass_of_tendsto_indicator
        controlSample controlWeight propensityScore controlPrognosticScore
        cell (massLimit cell) (hindicatorControl cell hcell))
    htotalLimit hscoreMeasTargetC hscoreMeasControl hcontrol_bound
    hcontrolEnvelope

/--
Scaled PATE double-score approximation convergence from convergence of
weighted joint-score indicator sums and scaled target-arm indicator-sum
differences.
-/
theorem tendsto_scaled_pateDoubleScoreApprox_error_zero_of_indicator_and_envelopes
    (scale : Index -> Real)
    (targetSample treatedSample controlSample : Index -> Finset Unit)
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
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
    (massLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
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
        scoreCellMass (targetSample index) (targetWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassTreated :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (treatedSample index) (treatedWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (controlSample index) (controlWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hindicatorTarget :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (targetSample index) (targetWeight index)
              (scoreCellIndicator
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (massLimit cell)))
    (hindicatorTreated :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (treatedSample index) (treatedWeight index)
              (scoreCellIndicator
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (massLimit cell)))
    (hindicatorControl :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (controlSample index) (controlWeight index)
              (scoreCellIndicator
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (massLimit cell)))
    (hscaledIndicatorTreated :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (targetSample index) (targetWeight index)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index)) cell) -
                weightedSampleSum (treatedSample index) (treatedWeight index)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index)) cell)))
          l (nhds 0))
    (hscaledIndicatorControl :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (targetSample index) (targetWeight index)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index)) cell) -
                weightedSampleSum (controlSample index) (controlWeight index)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index)) cell)))
          l (nhds 0))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
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
            (targetWeight index) (targetOutcomeT index)
            (targetOutcomeC index) -
          twoArmWeightedMeanContrast (treatedSample index)
            (controlSample index) (treatedWeight index)
            (controlWeight index) (treatedOutcome index)
            (controlOutcome index)))
      l (nhds 0) := by
  exact tendsto_scaled_pateDoubleScoreApprox_error_zero_of_cell_mass_and_envelopes
    scale targetSample treatedSample controlSample cells targetWeight
    treatedWeight controlWeight targetOutcomeT targetOutcomeC treatedOutcome
    controlOutcome propensityScore treatedPrognosticScore
    controlPrognosticScore treatedValue controlValue treatedEnvelope
    controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit massLimit
    hscale_nonneg hcoverTarget hcoverTreated hcoverControl hmassTarget
    hmassTreated hmassControl
    (fun cell hcell =>
      tendsto_pateDoubleScoreCellMass_of_tendsto_indicator
        targetSample targetWeight propensityScore treatedPrognosticScore
        controlPrognosticScore cell (massLimit cell)
        (hindicatorTarget cell hcell))
    (fun cell hcell =>
      tendsto_pateDoubleScoreCellMass_of_tendsto_indicator
        treatedSample treatedWeight propensityScore treatedPrognosticScore
        controlPrognosticScore cell (massLimit cell)
        (hindicatorTreated cell hcell))
    (fun cell hcell =>
      tendsto_pateDoubleScoreCellMass_of_tendsto_indicator
        controlSample controlWeight propensityScore treatedPrognosticScore
        controlPrognosticScore cell (massLimit cell)
        (hindicatorControl cell hcell))
    (fun cell hcell =>
      tendsto_scaled_scoreCellMass_sub_of_tendsto_scaled_weightedSampleSum_indicator_sub
        scale targetSample treatedSample targetWeight treatedWeight
        (fun index =>
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index) (controlPrognosticScore index))
        (fun index =>
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index) (controlPrognosticScore index))
        cell (hscaledIndicatorTreated cell hcell))
    (fun cell hcell =>
      tendsto_scaled_scoreCellMass_sub_of_tendsto_scaled_weightedSampleSum_indicator_sub
        scale targetSample controlSample targetWeight controlWeight
        (fun index =>
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index) (controlPrognosticScore index))
        (fun index =>
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index) (controlPrognosticScore index))
        cell (hscaledIndicatorControl cell hcell))
    htotalLimit hscoreMeasTargetT hscoreMeasTreated hscoreMeasTargetC
    hscoreMeasControl htreated_bound hcontrol_bound htreatedEnvelope
    hcontrolEnvelope

/--
Scaled PATT double-score approximation convergence from convergence of
weighted joint-score indicator sums and scaled target-control indicator-sum
differences.
-/
theorem tendsto_scaled_pattDoubleScoreApprox_error_zero_of_indicator_and_envelope
    (scale : Index -> Real)
    (targetSample controlSample : Index -> Finset Unit)
    (cells : Finset (PropensityCell × PATTProgCell))
    (targetWeight controlWeight : Index -> Unit -> Real)
    (treatedTargetOutcome targetControlOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (controlValue : Index -> PATTProgCell -> Real)
    (controlEnvelope : Index -> Real)
    (controlEnvelopeLimit : Real)
    (massLimit : PropensityCell × PATTProgCell -> Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
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
        scoreCellMass (targetSample index) (targetWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (controlSample index) (controlWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hindicatorTarget :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (targetSample index) (targetWeight index)
              (scoreCellIndicator
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (massLimit cell)))
    (hindicatorControl :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (controlSample index) (controlWeight index)
              (scoreCellIndicator
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (massLimit cell)))
    (hscaledIndicatorControl :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (targetSample index) (targetWeight index)
                  (scoreCellIndicator
                    (pattDoubleScore (propensityScore index)
                      (controlPrognosticScore index)) cell) -
                weightedSampleSum (controlSample index) (controlWeight index)
                  (scoreCellIndicator
                    (pattDoubleScore (propensityScore index)
                      (controlPrognosticScore index)) cell)))
          l (nhds 0))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
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
            (targetWeight index) (treatedTargetOutcome index)
            (targetControlOutcome index) -
          pattWeightedMeanContrast (targetSample index) (controlSample index)
            (targetWeight index) (controlWeight index)
            (treatedTargetOutcome index) (controlOutcome index)))
      l (nhds 0) := by
  exact tendsto_scaled_pattDoubleScoreApprox_error_zero_of_cell_mass_and_envelope
    scale targetSample controlSample cells targetWeight controlWeight
    treatedTargetOutcome targetControlOutcome controlOutcome propensityScore
    controlPrognosticScore controlValue controlEnvelope controlEnvelopeLimit
    massLimit hscale_nonneg hcoverTarget hcoverControl hmassTarget
    hmassControl
    (fun cell hcell =>
      tendsto_pattDoubleScoreCellMass_of_tendsto_indicator
        targetSample targetWeight propensityScore controlPrognosticScore
        cell (massLimit cell) (hindicatorTarget cell hcell))
    (fun cell hcell =>
      tendsto_pattDoubleScoreCellMass_of_tendsto_indicator
        controlSample controlWeight propensityScore controlPrognosticScore
        cell (massLimit cell) (hindicatorControl cell hcell))
    (fun cell hcell =>
      tendsto_scaled_scoreCellMass_sub_of_tendsto_scaled_weightedSampleSum_indicator_sub
        scale targetSample controlSample targetWeight controlWeight
        (fun index =>
          pattDoubleScore (propensityScore index)
            (controlPrognosticScore index))
        (fun index =>
          pattDoubleScore (propensityScore index)
            (controlPrognosticScore index))
        cell (hscaledIndicatorControl cell hcell))
    htotalLimit hscoreMeasTargetC hscoreMeasControl hcontrol_bound
    hcontrolEnvelope

end WDSM
end Matching
end StatInference
