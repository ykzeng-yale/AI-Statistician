import StatInference.Matching.WDSM.ReferenceTheoremsResidualLindebergRefinement
import StatInference.Matching.WDSM.EstimatedScoreLocalExperimentVarianceRefinement

/-!
# Combined residual-Lindeberg and score-adjustment refinements

This module composes the two current blocker-reduction lanes for Chen-Han
reference routes.  The wrappers below replace both a raw residual
`conditional_lindeberg` premise and a naked `score_adjustment_algebra` premise
with concrete WDSM inputs.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Param Index Treated Control : Type*} [DecidableEq Param]
variable {l : Filter Index}

omit [DecidableEq Param] in
/--
Direct Chen-Han martingale reference route with Lindeberg discharged by concrete
two-arm envelope bounds and the variance adjustment discharged by the fixed-law
finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_twoArm_envelope_lindeberg_fixedLaw_score_adjustment_identity
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
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
    (hgodambe_variance : variance.godambe_variance_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index)
    (hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index)
    (htreatedEnvelopeBound :
      Tendsto
        (fun index =>
          treatedEnvelope index ^ 3 *
            residualThirdMomentSum (treatedSample index)
              (treatedWeight index) (treatedResidual index))
        l (nhds 0))
    (hcontrolEnvelopeBound :
      Tendsto
        (fun index =>
          controlEnvelope index ^ 3 *
            residualThirdMomentSum (controlSample index)
              (controlWeight index) (controlResidual index))
        l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      variance.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_twoArm_envelope_lindeberg_bridges
    (l := l) treatedSample controlSample treatedWeight treatedCoefficient
    treatedResidual controlWeight controlCoefficient controlResidual
    treatedEnvelope controlEnvelope geometry radius residual bias known
    estimated variance hinputLindeberg hgeometry_regular hcatchment
    hmoment_transfer hresidual_reg hmartingale hquad hresidual_transfer
    hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
    hbias_transfer hdecomp hden hheterogeneity hknown_transfer hfirst hlocal
    hgodambe_normality hknown_variance_transfer
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      variance.score_adjustment_algebra parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret)
    hgodambe_variance htreatedWeightNonneg hcontrolWeightNonneg
    htreatedCoeffBound hcontrolCoeffBound htreatedEnvelopeBound
    hcontrolEnvelopeBound

omit [DecidableEq Param] in
/--
Direct Chen-Han martingale reference route with Lindeberg discharged by concrete
two-arm envelope bounds and the variance adjustment discharged by the
changing-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_twoArm_envelope_lindeberg_changingLaw_score_adjustment_identity
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
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
    (hgodambe_variance : variance.godambe_variance_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index)
    (hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index)
    (htreatedEnvelopeBound :
      Tendsto
        (fun index =>
          treatedEnvelope index ^ 3 *
            residualThirdMomentSum (treatedSample index)
              (treatedWeight index) (treatedResidual index))
        l (nhds 0))
    (hcontrolEnvelopeBound :
      Tendsto
        (fun index =>
          controlEnvelope index ^ 3 *
            residualThirdMomentSum (controlSample index)
              (controlWeight index) (controlResidual index))
        l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      variance.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_twoArm_envelope_lindeberg_bridges
    (l := l) treatedSample controlSample treatedWeight treatedCoefficient
    treatedResidual controlWeight controlCoefficient controlResidual
    treatedEnvelope controlEnvelope geometry radius residual bias known
    estimated variance hinputLindeberg hgeometry_regular hcatchment
    hmoment_transfer hresidual_reg hmartingale hquad hresidual_transfer
    hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
    hbias_transfer hdecomp hden hheterogeneity hknown_transfer hfirst hlocal
    hgodambe_normality hknown_variance_transfer
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      variance.score_adjustment_algebra parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret)
    hgodambe_variance htreatedWeightNonneg hcontrolWeightNonneg
    htreatedCoeffBound hcontrolCoeffBound htreatedEnvelopeBound
    hcontrolEnvelopeBound

omit [DecidableEq Param] in
/--
Direct Chen-Han martingale local-experiment route with Lindeberg discharged by
concrete two-arm envelope bounds and the local variance adjustment discharged by
the fixed-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_local_experiment_twoArm_envelope_lindeberg_fixedLaw_score_adjustment_identity
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
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
    (hgodambe : estimated.godambe_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index)
    (hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index)
    (htreatedEnvelopeBound :
      Tendsto
        (fun index =>
          treatedEnvelope index ^ 3 *
            residualThirdMomentSum (treatedSample index)
              (treatedWeight index) (treatedResidual index))
        l (nhds 0))
    (hcontrolEnvelopeBound :
      Tendsto
        (fun index =>
          controlEnvelope index ^ 3 *
            residualThirdMomentSum (controlSample index)
              (controlWeight index) (controlResidual index))
        l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_local_experiment_twoArm_envelope_lindeberg_bridges
    (l := l) treatedSample controlSample treatedWeight treatedCoefficient
    treatedResidual controlWeight controlCoefficient controlResidual
    treatedEnvelope controlEnvelope geometry radius residual bias known
    estimated hinputLindeberg hgeometry_regular hcatchment hmoment_transfer
    hresidual_reg hmartingale hquad hresidual_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden hheterogeneity hknown_normality_transfer
    hknown_variance_transfer hfirst hscore hfunctional hequicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      estimated.score_adjustment_algebra parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret)
    hgodambe htreatedWeightNonneg hcontrolWeightNonneg htreatedCoeffBound
    hcontrolCoeffBound htreatedEnvelopeBound hcontrolEnvelopeBound

omit [DecidableEq Param] in
/--
Direct Chen-Han martingale local-experiment route with Lindeberg discharged by
concrete two-arm envelope bounds and the local variance adjustment discharged by
the changing-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_local_experiment_twoArm_envelope_lindeberg_changingLaw_score_adjustment_identity
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
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
    (hgodambe : estimated.godambe_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index)
    (hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index)
    (htreatedEnvelopeBound :
      Tendsto
        (fun index =>
          treatedEnvelope index ^ 3 *
            residualThirdMomentSum (treatedSample index)
              (treatedWeight index) (treatedResidual index))
        l (nhds 0))
    (hcontrolEnvelopeBound :
      Tendsto
        (fun index =>
          controlEnvelope index ^ 3 *
            residualThirdMomentSum (controlSample index)
              (controlWeight index) (controlResidual index))
        l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_local_experiment_twoArm_envelope_lindeberg_bridges
    (l := l) treatedSample controlSample treatedWeight treatedCoefficient
    treatedResidual controlWeight controlCoefficient controlResidual
    treatedEnvelope controlEnvelope geometry radius residual bias known
    estimated hinputLindeberg hgeometry_regular hcatchment hmoment_transfer
    hresidual_reg hmartingale hquad hresidual_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden hheterogeneity hknown_normality_transfer
    hknown_variance_transfer hfirst hscore hfunctional hequicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      estimated.score_adjustment_algebra parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret)
    hgodambe htreatedWeightNonneg hcontrolWeightNonneg htreatedCoeffBound
    hcontrolCoeffBound htreatedEnvelopeBound hcontrolEnvelopeBound

