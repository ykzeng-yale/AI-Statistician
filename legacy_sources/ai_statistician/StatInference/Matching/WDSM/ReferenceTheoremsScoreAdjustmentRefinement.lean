import StatInference.Matching.WDSM.ReferenceTheorems
import StatInference.Matching.WDSM.EstimatedScoreLocalExperimentVarianceRefinement

/-!
# Score-adjustment refinements for WDSM reference-theorem routes

This module narrows the Chen-Han reference-theorem estimated-score routes.
Instead of asking callers for a naked `score_adjustment_algebra` premise, the
wrappers below consume the locally proved fixed-law or changing-law finite
quadratic-form identities from `ScoreAdjustmentAlgebra`.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Param : Type*} [DecidableEq Param]

omit [DecidableEq Param] in
/--
Chen-Han estimated-score variance formula with the adjustment premise
discharged by the fixed-law finite score-adjustment identity.
-/
theorem estimated_score_variance_formula_of_chen_han_reference_bridge_fixedLaw_score_adjustment_identity
    (geometry : ChenHanGeometryBridge)
    (variance : EstimatedScoreVarianceFormulaBridge)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        variance.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hknown_variance_transfer :
      geometry.limiting_variance_formula ->
        variance.known_score_variance_formula)
    (hgodambe : variance.godambe_variance_identity) :
    variance.estimated_score_variance_formula :=
  estimated_score_variance_formula_of_chen_han_reference_bridge
    geometry variance hgeometry_regular hcatchment hknown_variance_transfer
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      variance.score_adjustment_algebra parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret)
    hgodambe

omit [DecidableEq Param] in
/--
Chen-Han estimated-score variance formula with the adjustment premise
discharged by the changing-law finite score-adjustment identity.
-/
theorem estimated_score_variance_formula_of_chen_han_reference_bridge_changingLaw_score_adjustment_identity
    (geometry : ChenHanGeometryBridge)
    (variance : EstimatedScoreVarianceFormulaBridge)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        variance.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hknown_variance_transfer :
      geometry.limiting_variance_formula ->
        variance.known_score_variance_formula)
    (hgodambe : variance.godambe_variance_identity) :
    variance.estimated_score_variance_formula :=
  estimated_score_variance_formula_of_chen_han_reference_bridge
    geometry variance hgeometry_regular hcatchment hknown_variance_transfer
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      variance.score_adjustment_algebra parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret)
    hgodambe

omit [DecidableEq Param] in
/--
Direct Chen-Han reference route for estimated-score normality and variance,
with the variance adjustment discharged by the fixed-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_bridges_fixedLaw_score_adjustment_identity
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualArrayCLTBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (estimated : EstimatedScoreAsymptoticBridge)
    (variance : EstimatedScoreVarianceFormulaBridge)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        variance.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hquad : residual.quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hheterogeneity : known.heterogeneity_clt)
    (hknown_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hlocal : estimated.matching_functional_local_expansion)
    (hgodambe_normality : estimated.godambe_variance_identity)
    (hknown_variance_transfer :
      geometry.limiting_variance_formula ->
        variance.known_score_variance_formula)
    (hgodambe_variance : variance.godambe_variance_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      variance.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_bridges
    geometry radius residual bias known estimated variance hgeometry_regular
    hcatchment hmoment_transfer hresidual_reg hquad hresidual_transfer
    hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
    hbias_transfer hdecomp hden hheterogeneity hknown_transfer hfirst hlocal
    hgodambe_normality hknown_variance_transfer
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      variance.score_adjustment_algebra parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret)
    hgodambe_variance

omit [DecidableEq Param] in
/--
Direct Chen-Han reference route for estimated-score normality and variance,
with the variance adjustment discharged by the changing-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_bridges_changingLaw_score_adjustment_identity
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualArrayCLTBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (estimated : EstimatedScoreAsymptoticBridge)
    (variance : EstimatedScoreVarianceFormulaBridge)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        variance.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hquad : residual.quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hheterogeneity : known.heterogeneity_clt)
    (hknown_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hlocal : estimated.matching_functional_local_expansion)
    (hgodambe_normality : estimated.godambe_variance_identity)
    (hknown_variance_transfer :
      geometry.limiting_variance_formula ->
        variance.known_score_variance_formula)
    (hgodambe_variance : variance.godambe_variance_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      variance.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_bridges
    geometry radius residual bias known estimated variance hgeometry_regular
    hcatchment hmoment_transfer hresidual_reg hquad hresidual_transfer
    hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
    hbias_transfer hdecomp hden hheterogeneity hknown_transfer hfirst hlocal
    hgodambe_normality hknown_variance_transfer
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      variance.score_adjustment_algebra parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret)
    hgodambe_variance

omit [DecidableEq Param] in
/--
Direct Chen-Han local-experiment reference route with the local variance
adjustment discharged by the fixed-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_local_experiment_bridges_fixedLaw_score_adjustment_identity
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualArrayCLTBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hquad : residual.quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hheterogeneity : known.heterogeneity_clt)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      geometry.limiting_variance_formula ->
        estimated.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (hfunctional : estimated.matching_functional_local_derivative)
    (hequicontinuity : estimated.local_stochastic_equicontinuity)
    (hgodambe : estimated.godambe_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_local_experiment_bridges
    geometry radius residual bias known estimated hgeometry_regular
    hcatchment hmoment_transfer hresidual_reg hquad hresidual_transfer
    hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
    hbias_transfer hdecomp hden hheterogeneity hknown_normality_transfer
    hknown_variance_transfer hfirst hscore hfunctional hequicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      estimated.score_adjustment_algebra parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret)
    hgodambe

