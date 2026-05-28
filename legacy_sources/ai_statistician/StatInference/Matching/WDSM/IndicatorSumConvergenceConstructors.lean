import StatInference.Matching.WDSM.IndicatorSumConvergenceInterfaces

/-!
# Constructors for indicator-sum convergence bridges

This module turns the finite indicator-sum approximation convergence theorems
into concrete bridge records.  The bridge fields isolate the empirical-process
inputs as weighted joint-score indicator LLNs and scaled indicator-sum
differences.
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
Concrete PATE indicator-sum bridge from finite cell validity, envelope
convergence, and target/treated/control weighted indicator LLNs.
-/
noncomputable def pateDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelopes
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
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real) :
    PATEDoubleScoreIndicatorSumConvergenceBridge where
  eventual_finite_conditions :=
    (∀ index unit, unit ∈ targetSample index ->
      pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index)
        (controlPrognosticScore index) unit ∈ cells) ∧
    (∀ index unit, unit ∈ treatedSample index ->
      pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index)
        (controlPrognosticScore index) unit ∈ cells) ∧
    (∀ index unit, unit ∈ controlSample index ->
      pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index)
        (controlPrognosticScore index) unit ∈ cells) ∧
    (∀ index cell, cell ∈ cells ->
      scoreCellMass (targetSample index) (targetWeight index)
        (pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index)) cell ≠ 0) ∧
    (∀ index cell, cell ∈ cells ->
      scoreCellMass (treatedSample index) (treatedWeight index)
        (pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index)) cell ≠ 0) ∧
    (∀ index cell, cell ∈ cells ->
      scoreCellMass (controlSample index) (controlWeight index)
        (pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index)) cell ≠ 0) ∧
    (∀ index unit, unit ∈ targetSample index ->
      targetOutcomeT index unit =
        treatedValue index (treatedPrognosticScore index unit)) ∧
    (∀ index unit, unit ∈ treatedSample index ->
      treatedOutcome index unit =
        treatedValue index (treatedPrognosticScore index unit)) ∧
    (∀ index unit, unit ∈ targetSample index ->
      targetOutcomeC index unit =
        controlValue index (controlPrognosticScore index unit)) ∧
    (∀ index unit, unit ∈ controlSample index ->
      controlOutcome index unit =
        controlValue index (controlPrognosticScore index unit)) ∧
    (∀ index cell, cell ∈ cells ->
      |treatedCellValueOnPATEDoubleScore (treatedValue index) cell| ≤
        treatedEnvelope index) ∧
    (∀ index cell, cell ∈ cells ->
      |controlCellValueOnPATEDoubleScore (controlValue index) cell| ≤
        controlEnvelope index)
  envelope_convergence :=
    Tendsto treatedEnvelope l (nhds treatedEnvelopeLimit) ∧
      Tendsto controlEnvelope l (nhds controlEnvelopeLimit)
  weighted_indicator_sum_lln :=
    (∀ cell, cell ∈ cells ->
      Tendsto
        (fun index =>
          weightedSampleSum (targetSample index) (targetWeight index)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell))
        l (nhds (massLimit cell))) ∧
    (∀ cell, cell ∈ cells ->
      Tendsto
        (fun index =>
          weightedSampleSum (treatedSample index) (treatedWeight index)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell))
        l (nhds (massLimit cell))) ∧
    (∀ cell, cell ∈ cells ->
      Tendsto
        (fun index =>
          weightedSampleSum (controlSample index) (controlWeight index)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell))
        l (nhds (massLimit cell))) ∧
    (∑ cell ∈ cells, massLimit cell) ≠ 0
  pate_double_score_approximation_negligible :=
    Tendsto
      (fun index =>
        weightedSampleMeanContrast (targetSample index)
          (targetWeight index) (targetOutcomeT index)
          (targetOutcomeC index) -
        twoArmWeightedMeanContrast (treatedSample index)
          (controlSample index) (treatedWeight index)
          (controlWeight index) (treatedOutcome index)
          (controlOutcome index))
      l (nhds 0)
  bridge := by
    intro hfinite henvelope hindicator
    rcases hfinite with
      ⟨hcoverTarget, hcoverTreated, hcoverControl, hmassTarget,
        hmassTreated, hmassControl, hscoreMeasTargetT,
        hscoreMeasTreated, hscoreMeasTargetC, hscoreMeasControl,
        htreated_bound, hcontrol_bound⟩
    rcases hindicator with
      ⟨hindicatorTarget, hindicatorTreated, hindicatorControl,
        htotalLimit⟩
    exact
      tendsto_pateDoubleScoreApprox_error_zero_of_indicator_and_envelopes
        targetSample treatedSample controlSample cells targetWeight
        treatedWeight controlWeight targetOutcomeT targetOutcomeC
        treatedOutcome controlOutcome propensityScore treatedPrognosticScore
        controlPrognosticScore treatedValue controlValue treatedEnvelope
        controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit massLimit
        hcoverTarget hcoverTreated hcoverControl hmassTarget hmassTreated
        hmassControl hindicatorTarget hindicatorTreated hindicatorControl
        htotalLimit hscoreMeasTargetT hscoreMeasTreated hscoreMeasTargetC
        hscoreMeasControl htreated_bound hcontrol_bound henvelope.1
        henvelope.2

