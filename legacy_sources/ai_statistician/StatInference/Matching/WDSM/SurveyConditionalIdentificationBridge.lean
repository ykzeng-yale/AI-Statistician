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
The abstract PATE population target equals the score-space PATE when its arm
targets are the potential-outcome integrals and those outcomes have
score-sigma conditional-mean versions.
-/
theorem populationPATE_eq_scorePATE_of_condExp_scoreVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (repr : PATERepresentation)
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
    repr.populationPATE =
      (∫ sample, treatedScoreVersion sample ∂sampleLaw) -
        (∫ sample, controlScoreVersion sample ∂sampleLaw) := by
  simp [PATERepresentation.populationPATE]
  rw [hreprT, hreprC]
  exact
    populationPATE_integral_eq_scorePATE_of_condExp_ae_eq
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub treatedOutcome controlOutcome
      treatedScoreVersion controlScoreVersion htreated hcontrol

/--
The abstract PATT population target equals the score-space PATT when its
numerator and denominator targets are population integrals with score-sigma
conditional-mean versions.
-/
theorem populationPATT_eq_scorePATT_of_condExp_scoreVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (repr : PATTRepresentation)
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
    repr.populationPATT =
      (∫ sample, scoreEffectNumerator sample ∂sampleLaw) /
        (∫ sample, scoreTreatedMass sample ∂sampleLaw) := by
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
  exact
    populationPATE_eq_scorePATE_of_condExp_scoreVersions
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub repr treatedOutcome controlOutcome
      treatedScoreVersion controlScoreVersion hreprT hreprC
      htreated hcontrol

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
  exact
    populationPATT_eq_scorePATT_of_condExp_scoreVersions
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub repr treatedEffectNumerator treatedMass
      scoreEffectNumerator scoreTreatedMass hreprNumerator hreprMass
      hnumerator hmass

/--
Paired selected-sample Hájek PATE/PATT recovery from conditional score-space
versions at the abstract representation layer.
-/
theorem selectedHajekPATE_PATT_eq_scorePATE_PATT_of_condExp_scoreVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (htreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : pateRepr.control.sampling_mass ≠ 0)
    (hpattSampling : pattRepr.sampling_mass ≠ 0)
    (hpattMass : pattRepr.population_treated_mass ≠ 0)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass
      treatedScoreVersion controlScoreVersion scoreEffectNumerator
      scoreTreatedMass : Sample -> Real)
    (hreprT :
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw)
    (hreprC :
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw)
    (hreprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw)
    (htreated :
      sampleLaw[treatedOutcome | scoreSigma] =ᵐ[sampleLaw]
        treatedScoreVersion)
    (hcontrol :
      sampleLaw[controlOutcome | scoreSigma] =ᵐ[sampleLaw]
        controlScoreVersion)
    (hnumerator :
      sampleLaw[treatedEffectNumerator | scoreSigma] =ᵐ[sampleLaw]
        scoreEffectNumerator)
    (hmass :
      sampleLaw[treatedMass | scoreSigma] =ᵐ[sampleLaw] scoreTreatedMass) :
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedScoreVersion sample ∂sampleLaw) -
          (∫ sample, controlScoreVersion sample ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample, scoreEffectNumerator sample ∂sampleLaw) /
          (∫ sample, scoreTreatedMass sample ∂sampleLaw) := by
  constructor
  · exact
      selectedHajekPATE_eq_scorePATE_of_condExp_scoreVersions
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pateRepr htreatedSampling
        hcontrolSampling treatedOutcome controlOutcome treatedScoreVersion
        controlScoreVersion hreprT hreprC htreated hcontrol
  · exact
      selectedHajekPATT_eq_scorePATT_of_condExp_scoreVersions
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pattRepr hpattSampling hpattMass
        treatedEffectNumerator treatedMass scoreEffectNumerator
        scoreTreatedMass hreprNumerator hreprMass hnumerator hmass

