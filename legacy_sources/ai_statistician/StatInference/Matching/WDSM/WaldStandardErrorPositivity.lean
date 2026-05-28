import StatInference.Matching.WDSM.WaldInferenceBridge

/-!
# Wald standard-error positivity from variance positivity

The Wald coverage inputs require pointwise positive standard errors.  This
module reduces that requirement to pointwise positive variance estimates when
the standard error is defined as `sqrt(varianceEstimate)`.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open Filter
open scoped Topology

variable {Index Sample : Type*} [MeasurableSpace Sample] {l : Filter Index}

/-- A positive variance target gives a positive standard error. -/
theorem standardError_pos_of_variance_pos
    (varianceTarget : Real) (hvariance : 0 < varianceTarget) :
    0 < standardError varianceTarget := by
  unfold standardError
  exact Real.sqrt_pos.2 hvariance

/-- A positive variance target gives a nonzero standard error. -/
theorem standardError_ne_zero_of_variance_pos
    (varianceTarget : Real) (hvariance : 0 < varianceTarget) :
    standardError varianceTarget ≠ 0 :=
  (standardError_pos_of_variance_pos varianceTarget hvariance).ne'

omit [MeasurableSpace Sample] in
/-- Eventual pointwise positive variance estimates give eventual positive standard errors. -/
theorem eventually_standardError_positive_of_eventually_variance_positive
    (varianceEstimate : Index -> Sample -> Real)
    (hvariance :
      ∀ᶠ index in l, ∀ sample, 0 < varianceEstimate index sample) :
    ∀ᶠ index in l, ∀ sample, 0 < standardError (varianceEstimate index sample) := by
  filter_upwards [hvariance] with index hvariance_index sample
  exact standardError_pos_of_variance_pos
    (varianceEstimate index sample) (hvariance_index sample)

omit [MeasurableSpace Sample] in
/--
Eventual pointwise positive heterogeneity and nonnegative residual variance
make the oracle variance eventually pointwise positive.
-/
theorem eventually_oracleVariance_positive_of_eventually_heterogeneity_pos
    (heterogeneity residual : Index -> Sample -> Real)
    (hheterogeneity :
      ∀ᶠ index in l, ∀ sample, 0 < heterogeneity index sample)
    (hresidual :
      ∀ᶠ index in l, ∀ sample, 0 ≤ residual index sample) :
    ∀ᶠ index in l, ∀ sample,
      0 < oracleVariance (heterogeneity index sample)
        (residual index sample) := by
  filter_upwards [hheterogeneity, hresidual] with index hhet hres sample
  exact oracleVariance_pos_of_heterogeneity_pos_of_residual_nonneg
    (heterogeneity index sample) (residual index sample)
    (hhet sample) (hres sample)

omit [MeasurableSpace Sample] in
/--
Eventual pointwise nonnegative heterogeneity and positive residual variance
make the oracle variance eventually pointwise positive.
-/
theorem eventually_oracleVariance_positive_of_eventually_residual_pos
    (heterogeneity residual : Index -> Sample -> Real)
    (hheterogeneity :
      ∀ᶠ index in l, ∀ sample, 0 ≤ heterogeneity index sample)
    (hresidual :
      ∀ᶠ index in l, ∀ sample, 0 < residual index sample) :
    ∀ᶠ index in l, ∀ sample,
      0 < oracleVariance (heterogeneity index sample)
        (residual index sample) := by
  filter_upwards [hheterogeneity, hresidual] with index hhet hres sample
  exact oracleVariance_pos_of_residual_pos_of_heterogeneity_nonneg
    (heterogeneity index sample) (residual index sample)
    (hhet sample) (hres sample)

omit [MeasurableSpace Sample] in
/--
Eventual treated-side positivity gives pointwise positivity of the assembled
two-arm residual variance estimate.
-/
theorem eventually_twoArmWeightedResidualVariance_positive_of_eventually_treated_pos
    (denominator treatedShare controlShare treatedArmVariance
      controlArmVariance : Index -> Sample -> Real)
    (hdenominator :
      ∀ᶠ index in l, ∀ sample, denominator index sample ≠ 0)
    (htreatedShare :
      ∀ᶠ index in l, ∀ sample, 0 < treatedShare index sample)
    (hcontrolShare :
      ∀ᶠ index in l, ∀ sample, 0 ≤ controlShare index sample)
    (htreatedVariance :
      ∀ᶠ index in l, ∀ sample, 0 < treatedArmVariance index sample)
    (hcontrolVariance :
      ∀ᶠ index in l, ∀ sample, 0 ≤ controlArmVariance index sample) :
    ∀ᶠ index in l, ∀ sample,
      0 < twoArmWeightedResidualVariance (denominator index sample)
        (treatedShare index sample) (controlShare index sample)
        (treatedArmVariance index sample) (controlArmVariance index sample) := by
  filter_upwards
    [hdenominator, htreatedShare, hcontrolShare, htreatedVariance,
      hcontrolVariance] with index hden htreatedShare hcontrolShare
      htreatedVariance hcontrolVariance sample
  exact twoArmWeightedResidualVariance_pos_of_treated_pos
    (denominator index sample) (treatedShare index sample)
    (controlShare index sample) (treatedArmVariance index sample)
    (controlArmVariance index sample) (hden sample) (htreatedShare sample)
    (hcontrolShare sample) (htreatedVariance sample)
    (hcontrolVariance sample)

