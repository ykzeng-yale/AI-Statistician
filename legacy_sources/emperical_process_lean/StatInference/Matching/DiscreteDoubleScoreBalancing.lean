import StatInference.Matching.WDSM.DiscretePropensityBalancing

/-!
# Finite double-score balancing wrappers for WDSM

This module packages the finite cell-propensity balancing results for joint
double-score cells.  It proves the deterministic projection step: if arm
outcomes are functions of prognostic-score components, then they are functions
of the joint score cell used for propensity weighting.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Unit PropensityCell TreatedProgCell ControlProgCell : Type*}
  [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
  [DecidableEq ControlProgCell]

/--
Joint finite score for a PATE target: propensity score plus both arm-specific
prognostic scores.
-/
def pateDoubleScore
    (propensityScore : Unit -> PropensityCell)
    (treatedPrognosticScore : Unit -> TreatedProgCell)
    (controlPrognosticScore : Unit -> ControlProgCell) :
    Unit -> (PropensityCell × TreatedProgCell) × ControlProgCell :=
  fun unit =>
    ((propensityScore unit, treatedPrognosticScore unit),
      controlPrognosticScore unit)

/-- Treated prognostic value lifted to the PATE joint score cell. -/
def treatedCellValueOnPATEDoubleScore
    (treatedValue : TreatedProgCell -> Real) :
    (PropensityCell × TreatedProgCell) × ControlProgCell -> Real :=
  fun cell => treatedValue cell.1.2

/-- Control prognostic value lifted to the PATE joint score cell. -/
def controlCellValueOnPATEDoubleScore
    (controlValue : ControlProgCell -> Real) :
    (PropensityCell × TreatedProgCell) × ControlProgCell -> Real :=
  fun cell => controlValue cell.2

omit [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
  [DecidableEq ControlProgCell] in
theorem treated_scoreMeasurable_pateDoubleScore
    (propensityScore : Unit -> PropensityCell)
    (treatedPrognosticScore : Unit -> TreatedProgCell)
    (controlPrognosticScore : Unit -> ControlProgCell)
    (outcome : Unit -> Real) (treatedValue : TreatedProgCell -> Real)
    (sample : Finset Unit)
    (h :
      ∀ unit, unit ∈ sample ->
        outcome unit = treatedValue (treatedPrognosticScore unit)) :
    ∀ unit, unit ∈ sample ->
      outcome unit =
        treatedCellValueOnPATEDoubleScore treatedValue
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore unit) := by
  intro unit hunit
  simpa [treatedCellValueOnPATEDoubleScore, pateDoubleScore] using h unit hunit

omit [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
  [DecidableEq ControlProgCell] in
theorem control_scoreMeasurable_pateDoubleScore
    (propensityScore : Unit -> PropensityCell)
    (treatedPrognosticScore : Unit -> TreatedProgCell)
    (controlPrognosticScore : Unit -> ControlProgCell)
    (outcome : Unit -> Real) (controlValue : ControlProgCell -> Real)
    (sample : Finset Unit)
    (h :
      ∀ unit, unit ∈ sample ->
        outcome unit = controlValue (controlPrognosticScore unit)) :
    ∀ unit, unit ∈ sample ->
      outcome unit =
        controlCellValueOnPATEDoubleScore controlValue
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore unit) := by
  intro unit hunit
  simpa [controlCellValueOnPATEDoubleScore, pateDoubleScore] using h unit hunit

/--
Finite PATE double-score propensity wrapper.  The existing finite
cell-propensity balancing theorem is applied to the joint score cell
`(propensity, treated prognostic, control prognostic)`.
-/
theorem weightedSampleMeanContrast_eq_twoArmDoubleScoreWeightedMeanContrast
    (sample : Finset Unit)
    (cells : Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (baseWeight : Unit -> Real)
    (targetOutcomeT targetOutcomeC treatedOutcome controlOutcome : Unit -> Real)
    (propensityScore : Unit -> PropensityCell)
    (treatedPrognosticScore : Unit -> TreatedProgCell)
    (controlPrognosticScore : Unit -> ControlProgCell)
    (treatment : Unit -> Prop) [DecidablePred treatment]
    (treatedValue : TreatedProgCell -> Real)
    (controlValue : ControlProgCell -> Real)
    (hcover :
      ∀ unit, unit ∈ sample ->
        pateDoubleScore propensityScore treatedPrognosticScore
          controlPrognosticScore unit ∈ cells)
    (hmass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sample baseWeight
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore) cell ≠ 0)
    (htreated :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (sample.filter treatment) baseWeight
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore) cell ≠ 0)
    (hcontrol :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (sample.filter (fun unit => ¬ treatment unit))
          baseWeight
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore) cell ≠ 0)
    (hscoreMeasTargetT :
      ∀ unit, unit ∈ sample ->
        targetOutcomeT unit = treatedValue (treatedPrognosticScore unit))
    (hscoreMeasTreated :
      ∀ unit, unit ∈ sample.filter treatment ->
        treatedOutcome unit = treatedValue (treatedPrognosticScore unit))
    (hscoreMeasTargetC :
      ∀ unit, unit ∈ sample ->
        targetOutcomeC unit = controlValue (controlPrognosticScore unit))
    (hscoreMeasControl :
      ∀ unit, unit ∈ sample.filter (fun unit => ¬ treatment unit) ->
        controlOutcome unit = controlValue (controlPrognosticScore unit)) :
    weightedSampleMeanContrast sample baseWeight targetOutcomeT targetOutcomeC =
      twoArmWeightedMeanContrast (sample.filter treatment)
        (sample.filter (fun unit => ¬ treatment unit))
        (inverseCellProbabilityWeight baseWeight
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore)
          (scoreCellTreatmentProbability sample baseWeight
            (pateDoubleScore propensityScore treatedPrognosticScore
              controlPrognosticScore) treatment))
        (inverseCellProbabilityWeight baseWeight
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore)
          (scoreCellControlProbability sample baseWeight
            (pateDoubleScore propensityScore treatedPrognosticScore
              controlPrognosticScore) treatment))
        treatedOutcome controlOutcome := by
  exact
    weightedSampleMeanContrast_eq_twoArmCellPropensityWeightedMeanContrast
      sample cells baseWeight targetOutcomeT targetOutcomeC treatedOutcome
      controlOutcome
      (pateDoubleScore propensityScore treatedPrognosticScore
        controlPrognosticScore)
      treatment
      (treatedCellValueOnPATEDoubleScore treatedValue)
      (controlCellValueOnPATEDoubleScore controlValue)
      hcover hmass htreated hcontrol
      (treated_scoreMeasurable_pateDoubleScore propensityScore
        treatedPrognosticScore controlPrognosticScore targetOutcomeT
        treatedValue sample hscoreMeasTargetT)
      (treated_scoreMeasurable_pateDoubleScore propensityScore
        treatedPrognosticScore controlPrognosticScore treatedOutcome
        treatedValue (sample.filter treatment) hscoreMeasTreated)
      (control_scoreMeasurable_pateDoubleScore propensityScore
        treatedPrognosticScore controlPrognosticScore targetOutcomeC
        controlValue sample hscoreMeasTargetC)
      (control_scoreMeasurable_pateDoubleScore propensityScore
        treatedPrognosticScore controlPrognosticScore controlOutcome
        controlValue (sample.filter (fun unit => ¬ treatment unit))
        hscoreMeasControl)

