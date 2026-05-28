import StatInference.Matching.WDSM.SurveyConditionalIdentificationBridge

/-!
# Population inverse-selection identity constructors

This module is the measure-theoretic analogue of the finite inverse-selection
constructors.  It packages weighted selected-law integral identities into the
abstract `InverseSelectionIdentity`, `PATERepresentation`, and
`PATTRepresentation` structures consumed by the Hájek ratio and conditional
identification layers.

The theorem statements intentionally expose the remaining survey-ignorability
obligations as weighted selected-law integral identities.  Later work can
prove those identities from the sampling design assumptions and then reuse the
ratio layer without restating algebra.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open scoped MeasureTheory

variable {Sample : Type*} [MeasurableSpace Sample]

/--
Package a weighted selected-law integral recovery identity as an abstract
inverse-selection identity.
-/
noncomputable def inverseSelectionIdentityOfWeightedIntegralRecovery
    (selectedLaw populationLaw : Measure Sample)
    (surveyWeight target : Sample -> Real) (samplingMass : Real)
    (htarget :
      (∫ sample, surveyWeight sample * target sample ∂selectedLaw) =
        (∫ sample, target sample ∂populationLaw) / samplingMass)
    (hone :
      (∫ sample, surveyWeight sample ∂selectedLaw) = 1 / samplingMass) :
    InverseSelectionIdentity where
  selected_weighted_target :=
    ∫ sample, surveyWeight sample * target sample ∂selectedLaw
  selected_weighted_one := ∫ sample, surveyWeight sample ∂selectedLaw
  population_target := ∫ sample, target sample ∂populationLaw
  sampling_mass := samplingMass
  target_identity := htarget
  one_identity := hone

/--
Weighted selected-law Hájek recovery of a population-law integral from the
measure-level inverse-selection identities.
-/
theorem selectedWeightedIntegralRatio_eq_populationIntegral
    (selectedLaw populationLaw : Measure Sample)
    (surveyWeight target : Sample -> Real) (samplingMass : Real)
    (htarget :
      (∫ sample, surveyWeight sample * target sample ∂selectedLaw) =
        (∫ sample, target sample ∂populationLaw) / samplingMass)
    (hone :
      (∫ sample, surveyWeight sample ∂selectedLaw) = 1 / samplingMass)
    (hsampling : samplingMass ≠ 0) :
    (∫ sample, surveyWeight sample * target sample ∂selectedLaw) /
        (∫ sample, surveyWeight sample ∂selectedLaw) =
      ∫ sample, target sample ∂populationLaw := by
  exact
    InverseSelectionIdentity.hajekRatio_eq_populationTarget
      (inverseSelectionIdentityOfWeightedIntegralRecovery selectedLaw
        populationLaw surveyWeight target samplingMass htarget hone)
      hsampling

/--
Construct a PATE representation from two arm-specific weighted selected-law
integral recovery identities.
-/
noncomputable def pateRepresentationOfWeightedIntegralRecovery
    (selectedLaw populationLaw : Measure Sample)
    (treatedWeight controlWeight treatedOutcome controlOutcome :
      Sample -> Real)
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
        1 / controlSamplingMass) :
    PATERepresentation where
  treated :=
    inverseSelectionIdentityOfWeightedIntegralRecovery selectedLaw
      populationLaw treatedWeight treatedOutcome treatedSamplingMass
      htreatedTarget htreatedOne
  control :=
    inverseSelectionIdentityOfWeightedIntegralRecovery selectedLaw
      populationLaw controlWeight controlOutcome controlSamplingMass
      hcontrolTarget hcontrolOne

