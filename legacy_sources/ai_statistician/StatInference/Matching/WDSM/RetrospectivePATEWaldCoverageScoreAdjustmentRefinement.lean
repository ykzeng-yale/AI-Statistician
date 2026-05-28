import StatInference.Matching.WDSM.RetrospectivePATEWaldCoverage
import StatInference.Matching.WDSM.EstimatedScoreLocalExperimentVarianceRefinement

/-!
# Retrospective PATE Wald coverage with concrete score-adjustment algebra

This module pushes the fixed-law and changing-law score-adjustment refinements
through the retrospective PATE studentized and ordinary Wald coverage routes.
The coverage calibration, geometry, residual, local-expansion, and Godambe
premises remain explicit; these wrappers only replace direct
`score_adjustment_algebra` inputs by finite quadratic-form identities plus an
interpretation bridge.
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
Retrospective PATE estimated-score studentized weak limit, with
score-adjustment algebra supplied by the fixed-law finite quadratic-form
identity.
-/
theorem
    retrospective_pate_estimated_score_studentized_tendsto_of_audited_local_experiment_fixedLaw_score_adjustment_identity
    {Param : Type*}
    (b :
      RetrospectivePATEEstimatedScoreStudentizedBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hfirst :
      b.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hfunctional :
      b.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
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
          (fun _index => sampleLaw) limitLaw :=
  retrospective_pate_estimated_score_studentized_tendsto_of_audited_local_experiment
    b hexact hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
    hheterogeneity_variance hresidual_reg hquad hradius_regular
    hradius_geometry hfinite hden horthogonality hfirst hscore hfunctional
    hequicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      b.estimated_bridge.estimated_input.score_adjustment_algebra parameters
      oracleVariance firstStepLoading scoreCovariance hinterpret)
    hgodambe

/--
Retrospective PATE estimated-score studentized weak limit, with
score-adjustment algebra supplied by the changing-law finite quadratic-form
identity.
-/
theorem
    retrospective_pate_estimated_score_studentized_tendsto_of_audited_local_experiment_changingLaw_score_adjustment_identity
    {Param : Type*}
    (b :
      RetrospectivePATEEstimatedScoreStudentizedBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hfirst :
      b.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hfunctional :
      b.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
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
          (fun _index => sampleLaw) limitLaw :=
  retrospective_pate_estimated_score_studentized_tendsto_of_audited_local_experiment
    b hexact hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
    hheterogeneity_variance hresidual_reg hquad hradius_regular
    hradius_geometry hfinite hden horthogonality hfirst hscore hfunctional
    hequicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      b.estimated_bridge.estimated_input.score_adjustment_algebra parameters
      oracleVariance firstStepLoading targetDriftLoading scoreCovariance
      hinterpret)
    hgodambe

