import StatInference.Matching.WDSM.PopulationSurveyIdentificationBridge
import StatInference.Matching.WDSM.PopulationSurveySelectionDensity

/-!
# Population selection-density survey identification bridge

This module composes the primitive selection-density representation with the
population survey identification bridge.  The resulting theorems expose the
manuscript-level shape: selected-law survey-weighted Hájek PATE/PATT ratios
recover score-space targets when the selected law is a normalized
selection-probability tilt of the population law and survey weights invert the
selection probabilities.
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
Selection-density PATE identification with conditional score-space means.

This is a direct raw-ratio statement: the selected-law survey-weighted Hájek
PATE equals the population-law score-space PATE once each arm's selected-law
density is a normalized selection-probability tilt and the corresponding
survey weight is its inverse.
-/
theorem selectedWeightedIntegralPATE_eq_scorePATE_of_selectionDensity_condExp
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
    (htreatedCond :
      populationLaw[treatedOutcome | scoreSigma] =ᵐ[populationLaw]
        treatedScoreVersion)
    (hcontrolCond :
      populationLaw[controlOutcome | scoreSigma] =ᵐ[populationLaw]
        controlScoreVersion) :
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
    selectedWeightedIntegralPATE_eq_scorePATE_of_condExp_scoreVersions
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      hsub
      (fun sample => (treatedSurveyWeight sample : Real))
      (fun sample => (controlSurveyWeight sample : Real))
      treatedOutcome controlOutcome treatedScoreVersion controlScoreVersion
      treatedSamplingMass controlSamplingMass htreatedTarget htreatedOne
      hcontrolTarget hcontrolOne (ne_of_gt htreatedSamplingPos)
      (ne_of_gt hcontrolSamplingPos) htreatedCond hcontrolCond
  simpa [PATERepresentation.selectedHajekPATE,
    pateRepresentationOfWeightedIntegralRecovery,
    inverseSelectionIdentityOfWeightedIntegralRecovery] using hrepr

/--
Selection-density PATT identification with conditional score-space means.
-/
theorem selectedWeightedIntegralPATT_eq_scorePATT_of_selectionDensity_condExp
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
    (hnumeratorCond :
      populationLaw[treatedEffect | scoreSigma] =ᵐ[populationLaw] scoreEffect)
    (hmassCond :
      populationLaw[treatedMass | scoreSigma] =ᵐ[populationLaw] scoreMass) :
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
    selectedWeightedIntegralPATT_eq_scorePATT_of_condExp_scoreVersions
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      hsub (fun sample => (surveyWeight sample : Real)) treatedEffect
      treatedMass scoreEffect scoreMass samplingMass hnumeratorRecovery
      hmassRecovery (ne_of_gt hsamplingPos) hpopulationMass hnumeratorCond
      hmassCond
  simpa [PATTRepresentation.selectedHajekPATT,
    pattRepresentationOfWeightedIntegralRecovery] using hrepr

end WDSM
end Matching
end StatInference
