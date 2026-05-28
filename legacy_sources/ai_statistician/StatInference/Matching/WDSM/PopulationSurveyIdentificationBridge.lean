import StatInference.Matching.WDSM.PopulationInverseSelectionIdentity

/-!
# Population survey identification bridge

This module composes population inverse-selection integral recovery with
score-sigma conditional-mean and score-version identification.  It gives the
direct theorem shape needed by WDSM population identification: selected-law
survey-weighted Hájek ratios recover score-space PATE/PATT targets once survey
integral recovery and score-identification hypotheses are supplied.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open scoped MeasureTheory

variable {Sample : Type*} [mSample : MeasurableSpace Sample]
variable {scoreSigma : MeasurableSpace Sample}
variable {selectedLaw populationLaw : Measure[mSample] Sample}

/--
Selected-law weighted Hájek PATE recovers the score-space PATE when
arm-specific survey integral recovery and score-sigma conditional-mean
versions both hold.
-/
theorem selectedWeightedIntegralPATE_eq_scorePATE_of_condExp_scoreVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (treatedWeight controlWeight treatedOutcome controlOutcome
      treatedScoreVersion controlScoreVersion : Sample -> Real)
    (treatedSamplingMass controlSamplingMass : Real)
    (htreatedTarget :
      (∫ sample, treatedWeight sample * treatedOutcome sample ∂selectedLaw) =
        (∫ sample, treatedOutcome sample ∂populationLaw) /
          treatedSamplingMass)
    (htreatedOne :
      (∫ sample, treatedWeight sample ∂selectedLaw) =
        1 / treatedSamplingMass)
    (hcontrolTarget :
      (∫ sample, controlWeight sample * controlOutcome sample ∂selectedLaw) =
        (∫ sample, controlOutcome sample ∂populationLaw) /
          controlSamplingMass)
    (hcontrolOne :
      (∫ sample, controlWeight sample ∂selectedLaw) =
        1 / controlSamplingMass)
    (htreatedSampling : treatedSamplingMass ≠ 0)
    (hcontrolSampling : controlSamplingMass ≠ 0)
    (htreatedCond :
      populationLaw[treatedOutcome | scoreSigma] =ᵐ[populationLaw]
        treatedScoreVersion)
    (hcontrolCond :
      populationLaw[controlOutcome | scoreSigma] =ᵐ[populationLaw]
        controlScoreVersion) :
    PATERepresentation.selectedHajekPATE
        (@pateRepresentationOfWeightedIntegralRecovery Sample mSample
          selectedLaw
          populationLaw treatedWeight controlWeight treatedOutcome
          controlOutcome treatedSamplingMass controlSamplingMass
          htreatedTarget htreatedOne hcontrolTarget hcontrolOne) =
      (∫ sample, treatedScoreVersion sample ∂populationLaw) -
        (∫ sample, controlScoreVersion sample ∂populationLaw) := by
  exact
    selectedHajekPATE_eq_scorePATE_of_condExp_scoreVersions
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := populationLaw) hsub
      (@pateRepresentationOfWeightedIntegralRecovery Sample mSample
        selectedLaw
        populationLaw treatedWeight controlWeight treatedOutcome controlOutcome
        treatedSamplingMass controlSamplingMass htreatedTarget htreatedOne
        hcontrolTarget hcontrolOne)
      htreatedSampling hcontrolSampling treatedOutcome controlOutcome
      treatedScoreVersion controlScoreVersion rfl rfl htreatedCond
      hcontrolCond

