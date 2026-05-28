import StatInference.Matching.WDSM.ScoreRelations
import StatInference.Matching.WDSM.HajekWeights

/-!
# Prospective/common-weight specializations for WDSM

Prospective sampling is the common-inclusion-weight specialization of the
retrospective framework.  This module proves finite real-algebra reductions
used when treatment-specific weights collapse to a single common weight.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit : Type*}

theorem populationPropensityFromSelected_common_weight_eq
    (commonWeight selected : Real) (hweight : commonWeight ≠ 0) :
    populationPropensityFromSelected commonWeight commonWeight selected =
      selected := by
  unfold populationPropensityFromSelected
  field_simp [hweight]
  ring

/--
Under common sampling and common survey weights, the selected-sample propensity
recovers the population propensity directly.
-/
theorem populationPropensityFromSelected_common_weight_common_sampling_eq
    {populationPropensity samplingProbability commonWeight : Real}
    (hsampling : samplingProbability ≠ 0)
    (hweight : commonWeight ≠ 0) :
    populationPropensityFromSelected commonWeight commonWeight
        (selectedPropensity populationPropensity samplingProbability
          samplingProbability) =
      populationPropensity := by
  rw [populationPropensityFromSelected_common_weight_eq commonWeight _ hweight,
    selectedPropensity_eq_population_of_common_sampling hsampling]

/--
Under common sampling, using the common inverse sampling weight also recovers
the population propensity directly.
-/
theorem populationPropensityFromSelected_common_inverse_sampling_eq
    {populationPropensity samplingProbability : Real}
    (hsampling : samplingProbability ≠ 0) :
    populationPropensityFromSelected (1 / samplingProbability)
        (1 / samplingProbability)
        (selectedPropensity populationPropensity samplingProbability
          samplingProbability) =
      populationPropensity :=
  populationPropensityFromSelected_common_weight_common_sampling_eq hsampling
    (one_div_ne_zero hsampling)

theorem weight_ratio_eq_one_of_common_weight
    (commonWeight : Real) (hweight : commonWeight ≠ 0) :
    commonWeight / commonWeight = 1 := by
  exact div_self hweight

/-- A constant survey weight factors out of a finite weighted sum. -/
theorem weightedSum_constant_weight_eq
    (sample : Finset Unit) (value : Unit -> Real) (commonWeight : Real) :
    weightedSum sample (fun _unit => commonWeight) value =
      commonWeight * (∑ unit ∈ sample, value unit) := by
  unfold weightedSum
  rw [← Finset.mul_sum]

/-- A constant survey weight factors out of a finite Hájek denominator. -/
theorem weightedDenominator_constant_weight_eq
    (sample : Finset Unit) (commonWeight : Real) :
    weightedDenominator sample (fun _unit => commonWeight) =
      commonWeight * (∑ _unit ∈ sample, (1 : Real)) := by
  unfold weightedDenominator
  calc
    (∑ unit ∈ sample, commonWeight) =
        (∑ unit ∈ sample, commonWeight * (1 : Real)) := by
          exact Finset.sum_congr rfl
            (fun _unit _hunit => by ring)
    _ = commonWeight * (∑ _unit ∈ sample, (1 : Real)) := by
          rw [← Finset.mul_sum]

/-- The finite unit mass is the sample cardinality, coerced to `Real`. -/
theorem finiteUnitMass_eq_card (sample : Finset Unit) :
    (∑ _unit ∈ sample, (1 : Real)) = (sample.card : Real) := by
  simp

/-- A nonempty finite sample has positive finite unit mass. -/
theorem finiteUnitMass_pos_of_nonempty
    (sample : Finset Unit) (hnonempty : sample.Nonempty) :
    0 < (∑ _unit ∈ sample, (1 : Real)) := by
  rw [finiteUnitMass_eq_card]
  exact_mod_cast (Finset.card_pos.mpr hnonempty)

/-- A nonempty finite sample has nonzero finite unit mass. -/
theorem finiteUnitMass_ne_zero_of_nonempty
    (sample : Finset Unit) (hnonempty : sample.Nonempty) :
    (∑ _unit ∈ sample, (1 : Real)) ≠ 0 :=
  (finiteUnitMass_pos_of_nonempty sample hnonempty).ne'

