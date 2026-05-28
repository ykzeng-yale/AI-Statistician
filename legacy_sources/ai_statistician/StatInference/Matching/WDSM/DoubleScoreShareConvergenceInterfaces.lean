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

/-- Paired PATE/PATT ordinary double-score share convergence bridge. -/
structure PATEPATTDoubleScoreShareConvergenceBridge where
  pate_bridge : PATEDoubleScoreShareConvergenceBridge
  patt_bridge : PATTDoubleScoreShareConvergenceBridge

/-- Paired PATE/PATT scaled double-score share convergence bridge. -/
structure ScaledPATEPATTDoubleScoreShareConvergenceBridge where
  pate_bridge : ScaledPATEDoubleScoreShareConvergenceBridge
  patt_bridge : ScaledPATTDoubleScoreShareConvergenceBridge

/-- Paired PATE/PATT approximation negligibility from share bridges. -/
theorem pate_patt_double_score_approximation_negligible_of_share_bridges
    (pate : PATEDoubleScoreShareConvergenceBridge)
    (patt : PATTDoubleScoreShareConvergenceBridge)
    (hpateFinite : pate.eventual_finite_conditions)
    (hpateEnvelope : pate.envelope_convergence)
    (hpateL1 : pate.l1_double_score_share_convergence)
    (hpattFinite : patt.eventual_finite_conditions)
    (hpattEnvelope : patt.envelope_convergence)
    (hpattL1 : patt.l1_double_score_share_convergence) :
    pate.pate_double_score_approximation_negligible ∧
      patt.patt_double_score_approximation_negligible :=
  ⟨pate_double_score_approximation_negligible_of_share_bridge
      pate hpateFinite hpateEnvelope hpateL1,
    patt_double_score_approximation_negligible_of_share_bridge
      patt hpattFinite hpattEnvelope hpattL1⟩

/--
Paired PATE/PATT approximation negligibility from share bridges with the
finite, envelope, and L1 inputs packaged as paired hypotheses.
-/
theorem pate_patt_double_score_approximation_negligible_of_share_bridge_inputs
    (pate : PATEDoubleScoreShareConvergenceBridge)
    (patt : PATTDoubleScoreShareConvergenceBridge)
    (hfinite :
      pate.eventual_finite_conditions ∧ patt.eventual_finite_conditions)
    (henvelope :
      pate.envelope_convergence ∧ patt.envelope_convergence)
    (hl1 :
      pate.l1_double_score_share_convergence ∧
        patt.l1_double_score_share_convergence) :
    pate.pate_double_score_approximation_negligible ∧
      patt.patt_double_score_approximation_negligible :=
  pate_patt_double_score_approximation_negligible_of_share_bridges
    pate patt hfinite.1 henvelope.1 hl1.1 hfinite.2 henvelope.2 hl1.2

/--
Paired PATE/PATT approximation negligibility from a single paired ordinary
share-convergence bridge.
-/
theorem pate_patt_double_score_approximation_negligible_of_paired_share_bridge
    (b : PATEPATTDoubleScoreShareConvergenceBridge)
    (hfinite :
      b.pate_bridge.eventual_finite_conditions ∧
        b.patt_bridge.eventual_finite_conditions)
    (henvelope :
      b.pate_bridge.envelope_convergence ∧
        b.patt_bridge.envelope_convergence)
    (hl1 :
      b.pate_bridge.l1_double_score_share_convergence ∧
        b.patt_bridge.l1_double_score_share_convergence) :
    b.pate_bridge.pate_double_score_approximation_negligible ∧
      b.patt_bridge.patt_double_score_approximation_negligible :=
  pate_patt_double_score_approximation_negligible_of_share_bridge_inputs
    b.pate_bridge b.patt_bridge hfinite henvelope hl1