/--
Selected-Hájek PATE/PATT recovery from transported latent/reference targets.
The representation equalities and PATT mass side condition are stated for the
transported targets; Lean recovers the observed-outcome representation and
conditional-mean premises by a.e. transport.
-/
theorem selectedHajekPATE_PATT_eq_scorePATE_PATT_of_condExp_scoreVersions_targetTransport_targetRepresentation
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (htreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : pateRepr.control.sampling_mass ≠ 0)
    (hpattSampling : pattRepr.sampling_mass ≠ 0)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass
      treatedTarget controlTarget effectTarget massTarget
      treatedScoreVersion controlScoreVersion scoreEffectNumerator
      scoreTreatedMass : Sample -> Real)
    (hreprT :
      pateRepr.treated.population_target =
        ∫ sample, treatedTarget sample ∂sampleLaw)
    (hreprC :
      pateRepr.control.population_target =
        ∫ sample, controlTarget sample ∂sampleLaw)
    (hreprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, effectTarget sample ∂sampleLaw)
    (hreprMass :
      pattRepr.population_treated_mass =
        ∫ sample, massTarget sample ∂sampleLaw)
    (hmassTargetNonzero :
      (∫ sample, massTarget sample ∂sampleLaw) ≠ 0)
    (htreatedTransport :
      treatedOutcome =ᵐ[sampleLaw] treatedTarget)
    (hcontrolTransport :
      controlOutcome =ᵐ[sampleLaw] controlTarget)
    (hnumeratorTransport :
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget)
    (hmassTransport :
      treatedMass =ᵐ[sampleLaw] massTarget)
    (htreated :
      sampleLaw[treatedTarget | scoreSigma] =ᵐ[sampleLaw]
        treatedScoreVersion)
    (hcontrol :
      sampleLaw[controlTarget | scoreSigma] =ᵐ[sampleLaw]
        controlScoreVersion)
    (hnumerator :
      sampleLaw[effectTarget | scoreSigma] =ᵐ[sampleLaw]
        scoreEffectNumerator)
    (hmass :
      sampleLaw[massTarget | scoreSigma] =ᵐ[sampleLaw]
        scoreTreatedMass) :
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedScoreVersion sample ∂sampleLaw) -
          (∫ sample, controlScoreVersion sample ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample, scoreEffectNumerator sample ∂sampleLaw) /
          (∫ sample, scoreTreatedMass sample ∂sampleLaw) := by
  have hpattMass : pattRepr.population_treated_mass ≠ 0 := by
    rw [hreprMass]
    exact hmassTargetNonzero
  have hreprTObserved :
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw := by
    calc
      pateRepr.treated.population_target =
          ∫ sample, treatedTarget sample ∂sampleLaw := hreprT
      _ = ∫ sample, treatedOutcome sample ∂sampleLaw :=
          (integral_congr_ae htreatedTransport).symm
  have hreprCObserved :
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw := by
    calc
      pateRepr.control.population_target =
          ∫ sample, controlTarget sample ∂sampleLaw := hreprC
      _ = ∫ sample, controlOutcome sample ∂sampleLaw :=
          (integral_congr_ae hcontrolTransport).symm
  have hreprNumeratorObserved :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw := by
    calc
      pattRepr.population_treated_effect_numerator =
          ∫ sample, effectTarget sample ∂sampleLaw := hreprNumerator
      _ = ∫ sample, treatedEffectNumerator sample ∂sampleLaw :=
          (integral_congr_ae hnumeratorTransport).symm
  have hreprMassObserved :
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw := by
    calc
      pattRepr.population_treated_mass =
          ∫ sample, massTarget sample ∂sampleLaw := hreprMass
      _ = ∫ sample, treatedMass sample ∂sampleLaw :=
          (integral_congr_ae hmassTransport).symm
  have htreatedObserved :
      sampleLaw[treatedOutcome | scoreSigma] =ᵐ[sampleLaw]
        treatedScoreVersion :=
    (condExp_congr_ae (m := scoreSigma) (μ := sampleLaw)
      htreatedTransport).trans htreated
  have hcontrolObserved :
      sampleLaw[controlOutcome | scoreSigma] =ᵐ[sampleLaw]
        controlScoreVersion :=
    (condExp_congr_ae (m := scoreSigma) (μ := sampleLaw)
      hcontrolTransport).trans hcontrol
  have hnumeratorObserved :
      sampleLaw[treatedEffectNumerator | scoreSigma] =ᵐ[sampleLaw]
        scoreEffectNumerator :=
    (condExp_congr_ae (m := scoreSigma) (μ := sampleLaw)
      hnumeratorTransport).trans hnumerator
  have hmassObserved :
      sampleLaw[treatedMass | scoreSigma] =ᵐ[sampleLaw]
        scoreTreatedMass :=
    (condExp_congr_ae (m := scoreSigma) (μ := sampleLaw)
      hmassTransport).trans hmass
  exact
    selectedHajekPATE_PATT_eq_scorePATE_PATT_of_condExp_scoreVersions
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub pateRepr pattRepr htreatedSampling
      hcontrolSampling hpattSampling hpattMass treatedOutcome
      controlOutcome treatedEffectNumerator treatedMass treatedScoreVersion
      controlScoreVersion scoreEffectNumerator scoreTreatedMass
      hreprTObserved hreprCObserved hreprNumeratorObserved
      hreprMassObserved htreatedObserved hcontrolObserved hnumeratorObserved
      hmassObserved

/--
Selected-sample Hájek PATE recovers the score-space PATE when the
potential-outcome integrals agree a.e. with score-sigma measurable, integrable
score versions.
-/
theorem populationPATE_eq_scorePATE_of_ae_scoreVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (repr : PATERepresentation)
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
    repr.populationPATE =
      (∫ sample, treatedScoreVersion sample ∂sampleLaw) -
        (∫ sample, controlScoreVersion sample ∂sampleLaw) := by
  simp [PATERepresentation.populationPATE]
  rw [hreprT, hreprC]
  exact
    populationPATE_integral_eq_scorePATE_of_ae_eq_scoreVersions
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub treatedOutcome controlOutcome
      treatedScoreVersion controlScoreVersion htreated hcontrol htreatedMeas
      hcontrolMeas htreatedIntegrable hcontrolIntegrable