omit [DecidableEq Param] in
/--
Direct Chen-Han local-experiment reference route with the local variance
adjustment discharged by the changing-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_local_experiment_bridges_changingLaw_score_adjustment_identity
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualArrayCLTBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hquad : residual.quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hheterogeneity : known.heterogeneity_clt)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      geometry.limiting_variance_formula ->
        estimated.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (hfunctional : estimated.matching_functional_local_derivative)
    (hequicontinuity : estimated.local_stochastic_equicontinuity)
    (hgodambe : estimated.godambe_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_local_experiment_bridges
    geometry radius residual bias known estimated hgeometry_regular
    hcatchment hmoment_transfer hresidual_reg hquad hresidual_transfer
    hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
    hbias_transfer hdecomp hden hheterogeneity hknown_normality_transfer
    hknown_variance_transfer hfirst hscore hfunctional hequicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      estimated.score_adjustment_algebra parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret)
    hgodambe

omit [DecidableEq Param] in
/--
Direct Chen-Han local-experiment reference route with the local variance
adjustment discharged by the fixed-law finite identity and the remaining
local-experiment/Godambe obligations packaged as a compact core.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_local_experiment_bridges_fixedLaw_score_adjustment_identity_and_local_experiment_core
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualArrayCLTBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hquad : residual.quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hheterogeneity : known.heterogeneity_clt)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      geometry.limiting_variance_formula ->
        estimated.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (core : EstimatedScoreLocalExperimentVarianceCore estimated) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_local_experiment_bridges_fixedLaw_score_adjustment_identity
    geometry radius residual bias known estimated parameters oracleVariance
    firstStepLoading scoreCovariance hinterpret hgeometry_regular hcatchment
    hmoment_transfer hresidual_reg hquad hresidual_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden hheterogeneity hknown_normality_transfer
    hknown_variance_transfer hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

omit [DecidableEq Param] in
/--
Direct Chen-Han local-experiment reference route with the local variance
adjustment discharged by the changing-law finite identity and the remaining
local-experiment/Godambe obligations packaged as a compact core.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_local_experiment_bridges_changingLaw_score_adjustment_identity_and_local_experiment_core
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualArrayCLTBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hquad : residual.quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hheterogeneity : known.heterogeneity_clt)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      geometry.limiting_variance_formula ->
        estimated.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (core : EstimatedScoreLocalExperimentVarianceCore estimated) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_local_experiment_bridges_changingLaw_score_adjustment_identity
    geometry radius residual bias known estimated parameters oracleVariance
    firstStepLoading targetDriftLoading scoreCovariance hinterpret
    hgeometry_regular hcatchment hmoment_transfer hresidual_reg hquad
    hresidual_transfer hradius_regular hradius_geometry hradius_transfer
    hfinite hlipschitz hbias_transfer hdecomp hden hheterogeneity
    hknown_normality_transfer hknown_variance_transfer hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

omit [DecidableEq Param] in
/--
Direct Chen-Han martingale reference route with the variance adjustment
discharged by the fixed-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_bridges_fixedLaw_score_adjustment_identity
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (estimated : EstimatedScoreAsymptoticBridge)
    (variance : EstimatedScoreVarianceFormulaBridge)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        variance.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
    (hlindeberg : residual.conditional_lindeberg)
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hheterogeneity : known.heterogeneity_clt)
    (hknown_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hlocal : estimated.matching_functional_local_expansion)
    (hgodambe_normality : estimated.godambe_variance_identity)
    (hknown_variance_transfer :
      geometry.limiting_variance_formula ->
        variance.known_score_variance_formula)
    (hgodambe_variance : variance.godambe_variance_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      variance.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_bridges
    geometry radius residual bias known estimated variance hgeometry_regular
    hcatchment hmoment_transfer hresidual_reg hmartingale hlindeberg hquad
    hresidual_transfer hradius_regular hradius_geometry hradius_transfer
    hfinite hlipschitz hbias_transfer hdecomp hden hheterogeneity
    hknown_transfer hfirst hlocal hgodambe_normality
    hknown_variance_transfer
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      variance.score_adjustment_algebra parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret)
    hgodambe_variance

omit [DecidableEq Param] in
/--
Direct Chen-Han martingale reference route with the variance adjustment
discharged by the changing-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_bridges_changingLaw_score_adjustment_identity
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (estimated : EstimatedScoreAsymptoticBridge)
    (variance : EstimatedScoreVarianceFormulaBridge)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        variance.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
    (hlindeberg : residual.conditional_lindeberg)
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hheterogeneity : known.heterogeneity_clt)
    (hknown_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hlocal : estimated.matching_functional_local_expansion)
    (hgodambe_normality : estimated.godambe_variance_identity)
    (hknown_variance_transfer :
      geometry.limiting_variance_formula ->
        variance.known_score_variance_formula)
    (hgodambe_variance : variance.godambe_variance_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      variance.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_bridges
    geometry radius residual bias known estimated variance hgeometry_regular
    hcatchment hmoment_transfer hresidual_reg hmartingale hlindeberg hquad
    hresidual_transfer hradius_regular hradius_geometry hradius_transfer
    hfinite hlipschitz hbias_transfer hdecomp hden hheterogeneity
    hknown_transfer hfirst hlocal hgodambe_normality
    hknown_variance_transfer
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      variance.score_adjustment_algebra parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret)
    hgodambe_variance

