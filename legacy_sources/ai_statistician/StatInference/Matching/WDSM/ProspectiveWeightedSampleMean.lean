import StatInference.Matching.WDSM.ProspectiveSpecialization
import StatInference.Matching.WDSM.DiscretePATEBalancing
import StatInference.Matching.WDSM.DiscretePATTBalancing

/-!
# Prospective/common-weight sample mean specializations for WDSM

This module connects the finite WDSM `weightedSampleMean` API to the
common-weight Hájek algebra proved in `ProspectiveSpecialization`.  It is the
finite deterministic reduction used when a prospective design has a common
survey weight, so the WDSM weighted mean is an ordinary finite sample average.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit TreatedUnit ControlUnit : Type*}

/-- The WDSM weighted numerator is the aggregate Hájek weighted sum. -/
theorem weightedSampleSum_eq_weightedSum
    (sample : Finset Unit) (weight outcome : Unit -> Real) :
    weightedSampleSum sample weight outcome =
      weightedSum sample weight outcome := by
  rfl

/-- The WDSM weighted total is the aggregate Hájek denominator. -/
theorem weightedSampleTotal_eq_weightedDenominator
    (sample : Finset Unit) (weight : Unit -> Real) :
    weightedSampleTotal sample weight =
      weightedDenominator sample weight := by
  rfl

/-- The WDSM weighted sample mean is the aggregate Hájek mean. -/
theorem weightedSampleMean_eq_hajekMean
    (sample : Finset Unit) (weight outcome : Unit -> Real) :
    weightedSampleMean sample weight outcome =
      hajekMean sample weight outcome := by
  rfl

/--
With a nonzero common survey weight, the WDSM weighted sample mean equals the
ordinary finite-sum ratio with denominator `sum 1`.
-/
theorem weightedSampleMean_constant_weight_eq_unweighted_ratio
    (sample : Finset Unit) (outcome : Unit -> Real) (commonWeight : Real)
    (hweight : commonWeight ≠ 0)
    (hmass : (∑ _unit ∈ sample, (1 : Real)) ≠ 0) :
    weightedSampleMean sample (fun _unit => commonWeight) outcome =
      (∑ unit ∈ sample, outcome unit) /
        (∑ _unit ∈ sample, (1 : Real)) := by
  rw [weightedSampleMean_eq_hajekMean]
  exact hajekMean_constant_weight_eq_unweighted_ratio
    sample outcome commonWeight hweight hmass

/--
With a nonzero common survey weight, the WDSM weighted sample mean is the
ordinary finite sample average with denominator `sample.card`.
-/
theorem weightedSampleMean_constant_weight_eq_card_average
    (sample : Finset Unit) (outcome : Unit -> Real) (commonWeight : Real)
    (hweight : commonWeight ≠ 0)
    (hcard : (sample.card : Real) ≠ 0) :
    weightedSampleMean sample (fun _unit => commonWeight) outcome =
      (∑ unit ∈ sample, outcome unit) / (sample.card : Real) := by
  rw [weightedSampleMean_eq_hajekMean]
  exact hajekMean_constant_weight_eq_card_average
    sample outcome commonWeight hweight hcard

/--
With a nonzero common survey weight and a nonempty sample, the WDSM weighted
sample mean is the ordinary finite sample average.
-/
theorem weightedSampleMean_constant_weight_eq_card_average_of_nonempty
    (sample : Finset Unit) (outcome : Unit -> Real) (commonWeight : Real)
    (hweight : commonWeight ≠ 0)
    (hnonempty : sample.Nonempty) :
    weightedSampleMean sample (fun _unit => commonWeight) outcome =
      (∑ unit ∈ sample, outcome unit) / (sample.card : Real) := by
  rw [weightedSampleMean_eq_hajekMean]
  exact hajekMean_constant_weight_eq_card_average_of_nonempty
    sample outcome commonWeight hweight hnonempty

