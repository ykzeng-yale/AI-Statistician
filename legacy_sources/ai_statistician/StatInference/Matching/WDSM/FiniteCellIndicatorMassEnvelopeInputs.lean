import StatInference.Matching.WDSM.FiniteCellMassEnvelopeBridge
import StatInference.Matching.WDSM.FiniteCellIndicatorEventuallyIndicatorConvergence

/-!
# Indicator-sum inputs from finite cell-mass envelopes

The WDSM approximation interfaces consume weighted indicator-sum LLNs and
scaled indicator-sum difference limits.  Concrete survey arguments often
produce the equivalent statements as score-cell mass envelopes.  This module
packages that deterministic conversion for PATE and PATT double-score cells.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index UnitA UnitB Cell : Type*} {l : Filter Index}
  [DecidableEq Cell]

/--
Cellwise scaled weighted-indicator differences vanish when the equivalent
scaled score-cell mass differences are eventually bounded by a shrinking
finite-cell envelope.
-/
theorem cellwiseScaledWeightedIndicatorSumDifference_zero_of_scoreCellMass_envelope
    (cells : Finset Cell) (scale : Index -> Real)
    (sampleA : Index -> Finset UnitA) (sampleB : Index -> Finset UnitB)
    (weightA : Index -> UnitA -> Real)
    (weightB : Index -> UnitB -> Real)
    (scoreA : Index -> UnitA -> Cell)
    (scoreB : Index -> UnitB -> Cell)
    (scaledCellScale : Cell -> Real)
    (scaledEnvelope : Index -> Real)
    (hscaledBound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scale index *
            (scoreCellMass (sampleA index) (weightA index)
                (scoreA index) cell -
              scoreCellMass (sampleB index) (weightB index)
                (scoreB index) cell)| ≤
            scaledCellScale cell * scaledEnvelope index)
    (hscaledEnvelope :
      Tendsto scaledEnvelope l (nhds 0)) :
    ∀ cell, cell ∈ cells ->
      Tendsto
        (fun index =>
          scale index *
            (weightedSampleSum (sampleA index) (weightA index)
                (scoreCellIndicator (scoreA index) cell) -
              weightedSampleSum (sampleB index) (weightB index)
                (scoreCellIndicator (scoreB index) cell)))
        l (nhds 0) := by
  intro cell hcell
  have hmass :
      Tendsto
        (fun index =>
          scale index *
            (scoreCellMass (sampleA index) (weightA index)
                (scoreA index) cell -
              scoreCellMass (sampleB index) (weightB index)
                (scoreB index) cell))
        l (nhds 0) :=
    tendsto_zero_of_eventually_abs_le_bound
      (fun index =>
        scale index *
          (scoreCellMass (sampleA index) (weightA index)
              (scoreA index) cell -
            scoreCellMass (sampleB index) (weightB index)
              (scoreB index) cell))
      (fun index => scaledCellScale cell * scaledEnvelope index)
      (hscaledBound cell hcell)
      (by
        simpa using
          ((tendsto_const_nhds :
            Tendsto (fun _index : Index => scaledCellScale cell) l
              (nhds (scaledCellScale cell))).mul hscaledEnvelope))
  exact hmass.congr' <|
    Eventually.of_forall fun index =>
      scaled_scoreCellMass_sub_eq_scaled_weightedSampleSum_indicator_sub
        (scale index) (sampleA index) (sampleB index) (weightA index)
        (weightB index) (scoreA index) (scoreB index) cell