omit [DecidableEq Param] in
/--
Direct Chen-Han martingale local-experiment reference route with the local
variance adjustment discharged by the fixed-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_local_experiment_bridges_fixedLaw_score_adjustment_identity
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
    (hlindeberg : residual.conditional_lindeberg)
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hheterogeneity : known.heterogeneity_clt)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      geometry.limiting_variance_formula ->
        estimated.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (hfunctional : estimated.matching_functional_local_derivative)
    (hequicontinuity : estimated.local_stochastic_equicontinuity)
    (hgodambe : estimated.godambe_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_local_experiment_bridges
    geometry radius residual bias known estimated hgeometry_regular
    hcatchment hmoment_transfer hresidual_reg hmartingale hlindeberg hquad
    hresidual_transfer hradius_regular hradius_geometry hradius_transfer
    hfinite hlipschitz hbias_transfer hdecomp hden hheterogeneity
    hknown_normality_transfer hknown_variance_transfer hfirst hscore
    hfunctional hequicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      estimated.score_adjustment_algebra parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret)
    hgodambe

omit [DecidableEq Param] in
/--
Direct Chen-Han martingale local-experiment reference route with the local
variance adjustment discharged by the changing-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_local_experiment_bridges_changingLaw_score_adjustment_identity
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
    (hlindeberg : residual.conditional_lindeberg)
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hheterogeneity : known.heterogeneity_clt)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      geometry.limiting_variance_formula ->
        estimated.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (hfunctional : estimated.matching_functional_local_derivative)
    (hequicontinuity : estimated.local_stochastic_equicontinuity)
    (hgodambe : estimated.godambe_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_local_experiment_bridges
    geometry radius residual bias known estimated hgeometry_regular
    hcatchment hmoment_transfer hresidual_reg hmartingale hlindeberg hquad
    hresidual_transfer hradius_regular hradius_geometry hradius_transfer
    hfinite hlipschitz hbias_transfer hdecomp hden hheterogeneity
    hknown_normality_transfer hknown_variance_transfer hfirst hscore
    hfunctional hequicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      estimated.score_adjustment_algebra parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret)
    hgodambe

omit [DecidableEq Param] in
/--
Direct Chen-Han martingale local-experiment reference route with the local
variance adjustment discharged by the fixed-law finite identity and the
remaining local-experiment/Godambe obligations packaged as a compact core.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_local_experiment_bridges_fixedLaw_score_adjustment_identity_and_local_experiment_core
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
    (hlindeberg : residual.conditional_lindeberg)
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hheterogeneity : known.heterogeneity_clt)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      geometry.limiting_variance_formula ->
        estimated.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (core : EstimatedScoreLocalExperimentVarianceCore estimated) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_local_experiment_bridges_fixedLaw_score_adjustment_identity
    geometry radius residual bias known estimated parameters oracleVariance
    firstStepLoading scoreCovariance hinterpret hgeometry_regular hcatchment
    hmoment_transfer hresidual_reg hmartingale hlindeberg hquad
    hresidual_transfer hradius_regular hradius_geometry hradius_transfer
    hfinite hlipschitz hbias_transfer hdecomp hden hheterogeneity
    hknown_normality_transfer hknown_variance_transfer hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

omit [DecidableEq Param] in
/--
Direct Chen-Han martingale local-experiment reference route with the local
variance adjustment discharged by the changing-law finite identity and the
remaining local-experiment/Godambe obligations packaged as a compact core.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_local_experiment_bridges_changingLaw_score_adjustment_identity_and_local_experiment_core
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
    (hlindeberg : residual.conditional_lindeberg)
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hheterogeneity : known.heterogeneity_clt)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      geometry.limiting_variance_formula ->
        estimated.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (core : EstimatedScoreLocalExperimentVarianceCore estimated) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_local_experiment_bridges_changingLaw_score_adjustment_identity
    geometry radius residual bias known estimated parameters oracleVariance
    firstStepLoading targetDriftLoading scoreCovariance hinterpret
    hgeometry_regular hcatchment hmoment_transfer hresidual_reg hmartingale
    hlindeberg hquad hresidual_transfer hradius_regular hradius_geometry
    hradius_transfer hfinite hlipschitz hbias_transfer hdecomp hden
    hheterogeneity hknown_normality_transfer hknown_variance_transfer hfirst
    hscore core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

omit [DecidableEq Param] in
/--
Chen-Han component-variance reference route with the estimated-score variance
adjustment discharged by the fixed-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_bridges_fixedLaw_score_adjustment_identity
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (estimated : EstimatedScoreAsymptoticBridge)
    (estimatedVariance : EstimatedScoreVarianceFormulaBridge)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        estimatedVariance.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        knownVariance.heterogeneity_variance_formula)
    (hresidual_reg : residual.residual_moment_regularity)
    (hquad : residual.quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (horthogonality : knownVariance.component_orthogonality)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      knownVariance.known_score_variance_formula ->
        estimatedVariance.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hlocal : estimated.matching_functional_local_expansion)
    (hgodambe_normality : estimated.godambe_variance_identity)
    (hgodambe_variance : estimatedVariance.godambe_variance_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimatedVariance.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_bridges
    geometry radius heterogeneity residual bias known knownVariance
    estimated estimatedVariance hgeometry_regular hcatchment hmoment_transfer
    hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hquad hresidual_transfer
    hresidual_variance_transfer hradius_regular hradius_geometry
    hradius_transfer hfinite hlipschitz hbias_transfer hdecomp hden
    horthogonality hknown_normality_transfer hknown_variance_transfer
    hfirst hlocal hgodambe_normality
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      estimatedVariance.score_adjustment_algebra parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret)
    hgodambe_variance

