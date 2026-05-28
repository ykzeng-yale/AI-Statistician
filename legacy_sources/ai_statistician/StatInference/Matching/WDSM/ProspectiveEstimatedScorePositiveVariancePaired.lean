import StatInference.Matching.WDSM.ProspectivePATEEstimatedScorePositiveVariance
import StatInference.Matching.WDSM.ProspectivePATTEstimatedScorePositiveVariance

/-!
# Prospective paired estimated-score positive-variance inference

This module combines the audited prospective PATE and PATT estimated-score
positive-variance studentization layers into a paired theorem.  The theorem keeps
all paper-specific regularity inputs explicit on each arm.
-/

namespace StatInference
namespace Matching
namespace WDSM

universe u v w x y z

open MeasureTheory
open Filter
open scoped Topology

variable {Index Sample LimitSample : Type*}
variable [MeasurableSpace Sample] [MeasurableSpace LimitSample]
variable {sampleLaw : Measure Sample} {limitLaw : Measure LimitSample}
variable [IsProbabilityMeasure sampleLaw] [IsProbabilityMeasure limitLaw]
variable {l : Filter Index} [l.IsCountablyGenerated]

/--
Audited prospective PATE/PATT estimated-score studentized weak limits with
positivity stated at the limiting-variance level.
-/
theorem
    prospective_pate_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment
    (bPATE :
      ProspectivePATEEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScorePositiveVarianceBridge Index Sample
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
    (hPATE_functional :
      bPATE.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hPATE_equicontinuity :
      bPATE.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hPATE_adjustment :
      bPATE.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hPATE_godambe :
      bPATE.estimated_bridge.estimated_input.godambe_identity)
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
    (hPATT_functional :
      bPATT.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hPATT_equicontinuity :
      bPATT.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hPATT_adjustment :
      bPATT.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hPATT_godambe :
      bPATT.estimated_bridge.estimated_input.godambe_identity) :
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
            (fun _index => sampleLaw) limitLaw) := by
  constructor
  · exact
      prospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment
        bPATE
        hPATE_exact
        hPATE_bias_bound
        hPATE_geometry_regular
        hPATE_catchment
        hPATE_heterogeneity_moment
        hPATE_heterogeneity_variance
        hPATE_residual_reg
        hPATE_quad
        hPATE_radius_regular
        hPATE_radius_geometry
        hPATE_finite
        hPATE_den
        hPATE_orthogonality
        hPATE_first
        hPATE_score
        hPATE_functional
        hPATE_equicontinuity
        hPATE_adjustment
        hPATE_godambe
  · exact
      prospective_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment
      bPATT
        hPATT_exact
        hPATT_bias_bound
        hPATT_geometry_regular
        hPATT_catchment
        hPATT_heterogeneity_moment
        hPATT_heterogeneity_variance
        hPATT_residual_reg
        hPATT_quad
        hPATT_radius_regular
        hPATT_radius_geometry
        hPATT_finite
        hPATT_den
        hPATT_orthogonality
        hPATT_first
        hPATT_score
        hPATT_functional
        hPATT_equicontinuity
        hPATT_adjustment
        hPATT_godambe

/--
Audited prospective PATE/PATT estimated-score positive-variance studentized
weak limits with one compact local-experiment core per estimand.
-/
theorem
    prospective_pate_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_cores
    (bPATE :
      ProspectivePATEEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScorePositiveVarianceBridge Index Sample
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
            (fun _index => sampleLaw) limitLaw) := by
  constructor
  · exact
      prospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_core
        bPATE hPATE_exact hPATE_bias_bound hPATE_geometry_regular
        hPATE_catchment hPATE_heterogeneity_moment
        hPATE_heterogeneity_variance hPATE_residual_reg hPATE_quad
        hPATE_radius_regular hPATE_radius_geometry hPATE_finite hPATE_den
        hPATE_orthogonality hPATE_first hPATE_score hPATE_adjustment
        hPATE_core
  · exact
      prospective_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_core
        bPATT hPATT_exact hPATT_bias_bound hPATT_geometry_regular
        hPATT_catchment hPATT_heterogeneity_moment
        hPATT_heterogeneity_variance hPATT_residual_reg hPATT_quad
        hPATT_radius_regular hPATT_radius_geometry hPATT_finite hPATT_den
        hPATT_orthogonality hPATT_first hPATT_score hPATT_adjustment
        hPATT_core

