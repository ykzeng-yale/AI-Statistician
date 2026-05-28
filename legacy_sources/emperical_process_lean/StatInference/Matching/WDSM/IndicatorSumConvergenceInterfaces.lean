import StatInference.Matching.WDSM.FiniteCellIndicatorApproximationConvergence

/-!
# Indicator-sum convergence interfaces for WDSM

The deterministic WDSM approximation layer has been reduced past normalized
share vectors and finite cell masses.  The remaining stochastic inputs are now
ordinary weighted sums of bounded `0/1` joint-score indicators.

This module records those probability-layer obligations as named bridge
interfaces.  They are not LLN or CLT proofs.  Their purpose is to expose the
exact final stochastic claims that future survey-weighted empirical-process
ports must prove before the WDSM approximation layer is fully discharged.
-/

namespace StatInference
namespace Matching
namespace WDSM

/--
Stochastic bridge for unscaled PATE approximation from weighted joint-score
indicator-sum LLNs.

The intended future proof should derive `weighted_indicator_sum_lln` for the
target, treated, and control samples over every fixed PATE joint-score cell,
and derive `eventual_finite_conditions` plus `envelope_convergence` from the
paper's positivity, boundedness, and score-support assumptions.
-/
structure PATEDoubleScoreIndicatorSumConvergenceBridge where
  eventual_finite_conditions : Prop
  envelope_convergence : Prop
  weighted_indicator_sum_lln : Prop
  pate_double_score_approximation_negligible : Prop
  bridge :
    eventual_finite_conditions ->
    envelope_convergence ->
    weighted_indicator_sum_lln ->
    pate_double_score_approximation_negligible

theorem pate_double_score_approximation_negligible_of_indicator_bridge
    (b : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (hfinite : b.eventual_finite_conditions)
    (henvelope : b.envelope_convergence)
    (hindicator : b.weighted_indicator_sum_lln) :
    b.pate_double_score_approximation_negligible :=
  b.bridge hfinite henvelope hindicator

/--
Scaled stochastic bridge for PATE approximation from weighted joint-score
indicator-sum LLNs plus scaled target-arm indicator-sum difference CLTs.
-/
structure ScaledPATEDoubleScoreIndicatorSumConvergenceBridge where
  eventual_finite_conditions : Prop
  envelope_convergence : Prop
  weighted_indicator_sum_lln : Prop
  scaled_weighted_indicator_sum_difference_clt : Prop
  scaled_pate_double_score_approximation_negligible : Prop
  bridge :
    eventual_finite_conditions ->
    envelope_convergence ->
    weighted_indicator_sum_lln ->
    scaled_weighted_indicator_sum_difference_clt ->
    scaled_pate_double_score_approximation_negligible

theorem scaled_pate_double_score_approximation_negligible_of_indicator_bridge
    (b : ScaledPATEDoubleScoreIndicatorSumConvergenceBridge)
    (hfinite : b.eventual_finite_conditions)
    (henvelope : b.envelope_convergence)
    (hlln : b.weighted_indicator_sum_lln)
    (hclt : b.scaled_weighted_indicator_sum_difference_clt) :
    b.scaled_pate_double_score_approximation_negligible :=
  b.bridge hfinite henvelope hlln hclt

/--
Stochastic bridge for unscaled PATT approximation from weighted joint-score
indicator-sum LLNs.

Only the target and control samples enter the one-sided PATT counterfactual
control approximation.
-/
structure PATTDoubleScoreIndicatorSumConvergenceBridge where
  eventual_finite_conditions : Prop
  envelope_convergence : Prop
  weighted_indicator_sum_lln : Prop
  patt_double_score_approximation_negligible : Prop
  bridge :
    eventual_finite_conditions ->
    envelope_convergence ->
    weighted_indicator_sum_lln ->
    patt_double_score_approximation_negligible

theorem patt_double_score_approximation_negligible_of_indicator_bridge
    (b : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (hfinite : b.eventual_finite_conditions)
    (henvelope : b.envelope_convergence)
    (hindicator : b.weighted_indicator_sum_lln) :
    b.patt_double_score_approximation_negligible :=
  b.bridge hfinite henvelope hindicator

/--
Scaled stochastic bridge for PATT approximation from weighted joint-score
indicator-sum LLNs plus scaled target-control indicator-sum difference CLTs.
-/
structure ScaledPATTDoubleScoreIndicatorSumConvergenceBridge where
  eventual_finite_conditions : Prop
  envelope_convergence : Prop
  weighted_indicator_sum_lln : Prop
  scaled_weighted_indicator_sum_difference_clt : Prop
  scaled_patt_double_score_approximation_negligible : Prop
  bridge :
    eventual_finite_conditions ->
    envelope_convergence ->
    weighted_indicator_sum_lln ->
    scaled_weighted_indicator_sum_difference_clt ->
    scaled_patt_double_score_approximation_negligible

theorem scaled_patt_double_score_approximation_negligible_of_indicator_bridge
    (b : ScaledPATTDoubleScoreIndicatorSumConvergenceBridge)
    (hfinite : b.eventual_finite_conditions)
    (henvelope : b.envelope_convergence)
    (hlln : b.weighted_indicator_sum_lln)
    (hclt : b.scaled_weighted_indicator_sum_difference_clt) :
    b.scaled_patt_double_score_approximation_negligible :=
  b.bridge hfinite henvelope hlln hclt

end WDSM
end Matching
end StatInference