omit [DecidableEq Param] in
/--
Direct Chen-Han martingale local-experiment route with Lindeberg discharged by
concrete two-arm envelope bounds, fixed-law score-adjustment algebra supplied
by the finite identity, and the remaining local-experiment/Godambe obligations
packaged as a compact core.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_local_experiment_twoArm_envelope_lindeberg_fixedLaw_score_adjustment_identity_and_local_experiment_core
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
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
    (core : EstimatedScoreLocalExperimentVarianceCore estimated)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index)
    (hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index)
    (htreatedEnvelopeBound :
      Tendsto
        (fun index =>
          treatedEnvelope index ^ 3 *
            residualThirdMomentSum (treatedSample index)
              (treatedWeight index) (treatedResidual index))
        l (nhds 0))
    (hcontrolEnvelopeBound :
      Tendsto
        (fun index =>
          controlEnvelope index ^ 3 *
            residualThirdMomentSum (controlSample index)
              (controlWeight index) (controlResidual index))
        l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_local_experiment_twoArm_envelope_lindeberg_fixedLaw_score_adjustment_identity
    (l := l) treatedSample controlSample treatedWeight treatedCoefficient
    treatedResidual controlWeight controlCoefficient controlResidual
    treatedEnvelope controlEnvelope geometry radius residual bias known
    estimated parameters oracleVariance firstStepLoading scoreCovariance
    hinterpret hinputLindeberg hgeometry_regular hcatchment hmoment_transfer
    hresidual_reg hmartingale hquad hresidual_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden hheterogeneity hknown_normality_transfer
    hknown_variance_transfer hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity
    htreatedWeightNonneg hcontrolWeightNonneg htreatedCoeffBound
    hcontrolCoeffBound htreatedEnvelopeBound hcontrolEnvelopeBound

omit [DecidableEq Param] in
/--
Direct Chen-Han martingale local-experiment route with Lindeberg discharged by
concrete two-arm envelope bounds, changing-law score-adjustment algebra
supplied by the finite identity, and the remaining local-experiment/Godambe
obligations packaged as a compact core.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_local_experiment_twoArm_envelope_lindeberg_changingLaw_score_adjustment_identity_and_local_experiment_core
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
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
    (core : EstimatedScoreLocalExperimentVarianceCore estimated)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index)
    (hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index)
    (htreatedEnvelopeBound :
      Tendsto
        (fun index =>
          treatedEnvelope index ^ 3 *
            residualThirdMomentSum (treatedSample index)
              (treatedWeight index) (treatedResidual index))
        l (nhds 0))
    (hcontrolEnvelopeBound :
      Tendsto
        (fun index =>
          controlEnvelope index ^ 3 *
            residualThirdMomentSum (controlSample index)
              (controlWeight index) (controlResidual index))
        l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_local_experiment_twoArm_envelope_lindeberg_changingLaw_score_adjustment_identity
    (l := l) treatedSample controlSample treatedWeight treatedCoefficient
    treatedResidual controlWeight controlCoefficient controlResidual
    treatedEnvelope controlEnvelope geometry radius residual bias known
    estimated parameters oracleVariance firstStepLoading targetDriftLoading
    scoreCovariance hinterpret hinputLindeberg hgeometry_regular hcatchment
    hmoment_transfer hresidual_reg hmartingale hquad hresidual_transfer
    hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
    hbias_transfer hdecomp hden hheterogeneity hknown_normality_transfer
    hknown_variance_transfer hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity
    htreatedWeightNonneg hcontrolWeightNonneg htreatedCoeffBound
    hcontrolCoeffBound htreatedEnvelopeBound hcontrolEnvelopeBound

variable {TreatedCell ControlCell : Type*}
  [DecidableEq TreatedCell] [DecidableEq ControlCell]

omit [DecidableEq Param] in
/--
Direct Chen-Han martingale reference route with Lindeberg supplied by finite
score-cell coefficient loadings and the variance adjustment discharged by the
fixed-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_finite_scoreCell_lindeberg_fixedLaw_score_adjustment_identity
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficientLoading : Index -> TreatedCell -> Real)
    (controlCoefficientLoading : Index -> ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
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
    (hgodambe_variance : variance.godambe_variance_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoverEventually :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCoverEventually :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCover :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ index control, control ∈ controlSample index ->
        controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedCoefficientLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlCoefficientLoading index (controlScore index control))
    (htreatedCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedCoefficientLoading index cell| ≤ treatedEnvelope index)
    (hcontrolCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlCoefficientLoading index cell| ≤ controlEnvelope index)
    (htreatedThirdLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedThirdMomentLoading (treatedScore index treated) =
          |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ index control, control ∈ controlSample index ->
        controlThirdMomentLoading (controlScore index control) =
          |controlResidual index control| ^ 3)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit)
    (htreatedEnvelope : Tendsto treatedEnvelope l (nhds 0))
    (hcontrolEnvelope : Tendsto controlEnvelope l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      variance.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_finite_scoreCell_lindeberg_bridges
    (l := l) treatedCells controlCells treatedSample controlSample
    treatedWeight treatedCoefficient treatedResidual controlWeight
    controlCoefficient controlResidual treatedScore controlScore
    treatedCoefficientLoading controlCoefficientLoading
    treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
    controlMassLimit treatedEnvelope controlEnvelope geometry radius residual
    bias known estimated variance hinputLindeberg hgeometry_regular hcatchment
    hmoment_transfer hresidual_reg hmartingale hquad hresidual_transfer
    hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
    hbias_transfer hdecomp hden hheterogeneity hknown_transfer hfirst hlocal
    hgodambe_normality hknown_variance_transfer
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      variance.score_adjustment_algebra parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret)
    hgodambe_variance htreatedWeightNonneg hcontrolWeightNonneg
    htreatedCoverEventually hcontrolCoverEventually htreatedCover
    hcontrolCover htreatedCoefficient hcontrolCoefficient
    htreatedCoefficientLoadingBound hcontrolCoefficientLoadingBound
    htreatedThirdLoading hcontrolThirdLoading htreatedMass hcontrolMass
    htreatedEnvelope hcontrolEnvelope

omit [DecidableEq Param] in
/--
Direct Chen-Han martingale reference route with Lindeberg supplied by finite
score-cell coefficient loadings and the variance adjustment discharged by the
changing-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_finite_scoreCell_lindeberg_changingLaw_score_adjustment_identity
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficientLoading : Index -> TreatedCell -> Real)
    (controlCoefficientLoading : Index -> ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
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
    (hgodambe_variance : variance.godambe_variance_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoverEventually :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCoverEventually :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCover :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ index control, control ∈ controlSample index ->
        controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedCoefficientLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlCoefficientLoading index (controlScore index control))
    (htreatedCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedCoefficientLoading index cell| ≤ treatedEnvelope index)
    (hcontrolCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlCoefficientLoading index cell| ≤ controlEnvelope index)
    (htreatedThirdLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedThirdMomentLoading (treatedScore index treated) =
          |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ index control, control ∈ controlSample index ->
        controlThirdMomentLoading (controlScore index control) =
          |controlResidual index control| ^ 3)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit)
    (htreatedEnvelope : Tendsto treatedEnvelope l (nhds 0))
    (hcontrolEnvelope : Tendsto controlEnvelope l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      variance.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_finite_scoreCell_lindeberg_bridges
    (l := l) treatedCells controlCells treatedSample controlSample
    treatedWeight treatedCoefficient treatedResidual controlWeight
    controlCoefficient controlResidual treatedScore controlScore
    treatedCoefficientLoading controlCoefficientLoading
    treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
    controlMassLimit treatedEnvelope controlEnvelope geometry radius residual
    bias known estimated variance hinputLindeberg hgeometry_regular hcatchment
    hmoment_transfer hresidual_reg hmartingale hquad hresidual_transfer
    hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
    hbias_transfer hdecomp hden hheterogeneity hknown_transfer hfirst hlocal
    hgodambe_normality hknown_variance_transfer
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      variance.score_adjustment_algebra parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret)
    hgodambe_variance htreatedWeightNonneg hcontrolWeightNonneg
    htreatedCoverEventually hcontrolCoverEventually htreatedCover
    hcontrolCover htreatedCoefficient hcontrolCoefficient
    htreatedCoefficientLoadingBound hcontrolCoefficientLoadingBound
    htreatedThirdLoading hcontrolThirdLoading htreatedMass hcontrolMass
    htreatedEnvelope hcontrolEnvelope

omit [DecidableEq Param] in
/--
Direct Chen-Han martingale local-experiment route with Lindeberg supplied by
finite score-cell coefficient loadings and the local variance adjustment
discharged by the fixed-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_local_experiment_finite_scoreCell_lindeberg_fixedLaw_score_adjustment_identity
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficientLoading : Index -> TreatedCell -> Real)
    (controlCoefficientLoading : Index -> ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
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
    (hgodambe : estimated.godambe_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoverEventually :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCoverEventually :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCover :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ index control, control ∈ controlSample index ->
        controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedCoefficientLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlCoefficientLoading index (controlScore index control))
    (htreatedCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedCoefficientLoading index cell| ≤ treatedEnvelope index)
    (hcontrolCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlCoefficientLoading index cell| ≤ controlEnvelope index)
    (htreatedThirdLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedThirdMomentLoading (treatedScore index treated) =
          |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ index control, control ∈ controlSample index ->
        controlThirdMomentLoading (controlScore index control) =
          |controlResidual index control| ^ 3)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit)
    (htreatedEnvelope : Tendsto treatedEnvelope l (nhds 0))
    (hcontrolEnvelope : Tendsto controlEnvelope l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_local_experiment_finite_scoreCell_lindeberg_bridges
    (l := l) treatedCells controlCells treatedSample controlSample
    treatedWeight treatedCoefficient treatedResidual controlWeight
    controlCoefficient controlResidual treatedScore controlScore
    treatedCoefficientLoading controlCoefficientLoading
    treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
    controlMassLimit treatedEnvelope controlEnvelope geometry radius residual
    bias known estimated hinputLindeberg hgeometry_regular hcatchment
    hmoment_transfer hresidual_reg hmartingale hquad hresidual_transfer
    hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
    hbias_transfer hdecomp hden hheterogeneity hknown_normality_transfer
    hknown_variance_transfer hfirst hscore hfunctional hequicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      estimated.score_adjustment_algebra parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret)
    hgodambe htreatedWeightNonneg hcontrolWeightNonneg
    htreatedCoverEventually hcontrolCoverEventually htreatedCover
    hcontrolCover htreatedCoefficient hcontrolCoefficient
    htreatedCoefficientLoadingBound hcontrolCoefficientLoadingBound
    htreatedThirdLoading hcontrolThirdLoading htreatedMass hcontrolMass
    htreatedEnvelope hcontrolEnvelope

omit [DecidableEq Param] in
/--
Direct Chen-Han martingale local-experiment route with Lindeberg supplied by
finite score-cell coefficient loadings and the local variance adjustment
discharged by the changing-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_local_experiment_finite_scoreCell_lindeberg_changingLaw_score_adjustment_identity
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficientLoading : Index -> TreatedCell -> Real)
    (controlCoefficientLoading : Index -> ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
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
    (hgodambe : estimated.godambe_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoverEventually :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCoverEventually :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCover :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ index control, control ∈ controlSample index ->
        controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedCoefficientLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlCoefficientLoading index (controlScore index control))
    (htreatedCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedCoefficientLoading index cell| ≤ treatedEnvelope index)
    (hcontrolCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlCoefficientLoading index cell| ≤ controlEnvelope index)
    (htreatedThirdLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedThirdMomentLoading (treatedScore index treated) =
          |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ index control, control ∈ controlSample index ->
        controlThirdMomentLoading (controlScore index control) =
          |controlResidual index control| ^ 3)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit)
    (htreatedEnvelope : Tendsto treatedEnvelope l (nhds 0))
    (hcontrolEnvelope : Tendsto controlEnvelope l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_local_experiment_finite_scoreCell_lindeberg_bridges
    (l := l) treatedCells controlCells treatedSample controlSample
    treatedWeight treatedCoefficient treatedResidual controlWeight
    controlCoefficient controlResidual treatedScore controlScore
    treatedCoefficientLoading controlCoefficientLoading
    treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
    controlMassLimit treatedEnvelope controlEnvelope geometry radius residual
    bias known estimated hinputLindeberg hgeometry_regular hcatchment
    hmoment_transfer hresidual_reg hmartingale hquad hresidual_transfer
    hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
    hbias_transfer hdecomp hden hheterogeneity hknown_normality_transfer
    hknown_variance_transfer hfirst hscore hfunctional hequicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      estimated.score_adjustment_algebra parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret)
    hgodambe htreatedWeightNonneg hcontrolWeightNonneg
    htreatedCoverEventually hcontrolCoverEventually htreatedCover
    hcontrolCover htreatedCoefficient hcontrolCoefficient
    htreatedCoefficientLoadingBound hcontrolCoefficientLoadingBound
    htreatedThirdLoading hcontrolThirdLoading htreatedMass hcontrolMass
    htreatedEnvelope hcontrolEnvelope

