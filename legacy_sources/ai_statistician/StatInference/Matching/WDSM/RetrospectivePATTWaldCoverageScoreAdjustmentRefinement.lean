import StatInference.Matching.WDSM.RetrospectivePATTWaldCoverage
import StatInference.Matching.WDSM.EstimatedScoreAuditScoreAdjustmentRefinement

/-!
# Retrospective PATT Wald coverage with concrete score-adjustment algebra

This module pushes the fixed-law and changing-law score-adjustment refinements
through the retrospective PATT studentized and ordinary Wald coverage routes.
The coverage calibration, geometry, residual, local-expansion, and Godambe
premises remain explicit; these wrappers only replace direct first-step,
score-local, and `score_adjustment_algebra` inputs by first-step
Z-component evidence, transfer maps, and finite quadratic-form identities.
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
Retrospective PATT estimated-score studentized weak limit, with
score-adjustment algebra supplied by the fixed-law finite quadratic-form
identity.
-/
theorem
    retrospective_patt_estimated_score_studentized_tendsto_of_audited_local_experiment_fixedLaw_score_adjustment_identity
    {Param : Type*}
    (b :
      RetrospectivePATTEstimatedScoreStudentizedBridge Index Sample
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
  retrospective_patt_estimated_score_studentized_tendsto_of_audited_local_experiment
    b hexact hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
    hheterogeneity_variance hresidual_reg hquad hradius_regular
    hradius_geometry hfinite hden horthogonality hfirst hscore hfunctional
    hequicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      b.estimated_bridge.estimated_input.score_adjustment_algebra parameters
      oracleVariance firstStepLoading scoreCovariance hinterpret)
    hgodambe

