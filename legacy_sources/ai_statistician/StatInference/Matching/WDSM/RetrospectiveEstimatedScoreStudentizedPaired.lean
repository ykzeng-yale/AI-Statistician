import StatInference.Matching.WDSM.RetrospectivePATEEstimatedScoreStudentized
import StatInference.Matching.WDSM.RetrospectivePATTEstimatedScoreStudentized

/-!
# Retrospective paired estimated-score studentization

This module packages the retrospective PATE and PATT estimated-score
studentized limits behind one paired local-experiment-core interface.  It does
not add new probability assumptions; it only regroups the already audited
single-arm studentized routes.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open scoped Topology

variable {Index Sample LimitSample : Type*}
variable [MeasurableSpace Sample] [MeasurableSpace LimitSample]
variable {sampleLaw : Measure Sample} {limitLaw : Measure LimitSample}
variable [IsProbabilityMeasure sampleLaw] [IsProbabilityMeasure limitLaw]
variable {l : Filter Index} [l.IsCountablyGenerated]

/--
Retrospective paired PATE/PATT estimated-score studentized weak limits with
one compact local-experiment/Godambe core per estimand.
-/
theorem
    retrospective_pate_patt_estimated_score_studentized_tendsto_of_audited_local_experiment_cores
    (bPATE :
      RetrospectivePATEEstimatedScoreStudentizedBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (bPATT :
      RetrospectivePATTEstimatedScoreStudentizedBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (hPATE_exact :
      bPATE.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hPATE_bias_bound :
      bPATE.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hPATE_geometry_regular :
      bPATE.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hPATE_catchment :
      bPATE.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hPATE_heterogeneity_moment :
      bPATE.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hPATE_heterogeneity_variance :
      bPATE.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hPATE_residual_reg :
      bPATE.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hPATE_quad :
      bPATE.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hPATE_radius_regular :
      bPATE.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hPATE_radius_geometry :
      bPATE.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hPATE_finite :
      bPATE.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hPATE_den :
      bPATE.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (hPATE_orthogonality :
      bPATE.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hPATE_first :
      bPATE.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hPATE_score :
      bPATE.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hPATE_adjustment :
      bPATE.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hPATE_core :
      EstimatedScoreLocalExperimentVarianceCore
        bPATE.estimated_bridge.estimated_input)
    (hPATT_exact :
      bPATT.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hPATT_bias_bound :
      bPATT.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hPATT_geometry_regular :
      bPATT.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hPATT_catchment :
      bPATT.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hPATT_heterogeneity_moment :
      bPATT.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hPATT_heterogeneity_variance :
      bPATT.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hPATT_residual_reg :
      bPATT.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hPATT_quad :
      bPATT.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hPATT_radius_regular :
      bPATT.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hPATT_radius_geometry :
      bPATT.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hPATT_finite :
      bPATT.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hPATT_den :
      bPATT.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (hPATT_orthogonality :
      bPATT.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hPATT_first :
      bPATT.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hPATT_score :
      bPATT.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hPATT_adjustment :
      bPATT.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hPATT_core :
      EstimatedScoreLocalExperimentVarianceCore
        bPATT.estimated_bridge.estimated_input) :
    (bPATE.estimated_bridge.estimated_score_asymptotic_normality ∧
      bPATE.estimated_bridge.estimated_score_variance_formula ∧
        TendstoInDistribution
          (fun index sample =>
            bPATE.studentization_input.scaledStatistic index sample *
              (standardError
                (bPATE.studentization_input.varianceEstimate index sample))⁻¹)
          l
          (fun limitSample =>
            bPATE.studentization_input.limit limitSample *
              (standardError bPATE.studentization_input.varianceLimit)⁻¹)
          (fun _index => sampleLaw) limitLaw) ∧
      (bPATT.estimated_bridge.estimated_score_asymptotic_normality ∧
        bPATT.estimated_bridge.estimated_score_variance_formula ∧
          TendstoInDistribution
            (fun index sample =>
              bPATT.studentization_input.scaledStatistic index sample *
                (standardError
                  (bPATT.studentization_input.varianceEstimate index sample))⁻¹)
            l
            (fun limitSample =>
              bPATT.studentization_input.limit limitSample *
                (standardError bPATT.studentization_input.varianceLimit)⁻¹)
            (fun _index => sampleLaw) limitLaw) :=
  ⟨retrospective_pate_estimated_score_studentized_tendsto_of_audited_local_experiment_core
      bPATE hPATE_exact hPATE_bias_bound hPATE_geometry_regular
      hPATE_catchment hPATE_heterogeneity_moment
      hPATE_heterogeneity_variance hPATE_residual_reg hPATE_quad
      hPATE_radius_regular hPATE_radius_geometry hPATE_finite hPATE_den
      hPATE_orthogonality hPATE_first hPATE_score hPATE_adjustment
      hPATE_core,
    retrospective_patt_estimated_score_studentized_tendsto_of_audited_local_experiment_core
      bPATT hPATT_exact hPATT_bias_bound hPATT_geometry_regular
      hPATT_catchment hPATT_heterogeneity_moment
      hPATT_heterogeneity_variance hPATT_residual_reg hPATT_quad
      hPATT_radius_regular hPATT_radius_geometry hPATT_finite hPATT_den
      hPATT_orthogonality hPATT_first hPATT_score hPATT_adjustment
      hPATT_core⟩

end WDSM
end Matching
end StatInference