omit [DecidableEq Param] in
/--
Direct Chen-Han martingale local-experiment route with Lindeberg supplied by
finite score-cell coefficient loadings, fixed-law score-adjustment algebra
supplied by the finite identity, and the remaining local-experiment/Godambe
obligations packaged as a compact core.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_local_experiment_finite_scoreCell_lindeberg_fixedLaw_score_adjustment_identity_and_local_experiment_core
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficientLoading : Index -> TreatedCell -> Real)
    (controlCoefficientLoading : Index -> ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
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
    (core : EstimatedScoreLocalExperimentVarianceCore estimated)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoverEventually :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCoverEventually :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCover :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ index control, control ∈ controlSample index ->
        controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedCoefficientLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlCoefficientLoading index (controlScore index control))
    (htreatedCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedCoefficientLoading index cell| ≤ treatedEnvelope index)
    (hcontrolCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlCoefficientLoading index cell| ≤ controlEnvelope index)
    (htreatedThirdLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedThirdMomentLoading (treatedScore index treated) =
          |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ index control, control ∈ controlSample index ->
        controlThirdMomentLoading (controlScore index control) =
          |controlResidual index control| ^ 3)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit)
    (htreatedEnvelope : Tendsto treatedEnvelope l (nhds 0))
    (hcontrolEnvelope : Tendsto controlEnvelope l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_local_experiment_finite_scoreCell_lindeberg_fixedLaw_score_adjustment_identity
    (l := l) treatedCells controlCells treatedSample controlSample
    treatedWeight treatedCoefficient treatedResidual controlWeight
    controlCoefficient controlResidual treatedScore controlScore
    treatedCoefficientLoading controlCoefficientLoading
    treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
    controlMassLimit treatedEnvelope controlEnvelope geometry radius residual
    bias known estimated parameters oracleVariance firstStepLoading
    scoreCovariance hinterpret hinputLindeberg hgeometry_regular hcatchment
    hmoment_transfer hresidual_reg hmartingale hquad hresidual_transfer
    hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
    hbias_transfer hdecomp hden hheterogeneity hknown_normality_transfer
    hknown_variance_transfer hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity
    htreatedWeightNonneg hcontrolWeightNonneg htreatedCoverEventually
    hcontrolCoverEventually htreatedCover hcontrolCover htreatedCoefficient
    hcontrolCoefficient htreatedCoefficientLoadingBound
    hcontrolCoefficientLoadingBound htreatedThirdLoading hcontrolThirdLoading
    htreatedMass hcontrolMass htreatedEnvelope hcontrolEnvelope

omit [DecidableEq Param] in
/--
Direct Chen-Han martingale local-experiment route with Lindeberg supplied by
finite score-cell coefficient loadings, changing-law score-adjustment algebra
supplied by the finite identity, and the remaining local-experiment/Godambe
obligations packaged as a compact core.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_local_experiment_finite_scoreCell_lindeberg_changingLaw_score_adjustment_identity_and_local_experiment_core
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficientLoading : Index -> TreatedCell -> Real)
    (controlCoefficientLoading : Index -> ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
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
    (core : EstimatedScoreLocalExperimentVarianceCore estimated)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoverEventually :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCoverEventually :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCover :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ index control, control ∈ controlSample index ->
        controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedCoefficientLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlCoefficientLoading index (controlScore index control))
    (htreatedCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedCoefficientLoading index cell| ≤ treatedEnvelope index)
    (hcontrolCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlCoefficientLoading index cell| ≤ controlEnvelope index)
    (htreatedThirdLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedThirdMomentLoading (treatedScore index treated) =
          |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ index control, control ∈ controlSample index ->
        controlThirdMomentLoading (controlScore index control) =
          |controlResidual index control| ^ 3)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit)
    (htreatedEnvelope : Tendsto treatedEnvelope l (nhds 0))
    (hcontrolEnvelope : Tendsto controlEnvelope l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_local_experiment_finite_scoreCell_lindeberg_changingLaw_score_adjustment_identity
    (l := l) treatedCells controlCells treatedSample controlSample
    treatedWeight treatedCoefficient treatedResidual controlWeight
    controlCoefficient controlResidual treatedScore controlScore
    treatedCoefficientLoading controlCoefficientLoading
    treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
    controlMassLimit treatedEnvelope controlEnvelope geometry radius residual
    bias known estimated parameters oracleVariance firstStepLoading
    targetDriftLoading scoreCovariance hinterpret hinputLindeberg
    hgeometry_regular hcatchment hmoment_transfer hresidual_reg hmartingale
    hquad hresidual_transfer hradius_regular hradius_geometry hradius_transfer
    hfinite hlipschitz hbias_transfer hdecomp hden hheterogeneity
    hknown_normality_transfer hknown_variance_transfer hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity
    htreatedWeightNonneg hcontrolWeightNonneg htreatedCoverEventually
    hcontrolCoverEventually htreatedCover hcontrolCover htreatedCoefficient
    hcontrolCoefficient htreatedCoefficientLoadingBound
    hcontrolCoefficientLoadingBound htreatedThirdLoading hcontrolThirdLoading
    htreatedMass hcontrolMass htreatedEnvelope hcontrolEnvelope

omit [DecidableEq Param] in
/--
Component Chen-Han martingale reference route with Lindeberg discharged by
concrete two-arm envelope bounds and the variance adjustment discharged by the
fixed-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_twoArm_envelope_lindeberg_fixedLaw_score_adjustment_identity
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
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
    (hgodambe_variance : estimatedVariance.godambe_variance_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index)
    (hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index)
    (htreatedEnvelopeBound :
      Tendsto
        (fun index =>
          treatedEnvelope index ^ 3 *
            residualThirdMomentSum (treatedSample index)
              (treatedWeight index) (treatedResidual index))
        l (nhds 0))
    (hcontrolEnvelopeBound :
      Tendsto
        (fun index =>
          controlEnvelope index ^ 3 *
            residualThirdMomentSum (controlSample index)
              (controlWeight index) (controlResidual index))
        l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimatedVariance.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_twoArm_envelope_lindeberg_bridges
    (l := l) treatedSample controlSample treatedWeight treatedCoefficient
    treatedResidual controlWeight controlCoefficient controlResidual
    treatedEnvelope controlEnvelope geometry radius heterogeneity residual bias
    known knownVariance estimated estimatedVariance hinputLindeberg
    hgeometry_regular hcatchment hmoment_transfer hheterogeneity_moment
    hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hquad
    hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden horthogonality hknown_normality_transfer
    hknown_variance_transfer hfirst hlocal hgodambe_normality
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      estimatedVariance.score_adjustment_algebra parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret)
    hgodambe_variance htreatedWeightNonneg hcontrolWeightNonneg
    htreatedCoeffBound hcontrolCoeffBound htreatedEnvelopeBound
    hcontrolEnvelopeBound

omit [DecidableEq Param] in
/--
Component Chen-Han martingale reference route with Lindeberg discharged by
concrete two-arm envelope bounds and the variance adjustment discharged by the
changing-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_twoArm_envelope_lindeberg_changingLaw_score_adjustment_identity
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
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
    (hgodambe_variance : estimatedVariance.godambe_variance_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index)
    (hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index)
    (htreatedEnvelopeBound :
      Tendsto
        (fun index =>
          treatedEnvelope index ^ 3 *
            residualThirdMomentSum (treatedSample index)
              (treatedWeight index) (treatedResidual index))
        l (nhds 0))
    (hcontrolEnvelopeBound :
      Tendsto
        (fun index =>
          controlEnvelope index ^ 3 *
            residualThirdMomentSum (controlSample index)
              (controlWeight index) (controlResidual index))
        l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimatedVariance.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_twoArm_envelope_lindeberg_bridges
    (l := l) treatedSample controlSample treatedWeight treatedCoefficient
    treatedResidual controlWeight controlCoefficient controlResidual
    treatedEnvelope controlEnvelope geometry radius heterogeneity residual bias
    known knownVariance estimated estimatedVariance hinputLindeberg
    hgeometry_regular hcatchment hmoment_transfer hheterogeneity_moment
    hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hquad
    hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden horthogonality hknown_normality_transfer
    hknown_variance_transfer hfirst hlocal hgodambe_normality
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      estimatedVariance.score_adjustment_algebra parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret)
    hgodambe_variance htreatedWeightNonneg hcontrolWeightNonneg
    htreatedCoeffBound hcontrolCoeffBound htreatedEnvelopeBound
    hcontrolEnvelopeBound

omit [DecidableEq Param] in
/--
Component Chen-Han local-experiment martingale route with Lindeberg discharged
by concrete two-arm envelope bounds and the local variance adjustment discharged
by the fixed-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_twoArm_envelope_lindeberg_fixedLaw_score_adjustment_identity
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
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
    (hgodambe : estimated.godambe_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index)
    (hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index)
    (htreatedEnvelopeBound :
      Tendsto
        (fun index =>
          treatedEnvelope index ^ 3 *
            residualThirdMomentSum (treatedSample index)
              (treatedWeight index) (treatedResidual index))
        l (nhds 0))
    (hcontrolEnvelopeBound :
      Tendsto
        (fun index =>
          controlEnvelope index ^ 3 *
            residualThirdMomentSum (controlSample index)
              (controlWeight index) (controlResidual index))
        l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_twoArm_envelope_lindeberg_bridges
    (l := l) treatedSample controlSample treatedWeight treatedCoefficient
    treatedResidual controlWeight controlCoefficient controlResidual
    treatedEnvelope controlEnvelope geometry radius heterogeneity residual bias
    known knownVariance estimated hinputLindeberg hgeometry_regular hcatchment
    hmoment_transfer hheterogeneity_moment hheterogeneity_variance
    hheterogeneity_transfer hheterogeneity_variance_transfer hresidual_reg
    hmartingale hquad hresidual_transfer hresidual_variance_transfer
    hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
    hbias_transfer hdecomp hden horthogonality hknown_normality_transfer
    hknown_variance_transfer hfirst hscore hfunctional hequicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      estimated.score_adjustment_algebra parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret)
    hgodambe htreatedWeightNonneg hcontrolWeightNonneg htreatedCoeffBound
    hcontrolCoeffBound htreatedEnvelopeBound hcontrolEnvelopeBound

omit [DecidableEq Param] in
/--
Component Chen-Han local-experiment martingale route with Lindeberg discharged
by concrete two-arm envelope bounds and the local variance adjustment discharged
by the changing-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_twoArm_envelope_lindeberg_changingLaw_score_adjustment_identity
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
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
    (hgodambe : estimated.godambe_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index)
    (hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index)
    (htreatedEnvelopeBound :
      Tendsto
        (fun index =>
          treatedEnvelope index ^ 3 *
            residualThirdMomentSum (treatedSample index)
              (treatedWeight index) (treatedResidual index))
        l (nhds 0))
    (hcontrolEnvelopeBound :
      Tendsto
        (fun index =>
          controlEnvelope index ^ 3 *
            residualThirdMomentSum (controlSample index)
              (controlWeight index) (controlResidual index))
        l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_twoArm_envelope_lindeberg_bridges
    (l := l) treatedSample controlSample treatedWeight treatedCoefficient
    treatedResidual controlWeight controlCoefficient controlResidual
    treatedEnvelope controlEnvelope geometry radius heterogeneity residual bias
    known knownVariance estimated hinputLindeberg hgeometry_regular hcatchment
    hmoment_transfer hheterogeneity_moment hheterogeneity_variance
    hheterogeneity_transfer hheterogeneity_variance_transfer hresidual_reg
    hmartingale hquad hresidual_transfer hresidual_variance_transfer
    hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
    hbias_transfer hdecomp hden horthogonality hknown_normality_transfer
    hknown_variance_transfer hfirst hscore hfunctional hequicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      estimated.score_adjustment_algebra parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret)
    hgodambe htreatedWeightNonneg hcontrolWeightNonneg htreatedCoeffBound
    hcontrolCoeffBound htreatedEnvelopeBound hcontrolEnvelopeBound

omit [DecidableEq Param] in
/--
Component Chen-Han local-experiment martingale route with Lindeberg discharged
by concrete two-arm envelope bounds, fixed-law score-adjustment algebra supplied
by the finite identity, and the remaining local-experiment/Godambe obligations
packaged as a compact core.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_twoArm_envelope_lindeberg_fixedLaw_score_adjustment_identity_and_local_experiment_core
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
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
    (core : EstimatedScoreLocalExperimentVarianceCore estimated)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index)
    (hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index)
    (htreatedEnvelopeBound :
      Tendsto
        (fun index =>
          treatedEnvelope index ^ 3 *
            residualThirdMomentSum (treatedSample index)
              (treatedWeight index) (treatedResidual index))
        l (nhds 0))
    (hcontrolEnvelopeBound :
      Tendsto
        (fun index =>
          controlEnvelope index ^ 3 *
            residualThirdMomentSum (controlSample index)
              (controlWeight index) (controlResidual index))
        l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_twoArm_envelope_lindeberg_fixedLaw_score_adjustment_identity
    (l := l) treatedSample controlSample treatedWeight treatedCoefficient
    treatedResidual controlWeight controlCoefficient controlResidual
    treatedEnvelope controlEnvelope geometry radius heterogeneity residual bias
    known knownVariance estimated parameters oracleVariance firstStepLoading
    scoreCovariance hinterpret hinputLindeberg hgeometry_regular hcatchment
    hmoment_transfer hheterogeneity_moment hheterogeneity_variance
    hheterogeneity_transfer hheterogeneity_variance_transfer hresidual_reg
    hmartingale hquad hresidual_transfer hresidual_variance_transfer
    hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
    hbias_transfer hdecomp hden horthogonality hknown_normality_transfer
    hknown_variance_transfer hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity
    htreatedWeightNonneg hcontrolWeightNonneg htreatedCoeffBound
    hcontrolCoeffBound htreatedEnvelopeBound hcontrolEnvelopeBound

omit [DecidableEq Param] in
/--
Component Chen-Han local-experiment martingale route with Lindeberg discharged
by concrete two-arm envelope bounds, changing-law score-adjustment algebra
supplied by the finite identity, and the remaining local-experiment/Godambe
obligations packaged as a compact core.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_twoArm_envelope_lindeberg_changingLaw_score_adjustment_identity_and_local_experiment_core
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
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
    (core : EstimatedScoreLocalExperimentVarianceCore estimated)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index)
    (hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index)
    (htreatedEnvelopeBound :
      Tendsto
        (fun index =>
          treatedEnvelope index ^ 3 *
            residualThirdMomentSum (treatedSample index)
              (treatedWeight index) (treatedResidual index))
        l (nhds 0))
    (hcontrolEnvelopeBound :
      Tendsto
        (fun index =>
          controlEnvelope index ^ 3 *
            residualThirdMomentSum (controlSample index)
              (controlWeight index) (controlResidual index))
        l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_twoArm_envelope_lindeberg_changingLaw_score_adjustment_identity
    (l := l) treatedSample controlSample treatedWeight treatedCoefficient
    treatedResidual controlWeight controlCoefficient controlResidual
    treatedEnvelope controlEnvelope geometry radius heterogeneity residual bias
    known knownVariance estimated parameters oracleVariance firstStepLoading
    targetDriftLoading scoreCovariance hinterpret hinputLindeberg
    hgeometry_regular hcatchment hmoment_transfer hheterogeneity_moment
    hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hquad
    hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden horthogonality hknown_normality_transfer
    hknown_variance_transfer hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity
    htreatedWeightNonneg hcontrolWeightNonneg htreatedCoeffBound
    hcontrolCoeffBound htreatedEnvelopeBound hcontrolEnvelopeBound

omit [DecidableEq Param] in
/--
Component Chen-Han martingale reference route with Lindeberg supplied by finite
score-cell coefficient loadings and the variance adjustment discharged by the
fixed-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_finite_scoreCell_lindeberg_fixedLaw_score_adjustment_identity
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficientLoading : Index -> TreatedCell -> Real)
    (controlCoefficientLoading : Index -> ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
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
    (hgodambe_variance : estimatedVariance.godambe_variance_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoverEventually :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCoverEventually :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCover :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ index control, control ∈ controlSample index ->
        controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedCoefficientLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlCoefficientLoading index (controlScore index control))
    (htreatedCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedCoefficientLoading index cell| ≤ treatedEnvelope index)
    (hcontrolCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlCoefficientLoading index cell| ≤ controlEnvelope index)
    (htreatedThirdLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedThirdMomentLoading (treatedScore index treated) =
          |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ index control, control ∈ controlSample index ->
        controlThirdMomentLoading (controlScore index control) =
          |controlResidual index control| ^ 3)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit)
    (htreatedEnvelope : Tendsto treatedEnvelope l (nhds 0))
    (hcontrolEnvelope : Tendsto controlEnvelope l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimatedVariance.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_finite_scoreCell_lindeberg_bridges
    (l := l) treatedCells controlCells treatedSample controlSample
    treatedWeight treatedCoefficient treatedResidual controlWeight
    controlCoefficient controlResidual treatedScore controlScore
    treatedCoefficientLoading controlCoefficientLoading
    treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
    controlMassLimit treatedEnvelope controlEnvelope geometry radius
    heterogeneity residual bias known knownVariance estimated estimatedVariance
    hinputLindeberg hgeometry_regular hcatchment hmoment_transfer
    hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hquad
    hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden horthogonality hknown_normality_transfer
    hknown_variance_transfer hfirst hlocal hgodambe_normality
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      estimatedVariance.score_adjustment_algebra parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret)
    hgodambe_variance htreatedWeightNonneg hcontrolWeightNonneg
    htreatedCoverEventually hcontrolCoverEventually htreatedCover
    hcontrolCover htreatedCoefficient hcontrolCoefficient
    htreatedCoefficientLoadingBound hcontrolCoefficientLoadingBound
    htreatedThirdLoading hcontrolThirdLoading htreatedMass hcontrolMass
    htreatedEnvelope hcontrolEnvelope

