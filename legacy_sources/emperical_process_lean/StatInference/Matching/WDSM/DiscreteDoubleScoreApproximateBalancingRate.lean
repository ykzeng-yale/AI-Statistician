import StatInference.Matching.WDSM.DiscreteApproximateBalancingRate
import StatInference.Matching.WDSM.DiscreteDoubleScoreApproximateBalancing

/-!
# Rate transfer for approximate double-score balancing

This module specializes the approximate-balancing rate-transfer layer to the
joint WDSM double-score cells.  The results are deterministic `Tendsto`
bridges: once the stochastic layer proves L1 convergence of normalized
double-score share imbalances, these theorems give PATE/PATT contrast
negligibility and scaled negligibility.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter
open scoped BigOperators

variable {Index Unit PropensityCell TreatedProgCell ControlProgCell PATTProgCell : Type*}
  [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
  [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]
variable {l : Filter Index}

/-- L1 distance between normalized PATE double-score share vectors. -/
noncomputable def l1PATEDoubleScoreShareDistance
    (cells : Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (sampleA sampleB : Finset Unit)
    (weightA weightB : Unit -> Real)
    (propensityScore : Unit -> PropensityCell)
    (treatedPrognosticScore : Unit -> TreatedProgCell)
    (controlPrognosticScore : Unit -> ControlProgCell) : Real :=
  l1ScoreCellShareDistance cells sampleA sampleB weightA weightB
    (pateDoubleScore propensityScore treatedPrognosticScore
      controlPrognosticScore)
    (pateDoubleScore propensityScore treatedPrognosticScore
      controlPrognosticScore)

/-- L1 distance between normalized PATT double-score share vectors. -/
noncomputable def l1PATTDoubleScoreShareDistance
    (cells : Finset (PropensityCell × PATTProgCell))
    (sampleA sampleB : Finset Unit)
    (weightA weightB : Unit -> Real)
    (propensityScore : Unit -> PropensityCell)
    (controlPrognosticScore : Unit -> PATTProgCell) : Real :=
  l1ScoreCellShareDistance cells sampleA sampleB weightA weightB
    (pattDoubleScore propensityScore controlPrognosticScore)
    (pattDoubleScore propensityScore controlPrognosticScore)

theorem tendsto_pateDoubleScoreApprox_error_zero_of_l1
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
    (hcoverTarget :
      ∀ index unit, unit ∈ targetSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells index)
    (hcoverTreated :
      ∀ index unit, unit ∈ treatedSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells index)
    (hcoverControl :
      ∀ index unit, unit ∈ controlSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells index)
    (hmassTarget :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (targetSample index) (targetWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassTreated :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (treatedSample index) (treatedWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (controlSample index) (controlWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
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
      ∀ index cell, cell ∈ cells index ->
        |treatedCellValueOnPATEDoubleScore (treatedValue index) cell| ≤
          treatedEnvelope index)
    (hcontrol_bound :
      ∀ index cell, cell ∈ cells index ->
        |controlCellValueOnPATEDoubleScore (controlValue index) cell| ≤
          controlEnvelope index)
    (hrate :
      Tendsto
        (fun index =>
          treatedEnvelope index *
            l1PATEDoubleScoreShareDistance (cells index)
              (targetSample index) (treatedSample index)
              (targetWeight index) (treatedWeight index)
              (propensityScore index) (treatedPrognosticScore index)
              (controlPrognosticScore index) +
          controlEnvelope index *
            l1PATEDoubleScoreShareDistance (cells index)
              (targetSample index) (controlSample index)
              (targetWeight index) (controlWeight index)
              (propensityScore index) (treatedPrognosticScore index)
              (controlPrognosticScore index))
        l (nhds 0)) :
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
  exact tendsto_zero_of_abs_le_bound
    (fun index =>
      weightedSampleMeanContrast (targetSample index)
        (targetWeight index) (targetOutcomeT index) (targetOutcomeC index) -
      twoArmWeightedMeanContrast (treatedSample index)
        (controlSample index) (treatedWeight index) (controlWeight index)
        (treatedOutcome index) (controlOutcome index))
    (fun index =>
      treatedEnvelope index *
        l1PATEDoubleScoreShareDistance (cells index)
          (targetSample index) (treatedSample index)
          (targetWeight index) (treatedWeight index)
          (propensityScore index) (treatedPrognosticScore index)
          (controlPrognosticScore index) +
      controlEnvelope index *
        l1PATEDoubleScoreShareDistance (cells index)
          (targetSample index) (controlSample index)
          (targetWeight index) (controlWeight index)
          (propensityScore index) (treatedPrognosticScore index)
          (controlPrognosticScore index))
    (fun index => by
      unfold l1PATEDoubleScoreShareDistance l1ScoreCellShareDistance
      exact
        abs_weightedSampleMeanContrast_sub_twoArmWeightedMeanContrast_pateDoubleScore_le_l1
          (targetSample index) (treatedSample index) (controlSample index)
          (cells index) (targetWeight index) (treatedWeight index)
          (controlWeight index) (targetOutcomeT index) (targetOutcomeC index)
          (treatedOutcome index) (controlOutcome index)
          (propensityScore index) (treatedPrognosticScore index)
          (controlPrognosticScore index) (treatedValue index)
          (controlValue index) (treatedEnvelope index)
          (controlEnvelope index) (hcoverTarget index)
          (hcoverTreated index) (hcoverControl index) (hmassTarget index)
          (hmassTreated index) (hmassControl index)
          (hscoreMeasTargetT index) (hscoreMeasTreated index)
          (hscoreMeasTargetC index) (hscoreMeasControl index)
          (htreated_bound index) (hcontrol_bound index))
    hrate

theorem tendsto_scaled_pateDoubleScoreApprox_error_zero_of_l1
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
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hcoverTarget :
      ∀ index unit, unit ∈ targetSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells index)
    (hcoverTreated :
      ∀ index unit, unit ∈ treatedSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells index)
    (hcoverControl :
      ∀ index unit, unit ∈ controlSample index ->
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells index)
    (hmassTarget :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (targetSample index) (targetWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassTreated :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (treatedSample index) (treatedWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (controlSample index) (controlWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0)
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
      ∀ index cell, cell ∈ cells index ->
        |treatedCellValueOnPATEDoubleScore (treatedValue index) cell| ≤
          treatedEnvelope index)
    (hcontrol_bound :
      ∀ index cell, cell ∈ cells index ->
        |controlCellValueOnPATEDoubleScore (controlValue index) cell| ≤
          controlEnvelope index)
    (hscaled_rate :
      Tendsto
        (fun index =>
          scale index *
            (treatedEnvelope index *
              l1PATEDoubleScoreShareDistance (cells index)
                (targetSample index) (treatedSample index)
                (targetWeight index) (treatedWeight index)
                (propensityScore index) (treatedPrognosticScore index)
                (controlPrognosticScore index) +
            controlEnvelope index *
              l1PATEDoubleScoreShareDistance (cells index)
                (targetSample index) (controlSample index)
                (targetWeight index) (controlWeight index)
                (propensityScore index) (treatedPrognosticScore index)
                (controlPrognosticScore index)))
        l (nhds 0)) :
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
  exact tendsto_scaled_zero_of_abs_le_bound
    scale
    (fun index =>
      weightedSampleMeanContrast (targetSample index)
        (targetWeight index) (targetOutcomeT index) (targetOutcomeC index) -
      twoArmWeightedMeanContrast (treatedSample index)
        (controlSample index) (treatedWeight index) (controlWeight index)
        (treatedOutcome index) (controlOutcome index))
    (fun index =>
      treatedEnvelope index *
        l1PATEDoubleScoreShareDistance (cells index)
          (targetSample index) (treatedSample index)
          (targetWeight index) (treatedWeight index)
          (propensityScore index) (treatedPrognosticScore index)
          (controlPrognosticScore index) +
      controlEnvelope index *
        l1PATEDoubleScoreShareDistance (cells index)
          (targetSample index) (controlSample index)
          (targetWeight index) (controlWeight index)
          (propensityScore index) (treatedPrognosticScore index)
          (controlPrognosticScore index))
    hscale_nonneg
    (fun index => by
      unfold l1PATEDoubleScoreShareDistance l1ScoreCellShareDistance
      exact
        abs_weightedSampleMeanContrast_sub_twoArmWeightedMeanContrast_pateDoubleScore_le_l1
          (targetSample index) (treatedSample index) (controlSample index)
          (cells index) (targetWeight index) (treatedWeight index)
          (controlWeight index) (targetOutcomeT index) (targetOutcomeC index)
          (treatedOutcome index) (controlOutcome index)
          (propensityScore index) (treatedPrognosticScore index)
          (controlPrognosticScore index) (treatedValue index)
          (controlValue index) (treatedEnvelope index)
          (controlEnvelope index) (hcoverTarget index)
          (hcoverTreated index) (hcoverControl index) (hmassTarget index)
          (hmassTreated index) (hmassControl index)
          (hscoreMeasTargetT index) (hscoreMeasTreated index)
          (hscoreMeasTargetC index) (hscoreMeasControl index)
          (htreated_bound index) (hcontrol_bound index))
    hscaled_rate

theorem tendsto_pattDoubleScoreApprox_error_zero_of_l1
    (targetSample controlSample : Index -> Finset Unit)
    (cells : Index -> Finset (PropensityCell × PATTProgCell))
    (targetWeight controlWeight : Index -> Unit -> Real)
    (treatedTargetOutcome targetControlOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (controlValue : Index -> PATTProgCell -> Real)
    (controlEnvelope : Index -> Real)
    (hcoverTarget :
      ∀ index unit, unit ∈ targetSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells index)
    (hcoverControl :
      ∀ index unit, unit ∈ controlSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells index)
    (hmassTarget :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (targetSample index) (targetWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (controlSample index) (controlWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hscoreMeasTargetC :
      ∀ index unit, unit ∈ targetSample index ->
        targetControlOutcome index unit =
          controlValue index (controlPrognosticScore index unit))
    (hscoreMeasControl :
      ∀ index unit, unit ∈ controlSample index ->
        controlOutcome index unit =
          controlValue index (controlPrognosticScore index unit))
    (hcontrol_bound :
      ∀ index cell, cell ∈ cells index ->
        |controlCellValueOnPATTDoubleScore (controlValue index) cell| ≤
          controlEnvelope index)
    (hrate :
      Tendsto
        (fun index =>
          controlEnvelope index *
            l1PATTDoubleScoreShareDistance (cells index)
              (targetSample index) (controlSample index)
              (targetWeight index) (controlWeight index)
              (propensityScore index) (controlPrognosticScore index))
        l (nhds 0)) :
    Tendsto
      (fun index =>
        weightedSampleMeanContrast (targetSample index)
          (targetWeight index) (treatedTargetOutcome index)
          (targetControlOutcome index) -
        pattWeightedMeanContrast (targetSample index) (controlSample index)
          (targetWeight index) (controlWeight index)
          (treatedTargetOutcome index) (controlOutcome index))
      l (nhds 0) := by
  exact tendsto_zero_of_abs_le_bound
    (fun index =>
      weightedSampleMeanContrast (targetSample index)
        (targetWeight index) (treatedTargetOutcome index)
        (targetControlOutcome index) -
      pattWeightedMeanContrast (targetSample index) (controlSample index)
        (targetWeight index) (controlWeight index)
        (treatedTargetOutcome index) (controlOutcome index))
    (fun index =>
      controlEnvelope index *
        l1PATTDoubleScoreShareDistance (cells index)
          (targetSample index) (controlSample index)
          (targetWeight index) (controlWeight index)
          (propensityScore index) (controlPrognosticScore index))
    (fun index => by
      unfold l1PATTDoubleScoreShareDistance l1ScoreCellShareDistance
      exact
        abs_weightedSampleMeanContrast_sub_pattWeightedMeanContrast_pattDoubleScore_le_l1
          (targetSample index) (controlSample index) (cells index)
          (targetWeight index) (controlWeight index)
          (treatedTargetOutcome index) (targetControlOutcome index)
          (controlOutcome index) (propensityScore index)
          (controlPrognosticScore index) (controlValue index)
          (controlEnvelope index) (hcoverTarget index)
          (hcoverControl index) (hmassTarget index) (hmassControl index)
          (hscoreMeasTargetC index) (hscoreMeasControl index)
          (hcontrol_bound index))
    hrate

theorem tendsto_scaled_pattDoubleScoreApprox_error_zero_of_l1
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
    (hscale_nonneg : ∀ index, 0 ≤ scale index)
    (hcoverTarget :
      ∀ index unit, unit ∈ targetSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells index)
    (hcoverControl :
      ∀ index unit, unit ∈ controlSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells index)
    (hmassTarget :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (targetSample index) (targetWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (controlSample index) (controlWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hscoreMeasTargetC :
      ∀ index unit, unit ∈ targetSample index ->
        targetControlOutcome index unit =
          controlValue index (controlPrognosticScore index unit))
    (hscoreMeasControl :
      ∀ index unit, unit ∈ controlSample index ->
        controlOutcome index unit =
          controlValue index (controlPrognosticScore index unit))
    (hcontrol_bound :
      ∀ index cell, cell ∈ cells index ->
        |controlCellValueOnPATTDoubleScore (controlValue index) cell| ≤
          controlEnvelope index)
    (hscaled_rate :
      Tendsto
        (fun index =>
          scale index *
            (controlEnvelope index *
              l1PATTDoubleScoreShareDistance (cells index)
                (targetSample index) (controlSample index)
                (targetWeight index) (controlWeight index)
                (propensityScore index) (controlPrognosticScore index)))
        l (nhds 0)) :
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
  exact tendsto_scaled_zero_of_abs_le_bound
    scale
    (fun index =>
      weightedSampleMeanContrast (targetSample index)
        (targetWeight index) (treatedTargetOutcome index)
        (targetControlOutcome index) -
      pattWeightedMeanContrast (targetSample index) (controlSample index)
        (targetWeight index) (controlWeight index)
        (treatedTargetOutcome index) (controlOutcome index))
    (fun index =>
      controlEnvelope index *
        l1PATTDoubleScoreShareDistance (cells index)
          (targetSample index) (controlSample index)
          (targetWeight index) (controlWeight index)
          (propensityScore index) (controlPrognosticScore index))
    hscale_nonneg
    (fun index => by
      unfold l1PATTDoubleScoreShareDistance l1ScoreCellShareDistance
      exact
        abs_weightedSampleMeanContrast_sub_pattWeightedMeanContrast_pattDoubleScore_le_l1
          (targetSample index) (controlSample index) (cells index)
          (targetWeight index) (controlWeight index)
          (treatedTargetOutcome index) (targetControlOutcome index)
          (controlOutcome index) (propensityScore index)
          (controlPrognosticScore index) (controlValue index)
          (controlEnvelope index) (hcoverTarget index)
          (hcoverControl index) (hmassTarget index) (hmassControl index)
          (hscoreMeasTargetC index) (hscoreMeasControl index)
          (hcontrol_bound index))
    hscaled_rate

theorem tendsto_pateDoubleScoreApprox_error_zero_of_eventually_l1
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
    (hcoverTarget :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index) unit ∈ cells index)
    (hcoverTreated :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ treatedSample index ->
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index) unit ∈ cells index)
    (hcoverControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index) unit ∈ cells index)
    (hmassTarget :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          scoreCellMass (targetSample index) (targetWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index)
              (controlPrognosticScore index)) cell ≠ 0)
    (hmassTreated :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          scoreCellMass (treatedSample index) (treatedWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index)
              (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          scoreCellMass (controlSample index) (controlWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index)
              (controlPrognosticScore index)) cell ≠ 0)
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
        ∀ cell, cell ∈ cells index ->
          |treatedCellValueOnPATEDoubleScore (treatedValue index) cell| ≤
            treatedEnvelope index)
    (hcontrol_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          |controlCellValueOnPATEDoubleScore (controlValue index) cell| ≤
            controlEnvelope index)
    (hrate :
      Tendsto
        (fun index =>
          treatedEnvelope index *
            l1PATEDoubleScoreShareDistance (cells index)
              (targetSample index) (treatedSample index)
              (targetWeight index) (treatedWeight index)
              (propensityScore index) (treatedPrognosticScore index)
              (controlPrognosticScore index) +
          controlEnvelope index *
            l1PATEDoubleScoreShareDistance (cells index)
              (targetSample index) (controlSample index)
              (targetWeight index) (controlWeight index)
              (propensityScore index) (treatedPrognosticScore index)
              (controlPrognosticScore index))
        l (nhds 0)) :
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
  exact tendsto_weightedSampleMeanContrast_difference_zero_of_eventually_l1_scoreCellShare
    targetSample treatedSample controlSample cells targetWeight treatedWeight
    controlWeight targetOutcomeT targetOutcomeC treatedOutcome controlOutcome
    (fun index =>
      pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index) (controlPrognosticScore index))
    (fun index =>
      pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index) (controlPrognosticScore index))
    (fun index =>
      pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index) (controlPrognosticScore index))
    (fun index => treatedCellValueOnPATEDoubleScore (treatedValue index))
    (fun index => controlCellValueOnPATEDoubleScore (controlValue index))
    treatedEnvelope controlEnvelope hcoverTarget hcoverTreated hcoverControl
    hmassTarget hmassTreated hmassControl
    (by
      filter_upwards [hscoreMeasTargetT] with index hindex
      exact treated_scoreMeasurable_pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index) (controlPrognosticScore index)
        (targetOutcomeT index) (treatedValue index) (targetSample index)
        hindex)
    (by
      filter_upwards [hscoreMeasTreated] with index hindex
      exact treated_scoreMeasurable_pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index) (controlPrognosticScore index)
        (treatedOutcome index) (treatedValue index) (treatedSample index)
        hindex)
    (by
      filter_upwards [hscoreMeasTargetC] with index hindex
      exact control_scoreMeasurable_pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index) (controlPrognosticScore index)
        (targetOutcomeC index) (controlValue index) (targetSample index)
        hindex)
    (by
      filter_upwards [hscoreMeasControl] with index hindex
      exact control_scoreMeasurable_pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index) (controlPrognosticScore index)
        (controlOutcome index) (controlValue index) (controlSample index)
        hindex)
    htreated_bound hcontrol_bound hrate

