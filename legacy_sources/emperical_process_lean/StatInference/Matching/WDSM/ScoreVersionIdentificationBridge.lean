import StatInference.Matching.WDSM.ConditionalIdentificationBridge

/-!
# Score-version identification bridge for WDSM population targets

The finite score-cell layer often produces candidate score-space outcome
versions directly.  This module turns almost-everywhere equality to those
score versions, plus score-sigma measurability and integrability, into the
same PATE and PATT mean-identification interfaces used by the conditional
identification bridge.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open scoped MeasureTheory

variable {Sample : Type*} [mSample : MeasurableSpace Sample]
variable {scoreSigma : MeasurableSpace Sample}
variable {sampleLaw : Measure[mSample] Sample}

/--
If treated and control outcomes agree almost everywhere with score-space
versions, then the population PATE contrast equals the score-space contrast.
-/
theorem populationPATE_integral_eq_scorePATE_of_ae_eq_scoreVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (treatedOutcome controlOutcome treatedScoreVersion controlScoreVersion :
      Sample -> Real)
    (htreated :
      treatedOutcome =ᵐ[sampleLaw] treatedScoreVersion)
    (hcontrol :
      controlOutcome =ᵐ[sampleLaw] controlScoreVersion)
    (htreatedMeas :
      AEStronglyMeasurable[scoreSigma] treatedScoreVersion sampleLaw)
    (hcontrolMeas :
      AEStronglyMeasurable[scoreSigma] controlScoreVersion sampleLaw)
    (htreatedIntegrable : Integrable treatedScoreVersion sampleLaw)
    (hcontrolIntegrable : Integrable controlScoreVersion sampleLaw) :
    (∫ sample, treatedOutcome sample ∂sampleLaw) -
        (∫ sample, controlOutcome sample ∂sampleLaw) =
      (∫ sample, treatedScoreVersion sample ∂sampleLaw) -
        (∫ sample, controlScoreVersion sample ∂sampleLaw) := by
  rw [integral_eq_scoreVersion_of_ae_eq_scoreVersion
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub treatedOutcome treatedScoreVersion htreated htreatedMeas
    htreatedIntegrable]
  rw [integral_eq_scoreVersion_of_ae_eq_scoreVersion
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub controlOutcome controlScoreVersion hcontrol hcontrolMeas
    hcontrolIntegrable]

/--
Construct the PATE arm-mean identification interface from a.e. score-space
versions of the treated and control potential outcomes.
-/
noncomputable def pateArmMeanIdentificationOfAEScoreVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (treatedOutcome controlOutcome treatedScoreVersion controlScoreVersion :
      Sample -> Real)
    (htreated :
      treatedOutcome =ᵐ[sampleLaw] treatedScoreVersion)
    (hcontrol :
      controlOutcome =ᵐ[sampleLaw] controlScoreVersion)
    (htreatedMeas :
      AEStronglyMeasurable[scoreSigma] treatedScoreVersion sampleLaw)
    (hcontrolMeas :
      AEStronglyMeasurable[scoreSigma] controlScoreVersion sampleLaw)
    (htreatedIntegrable : Integrable treatedScoreVersion sampleLaw)
    (hcontrolIntegrable : Integrable controlScoreVersion sampleLaw) :
    PATEArmMeanIdentification where
  treated_population_mean := ∫ sample, treatedOutcome sample ∂sampleLaw
  control_population_mean := ∫ sample, controlOutcome sample ∂sampleLaw
  treated_score_mean := ∫ sample, treatedScoreVersion sample ∂sampleLaw
  control_score_mean := ∫ sample, controlScoreVersion sample ∂sampleLaw
  treated_identification := by
    symm
    exact
      integral_eq_scoreVersion_of_ae_eq_scoreVersion
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub treatedOutcome treatedScoreVersion
        htreated htreatedMeas htreatedIntegrable
  control_identification := by
    symm
    exact
      integral_eq_scoreVersion_of_ae_eq_scoreVersion
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub controlOutcome controlScoreVersion
        hcontrol hcontrolMeas hcontrolIntegrable

