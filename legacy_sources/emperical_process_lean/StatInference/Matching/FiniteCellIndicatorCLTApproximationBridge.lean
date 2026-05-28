import StatInference.Matching.WDSM.FiniteCellIndicatorCLTInterfaces
import StatInference.Matching.WDSM.IndicatorSumConvergenceInterfaces

/-!
# From finite score-cell indicator CLTs to WDSM approximation bridges

The deterministic approximation layer already reduces scaled PATE/PATT
approximation negligibility to weighted indicator LLNs plus a scaled
indicator-sum difference CLT.  This module connects that remaining scaled CLT
input to the finite score-cell vector CLT interface.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Cell : Type*} [DecidableEq Cell]

/--
Composition bridge from a finite score-cell vector CLT to the scaled PATE
indicator-sum approximation bridge.
-/
structure ScaledPATEFiniteScoreCellCLTApproximationBridge
    (Cell : Type*) [DecidableEq Cell] where
  vector_clt_bridge : FiniteScoreCellVectorCLTBridge Cell
  indicator_bridge : ScaledPATEDoubleScoreIndicatorSumConvergenceBridge
  vector_clt_to_scaled_indicator_difference :
    vector_clt_bridge.finite_dimensional_score_cell_vector_clt ->
      indicator_bridge.scaled_weighted_indicator_sum_difference_clt

theorem scaled_pate_approximation_negligible_of_finite_score_cell_clt
    (b : ScaledPATEFiniteScoreCellCLTApproximationBridge Cell)
    (hsimplex : b.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      b.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix : b.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hfinite : b.indicator_bridge.eventual_finite_conditions)
    (henvelope : b.indicator_bridge.envelope_convergence)
    (hlln : b.indicator_bridge.weighted_indicator_sum_lln) :
    b.indicator_bridge.scaled_pate_double_score_approximation_negligible := by
  have hvector :
      b.vector_clt_bridge.finite_dimensional_score_cell_vector_clt :=
    finite_score_cell_vector_clt_of_bridge
      b.vector_clt_bridge hsimplex hlinear hmatrix
  have hscaled :
      b.indicator_bridge.scaled_weighted_indicator_sum_difference_clt :=
    b.vector_clt_to_scaled_indicator_difference hvector
  exact scaled_pate_double_score_approximation_negligible_of_indicator_bridge
    b.indicator_bridge hfinite henvelope hlln hscaled

/--
Composition bridge from a finite score-cell vector CLT to the scaled PATT
indicator-sum approximation bridge.
-/
structure ScaledPATTFiniteScoreCellCLTApproximationBridge
    (Cell : Type*) [DecidableEq Cell] where
  vector_clt_bridge : FiniteScoreCellVectorCLTBridge Cell
  indicator_bridge : ScaledPATTDoubleScoreIndicatorSumConvergenceBridge
  vector_clt_to_scaled_indicator_difference :
    vector_clt_bridge.finite_dimensional_score_cell_vector_clt ->
      indicator_bridge.scaled_weighted_indicator_sum_difference_clt

theorem scaled_patt_approximation_negligible_of_finite_score_cell_clt
    (b : ScaledPATTFiniteScoreCellCLTApproximationBridge Cell)
    (hsimplex : b.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      b.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix : b.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hfinite : b.indicator_bridge.eventual_finite_conditions)
    (henvelope : b.indicator_bridge.envelope_convergence)
    (hlln : b.indicator_bridge.weighted_indicator_sum_lln) :
    b.indicator_bridge.scaled_patt_double_score_approximation_negligible := by
  have hvector :
      b.vector_clt_bridge.finite_dimensional_score_cell_vector_clt :=
    finite_score_cell_vector_clt_of_bridge
      b.vector_clt_bridge hsimplex hlinear hmatrix
  have hscaled :
      b.indicator_bridge.scaled_weighted_indicator_sum_difference_clt :=
    b.vector_clt_to_scaled_indicator_difference hvector
  exact scaled_patt_double_score_approximation_negligible_of_indicator_bridge
    b.indicator_bridge hfinite henvelope hlln hscaled

end WDSM
end Matching
end StatInference
