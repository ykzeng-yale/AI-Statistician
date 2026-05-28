import StatInference.Matching.WDSM.ProspectiveScoreCellShareConvergence

/-!
# Prospective finite count positivity for WDSM

The prospective normalized-count route leaves finite side conditions such as
nonempty samples and nonzero score-cell masses.  This module proves the
deterministic common-weight facts that discharge those side conditions from
ordinary finite count positivity.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Unit Cell PropensityCell TreatedProgCell ControlProgCell PATTProgCell : Type*}
  [DecidableEq Cell] [DecidableEq PropensityCell]
  [DecidableEq TreatedProgCell] [DecidableEq ControlProgCell]
  [DecidableEq PATTProgCell]

/-- A nonzero real-valued finite cardinality gives a nonempty finite sample. -/
theorem sampleNonempty_of_card_ne_zero_real
    (sample : Finset Unit) (hcard : (sample.card : Real) ≠ 0) :
    sample.Nonempty := by
  rw [← Finset.card_ne_zero]
  exact_mod_cast hcard

/-- A positive real-valued finite cardinality gives a nonempty finite sample. -/
theorem sampleNonempty_of_card_pos_real
    (sample : Finset Unit) (hcard : 0 < (sample.card : Real)) :
    sample.Nonempty :=
  sampleNonempty_of_card_ne_zero_real sample hcard.ne'

/--
Under a nonzero common survey weight, a nonzero finite score-cell count gives a
nonzero WDSM score-cell mass.
-/
theorem scoreCellMass_constant_weight_ne_zero_of_cell_card_ne_zero
    (sample : Finset Unit) (score : Unit -> Cell) (cell : Cell)
    (commonWeight : Real)
    (hweight : commonWeight ≠ 0)
    (hcard :
      (((sample.filter (fun unit => score unit = cell)).card : Real) ≠ 0)) :
    scoreCellMass sample (fun _unit => commonWeight) score cell ≠ 0 := by
  rw [scoreCellMass_constant_weight_eq_card]
  exact mul_ne_zero hweight hcard

/--
Under a positive common survey weight, a positive finite score-cell count gives
a positive WDSM score-cell mass.
-/
theorem scoreCellMass_constant_weight_pos_of_pos_of_cell_card_pos
    (sample : Finset Unit) (score : Unit -> Cell) (cell : Cell)
    (commonWeight : Real)
    (hweight : 0 < commonWeight)
    (hcard :
      0 < ((sample.filter (fun unit => score unit = cell)).card : Real)) :
    0 < scoreCellMass sample (fun _unit => commonWeight) score cell := by
  rw [scoreCellMass_constant_weight_eq_card]
  exact mul_pos hweight hcard

/--
Positive common weights and positive finite cell counts imply nonzero WDSM
score-cell masses.
-/
theorem scoreCellMass_constant_weight_ne_zero_of_pos_of_cell_card_pos
    (sample : Finset Unit) (score : Unit -> Cell) (cell : Cell)
    (commonWeight : Real)
    (hweight : 0 < commonWeight)
    (hcard :
      0 < ((sample.filter (fun unit => score unit = cell)).card : Real)) :
    scoreCellMass sample (fun _unit => commonWeight) score cell ≠ 0 :=
  (scoreCellMass_constant_weight_pos_of_pos_of_cell_card_pos
    sample score cell commonWeight hweight hcard).ne'

/--
PATE double-score specialization of nonzero common-weight cell masses from
nonzero finite cell counts.
-/
theorem pateDoubleScoreCellMass_constant_weight_ne_zero_of_cell_card_ne_zero
    (sample : Finset Unit)
    (propensityScore : Unit -> PropensityCell)
    (treatedPrognosticScore : Unit -> TreatedProgCell)
    (controlPrognosticScore : Unit -> ControlProgCell)
    (cell : (PropensityCell × TreatedProgCell) × ControlProgCell)
    (commonWeight : Real)
    (hweight : commonWeight ≠ 0)
    (hcard :
      (((sample.filter
        (fun unit =>
          pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore unit = cell)).card : Real) ≠ 0)) :
    scoreCellMass sample (fun _unit => commonWeight)
      (pateDoubleScore propensityScore treatedPrognosticScore
        controlPrognosticScore) cell ≠ 0 :=
  scoreCellMass_constant_weight_ne_zero_of_cell_card_ne_zero sample
    (pateDoubleScore propensityScore treatedPrognosticScore
      controlPrognosticScore) cell commonWeight hweight hcard

/--
PATT double-score specialization of nonzero common-weight cell masses from
nonzero finite cell counts.
-/
theorem pattDoubleScoreCellMass_constant_weight_ne_zero_of_cell_card_ne_zero
    (sample : Finset Unit)
    (propensityScore : Unit -> PropensityCell)
    (controlPrognosticScore : Unit -> PATTProgCell)
    (cell : PropensityCell × PATTProgCell)
    (commonWeight : Real)
    (hweight : commonWeight ≠ 0)
    (hcard :
      (((sample.filter
        (fun unit =>
          pattDoubleScore propensityScore controlPrognosticScore unit =
            cell)).card : Real) ≠ 0)) :
    scoreCellMass sample (fun _unit => commonWeight)
      (pattDoubleScore propensityScore controlPrognosticScore) cell ≠ 0 :=
  scoreCellMass_constant_weight_ne_zero_of_cell_card_ne_zero sample
    (pattDoubleScore propensityScore controlPrognosticScore) cell
    commonWeight hweight hcard

/--
Paired PATE/PATT double-score specialization of nonzero common-weight cell
masses from nonzero finite cell counts.
-/
theorem pate_pattDoubleScoreCellMass_constant_weight_ne_zero_of_cell_card_ne_zero
    (pateSample pattSample : Finset Unit)
    (propensityScore : Unit -> PropensityCell)
    (treatedPrognosticScore : Unit -> TreatedProgCell)
    (controlPrognosticScore : Unit -> ControlProgCell)
    (pattPrognosticScore : Unit -> PATTProgCell)
    (pateCell : (PropensityCell × TreatedProgCell) × ControlProgCell)
    (pattCell : PropensityCell × PATTProgCell)
    (pateCommonWeight pattCommonWeight : Real)
    (hpateWeight : pateCommonWeight ≠ 0)
    (hpattWeight : pattCommonWeight ≠ 0)
    (hpateCard :
      (((pateSample.filter
        (fun unit =>
          pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore unit = pateCell)).card : Real) ≠ 0))
    (hpattCard :
      (((pattSample.filter
        (fun unit =>
          pattDoubleScore propensityScore pattPrognosticScore unit =
            pattCell)).card : Real) ≠ 0)) :
    scoreCellMass pateSample (fun _unit => pateCommonWeight)
        (pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore) pateCell ≠ 0 ∧
      scoreCellMass pattSample (fun _unit => pattCommonWeight)
        (pattDoubleScore propensityScore pattPrognosticScore) pattCell ≠ 0 := by
  constructor
  · exact
      pateDoubleScoreCellMass_constant_weight_ne_zero_of_cell_card_ne_zero
        pateSample propensityScore treatedPrognosticScore
        controlPrognosticScore pateCell pateCommonWeight hpateWeight
        hpateCard
  · exact
      pattDoubleScoreCellMass_constant_weight_ne_zero_of_cell_card_ne_zero
        pattSample propensityScore pattPrognosticScore pattCell
        pattCommonWeight hpattWeight hpattCard

end WDSM
end Matching
end StatInference