omit [DecidableEq Param] in
/--
Component Chen-Han martingale reference route with Lindeberg supplied by finite
score-cell coefficient loadings and the variance adjustment discharged by the
changing-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_finite_scoreCell_lindeberg_changingLaw_score_adjustment_identity
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficientLoading : Index -> TreatedCell -> Real)
    (controlCoefficientLoading : Index -> ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
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
    (hgodambe_variance : estimatedVariance.godambe_variance_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoverEventually :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCoverEventually :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCover :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ index control, control ∈ controlSample index ->
        controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedCoefficientLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlCoefficientLoading index (controlScore index control))
    (htreatedCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedCoefficientLoading index cell| ≤ treatedEnvelope index)
    (hcontrolCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlCoefficientLoading index cell| ≤ controlEnvelope index)
    (htreatedThirdLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedThirdMomentLoading (treatedScore index treated) =
          |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ index control, control ∈ controlSample index ->
        controlThirdMomentLoading (controlScore index control) =
          |controlResidual index control| ^ 3)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit)
    (htreatedEnvelope : Tendsto treatedEnvelope l (nhds 0))
    (hcontrolEnvelope : Tendsto controlEnvelope l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimatedVariance.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_finite_scoreCell_lindeberg_bridges
    (l := l) treatedCells controlCells treatedSample controlSample
    treatedWeight treatedCoefficient treatedResidual controlWeight
    controlCoefficient controlResidual treatedScore controlScore
    treatedCoefficientLoading controlCoefficientLoading
    treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
    controlMassLimit treatedEnvelope controlEnvelope geometry radius
    heterogeneity residual bias known knownVariance estimated estimatedVariance
    hinputLindeberg hgeometry_regular hcatchment hmoment_transfer
    hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hquad
    hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden horthogonality hknown_normality_transfer
    hknown_variance_transfer hfirst hlocal hgodambe_normality
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      estimatedVariance.score_adjustment_algebra parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret)
    hgodambe_variance htreatedWeightNonneg hcontrolWeightNonneg
    htreatedCoverEventually hcontrolCoverEventually htreatedCover
    hcontrolCover htreatedCoefficient hcontrolCoefficient
    htreatedCoefficientLoadingBound hcontrolCoefficientLoadingBound
    htreatedThirdLoading hcontrolThirdLoading htreatedMass hcontrolMass
    htreatedEnvelope hcontrolEnvelope