/-- A nonempty finite sample has nonzero cardinality after coercion to `Real`. -/
theorem sampleCard_ne_zero_of_nonempty
    (sample : Finset Unit) (hnonempty : sample.Nonempty) :
    (sample.card : Real) ≠ 0 := by
  simpa [finiteUnitMass_eq_card] using
    finiteUnitMass_ne_zero_of_nonempty sample hnonempty

/-- A constant-weight Hájek denominator is the common weight times sample size. -/
theorem weightedDenominator_constant_weight_eq_card
    (sample : Finset Unit) (commonWeight : Real) :
    weightedDenominator sample (fun _unit => commonWeight) =
      commonWeight * (sample.card : Real) := by
  rw [weightedDenominator_constant_weight_eq, finiteUnitMass_eq_card]

/--
A positive common survey weight and nonempty sample give a positive Hájek
denominator.
-/
theorem weightedDenominator_constant_weight_pos_of_pos_of_nonempty
    (sample : Finset Unit) (commonWeight : Real)
    (hweight_pos : 0 < commonWeight)
    (hnonempty : sample.Nonempty) :
    0 < weightedDenominator sample (fun _unit => commonWeight) := by
  rw [weightedDenominator_constant_weight_eq_card]
  have hcard_pos : 0 < (sample.card : Real) := by
    exact_mod_cast (Finset.card_pos.mpr hnonempty)
  exact mul_pos hweight_pos hcard_pos

/--
A positive common survey weight and nonempty sample give a nonzero Hájek
denominator.
-/
theorem weightedDenominator_constant_weight_ne_zero_of_pos_of_nonempty
    (sample : Finset Unit) (commonWeight : Real)
    (hweight_pos : 0 < commonWeight)
    (hnonempty : sample.Nonempty) :
    weightedDenominator sample (fun _unit => commonWeight) ≠ 0 :=
  (weightedDenominator_constant_weight_pos_of_pos_of_nonempty sample
    commonWeight hweight_pos hnonempty).ne'

/--
A nonzero common survey weight and nonempty sample give a nonzero Hájek
denominator.
-/
theorem weightedDenominator_constant_weight_ne_zero_of_ne_zero_of_nonempty
    (sample : Finset Unit) (commonWeight : Real)
    (hweight : commonWeight ≠ 0)
    (hnonempty : sample.Nonempty) :
    weightedDenominator sample (fun _unit => commonWeight) ≠ 0 := by
  rw [weightedDenominator_constant_weight_eq_card]
  exact mul_ne_zero hweight (sampleCard_ne_zero_of_nonempty sample hnonempty)

/--
For a nonzero common survey weight and a nonempty sample, the normalized
survey weights sum to one.
-/
theorem sum_normalizedSurveyWeight_constant_weight_eq_one_of_nonempty
    (sample : Finset Unit) (commonWeight : Real)
    (hweight : commonWeight ≠ 0)
    (hnonempty : sample.Nonempty) :
    (∑ unit ∈ sample,
      normalizedSurveyWeight sample (fun _unit => commonWeight) unit) = 1 :=
  sum_normalizedSurveyWeight_eq_one sample (fun _unit => commonWeight)
    (weightedDenominator_constant_weight_ne_zero_of_ne_zero_of_nonempty
      sample commonWeight hweight hnonempty)

/--
Positive common survey weights and a nonempty sample are enough for the
normalized survey weights to sum to one.
-/
theorem sum_normalizedSurveyWeight_constant_weight_eq_one_of_pos_nonempty
    (sample : Finset Unit) (commonWeight : Real)
    (hweight_pos : 0 < commonWeight)
    (hnonempty : sample.Nonempty) :
    (∑ unit ∈ sample,
      normalizedSurveyWeight sample (fun _unit => commonWeight) unit) = 1 :=
  sum_normalizedSurveyWeight_constant_weight_eq_one_of_nonempty sample
    commonWeight hweight_pos.ne' hnonempty

/--
With a nonzero common survey weight and nonzero finite sample mass, every
normalized survey weight reduces to the inverse of the finite unit mass.
-/
theorem normalizedSurveyWeight_constant_weight_eq_inv_mass
    (sample : Finset Unit) (commonWeight : Real)
    (hweight : commonWeight ≠ 0)
    (hmass : (∑ _unit ∈ sample, (1 : Real)) ≠ 0)
    (unit : Unit) :
    normalizedSurveyWeight sample (fun _unit => commonWeight) unit =
      (1 : Real) / (∑ _unit ∈ sample, (1 : Real)) := by
  unfold normalizedSurveyWeight
  rw [weightedDenominator_constant_weight_eq]
  field_simp [hweight, hmass]

