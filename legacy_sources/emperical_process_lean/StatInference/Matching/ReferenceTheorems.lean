import StatInference.Matching.WDSM.AsymptoticInterfaces
import StatInference.Matching.WDSM.IdentificationInterfaces

/-!
# Named reference-theorem interfaces for WDSM

The WDSM project relies on prior matching theory from Abadie-Imbens,
Yang-Zhang, and Chen-Han.  This module records those dependencies as explicit
Lean bridge interfaces.  These are not substitutes for porting the reference
proofs; they make every imported reference theorem a named assumption until it
is reproduced locally.
-/

namespace StatInference
namespace Matching
namespace WDSM

/-- Abadie-Imbens known-score matching asymptotics, abstracted as a bridge. -/
structure AbadieImbensKnownScoreBridge where
  matching_regular : Prop
  bias_correction_valid : Prop
  known_score_linear_representation : Prop
  known_score_limit : Prop
  bridge :
    matching_regular ->
    bias_correction_valid ->
    known_score_linear_representation ->
    known_score_limit

theorem abadie_imbens_known_score_limit_of_bridge
    (b : AbadieImbensKnownScoreBridge)
    (hregular : b.matching_regular)
    (hbias : b.bias_correction_valid)
    (hlinear : b.known_score_linear_representation) :
    b.known_score_limit :=
  b.bridge hregular hbias hlinear

/-- Abadie-Imbens estimated-score local asymptotic adjustment. -/
structure AbadieImbensEstimatedScoreBridge where
  known_score_limit : Prop
  first_step_local_asymptotic_normality : Prop
  matching_functional_local_sensitivity : Prop
  estimated_score_limit : Prop
  bridge :
    known_score_limit ->
    first_step_local_asymptotic_normality ->
    matching_functional_local_sensitivity ->
    estimated_score_limit

theorem abadie_imbens_estimated_score_limit_of_bridge
    (b : AbadieImbensEstimatedScoreBridge)
    (hknown : b.known_score_limit)
    (hfirst : b.first_step_local_asymptotic_normality)
    (hsensitivity : b.matching_functional_local_sensitivity) :
    b.estimated_score_limit :=
  b.bridge hknown hfirst hsensitivity

/-- Yang-Zhang double-score and multiply robust score-reduction theorem. -/
structure YangZhangDoubleScoreBridge where
  treatment_ignorability : Prop
  propensity_route_correct : Prop
  prognostic_route_correct : Prop
  reduced_double_score_balancing : Prop
  double_robust_identification : Prop
  balancing_bridge :
    treatment_ignorability ->
    (propensity_route_correct ∨ prognostic_route_correct) ->
    reduced_double_score_balancing
  identification_bridge :
    reduced_double_score_balancing ->
    double_robust_identification

theorem yang_zhang_balancing_of_bridge
    (b : YangZhangDoubleScoreBridge)
    (hignorability : b.treatment_ignorability)
    (hroute : b.propensity_route_correct ∨ b.prognostic_route_correct) :
    b.reduced_double_score_balancing :=
  b.balancing_bridge hignorability hroute

theorem yang_zhang_identification_of_bridge
    (b : YangZhangDoubleScoreBridge)
    (hbalance : b.reduced_double_score_balancing) :
    b.double_robust_identification :=
  b.identification_bridge hbalance

/-- Chen-Han limiting matching-frequency and variance geometry. -/
structure ChenHanGeometryBridge where
  score_density_regular : Prop
  nearest_neighbor_catchment_moments : Prop
  reuse_frequency_moment_limits : Prop
  limiting_variance_formula : Prop
  moment_bridge :
    score_density_regular ->
    nearest_neighbor_catchment_moments ->
    reuse_frequency_moment_limits
  variance_bridge :
    reuse_frequency_moment_limits ->
    limiting_variance_formula

theorem chen_han_reuse_moment_limits_of_bridge
    (b : ChenHanGeometryBridge)
    (hregular : b.score_density_regular)
    (hcatchment : b.nearest_neighbor_catchment_moments) :
    b.reuse_frequency_moment_limits :=
  b.moment_bridge hregular hcatchment

