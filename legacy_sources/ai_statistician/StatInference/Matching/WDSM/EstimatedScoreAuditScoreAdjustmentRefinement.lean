import StatInference.Matching.WDSM.ProspectiveEstimatedScoreAudit
import StatInference.Matching.WDSM.RetrospectivePATEEstimatedScoreAudit
import StatInference.Matching.WDSM.RetrospectivePATTEstimatedScoreAudit
import StatInference.Matching.WDSM.RetrospectiveEstimatedScoreAuditPaired
import StatInference.Matching.WDSM.FirstStepZEstimatorScoreAdjustmentRefinement

/-!
# Audit-level estimated-score routes with concrete score-adjustment algebra

This module pushes the target-1321/1327 score-adjustment refinement up from the
first-step Z-estimator layer to audited WDSM estimated-score routes.  The
theorems here keep the prospective known-score audit inputs explicit, but no
longer require callers to pass the abstract `score_adjustment_algebra` premise
directly when a fixed-law or changing-law finite quadratic-form identity is the
intended source of that premise.
-/

namespace StatInference
namespace Matching
namespace WDSM

universe u v w x y z

/--
Prospective PATE audited estimated-score normality and variance from
Z-estimator components, with score-adjustment algebra supplied by the fixed-law
finite quadratic-form identity.
-/
theorem
    prospective_pate_estimated_score_normality_and_variance_of_audited_z_components_fixedLaw_score_adjustment_identity
    {Param : Type*}
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {TSample : ℕ -> Type u} {TParameter : Type v} {TMoment : Type w}
    {TInfluenceFunction : Type x} {TLinearPart : Type y}
    {TRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b : ProspectivePATEEstimatedScoreAuditBridge)
    (firstStep : PATEDoubleScoreFirstStepAssembly)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.estimated_input.score_adjustment_algebra)
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
    (hgodambe : b.estimated_input.godambe_identity) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula := by
  have hknown_pair :=
    prospective_pate_known_score_normality_and_variance_of_audited_bridges
      b.known_score_bridge hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality
  have hestimated_pair :=
    estimated_score_normality_and_variance_formula_of_pate_z_components_fixedLaw_score_adjustment_identity
      firstStep b.estimated_input parameters oracleVariance firstStepLoading
      scoreCovariance hinterpret propensity treated control hfirst_transfer
      hscore_transfer (b.known_normality_to_estimated_input hknown_pair.1)
      (b.known_variance_to_estimated_input hknown_pair.2) h_prop_weight
      h_treated_weight h_control_weight h_prop_component h_treated_component
      h_control_component hfunctional hequicontinuity hgodambe
  exact
    ⟨b.estimated_normality_to_prospective_pate hestimated_pair.1,
      b.estimated_variance_to_prospective_pate hestimated_pair.2⟩

/--
Prospective PATE audited estimated-score normality and variance from
Z-estimator components, with score-adjustment algebra supplied by the
changing-law finite quadratic-form identity.
-/
theorem
    prospective_pate_estimated_score_normality_and_variance_of_audited_z_components_changingLaw_score_adjustment_identity
    {Param : Type*}
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {TSample : ℕ -> Type u} {TParameter : Type v} {TMoment : Type w}
    {TInfluenceFunction : Type x} {TLinearPart : Type y}
    {TRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b : ProspectivePATEEstimatedScoreAuditBridge)
    (firstStep : PATEDoubleScoreFirstStepAssembly)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.estimated_input.score_adjustment_algebra)
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
    (hgodambe : b.estimated_input.godambe_identity) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula := by
  have hknown_pair :=
    prospective_pate_known_score_normality_and_variance_of_audited_bridges
      b.known_score_bridge hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality
  have hestimated_pair :=
    estimated_score_normality_and_variance_formula_of_pate_z_components_changingLaw_score_adjustment_identity
      firstStep b.estimated_input parameters oracleVariance firstStepLoading
      targetDriftLoading scoreCovariance hinterpret propensity treated control
      hfirst_transfer hscore_transfer
      (b.known_normality_to_estimated_input hknown_pair.1)
      (b.known_variance_to_estimated_input hknown_pair.2) h_prop_weight
      h_treated_weight h_control_weight h_prop_component h_treated_component
      h_control_component hfunctional hequicontinuity hgodambe
  exact
    ⟨b.estimated_normality_to_prospective_pate hestimated_pair.1,
      b.estimated_variance_to_prospective_pate hestimated_pair.2⟩

/--
Prospective PATT audited estimated-score normality and variance from
Z-estimator components, with score-adjustment algebra supplied by the fixed-law
finite quadratic-form identity.
-/
theorem
    prospective_patt_estimated_score_normality_and_variance_of_audited_z_components_fixedLaw_score_adjustment_identity
    {Param : Type*}
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b : ProspectivePATTEstimatedScoreAuditBridge)
    (firstStep : PATTDoubleScoreFirstStepAssembly)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.estimated_input.score_adjustment_algebra)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
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
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity)
    (hfunctional : b.estimated_input.matching_functional_local_derivative)
    (hequicontinuity : b.estimated_input.local_stochastic_equicontinuity)
    (hgodambe : b.estimated_input.godambe_identity) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula := by
  have hknown_pair :=
    prospective_patt_known_score_normality_and_variance_of_audited_bridges
      b.known_score_bridge hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality
  have hestimated_pair :=
    estimated_score_normality_and_variance_formula_of_patt_z_components_fixedLaw_score_adjustment_identity
      firstStep b.estimated_input parameters oracleVariance firstStepLoading
      scoreCovariance hinterpret propensity control hfirst_transfer
      hscore_transfer (b.known_normality_to_estimated_input hknown_pair.1)
      (b.known_variance_to_estimated_input hknown_pair.2) h_prop_weight
      h_control_weight h_prop_component h_control_component hfunctional
      hequicontinuity hgodambe
  exact
    ⟨b.estimated_normality_to_prospective_patt hestimated_pair.1,
      b.estimated_variance_to_prospective_patt hestimated_pair.2⟩

/--
Prospective PATT audited estimated-score normality and variance from
Z-estimator components, with score-adjustment algebra supplied by the
changing-law finite quadratic-form identity.
-/
theorem
    prospective_patt_estimated_score_normality_and_variance_of_audited_z_components_changingLaw_score_adjustment_identity
    {Param : Type*}
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b : ProspectivePATTEstimatedScoreAuditBridge)
    (firstStep : PATTDoubleScoreFirstStepAssembly)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.estimated_input.score_adjustment_algebra)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
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
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity)
    (hfunctional : b.estimated_input.matching_functional_local_derivative)
    (hequicontinuity : b.estimated_input.local_stochastic_equicontinuity)
    (hgodambe : b.estimated_input.godambe_identity) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula := by
  have hknown_pair :=
    prospective_patt_known_score_normality_and_variance_of_audited_bridges
      b.known_score_bridge hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality
  have hestimated_pair :=
    estimated_score_normality_and_variance_formula_of_patt_z_components_changingLaw_score_adjustment_identity
      firstStep b.estimated_input parameters oracleVariance firstStepLoading
      targetDriftLoading scoreCovariance hinterpret propensity control
      hfirst_transfer hscore_transfer
      (b.known_normality_to_estimated_input hknown_pair.1)
      (b.known_variance_to_estimated_input hknown_pair.2) h_prop_weight
      h_control_weight h_prop_component h_control_component hfunctional
      hequicontinuity hgodambe
  exact
    ⟨b.estimated_normality_to_prospective_patt hestimated_pair.1,
      b.estimated_variance_to_prospective_patt hestimated_pair.2⟩

/--
Prospective PATE audited estimated-score normality and variance from
Z-estimator components, with finite fixed-law score-adjustment algebra and a
compact local-experiment/Godambe core.
-/
theorem
    prospective_pate_estimated_score_normality_and_variance_of_audited_z_components_fixedLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {TSample : ℕ -> Type u} {TParameter : Type v} {TMoment : Type w}
    {TInfluenceFunction : Type x} {TLinearPart : Type y}
    {TRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b : ProspectivePATEEstimatedScoreAuditBridge)
    (firstStep : PATEDoubleScoreFirstStepAssembly)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.estimated_input.score_adjustment_algebra)
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
    (core : EstimatedScoreLocalExperimentVarianceCore b.estimated_input) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula := by
  exact
    prospective_pate_estimated_score_normality_and_variance_of_audited_z_components_fixedLaw_score_adjustment_identity
      b firstStep parameters oracleVariance firstStepLoading scoreCovariance
      hinterpret propensity treated control hexact hbias_bound
      hgeometry_regular hcatchment hheterogeneity_moment
      hheterogeneity_variance hresidual_reg hquad hradius_regular
      hradius_geometry hfinite hden horthogonality hfirst_transfer
      hscore_transfer h_prop_weight h_treated_weight h_control_weight
      h_prop_component h_treated_component h_control_component
      core.matching_functional_local_derivative
      core.local_stochastic_equicontinuity core.godambe_identity

/--
Prospective PATE audited estimated-score normality and variance from
Z-estimator components, with finite changing-law score-adjustment algebra and a
compact local-experiment/Godambe core.
-/
theorem
    prospective_pate_estimated_score_normality_and_variance_of_audited_z_components_changingLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {TSample : ℕ -> Type u} {TParameter : Type v} {TMoment : Type w}
    {TInfluenceFunction : Type x} {TLinearPart : Type y}
    {TRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b : ProspectivePATEEstimatedScoreAuditBridge)
    (firstStep : PATEDoubleScoreFirstStepAssembly)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.estimated_input.score_adjustment_algebra)
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
    (core : EstimatedScoreLocalExperimentVarianceCore b.estimated_input) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula := by
  exact
    prospective_pate_estimated_score_normality_and_variance_of_audited_z_components_changingLaw_score_adjustment_identity
      b firstStep parameters oracleVariance firstStepLoading
      targetDriftLoading scoreCovariance hinterpret propensity treated control
      hexact hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
      hheterogeneity_variance hresidual_reg hquad hradius_regular
      hradius_geometry hfinite hden horthogonality hfirst_transfer
      hscore_transfer h_prop_weight h_treated_weight h_control_weight
      h_prop_component h_treated_component h_control_component
      core.matching_functional_local_derivative
      core.local_stochastic_equicontinuity core.godambe_identity

/--
Prospective PATT audited estimated-score normality and variance from
Z-estimator components, with finite fixed-law score-adjustment algebra and a
compact local-experiment/Godambe core.
-/
theorem
    prospective_patt_estimated_score_normality_and_variance_of_audited_z_components_fixedLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b : ProspectivePATTEstimatedScoreAuditBridge)
    (firstStep : PATTDoubleScoreFirstStepAssembly)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.estimated_input.score_adjustment_algebra)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
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
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity)
    (core : EstimatedScoreLocalExperimentVarianceCore b.estimated_input) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula := by
  exact
    prospective_patt_estimated_score_normality_and_variance_of_audited_z_components_fixedLaw_score_adjustment_identity
      b firstStep parameters oracleVariance firstStepLoading scoreCovariance
      hinterpret propensity control hexact hbias_bound hgeometry_regular
      hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
      hquad hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst_transfer hscore_transfer h_prop_weight h_control_weight
      h_prop_component h_control_component
      core.matching_functional_local_derivative
      core.local_stochastic_equicontinuity core.godambe_identity

