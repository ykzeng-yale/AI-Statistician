import StatInference.Matching.WDSM.DiscreteDoubleScoreEffectShareIdentification
import StatInference.Matching.WDSM.DiscreteDoubleScoreRetrospectiveSurveyMean
import StatInference.Matching.WDSM.DiscreteDoubleScoreProspectiveSurveyMean

/-!
# Double-score survey-weighted effect-share identification

This module composes the finite double-score effect-share aggregate with the
retrospective/prospective selected-sample survey-weight recovery theorems.
It records that the selected weighted contrast and the target contrast share
the same target-share double-score candidate effect aggregate.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Unit PropensityCell TreatedProgCell ControlProgCell : Type*}
  [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
  [DecidableEq ControlProgCell]

/--
Retrospective selected-sample PATE double-score effect-share identification.
-/
theorem retrospectivePATEDoubleScoreWeight_common_effect_share_identification
    (targetSample selectedSample : Finset Unit)
    (cells : Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (baseWeight : Unit -> Real)
    (targetOutcomeT targetOutcomeC selectedOutcomeT selectedOutcomeC :
      Unit -> Real)
    (propensityScore : Unit -> PropensityCell)
    (treatedPrognosticScore : Unit -> TreatedProgCell)
    (controlPrognosticScore : Unit -> ControlProgCell)
    (treatment : Unit -> Prop) [DecidablePred treatment]
    (samplingIfTreated samplingIfControl :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (hcoverTarget :
      ∀ unit, unit ∈ targetSample ->
        pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore unit ∈ cells)
    (hcoverSelected :
      ∀ unit, unit ∈ selectedSample ->
        pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore unit ∈ cells)
    (hmassTarget :
      ∀ cell, cell ∈ cells ->
        scoreCellMass targetSample baseWeight
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore) cell ≠ 0)
    (hsamplingTreated :
      ∀ cell, cell ∈ cells -> samplingIfTreated cell ≠ 0)
    (hsamplingControl :
      ∀ cell, cell ∈ cells -> samplingIfControl cell ≠ 0)
    (htreatedMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (selectedSample.filter treatment) baseWeight
            (pateDoubleScore propensityScore treatedPrognosticScore
              controlPrognosticScore) cell =
          samplingIfTreated cell *
            scoreCellMass (targetSample.filter treatment) baseWeight
              (pateDoubleScore propensityScore treatedPrognosticScore
                controlPrognosticScore) cell)
    (hcontrolMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (selectedSample.filter (fun unit => ¬ treatment unit))
            baseWeight
            (pateDoubleScore propensityScore treatedPrognosticScore
              controlPrognosticScore) cell =
          samplingIfControl cell *
            scoreCellMass
              (targetSample.filter (fun unit => ¬ treatment unit))
              baseWeight
              (pateDoubleScore propensityScore treatedPrognosticScore
                controlPrognosticScore) cell)
    (hscoreMeasTargetT :
      ∀ unit, unit ∈ targetSample ->
        targetOutcomeT unit = treatedValue (treatedPrognosticScore unit))
    (hscoreMeasSelectedT :
      ∀ unit, unit ∈ selectedSample ->
        selectedOutcomeT unit = treatedValue (treatedPrognosticScore unit))
    (hscoreMeasTargetC :
      ∀ unit, unit ∈ targetSample ->
        targetOutcomeC unit = controlValue (controlPrognosticScore unit))
    (hscoreMeasSelectedC :
      ∀ unit, unit ∈ selectedSample ->
        selectedOutcomeC unit = controlValue (controlPrognosticScore unit)) :
    weightedSampleMeanContrast targetSample baseWeight
        targetOutcomeT targetOutcomeC =
        candidateCellMeanEffectShareAggregate targetSample cells baseWeight
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore)
          (treatedCellValueOnPATEDoubleScore treatedValue)
          (controlCellValueOnPATEDoubleScore controlValue) ∧
      weightedSampleMeanContrast selectedSample
          (retrospectiveInverseSamplingWeight baseWeight
            (pateDoubleScore propensityScore treatedPrognosticScore
              controlPrognosticScore)
            treatment samplingIfTreated samplingIfControl)
          selectedOutcomeT selectedOutcomeC =
        candidateCellMeanEffectShareAggregate targetSample cells baseWeight
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore)
          (treatedCellValueOnPATEDoubleScore treatedValue)
          (controlCellValueOnPATEDoubleScore controlValue) ∧
      weightedSampleMeanContrast targetSample baseWeight
          targetOutcomeT targetOutcomeC =
        weightedSampleMeanContrast selectedSample
          (retrospectiveInverseSamplingWeight baseWeight
            (pateDoubleScore propensityScore treatedPrognosticScore
              controlPrognosticScore)
            treatment samplingIfTreated samplingIfControl)
          selectedOutcomeT selectedOutcomeC := by
  have htarget :
      candidateCellMeanEffectShareAggregate targetSample cells baseWeight
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore)
          (treatedCellValueOnPATEDoubleScore treatedValue)
          (controlCellValueOnPATEDoubleScore controlValue) =
        weightedSampleMeanContrast targetSample baseWeight
          targetOutcomeT targetOutcomeC :=
    candidateCellMeanEffectShareAggregate_eq_weightedSampleMeanContrast_of_eq
      targetSample cells baseWeight targetOutcomeT targetOutcomeC
      (pateDoubleScore propensityScore treatedPrognosticScore
        controlPrognosticScore)
      (treatedCellValueOnPATEDoubleScore treatedValue)
      (controlCellValueOnPATEDoubleScore controlValue)
      hcoverTarget hmassTarget
      (fun cell hcell =>
        (scoreCellMean_eq_const_of_eq_on_cell
          targetSample baseWeight targetOutcomeT
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore)
          cell (treatedCellValueOnPATEDoubleScore treatedValue cell)
          (hmassTarget cell hcell)
          (fun unit hunit hscore => by
            rw [treated_scoreMeasurable_pateDoubleScore propensityScore
              treatedPrognosticScore controlPrognosticScore targetOutcomeT
              treatedValue targetSample hscoreMeasTargetT unit hunit,
              hscore])).symm)
      (fun cell hcell =>
        (scoreCellMean_eq_const_of_eq_on_cell
          targetSample baseWeight targetOutcomeC
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore)
          cell (controlCellValueOnPATEDoubleScore controlValue cell)
          (hmassTarget cell hcell)
          (fun unit hunit hscore => by
            rw [control_scoreMeasurable_pateDoubleScore propensityScore
              treatedPrognosticScore controlPrognosticScore targetOutcomeC
              controlValue targetSample hscoreMeasTargetC unit hunit,
              hscore])).symm)
  have hselected :
      weightedSampleMeanContrast targetSample baseWeight
          targetOutcomeT targetOutcomeC =
        weightedSampleMeanContrast selectedSample
          (retrospectiveInverseSamplingWeight baseWeight
            (pateDoubleScore propensityScore treatedPrognosticScore
              controlPrognosticScore)
            treatment samplingIfTreated samplingIfControl)
          selectedOutcomeT selectedOutcomeC :=
    weightedSampleMeanContrast_eq_retrospectivePATEDoubleScoreWeight
      targetSample selectedSample cells baseWeight targetOutcomeT
      targetOutcomeC selectedOutcomeT selectedOutcomeC propensityScore
      treatedPrognosticScore controlPrognosticScore treatment
      samplingIfTreated samplingIfControl treatedValue controlValue
      hcoverTarget hcoverSelected hmassTarget hsamplingTreated
      hsamplingControl htreatedMass hcontrolMass hscoreMeasTargetT
      hscoreMeasSelectedT hscoreMeasTargetC hscoreMeasSelectedC
  exact ⟨htarget.symm, hselected.symm.trans htarget.symm, hselected⟩

