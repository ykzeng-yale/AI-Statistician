import StatInference.Matching.WDSM.PopulationSelectionDensityDesign
import StatInference.Matching.WDSM.ConditionalMeanIntegralBridge
import StatInference.Matching.WDSM.ConditionalQuadraticVariationBridge
import StatInference.Matching.WDSM.ConditionalVarianceTargetBridge

/-!
# Population selection-density design quadratic variation

This module connects population selection-density designs to the residual
second-moment and conditional-variance targets used by WDSM residual variance
and CLT arguments.  These are exact population and selected-law identities;
nearest-neighbor moment limits and martingale CLTs remain separate bridge
requirements.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open scoped MeasureTheory ENNReal

variable {Sample : Type*} [mSample : MeasurableSpace Sample]
variable {scoreSigma : MeasurableSpace Sample}
variable {selectedLaw populationLaw : Measure[mSample] Sample}

private def designQuadraticWeightReal
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw) :
    Sample -> Real :=
  fun sample =>
    ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample selectedLaw
      populationLaw design) sample : Real)

private def centeredResidualSq
    (outcome scoreVersion : Sample -> Real) : Sample -> Real :=
  fun sample =>
    (outcome sample - scoreVersion sample) *
      (outcome sample - scoreVersion sample)

/--
The raw population squared centered residual integral is nonnegative.
-/
theorem populationIntegral_centeredResidual_sq_nonneg
    (outcome scoreVersion : Sample -> Real) :
    0 ≤
      ∫ sample, centeredResidualSq outcome scoreVersion sample
        ∂populationLaw := by
  refine integral_nonneg_of_ae ?_
  filter_upwards [] with sample
  exact mul_self_nonneg (outcome sample - scoreVersion sample)

/--
The selected-law survey-weighted squared centered residual integral is
nonnegative.
-/
theorem selectedWeightedIntegral_centeredResidual_sq_nonneg
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real) :
    0 ≤
      ∫ sample,
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) sample * centeredResidualSq outcome scoreVersion sample
        ∂selectedLaw := by
  refine integral_nonneg_of_ae ?_
  filter_upwards [] with sample
  have hweight :
      0 ≤
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) sample := by
    exact
      ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
        selectedLaw populationLaw design) sample).2
  exact mul_nonneg hweight
    (by
      simpa [centeredResidualSq] using
        mul_self_nonneg (outcome sample - scoreVersion sample))

/--
The raw population squared centered residual integral is zero if the outcome
equals its score version almost everywhere under the population law.
-/
theorem populationIntegral_centeredResidual_sq_eq_zero_of_ae_eq_scoreVersion
    (outcome scoreVersion : Sample -> Real)
    (houtcome : outcome =ᵐ[populationLaw] scoreVersion) :
    (∫ sample, centeredResidualSq outcome scoreVersion sample
      ∂populationLaw) = 0 := by
  refine integral_eq_zero_of_ae ?_
  filter_upwards [houtcome] with sample hsample
  simp [centeredResidualSq, hsample]

/--
Directly named variant of population squared centered-residual zero from
population-law a.e. score-version equality.
-/
theorem populationIntegral_centeredResidual_sq_eq_zero_of_direct_ae_scoreVersion
    (outcome scoreVersion : Sample -> Real)
    (hae : outcome =ᵐ[populationLaw] scoreVersion) :
    (∫ sample, centeredResidualSq outcome scoreVersion sample
      ∂populationLaw) = 0 :=
  populationIntegral_centeredResidual_sq_eq_zero_of_ae_eq_scoreVersion
    (mSample := mSample) (populationLaw := populationLaw) outcome
    scoreVersion hae

/--
The selected-law survey-weighted squared centered residual integral is zero if
the outcome equals its score version almost everywhere under the selected law.
-/
theorem selectedWeightedIntegral_centeredResidual_sq_eq_zero_of_selected_ae_eq_scoreVersion
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (houtcome : outcome =ᵐ[selectedLaw] scoreVersion) :
    (∫ sample,
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) sample * centeredResidualSq outcome scoreVersion sample
        ∂selectedLaw) = 0 := by
  refine integral_eq_zero_of_ae ?_
  filter_upwards [houtcome] with sample hsample
  simp [centeredResidualSq, hsample]

/--
Under a population selection-density design, the selected-law survey-weighted
integral of a squared centered residual recovers the population squared
residual integral divided by the sampling mass.
-/
theorem selectedWeightedIntegral_centeredResidual_sq_eq_populationIntegral_div
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real) :
    (∫ sample,
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) sample * centeredResidualSq outcome scoreVersion sample
        ∂selectedLaw) =
      (∫ sample, centeredResidualSq outcome scoreVersion sample
        ∂populationLaw) /
        @PopulationSelectionDensityDesign.samplingMass Sample mSample
          selectedLaw populationLaw design := by
  simpa [designQuadraticWeightReal, centeredResidualSq] using
    (@PopulationSelectionDensityDesign.surveyWeightedIntegral_eq_populationIntegral_div
      Sample mSample selectedLaw populationLaw design
      (centeredResidualSq outcome scoreVersion))

