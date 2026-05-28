import StatInference.Matching.WDSM.FiniteCellIndicatorKnownScoreAsymptoticBridge
import StatInference.Matching.WDSM.FirstStepZEstimatorBridge

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

/--
PATE finite score-cell estimated-score bridge built from the explicit
local-experiment input.
-/
def pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
    (known :
      PATEFiniteScoreCellKnownScoreAsymptoticBridge Cell)
    (estimated : EstimatedScoreLocalExperimentInput)
    (hknown_to_estimated :
      known.known_score_bridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality) :
    PATEFiniteScoreCellEstimatedScoreAsymptoticBridge Cell where
  known_score_finite_cell_bridge := known
  estimated_score_bridge :=
    estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated
  known_score_to_estimated_score_input := hknown_to_estimated

/--
PATE finite score-cell estimated-score asymptotic normality from the explicit
local-experiment input.
-/
theorem
    pate_estimated_score_asymptotic_normality_of_finite_score_cell_stochastic_local_experiment
    (known :
      PATEFiniteScoreCellKnownScoreAsymptoticBridge Cell)
    (estimated : EstimatedScoreLocalExperimentInput)
    (hknown_to_estimated :
      known.known_score_bridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hdesign :
      known.stochastic_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded :
      known.stochastic_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln :
      known.stochastic_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite :
      known.stochastic_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope :
      known.stochastic_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp : known.known_score_bridge.aggregate_hajek_decomposition)
    (hdenominator : known.known_score_bridge.denominator_stabilization)
    (hheterogeneity : known.known_score_bridge.heterogeneity_clt)
    (hresidual : known.known_score_bridge.residual_clt)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (hfunctional : estimated.matching_functional_local_derivative)
    (hequicontinuity : estimated.local_stochastic_equicontinuity)
    (hgodambe : estimated.godambe_variance_identity) :
    known.stochastic_bridge.lln_bridge.indicator_bridge.pate_double_score_approximation_negligible ∧
      estimated.estimated_score_asymptotic_normality :=
  pate_estimated_score_asymptotic_normality_of_finite_score_cell_stochastic
    (pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
      known estimated hknown_to_estimated)
    hdesign hbounded harray_lln hfinite henvelope hsimplex hlinear hmatrix
    hdecomp hdenominator hheterogeneity hresidual hfirst
    ⟨hscore, hfunctional, hequicontinuity⟩ hgodambe

/--
PATE finite score-cell estimated-score asymptotic normality from an explicit
local experiment, with the local derivative, stochastic equicontinuity, and
Godambe identity packaged in a compact core.
-/
theorem
    pate_estimated_score_asymptotic_normality_of_finite_score_cell_stochastic_local_experiment_core
    (known :
      PATEFiniteScoreCellKnownScoreAsymptoticBridge Cell)
    (estimated : EstimatedScoreLocalExperimentInput)
    (hknown_to_estimated :
      known.known_score_bridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hdesign :
      known.stochastic_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded :
      known.stochastic_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln :
      known.stochastic_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite :
      known.stochastic_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope :
      known.stochastic_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp : known.known_score_bridge.aggregate_hajek_decomposition)
    (hdenominator : known.known_score_bridge.denominator_stabilization)
    (hheterogeneity : known.known_score_bridge.heterogeneity_clt)
    (hresidual : known.known_score_bridge.residual_clt)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (core : EstimatedScoreLocalExperimentCore estimated) :
    known.stochastic_bridge.lln_bridge.indicator_bridge.pate_double_score_approximation_negligible ∧
      estimated.estimated_score_asymptotic_normality :=
  pate_estimated_score_asymptotic_normality_of_finite_score_cell_stochastic_local_experiment
    known estimated hknown_to_estimated hdesign hbounded harray_lln hfinite
    henvelope hsimplex hlinear hmatrix hdecomp hdenominator hheterogeneity
    hresidual hfirst hscore core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_variance_identity

