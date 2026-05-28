import StatInference.Matching.WDSM.PopulationInverseSelectionIdentity

/-!
# Population measure-scaling bridge

This module proves a concrete sufficient condition for the weighted
selected-law integral recovery identities used by
`PopulationInverseSelectionIdentity`: if the weighted selected measure is the
population law scaled by `1 / samplingMass`, then weighted selected integrals
are population integrals divided by `samplingMass`.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open scoped MeasureTheory ENNReal

variable {Sample : Type*} [MeasurableSpace Sample]

/--
Integrating against a population law scaled by a nonnegative real constant
multiplies the population integral by that constant.
-/
theorem integral_smul_measure_ofReal
    (populationLaw : Measure Sample) (target : Sample -> Real)
    (scale : Real) (hscale_nonneg : 0 ≤ scale) :
    (∫ sample, target sample ∂(ENNReal.ofReal scale • populationLaw)) =
      scale * (∫ sample, target sample ∂populationLaw) := by
  rw [integral_smul_measure]
  rw [ENNReal.toReal_ofReal hscale_nonneg]
  simp [smul_eq_mul]

/--
Integrating against the population law scaled by `1 / samplingMass` divides
the population integral by `samplingMass`.
-/
theorem integral_smul_measure_ofReal_inv_samplingMass
    (populationLaw : Measure Sample) (target : Sample -> Real)
    (samplingMass : Real) (hsampling_pos : 0 < samplingMass) :
    (∫ sample, target sample
        ∂(ENNReal.ofReal (1 / samplingMass) • populationLaw)) =
      (∫ sample, target sample ∂populationLaw) / samplingMass := by
  have hinv_nonneg : 0 ≤ 1 / samplingMass := by
    exact div_nonneg zero_le_one (le_of_lt hsampling_pos)
  rw [integral_smul_measure_ofReal populationLaw target (1 / samplingMass)
    hinv_nonneg]
  ring

/--
If a weighted selected measure is a nonnegative real multiple of the population
law, then weighted selected integrals are the same multiple of population
integrals.
-/
theorem weightedMeasureIntegral_eq_scale_mul_populationIntegral_of_measure_eq
    (weightedSelectedLaw populationLaw : Measure Sample)
    (target : Sample -> Real) (scale : Real) (hscale_nonneg : 0 ≤ scale)
    (hmeasure :
      weightedSelectedLaw = ENNReal.ofReal scale • populationLaw) :
    (∫ sample, target sample ∂weightedSelectedLaw) =
      scale * (∫ sample, target sample ∂populationLaw) := by
  rw [hmeasure]
  exact integral_smul_measure_ofReal populationLaw target scale hscale_nonneg

/--
If a weighted selected measure equals the population law scaled by
`1 / samplingMass`, then integrals over that weighted selected measure recover
population integrals divided by `samplingMass`.
-/
theorem weightedMeasureIntegral_eq_populationIntegral_div_of_measure_eq
    (weightedSelectedLaw populationLaw : Measure Sample)
    (target : Sample -> Real) (samplingMass : Real)
    (hsampling_pos : 0 < samplingMass)
    (hmeasure :
      weightedSelectedLaw =
        ENNReal.ofReal (1 / samplingMass) • populationLaw) :
    (∫ sample, target sample ∂weightedSelectedLaw) =
      (∫ sample, target sample ∂populationLaw) / samplingMass := by
  rw [hmeasure]
  exact integral_smul_measure_ofReal_inv_samplingMass populationLaw target
    samplingMass hsampling_pos

/--
Measure-scaling recovery packaged as an `InverseSelectionIdentity`.  The
population-total hypothesis is the measure-level analogue of the selected
denominator identity.
-/
noncomputable def inverseSelectionIdentityOfWeightedMeasureScaling
    (weightedSelectedLaw populationLaw : Measure Sample)
    (target : Sample -> Real) (samplingMass : Real)
    (hsampling_pos : 0 < samplingMass)
    (hmeasure :
      weightedSelectedLaw =
        ENNReal.ofReal (1 / samplingMass) • populationLaw)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1) :
    InverseSelectionIdentity where
  selected_weighted_target := ∫ sample, target sample ∂weightedSelectedLaw
  selected_weighted_one := ∫ _sample, (1 : Real) ∂weightedSelectedLaw
  population_target := ∫ sample, target sample ∂populationLaw
  sampling_mass := samplingMass
  target_identity :=
    weightedMeasureIntegral_eq_populationIntegral_div_of_measure_eq
      weightedSelectedLaw populationLaw target samplingMass hsampling_pos
      hmeasure
  one_identity := by
    rw [weightedMeasureIntegral_eq_populationIntegral_div_of_measure_eq
      weightedSelectedLaw populationLaw (fun _sample => (1 : Real))
      samplingMass hsampling_pos hmeasure]
    rw [hpopulationOne]