/--
Prospective PATT audited estimated-score normality and variance from
Z-estimator components, with finite changing-law score-adjustment algebra and a
compact local-experiment/Godambe core.
-/
theorem
    prospective_patt_estimated_score_normality_and_variance_of_audited_z_components_changingLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b : ProspectivePATTEstimatedScoreAuditBridge)
    (firstStep : PATTDoubleScoreFirstStepAssembly)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.estimated_input.score_adjustment_algebra)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
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
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity)
    (core : EstimatedScoreLocalExperimentVarianceCore b.estimated_input) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula := by
  exact
    prospective_patt_estimated_score_normality_and_variance_of_audited_z_components_changingLaw_score_adjustment_identity
      b firstStep parameters oracleVariance firstStepLoading
      targetDriftLoading scoreCovariance hinterpret propensity control hexact
      hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
      hheterogeneity_variance hresidual_reg hquad hradius_regular
      hradius_geometry hfinite hden horthogonality hfirst_transfer
      hscore_transfer h_prop_weight h_control_weight h_prop_component
      h_control_component core.matching_functional_local_derivative
      core.local_stochastic_equicontinuity core.godambe_identity

/--
Retrospective PATE audited estimated-score normality and variance from
Z-estimator components, with score-adjustment algebra supplied by the fixed-law
finite quadratic-form identity.
-/
theorem
    retrospective_pate_estimated_score_normality_and_variance_of_audited_z_components_fixedLaw_score_adjustment_identity
    {Param : Type*}
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
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.estimated_input.score_adjustment_algebra)
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
    (hgodambe : b.estimated_input.godambe_identity) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula := by
  have hknown_pair :=
    retrospective_pate_known_score_normality_and_variance_of_chen_han_audited_bridges
      b.known_score_bridge hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality
  have hestimated_pair :=
    estimated_score_normality_and_variance_formula_of_pate_z_components_fixedLaw_score_adjustment_identity
      firstStep b.estimated_input parameters oracleVariance firstStepLoading
      scoreCovariance hinterpret propensity treated control hfirst_transfer
      hscore_transfer (b.known_normality_to_estimated_input hknown_pair.1)
      (b.known_variance_to_estimated_input hknown_pair.2) h_prop_weight
      h_treated_weight h_control_weight h_prop_component h_treated_component
      h_control_component hfunctional hequicontinuity hgodambe
  exact
    ⟨b.estimated_normality_to_retrospective_pate hestimated_pair.1,
      b.estimated_variance_to_retrospective_pate hestimated_pair.2⟩

/--
Retrospective PATE audited estimated-score normality and variance from
Z-estimator components, with score-adjustment algebra supplied by the
changing-law finite quadratic-form identity.
-/
theorem
    retrospective_pate_estimated_score_normality_and_variance_of_audited_z_components_changingLaw_score_adjustment_identity
    {Param : Type*}
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
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.estimated_input.score_adjustment_algebra)
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
    (hgodambe : b.estimated_input.godambe_identity) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula := by
  have hknown_pair :=
    retrospective_pate_known_score_normality_and_variance_of_chen_han_audited_bridges
      b.known_score_bridge hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality
  have hestimated_pair :=
    estimated_score_normality_and_variance_formula_of_pate_z_components_changingLaw_score_adjustment_identity
      firstStep b.estimated_input parameters oracleVariance firstStepLoading
      targetDriftLoading scoreCovariance hinterpret propensity treated control
      hfirst_transfer hscore_transfer
      (b.known_normality_to_estimated_input hknown_pair.1)
      (b.known_variance_to_estimated_input hknown_pair.2) h_prop_weight
      h_treated_weight h_control_weight h_prop_component h_treated_component
      h_control_component hfunctional hequicontinuity hgodambe
  exact
    ⟨b.estimated_normality_to_retrospective_pate hestimated_pair.1,
      b.estimated_variance_to_retrospective_pate hestimated_pair.2⟩

/--
Retrospective PATT audited estimated-score normality and variance from
Z-estimator components, with score-adjustment algebra supplied by the fixed-law
finite quadratic-form identity.
-/
theorem
    retrospective_patt_estimated_score_normality_and_variance_of_audited_z_components_fixedLaw_score_adjustment_identity
    {Param : Type*}
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b : RetrospectivePATTEstimatedScoreAuditBridge)
    (firstStep : PATTDoubleScoreFirstStepAssembly)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.estimated_input.score_adjustment_algebra)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
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
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity)
    (hfunctional : b.estimated_input.matching_functional_local_derivative)
    (hequicontinuity : b.estimated_input.local_stochastic_equicontinuity)
    (hgodambe : b.estimated_input.godambe_identity) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula := by
  have hknown_pair :=
    retrospective_patt_known_score_normality_and_variance_of_audited_bridges
      b.known_score_bridge hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality
  have hestimated_pair :=
    estimated_score_normality_and_variance_formula_of_patt_z_components_fixedLaw_score_adjustment_identity
      firstStep b.estimated_input parameters oracleVariance firstStepLoading
      scoreCovariance hinterpret propensity control hfirst_transfer
      hscore_transfer (b.known_normality_to_estimated_input hknown_pair.1)
      (b.known_variance_to_estimated_input hknown_pair.2) h_prop_weight
      h_control_weight h_prop_component h_control_component hfunctional
      hequicontinuity hgodambe
  exact
    ⟨b.estimated_normality_to_retrospective_patt hestimated_pair.1,
      b.estimated_variance_to_retrospective_patt hestimated_pair.2⟩

/--
Retrospective PATT audited estimated-score normality and variance from
Z-estimator components, with score-adjustment algebra supplied by the
changing-law finite quadratic-form identity.
-/
theorem
    retrospective_patt_estimated_score_normality_and_variance_of_audited_z_components_changingLaw_score_adjustment_identity
    {Param : Type*}
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b : RetrospectivePATTEstimatedScoreAuditBridge)
    (firstStep : PATTDoubleScoreFirstStepAssembly)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.estimated_input.score_adjustment_algebra)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
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
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity)
    (hfunctional : b.estimated_input.matching_functional_local_derivative)
    (hequicontinuity : b.estimated_input.local_stochastic_equicontinuity)
    (hgodambe : b.estimated_input.godambe_identity) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula := by
  have hknown_pair :=
    retrospective_patt_known_score_normality_and_variance_of_audited_bridges
      b.known_score_bridge hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality
  have hestimated_pair :=
    estimated_score_normality_and_variance_formula_of_patt_z_components_changingLaw_score_adjustment_identity
      firstStep b.estimated_input parameters oracleVariance firstStepLoading
      targetDriftLoading scoreCovariance hinterpret propensity control
      hfirst_transfer hscore_transfer
      (b.known_normality_to_estimated_input hknown_pair.1)
      (b.known_variance_to_estimated_input hknown_pair.2) h_prop_weight
      h_control_weight h_prop_component h_control_component hfunctional
      hequicontinuity hgodambe
  exact
    ⟨b.estimated_normality_to_retrospective_patt hestimated_pair.1,
      b.estimated_variance_to_retrospective_patt hestimated_pair.2⟩

/--
Retrospective PATE audited estimated-score normality and variance from
Z-estimator components, with finite fixed-law score-adjustment algebra and a
compact local-experiment/Godambe core.
-/
theorem
    retrospective_pate_estimated_score_normality_and_variance_of_audited_z_components_fixedLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
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
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.estimated_input.score_adjustment_algebra)
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
    (core : EstimatedScoreLocalExperimentVarianceCore b.estimated_input) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula := by
  exact
    retrospective_pate_estimated_score_normality_and_variance_of_audited_z_components_fixedLaw_score_adjustment_identity
      b firstStep parameters oracleVariance firstStepLoading scoreCovariance
      hinterpret propensity treated control hexact hbias_bound
      hgeometry_regular hcatchment hheterogeneity_moment
      hheterogeneity_variance hresidual_reg hquad hradius_regular
      hradius_geometry hfinite hden horthogonality hfirst_transfer
      hscore_transfer h_prop_weight h_treated_weight h_control_weight
      h_prop_component h_treated_component h_control_component
      core.matching_functional_local_derivative
      core.local_stochastic_equicontinuity core.godambe_identity

/--
Retrospective PATE audited estimated-score normality and variance from
Z-estimator components, with finite changing-law score-adjustment algebra and a
compact local-experiment/Godambe core.
-/
theorem
    retrospective_pate_estimated_score_normality_and_variance_of_audited_z_components_changingLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
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
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.estimated_input.score_adjustment_algebra)
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
    (core : EstimatedScoreLocalExperimentVarianceCore b.estimated_input) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula := by
  exact
    retrospective_pate_estimated_score_normality_and_variance_of_audited_z_components_changingLaw_score_adjustment_identity
      b firstStep parameters oracleVariance firstStepLoading
      targetDriftLoading scoreCovariance hinterpret propensity treated control
      hexact hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
      hheterogeneity_variance hresidual_reg hquad hradius_regular
      hradius_geometry hfinite hden horthogonality hfirst_transfer
      hscore_transfer h_prop_weight h_treated_weight h_control_weight
      h_prop_component h_treated_component h_control_component
      core.matching_functional_local_derivative
      core.local_stochastic_equicontinuity core.godambe_identity

/--
Retrospective PATT audited estimated-score normality and variance from
Z-estimator components, with finite fixed-law score-adjustment algebra and a
compact local-experiment/Godambe core.
-/
theorem
    retrospective_patt_estimated_score_normality_and_variance_of_audited_z_components_fixedLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b : RetrospectivePATTEstimatedScoreAuditBridge)
    (firstStep : PATTDoubleScoreFirstStepAssembly)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.estimated_input.score_adjustment_algebra)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
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
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity)
    (core : EstimatedScoreLocalExperimentVarianceCore b.estimated_input) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula := by
  exact
    retrospective_patt_estimated_score_normality_and_variance_of_audited_z_components_fixedLaw_score_adjustment_identity
      b firstStep parameters oracleVariance firstStepLoading scoreCovariance
      hinterpret propensity control hexact hbias_bound hgeometry_regular
      hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
      hquad hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst_transfer hscore_transfer h_prop_weight h_control_weight
      h_prop_component h_control_component
      core.matching_functional_local_derivative
      core.local_stochastic_equicontinuity core.godambe_identity