/--
The selected-law survey-weighted squared centered residual integral is zero if
the outcome equals its score version almost everywhere under the population
law, by the selection-density recovery identity.
-/
theorem selectedWeightedIntegral_centeredResidual_sq_eq_zero_of_population_ae_eq_scoreVersion
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (houtcome : outcome =ᵐ[populationLaw] scoreVersion) :
    (∫ sample,
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) sample * centeredResidualSq outcome scoreVersion sample
        ∂selectedLaw) = 0 := by
  rw [selectedWeightedIntegral_centeredResidual_sq_eq_populationIntegral_div
    (mSample := mSample) (selectedLaw := selectedLaw)
    (populationLaw := populationLaw) design outcome scoreVersion]
  rw [populationIntegral_centeredResidual_sq_eq_zero_of_ae_eq_scoreVersion
    (mSample := mSample) (populationLaw := populationLaw) outcome
    scoreVersion houtcome]
  simp

/--
Directly named selected-law survey-weighted squared residual zero theorem from
population-law a.e. score-version equality.
-/
theorem selectedWeightedIntegral_centeredResidual_sq_eq_zero_of_direct_ae_scoreVersion
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (hae : outcome =ᵐ[populationLaw] scoreVersion) :
    (∫ sample,
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) sample * centeredResidualSq outcome scoreVersion sample
        ∂selectedLaw) = 0 :=
  selectedWeightedIntegral_centeredResidual_sq_eq_zero_of_population_ae_eq_scoreVersion
    (mSample := mSample) (selectedLaw := selectedLaw)
    (populationLaw := populationLaw) design outcome scoreVersion hae

/--
The raw population squared centered residual integral is nonnegative when its
conditional-variance version is nonnegative almost everywhere.
-/
theorem populationIntegral_centeredResidual_sq_nonneg_of_conditionalVariance_nonneg
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (outcome scoreVersion conditionalVariance : Sample -> Real)
    (hvariance :
      populationLaw[centeredResidualSq outcome scoreVersion | scoreSigma] =ᵐ[
        populationLaw] conditionalVariance)
    (hvarianceNonneg : 0 ≤ᵐ[populationLaw] conditionalVariance) :
    0 ≤
      ∫ sample, centeredResidualSq outcome scoreVersion sample
        ∂populationLaw := by
  rw [integral_eq_scoreVersion_of_condExp_ae_eq
    (mSample := mSample) (scoreSigma := scoreSigma)
    (sampleLaw := populationLaw) hsub
    (centeredResidualSq outcome scoreVersion) conditionalVariance hvariance]
  exact integral_nonneg_of_ae hvarianceNonneg

/--
The raw population squared centered residual integral is zero when its
conditional-variance version is zero almost everywhere.
-/
theorem populationIntegral_centeredResidual_sq_eq_zero_of_conditionalVariance_zero
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (outcome scoreVersion conditionalVariance : Sample -> Real)
    (hvariance :
      populationLaw[centeredResidualSq outcome scoreVersion | scoreSigma] =ᵐ[
        populationLaw] conditionalVariance)
    (hvarianceZero : conditionalVariance =ᵐ[populationLaw] 0) :
    (∫ sample, centeredResidualSq outcome scoreVersion sample
      ∂populationLaw) = 0 := by
  rw [integral_eq_scoreVersion_of_condExp_ae_eq
    (mSample := mSample) (scoreSigma := scoreSigma)
    (sampleLaw := populationLaw) hsub
    (centeredResidualSq outcome scoreVersion) conditionalVariance hvariance]
  exact integral_eq_zero_of_ae hvarianceZero

/--
The raw population squared centered residual integral is zero when its
score-sigma conditional second moment is zero almost everywhere.
-/
theorem populationIntegral_centeredResidual_sq_eq_zero_of_condExp_centeredResidual_sq_zero
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (outcome scoreVersion : Sample -> Real)
    (hzero :
      populationLaw[centeredResidualSq outcome scoreVersion | scoreSigma] =ᵐ[
        populationLaw] 0) :
    (∫ sample, centeredResidualSq outcome scoreVersion sample
      ∂populationLaw) = 0 :=
  populationIntegral_centeredResidual_sq_eq_zero_of_conditionalVariance_zero
    (mSample := mSample) (scoreSigma := scoreSigma)
    (populationLaw := populationLaw) hsub outcome scoreVersion
    (fun _sample => (0 : Real)) hzero
    (Filter.Eventually.of_forall (fun _sample => rfl))

