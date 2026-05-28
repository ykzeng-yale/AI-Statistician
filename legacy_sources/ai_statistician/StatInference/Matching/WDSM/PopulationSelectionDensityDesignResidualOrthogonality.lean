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
Raw-outcome-integrability variant of the population centered-residual
zero-integral theorem.  Score-version integrability is derived from the
conditional-mean equality.
-/
theorem integral_centeredResidual_eq_zero_of_condExp_scoreVersion_outcomeIntegrable
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (outcome scoreVersion : Sample -> Real)
    (houtcome : Integrable outcome populationLaw)
    (hcond :
      populationLaw[outcome | scoreSigma] =ᵐ[populationLaw] scoreVersion) :
    ∫ sample, (outcome sample - scoreVersion sample) ∂populationLaw = 0 := by
  exact integral_sub_scoreVersion_eq_zero_of_condExp_ae_eq_outcomeIntegrable
    (mSample := mSample) (scoreSigma := scoreSigma)
    (sampleLaw := populationLaw) hsub outcome scoreVersion houtcome hcond

/--
If an outcome agrees a.e. with a score-space version, then the centered
residual has population integral zero.
-/
theorem integral_centeredResidual_eq_zero_of_ae_scoreVersion
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (outcome scoreVersion : Sample -> Real)
    (houtcome : Integrable outcome populationLaw)
    (hscore : Integrable scoreVersion populationLaw)
    (hae : outcome =ᵐ[populationLaw] scoreVersion)
    (hscoreMeas :
      AEStronglyMeasurable[scoreSigma] scoreVersion populationLaw) :
    ∫ sample, (outcome sample - scoreVersion sample) ∂populationLaw = 0 := by
  exact
    integral_centeredResidual_eq_zero_of_condExp_scoreVersion
      (mSample := mSample) (scoreSigma := scoreSigma)
      (populationLaw := populationLaw) hsub outcome scoreVersion houtcome
      hscore
      (condExp_ae_eq_scoreVersion_of_ae_eq_aestronglyMeasurable
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := populationLaw) hsub outcome scoreVersion hae hscoreMeas
        hscore)

/--
Raw-outcome-integrability variant of the population a.e. score-version
residual-zero theorem.  Score-version integrability is transferred from the
a.e. equality.
-/
theorem integral_centeredResidual_eq_zero_of_ae_scoreVersion_outcomeIntegrable
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (outcome scoreVersion : Sample -> Real)
    (houtcome : Integrable outcome populationLaw)
    (hae : outcome =ᵐ[populationLaw] scoreVersion)
    (hscoreMeas :
      AEStronglyMeasurable[scoreSigma] scoreVersion populationLaw) :
    ∫ sample, (outcome sample - scoreVersion sample) ∂populationLaw = 0 := by
  exact
    integral_centeredResidual_eq_zero_of_ae_scoreVersion
      (mSample := mSample) (scoreSigma := scoreSigma)
      (populationLaw := populationLaw) hsub outcome scoreVersion houtcome
      (houtcome.congr hae) hae hscoreMeas

