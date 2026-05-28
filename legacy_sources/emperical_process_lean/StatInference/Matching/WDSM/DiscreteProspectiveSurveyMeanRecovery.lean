import StatInference.Matching.WDSM.DiscreteRetrospectiveSurveyMeanRecovery

/-!
# Finite prospective/common-sampling survey-weighted mean recovery

Prospective sampling is the common-sampling specialization of the retrospective
finite algebra: treated and control selected-cell masses share the same
cell-level sampling multiplier.  This module proves that a single inverse
common sampling weight recovers target total weight, score-cell shares,
score-measurable means, and score-measurable contrasts.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Unit Cell : Type*} [DecidableEq Cell]

/-- Common inverse sampling weight inside a selected finite sample. -/
noncomputable def prospectiveInverseSamplingWeight
    (baseWeight : Unit -> Real) (score : Unit -> Cell)
    (samplingMass : Cell -> Real) (unit : Unit) : Real :=
  baseWeight unit / samplingMass (score unit)

omit [DecidableEq Cell] in
theorem retrospectiveInverseSamplingWeight_common_sampling_eq
    (baseWeight : Unit -> Real) (score : Unit -> Cell)
    (treatment : Unit -> Prop) [DecidablePred treatment]
    (samplingMass : Cell -> Real) :
    retrospectiveInverseSamplingWeight baseWeight score treatment
        samplingMass samplingMass =
      prospectiveInverseSamplingWeight baseWeight score samplingMass := by
  funext unit
  unfold retrospectiveInverseSamplingWeight prospectiveInverseSamplingWeight
  by_cases htreatment : treatment unit
  · simp [htreatment]
  · simp [htreatment]

theorem weightedSampleTotal_prospectiveInverseSamplingWeight_eq
    (targetSample selectedSample : Finset Unit) (cells : Finset Cell)
    (baseWeight : Unit -> Real) (score : Unit -> Cell)
    (treatment : Unit -> Prop) [DecidablePred treatment]
    (samplingMass : Cell -> Real)
    (hcoverTarget : ∀ unit, unit ∈ targetSample -> score unit ∈ cells)
    (hcoverSelected : ∀ unit, unit ∈ selectedSample -> score unit ∈ cells)
    (hsampling : ∀ cell, cell ∈ cells -> samplingMass cell ≠ 0)
    (htreatedMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (selectedSample.filter treatment) baseWeight score cell =
          samplingMass cell *
            scoreCellMass (targetSample.filter treatment) baseWeight score
              cell)
    (hcontrolMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (selectedSample.filter (fun unit => ¬ treatment unit))
            baseWeight score cell =
          samplingMass cell *
            scoreCellMass
              (targetSample.filter (fun unit => ¬ treatment unit))
              baseWeight score cell) :
    weightedSampleTotal selectedSample
        (prospectiveInverseSamplingWeight baseWeight score samplingMass) =
      weightedSampleTotal targetSample baseWeight := by
  have h :=
    weightedSampleTotal_retrospectiveInverseSamplingWeight_eq targetSample
      selectedSample cells baseWeight score treatment samplingMass
      samplingMass hcoverTarget hcoverSelected hsampling hsampling
      htreatedMass hcontrolMass
  rw [retrospectiveInverseSamplingWeight_common_sampling_eq] at h
  exact h

theorem scoreCellShare_prospectiveInverseSamplingWeight_eq
    (targetSample selectedSample : Finset Unit) (cells : Finset Cell)
    (baseWeight : Unit -> Real) (score : Unit -> Cell)
    (treatment : Unit -> Prop) [DecidablePred treatment]
    (samplingMass : Cell -> Real) (cell : Cell)
    (hcell : cell ∈ cells)
    (hcoverTarget : ∀ unit, unit ∈ targetSample -> score unit ∈ cells)
    (hcoverSelected : ∀ unit, unit ∈ selectedSample -> score unit ∈ cells)
    (hsampling : ∀ cell, cell ∈ cells -> samplingMass cell ≠ 0)
    (htreatedMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (selectedSample.filter treatment) baseWeight score cell =
          samplingMass cell *
            scoreCellMass (targetSample.filter treatment) baseWeight score
              cell)
    (hcontrolMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (selectedSample.filter (fun unit => ¬ treatment unit))
            baseWeight score cell =
          samplingMass cell *
            scoreCellMass
              (targetSample.filter (fun unit => ¬ treatment unit))
              baseWeight score cell) :
    scoreCellShare selectedSample
        (prospectiveInverseSamplingWeight baseWeight score samplingMass)
        score cell =
      scoreCellShare targetSample baseWeight score cell := by
  have h :=
    scoreCellShare_retrospectiveInverseSamplingWeight_eq targetSample
      selectedSample cells baseWeight score treatment samplingMass
      samplingMass cell hcell hcoverTarget hcoverSelected hsampling hsampling
      htreatedMass hcontrolMass
  rw [retrospectiveInverseSamplingWeight_common_sampling_eq] at h
  exact h

