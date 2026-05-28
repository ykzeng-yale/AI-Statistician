import StatInference.Matching.WDSM.SlutskyAlgebra
import StatInference.Matching.WDSM.VarianceLimitAlgebra

/-!
# Studentized limit algebra for WDSM

This module composes the variance-consistency and Slutsky layers: once a
scaled WDSM statistic has a distributional limit and its variance estimator is
consistent in probability with nonzero limiting standard error, multiplying by
the inverse estimated standard error gives the corresponding studentized
distributional limit.
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
Studentized WDSM limit from variance consistency: if the scaled statistic has
a distributional limit and the variance estimator is consistent in probability
with nonzero limiting standard error, then the statistic multiplied by the
inverse estimated standard error has the corresponding product limit.
-/
theorem tendstoInDistribution_studentized_of_variance_consistency
    (scaledStatistic varianceEstimate : Index -> Sample -> Real)
    (limit : LimitSample -> Real) (varianceLimit : Real)
    (hscaled :
      TendstoInDistribution scaledStatistic l limit
        (fun _index => sampleLaw) limitLaw)
    (hvariance :
      TendstoInMeasure sampleLaw varianceEstimate l
        (fun _sample => varianceLimit))
    (hstandardErrorLimit : standardError varianceLimit ≠ 0)
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
      (fun limitSample => limit limitSample * (standardError varianceLimit)⁻¹)
      (fun _index => sampleLaw) limitLaw := by
  have hinverse :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          (standardError (varianceEstimate index sample))⁻¹) l
        (fun _sample => (standardError varianceLimit)⁻¹) :=
    tendstoInMeasure_inverseStandardError_of_tendstoInMeasure_variance
      varianceEstimate varianceLimit hvariance hstandardErrorLimit
  exact tendstoInDistribution_studentized_of_inverseStandardError
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    scaledStatistic
    (fun index sample =>
      (standardError (varianceEstimate index sample))⁻¹)
    limit (standardError varianceLimit)⁻¹
    hscaled hinverse hinverse_meas

/--
Studentized WDSM limit from variance consistency with positivity stated at the
variance limit.  This is the direct theorem form of the positive-variance
studentization bridge: a positive limiting variance supplies the nonzero
limiting standard-error premise needed by the generic theorem.
-/
theorem tendstoInDistribution_studentized_of_variance_consistency_pos_limit
    (scaledStatistic varianceEstimate : Index -> Sample -> Real)
    (limit : LimitSample -> Real) (varianceLimit : Real)
    (hscaled :
      TendstoInDistribution scaledStatistic l limit
        (fun _index => sampleLaw) limitLaw)
    (hvariance :
      TendstoInMeasure sampleLaw varianceEstimate l
        (fun _sample => varianceLimit))
    (hvarianceLimit : 0 < varianceLimit)
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
      (fun limitSample => limit limitSample * (standardError varianceLimit)⁻¹)
      (fun _index => sampleLaw) limitLaw := by
  exact tendstoInDistribution_studentized_of_variance_consistency
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    scaledStatistic varianceEstimate limit varianceLimit hscaled hvariance
    ((show 0 < standardError varianceLimit by
      unfold standardError
      exact Real.sqrt_pos.2 hvarianceLimit).ne')
    hinverse_meas

/--
Studentized limit with the oracle variance formula, deriving the variance
consistency premise from componentwise convergence in probability of the
heterogeneity and residual variance components.
-/
theorem tendstoInDistribution_studentized_of_oracleVariance_components_pos_limit
    (scaledStatistic : Index -> Sample -> Real)
    (heterogeneity residual : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (heterogeneityLimit residualLimit : Real)
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
          sampleLaw) :
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
      (fun _index => sampleLaw) limitLaw := by
  exact tendstoInDistribution_studentized_of_variance_consistency_pos_limit
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    scaledStatistic
    (fun index sample =>
      oracleVariance (heterogeneity index sample) (residual index sample))
    limit (oracleVariance heterogeneityLimit residualLimit) hscaled
    (tendstoInMeasure_oracleVariance_of_tendstoInMeasure_components
      (sampleLaw := sampleLaw) (l := l)
      heterogeneity residual heterogeneityLimit residualLimit
      hheterogeneity hresidual)
    hvarianceLimit_pos hinverse_meas

/--
Studentized limit with the changing-law estimated-score variance formula,
deriving the variance consistency premise from componentwise convergence in
probability of the oracle variance, projection reduction, and target drift.
-/
theorem tendstoInDistribution_studentized_of_estimatedScoreVariance_components_pos_limit
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
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
          sampleLaw) :
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
      (fun _index => sampleLaw) limitLaw := by
  exact tendstoInDistribution_studentized_of_variance_consistency_pos_limit
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    scaledStatistic
    (fun index sample =>
      estimatedScoreVariance (oracle index sample)
        (projectionReduction index sample) (targetDrift index sample))
    limit (estimatedScoreVariance oracleLimit projectionLimit targetDriftLimit)
    hscaled
    (tendstoInMeasure_estimatedScoreVariance_of_tendstoInMeasure_components
      (sampleLaw := sampleLaw) (l := l)
      oracle projectionReduction targetDrift oracleLimit projectionLimit
      targetDriftLimit horacle hprojection hdrift)
    hvarianceLimit_pos hinverse_meas