/--
Retrospective PATT estimated-score studentized weak limit, with
score-adjustment algebra supplied by the changing-law finite quadratic-form
identity.
-/
theorem
    retrospective_patt_estimated_score_studentized_tendsto_of_audited_local_experiment_changingLaw_score_adjustment_identity
    {Param : Type*}
    (b :
      RetrospectivePATTEstimatedScoreStudentizedBridge Index Sample
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
  retrospective_patt_estimated_score_studentized_tendsto_of_audited_local_experiment
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
Retrospective PATT estimated-score studentized weak limit, with fixed-law
score-adjustment algebra and one compact local-experiment/Godambe core.
-/
theorem
    retrospective_patt_estimated_score_studentized_tendsto_of_audited_local_experiment_fixedLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    (b :
      RetrospectivePATTEstimatedScoreStudentizedBridge Index Sample
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
  retrospective_patt_estimated_score_studentized_tendsto_of_audited_local_experiment_fixedLaw_score_adjustment_identity
    b parameters oracleVariance firstStepLoading scoreCovariance hinterpret
    hexact hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
    hheterogeneity_variance hresidual_reg hquad hradius_regular
    hradius_geometry hfinite hden horthogonality hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

/--
Retrospective PATT estimated-score studentized weak limit, with changing-law
score-adjustment algebra and one compact local-experiment/Godambe core.
-/
theorem
    retrospective_patt_estimated_score_studentized_tendsto_of_audited_local_experiment_changingLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    (b :
      RetrospectivePATTEstimatedScoreStudentizedBridge Index Sample
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
  retrospective_patt_estimated_score_studentized_tendsto_of_audited_local_experiment_changingLaw_score_adjustment_identity
    b parameters oracleVariance firstStepLoading targetDriftLoading
    scoreCovariance hinterpret hexact hbias_bound hgeometry_regular
    hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
    hquad hradius_regular hradius_geometry hfinite hden horthogonality
    hfirst hscore core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

/--
Retrospective PATT estimated-score studentized weak limit from first-step
Z-component certificates, with score-adjustment algebra supplied by the
fixed-law finite quadratic-form identity.
-/
theorem
    retrospective_patt_estimated_score_studentized_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity
    {Param : Type*}
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b :
      RetrospectivePATTEstimatedScoreStudentizedBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (firstStep : PATTDoubleScoreFirstStepAssembly)
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
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
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
  have hestimated_pair :=
    retrospective_patt_estimated_score_normality_and_variance_of_audited_z_components_fixedLaw_score_adjustment_identity
      b.estimated_bridge firstStep parameters oracleVariance firstStepLoading
      scoreCovariance hinterpret propensity control hexact hbias_bound
      hgeometry_regular hcatchment hheterogeneity_moment
      hheterogeneity_variance hresidual_reg hquad hradius_regular
      hradius_geometry hfinite hden horthogonality hfirst_transfer
      hscore_transfer h_prop_weight h_control_weight h_prop_component
      h_control_component hfunctional hequicontinuity hgodambe
  have hstudentized :=
    studentized_tendstoInDistribution_of_estimated_score_studentization_input
      b.studentization_input
      (b.estimated_score_to_scaled_tendsto hestimated_pair.1)
  exact ⟨hestimated_pair.1, hestimated_pair.2, hstudentized⟩

/--
Retrospective PATT estimated-score studentized weak limit from first-step
Z-component certificates, with score-adjustment algebra supplied by the
changing-law finite quadratic-form identity.
-/
theorem
    retrospective_patt_estimated_score_studentized_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity
    {Param : Type*}
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b :
      RetrospectivePATTEstimatedScoreStudentizedBridge Index Sample
        LimitSample sampleLaw limitLaw l)
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
        b.estimated_bridge.estimated_input.score_adjustment_algebra)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
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
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
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
  have hestimated_pair :=
    retrospective_patt_estimated_score_normality_and_variance_of_audited_z_components_changingLaw_score_adjustment_identity
      b.estimated_bridge firstStep parameters oracleVariance firstStepLoading
      targetDriftLoading scoreCovariance hinterpret propensity control hexact
      hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
      hheterogeneity_variance hresidual_reg hquad hradius_regular
      hradius_geometry hfinite hden horthogonality hfirst_transfer
      hscore_transfer h_prop_weight h_control_weight h_prop_component
      h_control_component hfunctional hequicontinuity hgodambe
  have hstudentized :=
    studentized_tendstoInDistribution_of_estimated_score_studentization_input
      b.studentization_input
      (b.estimated_score_to_scaled_tendsto hestimated_pair.1)
  exact ⟨hestimated_pair.1, hestimated_pair.2, hstudentized⟩

/--
Retrospective PATT estimated-score studentized weak limit from first-step
Z-component certificates, with fixed-law score-adjustment algebra and a compact
local-experiment/Godambe core.
-/
theorem
    retrospective_patt_estimated_score_studentized_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b :
      RetrospectivePATTEstimatedScoreStudentizedBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (firstStep : PATTDoubleScoreFirstStepAssembly)
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
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity)
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
  retrospective_patt_estimated_score_studentized_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity
    b firstStep parameters oracleVariance firstStepLoading scoreCovariance
    hinterpret propensity control hexact hbias_bound hgeometry_regular
    hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
    hquad hradius_regular hradius_geometry hfinite hden horthogonality
    hfirst_transfer hscore_transfer h_prop_weight h_control_weight
    h_prop_component h_control_component
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

/--
Retrospective PATT estimated-score studentized weak limit from first-step
Z-component certificates, with changing-law score-adjustment algebra and a
compact local-experiment/Godambe core.
-/
theorem
    retrospective_patt_estimated_score_studentized_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b :
      RetrospectivePATTEstimatedScoreStudentizedBridge Index Sample
        LimitSample sampleLaw limitLaw l)
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
        b.estimated_bridge.estimated_input.score_adjustment_algebra)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
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
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity)
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
  retrospective_patt_estimated_score_studentized_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity
    b firstStep parameters oracleVariance firstStepLoading targetDriftLoading
    scoreCovariance hinterpret propensity control hexact hbias_bound
    hgeometry_regular hcatchment hheterogeneity_moment
    hheterogeneity_variance hresidual_reg hquad hradius_regular
    hradius_geometry hfinite hden horthogonality hfirst_transfer
    hscore_transfer h_prop_weight h_control_weight h_prop_component
    h_control_component core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

