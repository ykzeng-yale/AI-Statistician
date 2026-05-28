import StatInference.Matching.WDSM.EstimatedScorePositiveVarianceScoreAdjustmentRefinement
import StatInference.Matching.WDSM.ProspectiveEstimatedScorePositiveVariancePaired
import StatInference.Matching.WDSM.RetrospectiveEstimatedScorePositiveVariancePaired

/-!
# Paired positive-variance estimated-score routes with concrete score-adjustment algebra

This module pushes the fixed-law and changing-law score-adjustment refinements
through the paired positive-variance studentization layer.  The theorems keep
the paper-specific local-experiment, geometry, residual, and Godambe premises
explicit, but replace the two direct `score_adjustment_algebra` inputs by
finite quadratic-form identities plus arm-specific interpretation bridges.
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
Prospective paired PATE/PATT positive-variance studentized route, with both
score-adjustment algebra premises supplied by fixed-law finite quadratic-form
identities.
-/
theorem
    prospective_pate_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_fixedLaw_score_adjustment_identities
    {PATEParam PATTParam : Type*}
    (bPATE :
      ProspectivePATEEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (pateParameters : Finset PATEParam) (pateOracleVariance : Real)
    (pateFirstStepLoading : PATEParam -> Real)
    (pateScoreCovariance : PATEParam -> PATEParam -> Real)
    (hpate_interpret :
      fixedLawScoreAdjustedVariance pateParameters pateOracleVariance
          pateFirstStepLoading pateScoreCovariance =
        pateOracleVariance -
          scoreQuadraticForm pateParameters pateFirstStepLoading
            pateScoreCovariance ->
        bPATE.estimated_bridge.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattScoreCovariance =
        pattOracleVariance -
          scoreQuadraticForm pattParameters pattFirstStepLoading
            pattScoreCovariance ->
        bPATT.estimated_bridge.estimated_input.score_adjustment_algebra)
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
            (fun _index => sampleLaw) limitLaw) :=
  prospective_pate_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment
    bPATE bPATT hPATE_exact hPATE_bias_bound hPATE_geometry_regular
    hPATE_catchment hPATE_heterogeneity_moment hPATE_heterogeneity_variance
    hPATE_residual_reg hPATE_quad hPATE_radius_regular
    hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
    hPATE_first hPATE_score hPATE_functional hPATE_equicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      bPATE.estimated_bridge.estimated_input.score_adjustment_algebra
      pateParameters pateOracleVariance pateFirstStepLoading
      pateScoreCovariance hpate_interpret)
    hPATE_godambe hPATT_exact hPATT_bias_bound hPATT_geometry_regular
    hPATT_catchment hPATT_heterogeneity_moment hPATT_heterogeneity_variance
    hPATT_residual_reg hPATT_quad hPATT_radius_regular
    hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
    hPATT_first hPATT_score hPATT_functional hPATT_equicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      bPATT.estimated_bridge.estimated_input.score_adjustment_algebra
      pattParameters pattOracleVariance pattFirstStepLoading
      pattScoreCovariance hpatt_interpret)
    hPATT_godambe

/--
Prospective paired PATE/PATT positive-variance studentized route, with both
score-adjustment algebra premises supplied by changing-law finite quadratic-form
identities.
-/
theorem
    prospective_pate_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_changingLaw_score_adjustment_identities
    {PATEParam PATTParam : Type*}
    (bPATE :
      ProspectivePATEEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
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
        bPATE.estimated_bridge.estimated_input.score_adjustment_algebra)
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
        bPATT.estimated_bridge.estimated_input.score_adjustment_algebra)
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
            (fun _index => sampleLaw) limitLaw) :=
  prospective_pate_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment
    bPATE bPATT hPATE_exact hPATE_bias_bound hPATE_geometry_regular
    hPATE_catchment hPATE_heterogeneity_moment hPATE_heterogeneity_variance
    hPATE_residual_reg hPATE_quad hPATE_radius_regular
    hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
    hPATE_first hPATE_score hPATE_functional hPATE_equicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      bPATE.estimated_bridge.estimated_input.score_adjustment_algebra
      pateParameters pateOracleVariance pateFirstStepLoading
      pateTargetDriftLoading pateScoreCovariance hpate_interpret)
    hPATE_godambe hPATT_exact hPATT_bias_bound hPATT_geometry_regular
    hPATT_catchment hPATT_heterogeneity_moment hPATT_heterogeneity_variance
    hPATT_residual_reg hPATT_quad hPATT_radius_regular
    hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
    hPATT_first hPATT_score hPATT_functional hPATT_equicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      bPATT.estimated_bridge.estimated_input.score_adjustment_algebra
      pattParameters pattOracleVariance pattFirstStepLoading
      pattTargetDriftLoading pattScoreCovariance hpatt_interpret)
    hPATT_godambe