variable {Unit PropensityCell TreatedProgCell ControlProgCell PATTProgCell : Type*}
  [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
  [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]

/--
PATE weighted indicator-sum LLN inputs from shrinking score-cell mass
envelopes for the target, treated, and control samples.
-/
theorem pate_weighted_indicator_sum_lln_of_scoreCellMass_envelopes
    (targetSample treatedSample controlSample : Index -> Finset Unit)
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (targetWeight treatedWeight controlWeight : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (massLimit massScaleTarget massScaleTreated massScaleControl :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (massEnvelopeTarget massEnvelopeTreated massEnvelopeControl :
      Index -> Real)
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
      Tendsto massEnvelopeControl l (nhds 0)) :
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
        l (nhds (massLimit cell))) := by
  exact
    ⟨cellwiseWeightedIndicatorSumLLN_of_eventually_abs_scoreCellMass_sub_le_envelope
        (l := l) cells targetSample targetWeight
        (fun index =>
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index))
        massLimit massScaleTarget massEnvelopeTarget hmassTarget_bound
        hmassEnvelopeTarget,
      cellwiseWeightedIndicatorSumLLN_of_eventually_abs_scoreCellMass_sub_le_envelope
        (l := l) cells treatedSample treatedWeight
        (fun index =>
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index))
        massLimit massScaleTreated massEnvelopeTreated hmassTreated_bound
        hmassEnvelopeTreated,
      cellwiseWeightedIndicatorSumLLN_of_eventually_abs_scoreCellMass_sub_le_envelope
        (l := l) cells controlSample controlWeight
        (fun index =>
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index))
        massLimit massScaleControl massEnvelopeControl hmassControl_bound
        hmassEnvelopeControl⟩

/--
Scaled PATE indicator-difference inputs from shrinking scaled score-cell mass
difference envelopes for target-versus-treated and target-versus-control
cells.
-/
theorem pate_scaled_indicator_difference_zero_of_scoreCellMass_envelopes
    (scale : Index -> Real)
    (targetSample treatedSample controlSample : Index -> Finset Unit)
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (targetWeight treatedWeight controlWeight : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (scaledMassScaleTreated scaledMassScaleControl :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (scaledMassEnvelopeTreated scaledMassEnvelopeControl : Index -> Real)
    (hscaledTreated_bound :
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
    (hscaledControl_bound :
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
    (hscaledMassEnvelopeTreated :
      Tendsto scaledMassEnvelopeTreated l (nhds 0))
    (hscaledMassEnvelopeControl :
      Tendsto scaledMassEnvelopeControl l (nhds 0)) :
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
        l (nhds 0)) := by
  exact
    ⟨cellwiseScaledWeightedIndicatorSumDifference_zero_of_scoreCellMass_envelope
        (l := l) cells scale targetSample treatedSample targetWeight
        treatedWeight
        (fun index =>
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index))
        (fun index =>
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index))
        scaledMassScaleTreated scaledMassEnvelopeTreated
        hscaledTreated_bound hscaledMassEnvelopeTreated,
      cellwiseScaledWeightedIndicatorSumDifference_zero_of_scoreCellMass_envelope
        (l := l) cells scale targetSample controlSample targetWeight
        controlWeight
        (fun index =>
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index))
        (fun index =>
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index))
        scaledMassScaleControl scaledMassEnvelopeControl
        hscaledControl_bound hscaledMassEnvelopeControl⟩

/--
PATT weighted indicator-sum LLN inputs from shrinking score-cell mass
envelopes for the target and control samples.
-/
theorem patt_weighted_indicator_sum_lln_of_scoreCellMass_envelopes
    (targetSample controlSample : Index -> Finset Unit)
    (cells : Finset (PropensityCell × PATTProgCell))
    (targetWeight controlWeight : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (massLimit massScaleTarget massScaleControl :
      PropensityCell × PATTProgCell -> Real)
    (massEnvelopeTarget massEnvelopeControl : Index -> Real)
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
      Tendsto massEnvelopeControl l (nhds 0)) :
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
        l (nhds (massLimit cell))) := by
  exact
    ⟨cellwiseWeightedIndicatorSumLLN_of_eventually_abs_scoreCellMass_sub_le_envelope
        (l := l) cells targetSample targetWeight
        (fun index =>
          pattDoubleScore (propensityScore index)
            (controlPrognosticScore index))
        massLimit massScaleTarget massEnvelopeTarget hmassTarget_bound
        hmassEnvelopeTarget,
      cellwiseWeightedIndicatorSumLLN_of_eventually_abs_scoreCellMass_sub_le_envelope
        (l := l) cells controlSample controlWeight
        (fun index =>
          pattDoubleScore (propensityScore index)
            (controlPrognosticScore index))
        massLimit massScaleControl massEnvelopeControl hmassControl_bound
        hmassEnvelopeControl⟩

