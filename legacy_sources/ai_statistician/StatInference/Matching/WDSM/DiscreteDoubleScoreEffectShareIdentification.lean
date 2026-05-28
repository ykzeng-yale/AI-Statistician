import StatInference.Matching.WDSM.DiscreteDoubleScoreBalancing
import StatInference.Matching.WDSM.DiscreteScoreMeasurableEffectShareIdentification

/-!
# Double-score effect-share identification

This module lifts the finite score-measurable effect-share identification
bridge to the joint double-score cells used by WDSM.  The only new content is
the projection algebra: prognostic-score-measurable outcomes are
double-score-measurable after adjoining the propensity-score cell.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Unit PropensityCell TreatedProgCell ControlProgCell : Type*}
  [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
  [DecidableEq ControlProgCell]

/--
Finite PATE double-score effect-share identification.  Target and observed
arm contrasts share the same target-share aggregate over the joint
`(propensity, treated prognostic, control prognostic)` cell.
-/
theorem pate_common_effect_share_identification_of_pateDoubleScore
    (targetSample treatedSample controlSample : Finset Unit)
    (cells : Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (targetWeight treatedWeight controlWeight : Unit -> Real)
    (targetOutcomeT targetOutcomeC treatedOutcome controlOutcome : Unit -> Real)
    (propensityScore : Unit -> PropensityCell)
    (treatedPrognosticScore : Unit -> TreatedProgCell)
    (controlPrognosticScore : Unit -> ControlProgCell)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
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
    (hshareTreated :
      ∀ cell, cell ∈ cells ->
        scoreCellShare targetSample targetWeight
            (pateDoubleScore propensityScore treatedPrognosticScore
              controlPrognosticScore) cell =
          scoreCellShare treatedSample treatedWeight
            (pateDoubleScore propensityScore treatedPrognosticScore
              controlPrognosticScore) cell)
    (hshareControl :
      ∀ cell, cell ∈ cells ->
        scoreCellShare targetSample targetWeight
            (pateDoubleScore propensityScore treatedPrognosticScore
              controlPrognosticScore) cell =
          scoreCellShare controlSample controlWeight
            (pateDoubleScore propensityScore treatedPrognosticScore
              controlPrognosticScore) cell)
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
        controlOutcome unit = controlValue (controlPrognosticScore unit)) :
    weightedSampleMeanContrast targetSample targetWeight
        targetOutcomeT targetOutcomeC =
        candidateCellMeanEffectShareAggregate targetSample cells targetWeight
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore)
          (treatedCellValueOnPATEDoubleScore treatedValue)
          (controlCellValueOnPATEDoubleScore controlValue) ∧
      twoArmWeightedMeanContrast treatedSample controlSample treatedWeight
          controlWeight treatedOutcome controlOutcome =
        candidateCellMeanEffectShareAggregate targetSample cells targetWeight
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore)
          (treatedCellValueOnPATEDoubleScore treatedValue)
          (controlCellValueOnPATEDoubleScore controlValue) ∧
      weightedSampleMeanContrast targetSample targetWeight
          targetOutcomeT targetOutcomeC =
        twoArmWeightedMeanContrast treatedSample controlSample
          treatedWeight controlWeight treatedOutcome controlOutcome := by
  exact
    pate_common_effect_share_identification_of_scoreMeasurable
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
      hcoverTarget hcoverTreated hcoverControl hmassTarget hmassTreated
      hmassControl hshareTreated hshareControl
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

variable {PATTProgCell : Type*} [DecidableEq PATTProgCell]