/--
Retrospective PATT audited estimated-score normality and variance from
Z-estimator components, with finite changing-law score-adjustment algebra and a
compact local-experiment/Godambe core.
-/
theorem
    retrospective_patt_estimated_score_normality_and_variance_of_audited_z_components_changingLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b : RetrospectivePATTEstimatedScoreAuditBridge)
    (firstStep : PATTDoubleScoreFirstStepAssembly)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.estimated_input.score_adjustment_algebra)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
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
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity)
    (core : EstimatedScoreLocalExperimentVarianceCore b.estimated_input) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula := by
  exact
    retrospective_patt_estimated_score_normality_and_variance_of_audited_z_components_changingLaw_score_adjustment_identity
      b firstStep parameters oracleVariance firstStepLoading
      targetDriftLoading scoreCovariance hinterpret propensity control hexact
      hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
      hheterogeneity_variance hresidual_reg hquad hradius_regular
      hradius_geometry hfinite hden horthogonality hfirst_transfer
      hscore_transfer h_prop_weight h_control_weight h_prop_component
      h_control_component core.matching_functional_local_derivative
      core.local_stochastic_equicontinuity core.godambe_identity

/--
Paired prospective PATE/PATT audit-level estimated-score normality and variance
from component Z-estimator certificates, with both score-adjustment premises
supplied by fixed-law finite quadratic-form identities.
-/
theorem
    prospective_pate_patt_estimated_score_normality_and_variance_of_audited_z_components_fixedLaw_score_adjustment_identities
    {PATEParam PATTParam : Type*}
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
    (pate : ProspectivePATEEstimatedScoreAuditBridge)
    (patt : ProspectivePATTEstimatedScoreAuditBridge)
    (pateFirstStep : PATEDoubleScoreFirstStepAssembly)
    (pattFirstStep : PATTDoubleScoreFirstStepAssembly)
    (pateParameters : Finset PATEParam) (pateOracleVariance : Real)
    (pateFirstStepLoading : PATEParam -> Real)
    (pateScoreCovariance : PATEParam -> PATEParam -> Real)
    (hpate_interpret :
      fixedLawScoreAdjustedVariance pateParameters pateOracleVariance
          pateFirstStepLoading pateScoreCovariance =
        pateOracleVariance -
          scoreQuadraticForm pateParameters pateFirstStepLoading
            pateScoreCovariance ->
        pate.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattScoreCovariance =
        pattOracleVariance -
          scoreQuadraticForm pattParameters pattFirstStepLoading
            pattScoreCovariance ->
        patt.estimated_input.score_adjustment_algebra)
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
    (hpattGodambe : patt.estimated_input.godambe_identity) :
    (pate.estimated_score_asymptotic_normality ∧
        pate.estimated_score_variance_formula) ∧
      (patt.estimated_score_asymptotic_normality ∧
        patt.estimated_score_variance_formula) := by
  exact
    prospective_pate_patt_estimated_score_normality_and_variance_of_audited_z_components
      pate patt pateFirstStep pattFirstStep patePropensity pateTreated
      pateControl pattPropensity pattControl hpateExact hpateBiasBound
      hpateGeometryRegular hpateCatchment hpateHeterogeneityMoment
      hpateHeterogeneityVariance hpateResidualReg hpateQuad
      hpateRadiusRegular hpateRadiusGeometry hpateFinite hpateDen
      hpateOrthogonality hpate_first_transfer hpate_score_transfer
      hpate_prop_weight hpate_treated_weight hpate_control_weight
      hpate_prop_component hpate_treated_component hpate_control_component
      hpateFunctional hpateEquicontinuity
      (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
        pate.estimated_input.score_adjustment_algebra pateParameters
        pateOracleVariance pateFirstStepLoading pateScoreCovariance
        hpate_interpret)
      hpateGodambe hpattExact hpattBiasBound hpattGeometryRegular
      hpattCatchment hpattHeterogeneityMoment hpattHeterogeneityVariance
      hpattResidualReg hpattQuad hpattRadiusRegular hpattRadiusGeometry
      hpattFinite hpattDen hpattOrthogonality hpatt_first_transfer
      hpatt_score_transfer hpatt_prop_weight hpatt_control_weight
      hpatt_prop_component hpatt_control_component hpattFunctional
      hpattEquicontinuity
      (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
        patt.estimated_input.score_adjustment_algebra pattParameters
        pattOracleVariance pattFirstStepLoading pattScoreCovariance
        hpatt_interpret)
      hpattGodambe

/--
Paired prospective PATE/PATT audit-level estimated-score normality and variance
from component Z-estimator certificates, fixed-law score-adjustment identities,
and one compact local-experiment/Godambe core per estimand.
-/
theorem
    prospective_pate_patt_estimated_score_normality_and_variance_of_audited_z_components_fixedLaw_score_adjustment_identities_and_local_experiment_cores
    {PATEParam PATTParam : Type*}
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
    (pate : ProspectivePATEEstimatedScoreAuditBridge)
    (patt : ProspectivePATTEstimatedScoreAuditBridge)
    (pateFirstStep : PATEDoubleScoreFirstStepAssembly)
    (pattFirstStep : PATTDoubleScoreFirstStepAssembly)
    (pateParameters : Finset PATEParam) (pateOracleVariance : Real)
    (pateFirstStepLoading : PATEParam -> Real)
    (pateScoreCovariance : PATEParam -> PATEParam -> Real)
    (hpate_interpret :
      fixedLawScoreAdjustedVariance pateParameters pateOracleVariance
          pateFirstStepLoading pateScoreCovariance =
        pateOracleVariance -
          scoreQuadraticForm pateParameters pateFirstStepLoading
            pateScoreCovariance ->
        pate.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattScoreCovariance =
        pattOracleVariance -
          scoreQuadraticForm pattParameters pattFirstStepLoading
            pattScoreCovariance ->
        patt.estimated_input.score_adjustment_algebra)
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
    (hpateCore : EstimatedScoreLocalExperimentVarianceCore pate.estimated_input)
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
    (hpattCore : EstimatedScoreLocalExperimentVarianceCore patt.estimated_input) :
    (pate.estimated_score_asymptotic_normality ∧
        pate.estimated_score_variance_formula) ∧
      (patt.estimated_score_asymptotic_normality ∧
        patt.estimated_score_variance_formula) := by
  exact
    ⟨prospective_pate_estimated_score_normality_and_variance_of_audited_z_components_fixedLaw_score_adjustment_identity_and_local_experiment_core
        pate pateFirstStep pateParameters pateOracleVariance
        pateFirstStepLoading pateScoreCovariance hpate_interpret
        patePropensity pateTreated pateControl hpateExact hpateBiasBound
        hpateGeometryRegular hpateCatchment hpateHeterogeneityMoment
        hpateHeterogeneityVariance hpateResidualReg hpateQuad
        hpateRadiusRegular hpateRadiusGeometry hpateFinite hpateDen
        hpateOrthogonality hpate_first_transfer hpate_score_transfer
        hpate_prop_weight hpate_treated_weight hpate_control_weight
        hpate_prop_component hpate_treated_component hpate_control_component
        hpateCore,
      prospective_patt_estimated_score_normality_and_variance_of_audited_z_components_fixedLaw_score_adjustment_identity_and_local_experiment_core
        patt pattFirstStep pattParameters pattOracleVariance
        pattFirstStepLoading pattScoreCovariance hpatt_interpret
        pattPropensity pattControl hpattExact hpattBiasBound
        hpattGeometryRegular hpattCatchment hpattHeterogeneityMoment
        hpattHeterogeneityVariance hpattResidualReg hpattQuad
        hpattRadiusRegular hpattRadiusGeometry hpattFinite hpattDen
        hpattOrthogonality hpatt_first_transfer hpatt_score_transfer
        hpatt_prop_weight hpatt_control_weight hpatt_prop_component
        hpatt_control_component hpattCore⟩

/--
Paired prospective PATE/PATT audit-level estimated-score normality and variance
from component Z-estimator certificates, with both score-adjustment premises
supplied by changing-law finite quadratic-form identities.
-/
theorem
    prospective_pate_patt_estimated_score_normality_and_variance_of_audited_z_components_changingLaw_score_adjustment_identities
    {PATEParam PATTParam : Type*}
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
    (pate : ProspectivePATEEstimatedScoreAuditBridge)
    (patt : ProspectivePATTEstimatedScoreAuditBridge)
    (pateFirstStep : PATEDoubleScoreFirstStepAssembly)
    (pattFirstStep : PATTDoubleScoreFirstStepAssembly)
    (pateParameters : Finset PATEParam) (pateOracleVariance : Real)
    (pateFirstStepLoading pateTargetDriftLoading : PATEParam -> Real)
    (pateScoreCovariance : PATEParam -> PATEParam -> Real)
    (hpate_interpret :
      changingLawScoreAdjustedVariance pateParameters pateOracleVariance
          pateFirstStepLoading pateTargetDriftLoading pateScoreCovariance =
        fixedLawScoreAdjustedVariance pateParameters pateOracleVariance
            pateFirstStepLoading pateScoreCovariance +
          scoreQuadraticForm pateParameters pateTargetDriftLoading
            pateScoreCovariance ->
        pate.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading pattTargetDriftLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      changingLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattTargetDriftLoading pattScoreCovariance =
        fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
            pattFirstStepLoading pattScoreCovariance +
          scoreQuadraticForm pattParameters pattTargetDriftLoading
            pattScoreCovariance ->
        patt.estimated_input.score_adjustment_algebra)
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
    (hpattGodambe : patt.estimated_input.godambe_identity) :
    (pate.estimated_score_asymptotic_normality ∧
        pate.estimated_score_variance_formula) ∧
      (patt.estimated_score_asymptotic_normality ∧
        patt.estimated_score_variance_formula) := by
  exact
    prospective_pate_patt_estimated_score_normality_and_variance_of_audited_z_components
      pate patt pateFirstStep pattFirstStep patePropensity pateTreated
      pateControl pattPropensity pattControl hpateExact hpateBiasBound
      hpateGeometryRegular hpateCatchment hpateHeterogeneityMoment
      hpateHeterogeneityVariance hpateResidualReg hpateQuad
      hpateRadiusRegular hpateRadiusGeometry hpateFinite hpateDen
      hpateOrthogonality hpate_first_transfer hpate_score_transfer
      hpate_prop_weight hpate_treated_weight hpate_control_weight
      hpate_prop_component hpate_treated_component hpate_control_component
      hpateFunctional hpateEquicontinuity
      (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
        pate.estimated_input.score_adjustment_algebra pateParameters
        pateOracleVariance pateFirstStepLoading pateTargetDriftLoading
        pateScoreCovariance hpate_interpret)
      hpateGodambe hpattExact hpattBiasBound hpattGeometryRegular
      hpattCatchment hpattHeterogeneityMoment hpattHeterogeneityVariance
      hpattResidualReg hpattQuad hpattRadiusRegular hpattRadiusGeometry
      hpattFinite hpattDen hpattOrthogonality hpatt_first_transfer
      hpatt_score_transfer hpatt_prop_weight hpatt_control_weight
      hpatt_prop_component hpatt_control_component hpattFunctional
      hpattEquicontinuity
      (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
        patt.estimated_input.score_adjustment_algebra pattParameters
        pattOracleVariance pattFirstStepLoading pattTargetDriftLoading
        pattScoreCovariance hpatt_interpret)
      hpattGodambe

