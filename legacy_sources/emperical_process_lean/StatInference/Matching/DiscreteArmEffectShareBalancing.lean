import StatInference.Matching.WDSM.DiscreteTreatmentEffectShareDecomposition
import StatInference.Matching.WDSM.DiscretePATEBalancing
import StatInference.Matching.WDSM.DiscretePATTBalancing

/-!
# Discrete arm-effect share balancing

This module connects observed arm contrasts to the target-share treatment
effect decomposition.  Equal normalized score-cell shares let arm-specific
candidate cell means be aggregated under the target score-cell shares.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {TargetUnit TreatedUnit ControlUnit Cell : Type*} [DecidableEq Cell]

/--
If treated and control arm score-cell shares match the target score-cell
shares, then the observed two-arm contrast is the target-share aggregate of
the treated/control candidate cell-mean difference.
-/
theorem twoArmWeightedMeanContrast_eq_candidateCellMeanEffectShareAggregate_of_scoreCellShare_eq
    (targetSample : Finset TargetUnit)
    (treatedSample : Finset TreatedUnit)
    (controlSample : Finset ControlUnit)
    (cells : Finset Cell)
    (targetWeight : TargetUnit -> Real)
    (treatedWeight : TreatedUnit -> Real)
    (controlWeight : ControlUnit -> Real)
    (treatedOutcome : TreatedUnit -> Real)
    (controlOutcome : ControlUnit -> Real)
    (targetScore : TargetUnit -> Cell)
    (treatedScore : TreatedUnit -> Cell)
    (controlScore : ControlUnit -> Cell)
    (treatedCandidate controlCandidate : Cell -> Real)
    (hcoverTreated :
      ∀ unit, unit ∈ treatedSample -> treatedScore unit ∈ cells)
    (hcoverControl :
      ∀ unit, unit ∈ controlSample -> controlScore unit ∈ cells)
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
    twoArmWeightedMeanContrast treatedSample controlSample
        treatedWeight controlWeight treatedOutcome controlOutcome =
      candidateCellMeanEffectShareAggregate targetSample cells targetWeight
        targetScore treatedCandidate controlCandidate := by
  have htreated :
      weightedSampleMean treatedSample treatedWeight treatedOutcome =
        candidateCellMeanShareAggregate treatedSample cells treatedWeight
          treatedScore treatedCandidate :=
    (candidateCellMeanShareAggregate_eq_weightedSampleMean_of_eq
      treatedSample cells treatedWeight treatedOutcome treatedScore
      treatedCandidate hcoverTreated hmassTreated
      htreatedCandidateArm).symm
  have hcontrol :
      weightedSampleMean controlSample controlWeight controlOutcome =
        candidateCellMeanShareAggregate controlSample cells controlWeight
          controlScore controlCandidate :=
    (candidateCellMeanShareAggregate_eq_weightedSampleMean_of_eq
      controlSample cells controlWeight controlOutcome controlScore
      controlCandidate hcoverControl hmassControl hcontrolCandidateArm).symm
  unfold twoArmWeightedMeanContrast
  rw [htreated, hcontrol]
  unfold candidateCellMeanShareAggregate candidateCellMeanEffectShareAggregate
  rw [← Finset.sum_sub_distrib]
  exact Finset.sum_congr rfl
    (fun cell hcell => by
      rw [← hshareTreated cell hcell, ← hshareControl cell hcell]
      ring)

/--
One-sided PATT version: the treated target mean is decomposed on the target
sample, while the control arm mean is transported to target score-cell shares.
-/
theorem pattWeightedMeanContrast_eq_candidateCellMeanEffectShareAggregate_of_control_share_eq
    (targetSample : Finset TargetUnit)
    (controlSample : Finset ControlUnit)
    (cells : Finset Cell)
    (targetWeight : TargetUnit -> Real)
    (controlWeight : ControlUnit -> Real)
    (treatedTargetOutcome : TargetUnit -> Real)
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
    (hcontrolCandidateArm :
      ∀ cell, cell ∈ cells ->
        controlCandidate cell =
          scoreCellMean controlSample controlWeight controlOutcome
            controlScore cell) :
    pattWeightedMeanContrast targetSample controlSample targetWeight
        controlWeight treatedTargetOutcome controlOutcome =
      candidateCellMeanEffectShareAggregate targetSample cells targetWeight
        targetScore treatedCandidate controlCandidate := by
  have htreated :
      weightedSampleMean targetSample targetWeight treatedTargetOutcome =
        candidateCellMeanShareAggregate targetSample cells targetWeight
          targetScore treatedCandidate :=
    (candidateCellMeanShareAggregate_eq_weightedSampleMean_of_eq
      targetSample cells targetWeight treatedTargetOutcome targetScore
      treatedCandidate hcoverTarget hmassTarget
      htreatedCandidateTarget).symm
  have hcontrol :
      weightedSampleMean controlSample controlWeight controlOutcome =
        candidateCellMeanShareAggregate controlSample cells controlWeight
          controlScore controlCandidate :=
    (candidateCellMeanShareAggregate_eq_weightedSampleMean_of_eq
      controlSample cells controlWeight controlOutcome controlScore
      controlCandidate hcoverControl hmassControl hcontrolCandidateArm).symm
  unfold pattWeightedMeanContrast
  rw [htreated, hcontrol]
  unfold candidateCellMeanShareAggregate candidateCellMeanEffectShareAggregate
  rw [← Finset.sum_sub_distrib]
  exact Finset.sum_congr rfl
    (fun cell hcell => by
      rw [← hshareControl cell hcell]
      ring)

end WDSM
end Matching
end StatInference