/--
PATE finite score-cell estimated-score asymptotic normality from an explicit
local experiment whose first-step and score-local inputs are assembled from
PATE component first-step evidence.
-/
theorem
    pate_estimated_score_asymptotic_normality_of_finite_score_cell_stochastic_local_experiment_first_step_components
    (known :
      PATEFiniteScoreCellKnownScoreAsymptoticBridge Cell)
    (estimated : EstimatedScoreLocalExperimentInput)
    (firstStep : PATEDoubleScoreFirstStepAssembly)
    (hknown_to_estimated :
      known.known_score_bridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        estimated.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        estimated.score_estimator_local_asymptotic_linearity)
    (hdesign :
      known.stochastic_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded :
      known.stochastic_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln :
      known.stochastic_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite :
      known.stochastic_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope :
      known.stochastic_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp : known.known_score_bridge.aggregate_hajek_decomposition)
    (hdenominator : known.known_score_bridge.denominator_stabilization)
    (hheterogeneity : known.known_score_bridge.heterogeneity_clt)
    (hresidual : known.known_score_bridge.residual_clt)
    (h_prop_weight : firstStep.propensity_weighting_design)
    (h_treated_weight : firstStep.treated_prognostic_weighting_design)
    (h_control_weight : firstStep.control_prognostic_weighting_design)
    (h_prop : firstStep.propensity_component_asymptotic_linearity)
    (h_treated :
      firstStep.treated_prognostic_component_asymptotic_linearity)
    (h_control :
      firstStep.control_prognostic_component_asymptotic_linearity)
    (hfunctional : estimated.matching_functional_local_derivative)
    (hequicontinuity : estimated.local_stochastic_equicontinuity)
    (hgodambe : estimated.godambe_variance_identity) :
    known.stochastic_bridge.lln_bridge.indicator_bridge.pate_double_score_approximation_negligible ∧
      estimated.estimated_score_asymptotic_normality := by
  have hfirst_score :
      firstStep.first_step_asymptotic_linearization ∧
        firstStep.score_estimator_local_asymptotic_linearity :=
    pate_first_step_and_score_local_linearity_of_components firstStep
      h_prop_weight h_treated_weight h_control_weight h_prop h_treated
      h_control
  exact
    pate_estimated_score_asymptotic_normality_of_finite_score_cell_stochastic_local_experiment
      known estimated hknown_to_estimated hdesign hbounded harray_lln
      hfinite henvelope hsimplex hlinear hmatrix hdecomp hdenominator
      hheterogeneity hresidual (hfirst_transfer hfirst_score.1)
      (hscore_transfer hfirst_score.2) hfunctional hequicontinuity
      hgodambe

/--
PATE finite score-cell estimated-score asymptotic normality from component
first-step evidence and a compact local-experiment core.
-/
theorem
    pate_estimated_score_asymptotic_normality_of_finite_score_cell_stochastic_local_experiment_first_step_components_core
    (known :
      PATEFiniteScoreCellKnownScoreAsymptoticBridge Cell)
    (estimated : EstimatedScoreLocalExperimentInput)
    (firstStep : PATEDoubleScoreFirstStepAssembly)
    (hknown_to_estimated :
      known.known_score_bridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        estimated.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        estimated.score_estimator_local_asymptotic_linearity)
    (hdesign :
      known.stochastic_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded :
      known.stochastic_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln :
      known.stochastic_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite :
      known.stochastic_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope :
      known.stochastic_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp : known.known_score_bridge.aggregate_hajek_decomposition)
    (hdenominator : known.known_score_bridge.denominator_stabilization)
    (hheterogeneity : known.known_score_bridge.heterogeneity_clt)
    (hresidual : known.known_score_bridge.residual_clt)
    (h_prop_weight : firstStep.propensity_weighting_design)
    (h_treated_weight : firstStep.treated_prognostic_weighting_design)
    (h_control_weight : firstStep.control_prognostic_weighting_design)
    (h_prop : firstStep.propensity_component_asymptotic_linearity)
    (h_treated :
      firstStep.treated_prognostic_component_asymptotic_linearity)
    (h_control :
      firstStep.control_prognostic_component_asymptotic_linearity)
    (core : EstimatedScoreLocalExperimentCore estimated) :
    known.stochastic_bridge.lln_bridge.indicator_bridge.pate_double_score_approximation_negligible ∧
      estimated.estimated_score_asymptotic_normality :=
  pate_estimated_score_asymptotic_normality_of_finite_score_cell_stochastic_local_experiment_first_step_components
    known estimated firstStep hknown_to_estimated hfirst_transfer
    hscore_transfer hdesign hbounded harray_lln hfinite henvelope hsimplex
    hlinear hmatrix hdecomp hdenominator hheterogeneity hresidual
    h_prop_weight h_treated_weight h_control_weight h_prop h_treated
    h_control core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_variance_identity

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

