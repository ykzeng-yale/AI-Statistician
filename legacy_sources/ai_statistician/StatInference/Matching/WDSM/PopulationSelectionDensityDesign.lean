import StatInference.Matching.WDSM.PopulationSurveySelectionDensity

/-!
# Population selection-density design object

This module packages the primitive population survey design assumptions used by
the selection-density bridge into a named Lean structure.  Later WDSM
identification and asymptotic statements can depend on this audited object
instead of repeating the same long list of selection-probability, inverse
survey-weight, and sampling-mass hypotheses.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open scoped MeasureTheory ENNReal

variable {Sample : Type*} [mSample : MeasurableSpace Sample]

/--
A primitive population selection-density survey design.

`selectedLaw` is the population law tilted by a nonnegative selection
probability and normalized by `samplingMass`; `surveyWeight` is the pointwise
inverse of that selection probability in `ENNReal`.
-/
structure PopulationSelectionDensityDesign
    (selectedLaw populationLaw : Measure Sample) where
  selectionProb : Sample -> NNReal
  surveyWeight : Sample -> NNReal
  samplingMass : Real
  selectionMeas : Measurable selectionProb
  weightMeas : Measurable surveyWeight
  sampling_pos : 0 < samplingMass
  selectedLaw_eq :
    selectedLaw =
      ENNReal.ofReal (1 / samplingMass) •
        populationLaw.withDensity
          (fun sample => (selectionProb sample : ENNReal))
  inverse_weight :
    ∀ sample,
      (selectionProb sample : ENNReal) *
        (surveyWeight sample : ENNReal) = 1

namespace PopulationSelectionDensityDesign

variable {selectedLaw populationLaw : Measure Sample}

/--
The packaged design assumptions imply the density-reweighted selected law is a
scaled population law.
-/
theorem withDensity_surveyWeight_eq_scaled_populationLaw
    (design : PopulationSelectionDensityDesign selectedLaw populationLaw) :
    selectedLaw.withDensity
        (fun sample => (design.surveyWeight sample : ENNReal)) =
      ENNReal.ofReal (1 / design.samplingMass) • populationLaw := by
  exact
    selectedLaw_withDensity_surveyWeight_eq_scaled_populationLaw selectedLaw
      populationLaw design.selectionProb design.surveyWeight
      design.samplingMass design.selectionMeas design.weightMeas
      design.selectedLaw_eq design.inverse_weight

/--
The selected law in a packaged selection-density design is absolutely
continuous with respect to the population law.
-/
theorem selectedLaw_absolutelyContinuous_populationLaw
    (design : PopulationSelectionDensityDesign selectedLaw populationLaw) :
    selectedLaw ≪ populationLaw := by
  rw [design.selectedLaw_eq]
  exact (withDensity_absolutelyContinuous populationLaw
    (fun sample => (design.selectionProb sample : ENNReal))).smul_left
      (ENNReal.ofReal (1 / design.samplingMass))

/--
Any population-law a.e. predicate also holds selected-law a.e. under a
population selection-density design.
-/
theorem selectedLaw_ae_of_populationLaw_ae
    (design : PopulationSelectionDensityDesign selectedLaw populationLaw)
    {predicate : Sample -> Prop}
    (hpopulation : ∀ᵐ sample ∂populationLaw, predicate sample) :
    ∀ᵐ sample ∂selectedLaw, predicate sample :=
  (selectedLaw_absolutelyContinuous_populationLaw design).ae_le hpopulation

/--
Population-law a.e. equality transfers to selected-law a.e. equality under a
population selection-density design.
-/
theorem selectedLaw_ae_eq_of_populationLaw_ae_eq
    (design : PopulationSelectionDensityDesign selectedLaw populationLaw)
    {left right : Sample -> Real}
    (hpopulation : left =ᵐ[populationLaw] right) :
    left =ᵐ[selectedLaw] right :=
  selectedLaw_ae_of_populationLaw_ae design hpopulation

/--
Population-law a.e. zero facts transfer to selected-law a.e. zero facts under
a population selection-density design.
-/
theorem selectedLaw_ae_eq_zero_of_populationLaw_ae_eq_zero
    (design : PopulationSelectionDensityDesign selectedLaw populationLaw)
    {target : Sample -> Real}
    (hpopulation : target =ᵐ[populationLaw] fun _sample => (0 : Real)) :
    target =ᵐ[selectedLaw] fun _sample => (0 : Real) :=
  selectedLaw_ae_eq_of_populationLaw_ae_eq design hpopulation

/--
Every selected-law survey-weighted integral recovers the corresponding
population-law integral divided by the sampling mass.
-/
theorem surveyWeightedIntegral_eq_populationIntegral_div
    (design : PopulationSelectionDensityDesign selectedLaw populationLaw)
    (target : Sample -> Real) :
    (∫ sample, (design.surveyWeight sample : Real) * target sample
        ∂selectedLaw) =
      (∫ sample, target sample ∂populationLaw) / design.samplingMass := by
  exact
    surveyWeightIntegral_eq_populationIntegral_div_of_densityScaling
      selectedLaw populationLaw design.surveyWeight target
      design.samplingMass design.weightMeas design.sampling_pos
      (withDensity_surveyWeight_eq_scaled_populationLaw design)

