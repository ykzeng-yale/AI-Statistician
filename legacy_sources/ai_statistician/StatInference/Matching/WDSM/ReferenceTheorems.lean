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
  survey_weighted_score_mean_representation : Prop
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

/-- Convert a Yang-Zhang balancing theorem into the internal
`DoubleScoreBalancingBridge` shape. -/
def doubleScoreBalancingBridgeOfYangZhang
    (b : YangZhangDoubleScoreBridge)
    (_hignorability : b.treatment_ignorability)
    (_hroute : b.propensity_route_correct ∨ b.prognostic_route_correct) :
    DoubleScoreBalancingBridge :=
{ treatment_unconfoundedness := b.treatment_ignorability
  propensity_component_balances := b.propensity_route_correct
  prognostic_component_balances := b.prognostic_route_correct
  double_score_balancing := b.reduced_double_score_balancing
  propensity_route := by
    intro hUnconf hProp
    exact yang_zhang_balancing_of_bridge b hUnconf (Or.inl hProp)
  prognostic_route := by
    intro hUnconf hPrognostic
    exact yang_zhang_balancing_of_bridge b hUnconf (Or.inr hPrognostic) }

/-- Recover internal double-score balancing conclusions through Yang-Zhang routes. -/
theorem double_score_balancing_of_yang_zhang_propensity_route
    (b : YangZhangDoubleScoreBridge)
    (hignorability : b.treatment_ignorability)
    (hpropensity : b.propensity_route_correct) :
    (doubleScoreBalancingBridgeOfYangZhang b hignorability
      (Or.inl hpropensity)).double_score_balancing :=
  by
    simpa [doubleScoreBalancingBridgeOfYangZhang] using
      (yang_zhang_balancing_of_bridge b hignorability (Or.inl hpropensity))

/-- Recover internal double-score balancing conclusions through Yang-Zhang routes. -/
theorem double_score_balancing_of_yang_zhang_prognostic_route
    (b : YangZhangDoubleScoreBridge)
    (hignorability : b.treatment_ignorability)
    (hprognostic : b.prognostic_route_correct) :
    (doubleScoreBalancingBridgeOfYangZhang b hignorability
      (Or.inr hprognostic)).double_score_balancing :=
  by
    simpa [doubleScoreBalancingBridgeOfYangZhang] using
      (yang_zhang_balancing_of_bridge b hignorability (Or.inr hprognostic))

/--
Promote a Yang-Zhang reference bridge and score-identification postulate into
the internal survey-weighted score mean interface.  The survey-weighted score
mean representation remains an explicit Yang-Zhang bridge field; it is not
discharged by this wrapper.
-/
def surveyWeightedScoreMeanBridgeOfYangZhang
    (b : YangZhangDoubleScoreBridge)
    (_hignorability : b.treatment_ignorability)
    (_hroute : b.propensity_route_correct ∨ b.prognostic_route_correct)
  (hident : b.double_robust_identification) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing :=
    b.reduced_double_score_balancing
  survey_weighted_score_mean_representation := b.survey_weighted_score_mean_representation
  score_space_identification := b.double_robust_identification
  bridge :=
    by
      intro _hbalance _hweightedRep
      exact hident
  }

/--
Route-driven Yang-Zhang score-mean bridge.  Unlike
`surveyWeightedScoreMeanBridgeOfYangZhang`, this adapter does not take the
double-robust identification conclusion as an external input: the bridge field
derives it from the reduced double-score balancing statement through the
Yang-Zhang identification bridge.
-/
def surveyWeightedScoreMeanBridgeOfYangZhangRoutes
    (b : YangZhangDoubleScoreBridge) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing := b.reduced_double_score_balancing
  survey_weighted_score_mean_representation :=
    b.survey_weighted_score_mean_representation
  score_space_identification := b.double_robust_identification
  bridge := by
    intro hbalance _hweightedRep
    exact yang_zhang_identification_of_bridge b hbalance }

/--
Compose Yang-Zhang ignorability plus either correct-score route with the
survey-weighted score-mean interface.  The final identification is obtained
from the bridge's route proof, not assumed as a premise.
-/
theorem score_space_identification_of_yang_zhang_routes
    (b : YangZhangDoubleScoreBridge)
    (hignorability : b.treatment_ignorability)
    (hroute : b.propensity_route_correct ∨ b.prognostic_route_correct)
    (hweightedRep : b.survey_weighted_score_mean_representation) :
    b.double_robust_identification :=
  score_space_identification_of_bridge
    (surveyWeightedScoreMeanBridgeOfYangZhangRoutes b)
    (yang_zhang_balancing_of_bridge b hignorability hroute)
    hweightedRep

/--
Propensity-route Yang-Zhang score-mean bridge.  The balancing field exposed to
downstream WDSM code is the propensity-route correctness assumption itself;
the bridge composes it with treatment ignorability and Yang-Zhang's
identification bridge.
-/
def surveyWeightedScoreMeanBridgeOfYangZhangPropensityRoute
    (b : YangZhangDoubleScoreBridge)
    (hignorability : b.treatment_ignorability) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing := b.propensity_route_correct
  survey_weighted_score_mean_representation :=
    b.survey_weighted_score_mean_representation
  score_space_identification := b.double_robust_identification
  bridge := by
    intro hpropensity _hweightedRep
    exact
      yang_zhang_identification_of_bridge b
        (yang_zhang_balancing_of_bridge b hignorability
          (Or.inl hpropensity)) }

/--
Prognostic-route Yang-Zhang score-mean bridge.  This is the symmetric
correct-prognostic-score adapter, with no final identification conclusion
assumed as an input.
-/
def surveyWeightedScoreMeanBridgeOfYangZhangPrognosticRoute
    (b : YangZhangDoubleScoreBridge)
    (hignorability : b.treatment_ignorability) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing := b.prognostic_route_correct
  survey_weighted_score_mean_representation :=
    b.survey_weighted_score_mean_representation
  score_space_identification := b.double_robust_identification
  bridge := by
    intro hprognostic _hweightedRep
    exact
      yang_zhang_identification_of_bridge b
        (yang_zhang_balancing_of_bridge b hignorability
          (Or.inr hprognostic)) }