/-- Paired scaled PATE/PATT approximation negligibility from share bridges. -/
theorem scaled_pate_patt_double_score_approximation_negligible_of_share_bridges
    (pate : ScaledPATEDoubleScoreShareConvergenceBridge)
    (patt : ScaledPATTDoubleScoreShareConvergenceBridge)
    (hpateFinite : pate.eventual_finite_conditions)
    (hpateEnvelope : pate.envelope_convergence)
    (hpateL1 : pate.scaled_l1_double_score_share_convergence)
    (hpattFinite : patt.eventual_finite_conditions)
    (hpattEnvelope : patt.envelope_convergence)
    (hpattL1 : patt.scaled_l1_double_score_share_convergence) :
    pate.scaled_pate_double_score_approximation_negligible ∧
      patt.scaled_patt_double_score_approximation_negligible :=
  ⟨scaled_pate_double_score_approximation_negligible_of_share_bridge
      pate hpateFinite hpateEnvelope hpateL1,
    scaled_patt_double_score_approximation_negligible_of_share_bridge
      patt hpattFinite hpattEnvelope hpattL1⟩

/--
Paired scaled PATE/PATT approximation negligibility from share bridges with
the finite, envelope, and scaled L1 inputs packaged as paired hypotheses.
-/
theorem scaled_pate_patt_double_score_approximation_negligible_of_share_bridge_inputs
    (pate : ScaledPATEDoubleScoreShareConvergenceBridge)
    (patt : ScaledPATTDoubleScoreShareConvergenceBridge)
    (hfinite :
      pate.eventual_finite_conditions ∧ patt.eventual_finite_conditions)
    (henvelope :
      pate.envelope_convergence ∧ patt.envelope_convergence)
    (hl1 :
      pate.scaled_l1_double_score_share_convergence ∧
        patt.scaled_l1_double_score_share_convergence) :
    pate.scaled_pate_double_score_approximation_negligible ∧
      patt.scaled_patt_double_score_approximation_negligible :=
  scaled_pate_patt_double_score_approximation_negligible_of_share_bridges
    pate patt hfinite.1 henvelope.1 hl1.1 hfinite.2 henvelope.2 hl1.2

/--
Paired scaled PATE/PATT approximation negligibility from a single paired
scaled share-convergence bridge.
-/
theorem scaled_pate_patt_double_score_approximation_negligible_of_paired_share_bridge
    (b : ScaledPATEPATTDoubleScoreShareConvergenceBridge)
    (hfinite :
      b.pate_bridge.eventual_finite_conditions ∧
        b.patt_bridge.eventual_finite_conditions)
    (henvelope :
      b.pate_bridge.envelope_convergence ∧
        b.patt_bridge.envelope_convergence)
    (hl1 :
      b.pate_bridge.scaled_l1_double_score_share_convergence ∧
        b.patt_bridge.scaled_l1_double_score_share_convergence) :
    b.pate_bridge.scaled_pate_double_score_approximation_negligible ∧
      b.patt_bridge.scaled_patt_double_score_approximation_negligible :=
  scaled_pate_patt_double_score_approximation_negligible_of_share_bridge_inputs
    b.pate_bridge b.patt_bridge hfinite henvelope hl1

/--
PATE approximation negligibility at ordinary and scaled rates from share
bridges.
-/
theorem pate_double_score_approximation_negligible_and_scaled_negligible_of_share_bridges
    (ordinary : PATEDoubleScoreShareConvergenceBridge)
    (scaled : ScaledPATEDoubleScoreShareConvergenceBridge)
    (hordinaryFinite : ordinary.eventual_finite_conditions)
    (hordinaryEnvelope : ordinary.envelope_convergence)
    (hordinaryL1 : ordinary.l1_double_score_share_convergence)
    (hscaledFinite : scaled.eventual_finite_conditions)
    (hscaledEnvelope : scaled.envelope_convergence)
    (hscaledL1 : scaled.scaled_l1_double_score_share_convergence) :
    ordinary.pate_double_score_approximation_negligible ∧
      scaled.scaled_pate_double_score_approximation_negligible :=
  ⟨pate_double_score_approximation_negligible_of_share_bridge
      ordinary hordinaryFinite hordinaryEnvelope hordinaryL1,
    scaled_pate_double_score_approximation_negligible_of_share_bridge
      scaled hscaledFinite hscaledEnvelope hscaledL1⟩

