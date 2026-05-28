import Mathlib.MeasureTheory.Integral.Bochner.Basic
import StatInference.Matching.WDSM.FiniteInverseSelectionIdentity
import StatInference.Matching.WDSM.PopulationSelectionDensityDesign

/-!
# Finite inverse-selection to population selection bridge

The finite inverse-selection identities prove exact selected-sample ratio
equalities.  The population selection-density design proves exact selected-law
Hájek ratio equalities.  This module connects the two layers without asserting
an unproved finite-sample-to-population step: that step is packaged as the
explicit assumption `FinitePopulationIntegralBridge`.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open scoped MeasureTheory ENNReal

variable {Unit Cell Sample : Type*} [DecidableEq Cell]
variable [MeasurableSpace Sample]

/--
Named finite-to-population bridge assumption.

This is the exact place where a later law of large numbers, sampling design
argument, or manuscript-specific identification step must be plugged in.  The
current deterministic bridge only consumes this equality; it does not prove it.
-/
structure FinitePopulationIntegralBridge
    (finiteTarget : Real) (populationLaw : Measure Sample)
    (populationOutcome : Sample -> Real) : Prop where
  finite_eq_populationIntegral :
    finiteTarget = ∫ sample, populationOutcome sample ∂populationLaw

/--
Retrospective finite inverse-selection ratio equals the population integral
whenever the target finite weighted mean is bridged to that population
integral.
-/
theorem retrospectiveFiniteInverseSelectionRatio_eq_populationIntegral_of_bridge
    (targetSample selectedSample : Finset Unit) (cells : Finset Cell)
    (baseWeight : Unit -> Real) (targetOutcome selectedOutcome : Unit -> Real)
    (score : Unit -> Cell) (treatment : Unit -> Prop)
    [DecidablePred treatment]
    (samplingIfTreated samplingIfControl : Cell -> Real)
    (cellValue : Cell -> Real)
    (populationLaw : Measure Sample) (populationOutcome : Sample -> Real)
    (bridge :
      FinitePopulationIntegralBridge
        (weightedSampleMean targetSample baseWeight targetOutcome)
        populationLaw populationOutcome)
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
    weightedSampleSum selectedSample
        (retrospectiveInverseSamplingWeight baseWeight score treatment
          samplingIfTreated samplingIfControl)
        selectedOutcome /
        weightedSampleTotal selectedSample
          (retrospectiveInverseSamplingWeight baseWeight score treatment
            samplingIfTreated samplingIfControl) =
      ∫ sample, populationOutcome sample ∂populationLaw := by
  calc
    weightedSampleSum selectedSample
        (retrospectiveInverseSamplingWeight baseWeight score treatment
          samplingIfTreated samplingIfControl)
        selectedOutcome /
        weightedSampleTotal selectedSample
          (retrospectiveInverseSamplingWeight baseWeight score treatment
            samplingIfTreated samplingIfControl) =
        weightedSampleMean targetSample baseWeight targetOutcome :=
      selectedRatio_eq_populationTarget_of_weightedSampleMeanEq
        selectedSample
        (retrospectiveInverseSamplingWeight baseWeight score treatment
          samplingIfTreated samplingIfControl)
        selectedOutcome
        (weightedSampleMean targetSample baseWeight targetOutcome)
        (by
          exact
            (weightedSampleMean_eq_retrospectiveInverseSamplingWeight_of_scoreMeasurable
              targetSample selectedSample cells baseWeight targetOutcome
              selectedOutcome score treatment samplingIfTreated
              samplingIfControl cellValue hcoverTarget hcoverSelected
              hmassTarget hsamplingTreated hsamplingControl htreatedMass
              hcontrolMass hscoreMeasTarget hscoreMeasSelected).symm)
        hselectedTotal
    _ = ∫ sample, populationOutcome sample ∂populationLaw :=
      bridge.finite_eq_populationIntegral

/--
Prospective/common-sampling finite inverse-selection ratio equals the
population integral whenever the target finite weighted mean is bridged to that
population integral.
-/
theorem prospectiveFiniteInverseSelectionRatio_eq_populationIntegral_of_bridge
    (targetSample selectedSample : Finset Unit) (cells : Finset Cell)
    (baseWeight : Unit -> Real) (targetOutcome selectedOutcome : Unit -> Real)
    (score : Unit -> Cell) (treatment : Unit -> Prop)
    [DecidablePred treatment]
    (samplingMass : Cell -> Real) (cellValue : Cell -> Real)
    (populationLaw : Measure Sample) (populationOutcome : Sample -> Real)
    (bridge :
      FinitePopulationIntegralBridge
        (weightedSampleMean targetSample baseWeight targetOutcome)
        populationLaw populationOutcome)
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
    weightedSampleSum selectedSample
        (prospectiveInverseSamplingWeight baseWeight score samplingMass)
        selectedOutcome /
        weightedSampleTotal selectedSample
          (prospectiveInverseSamplingWeight baseWeight score samplingMass) =
      ∫ sample, populationOutcome sample ∂populationLaw := by
  calc
    weightedSampleSum selectedSample
        (prospectiveInverseSamplingWeight baseWeight score samplingMass)
        selectedOutcome /
        weightedSampleTotal selectedSample
          (prospectiveInverseSamplingWeight baseWeight score samplingMass) =
        weightedSampleMean targetSample baseWeight targetOutcome :=
      selectedRatio_eq_populationTarget_of_weightedSampleMeanEq
        selectedSample
        (prospectiveInverseSamplingWeight baseWeight score samplingMass)
        selectedOutcome
        (weightedSampleMean targetSample baseWeight targetOutcome)
        (by
          exact
            (weightedSampleMean_eq_prospectiveInverseSamplingWeight_of_scoreMeasurable
              targetSample selectedSample cells baseWeight targetOutcome
              selectedOutcome score treatment samplingMass cellValue
              hcoverTarget hcoverSelected hmassTarget hsampling htreatedMass
              hcontrolMass hscoreMeasTarget hscoreMeasSelected).symm)
        hselectedTotal
    _ = ∫ sample, populationOutcome sample ∂populationLaw :=
      bridge.finite_eq_populationIntegral

