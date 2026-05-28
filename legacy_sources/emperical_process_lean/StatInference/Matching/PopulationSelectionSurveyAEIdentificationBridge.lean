import StatInference.Matching.WDSM.PopulationSurveyIdentificationBridge
import StatInference.Matching.WDSM.PopulationSurveySelectionDensity

/-!
# Population selection-density survey a.e. identification bridge

This module is the a.e.-score-version companion to
`PopulationSelectionSurveyIdentificationBridge`.  It composes primitive
selected-law tilting by a selection probability, inverse survey weighting, and
score-sigma measurable a.e. versions into raw selected-law survey-weighted
Hájek PATE/PATT identification formulas.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open scoped MeasureTheory ENNReal

variable {Sample : Type*} [mSample : MeasurableSpace Sample]
variable {scoreSigma : MeasurableSpace Sample}
variable {selectedLaw populationLaw : Measure[mSample] Sample}

/--
Selection-density PATE identification from a.e. score-space outcome versions.

The selected-law survey-weighted Hájek PATE equals the population-law
score-space PATE when each arm's selected law is a normalized
selection-probability tilt, survey weights invert the corresponding selection
probabilities, and the potential outcomes agree a.e. with score-sigma
measurable, integrable score versions.
-/
theorem selectedWeightedIntegralPATE_eq_scorePATE_of_selectionDensity_aeScoreVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (treatedSelectionProb treatedSurveyWeight
      controlSelectionProb controlSurveyWeight : Sample -> NNReal)
    (treatedOutcome controlOutcome
      treatedScoreVersion controlScoreVersion : Sample -> Real)
    (treatedSamplingMass controlSamplingMass : Real)
    (htreatedSelectionMeas :
      @Measurable Sample NNReal mSample _ treatedSelectionProb)
    (htreatedWeightMeas :
      @Measurable Sample NNReal mSample _ treatedSurveyWeight)
    (hcontrolSelectionMeas :
      @Measurable Sample NNReal mSample _ controlSelectionProb)
    (hcontrolWeightMeas :
      @Measurable Sample NNReal mSample _ controlSurveyWeight)
    (htreatedSamplingPos : 0 < treatedSamplingMass)
    (hcontrolSamplingPos : 0 < controlSamplingMass)
    (htreatedSelectedLaw :
      selectedLaw =
        ENNReal.ofReal (1 / treatedSamplingMass) •
          populationLaw.withDensity
            (fun sample => (treatedSelectionProb sample : ENNReal)))
    (hcontrolSelectedLaw :
      selectedLaw =
        ENNReal.ofReal (1 / controlSamplingMass) •
          populationLaw.withDensity
            (fun sample => (controlSelectionProb sample : ENNReal)))
    (htreatedInverse :
      ∀ sample,
        (treatedSelectionProb sample : ENNReal) *
          (treatedSurveyWeight sample : ENNReal) = 1)
    (hcontrolInverse :
      ∀ sample,
        (controlSelectionProb sample : ENNReal) *
          (controlSurveyWeight sample : ENNReal) = 1)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1)
    (htreatedAE :
      treatedOutcome =ᵐ[populationLaw] treatedScoreVersion)
    (hcontrolAE :
      controlOutcome =ᵐ[populationLaw] controlScoreVersion)
    (htreatedMeas :
      AEStronglyMeasurable[scoreSigma] treatedScoreVersion populationLaw)
    (hcontrolMeas :
      AEStronglyMeasurable[scoreSigma] controlScoreVersion populationLaw)
    (htreatedIntegrable : Integrable treatedScoreVersion populationLaw)
    (hcontrolIntegrable : Integrable controlScoreVersion populationLaw) :
    (∫ sample,
        (treatedSurveyWeight sample : Real) * treatedOutcome sample
        ∂selectedLaw) /
        (∫ sample, (treatedSurveyWeight sample : Real) ∂selectedLaw) -
      (∫ sample,
        (controlSurveyWeight sample : Real) * controlOutcome sample
        ∂selectedLaw) /
        (∫ sample, (controlSurveyWeight sample : Real) ∂selectedLaw) =
      (∫ sample, treatedScoreVersion sample ∂populationLaw) -
        (∫ sample, controlScoreVersion sample ∂populationLaw) := by
  have htreatedDensity :
      selectedLaw.withDensity
          (fun sample => (treatedSurveyWeight sample : ENNReal)) =
        ENNReal.ofReal (1 / treatedSamplingMass) • populationLaw :=
    @selectedLaw_withDensity_surveyWeight_eq_scaled_populationLaw Sample
      mSample
      selectedLaw populationLaw treatedSelectionProb treatedSurveyWeight
      treatedSamplingMass htreatedSelectionMeas htreatedWeightMeas
      htreatedSelectedLaw htreatedInverse
  have hcontrolDensity :
      selectedLaw.withDensity
          (fun sample => (controlSurveyWeight sample : ENNReal)) =
        ENNReal.ofReal (1 / controlSamplingMass) • populationLaw :=
    @selectedLaw_withDensity_surveyWeight_eq_scaled_populationLaw Sample
      mSample
      selectedLaw populationLaw controlSelectionProb controlSurveyWeight
      controlSamplingMass hcontrolSelectionMeas hcontrolWeightMeas
      hcontrolSelectedLaw hcontrolInverse
  have htreatedTarget :
      (∫ sample,
          (treatedSurveyWeight sample : Real) * treatedOutcome sample
          ∂selectedLaw) =
        (∫ sample, treatedOutcome sample ∂populationLaw) /
          treatedSamplingMass :=
    @surveyWeightIntegral_eq_populationIntegral_div_of_densityScaling Sample
      mSample
      selectedLaw populationLaw treatedSurveyWeight treatedOutcome
      treatedSamplingMass htreatedWeightMeas htreatedSamplingPos
      htreatedDensity
  have htreatedOne :
      (∫ sample, (treatedSurveyWeight sample : Real) ∂selectedLaw) =
        1 / treatedSamplingMass := by
    have h :=
      @surveyWeightIntegral_eq_populationIntegral_div_of_densityScaling Sample
        mSample
        selectedLaw populationLaw treatedSurveyWeight (fun _sample => (1 : Real))
        treatedSamplingMass htreatedWeightMeas htreatedSamplingPos
        htreatedDensity
    simpa [hpopulationOne] using h
  have hcontrolTarget :
      (∫ sample,
          (controlSurveyWeight sample : Real) * controlOutcome sample
          ∂selectedLaw) =
        (∫ sample, controlOutcome sample ∂populationLaw) /
          controlSamplingMass :=
    @surveyWeightIntegral_eq_populationIntegral_div_of_densityScaling Sample
      mSample
      selectedLaw populationLaw controlSurveyWeight controlOutcome
      controlSamplingMass hcontrolWeightMeas hcontrolSamplingPos
      hcontrolDensity
  have hcontrolOne :
      (∫ sample, (controlSurveyWeight sample : Real) ∂selectedLaw) =
        1 / controlSamplingMass := by
    have h :=
      @surveyWeightIntegral_eq_populationIntegral_div_of_densityScaling Sample
        mSample
        selectedLaw populationLaw controlSurveyWeight (fun _sample => (1 : Real))
        controlSamplingMass hcontrolWeightMeas hcontrolSamplingPos
        hcontrolDensity
    simpa [hpopulationOne] using h
  have hrepr :=
    selectedWeightedIntegralPATE_eq_scorePATE_of_ae_scoreVersions
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      hsub
      (fun sample => (treatedSurveyWeight sample : Real))
      (fun sample => (controlSurveyWeight sample : Real))
      treatedOutcome controlOutcome treatedScoreVersion controlScoreVersion
      treatedSamplingMass controlSamplingMass htreatedTarget htreatedOne
      hcontrolTarget hcontrolOne (ne_of_gt htreatedSamplingPos)
      (ne_of_gt hcontrolSamplingPos) htreatedAE hcontrolAE htreatedMeas
      hcontrolMeas htreatedIntegrable hcontrolIntegrable
  simpa [PATERepresentation.selectedHajekPATE,
    pateRepresentationOfWeightedIntegralRecovery,
    inverseSelectionIdentityOfWeightedIntegralRecovery] using hrepr

