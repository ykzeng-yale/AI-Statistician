import StatInference.Matching.WDSM.DiscreteContrastErrorBounds
import StatInference.Matching.WDSM.DiscretePATEBalancing
import StatInference.Matching.WDSM.DiscretePATTBalancing

/-!
# Finite approximate score-cell balancing for WDSM

Exact equality of normalized score-cell shares is a useful deterministic
target, but asymptotic proofs usually prove approximate balancing.  This module
proves finite L1 share-error bounds: if outcomes are score-measurable with
bounded cell values, then weighted mean and contrast discrepancies are bounded
by the L1 distance between the corresponding normalized score-cell shares.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {UnitA UnitB TargetUnit TreatedUnit ControlUnit Cell : Type*}
  [DecidableEq Cell]

omit [DecidableEq Cell] in
theorem abs_cellShareAggregate_sub_le_l1_share_error
    (cells : Finset Cell) (shareA shareB mean : Cell -> Real)
    (envelope : Real)
    (hmean_bound : ∀ cell, cell ∈ cells -> |mean cell| ≤ envelope) :
    |cellShareAggregate cells shareA mean -
        cellShareAggregate cells shareB mean| ≤
      envelope * (∑ cell ∈ cells, |shareA cell - shareB cell|) := by
  unfold cellShareAggregate
  have hsub :
      (∑ cell ∈ cells, shareA cell * mean cell) -
          (∑ cell ∈ cells, shareB cell * mean cell) =
        ∑ cell ∈ cells, (shareA cell - shareB cell) * mean cell := by
    rw [← Finset.sum_sub_distrib]
    exact Finset.sum_congr rfl
      (fun cell _ => by ring)
  calc
    |(∑ cell ∈ cells, shareA cell * mean cell) -
        (∑ cell ∈ cells, shareB cell * mean cell)| =
        |∑ cell ∈ cells, (shareA cell - shareB cell) * mean cell| := by
          rw [hsub]
    _ ≤ ∑ cell ∈ cells, |(shareA cell - shareB cell) * mean cell| := by
        exact Finset.abs_sum_le_sum_abs _ _
    _ = ∑ cell ∈ cells, |shareA cell - shareB cell| * |mean cell| := by
        exact Finset.sum_congr rfl
          (fun cell _ => by rw [abs_mul])
    _ ≤ ∑ cell ∈ cells, |shareA cell - shareB cell| * envelope := by
        exact Finset.sum_le_sum
          (fun cell hcell =>
            mul_le_mul_of_nonneg_left (hmean_bound cell hcell)
              (abs_nonneg (shareA cell - shareB cell)))
    _ = envelope * (∑ cell ∈ cells, |shareA cell - shareB cell|) := by
        rw [← Finset.sum_mul]
        ring

theorem weightedSampleMean_eq_cellShareAggregate_of_scoreMeasurable
    (sample : Finset UnitA) (cells : Finset Cell)
    (weight outcome : UnitA -> Real) (score : UnitA -> Cell)
    (cellValue : Cell -> Real)
    (hcover : ∀ unit, unit ∈ sample -> score unit ∈ cells)
    (hmass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sample weight score cell ≠ 0)
    (hscoreMeas :
      ∀ unit, unit ∈ sample -> outcome unit = cellValue (score unit)) :
    weightedSampleMean sample weight outcome =
      cellShareAggregate cells
        (fun cell => scoreCellShare sample weight score cell)
        cellValue := by
  rw [← candidateCellMeanShareAggregate_eq_cellShareAggregate]
  rw [← candidateCellMeanAggregate_eq_candidateCellMeanShareAggregate]
  exact (candidateCellMeanAggregate_eq_weightedSampleMean_of_eq
    sample cells weight outcome score cellValue hcover hmass
    (fun cell hcell =>
      (scoreCellMean_eq_const_of_eq_on_cell sample weight outcome score
        cell (cellValue cell) (hmass cell hcell)
        (fun unit hunit hscore => by
          rw [hscoreMeas unit hunit, hscore])).symm)).symm