/--
PATT finite score-cell estimated-score bridge built from the explicit
local-experiment input.
-/
def pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
    (known :
      PATTFiniteScoreCellKnownScoreAsymptoticBridge Cell)
    (estimated : EstimatedScoreLocalExperimentInput)
    (hknown_to_estimated :
      known.known_score_bridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality) :
    PATTFiniteScoreCellEstimatedScoreAsymptoticBridge Cell where
  known_score_finite_cell_bridge := known
  estimated_score_bridge :=
    estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated
  known_score_to_estimated_score_input := hknown_to_estimated

/--
PATT finite score-cell estimated-score asymptotic normality from the explicit
local-experiment input.
-/
theorem
    patt_estimated_score_asymptotic_normality_of_finite_score_cell_stochastic_local_experiment
    (known :
      PATTFiniteScoreCellKnownScoreAsymptoticBridge Cell)
    (estimated : EstimatedScoreLocalExperimentInput)
    (hknown_to_estimated :
      known.known_score_bridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hdesign :
      known.stochastic_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded :
      known.stochastic_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln :
      known.stochastic_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite :
      known.stochastic_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope :
      known.stochastic_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp : known.known_score_bridge.aggregate_hajek_decomposition)
    (hdenominator : known.known_score_bridge.denominator_stabilization)
    (hheterogeneity : known.known_score_bridge.heterogeneity_clt)
    (hresidual : known.known_score_bridge.residual_clt)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (hfunctional : estimated.matching_functional_local_derivative)
    (hequicontinuity : estimated.local_stochastic_equicontinuity)
    (hgodambe : estimated.godambe_variance_identity) :
    known.stochastic_bridge.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
      estimated.estimated_score_asymptotic_normality :=
  patt_estimated_score_asymptotic_normality_of_finite_score_cell_stochastic
    (pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
      known estimated hknown_to_estimated)
    hdesign hbounded harray_lln hfinite henvelope hsimplex hlinear hmatrix
    hdecomp hdenominator hheterogeneity hresidual hfirst
    ⟨hscore, hfunctional, hequicontinuity⟩ hgodambe

/--
PATT finite score-cell estimated-score asymptotic normality from an explicit
local experiment, with the local derivative, stochastic equicontinuity, and
Godambe identity packaged in a compact core.
-/
theorem
    patt_estimated_score_asymptotic_normality_of_finite_score_cell_stochastic_local_experiment_core
    (known :
      PATTFiniteScoreCellKnownScoreAsymptoticBridge Cell)
    (estimated : EstimatedScoreLocalExperimentInput)
    (hknown_to_estimated :
      known.known_score_bridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hdesign :
      known.stochastic_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded :
      known.stochastic_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln :
      known.stochastic_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite :
      known.stochastic_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope :
      known.stochastic_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp : known.known_score_bridge.aggregate_hajek_decomposition)
    (hdenominator : known.known_score_bridge.denominator_stabilization)
    (hheterogeneity : known.known_score_bridge.heterogeneity_clt)
    (hresidual : known.known_score_bridge.residual_clt)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (core : EstimatedScoreLocalExperimentCore estimated) :
    known.stochastic_bridge.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
      estimated.estimated_score_asymptotic_normality :=
  patt_estimated_score_asymptotic_normality_of_finite_score_cell_stochastic_local_experiment
    known estimated hknown_to_estimated hdesign hbounded harray_lln hfinite
    henvelope hsimplex hlinear hmatrix hdecomp hdenominator hheterogeneity
    hresidual hfirst hscore core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_variance_identity

