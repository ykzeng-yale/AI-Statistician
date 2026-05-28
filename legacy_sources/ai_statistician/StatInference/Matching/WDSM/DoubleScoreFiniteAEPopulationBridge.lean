import StatInference.Matching.WDSM.DoubleScoreFinitePopulationBridge

/-!
# Double-score finite estimator and finite-cell population bridge

This module packages the finite selected-sample double-score recovery theorems
with the finite-cell almost-everywhere population identification theorems.

Compared with `DoubleScoreFinitePopulationBridge`, the population side here is
stated through score-version almost-everywhere equalities plus finite score-cell
coverage and score measurability, rather than raw conditional-expectation
equalities.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open scoped MeasureTheory

variable {Unit Sample PropensityCell TreatedProgCell ControlProgCell : Type*}
variable {PATTProgCell : Type*}
variable [mSample : MeasurableSpace Sample]
variable {scoreSigma : MeasurableSpace Sample}
variable {sampleLaw : Measure[mSample] Sample}
variable [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
  [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]

/--
Retrospective PATE bridge with finite-cell population identification:
finite selected double-score inverse weighting recovers the target finite
contrast, while selected Hájek PATE is identified from double-score
almost-everywhere score versions under finite population score-cell coverage.
-/
theorem retrospectivePATEDoubleScore_finite_recovery_and_ae_population_identification
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [IsFiniteMeasure sampleLaw]
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
    (hfiniteTreatedMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (selectedSample.filter treatment) baseWeight
            (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
              unitControlPrognosticScore) cell =
          samplingIfTreated cell *
            scoreCellMass (targetSample.filter treatment) baseWeight
              (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
                unitControlPrognosticScore) cell)
    (hfiniteControlMass :
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
    (hpopulationScore :
      AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore samplePropensityScore sampleTreatedPrognosticScore
          sampleControlPrognosticScore) sampleLaw)
    (hcoverPopulation :
      ∀ᵐ sample ∂sampleLaw,
        pateDoubleScore samplePropensityScore sampleTreatedPrognosticScore
          sampleControlPrognosticScore sample ∈
          (cells : Set
            ((PropensityCell × TreatedProgCell) × ControlProgCell)))
    (htreatedAE :
      populationTreatedOutcome =ᵐ[sampleLaw]
        fun sample =>
          populationTreatedValue (sampleTreatedPrognosticScore sample))
    (hcontrolAE :
      populationControlOutcome =ᵐ[sampleLaw]
        fun sample =>
          populationControlValue (sampleControlPrognosticScore sample)) :
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
      hsamplingControl hfiniteTreatedMass hfiniteControlMass
      hscoreMeasTargetT hscoreMeasSelectedT hscoreMeasTargetC
      hscoreMeasSelectedC,
    selectedHajekPATE_eq_scorePATE_of_ae_pateDoubleScoreVersions_finset_abs_sum_bound
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub repr htreatedSampling hcontrolSampling
      cells samplePropensityScore sampleTreatedPrognosticScore
      sampleControlPrognosticScore populationTreatedOutcome
      populationControlOutcome populationTreatedValue populationControlValue
      hreprT hreprC hpopulationScore hcoverPopulation htreatedAE
      hcontrolAE⟩

/--
Prospective PATE bridge with finite-cell population identification.
-/
theorem prospectivePATEDoubleScore_finite_recovery_and_ae_population_identification
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [IsFiniteMeasure sampleLaw]
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
    (hfiniteSampling :
      ∀ cell, cell ∈ cells -> samplingMass cell ≠ 0)
    (hfiniteTreatedMass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (selectedSample.filter treatment) baseWeight
            (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
              unitControlPrognosticScore) cell =
          samplingMass cell *
            scoreCellMass (targetSample.filter treatment) baseWeight
              (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
                unitControlPrognosticScore) cell)
    (hfiniteControlMass :
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
    (hpopulationScore :
      AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore samplePropensityScore sampleTreatedPrognosticScore
          sampleControlPrognosticScore) sampleLaw)
    (hcoverPopulation :
      ∀ᵐ sample ∂sampleLaw,
        pateDoubleScore samplePropensityScore sampleTreatedPrognosticScore
          sampleControlPrognosticScore sample ∈
          (cells : Set
            ((PropensityCell × TreatedProgCell) × ControlProgCell)))
    (htreatedAE :
      populationTreatedOutcome =ᵐ[sampleLaw]
        fun sample =>
          populationTreatedValue (sampleTreatedPrognosticScore sample))
    (hcontrolAE :
      populationControlOutcome =ᵐ[sampleLaw]
        fun sample =>
          populationControlValue (sampleControlPrognosticScore sample)) :
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
      hmassTarget hfiniteSampling hfiniteTreatedMass hfiniteControlMass
      hscoreMeasTargetT hscoreMeasSelectedT hscoreMeasTargetC
      hscoreMeasSelectedC,
    selectedHajekPATE_eq_scorePATE_of_ae_pateDoubleScoreVersions_finset_abs_sum_bound
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub repr htreatedSampling hcontrolSampling
      cells samplePropensityScore sampleTreatedPrognosticScore
      sampleControlPrognosticScore populationTreatedOutcome
      populationControlOutcome populationTreatedValue populationControlValue
      hreprT hreprC hpopulationScore hcoverPopulation htreatedAE
      hcontrolAE⟩

/--
Retrospective PATT bridge with finite-cell population identification.
-/
theorem retrospectivePATTDoubleScore_finite_recovery_and_ae_population_identification
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    [IsFiniteMeasure sampleLaw]
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
    (hpopulationScore :
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore samplePropensityScore sampleControlPrognosticScore)
        sampleLaw)
    (hcoverPopulation :
      ∀ᵐ sample ∂sampleLaw,
        pattDoubleScore samplePropensityScore sampleControlPrognosticScore
          sample ∈ (cells : Set (PropensityCell × PATTProgCell)))
    (hnumeratorAE :
      populationTreatedEffectNumerator =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore samplePropensityScore
              sampleControlPrognosticScore sample))
    (hmassAE :
      populationTreatedMass =ᵐ[sampleLaw]
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
    selectedHajekPATT_eq_scorePATT_of_ae_pattDoubleScoreVersions_finset_abs_sum_bound
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub repr hpopulationSampling
      hpopulationTreatedMass cells samplePropensityScore
      sampleControlPrognosticScore populationTreatedEffectNumerator
      populationTreatedMass scoreEffectCellValue scoreTreatedMassCellValue
      hreprNumerator hreprMass hpopulationScore hcoverPopulation
      hnumeratorAE hmassAE⟩

/--
Prospective PATT bridge with finite-cell population identification.
-/
theorem prospectivePATTDoubleScore_finite_recovery_and_ae_population_identification
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    [IsFiniteMeasure sampleLaw]
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
    (hpopulationScore :
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore samplePropensityScore sampleControlPrognosticScore)
        sampleLaw)
    (hcoverPopulation :
      ∀ᵐ sample ∂sampleLaw,
        pattDoubleScore samplePropensityScore sampleControlPrognosticScore
          sample ∈ (cells : Set (PropensityCell × PATTProgCell)))
    (hnumeratorAE :
      populationTreatedEffectNumerator =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore samplePropensityScore
              sampleControlPrognosticScore sample))
    (hmassAE :
      populationTreatedMass =ᵐ[sampleLaw]
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
    selectedHajekPATT_eq_scorePATT_of_ae_pattDoubleScoreVersions_finset_abs_sum_bound
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub repr hpopulationSampling
      hpopulationTreatedMass cells samplePropensityScore
      sampleControlPrognosticScore populationTreatedEffectNumerator
      populationTreatedMass scoreEffectCellValue scoreTreatedMassCellValue
      hreprNumerator hreprMass hpopulationScore hcoverPopulation
      hnumeratorAE hmassAE⟩

/--
Paired retrospective PATE/PATT bridge with finite-cell almost-everywhere
population identification.
-/
theorem retrospectivePATE_PATTDoubleScore_finite_recovery_and_ae_population_identification
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    [IsFiniteMeasure sampleLaw]
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
    (hpateFiniteTreatedMass :
      ∀ cell, cell ∈ pateCells ->
        scoreCellMass (pateSelectedSample.filter treatment) pateBaseWeight
            (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
              unitControlPrognosticScore) cell =
          pateSamplingIfTreated cell *
            scoreCellMass (pateTargetSample.filter treatment) pateBaseWeight
              (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
                unitControlPrognosticScore) cell)
    (hpateFiniteControlMass :
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
    (hpatePopulationScore :
      AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore samplePropensityScore sampleTreatedPrognosticScore
          sampleControlPrognosticScore) sampleLaw)
    (hpateCoverPopulation :
      ∀ᵐ sample ∂sampleLaw,
        pateDoubleScore samplePropensityScore sampleTreatedPrognosticScore
          sampleControlPrognosticScore sample ∈
          (pateCells : Set
            ((PropensityCell × TreatedProgCell) × ControlProgCell)))
    (hpattPopulationScore :
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore samplePropensityScore
          samplePATTControlPrognosticScore) sampleLaw)
    (hpattCoverPopulation :
      ∀ᵐ sample ∂sampleLaw,
        pattDoubleScore samplePropensityScore samplePATTControlPrognosticScore
          sample ∈ (pattCells : Set (PropensityCell × PATTProgCell)))
    (hpateTreatedAE :
      populationTreatedOutcome =ᵐ[sampleLaw]
        fun sample =>
          populationTreatedValue (sampleTreatedPrognosticScore sample))
    (hpateControlAE :
      populationControlOutcome =ᵐ[sampleLaw]
        fun sample =>
          populationControlValue (sampleControlPrognosticScore sample))
    (hpattNumeratorAE :
      populationTreatedEffectNumerator =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore samplePropensityScore
              samplePATTControlPrognosticScore sample))
    (hpattMassAE :
      populationTreatedMass =ᵐ[sampleLaw]
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
      retrospectivePATEDoubleScore_finite_recovery_and_ae_population_identification
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
        hpateSamplingTreated hpateSamplingControl hpateFiniteTreatedMass
        hpateFiniteControlMass hpateScoreMeasTargetT hpateScoreMeasSelectedT
        hpateScoreMeasTargetC hpateScoreMeasSelectedC hpateReprT
        hpateReprC hpatePopulationScore hpateCoverPopulation
        hpateTreatedAE hpateControlAE
  · exact
      retrospectivePATTDoubleScore_finite_recovery_and_ae_population_identification
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
        hpattReprMass hpattPopulationScore hpattCoverPopulation
        hpattNumeratorAE hpattMassAE

/--
Paired prospective PATE/PATT bridge with finite-cell almost-everywhere
population identification.
-/
theorem prospectivePATE_PATTDoubleScore_finite_recovery_and_ae_population_identification
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    [IsFiniteMeasure sampleLaw]
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
    (hpateFiniteTreatedMass :
      ∀ cell, cell ∈ pateCells ->
        scoreCellMass (pateSelectedSample.filter treatment) pateBaseWeight
            (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
              unitControlPrognosticScore) cell =
          pateSamplingMass cell *
            scoreCellMass (pateTargetSample.filter treatment) pateBaseWeight
              (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
                unitControlPrognosticScore) cell)
    (hpateFiniteControlMass :
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
    (hpatePopulationScore :
      AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore samplePropensityScore sampleTreatedPrognosticScore
          sampleControlPrognosticScore) sampleLaw)
    (hpateCoverPopulation :
      ∀ᵐ sample ∂sampleLaw,
        pateDoubleScore samplePropensityScore sampleTreatedPrognosticScore
          sampleControlPrognosticScore sample ∈
          (pateCells : Set
            ((PropensityCell × TreatedProgCell) × ControlProgCell)))
    (hpattPopulationScore :
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore samplePropensityScore
          samplePATTControlPrognosticScore) sampleLaw)
    (hpattCoverPopulation :
      ∀ᵐ sample ∂sampleLaw,
        pattDoubleScore samplePropensityScore samplePATTControlPrognosticScore
          sample ∈ (pattCells : Set (PropensityCell × PATTProgCell)))
    (hpateTreatedAE :
      populationTreatedOutcome =ᵐ[sampleLaw]
        fun sample =>
          populationTreatedValue (sampleTreatedPrognosticScore sample))
    (hpateControlAE :
      populationControlOutcome =ᵐ[sampleLaw]
        fun sample =>
          populationControlValue (sampleControlPrognosticScore sample))
    (hpattNumeratorAE :
      populationTreatedEffectNumerator =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore samplePropensityScore
              samplePATTControlPrognosticScore sample))
    (hpattMassAE :
      populationTreatedMass =ᵐ[sampleLaw]
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
      prospectivePATEDoubleScore_finite_recovery_and_ae_population_identification
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
        hpateCoverSelected hpateMassTarget hpateSampling
        hpateFiniteTreatedMass hpateFiniteControlMass hpateScoreMeasTargetT
        hpateScoreMeasSelectedT hpateScoreMeasTargetC
        hpateScoreMeasSelectedC hpateReprT hpateReprC hpatePopulationScore
        hpateCoverPopulation hpateTreatedAE hpateControlAE
  · exact
      prospectivePATTDoubleScore_finite_recovery_and_ae_population_identification
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
        hpattPopulationScore hpattCoverPopulation hpattNumeratorAE
        hpattMassAE

/--
Retrospective PATE finite recovery and a.e. population identification over a
finite double-score alphabet, with finite coverage specialized to
`Finset.univ`.
-/
theorem retrospectivePATEDoubleScore_finite_recovery_and_ae_population_identification_fintype
    [Fintype ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [IsFiniteMeasure sampleLaw]
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
    (hfiniteTreatedMass :
      ∀ cell,
        scoreCellMass (selectedSample.filter treatment) baseWeight
            (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
              unitControlPrognosticScore) cell =
          samplingIfTreated cell *
            scoreCellMass (targetSample.filter treatment) baseWeight
              (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
                unitControlPrognosticScore) cell)
    (hfiniteControlMass :
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
    (hpopulationScore :
      AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore samplePropensityScore sampleTreatedPrognosticScore
          sampleControlPrognosticScore) sampleLaw)
    (htreatedAE :
      populationTreatedOutcome =ᵐ[sampleLaw]
        fun sample =>
          populationTreatedValue (sampleTreatedPrognosticScore sample))
    (hcontrolAE :
      populationControlOutcome =ᵐ[sampleLaw]
        fun sample =>
          populationControlValue (sampleControlPrognosticScore sample)) :
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
  retrospectivePATEDoubleScore_finite_recovery_and_ae_population_identification
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
    (fun cell _hcell => hfiniteTreatedMass cell)
    (fun cell _hcell => hfiniteControlMass cell)
    hscoreMeasTargetT hscoreMeasSelectedT hscoreMeasTargetC
    hscoreMeasSelectedC hreprT hreprC hpopulationScore
    (Filter.Eventually.of_forall (fun sample => by simp)) htreatedAE
    hcontrolAE

/--
Prospective PATE finite recovery and a.e. population identification over a
finite double-score alphabet, with finite coverage specialized to
`Finset.univ`.
-/
theorem prospectivePATEDoubleScore_finite_recovery_and_ae_population_identification_fintype
    [Fintype ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [IsFiniteMeasure sampleLaw]
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
    (hfiniteSampling : ∀ cell, samplingMass cell ≠ 0)
    (hfiniteTreatedMass :
      ∀ cell,
        scoreCellMass (selectedSample.filter treatment) baseWeight
            (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
              unitControlPrognosticScore) cell =
          samplingMass cell *
            scoreCellMass (targetSample.filter treatment) baseWeight
              (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
                unitControlPrognosticScore) cell)
    (hfiniteControlMass :
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
    (hpopulationScore :
      AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore samplePropensityScore sampleTreatedPrognosticScore
          sampleControlPrognosticScore) sampleLaw)
    (htreatedAE :
      populationTreatedOutcome =ᵐ[sampleLaw]
        fun sample =>
          populationTreatedValue (sampleTreatedPrognosticScore sample))
    (hcontrolAE :
      populationControlOutcome =ᵐ[sampleLaw]
        fun sample =>
          populationControlValue (sampleControlPrognosticScore sample)) :
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
  prospectivePATEDoubleScore_finite_recovery_and_ae_population_identification
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
    (fun cell _hcell => hfiniteSampling cell)
    (fun cell _hcell => hfiniteTreatedMass cell)
    (fun cell _hcell => hfiniteControlMass cell)
    hscoreMeasTargetT hscoreMeasSelectedT hscoreMeasTargetC
    hscoreMeasSelectedC hreprT hreprC hpopulationScore
    (Filter.Eventually.of_forall (fun sample => by simp)) htreatedAE
    hcontrolAE

/--
Retrospective PATT finite recovery and a.e. population identification over a
finite double-score alphabet, with finite coverage specialized to
`Finset.univ`.
-/
theorem retrospectivePATTDoubleScore_finite_recovery_and_ae_population_identification_fintype
    [Fintype (PropensityCell × PATTProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    [IsFiniteMeasure sampleLaw]
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
    (hpopulationScore :
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore samplePropensityScore sampleControlPrognosticScore)
        sampleLaw)
    (hnumeratorAE :
      populationTreatedEffectNumerator =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore samplePropensityScore
              sampleControlPrognosticScore sample))
    (hmassAE :
      populationTreatedMass =ᵐ[sampleLaw]
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
  retrospectivePATTDoubleScore_finite_recovery_and_ae_population_identification
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
    hpopulationScore (Filter.Eventually.of_forall (fun sample => by simp))
    hnumeratorAE hmassAE

/--
Prospective PATT finite recovery and a.e. population identification over a
finite double-score alphabet, with finite coverage specialized to
`Finset.univ`.
-/
theorem prospectivePATTDoubleScore_finite_recovery_and_ae_population_identification_fintype
    [Fintype (PropensityCell × PATTProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    [IsFiniteMeasure sampleLaw]
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
    (hpopulationScore :
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore samplePropensityScore sampleControlPrognosticScore)
        sampleLaw)
    (hnumeratorAE :
      populationTreatedEffectNumerator =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore samplePropensityScore
              sampleControlPrognosticScore sample))
    (hmassAE :
      populationTreatedMass =ᵐ[sampleLaw]
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
  prospectivePATTDoubleScore_finite_recovery_and_ae_population_identification
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
    hpopulationScore (Filter.Eventually.of_forall (fun sample => by simp))
    hnumeratorAE hmassAE

/--
Paired retrospective PATE/PATT finite recovery and a.e. population
identification over finite double-score alphabets.
-/
theorem retrospectivePATE_PATTDoubleScore_finite_recovery_and_ae_population_identification_fintype
    [Fintype ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [Fintype (PropensityCell × PATTProgCell)]
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    [IsFiniteMeasure sampleLaw]
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
    (hpateFiniteTreatedMass :
      ∀ cell,
        scoreCellMass (pateSelectedSample.filter treatment) pateBaseWeight
            (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
              unitControlPrognosticScore) cell =
          pateSamplingIfTreated cell *
            scoreCellMass (pateTargetSample.filter treatment) pateBaseWeight
              (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
                unitControlPrognosticScore) cell)
    (hpateFiniteControlMass :
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
    (hpatePopulationScore :
      AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore samplePropensityScore sampleTreatedPrognosticScore
          sampleControlPrognosticScore) sampleLaw)
    (hpattPopulationScore :
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore samplePropensityScore
          samplePATTControlPrognosticScore) sampleLaw)
    (hpateTreatedAE :
      populationTreatedOutcome =ᵐ[sampleLaw]
        fun sample =>
          populationTreatedValue (sampleTreatedPrognosticScore sample))
    (hpateControlAE :
      populationControlOutcome =ᵐ[sampleLaw]
        fun sample =>
          populationControlValue (sampleControlPrognosticScore sample))
    (hpattNumeratorAE :
      populationTreatedEffectNumerator =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore samplePropensityScore
              samplePATTControlPrognosticScore sample))
    (hpattMassAE :
      populationTreatedMass =ᵐ[sampleLaw]
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
      retrospectivePATEDoubleScore_finite_recovery_and_ae_population_identification_fintype
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
        hpateFiniteTreatedMass hpateFiniteControlMass hpateScoreMeasTargetT
        hpateScoreMeasSelectedT hpateScoreMeasTargetC
        hpateScoreMeasSelectedC hpateReprT hpateReprC hpatePopulationScore
        hpateTreatedAE hpateControlAE
  · exact
      retrospectivePATTDoubleScore_finite_recovery_and_ae_population_identification_fintype
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
        hpattReprNumerator hpattReprMass hpattPopulationScore
        hpattNumeratorAE hpattMassAE

/--
Paired prospective PATE/PATT finite recovery and a.e. population
identification over finite double-score alphabets.
-/
theorem prospectivePATE_PATTDoubleScore_finite_recovery_and_ae_population_identification_fintype
    [Fintype ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [Fintype (PropensityCell × PATTProgCell)]
    [TopologicalSpace ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [DiscreteTopology ((PropensityCell × TreatedProgCell) × ControlProgCell)]
    [TopologicalSpace (PropensityCell × PATTProgCell)]
    [DiscreteTopology (PropensityCell × PATTProgCell)]
    [IsFiniteMeasure sampleLaw]
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
    (hpateFiniteTreatedMass :
      ∀ cell,
        scoreCellMass (pateSelectedSample.filter treatment) pateBaseWeight
            (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
              unitControlPrognosticScore) cell =
          pateSamplingMass cell *
            scoreCellMass (pateTargetSample.filter treatment) pateBaseWeight
              (pateDoubleScore unitPropensityScore unitTreatedPrognosticScore
                unitControlPrognosticScore) cell)
    (hpateFiniteControlMass :
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
    (hpatePopulationScore :
      AEStronglyMeasurable[scoreSigma]
        (pateDoubleScore samplePropensityScore sampleTreatedPrognosticScore
          sampleControlPrognosticScore) sampleLaw)
    (hpattPopulationScore :
      AEStronglyMeasurable[scoreSigma]
        (pattDoubleScore samplePropensityScore
          samplePATTControlPrognosticScore) sampleLaw)
    (hpateTreatedAE :
      populationTreatedOutcome =ᵐ[sampleLaw]
        fun sample =>
          populationTreatedValue (sampleTreatedPrognosticScore sample))
    (hpateControlAE :
      populationControlOutcome =ᵐ[sampleLaw]
        fun sample =>
          populationControlValue (sampleControlPrognosticScore sample))
    (hpattNumeratorAE :
      populationTreatedEffectNumerator =ᵐ[sampleLaw]
        fun sample =>
          scoreEffectCellValue
            (pattDoubleScore samplePropensityScore
              samplePATTControlPrognosticScore sample))
    (hpattMassAE :
      populationTreatedMass =ᵐ[sampleLaw]
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
      prospectivePATEDoubleScore_finite_recovery_and_ae_population_identification_fintype
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
        hpateSampling hpateFiniteTreatedMass hpateFiniteControlMass
        hpateScoreMeasTargetT hpateScoreMeasSelectedT
        hpateScoreMeasTargetC hpateScoreMeasSelectedC hpateReprT
        hpateReprC hpatePopulationScore hpateTreatedAE hpateControlAE
  · exact
      prospectivePATTDoubleScore_finite_recovery_and_ae_population_identification_fintype
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
        hpattReprNumerator hpattReprMass hpattPopulationScore
        hpattNumeratorAE hpattMassAE

end WDSM
end Matching
end StatInference
