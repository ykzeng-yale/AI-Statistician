import StatInference.Matching.WDSM.EstimatedScoreAuditScoreAdjustmentRefinement
import StatInference.Matching.WDSM.ProspectivePATEEstimatedScorePositiveVariance
import StatInference.Matching.WDSM.ProspectivePATTEstimatedScorePositiveVariance
import StatInference.Matching.WDSM.RetrospectivePATEEstimatedScorePositiveVariance
import StatInference.Matching.WDSM.RetrospectivePATTEstimatedScorePositiveVariance

/-!
# Positive-variance estimated-score routes with concrete score-adjustment algebra

This module pushes the audited local-experiment score-adjustment refinements
through the positive-variance studentization layer.  The theorems below keep the
paper-specific local-experiment, geometry, residual, and Godambe premises
explicit, but replace direct `score_adjustment_algebra` inputs by fixed-law or
changing-law finite quadratic-form identities plus an interpretation bridge.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open Filter
open scoped Topology

variable {Index Sample LimitSample : Type*}
variable [MeasurableSpace Sample] [MeasurableSpace LimitSample]
variable {sampleLaw : Measure Sample} {limitLaw : Measure LimitSample}
variable [IsProbabilityMeasure sampleLaw] [IsProbabilityMeasure limitLaw]
variable {l : Filter Index} [l.IsCountablyGenerated]

/--
Prospective PATE positive-variance studentized route, with score-adjustment
algebra supplied by the fixed-law finite quadratic-form identity.
-/
theorem
    prospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_fixedLaw_score_adjustment_identity
    {Param : Type*}
    (b :
      ProspectivePATEEstimatedScorePositiveVarianceBridge Index Sample
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
  prospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment
    b hexact hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
    hheterogeneity_variance hresidual_reg hquad hradius_regular
    hradius_geometry hfinite hden horthogonality hfirst hscore hfunctional
    hequicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      b.estimated_bridge.estimated_input.score_adjustment_algebra parameters
      oracleVariance firstStepLoading scoreCovariance hinterpret)
    hgodambe

