import StatInference.Matching.WDSM.PopulationSelectionDensityDesignRepresentation
import StatInference.Matching.WDSM.SurveyConditionalIdentificationBridge

/-!
# Population selection-density design a.e. score representations

This module is the a.e.-score-version companion to
`PopulationSelectionDensityDesignScoreRepresentation`.  It proves score-space
PATE/PATT identification for the abstract representations built from packaged
selection-density design records when the target functions agree a.e. with
score-sigma measurable, integrable score versions.
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
The PATE representation built from arm-specific selection-density design
records recovers the score-space PATE when the outcomes agree a.e. with
score-sigma measurable, integrable score versions.
-/
theorem selectedHajekPATE_of_selectionDensityDesign_eq_scorePATE_aeScoreVersions
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
    PATERepresentation.selectedHajekPATE
        (@pateRepresentationOfSelectionDensityDesign Sample mSample
          selectedLaw populationLaw treatedDesign controlDesign treatedOutcome
          controlOutcome hpopulationOne) =
      (∫ sample, treatedScoreVersion sample ∂populationLaw) -
        (∫ sample, controlScoreVersion sample ∂populationLaw) := by
  let repr :=
    @pateRepresentationOfSelectionDensityDesign Sample mSample selectedLaw
      populationLaw treatedDesign controlDesign treatedOutcome controlOutcome
      hpopulationOne
  have htreatedSampling : repr.treated.sampling_mass ≠ 0 := by
    simpa [repr, pateRepresentationOfSelectionDensityDesign,
      pateRepresentationOfWeightedIntegralRecovery,
      inverseSelectionIdentityOfWeightedIntegralRecovery] using
      (ne_of_gt
        (@PopulationSelectionDensityDesign.sampling_pos Sample mSample
          selectedLaw populationLaw treatedDesign))
  have hcontrolSampling : repr.control.sampling_mass ≠ 0 := by
    simpa [repr, pateRepresentationOfSelectionDensityDesign,
      pateRepresentationOfWeightedIntegralRecovery,
      inverseSelectionIdentityOfWeightedIntegralRecovery] using
      (ne_of_gt
        (@PopulationSelectionDensityDesign.sampling_pos Sample mSample
          selectedLaw populationLaw controlDesign))
  have hreprT :
      repr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂populationLaw := by
    simp [repr, pateRepresentationOfSelectionDensityDesign,
      pateRepresentationOfWeightedIntegralRecovery,
      inverseSelectionIdentityOfWeightedIntegralRecovery]
  have hreprC :
      repr.control.population_target =
        ∫ sample, controlOutcome sample ∂populationLaw := by
    simp [repr, pateRepresentationOfSelectionDensityDesign,
      pateRepresentationOfWeightedIntegralRecovery,
      inverseSelectionIdentityOfWeightedIntegralRecovery]
  simpa [repr] using
    selectedHajekPATE_eq_scorePATE_of_ae_scoreVersions
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := populationLaw) hsub repr htreatedSampling
      hcontrolSampling treatedOutcome controlOutcome treatedScoreVersion
      controlScoreVersion hreprT hreprC htreatedAE hcontrolAE htreatedMeas
      hcontrolMeas htreatedIntegrable hcontrolIntegrable

/--
The PATT representation built from a selection-density design record recovers
the score-space PATT when the numerator and denominator agree a.e. with
score-sigma measurable, integrable score versions.
-/
theorem selectedHajekPATT_of_selectionDensityDesign_eq_scorePATT_aeScoreVersions
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
    PATTRepresentation.selectedHajekPATT
        (@pattRepresentationOfSelectionDensityDesign Sample mSample
          selectedLaw populationLaw design treatedEffect treatedMass) =
      (∫ sample, scoreEffect sample ∂populationLaw) /
        (∫ sample, scoreMass sample ∂populationLaw) := by
  let repr :=
    @pattRepresentationOfSelectionDensityDesign Sample mSample selectedLaw
      populationLaw design treatedEffect treatedMass
  have hsampling : repr.sampling_mass ≠ 0 := by
    simpa [repr, pattRepresentationOfSelectionDensityDesign,
      pattRepresentationOfWeightedIntegralRecovery] using
      (ne_of_gt
        (@PopulationSelectionDensityDesign.sampling_pos Sample mSample
          selectedLaw populationLaw design))
  have hreprNumerator :
      repr.population_treated_effect_numerator =
        ∫ sample, treatedEffect sample ∂populationLaw := by
    simp [repr, pattRepresentationOfSelectionDensityDesign,
      pattRepresentationOfWeightedIntegralRecovery]
  have hreprMass :
      repr.population_treated_mass =
        ∫ sample, treatedMass sample ∂populationLaw := by
    simp [repr, pattRepresentationOfSelectionDensityDesign,
      pattRepresentationOfWeightedIntegralRecovery]
  have htreatedMass : repr.population_treated_mass ≠ 0 := by
    simpa [hreprMass] using hpopulationMass
  simpa [repr] using
    selectedHajekPATT_eq_scorePATT_of_ae_scoreVersions
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := populationLaw) hsub repr hsampling htreatedMass
      treatedEffect treatedMass scoreEffect scoreMass hreprNumerator hreprMass
      hnumeratorAE hmassAE hnumeratorMeas hmassMeas hnumeratorIntegrable
      hmassIntegrable

end WDSM
end Matching
end StatInference