theorem tendsto_scaled_pateDoubleScoreApprox_error_zero_of_eventually_l1
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
    (hscale_nonneg : ∀ᶠ index in l, 0 ≤ scale index)
    (hcoverTarget :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index) unit ∈ cells index)
    (hcoverTreated :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ treatedSample index ->
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index) unit ∈ cells index)
    (hcoverControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index) unit ∈ cells index)
    (hmassTarget :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          scoreCellMass (targetSample index) (targetWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index)
              (controlPrognosticScore index)) cell ≠ 0)
    (hmassTreated :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          scoreCellMass (treatedSample index) (treatedWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index)
              (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          scoreCellMass (controlSample index) (controlWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index)
              (controlPrognosticScore index)) cell ≠ 0)
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
        ∀ cell, cell ∈ cells index ->
          |treatedCellValueOnPATEDoubleScore (treatedValue index) cell| ≤
            treatedEnvelope index)
    (hcontrol_bound :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          |controlCellValueOnPATEDoubleScore (controlValue index) cell| ≤
            controlEnvelope index)
    (hscaled_rate :
      Tendsto
        (fun index =>
          scale index *
            (treatedEnvelope index *
              l1PATEDoubleScoreShareDistance (cells index)
                (targetSample index) (treatedSample index)
                (targetWeight index) (treatedWeight index)
                (propensityScore index) (treatedPrognosticScore index)
                (controlPrognosticScore index) +
            controlEnvelope index *
              l1PATEDoubleScoreShareDistance (cells index)
                (targetSample index) (controlSample index)
                (targetWeight index) (controlWeight index)
                (propensityScore index) (treatedPrognosticScore index)
                (controlPrognosticScore index)))
        l (nhds 0)) :
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
  exact tendsto_scaled_weightedSampleMeanContrast_difference_zero_of_eventually_l1_scoreCellShare
    scale targetSample treatedSample controlSample cells targetWeight
    treatedWeight controlWeight targetOutcomeT targetOutcomeC treatedOutcome
    controlOutcome
    (fun index =>
      pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index) (controlPrognosticScore index))
    (fun index =>
      pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index) (controlPrognosticScore index))
    (fun index =>
      pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index) (controlPrognosticScore index))
    (fun index => treatedCellValueOnPATEDoubleScore (treatedValue index))
    (fun index => controlCellValueOnPATEDoubleScore (controlValue index))
    treatedEnvelope controlEnvelope hscale_nonneg hcoverTarget hcoverTreated
    hcoverControl hmassTarget hmassTreated hmassControl
    (by
      filter_upwards [hscoreMeasTargetT] with index hindex
      exact treated_scoreMeasurable_pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index) (controlPrognosticScore index)
        (targetOutcomeT index) (treatedValue index) (targetSample index)
        hindex)
    (by
      filter_upwards [hscoreMeasTreated] with index hindex
      exact treated_scoreMeasurable_pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index) (controlPrognosticScore index)
        (treatedOutcome index) (treatedValue index) (treatedSample index)
        hindex)
    (by
      filter_upwards [hscoreMeasTargetC] with index hindex
      exact control_scoreMeasurable_pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index) (controlPrognosticScore index)
        (targetOutcomeC index) (controlValue index) (targetSample index)
        hindex)
    (by
      filter_upwards [hscoreMeasControl] with index hindex
      exact control_scoreMeasurable_pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index) (controlPrognosticScore index)
        (controlOutcome index) (controlValue index) (controlSample index)
        hindex)
    htreated_bound hcontrol_bound hscaled_rate

