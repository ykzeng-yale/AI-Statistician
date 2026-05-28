import StatInference.Matching.WDSM.ChenHanGeometryAudit
import StatInference.Matching.WDSM.FiniteCellIndicatorLLNInterfaces

/-!
# Finite-cell route to weighted geometry moments

This module connects fixed finite score-cell indicator LLN interfaces to the
generic weighted geometry moment bridge.  It gives the Chen-Han catchment
obligation a more concrete reduction target: prove finite weighted
score-cell indicator LLNs and transfer them to the reuse-moment limit.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Cell : Type*} [DecidableEq Cell]

/--
Build a generic weighted geometry moment bridge from a finite score-cell
indicator LLN bridge and explicit transfers from the finite-cell LLN output
to the weighted reuse-moment target.
-/
def weightedGeometryMomentBridgeOfFiniteCellIndicatorLLN
    (lln : FiniteScoreCellIndicatorLLNBridge Cell)
    (scoreSpaceRegularity catchmentInput exactWeightedReuseMomentLimits : Prop)
    (regularity_to_design :
      scoreSpaceRegularity -> lln.survey_design_regularity)
    (catchment_to_bounded :
      catchmentInput -> lln.bounded_score_cell_indicators)
    (catchment_to_array_lln :
      catchmentInput -> lln.weighted_indicator_array_lln)
    (finite_cell_lln_to_reuse_moments :
      lln.cellwise_weighted_indicator_sum_lln ->
        exactWeightedReuseMomentLimits) :
    WeightedGeometryMomentBridge where
  score_space_regularity := scoreSpaceRegularity
  chen_han_catchment_input := catchmentInput
  exact_weighted_reuse_moment_limits := exactWeightedReuseMomentLimits
  bridge := by
    intro hregular hcatchment
    exact finite_cell_lln_to_reuse_moments
      (finite_score_cell_indicator_lln_of_bridge lln
        (regularity_to_design hregular)
        (catchment_to_bounded hcatchment)
        (catchment_to_array_lln hcatchment))

/--
Finite score-cell indicator LLN evidence yields weighted geometry moments
after the supplied finite-cell-to-reuse transfer.
-/
theorem weighted_geometry_moments_of_finite_cell_indicator_lln
    (lln : FiniteScoreCellIndicatorLLNBridge Cell)
    (scoreSpaceRegularity catchmentInput exactWeightedReuseMomentLimits : Prop)
    (regularity_to_design :
      scoreSpaceRegularity -> lln.survey_design_regularity)
    (catchment_to_bounded :
      catchmentInput -> lln.bounded_score_cell_indicators)
    (catchment_to_array_lln :
      catchmentInput -> lln.weighted_indicator_array_lln)
    (finite_cell_lln_to_reuse_moments :
      lln.cellwise_weighted_indicator_sum_lln ->
        exactWeightedReuseMomentLimits)
    (hregular : scoreSpaceRegularity)
    (hcatchment : catchmentInput) :
    exactWeightedReuseMomentLimits := by
  exact exact_weighted_reuse_moments_of_geometry
    (weightedGeometryMomentBridgeOfFiniteCellIndicatorLLN lln
      scoreSpaceRegularity catchmentInput exactWeightedReuseMomentLimits
      regularity_to_design catchment_to_bounded catchment_to_array_lln
      finite_cell_lln_to_reuse_moments)
    hregular hcatchment

/--
Finite score-cell indicator LLN evidence also yields the Chen-Han-named reuse
moment and limiting-variance conclusions once a variance transfer is supplied.
-/
theorem chen_han_reuse_and_variance_of_finite_cell_indicator_lln
    (lln : FiniteScoreCellIndicatorLLNBridge Cell)
    (scoreSpaceRegularity catchmentInput exactWeightedReuseMomentLimits
      limitingVarianceFormula : Prop)
    (regularity_to_design :
      scoreSpaceRegularity -> lln.survey_design_regularity)
    (catchment_to_bounded :
      catchmentInput -> lln.bounded_score_cell_indicators)
    (catchment_to_array_lln :
      catchmentInput -> lln.weighted_indicator_array_lln)
    (finite_cell_lln_to_reuse_moments :
      lln.cellwise_weighted_indicator_sum_lln ->
        exactWeightedReuseMomentLimits)
    (varianceTransfer :
      exactWeightedReuseMomentLimits -> limitingVarianceFormula)
    (hregular : scoreSpaceRegularity)
    (hcatchment : catchmentInput) :
    exactWeightedReuseMomentLimits ∧ limitingVarianceFormula := by
  exact chen_han_reuse_and_limiting_variance_of_weighted_geometry_bridge
    (weightedGeometryMomentBridgeOfFiniteCellIndicatorLLN lln
      scoreSpaceRegularity catchmentInput exactWeightedReuseMomentLimits
      regularity_to_design catchment_to_bounded catchment_to_array_lln
      finite_cell_lln_to_reuse_moments)
    limitingVarianceFormula varianceTransfer hregular hcatchment