theorem chen_han_limiting_variance_of_bridge
    (b : ChenHanGeometryBridge)
    (hmoments : b.reuse_frequency_moment_limits) :
    b.limiting_variance_formula :=
  b.variance_bridge hmoments

/--
Residual CLT and residual variance formula from Chen-Han reuse-frequency
moments plus the residual-array CLT/variance bridge.
-/
theorem residual_clt_and_variance_formula_of_chen_han_reference_bridge
    (geometry : ChenHanGeometryBridge)
    (residual : ResidualArrayCLTVarianceBridge)
    (hregular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hquad : residual.quadratic_variation_stabilization) :
    residual.residual_clt ∧ residual.residual_variance_formula := by
  have hreuse : geometry.reuse_frequency_moment_limits :=
    chen_han_reuse_moment_limits_of_bridge geometry hregular hcatchment
  exact residual_clt_and_variance_formula_of_reuse_moments residual
    (hmoment_transfer hreuse) hresidual_reg hquad

/--
Chen-Han-style nearest-neighbor radius-rate input for the WDSM bias term.

This is separate from the reuse-frequency moment bridge because the bias proof
uses a scaled survey-weighted average local score-radius rate, while the
variance proof uses catchment/reuse moment limits.
-/
structure ChenHanRadiusRateBridge where
  score_density_regular : Prop
  nearest_neighbor_radius_geometry : Prop
  weighted_average_radius_rate : Prop
  bridge :
    score_density_regular ->
    nearest_neighbor_radius_geometry ->
    weighted_average_radius_rate

theorem chen_han_weighted_average_radius_rate_of_bridge
    (b : ChenHanRadiusRateBridge)
    (hregular : b.score_density_regular)
    (hradius_geometry : b.nearest_neighbor_radius_geometry) :
    b.weighted_average_radius_rate :=
  b.bridge hregular hradius_geometry

/--
Reference theorem wrapper feeding the Chen-Han radius-rate input into the
average-radius matching-bias bridge used by the WDSM asymptotic interface.
-/
theorem matching_discrepancy_negligible_of_chen_han_radius_bridge
    (radius : ChenHanRadiusRateBridge)
    (bias : AverageRadiusBiasBridge)
    (hregular : radius.score_density_regular)
    (hradius_geometry : radius.nearest_neighbor_radius_geometry)
    (hradius_transfer :
      radius.weighted_average_radius_rate ->
        bias.weighted_average_radius_rate)
    (hfinite : bias.eventual_finite_matching_regular)
    (hlipschitz : bias.lipschitz_score_mean_regular) :
    bias.matching_discrepancy_negligible := by
  have hradius : radius.weighted_average_radius_rate :=
    chen_han_weighted_average_radius_rate_of_bridge radius
      hregular hradius_geometry
  exact matching_discrepancy_negligible_of_average_radius bias
    hfinite hlipschitz (hradius_transfer hradius)

/--
Known-score WDSM asymptotic normality from the Chen-Han reference interfaces.
The reuse-frequency moment bridge feeds the residual CLT route, while the
separate radius-rate bridge feeds the average-radius bias route.
-/
theorem known_score_asymptotic_normality_of_chen_han_reference_bridges
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualArrayCLTBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
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
    (hheterogeneity : known.heterogeneity_clt) :
    known.asymptotic_normality := by
  have hreuse : geometry.reuse_frequency_moment_limits :=
    chen_han_reuse_moment_limits_of_bridge geometry
      hgeometry_regular hcatchment
  have hresidual : residual.residual_clt :=
    residual_clt_of_reuse_moments residual
      (hmoment_transfer hreuse) hresidual_reg hquad
  have hbias : bias.matching_discrepancy_negligible :=
    matching_discrepancy_negligible_of_chen_han_radius_bridge radius bias
      hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
  exact known_score_asymptotic_normality_of_bridge known
    hdecomp hden hheterogeneity
    (hresidual_transfer hresidual)
    (hbias_transfer hbias)

