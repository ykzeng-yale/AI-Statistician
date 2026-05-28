import StatInference.Matching.WDSM.ProspectiveKnownScoreAsymptotic
import StatInference.Matching.WDSM.ReferenceTheorems

/-!
# Prospective known-score variance audit interfaces

This module packages the prospective/common-weight route from checked finite
algebra to known-score asymptotic normality together with the known-score
variance formula.  The Chen-Han geometry, radius-rate, residual quadratic
variation, heterogeneity variance, and component-orthogonality inputs remain
explicit named assumptions.
-/

namespace StatInference
namespace Matching
namespace WDSM

/--
Scenario-specific bridge for prospective PATE known-score asymptotic normality
and the known-score variance formula.
-/
structure ProspectivePATEKnownScoreVarianceBridge where
  asymptotic_bridge : ProspectivePATEKnownScoreAsymptoticBridge
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
  variance_to_prospective_pate :
    variance_bridge.known_score_variance_formula ->
      known_score_variance_formula

/--
Prospective PATE known-score asymptotic normality and variance formula from
checked finite evidence plus explicit Chen-Han, heterogeneity, residual, and
orthogonality inputs.
-/
theorem prospective_pate_known_score_normality_and_variance_of_audited_bridges
    (b : ProspectivePATEKnownScoreVarianceBridge)
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
    ⟨b.asymptotic_bridge.known_score_to_prospective_pate hpair.1,
      b.variance_to_prospective_pate hpair.2⟩

/--
Scenario-specific bridge for prospective PATT known-score asymptotic normality
and the known-score variance formula.
-/
structure ProspectivePATTKnownScoreVarianceBridge where
  asymptotic_bridge : ProspectivePATTKnownScoreAsymptoticBridge
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
  variance_to_prospective_patt :
    variance_bridge.known_score_variance_formula ->
      known_score_variance_formula

/--
Prospective PATT known-score asymptotic normality and variance formula from
checked one-sided finite evidence plus explicit geometry, heterogeneity,
residual, and orthogonality inputs.
-/
theorem prospective_patt_known_score_normality_and_variance_of_audited_bridges
    (b : ProspectivePATTKnownScoreVarianceBridge)
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
    ⟨b.asymptotic_bridge.known_score_to_prospective_patt hpair.1,
      b.variance_to_prospective_patt hpair.2⟩

/--
Paired prospective PATE/PATT known-score asymptotic normality and variance
formula from audited Chen-Han, residual, heterogeneity, and orthogonality
bridges.
-/
theorem prospective_pate_patt_known_score_normality_and_variance_of_audited_bridges
    (pate : ProspectivePATEKnownScoreVarianceBridge)
    (patt : ProspectivePATTKnownScoreVarianceBridge)
    (hpate_exact :
      pate.asymptotic_bridge.exact_decomposition_verified)
    (hpate_bias_bound :
      pate.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hpate_geometry_regular : pate.geometry_bridge.score_density_regular)
    (hpate_catchment : pate.geometry_bridge.nearest_neighbor_catchment_moments)
    (hpate_heterogeneity_moment :
      pate.heterogeneity_bridge.effect_moment_regularity)
    (hpate_heterogeneity_variance :
      pate.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hpate_residual_reg : pate.residual_bridge.residual_moment_regularity)
    (hpate_quad : pate.residual_bridge.quadratic_variation_stabilization)
    (hpate_radius_regular : pate.radius_bridge.score_density_regular)
    (hpate_radius_geometry :
      pate.radius_bridge.nearest_neighbor_radius_geometry)
    (hpate_finite :
      pate.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hpate_den :
      pate.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (hpate_orthogonality : pate.variance_bridge.component_orthogonality)
    (hpatt_exact :
      patt.asymptotic_bridge.exact_decomposition_verified)
    (hpatt_bias_bound :
      patt.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hpatt_geometry_regular : patt.geometry_bridge.score_density_regular)
    (hpatt_catchment : patt.geometry_bridge.nearest_neighbor_catchment_moments)
    (hpatt_heterogeneity_moment :
      patt.heterogeneity_bridge.effect_moment_regularity)
    (hpatt_heterogeneity_variance :
      patt.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hpatt_residual_reg : patt.residual_bridge.residual_moment_regularity)
    (hpatt_quad : patt.residual_bridge.quadratic_variation_stabilization)
    (hpatt_radius_regular : patt.radius_bridge.score_density_regular)
    (hpatt_radius_geometry :
      patt.radius_bridge.nearest_neighbor_radius_geometry)
    (hpatt_finite :
      patt.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hpatt_den :
      patt.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (hpatt_orthogonality : patt.variance_bridge.component_orthogonality) :
    pate.asymptotic_bridge.asymptotic_normality ∧
      pate.known_score_variance_formula ∧
      patt.asymptotic_bridge.asymptotic_normality ∧
      patt.known_score_variance_formula := by
  have hpate :
      pate.asymptotic_bridge.asymptotic_normality ∧
        pate.known_score_variance_formula :=
    prospective_pate_known_score_normality_and_variance_of_audited_bridges
      pate hpate_exact hpate_bias_bound hpate_geometry_regular
      hpate_catchment hpate_heterogeneity_moment
      hpate_heterogeneity_variance hpate_residual_reg hpate_quad
      hpate_radius_regular hpate_radius_geometry hpate_finite hpate_den
      hpate_orthogonality
  have hpatt :
      patt.asymptotic_bridge.asymptotic_normality ∧
        patt.known_score_variance_formula :=
    prospective_patt_known_score_normality_and_variance_of_audited_bridges
      patt hpatt_exact hpatt_bias_bound hpatt_geometry_regular
      hpatt_catchment hpatt_heterogeneity_moment
      hpatt_heterogeneity_variance hpatt_residual_reg hpatt_quad
      hpatt_radius_regular hpatt_radius_geometry hpatt_finite hpatt_den
      hpatt_orthogonality
  exact ⟨hpate.1, hpate.2, hpatt.1, hpatt.2⟩

end WDSM
end Matching
end StatInference
