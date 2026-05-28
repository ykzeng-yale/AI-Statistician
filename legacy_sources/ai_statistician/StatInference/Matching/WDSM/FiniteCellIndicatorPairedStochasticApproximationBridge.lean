import StatInference.Matching.WDSM.FiniteCellIndicatorStochasticApproximationBridge

/-!
# Paired PATE/PATT finite score-cell stochastic approximation bridge

The WDSM asymptotic discussion tracks PATE and PATT variants in parallel.  The
preceding module proves the finite score-cell stochastic approximation bridge
for each estimand separately.  This module packages the paired composition so a
single theorem can expose the two unscaled and two scaled approximation
conclusions together.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {PATECell PATTCell : Type*}
  [DecidableEq PATECell] [DecidableEq PATTCell]

/--
Paired finite score-cell stochastic approximation bridge for PATE and PATT.

The two cell types are allowed to differ: PATE uses the full joint
propensity/treated-prognostic/control-prognostic cell, while PATT uses the
one-sided propensity/control-prognostic cell.
-/
structure PATEPATTFiniteScoreCellStochasticApproximationBridge
    (PATECell PATTCell : Type*)
    [DecidableEq PATECell] [DecidableEq PATTCell] where
  pate_bridge : PATEFiniteScoreCellStochasticApproximationBridge PATECell
  patt_bridge : PATTFiniteScoreCellStochasticApproximationBridge PATTCell

/--
The paired bridge returns the four approximation conclusions needed by the
finite-cell route: unscaled PATE, scaled PATE, unscaled PATT, and scaled PATT.
-/
theorem
    pate_patt_unscaled_and_scaled_approximation_negligible_of_finite_score_cell_stochastic
    (b :
      PATEPATTFiniteScoreCellStochasticApproximationBridge PATECell PATTCell)
    (hpate_design :
      b.pate_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hpate_bounded :
      b.pate_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (hpate_array_lln :
      b.pate_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hpate_finite :
      b.pate_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (hpate_envelope :
      b.pate_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hpate_simplex :
      b.pate_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hpate_linear :
      b.pate_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpate_matrix :
      b.pate_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpatt_design :
      b.patt_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hpatt_bounded :
      b.patt_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (hpatt_array_lln :
      b.patt_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hpatt_finite :
      b.patt_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (hpatt_envelope :
      b.patt_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hpatt_simplex :
      b.patt_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hpatt_linear :
      b.patt_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpatt_matrix :
      b.patt_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified) :
    b.pate_bridge.lln_bridge.indicator_bridge.pate_double_score_approximation_negligible ∧
      b.pate_bridge.clt_bridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      b.patt_bridge.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
      b.patt_bridge.clt_bridge.indicator_bridge.scaled_patt_double_score_approximation_negligible := by
  have hpate :=
    pate_unscaled_and_scaled_approximation_negligible_of_finite_score_cell_stochastic
      b.pate_bridge hpate_design hpate_bounded hpate_array_lln
      hpate_finite hpate_envelope hpate_simplex hpate_linear hpate_matrix
  have hpatt :=
    patt_unscaled_and_scaled_approximation_negligible_of_finite_score_cell_stochastic
      b.patt_bridge hpatt_design hpatt_bounded hpatt_array_lln
      hpatt_finite hpatt_envelope hpatt_simplex hpatt_linear hpatt_matrix
  exact ⟨hpate.1, hpate.2, hpatt.1, hpatt.2⟩

/--
Paired finite score-cell stochastic approximation from finite LLNs and already
packaged finite score-cell vector CLTs for PATE and PATT.
-/
theorem
    pate_patt_unscaled_and_scaled_approximation_negligible_of_finite_score_cell_stochastic_vector_clt
    (b :
      PATEPATTFiniteScoreCellStochasticApproximationBridge PATECell PATTCell)
    (hpate_design :
      b.pate_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hpate_bounded :
      b.pate_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (hpate_array_lln :
      b.pate_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hpate_finite :
      b.pate_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (hpate_envelope :
      b.pate_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hpate_vector :
      b.pate_bridge.clt_bridge.vector_clt_bridge.finite_dimensional_score_cell_vector_clt)
    (hpatt_design :
      b.patt_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hpatt_bounded :
      b.patt_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (hpatt_array_lln :
      b.patt_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hpatt_finite :
      b.patt_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (hpatt_envelope :
      b.patt_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hpatt_vector :
      b.patt_bridge.clt_bridge.vector_clt_bridge.finite_dimensional_score_cell_vector_clt) :
    b.pate_bridge.lln_bridge.indicator_bridge.pate_double_score_approximation_negligible ∧
      b.pate_bridge.clt_bridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      b.patt_bridge.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
      b.patt_bridge.clt_bridge.indicator_bridge.scaled_patt_double_score_approximation_negligible := by
  have hpate :=
    pate_unscaled_and_scaled_approximation_negligible_of_finite_score_cell_stochastic_vector_clt
      b.pate_bridge hpate_design hpate_bounded hpate_array_lln
      hpate_finite hpate_envelope hpate_vector
  have hpatt :=
    patt_unscaled_and_scaled_approximation_negligible_of_finite_score_cell_stochastic_vector_clt
      b.patt_bridge hpatt_design hpatt_bounded hpatt_array_lln
      hpatt_finite hpatt_envelope hpatt_vector
  exact ⟨hpate.1, hpate.2, hpatt.1, hpatt.2⟩

end WDSM
end Matching
end StatInference
