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
If an outcome agrees a.e. with its score version, then the score-sigma
conditional second moment of the centered residual is zero.
-/
theorem condExp_centeredResidual_sq_ae_eq_zero_of_ae_scoreVersion
    (outcome scoreVersion : Sample -> Real)
    (hae : outcome =ᵐ[sampleLaw] scoreVersion) :
    sampleLaw[(fun sample =>
        (outcome sample - scoreVersion sample) *
          (outcome sample - scoreVersion sample)) | scoreSigma] =ᵐ[
      sampleLaw] 0 := by
  have hsqZero :
      (fun sample =>
        (outcome sample - scoreVersion sample) *
          (outcome sample - scoreVersion sample)) =ᵐ[sampleLaw]
        (fun _sample => (0 : Real)) := by
    filter_upwards [hae] with sample hsample
    simp [hsample]
  exact
    (condExp_congr_ae (m := scoreSigma) (μ := sampleLaw) hsqZero).trans
      (by
        change sampleLaw[(0 : Sample -> Real) | scoreSigma] =ᵐ[
          sampleLaw] (0 : Sample -> Real)
        rw [condExp_zero])

/--
If a residual is zero almost everywhere, then the conditional expectation of
any squared score-weighted residual is zero.  This direct route avoids carrying
the quadratic-variation integrability hypotheses when the residual itself
vanishes a.e.
-/
theorem condExp_scoreMeasurable_sq_mul_residual_sq_ae_eq_zero_of_residual_ae_zero
    (coefficient residual : Sample -> Real)
    (hresidualZero : residual =ᵐ[sampleLaw] 0) :
    sampleLaw[(fun sample =>
        (coefficient sample * coefficient sample) *
          (residual sample * residual sample)) | scoreSigma] =ᵐ[
      sampleLaw] 0 := by
  have hproductZero :
      (fun sample =>
        (coefficient sample * coefficient sample) *
          (residual sample * residual sample)) =ᵐ[sampleLaw]
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
Centered-residual specialization of the direct conditional-expectation zero
bridge for squared score-weighted residuals.
-/
theorem
    condExp_scoreMeasurable_sq_mul_centeredResidual_sq_ae_eq_zero_of_ae_scoreVersion
    (coefficient outcome scoreVersion : Sample -> Real)
    (hae : outcome =ᵐ[sampleLaw] scoreVersion) :
    sampleLaw[(fun sample =>
        (coefficient sample * coefficient sample) *
          ((outcome sample - scoreVersion sample) *
            (outcome sample - scoreVersion sample))) | scoreSigma] =ᵐ[
      sampleLaw] 0 := by
  exact
    condExp_scoreMeasurable_sq_mul_residual_sq_ae_eq_zero_of_residual_ae_zero
      (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
      coefficient (fun sample => outcome sample - scoreVersion sample)
      (by
        filter_upwards [hae] with sample hsample
        simp [hsample])

/--
If a residual is zero almost everywhere, then every squared weighted residual
has zero integral.  No score-measurability or conditional-variance route is
needed for this degenerate residual case.
-/
theorem integral_scoreMeasurable_sq_mul_residual_sq_eq_zero_of_residual_ae_zero
    (coefficient residual : Sample -> Real)
    (hresidualZero : residual =ᵐ[sampleLaw] 0) :
    ∫ sample,
        (coefficient sample * coefficient sample) *
          (residual sample * residual sample) ∂sampleLaw = 0 := by
  refine integral_eq_zero_of_ae ?_
  filter_upwards [hresidualZero] with sample hsample
  simp [hsample]

/--
Centered-residual specialization of the direct zero integral for squared
weighted residuals.
-/
theorem
    integral_scoreMeasurable_sq_mul_centeredResidual_sq_eq_zero_of_direct_ae_scoreVersion
    (coefficient outcome scoreVersion : Sample -> Real)
    (hae : outcome =ᵐ[sampleLaw] scoreVersion) :
    ∫ sample,
        (coefficient sample * coefficient sample) *
          ((outcome sample - scoreVersion sample) *
            (outcome sample - scoreVersion sample)) ∂sampleLaw = 0 := by
  exact
    integral_scoreMeasurable_sq_mul_residual_sq_eq_zero_of_residual_ae_zero
      (mSample := mSample) (sampleLaw := sampleLaw)
      coefficient (fun sample => outcome sample - scoreVersion sample)
      (by
        filter_upwards [hae] with sample hsample
        simp [hsample])

/--
If an outcome agrees a.e. with its score version, every score-measurable
squared coefficient has zero weighted centered-residual second moment.
-/
theorem integral_scoreMeasurable_sq_mul_centeredResidual_sq_eq_zero_of_ae_scoreVersion
    (hsub : scoreSigma ≤ mSample) [SigmaFinite (sampleLaw.trim hsub)]
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
            (outcome sample - scoreVersion sample)) sampleLaw)
    (hae : outcome =ᵐ[sampleLaw] scoreVersion) :
    ∫ sample,
        (coefficient sample * coefficient sample) *
          ((outcome sample - scoreVersion sample) *
            (outcome sample - scoreVersion sample)) ∂sampleLaw = 0 := by
  have h :=
    integral_scoreMeasurable_sq_mul_residual_sq_eq_variance
      (mSample := mSample) (scoreSigma := scoreSigma) (sampleLaw := sampleLaw)
      hsub coefficient (fun sample => outcome sample - scoreVersion sample)
      (fun _sample => (0 : Real)) hcoefficient hproduct hresidualSq
      (condExp_centeredResidual_sq_ae_eq_zero_of_ae_scoreVersion
        (mSample := mSample) (scoreSigma := scoreSigma)
        (sampleLaw := sampleLaw) outcome scoreVersion hae)
  simpa using h

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
