import StatInference.Matching.WDSM.WaldInferenceBridge

/-!
# Absolute and two-sided Wald critical-region calibration

This module proves that the absolute studentized critical region and the
two-sided studentized critical region define the same event-probability
sequence.  Thus later WDSM probability work only needs to prove one
critical-value calibration form.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open Filter
open scoped Topology

variable {Index Sample : Type*} [MeasurableSpace Sample] {l : Filter Index}

/-- The absolute and two-sided studentized critical regions are equivalent. -/
theorem absStudentized_event_iff_twoSided
    (estimator target criticalValue standardError scale : Real) :
    |waldStudentized estimator target standardError scale| ≤ criticalValue ↔
      -criticalValue ≤ waldStudentized estimator target standardError scale ∧
        waldStudentized estimator target standardError scale ≤ criticalValue := by
  rw [abs_le]

/-- Absolute and two-sided studentized events have equal `ENNReal` probabilities. -/
theorem absStudentizedEventProbability_eq_twoSidedStudentizedEventProbability
    (sampleLaw : Measure Sample)
    (estimator standardError : Sample -> Real)
    (target criticalValue scale : Real) :
    eventProbability sampleLaw
        (fun sample =>
          |waldStudentized (estimator sample) target (standardError sample)
            scale| ≤ criticalValue) =
      eventProbability sampleLaw
        (fun sample =>
          -criticalValue ≤
              waldStudentized (estimator sample) target
                (standardError sample) scale ∧
            waldStudentized (estimator sample) target
              (standardError sample) scale ≤ criticalValue) :=
  eventProbability_eq_of_forall_iff sampleLaw
    (fun sample =>
      absStudentized_event_iff_twoSided
        (estimator sample) target criticalValue (standardError sample) scale)

/-- Absolute and two-sided studentized events have equal real-valued probabilities. -/
theorem absStudentizedEventProbabilityReal_eq_twoSidedStudentizedEventProbabilityReal
    (sampleLaw : Measure Sample)
    (estimator standardError : Sample -> Real)
    (target criticalValue scale : Real) :
    eventProbabilityReal sampleLaw
        (fun sample =>
          |waldStudentized (estimator sample) target (standardError sample)
            scale| ≤ criticalValue) =
      eventProbabilityReal sampleLaw
        (fun sample =>
          -criticalValue ≤
              waldStudentized (estimator sample) target
                (standardError sample) scale ∧
            waldStudentized (estimator sample) target
              (standardError sample) scale ≤ criticalValue) :=
  eventProbabilityReal_eq_of_forall_iff sampleLaw
    (fun sample =>
      absStudentized_event_iff_twoSided
        (estimator sample) target criticalValue (standardError sample) scale)

/-- Equality of the absolute and two-sided real-valued calibration sequences. -/
theorem absStudentizedProbabilityReal_seq_eq_twoSided
    (sampleLaw : Index -> Measure Sample)
    (estimator standardError : Index -> Sample -> Real)
    (target criticalValue scale : Index -> Real) :
    (fun index =>
      eventProbabilityReal (sampleLaw index)
        (fun sample =>
          |waldStudentized (estimator index sample) (target index)
            (standardError index sample) (scale index)| ≤
              criticalValue index)) =
      (fun index =>
        eventProbabilityReal (sampleLaw index)
          (fun sample =>
            -criticalValue index ≤
                waldStudentized (estimator index sample) (target index)
                  (standardError index sample) (scale index) ∧
              waldStudentized (estimator index sample) (target index)
                (standardError index sample) (scale index) ≤
                  criticalValue index)) := by
  funext index
  exact absStudentizedEventProbabilityReal_eq_twoSidedStudentizedEventProbabilityReal
    (sampleLaw index) (estimator index) (standardError index) (target index)
    (criticalValue index) (scale index)

/-- Absolute calibration implies two-sided calibration for the same critical values. -/
theorem tendsto_twoSidedStudentizedProbabilityReal_of_abs
    (sampleLaw : Index -> Measure Sample)
    (estimator standardError : Index -> Sample -> Real)
    (target criticalValue scale : Index -> Real)
    (coverageLimit : Real)
    (habs :
      Tendsto
        (fun index =>
          eventProbabilityReal (sampleLaw index)
            (fun sample =>
              |waldStudentized (estimator index sample) (target index)
                (standardError index sample) (scale index)| ≤
                  criticalValue index)) l (nhds coverageLimit)) :
    Tendsto
      (fun index =>
        eventProbabilityReal (sampleLaw index)
          (fun sample =>
            -criticalValue index ≤
                waldStudentized (estimator index sample) (target index)
                  (standardError index sample) (scale index) ∧
              waldStudentized (estimator index sample) (target index)
                (standardError index sample) (scale index) ≤
                  criticalValue index)) l (nhds coverageLimit) := by
  rw [← absStudentizedProbabilityReal_seq_eq_twoSided
    sampleLaw estimator standardError target criticalValue scale]
  exact habs

