import StatInference.Matching.WDSM.FiniteInverseSelectionIdentity

/-!
# Finite Hájek representation constructors

This module packages finite inverse-selection identities into the PATE and
PATT representation structures used by the WDSM population-ratio layer.
It keeps the final finite-to-population ratio algebra explicit and reusable.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Unit : Type*}

/--
Two finite weighted-mean recovery statements induce the abstract PATE
representation used by the Hájek ratio layer.
-/
noncomputable def pateRepresentationOfWeightedSampleMeanEq
    (treatedSample controlSample : Finset Unit)
    (treatedWeight controlWeight treatedOutcome controlOutcome : Unit -> Real)
    (treatedTarget controlTarget : Real)
    (htreatedMean :
      weightedSampleMean treatedSample treatedWeight treatedOutcome =
        treatedTarget)
    (hcontrolMean :
      weightedSampleMean controlSample controlWeight controlOutcome =
        controlTarget)
    (htreatedTotal : weightedSampleTotal treatedSample treatedWeight ≠ 0)
    (hcontrolTotal : weightedSampleTotal controlSample controlWeight ≠ 0) :
    PATERepresentation where
  treated :=
    inverseSelectionIdentityOfWeightedSampleMeanEq treatedSample treatedWeight
      treatedOutcome treatedTarget htreatedMean htreatedTotal
  control :=
    inverseSelectionIdentityOfWeightedSampleMeanEq controlSample controlWeight
      controlOutcome controlTarget hcontrolMean hcontrolTotal

/--
The selected finite Hájek PATE built from two recovered arm means equals the
target finite contrast.
-/
theorem selectedHajekPATE_eq_targetContrast_of_weightedSampleMeanEq
    (treatedSample controlSample : Finset Unit)
    (treatedWeight controlWeight treatedOutcome controlOutcome : Unit -> Real)
    (treatedTarget controlTarget : Real)
    (htreatedMean :
      weightedSampleMean treatedSample treatedWeight treatedOutcome =
        treatedTarget)
    (hcontrolMean :
      weightedSampleMean controlSample controlWeight controlOutcome =
        controlTarget)
    (htreatedTotal : weightedSampleTotal treatedSample treatedWeight ≠ 0)
    (hcontrolTotal : weightedSampleTotal controlSample controlWeight ≠ 0) :
    PATERepresentation.selectedHajekPATE
        (pateRepresentationOfWeightedSampleMeanEq treatedSample controlSample
          treatedWeight controlWeight treatedOutcome controlOutcome
          treatedTarget controlTarget htreatedMean hcontrolMean
          htreatedTotal hcontrolTotal) =
      treatedTarget - controlTarget := by
  have htreatedSampling :
      (pateRepresentationOfWeightedSampleMeanEq treatedSample controlSample
          treatedWeight controlWeight treatedOutcome controlOutcome
          treatedTarget controlTarget htreatedMean hcontrolMean
          htreatedTotal hcontrolTotal).treated.sampling_mass ≠ 0 := by
    simp [pateRepresentationOfWeightedSampleMeanEq,
      inverseSelectionIdentityOfWeightedSampleMeanEq, htreatedTotal]
  have hcontrolSampling :
      (pateRepresentationOfWeightedSampleMeanEq treatedSample controlSample
          treatedWeight controlWeight treatedOutcome controlOutcome
          treatedTarget controlTarget htreatedMean hcontrolMean
          htreatedTotal hcontrolTotal).control.sampling_mass ≠ 0 := by
    simp [pateRepresentationOfWeightedSampleMeanEq,
      inverseSelectionIdentityOfWeightedSampleMeanEq, hcontrolTotal]
  rw [PATERepresentation.selectedHajekPATE_eq_populationPATE
    (pateRepresentationOfWeightedSampleMeanEq treatedSample controlSample
      treatedWeight controlWeight treatedOutcome controlOutcome treatedTarget
      controlTarget htreatedMean hcontrolMean htreatedTotal hcontrolTotal)
    htreatedSampling hcontrolSampling]
  rfl

/--
Construct the PATT representation from finite selected numerator and
denominator scaling identities sharing a common abstract sampling mass.
-/
noncomputable def pattRepresentationOfFiniteScaleIdentities
    (selectedEffect selectedMass populationEffectNumerator populationMass
      samplingMass : Real)
    (hnumerator :
      selectedEffect = populationEffectNumerator / samplingMass)
    (hmass :
      selectedMass = populationMass / samplingMass) :
    PATTRepresentation where
  selected_weighted_treated_effect := selectedEffect
  selected_weighted_treated_mass := selectedMass
  population_treated_effect_numerator := populationEffectNumerator
  population_treated_mass := populationMass
  sampling_mass := samplingMass
  numerator_identity := hnumerator
  denominator_identity := hmass

/--
The finite PATT Hájek ratio equals the target PATT whenever the selected
effect numerator and treated-mass denominator share the same scaling identity.
-/
theorem selectedHajekPATT_eq_populationPATT_of_finiteScaleIdentities
    (selectedEffect selectedMass populationEffectNumerator populationMass
      samplingMass : Real)
    (hnumerator :
      selectedEffect = populationEffectNumerator / samplingMass)
    (hmass :
      selectedMass = populationMass / samplingMass)
    (hsampling : samplingMass ≠ 0)
    (hpopulationMass : populationMass ≠ 0) :
    PATTRepresentation.selectedHajekPATT
        (pattRepresentationOfFiniteScaleIdentities selectedEffect selectedMass
          populationEffectNumerator populationMass samplingMass hnumerator
          hmass) =
      populationEffectNumerator / populationMass := by
  exact
    PATTRepresentation.selectedHajekPATT_eq_populationPATT
      (pattRepresentationOfFiniteScaleIdentities selectedEffect selectedMass
        populationEffectNumerator populationMass samplingMass hnumerator hmass)
      hsampling hpopulationMass

end WDSM
end Matching
end StatInference