/--
The Hájek ratio for a weighted selected measure satisfying the scaling
identity recovers the population integral.
-/
theorem weightedMeasureRatio_eq_populationIntegral_of_measureScaling
    (weightedSelectedLaw populationLaw : Measure Sample)
    (target : Sample -> Real) (samplingMass : Real)
    (hsampling_pos : 0 < samplingMass)
    (hmeasure :
      weightedSelectedLaw =
        ENNReal.ofReal (1 / samplingMass) • populationLaw)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1) :
    (∫ sample, target sample ∂weightedSelectedLaw) /
        (∫ _sample, (1 : Real) ∂weightedSelectedLaw) =
      ∫ sample, target sample ∂populationLaw := by
  exact
    InverseSelectionIdentity.hajekRatio_eq_populationTarget
      (inverseSelectionIdentityOfWeightedMeasureScaling weightedSelectedLaw
        populationLaw target samplingMass hsampling_pos hmeasure
        hpopulationOne)
      (ne_of_gt hsampling_pos)

/--
Arm-specific measure-scaling identities recover the population PATE contrast
from selected-law weighted Hájek ratios.
-/
theorem weightedMeasurePATE_eq_populationIntegralPATE_of_measureScaling
    (treatedWeightedSelectedLaw controlWeightedSelectedLaw
      populationLaw : Measure Sample)
    (treatedOutcome controlOutcome : Sample -> Real)
    (treatedSamplingMass controlSamplingMass : Real)
    (htreatedSampling_pos : 0 < treatedSamplingMass)
    (hcontrolSampling_pos : 0 < controlSamplingMass)
    (htreatedMeasure :
      treatedWeightedSelectedLaw =
        ENNReal.ofReal (1 / treatedSamplingMass) • populationLaw)
    (hcontrolMeasure :
      controlWeightedSelectedLaw =
        ENNReal.ofReal (1 / controlSamplingMass) • populationLaw)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1) :
    (∫ sample, treatedOutcome sample ∂treatedWeightedSelectedLaw) /
        (∫ _sample, (1 : Real) ∂treatedWeightedSelectedLaw) -
      (∫ sample, controlOutcome sample ∂controlWeightedSelectedLaw) /
        (∫ _sample, (1 : Real) ∂controlWeightedSelectedLaw) =
      (∫ sample, treatedOutcome sample ∂populationLaw) -
        (∫ sample, controlOutcome sample ∂populationLaw) := by
  rw [weightedMeasureRatio_eq_populationIntegral_of_measureScaling
    treatedWeightedSelectedLaw populationLaw treatedOutcome
    treatedSamplingMass htreatedSampling_pos htreatedMeasure hpopulationOne]
  rw [weightedMeasureRatio_eq_populationIntegral_of_measureScaling
    controlWeightedSelectedLaw populationLaw controlOutcome
    controlSamplingMass hcontrolSampling_pos hcontrolMeasure hpopulationOne]

/--
Common measure-scaling identities recover the population PATT ratio from the
selected-law weighted numerator and treated-mass denominator.
-/
theorem weightedMeasurePATT_eq_populationIntegralPATT_of_measureScaling
    (effectWeightedSelectedLaw massWeightedSelectedLaw
      populationLaw : Measure Sample)
    (treatedEffect treatedMass : Sample -> Real)
    (samplingMass : Real)
    (hsampling_pos : 0 < samplingMass)
    (heffectMeasure :
      effectWeightedSelectedLaw =
        ENNReal.ofReal (1 / samplingMass) • populationLaw)
    (hmassMeasure :
      massWeightedSelectedLaw =
        ENNReal.ofReal (1 / samplingMass) • populationLaw)
    (hpopulationMass :
      (∫ sample, treatedMass sample ∂populationLaw) ≠ 0) :
    (∫ sample, treatedEffect sample ∂effectWeightedSelectedLaw) /
        (∫ sample, treatedMass sample ∂massWeightedSelectedLaw) =
      (∫ sample, treatedEffect sample ∂populationLaw) /
        (∫ sample, treatedMass sample ∂populationLaw) := by
  rw [weightedMeasureIntegral_eq_populationIntegral_div_of_measure_eq
    effectWeightedSelectedLaw populationLaw treatedEffect samplingMass
    hsampling_pos heffectMeasure]
  rw [weightedMeasureIntegral_eq_populationIntegral_div_of_measure_eq
    massWeightedSelectedLaw populationLaw treatedMass samplingMass
    hsampling_pos hmassMeasure]
  field_simp [ne_of_gt hsampling_pos, hpopulationMass]

end WDSM
end Matching
end StatInference
