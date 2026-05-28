import StatInference.Matching.WDSM.DiscreteRetrospectiveSurveyWeighting

/-!
# Finite retrospective survey-weighted mean recovery for WDSM

This module lifts the direct retrospective survey-weighting algebra from cell
masses to score-cell shares and weighted means.  It proves that inverse
treatment-specific sampling weights applied inside selected data recover the
target weighted mean for any outcome that is a function of the score cell.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Unit Cell : Type*} [DecidableEq Cell]

theorem weightedSampleTotal_retrospectiveInverseSamplingWeight_eq
    (targetSample selectedSample : Finset Unit) (cells : Finset Cell)
    (baseWeight : Unit -> Real) (score : Unit -> Cell)
    (treatment : Unit -> Prop) [DecidablePred treatment]
    (samplingIfTreated samplingIfControl : Cell -> Real)
    (hcoverTarget : ∀ unit, unit ∈ targetSample -> score unit ∈ cells)
    (hcoverSelected : ∀ unit, unit ∈ selectedSample -> score unit ∈ cells)
    (hsamplingTreated :
      ∀ cell, cell ∈ cells -> samplingIfTreated cell ≠ 0)
    (hsamplingControl :
      ∀ cell, cell ∈ cells -> samplingIfControl cell ≠ 0)
    (htreatedMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (selectedSample.filter treatment) baseWeight score cell =
          samplingIfTreated cell *
            scoreCellMass (targetSample.filter treatment) baseWeight score
              cell)
    (hcontrolMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (selectedSample.filter (fun unit => ¬ treatment unit))
            baseWeight score cell =
          samplingIfControl cell *
            scoreCellMass
              (targetSample.filter (fun unit => ¬ treatment unit))
              baseWeight score cell) :
    weightedSampleTotal selectedSample
        (retrospectiveInverseSamplingWeight baseWeight score treatment
          samplingIfTreated samplingIfControl) =
      weightedSampleTotal targetSample baseWeight := by
  calc
    weightedSampleTotal selectedSample
        (retrospectiveInverseSamplingWeight baseWeight score treatment
          samplingIfTreated samplingIfControl) =
        ∑ cell ∈ cells,
          scoreCellMass selectedSample
            (retrospectiveInverseSamplingWeight baseWeight score treatment
              samplingIfTreated samplingIfControl)
            score cell := by
          exact (sum_scoreCellMass_eq_weightedSampleTotal_of_mapsTo
            selectedSample cells
            (retrospectiveInverseSamplingWeight baseWeight score treatment
              samplingIfTreated samplingIfControl)
            score hcoverSelected).symm
    _ = ∑ cell ∈ cells, scoreCellMass targetSample baseWeight score cell := by
        exact Finset.sum_congr rfl
          (fun cell hcell =>
            scoreCellMass_retrospectiveInverseSamplingWeight_eq targetSample
              selectedSample baseWeight score treatment samplingIfTreated
              samplingIfControl cell (hsamplingTreated cell hcell)
              (hsamplingControl cell hcell) (htreatedMass cell hcell)
              (hcontrolMass cell hcell))
    _ = weightedSampleTotal targetSample baseWeight := by
        exact sum_scoreCellMass_eq_weightedSampleTotal_of_mapsTo
          targetSample cells baseWeight score hcoverTarget

theorem scoreCellShare_retrospectiveInverseSamplingWeight_eq
    (targetSample selectedSample : Finset Unit) (cells : Finset Cell)
    (baseWeight : Unit -> Real) (score : Unit -> Cell)
    (treatment : Unit -> Prop) [DecidablePred treatment]
    (samplingIfTreated samplingIfControl : Cell -> Real) (cell : Cell)
    (hcell : cell ∈ cells)
    (hcoverTarget : ∀ unit, unit ∈ targetSample -> score unit ∈ cells)
    (hcoverSelected : ∀ unit, unit ∈ selectedSample -> score unit ∈ cells)
    (hsamplingTreated :
      ∀ cell, cell ∈ cells -> samplingIfTreated cell ≠ 0)
    (hsamplingControl :
      ∀ cell, cell ∈ cells -> samplingIfControl cell ≠ 0)
    (htreatedMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (selectedSample.filter treatment) baseWeight score cell =
          samplingIfTreated cell *
            scoreCellMass (targetSample.filter treatment) baseWeight score
              cell)
    (hcontrolMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (selectedSample.filter (fun unit => ¬ treatment unit))
            baseWeight score cell =
          samplingIfControl cell *
            scoreCellMass
              (targetSample.filter (fun unit => ¬ treatment unit))
              baseWeight score cell) :
    scoreCellShare selectedSample
        (retrospectiveInverseSamplingWeight baseWeight score treatment
          samplingIfTreated samplingIfControl)
        score cell =
      scoreCellShare targetSample baseWeight score cell := by
  unfold scoreCellShare
  rw [scoreCellMass_retrospectiveInverseSamplingWeight_eq targetSample
    selectedSample baseWeight score treatment samplingIfTreated
    samplingIfControl cell (hsamplingTreated cell hcell)
    (hsamplingControl cell hcell) (htreatedMass cell hcell)
    (hcontrolMass cell hcell)]
  rw [weightedSampleTotal_retrospectiveInverseSamplingWeight_eq targetSample
    selectedSample cells baseWeight score treatment samplingIfTreated
    samplingIfControl hcoverTarget hcoverSelected hsamplingTreated
    hsamplingControl htreatedMass hcontrolMass]

