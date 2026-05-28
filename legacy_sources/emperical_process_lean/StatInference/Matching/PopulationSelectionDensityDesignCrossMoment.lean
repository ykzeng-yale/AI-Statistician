import StatInference.Matching.WDSM.PopulationSelectionDensityDesign
import StatInference.Matching.WDSM.ConditionalMeanIntegralBridge
import StatInference.Matching.WDSM.ConditionalCrossMomentBridge

/-!
# Population selection-density design cross moments

This module is the off-diagonal companion to the selection-density design
quadratic-variation layer.  It proves exact selected-law survey-weighted
residual-product recovery and population conditional cross-moment rewrites for
score-measurable design weights.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open scoped MeasureTheory ENNReal

variable {Sample : Type*} [mSample : MeasurableSpace Sample]
variable {scoreSigma : MeasurableSpace Sample}
variable {selectedLaw populationLaw : Measure[mSample] Sample}

private def designCrossWeightReal
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw) :
    Sample -> Real :=
  fun sample =>
    ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample selectedLaw
      populationLaw design) sample : Real)

private def residualProduct
    (leftResidual rightResidual : Sample -> Real) : Sample -> Real :=
  fun sample => leftResidual sample * rightResidual sample

/--
Under a population selection-density design, the selected-law survey-weighted
integral of a residual product recovers the population residual-product
integral divided by the sampling mass.
-/
theorem selectedWeightedIntegral_residualProduct_eq_populationIntegral_div
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (leftResidual rightResidual : Sample -> Real) :
    (∫ sample,
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          design) sample * residualProduct leftResidual rightResidual sample
        ∂selectedLaw) =
      (∫ sample, residualProduct leftResidual rightResidual sample
        ∂populationLaw) /
        @PopulationSelectionDensityDesign.samplingMass Sample mSample
          selectedLaw populationLaw design := by
  simpa [designCrossWeightReal, residualProduct] using
    (@PopulationSelectionDensityDesign.surveyWeightedIntegral_eq_populationIntegral_div
      Sample mSample selectedLaw populationLaw design
      (residualProduct leftResidual rightResidual))

/--
If the score-sigma conditional residual cross moment is zero, then the raw
population residual-product integral is zero.
-/
theorem populationIntegral_residualProduct_eq_zero_of_conditionalCross_zero
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (leftResidual rightResidual : Sample -> Real)
    (hcrossZero :
      populationLaw[residualProduct leftResidual rightResidual | scoreSigma]
        =ᵐ[populationLaw] 0) :
    (∫ sample, residualProduct leftResidual rightResidual sample
      ∂populationLaw) = 0 := by
  have h :=
    integral_eq_scoreVersion_of_condExp_ae_eq
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := populationLaw) hsub
      (residualProduct leftResidual rightResidual) (fun _sample => (0 : Real))
      hcrossZero
  simpa using h

/--
If the score-sigma conditional residual cross moment is zero, then the
selected-law survey-weighted residual-product integral is zero.
-/
theorem selectedWeightedIntegral_residualProduct_eq_zero_of_conditionalCross_zero
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (leftResidual rightResidual : Sample -> Real)
    (hcrossZero :
      populationLaw[residualProduct leftResidual rightResidual | scoreSigma]
        =ᵐ[populationLaw] 0) :
    (∫ sample,
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          design) sample * residualProduct leftResidual rightResidual sample
        ∂selectedLaw) = 0 := by
  rw [selectedWeightedIntegral_residualProduct_eq_populationIntegral_div
    (mSample := mSample) (selectedLaw := selectedLaw)
    (populationLaw := populationLaw) design leftResidual rightResidual]
  rw [populationIntegral_residualProduct_eq_zero_of_conditionalCross_zero
    (mSample := mSample) (scoreSigma := scoreSigma)
    (populationLaw := populationLaw) hsub leftResidual rightResidual
    hcrossZero]
  simp

/--
The selected-law survey-weighted Hájek residual-product mean recovers the
population residual-product integral.
-/
theorem selectedHajek_residualProduct_eq_populationIntegral
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (leftResidual rightResidual : Sample -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1) :
    (∫ sample,
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          design) sample * residualProduct leftResidual rightResidual sample
        ∂selectedLaw) /
        (∫ sample,
          (@designCrossWeightReal Sample mSample selectedLaw populationLaw
            design) sample ∂selectedLaw) =
      ∫ sample, residualProduct leftResidual rightResidual sample
        ∂populationLaw := by
  simpa [designCrossWeightReal, residualProduct] using
    (@PopulationSelectionDensityDesign.hajekRatio_eq_populationIntegral
      Sample mSample selectedLaw populationLaw design
      (residualProduct leftResidual rightResidual) hpopulationOne)

