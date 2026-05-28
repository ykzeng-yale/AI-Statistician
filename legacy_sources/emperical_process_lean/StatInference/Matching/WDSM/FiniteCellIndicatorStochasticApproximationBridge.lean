import StatInference.Matching.WDSM.FiniteCellIndicatorCLTApproximationBridge
import StatInference.Matching.WDSM.FiniteCellIndicatorLLNInterfaces

/-!
# Finite score-cell stochastic approximation bridges for WDSM

This module packages the finite score-cell stochastic layer needed by WDSM:
finite weighted indicator LLNs for unscaled approximation and finite
score-cell vector CLTs for scaled approximation.  It does not prove those
probability theorems; it composes the named bridges that now expose them.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Cell : Type*} [DecidableEq Cell]

/--
Combined finite score-cell stochastic bridge for PATE approximation:
LLN inputs give unscaled negligibility, and the finite vector CLT input gives
scaled negligibility.
-/
structure PATEFiniteScoreCellStochasticApproximationBridge
    (Cell : Type*) [DecidableEq Cell] where
  lln_bridge : PATEFiniteScoreCellLLNApproximationBridge Cell
  clt_bridge : ScaledPATEFiniteScoreCellCLTApproximationBridge Cell
  finite_conditions_to_scaled :
    lln_bridge.indicator_bridge.eventual_finite_conditions ->
      clt_bridge.indicator_bridge.eventual_finite_conditions
  envelope_to_scaled :
    lln_bridge.indicator_bridge.envelope_convergence ->
      clt_bridge.indicator_bridge.envelope_convergence
  indicator_lln_to_scaled :
    lln_bridge.indicator_bridge.weighted_indicator_sum_lln ->
      clt_bridge.indicator_bridge.weighted_indicator_sum_lln

theorem
    pate_unscaled_and_scaled_approximation_negligible_of_finite_score_cell_stochastic
    (b : PATEFiniteScoreCellStochasticApproximationBridge Cell)
    (hdesign : b.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded : b.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln : b.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite : b.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope : b.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex : b.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      b.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      b.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified) :
    b.lln_bridge.indicator_bridge.pate_double_score_approximation_negligible ∧
      b.clt_bridge.indicator_bridge.scaled_pate_double_score_approximation_negligible := by
  have hcell_lln :
      b.lln_bridge.lln_bridge.cellwise_weighted_indicator_sum_lln :=
    finite_score_cell_indicator_lln_of_bridge
      b.lln_bridge.lln_bridge hdesign hbounded harray_lln
  have hindicator :
      b.lln_bridge.indicator_bridge.weighted_indicator_sum_lln :=
    b.lln_bridge.finite_lln_to_indicator_lln hcell_lln
  constructor
  · exact pate_double_score_approximation_negligible_of_indicator_bridge
      b.lln_bridge.indicator_bridge hfinite henvelope hindicator
  · exact scaled_pate_approximation_negligible_of_finite_score_cell_clt
      b.clt_bridge hsimplex hlinear hmatrix
      (b.finite_conditions_to_scaled hfinite)
      (b.envelope_to_scaled henvelope)
      (b.indicator_lln_to_scaled hindicator)

/--
Combined finite score-cell stochastic bridge for PATT approximation:
LLN inputs give unscaled negligibility, and the finite vector CLT input gives
scaled negligibility.
-/
structure PATTFiniteScoreCellStochasticApproximationBridge
    (Cell : Type*) [DecidableEq Cell] where
  lln_bridge : PATTFiniteScoreCellLLNApproximationBridge Cell
  clt_bridge : ScaledPATTFiniteScoreCellCLTApproximationBridge Cell
  finite_conditions_to_scaled :
    lln_bridge.indicator_bridge.eventual_finite_conditions ->
      clt_bridge.indicator_bridge.eventual_finite_conditions
  envelope_to_scaled :
    lln_bridge.indicator_bridge.envelope_convergence ->
      clt_bridge.indicator_bridge.envelope_convergence
  indicator_lln_to_scaled :
    lln_bridge.indicator_bridge.weighted_indicator_sum_lln ->
      clt_bridge.indicator_bridge.weighted_indicator_sum_lln

theorem
    patt_unscaled_and_scaled_approximation_negligible_of_finite_score_cell_stochastic
    (b : PATTFiniteScoreCellStochasticApproximationBridge Cell)
    (hdesign : b.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded : b.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln : b.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite : b.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope : b.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex : b.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      b.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      b.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified) :
    b.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
      b.clt_bridge.indicator_bridge.scaled_patt_double_score_approximation_negligible := by
  have hcell_lln :
      b.lln_bridge.lln_bridge.cellwise_weighted_indicator_sum_lln :=
    finite_score_cell_indicator_lln_of_bridge
      b.lln_bridge.lln_bridge hdesign hbounded harray_lln
  have hindicator :
      b.lln_bridge.indicator_bridge.weighted_indicator_sum_lln :=
    b.lln_bridge.finite_lln_to_indicator_lln hcell_lln
  constructor
  · exact patt_double_score_approximation_negligible_of_indicator_bridge
      b.lln_bridge.indicator_bridge hfinite henvelope hindicator
  · exact scaled_patt_approximation_negligible_of_finite_score_cell_clt
      b.clt_bridge hsimplex hlinear hmatrix
      (b.finite_conditions_to_scaled hfinite)
      (b.envelope_to_scaled henvelope)
      (b.indicator_lln_to_scaled hindicator)

end WDSM
end Matching
end StatInference
