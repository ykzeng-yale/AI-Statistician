import StatInference.Matching.WDSM.StudentizedLimitAlgebra
import StatInference.Matching.WDSM.VarianceLimitComponentPositivity

/-!
# Studentized WDSM limits from componentwise limiting-variance positivity

This module composes the studentized-limit bridges with the scalar
componentwise positivity facts for limiting variance formulas.  It removes raw
positive-limiting-variance premises from common oracle, estimated-score,
two-arm residual, and PATT residual studentization statements.
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

/-! ## Oracle variance -/

/--
Studentized oracle-variance weak limit where positive limiting variance is
derived from a positive heterogeneity limit and nonnegative residual limit.
-/
theorem tendstoInDistribution_studentized_of_oracleVariance_components_heterogeneity_pos_limit
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
    (hheterogeneityLimit_pos : 0 < heterogeneityLimit)
    (hresidualLimit_nonneg : 0 ≤ residualLimit)
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
  exact tendstoInDistribution_studentized_of_oracleVariance_components_pos_limit
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    scaledStatistic heterogeneity residual limit heterogeneityLimit
    residualLimit hscaled hheterogeneity hresidual
    (oracleVarianceLimit_pos_of_heterogeneity_pos heterogeneityLimit
      residualLimit hheterogeneityLimit_pos hresidualLimit_nonneg)
    hinverse_meas

/--
Studentized oracle-variance weak limit where positive limiting variance is
derived from a positive residual limit and nonnegative heterogeneity limit.
-/
theorem tendstoInDistribution_studentized_of_oracleVariance_components_residual_pos_limit
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
    (hheterogeneityLimit_nonneg : 0 ≤ heterogeneityLimit)
    (hresidualLimit_pos : 0 < residualLimit)
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
  exact tendstoInDistribution_studentized_of_oracleVariance_components_pos_limit
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    scaledStatistic heterogeneity residual limit heterogeneityLimit
    residualLimit hscaled hheterogeneity hresidual
    (oracleVarianceLimit_pos_of_residual_pos heterogeneityLimit
      residualLimit hheterogeneityLimit_nonneg hresidualLimit_pos)
    hinverse_meas

/-! ## Estimated-score variance -/

/--
Studentized changing-law estimated-score weak limit where positive limiting
variance is derived from strict projection slack and nonnegative target drift.
-/
theorem tendstoInDistribution_studentized_of_estimatedScoreVariance_components_projection_lt_limit
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
    (hprojection_lt_oracle : projectionLimit < oracleLimit)
    (hdriftLimit_nonneg : 0 ≤ targetDriftLimit)
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
  exact
    tendstoInDistribution_studentized_of_estimatedScoreVariance_components_pos_limit
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      scaledStatistic oracle projectionReduction targetDrift limit
      oracleLimit projectionLimit targetDriftLimit hscaled horacle
      hprojection hdrift
      (estimatedScoreVarianceLimit_pos_of_projection_lt_oracle_of_drift_nonneg
        oracleLimit projectionLimit targetDriftLimit hprojection_lt_oracle
        hdriftLimit_nonneg)
      hinverse_meas

/--
Studentized changing-law estimated-score weak limit where positive limiting
variance is derived from weak projection slack and positive target drift.
-/
theorem tendstoInDistribution_studentized_of_estimatedScoreVariance_components_projection_le_drift_pos_limit
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
    (hprojection_le_oracle : projectionLimit ≤ oracleLimit)
    (hdriftLimit_pos : 0 < targetDriftLimit)
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
  exact
    tendstoInDistribution_studentized_of_estimatedScoreVariance_components_pos_limit
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      scaledStatistic oracle projectionReduction targetDrift limit
      oracleLimit projectionLimit targetDriftLimit hscaled horacle
      hprojection hdrift
      (estimatedScoreVarianceLimit_pos_of_projection_le_oracle_of_drift_pos
        oracleLimit projectionLimit targetDriftLimit hprojection_le_oracle
        hdriftLimit_pos)
      hinverse_meas

/--
Studentized fixed-law estimated-score weak limit where positive limiting
variance is derived from strict projection slack.
-/
theorem tendstoInDistribution_studentized_of_fixedLawEstimatedScoreVariance_components_projection_lt_limit
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
    (hprojection_lt_oracle : projectionLimit < oracleLimit)
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
  exact
    tendstoInDistribution_studentized_of_fixedLawEstimatedScoreVariance_components_pos_limit
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      scaledStatistic oracle projectionReduction limit oracleLimit
      projectionLimit hscaled horacle hprojection
      (fixedLawEstimatedScoreVarianceLimit_pos_of_projection_lt_oracle
        oracleLimit projectionLimit hprojection_lt_oracle)
      hinverse_meas

