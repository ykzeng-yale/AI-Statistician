import StatInference.Matching.WDSM.PositiveVarianceWaldCoverageComponentPositivity
import StatInference.Matching.WDSM.VarianceLimitComponentPositivity

/-!
# Wald coverage from componentwise limiting-variance positivity

This module composes the positive-variance Wald coverage bridges with
componentwise positivity facts for both the limiting variance and the
finite-sample variance estimates.  The first slice handles oracle variance,
including both heterogeneity-positive and residual-positive routes.
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

/-! ## Oracle variance -/

/--
Absolute oracle-variance Wald coverage where the positive limiting variance is
derived from positive heterogeneity and nonnegative residual limits.
-/
theorem absolutePositiveVarianceWaldCoverage_tendsto_of_oracleVariance_components_heterogeneity_pos_limit
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
    (hheterogeneityLimit_pos : 0 < heterogeneityLimit)
    (hresidualLimit_nonneg : 0 ≤ residualLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (oracleVariance (heterogeneity index sample)
                (residual index sample)))⁻¹)
          sampleLaw)
    (hheterogeneity_pos :
      ∀ᶠ index in l, ∀ sample, 0 < heterogeneity index sample)
    (hresidual_nonneg :
      ∀ᶠ index in l, ∀ sample, 0 ≤ residual index sample)
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
  exact
    absolutePositiveVarianceWaldCoverage_tendsto_of_oracleVariance_components_heterogeneity_pos
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      sampleLawSeq estimator scaledStatistic heterogeneity residual target
      criticalValue scale limit heterogeneityLimit residualLimit coverageLimit
      hscaled hheterogeneity hresidual
      (oracleVarianceLimit_pos_of_heterogeneity_pos heterogeneityLimit
        residualLimit hheterogeneityLimit_pos hresidualLimit_nonneg)
      hinverse_meas hheterogeneity_pos hresidual_nonneg hscale_positive
      habsolute

/--
Two-sided oracle-variance Wald coverage where the positive limiting variance
is derived from positive heterogeneity and nonnegative residual limits.
-/
theorem twoSidedPositiveVarianceWaldCoverage_tendsto_of_oracleVariance_components_heterogeneity_pos_limit
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
    (hheterogeneityLimit_pos : 0 < heterogeneityLimit)
    (hresidualLimit_nonneg : 0 ≤ residualLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (oracleVariance (heterogeneity index sample)
                (residual index sample)))⁻¹)
          sampleLaw)
    (hheterogeneity_pos :
      ∀ᶠ index in l, ∀ sample, 0 < heterogeneity index sample)
    (hresidual_nonneg :
      ∀ᶠ index in l, ∀ sample, 0 ≤ residual index sample)
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
  exact
    twoSidedPositiveVarianceWaldCoverage_tendsto_of_oracleVariance_components_heterogeneity_pos
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      sampleLawSeq estimator scaledStatistic heterogeneity residual target
      criticalValue scale limit heterogeneityLimit residualLimit coverageLimit
      hscaled hheterogeneity hresidual
      (oracleVarianceLimit_pos_of_heterogeneity_pos heterogeneityLimit
        residualLimit hheterogeneityLimit_pos hresidualLimit_nonneg)
      hinverse_meas hheterogeneity_pos hresidual_nonneg hscale_positive
      htwoSided

/--
Absolute oracle-variance Wald coverage where the positive limiting variance is
derived from positive residual and nonnegative heterogeneity limits.
-/
theorem absolutePositiveVarianceWaldCoverage_tendsto_of_oracleVariance_components_residual_pos_limit
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
    (hheterogeneityLimit_nonneg : 0 ≤ heterogeneityLimit)
    (hresidualLimit_pos : 0 < residualLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (oracleVariance (heterogeneity index sample)
                (residual index sample)))⁻¹)
          sampleLaw)
    (hheterogeneity_nonneg :
      ∀ᶠ index in l, ∀ sample, 0 ≤ heterogeneity index sample)
    (hresidual_pos :
      ∀ᶠ index in l, ∀ sample, 0 < residual index sample)
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
  exact absolutePositiveVarianceWaldCoverage_tendsto_of_oracleVariance_components
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    sampleLawSeq estimator scaledStatistic heterogeneity residual target
    criticalValue scale limit heterogeneityLimit residualLimit coverageLimit
    hscaled hheterogeneity hresidual
    (oracleVarianceLimit_pos_of_residual_pos heterogeneityLimit residualLimit
      hheterogeneityLimit_nonneg hresidualLimit_pos)
    hinverse_meas
    (eventually_oracleVariance_positive_of_eventually_residual_pos
      (l := l) heterogeneity residual hheterogeneity_nonneg hresidual_pos)
    hscale_positive habsolute