/--
If `conditionalCross` is the score-sigma conditional residual cross moment,
then the selected-law survey-weighted Hájek residual-product target equals the
population conditional-cross integral.
-/
theorem selectedHajek_residualProduct_eq_conditionalCrossIntegral
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (leftResidual rightResidual conditionalCross : Sample -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1)
    (hcross :
      populationLaw[residualProduct leftResidual rightResidual | scoreSigma] =ᵐ[
        populationLaw] conditionalCross) :
    (∫ sample,
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          design) sample * residualProduct leftResidual rightResidual sample
        ∂selectedLaw) /
        (∫ sample,
          (@designCrossWeightReal Sample mSample selectedLaw populationLaw
            design) sample ∂selectedLaw) =
      ∫ sample, conditionalCross sample ∂populationLaw := by
  rw [selectedHajek_residualProduct_eq_populationIntegral
    (mSample := mSample) (selectedLaw := selectedLaw)
    (populationLaw := populationLaw) design leftResidual rightResidual
    hpopulationOne]
  exact
    integral_eq_scoreVersion_of_condExp_ae_eq
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := populationLaw) hsub
      (residualProduct leftResidual rightResidual) conditionalCross hcross

/--
If `conditionalCross` represents the score-sigma conditional residual cross
moment and that target is nonnegative a.e., then the raw population
residual-product integral is nonnegative.
-/
theorem populationIntegral_residualProduct_nonneg_of_conditionalCross_nonneg
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (leftResidual rightResidual conditionalCross : Sample -> Real)
    (hcross :
      populationLaw[residualProduct leftResidual rightResidual | scoreSigma] =ᵐ[
        populationLaw] conditionalCross)
    (hcrossNonneg : 0 ≤ᵐ[populationLaw] conditionalCross) :
    0 ≤ ∫ sample, residualProduct leftResidual rightResidual sample
      ∂populationLaw := by
  rw [integral_eq_scoreVersion_of_condExp_ae_eq
    (mSample := mSample) (scoreSigma := scoreSigma)
    (sampleLaw := populationLaw) hsub
    (residualProduct leftResidual rightResidual) conditionalCross hcross]
  exact integral_nonneg_of_ae hcrossNonneg

/--
If `conditionalCross` represents the score-sigma conditional residual cross
moment and that target is nonnegative a.e., then the selected-law
survey-weighted residual-product integral is nonnegative.
-/
theorem selectedWeightedIntegral_residualProduct_nonneg_of_conditionalCross_nonneg
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (leftResidual rightResidual conditionalCross : Sample -> Real)
    (hcross :
      populationLaw[residualProduct leftResidual rightResidual | scoreSigma] =ᵐ[
        populationLaw] conditionalCross)
    (hcrossNonneg : 0 ≤ᵐ[populationLaw] conditionalCross) :
    0 ≤
      ∫ sample,
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          design) sample * residualProduct leftResidual rightResidual sample
        ∂selectedLaw := by
  rw [selectedWeightedIntegral_residualProduct_eq_populationIntegral_div
    (mSample := mSample) (selectedLaw := selectedLaw)
    (populationLaw := populationLaw) design leftResidual rightResidual]
  exact div_nonneg
    (populationIntegral_residualProduct_nonneg_of_conditionalCross_nonneg
      (mSample := mSample) (scoreSigma := scoreSigma)
      (populationLaw := populationLaw) hsub leftResidual rightResidual
      conditionalCross hcross hcrossNonneg)
    (le_of_lt
      (@PopulationSelectionDensityDesign.sampling_pos Sample mSample
        selectedLaw populationLaw design))

/--
If `conditionalCross` represents the score-sigma conditional residual cross
moment and that target is nonnegative a.e., then the selected-law Hájek
residual-product target is nonnegative.
-/
theorem selectedHajek_residualProduct_nonneg_of_conditionalCross_nonneg
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (leftResidual rightResidual conditionalCross : Sample -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1)
    (hcross :
      populationLaw[residualProduct leftResidual rightResidual | scoreSigma] =ᵐ[
        populationLaw] conditionalCross)
    (hcrossNonneg : 0 ≤ᵐ[populationLaw] conditionalCross) :
    0 ≤
      (∫ sample,
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          design) sample * residualProduct leftResidual rightResidual sample
        ∂selectedLaw) /
        (∫ sample,
          (@designCrossWeightReal Sample mSample selectedLaw populationLaw
            design) sample ∂selectedLaw) := by
  rw [selectedHajek_residualProduct_eq_conditionalCrossIntegral
    (mSample := mSample) (scoreSigma := scoreSigma)
    (selectedLaw := selectedLaw) (populationLaw := populationLaw)
    hsub design leftResidual rightResidual conditionalCross hpopulationOne
    hcross]
  exact integral_nonneg_of_ae hcrossNonneg

