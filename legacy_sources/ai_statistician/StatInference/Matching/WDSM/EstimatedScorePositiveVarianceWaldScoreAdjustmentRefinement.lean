import StatInference.Matching.WDSM.EstimatedScorePositiveVarianceScoreAdjustmentRefinement
import StatInference.Matching.WDSM.ProspectiveEstimatedScorePositiveVariancePaired
import StatInference.Matching.WDSM.RetrospectiveEstimatedScorePositiveVariancePaired

/-!
# Single-arm positive-variance Wald coverage with concrete score-adjustment algebra

This module pushes the fixed-law and changing-law score-adjustment refinements
through the single-arm positive-variance Wald coverage routes.  The coverage
calibration, geometry, residual, local-expansion, and Godambe premises remain
explicit; these wrappers only replace direct `score_adjustment_algebra` inputs
by finite quadratic-form identities plus interpretation bridges.
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

section ProspectivePATEAbsolute

variable {Param : Type*}
variable
    (b :
      ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)

/--
Prospective PATE absolute positive-variance Wald coverage, with
score-adjustment algebra supplied by the fixed-law finite quadratic-form
identity.
-/
theorem
    prospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hfunctional :
      b.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hgodambe :
      b.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion b := by
  simpa [ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion] using
    prospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score
      b hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst hscore hfunctional hequicontinuity
      (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
        parameters oracleVariance firstStepLoading scoreCovariance
        hinterpret)
      hgodambe

/--
Prospective PATE absolute positive-variance Wald coverage, with
score-adjustment algebra supplied by the changing-law finite quadratic-form
identity.
-/
theorem
    prospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hfunctional :
      b.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hgodambe :
      b.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion b := by
  simpa [ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion] using
    prospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score
      b hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst hscore hfunctional hequicontinuity
      (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
        parameters oracleVariance firstStepLoading targetDriftLoading
        scoreCovariance hinterpret)
      hgodambe

/--
Prospective PATE absolute positive-variance Wald coverage, with fixed-law
score-adjustment algebra and a compact local-experiment/Godambe core.
-/
theorem
    prospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion b :=
  prospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identity
    (b := b) parameters oracleVariance firstStepLoading scoreCovariance
    hinterpret hexact hbias_bound hgeometry_regular hcatchment
    hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
    hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

/--
Prospective PATE absolute positive-variance Wald coverage, with changing-law
score-adjustment algebra and a compact local-experiment/Godambe core.
-/
theorem
    prospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion b :=
  prospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identity
    (b := b) parameters oracleVariance firstStepLoading targetDriftLoading
    scoreCovariance hinterpret hexact hbias_bound hgeometry_regular
    hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
    hquad hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

end ProspectivePATEAbsolute

section ProspectivePATETwoSided

variable {Param : Type*}
variable
    (b :
      ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)

/--
Prospective PATE two-sided positive-variance Wald coverage, with
score-adjustment algebra supplied by the fixed-law finite quadratic-form
identity.
-/
theorem
    prospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hfunctional :
      b.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hgodambe :
      b.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b := by
  simpa [ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion] using
    prospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score
      b hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst hscore hfunctional hequicontinuity
      (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
        parameters oracleVariance firstStepLoading scoreCovariance
        hinterpret)
      hgodambe

/--
Prospective PATE two-sided positive-variance Wald coverage, with
score-adjustment algebra supplied by the changing-law finite quadratic-form
identity.
-/
theorem
    prospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hfunctional :
      b.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hgodambe :
      b.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b := by
  simpa [ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion] using
    prospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score
      b hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst hscore hfunctional hequicontinuity
      (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
        parameters oracleVariance firstStepLoading targetDriftLoading
        scoreCovariance hinterpret)
      hgodambe

/--
Prospective PATE two-sided positive-variance Wald coverage, with fixed-law
score-adjustment algebra and a compact local-experiment/Godambe core.
-/
theorem
    prospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b :=
  prospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identity
    (b := b) parameters oracleVariance firstStepLoading scoreCovariance
    hinterpret hexact hbias_bound hgeometry_regular hcatchment
    hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
    hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

/--
Prospective PATE two-sided positive-variance Wald coverage, with changing-law
score-adjustment algebra and a compact local-experiment/Godambe core.
-/
theorem
    prospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b :=
  prospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identity
    (b := b) parameters oracleVariance firstStepLoading targetDriftLoading
    scoreCovariance hinterpret hexact hbias_bound hgeometry_regular
    hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
    hquad hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

end ProspectivePATETwoSided

section ProspectivePATTAbsolute

variable {Param : Type*}
variable
    (b :
      ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)

/--
Prospective PATT absolute positive-variance Wald coverage, with
score-adjustment algebra supplied by the fixed-law finite quadratic-form
identity.
-/
theorem
    prospective_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hfunctional :
      b.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hgodambe :
      b.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion b := by
  simpa [ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion] using
    prospective_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score
      b hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst hscore hfunctional hequicontinuity
      (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
        parameters oracleVariance firstStepLoading scoreCovariance
        hinterpret)
      hgodambe

/--
Prospective PATT absolute positive-variance Wald coverage, with
score-adjustment algebra supplied by the changing-law finite quadratic-form
identity.
-/
theorem
    prospective_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hfunctional :
      b.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hgodambe :
      b.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion b := by
  simpa [ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion] using
    prospective_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score
      b hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst hscore hfunctional hequicontinuity
      (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
        parameters oracleVariance firstStepLoading targetDriftLoading
        scoreCovariance hinterpret)
      hgodambe

/--
Prospective PATT absolute positive-variance Wald coverage, with fixed-law
score-adjustment algebra and a compact local-experiment/Godambe core.
-/
theorem
    prospective_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion b :=
  prospective_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identity
    (b := b) parameters oracleVariance firstStepLoading scoreCovariance
    hinterpret hexact hbias_bound hgeometry_regular hcatchment
    hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
    hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

/--
Prospective PATT absolute positive-variance Wald coverage, with changing-law
score-adjustment algebra and a compact local-experiment/Godambe core.
-/
theorem
    prospective_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion b :=
  prospective_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identity
    (b := b) parameters oracleVariance firstStepLoading targetDriftLoading
    scoreCovariance hinterpret hexact hbias_bound hgeometry_regular
    hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
    hquad hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