/--
Paired prospective PATE/PATT audit-level estimated-score normality and variance
from component Z-estimator certificates, changing-law score-adjustment
identities, and one compact local-experiment/Godambe core per estimand.
-/
theorem
    prospective_pate_patt_estimated_score_normality_and_variance_of_audited_z_components_changingLaw_score_adjustment_identities_and_local_experiment_cores
    {PATEParam PATTParam : Type*}
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
    (pate : ProspectivePATEEstimatedScoreAuditBridge)
    (patt : ProspectivePATTEstimatedScoreAuditBridge)
    (pateFirstStep : PATEDoubleScoreFirstStepAssembly)
    (pattFirstStep : PATTDoubleScoreFirstStepAssembly)
    (pateParameters : Finset PATEParam) (pateOracleVariance : Real)
    (pateFirstStepLoading pateTargetDriftLoading : PATEParam -> Real)
    (pateScoreCovariance : PATEParam -> PATEParam -> Real)
    (hpate_interpret :
      changingLawScoreAdjustedVariance pateParameters pateOracleVariance
          pateFirstStepLoading pateTargetDriftLoading pateScoreCovariance =
        fixedLawScoreAdjustedVariance pateParameters pateOracleVariance
            pateFirstStepLoading pateScoreCovariance +
          scoreQuadraticForm pateParameters pateTargetDriftLoading
            pateScoreCovariance ->
        pate.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading pattTargetDriftLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      changingLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattTargetDriftLoading pattScoreCovariance =
        fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
            pattFirstStepLoading pattScoreCovariance +
          scoreQuadraticForm pattParameters pattTargetDriftLoading
            pattScoreCovariance ->
        patt.estimated_input.score_adjustment_algebra)
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
    (hpateCore : EstimatedScoreLocalExperimentVarianceCore pate.estimated_input)
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
    (hpattCore : EstimatedScoreLocalExperimentVarianceCore patt.estimated_input) :
    (pate.estimated_score_asymptotic_normality ∧
        pate.estimated_score_variance_formula) ∧
      (patt.estimated_score_asymptotic_normality ∧
        patt.estimated_score_variance_formula) := by
  exact
    ⟨prospective_pate_estimated_score_normality_and_variance_of_audited_z_components_changingLaw_score_adjustment_identity_and_local_experiment_core
        pate pateFirstStep pateParameters pateOracleVariance
        pateFirstStepLoading pateTargetDriftLoading pateScoreCovariance
        hpate_interpret patePropensity pateTreated pateControl hpateExact
        hpateBiasBound hpateGeometryRegular hpateCatchment
        hpateHeterogeneityMoment hpateHeterogeneityVariance hpateResidualReg
        hpateQuad hpateRadiusRegular hpateRadiusGeometry hpateFinite hpateDen
        hpateOrthogonality hpate_first_transfer hpate_score_transfer
        hpate_prop_weight hpate_treated_weight hpate_control_weight
        hpate_prop_component hpate_treated_component hpate_control_component
        hpateCore,
      prospective_patt_estimated_score_normality_and_variance_of_audited_z_components_changingLaw_score_adjustment_identity_and_local_experiment_core
        patt pattFirstStep pattParameters pattOracleVariance
        pattFirstStepLoading pattTargetDriftLoading pattScoreCovariance
        hpatt_interpret pattPropensity pattControl hpattExact hpattBiasBound
        hpattGeometryRegular hpattCatchment hpattHeterogeneityMoment
        hpattHeterogeneityVariance hpattResidualReg hpattQuad
        hpattRadiusRegular hpattRadiusGeometry hpattFinite hpattDen
        hpattOrthogonality hpatt_first_transfer hpatt_score_transfer
        hpatt_prop_weight hpatt_control_weight hpatt_prop_component
        hpatt_control_component hpattCore⟩

/--
Paired retrospective PATE/PATT audit-level estimated-score normality and
variance from component Z-estimator certificates, with both score-adjustment
premises supplied by fixed-law finite quadratic-form identities.
-/
theorem
    retrospective_pate_patt_estimated_score_normality_and_variance_of_audited_z_components_fixedLaw_score_adjustment_identities
    {PATEParam PATTParam : Type*}
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
    (pateParameters : Finset PATEParam) (pateOracleVariance : Real)
    (pateFirstStepLoading : PATEParam -> Real)
    (pateScoreCovariance : PATEParam -> PATEParam -> Real)
    (hpate_interpret :
      fixedLawScoreAdjustedVariance pateParameters pateOracleVariance
          pateFirstStepLoading pateScoreCovariance =
        pateOracleVariance -
          scoreQuadraticForm pateParameters pateFirstStepLoading
            pateScoreCovariance ->
        pate.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattScoreCovariance =
        pattOracleVariance -
          scoreQuadraticForm pattParameters pattFirstStepLoading
            pattScoreCovariance ->
        patt.estimated_input.score_adjustment_algebra)
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
    (hpattGodambe : patt.estimated_input.godambe_identity) :
    (pate.estimated_score_asymptotic_normality ∧
        pate.estimated_score_variance_formula) ∧
      (patt.estimated_score_asymptotic_normality ∧
        patt.estimated_score_variance_formula) := by
  exact
    ⟨retrospective_pate_estimated_score_normality_and_variance_of_audited_z_components_fixedLaw_score_adjustment_identity
        pate pateFirstStep pateParameters pateOracleVariance
        pateFirstStepLoading pateScoreCovariance hpate_interpret
        patePropensity pateTreated pateControl hpateExact hpateBiasBound
        hpateGeometryRegular hpateCatchment hpateHeterogeneityMoment
        hpateHeterogeneityVariance hpateResidualReg hpateQuad
        hpateRadiusRegular hpateRadiusGeometry hpateFinite hpateDen
        hpateOrthogonality hpate_first_transfer hpate_score_transfer
        hpate_prop_weight hpate_treated_weight hpate_control_weight
        hpate_prop_component hpate_treated_component hpate_control_component
        hpateFunctional hpateEquicontinuity hpateGodambe,
      retrospective_patt_estimated_score_normality_and_variance_of_audited_z_components_fixedLaw_score_adjustment_identity
        patt pattFirstStep pattParameters pattOracleVariance
        pattFirstStepLoading pattScoreCovariance hpatt_interpret
        pattPropensity pattControl hpattExact hpattBiasBound
        hpattGeometryRegular hpattCatchment hpattHeterogeneityMoment
        hpattHeterogeneityVariance hpattResidualReg hpattQuad
        hpattRadiusRegular hpattRadiusGeometry hpattFinite hpattDen
        hpattOrthogonality hpatt_first_transfer hpatt_score_transfer
        hpatt_prop_weight hpatt_control_weight hpatt_prop_component
        hpatt_control_component hpattFunctional hpattEquicontinuity
        hpattGodambe⟩

/--
Paired retrospective PATE/PATT audit-level estimated-score normality and
variance from component Z-estimator certificates, fixed-law score-adjustment
identities, and one compact local-experiment/Godambe core per estimand.
-/
theorem
    retrospective_pate_patt_estimated_score_normality_and_variance_of_audited_z_components_fixedLaw_score_adjustment_identities_and_local_experiment_cores
    {PATEParam PATTParam : Type*}
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
    (pateParameters : Finset PATEParam) (pateOracleVariance : Real)
    (pateFirstStepLoading : PATEParam -> Real)
    (pateScoreCovariance : PATEParam -> PATEParam -> Real)
    (hpate_interpret :
      fixedLawScoreAdjustedVariance pateParameters pateOracleVariance
          pateFirstStepLoading pateScoreCovariance =
        pateOracleVariance -
          scoreQuadraticForm pateParameters pateFirstStepLoading
            pateScoreCovariance ->
        pate.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattScoreCovariance =
        pattOracleVariance -
          scoreQuadraticForm pattParameters pattFirstStepLoading
            pattScoreCovariance ->
        patt.estimated_input.score_adjustment_algebra)
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
    (hpateCore : EstimatedScoreLocalExperimentVarianceCore pate.estimated_input)
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
    (hpattCore : EstimatedScoreLocalExperimentVarianceCore patt.estimated_input) :
    (pate.estimated_score_asymptotic_normality ∧
        pate.estimated_score_variance_formula) ∧
      (patt.estimated_score_asymptotic_normality ∧
        patt.estimated_score_variance_formula) := by
  exact
    ⟨retrospective_pate_estimated_score_normality_and_variance_of_audited_z_components_fixedLaw_score_adjustment_identity_and_local_experiment_core
        pate pateFirstStep pateParameters pateOracleVariance
        pateFirstStepLoading pateScoreCovariance hpate_interpret
        patePropensity pateTreated pateControl hpateExact hpateBiasBound
        hpateGeometryRegular hpateCatchment hpateHeterogeneityMoment
        hpateHeterogeneityVariance hpateResidualReg hpateQuad
        hpateRadiusRegular hpateRadiusGeometry hpateFinite hpateDen
        hpateOrthogonality hpate_first_transfer hpate_score_transfer
        hpate_prop_weight hpate_treated_weight hpate_control_weight
        hpate_prop_component hpate_treated_component hpate_control_component
        hpateCore,
      retrospective_patt_estimated_score_normality_and_variance_of_audited_z_components_fixedLaw_score_adjustment_identity_and_local_experiment_core
        patt pattFirstStep pattParameters pattOracleVariance
        pattFirstStepLoading pattScoreCovariance hpatt_interpret
        pattPropensity pattControl hpattExact hpattBiasBound
        hpattGeometryRegular hpattCatchment hpattHeterogeneityMoment
        hpattHeterogeneityVariance hpattResidualReg hpattQuad
        hpattRadiusRegular hpattRadiusGeometry hpattFinite hpattDen
        hpattOrthogonality hpatt_first_transfer hpatt_score_transfer
        hpatt_prop_weight hpatt_control_weight hpatt_prop_component
        hpatt_control_component hpattCore⟩