omit [DecidableEq Param] in
/--
Chen-Han component-variance reference route with the estimated-score variance
adjustment discharged by the changing-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_bridges_changingLaw_score_adjustment_identity
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (estimated : EstimatedScoreAsymptoticBridge)
    (estimatedVariance : EstimatedScoreVarianceFormulaBridge)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        estimatedVariance.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        knownVariance.heterogeneity_variance_formula)
    (hresidual_reg : residual.residual_moment_regularity)
    (hquad : residual.quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (horthogonality : knownVariance.component_orthogonality)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      knownVariance.known_score_variance_formula ->
        estimatedVariance.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hlocal : estimated.matching_functional_local_expansion)
    (hgodambe_normality : estimated.godambe_variance_identity)
    (hgodambe_variance : estimatedVariance.godambe_variance_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimatedVariance.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_bridges
    geometry radius heterogeneity residual bias known knownVariance
    estimated estimatedVariance hgeometry_regular hcatchment hmoment_transfer
    hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hquad hresidual_transfer
    hresidual_variance_transfer hradius_regular hradius_geometry
    hradius_transfer hfinite hlipschitz hbias_transfer hdecomp hden
    horthogonality hknown_normality_transfer hknown_variance_transfer
    hfirst hlocal hgodambe_normality
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      estimatedVariance.score_adjustment_algebra parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret)
    hgodambe_variance

omit [DecidableEq Param] in
/--
Chen-Han component local-experiment reference route with the local variance
adjustment discharged by the fixed-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_local_experiment_bridges_fixedLaw_score_adjustment_identity
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        knownVariance.heterogeneity_variance_formula)
    (hresidual_reg : residual.residual_moment_regularity)
    (hquad : residual.quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (horthogonality : knownVariance.component_orthogonality)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      knownVariance.known_score_variance_formula ->
        estimated.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (hfunctional : estimated.matching_functional_local_derivative)
    (hequicontinuity : estimated.local_stochastic_equicontinuity)
    (hgodambe : estimated.godambe_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_local_experiment_bridges
    geometry radius heterogeneity residual bias known knownVariance estimated
    hgeometry_regular hcatchment hmoment_transfer hheterogeneity_moment
    hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hquad hresidual_transfer
    hresidual_variance_transfer hradius_regular hradius_geometry
    hradius_transfer hfinite hlipschitz hbias_transfer hdecomp hden
    horthogonality hknown_normality_transfer hknown_variance_transfer hfirst
    hscore hfunctional hequicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      estimated.score_adjustment_algebra parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret)
    hgodambe

omit [DecidableEq Param] in
/--
Chen-Han component local-experiment reference route with the local variance
adjustment discharged by the changing-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_local_experiment_bridges_changingLaw_score_adjustment_identity
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        knownVariance.heterogeneity_variance_formula)
    (hresidual_reg : residual.residual_moment_regularity)
    (hquad : residual.quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (horthogonality : knownVariance.component_orthogonality)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      knownVariance.known_score_variance_formula ->
        estimated.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (hfunctional : estimated.matching_functional_local_derivative)
    (hequicontinuity : estimated.local_stochastic_equicontinuity)
    (hgodambe : estimated.godambe_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_local_experiment_bridges
    geometry radius heterogeneity residual bias known knownVariance estimated
    hgeometry_regular hcatchment hmoment_transfer hheterogeneity_moment
    hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hquad hresidual_transfer
    hresidual_variance_transfer hradius_regular hradius_geometry
    hradius_transfer hfinite hlipschitz hbias_transfer hdecomp hden
    horthogonality hknown_normality_transfer hknown_variance_transfer hfirst
    hscore hfunctional hequicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      estimated.score_adjustment_algebra parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret)
    hgodambe

omit [DecidableEq Param] in
/--
Chen-Han component local-experiment reference route with the local variance
adjustment discharged by the fixed-law finite identity and the remaining
local-experiment/Godambe obligations packaged as a compact core.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_local_experiment_bridges_fixedLaw_score_adjustment_identity_and_local_experiment_core
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        knownVariance.heterogeneity_variance_formula)
    (hresidual_reg : residual.residual_moment_regularity)
    (hquad : residual.quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (horthogonality : knownVariance.component_orthogonality)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      knownVariance.known_score_variance_formula ->
        estimated.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (core : EstimatedScoreLocalExperimentVarianceCore estimated) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_local_experiment_bridges_fixedLaw_score_adjustment_identity
    geometry radius heterogeneity residual bias known knownVariance estimated
    parameters oracleVariance firstStepLoading scoreCovariance hinterpret
    hgeometry_regular hcatchment hmoment_transfer hheterogeneity_moment
    hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hquad hresidual_transfer
    hresidual_variance_transfer hradius_regular hradius_geometry
    hradius_transfer hfinite hlipschitz hbias_transfer hdecomp hden
    horthogonality hknown_normality_transfer hknown_variance_transfer hfirst
    hscore core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

omit [DecidableEq Param] in
/--
Chen-Han component local-experiment reference route with the local variance
adjustment discharged by the changing-law finite identity and the remaining
local-experiment/Godambe obligations packaged as a compact core.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_local_experiment_bridges_changingLaw_score_adjustment_identity_and_local_experiment_core
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        knownVariance.heterogeneity_variance_formula)
    (hresidual_reg : residual.residual_moment_regularity)
    (hquad : residual.quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (horthogonality : knownVariance.component_orthogonality)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      knownVariance.known_score_variance_formula ->
        estimated.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (core : EstimatedScoreLocalExperimentVarianceCore estimated) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_local_experiment_bridges_changingLaw_score_adjustment_identity
    geometry radius heterogeneity residual bias known knownVariance estimated
    parameters oracleVariance firstStepLoading targetDriftLoading
    scoreCovariance hinterpret hgeometry_regular hcatchment hmoment_transfer
    hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hquad hresidual_transfer
    hresidual_variance_transfer hradius_regular hradius_geometry
    hradius_transfer hfinite hlipschitz hbias_transfer hdecomp hden
    horthogonality hknown_normality_transfer hknown_variance_transfer hfirst
    hscore core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

omit [DecidableEq Param] in
/--
Chen-Han component martingale reference route with the estimated-score
variance adjustment discharged by the fixed-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_bridges_fixedLaw_score_adjustment_identity
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (estimated : EstimatedScoreAsymptoticBridge)
    (estimatedVariance : EstimatedScoreVarianceFormulaBridge)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        estimatedVariance.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        knownVariance.heterogeneity_variance_formula)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
    (hlindeberg : residual.conditional_lindeberg)
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (horthogonality : knownVariance.component_orthogonality)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      knownVariance.known_score_variance_formula ->
        estimatedVariance.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hlocal : estimated.matching_functional_local_expansion)
    (hgodambe_normality : estimated.godambe_variance_identity)
    (hgodambe_variance : estimatedVariance.godambe_variance_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimatedVariance.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_bridges
    geometry radius heterogeneity residual bias known knownVariance estimated
    estimatedVariance hgeometry_regular hcatchment hmoment_transfer
    hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hlindeberg
    hquad hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden horthogonality hknown_normality_transfer
    hknown_variance_transfer hfirst hlocal hgodambe_normality
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      estimatedVariance.score_adjustment_algebra parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret)
    hgodambe_variance