/--
Concrete scaled PATE indicator-sum bridge from finite validity, envelope
convergence, target/treated/control LLNs, and scaled target-arm indicator
differences.
-/
noncomputable def scaledPATEDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelopes
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
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real) :
    ScaledPATEDoubleScoreIndicatorSumConvergenceBridge where
  eventual_finite_conditions :=
    (∀ index, 0 ≤ scale index) ∧
    (∀ index unit, unit ∈ targetSample index ->
      pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index)
        (controlPrognosticScore index) unit ∈ cells) ∧
    (∀ index unit, unit ∈ treatedSample index ->
      pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index)
        (controlPrognosticScore index) unit ∈ cells) ∧
    (∀ index unit, unit ∈ controlSample index ->
      pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index)
        (controlPrognosticScore index) unit ∈ cells) ∧
    (∀ index cell, cell ∈ cells ->
      scoreCellMass (targetSample index) (targetWeight index)
        (pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index)) cell ≠ 0) ∧
    (∀ index cell, cell ∈ cells ->
      scoreCellMass (treatedSample index) (treatedWeight index)
        (pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index)) cell ≠ 0) ∧
    (∀ index cell, cell ∈ cells ->
      scoreCellMass (controlSample index) (controlWeight index)
        (pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index)) cell ≠ 0) ∧
    (∀ index unit, unit ∈ targetSample index ->
      targetOutcomeT index unit =
        treatedValue index (treatedPrognosticScore index unit)) ∧
    (∀ index unit, unit ∈ treatedSample index ->
      treatedOutcome index unit =
        treatedValue index (treatedPrognosticScore index unit)) ∧
    (∀ index unit, unit ∈ targetSample index ->
      targetOutcomeC index unit =
        controlValue index (controlPrognosticScore index unit)) ∧
    (∀ index unit, unit ∈ controlSample index ->
      controlOutcome index unit =
        controlValue index (controlPrognosticScore index unit)) ∧
    (∀ index cell, cell ∈ cells ->
      |treatedCellValueOnPATEDoubleScore (treatedValue index) cell| ≤
        treatedEnvelope index) ∧
    (∀ index cell, cell ∈ cells ->
      |controlCellValueOnPATEDoubleScore (controlValue index) cell| ≤
        controlEnvelope index)
  envelope_convergence :=
    Tendsto treatedEnvelope l (nhds treatedEnvelopeLimit) ∧
      Tendsto controlEnvelope l (nhds controlEnvelopeLimit)
  weighted_indicator_sum_lln :=
    (∀ cell, cell ∈ cells ->
      Tendsto
        (fun index =>
          weightedSampleSum (targetSample index) (targetWeight index)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell))
        l (nhds (massLimit cell))) ∧
    (∀ cell, cell ∈ cells ->
      Tendsto
        (fun index =>
          weightedSampleSum (treatedSample index) (treatedWeight index)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell))
        l (nhds (massLimit cell))) ∧
    (∀ cell, cell ∈ cells ->
      Tendsto
        (fun index =>
          weightedSampleSum (controlSample index) (controlWeight index)
            (scoreCellIndicator
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell))
        l (nhds (massLimit cell))) ∧
    (∑ cell ∈ cells, massLimit cell) ≠ 0
  scaled_weighted_indicator_sum_difference_clt :=
    (∀ cell, cell ∈ cells ->
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
        l (nhds 0)) ∧
    (∀ cell, cell ∈ cells ->
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
  scaled_pate_double_score_approximation_negligible :=
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
      l (nhds 0)
  bridge := by
    intro hfinite henvelope hlln hclt
    rcases hfinite with
      ⟨hscale_nonneg, hcoverTarget, hcoverTreated, hcoverControl,
        hmassTarget, hmassTreated, hmassControl, hscoreMeasTargetT,
        hscoreMeasTreated, hscoreMeasTargetC, hscoreMeasControl,
        htreated_bound, hcontrol_bound⟩
    rcases hlln with
      ⟨hindicatorTarget, hindicatorTreated, hindicatorControl,
        htotalLimit⟩
    rcases hclt with
      ⟨hscaledIndicatorTreated, hscaledIndicatorControl⟩
    exact
      tendsto_scaled_pateDoubleScoreApprox_error_zero_of_indicator_and_envelopes
        scale targetSample treatedSample controlSample cells targetWeight
        treatedWeight controlWeight targetOutcomeT targetOutcomeC
        treatedOutcome controlOutcome propensityScore treatedPrognosticScore
        controlPrognosticScore treatedValue controlValue treatedEnvelope
        controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit massLimit
        hscale_nonneg hcoverTarget hcoverTreated hcoverControl hmassTarget
        hmassTreated hmassControl hindicatorTarget hindicatorTreated
        hindicatorControl hscaledIndicatorTreated hscaledIndicatorControl
        htotalLimit hscoreMeasTargetT hscoreMeasTreated hscoreMeasTargetC
        hscoreMeasControl htreated_bound hcontrol_bound henvelope.1
        henvelope.2

/--
Concrete PATT indicator-sum bridge from finite cell validity, envelope
convergence, and target/control weighted indicator LLNs.
-/
noncomputable def pattDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelope
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
    (massLimit : PropensityCell × PATTProgCell -> Real) :
    PATTDoubleScoreIndicatorSumConvergenceBridge where
  eventual_finite_conditions :=
    (∀ index unit, unit ∈ targetSample index ->
      pattDoubleScore (propensityScore index)
        (controlPrognosticScore index) unit ∈ cells) ∧
    (∀ index unit, unit ∈ controlSample index ->
      pattDoubleScore (propensityScore index)
        (controlPrognosticScore index) unit ∈ cells) ∧
    (∀ index cell, cell ∈ cells ->
      scoreCellMass (targetSample index) (targetWeight index)
        (pattDoubleScore (propensityScore index)
          (controlPrognosticScore index)) cell ≠ 0) ∧
    (∀ index cell, cell ∈ cells ->
      scoreCellMass (controlSample index) (controlWeight index)
        (pattDoubleScore (propensityScore index)
          (controlPrognosticScore index)) cell ≠ 0) ∧
    (∀ index unit, unit ∈ targetSample index ->
      targetControlOutcome index unit =
        controlValue index (controlPrognosticScore index unit)) ∧
    (∀ index unit, unit ∈ controlSample index ->
      controlOutcome index unit =
        controlValue index (controlPrognosticScore index unit)) ∧
    (∀ index cell, cell ∈ cells ->
      |controlCellValueOnPATTDoubleScore (controlValue index) cell| ≤
        controlEnvelope index)
  envelope_convergence :=
    Tendsto controlEnvelope l (nhds controlEnvelopeLimit)
  weighted_indicator_sum_lln :=
    (∀ cell, cell ∈ cells ->
      Tendsto
        (fun index =>
          weightedSampleSum (targetSample index) (targetWeight index)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell))
        l (nhds (massLimit cell))) ∧
    (∀ cell, cell ∈ cells ->
      Tendsto
        (fun index =>
          weightedSampleSum (controlSample index) (controlWeight index)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell))
        l (nhds (massLimit cell))) ∧
    (∑ cell ∈ cells, massLimit cell) ≠ 0
  patt_double_score_approximation_negligible :=
    Tendsto
      (fun index =>
        weightedSampleMeanContrast (targetSample index)
          (targetWeight index) (treatedTargetOutcome index)
          (targetControlOutcome index) -
        pattWeightedMeanContrast (targetSample index) (controlSample index)
          (targetWeight index) (controlWeight index)
          (treatedTargetOutcome index) (controlOutcome index))
      l (nhds 0)
  bridge := by
    intro hfinite henvelope hindicator
    rcases hfinite with
      ⟨hcoverTarget, hcoverControl, hmassTarget, hmassControl,
        hscoreMeasTargetC, hscoreMeasControl, hcontrol_bound⟩
    rcases hindicator with
      ⟨hindicatorTarget, hindicatorControl, htotalLimit⟩
    exact
      tendsto_pattDoubleScoreApprox_error_zero_of_indicator_and_envelope
        targetSample controlSample cells targetWeight controlWeight
        treatedTargetOutcome targetControlOutcome controlOutcome
        propensityScore controlPrognosticScore controlValue controlEnvelope
        controlEnvelopeLimit massLimit hcoverTarget hcoverControl
        hmassTarget hmassControl hindicatorTarget hindicatorControl
        htotalLimit hscoreMeasTargetC hscoreMeasControl hcontrol_bound
        henvelope

