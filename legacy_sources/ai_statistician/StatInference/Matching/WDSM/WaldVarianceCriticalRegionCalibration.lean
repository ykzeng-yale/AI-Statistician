import StatInference.Matching.WDSM.WaldCriticalRegionCalibration
import StatInference.Matching.WDSM.WaldStandardErrorPositivity

/-!
# Variance-estimate Wald critical-region calibration

The variance-based Wald inputs package the standard error as
`standardError varianceEstimate`.  This module lifts the absolute/two-sided
critical-region calibration algebra to those variance-based inputs directly.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open Filter
open scoped Topology

variable {Index Sample : Type*} [MeasurableSpace Sample] {l : Filter Index}

/-- Absolute calibration implies two-sided calibration for variance-based Wald inputs. -/
theorem tendsto_twoSidedVarianceStudentizedProbabilityReal_of_abs
    (sampleLaw : Index -> Measure Sample)
    (estimator varianceEstimate : Index -> Sample -> Real)
    (target criticalValue scale : Index -> Real)
    (coverageLimit : Real)
    (habs :
      Tendsto
        (fun index =>
          eventProbabilityReal (sampleLaw index)
            (fun sample =>
              |waldStudentized (estimator index sample) (target index)
                (standardError (varianceEstimate index sample))
                (scale index)| ≤ criticalValue index)) l
        (nhds coverageLimit)) :
    Tendsto
      (fun index =>
        eventProbabilityReal (sampleLaw index)
          (fun sample =>
            -criticalValue index ≤
                waldStudentized (estimator index sample) (target index)
                  (standardError (varianceEstimate index sample))
                  (scale index) ∧
              waldStudentized (estimator index sample) (target index)
                (standardError (varianceEstimate index sample))
                (scale index) ≤ criticalValue index)) l
      (nhds coverageLimit) :=
  tendsto_twoSidedStudentizedProbabilityReal_of_abs
    sampleLaw estimator
    (fun index sample => standardError (varianceEstimate index sample))
    target criticalValue scale coverageLimit habs

/-- Two-sided calibration implies absolute calibration for variance-based Wald inputs. -/
theorem tendsto_absVarianceStudentizedProbabilityReal_of_twoSided
    (sampleLaw : Index -> Measure Sample)
    (estimator varianceEstimate : Index -> Sample -> Real)
    (target criticalValue scale : Index -> Real)
    (coverageLimit : Real)
    (htwoSided :
      Tendsto
        (fun index =>
          eventProbabilityReal (sampleLaw index)
            (fun sample =>
              -criticalValue index ≤
                  waldStudentized (estimator index sample) (target index)
                    (standardError (varianceEstimate index sample))
                    (scale index) ∧
                waldStudentized (estimator index sample) (target index)
                  (standardError (varianceEstimate index sample))
                  (scale index) ≤ criticalValue index)) l
        (nhds coverageLimit)) :
    Tendsto
      (fun index =>
        eventProbabilityReal (sampleLaw index)
          (fun sample =>
            |waldStudentized (estimator index sample) (target index)
              (standardError (varianceEstimate index sample))
              (scale index)| ≤ criticalValue index)) l
      (nhds coverageLimit) :=
  tendsto_absStudentizedProbabilityReal_of_twoSided
    sampleLaw estimator
    (fun index sample => standardError (varianceEstimate index sample))
    target criticalValue scale coverageLimit htwoSided

/-- Build a variance-based two-sided Wald coverage input from an absolute-region input. -/
def twoSidedWaldCoverageVarianceInput_of_absolute
    (input : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    TwoSidedWaldCoverageVarianceInput Index Sample l where
  sampleLawSeq := input.sampleLawSeq
  estimator := input.estimator
  varianceEstimate := input.varianceEstimate
  target := input.target
  criticalValue := input.criticalValue
  scale := input.scale
  coverageLimit := input.coverageLimit
  variance_positive := input.variance_positive
  scale_positive := input.scale_positive
  twoSidedStudentizedProbability_tendsto :=
    tendsto_twoSidedVarianceStudentizedProbabilityReal_of_abs
      input.sampleLawSeq input.estimator input.varianceEstimate input.target
      input.criticalValue input.scale input.coverageLimit
      input.absoluteStudentizedProbability_tendsto

/-- Build a variance-based absolute Wald coverage input from a two-sided-region input. -/
def absoluteWaldCoverageVarianceInput_of_twoSided
    (input : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    AbsoluteWaldCoverageVarianceInput Index Sample l where
  sampleLawSeq := input.sampleLawSeq
  estimator := input.estimator
  varianceEstimate := input.varianceEstimate
  target := input.target
  criticalValue := input.criticalValue
  scale := input.scale
  coverageLimit := input.coverageLimit
  variance_positive := input.variance_positive
  scale_positive := input.scale_positive
  absoluteStudentizedProbability_tendsto :=
    tendsto_absVarianceStudentizedProbabilityReal_of_twoSided
      input.sampleLawSeq input.estimator input.varianceEstimate input.target
      input.criticalValue input.scale input.coverageLimit
      input.twoSidedStudentizedProbability_tendsto

/-- Absolute variance-based calibration also gives the two-sided Wald coverage limit. -/
theorem twoSidedVarianceWaldCoverage_tendsto_of_absolute_input
    (input : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    Tendsto
      (fun index =>
        eventProbabilityReal (input.sampleLawSeq index)
          (fun sample =>
            waldCovers (input.estimator index sample) (input.target index)
              (input.criticalValue index)
              (standardError (input.varianceEstimate index sample))
              (input.scale index))) l (nhds input.coverageLimit) :=
  twoSidedWaldCoverage_tendsto_of_variance_input
    (twoSidedWaldCoverageVarianceInput_of_absolute input)

/-- Two-sided variance-based calibration also gives the absolute Wald coverage limit. -/
theorem absoluteVarianceWaldCoverage_tendsto_of_twoSided_input
    (input : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    Tendsto
      (fun index =>
        eventProbabilityReal (input.sampleLawSeq index)
          (fun sample =>
            waldCovers (input.estimator index sample) (input.target index)
              (input.criticalValue index)
              (standardError (input.varianceEstimate index sample))
              (input.scale index))) l (nhds input.coverageLimit) :=
  absoluteWaldCoverage_tendsto_of_variance_input
    (absoluteWaldCoverageVarianceInput_of_twoSided input)

end WDSM
end Matching
end StatInference