/--
Prospective paired PATE/PATT positive-variance studentized route from
first-step Z-estimator component certificates, with both score-adjustment
algebra premises supplied by fixed-law finite quadratic-form identities.
-/
theorem
    prospective_pate_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identities
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
      ProspectivePATEEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
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
        bPATE.estimated_bridge.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattScoreCovariance =
        pattOracleVariance -
          scoreQuadraticForm pattParameters pattFirstStepLoading
            pattScoreCovariance ->
        bPATT.estimated_bridge.estimated_input.score_adjustment_algebra)
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
            (fun _index => sampleLaw) limitLaw) :=
  prospective_pate_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_z_components
    bPATE bPATT pateFirstStep pattFirstStep patePropensity pateTreated
    pateControl pattPropensity pattControl hPATE_exact hPATE_bias_bound
    hPATE_geometry_regular hPATE_catchment hPATE_heterogeneity_moment
    hPATE_heterogeneity_variance hPATE_residual_reg hPATE_quad
    hPATE_radius_regular hPATE_radius_geometry hPATE_finite hPATE_den
    hPATE_orthogonality hPATE_first_transfer hPATE_score_transfer
    hPATE_prop_weight hPATE_treated_weight hPATE_control_weight
    hPATE_prop_component hPATE_treated_component hPATE_control_component
    hPATE_functional hPATE_equicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      bPATE.estimated_bridge.estimated_input.score_adjustment_algebra
      pateParameters pateOracleVariance pateFirstStepLoading
      pateScoreCovariance hpate_interpret)
    hPATE_godambe hPATT_exact hPATT_bias_bound hPATT_geometry_regular
    hPATT_catchment hPATT_heterogeneity_moment hPATT_heterogeneity_variance
    hPATT_residual_reg hPATT_quad hPATT_radius_regular
    hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
    hPATT_first_transfer hPATT_score_transfer hPATT_prop_weight
    hPATT_control_weight hPATT_prop_component hPATT_control_component
    hPATT_functional hPATT_equicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      bPATT.estimated_bridge.estimated_input.score_adjustment_algebra
      pattParameters pattOracleVariance pattFirstStepLoading
      pattScoreCovariance hpatt_interpret)
    hPATT_godambe

/--
Prospective paired PATE/PATT positive-variance studentized route from
first-step Z-estimator component certificates, with both score-adjustment
algebra premises supplied by changing-law finite quadratic-form identities.
-/
theorem
    prospective_pate_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_z_components_changingLaw_score_adjustment_identities
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
      ProspectivePATEEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
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
        bPATE.estimated_bridge.estimated_input.score_adjustment_algebra)
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
        bPATT.estimated_bridge.estimated_input.score_adjustment_algebra)
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
            (fun _index => sampleLaw) limitLaw) :=
  prospective_pate_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_z_components
    bPATE bPATT pateFirstStep pattFirstStep patePropensity pateTreated
    pateControl pattPropensity pattControl hPATE_exact hPATE_bias_bound
    hPATE_geometry_regular hPATE_catchment hPATE_heterogeneity_moment
    hPATE_heterogeneity_variance hPATE_residual_reg hPATE_quad
    hPATE_radius_regular hPATE_radius_geometry hPATE_finite hPATE_den
    hPATE_orthogonality hPATE_first_transfer hPATE_score_transfer
    hPATE_prop_weight hPATE_treated_weight hPATE_control_weight
    hPATE_prop_component hPATE_treated_component hPATE_control_component
    hPATE_functional hPATE_equicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      bPATE.estimated_bridge.estimated_input.score_adjustment_algebra
      pateParameters pateOracleVariance pateFirstStepLoading
      pateTargetDriftLoading pateScoreCovariance hpate_interpret)
    hPATE_godambe hPATT_exact hPATT_bias_bound hPATT_geometry_regular
    hPATT_catchment hPATT_heterogeneity_moment hPATT_heterogeneity_variance
    hPATT_residual_reg hPATT_quad hPATT_radius_regular
    hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
    hPATT_first_transfer hPATT_score_transfer hPATT_prop_weight
    hPATT_control_weight hPATT_prop_component hPATT_control_component
    hPATT_functional hPATT_equicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      bPATT.estimated_bridge.estimated_input.score_adjustment_algebra
      pattParameters pattOracleVariance pattFirstStepLoading
      pattTargetDriftLoading pattScoreCovariance hpatt_interpret)
    hPATT_godambe