/--
Direct score-space identification from the Yang-Zhang propensity route through
the route-specific score-mean bridge.
-/
theorem score_space_identification_of_yang_zhang_propensity_route
    (b : YangZhangDoubleScoreBridge)
    (hignorability : b.treatment_ignorability)
    (hpropensity : b.propensity_route_correct)
    (hweightedRep : b.survey_weighted_score_mean_representation) :
    b.double_robust_identification :=
  score_space_identification_of_bridge
    (surveyWeightedScoreMeanBridgeOfYangZhangPropensityRoute b hignorability)
    hpropensity hweightedRep

/--
Direct score-space identification from the Yang-Zhang prognostic route through
the route-specific score-mean bridge.
-/
theorem score_space_identification_of_yang_zhang_prognostic_route
    (b : YangZhangDoubleScoreBridge)
    (hignorability : b.treatment_ignorability)
    (hprognostic : b.prognostic_route_correct)
    (hweightedRep : b.survey_weighted_score_mean_representation) :
    b.double_robust_identification :=
  score_space_identification_of_bridge
    (surveyWeightedScoreMeanBridgeOfYangZhangPrognosticRoute b hignorability)
    hprognostic hweightedRep

/--
Compose a lower score-mean bridge, such as the primitive-residual selected
Hájek bridge, with the Yang-Zhang reference bridge.  The lower bridge proves
its own score-space identification from its balancing and representation
premises; a caller only supplies the interpretation of that proved endpoint as
one of the Yang-Zhang correct-score routes and the map from the lower
representation premise to the Yang-Zhang representation premise.
-/
def surveyWeightedScoreMeanBridgeOfYangZhangLowerScoreMeanRoute
    (b : YangZhangDoubleScoreBridge)
    (lower : SurveyWeightedScoreMeanBridge)
    (hignorability : b.treatment_ignorability)
    (hlowerRoute :
      lower.score_space_identification ->
        b.propensity_route_correct ∨ b.prognostic_route_correct)
    (hlowerWeighted :
      lower.survey_weighted_score_mean_representation ->
        b.survey_weighted_score_mean_representation) :
    SurveyWeightedScoreMeanBridge :=
{ double_score_balancing := lower.double_score_balancing
  survey_weighted_score_mean_representation :=
    lower.survey_weighted_score_mean_representation
  score_space_identification := b.double_robust_identification
  bridge := by
    intro hlowerBalance hlowerWeightedRep
    exact
      score_space_identification_of_yang_zhang_routes b hignorability
        (hlowerRoute
          (score_space_identification_of_bridge lower hlowerBalance
            hlowerWeightedRep))
        (hlowerWeighted hlowerWeightedRep) }

/--
Direct endpoint form of
`surveyWeightedScoreMeanBridgeOfYangZhangLowerScoreMeanRoute`.  It reduces a
Yang-Zhang final-identification call to the lower bridge's primitive premises,
plus explicit interpretation maps, instead of taking the Yang-Zhang route or
double-robust identification conclusion as assumptions.
-/
theorem score_space_identification_of_yang_zhang_lower_score_mean_route
    (b : YangZhangDoubleScoreBridge)
    (lower : SurveyWeightedScoreMeanBridge)
    (hignorability : b.treatment_ignorability)
    (hlowerRoute :
      lower.score_space_identification ->
        b.propensity_route_correct ∨ b.prognostic_route_correct)
    (hlowerWeighted :
      lower.survey_weighted_score_mean_representation ->
        b.survey_weighted_score_mean_representation)
    (hlowerBalance : lower.double_score_balancing)
    (hlowerWeightedRep : lower.survey_weighted_score_mean_representation) :
    b.double_robust_identification :=
  score_space_identification_of_bridge
    (surveyWeightedScoreMeanBridgeOfYangZhangLowerScoreMeanRoute b lower
      hignorability hlowerRoute hlowerWeighted)
    hlowerBalance hlowerWeightedRep

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
View a Chen-Han geometry reference bridge as the weighted WDSM geometry-moment
bridge consumed by the generic asymptotic interface.
-/
def weightedGeometryMomentBridgeOfChenHan
    (b : ChenHanGeometryBridge) : WeightedGeometryMomentBridge where
  score_space_regularity := b.score_density_regular
  chen_han_catchment_input := b.nearest_neighbor_catchment_moments
  exact_weighted_reuse_moment_limits := b.reuse_frequency_moment_limits
  bridge := b.moment_bridge

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
Residual CLT and residual variance formula from Chen-Han reuse-frequency
moments plus the explicit residual martingale-array CLT/variance input.
-/
theorem residual_clt_and_variance_formula_of_chen_han_reference_martingale_bridge
    (geometry : ChenHanGeometryBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (hregular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        residual.exact_weighted_reuse_moment_limits)
    (hresidual_reg : residual.residual_moment_regularity)
    (hmartingale : residual.martingale_difference_array)
    (hlindeberg : residual.conditional_lindeberg)
    (hquad : residual.predictable_quadratic_variation_stabilization) :
    residual.residual_clt ∧ residual.residual_variance_formula := by
  have hreuse : geometry.reuse_frequency_moment_limits :=
    chen_han_reuse_moment_limits_of_bridge geometry hregular hcatchment
  exact residual_clt_and_variance_formula_of_martingale_array_input residual
    (hmoment_transfer hreuse) hresidual_reg hmartingale hlindeberg hquad

/--
Residual CLT and residual variance formula from Chen-Han reuse-frequency
moments plus the named triangular martingale-array CLT bridge.
-/
theorem residual_clt_and_variance_formula_of_chen_han_reference_triangular_martingale_bridge
    (geometry : ChenHanGeometryBridge)
    (residualCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (exactWeightedReuseMomentLimits residualMomentRegularity : Prop)
    (hregular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        exactWeightedReuseMomentLimits)
    (hresidual_reg : residualMomentRegularity)
    (hmartingale : residualCLT.martingale_difference_array)
    (hlindeberg : residualCLT.conditional_lindeberg)
    (hquad : residualCLT.predictable_quadratic_variation_stabilization) :
    residualCLT.residual_clt ∧ residualCLT.residual_variance_formula := by
  have hreuse : geometry.reuse_frequency_moment_limits :=
    chen_han_reuse_moment_limits_of_bridge geometry hregular hcatchment
  exact
    residual_clt_and_variance_formula_of_martingale_array_input
      (residualMartingaleArrayInputOfTriangularMartingaleArrayCLTBridge
        exactWeightedReuseMomentLimits residualMomentRegularity residualCLT)
      (hmoment_transfer hreuse) hresidual_reg hmartingale hlindeberg hquad

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
Estimated-score WDSM asymptotic normality from the Chen-Han reference
interfaces using the explicit local-experiment input instead of the broad
estimated-score bridge.
-/
theorem estimated_score_asymptotic_normality_of_chen_han_reference_local_experiment_bridges
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualArrayCLTBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (estimated : EstimatedScoreLocalExperimentInput)
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
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (hfunctional : estimated.matching_functional_local_derivative)
    (hequicontinuity : estimated.local_stochastic_equicontinuity)
    (hgodambe : estimated.godambe_variance_identity) :
    estimated.estimated_score_asymptotic_normality := by
  have hknown : known.asymptotic_normality :=
    known_score_asymptotic_normality_of_chen_han_reference_bridges
      geometry radius residual bias known hgeometry_regular hcatchment
      hmoment_transfer hresidual_reg hquad hresidual_transfer
      hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
      hbias_transfer hdecomp hden hheterogeneity
  exact estimated_score_asymptotic_normality_of_local_experiment_input
    estimated (hknown_transfer hknown) hfirst hscore hfunctional
    hequicontinuity hgodambe

/--
Known-score WDSM asymptotic normality from Chen-Han reference inputs when the
residual input is supplied as a residual CLT/variance bridge but only normality
is needed.
-/
theorem known_score_asymptotic_normality_of_chen_han_reference_residual_variance_bridges
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualArrayCLTVarianceBridge)
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
    known.asymptotic_normality :=
  known_score_asymptotic_normality_of_chen_han_reference_bridges
    geometry radius (residualArrayCLTBridgeOfCLTVarianceBridge residual)
    bias known hgeometry_regular hcatchment hmoment_transfer hresidual_reg
    hquad hresidual_transfer hradius_regular hradius_geometry
    hradius_transfer hfinite hlipschitz hbias_transfer hdecomp hden
    hheterogeneity

/--
Estimated-score WDSM asymptotic normality from Chen-Han reference inputs and a
residual CLT/variance bridge, returning only normality.
-/
theorem estimated_score_asymptotic_normality_of_chen_han_reference_residual_variance_bridges
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualArrayCLTVarianceBridge)
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
    known_score_asymptotic_normality_of_chen_han_reference_residual_variance_bridges
      geometry radius residual bias known hgeometry_regular hcatchment
      hmoment_transfer hresidual_reg hquad hresidual_transfer
      hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
      hbias_transfer hdecomp hden hheterogeneity
  exact estimated_score_asymptotic_normality_of_bridge estimated
    (hknown_transfer hknown) hfirst hlocal hgodambe