/--
Selected-law weighted Hájek PATT recovers the score-space PATT when survey
integral recovery and score-sigma conditional-mean versions hold for the
treated-effect numerator and treated-mass denominator.
-/
theorem selectedWeightedIntegralPATT_eq_scorePATT_of_condExp_scoreVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (surveyWeight treatedEffect treatedMass
      scoreEffect scoreMass : Sample -> Real)
    (samplingMass : Real)
    (hnumeratorRecovery :
      (∫ sample, surveyWeight sample * treatedEffect sample ∂selectedLaw) =
        (∫ sample, treatedEffect sample ∂populationLaw) / samplingMass)
    (hmassRecovery :
      (∫ sample, surveyWeight sample * treatedMass sample ∂selectedLaw) =
        (∫ sample, treatedMass sample ∂populationLaw) / samplingMass)
    (hsampling : samplingMass ≠ 0)
    (hpopulationMass :
      (∫ sample, treatedMass sample ∂populationLaw) ≠ 0)
    (hnumeratorCond :
      populationLaw[treatedEffect | scoreSigma] =ᵐ[populationLaw] scoreEffect)
    (hmassCond :
      populationLaw[treatedMass | scoreSigma] =ᵐ[populationLaw] scoreMass) :
    PATTRepresentation.selectedHajekPATT
        (@pattRepresentationOfWeightedIntegralRecovery Sample mSample
          selectedLaw populationLaw surveyWeight treatedEffect treatedMass
          samplingMass hnumeratorRecovery hmassRecovery) =
      (∫ sample, scoreEffect sample ∂populationLaw) /
        (∫ sample, scoreMass sample ∂populationLaw) := by
  exact
    selectedHajekPATT_eq_scorePATT_of_condExp_scoreVersions
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := populationLaw) hsub
      (@pattRepresentationOfWeightedIntegralRecovery Sample mSample
        selectedLaw populationLaw surveyWeight treatedEffect treatedMass
        samplingMass hnumeratorRecovery hmassRecovery)
      hsampling hpopulationMass treatedEffect treatedMass scoreEffect
      scoreMass rfl rfl hnumeratorCond hmassCond

/--
Paired selected-law weighted Hájek PATE/PATT recovery from conditional
score-space versions and survey integral recovery.
-/
theorem selectedWeightedIntegralPATE_PATT_eq_scorePATE_PATT_of_condExp_scoreVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (treatedWeight controlWeight surveyWeight treatedOutcome controlOutcome
      treatedEffect treatedMass treatedScoreVersion controlScoreVersion
      scoreEffect scoreMass : Sample -> Real)
    (treatedSamplingMass controlSamplingMass pattSamplingMass : Real)
    (htreatedTarget :
      (∫ sample, treatedWeight sample * treatedOutcome sample ∂selectedLaw) =
        (∫ sample, treatedOutcome sample ∂populationLaw) /
          treatedSamplingMass)
    (htreatedOne :
      (∫ sample, treatedWeight sample ∂selectedLaw) =
        1 / treatedSamplingMass)
    (hcontrolTarget :
      (∫ sample, controlWeight sample * controlOutcome sample ∂selectedLaw) =
        (∫ sample, controlOutcome sample ∂populationLaw) /
          controlSamplingMass)
    (hcontrolOne :
      (∫ sample, controlWeight sample ∂selectedLaw) =
        1 / controlSamplingMass)
    (hnumeratorRecovery :
      (∫ sample, surveyWeight sample * treatedEffect sample ∂selectedLaw) =
        (∫ sample, treatedEffect sample ∂populationLaw) / pattSamplingMass)
    (hmassRecovery :
      (∫ sample, surveyWeight sample * treatedMass sample ∂selectedLaw) =
        (∫ sample, treatedMass sample ∂populationLaw) / pattSamplingMass)
    (htreatedSampling : treatedSamplingMass ≠ 0)
    (hcontrolSampling : controlSamplingMass ≠ 0)
    (hpattSampling : pattSamplingMass ≠ 0)
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
    PATERepresentation.selectedHajekPATE
        (@pateRepresentationOfWeightedIntegralRecovery Sample mSample
          selectedLaw populationLaw treatedWeight controlWeight treatedOutcome
          controlOutcome treatedSamplingMass controlSamplingMass
          htreatedTarget htreatedOne hcontrolTarget hcontrolOne) =
        (∫ sample, treatedScoreVersion sample ∂populationLaw) -
          (∫ sample, controlScoreVersion sample ∂populationLaw) ∧
      PATTRepresentation.selectedHajekPATT
        (@pattRepresentationOfWeightedIntegralRecovery Sample mSample
          selectedLaw populationLaw surveyWeight treatedEffect treatedMass
          pattSamplingMass hnumeratorRecovery hmassRecovery) =
        (∫ sample, scoreEffect sample ∂populationLaw) /
          (∫ sample, scoreMass sample ∂populationLaw) := by
  constructor
  · exact
      selectedWeightedIntegralPATE_eq_scorePATE_of_condExp_scoreVersions
        (mSample := mSample) (scoreSigma := scoreSigma)
        (selectedLaw := selectedLaw) (populationLaw := populationLaw)
        hsub treatedWeight controlWeight treatedOutcome controlOutcome
        treatedScoreVersion controlScoreVersion treatedSamplingMass
        controlSamplingMass htreatedTarget htreatedOne hcontrolTarget
        hcontrolOne htreatedSampling hcontrolSampling htreatedCond
        hcontrolCond
  · exact
      selectedWeightedIntegralPATT_eq_scorePATT_of_condExp_scoreVersions
        (mSample := mSample) (scoreSigma := scoreSigma)
        (selectedLaw := selectedLaw) (populationLaw := populationLaw)
        hsub surveyWeight treatedEffect treatedMass scoreEffect scoreMass
        pattSamplingMass hnumeratorRecovery hmassRecovery hpattSampling
        hpopulationMass hnumeratorCond hmassCond