omit [DecidableEq Param] in
/--
Chen-Han component martingale reference route with the estimated-score
variance adjustment discharged by the changing-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_bridges_changingLaw_score_adjustment_identity
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (estimated : EstimatedScoreAsymptoticBridge)
    (estimatedVariance : EstimatedScoreVarianceFormulaBridge)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        estimatedVariance.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        knownVariance.heterogeneity_variance_formula)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
    (hlindeberg : residual.conditional_lindeberg)
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (horthogonality : knownVariance.component_orthogonality)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      knownVariance.known_score_variance_formula ->
        estimatedVariance.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hlocal : estimated.matching_functional_local_expansion)
    (hgodambe_normality : estimated.godambe_variance_identity)
    (hgodambe_variance : estimatedVariance.godambe_variance_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimatedVariance.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_bridges
    geometry radius heterogeneity residual bias known knownVariance estimated
    estimatedVariance hgeometry_regular hcatchment hmoment_transfer
    hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hlindeberg
    hquad hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden horthogonality hknown_normality_transfer
    hknown_variance_transfer hfirst hlocal hgodambe_normality
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      estimatedVariance.score_adjustment_algebra parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret)
    hgodambe_variance

omit [DecidableEq Param] in
/--
Chen-Han component martingale local-experiment reference route with the local
variance adjustment discharged by the fixed-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_bridges_fixedLaw_score_adjustment_identity
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        knownVariance.heterogeneity_variance_formula)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
    (hlindeberg : residual.conditional_lindeberg)
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (horthogonality : knownVariance.component_orthogonality)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      knownVariance.known_score_variance_formula ->
        estimated.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (hfunctional : estimated.matching_functional_local_derivative)
    (hequicontinuity : estimated.local_stochastic_equicontinuity)
    (hgodambe : estimated.godambe_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_bridges
    geometry radius heterogeneity residual bias known knownVariance estimated
    hgeometry_regular hcatchment hmoment_transfer hheterogeneity_moment
    hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hlindeberg
    hquad hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden horthogonality hknown_normality_transfer
    hknown_variance_transfer hfirst hscore hfunctional hequicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      estimated.score_adjustment_algebra parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret)
    hgodambe

omit [DecidableEq Param] in
/--
Chen-Han component martingale local-experiment reference route with the local
variance adjustment discharged by the changing-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_bridges_changingLaw_score_adjustment_identity
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        knownVariance.heterogeneity_variance_formula)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
    (hlindeberg : residual.conditional_lindeberg)
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (horthogonality : knownVariance.component_orthogonality)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      knownVariance.known_score_variance_formula ->
        estimated.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (hfunctional : estimated.matching_functional_local_derivative)
    (hequicontinuity : estimated.local_stochastic_equicontinuity)
    (hgodambe : estimated.godambe_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_bridges
    geometry radius heterogeneity residual bias known knownVariance estimated
    hgeometry_regular hcatchment hmoment_transfer hheterogeneity_moment
    hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hlindeberg
    hquad hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden horthogonality hknown_normality_transfer
    hknown_variance_transfer hfirst hscore hfunctional hequicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      estimated.score_adjustment_algebra parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret)
    hgodambe

omit [DecidableEq Param] in
/--
Chen-Han component martingale local-experiment reference route with the local
variance adjustment discharged by the fixed-law finite identity and the
remaining local-experiment/Godambe obligations packaged as a compact core.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_bridges_fixedLaw_score_adjustment_identity_and_local_experiment_core
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        knownVariance.heterogeneity_variance_formula)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
    (hlindeberg : residual.conditional_lindeberg)
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (horthogonality : knownVariance.component_orthogonality)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      knownVariance.known_score_variance_formula ->
        estimated.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (core : EstimatedScoreLocalExperimentVarianceCore estimated) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_bridges_fixedLaw_score_adjustment_identity
    geometry radius heterogeneity residual bias known knownVariance estimated
    parameters oracleVariance firstStepLoading scoreCovariance hinterpret
    hgeometry_regular hcatchment hmoment_transfer hheterogeneity_moment
    hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hlindeberg
    hquad hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden horthogonality hknown_normality_transfer
    hknown_variance_transfer hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

omit [DecidableEq Param] in
/--
Chen-Han component martingale local-experiment reference route with the local
variance adjustment discharged by the changing-law finite identity and the
remaining local-experiment/Godambe obligations packaged as a compact core.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_bridges_changingLaw_score_adjustment_identity_and_local_experiment_core
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        knownVariance.heterogeneity_variance_formula)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
    (hlindeberg : residual.conditional_lindeberg)
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (horthogonality : knownVariance.component_orthogonality)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      knownVariance.known_score_variance_formula ->
        estimated.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (core : EstimatedScoreLocalExperimentVarianceCore estimated) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_bridges_changingLaw_score_adjustment_identity
    geometry radius heterogeneity residual bias known knownVariance estimated
    parameters oracleVariance firstStepLoading targetDriftLoading
    scoreCovariance hinterpret hgeometry_regular hcatchment hmoment_transfer
    hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hlindeberg
    hquad hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden horthogonality hknown_normality_transfer
    hknown_variance_transfer hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