/--
If an outcome agrees a.e. with a score-space version, then the centered
residual has population integral zero directly, without needing to route
through an explicit conditional-mean representation.
-/
theorem integral_centeredResidual_eq_zero_of_direct_ae_scoreVersion
    (outcome scoreVersion : Sample -> Real)
    (hae : outcome =ᵐ[populationLaw] scoreVersion) :
    ∫ sample, (outcome sample - scoreVersion sample) ∂populationLaw = 0 := by
  refine integral_eq_zero_of_ae ?_
  filter_upwards [hae] with sample hsample
  simp [hsample]

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
Raw-outcome-integrability variant of the selected-law survey-weighted centered
residual zero theorem under a population selection-density design.
-/
theorem
    selectedWeightedIntegral_centeredResidual_eq_zero_of_selectionDensityDesign_outcomeIntegrable
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (houtcome : Integrable outcome populationLaw)
    (hcond :
      populationLaw[outcome | scoreSigma] =ᵐ[populationLaw] scoreVersion) :
    (∫ sample,
        (@designResidualWeightReal Sample mSample selectedLaw populationLaw
          design) sample * (outcome sample - scoreVersion sample)
        ∂selectedLaw) = 0 := by
  have hresidualZero :
      ∫ sample, (outcome sample - scoreVersion sample) ∂populationLaw = 0 :=
    integral_centeredResidual_eq_zero_of_condExp_scoreVersion_outcomeIntegrable
      (mSample := mSample) (scoreSigma := scoreSigma)
      (populationLaw := populationLaw) hsub outcome scoreVersion houtcome
      hcond
  have hrecovery :=
    @PopulationSelectionDensityDesign.surveyWeightedIntegral_eq_populationIntegral_div
      Sample mSample selectedLaw populationLaw design
      (fun sample => outcome sample - scoreVersion sample)
  simpa [designResidualWeightReal, hresidualZero] using hrecovery

/--
Under a population selection-density design, the selected-law survey-weighted
integral of a centered residual is zero when the outcome agrees a.e. with its
score-space version.
-/
theorem selectedWeightedIntegral_centeredResidual_eq_zero_of_selectionDensityDesign_ae_scoreVersion
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (houtcome : Integrable outcome populationLaw)
    (hscore : Integrable scoreVersion populationLaw)
    (hae : outcome =ᵐ[populationLaw] scoreVersion)
    (hscoreMeas :
      AEStronglyMeasurable[scoreSigma] scoreVersion populationLaw) :
    (∫ sample,
        (@designResidualWeightReal Sample mSample selectedLaw populationLaw
          design) sample * (outcome sample - scoreVersion sample)
        ∂selectedLaw) = 0 := by
  exact
    selectedWeightedIntegral_centeredResidual_eq_zero_of_selectionDensityDesign
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      hsub design outcome scoreVersion houtcome hscore
      (condExp_ae_eq_scoreVersion_of_ae_eq_aestronglyMeasurable
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := populationLaw) hsub outcome scoreVersion hae hscoreMeas
        hscore)

/--
Raw-outcome-integrability variant of the selected-law survey-weighted centered
residual zero theorem under population-law a.e. score-version equality.
-/
theorem
    selectedWeightedIntegral_centeredResidual_eq_zero_of_selectionDensityDesign_ae_scoreVersion_outcomeIntegrable
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (houtcome : Integrable outcome populationLaw)
    (hae : outcome =ᵐ[populationLaw] scoreVersion)
    (hscoreMeas :
      AEStronglyMeasurable[scoreSigma] scoreVersion populationLaw) :
    (∫ sample,
        (@designResidualWeightReal Sample mSample selectedLaw populationLaw
          design) sample * (outcome sample - scoreVersion sample)
        ∂selectedLaw) = 0 := by
  exact
    selectedWeightedIntegral_centeredResidual_eq_zero_of_selectionDensityDesign_ae_scoreVersion
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      hsub design outcome scoreVersion houtcome (houtcome.congr hae) hae
      hscoreMeas

/--
Under a population selection-density design, the selected-law survey-weighted
integral of a centered residual is zero when the outcome agrees a.e. with its
score-space version under the population law, without additional score-version
measurability or integrability hypotheses.
-/
theorem selectedWeightedIntegral_centeredResidual_eq_zero_of_direct_population_ae_scoreVersion
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (hae : outcome =ᵐ[populationLaw] scoreVersion) :
    (∫ sample,
        (@designResidualWeightReal Sample mSample selectedLaw populationLaw
          design) sample * (outcome sample - scoreVersion sample)
        ∂selectedLaw) = 0 := by
  refine integral_eq_zero_of_ae ?_
  filter_upwards
    [PopulationSelectionDensityDesign.selectedLaw_ae_eq_of_populationLaw_ae_eq
      design hae] with sample hsample
  simp [hsample]

