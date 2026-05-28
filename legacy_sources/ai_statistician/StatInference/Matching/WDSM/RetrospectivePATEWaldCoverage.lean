import StatInference.Matching.WDSM.RetrospectivePATEEstimatedScoreStudentized
import StatInference.Matching.WDSM.WaldInferenceBridge

/-!
# Retrospective PATE Wald coverage interface

This module connects the audited retrospective PATE estimated-score
studentized limit to the final real-valued Wald coverage inputs.  The
critical-value calibration, positive standard error, and positive scale
conditions remain explicit fields of the Wald coverage input structures.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open Filter
open scoped Topology

/-- Retrospective PATE estimated-score absolute-Wald bridge. -/
structure RetrospectivePATEEstimatedScoreAbsoluteWaldBridge
    (Index Sample LimitSample : Type*) [MeasurableSpace Sample]
    [MeasurableSpace LimitSample] (sampleLaw : Measure Sample)
    (limitLaw : Measure LimitSample) (l : Filter Index)
    [IsProbabilityMeasure sampleLaw] [IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated] where
  studentized_bridge :
    RetrospectivePATEEstimatedScoreStudentizedBridge Index Sample LimitSample
      sampleLaw limitLaw l
  coverage_input : AbsoluteWaldCoverageInput Index Sample l

/-- Retrospective PATE estimated-score two-sided Wald bridge. -/
structure RetrospectivePATEEstimatedScoreTwoSidedWaldBridge
    (Index Sample LimitSample : Type*) [MeasurableSpace Sample]
    [MeasurableSpace LimitSample] (sampleLaw : Measure Sample)
    (limitLaw : Measure LimitSample) (l : Filter Index)
    [IsProbabilityMeasure sampleLaw] [IsProbabilityMeasure limitLaw]
    [l.IsCountablyGenerated] where
  studentized_bridge :
    RetrospectivePATEEstimatedScoreStudentizedBridge Index Sample LimitSample
      sampleLaw limitLaw l
  coverage_input : TwoSidedWaldCoverageInput Index Sample l

variable {Index Sample LimitSample : Type*}
variable [MeasurableSpace Sample] [MeasurableSpace LimitSample]
variable {sampleLaw : Measure Sample} {limitLaw : Measure LimitSample}
variable [IsProbabilityMeasure sampleLaw] [IsProbabilityMeasure limitLaw]
variable {l : Filter Index} [l.IsCountablyGenerated]

