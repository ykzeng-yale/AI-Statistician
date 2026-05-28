import StatInference.Matching.WDSM.PopulationSelectionDensityDesignRepresentation
import StatInference.Matching.WDSM.SurveyConditionalIdentificationBridge

/-!
# Population selection-density design score representations

This module combines the representation constructors from
`PopulationSelectionDensityDesignRepresentation` with the conditional
score-space identification bridge.  It proves score-space PATE/PATT
identification directly for the abstract representations built from packaged
selection-density design records.
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
records recovers the score-space PATE when the outcomes have score-sigma
conditional-mean versions.
-/
theorem selectedHajekPATE_of_selectionDensityDesign_eq_scorePATE_condExp
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
    selectedHajekPATE_eq_scorePATE_of_condExp_scoreVersions
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := populationLaw) hsub repr htreatedSampling
      hcontrolSampling treatedOutcome controlOutcome treatedScoreVersion
      controlScoreVersion hreprT hreprC htreatedCond hcontrolCond

/--
The PATT representation built from a selection-density design record recovers
the score-space PATT when the numerator and denominator have score-sigma
conditional-mean versions.
-/
theorem selectedHajekPATT_of_selectionDensityDesign_eq_scorePATT_condExp
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
    selectedHajekPATT_eq_scorePATT_of_condExp_scoreVersions
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := populationLaw) hsub repr hsampling htreatedMass
      treatedEffect treatedMass scoreEffect scoreMass hreprNumerator hreprMass
      hnumeratorCond hmassCond

/--
The PATE representation built from arm-specific selection-density design
records recovers the score-space PATE from a.e. score versions and raw outcome
integrability.
-/
theorem selectedHajekPATE_of_selectionDensityDesign_eq_scorePATE_ae_scoreVersions_outcomeIntegrable
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
    (htreatedIntegrable : Integrable treatedOutcome populationLaw)
    (hcontrolIntegrable : Integrable controlOutcome populationLaw) :
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
    selectedHajekPATE_eq_scorePATE_of_ae_scoreVersions_outcomeIntegrable
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := populationLaw) hsub repr htreatedSampling
      hcontrolSampling treatedOutcome controlOutcome treatedScoreVersion
      controlScoreVersion hreprT hreprC htreated hcontrol htreatedMeas
      hcontrolMeas htreatedIntegrable hcontrolIntegrable

/--
The PATT representation built from a selection-density design record recovers
the score-space PATT from a.e. score versions and raw outcome integrability.
-/
theorem selectedHajekPATT_of_selectionDensityDesign_eq_scorePATT_ae_scoreVersions_outcomeIntegrable
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (treatedEffect treatedMass scoreEffect scoreMass : Sample -> Real)
    (hpopulationMass :
      (∫ sample, treatedMass sample ∂populationLaw) ≠ 0)
    (heffect :
      treatedEffect =ᵐ[populationLaw] scoreEffect)
    (hmass :
      treatedMass =ᵐ[populationLaw] scoreMass)
    (heffectMeas :
      AEStronglyMeasurable[scoreSigma] scoreEffect populationLaw)
    (hmassMeas :
      AEStronglyMeasurable[scoreSigma] scoreMass populationLaw)
    (heffectIntegrable : Integrable treatedEffect populationLaw)
    (hmassIntegrable : Integrable treatedMass populationLaw) :
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
    selectedHajekPATT_eq_scorePATT_of_ae_scoreVersions_outcomeIntegrable
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := populationLaw) hsub repr hsampling htreatedMass
      treatedEffect treatedMass scoreEffect scoreMass hreprNumerator
      hreprMass heffect hmass heffectMeas hmassMeas heffectIntegrable
      hmassIntegrable

