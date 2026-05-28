import StatInference.Matching.WDSM.DiscreteRetrospectiveWeightRecovery

/-!
# Finite retrospective survey-weighting recovery for WDSM

This module proves the direct finite "where to weight" algebra.  If selected
treated/control score-cell masses are treatment-specific sampling multiples of
their target masses, then weighting selected treated units by the inverse
treated sampling multiplier and selected control units by the inverse control
sampling multiplier recovers target treated/control cell masses and hence the
target finite cell propensity.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Unit Cell : Type*} [DecidableEq Cell]

/-- Treatment-specific inverse sampling weight inside a selected finite sample. -/
noncomputable def retrospectiveInverseSamplingWeight
    (baseWeight : Unit -> Real) (score : Unit -> Cell)
    (treatment : Unit -> Prop) [DecidablePred treatment]
    (samplingIfTreated samplingIfControl : Cell -> Real)
    (unit : Unit) : Real :=
  if treatment unit then
    baseWeight unit / samplingIfTreated (score unit)
  else
    baseWeight unit / samplingIfControl (score unit)

theorem scoreCellMass_treated_retrospectiveInverseSamplingWeight_eq
    (targetSample selectedSample : Finset Unit)
    (baseWeight : Unit -> Real) (score : Unit -> Cell)
    (treatment : Unit -> Prop) [DecidablePred treatment]
    (samplingIfTreated samplingIfControl : Cell -> Real) (cell : Cell)
    (hsampling : samplingIfTreated cell ≠ 0)
    (hselectedMass :
      scoreCellMass (selectedSample.filter treatment) baseWeight score cell =
        samplingIfTreated cell *
          scoreCellMass (targetSample.filter treatment) baseWeight score
            cell) :
    scoreCellMass (selectedSample.filter treatment)
        (retrospectiveInverseSamplingWeight baseWeight score treatment
          samplingIfTreated samplingIfControl)
        score cell =
      scoreCellMass (targetSample.filter treatment) baseWeight score cell := by
  unfold scoreCellMass retrospectiveInverseSamplingWeight
  calc
    (∑ unit ∈ selectedSample.filter treatment with score unit = cell,
        (if treatment unit then
          baseWeight unit / samplingIfTreated (score unit)
        else
          baseWeight unit / samplingIfControl (score unit))) =
        ∑ unit ∈ selectedSample.filter treatment with score unit = cell,
          baseWeight unit / samplingIfTreated cell := by
          exact Finset.sum_congr rfl
            (fun unit hunit => by
              have htreatment : treatment unit :=
                (Finset.mem_filter.mp (Finset.mem_filter.mp hunit).1).2
              have hscore : score unit = cell :=
                (Finset.mem_filter.mp hunit).2
              simp [htreatment, hscore])
    _ = (∑ unit ∈ selectedSample.filter treatment with score unit = cell,
          baseWeight unit) / samplingIfTreated cell := by
          rw [Finset.sum_div]
    _ = scoreCellMass (selectedSample.filter treatment) baseWeight score cell /
          samplingIfTreated cell := by
          rfl
    _ = scoreCellMass (targetSample.filter treatment) baseWeight score cell := by
          rw [hselectedMass]
          field_simp [hsampling]

theorem scoreCellMass_control_retrospectiveInverseSamplingWeight_eq
    (targetSample selectedSample : Finset Unit)
    (baseWeight : Unit -> Real) (score : Unit -> Cell)
    (treatment : Unit -> Prop) [DecidablePred treatment]
    (samplingIfTreated samplingIfControl : Cell -> Real) (cell : Cell)
    (hsampling : samplingIfControl cell ≠ 0)
    (hselectedMass :
      scoreCellMass (selectedSample.filter (fun unit => ¬ treatment unit))
          baseWeight score cell =
        samplingIfControl cell *
          scoreCellMass
            (targetSample.filter (fun unit => ¬ treatment unit))
            baseWeight score cell) :
    scoreCellMass (selectedSample.filter (fun unit => ¬ treatment unit))
        (retrospectiveInverseSamplingWeight baseWeight score treatment
          samplingIfTreated samplingIfControl)
        score cell =
      scoreCellMass (targetSample.filter (fun unit => ¬ treatment unit))
        baseWeight score cell := by
  unfold scoreCellMass retrospectiveInverseSamplingWeight
  calc
    (∑ unit ∈ selectedSample.filter (fun unit => ¬ treatment unit) with
        score unit = cell,
        (if treatment unit then
          baseWeight unit / samplingIfTreated (score unit)
        else
          baseWeight unit / samplingIfControl (score unit))) =
        ∑ unit ∈ selectedSample.filter (fun unit => ¬ treatment unit) with
          score unit = cell,
          baseWeight unit / samplingIfControl cell := by
          exact Finset.sum_congr rfl
            (fun unit hunit => by
              have htreatment : ¬ treatment unit :=
                (Finset.mem_filter.mp (Finset.mem_filter.mp hunit).1).2
              have hscore : score unit = cell :=
                (Finset.mem_filter.mp hunit).2
              simp [htreatment, hscore])
    _ = (∑ unit ∈ selectedSample.filter (fun unit => ¬ treatment unit) with
          score unit = cell, baseWeight unit) / samplingIfControl cell := by
          rw [Finset.sum_div]
    _ = scoreCellMass
          (selectedSample.filter (fun unit => ¬ treatment unit))
          baseWeight score cell / samplingIfControl cell := by
          rfl
    _ = scoreCellMass
          (targetSample.filter (fun unit => ¬ treatment unit))
          baseWeight score cell := by
          rw [hselectedMass]
          field_simp [hsampling]