end ProspectivePATTAbsolute

section ProspectivePATTTwoSided

variable {Param : Type*}
variable
    (b :
      ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)

/--
Prospective PATT two-sided positive-variance Wald coverage, with
score-adjustment algebra supplied by the fixed-law finite quadratic-form
identity.
-/
theorem
    prospective_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hfunctional :
      b.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hgodambe :
      b.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b := by
  simpa [ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion] using
    prospective_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score
      b hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst hscore hfunctional hequicontinuity
      (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
        parameters oracleVariance firstStepLoading scoreCovariance
        hinterpret)
      hgodambe

/--
Prospective PATT two-sided positive-variance Wald coverage, with
score-adjustment algebra supplied by the changing-law finite quadratic-form
identity.
-/
theorem
    prospective_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hfunctional :
      b.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hgodambe :
      b.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b := by
  simpa [ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion] using
    prospective_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score
      b hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst hscore hfunctional hequicontinuity
      (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
        parameters oracleVariance firstStepLoading targetDriftLoading
        scoreCovariance hinterpret)
      hgodambe

/--
Prospective PATT two-sided positive-variance Wald coverage, with fixed-law
score-adjustment algebra and a compact local-experiment/Godambe core.
-/
theorem
    prospective_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b :=
  prospective_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identity
    (b := b) parameters oracleVariance firstStepLoading scoreCovariance
    hinterpret hexact hbias_bound hgeometry_regular hcatchment
    hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
    hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

/--
Prospective PATT two-sided positive-variance Wald coverage, with changing-law
score-adjustment algebra and a compact local-experiment/Godambe core.
-/
theorem
    prospective_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b :=
  prospective_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identity
    (b := b) parameters oracleVariance firstStepLoading targetDriftLoading
    scoreCovariance hinterpret hexact hbias_bound hgeometry_regular
    hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
    hquad hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

end ProspectivePATTTwoSided

section RetrospectivePATEAbsolute

variable {Param : Type*}
variable
    (b :
      RetrospectivePATEEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)

/--
Retrospective PATE absolute positive-variance Wald coverage, with
score-adjustment algebra supplied by the fixed-law finite quadratic-form
identity.
-/
theorem
    retrospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hfunctional :
      b.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hgodambe :
      b.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    RetrospectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion b := by
  simpa [RetrospectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion] using
    retrospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score
      b hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst hscore hfunctional hequicontinuity
      (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
        parameters oracleVariance firstStepLoading scoreCovariance
        hinterpret)
      hgodambe

/--
Retrospective PATE absolute positive-variance Wald coverage, with
score-adjustment algebra supplied by the changing-law finite quadratic-form
identity.
-/
theorem
    retrospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hfunctional :
      b.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hgodambe :
      b.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    RetrospectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion b := by
  simpa [RetrospectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion] using
    retrospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score
      b hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst hscore hfunctional hequicontinuity
      (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
        parameters oracleVariance firstStepLoading targetDriftLoading
        scoreCovariance hinterpret)
      hgodambe

/--
Retrospective PATE absolute positive-variance Wald coverage, with fixed-law
score-adjustment algebra and a compact local-experiment/Godambe core.
-/
theorem
    retrospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    RetrospectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion b :=
  retrospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identity
    (b := b) parameters oracleVariance firstStepLoading scoreCovariance
    hinterpret hexact hbias_bound hgeometry_regular hcatchment
    hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
    hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

/--
Retrospective PATE absolute positive-variance Wald coverage, with changing-law
score-adjustment algebra and a compact local-experiment/Godambe core.
-/
theorem
    retrospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    RetrospectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion b :=
  retrospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identity
    (b := b) parameters oracleVariance firstStepLoading targetDriftLoading
    scoreCovariance hinterpret hexact hbias_bound hgeometry_regular
    hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
    hquad hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

end RetrospectivePATEAbsolute

section RetrospectivePATETwoSided

variable {Param : Type*}
variable
    (b :
      RetrospectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)

/--
Retrospective PATE two-sided positive-variance Wald coverage, with
score-adjustment algebra supplied by the fixed-law finite quadratic-form
identity.
-/
theorem
    retrospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hfunctional :
      b.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hgodambe :
      b.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    RetrospectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b := by
  simpa [RetrospectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion] using
    retrospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score
      b hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst hscore hfunctional hequicontinuity
      (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
        parameters oracleVariance firstStepLoading scoreCovariance
        hinterpret)
      hgodambe

/--
Retrospective PATE two-sided positive-variance Wald coverage, with
score-adjustment algebra supplied by the changing-law finite quadratic-form
identity.
-/
theorem
    retrospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hfunctional :
      b.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hgodambe :
      b.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    RetrospectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b := by
  simpa [RetrospectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion] using
    retrospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score
      b hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst hscore hfunctional hequicontinuity
      (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
        parameters oracleVariance firstStepLoading targetDriftLoading
        scoreCovariance hinterpret)
      hgodambe

/--
Retrospective PATE two-sided positive-variance Wald coverage, with fixed-law
score-adjustment algebra and a compact local-experiment/Godambe core.
-/
theorem
    retrospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    RetrospectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b :=
  retrospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identity
    (b := b) parameters oracleVariance firstStepLoading scoreCovariance
    hinterpret hexact hbias_bound hgeometry_regular hcatchment
    hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
    hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

/--
Retrospective PATE two-sided positive-variance Wald coverage, with changing-law
score-adjustment algebra and a compact local-experiment/Godambe core.
-/
theorem
    retrospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    RetrospectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b :=
  retrospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identity
    (b := b) parameters oracleVariance firstStepLoading targetDriftLoading
    scoreCovariance hinterpret hexact hbias_bound hgeometry_regular
    hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
    hquad hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

end RetrospectivePATETwoSided

section RetrospectivePATTAbsolute

variable {Param : Type*}
variable
    (b :
      RetrospectivePATTEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)

