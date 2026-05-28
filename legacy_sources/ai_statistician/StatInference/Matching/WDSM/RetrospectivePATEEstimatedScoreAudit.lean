import StatInference.Matching.WDSM.RetrospectivePATEKnownScoreVariance
import StatInference.Matching.WDSM.FirstStepZEstimatorBridge

/-!
# Retrospective PATE estimated-score audit interface

This module records the estimated-score layer for retrospective PATE.  It
separates the audited retrospective known-score normality/variance route from
the first-step and non-smooth local-experiment inputs.
-/

namespace StatInference
namespace Matching
namespace WDSM

universe u v w x y z

/--
Scenario-specific bridge from audited retrospective PATE known-score results to
estimated-score asymptotic normality and its variance formula.
-/
structure RetrospectivePATEEstimatedScoreAuditBridge where
  known_score_bridge : RetrospectivePATEKnownScoreVarianceBridge
  estimated_input : EstimatedScoreLocalExperimentVarianceInput
  estimated_score_asymptotic_normality : Prop
  estimated_score_variance_formula : Prop
  known_normality_to_estimated_input :
    known_score_bridge.asymptotic_bridge.asymptotic_normality ->
      estimated_input.known_score_asymptotic_normality
  known_variance_to_estimated_input :
    known_score_bridge.known_score_variance_formula ->
      estimated_input.known_score_variance_formula
  estimated_normality_to_retrospective_pate :
    estimated_input.estimated_score_asymptotic_normality ->
      estimated_score_asymptotic_normality
  estimated_variance_to_retrospective_pate :
    estimated_input.estimated_score_variance_formula ->
      estimated_score_variance_formula

/--
Retrospective PATE estimated-score asymptotic normality and variance formula
from audited known-score inputs plus explicit local-experiment and Godambe
assumptions.
-/
theorem retrospective_pate_estimated_score_normality_and_variance_of_audited_local_experiment
    (b : RetrospectivePATEEstimatedScoreAuditBridge)
    (hexact :
      b.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst : b.estimated_input.first_step_asymptotic_linearization)
    (hscore : b.estimated_input.score_estimator_local_asymptotic_linearity)
    (hfunctional : b.estimated_input.matching_functional_local_derivative)
    (hequicontinuity : b.estimated_input.local_stochastic_equicontinuity)
    (hadjustment : b.estimated_input.score_adjustment_algebra)
    (hgodambe : b.estimated_input.godambe_identity) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula := by
  have hknown_pair :=
    retrospective_pate_known_score_normality_and_variance_of_chen_han_audited_bridges
      b.known_score_bridge
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
  have hestimated_pair :=
    estimated_score_asymptotic_normality_and_variance_formula_of_local_experiment_variance_input
      b.estimated_input
      (b.known_normality_to_estimated_input hknown_pair.1)
      (b.known_variance_to_estimated_input hknown_pair.2)
      hfirst hscore hfunctional hequicontinuity hadjustment hgodambe
  exact
    ⟨b.estimated_normality_to_retrospective_pate hestimated_pair.1,
      b.estimated_variance_to_retrospective_pate hestimated_pair.2⟩

/--
Retrospective PATE estimated-score asymptotic normality and variance formula
from audited known-score inputs, with the WDSM-specific local derivative,
stochastic equicontinuity, and Godambe obligations packaged as one compact
core.
-/
theorem
    retrospective_pate_estimated_score_normality_and_variance_of_audited_local_experiment_core
    (b : RetrospectivePATEEstimatedScoreAuditBridge)
    (hexact :
      b.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst : b.estimated_input.first_step_asymptotic_linearization)
    (hscore : b.estimated_input.score_estimator_local_asymptotic_linearity)
    (hadjustment : b.estimated_input.score_adjustment_algebra)
    (core : EstimatedScoreLocalExperimentVarianceCore b.estimated_input) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula := by
  exact
    retrospective_pate_estimated_score_normality_and_variance_of_audited_local_experiment
      b hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality hfirst
      hscore core.matching_functional_local_derivative
      core.local_stochastic_equicontinuity hadjustment core.godambe_identity