theorem weightedSampleMean_eq_retrospectiveInverseSamplingWeight_of_scoreMeasurable
    (targetSample selectedSample : Finset Unit) (cells : Finset Cell)
    (baseWeight : Unit -> Real) (targetOutcome selectedOutcome : Unit -> Real)
    (score : Unit -> Cell) (treatment : Unit -> Prop)
    [DecidablePred treatment]
    (samplingIfTreated samplingIfControl : Cell -> Real)
    (cellValue : Cell -> Real)
    (hcoverTarget : ∀ unit, unit ∈ targetSample -> score unit ∈ cells)
    (hcoverSelected : ∀ unit, unit ∈ selectedSample -> score unit ∈ cells)
    (hmassTarget :
      ∀ cell, cell ∈ cells ->
        scoreCellMass targetSample baseWeight score cell ≠ 0)
    (hsamplingTreated :
      ∀ cell, cell ∈ cells -> samplingIfTreated cell ≠ 0)
    (hsamplingControl :
      ∀ cell, cell ∈ cells -> samplingIfControl cell ≠ 0)
    (htreatedMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (selectedSample.filter treatment) baseWeight score cell =
          samplingIfTreated cell *
            scoreCellMass (targetSample.filter treatment) baseWeight score
              cell)
    (hcontrolMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (selectedSample.filter (fun unit => ¬ treatment unit))
            baseWeight score cell =
          samplingIfControl cell *
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
        (retrospectiveInverseSamplingWeight baseWeight score treatment
          samplingIfTreated samplingIfControl)
        selectedOutcome := by
  let retrospectiveWeight :=
    retrospectiveInverseSamplingWeight baseWeight score treatment
      samplingIfTreated samplingIfControl
  have hmassSelected :
      ∀ cell, cell ∈ cells ->
        scoreCellMass selectedSample retrospectiveWeight score cell ≠ 0 := by
    intro cell hcell
    rw [scoreCellMass_retrospectiveInverseSamplingWeight_eq targetSample
      selectedSample baseWeight score treatment samplingIfTreated
      samplingIfControl cell (hsamplingTreated cell hcell)
      (hsamplingControl cell hcell) (htreatedMass cell hcell)
      (hcontrolMass cell hcell)]
    exact hmassTarget cell hcell
  have hshare :
      ∀ cell, cell ∈ cells ->
        scoreCellShare targetSample baseWeight score cell =
          scoreCellShare selectedSample retrospectiveWeight score cell := by
    intro cell hcell
    exact (scoreCellShare_retrospectiveInverseSamplingWeight_eq targetSample
      selectedSample cells baseWeight score treatment samplingIfTreated
      samplingIfControl cell hcell hcoverTarget hcoverSelected
      hsamplingTreated hsamplingControl htreatedMass hcontrolMass).symm
  exact weightedSampleMean_eq_of_scoreCellShare_eq_and_scoreMeasurable
    targetSample selectedSample cells baseWeight retrospectiveWeight
    targetOutcome selectedOutcome score score cellValue hcoverTarget
    hcoverSelected hmassTarget hmassSelected hshare hscoreMeasTarget
    hscoreMeasSelected

theorem weightedSampleMeanContrast_eq_retrospectiveInverseSamplingWeight_of_scoreMeasurable
    (targetSample selectedSample : Finset Unit) (cells : Finset Cell)
    (baseWeight : Unit -> Real)
    (targetOutcomeA targetOutcomeB selectedOutcomeA selectedOutcomeB :
      Unit -> Real)
    (score : Unit -> Cell) (treatment : Unit -> Prop)
    [DecidablePred treatment]
    (samplingIfTreated samplingIfControl : Cell -> Real)
    (cellValueA cellValueB : Cell -> Real)
    (hcoverTarget : ∀ unit, unit ∈ targetSample -> score unit ∈ cells)
    (hcoverSelected : ∀ unit, unit ∈ selectedSample -> score unit ∈ cells)
    (hmassTarget :
      ∀ cell, cell ∈ cells ->
        scoreCellMass targetSample baseWeight score cell ≠ 0)
    (hsamplingTreated :
      ∀ cell, cell ∈ cells -> samplingIfTreated cell ≠ 0)
    (hsamplingControl :
      ∀ cell, cell ∈ cells -> samplingIfControl cell ≠ 0)
    (htreatedMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (selectedSample.filter treatment) baseWeight score cell =
          samplingIfTreated cell *
            scoreCellMass (targetSample.filter treatment) baseWeight score
              cell)
    (hcontrolMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (selectedSample.filter (fun unit => ¬ treatment unit))
            baseWeight score cell =
          samplingIfControl cell *
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
        (retrospectiveInverseSamplingWeight baseWeight score treatment
          samplingIfTreated samplingIfControl)
        selectedOutcomeA selectedOutcomeB := by
  unfold weightedSampleMeanContrast
  rw [weightedSampleMean_eq_retrospectiveInverseSamplingWeight_of_scoreMeasurable
    targetSample selectedSample cells baseWeight targetOutcomeA
    selectedOutcomeA score treatment samplingIfTreated samplingIfControl
    cellValueA hcoverTarget hcoverSelected hmassTarget hsamplingTreated
    hsamplingControl htreatedMass hcontrolMass hscoreMeasTargetA
    hscoreMeasSelectedA]
  rw [weightedSampleMean_eq_retrospectiveInverseSamplingWeight_of_scoreMeasurable
    targetSample selectedSample cells baseWeight targetOutcomeB
    selectedOutcomeB score treatment samplingIfTreated samplingIfControl
    cellValueB hcoverTarget hcoverSelected hmassTarget hsamplingTreated
    hsamplingControl htreatedMass hcontrolMass hscoreMeasTargetB
    hscoreMeasSelectedB]

end WDSM
end Matching
end StatInference
