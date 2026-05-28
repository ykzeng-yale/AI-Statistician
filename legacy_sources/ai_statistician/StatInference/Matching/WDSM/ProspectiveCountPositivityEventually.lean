import StatInference.Matching.WDSM.ProspectiveCountPositivity

/-!
# Eventually positive finite counts for prospective WDSM

The stochastic normalized-count route usually supplies side conditions only
eventually along the asymptotic filter.  This module lifts the finite
count-positivity lemmas to `∀ᶠ` statements.
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

/-- Eventually nonzero sample cardinality gives eventually nonempty samples. -/
theorem eventually_sampleNonempty_of_eventually_card_ne_zero_real
    (sample : Index -> Finset Unit)
    (hcard : ∀ᶠ index in l, ((sample index).card : Real) ≠ 0) :
    ∀ᶠ index in l, (sample index).Nonempty := by
  filter_upwards [hcard] with index hindex
  exact sampleNonempty_of_card_ne_zero_real (sample index) hindex

/-- Eventually positive sample cardinality gives eventually nonempty samples. -/
theorem eventually_sampleNonempty_of_eventually_card_pos_real
    (sample : Index -> Finset Unit)
    (hcard : ∀ᶠ index in l, 0 < ((sample index).card : Real)) :
    ∀ᶠ index in l, (sample index).Nonempty := by
  filter_upwards [hcard] with index hindex
  exact sampleNonempty_of_card_pos_real (sample index) hindex

/--
Eventually nonzero common weights and eventually nonzero finite cell counts
give eventually nonzero WDSM score-cell masses.
-/
theorem eventually_scoreCellMass_constant_weight_ne_zero_of_eventually_cell_card_ne_zero
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (cell : Cell)
    (commonWeight : Index -> Real)
    (hweight : ∀ᶠ index in l, commonWeight index ≠ 0)
    (hcard :
      ∀ᶠ index in l,
        (((sample index).filter
          (fun unit => score index unit = cell)).card : Real) ≠ 0) :
    ∀ᶠ index in l,
      scoreCellMass (sample index) (fun _unit => commonWeight index)
        (score index) cell ≠ 0 := by
  filter_upwards [hweight, hcard] with index hweight_index hcard_index
  exact
    scoreCellMass_constant_weight_ne_zero_of_cell_card_ne_zero
      (sample index) (score index) cell (commonWeight index)
      hweight_index hcard_index

/--
Eventually positive common weights and eventually positive finite cell counts
give eventually positive WDSM score-cell masses.
-/
theorem eventually_scoreCellMass_constant_weight_pos_of_eventually_pos_cell_card
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (cell : Cell)
    (commonWeight : Index -> Real)
    (hweight : ∀ᶠ index in l, 0 < commonWeight index)
    (hcard :
      ∀ᶠ index in l,
        0 < (((sample index).filter
          (fun unit => score index unit = cell)).card : Real)) :
    ∀ᶠ index in l,
      0 < scoreCellMass (sample index)
        (fun _unit => commonWeight index) (score index) cell := by
  filter_upwards [hweight, hcard] with index hweight_index hcard_index
  exact
    scoreCellMass_constant_weight_pos_of_pos_of_cell_card_pos
      (sample index) (score index) cell (commonWeight index)
      hweight_index hcard_index

/--
Eventually positive common weights and eventually positive finite cell counts
give eventually nonzero WDSM score-cell masses.
-/
theorem eventually_scoreCellMass_constant_weight_ne_zero_of_eventually_pos_cell_card
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (cell : Cell)
    (commonWeight : Index -> Real)
    (hweight : ∀ᶠ index in l, 0 < commonWeight index)
    (hcard :
      ∀ᶠ index in l,
        0 < (((sample index).filter
          (fun unit => score index unit = cell)).card : Real)) :
    ∀ᶠ index in l,
      scoreCellMass (sample index) (fun _unit => commonWeight index)
        (score index) cell ≠ 0 := by
  filter_upwards
    [eventually_scoreCellMass_constant_weight_pos_of_eventually_pos_cell_card
      sample score cell commonWeight hweight hcard] with index hpos
  exact hpos.ne'