variable {PATTProgCell : Type*} [DecidableEq PATTProgCell]

/-- Joint finite score for PATT: propensity score plus the control prognostic score. -/
def pattDoubleScore
    (propensityScore : Unit -> PropensityCell)
    (controlPrognosticScore : Unit -> PATTProgCell) :
    Unit -> PropensityCell × PATTProgCell :=
  fun unit => (propensityScore unit, controlPrognosticScore unit)

/-- Control prognostic value lifted to the PATT joint score cell. -/
def controlCellValueOnPATTDoubleScore
    (controlValue : PATTProgCell -> Real) :
    PropensityCell × PATTProgCell -> Real :=
  fun cell => controlValue cell.2

omit [DecidableEq PropensityCell] [DecidableEq PATTProgCell] in
theorem control_scoreMeasurable_pattDoubleScore
    (propensityScore : Unit -> PropensityCell)
    (controlPrognosticScore : Unit -> PATTProgCell)
    (outcome : Unit -> Real) (controlValue : PATTProgCell -> Real)
    (sample : Finset Unit)
    (h :
      ∀ unit, unit ∈ sample ->
        outcome unit = controlValue (controlPrognosticScore unit)) :
    ∀ unit, unit ∈ sample ->
      outcome unit =
        controlCellValueOnPATTDoubleScore controlValue
          (pattDoubleScore propensityScore controlPrognosticScore unit) := by
  intro unit hunit
  simpa [controlCellValueOnPATTDoubleScore, pattDoubleScore] using h unit hunit