/--
Retrospective PATT absolute-Wald coverage, with score-adjustment algebra
supplied by the fixed-law finite quadratic-form identity.
-/
theorem
    retrospective_patt_absoluteWaldCoverage_tendsto_of_estimated_score_studentized_fixedLaw_score_adjustment_identity
    {Param : Type*}
    (b :
      RetrospectivePATTEstimatedScoreAbsoluteWaldBridge Index Sample
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
            b.studentized_bridge.studentization_input.scaledStatistic index sample *
              (standardError
                (b.studentized_bridge.studentization_input.varianceEstimate index sample))⁻¹)
          l
          (fun limitSample =>
            b.studentized_bridge.studentization_input.limit limitSample *
              (standardError b.studentized_bridge.studentization_input.varianceLimit)⁻¹)
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
  retrospective_patt_absoluteWaldCoverage_tendsto_of_estimated_score_studentized
    b hexact hbias_bound hgeometry_regular hcatchment
    hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
    hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore hfunctional hequicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
      parameters oracleVariance firstStepLoading scoreCovariance hinterpret)
    hgodambe

/--
Retrospective PATT absolute-Wald coverage, with score-adjustment algebra
supplied by the changing-law finite quadratic-form identity.
-/
theorem
    retrospective_patt_absoluteWaldCoverage_tendsto_of_estimated_score_studentized_changingLaw_score_adjustment_identity
    {Param : Type*}
    (b :
      RetrospectivePATTEstimatedScoreAbsoluteWaldBridge Index Sample
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
            b.studentized_bridge.studentization_input.scaledStatistic index sample *
              (standardError
                (b.studentized_bridge.studentization_input.varianceEstimate index sample))⁻¹)
          l
          (fun limitSample =>
            b.studentized_bridge.studentization_input.limit limitSample *
              (standardError b.studentized_bridge.studentization_input.varianceLimit)⁻¹)
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
  retrospective_patt_absoluteWaldCoverage_tendsto_of_estimated_score_studentized
    b hexact hbias_bound hgeometry_regular hcatchment
    hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
    hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore hfunctional hequicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
      parameters oracleVariance firstStepLoading targetDriftLoading
      scoreCovariance hinterpret)
    hgodambe

/--
Retrospective PATT absolute-Wald coverage, with score-adjustment algebra
supplied by the fixed-law finite quadratic-form identity and the
local-experiment assumptions supplied by one compact core.
-/
theorem
    retrospective_patt_absoluteWaldCoverage_tendsto_of_estimated_score_studentized_fixedLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    (b :
      RetrospectivePATTEstimatedScoreAbsoluteWaldBridge Index Sample
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
            b.studentized_bridge.studentization_input.scaledStatistic index sample *
              (standardError
                (b.studentized_bridge.studentization_input.varianceEstimate index sample))⁻¹)
          l
          (fun limitSample =>
            b.studentized_bridge.studentization_input.limit limitSample *
              (standardError b.studentized_bridge.studentization_input.varianceLimit)⁻¹)
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
  retrospective_patt_absoluteWaldCoverage_tendsto_of_estimated_score_studentized_core
    b hexact hbias_bound hgeometry_regular hcatchment
    hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
    hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
      parameters oracleVariance firstStepLoading scoreCovariance hinterpret)
    core

/--
Retrospective PATT absolute-Wald coverage, with score-adjustment algebra
supplied by the changing-law finite quadratic-form identity and the
local-experiment assumptions supplied by one compact core.
-/
theorem
    retrospective_patt_absoluteWaldCoverage_tendsto_of_estimated_score_studentized_changingLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    (b :
      RetrospectivePATTEstimatedScoreAbsoluteWaldBridge Index Sample
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
            b.studentized_bridge.studentization_input.scaledStatistic index sample *
              (standardError
                (b.studentized_bridge.studentization_input.varianceEstimate index sample))⁻¹)
          l
          (fun limitSample =>
            b.studentized_bridge.studentization_input.limit limitSample *
              (standardError b.studentized_bridge.studentization_input.varianceLimit)⁻¹)
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
  retrospective_patt_absoluteWaldCoverage_tendsto_of_estimated_score_studentized_core
    b hexact hbias_bound hgeometry_regular hcatchment
    hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
    hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
      parameters oracleVariance firstStepLoading targetDriftLoading
      scoreCovariance hinterpret)
    core

