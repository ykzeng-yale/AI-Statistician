import StatInference.Matching.WDSM.PopulationMeasureScaling

/-!
# Population survey-density scaling bridge

This module connects literal survey-weight densities to the measure-scaling
bridge.  If the selected law reweighted by a nonnegative survey-weight density
equals the population law scaled by `1 / samplingMass`, then the weighted
selected-law integral identities required by the inverse-selection layer
follow.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open scoped MeasureTheory ENNReal

variable {Sample : Type*} [MeasurableSpace Sample]

/--
Integrating against a survey-weight density is the same as integrating the
survey-weighted target against the selected law.
-/
theorem surveyWeightIntegral_eq_withDensityIntegral
    (selectedLaw : Measure Sample) (surveyWeight : Sample -> NNReal)
    (target : Sample -> Real)
    (hweightMeas : Measurable surveyWeight) :
    (∫ sample, (surveyWeight sample : Real) * target sample ∂selectedLaw) =
      ∫ sample, target sample
        ∂selectedLaw.withDensity (fun sample => (surveyWeight sample : ENNReal)) := by
  rw [integral_withDensity_eq_integral_smul hweightMeas target]
  simp [NNReal.smul_def, smul_eq_mul]

/--
If the survey-weight density reweights the selected law into the population law
scaled by `1 / samplingMass`, then every survey-weighted selected integral
recovers the corresponding population integral divided by `samplingMass`.
-/
theorem surveyWeightIntegral_eq_populationIntegral_div_of_densityScaling
    (selectedLaw populationLaw : Measure Sample)
    (surveyWeight : Sample -> NNReal) (target : Sample -> Real)
    (samplingMass : Real)
    (hweightMeas : Measurable surveyWeight)
    (hsampling_pos : 0 < samplingMass)
    (hmeasure :
      selectedLaw.withDensity (fun sample => (surveyWeight sample : ENNReal)) =
        ENNReal.ofReal (1 / samplingMass) • populationLaw) :
    (∫ sample, (surveyWeight sample : Real) * target sample ∂selectedLaw) =
      (∫ sample, target sample ∂populationLaw) / samplingMass := by
  rw [surveyWeightIntegral_eq_withDensityIntegral selectedLaw surveyWeight
    target hweightMeas]
  exact
    weightedMeasureIntegral_eq_populationIntegral_div_of_measure_eq
      (selectedLaw.withDensity
        (fun sample => (surveyWeight sample : ENNReal)))
      populationLaw target samplingMass hsampling_pos hmeasure

/--
Density-scaling recovery packaged as the abstract inverse-selection identity.
This is the direct target for a future formal survey-ignorability theorem.
-/
noncomputable def inverseSelectionIdentityOfSurveyWeightDensityScaling
    (selectedLaw populationLaw : Measure Sample)
    (surveyWeight : Sample -> NNReal) (target : Sample -> Real)
    (samplingMass : Real)
    (hweightMeas : Measurable surveyWeight)
    (hsampling_pos : 0 < samplingMass)
    (hmeasure :
      selectedLaw.withDensity (fun sample => (surveyWeight sample : ENNReal)) =
        ENNReal.ofReal (1 / samplingMass) • populationLaw)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1) :
    InverseSelectionIdentity :=
  inverseSelectionIdentityOfWeightedIntegralRecovery selectedLaw populationLaw
    (fun sample => (surveyWeight sample : Real)) target samplingMass
    (surveyWeightIntegral_eq_populationIntegral_div_of_densityScaling
      selectedLaw populationLaw surveyWeight target samplingMass hweightMeas
      hsampling_pos hmeasure)
    (by
      have h :=
        surveyWeightIntegral_eq_populationIntegral_div_of_densityScaling
          selectedLaw populationLaw surveyWeight (fun _sample => (1 : Real))
          samplingMass hweightMeas hsampling_pos hmeasure
      simpa [hpopulationOne] using h)

/--
The selected-law survey-weighted Hájek ratio recovers the population integral
under survey-density scaling.
-/
theorem surveyWeightDensityRatio_eq_populationIntegral_of_densityScaling
    (selectedLaw populationLaw : Measure Sample)
    (surveyWeight : Sample -> NNReal) (target : Sample -> Real)
    (samplingMass : Real)
    (hweightMeas : Measurable surveyWeight)
    (hsampling_pos : 0 < samplingMass)
    (hmeasure :
      selectedLaw.withDensity (fun sample => (surveyWeight sample : ENNReal)) =
        ENNReal.ofReal (1 / samplingMass) • populationLaw)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1) :
    (∫ sample, (surveyWeight sample : Real) * target sample ∂selectedLaw) /
        (∫ sample, (surveyWeight sample : Real) ∂selectedLaw) =
      ∫ sample, target sample ∂populationLaw := by
  exact
    InverseSelectionIdentity.hajekRatio_eq_populationTarget
      (inverseSelectionIdentityOfSurveyWeightDensityScaling selectedLaw
        populationLaw surveyWeight target samplingMass hweightMeas
        hsampling_pos hmeasure hpopulationOne)
      (ne_of_gt hsampling_pos)

end WDSM
end Matching
end StatInference
