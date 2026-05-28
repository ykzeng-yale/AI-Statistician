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

end WDSM
end Matching
end StatInference
