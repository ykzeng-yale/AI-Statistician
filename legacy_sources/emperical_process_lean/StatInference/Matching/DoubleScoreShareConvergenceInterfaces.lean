import StatInference.Matching.WDSM.DiscreteDoubleScoreApproximateBalancingConvergence

/-!
# Double-score share convergence interfaces for WDSM

The deterministic WDSM approximation layer now reduces the main score-space
error to L1 convergence of normalized double-score share vectors, plus
envelope convergence and eventual finite positivity/coverage conditions.

This module records those remaining stochastic inputs as named bridge
interfaces.  They are not probability proofs.  They make the exact next
unproved layer explicit so reference results or future empirical-process work
can replace the bridge assumptions with concrete Lean theorems.
-/

namespace StatInference
namespace Matching
namespace WDSM

/--
Stochastic bridge for approximate PATE double-score balancing.

The intended future proof should derive `l1_double_score_share_convergence`
from a law of large numbers or empirical-process result for the joint
double-score partition, and derive `eventual_finite_conditions` from positivity
and support assumptions.
-/
structure PATEDoubleScoreShareConvergenceBridge where
  eventual_finite_conditions : Prop
  envelope_convergence : Prop
  l1_double_score_share_convergence : Prop
  pate_double_score_approximation_negligible : Prop
  bridge :
    eventual_finite_conditions ->
    envelope_convergence ->
    l1_double_score_share_convergence ->
    pate_double_score_approximation_negligible

theorem pate_double_score_approximation_negligible_of_share_bridge
    (b : PATEDoubleScoreShareConvergenceBridge)
    (hfinite : b.eventual_finite_conditions)
    (henvelope : b.envelope_convergence)
    (hl1 : b.l1_double_score_share_convergence) :
    b.pate_double_score_approximation_negligible :=
  b.bridge hfinite henvelope hl1

/--
Scaled stochastic bridge for approximate PATE double-score balancing.

This is the `sqrt n`-style version needed when the approximation term must be
negligible on the asymptotic-normality scale.
-/
structure ScaledPATEDoubleScoreShareConvergenceBridge where
  eventual_finite_conditions : Prop
  envelope_convergence : Prop
  scaled_l1_double_score_share_convergence : Prop
  scaled_pate_double_score_approximation_negligible : Prop
  bridge :
    eventual_finite_conditions ->
    envelope_convergence ->
    scaled_l1_double_score_share_convergence ->
    scaled_pate_double_score_approximation_negligible

theorem scaled_pate_double_score_approximation_negligible_of_share_bridge
    (b : ScaledPATEDoubleScoreShareConvergenceBridge)
    (hfinite : b.eventual_finite_conditions)
    (henvelope : b.envelope_convergence)
    (hl1 : b.scaled_l1_double_score_share_convergence) :
    b.scaled_pate_double_score_approximation_negligible :=
  b.bridge hfinite henvelope hl1

/--
Stochastic bridge for approximate PATT double-score balancing.

Only the counterfactual-control double-score share imbalance must converge,
because the treated target mean is observed directly in the one-sided PATT
contrast.
-/
structure PATTDoubleScoreShareConvergenceBridge where
  eventual_finite_conditions : Prop
  envelope_convergence : Prop
  l1_double_score_share_convergence : Prop
  patt_double_score_approximation_negligible : Prop
  bridge :
    eventual_finite_conditions ->
    envelope_convergence ->
    l1_double_score_share_convergence ->
    patt_double_score_approximation_negligible

theorem patt_double_score_approximation_negligible_of_share_bridge
    (b : PATTDoubleScoreShareConvergenceBridge)
    (hfinite : b.eventual_finite_conditions)
    (henvelope : b.envelope_convergence)
    (hl1 : b.l1_double_score_share_convergence) :
    b.patt_double_score_approximation_negligible :=
  b.bridge hfinite henvelope hl1

/-- Scaled version of the PATT double-score share convergence bridge. -/
structure ScaledPATTDoubleScoreShareConvergenceBridge where
  eventual_finite_conditions : Prop
  envelope_convergence : Prop
  scaled_l1_double_score_share_convergence : Prop
  scaled_patt_double_score_approximation_negligible : Prop
  bridge :
    eventual_finite_conditions ->
    envelope_convergence ->
    scaled_l1_double_score_share_convergence ->
    scaled_patt_double_score_approximation_negligible

theorem scaled_patt_double_score_approximation_negligible_of_share_bridge
    (b : ScaledPATTDoubleScoreShareConvergenceBridge)
    (hfinite : b.eventual_finite_conditions)
    (henvelope : b.envelope_convergence)
    (hl1 : b.scaled_l1_double_score_share_convergence) :
    b.scaled_patt_double_score_approximation_negligible :=
  b.bridge hfinite henvelope hl1

end WDSM
end Matching
end StatInference