/--
Paired retrospective PATE/PATT audit-level estimated-score normality and
variance from component Z-estimator certificates, with both score-adjustment
premises supplied by changing-law finite quadratic-form identities.
-/
theorem
    retrospective_pate_patt_estimated_score_normality_and_variance_of_audited_z_components_changingLaw_score_adjustment_identities
    {PATEParam PATTParam : Type*}
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
    (pateParameters : Finset PATEParam) (pateOracleVariance : Real)
    (pateFirstStepLoading pateTargetDriftLoading : PATEParam -> Real)
    (pateScoreCovariance : PATEParam -> PATEParam -> Real)
    (hpate_interpret :
      changingLawScoreAdjustedVariance pateParameters pateOracleVariance
          pateFirstStepLoading pateTargetDriftLoading pateScoreCovariance =
        fixedLawScoreAdjustedVariance pateParameters pateOracleVariance
            pateFirstStepLoading pateScoreCovariance +
          scoreQuadraticForm pateParameters pateTargetDriftLoading
            pateScoreCovariance ->
        pate.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading pattTargetDriftLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      changingLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattTargetDriftLoading pattScoreCovariance =
        fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
            pattFirstStepLoading pattScoreCovariance +
          scoreQuadraticForm pattParameters pattTargetDriftLoading
            pattScoreCovariance ->
        patt.estimated_input.score_adjustment_algebra)
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
    (hpattGodambe : patt.estimated_input.godambe_identity) :
    (pate.estimated_score_asymptotic_normality ∧
        pate.estimated_score_variance_formula) ∧
      (patt.estimated_score_asymptotic_normality ∧
        patt.estimated_score_variance_formula) := by
  exact
    ⟨retrospective_pate_estimated_score_normality_and_variance_of_audited_z_components_changingLaw_score_adjustment_identity
        pate pateFirstStep pateParameters pateOracleVariance
        pateFirstStepLoading pateTargetDriftLoading pateScoreCovariance
        hpate_interpret patePropensity pateTreated pateControl hpateExact
        hpateBiasBound hpateGeometryRegular hpateCatchment
        hpateHeterogeneityMoment hpateHeterogeneityVariance hpateResidualReg
        hpateQuad hpateRadiusRegular hpateRadiusGeometry hpateFinite hpateDen
        hpateOrthogonality hpate_first_transfer hpate_score_transfer
        hpate_prop_weight hpate_treated_weight hpate_control_weight
        hpate_prop_component hpate_treated_component hpate_control_component
        hpateFunctional hpateEquicontinuity hpateGodambe,
      retrospective_patt_estimated_score_normality_and_variance_of_audited_z_components_changingLaw_score_adjustment_identity
        patt pattFirstStep pattParameters pattOracleVariance
        pattFirstStepLoading pattTargetDriftLoading pattScoreCovariance
        hpatt_interpret pattPropensity pattControl hpattExact hpattBiasBound
        hpattGeometryRegular hpattCatchment hpattHeterogeneityMoment
        hpattHeterogeneityVariance hpattResidualReg hpattQuad
        hpattRadiusRegular hpattRadiusGeometry hpattFinite hpattDen
        hpattOrthogonality hpatt_first_transfer hpatt_score_transfer
        hpatt_prop_weight hpatt_control_weight hpatt_prop_component
        hpatt_control_component hpattFunctional hpattEquicontinuity
        hpattGodambe⟩

/--
Paired retrospective PATE/PATT audit-level estimated-score normality and
variance from component Z-estimator certificates, changing-law score-adjustment
identities, and one compact local-experiment/Godambe core per estimand.
-/
theorem
    retrospective_pate_patt_estimated_score_normality_and_variance_of_audited_z_components_changingLaw_score_adjustment_identities_and_local_experiment_cores
    {PATEParam PATTParam : Type*}
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
    (pateParameters : Finset PATEParam) (pateOracleVariance : Real)
    (pateFirstStepLoading pateTargetDriftLoading : PATEParam -> Real)
    (pateScoreCovariance : PATEParam -> PATEParam -> Real)
    (hpate_interpret :
      changingLawScoreAdjustedVariance pateParameters pateOracleVariance
          pateFirstStepLoading pateTargetDriftLoading pateScoreCovariance =
        fixedLawScoreAdjustedVariance pateParameters pateOracleVariance
            pateFirstStepLoading pateScoreCovariance +
          scoreQuadraticForm pateParameters pateTargetDriftLoading
            pateScoreCovariance ->
        pate.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading pattTargetDriftLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      changingLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattTargetDriftLoading pattScoreCovariance =
        fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
            pattFirstStepLoading pattScoreCovariance +
          scoreQuadraticForm pattParameters pattTargetDriftLoading
            pattScoreCovariance ->
        patt.estimated_input.score_adjustment_algebra)
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
    (hpateCore : EstimatedScoreLocalExperimentVarianceCore pate.estimated_input)
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
    (hpattCore : EstimatedScoreLocalExperimentVarianceCore patt.estimated_input) :
    (pate.estimated_score_asymptotic_normality ∧
        pate.estimated_score_variance_formula) ∧
      (patt.estimated_score_asymptotic_normality ∧
        patt.estimated_score_variance_formula) := by
  exact
    ⟨retrospective_pate_estimated_score_normality_and_variance_of_audited_z_components_changingLaw_score_adjustment_identity_and_local_experiment_core
        pate pateFirstStep pateParameters pateOracleVariance
        pateFirstStepLoading pateTargetDriftLoading pateScoreCovariance
        hpate_interpret patePropensity pateTreated pateControl hpateExact
        hpateBiasBound hpateGeometryRegular hpateCatchment
        hpateHeterogeneityMoment hpateHeterogeneityVariance hpateResidualReg
        hpateQuad hpateRadiusRegular hpateRadiusGeometry hpateFinite hpateDen
        hpateOrthogonality hpate_first_transfer hpate_score_transfer
        hpate_prop_weight hpate_treated_weight hpate_control_weight
        hpate_prop_component hpate_treated_component hpate_control_component
        hpateCore,
      retrospective_patt_estimated_score_normality_and_variance_of_audited_z_components_changingLaw_score_adjustment_identity_and_local_experiment_core
        patt pattFirstStep pattParameters pattOracleVariance
        pattFirstStepLoading pattTargetDriftLoading pattScoreCovariance
        hpatt_interpret pattPropensity pattControl hpattExact hpattBiasBound
        hpattGeometryRegular hpattCatchment hpattHeterogeneityMoment
        hpattHeterogeneityVariance hpattResidualReg hpattQuad
        hpattRadiusRegular hpattRadiusGeometry hpattFinite hpattDen
        hpattOrthogonality hpatt_first_transfer hpatt_score_transfer
        hpatt_prop_weight hpatt_control_weight hpatt_prop_component
        hpatt_control_component hpattCore⟩

/--
Prospective PATE audited local-experiment route, with score-adjustment algebra
supplied by the fixed-law finite quadratic-form identity.
-/
theorem
    prospective_pate_estimated_score_normality_and_variance_of_audited_local_experiment_fixedLaw_score_adjustment_identity
    {Param : Type*}
    (b : ProspectivePATEEstimatedScoreAuditBridge)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.estimated_input.score_adjustment_algebra)
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
    (hgodambe : b.estimated_input.godambe_identity) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula :=
  prospective_pate_estimated_score_normality_and_variance_of_audited_local_experiment
    b hexact hbias_bound hgeometry_regular hcatchment
    hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
    hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore hfunctional hequicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      b.estimated_input.score_adjustment_algebra parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret)
    hgodambe

/--
Prospective PATE audited local-experiment route, with score-adjustment algebra
supplied by the changing-law finite quadratic-form identity.
-/
theorem
    prospective_pate_estimated_score_normality_and_variance_of_audited_local_experiment_changingLaw_score_adjustment_identity
    {Param : Type*}
    (b : ProspectivePATEEstimatedScoreAuditBridge)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.estimated_input.score_adjustment_algebra)
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
    (hgodambe : b.estimated_input.godambe_identity) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula :=
  prospective_pate_estimated_score_normality_and_variance_of_audited_local_experiment
    b hexact hbias_bound hgeometry_regular hcatchment
    hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
    hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore hfunctional hequicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      b.estimated_input.score_adjustment_algebra parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret)
    hgodambe

/--
Prospective PATT audited local-experiment route, with score-adjustment algebra
supplied by the fixed-law finite quadratic-form identity.
-/
theorem
    prospective_patt_estimated_score_normality_and_variance_of_audited_local_experiment_fixedLaw_score_adjustment_identity
    {Param : Type*}
    (b : ProspectivePATTEstimatedScoreAuditBridge)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.estimated_input.score_adjustment_algebra)
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
    (hgodambe : b.estimated_input.godambe_identity) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula :=
  prospective_patt_estimated_score_normality_and_variance_of_audited_local_experiment
    b hexact hbias_bound hgeometry_regular hcatchment
    hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
    hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore hfunctional hequicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      b.estimated_input.score_adjustment_algebra parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret)
    hgodambe

/--
Prospective PATT audited local-experiment route, with score-adjustment algebra
supplied by the changing-law finite quadratic-form identity.
-/
theorem
    prospective_patt_estimated_score_normality_and_variance_of_audited_local_experiment_changingLaw_score_adjustment_identity
    {Param : Type*}
    (b : ProspectivePATTEstimatedScoreAuditBridge)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.estimated_input.score_adjustment_algebra)
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
    (hgodambe : b.estimated_input.godambe_identity) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula :=
  prospective_patt_estimated_score_normality_and_variance_of_audited_local_experiment
    b hexact hbias_bound hgeometry_regular hcatchment
    hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
    hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore hfunctional hequicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      b.estimated_input.score_adjustment_algebra parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret)
    hgodambe

/--
Prospective PATE audited local-experiment route, with finite fixed-law
score-adjustment algebra and a compact local-experiment/Godambe core.
-/
theorem
    prospective_pate_estimated_score_normality_and_variance_of_audited_local_experiment_fixedLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    (b : ProspectivePATEEstimatedScoreAuditBridge)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.estimated_input.score_adjustment_algebra)
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
    (core : EstimatedScoreLocalExperimentVarianceCore b.estimated_input) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula := by
  exact
    prospective_pate_estimated_score_normality_and_variance_of_audited_local_experiment_fixedLaw_score_adjustment_identity
      b parameters oracleVariance firstStepLoading scoreCovariance hinterpret
      hexact hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
      hheterogeneity_variance hresidual_reg hquad hradius_regular
      hradius_geometry hfinite hden horthogonality hfirst hscore
      core.matching_functional_local_derivative
      core.local_stochastic_equicontinuity core.godambe_identity

/--
Prospective PATE audited local-experiment route, with finite changing-law
score-adjustment algebra and a compact local-experiment/Godambe core.
-/
theorem
    prospective_pate_estimated_score_normality_and_variance_of_audited_local_experiment_changingLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    (b : ProspectivePATEEstimatedScoreAuditBridge)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.estimated_input.score_adjustment_algebra)
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
    (core : EstimatedScoreLocalExperimentVarianceCore b.estimated_input) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula := by
  exact
    prospective_pate_estimated_score_normality_and_variance_of_audited_local_experiment_changingLaw_score_adjustment_identity
      b parameters oracleVariance firstStepLoading targetDriftLoading
      scoreCovariance hinterpret hexact hbias_bound hgeometry_regular
      hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
      hquad hradius_regular hradius_geometry hfinite hden horthogonality hfirst
      hscore core.matching_functional_local_derivative
      core.local_stochastic_equicontinuity core.godambe_identity