/--
Estimated-score WDSM asymptotic normality from Chen-Han reference inputs, a
residual CLT/variance bridge, and the explicit local-experiment input.
-/
theorem estimated_score_asymptotic_normality_of_chen_han_reference_residual_variance_local_experiment_bridges
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (estimated : EstimatedScoreLocalExperimentInput)
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
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (hfunctional : estimated.matching_functional_local_derivative)
    (hequicontinuity : estimated.local_stochastic_equicontinuity)
    (hgodambe : estimated.godambe_variance_identity) :
    estimated.estimated_score_asymptotic_normality := by
  have hknown : known.asymptotic_normality :=
    known_score_asymptotic_normality_of_chen_han_reference_residual_variance_bridges
      geometry radius residual bias known hgeometry_regular hcatchment
      hmoment_transfer hresidual_reg hquad hresidual_transfer
      hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
      hbias_transfer hdecomp hden hheterogeneity
  exact estimated_score_asymptotic_normality_of_local_experiment_input
    estimated (hknown_transfer hknown) hfirst hscore hfunctional
    hequicontinuity hgodambe

/--
Known-score WDSM asymptotic normality from the Chen-Han reference interfaces
when the residual term is supplied through the explicit martingale-array CLT
input.
-/
theorem known_score_asymptotic_normality_of_chen_han_reference_martingale_bridges
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
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
    (hheterogeneity : known.heterogeneity_clt) :
    known.asymptotic_normality := by
  have hreuse : geometry.reuse_frequency_moment_limits :=
    chen_han_reuse_moment_limits_of_bridge geometry
      hgeometry_regular hcatchment
  have hresidual : residual.residual_clt :=
    residual_clt_of_martingale_array_input residual
      (hmoment_transfer hreuse) hresidual_reg hmartingale hlindeberg hquad
  have hbias : bias.matching_discrepancy_negligible :=
    matching_discrepancy_negligible_of_chen_han_radius_bridge radius bias
      hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
  exact known_score_asymptotic_normality_of_bridge known
    hdecomp hden hheterogeneity
    (hresidual_transfer hresidual)
    (hbias_transfer hbias)

/--
Estimated-score WDSM asymptotic normality from Chen-Han reference inputs and
the explicit residual martingale-array CLT route.
-/
theorem estimated_score_asymptotic_normality_of_chen_han_reference_martingale_bridges
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (estimated : EstimatedScoreAsymptoticBridge)
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
    (hgodambe : estimated.godambe_variance_identity) :
    estimated.estimated_score_asymptotic_normality := by
  have hknown : known.asymptotic_normality :=
    known_score_asymptotic_normality_of_chen_han_reference_martingale_bridges
      geometry radius residual bias known hgeometry_regular hcatchment
      hmoment_transfer hresidual_reg hmartingale hlindeberg hquad
      hresidual_transfer hradius_regular hradius_geometry hradius_transfer
      hfinite hlipschitz hbias_transfer hdecomp hden hheterogeneity
  exact estimated_score_asymptotic_normality_of_bridge estimated
    (hknown_transfer hknown) hfirst hlocal hgodambe