/--
Raw-outcome-integrability variant of abstract population PATE score-space
recovery from a.e. score versions.
-/
theorem populationPATE_eq_scorePATE_of_ae_scoreVersions_outcomeIntegrable
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (repr : PATERepresentation)
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
    (htreatedOutcomeIntegrable : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcomeIntegrable : Integrable controlOutcome sampleLaw) :
    repr.populationPATE =
      (∫ sample, treatedScoreVersion sample ∂sampleLaw) -
        (∫ sample, controlScoreVersion sample ∂sampleLaw) := by
  exact
    populationPATE_eq_scorePATE_of_ae_scoreVersions
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub repr treatedOutcome controlOutcome
      treatedScoreVersion controlScoreVersion hreprT hreprC htreated hcontrol
      htreatedMeas hcontrolMeas
      (htreatedOutcomeIntegrable.congr htreated)
      (hcontrolOutcomeIntegrable.congr hcontrol)

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
  exact
    populationPATE_eq_scorePATE_of_ae_scoreVersions
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub repr treatedOutcome controlOutcome
      treatedScoreVersion controlScoreVersion hreprT hreprC htreated hcontrol
      htreatedMeas hcontrolMeas htreatedIntegrable hcontrolIntegrable

/--
Raw-outcome-integrability variant of abstract selected-sample Hájek PATE
score-space recovery from a.e. score versions.
-/
theorem selectedHajekPATE_eq_scorePATE_of_ae_scoreVersions_outcomeIntegrable
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
    (htreatedOutcomeIntegrable : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcomeIntegrable : Integrable controlOutcome sampleLaw) :
    repr.selectedHajekPATE =
      (∫ sample, treatedScoreVersion sample ∂sampleLaw) -
        (∫ sample, controlScoreVersion sample ∂sampleLaw) := by
  exact
    selectedHajekPATE_eq_scorePATE_of_ae_scoreVersions
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub repr htreatedSampling
      hcontrolSampling treatedOutcome controlOutcome treatedScoreVersion
      controlScoreVersion hreprT hreprC htreated hcontrol htreatedMeas
      hcontrolMeas (htreatedOutcomeIntegrable.congr htreated)
      (hcontrolOutcomeIntegrable.congr hcontrol)

/--
Selected-sample Hájek PATT recovers the score-space PATT when the numerator
and denominator agree a.e. with score-sigma measurable, integrable score
versions.
-/
theorem populationPATT_eq_scorePATT_of_ae_scoreVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (repr : PATTRepresentation)
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
    repr.populationPATT =
      (∫ sample, scoreEffectNumerator sample ∂sampleLaw) /
        (∫ sample, scoreTreatedMass sample ∂sampleLaw) := by
  simp [PATTRepresentation.populationPATT]
  rw [hreprNumerator, hreprMass]
  rw [integral_eq_scoreVersion_of_ae_eq_scoreVersion
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub treatedEffectNumerator scoreEffectNumerator hnumerator
    hnumeratorMeas hnumeratorIntegrable]
  rw [integral_eq_scoreVersion_of_ae_eq_scoreVersion
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub treatedMass scoreTreatedMass hmass hmassMeas hmassIntegrable]

/--
Raw-outcome-integrability variant of abstract population PATT score-space
recovery from a.e. score versions.
-/
theorem populationPATT_eq_scorePATT_of_ae_scoreVersions_outcomeIntegrable
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (repr : PATTRepresentation)
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
    (hnumeratorOutcomeIntegrable :
      Integrable treatedEffectNumerator sampleLaw)
    (hmassOutcomeIntegrable : Integrable treatedMass sampleLaw) :
    repr.populationPATT =
      (∫ sample, scoreEffectNumerator sample ∂sampleLaw) /
        (∫ sample, scoreTreatedMass sample ∂sampleLaw) := by
  exact
    populationPATT_eq_scorePATT_of_ae_scoreVersions
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub repr treatedEffectNumerator treatedMass
      scoreEffectNumerator scoreTreatedMass hreprNumerator hreprMass
      hnumerator hmass hnumeratorMeas hmassMeas
      (hnumeratorOutcomeIntegrable.congr hnumerator)
      (hmassOutcomeIntegrable.congr hmass)

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
  exact
    populationPATT_eq_scorePATT_of_ae_scoreVersions
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub repr treatedEffectNumerator treatedMass
      scoreEffectNumerator scoreTreatedMass hreprNumerator hreprMass
      hnumerator hmass hnumeratorMeas hmassMeas hnumeratorIntegrable
      hmassIntegrable

/--
Raw-outcome-integrability variant of abstract selected-sample Hájek PATT
score-space recovery from a.e. score versions.
-/
theorem selectedHajekPATT_eq_scorePATT_of_ae_scoreVersions_outcomeIntegrable
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
    (hnumeratorOutcomeIntegrable :
      Integrable treatedEffectNumerator sampleLaw)
    (hmassOutcomeIntegrable : Integrable treatedMass sampleLaw) :
    repr.selectedHajekPATT =
      (∫ sample, scoreEffectNumerator sample ∂sampleLaw) /
        (∫ sample, scoreTreatedMass sample ∂sampleLaw) := by
  exact
    selectedHajekPATT_eq_scorePATT_of_ae_scoreVersions
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub repr hsampling htreatedMass
      treatedEffectNumerator treatedMass scoreEffectNumerator
      scoreTreatedMass hreprNumerator hreprMass hnumerator hmass
      hnumeratorMeas hmassMeas
      (hnumeratorOutcomeIntegrable.congr hnumerator)
      (hmassOutcomeIntegrable.congr hmass)