/--
Retrospective paired PATE/PATT positive-variance studentized route, with both
score-adjustment algebra premises supplied by fixed-law finite quadratic-form
identities.
-/
theorem
    retrospective_pate_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_fixedLaw_score_adjustment_identities
    {PATEParam PATTParam : Type*}
    (bPATE :
      RetrospectivePATEEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (bPATT :
      RetrospectivePATTEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (pateParameters : Finset PATEParam) (pateOracleVariance : Real)
    (pateFirstStepLoading : PATEParam -> Real)
    (pateScoreCovariance : PATEParam -> PATEParam -> Real)
    (hpate_interpret :
      fixedLawScoreAdjustedVariance pateParameters pateOracleVariance
          pateFirstStepLoading pateScoreCovariance =
        pateOracleVariance -
          scoreQuadraticForm pateParameters pateFirstStepLoading
            pateScoreCovariance ->
        bPATE.estimated_bridge.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattScoreCovariance =
        pattOracleVariance -
          scoreQuadraticForm pattParameters pattFirstStepLoading
            pattScoreCovariance ->
        bPATT.estimated_bridge.estimated_input.score_adjustment_algebra)
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
            (fun _index => sampleLaw) limitLaw) :=
  retrospective_pate_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment
    bPATE bPATT hPATE_exact hPATE_bias_bound hPATE_geometry_regular
    hPATE_catchment hPATE_heterogeneity_moment hPATE_heterogeneity_variance
    hPATE_residual_reg hPATE_quad hPATE_radius_regular
    hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
    hPATE_first hPATE_score hPATE_functional hPATE_equicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      bPATE.estimated_bridge.estimated_input.score_adjustment_algebra
      pateParameters pateOracleVariance pateFirstStepLoading
      pateScoreCovariance hpate_interpret)
    hPATE_godambe hPATT_exact hPATT_bias_bound hPATT_geometry_regular
    hPATT_catchment hPATT_heterogeneity_moment hPATT_heterogeneity_variance
    hPATT_residual_reg hPATT_quad hPATT_radius_regular
    hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
    hPATT_first hPATT_score hPATT_functional hPATT_equicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      bPATT.estimated_bridge.estimated_input.score_adjustment_algebra
      pattParameters pattOracleVariance pattFirstStepLoading
      pattScoreCovariance hpatt_interpret)
    hPATT_godambe

/--
Retrospective paired PATE/PATT positive-variance studentized route, with both
score-adjustment algebra premises supplied by changing-law finite quadratic-form
identities.
-/
theorem
    retrospective_pate_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_changingLaw_score_adjustment_identities
    {PATEParam PATTParam : Type*}
    (bPATE :
      RetrospectivePATEEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (bPATT :
      RetrospectivePATTEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
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
        bPATE.estimated_bridge.estimated_input.score_adjustment_algebra)
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
        bPATT.estimated_bridge.estimated_input.score_adjustment_algebra)
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
            (fun _index => sampleLaw) limitLaw) :=
  retrospective_pate_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment
    bPATE bPATT hPATE_exact hPATE_bias_bound hPATE_geometry_regular
    hPATE_catchment hPATE_heterogeneity_moment hPATE_heterogeneity_variance
    hPATE_residual_reg hPATE_quad hPATE_radius_regular
    hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
    hPATE_first hPATE_score hPATE_functional hPATE_equicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      bPATE.estimated_bridge.estimated_input.score_adjustment_algebra
      pateParameters pateOracleVariance pateFirstStepLoading
      pateTargetDriftLoading pateScoreCovariance hpate_interpret)
    hPATE_godambe hPATT_exact hPATT_bias_bound hPATT_geometry_regular
    hPATT_catchment hPATT_heterogeneity_moment hPATT_heterogeneity_variance
    hPATT_residual_reg hPATT_quad hPATT_radius_regular
    hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
    hPATT_first hPATT_score hPATT_functional hPATT_equicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      bPATT.estimated_bridge.estimated_input.score_adjustment_algebra
      pattParameters pattOracleVariance pattFirstStepLoading
      pattTargetDriftLoading pattScoreCovariance hpatt_interpret)
    hPATT_godambe