/--
Positive common weights are enough for the nonempty-sample WDSM sample-average
specialization.
-/
theorem weightedSampleMean_constant_weight_eq_card_average_of_pos_nonempty
    (sample : Finset Unit) (outcome : Unit -> Real) (commonWeight : Real)
    (hweight_pos : 0 < commonWeight)
    (hnonempty : sample.Nonempty) :
    weightedSampleMean sample (fun _unit => commonWeight) outcome =
      (∑ unit ∈ sample, outcome unit) / (sample.card : Real) :=
  weightedSampleMean_constant_weight_eq_card_average_of_nonempty
    sample outcome commonWeight hweight_pos.ne' hnonempty

/--
With a nonzero common survey weight and nonempty arm samples, a two-arm WDSM
contrast is the corresponding contrast of ordinary finite sample averages.
-/
theorem twoArmWeightedMeanContrast_constant_weight_eq_card_average_sub_of_nonempty
    (treatedSample : Finset TreatedUnit) (controlSample : Finset ControlUnit)
    (treatedOutcome : TreatedUnit -> Real) (controlOutcome : ControlUnit -> Real)
    (commonTreatedWeight commonControlWeight : Real)
    (htreated_weight : commonTreatedWeight ≠ 0)
    (hcontrol_weight : commonControlWeight ≠ 0)
    (htreated_nonempty : treatedSample.Nonempty)
    (hcontrol_nonempty : controlSample.Nonempty) :
    twoArmWeightedMeanContrast treatedSample controlSample
        (fun _unit => commonTreatedWeight) (fun _unit => commonControlWeight)
        treatedOutcome controlOutcome =
      (∑ unit ∈ treatedSample, treatedOutcome unit) /
          (treatedSample.card : Real) -
        (∑ unit ∈ controlSample, controlOutcome unit) /
          (controlSample.card : Real) := by
  unfold twoArmWeightedMeanContrast
  rw [weightedSampleMean_constant_weight_eq_card_average_of_nonempty
    treatedSample treatedOutcome commonTreatedWeight htreated_weight
    htreated_nonempty]
  rw [weightedSampleMean_constant_weight_eq_card_average_of_nonempty
    controlSample controlOutcome commonControlWeight hcontrol_weight
    hcontrol_nonempty]

/--
Positive common arm weights are enough for the nonempty two-arm WDSM ordinary
finite average contrast specialization.
-/
theorem twoArmWeightedMeanContrast_constant_weight_eq_card_average_sub_of_pos_nonempty
    (treatedSample : Finset TreatedUnit) (controlSample : Finset ControlUnit)
    (treatedOutcome : TreatedUnit -> Real) (controlOutcome : ControlUnit -> Real)
    (commonTreatedWeight commonControlWeight : Real)
    (htreated_weight_pos : 0 < commonTreatedWeight)
    (hcontrol_weight_pos : 0 < commonControlWeight)
    (htreated_nonempty : treatedSample.Nonempty)
    (hcontrol_nonempty : controlSample.Nonempty) :
    twoArmWeightedMeanContrast treatedSample controlSample
        (fun _unit => commonTreatedWeight) (fun _unit => commonControlWeight)
        treatedOutcome controlOutcome =
      (∑ unit ∈ treatedSample, treatedOutcome unit) /
          (treatedSample.card : Real) -
        (∑ unit ∈ controlSample, controlOutcome unit) /
          (controlSample.card : Real) :=
  twoArmWeightedMeanContrast_constant_weight_eq_card_average_sub_of_nonempty
    treatedSample controlSample treatedOutcome controlOutcome
    commonTreatedWeight commonControlWeight htreated_weight_pos.ne'
    hcontrol_weight_pos.ne' htreated_nonempty hcontrol_nonempty

/--
With a nonzero common survey weight and a nonempty sample, a WDSM
within-sample mean contrast is the ordinary finite average of the pointwise
difference.
-/
theorem weightedSampleMeanContrast_constant_weight_eq_card_average_difference_of_nonempty
    (sample : Finset Unit) (outcomeA outcomeB : Unit -> Real)
    (commonWeight : Real)
    (hweight : commonWeight ≠ 0)
    (hnonempty : sample.Nonempty) :
    weightedSampleMeanContrast sample (fun _unit => commonWeight)
        outcomeA outcomeB =
      (∑ unit ∈ sample, (outcomeA unit - outcomeB unit)) /
        (sample.card : Real) := by
  unfold weightedSampleMeanContrast
  rw [weightedSampleMean_eq_hajekMean]
  rw [weightedSampleMean_eq_hajekMean]
  exact hajekMean_constant_weight_sub_eq_card_average_difference_of_nonempty
    sample outcomeA outcomeB commonWeight hweight hnonempty