theorem tendsto_pattDoubleScoreApprox_error_zero_of_eventually_l1
    (targetSample controlSample : Index -> Finset Unit)
    (cells : Index -> Finset (PropensityCell × PATTProgCell))
    (targetWeight controlWeight : Index -> Unit -> Real)
    (treatedTargetOutcome targetControlOutcome controlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (controlValue : Index -> PATTProgCell -> Real)
    (controlEnvelope : Index -> Real)
    (hcoverTarget :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          pattDoubleScore (propensityScore index)
            (controlPrognosticScore index) unit ∈ cells index)
    (hcoverControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          pattDoubleScore (propensityScore index)
            (controlPrognosticScore index) unit ∈ cells index)
    (hmassTarget :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          scoreCellMass (targetSample index) (targetWeight index)
            (pattDoubleScore (propensityScore index)
              (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          scoreCellMass (controlSample index) (controlWeight index)
            (pattDoubleScore (propensityScore index)
              (controlPrognosticScore index)) cell ≠ 0)
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
        ∀ cell, cell ∈ cells index ->
          |controlCellValueOnPATTDoubleScore (controlValue index) cell| ≤
            controlEnvelope index)
    (hrate :
      Tendsto
        (fun index =>
          controlEnvelope index *
            l1PATTDoubleScoreShareDistance (cells index)
              (targetSample index) (controlSample index)
              (targetWeight index) (controlWeight index)
              (propensityScore index) (controlPrognosticScore index))
        l (nhds 0)) :
    Tendsto
      (fun index =>
        weightedSampleMeanContrast (targetSample index)
          (targetWeight index) (treatedTargetOutcome index)
          (targetControlOutcome index) -
        pattWeightedMeanContrast (targetSample index) (controlSample index)
          (targetWeight index) (controlWeight index)
          (treatedTargetOutcome index) (controlOutcome index))
      l (nhds 0) := by
  exact tendsto_pattWeightedMeanContrast_difference_zero_of_eventually_l1_scoreCellShare
    targetSample controlSample cells targetWeight controlWeight
    treatedTargetOutcome targetControlOutcome controlOutcome
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    (fun index => controlCellValueOnPATTDoubleScore (controlValue index))
    controlEnvelope hcoverTarget hcoverControl hmassTarget hmassControl
    (by
      filter_upwards [hscoreMeasTargetC] with index hindex
      exact control_scoreMeasurable_pattDoubleScore (propensityScore index)
        (controlPrognosticScore index) (targetControlOutcome index)
        (controlValue index) (targetSample index) hindex)
    (by
      filter_upwards [hscoreMeasControl] with index hindex
      exact control_scoreMeasurable_pattDoubleScore (propensityScore index)
        (controlPrognosticScore index) (controlOutcome index)
        (controlValue index) (controlSample index) hindex)
    hcontrol_bound hrate

theorem tendsto_scaled_pattDoubleScoreApprox_error_zero_of_eventually_l1
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
    (hscale_nonneg : ∀ᶠ index in l, 0 ≤ scale index)
    (hcoverTarget :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ targetSample index ->
          pattDoubleScore (propensityScore index)
            (controlPrognosticScore index) unit ∈ cells index)
    (hcoverControl :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          pattDoubleScore (propensityScore index)
            (controlPrognosticScore index) unit ∈ cells index)
    (hmassTarget :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          scoreCellMass (targetSample index) (targetWeight index)
            (pattDoubleScore (propensityScore index)
              (controlPrognosticScore index)) cell ≠ 0)
    (hmassControl :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index ->
          scoreCellMass (controlSample index) (controlWeight index)
            (pattDoubleScore (propensityScore index)
              (controlPrognosticScore index)) cell ≠ 0)
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
        ∀ cell, cell ∈ cells index ->
          |controlCellValueOnPATTDoubleScore (controlValue index) cell| ≤
            controlEnvelope index)
    (hscaled_rate :
      Tendsto
        (fun index =>
          scale index *
            (controlEnvelope index *
              l1PATTDoubleScoreShareDistance (cells index)
                (targetSample index) (controlSample index)
                (targetWeight index) (controlWeight index)
                (propensityScore index) (controlPrognosticScore index)))
        l (nhds 0)) :
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
  exact tendsto_scaled_pattWeightedMeanContrast_difference_zero_of_eventually_l1_scoreCellShare
    scale targetSample controlSample cells targetWeight controlWeight
    treatedTargetOutcome targetControlOutcome controlOutcome
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    (fun index => controlCellValueOnPATTDoubleScore (controlValue index))
    controlEnvelope hscale_nonneg hcoverTarget hcoverControl hmassTarget
    hmassControl
    (by
      filter_upwards [hscoreMeasTargetC] with index hindex
      exact control_scoreMeasurable_pattDoubleScore (propensityScore index)
        (controlPrognosticScore index) (targetControlOutcome index)
        (controlValue index) (targetSample index) hindex)
    (by
      filter_upwards [hscoreMeasControl] with index hindex
      exact control_scoreMeasurable_pattDoubleScore (propensityScore index)
        (controlPrognosticScore index) (controlOutcome index)
        (controlValue index) (controlSample index) hindex)
    hcontrol_bound hscaled_rate

end WDSM
end Matching
end StatInference
