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
ENNReal version of survey-weight density integration.  This is the form aligned
with Radon-Nikodym densities; the finite-a.e. hypothesis lets Mathlib convert
the density to its real-valued `toReal` version inside the integral.
-/
theorem surveyWeightIntegral_eq_withDensityIntegral_ennreal
    (selectedLaw : Measure Sample) (surveyWeight : Sample -> ENNReal)
    (target : Sample -> Real)
    (hweightMeas : Measurable surveyWeight)
    (hweight_lt_top : ∀ᵐ sample ∂selectedLaw, surveyWeight sample < ∞) :
    (∫ sample, (surveyWeight sample).toReal * target sample ∂selectedLaw) =
      ∫ sample, target sample ∂selectedLaw.withDensity surveyWeight := by
  rw [integral_withDensity_eq_integral_toReal_smul hweightMeas
    hweight_lt_top target]
  simp [smul_eq_mul]

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
ENNReal density-scaling recovery: if an ENNReal survey-weight density reweights
the selected law into the population law scaled by `1 / samplingMass`, then the
real-valued weighted selected integral recovers the population integral divided
by `samplingMass`.
-/
theorem surveyWeightIntegral_eq_populationIntegral_div_of_ennreal_densityScaling
    (selectedLaw populationLaw : Measure Sample)
    (surveyWeight : Sample -> ENNReal) (target : Sample -> Real)
    (samplingMass : Real)
    (hweightMeas : Measurable surveyWeight)
    (hweight_lt_top : ∀ᵐ sample ∂selectedLaw, surveyWeight sample < ∞)
    (hsampling_pos : 0 < samplingMass)
    (hmeasure :
      selectedLaw.withDensity surveyWeight =
        ENNReal.ofReal (1 / samplingMass) • populationLaw) :
    (∫ sample, (surveyWeight sample).toReal * target sample ∂selectedLaw) =
      (∫ sample, target sample ∂populationLaw) / samplingMass := by
  rw [surveyWeightIntegral_eq_withDensityIntegral_ennreal selectedLaw
    surveyWeight target hweightMeas hweight_lt_top]
  exact
    weightedMeasureIntegral_eq_populationIntegral_div_of_measure_eq
      (selectedLaw.withDensity surveyWeight)
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

/--
Arm-specific survey-density scaling recovers the population PATE contrast from
selected-law survey-weighted Hájek ratios.
-/
theorem surveyWeightDensityPATE_eq_populationIntegralPATE_of_densityScaling
    (selectedLaw populationLaw : Measure Sample)
    (treatedWeight controlWeight : Sample -> NNReal)
    (treatedOutcome controlOutcome : Sample -> Real)
    (treatedSamplingMass controlSamplingMass : Real)
    (htreatedWeightMeas : Measurable treatedWeight)
    (hcontrolWeightMeas : Measurable controlWeight)
    (htreatedSampling_pos : 0 < treatedSamplingMass)
    (hcontrolSampling_pos : 0 < controlSamplingMass)
    (htreatedMeasure :
      selectedLaw.withDensity
          (fun sample => (treatedWeight sample : ENNReal)) =
        ENNReal.ofReal (1 / treatedSamplingMass) • populationLaw)
    (hcontrolMeasure :
      selectedLaw.withDensity
          (fun sample => (controlWeight sample : ENNReal)) =
        ENNReal.ofReal (1 / controlSamplingMass) • populationLaw)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1) :
    (∫ sample, (treatedWeight sample : Real) * treatedOutcome sample
        ∂selectedLaw) /
        (∫ sample, (treatedWeight sample : Real) ∂selectedLaw) -
      (∫ sample, (controlWeight sample : Real) * controlOutcome sample
          ∂selectedLaw) /
        (∫ sample, (controlWeight sample : Real) ∂selectedLaw) =
      (∫ sample, treatedOutcome sample ∂populationLaw) -
        (∫ sample, controlOutcome sample ∂populationLaw) := by
  rw [surveyWeightDensityRatio_eq_populationIntegral_of_densityScaling
    selectedLaw populationLaw treatedWeight treatedOutcome treatedSamplingMass
    htreatedWeightMeas htreatedSampling_pos htreatedMeasure hpopulationOne]
  rw [surveyWeightDensityRatio_eq_populationIntegral_of_densityScaling
    selectedLaw populationLaw controlWeight controlOutcome controlSamplingMass
    hcontrolWeightMeas hcontrolSampling_pos hcontrolMeasure hpopulationOne]

