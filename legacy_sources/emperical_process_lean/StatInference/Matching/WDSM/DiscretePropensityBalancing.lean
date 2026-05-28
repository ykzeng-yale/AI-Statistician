import StatInference.Matching.WDSM.DiscreteInverseProbabilityBalancing

/-!
# Finite cell-propensity balancing for WDSM

This module connects the finite inverse-probability balancing theorem to a
binary-treatment cell propensity defined as a finite weighted treated-cell
mass divided by the target cell mass.  The result is deterministic: the
remaining probability-layer task is to prove that this finite cell-propensity
object is the Lean analogue of the population double-score propensity route.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Unit Cell : Type*} [DecidableEq Cell]

/-- Finite score-cell treatment probability as treated cell mass over target cell mass. -/
noncomputable def scoreCellTreatmentProbability
    (sample : Finset Unit) (baseWeight : Unit -> Real)
    (score : Unit -> Cell) (treatment : Unit -> Prop)
    [DecidablePred treatment] (cell : Cell) : Real :=
  scoreCellMass (sample.filter treatment) baseWeight score cell /
    scoreCellMass sample baseWeight score cell

/-- Finite score-cell control probability as control cell mass over target cell mass. -/
noncomputable def scoreCellControlProbability
    (sample : Finset Unit) (baseWeight : Unit -> Real)
    (score : Unit -> Cell) (treatment : Unit -> Prop)
    [DecidablePred treatment] (cell : Cell) : Real :=
  scoreCellMass (sample.filter (fun unit => ¬ treatment unit))
      baseWeight score cell /
    scoreCellMass sample baseWeight score cell

theorem scoreCellTreatmentMass_eq_treatmentProbability_mul_cellMass
    (sample : Finset Unit) (baseWeight : Unit -> Real)
    (score : Unit -> Cell) (treatment : Unit -> Prop)
    [DecidablePred treatment] (cell : Cell)
    (hmass : scoreCellMass sample baseWeight score cell ≠ 0) :
    scoreCellMass (sample.filter treatment) baseWeight score cell =
      scoreCellTreatmentProbability sample baseWeight score treatment cell *
        scoreCellMass sample baseWeight score cell := by
  unfold scoreCellTreatmentProbability
  field_simp [hmass]

theorem scoreCellControlMass_eq_controlProbability_mul_cellMass
    (sample : Finset Unit) (baseWeight : Unit -> Real)
    (score : Unit -> Cell) (treatment : Unit -> Prop)
    [DecidablePred treatment] (cell : Cell)
    (hmass : scoreCellMass sample baseWeight score cell ≠ 0) :
    scoreCellMass (sample.filter (fun unit => ¬ treatment unit))
        baseWeight score cell =
      scoreCellControlProbability sample baseWeight score treatment cell *
        scoreCellMass sample baseWeight score cell := by
  unfold scoreCellControlProbability
  field_simp [hmass]

theorem scoreCellTreatmentProbability_ne_zero
    (sample : Finset Unit) (baseWeight : Unit -> Real)
    (score : Unit -> Cell) (treatment : Unit -> Prop)
    [DecidablePred treatment] (cell : Cell)
    (htreated :
      scoreCellMass (sample.filter treatment) baseWeight score cell ≠ 0)
    (hmass : scoreCellMass sample baseWeight score cell ≠ 0) :
    scoreCellTreatmentProbability sample baseWeight score treatment cell ≠ 0 := by
  unfold scoreCellTreatmentProbability
  exact div_ne_zero htreated hmass

theorem scoreCellControlProbability_ne_zero
    (sample : Finset Unit) (baseWeight : Unit -> Real)
    (score : Unit -> Cell) (treatment : Unit -> Prop)
    [DecidablePred treatment] (cell : Cell)
    (hcontrol :
      scoreCellMass (sample.filter (fun unit => ¬ treatment unit))
        baseWeight score cell ≠ 0)
    (hmass : scoreCellMass sample baseWeight score cell ≠ 0) :
    scoreCellControlProbability sample baseWeight score treatment cell ≠ 0 := by
  unfold scoreCellControlProbability
  exact div_ne_zero hcontrol hmass

