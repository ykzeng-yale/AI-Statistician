import StatInference.Matching.WDSM.DiscreteRetrospectivePropensity

/-!
# Finite retrospective propensity-weight recovery for WDSM

This module completes the finite retrospective propensity algebra loop.  Once
selected treated/control score-cell masses are treatment-specific sampling
multiples of target treated/control masses, the selected finite cell propensity
has the retrospective Bayes form.  Applying treatment-specific inverse
sampling weights then recovers the target finite cell propensity.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Unit Cell : Type*} [DecidableEq Cell]

theorem scoreCellTreatmentProbability_pos_of_cellMass_pos
    (sample : Finset Unit) (baseWeight : Unit -> Real)
    (score : Unit -> Cell) (treatment : Unit -> Prop)
    [DecidablePred treatment] (cell : Cell)
    (htreated :
      0 < scoreCellMass (sample.filter treatment) baseWeight score cell)
    (hcontrol :
      0 < scoreCellMass (sample.filter (fun unit => ¬ treatment unit))
        baseWeight score cell) :
    0 < scoreCellTreatmentProbability sample baseWeight score treatment cell := by
  have htotal_pos : 0 < scoreCellMass sample baseWeight score cell := by
    rw [(scoreCellMass_treated_add_control_eq sample baseWeight score
      treatment cell).symm]
    exact add_pos htreated hcontrol
  unfold scoreCellTreatmentProbability
  exact div_pos htreated htotal_pos

theorem scoreCellTreatmentProbability_lt_one_of_control_cellMass_pos
    (sample : Finset Unit) (baseWeight : Unit -> Real)
    (score : Unit -> Cell) (treatment : Unit -> Prop)
    [DecidablePred treatment] (cell : Cell)
    (htreated :
      0 < scoreCellMass (sample.filter treatment) baseWeight score cell)
    (hcontrol :
      0 < scoreCellMass (sample.filter (fun unit => ¬ treatment unit))
        baseWeight score cell) :
    scoreCellTreatmentProbability sample baseWeight score treatment cell < 1 := by
  have htotal_pos : 0 < scoreCellMass sample baseWeight score cell := by
    rw [(scoreCellMass_treated_add_control_eq sample baseWeight score
      treatment cell).symm]
    exact add_pos htreated hcontrol
  unfold scoreCellTreatmentProbability
  rw [div_lt_one htotal_pos]
  rw [(scoreCellMass_treated_add_control_eq sample baseWeight score
    treatment cell).symm]
  exact lt_add_of_pos_right
    (scoreCellMass (sample.filter treatment) baseWeight score cell) hcontrol

/--
Finite retrospective recovery of the target cell propensity from the selected
cell propensity using treatment-specific inverse sampling weights.
-/
theorem populationPropensityFromSelected_scoreCellTreatmentProbability_eq
    (targetSample selectedSample : Finset Unit)
    (baseWeight : Unit -> Real) (score : Unit -> Cell)
    (treatment : Unit -> Prop) [DecidablePred treatment] (cell : Cell)
    (samplingIfTreated samplingIfControl : Real)
    (htreatedTarget :
      0 < scoreCellMass (targetSample.filter treatment) baseWeight score cell)
    (hcontrolTarget :
      0 < scoreCellMass (targetSample.filter (fun unit => ¬ treatment unit))
        baseWeight score cell)
    (hsamplingTreated : 0 < samplingIfTreated)
    (hsamplingControl : 0 < samplingIfControl)
    (htreatedMass :
      scoreCellMass (selectedSample.filter treatment) baseWeight score cell =
        samplingIfTreated *
          scoreCellMass (targetSample.filter treatment) baseWeight score cell)
    (hcontrolMass :
      scoreCellMass (selectedSample.filter (fun unit => ¬ treatment unit))
          baseWeight score cell =
        samplingIfControl *
          scoreCellMass (targetSample.filter (fun unit => ¬ treatment unit))
            baseWeight score cell) :
    populationPropensityFromSelected (1 / samplingIfTreated)
        (1 / samplingIfControl)
        (scoreCellTreatmentProbability selectedSample baseWeight score
          treatment cell) =
      scoreCellTreatmentProbability targetSample baseWeight score treatment
        cell := by
  have htotal_pos : 0 < scoreCellMass targetSample baseWeight score cell := by
    rw [(scoreCellMass_treated_add_control_eq targetSample baseWeight score
      treatment cell).symm]
    exact add_pos htreatedTarget hcontrolTarget
  have hselected :
      scoreCellTreatmentProbability selectedSample baseWeight score treatment
          cell =
        selectedPropensity
          (scoreCellTreatmentProbability targetSample baseWeight score
            treatment cell)
          samplingIfTreated samplingIfControl :=
    scoreCellTreatmentProbability_selected_eq_selectedPropensity
      targetSample selectedSample baseWeight score treatment cell
      samplingIfTreated samplingIfControl htotal_pos.ne' htreatedMass
      hcontrolMass
  have htarget_pos :
      0 < scoreCellTreatmentProbability targetSample baseWeight score
        treatment cell :=
    scoreCellTreatmentProbability_pos_of_cellMass_pos targetSample baseWeight
      score treatment cell htreatedTarget hcontrolTarget
  have htarget_lt_one :
      scoreCellTreatmentProbability targetSample baseWeight score treatment
          cell < 1 :=
    scoreCellTreatmentProbability_lt_one_of_control_cellMass_pos targetSample
      baseWeight score treatment cell htreatedTarget hcontrolTarget
  rw [hselected]
  exact populationPropensityFromSelected_inverse_sampling_eq
    htarget_pos htarget_lt_one hsamplingTreated hsamplingControl