/--
Prospective PATT audited local-experiment route, with finite fixed-law
score-adjustment algebra and a compact local-experiment/Godambe core.
-/
theorem
    prospective_patt_estimated_score_normality_and_variance_of_audited_local_experiment_fixedLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    (b : ProspectivePATTEstimatedScoreAuditBridge)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.estimated_input.score_adjustment_algebra)
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
    (core : EstimatedScoreLocalExperimentVarianceCore b.estimated_input) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula := by
  exact
    prospective_patt_estimated_score_normality_and_variance_of_audited_local_experiment_fixedLaw_score_adjustment_identity
      b parameters oracleVariance firstStepLoading scoreCovariance hinterpret
      hexact hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
      hheterogeneity_variance hresidual_reg hquad hradius_regular
      hradius_geometry hfinite hden horthogonality hfirst hscore
      core.matching_functional_local_derivative
      core.local_stochastic_equicontinuity core.godambe_identity

/--
Prospective PATT audited local-experiment route, with finite changing-law
score-adjustment algebra and a compact local-experiment/Godambe core.
-/
theorem
    prospective_patt_estimated_score_normality_and_variance_of_audited_local_experiment_changingLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    (b : ProspectivePATTEstimatedScoreAuditBridge)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.estimated_input.score_adjustment_algebra)
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
    (core : EstimatedScoreLocalExperimentVarianceCore b.estimated_input) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula := by
  exact
    prospective_patt_estimated_score_normality_and_variance_of_audited_local_experiment_changingLaw_score_adjustment_identity
      b parameters oracleVariance firstStepLoading targetDriftLoading
      scoreCovariance hinterpret hexact hbias_bound hgeometry_regular
      hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
      hquad hradius_regular hradius_geometry hfinite hden horthogonality hfirst
      hscore core.matching_functional_local_derivative
      core.local_stochastic_equicontinuity core.godambe_identity

/--
Retrospective PATE audited local-experiment route, with score-adjustment
algebra supplied by the fixed-law finite quadratic-form identity.
-/
theorem
    retrospective_pate_estimated_score_normality_and_variance_of_audited_local_experiment_fixedLaw_score_adjustment_identity
    {Param : Type*}
    (b : RetrospectivePATEEstimatedScoreAuditBridge)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.estimated_input.score_adjustment_algebra)
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
    (hgodambe : b.estimated_input.godambe_identity) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula :=
  retrospective_pate_estimated_score_normality_and_variance_of_audited_local_experiment
    b hexact hbias_bound hgeometry_regular hcatchment
    hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
    hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore hfunctional hequicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      b.estimated_input.score_adjustment_algebra parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret)
    hgodambe

/--
Retrospective PATE audited local-experiment route, with score-adjustment
algebra supplied by the changing-law finite quadratic-form identity.
-/
theorem
    retrospective_pate_estimated_score_normality_and_variance_of_audited_local_experiment_changingLaw_score_adjustment_identity
    {Param : Type*}
    (b : RetrospectivePATEEstimatedScoreAuditBridge)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.estimated_input.score_adjustment_algebra)
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
    (hgodambe : b.estimated_input.godambe_identity) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula :=
  retrospective_pate_estimated_score_normality_and_variance_of_audited_local_experiment
    b hexact hbias_bound hgeometry_regular hcatchment
    hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
    hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore hfunctional hequicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      b.estimated_input.score_adjustment_algebra parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret)
    hgodambe

/--
Retrospective PATT audited local-experiment route, with score-adjustment
algebra supplied by the fixed-law finite quadratic-form identity.
-/
theorem
    retrospective_patt_estimated_score_normality_and_variance_of_audited_local_experiment_fixedLaw_score_adjustment_identity
    {Param : Type*}
    (b : RetrospectivePATTEstimatedScoreAuditBridge)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.estimated_input.score_adjustment_algebra)
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
    (hgodambe : b.estimated_input.godambe_identity) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula :=
  retrospective_patt_estimated_score_normality_and_variance_of_audited_local_experiment
    b hexact hbias_bound hgeometry_regular hcatchment
    hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
    hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore hfunctional hequicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      b.estimated_input.score_adjustment_algebra parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret)
    hgodambe

/--
Retrospective PATT audited local-experiment route, with score-adjustment
algebra supplied by the changing-law finite quadratic-form identity.
-/
theorem
    retrospective_patt_estimated_score_normality_and_variance_of_audited_local_experiment_changingLaw_score_adjustment_identity
    {Param : Type*}
    (b : RetrospectivePATTEstimatedScoreAuditBridge)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.estimated_input.score_adjustment_algebra)
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
    (hgodambe : b.estimated_input.godambe_identity) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula :=
  retrospective_patt_estimated_score_normality_and_variance_of_audited_local_experiment
    b hexact hbias_bound hgeometry_regular hcatchment
    hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
    hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore hfunctional hequicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      b.estimated_input.score_adjustment_algebra parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret)
    hgodambe

/--
Retrospective PATE audited local-experiment route, with finite fixed-law
score-adjustment algebra and a compact local-experiment/Godambe core.
-/
theorem
    retrospective_pate_estimated_score_normality_and_variance_of_audited_local_experiment_fixedLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    (b : RetrospectivePATEEstimatedScoreAuditBridge)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.estimated_input.score_adjustment_algebra)
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
    (core : EstimatedScoreLocalExperimentVarianceCore b.estimated_input) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula := by
  exact
    retrospective_pate_estimated_score_normality_and_variance_of_audited_local_experiment_fixedLaw_score_adjustment_identity
      b parameters oracleVariance firstStepLoading scoreCovariance hinterpret
      hexact hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
      hheterogeneity_variance hresidual_reg hquad hradius_regular
      hradius_geometry hfinite hden horthogonality hfirst hscore
      core.matching_functional_local_derivative
      core.local_stochastic_equicontinuity core.godambe_identity

/--
Retrospective PATE audited local-experiment route, with finite changing-law
score-adjustment algebra and a compact local-experiment/Godambe core.
-/
theorem
    retrospective_pate_estimated_score_normality_and_variance_of_audited_local_experiment_changingLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    (b : RetrospectivePATEEstimatedScoreAuditBridge)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.estimated_input.score_adjustment_algebra)
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
    (core : EstimatedScoreLocalExperimentVarianceCore b.estimated_input) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula := by
  exact
    retrospective_pate_estimated_score_normality_and_variance_of_audited_local_experiment_changingLaw_score_adjustment_identity
      b parameters oracleVariance firstStepLoading targetDriftLoading
      scoreCovariance hinterpret hexact hbias_bound hgeometry_regular
      hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
      hquad hradius_regular hradius_geometry hfinite hden horthogonality hfirst
      hscore core.matching_functional_local_derivative
      core.local_stochastic_equicontinuity core.godambe_identity

/--
Retrospective PATT audited local-experiment route, with finite fixed-law
score-adjustment algebra and a compact local-experiment/Godambe core.
-/
theorem
    retrospective_patt_estimated_score_normality_and_variance_of_audited_local_experiment_fixedLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    (b : RetrospectivePATTEstimatedScoreAuditBridge)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.estimated_input.score_adjustment_algebra)
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
    (core : EstimatedScoreLocalExperimentVarianceCore b.estimated_input) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula := by
  exact
    retrospective_patt_estimated_score_normality_and_variance_of_audited_local_experiment_fixedLaw_score_adjustment_identity
      b parameters oracleVariance firstStepLoading scoreCovariance hinterpret
      hexact hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
      hheterogeneity_variance hresidual_reg hquad hradius_regular
      hradius_geometry hfinite hden horthogonality hfirst hscore
      core.matching_functional_local_derivative
      core.local_stochastic_equicontinuity core.godambe_identity

/--
Retrospective PATT audited local-experiment route, with finite changing-law
score-adjustment algebra and a compact local-experiment/Godambe core.
-/
theorem
    retrospective_patt_estimated_score_normality_and_variance_of_audited_local_experiment_changingLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    (b : RetrospectivePATTEstimatedScoreAuditBridge)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.estimated_input.score_adjustment_algebra)
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
    (core : EstimatedScoreLocalExperimentVarianceCore b.estimated_input) :
    b.estimated_score_asymptotic_normality ∧
      b.estimated_score_variance_formula := by
  exact
    retrospective_patt_estimated_score_normality_and_variance_of_audited_local_experiment_changingLaw_score_adjustment_identity
      b parameters oracleVariance firstStepLoading targetDriftLoading
      scoreCovariance hinterpret hexact hbias_bound hgeometry_regular
      hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
      hquad hradius_regular hradius_geometry hfinite hden horthogonality hfirst
      hscore core.matching_functional_local_derivative
      core.local_stochastic_equicontinuity core.godambe_identity

/--
Paired prospective PATE/PATT audited local-experiment routes, with both
score-adjustment premises supplied by fixed-law finite quadratic-form
identities.
-/
theorem
    prospective_pate_patt_estimated_score_normality_and_variance_of_audited_local_experiment_fixedLaw_score_adjustment_identities
    {PATEParam PATTParam : Type*}
    (pate : ProspectivePATEEstimatedScoreAuditBridge)
    (patt : ProspectivePATTEstimatedScoreAuditBridge)
    (pateParameters : Finset PATEParam) (pateOracleVariance : Real)
    (pateFirstStepLoading : PATEParam -> Real)
    (pateScoreCovariance : PATEParam -> PATEParam -> Real)
    (hpate_interpret :
      fixedLawScoreAdjustedVariance pateParameters pateOracleVariance
          pateFirstStepLoading pateScoreCovariance =
        pateOracleVariance -
          scoreQuadraticForm pateParameters pateFirstStepLoading
            pateScoreCovariance ->
        pate.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattScoreCovariance =
        pattOracleVariance -
          scoreQuadraticForm pattParameters pattFirstStepLoading
            pattScoreCovariance ->
        patt.estimated_input.score_adjustment_algebra)
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
    (hpattGodambe : patt.estimated_input.godambe_identity) :
    (pate.estimated_score_asymptotic_normality ∧
        pate.estimated_score_variance_formula) ∧
      (patt.estimated_score_asymptotic_normality ∧
        patt.estimated_score_variance_formula) :=
  ⟨prospective_pate_estimated_score_normality_and_variance_of_audited_local_experiment_fixedLaw_score_adjustment_identity
      pate pateParameters pateOracleVariance pateFirstStepLoading
      pateScoreCovariance hpate_interpret hpateExact hpateBiasBound
      hpateGeometryRegular hpateCatchment hpateHeterogeneityMoment
      hpateHeterogeneityVariance hpateResidualReg hpateQuad
      hpateRadiusRegular hpateRadiusGeometry hpateFinite hpateDen
      hpateOrthogonality hpateFirst hpateScore hpateFunctional
      hpateEquicontinuity hpateGodambe,
    prospective_patt_estimated_score_normality_and_variance_of_audited_local_experiment_fixedLaw_score_adjustment_identity
      patt pattParameters pattOracleVariance pattFirstStepLoading
      pattScoreCovariance hpatt_interpret hpattExact hpattBiasBound
      hpattGeometryRegular hpattCatchment hpattHeterogeneityMoment
      hpattHeterogeneityVariance hpattResidualReg hpattQuad
      hpattRadiusRegular hpattRadiusGeometry hpattFinite hpattDen
      hpattOrthogonality hpattFirst hpattScore hpattFunctional
      hpattEquicontinuity hpattGodambe⟩