/--
Retrospective PATT absolute positive-variance Wald coverage, with
score-adjustment algebra supplied by the fixed-law finite quadratic-form
identity.
-/
theorem
    retrospective_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hfunctional :
      b.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hgodambe :
      b.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    RetrospectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion b := by
  simpa [RetrospectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion] using
    retrospective_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score
      b hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst hscore hfunctional hequicontinuity
      (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
        parameters oracleVariance firstStepLoading scoreCovariance
        hinterpret)
      hgodambe

/--
Retrospective PATT absolute positive-variance Wald coverage, with
score-adjustment algebra supplied by the changing-law finite quadratic-form
identity.
-/
theorem
    retrospective_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hfunctional :
      b.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hgodambe :
      b.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    RetrospectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion b := by
  simpa [RetrospectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion] using
    retrospective_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score
      b hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst hscore hfunctional hequicontinuity
      (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
        parameters oracleVariance firstStepLoading targetDriftLoading
        scoreCovariance hinterpret)
      hgodambe

/--
Retrospective PATT absolute positive-variance Wald coverage, with fixed-law
score-adjustment algebra and a compact local-experiment/Godambe core.
-/
theorem
    retrospective_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    RetrospectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion b :=
  retrospective_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identity
    (b := b) parameters oracleVariance firstStepLoading scoreCovariance
    hinterpret hexact hbias_bound hgeometry_regular hcatchment
    hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
    hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

/--
Retrospective PATT absolute positive-variance Wald coverage, with changing-law
score-adjustment algebra and a compact local-experiment/Godambe core.
-/
theorem
    retrospective_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    RetrospectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion b :=
  retrospective_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identity
    (b := b) parameters oracleVariance firstStepLoading targetDriftLoading
    scoreCovariance hinterpret hexact hbias_bound hgeometry_regular
    hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
    hquad hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

end RetrospectivePATTAbsolute

section RetrospectivePATTTwoSided

variable {Param : Type*}
variable
    (b :
      RetrospectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)

/--
Retrospective PATT two-sided positive-variance Wald coverage, with
score-adjustment algebra supplied by the fixed-law finite quadratic-form
identity.
-/
theorem
    retrospective_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hfunctional :
      b.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hgodambe :
      b.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    RetrospectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b := by
  simpa [RetrospectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion] using
    retrospective_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score
      b hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst hscore hfunctional hequicontinuity
      (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
        parameters oracleVariance firstStepLoading scoreCovariance
        hinterpret)
      hgodambe

/--
Retrospective PATT two-sided positive-variance Wald coverage, with
score-adjustment algebra supplied by the changing-law finite quadratic-form
identity.
-/
theorem
    retrospective_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (hfunctional :
      b.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hgodambe :
      b.positive_bridge.estimated_bridge.estimated_input.godambe_identity) :
    RetrospectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b := by
  simpa [RetrospectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion] using
    retrospective_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score
      b hexact hbias_bound hgeometry_regular hcatchment
      hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
      hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst hscore hfunctional hequicontinuity
      (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
        parameters oracleVariance firstStepLoading targetDriftLoading
        scoreCovariance hinterpret)
      hgodambe

/--
Retrospective PATT two-sided positive-variance Wald coverage, with fixed-law
score-adjustment algebra and a compact local-experiment/Godambe core.
-/
theorem
    retrospective_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    RetrospectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b :=
  retrospective_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_fixedLaw_score_adjustment_identity
    (b := b) parameters oracleVariance firstStepLoading scoreCovariance
    hinterpret hexact hbias_bound hgeometry_regular hcatchment
    hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
    hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

/--
Retrospective PATT two-sided positive-variance Wald coverage, with changing-law
score-adjustment algebra and a compact local-experiment/Godambe core.
-/
theorem
    retrospective_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst :
      b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore :
      b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    RetrospectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b :=
  retrospective_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_estimated_score_changingLaw_score_adjustment_identity
    (b := b) parameters oracleVariance firstStepLoading targetDriftLoading
    scoreCovariance hinterpret hexact hbias_bound hgeometry_regular
    hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
    hquad hradius_regular hradius_geometry hfinite hden horthogonality hfirst
    hscore core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

end RetrospectivePATTTwoSided

section ProspectivePATEAbsoluteZComponents

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
      ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
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
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
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
      b.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hgodambe :
      b.positive_bridge.estimated_bridge.estimated_input.godambe_identity)

include firstStep propensity treated control hexact hbias_bound
  hgeometry_regular hcatchment hheterogeneity_moment hheterogeneity_variance
  hresidual_reg hquad hradius_regular hradius_geometry hfinite hden
  horthogonality hfirst_transfer hscore_transfer h_prop_weight
  h_treated_weight h_control_weight h_prop_component h_treated_component
  h_control_component hfunctional hequicontinuity hgodambe

/--
Prospective PATE absolute positive-variance Wald coverage from first-step
Z-component certificates, with score-adjustment algebra supplied by the
fixed-law finite quadratic-form identity.
-/
theorem
    prospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra) :
    ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion b := by
  simpa [ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion] using
    prospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components
      b firstStep propensity treated control hexact hbias_bound
      hgeometry_regular hcatchment hheterogeneity_moment
      hheterogeneity_variance hresidual_reg hquad hradius_regular
      hradius_geometry hfinite hden horthogonality hfirst_transfer
      hscore_transfer h_prop_weight h_treated_weight h_control_weight
      h_prop_component h_treated_component h_control_component hfunctional
      hequicontinuity
      (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
        parameters oracleVariance firstStepLoading scoreCovariance
        hinterpret)
      hgodambe

/--
Prospective PATE absolute positive-variance Wald coverage from first-step
Z-component certificates, with score-adjustment algebra supplied by the
changing-law finite quadratic-form identity.
-/
theorem
    prospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra) :
    ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion b := by
  simpa [ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion] using
    prospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components
      b firstStep propensity treated control hexact hbias_bound
      hgeometry_regular hcatchment hheterogeneity_moment
      hheterogeneity_variance hresidual_reg hquad hradius_regular
      hradius_geometry hfinite hden horthogonality hfirst_transfer
      hscore_transfer h_prop_weight h_treated_weight h_control_weight
      h_prop_component h_treated_component h_control_component hfunctional
      hequicontinuity
      (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
        parameters oracleVariance firstStepLoading targetDriftLoading
        scoreCovariance hinterpret)
      hgodambe

