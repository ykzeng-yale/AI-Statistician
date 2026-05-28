import StatInference.Matching.WDSM.AsymptoticInterfaces
import StatInference.Matching.WDSM.FiniteCellIndicatorPairedKnownScoreAsymptoticBridge
import StatInference.Matching.WDSM.FirstStepZEstimatorBridge

/-!
# Paired finite score-cell approximation to estimated-score WDSM asymptotics

This module composes the paired finite score-cell known-score bridge with the
estimated-score WDSM bridge for PATE and PATT.  The first-step expansion,
matching-functional local expansion, and Godambe variance identity remain
explicit assumptions for each estimand.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {PATECell PATTCell : Type*}
  [DecidableEq PATECell] [DecidableEq PATTCell]

/--
Paired estimated-score asymptotic bridge fed by paired finite score-cell
known-score approximation.
-/
structure PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge
    (PATECell PATTCell : Type*)
    [DecidableEq PATECell] [DecidableEq PATTCell] where
  known_score_finite_cell_bridge :
    PATEPATTFiniteScoreCellKnownScoreAsymptoticBridge PATECell PATTCell
  pate_estimated_score_bridge : EstimatedScoreAsymptoticBridge
  patt_estimated_score_bridge : EstimatedScoreAsymptoticBridge
  pate_known_score_to_estimated_score_input :
    known_score_finite_cell_bridge.pate_known_score_bridge.asymptotic_normality ->
      pate_estimated_score_bridge.known_score_asymptotic_normality
  patt_known_score_to_estimated_score_input :
    known_score_finite_cell_bridge.patt_known_score_bridge.asymptotic_normality ->
      patt_estimated_score_bridge.known_score_asymptotic_normality

