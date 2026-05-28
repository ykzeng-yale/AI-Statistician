import StatInference.Matching.WDSM.EstimatedScorePairedPositiveVarianceScoreAdjustmentRefinement

/-!
# Paired positive-variance Wald coverage with concrete score-adjustment algebra

This module pushes the fixed-law and changing-law score-adjustment refinements
through paired positive-variance Wald coverage routes.  The coverage
calibration premises remain explicit; the theorem wrappers only replace the two
direct `score_adjustment_algebra` inputs by finite quadratic-form identities
plus arm-specific interpretation bridges.
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
Prospective paired PATE/PATT absolute positive-variance Wald coverage, with
both score-adjustment algebra premises supplied by fixed-law finite
quadratic-form identities.
-/
theorem
    prospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identities
    {PATEParam PATTParam : Type*}
    (bPATE :
      ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (pateParameters : Finset PATEParam) (pateOracleVariance : Real)
    (pateFirstStepLoading : PATEParam -> Real)
    (pateScoreCovariance : PATEParam -> PATEParam -> Real)
    (hpate_interpret :
      fixedLawScoreAdjustedVariance pateParameters pateOracleVariance
          pateFirstStepLoading pateScoreCovariance =
        pateOracleVariance -
          scoreQuadraticForm pateParameters pateFirstStepLoading
            pateScoreCovariance ->
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattScoreCovariance =
        pattOracleVariance -
          scoreQuadraticForm pattParameters pattFirstStepLoading
            pattScoreCovariance ->
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hPATT_godambe :
      bPATT.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATE ∧
      ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATT :=
  prospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score
    bPATE bPATT hPATE_exact hPATE_bias_bound hPATE_geometry_regular
    hPATE_catchment hPATE_heterogeneity_moment hPATE_heterogeneity_variance
    hPATE_residual_reg hPATE_quad hPATE_radius_regular
    hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
    hPATE_first hPATE_score hPATE_functional hPATE_equicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
      pateParameters pateOracleVariance pateFirstStepLoading
      pateScoreCovariance hpate_interpret)
    hPATE_godambe hPATT_exact hPATT_bias_bound hPATT_geometry_regular
    hPATT_catchment hPATT_heterogeneity_moment hPATT_heterogeneity_variance
    hPATT_residual_reg hPATT_quad hPATT_radius_regular
    hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
    hPATT_first hPATT_score hPATT_functional hPATT_equicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
      pattParameters pattOracleVariance pattFirstStepLoading
      pattScoreCovariance hpatt_interpret)
    hPATT_godambe

/--
Prospective paired PATE/PATT absolute positive-variance Wald coverage, with
both score-adjustment algebra premises supplied by changing-law finite
quadratic-form identities.
-/
theorem
    prospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identities
    {PATEParam PATTParam : Type*}
    (bPATE :
      ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
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
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hPATT_godambe :
      bPATT.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATE ∧
      ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATT :=
  prospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score
    bPATE bPATT hPATE_exact hPATE_bias_bound hPATE_geometry_regular
    hPATE_catchment hPATE_heterogeneity_moment hPATE_heterogeneity_variance
    hPATE_residual_reg hPATE_quad hPATE_radius_regular
    hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
    hPATE_first hPATE_score hPATE_functional hPATE_equicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
      pateParameters pateOracleVariance pateFirstStepLoading
      pateTargetDriftLoading pateScoreCovariance hpate_interpret)
    hPATE_godambe hPATT_exact hPATT_bias_bound hPATT_geometry_regular
    hPATT_catchment hPATT_heterogeneity_moment hPATT_heterogeneity_variance
    hPATT_residual_reg hPATT_quad hPATT_radius_regular
    hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
    hPATT_first hPATT_score hPATT_functional hPATT_equicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
      pattParameters pattOracleVariance pattFirstStepLoading
      pattTargetDriftLoading pattScoreCovariance hpatt_interpret)
    hPATT_godambe

/--
Prospective paired PATE/PATT two-sided positive-variance Wald coverage, with
both score-adjustment algebra premises supplied by fixed-law finite
quadratic-form identities.
-/
theorem
    prospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identities
    {PATEParam PATTParam : Type*}
    (bPATE :
      ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (pateParameters : Finset PATEParam) (pateOracleVariance : Real)
    (pateFirstStepLoading : PATEParam -> Real)
    (pateScoreCovariance : PATEParam -> PATEParam -> Real)
    (hpate_interpret :
      fixedLawScoreAdjustedVariance pateParameters pateOracleVariance
          pateFirstStepLoading pateScoreCovariance =
        pateOracleVariance -
          scoreQuadraticForm pateParameters pateFirstStepLoading
            pateScoreCovariance ->
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattScoreCovariance =
        pattOracleVariance -
          scoreQuadraticForm pattParameters pattFirstStepLoading
            pattScoreCovariance ->
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hPATT_godambe :
      bPATT.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATE ∧
      ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATT :=
  prospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score
    bPATE bPATT hPATE_exact hPATE_bias_bound hPATE_geometry_regular
    hPATE_catchment hPATE_heterogeneity_moment hPATE_heterogeneity_variance
    hPATE_residual_reg hPATE_quad hPATE_radius_regular
    hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
    hPATE_first hPATE_score hPATE_functional hPATE_equicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
      pateParameters pateOracleVariance pateFirstStepLoading
      pateScoreCovariance hpate_interpret)
    hPATE_godambe hPATT_exact hPATT_bias_bound hPATT_geometry_regular
    hPATT_catchment hPATT_heterogeneity_moment hPATT_heterogeneity_variance
    hPATT_residual_reg hPATT_quad hPATT_radius_regular
    hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
    hPATT_first hPATT_score hPATT_functional hPATT_equicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
      pattParameters pattOracleVariance pattFirstStepLoading
      pattScoreCovariance hpatt_interpret)
    hPATT_godambe

/--
Prospective paired PATE/PATT two-sided positive-variance Wald coverage, with
both score-adjustment algebra premises supplied by changing-law finite
quadratic-form identities.
-/
theorem
    prospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identities
    {PATEParam PATTParam : Type*}
    (bPATE :
      ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
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
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hPATT_godambe :
      bPATT.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATE ∧
      ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATT :=
  prospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score
    bPATE bPATT hPATE_exact hPATE_bias_bound hPATE_geometry_regular
    hPATE_catchment hPATE_heterogeneity_moment hPATE_heterogeneity_variance
    hPATE_residual_reg hPATE_quad hPATE_radius_regular
    hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
    hPATE_first hPATE_score hPATE_functional hPATE_equicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
      pateParameters pateOracleVariance pateFirstStepLoading
      pateTargetDriftLoading pateScoreCovariance hpate_interpret)
    hPATE_godambe hPATT_exact hPATT_bias_bound hPATT_geometry_regular
    hPATT_catchment hPATT_heterogeneity_moment hPATT_heterogeneity_variance
    hPATT_residual_reg hPATT_quad hPATT_radius_regular
    hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
    hPATT_first hPATT_score hPATT_functional hPATT_equicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
      pattParameters pattOracleVariance pattFirstStepLoading
      pattTargetDriftLoading pattScoreCovariance hpatt_interpret)
    hPATT_godambe

