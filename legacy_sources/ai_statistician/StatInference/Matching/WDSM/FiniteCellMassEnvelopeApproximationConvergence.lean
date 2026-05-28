import StatInference.Matching.WDSM.DiscreteDoubleScoreApproximateBalancingConvergence
import StatInference.Matching.WDSM.FiniteCellShareEnvelopeConvergence

/-!
# WDSM approximation convergence from finite cell-mass envelopes

This module composes the finite double-score L1 share envelope route with the
existing approximation convergence wrappers.  Concrete survey-weighted LLNs
can now target eventual absolute joint-cell mass error bounds directly.
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
PATE double-score approximation convergence from shrinking finite joint
cell-mass envelopes, outcome envelope convergence, and the deterministic
finite score-measurability/positivity conditions.
-/
theorem tendsto_pateDoubleScoreApprox_error_zero_of_cell_mass_envelope_bounds
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
    (massLimit massScaleTarget massScaleTreated massScaleControl :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (massEnvelopeTarget massEnvelopeTreated massEnvelopeControl :
      Index -> Real)
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
    (hmassTarget_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (targetSample index) (targetWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleTarget cell * massEnvelopeTarget index)
    (hmassTreated_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (treatedSample index) (treatedWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleTreated cell * massEnvelopeTreated index)
    (hmassControl_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (controlSample index) (controlWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleControl cell * massEnvelopeControl index)
    (hmassEnvelopeTarget :
      Tendsto massEnvelopeTarget l (nhds 0))
    (hmassEnvelopeTreated :
      Tendsto massEnvelopeTreated l (nhds 0))
    (hmassEnvelopeControl :
      Tendsto massEnvelopeControl l (nhds 0))
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
    tendsto_l1PATEDoubleScoreShareDistance_zero_of_cell_mass_envelopes
      (l := l) cells targetSample treatedSample targetWeight treatedWeight
      propensityScore treatedPrognosticScore controlPrognosticScore
      massLimit massScaleTarget massScaleTreated massEnvelopeTarget
      massEnvelopeTreated hcoverTarget hcoverTreated hmassTarget_bound
      hmassTreated_bound hmassEnvelopeTarget hmassEnvelopeTreated
      htotalLimit
  have hcontrolL1 :
      Tendsto
        (fun index =>
          l1PATEDoubleScoreShareDistance cells
            (targetSample index) (controlSample index)
            (targetWeight index) (controlWeight index)
            (propensityScore index) (treatedPrognosticScore index)
            (controlPrognosticScore index))
        l (nhds 0) :=
    tendsto_l1PATEDoubleScoreShareDistance_zero_of_cell_mass_envelopes
      (l := l) cells targetSample controlSample targetWeight controlWeight
      propensityScore treatedPrognosticScore controlPrognosticScore
      massLimit massScaleTarget massScaleControl massEnvelopeTarget
      massEnvelopeControl hcoverTarget hcoverControl hmassTarget_bound
      hmassControl_bound hmassEnvelopeTarget hmassEnvelopeControl
      htotalLimit
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
PATE double-score approximation convergence from eventually valid finite
conditions and shrinking finite joint-cell mass envelopes.
-/
theorem tendsto_pateDoubleScoreApprox_error_zero_of_eventually_cell_mass_envelope_bounds
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
    (massLimit massScaleTarget massScaleTreated massScaleControl :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (massEnvelopeTarget massEnvelopeTreated massEnvelopeControl :
      Index -> Real)
    (hcoverTarget :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index) unit ∈ cells)
    (hcoverTreated :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ treatedSample index ->
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index) unit ∈ cells)
    (hcoverControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index) unit ∈ cells)
    (hmassTarget :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
          scoreCellMass (targetSample index) (targetWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index)
              (controlPrognosticScore index)) cell ≠ 0)
    (hmassTreated :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
          scoreCellMass (treatedSample index) (treatedWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index)
              (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
          scoreCellMass (controlSample index) (controlWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index)
              (controlPrognosticScore index)) cell ≠ 0)
    (hmassTarget_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (targetSample index) (targetWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleTarget cell * massEnvelopeTarget index)
    (hmassTreated_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (treatedSample index) (treatedWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleTreated cell * massEnvelopeTreated index)
    (hmassControl_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (controlSample index) (controlWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleControl cell * massEnvelopeControl index)
    (hmassEnvelopeTarget :
      Tendsto massEnvelopeTarget l (nhds 0))
    (hmassEnvelopeTreated :
      Tendsto massEnvelopeTreated l (nhds 0))
    (hmassEnvelopeControl :
      Tendsto massEnvelopeControl l (nhds 0))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
    (hscoreMeasTargetT :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          targetOutcomeT index unit =
            treatedValue index (treatedPrognosticScore index unit))
    (hscoreMeasTreated :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ treatedSample index ->
          treatedOutcome index unit =
            treatedValue index (treatedPrognosticScore index unit))
    (hscoreMeasTargetC :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          targetOutcomeC index unit =
            controlValue index (controlPrognosticScore index unit))
    (hscoreMeasControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          controlOutcome index unit =
            controlValue index (controlPrognosticScore index unit))
    (htreated_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
          |treatedCellValueOnPATEDoubleScore (treatedValue index) cell| ≤
            treatedEnvelope index)
    (hcontrol_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
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
    tendsto_l1PATEDoubleScoreShareDistance_zero_of_eventually_cell_mass_envelopes
      (l := l) cells targetSample treatedSample targetWeight treatedWeight
      propensityScore treatedPrognosticScore controlPrognosticScore
      massLimit massScaleTarget massScaleTreated massEnvelopeTarget
      massEnvelopeTreated hcoverTarget hcoverTreated hmassTarget_bound
      hmassTreated_bound hmassEnvelopeTarget hmassEnvelopeTreated
      htotalLimit
  have hcontrolL1 :
      Tendsto
        (fun index =>
          l1PATEDoubleScoreShareDistance cells
            (targetSample index) (controlSample index)
            (targetWeight index) (controlWeight index)
            (propensityScore index) (treatedPrognosticScore index)
            (controlPrognosticScore index))
        l (nhds 0) :=
    tendsto_l1PATEDoubleScoreShareDistance_zero_of_eventually_cell_mass_envelopes
      (l := l) cells targetSample controlSample targetWeight controlWeight
      propensityScore treatedPrognosticScore controlPrognosticScore
      massLimit massScaleTarget massScaleControl massEnvelopeTarget
      massEnvelopeControl hcoverTarget hcoverControl hmassTarget_bound
      hmassControl_bound hmassEnvelopeTarget hmassEnvelopeControl
      htotalLimit
  exact tendsto_pateDoubleScoreApprox_error_zero_of_eventually_l1_and_envelopes
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
Scaled PATE double-score approximation convergence from shrinking finite joint
cell-mass envelopes and shrinking scaled joint-cell mass-difference envelopes.
-/
theorem tendsto_scaled_pateDoubleScoreApprox_error_zero_of_cell_mass_envelope_bounds
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
    (massLimit massScaleTarget massScaleTreated massScaleControl :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (scaledMassScaleTreated scaledMassScaleControl :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (massEnvelopeTarget massEnvelopeTreated massEnvelopeControl :
      Index -> Real)
    (scaledMassEnvelopeTreated scaledMassEnvelopeControl : Index -> Real)
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
    (hmassTarget_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (targetSample index) (targetWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleTarget cell * massEnvelopeTarget index)
    (hmassTreated_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (treatedSample index) (treatedWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleTreated cell * massEnvelopeTreated index)
    (hmassControl_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (controlSample index) (controlWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleControl cell * massEnvelopeControl index)
    (hscaledMassTreated_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scale index *
            (scoreCellMass (targetSample index) (targetWeight index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell -
              scoreCellMass (treatedSample index) (treatedWeight index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell)| ≤
            scaledMassScaleTreated cell * scaledMassEnvelopeTreated index)
    (hscaledMassControl_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scale index *
            (scoreCellMass (targetSample index) (targetWeight index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell -
              scoreCellMass (controlSample index) (controlWeight index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell)| ≤
            scaledMassScaleControl cell * scaledMassEnvelopeControl index)
    (hmassEnvelopeTarget :
      Tendsto massEnvelopeTarget l (nhds 0))
    (hmassEnvelopeTreated :
      Tendsto massEnvelopeTreated l (nhds 0))
    (hmassEnvelopeControl :
      Tendsto massEnvelopeControl l (nhds 0))
    (hscaledMassEnvelopeTreated :
      Tendsto scaledMassEnvelopeTreated l (nhds 0))
    (hscaledMassEnvelopeControl :
      Tendsto scaledMassEnvelopeControl l (nhds 0))
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
    tendsto_scaled_l1PATEDoubleScoreShareDistance_zero_of_cell_mass_envelopes
      (l := l) cells scale targetSample treatedSample targetWeight
      treatedWeight propensityScore treatedPrognosticScore
      controlPrognosticScore massLimit massScaleTarget massScaleTreated
      scaledMassScaleTreated massEnvelopeTarget massEnvelopeTreated
      scaledMassEnvelopeTreated hscale_nonneg hcoverTarget hcoverTreated
      hmassTarget_bound hmassTreated_bound hscaledMassTreated_bound
      hmassEnvelopeTarget hmassEnvelopeTreated hscaledMassEnvelopeTreated
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
    tendsto_scaled_l1PATEDoubleScoreShareDistance_zero_of_cell_mass_envelopes
      (l := l) cells scale targetSample controlSample targetWeight
      controlWeight propensityScore treatedPrognosticScore
      controlPrognosticScore massLimit massScaleTarget massScaleControl
      scaledMassScaleControl massEnvelopeTarget massEnvelopeControl
      scaledMassEnvelopeControl hscale_nonneg hcoverTarget hcoverControl
      hmassTarget_bound hmassControl_bound hscaledMassControl_bound
      hmassEnvelopeTarget hmassEnvelopeControl hscaledMassEnvelopeControl
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
PATE double-score approximation convergence at ordinary and scaled rates from
shrinking finite joint cell-mass envelopes and shrinking scaled joint-cell
mass-difference envelopes.
-/
theorem tendsto_pateDoubleScoreApprox_error_zero_and_scaled_zero_of_cell_mass_envelope_bounds
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
    (massLimit massScaleTarget massScaleTreated massScaleControl :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (scaledMassScaleTreated scaledMassScaleControl :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (massEnvelopeTarget massEnvelopeTreated massEnvelopeControl :
      Index -> Real)
    (scaledMassEnvelopeTreated scaledMassEnvelopeControl : Index -> Real)
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
    (hmassTarget_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (targetSample index) (targetWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleTarget cell * massEnvelopeTarget index)
    (hmassTreated_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (treatedSample index) (treatedWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleTreated cell * massEnvelopeTreated index)
    (hmassControl_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (controlSample index) (controlWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleControl cell * massEnvelopeControl index)
    (hscaledMassTreated_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scale index *
            (scoreCellMass (targetSample index) (targetWeight index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell -
              scoreCellMass (treatedSample index) (treatedWeight index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell)| ≤
            scaledMassScaleTreated cell * scaledMassEnvelopeTreated index)
    (hscaledMassControl_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scale index *
            (scoreCellMass (targetSample index) (targetWeight index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell -
              scoreCellMass (controlSample index) (controlWeight index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell)| ≤
            scaledMassScaleControl cell * scaledMassEnvelopeControl index)
    (hmassEnvelopeTarget :
      Tendsto massEnvelopeTarget l (nhds 0))
    (hmassEnvelopeTreated :
      Tendsto massEnvelopeTreated l (nhds 0))
    (hmassEnvelopeControl :
      Tendsto massEnvelopeControl l (nhds 0))
    (hscaledMassEnvelopeTreated :
      Tendsto scaledMassEnvelopeTreated l (nhds 0))
    (hscaledMassEnvelopeControl :
      Tendsto scaledMassEnvelopeControl l (nhds 0))
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
        l (nhds 0) ∧
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
  constructor
  · apply
      (tendsto_pateDoubleScoreApprox_error_zero_of_cell_mass_envelope_bounds
        (l := l) (Index := Index) (Unit := Unit)
        (PropensityCell := PropensityCell)
        (TreatedProgCell := TreatedProgCell)
        (ControlProgCell := ControlProgCell))
    all_goals assumption
  · apply
      (tendsto_scaled_pateDoubleScoreApprox_error_zero_of_cell_mass_envelope_bounds
        (l := l) (Index := Index) (Unit := Unit)
        (PropensityCell := PropensityCell)
        (TreatedProgCell := TreatedProgCell)
        (ControlProgCell := ControlProgCell))
    all_goals assumption

/--
Scaled PATE double-score approximation convergence from eventually valid
finite conditions, eventual scale nonnegativity, shrinking finite joint-cell
mass envelopes, and shrinking scaled joint-cell mass-difference envelopes.
-/
theorem tendsto_scaled_pateDoubleScoreApprox_error_zero_of_eventually_cell_mass_envelope_bounds
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
    (massLimit massScaleTarget massScaleTreated massScaleControl :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (scaledMassScaleTreated scaledMassScaleControl :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (massEnvelopeTarget massEnvelopeTreated massEnvelopeControl :
      Index -> Real)
    (scaledMassEnvelopeTreated scaledMassEnvelopeControl : Index -> Real)
    (hscale_nonneg : ∀ᶠ index in l, 0 ≤ scale index)
    (hcoverTarget :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index) unit ∈ cells)
    (hcoverTreated :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ treatedSample index ->
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index) unit ∈ cells)
    (hcoverControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index) unit ∈ cells)
    (hmassTarget :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
          scoreCellMass (targetSample index) (targetWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index)
              (controlPrognosticScore index)) cell ≠ 0)
    (hmassTreated :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
          scoreCellMass (treatedSample index) (treatedWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index)
              (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
          scoreCellMass (controlSample index) (controlWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index)
              (controlPrognosticScore index)) cell ≠ 0)
    (hmassTarget_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (targetSample index) (targetWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleTarget cell * massEnvelopeTarget index)
    (hmassTreated_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (treatedSample index) (treatedWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleTreated cell * massEnvelopeTreated index)
    (hmassControl_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (controlSample index) (controlWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleControl cell * massEnvelopeControl index)
    (hscaledMassTreated_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scale index *
            (scoreCellMass (targetSample index) (targetWeight index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell -
              scoreCellMass (treatedSample index) (treatedWeight index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell)| ≤
            scaledMassScaleTreated cell * scaledMassEnvelopeTreated index)
    (hscaledMassControl_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scale index *
            (scoreCellMass (targetSample index) (targetWeight index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell -
              scoreCellMass (controlSample index) (controlWeight index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell)| ≤
            scaledMassScaleControl cell * scaledMassEnvelopeControl index)
    (hmassEnvelopeTarget :
      Tendsto massEnvelopeTarget l (nhds 0))
    (hmassEnvelopeTreated :
      Tendsto massEnvelopeTreated l (nhds 0))
    (hmassEnvelopeControl :
      Tendsto massEnvelopeControl l (nhds 0))
    (hscaledMassEnvelopeTreated :
      Tendsto scaledMassEnvelopeTreated l (nhds 0))
    (hscaledMassEnvelopeControl :
      Tendsto scaledMassEnvelopeControl l (nhds 0))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
    (hscoreMeasTargetT :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          targetOutcomeT index unit =
            treatedValue index (treatedPrognosticScore index unit))
    (hscoreMeasTreated :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ treatedSample index ->
          treatedOutcome index unit =
            treatedValue index (treatedPrognosticScore index unit))
    (hscoreMeasTargetC :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          targetOutcomeC index unit =
            controlValue index (controlPrognosticScore index unit))
    (hscoreMeasControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          controlOutcome index unit =
            controlValue index (controlPrognosticScore index unit))
    (htreated_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
          |treatedCellValueOnPATEDoubleScore (treatedValue index) cell| ≤
            treatedEnvelope index)
    (hcontrol_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
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
    tendsto_scaled_l1PATEDoubleScoreShareDistance_zero_of_eventually_cell_mass_envelopes
      (l := l) cells scale targetSample treatedSample targetWeight
      treatedWeight propensityScore treatedPrognosticScore
      controlPrognosticScore massLimit massScaleTarget massScaleTreated
      scaledMassScaleTreated massEnvelopeTarget massEnvelopeTreated
      scaledMassEnvelopeTreated hscale_nonneg hcoverTarget hcoverTreated
      hmassTarget_bound hmassTreated_bound hscaledMassTreated_bound
      hmassEnvelopeTarget hmassEnvelopeTreated hscaledMassEnvelopeTreated
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
    tendsto_scaled_l1PATEDoubleScoreShareDistance_zero_of_eventually_cell_mass_envelopes
      (l := l) cells scale targetSample controlSample targetWeight
      controlWeight propensityScore treatedPrognosticScore
      controlPrognosticScore massLimit massScaleTarget massScaleControl
      scaledMassScaleControl massEnvelopeTarget massEnvelopeControl
      scaledMassEnvelopeControl hscale_nonneg hcoverTarget hcoverControl
      hmassTarget_bound hmassControl_bound hscaledMassControl_bound
      hmassEnvelopeTarget hmassEnvelopeControl hscaledMassEnvelopeControl
      htotalLimit
  exact tendsto_scaled_pateDoubleScoreApprox_error_zero_of_eventually_scaled_l1_and_envelopes
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
PATE double-score approximation convergence at ordinary and scaled rates from
eventually valid finite conditions, eventual scale nonnegativity, shrinking
finite joint-cell mass envelopes, and shrinking scaled joint-cell
mass-difference envelopes.
-/
theorem tendsto_pateDoubleScoreApprox_error_zero_and_scaled_zero_of_eventually_cell_mass_envelope_bounds
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
    (massLimit massScaleTarget massScaleTreated massScaleControl :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (scaledMassScaleTreated scaledMassScaleControl :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (massEnvelopeTarget massEnvelopeTreated massEnvelopeControl :
      Index -> Real)
    (scaledMassEnvelopeTreated scaledMassEnvelopeControl : Index -> Real)
    (hscale_nonneg : ∀ᶠ index in l, 0 ≤ scale index)
    (hcoverTarget :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index) unit ∈ cells)
    (hcoverTreated :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ treatedSample index ->
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index) unit ∈ cells)
    (hcoverControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index) unit ∈ cells)
    (hmassTarget :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
          scoreCellMass (targetSample index) (targetWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index)
              (controlPrognosticScore index)) cell ≠ 0)
    (hmassTreated :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
          scoreCellMass (treatedSample index) (treatedWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index)
              (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
          scoreCellMass (controlSample index) (controlWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index)
              (controlPrognosticScore index)) cell ≠ 0)
    (hmassTarget_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (targetSample index) (targetWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleTarget cell * massEnvelopeTarget index)
    (hmassTreated_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (treatedSample index) (treatedWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleTreated cell * massEnvelopeTreated index)
    (hmassControl_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (controlSample index) (controlWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleControl cell * massEnvelopeControl index)
    (hscaledMassTreated_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scale index *
            (scoreCellMass (targetSample index) (targetWeight index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell -
              scoreCellMass (treatedSample index) (treatedWeight index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell)| ≤
            scaledMassScaleTreated cell * scaledMassEnvelopeTreated index)
    (hscaledMassControl_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scale index *
            (scoreCellMass (targetSample index) (targetWeight index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell -
              scoreCellMass (controlSample index) (controlWeight index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index)) cell)| ≤
            scaledMassScaleControl cell * scaledMassEnvelopeControl index)
    (hmassEnvelopeTarget :
      Tendsto massEnvelopeTarget l (nhds 0))
    (hmassEnvelopeTreated :
      Tendsto massEnvelopeTreated l (nhds 0))
    (hmassEnvelopeControl :
      Tendsto massEnvelopeControl l (nhds 0))
    (hscaledMassEnvelopeTreated :
      Tendsto scaledMassEnvelopeTreated l (nhds 0))
    (hscaledMassEnvelopeControl :
      Tendsto scaledMassEnvelopeControl l (nhds 0))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
    (hscoreMeasTargetT :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          targetOutcomeT index unit =
            treatedValue index (treatedPrognosticScore index unit))
    (hscoreMeasTreated :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ treatedSample index ->
          treatedOutcome index unit =
            treatedValue index (treatedPrognosticScore index unit))
    (hscoreMeasTargetC :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          targetOutcomeC index unit =
            controlValue index (controlPrognosticScore index unit))
    (hscoreMeasControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          controlOutcome index unit =
            controlValue index (controlPrognosticScore index unit))
    (htreated_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
          |treatedCellValueOnPATEDoubleScore (treatedValue index) cell| ≤
            treatedEnvelope index)
    (hcontrol_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
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
        l (nhds 0) ∧
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
  constructor
  · apply
      (tendsto_pateDoubleScoreApprox_error_zero_of_eventually_cell_mass_envelope_bounds
        (l := l) (Index := Index) (Unit := Unit)
        (PropensityCell := PropensityCell)
        (TreatedProgCell := TreatedProgCell)
        (ControlProgCell := ControlProgCell))
    all_goals assumption
  · apply
      (tendsto_scaled_pateDoubleScoreApprox_error_zero_of_eventually_cell_mass_envelope_bounds
        (l := l) (Index := Index) (Unit := Unit)
        (PropensityCell := PropensityCell)
        (TreatedProgCell := TreatedProgCell)
        (ControlProgCell := ControlProgCell))
    all_goals assumption

/--
PATT double-score approximation convergence from shrinking finite joint
cell-mass envelopes, outcome envelope convergence, and the deterministic
finite score-measurability/positivity conditions.
-/
theorem tendsto_pattDoubleScoreApprox_error_zero_of_cell_mass_envelope_bounds
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
    (massLimit massScaleTarget massScaleControl :
      PropensityCell × PATTProgCell -> Real)
    (massEnvelopeTarget massEnvelopeControl : Index -> Real)
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
    (hmassTarget_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (targetSample index) (targetWeight index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleTarget cell * massEnvelopeTarget index)
    (hmassControl_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (controlSample index) (controlWeight index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleControl cell * massEnvelopeControl index)
    (hmassEnvelopeTarget :
      Tendsto massEnvelopeTarget l (nhds 0))
    (hmassEnvelopeControl :
      Tendsto massEnvelopeControl l (nhds 0))
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
    tendsto_l1PATTDoubleScoreShareDistance_zero_of_cell_mass_envelopes
      (l := l) cells targetSample controlSample targetWeight controlWeight
      propensityScore controlPrognosticScore massLimit massScaleTarget
      massScaleControl massEnvelopeTarget massEnvelopeControl hcoverTarget
      hcoverControl hmassTarget_bound hmassControl_bound hmassEnvelopeTarget
      hmassEnvelopeControl htotalLimit
  exact tendsto_pattDoubleScoreApprox_error_zero_of_l1_and_envelope
    targetSample controlSample (fun _index => cells) targetWeight
    controlWeight treatedTargetOutcome targetControlOutcome controlOutcome
    propensityScore controlPrognosticScore controlValue controlEnvelope
    controlEnvelopeLimit hcoverTarget hcoverControl hmassTarget hmassControl
    hscoreMeasTargetC hscoreMeasControl hcontrol_bound hcontrolEnvelope
    hcontrolL1

/--
PATT double-score approximation convergence from eventually valid finite
conditions and shrinking finite joint-cell mass envelopes.
-/
theorem tendsto_pattDoubleScoreApprox_error_zero_of_eventually_cell_mass_envelope_bounds
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
    (massLimit massScaleTarget massScaleControl :
      PropensityCell × PATTProgCell -> Real)
    (massEnvelopeTarget massEnvelopeControl : Index -> Real)
    (hcoverTarget :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          pattDoubleScore (propensityScore index)
            (controlPrognosticScore index) unit ∈ cells)
    (hcoverControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          pattDoubleScore (propensityScore index)
            (controlPrognosticScore index) unit ∈ cells)
    (hmassTarget :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
          scoreCellMass (targetSample index) (targetWeight index)
            (pattDoubleScore (propensityScore index)
              (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
          scoreCellMass (controlSample index) (controlWeight index)
            (pattDoubleScore (propensityScore index)
              (controlPrognosticScore index)) cell ≠ 0)
    (hmassTarget_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (targetSample index) (targetWeight index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleTarget cell * massEnvelopeTarget index)
    (hmassControl_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (controlSample index) (controlWeight index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleControl cell * massEnvelopeControl index)
    (hmassEnvelopeTarget :
      Tendsto massEnvelopeTarget l (nhds 0))
    (hmassEnvelopeControl :
      Tendsto massEnvelopeControl l (nhds 0))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
    (hscoreMeasTargetC :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          targetControlOutcome index unit =
            controlValue index (controlPrognosticScore index unit))
    (hscoreMeasControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          controlOutcome index unit =
            controlValue index (controlPrognosticScore index unit))
    (hcontrol_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
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
    tendsto_l1PATTDoubleScoreShareDistance_zero_of_eventually_cell_mass_envelopes
      (l := l) cells targetSample controlSample targetWeight controlWeight
      propensityScore controlPrognosticScore massLimit massScaleTarget
      massScaleControl massEnvelopeTarget massEnvelopeControl hcoverTarget
      hcoverControl hmassTarget_bound hmassControl_bound hmassEnvelopeTarget
      hmassEnvelopeControl htotalLimit
  exact tendsto_pattDoubleScoreApprox_error_zero_of_eventually_l1_and_envelope
    targetSample controlSample (fun _index => cells) targetWeight
    controlWeight treatedTargetOutcome targetControlOutcome controlOutcome
    propensityScore controlPrognosticScore controlValue controlEnvelope
    controlEnvelopeLimit hcoverTarget hcoverControl hmassTarget hmassControl
    hscoreMeasTargetC hscoreMeasControl hcontrol_bound hcontrolEnvelope
    hcontrolL1

/--
Scaled PATT double-score approximation convergence from shrinking finite joint
cell-mass envelopes and a shrinking scaled joint-cell mass-difference envelope.
-/
theorem tendsto_scaled_pattDoubleScoreApprox_error_zero_of_cell_mass_envelope_bounds
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
    (massLimit massScaleTarget massScaleControl scaledMassScale :
      PropensityCell × PATTProgCell -> Real)
    (massEnvelopeTarget massEnvelopeControl scaledMassEnvelope :
      Index -> Real)
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
    (hmassTarget_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (targetSample index) (targetWeight index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleTarget cell * massEnvelopeTarget index)
    (hmassControl_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (controlSample index) (controlWeight index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleControl cell * massEnvelopeControl index)
    (hscaledMass_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scale index *
            (scoreCellMass (targetSample index) (targetWeight index)
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell -
              scoreCellMass (controlSample index) (controlWeight index)
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell)| ≤
            scaledMassScale cell * scaledMassEnvelope index)
    (hmassEnvelopeTarget :
      Tendsto massEnvelopeTarget l (nhds 0))
    (hmassEnvelopeControl :
      Tendsto massEnvelopeControl l (nhds 0))
    (hscaledMassEnvelope :
      Tendsto scaledMassEnvelope l (nhds 0))
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
    tendsto_scaled_l1PATTDoubleScoreShareDistance_zero_of_cell_mass_envelopes
      (l := l) cells scale targetSample controlSample targetWeight
      controlWeight propensityScore controlPrognosticScore massLimit
      massScaleTarget massScaleControl scaledMassScale massEnvelopeTarget
      massEnvelopeControl scaledMassEnvelope hscale_nonneg hcoverTarget
      hcoverControl hmassTarget_bound hmassControl_bound hscaledMass_bound
      hmassEnvelopeTarget hmassEnvelopeControl hscaledMassEnvelope
      htotalLimit
  exact tendsto_scaled_pattDoubleScoreApprox_error_zero_of_scaled_l1_and_envelope
    scale targetSample controlSample (fun _index => cells) targetWeight
    controlWeight treatedTargetOutcome targetControlOutcome controlOutcome
    propensityScore controlPrognosticScore controlValue controlEnvelope
    controlEnvelopeLimit hscale_nonneg hcoverTarget hcoverControl
    hmassTarget hmassControl hscoreMeasTargetC hscoreMeasControl
    hcontrol_bound hcontrolEnvelope hcontrolScaledL1

/--
PATT double-score approximation convergence at ordinary and scaled rates from
shrinking finite joint cell-mass envelopes and a shrinking scaled joint-cell
mass-difference envelope.
-/
theorem tendsto_pattDoubleScoreApprox_error_zero_and_scaled_zero_of_cell_mass_envelope_bounds
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
    (massLimit massScaleTarget massScaleControl scaledMassScale :
      PropensityCell × PATTProgCell -> Real)
    (massEnvelopeTarget massEnvelopeControl scaledMassEnvelope :
      Index -> Real)
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
    (hmassTarget_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (targetSample index) (targetWeight index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleTarget cell * massEnvelopeTarget index)
    (hmassControl_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (controlSample index) (controlWeight index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleControl cell * massEnvelopeControl index)
    (hscaledMass_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scale index *
            (scoreCellMass (targetSample index) (targetWeight index)
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell -
              scoreCellMass (controlSample index) (controlWeight index)
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell)| ≤
            scaledMassScale cell * scaledMassEnvelope index)
    (hmassEnvelopeTarget :
      Tendsto massEnvelopeTarget l (nhds 0))
    (hmassEnvelopeControl :
      Tendsto massEnvelopeControl l (nhds 0))
    (hscaledMassEnvelope :
      Tendsto scaledMassEnvelope l (nhds 0))
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
        l (nhds 0) ∧
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
  constructor
  · apply
      (tendsto_pattDoubleScoreApprox_error_zero_of_cell_mass_envelope_bounds
        (l := l) (Index := Index) (Unit := Unit)
        (PropensityCell := PropensityCell)
        (PATTProgCell := PATTProgCell))
    all_goals assumption
  · apply
      (tendsto_scaled_pattDoubleScoreApprox_error_zero_of_cell_mass_envelope_bounds
        (l := l) (Index := Index) (Unit := Unit)
        (PropensityCell := PropensityCell)
        (PATTProgCell := PATTProgCell))
    all_goals assumption

/--
Scaled PATT double-score approximation convergence from eventually valid
finite conditions, eventual scale nonnegativity, shrinking finite joint-cell
mass envelopes, and a shrinking scaled joint-cell mass-difference envelope.
-/
theorem tendsto_scaled_pattDoubleScoreApprox_error_zero_of_eventually_cell_mass_envelope_bounds
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
    (massLimit massScaleTarget massScaleControl scaledMassScale :
      PropensityCell × PATTProgCell -> Real)
    (massEnvelopeTarget massEnvelopeControl scaledMassEnvelope :
      Index -> Real)
    (hscale_nonneg : ∀ᶠ index in l, 0 ≤ scale index)
    (hcoverTarget :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          pattDoubleScore (propensityScore index)
            (controlPrognosticScore index) unit ∈ cells)
    (hcoverControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          pattDoubleScore (propensityScore index)
            (controlPrognosticScore index) unit ∈ cells)
    (hmassTarget :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
          scoreCellMass (targetSample index) (targetWeight index)
            (pattDoubleScore (propensityScore index)
              (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
          scoreCellMass (controlSample index) (controlWeight index)
            (pattDoubleScore (propensityScore index)
              (controlPrognosticScore index)) cell ≠ 0)
    (hmassTarget_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (targetSample index) (targetWeight index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleTarget cell * massEnvelopeTarget index)
    (hmassControl_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (controlSample index) (controlWeight index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleControl cell * massEnvelopeControl index)
    (hscaledMass_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scale index *
            (scoreCellMass (targetSample index) (targetWeight index)
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell -
              scoreCellMass (controlSample index) (controlWeight index)
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell)| ≤
            scaledMassScale cell * scaledMassEnvelope index)
    (hmassEnvelopeTarget :
      Tendsto massEnvelopeTarget l (nhds 0))
    (hmassEnvelopeControl :
      Tendsto massEnvelopeControl l (nhds 0))
    (hscaledMassEnvelope :
      Tendsto scaledMassEnvelope l (nhds 0))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
    (hscoreMeasTargetC :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          targetControlOutcome index unit =
            controlValue index (controlPrognosticScore index unit))
    (hscoreMeasControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          controlOutcome index unit =
            controlValue index (controlPrognosticScore index unit))
    (hcontrol_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
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
    tendsto_scaled_l1PATTDoubleScoreShareDistance_zero_of_eventually_cell_mass_envelopes
      (l := l) cells scale targetSample controlSample targetWeight
      controlWeight propensityScore controlPrognosticScore massLimit
      massScaleTarget massScaleControl scaledMassScale massEnvelopeTarget
      massEnvelopeControl scaledMassEnvelope hscale_nonneg hcoverTarget
      hcoverControl hmassTarget_bound hmassControl_bound hscaledMass_bound
      hmassEnvelopeTarget hmassEnvelopeControl hscaledMassEnvelope
      htotalLimit
  exact tendsto_scaled_pattDoubleScoreApprox_error_zero_of_eventually_scaled_l1_and_envelope
    scale targetSample controlSample (fun _index => cells) targetWeight
    controlWeight treatedTargetOutcome targetControlOutcome controlOutcome
    propensityScore controlPrognosticScore controlValue controlEnvelope
    controlEnvelopeLimit hscale_nonneg hcoverTarget hcoverControl
    hmassTarget hmassControl hscoreMeasTargetC hscoreMeasControl
    hcontrol_bound hcontrolEnvelope hcontrolScaledL1

/--
PATT double-score approximation convergence at ordinary and scaled rates from
eventually valid finite conditions, eventual scale nonnegativity, shrinking
finite joint-cell mass envelopes, and a shrinking scaled joint-cell
mass-difference envelope.
-/
theorem tendsto_pattDoubleScoreApprox_error_zero_and_scaled_zero_of_eventually_cell_mass_envelope_bounds
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
    (massLimit massScaleTarget massScaleControl scaledMassScale :
      PropensityCell × PATTProgCell -> Real)
    (massEnvelopeTarget massEnvelopeControl scaledMassEnvelope :
      Index -> Real)
    (hscale_nonneg : ∀ᶠ index in l, 0 ≤ scale index)
    (hcoverTarget :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          pattDoubleScore (propensityScore index)
            (controlPrognosticScore index) unit ∈ cells)
    (hcoverControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          pattDoubleScore (propensityScore index)
            (controlPrognosticScore index) unit ∈ cells)
    (hmassTarget :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
          scoreCellMass (targetSample index) (targetWeight index)
            (pattDoubleScore (propensityScore index)
              (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
          scoreCellMass (controlSample index) (controlWeight index)
            (pattDoubleScore (propensityScore index)
              (controlPrognosticScore index)) cell ≠ 0)
    (hmassTarget_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (targetSample index) (targetWeight index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleTarget cell * massEnvelopeTarget index)
    (hmassControl_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (controlSample index) (controlWeight index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleControl cell * massEnvelopeControl index)
    (hscaledMass_bound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scale index *
            (scoreCellMass (targetSample index) (targetWeight index)
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell -
              scoreCellMass (controlSample index) (controlWeight index)
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell)| ≤
            scaledMassScale cell * scaledMassEnvelope index)
    (hmassEnvelopeTarget :
      Tendsto massEnvelopeTarget l (nhds 0))
    (hmassEnvelopeControl :
      Tendsto massEnvelopeControl l (nhds 0))
    (hscaledMassEnvelope :
      Tendsto scaledMassEnvelope l (nhds 0))
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0)
    (hscoreMeasTargetC :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          targetControlOutcome index unit =
            controlValue index (controlPrognosticScore index unit))
    (hscoreMeasControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          controlOutcome index unit =
            controlValue index (controlPrognosticScore index unit))
    (hcontrol_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
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
        l (nhds 0) ∧
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
  constructor
  · apply
      (tendsto_pattDoubleScoreApprox_error_zero_of_eventually_cell_mass_envelope_bounds
        (l := l) (Index := Index) (Unit := Unit)
        (PropensityCell := PropensityCell)
        (PATTProgCell := PATTProgCell))
    all_goals assumption
  · apply
      (tendsto_scaled_pattDoubleScoreApprox_error_zero_of_eventually_cell_mass_envelope_bounds
        (l := l) (Index := Index) (Unit := Unit)
        (PropensityCell := PropensityCell)
        (PATTProgCell := PATTProgCell))
    all_goals assumption

/--
Paired PATE/PATT double-score approximation convergence at ordinary and
scaled rates from shrinking finite joint cell-mass envelopes.

The target/control samples, target outcomes, propensity score, and scale are
shared, while the PATE and PATT prognostic-score partitions and mass envelopes
remain separate.
-/
theorem tendsto_pate_pattDoubleScoreApprox_error_zero_and_scaled_zero_of_cell_mass_envelope_bounds
    (scale : Index -> Real)
    (targetSample treatedSample controlSample : Index -> Finset Unit)
    (pateCells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (pattCells : Finset (PropensityCell × PATTProgCell))
    (targetWeight treatedWeight controlWeight : Index -> Unit -> Real)
    (targetOutcomeT targetOutcomeC treatedOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (pateControlPrognosticScore : Index -> Unit -> ControlProgCell)
    (pattControlPrognosticScore : Index -> Unit -> PATTProgCell)
    (treatedValue : Index -> TreatedProgCell -> Real)
    (pateControlValue : Index -> ControlProgCell -> Real)
    (pattControlValue : Index -> PATTProgCell -> Real)
    (treatedEnvelope pateControlEnvelope pattControlEnvelope : Index -> Real)
    (treatedEnvelopeLimit pateControlEnvelopeLimit pattControlEnvelopeLimit :
      Real)
    (pateMassLimit pateMassScaleTarget pateMassScaleTreated
      pateMassScaleControl :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (pateScaledMassScaleTreated pateScaledMassScaleControl :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (pattMassLimit pattMassScaleTarget pattMassScaleControl
      pattScaledMassScale :
      PropensityCell × PATTProgCell -> Real)
    (pateMassEnvelopeTarget pateMassEnvelopeTreated pateMassEnvelopeControl :
      Index -> Real)
    (pateScaledMassEnvelopeTreated pateScaledMassEnvelopeControl :
      Index -> Real)
    (pattMassEnvelopeTarget pattMassEnvelopeControl pattScaledMassEnvelope :
      Index -> Real)
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hpateCoverTarget :
      ∀ index unit, unit ∈ targetSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (pateControlPrognosticScore index) unit ∈ pateCells)
    (hpateCoverTreated :
      ∀ index unit, unit ∈ treatedSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (pateControlPrognosticScore index) unit ∈ pateCells)
    (hpateCoverControl :
      ∀ index unit, unit ∈ controlSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (pateControlPrognosticScore index) unit ∈ pateCells)
    (hpattCoverTarget :
      ∀ index unit, unit ∈ targetSample index ->
        pattDoubleScore (propensityScore index)
          (pattControlPrognosticScore index) unit ∈ pattCells)
    (hpattCoverControl :
      ∀ index unit, unit ∈ controlSample index ->
        pattDoubleScore (propensityScore index)
          (pattControlPrognosticScore index) unit ∈ pattCells)
    (hpateMassTarget :
      ∀ index cell, cell ∈ pateCells ->
        scoreCellMass (targetSample index) (targetWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (pateControlPrognosticScore index)) cell ≠ 0)
    (hpateMassTreated :
      ∀ index cell, cell ∈ pateCells ->
        scoreCellMass (treatedSample index) (treatedWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (pateControlPrognosticScore index)) cell ≠ 0)
    (hpateMassControl :
      ∀ index cell, cell ∈ pateCells ->
        scoreCellMass (controlSample index) (controlWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (pateControlPrognosticScore index)) cell ≠ 0)
    (hpattMassTarget :
      ∀ index cell, cell ∈ pattCells ->
        scoreCellMass (targetSample index) (targetWeight index)
          (pattDoubleScore (propensityScore index)
            (pattControlPrognosticScore index)) cell ≠ 0)
    (hpattMassControl :
      ∀ index cell, cell ∈ pattCells ->
        scoreCellMass (controlSample index) (controlWeight index)
          (pattDoubleScore (propensityScore index)
            (pattControlPrognosticScore index)) cell ≠ 0)
    (hpateMassTarget_bound :
      ∀ cell, cell ∈ pateCells ->
        ∀ᶠ index in l,
          |scoreCellMass (targetSample index) (targetWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (pateControlPrognosticScore index)) cell -
            pateMassLimit cell| ≤
            pateMassScaleTarget cell * pateMassEnvelopeTarget index)
    (hpateMassTreated_bound :
      ∀ cell, cell ∈ pateCells ->
        ∀ᶠ index in l,
          |scoreCellMass (treatedSample index) (treatedWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (pateControlPrognosticScore index)) cell -
            pateMassLimit cell| ≤
            pateMassScaleTreated cell * pateMassEnvelopeTreated index)
    (hpateMassControl_bound :
      ∀ cell, cell ∈ pateCells ->
        ∀ᶠ index in l,
          |scoreCellMass (controlSample index) (controlWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (pateControlPrognosticScore index)) cell -
            pateMassLimit cell| ≤
            pateMassScaleControl cell * pateMassEnvelopeControl index)
    (hpateScaledMassTreated_bound :
      ∀ cell, cell ∈ pateCells ->
        ∀ᶠ index in l,
          |scale index *
            (scoreCellMass (targetSample index) (targetWeight index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (pateControlPrognosticScore index)) cell -
              scoreCellMass (treatedSample index) (treatedWeight index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (pateControlPrognosticScore index)) cell)| ≤
            pateScaledMassScaleTreated cell *
              pateScaledMassEnvelopeTreated index)
    (hpateScaledMassControl_bound :
      ∀ cell, cell ∈ pateCells ->
        ∀ᶠ index in l,
          |scale index *
            (scoreCellMass (targetSample index) (targetWeight index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (pateControlPrognosticScore index)) cell -
              scoreCellMass (controlSample index) (controlWeight index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (pateControlPrognosticScore index)) cell)| ≤
            pateScaledMassScaleControl cell *
              pateScaledMassEnvelopeControl index)
    (hpattMassTarget_bound :
      ∀ cell, cell ∈ pattCells ->
        ∀ᶠ index in l,
          |scoreCellMass (targetSample index) (targetWeight index)
              (pattDoubleScore (propensityScore index)
                (pattControlPrognosticScore index)) cell -
            pattMassLimit cell| ≤
            pattMassScaleTarget cell * pattMassEnvelopeTarget index)
    (hpattMassControl_bound :
      ∀ cell, cell ∈ pattCells ->
        ∀ᶠ index in l,
          |scoreCellMass (controlSample index) (controlWeight index)
              (pattDoubleScore (propensityScore index)
                (pattControlPrognosticScore index)) cell -
            pattMassLimit cell| ≤
            pattMassScaleControl cell * pattMassEnvelopeControl index)
    (hpattScaledMass_bound :
      ∀ cell, cell ∈ pattCells ->
        ∀ᶠ index in l,
          |scale index *
            (scoreCellMass (targetSample index) (targetWeight index)
                (pattDoubleScore (propensityScore index)
                  (pattControlPrognosticScore index)) cell -
              scoreCellMass (controlSample index) (controlWeight index)
                (pattDoubleScore (propensityScore index)
                  (pattControlPrognosticScore index)) cell)| ≤
            pattScaledMassScale cell * pattScaledMassEnvelope index)
    (hpateMassEnvelopeTarget :
      Tendsto pateMassEnvelopeTarget l (nhds 0))
    (hpateMassEnvelopeTreated :
      Tendsto pateMassEnvelopeTreated l (nhds 0))
    (hpateMassEnvelopeControl :
      Tendsto pateMassEnvelopeControl l (nhds 0))
    (hpateScaledMassEnvelopeTreated :
      Tendsto pateScaledMassEnvelopeTreated l (nhds 0))
    (hpateScaledMassEnvelopeControl :
      Tendsto pateScaledMassEnvelopeControl l (nhds 0))
    (hpattMassEnvelopeTarget :
      Tendsto pattMassEnvelopeTarget l (nhds 0))
    (hpattMassEnvelopeControl :
      Tendsto pattMassEnvelopeControl l (nhds 0))
    (hpattScaledMassEnvelope :
      Tendsto pattScaledMassEnvelope l (nhds 0))
    (hpateTotalLimit : (∑ cell ∈ pateCells, pateMassLimit cell) ≠ 0)
    (hpattTotalLimit : (∑ cell ∈ pattCells, pattMassLimit cell) ≠ 0)
    (hpateScoreMeasTargetT :
      ∀ index unit, unit ∈ targetSample index ->
        targetOutcomeT index unit =
          treatedValue index (treatedPrognosticScore index unit))
    (hpateScoreMeasTreated :
      ∀ index unit, unit ∈ treatedSample index ->
        treatedOutcome index unit =
          treatedValue index (treatedPrognosticScore index unit))
    (hpateScoreMeasTargetC :
      ∀ index unit, unit ∈ targetSample index ->
        targetOutcomeC index unit =
          pateControlValue index (pateControlPrognosticScore index unit))
    (hpateScoreMeasControl :
      ∀ index unit, unit ∈ controlSample index ->
        controlOutcome index unit =
          pateControlValue index (pateControlPrognosticScore index unit))
    (hpattScoreMeasTargetC :
      ∀ index unit, unit ∈ targetSample index ->
        targetOutcomeC index unit =
          pattControlValue index (pattControlPrognosticScore index unit))
    (hpattScoreMeasControl :
      ∀ index unit, unit ∈ controlSample index ->
        controlOutcome index unit =
          pattControlValue index (pattControlPrognosticScore index unit))
    (htreated_bound :
      ∀ index cell, cell ∈ pateCells ->
        |treatedCellValueOnPATEDoubleScore (treatedValue index) cell| ≤
          treatedEnvelope index)
    (hpateControl_bound :
      ∀ index cell, cell ∈ pateCells ->
        |controlCellValueOnPATEDoubleScore
            (pateControlValue index) cell| ≤
          pateControlEnvelope index)
    (hpattControl_bound :
      ∀ index cell, cell ∈ pattCells ->
        |controlCellValueOnPATTDoubleScore
            (pattControlValue index) cell| ≤
          pattControlEnvelope index)
    (htreatedEnvelope :
      Tendsto treatedEnvelope l (nhds treatedEnvelopeLimit))
    (hpateControlEnvelope :
      Tendsto pateControlEnvelope l (nhds pateControlEnvelopeLimit))
    (hpattControlEnvelope :
      Tendsto pattControlEnvelope l (nhds pattControlEnvelopeLimit)) :
    (Tendsto
        (fun index =>
          weightedSampleMeanContrast (targetSample index)
            (targetWeight index) (targetOutcomeT index)
            (targetOutcomeC index) -
          twoArmWeightedMeanContrast (treatedSample index)
            (controlSample index) (treatedWeight index)
            (controlWeight index) (treatedOutcome index)
            (controlOutcome index))
        l (nhds 0) ∧
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
        l (nhds 0)) ∧
      (Tendsto
        (fun index =>
          weightedSampleMeanContrast (targetSample index)
            (targetWeight index) (targetOutcomeT index)
            (targetOutcomeC index) -
          pattWeightedMeanContrast (targetSample index) (controlSample index)
            (targetWeight index) (controlWeight index)
            (targetOutcomeT index) (controlOutcome index))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleMeanContrast (targetSample index)
              (targetWeight index) (targetOutcomeT index)
              (targetOutcomeC index) -
            pattWeightedMeanContrast (targetSample index)
              (controlSample index) (targetWeight index)
              (controlWeight index) (targetOutcomeT index)
              (controlOutcome index)))
        l (nhds 0)) := by
  constructor
  · apply
      (tendsto_pateDoubleScoreApprox_error_zero_and_scaled_zero_of_cell_mass_envelope_bounds
        (l := l) (Index := Index) (Unit := Unit)
        (PropensityCell := PropensityCell)
        (TreatedProgCell := TreatedProgCell)
        (ControlProgCell := ControlProgCell))
    all_goals assumption
  · apply
      (tendsto_pattDoubleScoreApprox_error_zero_and_scaled_zero_of_cell_mass_envelope_bounds
        (l := l) (Index := Index) (Unit := Unit)
        (PropensityCell := PropensityCell)
        (PATTProgCell := PATTProgCell))
    all_goals assumption

/--
Paired PATE/PATT double-score approximation convergence at ordinary and
scaled rates from eventually valid finite joint cell-mass envelopes.

This is the asymptotic-ready version of the finite cell-mass envelope route:
finite score support, positive cell masses, score-measurability, and bounded
cell values only need to hold eventually along the index filter.
-/
theorem tendsto_pate_pattDoubleScoreApprox_error_zero_and_scaled_zero_of_eventually_cell_mass_envelope_bounds
    (scale : Index -> Real)
    (targetSample treatedSample controlSample : Index -> Finset Unit)
    (pateCells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (pattCells : Finset (PropensityCell × PATTProgCell))
    (targetWeight treatedWeight controlWeight : Index -> Unit -> Real)
    (targetOutcomeT targetOutcomeC treatedOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (pateControlPrognosticScore : Index -> Unit -> ControlProgCell)
    (pattControlPrognosticScore : Index -> Unit -> PATTProgCell)
    (treatedValue : Index -> TreatedProgCell -> Real)
    (pateControlValue : Index -> ControlProgCell -> Real)
    (pattControlValue : Index -> PATTProgCell -> Real)
    (treatedEnvelope pateControlEnvelope pattControlEnvelope : Index -> Real)
    (treatedEnvelopeLimit pateControlEnvelopeLimit pattControlEnvelopeLimit :
      Real)
    (pateMassLimit pateMassScaleTarget pateMassScaleTreated
      pateMassScaleControl :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (pateScaledMassScaleTreated pateScaledMassScaleControl :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (pattMassLimit pattMassScaleTarget pattMassScaleControl
      pattScaledMassScale :
      PropensityCell × PATTProgCell -> Real)
    (pateMassEnvelopeTarget pateMassEnvelopeTreated pateMassEnvelopeControl :
      Index -> Real)
    (pateScaledMassEnvelopeTreated pateScaledMassEnvelopeControl :
      Index -> Real)
    (pattMassEnvelopeTarget pattMassEnvelopeControl pattScaledMassEnvelope :
      Index -> Real)
    (hscale_nonneg : ∀ᶠ index in l, 0 ≤ scale index)
    (hpateCoverTarget :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (pateControlPrognosticScore index) unit ∈ pateCells)
    (hpateCoverTreated :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ treatedSample index ->
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (pateControlPrognosticScore index) unit ∈ pateCells)
    (hpateCoverControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (pateControlPrognosticScore index) unit ∈ pateCells)
    (hpattCoverTarget :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          pattDoubleScore (propensityScore index)
            (pattControlPrognosticScore index) unit ∈ pattCells)
    (hpattCoverControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          pattDoubleScore (propensityScore index)
            (pattControlPrognosticScore index) unit ∈ pattCells)
    (hpateMassTarget :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ pateCells ->
          scoreCellMass (targetSample index) (targetWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index)
              (pateControlPrognosticScore index)) cell ≠ 0)
    (hpateMassTreated :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ pateCells ->
          scoreCellMass (treatedSample index) (treatedWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index)
              (pateControlPrognosticScore index)) cell ≠ 0)
    (hpateMassControl :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ pateCells ->
          scoreCellMass (controlSample index) (controlWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index)
              (pateControlPrognosticScore index)) cell ≠ 0)
    (hpattMassTarget :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ pattCells ->
          scoreCellMass (targetSample index) (targetWeight index)
            (pattDoubleScore (propensityScore index)
              (pattControlPrognosticScore index)) cell ≠ 0)
    (hpattMassControl :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ pattCells ->
          scoreCellMass (controlSample index) (controlWeight index)
            (pattDoubleScore (propensityScore index)
              (pattControlPrognosticScore index)) cell ≠ 0)
    (hpateMassTarget_bound :
      ∀ cell, cell ∈ pateCells ->
        ∀ᶠ index in l,
          |scoreCellMass (targetSample index) (targetWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (pateControlPrognosticScore index)) cell -
            pateMassLimit cell| ≤
            pateMassScaleTarget cell * pateMassEnvelopeTarget index)
    (hpateMassTreated_bound :
      ∀ cell, cell ∈ pateCells ->
        ∀ᶠ index in l,
          |scoreCellMass (treatedSample index) (treatedWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (pateControlPrognosticScore index)) cell -
            pateMassLimit cell| ≤
            pateMassScaleTreated cell * pateMassEnvelopeTreated index)
    (hpateMassControl_bound :
      ∀ cell, cell ∈ pateCells ->
        ∀ᶠ index in l,
          |scoreCellMass (controlSample index) (controlWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (pateControlPrognosticScore index)) cell -
            pateMassLimit cell| ≤
            pateMassScaleControl cell * pateMassEnvelopeControl index)
    (hpateScaledMassTreated_bound :
      ∀ cell, cell ∈ pateCells ->
        ∀ᶠ index in l,
          |scale index *
            (scoreCellMass (targetSample index) (targetWeight index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (pateControlPrognosticScore index)) cell -
              scoreCellMass (treatedSample index) (treatedWeight index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (pateControlPrognosticScore index)) cell)| ≤
            pateScaledMassScaleTreated cell *
              pateScaledMassEnvelopeTreated index)
    (hpateScaledMassControl_bound :
      ∀ cell, cell ∈ pateCells ->
        ∀ᶠ index in l,
          |scale index *
            (scoreCellMass (targetSample index) (targetWeight index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (pateControlPrognosticScore index)) cell -
              scoreCellMass (controlSample index) (controlWeight index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (pateControlPrognosticScore index)) cell)| ≤
            pateScaledMassScaleControl cell *
              pateScaledMassEnvelopeControl index)
    (hpattMassTarget_bound :
      ∀ cell, cell ∈ pattCells ->
        ∀ᶠ index in l,
          |scoreCellMass (targetSample index) (targetWeight index)
              (pattDoubleScore (propensityScore index)
                (pattControlPrognosticScore index)) cell -
            pattMassLimit cell| ≤
            pattMassScaleTarget cell * pattMassEnvelopeTarget index)
    (hpattMassControl_bound :
      ∀ cell, cell ∈ pattCells ->
        ∀ᶠ index in l,
          |scoreCellMass (controlSample index) (controlWeight index)
              (pattDoubleScore (propensityScore index)
                (pattControlPrognosticScore index)) cell -
            pattMassLimit cell| ≤
            pattMassScaleControl cell * pattMassEnvelopeControl index)
    (hpattScaledMass_bound :
      ∀ cell, cell ∈ pattCells ->
        ∀ᶠ index in l,
          |scale index *
            (scoreCellMass (targetSample index) (targetWeight index)
                (pattDoubleScore (propensityScore index)
                  (pattControlPrognosticScore index)) cell -
              scoreCellMass (controlSample index) (controlWeight index)
                (pattDoubleScore (propensityScore index)
                  (pattControlPrognosticScore index)) cell)| ≤
            pattScaledMassScale cell * pattScaledMassEnvelope index)
    (hpateMassEnvelopeTarget :
      Tendsto pateMassEnvelopeTarget l (nhds 0))
    (hpateMassEnvelopeTreated :
      Tendsto pateMassEnvelopeTreated l (nhds 0))
    (hpateMassEnvelopeControl :
      Tendsto pateMassEnvelopeControl l (nhds 0))
    (hpateScaledMassEnvelopeTreated :
      Tendsto pateScaledMassEnvelopeTreated l (nhds 0))
    (hpateScaledMassEnvelopeControl :
      Tendsto pateScaledMassEnvelopeControl l (nhds 0))
    (hpattMassEnvelopeTarget :
      Tendsto pattMassEnvelopeTarget l (nhds 0))
    (hpattMassEnvelopeControl :
      Tendsto pattMassEnvelopeControl l (nhds 0))
    (hpattScaledMassEnvelope :
      Tendsto pattScaledMassEnvelope l (nhds 0))
    (hpateTotalLimit : (∑ cell ∈ pateCells, pateMassLimit cell) ≠ 0)
    (hpattTotalLimit : (∑ cell ∈ pattCells, pattMassLimit cell) ≠ 0)
    (hpateScoreMeasTargetT :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          targetOutcomeT index unit =
            treatedValue index (treatedPrognosticScore index unit))
    (hpateScoreMeasTreated :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ treatedSample index ->
          treatedOutcome index unit =
            treatedValue index (treatedPrognosticScore index unit))
    (hpateScoreMeasTargetC :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          targetOutcomeC index unit =
            pateControlValue index (pateControlPrognosticScore index unit))
    (hpateScoreMeasControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          controlOutcome index unit =
            pateControlValue index (pateControlPrognosticScore index unit))
    (hpattScoreMeasTargetC :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          targetOutcomeC index unit =
            pattControlValue index (pattControlPrognosticScore index unit))
    (hpattScoreMeasControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          controlOutcome index unit =
            pattControlValue index (pattControlPrognosticScore index unit))
    (htreated_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ pateCells ->
          |treatedCellValueOnPATEDoubleScore (treatedValue index) cell| ≤
            treatedEnvelope index)
    (hpateControl_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ pateCells ->
          |controlCellValueOnPATEDoubleScore
              (pateControlValue index) cell| ≤
            pateControlEnvelope index)
    (hpattControl_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ pattCells ->
          |controlCellValueOnPATTDoubleScore
              (pattControlValue index) cell| ≤
            pattControlEnvelope index)
    (htreatedEnvelope :
      Tendsto treatedEnvelope l (nhds treatedEnvelopeLimit))
    (hpateControlEnvelope :
      Tendsto pateControlEnvelope l (nhds pateControlEnvelopeLimit))
    (hpattControlEnvelope :
      Tendsto pattControlEnvelope l (nhds pattControlEnvelopeLimit)) :
    (Tendsto
        (fun index =>
          weightedSampleMeanContrast (targetSample index)
            (targetWeight index) (targetOutcomeT index)
            (targetOutcomeC index) -
          twoArmWeightedMeanContrast (treatedSample index)
            (controlSample index) (treatedWeight index)
            (controlWeight index) (treatedOutcome index)
            (controlOutcome index))
        l (nhds 0) ∧
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
        l (nhds 0)) ∧
      (Tendsto
        (fun index =>
          weightedSampleMeanContrast (targetSample index)
            (targetWeight index) (targetOutcomeT index)
            (targetOutcomeC index) -
          pattWeightedMeanContrast (targetSample index) (controlSample index)
            (targetWeight index) (controlWeight index)
            (targetOutcomeT index) (controlOutcome index))
        l (nhds 0) ∧
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleMeanContrast (targetSample index)
              (targetWeight index) (targetOutcomeT index)
              (targetOutcomeC index) -
            pattWeightedMeanContrast (targetSample index)
              (controlSample index) (targetWeight index)
              (controlWeight index) (targetOutcomeT index)
              (controlOutcome index)))
        l (nhds 0)) := by
  constructor
  · apply
      (tendsto_pateDoubleScoreApprox_error_zero_and_scaled_zero_of_eventually_cell_mass_envelope_bounds
        (l := l) (Index := Index) (Unit := Unit)
        (PropensityCell := PropensityCell)
        (TreatedProgCell := TreatedProgCell)
        (ControlProgCell := ControlProgCell))
    all_goals assumption
  · apply
      (tendsto_pattDoubleScoreApprox_error_zero_and_scaled_zero_of_eventually_cell_mass_envelope_bounds
        (l := l) (Index := Index) (Unit := Unit)
        (PropensityCell := PropensityCell)
        (PATTProgCell := PATTProgCell))
    all_goals assumption

end WDSM
end Matching
end StatInference
