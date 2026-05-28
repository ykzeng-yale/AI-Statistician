import StatInference.Matching.WDSM.PopulationSurveyDensityScaling

/-!
# Population survey selection-density bridge

This module proves the density equality targeted by the survey-density scaling
bridge from a more primitive survey design representation: the selected law is
the population law tilted by the selection probability and normalized by the
sampling mass, while the survey weight is the inverse of the selection
probability.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open scoped MeasureTheory ENNReal

variable {Sample : Type*} [MeasurableSpace Sample]

/--
If the selected law has density proportional to the selection probability and
the survey weight is pointwise inverse to that selection probability, then
density-reweighting the selected law by the survey weight gives the population
law scaled by `1 / samplingMass`.
-/
theorem selectedLaw_withDensity_surveyWeight_eq_scaled_populationLaw
    (selectedLaw populationLaw : Measure Sample)
    (selectionProb surveyWeight : Sample -> NNReal)
    (samplingMass : Real)
    (hselectionMeas : Measurable selectionProb)
    (hweightMeas : Measurable surveyWeight)
    (hselectedLaw :
      selectedLaw =
        ENNReal.ofReal (1 / samplingMass) •
          populationLaw.withDensity
            (fun sample => (selectionProb sample : ENNReal)))
    (hinverse :
      ∀ sample,
        (selectionProb sample : ENNReal) *
          (surveyWeight sample : ENNReal) = 1) :
    selectedLaw.withDensity (fun sample => (surveyWeight sample : ENNReal)) =
      ENNReal.ofReal (1 / samplingMass) • populationLaw := by
  rw [hselectedLaw]
  rw [withDensity_smul_measure]
  rw [← withDensity_mul populationLaw hselectionMeas.coe_nnreal_ennreal
    hweightMeas.coe_nnreal_ennreal]
  rw [withDensity_congr_ae
    (Filter.Eventually.of_forall
      (fun sample => by
        exact hinverse sample))]
  change
    ENNReal.ofReal (1 / samplingMass) •
        populationLaw.withDensity (1 : Sample -> ENNReal) =
      ENNReal.ofReal (1 / samplingMass) • populationLaw
  rw [withDensity_one]

/--
Under the primitive selection-density representation and inverse survey-weight
condition, the selected-law survey-weighted Hájek ratio recovers the population
integral.
-/
theorem surveyWeightDensityRatio_eq_populationIntegral_of_selectionDensity
    (selectedLaw populationLaw : Measure Sample)
    (selectionProb surveyWeight : Sample -> NNReal)
    (target : Sample -> Real)
    (samplingMass : Real)
    (hselectionMeas : Measurable selectionProb)
    (hweightMeas : Measurable surveyWeight)
    (hsampling_pos : 0 < samplingMass)
    (hselectedLaw :
      selectedLaw =
        ENNReal.ofReal (1 / samplingMass) •
          populationLaw.withDensity
            (fun sample => (selectionProb sample : ENNReal)))
    (hinverse :
      ∀ sample,
        (selectionProb sample : ENNReal) *
          (surveyWeight sample : ENNReal) = 1)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1) :
    (∫ sample, (surveyWeight sample : Real) * target sample ∂selectedLaw) /
        (∫ sample, (surveyWeight sample : Real) ∂selectedLaw) =
      ∫ sample, target sample ∂populationLaw := by
  exact
    surveyWeightDensityRatio_eq_populationIntegral_of_densityScaling
      selectedLaw populationLaw surveyWeight target samplingMass hweightMeas
      hsampling_pos
      (selectedLaw_withDensity_surveyWeight_eq_scaled_populationLaw
        selectedLaw populationLaw selectionProb surveyWeight samplingMass
        hselectionMeas hweightMeas hselectedLaw hinverse)
      hpopulationOne

