import StatInference.Matching.WDSM.FiniteCellIndicatorApproximationConvergence
import StatInference.Matching.WDSM.IndicatorSumConvergenceInterfaces

/-!
# Base indicator-bridge constructors from eventual assumptions

This module provides concrete bridge constructors that package eventual score-cell
coverage/positivity/measurability assumptions together with weighted indicator
sum convergence into the generic `*DoubleScoreIndicatorSumConvergenceBridge`
interfaces.  They are used by the finite-cell envelope-input module to expose a
single concrete bridge shape for downstream WDSM adapters.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Unit : Type*} {l : Filter Index}
  {PropensityCell TreatedProgCell ControlProgCell PATTProgCell : Type*}
  [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
  [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]

/--
Base PATE bridge from eventual conditions and indicator LLN assumptions.
-/
def pateDoubleScoreIndicatorSumConvergenceBridgeOfEventuallyIndicator
    (targetSample treatedSample controlSample : Index -> Finset Unit)
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (targetWeight treatedWeight controlWeight : Index -> Unit -> Real)
    (targetOutcomeT targetOutcomeC treatedOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (treatedValue : Index -> TreatedProgCell -> Real)
    (controlValue : Index -> ControlProgCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (treatedEnvelopeLimit controlEnvelopeLimit : Real)
    (massLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    PATEDoubleScoreIndicatorSumConvergenceBridge :=
  by
    let hfinite : Prop :=
      (∀ index unit, unit ∈ targetSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index) (controlPrognosticScore index) unit ∈ cells) ∧
      (∀ index unit, unit ∈ treatedSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index) (controlPrognosticScore index) unit ∈ cells) ∧
      (∀ index unit, unit ∈ controlSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index) (controlPrognosticScore index) unit ∈ cells) ∧
      (∀ index cell, cell ∈ cells ->
        scoreCellMass (targetSample index) (targetWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index) (controlPrognosticScore index)) cell ≠ 0) ∧
      (∀ index cell, cell ∈ cells ->
        scoreCellMass (treatedSample index) (treatedWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index) (controlPrognosticScore index)) cell ≠ 0) ∧
      (∀ index cell, cell ∈ cells ->
        scoreCellMass (controlSample index) (controlWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index) (controlPrognosticScore index)) cell ≠ 0) ∧
      (∀ index unit, unit ∈ targetSample index ->
        targetOutcomeT index unit =
          treatedValue index (treatedPrognosticScore index unit)) ∧
      (∀ index unit, unit ∈ treatedSample index ->
        treatedOutcome index unit =
          treatedValue index (treatedPrognosticScore index unit)) ∧
      (∀ index unit, unit ∈ targetSample index ->
        targetOutcomeC index unit =
          controlValue index (controlPrognosticScore index unit)) ∧
      (∀ index unit, unit ∈ controlSample index ->
        controlOutcome index unit =
          controlValue index (controlPrognosticScore index unit)) ∧
      (∀ index cell, cell ∈ cells ->
        |treatedCellValueOnPATEDoubleScore (treatedValue index) cell| ≤
          treatedEnvelope index) ∧
      (∀ index cell, cell ∈ cells ->
        |controlCellValueOnPATEDoubleScore (controlValue index) cell| ≤
          controlEnvelope index)
    let henv : Prop :=
      Tendsto treatedEnvelope l (nhds treatedEnvelopeLimit) ∧
      Tendsto controlEnvelope l (nhds controlEnvelopeLimit)
    let hlln : Prop :=
      (∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (targetSample index) (targetWeight index)
              (scoreCellIndicator
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (massLimit cell))) ∧
      (∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (treatedSample index) (treatedWeight index)
              (scoreCellIndicator
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (massLimit cell))) ∧
      (∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (controlSample index) (controlWeight index)
              (scoreCellIndicator
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (massLimit cell)))
    let hnegligible : Prop :=
        Tendsto
          (fun index =>
            weightedSampleMeanContrast (targetSample index)
              (targetWeight index) (targetOutcomeT index) (targetOutcomeC index) -
            twoArmWeightedMeanContrast (treatedSample index)
              (controlSample index) (treatedWeight index) (controlWeight index)
              (treatedOutcome index) (controlOutcome index))
          l (nhds 0)
    exact
      {
        eventual_finite_conditions := hfinite,
        envelope_convergence := henv,
        weighted_indicator_sum_lln := hlln,
        pate_double_score_approximation_negligible := hnegligible,
        bridge := by
          intro hfinite' henv' hlln'
          rcases hfinite' with
            ⟨hcoverTarget, hcoverTreated, hcoverControl, hmassTarget, hmassTreated,
              hmassControl, hscoreMeasTargetT, hscoreMeasTreated, hscoreMeasTargetC,
              hscoreMeasControl, htreated_bound, hcontrol_bound⟩
          rcases henv' with ⟨htreatedEnvelope, hcontrolEnvelope⟩
          rcases hlln' with ⟨hindicatorTarget, hindicatorTreated, hindicatorControl⟩
          exact
            tendsto_pateDoubleScoreApprox_error_zero_of_indicator_and_envelopes
              targetSample treatedSample controlSample cells targetWeight
              treatedWeight controlWeight targetOutcomeT targetOutcomeC
              treatedOutcome controlOutcome propensityScore
              treatedPrognosticScore controlPrognosticScore treatedValue
              controlValue treatedEnvelope controlEnvelope treatedEnvelopeLimit
              controlEnvelopeLimit massLimit hcoverTarget hcoverTreated
              hcoverControl hmassTarget hmassTreated hmassControl
              hindicatorTarget hindicatorTreated hindicatorControl htotalLimit
              hscoreMeasTargetT hscoreMeasTreated hscoreMeasTargetC
              hscoreMeasControl htreated_bound hcontrol_bound htreatedEnvelope
              hcontrolEnvelope
      }

