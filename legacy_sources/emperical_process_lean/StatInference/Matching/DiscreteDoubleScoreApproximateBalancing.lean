import StatInference.Matching.WDSM.DiscreteApproximateBalancing
import StatInference.Matching.WDSM.DiscreteDoubleScoreBalancing

/-!
# Finite approximate double-score balancing for WDSM

This module specializes the generic approximate score-cell balancing bounds to
the joint double-score cells used by WDSM.  It keeps the result deterministic:
future probability arguments must prove the relevant L1 share-imbalance rates
for these double-score cells.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Unit PropensityCell TreatedProgCell ControlProgCell PATTProgCell : Type*}
  [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
  [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]

/--
Finite approximate PATE double-score balancing bound.  If treated and control
potential/observed outcomes are functions of their prognostic-score components,
then the target PATE contrast and treated-minus-control arm contrast differ by
at most the two envelope-weighted L1 imbalances of joint double-score shares.
-/
theorem abs_weightedSampleMeanContrast_sub_twoArmWeightedMeanContrast_pateDoubleScore_le_l1
    (targetSample treatedSample controlSample : Finset Unit)
    (cells : Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (targetWeight treatedWeight controlWeight : Unit -> Real)
    (targetOutcomeT targetOutcomeC treatedOutcome controlOutcome : Unit -> Real)
    (propensityScore : Unit -> PropensityCell)
    (treatedPrognosticScore : Unit -> TreatedProgCell)
    (controlPrognosticScore : Unit -> ControlProgCell)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (treatedEnvelope controlEnvelope : Real)
    (hcoverTarget :
      ∀ unit, unit ∈ targetSample ->
        pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore unit ∈ cells)
    (hcoverTreated :
      ∀ unit, unit ∈ treatedSample ->
        pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore unit ∈ cells)
    (hcoverControl :
      ∀ unit, unit ∈ controlSample ->
        pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore unit ∈ cells)
    (hmassTarget :
      ∀ cell, cell ∈ cells ->
        scoreCellMass targetSample targetWeight
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore) cell ≠ 0)
    (hmassTreated :
      ∀ cell, cell ∈ cells ->
        scoreCellMass treatedSample treatedWeight
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore) cell ≠ 0)
    (hmassControl :
      ∀ cell, cell ∈ cells ->
        scoreCellMass controlSample controlWeight
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore) cell ≠ 0)
    (hscoreMeasTargetT :
      ∀ unit, unit ∈ targetSample ->
        targetOutcomeT unit = treatedValue (treatedPrognosticScore unit))
    (hscoreMeasTreated :
      ∀ unit, unit ∈ treatedSample ->
        treatedOutcome unit = treatedValue (treatedPrognosticScore unit))
    (hscoreMeasTargetC :
      ∀ unit, unit ∈ targetSample ->
        targetOutcomeC unit = controlValue (controlPrognosticScore unit))
    (hscoreMeasControl :
      ∀ unit, unit ∈ controlSample ->
        controlOutcome unit = controlValue (controlPrognosticScore unit))
    (htreated_bound :
      ∀ cell, cell ∈ cells ->
        |treatedCellValueOnPATEDoubleScore treatedValue cell| ≤
          treatedEnvelope)
    (hcontrol_bound :
      ∀ cell, cell ∈ cells ->
        |controlCellValueOnPATEDoubleScore controlValue cell| ≤
          controlEnvelope) :
    |weightedSampleMeanContrast targetSample targetWeight
        targetOutcomeT targetOutcomeC -
      twoArmWeightedMeanContrast treatedSample controlSample
        treatedWeight controlWeight treatedOutcome controlOutcome| ≤
      treatedEnvelope *
        (∑ cell ∈ cells,
          |scoreCellShare targetSample targetWeight
              (pateDoubleScore propensityScore treatedPrognosticScore
                controlPrognosticScore) cell -
            scoreCellShare treatedSample treatedWeight
              (pateDoubleScore propensityScore treatedPrognosticScore
                controlPrognosticScore) cell|) +
      controlEnvelope *
        (∑ cell ∈ cells,
          |scoreCellShare targetSample targetWeight
              (pateDoubleScore propensityScore treatedPrognosticScore
                controlPrognosticScore) cell -
            scoreCellShare controlSample controlWeight
              (pateDoubleScore propensityScore treatedPrognosticScore
                controlPrognosticScore) cell|) := by
  exact
    abs_weightedSampleMeanContrast_sub_twoArmWeightedMeanContrast_le_l1_scoreCellShare
      targetSample treatedSample controlSample cells targetWeight
      treatedWeight controlWeight targetOutcomeT targetOutcomeC
      treatedOutcome controlOutcome
      (pateDoubleScore propensityScore treatedPrognosticScore
        controlPrognosticScore)
      (pateDoubleScore propensityScore treatedPrognosticScore
        controlPrognosticScore)
      (pateDoubleScore propensityScore treatedPrognosticScore
        controlPrognosticScore)
      (treatedCellValueOnPATEDoubleScore treatedValue)
      (controlCellValueOnPATEDoubleScore controlValue)
      treatedEnvelope controlEnvelope hcoverTarget hcoverTreated
      hcoverControl hmassTarget hmassTreated hmassControl
      (treated_scoreMeasurable_pateDoubleScore propensityScore
        treatedPrognosticScore controlPrognosticScore targetOutcomeT
        treatedValue targetSample hscoreMeasTargetT)
      (treated_scoreMeasurable_pateDoubleScore propensityScore
        treatedPrognosticScore controlPrognosticScore treatedOutcome
        treatedValue treatedSample hscoreMeasTreated)
      (control_scoreMeasurable_pateDoubleScore propensityScore
        treatedPrognosticScore controlPrognosticScore targetOutcomeC
        controlValue targetSample hscoreMeasTargetC)
      (control_scoreMeasurable_pateDoubleScore propensityScore
        treatedPrognosticScore controlPrognosticScore controlOutcome
        controlValue controlSample hscoreMeasControl)
      htreated_bound hcontrol_bound