/--
Paired prospective PATE/PATT audited local-experiment routes, with both
score-adjustment premises supplied by changing-law finite quadratic-form
identities.
-/
theorem
    prospective_pate_patt_estimated_score_normality_and_variance_of_audited_local_experiment_changingLaw_score_adjustment_identities
    {PATEParam PATTParam : Type*}
    (pate : ProspectivePATEEstimatedScoreAuditBridge)
    (patt : ProspectivePATTEstimatedScoreAuditBridge)
    (pateParameters : Finset PATEParam) (pateOracleVariance : Real)
    (pateFirstStepLoading pateTargetDriftLoading : PATEParam -> Real)
    (pateScoreCovariance : PATEParam -> PATEParam -> Real)
    (hpate_interpret :
      changingLawScoreAdjustedVariance pateParameters pateOracleVariance
          pateFirstStepLoading pateTargetDriftLoading pateScoreCovariance =
        fixedLawScoreAdjustedVariance pateParameters pateOracleVariance
            pateFirstStepLoading pateScoreCovariance +
          scoreQuadraticForm pateParameters pateTargetDriftLoading
            pateScoreCovariance ->
        pate.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading pattTargetDriftLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      changingLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattTargetDriftLoading pattScoreCovariance =
        fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
            pattFirstStepLoading pattScoreCovariance +
          scoreQuadraticForm pattParameters pattTargetDriftLoading
            pattScoreCovariance ->
        patt.estimated_input.score_adjustment_algebra)
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
    (hpattGodambe : patt.estimated_input.godambe_identity) :
    (pate.estimated_score_asymptotic_normality ∧
        pate.estimated_score_variance_formula) ∧
      (patt.estimated_score_asymptotic_normality ∧
        patt.estimated_score_variance_formula) :=
  ⟨prospective_pate_estimated_score_normality_and_variance_of_audited_local_experiment_changingLaw_score_adjustment_identity
      pate pateParameters pateOracleVariance pateFirstStepLoading
      pateTargetDriftLoading pateScoreCovariance hpate_interpret hpateExact
      hpateBiasBound hpateGeometryRegular hpateCatchment
      hpateHeterogeneityMoment hpateHeterogeneityVariance hpateResidualReg
      hpateQuad hpateRadiusRegular hpateRadiusGeometry hpateFinite hpateDen
      hpateOrthogonality hpateFirst hpateScore hpateFunctional
      hpateEquicontinuity hpateGodambe,
    prospective_patt_estimated_score_normality_and_variance_of_audited_local_experiment_changingLaw_score_adjustment_identity
      patt pattParameters pattOracleVariance pattFirstStepLoading
      pattTargetDriftLoading pattScoreCovariance hpatt_interpret hpattExact
      hpattBiasBound hpattGeometryRegular hpattCatchment
      hpattHeterogeneityMoment hpattHeterogeneityVariance hpattResidualReg
      hpattQuad hpattRadiusRegular hpattRadiusGeometry hpattFinite hpattDen
      hpattOrthogonality hpattFirst hpattScore hpattFunctional
      hpattEquicontinuity hpattGodambe⟩

/--
Paired prospective PATE/PATT audited local-experiment routes, with fixed-law
score-adjustment identities and one compact local-experiment/Godambe core per
estimand.
-/
theorem
    prospective_pate_patt_estimated_score_normality_and_variance_of_audited_local_experiment_fixedLaw_score_adjustment_identities_and_local_experiment_cores
    {PATEParam PATTParam : Type*}
    (pate : ProspectivePATEEstimatedScoreAuditBridge)
    (patt : ProspectivePATTEstimatedScoreAuditBridge)
    (pateParameters : Finset PATEParam) (pateOracleVariance : Real)
    (pateFirstStepLoading : PATEParam -> Real)
    (pateScoreCovariance : PATEParam -> PATEParam -> Real)
    (hpate_interpret :
      fixedLawScoreAdjustedVariance pateParameters pateOracleVariance
          pateFirstStepLoading pateScoreCovariance =
        pateOracleVariance -
          scoreQuadraticForm pateParameters pateFirstStepLoading
            pateScoreCovariance ->
        pate.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattScoreCovariance =
        pattOracleVariance -
          scoreQuadraticForm pattParameters pattFirstStepLoading
            pattScoreCovariance ->
        patt.estimated_input.score_adjustment_algebra)
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
    (pateCore : EstimatedScoreLocalExperimentVarianceCore pate.estimated_input)
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
    (pattCore : EstimatedScoreLocalExperimentVarianceCore patt.estimated_input) :
    (pate.estimated_score_asymptotic_normality ∧
        pate.estimated_score_variance_formula) ∧
      (patt.estimated_score_asymptotic_normality ∧
        patt.estimated_score_variance_formula) :=
  ⟨prospective_pate_estimated_score_normality_and_variance_of_audited_local_experiment_fixedLaw_score_adjustment_identity_and_local_experiment_core
      pate pateParameters pateOracleVariance pateFirstStepLoading
      pateScoreCovariance hpate_interpret hpateExact hpateBiasBound
      hpateGeometryRegular hpateCatchment hpateHeterogeneityMoment
      hpateHeterogeneityVariance hpateResidualReg hpateQuad
      hpateRadiusRegular hpateRadiusGeometry hpateFinite hpateDen
      hpateOrthogonality hpateFirst hpateScore pateCore,
    prospective_patt_estimated_score_normality_and_variance_of_audited_local_experiment_fixedLaw_score_adjustment_identity_and_local_experiment_core
      patt pattParameters pattOracleVariance pattFirstStepLoading
      pattScoreCovariance hpatt_interpret hpattExact hpattBiasBound
      hpattGeometryRegular hpattCatchment hpattHeterogeneityMoment
      hpattHeterogeneityVariance hpattResidualReg hpattQuad
      hpattRadiusRegular hpattRadiusGeometry hpattFinite hpattDen
      hpattOrthogonality hpattFirst hpattScore pattCore⟩

/--
Paired prospective PATE/PATT audited local-experiment routes, with changing-law
score-adjustment identities and one compact local-experiment/Godambe core per
estimand.
-/
theorem
    prospective_pate_patt_estimated_score_normality_and_variance_of_audited_local_experiment_changingLaw_score_adjustment_identities_and_local_experiment_cores
    {PATEParam PATTParam : Type*}
    (pate : ProspectivePATEEstimatedScoreAuditBridge)
    (patt : ProspectivePATTEstimatedScoreAuditBridge)
    (pateParameters : Finset PATEParam) (pateOracleVariance : Real)
    (pateFirstStepLoading pateTargetDriftLoading : PATEParam -> Real)
    (pateScoreCovariance : PATEParam -> PATEParam -> Real)
    (hpate_interpret :
      changingLawScoreAdjustedVariance pateParameters pateOracleVariance
          pateFirstStepLoading pateTargetDriftLoading pateScoreCovariance =
        fixedLawScoreAdjustedVariance pateParameters pateOracleVariance
            pateFirstStepLoading pateScoreCovariance +
          scoreQuadraticForm pateParameters pateTargetDriftLoading
            pateScoreCovariance ->
        pate.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading pattTargetDriftLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      changingLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattTargetDriftLoading pattScoreCovariance =
        fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
            pattFirstStepLoading pattScoreCovariance +
          scoreQuadraticForm pattParameters pattTargetDriftLoading
            pattScoreCovariance ->
        patt.estimated_input.score_adjustment_algebra)
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
    (pateCore : EstimatedScoreLocalExperimentVarianceCore pate.estimated_input)
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
    (pattCore : EstimatedScoreLocalExperimentVarianceCore patt.estimated_input) :
    (pate.estimated_score_asymptotic_normality ∧
        pate.estimated_score_variance_formula) ∧
      (patt.estimated_score_asymptotic_normality ∧
        patt.estimated_score_variance_formula) :=
  ⟨prospective_pate_estimated_score_normality_and_variance_of_audited_local_experiment_changingLaw_score_adjustment_identity_and_local_experiment_core
      pate pateParameters pateOracleVariance pateFirstStepLoading
      pateTargetDriftLoading pateScoreCovariance hpate_interpret hpateExact
      hpateBiasBound hpateGeometryRegular hpateCatchment
      hpateHeterogeneityMoment hpateHeterogeneityVariance hpateResidualReg
      hpateQuad hpateRadiusRegular hpateRadiusGeometry hpateFinite hpateDen
      hpateOrthogonality hpateFirst hpateScore pateCore,
    prospective_patt_estimated_score_normality_and_variance_of_audited_local_experiment_changingLaw_score_adjustment_identity_and_local_experiment_core
      patt pattParameters pattOracleVariance pattFirstStepLoading
      pattTargetDriftLoading pattScoreCovariance hpatt_interpret hpattExact
      hpattBiasBound hpattGeometryRegular hpattCatchment
      hpattHeterogeneityMoment hpattHeterogeneityVariance hpattResidualReg
      hpattQuad hpattRadiusRegular hpattRadiusGeometry hpattFinite hpattDen
      hpattOrthogonality hpattFirst hpattScore pattCore⟩