/--
Scaled PATT indicator-difference inputs from a shrinking scaled score-cell
mass difference envelope for target-versus-control cells.
-/
theorem patt_scaled_indicator_difference_zero_of_scoreCellMass_envelope
    (scale : Index -> Real)
    (targetSample controlSample : Index -> Finset Unit)
    (cells : Finset (PropensityCell × PATTProgCell))
    (targetWeight controlWeight : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (scaledMassScale : PropensityCell × PATTProgCell -> Real)
    (scaledMassEnvelope : Index -> Real)
    (hscaled_bound :
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
    (hscaledMassEnvelope :
      Tendsto scaledMassEnvelope l (nhds 0)) :
    ∀ cell, cell ∈ cells ->
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
        l (nhds 0) :=
  cellwiseScaledWeightedIndicatorSumDifference_zero_of_scoreCellMass_envelope
    (l := l) cells scale targetSample controlSample targetWeight
    controlWeight
    (fun index =>
      pattDoubleScore (propensityScore index)
        (controlPrognosticScore index))
    (fun index =>
      pattDoubleScore (propensityScore index)
        (controlPrognosticScore index))
    scaledMassScale scaledMassEnvelope hscaled_bound hscaledMassEnvelope

/--
Concrete PATE indicator-sum bridge whose stochastic input is stated as
shrinking score-cell mass envelopes rather than already-converted weighted
indicator-sum LLNs.
-/
def pateDoubleScoreIndicatorSumConvergenceBridgeOfMassEnvelopeInputs
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
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    PATEDoubleScoreIndicatorSumConvergenceBridge :=
  let base :=
    pateDoubleScoreIndicatorSumConvergenceBridgeOfEventuallyIndicator
      (l := l) targetSample treatedSample controlSample cells
      targetWeight treatedWeight controlWeight targetOutcomeT
      targetOutcomeC treatedOutcome controlOutcome propensityScore
      treatedPrognosticScore controlPrognosticScore treatedValue
      controlValue treatedEnvelope controlEnvelope treatedEnvelopeLimit
      controlEnvelopeLimit massLimit htotalLimit
  { base with
    weighted_indicator_sum_lln :=
      (∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (targetSample index) (targetWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleTarget cell * massEnvelopeTarget index) ∧
      (∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (treatedSample index) (treatedWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleTreated cell * massEnvelopeTreated index) ∧
      (∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (controlSample index) (controlWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleControl cell * massEnvelopeControl index) ∧
      Tendsto massEnvelopeTarget l (nhds 0) ∧
      Tendsto massEnvelopeTreated l (nhds 0) ∧
      Tendsto massEnvelopeControl l (nhds 0)
    bridge := by
      intro hfinite henvelope hmass
      rcases hmass with
        ⟨hmassTarget_bound, hmassTreated_bound, hmassControl_bound,
          hmassEnvelopeTarget, hmassEnvelopeTreated,
          hmassEnvelopeControl⟩
      exact base.bridge hfinite henvelope
        (pate_weighted_indicator_sum_lln_of_scoreCellMass_envelopes
          (l := l) targetSample treatedSample controlSample cells
          targetWeight treatedWeight controlWeight propensityScore
          treatedPrognosticScore controlPrognosticScore massLimit
          massScaleTarget massScaleTreated massScaleControl
          massEnvelopeTarget massEnvelopeTreated massEnvelopeControl
          hmassTarget_bound hmassTreated_bound hmassControl_bound
          hmassEnvelopeTarget hmassEnvelopeTreated hmassEnvelopeControl) }

/--
Concrete scaled PATE indicator-sum bridge whose LLN and scaled-difference
inputs are both stated as score-cell mass-envelope obligations.
-/
def scaledPATEDoubleScoreIndicatorSumConvergenceBridgeOfMassEnvelopeInputs
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
    (massEnvelopeTarget massEnvelopeTreated massEnvelopeControl :
      Index -> Real)
    (scaledMassScaleTreated scaledMassScaleControl :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (scaledMassEnvelopeTreated scaledMassEnvelopeControl : Index -> Real)
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    ScaledPATEDoubleScoreIndicatorSumConvergenceBridge :=
  let base :=
    scaledPATEDoubleScoreIndicatorSumConvergenceBridgeOfEventuallyIndicator
      (l := l) scale targetSample treatedSample controlSample cells
      targetWeight treatedWeight controlWeight targetOutcomeT
      targetOutcomeC treatedOutcome controlOutcome propensityScore
      treatedPrognosticScore controlPrognosticScore treatedValue
      controlValue treatedEnvelope controlEnvelope treatedEnvelopeLimit
      controlEnvelopeLimit massLimit htotalLimit
  { base with
    weighted_indicator_sum_lln :=
      (∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (targetSample index) (targetWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleTarget cell * massEnvelopeTarget index) ∧
      (∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (treatedSample index) (treatedWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleTreated cell * massEnvelopeTreated index) ∧
      (∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (controlSample index) (controlWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleControl cell * massEnvelopeControl index) ∧
      Tendsto massEnvelopeTarget l (nhds 0) ∧
      Tendsto massEnvelopeTreated l (nhds 0) ∧
      Tendsto massEnvelopeControl l (nhds 0)
    scaled_weighted_indicator_sum_difference_clt :=
      (∀ cell, cell ∈ cells ->
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
            scaledMassScaleTreated cell * scaledMassEnvelopeTreated index) ∧
      (∀ cell, cell ∈ cells ->
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
            scaledMassScaleControl cell * scaledMassEnvelopeControl index) ∧
      Tendsto scaledMassEnvelopeTreated l (nhds 0) ∧
      Tendsto scaledMassEnvelopeControl l (nhds 0)
    bridge := by
      intro hfinite henvelope hmass hscaled
      rcases hmass with
        ⟨hmassTarget_bound, hmassTreated_bound, hmassControl_bound,
          hmassEnvelopeTarget, hmassEnvelopeTreated,
          hmassEnvelopeControl⟩
      rcases hscaled with
        ⟨hscaledTreated_bound, hscaledControl_bound,
          hscaledMassEnvelopeTreated, hscaledMassEnvelopeControl⟩
      exact base.bridge hfinite henvelope
        (pate_weighted_indicator_sum_lln_of_scoreCellMass_envelopes
          (l := l) targetSample treatedSample controlSample cells
          targetWeight treatedWeight controlWeight propensityScore
          treatedPrognosticScore controlPrognosticScore massLimit
          massScaleTarget massScaleTreated massScaleControl
          massEnvelopeTarget massEnvelopeTreated massEnvelopeControl
          hmassTarget_bound hmassTreated_bound hmassControl_bound
          hmassEnvelopeTarget hmassEnvelopeTreated hmassEnvelopeControl)
        (pate_scaled_indicator_difference_zero_of_scoreCellMass_envelopes
          (l := l) scale targetSample treatedSample controlSample cells
          targetWeight treatedWeight controlWeight propensityScore
          treatedPrognosticScore controlPrognosticScore
          scaledMassScaleTreated scaledMassScaleControl
          scaledMassEnvelopeTreated scaledMassEnvelopeControl
          hscaledTreated_bound hscaledControl_bound
          hscaledMassEnvelopeTreated hscaledMassEnvelopeControl) }

/--
Concrete PATT indicator-sum bridge whose stochastic input is stated as
shrinking score-cell mass envelopes.
-/
def pattDoubleScoreIndicatorSumConvergenceBridgeOfMassEnvelopeInputs
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
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    PATTDoubleScoreIndicatorSumConvergenceBridge :=
  let base :=
    pattDoubleScoreIndicatorSumConvergenceBridgeOfEventuallyIndicator
      (l := l) targetSample controlSample cells targetWeight
      controlWeight treatedTargetOutcome targetControlOutcome
      controlOutcome propensityScore controlPrognosticScore controlValue
      controlEnvelope controlEnvelopeLimit massLimit htotalLimit
  { base with
    weighted_indicator_sum_lln :=
      (∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (targetSample index) (targetWeight index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleTarget cell * massEnvelopeTarget index) ∧
      (∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (controlSample index) (controlWeight index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleControl cell * massEnvelopeControl index) ∧
      Tendsto massEnvelopeTarget l (nhds 0) ∧
      Tendsto massEnvelopeControl l (nhds 0)
    bridge := by
      intro hfinite henvelope hmass
      rcases hmass with
        ⟨hmassTarget_bound, hmassControl_bound, hmassEnvelopeTarget,
          hmassEnvelopeControl⟩
      exact base.bridge hfinite henvelope
        (patt_weighted_indicator_sum_lln_of_scoreCellMass_envelopes
          (l := l) targetSample controlSample cells targetWeight
          controlWeight propensityScore controlPrognosticScore massLimit
          massScaleTarget massScaleControl massEnvelopeTarget
          massEnvelopeControl hmassTarget_bound hmassControl_bound
          hmassEnvelopeTarget hmassEnvelopeControl) }

/--
Concrete scaled PATT indicator-sum bridge whose LLN and scaled-difference
inputs are both stated as score-cell mass-envelope obligations.
-/
def scaledPATTDoubleScoreIndicatorSumConvergenceBridgeOfMassEnvelopeInputs
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
    (massLimit massScaleTarget massScaleControl :
      PropensityCell × PATTProgCell -> Real)
    (massEnvelopeTarget massEnvelopeControl : Index -> Real)
    (scaledMassScale : PropensityCell × PATTProgCell -> Real)
    (scaledMassEnvelope : Index -> Real)
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    ScaledPATTDoubleScoreIndicatorSumConvergenceBridge :=
  let base :=
    scaledPATTDoubleScoreIndicatorSumConvergenceBridgeOfEventuallyIndicator
      (l := l) scale targetSample controlSample cells targetWeight
      controlWeight treatedTargetOutcome targetControlOutcome
      controlOutcome propensityScore controlPrognosticScore controlValue
      controlEnvelope controlEnvelopeLimit massLimit htotalLimit
  { base with
    weighted_indicator_sum_lln :=
      (∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (targetSample index) (targetWeight index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleTarget cell * massEnvelopeTarget index) ∧
      (∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (controlSample index) (controlWeight index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell - massLimit cell| ≤
            massScaleControl cell * massEnvelopeControl index) ∧
      Tendsto massEnvelopeTarget l (nhds 0) ∧
      Tendsto massEnvelopeControl l (nhds 0)
    scaled_weighted_indicator_sum_difference_clt :=
      (∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scale index *
            (scoreCellMass (targetSample index) (targetWeight index)
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell -
              scoreCellMass (controlSample index) (controlWeight index)
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index)) cell)| ≤
            scaledMassScale cell * scaledMassEnvelope index) ∧
      Tendsto scaledMassEnvelope l (nhds 0)
    bridge := by
      intro hfinite henvelope hmass hscaled
      rcases hmass with
        ⟨hmassTarget_bound, hmassControl_bound, hmassEnvelopeTarget,
          hmassEnvelopeControl⟩
      rcases hscaled with ⟨hscaled_bound, hscaledMassEnvelope⟩
      exact base.bridge hfinite henvelope
        (patt_weighted_indicator_sum_lln_of_scoreCellMass_envelopes
          (l := l) targetSample controlSample cells targetWeight
          controlWeight propensityScore controlPrognosticScore massLimit
          massScaleTarget massScaleControl massEnvelopeTarget
          massEnvelopeControl hmassTarget_bound hmassControl_bound
          hmassEnvelopeTarget hmassEnvelopeControl)
        (patt_scaled_indicator_difference_zero_of_scoreCellMass_envelope
          (l := l) scale targetSample controlSample cells targetWeight
          controlWeight propensityScore controlPrognosticScore
          scaledMassScale scaledMassEnvelope hscaled_bound
          hscaledMassEnvelope) }

/--
The same PATE mass-envelope evidence packages both the ordinary and scaled
double-score indicator-sum bridges.
-/
def pateDoubleScoreIndicatorSumConvergenceBridgesOfMassEnvelopeInputs
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
    (massEnvelopeTarget massEnvelopeTreated massEnvelopeControl :
      Index -> Real)
    (scaledMassScaleTreated scaledMassScaleControl :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (scaledMassEnvelopeTreated scaledMassEnvelopeControl : Index -> Real)
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    PATEDoubleScoreIndicatorSumConvergenceBridge ×
      ScaledPATEDoubleScoreIndicatorSumConvergenceBridge :=
  (pateDoubleScoreIndicatorSumConvergenceBridgeOfMassEnvelopeInputs
      (l := l) targetSample treatedSample controlSample cells
      targetWeight treatedWeight controlWeight targetOutcomeT targetOutcomeC
      treatedOutcome controlOutcome propensityScore treatedPrognosticScore
      controlPrognosticScore treatedValue controlValue treatedEnvelope
      controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit massLimit
      massScaleTarget massScaleTreated massScaleControl massEnvelopeTarget
      massEnvelopeTreated massEnvelopeControl htotalLimit,
    scaledPATEDoubleScoreIndicatorSumConvergenceBridgeOfMassEnvelopeInputs
      (l := l) scale targetSample treatedSample controlSample cells
      targetWeight treatedWeight controlWeight targetOutcomeT targetOutcomeC
      treatedOutcome controlOutcome propensityScore treatedPrognosticScore
      controlPrognosticScore treatedValue controlValue treatedEnvelope
      controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit massLimit
      massScaleTarget massScaleTreated massScaleControl massEnvelopeTarget
      massEnvelopeTreated massEnvelopeControl scaledMassScaleTreated
      scaledMassScaleControl scaledMassEnvelopeTreated
      scaledMassEnvelopeControl htotalLimit)

/--
The same PATT mass-envelope evidence packages both the ordinary and scaled
double-score indicator-sum bridges.
-/
def pattDoubleScoreIndicatorSumConvergenceBridgesOfMassEnvelopeInputs
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
    (massLimit massScaleTarget massScaleControl :
      PropensityCell × PATTProgCell -> Real)
    (massEnvelopeTarget massEnvelopeControl : Index -> Real)
    (scaledMassScale : PropensityCell × PATTProgCell -> Real)
    (scaledMassEnvelope : Index -> Real)
    (htotalLimit : (∑ cell ∈ cells, massLimit cell) ≠ 0) :
    PATTDoubleScoreIndicatorSumConvergenceBridge ×
      ScaledPATTDoubleScoreIndicatorSumConvergenceBridge :=
  (pattDoubleScoreIndicatorSumConvergenceBridgeOfMassEnvelopeInputs
      (l := l) targetSample controlSample cells targetWeight
      controlWeight treatedTargetOutcome targetControlOutcome controlOutcome
      propensityScore controlPrognosticScore controlValue controlEnvelope
      controlEnvelopeLimit massLimit massScaleTarget massScaleControl
      massEnvelopeTarget massEnvelopeControl htotalLimit,
    scaledPATTDoubleScoreIndicatorSumConvergenceBridgeOfMassEnvelopeInputs
      (l := l) scale targetSample controlSample cells targetWeight
      controlWeight treatedTargetOutcome targetControlOutcome controlOutcome
      propensityScore controlPrognosticScore controlValue controlEnvelope
      controlEnvelopeLimit massLimit massScaleTarget massScaleControl
      massEnvelopeTarget massEnvelopeControl scaledMassScale scaledMassEnvelope
      htotalLimit)

/--
Finite-score-alphabet PATE mass-envelope bridge, with the double-score cell set
specialized to `Finset.univ`.
-/
def pateDoubleScoreIndicatorSumConvergenceBridgeOfMassEnvelopeInputs_fintype
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
    (massLimit massScaleTarget massScaleTreated massScaleControl :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (massEnvelopeTarget massEnvelopeTreated massEnvelopeControl :
      Index -> Real)
    (htotalLimit :
      (∑ cell ∈
        (Finset.univ :
          Finset ((PropensityCell × TreatedProgCell) × ControlProgCell)),
        massLimit cell) ≠ 0) :
    PATEDoubleScoreIndicatorSumConvergenceBridge :=
  pateDoubleScoreIndicatorSumConvergenceBridgeOfMassEnvelopeInputs
    (l := l)
    targetSample treatedSample controlSample
    (Finset.univ :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    targetWeight treatedWeight controlWeight targetOutcomeT targetOutcomeC
    treatedOutcome controlOutcome propensityScore treatedPrognosticScore
    controlPrognosticScore treatedValue controlValue treatedEnvelope
    controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit massLimit
    massScaleTarget massScaleTreated massScaleControl massEnvelopeTarget
    massEnvelopeTreated massEnvelopeControl htotalLimit

/--
Finite-score-alphabet scaled PATE mass-envelope bridge, with the double-score
cell set specialized to `Finset.univ`.
-/
def scaledPATEDoubleScoreIndicatorSumConvergenceBridgeOfMassEnvelopeInputs_fintype
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
    (massLimit massScaleTarget massScaleTreated massScaleControl :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (massEnvelopeTarget massEnvelopeTreated massEnvelopeControl :
      Index -> Real)
    (scaledMassScaleTreated scaledMassScaleControl :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (scaledMassEnvelopeTreated scaledMassEnvelopeControl : Index -> Real)
    (htotalLimit :
      (∑ cell ∈
        (Finset.univ :
          Finset ((PropensityCell × TreatedProgCell) × ControlProgCell)),
        massLimit cell) ≠ 0) :
    ScaledPATEDoubleScoreIndicatorSumConvergenceBridge :=
  scaledPATEDoubleScoreIndicatorSumConvergenceBridgeOfMassEnvelopeInputs
    (l := l)
    scale targetSample treatedSample controlSample
    (Finset.univ :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    targetWeight treatedWeight controlWeight targetOutcomeT targetOutcomeC
    treatedOutcome controlOutcome propensityScore treatedPrognosticScore
    controlPrognosticScore treatedValue controlValue treatedEnvelope
    controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit massLimit
    massScaleTarget massScaleTreated massScaleControl massEnvelopeTarget
    massEnvelopeTreated massEnvelopeControl scaledMassScaleTreated
    scaledMassScaleControl scaledMassEnvelopeTreated
    scaledMassEnvelopeControl htotalLimit

/--
Finite-score-alphabet PATT mass-envelope bridge, with the double-score cell set
specialized to `Finset.univ`.
-/
def pattDoubleScoreIndicatorSumConvergenceBridgeOfMassEnvelopeInputs_fintype
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
    (massLimit massScaleTarget massScaleControl :
      PropensityCell × PATTProgCell -> Real)
    (massEnvelopeTarget massEnvelopeControl : Index -> Real)
    (htotalLimit :
      (∑ cell ∈ (Finset.univ : Finset (PropensityCell × PATTProgCell)),
        massLimit cell) ≠ 0) :
    PATTDoubleScoreIndicatorSumConvergenceBridge :=
  pattDoubleScoreIndicatorSumConvergenceBridgeOfMassEnvelopeInputs
    (l := l)
    targetSample controlSample
    (Finset.univ : Finset (PropensityCell × PATTProgCell)) targetWeight
    controlWeight treatedTargetOutcome targetControlOutcome controlOutcome
    propensityScore controlPrognosticScore controlValue controlEnvelope
    controlEnvelopeLimit massLimit massScaleTarget massScaleControl
    massEnvelopeTarget massEnvelopeControl htotalLimit

/--
Finite-score-alphabet scaled PATT mass-envelope bridge, with the double-score
cell set specialized to `Finset.univ`.
-/
def scaledPATTDoubleScoreIndicatorSumConvergenceBridgeOfMassEnvelopeInputs_fintype
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
    (massLimit massScaleTarget massScaleControl :
      PropensityCell × PATTProgCell -> Real)
    (massEnvelopeTarget massEnvelopeControl : Index -> Real)
    (scaledMassScale : PropensityCell × PATTProgCell -> Real)
    (scaledMassEnvelope : Index -> Real)
    (htotalLimit :
      (∑ cell ∈ (Finset.univ : Finset (PropensityCell × PATTProgCell)),
        massLimit cell) ≠ 0) :
    ScaledPATTDoubleScoreIndicatorSumConvergenceBridge :=
  scaledPATTDoubleScoreIndicatorSumConvergenceBridgeOfMassEnvelopeInputs
    (l := l)
    scale targetSample controlSample
    (Finset.univ : Finset (PropensityCell × PATTProgCell)) targetWeight
    controlWeight treatedTargetOutcome targetControlOutcome controlOutcome
    propensityScore controlPrognosticScore controlValue controlEnvelope
    controlEnvelopeLimit massLimit massScaleTarget massScaleControl
    massEnvelopeTarget massEnvelopeControl scaledMassScale scaledMassEnvelope
    htotalLimit

/--
Finite-score-alphabet PATE mass-envelope evidence packages both ordinary and
scaled double-score indicator-sum bridges.
-/
def pateDoubleScoreIndicatorSumConvergenceBridgesOfMassEnvelopeInputs_fintype
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
    (massLimit massScaleTarget massScaleTreated massScaleControl :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (massEnvelopeTarget massEnvelopeTreated massEnvelopeControl :
      Index -> Real)
    (scaledMassScaleTreated scaledMassScaleControl :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (scaledMassEnvelopeTreated scaledMassEnvelopeControl : Index -> Real)
    (htotalLimit :
      (∑ cell ∈
        (Finset.univ :
          Finset ((PropensityCell × TreatedProgCell) × ControlProgCell)),
        massLimit cell) ≠ 0) :
    PATEDoubleScoreIndicatorSumConvergenceBridge ×
      ScaledPATEDoubleScoreIndicatorSumConvergenceBridge :=
  pateDoubleScoreIndicatorSumConvergenceBridgesOfMassEnvelopeInputs
    (l := l)
    scale targetSample treatedSample controlSample
    (Finset.univ :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    targetWeight treatedWeight controlWeight targetOutcomeT targetOutcomeC
    treatedOutcome controlOutcome propensityScore treatedPrognosticScore
    controlPrognosticScore treatedValue controlValue treatedEnvelope
    controlEnvelope treatedEnvelopeLimit controlEnvelopeLimit massLimit
    massScaleTarget massScaleTreated massScaleControl massEnvelopeTarget
    massEnvelopeTreated massEnvelopeControl scaledMassScaleTreated
    scaledMassScaleControl scaledMassEnvelopeTreated
    scaledMassEnvelopeControl htotalLimit

/--
Finite-score-alphabet PATT mass-envelope evidence packages both ordinary and
scaled double-score indicator-sum bridges.
-/
def pattDoubleScoreIndicatorSumConvergenceBridgesOfMassEnvelopeInputs_fintype
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
    (massLimit massScaleTarget massScaleControl :
      PropensityCell × PATTProgCell -> Real)
    (massEnvelopeTarget massEnvelopeControl : Index -> Real)
    (scaledMassScale : PropensityCell × PATTProgCell -> Real)
    (scaledMassEnvelope : Index -> Real)
    (htotalLimit :
      (∑ cell ∈ (Finset.univ : Finset (PropensityCell × PATTProgCell)),
        massLimit cell) ≠ 0) :
    PATTDoubleScoreIndicatorSumConvergenceBridge ×
      ScaledPATTDoubleScoreIndicatorSumConvergenceBridge :=
  pattDoubleScoreIndicatorSumConvergenceBridgesOfMassEnvelopeInputs
    (l := l)
    scale targetSample controlSample
    (Finset.univ : Finset (PropensityCell × PATTProgCell)) targetWeight
    controlWeight treatedTargetOutcome targetControlOutcome controlOutcome
    propensityScore controlPrognosticScore controlValue controlEnvelope
    controlEnvelopeLimit massLimit massScaleTarget massScaleControl
    massEnvelopeTarget massEnvelopeControl scaledMassScale scaledMassEnvelope
    htotalLimit

end WDSM
end Matching
end StatInference
