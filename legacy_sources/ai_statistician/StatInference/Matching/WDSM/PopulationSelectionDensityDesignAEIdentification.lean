import StatInference.Matching.WDSM.PopulationSelectionDensityDesign
import StatInference.Matching.WDSM.PopulationSurveyIdentificationBridge

/-!
# Population selection-density design a.e. identification bridge

This module is the a.e.-score-version companion to
`PopulationSelectionDensityDesignIdentification`.  It derives selected-law
survey-weighted score-space identification directly from packaged
`PopulationSelectionDensityDesign` records and score-sigma measurable a.e.
versions.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open scoped MeasureTheory ENNReal

variable {Sample : Type*} [mSample : MeasurableSpace Sample]
variable {scoreSigma : MeasurableSpace Sample}
variable {selectedLaw populationLaw : Measure[mSample] Sample}

private def designAESurveyWeightReal
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw) :
    Sample -> Real :=
  fun sample =>
    ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample selectedLaw
      populationLaw design) sample : Real)

private def designAESamplingMass
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw) :
    Real :=
  @PopulationSelectionDensityDesign.samplingMass Sample mSample selectedLaw
    populationLaw design

private theorem designAESampling_pos
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw) :
    0 < @designAESamplingMass Sample mSample selectedLaw populationLaw design :=
  @PopulationSelectionDensityDesign.sampling_pos Sample mSample selectedLaw
    populationLaw design

/--
Design-record PATE identification from a.e. score-space outcome versions.
-/
theorem selectedWeightedIntegralPATE_eq_scorePATE_of_design_aeScoreVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (treatedDesign controlDesign :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (treatedOutcome controlOutcome
      treatedScoreVersion controlScoreVersion : Sample -> Real)
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
        (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
          treatedDesign) sample * treatedOutcome sample
        ∂selectedLaw) /
        (∫ sample,
          (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
            treatedDesign) sample ∂selectedLaw) -
      (∫ sample,
        (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
          controlDesign) sample * controlOutcome sample
        ∂selectedLaw) /
        (∫ sample,
          (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
            controlDesign) sample ∂selectedLaw) =
      (∫ sample, treatedScoreVersion sample ∂populationLaw) -
        (∫ sample, controlScoreVersion sample ∂populationLaw) := by
  have htreatedTarget :
      (∫ sample,
          (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
            treatedDesign) sample * treatedOutcome sample
          ∂selectedLaw) =
        (∫ sample, treatedOutcome sample ∂populationLaw) /
          @designAESamplingMass Sample mSample selectedLaw populationLaw
            treatedDesign := by
    simpa [designAESurveyWeightReal, designAESamplingMass] using
      (@PopulationSelectionDensityDesign.surveyWeightedIntegral_eq_populationIntegral_div
        Sample mSample selectedLaw populationLaw treatedDesign treatedOutcome)
  have htreatedOne :
      (∫ sample,
        (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
          treatedDesign) sample ∂selectedLaw) =
        1 / @designAESamplingMass Sample mSample selectedLaw populationLaw
          treatedDesign := by
    simpa [designAESurveyWeightReal, designAESamplingMass] using
      (@PopulationSelectionDensityDesign.surveyWeightedOne_eq_inv_samplingMass
        Sample mSample selectedLaw populationLaw treatedDesign hpopulationOne)
  have hcontrolTarget :
      (∫ sample,
          (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
            controlDesign) sample * controlOutcome sample
          ∂selectedLaw) =
        (∫ sample, controlOutcome sample ∂populationLaw) /
          @designAESamplingMass Sample mSample selectedLaw populationLaw
            controlDesign := by
    simpa [designAESurveyWeightReal, designAESamplingMass] using
      (@PopulationSelectionDensityDesign.surveyWeightedIntegral_eq_populationIntegral_div
        Sample mSample selectedLaw populationLaw controlDesign controlOutcome)
  have hcontrolOne :
      (∫ sample,
        (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
          controlDesign) sample ∂selectedLaw) =
        1 / @designAESamplingMass Sample mSample selectedLaw populationLaw
          controlDesign := by
    simpa [designAESurveyWeightReal, designAESamplingMass] using
      (@PopulationSelectionDensityDesign.surveyWeightedOne_eq_inv_samplingMass
        Sample mSample selectedLaw populationLaw controlDesign hpopulationOne)
  have hrepr :=
    selectedWeightedIntegralPATE_eq_scorePATE_of_ae_scoreVersions
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      hsub
      (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
        treatedDesign)
      (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
        controlDesign)
      treatedOutcome controlOutcome treatedScoreVersion controlScoreVersion
      (@designAESamplingMass Sample mSample selectedLaw populationLaw
        treatedDesign)
      (@designAESamplingMass Sample mSample selectedLaw populationLaw
        controlDesign)
      htreatedTarget htreatedOne hcontrolTarget hcontrolOne
      (ne_of_gt
        (@designAESampling_pos Sample mSample selectedLaw populationLaw
          treatedDesign))
      (ne_of_gt
        (@designAESampling_pos Sample mSample selectedLaw populationLaw
          controlDesign)) htreatedAE hcontrolAE htreatedMeas hcontrolMeas
      htreatedIntegrable hcontrolIntegrable
  simpa [PATERepresentation.selectedHajekPATE,
    pateRepresentationOfWeightedIntegralRecovery,
    inverseSelectionIdentityOfWeightedIntegralRecovery] using hrepr