omit hfunctional hequicontinuity hgodambe in
/--
Prospective PATE absolute positive-variance Wald coverage from first-step
Z-component certificates, with changing-law score-adjustment algebra and a
compact local-experiment/Godambe core.
-/
theorem
    prospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion b :=
  prospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity
    (b := b) (firstStep := firstStep) (propensity := propensity)
    (treated := treated) (control := control) hexact hbias_bound
    hgeometry_regular hcatchment hheterogeneity_moment
    hheterogeneity_variance hresidual_reg hquad hradius_regular
    hradius_geometry hfinite hden horthogonality hfirst_transfer
    hscore_transfer h_prop_weight h_treated_weight h_control_weight
    h_prop_component h_treated_component h_control_component
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity
    parameters oracleVariance firstStepLoading targetDriftLoading
    scoreCovariance hinterpret

omit hfunctional hequicontinuity hgodambe in
/--
Prospective PATE absolute positive-variance Wald coverage from first-step
Z-component certificates, with fixed-law score-adjustment algebra and a compact
local-experiment/Godambe core.
-/
theorem
    prospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    ProspectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion b :=
  prospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity
    (b := b) (firstStep := firstStep) (propensity := propensity)
    (treated := treated) (control := control) hexact hbias_bound
    hgeometry_regular hcatchment hheterogeneity_moment
    hheterogeneity_variance hresidual_reg hquad hradius_regular
    hradius_geometry hfinite hden horthogonality hfirst_transfer
    hscore_transfer h_prop_weight h_treated_weight h_control_weight
    h_prop_component h_treated_component h_control_component
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity parameters
    oracleVariance firstStepLoading scoreCovariance hinterpret

end ProspectivePATEAbsoluteZComponents

section ProspectivePATETwoSidedZComponents

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
      ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
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
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
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
      b.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hgodambe :
      b.positive_bridge.estimated_bridge.estimated_input.godambe_identity)

include firstStep propensity treated control hexact hbias_bound
  hgeometry_regular hcatchment hheterogeneity_moment hheterogeneity_variance
  hresidual_reg hquad hradius_regular hradius_geometry hfinite hden
  horthogonality hfirst_transfer hscore_transfer h_prop_weight
  h_treated_weight h_control_weight h_prop_component h_treated_component
  h_control_component hfunctional hequicontinuity hgodambe

/--
Prospective PATE two-sided positive-variance Wald coverage from first-step
Z-component certificates, with score-adjustment algebra supplied by the
fixed-law finite quadratic-form identity.
-/
theorem
    prospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra) :
    ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b := by
  simpa [ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion] using
    prospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components
      b firstStep propensity treated control hexact hbias_bound
      hgeometry_regular hcatchment hheterogeneity_moment
      hheterogeneity_variance hresidual_reg hquad hradius_regular
      hradius_geometry hfinite hden horthogonality hfirst_transfer
      hscore_transfer h_prop_weight h_treated_weight h_control_weight
      h_prop_component h_treated_component h_control_component hfunctional
      hequicontinuity
      (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
        parameters oracleVariance firstStepLoading scoreCovariance
        hinterpret)
      hgodambe

/--
Prospective PATE two-sided positive-variance Wald coverage from first-step
Z-component certificates, with score-adjustment algebra supplied by the
changing-law finite quadratic-form identity.
-/
theorem
    prospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra) :
    ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b := by
  simpa [ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion] using
    prospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components
      b firstStep propensity treated control hexact hbias_bound
      hgeometry_regular hcatchment hheterogeneity_moment
      hheterogeneity_variance hresidual_reg hquad hradius_regular
      hradius_geometry hfinite hden horthogonality hfirst_transfer
      hscore_transfer h_prop_weight h_treated_weight h_control_weight
      h_prop_component h_treated_component h_control_component hfunctional
      hequicontinuity
      (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
        parameters oracleVariance firstStepLoading targetDriftLoading
        scoreCovariance hinterpret)
      hgodambe

omit hfunctional hequicontinuity hgodambe in
/--
Prospective PATE two-sided positive-variance Wald coverage from first-step
Z-component certificates, with changing-law score-adjustment algebra and a
compact local-experiment/Godambe core.
-/
theorem
    prospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b :=
  prospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity
    (b := b) (firstStep := firstStep) (propensity := propensity)
    (treated := treated) (control := control) hexact hbias_bound
    hgeometry_regular hcatchment hheterogeneity_moment
    hheterogeneity_variance hresidual_reg hquad hradius_regular
    hradius_geometry hfinite hden horthogonality hfirst_transfer
    hscore_transfer h_prop_weight h_treated_weight h_control_weight
    h_prop_component h_treated_component h_control_component
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity
    parameters oracleVariance firstStepLoading targetDriftLoading
    scoreCovariance hinterpret

omit hfunctional hequicontinuity hgodambe in
/--
Prospective PATE two-sided positive-variance Wald coverage from first-step
Z-component certificates, with fixed-law score-adjustment algebra and a compact
local-experiment/Godambe core.
-/
theorem
    prospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    ProspectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b :=
  prospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity
    (b := b) (firstStep := firstStep) (propensity := propensity)
    (treated := treated) (control := control) hexact hbias_bound
    hgeometry_regular hcatchment hheterogeneity_moment
    hheterogeneity_variance hresidual_reg hquad hradius_regular
    hradius_geometry hfinite hden horthogonality hfirst_transfer
    hscore_transfer h_prop_weight h_treated_weight h_control_weight
    h_prop_component h_treated_component h_control_component
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity parameters
    oracleVariance firstStepLoading scoreCovariance hinterpret

end ProspectivePATETwoSidedZComponents

section ProspectivePATTAbsoluteZComponents

