import StatInference.Matching.WDSM.ConditionalResidualBridge
import Mathlib.MeasureTheory.Function.ConditionalExpectation.PullOut

/-!
# Conditional orthogonality bridge for WDSM residuals

Residual variance and CLT arguments repeatedly use the fact that score-measurable
coefficients are orthogonal to residuals with zero conditional mean.  This
module proves that measure-theoretic bridge using mathlib's conditional
expectation pull-out property.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open Filter
open scoped MeasureTheory

variable {Sample : Type*} [mSample : MeasurableSpace Sample]
variable {scoreSigma : MeasurableSpace Sample}
variable {sampleLaw : Measure[mSample] Sample}

/--
If a residual has zero conditional mean given the score sigma-field, multiplying
it by a score-sigma-field measurable coefficient preserves zero conditional
mean.
-/
theorem condExp_scoreMeasurable_mul_residual_ae_eq_zero
    (coefficient residual : Sample -> Real)
    (hcoefficient :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw)
    (hproduct :
      Integrable (fun sample => coefficient sample * residual sample)
        sampleLaw)
    (hresidual : Integrable residual sampleLaw)
    (hzero :
      sampleLaw[residual | scoreSigma] =ᵐ[sampleLaw] 0) :
    sampleLaw[(fun sample => coefficient sample * residual sample) | scoreSigma] =ᵐ[
      sampleLaw] 0 := by
  refine
    (condExp_mul_of_aestronglyMeasurable_left
      (m := scoreSigma) (μ := sampleLaw) hcoefficient hproduct
      hresidual).trans ?_
  filter_upwards [hzero] with sample hsample
  simp [hsample]

/--
Integral form of the conditional orthogonality bridge.  Under a
sub-sigma-field relation, a score-measurable coefficient times a residual with
zero conditional mean integrates to zero.
-/
theorem integral_scoreMeasurable_mul_residual_eq_zero
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (coefficient residual : Sample -> Real)
    (hcoefficient :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw)
    (hproduct :
      Integrable (fun sample => coefficient sample * residual sample)
        sampleLaw)
    (hresidual : Integrable residual sampleLaw)
    (hzero :
      sampleLaw[residual | scoreSigma] =ᵐ[sampleLaw] 0) :
    ∫ sample, coefficient sample * residual sample ∂sampleLaw = 0 := by
  have horth :
      sampleLaw[(fun sample => coefficient sample * residual sample) |
        scoreSigma] =ᵐ[sampleLaw] 0 :=
    condExp_scoreMeasurable_mul_residual_ae_eq_zero
      (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
      coefficient residual hcoefficient hproduct
      hresidual hzero
  rw [← integral_condExp
    (m := scoreSigma) (m₀ := mSample) (μ := sampleLaw)
    (f := fun sample => coefficient sample * residual sample) hsub]
  simpa using integral_congr_ae horth

/--
If a residual is zero almost everywhere, then any score-weighted residual has
zero conditional expectation.  This direct route is useful when the residual
vanishes by an a.e. score-version identity.
-/
theorem condExp_scoreMeasurable_mul_residual_ae_eq_zero_of_residual_ae_zero
    (coefficient residual : Sample -> Real)
    (hresidualZero : residual =ᵐ[sampleLaw] 0) :
    sampleLaw[(fun sample => coefficient sample * residual sample) |
      scoreSigma] =ᵐ[sampleLaw] 0 := by
  have hproductZero :
      (fun sample => coefficient sample * residual sample) =ᵐ[sampleLaw]
        (fun _sample => (0 : Real)) := by
    filter_upwards [hresidualZero] with sample hsample
    simp [hsample]
  exact
    (condExp_congr_ae (m := scoreSigma) (μ := sampleLaw)
      hproductZero).trans
      (by
        change sampleLaw[(0 : Sample -> Real) | scoreSigma] =ᵐ[
          sampleLaw] (0 : Sample -> Real)
        rw [condExp_zero])

/--
If a residual is zero almost everywhere, then every weighted residual has zero
integral.  No score-measurability or conditional-expectation pull-out is needed
for this degenerate residual case.
-/
theorem integral_scoreMeasurable_mul_residual_eq_zero_of_residual_ae_zero
    (coefficient residual : Sample -> Real)
    (hresidualZero : residual =ᵐ[sampleLaw] 0) :
    ∫ sample, coefficient sample * residual sample ∂sampleLaw = 0 := by
  refine integral_eq_zero_of_ae ?_
  filter_upwards [hresidualZero] with sample hsample
  simp [hsample]

/--
If an outcome agrees a.e. with its score version, then the centered residual
has zero score-sigma conditional expectation.
-/
theorem condExp_centeredResidual_ae_eq_zero_of_ae_scoreVersion
    (outcome scoreVersion : Sample -> Real)
    (hae : outcome =ᵐ[sampleLaw] scoreVersion) :
    sampleLaw[(fun sample => outcome sample - scoreVersion sample) |
      scoreSigma] =ᵐ[sampleLaw] 0 := by
  have hresidualZero :
      (fun sample => outcome sample - scoreVersion sample) =ᵐ[sampleLaw]
        (fun _sample => (0 : Real)) := by
    filter_upwards [hae] with sample hsample
    simp [hsample]
  exact
    (condExp_congr_ae (m := scoreSigma) (μ := sampleLaw)
      hresidualZero).trans
      (by
        change sampleLaw[(0 : Sample -> Real) | scoreSigma] =ᵐ[
          sampleLaw] (0 : Sample -> Real)
        rw [condExp_zero])

/--
If an outcome agrees a.e. with its score version, every score-measurable
coefficient is orthogonal to the centered residual.
-/
theorem integral_scoreMeasurable_mul_centeredResidual_eq_zero_of_ae_scoreVersion
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (coefficient outcome scoreVersion : Sample -> Real)
    (hcoefficient :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw)
    (hproduct :
      Integrable
        (fun sample => coefficient sample *
          (outcome sample - scoreVersion sample)) sampleLaw)
    (hresidual :
      Integrable (fun sample => outcome sample - scoreVersion sample)
        sampleLaw)
    (hae : outcome =ᵐ[sampleLaw] scoreVersion) :
    ∫ sample,
        coefficient sample * (outcome sample - scoreVersion sample)
        ∂sampleLaw = 0 := by
  exact
    integral_scoreMeasurable_mul_residual_eq_zero
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub coefficient
      (fun sample => outcome sample - scoreVersion sample)
      hcoefficient hproduct hresidual
      (condExp_centeredResidual_ae_eq_zero_of_ae_scoreVersion
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) outcome scoreVersion hae)

