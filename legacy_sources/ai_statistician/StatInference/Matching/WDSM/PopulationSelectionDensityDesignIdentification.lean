import StatInference.Matching.WDSM.PopulationSelectionDensityDesign
import StatInference.Matching.WDSM.PopulationSurveyIdentificationBridge
import StatInference.Matching.WDSM.ConditionalExpectationBridge

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
Design-record PATE identification from a.e. score-space versions.

This closes the common route where the paper first constructs score-space
versions of the two potential-outcome means and only then appeals to
conditional-score identification.
-/
theorem selectedWeightedIntegralPATE_eq_scorePATE_of_design_ae_scoreVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (treatedDesign controlDesign :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (treatedOutcome controlOutcome
      treatedScoreVersion controlScoreVersion : Sample -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1)
    (htreated :
      treatedOutcome =ᵐ[populationLaw] treatedScoreVersion)
    (hcontrol :
      controlOutcome =ᵐ[populationLaw] controlScoreVersion)
    (htreatedMeas :
      AEStronglyMeasurable[scoreSigma] treatedScoreVersion populationLaw)
    (hcontrolMeas :
      AEStronglyMeasurable[scoreSigma] controlScoreVersion populationLaw)
    (htreatedIntegrable :
      Integrable treatedScoreVersion populationLaw)
    (hcontrolIntegrable :
      Integrable controlScoreVersion populationLaw) :
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
  exact
    selectedWeightedIntegralPATE_eq_scorePATE_of_design_condExp
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      hsub treatedDesign controlDesign treatedOutcome controlOutcome
      treatedScoreVersion controlScoreVersion hpopulationOne
      (condExp_ae_eq_scoreVersion_of_ae_eq_aestronglyMeasurable
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := populationLaw) hsub treatedOutcome
        treatedScoreVersion htreated htreatedMeas htreatedIntegrable)
      (condExp_ae_eq_scoreVersion_of_ae_eq_aestronglyMeasurable
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := populationLaw) hsub controlOutcome
        controlScoreVersion hcontrol hcontrolMeas hcontrolIntegrable)

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

/--
Design-record PATT identification from a.e. score-space versions of the
treated-effect numerator and treated-mass denominator.
-/
theorem selectedWeightedIntegralPATT_eq_scorePATT_of_design_ae_scoreVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (treatedEffect treatedMass scoreEffect scoreMass : Sample -> Real)
    (hpopulationMass :
      (∫ sample, treatedMass sample ∂populationLaw) ≠ 0)
    (hnumerator :
      treatedEffect =ᵐ[populationLaw] scoreEffect)
    (hmass :
      treatedMass =ᵐ[populationLaw] scoreMass)
    (hnumeratorMeas :
      AEStronglyMeasurable[scoreSigma] scoreEffect populationLaw)
    (hmassMeas :
      AEStronglyMeasurable[scoreSigma] scoreMass populationLaw)
    (hnumeratorIntegrable :
      Integrable scoreEffect populationLaw)
    (hmassIntegrable :
      Integrable scoreMass populationLaw) :
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
  exact
    selectedWeightedIntegralPATT_eq_scorePATT_of_design_condExp
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      hsub design treatedEffect treatedMass scoreEffect scoreMass
      hpopulationMass
      (condExp_ae_eq_scoreVersion_of_ae_eq_aestronglyMeasurable
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := populationLaw) hsub treatedEffect scoreEffect
        hnumerator hnumeratorMeas hnumeratorIntegrable)
      (condExp_ae_eq_scoreVersion_of_ae_eq_aestronglyMeasurable
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := populationLaw) hsub treatedMass scoreMass hmass
        hmassMeas hmassIntegrable)

