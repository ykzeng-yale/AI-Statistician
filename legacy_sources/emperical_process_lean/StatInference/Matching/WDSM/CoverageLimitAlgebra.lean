import StatInference.Matching.WDSM.WaldIntervalAlgebra

/-!
# Coverage-limit algebra for WDSM Wald inference

The hard probability work for WDSM confidence intervals is still the
studentized weak limit and critical-value calibration.  This module records
the exact algebraic transfer that remains after those inputs are available:
event equivalence gives equal event indicators, and eventually equal coverage
and studentized-event probability sequences have the same limit.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open Filter

/-- Indicator of a proposition as a real-valued event variable. -/
def eventIndicator (event : Prop) [Decidable event] : Real :=
  if event then 1 else 0

/-- Probability, as an `ENNReal`, of an event in a sample space. -/
def eventProbability
    {Sample : Type*} [MeasurableSpace Sample]
    (sampleLaw : Measure Sample) (event : Sample -> Prop) : ENNReal :=
  sampleLaw {sample | event sample}

/-- Real-valued probability of an event in a sample space. -/
noncomputable def eventProbabilityReal
    {Sample : Type*} [MeasurableSpace Sample]
    (sampleLaw : Measure Sample) (event : Sample -> Prop) : Real :=
  sampleLaw.real {sample | event sample}

/-- Logically equivalent events have equal real-valued indicators. -/
theorem eventIndicator_eq_of_iff
    {first second : Prop} [Decidable first] [Decidable second]
    (hequiv : first ↔ second) :
    eventIndicator first = eventIndicator second := by
  unfold eventIndicator
  by_cases hfirst : first
  · have hsecond : second := hequiv.mp hfirst
    simp [hfirst, hsecond]
  · have hsecond : ¬ second := fun h => hfirst (hequiv.mpr h)
    simp [hfirst, hsecond]

/-- Pointwise equivalent events determine equal event sets. -/
theorem eventSet_eq_of_forall_iff
    {Sample : Type*} {first second : Sample -> Prop}
    (hequiv : ∀ sample, first sample ↔ second sample) :
    {sample | first sample} = {sample | second sample} := by
  ext sample
  exact hequiv sample

/-- Pointwise equivalent events have equal event probabilities. -/
theorem eventProbability_eq_of_forall_iff
    {Sample : Type*} [MeasurableSpace Sample]
    (sampleLaw : Measure Sample) {first second : Sample -> Prop}
    (hequiv : ∀ sample, first sample ↔ second sample) :
    eventProbability sampleLaw first = eventProbability sampleLaw second := by
  unfold eventProbability
  rw [eventSet_eq_of_forall_iff hequiv]

/-- Pointwise equivalent events have equal real-valued event probabilities. -/
theorem eventProbabilityReal_eq_of_forall_iff
    {Sample : Type*} [MeasurableSpace Sample]
    (sampleLaw : Measure Sample) {first second : Sample -> Prop}
    (hequiv : ∀ sample, first sample ↔ second sample) :
    eventProbabilityReal sampleLaw first =
      eventProbabilityReal sampleLaw second := by
  unfold eventProbabilityReal
  rw [eventSet_eq_of_forall_iff hequiv]

/--
For positive scale and standard error, the Wald coverage indicator equals the
indicator of the absolute studentized event.
-/
theorem waldCoverageIndicator_eq_absStudentizedIndicator
    (estimator target criticalValue standardError scale : Real)
    (hstandardError : 0 < standardError)
    (hscale : 0 < scale)
    [Decidable
      (waldCovers estimator target criticalValue standardError scale)]
    [Decidable
      (|waldStudentized estimator target standardError scale| ≤
        criticalValue)] :
    eventIndicator
        (waldCovers estimator target criticalValue standardError scale) =
      eventIndicator
        (|waldStudentized estimator target standardError scale| ≤
          criticalValue) :=
  eventIndicator_eq_of_iff
    (waldCovers_iff_abs_waldStudentized_le_critical estimator target
      criticalValue standardError scale hstandardError hscale)