/--
Prospective paired PATE/PATT absolute positive-variance Wald coverage, with
fixed-law score-adjustment algebra and compact local-experiment/Godambe cores.
-/
theorem
    prospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identities_and_local_experiment_cores
    {PATEParam PATTParam : Type*}
    (bPATE :
      ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (pateParameters : Finset PATEParam) (pateOracleVariance : Real)
    (pateFirstStepLoading : PATEParam -> Real)
    (pateScoreCovariance : PATEParam -> PATEParam -> Real)
    (hpate_interpret :
      fixedLawScoreAdjustedVariance pateParameters pateOracleVariance
          pateFirstStepLoading pateScoreCovariance =
        pateOracleVariance -
          scoreQuadraticForm pateParameters pateFirstStepLoading
            pateScoreCovariance ->
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattScoreCovariance =
        pattOracleVariance -
          scoreQuadraticForm pattParameters pattFirstStepLoading
            pattScoreCovariance ->
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hPATT_core :
      EstimatedScoreLocalExperimentVarianceCore
        bPATT.positive_bridge.estimated_bridge.estimated_input) :
    ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATE ∧
      ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATT :=
  prospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identities
    bPATE bPATT pateParameters pateOracleVariance pateFirstStepLoading
    pateScoreCovariance hpate_interpret pattParameters pattOracleVariance
    pattFirstStepLoading pattScoreCovariance hpatt_interpret hPATE_exact
    hPATE_bias_bound hPATE_geometry_regular hPATE_catchment
    hPATE_heterogeneity_moment hPATE_heterogeneity_variance
    hPATE_residual_reg hPATE_quad hPATE_radius_regular
    hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
    hPATE_first hPATE_score hPATE_core.matching_functional_local_derivative
    hPATE_core.local_stochastic_equicontinuity hPATE_core.godambe_identity
    hPATT_exact hPATT_bias_bound hPATT_geometry_regular hPATT_catchment
    hPATT_heterogeneity_moment hPATT_heterogeneity_variance
    hPATT_residual_reg hPATT_quad hPATT_radius_regular
    hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
    hPATT_first hPATT_score hPATT_core.matching_functional_local_derivative
    hPATT_core.local_stochastic_equicontinuity hPATT_core.godambe_identity

/--
Prospective paired PATE/PATT absolute positive-variance Wald coverage, with
changing-law score-adjustment algebra and compact local-experiment/Godambe
cores.
-/
theorem
    prospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identities_and_local_experiment_cores
    {PATEParam PATTParam : Type*}
    (bPATE :
      ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
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
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hPATT_core :
      EstimatedScoreLocalExperimentVarianceCore
        bPATT.positive_bridge.estimated_bridge.estimated_input) :
    ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATE ∧
      ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATT :=
  prospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identities
    bPATE bPATT pateParameters pateOracleVariance pateFirstStepLoading
    pateTargetDriftLoading pateScoreCovariance hpate_interpret
    pattParameters pattOracleVariance pattFirstStepLoading
    pattTargetDriftLoading pattScoreCovariance hpatt_interpret hPATE_exact
    hPATE_bias_bound hPATE_geometry_regular hPATE_catchment
    hPATE_heterogeneity_moment hPATE_heterogeneity_variance
    hPATE_residual_reg hPATE_quad hPATE_radius_regular
    hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
    hPATE_first hPATE_score hPATE_core.matching_functional_local_derivative
    hPATE_core.local_stochastic_equicontinuity hPATE_core.godambe_identity
    hPATT_exact hPATT_bias_bound hPATT_geometry_regular hPATT_catchment
    hPATT_heterogeneity_moment hPATT_heterogeneity_variance
    hPATT_residual_reg hPATT_quad hPATT_radius_regular
    hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
    hPATT_first hPATT_score hPATT_core.matching_functional_local_derivative
    hPATT_core.local_stochastic_equicontinuity hPATT_core.godambe_identity

/--
Prospective paired PATE/PATT two-sided positive-variance Wald coverage, with
fixed-law score-adjustment algebra and compact local-experiment/Godambe cores.
-/
theorem
    prospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identities_and_local_experiment_cores
    {PATEParam PATTParam : Type*}
    (bPATE :
      ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (pateParameters : Finset PATEParam) (pateOracleVariance : Real)
    (pateFirstStepLoading : PATEParam -> Real)
    (pateScoreCovariance : PATEParam -> PATEParam -> Real)
    (hpate_interpret :
      fixedLawScoreAdjustedVariance pateParameters pateOracleVariance
          pateFirstStepLoading pateScoreCovariance =
        pateOracleVariance -
          scoreQuadraticForm pateParameters pateFirstStepLoading
            pateScoreCovariance ->
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattScoreCovariance =
        pattOracleVariance -
          scoreQuadraticForm pattParameters pattFirstStepLoading
            pattScoreCovariance ->
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hPATT_core :
      EstimatedScoreLocalExperimentVarianceCore
        bPATT.positive_bridge.estimated_bridge.estimated_input) :
    ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATE ∧
      ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATT :=
  prospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identities
    bPATE bPATT pateParameters pateOracleVariance pateFirstStepLoading
    pateScoreCovariance hpate_interpret pattParameters pattOracleVariance
    pattFirstStepLoading pattScoreCovariance hpatt_interpret hPATE_exact
    hPATE_bias_bound hPATE_geometry_regular hPATE_catchment
    hPATE_heterogeneity_moment hPATE_heterogeneity_variance
    hPATE_residual_reg hPATE_quad hPATE_radius_regular
    hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
    hPATE_first hPATE_score hPATE_core.matching_functional_local_derivative
    hPATE_core.local_stochastic_equicontinuity hPATE_core.godambe_identity
    hPATT_exact hPATT_bias_bound hPATT_geometry_regular hPATT_catchment
    hPATT_heterogeneity_moment hPATT_heterogeneity_variance
    hPATT_residual_reg hPATT_quad hPATT_radius_regular
    hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
    hPATT_first hPATT_score hPATT_core.matching_functional_local_derivative
    hPATT_core.local_stochastic_equicontinuity hPATT_core.godambe_identity

/--
Prospective paired PATE/PATT two-sided positive-variance Wald coverage, with
changing-law score-adjustment algebra and compact local-experiment/Godambe
cores.
-/
theorem
    prospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identities_and_local_experiment_cores
    {PATEParam PATTParam : Type*}
    (bPATE :
      ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
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
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hPATT_core :
      EstimatedScoreLocalExperimentVarianceCore
        bPATT.positive_bridge.estimated_bridge.estimated_input) :
    ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATE ∧
      ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATT :=
  prospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identities
    bPATE bPATT pateParameters pateOracleVariance pateFirstStepLoading
    pateTargetDriftLoading pateScoreCovariance hpate_interpret
    pattParameters pattOracleVariance pattFirstStepLoading
    pattTargetDriftLoading pattScoreCovariance hpatt_interpret hPATE_exact
    hPATE_bias_bound hPATE_geometry_regular hPATE_catchment
    hPATE_heterogeneity_moment hPATE_heterogeneity_variance
    hPATE_residual_reg hPATE_quad hPATE_radius_regular
    hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
    hPATE_first hPATE_score hPATE_core.matching_functional_local_derivative
    hPATE_core.local_stochastic_equicontinuity hPATE_core.godambe_identity
    hPATT_exact hPATT_bias_bound hPATT_geometry_regular hPATT_catchment
    hPATT_heterogeneity_moment hPATT_heterogeneity_variance
    hPATT_residual_reg hPATT_quad hPATT_radius_regular
    hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
    hPATT_first hPATT_score hPATT_core.matching_functional_local_derivative
    hPATT_core.local_stochastic_equicontinuity hPATT_core.godambe_identity

/--
Retrospective paired PATE/PATT absolute positive-variance Wald coverage, with
both score-adjustment algebra premises supplied by fixed-law finite
quadratic-form identities.
-/
theorem
    retrospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identities
    {PATEParam PATTParam : Type*}
    (bPATE :
      RetrospectivePATEEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      RetrospectivePATTEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (pateParameters : Finset PATEParam) (pateOracleVariance : Real)
    (pateFirstStepLoading : PATEParam -> Real)
    (pateScoreCovariance : PATEParam -> PATEParam -> Real)
    (hpate_interpret :
      fixedLawScoreAdjustedVariance pateParameters pateOracleVariance
          pateFirstStepLoading pateScoreCovariance =
        pateOracleVariance -
          scoreQuadraticForm pateParameters pateFirstStepLoading
            pateScoreCovariance ->
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattScoreCovariance =
        pattOracleVariance -
          scoreQuadraticForm pattParameters pattFirstStepLoading
            pattScoreCovariance ->
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hPATT_godambe :
      bPATT.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    RetrospectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATE ∧
      RetrospectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATT :=
  retrospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score
    bPATE bPATT hPATE_exact hPATE_bias_bound hPATE_geometry_regular
    hPATE_catchment hPATE_heterogeneity_moment hPATE_heterogeneity_variance
    hPATE_residual_reg hPATE_quad hPATE_radius_regular
    hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
    hPATE_first hPATE_score hPATE_functional hPATE_equicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
      pateParameters pateOracleVariance pateFirstStepLoading
      pateScoreCovariance hpate_interpret)
    hPATE_godambe hPATT_exact hPATT_bias_bound hPATT_geometry_regular
    hPATT_catchment hPATT_heterogeneity_moment hPATT_heterogeneity_variance
    hPATT_residual_reg hPATT_quad hPATT_radius_regular
    hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
    hPATT_first hPATT_score hPATT_functional hPATT_equicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
      pattParameters pattOracleVariance pattFirstStepLoading
      pattScoreCovariance hpatt_interpret)
    hPATT_godambe

/--
Retrospective paired PATE/PATT absolute positive-variance Wald coverage, with
both score-adjustment algebra premises supplied by changing-law finite
quadratic-form identities.
-/
theorem
    retrospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identities
    {PATEParam PATTParam : Type*}
    (bPATE :
      RetrospectivePATEEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      RetrospectivePATTEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
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
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hPATT_godambe :
      bPATT.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    RetrospectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATE ∧
      RetrospectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATT :=
  retrospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score
    bPATE bPATT hPATE_exact hPATE_bias_bound hPATE_geometry_regular
    hPATE_catchment hPATE_heterogeneity_moment hPATE_heterogeneity_variance
    hPATE_residual_reg hPATE_quad hPATE_radius_regular
    hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
    hPATE_first hPATE_score hPATE_functional hPATE_equicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
      pateParameters pateOracleVariance pateFirstStepLoading
      pateTargetDriftLoading pateScoreCovariance hpate_interpret)
    hPATE_godambe hPATT_exact hPATT_bias_bound hPATT_geometry_regular
    hPATT_catchment hPATT_heterogeneity_moment hPATT_heterogeneity_variance
    hPATT_residual_reg hPATT_quad hPATT_radius_regular
    hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
    hPATT_first hPATT_score hPATT_functional hPATT_equicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
      pattParameters pattOracleVariance pattFirstStepLoading
      pattTargetDriftLoading pattScoreCovariance hpatt_interpret)
    hPATT_godambe

/--
Retrospective paired PATE/PATT two-sided positive-variance Wald coverage, with
both score-adjustment algebra premises supplied by fixed-law finite
quadratic-form identities.
-/
theorem
    retrospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identities
    {PATEParam PATTParam : Type*}
    (bPATE :
      RetrospectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      RetrospectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (pateParameters : Finset PATEParam) (pateOracleVariance : Real)
    (pateFirstStepLoading : PATEParam -> Real)
    (pateScoreCovariance : PATEParam -> PATEParam -> Real)
    (hpate_interpret :
      fixedLawScoreAdjustedVariance pateParameters pateOracleVariance
          pateFirstStepLoading pateScoreCovariance =
        pateOracleVariance -
          scoreQuadraticForm pateParameters pateFirstStepLoading
            pateScoreCovariance ->
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattScoreCovariance =
        pattOracleVariance -
          scoreQuadraticForm pattParameters pattFirstStepLoading
            pattScoreCovariance ->
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hPATT_godambe :
      bPATT.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    RetrospectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATE ∧
      RetrospectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATT :=
  retrospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score
    bPATE bPATT hPATE_exact hPATE_bias_bound hPATE_geometry_regular
    hPATE_catchment hPATE_heterogeneity_moment hPATE_heterogeneity_variance
    hPATE_residual_reg hPATE_quad hPATE_radius_regular
    hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
    hPATE_first hPATE_score hPATE_functional hPATE_equicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
      pateParameters pateOracleVariance pateFirstStepLoading
      pateScoreCovariance hpate_interpret)
    hPATE_godambe hPATT_exact hPATT_bias_bound hPATT_geometry_regular
    hPATT_catchment hPATT_heterogeneity_moment hPATT_heterogeneity_variance
    hPATT_residual_reg hPATT_quad hPATT_radius_regular
    hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
    hPATT_first hPATT_score hPATT_functional hPATT_equicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
      pattParameters pattOracleVariance pattFirstStepLoading
      pattScoreCovariance hpatt_interpret)
    hPATT_godambe

/--
Retrospective paired PATE/PATT two-sided positive-variance Wald coverage, with
both score-adjustment algebra premises supplied by changing-law finite
quadratic-form identities.
-/
theorem
    retrospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identities
    {PATEParam PATTParam : Type*}
    (bPATE :
      RetrospectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      RetrospectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
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
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hPATT_godambe :
      bPATT.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    RetrospectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATE ∧
      RetrospectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATT :=
  retrospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score
    bPATE bPATT hPATE_exact hPATE_bias_bound hPATE_geometry_regular
    hPATE_catchment hPATE_heterogeneity_moment hPATE_heterogeneity_variance
    hPATE_residual_reg hPATE_quad hPATE_radius_regular
    hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
    hPATE_first hPATE_score hPATE_functional hPATE_equicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
      pateParameters pateOracleVariance pateFirstStepLoading
      pateTargetDriftLoading pateScoreCovariance hpate_interpret)
    hPATE_godambe hPATT_exact hPATT_bias_bound hPATT_geometry_regular
    hPATT_catchment hPATT_heterogeneity_moment hPATT_heterogeneity_variance
    hPATT_residual_reg hPATT_quad hPATT_radius_regular
    hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
    hPATT_first hPATT_score hPATT_functional hPATT_equicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
      pattParameters pattOracleVariance pattFirstStepLoading
      pattTargetDriftLoading pattScoreCovariance hpatt_interpret)
    hPATT_godambe

