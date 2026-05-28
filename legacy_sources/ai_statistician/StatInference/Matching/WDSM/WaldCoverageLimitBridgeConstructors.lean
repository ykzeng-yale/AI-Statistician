import StatInference.Matching.WDSM.WaldVarianceCriticalRegionCalibration

/-!
# Constructors for Wald coverage-limit bridges

The generic `WaldCoverageLimitBridge` records only an eventual equality between
coverage probabilities and calibrated studentized-event probabilities.  This
module constructs that bridge from the standard absolute/two-sided Wald inputs,
including the variance-estimate versions used by the positive-variance WDSM
pipeline.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open Filter
open scoped Topology

variable {Index Sample : Type*} [MeasurableSpace Sample] {l : Filter Index}

/-- Build the generic coverage-limit bridge from an absolute Wald input. -/
noncomputable def waldCoverageLimitBridge_of_absoluteWaldCoverageInput
    (input : AbsoluteWaldCoverageInput Index Sample l) :
    WaldCoverageLimitBridge Index l where
  waldCoverageProbability := fun index =>
    eventProbabilityReal (input.sampleLawSeq index)
      (fun sample =>
        waldCovers (input.estimator index sample) (input.target index)
          (input.criticalValue index) (input.standardError index sample)
          (input.scale index))
  studentizedEventProbability := fun index =>
    eventProbabilityReal (input.sampleLawSeq index)
      (fun sample =>
        |waldStudentized (input.estimator index sample) (input.target index)
          (input.standardError index sample) (input.scale index)| ≤
            input.criticalValue index)
  coverageLimit := input.coverageLimit
  probabilities_agree :=
    eventuallyEq_waldCoverageProbabilityReal_absStudentized input.sampleLawSeq
      input.estimator input.standardError input.target input.criticalValue
      input.scale input.standardError_positive input.scale_positive
  studentizedEventProbability_tendsto :=
    input.absoluteStudentizedProbability_tendsto

/-- Build the generic coverage-limit bridge from a two-sided Wald input. -/
noncomputable def waldCoverageLimitBridge_of_twoSidedWaldCoverageInput
    (input : TwoSidedWaldCoverageInput Index Sample l) :
    WaldCoverageLimitBridge Index l where
  waldCoverageProbability := fun index =>
    eventProbabilityReal (input.sampleLawSeq index)
      (fun sample =>
        waldCovers (input.estimator index sample) (input.target index)
          (input.criticalValue index) (input.standardError index sample)
          (input.scale index))
  studentizedEventProbability := fun index =>
    eventProbabilityReal (input.sampleLawSeq index)
      (fun sample =>
        -input.criticalValue index ≤
            waldStudentized (input.estimator index sample)
              (input.target index) (input.standardError index sample)
              (input.scale index) ∧
          waldStudentized (input.estimator index sample)
            (input.target index) (input.standardError index sample)
            (input.scale index) ≤ input.criticalValue index)
  coverageLimit := input.coverageLimit
  probabilities_agree :=
    eventuallyEq_waldCoverageProbabilityReal_twoSidedStudentized
      input.sampleLawSeq input.estimator input.standardError input.target
      input.criticalValue input.scale input.standardError_positive
      input.scale_positive
  studentizedEventProbability_tendsto :=
    input.twoSidedStudentizedProbability_tendsto

/--
Build the generic coverage-limit bridge from a variance-estimate absolute Wald
input, after converting variance positivity to standard-error positivity.
-/
noncomputable def waldCoverageLimitBridge_of_absoluteWaldCoverageVarianceInput
    (input : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    WaldCoverageLimitBridge Index l :=
  waldCoverageLimitBridge_of_absoluteWaldCoverageInput
    (absoluteWaldCoverageInput_of_variance input)

/--
Build the generic coverage-limit bridge from a variance-estimate two-sided Wald
input, after converting variance positivity to standard-error positivity.
-/
noncomputable def waldCoverageLimitBridge_of_twoSidedWaldCoverageVarianceInput
    (input : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    WaldCoverageLimitBridge Index l :=
  waldCoverageLimitBridge_of_twoSidedWaldCoverageInput
    (twoSidedWaldCoverageInput_of_variance input)

end WDSM
end Matching
end StatInference
