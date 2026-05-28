import StatInference.Matching.WDSM.IndicatorSumConvergenceInterfaces

/-!
# Finite score-cell indicator LLN interfaces for WDSM

The deterministic WDSM approximation layer reduces unscaled approximation
negligibility to weighted indicator-sum LLNs over a fixed finite joint-score
partition.  This module records the finite score-cell LLN as an explicit
bridge and composes it with the existing PATE/PATT indicator-sum approximation
interfaces.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Cell : Type*} [DecidableEq Cell]

/--
Named bridge for finite weighted score-cell indicator LLNs.

The bridge is intentionally probability-abstract: later survey-weighted LLN or
empirical-process work should replace `weighted_indicator_array_lln` by a
concrete theorem and discharge `cellwise_weighted_indicator_sum_lln`.
-/
structure FiniteScoreCellIndicatorLLNBridge
    (Cell : Type*) [DecidableEq Cell] where
  cells : Finset Cell
  referenceShare : Cell -> Real
  survey_design_regularity : Prop
  bounded_score_cell_indicators : Prop
  weighted_indicator_array_lln : Prop
  cellwise_weighted_indicator_sum_lln : Prop
  bridge :
    survey_design_regularity ->
    bounded_score_cell_indicators ->
    weighted_indicator_array_lln ->
    cellwise_weighted_indicator_sum_lln

theorem finite_score_cell_indicator_lln_of_bridge
    (b : FiniteScoreCellIndicatorLLNBridge Cell)
    (hdesign : b.survey_design_regularity)
    (hbounded : b.bounded_score_cell_indicators)
    (hlln : b.weighted_indicator_array_lln) :
    b.cellwise_weighted_indicator_sum_lln :=
  b.bridge hdesign hbounded hlln

/--
Composition bridge from finite score-cell indicator LLNs to unscaled PATE
double-score approximation negligibility.
-/
structure PATEFiniteScoreCellLLNApproximationBridge
    (Cell : Type*) [DecidableEq Cell] where
  lln_bridge : FiniteScoreCellIndicatorLLNBridge Cell
  indicator_bridge : PATEDoubleScoreIndicatorSumConvergenceBridge
  finite_lln_to_indicator_lln :
    lln_bridge.cellwise_weighted_indicator_sum_lln ->
      indicator_bridge.weighted_indicator_sum_lln

theorem pate_approximation_negligible_of_finite_score_cell_lln
    (b : PATEFiniteScoreCellLLNApproximationBridge Cell)
    (hdesign : b.lln_bridge.survey_design_regularity)
    (hbounded : b.lln_bridge.bounded_score_cell_indicators)
    (harray_lln : b.lln_bridge.weighted_indicator_array_lln)
    (hfinite : b.indicator_bridge.eventual_finite_conditions)
    (henvelope : b.indicator_bridge.envelope_convergence) :
    b.indicator_bridge.pate_double_score_approximation_negligible := by
  have hcell_lln : b.lln_bridge.cellwise_weighted_indicator_sum_lln :=
    finite_score_cell_indicator_lln_of_bridge
      b.lln_bridge hdesign hbounded harray_lln
  have hindicator : b.indicator_bridge.weighted_indicator_sum_lln :=
    b.finite_lln_to_indicator_lln hcell_lln
  exact pate_double_score_approximation_negligible_of_indicator_bridge
    b.indicator_bridge hfinite henvelope hindicator

/--
Composition bridge from finite score-cell indicator LLNs to unscaled PATT
double-score approximation negligibility.
-/
structure PATTFiniteScoreCellLLNApproximationBridge
    (Cell : Type*) [DecidableEq Cell] where
  lln_bridge : FiniteScoreCellIndicatorLLNBridge Cell
  indicator_bridge : PATTDoubleScoreIndicatorSumConvergenceBridge
  finite_lln_to_indicator_lln :
    lln_bridge.cellwise_weighted_indicator_sum_lln ->
      indicator_bridge.weighted_indicator_sum_lln

theorem patt_approximation_negligible_of_finite_score_cell_lln
    (b : PATTFiniteScoreCellLLNApproximationBridge Cell)
    (hdesign : b.lln_bridge.survey_design_regularity)
    (hbounded : b.lln_bridge.bounded_score_cell_indicators)
    (harray_lln : b.lln_bridge.weighted_indicator_array_lln)
    (hfinite : b.indicator_bridge.eventual_finite_conditions)
    (henvelope : b.indicator_bridge.envelope_convergence) :
    b.indicator_bridge.patt_double_score_approximation_negligible := by
  have hcell_lln : b.lln_bridge.cellwise_weighted_indicator_sum_lln :=
    finite_score_cell_indicator_lln_of_bridge
      b.lln_bridge hdesign hbounded harray_lln
  have hindicator : b.indicator_bridge.weighted_indicator_sum_lln :=
    b.finite_lln_to_indicator_lln hcell_lln
  exact patt_double_score_approximation_negligible_of_indicator_bridge
    b.indicator_bridge hfinite henvelope hindicator

end WDSM
end Matching
end StatInference