omit [DecidableEq Param] in
/--
Chen-Han component design-cross-zero reference route with the estimated-score
variance adjustment discharged by the fixed-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_bridges_design_cross_zero_fixedLaw_score_adjustment_identity
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge knownVariance)
    (estimated : EstimatedScoreAsymptoticBridge)
    (estimatedVariance : EstimatedScoreVarianceFormulaBridge)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        estimatedVariance.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        knownVariance.heterogeneity_variance_formula)
    (hresidual_reg : residual.residual_moment_regularity)
    (hquad : residual.quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hcross : orthogonality.population_design_cross_terms_zero)
    (hlimit : orthogonality.limiting_cross_covariance_zero)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      knownVariance.known_score_variance_formula ->
        estimatedVariance.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hlocal : estimated.matching_functional_local_expansion)
    (hgodambe_normality : estimated.godambe_variance_identity)
    (hgodambe_variance : estimatedVariance.godambe_variance_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimatedVariance.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_bridges_design_cross_zero
    geometry radius heterogeneity residual bias known knownVariance
    orthogonality estimated estimatedVariance hgeometry_regular hcatchment
    hmoment_transfer hheterogeneity_moment hheterogeneity_variance
    hheterogeneity_transfer hheterogeneity_variance_transfer hresidual_reg
    hquad hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden hcross hlimit hknown_normality_transfer
    hknown_variance_transfer hfirst hlocal hgodambe_normality
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      estimatedVariance.score_adjustment_algebra parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret)
    hgodambe_variance

omit [DecidableEq Param] in
/--
Chen-Han component design-cross-zero reference route with the estimated-score
variance adjustment discharged by the changing-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_bridges_design_cross_zero_changingLaw_score_adjustment_identity
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge knownVariance)
    (estimated : EstimatedScoreAsymptoticBridge)
    (estimatedVariance : EstimatedScoreVarianceFormulaBridge)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        estimatedVariance.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        knownVariance.heterogeneity_variance_formula)
    (hresidual_reg : residual.residual_moment_regularity)
    (hquad : residual.quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hcross : orthogonality.population_design_cross_terms_zero)
    (hlimit : orthogonality.limiting_cross_covariance_zero)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      knownVariance.known_score_variance_formula ->
        estimatedVariance.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hlocal : estimated.matching_functional_local_expansion)
    (hgodambe_normality : estimated.godambe_variance_identity)
    (hgodambe_variance : estimatedVariance.godambe_variance_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimatedVariance.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_bridges_design_cross_zero
    geometry radius heterogeneity residual bias known knownVariance
    orthogonality estimated estimatedVariance hgeometry_regular hcatchment
    hmoment_transfer hheterogeneity_moment hheterogeneity_variance
    hheterogeneity_transfer hheterogeneity_variance_transfer hresidual_reg
    hquad hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden hcross hlimit hknown_normality_transfer
    hknown_variance_transfer hfirst hlocal hgodambe_normality
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      estimatedVariance.score_adjustment_algebra parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret)
    hgodambe_variance

omit [DecidableEq Param] in
/--
Chen-Han component design-cross-zero local-experiment reference route with the
local variance adjustment discharged by the fixed-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_local_experiment_bridges_design_cross_zero_fixedLaw_score_adjustment_identity
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge knownVariance)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        knownVariance.heterogeneity_variance_formula)
    (hresidual_reg : residual.residual_moment_regularity)
    (hquad : residual.quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hcross : orthogonality.population_design_cross_terms_zero)
    (hlimit : orthogonality.limiting_cross_covariance_zero)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      knownVariance.known_score_variance_formula ->
        estimated.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (hfunctional : estimated.matching_functional_local_derivative)
    (hequicontinuity : estimated.local_stochastic_equicontinuity)
    (hgodambe : estimated.godambe_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_local_experiment_bridges_design_cross_zero
    geometry radius heterogeneity residual bias known knownVariance
    orthogonality estimated hgeometry_regular hcatchment hmoment_transfer
    hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hquad hresidual_transfer
    hresidual_variance_transfer hradius_regular hradius_geometry
    hradius_transfer hfinite hlipschitz hbias_transfer hdecomp hden hcross
    hlimit hknown_normality_transfer hknown_variance_transfer hfirst hscore
    hfunctional hequicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      estimated.score_adjustment_algebra parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret)
    hgodambe

omit [DecidableEq Param] in
/--
Chen-Han component design-cross-zero local-experiment reference route with the
local variance adjustment discharged by the changing-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_local_experiment_bridges_design_cross_zero_changingLaw_score_adjustment_identity
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge knownVariance)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        knownVariance.heterogeneity_variance_formula)
    (hresidual_reg : residual.residual_moment_regularity)
    (hquad : residual.quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hcross : orthogonality.population_design_cross_terms_zero)
    (hlimit : orthogonality.limiting_cross_covariance_zero)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      knownVariance.known_score_variance_formula ->
        estimated.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (hfunctional : estimated.matching_functional_local_derivative)
    (hequicontinuity : estimated.local_stochastic_equicontinuity)
    (hgodambe : estimated.godambe_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_local_experiment_bridges_design_cross_zero
    geometry radius heterogeneity residual bias known knownVariance
    orthogonality estimated hgeometry_regular hcatchment hmoment_transfer
    hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hquad hresidual_transfer
    hresidual_variance_transfer hradius_regular hradius_geometry
    hradius_transfer hfinite hlipschitz hbias_transfer hdecomp hden hcross
    hlimit hknown_normality_transfer hknown_variance_transfer hfirst hscore
    hfunctional hequicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      estimated.score_adjustment_algebra parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret)
    hgodambe