/--
The selected-law survey-weighted squared centered residual integral is
nonnegative when its conditional-variance version is nonnegative almost
everywhere.
-/
theorem selectedWeightedIntegral_centeredResidual_sq_nonneg_of_conditionalVariance_nonneg
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion conditionalVariance : Sample -> Real)
    (hvariance :
      populationLaw[centeredResidualSq outcome scoreVersion | scoreSigma] =ᵐ[
        populationLaw] conditionalVariance)
    (hvarianceNonneg : 0 ≤ᵐ[populationLaw] conditionalVariance) :
    0 ≤
      (∫ sample,
          (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
            design) sample * centeredResidualSq outcome scoreVersion sample
          ∂selectedLaw) := by
  rw [selectedWeightedIntegral_centeredResidual_sq_eq_populationIntegral_div
    (mSample := mSample) (selectedLaw := selectedLaw)
    (populationLaw := populationLaw) design outcome scoreVersion]
  exact div_nonneg
    (populationIntegral_centeredResidual_sq_nonneg_of_conditionalVariance_nonneg
      (mSample := mSample) (scoreSigma := scoreSigma)
      (populationLaw := populationLaw) hsub outcome scoreVersion
      conditionalVariance hvariance hvarianceNonneg)
    (le_of_lt
      (@PopulationSelectionDensityDesign.sampling_pos Sample mSample
        selectedLaw populationLaw design))

/--
The selected-law survey-weighted squared centered residual integral is zero
when its conditional-variance version is zero almost everywhere.
-/
theorem selectedWeightedIntegral_centeredResidual_sq_eq_zero_of_conditionalVariance_zero
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion conditionalVariance : Sample -> Real)
    (hvariance :
      populationLaw[centeredResidualSq outcome scoreVersion | scoreSigma] =ᵐ[
        populationLaw] conditionalVariance)
    (hvarianceZero : conditionalVariance =ᵐ[populationLaw] 0) :
    (∫ sample,
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) sample * centeredResidualSq outcome scoreVersion sample
        ∂selectedLaw) = 0 := by
  rw [selectedWeightedIntegral_centeredResidual_sq_eq_populationIntegral_div
    (mSample := mSample) (selectedLaw := selectedLaw)
    (populationLaw := populationLaw) design outcome scoreVersion]
  rw [populationIntegral_centeredResidual_sq_eq_zero_of_conditionalVariance_zero
    (mSample := mSample) (scoreSigma := scoreSigma)
    (populationLaw := populationLaw) hsub outcome scoreVersion
    conditionalVariance hvariance hvarianceZero]
  simp

/--
The selected-law survey-weighted squared centered residual integral is zero
when its score-sigma conditional second moment is zero almost everywhere.
-/
theorem selectedWeightedIntegral_centeredResidual_sq_eq_zero_of_condExp_centeredResidual_sq_zero
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (hzero :
      populationLaw[centeredResidualSq outcome scoreVersion | scoreSigma] =ᵐ[
        populationLaw] 0) :
    (∫ sample,
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) sample * centeredResidualSq outcome scoreVersion sample
        ∂selectedLaw) = 0 :=
  selectedWeightedIntegral_centeredResidual_sq_eq_zero_of_conditionalVariance_zero
    (mSample := mSample) (scoreSigma := scoreSigma)
    (selectedLaw := selectedLaw) (populationLaw := populationLaw)
    hsub design outcome scoreVersion (fun _sample => (0 : Real)) hzero
    (Filter.Eventually.of_forall (fun _sample => rfl))

/--
The selected-law survey-weighted Hájek mean of a squared centered residual
recovers the population squared residual integral.
-/
theorem selectedHajek_centeredResidual_sq_eq_populationIntegral
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1) :
    (∫ sample,
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) sample * centeredResidualSq outcome scoreVersion sample
        ∂selectedLaw) /
        (∫ sample,
          (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
            design) sample ∂selectedLaw) =
      ∫ sample, centeredResidualSq outcome scoreVersion sample
        ∂populationLaw := by
  simpa [designQuadraticWeightReal, centeredResidualSq] using
    (@PopulationSelectionDensityDesign.hajekRatio_eq_populationIntegral
      Sample mSample selectedLaw populationLaw design
      (centeredResidualSq outcome scoreVersion) hpopulationOne)

/--
The selected-law Hájek squared centered residual target is nonnegative.
-/
theorem selectedHajek_centeredResidual_sq_nonneg
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1) :
    0 ≤
      (∫ sample,
          (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
            design) sample * centeredResidualSq outcome scoreVersion sample
          ∂selectedLaw) /
          (∫ sample,
            (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
              design) sample ∂selectedLaw) := by
  rw [selectedHajek_centeredResidual_sq_eq_populationIntegral
    (mSample := mSample) (selectedLaw := selectedLaw)
    (populationLaw := populationLaw) design outcome scoreVersion
    hpopulationOne]
  exact populationIntegral_centeredResidual_sq_nonneg
    (mSample := mSample) (populationLaw := populationLaw) outcome scoreVersion