/--
Finite approximate PATT double-score balancing bound.  Only the
counterfactual-control component is transported from the control sample, so
only the target-control L1 double-score share imbalance appears.
-/
theorem abs_weightedSampleMeanContrast_sub_pattWeightedMeanContrast_pattDoubleScore_le_l1
    (targetSample controlSample : Finset Unit)
    (cells : Finset (PropensityCell × PATTProgCell))
    (targetWeight controlWeight : Unit -> Real)
    (treatedTargetOutcome targetControlOutcome controlOutcome : Unit -> Real)
    (propensityScore : Unit -> PropensityCell)
    (controlPrognosticScore : Unit -> PATTProgCell)
    (controlValue : PATTProgCell -> Real)
    (controlEnvelope : Real)
    (hcoverTarget :
      ∀ unit, unit ∈ targetSample ->
        pattDoubleScore propensityScore controlPrognosticScore unit ∈ cells)
    (hcoverControl :
      ∀ unit, unit ∈ controlSample ->
        pattDoubleScore propensityScore controlPrognosticScore unit ∈ cells)
    (hmassTarget :
      ∀ cell, cell ∈ cells ->
        scoreCellMass targetSample targetWeight
          (pattDoubleScore propensityScore controlPrognosticScore) cell ≠ 0)
    (hmassControl :
      ∀ cell, cell ∈ cells ->
        scoreCellMass controlSample controlWeight
          (pattDoubleScore propensityScore controlPrognosticScore) cell ≠ 0)
    (hscoreMeasTargetC :
      ∀ unit, unit ∈ targetSample ->
        targetControlOutcome unit =
          controlValue (controlPrognosticScore unit))
    (hscoreMeasControl :
      ∀ unit, unit ∈ controlSample ->
        controlOutcome unit = controlValue (controlPrognosticScore unit))
    (hcontrol_bound :
      ∀ cell, cell ∈ cells ->
        |controlCellValueOnPATTDoubleScore controlValue cell| ≤
          controlEnvelope) :
    |weightedSampleMeanContrast targetSample targetWeight
        treatedTargetOutcome targetControlOutcome -
      pattWeightedMeanContrast targetSample controlSample targetWeight
        controlWeight treatedTargetOutcome controlOutcome| ≤
      controlEnvelope *
        (∑ cell ∈ cells,
          |scoreCellShare targetSample targetWeight
              (pattDoubleScore propensityScore controlPrognosticScore) cell -
            scoreCellShare controlSample controlWeight
              (pattDoubleScore propensityScore controlPrognosticScore) cell|) := by
  exact
    abs_weightedSampleMeanContrast_sub_pattWeightedMeanContrast_le_l1_scoreCellShare
      targetSample controlSample cells targetWeight controlWeight
      treatedTargetOutcome targetControlOutcome controlOutcome
      (pattDoubleScore propensityScore controlPrognosticScore)
      (pattDoubleScore propensityScore controlPrognosticScore)
      (controlCellValueOnPATTDoubleScore controlValue) controlEnvelope
      hcoverTarget hcoverControl hmassTarget hmassControl
      (control_scoreMeasurable_pattDoubleScore propensityScore
        controlPrognosticScore targetControlOutcome controlValue
        targetSample hscoreMeasTargetC)
      (control_scoreMeasurable_pattDoubleScore propensityScore
        controlPrognosticScore controlOutcome controlValue
        controlSample hscoreMeasControl)
      hcontrol_bound

end WDSM
end Matching
end StatInference
