import StatInference.Matching.WDSM.DiscreteEffectShareIdentification

/-!
# Score-measurable discrete effect-share identification

This module discharges the candidate cell-mean equalities in the finite
effect-share identification bridge when target and arm outcomes are exactly
functions of their discrete score cells.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {TargetUnit TreatedUnit ControlUnit Cell : Type*} [DecidableEq Cell]

/--
Finite PATE effect-share identification from score-measurable potential and
observed outcomes.  The common candidate cell effects are the differences of
the treated/control score-cell value functions.
-/
theorem pate_common_effect_share_identification_of_scoreMeasurable
    (targetSample : Finset TargetUnit)
    (treatedSample : Finset TreatedUnit)
    (controlSample : Finset ControlUnit)
    (cells : Finset Cell)
    (targetWeight : TargetUnit -> Real)
    (treatedWeight : TreatedUnit -> Real)
    (controlWeight : ControlUnit -> Real)
    (targetOutcomeT targetOutcomeC : TargetUnit -> Real)
    (treatedOutcome : TreatedUnit -> Real)
    (controlOutcome : ControlUnit -> Real)
    (targetScore : TargetUnit -> Cell)
    (treatedScore : TreatedUnit -> Cell)
    (controlScore : ControlUnit -> Cell)
    (treatedCellValue controlCellValue : Cell -> Real)
    (hcoverTarget :
      ∀ unit, unit ∈ targetSample -> targetScore unit ∈ cells)
    (hcoverTreated :
      ∀ unit, unit ∈ treatedSample -> treatedScore unit ∈ cells)
    (hcoverControl :
      ∀ unit, unit ∈ controlSample -> controlScore unit ∈ cells)
    (hmassTarget :
      ∀ cell, cell ∈ cells ->
        scoreCellMass targetSample targetWeight targetScore cell ≠ 0)
    (hmassTreated :
      ∀ cell, cell ∈ cells ->
        scoreCellMass treatedSample treatedWeight treatedScore cell ≠ 0)
    (hmassControl :
      ∀ cell, cell ∈ cells ->
        scoreCellMass controlSample controlWeight controlScore cell ≠ 0)
    (hshareTreated :
      ∀ cell, cell ∈ cells ->
        scoreCellShare targetSample targetWeight targetScore cell =
          scoreCellShare treatedSample treatedWeight treatedScore cell)
    (hshareControl :
      ∀ cell, cell ∈ cells ->
        scoreCellShare targetSample targetWeight targetScore cell =
          scoreCellShare controlSample controlWeight controlScore cell)
    (hscoreMeasTargetT :
      ∀ unit, unit ∈ targetSample ->
        targetOutcomeT unit = treatedCellValue (targetScore unit))
    (hscoreMeasTreated :
      ∀ unit, unit ∈ treatedSample ->
        treatedOutcome unit = treatedCellValue (treatedScore unit))
    (hscoreMeasTargetC :
      ∀ unit, unit ∈ targetSample ->
        targetOutcomeC unit = controlCellValue (targetScore unit))
    (hscoreMeasControl :
      ∀ unit, unit ∈ controlSample ->
        controlOutcome unit = controlCellValue (controlScore unit)) :
    weightedSampleMeanContrast targetSample targetWeight
        targetOutcomeT targetOutcomeC =
        candidateCellMeanEffectShareAggregate targetSample cells targetWeight
          targetScore treatedCellValue controlCellValue ∧
      twoArmWeightedMeanContrast treatedSample controlSample treatedWeight
          controlWeight treatedOutcome controlOutcome =
        candidateCellMeanEffectShareAggregate targetSample cells targetWeight
          targetScore treatedCellValue controlCellValue ∧
      weightedSampleMeanContrast targetSample targetWeight
          targetOutcomeT targetOutcomeC =
        twoArmWeightedMeanContrast treatedSample controlSample
          treatedWeight controlWeight treatedOutcome controlOutcome := by
  refine pate_common_effect_share_identification
    targetSample treatedSample controlSample cells targetWeight treatedWeight
    controlWeight targetOutcomeT targetOutcomeC treatedOutcome controlOutcome
    targetScore treatedScore controlScore treatedCellValue controlCellValue
    hcoverTarget hcoverTreated hcoverControl hmassTarget hmassTreated
    hmassControl hshareTreated hshareControl ?_ ?_ ?_ ?_
  · intro cell hcell
    exact (scoreCellMean_eq_const_of_eq_on_cell
      targetSample targetWeight targetOutcomeT targetScore cell
      (treatedCellValue cell) (hmassTarget cell hcell)
      (fun unit hunit hscore => by
        rw [hscoreMeasTargetT unit hunit, hscore])).symm
  · intro cell hcell
    exact (scoreCellMean_eq_const_of_eq_on_cell
      targetSample targetWeight targetOutcomeC targetScore cell
      (controlCellValue cell) (hmassTarget cell hcell)
      (fun unit hunit hscore => by
        rw [hscoreMeasTargetC unit hunit, hscore])).symm
  · intro cell hcell
    exact (scoreCellMean_eq_const_of_eq_on_cell
      treatedSample treatedWeight treatedOutcome treatedScore cell
      (treatedCellValue cell) (hmassTreated cell hcell)
      (fun unit hunit hscore => by
        rw [hscoreMeasTreated unit hunit, hscore])).symm
  · intro cell hcell
    exact (scoreCellMean_eq_const_of_eq_on_cell
      controlSample controlWeight controlOutcome controlScore cell
      (controlCellValue cell) (hmassControl cell hcell)
      (fun unit hunit hscore => by
        rw [hscoreMeasControl unit hunit, hscore])).symm