/--
The selected-law Hájek squared centered residual target is zero if the outcome
equals its score version almost everywhere under the population law.
-/
theorem selectedHajek_centeredResidual_sq_eq_zero_of_population_ae_eq_scoreVersion
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1)
    (houtcome : outcome =ᵐ[populationLaw] scoreVersion) :
    (∫ sample,
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) sample * centeredResidualSq outcome scoreVersion sample
        ∂selectedLaw) /
        (∫ sample,
          (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
            design) sample ∂selectedLaw) = 0 := by
  rw [selectedHajek_centeredResidual_sq_eq_populationIntegral
    (mSample := mSample) (selectedLaw := selectedLaw)
    (populationLaw := populationLaw) design outcome scoreVersion
    hpopulationOne]
  exact populationIntegral_centeredResidual_sq_eq_zero_of_ae_eq_scoreVersion
    (mSample := mSample) (populationLaw := populationLaw) outcome scoreVersion
    houtcome

/--
The selected-law Hájek squared centered residual target is zero if the outcome
equals its score version almost everywhere under the selected law.
-/
theorem selectedHajek_centeredResidual_sq_eq_zero_of_selected_ae_eq_scoreVersion
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (houtcome : outcome =ᵐ[selectedLaw] scoreVersion) :
    (∫ sample,
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) sample * centeredResidualSq outcome scoreVersion sample
        ∂selectedLaw) /
        (∫ sample,
          (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
            design) sample ∂selectedLaw) = 0 := by
  rw [selectedWeightedIntegral_centeredResidual_sq_eq_zero_of_selected_ae_eq_scoreVersion
    (mSample := mSample) (selectedLaw := selectedLaw)
    (populationLaw := populationLaw) design outcome scoreVersion houtcome]
  simp

/--
If `conditionalVariance` is the score-sigma conditional second moment of the
centered residual, then the selected-law survey-weighted Hájek squared
residual target equals the population conditional-variance integral.
-/
theorem selectedHajek_centeredResidual_sq_eq_conditionalVarianceIntegral
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion conditionalVariance : Sample -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1)
    (hvariance :
      populationLaw[centeredResidualSq outcome scoreVersion | scoreSigma] =ᵐ[
        populationLaw] conditionalVariance) :
    (∫ sample,
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) sample * centeredResidualSq outcome scoreVersion sample
        ∂selectedLaw) /
        (∫ sample,
          (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
            design) sample ∂selectedLaw) =
      ∫ sample, conditionalVariance sample ∂populationLaw := by
  rw [selectedHajek_centeredResidual_sq_eq_populationIntegral
    (mSample := mSample) (selectedLaw := selectedLaw)
    (populationLaw := populationLaw) design outcome scoreVersion
    hpopulationOne]
  exact
    integral_eq_scoreVersion_of_condExp_ae_eq
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := populationLaw) hsub
      (centeredResidualSq outcome scoreVersion) conditionalVariance hvariance

/--
If the design survey weight is score-sigma measurable and
`conditionalVariance` is the conditional second moment of a centered residual,
then the population design-weight quadratic variation rewrites to the
conditional-variance target.
-/
theorem integral_designWeight_sq_mul_centeredResidual_sq_eq_variance
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion conditionalVariance : Sample -> Real)
    (hweightMeas :
      AEStronglyMeasurable[scoreSigma]
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) populationLaw)
    (hproduct :
      Integrable
        (fun sample =>
          ((@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
            design) sample *
            (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
              design) sample) *
            centeredResidualSq outcome scoreVersion sample)
        populationLaw)
    (hresidualSq :
      Integrable (centeredResidualSq outcome scoreVersion) populationLaw)
    (hvariance :
      populationLaw[centeredResidualSq outcome scoreVersion | scoreSigma] =ᵐ[
        populationLaw] conditionalVariance) :
    ∫ sample,
        ((@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) sample *
          (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
            design) sample) *
          centeredResidualSq outcome scoreVersion sample ∂populationLaw =
      ∫ sample,
        ((@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) sample *
          (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
            design) sample) *
          conditionalVariance sample ∂populationLaw := by
  exact
    integral_scoreMeasurable_sq_mul_residual_sq_eq_variance
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := populationLaw) hsub
      (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
        design)
      (fun sample => outcome sample - scoreVersion sample)
      conditionalVariance hweightMeas
      (by simpa [centeredResidualSq, mul_assoc] using hproduct)
      (by simpa [centeredResidualSq] using hresidualSq)
      (by simpa [centeredResidualSq] using hvariance)

