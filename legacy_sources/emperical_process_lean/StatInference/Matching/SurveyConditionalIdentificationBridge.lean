import StatInference.Matching.WDSM.ScoreVersionIdentificationBridge

/-!
# Survey-ratio conditional identification bridge for WDSM

This module composes the abstract inverse-selection Hájek ratio identities
with the score-sigma conditional-mean and score-version identification
bridges.  It is a population-representation layer: selected-sample
survey-weighted Hájek ratios recover score-space PATE/PATT targets once the
survey inverse-selection identities and score-space identification hypotheses
are available.
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
Selected-sample Hájek PATE recovers the score-space PATE when the
inverse-selection population targets are the potential-outcome integrals and
those outcomes have score-sigma conditional-mean versions.
-/
theorem selectedHajekPATE_eq_scorePATE_of_condExp_scoreVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (repr : PATERepresentation)
    (htreatedSampling : repr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : repr.control.sampling_mass ≠ 0)
    (treatedOutcome controlOutcome treatedScoreVersion controlScoreVersion :
      Sample -> Real)
    (hreprT :
      repr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw)
    (hreprC :
      repr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw)
    (htreated :
      sampleLaw[treatedOutcome | scoreSigma] =ᵐ[sampleLaw]
        treatedScoreVersion)
    (hcontrol :
      sampleLaw[controlOutcome | scoreSigma] =ᵐ[sampleLaw]
        controlScoreVersion) :
    repr.selectedHajekPATE =
      (∫ sample, treatedScoreVersion sample ∂sampleLaw) -
        (∫ sample, controlScoreVersion sample ∂sampleLaw) := by
  rw [PATERepresentation.selectedHajekPATE_eq_populationPATE repr
    htreatedSampling hcontrolSampling]
  simp [PATERepresentation.populationPATE]
  rw [hreprT, hreprC]
  exact
    populationPATE_integral_eq_scorePATE_of_condExp_ae_eq
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub treatedOutcome controlOutcome
      treatedScoreVersion controlScoreVersion htreated hcontrol

/--
Selected-sample Hájek PATT recovers the score-space PATT when the
inverse-selection population numerator and denominator are the corresponding
population integrals and both have score-sigma conditional-mean versions.
-/
theorem selectedHajekPATT_eq_scorePATT_of_condExp_scoreVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (repr : PATTRepresentation)
    (hsampling : repr.sampling_mass ≠ 0)
    (htreatedMass : repr.population_treated_mass ≠ 0)
    (treatedEffectNumerator treatedMass
      scoreEffectNumerator scoreTreatedMass : Sample -> Real)
    (hreprNumerator :
      repr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      repr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw)
    (hnumerator :
      sampleLaw[treatedEffectNumerator | scoreSigma] =ᵐ[sampleLaw]
        scoreEffectNumerator)
    (hmass :
      sampleLaw[treatedMass | scoreSigma] =ᵐ[sampleLaw] scoreTreatedMass) :
    repr.selectedHajekPATT =
      (∫ sample, scoreEffectNumerator sample ∂sampleLaw) /
        (∫ sample, scoreTreatedMass sample ∂sampleLaw) := by
  rw [PATTRepresentation.selectedHajekPATT_eq_populationPATT repr
    hsampling htreatedMass]
  simp [PATTRepresentation.populationPATT]
  rw [hreprNumerator, hreprMass]
  rw [integral_eq_scoreVersion_of_condExp_ae_eq
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub treatedEffectNumerator scoreEffectNumerator hnumerator]
  rw [integral_eq_scoreVersion_of_condExp_ae_eq
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub treatedMass scoreTreatedMass hmass]

/--
Selected-sample Hájek PATE recovers the score-space PATE when the
potential-outcome integrals agree a.e. with score-sigma measurable, integrable
score versions.
-/
theorem selectedHajekPATE_eq_scorePATE_of_ae_scoreVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (repr : PATERepresentation)
    (htreatedSampling : repr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : repr.control.sampling_mass ≠ 0)
    (treatedOutcome controlOutcome treatedScoreVersion controlScoreVersion :
      Sample -> Real)
    (hreprT :
      repr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw)
    (hreprC :
      repr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw)
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
    repr.selectedHajekPATE =
      (∫ sample, treatedScoreVersion sample ∂sampleLaw) -
        (∫ sample, controlScoreVersion sample ∂sampleLaw) := by
  rw [PATERepresentation.selectedHajekPATE_eq_populationPATE repr
    htreatedSampling hcontrolSampling]
  simp [PATERepresentation.populationPATE]
  rw [hreprT, hreprC]
  exact
    populationPATE_integral_eq_scorePATE_of_ae_eq_scoreVersions
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub treatedOutcome controlOutcome
      treatedScoreVersion controlScoreVersion htreated hcontrol htreatedMeas
      hcontrolMeas htreatedIntegrable hcontrolIntegrable

/--
Selected-sample Hájek PATT recovers the score-space PATT when the numerator
and denominator agree a.e. with score-sigma measurable, integrable score
versions.
-/
theorem selectedHajekPATT_eq_scorePATT_of_ae_scoreVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (repr : PATTRepresentation)
    (hsampling : repr.sampling_mass ≠ 0)
    (htreatedMass : repr.population_treated_mass ≠ 0)
    (treatedEffectNumerator treatedMass
      scoreEffectNumerator scoreTreatedMass : Sample -> Real)
    (hreprNumerator :
      repr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      repr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw)
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
    repr.selectedHajekPATT =
      (∫ sample, scoreEffectNumerator sample ∂sampleLaw) /
        (∫ sample, scoreTreatedMass sample ∂sampleLaw) := by
  rw [PATTRepresentation.selectedHajekPATT_eq_populationPATT repr
    hsampling htreatedMass]
  simp [PATTRepresentation.populationPATT]
  rw [hreprNumerator, hreprMass]
  rw [integral_eq_scoreVersion_of_ae_eq_scoreVersion
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub treatedEffectNumerator scoreEffectNumerator hnumerator
    hnumeratorMeas hnumeratorIntegrable]
  rw [integral_eq_scoreVersion_of_ae_eq_scoreVersion
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub treatedMass scoreTreatedMass hmass hmassMeas hmassIntegrable]

end WDSM
end Matching
end StatInference