/--
Paired selected-sample Hájek PATE/PATT recovery from a.e. score-space
versions at the abstract representation layer.
-/
theorem selectedHajekPATE_PATT_eq_scorePATE_PATT_of_ae_scoreVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (htreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : pateRepr.control.sampling_mass ≠ 0)
    (hpattSampling : pattRepr.sampling_mass ≠ 0)
    (hpattMass : pattRepr.population_treated_mass ≠ 0)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass
      treatedScoreVersion controlScoreVersion scoreEffectNumerator
      scoreTreatedMass : Sample -> Real)
    (hreprT :
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw)
    (hreprC :
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw)
    (hreprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw)
    (htreated :
      treatedOutcome =ᵐ[sampleLaw] treatedScoreVersion)
    (hcontrol :
      controlOutcome =ᵐ[sampleLaw] controlScoreVersion)
    (hnumerator :
      treatedEffectNumerator =ᵐ[sampleLaw] scoreEffectNumerator)
    (hmass :
      treatedMass =ᵐ[sampleLaw] scoreTreatedMass)
    (htreatedMeas :
      AEStronglyMeasurable[scoreSigma] treatedScoreVersion sampleLaw)
    (hcontrolMeas :
      AEStronglyMeasurable[scoreSigma] controlScoreVersion sampleLaw)
    (hnumeratorMeas :
      AEStronglyMeasurable[scoreSigma] scoreEffectNumerator sampleLaw)
    (hmassMeas :
      AEStronglyMeasurable[scoreSigma] scoreTreatedMass sampleLaw)
    (htreatedIntegrable : Integrable treatedScoreVersion sampleLaw)
    (hcontrolIntegrable : Integrable controlScoreVersion sampleLaw)
    (hnumeratorIntegrable : Integrable scoreEffectNumerator sampleLaw)
    (hmassIntegrable : Integrable scoreTreatedMass sampleLaw) :
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedScoreVersion sample ∂sampleLaw) -
          (∫ sample, controlScoreVersion sample ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample, scoreEffectNumerator sample ∂sampleLaw) /
          (∫ sample, scoreTreatedMass sample ∂sampleLaw) := by
  constructor
  · exact
      selectedHajekPATE_eq_scorePATE_of_ae_scoreVersions
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pateRepr htreatedSampling
        hcontrolSampling treatedOutcome controlOutcome treatedScoreVersion
        controlScoreVersion hreprT hreprC htreated hcontrol htreatedMeas
        hcontrolMeas htreatedIntegrable hcontrolIntegrable
  · exact
      selectedHajekPATT_eq_scorePATT_of_ae_scoreVersions
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pattRepr hpattSampling hpattMass
        treatedEffectNumerator treatedMass scoreEffectNumerator
        scoreTreatedMass hreprNumerator hreprMass hnumerator hmass
        hnumeratorMeas hmassMeas hnumeratorIntegrable hmassIntegrable

/--
Raw-outcome-integrability paired selected-sample Hájek PATE/PATT recovery from
a.e. score-space versions at the abstract representation layer.
-/
theorem selectedHajekPATE_PATT_eq_scorePATE_PATT_of_ae_scoreVersions_outcomeIntegrable
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (htreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : pateRepr.control.sampling_mass ≠ 0)
    (hpattSampling : pattRepr.sampling_mass ≠ 0)
    (hpattMass : pattRepr.population_treated_mass ≠ 0)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass
      treatedScoreVersion controlScoreVersion scoreEffectNumerator
      scoreTreatedMass : Sample -> Real)
    (hreprT :
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw)
    (hreprC :
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw)
    (hreprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw)
    (hreprMass :
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw)
    (htreated :
      treatedOutcome =ᵐ[sampleLaw] treatedScoreVersion)
    (hcontrol :
      controlOutcome =ᵐ[sampleLaw] controlScoreVersion)
    (hnumerator :
      treatedEffectNumerator =ᵐ[sampleLaw] scoreEffectNumerator)
    (hmass :
      treatedMass =ᵐ[sampleLaw] scoreTreatedMass)
    (htreatedMeas :
      AEStronglyMeasurable[scoreSigma] treatedScoreVersion sampleLaw)
    (hcontrolMeas :
      AEStronglyMeasurable[scoreSigma] controlScoreVersion sampleLaw)
    (hnumeratorMeas :
      AEStronglyMeasurable[scoreSigma] scoreEffectNumerator sampleLaw)
    (hmassMeas :
      AEStronglyMeasurable[scoreSigma] scoreTreatedMass sampleLaw)
    (htreatedOutcomeIntegrable : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcomeIntegrable : Integrable controlOutcome sampleLaw)
    (hnumeratorOutcomeIntegrable :
      Integrable treatedEffectNumerator sampleLaw)
    (hmassOutcomeIntegrable : Integrable treatedMass sampleLaw) :
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedScoreVersion sample ∂sampleLaw) -
          (∫ sample, controlScoreVersion sample ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample, scoreEffectNumerator sample ∂sampleLaw) /
          (∫ sample, scoreTreatedMass sample ∂sampleLaw) := by
  constructor
  · exact
      selectedHajekPATE_eq_scorePATE_of_ae_scoreVersions_outcomeIntegrable
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pateRepr htreatedSampling
        hcontrolSampling treatedOutcome controlOutcome treatedScoreVersion
        controlScoreVersion hreprT hreprC htreated hcontrol htreatedMeas
        hcontrolMeas htreatedOutcomeIntegrable hcontrolOutcomeIntegrable
  · exact
      selectedHajekPATT_eq_scorePATT_of_ae_scoreVersions_outcomeIntegrable
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pattRepr hpattSampling hpattMass
      treatedEffectNumerator treatedMass scoreEffectNumerator
      scoreTreatedMass hreprNumerator hreprMass hnumerator hmass
      hnumeratorMeas hmassMeas hnumeratorOutcomeIntegrable
      hmassOutcomeIntegrable