/--
If `conditionalCross` represents the score-sigma conditional residual cross
moment and that target is zero a.e., then the raw population residual-product
integral is zero.
-/
theorem populationIntegral_residualProduct_eq_zero_of_conditionalCross_ae_zero
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (leftResidual rightResidual conditionalCross : Sample -> Real)
    (hcross :
      populationLaw[residualProduct leftResidual rightResidual | scoreSigma] =ᵐ[
        populationLaw] conditionalCross)
    (hcrossZero : conditionalCross =ᵐ[populationLaw] 0) :
    (∫ sample, residualProduct leftResidual rightResidual sample
      ∂populationLaw) = 0 := by
  rw [integral_eq_scoreVersion_of_condExp_ae_eq
    (mSample := mSample) (scoreSigma := scoreSigma)
    (sampleLaw := populationLaw) hsub
    (residualProduct leftResidual rightResidual) conditionalCross hcross]
  exact integral_eq_zero_of_ae hcrossZero

/--
If `conditionalCross` represents the score-sigma conditional residual cross
moment and that target is zero a.e., then the selected-law survey-weighted
residual-product integral is zero.
-/
theorem selectedWeightedIntegral_residualProduct_eq_zero_of_conditionalCross_ae_zero
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (leftResidual rightResidual conditionalCross : Sample -> Real)
    (hcross :
      populationLaw[residualProduct leftResidual rightResidual | scoreSigma] =ᵐ[
        populationLaw] conditionalCross)
    (hcrossZero : conditionalCross =ᵐ[populationLaw] 0) :
    (∫ sample,
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          design) sample * residualProduct leftResidual rightResidual sample
        ∂selectedLaw) = 0 := by
  rw [selectedWeightedIntegral_residualProduct_eq_populationIntegral_div
    (mSample := mSample) (selectedLaw := selectedLaw)
    (populationLaw := populationLaw) design leftResidual rightResidual]
  rw [populationIntegral_residualProduct_eq_zero_of_conditionalCross_ae_zero
    (mSample := mSample) (scoreSigma := scoreSigma)
    (populationLaw := populationLaw) hsub leftResidual rightResidual
    conditionalCross hcross hcrossZero]
  simp

/--
If `conditionalCross` represents the score-sigma conditional residual cross
moment and that target is zero a.e., then the selected-law Hájek
residual-product target is zero.
-/
theorem selectedHajek_residualProduct_eq_zero_of_conditionalCross_ae_zero
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (leftResidual rightResidual conditionalCross : Sample -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1)
    (hcross :
      populationLaw[residualProduct leftResidual rightResidual | scoreSigma] =ᵐ[
        populationLaw] conditionalCross)
    (hcrossZero : conditionalCross =ᵐ[populationLaw] 0) :
    (∫ sample,
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          design) sample * residualProduct leftResidual rightResidual sample
        ∂selectedLaw) /
        (∫ sample,
          (@designCrossWeightReal Sample mSample selectedLaw populationLaw
            design) sample ∂selectedLaw) = 0 := by
  rw [selectedHajek_residualProduct_eq_conditionalCrossIntegral
    (mSample := mSample) (scoreSigma := scoreSigma)
    (selectedLaw := selectedLaw) (populationLaw := populationLaw)
    hsub design leftResidual rightResidual conditionalCross hpopulationOne
    hcross]
  exact integral_eq_zero_of_ae hcrossZero

/--
If two design survey weights are score-sigma measurable and
`conditionalCross` is the conditional residual cross moment, then the
population design-weight cross product rewrites to the corresponding
conditional-cross target.
-/
theorem integral_designWeights_mul_residualProduct_eq_crossMoment
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (leftDesign rightDesign :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (leftResidual rightResidual conditionalCross : Sample -> Real)
    (hleftMeas :
      AEStronglyMeasurable[scoreSigma]
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          leftDesign) populationLaw)
    (hrightMeas :
      AEStronglyMeasurable[scoreSigma]
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          rightDesign) populationLaw)
    (hproduct :
      Integrable
        (fun sample =>
          ((@designCrossWeightReal Sample mSample selectedLaw populationLaw
            leftDesign) sample *
            (@designCrossWeightReal Sample mSample selectedLaw populationLaw
              rightDesign) sample) *
            residualProduct leftResidual rightResidual sample)
        populationLaw)
    (hresidualProduct :
      Integrable (residualProduct leftResidual rightResidual) populationLaw)
    (hcross :
      populationLaw[residualProduct leftResidual rightResidual | scoreSigma] =ᵐ[
        populationLaw] conditionalCross) :
    ∫ sample,
        ((@designCrossWeightReal Sample mSample selectedLaw populationLaw
          leftDesign) sample *
          (@designCrossWeightReal Sample mSample selectedLaw populationLaw
            rightDesign) sample) *
          residualProduct leftResidual rightResidual sample ∂populationLaw =
      ∫ sample,
        ((@designCrossWeightReal Sample mSample selectedLaw populationLaw
          leftDesign) sample *
          (@designCrossWeightReal Sample mSample selectedLaw populationLaw
            rightDesign) sample) *
          conditionalCross sample ∂populationLaw := by
  exact
    integral_scoreMeasurable_mul_residualProduct_eq_crossMoment
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := populationLaw) hsub
      (@designCrossWeightReal Sample mSample selectedLaw populationLaw
        leftDesign)
      (@designCrossWeightReal Sample mSample selectedLaw populationLaw
        rightDesign)
      leftResidual rightResidual conditionalCross hleftMeas hrightMeas
      (by simpa [residualProduct, mul_assoc] using hproduct)
      (by simpa [residualProduct] using hresidualProduct)
      (by simpa [residualProduct] using hcross)

