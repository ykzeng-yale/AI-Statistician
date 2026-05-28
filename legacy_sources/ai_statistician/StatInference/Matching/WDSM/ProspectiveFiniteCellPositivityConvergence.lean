import StatInference.Matching.WDSM.ProspectiveCountPositivityConvergence

/-!
# Finite-cell positivity from positive normalized-count limits

The prospective normalized-count route often proves positive limiting mass for
every cell in a fixed finite score partition.  This module turns those
cellwise limits into the eventual finite positivity side conditions used by
the WDSM approximation bridges.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Unit Cell PropensityCell TreatedProgCell ControlProgCell PATTProgCell : Type*}
  {l : Filter Index}
  [DecidableEq Cell] [DecidableEq PropensityCell]
  [DecidableEq TreatedProgCell] [DecidableEq ControlProgCell]
  [DecidableEq PATTProgCell]

/--
A finite collection of eventual properties holds eventually for every member
of the collection.
-/
theorem eventually_forall_mem_of_forall_eventually
    {α : Type*}
    (cells : Finset α)
    (p : Index -> α -> Prop)
    (h : ∀ cell, cell ∈ cells -> ∀ᶠ index in l, p index cell) :
    ∀ᶠ index in l, ∀ cell, cell ∈ cells -> p index cell :=
  (Filter.eventually_all_finset cells).mpr h

/--
Positive normalized score-cell count limits over a fixed finite partition give
eventually positive raw counts for every cell in the partition.
-/
theorem eventually_all_cell_cards_pos_of_tendsto_normalized_cell_cards_pos
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (cells : Finset Cell)
    (normalizer : Index -> Real)
    (cellLimit : Cell -> Real)
    (hnormalizer : ∀ᶠ index in l, 0 < normalizer index)
    (hcell :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            normalizer index *
              (((sample index).filter
                (fun unit => score index unit = cell)).card : Real))
          l (nhds (cellLimit cell)))
    (hlimit : ∀ cell, cell ∈ cells -> 0 < cellLimit cell) :
    ∀ᶠ index in l,
      ∀ cell, cell ∈ cells ->
        0 < (((sample index).filter
          (fun unit => score index unit = cell)).card : Real) :=
  eventually_forall_mem_of_forall_eventually cells
    (fun index cell =>
      0 < (((sample index).filter
        (fun unit => score index unit = cell)).card : Real))
    (fun cell hmem =>
      eventually_cell_card_pos_of_tendsto_normalized_cell_card_pos
        sample score cell normalizer (cellLimit cell) hnormalizer
        (hcell cell hmem) (hlimit cell hmem))

/--
Positive normalized score-cell count limits and eventually positive common
weights give eventually positive common-weight WDSM masses for every cell in a
fixed finite partition.
-/
theorem eventually_all_scoreCellMass_constant_weight_pos_of_tendsto_normalized_cell_cards_pos
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (cells : Finset Cell)
    (normalizer commonWeight : Index -> Real)
    (cellLimit : Cell -> Real)
    (hnormalizer : ∀ᶠ index in l, 0 < normalizer index)
    (hweight : ∀ᶠ index in l, 0 < commonWeight index)
    (hcell :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            normalizer index *
              (((sample index).filter
                (fun unit => score index unit = cell)).card : Real))
          l (nhds (cellLimit cell)))
    (hlimit : ∀ cell, cell ∈ cells -> 0 < cellLimit cell) :
    ∀ᶠ index in l,
      ∀ cell, cell ∈ cells ->
        0 < scoreCellMass (sample index)
          (fun _unit => commonWeight index) (score index) cell :=
  eventually_forall_mem_of_forall_eventually cells
    (fun index cell =>
      0 < scoreCellMass (sample index)
        (fun _unit => commonWeight index) (score index) cell)
    (fun cell hmem =>
      eventually_scoreCellMass_constant_weight_pos_of_tendsto_normalized_cell_card_pos
        sample score cell normalizer commonWeight (cellLimit cell)
        hnormalizer hweight (hcell cell hmem) (hlimit cell hmem))

/--
Positive normalized score-cell count limits and eventually nonzero common
weights give eventually nonzero common-weight WDSM masses for every cell in a
fixed finite partition.
-/
theorem eventually_all_scoreCellMass_constant_weight_ne_zero_of_tendsto_normalized_cell_cards_pos
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (cells : Finset Cell)
    (normalizer commonWeight : Index -> Real)
    (cellLimit : Cell -> Real)
    (hnormalizer : ∀ᶠ index in l, 0 < normalizer index)
    (hweight : ∀ᶠ index in l, commonWeight index ≠ 0)
    (hcell :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            normalizer index *
              (((sample index).filter
                (fun unit => score index unit = cell)).card : Real))
          l (nhds (cellLimit cell)))
    (hlimit : ∀ cell, cell ∈ cells -> 0 < cellLimit cell) :
    ∀ᶠ index in l,
      ∀ cell, cell ∈ cells ->
        scoreCellMass (sample index) (fun _unit => commonWeight index)
          (score index) cell ≠ 0 :=
  eventually_forall_mem_of_forall_eventually cells
    (fun index cell =>
      scoreCellMass (sample index) (fun _unit => commonWeight index)
        (score index) cell ≠ 0)
    (fun cell hmem =>
      eventually_scoreCellMass_constant_weight_ne_zero_of_tendsto_normalized_cell_card_pos
        sample score cell normalizer commonWeight (cellLimit cell)
        hnormalizer hweight (hcell cell hmem) (hlimit cell hmem))