variable {Param : Type*}
variable {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
variable {PInfluenceFunction : Type x} {PLinearPart : Type y}
variable {PRemainder : Type z}
variable {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
variable {CInfluenceFunction : Type x} {CLinearPart : Type y}
variable {CRemainder : Type z}
variable
    (b :
      ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (firstStep : PATTDoubleScoreFirstStepAssembly)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
    (control :
      FirstStepScoreComponentZEvidence CSample CParameter CMoment
        CInfluenceFunction CLinearPart CRemainder)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
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
      b.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hgodambe :
      b.positive_bridge.estimated_bridge.estimated_input.godambe_identity)

include firstStep propensity control hexact hbias_bound hgeometry_regular
  hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
  hquad hradius_regular hradius_geometry hfinite hden horthogonality
  hfirst_transfer hscore_transfer h_prop_weight h_control_weight
  h_prop_component h_control_component hfunctional hequicontinuity hgodambe

/--
Prospective PATT absolute positive-variance Wald coverage from first-step
Z-component certificates, with score-adjustment algebra supplied by the
fixed-law finite quadratic-form identity.
-/
theorem
    prospective_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra) :
    ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion b := by
  simpa [ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion] using
    prospective_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components
      b firstStep propensity control hexact hbias_bound hgeometry_regular
      hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
      hquad hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst_transfer hscore_transfer h_prop_weight h_control_weight
      h_prop_component h_control_component hfunctional hequicontinuity
      (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
        parameters oracleVariance firstStepLoading scoreCovariance
        hinterpret)
      hgodambe

/--
Prospective PATT absolute positive-variance Wald coverage from first-step
Z-component certificates, with score-adjustment algebra supplied by the
changing-law finite quadratic-form identity.
-/
theorem
    prospective_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra) :
    ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion b := by
  simpa [ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion] using
    prospective_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components
      b firstStep propensity control hexact hbias_bound hgeometry_regular
      hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
      hquad hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst_transfer hscore_transfer h_prop_weight h_control_weight
      h_prop_component h_control_component hfunctional hequicontinuity
      (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
        parameters oracleVariance firstStepLoading targetDriftLoading
        scoreCovariance hinterpret)
      hgodambe

omit hfunctional hequicontinuity hgodambe in
/--
Prospective PATT absolute positive-variance Wald coverage from first-step
Z-component certificates, with changing-law score-adjustment algebra and a
compact local-experiment/Godambe core.
-/
theorem
    prospective_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion b :=
  prospective_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity
    (b := b) (firstStep := firstStep) (propensity := propensity)
    (control := control) hexact hbias_bound hgeometry_regular hcatchment
    hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
    hradius_regular hradius_geometry hfinite hden horthogonality
    hfirst_transfer hscore_transfer h_prop_weight h_control_weight
    h_prop_component h_control_component
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity
    parameters oracleVariance firstStepLoading targetDriftLoading
    scoreCovariance hinterpret

omit hfunctional hequicontinuity hgodambe in
/--
Prospective PATT absolute positive-variance Wald coverage from first-step
Z-component certificates, with fixed-law score-adjustment algebra and a compact
local-experiment/Godambe core.
-/
theorem
    prospective_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    ProspectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion b :=
  prospective_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity
    (b := b) (firstStep := firstStep) (propensity := propensity)
    (control := control) hexact hbias_bound hgeometry_regular hcatchment
    hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
    hradius_regular hradius_geometry hfinite hden horthogonality
    hfirst_transfer hscore_transfer h_prop_weight h_control_weight
    h_prop_component h_control_component
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity parameters
    oracleVariance firstStepLoading scoreCovariance hinterpret

end ProspectivePATTAbsoluteZComponents

section ProspectivePATTTwoSidedZComponents

variable {Param : Type*}
variable {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
variable {PInfluenceFunction : Type x} {PLinearPart : Type y}
variable {PRemainder : Type z}
variable {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
variable {CInfluenceFunction : Type x} {CLinearPart : Type y}
variable {CRemainder : Type z}
variable
    (b :
      ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (firstStep : PATTDoubleScoreFirstStepAssembly)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
    (control :
      FirstStepScoreComponentZEvidence CSample CParameter CMoment
        CInfluenceFunction CLinearPart CRemainder)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
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
      b.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hgodambe :
      b.positive_bridge.estimated_bridge.estimated_input.godambe_identity)

include firstStep propensity control hexact hbias_bound hgeometry_regular
  hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
  hquad hradius_regular hradius_geometry hfinite hden horthogonality
  hfirst_transfer hscore_transfer h_prop_weight h_control_weight
  h_prop_component h_control_component hfunctional hequicontinuity hgodambe

/--
Prospective PATT two-sided positive-variance Wald coverage from first-step
Z-component certificates, with score-adjustment algebra supplied by the
fixed-law finite quadratic-form identity.
-/
theorem
    prospective_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra) :
    ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b := by
  simpa [ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion] using
    prospective_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components
      b firstStep propensity control hexact hbias_bound hgeometry_regular
      hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
      hquad hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst_transfer hscore_transfer h_prop_weight h_control_weight
      h_prop_component h_control_component hfunctional hequicontinuity
      (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
        parameters oracleVariance firstStepLoading scoreCovariance
        hinterpret)
      hgodambe

/--
Prospective PATT two-sided positive-variance Wald coverage from first-step
Z-component certificates, with score-adjustment algebra supplied by the
changing-law finite quadratic-form identity.
-/
theorem
    prospective_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra) :
    ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b := by
  simpa [ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion] using
    prospective_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components
      b firstStep propensity control hexact hbias_bound hgeometry_regular
      hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
      hquad hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst_transfer hscore_transfer h_prop_weight h_control_weight
      h_prop_component h_control_component hfunctional hequicontinuity
      (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
        parameters oracleVariance firstStepLoading targetDriftLoading
        scoreCovariance hinterpret)
      hgodambe

omit hfunctional hequicontinuity hgodambe in
/--
Prospective PATT two-sided positive-variance Wald coverage from first-step
Z-component certificates, with changing-law score-adjustment algebra and a
compact local-experiment/Godambe core.
-/
theorem
    prospective_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b :=
  prospective_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity
    (b := b) (firstStep := firstStep) (propensity := propensity)
    (control := control) hexact hbias_bound hgeometry_regular hcatchment
    hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
    hradius_regular hradius_geometry hfinite hden horthogonality
    hfirst_transfer hscore_transfer h_prop_weight h_control_weight
    h_prop_component h_control_component
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity
    parameters oracleVariance firstStepLoading targetDriftLoading
    scoreCovariance hinterpret

