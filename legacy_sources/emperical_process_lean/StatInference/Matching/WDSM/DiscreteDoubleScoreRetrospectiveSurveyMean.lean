import StatInference.Matching.WDSM.DiscreteDoubleScoreBalancing
import StatInference.Matching.WDSM.DiscreteRetrospectiveSurveyMeanRecovery

/-!
# Finite double-score retrospective survey-weighted mean recovery

This module combines the joint double-score projection layer with the direct
retrospective survey-weighted mean recovery layer.  It proves finite PATE and
PATT wrappers where inverse treatment-specific selected-data weights recover
target score-measurable contrasts on joint double-score cells.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Unit PropensityCell TreatedProgCell ControlProgCell : Type*}
  [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
  [DecidableEq ControlProgCell]

/--
Finite retrospective double-score PATE recovery.  If selected treated/control
joint-cell masses are treatment-specific sampling multiples of target
treated/control joint-cell masses, then inverse treatment-specific selected
weights recover the target PATE contrast for outcomes that are prognostic-score
measurable and hence joint-double-score measurable.
-/
theorem weightedSampleMeanContrast_eq_retrospectivePATEDoubleScoreWeight
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
      weightedSampleMeanContrast selectedSample
        (retrospectiveInverseSamplingWeight baseWeight
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore)
          treatment samplingIfTreated samplingIfControl)
        selectedOutcomeT selectedOutcomeC := by
  exact
    weightedSampleMeanContrast_eq_retrospectiveInverseSamplingWeight_of_scoreMeasurable
      targetSample selectedSample cells baseWeight targetOutcomeT
      targetOutcomeC selectedOutcomeT selectedOutcomeC
      (pateDoubleScore propensityScore treatedPrognosticScore
        controlPrognosticScore)
      treatment samplingIfTreated samplingIfControl
      (treatedCellValueOnPATEDoubleScore treatedValue)
      (controlCellValueOnPATEDoubleScore controlValue)
      hcoverTarget hcoverSelected hmassTarget hsamplingTreated
      hsamplingControl htreatedMass hcontrolMass
      (treated_scoreMeasurable_pateDoubleScore propensityScore
        treatedPrognosticScore controlPrognosticScore targetOutcomeT
        treatedValue targetSample hscoreMeasTargetT)
      (treated_scoreMeasurable_pateDoubleScore propensityScore
        treatedPrognosticScore controlPrognosticScore selectedOutcomeT
        treatedValue selectedSample hscoreMeasSelectedT)
      (control_scoreMeasurable_pateDoubleScore propensityScore
        treatedPrognosticScore controlPrognosticScore targetOutcomeC
        controlValue targetSample hscoreMeasTargetC)
      (control_scoreMeasurable_pateDoubleScore propensityScore
        treatedPrognosticScore controlPrognosticScore selectedOutcomeC
        controlValue selectedSample hscoreMeasSelectedC)

variable {PATTProgCell : Type*} [DecidableEq PATTProgCell]

/--
Finite retrospective double-score PATT recovery.  The treated target mean is
left as the target treated mean, while the counterfactual control mean is
recovered from selected data by inverse treatment-specific selected weights on
the PATT joint double-score cells.
-/
theorem weightedSampleMeanContrast_eq_retrospectivePATTDoubleScoreWeight
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
      pattWeightedMeanContrast targetSample selectedSample baseWeight
        (retrospectiveInverseSamplingWeight baseWeight
          (pattDoubleScore propensityScore controlPrognosticScore)
          treatment samplingIfTreated samplingIfControl)
        treatedTargetOutcome selectedControlOutcome := by
  have hcontrol :
      weightedSampleMean targetSample baseWeight targetControlOutcome =
        weightedSampleMean selectedSample
          (retrospectiveInverseSamplingWeight baseWeight
            (pattDoubleScore propensityScore controlPrognosticScore)
            treatment samplingIfTreated samplingIfControl)
          selectedControlOutcome :=
    weightedSampleMean_eq_retrospectiveInverseSamplingWeight_of_scoreMeasurable
      targetSample selectedSample cells baseWeight targetControlOutcome
      selectedControlOutcome
      (pattDoubleScore propensityScore controlPrognosticScore)
      treatment samplingIfTreated samplingIfControl
      (controlCellValueOnPATTDoubleScore controlValue)
      hcoverTarget hcoverSelected hmassTarget hsamplingTreated
      hsamplingControl htreatedMass hcontrolMass
      (control_scoreMeasurable_pattDoubleScore propensityScore
        controlPrognosticScore targetControlOutcome controlValue targetSample
        hscoreMeasTargetC)
      (control_scoreMeasurable_pattDoubleScore propensityScore
        controlPrognosticScore selectedControlOutcome controlValue
        selectedSample hscoreMeasSelectedC)
  unfold weightedSampleMeanContrast pattWeightedMeanContrast
  rw [hcontrol]

end WDSM
end Matching
end StatInference