/--
If an outcome agrees a.e. with its score-space version under the selected law,
then the selected-law survey-weighted centered-residual integral is zero.
-/
theorem selectedWeightedIntegral_centeredResidual_eq_zero_of_selected_ae_scoreVersion
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (hae : outcome =ᵐ[selectedLaw] scoreVersion) :
    (∫ sample,
        (@designResidualWeightReal Sample mSample selectedLaw populationLaw
          design) sample * (outcome sample - scoreVersion sample)
        ∂selectedLaw) = 0 := by
  refine integral_eq_zero_of_ae ?_
  filter_upwards [hae] with sample hsample
  simp [hsample]

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
Raw-outcome-integrability variant of the selected-law Hájek centered-residual
zero theorem under a population selection-density design.
-/
theorem selectedHajek_centeredResidual_eq_zero_of_selectionDensityDesign_outcomeIntegrable
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1)
    (houtcome : Integrable outcome populationLaw)
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
    integral_centeredResidual_eq_zero_of_condExp_scoreVersion_outcomeIntegrable
      (mSample := mSample) (scoreSigma := scoreSigma)
      (populationLaw := populationLaw) hsub outcome scoreVersion houtcome
      hcond
  have hratio :=
    @PopulationSelectionDensityDesign.hajekRatio_eq_populationIntegral
      Sample mSample selectedLaw populationLaw design
      (fun sample => outcome sample - scoreVersion sample) hpopulationOne
  simpa [designResidualWeightReal, hresidualZero] using hratio

/--
Under a population selection-density design, the selected-law survey-weighted
Hájek mean of a centered residual is zero when the outcome agrees a.e. with
its score-space version.
-/
theorem selectedHajek_centeredResidual_eq_zero_of_selectionDensityDesign_ae_scoreVersion
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1)
    (houtcome : Integrable outcome populationLaw)
    (hscore : Integrable scoreVersion populationLaw)
    (hae : outcome =ᵐ[populationLaw] scoreVersion)
    (hscoreMeas :
      AEStronglyMeasurable[scoreSigma] scoreVersion populationLaw) :
    (∫ sample,
        (@designResidualWeightReal Sample mSample selectedLaw populationLaw
          design) sample * (outcome sample - scoreVersion sample)
        ∂selectedLaw) /
        (∫ sample,
          (@designResidualWeightReal Sample mSample selectedLaw populationLaw
            design) sample ∂selectedLaw) = 0 := by
  exact
    selectedHajek_centeredResidual_eq_zero_of_selectionDensityDesign
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      hsub design outcome scoreVersion hpopulationOne houtcome hscore
      (condExp_ae_eq_scoreVersion_of_ae_eq_aestronglyMeasurable
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := populationLaw) hsub outcome scoreVersion hae hscoreMeas
        hscore)

/--
Raw-outcome-integrability variant of the selected-law Hájek centered-residual
zero theorem under population-law a.e. score-version equality.
-/
theorem
    selectedHajek_centeredResidual_eq_zero_of_selectionDensityDesign_ae_scoreVersion_outcomeIntegrable
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1)
    (houtcome : Integrable outcome populationLaw)
    (hae : outcome =ᵐ[populationLaw] scoreVersion)
    (hscoreMeas :
      AEStronglyMeasurable[scoreSigma] scoreVersion populationLaw) :
    (∫ sample,
        (@designResidualWeightReal Sample mSample selectedLaw populationLaw
          design) sample * (outcome sample - scoreVersion sample)
        ∂selectedLaw) /
        (∫ sample,
          (@designResidualWeightReal Sample mSample selectedLaw populationLaw
            design) sample ∂selectedLaw) = 0 := by
  exact
    selectedHajek_centeredResidual_eq_zero_of_selectionDensityDesign_ae_scoreVersion
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      hsub design outcome scoreVersion hpopulationOne houtcome
      (houtcome.congr hae) hae hscoreMeas

