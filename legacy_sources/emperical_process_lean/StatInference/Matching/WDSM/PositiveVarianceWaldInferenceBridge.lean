import StatInference.Matching.WDSM.WaldInferenceBridge
import StatInference.Matching.WDSM.WaldStandardErrorPositivity

/-!
# Positive-variance Wald inference input

The generic Wald inference bridge originally asks directly for a nonzero
limiting standard error.  This module provides the reusable version used by
variance-limit arguments: a positive limiting variance is enough.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open scoped Topology

variable {Index Sample LimitSample : Type*}
variable [MeasurableSpace Sample] [MeasurableSpace LimitSample]
variable {sampleLaw : MeasureTheory.Measure Sample}
variable {limitLaw : MeasureTheory.Measure LimitSample}
variable [MeasureTheory.IsProbabilityMeasure sampleLaw]
variable [MeasureTheory.IsProbabilityMeasure limitLaw]
variable {l : Filter Index}
variable [l.IsCountablyGenerated]

/--
End-to-end studentized limit input with positivity stated at the variance
limit rather than the standard-error limit.
-/
structure PositiveVarianceStudentizedLimitInput
    (Index Sample LimitSample : Type*) [MeasurableSpace Sample]
    [MeasurableSpace LimitSample] (sampleLaw : Measure Sample)
    (limitLaw : Measure LimitSample) (l : Filter Index)
    [IsProbabilityMeasure sampleLaw] [IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated] where
  scaledStatistic : Index -> Sample -> Real
  varianceEstimate : Index -> Sample -> Real
  limit : LimitSample -> Real
  varianceLimit : Real
  varianceLimit_pos : 0 < varianceLimit
  scaled_tendsto :
    TendstoInDistribution scaledStatistic l limit
      (fun _index => sampleLaw) limitLaw
  variance_tendsto :
    TendstoInMeasure sampleLaw varianceEstimate l
      (fun _sample => varianceLimit)
  inverseStandardError_measurable :
    ∀ index,
      AEMeasurable
        (fun sample => (standardError (varianceEstimate index sample))⁻¹)
        sampleLaw

/-- Convert positive-variance studentized input to the generic Wald input. -/
noncomputable def studentizedLimitInput_of_positiveVariance
    (input :
      PositiveVarianceStudentizedLimitInput Index Sample LimitSample
        sampleLaw limitLaw l) :
    StudentizedLimitInput Index Sample LimitSample sampleLaw limitLaw l where
  scaledStatistic := input.scaledStatistic
  varianceEstimate := input.varianceEstimate
  limit := input.limit
  varianceLimit := input.varianceLimit
  scaled_tendsto := input.scaled_tendsto
  variance_tendsto := input.variance_tendsto
  standardErrorLimit_ne_zero :=
    standardError_ne_zero_of_variance_pos input.varianceLimit
      input.varianceLimit_pos
  inverseStandardError_measurable := input.inverseStandardError_measurable

/--
Positive limiting variance, variance consistency, and a scaled weak limit give
the generic studentized weak limit.
-/
theorem studentized_tendstoInDistribution_of_positiveVarianceLimitInput
    (input :
      PositiveVarianceStudentizedLimitInput Index Sample LimitSample
        sampleLaw limitLaw l) :
    TendstoInDistribution
      (fun index sample =>
        input.scaledStatistic index sample *
          (standardError (input.varianceEstimate index sample))⁻¹)
      l
      (fun limitSample =>
        input.limit limitSample * (standardError input.varianceLimit)⁻¹)
      (fun _index => sampleLaw) limitLaw := by
  simpa [studentizedLimitInput_of_positiveVariance] using
    studentized_tendstoInDistribution_of_input
      (studentizedLimitInput_of_positiveVariance input)

/--
Direct positive-variance studentized weak-limit theorem.  This is equivalent
to `studentized_tendstoInDistribution_of_positiveVarianceLimitInput`, but avoids
forcing callers to build an input structure when the ingredients are already
available.
-/
theorem studentized_tendstoInDistribution_of_positiveVariance
    (scaledStatistic varianceEstimate : Index -> Sample -> Real)
    (limit : LimitSample -> Real) (varianceLimit : Real)
    (hvarianceLimit_pos : 0 < varianceLimit)
    (hscaled :
      TendstoInDistribution scaledStatistic l limit
        (fun _index => sampleLaw) limitLaw)
    (hvariance :
      TendstoInMeasure sampleLaw varianceEstimate l
        (fun _sample => varianceLimit))
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample => (standardError (varianceEstimate index sample))⁻¹)
          sampleLaw) :
    TendstoInDistribution
      (fun index sample =>
        scaledStatistic index sample *
          (standardError (varianceEstimate index sample))⁻¹)
      l
      (fun limitSample =>
        limit limitSample * (standardError varianceLimit)⁻¹)
      (fun _index => sampleLaw) limitLaw :=
  tendstoInDistribution_studentized_of_variance_consistency_pos_limit
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    scaledStatistic varianceEstimate limit varianceLimit hscaled hvariance
    hvarianceLimit_pos hinverse_meas

end WDSM
end Matching
end StatInference