/--
Positive common survey weights are enough for the nonempty within-sample WDSM
ordinary finite average contrast specialization.
-/
theorem weightedSampleMeanContrast_constant_weight_eq_card_average_difference_of_pos_nonempty
    (sample : Finset Unit) (outcomeA outcomeB : Unit -> Real)
    (commonWeight : Real)
    (hweight_pos : 0 < commonWeight)
    (hnonempty : sample.Nonempty) :
    weightedSampleMeanContrast sample (fun _unit => commonWeight)
        outcomeA outcomeB =
      (∑ unit ∈ sample, (outcomeA unit - outcomeB unit)) /
        (sample.card : Real) :=
  weightedSampleMeanContrast_constant_weight_eq_card_average_difference_of_nonempty
    sample outcomeA outcomeB commonWeight hweight_pos.ne' hnonempty

/--
With nonzero common survey weights and nonempty samples, the PATT WDSM
contrast is the treated target ordinary average minus the control ordinary
average.
-/
theorem pattWeightedMeanContrast_constant_weight_eq_card_average_sub_of_nonempty
    (targetSample : Finset Unit) (controlSample : Finset ControlUnit)
    (treatedTargetOutcome : Unit -> Real) (controlOutcome : ControlUnit -> Real)
    (commonTargetWeight commonControlWeight : Real)
    (htarget_weight : commonTargetWeight ≠ 0)
    (hcontrol_weight : commonControlWeight ≠ 0)
    (htarget_nonempty : targetSample.Nonempty)
    (hcontrol_nonempty : controlSample.Nonempty) :
    pattWeightedMeanContrast targetSample controlSample
        (fun _unit => commonTargetWeight) (fun _unit => commonControlWeight)
        treatedTargetOutcome controlOutcome =
      (∑ unit ∈ targetSample, treatedTargetOutcome unit) /
          (targetSample.card : Real) -
        (∑ unit ∈ controlSample, controlOutcome unit) /
          (controlSample.card : Real) := by
  unfold pattWeightedMeanContrast
  rw [weightedSampleMean_constant_weight_eq_card_average_of_nonempty
    targetSample treatedTargetOutcome commonTargetWeight htarget_weight
    htarget_nonempty]
  rw [weightedSampleMean_constant_weight_eq_card_average_of_nonempty
    controlSample controlOutcome commonControlWeight hcontrol_weight
    hcontrol_nonempty]

/--
Positive common weights are enough for the nonempty PATT WDSM ordinary finite
average contrast specialization.
-/
theorem pattWeightedMeanContrast_constant_weight_eq_card_average_sub_of_pos_nonempty
    (targetSample : Finset Unit) (controlSample : Finset ControlUnit)
    (treatedTargetOutcome : Unit -> Real) (controlOutcome : ControlUnit -> Real)
    (commonTargetWeight commonControlWeight : Real)
    (htarget_weight_pos : 0 < commonTargetWeight)
    (hcontrol_weight_pos : 0 < commonControlWeight)
    (htarget_nonempty : targetSample.Nonempty)
    (hcontrol_nonempty : controlSample.Nonempty) :
    pattWeightedMeanContrast targetSample controlSample
        (fun _unit => commonTargetWeight) (fun _unit => commonControlWeight)
        treatedTargetOutcome controlOutcome =
      (∑ unit ∈ targetSample, treatedTargetOutcome unit) /
          (targetSample.card : Real) -
        (∑ unit ∈ controlSample, controlOutcome unit) /
          (controlSample.card : Real) :=
  pattWeightedMeanContrast_constant_weight_eq_card_average_sub_of_nonempty
    targetSample controlSample treatedTargetOutcome controlOutcome
    commonTargetWeight commonControlWeight htarget_weight_pos.ne'
    hcontrol_weight_pos.ne' htarget_nonempty hcontrol_nonempty

end WDSM
end Matching
end StatInference
