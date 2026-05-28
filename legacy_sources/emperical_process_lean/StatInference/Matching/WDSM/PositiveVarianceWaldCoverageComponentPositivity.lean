import StatInference.Matching.WDSM.PositiveVarianceWaldCoverageBridge

/-!
# Wald coverage from componentwise variance positivity

This module composes the positive-variance Wald coverage bridge with the
componentwise eventual-positivity lemmas for the variance formulas.  The result
is a set of inference wrappers whose premises are stated at the oracle,
projection, drift, and residual-variance component level rather than as a raw
assembled variance-positivity assumption.
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
Absolute Wald coverage with the oracle variance formula, deriving the
assembled variance-positivity premise from eventual positive heterogeneity and
nonnegative residual variance components.
-/
theorem absolutePositiveVarianceWaldCoverage_tendsto_of_oracleVariance_components_heterogeneity_pos
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
  exact absolutePositiveVarianceWaldCoverage_tendsto_of_oracleVariance_components
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    sampleLawSeq estimator scaledStatistic heterogeneity residual target
    criticalValue scale limit heterogeneityLimit residualLimit coverageLimit
    hscaled hheterogeneity hresidual hvarianceLimit_pos hinverse_meas
    (eventually_oracleVariance_positive_of_eventually_heterogeneity_pos
      (l := l) heterogeneity residual hheterogeneity_pos hresidual_nonneg)
    hscale_positive habsolute

/--
Two-sided Wald coverage with the oracle variance formula, deriving the
assembled variance-positivity premise from eventual positive heterogeneity and
nonnegative residual variance components.
-/
theorem twoSidedPositiveVarianceWaldCoverage_tendsto_of_oracleVariance_components_heterogeneity_pos
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
  exact twoSidedPositiveVarianceWaldCoverage_tendsto_of_oracleVariance_components
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    sampleLawSeq estimator scaledStatistic heterogeneity residual target
    criticalValue scale limit heterogeneityLimit residualLimit coverageLimit
    hscaled hheterogeneity hresidual hvarianceLimit_pos hinverse_meas
    (eventually_oracleVariance_positive_of_eventually_heterogeneity_pos
      (l := l) heterogeneity residual hheterogeneity_pos hresidual_nonneg)
    hscale_positive htwoSided

/-! ## Estimated-score variance -/

/--
Absolute Wald coverage with the changing-law estimated-score variance formula,
deriving assembled variance positivity from strict projection slack and
nonnegative moving-target drift.
-/
theorem absolutePositiveVarianceWaldCoverage_tendsto_of_estimatedScoreVariance_components_projection_lt
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
    absolutePositiveVarianceWaldCoverage_tendsto_of_estimatedScoreVariance_components
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      sampleLawSeq estimator scaledStatistic oracle projectionReduction
      targetDrift target criticalValue scale limit oracleLimit projectionLimit
      targetDriftLimit coverageLimit hscaled horacle hprojection hdrift
      hvarianceLimit_pos hinverse_meas
      (eventually_estimatedScoreVariance_positive_of_eventually_projection_lt_oracle_of_drift_nonneg
        (l := l) oracle projectionReduction targetDrift
        hprojection_lt_oracle hdrift_nonneg)
      hscale_positive habsolute

/--
Two-sided Wald coverage with the changing-law estimated-score variance formula,
deriving assembled variance positivity from strict projection slack and
nonnegative moving-target drift.
-/
theorem twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimatedScoreVariance_components_projection_lt
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
    twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimatedScoreVariance_components
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      sampleLawSeq estimator scaledStatistic oracle projectionReduction
      targetDrift target criticalValue scale limit oracleLimit projectionLimit
      targetDriftLimit coverageLimit hscaled horacle hprojection hdrift
      hvarianceLimit_pos hinverse_meas
      (eventually_estimatedScoreVariance_positive_of_eventually_projection_lt_oracle_of_drift_nonneg
        (l := l) oracle projectionReduction targetDrift
        hprojection_lt_oracle hdrift_nonneg)
      hscale_positive htwoSided

/--
Absolute Wald coverage with the fixed-law estimated-score variance formula,
deriving assembled variance positivity from eventual strict projection slack.
-/
theorem absolutePositiveVarianceWaldCoverage_tendsto_of_fixedLawEstimatedScoreVariance_components_projection_lt
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
    absolutePositiveVarianceWaldCoverage_tendsto_of_fixedLawEstimatedScoreVariance_components
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      sampleLawSeq estimator scaledStatistic oracle projectionReduction target
      criticalValue scale limit oracleLimit projectionLimit coverageLimit
      hscaled horacle hprojection hvarianceLimit_pos hinverse_meas
      (eventually_fixedLawEstimatedScoreVariance_positive_of_eventually_projection_lt_oracle
        (l := l) oracle projectionReduction hprojection_lt_oracle)
      hscale_positive habsolute