theorem abs_weightedSampleMean_sub_le_l1_scoreCellShare_of_scoreMeasurable
    (sampleA : Finset UnitA) (sampleB : Finset UnitB)
    (cells : Finset Cell)
    (weightA : UnitA -> Real) (weightB : UnitB -> Real)
    (outcomeA : UnitA -> Real) (outcomeB : UnitB -> Real)
    (scoreA : UnitA -> Cell) (scoreB : UnitB -> Cell)
    (cellValue : Cell -> Real) (envelope : Real)
    (hcoverA : ∀ unit, unit ∈ sampleA -> scoreA unit ∈ cells)
    (hcoverB : ∀ unit, unit ∈ sampleB -> scoreB unit ∈ cells)
    (hmassA :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sampleA weightA scoreA cell ≠ 0)
    (hmassB :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sampleB weightB scoreB cell ≠ 0)
    (hscoreMeasA :
      ∀ unit, unit ∈ sampleA -> outcomeA unit = cellValue (scoreA unit))
    (hscoreMeasB :
      ∀ unit, unit ∈ sampleB -> outcomeB unit = cellValue (scoreB unit))
    (hcell_bound : ∀ cell, cell ∈ cells -> |cellValue cell| ≤ envelope) :
    |weightedSampleMean sampleA weightA outcomeA -
        weightedSampleMean sampleB weightB outcomeB| ≤
      envelope *
        (∑ cell ∈ cells,
          |scoreCellShare sampleA weightA scoreA cell -
            scoreCellShare sampleB weightB scoreB cell|) := by
  rw [weightedSampleMean_eq_cellShareAggregate_of_scoreMeasurable
    sampleA cells weightA outcomeA scoreA cellValue hcoverA hmassA
    hscoreMeasA]
  rw [weightedSampleMean_eq_cellShareAggregate_of_scoreMeasurable
    sampleB cells weightB outcomeB scoreB cellValue hcoverB hmassB
    hscoreMeasB]
  exact abs_cellShareAggregate_sub_le_l1_share_error cells
    (fun cell => scoreCellShare sampleA weightA scoreA cell)
    (fun cell => scoreCellShare sampleB weightB scoreB cell)
    cellValue envelope hcell_bound

theorem abs_weightedSampleMeanContrast_sub_twoArmWeightedMeanContrast_le_l1_scoreCellShare
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
    (treatedEnvelope controlEnvelope : Real)
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
        controlOutcome unit = controlCellValue (controlScore unit))
    (htreated_bound :
      ∀ cell, cell ∈ cells -> |treatedCellValue cell| ≤ treatedEnvelope)
    (hcontrol_bound :
      ∀ cell, cell ∈ cells -> |controlCellValue cell| ≤ controlEnvelope) :
    |weightedSampleMeanContrast targetSample targetWeight
        targetOutcomeT targetOutcomeC -
      twoArmWeightedMeanContrast treatedSample controlSample
        treatedWeight controlWeight treatedOutcome controlOutcome| ≤
      treatedEnvelope *
        (∑ cell ∈ cells,
          |scoreCellShare targetSample targetWeight targetScore cell -
            scoreCellShare treatedSample treatedWeight treatedScore cell|) +
      controlEnvelope *
        (∑ cell ∈ cells,
          |scoreCellShare targetSample targetWeight targetScore cell -
            scoreCellShare controlSample controlWeight controlScore cell|) := by
  unfold weightedSampleMeanContrast twoArmWeightedMeanContrast
  exact abs_sub_contrast_le_add
    (weightedSampleMean targetSample targetWeight targetOutcomeT)
    (weightedSampleMean targetSample targetWeight targetOutcomeC)
    (weightedSampleMean treatedSample treatedWeight treatedOutcome)
    (weightedSampleMean controlSample controlWeight controlOutcome)
    (treatedEnvelope *
      (∑ cell ∈ cells,
        |scoreCellShare targetSample targetWeight targetScore cell -
          scoreCellShare treatedSample treatedWeight treatedScore cell|))
    (controlEnvelope *
      (∑ cell ∈ cells,
        |scoreCellShare targetSample targetWeight targetScore cell -
          scoreCellShare controlSample controlWeight controlScore cell|))
    (abs_weightedSampleMean_sub_le_l1_scoreCellShare_of_scoreMeasurable
      targetSample treatedSample cells targetWeight treatedWeight
      targetOutcomeT treatedOutcome targetScore treatedScore treatedCellValue
      treatedEnvelope hcoverTarget hcoverTreated hmassTarget hmassTreated
      hscoreMeasTargetT hscoreMeasTreated htreated_bound)
    (abs_weightedSampleMean_sub_le_l1_scoreCellShare_of_scoreMeasurable
      targetSample controlSample cells targetWeight controlWeight
      targetOutcomeC controlOutcome targetScore controlScore controlCellValue
      controlEnvelope hcoverTarget hcoverControl hmassTarget hmassControl
      hscoreMeasTargetC hscoreMeasControl hcontrol_bound)