/--
Studentized limit with the fixed-law estimated-score variance formula,
deriving the variance consistency premise from componentwise convergence in
probability of the oracle variance and projection reduction.
-/
theorem tendstoInDistribution_studentized_of_fixedLawEstimatedScoreVariance_components_pos_limit
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit : Real)
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
          sampleLaw) :
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
      (fun _index => sampleLaw) limitLaw := by
  exact tendstoInDistribution_studentized_of_variance_consistency_pos_limit
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    scaledStatistic
    (fun index sample =>
      estimatedScoreVariance (oracle index sample)
        (projectionReduction index sample) 0)
    limit (estimatedScoreVariance oracleLimit projectionLimit 0) hscaled
    (tendstoInMeasure_fixedLawEstimatedScoreVariance_of_tendstoInMeasure_components
      (sampleLaw := sampleLaw) (l := l)
      oracle projectionReduction oracleLimit projectionLimit horacle
      hprojection)
    hvarianceLimit_pos hinverse_meas

/--
Studentized limit with the two-arm residual variance formula used as the
variance estimate.  The remaining probabilistic input is the consistency in
measure of the assembled two-arm residual variance target.
-/
theorem tendstoInDistribution_studentized_of_twoArmResidualVariance_pos_limit
    (scaledStatistic : Index -> Sample -> Real)
    (denominator treatedShare controlShare treatedArmVariance
      controlArmVariance : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (denominatorLimit treatedShareLimit controlShareLimit
      treatedVarianceLimit controlVarianceLimit : Real)
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
          sampleLaw) :
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
            (twoArmWeightedResidualVariance denominatorLimit treatedShareLimit
              controlShareLimit treatedVarianceLimit
              controlVarianceLimit))⁻¹)
      (fun _index => sampleLaw) limitLaw := by
  exact tendstoInDistribution_studentized_of_variance_consistency_pos_limit
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    scaledStatistic
    (fun index sample =>
      twoArmWeightedResidualVariance (denominator index sample)
        (treatedShare index sample) (controlShare index sample)
        (treatedArmVariance index sample) (controlArmVariance index sample))
    limit
    (twoArmWeightedResidualVariance denominatorLimit treatedShareLimit
      controlShareLimit treatedVarianceLimit controlVarianceLimit)
    hscaled hvariance hvarianceLimit_pos hinverse_meas

