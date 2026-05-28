import StatInference.Matching.WDSM.AsymptoticInterfaces
import StatInference.Matching.WDSM.FiniteCellIndicatorPairedStochasticApproximationBridge

/-!
# Paired finite score-cell approximation to known-score WDSM asymptotics

This module packages the PATE and PATT known-score finite-cell routes together.
The stochastic finite-cell layer still exposes the LLN and vector-CLT inputs as
named assumptions; this file proves only the composition into the paired
known-score asymptotic-normality conclusions.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {PATECell PATTCell : Type*}
  [DecidableEq PATECell] [DecidableEq PATTCell]

/--
Paired known-score asymptotic bridge fed by paired finite score-cell stochastic
approximation.

The scaled approximation conclusions are converted into the matching
discrepancy inputs required by the final known-score asymptotic bridges.
-/
structure PATEPATTFiniteScoreCellKnownScoreAsymptoticBridge
    (PATECell PATTCell : Type*)
    [DecidableEq PATECell] [DecidableEq PATTCell] where
  stochastic_bridge :
    PATEPATTFiniteScoreCellStochasticApproximationBridge PATECell PATTCell
  pate_known_score_bridge : KnownScoreAsymptoticBridge
  patt_known_score_bridge : KnownScoreAsymptoticBridge
  pate_scaled_approximation_to_matching_discrepancy :
    stochastic_bridge.pate_bridge.clt_bridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
      pate_known_score_bridge.matching_discrepancy_negligible
  patt_scaled_approximation_to_matching_discrepancy :
    stochastic_bridge.patt_bridge.clt_bridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
      patt_known_score_bridge.matching_discrepancy_negligible

/--
The paired finite score-cell known-score route yields both unscaled
approximation conclusions, both scaled approximation conclusions, and both
known-score asymptotic-normality conclusions.
-/
theorem
    pate_patt_known_score_asymptotic_normality_of_paired_finite_score_cell_stochastic
    (b :
      PATEPATTFiniteScoreCellKnownScoreAsymptoticBridge PATECell PATTCell)
    (hpate_design :
      b.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hpate_bounded :
      b.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (hpate_array_lln :
      b.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hpate_finite :
      b.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (hpate_envelope :
      b.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hpate_simplex :
      b.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hpate_linear :
      b.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpate_matrix :
      b.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpatt_design :
      b.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hpatt_bounded :
      b.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (hpatt_array_lln :
      b.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hpatt_finite :
      b.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (hpatt_envelope :
      b.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hpatt_simplex :
      b.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hpatt_linear :
      b.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpatt_matrix :
      b.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpate_decomp : b.pate_known_score_bridge.aggregate_hajek_decomposition)
    (hpate_denominator : b.pate_known_score_bridge.denominator_stabilization)
    (hpate_heterogeneity : b.pate_known_score_bridge.heterogeneity_clt)
    (hpate_residual : b.pate_known_score_bridge.residual_clt)
    (hpatt_decomp : b.patt_known_score_bridge.aggregate_hajek_decomposition)
    (hpatt_denominator : b.patt_known_score_bridge.denominator_stabilization)
    (hpatt_heterogeneity : b.patt_known_score_bridge.heterogeneity_clt)
    (hpatt_residual : b.patt_known_score_bridge.residual_clt) :
    b.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.pate_double_score_approximation_negligible ∧
      b.stochastic_bridge.pate_bridge.clt_bridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      b.pate_known_score_bridge.asymptotic_normality ∧
      b.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
      b.stochastic_bridge.patt_bridge.clt_bridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      b.patt_known_score_bridge.asymptotic_normality := by
  have happrox :=
    pate_patt_unscaled_and_scaled_approximation_negligible_of_finite_score_cell_stochastic
      b.stochastic_bridge hpate_design hpate_bounded hpate_array_lln
      hpate_finite hpate_envelope hpate_simplex hpate_linear hpate_matrix
      hpatt_design hpatt_bounded hpatt_array_lln hpatt_finite hpatt_envelope
      hpatt_simplex hpatt_linear hpatt_matrix
  have hpate_matching :
      b.pate_known_score_bridge.matching_discrepancy_negligible :=
    b.pate_scaled_approximation_to_matching_discrepancy happrox.2.1
  have hpatt_matching :
      b.patt_known_score_bridge.matching_discrepancy_negligible :=
    b.patt_scaled_approximation_to_matching_discrepancy happrox.2.2.2
  have hpate_asymptotic : b.pate_known_score_bridge.asymptotic_normality :=
    known_score_asymptotic_normality_of_bridge
      b.pate_known_score_bridge hpate_decomp hpate_denominator
      hpate_heterogeneity hpate_residual hpate_matching
  have hpatt_asymptotic : b.patt_known_score_bridge.asymptotic_normality :=
    known_score_asymptotic_normality_of_bridge
      b.patt_known_score_bridge hpatt_decomp hpatt_denominator
      hpatt_heterogeneity hpatt_residual hpatt_matching
  exact ⟨happrox.1, happrox.2.1, hpate_asymptotic,
    happrox.2.2.1, happrox.2.2.2, hpatt_asymptotic⟩

end WDSM
end Matching
end StatInference