/--
Retrospective finite inverse-selection ratio equals the population-design
selected-law Hájek ratio under the same named finite-to-population bridge.
-/
theorem retrospectiveFiniteInverseSelectionRatio_eq_designHajek_of_bridge
    (targetSample selectedSample : Finset Unit) (cells : Finset Cell)
    (baseWeight : Unit -> Real) (targetOutcome selectedOutcome : Unit -> Real)
    (score : Unit -> Cell) (treatment : Unit -> Prop)
    [DecidablePred treatment]
    (samplingIfTreated samplingIfControl : Cell -> Real)
    (cellValue : Cell -> Real)
    (selectedLaw populationLaw : Measure Sample)
    (design : PopulationSelectionDensityDesign selectedLaw populationLaw)
    (populationOutcome : Sample -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1)
    (bridge :
      FinitePopulationIntegralBridge
        (weightedSampleMean targetSample baseWeight targetOutcome)
        populationLaw populationOutcome)
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
    weightedSampleSum selectedSample
        (retrospectiveInverseSamplingWeight baseWeight score treatment
          samplingIfTreated samplingIfControl)
        selectedOutcome /
        weightedSampleTotal selectedSample
          (retrospectiveInverseSamplingWeight baseWeight score treatment
            samplingIfTreated samplingIfControl) =
      (∫ sample, (design.surveyWeight sample : Real) *
          populationOutcome sample ∂selectedLaw) /
        (∫ sample, (design.surveyWeight sample : Real) ∂selectedLaw) := by
  calc
    weightedSampleSum selectedSample
        (retrospectiveInverseSamplingWeight baseWeight score treatment
          samplingIfTreated samplingIfControl)
        selectedOutcome /
        weightedSampleTotal selectedSample
          (retrospectiveInverseSamplingWeight baseWeight score treatment
            samplingIfTreated samplingIfControl) =
        ∫ sample, populationOutcome sample ∂populationLaw :=
      retrospectiveFiniteInverseSelectionRatio_eq_populationIntegral_of_bridge
        targetSample selectedSample cells baseWeight targetOutcome
        selectedOutcome score treatment samplingIfTreated samplingIfControl
        cellValue populationLaw populationOutcome bridge hcoverTarget
        hcoverSelected hmassTarget hsamplingTreated hsamplingControl
        htreatedMass hcontrolMass hscoreMeasTarget hscoreMeasSelected
        hselectedTotal
    _ =
        (∫ sample, (design.surveyWeight sample : Real) *
            populationOutcome sample ∂selectedLaw) /
          (∫ sample, (design.surveyWeight sample : Real) ∂selectedLaw) :=
      (PopulationSelectionDensityDesign.hajekRatio_eq_populationIntegral
        design populationOutcome hpopulationOne).symm

/--
Prospective/common-sampling finite inverse-selection ratio equals the
population-design selected-law Hájek ratio under the same named
finite-to-population bridge.
-/
theorem prospectiveFiniteInverseSelectionRatio_eq_designHajek_of_bridge
    (targetSample selectedSample : Finset Unit) (cells : Finset Cell)
    (baseWeight : Unit -> Real) (targetOutcome selectedOutcome : Unit -> Real)
    (score : Unit -> Cell) (treatment : Unit -> Prop)
    [DecidablePred treatment]
    (samplingMass : Cell -> Real) (cellValue : Cell -> Real)
    (selectedLaw populationLaw : Measure Sample)
    (design : PopulationSelectionDensityDesign selectedLaw populationLaw)
    (populationOutcome : Sample -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1)
    (bridge :
      FinitePopulationIntegralBridge
        (weightedSampleMean targetSample baseWeight targetOutcome)
        populationLaw populationOutcome)
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
    weightedSampleSum selectedSample
        (prospectiveInverseSamplingWeight baseWeight score samplingMass)
        selectedOutcome /
        weightedSampleTotal selectedSample
          (prospectiveInverseSamplingWeight baseWeight score samplingMass) =
      (∫ sample, (design.surveyWeight sample : Real) *
          populationOutcome sample ∂selectedLaw) /
        (∫ sample, (design.surveyWeight sample : Real) ∂selectedLaw) := by
  calc
    weightedSampleSum selectedSample
        (prospectiveInverseSamplingWeight baseWeight score samplingMass)
        selectedOutcome /
        weightedSampleTotal selectedSample
          (prospectiveInverseSamplingWeight baseWeight score samplingMass) =
        ∫ sample, populationOutcome sample ∂populationLaw :=
      prospectiveFiniteInverseSelectionRatio_eq_populationIntegral_of_bridge
        targetSample selectedSample cells baseWeight targetOutcome
        selectedOutcome score treatment samplingMass cellValue populationLaw
        populationOutcome bridge hcoverTarget hcoverSelected hmassTarget
        hsampling htreatedMass hcontrolMass hscoreMeasTarget
        hscoreMeasSelected hselectedTotal
    _ =
        (∫ sample, (design.surveyWeight sample : Real) *
            populationOutcome sample ∂selectedLaw) /
          (∫ sample, (design.surveyWeight sample : Real) ∂selectedLaw) :=
      (PopulationSelectionDensityDesign.hajekRatio_eq_populationIntegral
        design populationOutcome hpopulationOne).symm

end WDSM
end Matching
end StatInference
