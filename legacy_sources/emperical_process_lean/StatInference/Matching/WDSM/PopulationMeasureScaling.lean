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
Integrating against the population law scaled by `1 / samplingMass` divides
the population integral by `samplingMass`.
-/
theorem integral_smul_measure_ofReal_inv_samplingMass
    (populationLaw : Measure Sample) (target : Sample -> Real)
    (samplingMass : Real) (hsampling_pos : 0 < samplingMass) :
    (∫ sample, target sample
        ∂(ENNReal.ofReal (1 / samplingMass) • populationLaw)) =
      (∫ sample, target sample ∂populationLaw) / samplingMass := by
  rw [integral_smul_measure]
  have hinv_nonneg : 0 ≤ 1 / samplingMass := by
    exact div_nonneg zero_le_one (le_of_lt hsampling_pos)
  rw [ENNReal.toReal_ofReal hinv_nonneg]
  ring

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

end WDSM
end Matching
end StatInference