/--
If `conditionalCross` represents the score-sigma conditional residual cross
moment and that target is nonnegative a.e., then the population design-weight
residual-product cross term is nonnegative.
-/
theorem integral_designWeights_mul_residualProduct_nonneg_of_conditionalCross_nonneg
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (leftDesign rightDesign :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (leftResidual rightResidual conditionalCross : Sample -> Real)
    (hleftMeas :
      AEStronglyMeasurable[scoreSigma]
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          leftDesign) populationLaw)
    (hrightMeas :
      AEStronglyMeasurable[scoreSigma]
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          rightDesign) populationLaw)
    (hproduct :
      Integrable
        (fun sample =>
          ((@designCrossWeightReal Sample mSample selectedLaw populationLaw
            leftDesign) sample *
            (@designCrossWeightReal Sample mSample selectedLaw populationLaw
              rightDesign) sample) *
            residualProduct leftResidual rightResidual sample)
        populationLaw)
    (hresidualProduct :
      Integrable (residualProduct leftResidual rightResidual) populationLaw)
    (hcross :
      populationLaw[residualProduct leftResidual rightResidual | scoreSigma] =ᵐ[
        populationLaw] conditionalCross)
    (hcrossNonneg : 0 ≤ᵐ[populationLaw] conditionalCross) :
    0 ≤ ∫ sample,
        ((@designCrossWeightReal Sample mSample selectedLaw populationLaw
          leftDesign) sample *
          (@designCrossWeightReal Sample mSample selectedLaw populationLaw
            rightDesign) sample) *
          residualProduct leftResidual rightResidual sample ∂populationLaw := by
  rw [integral_designWeights_mul_residualProduct_eq_crossMoment
    (mSample := mSample) (scoreSigma := scoreSigma)
    (selectedLaw := selectedLaw) (populationLaw := populationLaw)
    hsub leftDesign rightDesign leftResidual rightResidual conditionalCross
    hleftMeas hrightMeas hproduct hresidualProduct hcross]
  refine integral_nonneg_of_ae ?_
  filter_upwards [hcrossNonneg] with sample hnonneg
  have hleft :
      0 ≤
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          leftDesign) sample := by
    exact
      ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
        selectedLaw populationLaw leftDesign) sample).2
  have hright :
      0 ≤
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          rightDesign) sample := by
    exact
      ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
        selectedLaw populationLaw rightDesign) sample).2
  exact mul_nonneg (mul_nonneg hleft hright) hnonneg

/--
If `conditionalCross` represents the score-sigma conditional residual cross
moment and that target is zero a.e., then the population design-weight
residual-product cross term is zero.
-/
theorem integral_designWeights_mul_residualProduct_eq_zero_of_conditionalCross_ae_zero
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (leftDesign rightDesign :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (leftResidual rightResidual conditionalCross : Sample -> Real)
    (hleftMeas :
      AEStronglyMeasurable[scoreSigma]
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          leftDesign) populationLaw)
    (hrightMeas :
      AEStronglyMeasurable[scoreSigma]
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          rightDesign) populationLaw)
    (hproduct :
      Integrable
        (fun sample =>
          ((@designCrossWeightReal Sample mSample selectedLaw populationLaw
            leftDesign) sample *
            (@designCrossWeightReal Sample mSample selectedLaw populationLaw
              rightDesign) sample) *
            residualProduct leftResidual rightResidual sample)
        populationLaw)
    (hresidualProduct :
      Integrable (residualProduct leftResidual rightResidual) populationLaw)
    (hcross :
      populationLaw[residualProduct leftResidual rightResidual | scoreSigma] =ᵐ[
        populationLaw] conditionalCross)
    (hcrossZero : conditionalCross =ᵐ[populationLaw] 0) :
    ∫ sample,
        ((@designCrossWeightReal Sample mSample selectedLaw populationLaw
          leftDesign) sample *
          (@designCrossWeightReal Sample mSample selectedLaw populationLaw
            rightDesign) sample) *
          residualProduct leftResidual rightResidual sample ∂populationLaw =
      0 := by
  rw [integral_designWeights_mul_residualProduct_eq_crossMoment
    (mSample := mSample) (scoreSigma := scoreSigma)
    (selectedLaw := selectedLaw) (populationLaw := populationLaw)
    hsub leftDesign rightDesign leftResidual rightResidual conditionalCross
    hleftMeas hrightMeas hproduct hresidualProduct hcross]
  refine integral_eq_zero_of_ae ?_
  filter_upwards [hcrossZero] with sample hzero
  simp [hzero]