omit [DecidableEq Param] in
/--
Chen-Han component design-cross-zero local-experiment reference route with the
local variance adjustment discharged by the fixed-law finite identity and the
remaining local-experiment/Godambe obligations packaged as a compact core.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_local_experiment_bridges_design_cross_zero_fixedLaw_score_adjustment_identity_and_local_experiment_core
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge knownVariance)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        knownVariance.heterogeneity_variance_formula)
    (hresidual_reg : residual.residual_moment_regularity)
    (hquad : residual.quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hcross : orthogonality.population_design_cross_terms_zero)
    (hlimit : orthogonality.limiting_cross_covariance_zero)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      knownVariance.known_score_variance_formula ->
        estimated.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (core : EstimatedScoreLocalExperimentVarianceCore estimated) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_local_experiment_bridges_design_cross_zero_fixedLaw_score_adjustment_identity
    geometry radius heterogeneity residual bias known knownVariance
    orthogonality estimated parameters oracleVariance firstStepLoading
    scoreCovariance hinterpret hgeometry_regular hcatchment hmoment_transfer
    hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hquad hresidual_transfer
    hresidual_variance_transfer hradius_regular hradius_geometry
    hradius_transfer hfinite hlipschitz hbias_transfer hdecomp hden hcross
    hlimit hknown_normality_transfer hknown_variance_transfer hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

omit [DecidableEq Param] in
/--
Chen-Han component design-cross-zero local-experiment reference route with the
local variance adjustment discharged by the changing-law finite identity and
the remaining local-experiment/Godambe obligations packaged as a compact core.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_local_experiment_bridges_design_cross_zero_changingLaw_score_adjustment_identity_and_local_experiment_core
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge knownVariance)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        knownVariance.heterogeneity_variance_formula)
    (hresidual_reg : residual.residual_moment_regularity)
    (hquad : residual.quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hcross : orthogonality.population_design_cross_terms_zero)
    (hlimit : orthogonality.limiting_cross_covariance_zero)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      knownVariance.known_score_variance_formula ->
        estimated.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (core : EstimatedScoreLocalExperimentVarianceCore estimated) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_local_experiment_bridges_design_cross_zero_changingLaw_score_adjustment_identity
    geometry radius heterogeneity residual bias known knownVariance
    orthogonality estimated parameters oracleVariance firstStepLoading
    targetDriftLoading scoreCovariance hinterpret hgeometry_regular hcatchment
    hmoment_transfer hheterogeneity_moment hheterogeneity_variance
    hheterogeneity_transfer hheterogeneity_variance_transfer hresidual_reg
    hquad hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden hcross hlimit hknown_normality_transfer
    hknown_variance_transfer hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

omit [DecidableEq Param] in
/--
Chen-Han component design-cross-zero martingale reference route with the
estimated-score variance adjustment discharged by the fixed-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_bridges_design_cross_zero_fixedLaw_score_adjustment_identity
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge knownVariance)
    (estimated : EstimatedScoreAsymptoticBridge)
    (estimatedVariance : EstimatedScoreVarianceFormulaBridge)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        estimatedVariance.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        knownVariance.heterogeneity_variance_formula)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
    (hlindeberg : residual.conditional_lindeberg)
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hcross : orthogonality.population_design_cross_terms_zero)
    (hlimit : orthogonality.limiting_cross_covariance_zero)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      knownVariance.known_score_variance_formula ->
        estimatedVariance.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hlocal : estimated.matching_functional_local_expansion)
    (hgodambe_normality : estimated.godambe_variance_identity)
    (hgodambe_variance : estimatedVariance.godambe_variance_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimatedVariance.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_bridges_design_cross_zero
    geometry radius heterogeneity residual bias known knownVariance
    orthogonality estimated estimatedVariance hgeometry_regular hcatchment
    hmoment_transfer hheterogeneity_moment hheterogeneity_variance
    hheterogeneity_transfer hheterogeneity_variance_transfer hresidual_reg
    hmartingale hlindeberg hquad hresidual_transfer
    hresidual_variance_transfer hradius_regular hradius_geometry
    hradius_transfer hfinite hlipschitz hbias_transfer hdecomp hden hcross
    hlimit hknown_normality_transfer hknown_variance_transfer hfirst hlocal
    hgodambe_normality
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      estimatedVariance.score_adjustment_algebra parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret)
    hgodambe_variance

omit [DecidableEq Param] in
/--
Chen-Han component design-cross-zero martingale reference route with the
estimated-score variance adjustment discharged by the changing-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_bridges_design_cross_zero_changingLaw_score_adjustment_identity
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge knownVariance)
    (estimated : EstimatedScoreAsymptoticBridge)
    (estimatedVariance : EstimatedScoreVarianceFormulaBridge)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        estimatedVariance.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        knownVariance.heterogeneity_variance_formula)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
    (hlindeberg : residual.conditional_lindeberg)
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hcross : orthogonality.population_design_cross_terms_zero)
    (hlimit : orthogonality.limiting_cross_covariance_zero)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      knownVariance.known_score_variance_formula ->
        estimatedVariance.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hlocal : estimated.matching_functional_local_expansion)
    (hgodambe_normality : estimated.godambe_variance_identity)
    (hgodambe_variance : estimatedVariance.godambe_variance_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimatedVariance.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_bridges_design_cross_zero
    geometry radius heterogeneity residual bias known knownVariance
    orthogonality estimated estimatedVariance hgeometry_regular hcatchment
    hmoment_transfer hheterogeneity_moment hheterogeneity_variance
    hheterogeneity_transfer hheterogeneity_variance_transfer hresidual_reg
    hmartingale hlindeberg hquad hresidual_transfer
    hresidual_variance_transfer hradius_regular hradius_geometry
    hradius_transfer hfinite hlipschitz hbias_transfer hdecomp hden hcross
    hlimit hknown_normality_transfer hknown_variance_transfer hfirst hlocal
    hgodambe_normality
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      estimatedVariance.score_adjustment_algebra parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret)
    hgodambe_variance