/--
Design-weight quadratic-variation rewrite with score-measurability stated at
the packaged NNReal survey-weight level.
-/
theorem integral_designWeight_sq_mul_centeredResidual_sq_eq_variance_of_scoreMeasurable_weight
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion conditionalVariance : Sample -> Real)
    (hweightScoreMeas :
      @Measurable Sample NNReal scoreSigma _
        (@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw design))
    (hproduct :
      Integrable
        (fun sample =>
          ((@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
            design) sample *
            (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
              design) sample) *
            centeredResidualSq outcome scoreVersion sample)
        populationLaw)
    (hresidualSq :
      Integrable (centeredResidualSq outcome scoreVersion) populationLaw)
    (hvariance :
      populationLaw[centeredResidualSq outcome scoreVersion | scoreSigma] =ᵐ[
        populationLaw] conditionalVariance) :
    ∫ sample,
        ((@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) sample *
          (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
            design) sample) *
          centeredResidualSq outcome scoreVersion sample ∂populationLaw =
      ∫ sample,
        ((@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) sample *
          (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
            design) sample) *
          conditionalVariance sample ∂populationLaw := by
  have hweightMeas :
      AEStronglyMeasurable[scoreSigma]
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) populationLaw := by
    simpa [designQuadraticWeightReal] using
      (NNReal.continuous_coe.measurable.comp
        hweightScoreMeas).aestronglyMeasurable
  exact
    integral_designWeight_sq_mul_centeredResidual_sq_eq_variance
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      hsub design outcome scoreVersion conditionalVariance hweightMeas
      hproduct hresidualSq hvariance

/--
The population design-weight quadratic variation is nonnegative.
-/
theorem integral_designWeight_sq_mul_centeredResidual_sq_nonneg
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real) :
    0 ≤ ∫ sample,
      ((@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
        design) sample *
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) sample) *
        centeredResidualSq outcome scoreVersion sample ∂populationLaw := by
  refine integral_nonneg_of_ae ?_
  filter_upwards [] with sample
  have hweight :
      0 ≤
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) sample := by
    exact
      ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
        selectedLaw populationLaw design) sample).2
  exact mul_nonneg (mul_nonneg hweight hweight)
    (by
      simpa [centeredResidualSq] using
        mul_self_nonneg (outcome sample - scoreVersion sample))

/--
The population design-weight quadratic variation is zero if the outcome equals
its score version almost everywhere under the population law.
-/
theorem integral_designWeight_sq_mul_centeredResidual_sq_eq_zero_of_population_ae_eq_scoreVersion
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (houtcome : outcome =ᵐ[populationLaw] scoreVersion) :
    ∫ sample,
      ((@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
        design) sample *
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) sample) *
        centeredResidualSq outcome scoreVersion sample ∂populationLaw = 0 := by
  refine integral_eq_zero_of_ae ?_
  filter_upwards [houtcome] with sample hsample
  simp [centeredResidualSq, hsample]

/--
Directly named design-weight quadratic-variation zero theorem from
population-law a.e. score-version equality.
-/
theorem integral_designWeight_sq_mul_centeredResidual_sq_eq_zero_of_direct_ae_scoreVersion
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (hae : outcome =ᵐ[populationLaw] scoreVersion) :
    ∫ sample,
      ((@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
        design) sample *
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) sample) *
        centeredResidualSq outcome scoreVersion sample ∂populationLaw = 0 :=
  integral_designWeight_sq_mul_centeredResidual_sq_eq_zero_of_population_ae_eq_scoreVersion
    (mSample := mSample) (selectedLaw := selectedLaw)
    (populationLaw := populationLaw) design outcome scoreVersion hae

/--
The selected-law Hájek squared residual target is nonnegative when its
conditional-variance version is nonnegative almost everywhere.
-/
theorem selectedHajek_centeredResidual_sq_nonneg_of_conditionalVariance_nonneg
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion conditionalVariance : Sample -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1)
    (hvariance :
      populationLaw[centeredResidualSq outcome scoreVersion | scoreSigma] =ᵐ[
        populationLaw] conditionalVariance)
    (hvarianceNonneg : 0 ≤ᵐ[populationLaw] conditionalVariance) :
    0 ≤
      (∫ sample,
          (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
            design) sample * centeredResidualSq outcome scoreVersion sample
          ∂selectedLaw) /
          (∫ sample,
            (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
              design) sample ∂selectedLaw) := by
  rw [selectedHajek_centeredResidual_sq_eq_conditionalVarianceIntegral
    (mSample := mSample) (scoreSigma := scoreSigma)
    (selectedLaw := selectedLaw) (populationLaw := populationLaw)
    hsub design outcome scoreVersion conditionalVariance hpopulationOne
    hvariance]
  exact integral_nonneg_of_ae hvarianceNonneg

/--
The selected-law Hájek squared residual target is zero when its
conditional-variance version is zero almost everywhere.
-/
theorem selectedHajek_centeredResidual_sq_eq_zero_of_conditionalVariance_zero
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion conditionalVariance : Sample -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1)
    (hvariance :
      populationLaw[centeredResidualSq outcome scoreVersion | scoreSigma] =ᵐ[
        populationLaw] conditionalVariance)
    (hvarianceZero : conditionalVariance =ᵐ[populationLaw] 0) :
    (∫ sample,
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) sample * centeredResidualSq outcome scoreVersion sample
        ∂selectedLaw) /
        (∫ sample,
          (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
            design) sample ∂selectedLaw) = 0 := by
  rw [selectedHajek_centeredResidual_sq_eq_conditionalVarianceIntegral
    (mSample := mSample) (scoreSigma := scoreSigma)
    (selectedLaw := selectedLaw) (populationLaw := populationLaw)
    hsub design outcome scoreVersion conditionalVariance hpopulationOne
    hvariance]
  exact integral_eq_zero_of_ae hvarianceZero

