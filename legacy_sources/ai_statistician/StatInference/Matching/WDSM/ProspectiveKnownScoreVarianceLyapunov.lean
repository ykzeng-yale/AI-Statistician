import StatInference.Matching.WDSM.ProspectiveKnownScoreVarianceMartingale
import StatInference.Matching.WDSM.ResidualMartingaleLyapunovBridge

/-!
# Prospective known-score variance from Lyapunov residual inputs

This module lets the prospective known-score variance audit consume the
generic Lyapunov residual martingale-array input directly.  It is a thin
composition layer over the checked martingale-array variance bridge.
-/

namespace StatInference
namespace Matching
namespace WDSM

/--
Prospective PATE known-score variance bridge with the residual component
provided by the generic Lyapunov martingale-array input.
-/
structure ProspectivePATEKnownScoreVarianceLyapunovBridge where
  asymptotic_bridge : ProspectivePATEKnownScoreAsymptoticBridge
  geometry_bridge : ChenHanGeometryBridge
  radius_bridge : ChenHanRadiusRateBridge
  heterogeneity_bridge : HeterogeneityCLTVarianceBridge
  residual_input : ResidualLyapunovArrayCLTVarianceInput
  residual_martingale_difference : residual_input.martingale_difference_array
  residual_lyapunov : residual_input.conditional_lyapunov
  variance_bridge : KnownScoreVarianceFormulaBridge
  known_score_variance_formula : Prop
  moment_transfer :
    geometry_bridge.reuse_frequency_moment_limits ->
      residual_input.exact_weighted_reuse_moment_limits
  heterogeneity_clt_to_known :
    heterogeneity_bridge.heterogeneity_clt ->
      asymptotic_bridge.known_score_bridge.heterogeneity_clt
  heterogeneity_variance_to_known :
    heterogeneity_bridge.heterogeneity_variance_formula ->
      variance_bridge.heterogeneity_variance_formula
  residual_clt_to_known :
    residual_input.residual_clt ->
      asymptotic_bridge.known_score_bridge.residual_clt
  residual_variance_to_known :
    residual_input.residual_variance_formula ->
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
checked finite evidence plus a generic Lyapunov residual input.
-/
theorem prospective_pate_known_score_normality_and_variance_of_lyapunov_array_bridge
    (b : ProspectivePATEKnownScoreVarianceLyapunovBridge)
    (hexact : b.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular : b.geometry_bridge.score_density_regular)
    (hcatchment : b.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg : b.residual_input.residual_moment_regularity)
    (hquad :
      b.residual_input.predictable_quadratic_variation_stabilization)
    (hradius_regular : b.radius_bridge.score_density_regular)
    (hradius_geometry : b.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality : b.variance_bridge.component_orthogonality) :
    b.asymptotic_bridge.asymptotic_normality ∧
      b.known_score_variance_formula := by
  let residualInput : ResidualMartingaleArrayCLTVarianceInput :=
    residualMartingaleArrayCLTVarianceInputOfLyapunovArrayInput
      b.residual_input
  let martingaleBridge : ProspectivePATEKnownScoreVarianceMartingaleBridge := {
    asymptotic_bridge := b.asymptotic_bridge
    geometry_bridge := b.geometry_bridge
    radius_bridge := b.radius_bridge
    heterogeneity_bridge := b.heterogeneity_bridge
    residual_input := residualInput
    residual_martingale_difference := b.residual_martingale_difference
    residual_lindeberg := b.residual_lyapunov
    variance_bridge := b.variance_bridge
    known_score_variance_formula := b.known_score_variance_formula
    moment_transfer := b.moment_transfer
    heterogeneity_clt_to_known := b.heterogeneity_clt_to_known
    heterogeneity_variance_to_known := b.heterogeneity_variance_to_known
    residual_clt_to_known := b.residual_clt_to_known
    residual_variance_to_known := b.residual_variance_to_known
    radius_rate_to_bias := b.radius_rate_to_bias
    bias_to_known_score := b.bias_to_known_score
    variance_to_prospective_pate := b.variance_to_prospective_pate
  }
  exact prospective_pate_known_score_normality_and_variance_of_martingale_array_bridge
    martingaleBridge hexact hbias_bound hgeometry_regular hcatchment
    hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
    hradius_regular hradius_geometry hfinite hden horthogonality

