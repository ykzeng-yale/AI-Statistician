import StatInference.Matching.WDSM.RetrospectivePATEEstimatedScoreAudit
import StatInference.Matching.WDSM.RetrospectivePATTEstimatedScoreAudit

/-!
# Paired retrospective estimated-score audit interface

This module packages the retrospective PATE and PATT estimated-score audit
routes into one paired conclusion for downstream WDSM inference statements.
-/

namespace StatInference
namespace Matching
namespace WDSM

universe u v w x y z

/--
Paired retrospective PATE/PATT estimated-score asymptotic normality and
variance formulas from audited known-score bridges and local-experiment
assumptions.
-/
theorem retrospective_pate_patt_estimated_score_normality_and_variance_of_audited_local_experiment
    (pate : RetrospectivePATEEstimatedScoreAuditBridge)
    (patt : RetrospectivePATTEstimatedScoreAuditBridge)
    (hpateExact :
      pate.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hpateBiasBound :
      pate.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hpateGeometryRegular :
      pate.known_score_bridge.geometry_bridge.score_density_regular)
    (hpateCatchment :
      pate.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hpateHeterogeneityMoment :
      pate.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hpateHeterogeneityVariance :
      pate.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hpateResidualReg :
      pate.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hpateQuad :
      pate.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hpateRadiusRegular :
      pate.known_score_bridge.radius_bridge.score_density_regular)
    (hpateRadiusGeometry :
      pate.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hpateFinite :
      pate.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hpateDen :
      pate.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (hpateOrthogonality :
      pate.known_score_bridge.variance_bridge.component_orthogonality)
    (hpateFirst : pate.estimated_input.first_step_asymptotic_linearization)
    (hpateScore :
      pate.estimated_input.score_estimator_local_asymptotic_linearity)
    (hpateFunctional :
      pate.estimated_input.matching_functional_local_derivative)
    (hpateEquicontinuity :
      pate.estimated_input.local_stochastic_equicontinuity)
    (hpateAdjustment : pate.estimated_input.score_adjustment_algebra)
    (hpateGodambe : pate.estimated_input.godambe_identity)
    (hpattExact :
      patt.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hpattBiasBound :
      patt.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hpattGeometryRegular :
      patt.known_score_bridge.geometry_bridge.score_density_regular)
    (hpattCatchment :
      patt.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hpattHeterogeneityMoment :
      patt.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hpattHeterogeneityVariance :
      patt.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hpattResidualReg :
      patt.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hpattQuad :
      patt.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hpattRadiusRegular :
      patt.known_score_bridge.radius_bridge.score_density_regular)
    (hpattRadiusGeometry :
      patt.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hpattFinite :
      patt.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hpattDen :
      patt.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (hpattOrthogonality :
      patt.known_score_bridge.variance_bridge.component_orthogonality)
    (hpattFirst : patt.estimated_input.first_step_asymptotic_linearization)
    (hpattScore :
      patt.estimated_input.score_estimator_local_asymptotic_linearity)
    (hpattFunctional :
      patt.estimated_input.matching_functional_local_derivative)
    (hpattEquicontinuity :
      patt.estimated_input.local_stochastic_equicontinuity)
    (hpattAdjustment : patt.estimated_input.score_adjustment_algebra)
    (hpattGodambe : patt.estimated_input.godambe_identity) :
    (pate.estimated_score_asymptotic_normality ∧
        pate.estimated_score_variance_formula) ∧
      (patt.estimated_score_asymptotic_normality ∧
        patt.estimated_score_variance_formula) :=
  ⟨retrospective_pate_estimated_score_normality_and_variance_of_audited_local_experiment
      pate hpateExact hpateBiasBound hpateGeometryRegular hpateCatchment
      hpateHeterogeneityMoment hpateHeterogeneityVariance hpateResidualReg
      hpateQuad hpateRadiusRegular hpateRadiusGeometry hpateFinite hpateDen
      hpateOrthogonality hpateFirst hpateScore hpateFunctional
      hpateEquicontinuity hpateAdjustment hpateGodambe,
    retrospective_patt_estimated_score_normality_and_variance_of_audited_local_experiment
      patt hpattExact hpattBiasBound hpattGeometryRegular hpattCatchment
      hpattHeterogeneityMoment hpattHeterogeneityVariance hpattResidualReg
      hpattQuad hpattRadiusRegular hpattRadiusGeometry hpattFinite hpattDen
      hpattOrthogonality hpattFirst hpattScore hpattFunctional
      hpattEquicontinuity hpattAdjustment hpattGodambe⟩

/--
Paired retrospective PATE/PATT estimated-score asymptotic normality and
variance formulas from audited known-score bridges, with one compact
local-experiment core per estimand.
-/
theorem
    retrospective_pate_patt_estimated_score_normality_and_variance_of_audited_local_experiment_cores
    (pate : RetrospectivePATEEstimatedScoreAuditBridge)
    (patt : RetrospectivePATTEstimatedScoreAuditBridge)
    (hpateExact :
      pate.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hpateBiasBound :
      pate.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hpateGeometryRegular :
      pate.known_score_bridge.geometry_bridge.score_density_regular)
    (hpateCatchment :
      pate.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hpateHeterogeneityMoment :
      pate.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hpateHeterogeneityVariance :
      pate.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hpateResidualReg :
      pate.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hpateQuad :
      pate.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hpateRadiusRegular :
      pate.known_score_bridge.radius_bridge.score_density_regular)
    (hpateRadiusGeometry :
      pate.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hpateFinite :
      pate.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hpateDen :
      pate.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (hpateOrthogonality :
      pate.known_score_bridge.variance_bridge.component_orthogonality)
    (hpateFirst : pate.estimated_input.first_step_asymptotic_linearization)
    (hpateScore :
      pate.estimated_input.score_estimator_local_asymptotic_linearity)
    (hpateAdjustment : pate.estimated_input.score_adjustment_algebra)
    (hpateCore :
      EstimatedScoreLocalExperimentVarianceCore pate.estimated_input)
    (hpattExact :
      patt.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hpattBiasBound :
      patt.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hpattGeometryRegular :
      patt.known_score_bridge.geometry_bridge.score_density_regular)
    (hpattCatchment :
      patt.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hpattHeterogeneityMoment :
      patt.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hpattHeterogeneityVariance :
      patt.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hpattResidualReg :
      patt.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hpattQuad :
      patt.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hpattRadiusRegular :
      patt.known_score_bridge.radius_bridge.score_density_regular)
    (hpattRadiusGeometry :
      patt.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hpattFinite :
      patt.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hpattDen :
      patt.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (hpattOrthogonality :
      patt.known_score_bridge.variance_bridge.component_orthogonality)
    (hpattFirst : patt.estimated_input.first_step_asymptotic_linearization)
    (hpattScore :
      patt.estimated_input.score_estimator_local_asymptotic_linearity)
    (hpattAdjustment : patt.estimated_input.score_adjustment_algebra)
    (hpattCore :
      EstimatedScoreLocalExperimentVarianceCore patt.estimated_input) :
    (pate.estimated_score_asymptotic_normality ∧
        pate.estimated_score_variance_formula) ∧
      (patt.estimated_score_asymptotic_normality ∧
        patt.estimated_score_variance_formula) :=
  ⟨retrospective_pate_estimated_score_normality_and_variance_of_audited_local_experiment_core
      pate hpateExact hpateBiasBound hpateGeometryRegular hpateCatchment
      hpateHeterogeneityMoment hpateHeterogeneityVariance hpateResidualReg
      hpateQuad hpateRadiusRegular hpateRadiusGeometry hpateFinite hpateDen
      hpateOrthogonality hpateFirst hpateScore hpateAdjustment hpateCore,
    retrospective_patt_estimated_score_normality_and_variance_of_audited_local_experiment_core
      patt hpattExact hpattBiasBound hpattGeometryRegular hpattCatchment
      hpattHeterogeneityMoment hpattHeterogeneityVariance hpattResidualReg
      hpattQuad hpattRadiusRegular hpattRadiusGeometry hpattFinite hpattDen
      hpattOrthogonality hpattFirst hpattScore hpattAdjustment hpattCore⟩

/--
Paired retrospective PATE/PATT estimated-score asymptotic normality and
variance formulas from audited known-score bridges and first-step Z-estimator
component certificates.
-/
theorem retrospective_pate_patt_estimated_score_normality_and_variance_of_audited_z_components
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
    (pate : RetrospectivePATEEstimatedScoreAuditBridge)
    (patt : RetrospectivePATTEstimatedScoreAuditBridge)
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
    (hpateExact :
      pate.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hpateBiasBound :
      pate.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hpateGeometryRegular :
      pate.known_score_bridge.geometry_bridge.score_density_regular)
    (hpateCatchment :
      pate.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hpateHeterogeneityMoment :
      pate.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hpateHeterogeneityVariance :
      pate.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hpateResidualReg :
      pate.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hpateQuad :
      pate.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hpateRadiusRegular :
      pate.known_score_bridge.radius_bridge.score_density_regular)
    (hpateRadiusGeometry :
      pate.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hpateFinite :
      pate.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hpateDen :
      pate.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (hpateOrthogonality :
      pate.known_score_bridge.variance_bridge.component_orthogonality)
    (hpate_first_transfer :
      pateFirstStep.first_step_asymptotic_linearization ->
        pate.estimated_input.first_step_asymptotic_linearization)
    (hpate_score_transfer :
      pateFirstStep.score_estimator_local_asymptotic_linearity ->
        pate.estimated_input.score_estimator_local_asymptotic_linearity)
    (hpate_prop_weight :
      patePropensity.component.weighting_design ->
        pateFirstStep.propensity_weighting_design)
    (hpate_treated_weight :
      pateTreated.component.weighting_design ->
        pateFirstStep.treated_prognostic_weighting_design)
    (hpate_control_weight :
      pateControl.component.weighting_design ->
        pateFirstStep.control_prognostic_weighting_design)
    (hpate_prop_component :
      patePropensity.component.component_asymptotic_linearity ->
        pateFirstStep.propensity_component_asymptotic_linearity)
    (hpate_treated_component :
      pateTreated.component.component_asymptotic_linearity ->
        pateFirstStep.treated_prognostic_component_asymptotic_linearity)
    (hpate_control_component :
      pateControl.component.component_asymptotic_linearity ->
        pateFirstStep.control_prognostic_component_asymptotic_linearity)
    (hpateFunctional :
      pate.estimated_input.matching_functional_local_derivative)
    (hpateEquicontinuity :
      pate.estimated_input.local_stochastic_equicontinuity)
    (hpateAdjustment : pate.estimated_input.score_adjustment_algebra)
    (hpateGodambe : pate.estimated_input.godambe_identity)
    (hpattExact :
      patt.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hpattBiasBound :
      patt.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hpattGeometryRegular :
      patt.known_score_bridge.geometry_bridge.score_density_regular)
    (hpattCatchment :
      patt.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hpattHeterogeneityMoment :
      patt.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hpattHeterogeneityVariance :
      patt.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hpattResidualReg :
      patt.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hpattQuad :
      patt.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hpattRadiusRegular :
      patt.known_score_bridge.radius_bridge.score_density_regular)
    (hpattRadiusGeometry :
      patt.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hpattFinite :
      patt.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hpattDen :
      patt.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (hpattOrthogonality :
      patt.known_score_bridge.variance_bridge.component_orthogonality)
    (hpatt_first_transfer :
      pattFirstStep.first_step_asymptotic_linearization ->
        patt.estimated_input.first_step_asymptotic_linearization)
    (hpatt_score_transfer :
      pattFirstStep.score_estimator_local_asymptotic_linearity ->
        patt.estimated_input.score_estimator_local_asymptotic_linearity)
    (hpatt_prop_weight :
      pattPropensity.component.weighting_design ->
        pattFirstStep.propensity_weighting_design)
    (hpatt_control_weight :
      pattControl.component.weighting_design ->
        pattFirstStep.control_prognostic_weighting_design)
    (hpatt_prop_component :
      pattPropensity.component.component_asymptotic_linearity ->
        pattFirstStep.propensity_component_asymptotic_linearity)
    (hpatt_control_component :
      pattControl.component.component_asymptotic_linearity ->
        pattFirstStep.control_prognostic_component_asymptotic_linearity)
    (hpattFunctional :
      patt.estimated_input.matching_functional_local_derivative)
    (hpattEquicontinuity :
      patt.estimated_input.local_stochastic_equicontinuity)
    (hpattAdjustment : patt.estimated_input.score_adjustment_algebra)
    (hpattGodambe : patt.estimated_input.godambe_identity) :
    (pate.estimated_score_asymptotic_normality ∧
        pate.estimated_score_variance_formula) ∧
      (patt.estimated_score_asymptotic_normality ∧
        patt.estimated_score_variance_formula) :=
  ⟨retrospective_pate_estimated_score_normality_and_variance_of_audited_z_components
      pate pateFirstStep patePropensity pateTreated pateControl hpateExact
      hpateBiasBound hpateGeometryRegular hpateCatchment
      hpateHeterogeneityMoment hpateHeterogeneityVariance hpateResidualReg
      hpateQuad hpateRadiusRegular hpateRadiusGeometry hpateFinite hpateDen
      hpateOrthogonality hpate_first_transfer hpate_score_transfer
      hpate_prop_weight hpate_treated_weight hpate_control_weight
      hpate_prop_component hpate_treated_component hpate_control_component
      hpateFunctional hpateEquicontinuity hpateAdjustment hpateGodambe,
    retrospective_patt_estimated_score_normality_and_variance_of_audited_z_components
      patt pattFirstStep pattPropensity pattControl hpattExact
      hpattBiasBound hpattGeometryRegular hpattCatchment
      hpattHeterogeneityMoment hpattHeterogeneityVariance hpattResidualReg
      hpattQuad hpattRadiusRegular hpattRadiusGeometry hpattFinite hpattDen
      hpattOrthogonality hpatt_first_transfer hpatt_score_transfer
      hpatt_prop_weight hpatt_control_weight hpatt_prop_component
      hpatt_control_component hpattFunctional hpattEquicontinuity
      hpattAdjustment hpattGodambe⟩

/--
Paired retrospective PATE/PATT estimated-score asymptotic normality and
variance formulas from audited known-score bridges and first-step Z-estimator
component certificates, with one compact local-experiment core per estimand.
-/
theorem
    retrospective_pate_patt_estimated_score_normality_and_variance_of_audited_z_components_cores
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
    (pate : RetrospectivePATEEstimatedScoreAuditBridge)
    (patt : RetrospectivePATTEstimatedScoreAuditBridge)
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
    (hpateExact :
      pate.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hpateBiasBound :
      pate.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hpateGeometryRegular :
      pate.known_score_bridge.geometry_bridge.score_density_regular)
    (hpateCatchment :
      pate.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hpateHeterogeneityMoment :
      pate.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hpateHeterogeneityVariance :
      pate.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hpateResidualReg :
      pate.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hpateQuad :
      pate.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hpateRadiusRegular :
      pate.known_score_bridge.radius_bridge.score_density_regular)
    (hpateRadiusGeometry :
      pate.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hpateFinite :
      pate.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hpateDen :
      pate.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (hpateOrthogonality :
      pate.known_score_bridge.variance_bridge.component_orthogonality)
    (hpate_first_transfer :
      pateFirstStep.first_step_asymptotic_linearization ->
        pate.estimated_input.first_step_asymptotic_linearization)
    (hpate_score_transfer :
      pateFirstStep.score_estimator_local_asymptotic_linearity ->
        pate.estimated_input.score_estimator_local_asymptotic_linearity)
    (hpate_prop_weight :
      patePropensity.component.weighting_design ->
        pateFirstStep.propensity_weighting_design)
    (hpate_treated_weight :
      pateTreated.component.weighting_design ->
        pateFirstStep.treated_prognostic_weighting_design)
    (hpate_control_weight :
      pateControl.component.weighting_design ->
        pateFirstStep.control_prognostic_weighting_design)
    (hpate_prop_component :
      patePropensity.component.component_asymptotic_linearity ->
        pateFirstStep.propensity_component_asymptotic_linearity)
    (hpate_treated_component :
      pateTreated.component.component_asymptotic_linearity ->
        pateFirstStep.treated_prognostic_component_asymptotic_linearity)
    (hpate_control_component :
      pateControl.component.component_asymptotic_linearity ->
        pateFirstStep.control_prognostic_component_asymptotic_linearity)
    (hpateAdjustment : pate.estimated_input.score_adjustment_algebra)
    (hpateCore :
      EstimatedScoreLocalExperimentVarianceCore pate.estimated_input)
    (hpattExact :
      patt.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hpattBiasBound :
      patt.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hpattGeometryRegular :
      patt.known_score_bridge.geometry_bridge.score_density_regular)
    (hpattCatchment :
      patt.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hpattHeterogeneityMoment :
      patt.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hpattHeterogeneityVariance :
      patt.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hpattResidualReg :
      patt.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hpattQuad :
      patt.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hpattRadiusRegular :
      patt.known_score_bridge.radius_bridge.score_density_regular)
    (hpattRadiusGeometry :
      patt.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hpattFinite :
      patt.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hpattDen :
      patt.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (hpattOrthogonality :
      patt.known_score_bridge.variance_bridge.component_orthogonality)
    (hpatt_first_transfer :
      pattFirstStep.first_step_asymptotic_linearization ->
        patt.estimated_input.first_step_asymptotic_linearization)
    (hpatt_score_transfer :
      pattFirstStep.score_estimator_local_asymptotic_linearity ->
        patt.estimated_input.score_estimator_local_asymptotic_linearity)
    (hpatt_prop_weight :
      pattPropensity.component.weighting_design ->
        pattFirstStep.propensity_weighting_design)
    (hpatt_control_weight :
      pattControl.component.weighting_design ->
        pattFirstStep.control_prognostic_weighting_design)
    (hpatt_prop_component :
      pattPropensity.component.component_asymptotic_linearity ->
        pattFirstStep.propensity_component_asymptotic_linearity)
    (hpatt_control_component :
      pattControl.component.component_asymptotic_linearity ->
        pattFirstStep.control_prognostic_component_asymptotic_linearity)
    (hpattAdjustment : patt.estimated_input.score_adjustment_algebra)
    (hpattCore :
      EstimatedScoreLocalExperimentVarianceCore patt.estimated_input) :
    (pate.estimated_score_asymptotic_normality ∧
        pate.estimated_score_variance_formula) ∧
      (patt.estimated_score_asymptotic_normality ∧
        patt.estimated_score_variance_formula) :=
  ⟨retrospective_pate_estimated_score_normality_and_variance_of_audited_z_components_core
      pate pateFirstStep patePropensity pateTreated pateControl hpateExact
      hpateBiasBound hpateGeometryRegular hpateCatchment
      hpateHeterogeneityMoment hpateHeterogeneityVariance hpateResidualReg
      hpateQuad hpateRadiusRegular hpateRadiusGeometry hpateFinite hpateDen
      hpateOrthogonality hpate_first_transfer hpate_score_transfer
      hpate_prop_weight hpate_treated_weight hpate_control_weight
      hpate_prop_component hpate_treated_component hpate_control_component
      hpateAdjustment hpateCore,
    retrospective_patt_estimated_score_normality_and_variance_of_audited_z_components_core
      patt pattFirstStep pattPropensity pattControl hpattExact
      hpattBiasBound hpattGeometryRegular hpattCatchment
      hpattHeterogeneityMoment hpattHeterogeneityVariance hpattResidualReg
      hpattQuad hpattRadiusRegular hpattRadiusGeometry hpattFinite hpattDen
      hpattOrthogonality hpatt_first_transfer hpatt_score_transfer
      hpatt_prop_weight hpatt_control_weight hpatt_prop_component
      hpatt_control_component hpattAdjustment hpattCore⟩

/--
Paired retrospective PATE/PATT estimated-score normality conclusions and paired
variance formulas from audited known-score bridges and first-step Z-estimator
component certificates, with one compact local-experiment core per estimand.
-/
theorem
    retrospective_pate_patt_estimated_score_paired_normality_and_paired_variance_of_audited_z_components_cores
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
    (pate : RetrospectivePATEEstimatedScoreAuditBridge)
    (patt : RetrospectivePATTEstimatedScoreAuditBridge)
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
    (hpateExact :
      pate.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hpateBiasBound :
      pate.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hpateGeometryRegular :
      pate.known_score_bridge.geometry_bridge.score_density_regular)
    (hpateCatchment :
      pate.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hpateHeterogeneityMoment :
      pate.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hpateHeterogeneityVariance :
      pate.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hpateResidualReg :
      pate.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hpateQuad :
      pate.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hpateRadiusRegular :
      pate.known_score_bridge.radius_bridge.score_density_regular)
    (hpateRadiusGeometry :
      pate.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hpateFinite :
      pate.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hpateDen :
      pate.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (hpateOrthogonality :
      pate.known_score_bridge.variance_bridge.component_orthogonality)
    (hpate_first_transfer :
      pateFirstStep.first_step_asymptotic_linearization ->
        pate.estimated_input.first_step_asymptotic_linearization)
    (hpate_score_transfer :
      pateFirstStep.score_estimator_local_asymptotic_linearity ->
        pate.estimated_input.score_estimator_local_asymptotic_linearity)
    (hpate_prop_weight :
      patePropensity.component.weighting_design ->
        pateFirstStep.propensity_weighting_design)
    (hpate_treated_weight :
      pateTreated.component.weighting_design ->
        pateFirstStep.treated_prognostic_weighting_design)
    (hpate_control_weight :
      pateControl.component.weighting_design ->
        pateFirstStep.control_prognostic_weighting_design)
    (hpate_prop_component :
      patePropensity.component.component_asymptotic_linearity ->
        pateFirstStep.propensity_component_asymptotic_linearity)
    (hpate_treated_component :
      pateTreated.component.component_asymptotic_linearity ->
        pateFirstStep.treated_prognostic_component_asymptotic_linearity)
    (hpate_control_component :
      pateControl.component.component_asymptotic_linearity ->
        pateFirstStep.control_prognostic_component_asymptotic_linearity)
    (hpateAdjustment : pate.estimated_input.score_adjustment_algebra)
    (hpateCore :
      EstimatedScoreLocalExperimentVarianceCore pate.estimated_input)
    (hpattExact :
      patt.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hpattBiasBound :
      patt.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hpattGeometryRegular :
      patt.known_score_bridge.geometry_bridge.score_density_regular)
    (hpattCatchment :
      patt.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hpattHeterogeneityMoment :
      patt.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hpattHeterogeneityVariance :
      patt.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hpattResidualReg :
      patt.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hpattQuad :
      patt.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hpattRadiusRegular :
      patt.known_score_bridge.radius_bridge.score_density_regular)
    (hpattRadiusGeometry :
      patt.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hpattFinite :
      patt.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hpattDen :
      patt.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (hpattOrthogonality :
      patt.known_score_bridge.variance_bridge.component_orthogonality)
    (hpatt_first_transfer :
      pattFirstStep.first_step_asymptotic_linearization ->
        patt.estimated_input.first_step_asymptotic_linearization)
    (hpatt_score_transfer :
      pattFirstStep.score_estimator_local_asymptotic_linearity ->
        patt.estimated_input.score_estimator_local_asymptotic_linearity)
    (hpatt_prop_weight :
      pattPropensity.component.weighting_design ->
        pattFirstStep.propensity_weighting_design)
    (hpatt_control_weight :
      pattControl.component.weighting_design ->
        pattFirstStep.control_prognostic_weighting_design)
    (hpatt_prop_component :
      pattPropensity.component.component_asymptotic_linearity ->
        pattFirstStep.propensity_component_asymptotic_linearity)
    (hpatt_control_component :
      pattControl.component.component_asymptotic_linearity ->
        pattFirstStep.control_prognostic_component_asymptotic_linearity)
    (hpattAdjustment : patt.estimated_input.score_adjustment_algebra)
    (hpattCore :
      EstimatedScoreLocalExperimentVarianceCore patt.estimated_input) :
    (pate.estimated_score_asymptotic_normality ∧
        patt.estimated_score_asymptotic_normality) ∧
      (pate.estimated_score_variance_formula ∧
        patt.estimated_score_variance_formula) := by
  have h :=
    retrospective_pate_patt_estimated_score_normality_and_variance_of_audited_z_components_cores
      pate patt pateFirstStep pattFirstStep patePropensity pateTreated
      pateControl pattPropensity pattControl hpateExact hpateBiasBound
      hpateGeometryRegular hpateCatchment hpateHeterogeneityMoment
      hpateHeterogeneityVariance hpateResidualReg hpateQuad
      hpateRadiusRegular hpateRadiusGeometry hpateFinite hpateDen
      hpateOrthogonality hpate_first_transfer hpate_score_transfer
      hpate_prop_weight hpate_treated_weight hpate_control_weight
      hpate_prop_component hpate_treated_component hpate_control_component
      hpateAdjustment hpateCore hpattExact hpattBiasBound
      hpattGeometryRegular hpattCatchment hpattHeterogeneityMoment
      hpattHeterogeneityVariance hpattResidualReg hpattQuad
      hpattRadiusRegular hpattRadiusGeometry hpattFinite hpattDen
      hpattOrthogonality hpatt_first_transfer hpatt_score_transfer
      hpatt_prop_weight hpatt_control_weight hpatt_prop_component
      hpatt_control_component hpattAdjustment hpattCore
  exact ⟨⟨h.1.1, h.2.1⟩, ⟨h.1.2, h.2.2⟩⟩

/--
Paired retrospective PATE/PATT estimated-score normality conclusions and
paired variance formulas, regrouped for downstream Wald inference statements.
-/
theorem retrospective_pate_patt_estimated_score_paired_normality_and_paired_variance_of_audited_local_experiment
    (pate : RetrospectivePATEEstimatedScoreAuditBridge)
    (patt : RetrospectivePATTEstimatedScoreAuditBridge)
    (hpateExact :
      pate.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hpateBiasBound :
      pate.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hpateGeometryRegular :
      pate.known_score_bridge.geometry_bridge.score_density_regular)
    (hpateCatchment :
      pate.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hpateHeterogeneityMoment :
      pate.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hpateHeterogeneityVariance :
      pate.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hpateResidualReg :
      pate.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hpateQuad :
      pate.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hpateRadiusRegular :
      pate.known_score_bridge.radius_bridge.score_density_regular)
    (hpateRadiusGeometry :
      pate.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hpateFinite :
      pate.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hpateDen :
      pate.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (hpateOrthogonality :
      pate.known_score_bridge.variance_bridge.component_orthogonality)
    (hpateFirst : pate.estimated_input.first_step_asymptotic_linearization)
    (hpateScore :
      pate.estimated_input.score_estimator_local_asymptotic_linearity)
    (hpateFunctional :
      pate.estimated_input.matching_functional_local_derivative)
    (hpateEquicontinuity :
      pate.estimated_input.local_stochastic_equicontinuity)
    (hpateAdjustment : pate.estimated_input.score_adjustment_algebra)
    (hpateGodambe : pate.estimated_input.godambe_identity)
    (hpattExact :
      patt.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hpattBiasBound :
      patt.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hpattGeometryRegular :
      patt.known_score_bridge.geometry_bridge.score_density_regular)
    (hpattCatchment :
      patt.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hpattHeterogeneityMoment :
      patt.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hpattHeterogeneityVariance :
      patt.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hpattResidualReg :
      patt.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hpattQuad :
      patt.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hpattRadiusRegular :
      patt.known_score_bridge.radius_bridge.score_density_regular)
    (hpattRadiusGeometry :
      patt.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hpattFinite :
      patt.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hpattDen :
      patt.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (hpattOrthogonality :
      patt.known_score_bridge.variance_bridge.component_orthogonality)
    (hpattFirst : patt.estimated_input.first_step_asymptotic_linearization)
    (hpattScore :
      patt.estimated_input.score_estimator_local_asymptotic_linearity)
    (hpattFunctional :
      patt.estimated_input.matching_functional_local_derivative)
    (hpattEquicontinuity :
      patt.estimated_input.local_stochastic_equicontinuity)
    (hpattAdjustment : patt.estimated_input.score_adjustment_algebra)
    (hpattGodambe : patt.estimated_input.godambe_identity) :
    (pate.estimated_score_asymptotic_normality ∧
        patt.estimated_score_asymptotic_normality) ∧
      (pate.estimated_score_variance_formula ∧
        patt.estimated_score_variance_formula) := by
  have h :=
    retrospective_pate_patt_estimated_score_normality_and_variance_of_audited_local_experiment
      pate patt hpateExact hpateBiasBound hpateGeometryRegular
      hpateCatchment hpateHeterogeneityMoment hpateHeterogeneityVariance
      hpateResidualReg hpateQuad hpateRadiusRegular hpateRadiusGeometry
      hpateFinite hpateDen hpateOrthogonality hpateFirst hpateScore
      hpateFunctional hpateEquicontinuity hpateAdjustment hpateGodambe
      hpattExact hpattBiasBound hpattGeometryRegular hpattCatchment
      hpattHeterogeneityMoment hpattHeterogeneityVariance hpattResidualReg
      hpattQuad hpattRadiusRegular hpattRadiusGeometry hpattFinite hpattDen
      hpattOrthogonality hpattFirst hpattScore hpattFunctional
      hpattEquicontinuity hpattAdjustment hpattGodambe
  exact ⟨⟨h.1.1, h.2.1⟩, ⟨h.1.2, h.2.2⟩⟩

/--
Paired retrospective PATE/PATT estimated-score normality conclusions and
paired variance formulas from audited known-score bridges, with one compact
local-experiment core per estimand.
-/
theorem
    retrospective_pate_patt_estimated_score_paired_normality_and_paired_variance_of_audited_local_experiment_cores
    (pate : RetrospectivePATEEstimatedScoreAuditBridge)
    (patt : RetrospectivePATTEstimatedScoreAuditBridge)
    (hpateExact :
      pate.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hpateBiasBound :
      pate.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hpateGeometryRegular :
      pate.known_score_bridge.geometry_bridge.score_density_regular)
    (hpateCatchment :
      pate.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hpateHeterogeneityMoment :
      pate.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hpateHeterogeneityVariance :
      pate.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hpateResidualReg :
      pate.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hpateQuad :
      pate.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hpateRadiusRegular :
      pate.known_score_bridge.radius_bridge.score_density_regular)
    (hpateRadiusGeometry :
      pate.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hpateFinite :
      pate.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hpateDen :
      pate.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (hpateOrthogonality :
      pate.known_score_bridge.variance_bridge.component_orthogonality)
    (hpateFirst : pate.estimated_input.first_step_asymptotic_linearization)
    (hpateScore :
      pate.estimated_input.score_estimator_local_asymptotic_linearity)
    (hpateAdjustment : pate.estimated_input.score_adjustment_algebra)
    (hpateCore :
      EstimatedScoreLocalExperimentVarianceCore pate.estimated_input)
    (hpattExact :
      patt.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hpattBiasBound :
      patt.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hpattGeometryRegular :
      patt.known_score_bridge.geometry_bridge.score_density_regular)
    (hpattCatchment :
      patt.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hpattHeterogeneityMoment :
      patt.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hpattHeterogeneityVariance :
      patt.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hpattResidualReg :
      patt.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hpattQuad :
      patt.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hpattRadiusRegular :
      patt.known_score_bridge.radius_bridge.score_density_regular)
    (hpattRadiusGeometry :
      patt.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hpattFinite :
      patt.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hpattDen :
      patt.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (hpattOrthogonality :
      patt.known_score_bridge.variance_bridge.component_orthogonality)
    (hpattFirst : patt.estimated_input.first_step_asymptotic_linearization)
    (hpattScore :
      patt.estimated_input.score_estimator_local_asymptotic_linearity)
    (hpattAdjustment : patt.estimated_input.score_adjustment_algebra)
    (hpattCore :
      EstimatedScoreLocalExperimentVarianceCore patt.estimated_input) :
    (pate.estimated_score_asymptotic_normality ∧
        patt.estimated_score_asymptotic_normality) ∧
      (pate.estimated_score_variance_formula ∧
        patt.estimated_score_variance_formula) := by
  have h :=
    retrospective_pate_patt_estimated_score_normality_and_variance_of_audited_local_experiment_cores
      pate patt hpateExact hpateBiasBound hpateGeometryRegular
      hpateCatchment hpateHeterogeneityMoment hpateHeterogeneityVariance
      hpateResidualReg hpateQuad hpateRadiusRegular hpateRadiusGeometry
      hpateFinite hpateDen hpateOrthogonality hpateFirst hpateScore
      hpateAdjustment hpateCore hpattExact hpattBiasBound
      hpattGeometryRegular hpattCatchment hpattHeterogeneityMoment
      hpattHeterogeneityVariance hpattResidualReg hpattQuad
      hpattRadiusRegular hpattRadiusGeometry hpattFinite hpattDen
      hpattOrthogonality hpattFirst hpattScore hpattAdjustment hpattCore
  exact ⟨⟨h.1.1, h.2.1⟩, ⟨h.1.2, h.2.2⟩⟩

end WDSM
end Matching
end StatInference