/--
Design-record PATT identification from a.e. score-space numerator and
denominator versions.
-/
theorem selectedWeightedIntegralPATT_eq_scorePATT_of_design_aeScoreVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (treatedEffect treatedMass scoreEffect scoreMass : Sample -> Real)
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
    (∫ sample,
        (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
          design) sample * treatedEffect sample
        ∂selectedLaw) /
        (∫ sample,
          (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
            design) sample * treatedMass sample
          ∂selectedLaw) =
      (∫ sample, scoreEffect sample ∂populationLaw) /
        (∫ sample, scoreMass sample ∂populationLaw) := by
  have hnumeratorRecovery :
      (∫ sample,
        (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
          design) sample * treatedEffect sample
        ∂selectedLaw) =
        (∫ sample, treatedEffect sample ∂populationLaw) /
          @designAESamplingMass Sample mSample selectedLaw populationLaw
            design := by
    simpa [designAESurveyWeightReal, designAESamplingMass] using
      (@PopulationSelectionDensityDesign.surveyWeightedIntegral_eq_populationIntegral_div
        Sample mSample selectedLaw populationLaw design treatedEffect)
  have hmassRecovery :
      (∫ sample,
        (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
          design) sample * treatedMass sample
        ∂selectedLaw) =
        (∫ sample, treatedMass sample ∂populationLaw) /
          @designAESamplingMass Sample mSample selectedLaw populationLaw
            design := by
    simpa [designAESurveyWeightReal, designAESamplingMass] using
      (@PopulationSelectionDensityDesign.surveyWeightedIntegral_eq_populationIntegral_div
        Sample mSample selectedLaw populationLaw design treatedMass)
  have hrepr :=
    selectedWeightedIntegralPATT_eq_scorePATT_of_ae_scoreVersions
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      hsub (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
        design) treatedEffect
      treatedMass scoreEffect scoreMass
      (@designAESamplingMass Sample mSample selectedLaw populationLaw design)
      hnumeratorRecovery hmassRecovery
      (ne_of_gt
        (@designAESampling_pos Sample mSample selectedLaw populationLaw design))
      hpopulationMass hnumeratorAE hmassAE hnumeratorMeas hmassMeas
      hnumeratorIntegrable hmassIntegrable
  simpa [PATTRepresentation.selectedHajekPATT,
    pattRepresentationOfWeightedIntegralRecovery] using hrepr

