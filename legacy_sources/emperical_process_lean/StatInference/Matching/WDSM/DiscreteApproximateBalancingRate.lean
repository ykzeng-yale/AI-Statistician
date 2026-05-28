import StatInference.Matching.WDSM.DiscreteApproximateBalancing
import StatInference.Matching.WDSM.ScaledSqueezeAlgebra

/-!
# Rate transfer for finite approximate score-cell balancing

This module turns the finite approximate-balancing inequalities into real
`Tendsto` statements.  Once a stochastic layer proves that normalized
score-cell share L1 imbalance vanishes at the needed rate, these theorems give
the corresponding weighted mean and contrast negligibility conclusions.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter
open scoped BigOperators

variable {Index UnitA UnitB TargetUnit TreatedUnit ControlUnit Cell : Type*}
  [DecidableEq Cell]
variable {l : Filter Index}

/-- L1 distance between two normalized score-cell share vectors. -/
noncomputable def l1ScoreCellShareDistance
    (cells : Finset Cell)
    (sampleA : Finset UnitA) (sampleB : Finset UnitB)
    (weightA : UnitA -> Real) (weightB : UnitB -> Real)
    (scoreA : UnitA -> Cell) (scoreB : UnitB -> Cell) : Real :=
  ∑ cell ∈ cells,
    |scoreCellShare sampleA weightA scoreA cell -
      scoreCellShare sampleB weightB scoreB cell|

theorem tendsto_weightedSampleMean_difference_zero_of_l1_scoreCellShare
    (sampleA : Index -> Finset UnitA)
    (sampleB : Index -> Finset UnitB)
    (cells : Index -> Finset Cell)
    (weightA : Index -> UnitA -> Real)
    (weightB : Index -> UnitB -> Real)
    (outcomeA : Index -> UnitA -> Real)
    (outcomeB : Index -> UnitB -> Real)
    (scoreA : Index -> UnitA -> Cell)
    (scoreB : Index -> UnitB -> Cell)
    (cellValue : Index -> Cell -> Real)
    (envelope : Index -> Real)
    (hcoverA :
      ∀ index unit, unit ∈ sampleA index ->
        scoreA index unit ∈ cells index)
    (hcoverB :
      ∀ index unit, unit ∈ sampleB index ->
        scoreB index unit ∈ cells index)
    (hmassA :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (sampleA index) (weightA index)
          (scoreA index) cell ≠ 0)
    (hmassB :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (sampleB index) (weightB index)
          (scoreB index) cell ≠ 0)
    (hscoreMeasA :
      ∀ index unit, unit ∈ sampleA index ->
        outcomeA index unit = cellValue index (scoreA index unit))
    (hscoreMeasB :
      ∀ index unit, unit ∈ sampleB index ->
        outcomeB index unit = cellValue index (scoreB index unit))
    (hcell_bound :
      ∀ index cell, cell ∈ cells index ->
        |cellValue index cell| ≤ envelope index)
    (hrate :
      Tendsto
        (fun index =>
          envelope index *
            l1ScoreCellShareDistance (cells index) (sampleA index)
              (sampleB index) (weightA index) (weightB index)
              (scoreA index) (scoreB index))
        l (nhds 0)) :
    Tendsto
      (fun index =>
        weightedSampleMean (sampleA index) (weightA index)
          (outcomeA index) -
        weightedSampleMean (sampleB index) (weightB index)
          (outcomeB index))
      l (nhds 0) := by
  exact tendsto_zero_of_abs_le_bound
    (fun index =>
      weightedSampleMean (sampleA index) (weightA index)
        (outcomeA index) -
      weightedSampleMean (sampleB index) (weightB index)
        (outcomeB index))
    (fun index =>
      envelope index *
        l1ScoreCellShareDistance (cells index) (sampleA index)
          (sampleB index) (weightA index) (weightB index)
          (scoreA index) (scoreB index))
    (fun index => by
      unfold l1ScoreCellShareDistance
      exact
        abs_weightedSampleMean_sub_le_l1_scoreCellShare_of_scoreMeasurable
          (sampleA index) (sampleB index) (cells index)
          (weightA index) (weightB index) (outcomeA index)
          (outcomeB index) (scoreA index) (scoreB index)
          (cellValue index) (envelope index)
          (hcoverA index) (hcoverB index) (hmassA index) (hmassB index)
          (hscoreMeasA index) (hscoreMeasB index) (hcell_bound index))
    hrate