omit [MeasurableSpace Sample] in
/--
Eventual control-side positivity gives pointwise positivity of the assembled
two-arm residual variance estimate.
-/
theorem eventually_twoArmWeightedResidualVariance_positive_of_eventually_control_pos
    (denominator treatedShare controlShare treatedArmVariance
      controlArmVariance : Index -> Sample -> Real)
    (hdenominator :
      ∀ᶠ index in l, ∀ sample, denominator index sample ≠ 0)
    (htreatedShare :
      ∀ᶠ index in l, ∀ sample, 0 ≤ treatedShare index sample)
    (hcontrolShare :
      ∀ᶠ index in l, ∀ sample, 0 < controlShare index sample)
    (htreatedVariance :
      ∀ᶠ index in l, ∀ sample, 0 ≤ treatedArmVariance index sample)
    (hcontrolVariance :
      ∀ᶠ index in l, ∀ sample, 0 < controlArmVariance index sample) :
    ∀ᶠ index in l, ∀ sample,
      0 < twoArmWeightedResidualVariance (denominator index sample)
        (treatedShare index sample) (controlShare index sample)
        (treatedArmVariance index sample) (controlArmVariance index sample) := by
  filter_upwards
    [hdenominator, htreatedShare, hcontrolShare, htreatedVariance,
      hcontrolVariance] with index hden htreatedShare hcontrolShare
      htreatedVariance hcontrolVariance sample
  exact twoArmWeightedResidualVariance_pos_of_control_pos
    (denominator index sample) (treatedShare index sample)
    (controlShare index sample) (treatedArmVariance index sample)
    (controlArmVariance index sample) (hden sample) (htreatedShare sample)
    (hcontrolShare sample) (htreatedVariance sample)
    (hcontrolVariance sample)

omit [MeasurableSpace Sample] in
/--
Eventual treated-side positivity gives pointwise positivity of the assembled
PATT residual variance estimate.
-/
theorem eventually_pattWeightedResidualVariance_positive_of_eventually_treated_pos
    (denominator treatedShare controlShare treatedDirectVariance
      matchedControlVariance : Index -> Sample -> Real)
    (hdenominator :
      ∀ᶠ index in l, ∀ sample, denominator index sample ≠ 0)
    (htreatedShare :
      ∀ᶠ index in l, ∀ sample, 0 < treatedShare index sample)
    (hcontrolShare :
      ∀ᶠ index in l, ∀ sample, 0 ≤ controlShare index sample)
    (htreatedVariance :
      ∀ᶠ index in l, ∀ sample, 0 < treatedDirectVariance index sample)
    (hcontrolVariance :
      ∀ᶠ index in l, ∀ sample, 0 ≤ matchedControlVariance index sample) :
    ∀ᶠ index in l, ∀ sample,
      0 < pattWeightedResidualVariance (denominator index sample)
        (treatedShare index sample) (controlShare index sample)
        (treatedDirectVariance index sample)
        (matchedControlVariance index sample) := by
  filter_upwards
    [hdenominator, htreatedShare, hcontrolShare, htreatedVariance,
      hcontrolVariance] with index hden htreatedShare hcontrolShare
      htreatedVariance hcontrolVariance sample
  exact pattWeightedResidualVariance_pos_of_treated_pos
    (denominator index sample) (treatedShare index sample)
    (controlShare index sample) (treatedDirectVariance index sample)
    (matchedControlVariance index sample) (hden sample)
    (htreatedShare sample) (hcontrolShare sample)
    (htreatedVariance sample) (hcontrolVariance sample)