/--
Selected-Hájek PATE/PATT recovery from transported latent/reference targets
and a.e. score versions of those targets.  This is the a.e. score-version
analogue of the conditional target-transport theorem above: representation and
denominator nonzero conditions are stated on the transported targets, while
Lean transports integrability and a.e. score-version identities back to the
observed targets.
-/
theorem selectedHajekPATE_PATT_eq_scorePATE_PATT_of_ae_scoreVersions_targetTransport_targetRepresentation_targetIntegrable
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (htreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : pateRepr.control.sampling_mass ≠ 0)
    (hpattSampling : pattRepr.sampling_mass ≠ 0)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass
      treatedTarget controlTarget effectTarget massTarget
      treatedScoreVersion controlScoreVersion scoreEffectNumerator
      scoreTreatedMass : Sample -> Real)
    (hreprT :
      pateRepr.treated.population_target =
        ∫ sample, treatedTarget sample ∂sampleLaw)
    (hreprC :
      pateRepr.control.population_target =
        ∫ sample, controlTarget sample ∂sampleLaw)
    (hreprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, effectTarget sample ∂sampleLaw)
    (hreprMass :
      pattRepr.population_treated_mass =
        ∫ sample, massTarget sample ∂sampleLaw)
    (hmassTargetNonzero :
      (∫ sample, massTarget sample ∂sampleLaw) ≠ 0)
    (htreatedTransport :
      treatedOutcome =ᵐ[sampleLaw] treatedTarget)
    (hcontrolTransport :
      controlOutcome =ᵐ[sampleLaw] controlTarget)
    (hnumeratorTransport :
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget)
    (hmassTransport :
      treatedMass =ᵐ[sampleLaw] massTarget)
    (htreatedTarget :
      treatedTarget =ᵐ[sampleLaw] treatedScoreVersion)
    (hcontrolTarget :
      controlTarget =ᵐ[sampleLaw] controlScoreVersion)
    (hnumeratorTarget :
      effectTarget =ᵐ[sampleLaw] scoreEffectNumerator)
    (hmassTarget :
      massTarget =ᵐ[sampleLaw] scoreTreatedMass)
    (htreatedMeas :
      AEStronglyMeasurable[scoreSigma] treatedScoreVersion sampleLaw)
    (hcontrolMeas :
      AEStronglyMeasurable[scoreSigma] controlScoreVersion sampleLaw)
    (hnumeratorMeas :
      AEStronglyMeasurable[scoreSigma] scoreEffectNumerator sampleLaw)
    (hmassMeas :
      AEStronglyMeasurable[scoreSigma] scoreTreatedMass sampleLaw)
    (htreatedTargetInt : Integrable treatedTarget sampleLaw)
    (hcontrolTargetInt : Integrable controlTarget sampleLaw)
    (heffectTargetInt : Integrable effectTarget sampleLaw)
    (hmassTargetInt : Integrable massTarget sampleLaw) :
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedScoreVersion sample ∂sampleLaw) -
          (∫ sample, controlScoreVersion sample ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample, scoreEffectNumerator sample ∂sampleLaw) /
          (∫ sample, scoreTreatedMass sample ∂sampleLaw) := by
  have hpattMass : pattRepr.population_treated_mass ≠ 0 := by
    rw [hreprMass]
    exact hmassTargetNonzero
  have hreprTObserved :
      pateRepr.treated.population_target =
        ∫ sample, treatedOutcome sample ∂sampleLaw := by
    calc
      pateRepr.treated.population_target =
          ∫ sample, treatedTarget sample ∂sampleLaw := hreprT
      _ = ∫ sample, treatedOutcome sample ∂sampleLaw :=
          (integral_congr_ae htreatedTransport).symm
  have hreprCObserved :
      pateRepr.control.population_target =
        ∫ sample, controlOutcome sample ∂sampleLaw := by
    calc
      pateRepr.control.population_target =
          ∫ sample, controlTarget sample ∂sampleLaw := hreprC
      _ = ∫ sample, controlOutcome sample ∂sampleLaw :=
          (integral_congr_ae hcontrolTransport).symm
  have hreprNumeratorObserved :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, treatedEffectNumerator sample ∂sampleLaw := by
    calc
      pattRepr.population_treated_effect_numerator =
          ∫ sample, effectTarget sample ∂sampleLaw := hreprNumerator
      _ = ∫ sample, treatedEffectNumerator sample ∂sampleLaw :=
          (integral_congr_ae hnumeratorTransport).symm
  have hreprMassObserved :
      pattRepr.population_treated_mass =
        ∫ sample, treatedMass sample ∂sampleLaw := by
    calc
      pattRepr.population_treated_mass =
          ∫ sample, massTarget sample ∂sampleLaw := hreprMass
      _ = ∫ sample, treatedMass sample ∂sampleLaw :=
          (integral_congr_ae hmassTransport).symm
  exact
    selectedHajekPATE_PATT_eq_scorePATE_PATT_of_ae_scoreVersions_outcomeIntegrable
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub pateRepr pattRepr htreatedSampling
      hcontrolSampling hpattSampling hpattMass treatedOutcome
      controlOutcome treatedEffectNumerator treatedMass treatedScoreVersion
      controlScoreVersion scoreEffectNumerator scoreTreatedMass
      hreprTObserved hreprCObserved hreprNumeratorObserved
      hreprMassObserved (htreatedTransport.trans htreatedTarget)
      (hcontrolTransport.trans hcontrolTarget)
      (hnumeratorTransport.trans hnumeratorTarget)
      (hmassTransport.trans hmassTarget) htreatedMeas hcontrolMeas
      hnumeratorMeas hmassMeas
      (htreatedTargetInt.congr htreatedTransport.symm)
      (hcontrolTargetInt.congr hcontrolTransport.symm)
      (heffectTargetInt.congr hnumeratorTransport.symm)
      (hmassTargetInt.congr hmassTransport.symm)