/--
Paired audited prospective PATE/PATT estimated-score studentized weak limits
from first-step Z-estimator component certificates, with positivity stated at
the limiting-variance level.
-/
theorem
    prospective_pate_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_z_components
    {PATEPropSample : ℕ -> Type u} {PATEPropParameter : Type v}
    {PATEPropMoment : Type w} {PATEPropInfluenceFunction : Type x}
    {PATEPropLinearPart : Type y} {PATEPropRemainder : Type z}
    {PATETreatedSample : ℕ -> Type u} {PATETreatedParameter : Type v}
    {PATETreatedMoment : Type w} {PATETreatedInfluenceFunction : Type x}
    {PATETreatedLinearPart : Type y} {PATETreatedRemainder : Type z}
    {PATEControlSample : ℕ -> Type u} {PATEControlParameter : Type v}
    {PATEControlMoment : Type w} {PATEControlInfluenceFunction : Type x}
    {PATEControlLinearPart : Type y} {PATEControlRemainder : Type z}
    {PATTPropSample : ℕ -> Type u} {PATTPropParameter : Type v}
    {PATTPropMoment : Type w} {PATTPropInfluenceFunction : Type x}
    {PATTPropLinearPart : Type y} {PATTPropRemainder : Type z}
    {PATTControlSample : ℕ -> Type u} {PATTControlParameter : Type v}
    {PATTControlMoment : Type w} {PATTControlInfluenceFunction : Type x}
    {PATTControlLinearPart : Type y} {PATTControlRemainder : Type z}
    (bPATE :
      ProspectivePATEEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (pateFirstStep : PATEDoubleScoreFirstStepAssembly)
    (pattFirstStep : PATTDoubleScoreFirstStepAssembly)
    (patePropensity :
      FirstStepScoreComponentZEvidence PATEPropSample PATEPropParameter
        PATEPropMoment PATEPropInfluenceFunction PATEPropLinearPart
        PATEPropRemainder)
    (pateTreated :
      FirstStepScoreComponentZEvidence PATETreatedSample PATETreatedParameter
        PATETreatedMoment PATETreatedInfluenceFunction PATETreatedLinearPart
        PATETreatedRemainder)
    (pateControl :
      FirstStepScoreComponentZEvidence PATEControlSample PATEControlParameter
        PATEControlMoment PATEControlInfluenceFunction PATEControlLinearPart
        PATEControlRemainder)
    (pattPropensity :
      FirstStepScoreComponentZEvidence PATTPropSample PATTPropParameter
        PATTPropMoment PATTPropInfluenceFunction PATTPropLinearPart
        PATTPropRemainder)
    (pattControl :
      FirstStepScoreComponentZEvidence PATTControlSample PATTControlParameter
        PATTControlMoment PATTControlInfluenceFunction PATTControlLinearPart
        PATTControlRemainder)
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
    (hPATE_first_transfer :
      pateFirstStep.first_step_asymptotic_linearization ->
        bPATE.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hPATE_score_transfer :
      pateFirstStep.score_estimator_local_asymptotic_linearity ->
        bPATE.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hPATE_prop_weight :
      patePropensity.component.weighting_design ->
        pateFirstStep.propensity_weighting_design)
    (hPATE_treated_weight :
      pateTreated.component.weighting_design ->
        pateFirstStep.treated_prognostic_weighting_design)
    (hPATE_control_weight :
      pateControl.component.weighting_design ->
        pateFirstStep.control_prognostic_weighting_design)
    (hPATE_prop_component :
      patePropensity.component.component_asymptotic_linearity ->
        pateFirstStep.propensity_component_asymptotic_linearity)
    (hPATE_treated_component :
      pateTreated.component.component_asymptotic_linearity ->
        pateFirstStep.treated_prognostic_component_asymptotic_linearity)
    (hPATE_control_component :
      pateControl.component.component_asymptotic_linearity ->
        pateFirstStep.control_prognostic_component_asymptotic_linearity)
    (hPATE_functional :
      bPATE.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hPATE_equicontinuity :
      bPATE.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hPATE_adjustment :
      bPATE.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hPATE_godambe :
      bPATE.estimated_bridge.estimated_input.godambe_identity)
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
    (hPATT_first_transfer :
      pattFirstStep.first_step_asymptotic_linearization ->
        bPATT.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hPATT_score_transfer :
      pattFirstStep.score_estimator_local_asymptotic_linearity ->
        bPATT.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hPATT_prop_weight :
      pattPropensity.component.weighting_design ->
        pattFirstStep.propensity_weighting_design)
    (hPATT_control_weight :
      pattControl.component.weighting_design ->
        pattFirstStep.control_prognostic_weighting_design)
    (hPATT_prop_component :
      pattPropensity.component.component_asymptotic_linearity ->
        pattFirstStep.propensity_component_asymptotic_linearity)
    (hPATT_control_component :
      pattControl.component.component_asymptotic_linearity ->
        pattFirstStep.control_prognostic_component_asymptotic_linearity)
    (hPATT_functional :
      bPATT.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hPATT_equicontinuity :
      bPATT.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hPATT_adjustment :
      bPATT.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hPATT_godambe :
      bPATT.estimated_bridge.estimated_input.godambe_identity) :
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
            (fun _index => sampleLaw) limitLaw) := by
  constructor
  · exact
      prospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_z_components
        bPATE pateFirstStep patePropensity pateTreated pateControl hPATE_exact
        hPATE_bias_bound hPATE_geometry_regular hPATE_catchment
        hPATE_heterogeneity_moment hPATE_heterogeneity_variance
        hPATE_residual_reg hPATE_quad hPATE_radius_regular
        hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
        hPATE_first_transfer hPATE_score_transfer hPATE_prop_weight
        hPATE_treated_weight hPATE_control_weight hPATE_prop_component
        hPATE_treated_component hPATE_control_component hPATE_functional
        hPATE_equicontinuity hPATE_adjustment hPATE_godambe
  · exact
      prospective_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_z_components
        bPATT pattFirstStep pattPropensity pattControl hPATT_exact
        hPATT_bias_bound hPATT_geometry_regular hPATT_catchment
        hPATT_heterogeneity_moment hPATT_heterogeneity_variance
        hPATT_residual_reg hPATT_quad hPATT_radius_regular
        hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
        hPATT_first_transfer hPATT_score_transfer hPATT_prop_weight
        hPATT_control_weight hPATT_prop_component hPATT_control_component
        hPATT_functional hPATT_equicontinuity hPATT_adjustment hPATT_godambe

/--
Paired audited prospective PATE/PATT estimated-score positive-variance
studentized weak limits from first-step Z-estimator component certificates,
with one compact local-experiment core per estimand.
-/
theorem
    prospective_pate_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_z_components_core
    {PATEPropSample : ℕ -> Type u} {PATEPropParameter : Type v}
    {PATEPropMoment : Type w} {PATEPropInfluenceFunction : Type x}
    {PATEPropLinearPart : Type y} {PATEPropRemainder : Type z}
    {PATETreatedSample : ℕ -> Type u} {PATETreatedParameter : Type v}
    {PATETreatedMoment : Type w} {PATETreatedInfluenceFunction : Type x}
    {PATETreatedLinearPart : Type y} {PATETreatedRemainder : Type z}
    {PATEControlSample : ℕ -> Type u} {PATEControlParameter : Type v}
    {PATEControlMoment : Type w} {PATEControlInfluenceFunction : Type x}
    {PATEControlLinearPart : Type y} {PATEControlRemainder : Type z}
    {PATTPropSample : ℕ -> Type u} {PATTPropParameter : Type v}
    {PATTPropMoment : Type w} {PATTPropInfluenceFunction : Type x}
    {PATTPropLinearPart : Type y} {PATTPropRemainder : Type z}
    {PATTControlSample : ℕ -> Type u} {PATTControlParameter : Type v}
    {PATTControlMoment : Type w} {PATTControlInfluenceFunction : Type x}
    {PATTControlLinearPart : Type y} {PATTControlRemainder : Type z}
    (bPATE :
      ProspectivePATEEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (pateFirstStep : PATEDoubleScoreFirstStepAssembly)
    (pattFirstStep : PATTDoubleScoreFirstStepAssembly)
    (patePropensity :
      FirstStepScoreComponentZEvidence PATEPropSample PATEPropParameter
        PATEPropMoment PATEPropInfluenceFunction PATEPropLinearPart
        PATEPropRemainder)
    (pateTreated :
      FirstStepScoreComponentZEvidence PATETreatedSample PATETreatedParameter
        PATETreatedMoment PATETreatedInfluenceFunction PATETreatedLinearPart
        PATETreatedRemainder)
    (pateControl :
      FirstStepScoreComponentZEvidence PATEControlSample PATEControlParameter
        PATEControlMoment PATEControlInfluenceFunction PATEControlLinearPart
        PATEControlRemainder)
    (pattPropensity :
      FirstStepScoreComponentZEvidence PATTPropSample PATTPropParameter
        PATTPropMoment PATTPropInfluenceFunction PATTPropLinearPart
        PATTPropRemainder)
    (pattControl :
      FirstStepScoreComponentZEvidence PATTControlSample PATTControlParameter
        PATTControlMoment PATTControlInfluenceFunction PATTControlLinearPart
        PATTControlRemainder)
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
    (hPATE_first_transfer :
      pateFirstStep.first_step_asymptotic_linearization ->
        bPATE.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hPATE_score_transfer :
      pateFirstStep.score_estimator_local_asymptotic_linearity ->
        bPATE.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hPATE_prop_weight :
      patePropensity.component.weighting_design ->
        pateFirstStep.propensity_weighting_design)
    (hPATE_treated_weight :
      pateTreated.component.weighting_design ->
        pateFirstStep.treated_prognostic_weighting_design)
    (hPATE_control_weight :
      pateControl.component.weighting_design ->
        pateFirstStep.control_prognostic_weighting_design)
    (hPATE_prop_component :
      patePropensity.component.component_asymptotic_linearity ->
        pateFirstStep.propensity_component_asymptotic_linearity)
    (hPATE_treated_component :
      pateTreated.component.component_asymptotic_linearity ->
        pateFirstStep.treated_prognostic_component_asymptotic_linearity)
    (hPATE_control_component :
      pateControl.component.component_asymptotic_linearity ->
        pateFirstStep.control_prognostic_component_asymptotic_linearity)
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
    (hPATT_first_transfer :
      pattFirstStep.first_step_asymptotic_linearization ->
        bPATT.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hPATT_score_transfer :
      pattFirstStep.score_estimator_local_asymptotic_linearity ->
        bPATT.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hPATT_prop_weight :
      pattPropensity.component.weighting_design ->
        pattFirstStep.propensity_weighting_design)
    (hPATT_control_weight :
      pattControl.component.weighting_design ->
        pattFirstStep.control_prognostic_weighting_design)
    (hPATT_prop_component :
      pattPropensity.component.component_asymptotic_linearity ->
        pattFirstStep.propensity_component_asymptotic_linearity)
    (hPATT_control_component :
      pattControl.component.component_asymptotic_linearity ->
        pattFirstStep.control_prognostic_component_asymptotic_linearity)
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
            (fun _index => sampleLaw) limitLaw) := by
  constructor
  · exact
      prospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_z_components_core
        bPATE pateFirstStep patePropensity pateTreated pateControl
        hPATE_exact hPATE_bias_bound hPATE_geometry_regular
        hPATE_catchment hPATE_heterogeneity_moment
        hPATE_heterogeneity_variance hPATE_residual_reg hPATE_quad
        hPATE_radius_regular hPATE_radius_geometry hPATE_finite hPATE_den
        hPATE_orthogonality hPATE_first_transfer hPATE_score_transfer
        hPATE_prop_weight hPATE_treated_weight hPATE_control_weight
        hPATE_prop_component hPATE_treated_component hPATE_control_component
        hPATE_adjustment hPATE_core
  · exact
      prospective_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_z_components_core
        bPATT pattFirstStep pattPropensity pattControl hPATT_exact
        hPATT_bias_bound hPATT_geometry_regular hPATT_catchment
        hPATT_heterogeneity_moment hPATT_heterogeneity_variance
        hPATT_residual_reg hPATT_quad hPATT_radius_regular
        hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
        hPATT_first_transfer hPATT_score_transfer hPATT_prop_weight
        hPATT_control_weight hPATT_prop_component hPATT_control_component
        hPATT_adjustment hPATT_core