/--
Selected-law weighted Hájek PATE recovers the score-space PATE when survey
integral recovery holds and the potential outcomes agree a.e. with
score-sigma measurable, integrable score versions.
-/
theorem selectedWeightedIntegralPATE_eq_scorePATE_of_ae_scoreVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (treatedWeight controlWeight treatedOutcome controlOutcome
      treatedScoreVersion controlScoreVersion : Sample -> Real)
    (treatedSamplingMass controlSamplingMass : Real)
    (htreatedTarget :
      (∫ sample, treatedWeight sample * treatedOutcome sample ∂selectedLaw) =
        (∫ sample, treatedOutcome sample ∂populationLaw) /
          treatedSamplingMass)
    (htreatedOne :
      (∫ sample, treatedWeight sample ∂selectedLaw) =
        1 / treatedSamplingMass)
    (hcontrolTarget :
      (∫ sample, controlWeight sample * controlOutcome sample ∂selectedLaw) =
        (∫ sample, controlOutcome sample ∂populationLaw) /
          controlSamplingMass)
    (hcontrolOne :
      (∫ sample, controlWeight sample ∂selectedLaw) =
        1 / controlSamplingMass)
    (htreatedSampling : treatedSamplingMass ≠ 0)
    (hcontrolSampling : controlSamplingMass ≠ 0)
    (htreated :
      treatedOutcome =ᵐ[populationLaw] treatedScoreVersion)
    (hcontrol :
      controlOutcome =ᵐ[populationLaw] controlScoreVersion)
    (htreatedMeas :
      AEStronglyMeasurable[scoreSigma] treatedScoreVersion populationLaw)
    (hcontrolMeas :
      AEStronglyMeasurable[scoreSigma] controlScoreVersion populationLaw)
    (htreatedIntegrable : Integrable treatedScoreVersion populationLaw)
    (hcontrolIntegrable : Integrable controlScoreVersion populationLaw) :
    PATERepresentation.selectedHajekPATE
        (@pateRepresentationOfWeightedIntegralRecovery Sample mSample
          selectedLaw
          populationLaw treatedWeight controlWeight treatedOutcome
          controlOutcome treatedSamplingMass controlSamplingMass
          htreatedTarget htreatedOne hcontrolTarget hcontrolOne) =
      (∫ sample, treatedScoreVersion sample ∂populationLaw) -
        (∫ sample, controlScoreVersion sample ∂populationLaw) := by
  exact
    selectedHajekPATE_eq_scorePATE_of_ae_scoreVersions
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := populationLaw) hsub
      (@pateRepresentationOfWeightedIntegralRecovery Sample mSample
        selectedLaw
        populationLaw treatedWeight controlWeight treatedOutcome controlOutcome
        treatedSamplingMass controlSamplingMass htreatedTarget htreatedOne
        hcontrolTarget hcontrolOne)
      htreatedSampling hcontrolSampling treatedOutcome controlOutcome
      treatedScoreVersion controlScoreVersion rfl rfl htreated hcontrol
      htreatedMeas hcontrolMeas htreatedIntegrable hcontrolIntegrable