/-!
The prospective/common-sampling version is obtained by specializing the
retrospective theorem to a common sampling multiplier.
-/

/-- Prospective selected-sample PATE double-score effect-share identification. -/
theorem prospectivePATEDoubleScoreWeight_common_effect_share_identification
    (targetSample selectedSample : Finset Unit)
    (cells : Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (baseWeight : Unit -> Real)
    (targetOutcomeT targetOutcomeC selectedOutcomeT selectedOutcomeC :
      Unit -> Real)
    (propensityScore : Unit -> PropensityCell)
    (treatedPrognosticScore : Unit -> TreatedProgCell)
    (controlPrognosticScore : Unit -> ControlProgCell)
    (treatment : Unit -> Prop) [DecidablePred treatment]
    (samplingMass :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (hcoverTarget :
      ∀ unit, unit ∈ targetSample ->
        pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore unit ∈ cells)
    (hcoverSelected :
      ∀ unit, unit ∈ selectedSample ->
        pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore unit ∈ cells)
    (hmassTarget :
      ∀ cell, cell ∈ cells ->
        scoreCellMass targetSample baseWeight
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore) cell ≠ 0)
    (hsampling : ∀ cell, cell ∈ cells -> samplingMass cell ≠ 0)
    (htreatedMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (selectedSample.filter treatment) baseWeight
            (pateDoubleScore propensityScore treatedPrognosticScore
              controlPrognosticScore) cell =
          samplingMass cell *
            scoreCellMass (targetSample.filter treatment) baseWeight
              (pateDoubleScore propensityScore treatedPrognosticScore
                controlPrognosticScore) cell)
    (hcontrolMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (selectedSample.filter (fun unit => ¬ treatment unit))
            baseWeight
            (pateDoubleScore propensityScore treatedPrognosticScore
              controlPrognosticScore) cell =
          samplingMass cell *
            scoreCellMass
              (targetSample.filter (fun unit => ¬ treatment unit))
              baseWeight
              (pateDoubleScore propensityScore treatedPrognosticScore
                controlPrognosticScore) cell)
    (hscoreMeasTargetT :
      ∀ unit, unit ∈ targetSample ->
        targetOutcomeT unit = treatedValue (treatedPrognosticScore unit))
    (hscoreMeasSelectedT :
      ∀ unit, unit ∈ selectedSample ->
        selectedOutcomeT unit = treatedValue (treatedPrognosticScore unit))
    (hscoreMeasTargetC :
      ∀ unit, unit ∈ targetSample ->
        targetOutcomeC unit = controlValue (controlPrognosticScore unit))
    (hscoreMeasSelectedC :
      ∀ unit, unit ∈ selectedSample ->
        selectedOutcomeC unit = controlValue (controlPrognosticScore unit)) :
    weightedSampleMeanContrast targetSample baseWeight
        targetOutcomeT targetOutcomeC =
        candidateCellMeanEffectShareAggregate targetSample cells baseWeight
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore)
          (treatedCellValueOnPATEDoubleScore treatedValue)
          (controlCellValueOnPATEDoubleScore controlValue) ∧
      weightedSampleMeanContrast selectedSample
          (prospectiveInverseSamplingWeight baseWeight
            (pateDoubleScore propensityScore treatedPrognosticScore
              controlPrognosticScore)
            samplingMass)
          selectedOutcomeT selectedOutcomeC =
        candidateCellMeanEffectShareAggregate targetSample cells baseWeight
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore)
          (treatedCellValueOnPATEDoubleScore treatedValue)
          (controlCellValueOnPATEDoubleScore controlValue) ∧
      weightedSampleMeanContrast targetSample baseWeight
          targetOutcomeT targetOutcomeC =
        weightedSampleMeanContrast selectedSample
          (prospectiveInverseSamplingWeight baseWeight
            (pateDoubleScore propensityScore treatedPrognosticScore
              controlPrognosticScore)
            samplingMass)
          selectedOutcomeT selectedOutcomeC := by
  simpa [retrospectiveInverseSamplingWeight_common_sampling_eq] using
    retrospectivePATEDoubleScoreWeight_common_effect_share_identification
      targetSample selectedSample cells baseWeight targetOutcomeT
      targetOutcomeC selectedOutcomeT selectedOutcomeC propensityScore
      treatedPrognosticScore controlPrognosticScore treatment samplingMass
      samplingMass treatedValue controlValue hcoverTarget hcoverSelected
      hmassTarget hsampling hsampling htreatedMass hcontrolMass
      hscoreMeasTargetT hscoreMeasSelectedT hscoreMeasTargetC
      hscoreMeasSelectedC