/--
Retrospective paired PATE/PATT positive-variance studentized route from
first-step Z-estimator component certificates, with both score-adjustment
algebra premises supplied by fixed-law finite quadratic-form identities.
-/
theorem
    retrospective_pate_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identities
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
      RetrospectivePATEEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (bPATT :
      RetrospectivePATTEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
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
        bPATE.estimated_bridge.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattScoreCovariance =
        pattOracleVariance -
          scoreQuadraticForm pattParameters pattFirstStepLoading
            pattScoreCovariance ->
        bPATT.estimated_bridge.estimated_input.score_adjustment_algebra)
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
            (fun _index => sampleLaw) limitLaw) :=
  retrospective_pate_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_z_components
    bPATE bPATT pateFirstStep pattFirstStep patePropensity pateTreated
    pateControl pattPropensity pattControl hPATE_exact hPATE_bias_bound
    hPATE_geometry_regular hPATE_catchment hPATE_heterogeneity_moment
    hPATE_heterogeneity_variance hPATE_residual_reg hPATE_quad
    hPATE_radius_regular hPATE_radius_geometry hPATE_finite hPATE_den
    hPATE_orthogonality hPATE_first_transfer hPATE_score_transfer
    hPATE_prop_weight hPATE_treated_weight hPATE_control_weight
    hPATE_prop_component hPATE_treated_component hPATE_control_component
    hPATE_functional hPATE_equicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      bPATE.estimated_bridge.estimated_input.score_adjustment_algebra
      pateParameters pateOracleVariance pateFirstStepLoading
      pateScoreCovariance hpate_interpret)
    hPATE_godambe hPATT_exact hPATT_bias_bound hPATT_geometry_regular
    hPATT_catchment hPATT_heterogeneity_moment hPATT_heterogeneity_variance
    hPATT_residual_reg hPATT_quad hPATT_radius_regular
    hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
    hPATT_first_transfer hPATT_score_transfer hPATT_prop_weight
    hPATT_control_weight hPATT_prop_component hPATT_control_component
    hPATT_functional hPATT_equicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      bPATT.estimated_bridge.estimated_input.score_adjustment_algebra
      pattParameters pattOracleVariance pattFirstStepLoading
      pattScoreCovariance hpatt_interpret)
    hPATT_godambe

/--
Retrospective paired PATE/PATT positive-variance studentized route from
first-step Z-estimator component certificates, with both score-adjustment
algebra premises supplied by changing-law finite quadratic-form identities.
-/
theorem
    retrospective_pate_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_z_components_changingLaw_score_adjustment_identities
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
      RetrospectivePATEEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (bPATT :
      RetrospectivePATTEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
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
        bPATE.estimated_bridge.estimated_input.score_adjustment_algebra)
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
        bPATT.estimated_bridge.estimated_input.score_adjustment_algebra)
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
            (fun _index => sampleLaw) limitLaw) :=
  retrospective_pate_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_z_components
    bPATE bPATT pateFirstStep pattFirstStep patePropensity pateTreated
    pateControl pattPropensity pattControl hPATE_exact hPATE_bias_bound
    hPATE_geometry_regular hPATE_catchment hPATE_heterogeneity_moment
    hPATE_heterogeneity_variance hPATE_residual_reg hPATE_quad
    hPATE_radius_regular hPATE_radius_geometry hPATE_finite hPATE_den
    hPATE_orthogonality hPATE_first_transfer hPATE_score_transfer
    hPATE_prop_weight hPATE_treated_weight hPATE_control_weight
    hPATE_prop_component hPATE_treated_component hPATE_control_component
    hPATE_functional hPATE_equicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      bPATE.estimated_bridge.estimated_input.score_adjustment_algebra
      pateParameters pateOracleVariance pateFirstStepLoading
      pateTargetDriftLoading pateScoreCovariance hpate_interpret)
    hPATE_godambe hPATT_exact hPATT_bias_bound hPATT_geometry_regular
    hPATT_catchment hPATT_heterogeneity_moment hPATT_heterogeneity_variance
    hPATT_residual_reg hPATT_quad hPATT_radius_regular
    hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
    hPATT_first_transfer hPATT_score_transfer hPATT_prop_weight
    hPATT_control_weight hPATT_prop_component hPATT_control_component
    hPATT_functional hPATT_equicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      bPATT.estimated_bridge.estimated_input.score_adjustment_algebra
      pattParameters pattOracleVariance pattFirstStepLoading
      pattTargetDriftLoading pattScoreCovariance hpatt_interpret)
    hPATT_godambe