theorem weightedSampleMean_eq_prospectiveInverseSamplingWeight_of_scoreMeasurable
    (targetSample selectedSample : Finset Unit) (cells : Finset Cell)
    (baseWeight : Unit -> Real) (targetOutcome selectedOutcome : Unit -> Real)
    (score : Unit -> Cell) (treatment : Unit -> Prop)
    [DecidablePred treatment]
    (samplingMass : Cell -> Real) (cellValue : Cell -> Real)
    (hcoverTarget : ∀ unit, unit ∈ targetSample -> score unit ∈ cells)
    (hcoverSelected : ∀ unit, unit ∈ selectedSample -> score unit ∈ cells)
    (hmassTarget :
      ∀ cell, cell ∈ cells ->
        scoreCellMass targetSample baseWeight score cell ≠ 0)
    (hsampling : ∀ cell, cell ∈ cells -> samplingMass cell ≠ 0)
    (htreatedMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (selectedSample.filter treatment) baseWeight score cell =
          samplingMass cell *
            scoreCellMass (targetSample.filter treatment) baseWeight score
              cell)
    (hcontrolMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (selectedSample.filter (fun unit => ¬ treatment unit))
            baseWeight score cell =
          samplingMass cell *
            scoreCellMass
              (targetSample.filter (fun unit => ¬ treatment unit))
              baseWeight score cell)
    (hscoreMeasTarget :
      ∀ unit, unit ∈ targetSample ->
        targetOutcome unit = cellValue (score unit))
    (hscoreMeasSelected :
      ∀ unit, unit ∈ selectedSample ->
        selectedOutcome unit = cellValue (score unit)) :
    weightedSampleMean targetSample baseWeight targetOutcome =
      weightedSampleMean selectedSample
        (prospectiveInverseSamplingWeight baseWeight score samplingMass)
        selectedOutcome := by
  have h :=
    weightedSampleMean_eq_retrospectiveInverseSamplingWeight_of_scoreMeasurable
      targetSample selectedSample cells baseWeight targetOutcome
      selectedOutcome score treatment samplingMass samplingMass cellValue
      hcoverTarget hcoverSelected hmassTarget hsampling hsampling
      htreatedMass hcontrolMass hscoreMeasTarget hscoreMeasSelected
  rw [retrospectiveInverseSamplingWeight_common_sampling_eq] at h
  exact h

theorem weightedSampleMeanContrast_eq_prospectiveInverseSamplingWeight_of_scoreMeasurable
    (targetSample selectedSample : Finset Unit) (cells : Finset Cell)
    (baseWeight : Unit -> Real)
    (targetOutcomeA targetOutcomeB selectedOutcomeA selectedOutcomeB :
      Unit -> Real)
    (score : Unit -> Cell) (treatment : Unit -> Prop)
    [DecidablePred treatment]
    (samplingMass : Cell -> Real)
    (cellValueA cellValueB : Cell -> Real)
    (hcoverTarget : ∀ unit, unit ∈ targetSample -> score unit ∈ cells)
    (hcoverSelected : ∀ unit, unit ∈ selectedSample -> score unit ∈ cells)
    (hmassTarget :
      ∀ cell, cell ∈ cells ->
        scoreCellMass targetSample baseWeight score cell ≠ 0)
    (hsampling : ∀ cell, cell ∈ cells -> samplingMass cell ≠ 0)
    (htreatedMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (selectedSample.filter treatment) baseWeight score cell =
          samplingMass cell *
            scoreCellMass (targetSample.filter treatment) baseWeight score
              cell)
    (hcontrolMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (selectedSample.filter (fun unit => ¬ treatment unit))
            baseWeight score cell =
          samplingMass cell *
            scoreCellMass
              (targetSample.filter (fun unit => ¬ treatment unit))
              baseWeight score cell)
    (hscoreMeasTargetA :
      ∀ unit, unit ∈ targetSample ->
        targetOutcomeA unit = cellValueA (score unit))
    (hscoreMeasSelectedA :
      ∀ unit, unit ∈ selectedSample ->
        selectedOutcomeA unit = cellValueA (score unit))
    (hscoreMeasTargetB :
      ∀ unit, unit ∈ targetSample ->
        targetOutcomeB unit = cellValueB (score unit))
    (hscoreMeasSelectedB :
      ∀ unit, unit ∈ selectedSample ->
        selectedOutcomeB unit = cellValueB (score unit)) :
    weightedSampleMeanContrast targetSample baseWeight
        targetOutcomeA targetOutcomeB =
      weightedSampleMeanContrast selectedSample
        (prospectiveInverseSamplingWeight baseWeight score samplingMass)
        selectedOutcomeA selectedOutcomeB := by
  have h :=
    weightedSampleMeanContrast_eq_retrospectiveInverseSamplingWeight_of_scoreMeasurable
      targetSample selectedSample cells baseWeight targetOutcomeA
      targetOutcomeB selectedOutcomeA selectedOutcomeB score treatment
      samplingMass samplingMass cellValueA cellValueB hcoverTarget
      hcoverSelected hmassTarget hsampling hsampling htreatedMass
      hcontrolMass hscoreMeasTargetA hscoreMeasSelectedA hscoreMeasTargetB
      hscoreMeasSelectedB
  rw [retrospectiveInverseSamplingWeight_common_sampling_eq] at h
  exact h

end WDSM
end Matching
end StatInference