/--
Retrospective PATT two-sided Wald coverage, with score-adjustment algebra
supplied by the fixed-law finite quadratic-form identity.
-/
theorem
    retrospective_patt_twoSidedWaldCoverage_tendsto_of_estimated_score_studentized_fixedLaw_score_adjustment_identity
    {Param : Type*}
    (b :
      RetrospectivePATTEstimatedScoreTwoSidedWaldBridge Index Sample
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
            b.studentized_bridge.studentization_input.scaledStatistic index sample *
              (standardError
                (b.studentized_bridge.studentization_input.varianceEstimate index sample))⁻¹)
          l
          (fun limitSample =>
            b.studentized_bridge.studentization_input.limit limitSample *
              (standardError b.studentized_bridge.studentization_input.varianceLimit)⁻¹)
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
  retrospective_patt_twoSidedWaldCoverage_tendsto_of_estimated_score_studentized
    b hexact hbias_bound hgeometry_regular hcatchment
    hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
    hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore hfunctional hequicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
      parameters oracleVariance firstStepLoading scoreCovariance hinterpret)
    hgodambe

/--
Retrospective PATT two-sided Wald coverage, with score-adjustment algebra
supplied by the changing-law finite quadratic-form identity.
-/
theorem
    retrospective_patt_twoSidedWaldCoverage_tendsto_of_estimated_score_studentized_changingLaw_score_adjustment_identity
    {Param : Type*}
    (b :
      RetrospectivePATTEstimatedScoreTwoSidedWaldBridge Index Sample
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
            b.studentized_bridge.studentization_input.scaledStatistic index sample *
              (standardError
                (b.studentized_bridge.studentization_input.varianceEstimate index sample))⁻¹)
          l
          (fun limitSample =>
            b.studentized_bridge.studentization_input.limit limitSample *
              (standardError b.studentized_bridge.studentization_input.varianceLimit)⁻¹)
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
  retrospective_patt_twoSidedWaldCoverage_tendsto_of_estimated_score_studentized
    b hexact hbias_bound hgeometry_regular hcatchment
    hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
    hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore hfunctional hequicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
      parameters oracleVariance firstStepLoading targetDriftLoading
      scoreCovariance hinterpret)
    hgodambe

/--
Retrospective PATT two-sided Wald coverage, with score-adjustment algebra
supplied by the fixed-law finite quadratic-form identity and the
local-experiment assumptions supplied by one compact core.
-/
theorem
    retrospective_patt_twoSidedWaldCoverage_tendsto_of_estimated_score_studentized_fixedLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    (b :
      RetrospectivePATTEstimatedScoreTwoSidedWaldBridge Index Sample
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
            b.studentized_bridge.studentization_input.scaledStatistic index sample *
              (standardError
                (b.studentized_bridge.studentization_input.varianceEstimate index sample))⁻¹)
          l
          (fun limitSample =>
            b.studentized_bridge.studentization_input.limit limitSample *
              (standardError b.studentized_bridge.studentization_input.varianceLimit)⁻¹)
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
  retrospective_patt_twoSidedWaldCoverage_tendsto_of_estimated_score_studentized_core
    b hexact hbias_bound hgeometry_regular hcatchment
    hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
    hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
      parameters oracleVariance firstStepLoading scoreCovariance hinterpret)
    core

