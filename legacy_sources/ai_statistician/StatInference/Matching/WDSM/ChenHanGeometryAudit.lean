import StatInference.Matching.WDSM.ReferenceTheorems

/-!
# Chen-Han geometry audit adapters

This module connects the Chen-Han-named geometry bridge used in the WDSM
reference layer to the generic weighted geometry moment bridge used in the
probability-layer interfaces.  The mathematical catchment/reuse-frequency
limit is still an explicit input; this file makes its role uniform.
-/

namespace StatInference
namespace Matching
namespace WDSM

/--
Package a generic weighted geometry moment bridge as the Chen-Han-named
geometry bridge used by the WDSM reference theorems.
-/
def chenHanGeometryBridgeOfWeightedGeometryMomentBridge
    (b : WeightedGeometryMomentBridge)
    (limitingVarianceFormula : Prop)
    (varianceTransfer :
      b.exact_weighted_reuse_moment_limits -> limitingVarianceFormula) :
    ChenHanGeometryBridge where
  score_density_regular := b.score_space_regularity
  nearest_neighbor_catchment_moments := b.chen_han_catchment_input
  reuse_frequency_moment_limits := b.exact_weighted_reuse_moment_limits
  limiting_variance_formula := limitingVarianceFormula
  moment_bridge := b.bridge
  variance_bridge := varianceTransfer

/--
Every Chen-Han-named geometry bridge gives a generic weighted geometry moment
bridge with the same regularity, catchment, and reuse-frequency claims.
-/
def weightedGeometryMomentBridgeOfChenHanGeometryBridge
    (b : ChenHanGeometryBridge) :
    WeightedGeometryMomentBridge where
  score_space_regularity := b.score_density_regular
  chen_han_catchment_input := b.nearest_neighbor_catchment_moments
  exact_weighted_reuse_moment_limits := b.reuse_frequency_moment_limits
  bridge := b.moment_bridge

/--
Generic weighted geometry moment evidence yields the Chen-Han reuse-frequency
moment limit and its limiting variance formula through the supplied variance
transfer.
-/
theorem chen_han_reuse_and_limiting_variance_of_weighted_geometry_bridge
    (b : WeightedGeometryMomentBridge)
    (limitingVarianceFormula : Prop)
    (varianceTransfer :
      b.exact_weighted_reuse_moment_limits -> limitingVarianceFormula)
    (hregular : b.score_space_regularity)
    (hcatchment : b.chen_han_catchment_input) :
    b.exact_weighted_reuse_moment_limits ∧ limitingVarianceFormula := by
  have hmoments : b.exact_weighted_reuse_moment_limits :=
    exact_weighted_reuse_moments_of_geometry b hregular hcatchment
  exact ⟨hmoments, varianceTransfer hmoments⟩

/--
Paired weighted geometry moment conclusions from two generic Chen-Han geometry
bridges.
-/
theorem paired_exact_weighted_reuse_moments_of_geometry
    (left right : WeightedGeometryMomentBridge)
    (hleft_regular : left.score_space_regularity)
    (hleft_catchment : left.chen_han_catchment_input)
    (hright_regular : right.score_space_regularity)
    (hright_catchment : right.chen_han_catchment_input) :
    left.exact_weighted_reuse_moment_limits ∧
      right.exact_weighted_reuse_moment_limits :=
  ⟨exact_weighted_reuse_moments_of_geometry left hleft_regular
      hleft_catchment,
    exact_weighted_reuse_moments_of_geometry right hright_regular
      hright_catchment⟩

/--
Paired Chen-Han reuse-frequency moment and limiting-variance conclusions from
two generic weighted geometry moment bridges.
-/
theorem paired_chen_han_reuse_and_limiting_variance_of_weighted_geometry_bridge
    (left right : WeightedGeometryMomentBridge)
    (leftLimitingVarianceFormula rightLimitingVarianceFormula : Prop)
    (leftVarianceTransfer :
      left.exact_weighted_reuse_moment_limits ->
        leftLimitingVarianceFormula)
    (rightVarianceTransfer :
      right.exact_weighted_reuse_moment_limits ->
        rightLimitingVarianceFormula)
    (hleft_regular : left.score_space_regularity)
    (hleft_catchment : left.chen_han_catchment_input)
    (hright_regular : right.score_space_regularity)
    (hright_catchment : right.chen_han_catchment_input) :
    left.exact_weighted_reuse_moment_limits ∧
      leftLimitingVarianceFormula ∧
      right.exact_weighted_reuse_moment_limits ∧
      rightLimitingVarianceFormula := by
  have hleft :
      left.exact_weighted_reuse_moment_limits ∧
        leftLimitingVarianceFormula :=
    chen_han_reuse_and_limiting_variance_of_weighted_geometry_bridge
      left leftLimitingVarianceFormula leftVarianceTransfer
      hleft_regular hleft_catchment
  have hright :
      right.exact_weighted_reuse_moment_limits ∧
        rightLimitingVarianceFormula :=
    chen_han_reuse_and_limiting_variance_of_weighted_geometry_bridge
      right rightLimitingVarianceFormula rightVarianceTransfer
      hright_regular hright_catchment
  exact ⟨hleft.1, hleft.2, hright.1, hright.2⟩

/--
The Chen-Han-named and generic bridge views have the same reuse-frequency
moment conclusion under matching regularity and catchment inputs.
-/
theorem chen_han_reuse_moment_limits_eq_weighted_geometry_moments
    (b : WeightedGeometryMomentBridge)
    (limitingVarianceFormula : Prop)
    (varianceTransfer :
      b.exact_weighted_reuse_moment_limits -> limitingVarianceFormula)
    (hregular : b.score_space_regularity)
    (hcatchment : b.chen_han_catchment_input) :
    (chenHanGeometryBridgeOfWeightedGeometryMomentBridge b
      limitingVarianceFormula varianceTransfer).reuse_frequency_moment_limits :=
  chen_han_reuse_moment_limits_of_bridge
    (chenHanGeometryBridgeOfWeightedGeometryMomentBridge b
      limitingVarianceFormula varianceTransfer)
    hregular hcatchment

end WDSM
end Matching
end StatInference