/--
Selected-law weighted Hájek PATT recovers the score-space PATT when survey
integral recovery holds and the numerator/denominator agree a.e. with
score-sigma measurable, integrable score versions.
-/
theorem selectedWeightedIntegralPATT_eq_scorePATT_of_ae_scoreVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (surveyWeight treatedEffect treatedMass
      scoreEffect scoreMass : Sample -> Real)
    (samplingMass : Real)
    (hnumeratorRecovery :
      (∫ sample, surveyWeight sample * treatedEffect sample ∂selectedLaw) =
        (∫ sample, treatedEffect sample ∂populationLaw) / samplingMass)
    (hmassRecovery :
      (∫ sample, surveyWeight sample * treatedMass sample ∂selectedLaw) =
        (∫ sample, treatedMass sample ∂populationLaw) / samplingMass)
    (hsampling : samplingMass ≠ 0)
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
    PATTRepresentation.selectedHajekPATT
        (@pattRepresentationOfWeightedIntegralRecovery Sample mSample
          selectedLaw populationLaw
          surveyWeight treatedEffect treatedMass samplingMass
          hnumeratorRecovery hmassRecovery) =
      (∫ sample, scoreEffect sample ∂populationLaw) /
        (∫ sample, scoreMass sample ∂populationLaw) := by
  exact
    selectedHajekPATT_eq_scorePATT_of_ae_scoreVersions
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := populationLaw) hsub
      (@pattRepresentationOfWeightedIntegralRecovery Sample mSample
        selectedLaw populationLaw
        surveyWeight treatedEffect treatedMass samplingMass hnumeratorRecovery
        hmassRecovery)
      hsampling hpopulationMass treatedEffect treatedMass scoreEffect
      scoreMass rfl rfl hnumeratorAE hmassAE hnumeratorMeas hmassMeas
      hnumeratorIntegrable hmassIntegrable