/--
If the score-sigma conditional residual cross moment is zero, then the
selected-law survey-weighted Hájek residual-product target is zero.
-/
theorem selectedHajek_residualProduct_eq_zero_of_conditionalCross_zero
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (leftResidual rightResidual : Sample -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1)
    (hcrossZero :
      populationLaw[residualProduct leftResidual rightResidual | scoreSigma]
        =ᵐ[populationLaw] 0) :
    (∫ sample,
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          design) sample * residualProduct leftResidual rightResidual sample
        ∂selectedLaw) /
        (∫ sample,
          (@designCrossWeightReal Sample mSample selectedLaw populationLaw
            design) sample ∂selectedLaw) = 0 := by
  have h :=
    selectedHajek_residualProduct_eq_conditionalCrossIntegral
      (mSample := mSample) (scoreSigma := scoreSigma)
      (selectedLaw := selectedLaw) (populationLaw := populationLaw)
      hsub design leftResidual rightResidual (fun _sample => (0 : Real))
      hpopulationOne hcrossZero
  simpa using h

/--
If the score-sigma conditional residual cross moment is zero, then the
population design-weight residual-product cross term is zero.
-/
theorem integral_designWeights_mul_residualProduct_eq_zero_of_conditionalCross_zero
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (populationLaw.trim hsub)]
    (leftDesign rightDesign :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (leftResidual rightResidual : Sample -> Real)
    (hleftMeas :
      AEStronglyMeasurable[scoreSigma]
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          leftDesign) populationLaw)
    (hrightMeas :
      AEStronglyMeasurable[scoreSigma]
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          rightDesign) populationLaw)
    (hproduct :
      Integrable
        (fun sample =>
          ((@designCrossWeightReal Sample mSample selectedLaw populationLaw
            leftDesign) sample *
            (@designCrossWeightReal Sample mSample selectedLaw populationLaw
              rightDesign) sample) *
            residualProduct leftResidual rightResidual sample)
        populationLaw)
    (hresidualProduct :
      Integrable (residualProduct leftResidual rightResidual) populationLaw)
    (hcrossZero :
      populationLaw[residualProduct leftResidual rightResidual | scoreSigma]
        =ᵐ[populationLaw] 0) :
    ∫ sample,
        ((@designCrossWeightReal Sample mSample selectedLaw populationLaw
          leftDesign) sample *
          (@designCrossWeightReal Sample mSample selectedLaw populationLaw
            rightDesign) sample) *
          residualProduct leftResidual rightResidual sample ∂populationLaw =
      0 := by
  exact
    integral_scoreMeasurable_mul_residualProduct_eq_zero_of_condExp_zero
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := populationLaw) hsub
      (@designCrossWeightReal Sample mSample selectedLaw populationLaw
        leftDesign)
      (@designCrossWeightReal Sample mSample selectedLaw populationLaw
        rightDesign)
      leftResidual rightResidual hleftMeas hrightMeas
      (by simpa [residualProduct, mul_assoc] using hproduct)
      (by simpa [residualProduct] using hresidualProduct)
      (by simpa [residualProduct] using hcrossZero)

/--
If the left residual is zero a.e. under the population law, then the raw
population residual-product integral is zero.
-/
theorem populationIntegral_residualProduct_eq_zero_of_leftResidual_ae_zero
    (leftResidual rightResidual : Sample -> Real)
    (hleftZero : leftResidual =ᵐ[populationLaw] 0) :
    (∫ sample, residualProduct leftResidual rightResidual sample
      ∂populationLaw) = 0 := by
  refine integral_eq_zero_of_ae ?_
  filter_upwards [hleftZero] with sample hleft
  simp [residualProduct, hleft]

/--
If the left residual is zero a.e. under the selected law, then the selected-law
survey-weighted residual-product integral is zero.
-/
theorem selectedWeightedIntegral_residualProduct_eq_zero_of_selected_leftResidual_ae_zero
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (leftResidual rightResidual : Sample -> Real)
    (hleftZero : leftResidual =ᵐ[selectedLaw] 0) :
    (∫ sample,
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          design) sample * residualProduct leftResidual rightResidual sample
        ∂selectedLaw) = 0 := by
  refine integral_eq_zero_of_ae ?_
  filter_upwards [hleftZero] with sample hleft
  simp [residualProduct, hleft]

