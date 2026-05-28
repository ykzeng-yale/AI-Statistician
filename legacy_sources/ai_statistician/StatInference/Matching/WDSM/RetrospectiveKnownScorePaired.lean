import StatInference.Matching.WDSM.RetrospectivePATEKnownScoreVariance
import StatInference.Matching.WDSM.RetrospectivePATTKnownScoreVariance

/-!
# Paired retrospective known-score audit wrappers

This module packages the retrospective PATE and PATT known-score routes in
paired conjunctions, matching the prospective paired wrappers.
-/

namespace StatInference
namespace Matching
namespace WDSM

/--
Paired retrospective known-score asymptotic normality from audited finite
algebra and explicit stochastic inputs.
-/
theorem retrospective_pate_patt_known_score_asymptotic_normality_of_audited_bridges
    (bpate : RetrospectivePATEKnownScoreAsymptoticBridge)
    (bpatt : RetrospectivePATTKnownScoreAsymptoticBridge)
    (hpate_exact : bpate.exact_decomposition_verified)
    (hpate_bias_bound : bpate.deterministic_discrepancy_bound_verified)
    (hpate_finite : bpate.bias_bridge.eventual_finite_matching_regular)
    (hpate_radius : bpate.bias_bridge.weighted_average_radius_rate)
    (hpate_den : bpate.known_score_bridge.denominator_stabilization)
    (hpate_heterogeneity : bpate.known_score_bridge.heterogeneity_clt)
    (hpate_residual : bpate.known_score_bridge.residual_clt)
    (hpatt_exact : bpatt.exact_decomposition_verified)
    (hpatt_bias_bound : bpatt.deterministic_discrepancy_bound_verified)
    (hpatt_finite : bpatt.bias_bridge.eventual_finite_matching_regular)
    (hpatt_radius : bpatt.bias_bridge.weighted_average_radius_rate)
    (hpatt_den : bpatt.known_score_bridge.denominator_stabilization)
    (hpatt_heterogeneity : bpatt.known_score_bridge.heterogeneity_clt)
    (hpatt_residual : bpatt.known_score_bridge.residual_clt) :
    bpate.asymptotic_normality ∧ bpatt.asymptotic_normality := by
  constructor
  · exact
      retrospective_pate_known_score_asymptotic_normality_of_audited_bridges
        bpate hpate_exact hpate_bias_bound hpate_finite hpate_radius
        hpate_den hpate_heterogeneity hpate_residual
  · exact
      retrospective_patt_known_score_asymptotic_normality_of_audited_bridges
        bpatt hpatt_exact hpatt_bias_bound hpatt_finite hpatt_radius
        hpatt_den hpatt_heterogeneity hpatt_residual

/--
Paired retrospective PATE/PATT known-score asymptotic normality and variance
formula from audited Chen-Han, residual, heterogeneity, and orthogonality
bridges.
-/
theorem retrospective_pate_patt_known_score_normality_and_variance_of_audited_bridges
    (pate : RetrospectivePATEKnownScoreVarianceBridge)
    (patt : RetrospectivePATTKnownScoreVarianceBridge)
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
    retrospective_pate_known_score_normality_and_variance_of_chen_han_audited_bridges
      pate hpate_exact hpate_bias_bound hpate_geometry_regular
      hpate_catchment hpate_heterogeneity_moment
      hpate_heterogeneity_variance hpate_residual_reg hpate_quad
      hpate_radius_regular hpate_radius_geometry hpate_finite hpate_den
      hpate_orthogonality
  have hpatt :
      patt.asymptotic_bridge.asymptotic_normality ∧
        patt.known_score_variance_formula :=
    retrospective_patt_known_score_normality_and_variance_of_audited_bridges
      patt hpatt_exact hpatt_bias_bound hpatt_geometry_regular
      hpatt_catchment hpatt_heterogeneity_moment
      hpatt_heterogeneity_variance hpatt_residual_reg hpatt_quad
      hpatt_radius_regular hpatt_radius_geometry hpatt_finite hpatt_den
      hpatt_orthogonality
  exact ⟨hpate.1, hpate.2, hpatt.1, hpatt.2⟩

end WDSM
end Matching
end StatInference
