import StatInference.Matching.WDSM.DiscreteProspectiveSurveyMeanRecovery
import StatInference.Matching.WDSM.SurveyRatio

/-!
# Finite inverse-selection identity constructors

The finite survey-weight recovery modules prove equality of target and
selected Hájek means.  The population-ratio layer consumes
`InverseSelectionIdentity`.  This module connects those layers by constructing
an inverse-selection identity from a finite weighted-mean recovery statement,
then specializes that constructor to retrospective and prospective
score-measurable survey recovery.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Unit Cell : Type*} [DecidableEq Cell]

/--
A finite weighted-sample mean equality induces the abstract
`InverseSelectionIdentity` used by the Hájek ratio layer.  The abstract
sampling mass is represented as the reciprocal of the selected weighted total.
-/
noncomputable def inverseSelectionIdentityOfWeightedSampleMeanEq
    (sample : Finset Unit) (weight outcome : Unit -> Real)
    (populationTarget : Real)
    (hmean : weightedSampleMean sample weight outcome = populationTarget)
    (htotal : weightedSampleTotal sample weight ≠ 0) :
    InverseSelectionIdentity where
  selected_weighted_target := weightedSampleSum sample weight outcome
  selected_weighted_one := weightedSampleTotal sample weight
  population_target := populationTarget
  sampling_mass := (weightedSampleTotal sample weight)⁻¹
  target_identity := by
    rw [← hmean]
    unfold weightedSampleMean
    field_simp [htotal]
  one_identity := by
    field_simp [htotal]

/--
The selected weighted numerator divided by the selected weighted total
recovers the supplied population target whenever the finite weighted mean
recovers that target.
-/
theorem selectedRatio_eq_populationTarget_of_weightedSampleMeanEq
    (sample : Finset Unit) (weight outcome : Unit -> Real)
    (populationTarget : Real)
    (hmean : weightedSampleMean sample weight outcome = populationTarget)
    (htotal : weightedSampleTotal sample weight ≠ 0) :
    weightedSampleSum sample weight outcome /
        weightedSampleTotal sample weight =
      populationTarget := by
  have hsampling :
      (inverseSelectionIdentityOfWeightedSampleMeanEq sample weight outcome
        populationTarget hmean htotal).sampling_mass ≠ 0 := by
    simp [inverseSelectionIdentityOfWeightedSampleMeanEq, htotal]
  exact
    InverseSelectionIdentity.hajekRatio_eq_populationTarget
      (inverseSelectionIdentityOfWeightedSampleMeanEq sample weight outcome
        populationTarget hmean htotal)
      hsampling

/--
Retrospective finite survey recovery, packaged as an
`InverseSelectionIdentity`.  This is the finite selected-sample version of the
retrospective inverse-selection identity for a score-measurable outcome.
-/
noncomputable def inverseSelectionIdentityOfRetrospectiveScoreMeasurableMean
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
        selectedOutcome unit = cellValue (score unit))
    (hselectedTotal :
      weightedSampleTotal selectedSample
        (retrospectiveInverseSamplingWeight baseWeight score treatment
          samplingIfTreated samplingIfControl) ≠ 0) :
    InverseSelectionIdentity :=
  inverseSelectionIdentityOfWeightedSampleMeanEq selectedSample
    (retrospectiveInverseSamplingWeight baseWeight score treatment
      samplingIfTreated samplingIfControl)
    selectedOutcome
    (weightedSampleMean targetSample baseWeight targetOutcome)
    (by
      exact
        (weightedSampleMean_eq_retrospectiveInverseSamplingWeight_of_scoreMeasurable
          targetSample selectedSample cells baseWeight targetOutcome
          selectedOutcome score treatment samplingIfTreated samplingIfControl
          cellValue hcoverTarget hcoverSelected hmassTarget hsamplingTreated
          hsamplingControl htreatedMass hcontrolMass hscoreMeasTarget
          hscoreMeasSelected).symm)
    hselectedTotal

/--
Prospective finite survey recovery, packaged as an
`InverseSelectionIdentity`.  This is the common-sampling specialization of the
finite selected-sample identity for a score-measurable outcome.
-/
noncomputable def inverseSelectionIdentityOfProspectiveScoreMeasurableMean
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
        selectedOutcome unit = cellValue (score unit))
    (hselectedTotal :
      weightedSampleTotal selectedSample
        (prospectiveInverseSamplingWeight baseWeight score samplingMass) ≠ 0) :
    InverseSelectionIdentity :=
  inverseSelectionIdentityOfWeightedSampleMeanEq selectedSample
    (prospectiveInverseSamplingWeight baseWeight score samplingMass)
    selectedOutcome
    (weightedSampleMean targetSample baseWeight targetOutcome)
    (by
      exact
        (weightedSampleMean_eq_prospectiveInverseSamplingWeight_of_scoreMeasurable
          targetSample selectedSample cells baseWeight targetOutcome
          selectedOutcome score treatment samplingMass cellValue hcoverTarget
          hcoverSelected hmassTarget hsampling htreatedMass hcontrolMass
          hscoreMeasTarget hscoreMeasSelected).symm)
    hselectedTotal

end WDSM
end Matching
end StatInference