/--
Prospective PATE positive-variance studentized route, with score-adjustment
algebra supplied by the changing-law finite quadratic-form identity.
-/
theorem
    prospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_changingLaw_score_adjustment_identity
    {Param : Type*}
    (b :
      ProspectivePATEEstimatedScorePositiveVarianceBridge Index Sample
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
  prospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment
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
Prospective PATT positive-variance studentized route, with score-adjustment
algebra supplied by the fixed-law finite quadratic-form identity.
-/
theorem
    prospective_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_fixedLaw_score_adjustment_identity
    {Param : Type*}
    (b :
      ProspectivePATTEstimatedScorePositiveVarianceBridge Index Sample
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
  prospective_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment
    b hexact hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
    hheterogeneity_variance hresidual_reg hquad hradius_regular
    hradius_geometry hfinite hden horthogonality hfirst hscore hfunctional
    hequicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      b.estimated_bridge.estimated_input.score_adjustment_algebra parameters
      oracleVariance firstStepLoading scoreCovariance hinterpret)
    hgodambe

/--
Prospective PATT positive-variance studentized route, with score-adjustment
algebra supplied by the changing-law finite quadratic-form identity.
-/
theorem
    prospective_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_changingLaw_score_adjustment_identity
    {Param : Type*}
    (b :
      ProspectivePATTEstimatedScorePositiveVarianceBridge Index Sample
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
  prospective_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment
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
Retrospective PATE positive-variance studentized route, with score-adjustment
algebra supplied by the fixed-law finite quadratic-form identity.
-/
theorem
    retrospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_fixedLaw_score_adjustment_identity
    {Param : Type*}
    (b :
      RetrospectivePATEEstimatedScorePositiveVarianceBridge Index Sample
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
  retrospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment
    b hexact hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
    hheterogeneity_variance hresidual_reg hquad hradius_regular
    hradius_geometry hfinite hden horthogonality hfirst hscore hfunctional
    hequicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      b.estimated_bridge.estimated_input.score_adjustment_algebra parameters
      oracleVariance firstStepLoading scoreCovariance hinterpret)
    hgodambe

/--
Retrospective PATE positive-variance studentized route, with score-adjustment
algebra supplied by the changing-law finite quadratic-form identity.
-/
theorem
    retrospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_changingLaw_score_adjustment_identity
    {Param : Type*}
    (b :
      RetrospectivePATEEstimatedScorePositiveVarianceBridge Index Sample
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
  retrospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment
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
Retrospective PATT positive-variance studentized route, with score-adjustment
algebra supplied by the fixed-law finite quadratic-form identity.
-/
theorem
    retrospective_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_fixedLaw_score_adjustment_identity
    {Param : Type*}
    (b :
      RetrospectivePATTEstimatedScorePositiveVarianceBridge Index Sample
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
  retrospective_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment
    b hexact hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
    hheterogeneity_variance hresidual_reg hquad hradius_regular
    hradius_geometry hfinite hden horthogonality hfirst hscore hfunctional
    hequicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      b.estimated_bridge.estimated_input.score_adjustment_algebra parameters
      oracleVariance firstStepLoading scoreCovariance hinterpret)
    hgodambe

/--
Retrospective PATT positive-variance studentized route, with score-adjustment
algebra supplied by the changing-law finite quadratic-form identity.
-/
theorem
    retrospective_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_changingLaw_score_adjustment_identity
    {Param : Type*}
    (b :
      RetrospectivePATTEstimatedScorePositiveVarianceBridge Index Sample
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
  retrospective_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment
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
Prospective PATE positive-variance studentized route, with fixed-law
score-adjustment algebra and a compact local-experiment/Godambe core.
-/
theorem
    prospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_fixedLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    (b :
      ProspectivePATEEstimatedScorePositiveVarianceBridge Index Sample
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
  prospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_fixedLaw_score_adjustment_identity
    b parameters oracleVariance firstStepLoading scoreCovariance hinterpret
    hexact hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
    hheterogeneity_variance hresidual_reg hquad hradius_regular
    hradius_geometry hfinite hden horthogonality hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

/--
Prospective PATE positive-variance studentized route, with changing-law
score-adjustment algebra and a compact local-experiment/Godambe core.
-/
theorem
    prospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_changingLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    (b :
      ProspectivePATEEstimatedScorePositiveVarianceBridge Index Sample
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
  prospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_changingLaw_score_adjustment_identity
    b parameters oracleVariance firstStepLoading targetDriftLoading
    scoreCovariance hinterpret hexact hbias_bound hgeometry_regular
    hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
    hquad hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

/--
Prospective PATT positive-variance studentized route, with fixed-law
score-adjustment algebra and a compact local-experiment/Godambe core.
-/
theorem
    prospective_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_fixedLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    (b :
      ProspectivePATTEstimatedScorePositiveVarianceBridge Index Sample
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
  prospective_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_fixedLaw_score_adjustment_identity
    b parameters oracleVariance firstStepLoading scoreCovariance hinterpret
    hexact hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
    hheterogeneity_variance hresidual_reg hquad hradius_regular
    hradius_geometry hfinite hden horthogonality hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

/--
Prospective PATT positive-variance studentized route, with changing-law
score-adjustment algebra and a compact local-experiment/Godambe core.
-/
theorem
    prospective_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_changingLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    (b :
      ProspectivePATTEstimatedScorePositiveVarianceBridge Index Sample
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
  prospective_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_changingLaw_score_adjustment_identity
    b parameters oracleVariance firstStepLoading targetDriftLoading
    scoreCovariance hinterpret hexact hbias_bound hgeometry_regular
    hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
    hquad hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

/--
Retrospective PATE positive-variance studentized route, with fixed-law
score-adjustment algebra and a compact local-experiment/Godambe core.
-/
theorem
    retrospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_fixedLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    (b :
      RetrospectivePATEEstimatedScorePositiveVarianceBridge Index Sample
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
  retrospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_fixedLaw_score_adjustment_identity
    b parameters oracleVariance firstStepLoading scoreCovariance hinterpret
    hexact hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
    hheterogeneity_variance hresidual_reg hquad hradius_regular
    hradius_geometry hfinite hden horthogonality hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

/--
Retrospective PATE positive-variance studentized route, with changing-law
score-adjustment algebra and a compact local-experiment/Godambe core.
-/
theorem
    retrospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_changingLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    (b :
      RetrospectivePATEEstimatedScorePositiveVarianceBridge Index Sample
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
  retrospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_changingLaw_score_adjustment_identity
    b parameters oracleVariance firstStepLoading targetDriftLoading
    scoreCovariance hinterpret hexact hbias_bound hgeometry_regular
    hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
    hquad hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

/--
Retrospective PATT positive-variance studentized route, with fixed-law
score-adjustment algebra and a compact local-experiment/Godambe core.
-/
theorem
    retrospective_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_fixedLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    (b :
      RetrospectivePATTEstimatedScorePositiveVarianceBridge Index Sample
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
  retrospective_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_fixedLaw_score_adjustment_identity
    b parameters oracleVariance firstStepLoading scoreCovariance hinterpret
    hexact hbias_bound hgeometry_regular hcatchment hheterogeneity_moment
    hheterogeneity_variance hresidual_reg hquad hradius_regular
    hradius_geometry hfinite hden horthogonality hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

/--
Retrospective PATT positive-variance studentized route, with changing-law
score-adjustment algebra and a compact local-experiment/Godambe core.
-/
theorem
    retrospective_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_changingLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    (b :
      RetrospectivePATTEstimatedScorePositiveVarianceBridge Index Sample
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
  retrospective_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_changingLaw_score_adjustment_identity
    b parameters oracleVariance firstStepLoading targetDriftLoading
    scoreCovariance hinterpret hexact hbias_bound hgeometry_regular
    hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
    hquad hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

/--
Prospective PATE positive-variance studentized route from first-step
Z-component certificates, with fixed-law score-adjustment algebra and a compact
local-experiment/Godambe core.
-/
theorem
    prospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity_and_local_experiment_core
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
      ProspectivePATEEstimatedScorePositiveVarianceBridge Index Sample
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
  prospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_z_components
    b firstStep propensity treated control hexact hbias_bound
    hgeometry_regular hcatchment hheterogeneity_moment
    hheterogeneity_variance hresidual_reg hquad hradius_regular
    hradius_geometry hfinite hden horthogonality hfirst_transfer
    hscore_transfer h_prop_weight h_treated_weight h_control_weight
    h_prop_component h_treated_component h_control_component
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      b.estimated_bridge.estimated_input.score_adjustment_algebra parameters
      oracleVariance firstStepLoading scoreCovariance hinterpret)
    core.godambe_identity

/--
Prospective PATE positive-variance studentized route from first-step
Z-component certificates, with changing-law score-adjustment algebra and a
compact local-experiment/Godambe core.
-/
theorem
    prospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity_and_local_experiment_core
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
      ProspectivePATEEstimatedScorePositiveVarianceBridge Index Sample
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
  prospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_z_components
    b firstStep propensity treated control hexact hbias_bound
    hgeometry_regular hcatchment hheterogeneity_moment
    hheterogeneity_variance hresidual_reg hquad hradius_regular
    hradius_geometry hfinite hden horthogonality hfirst_transfer
    hscore_transfer h_prop_weight h_treated_weight h_control_weight
    h_prop_component h_treated_component h_control_component
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      b.estimated_bridge.estimated_input.score_adjustment_algebra parameters
      oracleVariance firstStepLoading targetDriftLoading scoreCovariance
      hinterpret)
    core.godambe_identity

/--
Prospective PATT positive-variance studentized route from first-step
Z-component certificates, with fixed-law score-adjustment algebra and a compact
local-experiment/Godambe core.
-/
theorem
    prospective_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b :
      ProspectivePATTEstimatedScorePositiveVarianceBridge Index Sample
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
  prospective_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_z_components
    b firstStep propensity control hexact hbias_bound hgeometry_regular
    hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
    hquad hradius_regular hradius_geometry hfinite hden horthogonality
    hfirst_transfer hscore_transfer h_prop_weight h_control_weight
    h_prop_component h_control_component core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      b.estimated_bridge.estimated_input.score_adjustment_algebra parameters
      oracleVariance firstStepLoading scoreCovariance hinterpret)
    core.godambe_identity

/--
Prospective PATT positive-variance studentized route from first-step
Z-component certificates, with changing-law score-adjustment algebra and a
compact local-experiment/Godambe core.
-/
theorem
    prospective_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity_and_local_experiment_core
    {Param : Type*}
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b :
      ProspectivePATTEstimatedScorePositiveVarianceBridge Index Sample
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
  prospective_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_z_components
    b firstStep propensity control hexact hbias_bound hgeometry_regular
    hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
    hquad hradius_regular hradius_geometry hfinite hden horthogonality
    hfirst_transfer hscore_transfer h_prop_weight h_control_weight
    h_prop_component h_control_component core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      b.estimated_bridge.estimated_input.score_adjustment_algebra parameters
      oracleVariance firstStepLoading targetDriftLoading scoreCovariance
      hinterpret)
    core.godambe_identity

end WDSM
end Matching
end StatInference
