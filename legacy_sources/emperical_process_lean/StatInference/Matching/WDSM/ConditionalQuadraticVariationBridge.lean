import StatInference.Matching.WDSM.ConditionalOrthogonalityBridge

/-!
# Conditional quadratic-variation bridge for WDSM residuals

The finite residual variance modules use quadratic variations of the form
`coefficient^2 * conditionalVariance`.  This module proves the
measure-theoretic pull-out step behind that target: score-measurable squared
coefficients can be pulled outside the conditional expectation of squared
residuals.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open scoped MeasureTheory

variable {Sample : Type*} [mSample : MeasurableSpace Sample]
variable {scoreSigma : MeasurableSpace Sample}
variable {sampleLaw : Measure[mSample] Sample}

/--
Score-sigma-field measurable squared coefficients pull out of the conditional
expectation of squared residuals.
-/
theorem condExp_scoreMeasurable_sq_mul_residual_sq_ae_eq
    (coefficient residual : Sample -> Real)
    (hcoefficient :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw)
    (hproduct :
      Integrable
        (fun sample =>
          (coefficient sample * coefficient sample) *
            (residual sample * residual sample)) sampleLaw)
    (hresidualSq :
      Integrable (fun sample => residual sample * residual sample)
        sampleLaw) :
    sampleLaw[(fun sample =>
        (coefficient sample * coefficient sample) *
          (residual sample * residual sample)) | scoreSigma] =ᵐ[sampleLaw]
      fun sample =>
        (coefficient sample * coefficient sample) *
          sampleLaw[(fun sample => residual sample * residual sample) |
            scoreSigma] sample := by
  have hcoefficientSq :
      AEStronglyMeasurable[scoreSigma]
        (fun sample => coefficient sample * coefficient sample) sampleLaw :=
    hcoefficient.mul hcoefficient
  exact
    condExp_mul_of_aestronglyMeasurable_left
      (m := scoreSigma) (μ := sampleLaw) hcoefficientSq hproduct
      hresidualSq

/--
Integral form of the quadratic-variation bridge.  If `conditionalVariance` is
the conditional second moment of the residual, then the unconditional second
moment of a score-measurable weighted residual equals the corresponding
quadratic-variation integral.
-/
theorem integral_scoreMeasurable_sq_mul_residual_sq_eq_variance
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (coefficient residual conditionalVariance : Sample -> Real)
    (hcoefficient :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw)
    (hproduct :
      Integrable
        (fun sample =>
          (coefficient sample * coefficient sample) *
            (residual sample * residual sample)) sampleLaw)
    (hresidualSq :
      Integrable (fun sample => residual sample * residual sample)
        sampleLaw)
    (hvariance :
      sampleLaw[(fun sample => residual sample * residual sample) |
        scoreSigma] =ᵐ[sampleLaw] conditionalVariance) :
    ∫ sample,
        (coefficient sample * coefficient sample) *
          (residual sample * residual sample) ∂sampleLaw =
      ∫ sample,
        (coefficient sample * coefficient sample) *
          conditionalVariance sample ∂sampleLaw := by
  rw [← integral_condExp
    (m := scoreSigma) (m₀ := mSample) (μ := sampleLaw)
    (f := fun sample =>
      (coefficient sample * coefficient sample) *
        (residual sample * residual sample)) hsub]
  refine integral_congr_ae ?_
  exact
    (condExp_scoreMeasurable_sq_mul_residual_sq_ae_eq
      (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
      coefficient residual hcoefficient hproduct hresidualSq).trans
      (hvariance.mono fun sample hsample => by
        simp [hsample])

/--
Centered-residual specialization of the conditional quadratic-variation
pull-out.
-/
theorem condExp_scoreMeasurable_sq_mul_centeredResidual_sq_ae_eq
    (coefficient outcome scoreVersion : Sample -> Real)
    (hcoefficient :
      AEStronglyMeasurable[scoreSigma] coefficient sampleLaw)
    (hproduct :
      Integrable
        (fun sample =>
          (coefficient sample * coefficient sample) *
            ((outcome sample - scoreVersion sample) *
              (outcome sample - scoreVersion sample))) sampleLaw)
    (hresidualSq :
      Integrable
        (fun sample =>
          (outcome sample - scoreVersion sample) *
            (outcome sample - scoreVersion sample)) sampleLaw) :
    sampleLaw[(fun sample =>
        (coefficient sample * coefficient sample) *
          ((outcome sample - scoreVersion sample) *
            (outcome sample - scoreVersion sample))) | scoreSigma] =ᵐ[
      sampleLaw]
      fun sample =>
        (coefficient sample * coefficient sample) *
          sampleLaw[(fun sample =>
            (outcome sample - scoreVersion sample) *
              (outcome sample - scoreVersion sample)) | scoreSigma] sample := by
  exact
    condExp_scoreMeasurable_sq_mul_residual_sq_ae_eq
      (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
      coefficient (fun sample => outcome sample - scoreVersion sample)
      hcoefficient hproduct hresidualSq

end WDSM
end Matching
end StatInference