/--
Direct a.e. variant of weighted centered-residual orthogonality.
-/
theorem integral_scoreMeasurable_mul_centeredResidual_eq_zero_of_direct_ae_scoreVersion
    (coefficient outcome scoreVersion : Sample -> Real)
    (hae : outcome =ᵐ[sampleLaw] scoreVersion) :
    ∫ sample,
        coefficient sample * (outcome sample - scoreVersion sample)
        ∂sampleLaw = 0 := by
  exact
    integral_scoreMeasurable_mul_residual_eq_zero_of_residual_ae_zero
      (mSample := mSample) (sampleLaw := sampleLaw) coefficient
      (fun sample => outcome sample - scoreVersion sample)
      (by
        filter_upwards [hae] with sample hsample
        simp [hsample])

/--
Combined centered-residual version.  If a score-space version is the
conditional expectation of an outcome, then every score-measurable coefficient
is conditionally orthogonal to the centered residual.
-/
theorem condExp_scoreMeasurable_mul_centeredResidual_ae_eq_zero
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (coefficient outcome scoreVersion : Sample -> Real)
    (hcoefficient :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw)
    (houtcome : Integrable outcome sampleLaw)
    (hscore : Integrable scoreVersion sampleLaw)
    (hscoreMeas :
      AEStronglyMeasurable[scoreSigma] scoreVersion sampleLaw)
    (hproduct :
      Integrable
        (fun sample => coefficient sample *
          (outcome sample - scoreVersion sample)) sampleLaw)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion) :
    sampleLaw[(fun sample =>
        coefficient sample * (outcome sample - scoreVersion sample)) |
        scoreSigma] =ᵐ[sampleLaw] 0 := by
  exact
    condExp_scoreMeasurable_mul_residual_ae_eq_zero
      (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
      coefficient
      (fun sample => outcome sample - scoreVersion sample)
      hcoefficient hproduct (houtcome.sub hscore)
      (condExp_residual_ae_eq_zero_of_condExp_ae_eq_scoreVersion_aestronglyMeasurable
        (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
        hsub outcome scoreVersion houtcome hscore
        hscoreMeas hcond)

/--
Raw-outcome-integrability variant of conditional orthogonality for a
score-measurable weighted centered residual.
-/
theorem condExp_scoreMeasurable_mul_centeredResidual_ae_eq_zero_outcomeIntegrable
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (coefficient outcome scoreVersion : Sample -> Real)
    (hcoefficient :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw)
    (houtcome : Integrable outcome sampleLaw)
    (hscoreMeas :
      AEStronglyMeasurable[scoreSigma] scoreVersion sampleLaw)
    (hproduct :
      Integrable
        (fun sample => coefficient sample *
          (outcome sample - scoreVersion sample)) sampleLaw)
    (hcond :
      sampleLaw[outcome | scoreSigma] =ᵐ[sampleLaw] scoreVersion) :
    sampleLaw[(fun sample =>
        coefficient sample * (outcome sample - scoreVersion sample)) |
        scoreSigma] =ᵐ[sampleLaw] 0 := by
  have hscore : Integrable scoreVersion sampleLaw :=
    integrable_condExp.congr hcond
  exact
    condExp_scoreMeasurable_mul_centeredResidual_ae_eq_zero
      (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
      hsub coefficient outcome scoreVersion hcoefficient houtcome hscore
      hscoreMeas hproduct hcond

end WDSM
end Matching
end StatInference