/--
For positive scale and standard error, the Wald coverage indicator equals the
indicator of the two-sided studentized event.
-/
theorem waldCoverageIndicator_eq_twoSidedStudentizedIndicator
    (estimator target criticalValue standardError scale : Real)
    (hstandardError : 0 < standardError)
    (hscale : 0 < scale)
    [Decidable
      (waldCovers estimator target criticalValue standardError scale)]
    [Decidable
      (-criticalValue ≤ waldStudentized estimator target standardError scale ∧
        waldStudentized estimator target standardError scale ≤
          criticalValue)] :
    eventIndicator
        (waldCovers estimator target criticalValue standardError scale) =
      eventIndicator
        (-criticalValue ≤ waldStudentized estimator target standardError scale ∧
          waldStudentized estimator target standardError scale ≤
            criticalValue) :=
  eventIndicator_eq_of_iff
    (waldCovers_iff_waldStudentized_between estimator target criticalValue
      standardError scale hstandardError hscale)

/--
For random estimators with pointwise positive standard error and scale, the
Wald coverage event has the same probability as the absolute studentized
event.
-/
theorem waldCoverageEventProbability_eq_absStudentizedEventProbability
    {Sample : Type*} [MeasurableSpace Sample]
    (sampleLaw : Measure Sample)
    (estimator standardError : Sample -> Real)
    (target criticalValue scale : Real)
    (hstandardError : ∀ sample, 0 < standardError sample)
    (hscale : 0 < scale) :
    eventProbability sampleLaw
        (fun sample =>
          waldCovers (estimator sample) target criticalValue
            (standardError sample) scale) =
      eventProbability sampleLaw
        (fun sample =>
          |waldStudentized (estimator sample) target
            (standardError sample) scale| ≤ criticalValue) :=
  eventProbability_eq_of_forall_iff sampleLaw
    (fun sample =>
      waldCovers_iff_abs_waldStudentized_le_critical
        (estimator sample) target criticalValue (standardError sample) scale
        (hstandardError sample) hscale)

/--
For random estimators with pointwise positive standard error and scale, the
Wald coverage event has the same probability as the two-sided studentized
event.
-/
theorem waldCoverageEventProbability_eq_twoSidedStudentizedEventProbability
    {Sample : Type*} [MeasurableSpace Sample]
    (sampleLaw : Measure Sample)
    (estimator standardError : Sample -> Real)
    (target criticalValue scale : Real)
    (hstandardError : ∀ sample, 0 < standardError sample)
    (hscale : 0 < scale) :
    eventProbability sampleLaw
        (fun sample =>
          waldCovers (estimator sample) target criticalValue
            (standardError sample) scale) =
      eventProbability sampleLaw
        (fun sample =>
          -criticalValue ≤
              waldStudentized (estimator sample) target
                (standardError sample) scale ∧
            waldStudentized (estimator sample) target
              (standardError sample) scale ≤ criticalValue) :=
  eventProbability_eq_of_forall_iff sampleLaw
    (fun sample =>
      waldCovers_iff_waldStudentized_between
        (estimator sample) target criticalValue (standardError sample) scale
        (hstandardError sample) hscale)

/--
Real-valued version: Wald coverage and absolute studentized events have equal
probability under pointwise positive standard errors and positive scale.
-/
theorem waldCoverageEventProbabilityReal_eq_absStudentizedEventProbabilityReal
    {Sample : Type*} [MeasurableSpace Sample]
    (sampleLaw : Measure Sample)
    (estimator standardError : Sample -> Real)
    (target criticalValue scale : Real)
    (hstandardError : ∀ sample, 0 < standardError sample)
    (hscale : 0 < scale) :
    eventProbabilityReal sampleLaw
        (fun sample =>
          waldCovers (estimator sample) target criticalValue
            (standardError sample) scale) =
      eventProbabilityReal sampleLaw
        (fun sample =>
          |waldStudentized (estimator sample) target
            (standardError sample) scale| ≤ criticalValue) :=
  eventProbabilityReal_eq_of_forall_iff sampleLaw
    (fun sample =>
      waldCovers_iff_abs_waldStudentized_le_critical
        (estimator sample) target criticalValue (standardError sample) scale
        (hstandardError sample) hscale)