theorem scoreCellMass_retrospectiveInverseSamplingWeight_eq
    (targetSample selectedSample : Finset Unit)
    (baseWeight : Unit -> Real) (score : Unit -> Cell)
    (treatment : Unit -> Prop) [DecidablePred treatment]
    (samplingIfTreated samplingIfControl : Cell -> Real) (cell : Cell)
    (hsamplingTreated : samplingIfTreated cell ≠ 0)
    (hsamplingControl : samplingIfControl cell ≠ 0)
    (htreatedMass :
      scoreCellMass (selectedSample.filter treatment) baseWeight score cell =
        samplingIfTreated cell *
          scoreCellMass (targetSample.filter treatment) baseWeight score cell)
    (hcontrolMass :
      scoreCellMass (selectedSample.filter (fun unit => ¬ treatment unit))
          baseWeight score cell =
        samplingIfControl cell *
          scoreCellMass
            (targetSample.filter (fun unit => ¬ treatment unit))
            baseWeight score cell) :
    scoreCellMass selectedSample
        (retrospectiveInverseSamplingWeight baseWeight score treatment
          samplingIfTreated samplingIfControl)
        score cell =
      scoreCellMass targetSample baseWeight score cell := by
  rw [(scoreCellMass_treated_add_control_eq selectedSample
    (retrospectiveInverseSamplingWeight baseWeight score treatment
      samplingIfTreated samplingIfControl) score treatment cell).symm]
  rw [scoreCellMass_treated_retrospectiveInverseSamplingWeight_eq
    targetSample selectedSample baseWeight score treatment samplingIfTreated
    samplingIfControl cell hsamplingTreated htreatedMass]
  rw [scoreCellMass_control_retrospectiveInverseSamplingWeight_eq
    targetSample selectedSample baseWeight score treatment samplingIfTreated
    samplingIfControl cell hsamplingControl hcontrolMass]
  exact scoreCellMass_treated_add_control_eq targetSample baseWeight score
    treatment cell

theorem scoreCellTreatmentProbability_retrospectiveInverseSamplingWeight_eq
    (targetSample selectedSample : Finset Unit)
    (baseWeight : Unit -> Real) (score : Unit -> Cell)
    (treatment : Unit -> Prop) [DecidablePred treatment]
    (samplingIfTreated samplingIfControl : Cell -> Real) (cell : Cell)
    (hsamplingTreated : samplingIfTreated cell ≠ 0)
    (hsamplingControl : samplingIfControl cell ≠ 0)
    (htreatedMass :
      scoreCellMass (selectedSample.filter treatment) baseWeight score cell =
        samplingIfTreated cell *
          scoreCellMass (targetSample.filter treatment) baseWeight score cell)
    (hcontrolMass :
      scoreCellMass (selectedSample.filter (fun unit => ¬ treatment unit))
          baseWeight score cell =
        samplingIfControl cell *
          scoreCellMass
            (targetSample.filter (fun unit => ¬ treatment unit))
            baseWeight score cell) :
    scoreCellTreatmentProbability selectedSample
        (retrospectiveInverseSamplingWeight baseWeight score treatment
          samplingIfTreated samplingIfControl)
        score treatment cell =
      scoreCellTreatmentProbability targetSample baseWeight score treatment
        cell := by
  unfold scoreCellTreatmentProbability
  rw [scoreCellMass_treated_retrospectiveInverseSamplingWeight_eq
    targetSample selectedSample baseWeight score treatment samplingIfTreated
    samplingIfControl cell hsamplingTreated htreatedMass]
  rw [scoreCellMass_retrospectiveInverseSamplingWeight_eq targetSample
    selectedSample baseWeight score treatment samplingIfTreated
    samplingIfControl cell hsamplingTreated hsamplingControl htreatedMass
    hcontrolMass]

end WDSM
end Matching
end StatInference