/--
The paired finite score-cell estimated-score route yields the PATE/PATT
unscaled and scaled approximation conclusions, the PATE/PATT known-score
asymptotic conclusions, and the PATE/PATT estimated-score asymptotic
conclusions.
-/
theorem
    pate_patt_estimated_score_asymptotic_normality_of_paired_finite_score_cell_stochastic
    (b :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell PATTCell)
    (hpate_design :
      b.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hpate_bounded :
      b.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (hpate_array_lln :
      b.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hpate_finite :
      b.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (hpate_envelope :
      b.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hpate_simplex :
      b.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hpate_linear :
      b.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpate_matrix :
      b.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpatt_design :
      b.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hpatt_bounded :
      b.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (hpatt_array_lln :
      b.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hpatt_finite :
      b.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (hpatt_envelope :
      b.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hpatt_simplex :
      b.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hpatt_linear :
      b.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpatt_matrix :
      b.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpate_decomp :
      b.known_score_finite_cell_bridge.pate_known_score_bridge.aggregate_hajek_decomposition)
    (hpate_denominator :
      b.known_score_finite_cell_bridge.pate_known_score_bridge.denominator_stabilization)
    (hpate_heterogeneity :
      b.known_score_finite_cell_bridge.pate_known_score_bridge.heterogeneity_clt)
    (hpate_residual :
      b.known_score_finite_cell_bridge.pate_known_score_bridge.residual_clt)
    (hpatt_decomp :
      b.known_score_finite_cell_bridge.patt_known_score_bridge.aggregate_hajek_decomposition)
    (hpatt_denominator :
      b.known_score_finite_cell_bridge.patt_known_score_bridge.denominator_stabilization)
    (hpatt_heterogeneity :
      b.known_score_finite_cell_bridge.patt_known_score_bridge.heterogeneity_clt)
    (hpatt_residual :
      b.known_score_finite_cell_bridge.patt_known_score_bridge.residual_clt)
    (hpate_first :
      b.pate_estimated_score_bridge.first_step_asymptotic_linearization)
    (hpate_local :
      b.pate_estimated_score_bridge.matching_functional_local_expansion)
    (hpate_godambe :
      b.pate_estimated_score_bridge.godambe_variance_identity)
    (hpatt_first :
      b.patt_estimated_score_bridge.first_step_asymptotic_linearization)
    (hpatt_local :
      b.patt_estimated_score_bridge.matching_functional_local_expansion)
    (hpatt_godambe :
      b.patt_estimated_score_bridge.godambe_variance_identity) :
    b.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.pate_double_score_approximation_negligible ∧
      b.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.clt_bridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      b.known_score_finite_cell_bridge.pate_known_score_bridge.asymptotic_normality ∧
      b.pate_estimated_score_bridge.estimated_score_asymptotic_normality ∧
      b.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
      b.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.clt_bridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      b.known_score_finite_cell_bridge.patt_known_score_bridge.asymptotic_normality ∧
      b.patt_estimated_score_bridge.estimated_score_asymptotic_normality := by
  have hknown_pair :=
    pate_patt_known_score_asymptotic_normality_of_paired_finite_score_cell_stochastic
      b.known_score_finite_cell_bridge hpate_design hpate_bounded
      hpate_array_lln hpate_finite hpate_envelope hpate_simplex
      hpate_linear hpate_matrix hpatt_design hpatt_bounded hpatt_array_lln
      hpatt_finite hpatt_envelope hpatt_simplex hpatt_linear hpatt_matrix
      hpate_decomp hpate_denominator hpate_heterogeneity hpate_residual
      hpatt_decomp hpatt_denominator hpatt_heterogeneity hpatt_residual
  have hpate_known :
      b.known_score_finite_cell_bridge.pate_known_score_bridge.asymptotic_normality :=
    hknown_pair.2.2.1
  have hpatt_known :
      b.known_score_finite_cell_bridge.patt_known_score_bridge.asymptotic_normality :=
    hknown_pair.2.2.2.2.2
  have hpate_known_input :
      b.pate_estimated_score_bridge.known_score_asymptotic_normality :=
    b.pate_known_score_to_estimated_score_input hpate_known
  have hpatt_known_input :
      b.patt_estimated_score_bridge.known_score_asymptotic_normality :=
    b.patt_known_score_to_estimated_score_input hpatt_known
  have hpate_estimated :
      b.pate_estimated_score_bridge.estimated_score_asymptotic_normality :=
    estimated_score_asymptotic_normality_of_bridge
      b.pate_estimated_score_bridge hpate_known_input hpate_first
      hpate_local hpate_godambe
  have hpatt_estimated :
      b.patt_estimated_score_bridge.estimated_score_asymptotic_normality :=
    estimated_score_asymptotic_normality_of_bridge
      b.patt_estimated_score_bridge hpatt_known_input hpatt_first
      hpatt_local hpatt_godambe
  exact ⟨hknown_pair.1, hknown_pair.2.1, hpate_known, hpate_estimated,
    hknown_pair.2.2.2.1, hknown_pair.2.2.2.2.1, hpatt_known,
    hpatt_estimated⟩

/--
Paired finite score-cell estimated-score bridge built from explicit PATE/PATT
local-experiment inputs.
-/
def patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
    (known :
      PATEPATTFiniteScoreCellKnownScoreAsymptoticBridge PATECell PATTCell)
    (pateEstimated : EstimatedScoreLocalExperimentInput)
    (pattEstimated : EstimatedScoreLocalExperimentInput)
    (hpate_known_to_estimated :
      known.pate_known_score_bridge.asymptotic_normality ->
        pateEstimated.known_score_asymptotic_normality)
    (hpatt_known_to_estimated :
      known.patt_known_score_bridge.asymptotic_normality ->
        pattEstimated.known_score_asymptotic_normality) :
    PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell PATTCell where
  known_score_finite_cell_bridge := known
  pate_estimated_score_bridge :=
    estimatedScoreAsymptoticBridgeOfLocalExperimentInput pateEstimated
  patt_estimated_score_bridge :=
    estimatedScoreAsymptoticBridgeOfLocalExperimentInput pattEstimated
  pate_known_score_to_estimated_score_input := hpate_known_to_estimated
  patt_known_score_to_estimated_score_input := hpatt_known_to_estimated

/--
Paired finite score-cell estimated-score asymptotic normality from explicit
PATE/PATT local-experiment inputs.
-/
theorem
    pate_patt_estimated_score_asymptotic_normality_of_paired_finite_score_cell_stochastic_local_experiment
    (known :
      PATEPATTFiniteScoreCellKnownScoreAsymptoticBridge PATECell PATTCell)
    (pateEstimated : EstimatedScoreLocalExperimentInput)
    (pattEstimated : EstimatedScoreLocalExperimentInput)
    (hpate_known_to_estimated :
      known.pate_known_score_bridge.asymptotic_normality ->
        pateEstimated.known_score_asymptotic_normality)
    (hpatt_known_to_estimated :
      known.patt_known_score_bridge.asymptotic_normality ->
        pattEstimated.known_score_asymptotic_normality)
    (hpate_design :
      known.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hpate_bounded :
      known.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (hpate_array_lln :
      known.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hpate_finite :
      known.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (hpate_envelope :
      known.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hpate_simplex :
      known.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hpate_linear :
      known.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpate_matrix :
      known.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpatt_design :
      known.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hpatt_bounded :
      known.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (hpatt_array_lln :
      known.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hpatt_finite :
      known.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (hpatt_envelope :
      known.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hpatt_simplex :
      known.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hpatt_linear :
      known.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpatt_matrix :
      known.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpate_decomp :
      known.pate_known_score_bridge.aggregate_hajek_decomposition)
    (hpate_denominator :
      known.pate_known_score_bridge.denominator_stabilization)
    (hpate_heterogeneity :
      known.pate_known_score_bridge.heterogeneity_clt)
    (hpate_residual : known.pate_known_score_bridge.residual_clt)
    (hpatt_decomp :
      known.patt_known_score_bridge.aggregate_hajek_decomposition)
    (hpatt_denominator :
      known.patt_known_score_bridge.denominator_stabilization)
    (hpatt_heterogeneity :
      known.patt_known_score_bridge.heterogeneity_clt)
    (hpatt_residual : known.patt_known_score_bridge.residual_clt)
    (hpate_first : pateEstimated.first_step_asymptotic_linearization)
    (hpate_score :
      pateEstimated.score_estimator_local_asymptotic_linearity)
    (hpate_functional :
      pateEstimated.matching_functional_local_derivative)
    (hpate_equicontinuity :
      pateEstimated.local_stochastic_equicontinuity)
    (hpate_godambe : pateEstimated.godambe_variance_identity)
    (hpatt_first : pattEstimated.first_step_asymptotic_linearization)
    (hpatt_score :
      pattEstimated.score_estimator_local_asymptotic_linearity)
    (hpatt_functional :
      pattEstimated.matching_functional_local_derivative)
    (hpatt_equicontinuity :
      pattEstimated.local_stochastic_equicontinuity)
    (hpatt_godambe : pattEstimated.godambe_variance_identity) :
    known.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.pate_double_score_approximation_negligible ∧
      known.stochastic_bridge.pate_bridge.clt_bridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      known.pate_known_score_bridge.asymptotic_normality ∧
      pateEstimated.estimated_score_asymptotic_normality ∧
      known.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
      known.stochastic_bridge.patt_bridge.clt_bridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      known.patt_known_score_bridge.asymptotic_normality ∧
      pattEstimated.estimated_score_asymptotic_normality :=
  pate_patt_estimated_score_asymptotic_normality_of_paired_finite_score_cell_stochastic
    (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
      known pateEstimated pattEstimated hpate_known_to_estimated
      hpatt_known_to_estimated)
    hpate_design hpate_bounded hpate_array_lln hpate_finite
    hpate_envelope hpate_simplex hpate_linear hpate_matrix hpatt_design
    hpatt_bounded hpatt_array_lln hpatt_finite hpatt_envelope hpatt_simplex
    hpatt_linear hpatt_matrix hpate_decomp hpate_denominator
    hpate_heterogeneity hpate_residual hpatt_decomp hpatt_denominator
    hpatt_heterogeneity hpatt_residual hpate_first
    ⟨hpate_score, hpate_functional, hpate_equicontinuity⟩ hpate_godambe
    hpatt_first
    ⟨hpatt_score, hpatt_functional, hpatt_equicontinuity⟩ hpatt_godambe

/--
Paired finite score-cell estimated-score asymptotic normality from explicit
PATE/PATT local-experiment inputs, with the local derivative, stochastic
equicontinuity, and Godambe identity packaged as one compact core per estimand.
-/
theorem
    pate_patt_estimated_score_asymptotic_normality_of_paired_finite_score_cell_stochastic_local_experiment_core
    (known :
      PATEPATTFiniteScoreCellKnownScoreAsymptoticBridge PATECell PATTCell)
    (pateEstimated : EstimatedScoreLocalExperimentInput)
    (pattEstimated : EstimatedScoreLocalExperimentInput)
    (hpate_known_to_estimated :
      known.pate_known_score_bridge.asymptotic_normality ->
        pateEstimated.known_score_asymptotic_normality)
    (hpatt_known_to_estimated :
      known.patt_known_score_bridge.asymptotic_normality ->
        pattEstimated.known_score_asymptotic_normality)
    (hpate_design :
      known.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hpate_bounded :
      known.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (hpate_array_lln :
      known.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hpate_finite :
      known.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (hpate_envelope :
      known.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hpate_simplex :
      known.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hpate_linear :
      known.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpate_matrix :
      known.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpatt_design :
      known.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hpatt_bounded :
      known.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (hpatt_array_lln :
      known.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hpatt_finite :
      known.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (hpatt_envelope :
      known.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hpatt_simplex :
      known.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hpatt_linear :
      known.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpatt_matrix :
      known.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpate_decomp :
      known.pate_known_score_bridge.aggregate_hajek_decomposition)
    (hpate_denominator :
      known.pate_known_score_bridge.denominator_stabilization)
    (hpate_heterogeneity :
      known.pate_known_score_bridge.heterogeneity_clt)
    (hpate_residual : known.pate_known_score_bridge.residual_clt)
    (hpatt_decomp :
      known.patt_known_score_bridge.aggregate_hajek_decomposition)
    (hpatt_denominator :
      known.patt_known_score_bridge.denominator_stabilization)
    (hpatt_heterogeneity :
      known.patt_known_score_bridge.heterogeneity_clt)
    (hpatt_residual : known.patt_known_score_bridge.residual_clt)
    (hpate_first : pateEstimated.first_step_asymptotic_linearization)
    (hpate_score :
      pateEstimated.score_estimator_local_asymptotic_linearity)
    (hpate_core : EstimatedScoreLocalExperimentCore pateEstimated)
    (hpatt_first : pattEstimated.first_step_asymptotic_linearization)
    (hpatt_score :
      pattEstimated.score_estimator_local_asymptotic_linearity)
    (hpatt_core : EstimatedScoreLocalExperimentCore pattEstimated) :
    known.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.pate_double_score_approximation_negligible ∧
      known.stochastic_bridge.pate_bridge.clt_bridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      known.pate_known_score_bridge.asymptotic_normality ∧
      pateEstimated.estimated_score_asymptotic_normality ∧
      known.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
      known.stochastic_bridge.patt_bridge.clt_bridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      known.patt_known_score_bridge.asymptotic_normality ∧
      pattEstimated.estimated_score_asymptotic_normality :=
  pate_patt_estimated_score_asymptotic_normality_of_paired_finite_score_cell_stochastic_local_experiment
    known pateEstimated pattEstimated hpate_known_to_estimated
    hpatt_known_to_estimated hpate_design hpate_bounded hpate_array_lln
    hpate_finite hpate_envelope hpate_simplex hpate_linear hpate_matrix
    hpatt_design hpatt_bounded hpatt_array_lln hpatt_finite
    hpatt_envelope hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
    hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
    hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
    hpate_score hpate_core.matching_functional_local_derivative
    hpate_core.local_stochastic_equicontinuity
    hpate_core.godambe_variance_identity hpatt_first hpatt_score
    hpatt_core.matching_functional_local_derivative
    hpatt_core.local_stochastic_equicontinuity
    hpatt_core.godambe_variance_identity

/--
Paired finite score-cell estimated-score asymptotic normality from explicit
PATE/PATT local experiments whose first-step and score-local inputs are
assembled from paired PATE/PATT first-step evidence.
-/
theorem
    pate_patt_estimated_score_asymptotic_normality_of_paired_finite_score_cell_stochastic_local_experiment_first_step_components
    (known :
      PATEPATTFiniteScoreCellKnownScoreAsymptoticBridge PATECell PATTCell)
    (pateEstimated : EstimatedScoreLocalExperimentInput)
    (pattEstimated : EstimatedScoreLocalExperimentInput)
    (pateFirstStep : PATEDoubleScoreFirstStepAssembly)
    (pattFirstStep : PATTDoubleScoreFirstStepAssembly)
    (hpate_known_to_estimated :
      known.pate_known_score_bridge.asymptotic_normality ->
        pateEstimated.known_score_asymptotic_normality)
    (hpatt_known_to_estimated :
      known.patt_known_score_bridge.asymptotic_normality ->
        pattEstimated.known_score_asymptotic_normality)
    (hpate_first_transfer :
      pateFirstStep.first_step_asymptotic_linearization ->
        pateEstimated.first_step_asymptotic_linearization)
    (hpate_score_transfer :
      pateFirstStep.score_estimator_local_asymptotic_linearity ->
        pateEstimated.score_estimator_local_asymptotic_linearity)
    (hpatt_first_transfer :
      pattFirstStep.first_step_asymptotic_linearization ->
        pattEstimated.first_step_asymptotic_linearization)
    (hpatt_score_transfer :
      pattFirstStep.score_estimator_local_asymptotic_linearity ->
        pattEstimated.score_estimator_local_asymptotic_linearity)
    (hpate_design :
      known.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hpate_bounded :
      known.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (hpate_array_lln :
      known.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hpate_finite :
      known.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (hpate_envelope :
      known.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hpate_simplex :
      known.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hpate_linear :
      known.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpate_matrix :
      known.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpatt_design :
      known.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hpatt_bounded :
      known.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (hpatt_array_lln :
      known.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hpatt_finite :
      known.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (hpatt_envelope :
      known.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hpatt_simplex :
      known.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hpatt_linear :
      known.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpatt_matrix :
      known.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpate_decomp :
      known.pate_known_score_bridge.aggregate_hajek_decomposition)
    (hpate_denominator :
      known.pate_known_score_bridge.denominator_stabilization)
    (hpate_heterogeneity :
      known.pate_known_score_bridge.heterogeneity_clt)
    (hpate_residual : known.pate_known_score_bridge.residual_clt)
    (hpatt_decomp :
      known.patt_known_score_bridge.aggregate_hajek_decomposition)
    (hpatt_denominator :
      known.patt_known_score_bridge.denominator_stabilization)
    (hpatt_heterogeneity :
      known.patt_known_score_bridge.heterogeneity_clt)
    (hpatt_residual : known.patt_known_score_bridge.residual_clt)
    (hpate_prop_weight : pateFirstStep.propensity_weighting_design)
    (hpate_treated_weight :
      pateFirstStep.treated_prognostic_weighting_design)
    (hpate_control_weight :
      pateFirstStep.control_prognostic_weighting_design)
    (hpate_prop :
      pateFirstStep.propensity_component_asymptotic_linearity)
    (hpate_treated :
      pateFirstStep.treated_prognostic_component_asymptotic_linearity)
    (hpate_control :
      pateFirstStep.control_prognostic_component_asymptotic_linearity)
    (hpatt_prop_weight : pattFirstStep.propensity_weighting_design)
    (hpatt_control_weight :
      pattFirstStep.control_prognostic_weighting_design)
    (hpatt_prop :
      pattFirstStep.propensity_component_asymptotic_linearity)
    (hpatt_control :
      pattFirstStep.control_prognostic_component_asymptotic_linearity)
    (hpate_functional :
      pateEstimated.matching_functional_local_derivative)
    (hpate_equicontinuity :
      pateEstimated.local_stochastic_equicontinuity)
    (hpate_godambe : pateEstimated.godambe_variance_identity)
    (hpatt_functional :
      pattEstimated.matching_functional_local_derivative)
    (hpatt_equicontinuity :
      pattEstimated.local_stochastic_equicontinuity)
    (hpatt_godambe : pattEstimated.godambe_variance_identity) :
    known.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.pate_double_score_approximation_negligible ∧
      known.stochastic_bridge.pate_bridge.clt_bridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      known.pate_known_score_bridge.asymptotic_normality ∧
      pateEstimated.estimated_score_asymptotic_normality ∧
      known.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
      known.stochastic_bridge.patt_bridge.clt_bridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      known.patt_known_score_bridge.asymptotic_normality ∧
      pattEstimated.estimated_score_asymptotic_normality := by
  have hfirst_score :
      pateFirstStep.first_step_asymptotic_linearization ∧
        pateFirstStep.score_estimator_local_asymptotic_linearity ∧
        pattFirstStep.first_step_asymptotic_linearization ∧
        pattFirstStep.score_estimator_local_asymptotic_linearity :=
    paired_pate_patt_first_step_and_score_local_linearity_of_components
      pateFirstStep pattFirstStep hpate_prop_weight hpate_treated_weight
      hpate_control_weight hpate_prop hpate_treated hpate_control
      hpatt_prop_weight hpatt_control_weight hpatt_prop hpatt_control
  exact
    pate_patt_estimated_score_asymptotic_normality_of_paired_finite_score_cell_stochastic_local_experiment
      known pateEstimated pattEstimated hpate_known_to_estimated
      hpatt_known_to_estimated hpate_design hpate_bounded hpate_array_lln
      hpate_finite hpate_envelope hpate_simplex hpate_linear hpate_matrix
      hpatt_design hpatt_bounded hpatt_array_lln hpatt_finite
      hpatt_envelope hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual
      (hpate_first_transfer hfirst_score.1)
      (hpate_score_transfer hfirst_score.2.1) hpate_functional
      hpate_equicontinuity hpate_godambe
      (hpatt_first_transfer hfirst_score.2.2.1)
      (hpatt_score_transfer hfirst_score.2.2.2) hpatt_functional
      hpatt_equicontinuity hpatt_godambe

end WDSM
end Matching
end StatInference
