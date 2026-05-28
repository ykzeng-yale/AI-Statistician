import StatInference.Matching.WDSM.AsymptoticInterfaces
import StatInference.Matching.WDSM.FiniteCellIndicatorStochasticApproximationBridge

/-!
# Finite score-cell approximation to known-score WDSM asymptotics

This module composes the finite score-cell stochastic approximation layer with
the existing known-score asymptotic-normality bridge.  The remaining
probability inputs stay explicit: denominator stabilization, heterogeneity CLT,
residual CLT, and the conversion from scaled approximation negligibility to the
matching-discrepancy term used in the final asymptotic bridge.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Cell : Type*} [DecidableEq Cell]

/-- PATE known-score asymptotic bridge fed by finite score-cell stochastic approximation. -/
structure PATEFiniteScoreCellKnownScoreAsymptoticBridge
    (Cell : Type*) [DecidableEq Cell] where
  stochastic_bridge : PATEFiniteScoreCellStochasticApproximationBridge Cell
  known_score_bridge : KnownScoreAsymptoticBridge
  scaled_approximation_to_matching_discrepancy :
    stochastic_bridge.clt_bridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
      known_score_bridge.matching_discrepancy_negligible

theorem
    pate_known_score_asymptotic_normality_of_finite_score_cell_stochastic
    (b : PATEFiniteScoreCellKnownScoreAsymptoticBridge Cell)
    (hdesign :
      b.stochastic_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded :
      b.stochastic_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln :
      b.stochastic_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite :
      b.stochastic_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope :
      b.stochastic_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex :
      b.stochastic_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      b.stochastic_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      b.stochastic_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp : b.known_score_bridge.aggregate_hajek_decomposition)
    (hdenominator : b.known_score_bridge.denominator_stabilization)
    (hheterogeneity : b.known_score_bridge.heterogeneity_clt)
    (hresidual : b.known_score_bridge.residual_clt) :
    b.stochastic_bridge.lln_bridge.indicator_bridge.pate_double_score_approximation_negligible ∧
      b.known_score_bridge.asymptotic_normality := by
  have happrox :=
    pate_unscaled_and_scaled_approximation_negligible_of_finite_score_cell_stochastic
      b.stochastic_bridge hdesign hbounded harray_lln hfinite henvelope
      hsimplex hlinear hmatrix
  have hmatching :
      b.known_score_bridge.matching_discrepancy_negligible :=
    b.scaled_approximation_to_matching_discrepancy happrox.2
  exact ⟨happrox.1,
    known_score_asymptotic_normality_of_bridge b.known_score_bridge
      hdecomp hdenominator hheterogeneity hresidual hmatching⟩

/-- PATT known-score asymptotic bridge fed by finite score-cell stochastic approximation. -/
structure PATTFiniteScoreCellKnownScoreAsymptoticBridge
    (Cell : Type*) [DecidableEq Cell] where
  stochastic_bridge : PATTFiniteScoreCellStochasticApproximationBridge Cell
  known_score_bridge : KnownScoreAsymptoticBridge
  scaled_approximation_to_matching_discrepancy :
    stochastic_bridge.clt_bridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
      known_score_bridge.matching_discrepancy_negligible

theorem
    patt_known_score_asymptotic_normality_of_finite_score_cell_stochastic
    (b : PATTFiniteScoreCellKnownScoreAsymptoticBridge Cell)
    (hdesign :
      b.stochastic_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded :
      b.stochastic_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln :
      b.stochastic_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite :
      b.stochastic_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope :
      b.stochastic_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex :
      b.stochastic_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      b.stochastic_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      b.stochastic_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp : b.known_score_bridge.aggregate_hajek_decomposition)
    (hdenominator : b.known_score_bridge.denominator_stabilization)
    (hheterogeneity : b.known_score_bridge.heterogeneity_clt)
    (hresidual : b.known_score_bridge.residual_clt) :
    b.stochastic_bridge.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
      b.known_score_bridge.asymptotic_normality := by
  have happrox :=
    patt_unscaled_and_scaled_approximation_negligible_of_finite_score_cell_stochastic
      b.stochastic_bridge hdesign hbounded harray_lln hfinite henvelope
      hsimplex hlinear hmatrix
  have hmatching :
      b.known_score_bridge.matching_discrepancy_negligible :=
    b.scaled_approximation_to_matching_discrepancy happrox.2
  exact ⟨happrox.1,
    known_score_asymptotic_normality_of_bridge b.known_score_bridge
      hdecomp hdenominator hheterogeneity hresidual hmatching⟩

end WDSM
end Matching
end StatInference