/--
Under a population selection-density design, the selected-law survey-weighted
Hájek mean of a centered residual is zero when the outcome agrees a.e. with
its score-space version under the population law, without additional
score-version measurability or integrability hypotheses.
-/
theorem selectedHajek_centeredResidual_eq_zero_of_direct_population_ae_scoreVersion
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (_hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1)
    (hae : outcome =ᵐ[populationLaw] scoreVersion) :
    (∫ sample,
        (@designResidualWeightReal Sample mSample selectedLaw populationLaw
          design) sample * (outcome sample - scoreVersion sample)
        ∂selectedLaw) /
        (∫ sample,
          (@designResidualWeightReal Sample mSample selectedLaw populationLaw
            design) sample ∂selectedLaw) = 0 := by
  rw [selectedWeightedIntegral_centeredResidual_eq_zero_of_selected_ae_scoreVersion
    (mSample := mSample) (selectedLaw := selectedLaw)
    (populationLaw := populationLaw) design outcome scoreVersion
    (PopulationSelectionDensityDesign.selectedLaw_ae_eq_of_populationLaw_ae_eq
      design hae)]
  simp

/--
If an outcome agrees a.e. with its score-space version under the selected law,
then the selected-law Hájek centered-residual target is zero.
-/
theorem selectedHajek_centeredResidual_eq_zero_of_selected_ae_scoreVersion
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (hae : outcome =ᵐ[selectedLaw] scoreVersion) :
    (∫ sample,
        (@designResidualWeightReal Sample mSample selectedLaw populationLaw
          design) sample * (outcome sample - scoreVersion sample)
        ∂selectedLaw) /
        (∫ sample,
          (@designResidualWeightReal Sample mSample selectedLaw populationLaw
            design) sample ∂selectedLaw) = 0 := by
  rw [selectedWeightedIntegral_centeredResidual_eq_zero_of_selected_ae_scoreVersion
    (mSample := mSample) (selectedLaw := selectedLaw)
    (populationLaw := populationLaw) design outcome scoreVersion hae]
  simp

/--
Population-law a.e. score-version equality is enough for the selected-law
Hájek centered-residual target to vanish; no population-mass normalization is
needed once selected-law absolute continuity is used.
-/
theorem selectedHajek_centeredResidual_eq_zero_of_population_ae_scoreVersion
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (hae : outcome =ᵐ[populationLaw] scoreVersion) :
    (∫ sample,
        (@designResidualWeightReal Sample mSample selectedLaw populationLaw
          design) sample * (outcome sample - scoreVersion sample)
        ∂selectedLaw) /
        (∫ sample,
          (@designResidualWeightReal Sample mSample selectedLaw populationLaw
            design) sample ∂selectedLaw) = 0 :=
  selectedHajek_centeredResidual_eq_zero_of_selected_ae_scoreVersion
    (mSample := mSample) (selectedLaw := selectedLaw)
    (populationLaw := populationLaw) design outcome scoreVersion
    (PopulationSelectionDensityDesign.selectedLaw_ae_eq_of_populationLaw_ae_eq
      design hae)

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

/--
Raw-outcome-integrability variant of score-measurable design-weight
orthogonality under a conditional score-version mean.
-/
theorem integral_scoreMeasurable_designWeight_mul_centeredResidual_eq_zero_outcomeIntegrable
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
  have hscore : Integrable scoreVersion populationLaw :=
    integrable_condExp.congr hcond
  exact
    integral_scoreMeasurable_designWeight_mul_centeredResidual_eq_zero
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      hsub design outcome scoreVersion hweightMeas houtcome hscore
      hscoreMeas hproduct hcond