/--
With a nonzero common survey weight and nonzero sample cardinality, every
normalized survey weight reduces to the inverse sample size.
-/
theorem normalizedSurveyWeight_constant_weight_eq_inv_card
    (sample : Finset Unit) (commonWeight : Real)
    (hweight : commonWeight ≠ 0)
    (hcard : (sample.card : Real) ≠ 0)
    (unit : Unit) :
    normalizedSurveyWeight sample (fun _unit => commonWeight) unit =
      (1 : Real) / (sample.card : Real) := by
  rw [normalizedSurveyWeight_constant_weight_eq_inv_mass
    sample commonWeight hweight _ unit]
  · rw [finiteUnitMass_eq_card]
  · simpa [finiteUnitMass_eq_card] using hcard

/--
With a nonzero common survey weight and a nonempty sample, every normalized
survey weight reduces to the inverse sample size.
-/
theorem normalizedSurveyWeight_constant_weight_eq_inv_card_of_nonempty
    (sample : Finset Unit) (commonWeight : Real)
    (hweight : commonWeight ≠ 0)
    (hnonempty : sample.Nonempty)
    (unit : Unit) :
    normalizedSurveyWeight sample (fun _unit => commonWeight) unit =
      (1 : Real) / (sample.card : Real) :=
  normalizedSurveyWeight_constant_weight_eq_inv_card sample commonWeight
    hweight (sampleCard_ne_zero_of_nonempty sample hnonempty) unit

