import StatInference.Matching.WDSM.CoverageLimitAlgebra
import StatInference.Matching.WDSM.StudentizedLimitAlgebra

/-!
# Wald inference bridge for WDSM

This module names the final inference-layer interface without hiding the hard
probability input.  The studentized weak limit and variance consistency can be
proved by the existing Slutsky modules.  The remaining critical-value
calibration is still an explicit assumption: a theorem about the probability
of the absolute or two-sided studentized event.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open Filter
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
End-to-end studentized limit input for WDSM Wald inference.  This structure
keeps the proof obligations visible: scaled-statistic weak convergence,
variance consistency, nonzero limiting standard error, and measurability of
the inverse standard-error multiplier.
-/
structure StudentizedLimitInput
    (Index Sample LimitSample : Type*) [MeasurableSpace Sample]
    [MeasurableSpace LimitSample] (sampleLaw : Measure Sample)
    (limitLaw : Measure LimitSample) (l : Filter Index)
    [IsProbabilityMeasure sampleLaw] [IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated] where
  scaledStatistic : Index -> Sample -> Real
  varianceEstimate : Index -> Sample -> Real
  limit : LimitSample -> Real
  varianceLimit : Real
  scaled_tendsto :
    TendstoInDistribution scaledStatistic l limit
      (fun _index => sampleLaw) limitLaw
  variance_tendsto :
    TendstoInMeasure sampleLaw varianceEstimate l
      (fun _sample => varianceLimit)
  standardErrorLimit_ne_zero :
    standardError varianceLimit ≠ 0
  inverseStandardError_measurable :
    ∀ index,
      AEMeasurable
        (fun sample => (standardError (varianceEstimate index sample))⁻¹)
        sampleLaw

/-- The studentized limit input yields the studentized distributional limit. -/
theorem studentized_tendstoInDistribution_of_input
    (input :
      StudentizedLimitInput Index Sample LimitSample sampleLaw limitLaw l) :
    TendstoInDistribution
      (fun index sample =>
        input.scaledStatistic index sample *
          (standardError (input.varianceEstimate index sample))⁻¹)
      l
      (fun limitSample =>
        input.limit limitSample * (standardError input.varianceLimit)⁻¹)
      (fun _index => sampleLaw) limitLaw :=
  tendstoInDistribution_studentized_of_variance_consistency
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    input.scaledStatistic input.varianceEstimate input.limit
    input.varianceLimit input.scaled_tendsto input.variance_tendsto
    input.standardErrorLimit_ne_zero input.inverseStandardError_measurable

/--
Final real-valued Wald coverage input for an absolute-value critical region.
The field `absoluteStudentizedProbability_tendsto` is the remaining
critical-value calibration theorem to be proved from the studentized limiting
law.
-/
structure AbsoluteWaldCoverageInput
    (Index Sample : Type*) [MeasurableSpace Sample] (l : Filter Index) where
  sampleLawSeq : Index -> Measure Sample
  estimator : Index -> Sample -> Real
  standardError : Index -> Sample -> Real
  target : Index -> Real
  criticalValue : Index -> Real
  scale : Index -> Real
  coverageLimit : Real
  standardError_positive :
    ∀ᶠ index in l, ∀ sample, 0 < standardError index sample
  scale_positive : ∀ᶠ index in l, 0 < scale index
  absoluteStudentizedProbability_tendsto :
    Tendsto
      (fun index =>
        eventProbabilityReal (sampleLawSeq index)
          (fun sample =>
            |waldStudentized (estimator index sample) (target index)
              (standardError index sample) (scale index)| ≤
                criticalValue index)) l (nhds coverageLimit)

omit [l.IsCountablyGenerated] in
/-- Absolute critical-region calibration yields the real-valued Wald coverage limit. -/
theorem absoluteWaldCoverage_tendsto_of_input
    (input : AbsoluteWaldCoverageInput Index Sample l) :
    Tendsto
      (fun index =>
        eventProbabilityReal (input.sampleLawSeq index)
          (fun sample =>
            waldCovers (input.estimator index sample) (input.target index)
              (input.criticalValue index) (input.standardError index sample)
              (input.scale index))) l (nhds input.coverageLimit) :=
  tendsto_waldCoverageProbabilityReal_absStudentized_of_tendsto
    input.sampleLawSeq input.estimator input.standardError input.target
    input.criticalValue input.scale input.coverageLimit
    input.standardError_positive input.scale_positive
    input.absoluteStudentizedProbability_tendsto

/--
Final real-valued Wald coverage input for a two-sided critical region.  The
field `twoSidedStudentizedProbability_tendsto` is the remaining critical-value
calibration theorem to be proved from the studentized limiting law.
-/
structure TwoSidedWaldCoverageInput
    (Index Sample : Type*) [MeasurableSpace Sample] (l : Filter Index) where
  sampleLawSeq : Index -> Measure Sample
  estimator : Index -> Sample -> Real
  standardError : Index -> Sample -> Real
  target : Index -> Real
  criticalValue : Index -> Real
  scale : Index -> Real
  coverageLimit : Real
  standardError_positive :
    ∀ᶠ index in l, ∀ sample, 0 < standardError index sample
  scale_positive : ∀ᶠ index in l, 0 < scale index
  twoSidedStudentizedProbability_tendsto :
    Tendsto
      (fun index =>
        eventProbabilityReal (sampleLawSeq index)
          (fun sample =>
            -criticalValue index ≤
                waldStudentized (estimator index sample) (target index)
                  (standardError index sample) (scale index) ∧
              waldStudentized (estimator index sample) (target index)
                (standardError index sample) (scale index) ≤
                  criticalValue index)) l (nhds coverageLimit)

omit [l.IsCountablyGenerated] in
/-- Two-sided critical-region calibration yields the real-valued Wald coverage limit. -/
theorem twoSidedWaldCoverage_tendsto_of_input
    (input : TwoSidedWaldCoverageInput Index Sample l) :
    Tendsto
      (fun index =>
        eventProbabilityReal (input.sampleLawSeq index)
          (fun sample =>
            waldCovers (input.estimator index sample) (input.target index)
              (input.criticalValue index) (input.standardError index sample)
              (input.scale index))) l (nhds input.coverageLimit) :=
  tendsto_waldCoverageProbabilityReal_twoSidedStudentized_of_tendsto
    input.sampleLawSeq input.estimator input.standardError input.target
    input.criticalValue input.scale input.coverageLimit
    input.standardError_positive input.scale_positive
    input.twoSidedStudentizedProbability_tendsto

end WDSM
end Matching
end StatInference