/--
Estimated-score WDSM asymptotic normality from Chen-Han reference inputs and
the explicit residual martingale-array CLT route, using the explicit
local-experiment input instead of the broad estimated-score bridge.
-/
theorem estimated_score_asymptotic_normality_of_chen_han_reference_martingale_local_experiment_bridges
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (estimated : EstimatedScoreLocalExperimentInput)
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
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (hfunctional : estimated.matching_functional_local_derivative)
    (hequicontinuity : estimated.local_stochastic_equicontinuity)
    (hgodambe : estimated.godambe_variance_identity) :
    estimated.estimated_score_asymptotic_normality := by
  have hknown : known.asymptotic_normality :=
    known_score_asymptotic_normality_of_chen_han_reference_martingale_bridges
      geometry radius residual bias known hgeometry_regular hcatchment
      hmoment_transfer hresidual_reg hmartingale hlindeberg hquad
      hresidual_transfer hradius_regular hradius_geometry hradius_transfer
      hfinite hlipschitz hbias_transfer hdecomp hden hheterogeneity
  exact estimated_score_asymptotic_normality_of_local_experiment_input
    estimated (hknown_transfer hknown) hfirst hscore hfunctional
    hequicontinuity hgodambe

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
Chen-Han reference bridge delivering both the WDSM known-score asymptotic
normality conclusion and the Chen-Han limiting variance formula, using the
explicit residual martingale-array CLT route for normality.
-/
theorem known_score_asymptotic_normality_and_limiting_variance_of_chen_han_reference_martingale_bridges
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
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
    (hheterogeneity : known.heterogeneity_clt) :
    known.asymptotic_normality ∧ geometry.limiting_variance_formula := by
  have hknown : known.asymptotic_normality :=
    known_score_asymptotic_normality_of_chen_han_reference_martingale_bridges
      geometry radius residual bias known hgeometry_regular hcatchment
      hmoment_transfer hresidual_reg hmartingale hlindeberg hquad
      hresidual_transfer hradius_regular hradius_geometry hradius_transfer
      hfinite hlipschitz hbias_transfer hdecomp hden hheterogeneity
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
Known-score WDSM asymptotic normality and known-score variance formula from
Chen-Han reuse/radius inputs when the residual term is supplied through the
explicit martingale-array CLT/variance interface.
-/
theorem known_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_bridges
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
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
    (hmartingale : residual.martingale_difference_array)
    (hlindeberg : residual.conditional_lindeberg)
    (hquad : residual.predictable_quadratic_variation_stabilization)
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
  have hradius : bias.weighted_average_radius_rate :=
    hradius_transfer
      (chen_han_weighted_average_radius_rate_of_bridge radius
        hradius_regular hradius_geometry)
  exact
    known_score_asymptotic_normality_and_variance_formula_of_geometry_martingale_array
      (weightedGeometryMomentBridgeOfChenHan geometry) heterogeneity
      residual bias known variance hgeometry_regular hcatchment
      hmoment_transfer hheterogeneity_moment hheterogeneity_variance
      hheterogeneity_transfer hheterogeneity_variance_transfer
      hresidual_reg hmartingale hlindeberg hquad hresidual_transfer
      hresidual_variance_transfer hfinite hlipschitz hradius hbias_transfer
      hdecomp hden horthogonality

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
Estimated-score WDSM asymptotic normality and estimated-score variance formula
from the Chen-Han component reference inputs using one combined
local-experiment/Godambe variance input.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_local_experiment_bridges
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
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
    (hadjustment : estimated.score_adjustment_algebra)
    (hgodambe : estimated.godambe_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula := by
  have hknown :=
    known_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_bridges
      geometry radius heterogeneity residual bias known knownVariance
      hgeometry_regular hcatchment hmoment_transfer hheterogeneity_moment
      hheterogeneity_variance hheterogeneity_transfer
      hheterogeneity_variance_transfer hresidual_reg hquad hresidual_transfer
      hresidual_variance_transfer hradius_regular hradius_geometry
      hradius_transfer hfinite hlipschitz hbias_transfer hdecomp hden
      horthogonality
  exact
    estimated_score_asymptotic_normality_and_variance_formula_of_local_experiment_variance_input
      estimated (hknown_normality_transfer hknown.1)
      (hknown_variance_transfer hknown.2) hfirst hscore hfunctional
      hequicontinuity hadjustment hgodambe

/--
Estimated-score WDSM asymptotic normality and estimated-score variance formula
from the Chen-Han reference inputs when the residual component is routed
through explicit martingale-array CLT/variance assumptions.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_bridges
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
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
    (hadjustment : estimatedVariance.score_adjustment_algebra)
    (hgodambe_variance : estimatedVariance.godambe_variance_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimatedVariance.estimated_score_variance_formula := by
  have hradius : bias.weighted_average_radius_rate :=
    hradius_transfer
      (chen_han_weighted_average_radius_rate_of_bridge radius
        hradius_regular hradius_geometry)
  exact
    estimated_score_asymptotic_normality_and_variance_formula_of_geometry_martingale_array
      (weightedGeometryMomentBridgeOfChenHan geometry) heterogeneity
      residual bias known knownVariance estimated estimatedVariance
      hgeometry_regular hcatchment hmoment_transfer hheterogeneity_moment
      hheterogeneity_variance hheterogeneity_transfer
      hheterogeneity_variance_transfer hresidual_reg hmartingale hlindeberg
      hquad hresidual_transfer hresidual_variance_transfer hfinite
      hlipschitz hradius hbias_transfer hdecomp hden horthogonality
      hknown_normality_transfer hknown_variance_transfer hfirst hlocal
      hgodambe_normality hadjustment hgodambe_variance

/--
Estimated-score WDSM asymptotic normality and estimated-score variance formula
from Chen-Han reference inputs, explicit residual martingale-array assumptions,
and a combined local-experiment variance input with one shared Godambe premise.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_bridges
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
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
    (hadjustment : estimated.score_adjustment_algebra)
    (hgodambe : estimated.godambe_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula := by
  have hradius : bias.weighted_average_radius_rate :=
    hradius_transfer
      (chen_han_weighted_average_radius_rate_of_bridge radius
        hradius_regular hradius_geometry)
  exact
    estimated_score_asymptotic_normality_and_variance_formula_of_geometry_martingale_array_local_experiment
      (weightedGeometryMomentBridgeOfChenHan geometry) heterogeneity
      residual bias known knownVariance estimated hgeometry_regular
      hcatchment hmoment_transfer hheterogeneity_moment
      hheterogeneity_variance hheterogeneity_transfer
      hheterogeneity_variance_transfer hresidual_reg hmartingale hlindeberg
      hquad hresidual_transfer hresidual_variance_transfer hfinite
      hlipschitz hradius hbias_transfer hdecomp hden horthogonality
      hknown_normality_transfer hknown_variance_transfer hfirst hscore
      hfunctional hequicontinuity hadjustment hgodambe

/--
Known-score WDSM asymptotic normality and known-score variance formula from
Chen-Han reuse/radius inputs when the residual term is supplied through the
named triangular martingale-array CLT bridge.
-/
theorem known_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_triangular_martingale_bridges
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residualCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (variance : KnownScoreVarianceFormulaBridge)
    (exactWeightedReuseMomentLimits residualMomentRegularity : Prop)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        exactWeightedReuseMomentLimits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        variance.heterogeneity_variance_formula)
    (hresidual_reg : residualMomentRegularity)
    (hmartingale : residualCLT.martingale_difference_array)
    (hlindeberg : residualCLT.conditional_lindeberg)
    (hquad : residualCLT.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residualCLT.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residualCLT.residual_variance_formula ->
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
    known.asymptotic_normality ∧ variance.known_score_variance_formula :=
  known_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_bridges
    geometry radius heterogeneity
    (residualMartingaleArrayInputOfTriangularMartingaleArrayCLTBridge
      exactWeightedReuseMomentLimits residualMomentRegularity residualCLT)
    bias known variance hgeometry_regular hcatchment hmoment_transfer
    hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hlindeberg
    hquad hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden horthogonality

/--
Estimated-score WDSM asymptotic normality and estimated-score variance formula
from Chen-Han reference inputs when the residual component is routed through
the named triangular martingale-array CLT bridge.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_triangular_martingale_bridges
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residualCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (estimated : EstimatedScoreAsymptoticBridge)
    (estimatedVariance : EstimatedScoreVarianceFormulaBridge)
    (exactWeightedReuseMomentLimits residualMomentRegularity : Prop)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        exactWeightedReuseMomentLimits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        knownVariance.heterogeneity_variance_formula)
    (hresidual_reg : residualMomentRegularity)
    (hmartingale : residualCLT.martingale_difference_array)
    (hlindeberg : residualCLT.conditional_lindeberg)
    (hquad : residualCLT.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residualCLT.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residualCLT.residual_variance_formula ->
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
      estimatedVariance.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_bridges
    geometry radius heterogeneity
    (residualMartingaleArrayInputOfTriangularMartingaleArrayCLTBridge
      exactWeightedReuseMomentLimits residualMomentRegularity residualCLT)
    bias known knownVariance estimated estimatedVariance hgeometry_regular
    hcatchment hmoment_transfer hheterogeneity_moment
    hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hlindeberg
    hquad hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden horthogonality hknown_normality_transfer
    hknown_variance_transfer hfirst hlocal hgodambe_normality hadjustment
    hgodambe_variance

/--
Estimated-score WDSM asymptotic normality and estimated-score variance formula
from Chen-Han reference inputs, the named triangular martingale-array CLT
bridge, and a combined local-experiment variance input.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_triangular_martingale_local_experiment_bridges
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residualCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (exactWeightedReuseMomentLimits residualMomentRegularity : Prop)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        exactWeightedReuseMomentLimits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        knownVariance.heterogeneity_variance_formula)
    (hresidual_reg : residualMomentRegularity)
    (hmartingale : residualCLT.martingale_difference_array)
    (hlindeberg : residualCLT.conditional_lindeberg)
    (hquad : residualCLT.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residualCLT.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residualCLT.residual_variance_formula ->
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
    (hadjustment : estimated.score_adjustment_algebra)
    (hgodambe : estimated.godambe_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_bridges
    geometry radius heterogeneity
    (residualMartingaleArrayInputOfTriangularMartingaleArrayCLTBridge
      exactWeightedReuseMomentLimits residualMomentRegularity residualCLT)
    bias known knownVariance estimated hgeometry_regular hcatchment
    hmoment_transfer hheterogeneity_moment hheterogeneity_variance
    hheterogeneity_transfer hheterogeneity_variance_transfer hresidual_reg
    hmartingale hlindeberg hquad hresidual_transfer
    hresidual_variance_transfer hradius_regular hradius_geometry
    hradius_transfer hfinite hlipschitz hbias_transfer hdecomp hden
    horthogonality hknown_normality_transfer hknown_variance_transfer
    hfirst hscore hfunctional hequicontinuity hadjustment hgodambe

/--
Known-score WDSM asymptotic normality and known-score variance formula from
Chen-Han reuse/radius inputs when component orthogonality is supplied by
granular population/design cross-term-zero premises.
-/
theorem known_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_bridges_design_cross_zero
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (variance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge variance)
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
    (hcross : orthogonality.population_design_cross_terms_zero)
    (hlimit : orthogonality.limiting_cross_covariance_zero) :
    known.asymptotic_normality ∧ variance.known_score_variance_formula := by
  have hradius : bias.weighted_average_radius_rate :=
    hradius_transfer
      (chen_han_weighted_average_radius_rate_of_bridge radius
        hradius_regular hradius_geometry)
  exact
    known_score_asymptotic_normality_and_variance_formula_of_geometry_design_cross_zero
      (weightedGeometryMomentBridgeOfChenHan geometry) heterogeneity
      residual bias known variance orthogonality hgeometry_regular
      hcatchment hmoment_transfer hheterogeneity_moment
      hheterogeneity_variance hheterogeneity_transfer
      hheterogeneity_variance_transfer hresidual_reg hquad
      hresidual_transfer hresidual_variance_transfer hfinite hlipschitz
      hradius hbias_transfer hdecomp hden hcross hlimit

/--
Known-score WDSM asymptotic normality and known-score variance formula from
Chen-Han reuse/radius inputs, explicit martingale-array residual assumptions,
and granular population/design cross-term-zero orthogonality premises.
-/
theorem known_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_bridges_design_cross_zero
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (variance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge variance)
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
    (hmartingale : residual.martingale_difference_array)
    (hlindeberg : residual.conditional_lindeberg)
    (hquad : residual.predictable_quadratic_variation_stabilization)
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
    (hcross : orthogonality.population_design_cross_terms_zero)
    (hlimit : orthogonality.limiting_cross_covariance_zero) :
    known.asymptotic_normality ∧ variance.known_score_variance_formula := by
  have hradius : bias.weighted_average_radius_rate :=
    hradius_transfer
      (chen_han_weighted_average_radius_rate_of_bridge radius
        hradius_regular hradius_geometry)
  exact
    known_score_asymptotic_normality_and_variance_formula_of_geometry_martingale_array_design_cross_zero
      (weightedGeometryMomentBridgeOfChenHan geometry) heterogeneity
      residual bias known variance orthogonality hgeometry_regular
      hcatchment hmoment_transfer hheterogeneity_moment
      hheterogeneity_variance hheterogeneity_transfer
      hheterogeneity_variance_transfer hresidual_reg hmartingale hlindeberg
      hquad hresidual_transfer hresidual_variance_transfer hfinite
      hlipschitz hradius hbias_transfer hdecomp hden hcross hlimit

/--
Known-score WDSM asymptotic normality and known-score variance formula from
Chen-Han reuse/radius inputs, the named triangular martingale-array CLT bridge,
and granular population/design cross-term-zero orthogonality premises.
-/
theorem known_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_triangular_martingale_bridges_design_cross_zero
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residualCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (variance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge variance)
    (exactWeightedReuseMomentLimits residualMomentRegularity : Prop)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        exactWeightedReuseMomentLimits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        variance.heterogeneity_variance_formula)
    (hresidual_reg : residualMomentRegularity)
    (hmartingale : residualCLT.martingale_difference_array)
    (hlindeberg : residualCLT.conditional_lindeberg)
    (hquad : residualCLT.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residualCLT.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residualCLT.residual_variance_formula ->
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
    (hcross : orthogonality.population_design_cross_terms_zero)
    (hlimit : orthogonality.limiting_cross_covariance_zero) :
    known.asymptotic_normality ∧ variance.known_score_variance_formula :=
  known_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_bridges_design_cross_zero
    geometry radius heterogeneity
    (residualMartingaleArrayInputOfTriangularMartingaleArrayCLTBridge
      exactWeightedReuseMomentLimits residualMomentRegularity residualCLT)
    bias known variance orthogonality hgeometry_regular hcatchment
    hmoment_transfer hheterogeneity_moment hheterogeneity_variance
    hheterogeneity_transfer hheterogeneity_variance_transfer hresidual_reg
    hmartingale hlindeberg hquad hresidual_transfer
    hresidual_variance_transfer hradius_regular hradius_geometry
    hradius_transfer hfinite hlipschitz hbias_transfer hdecomp hden hcross
    hlimit

/--
Estimated-score WDSM asymptotic normality and estimated-score variance formula
from Chen-Han component reference inputs when component orthogonality is
supplied by granular population/design cross-term-zero premises.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_bridges_design_cross_zero
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
    (hadjustment : estimatedVariance.score_adjustment_algebra)
    (hgodambe_variance : estimatedVariance.godambe_variance_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimatedVariance.estimated_score_variance_formula := by
  have hradius : bias.weighted_average_radius_rate :=
    hradius_transfer
      (chen_han_weighted_average_radius_rate_of_bridge radius
        hradius_regular hradius_geometry)
  exact
    estimated_score_asymptotic_normality_and_variance_formula_of_geometry_design_cross_zero
      (weightedGeometryMomentBridgeOfChenHan geometry) heterogeneity
      residual bias known knownVariance orthogonality estimated
      estimatedVariance hgeometry_regular hcatchment hmoment_transfer
      hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
      hheterogeneity_variance_transfer hresidual_reg hquad
      hresidual_transfer hresidual_variance_transfer hfinite hlipschitz
      hradius hbias_transfer hdecomp hden hcross hlimit
      hknown_normality_transfer hknown_variance_transfer hfirst hlocal
      hgodambe_normality hadjustment hgodambe_variance

/--
Estimated-score WDSM asymptotic normality and estimated-score variance formula
from Chen-Han component reference inputs, explicit local-experiment variance
inputs, and granular population/design cross-term-zero premises.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_local_experiment_bridges_design_cross_zero
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
    (hadjustment : estimated.score_adjustment_algebra)
    (hgodambe : estimated.godambe_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula := by
  have hradius : bias.weighted_average_radius_rate :=
    hradius_transfer
      (chen_han_weighted_average_radius_rate_of_bridge radius
        hradius_regular hradius_geometry)
  exact
    estimated_score_asymptotic_normality_and_variance_formula_of_geometry_local_experiment_design_cross_zero
      (weightedGeometryMomentBridgeOfChenHan geometry) heterogeneity
      residual bias known knownVariance orthogonality estimated
      hgeometry_regular hcatchment hmoment_transfer hheterogeneity_moment
      hheterogeneity_variance hheterogeneity_transfer
      hheterogeneity_variance_transfer hresidual_reg hquad
      hresidual_transfer hresidual_variance_transfer hfinite hlipschitz
      hradius hbias_transfer hdecomp hden hcross hlimit
      hknown_normality_transfer hknown_variance_transfer hfirst hscore
      hfunctional hequicontinuity hadjustment hgodambe

/--
Estimated-score WDSM asymptotic normality and estimated-score variance formula
from Chen-Han component reference inputs, explicit martingale-array residual
assumptions, and granular population/design cross-term-zero premises.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_bridges_design_cross_zero
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
    (hadjustment : estimatedVariance.score_adjustment_algebra)
    (hgodambe_variance : estimatedVariance.godambe_variance_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimatedVariance.estimated_score_variance_formula := by
  have hradius : bias.weighted_average_radius_rate :=
    hradius_transfer
      (chen_han_weighted_average_radius_rate_of_bridge radius
        hradius_regular hradius_geometry)
  exact
    estimated_score_asymptotic_normality_and_variance_formula_of_geometry_martingale_array_design_cross_zero
      (weightedGeometryMomentBridgeOfChenHan geometry) heterogeneity
      residual bias known knownVariance orthogonality estimated
      estimatedVariance hgeometry_regular hcatchment hmoment_transfer
      hheterogeneity_moment hheterogeneity_variance hheterogeneity_transfer
      hheterogeneity_variance_transfer hresidual_reg hmartingale hlindeberg
      hquad hresidual_transfer hresidual_variance_transfer hfinite
      hlipschitz hradius hbias_transfer hdecomp hden hcross hlimit
      hknown_normality_transfer hknown_variance_transfer hfirst hlocal
      hgodambe_normality hadjustment hgodambe_variance

/--
Estimated-score WDSM asymptotic normality and estimated-score variance formula
from Chen-Han component reference inputs, explicit martingale-array residual
assumptions, explicit local-experiment variance inputs, and granular
population/design cross-term-zero premises.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_bridges_design_cross_zero
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
    (hadjustment : estimated.score_adjustment_algebra)
    (hgodambe : estimated.godambe_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula := by
  have hradius : bias.weighted_average_radius_rate :=
    hradius_transfer
      (chen_han_weighted_average_radius_rate_of_bridge radius
        hradius_regular hradius_geometry)
  exact
    estimated_score_asymptotic_normality_and_variance_formula_of_geometry_martingale_array_local_experiment_design_cross_zero
      (weightedGeometryMomentBridgeOfChenHan geometry) heterogeneity
      residual bias known knownVariance orthogonality estimated
      hgeometry_regular hcatchment hmoment_transfer hheterogeneity_moment
      hheterogeneity_variance hheterogeneity_transfer
      hheterogeneity_variance_transfer hresidual_reg hmartingale hlindeberg
      hquad hresidual_transfer hresidual_variance_transfer hfinite
      hlipschitz hradius hbias_transfer hdecomp hden hcross hlimit
      hknown_normality_transfer hknown_variance_transfer hfirst hscore
      hfunctional hequicontinuity hadjustment hgodambe

/--
Estimated-score WDSM asymptotic normality and estimated-score variance formula
from Chen-Han component reference inputs, the named triangular martingale-array
CLT bridge, and granular population/design cross-term-zero premises.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_triangular_martingale_bridges_design_cross_zero
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residualCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge knownVariance)
    (estimated : EstimatedScoreAsymptoticBridge)
    (estimatedVariance : EstimatedScoreVarianceFormulaBridge)
    (exactWeightedReuseMomentLimits residualMomentRegularity : Prop)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        exactWeightedReuseMomentLimits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        knownVariance.heterogeneity_variance_formula)
    (hresidual_reg : residualMomentRegularity)
    (hmartingale : residualCLT.martingale_difference_array)
    (hlindeberg : residualCLT.conditional_lindeberg)
    (hquad : residualCLT.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residualCLT.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residualCLT.residual_variance_formula ->
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
    (hadjustment : estimatedVariance.score_adjustment_algebra)
    (hgodambe_variance : estimatedVariance.godambe_variance_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimatedVariance.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_bridges_design_cross_zero
    geometry radius heterogeneity
    (residualMartingaleArrayInputOfTriangularMartingaleArrayCLTBridge
      exactWeightedReuseMomentLimits residualMomentRegularity residualCLT)
    bias known knownVariance orthogonality estimated estimatedVariance
    hgeometry_regular hcatchment hmoment_transfer hheterogeneity_moment
    hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hlindeberg
    hquad hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden hcross hlimit hknown_normality_transfer
    hknown_variance_transfer hfirst hlocal hgodambe_normality hadjustment
    hgodambe_variance

/--
Estimated-score WDSM asymptotic normality and estimated-score variance formula
from Chen-Han component reference inputs, the named triangular martingale-array
CLT bridge, explicit local-experiment variance inputs, and granular
population/design cross-term-zero premises.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_triangular_martingale_local_experiment_bridges_design_cross_zero
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (heterogeneity : HeterogeneityCLTVarianceBridge)
    (residualCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (knownVariance : KnownScoreVarianceFormulaBridge)
    (orthogonality :
      KnownScoreComponentOrthogonalityBridge knownVariance)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (exactWeightedReuseMomentLimits residualMomentRegularity : Prop)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        exactWeightedReuseMomentLimits)
    (hheterogeneity_moment : heterogeneity.effect_moment_regularity)
    (hheterogeneity_variance :
      heterogeneity.centered_effect_variance_stabilization)
    (hheterogeneity_transfer :
      heterogeneity.heterogeneity_clt -> known.heterogeneity_clt)
    (hheterogeneity_variance_transfer :
      heterogeneity.heterogeneity_variance_formula ->
        knownVariance.heterogeneity_variance_formula)
    (hresidual_reg : residualMomentRegularity)
    (hmartingale : residualCLT.martingale_difference_array)
    (hlindeberg : residualCLT.conditional_lindeberg)
    (hquad : residualCLT.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residualCLT.residual_clt -> known.residual_clt)
    (hresidual_variance_transfer :
      residualCLT.residual_variance_formula ->
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
    (hadjustment : estimated.score_adjustment_algebra)
    (hgodambe : estimated.godambe_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_component_reference_martingale_local_experiment_bridges_design_cross_zero
    geometry radius heterogeneity
    (residualMartingaleArrayInputOfTriangularMartingaleArrayCLTBridge
      exactWeightedReuseMomentLimits residualMomentRegularity residualCLT)
    bias known knownVariance orthogonality estimated hgeometry_regular
    hcatchment hmoment_transfer hheterogeneity_moment
    hheterogeneity_variance hheterogeneity_transfer
    hheterogeneity_variance_transfer hresidual_reg hmartingale hlindeberg
    hquad hresidual_transfer hresidual_variance_transfer hradius_regular
    hradius_geometry hradius_transfer hfinite hlipschitz hbias_transfer
    hdecomp hden hcross hlimit hknown_normality_transfer
    hknown_variance_transfer hfirst hscore hfunctional hequicontinuity
    hadjustment hgodambe

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

/--
Estimated-score WDSM asymptotic normality together with its estimated-score
variance formula from the direct Chen-Han limiting-variance route using one
combined local-experiment/Godambe variance input.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_local_experiment_bridges
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualArrayCLTBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
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
    (hadjustment : estimated.score_adjustment_algebra)
    (hgodambe : estimated.godambe_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula := by
  have hknown :
      known.asymptotic_normality ∧ geometry.limiting_variance_formula :=
    known_score_asymptotic_normality_and_limiting_variance_of_chen_han_reference_bridges
      geometry radius residual bias known hgeometry_regular hcatchment
      hmoment_transfer hresidual_reg hquad hresidual_transfer
      hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
      hbias_transfer hdecomp hden hheterogeneity
  exact
    estimated_score_asymptotic_normality_and_variance_formula_of_local_experiment_variance_input
      estimated (hknown_normality_transfer hknown.1)
      (hknown_variance_transfer hknown.2) hfirst hscore hfunctional
      hequicontinuity hadjustment hgodambe

/--
Estimated-score WDSM asymptotic normality together with its estimated-score
variance formula from the Chen-Han reference inputs and Godambe layer, using
the explicit residual martingale-array CLT route for normality.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_bridges
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
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
    (hadjustment : variance.score_adjustment_algebra)
    (hgodambe_variance : variance.godambe_variance_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      variance.estimated_score_variance_formula := by
  have hnormal :
      estimated.estimated_score_asymptotic_normality :=
    estimated_score_asymptotic_normality_of_chen_han_reference_martingale_bridges
      geometry radius residual bias known estimated hgeometry_regular
      hcatchment hmoment_transfer hresidual_reg hmartingale hlindeberg hquad
      hresidual_transfer hradius_regular hradius_geometry hradius_transfer
      hfinite hlipschitz hbias_transfer hdecomp hden hheterogeneity
      hknown_transfer hfirst hlocal hgodambe_normality
  have hvariance :
      variance.estimated_score_variance_formula :=
    estimated_score_variance_formula_of_chen_han_reference_bridge
      geometry variance hgeometry_regular hcatchment hknown_variance_transfer
      hadjustment hgodambe_variance
  exact ⟨hnormal, hvariance⟩

/--
Estimated-score WDSM asymptotic normality together with its estimated-score
variance formula from Chen-Han reference inputs, the explicit residual
martingale-array CLT route, and one combined local-experiment/Godambe input.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_local_experiment_bridges
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residual : ResidualMartingaleArrayCLTVarianceInput)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
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
    (hadjustment : estimated.score_adjustment_algebra)
    (hgodambe : estimated.godambe_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula := by
  have hknown :
      known.asymptotic_normality ∧ geometry.limiting_variance_formula :=
    known_score_asymptotic_normality_and_limiting_variance_of_chen_han_reference_martingale_bridges
      geometry radius residual bias known hgeometry_regular hcatchment
      hmoment_transfer hresidual_reg hmartingale hlindeberg hquad
      hresidual_transfer hradius_regular hradius_geometry hradius_transfer
      hfinite hlipschitz hbias_transfer hdecomp hden hheterogeneity
  exact
    estimated_score_asymptotic_normality_and_variance_formula_of_local_experiment_variance_input
      estimated (hknown_normality_transfer hknown.1)
      (hknown_variance_transfer hknown.2) hfirst hscore hfunctional
      hequicontinuity hadjustment hgodambe

/--
Estimated-score WDSM asymptotic normality together with its estimated-score
variance formula from the direct Chen-Han limiting-variance route, using the
named triangular martingale-array CLT bridge for normality.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_triangular_martingale_bridges
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residualCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (estimated : EstimatedScoreAsymptoticBridge)
    (variance : EstimatedScoreVarianceFormulaBridge)
    (exactWeightedReuseMomentLimits residualMomentRegularity : Prop)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        exactWeightedReuseMomentLimits)
    (hresidual_reg : residualMomentRegularity)
    (hmartingale : residualCLT.martingale_difference_array)
    (hlindeberg : residualCLT.conditional_lindeberg)
    (hquad : residualCLT.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residualCLT.residual_clt -> known.residual_clt)
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
      variance.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_bridges
    geometry radius
    (residualMartingaleArrayInputOfTriangularMartingaleArrayCLTBridge
      exactWeightedReuseMomentLimits residualMomentRegularity residualCLT)
    bias known estimated variance hgeometry_regular hcatchment
    hmoment_transfer hresidual_reg hmartingale hlindeberg hquad
    hresidual_transfer hradius_regular hradius_geometry hradius_transfer
    hfinite hlipschitz hbias_transfer hdecomp hden hheterogeneity
    hknown_transfer hfirst hlocal hgodambe_normality
    hknown_variance_transfer hadjustment hgodambe_variance

/--
Estimated-score WDSM asymptotic normality together with its estimated-score
variance formula from the direct Chen-Han limiting-variance route, using the
named triangular martingale-array CLT bridge and one combined
local-experiment/Godambe input.
-/
theorem estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_triangular_martingale_local_experiment_bridges
    (geometry : ChenHanGeometryBridge)
    (radius : ChenHanRadiusRateBridge)
    (residualCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (bias : AverageRadiusBiasBridge)
    (known : KnownScoreAsymptoticBridge)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (exactWeightedReuseMomentLimits residualMomentRegularity : Prop)
    (hgeometry_regular : geometry.score_density_regular)
    (hcatchment : geometry.nearest_neighbor_catchment_moments)
    (hmoment_transfer :
      geometry.reuse_frequency_moment_limits ->
        exactWeightedReuseMomentLimits)
    (hresidual_reg : residualMomentRegularity)
    (hmartingale : residualCLT.martingale_difference_array)
    (hlindeberg : residualCLT.conditional_lindeberg)
    (hquad : residualCLT.predictable_quadratic_variation_stabilization)
    (hresidual_transfer : residualCLT.residual_clt -> known.residual_clt)
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
    (hadjustment : estimated.score_adjustment_algebra)
    (hgodambe : estimated.godambe_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_martingale_local_experiment_bridges
    geometry radius
    (residualMartingaleArrayInputOfTriangularMartingaleArrayCLTBridge
      exactWeightedReuseMomentLimits residualMomentRegularity residualCLT)
    bias known estimated hgeometry_regular hcatchment hmoment_transfer
    hresidual_reg hmartingale hlindeberg hquad hresidual_transfer
    hradius_regular hradius_geometry hradius_transfer hfinite hlipschitz
    hbias_transfer hdecomp hden hheterogeneity hknown_normality_transfer
    hknown_variance_transfer hfirst hscore hfunctional hequicontinuity
    hadjustment hgodambe

end WDSM
end Matching
end StatInference