/--
With a positive common survey weight and a nonempty sample, every normalized
survey weight is positive.
-/
theorem normalizedSurveyWeight_constant_weight_pos_of_pos_of_nonempty
    (sample : Finset Unit) (commonWeight : Real)
    (hweight_pos : 0 < commonWeight)
    (hnonempty : sample.Nonempty)
    (unit : Unit) :
    0 < normalizedSurveyWeight sample (fun _unit => commonWeight) unit := by
  rw [normalizedSurveyWeight_constant_weight_eq_inv_card_of_nonempty
    sample commonWeight hweight_pos.ne' hnonempty unit]
  have hcard_pos : 0 < (sample.card : Real) := by
    exact_mod_cast (Finset.card_pos.mpr hnonempty)
  exact div_pos zero_lt_one hcard_pos

/--
With a nonzero common survey weight, the Hajek mean equals the ratio formed by
the unweighted finite sum and the finite unit mass `sum 1`.
-/
theorem hajekMean_constant_weight_eq_unweighted_ratio
    (sample : Finset Unit) (value : Unit -> Real) (commonWeight : Real)
    (hweight : commonWeight ≠ 0)
    (hmass : (∑ _unit ∈ sample, (1 : Real)) ≠ 0) :
    hajekMean sample (fun _unit => commonWeight) value =
      (∑ unit ∈ sample, value unit) /
        (∑ _unit ∈ sample, (1 : Real)) := by
  unfold hajekMean
  rw [weightedSum_constant_weight_eq,
    weightedDenominator_constant_weight_eq]
  field_simp [hweight, hmass]

/--
With a nonzero common survey weight, the Hájek mean is the ordinary finite
sample average with denominator `sample.card`.
-/
theorem hajekMean_constant_weight_eq_card_average
    (sample : Finset Unit) (value : Unit -> Real) (commonWeight : Real)
    (hweight : commonWeight ≠ 0)
    (hcard : (sample.card : Real) ≠ 0) :
    hajekMean sample (fun _unit => commonWeight) value =
      (∑ unit ∈ sample, value unit) / (sample.card : Real) := by
  rw [hajekMean_constant_weight_eq_unweighted_ratio
    sample value commonWeight hweight _]
  · rw [finiteUnitMass_eq_card]
  · simpa [finiteUnitMass_eq_card] using hcard

/--
With a nonzero common survey weight and a nonempty sample, the Hájek mean is
the ordinary finite sample average with denominator `sample.card`.
-/
theorem hajekMean_constant_weight_eq_card_average_of_nonempty
    (sample : Finset Unit) (value : Unit -> Real) (commonWeight : Real)
    (hweight : commonWeight ≠ 0)
    (hnonempty : sample.Nonempty) :
    hajekMean sample (fun _unit => commonWeight) value =
      (∑ unit ∈ sample, value unit) / (sample.card : Real) :=
  hajekMean_constant_weight_eq_card_average sample value commonWeight hweight
    (sampleCard_ne_zero_of_nonempty sample hnonempty)

/--
Positive common weights are enough for the nonempty-sample ordinary finite
sample average specialization.
-/
theorem hajekMean_constant_weight_eq_card_average_of_pos_nonempty
    (sample : Finset Unit) (value : Unit -> Real) (commonWeight : Real)
    (hweight_pos : 0 < commonWeight)
    (hnonempty : sample.Nonempty) :
    hajekMean sample (fun _unit => commonWeight) value =
      (∑ unit ∈ sample, value unit) / (sample.card : Real) :=
  hajekMean_constant_weight_eq_card_average_of_nonempty sample value
    commonWeight hweight_pos.ne' hnonempty

/--
With a nonzero common survey weight, the normalized-weight average is the
ordinary finite-sum ratio with denominator `sum 1`.
-/
theorem sum_normalizedSurveyWeight_constant_weight_mul_eq_unweighted_ratio
    (sample : Finset Unit) (value : Unit -> Real) (commonWeight : Real)
    (hweight : commonWeight ≠ 0)
    (hmass : (∑ _unit ∈ sample, (1 : Real)) ≠ 0) :
    (∑ unit ∈ sample,
      normalizedSurveyWeight sample (fun _unit => commonWeight) unit *
        value unit) =
      (∑ unit ∈ sample, value unit) /
        (∑ _unit ∈ sample, (1 : Real)) := by
  rw [← hajekMean_eq_sum_normalizedSurveyWeight_mul]
  exact hajekMean_constant_weight_eq_unweighted_ratio
    sample value commonWeight hweight hmass

/--
With a nonzero common survey weight, the normalized-weight average is the
ordinary finite sample average with denominator `sample.card`.
-/
theorem sum_normalizedSurveyWeight_constant_weight_mul_eq_card_average
    (sample : Finset Unit) (value : Unit -> Real) (commonWeight : Real)
    (hweight : commonWeight ≠ 0)
    (hcard : (sample.card : Real) ≠ 0) :
    (∑ unit ∈ sample,
      normalizedSurveyWeight sample (fun _unit => commonWeight) unit *
        value unit) =
      (∑ unit ∈ sample, value unit) / (sample.card : Real) := by
  rw [← hajekMean_eq_sum_normalizedSurveyWeight_mul]
  exact hajekMean_constant_weight_eq_card_average
    sample value commonWeight hweight hcard

/--
With a nonzero common survey weight and a nonempty sample, the normalized-weight
average is the ordinary finite sample average.
-/
theorem sum_normalizedSurveyWeight_constant_weight_mul_eq_card_average_of_nonempty
    (sample : Finset Unit) (value : Unit -> Real) (commonWeight : Real)
    (hweight : commonWeight ≠ 0)
    (hnonempty : sample.Nonempty) :
    (∑ unit ∈ sample,
      normalizedSurveyWeight sample (fun _unit => commonWeight) unit *
        value unit) =
      (∑ unit ∈ sample, value unit) / (sample.card : Real) := by
  exact sum_normalizedSurveyWeight_constant_weight_mul_eq_card_average
    sample value commonWeight hweight
    (sampleCard_ne_zero_of_nonempty sample hnonempty)

/--
Positive common survey weights are enough for the nonempty-sample
normalized-weight average specialization.
-/
theorem sum_normalizedSurveyWeight_constant_weight_mul_eq_card_average_of_pos_nonempty
    (sample : Finset Unit) (value : Unit -> Real) (commonWeight : Real)
    (hweight_pos : 0 < commonWeight)
    (hnonempty : sample.Nonempty) :
    (∑ unit ∈ sample,
      normalizedSurveyWeight sample (fun _unit => commonWeight) unit *
        value unit) =
      (∑ unit ∈ sample, value unit) / (sample.card : Real) :=
  sum_normalizedSurveyWeight_constant_weight_mul_eq_card_average_of_nonempty
    sample value commonWeight hweight_pos.ne' hnonempty

/--
With a nonzero common survey weight and nonempty samples, a two-sample Hájek
contrast is the corresponding contrast of ordinary finite sample averages.
-/
theorem hajekMean_constant_weight_sub_eq_card_average_sub_of_nonempty
    (leftSample rightSample : Finset Unit)
    (leftValue rightValue : Unit -> Real) (commonWeight : Real)
    (hweight : commonWeight ≠ 0)
    (hleft_nonempty : leftSample.Nonempty)
    (hright_nonempty : rightSample.Nonempty) :
    hajekMean leftSample (fun _unit => commonWeight) leftValue -
        hajekMean rightSample (fun _unit => commonWeight) rightValue =
      (∑ unit ∈ leftSample, leftValue unit) / (leftSample.card : Real) -
        (∑ unit ∈ rightSample, rightValue unit) /
          (rightSample.card : Real) := by
  rw [hajekMean_constant_weight_eq_card_average_of_nonempty
    leftSample leftValue commonWeight hweight hleft_nonempty]
  rw [hajekMean_constant_weight_eq_card_average_of_nonempty
    rightSample rightValue commonWeight hweight hright_nonempty]

/--
Positive common survey weights are enough for the nonempty two-sample Hájek
contrast specialization.
-/
theorem hajekMean_constant_weight_sub_eq_card_average_sub_of_pos_nonempty
    (leftSample rightSample : Finset Unit)
    (leftValue rightValue : Unit -> Real) (commonWeight : Real)
    (hweight_pos : 0 < commonWeight)
    (hleft_nonempty : leftSample.Nonempty)
    (hright_nonempty : rightSample.Nonempty) :
    hajekMean leftSample (fun _unit => commonWeight) leftValue -
        hajekMean rightSample (fun _unit => commonWeight) rightValue =
      (∑ unit ∈ leftSample, leftValue unit) / (leftSample.card : Real) -
        (∑ unit ∈ rightSample, rightValue unit) /
          (rightSample.card : Real) :=
  hajekMean_constant_weight_sub_eq_card_average_sub_of_nonempty
    leftSample rightSample leftValue rightValue commonWeight
    hweight_pos.ne' hleft_nonempty hright_nonempty

/--
With a nonzero common survey weight and nonempty samples, a two-sample
normalized-weight contrast is the corresponding contrast of ordinary finite
sample averages.
-/
theorem sum_normalizedSurveyWeight_constant_weight_mul_sub_eq_card_average_sub_of_nonempty
    (leftSample rightSample : Finset Unit)
    (leftValue rightValue : Unit -> Real) (commonWeight : Real)
    (hweight : commonWeight ≠ 0)
    (hleft_nonempty : leftSample.Nonempty)
    (hright_nonempty : rightSample.Nonempty) :
    (∑ unit ∈ leftSample,
        normalizedSurveyWeight leftSample (fun _unit => commonWeight) unit *
          leftValue unit) -
        (∑ unit ∈ rightSample,
          normalizedSurveyWeight rightSample (fun _unit => commonWeight) unit *
            rightValue unit) =
      (∑ unit ∈ leftSample, leftValue unit) / (leftSample.card : Real) -
        (∑ unit ∈ rightSample, rightValue unit) /
          (rightSample.card : Real) := by
  rw [sum_normalizedSurveyWeight_constant_weight_mul_eq_card_average_of_nonempty
    leftSample leftValue commonWeight hweight hleft_nonempty]
  rw [sum_normalizedSurveyWeight_constant_weight_mul_eq_card_average_of_nonempty
    rightSample rightValue commonWeight hweight hright_nonempty]

/--
Positive common survey weights are enough for the nonempty two-sample
normalized-weight contrast specialization.
-/
theorem sum_normalizedSurveyWeight_constant_weight_mul_sub_eq_card_average_sub_of_pos_nonempty
    (leftSample rightSample : Finset Unit)
    (leftValue rightValue : Unit -> Real) (commonWeight : Real)
    (hweight_pos : 0 < commonWeight)
    (hleft_nonempty : leftSample.Nonempty)
    (hright_nonempty : rightSample.Nonempty) :
    (∑ unit ∈ leftSample,
        normalizedSurveyWeight leftSample (fun _unit => commonWeight) unit *
          leftValue unit) -
        (∑ unit ∈ rightSample,
          normalizedSurveyWeight rightSample (fun _unit => commonWeight) unit *
            rightValue unit) =
      (∑ unit ∈ leftSample, leftValue unit) / (leftSample.card : Real) -
        (∑ unit ∈ rightSample, rightValue unit) /
          (rightSample.card : Real) :=
  sum_normalizedSurveyWeight_constant_weight_mul_sub_eq_card_average_sub_of_nonempty
    leftSample rightSample leftValue rightValue commonWeight
    hweight_pos.ne' hleft_nonempty hright_nonempty

/--
On a common nonempty sample, a common-weight Hájek contrast is the ordinary
finite average of the pointwise difference.
-/
theorem hajekMean_constant_weight_sub_eq_card_average_difference_of_nonempty
    (sample : Finset Unit) (leftValue rightValue : Unit -> Real)
    (commonWeight : Real) (hweight : commonWeight ≠ 0)
    (hnonempty : sample.Nonempty) :
    hajekMean sample (fun _unit => commonWeight) leftValue -
        hajekMean sample (fun _unit => commonWeight) rightValue =
      (∑ unit ∈ sample, (leftValue unit - rightValue unit)) /
        (sample.card : Real) := by
  rw [hajekMean_constant_weight_eq_card_average_of_nonempty
    sample leftValue commonWeight hweight hnonempty]
  rw [hajekMean_constant_weight_eq_card_average_of_nonempty
    sample rightValue commonWeight hweight hnonempty]
  have hsum := Finset.sum_sub_distrib (s := sample) leftValue rightValue
  rw [hsum]
  ring

/--
Positive common survey weights are enough for the common-sample Hájek contrast
as an ordinary average of pointwise differences.
-/
theorem hajekMean_constant_weight_sub_eq_card_average_difference_of_pos_nonempty
    (sample : Finset Unit) (leftValue rightValue : Unit -> Real)
    (commonWeight : Real) (hweight_pos : 0 < commonWeight)
    (hnonempty : sample.Nonempty) :
    hajekMean sample (fun _unit => commonWeight) leftValue -
        hajekMean sample (fun _unit => commonWeight) rightValue =
      (∑ unit ∈ sample, (leftValue unit - rightValue unit)) /
        (sample.card : Real) :=
  hajekMean_constant_weight_sub_eq_card_average_difference_of_nonempty
    sample leftValue rightValue commonWeight hweight_pos.ne' hnonempty

/--
On a common nonempty sample, a common-weight normalized-weight contrast is the
ordinary finite average of the pointwise difference.
-/
theorem sum_normalizedSurveyWeight_constant_weight_mul_sub_mul_eq_card_average_difference_of_nonempty
    (sample : Finset Unit) (leftValue rightValue : Unit -> Real)
    (commonWeight : Real) (hweight : commonWeight ≠ 0)
    (hnonempty : sample.Nonempty) :
    (∑ unit ∈ sample,
        normalizedSurveyWeight sample (fun _unit => commonWeight) unit *
          leftValue unit) -
        (∑ unit ∈ sample,
          normalizedSurveyWeight sample (fun _unit => commonWeight) unit *
            rightValue unit) =
      (∑ unit ∈ sample, (leftValue unit - rightValue unit)) /
        (sample.card : Real) := by
  rw [sum_normalizedSurveyWeight_constant_weight_mul_eq_card_average_of_nonempty
    sample leftValue commonWeight hweight hnonempty]
  rw [sum_normalizedSurveyWeight_constant_weight_mul_eq_card_average_of_nonempty
    sample rightValue commonWeight hweight hnonempty]
  have hsum := Finset.sum_sub_distrib (s := sample) leftValue rightValue
  rw [hsum]
  ring

/--
Positive common survey weights are enough for the common-sample
normalized-weight contrast as an ordinary average of pointwise differences.
-/
theorem sum_normalizedSurveyWeight_constant_weight_mul_sub_mul_eq_card_average_difference_of_pos_nonempty
    (sample : Finset Unit) (leftValue rightValue : Unit -> Real)
    (commonWeight : Real) (hweight_pos : 0 < commonWeight)
    (hnonempty : sample.Nonempty) :
    (∑ unit ∈ sample,
        normalizedSurveyWeight sample (fun _unit => commonWeight) unit *
          leftValue unit) -
        (∑ unit ∈ sample,
          normalizedSurveyWeight sample (fun _unit => commonWeight) unit *
            rightValue unit) =
      (∑ unit ∈ sample, (leftValue unit - rightValue unit)) /
        (sample.card : Real) :=
  sum_normalizedSurveyWeight_constant_weight_mul_sub_mul_eq_card_average_difference_of_nonempty
    sample leftValue rightValue commonWeight hweight_pos.ne' hnonempty

end WDSM
end Matching
end StatInference
