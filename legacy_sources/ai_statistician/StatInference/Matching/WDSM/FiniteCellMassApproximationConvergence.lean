import StatInference.Matching.WDSM.DiscreteDoubleScoreApproximateBalancingConvergence
import StatInference.Matching.WDSM.FiniteCellMassConvergence

/-!
# Finite cell-mass convergence to WDSM approximation convergence

The previous deterministic layer reduced double-score share imbalance to
finite weighted cell-mass convergence.  This module composes that reduction
with the approximate-balancing convergence wrappers, so the stochastic target
for the WDSM approximation error is stated directly in terms of finite
cell-mass limits.
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
PATE double-score approximation convergence from fixed finite joint
cell-mass convergence, envelope convergence, and the finite positivity and
score-measurability conditions already used by the deterministic WDSM bound.
-/
theorem tendsto_pateDoubleScoreApprox_error_zero_of_cell_mass_and_envelopes
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
    (hcoverTarget :
      ∀ index unit, unit ∈ targetSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hcoverTreated :
      ∀ index unit, unit ∈ treatedSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hcoverControl :
      ∀ index unit, unit ∈ controlSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hmassTarget :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (targetSample index) (targetWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassTreated :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (treatedSample index) (treatedWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (controlSample index) (controlWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassTarget_tendsto :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellMass (targetSample index) (targetWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell)
          l (nhds (massLimit cell)))
    (hmassTreated_tendsto :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellMass (treatedSample index) (treatedWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell)
          l (nhds (massLimit cell)))
    (hmassControl_tendsto :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellMass (controlSample index) (controlWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell)
          l (nhds (massLimit cell)))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
    (hscoreMeasTargetT :
      ∀ index unit, unit ∈ targetSample index ->
        targetOutcomeT index unit =
          treatedValue index (treatedPrognosticScore index unit))
    (hscoreMeasTreated :
      ∀ index unit, unit ∈ treatedSample index ->
        treatedOutcome index unit =
          treatedValue index (treatedPrognosticScore index unit))
    (hscoreMeasTargetC :
      ∀ index unit, unit ∈ targetSample index ->
        targetOutcomeC index unit =
          controlValue index (controlPrognosticScore index unit))
    (hscoreMeasControl :
      ∀ index unit, unit ∈ controlSample index ->
        controlOutcome index unit =
          controlValue index (controlPrognosticScore index unit))
    (htreated_bound :
      ∀ index cell, cell ∈ cells ->
        |treatedCellValueOnPATEDoubleScore (treatedValue index) cell| ≤
          treatedEnvelope index)
    (hcontrol_bound :
      ∀ index cell, cell ∈ cells ->
        |controlCellValueOnPATEDoubleScore (controlValue index) cell| ≤
          controlEnvelope index)
    (htreatedEnvelope :
      Tendsto treatedEnvelope l (nhds treatedEnvelopeLimit))
    (hcontrolEnvelope :
      Tendsto controlEnvelope l (nhds controlEnvelopeLimit)) :
    Tendsto
      (fun index =>
        weightedSampleMeanContrast (targetSample index)
          (targetWeight index) (targetOutcomeT index)
          (targetOutcomeC index) -
        twoArmWeightedMeanContrast (treatedSample index)
          (controlSample index) (treatedWeight index)
          (controlWeight index) (treatedOutcome index)
          (controlOutcome index))
      l (nhds 0) := by
  have htreatedL1 :
      Tendsto
        (fun index =>
          l1PATEDoubleScoreShareDistance cells
            (targetSample index) (treatedSample index)
            (targetWeight index) (treatedWeight index)
            (propensityScore index) (treatedPrognosticScore index)
            (controlPrognosticScore index))
        l (nhds 0) :=
    tendsto_l1PATEDoubleScoreShareDistance_zero_of_cell_mass
      cells targetSample treatedSample targetWeight treatedWeight
      propensityScore treatedPrognosticScore controlPrognosticScore
      massLimit hcoverTarget hcoverTreated hmassTarget_tendsto
      hmassTreated_tendsto htotalLimit
  have hcontrolL1 :
      Tendsto
        (fun index =>
          l1PATEDoubleScoreShareDistance cells
            (targetSample index) (controlSample index)
            (targetWeight index) (controlWeight index)
            (propensityScore index) (treatedPrognosticScore index)
            (controlPrognosticScore index))
        l (nhds 0) :=
    tendsto_l1PATEDoubleScoreShareDistance_zero_of_cell_mass
      cells targetSample controlSample targetWeight controlWeight
      propensityScore treatedPrognosticScore controlPrognosticScore
      massLimit hcoverTarget hcoverControl hmassTarget_tendsto
      hmassControl_tendsto htotalLimit
  exact tendsto_pateDoubleScoreApprox_error_zero_of_l1_and_envelopes
    targetSample treatedSample controlSample (fun _index => cells)
    targetWeight treatedWeight controlWeight targetOutcomeT targetOutcomeC
    treatedOutcome controlOutcome propensityScore treatedPrognosticScore
    controlPrognosticScore treatedValue controlValue treatedEnvelope
    controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit hcoverTarget
    hcoverTreated hcoverControl hmassTarget hmassTreated hmassControl
    hscoreMeasTargetT hscoreMeasTreated hscoreMeasTargetC
    hscoreMeasControl htreated_bound hcontrol_bound htreatedEnvelope
    hcontrolEnvelope htreatedL1 hcontrolL1

/--
PATT double-score approximation convergence from fixed finite joint
cell-mass convergence, envelope convergence, and finite deterministic WDSM
conditions.
-/
theorem tendsto_pattDoubleScoreApprox_error_zero_of_cell_mass_and_envelope
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
    (massLimit : PropensityCell × PATTProgCell -> Real)
    (hcoverTarget :
      ∀ index unit, unit ∈ targetSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hcoverControl :
      ∀ index unit, unit ∈ controlSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hmassTarget :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (targetSample index) (targetWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (controlSample index) (controlWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassTarget_tendsto :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellMass (targetSample index) (targetWeight index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell)
          l (nhds (massLimit cell)))
    (hmassControl_tendsto :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellMass (controlSample index) (controlWeight index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell)
          l (nhds (massLimit cell)))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
    (hscoreMeasTargetC :
      ∀ index unit, unit ∈ targetSample index ->
        targetControlOutcome index unit =
          controlValue index (controlPrognosticScore index unit))
    (hscoreMeasControl :
      ∀ index unit, unit ∈ controlSample index ->
        controlOutcome index unit =
          controlValue index (controlPrognosticScore index unit))
    (hcontrol_bound :
      ∀ index cell, cell ∈ cells ->
        |controlCellValueOnPATTDoubleScore (controlValue index) cell| ≤
          controlEnvelope index)
    (hcontrolEnvelope :
      Tendsto controlEnvelope l (nhds controlEnvelopeLimit)) :
    Tendsto
      (fun index =>
        weightedSampleMeanContrast (targetSample index)
          (targetWeight index) (treatedTargetOutcome index)
          (targetControlOutcome index) -
        pattWeightedMeanContrast (targetSample index) (controlSample index)
          (targetWeight index) (controlWeight index)
          (treatedTargetOutcome index) (controlOutcome index))
      l (nhds 0) := by
  have hcontrolL1 :
      Tendsto
        (fun index =>
          l1PATTDoubleScoreShareDistance cells
            (targetSample index) (controlSample index)
            (targetWeight index) (controlWeight index)
            (propensityScore index) (controlPrognosticScore index))
        l (nhds 0) :=
    tendsto_l1PATTDoubleScoreShareDistance_zero_of_cell_mass
      cells targetSample controlSample targetWeight controlWeight
      propensityScore controlPrognosticScore massLimit hcoverTarget
      hcoverControl hmassTarget_tendsto hmassControl_tendsto htotalLimit
  exact tendsto_pattDoubleScoreApprox_error_zero_of_l1_and_envelope
    targetSample controlSample (fun _index => cells) targetWeight
    controlWeight treatedTargetOutcome targetControlOutcome controlOutcome
    propensityScore controlPrognosticScore controlValue controlEnvelope
    controlEnvelopeLimit hcoverTarget hcoverControl hmassTarget
    hmassControl hscoreMeasTargetC hscoreMeasControl hcontrol_bound
    hcontrolEnvelope hcontrolL1

/--
Scaled PATE double-score approximation convergence from fixed finite joint
cell-mass limits plus scaled target-arm cell-mass-difference convergence.
-/
theorem tendsto_scaled_pateDoubleScoreApprox_error_zero_of_cell_mass_and_envelopes
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
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hcoverTarget :
      ∀ index unit, unit ∈ targetSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hcoverTreated :
      ∀ index unit, unit ∈ treatedSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hcoverControl :
      ∀ index unit, unit ∈ controlSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hmassTarget :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (targetSample index) (targetWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassTreated :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (treatedSample index) (treatedWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (controlSample index) (controlWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassTarget_tendsto :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellMass (targetSample index) (targetWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell)
          l (nhds (massLimit cell)))
    (hmassTreated_tendsto :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellMass (treatedSample index) (treatedWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell)
          l (nhds (massLimit cell)))
    (hmassControl_tendsto :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellMass (controlSample index) (controlWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell)
          l (nhds (massLimit cell)))
    (hscaledMassTreated :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (scoreCellMass (targetSample index) (targetWeight index)
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell -
                scoreCellMass (treatedSample index) (treatedWeight index)
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell))
          l (nhds 0))
    (hscaledMassControl :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (scoreCellMass (targetSample index) (targetWeight index)
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell -
                scoreCellMass (controlSample index) (controlWeight index)
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index)) cell))
          l (nhds 0))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
    (hscoreMeasTargetT :
      ∀ index unit, unit ∈ targetSample index ->
        targetOutcomeT index unit =
          treatedValue index (treatedPrognosticScore index unit))
    (hscoreMeasTreated :
      ∀ index unit, unit ∈ treatedSample index ->
        treatedOutcome index unit =
          treatedValue index (treatedPrognosticScore index unit))
    (hscoreMeasTargetC :
      ∀ index unit, unit ∈ targetSample index ->
        targetOutcomeC index unit =
          controlValue index (controlPrognosticScore index unit))
    (hscoreMeasControl :
      ∀ index unit, unit ∈ controlSample index ->
        controlOutcome index unit =
          controlValue index (controlPrognosticScore index unit))
    (htreated_bound :
      ∀ index cell, cell ∈ cells ->
        |treatedCellValueOnPATEDoubleScore (treatedValue index) cell| ≤
          treatedEnvelope index)
    (hcontrol_bound :
      ∀ index cell, cell ∈ cells ->
        |controlCellValueOnPATEDoubleScore (controlValue index) cell| ≤
          controlEnvelope index)
    (htreatedEnvelope :
      Tendsto treatedEnvelope l (nhds treatedEnvelopeLimit))
    (hcontrolEnvelope :
      Tendsto controlEnvelope l (nhds controlEnvelopeLimit)) :
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
      l (nhds 0) := by
  have htreatedScaledL1 :
      Tendsto
        (fun index =>
          scale index *
            l1PATEDoubleScoreShareDistance cells
              (targetSample index) (treatedSample index)
              (targetWeight index) (treatedWeight index)
              (propensityScore index) (treatedPrognosticScore index)
              (controlPrognosticScore index))
        l (nhds 0) :=
    tendsto_scaled_l1PATEDoubleScoreShareDistance_zero_of_cell_mass
      cells scale targetSample treatedSample targetWeight treatedWeight
      propensityScore treatedPrognosticScore controlPrognosticScore
      massLimit hscale_nonneg hcoverTarget hcoverTreated
      hmassTarget_tendsto hmassTreated_tendsto hscaledMassTreated
      htotalLimit
  have hcontrolScaledL1 :
      Tendsto
        (fun index =>
          scale index *
            l1PATEDoubleScoreShareDistance cells
              (targetSample index) (controlSample index)
              (targetWeight index) (controlWeight index)
              (propensityScore index) (treatedPrognosticScore index)
              (controlPrognosticScore index))
        l (nhds 0) :=
    tendsto_scaled_l1PATEDoubleScoreShareDistance_zero_of_cell_mass
      cells scale targetSample controlSample targetWeight controlWeight
      propensityScore treatedPrognosticScore controlPrognosticScore
      massLimit hscale_nonneg hcoverTarget hcoverControl
      hmassTarget_tendsto hmassControl_tendsto hscaledMassControl
      htotalLimit
  exact tendsto_scaled_pateDoubleScoreApprox_error_zero_of_scaled_l1_and_envelopes
    scale targetSample treatedSample controlSample (fun _index => cells)
    targetWeight treatedWeight controlWeight targetOutcomeT targetOutcomeC
    treatedOutcome controlOutcome propensityScore treatedPrognosticScore
    controlPrognosticScore treatedValue controlValue treatedEnvelope
    controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit hscale_nonneg
    hcoverTarget hcoverTreated hcoverControl hmassTarget hmassTreated
    hmassControl hscoreMeasTargetT hscoreMeasTreated hscoreMeasTargetC
    hscoreMeasControl htreated_bound hcontrol_bound htreatedEnvelope
    hcontrolEnvelope htreatedScaledL1 hcontrolScaledL1

/--
Scaled PATT double-score approximation convergence from fixed finite joint
cell-mass limits plus scaled target-control cell-mass-difference convergence.
-/
theorem tendsto_scaled_pattDoubleScoreApprox_error_zero_of_cell_mass_and_envelope
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
    (massLimit : PropensityCell × PATTProgCell -> Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hcoverTarget :
      ∀ index unit, unit ∈ targetSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hcoverControl :
      ∀ index unit, unit ∈ controlSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells)
    (hmassTarget :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (targetSample index) (targetWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ index cell, cell ∈ cells ->
        scoreCellMass (controlSample index) (controlWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassTarget_tendsto :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellMass (targetSample index) (targetWeight index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell)
          l (nhds (massLimit cell)))
    (hmassControl_tendsto :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scoreCellMass (controlSample index) (controlWeight index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell)
          l (nhds (massLimit cell)))
    (hscaledMassControl :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            scale index *
              (scoreCellMass (targetSample index) (targetWeight index)
                  (pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index)) cell -
                scoreCellMass (controlSample index) (controlWeight index)
                  (pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index)) cell))
          l (nhds 0))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
    (hscoreMeasTargetC :
      ∀ index unit, unit ∈ targetSample index ->
        targetControlOutcome index unit =
          controlValue index (controlPrognosticScore index unit))
    (hscoreMeasControl :
      ∀ index unit, unit ∈ controlSample index ->
        controlOutcome index unit =
          controlValue index (controlPrognosticScore index unit))
    (hcontrol_bound :
      ∀ index cell, cell ∈ cells ->
        |controlCellValueOnPATTDoubleScore (controlValue index) cell| ≤
          controlEnvelope index)
    (hcontrolEnvelope :
      Tendsto controlEnvelope l (nhds controlEnvelopeLimit)) :
    Tendsto
      (fun index =>
        scale index *
          (weightedSampleMeanContrast (targetSample index)
            (targetWeight index) (treatedTargetOutcome index)
            (targetControlOutcome index) -
          pattWeightedMeanContrast (targetSample index) (controlSample index)
            (targetWeight index) (controlWeight index)
            (treatedTargetOutcome index) (controlOutcome index)))
      l (nhds 0) := by
  have hcontrolScaledL1 :
      Tendsto
        (fun index =>
          scale index *
            l1PATTDoubleScoreShareDistance cells
              (targetSample index) (controlSample index)
              (targetWeight index) (controlWeight index)
              (propensityScore index) (controlPrognosticScore index))
        l (nhds 0) :=
    tendsto_scaled_l1PATTDoubleScoreShareDistance_zero_of_cell_mass
      cells scale targetSample controlSample targetWeight controlWeight
      propensityScore controlPrognosticScore massLimit hscale_nonneg
      hcoverTarget hcoverControl hmassTarget_tendsto hmassControl_tendsto
      hscaledMassControl htotalLimit
  exact tendsto_scaled_pattDoubleScoreApprox_error_zero_of_scaled_l1_and_envelope
    scale targetSample controlSample (fun _index => cells) targetWeight
    controlWeight treatedTargetOutcome targetControlOutcome controlOutcome
    propensityScore controlPrognosticScore controlValue controlEnvelope
    controlEnvelopeLimit hscale_nonneg hcoverTarget hcoverControl
    hmassTarget hmassControl hscoreMeasTargetC hscoreMeasControl
    hcontrol_bound hcontrolEnvelope hcontrolScaledL1

end WDSM
end Matching
end StatInference