/--
Prospective paired PATE/PATT positive-variance studentized route, with fixed-law
score-adjustment identities and one compact local-experiment/Godambe core per
estimand.
-/
theorem
    prospective_pate_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_fixedLaw_score_adjustment_identities_and_local_experiment_cores
    {PATEParam PATTParam : Type*}
    (bPATE :
      ProspectivePATEEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (pateParameters : Finset PATEParam) (pateOracleVariance : Real)
    (pateFirstStepLoading : PATEParam -> Real)
    (pateScoreCovariance : PATEParam -> PATEParam -> Real)
    (hpate_interpret :
      fixedLawScoreAdjustedVariance pateParameters pateOracleVariance
          pateFirstStepLoading pateScoreCovariance =
        pateOracleVariance -
          scoreQuadraticForm pateParameters pateFirstStepLoading
            pateScoreCovariance ->
        bPATE.estimated_bridge.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattScoreCovariance =
        pattOracleVariance -
          scoreQuadraticForm pattParameters pattFirstStepLoading
            pattScoreCovariance ->
        bPATT.estimated_bridge.estimated_input.score_adjustment_algebra)
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
            (fun _index => sampleLaw) limitLaw) :=
  ⟨prospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_fixedLaw_score_adjustment_identity_and_local_experiment_core
      bPATE pateParameters pateOracleVariance pateFirstStepLoading
      pateScoreCovariance hpate_interpret hPATE_exact hPATE_bias_bound
      hPATE_geometry_regular hPATE_catchment hPATE_heterogeneity_moment
      hPATE_heterogeneity_variance hPATE_residual_reg hPATE_quad
      hPATE_radius_regular hPATE_radius_geometry hPATE_finite hPATE_den
      hPATE_orthogonality hPATE_first hPATE_score hPATE_core,
    prospective_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_fixedLaw_score_adjustment_identity_and_local_experiment_core
      bPATT pattParameters pattOracleVariance pattFirstStepLoading
      pattScoreCovariance hpatt_interpret hPATT_exact hPATT_bias_bound
      hPATT_geometry_regular hPATT_catchment hPATT_heterogeneity_moment
      hPATT_heterogeneity_variance hPATT_residual_reg hPATT_quad
      hPATT_radius_regular hPATT_radius_geometry hPATT_finite hPATT_den
      hPATT_orthogonality hPATT_first hPATT_score hPATT_core⟩

/--
Prospective paired PATE/PATT positive-variance studentized route, with
changing-law score-adjustment identities and one compact local-experiment/
Godambe core per estimand.
-/
theorem
    prospective_pate_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_changingLaw_score_adjustment_identities_and_local_experiment_cores
    {PATEParam PATTParam : Type*}
    (bPATE :
      ProspectivePATEEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
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
        bPATE.estimated_bridge.estimated_input.score_adjustment_algebra)
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
        bPATT.estimated_bridge.estimated_input.score_adjustment_algebra)
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
            (fun _index => sampleLaw) limitLaw) :=
  ⟨prospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_changingLaw_score_adjustment_identity_and_local_experiment_core
      bPATE pateParameters pateOracleVariance pateFirstStepLoading
      pateTargetDriftLoading pateScoreCovariance hpate_interpret hPATE_exact
      hPATE_bias_bound hPATE_geometry_regular hPATE_catchment
      hPATE_heterogeneity_moment hPATE_heterogeneity_variance
      hPATE_residual_reg hPATE_quad hPATE_radius_regular
      hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
      hPATE_first hPATE_score hPATE_core,
    prospective_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_changingLaw_score_adjustment_identity_and_local_experiment_core
      bPATT pattParameters pattOracleVariance pattFirstStepLoading
      pattTargetDriftLoading pattScoreCovariance hpatt_interpret hPATT_exact
      hPATT_bias_bound hPATT_geometry_regular hPATT_catchment
      hPATT_heterogeneity_moment hPATT_heterogeneity_variance
      hPATT_residual_reg hPATT_quad hPATT_radius_regular
      hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
      hPATT_first hPATT_score hPATT_core⟩