/--
Paired retrospective PATE/PATT audited local-experiment routes, with both
score-adjustment premises supplied by fixed-law finite quadratic-form
identities.
-/
theorem
    retrospective_pate_patt_estimated_score_normality_and_variance_of_audited_local_experiment_fixedLaw_score_adjustment_identities
    {PATEParam PATTParam : Type*}
    (pate : RetrospectivePATEEstimatedScoreAuditBridge)
    (patt : RetrospectivePATTEstimatedScoreAuditBridge)
    (pateParameters : Finset PATEParam) (pateOracleVariance : Real)
    (pateFirstStepLoading : PATEParam -> Real)
    (pateScoreCovariance : PATEParam -> PATEParam -> Real)
    (hpate_interpret :
      fixedLawScoreAdjustedVariance pateParameters pateOracleVariance
          pateFirstStepLoading pateScoreCovariance =
        pateOracleVariance -
          scoreQuadraticForm pateParameters pateFirstStepLoading
            pateScoreCovariance ->
        pate.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattScoreCovariance =
        pattOracleVariance -
          scoreQuadraticForm pattParameters pattFirstStepLoading
            pattScoreCovariance ->
        patt.estimated_input.score_adjustment_algebra)
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
    (hpattGodambe : patt.estimated_input.godambe_identity) :
    (pate.estimated_score_asymptotic_normality ∧
        pate.estimated_score_variance_formula) ∧
      (patt.estimated_score_asymptotic_normality ∧
        patt.estimated_score_variance_formula) :=
  ⟨retrospective_pate_estimated_score_normality_and_variance_of_audited_local_experiment_fixedLaw_score_adjustment_identity
      pate pateParameters pateOracleVariance pateFirstStepLoading
      pateScoreCovariance hpate_interpret hpateExact hpateBiasBound
      hpateGeometryRegular hpateCatchment hpateHeterogeneityMoment
      hpateHeterogeneityVariance hpateResidualReg hpateQuad
      hpateRadiusRegular hpateRadiusGeometry hpateFinite hpateDen
      hpateOrthogonality hpateFirst hpateScore hpateFunctional
      hpateEquicontinuity hpateGodambe,
    retrospective_patt_estimated_score_normality_and_variance_of_audited_local_experiment_fixedLaw_score_adjustment_identity
      patt pattParameters pattOracleVariance pattFirstStepLoading
      pattScoreCovariance hpatt_interpret hpattExact hpattBiasBound
      hpattGeometryRegular hpattCatchment hpattHeterogeneityMoment
      hpattHeterogeneityVariance hpattResidualReg hpattQuad
      hpattRadiusRegular hpattRadiusGeometry hpattFinite hpattDen
      hpattOrthogonality hpattFirst hpattScore hpattFunctional
      hpattEquicontinuity hpattGodambe⟩

/--
Paired retrospective PATE/PATT audited local-experiment routes, with both
score-adjustment premises supplied by changing-law finite quadratic-form
identities.
-/
theorem
    retrospective_pate_patt_estimated_score_normality_and_variance_of_audited_local_experiment_changingLaw_score_adjustment_identities
    {PATEParam PATTParam : Type*}
    (pate : RetrospectivePATEEstimatedScoreAuditBridge)
    (patt : RetrospectivePATTEstimatedScoreAuditBridge)
    (pateParameters : Finset PATEParam) (pateOracleVariance : Real)
    (pateFirstStepLoading pateTargetDriftLoading : PATEParam -> Real)
    (pateScoreCovariance : PATEParam -> PATEParam -> Real)
    (hpate_interpret :
      changingLawScoreAdjustedVariance pateParameters pateOracleVariance
          pateFirstStepLoading pateTargetDriftLoading pateScoreCovariance =
        fixedLawScoreAdjustedVariance pateParameters pateOracleVariance
            pateFirstStepLoading pateScoreCovariance +
          scoreQuadraticForm pateParameters pateTargetDriftLoading
            pateScoreCovariance ->
        pate.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading pattTargetDriftLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      changingLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattTargetDriftLoading pattScoreCovariance =
        fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
            pattFirstStepLoading pattScoreCovariance +
          scoreQuadraticForm pattParameters pattTargetDriftLoading
            pattScoreCovariance ->
        patt.estimated_input.score_adjustment_algebra)
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
    (hpattGodambe : patt.estimated_input.godambe_identity) :
    (pate.estimated_score_asymptotic_normality ∧
        pate.estimated_score_variance_formula) ∧
      (patt.estimated_score_asymptotic_normality ∧
        patt.estimated_score_variance_formula) :=
  ⟨retrospective_pate_estimated_score_normality_and_variance_of_audited_local_experiment_changingLaw_score_adjustment_identity
      pate pateParameters pateOracleVariance pateFirstStepLoading
      pateTargetDriftLoading pateScoreCovariance hpate_interpret hpateExact
      hpateBiasBound hpateGeometryRegular hpateCatchment
      hpateHeterogeneityMoment hpateHeterogeneityVariance hpateResidualReg
      hpateQuad hpateRadiusRegular hpateRadiusGeometry hpateFinite hpateDen
      hpateOrthogonality hpateFirst hpateScore hpateFunctional
      hpateEquicontinuity hpateGodambe,
    retrospective_patt_estimated_score_normality_and_variance_of_audited_local_experiment_changingLaw_score_adjustment_identity
      patt pattParameters pattOracleVariance pattFirstStepLoading
      pattTargetDriftLoading pattScoreCovariance hpatt_interpret hpattExact
      hpattBiasBound hpattGeometryRegular hpattCatchment
      hpattHeterogeneityMoment hpattHeterogeneityVariance hpattResidualReg
      hpattQuad hpattRadiusRegular hpattRadiusGeometry hpattFinite hpattDen
      hpattOrthogonality hpattFirst hpattScore hpattFunctional
      hpattEquicontinuity hpattGodambe⟩

/--
Paired retrospective PATE/PATT audited local-experiment routes, with fixed-law
score-adjustment identities and one compact local-experiment/Godambe core per
estimand.
-/
theorem
    retrospective_pate_patt_estimated_score_normality_and_variance_of_audited_local_experiment_fixedLaw_score_adjustment_identities_and_local_experiment_cores
    {PATEParam PATTParam : Type*}
    (pate : RetrospectivePATEEstimatedScoreAuditBridge)
    (patt : RetrospectivePATTEstimatedScoreAuditBridge)
    (pateParameters : Finset PATEParam) (pateOracleVariance : Real)
    (pateFirstStepLoading : PATEParam -> Real)
    (pateScoreCovariance : PATEParam -> PATEParam -> Real)
    (hpate_interpret :
      fixedLawScoreAdjustedVariance pateParameters pateOracleVariance
          pateFirstStepLoading pateScoreCovariance =
        pateOracleVariance -
          scoreQuadraticForm pateParameters pateFirstStepLoading
            pateScoreCovariance ->
        pate.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattScoreCovariance =
        pattOracleVariance -
          scoreQuadraticForm pattParameters pattFirstStepLoading
            pattScoreCovariance ->
        patt.estimated_input.score_adjustment_algebra)
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
    (pateCore : EstimatedScoreLocalExperimentVarianceCore pate.estimated_input)
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
    (pattCore : EstimatedScoreLocalExperimentVarianceCore patt.estimated_input) :
    (pate.estimated_score_asymptotic_normality ∧
        pate.estimated_score_variance_formula) ∧
      (patt.estimated_score_asymptotic_normality ∧
        patt.estimated_score_variance_formula) :=
  ⟨retrospective_pate_estimated_score_normality_and_variance_of_audited_local_experiment_fixedLaw_score_adjustment_identity_and_local_experiment_core
      pate pateParameters pateOracleVariance pateFirstStepLoading
      pateScoreCovariance hpate_interpret hpateExact hpateBiasBound
      hpateGeometryRegular hpateCatchment hpateHeterogeneityMoment
      hpateHeterogeneityVariance hpateResidualReg hpateQuad
      hpateRadiusRegular hpateRadiusGeometry hpateFinite hpateDen
      hpateOrthogonality hpateFirst hpateScore pateCore,
    retrospective_patt_estimated_score_normality_and_variance_of_audited_local_experiment_fixedLaw_score_adjustment_identity_and_local_experiment_core
      patt pattParameters pattOracleVariance pattFirstStepLoading
      pattScoreCovariance hpatt_interpret hpattExact hpattBiasBound
      hpattGeometryRegular hpattCatchment hpattHeterogeneityMoment
      hpattHeterogeneityVariance hpattResidualReg hpattQuad
      hpattRadiusRegular hpattRadiusGeometry hpattFinite hpattDen
      hpattOrthogonality hpattFirst hpattScore pattCore⟩

/--
Paired retrospective PATE/PATT audited local-experiment routes, with
changing-law score-adjustment identities and one compact local-experiment/
Godambe core per estimand.
-/
theorem
    retrospective_pate_patt_estimated_score_normality_and_variance_of_audited_local_experiment_changingLaw_score_adjustment_identities_and_local_experiment_cores
    {PATEParam PATTParam : Type*}
    (pate : RetrospectivePATEEstimatedScoreAuditBridge)
    (patt : RetrospectivePATTEstimatedScoreAuditBridge)
    (pateParameters : Finset PATEParam) (pateOracleVariance : Real)
    (pateFirstStepLoading pateTargetDriftLoading : PATEParam -> Real)
    (pateScoreCovariance : PATEParam -> PATEParam -> Real)
    (hpate_interpret :
      changingLawScoreAdjustedVariance pateParameters pateOracleVariance
          pateFirstStepLoading pateTargetDriftLoading pateScoreCovariance =
        fixedLawScoreAdjustedVariance pateParameters pateOracleVariance
            pateFirstStepLoading pateScoreCovariance +
          scoreQuadraticForm pateParameters pateTargetDriftLoading
            pateScoreCovariance ->
        pate.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading pattTargetDriftLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      changingLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattTargetDriftLoading pattScoreCovariance =
        fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
            pattFirstStepLoading pattScoreCovariance +
          scoreQuadraticForm pattParameters pattTargetDriftLoading
            pattScoreCovariance ->
        patt.estimated_input.score_adjustment_algebra)
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
    (pateCore : EstimatedScoreLocalExperimentVarianceCore pate.estimated_input)
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
    (pattCore : EstimatedScoreLocalExperimentVarianceCore patt.estimated_input) :
    (pate.estimated_score_asymptotic_normality ∧
        pate.estimated_score_variance_formula) ∧
      (patt.estimated_score_asymptotic_normality ∧
        patt.estimated_score_variance_formula) :=
  ⟨retrospective_pate_estimated_score_normality_and_variance_of_audited_local_experiment_changingLaw_score_adjustment_identity_and_local_experiment_core
      pate pateParameters pateOracleVariance pateFirstStepLoading
      pateTargetDriftLoading pateScoreCovariance hpate_interpret hpateExact
      hpateBiasBound hpateGeometryRegular hpateCatchment
      hpateHeterogeneityMoment hpateHeterogeneityVariance hpateResidualReg
      hpateQuad hpateRadiusRegular hpateRadiusGeometry hpateFinite hpateDen
      hpateOrthogonality hpateFirst hpateScore pateCore,
    retrospective_patt_estimated_score_normality_and_variance_of_audited_local_experiment_changingLaw_score_adjustment_identity_and_local_experiment_core
      patt pattParameters pattOracleVariance pattFirstStepLoading
      pattTargetDriftLoading pattScoreCovariance hpatt_interpret hpattExact
      hpattBiasBound hpattGeometryRegular hpattCatchment
      hpattHeterogeneityMoment hpattHeterogeneityVariance hpattResidualReg
      hpattQuad hpattRadiusRegular hpattRadiusGeometry hpattFinite hpattDen
      hpattOrthogonality hpattFirst hpattScore pattCore⟩

end WDSM
end Matching
end StatInference