theorem abs_weightedSampleMeanContrast_sub_pattWeightedMeanContrast_le_l1_scoreCellShare
    (targetSample : Finset TargetUnit)
    (controlSample : Finset ControlUnit)
    (cells : Finset Cell)
    (targetWeight : TargetUnit -> Real)
    (controlWeight : ControlUnit -> Real)
    (treatedTargetOutcome targetControlOutcome : TargetUnit -> Real)
    (controlOutcome : ControlUnit -> Real)
    (targetScore : TargetUnit -> Cell)
    (controlScore : ControlUnit -> Cell)
    (controlCellValue : Cell -> Real)
    (controlEnvelope : Real)
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
    (hscoreMeasTargetC :
      ∀ unit, unit ∈ targetSample ->
        targetControlOutcome unit = controlCellValue (targetScore unit))
    (hscoreMeasControl :
      ∀ unit, unit ∈ controlSample ->
        controlOutcome unit = controlCellValue (controlScore unit))
    (hcontrol_bound :
      ∀ cell, cell ∈ cells -> |controlCellValue cell| ≤ controlEnvelope) :
    |weightedSampleMeanContrast targetSample targetWeight
        treatedTargetOutcome targetControlOutcome -
      pattWeightedMeanContrast targetSample controlSample targetWeight
        controlWeight treatedTargetOutcome controlOutcome| ≤
      controlEnvelope *
        (∑ cell ∈ cells,
          |scoreCellShare targetSample targetWeight targetScore cell -
            scoreCellShare controlSample controlWeight controlScore cell|) := by
  unfold weightedSampleMeanContrast pattWeightedMeanContrast
  calc
    |(weightedSampleMean targetSample targetWeight treatedTargetOutcome -
        weightedSampleMean targetSample targetWeight targetControlOutcome) -
      (weightedSampleMean targetSample targetWeight treatedTargetOutcome -
        weightedSampleMean controlSample controlWeight controlOutcome)| =
        |weightedSampleMean controlSample controlWeight controlOutcome -
          weightedSampleMean targetSample targetWeight targetControlOutcome| := by
          congr 1
          ring
    _ = |weightedSampleMean targetSample targetWeight targetControlOutcome -
          weightedSampleMean controlSample controlWeight controlOutcome| := by
        rw [abs_sub_comm]
    _ ≤ controlEnvelope *
          (∑ cell ∈ cells,
            |scoreCellShare targetSample targetWeight targetScore cell -
              scoreCellShare controlSample controlWeight controlScore cell|) := by
        exact
          abs_weightedSampleMean_sub_le_l1_scoreCellShare_of_scoreMeasurable
            targetSample controlSample cells targetWeight controlWeight
            targetControlOutcome controlOutcome targetScore controlScore
            controlCellValue controlEnvelope hcoverTarget hcoverControl
            hmassTarget hmassControl hscoreMeasTargetC hscoreMeasControl
            hcontrol_bound

end WDSM
end Matching
end StatInference