/--
Retrospective PATT two-sided Wald coverage, with score-adjustment algebra
supplied by the changing-law finite quadratic-form identity and the
local-experiment assumptions supplied by one compact core.
-/
theorem
    retrospective_patt_twoSidedWaldCoverage_tendsto_of_estimated_score_studentized_changingLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    (b :
      RetrospectivePATTEstimatedScoreTwoSidedWaldBridge Index Sample
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
            b.studentized_bridge.studentization_input.scaledStatistic index sample *
              (standardError
                (b.studentized_bridge.studentization_input.varianceEstimate index sample))⁻¹)
          l
          (fun limitSample =>
            b.studentized_bridge.studentization_input.limit limitSample *
              (standardError b.studentized_bridge.studentization_input.varianceLimit)⁻¹)
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
  retrospective_patt_twoSidedWaldCoverage_tendsto_of_estimated_score_studentized_core
    b hexact hbias_bound hgeometry_regular hcatchment
    hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
    hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
      parameters oracleVariance firstStepLoading targetDriftLoading
      scoreCovariance hinterpret)
    core

/--
Retrospective PATT absolute Wald coverage from first-step Z-component
certificates and the fixed-law finite score-adjustment identity.
-/
theorem
    retrospective_patt_absoluteWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity
    {Param : Type*}
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b :
      RetrospectivePATTEstimatedScoreAbsoluteWaldBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (firstStep : PATTDoubleScoreFirstStepAssembly)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
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
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity)
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
            b.studentized_bridge.studentization_input.scaledStatistic index sample *
              (standardError
                (b.studentized_bridge.studentization_input.varianceEstimate index sample))⁻¹)
          l
          (fun limitSample =>
            b.studentized_bridge.studentization_input.limit limitSample *
              (standardError b.studentized_bridge.studentization_input.varianceLimit)⁻¹)
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
    retrospective_patt_estimated_score_studentized_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity
      b.studentized_bridge firstStep parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret propensity control hexact
      hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
      hheterogeneity_variance hresidual_reg hquad hradius_regular
      hradius_geometry hfinite hden horthogonality hfirst_transfer
      hscore_transfer h_prop_weight h_control_weight h_prop_component
      h_control_component hfunctional hequicontinuity hgodambe
  have hcoverage := absoluteWaldCoverage_tendsto_of_input b.coverage_input
  exact ⟨hstudentized.1, hstudentized.2.1, hstudentized.2.2, hcoverage⟩

/--
Retrospective PATT absolute Wald coverage from first-step Z-component
certificates and the changing-law finite score-adjustment identity.
-/
theorem
    retrospective_patt_absoluteWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity
    {Param : Type*}
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b :
      RetrospectivePATTEstimatedScoreAbsoluteWaldBridge Index Sample
        LimitSample sampleLaw limitLaw l)
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
        b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
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
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity)
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
            b.studentized_bridge.studentization_input.scaledStatistic index sample *
              (standardError
                (b.studentized_bridge.studentization_input.varianceEstimate index sample))⁻¹)
          l
          (fun limitSample =>
            b.studentized_bridge.studentization_input.limit limitSample *
              (standardError b.studentized_bridge.studentization_input.varianceLimit)⁻¹)
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
    retrospective_patt_estimated_score_studentized_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity
      b.studentized_bridge firstStep parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret
      propensity control hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst_transfer hscore_transfer h_prop_weight h_control_weight
      h_prop_component h_control_component hfunctional hequicontinuity
      hgodambe
  have hcoverage := absoluteWaldCoverage_tendsto_of_input b.coverage_input
  exact ⟨hstudentized.1, hstudentized.2.1, hstudentized.2.2, hcoverage⟩

/--
Retrospective PATT absolute Wald coverage from first-step Z-component
certificates, the fixed-law finite score-adjustment identity, and a compact
local-experiment/Godambe core.
-/
theorem
    retrospective_patt_absoluteWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b :
      RetrospectivePATTEstimatedScoreAbsoluteWaldBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (firstStep : PATTDoubleScoreFirstStepAssembly)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
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
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.studentized_bridge.estimated_bridge.estimated_input) :
    b.studentized_bridge.estimated_bridge.estimated_score_asymptotic_normality ∧
      b.studentized_bridge.estimated_bridge.estimated_score_variance_formula ∧
        TendstoInDistribution
          (fun index sample =>
            b.studentized_bridge.studentization_input.scaledStatistic index sample *
              (standardError
                (b.studentized_bridge.studentization_input.varianceEstimate index sample))⁻¹)
          l
          (fun limitSample =>
            b.studentized_bridge.studentization_input.limit limitSample *
              (standardError b.studentized_bridge.studentization_input.varianceLimit)⁻¹)
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
    retrospective_patt_estimated_score_studentized_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity_and_local_experiment_core
      b.studentized_bridge firstStep parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret propensity control hexact
      hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
      hheterogeneity_variance hresidual_reg hquad hradius_regular
      hradius_geometry hfinite hden horthogonality hfirst_transfer
      hscore_transfer h_prop_weight h_control_weight h_prop_component
      h_control_component core
  have hcoverage := absoluteWaldCoverage_tendsto_of_input b.coverage_input
  exact ⟨hstudentized.1, hstudentized.2.1, hstudentized.2.2, hcoverage⟩

