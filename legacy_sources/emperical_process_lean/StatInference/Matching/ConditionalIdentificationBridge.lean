import StatInference.Matching.WDSM.ConditionalMeanIntegralBridge
import StatInference.Matching.WDSM.IdentificationInterfaces

/-!
# Conditional identification bridge for WDSM population targets

This module packages score-sigma conditional-mean equalities into the existing
PATE and PATT population-identification interfaces.  It is the
measure-theoretic bridge from conditional mean versions to arm-level and
one-sided population target algebra.
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
If the treated and control potential-outcome conditional means are represented
by score-space versions, then the population PATE contrast equals the
score-space contrast.
-/
theorem populationPATE_integral_eq_scorePATE_of_condExp_ae_eq
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (treatedOutcome controlOutcome treatedScoreVersion controlScoreVersion :
      Sample -> Real)
    (htreated :
      sampleLaw[treatedOutcome | scoreSigma] =ᵐ[sampleLaw]
        treatedScoreVersion)
    (hcontrol :
      sampleLaw[controlOutcome | scoreSigma] =ᵐ[sampleLaw]
        controlScoreVersion) :
    (∫ sample, treatedOutcome sample ∂sampleLaw) -
        (∫ sample, controlOutcome sample ∂sampleLaw) =
      (∫ sample, treatedScoreVersion sample ∂sampleLaw) -
        (∫ sample, controlScoreVersion sample ∂sampleLaw) := by
  rw [integral_eq_scoreVersion_of_condExp_ae_eq
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub treatedOutcome treatedScoreVersion htreated]
  rw [integral_eq_scoreVersion_of_condExp_ae_eq
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub controlOutcome controlScoreVersion hcontrol]

/--
Construct the existing PATE arm-mean identification interface from
score-sigma conditional-mean versions.
-/
noncomputable def pateArmMeanIdentificationOfCondExpScoreVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (treatedOutcome controlOutcome treatedScoreVersion controlScoreVersion :
      Sample -> Real)
    (htreated :
      sampleLaw[treatedOutcome | scoreSigma] =ᵐ[sampleLaw]
        treatedScoreVersion)
    (hcontrol :
      sampleLaw[controlOutcome | scoreSigma] =ᵐ[sampleLaw]
        controlScoreVersion) :
    PATEArmMeanIdentification where
  treated_population_mean := ∫ sample, treatedOutcome sample ∂sampleLaw
  control_population_mean := ∫ sample, controlOutcome sample ∂sampleLaw
  treated_score_mean := ∫ sample, treatedScoreVersion sample ∂sampleLaw
  control_score_mean := ∫ sample, controlScoreVersion sample ∂sampleLaw
  treated_identification := by
    symm
    exact
      integral_eq_scoreVersion_of_condExp_ae_eq
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub treatedOutcome treatedScoreVersion
        htreated
  control_identification := by
    symm
    exact
      integral_eq_scoreVersion_of_condExp_ae_eq
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub controlOutcome controlScoreVersion
        hcontrol

/--
The score-space PATE interface obtained from conditional means recovers the
population PATE.
-/
theorem scorePATE_eq_populationPATE_of_condExp_scoreVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (treatedOutcome controlOutcome treatedScoreVersion controlScoreVersion :
      Sample -> Real)
    (htreated :
      sampleLaw[treatedOutcome | scoreSigma] =ᵐ[sampleLaw]
        treatedScoreVersion)
    (hcontrol :
      sampleLaw[controlOutcome | scoreSigma] =ᵐ[sampleLaw]
        controlScoreVersion) :
    PATEArmMeanIdentification.scorePATE
        (pateArmMeanIdentificationOfCondExpScoreVersions
          (mSample := mSample) (scoreSigma := scoreSigma)
          (sampleLaw := sampleLaw) hsub treatedOutcome controlOutcome
          treatedScoreVersion controlScoreVersion htreated hcontrol) =
      PATEArmMeanIdentification.populationPATE
        (pateArmMeanIdentificationOfCondExpScoreVersions
          (mSample := mSample) (scoreSigma := scoreSigma)
          (sampleLaw := sampleLaw) hsub treatedOutcome controlOutcome
          treatedScoreVersion controlScoreVersion htreated hcontrol) := by
  exact
    PATEArmMeanIdentification.scorePATE_eq_populationPATE
      (pateArmMeanIdentificationOfCondExpScoreVersions
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub treatedOutcome controlOutcome
        treatedScoreVersion controlScoreVersion htreated hcontrol)

/--
Construct the existing PATT mean-identification interface from conditional
versions of the treated-effect numerator and treated-mass denominator.
-/
noncomputable def pattMeanIdentificationOfCondExpScoreVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (treatedEffectNumerator treatedMass
      scoreEffectNumerator scoreTreatedMass : Sample -> Real)
    (hnumerator :
      sampleLaw[treatedEffectNumerator | scoreSigma] =ᵐ[sampleLaw]
        scoreEffectNumerator)
    (hmass :
      sampleLaw[treatedMass | scoreSigma] =ᵐ[sampleLaw] scoreTreatedMass) :
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
      integral_eq_scoreVersion_of_condExp_ae_eq
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub treatedEffectNumerator
        scoreEffectNumerator hnumerator
  mass_identification := by
    symm
    exact
      integral_eq_scoreVersion_of_condExp_ae_eq
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub treatedMass scoreTreatedMass hmass

/--
The score-space PATT interface obtained from conditional means recovers the
population PATT ratio.
-/
theorem scorePATT_eq_populationPATT_of_condExp_scoreVersions
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (treatedEffectNumerator treatedMass
      scoreEffectNumerator scoreTreatedMass : Sample -> Real)
    (hnumerator :
      sampleLaw[treatedEffectNumerator | scoreSigma] =ᵐ[sampleLaw]
        scoreEffectNumerator)
    (hmass :
      sampleLaw[treatedMass | scoreSigma] =ᵐ[sampleLaw] scoreTreatedMass) :
    PATTMeanIdentification.scorePATT
        (pattMeanIdentificationOfCondExpScoreVersions
          (mSample := mSample) (scoreSigma := scoreSigma)
          (sampleLaw := sampleLaw) hsub treatedEffectNumerator treatedMass
          scoreEffectNumerator scoreTreatedMass hnumerator hmass) =
      PATTMeanIdentification.populationPATT
        (pattMeanIdentificationOfCondExpScoreVersions
          (mSample := mSample) (scoreSigma := scoreSigma)
          (sampleLaw := sampleLaw) hsub treatedEffectNumerator treatedMass
          scoreEffectNumerator scoreTreatedMass hnumerator hmass) := by
  exact
    PATTMeanIdentification.scorePATT_eq_populationPATT
      (pattMeanIdentificationOfCondExpScoreVersions
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) hsub treatedEffectNumerator treatedMass
        scoreEffectNumerator scoreTreatedMass hnumerator hmass)

end WDSM
end Matching
end StatInference