/--
Retrospective paired PATE/PATT positive-variance studentized route, with
fixed-law score-adjustment identities and one compact local-experiment/Godambe
core per estimand.
-/
theorem
    retrospective_pate_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_fixedLaw_score_adjustment_identities_and_local_experiment_cores
    {PATEParam PATTParam : Type*}
    (bPATE :
      RetrospectivePATEEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (bPATT :
      RetrospectivePATTEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (pateParameters : Finset PATEParam) (pateOracleVariance : Real)
    (pateFirstStepLoading : PATEParam -> Real)
    (pateScoreCovariance : PATEParam -> PATEParam -> Real)
    (hpate_interpret :
      fixedLawScoreAdjustedVariance pateParameters pateOracleVariance
          pateFirstStepLoading pateScoreCovariance =
        pateOracleVariance -
          scoreQuadraticForm pateParameters pateFirstStepLoading
            pateScoreCovariance ->
        bPATE.estimated_bridge.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattScoreCovariance =
        pattOracleVariance -
          scoreQuadraticForm pattParameters pattFirstStepLoading
            pattScoreCovariance ->
        bPATT.estimated_bridge.estimated_input.score_adjustment_algebra)
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
            (fun _index => sampleLaw) limitLaw) :=
  ⟨retrospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_fixedLaw_score_adjustment_identity_and_local_experiment_core
      bPATE pateParameters pateOracleVariance pateFirstStepLoading
      pateScoreCovariance hpate_interpret hPATE_exact hPATE_bias_bound
      hPATE_geometry_regular hPATE_catchment hPATE_heterogeneity_moment
      hPATE_heterogeneity_variance hPATE_residual_reg hPATE_quad
      hPATE_radius_regular hPATE_radius_geometry hPATE_finite hPATE_den
      hPATE_orthogonality hPATE_first hPATE_score hPATE_core,
    retrospective_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_fixedLaw_score_adjustment_identity_and_local_experiment_core
      bPATT pattParameters pattOracleVariance pattFirstStepLoading
      pattScoreCovariance hpatt_interpret hPATT_exact hPATT_bias_bound
      hPATT_geometry_regular hPATT_catchment hPATT_heterogeneity_moment
      hPATT_heterogeneity_variance hPATT_residual_reg hPATT_quad
      hPATT_radius_regular hPATT_radius_geometry hPATT_finite hPATT_den
      hPATT_orthogonality hPATT_first hPATT_score hPATT_core⟩

/--
Retrospective paired PATE/PATT positive-variance studentized route, with
changing-law score-adjustment identities and one compact local-experiment/
Godambe core per estimand.
-/
theorem
    retrospective_pate_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_changingLaw_score_adjustment_identities_and_local_experiment_cores
    {PATEParam PATTParam : Type*}
    (bPATE :
      RetrospectivePATEEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (bPATT :
      RetrospectivePATTEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
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
        bPATE.estimated_bridge.estimated_input.score_adjustment_algebra)
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
        bPATT.estimated_bridge.estimated_input.score_adjustment_algebra)
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
            (fun _index => sampleLaw) limitLaw) :=
  ⟨retrospective_pate_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_changingLaw_score_adjustment_identity_and_local_experiment_core
      bPATE pateParameters pateOracleVariance pateFirstStepLoading
      pateTargetDriftLoading pateScoreCovariance hpate_interpret hPATE_exact
      hPATE_bias_bound hPATE_geometry_regular hPATE_catchment
      hPATE_heterogeneity_moment hPATE_heterogeneity_variance
      hPATE_residual_reg hPATE_quad hPATE_radius_regular
      hPATE_radius_geometry hPATE_finite hPATE_den hPATE_orthogonality
      hPATE_first hPATE_score hPATE_core,
    retrospective_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_local_experiment_changingLaw_score_adjustment_identity_and_local_experiment_core
      bPATT pattParameters pattOracleVariance pattFirstStepLoading
      pattTargetDriftLoading pattScoreCovariance hpatt_interpret hPATT_exact
      hPATT_bias_bound hPATT_geometry_regular hPATT_catchment
      hPATT_heterogeneity_moment hPATT_heterogeneity_variance
      hPATT_residual_reg hPATT_quad hPATT_radius_regular
      hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
      hPATT_first hPATT_score hPATT_core⟩