/--
Retrospective paired PATE/PATT absolute positive-variance Wald coverage, with
fixed-law score-adjustment algebra and compact local-experiment/Godambe cores.
-/
theorem
    retrospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identities_and_local_experiment_cores
    {PATEParam PATTParam : Type*}
    (bPATE :
      RetrospectivePATEEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      RetrospectivePATTEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (pateParameters : Finset PATEParam) (pateOracleVariance : Real)
    (pateFirstStepLoading : PATEParam -> Real)
    (pateScoreCovariance : PATEParam -> PATEParam -> Real)
    (hpate_interpret :
      fixedLawScoreAdjustedVariance pateParameters pateOracleVariance
          pateFirstStepLoading pateScoreCovariance =
        pateOracleVariance -
          scoreQuadraticForm pateParameters pateFirstStepLoading
            pateScoreCovariance ->
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattScoreCovariance =
        pattOracleVariance -
          scoreQuadraticForm pattParameters pattFirstStepLoading
            pattScoreCovariance ->
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hPATT_core :
      EstimatedScoreLocalExperimentVarianceCore
        bPATT.positive_bridge.estimated_bridge.estimated_input) :
    RetrospectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATE ∧
      RetrospectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATT :=
  retrospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identities
    bPATE bPATT pateParameters pateOracleVariance pateFirstStepLoading
    pateScoreCovariance hpate_interpret pattParameters pattOracleVariance
    pattFirstStepLoading pattScoreCovariance hpatt_interpret hPATE_exact
    hPATE_bias_bound hPATE_geometry_regular hPATE_catchment
    hPATE_heterogeneity_moment hPATE_heterogeneity_variance
    hPATE_residual_reg hPATE_quad hPATE_radius_regular
    hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
    hPATE_first hPATE_score hPATE_core.matching_functional_local_derivative
    hPATE_core.local_stochastic_equicontinuity hPATE_core.godambe_identity
    hPATT_exact hPATT_bias_bound hPATT_geometry_regular hPATT_catchment
    hPATT_heterogeneity_moment hPATT_heterogeneity_variance
    hPATT_residual_reg hPATT_quad hPATT_radius_regular
    hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
    hPATT_first hPATT_score hPATT_core.matching_functional_local_derivative
    hPATT_core.local_stochastic_equicontinuity hPATT_core.godambe_identity

/--
Retrospective paired PATE/PATT absolute positive-variance Wald coverage, with
changing-law score-adjustment algebra and compact local-experiment/Godambe
cores.
-/
theorem
    retrospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identities_and_local_experiment_cores
    {PATEParam PATTParam : Type*}
    (bPATE :
      RetrospectivePATEEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      RetrospectivePATTEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
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
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hPATT_core :
      EstimatedScoreLocalExperimentVarianceCore
        bPATT.positive_bridge.estimated_bridge.estimated_input) :
    RetrospectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATE ∧
      RetrospectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATT :=
  retrospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identities
    bPATE bPATT pateParameters pateOracleVariance pateFirstStepLoading
    pateTargetDriftLoading pateScoreCovariance hpate_interpret
    pattParameters pattOracleVariance pattFirstStepLoading
    pattTargetDriftLoading pattScoreCovariance hpatt_interpret hPATE_exact
    hPATE_bias_bound hPATE_geometry_regular hPATE_catchment
    hPATE_heterogeneity_moment hPATE_heterogeneity_variance
    hPATE_residual_reg hPATE_quad hPATE_radius_regular
    hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
    hPATE_first hPATE_score hPATE_core.matching_functional_local_derivative
    hPATE_core.local_stochastic_equicontinuity hPATE_core.godambe_identity
    hPATT_exact hPATT_bias_bound hPATT_geometry_regular hPATT_catchment
    hPATT_heterogeneity_moment hPATT_heterogeneity_variance
    hPATT_residual_reg hPATT_quad hPATT_radius_regular
    hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
    hPATT_first hPATT_score hPATT_core.matching_functional_local_derivative
    hPATT_core.local_stochastic_equicontinuity hPATT_core.godambe_identity

/--
Retrospective paired PATE/PATT two-sided positive-variance Wald coverage, with
fixed-law score-adjustment algebra and compact local-experiment/Godambe cores.
-/
theorem
    retrospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identities_and_local_experiment_cores
    {PATEParam PATTParam : Type*}
    (bPATE :
      RetrospectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      RetrospectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (pateParameters : Finset PATEParam) (pateOracleVariance : Real)
    (pateFirstStepLoading : PATEParam -> Real)
    (pateScoreCovariance : PATEParam -> PATEParam -> Real)
    (hpate_interpret :
      fixedLawScoreAdjustedVariance pateParameters pateOracleVariance
          pateFirstStepLoading pateScoreCovariance =
        pateOracleVariance -
          scoreQuadraticForm pateParameters pateFirstStepLoading
            pateScoreCovariance ->
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattScoreCovariance =
        pattOracleVariance -
          scoreQuadraticForm pattParameters pattFirstStepLoading
            pattScoreCovariance ->
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hPATT_core :
      EstimatedScoreLocalExperimentVarianceCore
        bPATT.positive_bridge.estimated_bridge.estimated_input) :
    RetrospectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATE ∧
      RetrospectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATT :=
  retrospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identities
    bPATE bPATT pateParameters pateOracleVariance pateFirstStepLoading
    pateScoreCovariance hpate_interpret pattParameters pattOracleVariance
    pattFirstStepLoading pattScoreCovariance hpatt_interpret hPATE_exact
    hPATE_bias_bound hPATE_geometry_regular hPATE_catchment
    hPATE_heterogeneity_moment hPATE_heterogeneity_variance
    hPATE_residual_reg hPATE_quad hPATE_radius_regular
    hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
    hPATE_first hPATE_score hPATE_core.matching_functional_local_derivative
    hPATE_core.local_stochastic_equicontinuity hPATE_core.godambe_identity
    hPATT_exact hPATT_bias_bound hPATT_geometry_regular hPATT_catchment
    hPATT_heterogeneity_moment hPATT_heterogeneity_variance
    hPATT_residual_reg hPATT_quad hPATT_radius_regular
    hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
    hPATT_first hPATT_score hPATT_core.matching_functional_local_derivative
    hPATT_core.local_stochastic_equicontinuity hPATT_core.godambe_identity

/--
Retrospective paired PATE/PATT two-sided positive-variance Wald coverage, with
changing-law score-adjustment algebra and compact local-experiment/Godambe
cores.
-/
theorem
    retrospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identities_and_local_experiment_cores
    {PATEParam PATTParam : Type*}
    (bPATE :
      RetrospectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      RetrospectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
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
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hPATT_core :
      EstimatedScoreLocalExperimentVarianceCore
        bPATT.positive_bridge.estimated_bridge.estimated_input) :
    RetrospectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATE ∧
      RetrospectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATT :=
  retrospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identities
    bPATE bPATT pateParameters pateOracleVariance pateFirstStepLoading
    pateTargetDriftLoading pateScoreCovariance hpate_interpret
    pattParameters pattOracleVariance pattFirstStepLoading
    pattTargetDriftLoading pattScoreCovariance hpatt_interpret hPATE_exact
    hPATE_bias_bound hPATE_geometry_regular hPATE_catchment
    hPATE_heterogeneity_moment hPATE_heterogeneity_variance
    hPATE_residual_reg hPATE_quad hPATE_radius_regular
    hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
    hPATE_first hPATE_score hPATE_core.matching_functional_local_derivative
    hPATE_core.local_stochastic_equicontinuity hPATE_core.godambe_identity
    hPATT_exact hPATT_bias_bound hPATT_geometry_regular hPATT_catchment
    hPATT_heterogeneity_moment hPATT_heterogeneity_variance
    hPATT_residual_reg hPATT_quad hPATT_radius_regular
    hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
    hPATT_first hPATT_score hPATT_core.matching_functional_local_derivative
    hPATT_core.local_stochastic_equicontinuity hPATT_core.godambe_identity

/--
Prospective paired PATE/PATT absolute positive-variance Wald coverage from
first-step Z-estimator component certificates, with both score-adjustment
algebra premises supplied by fixed-law finite quadratic-form identities.
-/
theorem
    prospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identities
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
    (bPATE :
      ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
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
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattScoreCovariance =
        pattOracleVariance -
          scoreQuadraticForm pattParameters pattFirstStepLoading
            pattScoreCovariance ->
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hPATT_godambe :
      bPATT.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATE ∧
      ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATT := by
  have hPATE_first_score :=
    estimated_score_local_experiment_variance_input_first_step_and_score_local_of_pate_z_components
      pateFirstStep bPATE.positive_bridge.estimated_bridge.estimated_input
      patePropensity pateTreated pateControl hPATE_first_transfer
      hPATE_score_transfer hPATE_prop_weight hPATE_treated_weight
      hPATE_control_weight hPATE_prop_component hPATE_treated_component
      hPATE_control_component
  have hPATT_first_score :=
    estimated_score_local_experiment_variance_input_first_step_and_score_local_of_patt_z_components
      pattFirstStep bPATT.positive_bridge.estimated_bridge.estimated_input
      pattPropensity pattControl hPATT_first_transfer hPATT_score_transfer
      hPATT_prop_weight hPATT_control_weight hPATT_prop_component
      hPATT_control_component
  exact
    prospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identities
      bPATE bPATT pateParameters pateOracleVariance pateFirstStepLoading
      pateScoreCovariance hpate_interpret pattParameters pattOracleVariance
      pattFirstStepLoading pattScoreCovariance hpatt_interpret hPATE_exact
      hPATE_bias_bound hPATE_geometry_regular hPATE_catchment
      hPATE_heterogeneity_moment hPATE_heterogeneity_variance
      hPATE_residual_reg hPATE_quad hPATE_radius_regular
      hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
      hPATE_first_score.1 hPATE_first_score.2 hPATE_functional
      hPATE_equicontinuity hPATE_godambe hPATT_exact hPATT_bias_bound
      hPATT_geometry_regular hPATT_catchment hPATT_heterogeneity_moment
      hPATT_heterogeneity_variance hPATT_residual_reg hPATT_quad
      hPATT_radius_regular hPATT_radius_geometry hPATT_finite hPATT_den
      hPATT_orthogonality hPATT_first_score.1 hPATT_first_score.2
      hPATT_functional hPATT_equicontinuity hPATT_godambe

/--
Prospective paired PATE/PATT absolute positive-variance Wald coverage from
first-step Z-estimator component certificates, with fixed-law score-adjustment
algebra and compact local-experiment/Godambe cores.
-/
theorem
    prospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identities_and_local_experiment_cores
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
    (bPATE :
      ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
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
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattScoreCovariance =
        pattOracleVariance -
          scoreQuadraticForm pattParameters pattFirstStepLoading
            pattScoreCovariance ->
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hPATT_core :
      EstimatedScoreLocalExperimentVarianceCore
        bPATT.positive_bridge.estimated_bridge.estimated_input) :
    ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATE ∧
      ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATT := by
  have hPATE_first_score :=
    estimated_score_local_experiment_variance_input_first_step_and_score_local_of_pate_z_components
      pateFirstStep bPATE.positive_bridge.estimated_bridge.estimated_input
      patePropensity pateTreated pateControl hPATE_first_transfer
      hPATE_score_transfer hPATE_prop_weight hPATE_treated_weight
      hPATE_control_weight hPATE_prop_component hPATE_treated_component
      hPATE_control_component
  have hPATT_first_score :=
    estimated_score_local_experiment_variance_input_first_step_and_score_local_of_patt_z_components
      pattFirstStep bPATT.positive_bridge.estimated_bridge.estimated_input
      pattPropensity pattControl hPATT_first_transfer hPATT_score_transfer
      hPATT_prop_weight hPATT_control_weight hPATT_prop_component
      hPATT_control_component
  exact
    prospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identities
      bPATE bPATT pateParameters pateOracleVariance pateFirstStepLoading
      pateScoreCovariance hpate_interpret pattParameters pattOracleVariance
      pattFirstStepLoading pattScoreCovariance hpatt_interpret hPATE_exact
      hPATE_bias_bound hPATE_geometry_regular hPATE_catchment
      hPATE_heterogeneity_moment hPATE_heterogeneity_variance
      hPATE_residual_reg hPATE_quad hPATE_radius_regular
      hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
      hPATE_first_score.1 hPATE_first_score.2
      hPATE_core.matching_functional_local_derivative
      hPATE_core.local_stochastic_equicontinuity hPATE_core.godambe_identity
      hPATT_exact hPATT_bias_bound hPATT_geometry_regular hPATT_catchment
      hPATT_heterogeneity_moment hPATT_heterogeneity_variance
      hPATT_residual_reg hPATT_quad hPATT_radius_regular
      hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
      hPATT_first_score.1 hPATT_first_score.2
      hPATT_core.matching_functional_local_derivative
      hPATT_core.local_stochastic_equicontinuity hPATT_core.godambe_identity

/--
Prospective paired PATE/PATT absolute positive-variance Wald coverage from
first-step Z-estimator component certificates, with both score-adjustment
algebra premises supplied by changing-law finite quadratic-form identities.
-/
theorem
    prospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identities
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
    (bPATE :
      ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
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
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hPATT_godambe :
      bPATT.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATE ∧
      ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATT := by
  have hPATE_first_score :=
    estimated_score_local_experiment_variance_input_first_step_and_score_local_of_pate_z_components
      pateFirstStep bPATE.positive_bridge.estimated_bridge.estimated_input
      patePropensity pateTreated pateControl hPATE_first_transfer
      hPATE_score_transfer hPATE_prop_weight hPATE_treated_weight
      hPATE_control_weight hPATE_prop_component hPATE_treated_component
      hPATE_control_component
  have hPATT_first_score :=
    estimated_score_local_experiment_variance_input_first_step_and_score_local_of_patt_z_components
      pattFirstStep bPATT.positive_bridge.estimated_bridge.estimated_input
      pattPropensity pattControl hPATT_first_transfer hPATT_score_transfer
      hPATT_prop_weight hPATT_control_weight hPATT_prop_component
      hPATT_control_component
  exact
    prospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identities
      bPATE bPATT pateParameters pateOracleVariance pateFirstStepLoading
      pateTargetDriftLoading pateScoreCovariance hpate_interpret
      pattParameters pattOracleVariance pattFirstStepLoading
      pattTargetDriftLoading pattScoreCovariance hpatt_interpret
      hPATE_exact hPATE_bias_bound hPATE_geometry_regular hPATE_catchment
      hPATE_heterogeneity_moment hPATE_heterogeneity_variance
      hPATE_residual_reg hPATE_quad hPATE_radius_regular
      hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
      hPATE_first_score.1 hPATE_first_score.2 hPATE_functional
      hPATE_equicontinuity hPATE_godambe hPATT_exact hPATT_bias_bound
      hPATT_geometry_regular hPATT_catchment hPATT_heterogeneity_moment
      hPATT_heterogeneity_variance hPATT_residual_reg hPATT_quad
      hPATT_radius_regular hPATT_radius_geometry hPATT_finite hPATT_den
      hPATT_orthogonality hPATT_first_score.1 hPATT_first_score.2
      hPATT_functional hPATT_equicontinuity hPATT_godambe

/--
Prospective paired PATE/PATT absolute positive-variance Wald coverage from
first-step Z-estimator component certificates, with changing-law score-adjustment
algebra and compact local-experiment/Godambe cores.
-/
theorem
    prospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identities_and_local_experiment_cores
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
    (bPATE :
      ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
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
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hPATT_core :
      EstimatedScoreLocalExperimentVarianceCore
        bPATT.positive_bridge.estimated_bridge.estimated_input) :
    ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATE ∧
      ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATT := by
  have hPATE_first_score :=
    estimated_score_local_experiment_variance_input_first_step_and_score_local_of_pate_z_components
      pateFirstStep bPATE.positive_bridge.estimated_bridge.estimated_input
      patePropensity pateTreated pateControl hPATE_first_transfer
      hPATE_score_transfer hPATE_prop_weight hPATE_treated_weight
      hPATE_control_weight hPATE_prop_component hPATE_treated_component
      hPATE_control_component
  have hPATT_first_score :=
    estimated_score_local_experiment_variance_input_first_step_and_score_local_of_patt_z_components
      pattFirstStep bPATT.positive_bridge.estimated_bridge.estimated_input
      pattPropensity pattControl hPATT_first_transfer hPATT_score_transfer
      hPATT_prop_weight hPATT_control_weight hPATT_prop_component
      hPATT_control_component
  exact
    prospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identities_and_local_experiment_cores
      bPATE bPATT pateParameters pateOracleVariance pateFirstStepLoading
      pateTargetDriftLoading pateScoreCovariance hpate_interpret
      pattParameters pattOracleVariance pattFirstStepLoading
      pattTargetDriftLoading pattScoreCovariance hpatt_interpret
      hPATE_exact hPATE_bias_bound hPATE_geometry_regular hPATE_catchment
      hPATE_heterogeneity_moment hPATE_heterogeneity_variance
      hPATE_residual_reg hPATE_quad hPATE_radius_regular
      hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
      hPATE_first_score.1 hPATE_first_score.2 hPATE_core hPATT_exact
      hPATT_bias_bound hPATT_geometry_regular hPATT_catchment
      hPATT_heterogeneity_moment hPATT_heterogeneity_variance
      hPATT_residual_reg hPATT_quad hPATT_radius_regular
      hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
      hPATT_first_score.1 hPATT_first_score.2 hPATT_core


/--
Prospective paired PATE/PATT two-sided positive-variance Wald coverage from
first-step Z-estimator component certificates, with both score-adjustment
algebra premises supplied by fixed-law finite quadratic-form identities.
-/
theorem
    prospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identities
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
    (bPATE :
      ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
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
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattScoreCovariance =
        pattOracleVariance -
          scoreQuadraticForm pattParameters pattFirstStepLoading
            pattScoreCovariance ->
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hPATT_godambe :
      bPATT.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATE ∧
      ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATT := by
  have hPATE_first_score :=
    estimated_score_local_experiment_variance_input_first_step_and_score_local_of_pate_z_components
      pateFirstStep bPATE.positive_bridge.estimated_bridge.estimated_input
      patePropensity pateTreated pateControl hPATE_first_transfer
      hPATE_score_transfer hPATE_prop_weight hPATE_treated_weight
      hPATE_control_weight hPATE_prop_component hPATE_treated_component
      hPATE_control_component
  have hPATT_first_score :=
    estimated_score_local_experiment_variance_input_first_step_and_score_local_of_patt_z_components
      pattFirstStep bPATT.positive_bridge.estimated_bridge.estimated_input
      pattPropensity pattControl hPATT_first_transfer hPATT_score_transfer
      hPATT_prop_weight hPATT_control_weight hPATT_prop_component
      hPATT_control_component
  exact
    prospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identities
      bPATE bPATT pateParameters pateOracleVariance pateFirstStepLoading
      pateScoreCovariance hpate_interpret pattParameters pattOracleVariance
      pattFirstStepLoading pattScoreCovariance hpatt_interpret hPATE_exact
      hPATE_bias_bound hPATE_geometry_regular hPATE_catchment
      hPATE_heterogeneity_moment hPATE_heterogeneity_variance
      hPATE_residual_reg hPATE_quad hPATE_radius_regular
      hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
      hPATE_first_score.1 hPATE_first_score.2 hPATE_functional
      hPATE_equicontinuity hPATE_godambe hPATT_exact hPATT_bias_bound
      hPATT_geometry_regular hPATT_catchment hPATT_heterogeneity_moment
      hPATT_heterogeneity_variance hPATT_residual_reg hPATT_quad
      hPATT_radius_regular hPATT_radius_geometry hPATT_finite hPATT_den
      hPATT_orthogonality hPATT_first_score.1 hPATT_first_score.2
      hPATT_functional hPATT_equicontinuity hPATT_godambe

/--
Prospective paired PATE/PATT two-sided positive-variance Wald coverage from
first-step Z-estimator component certificates, with both score-adjustment
algebra premises supplied by changing-law finite quadratic-form identities.
-/
theorem
    prospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identities
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
    (bPATE :
      ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
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
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hPATT_godambe :
      bPATT.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATE ∧
      ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATT := by
  have hPATE_first_score :=
    estimated_score_local_experiment_variance_input_first_step_and_score_local_of_pate_z_components
      pateFirstStep bPATE.positive_bridge.estimated_bridge.estimated_input
      patePropensity pateTreated pateControl hPATE_first_transfer
      hPATE_score_transfer hPATE_prop_weight hPATE_treated_weight
      hPATE_control_weight hPATE_prop_component hPATE_treated_component
      hPATE_control_component
  have hPATT_first_score :=
    estimated_score_local_experiment_variance_input_first_step_and_score_local_of_patt_z_components
      pattFirstStep bPATT.positive_bridge.estimated_bridge.estimated_input
      pattPropensity pattControl hPATT_first_transfer hPATT_score_transfer
      hPATT_prop_weight hPATT_control_weight hPATT_prop_component
      hPATT_control_component
  exact
    prospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identities
      bPATE bPATT pateParameters pateOracleVariance pateFirstStepLoading
      pateTargetDriftLoading pateScoreCovariance hpate_interpret
      pattParameters pattOracleVariance pattFirstStepLoading
      pattTargetDriftLoading pattScoreCovariance hpatt_interpret
      hPATE_exact hPATE_bias_bound hPATE_geometry_regular hPATE_catchment
      hPATE_heterogeneity_moment hPATE_heterogeneity_variance
      hPATE_residual_reg hPATE_quad hPATE_radius_regular
      hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
      hPATE_first_score.1 hPATE_first_score.2 hPATE_functional
      hPATE_equicontinuity hPATE_godambe hPATT_exact hPATT_bias_bound
      hPATT_geometry_regular hPATT_catchment hPATT_heterogeneity_moment
      hPATT_heterogeneity_variance hPATT_residual_reg hPATT_quad
      hPATT_radius_regular hPATT_radius_geometry hPATT_finite hPATT_den
      hPATT_orthogonality hPATT_first_score.1 hPATT_first_score.2
      hPATT_functional hPATT_equicontinuity hPATT_godambe

/--
Prospective paired PATE/PATT two-sided positive-variance Wald coverage from
first-step Z-estimator component certificates, with fixed-law score-adjustment
algebra and compact local-experiment/Godambe cores.
-/
theorem
    prospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identities_and_local_experiment_cores
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
    (bPATE :
      ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
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
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattScoreCovariance =
        pattOracleVariance -
          scoreQuadraticForm pattParameters pattFirstStepLoading
            pattScoreCovariance ->
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hPATT_core :
      EstimatedScoreLocalExperimentVarianceCore
        bPATT.positive_bridge.estimated_bridge.estimated_input) :
    ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATE ∧
      ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATT := by
  have hPATE_first_score :=
    estimated_score_local_experiment_variance_input_first_step_and_score_local_of_pate_z_components
      pateFirstStep bPATE.positive_bridge.estimated_bridge.estimated_input
      patePropensity pateTreated pateControl hPATE_first_transfer
      hPATE_score_transfer hPATE_prop_weight hPATE_treated_weight
      hPATE_control_weight hPATE_prop_component hPATE_treated_component
      hPATE_control_component
  have hPATT_first_score :=
    estimated_score_local_experiment_variance_input_first_step_and_score_local_of_patt_z_components
      pattFirstStep bPATT.positive_bridge.estimated_bridge.estimated_input
      pattPropensity pattControl hPATT_first_transfer hPATT_score_transfer
      hPATT_prop_weight hPATT_control_weight hPATT_prop_component
      hPATT_control_component
  exact
    prospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identities_and_local_experiment_cores
      bPATE bPATT pateParameters pateOracleVariance pateFirstStepLoading
      pateScoreCovariance hpate_interpret pattParameters pattOracleVariance
      pattFirstStepLoading pattScoreCovariance hpatt_interpret hPATE_exact
      hPATE_bias_bound hPATE_geometry_regular hPATE_catchment
      hPATE_heterogeneity_moment hPATE_heterogeneity_variance
      hPATE_residual_reg hPATE_quad hPATE_radius_regular
      hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
      hPATE_first_score.1 hPATE_first_score.2 hPATE_core hPATT_exact
      hPATT_bias_bound hPATT_geometry_regular hPATT_catchment
      hPATT_heterogeneity_moment hPATT_heterogeneity_variance
      hPATT_residual_reg hPATT_quad hPATT_radius_regular
      hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
      hPATT_first_score.1 hPATT_first_score.2 hPATT_core

/--
Prospective paired PATE/PATT two-sided positive-variance Wald coverage from
first-step Z-estimator component certificates, with changing-law score-adjustment
algebra and compact local-experiment/Godambe cores.
-/
theorem
    prospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identities_and_local_experiment_cores
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
    (bPATE :
      ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
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
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hPATT_core :
      EstimatedScoreLocalExperimentVarianceCore
        bPATT.positive_bridge.estimated_bridge.estimated_input) :
    ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATE ∧
      ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATT := by
  have hPATE_first_score :=
    estimated_score_local_experiment_variance_input_first_step_and_score_local_of_pate_z_components
      pateFirstStep bPATE.positive_bridge.estimated_bridge.estimated_input
      patePropensity pateTreated pateControl hPATE_first_transfer
      hPATE_score_transfer hPATE_prop_weight hPATE_treated_weight
      hPATE_control_weight hPATE_prop_component hPATE_treated_component
      hPATE_control_component
  have hPATT_first_score :=
    estimated_score_local_experiment_variance_input_first_step_and_score_local_of_patt_z_components
      pattFirstStep bPATT.positive_bridge.estimated_bridge.estimated_input
      pattPropensity pattControl hPATT_first_transfer hPATT_score_transfer
      hPATT_prop_weight hPATT_control_weight hPATT_prop_component
      hPATT_control_component
  exact
    prospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identities_and_local_experiment_cores
      bPATE bPATT pateParameters pateOracleVariance pateFirstStepLoading
      pateTargetDriftLoading pateScoreCovariance hpate_interpret
      pattParameters pattOracleVariance pattFirstStepLoading
      pattTargetDriftLoading pattScoreCovariance hpatt_interpret
      hPATE_exact hPATE_bias_bound hPATE_geometry_regular hPATE_catchment
      hPATE_heterogeneity_moment hPATE_heterogeneity_variance
      hPATE_residual_reg hPATE_quad hPATE_radius_regular
      hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
      hPATE_first_score.1 hPATE_first_score.2 hPATE_core hPATT_exact
      hPATT_bias_bound hPATT_geometry_regular hPATT_catchment
      hPATT_heterogeneity_moment hPATT_heterogeneity_variance
      hPATT_residual_reg hPATT_quad hPATT_radius_regular
      hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
      hPATT_first_score.1 hPATT_first_score.2 hPATT_core

/--
Retrospective paired PATE/PATT absolute positive-variance Wald coverage from
first-step Z-estimator component certificates, with both score-adjustment
algebra premises supplied by fixed-law finite quadratic-form identities.
-/
theorem
    retrospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identities
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
    (bPATE :
      RetrospectivePATEEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      RetrospectivePATTEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
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
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattScoreCovariance =
        pattOracleVariance -
          scoreQuadraticForm pattParameters pattFirstStepLoading
            pattScoreCovariance ->
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hPATT_godambe :
      bPATT.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    RetrospectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATE ∧
      RetrospectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATT := by
  have hPATE_first_score :=
    estimated_score_local_experiment_variance_input_first_step_and_score_local_of_pate_z_components
      pateFirstStep bPATE.positive_bridge.estimated_bridge.estimated_input
      patePropensity pateTreated pateControl hPATE_first_transfer
      hPATE_score_transfer hPATE_prop_weight hPATE_treated_weight
      hPATE_control_weight hPATE_prop_component hPATE_treated_component
      hPATE_control_component
  have hPATT_first_score :=
    estimated_score_local_experiment_variance_input_first_step_and_score_local_of_patt_z_components
      pattFirstStep bPATT.positive_bridge.estimated_bridge.estimated_input
      pattPropensity pattControl hPATT_first_transfer hPATT_score_transfer
      hPATT_prop_weight hPATT_control_weight hPATT_prop_component
      hPATT_control_component
  exact
    retrospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identities
      bPATE bPATT pateParameters pateOracleVariance pateFirstStepLoading
      pateScoreCovariance hpate_interpret pattParameters pattOracleVariance
      pattFirstStepLoading pattScoreCovariance hpatt_interpret hPATE_exact
      hPATE_bias_bound hPATE_geometry_regular hPATE_catchment
      hPATE_heterogeneity_moment hPATE_heterogeneity_variance
      hPATE_residual_reg hPATE_quad hPATE_radius_regular
      hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
      hPATE_first_score.1 hPATE_first_score.2 hPATE_functional
      hPATE_equicontinuity hPATE_godambe hPATT_exact hPATT_bias_bound
      hPATT_geometry_regular hPATT_catchment hPATT_heterogeneity_moment
      hPATT_heterogeneity_variance hPATT_residual_reg hPATT_quad
      hPATT_radius_regular hPATT_radius_geometry hPATT_finite hPATT_den
      hPATT_orthogonality hPATT_first_score.1 hPATT_first_score.2
      hPATT_functional hPATT_equicontinuity hPATT_godambe

/--
Retrospective paired PATE/PATT absolute positive-variance Wald coverage from
first-step Z-estimator component certificates, with both score-adjustment
algebra premises supplied by changing-law finite quadratic-form identities.
-/
theorem
    retrospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identities
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
    (bPATE :
      RetrospectivePATEEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      RetrospectivePATTEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
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
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hPATT_godambe :
      bPATT.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    RetrospectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATE ∧
      RetrospectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATT := by
  have hPATE_first_score :=
    estimated_score_local_experiment_variance_input_first_step_and_score_local_of_pate_z_components
      pateFirstStep bPATE.positive_bridge.estimated_bridge.estimated_input
      patePropensity pateTreated pateControl hPATE_first_transfer
      hPATE_score_transfer hPATE_prop_weight hPATE_treated_weight
      hPATE_control_weight hPATE_prop_component hPATE_treated_component
      hPATE_control_component
  have hPATT_first_score :=
    estimated_score_local_experiment_variance_input_first_step_and_score_local_of_patt_z_components
      pattFirstStep bPATT.positive_bridge.estimated_bridge.estimated_input
      pattPropensity pattControl hPATT_first_transfer hPATT_score_transfer
      hPATT_prop_weight hPATT_control_weight hPATT_prop_component
      hPATT_control_component
  exact
    retrospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identities
      bPATE bPATT pateParameters pateOracleVariance pateFirstStepLoading
      pateTargetDriftLoading pateScoreCovariance hpate_interpret
      pattParameters pattOracleVariance pattFirstStepLoading
      pattTargetDriftLoading pattScoreCovariance hpatt_interpret
      hPATE_exact hPATE_bias_bound hPATE_geometry_regular hPATE_catchment
      hPATE_heterogeneity_moment hPATE_heterogeneity_variance
      hPATE_residual_reg hPATE_quad hPATE_radius_regular
      hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
      hPATE_first_score.1 hPATE_first_score.2 hPATE_functional
      hPATE_equicontinuity hPATE_godambe hPATT_exact hPATT_bias_bound
      hPATT_geometry_regular hPATT_catchment hPATT_heterogeneity_moment
      hPATT_heterogeneity_variance hPATT_residual_reg hPATT_quad
      hPATT_radius_regular hPATT_radius_geometry hPATT_finite hPATT_den
      hPATT_orthogonality hPATT_first_score.1 hPATT_first_score.2
      hPATT_functional hPATT_equicontinuity hPATT_godambe

/--
Retrospective paired PATE/PATT absolute positive-variance Wald coverage from
first-step Z-estimator component certificates, with fixed-law score-adjustment
algebra and compact local-experiment/Godambe cores.
-/
theorem
    retrospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identities_and_local_experiment_cores
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
    (bPATE :
      RetrospectivePATEEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      RetrospectivePATTEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
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
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattScoreCovariance =
        pattOracleVariance -
          scoreQuadraticForm pattParameters pattFirstStepLoading
            pattScoreCovariance ->
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hPATT_core :
      EstimatedScoreLocalExperimentVarianceCore
        bPATT.positive_bridge.estimated_bridge.estimated_input) :
    RetrospectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATE ∧
      RetrospectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATT := by
  have hPATE_first_score :=
    estimated_score_local_experiment_variance_input_first_step_and_score_local_of_pate_z_components
      pateFirstStep bPATE.positive_bridge.estimated_bridge.estimated_input
      patePropensity pateTreated pateControl hPATE_first_transfer
      hPATE_score_transfer hPATE_prop_weight hPATE_treated_weight
      hPATE_control_weight hPATE_prop_component hPATE_treated_component
      hPATE_control_component
  have hPATT_first_score :=
    estimated_score_local_experiment_variance_input_first_step_and_score_local_of_patt_z_components
      pattFirstStep bPATT.positive_bridge.estimated_bridge.estimated_input
      pattPropensity pattControl hPATT_first_transfer hPATT_score_transfer
      hPATT_prop_weight hPATT_control_weight hPATT_prop_component
      hPATT_control_component
  exact
    retrospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identities_and_local_experiment_cores
      bPATE bPATT pateParameters pateOracleVariance pateFirstStepLoading
      pateScoreCovariance hpate_interpret pattParameters pattOracleVariance
      pattFirstStepLoading pattScoreCovariance hpatt_interpret hPATE_exact
      hPATE_bias_bound hPATE_geometry_regular hPATE_catchment
      hPATE_heterogeneity_moment hPATE_heterogeneity_variance
      hPATE_residual_reg hPATE_quad hPATE_radius_regular
      hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
      hPATE_first_score.1 hPATE_first_score.2 hPATE_core hPATT_exact
      hPATT_bias_bound hPATT_geometry_regular hPATT_catchment
      hPATT_heterogeneity_moment hPATT_heterogeneity_variance
      hPATT_residual_reg hPATT_quad hPATT_radius_regular
      hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
      hPATT_first_score.1 hPATT_first_score.2 hPATT_core

/--
Retrospective paired PATE/PATT absolute positive-variance Wald coverage from
first-step Z-estimator component certificates, with changing-law score-adjustment
algebra and compact local-experiment/Godambe cores.
-/
theorem
    retrospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identities_and_local_experiment_cores
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
    (bPATE :
      RetrospectivePATEEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      RetrospectivePATTEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
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
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hPATT_core :
      EstimatedScoreLocalExperimentVarianceCore
        bPATT.positive_bridge.estimated_bridge.estimated_input) :
    RetrospectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATE ∧
      RetrospectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion bPATT := by
  have hPATE_first_score :=
    estimated_score_local_experiment_variance_input_first_step_and_score_local_of_pate_z_components
      pateFirstStep bPATE.positive_bridge.estimated_bridge.estimated_input
      patePropensity pateTreated pateControl hPATE_first_transfer
      hPATE_score_transfer hPATE_prop_weight hPATE_treated_weight
      hPATE_control_weight hPATE_prop_component hPATE_treated_component
      hPATE_control_component
  have hPATT_first_score :=
    estimated_score_local_experiment_variance_input_first_step_and_score_local_of_patt_z_components
      pattFirstStep bPATT.positive_bridge.estimated_bridge.estimated_input
      pattPropensity pattControl hPATT_first_transfer hPATT_score_transfer
      hPATT_prop_weight hPATT_control_weight hPATT_prop_component
      hPATT_control_component
  exact
    retrospective_pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identities_and_local_experiment_cores
      bPATE bPATT pateParameters pateOracleVariance pateFirstStepLoading
      pateTargetDriftLoading pateScoreCovariance hpate_interpret
      pattParameters pattOracleVariance pattFirstStepLoading
      pattTargetDriftLoading pattScoreCovariance hpatt_interpret
      hPATE_exact hPATE_bias_bound hPATE_geometry_regular hPATE_catchment
      hPATE_heterogeneity_moment hPATE_heterogeneity_variance
      hPATE_residual_reg hPATE_quad hPATE_radius_regular
      hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
      hPATE_first_score.1 hPATE_first_score.2 hPATE_core hPATT_exact
      hPATT_bias_bound hPATT_geometry_regular hPATT_catchment
      hPATT_heterogeneity_moment hPATT_heterogeneity_variance
      hPATT_residual_reg hPATT_quad hPATT_radius_regular
      hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
      hPATT_first_score.1 hPATT_first_score.2 hPATT_core

/--
Retrospective paired PATE/PATT two-sided positive-variance Wald coverage from
first-step Z-estimator component certificates, with both score-adjustment
algebra premises supplied by fixed-law finite quadratic-form identities.
-/
theorem
    retrospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identities
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
    (bPATE :
      RetrospectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      RetrospectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
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
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattScoreCovariance =
        pattOracleVariance -
          scoreQuadraticForm pattParameters pattFirstStepLoading
            pattScoreCovariance ->
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hPATT_godambe :
      bPATT.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    RetrospectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATE ∧
      RetrospectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATT := by
  have hPATE_first_score :=
    estimated_score_local_experiment_variance_input_first_step_and_score_local_of_pate_z_components
      pateFirstStep bPATE.positive_bridge.estimated_bridge.estimated_input
      patePropensity pateTreated pateControl hPATE_first_transfer
      hPATE_score_transfer hPATE_prop_weight hPATE_treated_weight
      hPATE_control_weight hPATE_prop_component hPATE_treated_component
      hPATE_control_component
  have hPATT_first_score :=
    estimated_score_local_experiment_variance_input_first_step_and_score_local_of_patt_z_components
      pattFirstStep bPATT.positive_bridge.estimated_bridge.estimated_input
      pattPropensity pattControl hPATT_first_transfer hPATT_score_transfer
      hPATT_prop_weight hPATT_control_weight hPATT_prop_component
      hPATT_control_component
  exact
    retrospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identities
      bPATE bPATT pateParameters pateOracleVariance pateFirstStepLoading
      pateScoreCovariance hpate_interpret pattParameters pattOracleVariance
      pattFirstStepLoading pattScoreCovariance hpatt_interpret hPATE_exact
      hPATE_bias_bound hPATE_geometry_regular hPATE_catchment
      hPATE_heterogeneity_moment hPATE_heterogeneity_variance
      hPATE_residual_reg hPATE_quad hPATE_radius_regular
      hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
      hPATE_first_score.1 hPATE_first_score.2 hPATE_functional
      hPATE_equicontinuity hPATE_godambe hPATT_exact hPATT_bias_bound
      hPATT_geometry_regular hPATT_catchment hPATT_heterogeneity_moment
      hPATT_heterogeneity_variance hPATT_residual_reg hPATT_quad
      hPATT_radius_regular hPATT_radius_geometry hPATT_finite hPATT_den
      hPATT_orthogonality hPATT_first_score.1 hPATT_first_score.2
      hPATT_functional hPATT_equicontinuity hPATT_godambe

/--
Retrospective paired PATE/PATT two-sided positive-variance Wald coverage from
first-step Z-estimator component certificates, with both score-adjustment
algebra premises supplied by changing-law finite quadratic-form identities.
-/
theorem
    retrospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identities
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
    (bPATE :
      RetrospectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      RetrospectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
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
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hPATT_godambe :
      bPATT.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    RetrospectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATE ∧
      RetrospectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATT := by
  have hPATE_first_score :=
    estimated_score_local_experiment_variance_input_first_step_and_score_local_of_pate_z_components
      pateFirstStep bPATE.positive_bridge.estimated_bridge.estimated_input
      patePropensity pateTreated pateControl hPATE_first_transfer
      hPATE_score_transfer hPATE_prop_weight hPATE_treated_weight
      hPATE_control_weight hPATE_prop_component hPATE_treated_component
      hPATE_control_component
  have hPATT_first_score :=
    estimated_score_local_experiment_variance_input_first_step_and_score_local_of_patt_z_components
      pattFirstStep bPATT.positive_bridge.estimated_bridge.estimated_input
      pattPropensity pattControl hPATT_first_transfer hPATT_score_transfer
      hPATT_prop_weight hPATT_control_weight hPATT_prop_component
      hPATT_control_component
  exact
    retrospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identities
      bPATE bPATT pateParameters pateOracleVariance pateFirstStepLoading
      pateTargetDriftLoading pateScoreCovariance hpate_interpret
      pattParameters pattOracleVariance pattFirstStepLoading
      pattTargetDriftLoading pattScoreCovariance hpatt_interpret
      hPATE_exact hPATE_bias_bound hPATE_geometry_regular hPATE_catchment
      hPATE_heterogeneity_moment hPATE_heterogeneity_variance
      hPATE_residual_reg hPATE_quad hPATE_radius_regular
      hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
      hPATE_first_score.1 hPATE_first_score.2 hPATE_functional
      hPATE_equicontinuity hPATE_godambe hPATT_exact hPATT_bias_bound
      hPATT_geometry_regular hPATT_catchment hPATT_heterogeneity_moment
      hPATT_heterogeneity_variance hPATT_residual_reg hPATT_quad
      hPATT_radius_regular hPATT_radius_geometry hPATT_finite hPATT_den
      hPATT_orthogonality hPATT_first_score.1 hPATT_first_score.2
      hPATT_functional hPATT_equicontinuity hPATT_godambe

/--
Retrospective paired PATE/PATT two-sided positive-variance Wald coverage from
first-step Z-estimator component certificates, with fixed-law score-adjustment
algebra and compact local-experiment/Godambe cores.
-/
theorem
    retrospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identities_and_local_experiment_cores
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
    (bPATE :
      RetrospectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      RetrospectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
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
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattScoreCovariance =
        pattOracleVariance -
          scoreQuadraticForm pattParameters pattFirstStepLoading
            pattScoreCovariance ->
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hPATT_core :
      EstimatedScoreLocalExperimentVarianceCore
        bPATT.positive_bridge.estimated_bridge.estimated_input) :
    RetrospectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATE ∧
      RetrospectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATT := by
  have hPATE_first_score :=
    estimated_score_local_experiment_variance_input_first_step_and_score_local_of_pate_z_components
      pateFirstStep bPATE.positive_bridge.estimated_bridge.estimated_input
      patePropensity pateTreated pateControl hPATE_first_transfer
      hPATE_score_transfer hPATE_prop_weight hPATE_treated_weight
      hPATE_control_weight hPATE_prop_component hPATE_treated_component
      hPATE_control_component
  have hPATT_first_score :=
    estimated_score_local_experiment_variance_input_first_step_and_score_local_of_patt_z_components
      pattFirstStep bPATT.positive_bridge.estimated_bridge.estimated_input
      pattPropensity pattControl hPATT_first_transfer hPATT_score_transfer
      hPATT_prop_weight hPATT_control_weight hPATT_prop_component
      hPATT_control_component
  exact
    retrospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identities_and_local_experiment_cores
      bPATE bPATT pateParameters pateOracleVariance pateFirstStepLoading
      pateScoreCovariance hpate_interpret pattParameters pattOracleVariance
      pattFirstStepLoading pattScoreCovariance hpatt_interpret hPATE_exact
      hPATE_bias_bound hPATE_geometry_regular hPATE_catchment
      hPATE_heterogeneity_moment hPATE_heterogeneity_variance
      hPATE_residual_reg hPATE_quad hPATE_radius_regular
      hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
      hPATE_first_score.1 hPATE_first_score.2 hPATE_core hPATT_exact
      hPATT_bias_bound hPATT_geometry_regular hPATT_catchment
      hPATT_heterogeneity_moment hPATT_heterogeneity_variance
      hPATT_residual_reg hPATT_quad hPATT_radius_regular
      hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
      hPATT_first_score.1 hPATT_first_score.2 hPATT_core

/--
Retrospective paired PATE/PATT two-sided positive-variance Wald coverage from
first-step Z-estimator component certificates, with changing-law score-adjustment
algebra and compact local-experiment/Godambe cores.
-/
theorem
    retrospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identities_and_local_experiment_cores
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
    (bPATE :
      RetrospectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (bPATT :
      RetrospectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
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
        bPATE.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
        bPATT.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
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
    (hPATT_core :
      EstimatedScoreLocalExperimentVarianceCore
        bPATT.positive_bridge.estimated_bridge.estimated_input) :
    RetrospectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATE ∧
      RetrospectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion bPATT := by
  have hPATE_first_score :=
    estimated_score_local_experiment_variance_input_first_step_and_score_local_of_pate_z_components
      pateFirstStep bPATE.positive_bridge.estimated_bridge.estimated_input
      patePropensity pateTreated pateControl hPATE_first_transfer
      hPATE_score_transfer hPATE_prop_weight hPATE_treated_weight
      hPATE_control_weight hPATE_prop_component hPATE_treated_component
      hPATE_control_component
  have hPATT_first_score :=
    estimated_score_local_experiment_variance_input_first_step_and_score_local_of_patt_z_components
      pattFirstStep bPATT.positive_bridge.estimated_bridge.estimated_input
      pattPropensity pattControl hPATT_first_transfer hPATT_score_transfer
      hPATT_prop_weight hPATT_control_weight hPATT_prop_component
      hPATT_control_component
  exact
    retrospective_pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identities_and_local_experiment_cores
      bPATE bPATT pateParameters pateOracleVariance pateFirstStepLoading
      pateTargetDriftLoading pateScoreCovariance hpate_interpret
      pattParameters pattOracleVariance pattFirstStepLoading
      pattTargetDriftLoading pattScoreCovariance hpatt_interpret
      hPATE_exact hPATE_bias_bound hPATE_geometry_regular hPATE_catchment
      hPATE_heterogeneity_moment hPATE_heterogeneity_variance
      hPATE_residual_reg hPATE_quad hPATE_radius_regular
      hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
      hPATE_first_score.1 hPATE_first_score.2 hPATE_core hPATT_exact
      hPATT_bias_bound hPATT_geometry_regular hPATT_catchment
      hPATT_heterogeneity_moment hPATT_heterogeneity_variance
      hPATT_residual_reg hPATT_quad hPATT_radius_regular
      hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
      hPATT_first_score.1 hPATT_first_score.2 hPATT_core

end WDSM
end Matching
end StatInference