/--
The survey-weighted selected-law mass is the inverse sampling mass when the
population law has integral-one mass in the real-integral normalization.
-/
theorem surveyWeightedOne_eq_inv_samplingMass
    (design : PopulationSelectionDensityDesign selectedLaw populationLaw)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1) :
    (∫ sample, (design.surveyWeight sample : Real) ∂selectedLaw) =
      1 / design.samplingMass := by
  have h :=
    surveyWeightedIntegral_eq_populationIntegral_div design
      (fun _sample => (1 : Real))
  simpa [hpopulationOne] using h

/--
The packaged design assumptions construct the abstract inverse-selection
identity consumed by the population Hájek ratio layer.
-/
noncomputable def toInverseSelectionIdentity
    (design : PopulationSelectionDensityDesign selectedLaw populationLaw)
    (target : Sample -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1) :
    InverseSelectionIdentity :=
  inverseSelectionIdentityOfWeightedIntegralRecovery selectedLaw populationLaw
    (fun sample => (design.surveyWeight sample : Real)) target
    design.samplingMass
    (surveyWeightedIntegral_eq_populationIntegral_div design target)
    (surveyWeightedOne_eq_inv_samplingMass design hpopulationOne)

/--
The selected-law survey-weighted Hájek ratio recovers the population-law
integral for any target under a packaged population selection-density design.
-/
theorem hajekRatio_eq_populationIntegral
    (design : PopulationSelectionDensityDesign selectedLaw populationLaw)
    (target : Sample -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1) :
    (∫ sample, (design.surveyWeight sample : Real) * target sample
        ∂selectedLaw) /
        (∫ sample, (design.surveyWeight sample : Real) ∂selectedLaw) =
      ∫ sample, target sample ∂populationLaw := by
  exact
    InverseSelectionIdentity.hajekRatio_eq_populationTarget
      (toInverseSelectionIdentity design target hpopulationOne)
      (ne_of_gt design.sampling_pos)

/--
If the packaged survey weight is measurable with respect to a score sigma-field,
then its real-valued coercion is a.e. strongly measurable with respect to that
score sigma-field.
-/
theorem aestronglyMeasurable_surveyWeight_real_of_scoreMeasurable
    {scoreSigma : MeasurableSpace Sample} {sampleLaw : Measure[mSample] Sample}
    (design : @PopulationSelectionDensityDesign Sample mSample selectedLaw
      populationLaw)
    (hweightScoreMeas :
      @Measurable Sample NNReal scoreSigma _
        (@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw design)) :
    AEStronglyMeasurable[scoreSigma]
      (fun sample =>
        ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw design) sample : Real)) sampleLaw := by
  exact (NNReal.continuous_coe.measurable.comp
    hweightScoreMeas).aestronglyMeasurable

/--
If two packaged survey weights are score-sigma measurable, then their
real-valued product is a.e. strongly measurable with respect to that score
sigma-field.
-/
theorem aestronglyMeasurable_surveyWeight_real_mul_of_scoreMeasurable
    {scoreSigma : MeasurableSpace Sample} {sampleLaw : Measure[mSample] Sample}
    (leftDesign rightDesign :
      @PopulationSelectionDensityDesign Sample mSample selectedLaw
        populationLaw)
    (hleftWeight :
      @Measurable Sample NNReal scoreSigma _
        (@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw leftDesign))
    (hrightWeight :
      @Measurable Sample NNReal scoreSigma _
        (@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw rightDesign)) :
    AEStronglyMeasurable[scoreSigma]
      (fun sample =>
        ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw leftDesign) sample : Real) *
        ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw rightDesign) sample : Real)) sampleLaw := by
  have hleft :
      AEStronglyMeasurable[scoreSigma]
        (fun sample =>
          ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
            selectedLaw populationLaw leftDesign) sample : Real)) sampleLaw := by
    exact (NNReal.continuous_coe.measurable.comp
      hleftWeight).aestronglyMeasurable
  have hright :
      AEStronglyMeasurable[scoreSigma]
        (fun sample =>
          ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
            selectedLaw populationLaw rightDesign) sample : Real)) sampleLaw := by
    exact (NNReal.continuous_coe.measurable.comp
      hrightWeight).aestronglyMeasurable
  exact hleft.mul hright

/--
If a packaged survey weight is score-sigma measurable, then its real-valued
square is a.e. strongly measurable with respect to that score sigma-field.
-/
theorem aestronglyMeasurable_surveyWeight_real_sq_of_scoreMeasurable
    {scoreSigma : MeasurableSpace Sample} {sampleLaw : Measure[mSample] Sample}
    (design : @PopulationSelectionDensityDesign Sample mSample selectedLaw
      populationLaw)
    (hweightScoreMeas :
      @Measurable Sample NNReal scoreSigma _
        (@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw design)) :
    AEStronglyMeasurable[scoreSigma]
      (fun sample =>
        ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw design) sample : Real) *
        ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
          selectedLaw populationLaw design) sample : Real)) sampleLaw := by
  have hweight :
      AEStronglyMeasurable[scoreSigma]
        (fun sample =>
          ((@PopulationSelectionDensityDesign.surveyWeight Sample mSample
            selectedLaw populationLaw design) sample : Real)) sampleLaw := by
    exact (NNReal.continuous_coe.measurable.comp
      hweightScoreMeas).aestronglyMeasurable
  exact hweight.mul hweight

end PopulationSelectionDensityDesign

end WDSM
end Matching
end StatInference