/--
The selected-law Hájek squared residual target is zero when its score-sigma
conditional second moment is zero almost everywhere.
-/
theorem selectedHajek_centeredResidual_sq_eq_zero_of_condExp_centeredResidual_sq_zero
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1)
    (hzero :
      populationLaw[centeredResidualSq outcome scoreVersion | scoreSigma] =ᵐ[
        populationLaw] 0) :
    (∫ sample,
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) sample * centeredResidualSq outcome scoreVersion sample
        ∂selectedLaw) /
        (∫ sample,
          (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
            design) sample ∂selectedLaw) = 0 :=
  selectedHajek_centeredResidual_sq_eq_zero_of_conditionalVariance_zero
    (mSample := mSample) (scoreSigma := scoreSigma)
    (selectedLaw := selectedLaw) (populationLaw := populationLaw)
    hsub design outcome scoreVersion (fun _sample => (0 : Real))
    hpopulationOne hzero
    (Filter.Eventually.of_forall (fun _sample => rfl))

/--
Directly named selected-law Hájek squared residual zero theorem from
population-law a.e. score-version equality.
-/
theorem selectedHajek_centeredResidual_sq_eq_zero_of_direct_ae_scoreVersion
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1)
    (hae : outcome =ᵐ[populationLaw] scoreVersion) :
    (∫ sample,
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) sample * centeredResidualSq outcome scoreVersion sample
        ∂selectedLaw) /
        (∫ sample,
          (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
            design) sample ∂selectedLaw) = 0 :=
  selectedHajek_centeredResidual_sq_eq_zero_of_population_ae_eq_scoreVersion
    (mSample := mSample) (selectedLaw := selectedLaw)
    (populationLaw := populationLaw) design outcome scoreVersion
    hpopulationOne hae

/--
The population design-weight quadratic variation is nonnegative when the
conditional-variance target is nonnegative almost everywhere.
-/
theorem integral_designWeight_sq_mul_centeredResidual_sq_nonneg_of_conditionalVariance_nonneg
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion conditionalVariance : Sample -> Real)
    (hweightMeas :
      AEStronglyMeasurable[scoreSigma]
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) populationLaw)
    (hproduct :
      Integrable
        (fun sample =>
          ((@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
            design) sample *
            (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
              design) sample) *
            centeredResidualSq outcome scoreVersion sample)
        populationLaw)
    (hresidualSq :
      Integrable (centeredResidualSq outcome scoreVersion) populationLaw)
    (hvariance :
      populationLaw[centeredResidualSq outcome scoreVersion | scoreSigma] =ᵐ[
        populationLaw] conditionalVariance)
    (hvarianceNonneg : 0 ≤ᵐ[populationLaw] conditionalVariance) :
    0 ≤ ∫ sample,
      ((@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
        design) sample *
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) sample) *
        centeredResidualSq outcome scoreVersion sample ∂populationLaw := by
  rw [integral_designWeight_sq_mul_centeredResidual_sq_eq_variance
    (mSample := mSample) (scoreSigma := scoreSigma)
    (selectedLaw := selectedLaw) (populationLaw := populationLaw)
    hsub design outcome scoreVersion conditionalVariance hweightMeas hproduct
    hresidualSq hvariance]
  exact
    integral_scoreMeasurable_sq_mul_conditionalVariance_nonneg
      (mSample := mSample) (sampleLaw := populationLaw)
      (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
        design)
      conditionalVariance hvarianceNonneg

/--
Nonnegativity of the design-weight quadratic variation with score-measurability
stated at the packaged NNReal survey-weight level.
-/
theorem integral_designWeight_sq_mul_centeredResidual_sq_nonneg_of_conditionalVariance_nonneg_of_scoreMeasurable_weight
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion conditionalVariance : Sample -> Real)
    (hweightScoreMeas :
      @Measurable Sample NNReal scoreSigma _
        (@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw design))
    (hproduct :
      Integrable
        (fun sample =>
          ((@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
            design) sample *
            (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
              design) sample) *
            centeredResidualSq outcome scoreVersion sample)
        populationLaw)
    (hresidualSq :
      Integrable (centeredResidualSq outcome scoreVersion) populationLaw)
    (hvariance :
      populationLaw[centeredResidualSq outcome scoreVersion | scoreSigma] =ᵐ[
        populationLaw] conditionalVariance)
    (hvarianceNonneg : 0 ≤ᵐ[populationLaw] conditionalVariance) :
    0 ≤ ∫ sample,
      ((@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
        design) sample *
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) sample) *
        centeredResidualSq outcome scoreVersion sample ∂populationLaw := by
  have hweightMeas :
      AEStronglyMeasurable[scoreSigma]
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) populationLaw := by
    simpa [designQuadraticWeightReal] using
      (NNReal.continuous_coe.measurable.comp
        hweightScoreMeas).aestronglyMeasurable
  exact
    integral_designWeight_sq_mul_centeredResidual_sq_nonneg_of_conditionalVariance_nonneg
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      hsub design outcome scoreVersion conditionalVariance hweightMeas
      hproduct hresidualSq hvariance hvarianceNonneg