/--
If the left residual is zero a.e. under the selected law, then the selected-law
Hájek residual-product target is zero.
-/
theorem selectedHajek_residualProduct_eq_zero_of_selected_leftResidual_ae_zero
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (leftResidual rightResidual : Sample -> Real)
    (hleftZero : leftResidual =ᵐ[selectedLaw] 0) :
    (∫ sample,
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          design) sample * residualProduct leftResidual rightResidual sample
        ∂selectedLaw) /
        (∫ sample,
          (@designCrossWeightReal Sample mSample selectedLaw populationLaw
            design) sample ∂selectedLaw) = 0 := by
  rw [selectedWeightedIntegral_residualProduct_eq_zero_of_selected_leftResidual_ae_zero
    (mSample := mSample) (selectedLaw := selectedLaw)
    (populationLaw := populationLaw) design leftResidual rightResidual
    hleftZero]
  simp

/--
If the left residual is zero a.e. under the population law, then the
selected-law survey-weighted residual-product integral is zero by the
selection-density recovery identity.
-/
theorem selectedWeightedIntegral_residualProduct_eq_zero_of_population_leftResidual_ae_zero
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (leftResidual rightResidual : Sample -> Real)
    (hleftZero : leftResidual =ᵐ[populationLaw] 0) :
    (∫ sample,
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          design) sample * residualProduct leftResidual rightResidual sample
        ∂selectedLaw) = 0 := by
  rw [selectedWeightedIntegral_residualProduct_eq_populationIntegral_div
    (mSample := mSample) (selectedLaw := selectedLaw)
    (populationLaw := populationLaw) design leftResidual rightResidual]
  rw [populationIntegral_residualProduct_eq_zero_of_leftResidual_ae_zero
    (mSample := mSample) (populationLaw := populationLaw)
    leftResidual rightResidual hleftZero]
  simp

/--
If the left residual is zero a.e. under the population law, then the
selected-law Hájek residual-product target is zero.
-/
theorem selectedHajek_residualProduct_eq_zero_of_population_leftResidual_ae_zero
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (leftResidual rightResidual : Sample -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1)
    (hleftZero : leftResidual =ᵐ[populationLaw] 0) :
    (∫ sample,
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          design) sample * residualProduct leftResidual rightResidual sample
        ∂selectedLaw) /
        (∫ sample,
          (@designCrossWeightReal Sample mSample selectedLaw populationLaw
            design) sample ∂selectedLaw) = 0 := by
  rw [selectedHajek_residualProduct_eq_populationIntegral
    (mSample := mSample) (selectedLaw := selectedLaw)
    (populationLaw := populationLaw) design leftResidual rightResidual
    hpopulationOne]
  exact populationIntegral_residualProduct_eq_zero_of_leftResidual_ae_zero
    (mSample := mSample) (populationLaw := populationLaw)
    leftResidual rightResidual hleftZero

/--
If the left residual is zero a.e. under the population law, then the
population design-weight residual-product cross term is zero.
-/
theorem integral_designWeights_mul_residualProduct_eq_zero_of_population_leftResidual_ae_zero
    (leftDesign rightDesign :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (leftResidual rightResidual : Sample -> Real)
    (hleftZero : leftResidual =ᵐ[populationLaw] 0) :
    ∫ sample,
        ((@designCrossWeightReal Sample mSample selectedLaw populationLaw
          leftDesign) sample *
          (@designCrossWeightReal Sample mSample selectedLaw populationLaw
            rightDesign) sample) *
          residualProduct leftResidual rightResidual sample ∂populationLaw =
      0 := by
  refine integral_eq_zero_of_ae ?_
  filter_upwards [hleftZero] with sample hleft
  simp [residualProduct, hleft]

/--
If the right residual is zero a.e. under the population law, then the raw
population residual-product integral is zero.
-/
theorem populationIntegral_residualProduct_eq_zero_of_rightResidual_ae_zero
    (leftResidual rightResidual : Sample -> Real)
    (hrightZero : rightResidual =ᵐ[populationLaw] 0) :
    (∫ sample, residualProduct leftResidual rightResidual sample
      ∂populationLaw) = 0 := by
  refine integral_eq_zero_of_ae ?_
  filter_upwards [hrightZero] with sample hright
  simp [residualProduct, hright]

/--
If the right residual is zero a.e. under the selected law, then the selected-law
survey-weighted residual-product integral is zero.
-/
theorem selectedWeightedIntegral_residualProduct_eq_zero_of_selected_rightResidual_ae_zero
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (leftResidual rightResidual : Sample -> Real)
    (hrightZero : rightResidual =ᵐ[selectedLaw] 0) :
    (∫ sample,
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          design) sample * residualProduct leftResidual rightResidual sample
        ∂selectedLaw) = 0 := by
  refine integral_eq_zero_of_ae ?_
  filter_upwards [hrightZero] with sample hright
  simp [residualProduct, hright]

