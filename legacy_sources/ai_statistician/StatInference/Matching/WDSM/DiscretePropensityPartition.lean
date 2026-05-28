import StatInference.Matching.WDSM.DiscretePropensityBalancing

/-!
# Finite binary cell-propensity partition algebra for WDSM

This module proves the binary-treatment algebra behind the finite
cell-propensity route.  Treated and control weighted masses partition each
score cell, so the corresponding finite treatment and control cell
propensities sum to one and have the expected odds representation.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Unit Cell : Type*} [DecidableEq Cell]

theorem scoreCellMass_treated_add_control_eq
    (sample : Finset Unit) (baseWeight : Unit -> Real)
    (score : Unit -> Cell) (treatment : Unit -> Prop)
    [DecidablePred treatment] (cell : Cell) :
    scoreCellMass (sample.filter treatment) baseWeight score cell +
      scoreCellMass (sample.filter (fun unit => ¬ treatment unit))
        baseWeight score cell =
      scoreCellMass sample baseWeight score cell := by
  unfold scoreCellMass
  have htreatedSet :
      (sample.filter treatment).filter (fun unit => score unit = cell) =
        (sample.filter (fun unit => score unit = cell)).filter treatment := by
    ext unit
    simp [and_comm, and_left_comm]
  have hcontrolSet :
      (sample.filter (fun unit => ¬ treatment unit)).filter
          (fun unit => score unit = cell) =
        (sample.filter (fun unit => score unit = cell)).filter
          (fun unit => ¬ treatment unit) := by
    ext unit
    simp [and_comm, and_left_comm]
  rw [htreatedSet, hcontrolSet]
  exact Finset.sum_filter_add_sum_filter_not
    (sample.filter (fun unit => score unit = cell)) treatment baseWeight

theorem scoreCellTreatmentProbability_add_controlProbability_eq_one
    (sample : Finset Unit) (baseWeight : Unit -> Real)
    (score : Unit -> Cell) (treatment : Unit -> Prop)
    [DecidablePred treatment] (cell : Cell)
    (hmass : scoreCellMass sample baseWeight score cell ≠ 0) :
    scoreCellTreatmentProbability sample baseWeight score treatment cell +
      scoreCellControlProbability sample baseWeight score treatment cell = 1 := by
  unfold scoreCellTreatmentProbability scoreCellControlProbability
  rw [← add_div]
  rw [scoreCellMass_treated_add_control_eq sample baseWeight score treatment cell]
  exact div_self hmass

theorem one_sub_scoreCellTreatmentProbability_eq_controlProbability
    (sample : Finset Unit) (baseWeight : Unit -> Real)
    (score : Unit -> Cell) (treatment : Unit -> Prop)
    [DecidablePred treatment] (cell : Cell)
    (hmass : scoreCellMass sample baseWeight score cell ≠ 0) :
    1 - scoreCellTreatmentProbability sample baseWeight score treatment cell =
      scoreCellControlProbability sample baseWeight score treatment cell := by
  have hsum :=
    scoreCellTreatmentProbability_add_controlProbability_eq_one
      sample baseWeight score treatment cell hmass
  linarith

theorem one_sub_scoreCellControlProbability_eq_treatmentProbability
    (sample : Finset Unit) (baseWeight : Unit -> Real)
    (score : Unit -> Cell) (treatment : Unit -> Prop)
    [DecidablePred treatment] (cell : Cell)
    (hmass : scoreCellMass sample baseWeight score cell ≠ 0) :
    1 - scoreCellControlProbability sample baseWeight score treatment cell =
      scoreCellTreatmentProbability sample baseWeight score treatment cell := by
  have hsum :=
    scoreCellTreatmentProbability_add_controlProbability_eq_one
      sample baseWeight score treatment cell hmass
  linarith

theorem scoreCellTreatmentProbability_div_controlProbability_eq_mass_ratio
    (sample : Finset Unit) (baseWeight : Unit -> Real)
    (score : Unit -> Cell) (treatment : Unit -> Prop)
    [DecidablePred treatment] (cell : Cell)
    (hmass : scoreCellMass sample baseWeight score cell ≠ 0)
    (hcontrol :
      scoreCellMass (sample.filter (fun unit => ¬ treatment unit))
        baseWeight score cell ≠ 0) :
    scoreCellTreatmentProbability sample baseWeight score treatment cell /
        scoreCellControlProbability sample baseWeight score treatment cell =
      scoreCellMass (sample.filter treatment) baseWeight score cell /
        scoreCellMass (sample.filter (fun unit => ¬ treatment unit))
          baseWeight score cell := by
  unfold scoreCellTreatmentProbability scoreCellControlProbability
  field_simp [hmass, hcontrol]

theorem scoreCellTreatmentProbability_odds_eq_mass_ratio
    (sample : Finset Unit) (baseWeight : Unit -> Real)
    (score : Unit -> Cell) (treatment : Unit -> Prop)
    [DecidablePred treatment] (cell : Cell)
    (hmass : scoreCellMass sample baseWeight score cell ≠ 0)
    (hcontrol :
      scoreCellMass (sample.filter (fun unit => ¬ treatment unit))
        baseWeight score cell ≠ 0) :
    scoreCellTreatmentProbability sample baseWeight score treatment cell /
        (1 - scoreCellTreatmentProbability sample baseWeight score treatment cell) =
      scoreCellMass (sample.filter treatment) baseWeight score cell /
        scoreCellMass (sample.filter (fun unit => ¬ treatment unit))
          baseWeight score cell := by
  rw [one_sub_scoreCellTreatmentProbability_eq_controlProbability
    sample baseWeight score treatment cell hmass]
  exact scoreCellTreatmentProbability_div_controlProbability_eq_mass_ratio
    sample baseWeight score treatment cell hmass hcontrol

theorem scoreCellTreatmentProbability_nonneg
    (sample : Finset Unit) (baseWeight : Unit -> Real)
    (score : Unit -> Cell) (treatment : Unit -> Prop)
    [DecidablePred treatment] (cell : Cell)
    (hmass_nonneg : 0 ≤ scoreCellMass sample baseWeight score cell)
    (hweight :
      ∀ unit, unit ∈ sample -> treatment unit -> score unit = cell ->
        0 ≤ baseWeight unit) :
    0 ≤ scoreCellTreatmentProbability sample baseWeight score treatment cell := by
  unfold scoreCellTreatmentProbability
  exact div_nonneg
    (scoreCellMass_nonneg (sample.filter treatment) baseWeight score cell
      (fun unit hunit hscore =>
        hweight unit (Finset.mem_filter.mp hunit).1
          (Finset.mem_filter.mp hunit).2 hscore))
    hmass_nonneg

theorem scoreCellControlProbability_nonneg
    (sample : Finset Unit) (baseWeight : Unit -> Real)
    (score : Unit -> Cell) (treatment : Unit -> Prop)
    [DecidablePred treatment] (cell : Cell)
    (hmass_nonneg : 0 ≤ scoreCellMass sample baseWeight score cell)
    (hweight :
      ∀ unit, unit ∈ sample -> ¬ treatment unit -> score unit = cell ->
        0 ≤ baseWeight unit) :
    0 ≤ scoreCellControlProbability sample baseWeight score treatment cell := by
  unfold scoreCellControlProbability
  exact div_nonneg
    (scoreCellMass_nonneg
      (sample.filter (fun unit => ¬ treatment unit)) baseWeight score cell
      (fun unit hunit hscore =>
        hweight unit (Finset.mem_filter.mp hunit).1
          (Finset.mem_filter.mp hunit).2 hscore))
    hmass_nonneg

end WDSM
end Matching
end StatInference
