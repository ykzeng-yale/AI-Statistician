import StatInference.Matching.WDSM.PositiveVarianceWaldInferenceBridge
import StatInference.Matching.WDSM.WaldVarianceCriticalRegionCalibration

/-!
# Positive-variance Wald coverage bridge

This module packages the generic end-to-end inference step used after a WDSM
asymptotic normality proof supplies a scaled weak limit and a variance
consistency proof.  Positive limiting variance yields the studentized weak
limit, and a variance-based critical-region calibration input yields the
real-valued Wald coverage limit.
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

/-! ## Absolute critical-region calibration -/

/--
Generic WDSM Wald inference bridge with positive limiting variance and an
absolute studentized critical-region calibration stated through variance
estimates.
-/
structure AbsolutePositiveVarianceWaldCoverageBridge
    (Index Sample LimitSample : Type*) [MeasurableSpace Sample]
    [MeasurableSpace LimitSample] (sampleLaw : Measure Sample)
    (limitLaw : Measure LimitSample) (l : Filter Index)
    [IsProbabilityMeasure sampleLaw] [IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated] where
  studentized_input :
    PositiveVarianceStudentizedLimitInput Index Sample LimitSample
      sampleLaw limitLaw l
  coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l

/--
Positive-variance studentization plus absolute variance-based calibration
yields both the studentized weak limit and the real-valued Wald coverage limit.
-/
theorem absolutePositiveVarianceWaldCoverage_tendsto_of_bridge
    (bridge :
      AbsolutePositiveVarianceWaldCoverageBridge Index Sample LimitSample
        sampleLaw limitLaw l) :
    TendstoInDistribution
        (fun index sample =>
          bridge.studentized_input.scaledStatistic index sample *
            (standardError
              (bridge.studentized_input.varianceEstimate index sample))⁻¹)
        l
        (fun limitSample =>
          bridge.studentized_input.limit limitSample *
            (standardError bridge.studentized_input.varianceLimit)⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      Tendsto
        (fun index =>
          eventProbabilityReal (bridge.coverage_input.sampleLawSeq index)
            (fun sample =>
              waldCovers (bridge.coverage_input.estimator index sample)
                (bridge.coverage_input.target index)
                (bridge.coverage_input.criticalValue index)
                (standardError
                  (bridge.coverage_input.varianceEstimate index sample))
                (bridge.coverage_input.scale index)))
        l (nhds bridge.coverage_input.coverageLimit) := by
  exact
    ⟨studentized_tendstoInDistribution_of_positiveVarianceLimitInput
        bridge.studentized_input,
      absoluteWaldCoverage_tendsto_of_variance_input bridge.coverage_input⟩

/--
Direct absolute positive-variance Wald coverage bridge.  This version takes the
studentization ingredients directly and combines them with an absolute
variance-based Wald calibration input, avoiding the packaged bridge structure.
-/
theorem absolutePositiveVarianceWaldCoverage_tendsto_of_inputs
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
          sampleLaw)
    (coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    TendstoInDistribution
        (fun index sample =>
          scaledStatistic index sample *
            (standardError (varianceEstimate index sample))⁻¹)
        l
        (fun limitSample =>
          limit limitSample * (standardError varianceLimit)⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      Tendsto
        (fun index =>
          eventProbabilityReal (coverage_input.sampleLawSeq index)
            (fun sample =>
              waldCovers (coverage_input.estimator index sample)
                (coverage_input.target index)
                (coverage_input.criticalValue index)
                (standardError
                  (coverage_input.varianceEstimate index sample))
                (coverage_input.scale index)))
        l (nhds coverage_input.coverageLimit) := by
  exact
    ⟨studentized_tendstoInDistribution_of_positiveVariance
        (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
        scaledStatistic varianceEstimate limit varianceLimit
        hvarianceLimit_pos hscaled hvariance hinverse_meas,
      absoluteWaldCoverage_tendsto_of_variance_input coverage_input⟩

/--
Absolute variance-based calibration can also be read through the two-sided
critical-region form while preserving the same Wald coverage conclusion.
-/
theorem twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_bridge
    (bridge :
      AbsolutePositiveVarianceWaldCoverageBridge Index Sample LimitSample
        sampleLaw limitLaw l) :
    TendstoInDistribution
        (fun index sample =>
          bridge.studentized_input.scaledStatistic index sample *
            (standardError
              (bridge.studentized_input.varianceEstimate index sample))⁻¹)
        l
        (fun limitSample =>
          bridge.studentized_input.limit limitSample *
            (standardError bridge.studentized_input.varianceLimit)⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      Tendsto
        (fun index =>
          eventProbabilityReal (bridge.coverage_input.sampleLawSeq index)
            (fun sample =>
              waldCovers (bridge.coverage_input.estimator index sample)
                (bridge.coverage_input.target index)
                (bridge.coverage_input.criticalValue index)
                (standardError
                  (bridge.coverage_input.varianceEstimate index sample))
                (bridge.coverage_input.scale index)))
        l (nhds bridge.coverage_input.coverageLimit) := by
  exact
    ⟨studentized_tendstoInDistribution_of_positiveVarianceLimitInput
        bridge.studentized_input,
      twoSidedVarianceWaldCoverage_tendsto_of_absolute_input
        bridge.coverage_input⟩

/--
Direct cross-calibrated absolute-input positive-variance Wald coverage bridge:
an absolute variance-based calibration input can be read through the two-sided
critical-region calibration while preserving the same Wald coverage conclusion.
-/
theorem twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_inputs
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
          sampleLaw)
    (coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    TendstoInDistribution
        (fun index sample =>
          scaledStatistic index sample *
            (standardError (varianceEstimate index sample))⁻¹)
        l
        (fun limitSample =>
          limit limitSample * (standardError varianceLimit)⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      Tendsto
        (fun index =>
          eventProbabilityReal (coverage_input.sampleLawSeq index)
            (fun sample =>
              waldCovers (coverage_input.estimator index sample)
                (coverage_input.target index)
                (coverage_input.criticalValue index)
                (standardError
                  (coverage_input.varianceEstimate index sample))
                (coverage_input.scale index)))
        l (nhds coverage_input.coverageLimit) := by
  exact
    ⟨studentized_tendstoInDistribution_of_positiveVariance
        (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
        scaledStatistic varianceEstimate limit varianceLimit
        hvarianceLimit_pos hscaled hvariance hinverse_meas,
      twoSidedVarianceWaldCoverage_tendsto_of_absolute_input
        coverage_input⟩

/-! ## Two-sided critical-region calibration -/

/--
Generic WDSM Wald inference bridge with positive limiting variance and a
two-sided studentized critical-region calibration stated through variance
estimates.
-/
structure TwoSidedPositiveVarianceWaldCoverageBridge
    (Index Sample LimitSample : Type*) [MeasurableSpace Sample]
    [MeasurableSpace LimitSample] (sampleLaw : Measure Sample)
    (limitLaw : Measure LimitSample) (l : Filter Index)
    [IsProbabilityMeasure sampleLaw] [IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated] where
  studentized_input :
    PositiveVarianceStudentizedLimitInput Index Sample LimitSample
      sampleLaw limitLaw l
  coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l

/--
Positive-variance studentization plus two-sided variance-based calibration
yields both the studentized weak limit and the real-valued Wald coverage limit.
-/
theorem twoSidedPositiveVarianceWaldCoverage_tendsto_of_bridge
    (bridge :
      TwoSidedPositiveVarianceWaldCoverageBridge Index Sample LimitSample
        sampleLaw limitLaw l) :
    TendstoInDistribution
        (fun index sample =>
          bridge.studentized_input.scaledStatistic index sample *
            (standardError
              (bridge.studentized_input.varianceEstimate index sample))⁻¹)
        l
        (fun limitSample =>
          bridge.studentized_input.limit limitSample *
            (standardError bridge.studentized_input.varianceLimit)⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      Tendsto
        (fun index =>
          eventProbabilityReal (bridge.coverage_input.sampleLawSeq index)
            (fun sample =>
              waldCovers (bridge.coverage_input.estimator index sample)
                (bridge.coverage_input.target index)
                (bridge.coverage_input.criticalValue index)
                (standardError
                  (bridge.coverage_input.varianceEstimate index sample))
                (bridge.coverage_input.scale index)))
        l (nhds bridge.coverage_input.coverageLimit) := by
  exact
    ⟨studentized_tendstoInDistribution_of_positiveVarianceLimitInput
        bridge.studentized_input,
      twoSidedWaldCoverage_tendsto_of_variance_input bridge.coverage_input⟩

/--
Direct two-sided positive-variance Wald coverage bridge.  This version takes
the studentization ingredients directly and combines them with a two-sided
variance-based Wald calibration input, avoiding the packaged bridge structure.
-/
theorem twoSidedPositiveVarianceWaldCoverage_tendsto_of_inputs
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
          sampleLaw)
    (coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    TendstoInDistribution
        (fun index sample =>
          scaledStatistic index sample *
            (standardError (varianceEstimate index sample))⁻¹)
        l
        (fun limitSample =>
          limit limitSample * (standardError varianceLimit)⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      Tendsto
        (fun index =>
          eventProbabilityReal (coverage_input.sampleLawSeq index)
            (fun sample =>
              waldCovers (coverage_input.estimator index sample)
                (coverage_input.target index)
                (coverage_input.criticalValue index)
                (standardError
                  (coverage_input.varianceEstimate index sample))
                (coverage_input.scale index)))
        l (nhds coverage_input.coverageLimit) := by
  exact
    ⟨studentized_tendstoInDistribution_of_positiveVariance
        (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
        scaledStatistic varianceEstimate limit varianceLimit
        hvarianceLimit_pos hscaled hvariance hinverse_meas,
      twoSidedWaldCoverage_tendsto_of_variance_input coverage_input⟩

/--
Two-sided variance-based calibration can also be read through the absolute
critical-region form while preserving the same Wald coverage conclusion.
-/
theorem absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_bridge
    (bridge :
      TwoSidedPositiveVarianceWaldCoverageBridge Index Sample LimitSample
        sampleLaw limitLaw l) :
    TendstoInDistribution
        (fun index sample =>
          bridge.studentized_input.scaledStatistic index sample *
            (standardError
              (bridge.studentized_input.varianceEstimate index sample))⁻¹)
        l
        (fun limitSample =>
          bridge.studentized_input.limit limitSample *
            (standardError bridge.studentized_input.varianceLimit)⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      Tendsto
        (fun index =>
          eventProbabilityReal (bridge.coverage_input.sampleLawSeq index)
            (fun sample =>
              waldCovers (bridge.coverage_input.estimator index sample)
                (bridge.coverage_input.target index)
                (bridge.coverage_input.criticalValue index)
                (standardError
                  (bridge.coverage_input.varianceEstimate index sample))
                (bridge.coverage_input.scale index)))
        l (nhds bridge.coverage_input.coverageLimit) := by
  exact
    ⟨studentized_tendstoInDistribution_of_positiveVarianceLimitInput
        bridge.studentized_input,
      absoluteVarianceWaldCoverage_tendsto_of_twoSided_input
        bridge.coverage_input⟩

/--
Direct cross-calibrated two-sided-input positive-variance Wald coverage bridge:
a two-sided variance-based calibration input can be read through the absolute
critical-region calibration while preserving the same Wald coverage conclusion.
-/
theorem absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_inputs
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
          sampleLaw)
    (coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    TendstoInDistribution
        (fun index sample =>
          scaledStatistic index sample *
            (standardError (varianceEstimate index sample))⁻¹)
        l
        (fun limitSample =>
          limit limitSample * (standardError varianceLimit)⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      Tendsto
        (fun index =>
          eventProbabilityReal (coverage_input.sampleLawSeq index)
            (fun sample =>
              waldCovers (coverage_input.estimator index sample)
                (coverage_input.target index)
                (coverage_input.criticalValue index)
                (standardError
                  (coverage_input.varianceEstimate index sample))
                (coverage_input.scale index)))
        l (nhds coverage_input.coverageLimit) := by
  exact
    ⟨studentized_tendstoInDistribution_of_positiveVariance
        (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
        scaledStatistic varianceEstimate limit varianceLimit
        hvarianceLimit_pos hscaled hvariance hinverse_meas,
      absoluteVarianceWaldCoverage_tendsto_of_twoSided_input
        coverage_input⟩

/-! ## Oracle and estimated-score variance specializations -/

/--
Absolute Wald coverage bridge with the oracle variance formula, deriving
variance consistency from heterogeneity/residual component consistency.
-/
theorem absolutePositiveVarianceWaldCoverage_tendsto_of_oracleVariance_components
    (sampleLawSeq : Index -> Measure Sample)
    (estimator scaledStatistic : Index -> Sample -> Real)
    (heterogeneity residual : Index -> Sample -> Real)
    (target criticalValue scale : Index -> Real)
    (limit : LimitSample -> Real)
    (heterogeneityLimit residualLimit coverageLimit : Real)
    (hscaled :
      TendstoInDistribution scaledStatistic l limit
        (fun _index => sampleLaw) limitLaw)
    (hheterogeneity :
      TendstoInMeasure sampleLaw heterogeneity l
        (fun _sample => heterogeneityLimit))
    (hresidual :
      TendstoInMeasure sampleLaw residual l
        (fun _sample => residualLimit))
    (hvarianceLimit_pos :
      0 < oracleVariance heterogeneityLimit residualLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (oracleVariance (heterogeneity index sample)
                (residual index sample)))⁻¹)
          sampleLaw)
    (hvariance_positive :
      ∀ᶠ index in l, ∀ sample,
        0 < oracleVariance (heterogeneity index sample)
          (residual index sample))
    (hscale_positive : ∀ᶠ index in l, 0 < scale index)
    (habsolute :
      Tendsto
        (fun index =>
          eventProbabilityReal (sampleLawSeq index)
            (fun sample =>
              |waldStudentized (estimator index sample) (target index)
                (standardError
                  (oracleVariance (heterogeneity index sample)
                    (residual index sample)))
                (scale index)| ≤ criticalValue index)) l
        (nhds coverageLimit)) :
    TendstoInDistribution
        (fun index sample =>
          scaledStatistic index sample *
            (standardError
              (oracleVariance (heterogeneity index sample)
                (residual index sample)))⁻¹)
        l
        (fun limitSample =>
          limit limitSample *
            (standardError
              (oracleVariance heterogeneityLimit residualLimit))⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      Tendsto
        (fun index =>
          eventProbabilityReal (sampleLawSeq index)
            (fun sample =>
              waldCovers (estimator index sample) (target index)
                (criticalValue index)
                (standardError
                  (oracleVariance (heterogeneity index sample)
                    (residual index sample)))
                (scale index)))
        l (nhds coverageLimit) := by
  exact absolutePositiveVarianceWaldCoverage_tendsto_of_inputs
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    scaledStatistic
    (fun index sample =>
      oracleVariance (heterogeneity index sample) (residual index sample))
    limit (oracleVariance heterogeneityLimit residualLimit)
    hvarianceLimit_pos hscaled
    (tendstoInMeasure_oracleVariance_of_tendstoInMeasure_components
      (sampleLaw := sampleLaw) (l := l)
      heterogeneity residual heterogeneityLimit residualLimit
      hheterogeneity hresidual)
    hinverse_meas
    { sampleLawSeq := sampleLawSeq
      estimator := estimator
      varianceEstimate := fun index sample =>
        oracleVariance (heterogeneity index sample) (residual index sample)
      target := target
      criticalValue := criticalValue
      scale := scale
      coverageLimit := coverageLimit
      variance_positive := hvariance_positive
      scale_positive := hscale_positive
      absoluteStudentizedProbability_tendsto := habsolute }

/--
Two-sided Wald coverage bridge with the oracle variance formula, deriving
variance consistency from heterogeneity/residual component consistency.
-/
theorem twoSidedPositiveVarianceWaldCoverage_tendsto_of_oracleVariance_components
    (sampleLawSeq : Index -> Measure Sample)
    (estimator scaledStatistic : Index -> Sample -> Real)
    (heterogeneity residual : Index -> Sample -> Real)
    (target criticalValue scale : Index -> Real)
    (limit : LimitSample -> Real)
    (heterogeneityLimit residualLimit coverageLimit : Real)
    (hscaled :
      TendstoInDistribution scaledStatistic l limit
        (fun _index => sampleLaw) limitLaw)
    (hheterogeneity :
      TendstoInMeasure sampleLaw heterogeneity l
        (fun _sample => heterogeneityLimit))
    (hresidual :
      TendstoInMeasure sampleLaw residual l
        (fun _sample => residualLimit))
    (hvarianceLimit_pos :
      0 < oracleVariance heterogeneityLimit residualLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (oracleVariance (heterogeneity index sample)
                (residual index sample)))⁻¹)
          sampleLaw)
    (hvariance_positive :
      ∀ᶠ index in l, ∀ sample,
        0 < oracleVariance (heterogeneity index sample)
          (residual index sample))
    (hscale_positive : ∀ᶠ index in l, 0 < scale index)
    (htwoSided :
      Tendsto
        (fun index =>
          eventProbabilityReal (sampleLawSeq index)
            (fun sample =>
              -criticalValue index ≤
                  waldStudentized (estimator index sample) (target index)
                    (standardError
                      (oracleVariance (heterogeneity index sample)
                        (residual index sample)))
                    (scale index) ∧
                waldStudentized (estimator index sample) (target index)
                  (standardError
                    (oracleVariance (heterogeneity index sample)
                      (residual index sample)))
                  (scale index) ≤ criticalValue index)) l
        (nhds coverageLimit)) :
    TendstoInDistribution
        (fun index sample =>
          scaledStatistic index sample *
            (standardError
              (oracleVariance (heterogeneity index sample)
                (residual index sample)))⁻¹)
        l
        (fun limitSample =>
          limit limitSample *
            (standardError
              (oracleVariance heterogeneityLimit residualLimit))⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      Tendsto
        (fun index =>
          eventProbabilityReal (sampleLawSeq index)
            (fun sample =>
              waldCovers (estimator index sample) (target index)
                (criticalValue index)
                (standardError
                  (oracleVariance (heterogeneity index sample)
                    (residual index sample)))
                (scale index)))
        l (nhds coverageLimit) := by
  exact twoSidedPositiveVarianceWaldCoverage_tendsto_of_inputs
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    scaledStatistic
    (fun index sample =>
      oracleVariance (heterogeneity index sample) (residual index sample))
    limit (oracleVariance heterogeneityLimit residualLimit)
    hvarianceLimit_pos hscaled
    (tendstoInMeasure_oracleVariance_of_tendstoInMeasure_components
      (sampleLaw := sampleLaw) (l := l)
      heterogeneity residual heterogeneityLimit residualLimit
      hheterogeneity hresidual)
    hinverse_meas
    { sampleLawSeq := sampleLawSeq
      estimator := estimator
      varianceEstimate := fun index sample =>
        oracleVariance (heterogeneity index sample) (residual index sample)
      target := target
      criticalValue := criticalValue
      scale := scale
      coverageLimit := coverageLimit
      variance_positive := hvariance_positive
      scale_positive := hscale_positive
      twoSidedStudentizedProbability_tendsto := htwoSided }

/--
Absolute Wald coverage bridge with the changing-law estimated-score variance
formula, deriving variance consistency from oracle/projection/drift component
consistency.
-/
theorem absolutePositiveVarianceWaldCoverage_tendsto_of_estimatedScoreVariance_components
    (sampleLawSeq : Index -> Measure Sample)
    (estimator scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (target criticalValue scale : Index -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit coverageLimit : Real)
    (hscaled :
      TendstoInDistribution scaledStatistic l limit
        (fun _index => sampleLaw) limitLaw)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hvarianceLimit_pos :
      0 < estimatedScoreVariance oracleLimit projectionLimit targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (hvariance_positive :
      ∀ᶠ index in l, ∀ sample,
        0 < estimatedScoreVariance (oracle index sample)
          (projectionReduction index sample) (targetDrift index sample))
    (hscale_positive : ∀ᶠ index in l, 0 < scale index)
    (habsolute :
      Tendsto
        (fun index =>
          eventProbabilityReal (sampleLawSeq index)
            (fun sample =>
              |waldStudentized (estimator index sample) (target index)
                (standardError
                  (estimatedScoreVariance (oracle index sample)
                    (projectionReduction index sample)
                    (targetDrift index sample)))
                (scale index)| ≤ criticalValue index)) l
        (nhds coverageLimit)) :
    TendstoInDistribution
        (fun index sample =>
          scaledStatistic index sample *
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
        l
        (fun limitSample =>
          limit limitSample *
            (standardError
              (estimatedScoreVariance oracleLimit projectionLimit
                targetDriftLimit))⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      Tendsto
        (fun index =>
          eventProbabilityReal (sampleLawSeq index)
            (fun sample =>
              waldCovers (estimator index sample) (target index)
                (criticalValue index)
                (standardError
                  (estimatedScoreVariance (oracle index sample)
                    (projectionReduction index sample)
                    (targetDrift index sample)))
                (scale index)))
        l (nhds coverageLimit) := by
  exact absolutePositiveVarianceWaldCoverage_tendsto_of_inputs
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    scaledStatistic
    (fun index sample =>
      estimatedScoreVariance (oracle index sample)
        (projectionReduction index sample) (targetDrift index sample))
    limit (estimatedScoreVariance oracleLimit projectionLimit targetDriftLimit)
    hvarianceLimit_pos hscaled
    (tendstoInMeasure_estimatedScoreVariance_of_tendstoInMeasure_components
      (sampleLaw := sampleLaw) (l := l)
      oracle projectionReduction targetDrift oracleLimit projectionLimit
      targetDriftLimit horacle hprojection hdrift)
    hinverse_meas
    { sampleLawSeq := sampleLawSeq
      estimator := estimator
      varianceEstimate := fun index sample =>
        estimatedScoreVariance (oracle index sample)
          (projectionReduction index sample) (targetDrift index sample)
      target := target
      criticalValue := criticalValue
      scale := scale
      coverageLimit := coverageLimit
      variance_positive := hvariance_positive
      scale_positive := hscale_positive
      absoluteStudentizedProbability_tendsto := habsolute }

/--
Two-sided Wald coverage bridge with the changing-law estimated-score variance
formula, deriving variance consistency from oracle/projection/drift component
consistency.
-/
theorem twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimatedScoreVariance_components
    (sampleLawSeq : Index -> Measure Sample)
    (estimator scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (target criticalValue scale : Index -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit coverageLimit : Real)
    (hscaled :
      TendstoInDistribution scaledStatistic l limit
        (fun _index => sampleLaw) limitLaw)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hvarianceLimit_pos :
      0 < estimatedScoreVariance oracleLimit projectionLimit targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (hvariance_positive :
      ∀ᶠ index in l, ∀ sample,
        0 < estimatedScoreVariance (oracle index sample)
          (projectionReduction index sample) (targetDrift index sample))
    (hscale_positive : ∀ᶠ index in l, 0 < scale index)
    (htwoSided :
      Tendsto
        (fun index =>
          eventProbabilityReal (sampleLawSeq index)
            (fun sample =>
              -criticalValue index ≤
                  waldStudentized (estimator index sample) (target index)
                    (standardError
                      (estimatedScoreVariance (oracle index sample)
                        (projectionReduction index sample)
                        (targetDrift index sample)))
                    (scale index) ∧
                waldStudentized (estimator index sample) (target index)
                  (standardError
                    (estimatedScoreVariance (oracle index sample)
                      (projectionReduction index sample)
                      (targetDrift index sample)))
                  (scale index) ≤ criticalValue index)) l
        (nhds coverageLimit)) :
    TendstoInDistribution
        (fun index sample =>
          scaledStatistic index sample *
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
        l
        (fun limitSample =>
          limit limitSample *
            (standardError
              (estimatedScoreVariance oracleLimit projectionLimit
                targetDriftLimit))⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      Tendsto
        (fun index =>
          eventProbabilityReal (sampleLawSeq index)
            (fun sample =>
              waldCovers (estimator index sample) (target index)
                (criticalValue index)
                (standardError
                  (estimatedScoreVariance (oracle index sample)
                    (projectionReduction index sample)
                    (targetDrift index sample)))
                (scale index)))
        l (nhds coverageLimit) := by
  exact twoSidedPositiveVarianceWaldCoverage_tendsto_of_inputs
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    scaledStatistic
    (fun index sample =>
      estimatedScoreVariance (oracle index sample)
        (projectionReduction index sample) (targetDrift index sample))
    limit (estimatedScoreVariance oracleLimit projectionLimit targetDriftLimit)
    hvarianceLimit_pos hscaled
    (tendstoInMeasure_estimatedScoreVariance_of_tendstoInMeasure_components
      (sampleLaw := sampleLaw) (l := l)
      oracle projectionReduction targetDrift oracleLimit projectionLimit
      targetDriftLimit horacle hprojection hdrift)
    hinverse_meas
    { sampleLawSeq := sampleLawSeq
      estimator := estimator
      varianceEstimate := fun index sample =>
        estimatedScoreVariance (oracle index sample)
          (projectionReduction index sample) (targetDrift index sample)
      target := target
      criticalValue := criticalValue
      scale := scale
      coverageLimit := coverageLimit
      variance_positive := hvariance_positive
      scale_positive := hscale_positive
      twoSidedStudentizedProbability_tendsto := htwoSided }

/--
Absolute Wald coverage bridge with the fixed-law estimated-score variance
formula, deriving variance consistency from oracle/projection component
consistency.
-/
theorem absolutePositiveVarianceWaldCoverage_tendsto_of_fixedLawEstimatedScoreVariance_components
    (sampleLawSeq : Index -> Measure Sample)
    (estimator scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction : Index -> Sample -> Real)
    (target criticalValue scale : Index -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit coverageLimit : Real)
    (hscaled :
      TendstoInDistribution scaledStatistic l limit
        (fun _index => sampleLaw) limitLaw)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hvarianceLimit_pos :
      0 < estimatedScoreVariance oracleLimit projectionLimit 0)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (hvariance_positive :
      ∀ᶠ index in l, ∀ sample,
        0 < estimatedScoreVariance (oracle index sample)
          (projectionReduction index sample) 0)
    (hscale_positive : ∀ᶠ index in l, 0 < scale index)
    (habsolute :
      Tendsto
        (fun index =>
          eventProbabilityReal (sampleLawSeq index)
            (fun sample =>
              |waldStudentized (estimator index sample) (target index)
                (standardError
                  (estimatedScoreVariance (oracle index sample)
                    (projectionReduction index sample) 0))
                (scale index)| ≤ criticalValue index)) l
        (nhds coverageLimit)) :
    TendstoInDistribution
        (fun index sample =>
          scaledStatistic index sample *
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample) 0))⁻¹)
        l
        (fun limitSample =>
          limit limitSample *
            (standardError
              (estimatedScoreVariance oracleLimit projectionLimit 0))⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      Tendsto
        (fun index =>
          eventProbabilityReal (sampleLawSeq index)
            (fun sample =>
              waldCovers (estimator index sample) (target index)
                (criticalValue index)
                (standardError
                  (estimatedScoreVariance (oracle index sample)
                    (projectionReduction index sample) 0))
                (scale index)))
        l (nhds coverageLimit) := by
  exact absolutePositiveVarianceWaldCoverage_tendsto_of_inputs
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    scaledStatistic
    (fun index sample =>
      estimatedScoreVariance (oracle index sample)
        (projectionReduction index sample) 0)
    limit (estimatedScoreVariance oracleLimit projectionLimit 0)
    hvarianceLimit_pos hscaled
    (tendstoInMeasure_fixedLawEstimatedScoreVariance_of_tendstoInMeasure_components
      (sampleLaw := sampleLaw) (l := l)
      oracle projectionReduction oracleLimit projectionLimit horacle
      hprojection)
    hinverse_meas
    { sampleLawSeq := sampleLawSeq
      estimator := estimator
      varianceEstimate := fun index sample =>
        estimatedScoreVariance (oracle index sample)
          (projectionReduction index sample) 0
      target := target
      criticalValue := criticalValue
      scale := scale
      coverageLimit := coverageLimit
      variance_positive := hvariance_positive
      scale_positive := hscale_positive
      absoluteStudentizedProbability_tendsto := habsolute }

/--
Two-sided Wald coverage bridge with the fixed-law estimated-score variance
formula, deriving variance consistency from oracle/projection component
consistency.
-/
theorem twoSidedPositiveVarianceWaldCoverage_tendsto_of_fixedLawEstimatedScoreVariance_components
    (sampleLawSeq : Index -> Measure Sample)
    (estimator scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction : Index -> Sample -> Real)
    (target criticalValue scale : Index -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit coverageLimit : Real)
    (hscaled :
      TendstoInDistribution scaledStatistic l limit
        (fun _index => sampleLaw) limitLaw)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hvarianceLimit_pos :
      0 < estimatedScoreVariance oracleLimit projectionLimit 0)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (hvariance_positive :
      ∀ᶠ index in l, ∀ sample,
        0 < estimatedScoreVariance (oracle index sample)
          (projectionReduction index sample) 0)
    (hscale_positive : ∀ᶠ index in l, 0 < scale index)
    (htwoSided :
      Tendsto
        (fun index =>
          eventProbabilityReal (sampleLawSeq index)
            (fun sample =>
              -criticalValue index ≤
                  waldStudentized (estimator index sample) (target index)
                    (standardError
                      (estimatedScoreVariance (oracle index sample)
                        (projectionReduction index sample) 0))
                    (scale index) ∧
                waldStudentized (estimator index sample) (target index)
                  (standardError
                    (estimatedScoreVariance (oracle index sample)
                      (projectionReduction index sample) 0))
                  (scale index) ≤ criticalValue index)) l
        (nhds coverageLimit)) :
    TendstoInDistribution
        (fun index sample =>
          scaledStatistic index sample *
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample) 0))⁻¹)
        l
        (fun limitSample =>
          limit limitSample *
            (standardError
              (estimatedScoreVariance oracleLimit projectionLimit 0))⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      Tendsto
        (fun index =>
          eventProbabilityReal (sampleLawSeq index)
            (fun sample =>
              waldCovers (estimator index sample) (target index)
                (criticalValue index)
                (standardError
                  (estimatedScoreVariance (oracle index sample)
                    (projectionReduction index sample) 0))
                (scale index)))
        l (nhds coverageLimit) := by
  exact twoSidedPositiveVarianceWaldCoverage_tendsto_of_inputs
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    scaledStatistic
    (fun index sample =>
      estimatedScoreVariance (oracle index sample)
        (projectionReduction index sample) 0)
    limit (estimatedScoreVariance oracleLimit projectionLimit 0)
    hvarianceLimit_pos hscaled
    (tendstoInMeasure_fixedLawEstimatedScoreVariance_of_tendstoInMeasure_components
      (sampleLaw := sampleLaw) (l := l)
      oracle projectionReduction oracleLimit projectionLimit horacle
      hprojection)
    hinverse_meas
    { sampleLawSeq := sampleLawSeq
      estimator := estimator
      varianceEstimate := fun index sample =>
        estimatedScoreVariance (oracle index sample)
          (projectionReduction index sample) 0
      target := target
      criticalValue := criticalValue
      scale := scale
      coverageLimit := coverageLimit
      variance_positive := hvariance_positive
      scale_positive := hscale_positive
      twoSidedStudentizedProbability_tendsto := htwoSided }

/-! ## Residual variance specializations -/

/--
Absolute Wald coverage bridge with the two-arm residual variance formula used
both for studentization and for the variance-based Wald standard error.
-/
theorem absolutePositiveVarianceWaldCoverage_tendsto_of_twoArmResidualVariance
    (sampleLawSeq : Index -> Measure Sample)
    (estimator scaledStatistic : Index -> Sample -> Real)
    (denominator treatedShare controlShare treatedArmVariance
      controlArmVariance : Index -> Sample -> Real)
    (target criticalValue scale : Index -> Real)
    (limit : LimitSample -> Real)
    (denominatorLimit treatedShareLimit controlShareLimit
      treatedVarianceLimit controlVarianceLimit : Real)
    (coverageLimit : Real)
    (hscaled :
      TendstoInDistribution scaledStatistic l limit
        (fun _index => sampleLaw) limitLaw)
    (hvariance :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          twoArmWeightedResidualVariance (denominator index sample)
            (treatedShare index sample) (controlShare index sample)
            (treatedArmVariance index sample)
            (controlArmVariance index sample)) l
        (fun _sample =>
          twoArmWeightedResidualVariance denominatorLimit treatedShareLimit
            controlShareLimit treatedVarianceLimit controlVarianceLimit))
    (hvarianceLimit_pos :
      0 < twoArmWeightedResidualVariance denominatorLimit treatedShareLimit
        controlShareLimit treatedVarianceLimit controlVarianceLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (twoArmWeightedResidualVariance (denominator index sample)
                (treatedShare index sample) (controlShare index sample)
                (treatedArmVariance index sample)
                (controlArmVariance index sample)))⁻¹)
          sampleLaw)
    (hvariance_positive :
      ∀ᶠ index in l, ∀ sample,
        0 < twoArmWeightedResidualVariance (denominator index sample)
          (treatedShare index sample) (controlShare index sample)
          (treatedArmVariance index sample) (controlArmVariance index sample))
    (hscale_positive : ∀ᶠ index in l, 0 < scale index)
    (habsolute :
      Tendsto
        (fun index =>
          eventProbabilityReal (sampleLawSeq index)
            (fun sample =>
              |waldStudentized (estimator index sample) (target index)
                (standardError
                  (twoArmWeightedResidualVariance (denominator index sample)
                    (treatedShare index sample) (controlShare index sample)
                    (treatedArmVariance index sample)
                    (controlArmVariance index sample)))
                (scale index)| ≤ criticalValue index)) l
        (nhds coverageLimit)) :
    TendstoInDistribution
        (fun index sample =>
          scaledStatistic index sample *
            (standardError
              (twoArmWeightedResidualVariance (denominator index sample)
                (treatedShare index sample) (controlShare index sample)
                (treatedArmVariance index sample)
                (controlArmVariance index sample)))⁻¹)
        l
        (fun limitSample =>
          limit limitSample *
            (standardError
              (twoArmWeightedResidualVariance denominatorLimit
                treatedShareLimit controlShareLimit treatedVarianceLimit
                controlVarianceLimit))⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      Tendsto
        (fun index =>
          eventProbabilityReal (sampleLawSeq index)
            (fun sample =>
              waldCovers (estimator index sample) (target index)
                (criticalValue index)
                (standardError
                  (twoArmWeightedResidualVariance (denominator index sample)
                    (treatedShare index sample) (controlShare index sample)
                    (treatedArmVariance index sample)
                    (controlArmVariance index sample)))
                (scale index)))
        l (nhds coverageLimit) := by
  exact absolutePositiveVarianceWaldCoverage_tendsto_of_inputs
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    scaledStatistic
    (fun index sample =>
      twoArmWeightedResidualVariance (denominator index sample)
        (treatedShare index sample) (controlShare index sample)
        (treatedArmVariance index sample) (controlArmVariance index sample))
    limit
    (twoArmWeightedResidualVariance denominatorLimit treatedShareLimit
      controlShareLimit treatedVarianceLimit controlVarianceLimit)
    hvarianceLimit_pos hscaled hvariance hinverse_meas
    { sampleLawSeq := sampleLawSeq
      estimator := estimator
      varianceEstimate := fun index sample =>
        twoArmWeightedResidualVariance (denominator index sample)
          (treatedShare index sample) (controlShare index sample)
          (treatedArmVariance index sample) (controlArmVariance index sample)
      target := target
      criticalValue := criticalValue
      scale := scale
      coverageLimit := coverageLimit
      variance_positive := hvariance_positive
      scale_positive := hscale_positive
      absoluteStudentizedProbability_tendsto := habsolute }

/--
Two-sided Wald coverage bridge with the two-arm residual variance formula used
both for studentization and for the variance-based Wald standard error.
-/
theorem twoSidedPositiveVarianceWaldCoverage_tendsto_of_twoArmResidualVariance
    (sampleLawSeq : Index -> Measure Sample)
    (estimator scaledStatistic : Index -> Sample -> Real)
    (denominator treatedShare controlShare treatedArmVariance
      controlArmVariance : Index -> Sample -> Real)
    (target criticalValue scale : Index -> Real)
    (limit : LimitSample -> Real)
    (denominatorLimit treatedShareLimit controlShareLimit
      treatedVarianceLimit controlVarianceLimit : Real)
    (coverageLimit : Real)
    (hscaled :
      TendstoInDistribution scaledStatistic l limit
        (fun _index => sampleLaw) limitLaw)
    (hvariance :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          twoArmWeightedResidualVariance (denominator index sample)
            (treatedShare index sample) (controlShare index sample)
            (treatedArmVariance index sample)
            (controlArmVariance index sample)) l
        (fun _sample =>
          twoArmWeightedResidualVariance denominatorLimit treatedShareLimit
            controlShareLimit treatedVarianceLimit controlVarianceLimit))
    (hvarianceLimit_pos :
      0 < twoArmWeightedResidualVariance denominatorLimit treatedShareLimit
        controlShareLimit treatedVarianceLimit controlVarianceLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (twoArmWeightedResidualVariance (denominator index sample)
                (treatedShare index sample) (controlShare index sample)
                (treatedArmVariance index sample)
                (controlArmVariance index sample)))⁻¹)
          sampleLaw)
    (hvariance_positive :
      ∀ᶠ index in l, ∀ sample,
        0 < twoArmWeightedResidualVariance (denominator index sample)
          (treatedShare index sample) (controlShare index sample)
          (treatedArmVariance index sample) (controlArmVariance index sample))
    (hscale_positive : ∀ᶠ index in l, 0 < scale index)
    (htwoSided :
      Tendsto
        (fun index =>
          eventProbabilityReal (sampleLawSeq index)
            (fun sample =>
              -criticalValue index ≤
                  waldStudentized (estimator index sample) (target index)
                    (standardError
                      (twoArmWeightedResidualVariance
                        (denominator index sample)
                        (treatedShare index sample)
                        (controlShare index sample)
                        (treatedArmVariance index sample)
                        (controlArmVariance index sample)))
                    (scale index) ∧
                waldStudentized (estimator index sample) (target index)
                  (standardError
                    (twoArmWeightedResidualVariance (denominator index sample)
                      (treatedShare index sample) (controlShare index sample)
                      (treatedArmVariance index sample)
                      (controlArmVariance index sample)))
                  (scale index) ≤ criticalValue index)) l
        (nhds coverageLimit)) :
    TendstoInDistribution
        (fun index sample =>
          scaledStatistic index sample *
            (standardError
              (twoArmWeightedResidualVariance (denominator index sample)
                (treatedShare index sample) (controlShare index sample)
                (treatedArmVariance index sample)
                (controlArmVariance index sample)))⁻¹)
        l
        (fun limitSample =>
          limit limitSample *
            (standardError
              (twoArmWeightedResidualVariance denominatorLimit
                treatedShareLimit controlShareLimit treatedVarianceLimit
                controlVarianceLimit))⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      Tendsto
        (fun index =>
          eventProbabilityReal (sampleLawSeq index)
            (fun sample =>
              waldCovers (estimator index sample) (target index)
                (criticalValue index)
                (standardError
                  (twoArmWeightedResidualVariance (denominator index sample)
                    (treatedShare index sample) (controlShare index sample)
                    (treatedArmVariance index sample)
                    (controlArmVariance index sample)))
                (scale index)))
        l (nhds coverageLimit) := by
  exact twoSidedPositiveVarianceWaldCoverage_tendsto_of_inputs
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    scaledStatistic
    (fun index sample =>
      twoArmWeightedResidualVariance (denominator index sample)
        (treatedShare index sample) (controlShare index sample)
        (treatedArmVariance index sample) (controlArmVariance index sample))
    limit
    (twoArmWeightedResidualVariance denominatorLimit treatedShareLimit
      controlShareLimit treatedVarianceLimit controlVarianceLimit)
    hvarianceLimit_pos hscaled hvariance hinverse_meas
    { sampleLawSeq := sampleLawSeq
      estimator := estimator
      varianceEstimate := fun index sample =>
        twoArmWeightedResidualVariance (denominator index sample)
          (treatedShare index sample) (controlShare index sample)
          (treatedArmVariance index sample) (controlArmVariance index sample)
      target := target
      criticalValue := criticalValue
      scale := scale
      coverageLimit := coverageLimit
      variance_positive := hvariance_positive
      scale_positive := hscale_positive
      twoSidedStudentizedProbability_tendsto := htwoSided }

/--
Absolute Wald coverage bridge with the PATT residual variance formula used
both for studentization and for the variance-based Wald standard error.
-/
theorem absolutePositiveVarianceWaldCoverage_tendsto_of_pattResidualVariance
    (sampleLawSeq : Index -> Measure Sample)
    (estimator scaledStatistic : Index -> Sample -> Real)
    (denominator treatedShare controlShare treatedDirectVariance
      matchedControlVariance : Index -> Sample -> Real)
    (target criticalValue scale : Index -> Real)
    (limit : LimitSample -> Real)
    (denominatorLimit treatedShareLimit controlShareLimit
      treatedDirectVarianceLimit matchedControlVarianceLimit : Real)
    (coverageLimit : Real)
    (hscaled :
      TendstoInDistribution scaledStatistic l limit
        (fun _index => sampleLaw) limitLaw)
    (hvariance :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          pattWeightedResidualVariance (denominator index sample)
            (treatedShare index sample) (controlShare index sample)
            (treatedDirectVariance index sample)
            (matchedControlVariance index sample)) l
        (fun _sample =>
          pattWeightedResidualVariance denominatorLimit treatedShareLimit
            controlShareLimit treatedDirectVarianceLimit
            matchedControlVarianceLimit))
    (hvarianceLimit_pos :
      0 < pattWeightedResidualVariance denominatorLimit treatedShareLimit
        controlShareLimit treatedDirectVarianceLimit matchedControlVarianceLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (pattWeightedResidualVariance (denominator index sample)
                (treatedShare index sample) (controlShare index sample)
                (treatedDirectVariance index sample)
                (matchedControlVariance index sample)))⁻¹)
          sampleLaw)
    (hvariance_positive :
      ∀ᶠ index in l, ∀ sample,
        0 < pattWeightedResidualVariance (denominator index sample)
          (treatedShare index sample) (controlShare index sample)
          (treatedDirectVariance index sample)
          (matchedControlVariance index sample))
    (hscale_positive : ∀ᶠ index in l, 0 < scale index)
    (habsolute :
      Tendsto
        (fun index =>
          eventProbabilityReal (sampleLawSeq index)
            (fun sample =>
              |waldStudentized (estimator index sample) (target index)
                (standardError
                  (pattWeightedResidualVariance (denominator index sample)
                    (treatedShare index sample) (controlShare index sample)
                    (treatedDirectVariance index sample)
                    (matchedControlVariance index sample)))
                (scale index)| ≤ criticalValue index)) l
        (nhds coverageLimit)) :
    TendstoInDistribution
        (fun index sample =>
          scaledStatistic index sample *
            (standardError
              (pattWeightedResidualVariance (denominator index sample)
                (treatedShare index sample) (controlShare index sample)
                (treatedDirectVariance index sample)
                (matchedControlVariance index sample)))⁻¹)
        l
        (fun limitSample =>
          limit limitSample *
            (standardError
              (pattWeightedResidualVariance denominatorLimit treatedShareLimit
                controlShareLimit treatedDirectVarianceLimit
                matchedControlVarianceLimit))⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      Tendsto
        (fun index =>
          eventProbabilityReal (sampleLawSeq index)
            (fun sample =>
              waldCovers (estimator index sample) (target index)
                (criticalValue index)
                (standardError
                  (pattWeightedResidualVariance (denominator index sample)
                    (treatedShare index sample) (controlShare index sample)
                    (treatedDirectVariance index sample)
                    (matchedControlVariance index sample)))
                (scale index)))
        l (nhds coverageLimit) := by
  exact absolutePositiveVarianceWaldCoverage_tendsto_of_inputs
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    scaledStatistic
    (fun index sample =>
      pattWeightedResidualVariance (denominator index sample)
        (treatedShare index sample) (controlShare index sample)
        (treatedDirectVariance index sample)
        (matchedControlVariance index sample))
    limit
    (pattWeightedResidualVariance denominatorLimit treatedShareLimit
      controlShareLimit treatedDirectVarianceLimit matchedControlVarianceLimit)
    hvarianceLimit_pos hscaled hvariance hinverse_meas
    { sampleLawSeq := sampleLawSeq
      estimator := estimator
      varianceEstimate := fun index sample =>
        pattWeightedResidualVariance (denominator index sample)
          (treatedShare index sample) (controlShare index sample)
          (treatedDirectVariance index sample)
          (matchedControlVariance index sample)
      target := target
      criticalValue := criticalValue
      scale := scale
      coverageLimit := coverageLimit
      variance_positive := hvariance_positive
      scale_positive := hscale_positive
      absoluteStudentizedProbability_tendsto := habsolute }

/--
Two-sided Wald coverage bridge with the PATT residual variance formula used
both for studentization and for the variance-based Wald standard error.
-/
theorem twoSidedPositiveVarianceWaldCoverage_tendsto_of_pattResidualVariance
    (sampleLawSeq : Index -> Measure Sample)
    (estimator scaledStatistic : Index -> Sample -> Real)
    (denominator treatedShare controlShare treatedDirectVariance
      matchedControlVariance : Index -> Sample -> Real)
    (target criticalValue scale : Index -> Real)
    (limit : LimitSample -> Real)
    (denominatorLimit treatedShareLimit controlShareLimit
      treatedDirectVarianceLimit matchedControlVarianceLimit : Real)
    (coverageLimit : Real)
    (hscaled :
      TendstoInDistribution scaledStatistic l limit
        (fun _index => sampleLaw) limitLaw)
    (hvariance :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          pattWeightedResidualVariance (denominator index sample)
            (treatedShare index sample) (controlShare index sample)
            (treatedDirectVariance index sample)
            (matchedControlVariance index sample)) l
        (fun _sample =>
          pattWeightedResidualVariance denominatorLimit treatedShareLimit
            controlShareLimit treatedDirectVarianceLimit
            matchedControlVarianceLimit))
    (hvarianceLimit_pos :
      0 < pattWeightedResidualVariance denominatorLimit treatedShareLimit
        controlShareLimit treatedDirectVarianceLimit matchedControlVarianceLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (pattWeightedResidualVariance (denominator index sample)
                (treatedShare index sample) (controlShare index sample)
                (treatedDirectVariance index sample)
                (matchedControlVariance index sample)))⁻¹)
          sampleLaw)
    (hvariance_positive :
      ∀ᶠ index in l, ∀ sample,
        0 < pattWeightedResidualVariance (denominator index sample)
          (treatedShare index sample) (controlShare index sample)
          (treatedDirectVariance index sample)
          (matchedControlVariance index sample))
    (hscale_positive : ∀ᶠ index in l, 0 < scale index)
    (htwoSided :
      Tendsto
        (fun index =>
          eventProbabilityReal (sampleLawSeq index)
            (fun sample =>
              -criticalValue index ≤
                  waldStudentized (estimator index sample) (target index)
                    (standardError
                      (pattWeightedResidualVariance (denominator index sample)
                        (treatedShare index sample)
                        (controlShare index sample)
                        (treatedDirectVariance index sample)
                        (matchedControlVariance index sample)))
                    (scale index) ∧
                waldStudentized (estimator index sample) (target index)
                  (standardError
                    (pattWeightedResidualVariance (denominator index sample)
                      (treatedShare index sample) (controlShare index sample)
                      (treatedDirectVariance index sample)
                      (matchedControlVariance index sample)))
                  (scale index) ≤ criticalValue index)) l
        (nhds coverageLimit)) :
    TendstoInDistribution
        (fun index sample =>
          scaledStatistic index sample *
            (standardError
              (pattWeightedResidualVariance (denominator index sample)
                (treatedShare index sample) (controlShare index sample)
                (treatedDirectVariance index sample)
                (matchedControlVariance index sample)))⁻¹)
        l
        (fun limitSample =>
          limit limitSample *
            (standardError
              (pattWeightedResidualVariance denominatorLimit treatedShareLimit
                controlShareLimit treatedDirectVarianceLimit
                matchedControlVarianceLimit))⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      Tendsto
        (fun index =>
          eventProbabilityReal (sampleLawSeq index)
            (fun sample =>
              waldCovers (estimator index sample) (target index)
                (criticalValue index)
                (standardError
                  (pattWeightedResidualVariance (denominator index sample)
                    (treatedShare index sample) (controlShare index sample)
                    (treatedDirectVariance index sample)
                    (matchedControlVariance index sample)))
                (scale index)))
        l (nhds coverageLimit) := by
  exact twoSidedPositiveVarianceWaldCoverage_tendsto_of_inputs
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    scaledStatistic
    (fun index sample =>
      pattWeightedResidualVariance (denominator index sample)
        (treatedShare index sample) (controlShare index sample)
        (treatedDirectVariance index sample)
        (matchedControlVariance index sample))
    limit
    (pattWeightedResidualVariance denominatorLimit treatedShareLimit
      controlShareLimit treatedDirectVarianceLimit matchedControlVarianceLimit)
    hvarianceLimit_pos hscaled hvariance hinverse_meas
    { sampleLawSeq := sampleLawSeq
      estimator := estimator
      varianceEstimate := fun index sample =>
        pattWeightedResidualVariance (denominator index sample)
          (treatedShare index sample) (controlShare index sample)
          (treatedDirectVariance index sample)
          (matchedControlVariance index sample)
      target := target
      criticalValue := criticalValue
      scale := scale
      coverageLimit := coverageLimit
      variance_positive := hvariance_positive
      scale_positive := hscale_positive
      twoSidedStudentizedProbability_tendsto := htwoSided }

/--
Absolute Wald coverage bridge with the two-arm residual variance formula,
deriving residual variance consistency from componentwise convergence in
probability before applying the positive-variance coverage bridge.
-/
theorem absolutePositiveVarianceWaldCoverage_tendsto_of_twoArmResidualVariance_components
    (sampleLawSeq : Index -> Measure Sample)
    (estimator scaledStatistic : Index -> Sample -> Real)
    (denominator treatedShare controlShare treatedArmVariance
      controlArmVariance : Index -> Sample -> Real)
    (target criticalValue scale : Index -> Real)
    (limit : LimitSample -> Real)
    (denominatorLimit treatedShareLimit controlShareLimit
      treatedVarianceLimit controlVarianceLimit : Real)
    (coverageLimit : Real)
    (hscaled :
      TendstoInDistribution scaledStatistic l limit
        (fun _index => sampleLaw) limitLaw)
    (hdenominator :
      TendstoInMeasure sampleLaw denominator l
        (fun _sample => denominatorLimit))
    (htreatedShare :
      TendstoInMeasure sampleLaw treatedShare l
        (fun _sample => treatedShareLimit))
    (hcontrolShare :
      TendstoInMeasure sampleLaw controlShare l
        (fun _sample => controlShareLimit))
    (htreatedVariance :
      TendstoInMeasure sampleLaw treatedArmVariance l
        (fun _sample => treatedVarianceLimit))
    (hcontrolVariance :
      TendstoInMeasure sampleLaw controlArmVariance l
        (fun _sample => controlVarianceLimit))
    (hdenominatorLimit : denominatorLimit ≠ 0)
    (hvarianceLimit_pos :
      0 < twoArmWeightedResidualVariance denominatorLimit treatedShareLimit
        controlShareLimit treatedVarianceLimit controlVarianceLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (twoArmWeightedResidualVariance (denominator index sample)
                (treatedShare index sample) (controlShare index sample)
                (treatedArmVariance index sample)
                (controlArmVariance index sample)))⁻¹)
          sampleLaw)
    (hvariance_positive :
      ∀ᶠ index in l, ∀ sample,
        0 < twoArmWeightedResidualVariance (denominator index sample)
          (treatedShare index sample) (controlShare index sample)
          (treatedArmVariance index sample) (controlArmVariance index sample))
    (hscale_positive : ∀ᶠ index in l, 0 < scale index)
    (habsolute :
      Tendsto
        (fun index =>
          eventProbabilityReal (sampleLawSeq index)
            (fun sample =>
              |waldStudentized (estimator index sample) (target index)
                (standardError
                  (twoArmWeightedResidualVariance (denominator index sample)
                    (treatedShare index sample) (controlShare index sample)
                    (treatedArmVariance index sample)
                    (controlArmVariance index sample)))
                (scale index)| ≤ criticalValue index)) l
        (nhds coverageLimit)) :
    TendstoInDistribution
        (fun index sample =>
          scaledStatistic index sample *
            (standardError
              (twoArmWeightedResidualVariance (denominator index sample)
                (treatedShare index sample) (controlShare index sample)
                (treatedArmVariance index sample)
                (controlArmVariance index sample)))⁻¹)
        l
        (fun limitSample =>
          limit limitSample *
            (standardError
              (twoArmWeightedResidualVariance denominatorLimit
                treatedShareLimit controlShareLimit treatedVarianceLimit
                controlVarianceLimit))⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      Tendsto
        (fun index =>
          eventProbabilityReal (sampleLawSeq index)
            (fun sample =>
              waldCovers (estimator index sample) (target index)
                (criticalValue index)
                (standardError
                  (twoArmWeightedResidualVariance (denominator index sample)
                    (treatedShare index sample) (controlShare index sample)
                    (treatedArmVariance index sample)
                    (controlArmVariance index sample)))
                (scale index)))
        l (nhds coverageLimit) := by
  exact absolutePositiveVarianceWaldCoverage_tendsto_of_twoArmResidualVariance
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    sampleLawSeq estimator scaledStatistic denominator treatedShare
    controlShare treatedArmVariance controlArmVariance target criticalValue
    scale limit denominatorLimit treatedShareLimit controlShareLimit
    treatedVarianceLimit controlVarianceLimit coverageLimit hscaled
    (tendstoInMeasure_twoArmWeightedResidualVariance_of_tendstoInMeasure
      (sampleLaw := sampleLaw) (l := l)
      denominator treatedShare controlShare treatedArmVariance
      controlArmVariance denominatorLimit treatedShareLimit controlShareLimit
      treatedVarianceLimit controlVarianceLimit hdenominator htreatedShare
      hcontrolShare htreatedVariance hcontrolVariance hdenominatorLimit)
    hvarianceLimit_pos hinverse_meas hvariance_positive hscale_positive
    habsolute

/--
Two-sided Wald coverage bridge with the two-arm residual variance formula,
deriving residual variance consistency from componentwise convergence in
probability before applying the positive-variance coverage bridge.
-/
theorem twoSidedPositiveVarianceWaldCoverage_tendsto_of_twoArmResidualVariance_components
    (sampleLawSeq : Index -> Measure Sample)
    (estimator scaledStatistic : Index -> Sample -> Real)
    (denominator treatedShare controlShare treatedArmVariance
      controlArmVariance : Index -> Sample -> Real)
    (target criticalValue scale : Index -> Real)
    (limit : LimitSample -> Real)
    (denominatorLimit treatedShareLimit controlShareLimit
      treatedVarianceLimit controlVarianceLimit : Real)
    (coverageLimit : Real)
    (hscaled :
      TendstoInDistribution scaledStatistic l limit
        (fun _index => sampleLaw) limitLaw)
    (hdenominator :
      TendstoInMeasure sampleLaw denominator l
        (fun _sample => denominatorLimit))
    (htreatedShare :
      TendstoInMeasure sampleLaw treatedShare l
        (fun _sample => treatedShareLimit))
    (hcontrolShare :
      TendstoInMeasure sampleLaw controlShare l
        (fun _sample => controlShareLimit))
    (htreatedVariance :
      TendstoInMeasure sampleLaw treatedArmVariance l
        (fun _sample => treatedVarianceLimit))
    (hcontrolVariance :
      TendstoInMeasure sampleLaw controlArmVariance l
        (fun _sample => controlVarianceLimit))
    (hdenominatorLimit : denominatorLimit ≠ 0)
    (hvarianceLimit_pos :
      0 < twoArmWeightedResidualVariance denominatorLimit treatedShareLimit
        controlShareLimit treatedVarianceLimit controlVarianceLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (twoArmWeightedResidualVariance (denominator index sample)
                (treatedShare index sample) (controlShare index sample)
                (treatedArmVariance index sample)
                (controlArmVariance index sample)))⁻¹)
          sampleLaw)
    (hvariance_positive :
      ∀ᶠ index in l, ∀ sample,
        0 < twoArmWeightedResidualVariance (denominator index sample)
          (treatedShare index sample) (controlShare index sample)
          (treatedArmVariance index sample) (controlArmVariance index sample))
    (hscale_positive : ∀ᶠ index in l, 0 < scale index)
    (htwoSided :
      Tendsto
        (fun index =>
          eventProbabilityReal (sampleLawSeq index)
            (fun sample =>
              -criticalValue index ≤
                  waldStudentized (estimator index sample) (target index)
                    (standardError
                      (twoArmWeightedResidualVariance
                        (denominator index sample)
                        (treatedShare index sample)
                        (controlShare index sample)
                        (treatedArmVariance index sample)
                        (controlArmVariance index sample)))
                    (scale index) ∧
                waldStudentized (estimator index sample) (target index)
                  (standardError
                    (twoArmWeightedResidualVariance (denominator index sample)
                      (treatedShare index sample) (controlShare index sample)
                      (treatedArmVariance index sample)
                      (controlArmVariance index sample)))
                  (scale index) ≤ criticalValue index)) l
        (nhds coverageLimit)) :
    TendstoInDistribution
        (fun index sample =>
          scaledStatistic index sample *
            (standardError
              (twoArmWeightedResidualVariance (denominator index sample)
                (treatedShare index sample) (controlShare index sample)
                (treatedArmVariance index sample)
                (controlArmVariance index sample)))⁻¹)
        l
        (fun limitSample =>
          limit limitSample *
            (standardError
              (twoArmWeightedResidualVariance denominatorLimit
                treatedShareLimit controlShareLimit treatedVarianceLimit
                controlVarianceLimit))⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      Tendsto
        (fun index =>
          eventProbabilityReal (sampleLawSeq index)
            (fun sample =>
              waldCovers (estimator index sample) (target index)
                (criticalValue index)
                (standardError
                  (twoArmWeightedResidualVariance (denominator index sample)
                    (treatedShare index sample) (controlShare index sample)
                    (treatedArmVariance index sample)
                    (controlArmVariance index sample)))
                (scale index)))
        l (nhds coverageLimit) := by
  exact twoSidedPositiveVarianceWaldCoverage_tendsto_of_twoArmResidualVariance
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    sampleLawSeq estimator scaledStatistic denominator treatedShare
    controlShare treatedArmVariance controlArmVariance target criticalValue
    scale limit denominatorLimit treatedShareLimit controlShareLimit
    treatedVarianceLimit controlVarianceLimit coverageLimit hscaled
    (tendstoInMeasure_twoArmWeightedResidualVariance_of_tendstoInMeasure
      (sampleLaw := sampleLaw) (l := l)
      denominator treatedShare controlShare treatedArmVariance
      controlArmVariance denominatorLimit treatedShareLimit controlShareLimit
      treatedVarianceLimit controlVarianceLimit hdenominator htreatedShare
      hcontrolShare htreatedVariance hcontrolVariance hdenominatorLimit)
    hvarianceLimit_pos hinverse_meas hvariance_positive hscale_positive
    htwoSided

/--
Absolute Wald coverage bridge with the PATT residual variance formula,
deriving residual variance consistency from componentwise convergence in
probability before applying the positive-variance coverage bridge.
-/
theorem absolutePositiveVarianceWaldCoverage_tendsto_of_pattResidualVariance_components
    (sampleLawSeq : Index -> Measure Sample)
    (estimator scaledStatistic : Index -> Sample -> Real)
    (denominator treatedShare controlShare treatedDirectVariance
      matchedControlVariance : Index -> Sample -> Real)
    (target criticalValue scale : Index -> Real)
    (limit : LimitSample -> Real)
    (denominatorLimit treatedShareLimit controlShareLimit
      treatedDirectVarianceLimit matchedControlVarianceLimit : Real)
    (coverageLimit : Real)
    (hscaled :
      TendstoInDistribution scaledStatistic l limit
        (fun _index => sampleLaw) limitLaw)
    (hdenominator :
      TendstoInMeasure sampleLaw denominator l
        (fun _sample => denominatorLimit))
    (htreatedShare :
      TendstoInMeasure sampleLaw treatedShare l
        (fun _sample => treatedShareLimit))
    (hcontrolShare :
      TendstoInMeasure sampleLaw controlShare l
        (fun _sample => controlShareLimit))
    (htreatedVariance :
      TendstoInMeasure sampleLaw treatedDirectVariance l
        (fun _sample => treatedDirectVarianceLimit))
    (hcontrolVariance :
      TendstoInMeasure sampleLaw matchedControlVariance l
        (fun _sample => matchedControlVarianceLimit))
    (hdenominatorLimit : denominatorLimit ≠ 0)
    (hvarianceLimit_pos :
      0 < pattWeightedResidualVariance denominatorLimit treatedShareLimit
        controlShareLimit treatedDirectVarianceLimit matchedControlVarianceLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (pattWeightedResidualVariance (denominator index sample)
                (treatedShare index sample) (controlShare index sample)
                (treatedDirectVariance index sample)
                (matchedControlVariance index sample)))⁻¹)
          sampleLaw)
    (hvariance_positive :
      ∀ᶠ index in l, ∀ sample,
        0 < pattWeightedResidualVariance (denominator index sample)
          (treatedShare index sample) (controlShare index sample)
          (treatedDirectVariance index sample)
          (matchedControlVariance index sample))
    (hscale_positive : ∀ᶠ index in l, 0 < scale index)
    (habsolute :
      Tendsto
        (fun index =>
          eventProbabilityReal (sampleLawSeq index)
            (fun sample =>
              |waldStudentized (estimator index sample) (target index)
                (standardError
                  (pattWeightedResidualVariance (denominator index sample)
                    (treatedShare index sample) (controlShare index sample)
                    (treatedDirectVariance index sample)
                    (matchedControlVariance index sample)))
                (scale index)| ≤ criticalValue index)) l
        (nhds coverageLimit)) :
    TendstoInDistribution
        (fun index sample =>
          scaledStatistic index sample *
            (standardError
              (pattWeightedResidualVariance (denominator index sample)
                (treatedShare index sample) (controlShare index sample)
                (treatedDirectVariance index sample)
                (matchedControlVariance index sample)))⁻¹)
        l
        (fun limitSample =>
          limit limitSample *
            (standardError
              (pattWeightedResidualVariance denominatorLimit treatedShareLimit
                controlShareLimit treatedDirectVarianceLimit
                matchedControlVarianceLimit))⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      Tendsto
        (fun index =>
          eventProbabilityReal (sampleLawSeq index)
            (fun sample =>
              waldCovers (estimator index sample) (target index)
                (criticalValue index)
                (standardError
                  (pattWeightedResidualVariance (denominator index sample)
                    (treatedShare index sample) (controlShare index sample)
                    (treatedDirectVariance index sample)
                    (matchedControlVariance index sample)))
                (scale index)))
        l (nhds coverageLimit) := by
  exact absolutePositiveVarianceWaldCoverage_tendsto_of_pattResidualVariance
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    sampleLawSeq estimator scaledStatistic denominator treatedShare
    controlShare treatedDirectVariance matchedControlVariance target
    criticalValue scale limit denominatorLimit treatedShareLimit
    controlShareLimit treatedDirectVarianceLimit matchedControlVarianceLimit
    coverageLimit hscaled
    (tendstoInMeasure_pattWeightedResidualVariance_of_tendstoInMeasure
      (sampleLaw := sampleLaw) (l := l)
      denominator treatedShare controlShare treatedDirectVariance
      matchedControlVariance denominatorLimit treatedShareLimit
      controlShareLimit treatedDirectVarianceLimit matchedControlVarianceLimit
      hdenominator htreatedShare hcontrolShare htreatedVariance
      hcontrolVariance hdenominatorLimit)
    hvarianceLimit_pos hinverse_meas hvariance_positive hscale_positive
    habsolute

/--
Two-sided Wald coverage bridge with the PATT residual variance formula,
deriving residual variance consistency from componentwise convergence in
probability before applying the positive-variance coverage bridge.
-/
theorem twoSidedPositiveVarianceWaldCoverage_tendsto_of_pattResidualVariance_components
    (sampleLawSeq : Index -> Measure Sample)
    (estimator scaledStatistic : Index -> Sample -> Real)
    (denominator treatedShare controlShare treatedDirectVariance
      matchedControlVariance : Index -> Sample -> Real)
    (target criticalValue scale : Index -> Real)
    (limit : LimitSample -> Real)
    (denominatorLimit treatedShareLimit controlShareLimit
      treatedDirectVarianceLimit matchedControlVarianceLimit : Real)
    (coverageLimit : Real)
    (hscaled :
      TendstoInDistribution scaledStatistic l limit
        (fun _index => sampleLaw) limitLaw)
    (hdenominator :
      TendstoInMeasure sampleLaw denominator l
        (fun _sample => denominatorLimit))
    (htreatedShare :
      TendstoInMeasure sampleLaw treatedShare l
        (fun _sample => treatedShareLimit))
    (hcontrolShare :
      TendstoInMeasure sampleLaw controlShare l
        (fun _sample => controlShareLimit))
    (htreatedVariance :
      TendstoInMeasure sampleLaw treatedDirectVariance l
        (fun _sample => treatedDirectVarianceLimit))
    (hcontrolVariance :
      TendstoInMeasure sampleLaw matchedControlVariance l
        (fun _sample => matchedControlVarianceLimit))
    (hdenominatorLimit : denominatorLimit ≠ 0)
    (hvarianceLimit_pos :
      0 < pattWeightedResidualVariance denominatorLimit treatedShareLimit
        controlShareLimit treatedDirectVarianceLimit matchedControlVarianceLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (pattWeightedResidualVariance (denominator index sample)
                (treatedShare index sample) (controlShare index sample)
                (treatedDirectVariance index sample)
                (matchedControlVariance index sample)))⁻¹)
          sampleLaw)
    (hvariance_positive :
      ∀ᶠ index in l, ∀ sample,
        0 < pattWeightedResidualVariance (denominator index sample)
          (treatedShare index sample) (controlShare index sample)
          (treatedDirectVariance index sample)
          (matchedControlVariance index sample))
    (hscale_positive : ∀ᶠ index in l, 0 < scale index)
    (htwoSided :
      Tendsto
        (fun index =>
          eventProbabilityReal (sampleLawSeq index)
            (fun sample =>
              -criticalValue index ≤
                  waldStudentized (estimator index sample) (target index)
                    (standardError
                      (pattWeightedResidualVariance (denominator index sample)
                        (treatedShare index sample)
                        (controlShare index sample)
                        (treatedDirectVariance index sample)
                        (matchedControlVariance index sample)))
                    (scale index) ∧
                waldStudentized (estimator index sample) (target index)
                  (standardError
                    (pattWeightedResidualVariance (denominator index sample)
                      (treatedShare index sample) (controlShare index sample)
                      (treatedDirectVariance index sample)
                      (matchedControlVariance index sample)))
                  (scale index) ≤ criticalValue index)) l
        (nhds coverageLimit)) :
    TendstoInDistribution
        (fun index sample =>
          scaledStatistic index sample *
            (standardError
              (pattWeightedResidualVariance (denominator index sample)
                (treatedShare index sample) (controlShare index sample)
                (treatedDirectVariance index sample)
                (matchedControlVariance index sample)))⁻¹)
        l
        (fun limitSample =>
          limit limitSample *
            (standardError
              (pattWeightedResidualVariance denominatorLimit treatedShareLimit
                controlShareLimit treatedDirectVarianceLimit
                matchedControlVarianceLimit))⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      Tendsto
        (fun index =>
          eventProbabilityReal (sampleLawSeq index)
            (fun sample =>
              waldCovers (estimator index sample) (target index)
                (criticalValue index)
                (standardError
                  (pattWeightedResidualVariance (denominator index sample)
                    (treatedShare index sample) (controlShare index sample)
                    (treatedDirectVariance index sample)
                    (matchedControlVariance index sample)))
                (scale index)))
        l (nhds coverageLimit) := by
  exact twoSidedPositiveVarianceWaldCoverage_tendsto_of_pattResidualVariance
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    sampleLawSeq estimator scaledStatistic denominator treatedShare
    controlShare treatedDirectVariance matchedControlVariance target
    criticalValue scale limit denominatorLimit treatedShareLimit
    controlShareLimit treatedDirectVarianceLimit matchedControlVarianceLimit
    coverageLimit hscaled
    (tendstoInMeasure_pattWeightedResidualVariance_of_tendstoInMeasure
      (sampleLaw := sampleLaw) (l := l)
      denominator treatedShare controlShare treatedDirectVariance
      matchedControlVariance denominatorLimit treatedShareLimit
      controlShareLimit treatedDirectVarianceLimit matchedControlVarianceLimit
      hdenominator htreatedShare hcontrolShare htreatedVariance
      hcontrolVariance hdenominatorLimit)
    hvarianceLimit_pos hinverse_meas hvariance_positive hscale_positive
    htwoSided

end WDSM
end Matching
end StatInference