omit [DecidableEq Param] in
/--
Component Chen-Han local-experiment martingale route with Lindeberg supplied by
finite score-cell coefficient loadings and the local variance adjustment
discharged by the fixed-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_finite_scoreCell_lindeberg_fixedLaw_score_adjustment_identity
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficientLoading : Index -> TreatedCell -> Real)
    (controlCoefficientLoading : Index -> ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
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
    (hgodambe : estimated.godambe_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoverEventually :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCoverEventually :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCover :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ index control, control ∈ controlSample index ->
        controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedCoefficientLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlCoefficientLoading index (controlScore index control))
    (htreatedCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedCoefficientLoading index cell| ≤ treatedEnvelope index)
    (hcontrolCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlCoefficientLoading index cell| ≤ controlEnvelope index)
    (htreatedThirdLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedThirdMomentLoading (treatedScore index treated) =
          |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ index control, control ∈ controlSample index ->
        controlThirdMomentLoading (controlScore index control) =
          |controlResidual index control| ^ 3)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit)
    (htreatedEnvelope : Tendsto treatedEnvelope l (nhds 0))
    (hcontrolEnvelope : Tendsto controlEnvelope l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_finite_scoreCell_lindeberg_bridges
    (l := l) treatedCells controlCells treatedSample controlSample
    treatedWeight treatedCoefficient treatedResidual controlWeight
    controlCoefficient controlResidual treatedScore controlScore
    treatedCoefficientLoading controlCoefficientLoading
    treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
    controlMassLimit treatedEnvelope controlEnvelope geometry radius
    heterogeneity residual bias known knownVariance estimated hinputLindeberg
    hgeometry_regular hcatchment hmoment_transfer hheterogeneity_moment
    hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hquad
    hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden horthogonality hknown_normality_transfer
    hknown_variance_transfer hfirst hscore hfunctional hequicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      estimated.score_adjustment_algebra parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret)
    hgodambe htreatedWeightNonneg hcontrolWeightNonneg
    htreatedCoverEventually hcontrolCoverEventually htreatedCover
    hcontrolCover htreatedCoefficient hcontrolCoefficient
    htreatedCoefficientLoadingBound hcontrolCoefficientLoadingBound
    htreatedThirdLoading hcontrolThirdLoading htreatedMass hcontrolMass
    htreatedEnvelope hcontrolEnvelope

omit [DecidableEq Param] in
/--
Component Chen-Han local-experiment martingale route with Lindeberg supplied by
finite score-cell coefficient loadings and the local variance adjustment
discharged by the changing-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_finite_scoreCell_lindeberg_changingLaw_score_adjustment_identity
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficientLoading : Index -> TreatedCell -> Real)
    (controlCoefficientLoading : Index -> ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
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
    (hgodambe : estimated.godambe_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoverEventually :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCoverEventually :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCover :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ index control, control ∈ controlSample index ->
        controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedCoefficientLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlCoefficientLoading index (controlScore index control))
    (htreatedCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedCoefficientLoading index cell| ≤ treatedEnvelope index)
    (hcontrolCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlCoefficientLoading index cell| ≤ controlEnvelope index)
    (htreatedThirdLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedThirdMomentLoading (treatedScore index treated) =
          |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ index control, control ∈ controlSample index ->
        controlThirdMomentLoading (controlScore index control) =
          |controlResidual index control| ^ 3)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit)
    (htreatedEnvelope : Tendsto treatedEnvelope l (nhds 0))
    (hcontrolEnvelope : Tendsto controlEnvelope l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_finite_scoreCell_lindeberg_bridges
    (l := l) treatedCells controlCells treatedSample controlSample
    treatedWeight treatedCoefficient treatedResidual controlWeight
    controlCoefficient controlResidual treatedScore controlScore
    treatedCoefficientLoading controlCoefficientLoading
    treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
    controlMassLimit treatedEnvelope controlEnvelope geometry radius
    heterogeneity residual bias known knownVariance estimated hinputLindeberg
    hgeometry_regular hcatchment hmoment_transfer hheterogeneity_moment
    hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hquad
    hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden horthogonality hknown_normality_transfer
    hknown_variance_transfer hfirst hscore hfunctional hequicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      estimated.score_adjustment_algebra parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret)
    hgodambe htreatedWeightNonneg hcontrolWeightNonneg
    htreatedCoverEventually hcontrolCoverEventually htreatedCover
    hcontrolCover htreatedCoefficient hcontrolCoefficient
    htreatedCoefficientLoadingBound hcontrolCoefficientLoadingBound
    htreatedThirdLoading hcontrolThirdLoading htreatedMass hcontrolMass
    htreatedEnvelope hcontrolEnvelope