/--
Primitive selection-density assumptions imply selected-law survey-weighted
PATE recovery for two arm-specific inverse survey weights.
-/
theorem surveyWeightDensityPATE_eq_populationIntegralPATE_of_selectionDensity
    (selectedLaw populationLaw : Measure Sample)
    (treatedSelectionProb controlSelectionProb
      treatedWeight controlWeight : Sample -> NNReal)
    (treatedOutcome controlOutcome : Sample -> Real)
    (treatedSamplingMass controlSamplingMass : Real)
    (htreatedSelectionMeas : Measurable treatedSelectionProb)
    (hcontrolSelectionMeas : Measurable controlSelectionProb)
    (htreatedWeightMeas : Measurable treatedWeight)
    (hcontrolWeightMeas : Measurable controlWeight)
    (htreatedSampling_pos : 0 < treatedSamplingMass)
    (hcontrolSampling_pos : 0 < controlSamplingMass)
    (htreatedSelectedLaw :
      selectedLaw =
        ENNReal.ofReal (1 / treatedSamplingMass) •
          populationLaw.withDensity
            (fun sample => (treatedSelectionProb sample : ENNReal)))
    (hcontrolSelectedLaw :
      selectedLaw =
        ENNReal.ofReal (1 / controlSamplingMass) •
          populationLaw.withDensity
            (fun sample => (controlSelectionProb sample : ENNReal)))
    (htreatedInverse :
      ∀ sample,
        (treatedSelectionProb sample : ENNReal) *
          (treatedWeight sample : ENNReal) = 1)
    (hcontrolInverse :
      ∀ sample,
        (controlSelectionProb sample : ENNReal) *
          (controlWeight sample : ENNReal) = 1)
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
  exact
    surveyWeightDensityPATE_eq_populationIntegralPATE_of_densityScaling
      selectedLaw populationLaw treatedWeight controlWeight treatedOutcome
      controlOutcome treatedSamplingMass controlSamplingMass
      htreatedWeightMeas hcontrolWeightMeas htreatedSampling_pos
      hcontrolSampling_pos
      (selectedLaw_withDensity_surveyWeight_eq_scaled_populationLaw
        selectedLaw populationLaw treatedSelectionProb treatedWeight
        treatedSamplingMass htreatedSelectionMeas htreatedWeightMeas
        htreatedSelectedLaw htreatedInverse)
      (selectedLaw_withDensity_surveyWeight_eq_scaled_populationLaw
        selectedLaw populationLaw controlSelectionProb controlWeight
        controlSamplingMass hcontrolSelectionMeas hcontrolWeightMeas
        hcontrolSelectedLaw hcontrolInverse)
      hpopulationOne

/--
Primitive selection-density assumptions imply selected-law survey-weighted
PATT recovery for a common inverse survey weight.
-/
theorem surveyWeightDensityPATT_eq_populationIntegralPATT_of_selectionDensity
    (selectedLaw populationLaw : Measure Sample)
    (selectionProb surveyWeight : Sample -> NNReal)
    (treatedEffect treatedMass : Sample -> Real)
    (samplingMass : Real)
    (hselectionMeas : Measurable selectionProb)
    (hweightMeas : Measurable surveyWeight)
    (hsampling_pos : 0 < samplingMass)
    (hselectedLaw :
      selectedLaw =
        ENNReal.ofReal (1 / samplingMass) •
          populationLaw.withDensity
            (fun sample => (selectionProb sample : ENNReal)))
    (hinverse :
      ∀ sample,
        (selectionProb sample : ENNReal) *
          (surveyWeight sample : ENNReal) = 1)
    (hpopulationMass :
      (∫ sample, treatedMass sample ∂populationLaw) ≠ 0) :
    (∫ sample, (surveyWeight sample : Real) * treatedEffect sample
        ∂selectedLaw) /
        (∫ sample, (surveyWeight sample : Real) * treatedMass sample
          ∂selectedLaw) =
      (∫ sample, treatedEffect sample ∂populationLaw) /
        (∫ sample, treatedMass sample ∂populationLaw) := by
  exact
    surveyWeightDensityPATT_eq_populationIntegralPATT_of_densityScaling
      selectedLaw populationLaw surveyWeight treatedEffect treatedMass
      samplingMass hweightMeas hsampling_pos
      (selectedLaw_withDensity_surveyWeight_eq_scaled_populationLaw
        selectedLaw populationLaw selectionProb surveyWeight samplingMass
        hselectionMeas hweightMeas hselectedLaw hinverse)
      hpopulationMass

