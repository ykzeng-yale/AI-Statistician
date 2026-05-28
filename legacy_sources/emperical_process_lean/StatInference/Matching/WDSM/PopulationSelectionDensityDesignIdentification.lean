import StatInference.Matching.WDSM.PopulationSelectionDensityDesign
import StatInference.Matching.WDSM.PopulationSurveyIdentificationBridge

/-!
# Population selection-density design identification bridge

This module derives selected-law survey-weighted score-space identification
directly from packaged `PopulationSelectionDensityDesign` records.  It is a
thin interface layer: the primitive design object supplies survey-weighted
integral recovery, and the existing population survey identification bridge
supplies the conditional score-space PATE/PATT identification step.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open scoped MeasureTheory ENNReal

variable {Sample : Type*} [mSample : MeasurableSpace Sample]
variable {scoreSigma : MeasurableSpace Sample}
variable {selectedLaw populationLaw : Measure[mSample] Sample}

private def designSurveyWeightReal
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw) :
    Sample -> Real :=
  fun sample =>
    ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample selectedLaw
      populationLaw design) sample : Real)

private def designSamplingMass
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw) :
    Real :=
  @PopulationSelectionDensityDesign.samplingMass Sample mSample selectedLaw
    populationLaw design

private theorem designSampling_pos
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw) :
    0 < @designSamplingMass Sample mSample selectedLaw populationLaw design :=
  @PopulationSelectionDensityDesign.sampling_pos Sample mSample selectedLaw
    populationLaw design

/--
Design-record PATE identification with conditional score-space means.

