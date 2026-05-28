import StatInference.Matching.WDSM.DiscreteDoubleScoreSurveyEffectShareIdentification

/-!
# Zero-error consequences of double-score survey effect-share identification

The effect-share identification module proves exact equality between target
finite contrasts and selected-sample inverse-weighted contrasts.  This module
packages those equalities as absolute-error-zero statements, which are the
finite deterministic inputs consumed by later convergence and Wald layers.
-/

namespace StatInference
namespace Matching
namespace WDSM

private theorem abs_sub_eq_zero_of_eq_real (x y : Real) (h : x = y) :
    |x - y| = 0 := by
  rw [h]
  simp

variable {Unit PropensityCell TreatedProgCell ControlProgCell PATTProgCell : Type*}
  [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
  [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]

/--
Retrospective selected-sample PATE double-score zero-error consequence.
-/
theorem abs_target_sub_retrospectivePATEDoubleScoreWeight_eq_zero
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
    |weightedSampleMeanContrast targetSample baseWeight
        targetOutcomeT targetOutcomeC -
      weightedSampleMeanContrast selectedSample
        (retrospectiveInverseSamplingWeight baseWeight
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore)
          treatment samplingIfTreated samplingIfControl)
        selectedOutcomeT selectedOutcomeC| = 0 := by
  exact abs_sub_eq_zero_of_eq_real _ _
    ((retrospectivePATEDoubleScoreWeight_common_effect_share_identification
      targetSample selectedSample cells baseWeight targetOutcomeT
      targetOutcomeC selectedOutcomeT selectedOutcomeC propensityScore
      treatedPrognosticScore controlPrognosticScore treatment
      samplingIfTreated samplingIfControl treatedValue controlValue
      hcoverTarget hcoverSelected hmassTarget hsamplingTreated
      hsamplingControl htreatedMass hcontrolMass hscoreMeasTargetT
      hscoreMeasSelectedT hscoreMeasTargetC hscoreMeasSelectedC).2.2)

/-- Prospective selected-sample PATE double-score zero-error consequence. -/
theorem abs_target_sub_prospectivePATEDoubleScoreWeight_eq_zero
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
    |weightedSampleMeanContrast targetSample baseWeight
        targetOutcomeT targetOutcomeC -
      weightedSampleMeanContrast selectedSample
        (prospectiveInverseSamplingWeight baseWeight
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore)
          samplingMass)
        selectedOutcomeT selectedOutcomeC| = 0 := by
  exact abs_sub_eq_zero_of_eq_real _ _
    ((prospectivePATEDoubleScoreWeight_common_effect_share_identification
      targetSample selectedSample cells baseWeight targetOutcomeT
      targetOutcomeC selectedOutcomeT selectedOutcomeC propensityScore
      treatedPrognosticScore controlPrognosticScore treatment samplingMass
      treatedValue controlValue hcoverTarget hcoverSelected hmassTarget
      hsampling htreatedMass hcontrolMass hscoreMeasTargetT
      hscoreMeasSelectedT hscoreMeasTargetC hscoreMeasSelectedC).2.2)

/--
Retrospective selected-sample PATT double-score zero-error consequence.
-/
theorem abs_target_sub_retrospectivePATTDoubleScoreWeight_eq_zero
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
    |weightedSampleMeanContrast targetSample baseWeight
        treatedTargetOutcome targetControlOutcome -
      pattWeightedMeanContrast targetSample selectedSample baseWeight
        (retrospectiveInverseSamplingWeight baseWeight
          (pattDoubleScore propensityScore controlPrognosticScore)
          treatment samplingIfTreated samplingIfControl)
        treatedTargetOutcome selectedControlOutcome| = 0 := by
  exact abs_sub_eq_zero_of_eq_real _ _
    ((retrospectivePATTDoubleScoreWeight_common_effect_share_identification
      targetSample selectedSample cells baseWeight treatedTargetOutcome
      targetControlOutcome selectedControlOutcome propensityScore
      controlPrognosticScore treatment samplingIfTreated samplingIfControl
      treatedCellValue controlValue hcoverTarget hcoverSelected hmassTarget
      hsamplingTreated hsamplingControl htreatedMass hcontrolMass
      hscoreMeasTargetT hscoreMeasTargetC hscoreMeasSelectedC).2.2)

/-- Prospective selected-sample PATT double-score zero-error consequence. -/
theorem abs_target_sub_prospectivePATTDoubleScoreWeight_eq_zero
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
    |weightedSampleMeanContrast targetSample baseWeight
        treatedTargetOutcome targetControlOutcome -
      pattWeightedMeanContrast targetSample selectedSample baseWeight
        (prospectiveInverseSamplingWeight baseWeight
          (pattDoubleScore propensityScore controlPrognosticScore)
          samplingMass)
        treatedTargetOutcome selectedControlOutcome| = 0 := by
  exact abs_sub_eq_zero_of_eq_real _ _
    ((prospectivePATTDoubleScoreWeight_common_effect_share_identification
      targetSample selectedSample cells baseWeight treatedTargetOutcome
      targetControlOutcome selectedControlOutcome propensityScore
      controlPrognosticScore treatment samplingMass treatedCellValue
      controlValue hcoverTarget hcoverSelected hmassTarget hsampling
      htreatedMass hcontrolMass hscoreMeasTargetT hscoreMeasTargetC
      hscoreMeasSelectedC).2.2)

end WDSM
end Matching
end StatInference