/-! ## Two-arm residual variance -/

/--
Studentized two-arm residual-variance weak limit where positive limiting
variance is derived from treated-side limit positivity.
-/
theorem tendstoInDistribution_studentized_of_twoArmResidualVariance_components_treated_pos_limit
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
  exact
    tendstoInDistribution_studentized_of_twoArmResidualVariance_components_pos_limit
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      scaledStatistic denominator treatedShare controlShare treatedArmVariance
      controlArmVariance limit denominatorLimit treatedShareLimit
      controlShareLimit treatedVarianceLimit controlVarianceLimit hscaled
      hdenominator htreatedShare hcontrolShare htreatedVariance
      hcontrolVariance hdenominatorLimit
      (twoArmWeightedResidualVarianceLimit_pos_of_treated_pos
        denominatorLimit treatedShareLimit controlShareLimit
        treatedVarianceLimit controlVarianceLimit hdenominatorLimit
        htreatedShareLimit_pos hcontrolShareLimit_nonneg
        htreatedVarianceLimit_pos hcontrolVarianceLimit_nonneg)
      hinverse_meas

/--
Studentized two-arm residual-variance weak limit where positive limiting
variance is derived from control-side limit positivity.
-/
theorem tendstoInDistribution_studentized_of_twoArmResidualVariance_components_control_pos_limit
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
  exact
    tendstoInDistribution_studentized_of_twoArmResidualVariance_components_pos_limit
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      scaledStatistic denominator treatedShare controlShare treatedArmVariance
      controlArmVariance limit denominatorLimit treatedShareLimit
      controlShareLimit treatedVarianceLimit controlVarianceLimit hscaled
      hdenominator htreatedShare hcontrolShare htreatedVariance
      hcontrolVariance hdenominatorLimit
      (twoArmWeightedResidualVarianceLimit_pos_of_control_pos
        denominatorLimit treatedShareLimit controlShareLimit
        treatedVarianceLimit controlVarianceLimit hdenominatorLimit
        htreatedShareLimit_nonneg hcontrolShareLimit_pos
        htreatedVarianceLimit_nonneg hcontrolVarianceLimit_pos)
      hinverse_meas

/-! ## PATT residual variance -/

/--
Studentized PATT residual-variance weak limit where positive limiting variance
is derived from treated-side limit positivity.
-/
theorem tendstoInDistribution_studentized_of_pattResidualVariance_components_treated_pos_limit
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
  exact
    tendstoInDistribution_studentized_of_pattResidualVariance_components_pos_limit
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      scaledStatistic denominator treatedShare controlShare
      treatedDirectVariance matchedControlVariance limit denominatorLimit
      treatedShareLimit controlShareLimit treatedDirectVarianceLimit
      matchedControlVarianceLimit hscaled hdenominator htreatedShare
      hcontrolShare htreatedVariance hcontrolVariance hdenominatorLimit
      (pattWeightedResidualVarianceLimit_pos_of_treated_pos
        denominatorLimit treatedShareLimit controlShareLimit
        treatedDirectVarianceLimit matchedControlVarianceLimit
        hdenominatorLimit htreatedShareLimit_pos hcontrolShareLimit_nonneg
        htreatedVarianceLimit_pos hcontrolVarianceLimit_nonneg)
      hinverse_meas

/--
Studentized PATT residual-variance weak limit where positive limiting variance
is derived from matched-control-side limit positivity.
-/
theorem tendstoInDistribution_studentized_of_pattResidualVariance_components_control_pos_limit
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
  exact
    tendstoInDistribution_studentized_of_pattResidualVariance_components_pos_limit
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      scaledStatistic denominator treatedShare controlShare
      treatedDirectVariance matchedControlVariance limit denominatorLimit
      treatedShareLimit controlShareLimit treatedDirectVarianceLimit
      matchedControlVarianceLimit hscaled hdenominator htreatedShare
      hcontrolShare htreatedVariance hcontrolVariance hdenominatorLimit
      (pattWeightedResidualVarianceLimit_pos_of_control_pos
        denominatorLimit treatedShareLimit controlShareLimit
        treatedDirectVarianceLimit matchedControlVarianceLimit
        hdenominatorLimit htreatedShareLimit_nonneg hcontrolShareLimit_pos
        htreatedVarianceLimit_nonneg hcontrolVarianceLimit_pos)
      hinverse_meas

end WDSM
end Matching
end StatInference
