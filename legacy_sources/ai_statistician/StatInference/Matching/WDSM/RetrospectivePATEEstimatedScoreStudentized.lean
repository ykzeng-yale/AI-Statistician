import StatInference.Matching.WDSM.RetrospectivePATEEstimatedScoreAudit
import StatInference.Matching.WDSM.FiniteCellIndicatorEstimatedScoreStudentizedBridge

/-!
# Retrospective PATE estimated-score studentization

This module connects the audited retrospective PATE estimated-score normality
and variance formula to the generic variance-consistency studentization layer.
Variance consistency, nonzero limiting standard error, and measurability of
the inverse standard-error multiplier remain explicit fields of
`EstimatedScoreStudentizationInput`.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open scoped Topology

/--
Retrospective PATE estimated-score bridge plus studentization data.
-/
structure RetrospectivePATEEstimatedScoreStudentizedBridge
    (Index Sample LimitSample : Type*) [MeasurableSpace Sample]
    [MeasurableSpace LimitSample] (sampleLaw : Measure Sample)
    (limitLaw : Measure LimitSample) (l : Filter Index)
    [IsProbabilityMeasure sampleLaw] [IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated] where
  estimated_bridge : RetrospectivePATEEstimatedScoreAuditBridge
  studentization_input :
    EstimatedScoreStudentizationInput Index Sample LimitSample sampleLaw
      limitLaw l
  estimated_score_to_scaled_tendsto :
    estimated_bridge.estimated_score_asymptotic_normality ->
      TendstoInDistribution studentization_input.scaledStatistic l
        studentization_input.limit (fun _index => sampleLaw) limitLaw

variable {Index Sample LimitSample : Type*}
variable [MeasurableSpace Sample] [MeasurableSpace LimitSample]
variable {sampleLaw : Measure Sample} {limitLaw : Measure LimitSample}
variable [IsProbabilityMeasure sampleLaw] [IsProbabilityMeasure limitLaw]
variable {l : Filter Index} [l.IsCountablyGenerated]

/--
Audited retrospective PATE estimated-score studentized weak limit.
-/
theorem retrospective_pate_estimated_score_studentized_tendsto_of_audited_local_experiment
    (b :
      RetrospectivePATEEstimatedScoreStudentizedBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (hexact :
      b.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst : b.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore : b.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hfunctional : b.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity : b.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hadjustment : b.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hgodambe : b.estimated_bridge.estimated_input.godambe_identity) :
    b.estimated_bridge.estimated_score_asymptotic_normality ∧
      b.estimated_bridge.estimated_score_variance_formula ∧
        TendstoInDistribution
          (fun index sample =>
            b.studentization_input.scaledStatistic index sample *
              (standardError
                (b.studentization_input.varianceEstimate index sample))⁻¹)
          l
          (fun limitSample =>
            b.studentization_input.limit limitSample *
              (standardError b.studentization_input.varianceLimit)⁻¹)
          (fun _index => sampleLaw) limitLaw := by
  have hestimated_pair :=
    retrospective_pate_estimated_score_normality_and_variance_of_audited_local_experiment
      b.estimated_bridge
      hexact
      hbias_bound
      hgeometry_regular
      hcatchment
      hheterogeneity_moment
      hheterogeneity_variance
      hresidual_reg
      hquad
      hradius_regular
      hradius_geometry
      hfinite
      hden
      horthogonality
      hfirst hscore hfunctional hequicontinuity hadjustment hgodambe
  have hstudentized :=
    studentized_tendstoInDistribution_of_estimated_score_studentization_input
      b.studentization_input
      (b.estimated_score_to_scaled_tendsto hestimated_pair.1)
  exact ⟨hestimated_pair.1, hestimated_pair.2, hstudentized⟩

/--
Audited retrospective PATE estimated-score studentized weak limit with the
WDSM-specific local derivative, stochastic equicontinuity, and Godambe
obligations packaged as one compact core.
-/
theorem
    retrospective_pate_estimated_score_studentized_tendsto_of_audited_local_experiment_core
    (b :
      RetrospectivePATEEstimatedScoreStudentizedBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (hexact :
      b.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst : b.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore : b.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hadjustment : b.estimated_bridge.estimated_input.score_adjustment_algebra)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.estimated_bridge.estimated_input) :
    b.estimated_bridge.estimated_score_asymptotic_normality ∧
      b.estimated_bridge.estimated_score_variance_formula ∧
        TendstoInDistribution
          (fun index sample =>
            b.studentization_input.scaledStatistic index sample *
              (standardError
                (b.studentization_input.varianceEstimate index sample))⁻¹)
          l
          (fun limitSample =>
            b.studentization_input.limit limitSample *
              (standardError b.studentization_input.varianceLimit)⁻¹)
          (fun _index => sampleLaw) limitLaw := by
  exact
    retrospective_pate_estimated_score_studentized_tendsto_of_audited_local_experiment
      b
      hexact
      hbias_bound
      hgeometry_regular
      hcatchment
      hheterogeneity_moment
      hheterogeneity_variance
      hresidual_reg
      hquad
      hradius_regular
      hradius_geometry
      hfinite
      hden
      horthogonality
      hfirst
      hscore
      core.matching_functional_local_derivative
      core.local_stochastic_equicontinuity
      hadjustment
      core.godambe_identity

end WDSM
end Matching
end StatInference