/--
Paired raw selected-law survey-weighted PATE/PATT identification from packaged
selection-density design records and conditional score-space mean versions.
-/
theorem selectedWeightedIntegralPATE_PATT_eq_scorePATE_PATT_of_design_condExp
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
    (htreatedCond :
      populationLaw[treatedOutcome | scoreSigma] =ᵐ[populationLaw]
        treatedScoreVersion)
    (hcontrolCond :
      populationLaw[controlOutcome | scoreSigma] =ᵐ[populationLaw]
        controlScoreVersion)
    (hnumeratorCond :
      populationLaw[treatedEffect | scoreSigma] =ᵐ[populationLaw] scoreEffect)
    (hmassCond :
      populationLaw[treatedMass | scoreSigma] =ᵐ[populationLaw] scoreMass) :
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
          (∫ sample, controlScoreVersion sample ∂populationLaw) ∧
      (∫ sample,
        (@designSurveyWeightReal Sample mSample selectedLaw populationLaw
          pattDesign) sample * treatedEffect sample
        ∂selectedLaw) /
        (∫ sample,
          (@designSurveyWeightReal Sample mSample selectedLaw populationLaw
            pattDesign) sample * treatedMass sample
          ∂selectedLaw) =
        (∫ sample, scoreEffect sample ∂populationLaw) /
          (∫ sample, scoreMass sample ∂populationLaw) := by
  constructor
  · exact
      selectedWeightedIntegralPATE_eq_scorePATE_of_design_condExp
        (mSample := mSample) (scoreSigma := scoreSigma)
        (selectedLaw := selectedLaw) (populationLaw := populationLaw)
        hsub treatedDesign controlDesign treatedOutcome controlOutcome
        treatedScoreVersion controlScoreVersion hpopulationOne htreatedCond
        hcontrolCond
  · exact
      selectedWeightedIntegralPATT_eq_scorePATT_of_design_condExp
        (mSample := mSample) (scoreSigma := scoreSigma)
        (selectedLaw := selectedLaw) (populationLaw := populationLaw)
        hsub pattDesign treatedEffect treatedMass scoreEffect scoreMass
        hpopulationMass hnumeratorCond hmassCond

/--
Paired raw selected-law survey-weighted PATE/PATT identification from packaged
selection-density design records and a.e. score-space versions.
-/
theorem selectedWeightedIntegralPATE_PATT_eq_scorePATE_PATT_of_design_ae_scoreVersions
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
          (∫ sample, controlScoreVersion sample ∂populationLaw) ∧
      (∫ sample,
        (@designSurveyWeightReal Sample mSample selectedLaw populationLaw
          pattDesign) sample * treatedEffect sample
        ∂selectedLaw) /
        (∫ sample,
          (@designSurveyWeightReal Sample mSample selectedLaw populationLaw
            pattDesign) sample * treatedMass sample
          ∂selectedLaw) =
        (∫ sample, scoreEffect sample ∂populationLaw) /
          (∫ sample, scoreMass sample ∂populationLaw) := by
  constructor
  · exact
      selectedWeightedIntegralPATE_eq_scorePATE_of_design_ae_scoreVersions
        (mSample := mSample) (scoreSigma := scoreSigma)
        (selectedLaw := selectedLaw) (populationLaw := populationLaw)
        hsub treatedDesign controlDesign treatedOutcome controlOutcome
        treatedScoreVersion controlScoreVersion hpopulationOne htreatedAE
        hcontrolAE htreatedMeas hcontrolMeas htreatedIntegrable
        hcontrolIntegrable
  · exact
      selectedWeightedIntegralPATT_eq_scorePATT_of_design_ae_scoreVersions
        (mSample := mSample) (scoreSigma := scoreSigma)
        (selectedLaw := selectedLaw) (populationLaw := populationLaw)
        hsub pattDesign treatedEffect treatedMass scoreEffect scoreMass
        hpopulationMass hnumeratorAE hmassAE hnumeratorMeas hmassMeas
        hnumeratorIntegrable hmassIntegrable

/--
Raw-outcome-integrability variant of design-record PATE identification from
a.e. score-space versions.
-/
theorem selectedWeightedIntegralPATE_eq_scorePATE_of_design_ae_scoreVersions_outcomeIntegrable
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (treatedDesign controlDesign :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (treatedOutcome controlOutcome
      treatedScoreVersion controlScoreVersion : Sample -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1)
    (htreated :
      treatedOutcome =ᵐ[populationLaw] treatedScoreVersion)
    (hcontrol :
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
  exact
    selectedWeightedIntegralPATE_eq_scorePATE_of_design_condExp
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      hsub treatedDesign controlDesign treatedOutcome controlOutcome
      treatedScoreVersion controlScoreVersion hpopulationOne
      (condExp_ae_eq_scoreVersion_of_ae_eq_aestronglyMeasurable_outcomeIntegrable
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := populationLaw) hsub treatedOutcome
        treatedScoreVersion htreated htreatedMeas htreatedOutcomeIntegrable)
      (condExp_ae_eq_scoreVersion_of_ae_eq_aestronglyMeasurable_outcomeIntegrable
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := populationLaw) hsub controlOutcome
        controlScoreVersion hcontrol hcontrolMeas hcontrolOutcomeIntegrable)

