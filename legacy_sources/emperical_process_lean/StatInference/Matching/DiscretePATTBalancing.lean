import StatInference.Matching.WDSM.DiscreteBalancingAlgebra

/-!
# Discrete one-sided PATT balancing algebra for WDSM

This module packages finite score-cell balancing into the one-sided PATT
contrast.  The treated target mean is direct; only the counterfactual control
mean is transported from a control-arm sample through score-cell balancing.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {TargetUnit ControlUnit Cell : Type*} [DecidableEq Cell]

/--
One-sided PATT observed contrast: treated-target weighted mean minus
control-arm weighted mean.
-/
noncomputable def pattWeightedMeanContrast
    (targetSample : Finset TargetUnit) (controlSample : Finset ControlUnit)
    (targetWeight : TargetUnit -> Real)
    (controlWeight : ControlUnit -> Real)
    (treatedTargetOutcome : TargetUnit -> Real)
    (controlOutcome : ControlUnit -> Real) : Real :=
  weightedSampleMean targetSample targetWeight treatedTargetOutcome -
    weightedSampleMean controlSample controlWeight controlOutcome

/--
Finite one-sided score-cell balancing theorem for a PATT-style contrast.

If the control-arm sample has the same normalized score-cell shares as the
treated target sample, and if a common candidate control cell mean equals both
the target counterfactual-control cell mean and the control-arm observed cell
mean, then the finite treated-target PATT equals the treated-target direct
mean minus the control-arm weighted mean.
-/
theorem weightedSampleMeanContrast_eq_pattWeightedMeanContrast_of_control_balancing
    (targetSample : Finset TargetUnit)
    (controlSample : Finset ControlUnit)
    (cells : Finset Cell)
    (targetWeight : TargetUnit -> Real)
    (controlWeight : ControlUnit -> Real)
    (treatedTargetOutcome targetControlOutcome : TargetUnit -> Real)
    (controlOutcome : ControlUnit -> Real)
    (targetScore : TargetUnit -> Cell)
    (controlScore : ControlUnit -> Cell)
    (controlCandidate : Cell -> Real)
    (hcoverTarget :
      ∀ unit, unit ∈ targetSample -> targetScore unit ∈ cells)
    (hcoverControl :
      ∀ unit, unit ∈ controlSample -> controlScore unit ∈ cells)
    (hmassTarget :
      ∀ cell, cell ∈ cells ->
        scoreCellMass targetSample targetWeight targetScore cell ≠ 0)
    (hmassControl :
      ∀ cell, cell ∈ cells ->
        scoreCellMass controlSample controlWeight controlScore cell ≠ 0)
    (hshareControl :
      ∀ cell, cell ∈ cells ->
        scoreCellShare targetSample targetWeight targetScore cell =
          scoreCellShare controlSample controlWeight controlScore cell)
    (hcontrolCandidateTarget :
      ∀ cell, cell ∈ cells ->
        controlCandidate cell =
          scoreCellMean targetSample targetWeight targetControlOutcome
            targetScore cell)
    (hcontrolCandidateArm :
      ∀ cell, cell ∈ cells ->
        controlCandidate cell =
          scoreCellMean controlSample controlWeight controlOutcome
            controlScore cell) :
    weightedSampleMeanContrast targetSample targetWeight
        treatedTargetOutcome targetControlOutcome =
      pattWeightedMeanContrast targetSample controlSample targetWeight
        controlWeight treatedTargetOutcome controlOutcome := by
  have hcontrol :
      weightedSampleMean targetSample targetWeight targetControlOutcome =
        weightedSampleMean controlSample controlWeight controlOutcome :=
    weightedSampleMean_eq_of_scoreCellShare_eq_and_candidateCellMean_eq
      targetSample controlSample cells targetWeight controlWeight
      targetControlOutcome controlOutcome targetScore controlScore
      controlCandidate hcoverTarget hcoverControl hmassTarget hmassControl
      hshareControl hcontrolCandidateTarget hcontrolCandidateArm
  unfold weightedSampleMeanContrast pattWeightedMeanContrast
  rw [hcontrol]

end WDSM
end Matching
end StatInference