/--
Scaled PATE bridge from eventual conditions and indicator LLN/CLT assumptions.
-/
def scaledPATEDoubleScoreIndicatorSumConvergenceBridgeOfEventuallyIndicator
    (scale : Index -> Real)
    (targetSample treatedSample controlSample : Index -> Finset Unit)
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (targetWeight treatedWeight controlWeight : Index -> Unit -> Real)
    (targetOutcomeT targetOutcomeC treatedOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (treatedValue : Index -> TreatedProgCell -> Real)
    (controlValue : Index -> ControlProgCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (treatedEnvelopeLimit controlEnvelopeLimit : Real)
    (massLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    ScaledPATEDoubleScoreIndicatorSumConvergenceBridge :=
  by
    let hfinite : Prop :=
      (∀ index, 0 ≤ scale index) ∧
      (∀ index unit, unit ∈ targetSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index) (controlPrognosticScore index) unit ∈ cells) ∧
      (∀ index unit, unit ∈ treatedSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index) (controlPrognosticScore index) unit ∈ cells) ∧
      (∀ index unit, unit ∈ controlSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index) (controlPrognosticScore index) unit ∈ cells) ∧
      (∀ index cell, cell ∈ cells ->
        scoreCellMass (targetSample index) (targetWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index) (controlPrognosticScore index)) cell ≠ 0) ∧
      (∀ index cell, cell ∈ cells ->
        scoreCellMass (treatedSample index) (treatedWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index) (controlPrognosticScore index)) cell ≠ 0) ∧
      (∀ index cell, cell ∈ cells ->
        scoreCellMass (controlSample index) (controlWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index) (controlPrognosticScore index)) cell ≠ 0) ∧
      (∀ index unit, unit ∈ targetSample index ->
        targetOutcomeT index unit =
          treatedValue index (treatedPrognosticScore index unit)) ∧
      (∀ index unit, unit ∈ treatedSample index ->
        treatedOutcome index unit =
          treatedValue index (treatedPrognosticScore index unit)) ∧
      (∀ index unit, unit ∈ targetSample index ->
        targetOutcomeC index unit =
          controlValue index (controlPrognosticScore index unit)) ∧
      (∀ index unit, unit ∈ controlSample index ->
        controlOutcome index unit =
          controlValue index (controlPrognosticScore index unit)) ∧
      (∀ index cell, cell ∈ cells ->
        |treatedCellValueOnPATEDoubleScore (treatedValue index) cell| ≤
          treatedEnvelope index) ∧
      (∀ index cell, cell ∈ cells ->
        |controlCellValueOnPATEDoubleScore (controlValue index) cell| ≤
          controlEnvelope index)
    let henv : Prop :=
      Tendsto treatedEnvelope l (nhds treatedEnvelopeLimit) ∧
      Tendsto controlEnvelope l (nhds controlEnvelopeLimit)
    let hlln : Prop :=
      (∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (targetSample index) (targetWeight index)
              (scoreCellIndicator
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (massLimit cell))) ∧
      (∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (treatedSample index) (treatedWeight index)
              (scoreCellIndicator
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (massLimit cell))) ∧
      (∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (controlSample index) (controlWeight index)
              (scoreCellIndicator
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (massLimit cell)))
    let hscaled : Prop :=
      (∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (targetSample index) (targetWeight index)
                (scoreCellIndicator
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell) -
                weightedSampleSum (treatedSample index) (treatedWeight index)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index)) cell)))
          l (nhds 0)) ∧
      (∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (targetSample index) (targetWeight index)
                (scoreCellIndicator
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell) -
                weightedSampleSum (controlSample index) (controlWeight index)
                  (scoreCellIndicator
                    (pateDoubleScore (propensityScore index)
                      (treatedPrognosticScore index)
                      (controlPrognosticScore index)) cell)))
          l (nhds 0))
    let hnegligible : Prop :=
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleMeanContrast (targetSample index)
                (targetWeight index) (targetOutcomeT index) (targetOutcomeC index) -
              twoArmWeightedMeanContrast (treatedSample index)
                (controlSample index) (treatedWeight index) (controlWeight index)
                (treatedOutcome index) (controlOutcome index)))
          l (nhds 0)
    exact
      {
        eventual_finite_conditions := hfinite,
        envelope_convergence := henv,
        weighted_indicator_sum_lln := hlln,
        scaled_weighted_indicator_sum_difference_clt := hscaled,
        scaled_pate_double_score_approximation_negligible := hnegligible,
        bridge := by
          intro hfinite' henv' hlln' hscaled'
          rcases hfinite' with
            ⟨hscale_nonneg, hcoverTarget, hcoverTreated, hcoverControl,
              hmassTarget, hmassTreated, hmassControl, hscoreMeasTargetT,
              hscoreMeasTreated, hscoreMeasTargetC, hscoreMeasControl,
              htreated_bound, hcontrol_bound⟩
          rcases henv' with ⟨htreatedEnvelope, hcontrolEnvelope⟩
          rcases hlln' with ⟨hindicatorTarget, hindicatorTreated, hindicatorControl⟩
          rcases hscaled' with ⟨hscaledTreated, hscaledControl⟩
          exact
            tendsto_scaled_pateDoubleScoreApprox_error_zero_of_indicator_and_envelopes
              scale targetSample treatedSample controlSample cells targetWeight
              treatedWeight controlWeight targetOutcomeT targetOutcomeC
              treatedOutcome controlOutcome propensityScore
              treatedPrognosticScore controlPrognosticScore treatedValue
              controlValue treatedEnvelope controlEnvelope treatedEnvelopeLimit
              controlEnvelopeLimit massLimit hscale_nonneg hcoverTarget
              hcoverTreated hcoverControl hmassTarget hmassTreated hmassControl
              hindicatorTarget hindicatorTreated hindicatorControl
              hscaledTreated hscaledControl htotalLimit hscoreMeasTargetT
              hscoreMeasTreated hscoreMeasTargetC hscoreMeasControl
              htreated_bound hcontrol_bound htreatedEnvelope hcontrolEnvelope
      }