/--
Paired raw selected-law survey-weighted PATE/PATT identification from packaged
selection-density design records and a.e. score-space versions.
-/
theorem selectedWeightedIntegralPATE_PATT_eq_scorePATE_PATT_of_design_aeScoreVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (treatedDesign controlDesign pattDesign :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (treatedOutcome controlOutcome treatedEffect treatedMass
      treatedScoreVersion controlScoreVersion scoreEffect scoreMass :
      Sample -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1)
    (hpopulationMass :
      (∫ sample, treatedMass sample ∂populationLaw) ≠ 0)
    (htreatedAE :
      treatedOutcome =ᵐ[populationLaw] treatedScoreVersion)
    (hcontrolAE :
      controlOutcome =ᵐ[populationLaw] controlScoreVersion)
    (hnumeratorAE :
      treatedEffect =ᵐ[populationLaw] scoreEffect)
    (hmassAE :
      treatedMass =ᵐ[populationLaw] scoreMass)
    (htreatedMeas :
      AEStronglyMeasurable[scoreSigma] treatedScoreVersion populationLaw)
    (hcontrolMeas :
      AEStronglyMeasurable[scoreSigma] controlScoreVersion populationLaw)
    (hnumeratorMeas :
      AEStronglyMeasurable[scoreSigma] scoreEffect populationLaw)
    (hmassMeas :
      AEStronglyMeasurable[scoreSigma] scoreMass populationLaw)
    (htreatedIntegrable :
      Integrable treatedScoreVersion populationLaw)
    (hcontrolIntegrable :
      Integrable controlScoreVersion populationLaw)
    (hnumeratorIntegrable :
      Integrable scoreEffect populationLaw)
    (hmassIntegrable :
      Integrable scoreMass populationLaw) :
    (∫ sample,
        (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
          treatedDesign) sample * treatedOutcome sample
        ∂selectedLaw) /
        (∫ sample,
          (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
            treatedDesign) sample ∂selectedLaw) -
      (∫ sample,
        (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
          controlDesign) sample * controlOutcome sample
        ∂selectedLaw) /
        (∫ sample,
          (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
            controlDesign) sample ∂selectedLaw) =
        (∫ sample, treatedScoreVersion sample ∂populationLaw) -
          (∫ sample, controlScoreVersion sample ∂populationLaw) ∧
      (∫ sample,
        (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
          pattDesign) sample * treatedEffect sample
        ∂selectedLaw) /
        (∫ sample,
          (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
            pattDesign) sample * treatedMass sample
          ∂selectedLaw) =
        (∫ sample, scoreEffect sample ∂populationLaw) /
          (∫ sample, scoreMass sample ∂populationLaw) := by
  constructor
  · exact
      selectedWeightedIntegralPATE_eq_scorePATE_of_design_aeScoreVersions
        (mSample := mSample) (scoreSigma := scoreSigma)
        (selectedLaw := selectedLaw) (populationLaw := populationLaw)
        hsub treatedDesign controlDesign treatedOutcome controlOutcome
        treatedScoreVersion controlScoreVersion hpopulationOne htreatedAE
        hcontrolAE htreatedMeas hcontrolMeas htreatedIntegrable
        hcontrolIntegrable
  · exact
      selectedWeightedIntegralPATT_eq_scorePATT_of_design_aeScoreVersions
        (mSample := mSample) (scoreSigma := scoreSigma)
        (selectedLaw := selectedLaw) (populationLaw := populationLaw)
        hsub pattDesign treatedEffect treatedMass scoreEffect scoreMass
        hpopulationMass hnumeratorAE hmassAE hnumeratorMeas hmassMeas
        hnumeratorIntegrable hmassIntegrable

/--
Raw-outcome-integrability variant of design-record PATE identification from
a.e. score-space outcome versions.
-/
theorem selectedWeightedIntegralPATE_eq_scorePATE_of_design_aeScoreVersions_outcomeIntegrable
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (treatedDesign controlDesign :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (treatedOutcome controlOutcome
      treatedScoreVersion controlScoreVersion : Sample -> Real)
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
    (htreatedOutcomeIntegrable :
      Integrable treatedOutcome populationLaw)
    (hcontrolOutcomeIntegrable :
      Integrable controlOutcome populationLaw) :
    (∫ sample,
        (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
          treatedDesign) sample * treatedOutcome sample
        ∂selectedLaw) /
        (∫ sample,
          (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
            treatedDesign) sample ∂selectedLaw) -
      (∫ sample,
        (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
          controlDesign) sample * controlOutcome sample
        ∂selectedLaw) /
        (∫ sample,
          (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
            controlDesign) sample ∂selectedLaw) =
      (∫ sample, treatedScoreVersion sample ∂populationLaw) -
        (∫ sample, controlScoreVersion sample ∂populationLaw) := by
  have htreatedTarget :
      (∫ sample,
          (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
            treatedDesign) sample * treatedOutcome sample
          ∂selectedLaw) =
        (∫ sample, treatedOutcome sample ∂populationLaw) /
          @designAESamplingMass Sample mSample selectedLaw populationLaw
            treatedDesign := by
    simpa [designAESurveyWeightReal, designAESamplingMass] using
      (@PopulationSelectionDensityDesign.surveyWeightedIntegral_eq_populationIntegral_div
        Sample mSample selectedLaw populationLaw treatedDesign treatedOutcome)
  have htreatedOne :
      (∫ sample,
        (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
          treatedDesign) sample ∂selectedLaw) =
        1 / @designAESamplingMass Sample mSample selectedLaw populationLaw
          treatedDesign := by
    simpa [designAESurveyWeightReal, designAESamplingMass] using
      (@PopulationSelectionDensityDesign.surveyWeightedOne_eq_inv_samplingMass
        Sample mSample selectedLaw populationLaw treatedDesign hpopulationOne)
  have hcontrolTarget :
      (∫ sample,
          (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
            controlDesign) sample * controlOutcome sample
          ∂selectedLaw) =
        (∫ sample, controlOutcome sample ∂populationLaw) /
          @designAESamplingMass Sample mSample selectedLaw populationLaw
            controlDesign := by
    simpa [designAESurveyWeightReal, designAESamplingMass] using
      (@PopulationSelectionDensityDesign.surveyWeightedIntegral_eq_populationIntegral_div
        Sample mSample selectedLaw populationLaw controlDesign controlOutcome)
  have hcontrolOne :
      (∫ sample,
        (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
          controlDesign) sample ∂selectedLaw) =
        1 / @designAESamplingMass Sample mSample selectedLaw populationLaw
          controlDesign := by
    simpa [designAESurveyWeightReal, designAESamplingMass] using
      (@PopulationSelectionDensityDesign.surveyWeightedOne_eq_inv_samplingMass
        Sample mSample selectedLaw populationLaw controlDesign hpopulationOne)
  have hrepr :=
    selectedWeightedIntegralPATE_eq_scorePATE_of_ae_scoreVersions_outcomeIntegrable
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      hsub
      (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
        treatedDesign)
      (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
        controlDesign)
      treatedOutcome controlOutcome treatedScoreVersion controlScoreVersion
      (@designAESamplingMass Sample mSample selectedLaw populationLaw
        treatedDesign)
      (@designAESamplingMass Sample mSample selectedLaw populationLaw
        controlDesign)
      htreatedTarget htreatedOne hcontrolTarget hcontrolOne
      (ne_of_gt
        (@designAESampling_pos Sample mSample selectedLaw populationLaw
          treatedDesign))
      (ne_of_gt
        (@designAESampling_pos Sample mSample selectedLaw populationLaw
          controlDesign)) htreatedAE hcontrolAE htreatedMeas hcontrolMeas
      htreatedOutcomeIntegrable hcontrolOutcomeIntegrable
  simpa [PATERepresentation.selectedHajekPATE,
    pateRepresentationOfWeightedIntegralRecovery,
    inverseSelectionIdentityOfWeightedIntegralRecovery] using hrepr

/--
Raw-outcome-integrability variant of design-record PATT identification from
a.e. score-space numerator and denominator versions.
-/
theorem selectedWeightedIntegralPATT_eq_scorePATT_of_design_aeScoreVersions_outcomeIntegrable
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (treatedEffect treatedMass scoreEffect scoreMass : Sample -> Real)
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
    (hnumeratorOutcomeIntegrable :
      Integrable treatedEffect populationLaw)
    (hmassOutcomeIntegrable :
      Integrable treatedMass populationLaw) :
    (∫ sample,
        (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
          design) sample * treatedEffect sample
        ∂selectedLaw) /
        (∫ sample,
          (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
            design) sample * treatedMass sample
          ∂selectedLaw) =
      (∫ sample, scoreEffect sample ∂populationLaw) /
        (∫ sample, scoreMass sample ∂populationLaw) := by
  have hnumeratorRecovery :
      (∫ sample,
        (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
          design) sample * treatedEffect sample
        ∂selectedLaw) =
        (∫ sample, treatedEffect sample ∂populationLaw) /
          @designAESamplingMass Sample mSample selectedLaw populationLaw
            design := by
    simpa [designAESurveyWeightReal, designAESamplingMass] using
      (@PopulationSelectionDensityDesign.surveyWeightedIntegral_eq_populationIntegral_div
        Sample mSample selectedLaw populationLaw design treatedEffect)
  have hmassRecovery :
      (∫ sample,
        (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
          design) sample * treatedMass sample
        ∂selectedLaw) =
        (∫ sample, treatedMass sample ∂populationLaw) /
          @designAESamplingMass Sample mSample selectedLaw populationLaw
            design := by
    simpa [designAESurveyWeightReal, designAESamplingMass] using
      (@PopulationSelectionDensityDesign.surveyWeightedIntegral_eq_populationIntegral_div
        Sample mSample selectedLaw populationLaw design treatedMass)
  have hrepr :=
    selectedWeightedIntegralPATT_eq_scorePATT_of_ae_scoreVersions_outcomeIntegrable
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      hsub (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
        design) treatedEffect
      treatedMass scoreEffect scoreMass
      (@designAESamplingMass Sample mSample selectedLaw populationLaw design)
      hnumeratorRecovery hmassRecovery
      (ne_of_gt
        (@designAESampling_pos Sample mSample selectedLaw populationLaw design))
      hpopulationMass hnumeratorAE hmassAE hnumeratorMeas hmassMeas
      hnumeratorOutcomeIntegrable hmassOutcomeIntegrable
  simpa [PATTRepresentation.selectedHajekPATT,
    pattRepresentationOfWeightedIntegralRecovery] using hrepr

/--
Raw-outcome-integrability paired selected-law survey-weighted PATE/PATT
identification from packaged selection-density design records and a.e.
score-space versions.
-/
theorem selectedWeightedIntegralPATE_PATT_eq_scorePATE_PATT_of_design_aeScoreVersions_outcomeIntegrable
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (treatedDesign controlDesign pattDesign :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (treatedOutcome controlOutcome treatedEffect treatedMass
      treatedScoreVersion controlScoreVersion scoreEffect scoreMass :
      Sample -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1)
    (hpopulationMass :
      (∫ sample, treatedMass sample ∂populationLaw) ≠ 0)
    (htreatedAE :
      treatedOutcome =ᵐ[populationLaw] treatedScoreVersion)
    (hcontrolAE :
      controlOutcome =ᵐ[populationLaw] controlScoreVersion)
    (hnumeratorAE :
      treatedEffect =ᵐ[populationLaw] scoreEffect)
    (hmassAE :
      treatedMass =ᵐ[populationLaw] scoreMass)
    (htreatedMeas :
      AEStronglyMeasurable[scoreSigma] treatedScoreVersion populationLaw)
    (hcontrolMeas :
      AEStronglyMeasurable[scoreSigma] controlScoreVersion populationLaw)
    (hnumeratorMeas :
      AEStronglyMeasurable[scoreSigma] scoreEffect populationLaw)
    (hmassMeas :
      AEStronglyMeasurable[scoreSigma] scoreMass populationLaw)
    (htreatedOutcomeIntegrable :
      Integrable treatedOutcome populationLaw)
    (hcontrolOutcomeIntegrable :
      Integrable controlOutcome populationLaw)
    (hnumeratorOutcomeIntegrable :
      Integrable treatedEffect populationLaw)
    (hmassOutcomeIntegrable :
      Integrable treatedMass populationLaw) :
    (∫ sample,
        (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
          treatedDesign) sample * treatedOutcome sample
        ∂selectedLaw) /
        (∫ sample,
          (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
            treatedDesign) sample ∂selectedLaw) -
      (∫ sample,
        (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
          controlDesign) sample * controlOutcome sample
        ∂selectedLaw) /
        (∫ sample,
          (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
            controlDesign) sample ∂selectedLaw) =
        (∫ sample, treatedScoreVersion sample ∂populationLaw) -
          (∫ sample, controlScoreVersion sample ∂populationLaw) ∧
      (∫ sample,
        (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
          pattDesign) sample * treatedEffect sample
        ∂selectedLaw) /
        (∫ sample,
          (@designAESurveyWeightReal Sample mSample selectedLaw populationLaw
            pattDesign) sample * treatedMass sample
          ∂selectedLaw) =
        (∫ sample, scoreEffect sample ∂populationLaw) /
          (∫ sample, scoreMass sample ∂populationLaw) := by
  constructor
  · exact
      selectedWeightedIntegralPATE_eq_scorePATE_of_design_aeScoreVersions_outcomeIntegrable
        (mSample := mSample) (scoreSigma := scoreSigma)
        (selectedLaw := selectedLaw) (populationLaw := populationLaw)
        hsub treatedDesign controlDesign treatedOutcome controlOutcome
        treatedScoreVersion controlScoreVersion hpopulationOne htreatedAE
        hcontrolAE htreatedMeas hcontrolMeas htreatedOutcomeIntegrable
        hcontrolOutcomeIntegrable
  · exact
      selectedWeightedIntegralPATT_eq_scorePATT_of_design_aeScoreVersions_outcomeIntegrable
        (mSample := mSample) (scoreSigma := scoreSigma)
        (selectedLaw := selectedLaw) (populationLaw := populationLaw)
        hsub pattDesign treatedEffect treatedMass scoreEffect scoreMass
        hpopulationMass hnumeratorAE hmassAE hnumeratorMeas hmassMeas
        hnumeratorOutcomeIntegrable hmassOutcomeIntegrable

end WDSM
end Matching
end StatInference