/--
If the design survey weight is score-sigma measurable and the outcome agrees
a.e. with its score-space version, then the design-weighted centered residual
is population-orthogonal.
-/
theorem integral_scoreMeasurable_designWeight_mul_centeredResidual_eq_zero_of_ae_scoreVersion
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
    (hae : outcome =ᵐ[populationLaw] scoreVersion) :
    ∫ sample,
      (@designResidualWeightReal Sample mSample selectedLaw populationLaw
        design) sample * (outcome sample - scoreVersion sample)
      ∂populationLaw = 0 := by
  exact
    integral_scoreMeasurable_designWeight_mul_centeredResidual_eq_zero
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      hsub design outcome scoreVersion hweightMeas houtcome hscore
      hscoreMeas hproduct
      (condExp_ae_eq_scoreVersion_of_ae_eq_aestronglyMeasurable
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := populationLaw) hsub outcome scoreVersion hae hscoreMeas
        hscore)

/--
Raw-outcome-integrability variant of score-measurable design-weight
orthogonality under population-law a.e. score-version equality.
-/
theorem
    integral_scoreMeasurable_designWeight_mul_centeredResidual_eq_zero_of_ae_scoreVersion_outcomeIntegrable
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
    (hscoreMeas :
      AEStronglyMeasurable[scoreSigma] scoreVersion populationLaw)
    (hproduct :
      Integrable
        (fun sample =>
          (@designResidualWeightReal Sample mSample selectedLaw populationLaw
            design) sample * (outcome sample - scoreVersion sample))
        populationLaw)
    (hae : outcome =ᵐ[populationLaw] scoreVersion) :
    ∫ sample,
      (@designResidualWeightReal Sample mSample selectedLaw populationLaw
        design) sample * (outcome sample - scoreVersion sample)
      ∂populationLaw = 0 := by
  exact
    integral_scoreMeasurable_designWeight_mul_centeredResidual_eq_zero_of_ae_scoreVersion
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      hsub design outcome scoreVersion hweightMeas houtcome
      (houtcome.congr hae) hscoreMeas hproduct hae

/--
If the design survey weight is score-sigma measurable and the outcome agrees
a.e. with its score-space version, then the design-weighted centered residual
is population-orthogonal directly from the a.e. residual-zero fact.
-/
theorem integral_scoreMeasurable_designWeight_mul_centeredResidual_eq_zero_of_direct_ae_scoreVersion
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (hweightMeas :
      AEStronglyMeasurable[scoreSigma]
        (@designResidualWeightReal Sample mSample selectedLaw populationLaw
          design) populationLaw)
    (hproduct :
      Integrable
        (fun sample =>
          (@designResidualWeightReal Sample mSample selectedLaw populationLaw
            design) sample * (outcome sample - scoreVersion sample))
        populationLaw)
    (hresidual :
      Integrable (fun sample => outcome sample - scoreVersion sample)
        populationLaw)
    (hae : outcome =ᵐ[populationLaw] scoreVersion) :
    ∫ sample,
      (@designResidualWeightReal Sample mSample selectedLaw populationLaw
        design) sample * (outcome sample - scoreVersion sample)
      ∂populationLaw = 0 := by
  exact
    integral_scoreMeasurable_mul_centeredResidual_eq_zero_of_ae_scoreVersion
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := populationLaw) hsub
      (@designResidualWeightReal Sample mSample selectedLaw populationLaw
        design)
      outcome scoreVersion hweightMeas hproduct hresidual hae

/--
Raw-outcome-integrability variant of the direct a.e. residual-zero population
orthogonality theorem.
-/
theorem
    integral_scoreMeasurable_designWeight_mul_centeredResidual_eq_zero_of_direct_ae_scoreVersion_outcomeIntegrable
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
    (hproduct :
      Integrable
        (fun sample =>
          (@designResidualWeightReal Sample mSample selectedLaw populationLaw
            design) sample * (outcome sample - scoreVersion sample))
        populationLaw)
    (hae : outcome =ᵐ[populationLaw] scoreVersion) :
    ∫ sample,
      (@designResidualWeightReal Sample mSample selectedLaw populationLaw
        design) sample * (outcome sample - scoreVersion sample)
      ∂populationLaw = 0 := by
  exact
    integral_scoreMeasurable_designWeight_mul_centeredResidual_eq_zero_of_direct_ae_scoreVersion
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      hsub design outcome scoreVersion hweightMeas hproduct
      (houtcome.sub (houtcome.congr hae)) hae

