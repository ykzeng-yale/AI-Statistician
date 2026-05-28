import StatInference.Matching.WDSM.PopulationSelectionDensityDesign

/-!
# Population selection-density design representations

This module packages `PopulationSelectionDensityDesign` records as the abstract
`PATERepresentation` and `PATTRepresentation` objects used by the Hájek ratio
and score-identification layers.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open scoped MeasureTheory ENNReal

variable {Sample : Type*} [MeasurableSpace Sample]
variable {selectedLaw populationLaw : Measure Sample}

/--
Construct a PATE representation from two arm-specific population
selection-density design records.
-/
noncomputable def pateRepresentationOfSelectionDensityDesign
    (treatedDesign controlDesign :
      PopulationSelectionDensityDesign selectedLaw populationLaw)
    (treatedOutcome controlOutcome : Sample -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1) :
    PATERepresentation :=
  pateRepresentationOfWeightedIntegralRecovery selectedLaw populationLaw
    (fun sample => (treatedDesign.surveyWeight sample : Real))
    (fun sample => (controlDesign.surveyWeight sample : Real))
    treatedOutcome controlOutcome treatedDesign.samplingMass
    controlDesign.samplingMass
    (PopulationSelectionDensityDesign.surveyWeightedIntegral_eq_populationIntegral_div
      treatedDesign
        treatedOutcome)
    (PopulationSelectionDensityDesign.surveyWeightedOne_eq_inv_samplingMass
      treatedDesign hpopulationOne)
    (PopulationSelectionDensityDesign.surveyWeightedIntegral_eq_populationIntegral_div
      controlDesign
        controlOutcome)
    (PopulationSelectionDensityDesign.surveyWeightedOne_eq_inv_samplingMass
      controlDesign hpopulationOne)

/--
The selected-law Hájek PATE represented by selection-density design records
recovers the population-law PATE contrast.
-/
theorem selectedHajekPATE_of_selectionDensityDesign_eq_populationIntegralPATE
    (treatedDesign controlDesign :
      PopulationSelectionDensityDesign selectedLaw populationLaw)
    (treatedOutcome controlOutcome : Sample -> Real)
    (hpopulationOne :
      (∫ _sample, (1 : Real) ∂populationLaw) = 1) :
    PATERepresentation.selectedHajekPATE
        (pateRepresentationOfSelectionDensityDesign treatedDesign
          controlDesign treatedOutcome controlOutcome hpopulationOne) =
      (∫ sample, treatedOutcome sample ∂populationLaw) -
        (∫ sample, controlOutcome sample ∂populationLaw) := by
  simpa [pateRepresentationOfSelectionDensityDesign] using
    selectedWeightedIntegralPATE_eq_populationIntegralPATE selectedLaw
      populationLaw
      (fun sample => (treatedDesign.surveyWeight sample : Real))
      (fun sample => (controlDesign.surveyWeight sample : Real))
      treatedOutcome controlOutcome treatedDesign.samplingMass
      controlDesign.samplingMass
      (PopulationSelectionDensityDesign.surveyWeightedIntegral_eq_populationIntegral_div
        treatedDesign
          treatedOutcome)
      (PopulationSelectionDensityDesign.surveyWeightedOne_eq_inv_samplingMass
        treatedDesign hpopulationOne)
      (PopulationSelectionDensityDesign.surveyWeightedIntegral_eq_populationIntegral_div
        controlDesign
          controlOutcome)
      (PopulationSelectionDensityDesign.surveyWeightedOne_eq_inv_samplingMass
        controlDesign hpopulationOne)
      (ne_of_gt treatedDesign.sampling_pos)
      (ne_of_gt controlDesign.sampling_pos)

/--
Construct a PATT representation from a population selection-density design
record and numerator/denominator targets.
-/
noncomputable def pattRepresentationOfSelectionDensityDesign
    (design : PopulationSelectionDensityDesign selectedLaw populationLaw)
    (treatedEffect treatedMass : Sample -> Real) :
    PATTRepresentation :=
  pattRepresentationOfWeightedIntegralRecovery selectedLaw populationLaw
    (fun sample => (design.surveyWeight sample : Real)) treatedEffect
    treatedMass design.samplingMass
    (PopulationSelectionDensityDesign.surveyWeightedIntegral_eq_populationIntegral_div
      design treatedEffect)
    (PopulationSelectionDensityDesign.surveyWeightedIntegral_eq_populationIntegral_div
      design treatedMass)

/--
The selected-law Hájek PATT represented by a selection-density design record
recovers the population-law PATT ratio.
-/
theorem selectedHajekPATT_of_selectionDensityDesign_eq_populationIntegralPATT
    (design : PopulationSelectionDensityDesign selectedLaw populationLaw)
    (treatedEffect treatedMass : Sample -> Real)
    (hpopulationMass :
      (∫ sample, treatedMass sample ∂populationLaw) ≠ 0) :
    PATTRepresentation.selectedHajekPATT
        (pattRepresentationOfSelectionDensityDesign design treatedEffect
          treatedMass) =
      (∫ sample, treatedEffect sample ∂populationLaw) /
        (∫ sample, treatedMass sample ∂populationLaw) := by
  simpa [pattRepresentationOfSelectionDensityDesign] using
    selectedWeightedIntegralPATT_eq_populationIntegralPATT selectedLaw
      populationLaw (fun sample => (design.surveyWeight sample : Real))
      treatedEffect treatedMass design.samplingMass
      (PopulationSelectionDensityDesign.surveyWeightedIntegral_eq_populationIntegral_div
        design treatedEffect)
      (PopulationSelectionDensityDesign.surveyWeightedIntegral_eq_populationIntegral_div
        design treatedMass)
      (ne_of_gt design.sampling_pos) hpopulationMass

end WDSM
end Matching
end StatInference
