import StatInference.Matching.WDSM.ProspectiveCountPositivityEventually

/-!
# Eventual count positivity from positive normalized-count limits

This module connects LLN-style positive normalized count limits to the
eventual finite positivity side conditions used by the prospective WDSM route.
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
If a positive normalizer times the sample size converges to a positive limit,
then the finite sample is eventually nonempty.
-/
theorem eventually_card_pos_of_tendsto_normalized_card_pos
    (sample : Index -> Finset Unit)
    (normalizer : Index -> Real)
    (cardLimit : Real)
    (hnormalizer : ∀ᶠ index in l, 0 < normalizer index)
    (hcard :
      Tendsto
        (fun index => normalizer index * ((sample index).card : Real))
        l (nhds cardLimit))
    (hlimit : 0 < cardLimit) :
    ∀ᶠ index in l, 0 < ((sample index).card : Real) := by
  have hnormalized :
      ∀ᶠ index in l,
        0 < normalizer index * ((sample index).card : Real) :=
    hcard.eventually (eventually_gt_nhds hlimit)
  filter_upwards [hnormalizer, hnormalized] with index hnorm hprod
  have hdiv :
      0 <
        (normalizer index * ((sample index).card : Real)) /
          normalizer index :=
    div_pos hprod hnorm
  rwa [mul_div_cancel_left₀ _ hnorm.ne'] at hdiv

/--
If a positive normalizer times the sample size converges to a positive limit,
then the finite sample is eventually nonempty.
-/
theorem eventually_sampleNonempty_of_tendsto_normalized_card_pos
    (sample : Index -> Finset Unit)
    (normalizer : Index -> Real)
    (cardLimit : Real)
    (hnormalizer : ∀ᶠ index in l, 0 < normalizer index)
    (hcard :
      Tendsto
        (fun index => normalizer index * ((sample index).card : Real))
        l (nhds cardLimit))
    (hlimit : 0 < cardLimit) :
    ∀ᶠ index in l, (sample index).Nonempty :=
  eventually_sampleNonempty_of_eventually_card_pos_real sample
    (eventually_card_pos_of_tendsto_normalized_card_pos
      sample normalizer cardLimit hnormalizer hcard hlimit)

/--
If a positive normalizer times a score-cell count converges to a positive
limit, then the raw score-cell count is eventually positive.
-/
theorem eventually_cell_card_pos_of_tendsto_normalized_cell_card_pos
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (cell : Cell)
    (normalizer : Index -> Real)
    (cellLimit : Real)
    (hnormalizer : ∀ᶠ index in l, 0 < normalizer index)
    (hcell :
      Tendsto
        (fun index =>
          normalizer index *
            (((sample index).filter
              (fun unit => score index unit = cell)).card : Real))
        l (nhds cellLimit))
    (hlimit : 0 < cellLimit) :
    ∀ᶠ index in l,
      0 < (((sample index).filter
        (fun unit => score index unit = cell)).card : Real) := by
  have hnormalized :
      ∀ᶠ index in l,
        0 <
          normalizer index *
            (((sample index).filter
              (fun unit => score index unit = cell)).card : Real) :=
    hcell.eventually (eventually_gt_nhds hlimit)
  filter_upwards [hnormalizer, hnormalized] with index hnorm hprod
  have hdiv :
      0 <
        (normalizer index *
            (((sample index).filter
              (fun unit => score index unit = cell)).card : Real)) /
          normalizer index :=
    div_pos hprod hnorm
  rwa [mul_div_cancel_left₀ _ hnorm.ne'] at hdiv

/--
Positive normalized score-cell count limits and eventually positive common
weights give eventually positive common-weight WDSM score-cell masses.
-/
theorem eventually_scoreCellMass_constant_weight_pos_of_tendsto_normalized_cell_card_pos
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (cell : Cell)
    (normalizer commonWeight : Index -> Real)
    (cellLimit : Real)
    (hnormalizer : ∀ᶠ index in l, 0 < normalizer index)
    (hweight : ∀ᶠ index in l, 0 < commonWeight index)
    (hcell :
      Tendsto
        (fun index =>
          normalizer index *
            (((sample index).filter
              (fun unit => score index unit = cell)).card : Real))
        l (nhds cellLimit))
    (hlimit : 0 < cellLimit) :
    ∀ᶠ index in l,
      0 < scoreCellMass (sample index)
        (fun _unit => commonWeight index) (score index) cell :=
  eventually_scoreCellMass_constant_weight_pos_of_eventually_pos_cell_card
    sample score cell commonWeight hweight
    (eventually_cell_card_pos_of_tendsto_normalized_cell_card_pos
      sample score cell normalizer cellLimit hnormalizer hcell hlimit)

/--
Positive normalized score-cell count limits and eventually nonzero common
weights give eventually nonzero common-weight WDSM score-cell masses.
-/
theorem eventually_scoreCellMass_constant_weight_ne_zero_of_tendsto_normalized_cell_card_pos
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (cell : Cell)
    (normalizer commonWeight : Index -> Real)
    (cellLimit : Real)
    (hnormalizer : ∀ᶠ index in l, 0 < normalizer index)
    (hweight : ∀ᶠ index in l, commonWeight index ≠ 0)
    (hcell :
      Tendsto
        (fun index =>
          normalizer index *
            (((sample index).filter
              (fun unit => score index unit = cell)).card : Real))
        l (nhds cellLimit))
    (hlimit : 0 < cellLimit) :
    ∀ᶠ index in l,
      scoreCellMass (sample index) (fun _unit => commonWeight index)
        (score index) cell ≠ 0 :=
  eventually_scoreCellMass_constant_weight_ne_zero_of_eventually_cell_card_ne_zero
    sample score cell commonWeight hweight
    ((eventually_cell_card_pos_of_tendsto_normalized_cell_card_pos
      sample score cell normalizer cellLimit hnormalizer hcell hlimit).mono
      (fun _index hpos => hpos.ne'))

/--
PATE double-score specialization: positive normalized cell-count limits give
eventually nonzero common-weight PATE score-cell masses.
-/
theorem eventually_pateDoubleScoreCellMass_constant_weight_ne_zero_of_tendsto_normalized_cell_card_pos
    (sample : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (cell : (PropensityCell × TreatedProgCell) × ControlProgCell)
    (normalizer commonWeight : Index -> Real)
    (cellLimit : Real)
    (hnormalizer : ∀ᶠ index in l, 0 < normalizer index)
    (hweight : ∀ᶠ index in l, commonWeight index ≠ 0)
    (hcell :
      Tendsto
        (fun index =>
          normalizer index *
            (((sample index).filter
              (fun unit =>
                pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index) unit = cell)).card :
              Real))
        l (nhds cellLimit))
    (hlimit : 0 < cellLimit) :
    ∀ᶠ index in l,
      scoreCellMass (sample index) (fun _unit => commonWeight index)
        (pateDoubleScore (propensityScore index)
          (treatedPrognosticScore index)
          (controlPrognosticScore index)) cell ≠ 0 :=
  eventually_scoreCellMass_constant_weight_ne_zero_of_tendsto_normalized_cell_card_pos
    sample
    (fun index =>
      pateDoubleScore (propensityScore index)
        (treatedPrognosticScore index)
        (controlPrognosticScore index))
    cell normalizer commonWeight cellLimit hnormalizer hweight hcell hlimit

/--
PATT double-score specialization: positive normalized cell-count limits give
eventually nonzero common-weight PATT score-cell masses.
-/
theorem eventually_pattDoubleScoreCellMass_constant_weight_ne_zero_of_tendsto_normalized_cell_card_pos
    (sample : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (cell : PropensityCell × PATTProgCell)
    (normalizer commonWeight : Index -> Real)
    (cellLimit : Real)
    (hnormalizer : ∀ᶠ index in l, 0 < normalizer index)
    (hweight : ∀ᶠ index in l, commonWeight index ≠ 0)
    (hcell :
      Tendsto
        (fun index =>
          normalizer index *
            (((sample index).filter
              (fun unit =>
                pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index) unit = cell)).card :
              Real))
        l (nhds cellLimit))
    (hlimit : 0 < cellLimit) :
    ∀ᶠ index in l,
      scoreCellMass (sample index) (fun _unit => commonWeight index)
        (pattDoubleScore (propensityScore index)
          (controlPrognosticScore index)) cell ≠ 0 :=
  eventually_scoreCellMass_constant_weight_ne_zero_of_tendsto_normalized_cell_card_pos
    sample
    (fun index =>
      pattDoubleScore (propensityScore index)
        (controlPrognosticScore index))
    cell normalizer commonWeight cellLimit hnormalizer hweight hcell hlimit

/--
Paired PATE/PATT double-score specialization: positive normalized cell-count
limits give eventually nonzero common-weight score-cell masses.
-/
theorem eventually_pate_pattDoubleScoreCellMass_constant_weight_ne_zero_of_tendsto_normalized_cell_card_pos
    (pateSample pattSample : Index -> Finset Unit)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (pattPrognosticScore : Index -> Unit -> PATTProgCell)
    (pateCell : (PropensityCell × TreatedProgCell) × ControlProgCell)
    (pattCell : PropensityCell × PATTProgCell)
    (pateNormalizer pateCommonWeight pattNormalizer pattCommonWeight :
      Index -> Real)
    (pateCellLimit pattCellLimit : Real)
    (hpateNormalizer : ∀ᶠ index in l, 0 < pateNormalizer index)
    (hpattNormalizer : ∀ᶠ index in l, 0 < pattNormalizer index)
    (hpateWeight : ∀ᶠ index in l, pateCommonWeight index ≠ 0)
    (hpattWeight : ∀ᶠ index in l, pattCommonWeight index ≠ 0)
    (hpateCell :
      Tendsto
        (fun index =>
          pateNormalizer index *
            (((pateSample index).filter
              (fun unit =>
                pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index) unit = pateCell)).card :
              Real))
        l (nhds pateCellLimit))
    (hpattCell :
      Tendsto
        (fun index =>
          pattNormalizer index *
            (((pattSample index).filter
              (fun unit =>
                pattDoubleScore (propensityScore index)
                  (pattPrognosticScore index) unit = pattCell)).card :
              Real))
        l (nhds pattCellLimit))
    (hpateLimit : 0 < pateCellLimit)
    (hpattLimit : 0 < pattCellLimit) :
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
      eventually_pateDoubleScoreCellMass_constant_weight_ne_zero_of_tendsto_normalized_cell_card_pos
        pateSample propensityScore treatedPrognosticScore
        controlPrognosticScore pateCell pateNormalizer pateCommonWeight
        pateCellLimit hpateNormalizer hpateWeight hpateCell hpateLimit
  · exact
      eventually_pattDoubleScoreCellMass_constant_weight_ne_zero_of_tendsto_normalized_cell_card_pos
        pattSample propensityScore pattPrognosticScore pattCell
        pattNormalizer pattCommonWeight pattCellLimit hpattNormalizer
        hpattWeight hpattCell hpattLimit

end WDSM
end Matching
end StatInference