/--
Concrete scaled PATT indicator-sum bridge from finite validity, envelope
convergence, target/control LLNs, and scaled target-control indicator
differences.
-/
noncomputable def scaledPATTDoubleScoreIndicatorSumConvergenceBridge_of_indicator_and_envelope
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
    (massLimit : PropensityCell × PATTProgCell -> Real) :
    ScaledPATTDoubleScoreIndicatorSumConvergenceBridge where
  eventual_finite_conditions :=
    (∀ index, 0 ≤ scale index) ∧
    (∀ index unit, unit ∈ targetSample index ->
      pattDoubleScore (propensityScore index)
        (controlPrognosticScore index) unit ∈ cells) ∧
    (∀ index unit, unit ∈ controlSample index ->
      pattDoubleScore (propensityScore index)
        (controlPrognosticScore index) unit ∈ cells) ∧
    (∀ index cell, cell ∈ cells ->
      scoreCellMass (targetSample index) (targetWeight index)
        (pattDoubleScore (propensityScore index)
          (controlPrognosticScore index)) cell ≠ 0) ∧
    (∀ index cell, cell ∈ cells ->
      scoreCellMass (controlSample index) (controlWeight index)
        (pattDoubleScore (propensityScore index)
          (controlPrognosticScore index)) cell ≠ 0) ∧
    (∀ index unit, unit ∈ targetSample index ->
      targetControlOutcome index unit =
        controlValue index (controlPrognosticScore index unit)) ∧
    (∀ index unit, unit ∈ controlSample index ->
      controlOutcome index unit =
        controlValue index (controlPrognosticScore index unit)) ∧
    (∀ index cell, cell ∈ cells ->
      |controlCellValueOnPATTDoubleScore (controlValue index) cell| ≤
        controlEnvelope index)
  envelope_convergence :=
    Tendsto controlEnvelope l (nhds controlEnvelopeLimit)
  weighted_indicator_sum_lln :=
    (∀ cell, cell ∈ cells ->
      Tendsto
        (fun index =>
          weightedSampleSum (targetSample index) (targetWeight index)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell))
        l (nhds (massLimit cell))) ∧
    (∀ cell, cell ∈ cells ->
      Tendsto
        (fun index =>
          weightedSampleSum (controlSample index) (controlWeight index)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell))
        l (nhds (massLimit cell))) ∧
    (∑ cell ∈ cells, massLimit cell) ≠ 0
  scaled_weighted_indicator_sum_difference_clt :=
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
        l (nhds 0)
  scaled_patt_double_score_approximation_negligible :=
    Tendsto
      (fun index =>
        scale index *
          (weightedSampleMeanContrast (targetSample index)
            (targetWeight index) (treatedTargetOutcome index)
            (targetControlOutcome index) -
          pattWeightedMeanContrast (targetSample index) (controlSample index)
            (targetWeight index) (controlWeight index)
            (treatedTargetOutcome index) (controlOutcome index)))
      l (nhds 0)
  bridge := by
    intro hfinite henvelope hlln hclt
    rcases hfinite with
      ⟨hscale_nonneg, hcoverTarget, hcoverControl, hmassTarget, hmassControl,
        hscoreMeasTargetC, hscoreMeasControl, hcontrol_bound⟩
    rcases hlln with
      ⟨hindicatorTarget, hindicatorControl, htotalLimit⟩
    exact
      tendsto_scaled_pattDoubleScoreApprox_error_zero_of_indicator_and_envelope
        scale targetSample controlSample cells targetWeight controlWeight
        treatedTargetOutcome targetControlOutcome controlOutcome
        propensityScore controlPrognosticScore controlValue controlEnvelope
        controlEnvelopeLimit massLimit hscale_nonneg hcoverTarget
        hcoverControl hmassTarget hmassControl hindicatorTarget
        hindicatorControl hclt htotalLimit hscoreMeasTargetC
        hscoreMeasControl hcontrol_bound henvelope

end WDSM
end Matching
end StatInference