/--
Absolute-Wald coverage for retrospective PATE from the audited studentized
estimated-score bridge and an explicit absolute critical-region calibration
input.
-/
theorem retrospective_pate_absoluteWaldCoverage_tendsto_of_estimated_score_studentized
    (b :
      RetrospectivePATEEstimatedScoreAbsoluteWaldBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (hexact :
      b.studentized_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.studentized_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.studentized_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.studentized_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.studentized_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.studentized_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.studentized_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.studentized_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.studentized_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.studentized_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.studentized_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.studentized_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.studentized_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.studentized_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.studentized_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hfunctional :
      b.studentized_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.studentized_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hadjustment :
      b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hgodambe :
      b.studentized_bridge.estimated_bridge.estimated_input.godambe_identity) :
    b.studentized_bridge.estimated_bridge.estimated_score_asymptotic_normality ∧
      b.studentized_bridge.estimated_bridge.estimated_score_variance_formula ∧
        TendstoInDistribution
          (fun index sample =>
            b.studentized_bridge.studentization_input.scaledStatistic index
                sample *
              (standardError
                (b.studentized_bridge.studentization_input.varianceEstimate
                  index sample))⁻¹)
          l
          (fun limitSample =>
            b.studentized_bridge.studentization_input.limit limitSample *
              (standardError
                b.studentized_bridge.studentization_input.varianceLimit)⁻¹)
          (fun _index => sampleLaw) limitLaw ∧
          Tendsto
            (fun index =>
              eventProbabilityReal (b.coverage_input.sampleLawSeq index)
                (fun sample =>
                  waldCovers (b.coverage_input.estimator index sample)
                    (b.coverage_input.target index)
                    (b.coverage_input.criticalValue index)
                    (b.coverage_input.standardError index sample)
                    (b.coverage_input.scale index)))
            l (nhds b.coverage_input.coverageLimit) := by
  have hstudentized :=
    retrospective_pate_estimated_score_studentized_tendsto_of_audited_local_experiment
      b.studentized_bridge
      hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst hscore hfunctional hequicontinuity hadjustment hgodambe
  have hcoverage := absoluteWaldCoverage_tendsto_of_input b.coverage_input
  exact ⟨hstudentized.1, hstudentized.2.1, hstudentized.2.2, hcoverage⟩

/--
Two-sided Wald coverage for retrospective PATE from the audited studentized
estimated-score bridge and an explicit two-sided critical-region calibration
input.
-/
theorem retrospective_pate_twoSidedWaldCoverage_tendsto_of_estimated_score_studentized
    (b :
      RetrospectivePATEEstimatedScoreTwoSidedWaldBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (hexact :
      b.studentized_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.studentized_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.studentized_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.studentized_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.studentized_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.studentized_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.studentized_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.studentized_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.studentized_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.studentized_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.studentized_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.studentized_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.studentized_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.studentized_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.studentized_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hfunctional :
      b.studentized_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.studentized_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hadjustment :
      b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hgodambe :
      b.studentized_bridge.estimated_bridge.estimated_input.godambe_identity) :
    b.studentized_bridge.estimated_bridge.estimated_score_asymptotic_normality ∧
      b.studentized_bridge.estimated_bridge.estimated_score_variance_formula ∧
        TendstoInDistribution
          (fun index sample =>
            b.studentized_bridge.studentization_input.scaledStatistic index
                sample *
              (standardError
                (b.studentized_bridge.studentization_input.varianceEstimate
                  index sample))⁻¹)
          l
          (fun limitSample =>
            b.studentized_bridge.studentization_input.limit limitSample *
              (standardError
                b.studentized_bridge.studentization_input.varianceLimit)⁻¹)
          (fun _index => sampleLaw) limitLaw ∧
          Tendsto
            (fun index =>
              eventProbabilityReal (b.coverage_input.sampleLawSeq index)
                (fun sample =>
                  waldCovers (b.coverage_input.estimator index sample)
                    (b.coverage_input.target index)
                    (b.coverage_input.criticalValue index)
                    (b.coverage_input.standardError index sample)
                    (b.coverage_input.scale index)))
            l (nhds b.coverage_input.coverageLimit) := by
  have hstudentized :=
    retrospective_pate_estimated_score_studentized_tendsto_of_audited_local_experiment
      b.studentized_bridge
      hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst hscore hfunctional hequicontinuity hadjustment hgodambe
  have hcoverage := twoSidedWaldCoverage_tendsto_of_input b.coverage_input
  exact ⟨hstudentized.1, hstudentized.2.1, hstudentized.2.2, hcoverage⟩

/--
Absolute-Wald coverage for retrospective PATE with the WDSM-specific local
derivative, stochastic equicontinuity, and Godambe obligations packaged as one
compact core.
-/
theorem
    retrospective_pate_absoluteWaldCoverage_tendsto_of_estimated_score_studentized_core
    (b :
      RetrospectivePATEEstimatedScoreAbsoluteWaldBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (hexact :
      b.studentized_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.studentized_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.studentized_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.studentized_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.studentized_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.studentized_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.studentized_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.studentized_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.studentized_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.studentized_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.studentized_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.studentized_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.studentized_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.studentized_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.studentized_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hadjustment :
      b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.studentized_bridge.estimated_bridge.estimated_input) :
    b.studentized_bridge.estimated_bridge.estimated_score_asymptotic_normality ∧
      b.studentized_bridge.estimated_bridge.estimated_score_variance_formula ∧
        TendstoInDistribution
          (fun index sample =>
            b.studentized_bridge.studentization_input.scaledStatistic index
                sample *
              (standardError
                (b.studentized_bridge.studentization_input.varianceEstimate
                  index sample))⁻¹)
          l
          (fun limitSample =>
            b.studentized_bridge.studentization_input.limit limitSample *
              (standardError
                b.studentized_bridge.studentization_input.varianceLimit)⁻¹)
          (fun _index => sampleLaw) limitLaw ∧
          Tendsto
            (fun index =>
              eventProbabilityReal (b.coverage_input.sampleLawSeq index)
                (fun sample =>
                  waldCovers (b.coverage_input.estimator index sample)
                    (b.coverage_input.target index)
                    (b.coverage_input.criticalValue index)
                    (b.coverage_input.standardError index sample)
                    (b.coverage_input.scale index)))
            l (nhds b.coverage_input.coverageLimit) := by
  exact
    retrospective_pate_absoluteWaldCoverage_tendsto_of_estimated_score_studentized
      b hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality hfirst
      hscore core.matching_functional_local_derivative
      core.local_stochastic_equicontinuity hadjustment core.godambe_identity

/--
Two-sided Wald coverage for retrospective PATE with the WDSM-specific local
derivative, stochastic equicontinuity, and Godambe obligations packaged as one
compact core.
-/
theorem
    retrospective_pate_twoSidedWaldCoverage_tendsto_of_estimated_score_studentized_core
    (b :
      RetrospectivePATEEstimatedScoreTwoSidedWaldBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (hexact :
      b.studentized_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.studentized_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.studentized_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.studentized_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.studentized_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.studentized_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.studentized_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.studentized_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.studentized_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.studentized_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.studentized_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.studentized_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.studentized_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.studentized_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.studentized_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hadjustment :
      b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.studentized_bridge.estimated_bridge.estimated_input) :
    b.studentized_bridge.estimated_bridge.estimated_score_asymptotic_normality ∧
      b.studentized_bridge.estimated_bridge.estimated_score_variance_formula ∧
        TendstoInDistribution
          (fun index sample =>
            b.studentized_bridge.studentization_input.scaledStatistic index
                sample *
              (standardError
                (b.studentized_bridge.studentization_input.varianceEstimate
                  index sample))⁻¹)
          l
          (fun limitSample =>
            b.studentized_bridge.studentization_input.limit limitSample *
              (standardError
                b.studentized_bridge.studentization_input.varianceLimit)⁻¹)
          (fun _index => sampleLaw) limitLaw ∧
          Tendsto
            (fun index =>
              eventProbabilityReal (b.coverage_input.sampleLawSeq index)
                (fun sample =>
                  waldCovers (b.coverage_input.estimator index sample)
                    (b.coverage_input.target index)
                    (b.coverage_input.criticalValue index)
                    (b.coverage_input.standardError index sample)
                    (b.coverage_input.scale index)))
            l (nhds b.coverage_input.coverageLimit) := by
  exact
    retrospective_pate_twoSidedWaldCoverage_tendsto_of_estimated_score_studentized
      b hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality hfirst
      hscore core.matching_functional_local_derivative
      core.local_stochastic_equicontinuity hadjustment core.godambe_identity

end WDSM
end Matching
end StatInference