/--
PATT approximation negligibility at ordinary and scaled rates from share
bridges.
-/
theorem patt_double_score_approximation_negligible_and_scaled_negligible_of_share_bridges
    (ordinary : PATTDoubleScoreShareConvergenceBridge)
    (scaled : ScaledPATTDoubleScoreShareConvergenceBridge)
    (hordinaryFinite : ordinary.eventual_finite_conditions)
    (hordinaryEnvelope : ordinary.envelope_convergence)
    (hordinaryL1 : ordinary.l1_double_score_share_convergence)
    (hscaledFinite : scaled.eventual_finite_conditions)
    (hscaledEnvelope : scaled.envelope_convergence)
    (hscaledL1 : scaled.scaled_l1_double_score_share_convergence) :
    ordinary.patt_double_score_approximation_negligible ∧
      scaled.scaled_patt_double_score_approximation_negligible :=
  ⟨patt_double_score_approximation_negligible_of_share_bridge
      ordinary hordinaryFinite hordinaryEnvelope hordinaryL1,
    scaled_patt_double_score_approximation_negligible_of_share_bridge
      scaled hscaledFinite hscaledEnvelope hscaledL1⟩

/--
Paired PATE/PATT approximation negligibility at ordinary and scaled rates from
share bridges.
-/
theorem pate_patt_double_score_approximation_negligible_and_scaled_negligible_of_share_bridges
    (pateOrdinary : PATEDoubleScoreShareConvergenceBridge)
    (pateScaled : ScaledPATEDoubleScoreShareConvergenceBridge)
    (pattOrdinary : PATTDoubleScoreShareConvergenceBridge)
    (pattScaled : ScaledPATTDoubleScoreShareConvergenceBridge)
    (hpateOrdinaryFinite : pateOrdinary.eventual_finite_conditions)
    (hpateOrdinaryEnvelope : pateOrdinary.envelope_convergence)
    (hpateOrdinaryL1 : pateOrdinary.l1_double_score_share_convergence)
    (hpateScaledFinite : pateScaled.eventual_finite_conditions)
    (hpateScaledEnvelope : pateScaled.envelope_convergence)
    (hpateScaledL1 : pateScaled.scaled_l1_double_score_share_convergence)
    (hpattOrdinaryFinite : pattOrdinary.eventual_finite_conditions)
    (hpattOrdinaryEnvelope : pattOrdinary.envelope_convergence)
    (hpattOrdinaryL1 : pattOrdinary.l1_double_score_share_convergence)
    (hpattScaledFinite : pattScaled.eventual_finite_conditions)
    (hpattScaledEnvelope : pattScaled.envelope_convergence)
    (hpattScaledL1 : pattScaled.scaled_l1_double_score_share_convergence) :
    (pateOrdinary.pate_double_score_approximation_negligible ∧
      pateScaled.scaled_pate_double_score_approximation_negligible) ∧
      (pattOrdinary.patt_double_score_approximation_negligible ∧
        pattScaled.scaled_patt_double_score_approximation_negligible) :=
  ⟨pate_double_score_approximation_negligible_and_scaled_negligible_of_share_bridges
      pateOrdinary pateScaled hpateOrdinaryFinite hpateOrdinaryEnvelope
      hpateOrdinaryL1 hpateScaledFinite hpateScaledEnvelope hpateScaledL1,
    patt_double_score_approximation_negligible_and_scaled_negligible_of_share_bridges
      pattOrdinary pattScaled hpattOrdinaryFinite hpattOrdinaryEnvelope
      hpattOrdinaryL1 hpattScaledFinite hpattScaledEnvelope hpattScaledL1⟩