/-- PATE double-score eventual nonzero mass from eventual nonzero cell counts. -/
theorem eventually_pateDoubleScoreCellMass_constant_weight_ne_zero_of_eventually_cell_card_ne_zero
    (sample : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (cell : (PropensityCell × TreatedProgCell) × ControlProgCell)
    (commonWeight : Index -> Real)
    (hweight : ∀ᶠ index in l, commonWeight index ≠ 0)
    (hcard :
      ∀ᶠ index in l,
        (((sample index).filter
          (fun unit =>
            pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index)
              (controlPrognosticScore index) unit = cell)).card : Real) ≠
          0) :
    ∀ᶠ index in l,
      scoreCellMass (sample index) (fun _unit => commonWeight index)
        (pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index)) cell ≠ 0 := by
  exact
    eventually_scoreCellMass_constant_weight_ne_zero_of_eventually_cell_card_ne_zero
      sample
      (fun index =>
        pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index))
      cell commonWeight hweight hcard

/-- PATT double-score eventual nonzero mass from eventual nonzero cell counts. -/
theorem eventually_pattDoubleScoreCellMass_constant_weight_ne_zero_of_eventually_cell_card_ne_zero
    (sample : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (cell : PropensityCell × PATTProgCell)
    (commonWeight : Index -> Real)
    (hweight : ∀ᶠ index in l, commonWeight index ≠ 0)
    (hcard :
      ∀ᶠ index in l,
        (((sample index).filter
          (fun unit =>
            pattDoubleScore (propensityScore index)
              (controlPrognosticScore index) unit = cell)).card : Real) ≠
          0) :
    ∀ᶠ index in l,
      scoreCellMass (sample index) (fun _unit => commonWeight index)
        (pattDoubleScore (propensityScore index)
          (controlPrognosticScore index)) cell ≠ 0 := by
  exact
    eventually_scoreCellMass_constant_weight_ne_zero_of_eventually_cell_card_ne_zero
      sample
      (fun index =>
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index))
      cell commonWeight hweight hcard

/--
Paired PATE/PATT double-score eventual nonzero common-weight cell masses from
eventual nonzero finite cell counts.
-/
theorem eventually_pate_pattDoubleScoreCellMass_constant_weight_ne_zero_of_eventually_cell_card_ne_zero
    (pateSample pattSample : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (pattPrognosticScore : Index -> Unit -> PATTProgCell)
    (pateCell : (PropensityCell × TreatedProgCell) × ControlProgCell)
    (pattCell : PropensityCell × PATTProgCell)
    (pateCommonWeight pattCommonWeight : Index -> Real)
    (hpateWeight : ∀ᶠ index in l, pateCommonWeight index ≠ 0)
    (hpattWeight : ∀ᶠ index in l, pattCommonWeight index ≠ 0)
    (hpateCard :
      ∀ᶠ index in l,
        (((pateSample index).filter
          (fun unit =>
            pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index)
              (controlPrognosticScore index) unit = pateCell)).card : Real) ≠
          0)
    (hpattCard :
      ∀ᶠ index in l,
        (((pattSample index).filter
          (fun unit =>
            pattDoubleScore (propensityScore index)
              (pattPrognosticScore index) unit = pattCell)).card : Real) ≠
          0) :
    (∀ᶠ index in l,
      scoreCellMass (pateSample index)
          (fun _unit => pateCommonWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index)
            (controlPrognosticScore index)) pateCell ≠ 0) ∧
      (∀ᶠ index in l,
        scoreCellMass (pattSample index)
            (fun _unit => pattCommonWeight index)
            (pattDoubleScore (propensityScore index)
              (pattPrognosticScore index)) pattCell ≠ 0) := by
  constructor
  · exact
      eventually_pateDoubleScoreCellMass_constant_weight_ne_zero_of_eventually_cell_card_ne_zero
        pateSample propensityScore treatedPrognosticScore
        controlPrognosticScore pateCell pateCommonWeight hpateWeight
        hpateCard
  · exact
      eventually_pattDoubleScoreCellMass_constant_weight_ne_zero_of_eventually_cell_card_ne_zero
        pattSample propensityScore pattPrognosticScore pattCell
        pattCommonWeight hpattWeight hpattCard

end WDSM
end Matching
end StatInference