/--
Prospective paired PATE/PATT positive-variance studentized route from
first-step Z-estimator component certificates, with both score-adjustment
algebra premises supplied by fixed-law finite quadratic-form identities and compact
local-experiment/Godambe cores.
-/
theorem
    prospective_pate_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identities_and_local_experiment_cores
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
      ProspectivePATEEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
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
        bPATE.estimated_bridge.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattScoreCovariance =
        pattOracleVariance -
          scoreQuadraticForm pattParameters pattFirstStepLoading
            pattScoreCovariance ->
        bPATT.estimated_bridge.estimated_input.score_adjustment_algebra)
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
            (fun _index => sampleLaw) limitLaw) :=
  prospective_pate_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_z_components
    bPATE bPATT pateFirstStep pattFirstStep patePropensity pateTreated
    pateControl pattPropensity pattControl hPATE_exact hPATE_bias_bound
    hPATE_geometry_regular hPATE_catchment hPATE_heterogeneity_moment
    hPATE_heterogeneity_variance hPATE_residual_reg hPATE_quad
    hPATE_radius_regular hPATE_radius_geometry hPATE_finite hPATE_den
    hPATE_orthogonality hPATE_first_transfer hPATE_score_transfer
    hPATE_prop_weight hPATE_treated_weight hPATE_control_weight
    hPATE_prop_component hPATE_treated_component hPATE_control_component
    hPATE_core.matching_functional_local_derivative
    hPATE_core.local_stochastic_equicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      bPATE.estimated_bridge.estimated_input.score_adjustment_algebra
      pateParameters pateOracleVariance pateFirstStepLoading
      pateScoreCovariance hpate_interpret)
    hPATE_core.godambe_identity hPATT_exact hPATT_bias_bound hPATT_geometry_regular
    hPATT_catchment hPATT_heterogeneity_moment hPATT_heterogeneity_variance
    hPATT_residual_reg hPATT_quad hPATT_radius_regular
    hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
    hPATT_first_transfer hPATT_score_transfer hPATT_prop_weight
    hPATT_control_weight hPATT_prop_component hPATT_control_component
    hPATT_core.matching_functional_local_derivative
    hPATT_core.local_stochastic_equicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      bPATT.estimated_bridge.estimated_input.score_adjustment_algebra
      pattParameters pattOracleVariance pattFirstStepLoading
      pattScoreCovariance hpatt_interpret)
    hPATT_core.godambe_identity

/--
Prospective paired PATE/PATT positive-variance studentized route from
first-step Z-estimator component certificates, with both score-adjustment
algebra premises supplied by changing-law finite quadratic-form identities and compact
local-experiment/Godambe cores.
-/
theorem
    prospective_pate_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_z_components_changingLaw_score_adjustment_identities_and_local_experiment_cores
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
      ProspectivePATEEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (bPATT :
      ProspectivePATTEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
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
        bPATE.estimated_bridge.estimated_input.score_adjustment_algebra)
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
        bPATT.estimated_bridge.estimated_input.score_adjustment_algebra)
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
            (fun _index => sampleLaw) limitLaw) :=
  prospective_pate_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_z_components
    bPATE bPATT pateFirstStep pattFirstStep patePropensity pateTreated
    pateControl pattPropensity pattControl hPATE_exact hPATE_bias_bound
    hPATE_geometry_regular hPATE_catchment hPATE_heterogeneity_moment
    hPATE_heterogeneity_variance hPATE_residual_reg hPATE_quad
    hPATE_radius_regular hPATE_radius_geometry hPATE_finite hPATE_den
    hPATE_orthogonality hPATE_first_transfer hPATE_score_transfer
    hPATE_prop_weight hPATE_treated_weight hPATE_control_weight
    hPATE_prop_component hPATE_treated_component hPATE_control_component
    hPATE_core.matching_functional_local_derivative
    hPATE_core.local_stochastic_equicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      bPATE.estimated_bridge.estimated_input.score_adjustment_algebra
      pateParameters pateOracleVariance pateFirstStepLoading
      pateTargetDriftLoading pateScoreCovariance hpate_interpret)
    hPATE_core.godambe_identity hPATT_exact hPATT_bias_bound hPATT_geometry_regular
    hPATT_catchment hPATT_heterogeneity_moment hPATT_heterogeneity_variance
    hPATT_residual_reg hPATT_quad hPATT_radius_regular
    hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
    hPATT_first_transfer hPATT_score_transfer hPATT_prop_weight
    hPATT_control_weight hPATT_prop_component hPATT_control_component
    hPATT_core.matching_functional_local_derivative
    hPATT_core.local_stochastic_equicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      bPATT.estimated_bridge.estimated_input.score_adjustment_algebra
      pattParameters pattOracleVariance pattFirstStepLoading
      pattTargetDriftLoading pattScoreCovariance hpatt_interpret)
    hPATT_core.godambe_identity