/--
Retrospective PATT absolute Wald coverage from first-step Z-component
certificates, the changing-law finite score-adjustment identity, and a compact
local-experiment/Godambe core.
-/
theorem
    retrospective_patt_absoluteWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b :
      RetrospectivePATTEstimatedScoreAbsoluteWaldBridge Index Sample
        LimitSample sampleLaw limitLaw l)
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
        b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
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
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.studentized_bridge.estimated_bridge.estimated_input) :
    b.studentized_bridge.estimated_bridge.estimated_score_asymptotic_normality ∧
      b.studentized_bridge.estimated_bridge.estimated_score_variance_formula ∧
        TendstoInDistribution
          (fun index sample =>
            b.studentized_bridge.studentization_input.scaledStatistic index sample *
              (standardError
                (b.studentized_bridge.studentization_input.varianceEstimate index sample))⁻¹)
          l
          (fun limitSample =>
            b.studentized_bridge.studentization_input.limit limitSample *
              (standardError b.studentized_bridge.studentization_input.varianceLimit)⁻¹)
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
    retrospective_patt_estimated_score_studentized_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity_and_local_experiment_core
      b.studentized_bridge firstStep parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret
      propensity control hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst_transfer hscore_transfer h_prop_weight h_control_weight
      h_prop_component h_control_component core
  have hcoverage := absoluteWaldCoverage_tendsto_of_input b.coverage_input
  exact ⟨hstudentized.1, hstudentized.2.1, hstudentized.2.2, hcoverage⟩

/--
Retrospective PATT two-sided Wald coverage from first-step Z-component
certificates and the fixed-law finite score-adjustment identity.
-/
theorem
    retrospective_patt_twoSidedWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity
    {Param : Type*}
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b :
      RetrospectivePATTEstimatedScoreTwoSidedWaldBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (firstStep : PATTDoubleScoreFirstStepAssembly)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
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
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity)
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
            b.studentized_bridge.studentization_input.scaledStatistic index sample *
              (standardError
                (b.studentized_bridge.studentization_input.varianceEstimate index sample))⁻¹)
          l
          (fun limitSample =>
            b.studentized_bridge.studentization_input.limit limitSample *
              (standardError b.studentized_bridge.studentization_input.varianceLimit)⁻¹)
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
    retrospective_patt_estimated_score_studentized_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity
      b.studentized_bridge firstStep parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret propensity control hexact
      hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
      hheterogeneity_variance hresidual_reg hquad hradius_regular
      hradius_geometry hfinite hden horthogonality hfirst_transfer
      hscore_transfer h_prop_weight h_control_weight h_prop_component
      h_control_component hfunctional hequicontinuity hgodambe
  have hcoverage := twoSidedWaldCoverage_tendsto_of_input b.coverage_input
  exact ⟨hstudentized.1, hstudentized.2.1, hstudentized.2.2, hcoverage⟩