/--
Observed-outcome-integrability variant of the transported-target a.e.
score-version selected-Hájek route.  When the paper supplies integrability for
the observed WDSM targets, the a.e. target-transport identities transfer those
integrability assumptions to the latent/reference targets used in the
representation field.
-/
theorem selectedHajekPATE_PATT_eq_scorePATE_PATT_of_ae_scoreVersions_targetTransport_targetRepresentation_outcomeIntegrable
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (htreatedSampling : pateRepr.treated.sampling_mass ≠ 0)
    (hcontrolSampling : pateRepr.control.sampling_mass ≠ 0)
    (hpattSampling : pattRepr.sampling_mass ≠ 0)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass
      treatedTarget controlTarget effectTarget massTarget
      treatedScoreVersion controlScoreVersion scoreEffectNumerator
      scoreTreatedMass : Sample -> Real)
    (hreprT :
      pateRepr.treated.population_target =
        ∫ sample, treatedTarget sample ∂sampleLaw)
    (hreprC :
      pateRepr.control.population_target =
        ∫ sample, controlTarget sample ∂sampleLaw)
    (hreprNumerator :
      pattRepr.population_treated_effect_numerator =
        ∫ sample, effectTarget sample ∂sampleLaw)
    (hreprMass :
      pattRepr.population_treated_mass =
        ∫ sample, massTarget sample ∂sampleLaw)
    (hmassTargetNonzero :
      (∫ sample, massTarget sample ∂sampleLaw) ≠ 0)
    (htreatedTransport :
      treatedOutcome =ᵐ[sampleLaw] treatedTarget)
    (hcontrolTransport :
      controlOutcome =ᵐ[sampleLaw] controlTarget)
    (hnumeratorTransport :
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget)
    (hmassTransport :
      treatedMass =ᵐ[sampleLaw] massTarget)
    (htreatedTarget :
      treatedTarget =ᵐ[sampleLaw] treatedScoreVersion)
    (hcontrolTarget :
      controlTarget =ᵐ[sampleLaw] controlScoreVersion)
    (hnumeratorTarget :
      effectTarget =ᵐ[sampleLaw] scoreEffectNumerator)
    (hmassTarget :
      massTarget =ᵐ[sampleLaw] scoreTreatedMass)
    (htreatedMeas :
      AEStronglyMeasurable[scoreSigma] treatedScoreVersion sampleLaw)
    (hcontrolMeas :
      AEStronglyMeasurable[scoreSigma] controlScoreVersion sampleLaw)
    (hnumeratorMeas :
      AEStronglyMeasurable[scoreSigma] scoreEffectNumerator sampleLaw)
    (hmassMeas :
      AEStronglyMeasurable[scoreSigma] scoreTreatedMass sampleLaw)
    (htreatedOutcomeInt : Integrable treatedOutcome sampleLaw)
    (hcontrolOutcomeInt : Integrable controlOutcome sampleLaw)
    (hnumeratorOutcomeInt :
      Integrable treatedEffectNumerator sampleLaw)
    (hmassOutcomeInt : Integrable treatedMass sampleLaw) :
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedScoreVersion sample ∂sampleLaw) -
          (∫ sample, controlScoreVersion sample ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample, scoreEffectNumerator sample ∂sampleLaw) /
          (∫ sample, scoreTreatedMass sample ∂sampleLaw) :=
  selectedHajekPATE_PATT_eq_scorePATE_PATT_of_ae_scoreVersions_targetTransport_targetRepresentation_targetIntegrable
    (mSample := mSample) (scoreSigma := scoreSigma)
    (sampleLaw := sampleLaw) hsub pateRepr pattRepr htreatedSampling
    hcontrolSampling hpattSampling treatedOutcome controlOutcome
    treatedEffectNumerator treatedMass treatedTarget controlTarget
    effectTarget massTarget treatedScoreVersion controlScoreVersion
    scoreEffectNumerator scoreTreatedMass hreprT hreprC hreprNumerator
    hreprMass hmassTargetNonzero htreatedTransport hcontrolTransport
    hnumeratorTransport hmassTransport htreatedTarget hcontrolTarget
    hnumeratorTarget hmassTarget htreatedMeas hcontrolMeas hnumeratorMeas
    hmassMeas (htreatedOutcomeInt.congr htreatedTransport)
    (hcontrolOutcomeInt.congr hcontrolTransport)
    (hnumeratorOutcomeInt.congr hnumeratorTransport)
    (hmassOutcomeInt.congr hmassTransport)

