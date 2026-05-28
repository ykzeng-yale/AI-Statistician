import StatInference.Matching.WDSM.RetrospectivePATTKnownScoreAsymptotic
import StatInference.Matching.WDSM.ReferenceTheorems

/-!
# Retrospective PATT known-score variance interface

This module packages the audited route from retrospective PATT finite algebra
to the known-score variance formula.  It deliberately keeps the one-sided
reuse/radius inputs, heterogeneity variance, asymmetric residual quadratic
variation, and component orthogonality as explicit assumptions.
-/

namespace StatInference
namespace Matching
namespace WDSM

/--
Scenario-specific bridge for retrospective PATT known-score asymptotic
normality together with the known-score variance formula.
-/
structure RetrospectivePATTKnownScoreVarianceBridge where
  asymptotic_bridge : RetrospectivePATTKnownScoreAsymptoticBridge
  geometry_bridge : ChenHanGeometryBridge
  radius_bridge : ChenHanRadiusRateBridge
  heterogeneity_bridge : HeterogeneityCLTVarianceBridge
  residual_bridge : ResidualArrayCLTVarianceBridge
  variance_bridge : KnownScoreVarianceFormulaBridge
  known_score_variance_formula : Prop
  moment_transfer :
    geometry_bridge.reuse_frequency_moment_limits ->
      residual_bridge.exact_weighted_reuse_moment_limits
  heterogeneity_clt_to_known :
    heterogeneity_bridge.heterogeneity_clt ->
      asymptotic_bridge.known_score_bridge.heterogeneity_clt
  heterogeneity_variance_to_known :
    heterogeneity_bridge.heterogeneity_variance_formula ->
      variance_bridge.heterogeneity_variance_formula
  residual_clt_to_known :
    residual_bridge.residual_clt ->
      asymptotic_bridge.known_score_bridge.residual_clt
  residual_variance_to_known :
    residual_bridge.residual_variance_formula ->
      variance_bridge.residual_variance_formula
  radius_rate_to_bias :
    radius_bridge.weighted_average_radius_rate ->
      asymptotic_bridge.bias_bridge.weighted_average_radius_rate
  bias_to_known_score :
    asymptotic_bridge.bias_bridge.matching_discrepancy_negligible ->
      asymptotic_bridge.known_score_bridge.matching_discrepancy_negligible
  variance_to_retrospective_patt :
    variance_bridge.known_score_variance_formula ->
      known_score_variance_formula

/--
Retrospective PATT known-score asymptotic normality and variance formula from
checked finite evidence plus explicit geometry, heterogeneity, residual, and
orthogonality inputs.
-/
theorem retrospective_patt_known_score_normality_and_variance_of_audited_bridges
    (b : RetrospectivePATTKnownScoreVarianceBridge)
    (hexact : b.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular : b.geometry_bridge.score_density_regular)
    (hcatchment : b.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg : b.residual_bridge.residual_moment_regularity)
    (hquad : b.residual_bridge.quadratic_variation_stabilization)
    (hradius_regular : b.radius_bridge.score_density_regular)
    (hradius_geometry : b.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality : b.variance_bridge.component_orthogonality) :
    b.asymptotic_bridge.asymptotic_normality ∧
      b.known_score_variance_formula := by
  have hpair :=
    known_score_asymptotic_normality_and_variance_formula_of_chen_han_reference_bridges
      b.geometry_bridge
      b.radius_bridge
      b.heterogeneity_bridge
      b.residual_bridge
      b.asymptotic_bridge.bias_bridge
      b.asymptotic_bridge.known_score_bridge
      b.variance_bridge
      hgeometry_regular
      hcatchment
      b.moment_transfer
      hheterogeneity_moment
      hheterogeneity_variance
      b.heterogeneity_clt_to_known
      b.heterogeneity_variance_to_known
      hresidual_reg
      hquad
      b.residual_clt_to_known
      b.residual_variance_to_known
      hradius_regular
      hradius_geometry
      b.radius_rate_to_bias
      hfinite
      (b.asymptotic_bridge.deterministic_bound_to_bias_regular hbias_bound)
      b.bias_to_known_score
      (b.asymptotic_bridge.exact_decomposition_to_aggregate hexact)
      hden
      horthogonality
  exact
    ⟨b.asymptotic_bridge.known_score_to_retrospective_patt hpair.1,
      b.variance_to_retrospective_patt hpair.2⟩

end WDSM
end Matching
end StatInference