/--
The population design-weight quadratic variation is zero when the
conditional-variance target is zero almost everywhere.
-/
theorem integral_designWeight_sq_mul_centeredResidual_sq_eq_zero_of_conditionalVariance_zero
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion conditionalVariance : Sample -> Real)
    (hweightMeas :
      AEStronglyMeasurable[scoreSigma]
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) populationLaw)
    (hproduct :
      Integrable
        (fun sample =>
          ((@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
            design) sample *
            (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
              design) sample) *
            centeredResidualSq outcome scoreVersion sample)
        populationLaw)
    (hresidualSq :
      Integrable (centeredResidualSq outcome scoreVersion) populationLaw)
    (hvariance :
      populationLaw[centeredResidualSq outcome scoreVersion | scoreSigma] =ᵐ[
        populationLaw] conditionalVariance)
    (hvarianceZero : conditionalVariance =ᵐ[populationLaw] 0) :
    ∫ sample,
      ((@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
        design) sample *
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) sample) *
        centeredResidualSq outcome scoreVersion sample ∂populationLaw = 0 := by
  rw [integral_designWeight_sq_mul_centeredResidual_sq_eq_variance
    (mSample := mSample) (scoreSigma := scoreSigma)
    (selectedLaw := selectedLaw) (populationLaw := populationLaw)
    hsub design outcome scoreVersion conditionalVariance hweightMeas hproduct
    hresidualSq hvariance]
  exact
    integral_scoreMeasurable_sq_mul_conditionalVariance_eq_zero_of_ae_eq_zero
      (mSample := mSample) (sampleLaw := populationLaw)
      (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
        design)
      conditionalVariance hvarianceZero

/--
The population design-weight quadratic variation is zero when the score-sigma
conditional second moment of the centered residual is zero almost everywhere.
-/
theorem integral_designWeight_sq_mul_centeredResidual_sq_eq_zero_of_condExp_centeredResidual_sq_zero
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (hweightMeas :
      AEStronglyMeasurable[scoreSigma]
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) populationLaw)
    (hproduct :
      Integrable
        (fun sample =>
          ((@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
            design) sample *
            (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
              design) sample) *
            centeredResidualSq outcome scoreVersion sample)
        populationLaw)
    (hresidualSq :
      Integrable (centeredResidualSq outcome scoreVersion) populationLaw)
    (hzero :
      populationLaw[centeredResidualSq outcome scoreVersion | scoreSigma] =ᵐ[
        populationLaw] 0) :
    ∫ sample,
      ((@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
        design) sample *
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) sample) *
        centeredResidualSq outcome scoreVersion sample ∂populationLaw = 0 :=
  integral_designWeight_sq_mul_centeredResidual_sq_eq_zero_of_conditionalVariance_zero
    (mSample := mSample) (scoreSigma := scoreSigma)
    (selectedLaw := selectedLaw) (populationLaw := populationLaw)
    hsub design outcome scoreVersion (fun _sample => (0 : Real))
    hweightMeas hproduct hresidualSq hzero
    (Filter.Eventually.of_forall (fun _sample => rfl))

/--
Zero design-weight quadratic variation from a zero conditional-variance target,
with score-measurability stated at the packaged NNReal survey-weight level.
-/
theorem integral_designWeight_sq_mul_centeredResidual_sq_eq_zero_of_conditionalVariance_zero_of_scoreMeasurable_weight
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion conditionalVariance : Sample -> Real)
    (hweightScoreMeas :
      @Measurable Sample NNReal scoreSigma _
        (@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw design))
    (hproduct :
      Integrable
        (fun sample =>
          ((@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
            design) sample *
            (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
              design) sample) *
            centeredResidualSq outcome scoreVersion sample)
        populationLaw)
    (hresidualSq :
      Integrable (centeredResidualSq outcome scoreVersion) populationLaw)
    (hvariance :
      populationLaw[centeredResidualSq outcome scoreVersion | scoreSigma] =ᵐ[
        populationLaw] conditionalVariance)
    (hvarianceZero : conditionalVariance =ᵐ[populationLaw] 0) :
    ∫ sample,
      ((@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
        design) sample *
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) sample) *
        centeredResidualSq outcome scoreVersion sample ∂populationLaw = 0 := by
  have hweightMeas :
      AEStronglyMeasurable[scoreSigma]
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) populationLaw := by
    simpa [designQuadraticWeightReal] using
      (NNReal.continuous_coe.measurable.comp
        hweightScoreMeas).aestronglyMeasurable
  exact
    integral_designWeight_sq_mul_centeredResidual_sq_eq_zero_of_conditionalVariance_zero
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      hsub design outcome scoreVersion conditionalVariance hweightMeas
      hproduct hresidualSq hvariance hvarianceZero