omit [DecidableEq Param] in
/--
Component Chen-Han local-experiment martingale route with Lindeberg supplied by
finite score-cell coefficient loadings, fixed-law score-adjustment algebra
supplied by the finite identity, and the remaining local-experiment/Godambe
obligations packaged as a compact core.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_finite_scoreCell_lindeberg_fixedLaw_score_adjustment_identity_and_local_experiment_core
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficientLoading : Index -> TreatedCell -> Real)
    (controlCoefficientLoading : Index -> ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
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
    (core : EstimatedScoreLocalExperimentVarianceCore estimated)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoverEventually :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCoverEventually :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCover :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ index control, control ∈ controlSample index ->
        controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedCoefficientLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlCoefficientLoading index (controlScore index control))
    (htreatedCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedCoefficientLoading index cell| ≤ treatedEnvelope index)
    (hcontrolCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlCoefficientLoading index cell| ≤ controlEnvelope index)
    (htreatedThirdLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedThirdMomentLoading (treatedScore index treated) =
          |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ index control, control ∈ controlSample index ->
        controlThirdMomentLoading (controlScore index control) =
          |controlResidual index control| ^ 3)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit)
    (htreatedEnvelope : Tendsto treatedEnvelope l (nhds 0))
    (hcontrolEnvelope : Tendsto controlEnvelope l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_finite_scoreCell_lindeberg_fixedLaw_score_adjustment_identity
    (l := l) treatedCells controlCells treatedSample controlSample
    treatedWeight treatedCoefficient treatedResidual controlWeight
    controlCoefficient controlResidual treatedScore controlScore
    treatedCoefficientLoading controlCoefficientLoading
    treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
    controlMassLimit treatedEnvelope controlEnvelope geometry radius
    heterogeneity residual bias known knownVariance estimated parameters
    oracleVariance firstStepLoading scoreCovariance hinterpret
    hinputLindeberg hgeometry_regular hcatchment hmoment_transfer
    hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hquad
    hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden horthogonality hknown_normality_transfer
    hknown_variance_transfer hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity
    htreatedWeightNonneg hcontrolWeightNonneg htreatedCoverEventually
    hcontrolCoverEventually htreatedCover hcontrolCover htreatedCoefficient
    hcontrolCoefficient htreatedCoefficientLoadingBound
    hcontrolCoefficientLoadingBound htreatedThirdLoading hcontrolThirdLoading
    htreatedMass hcontrolMass htreatedEnvelope hcontrolEnvelope

omit [DecidableEq Param] in
/--
Component Chen-Han local-experiment martingale route with Lindeberg supplied by
finite score-cell coefficient loadings, changing-law score-adjustment algebra
supplied by the finite identity, and the remaining local-experiment/Godambe
obligations packaged as a compact core.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_finite_scoreCell_lindeberg_changingLaw_score_adjustment_identity_and_local_experiment_core
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficientLoading : Index -> TreatedCell -> Real)
    (controlCoefficientLoading : Index -> ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
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
    (core : EstimatedScoreLocalExperimentVarianceCore estimated)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoverEventually :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCoverEventually :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCover :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ index control, control ∈ controlSample index ->
        controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedCoefficientLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlCoefficientLoading index (controlScore index control))
    (htreatedCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedCoefficientLoading index cell| ≤ treatedEnvelope index)
    (hcontrolCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlCoefficientLoading index cell| ≤ controlEnvelope index)
    (htreatedThirdLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedThirdMomentLoading (treatedScore index treated) =
          |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ index control, control ∈ controlSample index ->
        controlThirdMomentLoading (controlScore index control) =
          |controlResidual index control| ^ 3)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit)
    (htreatedEnvelope : Tendsto treatedEnvelope l (nhds 0))
    (hcontrolEnvelope : Tendsto controlEnvelope l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_finite_scoreCell_lindeberg_changingLaw_score_adjustment_identity
    (l := l) treatedCells controlCells treatedSample controlSample
    treatedWeight treatedCoefficient treatedResidual controlWeight
    controlCoefficient controlResidual treatedScore controlScore
    treatedCoefficientLoading controlCoefficientLoading
    treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
    controlMassLimit treatedEnvelope controlEnvelope geometry radius
    heterogeneity residual bias known knownVariance estimated parameters
    oracleVariance firstStepLoading targetDriftLoading scoreCovariance
    hinterpret hinputLindeberg hgeometry_regular hcatchment hmoment_transfer
    hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hquad
    hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden horthogonality hknown_normality_transfer
    hknown_variance_transfer hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity
    htreatedWeightNonneg hcontrolWeightNonneg htreatedCoverEventually
    hcontrolCoverEventually htreatedCover hcontrolCover htreatedCoefficient
    hcontrolCoefficient htreatedCoefficientLoadingBound
    hcontrolCoefficientLoadingBound htreatedThirdLoading hcontrolThirdLoading
    htreatedMass hcontrolMass htreatedEnvelope hcontrolEnvelope

omit [DecidableEq Param] in
/--
Component Chen-Han design-cross-zero martingale route with Lindeberg supplied
by concrete two-arm envelope bounds and the estimated-score variance adjustment
discharged by the fixed-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_design_cross_zero_twoArm_envelope_lindeberg_fixedLaw_score_adjustment_identity
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
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
    (hgodambe_variance : estimatedVariance.godambe_variance_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index)
    (hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index)
    (htreatedEnvelopeBound :
      Tendsto
        (fun index =>
          treatedEnvelope index ^ 3 *
            residualThirdMomentSum (treatedSample index)
              (treatedWeight index) (treatedResidual index))
        l (nhds 0))
    (hcontrolEnvelopeBound :
      Tendsto
        (fun index =>
          controlEnvelope index ^ 3 *
            residualThirdMomentSum (controlSample index)
              (controlWeight index) (controlResidual index))
        l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimatedVariance.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_design_cross_zero_twoArm_envelope_lindeberg_bridges
    (l := l) treatedSample controlSample treatedWeight treatedCoefficient
    treatedResidual controlWeight controlCoefficient controlResidual
    treatedEnvelope controlEnvelope geometry radius heterogeneity residual
    bias known knownVariance orthogonality estimated estimatedVariance
    hinputLindeberg hgeometry_regular hcatchment hmoment_transfer
    hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hquad
    hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden hcross hlimit hknown_normality_transfer
    hknown_variance_transfer hfirst hlocal hgodambe_normality
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      estimatedVariance.score_adjustment_algebra parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret)
    hgodambe_variance htreatedWeightNonneg hcontrolWeightNonneg
    htreatedCoeffBound hcontrolCoeffBound htreatedEnvelopeBound
    hcontrolEnvelopeBound

omit [DecidableEq Param] in
/--
Component Chen-Han design-cross-zero martingale route with Lindeberg supplied
by concrete two-arm envelope bounds and the estimated-score variance adjustment
discharged by the changing-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_design_cross_zero_twoArm_envelope_lindeberg_changingLaw_score_adjustment_identity
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
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
    (hgodambe_variance : estimatedVariance.godambe_variance_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index)
    (hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index)
    (htreatedEnvelopeBound :
      Tendsto
        (fun index =>
          treatedEnvelope index ^ 3 *
            residualThirdMomentSum (treatedSample index)
              (treatedWeight index) (treatedResidual index))
        l (nhds 0))
    (hcontrolEnvelopeBound :
      Tendsto
        (fun index =>
          controlEnvelope index ^ 3 *
            residualThirdMomentSum (controlSample index)
              (controlWeight index) (controlResidual index))
        l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimatedVariance.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_design_cross_zero_twoArm_envelope_lindeberg_bridges
    (l := l) treatedSample controlSample treatedWeight treatedCoefficient
    treatedResidual controlWeight controlCoefficient controlResidual
    treatedEnvelope controlEnvelope geometry radius heterogeneity residual
    bias known knownVariance orthogonality estimated estimatedVariance
    hinputLindeberg hgeometry_regular hcatchment hmoment_transfer
    hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hquad
    hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden hcross hlimit hknown_normality_transfer
    hknown_variance_transfer hfirst hlocal hgodambe_normality
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      estimatedVariance.score_adjustment_algebra parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret)
    hgodambe_variance htreatedWeightNonneg hcontrolWeightNonneg
    htreatedCoeffBound hcontrolCoeffBound htreatedEnvelopeBound
    hcontrolEnvelopeBound

omit [DecidableEq Param] in
/--
Component Chen-Han design-cross-zero local-experiment martingale route with
Lindeberg supplied by concrete two-arm envelope bounds and the local variance
adjustment discharged by the fixed-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_design_cross_zero_twoArm_envelope_lindeberg_fixedLaw_score_adjustment_identity
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
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
    (hgodambe : estimated.godambe_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index)
    (hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index)
    (htreatedEnvelopeBound :
      Tendsto
        (fun index =>
          treatedEnvelope index ^ 3 *
            residualThirdMomentSum (treatedSample index)
              (treatedWeight index) (treatedResidual index))
        l (nhds 0))
    (hcontrolEnvelopeBound :
      Tendsto
        (fun index =>
          controlEnvelope index ^ 3 *
            residualThirdMomentSum (controlSample index)
              (controlWeight index) (controlResidual index))
        l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_design_cross_zero_twoArm_envelope_lindeberg_bridges
    (l := l) treatedSample controlSample treatedWeight treatedCoefficient
    treatedResidual controlWeight controlCoefficient controlResidual
    treatedEnvelope controlEnvelope geometry radius heterogeneity residual
    bias known knownVariance orthogonality estimated hinputLindeberg
    hgeometry_regular hcatchment hmoment_transfer hheterogeneity_moment
    hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hquad
    hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden hcross hlimit hknown_normality_transfer
    hknown_variance_transfer hfirst hscore hfunctional hequicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      estimated.score_adjustment_algebra parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret)
    hgodambe htreatedWeightNonneg hcontrolWeightNonneg htreatedCoeffBound
    hcontrolCoeffBound htreatedEnvelopeBound hcontrolEnvelopeBound

omit [DecidableEq Param] in
/--
Component Chen-Han design-cross-zero local-experiment martingale route with
Lindeberg supplied by concrete two-arm envelope bounds and the local variance
adjustment discharged by the changing-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_design_cross_zero_twoArm_envelope_lindeberg_changingLaw_score_adjustment_identity
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
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
    (hgodambe : estimated.godambe_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index)
    (hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index)
    (htreatedEnvelopeBound :
      Tendsto
        (fun index =>
          treatedEnvelope index ^ 3 *
            residualThirdMomentSum (treatedSample index)
              (treatedWeight index) (treatedResidual index))
        l (nhds 0))
    (hcontrolEnvelopeBound :
      Tendsto
        (fun index =>
          controlEnvelope index ^ 3 *
            residualThirdMomentSum (controlSample index)
              (controlWeight index) (controlResidual index))
        l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_design_cross_zero_twoArm_envelope_lindeberg_bridges
    (l := l) treatedSample controlSample treatedWeight treatedCoefficient
    treatedResidual controlWeight controlCoefficient controlResidual
    treatedEnvelope controlEnvelope geometry radius heterogeneity residual
    bias known knownVariance orthogonality estimated hinputLindeberg
    hgeometry_regular hcatchment hmoment_transfer hheterogeneity_moment
    hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hquad
    hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden hcross hlimit hknown_normality_transfer
    hknown_variance_transfer hfirst hscore hfunctional hequicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      estimated.score_adjustment_algebra parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret)
    hgodambe htreatedWeightNonneg hcontrolWeightNonneg htreatedCoeffBound
    hcontrolCoeffBound htreatedEnvelopeBound hcontrolEnvelopeBound

omit [DecidableEq Param] in
/--
Component Chen-Han design-cross-zero local-experiment martingale route with
Lindeberg supplied by concrete two-arm envelope bounds, fixed-law
score-adjustment algebra supplied by the finite identity, and the remaining
local-experiment/Godambe obligations packaged as a compact core.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_design_cross_zero_twoArm_envelope_lindeberg_fixedLaw_score_adjustment_identity_and_local_experiment_core
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
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
    (core : EstimatedScoreLocalExperimentVarianceCore estimated)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index)
    (hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index)
    (htreatedEnvelopeBound :
      Tendsto
        (fun index =>
          treatedEnvelope index ^ 3 *
            residualThirdMomentSum (treatedSample index)
              (treatedWeight index) (treatedResidual index))
        l (nhds 0))
    (hcontrolEnvelopeBound :
      Tendsto
        (fun index =>
          controlEnvelope index ^ 3 *
            residualThirdMomentSum (controlSample index)
              (controlWeight index) (controlResidual index))
        l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_design_cross_zero_twoArm_envelope_lindeberg_fixedLaw_score_adjustment_identity
    (l := l) treatedSample controlSample treatedWeight treatedCoefficient
    treatedResidual controlWeight controlCoefficient controlResidual
    treatedEnvelope controlEnvelope geometry radius heterogeneity residual bias
    known knownVariance orthogonality estimated parameters oracleVariance
    firstStepLoading scoreCovariance hinterpret hinputLindeberg
    hgeometry_regular hcatchment hmoment_transfer hheterogeneity_moment
    hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hquad
    hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden hcross hlimit hknown_normality_transfer
    hknown_variance_transfer hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity
    htreatedWeightNonneg hcontrolWeightNonneg htreatedCoeffBound
    hcontrolCoeffBound htreatedEnvelopeBound hcontrolEnvelopeBound

omit [DecidableEq Param] in
/--
Component Chen-Han design-cross-zero local-experiment martingale route with
Lindeberg supplied by concrete two-arm envelope bounds, changing-law
score-adjustment algebra supplied by the finite identity, and the remaining
local-experiment/Godambe obligations packaged as a compact core.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_design_cross_zero_twoArm_envelope_lindeberg_changingLaw_score_adjustment_identity_and_local_experiment_core
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
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
    (core : EstimatedScoreLocalExperimentVarianceCore estimated)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoeffBound :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          |treatedCoefficient index treated| ≤ treatedEnvelope index)
    (hcontrolCoeffBound :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          |controlCoefficient index control| ≤ controlEnvelope index)
    (htreatedEnvelopeBound :
      Tendsto
        (fun index =>
          treatedEnvelope index ^ 3 *
            residualThirdMomentSum (treatedSample index)
              (treatedWeight index) (treatedResidual index))
        l (nhds 0))
    (hcontrolEnvelopeBound :
      Tendsto
        (fun index =>
          controlEnvelope index ^ 3 *
            residualThirdMomentSum (controlSample index)
              (controlWeight index) (controlResidual index))
        l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_design_cross_zero_twoArm_envelope_lindeberg_changingLaw_score_adjustment_identity
    (l := l) treatedSample controlSample treatedWeight treatedCoefficient
    treatedResidual controlWeight controlCoefficient controlResidual
    treatedEnvelope controlEnvelope geometry radius heterogeneity residual bias
    known knownVariance orthogonality estimated parameters oracleVariance
    firstStepLoading targetDriftLoading scoreCovariance hinterpret
    hinputLindeberg hgeometry_regular hcatchment hmoment_transfer
    hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hquad
    hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden hcross hlimit hknown_normality_transfer
    hknown_variance_transfer hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity
    htreatedWeightNonneg hcontrolWeightNonneg htreatedCoeffBound
    hcontrolCoeffBound htreatedEnvelopeBound hcontrolEnvelopeBound

omit [DecidableEq Param] in
/--
Component Chen-Han design-cross-zero martingale route with Lindeberg supplied
by finite score-cell coefficient loadings and the estimated-score variance
adjustment discharged by the fixed-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_design_cross_zero_finite_scoreCell_lindeberg_fixedLaw_score_adjustment_identity
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficientLoading : Index -> TreatedCell -> Real)
    (controlCoefficientLoading : Index -> ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
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
    (hgodambe_variance : estimatedVariance.godambe_variance_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoverEventually :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCoverEventually :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCover :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ index control, control ∈ controlSample index ->
        controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedCoefficientLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlCoefficientLoading index (controlScore index control))
    (htreatedCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedCoefficientLoading index cell| ≤ treatedEnvelope index)
    (hcontrolCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlCoefficientLoading index cell| ≤ controlEnvelope index)
    (htreatedThirdLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedThirdMomentLoading (treatedScore index treated) =
          |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ index control, control ∈ controlSample index ->
        controlThirdMomentLoading (controlScore index control) =
          |controlResidual index control| ^ 3)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit)
    (htreatedEnvelope : Tendsto treatedEnvelope l (nhds 0))
    (hcontrolEnvelope : Tendsto controlEnvelope l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimatedVariance.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_design_cross_zero_finite_scoreCell_lindeberg_bridges
    (l := l) treatedCells controlCells treatedSample controlSample
    treatedWeight treatedCoefficient treatedResidual controlWeight
    controlCoefficient controlResidual treatedScore controlScore
    treatedCoefficientLoading controlCoefficientLoading
    treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
    controlMassLimit treatedEnvelope controlEnvelope geometry radius
    heterogeneity residual bias known knownVariance orthogonality estimated
    estimatedVariance hinputLindeberg hgeometry_regular hcatchment
    hmoment_transfer hheterogeneity_moment hheterogeneity_variance
    hheterogeneity_transfer hheterogeneity_variance_transfer hresidual_reg
    hmartingale hquad hresidual_transfer hresidual_variance_transfer
    hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
    hbias_transfer hdecomp hden hcross hlimit hknown_normality_transfer
    hknown_variance_transfer hfirst hlocal hgodambe_normality
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      estimatedVariance.score_adjustment_algebra parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret)
    hgodambe_variance htreatedWeightNonneg hcontrolWeightNonneg
    htreatedCoverEventually hcontrolCoverEventually htreatedCover
    hcontrolCover htreatedCoefficient hcontrolCoefficient
    htreatedCoefficientLoadingBound hcontrolCoefficientLoadingBound
    htreatedThirdLoading hcontrolThirdLoading htreatedMass hcontrolMass
    htreatedEnvelope hcontrolEnvelope