omit hfunctional hequicontinuity hgodambe in
/--
Prospective PATT two-sided positive-variance Wald coverage from first-step
Z-component certificates, with fixed-law score-adjustment algebra and a compact
local-experiment/Godambe core.
-/
theorem
    prospective_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    ProspectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b :=
  prospective_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity
    (b := b) (firstStep := firstStep) (propensity := propensity)
    (control := control) hexact hbias_bound hgeometry_regular hcatchment
    hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
    hradius_regular hradius_geometry hfinite hden horthogonality
    hfirst_transfer hscore_transfer h_prop_weight h_control_weight
    h_prop_component h_control_component
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity parameters
    oracleVariance firstStepLoading scoreCovariance hinterpret

end ProspectivePATTTwoSidedZComponents

section RetrospectivePATEAbsoluteZComponents

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
      RetrospectivePATEEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
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
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
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
      b.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hgodambe :
      b.positive_bridge.estimated_bridge.estimated_input.godambe_identity)

include firstStep propensity treated control hexact hbias_bound
  hgeometry_regular hcatchment hheterogeneity_moment hheterogeneity_variance
  hresidual_reg hquad hradius_regular hradius_geometry hfinite hden
  horthogonality hfirst_transfer hscore_transfer h_prop_weight
  h_treated_weight h_control_weight h_prop_component h_treated_component
  h_control_component hfunctional hequicontinuity hgodambe

/--
Retrospective PATE absolute positive-variance Wald coverage from first-step
Z-component certificates, with score-adjustment algebra supplied by the
fixed-law finite quadratic-form identity.
-/
theorem
    retrospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra) :
    RetrospectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion b := by
  simpa [RetrospectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion] using
    retrospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components
      b firstStep propensity treated control hexact hbias_bound
      hgeometry_regular hcatchment hheterogeneity_moment
      hheterogeneity_variance hresidual_reg hquad hradius_regular
      hradius_geometry hfinite hden horthogonality hfirst_transfer
      hscore_transfer h_prop_weight h_treated_weight h_control_weight
      h_prop_component h_treated_component h_control_component hfunctional
      hequicontinuity
      (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
        parameters oracleVariance firstStepLoading scoreCovariance
        hinterpret)
      hgodambe

/--
Retrospective PATE absolute positive-variance Wald coverage from first-step
Z-component certificates, with score-adjustment algebra supplied by the
changing-law finite quadratic-form identity.
-/
theorem
    retrospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra) :
    RetrospectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion b := by
  simpa [RetrospectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion] using
    retrospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components
      b firstStep propensity treated control hexact hbias_bound
      hgeometry_regular hcatchment hheterogeneity_moment
      hheterogeneity_variance hresidual_reg hquad hradius_regular
      hradius_geometry hfinite hden horthogonality hfirst_transfer
      hscore_transfer h_prop_weight h_treated_weight h_control_weight
      h_prop_component h_treated_component h_control_component hfunctional
      hequicontinuity
      (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
        parameters oracleVariance firstStepLoading targetDriftLoading
        scoreCovariance hinterpret)
      hgodambe

omit hfunctional hequicontinuity hgodambe in
/--
Retrospective PATE absolute positive-variance Wald coverage from first-step
Z-component certificates, with changing-law score-adjustment algebra and a
compact local-experiment/Godambe core.
-/
theorem
    retrospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    RetrospectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion b :=
  retrospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity
    (b := b) (firstStep := firstStep) (propensity := propensity)
    (treated := treated) (control := control) hexact hbias_bound
    hgeometry_regular hcatchment hheterogeneity_moment
    hheterogeneity_variance hresidual_reg hquad hradius_regular
    hradius_geometry hfinite hden horthogonality hfirst_transfer
    hscore_transfer h_prop_weight h_treated_weight h_control_weight
    h_prop_component h_treated_component h_control_component
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity
    parameters oracleVariance firstStepLoading targetDriftLoading
    scoreCovariance hinterpret

omit hfunctional hequicontinuity hgodambe in
/--
Retrospective PATE absolute positive-variance Wald coverage from first-step
Z-component certificates, with fixed-law score-adjustment algebra and a compact
local-experiment/Godambe core.
-/
theorem
    retrospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    RetrospectivePATEEstimatedScoreAbsolutePositiveVarianceWaldConclusion b :=
  retrospective_pate_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity
    (b := b) (firstStep := firstStep) (propensity := propensity)
    (treated := treated) (control := control) hexact hbias_bound
    hgeometry_regular hcatchment hheterogeneity_moment
    hheterogeneity_variance hresidual_reg hquad hradius_regular
    hradius_geometry hfinite hden horthogonality hfirst_transfer
    hscore_transfer h_prop_weight h_treated_weight h_control_weight
    h_prop_component h_treated_component h_control_component
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity parameters
    oracleVariance firstStepLoading scoreCovariance hinterpret

end RetrospectivePATEAbsoluteZComponents

section RetrospectivePATETwoSidedZComponents

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
      RetrospectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
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
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
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
      b.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hgodambe :
      b.positive_bridge.estimated_bridge.estimated_input.godambe_identity)

include firstStep propensity treated control hexact hbias_bound
  hgeometry_regular hcatchment hheterogeneity_moment hheterogeneity_variance
  hresidual_reg hquad hradius_regular hradius_geometry hfinite hden
  horthogonality hfirst_transfer hscore_transfer h_prop_weight
  h_treated_weight h_control_weight h_prop_component h_treated_component
  h_control_component hfunctional hequicontinuity hgodambe

/--
Retrospective PATE two-sided positive-variance Wald coverage from first-step
Z-component certificates, with score-adjustment algebra supplied by the
fixed-law finite quadratic-form identity.
-/
theorem
    retrospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra) :
    RetrospectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b := by
  simpa [RetrospectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion] using
    retrospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components
      b firstStep propensity treated control hexact hbias_bound
      hgeometry_regular hcatchment hheterogeneity_moment
      hheterogeneity_variance hresidual_reg hquad hradius_regular
      hradius_geometry hfinite hden horthogonality hfirst_transfer
      hscore_transfer h_prop_weight h_treated_weight h_control_weight
      h_prop_component h_treated_component h_control_component hfunctional
      hequicontinuity
      (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
        parameters oracleVariance firstStepLoading scoreCovariance
        hinterpret)
      hgodambe