/--
If the right residual is zero a.e. under the selected law, then the selected-law
Hájek residual-product target is zero.
-/
theorem selectedHajek_residualProduct_eq_zero_of_selected_rightResidual_ae_zero
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (leftResidual rightResidual : Sample -> Real)
    (hrightZero : rightResidual =ᵐ[selectedLaw] 0) :
    (∫ sample,
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          design) sample * residualProduct leftResidual rightResidual sample
        ∂selectedLaw) /
        (∫ sample,
          (@designCrossWeightReal Sample mSample selectedLaw populationLaw
            design) sample ∂selectedLaw) = 0 := by
  rw [selectedWeightedIntegral_residualProduct_eq_zero_of_selected_rightResidual_ae_zero
    (mSample := mSample) (selectedLaw := selectedLaw)
    (populationLaw := populationLaw) design leftResidual rightResidual
    hrightZero]
  simp

/--
If the right residual is zero a.e. under the population law, then the
selected-law survey-weighted residual-product integral is zero by the
selection-density recovery identity.
-/
theorem selectedWeightedIntegral_residualProduct_eq_zero_of_population_rightResidual_ae_zero
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (leftResidual rightResidual : Sample -> Real)
    (hrightZero : rightResidual =ᵐ[populationLaw] 0) :
    (∫ sample,
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          design) sample * residualProduct leftResidual rightResidual sample
        ∂selectedLaw) = 0 := by
  rw [selectedWeightedIntegral_residualProduct_eq_populationIntegral_div
    (mSample := mSample) (selectedLaw := selectedLaw)
    (populationLaw := populationLaw) design leftResidual rightResidual]
  rw [populationIntegral_residualProduct_eq_zero_of_rightResidual_ae_zero
    (mSample := mSample) (populationLaw := populationLaw)
    leftResidual rightResidual hrightZero]
  simp

/--
If the right residual is zero a.e. under the population law, then the
selected-law Hájek residual-product target is zero.
-/
theorem selectedHajek_residualProduct_eq_zero_of_population_rightResidual_ae_zero
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (leftResidual rightResidual : Sample -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1)
    (hrightZero : rightResidual =ᵐ[populationLaw] 0) :
    (∫ sample,
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          design) sample * residualProduct leftResidual rightResidual sample
        ∂selectedLaw) /
        (∫ sample,
          (@designCrossWeightReal Sample mSample selectedLaw populationLaw
            design) sample ∂selectedLaw) = 0 := by
  rw [selectedHajek_residualProduct_eq_populationIntegral
    (mSample := mSample) (selectedLaw := selectedLaw)
    (populationLaw := populationLaw) design leftResidual rightResidual
    hpopulationOne]
  exact populationIntegral_residualProduct_eq_zero_of_rightResidual_ae_zero
    (mSample := mSample) (populationLaw := populationLaw)
    leftResidual rightResidual hrightZero

/--
If the right residual is zero a.e. under the population law, then the
population design-weight residual-product cross term is zero.
-/
theorem integral_designWeights_mul_residualProduct_eq_zero_of_population_rightResidual_ae_zero
    (leftDesign rightDesign :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (leftResidual rightResidual : Sample -> Real)
    (hrightZero : rightResidual =ᵐ[populationLaw] 0) :
    ∫ sample,
        ((@designCrossWeightReal Sample mSample selectedLaw populationLaw
          leftDesign) sample *
          (@designCrossWeightReal Sample mSample selectedLaw populationLaw
            rightDesign) sample) *
          residualProduct leftResidual rightResidual sample ∂populationLaw =
      0 := by
  refine integral_eq_zero_of_ae ?_
  filter_upwards [hrightZero] with sample hright
  simp [residualProduct, hright]

/--
The raw population diagonal residual-product integral is nonnegative.
-/
theorem populationIntegral_residualProduct_self_nonneg
    (residual : Sample -> Real) :
    0 ≤ ∫ sample, residualProduct residual residual sample ∂populationLaw := by
  refine integral_nonneg_of_ae ?_
  filter_upwards [] with sample
  exact mul_self_nonneg (residual sample)

/--
The selected-law survey-weighted diagonal residual-product integral is
nonnegative.
-/
theorem selectedWeightedIntegral_residualProduct_self_nonneg
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (residual : Sample -> Real) :
    0 ≤
      ∫ sample,
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          design) sample * residualProduct residual residual sample
        ∂selectedLaw := by
  refine integral_nonneg_of_ae ?_
  filter_upwards [] with sample
  have hweight :
      0 ≤
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          design) sample := by
    exact
      ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
        selectedLaw populationLaw design) sample).2
  exact mul_nonneg hweight
    (by
      simpa [residualProduct] using mul_self_nonneg (residual sample))