/--
Raw-outcome-integrability variant of design-record PATT identification from
a.e. score-space numerator and denominator versions.
-/
theorem selectedWeightedIntegralPATT_eq_scorePATT_of_design_ae_scoreVersions_outcomeIntegrable
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (treatedEffect treatedMass scoreEffect scoreMass : Sample -> Real)
    (hpopulationMass :
      (∫ sample, treatedMass sample ∂populationLaw) ≠ 0)
    (hnumerator :
      treatedEffect =ᵐ[populationLaw] scoreEffect)
    (hmass :
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
        (@designSurveyWeightReal Sample mSample selectedLaw populationLaw
          design) sample * treatedEffect sample
        ∂selectedLaw) /
        (∫ sample,
          (@designSurveyWeightReal Sample mSample selectedLaw populationLaw
            design) sample * treatedMass sample
          ∂selectedLaw) =
      (∫ sample, scoreEffect sample ∂populationLaw) /
        (∫ sample, scoreMass sample ∂populationLaw) := by
  exact
    selectedWeightedIntegralPATT_eq_scorePATT_of_design_condExp
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      hsub design treatedEffect treatedMass scoreEffect scoreMass
      hpopulationMass
      (condExp_ae_eq_scoreVersion_of_ae_eq_aestronglyMeasurable_outcomeIntegrable
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := populationLaw) hsub treatedEffect scoreEffect
        hnumerator hnumeratorMeas hnumeratorOutcomeIntegrable)
      (condExp_ae_eq_scoreVersion_of_ae_eq_aestronglyMeasurable_outcomeIntegrable
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := populationLaw) hsub treatedMass scoreMass hmass
        hmassMeas hmassOutcomeIntegrable)

/--
Raw-outcome-integrability paired PATE/PATT identification from packaged
selection-density design records and a.e. score-space versions.
-/
theorem selectedWeightedIntegralPATE_PATT_eq_scorePATE_PATT_of_design_ae_scoreVersions_outcomeIntegrable
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
          (∫ sample, controlScoreVersion sample ∂populationLaw) ∧
      (∫ sample,
        (@designSurveyWeightReal Sample mSample selectedLaw populationLaw
          pattDesign) sample * treatedEffect sample
        ∂selectedLaw) /
        (∫ sample,
          (@designSurveyWeightReal Sample mSample selectedLaw populationLaw
            pattDesign) sample * treatedMass sample
          ∂selectedLaw) =
        (∫ sample, scoreEffect sample ∂populationLaw) /
          (∫ sample, scoreMass sample ∂populationLaw) := by
  constructor
  · exact
      selectedWeightedIntegralPATE_eq_scorePATE_of_design_ae_scoreVersions_outcomeIntegrable
        (mSample := mSample) (scoreSigma := scoreSigma)
        (selectedLaw := selectedLaw) (populationLaw := populationLaw)
        hsub treatedDesign controlDesign treatedOutcome controlOutcome
        treatedScoreVersion controlScoreVersion hpopulationOne htreatedAE
        hcontrolAE htreatedMeas hcontrolMeas htreatedOutcomeIntegrable
        hcontrolOutcomeIntegrable
  · exact
      selectedWeightedIntegralPATT_eq_scorePATT_of_design_ae_scoreVersions_outcomeIntegrable
        (mSample := mSample) (scoreSigma := scoreSigma)
        (selectedLaw := selectedLaw) (populationLaw := populationLaw)
        hsub pattDesign treatedEffect treatedMass scoreEffect scoreMass
        hpopulationMass hnumeratorAE hmassAE hnumeratorMeas hmassMeas
        hnumeratorOutcomeIntegrable hmassOutcomeIntegrable

end WDSM
end Matching
end StatInference