/--
PATE double-score specialization: positive normalized cell-count limits give
eventually positive common-weight PATE score-cell masses for every cell in a
fixed finite partition.
-/
theorem eventually_all_pateDoubleScoreCellMass_constant_weight_pos_of_tendsto_normalized_cell_cards_pos
    (sample : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (cells : Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (normalizer commonWeight : Index -> Real)
    (cellLimit : ((PropensityCell × TreatedProgCell) × ControlProgCell) -> Real)
    (hnormalizer : ∀ᶠ index in l, 0 < normalizer index)
    (hweight : ∀ᶠ index in l, 0 < commonWeight index)
    (hcell :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            normalizer index *
              (((sample index).filter
                (fun unit =>
                  pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real))
          l (nhds (cellLimit cell)))
    (hlimit : ∀ cell, cell ∈ cells -> 0 < cellLimit cell) :
    ∀ᶠ index in l,
      ∀ cell, cell ∈ cells ->
        0 < scoreCellMass (sample index)
          (fun _unit => commonWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell :=
  eventually_all_scoreCellMass_constant_weight_pos_of_tendsto_normalized_cell_cards_pos
    sample
    (fun index =>
      pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index)
        (controlPrognosticScore index))
    cells normalizer commonWeight cellLimit hnormalizer hweight hcell hlimit

/--
PATE double-score specialization: positive normalized cell-count limits give
eventually nonzero common-weight PATE score-cell masses for every cell in a
fixed finite partition.
-/
theorem eventually_all_pateDoubleScoreCellMass_constant_weight_ne_zero_of_tendsto_normalized_cell_cards_pos
    (sample : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (cells : Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (normalizer commonWeight : Index -> Real)
    (cellLimit : ((PropensityCell × TreatedProgCell) × ControlProgCell) -> Real)
    (hnormalizer : ∀ᶠ index in l, 0 < normalizer index)
    (hweight : ∀ᶠ index in l, commonWeight index ≠ 0)
    (hcell :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            normalizer index *
              (((sample index).filter
                (fun unit =>
                  pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real))
          l (nhds (cellLimit cell)))
    (hlimit : ∀ cell, cell ∈ cells -> 0 < cellLimit cell) :
    ∀ᶠ index in l,
      ∀ cell, cell ∈ cells ->
        scoreCellMass (sample index) (fun _unit => commonWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) cell ≠ 0 :=
  eventually_forall_mem_of_forall_eventually cells
    (fun index cell =>
      scoreCellMass (sample index) (fun _unit => commonWeight index)
        (pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index)) cell ≠ 0)
    (fun cell hmem =>
      eventually_pateDoubleScoreCellMass_constant_weight_ne_zero_of_tendsto_normalized_cell_card_pos
        sample propensityScore treatedPrognosticScore controlPrognosticScore
        cell normalizer commonWeight (cellLimit cell) hnormalizer hweight
        (hcell cell hmem) (hlimit cell hmem))

/--
PATT double-score specialization: positive normalized cell-count limits give
eventually positive common-weight PATT score-cell masses for every cell in a
fixed finite partition.
-/
theorem eventually_all_pattDoubleScoreCellMass_constant_weight_pos_of_tendsto_normalized_cell_cards_pos
    (sample : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (cells : Finset (PropensityCell × PATTProgCell))
    (normalizer commonWeight : Index -> Real)
    (cellLimit : PropensityCell × PATTProgCell -> Real)
    (hnormalizer : ∀ᶠ index in l, 0 < normalizer index)
    (hweight : ∀ᶠ index in l, 0 < commonWeight index)
    (hcell :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            normalizer index *
              (((sample index).filter
                (fun unit =>
                  pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real))
          l (nhds (cellLimit cell)))
    (hlimit : ∀ cell, cell ∈ cells -> 0 < cellLimit cell) :
    ∀ᶠ index in l,
      ∀ cell, cell ∈ cells ->
        0 < scoreCellMass (sample index)
          (fun _unit => commonWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell :=
  eventually_all_scoreCellMass_constant_weight_pos_of_tendsto_normalized_cell_cards_pos
    sample
    (fun index =>
      pattDoubleScore (propensityScore index)
        (controlPrognosticScore index))
    cells normalizer commonWeight cellLimit hnormalizer hweight hcell hlimit

/--
PATT double-score specialization: positive normalized cell-count limits give
eventually nonzero common-weight PATT score-cell masses for every cell in a
fixed finite partition.
-/
theorem eventually_all_pattDoubleScoreCellMass_constant_weight_ne_zero_of_tendsto_normalized_cell_cards_pos
    (sample : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (cells : Finset (PropensityCell × PATTProgCell))
    (normalizer commonWeight : Index -> Real)
    (cellLimit : PropensityCell × PATTProgCell -> Real)
    (hnormalizer : ∀ᶠ index in l, 0 < normalizer index)
    (hweight : ∀ᶠ index in l, commonWeight index ≠ 0)
    (hcell :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index =>
            normalizer index *
              (((sample index).filter
                (fun unit =>
                  pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index) unit = cell)).card :
                Real))
          l (nhds (cellLimit cell)))
    (hlimit : ∀ cell, cell ∈ cells -> 0 < cellLimit cell) :
    ∀ᶠ index in l,
      ∀ cell, cell ∈ cells ->
        scoreCellMass (sample index) (fun _unit => commonWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0 :=
  eventually_forall_mem_of_forall_eventually cells
    (fun index cell =>
      scoreCellMass (sample index) (fun _unit => commonWeight index)
        (pattDoubleScore (propensityScore index)
          (controlPrognosticScore index)) cell ≠ 0)
    (fun cell hmem =>
      eventually_pattDoubleScoreCellMass_constant_weight_ne_zero_of_tendsto_normalized_cell_card_pos
        sample propensityScore controlPrognosticScore cell normalizer
        commonWeight (cellLimit cell) hnormalizer hweight
        (hcell cell hmem) (hlimit cell hmem))

end WDSM
end Matching
end StatInference