/--
The selected-law Hájek diagonal residual-product target is nonnegative.
-/
theorem selectedHajek_residualProduct_self_nonneg
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (residual : Sample -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1) :
    0 ≤
      (∫ sample,
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          design) sample * residualProduct residual residual sample
        ∂selectedLaw) /
        (∫ sample,
          (@designCrossWeightReal Sample mSample selectedLaw populationLaw
            design) sample ∂selectedLaw) := by
  rw [selectedHajek_residualProduct_eq_populationIntegral
    (mSample := mSample) (selectedLaw := selectedLaw)
    (populationLaw := populationLaw) design residual residual
    hpopulationOne]
  exact populationIntegral_residualProduct_self_nonneg
    (mSample := mSample) (populationLaw := populationLaw) residual

/--
The population design-weight diagonal residual-product cross term is
nonnegative.
-/
theorem integral_designWeights_mul_residualProduct_self_nonneg
    (leftDesign rightDesign :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (residual : Sample -> Real) :
    0 ≤ ∫ sample,
        ((@designCrossWeightReal Sample mSample selectedLaw populationLaw
          leftDesign) sample *
          (@designCrossWeightReal Sample mSample selectedLaw populationLaw
            rightDesign) sample) *
          residualProduct residual residual sample ∂populationLaw := by
  refine integral_nonneg_of_ae ?_
  filter_upwards [] with sample
  have hleft :
      0 ≤
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          leftDesign) sample := by
    exact
      ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
        selectedLaw populationLaw leftDesign) sample).2
  have hright :
      0 ≤
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          rightDesign) sample := by
    exact
      ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
        selectedLaw populationLaw rightDesign) sample).2
  exact mul_nonneg (mul_nonneg hleft hright)
    (by
      simpa [residualProduct] using mul_self_nonneg (residual sample))

/--
Selected-law survey-weighted residual-product integrals are symmetric in the
two residuals.
-/
theorem selectedWeightedIntegral_residualProduct_symm
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (leftResidual rightResidual : Sample -> Real) :
    (∫ sample,
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          design) sample * residualProduct leftResidual rightResidual sample
        ∂selectedLaw) =
      ∫ sample,
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          design) sample * residualProduct rightResidual leftResidual sample
        ∂selectedLaw := by
  refine integral_congr_ae ?_
  filter_upwards [] with sample
  simp [residualProduct, mul_comm, mul_assoc]

/--
Selected-law survey-weighted Hájek residual-product targets are symmetric in
the two residuals.
-/
theorem selectedHajek_residualProduct_symm
    (design :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (leftResidual rightResidual : Sample -> Real) :
    (∫ sample,
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          design) sample * residualProduct leftResidual rightResidual sample
        ∂selectedLaw) /
        (∫ sample,
          (@designCrossWeightReal Sample mSample selectedLaw populationLaw
            design) sample ∂selectedLaw) =
      (∫ sample,
        (@designCrossWeightReal Sample mSample selectedLaw populationLaw
          design) sample * residualProduct rightResidual leftResidual sample
        ∂selectedLaw) /
        (∫ sample,
          (@designCrossWeightReal Sample mSample selectedLaw populationLaw
            design) sample ∂selectedLaw) := by
  rw [selectedWeightedIntegral_residualProduct_symm
    (mSample := mSample) (selectedLaw := selectedLaw)
    (populationLaw := populationLaw) design leftResidual rightResidual]

/--
Population design-weight residual-product cross terms are symmetric when the
two designs and residuals are swapped together.
-/
theorem integral_designWeights_mul_residualProduct_symm
    (leftDesign rightDesign :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (leftResidual rightResidual : Sample -> Real) :
    (∫ sample,
        ((@designCrossWeightReal Sample mSample selectedLaw populationLaw
          leftDesign) sample *
          (@designCrossWeightReal Sample mSample selectedLaw populationLaw
            rightDesign) sample) *
          residualProduct leftResidual rightResidual sample ∂populationLaw) =
      ∫ sample,
        ((@designCrossWeightReal Sample mSample selectedLaw populationLaw
          rightDesign) sample *
          (@designCrossWeightReal Sample mSample selectedLaw populationLaw
            leftDesign) sample) *
          residualProduct rightResidual leftResidual sample ∂populationLaw := by
  refine integral_congr_ae ?_
  filter_upwards [] with sample
  simp [residualProduct, mul_comm, mul_assoc]

end WDSM
end Matching
end StatInference