/--
Finite PATT effect-share identification from score-measurable target treated
outcomes and target/observed control outcomes.
-/
theorem patt_common_effect_share_identification_of_scoreMeasurable
    (targetSample : Finset TargetUnit)
    (controlSample : Finset ControlUnit)
    (cells : Finset Cell)
    (targetWeight : TargetUnit -> Real)
    (controlWeight : ControlUnit -> Real)
    (treatedTargetOutcome targetControlOutcome : TargetUnit -> Real)
    (controlOutcome : ControlUnit -> Real)
    (targetScore : TargetUnit -> Cell)
    (controlScore : ControlUnit -> Cell)
    (treatedCellValue controlCellValue : Cell -> Real)
    (hcoverTarget :
      ∀ unit, unit ∈ targetSample -> targetScore unit ∈ cells)
    (hcoverControl :
      ∀ unit, unit ∈ controlSample -> controlScore unit ∈ cells)
    (hmassTarget :
      ∀ cell, cell ∈ cells ->
        scoreCellMass targetSample targetWeight targetScore cell ≠ 0)
    (hmassControl :
      ∀ cell, cell ∈ cells ->
        scoreCellMass controlSample controlWeight controlScore cell ≠ 0)
    (hshareControl :
      ∀ cell, cell ∈ cells ->
        scoreCellShare targetSample targetWeight targetScore cell =
          scoreCellShare controlSample controlWeight controlScore cell)
    (hscoreMeasTargetT :
      ∀ unit, unit ∈ targetSample ->
        treatedTargetOutcome unit = treatedCellValue (targetScore unit))
    (hscoreMeasTargetC :
      ∀ unit, unit ∈ targetSample ->
        targetControlOutcome unit = controlCellValue (targetScore unit))
    (hscoreMeasControl :
      ∀ unit, unit ∈ controlSample ->
        controlOutcome unit = controlCellValue (controlScore unit)) :
    weightedSampleMeanContrast targetSample targetWeight
        treatedTargetOutcome targetControlOutcome =
        candidateCellMeanEffectShareAggregate targetSample cells targetWeight
          targetScore treatedCellValue controlCellValue ∧
      pattWeightedMeanContrast targetSample controlSample targetWeight
          controlWeight treatedTargetOutcome controlOutcome =
        candidateCellMeanEffectShareAggregate targetSample cells targetWeight
          targetScore treatedCellValue controlCellValue ∧
      weightedSampleMeanContrast targetSample targetWeight
          treatedTargetOutcome targetControlOutcome =
        pattWeightedMeanContrast targetSample controlSample targetWeight
          controlWeight treatedTargetOutcome controlOutcome := by
  refine patt_common_effect_share_identification
    targetSample controlSample cells targetWeight controlWeight
    treatedTargetOutcome targetControlOutcome controlOutcome targetScore
    controlScore treatedCellValue controlCellValue hcoverTarget hcoverControl
    hmassTarget hmassControl hshareControl ?_ ?_ ?_
  · intro cell hcell
    exact (scoreCellMean_eq_const_of_eq_on_cell
      targetSample targetWeight treatedTargetOutcome targetScore cell
      (treatedCellValue cell) (hmassTarget cell hcell)
      (fun unit hunit hscore => by
        rw [hscoreMeasTargetT unit hunit, hscore])).symm
  · intro cell hcell
    exact (scoreCellMean_eq_const_of_eq_on_cell
      targetSample targetWeight targetControlOutcome targetScore cell
      (controlCellValue cell) (hmassTarget cell hcell)
      (fun unit hunit hscore => by
        rw [hscoreMeasTargetC unit hunit, hscore])).symm
  · intro cell hcell
    exact (scoreCellMean_eq_const_of_eq_on_cell
      controlSample controlWeight controlOutcome controlScore cell
      (controlCellValue cell) (hmassControl cell hcell)
      (fun unit hunit hscore => by
        rw [hscoreMeasControl unit hunit, hscore])).symm

end WDSM
end Matching
end StatInference