variable {PATTProgCell : Type*} [DecidableEq PATTProgCell]

/--
Retrospective selected-sample PATT double-score effect-share identification.
-/
theorem retrospectivePATTDoubleScoreWeight_common_effect_share_identification
    (targetSample selectedSample : Finset Unit)
    (cells : Finset (PropensityCell × PATTProgCell))
    (baseWeight : Unit -> Real)
    (treatedTargetOutcome targetControlOutcome selectedControlOutcome :
      Unit -> Real)
    (propensityScore : Unit -> PropensityCell)
    (controlPrognosticScore : Unit -> PATTProgCell)
    (treatment : Unit -> Prop) [DecidablePred treatment]
    (samplingIfTreated samplingIfControl :
      PropensityCell × PATTProgCell -> Real)
    (treatedCellValue : PropensityCell × PATTProgCell -> Real)
    (controlValue : PATTProgCell -> Real)
    (hcoverTarget :
      ∀ unit, unit ∈ targetSample ->
        pattDoubleScore propensityScore controlPrognosticScore unit ∈ cells)
    (hcoverSelected :
      ∀ unit, unit ∈ selectedSample ->
        pattDoubleScore propensityScore controlPrognosticScore unit ∈ cells)
    (hmassTarget :
      ∀ cell, cell ∈ cells ->
        scoreCellMass targetSample baseWeight
          (pattDoubleScore propensityScore controlPrognosticScore) cell ≠ 0)
    (hsamplingTreated :
      ∀ cell, cell ∈ cells -> samplingIfTreated cell ≠ 0)
    (hsamplingControl :
      ∀ cell, cell ∈ cells -> samplingIfControl cell ≠ 0)
    (htreatedMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (selectedSample.filter treatment) baseWeight
            (pattDoubleScore propensityScore controlPrognosticScore) cell =
          samplingIfTreated cell *
            scoreCellMass (targetSample.filter treatment) baseWeight
              (pattDoubleScore propensityScore controlPrognosticScore) cell)
    (hcontrolMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (selectedSample.filter (fun unit => ¬ treatment unit))
            baseWeight
            (pattDoubleScore propensityScore controlPrognosticScore) cell =
          samplingIfControl cell *
            scoreCellMass
              (targetSample.filter (fun unit => ¬ treatment unit))
              baseWeight
              (pattDoubleScore propensityScore controlPrognosticScore) cell)
    (hscoreMeasTargetT :
      ∀ unit, unit ∈ targetSample ->
        treatedTargetOutcome unit =
          treatedCellValue
            (pattDoubleScore propensityScore controlPrognosticScore unit))
    (hscoreMeasTargetC :
      ∀ unit, unit ∈ targetSample ->
        targetControlOutcome unit =
          controlValue (controlPrognosticScore unit))
    (hscoreMeasSelectedC :
      ∀ unit, unit ∈ selectedSample ->
        selectedControlOutcome unit =
          controlValue (controlPrognosticScore unit)) :
    weightedSampleMeanContrast targetSample baseWeight
        treatedTargetOutcome targetControlOutcome =
        candidateCellMeanEffectShareAggregate targetSample cells baseWeight
          (pattDoubleScore propensityScore controlPrognosticScore)
          treatedCellValue
          (controlCellValueOnPATTDoubleScore controlValue) ∧
      pattWeightedMeanContrast targetSample selectedSample baseWeight
          (retrospectiveInverseSamplingWeight baseWeight
            (pattDoubleScore propensityScore controlPrognosticScore)
            treatment samplingIfTreated samplingIfControl)
          treatedTargetOutcome selectedControlOutcome =
        candidateCellMeanEffectShareAggregate targetSample cells baseWeight
          (pattDoubleScore propensityScore controlPrognosticScore)
          treatedCellValue
          (controlCellValueOnPATTDoubleScore controlValue) ∧
      weightedSampleMeanContrast targetSample baseWeight
          treatedTargetOutcome targetControlOutcome =
        pattWeightedMeanContrast targetSample selectedSample baseWeight
          (retrospectiveInverseSamplingWeight baseWeight
            (pattDoubleScore propensityScore controlPrognosticScore)
            treatment samplingIfTreated samplingIfControl)
          treatedTargetOutcome selectedControlOutcome := by
  have htarget :
      candidateCellMeanEffectShareAggregate targetSample cells baseWeight
          (pattDoubleScore propensityScore controlPrognosticScore)
          treatedCellValue
          (controlCellValueOnPATTDoubleScore controlValue) =
        weightedSampleMeanContrast targetSample baseWeight
          treatedTargetOutcome targetControlOutcome :=
    candidateCellMeanEffectShareAggregate_eq_weightedSampleMeanContrast_of_eq
      targetSample cells baseWeight treatedTargetOutcome targetControlOutcome
      (pattDoubleScore propensityScore controlPrognosticScore)
      treatedCellValue (controlCellValueOnPATTDoubleScore controlValue)
      hcoverTarget hmassTarget
      (fun cell hcell =>
        (scoreCellMean_eq_const_of_eq_on_cell
          targetSample baseWeight treatedTargetOutcome
          (pattDoubleScore propensityScore controlPrognosticScore)
          cell (treatedCellValue cell) (hmassTarget cell hcell)
          (fun unit hunit hscore => by
            rw [hscoreMeasTargetT unit hunit, hscore])).symm)
      (fun cell hcell =>
        (scoreCellMean_eq_const_of_eq_on_cell
          targetSample baseWeight targetControlOutcome
          (pattDoubleScore propensityScore controlPrognosticScore)
          cell (controlCellValueOnPATTDoubleScore controlValue cell)
          (hmassTarget cell hcell)
          (fun unit hunit hscore => by
            rw [control_scoreMeasurable_pattDoubleScore propensityScore
              controlPrognosticScore targetControlOutcome controlValue
              targetSample hscoreMeasTargetC unit hunit, hscore])).symm)
  have hselected :
      weightedSampleMeanContrast targetSample baseWeight
          treatedTargetOutcome targetControlOutcome =
        pattWeightedMeanContrast targetSample selectedSample baseWeight
          (retrospectiveInverseSamplingWeight baseWeight
            (pattDoubleScore propensityScore controlPrognosticScore)
            treatment samplingIfTreated samplingIfControl)
          treatedTargetOutcome selectedControlOutcome :=
    weightedSampleMeanContrast_eq_retrospectivePATTDoubleScoreWeight
      targetSample selectedSample cells baseWeight treatedTargetOutcome
      targetControlOutcome selectedControlOutcome propensityScore
      controlPrognosticScore treatment samplingIfTreated samplingIfControl
      controlValue hcoverTarget hcoverSelected hmassTarget
      hsamplingTreated hsamplingControl htreatedMass hcontrolMass
      hscoreMeasTargetC hscoreMeasSelectedC
  exact ⟨htarget.symm, hselected.symm.trans htarget.symm, hselected⟩