/--
Estimated-score WDSM asymptotic normality from the Chen-Han reference
interfaces plus the estimated-score local expansion and Godambe inputs.
-/
theorem estimated_score_asymptotic_normality_of_chen_han_reference_bridges
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualArrayCLTBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (estimated : EstimatedScoreAsymptoticBridge)
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
    (hgodambe : estimated.godambe_variance_identity) :
    estimated.estimated_score_asymptotic_normality := by
  have hknown : known.asymptotic_normality :=
    known_score_asymptotic_normality_of_chen_han_reference_bridges
      geometry radius residual bias known hgeometry_regular hcatchment
      hmoment_transfer hresidual_reg hquad hresidual_transfer
      hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
      hbias_transfer hdecomp hden hheterogeneity
  exact estimated_score_asymptotic_normality_of_bridge estimated
    (hknown_transfer hknown) hfirst hlocal hgodambe

/--
Chen-Han reference bridge delivering both the WDSM known-score asymptotic
normality conclusion and the Chen-Han limiting variance formula.
-/
theorem known_score_asymptotic_normality_and_limiting_variance_of_chen_han_reference_bridges
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualArrayCLTBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
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
    (hheterogeneity : known.heterogeneity_clt) :
    known.asymptotic_normality ∧ geometry.limiting_variance_formula := by
  have hknown : known.asymptotic_normality :=
    known_score_asymptotic_normality_of_chen_han_reference_bridges
      geometry radius residual bias known hgeometry_regular hcatchment
      hmoment_transfer hresidual_reg hquad hresidual_transfer
      hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
      hbias_transfer hdecomp hden hheterogeneity
  have hreuse : geometry.reuse_frequency_moment_limits :=
    chen_han_reuse_moment_limits_of_bridge geometry
      hgeometry_regular hcatchment
  exact ⟨hknown, chen_han_limiting_variance_of_bridge geometry hreuse⟩

/--
Known-score WDSM asymptotic normality together with heterogeneity and residual
variance formulas from the Chen-Han reference inputs and a heterogeneity
CLT/variance bridge.
-/
theorem known_score_asymptotic_normality_and_component_variance_formulas_of_chen_han_reference_bridges
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
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
    (hden : known.denominator_stabilization) :
    known.asymptotic_normality ∧
      heterogeneity.heterogeneity_variance_formula ∧
        residual.residual_variance_formula := by
  have hreuse : geometry.reuse_frequency_moment_limits :=
    chen_han_reuse_moment_limits_of_bridge geometry
      hgeometry_regular hcatchment
  have hheterogeneity_pair :
      heterogeneity.heterogeneity_clt ∧
        heterogeneity.heterogeneity_variance_formula :=
    heterogeneity_clt_and_variance_formula_of_bridge heterogeneity
      hheterogeneity_moment hheterogeneity_variance
  have hresidual_pair :
      residual.residual_clt ∧ residual.residual_variance_formula :=
    residual_clt_and_variance_formula_of_reuse_moments residual
      (hmoment_transfer hreuse) hresidual_reg hquad
  have hbias : bias.matching_discrepancy_negligible :=
    matching_discrepancy_negligible_of_chen_han_radius_bridge radius bias
      hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
  have hknown : known.asymptotic_normality :=
    known_score_asymptotic_normality_of_bridge known
      hdecomp hden
      (hheterogeneity_transfer hheterogeneity_pair.1)
      (hresidual_transfer hresidual_pair.1)
      (hbias_transfer hbias)
  exact ⟨hknown, hheterogeneity_pair.2, hresidual_pair.2⟩

/--
Known-score WDSM asymptotic normality and known-score variance formula from
Chen-Han reuse/radius inputs, heterogeneity variance inputs, and the component
variance additivity bridge.
-/
theorem known_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_bridges
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (variance : KnownScoreVarianceFormulaBridge)
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
        variance.heterogeneity_variance_formula)
    (hresidual_reg : residual.residual_moment_regularity)
    (hquad : residual.quadratic_variation_stabilization)
    (hresidual_transfer : residual.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residual.residual_variance_formula ->
        variance.residual_variance_formula)
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
    (horthogonality : variance.component_orthogonality) :
    known.asymptotic_normality ∧ variance.known_score_variance_formula := by
  have hcomponents :=
    known_score_asymptotic_normality_and_component_variance_formulas_of_chen_han_reference_bridges
      geometry radius heterogeneity residual bias known hgeometry_regular
      hcatchment hmoment_transfer hheterogeneity_moment
      hheterogeneity_variance hheterogeneity_transfer hresidual_reg hquad
      hresidual_transfer hradius_regular hradius_geometry hradius_transfer
      hfinite hlipschitz hbias_transfer hdecomp hden
  have hvariance : variance.known_score_variance_formula :=
    known_score_variance_formula_of_component_variances variance
      (hheterogeneity_variance_transfer hcomponents.2.1)
      (hresidual_variance_transfer hcomponents.2.2)
      horthogonality
  exact ⟨hcomponents.1, hvariance⟩