/--
Two-sided Wald coverage with the fixed-law estimated-score variance formula,
deriving assembled variance positivity from eventual strict projection slack.
-/
theorem twoSidedPositiveVarianceWaldCoverage_tendsto_of_fixedLawEstimatedScoreVariance_components_projection_lt
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
    twoSidedPositiveVarianceWaldCoverage_tendsto_of_fixedLawEstimatedScoreVariance_components
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      sampleLawSeq estimator scaledStatistic oracle projectionReduction target
      criticalValue scale limit oracleLimit projectionLimit coverageLimit
      hscaled horacle hprojection hvarianceLimit_pos hinverse_meas
      (eventually_fixedLawEstimatedScoreVariance_positive_of_eventually_projection_lt_oracle
        (l := l) oracle projectionReduction hprojection_lt_oracle)
      hscale_positive htwoSided

/-! ## Residual variance -/

/--
Absolute two-arm residual-variance Wald coverage, deriving assembled variance
positivity from treated-side positivity and control-side nonnegativity.
-/
theorem absolutePositiveVarianceWaldCoverage_tendsto_of_twoArmResidualVariance_components_treated_pos
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
    absolutePositiveVarianceWaldCoverage_tendsto_of_twoArmResidualVariance_components
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      sampleLawSeq estimator scaledStatistic denominator treatedShare
      controlShare treatedArmVariance controlArmVariance target criticalValue
      scale limit denominatorLimit treatedShareLimit controlShareLimit
      treatedVarianceLimit controlVarianceLimit coverageLimit hscaled
      hdenominator htreatedShare hcontrolShare htreatedVariance
      hcontrolVariance hdenominatorLimit hvarianceLimit_pos hinverse_meas
      (eventually_twoArmWeightedResidualVariance_positive_of_eventually_treated_pos
        (l := l) denominator treatedShare controlShare treatedArmVariance
        controlArmVariance hdenominator_ne htreatedShare_pos
        hcontrolShare_nonneg htreatedVariance_pos hcontrolVariance_nonneg)
      hscale_positive habsolute

/--
Two-sided two-arm residual-variance Wald coverage, deriving assembled variance
positivity from treated-side positivity and control-side nonnegativity.
-/
theorem twoSidedPositiveVarianceWaldCoverage_tendsto_of_twoArmResidualVariance_components_treated_pos
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
    twoSidedPositiveVarianceWaldCoverage_tendsto_of_twoArmResidualVariance_components
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      sampleLawSeq estimator scaledStatistic denominator treatedShare
      controlShare treatedArmVariance controlArmVariance target criticalValue
      scale limit denominatorLimit treatedShareLimit controlShareLimit
      treatedVarianceLimit controlVarianceLimit coverageLimit hscaled
      hdenominator htreatedShare hcontrolShare htreatedVariance
      hcontrolVariance hdenominatorLimit hvarianceLimit_pos hinverse_meas
      (eventually_twoArmWeightedResidualVariance_positive_of_eventually_treated_pos
        (l := l) denominator treatedShare controlShare treatedArmVariance
        controlArmVariance hdenominator_ne htreatedShare_pos
        hcontrolShare_nonneg htreatedVariance_pos hcontrolVariance_nonneg)
      hscale_positive htwoSided

/--
Absolute two-arm residual-variance Wald coverage, deriving assembled variance
positivity from control-side positivity and treated-side nonnegativity.
-/
theorem absolutePositiveVarianceWaldCoverage_tendsto_of_twoArmResidualVariance_components_control_pos
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
    absolutePositiveVarianceWaldCoverage_tendsto_of_twoArmResidualVariance_components
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      sampleLawSeq estimator scaledStatistic denominator treatedShare
      controlShare treatedArmVariance controlArmVariance target criticalValue
      scale limit denominatorLimit treatedShareLimit controlShareLimit
      treatedVarianceLimit controlVarianceLimit coverageLimit hscaled
      hdenominator htreatedShare hcontrolShare htreatedVariance
      hcontrolVariance hdenominatorLimit hvarianceLimit_pos hinverse_meas
      (eventually_twoArmWeightedResidualVariance_positive_of_eventually_control_pos
        (l := l) denominator treatedShare controlShare treatedArmVariance
        controlArmVariance hdenominator_ne htreatedShare_nonneg
        hcontrolShare_pos htreatedVariance_nonneg hcontrolVariance_pos)
      hscale_positive habsolute

/--
Two-sided two-arm residual-variance Wald coverage, deriving assembled variance
positivity from control-side positivity and treated-side nonnegativity.
-/
theorem twoSidedPositiveVarianceWaldCoverage_tendsto_of_twoArmResidualVariance_components_control_pos
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
    twoSidedPositiveVarianceWaldCoverage_tendsto_of_twoArmResidualVariance_components
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      sampleLawSeq estimator scaledStatistic denominator treatedShare
      controlShare treatedArmVariance controlArmVariance target criticalValue
      scale limit denominatorLimit treatedShareLimit controlShareLimit
      treatedVarianceLimit controlVarianceLimit coverageLimit hscaled
      hdenominator htreatedShare hcontrolShare htreatedVariance
      hcontrolVariance hdenominatorLimit hvarianceLimit_pos hinverse_meas
      (eventually_twoArmWeightedResidualVariance_positive_of_eventually_control_pos
        (l := l) denominator treatedShare controlShare treatedArmVariance
        controlArmVariance hdenominator_ne htreatedShare_nonneg
        hcontrolShare_pos htreatedVariance_nonneg hcontrolVariance_pos)
      hscale_positive htwoSided

