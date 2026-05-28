import StatInference.Matching.WDSM.ProspectiveFiniteCellPositivityConvergence

/-!
# Prospective finite side conditions from positive normalized counts

This module packages the eventual finite side conditions needed by the
prospective/common-weight approximation route.  Positive normalized total-count
limits give eventual sample nonemptiness, while positive normalized cell-count
limits over a finite partition give eventual nonzero common-weight cell masses
for every cell.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Unit PropensityCell TreatedProgCell ControlProgCell PATTProgCell : Type*}
  {l : Filter Index}
  [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
  [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]

/--
PATE side-condition bundle: positive normalized total counts and positive
normalized PATE double-score cell counts imply, eventually, nonempty target,
treated, and control samples and nonzero common-weight cell masses for every
cell in the fixed finite partition.
-/
theorem eventually_pateSideConditions_of_tendsto_positive_normalized_counts
    (targetSample treatedSample controlSample : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (targetNormalizer treatedNormalizer controlNormalizer : Index -> Real)
    (targetCommonWeight treatedCommonWeight controlCommonWeight :
      Index -> Real)
    (targetTotalLimit treatedTotalLimit controlTotalLimit : Real)
    (cellLimit :
      (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (hnormalizerTarget : ∀ᶠ index in l, 0 < targetNormalizer index)
    (hnormalizerTreated : ∀ᶠ index in l, 0 < treatedNormalizer index)
    (hnormalizerControl : ∀ᶠ index in l, 0 < controlNormalizer index)
    (hweightTarget : ∀ᶠ index in l, targetCommonWeight index ≠ 0)
    (hweightTreated : ∀ᶠ index in l, treatedCommonWeight index ≠ 0)
    (hweightControl : ∀ᶠ index in l, controlCommonWeight index ≠ 0)
    (htotalTarget :
      Tendsto
        (fun index =>
          targetNormalizer index * ((targetSample index).card : Real))
        l (nhds targetTotalLimit))
    (htotalTreated :
      Tendsto
        (fun index =>
          treatedNormalizer index * ((treatedSample index).card : Real))
        l (nhds treatedTotalLimit))
    (htotalControl :
      Tendsto
        (fun index =>
          controlNormalizer index * ((controlSample index).card : Real))
        l (nhds controlTotalLimit))
    (htotalTarget_pos : 0 < targetTotalLimit)
    (htotalTreated_pos : 0 < treatedTotalLimit)
    (htotalControl_pos : 0 < controlTotalLimit)
    (hcellTarget :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            targetNormalizer index *
              (((targetSample index).filter
                (fun unit =>
                  pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real))
          l (nhds (cellLimit cell)))
    (hcellTreated :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            treatedNormalizer index *
              (((treatedSample index).filter
                (fun unit =>
                  pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real))
          l (nhds (cellLimit cell)))
    (hcellControl :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            controlNormalizer index *
              (((controlSample index).filter
                (fun unit =>
                  pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real))
          l (nhds (cellLimit cell)))
    (hcell_pos : ∀ cell, cell ∈ cells -> 0 < cellLimit cell) :
    ∀ᶠ index in l,
      (targetSample index).Nonempty ∧
        (treatedSample index).Nonempty ∧
        (controlSample index).Nonempty ∧
        (∀ cell, cell ∈ cells ->
          scoreCellMass (targetSample index)
            (fun _unit => targetCommonWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index)
              (controlPrognosticScore index)) cell ≠ 0) ∧
        (∀ cell, cell ∈ cells ->
          scoreCellMass (treatedSample index)
            (fun _unit => treatedCommonWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index)
              (controlPrognosticScore index)) cell ≠ 0) ∧
        (∀ cell, cell ∈ cells ->
          scoreCellMass (controlSample index)
            (fun _unit => controlCommonWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index)
              (controlPrognosticScore index)) cell ≠ 0) := by
  have hnonemptyTarget :
      ∀ᶠ index in l, (targetSample index).Nonempty :=
    eventually_sampleNonempty_of_tendsto_normalized_card_pos
      targetSample targetNormalizer targetTotalLimit hnormalizerTarget
      htotalTarget htotalTarget_pos
  have hnonemptyTreated :
      ∀ᶠ index in l, (treatedSample index).Nonempty :=
    eventually_sampleNonempty_of_tendsto_normalized_card_pos
      treatedSample treatedNormalizer treatedTotalLimit hnormalizerTreated
      htotalTreated htotalTreated_pos
  have hnonemptyControl :
      ∀ᶠ index in l, (controlSample index).Nonempty :=
    eventually_sampleNonempty_of_tendsto_normalized_card_pos
      controlSample controlNormalizer controlTotalLimit hnormalizerControl
      htotalControl htotalControl_pos
  have hmassTarget :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
          scoreCellMass (targetSample index)
            (fun _unit => targetCommonWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index)
              (controlPrognosticScore index)) cell ≠ 0 :=
    eventually_all_pateDoubleScoreCellMass_constant_weight_ne_zero_of_tendsto_normalized_cell_cards_pos
      targetSample propensityScore treatedPrognosticScore
      controlPrognosticScore cells targetNormalizer targetCommonWeight
      cellLimit hnormalizerTarget hweightTarget hcellTarget hcell_pos
  have hmassTreated :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
          scoreCellMass (treatedSample index)
            (fun _unit => treatedCommonWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index)
              (controlPrognosticScore index)) cell ≠ 0 :=
    eventually_all_pateDoubleScoreCellMass_constant_weight_ne_zero_of_tendsto_normalized_cell_cards_pos
      treatedSample propensityScore treatedPrognosticScore
      controlPrognosticScore cells treatedNormalizer treatedCommonWeight
      cellLimit hnormalizerTreated hweightTreated hcellTreated hcell_pos
  have hmassControl :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
          scoreCellMass (controlSample index)
            (fun _unit => controlCommonWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index)
              (controlPrognosticScore index)) cell ≠ 0 :=
    eventually_all_pateDoubleScoreCellMass_constant_weight_ne_zero_of_tendsto_normalized_cell_cards_pos
      controlSample propensityScore treatedPrognosticScore
      controlPrognosticScore cells controlNormalizer controlCommonWeight
      cellLimit hnormalizerControl hweightControl hcellControl hcell_pos
  filter_upwards
    [hnonemptyTarget, hnonemptyTreated, hnonemptyControl,
      hmassTarget, hmassTreated, hmassControl] with
    index htarget_nonempty htreated_nonempty hcontrol_nonempty
    htarget_mass htreated_mass hcontrol_mass
  exact
    ⟨htarget_nonempty, htreated_nonempty, hcontrol_nonempty,
      htarget_mass, htreated_mass, hcontrol_mass⟩

/--
PATT side-condition bundle: positive normalized total counts and positive
normalized PATT double-score cell counts imply, eventually, nonempty target and
control samples and nonzero common-weight cell masses for every cell in the
fixed finite partition.
-/
theorem eventually_pattSideConditions_of_tendsto_positive_normalized_counts
    (targetSample controlSample : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (cells : Finset (PropensityCell × PATTProgCell))
    (targetNormalizer controlNormalizer : Index -> Real)
    (targetCommonWeight controlCommonWeight : Index -> Real)
    (targetTotalLimit controlTotalLimit : Real)
    (cellLimit : PropensityCell × PATTProgCell -> Real)
    (hnormalizerTarget : ∀ᶠ index in l, 0 < targetNormalizer index)
    (hnormalizerControl : ∀ᶠ index in l, 0 < controlNormalizer index)
    (hweightTarget : ∀ᶠ index in l, targetCommonWeight index ≠ 0)
    (hweightControl : ∀ᶠ index in l, controlCommonWeight index ≠ 0)
    (htotalTarget :
      Tendsto
        (fun index =>
          targetNormalizer index * ((targetSample index).card : Real))
        l (nhds targetTotalLimit))
    (htotalControl :
      Tendsto
        (fun index =>
          controlNormalizer index * ((controlSample index).card : Real))
        l (nhds controlTotalLimit))
    (htotalTarget_pos : 0 < targetTotalLimit)
    (htotalControl_pos : 0 < controlTotalLimit)
    (hcellTarget :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            targetNormalizer index *
              (((targetSample index).filter
                (fun unit =>
                  pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real))
          l (nhds (cellLimit cell)))
    (hcellControl :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            controlNormalizer index *
              (((controlSample index).filter
                (fun unit =>
                  pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real))
          l (nhds (cellLimit cell)))
    (hcell_pos : ∀ cell, cell ∈ cells -> 0 < cellLimit cell) :
    ∀ᶠ index in l,
      (targetSample index).Nonempty ∧
        (controlSample index).Nonempty ∧
        (∀ cell, cell ∈ cells ->
          scoreCellMass (targetSample index)
            (fun _unit => targetCommonWeight index)
            (pattDoubleScore (propensityScore index)
              (controlPrognosticScore index)) cell ≠ 0) ∧
        (∀ cell, cell ∈ cells ->
          scoreCellMass (controlSample index)
            (fun _unit => controlCommonWeight index)
            (pattDoubleScore (propensityScore index)
              (controlPrognosticScore index)) cell ≠ 0) := by
  have hnonemptyTarget :
      ∀ᶠ index in l, (targetSample index).Nonempty :=
    eventually_sampleNonempty_of_tendsto_normalized_card_pos
      targetSample targetNormalizer targetTotalLimit hnormalizerTarget
      htotalTarget htotalTarget_pos
  have hnonemptyControl :
      ∀ᶠ index in l, (controlSample index).Nonempty :=
    eventually_sampleNonempty_of_tendsto_normalized_card_pos
      controlSample controlNormalizer controlTotalLimit hnormalizerControl
      htotalControl htotalControl_pos
  have hmassTarget :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
          scoreCellMass (targetSample index)
            (fun _unit => targetCommonWeight index)
            (pattDoubleScore (propensityScore index)
              (controlPrognosticScore index)) cell ≠ 0 :=
    eventually_all_pattDoubleScoreCellMass_constant_weight_ne_zero_of_tendsto_normalized_cell_cards_pos
      targetSample propensityScore controlPrognosticScore cells
      targetNormalizer targetCommonWeight cellLimit hnormalizerTarget
      hweightTarget hcellTarget hcell_pos
  have hmassControl :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells ->
          scoreCellMass (controlSample index)
            (fun _unit => controlCommonWeight index)
            (pattDoubleScore (propensityScore index)
              (controlPrognosticScore index)) cell ≠ 0 :=
    eventually_all_pattDoubleScoreCellMass_constant_weight_ne_zero_of_tendsto_normalized_cell_cards_pos
      controlSample propensityScore controlPrognosticScore cells
      controlNormalizer controlCommonWeight cellLimit hnormalizerControl
      hweightControl hcellControl hcell_pos
  filter_upwards
    [hnonemptyTarget, hnonemptyControl, hmassTarget, hmassControl] with
    index htarget_nonempty hcontrol_nonempty htarget_mass hcontrol_mass
  exact
    ⟨htarget_nonempty, hcontrol_nonempty, htarget_mass, hcontrol_mass⟩

end WDSM
end Matching
end StatInference