/--
Real-valued version: Wald coverage and two-sided studentized events have equal
probability under pointwise positive standard errors and positive scale.
-/
theorem waldCoverageEventProbabilityReal_eq_twoSidedStudentizedEventProbabilityReal
    {Sample : Type*} [MeasurableSpace Sample]
    (sampleLaw : Measure Sample)
    (estimator standardError : Sample -> Real)
    (target criticalValue scale : Real)
    (hstandardError : ∀ sample, 0 < standardError sample)
    (hscale : 0 < scale) :
    eventProbabilityReal sampleLaw
        (fun sample =>
          waldCovers (estimator sample) target criticalValue
            (standardError sample) scale) =
      eventProbabilityReal sampleLaw
        (fun sample =>
          -criticalValue ≤
              waldStudentized (estimator sample) target
                (standardError sample) scale ∧
            waldStudentized (estimator sample) target
              (standardError sample) scale ≤ criticalValue) :=
  eventProbabilityReal_eq_of_forall_iff sampleLaw
    (fun sample =>
      waldCovers_iff_waldStudentized_between
        (estimator sample) target criticalValue (standardError sample) scale
        (hstandardError sample) hscale)

/--
Eventual pointwise positivity gives eventual equality of Wald coverage and
absolute studentized event-probability sequences.
-/
theorem eventuallyEq_waldCoverageProbability_absStudentized
    {Index Sample : Type*} [MeasurableSpace Sample] {l : Filter Index}
    (sampleLaw : Index -> Measure Sample)
    (estimator standardError : Index -> Sample -> Real)
    (target criticalValue scale : Index -> Real)
    (hstandardError :
      ∀ᶠ index in l, ∀ sample, 0 < standardError index sample)
    (hscale : ∀ᶠ index in l, 0 < scale index) :
    (fun index =>
      eventProbability (sampleLaw index)
        (fun sample =>
          waldCovers (estimator index sample) (target index)
            (criticalValue index) (standardError index sample)
            (scale index))) =ᶠ[l]
      (fun index =>
        eventProbability (sampleLaw index)
          (fun sample =>
            |waldStudentized (estimator index sample) (target index)
              (standardError index sample) (scale index)| ≤
                criticalValue index)) := by
  filter_upwards [hstandardError, hscale] with index hse hscale_index
  exact waldCoverageEventProbability_eq_absStudentizedEventProbability
    (sampleLaw index) (estimator index) (standardError index) (target index)
    (criticalValue index) (scale index) hse hscale_index

/--
Eventual pointwise positivity gives eventual equality of Wald coverage and
two-sided studentized event-probability sequences.
-/
theorem eventuallyEq_waldCoverageProbability_twoSidedStudentized
    {Index Sample : Type*} [MeasurableSpace Sample] {l : Filter Index}
    (sampleLaw : Index -> Measure Sample)
    (estimator standardError : Index -> Sample -> Real)
    (target criticalValue scale : Index -> Real)
    (hstandardError :
      ∀ᶠ index in l, ∀ sample, 0 < standardError index sample)
    (hscale : ∀ᶠ index in l, 0 < scale index) :
    (fun index =>
      eventProbability (sampleLaw index)
        (fun sample =>
          waldCovers (estimator index sample) (target index)
            (criticalValue index) (standardError index sample)
            (scale index))) =ᶠ[l]
      (fun index =>
        eventProbability (sampleLaw index)
          (fun sample =>
            -criticalValue index ≤
                waldStudentized (estimator index sample) (target index)
                  (standardError index sample) (scale index) ∧
              waldStudentized (estimator index sample) (target index)
                (standardError index sample) (scale index) ≤
                  criticalValue index)) := by
  filter_upwards [hstandardError, hscale] with index hse hscale_index
  exact waldCoverageEventProbability_eq_twoSidedStudentizedEventProbability
    (sampleLaw index) (estimator index) (standardError index) (target index)
    (criticalValue index) (scale index) hse hscale_index