/--
Paired selected-law weighted Hájek PATE/PATT recovery from a.e. score-space
versions and survey integral recovery.
-/
theorem selectedWeightedIntegralPATE_PATT_eq_scorePATE_PATT_of_ae_scoreVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (treatedWeight controlWeight surveyWeight treatedOutcome controlOutcome
      treatedEffect treatedMass treatedScoreVersion controlScoreVersion
      scoreEffect scoreMass : Sample -> Real)
    (treatedSamplingMass controlSamplingMass pattSamplingMass : Real)
    (htreatedTarget :
      (∫ sample, treatedWeight sample * treatedOutcome sample ∂selectedLaw) =
        (∫ sample, treatedOutcome sample ∂populationLaw) /
          treatedSamplingMass)
    (htreatedOne :
      (∫ sample, treatedWeight sample ∂selectedLaw) =
        1 / treatedSamplingMass)
    (hcontrolTarget :
      (∫ sample, controlWeight sample * controlOutcome sample ∂selectedLaw) =
        (∫ sample, controlOutcome sample ∂populationLaw) /
          controlSamplingMass)
    (hcontrolOne :
      (∫ sample, controlWeight sample ∂selectedLaw) =
        1 / controlSamplingMass)
    (hnumeratorRecovery :
      (∫ sample, surveyWeight sample * treatedEffect sample ∂selectedLaw) =
        (∫ sample, treatedEffect sample ∂populationLaw) / pattSamplingMass)
    (hmassRecovery :
      (∫ sample, surveyWeight sample * treatedMass sample ∂selectedLaw) =
        (∫ sample, treatedMass sample ∂populationLaw) / pattSamplingMass)
    (htreatedSampling : treatedSamplingMass ≠ 0)
    (hcontrolSampling : controlSamplingMass ≠ 0)
    (hpattSampling : pattSamplingMass ≠ 0)
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
    (htreatedIntegrable : Integrable treatedScoreVersion populationLaw)
    (hcontrolIntegrable : Integrable controlScoreVersion populationLaw)
    (hnumeratorIntegrable : Integrable scoreEffect populationLaw)
    (hmassIntegrable : Integrable scoreMass populationLaw) :
    PATERepresentation.selectedHajekPATE
        (@pateRepresentationOfWeightedIntegralRecovery Sample mSample
          selectedLaw populationLaw treatedWeight controlWeight treatedOutcome
          controlOutcome treatedSamplingMass controlSamplingMass
          htreatedTarget htreatedOne hcontrolTarget hcontrolOne) =
        (∫ sample, treatedScoreVersion sample ∂populationLaw) -
          (∫ sample, controlScoreVersion sample ∂populationLaw) ∧
      PATTRepresentation.selectedHajekPATT
        (@pattRepresentationOfWeightedIntegralRecovery Sample mSample
          selectedLaw populationLaw surveyWeight treatedEffect treatedMass
          pattSamplingMass hnumeratorRecovery hmassRecovery) =
        (∫ sample, scoreEffect sample ∂populationLaw) /
          (∫ sample, scoreMass sample ∂populationLaw) := by
  constructor
  · exact
      selectedWeightedIntegralPATE_eq_scorePATE_of_ae_scoreVersions
        (mSample := mSample) (scoreSigma := scoreSigma)
        (selectedLaw := selectedLaw) (populationLaw := populationLaw)
        hsub treatedWeight controlWeight treatedOutcome controlOutcome
        treatedScoreVersion controlScoreVersion treatedSamplingMass
        controlSamplingMass htreatedTarget htreatedOne hcontrolTarget
        hcontrolOne htreatedSampling hcontrolSampling htreatedAE hcontrolAE
        htreatedMeas hcontrolMeas htreatedIntegrable hcontrolIntegrable
  · exact
      selectedWeightedIntegralPATT_eq_scorePATT_of_ae_scoreVersions
        (mSample := mSample) (scoreSigma := scoreSigma)
        (selectedLaw := selectedLaw) (populationLaw := populationLaw)
        hsub surveyWeight treatedEffect treatedMass scoreEffect scoreMass
        pattSamplingMass hnumeratorRecovery hmassRecovery hpattSampling
        hpopulationMass hnumeratorAE hmassAE hnumeratorMeas hmassMeas
        hnumeratorIntegrable hmassIntegrable