/--
Generic `SurveyWeightedScoreMeanBridge` for selected-Hájek target transport
with a.e. score versions of latent/reference targets.  This packages the
representation-layer route so downstream score-specific modules can expose a
single bridge rather than restating the target transport, target integrability,
score-version measurability, and target representation fields separately.
-/
noncomputable def surveyWeightedScoreMeanBridge_of_selectedHajek_ae_scoreVersions_targetTransport_targetRepresentation_targetIntegrable
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass
      treatedTarget controlTarget effectTarget massTarget
      treatedScoreVersion controlScoreVersion scoreEffectNumerator
      scoreTreatedMass : Sample -> Real) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing :=
    Integrable treatedTarget sampleLaw ∧
      Integrable controlTarget sampleLaw ∧
      Integrable effectTarget sampleLaw ∧
      Integrable massTarget sampleLaw ∧
      treatedOutcome =ᵐ[sampleLaw] treatedTarget ∧
      controlOutcome =ᵐ[sampleLaw] controlTarget ∧
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget ∧
      treatedMass =ᵐ[sampleLaw] massTarget ∧
      treatedTarget =ᵐ[sampleLaw] treatedScoreVersion ∧
      controlTarget =ᵐ[sampleLaw] controlScoreVersion ∧
      effectTarget =ᵐ[sampleLaw] scoreEffectNumerator ∧
      massTarget =ᵐ[sampleLaw] scoreTreatedMass ∧
      AEStronglyMeasurable[scoreSigma] treatedScoreVersion sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] controlScoreVersion sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] scoreEffectNumerator sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] scoreTreatedMass sampleLaw
  survey_weighted_score_mean_representation :=
    pateRepr.treated.sampling_mass ≠ 0 ∧
      pateRepr.control.sampling_mass ≠ 0 ∧
      pattRepr.sampling_mass ≠ 0 ∧
      (∫ sample, massTarget sample ∂sampleLaw) ≠ 0 ∧
      pateRepr.treated.population_target =
        ∫ sample, treatedTarget sample ∂sampleLaw ∧
      pateRepr.control.population_target =
        ∫ sample, controlTarget sample ∂sampleLaw ∧
      pattRepr.population_treated_effect_numerator =
        ∫ sample, effectTarget sample ∂sampleLaw ∧
      pattRepr.population_treated_mass =
        ∫ sample, massTarget sample ∂sampleLaw
  score_space_identification :=
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedScoreVersion sample ∂sampleLaw) -
          (∫ sample, controlScoreVersion sample ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample, scoreEffectNumerator sample ∂sampleLaw) /
          (∫ sample, scoreTreatedMass sample ∂sampleLaw)
  bridge := by
    intro hbalance hweighted
    rcases hbalance with
      ⟨htreatedTargetInt, hcontrolTargetInt, heffectTargetInt,
        hmassTargetInt, htreatedTransport, hcontrolTransport,
        hnumeratorTransport, hmassTransport, htreatedTarget,
        hcontrolTarget, hnumeratorTarget, hmassTarget, htreatedMeas,
        hcontrolMeas, hnumeratorMeas, hmassMeas⟩
    rcases hweighted with
      ⟨htreatedSampling, hcontrolSampling, hpattSampling,
        hmassTargetNonzero, hreprT, hreprC, hreprNumerator, hreprMass⟩
    exact
      selectedHajekPATE_PATT_eq_scorePATE_PATT_of_ae_scoreVersions_targetTransport_targetRepresentation_targetIntegrable
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pateRepr pattRepr htreatedSampling
        hcontrolSampling hpattSampling treatedOutcome controlOutcome
        treatedEffectNumerator treatedMass treatedTarget controlTarget
        effectTarget massTarget treatedScoreVersion controlScoreVersion
        scoreEffectNumerator scoreTreatedMass hreprT hreprC
        hreprNumerator hreprMass hmassTargetNonzero htreatedTransport
        hcontrolTransport hnumeratorTransport hmassTransport htreatedTarget
        hcontrolTarget hnumeratorTarget hmassTarget htreatedMeas hcontrolMeas
        hnumeratorMeas hmassMeas htreatedTargetInt hcontrolTargetInt
        heffectTargetInt hmassTargetInt
  }