/--
Absolute PATT residual-variance Wald coverage, deriving assembled variance
positivity from treated-side positivity and matched-control nonnegativity.
-/
theorem absolutePositiveVarianceWaldCoverage_tendsto_of_pattResidualVariance_components_treated_pos
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
    absolutePositiveVarianceWaldCoverage_tendsto_of_pattResidualVariance_components
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      sampleLawSeq estimator scaledStatistic denominator treatedShare
      controlShare treatedDirectVariance matchedControlVariance target
      criticalValue scale limit denominatorLimit treatedShareLimit
      controlShareLimit treatedDirectVarianceLimit matchedControlVarianceLimit
      coverageLimit hscaled hdenominator htreatedShare hcontrolShare
      htreatedVariance hcontrolVariance hdenominatorLimit hvarianceLimit_pos
      hinverse_meas
      (eventually_pattWeightedResidualVariance_positive_of_eventually_treated_pos
        (l := l) denominator treatedShare controlShare
        treatedDirectVariance matchedControlVariance hdenominator_ne
        htreatedShare_pos hcontrolShare_nonneg htreatedVariance_pos
        hcontrolVariance_nonneg)
      hscale_positive habsolute

/--
Two-sided PATT residual-variance Wald coverage, deriving assembled variance
positivity from treated-side positivity and matched-control nonnegativity.
-/
theorem twoSidedPositiveVarianceWaldCoverage_tendsto_of_pattResidualVariance_components_treated_pos
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
    twoSidedPositiveVarianceWaldCoverage_tendsto_of_pattResidualVariance_components
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      sampleLawSeq estimator scaledStatistic denominator treatedShare
      controlShare treatedDirectVariance matchedControlVariance target
      criticalValue scale limit denominatorLimit treatedShareLimit
      controlShareLimit treatedDirectVarianceLimit matchedControlVarianceLimit
      coverageLimit hscaled hdenominator htreatedShare hcontrolShare
      htreatedVariance hcontrolVariance hdenominatorLimit hvarianceLimit_pos
      hinverse_meas
      (eventually_pattWeightedResidualVariance_positive_of_eventually_treated_pos
        (l := l) denominator treatedShare controlShare
        treatedDirectVariance matchedControlVariance hdenominator_ne
        htreatedShare_pos hcontrolShare_nonneg htreatedVariance_pos
        hcontrolVariance_nonneg)
      hscale_positive htwoSided

/--
Absolute PATT residual-variance Wald coverage, deriving assembled variance
positivity from matched-control-side positivity and treated-side nonnegativity.
-/
theorem absolutePositiveVarianceWaldCoverage_tendsto_of_pattResidualVariance_components_control_pos
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
    absolutePositiveVarianceWaldCoverage_tendsto_of_pattResidualVariance_components
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      sampleLawSeq estimator scaledStatistic denominator treatedShare
      controlShare treatedDirectVariance matchedControlVariance target
      criticalValue scale limit denominatorLimit treatedShareLimit
      controlShareLimit treatedDirectVarianceLimit matchedControlVarianceLimit
      coverageLimit hscaled hdenominator htreatedShare hcontrolShare
      htreatedVariance hcontrolVariance hdenominatorLimit hvarianceLimit_pos
      hinverse_meas
      (eventually_pattWeightedResidualVariance_positive_of_eventually_control_pos
        (l := l) denominator treatedShare controlShare
        treatedDirectVariance matchedControlVariance hdenominator_ne
        htreatedShare_nonneg hcontrolShare_pos htreatedVariance_nonneg
        hcontrolVariance_pos)
      hscale_positive habsolute

/--
Two-sided PATT residual-variance Wald coverage, deriving assembled variance
positivity from matched-control-side positivity and treated-side nonnegativity.
-/
theorem twoSidedPositiveVarianceWaldCoverage_tendsto_of_pattResidualVariance_components_control_pos
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
    twoSidedPositiveVarianceWaldCoverage_tendsto_of_pattResidualVariance_components
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      sampleLawSeq estimator scaledStatistic denominator treatedShare
      controlShare treatedDirectVariance matchedControlVariance target
      criticalValue scale limit denominatorLimit treatedShareLimit
      controlShareLimit treatedDirectVarianceLimit matchedControlVarianceLimit
      coverageLimit hscaled hdenominator htreatedShare hcontrolShare
      htreatedVariance hcontrolVariance hdenominatorLimit hvarianceLimit_pos
      hinverse_meas
      (eventually_pattWeightedResidualVariance_positive_of_eventually_control_pos
        (l := l) denominator treatedShare controlShare
        treatedDirectVariance matchedControlVariance hdenominator_ne
        htreatedShare_nonneg hcontrolShare_pos htreatedVariance_nonneg
        hcontrolVariance_pos)
      hscale_positive htwoSided

end WDSM
end Matching
end StatInference