/--
Eventual pointwise positivity gives eventual equality of real-valued Wald
coverage and absolute studentized event-probability sequences.
-/
theorem eventuallyEq_waldCoverageProbabilityReal_absStudentized
    {Index Sample : Type*} [MeasurableSpace Sample] {l : Filter Index}
    (sampleLaw : Index -> Measure Sample)
    (estimator standardError : Index -> Sample -> Real)
    (target criticalValue scale : Index -> Real)
    (hstandardError :
      ∀ᶠ index in l, ∀ sample, 0 < standardError index sample)
    (hscale : ∀ᶠ index in l, 0 < scale index) :
    (fun index =>
      eventProbabilityReal (sampleLaw index)
        (fun sample =>
          waldCovers (estimator index sample) (target index)
            (criticalValue index) (standardError index sample)
            (scale index))) =ᶠ[l]
      (fun index =>
        eventProbabilityReal (sampleLaw index)
          (fun sample =>
            |waldStudentized (estimator index sample) (target index)
              (standardError index sample) (scale index)| ≤
                criticalValue index)) := by
  filter_upwards [hstandardError, hscale] with index hse hscale_index
  exact waldCoverageEventProbabilityReal_eq_absStudentizedEventProbabilityReal
    (sampleLaw index) (estimator index) (standardError index) (target index)
    (criticalValue index) (scale index) hse hscale_index

/--
Eventual pointwise positivity gives eventual equality of real-valued Wald
coverage and two-sided studentized event-probability sequences.
-/
theorem eventuallyEq_waldCoverageProbabilityReal_twoSidedStudentized
    {Index Sample : Type*} [MeasurableSpace Sample] {l : Filter Index}
    (sampleLaw : Index -> Measure Sample)
    (estimator standardError : Index -> Sample -> Real)
    (target criticalValue scale : Index -> Real)
    (hstandardError :
      ∀ᶠ index in l, ∀ sample, 0 < standardError index sample)
    (hscale : ∀ᶠ index in l, 0 < scale index) :
    (fun index =>
      eventProbabilityReal (sampleLaw index)
        (fun sample =>
          waldCovers (estimator index sample) (target index)
            (criticalValue index) (standardError index sample)
            (scale index))) =ᶠ[l]
      (fun index =>
        eventProbabilityReal (sampleLaw index)
          (fun sample =>
            -criticalValue index ≤
                waldStudentized (estimator index sample) (target index)
                  (standardError index sample) (scale index) ∧
              waldStudentized (estimator index sample) (target index)
                (standardError index sample) (scale index) ≤
                  criticalValue index)) := by
  filter_upwards [hstandardError, hscale] with index hse hscale_index
  exact
    waldCoverageEventProbabilityReal_eq_twoSidedStudentizedEventProbabilityReal
      (sampleLaw index) (estimator index) (standardError index) (target index)
      (criticalValue index) (scale index) hse hscale_index

/--
Eventually equal probability sequences have the same limit.  This is the
abstract coverage-probability transfer after event equivalence and
critical-value calibration have identified the studentized-event limit.
-/
theorem tendsto_waldCoverageProbability_of_eventually_eq_studentized
    {Index : Type*} {l : Filter Index}
    (waldCoverageProbability studentizedEventProbability : Index -> Real)
    (coverageLimit : Real)
    (heq :
      waldCoverageProbability =ᶠ[l] studentizedEventProbability)
    (hstudentized :
      Tendsto studentizedEventProbability l (nhds coverageLimit)) :
    Tendsto waldCoverageProbability l (nhds coverageLimit) :=
  hstudentized.congr' heq.symm