/--
Raw-outcome-integrability variant of selected-law weighted Hájek PATE
score-space recovery from a.e. score versions and survey integral recovery.
-/
theorem selectedWeightedIntegralPATE_eq_scorePATE_of_ae_scoreVersions_outcomeIntegrable
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (treatedWeight controlWeight treatedOutcome controlOutcome
      treatedScoreVersion controlScoreVersion : Sample -> Real)
    (treatedSamplingMass controlSamplingMass : Real)
    (htreatedTarget :
      (∫ sample, treatedWeight sample * treatedOutcome sample ∂selectedLaw) =
        (∫ sample, treatedOutcome sample ∂populationLaw) /
          treatedSamplingMass)
    (htreatedOne :
      (∫ sample, treatedWeight sample ∂selectedLaw) =
        1 / treatedSamplingMass)
    (hcontrolTarget :
      (∫ sample, controlWeight sample * controlOutcome sample ∂selectedLaw) =
        (∫ sample, controlOutcome sample ∂populationLaw) /
          controlSamplingMass)
    (hcontrolOne :
      (∫ sample, controlWeight sample ∂selectedLaw) =
        1 / controlSamplingMass)
    (htreatedSampling : treatedSamplingMass ≠ 0)
    (hcontrolSampling : controlSamplingMass ≠ 0)
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
    PATERepresentation.selectedHajekPATE
        (@pateRepresentationOfWeightedIntegralRecovery Sample mSample
          selectedLaw
          populationLaw treatedWeight controlWeight treatedOutcome
          controlOutcome treatedSamplingMass controlSamplingMass
          htreatedTarget htreatedOne hcontrolTarget hcontrolOne) =
      (∫ sample, treatedScoreVersion sample ∂populationLaw) -
        (∫ sample, controlScoreVersion sample ∂populationLaw) := by
  exact
    selectedHajekPATE_eq_scorePATE_of_ae_scoreVersions_outcomeIntegrable
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := populationLaw) hsub
      (@pateRepresentationOfWeightedIntegralRecovery Sample mSample
        selectedLaw
        populationLaw treatedWeight controlWeight treatedOutcome controlOutcome
        treatedSamplingMass controlSamplingMass htreatedTarget htreatedOne
        hcontrolTarget hcontrolOne)
      htreatedSampling hcontrolSampling treatedOutcome controlOutcome
      treatedScoreVersion controlScoreVersion rfl rfl htreated hcontrol
      htreatedMeas hcontrolMeas htreatedOutcomeIntegrable
      hcontrolOutcomeIntegrable

/--
Raw-outcome-integrability variant of selected-law weighted Hájek PATT
score-space recovery from a.e. score versions and survey integral recovery.
-/
theorem selectedWeightedIntegralPATT_eq_scorePATT_of_ae_scoreVersions_outcomeIntegrable
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (surveyWeight treatedEffect treatedMass
      scoreEffect scoreMass : Sample -> Real)
    (samplingMass : Real)
    (hnumeratorRecovery :
      (∫ sample, surveyWeight sample * treatedEffect sample ∂selectedLaw) =
        (∫ sample, treatedEffect sample ∂populationLaw) / samplingMass)
    (hmassRecovery :
      (∫ sample, surveyWeight sample * treatedMass sample ∂selectedLaw) =
        (∫ sample, treatedMass sample ∂populationLaw) / samplingMass)
    (hsampling : samplingMass ≠ 0)
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
    PATTRepresentation.selectedHajekPATT
        (@pattRepresentationOfWeightedIntegralRecovery Sample mSample
          selectedLaw populationLaw
          surveyWeight treatedEffect treatedMass samplingMass
          hnumeratorRecovery hmassRecovery) =
      (∫ sample, scoreEffect sample ∂populationLaw) /
        (∫ sample, scoreMass sample ∂populationLaw) := by
  exact
    selectedHajekPATT_eq_scorePATT_of_ae_scoreVersions_outcomeIntegrable
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := populationLaw) hsub
      (@pattRepresentationOfWeightedIntegralRecovery Sample mSample
        selectedLaw populationLaw
        surveyWeight treatedEffect treatedMass samplingMass hnumeratorRecovery
        hmassRecovery)
      hsampling hpopulationMass treatedEffect treatedMass scoreEffect
      scoreMass rfl rfl hnumeratorAE hmassAE hnumeratorMeas hmassMeas
      hnumeratorOutcomeIntegrable hmassOutcomeIntegrable

