import StatInference.Matching.WDSM.DiscreteArmEffectShareBalancing

/-!
# Discrete effect-share identification bridge

This module packages the target-share decomposition and observed-arm
balancing decomposition into a common finite identification statement.  The
result exposes the shared candidate score-cell effect aggregate, which is the
finite target that later conditional-expectation and balancing arguments must
justify.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {TargetUnit TreatedUnit ControlUnit Cell : Type*} [DecidableEq Cell]

/--
Finite PATE effect-share identification.  Target potential-outcome contrast
and observed treated-minus-control arm contrast both equal the same
target-share aggregate of candidate score-cell effects.
-/
theorem pate_common_effect_share_identification
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
    (hcontrolCandidateTarget :
      ∀ cell, cell ∈ cells ->
        controlCandidate cell =
          scoreCellMean targetSample targetWeight targetOutcomeC
            targetScore cell)
    (htreatedCandidateArm :
      ∀ cell, cell ∈ cells ->
        treatedCandidate cell =
          scoreCellMean treatedSample treatedWeight treatedOutcome
            treatedScore cell)
    (hcontrolCandidateArm :
      ∀ cell, cell ∈ cells ->
        controlCandidate cell =
          scoreCellMean controlSample controlWeight controlOutcome
            controlScore cell) :
    weightedSampleMeanContrast targetSample targetWeight
        targetOutcomeT targetOutcomeC =
        candidateCellMeanEffectShareAggregate targetSample cells targetWeight
          targetScore treatedCandidate controlCandidate ∧
      twoArmWeightedMeanContrast treatedSample controlSample treatedWeight
          controlWeight treatedOutcome controlOutcome =
        candidateCellMeanEffectShareAggregate targetSample cells targetWeight
          targetScore treatedCandidate controlCandidate ∧
      weightedSampleMeanContrast targetSample targetWeight
          targetOutcomeT targetOutcomeC =
        twoArmWeightedMeanContrast treatedSample controlSample
          treatedWeight controlWeight treatedOutcome controlOutcome := by
  have htarget :
      candidateCellMeanEffectShareAggregate targetSample cells targetWeight
          targetScore treatedCandidate controlCandidate =
        weightedSampleMeanContrast targetSample targetWeight
          targetOutcomeT targetOutcomeC :=
    candidateCellMeanEffectShareAggregate_eq_weightedSampleMeanContrast_of_eq
      targetSample cells targetWeight targetOutcomeT targetOutcomeC
      targetScore treatedCandidate controlCandidate hcoverTarget hmassTarget
      htreatedCandidateTarget hcontrolCandidateTarget
  have harm :
      twoArmWeightedMeanContrast treatedSample controlSample treatedWeight
          controlWeight treatedOutcome controlOutcome =
        candidateCellMeanEffectShareAggregate targetSample cells targetWeight
          targetScore treatedCandidate controlCandidate :=
    twoArmWeightedMeanContrast_eq_candidateCellMeanEffectShareAggregate_of_scoreCellShare_eq
      targetSample treatedSample controlSample cells targetWeight
      treatedWeight controlWeight treatedOutcome controlOutcome targetScore
      treatedScore controlScore treatedCandidate controlCandidate
      hcoverTreated hcoverControl hmassTreated hmassControl hshareTreated
      hshareControl htreatedCandidateArm hcontrolCandidateArm
  exact ⟨htarget.symm, harm, htarget.symm.trans harm.symm⟩

/--
Finite PATT effect-share identification.  The treated-target contrast and the
observed one-sided PATT contrast both equal the same target-share aggregate of
candidate score-cell effects.
-/
theorem patt_common_effect_share_identification
    (targetSample : Finset TargetUnit)
    (controlSample : Finset ControlUnit)
    (cells : Finset Cell)
    (targetWeight : TargetUnit -> Real)
    (controlWeight : ControlUnit -> Real)
    (treatedTargetOutcome targetControlOutcome : TargetUnit -> Real)
    (controlOutcome : ControlUnit -> Real)
    (targetScore : TargetUnit -> Cell)
    (controlScore : ControlUnit -> Cell)
    (treatedCandidate controlCandidate : Cell -> Real)
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
    (htreatedCandidateTarget :
      ∀ cell, cell ∈ cells ->
        treatedCandidate cell =
          scoreCellMean targetSample targetWeight treatedTargetOutcome
            targetScore cell)
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
        candidateCellMeanEffectShareAggregate targetSample cells targetWeight
          targetScore treatedCandidate controlCandidate ∧
      pattWeightedMeanContrast targetSample controlSample targetWeight
          controlWeight treatedTargetOutcome controlOutcome =
        candidateCellMeanEffectShareAggregate targetSample cells targetWeight
          targetScore treatedCandidate controlCandidate ∧
      weightedSampleMeanContrast targetSample targetWeight
          treatedTargetOutcome targetControlOutcome =
        pattWeightedMeanContrast targetSample controlSample targetWeight
          controlWeight treatedTargetOutcome controlOutcome := by
  have htarget :
      candidateCellMeanEffectShareAggregate targetSample cells targetWeight
          targetScore treatedCandidate controlCandidate =
        weightedSampleMeanContrast targetSample targetWeight
          treatedTargetOutcome targetControlOutcome :=
    candidateCellMeanEffectShareAggregate_eq_weightedSampleMeanContrast_of_eq
      targetSample cells targetWeight treatedTargetOutcome
      targetControlOutcome targetScore treatedCandidate controlCandidate
      hcoverTarget hmassTarget htreatedCandidateTarget
      hcontrolCandidateTarget
  have harm :
      pattWeightedMeanContrast targetSample controlSample targetWeight
          controlWeight treatedTargetOutcome controlOutcome =
        candidateCellMeanEffectShareAggregate targetSample cells targetWeight
          targetScore treatedCandidate controlCandidate :=
    pattWeightedMeanContrast_eq_candidateCellMeanEffectShareAggregate_of_control_share_eq
      targetSample controlSample cells targetWeight controlWeight
      treatedTargetOutcome controlOutcome targetScore controlScore
      treatedCandidate controlCandidate hcoverTarget hcoverControl
      hmassTarget hmassControl hshareControl htreatedCandidateTarget
      hcontrolCandidateArm
  exact ⟨htarget.symm, harm, htarget.symm.trans harm.symm⟩

end WDSM
end Matching
end StatInference
