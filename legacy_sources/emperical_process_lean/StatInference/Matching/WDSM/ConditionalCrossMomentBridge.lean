import StatInference.Matching.WDSM.ConditionalQuadraticVariationBridge

/-!
# Conditional cross-moment bridge for WDSM residuals

The finite residual covariance modules reduce variance calculations to
quadratic variations once off-diagonal residual cross moments vanish.  This
module proves the measure-theoretic pull-out step for cross products with
score-measurable coefficients.
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
Products of score-sigma-field measurable coefficients pull out of conditional
expectations of residual cross products.
-/
theorem condExp_scoreMeasurable_mul_residualProduct_ae_eq
    (leftCoefficient rightCoefficient leftResidual rightResidual :
      Sample -> Real)
    (hleft :
      AEStronglyMeasurable[scoreSigma] leftCoefficient sampleLaw)
    (hright :
      AEStronglyMeasurable[scoreSigma] rightCoefficient sampleLaw)
    (hproduct :
      Integrable
        (fun sample =>
          (leftCoefficient sample * rightCoefficient sample) *
            (leftResidual sample * rightResidual sample)) sampleLaw)
    (hresidualProduct :
      Integrable (fun sample => leftResidual sample * rightResidual sample)
        sampleLaw) :
    sampleLaw[(fun sample =>
        (leftCoefficient sample * rightCoefficient sample) *
          (leftResidual sample * rightResidual sample)) | scoreSigma] =ᵐ[
      sampleLaw]
      fun sample =>
        (leftCoefficient sample * rightCoefficient sample) *
          sampleLaw[(fun sample => leftResidual sample * rightResidual sample) |
            scoreSigma] sample := by
  have hcoefficientProduct :
      AEStronglyMeasurable[scoreSigma]
        (fun sample => leftCoefficient sample * rightCoefficient sample)
        sampleLaw :=
    hleft.mul hright
  exact
    condExp_mul_of_aestronglyMeasurable_left
      (m := scoreSigma) (μ := sampleLaw) hcoefficientProduct hproduct
      hresidualProduct

/--
Integral form of the conditional cross-moment bridge.  If `conditionalCross`
is the conditional residual cross moment, then the weighted residual
cross-product integral equals the corresponding score-space cross-moment
integral.
-/
theorem integral_scoreMeasurable_mul_residualProduct_eq_crossMoment
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (leftCoefficient rightCoefficient leftResidual rightResidual
      conditionalCross : Sample -> Real)
    (hleft :
      AEStronglyMeasurable[scoreSigma] leftCoefficient sampleLaw)
    (hright :
      AEStronglyMeasurable[scoreSigma] rightCoefficient sampleLaw)
    (hproduct :
      Integrable
        (fun sample =>
          (leftCoefficient sample * rightCoefficient sample) *
            (leftResidual sample * rightResidual sample)) sampleLaw)
    (hresidualProduct :
      Integrable (fun sample => leftResidual sample * rightResidual sample)
        sampleLaw)
    (hcross :
      sampleLaw[(fun sample => leftResidual sample * rightResidual sample) |
        scoreSigma] =ᵐ[sampleLaw] conditionalCross) :
    ∫ sample,
        (leftCoefficient sample * rightCoefficient sample) *
          (leftResidual sample * rightResidual sample) ∂sampleLaw =
      ∫ sample,
        (leftCoefficient sample * rightCoefficient sample) *
          conditionalCross sample ∂sampleLaw := by
  rw [← integral_condExp
    (m := scoreSigma) (m₀ := mSample) (μ := sampleLaw)
    (f := fun sample =>
      (leftCoefficient sample * rightCoefficient sample) *
        (leftResidual sample * rightResidual sample)) hsub]
  refine integral_congr_ae ?_
  exact
    (condExp_scoreMeasurable_mul_residualProduct_ae_eq
      (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
      leftCoefficient rightCoefficient leftResidual rightResidual hleft hright
      hproduct hresidualProduct).trans
      (hcross.mono fun sample hsample => by
        simp [hsample])

/--
If the conditional residual cross moment is zero, then every score-measurable
coefficient product has zero unconditional residual cross moment.
-/
theorem integral_scoreMeasurable_mul_residualProduct_eq_zero_of_condExp_zero
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (leftCoefficient rightCoefficient leftResidual rightResidual :
      Sample -> Real)
    (hleft :
      AEStronglyMeasurable[scoreSigma] leftCoefficient sampleLaw)
    (hright :
      AEStronglyMeasurable[scoreSigma] rightCoefficient sampleLaw)
    (hproduct :
      Integrable
        (fun sample =>
          (leftCoefficient sample * rightCoefficient sample) *
            (leftResidual sample * rightResidual sample)) sampleLaw)
    (hresidualProduct :
      Integrable (fun sample => leftResidual sample * rightResidual sample)
        sampleLaw)
    (hcrossZero :
      sampleLaw[(fun sample => leftResidual sample * rightResidual sample) |
        scoreSigma] =ᵐ[sampleLaw] 0) :
    ∫ sample,
        (leftCoefficient sample * rightCoefficient sample) *
          (leftResidual sample * rightResidual sample) ∂sampleLaw = 0 := by
  have h :=
    integral_scoreMeasurable_mul_residualProduct_eq_crossMoment
      (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
      hsub leftCoefficient rightCoefficient
      leftResidual rightResidual (fun _sample => (0 : Real)) hleft hright
      hproduct hresidualProduct hcrossZero
  simpa using h

end WDSM
end Matching
end StatInference
