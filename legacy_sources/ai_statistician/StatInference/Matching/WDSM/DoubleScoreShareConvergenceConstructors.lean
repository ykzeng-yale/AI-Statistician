import StatInference.Matching.WDSM.DoubleScoreShareConvergenceInterfaces

/-!
# Constructors for double-score share convergence bridges

This module turns the deterministic approximate-balancing convergence theorems
into concrete bridge records.  The remaining stochastic task is exactly the
eventual finite-cell validity, envelope convergence, and L1 double-score share
convergence recorded in the bridge fields.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Unit PropensityCell TreatedProgCell ControlProgCell PATTProgCell : Type*}
  [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
  [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]
variable {l : Filter Index}

/--
Concrete PATE double-score share-convergence bridge from the eventual finite
conditions, envelope convergence, and ordinary L1 share convergence.
-/
noncomputable def pateDoubleScoreShareConvergenceBridge_of_eventually_l1_and_envelopes
    (targetSample treatedSample controlSample : Index -> Finset Unit)
    (cells :
      Index -> Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (targetWeight treatedWeight controlWeight : Index -> Unit -> Real)
    (targetOutcomeT targetOutcomeC treatedOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (treatedValue : Index -> TreatedProgCell -> Real)
    (controlValue : Index -> ControlProgCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (treatedEnvelopeLimit controlEnvelopeLimit : Real) :
    PATEDoubleScoreShareConvergenceBridge where
  eventual_finite_conditions :=
    (∀ᶠ index in l,
      ∀ unit, unit ∈ targetSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells index) ∧
    (∀ᶠ index in l,
      ∀ unit, unit ∈ treatedSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells index) ∧
    (∀ᶠ index in l,
      ∀ unit, unit ∈ controlSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells index) ∧
    (∀ᶠ index in l,
      ∀ cell, cell ∈ cells index ->
        scoreCellMass (targetSample index) (targetWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0) ∧
    (∀ᶠ index in l,
      ∀ cell, cell ∈ cells index ->
        scoreCellMass (treatedSample index) (treatedWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0) ∧
    (∀ᶠ index in l,
      ∀ cell, cell ∈ cells index ->
        scoreCellMass (controlSample index) (controlWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0) ∧
    (∀ᶠ index in l,
      ∀ unit, unit ∈ targetSample index ->
        targetOutcomeT index unit =
          treatedValue index (treatedPrognosticScore index unit)) ∧
    (∀ᶠ index in l,
      ∀ unit, unit ∈ treatedSample index ->
        treatedOutcome index unit =
          treatedValue index (treatedPrognosticScore index unit)) ∧
    (∀ᶠ index in l,
      ∀ unit, unit ∈ targetSample index ->
        targetOutcomeC index unit =
          controlValue index (controlPrognosticScore index unit)) ∧
    (∀ᶠ index in l,
      ∀ unit, unit ∈ controlSample index ->
        controlOutcome index unit =
          controlValue index (controlPrognosticScore index unit)) ∧
    (∀ᶠ index in l,
      ∀ cell, cell ∈ cells index ->
        |treatedCellValueOnPATEDoubleScore (treatedValue index) cell| ≤
          treatedEnvelope index) ∧
    (∀ᶠ index in l,
      ∀ cell, cell ∈ cells index ->
        |controlCellValueOnPATEDoubleScore (controlValue index) cell| ≤
          controlEnvelope index)
  envelope_convergence :=
    Tendsto treatedEnvelope l (nhds treatedEnvelopeLimit) ∧
      Tendsto controlEnvelope l (nhds controlEnvelopeLimit)
  l1_double_score_share_convergence :=
    Tendsto
      (fun index =>
        l1PATEDoubleScoreShareDistance (cells index)
          (targetSample index) (treatedSample index)
          (targetWeight index) (treatedWeight index)
          (propensityScore index) (treatedPrognosticScore index)
          (controlPrognosticScore index))
      l (nhds 0) ∧
    Tendsto
      (fun index =>
        l1PATEDoubleScoreShareDistance (cells index)
          (targetSample index) (controlSample index)
          (targetWeight index) (controlWeight index)
          (propensityScore index) (treatedPrognosticScore index)
          (controlPrognosticScore index))
      l (nhds 0)
  pate_double_score_approximation_negligible :=
    Tendsto
      (fun index =>
        weightedSampleMeanContrast (targetSample index)
          (targetWeight index) (targetOutcomeT index)
          (targetOutcomeC index) -
        twoArmWeightedMeanContrast (treatedSample index)
          (controlSample index) (treatedWeight index)
          (controlWeight index) (treatedOutcome index)
          (controlOutcome index))
      l (nhds 0)
  bridge := by
    intro hfinite henvelope hl1
    rcases hfinite with
      ⟨hcoverTarget, hcoverTreated, hcoverControl, hmassTarget,
        hmassTreated, hmassControl, hscoreMeasTargetT,
        hscoreMeasTreated, hscoreMeasTargetC, hscoreMeasControl,
        htreated_bound, hcontrol_bound⟩
    exact
      tendsto_pateDoubleScoreApprox_error_zero_of_eventually_l1_and_envelopes
        targetSample treatedSample controlSample cells targetWeight
        treatedWeight controlWeight targetOutcomeT targetOutcomeC
        treatedOutcome controlOutcome propensityScore treatedPrognosticScore
        controlPrognosticScore treatedValue controlValue treatedEnvelope
        controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit hcoverTarget
        hcoverTreated hcoverControl hmassTarget hmassTreated hmassControl
        hscoreMeasTargetT hscoreMeasTreated hscoreMeasTargetC
        hscoreMeasControl htreated_bound hcontrol_bound henvelope.1
        henvelope.2 hl1.1 hl1.2

/-- Scaled PATE double-score share-convergence bridge constructor. -/
noncomputable def scaledPATEDoubleScoreShareConvergenceBridge_of_eventually_scaled_l1_and_envelopes
    (scale : Index -> Real)
    (targetSample treatedSample controlSample : Index -> Finset Unit)
    (cells :
      Index -> Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (targetWeight treatedWeight controlWeight : Index -> Unit -> Real)
    (targetOutcomeT targetOutcomeC treatedOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (treatedValue : Index -> TreatedProgCell -> Real)
    (controlValue : Index -> ControlProgCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (treatedEnvelopeLimit controlEnvelopeLimit : Real) :
    ScaledPATEDoubleScoreShareConvergenceBridge where
  eventual_finite_conditions :=
    (∀ᶠ index in l, 0 ≤ scale index) ∧
    (∀ᶠ index in l,
      ∀ unit, unit ∈ targetSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells index) ∧
    (∀ᶠ index in l,
      ∀ unit, unit ∈ treatedSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells index) ∧
    (∀ᶠ index in l,
      ∀ unit, unit ∈ controlSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells index) ∧
    (∀ᶠ index in l,
      ∀ cell, cell ∈ cells index ->
        scoreCellMass (targetSample index) (targetWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0) ∧
    (∀ᶠ index in l,
      ∀ cell, cell ∈ cells index ->
        scoreCellMass (treatedSample index) (treatedWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0) ∧
    (∀ᶠ index in l,
      ∀ cell, cell ∈ cells index ->
        scoreCellMass (controlSample index) (controlWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0) ∧
    (∀ᶠ index in l,
      ∀ unit, unit ∈ targetSample index ->
        targetOutcomeT index unit =
          treatedValue index (treatedPrognosticScore index unit)) ∧
    (∀ᶠ index in l,
      ∀ unit, unit ∈ treatedSample index ->
        treatedOutcome index unit =
          treatedValue index (treatedPrognosticScore index unit)) ∧
    (∀ᶠ index in l,
      ∀ unit, unit ∈ targetSample index ->
        targetOutcomeC index unit =
          controlValue index (controlPrognosticScore index unit)) ∧
    (∀ᶠ index in l,
      ∀ unit, unit ∈ controlSample index ->
        controlOutcome index unit =
          controlValue index (controlPrognosticScore index unit)) ∧
    (∀ᶠ index in l,
      ∀ cell, cell ∈ cells index ->
        |treatedCellValueOnPATEDoubleScore (treatedValue index) cell| ≤
          treatedEnvelope index) ∧
    (∀ᶠ index in l,
      ∀ cell, cell ∈ cells index ->
        |controlCellValueOnPATEDoubleScore (controlValue index) cell| ≤
          controlEnvelope index)
  envelope_convergence :=
    Tendsto treatedEnvelope l (nhds treatedEnvelopeLimit) ∧
      Tendsto controlEnvelope l (nhds controlEnvelopeLimit)
  scaled_l1_double_score_share_convergence :=
    Tendsto
      (fun index =>
        scale index *
          l1PATEDoubleScoreShareDistance (cells index)
            (targetSample index) (treatedSample index)
            (targetWeight index) (treatedWeight index)
            (propensityScore index) (treatedPrognosticScore index)
            (controlPrognosticScore index))
      l (nhds 0) ∧
    Tendsto
      (fun index =>
        scale index *
          l1PATEDoubleScoreShareDistance (cells index)
            (targetSample index) (controlSample index)
            (targetWeight index) (controlWeight index)
            (propensityScore index) (treatedPrognosticScore index)
            (controlPrognosticScore index))
      l (nhds 0)
  scaled_pate_double_score_approximation_negligible :=
    Tendsto
      (fun index =>
        scale index *
          (weightedSampleMeanContrast (targetSample index)
            (targetWeight index) (targetOutcomeT index)
            (targetOutcomeC index) -
          twoArmWeightedMeanContrast (treatedSample index)
            (controlSample index) (treatedWeight index)
            (controlWeight index) (treatedOutcome index)
            (controlOutcome index)))
      l (nhds 0)
  bridge := by
    intro hfinite henvelope hl1
    rcases hfinite with
      ⟨hscale_nonneg, hcoverTarget, hcoverTreated, hcoverControl,
        hmassTarget, hmassTreated, hmassControl, hscoreMeasTargetT,
        hscoreMeasTreated, hscoreMeasTargetC, hscoreMeasControl,
        htreated_bound, hcontrol_bound⟩
    exact
      tendsto_scaled_pateDoubleScoreApprox_error_zero_of_eventually_scaled_l1_and_envelopes
        scale targetSample treatedSample controlSample cells targetWeight
        treatedWeight controlWeight targetOutcomeT targetOutcomeC
        treatedOutcome controlOutcome propensityScore treatedPrognosticScore
        controlPrognosticScore treatedValue controlValue treatedEnvelope
        controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit
        hscale_nonneg hcoverTarget hcoverTreated hcoverControl hmassTarget
        hmassTreated hmassControl hscoreMeasTargetT hscoreMeasTreated
        hscoreMeasTargetC hscoreMeasControl htreated_bound hcontrol_bound
        henvelope.1 henvelope.2 hl1.1 hl1.2

/--
Concrete PATT double-score share-convergence bridge from the eventual finite
conditions, envelope convergence, and ordinary L1 share convergence.
-/
noncomputable def pattDoubleScoreShareConvergenceBridge_of_eventually_l1_and_envelope
    (targetSample controlSample : Index -> Finset Unit)
    (cells : Index -> Finset (PropensityCell × PATTProgCell))
    (targetWeight controlWeight : Index -> Unit -> Real)
    (treatedTargetOutcome targetControlOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (controlValue : Index -> PATTProgCell -> Real)
    (controlEnvelope : Index -> Real)
    (controlEnvelopeLimit : Real) :
    PATTDoubleScoreShareConvergenceBridge where
  eventual_finite_conditions :=
    (∀ᶠ index in l,
      ∀ unit, unit ∈ targetSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells index) ∧
    (∀ᶠ index in l,
      ∀ unit, unit ∈ controlSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells index) ∧
    (∀ᶠ index in l,
      ∀ cell, cell ∈ cells index ->
        scoreCellMass (targetSample index) (targetWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0) ∧
    (∀ᶠ index in l,
      ∀ cell, cell ∈ cells index ->
        scoreCellMass (controlSample index) (controlWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0) ∧
    (∀ᶠ index in l,
      ∀ unit, unit ∈ targetSample index ->
        targetControlOutcome index unit =
          controlValue index (controlPrognosticScore index unit)) ∧
    (∀ᶠ index in l,
      ∀ unit, unit ∈ controlSample index ->
        controlOutcome index unit =
          controlValue index (controlPrognosticScore index unit)) ∧
    (∀ᶠ index in l,
      ∀ cell, cell ∈ cells index ->
        |controlCellValueOnPATTDoubleScore (controlValue index) cell| ≤
          controlEnvelope index)
  envelope_convergence :=
    Tendsto controlEnvelope l (nhds controlEnvelopeLimit)
  l1_double_score_share_convergence :=
    Tendsto
      (fun index =>
        l1PATTDoubleScoreShareDistance (cells index)
          (targetSample index) (controlSample index)
          (targetWeight index) (controlWeight index)
          (propensityScore index) (controlPrognosticScore index))
      l (nhds 0)
  patt_double_score_approximation_negligible :=
    Tendsto
      (fun index =>
        weightedSampleMeanContrast (targetSample index)
          (targetWeight index) (treatedTargetOutcome index)
          (targetControlOutcome index) -
        pattWeightedMeanContrast (targetSample index) (controlSample index)
          (targetWeight index) (controlWeight index)
          (treatedTargetOutcome index) (controlOutcome index))
      l (nhds 0)
  bridge := by
    intro hfinite henvelope hl1
    rcases hfinite with
      ⟨hcoverTarget, hcoverControl, hmassTarget, hmassControl,
        hscoreMeasTargetC, hscoreMeasControl, hcontrol_bound⟩
    exact
      tendsto_pattDoubleScoreApprox_error_zero_of_eventually_l1_and_envelope
        targetSample controlSample cells targetWeight controlWeight
        treatedTargetOutcome targetControlOutcome controlOutcome
        propensityScore controlPrognosticScore controlValue controlEnvelope
        controlEnvelopeLimit hcoverTarget hcoverControl hmassTarget
        hmassControl hscoreMeasTargetC hscoreMeasControl hcontrol_bound
        henvelope hl1

/-- Scaled PATT double-score share-convergence bridge constructor. -/
noncomputable def scaledPATTDoubleScoreShareConvergenceBridge_of_eventually_scaled_l1_and_envelope
    (scale : Index -> Real)
    (targetSample controlSample : Index -> Finset Unit)
    (cells : Index -> Finset (PropensityCell × PATTProgCell))
    (targetWeight controlWeight : Index -> Unit -> Real)
    (treatedTargetOutcome targetControlOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (controlValue : Index -> PATTProgCell -> Real)
    (controlEnvelope : Index -> Real)
    (controlEnvelopeLimit : Real) :
    ScaledPATTDoubleScoreShareConvergenceBridge where
  eventual_finite_conditions :=
    (∀ᶠ index in l, 0 ≤ scale index) ∧
    (∀ᶠ index in l,
      ∀ unit, unit ∈ targetSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells index) ∧
    (∀ᶠ index in l,
      ∀ unit, unit ∈ controlSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells index) ∧
    (∀ᶠ index in l,
      ∀ cell, cell ∈ cells index ->
        scoreCellMass (targetSample index) (targetWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0) ∧
    (∀ᶠ index in l,
      ∀ cell, cell ∈ cells index ->
        scoreCellMass (controlSample index) (controlWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0) ∧
    (∀ᶠ index in l,
      ∀ unit, unit ∈ targetSample index ->
        targetControlOutcome index unit =
          controlValue index (controlPrognosticScore index unit)) ∧
    (∀ᶠ index in l,
      ∀ unit, unit ∈ controlSample index ->
        controlOutcome index unit =
          controlValue index (controlPrognosticScore index unit)) ∧
    (∀ᶠ index in l,
      ∀ cell, cell ∈ cells index ->
        |controlCellValueOnPATTDoubleScore (controlValue index) cell| ≤
          controlEnvelope index)
  envelope_convergence :=
    Tendsto controlEnvelope l (nhds controlEnvelopeLimit)
  scaled_l1_double_score_share_convergence :=
    Tendsto
      (fun index =>
        scale index *
          l1PATTDoubleScoreShareDistance (cells index)
            (targetSample index) (controlSample index)
            (targetWeight index) (controlWeight index)
            (propensityScore index) (controlPrognosticScore index))
      l (nhds 0)
  scaled_patt_double_score_approximation_negligible :=
    Tendsto
      (fun index =>
        scale index *
          (weightedSampleMeanContrast (targetSample index)
            (targetWeight index) (treatedTargetOutcome index)
            (targetControlOutcome index) -
          pattWeightedMeanContrast (targetSample index) (controlSample index)
            (targetWeight index) (controlWeight index)
            (treatedTargetOutcome index) (controlOutcome index)))
      l (nhds 0)
  bridge := by
    intro hfinite henvelope hl1
    rcases hfinite with
      ⟨hscale_nonneg, hcoverTarget, hcoverControl, hmassTarget, hmassControl,
        hscoreMeasTargetC, hscoreMeasControl, hcontrol_bound⟩
    exact
      tendsto_scaled_pattDoubleScoreApprox_error_zero_of_eventually_scaled_l1_and_envelope
        scale targetSample controlSample cells targetWeight controlWeight
        treatedTargetOutcome targetControlOutcome controlOutcome
        propensityScore controlPrognosticScore controlValue controlEnvelope
        controlEnvelopeLimit hscale_nonneg hcoverTarget hcoverControl
        hmassTarget hmassControl hscoreMeasTargetC hscoreMeasControl
        hcontrol_bound henvelope hl1

/-- Build the paired ordinary PATE/PATT bridge from its component bridges. -/
def patePATTDoubleScoreShareConvergenceBridge_of_bridges
    (pate : PATEDoubleScoreShareConvergenceBridge)
    (patt : PATTDoubleScoreShareConvergenceBridge) :
    PATEPATTDoubleScoreShareConvergenceBridge where
  pate_bridge := pate
  patt_bridge := patt

/-- Build the paired scaled PATE/PATT bridge from its component bridges. -/
def scaledPATEPATTDoubleScoreShareConvergenceBridge_of_bridges
    (pate : ScaledPATEDoubleScoreShareConvergenceBridge)
    (patt : ScaledPATTDoubleScoreShareConvergenceBridge) :
    ScaledPATEPATTDoubleScoreShareConvergenceBridge where
  pate_bridge := pate
  patt_bridge := patt

/--
Build the ordinary/scaled paired PATE/PATT bridge from paired ordinary and
scaled bridges.
-/
def patePATTOrdinaryScaledDoubleScoreShareConvergenceBridge_of_paired_bridges
    (ordinary : PATEPATTDoubleScoreShareConvergenceBridge)
    (scaled : ScaledPATEPATTDoubleScoreShareConvergenceBridge) :
    PATEPATTOrdinaryScaledDoubleScoreShareConvergenceBridge where
  ordinary_bridge := ordinary
  scaled_bridge := scaled

/--
Build the ordinary/scaled paired PATE/PATT bridge directly from the four
component ordinary/scaled PATE/PATT bridges.
-/
def patePATTOrdinaryScaledDoubleScoreShareConvergenceBridge_of_bridges
    (pateOrdinary : PATEDoubleScoreShareConvergenceBridge)
    (pateScaled : ScaledPATEDoubleScoreShareConvergenceBridge)
    (pattOrdinary : PATTDoubleScoreShareConvergenceBridge)
    (pattScaled : ScaledPATTDoubleScoreShareConvergenceBridge) :
    PATEPATTOrdinaryScaledDoubleScoreShareConvergenceBridge :=
  patePATTOrdinaryScaledDoubleScoreShareConvergenceBridge_of_paired_bridges
    (patePATTDoubleScoreShareConvergenceBridge_of_bridges
      pateOrdinary pattOrdinary)
    (scaledPATEPATTDoubleScoreShareConvergenceBridge_of_bridges
      pateScaled pattScaled)

end WDSM
end Matching
end StatInference
