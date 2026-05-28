import StatInference.Matching.WDSM.PopulationSelectionDensityDesign
import StatInference.Matching.WDSM.ConditionalMeanIntegralBridge
import StatInference.Matching.WDSM.ConditionalOrthogonalityBridge

/-!
# Population selection-density design residual orthogonality

This module connects the population selection-density design layer to the
residual orthogonality facts used by residual variance and CLT arguments.  The
results are still population-level: they do not prove a residual CLT, but they
turn conditional score-space mean assumptions into exact zero residual moments
and selected-law survey-weighted residual means.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open scoped MeasureTheory ENNReal

variable {Sample : Type*} [mSample : MeasurableSpace Sample]
variable {scoreSigma : MeasurableSpace Sample}
variable {selectedLaw populationLaw : Measure[mSample] Sample}

private def designResidualWeightReal
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw) :
    Sample -> Real :=
  fun sample =>
    ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample selectedLaw
      populationLaw design) sample : Real)

/--
If a score-space version is the conditional expectation of an integrable
outcome, then the centered residual has population integral zero.
-/
theorem integral_centeredResidual_eq_zero_of_condExp_scoreVersion
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (outcome scoreVersion : Sample -> Real)
    (houtcome : Integrable outcome populationLaw)
    (hscore : Integrable scoreVersion populationLaw)
    (hcond :
      populationLaw[outcome | scoreSigma] =ᵐ[populationLaw] scoreVersion) :
    ∫ sample, (outcome sample - scoreVersion sample) ∂populationLaw = 0 := by
  have hmean :=
    integral_eq_scoreVersion_of_condExp_ae_eq
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := populationLaw) hsub outcome scoreVersion hcond
  rw [integral_sub houtcome hscore]
  rw [hmean]
  simp

/--
Under a population selection-density design, the selected-law survey-weighted
integral of a centered residual is zero.
-/
theorem selectedWeightedIntegral_centeredResidual_eq_zero_of_selectionDensityDesign
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (houtcome : Integrable outcome populationLaw)
    (hscore : Integrable scoreVersion populationLaw)
    (hcond :
      populationLaw[outcome | scoreSigma] =ᵐ[populationLaw] scoreVersion) :
    (∫ sample,
        (@designResidualWeightReal Sample mSample selectedLaw populationLaw
          design) sample * (outcome sample - scoreVersion sample)
        ∂selectedLaw) = 0 := by
  have hresidualZero :
      ∫ sample, (outcome sample - scoreVersion sample) ∂populationLaw = 0 :=
    integral_centeredResidual_eq_zero_of_condExp_scoreVersion
      (mSample := mSample) (scoreSigma := scoreSigma)
      (populationLaw := populationLaw) hsub outcome scoreVersion houtcome
      hscore hcond
  have hrecovery :=
    @PopulationSelectionDensityDesign.surveyWeightedIntegral_eq_populationIntegral_div
      Sample mSample selectedLaw populationLaw design
      (fun sample => outcome sample - scoreVersion sample)
  simpa [designResidualWeightReal, hresidualZero] using hrecovery

/--
Under a population selection-density design, the selected-law survey-weighted
Hájek mean of a centered residual is zero.
-/
theorem selectedHajek_centeredResidual_eq_zero_of_selectionDensityDesign
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1)
    (houtcome : Integrable outcome populationLaw)
    (hscore : Integrable scoreVersion populationLaw)
    (hcond :
      populationLaw[outcome | scoreSigma] =ᵐ[populationLaw] scoreVersion) :
    (∫ sample,
        (@designResidualWeightReal Sample mSample selectedLaw populationLaw
          design) sample * (outcome sample - scoreVersion sample)
        ∂selectedLaw) /
        (∫ sample,
          (@designResidualWeightReal Sample mSample selectedLaw populationLaw
            design) sample ∂selectedLaw) = 0 := by
  have hresidualZero :
      ∫ sample, (outcome sample - scoreVersion sample) ∂populationLaw = 0 :=
    integral_centeredResidual_eq_zero_of_condExp_scoreVersion
      (mSample := mSample) (scoreSigma := scoreSigma)
      (populationLaw := populationLaw) hsub outcome scoreVersion houtcome
      hscore hcond
  have hratio :=
    @PopulationSelectionDensityDesign.hajekRatio_eq_populationIntegral
      Sample mSample selectedLaw populationLaw design
      (fun sample => outcome sample - scoreVersion sample) hpopulationOne
  simpa [designResidualWeightReal, hresidualZero] using hratio

/--
If the design survey weight is score-sigma measurable, then it is
population-orthogonal to the centered residual induced by a score-space
conditional mean.
-/
theorem integral_scoreMeasurable_designWeight_mul_centeredResidual_eq_zero
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (hweightMeas :
      AEStronglyMeasurable[scoreSigma]
        (@designResidualWeightReal Sample mSample selectedLaw populationLaw
          design) populationLaw)
    (houtcome : Integrable outcome populationLaw)
    (hscore : Integrable scoreVersion populationLaw)
    (hscoreMeas :
      AEStronglyMeasurable[scoreSigma] scoreVersion populationLaw)
    (hproduct :
      Integrable
        (fun sample =>
          (@designResidualWeightReal Sample mSample selectedLaw populationLaw
            design) sample * (outcome sample - scoreVersion sample))
        populationLaw)
    (hcond :
      populationLaw[outcome | scoreSigma] =ᵐ[populationLaw] scoreVersion) :
    ∫ sample,
      (@designResidualWeightReal Sample mSample selectedLaw populationLaw
        design) sample * (outcome sample - scoreVersion sample)
      ∂populationLaw = 0 := by
  have hzero :
      populationLaw[(fun sample => outcome sample - scoreVersion sample) |
        scoreSigma] =ᵐ[populationLaw] 0 :=
    condExp_residual_ae_eq_zero_of_condExp_ae_eq_scoreVersion_aestronglyMeasurable
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := populationLaw) hsub outcome scoreVersion houtcome hscore
      hscoreMeas hcond
  exact
    integral_scoreMeasurable_mul_residual_eq_zero
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := populationLaw) hsub
      (@designResidualWeightReal Sample mSample selectedLaw populationLaw
        design)
      (fun sample => outcome sample - scoreVersion sample)
      hweightMeas hproduct (houtcome.sub hscore) hzero

end WDSM
end Matching
end StatInference
