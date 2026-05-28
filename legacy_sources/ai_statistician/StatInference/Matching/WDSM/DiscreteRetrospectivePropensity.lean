import StatInference.Matching.WDSM.DiscretePropensityPartition
import StatInference.Matching.WDSM.ScoreRelations

/-!
# Finite retrospective propensity algebra for WDSM

This module connects finite binary score-cell propensities to the retrospective
Bayes formula already proved in `ScoreRelations`.  If selected treated/control
cell masses are treatment-specific sampling multiples of target treated/control
cell masses, then the selected finite cell propensity is exactly the
retrospective `selectedPropensity` expression.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Unit Cell : Type*} [DecidableEq Cell]

/--
Selected cell propensity written directly from target treated/control masses
and treatment-specific sampling multipliers.
-/
noncomputable def selectedCellPropensityFromMasses
    (treatedMass controlMass samplingIfTreated samplingIfControl : Real) : Real :=
  samplingIfTreated * treatedMass /
    (samplingIfTreated * treatedMass + samplingIfControl * controlMass)

theorem selectedCellPropensityFromMasses_eq_selectedPropensity
    {treatedMass controlMass totalMass samplingIfTreated samplingIfControl : Real}
    (htotal : totalMass ≠ 0)
    (hpartition : treatedMass + controlMass = totalMass) :
    selectedCellPropensityFromMasses treatedMass controlMass
        samplingIfTreated samplingIfControl =
      selectedPropensity (treatedMass / totalMass)
        samplingIfTreated samplingIfControl := by
  have hcontrol :
      1 - treatedMass / totalMass = controlMass / totalMass := by
    field_simp [htotal]
    linarith
  unfold selectedCellPropensityFromMasses selectedPropensity
  rw [hcontrol]
  field_simp [htotal]

theorem scoreCellTreatmentProbability_selected_eq_selectedPropensity
    (targetSample selectedSample : Finset Unit)
    (baseWeight : Unit -> Real) (score : Unit -> Cell)
    (treatment : Unit -> Prop) [DecidablePred treatment] (cell : Cell)
    (samplingIfTreated samplingIfControl : Real)
    (htotal : scoreCellMass targetSample baseWeight score cell ≠ 0)
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
    scoreCellTreatmentProbability selectedSample baseWeight score treatment cell =
      selectedPropensity
        (scoreCellTreatmentProbability targetSample baseWeight score treatment
          cell)
        samplingIfTreated samplingIfControl := by
  calc
    scoreCellTreatmentProbability selectedSample baseWeight score treatment cell =
        selectedCellPropensityFromMasses
          (scoreCellMass (targetSample.filter treatment) baseWeight score cell)
          (scoreCellMass
            (targetSample.filter (fun unit => ¬ treatment unit))
            baseWeight score cell)
          samplingIfTreated samplingIfControl := by
          unfold scoreCellTreatmentProbability selectedCellPropensityFromMasses
          rw [(scoreCellMass_treated_add_control_eq selectedSample baseWeight
            score treatment cell).symm]
          rw [htreatedMass, hcontrolMass]
    _ = selectedPropensity
        (scoreCellTreatmentProbability targetSample baseWeight score treatment
          cell)
        samplingIfTreated samplingIfControl := by
          unfold scoreCellTreatmentProbability
          exact selectedCellPropensityFromMasses_eq_selectedPropensity
            htotal
            (scoreCellMass_treated_add_control_eq targetSample baseWeight
              score treatment cell)

theorem scoreCellTreatmentProbability_selected_eq_target_of_common_sampling
    (targetSample selectedSample : Finset Unit)
    (baseWeight : Unit -> Real) (score : Unit -> Cell)
    (treatment : Unit -> Prop) [DecidablePred treatment] (cell : Cell)
    (samplingMass : Real)
    (htotal : scoreCellMass targetSample baseWeight score cell ≠ 0)
    (hsampling : samplingMass ≠ 0)
    (htreatedMass :
      scoreCellMass (selectedSample.filter treatment) baseWeight score cell =
        samplingMass *
          scoreCellMass (targetSample.filter treatment) baseWeight score cell)
    (hcontrolMass :
      scoreCellMass (selectedSample.filter (fun unit => ¬ treatment unit))
          baseWeight score cell =
        samplingMass *
          scoreCellMass (targetSample.filter (fun unit => ¬ treatment unit))
            baseWeight score cell) :
    scoreCellTreatmentProbability selectedSample baseWeight score treatment cell =
      scoreCellTreatmentProbability targetSample baseWeight score treatment
        cell := by
  rw [scoreCellTreatmentProbability_selected_eq_selectedPropensity
    targetSample selectedSample baseWeight score treatment cell samplingMass
    samplingMass htotal htreatedMass hcontrolMass]
  exact selectedPropensity_eq_population_of_common_sampling hsampling

end WDSM
end Matching
end StatInference
