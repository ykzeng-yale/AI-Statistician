import StatInference.Matching.WDSM.DiscreteBalancingAlgebra

/-!
# Discrete two-arm PATE balancing algebra for WDSM

This module packages the finite balancing algebra into the two-arm contrast
used by PATE.  It is still deterministic: the theorem assumes the score-cell
share equalities and cellwise candidate-mean equalities that probability-layer
balancing and conditional-expectation arguments must later prove.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {TargetUnit TreatedUnit ControlUnit Cell : Type*} [DecidableEq Cell]

/-- Difference between separate treated-arm and control-arm weighted means. -/
noncomputable def twoArmWeightedMeanContrast
    (treatedSample : Finset TreatedUnit) (controlSample : Finset ControlUnit)
    (treatedWeight : TreatedUnit -> Real)
    (controlWeight : ControlUnit -> Real)
    (treatedOutcome : TreatedUnit -> Real)
    (controlOutcome : ControlUnit -> Real) : Real :=
  weightedSampleMean treatedSample treatedWeight treatedOutcome -
    weightedSampleMean controlSample controlWeight controlOutcome

/--
Finite two-arm score-cell balancing theorem for a PATE-style contrast.

If treated and control arm samples have the same normalized score-cell shares
as the target sample, and if the treated/control candidate cell means equal
both the target potential-outcome cell means and the corresponding arm cell
means, then the target finite PATE equals the treated-minus-control weighted
arm mean contrast.
-/
theorem weightedSampleMeanContrast_eq_twoArmWeightedMeanContrast_of_balancing
    (targetSample : Finset TargetUnit)
    (treatedSample : Finset TreatedUnit)
    (controlSample : Finset ControlUnit)
    (cells : Finset Cell)
    (targetWeight : TargetUnit -> Real)
    (treatedWeight : TreatedUnit -> Real)
    (controlWeight : ControlUnit -> Real)
    (targetOutcomeT targetOutcomeC : TargetUnit -> Real)
    (treatedOutcome : TreatedUnit -> Real)
    (controlOutcome : ControlUnit -> Real)
    (targetScore : TargetUnit -> Cell)
    (treatedScore : TreatedUnit -> Cell)
    (controlScore : ControlUnit -> Cell)
    (treatedCandidate controlCandidate : Cell -> Real)
    (hcoverTarget :
      ∀ unit, unit ∈ targetSample -> targetScore unit ∈ cells)
    (hcoverTreated :
      ∀ unit, unit ∈ treatedSample -> treatedScore unit ∈ cells)
    (hcoverControl :
      ∀ unit, unit ∈ controlSample -> controlScore unit ∈ cells)
    (hmassTarget :
      ∀ cell, cell ∈ cells ->
        scoreCellMass targetSample targetWeight targetScore cell ≠ 0)
    (hmassTreated :
      ∀ cell, cell ∈ cells ->
        scoreCellMass treatedSample treatedWeight treatedScore cell ≠ 0)
    (hmassControl :
      ∀ cell, cell ∈ cells ->
        scoreCellMass controlSample controlWeight controlScore cell ≠ 0)
    (hshareTreated :
      ∀ cell, cell ∈ cells ->
        scoreCellShare targetSample targetWeight targetScore cell =
          scoreCellShare treatedSample treatedWeight treatedScore cell)
    (hshareControl :
      ∀ cell, cell ∈ cells ->
        scoreCellShare targetSample targetWeight targetScore cell =
          scoreCellShare controlSample controlWeight controlScore cell)
    (htreatedCandidateTarget :
      ∀ cell, cell ∈ cells ->
        treatedCandidate cell =
          scoreCellMean targetSample targetWeight targetOutcomeT
            targetScore cell)
    (htreatedCandidateArm :
      ∀ cell, cell ∈ cells ->
        treatedCandidate cell =
          scoreCellMean treatedSample treatedWeight treatedOutcome
            treatedScore cell)
    (hcontrolCandidateTarget :
      ∀ cell, cell ∈ cells ->
        controlCandidate cell =
          scoreCellMean targetSample targetWeight targetOutcomeC
            targetScore cell)
    (hcontrolCandidateArm :
      ∀ cell, cell ∈ cells ->
        controlCandidate cell =
          scoreCellMean controlSample controlWeight controlOutcome
            controlScore cell) :
    weightedSampleMeanContrast targetSample targetWeight
        targetOutcomeT targetOutcomeC =
      twoArmWeightedMeanContrast treatedSample controlSample
        treatedWeight controlWeight treatedOutcome controlOutcome := by
  have htreated :
      weightedSampleMean targetSample targetWeight targetOutcomeT =
        weightedSampleMean treatedSample treatedWeight treatedOutcome :=
    weightedSampleMean_eq_of_scoreCellShare_eq_and_candidateCellMean_eq
      targetSample treatedSample cells targetWeight treatedWeight
      targetOutcomeT treatedOutcome targetScore treatedScore
      treatedCandidate hcoverTarget hcoverTreated hmassTarget hmassTreated
      hshareTreated htreatedCandidateTarget htreatedCandidateArm
  have hcontrol :
      weightedSampleMean targetSample targetWeight targetOutcomeC =
        weightedSampleMean controlSample controlWeight controlOutcome :=
    weightedSampleMean_eq_of_scoreCellShare_eq_and_candidateCellMean_eq
      targetSample controlSample cells targetWeight controlWeight
      targetOutcomeC controlOutcome targetScore controlScore
      controlCandidate hcoverTarget hcoverControl hmassTarget hmassControl
      hshareControl hcontrolCandidateTarget hcontrolCandidateArm
  unfold weightedSampleMeanContrast twoArmWeightedMeanContrast
  rw [htreated, hcontrol]

end WDSM
end Matching
end StatInference