/--
Finite PATT double-score effect-share identification.  The control potential
and observed control outcomes are control-prognostic-score-measurable, hence
measurable on the PATT double score; the direct treated target outcome is
allowed to be any function of the PATT double-score cell.
-/
theorem patt_common_effect_share_identification_of_pattDoubleScore
    (targetSample controlSample : Finset Unit)
    (cells : Finset (PropensityCell × PATTProgCell))
    (targetWeight controlWeight : Unit -> Real)
    (treatedTargetOutcome targetControlOutcome controlOutcome : Unit -> Real)
    (propensityScore : Unit -> PropensityCell)
    (controlPrognosticScore : Unit -> PATTProgCell)
    (treatedCellValue : PropensityCell × PATTProgCell -> Real)
    (controlValue : PATTProgCell -> Real)
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
    (hshareControl :
      ∀ cell, cell ∈ cells ->
        scoreCellShare targetSample targetWeight
            (pattDoubleScore propensityScore controlPrognosticScore) cell =
          scoreCellShare controlSample controlWeight
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
    (hscoreMeasControl :
      ∀ unit, unit ∈ controlSample ->
        controlOutcome unit = controlValue (controlPrognosticScore unit)) :
    weightedSampleMeanContrast targetSample targetWeight
        treatedTargetOutcome targetControlOutcome =
        candidateCellMeanEffectShareAggregate targetSample cells targetWeight
          (pattDoubleScore propensityScore controlPrognosticScore)
          treatedCellValue
          (controlCellValueOnPATTDoubleScore controlValue) ∧
      pattWeightedMeanContrast targetSample controlSample targetWeight
          controlWeight treatedTargetOutcome controlOutcome =
        candidateCellMeanEffectShareAggregate targetSample cells targetWeight
          (pattDoubleScore propensityScore controlPrognosticScore)
          treatedCellValue
          (controlCellValueOnPATTDoubleScore controlValue) ∧
      weightedSampleMeanContrast targetSample targetWeight
          treatedTargetOutcome targetControlOutcome =
        pattWeightedMeanContrast targetSample controlSample targetWeight
          controlWeight treatedTargetOutcome controlOutcome := by
  exact
    patt_common_effect_share_identification_of_scoreMeasurable
      targetSample controlSample cells targetWeight controlWeight
      treatedTargetOutcome targetControlOutcome controlOutcome
      (pattDoubleScore propensityScore controlPrognosticScore)
      (pattDoubleScore propensityScore controlPrognosticScore)
      treatedCellValue
      (controlCellValueOnPATTDoubleScore controlValue)
      hcoverTarget hcoverControl hmassTarget hmassControl hshareControl
      hscoreMeasTargetT
      (control_scoreMeasurable_pattDoubleScore propensityScore
        controlPrognosticScore targetControlOutcome controlValue
        targetSample hscoreMeasTargetC)
      (control_scoreMeasurable_pattDoubleScore propensityScore
        controlPrognosticScore controlOutcome controlValue controlSample
        hscoreMeasControl)

/--
Paired finite PATE/PATT double-score effect-share identification.
-/
theorem pate_patt_common_effect_share_identification_of_doubleScore
    (pateTargetSample pateTreatedSample pateControlSample
      pattTargetSample pattControlSample : Finset Unit)
    (pateCells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (pattCells : Finset (PropensityCell × PATTProgCell))
    (pateTargetWeight pateTreatedWeight pateControlWeight
      pattTargetWeight pattControlWeight : Unit -> Real)
    (pateTargetOutcomeT pateTargetOutcomeC pateTreatedOutcome
      pateControlOutcome pattTreatedTargetOutcome pattTargetControlOutcome
      pattControlOutcome : Unit -> Real)
    (propensityScore : Unit -> PropensityCell)
    (treatedPrognosticScore : Unit -> TreatedProgCell)
    (controlPrognosticScore : Unit -> ControlProgCell)
    (pattControlPrognosticScore : Unit -> PATTProgCell)
    (pateTreatedValue : TreatedProgCell -> Real)
    (pateControlValue : ControlProgCell -> Real)
    (pattTreatedCellValue : PropensityCell × PATTProgCell -> Real)
    (pattControlValue : PATTProgCell -> Real)
    (hpateCoverTarget :
      ∀ unit, unit ∈ pateTargetSample ->
        pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore unit ∈ pateCells)
    (hpateCoverTreated :
      ∀ unit, unit ∈ pateTreatedSample ->
        pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore unit ∈ pateCells)
    (hpateCoverControl :
      ∀ unit, unit ∈ pateControlSample ->
        pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore unit ∈ pateCells)
    (hpattCoverTarget :
      ∀ unit, unit ∈ pattTargetSample ->
        pattDoubleScore propensityScore pattControlPrognosticScore unit ∈
          pattCells)
    (hpattCoverControl :
      ∀ unit, unit ∈ pattControlSample ->
        pattDoubleScore propensityScore pattControlPrognosticScore unit ∈
          pattCells)
    (hpateMassTarget :
      ∀ cell, cell ∈ pateCells ->
        scoreCellMass pateTargetSample pateTargetWeight
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore) cell ≠ 0)
    (hpateMassTreated :
      ∀ cell, cell ∈ pateCells ->
        scoreCellMass pateTreatedSample pateTreatedWeight
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore) cell ≠ 0)
    (hpateMassControl :
      ∀ cell, cell ∈ pateCells ->
        scoreCellMass pateControlSample pateControlWeight
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore) cell ≠ 0)
    (hpattMassTarget :
      ∀ cell, cell ∈ pattCells ->
        scoreCellMass pattTargetSample pattTargetWeight
          (pattDoubleScore propensityScore pattControlPrognosticScore)
          cell ≠ 0)
    (hpattMassControl :
      ∀ cell, cell ∈ pattCells ->
        scoreCellMass pattControlSample pattControlWeight
          (pattDoubleScore propensityScore pattControlPrognosticScore)
          cell ≠ 0)
    (hpateShareTreated :
      ∀ cell, cell ∈ pateCells ->
        scoreCellShare pateTargetSample pateTargetWeight
            (pateDoubleScore propensityScore treatedPrognosticScore
              controlPrognosticScore) cell =
          scoreCellShare pateTreatedSample pateTreatedWeight
            (pateDoubleScore propensityScore treatedPrognosticScore
              controlPrognosticScore) cell)
    (hpateShareControl :
      ∀ cell, cell ∈ pateCells ->
        scoreCellShare pateTargetSample pateTargetWeight
            (pateDoubleScore propensityScore treatedPrognosticScore
              controlPrognosticScore) cell =
          scoreCellShare pateControlSample pateControlWeight
            (pateDoubleScore propensityScore treatedPrognosticScore
              controlPrognosticScore) cell)
    (hpattShareControl :
      ∀ cell, cell ∈ pattCells ->
        scoreCellShare pattTargetSample pattTargetWeight
            (pattDoubleScore propensityScore pattControlPrognosticScore) cell =
          scoreCellShare pattControlSample pattControlWeight
            (pattDoubleScore propensityScore pattControlPrognosticScore) cell)
    (hpateScoreMeasTargetT :
      ∀ unit, unit ∈ pateTargetSample ->
        pateTargetOutcomeT unit =
          pateTreatedValue (treatedPrognosticScore unit))
    (hpateScoreMeasTreated :
      ∀ unit, unit ∈ pateTreatedSample ->
        pateTreatedOutcome unit =
          pateTreatedValue (treatedPrognosticScore unit))
    (hpateScoreMeasTargetC :
      ∀ unit, unit ∈ pateTargetSample ->
        pateTargetOutcomeC unit =
          pateControlValue (controlPrognosticScore unit))
    (hpateScoreMeasControl :
      ∀ unit, unit ∈ pateControlSample ->
        pateControlOutcome unit =
          pateControlValue (controlPrognosticScore unit))
    (hpattScoreMeasTargetT :
      ∀ unit, unit ∈ pattTargetSample ->
        pattTreatedTargetOutcome unit =
          pattTreatedCellValue
            (pattDoubleScore propensityScore pattControlPrognosticScore unit))
    (hpattScoreMeasTargetC :
      ∀ unit, unit ∈ pattTargetSample ->
        pattTargetControlOutcome unit =
          pattControlValue (pattControlPrognosticScore unit))
    (hpattScoreMeasControl :
      ∀ unit, unit ∈ pattControlSample ->
        pattControlOutcome unit =
          pattControlValue (pattControlPrognosticScore unit)) :
    (weightedSampleMeanContrast pateTargetSample pateTargetWeight
        pateTargetOutcomeT pateTargetOutcomeC =
        candidateCellMeanEffectShareAggregate pateTargetSample pateCells
          pateTargetWeight
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore)
          (treatedCellValueOnPATEDoubleScore pateTreatedValue)
          (controlCellValueOnPATEDoubleScore pateControlValue) ∧
      twoArmWeightedMeanContrast pateTreatedSample pateControlSample
          pateTreatedWeight pateControlWeight pateTreatedOutcome
          pateControlOutcome =
        candidateCellMeanEffectShareAggregate pateTargetSample pateCells
          pateTargetWeight
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore)
          (treatedCellValueOnPATEDoubleScore pateTreatedValue)
          (controlCellValueOnPATEDoubleScore pateControlValue) ∧
      weightedSampleMeanContrast pateTargetSample pateTargetWeight
          pateTargetOutcomeT pateTargetOutcomeC =
        twoArmWeightedMeanContrast pateTreatedSample pateControlSample
          pateTreatedWeight pateControlWeight pateTreatedOutcome
          pateControlOutcome) ∧
      (weightedSampleMeanContrast pattTargetSample pattTargetWeight
        pattTreatedTargetOutcome pattTargetControlOutcome =
        candidateCellMeanEffectShareAggregate pattTargetSample pattCells
          pattTargetWeight
          (pattDoubleScore propensityScore pattControlPrognosticScore)
          pattTreatedCellValue
          (controlCellValueOnPATTDoubleScore pattControlValue) ∧
      pattWeightedMeanContrast pattTargetSample pattControlSample
          pattTargetWeight pattControlWeight pattTreatedTargetOutcome
          pattControlOutcome =
        candidateCellMeanEffectShareAggregate pattTargetSample pattCells
          pattTargetWeight
          (pattDoubleScore propensityScore pattControlPrognosticScore)
          pattTreatedCellValue
          (controlCellValueOnPATTDoubleScore pattControlValue) ∧
      weightedSampleMeanContrast pattTargetSample pattTargetWeight
          pattTreatedTargetOutcome pattTargetControlOutcome =
        pattWeightedMeanContrast pattTargetSample pattControlSample
          pattTargetWeight pattControlWeight pattTreatedTargetOutcome
          pattControlOutcome) := by
  constructor
  · exact
      pate_common_effect_share_identification_of_pateDoubleScore
        pateTargetSample pateTreatedSample pateControlSample pateCells
        pateTargetWeight pateTreatedWeight pateControlWeight
        pateTargetOutcomeT pateTargetOutcomeC pateTreatedOutcome
        pateControlOutcome propensityScore treatedPrognosticScore
        controlPrognosticScore pateTreatedValue pateControlValue
        hpateCoverTarget hpateCoverTreated hpateCoverControl
        hpateMassTarget hpateMassTreated hpateMassControl
        hpateShareTreated hpateShareControl hpateScoreMeasTargetT
        hpateScoreMeasTreated hpateScoreMeasTargetC hpateScoreMeasControl
  · exact
      patt_common_effect_share_identification_of_pattDoubleScore
        pattTargetSample pattControlSample pattCells pattTargetWeight
        pattControlWeight pattTreatedTargetOutcome pattTargetControlOutcome
        pattControlOutcome propensityScore pattControlPrognosticScore
        pattTreatedCellValue pattControlValue hpattCoverTarget
        hpattCoverControl hpattMassTarget hpattMassControl hpattShareControl
        hpattScoreMeasTargetT hpattScoreMeasTargetC hpattScoreMeasControl

end WDSM
end Matching
end StatInference