/--
Paired weighted geometry moments from two finite score-cell indicator LLN
bridges.
-/
theorem paired_weighted_geometry_moments_of_finite_cell_indicator_lln
    {LeftCell RightCell : Type*}
    [DecidableEq LeftCell] [DecidableEq RightCell]
    (leftLLN : FiniteScoreCellIndicatorLLNBridge LeftCell)
    (rightLLN : FiniteScoreCellIndicatorLLNBridge RightCell)
    (leftScoreSpaceRegularity leftCatchmentInput
      leftExactWeightedReuseMomentLimits : Prop)
    (rightScoreSpaceRegularity rightCatchmentInput
      rightExactWeightedReuseMomentLimits : Prop)
    (left_regularity_to_design :
      leftScoreSpaceRegularity -> leftLLN.survey_design_regularity)
    (left_catchment_to_bounded :
      leftCatchmentInput -> leftLLN.bounded_score_cell_indicators)
    (left_catchment_to_array_lln :
      leftCatchmentInput -> leftLLN.weighted_indicator_array_lln)
    (left_finite_cell_lln_to_reuse_moments :
      leftLLN.cellwise_weighted_indicator_sum_lln ->
        leftExactWeightedReuseMomentLimits)
    (right_regularity_to_design :
      rightScoreSpaceRegularity -> rightLLN.survey_design_regularity)
    (right_catchment_to_bounded :
      rightCatchmentInput -> rightLLN.bounded_score_cell_indicators)
    (right_catchment_to_array_lln :
      rightCatchmentInput -> rightLLN.weighted_indicator_array_lln)
    (right_finite_cell_lln_to_reuse_moments :
      rightLLN.cellwise_weighted_indicator_sum_lln ->
        rightExactWeightedReuseMomentLimits)
    (hleft_regular : leftScoreSpaceRegularity)
    (hleft_catchment : leftCatchmentInput)
    (hright_regular : rightScoreSpaceRegularity)
    (hright_catchment : rightCatchmentInput) :
    leftExactWeightedReuseMomentLimits ∧
      rightExactWeightedReuseMomentLimits :=
  ⟨weighted_geometry_moments_of_finite_cell_indicator_lln
      leftLLN leftScoreSpaceRegularity leftCatchmentInput
      leftExactWeightedReuseMomentLimits left_regularity_to_design
      left_catchment_to_bounded left_catchment_to_array_lln
      left_finite_cell_lln_to_reuse_moments hleft_regular
      hleft_catchment,
    weighted_geometry_moments_of_finite_cell_indicator_lln
      rightLLN rightScoreSpaceRegularity rightCatchmentInput
      rightExactWeightedReuseMomentLimits right_regularity_to_design
      right_catchment_to_bounded right_catchment_to_array_lln
      right_finite_cell_lln_to_reuse_moments hright_regular
      hright_catchment⟩

/--
Paired Chen-Han reuse-moment and limiting-variance conclusions from two
finite score-cell indicator LLN bridges.
-/
theorem paired_chen_han_reuse_and_variance_of_finite_cell_indicator_lln
    {LeftCell RightCell : Type*}
    [DecidableEq LeftCell] [DecidableEq RightCell]
    (leftLLN : FiniteScoreCellIndicatorLLNBridge LeftCell)
    (rightLLN : FiniteScoreCellIndicatorLLNBridge RightCell)
    (leftScoreSpaceRegularity leftCatchmentInput
      leftExactWeightedReuseMomentLimits leftLimitingVarianceFormula : Prop)
    (rightScoreSpaceRegularity rightCatchmentInput
      rightExactWeightedReuseMomentLimits rightLimitingVarianceFormula : Prop)
    (left_regularity_to_design :
      leftScoreSpaceRegularity -> leftLLN.survey_design_regularity)
    (left_catchment_to_bounded :
      leftCatchmentInput -> leftLLN.bounded_score_cell_indicators)
    (left_catchment_to_array_lln :
      leftCatchmentInput -> leftLLN.weighted_indicator_array_lln)
    (left_finite_cell_lln_to_reuse_moments :
      leftLLN.cellwise_weighted_indicator_sum_lln ->
        leftExactWeightedReuseMomentLimits)
    (left_variance_transfer :
      leftExactWeightedReuseMomentLimits -> leftLimitingVarianceFormula)
    (right_regularity_to_design :
      rightScoreSpaceRegularity -> rightLLN.survey_design_regularity)
    (right_catchment_to_bounded :
      rightCatchmentInput -> rightLLN.bounded_score_cell_indicators)
    (right_catchment_to_array_lln :
      rightCatchmentInput -> rightLLN.weighted_indicator_array_lln)
    (right_finite_cell_lln_to_reuse_moments :
      rightLLN.cellwise_weighted_indicator_sum_lln ->
        rightExactWeightedReuseMomentLimits)
    (right_variance_transfer :
      rightExactWeightedReuseMomentLimits -> rightLimitingVarianceFormula)
    (hleft_regular : leftScoreSpaceRegularity)
    (hleft_catchment : leftCatchmentInput)
    (hright_regular : rightScoreSpaceRegularity)
    (hright_catchment : rightCatchmentInput) :
    leftExactWeightedReuseMomentLimits ∧
      leftLimitingVarianceFormula ∧
      rightExactWeightedReuseMomentLimits ∧
      rightLimitingVarianceFormula := by
  have hleft :
      leftExactWeightedReuseMomentLimits ∧ leftLimitingVarianceFormula :=
    chen_han_reuse_and_variance_of_finite_cell_indicator_lln
      leftLLN leftScoreSpaceRegularity leftCatchmentInput
      leftExactWeightedReuseMomentLimits leftLimitingVarianceFormula
      left_regularity_to_design left_catchment_to_bounded
      left_catchment_to_array_lln left_finite_cell_lln_to_reuse_moments
      left_variance_transfer hleft_regular hleft_catchment
  have hright :
      rightExactWeightedReuseMomentLimits ∧ rightLimitingVarianceFormula :=
    chen_han_reuse_and_variance_of_finite_cell_indicator_lln
      rightLLN rightScoreSpaceRegularity rightCatchmentInput
      rightExactWeightedReuseMomentLimits rightLimitingVarianceFormula
      right_regularity_to_design right_catchment_to_bounded
      right_catchment_to_array_lln right_finite_cell_lln_to_reuse_moments
      right_variance_transfer hright_regular hright_catchment
  exact ⟨hleft.1, hleft.2, hright.1, hright.2⟩

end WDSM
end Matching
end StatInference