/--
Retrospective PATT two-sided Wald coverage from first-step Z-component
certificates and the changing-law finite score-adjustment identity.
-/
theorem
    retrospective_patt_twoSidedWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity
    {Param : Type*}
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b :
      RetrospectivePATTEstimatedScoreTwoSidedWaldBridge Index Sample
        LimitSample sampleLaw limitLaw l)
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
        b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
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
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity)
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
            b.studentized_bridge.studentization_input.scaledStatistic index sample *
              (standardError
                (b.studentized_bridge.studentization_input.varianceEstimate index sample))⁻¹)
          l
          (fun limitSample =>
            b.studentized_bridge.studentization_input.limit limitSample *
              (standardError b.studentized_bridge.studentization_input.varianceLimit)⁻¹)
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
    retrospective_patt_estimated_score_studentized_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity
      b.studentized_bridge firstStep parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret
      propensity control hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst_transfer hscore_transfer h_prop_weight h_control_weight
      h_prop_component h_control_component hfunctional hequicontinuity
      hgodambe
  have hcoverage := twoSidedWaldCoverage_tendsto_of_input b.coverage_input
  exact ⟨hstudentized.1, hstudentized.2.1, hstudentized.2.2, hcoverage⟩

/--
Retrospective PATT two-sided Wald coverage from first-step Z-component
certificates, the fixed-law finite score-adjustment identity, and a compact
local-experiment/Godambe core.
-/
theorem
    retrospective_patt_twoSidedWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b :
      RetrospectivePATTEstimatedScoreTwoSidedWaldBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (firstStep : PATTDoubleScoreFirstStepAssembly)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
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
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.studentized_bridge.estimated_bridge.estimated_input) :
    b.studentized_bridge.estimated_bridge.estimated_score_asymptotic_normality ∧
      b.studentized_bridge.estimated_bridge.estimated_score_variance_formula ∧
        TendstoInDistribution
          (fun index sample =>
            b.studentized_bridge.studentization_input.scaledStatistic index sample *
              (standardError
                (b.studentized_bridge.studentization_input.varianceEstimate index sample))⁻¹)
          l
          (fun limitSample =>
            b.studentized_bridge.studentization_input.limit limitSample *
              (standardError b.studentized_bridge.studentization_input.varianceLimit)⁻¹)
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
    retrospective_patt_estimated_score_studentized_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity_and_local_experiment_core
      b.studentized_bridge firstStep parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret propensity control hexact
      hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
      hheterogeneity_variance hresidual_reg hquad hradius_regular
      hradius_geometry hfinite hden horthogonality hfirst_transfer
      hscore_transfer h_prop_weight h_control_weight h_prop_component
      h_control_component core
  have hcoverage := twoSidedWaldCoverage_tendsto_of_input b.coverage_input
  exact ⟨hstudentized.1, hstudentized.2.1, hstudentized.2.2, hcoverage⟩

/--
Retrospective PATT two-sided Wald coverage from first-step Z-component
certificates, the changing-law finite score-adjustment identity, and a compact
local-experiment/Godambe core.
-/
theorem
    retrospective_patt_twoSidedWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b :
      RetrospectivePATTEstimatedScoreTwoSidedWaldBridge Index Sample
        LimitSample sampleLaw limitLaw l)
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
        b.studentized_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
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
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.studentized_bridge.estimated_bridge.estimated_input) :
    b.studentized_bridge.estimated_bridge.estimated_score_asymptotic_normality ∧
      b.studentized_bridge.estimated_bridge.estimated_score_variance_formula ∧
        TendstoInDistribution
          (fun index sample =>
            b.studentized_bridge.studentization_input.scaledStatistic index sample *
              (standardError
                (b.studentized_bridge.studentization_input.varianceEstimate index sample))⁻¹)
          l
          (fun limitSample =>
            b.studentized_bridge.studentization_input.limit limitSample *
              (standardError b.studentized_bridge.studentization_input.varianceLimit)⁻¹)
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
    retrospective_patt_estimated_score_studentized_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity_and_local_experiment_core
      b.studentized_bridge firstStep parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret
      propensity control hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst_transfer hscore_transfer h_prop_weight h_control_weight
      h_prop_component h_control_component core
  have hcoverage := twoSidedWaldCoverage_tendsto_of_input b.coverage_input
  exact ⟨hstudentized.1, hstudentized.2.1, hstudentized.2.2, hcoverage⟩

end WDSM
end Matching
end StatInference