/--
Retrospective paired PATE/PATT positive-variance studentized route from
first-step Z-estimator component certificates, with both score-adjustment
algebra premises supplied by fixed-law finite quadratic-form identities and compact
local-experiment/Godambe cores.
-/
theorem
    retrospective_pate_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_z_components_fixedLaw_score_adjustment_identities_and_local_experiment_cores
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
      RetrospectivePATEEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (bPATT :
      RetrospectivePATTEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
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
        bPATE.estimated_bridge.estimated_input.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattScoreCovariance =
        pattOracleVariance -
          scoreQuadraticForm pattParameters pattFirstStepLoading
            pattScoreCovariance ->
        bPATT.estimated_bridge.estimated_input.score_adjustment_algebra)
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
            (fun _index => sampleLaw) limitLaw) :=
  retrospective_pate_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_z_components
    bPATE bPATT pateFirstStep pattFirstStep patePropensity pateTreated
    pateControl pattPropensity pattControl hPATE_exact hPATE_bias_bound
    hPATE_geometry_regular hPATE_catchment hPATE_heterogeneity_moment
    hPATE_heterogeneity_variance hPATE_residual_reg hPATE_quad
    hPATE_radius_regular hPATE_radius_geometry hPATE_finite hPATE_den
    hPATE_orthogonality hPATE_first_transfer hPATE_score_transfer
    hPATE_prop_weight hPATE_treated_weight hPATE_control_weight
    hPATE_prop_component hPATE_treated_component hPATE_control_component
    hPATE_core.matching_functional_local_derivative
    hPATE_core.local_stochastic_equicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      bPATE.estimated_bridge.estimated_input.score_adjustment_algebra
      pateParameters pateOracleVariance pateFirstStepLoading
      pateScoreCovariance hpate_interpret)
    hPATE_core.godambe_identity hPATT_exact hPATT_bias_bound hPATT_geometry_regular
    hPATT_catchment hPATT_heterogeneity_moment hPATT_heterogeneity_variance
    hPATT_residual_reg hPATT_quad hPATT_radius_regular
    hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
    hPATT_first_transfer hPATT_score_transfer hPATT_prop_weight
    hPATT_control_weight hPATT_prop_component hPATT_control_component
    hPATT_core.matching_functional_local_derivative
    hPATT_core.local_stochastic_equicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      bPATT.estimated_bridge.estimated_input.score_adjustment_algebra
      pattParameters pattOracleVariance pattFirstStepLoading
      pattScoreCovariance hpatt_interpret)
    hPATT_core.godambe_identity

/--
Retrospective paired PATE/PATT positive-variance studentized route from
first-step Z-estimator component certificates, with both score-adjustment
algebra premises supplied by changing-law finite quadratic-form identities and compact
local-experiment/Godambe cores.
-/
theorem
    retrospective_pate_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_z_components_changingLaw_score_adjustment_identities_and_local_experiment_cores
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
      RetrospectivePATEEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
    (bPATT :
      RetrospectivePATTEstimatedScorePositiveVarianceBridge Index Sample
        LimitSample sampleLaw limitLaw l)
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
        bPATE.estimated_bridge.estimated_input.score_adjustment_algebra)
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
        bPATT.estimated_bridge.estimated_input.score_adjustment_algebra)
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
            (fun _index => sampleLaw) limitLaw) :=
  retrospective_pate_patt_estimated_score_positiveVariance_studentized_tendsto_of_audited_z_components
    bPATE bPATT pateFirstStep pattFirstStep patePropensity pateTreated
    pateControl pattPropensity pattControl hPATE_exact hPATE_bias_bound
    hPATE_geometry_regular hPATE_catchment hPATE_heterogeneity_moment
    hPATE_heterogeneity_variance hPATE_residual_reg hPATE_quad
    hPATE_radius_regular hPATE_radius_geometry hPATE_finite hPATE_den
    hPATE_orthogonality hPATE_first_transfer hPATE_score_transfer
    hPATE_prop_weight hPATE_treated_weight hPATE_control_weight
    hPATE_prop_component hPATE_treated_component hPATE_control_component
    hPATE_core.matching_functional_local_derivative
    hPATE_core.local_stochastic_equicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      bPATE.estimated_bridge.estimated_input.score_adjustment_algebra
      pateParameters pateOracleVariance pateFirstStepLoading
      pateTargetDriftLoading pateScoreCovariance hpate_interpret)
    hPATE_core.godambe_identity hPATT_exact hPATT_bias_bound hPATT_geometry_regular
    hPATT_catchment hPATT_heterogeneity_moment hPATT_heterogeneity_variance
    hPATT_residual_reg hPATT_quad hPATT_radius_regular
    hPATT_radius_geometry hPATT_finite hPATT_den hPATT_orthogonality
    hPATT_first_transfer hPATT_score_transfer hPATT_prop_weight
    hPATT_control_weight hPATT_prop_component hPATT_control_component
    hPATT_core.matching_functional_local_derivative
    hPATT_core.local_stochastic_equicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      bPATT.estimated_bridge.estimated_input.score_adjustment_algebra
      pattParameters pattOracleVariance pattFirstStepLoading
      pattTargetDriftLoading pattScoreCovariance hpatt_interpret)
    hPATT_core.godambe_identity

end WDSM
end Matching
end StatInference