theorem tendsto_weightedSampleMeanContrast_difference_zero_of_l1_scoreCellShare
    (targetSample : Index -> Finset TargetUnit)
    (treatedSample : Index -> Finset TreatedUnit)
    (controlSample : Index -> Finset ControlUnit)
    (cells : Index -> Finset Cell)
    (targetWeight : Index -> TargetUnit -> Real)
    (treatedWeight : Index -> TreatedUnit -> Real)
    (controlWeight : Index -> ControlUnit -> Real)
    (targetOutcomeT targetOutcomeC : Index -> TargetUnit -> Real)
    (treatedOutcome : Index -> TreatedUnit -> Real)
    (controlOutcome : Index -> ControlUnit -> Real)
    (targetScore : Index -> TargetUnit -> Cell)
    (treatedScore : Index -> TreatedUnit -> Cell)
    (controlScore : Index -> ControlUnit -> Cell)
    (treatedCellValue controlCellValue : Index -> Cell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (hcoverTarget :
      ∀ index unit, unit ∈ targetSample index ->
        targetScore index unit ∈ cells index)
    (hcoverTreated :
      ∀ index unit, unit ∈ treatedSample index ->
        treatedScore index unit ∈ cells index)
    (hcoverControl :
      ∀ index unit, unit ∈ controlSample index ->
        controlScore index unit ∈ cells index)
    (hmassTarget :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (targetSample index) (targetWeight index)
          (targetScore index) cell ≠ 0)
    (hmassTreated :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (treatedSample index) (treatedWeight index)
          (treatedScore index) cell ≠ 0)
    (hmassControl :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (controlSample index) (controlWeight index)
          (controlScore index) cell ≠ 0)
    (hscoreMeasTargetT :
      ∀ index unit, unit ∈ targetSample index ->
        targetOutcomeT index unit =
          treatedCellValue index (targetScore index unit))
    (hscoreMeasTreated :
      ∀ index unit, unit ∈ treatedSample index ->
        treatedOutcome index unit =
          treatedCellValue index (treatedScore index unit))
    (hscoreMeasTargetC :
      ∀ index unit, unit ∈ targetSample index ->
        targetOutcomeC index unit =
          controlCellValue index (targetScore index unit))
    (hscoreMeasControl :
      ∀ index unit, unit ∈ controlSample index ->
        controlOutcome index unit =
          controlCellValue index (controlScore index unit))
    (htreated_bound :
      ∀ index cell, cell ∈ cells index ->
        |treatedCellValue index cell| ≤ treatedEnvelope index)
    (hcontrol_bound :
      ∀ index cell, cell ∈ cells index ->
        |controlCellValue index cell| ≤ controlEnvelope index)
    (hrate :
      Tendsto
        (fun index =>
          treatedEnvelope index *
            l1ScoreCellShareDistance (cells index) (targetSample index)
              (treatedSample index) (targetWeight index)
              (treatedWeight index) (targetScore index)
              (treatedScore index) +
          controlEnvelope index *
            l1ScoreCellShareDistance (cells index) (targetSample index)
              (controlSample index) (targetWeight index)
              (controlWeight index) (targetScore index)
              (controlScore index))
        l (nhds 0)) :
    Tendsto
      (fun index =>
        weightedSampleMeanContrast (targetSample index) (targetWeight index)
          (targetOutcomeT index) (targetOutcomeC index) -
        twoArmWeightedMeanContrast (treatedSample index) (controlSample index)
          (treatedWeight index) (controlWeight index)
          (treatedOutcome index) (controlOutcome index))
      l (nhds 0) := by
  exact tendsto_zero_of_abs_le_bound
    (fun index =>
      weightedSampleMeanContrast (targetSample index) (targetWeight index)
        (targetOutcomeT index) (targetOutcomeC index) -
      twoArmWeightedMeanContrast (treatedSample index) (controlSample index)
        (treatedWeight index) (controlWeight index)
        (treatedOutcome index) (controlOutcome index))
    (fun index =>
      treatedEnvelope index *
        l1ScoreCellShareDistance (cells index) (targetSample index)
          (treatedSample index) (targetWeight index)
          (treatedWeight index) (targetScore index) (treatedScore index) +
      controlEnvelope index *
        l1ScoreCellShareDistance (cells index) (targetSample index)
          (controlSample index) (targetWeight index)
          (controlWeight index) (targetScore index) (controlScore index))
    (fun index => by
      unfold l1ScoreCellShareDistance
      exact
        abs_weightedSampleMeanContrast_sub_twoArmWeightedMeanContrast_le_l1_scoreCellShare
          (targetSample index) (treatedSample index) (controlSample index)
          (cells index) (targetWeight index) (treatedWeight index)
          (controlWeight index) (targetOutcomeT index) (targetOutcomeC index)
          (treatedOutcome index) (controlOutcome index)
          (targetScore index) (treatedScore index) (controlScore index)
          (treatedCellValue index) (controlCellValue index)
          (treatedEnvelope index) (controlEnvelope index)
          (hcoverTarget index) (hcoverTreated index) (hcoverControl index)
          (hmassTarget index) (hmassTreated index) (hmassControl index)
          (hscoreMeasTargetT index) (hscoreMeasTreated index)
          (hscoreMeasTargetC index) (hscoreMeasControl index)
          (htreated_bound index) (hcontrol_bound index))
    hrate

theorem tendsto_scaled_weightedSampleMeanContrast_difference_zero_of_l1_scoreCellShare
    (scale : Index -> Real)
    (targetSample : Index -> Finset TargetUnit)
    (treatedSample : Index -> Finset TreatedUnit)
    (controlSample : Index -> Finset ControlUnit)
    (cells : Index -> Finset Cell)
    (targetWeight : Index -> TargetUnit -> Real)
    (treatedWeight : Index -> TreatedUnit -> Real)
    (controlWeight : Index -> ControlUnit -> Real)
    (targetOutcomeT targetOutcomeC : Index -> TargetUnit -> Real)
    (treatedOutcome : Index -> TreatedUnit -> Real)
    (controlOutcome : Index -> ControlUnit -> Real)
    (targetScore : Index -> TargetUnit -> Cell)
    (treatedScore : Index -> TreatedUnit -> Cell)
    (controlScore : Index -> ControlUnit -> Cell)
    (treatedCellValue controlCellValue : Index -> Cell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hcoverTarget :
      ∀ index unit, unit ∈ targetSample index ->
        targetScore index unit ∈ cells index)
    (hcoverTreated :
      ∀ index unit, unit ∈ treatedSample index ->
        treatedScore index unit ∈ cells index)
    (hcoverControl :
      ∀ index unit, unit ∈ controlSample index ->
        controlScore index unit ∈ cells index)
    (hmassTarget :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (targetSample index) (targetWeight index)
          (targetScore index) cell ≠ 0)
    (hmassTreated :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (treatedSample index) (treatedWeight index)
          (treatedScore index) cell ≠ 0)
    (hmassControl :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (controlSample index) (controlWeight index)
          (controlScore index) cell ≠ 0)
    (hscoreMeasTargetT :
      ∀ index unit, unit ∈ targetSample index ->
        targetOutcomeT index unit =
          treatedCellValue index (targetScore index unit))
    (hscoreMeasTreated :
      ∀ index unit, unit ∈ treatedSample index ->
        treatedOutcome index unit =
          treatedCellValue index (treatedScore index unit))
    (hscoreMeasTargetC :
      ∀ index unit, unit ∈ targetSample index ->
        targetOutcomeC index unit =
          controlCellValue index (targetScore index unit))
    (hscoreMeasControl :
      ∀ index unit, unit ∈ controlSample index ->
        controlOutcome index unit =
          controlCellValue index (controlScore index unit))
    (htreated_bound :
      ∀ index cell, cell ∈ cells index ->
        |treatedCellValue index cell| ≤ treatedEnvelope index)
    (hcontrol_bound :
      ∀ index cell, cell ∈ cells index ->
        |controlCellValue index cell| ≤ controlEnvelope index)
    (hscaled_rate :
      Tendsto
        (fun index =>
          scale index *
            (treatedEnvelope index *
              l1ScoreCellShareDistance (cells index) (targetSample index)
                (treatedSample index) (targetWeight index)
                (treatedWeight index) (targetScore index)
                (treatedScore index) +
            controlEnvelope index *
              l1ScoreCellShareDistance (cells index) (targetSample index)
                (controlSample index) (targetWeight index)
                (controlWeight index) (targetScore index)
                (controlScore index)))
        l (nhds 0)) :
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
  exact tendsto_scaled_zero_of_abs_le_bound
    scale
    (fun index =>
      weightedSampleMeanContrast (targetSample index) (targetWeight index)
        (targetOutcomeT index) (targetOutcomeC index) -
      twoArmWeightedMeanContrast (treatedSample index) (controlSample index)
        (treatedWeight index) (controlWeight index)
        (treatedOutcome index) (controlOutcome index))
    (fun index =>
      treatedEnvelope index *
        l1ScoreCellShareDistance (cells index) (targetSample index)
          (treatedSample index) (targetWeight index)
          (treatedWeight index) (targetScore index) (treatedScore index) +
      controlEnvelope index *
        l1ScoreCellShareDistance (cells index) (targetSample index)
          (controlSample index) (targetWeight index)
          (controlWeight index) (targetScore index) (controlScore index))
    hscale_nonneg
    (fun index => by
      unfold l1ScoreCellShareDistance
      exact
        abs_weightedSampleMeanContrast_sub_twoArmWeightedMeanContrast_le_l1_scoreCellShare
          (targetSample index) (treatedSample index) (controlSample index)
          (cells index) (targetWeight index) (treatedWeight index)
          (controlWeight index) (targetOutcomeT index) (targetOutcomeC index)
          (treatedOutcome index) (controlOutcome index)
          (targetScore index) (treatedScore index) (controlScore index)
          (treatedCellValue index) (controlCellValue index)
          (treatedEnvelope index) (controlEnvelope index)
          (hcoverTarget index) (hcoverTreated index) (hcoverControl index)
          (hmassTarget index) (hmassTreated index) (hmassControl index)
          (hscoreMeasTargetT index) (hscoreMeasTreated index)
          (hscoreMeasTargetC index) (hscoreMeasControl index)
          (htreated_bound index) (hcontrol_bound index))
    hscaled_rate

theorem tendsto_pattWeightedMeanContrast_difference_zero_of_l1_scoreCellShare
    (targetSample : Index -> Finset TargetUnit)
    (controlSample : Index -> Finset ControlUnit)
    (cells : Index -> Finset Cell)
    (targetWeight : Index -> TargetUnit -> Real)
    (controlWeight : Index -> ControlUnit -> Real)
    (treatedTargetOutcome targetControlOutcome : Index -> TargetUnit -> Real)
    (controlOutcome : Index -> ControlUnit -> Real)
    (targetScore : Index -> TargetUnit -> Cell)
    (controlScore : Index -> ControlUnit -> Cell)
    (controlCellValue : Index -> Cell -> Real)
    (controlEnvelope : Index -> Real)
    (hcoverTarget :
      ∀ index unit, unit ∈ targetSample index ->
        targetScore index unit ∈ cells index)
    (hcoverControl :
      ∀ index unit, unit ∈ controlSample index ->
        controlScore index unit ∈ cells index)
    (hmassTarget :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (targetSample index) (targetWeight index)
          (targetScore index) cell ≠ 0)
    (hmassControl :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (controlSample index) (controlWeight index)
          (controlScore index) cell ≠ 0)
    (hscoreMeasTargetC :
      ∀ index unit, unit ∈ targetSample index ->
        targetControlOutcome index unit =
          controlCellValue index (targetScore index unit))
    (hscoreMeasControl :
      ∀ index unit, unit ∈ controlSample index ->
        controlOutcome index unit =
          controlCellValue index (controlScore index unit))
    (hcontrol_bound :
      ∀ index cell, cell ∈ cells index ->
        |controlCellValue index cell| ≤ controlEnvelope index)
    (hrate :
      Tendsto
        (fun index =>
          controlEnvelope index *
            l1ScoreCellShareDistance (cells index) (targetSample index)
              (controlSample index) (targetWeight index)
              (controlWeight index) (targetScore index)
              (controlScore index))
        l (nhds 0)) :
    Tendsto
      (fun index =>
        weightedSampleMeanContrast (targetSample index) (targetWeight index)
          (treatedTargetOutcome index) (targetControlOutcome index) -
        pattWeightedMeanContrast (targetSample index) (controlSample index)
          (targetWeight index) (controlWeight index)
          (treatedTargetOutcome index) (controlOutcome index))
      l (nhds 0) := by
  exact tendsto_zero_of_abs_le_bound
    (fun index =>
      weightedSampleMeanContrast (targetSample index) (targetWeight index)
        (treatedTargetOutcome index) (targetControlOutcome index) -
      pattWeightedMeanContrast (targetSample index) (controlSample index)
        (targetWeight index) (controlWeight index)
        (treatedTargetOutcome index) (controlOutcome index))
    (fun index =>
      controlEnvelope index *
        l1ScoreCellShareDistance (cells index) (targetSample index)
          (controlSample index) (targetWeight index) (controlWeight index)
          (targetScore index) (controlScore index))
    (fun index => by
      unfold l1ScoreCellShareDistance
      exact
        abs_weightedSampleMeanContrast_sub_pattWeightedMeanContrast_le_l1_scoreCellShare
          (targetSample index) (controlSample index) (cells index)
          (targetWeight index) (controlWeight index)
          (treatedTargetOutcome index) (targetControlOutcome index)
          (controlOutcome index) (targetScore index) (controlScore index)
          (controlCellValue index) (controlEnvelope index)
          (hcoverTarget index) (hcoverControl index) (hmassTarget index)
          (hmassControl index) (hscoreMeasTargetC index)
          (hscoreMeasControl index) (hcontrol_bound index))
    hrate

theorem tendsto_scaled_pattWeightedMeanContrast_difference_zero_of_l1_scoreCellShare
    (scale : Index -> Real)
    (targetSample : Index -> Finset TargetUnit)
    (controlSample : Index -> Finset ControlUnit)
    (cells : Index -> Finset Cell)
    (targetWeight : Index -> TargetUnit -> Real)
    (controlWeight : Index -> ControlUnit -> Real)
    (treatedTargetOutcome targetControlOutcome : Index -> TargetUnit -> Real)
    (controlOutcome : Index -> ControlUnit -> Real)
    (targetScore : Index -> TargetUnit -> Cell)
    (controlScore : Index -> ControlUnit -> Cell)
    (controlCellValue : Index -> Cell -> Real)
    (controlEnvelope : Index -> Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hcoverTarget :
      ∀ index unit, unit ∈ targetSample index ->
        targetScore index unit ∈ cells index)
    (hcoverControl :
      ∀ index unit, unit ∈ controlSample index ->
        controlScore index unit ∈ cells index)
    (hmassTarget :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (targetSample index) (targetWeight index)
          (targetScore index) cell ≠ 0)
    (hmassControl :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (controlSample index) (controlWeight index)
          (controlScore index) cell ≠ 0)
    (hscoreMeasTargetC :
      ∀ index unit, unit ∈ targetSample index ->
        targetControlOutcome index unit =
          controlCellValue index (targetScore index unit))
    (hscoreMeasControl :
      ∀ index unit, unit ∈ controlSample index ->
        controlOutcome index unit =
          controlCellValue index (controlScore index unit))
    (hcontrol_bound :
      ∀ index cell, cell ∈ cells index ->
        |controlCellValue index cell| ≤ controlEnvelope index)
    (hscaled_rate :
      Tendsto
        (fun index =>
          scale index *
            (controlEnvelope index *
              l1ScoreCellShareDistance (cells index) (targetSample index)
                (controlSample index) (targetWeight index)
                (controlWeight index) (targetScore index)
                (controlScore index)))
        l (nhds 0)) :
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
  exact tendsto_scaled_zero_of_abs_le_bound
    scale
    (fun index =>
      weightedSampleMeanContrast (targetSample index) (targetWeight index)
        (treatedTargetOutcome index) (targetControlOutcome index) -
      pattWeightedMeanContrast (targetSample index) (controlSample index)
        (targetWeight index) (controlWeight index)
        (treatedTargetOutcome index) (controlOutcome index))
    (fun index =>
      controlEnvelope index *
        l1ScoreCellShareDistance (cells index) (targetSample index)
          (controlSample index) (targetWeight index) (controlWeight index)
          (targetScore index) (controlScore index))
    hscale_nonneg
    (fun index => by
      unfold l1ScoreCellShareDistance
      exact
        abs_weightedSampleMeanContrast_sub_pattWeightedMeanContrast_le_l1_scoreCellShare
          (targetSample index) (controlSample index) (cells index)
          (targetWeight index) (controlWeight index)
          (treatedTargetOutcome index) (targetControlOutcome index)
          (controlOutcome index) (targetScore index) (controlScore index)
          (controlCellValue index) (controlEnvelope index)
          (hcoverTarget index) (hcoverControl index) (hmassTarget index)
          (hmassControl index) (hscoreMeasTargetC index)
          (hscoreMeasControl index) (hcontrol_bound index))
    hscaled_rate

theorem tendsto_weightedSampleMeanContrast_difference_zero_of_eventually_l1_scoreCellShare
    (targetSample : Index -> Finset TargetUnit)
    (treatedSample : Index -> Finset TreatedUnit)
    (controlSample : Index -> Finset ControlUnit)
    (cells : Index -> Finset Cell)
    (targetWeight : Index -> TargetUnit -> Real)
    (treatedWeight : Index -> TreatedUnit -> Real)
    (controlWeight : Index -> ControlUnit -> Real)
    (targetOutcomeT targetOutcomeC : Index -> TargetUnit -> Real)
    (treatedOutcome : Index -> TreatedUnit -> Real)
    (controlOutcome : Index -> ControlUnit -> Real)
    (targetScore : Index -> TargetUnit -> Cell)
    (treatedScore : Index -> TreatedUnit -> Cell)
    (controlScore : Index -> ControlUnit -> Cell)
    (treatedCellValue controlCellValue : Index -> Cell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (hcoverTarget :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          targetScore index unit ∈ cells index)
    (hcoverTreated :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ treatedSample index ->
          treatedScore index unit ∈ cells index)
    (hcoverControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          controlScore index unit ∈ cells index)
    (hmassTarget :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          scoreCellMass (targetSample index) (targetWeight index)
            (targetScore index) cell ≠ 0)
    (hmassTreated :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          scoreCellMass (treatedSample index) (treatedWeight index)
            (treatedScore index) cell ≠ 0)
    (hmassControl :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          scoreCellMass (controlSample index) (controlWeight index)
            (controlScore index) cell ≠ 0)
    (hscoreMeasTargetT :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          targetOutcomeT index unit =
            treatedCellValue index (targetScore index unit))
    (hscoreMeasTreated :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ treatedSample index ->
          treatedOutcome index unit =
            treatedCellValue index (treatedScore index unit))
    (hscoreMeasTargetC :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          targetOutcomeC index unit =
            controlCellValue index (targetScore index unit))
    (hscoreMeasControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          controlOutcome index unit =
            controlCellValue index (controlScore index unit))
    (htreated_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          |treatedCellValue index cell| ≤ treatedEnvelope index)
    (hcontrol_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          |controlCellValue index cell| ≤ controlEnvelope index)
    (hrate :
      Tendsto
        (fun index =>
          treatedEnvelope index *
            l1ScoreCellShareDistance (cells index) (targetSample index)
              (treatedSample index) (targetWeight index)
              (treatedWeight index) (targetScore index)
              (treatedScore index) +
          controlEnvelope index *
            l1ScoreCellShareDistance (cells index) (targetSample index)
              (controlSample index) (targetWeight index)
              (controlWeight index) (targetScore index)
              (controlScore index))
        l (nhds 0)) :
    Tendsto
      (fun index =>
        weightedSampleMeanContrast (targetSample index) (targetWeight index)
          (targetOutcomeT index) (targetOutcomeC index) -
        twoArmWeightedMeanContrast (treatedSample index) (controlSample index)
          (treatedWeight index) (controlWeight index)
          (treatedOutcome index) (controlOutcome index))
      l (nhds 0) := by
  have hbound :
      ∀ᶠ index in l,
        |weightedSampleMeanContrast (targetSample index) (targetWeight index)
            (targetOutcomeT index) (targetOutcomeC index) -
          twoArmWeightedMeanContrast (treatedSample index)
            (controlSample index) (treatedWeight index)
            (controlWeight index) (treatedOutcome index)
            (controlOutcome index)| ≤
          treatedEnvelope index *
            l1ScoreCellShareDistance (cells index) (targetSample index)
              (treatedSample index) (targetWeight index)
              (treatedWeight index) (targetScore index)
              (treatedScore index) +
          controlEnvelope index *
            l1ScoreCellShareDistance (cells index) (targetSample index)
              (controlSample index) (targetWeight index)
              (controlWeight index) (targetScore index)
              (controlScore index) := by
    filter_upwards [hcoverTarget, hcoverTreated, hcoverControl, hmassTarget,
      hmassTreated, hmassControl, hscoreMeasTargetT, hscoreMeasTreated,
      hscoreMeasTargetC, hscoreMeasControl, htreated_bound,
      hcontrol_bound] with index hcoverTarget_index hcoverTreated_index
      hcoverControl_index hmassTarget_index hmassTreated_index
      hmassControl_index hscoreMeasTargetT_index hscoreMeasTreated_index
      hscoreMeasTargetC_index hscoreMeasControl_index htreated_bound_index
      hcontrol_bound_index
    unfold l1ScoreCellShareDistance
    exact
      abs_weightedSampleMeanContrast_sub_twoArmWeightedMeanContrast_le_l1_scoreCellShare
        (targetSample index) (treatedSample index) (controlSample index)
        (cells index) (targetWeight index) (treatedWeight index)
        (controlWeight index) (targetOutcomeT index) (targetOutcomeC index)
        (treatedOutcome index) (controlOutcome index)
        (targetScore index) (treatedScore index) (controlScore index)
        (treatedCellValue index) (controlCellValue index)
        (treatedEnvelope index) (controlEnvelope index)
        hcoverTarget_index hcoverTreated_index hcoverControl_index
        hmassTarget_index hmassTreated_index hmassControl_index
        hscoreMeasTargetT_index hscoreMeasTreated_index
        hscoreMeasTargetC_index hscoreMeasControl_index
        htreated_bound_index hcontrol_bound_index
  exact tendsto_zero_of_eventually_abs_le_bound
    (fun index =>
      weightedSampleMeanContrast (targetSample index) (targetWeight index)
        (targetOutcomeT index) (targetOutcomeC index) -
      twoArmWeightedMeanContrast (treatedSample index) (controlSample index)
        (treatedWeight index) (controlWeight index)
        (treatedOutcome index) (controlOutcome index))
    (fun index =>
      treatedEnvelope index *
        l1ScoreCellShareDistance (cells index) (targetSample index)
          (treatedSample index) (targetWeight index) (treatedWeight index)
          (targetScore index) (treatedScore index) +
      controlEnvelope index *
        l1ScoreCellShareDistance (cells index) (targetSample index)
          (controlSample index) (targetWeight index) (controlWeight index)
          (targetScore index) (controlScore index))
    hbound hrate

theorem tendsto_scaled_weightedSampleMeanContrast_difference_zero_of_eventually_l1_scoreCellShare
    (scale : Index -> Real)
    (targetSample : Index -> Finset TargetUnit)
    (treatedSample : Index -> Finset TreatedUnit)
    (controlSample : Index -> Finset ControlUnit)
    (cells : Index -> Finset Cell)
    (targetWeight : Index -> TargetUnit -> Real)
    (treatedWeight : Index -> TreatedUnit -> Real)
    (controlWeight : Index -> ControlUnit -> Real)
    (targetOutcomeT targetOutcomeC : Index -> TargetUnit -> Real)
    (treatedOutcome : Index -> TreatedUnit -> Real)
    (controlOutcome : Index -> ControlUnit -> Real)
    (targetScore : Index -> TargetUnit -> Cell)
    (treatedScore : Index -> TreatedUnit -> Cell)
    (controlScore : Index -> ControlUnit -> Cell)
    (treatedCellValue controlCellValue : Index -> Cell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (hscale_nonneg : ∀ᶠ index in l, 0 ≤ scale index)
    (hcoverTarget :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          targetScore index unit ∈ cells index)
    (hcoverTreated :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ treatedSample index ->
          treatedScore index unit ∈ cells index)
    (hcoverControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          controlScore index unit ∈ cells index)
    (hmassTarget :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          scoreCellMass (targetSample index) (targetWeight index)
            (targetScore index) cell ≠ 0)
    (hmassTreated :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          scoreCellMass (treatedSample index) (treatedWeight index)
            (treatedScore index) cell ≠ 0)
    (hmassControl :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          scoreCellMass (controlSample index) (controlWeight index)
            (controlScore index) cell ≠ 0)
    (hscoreMeasTargetT :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          targetOutcomeT index unit =
            treatedCellValue index (targetScore index unit))
    (hscoreMeasTreated :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ treatedSample index ->
          treatedOutcome index unit =
            treatedCellValue index (treatedScore index unit))
    (hscoreMeasTargetC :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          targetOutcomeC index unit =
            controlCellValue index (targetScore index unit))
    (hscoreMeasControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          controlOutcome index unit =
            controlCellValue index (controlScore index unit))
    (htreated_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          |treatedCellValue index cell| ≤ treatedEnvelope index)
    (hcontrol_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          |controlCellValue index cell| ≤ controlEnvelope index)
    (hscaled_rate :
      Tendsto
        (fun index =>
          scale index *
            (treatedEnvelope index *
              l1ScoreCellShareDistance (cells index) (targetSample index)
                (treatedSample index) (targetWeight index)
                (treatedWeight index) (targetScore index)
                (treatedScore index) +
            controlEnvelope index *
              l1ScoreCellShareDistance (cells index) (targetSample index)
                (controlSample index) (targetWeight index)
                (controlWeight index) (targetScore index)
                (controlScore index)))
        l (nhds 0)) :
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
  have hbound :
      ∀ᶠ index in l,
        |weightedSampleMeanContrast (targetSample index) (targetWeight index)
            (targetOutcomeT index) (targetOutcomeC index) -
          twoArmWeightedMeanContrast (treatedSample index)
            (controlSample index) (treatedWeight index)
            (controlWeight index) (treatedOutcome index)
            (controlOutcome index)| ≤
          treatedEnvelope index *
            l1ScoreCellShareDistance (cells index) (targetSample index)
              (treatedSample index) (targetWeight index)
              (treatedWeight index) (targetScore index)
              (treatedScore index) +
          controlEnvelope index *
            l1ScoreCellShareDistance (cells index) (targetSample index)
              (controlSample index) (targetWeight index)
              (controlWeight index) (targetScore index)
              (controlScore index) := by
    filter_upwards [hcoverTarget, hcoverTreated, hcoverControl, hmassTarget,
      hmassTreated, hmassControl, hscoreMeasTargetT, hscoreMeasTreated,
      hscoreMeasTargetC, hscoreMeasControl, htreated_bound,
      hcontrol_bound] with index hcoverTarget_index hcoverTreated_index
      hcoverControl_index hmassTarget_index hmassTreated_index
      hmassControl_index hscoreMeasTargetT_index hscoreMeasTreated_index
      hscoreMeasTargetC_index hscoreMeasControl_index htreated_bound_index
      hcontrol_bound_index
    unfold l1ScoreCellShareDistance
    exact
      abs_weightedSampleMeanContrast_sub_twoArmWeightedMeanContrast_le_l1_scoreCellShare
        (targetSample index) (treatedSample index) (controlSample index)
        (cells index) (targetWeight index) (treatedWeight index)
        (controlWeight index) (targetOutcomeT index) (targetOutcomeC index)
        (treatedOutcome index) (controlOutcome index)
        (targetScore index) (treatedScore index) (controlScore index)
        (treatedCellValue index) (controlCellValue index)
        (treatedEnvelope index) (controlEnvelope index)
        hcoverTarget_index hcoverTreated_index hcoverControl_index
        hmassTarget_index hmassTreated_index hmassControl_index
        hscoreMeasTargetT_index hscoreMeasTreated_index
        hscoreMeasTargetC_index hscoreMeasControl_index
        htreated_bound_index hcontrol_bound_index
  exact tendsto_scaled_zero_of_eventually_abs_le_bound
    scale
    (fun index =>
      weightedSampleMeanContrast (targetSample index) (targetWeight index)
        (targetOutcomeT index) (targetOutcomeC index) -
      twoArmWeightedMeanContrast (treatedSample index) (controlSample index)
        (treatedWeight index) (controlWeight index)
        (treatedOutcome index) (controlOutcome index))
    (fun index =>
      treatedEnvelope index *
        l1ScoreCellShareDistance (cells index) (targetSample index)
          (treatedSample index) (targetWeight index) (treatedWeight index)
          (targetScore index) (treatedScore index) +
      controlEnvelope index *
        l1ScoreCellShareDistance (cells index) (targetSample index)
          (controlSample index) (targetWeight index) (controlWeight index)
          (targetScore index) (controlScore index))
    hscale_nonneg hbound hscaled_rate

theorem tendsto_pattWeightedMeanContrast_difference_zero_of_eventually_l1_scoreCellShare
    (targetSample : Index -> Finset TargetUnit)
    (controlSample : Index -> Finset ControlUnit)
    (cells : Index -> Finset Cell)
    (targetWeight : Index -> TargetUnit -> Real)
    (controlWeight : Index -> ControlUnit -> Real)
    (treatedTargetOutcome targetControlOutcome : Index -> TargetUnit -> Real)
    (controlOutcome : Index -> ControlUnit -> Real)
    (targetScore : Index -> TargetUnit -> Cell)
    (controlScore : Index -> ControlUnit -> Cell)
    (controlCellValue : Index -> Cell -> Real)
    (controlEnvelope : Index -> Real)
    (hcoverTarget :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          targetScore index unit ∈ cells index)
    (hcoverControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          controlScore index unit ∈ cells index)
    (hmassTarget :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          scoreCellMass (targetSample index) (targetWeight index)
            (targetScore index) cell ≠ 0)
    (hmassControl :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          scoreCellMass (controlSample index) (controlWeight index)
            (controlScore index) cell ≠ 0)
    (hscoreMeasTargetC :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          targetControlOutcome index unit =
            controlCellValue index (targetScore index unit))
    (hscoreMeasControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          controlOutcome index unit =
            controlCellValue index (controlScore index unit))
    (hcontrol_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          |controlCellValue index cell| ≤ controlEnvelope index)
    (hrate :
      Tendsto
        (fun index =>
          controlEnvelope index *
            l1ScoreCellShareDistance (cells index) (targetSample index)
              (controlSample index) (targetWeight index)
              (controlWeight index) (targetScore index)
              (controlScore index))
        l (nhds 0)) :
    Tendsto
      (fun index =>
        weightedSampleMeanContrast (targetSample index) (targetWeight index)
          (treatedTargetOutcome index) (targetControlOutcome index) -
        pattWeightedMeanContrast (targetSample index) (controlSample index)
          (targetWeight index) (controlWeight index)
          (treatedTargetOutcome index) (controlOutcome index))
      l (nhds 0) := by
  have hbound :
      ∀ᶠ index in l,
        |weightedSampleMeanContrast (targetSample index) (targetWeight index)
            (treatedTargetOutcome index) (targetControlOutcome index) -
          pattWeightedMeanContrast (targetSample index) (controlSample index)
            (targetWeight index) (controlWeight index)
            (treatedTargetOutcome index) (controlOutcome index)| ≤
          controlEnvelope index *
            l1ScoreCellShareDistance (cells index) (targetSample index)
              (controlSample index) (targetWeight index)
              (controlWeight index) (targetScore index)
              (controlScore index) := by
    filter_upwards [hcoverTarget, hcoverControl, hmassTarget, hmassControl,
      hscoreMeasTargetC, hscoreMeasControl, hcontrol_bound] with index
      hcoverTarget_index hcoverControl_index hmassTarget_index
      hmassControl_index hscoreMeasTargetC_index hscoreMeasControl_index
      hcontrol_bound_index
    unfold l1ScoreCellShareDistance
    exact
      abs_weightedSampleMeanContrast_sub_pattWeightedMeanContrast_le_l1_scoreCellShare
        (targetSample index) (controlSample index) (cells index)
        (targetWeight index) (controlWeight index)
        (treatedTargetOutcome index) (targetControlOutcome index)
        (controlOutcome index) (targetScore index) (controlScore index)
        (controlCellValue index) (controlEnvelope index)
        hcoverTarget_index hcoverControl_index hmassTarget_index
        hmassControl_index hscoreMeasTargetC_index hscoreMeasControl_index
        hcontrol_bound_index
  exact tendsto_zero_of_eventually_abs_le_bound
    (fun index =>
      weightedSampleMeanContrast (targetSample index) (targetWeight index)
        (treatedTargetOutcome index) (targetControlOutcome index) -
      pattWeightedMeanContrast (targetSample index) (controlSample index)
        (targetWeight index) (controlWeight index)
        (treatedTargetOutcome index) (controlOutcome index))
    (fun index =>
      controlEnvelope index *
        l1ScoreCellShareDistance (cells index) (targetSample index)
          (controlSample index) (targetWeight index) (controlWeight index)
          (targetScore index) (controlScore index))
    hbound hrate

theorem tendsto_scaled_pattWeightedMeanContrast_difference_zero_of_eventually_l1_scoreCellShare
    (scale : Index -> Real)
    (targetSample : Index -> Finset TargetUnit)
    (controlSample : Index -> Finset ControlUnit)
    (cells : Index -> Finset Cell)
    (targetWeight : Index -> TargetUnit -> Real)
    (controlWeight : Index -> ControlUnit -> Real)
    (treatedTargetOutcome targetControlOutcome : Index -> TargetUnit -> Real)
    (controlOutcome : Index -> ControlUnit -> Real)
    (targetScore : Index -> TargetUnit -> Cell)
    (controlScore : Index -> ControlUnit -> Cell)
    (controlCellValue : Index -> Cell -> Real)
    (controlEnvelope : Index -> Real)
    (hscale_nonneg : ∀ᶠ index in l, 0 ≤ scale index)
    (hcoverTarget :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          targetScore index unit ∈ cells index)
    (hcoverControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          controlScore index unit ∈ cells index)
    (hmassTarget :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          scoreCellMass (targetSample index) (targetWeight index)
            (targetScore index) cell ≠ 0)
    (hmassControl :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          scoreCellMass (controlSample index) (controlWeight index)
            (controlScore index) cell ≠ 0)
    (hscoreMeasTargetC :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          targetControlOutcome index unit =
            controlCellValue index (targetScore index unit))
    (hscoreMeasControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          controlOutcome index unit =
            controlCellValue index (controlScore index unit))
    (hcontrol_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          |controlCellValue index cell| ≤ controlEnvelope index)
    (hscaled_rate :
      Tendsto
        (fun index =>
          scale index *
            (controlEnvelope index *
              l1ScoreCellShareDistance (cells index) (targetSample index)
                (controlSample index) (targetWeight index)
                (controlWeight index) (targetScore index)
                (controlScore index)))
        l (nhds 0)) :
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
  have hbound :
      ∀ᶠ index in l,
        |weightedSampleMeanContrast (targetSample index) (targetWeight index)
            (treatedTargetOutcome index) (targetControlOutcome index) -
          pattWeightedMeanContrast (targetSample index) (controlSample index)
            (targetWeight index) (controlWeight index)
            (treatedTargetOutcome index) (controlOutcome index)| ≤
          controlEnvelope index *
            l1ScoreCellShareDistance (cells index) (targetSample index)
              (controlSample index) (targetWeight index)
              (controlWeight index) (targetScore index)
              (controlScore index) := by
    filter_upwards [hcoverTarget, hcoverControl, hmassTarget, hmassControl,
      hscoreMeasTargetC, hscoreMeasControl, hcontrol_bound] with index
      hcoverTarget_index hcoverControl_index hmassTarget_index
      hmassControl_index hscoreMeasTargetC_index hscoreMeasControl_index
      hcontrol_bound_index
    unfold l1ScoreCellShareDistance
    exact
      abs_weightedSampleMeanContrast_sub_pattWeightedMeanContrast_le_l1_scoreCellShare
        (targetSample index) (controlSample index) (cells index)
        (targetWeight index) (controlWeight index)
        (treatedTargetOutcome index) (targetControlOutcome index)
        (controlOutcome index) (targetScore index) (controlScore index)
        (controlCellValue index) (controlEnvelope index)
        hcoverTarget_index hcoverControl_index hmassTarget_index
        hmassControl_index hscoreMeasTargetC_index hscoreMeasControl_index
        hcontrol_bound_index
  exact tendsto_scaled_zero_of_eventually_abs_le_bound
    scale
    (fun index =>
      weightedSampleMeanContrast (targetSample index) (targetWeight index)
        (treatedTargetOutcome index) (targetControlOutcome index) -
      pattWeightedMeanContrast (targetSample index) (controlSample index)
        (targetWeight index) (controlWeight index)
        (treatedTargetOutcome index) (controlOutcome index))
    (fun index =>
      controlEnvelope index *
        l1ScoreCellShareDistance (cells index) (targetSample index)
          (controlSample index) (targetWeight index) (controlWeight index)
          (targetScore index) (controlScore index))
    hscale_nonneg hbound hscaled_rate

end WDSM
end Matching
end StatInference