/--
Common survey-density scaling recovers the population PATT ratio from the
selected-law survey-weighted numerator and treated-mass denominator.
-/
theorem surveyWeightDensityPATT_eq_populationIntegralPATT_of_densityScaling
    (selectedLaw populationLaw : Measure Sample)
    (surveyWeight : Sample -> NNReal)
    (treatedEffect treatedMass : Sample -> Real)
    (samplingMass : Real)
    (hweightMeas : Measurable surveyWeight)
    (hsampling_pos : 0 < samplingMass)
    (hmeasure :
      selectedLaw.withDensity (fun sample => (surveyWeight sample : ENNReal)) =
        ENNReal.ofReal (1 / samplingMass) • populationLaw)
    (hpopulationMass :
      (∫ sample, treatedMass sample ∂populationLaw) ≠ 0) :
    (∫ sample, (surveyWeight sample : Real) * treatedEffect sample
        ∂selectedLaw) /
        (∫ sample, (surveyWeight sample : Real) * treatedMass sample
          ∂selectedLaw) =
      (∫ sample, treatedEffect sample ∂populationLaw) /
        (∫ sample, treatedMass sample ∂populationLaw) := by
  rw [surveyWeightIntegral_eq_populationIntegral_div_of_densityScaling
    selectedLaw populationLaw surveyWeight treatedEffect samplingMass
    hweightMeas hsampling_pos hmeasure]
  rw [surveyWeightIntegral_eq_populationIntegral_div_of_densityScaling
    selectedLaw populationLaw surveyWeight treatedMass samplingMass
    hweightMeas hsampling_pos hmeasure]
  field_simp [ne_of_gt hsampling_pos, hpopulationMass]

/--
Paired PATE/PATT survey-density scaling recovery, used by paper-level
identification checkpoints that carry both estimands simultaneously.
-/
theorem surveyWeightDensityPATE_PATT_eq_populationIntegralPATE_PATT_of_densityScaling
    (selectedLaw populationLaw : Measure Sample)
    (treatedWeight controlWeight pattWeight : Sample -> NNReal)
    (treatedOutcome controlOutcome treatedEffect treatedMass :
      Sample -> Real)
    (treatedSamplingMass controlSamplingMass pattSamplingMass : Real)
    (htreatedWeightMeas : Measurable treatedWeight)
    (hcontrolWeightMeas : Measurable controlWeight)
    (hpattWeightMeas : Measurable pattWeight)
    (htreatedSampling_pos : 0 < treatedSamplingMass)
    (hcontrolSampling_pos : 0 < controlSamplingMass)
    (hpattSampling_pos : 0 < pattSamplingMass)
    (htreatedMeasure :
      selectedLaw.withDensity
          (fun sample => (treatedWeight sample : ENNReal)) =
        ENNReal.ofReal (1 / treatedSamplingMass) • populationLaw)
    (hcontrolMeasure :
      selectedLaw.withDensity
          (fun sample => (controlWeight sample : ENNReal)) =
        ENNReal.ofReal (1 / controlSamplingMass) • populationLaw)
    (hpattMeasure :
      selectedLaw.withDensity (fun sample => (pattWeight sample : ENNReal)) =
        ENNReal.ofReal (1 / pattSamplingMass) • populationLaw)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1)
    (hpopulationMass :
      (∫ sample, treatedMass sample ∂populationLaw) ≠ 0) :
    (∫ sample, (treatedWeight sample : Real) * treatedOutcome sample
        ∂selectedLaw) /
        (∫ sample, (treatedWeight sample : Real) ∂selectedLaw) -
      (∫ sample, (controlWeight sample : Real) * controlOutcome sample
          ∂selectedLaw) /
        (∫ sample, (controlWeight sample : Real) ∂selectedLaw) =
        (∫ sample, treatedOutcome sample ∂populationLaw) -
          (∫ sample, controlOutcome sample ∂populationLaw) ∧
      (∫ sample, (pattWeight sample : Real) * treatedEffect sample
          ∂selectedLaw) /
          (∫ sample, (pattWeight sample : Real) * treatedMass sample
            ∂selectedLaw) =
        (∫ sample, treatedEffect sample ∂populationLaw) /
          (∫ sample, treatedMass sample ∂populationLaw) := by
  constructor
  · exact
      surveyWeightDensityPATE_eq_populationIntegralPATE_of_densityScaling
        selectedLaw populationLaw treatedWeight controlWeight treatedOutcome
        controlOutcome treatedSamplingMass controlSamplingMass
        htreatedWeightMeas hcontrolWeightMeas htreatedSampling_pos
        hcontrolSampling_pos htreatedMeasure hcontrolMeasure hpopulationOne
  · exact
      surveyWeightDensityPATT_eq_populationIntegralPATT_of_densityScaling
        selectedLaw populationLaw pattWeight treatedEffect treatedMass
        pattSamplingMass hpattWeightMeas hpattSampling_pos hpattMeasure
        hpopulationMass

end WDSM
end Matching
end StatInference