/--
Zero design-weight quadratic variation from a zero conditional second moment,
with score-measurability stated at the packaged NNReal survey-weight level.
-/
theorem integral_designWeight_sq_mul_centeredResidual_sq_eq_zero_of_condExp_centeredResidual_sq_zero_of_scoreMeasurable_weight
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (hweightScoreMeas :
      @Measurable Sample NNReal scoreSigma _
        (@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw design))
    (hproduct :
      Integrable
        (fun sample =>
          ((@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
            design) sample *
            (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
              design) sample) *
            centeredResidualSq outcome scoreVersion sample)
        populationLaw)
    (hresidualSq :
      Integrable (centeredResidualSq outcome scoreVersion) populationLaw)
    (hzero :
      populationLaw[centeredResidualSq outcome scoreVersion | scoreSigma] =ᵐ[
        populationLaw] 0) :
    ∫ sample,
      ((@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
        design) sample *
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) sample) *
        centeredResidualSq outcome scoreVersion sample ∂populationLaw = 0 := by
  have hweightMeas :
      AEStronglyMeasurable[scoreSigma]
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) populationLaw := by
    simpa [designQuadraticWeightReal] using
      (NNReal.continuous_coe.measurable.comp
        hweightScoreMeas).aestronglyMeasurable
  exact
    integral_designWeight_sq_mul_centeredResidual_sq_eq_zero_of_condExp_centeredResidual_sq_zero
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      hsub design outcome scoreVersion hweightMeas hproduct hresidualSq hzero

/--
The population design-weight quadratic variation is zero when the outcome
agrees a.e. with its score version under the population law, routed through
the conditional quadratic-variation bridge.
-/
theorem integral_designWeight_sq_mul_centeredResidual_sq_eq_zero_of_ae_scoreVersion
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (hweightMeas :
      AEStronglyMeasurable[scoreSigma]
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) populationLaw)
    (hproduct :
      Integrable
        (fun sample =>
          ((@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
            design) sample *
            (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
              design) sample) *
            centeredResidualSq outcome scoreVersion sample)
        populationLaw)
    (hresidualSq :
      Integrable (centeredResidualSq outcome scoreVersion) populationLaw)
    (houtcome : outcome =ᵐ[populationLaw] scoreVersion) :
    ∫ sample,
      ((@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
        design) sample *
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) sample) *
        centeredResidualSq outcome scoreVersion sample ∂populationLaw = 0 := by
  exact
    integral_scoreMeasurable_sq_mul_centeredResidual_sq_eq_zero_of_ae_scoreVersion
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := populationLaw) hsub
      (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
        design)
      outcome scoreVersion hweightMeas
      (by simpa [centeredResidualSq, mul_assoc] using hproduct)
      (by simpa [centeredResidualSq] using hresidualSq)
      houtcome

/--
Zero design-weight quadratic variation from a population-law a.e.
score-version equality, with score-measurability stated at the packaged NNReal
survey-weight level.
-/
theorem integral_designWeight_sq_mul_centeredResidual_sq_eq_zero_of_ae_scoreVersion_of_scoreMeasurable_weight
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (hweightScoreMeas :
      @Measurable Sample NNReal scoreSigma _
        (@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw design))
    (hproduct :
      Integrable
        (fun sample =>
          ((@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
            design) sample *
            (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
              design) sample) *
            centeredResidualSq outcome scoreVersion sample)
        populationLaw)
    (hresidualSq :
      Integrable (centeredResidualSq outcome scoreVersion) populationLaw)
    (houtcome : outcome =ᵐ[populationLaw] scoreVersion) :
    ∫ sample,
      ((@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
        design) sample *
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) sample) *
        centeredResidualSq outcome scoreVersion sample ∂populationLaw = 0 := by
  have hweightMeas :
      AEStronglyMeasurable[scoreSigma]
        (@designQuadraticWeightReal Sample mSample selectedLaw populationLaw
          design) populationLaw := by
    simpa [designQuadraticWeightReal] using
      (NNReal.continuous_coe.measurable.comp
        hweightScoreMeas).aestronglyMeasurable
  exact
    integral_designWeight_sq_mul_centeredResidual_sq_eq_zero_of_ae_scoreVersion
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      hsub design outcome scoreVersion hweightMeas hproduct hresidualSq
      houtcome

end WDSM
end Matching
end StatInference
