import StatInference.Matching.WDSM.ConditionalQuadraticVariationBridge

/-!
# Conditional variance target bridge for WDSM residuals

The previous conditional quadratic-variation bridge rewrites weighted residual
second moments as integrals of score-measurable squared coefficients times a
conditional variance target.  This module proves the elementary positivity and
zero-specialization facts for that target.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory

variable {Sample : Type*} [mSample : MeasurableSpace Sample]
variable {sampleLaw : Measure[mSample] Sample}

/--
The score-space residual variance target is nonnegative when the conditional
variance is nonnegative almost everywhere.
-/
theorem integral_scoreMeasurable_sq_mul_conditionalVariance_nonneg
    (coefficient conditionalVariance : Sample -> Real)
    (hvariance_nonneg :
      0 ≤ᵐ[sampleLaw] conditionalVariance) :
    0 ≤ ∫ sample,
      (coefficient sample * coefficient sample) *
        conditionalVariance sample ∂sampleLaw := by
  refine integral_nonneg_of_ae ?_
  filter_upwards [hvariance_nonneg] with sample hvariance
  exact mul_nonneg (mul_self_nonneg (coefficient sample)) hvariance

/--
If the conditional variance is zero almost everywhere, then the corresponding
score-space residual variance target is zero.
-/
theorem integral_scoreMeasurable_sq_mul_conditionalVariance_eq_zero_of_ae_eq_zero
    (coefficient conditionalVariance : Sample -> Real)
    (hvariance_zero :
      conditionalVariance =ᵐ[sampleLaw] 0) :
    ∫ sample,
      (coefficient sample * coefficient sample) *
        conditionalVariance sample ∂sampleLaw = 0 := by
  refine integral_eq_zero_of_ae ?_
  filter_upwards [hvariance_zero] with sample hvariance
  simp [hvariance]

/--
Nonnegativity after the conditional quadratic-variation rewrite: if the
conditional second moment is represented by a nonnegative variance function,
then the rewritten quadratic-variation integral is nonnegative.
-/
theorem integral_scoreMeasurable_sq_mul_residual_sq_rewrite_nonneg
    {scoreSigma : MeasurableSpace Sample}
    (hsub : scoreSigma ≤ mSample)
    [SigmaFinite (sampleLaw.trim hsub)]
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
        scoreSigma] =ᵐ[sampleLaw] conditionalVariance)
    (hvariance_nonneg :
      0 ≤ᵐ[sampleLaw] conditionalVariance) :
    0 ≤ ∫ sample,
      (coefficient sample * coefficient sample) *
        (residual sample * residual sample) ∂sampleLaw := by
  rw [integral_scoreMeasurable_sq_mul_residual_sq_eq_variance
    (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
    hsub coefficient residual conditionalVariance
    hcoefficient hproduct hresidualSq hvariance]
  exact integral_scoreMeasurable_sq_mul_conditionalVariance_nonneg
    (mSample := mSample) (sampleLaw := sampleLaw) coefficient
    conditionalVariance hvariance_nonneg

end WDSM
end Matching
end StatInference