omit [DecidableEq Param] in
/--
Component Chen-Han design-cross-zero martingale route with Lindeberg supplied
by finite score-cell coefficient loadings and the estimated-score variance
adjustment discharged by the changing-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_design_cross_zero_finite_scoreCell_lindeberg_changingLaw_score_adjustment_identity
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficientLoading : Index -> TreatedCell -> Real)
    (controlCoefficientLoading : Index -> ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
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
    (hgodambe_variance : estimatedVariance.godambe_variance_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoverEventually :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCoverEventually :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCover :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ index control, control ∈ controlSample index ->
        controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedCoefficientLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlCoefficientLoading index (controlScore index control))
    (htreatedCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedCoefficientLoading index cell| ≤ treatedEnvelope index)
    (hcontrolCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlCoefficientLoading index cell| ≤ controlEnvelope index)
    (htreatedThirdLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedThirdMomentLoading (treatedScore index treated) =
          |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ index control, control ∈ controlSample index ->
        controlThirdMomentLoading (controlScore index control) =
          |controlResidual index control| ^ 3)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit)
    (htreatedEnvelope : Tendsto treatedEnvelope l (nhds 0))
    (hcontrolEnvelope : Tendsto controlEnvelope l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimatedVariance.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_design_cross_zero_finite_scoreCell_lindeberg_bridges
    (l := l) treatedCells controlCells treatedSample controlSample
    treatedWeight treatedCoefficient treatedResidual controlWeight
    controlCoefficient controlResidual treatedScore controlScore
    treatedCoefficientLoading controlCoefficientLoading
    treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
    controlMassLimit treatedEnvelope controlEnvelope geometry radius
    heterogeneity residual bias known knownVariance orthogonality estimated
    estimatedVariance hinputLindeberg hgeometry_regular hcatchment
    hmoment_transfer hheterogeneity_moment hheterogeneity_variance
    hheterogeneity_transfer hheterogeneity_variance_transfer hresidual_reg
    hmartingale hquad hresidual_transfer hresidual_variance_transfer
    hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
    hbias_transfer hdecomp hden hcross hlimit hknown_normality_transfer
    hknown_variance_transfer hfirst hlocal hgodambe_normality
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      estimatedVariance.score_adjustment_algebra parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret)
    hgodambe_variance htreatedWeightNonneg hcontrolWeightNonneg
    htreatedCoverEventually hcontrolCoverEventually htreatedCover
    hcontrolCover htreatedCoefficient hcontrolCoefficient
    htreatedCoefficientLoadingBound hcontrolCoefficientLoadingBound
    htreatedThirdLoading hcontrolThirdLoading htreatedMass hcontrolMass
    htreatedEnvelope hcontrolEnvelope

