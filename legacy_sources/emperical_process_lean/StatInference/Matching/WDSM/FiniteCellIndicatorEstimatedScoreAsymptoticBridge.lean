import StatInference.Matching.WDSM.FiniteCellIndicatorKnownScoreAsymptoticBridge

/-!
# Finite score-cell approximation to estimated-score WDSM asymptotics

This module composes the finite score-cell known-score asymptotic bridge with
the estimated-score WDSM asymptotic bridge.  The non-smooth first-step
expansion, matching-functional local expansion, and Godambe variance identity
remain explicit inputs.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Cell : Type*} [DecidableEq Cell]

/-- PATE estimated-score asymptotic bridge fed by finite score-cell approximation. -/
structure PATEFiniteScoreCellEstimatedScoreAsymptoticBridge
    (Cell : Type*) [DecidableEq Cell] where
  known_score_finite_cell_bridge :
    PATEFiniteScoreCellKnownScoreAsymptoticBridge Cell
  estimated_score_bridge : EstimatedScoreAsymptoticBridge
  known_score_to_estimated_score_input :
    known_score_finite_cell_bridge.known_score_bridge.asymptotic_normality ->
      estimated_score_bridge.known_score_asymptotic_normality

theorem
    pate_estimated_score_asymptotic_normality_of_finite_score_cell_stochastic
    (b : PATEFiniteScoreCellEstimatedScoreAsymptoticBridge Cell)
    (hdesign :
      b.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded :
      b.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln :
      b.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite :
      b.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope :
      b.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex :
      b.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      b.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      b.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp :
      b.known_score_finite_cell_bridge.known_score_bridge.aggregate_hajek_decomposition)
    (hdenominator :
      b.known_score_finite_cell_bridge.known_score_bridge.denominator_stabilization)
    (hheterogeneity :
      b.known_score_finite_cell_bridge.known_score_bridge.heterogeneity_clt)
    (hresidual :
      b.known_score_finite_cell_bridge.known_score_bridge.residual_clt)
    (hfirst :
      b.estimated_score_bridge.first_step_asymptotic_linearization)
    (hlocal :
      b.estimated_score_bridge.matching_functional_local_expansion)
    (hgodambe :
      b.estimated_score_bridge.godambe_variance_identity) :
    b.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.pate_double_score_approximation_negligible ∧
      b.estimated_score_bridge.estimated_score_asymptotic_normality := by
  have hknown_pair :=
    pate_known_score_asymptotic_normality_of_finite_score_cell_stochastic
      b.known_score_finite_cell_bridge hdesign hbounded harray_lln hfinite
      henvelope hsimplex hlinear hmatrix hdecomp hdenominator hheterogeneity
      hresidual
  have hknown_input :
      b.estimated_score_bridge.known_score_asymptotic_normality :=
    b.known_score_to_estimated_score_input hknown_pair.2
  exact ⟨hknown_pair.1,
    estimated_score_asymptotic_normality_of_bridge b.estimated_score_bridge
      hknown_input hfirst hlocal hgodambe⟩

/-- PATT estimated-score asymptotic bridge fed by finite score-cell approximation. -/
structure PATTFiniteScoreCellEstimatedScoreAsymptoticBridge
    (Cell : Type*) [DecidableEq Cell] where
  known_score_finite_cell_bridge :
    PATTFiniteScoreCellKnownScoreAsymptoticBridge Cell
  estimated_score_bridge : EstimatedScoreAsymptoticBridge
  known_score_to_estimated_score_input :
    known_score_finite_cell_bridge.known_score_bridge.asymptotic_normality ->
      estimated_score_bridge.known_score_asymptotic_normality

theorem
    patt_estimated_score_asymptotic_normality_of_finite_score_cell_stochastic
    (b : PATTFiniteScoreCellEstimatedScoreAsymptoticBridge Cell)
    (hdesign :
      b.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded :
      b.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln :
      b.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite :
      b.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope :
      b.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex :
      b.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      b.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      b.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp :
      b.known_score_finite_cell_bridge.known_score_bridge.aggregate_hajek_decomposition)
    (hdenominator :
      b.known_score_finite_cell_bridge.known_score_bridge.denominator_stabilization)
    (hheterogeneity :
      b.known_score_finite_cell_bridge.known_score_bridge.heterogeneity_clt)
    (hresidual :
      b.known_score_finite_cell_bridge.known_score_bridge.residual_clt)
    (hfirst :
      b.estimated_score_bridge.first_step_asymptotic_linearization)
    (hlocal :
      b.estimated_score_bridge.matching_functional_local_expansion)
    (hgodambe :
      b.estimated_score_bridge.godambe_variance_identity) :
    b.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
      b.estimated_score_bridge.estimated_score_asymptotic_normality := by
  have hknown_pair :=
    patt_known_score_asymptotic_normality_of_finite_score_cell_stochastic
      b.known_score_finite_cell_bridge hdesign hbounded harray_lln hfinite
      henvelope hsimplex hlinear hmatrix hdecomp hdenominator hheterogeneity
      hresidual
  have hknown_input :
      b.estimated_score_bridge.known_score_asymptotic_normality :=
    b.known_score_to_estimated_score_input hknown_pair.2
  exact ⟨hknown_pair.1,
    estimated_score_asymptotic_normality_of_bridge b.estimated_score_bridge
      hknown_input hfirst hlocal hgodambe⟩

end WDSM
end Matching
end StatInference