/--
Raw-outcome-integrability paired selected-law weighted Hájek PATE/PATT recovery
from a.e. score-space versions and survey integral recovery.
-/
theorem selectedWeightedIntegralPATE_PATT_eq_scorePATE_PATT_of_ae_scoreVersions_outcomeIntegrable
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (treatedWeight controlWeight surveyWeight treatedOutcome controlOutcome
      treatedEffect treatedMass treatedScoreVersion controlScoreVersion
      scoreEffect scoreMass : Sample -> Real)
    (treatedSamplingMass controlSamplingMass pattSamplingMass : Real)
    (htreatedTarget :
      (∫ sample, treatedWeight sample * treatedOutcome sample ∂selectedLaw) =
        (∫ sample, treatedOutcome sample ∂populationLaw) /
          treatedSamplingMass)
    (htreatedOne :
      (∫ sample, treatedWeight sample ∂selectedLaw) =
        1 / treatedSamplingMass)
    (hcontrolTarget :
      (∫ sample, controlWeight sample * controlOutcome sample ∂selectedLaw) =
        (∫ sample, controlOutcome sample ∂populationLaw) /
          controlSamplingMass)
    (hcontrolOne :
      (∫ sample, controlWeight sample ∂selectedLaw) =
        1 / controlSamplingMass)
    (hnumeratorRecovery :
      (∫ sample, surveyWeight sample * treatedEffect sample ∂selectedLaw) =
        (∫ sample, treatedEffect sample ∂populationLaw) / pattSamplingMass)
    (hmassRecovery :
      (∫ sample, surveyWeight sample * treatedMass sample ∂selectedLaw) =
        (∫ sample, treatedMass sample ∂populationLaw) / pattSamplingMass)
    (htreatedSampling : treatedSamplingMass ≠ 0)
    (hcontrolSampling : controlSamplingMass ≠ 0)
    (hpattSampling : pattSamplingMass ≠ 0)
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
    PATERepresentation.selectedHajekPATE
        (@pateRepresentationOfWeightedIntegralRecovery Sample mSample
          selectedLaw populationLaw treatedWeight controlWeight treatedOutcome
          controlOutcome treatedSamplingMass controlSamplingMass
          htreatedTarget htreatedOne hcontrolTarget hcontrolOne) =
        (∫ sample, treatedScoreVersion sample ∂populationLaw) -
          (∫ sample, controlScoreVersion sample ∂populationLaw) ∧
      PATTRepresentation.selectedHajekPATT
        (@pattRepresentationOfWeightedIntegralRecovery Sample mSample
          selectedLaw populationLaw surveyWeight treatedEffect treatedMass
          pattSamplingMass hnumeratorRecovery hmassRecovery) =
        (∫ sample, scoreEffect sample ∂populationLaw) /
          (∫ sample, scoreMass sample ∂populationLaw) := by
  constructor
  · exact
      selectedWeightedIntegralPATE_eq_scorePATE_of_ae_scoreVersions_outcomeIntegrable
        (mSample := mSample) (scoreSigma := scoreSigma)
        (selectedLaw := selectedLaw) (populationLaw := populationLaw)
        hsub treatedWeight controlWeight treatedOutcome controlOutcome
        treatedScoreVersion controlScoreVersion treatedSamplingMass
        controlSamplingMass htreatedTarget htreatedOne hcontrolTarget
        hcontrolOne htreatedSampling hcontrolSampling htreatedAE hcontrolAE
        htreatedMeas hcontrolMeas htreatedOutcomeIntegrable
        hcontrolOutcomeIntegrable
  · exact
      selectedWeightedIntegralPATT_eq_scorePATT_of_ae_scoreVersions_outcomeIntegrable
        (mSample := mSample) (scoreSigma := scoreSigma)
        (selectedLaw := selectedLaw) (populationLaw := populationLaw)
        hsub surveyWeight treatedEffect treatedMass scoreEffect scoreMass
        pattSamplingMass hnumeratorRecovery hmassRecovery hpattSampling
        hpopulationMass hnumeratorAE hmassAE hnumeratorMeas hmassMeas
        hnumeratorOutcomeIntegrable hmassOutcomeIntegrable

end WDSM
end Matching
end StatInference