/--
Selected-law weighted Hájek PATE recovers the population-law PATE contrast
once the two arm-specific inverse-selection integral identities hold.
-/
theorem selectedWeightedIntegralPATE_eq_populationIntegralPATE
    (selectedLaw populationLaw : Measure Sample)
    (treatedWeight controlWeight treatedOutcome controlOutcome :
      Sample -> Real)
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
    (hcontrolSampling : controlSamplingMass ≠ 0) :
    PATERepresentation.selectedHajekPATE
        (pateRepresentationOfWeightedIntegralRecovery selectedLaw
          populationLaw treatedWeight controlWeight treatedOutcome
          controlOutcome treatedSamplingMass controlSamplingMass
          htreatedTarget htreatedOne hcontrolTarget hcontrolOne) =
      (∫ sample, treatedOutcome sample ∂populationLaw) -
        (∫ sample, controlOutcome sample ∂populationLaw) := by
  exact
    PATERepresentation.selectedHajekPATE_eq_populationPATE
      (pateRepresentationOfWeightedIntegralRecovery selectedLaw populationLaw
        treatedWeight controlWeight treatedOutcome controlOutcome
        treatedSamplingMass controlSamplingMass htreatedTarget htreatedOne
        hcontrolTarget hcontrolOne)
      htreatedSampling hcontrolSampling

/--
Construct a PATT representation from weighted selected-law integral recovery
identities for the treated-effect numerator and treated-mass denominator.
-/
noncomputable def pattRepresentationOfWeightedIntegralRecovery
    (selectedLaw populationLaw : Measure Sample)
    (surveyWeight treatedEffect treatedMass : Sample -> Real)
    (samplingMass : Real)
    (hnumerator :
      (∫ sample, surveyWeight sample * treatedEffect sample ∂selectedLaw) =
        (∫ sample, treatedEffect sample ∂populationLaw) / samplingMass)
    (hmass :
      (∫ sample, surveyWeight sample * treatedMass sample ∂selectedLaw) =
        (∫ sample, treatedMass sample ∂populationLaw) / samplingMass) :
    PATTRepresentation where
  selected_weighted_treated_effect :=
    ∫ sample, surveyWeight sample * treatedEffect sample ∂selectedLaw
  selected_weighted_treated_mass :=
    ∫ sample, surveyWeight sample * treatedMass sample ∂selectedLaw
  population_treated_effect_numerator :=
    ∫ sample, treatedEffect sample ∂populationLaw
  population_treated_mass := ∫ sample, treatedMass sample ∂populationLaw
  sampling_mass := samplingMass
  numerator_identity := hnumerator
  denominator_identity := hmass

/--
Selected-law weighted Hájek PATT recovers the population-law PATT ratio once
the numerator and denominator share the same inverse-selection normalization.
-/
theorem selectedWeightedIntegralPATT_eq_populationIntegralPATT
    (selectedLaw populationLaw : Measure Sample)
    (surveyWeight treatedEffect treatedMass : Sample -> Real)
    (samplingMass : Real)
    (hnumerator :
      (∫ sample, surveyWeight sample * treatedEffect sample ∂selectedLaw) =
        (∫ sample, treatedEffect sample ∂populationLaw) / samplingMass)
    (hmass :
      (∫ sample, surveyWeight sample * treatedMass sample ∂selectedLaw) =
        (∫ sample, treatedMass sample ∂populationLaw) / samplingMass)
    (hsampling : samplingMass ≠ 0)
    (htreatedMass :
      (∫ sample, treatedMass sample ∂populationLaw) ≠ 0) :
    PATTRepresentation.selectedHajekPATT
        (pattRepresentationOfWeightedIntegralRecovery selectedLaw populationLaw
          surveyWeight treatedEffect treatedMass samplingMass hnumerator
          hmass) =
      (∫ sample, treatedEffect sample ∂populationLaw) /
        (∫ sample, treatedMass sample ∂populationLaw) := by
  exact
    PATTRepresentation.selectedHajekPATT_eq_populationPATT
      (pattRepresentationOfWeightedIntegralRecovery selectedLaw populationLaw
        surveyWeight treatedEffect treatedMass samplingMass hnumerator hmass)
      hsampling htreatedMass

end WDSM
end Matching
end StatInference