/--
Two-sided oracle-variance Wald coverage where the positive limiting variance is
derived from positive residual and nonnegative heterogeneity limits.
-/
theorem twoSidedPositiveVarianceWaldCoverage_tendsto_of_oracleVariance_components_residual_pos_limit
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
    (hheterogeneityLimit_nonneg : 0 ≤ heterogeneityLimit)
    (hresidualLimit_pos : 0 < residualLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (oracleVariance (heterogeneity index sample)
                (residual index sample)))⁻¹)
          sampleLaw)
    (hheterogeneity_nonneg :
      ∀ᶠ index in l, ∀ sample, 0 ≤ heterogeneity index sample)
    (hresidual_pos :
      ∀ᶠ index in l, ∀ sample, 0 < residual index sample)
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
  exact twoSidedPositiveVarianceWaldCoverage_tendsto_of_oracleVariance_components
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    sampleLawSeq estimator scaledStatistic heterogeneity residual target
    criticalValue scale limit heterogeneityLimit residualLimit coverageLimit
    hscaled hheterogeneity hresidual
    (oracleVarianceLimit_pos_of_residual_pos heterogeneityLimit residualLimit
      hheterogeneityLimit_nonneg hresidualLimit_pos)
    hinverse_meas
    (eventually_oracleVariance_positive_of_eventually_residual_pos
      (l := l) heterogeneity residual hheterogeneity_nonneg hresidual_pos)
    hscale_positive htwoSided

/-! ## Estimated-score variance -/

/--
Absolute Wald coverage with changing-law estimated-score variance where the
positive limiting variance is derived from strict projection slack and
nonnegative target drift.
-/
theorem absolutePositiveVarianceWaldCoverage_tendsto_of_estimatedScoreVariance_components_projection_lt_limit
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
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hdriftLimit_nonneg : 0 ≤ targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (hprojection_lt_oracle :
      ∀ᶠ index in l, ∀ sample,
        projectionReduction index sample < oracle index sample)
    (hdrift_nonneg :
      ∀ᶠ index in l, ∀ sample, 0 ≤ targetDrift index sample)
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
  exact
    absolutePositiveVarianceWaldCoverage_tendsto_of_estimatedScoreVariance_components_projection_lt
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      sampleLawSeq estimator scaledStatistic oracle projectionReduction
      targetDrift target criticalValue scale limit oracleLimit projectionLimit
      targetDriftLimit coverageLimit hscaled horacle hprojection hdrift
      (estimatedScoreVarianceLimit_pos_of_projection_lt_oracle_of_drift_nonneg
        oracleLimit projectionLimit targetDriftLimit
        hprojectionLimit_lt_oracle hdriftLimit_nonneg)
      hinverse_meas hprojection_lt_oracle hdrift_nonneg hscale_positive
      habsolute

/--
Two-sided Wald coverage with changing-law estimated-score variance where the
positive limiting variance is derived from strict projection slack and
nonnegative target drift.
-/
theorem twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimatedScoreVariance_components_projection_lt_limit
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
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hdriftLimit_nonneg : 0 ≤ targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (hprojection_lt_oracle :
      ∀ᶠ index in l, ∀ sample,
        projectionReduction index sample < oracle index sample)
    (hdrift_nonneg :
      ∀ᶠ index in l, ∀ sample, 0 ≤ targetDrift index sample)
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
  exact
    twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimatedScoreVariance_components_projection_lt
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      sampleLawSeq estimator scaledStatistic oracle projectionReduction
      targetDrift target criticalValue scale limit oracleLimit projectionLimit
      targetDriftLimit coverageLimit hscaled horacle hprojection hdrift
      (estimatedScoreVarianceLimit_pos_of_projection_lt_oracle_of_drift_nonneg
        oracleLimit projectionLimit targetDriftLimit
        hprojectionLimit_lt_oracle hdriftLimit_nonneg)
      hinverse_meas hprojection_lt_oracle hdrift_nonneg hscale_positive
      htwoSided