/--
Base PATT bridge from eventual conditions and indicator LLN assumptions.
-/
def pattDoubleScoreIndicatorSumConvergenceBridgeOfEventuallyIndicator
    (targetSample controlSample : Index -> Finset Unit)
    (cells : Finset (PropensityCell × PATTProgCell))
    (targetWeight controlWeight : Index -> Unit -> Real)
    (treatedTargetOutcome targetControlOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (controlValue : Index -> PATTProgCell -> Real)
    (controlEnvelope : Index -> Real)
    (controlEnvelopeLimit : Real)
    (massLimit : (PropensityCell × PATTProgCell) -> Real)
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    PATTDoubleScoreIndicatorSumConvergenceBridge :=
  by
    let hfinite : Prop :=
      (∀ index unit, unit ∈ targetSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells) ∧
      (∀ index unit, unit ∈ controlSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells) ∧
      (∀ index cell, cell ∈ cells ->
        scoreCellMass (targetSample index) (targetWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0) ∧
      (∀ index cell, cell ∈ cells ->
        scoreCellMass (controlSample index) (controlWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0) ∧
      (∀ index unit, unit ∈ targetSample index ->
        targetControlOutcome index unit =
          controlValue index (controlPrognosticScore index unit)) ∧
      (∀ index unit, unit ∈ controlSample index ->
        controlOutcome index unit =
          controlValue index (controlPrognosticScore index unit)) ∧
        (∀ index cell, cell ∈ cells ->
        |controlCellValueOnPATTDoubleScore (controlValue index) cell| ≤
          controlEnvelope index)
    let henv : Prop :=
      Tendsto controlEnvelope l (nhds controlEnvelopeLimit)
    let hlln : Prop :=
      (∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (targetSample index) (targetWeight index)
              (scoreCellIndicator
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (massLimit cell))) ∧
      (∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (controlSample index) (controlWeight index)
            (scoreCellIndicator
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell))
          l (nhds (massLimit cell)))
    let hnegligible : Prop :=
        Tendsto
          (fun index =>
            weightedSampleMeanContrast (targetSample index)
              (targetWeight index) (treatedTargetOutcome index)
              (targetControlOutcome index) -
            pattWeightedMeanContrast (targetSample index) (controlSample index)
              (targetWeight index) (controlWeight index)
              (treatedTargetOutcome index) (controlOutcome index))
          l (nhds 0)
    exact
      {
        eventual_finite_conditions := hfinite,
        envelope_convergence := henv,
        weighted_indicator_sum_lln := hlln,
        patt_double_score_approximation_negligible := hnegligible,
        bridge := by
          intro hfinite' henv' hlln'
          rcases hfinite' with
            ⟨hcoverTarget, hcoverControl, hmassTarget, hmassControl,
              hscoreMeasTargetC, hscoreMeasControl, hcontrol_bound⟩
          rcases hlln' with ⟨hindicatorTarget, hindicatorControl⟩
          exact
            tendsto_pattDoubleScoreApprox_error_zero_of_indicator_and_envelope
              targetSample controlSample cells targetWeight controlWeight
              treatedTargetOutcome targetControlOutcome controlOutcome
              propensityScore controlPrognosticScore controlValue
              controlEnvelope controlEnvelopeLimit massLimit hcoverTarget hcoverControl
              hmassTarget hmassControl hindicatorTarget hindicatorControl
              htotalLimit hscoreMeasTargetC hscoreMeasControl hcontrol_bound
              henv'
      }

/--
Scaled PATT bridge from eventual conditions and indicator LLN/CLT assumptions.
-/
def scaledPATTDoubleScoreIndicatorSumConvergenceBridgeOfEventuallyIndicator
    (scale : Index -> Real)
    (targetSample controlSample : Index -> Finset Unit)
    (cells : Finset (PropensityCell × PATTProgCell))
    (targetWeight controlWeight : Index -> Unit -> Real)
    (treatedTargetOutcome targetControlOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (controlValue : Index -> PATTProgCell -> Real)
    (controlEnvelope : Index -> Real)
    (controlEnvelopeLimit : Real)
    (massLimit : (PropensityCell × PATTProgCell) -> Real)
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    ScaledPATTDoubleScoreIndicatorSumConvergenceBridge :=
  by
    let hfinite : Prop :=
      (∀ index, 0 ≤ scale index) ∧
      (∀ index unit, unit ∈ targetSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells) ∧
      (∀ index unit, unit ∈ controlSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells) ∧
      (∀ index cell, cell ∈ cells ->
        scoreCellMass (targetSample index) (targetWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0) ∧
      (∀ index cell, cell ∈ cells ->
        scoreCellMass (controlSample index) (controlWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0) ∧
      (∀ index unit, unit ∈ targetSample index ->
        targetControlOutcome index unit =
          controlValue index (controlPrognosticScore index unit)) ∧
      (∀ index unit, unit ∈ controlSample index ->
        controlOutcome index unit =
          controlValue index (controlPrognosticScore index unit)) ∧
      (∀ index cell, cell ∈ cells ->
        |controlCellValueOnPATTDoubleScore (controlValue index) cell| ≤
          controlEnvelope index)
    let henv : Prop :=
      Tendsto controlEnvelope l (nhds controlEnvelopeLimit)
    let hlln : Prop :=
      (∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (targetSample index) (targetWeight index)
              (scoreCellIndicator
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (massLimit cell))) ∧
      (∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            weightedSampleSum (controlSample index) (controlWeight index)
              (scoreCellIndicator
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell))
          l (nhds (massLimit cell)))
    let hscaled : Prop :=
      (∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (weightedSampleSum (targetSample index) (targetWeight index)
                (scoreCellIndicator
                  (pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index)) cell) -
                weightedSampleSum (controlSample index) (controlWeight index)
                  (scoreCellIndicator
                    (pattDoubleScore (propensityScore index)
                      (controlPrognosticScore index)) cell)))
          l (nhds 0))
    let hnegligible : Prop :=
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
    exact
      {
        eventual_finite_conditions := hfinite,
        envelope_convergence := henv,
        weighted_indicator_sum_lln := hlln,
        scaled_weighted_indicator_sum_difference_clt := hscaled,
        scaled_patt_double_score_approximation_negligible := hnegligible,
        bridge := by
          intro hfinite' henv' hlln' hscaled'
          rcases hfinite' with
            ⟨hscale_nonneg, hcoverTarget, hcoverControl, hmassTarget, hmassControl,
              hscoreMeasTargetC, hscoreMeasControl, hcontrol_bound⟩
          rcases hlln' with ⟨hindicatorTarget, hindicatorControl⟩
          let hscaledControl := hscaled'
          exact
            tendsto_scaled_pattDoubleScoreApprox_error_zero_of_indicator_and_envelope
              scale targetSample controlSample cells targetWeight controlWeight
              treatedTargetOutcome targetControlOutcome controlOutcome
              propensityScore controlPrognosticScore controlValue
              controlEnvelope controlEnvelopeLimit massLimit hscale_nonneg hcoverTarget
              hcoverControl hmassTarget hmassControl hindicatorTarget
              hindicatorControl hscaledControl htotalLimit hscoreMeasTargetC
              hscoreMeasControl hcontrol_bound henv'
      }

/--
Base PATE bridge for a finite double-score alphabet, with the cell set
specialized to `Finset.univ`.
-/
def pateDoubleScoreIndicatorSumConvergenceBridgeOfEventuallyIndicator_fintype
    [Fintype PropensityCell] [Fintype TreatedProgCell]
    [Fintype ControlProgCell]
    (targetSample treatedSample controlSample : Index -> Finset Unit)
    (targetWeight treatedWeight controlWeight : Index -> Unit -> Real)
    (targetOutcomeT targetOutcomeC treatedOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (treatedValue : Index -> TreatedProgCell -> Real)
    (controlValue : Index -> ControlProgCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (treatedEnvelopeLimit controlEnvelopeLimit : Real)
    (massLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (htotalLimit :
      (∑ cell ∈
        (Finset.univ :
          Finset ((PropensityCell × TreatedProgCell) × ControlProgCell)),
        massLimit cell) ≠ 0) :
    PATEDoubleScoreIndicatorSumConvergenceBridge :=
  pateDoubleScoreIndicatorSumConvergenceBridgeOfEventuallyIndicator
    (l := l)
    targetSample treatedSample controlSample
    (Finset.univ :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    targetWeight treatedWeight controlWeight targetOutcomeT targetOutcomeC
    treatedOutcome controlOutcome propensityScore treatedPrognosticScore
    controlPrognosticScore treatedValue controlValue treatedEnvelope
    controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit massLimit
    htotalLimit

/--
Scaled PATE bridge for a finite double-score alphabet, with the cell set
specialized to `Finset.univ`.
-/
def scaledPATEDoubleScoreIndicatorSumConvergenceBridgeOfEventuallyIndicator_fintype
    [Fintype PropensityCell] [Fintype TreatedProgCell]
    [Fintype ControlProgCell]
    (scale : Index -> Real)
    (targetSample treatedSample controlSample : Index -> Finset Unit)
    (targetWeight treatedWeight controlWeight : Index -> Unit -> Real)
    (targetOutcomeT targetOutcomeC treatedOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (treatedValue : Index -> TreatedProgCell -> Real)
    (controlValue : Index -> ControlProgCell -> Real)
    (treatedEnvelope controlEnvelope : Index -> Real)
    (treatedEnvelopeLimit controlEnvelopeLimit : Real)
    (massLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (htotalLimit :
      (∑ cell ∈
        (Finset.univ :
          Finset ((PropensityCell × TreatedProgCell) × ControlProgCell)),
        massLimit cell) ≠ 0) :
    ScaledPATEDoubleScoreIndicatorSumConvergenceBridge :=
  scaledPATEDoubleScoreIndicatorSumConvergenceBridgeOfEventuallyIndicator
    (l := l)
    scale targetSample treatedSample controlSample
    (Finset.univ :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    targetWeight treatedWeight controlWeight targetOutcomeT targetOutcomeC
    treatedOutcome controlOutcome propensityScore treatedPrognosticScore
    controlPrognosticScore treatedValue controlValue treatedEnvelope
    controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit massLimit
    htotalLimit

/--
Base PATT bridge for a finite double-score alphabet, with the cell set
specialized to `Finset.univ`.
-/
def pattDoubleScoreIndicatorSumConvergenceBridgeOfEventuallyIndicator_fintype
    [Fintype PropensityCell] [Fintype PATTProgCell]
    (targetSample controlSample : Index -> Finset Unit)
    (targetWeight controlWeight : Index -> Unit -> Real)
    (treatedTargetOutcome targetControlOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (controlValue : Index -> PATTProgCell -> Real)
    (controlEnvelope : Index -> Real)
    (controlEnvelopeLimit : Real)
    (massLimit : PropensityCell × PATTProgCell -> Real)
    (htotalLimit :
      (∑ cell ∈ (Finset.univ : Finset (PropensityCell × PATTProgCell)),
        massLimit cell) ≠ 0) :
    PATTDoubleScoreIndicatorSumConvergenceBridge :=
  pattDoubleScoreIndicatorSumConvergenceBridgeOfEventuallyIndicator
    (l := l)
    targetSample controlSample
    (Finset.univ : Finset (PropensityCell × PATTProgCell)) targetWeight
    controlWeight treatedTargetOutcome targetControlOutcome controlOutcome
    propensityScore controlPrognosticScore controlValue controlEnvelope
    controlEnvelopeLimit massLimit htotalLimit

/--
Scaled PATT bridge for a finite double-score alphabet, with the cell set
specialized to `Finset.univ`.
-/
def scaledPATTDoubleScoreIndicatorSumConvergenceBridgeOfEventuallyIndicator_fintype
    [Fintype PropensityCell] [Fintype PATTProgCell]
    (scale : Index -> Real)
    (targetSample controlSample : Index -> Finset Unit)
    (targetWeight controlWeight : Index -> Unit -> Real)
    (treatedTargetOutcome targetControlOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (controlValue : Index -> PATTProgCell -> Real)
    (controlEnvelope : Index -> Real)
    (controlEnvelopeLimit : Real)
    (massLimit : PropensityCell × PATTProgCell -> Real)
    (htotalLimit :
      (∑ cell ∈ (Finset.univ : Finset (PropensityCell × PATTProgCell)),
        massLimit cell) ≠ 0) :
    ScaledPATTDoubleScoreIndicatorSumConvergenceBridge :=
  scaledPATTDoubleScoreIndicatorSumConvergenceBridgeOfEventuallyIndicator
    (l := l)
    scale targetSample controlSample
    (Finset.univ : Finset (PropensityCell × PATTProgCell)) targetWeight
    controlWeight treatedTargetOutcome targetControlOutcome controlOutcome
    propensityScore controlPrognosticScore controlValue controlEnvelope
    controlEnvelopeLimit massLimit htotalLimit

end WDSM
end Matching
end StatInference