/--
Retrospective PATE two-sided positive-variance Wald coverage from first-step
Z-component certificates, with score-adjustment algebra supplied by the
changing-law finite quadratic-form identity.
-/
theorem
    retrospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra) :
    RetrospectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b := by
  simpa [RetrospectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion] using
    retrospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components
      b firstStep propensity treated control hexact hbias_bound
      hgeometry_regular hcatchment hheterogeneity_moment
      hheterogeneity_variance hresidual_reg hquad hradius_regular
      hradius_geometry hfinite hden horthogonality hfirst_transfer
      hscore_transfer h_prop_weight h_treated_weight h_control_weight
      h_prop_component h_treated_component h_control_component hfunctional
      hequicontinuity
      (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
        parameters oracleVariance firstStepLoading targetDriftLoading
        scoreCovariance hinterpret)
      hgodambe

omit hfunctional hequicontinuity hgodambe in
/--
Retrospective PATE two-sided positive-variance Wald coverage from first-step
Z-component certificates, with changing-law score-adjustment algebra and a
compact local-experiment/Godambe core.
-/
theorem
    retrospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    RetrospectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b :=
  retrospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity
    (b := b) (firstStep := firstStep) (propensity := propensity)
    (treated := treated) (control := control) hexact hbias_bound
    hgeometry_regular hcatchment hheterogeneity_moment
    hheterogeneity_variance hresidual_reg hquad hradius_regular
    hradius_geometry hfinite hden horthogonality hfirst_transfer
    hscore_transfer h_prop_weight h_treated_weight h_control_weight
    h_prop_component h_treated_component h_control_component
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity
    parameters oracleVariance firstStepLoading targetDriftLoading
    scoreCovariance hinterpret

omit hfunctional hequicontinuity hgodambe in
/--
Retrospective PATE two-sided positive-variance Wald coverage from first-step
Z-component certificates, with fixed-law score-adjustment algebra and a compact
local-experiment/Godambe core.
-/
theorem
    retrospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    RetrospectivePATEEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b :=
  retrospective_pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity
    (b := b) (firstStep := firstStep) (propensity := propensity)
    (treated := treated) (control := control) hexact hbias_bound
    hgeometry_regular hcatchment hheterogeneity_moment
    hheterogeneity_variance hresidual_reg hquad hradius_regular
    hradius_geometry hfinite hden horthogonality hfirst_transfer
    hscore_transfer h_prop_weight h_treated_weight h_control_weight
    h_prop_component h_treated_component h_control_component
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity parameters
    oracleVariance firstStepLoading scoreCovariance hinterpret

end RetrospectivePATETwoSidedZComponents

section RetrospectivePATTAbsoluteZComponents

variable {Param : Type*}
variable {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
variable {PInfluenceFunction : Type x} {PLinearPart : Type y}
variable {PRemainder : Type z}
variable {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
variable {CInfluenceFunction : Type x} {CLinearPart : Type y}
variable {CRemainder : Type z}
variable
    (b :
      RetrospectivePATTEstimatedScoreAbsolutePositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (firstStep : PATTDoubleScoreFirstStepAssembly)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
    (control :
      FirstStepScoreComponentZEvidence CSample CParameter CMoment
        CInfluenceFunction CLinearPart CRemainder)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
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
      b.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hgodambe :
      b.positive_bridge.estimated_bridge.estimated_input.godambe_identity)

include firstStep propensity control hexact hbias_bound hgeometry_regular
  hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
  hquad hradius_regular hradius_geometry hfinite hden horthogonality
  hfirst_transfer hscore_transfer h_prop_weight h_control_weight
  h_prop_component h_control_component hfunctional hequicontinuity hgodambe

/--
Retrospective PATT absolute positive-variance Wald coverage from first-step
Z-component certificates, with score-adjustment algebra supplied by the
fixed-law finite quadratic-form identity.
-/
theorem
    retrospective_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra) :
    RetrospectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion b := by
  simpa [RetrospectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion] using
    retrospective_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components
      b firstStep propensity control hexact hbias_bound hgeometry_regular
      hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
      hquad hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst_transfer hscore_transfer h_prop_weight h_control_weight
      h_prop_component h_control_component hfunctional hequicontinuity
      (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
        parameters oracleVariance firstStepLoading scoreCovariance
        hinterpret)
      hgodambe

/--
Retrospective PATT absolute positive-variance Wald coverage from first-step
Z-component certificates, with score-adjustment algebra supplied by the
changing-law finite quadratic-form identity.
-/
theorem
    retrospective_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra) :
    RetrospectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion b := by
  simpa [RetrospectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion] using
    retrospective_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components
      b firstStep propensity control hexact hbias_bound hgeometry_regular
      hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
      hquad hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst_transfer hscore_transfer h_prop_weight h_control_weight
      h_prop_component h_control_component hfunctional hequicontinuity
      (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
        parameters oracleVariance firstStepLoading targetDriftLoading
        scoreCovariance hinterpret)
      hgodambe

omit hfunctional hequicontinuity hgodambe in
/--
Retrospective PATT absolute positive-variance Wald coverage from first-step
Z-component certificates, with changing-law score-adjustment algebra and a
compact local-experiment/Godambe core.
-/
theorem
    retrospective_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    RetrospectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion b :=
  retrospective_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity
    (b := b) (firstStep := firstStep) (propensity := propensity)
    (control := control) hexact hbias_bound hgeometry_regular hcatchment
    hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
    hradius_regular hradius_geometry hfinite hden horthogonality
    hfirst_transfer hscore_transfer h_prop_weight h_control_weight
    h_prop_component h_control_component
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity
    parameters oracleVariance firstStepLoading targetDriftLoading
    scoreCovariance hinterpret