/--
Prospective PATT known-score variance bridge with the residual component
provided by the generic Lyapunov martingale-array input.
-/
structure ProspectivePATTKnownScoreVarianceLyapunovBridge where
  asymptotic_bridge : ProspectivePATTKnownScoreAsymptoticBridge
  geometry_bridge : ChenHanGeometryBridge
  radius_bridge : ChenHanRadiusRateBridge
  heterogeneity_bridge : HeterogeneityCLTVarianceBridge
  residual_input : ResidualLyapunovArrayCLTVarianceInput
  residual_martingale_difference : residual_input.martingale_difference_array
  residual_lyapunov : residual_input.conditional_lyapunov
  variance_bridge : KnownScoreVarianceFormulaBridge
  known_score_variance_formula : Prop
  moment_transfer :
    geometry_bridge.reuse_frequency_moment_limits ->
      residual_input.exact_weighted_reuse_moment_limits
  heterogeneity_clt_to_known :
    heterogeneity_bridge.heterogeneity_clt ->
      asymptotic_bridge.known_score_bridge.heterogeneity_clt
  heterogeneity_variance_to_known :
    heterogeneity_bridge.heterogeneity_variance_formula ->
      variance_bridge.heterogeneity_variance_formula
  residual_clt_to_known :
    residual_input.residual_clt ->
      asymptotic_bridge.known_score_bridge.residual_clt
  residual_variance_to_known :
    residual_input.residual_variance_formula ->
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
checked one-sided finite evidence plus a generic Lyapunov residual input.
-/
theorem prospective_patt_known_score_normality_and_variance_of_lyapunov_array_bridge
    (b : ProspectivePATTKnownScoreVarianceLyapunovBridge)
    (hexact : b.asymptotic_bridge.exact_decomposition_verified)
    (hbias_bound :
      b.asymptotic_bridge.deterministic_discrepancy_bound_verified)
    (hgeometry_regular : b.geometry_bridge.score_density_regular)
    (hcatchment : b.geometry_bridge.nearest_neighbor_catchment_moments)
    (hheterogeneity_moment :
      b.heterogeneity_bridge.effect_moment_regularity)
    (hheterogeneity_variance :
      b.heterogeneity_bridge.centered_effect_variance_stabilization)
    (hresidual_reg : b.residual_input.residual_moment_regularity)
    (hquad :
      b.residual_input.predictable_quadratic_variation_stabilization)
    (hradius_regular : b.radius_bridge.score_density_regular)
    (hradius_geometry : b.radius_bridge.nearest_neighbor_radius_geometry)
    (hfinite :
      b.asymptotic_bridge.bias_bridge.eventual_finite_matching_regular)
    (hden :
      b.asymptotic_bridge.known_score_bridge.denominator_stabilization)
    (horthogonality : b.variance_bridge.component_orthogonality) :
    b.asymptotic_bridge.asymptotic_normality ∧
      b.known_score_variance_formula := by
  let residualInput : ResidualMartingaleArrayCLTVarianceInput :=
    residualMartingaleArrayCLTVarianceInputOfLyapunovArrayInput
      b.residual_input
  let martingaleBridge : ProspectivePATTKnownScoreVarianceMartingaleBridge := {
    asymptotic_bridge := b.asymptotic_bridge
    geometry_bridge := b.geometry_bridge
    radius_bridge := b.radius_bridge
    heterogeneity_bridge := b.heterogeneity_bridge
    residual_input := residualInput
    residual_martingale_difference := b.residual_martingale_difference
    residual_lindeberg := b.residual_lyapunov
    variance_bridge := b.variance_bridge
    known_score_variance_formula := b.known_score_variance_formula
    moment_transfer := b.moment_transfer
    heterogeneity_clt_to_known := b.heterogeneity_clt_to_known
    heterogeneity_variance_to_known := b.heterogeneity_variance_to_known
    residual_clt_to_known := b.residual_clt_to_known
    residual_variance_to_known := b.residual_variance_to_known
    radius_rate_to_bias := b.radius_rate_to_bias
    bias_to_known_score := b.bias_to_known_score
    variance_to_prospective_patt := b.variance_to_prospective_patt
  }
  exact prospective_patt_known_score_normality_and_variance_of_martingale_array_bridge
    martingaleBridge hexact hbias_bound hgeometry_regular hcatchment
    hheterogeneity_moment hheterogeneity_variance hresidual_reg hquad
    hradius_regular hradius_geometry hfinite hden horthogonality

/--
Paired prospective PATE/PATT known-score asymptotic normality and variance
formula from audited Lyapunov martingale-array residual inputs.
-/
theorem prospective_pate_patt_known_score_normality_and_variance_of_lyapunov_array_bridge
    (pate : ProspectivePATEKnownScoreVarianceLyapunovBridge)
    (patt : ProspectivePATTKnownScoreVarianceLyapunovBridge)
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
    (hpate_residual_reg : pate.residual_input.residual_moment_regularity)
    (hpate_quad :
      pate.residual_input.predictable_quadratic_variation_stabilization)
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
    (hpatt_residual_reg : patt.residual_input.residual_moment_regularity)
    (hpatt_quad :
      patt.residual_input.predictable_quadratic_variation_stabilization)
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
    prospective_pate_known_score_normality_and_variance_of_lyapunov_array_bridge
      pate hpate_exact hpate_bias_bound hpate_geometry_regular
      hpate_catchment hpate_heterogeneity_moment
      hpate_heterogeneity_variance hpate_residual_reg hpate_quad
      hpate_radius_regular hpate_radius_geometry hpate_finite hpate_den
      hpate_orthogonality
  have hpatt :
      patt.asymptotic_bridge.asymptotic_normality ∧
        patt.known_score_variance_formula :=
    prospective_patt_known_score_normality_and_variance_of_lyapunov_array_bridge
      patt hpatt_exact hpatt_bias_bound hpatt_geometry_regular
      hpatt_catchment hpatt_heterogeneity_moment
      hpatt_heterogeneity_variance hpatt_residual_reg hpatt_quad
      hpatt_radius_regular hpatt_radius_geometry hpatt_finite hpatt_den
      hpatt_orthogonality
  exact ⟨hpate.1, hpate.2, hpatt.1, hpatt.2⟩

end WDSM
end Matching
end StatInference