/--
Paired PATE/PATT approximation negligibility at ordinary and scaled rates from
share bridges with paired ordinary/scaled inputs packaged as conjunctions.
-/
theorem pate_patt_double_score_approximation_negligible_and_scaled_negligible_of_share_bridge_inputs
    (pateOrdinary : PATEDoubleScoreShareConvergenceBridge)
    (pateScaled : ScaledPATEDoubleScoreShareConvergenceBridge)
    (pattOrdinary : PATTDoubleScoreShareConvergenceBridge)
    (pattScaled : ScaledPATTDoubleScoreShareConvergenceBridge)
    (hordinaryFinite :
      pateOrdinary.eventual_finite_conditions ∧
        pattOrdinary.eventual_finite_conditions)
    (hordinaryEnvelope :
      pateOrdinary.envelope_convergence ∧
        pattOrdinary.envelope_convergence)
    (hordinaryL1 :
      pateOrdinary.l1_double_score_share_convergence ∧
        pattOrdinary.l1_double_score_share_convergence)
    (hscaledFinite :
      pateScaled.eventual_finite_conditions ∧
        pattScaled.eventual_finite_conditions)
    (hscaledEnvelope :
      pateScaled.envelope_convergence ∧ pattScaled.envelope_convergence)
    (hscaledL1 :
      pateScaled.scaled_l1_double_score_share_convergence ∧
        pattScaled.scaled_l1_double_score_share_convergence) :
    (pateOrdinary.pate_double_score_approximation_negligible ∧
      pateScaled.scaled_pate_double_score_approximation_negligible) ∧
      (pattOrdinary.patt_double_score_approximation_negligible ∧
        pattScaled.scaled_patt_double_score_approximation_negligible) :=
  pate_patt_double_score_approximation_negligible_and_scaled_negligible_of_share_bridges
    pateOrdinary pateScaled pattOrdinary pattScaled hordinaryFinite.1
    hordinaryEnvelope.1 hordinaryL1.1 hscaledFinite.1 hscaledEnvelope.1
    hscaledL1.1 hordinaryFinite.2 hordinaryEnvelope.2 hordinaryL1.2
    hscaledFinite.2 hscaledEnvelope.2 hscaledL1.2

/--
Paired PATE/PATT ordinary and scaled double-score share convergence bridge.
-/
structure PATEPATTOrdinaryScaledDoubleScoreShareConvergenceBridge where
  ordinary_bridge : PATEPATTDoubleScoreShareConvergenceBridge
  scaled_bridge : ScaledPATEPATTDoubleScoreShareConvergenceBridge

/--
Paired PATE/PATT approximation negligibility at ordinary and scaled rates from
a single ordinary/scaled paired share-convergence bridge.
-/
theorem pate_patt_double_score_approximation_negligible_and_scaled_negligible_of_paired_share_bridge
    (b : PATEPATTOrdinaryScaledDoubleScoreShareConvergenceBridge)
    (hordinaryFinite :
      b.ordinary_bridge.pate_bridge.eventual_finite_conditions ∧
        b.ordinary_bridge.patt_bridge.eventual_finite_conditions)
    (hordinaryEnvelope :
      b.ordinary_bridge.pate_bridge.envelope_convergence ∧
        b.ordinary_bridge.patt_bridge.envelope_convergence)
    (hordinaryL1 :
      b.ordinary_bridge.pate_bridge.l1_double_score_share_convergence ∧
        b.ordinary_bridge.patt_bridge.l1_double_score_share_convergence)
    (hscaledFinite :
      b.scaled_bridge.pate_bridge.eventual_finite_conditions ∧
        b.scaled_bridge.patt_bridge.eventual_finite_conditions)
    (hscaledEnvelope :
      b.scaled_bridge.pate_bridge.envelope_convergence ∧
        b.scaled_bridge.patt_bridge.envelope_convergence)
    (hscaledL1 :
      b.scaled_bridge.pate_bridge.scaled_l1_double_score_share_convergence ∧
        b.scaled_bridge.patt_bridge.scaled_l1_double_score_share_convergence) :
    (b.ordinary_bridge.pate_bridge.pate_double_score_approximation_negligible ∧
      b.scaled_bridge.pate_bridge.scaled_pate_double_score_approximation_negligible) ∧
      (b.ordinary_bridge.patt_bridge.patt_double_score_approximation_negligible ∧
        b.scaled_bridge.patt_bridge.scaled_patt_double_score_approximation_negligible) :=
  pate_patt_double_score_approximation_negligible_and_scaled_negligible_of_share_bridge_inputs
    b.ordinary_bridge.pate_bridge b.scaled_bridge.pate_bridge
    b.ordinary_bridge.patt_bridge b.scaled_bridge.patt_bridge hordinaryFinite
    hordinaryEnvelope hordinaryL1 hscaledFinite hscaledEnvelope hscaledL1

end WDSM
end Matching
end StatInference