/-- Conclusion of the prospective PATE absolute positive-variance Wald wrapper. -/
def ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion
    (b :
      ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l) : Prop :=
  b.positive_bridge.estimated_bridge.estimated_score_asymptotic_normality ∧
    b.positive_bridge.estimated_bridge.estimated_score_variance_formula ∧
      TendstoInDistribution
        (fun index sample =>
          b.positive_bridge.studentization_input.scaledStatistic index sample *
            (standardError
              (b.positive_bridge.studentization_input.varianceEstimate index sample))⁻¹)
        l
        (fun limitSample =>
          b.positive_bridge.studentization_input.limit limitSample *
            (standardError b.positive_bridge.studentization_input.varianceLimit)⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
        Tendsto
          (fun index =>
            eventProbabilityReal (b.coverage_input.sampleLawSeq index)
              (fun sample =>
                waldCovers (b.coverage_input.estimator index sample)
                  (b.coverage_input.target index)
                  (b.coverage_input.criticalValue index)
                  (standardError
                    (b.coverage_input.varianceEstimate index sample))
                  (b.coverage_input.scale index)))
          l (nhds b.coverage_input.coverageLimit)

/-- Conclusion of the prospective PATT absolute positive-variance Wald wrapper. -/
def ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion
    (b :
      ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l) : Prop :=
  b.positive_bridge.estimated_bridge.estimated_score_asymptotic_normality ∧
    b.positive_bridge.estimated_bridge.estimated_score_variance_formula ∧
      TendstoInDistribution
        (fun index sample =>
          b.positive_bridge.studentization_input.scaledStatistic index sample *
            (standardError
              (b.positive_bridge.studentization_input.varianceEstimate index sample))⁻¹)
        l
        (fun limitSample =>
          b.positive_bridge.studentization_input.limit limitSample *
            (standardError b.positive_bridge.studentization_input.varianceLimit)⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
        Tendsto
          (fun index =>
            eventProbabilityReal (b.coverage_input.sampleLawSeq index)
              (fun sample =>
                waldCovers (b.coverage_input.estimator index sample)
                  (b.coverage_input.target index)
                  (b.coverage_input.criticalValue index)
                  (standardError
                    (b.coverage_input.varianceEstimate index sample))
                  (b.coverage_input.scale index)))
          l (nhds b.coverage_input.coverageLimit)

/--
Paired absolute variance-based Wald coverage for prospective PATE and PATT from
audited estimated-score positive-variance studentization.
-/
theorem prospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score
    (bPATE :
      ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (hPATE_exact :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hPATE_bias_bound :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hPATE_geometry_regular :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hPATE_catchment :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hPATE_heterogeneity_moment :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hPATE_heterogeneity_variance :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hPATE_residual_reg :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hPATE_quad :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hPATE_radius_regular :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hPATE_radius_geometry :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hPATE_finite :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hPATE_den :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (hPATE_orthogonality :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hPATE_first :
      bPATE.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hPATE_score :
      bPATE.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hPATE_functional :
      bPATE.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hPATE_equicontinuity :
      bPATE.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hPATE_adjustment :
      bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hPATE_godambe :
      bPATE.positive_bridge.estimated_bridge.estimated_input.godambe_identity)
    (hPATT_exact :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hPATT_bias_bound :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hPATT_geometry_regular :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hPATT_catchment :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hPATT_heterogeneity_moment :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hPATT_heterogeneity_variance :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hPATT_residual_reg :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hPATT_quad :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hPATT_radius_regular :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hPATT_radius_geometry :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hPATT_finite :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hPATT_den :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (hPATT_orthogonality :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hPATT_first :
      bPATT.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hPATT_score :
      bPATT.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hPATT_functional :
      bPATT.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hPATT_equicontinuity :
      bPATT.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hPATT_adjustment :
      bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hPATT_godambe :
      bPATT.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATE ∧
      ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATT := by
  constructor
  · simpa [ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion] using
      prospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score
        bPATE
        hPATE_exact hPATE_bias_bound hPATE_geometry_regular hPATE_catchment
        hPATE_heterogeneity_moment hPATE_heterogeneity_variance
        hPATE_residual_reg hPATE_quad hPATE_radius_regular
        hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
        hPATE_first hPATE_score hPATE_functional hPATE_equicontinuity
        hPATE_adjustment hPATE_godambe
  · simpa [ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion] using
      prospective_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score
        bPATT
        hPATT_exact hPATT_bias_bound hPATT_geometry_regular hPATT_catchment
        hPATT_heterogeneity_moment hPATT_heterogeneity_variance
        hPATT_residual_reg hPATT_quad hPATT_radius_regular
        hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
        hPATT_first hPATT_score hPATT_functional hPATT_equicontinuity
        hPATT_adjustment hPATT_godambe

/-- Conclusion of the prospective PATE two-sided positive-variance Wald wrapper. -/
def ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
    (b :
      ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l) : Prop :=
  b.positive_bridge.estimated_bridge.estimated_score_asymptotic_normality ∧
    b.positive_bridge.estimated_bridge.estimated_score_variance_formula ∧
      TendstoInDistribution
        (fun index sample =>
          b.positive_bridge.studentization_input.scaledStatistic index sample *
            (standardError
              (b.positive_bridge.studentization_input.varianceEstimate index sample))⁻¹)
        l
        (fun limitSample =>
          b.positive_bridge.studentization_input.limit limitSample *
            (standardError b.positive_bridge.studentization_input.varianceLimit)⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
        Tendsto
          (fun index =>
            eventProbabilityReal (b.coverage_input.sampleLawSeq index)
              (fun sample =>
                waldCovers (b.coverage_input.estimator index sample)
                  (b.coverage_input.target index)
                  (b.coverage_input.criticalValue index)
                  (standardError
                    (b.coverage_input.varianceEstimate index sample))
                  (b.coverage_input.scale index)))
          l (nhds b.coverage_input.coverageLimit)

/-- Conclusion of the prospective PATT two-sided positive-variance Wald wrapper. -/
def ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
    (b :
      ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l) : Prop :=
  b.positive_bridge.estimated_bridge.estimated_score_asymptotic_normality ∧
    b.positive_bridge.estimated_bridge.estimated_score_variance_formula ∧
      TendstoInDistribution
        (fun index sample =>
          b.positive_bridge.studentization_input.scaledStatistic index sample *
            (standardError
              (b.positive_bridge.studentization_input.varianceEstimate index sample))⁻¹)
        l
        (fun limitSample =>
          b.positive_bridge.studentization_input.limit limitSample *
            (standardError b.positive_bridge.studentization_input.varianceLimit)⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
        Tendsto
          (fun index =>
            eventProbabilityReal (b.coverage_input.sampleLawSeq index)
              (fun sample =>
                waldCovers (b.coverage_input.estimator index sample)
                  (b.coverage_input.target index)
                  (b.coverage_input.criticalValue index)
                  (standardError
                    (b.coverage_input.varianceEstimate index sample))
                  (b.coverage_input.scale index)))
          l (nhds b.coverage_input.coverageLimit)

/--
Paired two-sided variance-based Wald coverage for prospective PATE and PATT
from audited estimated-score positive-variance studentization.
-/
theorem prospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score
    (bPATE :
      ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (hPATE_exact :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hPATE_bias_bound :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hPATE_geometry_regular :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hPATE_catchment :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hPATE_heterogeneity_moment :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hPATE_heterogeneity_variance :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hPATE_residual_reg :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hPATE_quad :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hPATE_radius_regular :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hPATE_radius_geometry :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hPATE_finite :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hPATE_den :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (hPATE_orthogonality :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hPATE_first :
      bPATE.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hPATE_score :
      bPATE.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hPATE_functional :
      bPATE.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hPATE_equicontinuity :
      bPATE.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hPATE_adjustment :
      bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hPATE_godambe :
      bPATE.positive_bridge.estimated_bridge.estimated_input.godambe_identity)
    (hPATT_exact :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hPATT_bias_bound :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hPATT_geometry_regular :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hPATT_catchment :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hPATT_heterogeneity_moment :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hPATT_heterogeneity_variance :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hPATT_residual_reg :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hPATT_quad :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hPATT_radius_regular :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hPATT_radius_geometry :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hPATT_finite :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hPATT_den :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (hPATT_orthogonality :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hPATT_first :
      bPATT.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hPATT_score :
      bPATT.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hPATT_functional :
      bPATT.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hPATT_equicontinuity :
      bPATT.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hPATT_adjustment :
      bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hPATT_godambe :
      bPATT.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATE ∧
      ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATT := by
  constructor
  · simpa [ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion] using
      prospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score
        bPATE
        hPATE_exact hPATE_bias_bound hPATE_geometry_regular hPATE_catchment
        hPATE_heterogeneity_moment hPATE_heterogeneity_variance
        hPATE_residual_reg hPATE_quad hPATE_radius_regular
        hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
        hPATE_first hPATE_score hPATE_functional hPATE_equicontinuity
        hPATE_adjustment hPATE_godambe
  · simpa [ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion] using
      prospective_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score
        bPATT
        hPATT_exact hPATT_bias_bound hPATT_geometry_regular hPATT_catchment
        hPATT_heterogeneity_moment hPATT_heterogeneity_variance
        hPATT_residual_reg hPATT_quad hPATT_radius_regular
        hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
        hPATT_first hPATT_score hPATT_functional hPATT_equicontinuity
        hPATT_adjustment hPATT_godambe

/--
Paired absolute variance-based Wald coverage for prospective PATE and PATT from
audited estimated-score positive-variance studentization, with one compact
local-experiment core per estimand.
-/
theorem
    prospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_core
    (bPATE :
      ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (hPATE_exact :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hPATE_bias_bound :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hPATE_geometry_regular :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hPATE_catchment :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hPATE_heterogeneity_moment :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hPATE_heterogeneity_variance :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hPATE_residual_reg :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hPATE_quad :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hPATE_radius_regular :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hPATE_radius_geometry :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hPATE_finite :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hPATE_den :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (hPATE_orthogonality :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hPATE_first :
      bPATE.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hPATE_score :
      bPATE.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hPATE_adjustment :
      bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hPATE_core :
      EstimatedScoreLocalExperimentVarianceCore
        bPATE.positive_bridge.estimated_bridge.estimated_input)
    (hPATT_exact :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hPATT_bias_bound :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hPATT_geometry_regular :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hPATT_catchment :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hPATT_heterogeneity_moment :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hPATT_heterogeneity_variance :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hPATT_residual_reg :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hPATT_quad :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hPATT_radius_regular :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hPATT_radius_geometry :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hPATT_finite :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hPATT_den :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (hPATT_orthogonality :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hPATT_first :
      bPATT.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hPATT_score :
      bPATT.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hPATT_adjustment :
      bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hPATT_core :
      EstimatedScoreLocalExperimentVarianceCore
        bPATT.positive_bridge.estimated_bridge.estimated_input) :
    ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATE ∧
      ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATT :=
  prospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score
    bPATE bPATT hPATE_exact hPATE_bias_bound hPATE_geometry_regular
    hPATE_catchment hPATE_heterogeneity_moment hPATE_heterogeneity_variance
    hPATE_residual_reg hPATE_quad hPATE_radius_regular hPATE_radius_geometry
    hPATE_finite hPATE_den hPATE_orthogonality hPATE_first hPATE_score
    hPATE_core.matching_functional_local_derivative
    hPATE_core.local_stochastic_equicontinuity hPATE_adjustment
    hPATE_core.godambe_identity hPATT_exact hPATT_bias_bound
    hPATT_geometry_regular hPATT_catchment hPATT_heterogeneity_moment
    hPATT_heterogeneity_variance hPATT_residual_reg hPATT_quad
    hPATT_radius_regular hPATT_radius_geometry hPATT_finite hPATT_den
    hPATT_orthogonality hPATT_first hPATT_score
    hPATT_core.matching_functional_local_derivative
    hPATT_core.local_stochastic_equicontinuity hPATT_adjustment
    hPATT_core.godambe_identity

/--
Paired two-sided variance-based Wald coverage for prospective PATE and PATT
from audited estimated-score positive-variance studentization, with one compact
local-experiment core per estimand.
-/
theorem
    prospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_core
    (bPATE :
      ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (hPATE_exact :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hPATE_bias_bound :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hPATE_geometry_regular :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hPATE_catchment :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hPATE_heterogeneity_moment :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hPATE_heterogeneity_variance :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hPATE_residual_reg :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hPATE_quad :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hPATE_radius_regular :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hPATE_radius_geometry :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hPATE_finite :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hPATE_den :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (hPATE_orthogonality :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hPATE_first :
      bPATE.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hPATE_score :
      bPATE.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hPATE_adjustment :
      bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hPATE_core :
      EstimatedScoreLocalExperimentVarianceCore
        bPATE.positive_bridge.estimated_bridge.estimated_input)
    (hPATT_exact :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hPATT_bias_bound :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hPATT_geometry_regular :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hPATT_catchment :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hPATT_heterogeneity_moment :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hPATT_heterogeneity_variance :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hPATT_residual_reg :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hPATT_quad :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hPATT_radius_regular :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hPATT_radius_geometry :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hPATT_finite :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hPATT_den :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (hPATT_orthogonality :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hPATT_first :
      bPATT.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hPATT_score :
      bPATT.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hPATT_adjustment :
      bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hPATT_core :
      EstimatedScoreLocalExperimentVarianceCore
        bPATT.positive_bridge.estimated_bridge.estimated_input) :
    ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATE ∧
      ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATT :=
  prospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score
    bPATE bPATT hPATE_exact hPATE_bias_bound hPATE_geometry_regular
    hPATE_catchment hPATE_heterogeneity_moment hPATE_heterogeneity_variance
    hPATE_residual_reg hPATE_quad hPATE_radius_regular hPATE_radius_geometry
    hPATE_finite hPATE_den hPATE_orthogonality hPATE_first hPATE_score
    hPATE_core.matching_functional_local_derivative
    hPATE_core.local_stochastic_equicontinuity hPATE_adjustment
    hPATE_core.godambe_identity hPATT_exact hPATT_bias_bound
    hPATT_geometry_regular hPATT_catchment hPATT_heterogeneity_moment
    hPATT_heterogeneity_variance hPATT_residual_reg hPATT_quad
    hPATT_radius_regular hPATT_radius_geometry hPATT_finite hPATT_den
    hPATT_orthogonality hPATT_first hPATT_score
    hPATT_core.matching_functional_local_derivative
    hPATT_core.local_stochastic_equicontinuity hPATT_adjustment
    hPATT_core.godambe_identity

/--
Paired absolute variance-based Wald coverage for prospective PATE and PATT from
first-step Z-estimator component certificates.
-/
theorem
    prospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components
    {PATEPropSample : ℕ -> Type u} {PATEPropParameter : Type v}
    {PATEPropMoment : Type w} {PATEPropInfluenceFunction : Type x}
    {PATEPropLinearPart : Type y} {PATEPropRemainder : Type z}
    {PATETreatedSample : ℕ -> Type u} {PATETreatedParameter : Type v}
    {PATETreatedMoment : Type w} {PATETreatedInfluenceFunction : Type x}
    {PATETreatedLinearPart : Type y} {PATETreatedRemainder : Type z}
    {PATEControlSample : ℕ -> Type u} {PATEControlParameter : Type v}
    {PATEControlMoment : Type w} {PATEControlInfluenceFunction : Type x}
    {PATEControlLinearPart : Type y} {PATEControlRemainder : Type z}
    {PATTPropSample : ℕ -> Type u} {PATTPropParameter : Type v}
    {PATTPropMoment : Type w} {PATTPropInfluenceFunction : Type x}
    {PATTPropLinearPart : Type y} {PATTPropRemainder : Type z}
    {PATTControlSample : ℕ -> Type u} {PATTControlParameter : Type v}
    {PATTControlMoment : Type w} {PATTControlInfluenceFunction : Type x}
    {PATTControlLinearPart : Type y} {PATTControlRemainder : Type z}
    (bPATE :
      ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (pateFirstStep : PATEDoubleScoreFirstStepAssembly)
    (pattFirstStep : PATTDoubleScoreFirstStepAssembly)
    (patePropensity :
      FirstStepScoreComponentZEvidence PATEPropSample PATEPropParameter
        PATEPropMoment PATEPropInfluenceFunction PATEPropLinearPart
        PATEPropRemainder)
    (pateTreated :
      FirstStepScoreComponentZEvidence PATETreatedSample PATETreatedParameter
        PATETreatedMoment PATETreatedInfluenceFunction PATETreatedLinearPart
        PATETreatedRemainder)
    (pateControl :
      FirstStepScoreComponentZEvidence PATEControlSample PATEControlParameter
        PATEControlMoment PATEControlInfluenceFunction PATEControlLinearPart
        PATEControlRemainder)
    (pattPropensity :
      FirstStepScoreComponentZEvidence PATTPropSample PATTPropParameter
        PATTPropMoment PATTPropInfluenceFunction PATTPropLinearPart
        PATTPropRemainder)
    (pattControl :
      FirstStepScoreComponentZEvidence PATTControlSample PATTControlParameter
        PATTControlMoment PATTControlInfluenceFunction PATTControlLinearPart
        PATTControlRemainder)
    (hPATE_exact :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hPATE_bias_bound :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hPATE_geometry_regular :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hPATE_catchment :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hPATE_heterogeneity_moment :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hPATE_heterogeneity_variance :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hPATE_residual_reg :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hPATE_quad :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hPATE_radius_regular :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hPATE_radius_geometry :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hPATE_finite :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hPATE_den :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (hPATE_orthogonality :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hPATE_first_transfer :
      pateFirstStep.first_step_asymptotic_linearization ->
        bPATE.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hPATE_score_transfer :
      pateFirstStep.score_estimator_local_asymptotic_linearity ->
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hPATE_prop_weight :
      patePropensity.component.weighting_design ->
        pateFirstStep.propensity_weighting_design)
    (hPATE_treated_weight :
      pateTreated.component.weighting_design ->
        pateFirstStep.treated_prognostic_weighting_design)
    (hPATE_control_weight :
      pateControl.component.weighting_design ->
        pateFirstStep.control_prognostic_weighting_design)
    (hPATE_prop_component :
      patePropensity.component.component_asymptotic_linearity ->
        pateFirstStep.propensity_component_asymptotic_linearity)
    (hPATE_treated_component :
      pateTreated.component.component_asymptotic_linearity ->
        pateFirstStep.treated_prognostic_component_asymptotic_linearity)
    (hPATE_control_component :
      pateControl.component.component_asymptotic_linearity ->
        pateFirstStep.control_prognostic_component_asymptotic_linearity)
    (hPATE_functional :
      bPATE.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hPATE_equicontinuity :
      bPATE.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hPATE_adjustment :
      bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hPATE_godambe :
      bPATE.positive_bridge.estimated_bridge.estimated_input.godambe_identity)
    (hPATT_exact :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hPATT_bias_bound :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hPATT_geometry_regular :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hPATT_catchment :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hPATT_heterogeneity_moment :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hPATT_heterogeneity_variance :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hPATT_residual_reg :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hPATT_quad :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hPATT_radius_regular :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hPATT_radius_geometry :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hPATT_finite :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hPATT_den :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (hPATT_orthogonality :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hPATT_first_transfer :
      pattFirstStep.first_step_asymptotic_linearization ->
        bPATT.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hPATT_score_transfer :
      pattFirstStep.score_estimator_local_asymptotic_linearity ->
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hPATT_prop_weight :
      pattPropensity.component.weighting_design ->
        pattFirstStep.propensity_weighting_design)
    (hPATT_control_weight :
      pattControl.component.weighting_design ->
        pattFirstStep.control_prognostic_weighting_design)
    (hPATT_prop_component :
      pattPropensity.component.component_asymptotic_linearity ->
        pattFirstStep.propensity_component_asymptotic_linearity)
    (hPATT_control_component :
      pattControl.component.component_asymptotic_linearity ->
        pattFirstStep.control_prognostic_component_asymptotic_linearity)
    (hPATT_functional :
      bPATT.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hPATT_equicontinuity :
      bPATT.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hPATT_adjustment :
      bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hPATT_godambe :
      bPATT.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATE ∧
      ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATT := by
  constructor
  · simpa [ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion] using
      prospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components
        bPATE pateFirstStep patePropensity pateTreated pateControl
        hPATE_exact hPATE_bias_bound hPATE_geometry_regular hPATE_catchment
        hPATE_heterogeneity_moment hPATE_heterogeneity_variance
        hPATE_residual_reg hPATE_quad hPATE_radius_regular
        hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
        hPATE_first_transfer hPATE_score_transfer hPATE_prop_weight
        hPATE_treated_weight hPATE_control_weight hPATE_prop_component
        hPATE_treated_component hPATE_control_component hPATE_functional
        hPATE_equicontinuity hPATE_adjustment hPATE_godambe
  · simpa [ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion] using
      prospective_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components
        bPATT pattFirstStep pattPropensity pattControl hPATT_exact
        hPATT_bias_bound hPATT_geometry_regular hPATT_catchment
        hPATT_heterogeneity_moment hPATT_heterogeneity_variance
        hPATT_residual_reg hPATT_quad hPATT_radius_regular
        hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
        hPATT_first_transfer hPATT_score_transfer hPATT_prop_weight
        hPATT_control_weight hPATT_prop_component hPATT_control_component
        hPATT_functional hPATT_equicontinuity hPATT_adjustment hPATT_godambe

/--
Paired two-sided variance-based Wald coverage for prospective PATE and PATT
from first-step Z-estimator component certificates.
-/
theorem
    prospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components
    {PATEPropSample : ℕ -> Type u} {PATEPropParameter : Type v}
    {PATEPropMoment : Type w} {PATEPropInfluenceFunction : Type x}
    {PATEPropLinearPart : Type y} {PATEPropRemainder : Type z}
    {PATETreatedSample : ℕ -> Type u} {PATETreatedParameter : Type v}
    {PATETreatedMoment : Type w} {PATETreatedInfluenceFunction : Type x}
    {PATETreatedLinearPart : Type y} {PATETreatedRemainder : Type z}
    {PATEControlSample : ℕ -> Type u} {PATEControlParameter : Type v}
    {PATEControlMoment : Type w} {PATEControlInfluenceFunction : Type x}
    {PATEControlLinearPart : Type y} {PATEControlRemainder : Type z}
    {PATTPropSample : ℕ -> Type u} {PATTPropParameter : Type v}
    {PATTPropMoment : Type w} {PATTPropInfluenceFunction : Type x}
    {PATTPropLinearPart : Type y} {PATTPropRemainder : Type z}
    {PATTControlSample : ℕ -> Type u} {PATTControlParameter : Type v}
    {PATTControlMoment : Type w} {PATTControlInfluenceFunction : Type x}
    {PATTControlLinearPart : Type y} {PATTControlRemainder : Type z}
    (bPATE :
      ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (pateFirstStep : PATEDoubleScoreFirstStepAssembly)
    (pattFirstStep : PATTDoubleScoreFirstStepAssembly)
    (patePropensity :
      FirstStepScoreComponentZEvidence PATEPropSample PATEPropParameter
        PATEPropMoment PATEPropInfluenceFunction PATEPropLinearPart
        PATEPropRemainder)
    (pateTreated :
      FirstStepScoreComponentZEvidence PATETreatedSample PATETreatedParameter
        PATETreatedMoment PATETreatedInfluenceFunction PATETreatedLinearPart
        PATETreatedRemainder)
    (pateControl :
      FirstStepScoreComponentZEvidence PATEControlSample PATEControlParameter
        PATEControlMoment PATEControlInfluenceFunction PATEControlLinearPart
        PATEControlRemainder)
    (pattPropensity :
      FirstStepScoreComponentZEvidence PATTPropSample PATTPropParameter
        PATTPropMoment PATTPropInfluenceFunction PATTPropLinearPart
        PATTPropRemainder)
    (pattControl :
      FirstStepScoreComponentZEvidence PATTControlSample PATTControlParameter
        PATTControlMoment PATTControlInfluenceFunction PATTControlLinearPart
        PATTControlRemainder)
    (hPATE_exact :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hPATE_bias_bound :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hPATE_geometry_regular :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hPATE_catchment :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hPATE_heterogeneity_moment :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hPATE_heterogeneity_variance :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hPATE_residual_reg :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hPATE_quad :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hPATE_radius_regular :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hPATE_radius_geometry :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hPATE_finite :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hPATE_den :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (hPATE_orthogonality :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hPATE_first_transfer :
      pateFirstStep.first_step_asymptotic_linearization ->
        bPATE.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hPATE_score_transfer :
      pateFirstStep.score_estimator_local_asymptotic_linearity ->
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hPATE_prop_weight :
      patePropensity.component.weighting_design ->
        pateFirstStep.propensity_weighting_design)
    (hPATE_treated_weight :
      pateTreated.component.weighting_design ->
        pateFirstStep.treated_prognostic_weighting_design)
    (hPATE_control_weight :
      pateControl.component.weighting_design ->
        pateFirstStep.control_prognostic_weighting_design)
    (hPATE_prop_component :
      patePropensity.component.component_asymptotic_linearity ->
        pateFirstStep.propensity_component_asymptotic_linearity)
    (hPATE_treated_component :
      pateTreated.component.component_asymptotic_linearity ->
        pateFirstStep.treated_prognostic_component_asymptotic_linearity)
    (hPATE_control_component :
      pateControl.component.component_asymptotic_linearity ->
        pateFirstStep.control_prognostic_component_asymptotic_linearity)
    (hPATE_functional :
      bPATE.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hPATE_equicontinuity :
      bPATE.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hPATE_adjustment :
      bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hPATE_godambe :
      bPATE.positive_bridge.estimated_bridge.estimated_input.godambe_identity)
    (hPATT_exact :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hPATT_bias_bound :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hPATT_geometry_regular :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hPATT_catchment :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hPATT_heterogeneity_moment :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hPATT_heterogeneity_variance :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hPATT_residual_reg :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hPATT_quad :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hPATT_radius_regular :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hPATT_radius_geometry :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hPATT_finite :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hPATT_den :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (hPATT_orthogonality :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hPATT_first_transfer :
      pattFirstStep.first_step_asymptotic_linearization ->
        bPATT.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hPATT_score_transfer :
      pattFirstStep.score_estimator_local_asymptotic_linearity ->
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hPATT_prop_weight :
      pattPropensity.component.weighting_design ->
        pattFirstStep.propensity_weighting_design)
    (hPATT_control_weight :
      pattControl.component.weighting_design ->
        pattFirstStep.control_prognostic_weighting_design)
    (hPATT_prop_component :
      pattPropensity.component.component_asymptotic_linearity ->
        pattFirstStep.propensity_component_asymptotic_linearity)
    (hPATT_control_component :
      pattControl.component.component_asymptotic_linearity ->
        pattFirstStep.control_prognostic_component_asymptotic_linearity)
    (hPATT_functional :
      bPATT.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hPATT_equicontinuity :
      bPATT.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hPATT_adjustment :
      bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hPATT_godambe :
      bPATT.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATE ∧
      ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATT := by
  constructor
  · simpa [ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion] using
      prospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components
        bPATE pateFirstStep patePropensity pateTreated pateControl
        hPATE_exact hPATE_bias_bound hPATE_geometry_regular hPATE_catchment
        hPATE_heterogeneity_moment hPATE_heterogeneity_variance
        hPATE_residual_reg hPATE_quad hPATE_radius_regular
        hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
        hPATE_first_transfer hPATE_score_transfer hPATE_prop_weight
        hPATE_treated_weight hPATE_control_weight hPATE_prop_component
        hPATE_treated_component hPATE_control_component hPATE_functional
        hPATE_equicontinuity hPATE_adjustment hPATE_godambe
  · simpa [ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion] using
      prospective_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components
        bPATT pattFirstStep pattPropensity pattControl hPATT_exact
        hPATT_bias_bound hPATT_geometry_regular hPATT_catchment
        hPATT_heterogeneity_moment hPATT_heterogeneity_variance
        hPATT_residual_reg hPATT_quad hPATT_radius_regular
        hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
        hPATT_first_transfer hPATT_score_transfer hPATT_prop_weight
        hPATT_control_weight hPATT_prop_component hPATT_control_component
        hPATT_functional hPATT_equicontinuity hPATT_adjustment hPATT_godambe

/--
Paired absolute variance-based Wald coverage for prospective PATE and PATT
from first-step Z-estimator component certificates, with one compact
local-experiment core per estimand.
-/
theorem
    prospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components_core
    {PATEPropSample : ℕ -> Type u} {PATEPropParameter : Type v}
    {PATEPropMoment : Type w} {PATEPropInfluenceFunction : Type x}
    {PATEPropLinearPart : Type y} {PATEPropRemainder : Type z}
    {PATETreatedSample : ℕ -> Type u} {PATETreatedParameter : Type v}
    {PATETreatedMoment : Type w} {PATETreatedInfluenceFunction : Type x}
    {PATETreatedLinearPart : Type y} {PATETreatedRemainder : Type z}
    {PATEControlSample : ℕ -> Type u} {PATEControlParameter : Type v}
    {PATEControlMoment : Type w} {PATEControlInfluenceFunction : Type x}
    {PATEControlLinearPart : Type y} {PATEControlRemainder : Type z}
    {PATTPropSample : ℕ -> Type u} {PATTPropParameter : Type v}
    {PATTPropMoment : Type w} {PATTPropInfluenceFunction : Type x}
    {PATTPropLinearPart : Type y} {PATTPropRemainder : Type z}
    {PATTControlSample : ℕ -> Type u} {PATTControlParameter : Type v}
    {PATTControlMoment : Type w} {PATTControlInfluenceFunction : Type x}
    {PATTControlLinearPart : Type y} {PATTControlRemainder : Type z}
    (bPATE :
      ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (pateFirstStep : PATEDoubleScoreFirstStepAssembly)
    (pattFirstStep : PATTDoubleScoreFirstStepAssembly)
    (patePropensity :
      FirstStepScoreComponentZEvidence PATEPropSample PATEPropParameter
        PATEPropMoment PATEPropInfluenceFunction PATEPropLinearPart
        PATEPropRemainder)
    (pateTreated :
      FirstStepScoreComponentZEvidence PATETreatedSample PATETreatedParameter
        PATETreatedMoment PATETreatedInfluenceFunction PATETreatedLinearPart
        PATETreatedRemainder)
    (pateControl :
      FirstStepScoreComponentZEvidence PATEControlSample PATEControlParameter
        PATEControlMoment PATEControlInfluenceFunction PATEControlLinearPart
        PATEControlRemainder)
    (pattPropensity :
      FirstStepScoreComponentZEvidence PATTPropSample PATTPropParameter
        PATTPropMoment PATTPropInfluenceFunction PATTPropLinearPart
        PATTPropRemainder)
    (pattControl :
      FirstStepScoreComponentZEvidence PATTControlSample PATTControlParameter
        PATTControlMoment PATTControlInfluenceFunction PATTControlLinearPart
        PATTControlRemainder)
    (hPATE_exact :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hPATE_bias_bound :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hPATE_geometry_regular :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hPATE_catchment :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hPATE_heterogeneity_moment :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hPATE_heterogeneity_variance :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hPATE_residual_reg :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hPATE_quad :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hPATE_radius_regular :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hPATE_radius_geometry :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hPATE_finite :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hPATE_den :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (hPATE_orthogonality :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hPATE_first_transfer :
      pateFirstStep.first_step_asymptotic_linearization ->
        bPATE.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hPATE_score_transfer :
      pateFirstStep.score_estimator_local_asymptotic_linearity ->
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hPATE_prop_weight :
      patePropensity.component.weighting_design ->
        pateFirstStep.propensity_weighting_design)
    (hPATE_treated_weight :
      pateTreated.component.weighting_design ->
        pateFirstStep.treated_prognostic_weighting_design)
    (hPATE_control_weight :
      pateControl.component.weighting_design ->
        pateFirstStep.control_prognostic_weighting_design)
    (hPATE_prop_component :
      patePropensity.component.component_asymptotic_linearity ->
        pateFirstStep.propensity_component_asymptotic_linearity)
    (hPATE_treated_component :
      pateTreated.component.component_asymptotic_linearity ->
        pateFirstStep.treated_prognostic_component_asymptotic_linearity)
    (hPATE_control_component :
      pateControl.component.component_asymptotic_linearity ->
        pateFirstStep.control_prognostic_component_asymptotic_linearity)
    (hPATE_adjustment :
      bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hPATE_core :
      EstimatedScoreLocalExperimentVarianceCore
        bPATE.positive_bridge.estimated_bridge.estimated_input)
    (hPATT_exact :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hPATT_bias_bound :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hPATT_geometry_regular :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hPATT_catchment :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hPATT_heterogeneity_moment :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hPATT_heterogeneity_variance :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hPATT_residual_reg :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hPATT_quad :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hPATT_radius_regular :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hPATT_radius_geometry :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hPATT_finite :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hPATT_den :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (hPATT_orthogonality :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hPATT_first_transfer :
      pattFirstStep.first_step_asymptotic_linearization ->
        bPATT.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hPATT_score_transfer :
      pattFirstStep.score_estimator_local_asymptotic_linearity ->
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hPATT_prop_weight :
      pattPropensity.component.weighting_design ->
        pattFirstStep.propensity_weighting_design)
    (hPATT_control_weight :
      pattControl.component.weighting_design ->
        pattFirstStep.control_prognostic_weighting_design)
    (hPATT_prop_component :
      pattPropensity.component.component_asymptotic_linearity ->
        pattFirstStep.propensity_component_asymptotic_linearity)
    (hPATT_control_component :
      pattControl.component.component_asymptotic_linearity ->
        pattFirstStep.control_prognostic_component_asymptotic_linearity)
    (hPATT_adjustment :
      bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hPATT_core :
      EstimatedScoreLocalExperimentVarianceCore
        bPATT.positive_bridge.estimated_bridge.estimated_input) :
    ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATE ∧
      ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATT :=
  prospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components
    bPATE bPATT pateFirstStep pattFirstStep patePropensity pateTreated
    pateControl pattPropensity pattControl hPATE_exact hPATE_bias_bound
    hPATE_geometry_regular hPATE_catchment hPATE_heterogeneity_moment
    hPATE_heterogeneity_variance hPATE_residual_reg hPATE_quad
    hPATE_radius_regular hPATE_radius_geometry hPATE_finite hPATE_den
    hPATE_orthogonality hPATE_first_transfer hPATE_score_transfer
    hPATE_prop_weight hPATE_treated_weight hPATE_control_weight
    hPATE_prop_component hPATE_treated_component hPATE_control_component
    hPATE_core.matching_functional_local_derivative
    hPATE_core.local_stochastic_equicontinuity hPATE_adjustment
    hPATE_core.godambe_identity hPATT_exact hPATT_bias_bound
    hPATT_geometry_regular hPATT_catchment hPATT_heterogeneity_moment
    hPATT_heterogeneity_variance hPATT_residual_reg hPATT_quad
    hPATT_radius_regular hPATT_radius_geometry hPATT_finite hPATT_den
    hPATT_orthogonality hPATT_first_transfer hPATT_score_transfer
    hPATT_prop_weight hPATT_control_weight hPATT_prop_component
    hPATT_control_component
    hPATT_core.matching_functional_local_derivative
    hPATT_core.local_stochastic_equicontinuity hPATT_adjustment
    hPATT_core.godambe_identity

/--
Paired two-sided variance-based Wald coverage for prospective PATE and PATT
from first-step Z-estimator component certificates, with one compact
local-experiment core per estimand.
-/
theorem
    prospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components_core
    {PATEPropSample : ℕ -> Type u} {PATEPropParameter : Type v}
    {PATEPropMoment : Type w} {PATEPropInfluenceFunction : Type x}
    {PATEPropLinearPart : Type y} {PATEPropRemainder : Type z}
    {PATETreatedSample : ℕ -> Type u} {PATETreatedParameter : Type v}
    {PATETreatedMoment : Type w} {PATETreatedInfluenceFunction : Type x}
    {PATETreatedLinearPart : Type y} {PATETreatedRemainder : Type z}
    {PATEControlSample : ℕ -> Type u} {PATEControlParameter : Type v}
    {PATEControlMoment : Type w} {PATEControlInfluenceFunction : Type x}
    {PATEControlLinearPart : Type y} {PATEControlRemainder : Type z}
    {PATTPropSample : ℕ -> Type u} {PATTPropParameter : Type v}
    {PATTPropMoment : Type w} {PATTPropInfluenceFunction : Type x}
    {PATTPropLinearPart : Type y} {PATTPropRemainder : Type z}
    {PATTControlSample : ℕ -> Type u} {PATTControlParameter : Type v}
    {PATTControlMoment : Type w} {PATTControlInfluenceFunction : Type x}
    {PATTControlLinearPart : Type y} {PATTControlRemainder : Type z}
    (bPATE :
      ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (pateFirstStep : PATEDoubleScoreFirstStepAssembly)
    (pattFirstStep : PATTDoubleScoreFirstStepAssembly)
    (patePropensity :
      FirstStepScoreComponentZEvidence PATEPropSample PATEPropParameter
        PATEPropMoment PATEPropInfluenceFunction PATEPropLinearPart
        PATEPropRemainder)
    (pateTreated :
      FirstStepScoreComponentZEvidence PATETreatedSample PATETreatedParameter
        PATETreatedMoment PATETreatedInfluenceFunction PATETreatedLinearPart
        PATETreatedRemainder)
    (pateControl :
      FirstStepScoreComponentZEvidence PATEControlSample PATEControlParameter
        PATEControlMoment PATEControlInfluenceFunction PATEControlLinearPart
        PATEControlRemainder)
    (pattPropensity :
      FirstStepScoreComponentZEvidence PATTPropSample PATTPropParameter
        PATTPropMoment PATTPropInfluenceFunction PATTPropLinearPart
        PATTPropRemainder)
    (pattControl :
      FirstStepScoreComponentZEvidence PATTControlSample PATTControlParameter
        PATTControlMoment PATTControlInfluenceFunction PATTControlLinearPart
        PATTControlRemainder)
    (hPATE_exact :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hPATE_bias_bound :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hPATE_geometry_regular :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hPATE_catchment :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hPATE_heterogeneity_moment :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hPATE_heterogeneity_variance :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hPATE_residual_reg :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hPATE_quad :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hPATE_radius_regular :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hPATE_radius_geometry :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hPATE_finite :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hPATE_den :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (hPATE_orthogonality :
      bPATE.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hPATE_first_transfer :
      pateFirstStep.first_step_asymptotic_linearization ->
        bPATE.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hPATE_score_transfer :
      pateFirstStep.score_estimator_local_asymptotic_linearity ->
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hPATE_prop_weight :
      patePropensity.component.weighting_design ->
        pateFirstStep.propensity_weighting_design)
    (hPATE_treated_weight :
      pateTreated.component.weighting_design ->
        pateFirstStep.treated_prognostic_weighting_design)
    (hPATE_control_weight :
      pateControl.component.weighting_design ->
        pateFirstStep.control_prognostic_weighting_design)
    (hPATE_prop_component :
      patePropensity.component.component_asymptotic_linearity ->
        pateFirstStep.propensity_component_asymptotic_linearity)
    (hPATE_treated_component :
      pateTreated.component.component_asymptotic_linearity ->
        pateFirstStep.treated_prognostic_component_asymptotic_linearity)
    (hPATE_control_component :
      pateControl.component.component_asymptotic_linearity ->
        pateFirstStep.control_prognostic_component_asymptotic_linearity)
    (hPATE_adjustment :
      bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hPATE_core :
      EstimatedScoreLocalExperimentVarianceCore
        bPATE.positive_bridge.estimated_bridge.estimated_input)
    (hPATT_exact :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hPATT_bias_bound :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hPATT_geometry_regular :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hPATT_catchment :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hPATT_heterogeneity_moment :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hPATT_heterogeneity_variance :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hPATT_residual_reg :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hPATT_quad :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hPATT_radius_regular :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hPATT_radius_geometry :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hPATT_finite :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hPATT_den :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (hPATT_orthogonality :
      bPATT.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hPATT_first_transfer :
      pattFirstStep.first_step_asymptotic_linearization ->
        bPATT.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hPATT_score_transfer :
      pattFirstStep.score_estimator_local_asymptotic_linearity ->
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hPATT_prop_weight :
      pattPropensity.component.weighting_design ->
        pattFirstStep.propensity_weighting_design)
    (hPATT_control_weight :
      pattControl.component.weighting_design ->
        pattFirstStep.control_prognostic_weighting_design)
    (hPATT_prop_component :
      pattPropensity.component.component_asymptotic_linearity ->
        pattFirstStep.propensity_component_asymptotic_linearity)
    (hPATT_control_component :
      pattControl.component.component_asymptotic_linearity ->
        pattFirstStep.control_prognostic_component_asymptotic_linearity)
    (hPATT_adjustment :
      bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hPATT_core :
      EstimatedScoreLocalExperimentVarianceCore
        bPATT.positive_bridge.estimated_bridge.estimated_input) :
    ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATE ∧
      ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATT :=
  prospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components
    bPATE bPATT pateFirstStep pattFirstStep patePropensity pateTreated
    pateControl pattPropensity pattControl hPATE_exact hPATE_bias_bound
    hPATE_geometry_regular hPATE_catchment hPATE_heterogeneity_moment
    hPATE_heterogeneity_variance hPATE_residual_reg hPATE_quad
    hPATE_radius_regular hPATE_radius_geometry hPATE_finite hPATE_den
    hPATE_orthogonality hPATE_first_transfer hPATE_score_transfer
    hPATE_prop_weight hPATE_treated_weight hPATE_control_weight
    hPATE_prop_component hPATE_treated_component hPATE_control_component
    hPATE_core.matching_functional_local_derivative
    hPATE_core.local_stochastic_equicontinuity hPATE_adjustment
    hPATE_core.godambe_identity hPATT_exact hPATT_bias_bound
    hPATT_geometry_regular hPATT_catchment hPATT_heterogeneity_moment
    hPATT_heterogeneity_variance hPATT_residual_reg hPATT_quad
    hPATT_radius_regular hPATT_radius_geometry hPATT_finite hPATT_den
    hPATT_orthogonality hPATT_first_transfer hPATT_score_transfer
    hPATT_prop_weight hPATT_control_weight hPATT_prop_component
    hPATT_control_component
    hPATT_core.matching_functional_local_derivative
    hPATT_core.local_stochastic_equicontinuity hPATT_adjustment
    hPATT_core.godambe_identity

end WDSM
end Matching
end StatInference