/--
Design-weighted residual orthogonality with score-measurability stated at the
packaged NNReal survey-weight level.
-/
theorem integral_scoreMeasurable_designWeight_mul_centeredResidual_eq_zero_of_scoreMeasurable_weight
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (hweightScoreMeas :
      @Measurable Sample NNReal scoreSigma _
        (@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw design))
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
  have hweightMeas :
      AEStronglyMeasurable[scoreSigma]
        (@designResidualWeightReal Sample mSample selectedLaw populationLaw
          design) populationLaw := by
    simpa [designResidualWeightReal] using
      (NNReal.continuous_coe.measurable.comp
        hweightScoreMeas).aestronglyMeasurable
  exact
    integral_scoreMeasurable_designWeight_mul_centeredResidual_eq_zero
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      hsub design outcome scoreVersion hweightMeas houtcome hscore
      hscoreMeas hproduct hcond

/--
Raw-outcome-integrability residual orthogonality with score-measurability
stated at the packaged NNReal survey-weight level.
-/
theorem integral_scoreMeasurable_designWeight_mul_centeredResidual_eq_zero_outcomeIntegrable_of_scoreMeasurable_weight
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (hweightScoreMeas :
      @Measurable Sample NNReal scoreSigma _
        (@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw design))
    (houtcome : Integrable outcome populationLaw)
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
  have hweightMeas :
      AEStronglyMeasurable[scoreSigma]
        (@designResidualWeightReal Sample mSample selectedLaw populationLaw
          design) populationLaw := by
    simpa [designResidualWeightReal] using
      (NNReal.continuous_coe.measurable.comp
        hweightScoreMeas).aestronglyMeasurable
  exact
    integral_scoreMeasurable_designWeight_mul_centeredResidual_eq_zero_outcomeIntegrable
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      hsub design outcome scoreVersion hweightMeas houtcome hscoreMeas
      hproduct hcond

/--
A.e. score-version residual orthogonality with score-measurability stated at
the packaged NNReal survey-weight level.
-/
theorem integral_scoreMeasurable_designWeight_mul_centeredResidual_eq_zero_of_ae_scoreVersion_of_scoreMeasurable_weight
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (hweightScoreMeas :
      @Measurable Sample NNReal scoreSigma _
        (@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw design))
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
    (hae : outcome =ᵐ[populationLaw] scoreVersion) :
    ∫ sample,
      (@designResidualWeightReal Sample mSample selectedLaw populationLaw
        design) sample * (outcome sample - scoreVersion sample)
      ∂populationLaw = 0 := by
  have hweightMeas :
      AEStronglyMeasurable[scoreSigma]
        (@designResidualWeightReal Sample mSample selectedLaw populationLaw
          design) populationLaw := by
    simpa [designResidualWeightReal] using
      (NNReal.continuous_coe.measurable.comp
        hweightScoreMeas).aestronglyMeasurable
  exact
    integral_scoreMeasurable_designWeight_mul_centeredResidual_eq_zero_of_ae_scoreVersion
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      hsub design outcome scoreVersion hweightMeas houtcome hscore
      hscoreMeas hproduct hae