/--
Primitive selection-density assumptions imply paired selected-law
survey-weighted PATE/PATT recovery.
-/
theorem
    surveyWeightDensityPATE_PATT_eq_populationIntegralPATE_PATT_of_selectionDensity
    (selectedLaw populationLaw : Measure Sample)
    (treatedSelectionProb controlSelectionProb pattSelectionProb
      treatedWeight controlWeight pattWeight : Sample -> NNReal)
    (treatedOutcome controlOutcome treatedEffect treatedMass : Sample -> Real)
    (treatedSamplingMass controlSamplingMass pattSamplingMass : Real)
    (htreatedSelectionMeas : Measurable treatedSelectionProb)
    (hcontrolSelectionMeas : Measurable controlSelectionProb)
    (hpattSelectionMeas : Measurable pattSelectionProb)
    (htreatedWeightMeas : Measurable treatedWeight)
    (hcontrolWeightMeas : Measurable controlWeight)
    (hpattWeightMeas : Measurable pattWeight)
    (htreatedSampling_pos : 0 < treatedSamplingMass)
    (hcontrolSampling_pos : 0 < controlSamplingMass)
    (hpattSampling_pos : 0 < pattSamplingMass)
    (htreatedSelectedLaw :
      selectedLaw =
        ENNReal.ofReal (1 / treatedSamplingMass) •
          populationLaw.withDensity
            (fun sample => (treatedSelectionProb sample : ENNReal)))
    (hcontrolSelectedLaw :
      selectedLaw =
        ENNReal.ofReal (1 / controlSamplingMass) •
          populationLaw.withDensity
            (fun sample => (controlSelectionProb sample : ENNReal)))
    (hpattSelectedLaw :
      selectedLaw =
        ENNReal.ofReal (1 / pattSamplingMass) •
          populationLaw.withDensity
            (fun sample => (pattSelectionProb sample : ENNReal)))
    (htreatedInverse :
      ∀ sample,
        (treatedSelectionProb sample : ENNReal) *
          (treatedWeight sample : ENNReal) = 1)
    (hcontrolInverse :
      ∀ sample,
        (controlSelectionProb sample : ENNReal) *
          (controlWeight sample : ENNReal) = 1)
    (hpattInverse :
      ∀ sample,
        (pattSelectionProb sample : ENNReal) *
          (pattWeight sample : ENNReal) = 1)
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
  exact
    surveyWeightDensityPATE_PATT_eq_populationIntegralPATE_PATT_of_densityScaling
      selectedLaw populationLaw treatedWeight controlWeight pattWeight
      treatedOutcome controlOutcome treatedEffect treatedMass
      treatedSamplingMass controlSamplingMass pattSamplingMass
      htreatedWeightMeas hcontrolWeightMeas hpattWeightMeas
      htreatedSampling_pos hcontrolSampling_pos hpattSampling_pos
      (selectedLaw_withDensity_surveyWeight_eq_scaled_populationLaw
        selectedLaw populationLaw treatedSelectionProb treatedWeight
        treatedSamplingMass htreatedSelectionMeas htreatedWeightMeas
        htreatedSelectedLaw htreatedInverse)
      (selectedLaw_withDensity_surveyWeight_eq_scaled_populationLaw
        selectedLaw populationLaw controlSelectionProb controlWeight
        controlSamplingMass hcontrolSelectionMeas hcontrolWeightMeas
        hcontrolSelectedLaw hcontrolInverse)
      (selectedLaw_withDensity_surveyWeight_eq_scaled_populationLaw
        selectedLaw populationLaw pattSelectionProb pattWeight
        pattSamplingMass hpattSelectionMeas hpattWeightMeas hpattSelectedLaw
        hpattInverse)
      hpopulationOne hpopulationMass

end WDSM
end Matching
end StatInference