omit hfunctional hequicontinuity hgodambe in
/--
Retrospective PATT absolute positive-variance Wald coverage from first-step
Z-component certificates, with fixed-law score-adjustment algebra and a compact
local-experiment/Godambe core.
-/
theorem
    retrospective_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    RetrospectivePATTEstimatedScoreAbsolutePositiveVarianceWaldConclusion b :=
  retrospective_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity
    (b := b) (firstStep := firstStep) (propensity := propensity)
    (control := control) hexact hbias_bound hgeometry_regular hcatchment
    hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
    hradius_regular hradius_geometry hfinite hden horthogonality
    hfirst_transfer hscore_transfer h_prop_weight h_control_weight
    h_prop_component h_control_component
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity parameters
    oracleVariance firstStepLoading scoreCovariance hinterpret

end RetrospectivePATTAbsoluteZComponents

section RetrospectivePATTTwoSidedZComponents

variable {Param : Type*}
variable {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
variable {PInfluenceFunction : Type x} {PLinearPart : Type y}
variable {PRemainder : Type z}
variable {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
variable {CInfluenceFunction : Type x} {CLinearPart : Type y}
variable {CRemainder : Type z}
variable
    (b :
      RetrospectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldBridge Index
        Sample LimitSample sampleLaw limitLaw l)
    (firstStep : PATTDoubleScoreFirstStepAssembly)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
    (control :
      FirstStepScoreComponentZEvidence CSample CParameter CMoment
        CInfluenceFunction CLinearPart CRemainder)
    (hexact :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.score_density_regular)
    (hcatchment :
      b.positive_bridge.estimated_bridge.known_score_bridge.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.positive_bridge.estimated_bridge.known_score_bridge.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.residual_moment_regularity)
    (hquad :
      b.positive_bridge.estimated_bridge.known_score_bridge.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.score_density_regular)
    (hradius_geometry :
      b.positive_bridge.estimated_bridge.known_score_bridge.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.positive_bridge.estimated_bridge.known_score_bridge.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality :
      b.positive_bridge.estimated_bridge.known_score_bridge.variance_bridge.component_orthogonality)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        b.positive_bridge.estimated_bridge.estimated_input.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        b.positive_bridge.estimated_bridge.estimated_input.score_estimator_local_asymptotic_linearity)
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
      b.positive_bridge.estimated_bridge.estimated_input.matching_functional_local_derivative)
    (hequicontinuity :
      b.positive_bridge.estimated_bridge.estimated_input.local_stochastic_equicontinuity)
    (hgodambe :
      b.positive_bridge.estimated_bridge.estimated_input.godambe_identity)

include firstStep propensity control hexact hbias_bound hgeometry_regular
  hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
  hquad hradius_regular hradius_geometry hfinite hden horthogonality
  hfirst_transfer hscore_transfer h_prop_weight h_control_weight
  h_prop_component h_control_component hfunctional hequicontinuity hgodambe

/--
Retrospective PATT two-sided positive-variance Wald coverage from first-step
Z-component certificates, with score-adjustment algebra supplied by the
fixed-law finite quadratic-form identity.
-/
theorem
    retrospective_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra) :
    RetrospectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b := by
  simpa [RetrospectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion] using
    retrospective_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components
      b firstStep propensity control hexact hbias_bound hgeometry_regular
      hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
      hquad hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst_transfer hscore_transfer h_prop_weight h_control_weight
      h_prop_component h_control_component hfunctional hequicontinuity
      (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
        parameters oracleVariance firstStepLoading scoreCovariance
        hinterpret)
      hgodambe

/--
Retrospective PATT two-sided positive-variance Wald coverage from first-step
Z-component certificates, with score-adjustment algebra supplied by the
changing-law finite quadratic-form identity.
-/
theorem
    retrospective_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra) :
    RetrospectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b := by
  simpa [RetrospectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion] using
    retrospective_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components
      b firstStep propensity control hexact hbias_bound hgeometry_regular
      hcatchment hheterogeneity_moment hheterogeneity_variance hresidual_reg
      hquad hradius_regular hradius_geometry hfinite hden horthogonality
      hfirst_transfer hscore_transfer h_prop_weight h_control_weight
      h_prop_component h_control_component hfunctional hequicontinuity
      (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra
        parameters oracleVariance firstStepLoading targetDriftLoading
        scoreCovariance hinterpret)
      hgodambe

omit hfunctional hequicontinuity hgodambe in
/--
Retrospective PATT two-sided positive-variance Wald coverage from first-step
Z-component certificates, with changing-law score-adjustment algebra and a
compact local-experiment/Godambe core.
-/
theorem
    retrospective_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    RetrospectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b :=
  retrospective_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components_changingLaw_score_adjustment_identity
    (b := b) (firstStep := firstStep) (propensity := propensity)
    (control := control) hexact hbias_bound hgeometry_regular hcatchment
    hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
    hradius_regular hradius_geometry hfinite hden horthogonality
    hfirst_transfer hscore_transfer h_prop_weight h_control_weight
    h_prop_component h_control_component
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity
    parameters oracleVariance firstStepLoading targetDriftLoading
    scoreCovariance hinterpret

omit hfunctional hequicontinuity hgodambe in
/--
Retrospective PATT two-sided positive-variance Wald coverage from first-step
Z-component certificates, with fixed-law score-adjustment algebra and a compact
local-experiment/Godambe core.
-/
theorem
    retrospective_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity_and_local_experiment_core
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        b.positive_bridge.estimated_bridge.estimated_input.score_adjustment_algebra)
    (core :
      EstimatedScoreLocalExperimentVarianceCore
        b.positive_bridge.estimated_bridge.estimated_input) :
    RetrospectivePATTEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b :=
  retrospective_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identity
    (b := b) (firstStep := firstStep) (propensity := propensity)
    (control := control) hexact hbias_bound hgeometry_regular hcatchment
    hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
    hradius_regular hradius_geometry hfinite hden horthogonality
    hfirst_transfer hscore_transfer h_prop_weight h_control_weight
    h_prop_component h_control_component
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity parameters
    oracleVariance firstStepLoading scoreCovariance hinterpret

end RetrospectivePATTTwoSidedZComponents

end WDSM
end Matching
end StatInference
