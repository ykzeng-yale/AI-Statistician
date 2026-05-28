import StatInference.Matching.WDSM.DiscreteDoubleScoreProspectiveSurveyMean
import StatInference.Matching.WDSM.DiscreteDoubleScoreRetrospectiveSurveyMean
import StatInference.Matching.WDSM.DoubleScoreConditionalIdentificationBridge

/-!
# Double-score finite estimator and population bridge

This module packages two checked layers for the WDSM PATE scenario:

* finite double-score survey-weighted estimator recovery, and
* selected-sample Hájek population identification through double-score
  conditional mean versions.

The theorem statements keep the finite-sample obligations and the population
identification obligations separate, but return them together as one audited
scenario bridge.  Later asymptotic work can use this package before adding
finite-to-population convergence and CLT assumptions.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open scoped MeasureTheory

variable {Unit Sample PropensityCell TreatedProgCell ControlProgCell : Type*}
variable [mSample : MeasurableSpace Sample]
variable {scoreSigma : MeasurableSpace Sample}
variable {sampleLaw : Measure[mSample] Sample}
variable [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
  [DecidableEq ControlProgCell]
variable {PATTProgCell : Type*} [DecidableEq PATTProgCell]

/--
Retrospective PATE bridge: the finite selected double-score inverse-weighted
contrast recovers the finite target contrast, and the population selected
Hájek representation recovers the double-score conditional-mean target.
-/
theorem retrospectivePATEDoubleScore_finite_recovery_and_population_identification
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (targetSample selectedSample : Finset Unit)
    (cells : Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (baseWeight : Unit -> Real)
    (targetOutcomeT targetOutcomeC selectedOutcomeT selectedOutcomeC :
      Unit -> Real)
    (unitPropensityScore : Unit -> PropensityCell)
    (unitTreatedPrognosticScore : Unit -> TreatedProgCell)
    (unitControlPrognosticScore : Unit -> ControlProgCell)
    (treatment : Unit -> Prop) [DecidablePred treatment]
    (samplingIfTreated samplingIfControl :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (repr : PATERepresentation)
    (htreatedSampling : repr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : repr.control.sampling_mass ≠ 0)
    (samplePropensityScore : Sample -> PropensityCell)
    (sampleTreatedPrognosticScore : Sample -> TreatedProgCell)
    (sampleControlPrognosticScore : Sample -> ControlProgCell)
    (populationTreatedOutcome populationControlOutcome : Sample -> Real)
    (populationTreatedValue : TreatedProgCell -> Real)
    (populationControlValue : ControlProgCell -> Real)
    (hcoverTarget :
      ∀ unit, unit ∈ targetSample ->
        pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
          unitControlPrognosticScore unit ∈ cells)
    (hcoverSelected :
      ∀ unit, unit ∈ selectedSample ->
        pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
          unitControlPrognosticScore unit ∈ cells)
    (hmassTarget :
      ∀ cell, cell ∈ cells ->
        scoreCellMass targetSample baseWeight
          (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
            unitControlPrognosticScore) cell ≠ 0)
    (hsamplingTreated :
      ∀ cell, cell ∈ cells -> samplingIfTreated cell ≠ 0)
    (hsamplingControl :
      ∀ cell, cell ∈ cells -> samplingIfControl cell ≠ 0)
    (htreatedMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (selectedSample.filter treatment) baseWeight
            (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
              unitControlPrognosticScore) cell =
          samplingIfTreated cell *
            scoreCellMass (targetSample.filter treatment) baseWeight
              (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
                unitControlPrognosticScore) cell)
    (hcontrolMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (selectedSample.filter (fun unit => ¬ treatment unit))
            baseWeight
            (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
              unitControlPrognosticScore) cell =
          samplingIfControl cell *
            scoreCellMass
              (targetSample.filter (fun unit => ¬ treatment unit))
              baseWeight
              (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
                unitControlPrognosticScore) cell)
    (hscoreMeasTargetT :
      ∀ unit, unit ∈ targetSample ->
        targetOutcomeT unit = treatedValue (unitTreatedPrognosticScore unit))
    (hscoreMeasSelectedT :
      ∀ unit, unit ∈ selectedSample ->
        selectedOutcomeT unit = treatedValue (unitTreatedPrognosticScore unit))
    (hscoreMeasTargetC :
      ∀ unit, unit ∈ targetSample ->
        targetOutcomeC unit = controlValue (unitControlPrognosticScore unit))
    (hscoreMeasSelectedC :
      ∀ unit, unit ∈ selectedSample ->
        selectedOutcomeC unit = controlValue (unitControlPrognosticScore unit))
    (hreprT :
      repr.treated.population_target =
        ∫ sample, populationTreatedOutcome sample ∂sampleLaw)
    (hreprC :
      repr.control.population_target =
        ∫ sample, populationControlOutcome sample ∂sampleLaw)
    (hcondT :
      sampleLaw[populationTreatedOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => populationTreatedValue
          (sampleTreatedPrognosticScore sample))
    (hcondC :
      sampleLaw[populationControlOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => populationControlValue
          (sampleControlPrognosticScore sample)) :
    weightedSampleMeanContrast targetSample baseWeight targetOutcomeT
          targetOutcomeC =
        weightedSampleMeanContrast selectedSample
          (retrospectiveInverseSamplingWeight baseWeight
            (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
              unitControlPrognosticScore)
            treatment samplingIfTreated samplingIfControl)
          selectedOutcomeT selectedOutcomeC ∧
      repr.selectedHajekPATE =
        (∫ sample,
            populationTreatedValue (sampleTreatedPrognosticScore sample)
            ∂sampleLaw) -
          (∫ sample,
            populationControlValue (sampleControlPrognosticScore sample)
            ∂sampleLaw) :=
  ⟨weightedSampleMeanContrast_eq_retrospectivePATEDoubleScoreWeight
      targetSample selectedSample cells baseWeight targetOutcomeT
      targetOutcomeC selectedOutcomeT selectedOutcomeC unitPropensityScore
      unitTreatedPrognosticScore unitControlPrognosticScore treatment
      samplingIfTreated samplingIfControl treatedValue controlValue
      hcoverTarget hcoverSelected hmassTarget hsamplingTreated
      hsamplingControl htreatedMass hcontrolMass hscoreMeasTargetT
      hscoreMeasSelectedT hscoreMeasTargetC hscoreMeasSelectedC,
    selectedHajekPATE_eq_scorePATE_of_condExp_pateDoubleScoreVersions
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub repr htreatedSampling hcontrolSampling
      samplePropensityScore sampleTreatedPrognosticScore
      sampleControlPrognosticScore populationTreatedOutcome
      populationControlOutcome populationTreatedValue populationControlValue
      hreprT hreprC hcondT hcondC⟩

/--
Prospective PATE bridge: the finite selected double-score common inverse
sampling-weight contrast recovers the finite target contrast, and the
population selected Hájek representation recovers the double-score
conditional-mean target.
-/
theorem prospectivePATEDoubleScore_finite_recovery_and_population_identification
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (targetSample selectedSample : Finset Unit)
    (cells : Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (baseWeight : Unit -> Real)
    (targetOutcomeT targetOutcomeC selectedOutcomeT selectedOutcomeC :
      Unit -> Real)
    (unitPropensityScore : Unit -> PropensityCell)
    (unitTreatedPrognosticScore : Unit -> TreatedProgCell)
    (unitControlPrognosticScore : Unit -> ControlProgCell)
    (treatment : Unit -> Prop) [DecidablePred treatment]
    (samplingMass :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (repr : PATERepresentation)
    (htreatedSampling : repr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : repr.control.sampling_mass ≠ 0)
    (samplePropensityScore : Sample -> PropensityCell)
    (sampleTreatedPrognosticScore : Sample -> TreatedProgCell)
    (sampleControlPrognosticScore : Sample -> ControlProgCell)
    (populationTreatedOutcome populationControlOutcome : Sample -> Real)
    (populationTreatedValue : TreatedProgCell -> Real)
    (populationControlValue : ControlProgCell -> Real)
    (hcoverTarget :
      ∀ unit, unit ∈ targetSample ->
        pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
          unitControlPrognosticScore unit ∈ cells)
    (hcoverSelected :
      ∀ unit, unit ∈ selectedSample ->
        pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
          unitControlPrognosticScore unit ∈ cells)
    (hmassTarget :
      ∀ cell, cell ∈ cells ->
        scoreCellMass targetSample baseWeight
          (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
            unitControlPrognosticScore) cell ≠ 0)
    (hsampling : ∀ cell, cell ∈ cells -> samplingMass cell ≠ 0)
    (htreatedMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (selectedSample.filter treatment) baseWeight
            (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
              unitControlPrognosticScore) cell =
          samplingMass cell *
            scoreCellMass (targetSample.filter treatment) baseWeight
              (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
                unitControlPrognosticScore) cell)
    (hcontrolMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (selectedSample.filter (fun unit => ¬ treatment unit))
            baseWeight
            (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
              unitControlPrognosticScore) cell =
          samplingMass cell *
            scoreCellMass
              (targetSample.filter (fun unit => ¬ treatment unit))
              baseWeight
              (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
                unitControlPrognosticScore) cell)
    (hscoreMeasTargetT :
      ∀ unit, unit ∈ targetSample ->
        targetOutcomeT unit = treatedValue (unitTreatedPrognosticScore unit))
    (hscoreMeasSelectedT :
      ∀ unit, unit ∈ selectedSample ->
        selectedOutcomeT unit = treatedValue (unitTreatedPrognosticScore unit))
    (hscoreMeasTargetC :
      ∀ unit, unit ∈ targetSample ->
        targetOutcomeC unit = controlValue (unitControlPrognosticScore unit))
    (hscoreMeasSelectedC :
      ∀ unit, unit ∈ selectedSample ->
        selectedOutcomeC unit = controlValue (unitControlPrognosticScore unit))
    (hreprT :
      repr.treated.population_target =
        ∫ sample, populationTreatedOutcome sample ∂sampleLaw)
    (hreprC :
      repr.control.population_target =
        ∫ sample, populationControlOutcome sample ∂sampleLaw)
    (hcondT :
      sampleLaw[populationTreatedOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => populationTreatedValue
          (sampleTreatedPrognosticScore sample))
    (hcondC :
      sampleLaw[populationControlOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => populationControlValue
          (sampleControlPrognosticScore sample)) :
    weightedSampleMeanContrast targetSample baseWeight targetOutcomeT
          targetOutcomeC =
        weightedSampleMeanContrast selectedSample
          (prospectiveInverseSamplingWeight baseWeight
            (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
              unitControlPrognosticScore)
            samplingMass)
          selectedOutcomeT selectedOutcomeC ∧
      repr.selectedHajekPATE =
        (∫ sample,
            populationTreatedValue (sampleTreatedPrognosticScore sample)
            ∂sampleLaw) -
          (∫ sample,
            populationControlValue (sampleControlPrognosticScore sample)
            ∂sampleLaw) :=
  ⟨weightedSampleMeanContrast_eq_prospectivePATEDoubleScoreWeight
      targetSample selectedSample cells baseWeight targetOutcomeT
      targetOutcomeC selectedOutcomeT selectedOutcomeC unitPropensityScore
      unitTreatedPrognosticScore unitControlPrognosticScore treatment
      samplingMass treatedValue controlValue hcoverTarget hcoverSelected
      hmassTarget hsampling htreatedMass hcontrolMass hscoreMeasTargetT
      hscoreMeasSelectedT hscoreMeasTargetC hscoreMeasSelectedC,
    selectedHajekPATE_eq_scorePATE_of_condExp_pateDoubleScoreVersions
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub repr htreatedSampling hcontrolSampling
      samplePropensityScore sampleTreatedPrognosticScore
      sampleControlPrognosticScore populationTreatedOutcome
      populationControlOutcome populationTreatedValue populationControlValue
      hreprT hreprC hcondT hcondC⟩

/--
Retrospective PATT bridge: the finite selected double-score inverse-weighted
one-sided contrast recovers the finite target contrast, and the population
selected Hájek representation recovers the PATT double-score conditional-mean
ratio target.
-/
theorem retrospectivePATTDoubleScore_finite_recovery_and_population_identification
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (targetSample selectedSample : Finset Unit)
    (cells : Finset (PropensityCell × PATTProgCell))
    (baseWeight : Unit -> Real)
    (treatedTargetOutcome targetControlOutcome selectedControlOutcome :
      Unit -> Real)
    (unitPropensityScore : Unit -> PropensityCell)
    (unitControlPrognosticScore : Unit -> PATTProgCell)
    (treatment : Unit -> Prop) [DecidablePred treatment]
    (samplingIfTreated samplingIfControl :
      PropensityCell × PATTProgCell -> Real)
    (controlValue : PATTProgCell -> Real)
    (repr : PATTRepresentation)
    (hpopulationSampling : repr.sampling_mass ≠ 0)
    (hpopulationTreatedMass : repr.population_treated_mass ≠ 0)
    (samplePropensityScore : Sample -> PropensityCell)
    (sampleControlPrognosticScore : Sample -> PATTProgCell)
    (populationTreatedEffectNumerator populationTreatedMass :
      Sample -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hcoverTarget :
      ∀ unit, unit ∈ targetSample ->
        pattDoubleScore unitPropensityScore unitControlPrognosticScore
          unit ∈ cells)
    (hcoverSelected :
      ∀ unit, unit ∈ selectedSample ->
        pattDoubleScore unitPropensityScore unitControlPrognosticScore
          unit ∈ cells)
    (hmassTarget :
      ∀ cell, cell ∈ cells ->
        scoreCellMass targetSample baseWeight
          (pattDoubleScore unitPropensityScore unitControlPrognosticScore)
          cell ≠ 0)
    (hsamplingTreated :
      ∀ cell, cell ∈ cells -> samplingIfTreated cell ≠ 0)
    (hsamplingControl :
      ∀ cell, cell ∈ cells -> samplingIfControl cell ≠ 0)
    (hfiniteTreatedMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (selectedSample.filter treatment) baseWeight
            (pattDoubleScore unitPropensityScore unitControlPrognosticScore)
            cell =
          samplingIfTreated cell *
            scoreCellMass (targetSample.filter treatment) baseWeight
              (pattDoubleScore unitPropensityScore
                unitControlPrognosticScore) cell)
    (hfiniteControlMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (selectedSample.filter (fun unit => ¬ treatment unit))
            baseWeight
            (pattDoubleScore unitPropensityScore unitControlPrognosticScore)
            cell =
          samplingIfControl cell *
            scoreCellMass
              (targetSample.filter (fun unit => ¬ treatment unit))
              baseWeight
              (pattDoubleScore unitPropensityScore
                unitControlPrognosticScore) cell)
    (hscoreMeasTargetC :
      ∀ unit, unit ∈ targetSample ->
        targetControlOutcome unit =
          controlValue (unitControlPrognosticScore unit))
    (hscoreMeasSelectedC :
      ∀ unit, unit ∈ selectedSample ->
        selectedControlOutcome unit =
          controlValue (unitControlPrognosticScore unit))
    (hreprNumerator :
      repr.population_treated_effect_numerator =
        ∫ sample, populationTreatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      repr.population_treated_mass =
        ∫ sample, populationTreatedMass sample ∂sampleLaw)
    (hcondNumerator :
      sampleLaw[populationTreatedEffectNumerator | scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore samplePropensityScore
              sampleControlPrognosticScore sample))
    (hcondMass :
      sampleLaw[populationTreatedMass | scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore samplePropensityScore
              sampleControlPrognosticScore sample)) :
    weightedSampleMeanContrast targetSample baseWeight treatedTargetOutcome
          targetControlOutcome =
        pattWeightedMeanContrast targetSample selectedSample baseWeight
          (retrospectiveInverseSamplingWeight baseWeight
            (pattDoubleScore unitPropensityScore unitControlPrognosticScore)
            treatment samplingIfTreated samplingIfControl)
          treatedTargetOutcome selectedControlOutcome ∧
      repr.selectedHajekPATT =
        (∫ sample,
            scoreEffectCellValue
              (pattDoubleScore samplePropensityScore
                sampleControlPrognosticScore sample)
            ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore samplePropensityScore
                sampleControlPrognosticScore sample)
            ∂sampleLaw) :=
  ⟨weightedSampleMeanContrast_eq_retrospectivePATTDoubleScoreWeight
      targetSample selectedSample cells baseWeight treatedTargetOutcome
      targetControlOutcome selectedControlOutcome unitPropensityScore
      unitControlPrognosticScore treatment samplingIfTreated
      samplingIfControl controlValue hcoverTarget hcoverSelected hmassTarget
      hsamplingTreated hsamplingControl hfiniteTreatedMass
      hfiniteControlMass hscoreMeasTargetC hscoreMeasSelectedC,
    selectedHajekPATT_eq_scorePATT_of_condExp_pattDoubleScoreVersions
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub repr hpopulationSampling
      hpopulationTreatedMass samplePropensityScore sampleControlPrognosticScore
      populationTreatedEffectNumerator populationTreatedMass
      scoreEffectCellValue scoreTreatedMassCellValue hreprNumerator hreprMass
      hcondNumerator hcondMass⟩

/--
Paired retrospective PATE/PATT bridge: finite double-score recovery and the
corresponding population conditional-mean identification are returned together
for the two target estimands.
-/
theorem retrospectivePATE_PATTDoubleScore_finite_recovery_and_population_identification
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateTargetSample pateSelectedSample pattTargetSample pattSelectedSample :
      Finset Unit)
    (pateCells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (pattCells : Finset (PropensityCell × PATTProgCell))
    (pateBaseWeight pattBaseWeight : Unit -> Real)
    (pateTargetOutcomeT pateTargetOutcomeC pateSelectedOutcomeT
      pateSelectedOutcomeC pattTreatedTargetOutcome pattTargetControlOutcome
      pattSelectedControlOutcome : Unit -> Real)
    (unitPropensityScore : Unit -> PropensityCell)
    (unitTreatedPrognosticScore : Unit -> TreatedProgCell)
    (unitControlPrognosticScore : Unit -> ControlProgCell)
    (unitPATTControlPrognosticScore : Unit -> PATTProgCell)
    (treatment : Unit -> Prop) [DecidablePred treatment]
    (pateSamplingIfTreated pateSamplingIfControl :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (pattSamplingIfTreated pattSamplingIfControl :
      PropensityCell × PATTProgCell -> Real)
    (pateTreatedValue : TreatedProgCell -> Real)
    (pateControlValue : ControlProgCell -> Real)
    (pattControlValue : PATTProgCell -> Real)
    (pateRepr : PATERepresentation)
    (hpateTreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hpateControlSampling : pateRepr.control.sampling_mass ≠ 0)
    (pattRepr : PATTRepresentation)
    (hpattPopulationSampling : pattRepr.sampling_mass ≠ 0)
    (hpattPopulationTreatedMass : pattRepr.population_treated_mass ≠ 0)
    (samplePropensityScore : Sample -> PropensityCell)
    (sampleTreatedPrognosticScore : Sample -> TreatedProgCell)
    (sampleControlPrognosticScore : Sample -> ControlProgCell)
    (samplePATTControlPrognosticScore : Sample -> PATTProgCell)
    (populationTreatedOutcome populationControlOutcome : Sample -> Real)
    (populationTreatedEffectNumerator populationTreatedMass : Sample -> Real)
    (populationTreatedValue : TreatedProgCell -> Real)
    (populationControlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpateCoverTarget :
      ∀ unit, unit ∈ pateTargetSample ->
        pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
          unitControlPrognosticScore unit ∈ pateCells)
    (hpateCoverSelected :
      ∀ unit, unit ∈ pateSelectedSample ->
        pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
          unitControlPrognosticScore unit ∈ pateCells)
    (hpattCoverTarget :
      ∀ unit, unit ∈ pattTargetSample ->
        pattDoubleScore unitPropensityScore unitPATTControlPrognosticScore
          unit ∈ pattCells)
    (hpattCoverSelected :
      ∀ unit, unit ∈ pattSelectedSample ->
        pattDoubleScore unitPropensityScore unitPATTControlPrognosticScore
          unit ∈ pattCells)
    (hpateMassTarget :
      ∀ cell, cell ∈ pateCells ->
        scoreCellMass pateTargetSample pateBaseWeight
          (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
            unitControlPrognosticScore) cell ≠ 0)
    (hpattMassTarget :
      ∀ cell, cell ∈ pattCells ->
        scoreCellMass pattTargetSample pattBaseWeight
          (pattDoubleScore unitPropensityScore
            unitPATTControlPrognosticScore) cell ≠ 0)
    (hpateSamplingTreated :
      ∀ cell, cell ∈ pateCells -> pateSamplingIfTreated cell ≠ 0)
    (hpateSamplingControl :
      ∀ cell, cell ∈ pateCells -> pateSamplingIfControl cell ≠ 0)
    (hpattSamplingTreated :
      ∀ cell, cell ∈ pattCells -> pattSamplingIfTreated cell ≠ 0)
    (hpattSamplingControl :
      ∀ cell, cell ∈ pattCells -> pattSamplingIfControl cell ≠ 0)
    (hpateTreatedMass :
      ∀ cell, cell ∈ pateCells ->
        scoreCellMass (pateSelectedSample.filter treatment) pateBaseWeight
            (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
              unitControlPrognosticScore) cell =
          pateSamplingIfTreated cell *
            scoreCellMass (pateTargetSample.filter treatment) pateBaseWeight
              (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
                unitControlPrognosticScore) cell)
    (hpateControlMass :
      ∀ cell, cell ∈ pateCells ->
        scoreCellMass
            (pateSelectedSample.filter (fun unit => ¬ treatment unit))
            pateBaseWeight
            (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
              unitControlPrognosticScore) cell =
          pateSamplingIfControl cell *
            scoreCellMass
              (pateTargetSample.filter (fun unit => ¬ treatment unit))
              pateBaseWeight
              (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
                unitControlPrognosticScore) cell)
    (hpattFiniteTreatedMass :
      ∀ cell, cell ∈ pattCells ->
        scoreCellMass (pattSelectedSample.filter treatment) pattBaseWeight
            (pattDoubleScore unitPropensityScore
              unitPATTControlPrognosticScore) cell =
          pattSamplingIfTreated cell *
            scoreCellMass (pattTargetSample.filter treatment) pattBaseWeight
              (pattDoubleScore unitPropensityScore
                unitPATTControlPrognosticScore) cell)
    (hpattFiniteControlMass :
      ∀ cell, cell ∈ pattCells ->
        scoreCellMass
            (pattSelectedSample.filter (fun unit => ¬ treatment unit))
            pattBaseWeight
            (pattDoubleScore unitPropensityScore
              unitPATTControlPrognosticScore) cell =
          pattSamplingIfControl cell *
            scoreCellMass
              (pattTargetSample.filter (fun unit => ¬ treatment unit))
              pattBaseWeight
              (pattDoubleScore unitPropensityScore
                unitPATTControlPrognosticScore) cell)
    (hpateScoreMeasTargetT :
      ∀ unit, unit ∈ pateTargetSample ->
        pateTargetOutcomeT unit =
          pateTreatedValue (unitTreatedPrognosticScore unit))
    (hpateScoreMeasSelectedT :
      ∀ unit, unit ∈ pateSelectedSample ->
        pateSelectedOutcomeT unit =
          pateTreatedValue (unitTreatedPrognosticScore unit))
    (hpateScoreMeasTargetC :
      ∀ unit, unit ∈ pateTargetSample ->
        pateTargetOutcomeC unit =
          pateControlValue (unitControlPrognosticScore unit))
    (hpateScoreMeasSelectedC :
      ∀ unit, unit ∈ pateSelectedSample ->
        pateSelectedOutcomeC unit =
          pateControlValue (unitControlPrognosticScore unit))
    (hpattScoreMeasTargetC :
      ∀ unit, unit ∈ pattTargetSample ->
        pattTargetControlOutcome unit =
          pattControlValue (unitPATTControlPrognosticScore unit))
    (hpattScoreMeasSelectedC :
      ∀ unit, unit ∈ pattSelectedSample ->
        pattSelectedControlOutcome unit =
          pattControlValue (unitPATTControlPrognosticScore unit))
    (hpateReprT :
      pateRepr.treated.population_target =
        ∫ sample, populationTreatedOutcome sample ∂sampleLaw)
    (hpateReprC :
      pateRepr.control.population_target =
        ∫ sample, populationControlOutcome sample ∂sampleLaw)
    (hpattReprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, populationTreatedEffectNumerator sample ∂sampleLaw)
    (hpattReprMass :
      pattRepr.population_treated_mass =
        ∫ sample, populationTreatedMass sample ∂sampleLaw)
    (hpateCondT :
      sampleLaw[populationTreatedOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => populationTreatedValue
          (sampleTreatedPrognosticScore sample))
    (hpateCondC :
      sampleLaw[populationControlOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => populationControlValue
          (sampleControlPrognosticScore sample))
    (hpattCondNumerator :
      sampleLaw[populationTreatedEffectNumerator | scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore samplePropensityScore
              samplePATTControlPrognosticScore sample))
    (hpattCondMass :
      sampleLaw[populationTreatedMass | scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore samplePropensityScore
              samplePATTControlPrognosticScore sample)) :
    (weightedSampleMeanContrast pateTargetSample pateBaseWeight
          pateTargetOutcomeT pateTargetOutcomeC =
        weightedSampleMeanContrast pateSelectedSample
          (retrospectiveInverseSamplingWeight pateBaseWeight
            (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
              unitControlPrognosticScore)
            treatment pateSamplingIfTreated pateSamplingIfControl)
          pateSelectedOutcomeT pateSelectedOutcomeC ∧
      pateRepr.selectedHajekPATE =
        (∫ sample,
            populationTreatedValue (sampleTreatedPrognosticScore sample)
            ∂sampleLaw) -
          (∫ sample,
            populationControlValue (sampleControlPrognosticScore sample)
            ∂sampleLaw)) ∧
      (weightedSampleMeanContrast pattTargetSample pattBaseWeight
          pattTreatedTargetOutcome pattTargetControlOutcome =
        pattWeightedMeanContrast pattTargetSample pattSelectedSample
          pattBaseWeight
          (retrospectiveInverseSamplingWeight pattBaseWeight
            (pattDoubleScore unitPropensityScore
              unitPATTControlPrognosticScore)
            treatment pattSamplingIfTreated pattSamplingIfControl)
          pattTreatedTargetOutcome pattSelectedControlOutcome ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
            scoreEffectCellValue
              (pattDoubleScore samplePropensityScore
                samplePATTControlPrognosticScore sample)
            ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore samplePropensityScore
                samplePATTControlPrognosticScore sample)
            ∂sampleLaw)) := by
  constructor
  · exact
      retrospectivePATEDoubleScore_finite_recovery_and_population_identification
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pateTargetSample pateSelectedSample
        pateCells pateBaseWeight pateTargetOutcomeT pateTargetOutcomeC
        pateSelectedOutcomeT pateSelectedOutcomeC unitPropensityScore
        unitTreatedPrognosticScore unitControlPrognosticScore treatment
        pateSamplingIfTreated pateSamplingIfControl pateTreatedValue
        pateControlValue pateRepr hpateTreatedSampling hpateControlSampling
        samplePropensityScore sampleTreatedPrognosticScore
        sampleControlPrognosticScore populationTreatedOutcome
        populationControlOutcome populationTreatedValue populationControlValue
        hpateCoverTarget hpateCoverSelected hpateMassTarget
        hpateSamplingTreated hpateSamplingControl hpateTreatedMass
        hpateControlMass hpateScoreMeasTargetT hpateScoreMeasSelectedT
        hpateScoreMeasTargetC hpateScoreMeasSelectedC hpateReprT
        hpateReprC hpateCondT hpateCondC
  · exact
      retrospectivePATTDoubleScore_finite_recovery_and_population_identification
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pattTargetSample pattSelectedSample
        pattCells pattBaseWeight pattTreatedTargetOutcome
        pattTargetControlOutcome pattSelectedControlOutcome
        unitPropensityScore unitPATTControlPrognosticScore treatment
        pattSamplingIfTreated pattSamplingIfControl pattControlValue pattRepr
        hpattPopulationSampling hpattPopulationTreatedMass
        samplePropensityScore samplePATTControlPrognosticScore
        populationTreatedEffectNumerator populationTreatedMass
        scoreEffectCellValue scoreTreatedMassCellValue hpattCoverTarget
        hpattCoverSelected hpattMassTarget hpattSamplingTreated
        hpattSamplingControl hpattFiniteTreatedMass hpattFiniteControlMass
        hpattScoreMeasTargetC hpattScoreMeasSelectedC hpattReprNumerator
        hpattReprMass hpattCondNumerator hpattCondMass

/--
Prospective PATT bridge: the finite selected double-score common
inverse-weighted one-sided contrast recovers the finite target contrast, and
the population selected Hájek representation recovers the PATT double-score
conditional-mean ratio target.
-/
theorem prospectivePATTDoubleScore_finite_recovery_and_population_identification
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (targetSample selectedSample : Finset Unit)
    (cells : Finset (PropensityCell × PATTProgCell))
    (baseWeight : Unit -> Real)
    (treatedTargetOutcome targetControlOutcome selectedControlOutcome :
      Unit -> Real)
    (unitPropensityScore : Unit -> PropensityCell)
    (unitControlPrognosticScore : Unit -> PATTProgCell)
    (treatment : Unit -> Prop) [DecidablePred treatment]
    (samplingMass : PropensityCell × PATTProgCell -> Real)
    (controlValue : PATTProgCell -> Real)
    (repr : PATTRepresentation)
    (hpopulationSampling : repr.sampling_mass ≠ 0)
    (hpopulationTreatedMass : repr.population_treated_mass ≠ 0)
    (samplePropensityScore : Sample -> PropensityCell)
    (sampleControlPrognosticScore : Sample -> PATTProgCell)
    (populationTreatedEffectNumerator populationTreatedMass :
      Sample -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hcoverTarget :
      ∀ unit, unit ∈ targetSample ->
        pattDoubleScore unitPropensityScore unitControlPrognosticScore
          unit ∈ cells)
    (hcoverSelected :
      ∀ unit, unit ∈ selectedSample ->
        pattDoubleScore unitPropensityScore unitControlPrognosticScore
          unit ∈ cells)
    (hmassTarget :
      ∀ cell, cell ∈ cells ->
        scoreCellMass targetSample baseWeight
          (pattDoubleScore unitPropensityScore unitControlPrognosticScore)
          cell ≠ 0)
    (hfiniteSampling :
      ∀ cell, cell ∈ cells -> samplingMass cell ≠ 0)
    (hfiniteTreatedMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (selectedSample.filter treatment) baseWeight
            (pattDoubleScore unitPropensityScore unitControlPrognosticScore)
            cell =
          samplingMass cell *
            scoreCellMass (targetSample.filter treatment) baseWeight
              (pattDoubleScore unitPropensityScore
                unitControlPrognosticScore) cell)
    (hfiniteControlMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (selectedSample.filter (fun unit => ¬ treatment unit))
            baseWeight
            (pattDoubleScore unitPropensityScore unitControlPrognosticScore)
            cell =
          samplingMass cell *
            scoreCellMass
              (targetSample.filter (fun unit => ¬ treatment unit))
              baseWeight
              (pattDoubleScore unitPropensityScore
                unitControlPrognosticScore) cell)
    (hscoreMeasTargetC :
      ∀ unit, unit ∈ targetSample ->
        targetControlOutcome unit =
          controlValue (unitControlPrognosticScore unit))
    (hscoreMeasSelectedC :
      ∀ unit, unit ∈ selectedSample ->
        selectedControlOutcome unit =
          controlValue (unitControlPrognosticScore unit))
    (hreprNumerator :
      repr.population_treated_effect_numerator =
        ∫ sample, populationTreatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      repr.population_treated_mass =
        ∫ sample, populationTreatedMass sample ∂sampleLaw)
    (hcondNumerator :
      sampleLaw[populationTreatedEffectNumerator | scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore samplePropensityScore
              sampleControlPrognosticScore sample))
    (hcondMass :
      sampleLaw[populationTreatedMass | scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore samplePropensityScore
              sampleControlPrognosticScore sample)) :
    weightedSampleMeanContrast targetSample baseWeight treatedTargetOutcome
          targetControlOutcome =
        pattWeightedMeanContrast targetSample selectedSample baseWeight
          (prospectiveInverseSamplingWeight baseWeight
            (pattDoubleScore unitPropensityScore unitControlPrognosticScore)
            samplingMass)
          treatedTargetOutcome selectedControlOutcome ∧
      repr.selectedHajekPATT =
        (∫ sample,
            scoreEffectCellValue
              (pattDoubleScore samplePropensityScore
                sampleControlPrognosticScore sample)
            ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore samplePropensityScore
                sampleControlPrognosticScore sample)
            ∂sampleLaw) :=
  ⟨weightedSampleMeanContrast_eq_prospectivePATTDoubleScoreWeight
      targetSample selectedSample cells baseWeight treatedTargetOutcome
      targetControlOutcome selectedControlOutcome unitPropensityScore
      unitControlPrognosticScore treatment samplingMass controlValue
      hcoverTarget hcoverSelected hmassTarget hfiniteSampling
      hfiniteTreatedMass hfiniteControlMass hscoreMeasTargetC
      hscoreMeasSelectedC,
    selectedHajekPATT_eq_scorePATT_of_condExp_pattDoubleScoreVersions
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub repr hpopulationSampling
      hpopulationTreatedMass samplePropensityScore sampleControlPrognosticScore
      populationTreatedEffectNumerator populationTreatedMass
      scoreEffectCellValue scoreTreatedMassCellValue hreprNumerator hreprMass
      hcondNumerator hcondMass⟩

/--
Paired prospective PATE/PATT bridge: finite common-sampling double-score
recovery and population conditional-mean identification for both target
estimands.
-/
theorem prospectivePATE_PATTDoubleScore_finite_recovery_and_population_identification
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateTargetSample pateSelectedSample pattTargetSample pattSelectedSample :
      Finset Unit)
    (pateCells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (pattCells : Finset (PropensityCell × PATTProgCell))
    (pateBaseWeight pattBaseWeight : Unit -> Real)
    (pateTargetOutcomeT pateTargetOutcomeC pateSelectedOutcomeT
      pateSelectedOutcomeC pattTreatedTargetOutcome pattTargetControlOutcome
      pattSelectedControlOutcome : Unit -> Real)
    (unitPropensityScore : Unit -> PropensityCell)
    (unitTreatedPrognosticScore : Unit -> TreatedProgCell)
    (unitControlPrognosticScore : Unit -> ControlProgCell)
    (unitPATTControlPrognosticScore : Unit -> PATTProgCell)
    (treatment : Unit -> Prop) [DecidablePred treatment]
    (pateSamplingMass :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (pattSamplingMass : PropensityCell × PATTProgCell -> Real)
    (pateTreatedValue : TreatedProgCell -> Real)
    (pateControlValue : ControlProgCell -> Real)
    (pattControlValue : PATTProgCell -> Real)
    (pateRepr : PATERepresentation)
    (hpateTreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hpateControlSampling : pateRepr.control.sampling_mass ≠ 0)
    (pattRepr : PATTRepresentation)
    (hpattPopulationSampling : pattRepr.sampling_mass ≠ 0)
    (hpattPopulationTreatedMass : pattRepr.population_treated_mass ≠ 0)
    (samplePropensityScore : Sample -> PropensityCell)
    (sampleTreatedPrognosticScore : Sample -> TreatedProgCell)
    (sampleControlPrognosticScore : Sample -> ControlProgCell)
    (samplePATTControlPrognosticScore : Sample -> PATTProgCell)
    (populationTreatedOutcome populationControlOutcome : Sample -> Real)
    (populationTreatedEffectNumerator populationTreatedMass : Sample -> Real)
    (populationTreatedValue : TreatedProgCell -> Real)
    (populationControlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpateCoverTarget :
      ∀ unit, unit ∈ pateTargetSample ->
        pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
          unitControlPrognosticScore unit ∈ pateCells)
    (hpateCoverSelected :
      ∀ unit, unit ∈ pateSelectedSample ->
        pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
          unitControlPrognosticScore unit ∈ pateCells)
    (hpattCoverTarget :
      ∀ unit, unit ∈ pattTargetSample ->
        pattDoubleScore unitPropensityScore unitPATTControlPrognosticScore
          unit ∈ pattCells)
    (hpattCoverSelected :
      ∀ unit, unit ∈ pattSelectedSample ->
        pattDoubleScore unitPropensityScore unitPATTControlPrognosticScore
          unit ∈ pattCells)
    (hpateMassTarget :
      ∀ cell, cell ∈ pateCells ->
        scoreCellMass pateTargetSample pateBaseWeight
          (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
            unitControlPrognosticScore) cell ≠ 0)
    (hpattMassTarget :
      ∀ cell, cell ∈ pattCells ->
        scoreCellMass pattTargetSample pattBaseWeight
          (pattDoubleScore unitPropensityScore
            unitPATTControlPrognosticScore) cell ≠ 0)
    (hpateSampling :
      ∀ cell, cell ∈ pateCells -> pateSamplingMass cell ≠ 0)
    (hpattSampling :
      ∀ cell, cell ∈ pattCells -> pattSamplingMass cell ≠ 0)
    (hpateTreatedMass :
      ∀ cell, cell ∈ pateCells ->
        scoreCellMass (pateSelectedSample.filter treatment) pateBaseWeight
            (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
              unitControlPrognosticScore) cell =
          pateSamplingMass cell *
            scoreCellMass (pateTargetSample.filter treatment) pateBaseWeight
              (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
                unitControlPrognosticScore) cell)
    (hpateControlMass :
      ∀ cell, cell ∈ pateCells ->
        scoreCellMass
            (pateSelectedSample.filter (fun unit => ¬ treatment unit))
            pateBaseWeight
            (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
              unitControlPrognosticScore) cell =
          pateSamplingMass cell *
            scoreCellMass
              (pateTargetSample.filter (fun unit => ¬ treatment unit))
              pateBaseWeight
              (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
                unitControlPrognosticScore) cell)
    (hpattFiniteTreatedMass :
      ∀ cell, cell ∈ pattCells ->
        scoreCellMass (pattSelectedSample.filter treatment) pattBaseWeight
            (pattDoubleScore unitPropensityScore
              unitPATTControlPrognosticScore) cell =
          pattSamplingMass cell *
            scoreCellMass (pattTargetSample.filter treatment) pattBaseWeight
              (pattDoubleScore unitPropensityScore
                unitPATTControlPrognosticScore) cell)
    (hpattFiniteControlMass :
      ∀ cell, cell ∈ pattCells ->
        scoreCellMass
            (pattSelectedSample.filter (fun unit => ¬ treatment unit))
            pattBaseWeight
            (pattDoubleScore unitPropensityScore
              unitPATTControlPrognosticScore) cell =
          pattSamplingMass cell *
            scoreCellMass
              (pattTargetSample.filter (fun unit => ¬ treatment unit))
              pattBaseWeight
              (pattDoubleScore unitPropensityScore
                unitPATTControlPrognosticScore) cell)
    (hpateScoreMeasTargetT :
      ∀ unit, unit ∈ pateTargetSample ->
        pateTargetOutcomeT unit =
          pateTreatedValue (unitTreatedPrognosticScore unit))
    (hpateScoreMeasSelectedT :
      ∀ unit, unit ∈ pateSelectedSample ->
        pateSelectedOutcomeT unit =
          pateTreatedValue (unitTreatedPrognosticScore unit))
    (hpateScoreMeasTargetC :
      ∀ unit, unit ∈ pateTargetSample ->
        pateTargetOutcomeC unit =
          pateControlValue (unitControlPrognosticScore unit))
    (hpateScoreMeasSelectedC :
      ∀ unit, unit ∈ pateSelectedSample ->
        pateSelectedOutcomeC unit =
          pateControlValue (unitControlPrognosticScore unit))
    (hpattScoreMeasTargetC :
      ∀ unit, unit ∈ pattTargetSample ->
        pattTargetControlOutcome unit =
          pattControlValue (unitPATTControlPrognosticScore unit))
    (hpattScoreMeasSelectedC :
      ∀ unit, unit ∈ pattSelectedSample ->
        pattSelectedControlOutcome unit =
          pattControlValue (unitPATTControlPrognosticScore unit))
    (hpateReprT :
      pateRepr.treated.population_target =
        ∫ sample, populationTreatedOutcome sample ∂sampleLaw)
    (hpateReprC :
      pateRepr.control.population_target =
        ∫ sample, populationControlOutcome sample ∂sampleLaw)
    (hpattReprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, populationTreatedEffectNumerator sample ∂sampleLaw)
    (hpattReprMass :
      pattRepr.population_treated_mass =
        ∫ sample, populationTreatedMass sample ∂sampleLaw)
    (hpateCondT :
      sampleLaw[populationTreatedOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => populationTreatedValue
          (sampleTreatedPrognosticScore sample))
    (hpateCondC :
      sampleLaw[populationControlOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => populationControlValue
          (sampleControlPrognosticScore sample))
    (hpattCondNumerator :
      sampleLaw[populationTreatedEffectNumerator | scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore samplePropensityScore
              samplePATTControlPrognosticScore sample))
    (hpattCondMass :
      sampleLaw[populationTreatedMass | scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore samplePropensityScore
              samplePATTControlPrognosticScore sample)) :
    (weightedSampleMeanContrast pateTargetSample pateBaseWeight
          pateTargetOutcomeT pateTargetOutcomeC =
        weightedSampleMeanContrast pateSelectedSample
          (prospectiveInverseSamplingWeight pateBaseWeight
            (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
              unitControlPrognosticScore)
            pateSamplingMass)
          pateSelectedOutcomeT pateSelectedOutcomeC ∧
      pateRepr.selectedHajekPATE =
        (∫ sample,
            populationTreatedValue (sampleTreatedPrognosticScore sample)
            ∂sampleLaw) -
          (∫ sample,
            populationControlValue (sampleControlPrognosticScore sample)
            ∂sampleLaw)) ∧
      (weightedSampleMeanContrast pattTargetSample pattBaseWeight
          pattTreatedTargetOutcome pattTargetControlOutcome =
        pattWeightedMeanContrast pattTargetSample pattSelectedSample
          pattBaseWeight
          (prospectiveInverseSamplingWeight pattBaseWeight
            (pattDoubleScore unitPropensityScore
              unitPATTControlPrognosticScore)
            pattSamplingMass)
          pattTreatedTargetOutcome pattSelectedControlOutcome ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
            scoreEffectCellValue
              (pattDoubleScore samplePropensityScore
                samplePATTControlPrognosticScore sample)
            ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore samplePropensityScore
                samplePATTControlPrognosticScore sample)
            ∂sampleLaw)) := by
  constructor
  · exact
      prospectivePATEDoubleScore_finite_recovery_and_population_identification
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pateTargetSample pateSelectedSample
        pateCells pateBaseWeight pateTargetOutcomeT pateTargetOutcomeC
        pateSelectedOutcomeT pateSelectedOutcomeC unitPropensityScore
        unitTreatedPrognosticScore unitControlPrognosticScore treatment
        pateSamplingMass pateTreatedValue pateControlValue pateRepr
        hpateTreatedSampling hpateControlSampling samplePropensityScore
        sampleTreatedPrognosticScore sampleControlPrognosticScore
        populationTreatedOutcome populationControlOutcome
        populationTreatedValue populationControlValue hpateCoverTarget
        hpateCoverSelected hpateMassTarget hpateSampling hpateTreatedMass
        hpateControlMass hpateScoreMeasTargetT hpateScoreMeasSelectedT
        hpateScoreMeasTargetC hpateScoreMeasSelectedC hpateReprT
        hpateReprC hpateCondT hpateCondC
  · exact
      prospectivePATTDoubleScore_finite_recovery_and_population_identification
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pattTargetSample pattSelectedSample
        pattCells pattBaseWeight pattTreatedTargetOutcome
        pattTargetControlOutcome pattSelectedControlOutcome
        unitPropensityScore unitPATTControlPrognosticScore treatment
        pattSamplingMass pattControlValue pattRepr hpattPopulationSampling
        hpattPopulationTreatedMass samplePropensityScore
        samplePATTControlPrognosticScore populationTreatedEffectNumerator
        populationTreatedMass scoreEffectCellValue scoreTreatedMassCellValue
        hpattCoverTarget hpattCoverSelected hpattMassTarget hpattSampling
        hpattFiniteTreatedMass hpattFiniteControlMass hpattScoreMeasTargetC
        hpattScoreMeasSelectedC hpattReprNumerator hpattReprMass
        hpattCondNumerator hpattCondMass

/--
Retrospective PATE finite recovery and population identification over a finite
double-score alphabet, with the cell set specialized to `Finset.univ`.
-/
theorem retrospectivePATEDoubleScore_finite_recovery_and_population_identification_fintype
    [Fintype ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (targetSample selectedSample : Finset Unit)
    (baseWeight : Unit -> Real)
    (targetOutcomeT targetOutcomeC selectedOutcomeT selectedOutcomeC :
      Unit -> Real)
    (unitPropensityScore : Unit -> PropensityCell)
    (unitTreatedPrognosticScore : Unit -> TreatedProgCell)
    (unitControlPrognosticScore : Unit -> ControlProgCell)
    (treatment : Unit -> Prop) [DecidablePred treatment]
    (samplingIfTreated samplingIfControl :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (repr : PATERepresentation)
    (htreatedSampling : repr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : repr.control.sampling_mass ≠ 0)
    (samplePropensityScore : Sample -> PropensityCell)
    (sampleTreatedPrognosticScore : Sample -> TreatedProgCell)
    (sampleControlPrognosticScore : Sample -> ControlProgCell)
    (populationTreatedOutcome populationControlOutcome : Sample -> Real)
    (populationTreatedValue : TreatedProgCell -> Real)
    (populationControlValue : ControlProgCell -> Real)
    (hmassTarget :
      ∀ cell,
        scoreCellMass targetSample baseWeight
          (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
            unitControlPrognosticScore) cell ≠ 0)
    (hsamplingTreated : ∀ cell, samplingIfTreated cell ≠ 0)
    (hsamplingControl : ∀ cell, samplingIfControl cell ≠ 0)
    (htreatedMass :
      ∀ cell,
        scoreCellMass (selectedSample.filter treatment) baseWeight
            (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
              unitControlPrognosticScore) cell =
          samplingIfTreated cell *
            scoreCellMass (targetSample.filter treatment) baseWeight
              (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
                unitControlPrognosticScore) cell)
    (hcontrolMass :
      ∀ cell,
        scoreCellMass (selectedSample.filter (fun unit => ¬ treatment unit))
            baseWeight
            (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
              unitControlPrognosticScore) cell =
          samplingIfControl cell *
            scoreCellMass
              (targetSample.filter (fun unit => ¬ treatment unit))
              baseWeight
              (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
                unitControlPrognosticScore) cell)
    (hscoreMeasTargetT :
      ∀ unit, unit ∈ targetSample ->
        targetOutcomeT unit = treatedValue (unitTreatedPrognosticScore unit))
    (hscoreMeasSelectedT :
      ∀ unit, unit ∈ selectedSample ->
        selectedOutcomeT unit = treatedValue (unitTreatedPrognosticScore unit))
    (hscoreMeasTargetC :
      ∀ unit, unit ∈ targetSample ->
        targetOutcomeC unit = controlValue (unitControlPrognosticScore unit))
    (hscoreMeasSelectedC :
      ∀ unit, unit ∈ selectedSample ->
        selectedOutcomeC unit = controlValue (unitControlPrognosticScore unit))
    (hreprT :
      repr.treated.population_target =
        ∫ sample, populationTreatedOutcome sample ∂sampleLaw)
    (hreprC :
      repr.control.population_target =
        ∫ sample, populationControlOutcome sample ∂sampleLaw)
    (hcondT :
      sampleLaw[populationTreatedOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => populationTreatedValue
          (sampleTreatedPrognosticScore sample))
    (hcondC :
      sampleLaw[populationControlOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => populationControlValue
          (sampleControlPrognosticScore sample)) :
    weightedSampleMeanContrast targetSample baseWeight targetOutcomeT
          targetOutcomeC =
        weightedSampleMeanContrast selectedSample
          (retrospectiveInverseSamplingWeight baseWeight
            (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
              unitControlPrognosticScore)
            treatment samplingIfTreated samplingIfControl)
          selectedOutcomeT selectedOutcomeC ∧
      repr.selectedHajekPATE =
        (∫ sample,
            populationTreatedValue (sampleTreatedPrognosticScore sample)
            ∂sampleLaw) -
          (∫ sample,
            populationControlValue (sampleControlPrognosticScore sample)
            ∂sampleLaw) :=
  retrospectivePATEDoubleScore_finite_recovery_and_population_identification
    (mSample := mSample) (scoreSigma := scoreSigma)
    (sampleLaw := sampleLaw) hsub targetSample selectedSample Finset.univ
    baseWeight targetOutcomeT targetOutcomeC selectedOutcomeT
    selectedOutcomeC unitPropensityScore unitTreatedPrognosticScore
    unitControlPrognosticScore treatment samplingIfTreated samplingIfControl
    treatedValue controlValue repr htreatedSampling hcontrolSampling
    samplePropensityScore sampleTreatedPrognosticScore
    sampleControlPrognosticScore populationTreatedOutcome
    populationControlOutcome populationTreatedValue populationControlValue
    (fun _unit _hunit => by simp)
    (fun _unit _hunit => by simp)
    (fun cell _hcell => hmassTarget cell)
    (fun cell _hcell => hsamplingTreated cell)
    (fun cell _hcell => hsamplingControl cell)
    (fun cell _hcell => htreatedMass cell)
    (fun cell _hcell => hcontrolMass cell)
    hscoreMeasTargetT hscoreMeasSelectedT hscoreMeasTargetC
    hscoreMeasSelectedC hreprT hreprC hcondT hcondC

/--
Prospective PATE finite recovery and population identification over a finite
double-score alphabet, with the cell set specialized to `Finset.univ`.
-/
theorem prospectivePATEDoubleScore_finite_recovery_and_population_identification_fintype
    [Fintype ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (targetSample selectedSample : Finset Unit)
    (baseWeight : Unit -> Real)
    (targetOutcomeT targetOutcomeC selectedOutcomeT selectedOutcomeC :
      Unit -> Real)
    (unitPropensityScore : Unit -> PropensityCell)
    (unitTreatedPrognosticScore : Unit -> TreatedProgCell)
    (unitControlPrognosticScore : Unit -> ControlProgCell)
    (treatment : Unit -> Prop) [DecidablePred treatment]
    (samplingMass :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (repr : PATERepresentation)
    (htreatedSampling : repr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : repr.control.sampling_mass ≠ 0)
    (samplePropensityScore : Sample -> PropensityCell)
    (sampleTreatedPrognosticScore : Sample -> TreatedProgCell)
    (sampleControlPrognosticScore : Sample -> ControlProgCell)
    (populationTreatedOutcome populationControlOutcome : Sample -> Real)
    (populationTreatedValue : TreatedProgCell -> Real)
    (populationControlValue : ControlProgCell -> Real)
    (hmassTarget :
      ∀ cell,
        scoreCellMass targetSample baseWeight
          (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
            unitControlPrognosticScore) cell ≠ 0)
    (hsampling : ∀ cell, samplingMass cell ≠ 0)
    (htreatedMass :
      ∀ cell,
        scoreCellMass (selectedSample.filter treatment) baseWeight
            (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
              unitControlPrognosticScore) cell =
          samplingMass cell *
            scoreCellMass (targetSample.filter treatment) baseWeight
              (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
                unitControlPrognosticScore) cell)
    (hcontrolMass :
      ∀ cell,
        scoreCellMass (selectedSample.filter (fun unit => ¬ treatment unit))
            baseWeight
            (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
              unitControlPrognosticScore) cell =
          samplingMass cell *
            scoreCellMass
              (targetSample.filter (fun unit => ¬ treatment unit))
              baseWeight
              (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
                unitControlPrognosticScore) cell)
    (hscoreMeasTargetT :
      ∀ unit, unit ∈ targetSample ->
        targetOutcomeT unit = treatedValue (unitTreatedPrognosticScore unit))
    (hscoreMeasSelectedT :
      ∀ unit, unit ∈ selectedSample ->
        selectedOutcomeT unit = treatedValue (unitTreatedPrognosticScore unit))
    (hscoreMeasTargetC :
      ∀ unit, unit ∈ targetSample ->
        targetOutcomeC unit = controlValue (unitControlPrognosticScore unit))
    (hscoreMeasSelectedC :
      ∀ unit, unit ∈ selectedSample ->
        selectedOutcomeC unit = controlValue (unitControlPrognosticScore unit))
    (hreprT :
      repr.treated.population_target =
        ∫ sample, populationTreatedOutcome sample ∂sampleLaw)
    (hreprC :
      repr.control.population_target =
        ∫ sample, populationControlOutcome sample ∂sampleLaw)
    (hcondT :
      sampleLaw[populationTreatedOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => populationTreatedValue
          (sampleTreatedPrognosticScore sample))
    (hcondC :
      sampleLaw[populationControlOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => populationControlValue
          (sampleControlPrognosticScore sample)) :
    weightedSampleMeanContrast targetSample baseWeight targetOutcomeT
          targetOutcomeC =
        weightedSampleMeanContrast selectedSample
          (prospectiveInverseSamplingWeight baseWeight
            (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
              unitControlPrognosticScore)
            samplingMass)
          selectedOutcomeT selectedOutcomeC ∧
      repr.selectedHajekPATE =
        (∫ sample,
            populationTreatedValue (sampleTreatedPrognosticScore sample)
            ∂sampleLaw) -
          (∫ sample,
            populationControlValue (sampleControlPrognosticScore sample)
            ∂sampleLaw) :=
  prospectivePATEDoubleScore_finite_recovery_and_population_identification
    (mSample := mSample) (scoreSigma := scoreSigma)
    (sampleLaw := sampleLaw) hsub targetSample selectedSample Finset.univ
    baseWeight targetOutcomeT targetOutcomeC selectedOutcomeT
    selectedOutcomeC unitPropensityScore unitTreatedPrognosticScore
    unitControlPrognosticScore treatment samplingMass treatedValue
    controlValue repr htreatedSampling hcontrolSampling
    samplePropensityScore sampleTreatedPrognosticScore
    sampleControlPrognosticScore populationTreatedOutcome
    populationControlOutcome populationTreatedValue populationControlValue
    (fun _unit _hunit => by simp)
    (fun _unit _hunit => by simp)
    (fun cell _hcell => hmassTarget cell)
    (fun cell _hcell => hsampling cell)
    (fun cell _hcell => htreatedMass cell)
    (fun cell _hcell => hcontrolMass cell)
    hscoreMeasTargetT hscoreMeasSelectedT hscoreMeasTargetC
    hscoreMeasSelectedC hreprT hreprC hcondT hcondC

/--
Retrospective PATT finite recovery and population identification over a finite
double-score alphabet, with the cell set specialized to `Finset.univ`.
-/
theorem retrospectivePATTDoubleScore_finite_recovery_and_population_identification_fintype
    [Fintype (PropensityCell × PATTProgCell)]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (targetSample selectedSample : Finset Unit)
    (baseWeight : Unit -> Real)
    (treatedTargetOutcome targetControlOutcome selectedControlOutcome :
      Unit -> Real)
    (unitPropensityScore : Unit -> PropensityCell)
    (unitControlPrognosticScore : Unit -> PATTProgCell)
    (treatment : Unit -> Prop) [DecidablePred treatment]
    (samplingIfTreated samplingIfControl :
      PropensityCell × PATTProgCell -> Real)
    (controlValue : PATTProgCell -> Real)
    (repr : PATTRepresentation)
    (hpopulationSampling : repr.sampling_mass ≠ 0)
    (hpopulationTreatedMass : repr.population_treated_mass ≠ 0)
    (samplePropensityScore : Sample -> PropensityCell)
    (sampleControlPrognosticScore : Sample -> PATTProgCell)
    (populationTreatedEffectNumerator populationTreatedMass :
      Sample -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hmassTarget :
      ∀ cell,
        scoreCellMass targetSample baseWeight
          (pattDoubleScore unitPropensityScore unitControlPrognosticScore)
          cell ≠ 0)
    (hsamplingTreated : ∀ cell, samplingIfTreated cell ≠ 0)
    (hsamplingControl : ∀ cell, samplingIfControl cell ≠ 0)
    (hfiniteTreatedMass :
      ∀ cell,
        scoreCellMass (selectedSample.filter treatment) baseWeight
            (pattDoubleScore unitPropensityScore unitControlPrognosticScore)
            cell =
          samplingIfTreated cell *
            scoreCellMass (targetSample.filter treatment) baseWeight
              (pattDoubleScore unitPropensityScore
                unitControlPrognosticScore) cell)
    (hfiniteControlMass :
      ∀ cell,
        scoreCellMass (selectedSample.filter (fun unit => ¬ treatment unit))
            baseWeight
            (pattDoubleScore unitPropensityScore unitControlPrognosticScore)
            cell =
          samplingIfControl cell *
            scoreCellMass
              (targetSample.filter (fun unit => ¬ treatment unit))
              baseWeight
              (pattDoubleScore unitPropensityScore
                unitControlPrognosticScore) cell)
    (hscoreMeasTargetC :
      ∀ unit, unit ∈ targetSample ->
        targetControlOutcome unit =
          controlValue (unitControlPrognosticScore unit))
    (hscoreMeasSelectedC :
      ∀ unit, unit ∈ selectedSample ->
        selectedControlOutcome unit =
          controlValue (unitControlPrognosticScore unit))
    (hreprNumerator :
      repr.population_treated_effect_numerator =
        ∫ sample, populationTreatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      repr.population_treated_mass =
        ∫ sample, populationTreatedMass sample ∂sampleLaw)
    (hcondNumerator :
      sampleLaw[populationTreatedEffectNumerator | scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore samplePropensityScore
              sampleControlPrognosticScore sample))
    (hcondMass :
      sampleLaw[populationTreatedMass | scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore samplePropensityScore
              sampleControlPrognosticScore sample)) :
    weightedSampleMeanContrast targetSample baseWeight treatedTargetOutcome
          targetControlOutcome =
        pattWeightedMeanContrast targetSample selectedSample baseWeight
          (retrospectiveInverseSamplingWeight baseWeight
            (pattDoubleScore unitPropensityScore unitControlPrognosticScore)
            treatment samplingIfTreated samplingIfControl)
          treatedTargetOutcome selectedControlOutcome ∧
      repr.selectedHajekPATT =
        (∫ sample,
            scoreEffectCellValue
              (pattDoubleScore samplePropensityScore
                sampleControlPrognosticScore sample)
            ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore samplePropensityScore
                sampleControlPrognosticScore sample)
            ∂sampleLaw) :=
  retrospectivePATTDoubleScore_finite_recovery_and_population_identification
    (mSample := mSample) (scoreSigma := scoreSigma)
    (sampleLaw := sampleLaw) hsub targetSample selectedSample Finset.univ
    baseWeight treatedTargetOutcome targetControlOutcome
    selectedControlOutcome unitPropensityScore unitControlPrognosticScore
    treatment samplingIfTreated samplingIfControl controlValue repr
    hpopulationSampling hpopulationTreatedMass samplePropensityScore
    sampleControlPrognosticScore populationTreatedEffectNumerator
    populationTreatedMass scoreEffectCellValue scoreTreatedMassCellValue
    (fun _unit _hunit => by simp)
    (fun _unit _hunit => by simp)
    (fun cell _hcell => hmassTarget cell)
    (fun cell _hcell => hsamplingTreated cell)
    (fun cell _hcell => hsamplingControl cell)
    (fun cell _hcell => hfiniteTreatedMass cell)
    (fun cell _hcell => hfiniteControlMass cell)
    hscoreMeasTargetC hscoreMeasSelectedC hreprNumerator hreprMass
    hcondNumerator hcondMass

/--
Prospective PATT finite recovery and population identification over a finite
double-score alphabet, with the cell set specialized to `Finset.univ`.
-/
theorem prospectivePATTDoubleScore_finite_recovery_and_population_identification_fintype
    [Fintype (PropensityCell × PATTProgCell)]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (targetSample selectedSample : Finset Unit)
    (baseWeight : Unit -> Real)
    (treatedTargetOutcome targetControlOutcome selectedControlOutcome :
      Unit -> Real)
    (unitPropensityScore : Unit -> PropensityCell)
    (unitControlPrognosticScore : Unit -> PATTProgCell)
    (treatment : Unit -> Prop) [DecidablePred treatment]
    (samplingMass : PropensityCell × PATTProgCell -> Real)
    (controlValue : PATTProgCell -> Real)
    (repr : PATTRepresentation)
    (hpopulationSampling : repr.sampling_mass ≠ 0)
    (hpopulationTreatedMass : repr.population_treated_mass ≠ 0)
    (samplePropensityScore : Sample -> PropensityCell)
    (sampleControlPrognosticScore : Sample -> PATTProgCell)
    (populationTreatedEffectNumerator populationTreatedMass :
      Sample -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hmassTarget :
      ∀ cell,
        scoreCellMass targetSample baseWeight
          (pattDoubleScore unitPropensityScore unitControlPrognosticScore)
          cell ≠ 0)
    (hfiniteSampling : ∀ cell, samplingMass cell ≠ 0)
    (hfiniteTreatedMass :
      ∀ cell,
        scoreCellMass (selectedSample.filter treatment) baseWeight
            (pattDoubleScore unitPropensityScore unitControlPrognosticScore)
            cell =
          samplingMass cell *
            scoreCellMass (targetSample.filter treatment) baseWeight
              (pattDoubleScore unitPropensityScore
                unitControlPrognosticScore) cell)
    (hfiniteControlMass :
      ∀ cell,
        scoreCellMass (selectedSample.filter (fun unit => ¬ treatment unit))
            baseWeight
            (pattDoubleScore unitPropensityScore unitControlPrognosticScore)
            cell =
          samplingMass cell *
            scoreCellMass
              (targetSample.filter (fun unit => ¬ treatment unit))
              baseWeight
              (pattDoubleScore unitPropensityScore
                unitControlPrognosticScore) cell)
    (hscoreMeasTargetC :
      ∀ unit, unit ∈ targetSample ->
        targetControlOutcome unit =
          controlValue (unitControlPrognosticScore unit))
    (hscoreMeasSelectedC :
      ∀ unit, unit ∈ selectedSample ->
        selectedControlOutcome unit =
          controlValue (unitControlPrognosticScore unit))
    (hreprNumerator :
      repr.population_treated_effect_numerator =
        ∫ sample, populationTreatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      repr.population_treated_mass =
        ∫ sample, populationTreatedMass sample ∂sampleLaw)
    (hcondNumerator :
      sampleLaw[populationTreatedEffectNumerator | scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore samplePropensityScore
              sampleControlPrognosticScore sample))
    (hcondMass :
      sampleLaw[populationTreatedMass | scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore samplePropensityScore
              sampleControlPrognosticScore sample)) :
    weightedSampleMeanContrast targetSample baseWeight treatedTargetOutcome
          targetControlOutcome =
        pattWeightedMeanContrast targetSample selectedSample baseWeight
          (prospectiveInverseSamplingWeight baseWeight
            (pattDoubleScore unitPropensityScore unitControlPrognosticScore)
            samplingMass)
          treatedTargetOutcome selectedControlOutcome ∧
      repr.selectedHajekPATT =
        (∫ sample,
            scoreEffectCellValue
              (pattDoubleScore samplePropensityScore
                sampleControlPrognosticScore sample)
            ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore samplePropensityScore
                sampleControlPrognosticScore sample)
            ∂sampleLaw) :=
  prospectivePATTDoubleScore_finite_recovery_and_population_identification
    (mSample := mSample) (scoreSigma := scoreSigma)
    (sampleLaw := sampleLaw) hsub targetSample selectedSample Finset.univ
    baseWeight treatedTargetOutcome targetControlOutcome
    selectedControlOutcome unitPropensityScore unitControlPrognosticScore
    treatment samplingMass controlValue repr hpopulationSampling
    hpopulationTreatedMass samplePropensityScore
    sampleControlPrognosticScore populationTreatedEffectNumerator
    populationTreatedMass scoreEffectCellValue scoreTreatedMassCellValue
    (fun _unit _hunit => by simp)
    (fun _unit _hunit => by simp)
    (fun cell _hcell => hmassTarget cell)
    (fun cell _hcell => hfiniteSampling cell)
    (fun cell _hcell => hfiniteTreatedMass cell)
    (fun cell _hcell => hfiniteControlMass cell)
    hscoreMeasTargetC hscoreMeasSelectedC hreprNumerator hreprMass
    hcondNumerator hcondMass

/--
Paired retrospective PATE/PATT finite recovery and conditional population
identification over finite double-score alphabets.
-/
theorem retrospectivePATE_PATTDoubleScore_finite_recovery_and_population_identification_fintype
    [Fintype ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [Fintype (PropensityCell × PATTProgCell)]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateTargetSample pateSelectedSample pattTargetSample pattSelectedSample :
      Finset Unit)
    (pateBaseWeight pattBaseWeight : Unit -> Real)
    (pateTargetOutcomeT pateTargetOutcomeC pateSelectedOutcomeT
      pateSelectedOutcomeC pattTreatedTargetOutcome pattTargetControlOutcome
      pattSelectedControlOutcome : Unit -> Real)
    (unitPropensityScore : Unit -> PropensityCell)
    (unitTreatedPrognosticScore : Unit -> TreatedProgCell)
    (unitControlPrognosticScore : Unit -> ControlProgCell)
    (unitPATTControlPrognosticScore : Unit -> PATTProgCell)
    (treatment : Unit -> Prop) [DecidablePred treatment]
    (pateSamplingIfTreated pateSamplingIfControl :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (pattSamplingIfTreated pattSamplingIfControl :
      PropensityCell × PATTProgCell -> Real)
    (pateTreatedValue : TreatedProgCell -> Real)
    (pateControlValue : ControlProgCell -> Real)
    (pattControlValue : PATTProgCell -> Real)
    (pateRepr : PATERepresentation)
    (hpateTreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hpateControlSampling : pateRepr.control.sampling_mass ≠ 0)
    (pattRepr : PATTRepresentation)
    (hpattPopulationSampling : pattRepr.sampling_mass ≠ 0)
    (hpattPopulationTreatedMass : pattRepr.population_treated_mass ≠ 0)
    (samplePropensityScore : Sample -> PropensityCell)
    (sampleTreatedPrognosticScore : Sample -> TreatedProgCell)
    (sampleControlPrognosticScore : Sample -> ControlProgCell)
    (samplePATTControlPrognosticScore : Sample -> PATTProgCell)
    (populationTreatedOutcome populationControlOutcome : Sample -> Real)
    (populationTreatedEffectNumerator populationTreatedMass : Sample -> Real)
    (populationTreatedValue : TreatedProgCell -> Real)
    (populationControlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpateMassTarget :
      ∀ cell,
        scoreCellMass pateTargetSample pateBaseWeight
          (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
            unitControlPrognosticScore) cell ≠ 0)
    (hpattMassTarget :
      ∀ cell,
        scoreCellMass pattTargetSample pattBaseWeight
          (pattDoubleScore unitPropensityScore
            unitPATTControlPrognosticScore) cell ≠ 0)
    (hpateSamplingTreated : ∀ cell, pateSamplingIfTreated cell ≠ 0)
    (hpateSamplingControl : ∀ cell, pateSamplingIfControl cell ≠ 0)
    (hpattSamplingTreated : ∀ cell, pattSamplingIfTreated cell ≠ 0)
    (hpattSamplingControl : ∀ cell, pattSamplingIfControl cell ≠ 0)
    (hpateTreatedMass :
      ∀ cell,
        scoreCellMass (pateSelectedSample.filter treatment) pateBaseWeight
            (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
              unitControlPrognosticScore) cell =
          pateSamplingIfTreated cell *
            scoreCellMass (pateTargetSample.filter treatment) pateBaseWeight
              (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
                unitControlPrognosticScore) cell)
    (hpateControlMass :
      ∀ cell,
        scoreCellMass
            (pateSelectedSample.filter (fun unit => ¬ treatment unit))
            pateBaseWeight
            (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
              unitControlPrognosticScore) cell =
          pateSamplingIfControl cell *
            scoreCellMass
              (pateTargetSample.filter (fun unit => ¬ treatment unit))
              pateBaseWeight
              (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
                unitControlPrognosticScore) cell)
    (hpattFiniteTreatedMass :
      ∀ cell,
        scoreCellMass (pattSelectedSample.filter treatment) pattBaseWeight
            (pattDoubleScore unitPropensityScore
              unitPATTControlPrognosticScore) cell =
          pattSamplingIfTreated cell *
            scoreCellMass (pattTargetSample.filter treatment) pattBaseWeight
              (pattDoubleScore unitPropensityScore
                unitPATTControlPrognosticScore) cell)
    (hpattFiniteControlMass :
      ∀ cell,
        scoreCellMass
            (pattSelectedSample.filter (fun unit => ¬ treatment unit))
            pattBaseWeight
            (pattDoubleScore unitPropensityScore
              unitPATTControlPrognosticScore) cell =
          pattSamplingIfControl cell *
            scoreCellMass
              (pattTargetSample.filter (fun unit => ¬ treatment unit))
              pattBaseWeight
              (pattDoubleScore unitPropensityScore
                unitPATTControlPrognosticScore) cell)
    (hpateScoreMeasTargetT :
      ∀ unit, unit ∈ pateTargetSample ->
        pateTargetOutcomeT unit =
          pateTreatedValue (unitTreatedPrognosticScore unit))
    (hpateScoreMeasSelectedT :
      ∀ unit, unit ∈ pateSelectedSample ->
        pateSelectedOutcomeT unit =
          pateTreatedValue (unitTreatedPrognosticScore unit))
    (hpateScoreMeasTargetC :
      ∀ unit, unit ∈ pateTargetSample ->
        pateTargetOutcomeC unit =
          pateControlValue (unitControlPrognosticScore unit))
    (hpateScoreMeasSelectedC :
      ∀ unit, unit ∈ pateSelectedSample ->
        pateSelectedOutcomeC unit =
          pateControlValue (unitControlPrognosticScore unit))
    (hpattScoreMeasTargetC :
      ∀ unit, unit ∈ pattTargetSample ->
        pattTargetControlOutcome unit =
          pattControlValue (unitPATTControlPrognosticScore unit))
    (hpattScoreMeasSelectedC :
      ∀ unit, unit ∈ pattSelectedSample ->
        pattSelectedControlOutcome unit =
          pattControlValue (unitPATTControlPrognosticScore unit))
    (hpateReprT :
      pateRepr.treated.population_target =
        ∫ sample, populationTreatedOutcome sample ∂sampleLaw)
    (hpateReprC :
      pateRepr.control.population_target =
        ∫ sample, populationControlOutcome sample ∂sampleLaw)
    (hpattReprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, populationTreatedEffectNumerator sample ∂sampleLaw)
    (hpattReprMass :
      pattRepr.population_treated_mass =
        ∫ sample, populationTreatedMass sample ∂sampleLaw)
    (hpateCondT :
      sampleLaw[populationTreatedOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => populationTreatedValue
          (sampleTreatedPrognosticScore sample))
    (hpateCondC :
      sampleLaw[populationControlOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => populationControlValue
          (sampleControlPrognosticScore sample))
    (hpattCondNumerator :
      sampleLaw[populationTreatedEffectNumerator | scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore samplePropensityScore
              samplePATTControlPrognosticScore sample))
    (hpattCondMass :
      sampleLaw[populationTreatedMass | scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore samplePropensityScore
              samplePATTControlPrognosticScore sample)) :
    (weightedSampleMeanContrast pateTargetSample pateBaseWeight
          pateTargetOutcomeT pateTargetOutcomeC =
        weightedSampleMeanContrast pateSelectedSample
          (retrospectiveInverseSamplingWeight pateBaseWeight
            (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
              unitControlPrognosticScore)
            treatment pateSamplingIfTreated pateSamplingIfControl)
          pateSelectedOutcomeT pateSelectedOutcomeC ∧
      pateRepr.selectedHajekPATE =
        (∫ sample,
            populationTreatedValue (sampleTreatedPrognosticScore sample)
            ∂sampleLaw) -
          (∫ sample,
            populationControlValue (sampleControlPrognosticScore sample)
            ∂sampleLaw)) ∧
      (weightedSampleMeanContrast pattTargetSample pattBaseWeight
          pattTreatedTargetOutcome pattTargetControlOutcome =
        pattWeightedMeanContrast pattTargetSample pattSelectedSample
          pattBaseWeight
          (retrospectiveInverseSamplingWeight pattBaseWeight
            (pattDoubleScore unitPropensityScore
              unitPATTControlPrognosticScore)
            treatment pattSamplingIfTreated pattSamplingIfControl)
          pattTreatedTargetOutcome pattSelectedControlOutcome ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
            scoreEffectCellValue
              (pattDoubleScore samplePropensityScore
                samplePATTControlPrognosticScore sample)
            ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore samplePropensityScore
                samplePATTControlPrognosticScore sample)
            ∂sampleLaw)) := by
  constructor
  · exact
      retrospectivePATEDoubleScore_finite_recovery_and_population_identification_fintype
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pateTargetSample pateSelectedSample
        pateBaseWeight pateTargetOutcomeT pateTargetOutcomeC
        pateSelectedOutcomeT pateSelectedOutcomeC unitPropensityScore
        unitTreatedPrognosticScore unitControlPrognosticScore treatment
        pateSamplingIfTreated pateSamplingIfControl pateTreatedValue
        pateControlValue pateRepr hpateTreatedSampling hpateControlSampling
        samplePropensityScore sampleTreatedPrognosticScore
        sampleControlPrognosticScore populationTreatedOutcome
        populationControlOutcome populationTreatedValue populationControlValue
        hpateMassTarget hpateSamplingTreated hpateSamplingControl
        hpateTreatedMass hpateControlMass hpateScoreMeasTargetT
        hpateScoreMeasSelectedT hpateScoreMeasTargetC
        hpateScoreMeasSelectedC hpateReprT hpateReprC hpateCondT
        hpateCondC
  · exact
      retrospectivePATTDoubleScore_finite_recovery_and_population_identification_fintype
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pattTargetSample pattSelectedSample
        pattBaseWeight pattTreatedTargetOutcome pattTargetControlOutcome
        pattSelectedControlOutcome unitPropensityScore
        unitPATTControlPrognosticScore treatment pattSamplingIfTreated
        pattSamplingIfControl pattControlValue pattRepr
        hpattPopulationSampling hpattPopulationTreatedMass
        samplePropensityScore samplePATTControlPrognosticScore
        populationTreatedEffectNumerator populationTreatedMass
        scoreEffectCellValue scoreTreatedMassCellValue hpattMassTarget
        hpattSamplingTreated hpattSamplingControl hpattFiniteTreatedMass
        hpattFiniteControlMass hpattScoreMeasTargetC hpattScoreMeasSelectedC
        hpattReprNumerator hpattReprMass hpattCondNumerator hpattCondMass

/--
Paired prospective PATE/PATT finite recovery and conditional population
identification over finite double-score alphabets.
-/
theorem prospectivePATE_PATTDoubleScore_finite_recovery_and_population_identification_fintype
    [Fintype ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [Fintype (PropensityCell × PATTProgCell)]
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateTargetSample pateSelectedSample pattTargetSample pattSelectedSample :
      Finset Unit)
    (pateBaseWeight pattBaseWeight : Unit -> Real)
    (pateTargetOutcomeT pateTargetOutcomeC pateSelectedOutcomeT
      pateSelectedOutcomeC pattTreatedTargetOutcome pattTargetControlOutcome
      pattSelectedControlOutcome : Unit -> Real)
    (unitPropensityScore : Unit -> PropensityCell)
    (unitTreatedPrognosticScore : Unit -> TreatedProgCell)
    (unitControlPrognosticScore : Unit -> ControlProgCell)
    (unitPATTControlPrognosticScore : Unit -> PATTProgCell)
    (treatment : Unit -> Prop) [DecidablePred treatment]
    (pateSamplingMass :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (pattSamplingMass : PropensityCell × PATTProgCell -> Real)
    (pateTreatedValue : TreatedProgCell -> Real)
    (pateControlValue : ControlProgCell -> Real)
    (pattControlValue : PATTProgCell -> Real)
    (pateRepr : PATERepresentation)
    (hpateTreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hpateControlSampling : pateRepr.control.sampling_mass ≠ 0)
    (pattRepr : PATTRepresentation)
    (hpattPopulationSampling : pattRepr.sampling_mass ≠ 0)
    (hpattPopulationTreatedMass : pattRepr.population_treated_mass ≠ 0)
    (samplePropensityScore : Sample -> PropensityCell)
    (sampleTreatedPrognosticScore : Sample -> TreatedProgCell)
    (sampleControlPrognosticScore : Sample -> ControlProgCell)
    (samplePATTControlPrognosticScore : Sample -> PATTProgCell)
    (populationTreatedOutcome populationControlOutcome : Sample -> Real)
    (populationTreatedEffectNumerator populationTreatedMass : Sample -> Real)
    (populationTreatedValue : TreatedProgCell -> Real)
    (populationControlValue : ControlProgCell -> Real)
    (scoreEffectCellValue scoreTreatedMassCellValue :
      PropensityCell × PATTProgCell -> Real)
    (hpateMassTarget :
      ∀ cell,
        scoreCellMass pateTargetSample pateBaseWeight
          (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
            unitControlPrognosticScore) cell ≠ 0)
    (hpattMassTarget :
      ∀ cell,
        scoreCellMass pattTargetSample pattBaseWeight
          (pattDoubleScore unitPropensityScore
            unitPATTControlPrognosticScore) cell ≠ 0)
    (hpateSampling : ∀ cell, pateSamplingMass cell ≠ 0)
    (hpattSampling : ∀ cell, pattSamplingMass cell ≠ 0)
    (hpateTreatedMass :
      ∀ cell,
        scoreCellMass (pateSelectedSample.filter treatment) pateBaseWeight
            (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
              unitControlPrognosticScore) cell =
          pateSamplingMass cell *
            scoreCellMass (pateTargetSample.filter treatment) pateBaseWeight
              (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
                unitControlPrognosticScore) cell)
    (hpateControlMass :
      ∀ cell,
        scoreCellMass
            (pateSelectedSample.filter (fun unit => ¬ treatment unit))
            pateBaseWeight
            (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
              unitControlPrognosticScore) cell =
          pateSamplingMass cell *
            scoreCellMass
              (pateTargetSample.filter (fun unit => ¬ treatment unit))
              pateBaseWeight
              (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
                unitControlPrognosticScore) cell)
    (hpattFiniteTreatedMass :
      ∀ cell,
        scoreCellMass (pattSelectedSample.filter treatment) pattBaseWeight
            (pattDoubleScore unitPropensityScore
              unitPATTControlPrognosticScore) cell =
          pattSamplingMass cell *
            scoreCellMass (pattTargetSample.filter treatment) pattBaseWeight
              (pattDoubleScore unitPropensityScore
                unitPATTControlPrognosticScore) cell)
    (hpattFiniteControlMass :
      ∀ cell,
        scoreCellMass
            (pattSelectedSample.filter (fun unit => ¬ treatment unit))
            pattBaseWeight
            (pattDoubleScore unitPropensityScore
              unitPATTControlPrognosticScore) cell =
          pattSamplingMass cell *
            scoreCellMass
              (pattTargetSample.filter (fun unit => ¬ treatment unit))
              pattBaseWeight
              (pattDoubleScore unitPropensityScore
                unitPATTControlPrognosticScore) cell)
    (hpateScoreMeasTargetT :
      ∀ unit, unit ∈ pateTargetSample ->
        pateTargetOutcomeT unit =
          pateTreatedValue (unitTreatedPrognosticScore unit))
    (hpateScoreMeasSelectedT :
      ∀ unit, unit ∈ pateSelectedSample ->
        pateSelectedOutcomeT unit =
          pateTreatedValue (unitTreatedPrognosticScore unit))
    (hpateScoreMeasTargetC :
      ∀ unit, unit ∈ pateTargetSample ->
        pateTargetOutcomeC unit =
          pateControlValue (unitControlPrognosticScore unit))
    (hpateScoreMeasSelectedC :
      ∀ unit, unit ∈ pateSelectedSample ->
        pateSelectedOutcomeC unit =
          pateControlValue (unitControlPrognosticScore unit))
    (hpattScoreMeasTargetC :
      ∀ unit, unit ∈ pattTargetSample ->
        pattTargetControlOutcome unit =
          pattControlValue (unitPATTControlPrognosticScore unit))
    (hpattScoreMeasSelectedC :
      ∀ unit, unit ∈ pattSelectedSample ->
        pattSelectedControlOutcome unit =
          pattControlValue (unitPATTControlPrognosticScore unit))
    (hpateReprT :
      pateRepr.treated.population_target =
        ∫ sample, populationTreatedOutcome sample ∂sampleLaw)
    (hpateReprC :
      pateRepr.control.population_target =
        ∫ sample, populationControlOutcome sample ∂sampleLaw)
    (hpattReprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, populationTreatedEffectNumerator sample ∂sampleLaw)
    (hpattReprMass :
      pattRepr.population_treated_mass =
        ∫ sample, populationTreatedMass sample ∂sampleLaw)
    (hpateCondT :
      sampleLaw[populationTreatedOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => populationTreatedValue
          (sampleTreatedPrognosticScore sample))
    (hpateCondC :
      sampleLaw[populationControlOutcome | scoreSigma] =ᵐ[sampleLaw]
        fun sample => populationControlValue
          (sampleControlPrognosticScore sample))
    (hpattCondNumerator :
      sampleLaw[populationTreatedEffectNumerator | scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore samplePropensityScore
              samplePATTControlPrognosticScore sample))
    (hpattCondMass :
      sampleLaw[populationTreatedMass | scoreSigma] =ᵐ[sampleLaw]
        fun sample =>
          scoreTreatedMassCellValue
            (pattDoubleScore samplePropensityScore
              samplePATTControlPrognosticScore sample)) :
    (weightedSampleMeanContrast pateTargetSample pateBaseWeight
          pateTargetOutcomeT pateTargetOutcomeC =
        weightedSampleMeanContrast pateSelectedSample
          (prospectiveInverseSamplingWeight pateBaseWeight
            (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
              unitControlPrognosticScore)
            pateSamplingMass)
          pateSelectedOutcomeT pateSelectedOutcomeC ∧
      pateRepr.selectedHajekPATE =
        (∫ sample,
            populationTreatedValue (sampleTreatedPrognosticScore sample)
            ∂sampleLaw) -
          (∫ sample,
            populationControlValue (sampleControlPrognosticScore sample)
            ∂sampleLaw)) ∧
      (weightedSampleMeanContrast pattTargetSample pattBaseWeight
          pattTreatedTargetOutcome pattTargetControlOutcome =
        pattWeightedMeanContrast pattTargetSample pattSelectedSample
          pattBaseWeight
          (prospectiveInverseSamplingWeight pattBaseWeight
            (pattDoubleScore unitPropensityScore
              unitPATTControlPrognosticScore)
            pattSamplingMass)
          pattTreatedTargetOutcome pattSelectedControlOutcome ∧
      pattRepr.selectedHajekPATT =
        (∫ sample,
            scoreEffectCellValue
              (pattDoubleScore samplePropensityScore
                samplePATTControlPrognosticScore sample)
            ∂sampleLaw) /
          (∫ sample,
            scoreTreatedMassCellValue
              (pattDoubleScore samplePropensityScore
                samplePATTControlPrognosticScore sample)
            ∂sampleLaw)) := by
  constructor
  · exact
      prospectivePATEDoubleScore_finite_recovery_and_population_identification_fintype
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pateTargetSample pateSelectedSample
        pateBaseWeight pateTargetOutcomeT pateTargetOutcomeC
        pateSelectedOutcomeT pateSelectedOutcomeC unitPropensityScore
        unitTreatedPrognosticScore unitControlPrognosticScore treatment
        pateSamplingMass pateTreatedValue pateControlValue pateRepr
        hpateTreatedSampling hpateControlSampling samplePropensityScore
        sampleTreatedPrognosticScore sampleControlPrognosticScore
        populationTreatedOutcome populationControlOutcome
        populationTreatedValue populationControlValue hpateMassTarget
        hpateSampling hpateTreatedMass hpateControlMass
        hpateScoreMeasTargetT hpateScoreMeasSelectedT
        hpateScoreMeasTargetC hpateScoreMeasSelectedC hpateReprT
        hpateReprC hpateCondT hpateCondC
  · exact
      prospectivePATTDoubleScore_finite_recovery_and_population_identification_fintype
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pattTargetSample pattSelectedSample
        pattBaseWeight pattTreatedTargetOutcome pattTargetControlOutcome
        pattSelectedControlOutcome unitPropensityScore
        unitPATTControlPrognosticScore treatment pattSamplingMass
        pattControlValue pattRepr hpattPopulationSampling
        hpattPopulationTreatedMass samplePropensityScore
        samplePATTControlPrognosticScore populationTreatedEffectNumerator
        populationTreatedMass scoreEffectCellValue scoreTreatedMassCellValue
        hpattMassTarget hpattSampling hpattFiniteTreatedMass
        hpattFiniteControlMass hpattScoreMeasTargetC hpattScoreMeasSelectedC
        hpattReprNumerator hpattReprMass hpattCondNumerator hpattCondMass

end WDSM
end Matching
end StatInference
