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

end WDSM
end Matching
end StatInference