The two arm-specific packaged population selection-density designs discharge
the selected-law survey integral recovery assumptions needed by the population
survey identification bridge.
-/
theorem selectedWeightedIntegralPATE_eq_scorePATE_of_design_condExp
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (treatedDesign controlDesign :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (treatedOutcome controlOutcome
      treatedScoreVersion controlScoreVersion : Sample -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1)
    (htreatedCond :
      populationLaw[treatedOutcome | scoreSigma] =ᵐ[populationLaw]
        treatedScoreVersion)
    (hcontrolCond :
      populationLaw[controlOutcome | scoreSigma] =ᵐ[populationLaw]
        controlScoreVersion) :
    (∫ sample,
        (@designSurveyWeightReal Sample mSample selectedLaw populationLaw
          treatedDesign) sample * treatedOutcome sample
        ∂selectedLaw) /
        (∫ sample,
          (@designSurveyWeightReal Sample mSample selectedLaw populationLaw
            treatedDesign) sample ∂selectedLaw) -
      (∫ sample,
        (@designSurveyWeightReal Sample mSample selectedLaw populationLaw
          controlDesign) sample * controlOutcome sample
        ∂selectedLaw) /
        (∫ sample,
          (@designSurveyWeightReal Sample mSample selectedLaw populationLaw
            controlDesign) sample ∂selectedLaw) =
      (∫ sample, treatedScoreVersion sample ∂populationLaw) -
        (∫ sample, controlScoreVersion sample ∂populationLaw) := by
  have htreatedTarget :
      (∫ sample,
          (@designSurveyWeightReal Sample mSample selectedLaw populationLaw
            treatedDesign) sample * treatedOutcome sample
          ∂selectedLaw) =
        (∫ sample, treatedOutcome sample ∂populationLaw) /
          @designSamplingMass Sample mSample selectedLaw populationLaw
            treatedDesign := by
    simpa [designSurveyWeightReal, designSamplingMass] using
      (@PopulationSelectionDensityDesign.surveyWeightedIntegral_eq_populationIntegral_div
        Sample mSample selectedLaw populationLaw treatedDesign treatedOutcome)
  have htreatedOne :
      (∫ sample,
        (@designSurveyWeightReal Sample mSample selectedLaw populationLaw
          treatedDesign) sample ∂selectedLaw) =
        1 / @designSamplingMass Sample mSample selectedLaw populationLaw
          treatedDesign := by
    simpa [designSurveyWeightReal, designSamplingMass] using
      (@PopulationSelectionDensityDesign.surveyWeightedOne_eq_inv_samplingMass
        Sample mSample selectedLaw populationLaw treatedDesign hpopulationOne)
  have hcontrolTarget :
      (∫ sample,
          (@designSurveyWeightReal Sample mSample selectedLaw populationLaw
            controlDesign) sample * controlOutcome sample
          ∂selectedLaw) =
        (∫ sample, controlOutcome sample ∂populationLaw) /
          @designSamplingMass Sample mSample selectedLaw populationLaw
            controlDesign := by
    simpa [designSurveyWeightReal, designSamplingMass] using
      (@PopulationSelectionDensityDesign.surveyWeightedIntegral_eq_populationIntegral_div
        Sample mSample selectedLaw populationLaw controlDesign controlOutcome)
  have hcontrolOne :
      (∫ sample,
        (@designSurveyWeightReal Sample mSample selectedLaw populationLaw
          controlDesign) sample ∂selectedLaw) =
        1 / @designSamplingMass Sample mSample selectedLaw populationLaw
          controlDesign := by
    simpa [designSurveyWeightReal, designSamplingMass] using
      (@PopulationSelectionDensityDesign.surveyWeightedOne_eq_inv_samplingMass
        Sample mSample selectedLaw populationLaw controlDesign hpopulationOne)
  have hrepr :=
    selectedWeightedIntegralPATE_eq_scorePATE_of_condExp_scoreVersions
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      hsub
      (@designSurveyWeightReal Sample mSample selectedLaw populationLaw
        treatedDesign)
      (@designSurveyWeightReal Sample mSample selectedLaw populationLaw
        controlDesign)
      treatedOutcome controlOutcome treatedScoreVersion controlScoreVersion
      (@designSamplingMass Sample mSample selectedLaw populationLaw
        treatedDesign)
      (@designSamplingMass Sample mSample selectedLaw populationLaw
        controlDesign)
      htreatedTarget
      htreatedOne hcontrolTarget hcontrolOne
      (ne_of_gt
        (@designSampling_pos Sample mSample selectedLaw populationLaw
          treatedDesign))
      (ne_of_gt
        (@designSampling_pos Sample mSample selectedLaw populationLaw
          controlDesign)) htreatedCond hcontrolCond
  simpa [PATERepresentation.selectedHajekPATE,
    pateRepresentationOfWeightedIntegralRecovery,
    inverseSelectionIdentityOfWeightedIntegralRecovery] using hrepr

/--
Design-record PATT identification with conditional score-space means.
-/
theorem selectedWeightedIntegralPATT_eq_scorePATT_of_design_condExp
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (treatedEffect treatedMass scoreEffect scoreMass : Sample -> Real)
    (hpopulationMass :
      (∫ sample, treatedMass sample ∂populationLaw) ≠ 0)
    (hnumeratorCond :
      populationLaw[treatedEffect | scoreSigma] =ᵐ[populationLaw] scoreEffect)
    (hmassCond :
      populationLaw[treatedMass | scoreSigma] =ᵐ[populationLaw] scoreMass) :
    (∫ sample,
        (@designSurveyWeightReal Sample mSample selectedLaw populationLaw
          design) sample * treatedEffect sample
        ∂selectedLaw) /
        (∫ sample,
          (@designSurveyWeightReal Sample mSample selectedLaw populationLaw
            design) sample * treatedMass sample
          ∂selectedLaw) =
      (∫ sample, scoreEffect sample ∂populationLaw) /
        (∫ sample, scoreMass sample ∂populationLaw) := by
  have hnumeratorRecovery :
      (∫ sample,
        (@designSurveyWeightReal Sample mSample selectedLaw populationLaw
          design) sample * treatedEffect sample
        ∂selectedLaw) =
        (∫ sample, treatedEffect sample ∂populationLaw) /
          @designSamplingMass Sample mSample selectedLaw populationLaw
            design := by
    simpa [designSurveyWeightReal, designSamplingMass] using
      (@PopulationSelectionDensityDesign.surveyWeightedIntegral_eq_populationIntegral_div
        Sample mSample selectedLaw populationLaw design treatedEffect)
  have hmassRecovery :
      (∫ sample,
        (@designSurveyWeightReal Sample mSample selectedLaw populationLaw
          design) sample * treatedMass sample
        ∂selectedLaw) =
        (∫ sample, treatedMass sample ∂populationLaw) /
          @designSamplingMass Sample mSample selectedLaw populationLaw
            design := by
    simpa [designSurveyWeightReal, designSamplingMass] using
      (@PopulationSelectionDensityDesign.surveyWeightedIntegral_eq_populationIntegral_div
        Sample mSample selectedLaw populationLaw design treatedMass)
  have hrepr :=
    selectedWeightedIntegralPATT_eq_scorePATT_of_condExp_scoreVersions
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      hsub (@designSurveyWeightReal Sample mSample selectedLaw populationLaw
        design) treatedEffect
      treatedMass scoreEffect scoreMass
      (@designSamplingMass Sample mSample selectedLaw populationLaw design)
      hnumeratorRecovery hmassRecovery
      (ne_of_gt
        (@designSampling_pos Sample mSample selectedLaw populationLaw design))
      hpopulationMass hnumeratorCond hmassCond
  simpa [PATTRepresentation.selectedHajekPATT,
    pattRepresentationOfWeightedIntegralRecovery] using hrepr

end WDSM
end Matching
end StatInference