/--
Estimated-score WDSM asymptotic normality and estimated-score variance formula
from the Chen-Han reference inputs, using component variance formulas to obtain
the known-score variance formula before applying the Godambe adjustment.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_bridges
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (estimated : EstimatedScoreAsymptoticBridge)
    (estimatedVariance : EstimatedScoreVarianceFormulaBridge)
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
    (hadjustment : estimatedVariance.score_adjustment_algebra)
    (hgodambe_variance : estimatedVariance.godambe_variance_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimatedVariance.estimated_score_variance_formula := by
  have hknown :=
    known_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_bridges
      geometry radius heterogeneity residual bias known knownVariance
      hgeometry_regular hcatchment hmoment_transfer hheterogeneity_moment
      hheterogeneity_variance hheterogeneity_transfer
      hheterogeneity_variance_transfer hresidual_reg hquad hresidual_transfer
      hresidual_variance_transfer hradius_regular hradius_geometry
      hradius_transfer hfinite hlipschitz hbias_transfer hdecomp hden
      horthogonality
  have hnormal : estimated.estimated_score_asymptotic_normality :=
    estimated_score_asymptotic_normality_of_bridge estimated
      (hknown_normality_transfer hknown.1) hfirst hlocal hgodambe_normality
  have hvariance :
      estimatedVariance.estimated_score_variance_formula :=
    estimated_score_variance_formula_of_bridge estimatedVariance
      (hknown_variance_transfer hknown.2) hadjustment hgodambe_variance
  exact ⟨hnormal, hvariance⟩

/--
Estimated-score limiting variance formula from the Chen-Han known-score
limiting variance formula and the estimated-score Godambe adjustment bridge.
-/
theorem estimated_score_variance_formula_of_chen_han_reference_bridge
    (geometry : ChenHanGeometryBridge)
    (variance : EstimatedScoreVarianceFormulaBridge)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hknown_variance_transfer :
      geometry.limiting_variance_formula ->
        variance.known_score_variance_formula)
    (hadjustment : variance.score_adjustment_algebra)
    (hgodambe : variance.godambe_variance_identity) :
    variance.estimated_score_variance_formula := by
  have hreuse : geometry.reuse_frequency_moment_limits :=
    chen_han_reuse_moment_limits_of_bridge geometry
      hgeometry_regular hcatchment
  have hknown_variance : geometry.limiting_variance_formula :=
    chen_han_limiting_variance_of_bridge geometry hreuse
  exact estimated_score_variance_formula_of_bridge variance
    (hknown_variance_transfer hknown_variance) hadjustment hgodambe

/--
Estimated-score WDSM asymptotic normality together with its estimated-score
variance formula from the Chen-Han reference inputs and Godambe layer.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_bridges
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualArrayCLTBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (estimated : EstimatedScoreAsymptoticBridge)
    (variance : EstimatedScoreVarianceFormulaBridge)
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
    (hadjustment : variance.score_adjustment_algebra)
    (hgodambe_variance : variance.godambe_variance_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      variance.estimated_score_variance_formula := by
  have hnormal :
      estimated.estimated_score_asymptotic_normality :=
    estimated_score_asymptotic_normality_of_chen_han_reference_bridges
      geometry radius residual bias known estimated hgeometry_regular
      hcatchment hmoment_transfer hresidual_reg hquad hresidual_transfer
      hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
      hbias_transfer hdecomp hden hheterogeneity hknown_transfer hfirst
      hlocal hgodambe_normality
  have hvariance :
      variance.estimated_score_variance_formula :=
    estimated_score_variance_formula_of_chen_han_reference_bridge
      geometry variance hgeometry_regular hcatchment hknown_variance_transfer
      hadjustment hgodambe_variance
  exact ⟨hnormal, hvariance⟩

end WDSM
end Matching
end StatInference