/--
The PATE interface generated from a.e. score-space versions recovers the
population PATE.
-/
theorem scorePATE_eq_populationPATE_of_ae_scoreVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (treatedOutcome controlOutcome treatedScoreVersion controlScoreVersion :
      Sample -> Real)
    (htreated :
      treatedOutcome =ᵐ[sampleLaw] treatedScoreVersion)
    (hcontrol :
      controlOutcome =ᵐ[sampleLaw] controlScoreVersion)
    (htreatedMeas :
      AEStronglyMeasurable[scoreSigma] treatedScoreVersion sampleLaw)
    (hcontrolMeas :
      AEStronglyMeasurable[scoreSigma] controlScoreVersion sampleLaw)
    (htreatedIntegrable : Integrable treatedScoreVersion sampleLaw)
    (hcontrolIntegrable : Integrable controlScoreVersion sampleLaw) :
    PATEArmMeanIdentification.scorePATE
        (pateArmMeanIdentificationOfAEScoreVersions
          (mSample := mSample) (scoreSigma := scoreSigma)
          (sampleLaw := sampleLaw) hsub treatedOutcome controlOutcome
          treatedScoreVersion controlScoreVersion htreated hcontrol
          htreatedMeas hcontrolMeas htreatedIntegrable hcontrolIntegrable) =
      PATEArmMeanIdentification.populationPATE
        (pateArmMeanIdentificationOfAEScoreVersions
          (mSample := mSample) (scoreSigma := scoreSigma)
          (sampleLaw := sampleLaw) hsub treatedOutcome controlOutcome
          treatedScoreVersion controlScoreVersion htreated hcontrol
          htreatedMeas hcontrolMeas htreatedIntegrable hcontrolIntegrable) := by
  exact
    PATEArmMeanIdentification.scorePATE_eq_populationPATE
      (pateArmMeanIdentificationOfAEScoreVersions
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub treatedOutcome controlOutcome
        treatedScoreVersion controlScoreVersion htreated hcontrol
        htreatedMeas hcontrolMeas htreatedIntegrable hcontrolIntegrable)

/--
Construct the PATT mean-identification interface from a.e. score-space versions
of the treated-effect numerator and treated-mass denominator.
-/
noncomputable def pattMeanIdentificationOfAEScoreVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (treatedEffectNumerator treatedMass
      scoreEffectNumerator scoreTreatedMass : Sample -> Real)
    (hnumerator :
      treatedEffectNumerator =ᵐ[sampleLaw] scoreEffectNumerator)
    (hmass :
      treatedMass =ᵐ[sampleLaw] scoreTreatedMass)
    (hnumeratorMeas :
      AEStronglyMeasurable[scoreSigma] scoreEffectNumerator sampleLaw)
    (hmassMeas :
      AEStronglyMeasurable[scoreSigma] scoreTreatedMass sampleLaw)
    (hnumeratorIntegrable : Integrable scoreEffectNumerator sampleLaw)
    (hmassIntegrable : Integrable scoreTreatedMass sampleLaw) :
    PATTMeanIdentification where
  population_treated_effect_numerator :=
    ∫ sample, treatedEffectNumerator sample ∂sampleLaw
  population_treated_mass := ∫ sample, treatedMass sample ∂sampleLaw
  score_treated_effect_numerator :=
    ∫ sample, scoreEffectNumerator sample ∂sampleLaw
  score_treated_mass := ∫ sample, scoreTreatedMass sample ∂sampleLaw
  numerator_identification := by
    symm
    exact
      integral_eq_scoreVersion_of_ae_eq_scoreVersion
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub treatedEffectNumerator
        scoreEffectNumerator hnumerator hnumeratorMeas hnumeratorIntegrable
  mass_identification := by
    symm
    exact
      integral_eq_scoreVersion_of_ae_eq_scoreVersion
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub treatedMass scoreTreatedMass hmass
        hmassMeas hmassIntegrable

/--
The PATT interface generated from a.e. score-space versions recovers the
population PATT ratio.
-/
theorem scorePATT_eq_populationPATT_of_ae_scoreVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (treatedEffectNumerator treatedMass
      scoreEffectNumerator scoreTreatedMass : Sample -> Real)
    (hnumerator :
      treatedEffectNumerator =ᵐ[sampleLaw] scoreEffectNumerator)
    (hmass :
      treatedMass =ᵐ[sampleLaw] scoreTreatedMass)
    (hnumeratorMeas :
      AEStronglyMeasurable[scoreSigma] scoreEffectNumerator sampleLaw)
    (hmassMeas :
      AEStronglyMeasurable[scoreSigma] scoreTreatedMass sampleLaw)
    (hnumeratorIntegrable : Integrable scoreEffectNumerator sampleLaw)
    (hmassIntegrable : Integrable scoreTreatedMass sampleLaw) :
    PATTMeanIdentification.scorePATT
        (pattMeanIdentificationOfAEScoreVersions
          (mSample := mSample) (scoreSigma := scoreSigma)
          (sampleLaw := sampleLaw) hsub treatedEffectNumerator treatedMass
          scoreEffectNumerator scoreTreatedMass hnumerator hmass
          hnumeratorMeas hmassMeas hnumeratorIntegrable hmassIntegrable) =
      PATTMeanIdentification.populationPATT
        (pattMeanIdentificationOfAEScoreVersions
          (mSample := mSample) (scoreSigma := scoreSigma)
          (sampleLaw := sampleLaw) hsub treatedEffectNumerator treatedMass
          scoreEffectNumerator scoreTreatedMass hnumerator hmass
          hnumeratorMeas hmassMeas hnumeratorIntegrable hmassIntegrable) := by
  exact
    PATTMeanIdentification.scorePATT_eq_populationPATT
      (pattMeanIdentificationOfAEScoreVersions
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub treatedEffectNumerator treatedMass
        scoreEffectNumerator scoreTreatedMass hnumerator hmass hnumeratorMeas
        hmassMeas hnumeratorIntegrable hmassIntegrable)

end WDSM
end Matching
end StatInference