/--
Absolute Wald coverage with changing-law estimated-score variance where weak
projection slack is rescued by positive moving-target drift.
-/
theorem absolutePositiveVarianceWaldCoverage_tendsto_of_estimatedScoreVariance_components_projection_le_drift_pos_limit
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
    (hprojectionLimit_le_oracle : projectionLimit ≤ oracleLimit)
    (hdriftLimit_pos : 0 < targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (hprojection_le_oracle :
      ∀ᶠ index in l, ∀ sample,
        projectionReduction index sample ≤ oracle index sample)
    (hdrift_pos :
      ∀ᶠ index in l, ∀ sample, 0 < targetDrift index sample)
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
  exact
    absolutePositiveVarianceWaldCoverage_tendsto_of_estimatedScoreVariance_components
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      sampleLawSeq estimator scaledStatistic oracle projectionReduction
      targetDrift target criticalValue scale limit oracleLimit projectionLimit
      targetDriftLimit coverageLimit hscaled horacle hprojection hdrift
      (estimatedScoreVarianceLimit_pos_of_projection_le_oracle_of_drift_pos
        oracleLimit projectionLimit targetDriftLimit hprojectionLimit_le_oracle
        hdriftLimit_pos)
      hinverse_meas
      (eventually_estimatedScoreVariance_positive_of_eventually_projection_le_oracle_of_drift_pos
        (l := l) oracle projectionReduction targetDrift
        hprojection_le_oracle hdrift_pos)
      hscale_positive habsolute

/--
Two-sided Wald coverage with changing-law estimated-score variance where weak
projection slack is rescued by positive moving-target drift.
-/
theorem twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimatedScoreVariance_components_projection_le_drift_pos_limit
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
    (hprojectionLimit_le_oracle : projectionLimit ≤ oracleLimit)
    (hdriftLimit_pos : 0 < targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (hprojection_le_oracle :
      ∀ᶠ index in l, ∀ sample,
        projectionReduction index sample ≤ oracle index sample)
    (hdrift_pos :
      ∀ᶠ index in l, ∀ sample, 0 < targetDrift index sample)
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
  exact
    twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimatedScoreVariance_components
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      sampleLawSeq estimator scaledStatistic oracle projectionReduction
      targetDrift target criticalValue scale limit oracleLimit projectionLimit
      targetDriftLimit coverageLimit hscaled horacle hprojection hdrift
      (estimatedScoreVarianceLimit_pos_of_projection_le_oracle_of_drift_pos
        oracleLimit projectionLimit targetDriftLimit hprojectionLimit_le_oracle
        hdriftLimit_pos)
      hinverse_meas
      (eventually_estimatedScoreVariance_positive_of_eventually_projection_le_oracle_of_drift_pos
        (l := l) oracle projectionReduction targetDrift
        hprojection_le_oracle hdrift_pos)
      hscale_positive htwoSided

/--
Absolute Wald coverage with fixed-law estimated-score variance where the
positive limiting variance is derived from strict projection slack.
-/
theorem absolutePositiveVarianceWaldCoverage_tendsto_of_fixedLawEstimatedScoreVariance_components_projection_lt_limit
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
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (hprojection_lt_oracle :
      ∀ᶠ index in l, ∀ sample,
        projectionReduction index sample < oracle index sample)
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
  exact
    absolutePositiveVarianceWaldCoverage_tendsto_of_fixedLawEstimatedScoreVariance_components_projection_lt
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      sampleLawSeq estimator scaledStatistic oracle projectionReduction target
      criticalValue scale limit oracleLimit projectionLimit coverageLimit
      hscaled horacle hprojection
      (fixedLawEstimatedScoreVarianceLimit_pos_of_projection_lt_oracle
        oracleLimit projectionLimit hprojectionLimit_lt_oracle)
      hinverse_meas hprojection_lt_oracle hscale_positive habsolute

/--
Two-sided Wald coverage with fixed-law estimated-score variance where the
positive limiting variance is derived from strict projection slack.
-/
theorem twoSidedPositiveVarianceWaldCoverage_tendsto_of_fixedLawEstimatedScoreVariance_components_projection_lt_limit
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
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (hprojection_lt_oracle :
      ∀ᶠ index in l, ∀ sample,
        projectionReduction index sample < oracle index sample)
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
  exact
    twoSidedPositiveVarianceWaldCoverage_tendsto_of_fixedLawEstimatedScoreVariance_components_projection_lt
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      sampleLawSeq estimator scaledStatistic oracle projectionReduction target
      criticalValue scale limit oracleLimit projectionLimit coverageLimit
      hscaled horacle hprojection
      (fixedLawEstimatedScoreVarianceLimit_pos_of_projection_lt_oracle
        oracleLimit projectionLimit hprojectionLimit_lt_oracle)
      hinverse_meas hprojection_lt_oracle hscale_positive htwoSided

/-! ## Two-arm residual variance -/

/--
Absolute two-arm residual-variance Wald coverage where the positive limiting
variance is derived from positive treated share and treated residual-variance
limits.
-/
theorem absolutePositiveVarianceWaldCoverage_tendsto_of_twoArmResidualVariance_components_treated_pos_limit
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
    (htreatedShareLimit_pos : 0 < treatedShareLimit)
    (hcontrolShareLimit_nonneg : 0 ≤ controlShareLimit)
    (htreatedVarianceLimit_pos : 0 < treatedVarianceLimit)
    (hcontrolVarianceLimit_nonneg : 0 ≤ controlVarianceLimit)
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
    (hdenominator_ne :
      ∀ᶠ index in l, ∀ sample, denominator index sample ≠ 0)
    (htreatedShare_pos :
      ∀ᶠ index in l, ∀ sample, 0 < treatedShare index sample)
    (hcontrolShare_nonneg :
      ∀ᶠ index in l, ∀ sample, 0 ≤ controlShare index sample)
    (htreatedVariance_pos :
      ∀ᶠ index in l, ∀ sample, 0 < treatedArmVariance index sample)
    (hcontrolVariance_nonneg :
      ∀ᶠ index in l, ∀ sample, 0 ≤ controlArmVariance index sample)
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
  exact
    absolutePositiveVarianceWaldCoverage_tendsto_of_twoArmResidualVariance_components_treated_pos
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      sampleLawSeq estimator scaledStatistic denominator treatedShare
      controlShare treatedArmVariance controlArmVariance target criticalValue
      scale limit denominatorLimit treatedShareLimit controlShareLimit
      treatedVarianceLimit controlVarianceLimit coverageLimit hscaled
      hdenominator htreatedShare hcontrolShare htreatedVariance
      hcontrolVariance hdenominatorLimit
      (twoArmWeightedResidualVarianceLimit_pos_of_treated_pos
        denominatorLimit treatedShareLimit controlShareLimit
        treatedVarianceLimit controlVarianceLimit hdenominatorLimit
        htreatedShareLimit_pos hcontrolShareLimit_nonneg
        htreatedVarianceLimit_pos hcontrolVarianceLimit_nonneg)
      hinverse_meas hdenominator_ne htreatedShare_pos
      hcontrolShare_nonneg htreatedVariance_pos hcontrolVariance_nonneg
      hscale_positive habsolute

/--
Two-sided two-arm residual-variance Wald coverage where the positive limiting
variance is derived from positive treated share and treated residual-variance
limits.
-/
theorem twoSidedPositiveVarianceWaldCoverage_tendsto_of_twoArmResidualVariance_components_treated_pos_limit
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
    (htreatedShareLimit_pos : 0 < treatedShareLimit)
    (hcontrolShareLimit_nonneg : 0 ≤ controlShareLimit)
    (htreatedVarianceLimit_pos : 0 < treatedVarianceLimit)
    (hcontrolVarianceLimit_nonneg : 0 ≤ controlVarianceLimit)
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
    (hdenominator_ne :
      ∀ᶠ index in l, ∀ sample, denominator index sample ≠ 0)
    (htreatedShare_pos :
      ∀ᶠ index in l, ∀ sample, 0 < treatedShare index sample)
    (hcontrolShare_nonneg :
      ∀ᶠ index in l, ∀ sample, 0 ≤ controlShare index sample)
    (htreatedVariance_pos :
      ∀ᶠ index in l, ∀ sample, 0 < treatedArmVariance index sample)
    (hcontrolVariance_nonneg :
      ∀ᶠ index in l, ∀ sample, 0 ≤ controlArmVariance index sample)
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
  exact
    twoSidedPositiveVarianceWaldCoverage_tendsto_of_twoArmResidualVariance_components_treated_pos
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      sampleLawSeq estimator scaledStatistic denominator treatedShare
      controlShare treatedArmVariance controlArmVariance target criticalValue
      scale limit denominatorLimit treatedShareLimit controlShareLimit
      treatedVarianceLimit controlVarianceLimit coverageLimit hscaled
      hdenominator htreatedShare hcontrolShare htreatedVariance
      hcontrolVariance hdenominatorLimit
      (twoArmWeightedResidualVarianceLimit_pos_of_treated_pos
        denominatorLimit treatedShareLimit controlShareLimit
        treatedVarianceLimit controlVarianceLimit hdenominatorLimit
        htreatedShareLimit_pos hcontrolShareLimit_nonneg
        htreatedVarianceLimit_pos hcontrolVarianceLimit_nonneg)
      hinverse_meas hdenominator_ne htreatedShare_pos
      hcontrolShare_nonneg htreatedVariance_pos hcontrolVariance_nonneg
      hscale_positive htwoSided

/--
Absolute two-arm residual-variance Wald coverage where the positive limiting
variance is derived from positive control share and control residual-variance
limits.
-/
theorem absolutePositiveVarianceWaldCoverage_tendsto_of_twoArmResidualVariance_components_control_pos_limit
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
    (htreatedShareLimit_nonneg : 0 ≤ treatedShareLimit)
    (hcontrolShareLimit_pos : 0 < controlShareLimit)
    (htreatedVarianceLimit_nonneg : 0 ≤ treatedVarianceLimit)
    (hcontrolVarianceLimit_pos : 0 < controlVarianceLimit)
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
    (hdenominator_ne :
      ∀ᶠ index in l, ∀ sample, denominator index sample ≠ 0)
    (htreatedShare_nonneg :
      ∀ᶠ index in l, ∀ sample, 0 ≤ treatedShare index sample)
    (hcontrolShare_pos :
      ∀ᶠ index in l, ∀ sample, 0 < controlShare index sample)
    (htreatedVariance_nonneg :
      ∀ᶠ index in l, ∀ sample, 0 ≤ treatedArmVariance index sample)
    (hcontrolVariance_pos :
      ∀ᶠ index in l, ∀ sample, 0 < controlArmVariance index sample)
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
  exact
    absolutePositiveVarianceWaldCoverage_tendsto_of_twoArmResidualVariance_components_control_pos
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      sampleLawSeq estimator scaledStatistic denominator treatedShare
      controlShare treatedArmVariance controlArmVariance target criticalValue
      scale limit denominatorLimit treatedShareLimit controlShareLimit
      treatedVarianceLimit controlVarianceLimit coverageLimit hscaled
      hdenominator htreatedShare hcontrolShare htreatedVariance
      hcontrolVariance hdenominatorLimit
      (twoArmWeightedResidualVarianceLimit_pos_of_control_pos
        denominatorLimit treatedShareLimit controlShareLimit
        treatedVarianceLimit controlVarianceLimit hdenominatorLimit
        htreatedShareLimit_nonneg hcontrolShareLimit_pos
        htreatedVarianceLimit_nonneg hcontrolVarianceLimit_pos)
      hinverse_meas hdenominator_ne htreatedShare_nonneg
      hcontrolShare_pos htreatedVariance_nonneg hcontrolVariance_pos
      hscale_positive habsolute

/--
Two-sided two-arm residual-variance Wald coverage where the positive limiting
variance is derived from positive control share and control residual-variance
limits.
-/
theorem twoSidedPositiveVarianceWaldCoverage_tendsto_of_twoArmResidualVariance_components_control_pos_limit
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
    (htreatedShareLimit_nonneg : 0 ≤ treatedShareLimit)
    (hcontrolShareLimit_pos : 0 < controlShareLimit)
    (htreatedVarianceLimit_nonneg : 0 ≤ treatedVarianceLimit)
    (hcontrolVarianceLimit_pos : 0 < controlVarianceLimit)
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
    (hdenominator_ne :
      ∀ᶠ index in l, ∀ sample, denominator index sample ≠ 0)
    (htreatedShare_nonneg :
      ∀ᶠ index in l, ∀ sample, 0 ≤ treatedShare index sample)
    (hcontrolShare_pos :
      ∀ᶠ index in l, ∀ sample, 0 < controlShare index sample)
    (htreatedVariance_nonneg :
      ∀ᶠ index in l, ∀ sample, 0 ≤ treatedArmVariance index sample)
    (hcontrolVariance_pos :
      ∀ᶠ index in l, ∀ sample, 0 < controlArmVariance index sample)
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
  exact
    twoSidedPositiveVarianceWaldCoverage_tendsto_of_twoArmResidualVariance_components_control_pos
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      sampleLawSeq estimator scaledStatistic denominator treatedShare
      controlShare treatedArmVariance controlArmVariance target criticalValue
      scale limit denominatorLimit treatedShareLimit controlShareLimit
      treatedVarianceLimit controlVarianceLimit coverageLimit hscaled
      hdenominator htreatedShare hcontrolShare htreatedVariance
      hcontrolVariance hdenominatorLimit
      (twoArmWeightedResidualVarianceLimit_pos_of_control_pos
        denominatorLimit treatedShareLimit controlShareLimit
        treatedVarianceLimit controlVarianceLimit hdenominatorLimit
        htreatedShareLimit_nonneg hcontrolShareLimit_pos
        htreatedVarianceLimit_nonneg hcontrolVarianceLimit_pos)
      hinverse_meas hdenominator_ne htreatedShare_nonneg
      hcontrolShare_pos htreatedVariance_nonneg hcontrolVariance_pos
      hscale_positive htwoSided

/-! ## PATT residual variance -/

/--
Absolute PATT residual-variance Wald coverage where the positive limiting
variance is derived from positive treated share and treated direct
residual-variance limits.
-/
theorem absolutePositiveVarianceWaldCoverage_tendsto_of_pattResidualVariance_components_treated_pos_limit
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
    (htreatedShareLimit_pos : 0 < treatedShareLimit)
    (hcontrolShareLimit_nonneg : 0 ≤ controlShareLimit)
    (htreatedVarianceLimit_pos : 0 < treatedDirectVarianceLimit)
    (hcontrolVarianceLimit_nonneg : 0 ≤ matchedControlVarianceLimit)
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
    (hdenominator_ne :
      ∀ᶠ index in l, ∀ sample, denominator index sample ≠ 0)
    (htreatedShare_pos :
      ∀ᶠ index in l, ∀ sample, 0 < treatedShare index sample)
    (hcontrolShare_nonneg :
      ∀ᶠ index in l, ∀ sample, 0 ≤ controlShare index sample)
    (htreatedVariance_pos :
      ∀ᶠ index in l, ∀ sample, 0 < treatedDirectVariance index sample)
    (hcontrolVariance_nonneg :
      ∀ᶠ index in l, ∀ sample, 0 ≤ matchedControlVariance index sample)
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
  exact
    absolutePositiveVarianceWaldCoverage_tendsto_of_pattResidualVariance_components_treated_pos
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      sampleLawSeq estimator scaledStatistic denominator treatedShare
      controlShare treatedDirectVariance matchedControlVariance target
      criticalValue scale limit denominatorLimit treatedShareLimit
      controlShareLimit treatedDirectVarianceLimit matchedControlVarianceLimit
      coverageLimit hscaled hdenominator htreatedShare hcontrolShare
      htreatedVariance hcontrolVariance hdenominatorLimit
      (pattWeightedResidualVarianceLimit_pos_of_treated_pos
        denominatorLimit treatedShareLimit controlShareLimit
        treatedDirectVarianceLimit matchedControlVarianceLimit
        hdenominatorLimit htreatedShareLimit_pos hcontrolShareLimit_nonneg
        htreatedVarianceLimit_pos hcontrolVarianceLimit_nonneg)
      hinverse_meas hdenominator_ne htreatedShare_pos
      hcontrolShare_nonneg htreatedVariance_pos hcontrolVariance_nonneg
      hscale_positive habsolute

/--
Two-sided PATT residual-variance Wald coverage where the positive limiting
variance is derived from positive treated share and treated direct
residual-variance limits.
-/
theorem twoSidedPositiveVarianceWaldCoverage_tendsto_of_pattResidualVariance_components_treated_pos_limit
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
    (htreatedShareLimit_pos : 0 < treatedShareLimit)
    (hcontrolShareLimit_nonneg : 0 ≤ controlShareLimit)
    (htreatedVarianceLimit_pos : 0 < treatedDirectVarianceLimit)
    (hcontrolVarianceLimit_nonneg : 0 ≤ matchedControlVarianceLimit)
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
    (hdenominator_ne :
      ∀ᶠ index in l, ∀ sample, denominator index sample ≠ 0)
    (htreatedShare_pos :
      ∀ᶠ index in l, ∀ sample, 0 < treatedShare index sample)
    (hcontrolShare_nonneg :
      ∀ᶠ index in l, ∀ sample, 0 ≤ controlShare index sample)
    (htreatedVariance_pos :
      ∀ᶠ index in l, ∀ sample, 0 < treatedDirectVariance index sample)
    (hcontrolVariance_nonneg :
      ∀ᶠ index in l, ∀ sample, 0 ≤ matchedControlVariance index sample)
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
  exact
    twoSidedPositiveVarianceWaldCoverage_tendsto_of_pattResidualVariance_components_treated_pos
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      sampleLawSeq estimator scaledStatistic denominator treatedShare
      controlShare treatedDirectVariance matchedControlVariance target
      criticalValue scale limit denominatorLimit treatedShareLimit
      controlShareLimit treatedDirectVarianceLimit matchedControlVarianceLimit
      coverageLimit hscaled hdenominator htreatedShare hcontrolShare
      htreatedVariance hcontrolVariance hdenominatorLimit
      (pattWeightedResidualVarianceLimit_pos_of_treated_pos
        denominatorLimit treatedShareLimit controlShareLimit
        treatedDirectVarianceLimit matchedControlVarianceLimit
        hdenominatorLimit htreatedShareLimit_pos hcontrolShareLimit_nonneg
        htreatedVarianceLimit_pos hcontrolVarianceLimit_nonneg)
      hinverse_meas hdenominator_ne htreatedShare_pos
      hcontrolShare_nonneg htreatedVariance_pos hcontrolVariance_nonneg
      hscale_positive htwoSided

/--
Absolute PATT residual-variance Wald coverage where the positive limiting
variance is derived from positive control share and matched-control
residual-variance limits.
-/
theorem absolutePositiveVarianceWaldCoverage_tendsto_of_pattResidualVariance_components_control_pos_limit
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
    (htreatedShareLimit_nonneg : 0 ≤ treatedShareLimit)
    (hcontrolShareLimit_pos : 0 < controlShareLimit)
    (htreatedVarianceLimit_nonneg : 0 ≤ treatedDirectVarianceLimit)
    (hcontrolVarianceLimit_pos : 0 < matchedControlVarianceLimit)
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
    (hdenominator_ne :
      ∀ᶠ index in l, ∀ sample, denominator index sample ≠ 0)
    (htreatedShare_nonneg :
      ∀ᶠ index in l, ∀ sample, 0 ≤ treatedShare index sample)
    (hcontrolShare_pos :
      ∀ᶠ index in l, ∀ sample, 0 < controlShare index sample)
    (htreatedVariance_nonneg :
      ∀ᶠ index in l, ∀ sample, 0 ≤ treatedDirectVariance index sample)
    (hcontrolVariance_pos :
      ∀ᶠ index in l, ∀ sample, 0 < matchedControlVariance index sample)
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
  exact
    absolutePositiveVarianceWaldCoverage_tendsto_of_pattResidualVariance_components_control_pos
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      sampleLawSeq estimator scaledStatistic denominator treatedShare
      controlShare treatedDirectVariance matchedControlVariance target
      criticalValue scale limit denominatorLimit treatedShareLimit
      controlShareLimit treatedDirectVarianceLimit matchedControlVarianceLimit
      coverageLimit hscaled hdenominator htreatedShare hcontrolShare
      htreatedVariance hcontrolVariance hdenominatorLimit
      (pattWeightedResidualVarianceLimit_pos_of_control_pos
        denominatorLimit treatedShareLimit controlShareLimit
        treatedDirectVarianceLimit matchedControlVarianceLimit
        hdenominatorLimit htreatedShareLimit_nonneg hcontrolShareLimit_pos
        htreatedVarianceLimit_nonneg hcontrolVarianceLimit_pos)
      hinverse_meas hdenominator_ne htreatedShare_nonneg
      hcontrolShare_pos htreatedVariance_nonneg hcontrolVariance_pos
      hscale_positive habsolute

/--
Two-sided PATT residual-variance Wald coverage where the positive limiting
variance is derived from positive control share and matched-control
residual-variance limits.
-/
theorem twoSidedPositiveVarianceWaldCoverage_tendsto_of_pattResidualVariance_components_control_pos_limit
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
    (htreatedShareLimit_nonneg : 0 ≤ treatedShareLimit)
    (hcontrolShareLimit_pos : 0 < controlShareLimit)
    (htreatedVarianceLimit_nonneg : 0 ≤ treatedDirectVarianceLimit)
    (hcontrolVarianceLimit_pos : 0 < matchedControlVarianceLimit)
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
    (hdenominator_ne :
      ∀ᶠ index in l, ∀ sample, denominator index sample ≠ 0)
    (htreatedShare_nonneg :
      ∀ᶠ index in l, ∀ sample, 0 ≤ treatedShare index sample)
    (hcontrolShare_pos :
      ∀ᶠ index in l, ∀ sample, 0 < controlShare index sample)
    (htreatedVariance_nonneg :
      ∀ᶠ index in l, ∀ sample, 0 ≤ treatedDirectVariance index sample)
    (hcontrolVariance_pos :
      ∀ᶠ index in l, ∀ sample, 0 < matchedControlVariance index sample)
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
  exact
    twoSidedPositiveVarianceWaldCoverage_tendsto_of_pattResidualVariance_components_control_pos
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      sampleLawSeq estimator scaledStatistic denominator treatedShare
      controlShare treatedDirectVariance matchedControlVariance target
      criticalValue scale limit denominatorLimit treatedShareLimit
      controlShareLimit treatedDirectVarianceLimit matchedControlVarianceLimit
      coverageLimit hscaled hdenominator htreatedShare hcontrolShare
      htreatedVariance hcontrolVariance hdenominatorLimit
      (pattWeightedResidualVarianceLimit_pos_of_control_pos
        denominatorLimit treatedShareLimit controlShareLimit
        treatedDirectVarianceLimit matchedControlVarianceLimit
        hdenominatorLimit htreatedShareLimit_nonneg hcontrolShareLimit_pos
        htreatedVarianceLimit_nonneg hcontrolVarianceLimit_pos)
      hinverse_meas hdenominator_ne htreatedShare_nonneg
      hcontrolShare_pos htreatedVariance_nonneg hcontrolVariance_pos
      hscale_positive htwoSided

end WDSM
end Matching
end StatInference