/--
Retrospective PATE estimated-score studentized weak limit, with fixed-law
score-adjustment algebra and one compact local-experiment/Godambe core.
-/
theorem
    retrospective_pate_estimated_score_studentized_tendsto_of_audited_local_experiment_fixedLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    (b :
      RetrospectivePATEEstimatedScoreStudentizedBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hfirst :
      b.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
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
          (fun _index => sampleLaw) limitLaw :=
  retrospective_pate_estimated_score_studentized_tendsto_of_audited_local_experiment_fixedLaw_score_adjustment_identity
    b parameters oracleVariance firstStepLoading scoreCovariance hinterpret
    hexact hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
    hheterogeneity_variance hresidual_reg hquad hradius_regular
    hradius_geometry hfinite hden horthogonality hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

/--
Retrospective PATE estimated-score studentized weak limit, with changing-law
score-adjustment algebra and one compact local-experiment/Godambe core.
-/
theorem
    retrospective_pate_estimated_score_studentized_tendsto_of_audited_local_experiment_changingLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    (b :
      RetrospectivePATEEstimatedScoreStudentizedBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hfirst :
      b.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
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
          (fun _index => sampleLaw) limitLaw :=
  retrospective_pate_estimated_score_studentized_tendsto_of_audited_local_experiment_changingLaw_score_adjustment_identity
    b parameters oracleVariance firstStepLoading targetDriftLoading
    scoreCovariance hinterpret hexact hbias_bound hgeometry_regular
    hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
    hquad hradius_regular hradius_geometry hfinite hden horthogonality
    hfirst hscore core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

/--
Retrospective PATE estimated-score studentized weak limit from first-step
Z-component certificates, with score-adjustment algebra supplied by the
fixed-law finite quadratic-form identity.
-/
theorem
    retrospective_pate_estimated_score_studentized_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity
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
    (b :
      RetrospectivePATEEstimatedScoreStudentizedBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (firstStep : PATEDoubleScoreFirstStepAssembly)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        b.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        b.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
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
    (hfunctional :
      b.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
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
  have hfirst_score :
      b.estimated_bridge.estimated_input.first_step_asymptotic_linearization ∧
        b.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity :=
    estimated_score_local_experiment_variance_input_first_step_and_score_local_of_pate_z_components
      firstStep b.estimated_bridge.estimated_input propensity treated control
      hfirst_transfer hscore_transfer h_prop_weight h_treated_weight
      h_control_weight h_prop_component h_treated_component
      h_control_component
  exact
    retrospective_pate_estimated_score_studentized_tendsto_of_audited_local_experiment_fixedLaw_score_adjustment_identity
      b parameters oracleVariance firstStepLoading scoreCovariance
      hinterpret hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst_score.1 hfirst_score.2 hfunctional hequicontinuity hgodambe

/--
Retrospective PATE estimated-score studentized weak limit from first-step
Z-component certificates, with score-adjustment algebra supplied by the
changing-law finite quadratic-form identity.
-/
theorem
    retrospective_pate_estimated_score_studentized_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity
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
    (b :
      RetrospectivePATEEstimatedScoreStudentizedBridge Index Sample
        LimitSample sampleLaw limitLaw l)
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
        b.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        b.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        b.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
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
    (hfunctional :
      b.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
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
  have hfirst_score :
      b.estimated_bridge.estimated_input.first_step_asymptotic_linearization ∧
        b.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity :=
    estimated_score_local_experiment_variance_input_first_step_and_score_local_of_pate_z_components
      firstStep b.estimated_bridge.estimated_input propensity treated control
      hfirst_transfer hscore_transfer h_prop_weight h_treated_weight
      h_control_weight h_prop_component h_treated_component
      h_control_component
  exact
    retrospective_pate_estimated_score_studentized_tendsto_of_audited_local_experiment_changingLaw_score_adjustment_identity
      b parameters oracleVariance firstStepLoading targetDriftLoading
      scoreCovariance hinterpret hexact hbias_bound hgeometry_regular
      hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
      hquad hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst_score.1 hfirst_score.2 hfunctional hequicontinuity hgodambe

/--
Retrospective PATE estimated-score studentized weak limit from first-step
Z-component certificates, with fixed-law score-adjustment algebra and compact
local-experiment/Godambe core.
-/
theorem
    retrospective_pate_estimated_score_studentized_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity_and_local_experiment_core
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
    (b :
      RetrospectivePATEEstimatedScoreStudentizedBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (firstStep : PATEDoubleScoreFirstStepAssembly)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        b.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        b.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
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
    (core :
      EstimatedScoreLocalExperimentVarianceCore b.estimated_bridge.estimated_input) :
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
          (fun _index => sampleLaw) limitLaw :=
  retrospective_pate_estimated_score_studentized_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity
    b firstStep parameters oracleVariance firstStepLoading scoreCovariance
    hinterpret propensity treated control hexact hbias_bound hgeometry_regular
    hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
    hquad hradius_regular hradius_geometry hfinite hden horthogonality
    hfirst_transfer hscore_transfer h_prop_weight h_treated_weight
    h_control_weight h_prop_component h_treated_component h_control_component
    core.matching_functional_local_derivative core.local_stochastic_equicontinuity
    core.godambe_identity

/--
Retrospective PATE estimated-score studentized weak limit from first-step
Z-component certificates, with changing-law score-adjustment algebra and
compact local-experiment/Godambe core.
-/
theorem
    retrospective_pate_estimated_score_studentized_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity_and_local_experiment_core
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
    (b :
      RetrospectivePATEEstimatedScoreStudentizedBridge Index Sample
        LimitSample sampleLaw limitLaw l)
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
        b.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        b.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        b.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
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
    (core :
      EstimatedScoreLocalExperimentVarianceCore b.estimated_bridge.estimated_input) :
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
          (fun _index => sampleLaw) limitLaw :=
  retrospective_pate_estimated_score_studentized_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity
    b firstStep parameters oracleVariance firstStepLoading targetDriftLoading
    scoreCovariance hinterpret propensity treated control hexact hbias_bound
    hgeometry_regular hcatchment hheterogeneity_moment
    hheterogeneity_variance hresidual_reg hquad hradius_regular
    hradius_geometry hfinite hden horthogonality hfirst_transfer
    hscore_transfer h_prop_weight h_treated_weight h_control_weight
    h_prop_component h_treated_component h_control_component
    core.matching_functional_local_derivative core.local_stochastic_equicontinuity
    core.godambe_identity

/--
Retrospective PATE absolute-Wald coverage, with score-adjustment algebra
supplied by the fixed-law finite quadratic-form identity.
-/
theorem
    retrospective_pate_absoluteWaldCoverage_tendsto_of_estimated_score_studentized_fixedLaw_score_adjustment_identity
    {Param : Type*}
    (b :
      RetrospectivePATEEstimatedScoreAbsoluteWaldBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
            l (nhds b.coverage_input.coverageLimit) :=
  retrospective_pate_absoluteWaldCoverage_tendsto_of_estimated_score_studentized
    b hexact hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
    hheterogeneity_variance hresidual_reg hquad hradius_regular
    hradius_geometry hfinite hden horthogonality hfirst hscore hfunctional
    hequicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
      parameters oracleVariance firstStepLoading scoreCovariance hinterpret)
    hgodambe

/--
Retrospective PATE absolute-Wald coverage, with score-adjustment algebra
supplied by the changing-law finite quadratic-form identity.
-/
theorem
    retrospective_pate_absoluteWaldCoverage_tendsto_of_estimated_score_studentized_changingLaw_score_adjustment_identity
    {Param : Type*}
    (b :
      RetrospectivePATEEstimatedScoreAbsoluteWaldBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
            l (nhds b.coverage_input.coverageLimit) :=
  retrospective_pate_absoluteWaldCoverage_tendsto_of_estimated_score_studentized
    b hexact hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
    hheterogeneity_variance hresidual_reg hquad hradius_regular
    hradius_geometry hfinite hden horthogonality hfirst hscore hfunctional
    hequicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
      parameters oracleVariance firstStepLoading targetDriftLoading
      scoreCovariance hinterpret)
    hgodambe

/--
Retrospective PATE absolute-Wald coverage, with score-adjustment algebra
supplied by the fixed-law finite quadratic-form identity and the
local-experiment assumptions supplied by one compact core.
-/
theorem
    retrospective_pate_absoluteWaldCoverage_tendsto_of_estimated_score_studentized_fixedLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    (b :
      RetrospectivePATEEstimatedScoreAbsoluteWaldBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
            l (nhds b.coverage_input.coverageLimit) :=
  retrospective_pate_absoluteWaldCoverage_tendsto_of_estimated_score_studentized_fixedLaw_score_adjustment_identity
    b parameters oracleVariance firstStepLoading scoreCovariance hinterpret
    hexact hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
    hheterogeneity_variance hresidual_reg hquad hradius_regular
    hradius_geometry hfinite hden horthogonality hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

/--
Retrospective PATE absolute-Wald coverage, with score-adjustment algebra
supplied by the changing-law finite quadratic-form identity and the
local-experiment assumptions supplied by one compact core.
-/
theorem
    retrospective_pate_absoluteWaldCoverage_tendsto_of_estimated_score_studentized_changingLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    (b :
      RetrospectivePATEEstimatedScoreAbsoluteWaldBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
            l (nhds b.coverage_input.coverageLimit) :=
  retrospective_pate_absoluteWaldCoverage_tendsto_of_estimated_score_studentized_changingLaw_score_adjustment_identity
    b parameters oracleVariance firstStepLoading targetDriftLoading
    scoreCovariance hinterpret hexact hbias_bound hgeometry_regular
    hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
    hquad hradius_regular hradius_geometry hfinite hden horthogonality
    hfirst hscore core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

/--
Retrospective PATE two-sided Wald coverage, with score-adjustment algebra
supplied by the fixed-law finite quadratic-form identity.
-/
theorem
    retrospective_pate_twoSidedWaldCoverage_tendsto_of_estimated_score_studentized_fixedLaw_score_adjustment_identity
    {Param : Type*}
    (b :
      RetrospectivePATEEstimatedScoreTwoSidedWaldBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
            l (nhds b.coverage_input.coverageLimit) :=
  retrospective_pate_twoSidedWaldCoverage_tendsto_of_estimated_score_studentized
    b hexact hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
    hheterogeneity_variance hresidual_reg hquad hradius_regular
    hradius_geometry hfinite hden horthogonality hfirst hscore hfunctional
    hequicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
      parameters oracleVariance firstStepLoading scoreCovariance hinterpret)
    hgodambe

/--
Retrospective PATE two-sided Wald coverage, with score-adjustment algebra
supplied by the changing-law finite quadratic-form identity.
-/
theorem
    retrospective_pate_twoSidedWaldCoverage_tendsto_of_estimated_score_studentized_changingLaw_score_adjustment_identity
    {Param : Type*}
    (b :
      RetrospectivePATEEstimatedScoreTwoSidedWaldBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
            l (nhds b.coverage_input.coverageLimit) :=
  retrospective_pate_twoSidedWaldCoverage_tendsto_of_estimated_score_studentized
    b hexact hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
    hheterogeneity_variance hresidual_reg hquad hradius_regular
    hradius_geometry hfinite hden horthogonality hfirst hscore hfunctional
    hequicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
      parameters oracleVariance firstStepLoading targetDriftLoading
      scoreCovariance hinterpret)
    hgodambe

/--
Retrospective PATE two-sided Wald coverage, with score-adjustment algebra
supplied by the fixed-law finite quadratic-form identity and the
local-experiment assumptions supplied by one compact core.
-/
theorem
    retrospective_pate_twoSidedWaldCoverage_tendsto_of_estimated_score_studentized_fixedLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    (b :
      RetrospectivePATEEstimatedScoreTwoSidedWaldBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
            l (nhds b.coverage_input.coverageLimit) :=
  retrospective_pate_twoSidedWaldCoverage_tendsto_of_estimated_score_studentized_fixedLaw_score_adjustment_identity
    b parameters oracleVariance firstStepLoading scoreCovariance hinterpret
    hexact hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
    hheterogeneity_variance hresidual_reg hquad hradius_regular
    hradius_geometry hfinite hden horthogonality hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

/--
Retrospective PATE two-sided Wald coverage, with score-adjustment algebra
supplied by the changing-law finite quadratic-form identity and the
local-experiment assumptions supplied by one compact core.
-/
theorem
    retrospective_pate_twoSidedWaldCoverage_tendsto_of_estimated_score_studentized_changingLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    (b :
      RetrospectivePATEEstimatedScoreTwoSidedWaldBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
            l (nhds b.coverage_input.coverageLimit) :=
  retrospective_pate_twoSidedWaldCoverage_tendsto_of_estimated_score_studentized_changingLaw_score_adjustment_identity
    b parameters oracleVariance firstStepLoading targetDriftLoading
    scoreCovariance hinterpret hexact hbias_bound hgeometry_regular
    hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
    hquad hradius_regular hradius_geometry hfinite hden horthogonality
    hfirst hscore core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

section RetrospectivePATEAbsoluteWaldZComponents

variable {Param : Type*}
variable {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
variable {PInfluenceFunction : Type x} {PLinearPart : Type y}
variable {PRemainder : Type z}
variable {TSample : ℕ -> Type u} {TParameter : Type v} {TMoment : Type w}
variable {TInfluenceFunction : Type x} {TLinearPart : Type y}
variable {TRemainder : Type z}
variable {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
variable {CInfluenceFunction : Type x} {CLinearPart : Type y}
variable {CRemainder : Type z}
variable
    (b :
      RetrospectivePATEEstimatedScoreAbsoluteWaldBridge Index Sample
        LimitSample sampleLaw limitLaw l)
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
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        b.studentized_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        b.studentized_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
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
    (hfunctional :
      b.studentized_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.studentized_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hgodambe :
      b.studentized_bridge.estimated_bridge.estimated_input.godambe_identity)

include b firstStep propensity treated control hexact hbias_bound
  hgeometry_regular hcatchment hheterogeneity_moment hheterogeneity_variance
  hresidual_reg hquad hradius_regular hradius_geometry hfinite hden
  horthogonality hfirst_transfer hscore_transfer h_prop_weight
  h_treated_weight h_control_weight h_prop_component h_treated_component
  h_control_component hfunctional hequicontinuity hgodambe

/--
Retrospective PATE absolute-Wald coverage from first-step Z-component
certificates, with score-adjustment algebra supplied by the fixed-law finite
quadratic-form identity.
-/
theorem
    retrospective_pate_absoluteWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra) :
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
    retrospective_pate_estimated_score_studentized_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity
      b.studentized_bridge firstStep parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret propensity treated control
      hexact hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
      hheterogeneity_variance hresidual_reg hquad hradius_regular
      hradius_geometry hfinite hden horthogonality hfirst_transfer
      hscore_transfer h_prop_weight h_treated_weight h_control_weight
      h_prop_component h_treated_component h_control_component hfunctional
      hequicontinuity hgodambe
  have hcoverage := absoluteWaldCoverage_tendsto_of_input b.coverage_input
  exact ⟨hstudentized.1, hstudentized.2.1, hstudentized.2.2, hcoverage⟩

/--
Retrospective PATE absolute-Wald coverage from first-step Z-component
certificates, with score-adjustment algebra supplied by the changing-law
finite quadratic-form identity.
-/
theorem
    retrospective_pate_absoluteWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra) :
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
    retrospective_pate_estimated_score_studentized_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity
      b.studentized_bridge firstStep parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret
      propensity treated control hexact hbias_bound hgeometry_regular
      hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
      hquad hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst_transfer hscore_transfer h_prop_weight h_treated_weight
      h_control_weight h_prop_component h_treated_component
      h_control_component hfunctional hequicontinuity hgodambe
  have hcoverage := absoluteWaldCoverage_tendsto_of_input b.coverage_input
  exact ⟨hstudentized.1, hstudentized.2.1, hstudentized.2.2, hcoverage⟩

omit hfunctional hequicontinuity hgodambe in
/--
Retrospective PATE absolute-Wald coverage from first-step Z-component
certificates, with fixed-law score-adjustment algebra and compact
local-experiment/Godambe core.
-/
theorem
    retrospective_pate_absoluteWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
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
  have hstudentized :=
    retrospective_pate_estimated_score_studentized_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity_and_local_experiment_core
      b.studentized_bridge firstStep parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret propensity treated control
      hexact hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
      hheterogeneity_variance hresidual_reg hquad hradius_regular
      hradius_geometry hfinite hden horthogonality hfirst_transfer
      hscore_transfer h_prop_weight h_treated_weight h_control_weight
      h_prop_component h_treated_component h_control_component core
  have hcoverage := absoluteWaldCoverage_tendsto_of_input b.coverage_input
  exact ⟨hstudentized.1, hstudentized.2.1, hstudentized.2.2, hcoverage⟩

omit hfunctional hequicontinuity hgodambe in
/--
Retrospective PATE absolute-Wald coverage from first-step Z-component
certificates, with changing-law score-adjustment algebra and compact
local-experiment/Godambe core.
-/
theorem
    retrospective_pate_absoluteWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
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
  have hstudentized :=
    retrospective_pate_estimated_score_studentized_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity_and_local_experiment_core
      b.studentized_bridge firstStep parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret
      propensity treated control hexact hbias_bound hgeometry_regular
      hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
      hquad hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst_transfer hscore_transfer h_prop_weight h_treated_weight
      h_control_weight h_prop_component h_treated_component
      h_control_component core
  have hcoverage := absoluteWaldCoverage_tendsto_of_input b.coverage_input
  exact ⟨hstudentized.1, hstudentized.2.1, hstudentized.2.2, hcoverage⟩

end RetrospectivePATEAbsoluteWaldZComponents

section RetrospectivePATETwoSidedWaldZComponents

variable {Param : Type*}
variable {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
variable {PInfluenceFunction : Type x} {PLinearPart : Type y}
variable {PRemainder : Type z}
variable {TSample : ℕ -> Type u} {TParameter : Type v} {TMoment : Type w}
variable {TInfluenceFunction : Type x} {TLinearPart : Type y}
variable {TRemainder : Type z}
variable {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
variable {CInfluenceFunction : Type x} {CLinearPart : Type y}
variable {CRemainder : Type z}
variable
    (b :
      RetrospectivePATEEstimatedScoreTwoSidedWaldBridge Index Sample
        LimitSample sampleLaw limitLaw l)
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
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        b.studentized_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        b.studentized_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
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
    (hfunctional :
      b.studentized_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.studentized_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hgodambe :
      b.studentized_bridge.estimated_bridge.estimated_input.godambe_identity)

include b firstStep propensity treated control hexact hbias_bound
  hgeometry_regular hcatchment hheterogeneity_moment hheterogeneity_variance
  hresidual_reg hquad hradius_regular hradius_geometry hfinite hden
  horthogonality hfirst_transfer hscore_transfer h_prop_weight
  h_treated_weight h_control_weight h_prop_component h_treated_component
  h_control_component hfunctional hequicontinuity hgodambe

/--
Retrospective PATE two-sided Wald coverage from first-step Z-component
certificates, with score-adjustment algebra supplied by the fixed-law finite
quadratic-form identity.
-/
theorem
    retrospective_pate_twoSidedWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra) :
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
    retrospective_pate_estimated_score_studentized_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity
      b.studentized_bridge firstStep parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret propensity treated control
      hexact hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
      hheterogeneity_variance hresidual_reg hquad hradius_regular
      hradius_geometry hfinite hden horthogonality hfirst_transfer
      hscore_transfer h_prop_weight h_treated_weight h_control_weight
      h_prop_component h_treated_component h_control_component hfunctional
      hequicontinuity hgodambe
  have hcoverage := twoSidedWaldCoverage_tendsto_of_input b.coverage_input
  exact ⟨hstudentized.1, hstudentized.2.1, hstudentized.2.2, hcoverage⟩

/--
Retrospective PATE two-sided Wald coverage from first-step Z-component
certificates, with score-adjustment algebra supplied by the changing-law
finite quadratic-form identity.
-/
theorem
    retrospective_pate_twoSidedWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra) :
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
    retrospective_pate_estimated_score_studentized_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity
      b.studentized_bridge firstStep parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret
      propensity treated control hexact hbias_bound hgeometry_regular
      hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
      hquad hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst_transfer hscore_transfer h_prop_weight h_treated_weight
      h_control_weight h_prop_component h_treated_component
      h_control_component hfunctional hequicontinuity hgodambe
  have hcoverage := twoSidedWaldCoverage_tendsto_of_input b.coverage_input
  exact ⟨hstudentized.1, hstudentized.2.1, hstudentized.2.2, hcoverage⟩

omit hfunctional hequicontinuity hgodambe in
/--
Retrospective PATE two-sided Wald coverage from first-step Z-component
certificates, with fixed-law score-adjustment algebra and compact
local-experiment/Godambe core.
-/
theorem
    retrospective_pate_twoSidedWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
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
  have hstudentized :=
    retrospective_pate_estimated_score_studentized_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity_and_local_experiment_core
      b.studentized_bridge firstStep parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret propensity treated control
      hexact hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
      hheterogeneity_variance hresidual_reg hquad hradius_regular
      hradius_geometry hfinite hden horthogonality hfirst_transfer
      hscore_transfer h_prop_weight h_treated_weight h_control_weight
      h_prop_component h_treated_component h_control_component core
  have hcoverage := twoSidedWaldCoverage_tendsto_of_input b.coverage_input
  exact ⟨hstudentized.1, hstudentized.2.1, hstudentized.2.2, hcoverage⟩

omit hfunctional hequicontinuity hgodambe in
/--
Retrospective PATE two-sided Wald coverage from first-step Z-component
certificates, with changing-law score-adjustment algebra and compact
local-experiment/Godambe core.
-/
theorem
    retrospective_pate_twoSidedWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
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
  have hstudentized :=
    retrospective_pate_estimated_score_studentized_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity_and_local_experiment_core
      b.studentized_bridge firstStep parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret
      propensity treated control hexact hbias_bound hgeometry_regular
      hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
      hquad hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst_transfer hscore_transfer h_prop_weight h_treated_weight
      h_control_weight h_prop_component h_treated_component
      h_control_component core
  have hcoverage := twoSidedWaldCoverage_tendsto_of_input b.coverage_input
  exact ⟨hstudentized.1, hstudentized.2.1, hstudentized.2.2, hcoverage⟩

end RetrospectivePATETwoSidedWaldZComponents

end WDSM
end Matching
end StatInference