/--
Finite retrospective odds relation: target cell odds equal selected cell odds
multiplied by the inverse sampling-weight ratio.
-/
theorem scoreCellTreatmentProbability_odds_eq_weight_ratio_mul_selected_odds
    (targetSample selectedSample : Finset Unit)
    (baseWeight : Unit -> Real) (score : Unit -> Cell)
    (treatment : Unit -> Prop) [DecidablePred treatment] (cell : Cell)
    (samplingIfTreated samplingIfControl : Real)
    (htreatedTarget :
      0 < scoreCellMass (targetSample.filter treatment) baseWeight score cell)
    (hcontrolTarget :
      0 < scoreCellMass (targetSample.filter (fun unit => ¬ treatment unit))
        baseWeight score cell)
    (hsamplingTreated : 0 < samplingIfTreated)
    (hsamplingControl : 0 < samplingIfControl)
    (htreatedMass :
      scoreCellMass (selectedSample.filter treatment) baseWeight score cell =
        samplingIfTreated *
          scoreCellMass (targetSample.filter treatment) baseWeight score cell)
    (hcontrolMass :
      scoreCellMass (selectedSample.filter (fun unit => ¬ treatment unit))
          baseWeight score cell =
        samplingIfControl *
          scoreCellMass (targetSample.filter (fun unit => ¬ treatment unit))
            baseWeight score cell) :
    scoreCellTreatmentProbability targetSample baseWeight score treatment cell /
        (1 - scoreCellTreatmentProbability targetSample baseWeight score
          treatment cell) =
      ((1 / samplingIfTreated) / (1 / samplingIfControl)) *
        (scoreCellTreatmentProbability selectedSample baseWeight score
          treatment cell /
          (1 - scoreCellTreatmentProbability selectedSample baseWeight score
            treatment cell)) := by
  have htotal_pos : 0 < scoreCellMass targetSample baseWeight score cell := by
    rw [(scoreCellMass_treated_add_control_eq targetSample baseWeight score
      treatment cell).symm]
    exact add_pos htreatedTarget hcontrolTarget
  have hselected :
      scoreCellTreatmentProbability selectedSample baseWeight score treatment
          cell =
        selectedPropensity
          (scoreCellTreatmentProbability targetSample baseWeight score
            treatment cell)
          samplingIfTreated samplingIfControl :=
    scoreCellTreatmentProbability_selected_eq_selectedPropensity
      targetSample selectedSample baseWeight score treatment cell
      samplingIfTreated samplingIfControl htotal_pos.ne' htreatedMass
      hcontrolMass
  have htarget_pos :
      0 < scoreCellTreatmentProbability targetSample baseWeight score
        treatment cell :=
    scoreCellTreatmentProbability_pos_of_cellMass_pos targetSample baseWeight
      score treatment cell htreatedTarget hcontrolTarget
  have htarget_lt_one :
      scoreCellTreatmentProbability targetSample baseWeight score treatment
          cell < 1 :=
    scoreCellTreatmentProbability_lt_one_of_control_cellMass_pos targetSample
      baseWeight score treatment cell htreatedTarget hcontrolTarget
  rw [hselected]
  exact population_odds_eq_weight_ratio_mul_selected_odds
    htarget_pos htarget_lt_one hsamplingTreated hsamplingControl

end WDSM
end Matching
end StatInference