/--
Retrospective PATE estimated-score asymptotic normality and variance formula
from audited known-score inputs plus first-step Z-estimator component
certificates.
-/
theorem retrospective_pate_estimated_score_normality_and_variance_of_audited_z_components
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {TSample : ℕ -> Type u} {TParameter : Type v} {TMoment : Type w}
    {TInfluenceFunction : Type x} {TLinearPart : Type y}
    {TRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b : RetrospectivePATEEstimatedScoreAuditBridge)
    (firstStep : PATEDoubleScoreFirstStepAssembly)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
    (treated :
      FirstStepScoreComponentZEvidence TSample TParameter TMoment
        TInfluenceFunction TLinearPart TRemainder)
    (control :
      FirstStepScoreComponentZEvidence CSample CParameter CMoment
        CInfluenceFunction CLinearPart CRemainder)
    (hexact :
      b.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        b.estimated_input.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        b.estimated_input.score_estimator_local_asymptotic_linearity)
    (h_prop_weight :
      propensity.component.weighting_design ->
        firstStep.propensity_weighting_design)
    (h_treated_weight :
      treated.component.weighting_design ->
        firstStep.treated_prognostic_weighting_design)
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_treated_component :
      treated.component.component_asymptotic_linearity ->
        firstStep.treated_prognostic_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity)
    (hfunctional : b.estimated_input.matching_functional_local_derivative)
    (hequicontinuity : b.estimated_input.local_stochastic_equicontinuity)
    (hadjustment : b.estimated_input.score_adjustment_algebra)
    (hgodambe : b.estimated_input.godambe_identity) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula := by
  have hknown_pair :=
    retrospective_pate_known_score_normality_and_variance_of_chen_han_audited_bridges
      b.known_score_bridge
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
  have hestimated_pair :=
    estimated_score_normality_and_variance_formula_of_pate_z_components
      firstStep b.estimated_input propensity treated control
      hfirst_transfer hscore_transfer
      (b.known_normality_to_estimated_input hknown_pair.1)
      (b.known_variance_to_estimated_input hknown_pair.2)
      h_prop_weight h_treated_weight h_control_weight h_prop_component
      h_treated_component h_control_component hfunctional hequicontinuity
      hadjustment hgodambe
  exact
    ⟨b.estimated_normality_to_retrospective_pate hestimated_pair.1,
      b.estimated_variance_to_retrospective_pate hestimated_pair.2⟩

/--
Retrospective PATE estimated-score asymptotic normality and variance formula
from audited known-score inputs plus first-step Z-estimator component
certificates, with the local derivative, stochastic equicontinuity, and
Godambe obligations packaged as one compact core.
-/
theorem
    retrospective_pate_estimated_score_normality_and_variance_of_audited_z_components_core
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {TSample : ℕ -> Type u} {TParameter : Type v} {TMoment : Type w}
    {TInfluenceFunction : Type x} {TLinearPart : Type y}
    {TRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b : RetrospectivePATEEstimatedScoreAuditBridge)
    (firstStep : PATEDoubleScoreFirstStepAssembly)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
    (treated :
      FirstStepScoreComponentZEvidence TSample TParameter TMoment
        TInfluenceFunction TLinearPart TRemainder)
    (control :
      FirstStepScoreComponentZEvidence CSample CParameter CMoment
        CInfluenceFunction CLinearPart CRemainder)
    (hexact :
      b.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        b.estimated_input.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        b.estimated_input.score_estimator_local_asymptotic_linearity)
    (h_prop_weight :
      propensity.component.weighting_design ->
        firstStep.propensity_weighting_design)
    (h_treated_weight :
      treated.component.weighting_design ->
        firstStep.treated_prognostic_weighting_design)
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_treated_component :
      treated.component.component_asymptotic_linearity ->
        firstStep.treated_prognostic_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity)
    (hadjustment : b.estimated_input.score_adjustment_algebra)
    (core : EstimatedScoreLocalExperimentVarianceCore b.estimated_input) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula := by
  exact
    retrospective_pate_estimated_score_normality_and_variance_of_audited_z_components
      b firstStep propensity treated control hexact hbias_bound
      hgeometry_regular hcatchment hheterogeneity_moment
      hheterogeneity_variance hresidual_reg hquad hradius_regular
      hradius_geometry hfinite hden horthogonality hfirst_transfer
      hscore_transfer h_prop_weight h_treated_weight h_control_weight
      h_prop_component h_treated_component h_control_component
      core.matching_functional_local_derivative
      core.local_stochastic_equicontinuity hadjustment core.godambe_identity

end WDSM
end Matching
end StatInference
