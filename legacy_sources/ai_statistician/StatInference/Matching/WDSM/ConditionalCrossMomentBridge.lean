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

/--
If the left outcome agrees a.e. with its score version, then the
score-sigma conditional residual cross moment is zero.
-/
theorem condExp_leftCenteredResidualProduct_ae_eq_zero_of_ae_scoreVersion
    (leftOutcome leftScoreVersion rightResidual : Sample -> Real)
    (hae : leftOutcome =ᵐ[sampleLaw] leftScoreVersion) :
    sampleLaw[(fun sample =>
        (leftOutcome sample - leftScoreVersion sample) *
          rightResidual sample) | scoreSigma] =ᵐ[sampleLaw] 0 := by
  have hproductZero :
      (fun sample =>
        (leftOutcome sample - leftScoreVersion sample) *
          rightResidual sample) =ᵐ[sampleLaw]
        (fun _sample => (0 : Real)) := by
    filter_upwards [hae] with sample hsample
    simp [hsample]
  exact
    (condExp_congr_ae (m := scoreSigma) (μ := sampleLaw)
      hproductZero).trans
      (by
        change sampleLaw[(0 : Sample -> Real) | scoreSigma] =ᵐ[
          sampleLaw] (0 : Sample -> Real)
        rw [condExp_zero])

/--
If the right outcome agrees a.e. with its score version, then the
score-sigma conditional residual cross moment is zero.
-/
theorem condExp_rightCenteredResidualProduct_ae_eq_zero_of_ae_scoreVersion
    (leftResidual rightOutcome rightScoreVersion : Sample -> Real)
    (hae : rightOutcome =ᵐ[sampleLaw] rightScoreVersion) :
    sampleLaw[(fun sample =>
        leftResidual sample *
          (rightOutcome sample - rightScoreVersion sample)) | scoreSigma]
      =ᵐ[sampleLaw] 0 := by
  have hproductZero :
      (fun sample =>
        leftResidual sample *
          (rightOutcome sample - rightScoreVersion sample)) =ᵐ[sampleLaw]
        (fun _sample => (0 : Real)) := by
    filter_upwards [hae] with sample hsample
    simp [hsample]
  exact
    (condExp_congr_ae (m := scoreSigma) (μ := sampleLaw)
      hproductZero).trans
      (by
        change sampleLaw[(0 : Sample -> Real) | scoreSigma] =ᵐ[
          sampleLaw] (0 : Sample -> Real)
        rw [condExp_zero])

/--
If the left outcome agrees a.e. with its score version, then every pair of
score-measurable coefficients has zero weighted residual cross moment.
-/
theorem integral_scoreMeasurable_mul_leftCenteredResidualProduct_eq_zero_of_ae_scoreVersion
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (leftCoefficient rightCoefficient leftOutcome leftScoreVersion
      rightResidual : Sample -> Real)
    (hleft :
      AEStronglyMeasurable[scoreSigma] leftCoefficient sampleLaw)
    (hright :
      AEStronglyMeasurable[scoreSigma] rightCoefficient sampleLaw)
    (hproduct :
      Integrable
        (fun sample =>
          (leftCoefficient sample * rightCoefficient sample) *
            ((leftOutcome sample - leftScoreVersion sample) *
              rightResidual sample)) sampleLaw)
    (hresidualProduct :
      Integrable
        (fun sample =>
          (leftOutcome sample - leftScoreVersion sample) *
            rightResidual sample) sampleLaw)
    (hae : leftOutcome =ᵐ[sampleLaw] leftScoreVersion) :
    ∫ sample,
        (leftCoefficient sample * rightCoefficient sample) *
          ((leftOutcome sample - leftScoreVersion sample) *
            rightResidual sample) ∂sampleLaw = 0 := by
  exact
    integral_scoreMeasurable_mul_residualProduct_eq_zero_of_condExp_zero
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub leftCoefficient rightCoefficient
      (fun sample => leftOutcome sample - leftScoreVersion sample)
      rightResidual hleft hright hproduct hresidualProduct
      (condExp_leftCenteredResidualProduct_ae_eq_zero_of_ae_scoreVersion
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) leftOutcome leftScoreVersion rightResidual hae)

/--
If the right outcome agrees a.e. with its score version, then every pair of
score-measurable coefficients has zero weighted residual cross moment.
-/
theorem integral_scoreMeasurable_mul_rightCenteredResidualProduct_eq_zero_of_ae_scoreVersion
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
    (leftCoefficient rightCoefficient leftResidual rightOutcome
      rightScoreVersion : Sample -> Real)
    (hleft :
      AEStronglyMeasurable[scoreSigma] leftCoefficient sampleLaw)
    (hright :
      AEStronglyMeasurable[scoreSigma] rightCoefficient sampleLaw)
    (hproduct :
      Integrable
        (fun sample =>
          (leftCoefficient sample * rightCoefficient sample) *
            (leftResidual sample *
              (rightOutcome sample - rightScoreVersion sample))) sampleLaw)
    (hresidualProduct :
      Integrable
        (fun sample =>
          leftResidual sample *
            (rightOutcome sample - rightScoreVersion sample)) sampleLaw)
    (hae : rightOutcome =ᵐ[sampleLaw] rightScoreVersion) :
    ∫ sample,
        (leftCoefficient sample * rightCoefficient sample) *
          (leftResidual sample *
            (rightOutcome sample - rightScoreVersion sample)) ∂sampleLaw =
      0 := by
  exact
    integral_scoreMeasurable_mul_residualProduct_eq_zero_of_condExp_zero
      (mSample := mSample) (scoreSigma := scoreSigma)
      (sampleLaw := sampleLaw) hsub leftCoefficient rightCoefficient
      leftResidual
      (fun sample => rightOutcome sample - rightScoreVersion sample)
      hleft hright hproduct hresidualProduct
      (condExp_rightCenteredResidualProduct_ae_eq_zero_of_ae_scoreVersion
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) leftResidual rightOutcome rightScoreVersion hae)

end WDSM
end Matching
end StatInference