omit [MeasurableSpace Sample] in
/--
Eventual matched-control-side positivity gives pointwise positivity of the
assembled PATT residual variance estimate.
-/
theorem eventually_pattWeightedResidualVariance_positive_of_eventually_control_pos
    (denominator treatedShare controlShare treatedDirectVariance
      matchedControlVariance : Index -> Sample -> Real)
    (hdenominator :
      ∀ᶠ index in l, ∀ sample, denominator index sample ≠ 0)
    (htreatedShare :
      ∀ᶠ index in l, ∀ sample, 0 ≤ treatedShare index sample)
    (hcontrolShare :
      ∀ᶠ index in l, ∀ sample, 0 < controlShare index sample)
    (htreatedVariance :
      ∀ᶠ index in l, ∀ sample, 0 ≤ treatedDirectVariance index sample)
    (hcontrolVariance :
      ∀ᶠ index in l, ∀ sample, 0 < matchedControlVariance index sample) :
    ∀ᶠ index in l, ∀ sample,
      0 < pattWeightedResidualVariance (denominator index sample)
        (treatedShare index sample) (controlShare index sample)
        (treatedDirectVariance index sample)
        (matchedControlVariance index sample) := by
  filter_upwards
    [hdenominator, htreatedShare, hcontrolShare, htreatedVariance,
      hcontrolVariance] with index hden htreatedShare hcontrolShare
      htreatedVariance hcontrolVariance sample
  exact pattWeightedResidualVariance_pos_of_control_pos
    (denominator index sample) (treatedShare index sample)
    (controlShare index sample) (treatedDirectVariance index sample)
    (matchedControlVariance index sample) (hden sample)
    (htreatedShare sample) (hcontrolShare sample)
    (htreatedVariance sample) (hcontrolVariance sample)

omit [MeasurableSpace Sample] in
/--
Eventual strict projection slack gives pointwise positivity of the fixed-law
estimated-score variance estimate.
-/
theorem eventually_fixedLawEstimatedScoreVariance_positive_of_eventually_projection_lt_oracle
    (oracle projectionReduction : Index -> Sample -> Real)
    (hprojection_lt_oracle :
      ∀ᶠ index in l, ∀ sample,
        projectionReduction index sample < oracle index sample) :
    ∀ᶠ index in l, ∀ sample,
      0 < estimatedScoreVariance (oracle index sample)
        (projectionReduction index sample) 0 := by
  filter_upwards [hprojection_lt_oracle] with index hlt sample
  exact fixedLawEstimatedScoreVariance_pos_of_projection_lt_oracle
    (oracle index sample) (projectionReduction index sample) (hlt sample)

omit [MeasurableSpace Sample] in
/--
Eventual strict projection slack and nonnegative moving-target drift give
pointwise positivity of the changing-law estimated-score variance estimate.
-/
theorem eventually_estimatedScoreVariance_positive_of_eventually_projection_lt_oracle_of_drift_nonneg
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (hprojection_lt_oracle :
      ∀ᶠ index in l, ∀ sample,
        projectionReduction index sample < oracle index sample)
    (hdrift :
      ∀ᶠ index in l, ∀ sample, 0 ≤ targetDrift index sample) :
    ∀ᶠ index in l, ∀ sample,
      0 < estimatedScoreVariance (oracle index sample)
        (projectionReduction index sample) (targetDrift index sample) := by
  filter_upwards [hprojection_lt_oracle, hdrift] with index hlt hdrift sample
  exact changingTargetVariance_pos_of_projection_lt_oracle_of_drift_nonneg
    (oracle index sample) (projectionReduction index sample)
    (targetDrift index sample) (hlt sample) (hdrift sample)

omit [MeasurableSpace Sample] in
/--
Eventual weak projection slack and positive moving-target drift give pointwise
positivity of the changing-law estimated-score variance estimate.
-/
theorem eventually_estimatedScoreVariance_positive_of_eventually_projection_le_oracle_of_drift_pos
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (hprojection_le_oracle :
      ∀ᶠ index in l, ∀ sample,
        projectionReduction index sample ≤ oracle index sample)
    (hdrift :
      ∀ᶠ index in l, ∀ sample, 0 < targetDrift index sample) :
    ∀ᶠ index in l, ∀ sample,
      0 < estimatedScoreVariance (oracle index sample)
        (projectionReduction index sample) (targetDrift index sample) := by
  filter_upwards [hprojection_le_oracle, hdrift] with index hle hdrift sample
  exact changingTargetVariance_pos_of_projection_le_oracle_of_drift_pos
    (oracle index sample) (projectionReduction index sample)
    (targetDrift index sample) (hle sample) (hdrift sample)