/-- Two-sided calibration implies absolute calibration for the same critical values. -/
theorem tendsto_absStudentizedProbabilityReal_of_twoSided
    (sampleLaw : Index -> Measure Sample)
    (estimator standardError : Index -> Sample -> Real)
    (target criticalValue scale : Index -> Real)
    (coverageLimit : Real)
    (htwoSided :
      Tendsto
        (fun index =>
          eventProbabilityReal (sampleLaw index)
            (fun sample =>
              -criticalValue index ≤
                  waldStudentized (estimator index sample) (target index)
                    (standardError index sample) (scale index) ∧
                waldStudentized (estimator index sample) (target index)
                  (standardError index sample) (scale index) ≤
                    criticalValue index)) l (nhds coverageLimit)) :
    Tendsto
      (fun index =>
        eventProbabilityReal (sampleLaw index)
          (fun sample =>
            |waldStudentized (estimator index sample) (target index)
              (standardError index sample) (scale index)| ≤
                criticalValue index)) l (nhds coverageLimit) := by
  rw [absStudentizedProbabilityReal_seq_eq_twoSided
    sampleLaw estimator standardError target criticalValue scale]
  exact htwoSided

/-- Build a two-sided Wald coverage input from an absolute-region input. -/
def twoSidedWaldCoverageInput_of_absolute
    (input : AbsoluteWaldCoverageInput Index Sample l) :
    TwoSidedWaldCoverageInput Index Sample l where
  sampleLawSeq := input.sampleLawSeq
  estimator := input.estimator
  standardError := input.standardError
  target := input.target
  criticalValue := input.criticalValue
  scale := input.scale
  coverageLimit := input.coverageLimit
  standardError_positive := input.standardError_positive
  scale_positive := input.scale_positive
  twoSidedStudentizedProbability_tendsto :=
    tendsto_twoSidedStudentizedProbabilityReal_of_abs
      input.sampleLawSeq input.estimator input.standardError input.target
      input.criticalValue input.scale input.coverageLimit
      input.absoluteStudentizedProbability_tendsto

/-- Build an absolute Wald coverage input from a two-sided-region input. -/
def absoluteWaldCoverageInput_of_twoSided
    (input : TwoSidedWaldCoverageInput Index Sample l) :
    AbsoluteWaldCoverageInput Index Sample l where
  sampleLawSeq := input.sampleLawSeq
  estimator := input.estimator
  standardError := input.standardError
  target := input.target
  criticalValue := input.criticalValue
  scale := input.scale
  coverageLimit := input.coverageLimit
  standardError_positive := input.standardError_positive
  scale_positive := input.scale_positive
  absoluteStudentizedProbability_tendsto :=
    tendsto_absStudentizedProbabilityReal_of_twoSided
      input.sampleLawSeq input.estimator input.standardError input.target
      input.criticalValue input.scale input.coverageLimit
      input.twoSidedStudentizedProbability_tendsto

/-- Absolute-region calibration also gives the two-sided Wald coverage limit. -/
theorem twoSidedWaldCoverage_tendsto_of_absolute_input
    (input : AbsoluteWaldCoverageInput Index Sample l) :
    Tendsto
      (fun index =>
        eventProbabilityReal (input.sampleLawSeq index)
          (fun sample =>
            waldCovers (input.estimator index sample) (input.target index)
              (input.criticalValue index) (input.standardError index sample)
              (input.scale index))) l (nhds input.coverageLimit) :=
  twoSidedWaldCoverage_tendsto_of_input
    (twoSidedWaldCoverageInput_of_absolute input)

/-- Two-sided-region calibration also gives the absolute Wald coverage limit. -/
theorem absoluteWaldCoverage_tendsto_of_twoSided_input
    (input : TwoSidedWaldCoverageInput Index Sample l) :
    Tendsto
      (fun index =>
        eventProbabilityReal (input.sampleLawSeq index)
          (fun sample =>
            waldCovers (input.estimator index sample) (input.target index)
              (input.criticalValue index) (input.standardError index sample)
              (input.scale index))) l (nhds input.coverageLimit) :=
  absoluteWaldCoverage_tendsto_of_input
    (absoluteWaldCoverageInput_of_twoSided input)

end WDSM
end Matching
end StatInference