omit [DecidableEq Param] in
/--
Component Chen-Han design-cross-zero local-experiment martingale route with
Lindeberg supplied by finite score-cell coefficient loadings and the local
variance adjustment discharged by the fixed-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_design_cross_zero_finite_scoreCell_lindeberg_fixedLaw_score_adjustment_identity
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficientLoading : Index -> TreatedCell -> Real)
    (controlCoefficientLoading : Index -> ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
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
    (hgodambe : estimated.godambe_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoverEventually :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCoverEventually :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCover :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ index control, control ∈ controlSample index ->
        controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedCoefficientLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlCoefficientLoading index (controlScore index control))
    (htreatedCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedCoefficientLoading index cell| ≤ treatedEnvelope index)
    (hcontrolCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlCoefficientLoading index cell| ≤ controlEnvelope index)
    (htreatedThirdLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedThirdMomentLoading (treatedScore index treated) =
          |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ index control, control ∈ controlSample index ->
        controlThirdMomentLoading (controlScore index control) =
          |controlResidual index control| ^ 3)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit)
    (htreatedEnvelope : Tendsto treatedEnvelope l (nhds 0))
    (hcontrolEnvelope : Tendsto controlEnvelope l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_design_cross_zero_finite_scoreCell_lindeberg_bridges
    (l := l) treatedCells controlCells treatedSample controlSample
    treatedWeight treatedCoefficient treatedResidual controlWeight
    controlCoefficient controlResidual treatedScore controlScore
    treatedCoefficientLoading controlCoefficientLoading
    treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
    controlMassLimit treatedEnvelope controlEnvelope geometry radius
    heterogeneity residual bias known knownVariance orthogonality estimated
    hinputLindeberg hgeometry_regular hcatchment hmoment_transfer
    hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hquad
    hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden hcross hlimit hknown_normality_transfer
    hknown_variance_transfer hfirst hscore hfunctional hequicontinuity
    (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
      estimated.score_adjustment_algebra parameters oracleVariance
      firstStepLoading scoreCovariance hinterpret)
    hgodambe htreatedWeightNonneg hcontrolWeightNonneg
    htreatedCoverEventually hcontrolCoverEventually htreatedCover
    hcontrolCover htreatedCoefficient hcontrolCoefficient
    htreatedCoefficientLoadingBound hcontrolCoefficientLoadingBound
    htreatedThirdLoading hcontrolThirdLoading htreatedMass hcontrolMass
    htreatedEnvelope hcontrolEnvelope

omit [DecidableEq Param] in
/--
Component Chen-Han design-cross-zero local-experiment martingale route with
Lindeberg supplied by finite score-cell coefficient loadings and the local
variance adjustment discharged by the changing-law finite identity.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_design_cross_zero_finite_scoreCell_lindeberg_changingLaw_score_adjustment_identity
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficientLoading : Index -> TreatedCell -> Real)
    (controlCoefficientLoading : Index -> ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
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
    (hgodambe : estimated.godambe_identity)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoverEventually :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCoverEventually :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCover :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ index control, control ∈ controlSample index ->
        controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedCoefficientLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlCoefficientLoading index (controlScore index control))
    (htreatedCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedCoefficientLoading index cell| ≤ treatedEnvelope index)
    (hcontrolCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlCoefficientLoading index cell| ≤ controlEnvelope index)
    (htreatedThirdLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedThirdMomentLoading (treatedScore index treated) =
          |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ index control, control ∈ controlSample index ->
        controlThirdMomentLoading (controlScore index control) =
          |controlResidual index control| ^ 3)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit)
    (htreatedEnvelope : Tendsto treatedEnvelope l (nhds 0))
    (hcontrolEnvelope : Tendsto controlEnvelope l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_design_cross_zero_finite_scoreCell_lindeberg_bridges
    (l := l) treatedCells controlCells treatedSample controlSample
    treatedWeight treatedCoefficient treatedResidual controlWeight
    controlCoefficient controlResidual treatedScore controlScore
    treatedCoefficientLoading controlCoefficientLoading
    treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
    controlMassLimit treatedEnvelope controlEnvelope geometry radius
    heterogeneity residual bias known knownVariance orthogonality estimated
    hinputLindeberg hgeometry_regular hcatchment hmoment_transfer
    hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hquad
    hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden hcross hlimit hknown_normality_transfer
    hknown_variance_transfer hfirst hscore hfunctional hequicontinuity
    (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
      estimated.score_adjustment_algebra parameters oracleVariance
      firstStepLoading targetDriftLoading scoreCovariance hinterpret)
    hgodambe htreatedWeightNonneg hcontrolWeightNonneg
    htreatedCoverEventually hcontrolCoverEventually htreatedCover
    hcontrolCover htreatedCoefficient hcontrolCoefficient
    htreatedCoefficientLoadingBound hcontrolCoefficientLoadingBound
    htreatedThirdLoading hcontrolThirdLoading htreatedMass hcontrolMass
    htreatedEnvelope hcontrolEnvelope

omit [DecidableEq Param] in
/--
Component Chen-Han design-cross-zero local-experiment martingale route with
Lindeberg supplied by finite score-cell coefficient loadings, fixed-law
score-adjustment algebra supplied by the finite identity, and the remaining
local-experiment/Godambe obligations packaged as a compact core.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_design_cross_zero_finite_scoreCell_lindeberg_fixedLaw_score_adjustment_identity_and_local_experiment_core
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficientLoading : Index -> TreatedCell -> Real)
    (controlCoefficientLoading : Index -> ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
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
    (core : EstimatedScoreLocalExperimentVarianceCore estimated)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoverEventually :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCoverEventually :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCover :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ index control, control ∈ controlSample index ->
        controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedCoefficientLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlCoefficientLoading index (controlScore index control))
    (htreatedCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedCoefficientLoading index cell| ≤ treatedEnvelope index)
    (hcontrolCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlCoefficientLoading index cell| ≤ controlEnvelope index)
    (htreatedThirdLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedThirdMomentLoading (treatedScore index treated) =
          |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ index control, control ∈ controlSample index ->
        controlThirdMomentLoading (controlScore index control) =
          |controlResidual index control| ^ 3)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit)
    (htreatedEnvelope : Tendsto treatedEnvelope l (nhds 0))
    (hcontrolEnvelope : Tendsto controlEnvelope l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_design_cross_zero_finite_scoreCell_lindeberg_fixedLaw_score_adjustment_identity
    (l := l) treatedCells controlCells treatedSample controlSample
    treatedWeight treatedCoefficient treatedResidual controlWeight
    controlCoefficient controlResidual treatedScore controlScore
    treatedCoefficientLoading controlCoefficientLoading
    treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
    controlMassLimit treatedEnvelope controlEnvelope geometry radius
    heterogeneity residual bias known knownVariance orthogonality estimated
    parameters oracleVariance firstStepLoading scoreCovariance hinterpret
    hinputLindeberg hgeometry_regular hcatchment hmoment_transfer
    hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hquad
    hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden hcross hlimit hknown_normality_transfer
    hknown_variance_transfer hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity
    htreatedWeightNonneg hcontrolWeightNonneg htreatedCoverEventually
    hcontrolCoverEventually htreatedCover hcontrolCover htreatedCoefficient
    hcontrolCoefficient htreatedCoefficientLoadingBound
    hcontrolCoefficientLoadingBound htreatedThirdLoading hcontrolThirdLoading
    htreatedMass hcontrolMass htreatedEnvelope hcontrolEnvelope

omit [DecidableEq Param] in
/--
Component Chen-Han design-cross-zero local-experiment martingale route with
Lindeberg supplied by finite score-cell coefficient loadings, changing-law
score-adjustment algebra supplied by the finite identity, and the remaining
local-experiment/Godambe obligations packaged as a compact core.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_design_cross_zero_finite_scoreCell_lindeberg_changingLaw_score_adjustment_identity_and_local_experiment_core
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficientLoading : Index -> TreatedCell -> Real)
    (controlCoefficientLoading : Index -> ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
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
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        residual.conditional_lindeberg)
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
    (core : EstimatedScoreLocalExperimentVarianceCore estimated)
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoverEventually :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCoverEventually :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCover :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ index control, control ∈ controlSample index ->
        controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedCoefficientLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlCoefficientLoading index (controlScore index control))
    (htreatedCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ treatedCells ->
          |treatedCoefficientLoading index cell| ≤ treatedEnvelope index)
    (hcontrolCoefficientLoadingBound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ controlCells ->
          |controlCoefficientLoading index cell| ≤ controlEnvelope index)
    (htreatedThirdLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedThirdMomentLoading (treatedScore index treated) =
          |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ index control, control ∈ controlSample index ->
        controlThirdMomentLoading (controlScore index control) =
          |controlResidual index control| ^ 3)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit)
    (htreatedEnvelope : Tendsto treatedEnvelope l (nhds 0))
    (hcontrolEnvelope : Tendsto controlEnvelope l (nhds 0)) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_design_cross_zero_finite_scoreCell_lindeberg_changingLaw_score_adjustment_identity
    (l := l) treatedCells controlCells treatedSample controlSample
    treatedWeight treatedCoefficient treatedResidual controlWeight
    controlCoefficient controlResidual treatedScore controlScore
    treatedCoefficientLoading controlCoefficientLoading
    treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
    controlMassLimit treatedEnvelope controlEnvelope geometry radius
    heterogeneity residual bias known knownVariance orthogonality estimated
    parameters oracleVariance firstStepLoading targetDriftLoading
    scoreCovariance hinterpret hinputLindeberg hgeometry_regular hcatchment
    hmoment_transfer hheterogeneity_moment hheterogeneity_variance
    hheterogeneity_transfer hheterogeneity_variance_transfer hresidual_reg
    hmartingale hquad hresidual_transfer hresidual_variance_transfer
    hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
    hbias_transfer hdecomp hden hcross hlimit hknown_normality_transfer
    hknown_variance_transfer hfirst hscore
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity
    htreatedWeightNonneg hcontrolWeightNonneg htreatedCoverEventually
    hcontrolCoverEventually htreatedCover hcontrolCover htreatedCoefficient
    hcontrolCoefficient htreatedCoefficientLoadingBound
    hcontrolCoefficientLoadingBound htreatedThirdLoading hcontrolThirdLoading
    htreatedMass hcontrolMass htreatedEnvelope hcontrolEnvelope

end WDSM
end Matching
end StatInference