/--
Selection-density PATT identification from a.e. score-space numerator and
denominator versions.
-/
theorem selectedWeightedIntegralPATT_eq_scorePATT_of_selectionDensity_aeScoreVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (selectionProb surveyWeight : Sample -> NNReal)
    (treatedEffect treatedMass scoreEffect scoreMass : Sample -> Real)
    (samplingMass : Real)
    (hselectionMeas :
      @Measurable Sample NNReal mSample _ selectionProb)
    (hweightMeas :
      @Measurable Sample NNReal mSample _ surveyWeight)
    (hsamplingPos : 0 < samplingMass)
    (hselectedLaw :
      selectedLaw =
        ENNReal.ofReal (1 / samplingMass) •
          populationLaw.withDensity
            (fun sample => (selectionProb sample : ENNReal)))
    (hinverse :
      ∀ sample,
        (selectionProb sample : ENNReal) *
          (surveyWeight sample : ENNReal) = 1)
    (hpopulationMass :
      (∫ sample, treatedMass sample ∂populationLaw) ≠ 0)
    (hnumeratorAE :
      treatedEffect =ᵐ[populationLaw] scoreEffect)
    (hmassAE :
      treatedMass =ᵐ[populationLaw] scoreMass)
    (hnumeratorMeas :
      AEStronglyMeasurable[scoreSigma] scoreEffect populationLaw)
    (hmassMeas :
      AEStronglyMeasurable[scoreSigma] scoreMass populationLaw)
    (hnumeratorIntegrable : Integrable scoreEffect populationLaw)
    (hmassIntegrable : Integrable scoreMass populationLaw) :
    (∫ sample, (surveyWeight sample : Real) * treatedEffect sample
        ∂selectedLaw) /
        (∫ sample, (surveyWeight sample : Real) * treatedMass sample
          ∂selectedLaw) =
      (∫ sample, scoreEffect sample ∂populationLaw) /
        (∫ sample, scoreMass sample ∂populationLaw) := by
  have hdensity :
      selectedLaw.withDensity (fun sample => (surveyWeight sample : ENNReal)) =
        ENNReal.ofReal (1 / samplingMass) • populationLaw :=
    @selectedLaw_withDensity_surveyWeight_eq_scaled_populationLaw Sample
      mSample
      selectedLaw populationLaw selectionProb surveyWeight samplingMass
      hselectionMeas hweightMeas hselectedLaw hinverse
  have hnumeratorRecovery :
      (∫ sample, (surveyWeight sample : Real) * treatedEffect sample
        ∂selectedLaw) =
        (∫ sample, treatedEffect sample ∂populationLaw) / samplingMass :=
    @surveyWeightIntegral_eq_populationIntegral_div_of_densityScaling Sample
      mSample
      selectedLaw populationLaw surveyWeight treatedEffect samplingMass
      hweightMeas hsamplingPos hdensity
  have hmassRecovery :
      (∫ sample, (surveyWeight sample : Real) * treatedMass sample
        ∂selectedLaw) =
        (∫ sample, treatedMass sample ∂populationLaw) / samplingMass :=
    @surveyWeightIntegral_eq_populationIntegral_div_of_densityScaling Sample
      mSample
      selectedLaw populationLaw surveyWeight treatedMass samplingMass
      hweightMeas hsamplingPos hdensity
  have hrepr :=
    selectedWeightedIntegralPATT_eq_scorePATT_of_ae_scoreVersions
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      hsub (fun sample => (surveyWeight sample : Real)) treatedEffect
      treatedMass scoreEffect scoreMass samplingMass hnumeratorRecovery
      hmassRecovery (ne_of_gt hsamplingPos) hpopulationMass hnumeratorAE
      hmassAE hnumeratorMeas hmassMeas hnumeratorIntegrable hmassIntegrable
  simpa [PATTRepresentation.selectedHajekPATT,
    pattRepresentationOfWeightedIntegralRecovery] using hrepr

end WDSM
end Matching
end StatInference
