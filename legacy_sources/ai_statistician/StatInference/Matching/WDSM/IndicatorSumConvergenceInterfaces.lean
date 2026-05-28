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

/--
Paired PATE/PATT approximation negligibility from their indicator-sum bridges.
-/
theorem pate_patt_double_score_approximation_negligible_of_indicator_bridges
    (pate : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (patt : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (hpateFinite : pate.eventual_finite_conditions)
    (hpateEnvelope : pate.envelope_convergence)
    (hpateIndicator : pate.weighted_indicator_sum_lln)
    (hpattFinite : patt.eventual_finite_conditions)
    (hpattEnvelope : patt.envelope_convergence)
    (hpattIndicator : patt.weighted_indicator_sum_lln) :
    pate.pate_double_score_approximation_negligible ∧
      patt.patt_double_score_approximation_negligible :=
  ⟨pate_double_score_approximation_negligible_of_indicator_bridge
      pate hpateFinite hpateEnvelope hpateIndicator,
    patt_double_score_approximation_negligible_of_indicator_bridge
      patt hpattFinite hpattEnvelope hpattIndicator⟩

/--
Paired PATE/PATT approximation negligibility from indicator-sum bridges with
the finite, envelope, and indicator LLN inputs packaged as paired hypotheses.
-/
theorem pate_patt_double_score_approximation_negligible_of_indicator_bridge_inputs
    (pate : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (patt : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (hfinite :
      pate.eventual_finite_conditions ∧ patt.eventual_finite_conditions)
    (henvelope :
      pate.envelope_convergence ∧ patt.envelope_convergence)
    (hindicator :
      pate.weighted_indicator_sum_lln ∧
        patt.weighted_indicator_sum_lln) :
    pate.pate_double_score_approximation_negligible ∧
      patt.patt_double_score_approximation_negligible :=
  pate_patt_double_score_approximation_negligible_of_indicator_bridges
    pate patt hfinite.1 henvelope.1 hindicator.1 hfinite.2 henvelope.2
    hindicator.2

/--
Paired scaled PATE/PATT approximation negligibility from their indicator-sum
bridges.
-/
theorem scaled_pate_patt_double_score_approximation_negligible_of_indicator_bridges
    (pate : ScaledPATEDoubleScoreIndicatorSumConvergenceBridge)
    (patt : ScaledPATTDoubleScoreIndicatorSumConvergenceBridge)
    (hpateFinite : pate.eventual_finite_conditions)
    (hpateEnvelope : pate.envelope_convergence)
    (hpateLLN : pate.weighted_indicator_sum_lln)
    (hpateCLT : pate.scaled_weighted_indicator_sum_difference_clt)
    (hpattFinite : patt.eventual_finite_conditions)
    (hpattEnvelope : patt.envelope_convergence)
    (hpattLLN : patt.weighted_indicator_sum_lln)
    (hpattCLT : patt.scaled_weighted_indicator_sum_difference_clt) :
    pate.scaled_pate_double_score_approximation_negligible ∧
      patt.scaled_patt_double_score_approximation_negligible :=
  ⟨scaled_pate_double_score_approximation_negligible_of_indicator_bridge
      pate hpateFinite hpateEnvelope hpateLLN hpateCLT,
    scaled_patt_double_score_approximation_negligible_of_indicator_bridge
      patt hpattFinite hpattEnvelope hpattLLN hpattCLT⟩

/--
Paired scaled PATE/PATT approximation negligibility from indicator-sum bridges
with finite, envelope, LLN, and scaled CLT inputs packaged as paired
hypotheses.
-/
theorem scaled_pate_patt_double_score_approximation_negligible_of_indicator_bridge_inputs
    (pate : ScaledPATEDoubleScoreIndicatorSumConvergenceBridge)
    (patt : ScaledPATTDoubleScoreIndicatorSumConvergenceBridge)
    (hfinite :
      pate.eventual_finite_conditions ∧ patt.eventual_finite_conditions)
    (henvelope :
      pate.envelope_convergence ∧ patt.envelope_convergence)
    (hlln :
      pate.weighted_indicator_sum_lln ∧ patt.weighted_indicator_sum_lln)
    (hclt :
      pate.scaled_weighted_indicator_sum_difference_clt ∧
        patt.scaled_weighted_indicator_sum_difference_clt) :
    pate.scaled_pate_double_score_approximation_negligible ∧
      patt.scaled_patt_double_score_approximation_negligible :=
  scaled_pate_patt_double_score_approximation_negligible_of_indicator_bridges
    pate patt hfinite.1 henvelope.1 hlln.1 hclt.1 hfinite.2 henvelope.2
    hlln.2 hclt.2

/--
PATE approximation negligibility at ordinary and scaled rates from
indicator-sum bridges.
-/
theorem pate_double_score_approximation_negligible_and_scaled_negligible_of_indicator_bridges
    (ordinary : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (scaled : ScaledPATEDoubleScoreIndicatorSumConvergenceBridge)
    (hordinaryFinite : ordinary.eventual_finite_conditions)
    (hordinaryEnvelope : ordinary.envelope_convergence)
    (hordinaryIndicator : ordinary.weighted_indicator_sum_lln)
    (hscaledFinite : scaled.eventual_finite_conditions)
    (hscaledEnvelope : scaled.envelope_convergence)
    (hscaledLLN : scaled.weighted_indicator_sum_lln)
    (hscaledCLT : scaled.scaled_weighted_indicator_sum_difference_clt) :
    ordinary.pate_double_score_approximation_negligible ∧
      scaled.scaled_pate_double_score_approximation_negligible :=
  ⟨pate_double_score_approximation_negligible_of_indicator_bridge
      ordinary hordinaryFinite hordinaryEnvelope hordinaryIndicator,
    scaled_pate_double_score_approximation_negligible_of_indicator_bridge
      scaled hscaledFinite hscaledEnvelope hscaledLLN hscaledCLT⟩

/--
PATT approximation negligibility at ordinary and scaled rates from
indicator-sum bridges.
-/
theorem patt_double_score_approximation_negligible_and_scaled_negligible_of_indicator_bridges
    (ordinary : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (scaled : ScaledPATTDoubleScoreIndicatorSumConvergenceBridge)
    (hordinaryFinite : ordinary.eventual_finite_conditions)
    (hordinaryEnvelope : ordinary.envelope_convergence)
    (hordinaryIndicator : ordinary.weighted_indicator_sum_lln)
    (hscaledFinite : scaled.eventual_finite_conditions)
    (hscaledEnvelope : scaled.envelope_convergence)
    (hscaledLLN : scaled.weighted_indicator_sum_lln)
    (hscaledCLT : scaled.scaled_weighted_indicator_sum_difference_clt) :
    ordinary.patt_double_score_approximation_negligible ∧
      scaled.scaled_patt_double_score_approximation_negligible :=
  ⟨patt_double_score_approximation_negligible_of_indicator_bridge
      ordinary hordinaryFinite hordinaryEnvelope hordinaryIndicator,
    scaled_patt_double_score_approximation_negligible_of_indicator_bridge
      scaled hscaledFinite hscaledEnvelope hscaledLLN hscaledCLT⟩

/--
Paired PATE/PATT approximation negligibility at ordinary and scaled rates from
indicator-sum bridges.
-/
theorem pate_patt_double_score_approximation_negligible_and_scaled_negligible_of_indicator_bridges
    (pateOrdinary : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateScaled : ScaledPATEDoubleScoreIndicatorSumConvergenceBridge)
    (pattOrdinary : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattScaled : ScaledPATTDoubleScoreIndicatorSumConvergenceBridge)
    (hpateOrdinaryFinite : pateOrdinary.eventual_finite_conditions)
    (hpateOrdinaryEnvelope : pateOrdinary.envelope_convergence)
    (hpateOrdinaryIndicator : pateOrdinary.weighted_indicator_sum_lln)
    (hpateScaledFinite : pateScaled.eventual_finite_conditions)
    (hpateScaledEnvelope : pateScaled.envelope_convergence)
    (hpateScaledLLN : pateScaled.weighted_indicator_sum_lln)
    (hpateScaledCLT :
      pateScaled.scaled_weighted_indicator_sum_difference_clt)
    (hpattOrdinaryFinite : pattOrdinary.eventual_finite_conditions)
    (hpattOrdinaryEnvelope : pattOrdinary.envelope_convergence)
    (hpattOrdinaryIndicator : pattOrdinary.weighted_indicator_sum_lln)
    (hpattScaledFinite : pattScaled.eventual_finite_conditions)
    (hpattScaledEnvelope : pattScaled.envelope_convergence)
    (hpattScaledLLN : pattScaled.weighted_indicator_sum_lln)
    (hpattScaledCLT :
      pattScaled.scaled_weighted_indicator_sum_difference_clt) :
    (pateOrdinary.pate_double_score_approximation_negligible ∧
      pateScaled.scaled_pate_double_score_approximation_negligible) ∧
      (pattOrdinary.patt_double_score_approximation_negligible ∧
        pattScaled.scaled_patt_double_score_approximation_negligible) :=
  ⟨pate_double_score_approximation_negligible_and_scaled_negligible_of_indicator_bridges
      pateOrdinary pateScaled hpateOrdinaryFinite hpateOrdinaryEnvelope
      hpateOrdinaryIndicator hpateScaledFinite hpateScaledEnvelope
      hpateScaledLLN hpateScaledCLT,
    patt_double_score_approximation_negligible_and_scaled_negligible_of_indicator_bridges
      pattOrdinary pattScaled hpattOrdinaryFinite hpattOrdinaryEnvelope
      hpattOrdinaryIndicator hpattScaledFinite hpattScaledEnvelope
      hpattScaledLLN hpattScaledCLT⟩

/--
Paired PATE/PATT approximation negligibility at ordinary and scaled rates from
indicator-sum bridges with paired inputs packaged as conjunctions.
-/
theorem pate_patt_double_score_approximation_negligible_and_scaled_negligible_of_indicator_bridge_inputs
    (pateOrdinary : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateScaled : ScaledPATEDoubleScoreIndicatorSumConvergenceBridge)
    (pattOrdinary : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattScaled : ScaledPATTDoubleScoreIndicatorSumConvergenceBridge)
    (hordinaryFinite :
      pateOrdinary.eventual_finite_conditions ∧
        pattOrdinary.eventual_finite_conditions)
    (hordinaryEnvelope :
      pateOrdinary.envelope_convergence ∧
        pattOrdinary.envelope_convergence)
    (hordinaryIndicator :
      pateOrdinary.weighted_indicator_sum_lln ∧
        pattOrdinary.weighted_indicator_sum_lln)
    (hscaledFinite :
      pateScaled.eventual_finite_conditions ∧
        pattScaled.eventual_finite_conditions)
    (hscaledEnvelope :
      pateScaled.envelope_convergence ∧ pattScaled.envelope_convergence)
    (hscaledLLN :
      pateScaled.weighted_indicator_sum_lln ∧
        pattScaled.weighted_indicator_sum_lln)
    (hscaledCLT :
      pateScaled.scaled_weighted_indicator_sum_difference_clt ∧
        pattScaled.scaled_weighted_indicator_sum_difference_clt) :
    (pateOrdinary.pate_double_score_approximation_negligible ∧
      pateScaled.scaled_pate_double_score_approximation_negligible) ∧
      (pattOrdinary.patt_double_score_approximation_negligible ∧
        pattScaled.scaled_patt_double_score_approximation_negligible) :=
  pate_patt_double_score_approximation_negligible_and_scaled_negligible_of_indicator_bridges
    pateOrdinary pateScaled pattOrdinary pattScaled hordinaryFinite.1
    hordinaryEnvelope.1 hordinaryIndicator.1 hscaledFinite.1
    hscaledEnvelope.1 hscaledLLN.1 hscaledCLT.1 hordinaryFinite.2
    hordinaryEnvelope.2 hordinaryIndicator.2 hscaledFinite.2
    hscaledEnvelope.2 hscaledLLN.2 hscaledCLT.2

end WDSM
end Matching
end StatInference