/--
Direct real-valued Wald coverage-limit transfer from the calibrated absolute
studentized event probability, under eventual pointwise positivity.
-/
theorem tendsto_waldCoverageProbabilityReal_absStudentized_of_tendsto
    {Index Sample : Type*} [MeasurableSpace Sample] {l : Filter Index}
    (sampleLaw : Index -> Measure Sample)
    (estimator standardError : Index -> Sample -> Real)
    (target criticalValue scale : Index -> Real)
    (coverageLimit : Real)
    (hstandardError :
      ∀ᶠ index in l, ∀ sample, 0 < standardError index sample)
    (hscale : ∀ᶠ index in l, 0 < scale index)
    (hstudentized :
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
            waldCovers (estimator index sample) (target index)
              (criticalValue index) (standardError index sample)
              (scale index))) l (nhds coverageLimit) :=
  tendsto_waldCoverageProbability_of_eventually_eq_studentized
    (fun index =>
      eventProbabilityReal (sampleLaw index)
        (fun sample =>
          waldCovers (estimator index sample) (target index)
            (criticalValue index) (standardError index sample)
            (scale index)))
    (fun index =>
      eventProbabilityReal (sampleLaw index)
        (fun sample =>
          |waldStudentized (estimator index sample) (target index)
            (standardError index sample) (scale index)| ≤
              criticalValue index))
    coverageLimit
    (eventuallyEq_waldCoverageProbabilityReal_absStudentized sampleLaw
      estimator standardError target criticalValue scale hstandardError hscale)
    hstudentized

/--
Direct real-valued Wald coverage-limit transfer from the calibrated two-sided
studentized event probability, under eventual pointwise positivity.
-/
theorem tendsto_waldCoverageProbabilityReal_twoSidedStudentized_of_tendsto
    {Index Sample : Type*} [MeasurableSpace Sample] {l : Filter Index}
    (sampleLaw : Index -> Measure Sample)
    (estimator standardError : Index -> Sample -> Real)
    (target criticalValue scale : Index -> Real)
    (coverageLimit : Real)
    (hstandardError :
      ∀ᶠ index in l, ∀ sample, 0 < standardError index sample)
    (hscale : ∀ᶠ index in l, 0 < scale index)
    (hstudentized :
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
            waldCovers (estimator index sample) (target index)
              (criticalValue index) (standardError index sample)
              (scale index))) l (nhds coverageLimit) :=
  tendsto_waldCoverageProbability_of_eventually_eq_studentized
    (fun index =>
      eventProbabilityReal (sampleLaw index)
        (fun sample =>
          waldCovers (estimator index sample) (target index)
            (criticalValue index) (standardError index sample)
            (scale index)))
    (fun index =>
      eventProbabilityReal (sampleLaw index)
        (fun sample =>
          -criticalValue index ≤
              waldStudentized (estimator index sample) (target index)
                (standardError index sample) (scale index) ∧
            waldStudentized (estimator index sample) (target index)
              (standardError index sample) (scale index) ≤
                criticalValue index))
    coverageLimit
    (eventuallyEq_waldCoverageProbabilityReal_twoSidedStudentized sampleLaw
      estimator standardError target criticalValue scale hstandardError hscale)
    hstudentized

/--
Named bridge for the remaining WDSM Wald critical-value calibration step.
Later probability work must supply `studentizedEventProbability_tendsto` from
the studentized limiting distribution and the chosen critical value, and
`probabilities_agree` from the event-equivalence algebra above.
-/
structure WaldCoverageLimitBridge (Index : Type*) (l : Filter Index) where
  waldCoverageProbability : Index -> Real
  studentizedEventProbability : Index -> Real
  coverageLimit : Real
  probabilities_agree :
    waldCoverageProbability =ᶠ[l] studentizedEventProbability
  studentizedEventProbability_tendsto :
    Tendsto studentizedEventProbability l (nhds coverageLimit)

/-- The named Wald coverage bridge yields the coverage probability limit. -/
theorem waldCoverageProbability_tendsto_of_bridge
    {Index : Type*} {l : Filter Index}
    (bridge : WaldCoverageLimitBridge Index l) :
    Tendsto bridge.waldCoverageProbability l (nhds bridge.coverageLimit) :=
  tendsto_waldCoverageProbability_of_eventually_eq_studentized
    bridge.waldCoverageProbability bridge.studentizedEventProbability
    bridge.coverageLimit bridge.probabilities_agree
    bridge.studentizedEventProbability_tendsto

end WDSM
end Matching
end StatInference