/--
Finite PATT double-score propensity wrapper.  The existing finite
cell-propensity balancing theorem is applied to the joint score cell
`(propensity, control prognostic)`.
-/
theorem weightedSampleMeanContrast_eq_pattDoubleScoreWeightedMeanContrast
    (sample : Finset Unit)
    (cells : Finset (PropensityCell × PATTProgCell))
    (baseWeight : Unit -> Real)
    (treatedTargetOutcome targetControlOutcome controlOutcome : Unit -> Real)
    (propensityScore : Unit -> PropensityCell)
    (controlPrognosticScore : Unit -> PATTProgCell)
    (treatment : Unit -> Prop) [DecidablePred treatment]
    (controlValue : PATTProgCell -> Real)
    (hcover :
      ∀ unit, unit ∈ sample ->
        pattDoubleScore propensityScore controlPrognosticScore unit ∈ cells)
    (hmass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sample baseWeight
          (pattDoubleScore propensityScore controlPrognosticScore) cell ≠ 0)
    (hcontrol :
      ∀ cell, cell ∈ cells ->
        scoreCellMass (sample.filter (fun unit => ¬ treatment unit))
          baseWeight
          (pattDoubleScore propensityScore controlPrognosticScore) cell ≠ 0)
    (hscoreMeasTargetC :
      ∀ unit, unit ∈ sample ->
        targetControlOutcome unit =
          controlValue (controlPrognosticScore unit))
    (hscoreMeasControl :
      ∀ unit, unit ∈ sample.filter (fun unit => ¬ treatment unit) ->
        controlOutcome unit = controlValue (controlPrognosticScore unit)) :
    weightedSampleMeanContrast sample baseWeight
        treatedTargetOutcome targetControlOutcome =
      pattWeightedMeanContrast sample
        (sample.filter (fun unit => ¬ treatment unit)) baseWeight
        (inverseCellProbabilityWeight baseWeight
          (pattDoubleScore propensityScore controlPrognosticScore)
          (scoreCellControlProbability sample baseWeight
            (pattDoubleScore propensityScore controlPrognosticScore)
            treatment))
        treatedTargetOutcome controlOutcome := by
  exact
    weightedSampleMeanContrast_eq_pattCellPropensityWeightedMeanContrast
      sample cells baseWeight treatedTargetOutcome targetControlOutcome
      controlOutcome
      (pattDoubleScore propensityScore controlPrognosticScore)
      treatment
      (controlCellValueOnPATTDoubleScore controlValue)
      hcover hmass hcontrol
      (control_scoreMeasurable_pattDoubleScore propensityScore
        controlPrognosticScore targetControlOutcome controlValue sample
        hscoreMeasTargetC)
      (control_scoreMeasurable_pattDoubleScore propensityScore
        controlPrognosticScore controlOutcome controlValue
        (sample.filter (fun unit => ¬ treatment unit)) hscoreMeasControl)

end WDSM
end Matching
end StatInference