/--
Raw-outcome-integrability a.e. score-version residual orthogonality with
score-measurability stated at the packaged NNReal survey-weight level.
-/
theorem
    integral_scoreMeasurable_designWeight_mul_centeredResidual_eq_zero_of_ae_scoreVersion_outcomeIntegrable_of_scoreMeasurable_weight
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (hweightScoreMeas :
      @Measurable Sample NNReal scoreSigma _
        (@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw design))
    (houtcome : Integrable outcome populationLaw)
    (hscoreMeas :
      AEStronglyMeasurable[scoreSigma] scoreVersion populationLaw)
    (hproduct :
      Integrable
        (fun sample =>
          (@designResidualWeightReal Sample mSample selectedLaw populationLaw
            design) sample * (outcome sample - scoreVersion sample))
        populationLaw)
    (hae : outcome =ᵐ[populationLaw] scoreVersion) :
    ∫ sample,
      (@designResidualWeightReal Sample mSample selectedLaw populationLaw
        design) sample * (outcome sample - scoreVersion sample)
      ∂populationLaw = 0 := by
  have hweightMeas :
      AEStronglyMeasurable[scoreSigma]
        (@designResidualWeightReal Sample mSample selectedLaw populationLaw
          design) populationLaw := by
    simpa [designResidualWeightReal] using
      (NNReal.continuous_coe.measurable.comp
        hweightScoreMeas).aestronglyMeasurable
  exact
    integral_scoreMeasurable_designWeight_mul_centeredResidual_eq_zero_of_ae_scoreVersion_outcomeIntegrable
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      hsub design outcome scoreVersion hweightMeas houtcome hscoreMeas
      hproduct hae

/--
Direct a.e. score-version residual orthogonality with score-measurability
stated at the packaged NNReal survey-weight level.
-/
theorem integral_scoreMeasurable_designWeight_mul_centeredResidual_eq_zero_of_direct_ae_scoreVersion_of_scoreMeasurable_weight
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
          (@designResidualWeightReal Sample mSample selectedLaw populationLaw
            design) sample * (outcome sample - scoreVersion sample))
        populationLaw)
    (hresidual :
      Integrable (fun sample => outcome sample - scoreVersion sample)
        populationLaw)
    (hae : outcome =ᵐ[populationLaw] scoreVersion) :
    ∫ sample,
      (@designResidualWeightReal Sample mSample selectedLaw populationLaw
        design) sample * (outcome sample - scoreVersion sample)
      ∂populationLaw = 0 := by
  have hweightMeas :
      AEStronglyMeasurable[scoreSigma]
        (@designResidualWeightReal Sample mSample selectedLaw populationLaw
          design) populationLaw := by
    simpa [designResidualWeightReal] using
      (NNReal.continuous_coe.measurable.comp
        hweightScoreMeas).aestronglyMeasurable
  exact
    integral_scoreMeasurable_designWeight_mul_centeredResidual_eq_zero_of_direct_ae_scoreVersion
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      hsub design outcome scoreVersion hweightMeas hproduct hresidual hae

/--
Raw-outcome-integrability direct a.e. score-version residual orthogonality
with score-measurability stated at the packaged NNReal survey-weight level.
-/
theorem
    integral_scoreMeasurable_designWeight_mul_centeredResidual_eq_zero_of_direct_ae_scoreVersion_outcomeIntegrable_of_scoreMeasurable_weight
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (outcome scoreVersion : Sample -> Real)
    (hweightScoreMeas :
      @Measurable Sample NNReal scoreSigma _
        (@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw design))
    (houtcome : Integrable outcome populationLaw)
    (hproduct :
      Integrable
        (fun sample =>
          (@designResidualWeightReal Sample mSample selectedLaw populationLaw
            design) sample * (outcome sample - scoreVersion sample))
        populationLaw)
    (hae : outcome =ᵐ[populationLaw] scoreVersion) :
    ∫ sample,
      (@designResidualWeightReal Sample mSample selectedLaw populationLaw
        design) sample * (outcome sample - scoreVersion sample)
      ∂populationLaw = 0 := by
  have hweightMeas :
      AEStronglyMeasurable[scoreSigma]
        (@designResidualWeightReal Sample mSample selectedLaw populationLaw
          design) populationLaw := by
    simpa [designResidualWeightReal] using
      (NNReal.continuous_coe.measurable.comp
        hweightScoreMeas).aestronglyMeasurable
  exact
    integral_scoreMeasurable_designWeight_mul_centeredResidual_eq_zero_of_direct_ae_scoreVersion_outcomeIntegrable
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      hsub design outcome scoreVersion hweightMeas houtcome hproduct hae

end WDSM
end Matching
end StatInference