/--
Studentized limit with the two-arm residual variance formula, deriving the
variance-consistency premise from componentwise convergence in probability of
the denominator, arm shares, and residual variance proxies.
-/
theorem tendstoInDistribution_studentized_of_twoArmResidualVariance_components_pos_limit
    (scaledStatistic : Index -> Sample -> Real)
    (denominator treatedShare controlShare treatedArmVariance
      controlArmVariance : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (denominatorLimit treatedShareLimit controlShareLimit
      treatedVarianceLimit controlVarianceLimit : Real)
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
          sampleLaw) :
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
            (twoArmWeightedResidualVariance denominatorLimit treatedShareLimit
              controlShareLimit treatedVarianceLimit
              controlVarianceLimit))⁻¹)
      (fun _index => sampleLaw) limitLaw := by
  exact tendstoInDistribution_studentized_of_twoArmResidualVariance_pos_limit
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    scaledStatistic denominator treatedShare controlShare treatedArmVariance
    controlArmVariance limit denominatorLimit treatedShareLimit
    controlShareLimit treatedVarianceLimit controlVarianceLimit hscaled
    (tendstoInMeasure_twoArmWeightedResidualVariance_of_tendstoInMeasure
      (sampleLaw := sampleLaw) (l := l)
      denominator treatedShare controlShare treatedArmVariance
      controlArmVariance denominatorLimit treatedShareLimit controlShareLimit
      treatedVarianceLimit controlVarianceLimit hdenominator htreatedShare
      hcontrolShare htreatedVariance hcontrolVariance hdenominatorLimit)
    hvarianceLimit_pos hinverse_meas

/--
Studentized limit with the PATT residual variance formula used as the variance
estimate.  This is the one-sided PATT analogue of the two-arm residual
studentization wrapper.
-/
theorem tendstoInDistribution_studentized_of_pattResidualVariance_pos_limit
    (scaledStatistic : Index -> Sample -> Real)
    (denominator treatedShare controlShare treatedDirectVariance
      matchedControlVariance : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (denominatorLimit treatedShareLimit controlShareLimit
      treatedDirectVarianceLimit matchedControlVarianceLimit : Real)
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
          sampleLaw) :
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
      (fun _index => sampleLaw) limitLaw := by
  exact tendstoInDistribution_studentized_of_variance_consistency_pos_limit
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
    hscaled hvariance hvarianceLimit_pos hinverse_meas

/--
Studentized limit with the PATT residual variance formula, deriving the
variance-consistency premise from componentwise convergence in probability of
the denominator, PATT shares, and residual variance proxies.
-/
theorem tendstoInDistribution_studentized_of_pattResidualVariance_components_pos_limit
    (scaledStatistic : Index -> Sample -> Real)
    (denominator treatedShare controlShare treatedDirectVariance
      matchedControlVariance : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (denominatorLimit treatedShareLimit controlShareLimit
      treatedDirectVarianceLimit matchedControlVarianceLimit : Real)
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
          sampleLaw) :
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
      (fun _index => sampleLaw) limitLaw := by
  exact tendstoInDistribution_studentized_of_pattResidualVariance_pos_limit
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    scaledStatistic denominator treatedShare controlShare treatedDirectVariance
    matchedControlVariance limit denominatorLimit treatedShareLimit
    controlShareLimit treatedDirectVarianceLimit matchedControlVarianceLimit
    hscaled
    (tendstoInMeasure_pattWeightedResidualVariance_of_tendstoInMeasure
      (sampleLaw := sampleLaw) (l := l)
      denominator treatedShare controlShare treatedDirectVariance
      matchedControlVariance denominatorLimit treatedShareLimit
      controlShareLimit treatedDirectVarianceLimit matchedControlVarianceLimit
      hdenominator htreatedShare hcontrolShare htreatedVariance
      hcontrolVariance hdenominatorLimit)
    hvarianceLimit_pos hinverse_meas

end WDSM
end Matching
end StatInference