/--
Paired PATE/PATT score-space identification from packaged selection-density
design records and conditional score-space mean versions.
-/
theorem selectedHajekPATE_PATT_of_selectionDensityDesign_eq_scorePATE_PATT_condExp
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
    PATERepresentation.selectedHajekPATE
        (@pateRepresentationOfSelectionDensityDesign Sample mSample
          selectedLaw populationLaw treatedDesign controlDesign treatedOutcome
          controlOutcome hpopulationOne) =
        (∫ sample, treatedScoreVersion sample ∂populationLaw) -
          (∫ sample, controlScoreVersion sample ∂populationLaw) ∧
      PATTRepresentation.selectedHajekPATT
        (@pattRepresentationOfSelectionDensityDesign Sample mSample
          selectedLaw populationLaw pattDesign treatedEffect treatedMass) =
        (∫ sample, scoreEffect sample ∂populationLaw) /
          (∫ sample, scoreMass sample ∂populationLaw) := by
  constructor
  · exact
      selectedHajekPATE_of_selectionDensityDesign_eq_scorePATE_condExp
        (mSample := mSample) (scoreSigma := scoreSigma)
        (selectedLaw := selectedLaw) (populationLaw := populationLaw)
        hsub treatedDesign controlDesign treatedOutcome controlOutcome
        treatedScoreVersion controlScoreVersion hpopulationOne htreatedCond
        hcontrolCond
  · exact
      selectedHajekPATT_of_selectionDensityDesign_eq_scorePATT_condExp
        (mSample := mSample) (scoreSigma := scoreSigma)
        (selectedLaw := selectedLaw) (populationLaw := populationLaw)
        hsub pattDesign treatedEffect treatedMass scoreEffect scoreMass
        hpopulationMass hnumeratorCond hmassCond

/--
Paired PATE/PATT score-space identification from packaged selection-density
design records, a.e. score versions, and raw outcome integrability.
-/
theorem selectedHajekPATE_PATT_of_selectionDensityDesign_eq_scorePATE_PATT_ae_scoreVersions_outcomeIntegrable
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
    (htreated :
      treatedOutcome =ᵐ[populationLaw] treatedScoreVersion)
    (hcontrol :
      controlOutcome =ᵐ[populationLaw] controlScoreVersion)
    (heffect :
      treatedEffect =ᵐ[populationLaw] scoreEffect)
    (hmass :
      treatedMass =ᵐ[populationLaw] scoreMass)
    (htreatedMeas :
      AEStronglyMeasurable[scoreSigma] treatedScoreVersion populationLaw)
    (hcontrolMeas :
      AEStronglyMeasurable[scoreSigma] controlScoreVersion populationLaw)
    (heffectMeas :
      AEStronglyMeasurable[scoreSigma] scoreEffect populationLaw)
    (hmassMeas :
      AEStronglyMeasurable[scoreSigma] scoreMass populationLaw)
    (htreatedIntegrable : Integrable treatedOutcome populationLaw)
    (hcontrolIntegrable : Integrable controlOutcome populationLaw)
    (heffectIntegrable : Integrable treatedEffect populationLaw)
    (hmassIntegrable : Integrable treatedMass populationLaw) :
    PATERepresentation.selectedHajekPATE
        (@pateRepresentationOfSelectionDensityDesign Sample mSample
          selectedLaw populationLaw treatedDesign controlDesign treatedOutcome
          controlOutcome hpopulationOne) =
        (∫ sample, treatedScoreVersion sample ∂populationLaw) -
          (∫ sample, controlScoreVersion sample ∂populationLaw) ∧
      PATTRepresentation.selectedHajekPATT
        (@pattRepresentationOfSelectionDensityDesign Sample mSample
          selectedLaw populationLaw pattDesign treatedEffect treatedMass) =
        (∫ sample, scoreEffect sample ∂populationLaw) /
          (∫ sample, scoreMass sample ∂populationLaw) := by
  constructor
  · exact
      selectedHajekPATE_of_selectionDensityDesign_eq_scorePATE_ae_scoreVersions_outcomeIntegrable
        (mSample := mSample) (scoreSigma := scoreSigma)
        (selectedLaw := selectedLaw) (populationLaw := populationLaw)
        hsub treatedDesign controlDesign treatedOutcome controlOutcome
        treatedScoreVersion controlScoreVersion hpopulationOne htreated
        hcontrol htreatedMeas hcontrolMeas htreatedIntegrable
        hcontrolIntegrable
  · exact
      selectedHajekPATT_of_selectionDensityDesign_eq_scorePATT_ae_scoreVersions_outcomeIntegrable
        (mSample := mSample) (scoreSigma := scoreSigma)
        (selectedLaw := selectedLaw) (populationLaw := populationLaw)
        hsub pattDesign treatedEffect treatedMass scoreEffect scoreMass
        hpopulationMass heffect hmass heffectMeas hmassMeas
        heffectIntegrable hmassIntegrable

end WDSM
end Matching
end StatInference