theorem scoreCellShare_treated_inverseTreatmentProbability_eq
    (sample : Finset Unit) (cells : Finset Cell)
    (baseWeight : Unit -> Real) (score : Unit -> Cell)
    (treatment : Unit -> Prop) [DecidablePred treatment] (cell : Cell)
    (hcover : ∀ unit, unit ∈ sample -> score unit ∈ cells)
    (hcell : cell ∈ cells)
    (hmass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sample baseWeight score cell ≠ 0)
    (htreated :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (sample.filter treatment) baseWeight score cell ≠ 0) :
    scoreCellShare (sample.filter treatment)
        (inverseCellProbabilityWeight baseWeight score
          (scoreCellTreatmentProbability sample baseWeight score treatment))
        score cell =
      scoreCellShare sample baseWeight score cell := by
  exact scoreCellShare_inverseCellProbabilityWeight_eq_of_cellMass_eq
    sample (sample.filter treatment) cells baseWeight score
    (scoreCellTreatmentProbability sample baseWeight score treatment) cell
    hcover
    (fun unit hunit => hcover unit (Finset.mem_filter.mp hunit).1)
    (fun cell hcell =>
      scoreCellTreatmentProbability_ne_zero sample baseWeight score
        treatment cell (htreated cell hcell) (hmass cell hcell))
    hcell
    (fun cell hcell =>
      scoreCellTreatmentMass_eq_treatmentProbability_mul_cellMass
        sample baseWeight score treatment cell (hmass cell hcell))

theorem scoreCellShare_control_inverseControlProbability_eq
    (sample : Finset Unit) (cells : Finset Cell)
    (baseWeight : Unit -> Real) (score : Unit -> Cell)
    (treatment : Unit -> Prop) [DecidablePred treatment] (cell : Cell)
    (hcover : ∀ unit, unit ∈ sample -> score unit ∈ cells)
    (hcell : cell ∈ cells)
    (hmass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sample baseWeight score cell ≠ 0)
    (hcontrol :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (sample.filter (fun unit => ¬ treatment unit))
          baseWeight score cell ≠ 0) :
    scoreCellShare (sample.filter (fun unit => ¬ treatment unit))
        (inverseCellProbabilityWeight baseWeight score
          (scoreCellControlProbability sample baseWeight score treatment))
        score cell =
      scoreCellShare sample baseWeight score cell := by
  exact scoreCellShare_inverseCellProbabilityWeight_eq_of_cellMass_eq
    sample (sample.filter (fun unit => ¬ treatment unit)) cells baseWeight
    score (scoreCellControlProbability sample baseWeight score treatment)
    cell hcover
    (fun unit hunit => hcover unit (Finset.mem_filter.mp hunit).1)
    (fun cell hcell =>
      scoreCellControlProbability_ne_zero sample baseWeight score treatment
        cell (hcontrol cell hcell) (hmass cell hcell))
    hcell
    (fun cell hcell =>
      scoreCellControlMass_eq_controlProbability_mul_cellMass
        sample baseWeight score treatment cell (hmass cell hcell))