/--
Generic `SurveyWeightedScoreMeanBridge` for selected-Hájek target transport
with observed-target integrability.  This has the same a.e. target-score route
as `surveyWeightedScoreMeanBridge_of_selectedHajek_ae_scoreVersions_targetTransport_targetRepresentation_targetIntegrable`,
but the balancing field asks for integrability of the observed WDSM targets;
Lean transfers it to the latent/reference targets through the a.e. transport
equalities.
-/
noncomputable def surveyWeightedScoreMeanBridge_of_selectedHajek_ae_scoreVersions_targetTransport_targetRepresentation_outcomeIntegrable
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (pateRepr : PATERepresentation)
    (pattRepr : PATTRepresentation)
    (treatedOutcome controlOutcome treatedEffectNumerator treatedMass
      treatedTarget controlTarget effectTarget massTarget
      treatedScoreVersion controlScoreVersion scoreEffectNumerator
      scoreTreatedMass : Sample -> Real) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing :=
    Integrable treatedOutcome sampleLaw ∧
      Integrable controlOutcome sampleLaw ∧
      Integrable treatedEffectNumerator sampleLaw ∧
      Integrable treatedMass sampleLaw ∧
      treatedOutcome =ᵐ[sampleLaw] treatedTarget ∧
      controlOutcome =ᵐ[sampleLaw] controlTarget ∧
      treatedEffectNumerator =ᵐ[sampleLaw] effectTarget ∧
      treatedMass =ᵐ[sampleLaw] massTarget ∧
      treatedTarget =ᵐ[sampleLaw] treatedScoreVersion ∧
      controlTarget =ᵐ[sampleLaw] controlScoreVersion ∧
      effectTarget =ᵐ[sampleLaw] scoreEffectNumerator ∧
      massTarget =ᵐ[sampleLaw] scoreTreatedMass ∧
      AEStronglyMeasurable[scoreSigma] treatedScoreVersion sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] controlScoreVersion sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] scoreEffectNumerator sampleLaw ∧
      AEStronglyMeasurable[scoreSigma] scoreTreatedMass sampleLaw
  survey_weighted_score_mean_representation :=
    pateRepr.treated.sampling_mass ≠ 0 ∧
      pateRepr.control.sampling_mass ≠ 0 ∧
      pattRepr.sampling_mass ≠ 0 ∧
      (∫ sample, massTarget sample ∂sampleLaw) ≠ 0 ∧
      pateRepr.treated.population_target =
        ∫ sample, treatedTarget sample ∂sampleLaw ∧
      pateRepr.control.population_target =
        ∫ sample, controlTarget sample ∂sampleLaw ∧
      pattRepr.population_treated_effect_numerator =
        ∫ sample, effectTarget sample ∂sampleLaw ∧
      pattRepr.population_treated_mass =
        ∫ sample, massTarget sample ∂sampleLaw
  score_space_identification :=
    pateRepr.selectedHajekPATE =
        (∫ sample, treatedScoreVersion sample ∂sampleLaw) -
          (∫ sample, controlScoreVersion sample ∂sampleLaw) ∧
      pattRepr.selectedHajekPATT =
        (∫ sample, scoreEffectNumerator sample ∂sampleLaw) /
          (∫ sample, scoreTreatedMass sample ∂sampleLaw)
  bridge := by
    intro hbalance hweighted
    rcases hbalance with
      ⟨htreatedOutcomeInt, hcontrolOutcomeInt, hnumeratorOutcomeInt,
        hmassOutcomeInt, htreatedTransport, hcontrolTransport,
        hnumeratorTransport, hmassTransport, htreatedTarget,
        hcontrolTarget, hnumeratorTarget, hmassTarget, htreatedMeas,
        hcontrolMeas, hnumeratorMeas, hmassMeas⟩
    rcases hweighted with
      ⟨htreatedSampling, hcontrolSampling, hpattSampling,
        hmassTargetNonzero, hreprT, hreprC, hreprNumerator, hreprMass⟩
    exact
      selectedHajekPATE_PATT_eq_scorePATE_PATT_of_ae_scoreVersions_targetTransport_targetRepresentation_outcomeIntegrable
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub pateRepr pattRepr htreatedSampling
        hcontrolSampling hpattSampling treatedOutcome controlOutcome
        treatedEffectNumerator treatedMass treatedTarget controlTarget
        effectTarget massTarget treatedScoreVersion controlScoreVersion
        scoreEffectNumerator scoreTreatedMass hreprT hreprC
        hreprNumerator hreprMass hmassTargetNonzero htreatedTransport
        hcontrolTransport hnumeratorTransport hmassTransport htreatedTarget
        hcontrolTarget hnumeratorTarget hmassTarget htreatedMeas hcontrolMeas
        hnumeratorMeas hmassMeas htreatedOutcomeInt hcontrolOutcomeInt
        hnumeratorOutcomeInt hmassOutcomeInt
  }

end WDSM
end Matching
end StatInference