/-- Prospective selected-sample PATT double-score effect-share identification. -/
theorem prospectivePATTDoubleScoreWeight_common_effect_share_identification
    (targetSample selectedSample : Finset Unit)
    (cells : Finset (PropensityCell × PATTProgCell))
    (baseWeight : Unit -> Real)
    (treatedTargetOutcome targetControlOutcome selectedControlOutcome :
      Unit -> Real)
    (propensityScore : Unit -> PropensityCell)
    (controlPrognosticScore : Unit -> PATTProgCell)
    (treatment : Unit -> Prop) [DecidablePred treatment]
    (samplingMass : PropensityCell × PATTProgCell -> Real)
    (treatedCellValue : PropensityCell × PATTProgCell -> Real)
    (controlValue : PATTProgCell -> Real)
    (hcoverTarget :
      ∀ unit, unit ∈ targetSample ->
        pattDoubleScore propensityScore controlPrognosticScore unit ∈ cells)
    (hcoverSelected :
      ∀ unit, unit ∈ selectedSample ->
        pattDoubleScore propensityScore controlPrognosticScore unit ∈ cells)
    (hmassTarget :
      ∀ cell, cell ∈ cells ->
        scoreCellMass targetSample baseWeight
          (pattDoubleScore propensityScore controlPrognosticScore) cell ≠ 0)
    (hsampling : ∀ cell, cell ∈ cells -> samplingMass cell ≠ 0)
    (htreatedMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (selectedSample.filter treatment) baseWeight
            (pattDoubleScore propensityScore controlPrognosticScore) cell =
          samplingMass cell *
            scoreCellMass (targetSample.filter treatment) baseWeight
              (pattDoubleScore propensityScore controlPrognosticScore) cell)
    (hcontrolMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (selectedSample.filter (fun unit => ¬ treatment unit))
            baseWeight
            (pattDoubleScore propensityScore controlPrognosticScore) cell =
          samplingMass cell *
            scoreCellMass
              (targetSample.filter (fun unit => ¬ treatment unit))
              baseWeight
              (pattDoubleScore propensityScore controlPrognosticScore) cell)
    (hscoreMeasTargetT :
      ∀ unit, unit ∈ targetSample ->
        treatedTargetOutcome unit =
          treatedCellValue
            (pattDoubleScore propensityScore controlPrognosticScore unit))
    (hscoreMeasTargetC :
      ∀ unit, unit ∈ targetSample ->
        targetControlOutcome unit =
          controlValue (controlPrognosticScore unit))
    (hscoreMeasSelectedC :
      ∀ unit, unit ∈ selectedSample ->
        selectedControlOutcome unit =
          controlValue (controlPrognosticScore unit)) :
    weightedSampleMeanContrast targetSample baseWeight
        treatedTargetOutcome targetControlOutcome =
        candidateCellMeanEffectShareAggregate targetSample cells baseWeight
          (pattDoubleScore propensityScore controlPrognosticScore)
          treatedCellValue
          (controlCellValueOnPATTDoubleScore controlValue) ∧
      pattWeightedMeanContrast targetSample selectedSample baseWeight
          (prospectiveInverseSamplingWeight baseWeight
            (pattDoubleScore propensityScore controlPrognosticScore)
            samplingMass)
          treatedTargetOutcome selectedControlOutcome =
        candidateCellMeanEffectShareAggregate targetSample cells baseWeight
          (pattDoubleScore propensityScore controlPrognosticScore)
          treatedCellValue
          (controlCellValueOnPATTDoubleScore controlValue) ∧
      weightedSampleMeanContrast targetSample baseWeight
          treatedTargetOutcome targetControlOutcome =
        pattWeightedMeanContrast targetSample selectedSample baseWeight
          (prospectiveInverseSamplingWeight baseWeight
            (pattDoubleScore propensityScore controlPrognosticScore)
            samplingMass)
          treatedTargetOutcome selectedControlOutcome := by
  simpa [retrospectiveInverseSamplingWeight_common_sampling_eq] using
    retrospectivePATTDoubleScoreWeight_common_effect_share_identification
      targetSample selectedSample cells baseWeight treatedTargetOutcome
      targetControlOutcome selectedControlOutcome propensityScore
      controlPrognosticScore treatment samplingMass samplingMass
      treatedCellValue controlValue hcoverTarget hcoverSelected hmassTarget
      hsampling hsampling htreatedMass hcontrolMass hscoreMeasTargetT
      hscoreMeasTargetC hscoreMeasSelectedC

end WDSM
end Matching
end StatInference