/--
PATT finite score-cell estimated-score asymptotic normality from an explicit
local experiment whose first-step and score-local inputs are assembled from
PATT component first-step evidence.
-/
theorem
    patt_estimated_score_asymptotic_normality_of_finite_score_cell_stochastic_local_experiment_first_step_components
    (known :
      PATTFiniteScoreCellKnownScoreAsymptoticBridge Cell)
    (estimated : EstimatedScoreLocalExperimentInput)
    (firstStep : PATTDoubleScoreFirstStepAssembly)
    (hknown_to_estimated :
      known.known_score_bridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        estimated.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        estimated.score_estimator_local_asymptotic_linearity)
    (hdesign :
      known.stochastic_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded :
      known.stochastic_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln :
      known.stochastic_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite :
      known.stochastic_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope :
      known.stochastic_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp : known.known_score_bridge.aggregate_hajek_decomposition)
    (hdenominator : known.known_score_bridge.denominator_stabilization)
    (hheterogeneity : known.known_score_bridge.heterogeneity_clt)
    (hresidual : known.known_score_bridge.residual_clt)
    (h_prop_weight : firstStep.propensity_weighting_design)
    (h_control_weight : firstStep.control_prognostic_weighting_design)
    (h_prop : firstStep.propensity_component_asymptotic_linearity)
    (h_control :
      firstStep.control_prognostic_component_asymptotic_linearity)
    (hfunctional : estimated.matching_functional_local_derivative)
    (hequicontinuity : estimated.local_stochastic_equicontinuity)
    (hgodambe : estimated.godambe_variance_identity) :
    known.stochastic_bridge.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
      estimated.estimated_score_asymptotic_normality := by
  have hfirst_score :
      firstStep.first_step_asymptotic_linearization ∧
        firstStep.score_estimator_local_asymptotic_linearity :=
    patt_first_step_and_score_local_linearity_of_components firstStep
      h_prop_weight h_control_weight h_prop h_control
  exact
    patt_estimated_score_asymptotic_normality_of_finite_score_cell_stochastic_local_experiment
      known estimated hknown_to_estimated hdesign hbounded harray_lln
      hfinite henvelope hsimplex hlinear hmatrix hdecomp hdenominator
      hheterogeneity hresidual (hfirst_transfer hfirst_score.1)
      (hscore_transfer hfirst_score.2) hfunctional hequicontinuity
      hgodambe

/--
PATT finite score-cell estimated-score asymptotic normality from component
first-step evidence and a compact local-experiment core.
-/
theorem
    patt_estimated_score_asymptotic_normality_of_finite_score_cell_stochastic_local_experiment_first_step_components_core
    (known :
      PATTFiniteScoreCellKnownScoreAsymptoticBridge Cell)
    (estimated : EstimatedScoreLocalExperimentInput)
    (firstStep : PATTDoubleScoreFirstStepAssembly)
    (hknown_to_estimated :
      known.known_score_bridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        estimated.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        estimated.score_estimator_local_asymptotic_linearity)
    (hdesign :
      known.stochastic_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded :
      known.stochastic_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln :
      known.stochastic_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite :
      known.stochastic_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope :
      known.stochastic_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp : known.known_score_bridge.aggregate_hajek_decomposition)
    (hdenominator : known.known_score_bridge.denominator_stabilization)
    (hheterogeneity : known.known_score_bridge.heterogeneity_clt)
    (hresidual : known.known_score_bridge.residual_clt)
    (h_prop_weight : firstStep.propensity_weighting_design)
    (h_control_weight : firstStep.control_prognostic_weighting_design)
    (h_prop : firstStep.propensity_component_asymptotic_linearity)
    (h_control :
      firstStep.control_prognostic_component_asymptotic_linearity)
    (core : EstimatedScoreLocalExperimentCore estimated) :
    known.stochastic_bridge.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
      estimated.estimated_score_asymptotic_normality :=
  patt_estimated_score_asymptotic_normality_of_finite_score_cell_stochastic_local_experiment_first_step_components
    known estimated firstStep hknown_to_estimated hfirst_transfer
    hscore_transfer hdesign hbounded harray_lln hfinite henvelope hsimplex
    hlinear hmatrix hdecomp hdenominator hheterogeneity hresidual
    h_prop_weight h_control_weight h_prop h_control
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_variance_identity

end WDSM
end Matching
end StatInference