/--
Absolute Wald coverage input stated in terms of a variance estimate rather than
a precomputed standard error.
-/
structure AbsoluteWaldCoverageVarianceInput
    (Index Sample : Type*) [MeasurableSpace Sample] (l : Filter Index) where
  sampleLawSeq : Index -> Measure Sample
  estimator : Index -> Sample -> Real
  varianceEstimate : Index -> Sample -> Real
  target : Index -> Real
  criticalValue : Index -> Real
  scale : Index -> Real
  coverageLimit : Real
  variance_positive :
    ∀ᶠ index in l, ∀ sample, 0 < varianceEstimate index sample
  scale_positive : ∀ᶠ index in l, 0 < scale index
  absoluteStudentizedProbability_tendsto :
    Tendsto
      (fun index =>
        eventProbabilityReal (sampleLawSeq index)
          (fun sample =>
            |waldStudentized (estimator index sample) (target index)
              (standardError (varianceEstimate index sample))
              (scale index)| ≤ criticalValue index)) l (nhds coverageLimit)

/-- Convert variance-based absolute Wald input to the standard-error input. -/
noncomputable def absoluteWaldCoverageInput_of_variance
    (input : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    AbsoluteWaldCoverageInput Index Sample l where
  sampleLawSeq := input.sampleLawSeq
  estimator := input.estimator
  standardError := fun index sample =>
    standardError (input.varianceEstimate index sample)
  target := input.target
  criticalValue := input.criticalValue
  scale := input.scale
  coverageLimit := input.coverageLimit
  standardError_positive :=
    eventually_standardError_positive_of_eventually_variance_positive
      input.varianceEstimate input.variance_positive
  scale_positive := input.scale_positive
  absoluteStudentizedProbability_tendsto :=
    input.absoluteStudentizedProbability_tendsto

/-- Variance-based absolute Wald input yields the real-valued coverage limit. -/
theorem absoluteWaldCoverage_tendsto_of_variance_input
    (input : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    Tendsto
      (fun index =>
        eventProbabilityReal (input.sampleLawSeq index)
          (fun sample =>
            waldCovers (input.estimator index sample) (input.target index)
              (input.criticalValue index)
              (standardError (input.varianceEstimate index sample))
              (input.scale index))) l (nhds input.coverageLimit) :=
  absoluteWaldCoverage_tendsto_of_input
    (absoluteWaldCoverageInput_of_variance input)

/--
Two-sided Wald coverage input stated in terms of a variance estimate rather
than a precomputed standard error.
-/
structure TwoSidedWaldCoverageVarianceInput
    (Index Sample : Type*) [MeasurableSpace Sample] (l : Filter Index) where
  sampleLawSeq : Index -> Measure Sample
  estimator : Index -> Sample -> Real
  varianceEstimate : Index -> Sample -> Real
  target : Index -> Real
  criticalValue : Index -> Real
  scale : Index -> Real
  coverageLimit : Real
  variance_positive :
    ∀ᶠ index in l, ∀ sample, 0 < varianceEstimate index sample
  scale_positive : ∀ᶠ index in l, 0 < scale index
  twoSidedStudentizedProbability_tendsto :
    Tendsto
      (fun index =>
        eventProbabilityReal (sampleLawSeq index)
          (fun sample =>
            -criticalValue index ≤
                waldStudentized (estimator index sample) (target index)
                  (standardError (varianceEstimate index sample))
                  (scale index) ∧
              waldStudentized (estimator index sample) (target index)
                (standardError (varianceEstimate index sample))
                (scale index) ≤ criticalValue index)) l (nhds coverageLimit)

/-- Convert variance-based two-sided Wald input to the standard-error input. -/
noncomputable def twoSidedWaldCoverageInput_of_variance
    (input : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    TwoSidedWaldCoverageInput Index Sample l where
  sampleLawSeq := input.sampleLawSeq
  estimator := input.estimator
  standardError := fun index sample =>
    standardError (input.varianceEstimate index sample)
  target := input.target
  criticalValue := input.criticalValue
  scale := input.scale
  coverageLimit := input.coverageLimit
  standardError_positive :=
    eventually_standardError_positive_of_eventually_variance_positive
      input.varianceEstimate input.variance_positive
  scale_positive := input.scale_positive
  twoSidedStudentizedProbability_tendsto :=
    input.twoSidedStudentizedProbability_tendsto

/-- Variance-based two-sided Wald input yields the real-valued coverage limit. -/
theorem twoSidedWaldCoverage_tendsto_of_variance_input
    (input : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    Tendsto
      (fun index =>
        eventProbabilityReal (input.sampleLawSeq index)
          (fun sample =>
            waldCovers (input.estimator index sample) (input.target index)
              (input.criticalValue index)
              (standardError (input.varianceEstimate index sample))
              (input.scale index))) l (nhds input.coverageLimit) :=
  twoSidedWaldCoverage_tendsto_of_input
    (twoSidedWaldCoverageInput_of_variance input)

end WDSM
end Matching
end StatInference