/--
Finite PATE balancing through cell propensities defined by treated/control
weighted cell-mass ratios.
-/
theorem weightedSampleMeanContrast_eq_twoArmCellPropensityWeightedMeanContrast
    (sample : Finset Unit) (cells : Finset Cell)
    (baseWeight : Unit -> Real)
    (targetOutcomeT targetOutcomeC treatedOutcome controlOutcome : Unit -> Real)
    (score : Unit -> Cell) (treatment : Unit -> Prop)
    [DecidablePred treatment]
    (treatedCellValue controlCellValue : Cell -> Real)
    (hcover : ∀ unit, unit ∈ sample -> score unit ∈ cells)
    (hmass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sample baseWeight score cell ≠ 0)
    (htreated :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (sample.filter treatment) baseWeight score cell ≠ 0)
    (hcontrol :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (sample.filter (fun unit => ¬ treatment unit))
          baseWeight score cell ≠ 0)
    (hscoreMeasTargetT :
      ∀ unit, unit ∈ sample ->
        targetOutcomeT unit = treatedCellValue (score unit))
    (hscoreMeasTreated :
      ∀ unit, unit ∈ sample.filter treatment ->
        treatedOutcome unit = treatedCellValue (score unit))
    (hscoreMeasTargetC :
      ∀ unit, unit ∈ sample ->
        targetOutcomeC unit = controlCellValue (score unit))
    (hscoreMeasControl :
      ∀ unit, unit ∈ sample.filter (fun unit => ¬ treatment unit) ->
        controlOutcome unit = controlCellValue (score unit)) :
    weightedSampleMeanContrast sample baseWeight
        targetOutcomeT targetOutcomeC =
      twoArmWeightedMeanContrast (sample.filter treatment)
        (sample.filter (fun unit => ¬ treatment unit))
        (inverseCellProbabilityWeight baseWeight score
          (scoreCellTreatmentProbability sample baseWeight score treatment))
        (inverseCellProbabilityWeight baseWeight score
          (scoreCellControlProbability sample baseWeight score treatment))
        treatedOutcome controlOutcome := by
  exact
    weightedSampleMeanContrast_eq_twoArmInverseProbabilityWeightedMeanContrast
      sample (sample.filter treatment)
      (sample.filter (fun unit => ¬ treatment unit)) cells baseWeight
      targetOutcomeT targetOutcomeC treatedOutcome controlOutcome score
      (scoreCellTreatmentProbability sample baseWeight score treatment)
      (scoreCellControlProbability sample baseWeight score treatment)
      treatedCellValue controlCellValue hcover
      (fun unit hunit => hcover unit (Finset.mem_filter.mp hunit).1)
      (fun unit hunit => hcover unit (Finset.mem_filter.mp hunit).1)
      hmass
      (fun cell hcell =>
        scoreCellTreatmentProbability_ne_zero sample baseWeight score
          treatment cell (htreated cell hcell) (hmass cell hcell))
      (fun cell hcell =>
        scoreCellControlProbability_ne_zero sample baseWeight score treatment
          cell (hcontrol cell hcell) (hmass cell hcell))
      (fun cell hcell =>
        scoreCellTreatmentMass_eq_treatmentProbability_mul_cellMass
          sample baseWeight score treatment cell (hmass cell hcell))
      (fun cell hcell =>
        scoreCellControlMass_eq_controlProbability_mul_cellMass
          sample baseWeight score treatment cell (hmass cell hcell))
      hscoreMeasTargetT hscoreMeasTreated hscoreMeasTargetC hscoreMeasControl

/--
Finite PATT balancing through the control cell propensity defined by the
control weighted cell-mass ratio.
-/
theorem weightedSampleMeanContrast_eq_pattCellPropensityWeightedMeanContrast
    (sample : Finset Unit) (cells : Finset Cell)
    (baseWeight : Unit -> Real)
    (treatedTargetOutcome targetControlOutcome controlOutcome : Unit -> Real)
    (score : Unit -> Cell) (treatment : Unit -> Prop)
    [DecidablePred treatment]
    (controlCellValue : Cell -> Real)
    (hcover : ∀ unit, unit ∈ sample -> score unit ∈ cells)
    (hmass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sample baseWeight score cell ≠ 0)
    (hcontrol :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (sample.filter (fun unit => ¬ treatment unit))
          baseWeight score cell ≠ 0)
    (hscoreMeasTargetC :
      ∀ unit, unit ∈ sample ->
        targetControlOutcome unit = controlCellValue (score unit))
    (hscoreMeasControl :
      ∀ unit, unit ∈ sample.filter (fun unit => ¬ treatment unit) ->
        controlOutcome unit = controlCellValue (score unit)) :
    weightedSampleMeanContrast sample baseWeight
        treatedTargetOutcome targetControlOutcome =
      pattWeightedMeanContrast sample
        (sample.filter (fun unit => ¬ treatment unit)) baseWeight
        (inverseCellProbabilityWeight baseWeight score
          (scoreCellControlProbability sample baseWeight score treatment))
        treatedTargetOutcome controlOutcome := by
  exact
    weightedSampleMeanContrast_eq_pattInverseProbabilityWeightedMeanContrast
      sample (sample.filter (fun unit => ¬ treatment unit)) cells baseWeight
      treatedTargetOutcome targetControlOutcome controlOutcome score
      (scoreCellControlProbability sample baseWeight score treatment)
      controlCellValue hcover
      (fun unit hunit => hcover unit (Finset.mem_filter.mp hunit).1)
      hmass
      (fun cell hcell =>
        scoreCellControlProbability_ne_zero sample baseWeight score treatment
          cell (hcontrol cell hcell) (hmass cell hcell))
      (fun cell hcell =>
        scoreCellControlMass_eq_controlProbability_mul_cellMass
          sample baseWeight score treatment cell (hmass cell hcell))
      hscoreMeasTargetC hscoreMeasControl

end WDSM
end Matching
end StatInference