omit [DecidableEq Param] in
/--
Chen-Han component design-cross-zero martingale local-experiment route with
the local variance adjustment discharged by the fixed-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_bridges_design_cross_zero_fixedLaw_score_adjustment_identity
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge knownVariance)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        knownVariance.heterogeneity_variance_formula)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
    (hlindeberg : residual.conditional_lindeberg)
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hcross : orthogonality.population_design_cross_terms_zero)
    (hlimit : orthogonality.limiting_cross_covariance_zero)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      knownVariance.known_score_variance_formula ->
        estimated.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (hfunctional : estimated.matching_functional_local_derivative)
    (hequicontinuity : estimated.local_stochastic_equicontinuity)
    (hgodambe : estimated.godambe_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_bridges_design_cross_zero
    geometry radius heterogeneity residual bias known knownVariance
    orthogonality estimated hgeometry_regular hcatchment hmoment_transfer
    hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hlindeberg
    hquad hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden hcross hlimit hknown_normality_transfer
    hknown_variance_transfer hfirst hscore hfunctional hequicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      estimated.score_adjustment_algebra parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret)
    hgodambe

omit [DecidableEq Param] in
/--
Chen-Han component design-cross-zero martingale local-experiment route with
the local variance adjustment discharged by the changing-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_bridges_design_cross_zero_changingLaw_score_adjustment_identity
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge knownVariance)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        knownVariance.heterogeneity_variance_formula)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
    (hlindeberg : residual.conditional_lindeberg)
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hcross : orthogonality.population_design_cross_terms_zero)
    (hlimit : orthogonality.limiting_cross_covariance_zero)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      knownVariance.known_score_variance_formula ->
        estimated.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (hfunctional : estimated.matching_functional_local_derivative)
    (hequicontinuity : estimated.local_stochastic_equicontinuity)
    (hgodambe : estimated.godambe_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_bridges_design_cross_zero
    geometry radius heterogeneity residual bias known knownVariance
    orthogonality estimated hgeometry_regular hcatchment hmoment_transfer
    hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hlindeberg
    hquad hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden hcross hlimit hknown_normality_transfer
    hknown_variance_transfer hfirst hscore hfunctional hequicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      estimated.score_adjustment_algebra parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret)
    hgodambe

omit [DecidableEq Param] in
/--
Chen-Han component design-cross-zero martingale local-experiment route with
the local variance adjustment discharged by the fixed-law finite identity and
the remaining local-experiment/Godambe obligations packaged as a compact core.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_bridges_design_cross_zero_fixedLaw_score_adjustment_identity_and_local_experiment_core
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge knownVariance)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        knownVariance.heterogeneity_variance_formula)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
    (hlindeberg : residual.conditional_lindeberg)
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hcross : orthogonality.population_design_cross_terms_zero)
    (hlimit : orthogonality.limiting_cross_covariance_zero)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      knownVariance.known_score_variance_formula ->
        estimated.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (core : EstimatedScoreLocalExperimentVarianceCore estimated) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_bridges_design_cross_zero_fixedLaw_score_adjustment_identity
    geometry radius heterogeneity residual bias known knownVariance
    orthogonality estimated parameters oracleVariance firstStepLoading
    scoreCovariance hinterpret hgeometry_regular hcatchment hmoment_transfer
    hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hlindeberg
    hquad hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden hcross hlimit hknown_normality_transfer
    hknown_variance_transfer hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

omit [DecidableEq Param] in
/--
Chen-Han component design-cross-zero martingale local-experiment route with
the local variance adjustment discharged by the changing-law finite identity
and the remaining local-experiment/Godambe obligations packaged as a compact
core.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_bridges_design_cross_zero_changingLaw_score_adjustment_identity_and_local_experiment_core
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge knownVariance)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        knownVariance.heterogeneity_variance_formula)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
    (hlindeberg : residual.conditional_lindeberg)
    (hquad : residual.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        knownVariance.residual_variance_formula)
    (hradius_regular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular)
    (hbias_transfer :
      bias.matching_discrepancy_negligible ->
        known.matching_discrepancy_negligible)
    (hdecomp : known.aggregate_hajek_decomposition)
    (hden : known.denominator_stabilization)
    (hcross : orthogonality.population_design_cross_terms_zero)
    (hlimit : orthogonality.limiting_cross_covariance_zero)
    (hknown_normality_transfer :
      known.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hknown_variance_transfer :
      knownVariance.known_score_variance_formula ->
        estimated.known_score_variance_formula)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (core : EstimatedScoreLocalExperimentVarianceCore estimated) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_bridges_design_cross_zero_changingLaw_score_adjustment_identity
    geometry radius heterogeneity residual bias known knownVariance
    orthogonality estimated parameters oracleVariance firstStepLoading
    targetDriftLoading scoreCovariance hinterpret hgeometry_regular hcatchment
    hmoment_transfer hheterogeneity_moment hheterogeneity_variance
    hheterogeneity_transfer hheterogeneity_variance_transfer hresidual_reg
    hmartingale hlindeberg hquad hresidual_transfer
    hresidual_variance_transfer hradius_regular hradius_geometry
    hradius_transfer hfinite hlipschitz hbias_transfer hdecomp hden hcross
    hlimit hknown_normality_transfer hknown_variance_transfer hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

end WDSM
end Matching
end StatInference
