import StatInference.Matching.WDSM.BiasDecomposition
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Ring

/-!
# Aggregate Hajek decomposition algebra for WDSM

This module proves the finite aggregation step used after the WDSM unit-level
decomposition: a pointwise contrast decomposition lifts to the survey-weighted
Hajek estimator after centering by the same target.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit : Type*}

/-- Weighted finite sum over a sample set. -/
noncomputable def weightedSum (sample : Finset Unit)
    (weight value : Unit -> Real) : Real :=
  ∑ unit ∈ sample, weight unit * value unit

/-- Hajek denominator, i.e. the sum of survey weights over the sample set. -/
noncomputable def weightedDenominator (sample : Finset Unit)
    (weight : Unit -> Real) : Real :=
  ∑ unit ∈ sample, weight unit

/-- Hajek mean of `value` under finite survey weights. -/
noncomputable def hajekMean (sample : Finset Unit)
    (weight value : Unit -> Real) : Real :=
  weightedSum sample weight value / weightedDenominator sample weight

theorem weightedSum_zero (sample : Finset Unit)
    (weight : Unit -> Real) :
    weightedSum sample weight (fun _unit => 0) = 0 := by
  simp [weightedSum]

theorem weightedSum_const (sample : Finset Unit)
    (weight : Unit -> Real) (target : Real) :
    weightedSum sample weight (fun _unit => target) =
      target * weightedDenominator sample weight := by
  unfold weightedSum weightedDenominator
  calc
    (∑ unit ∈ sample, weight unit * (fun _unit => target) unit)
        = (∑ unit ∈ sample, weight unit) * target := by
          rw [Finset.sum_mul]
    _ = target * (∑ unit ∈ sample, weight unit) := by
          ring

theorem hajekMean_const (sample : Finset Unit)
    (weight : Unit -> Real) (target : Real)
    (hden : weightedDenominator sample weight ≠ 0) :
    hajekMean sample weight (fun _unit => target) = target := by
  unfold hajekMean
  rw [weightedSum_const]
  field_simp [hden]

theorem hajekMean_zero (sample : Finset Unit)
    (weight : Unit -> Real)
    (hden : weightedDenominator sample weight ≠ 0) :
    hajekMean sample weight (fun _unit => 0) = 0 := by
  simpa using hajekMean_const sample weight 0 hden

theorem weightedSum_congr_on_sample (sample : Finset Unit)
    (weight valueA valueB : Unit -> Real)
    (h : ∀ unit, unit ∈ sample -> valueA unit = valueB unit) :
    weightedSum sample weight valueA = weightedSum sample weight valueB := by
  unfold weightedSum
  exact Finset.sum_congr rfl
    (fun unit hunit => by rw [h unit hunit])

theorem weightedSum_add (sample : Finset Unit)
    (weight valueA valueB : Unit -> Real) :
    weightedSum sample weight (fun unit => valueA unit + valueB unit) =
      weightedSum sample weight valueA + weightedSum sample weight valueB := by
  unfold weightedSum
  simp [mul_add, Finset.sum_add_distrib]

theorem weightedSum_sub (sample : Finset Unit)
    (weight valueA valueB : Unit -> Real) :
    weightedSum sample weight (fun unit => valueA unit - valueB unit) =
      weightedSum sample weight valueA - weightedSum sample weight valueB := by
  unfold weightedSum
  simp [mul_sub, Finset.sum_sub_distrib]

theorem weightedSum_neg (sample : Finset Unit)
    (weight value : Unit -> Real) :
    weightedSum sample weight (fun unit => -value unit) =
      -weightedSum sample weight value := by
  unfold weightedSum
  simp [Finset.sum_neg_distrib]

theorem weightedSum_smul_const (sample : Finset Unit)
    (weight value : Unit -> Real) (scale : Real) :
    weightedSum sample weight (fun unit => scale * value unit) =
      scale * weightedSum sample weight value := by
  unfold weightedSum
  calc
    (∑ unit ∈ sample, weight unit * (scale * value unit))
        = ∑ unit ∈ sample, scale * (weight unit * value unit) := by
          exact Finset.sum_congr rfl (fun unit _hunit => by ring)
    _ = scale * (∑ unit ∈ sample, weight unit * value unit) := by
        rw [Finset.mul_sum]

theorem weightedSum_eq_zero_of_value_zero_on_sample (sample : Finset Unit)
    (weight value : Unit -> Real)
    (hzero : ∀ unit, unit ∈ sample -> value unit = 0) :
    weightedSum sample weight value = 0 := by
  unfold weightedSum
  exact Finset.sum_eq_zero
    (fun unit hunit => by rw [hzero unit hunit]; ring)

theorem weightedSum_eq_zero_of_weight_zero_on_sample (sample : Finset Unit)
    (weight value : Unit -> Real)
    (hzero : ∀ unit, unit ∈ sample -> weight unit = 0) :
    weightedSum sample weight value = 0 := by
  unfold weightedSum
  exact Finset.sum_eq_zero
    (fun unit hunit => by rw [hzero unit hunit]; ring)

theorem weightedDenominator_eq_weightedSum_one (sample : Finset Unit)
    (weight : Unit -> Real) :
    weightedDenominator sample weight =
      weightedSum sample weight (fun _unit => 1) := by
  simp [weightedDenominator, weightedSum]

theorem weightedDenominator_nonneg (sample : Finset Unit)
    (weight : Unit -> Real)
    (hweight_nonneg : ∀ unit, unit ∈ sample -> 0 ≤ weight unit) :
    0 ≤ weightedDenominator sample weight := by
  unfold weightedDenominator
  exact Finset.sum_nonneg (fun unit hunit => hweight_nonneg unit hunit)

theorem weightedSum_nonneg (sample : Finset Unit)
    (weight value : Unit -> Real)
    (hweight_nonneg : ∀ unit, unit ∈ sample -> 0 ≤ weight unit)
    (hvalue_nonneg : ∀ unit, unit ∈ sample -> 0 ≤ value unit) :
    0 ≤ weightedSum sample weight value := by
  unfold weightedSum
  exact Finset.sum_nonneg
    (fun unit hunit => mul_nonneg
      (hweight_nonneg unit hunit) (hvalue_nonneg unit hunit))

theorem hajekMean_congr_on_sample (sample : Finset Unit)
    (weight valueA valueB : Unit -> Real)
    (h : ∀ unit, unit ∈ sample -> valueA unit = valueB unit) :
    hajekMean sample weight valueA = hajekMean sample weight valueB := by
  unfold hajekMean
  rw [weightedSum_congr_on_sample sample weight valueA valueB h]

theorem hajekMean_add (sample : Finset Unit)
    (weight valueA valueB : Unit -> Real)
    (hden : weightedDenominator sample weight ≠ 0) :
    hajekMean sample weight (fun unit => valueA unit + valueB unit) =
      hajekMean sample weight valueA + hajekMean sample weight valueB := by
  unfold hajekMean
  rw [weightedSum_add]
  field_simp [hden]

theorem hajekMean_sub (sample : Finset Unit)
    (weight valueA valueB : Unit -> Real)
    (hden : weightedDenominator sample weight ≠ 0) :
    hajekMean sample weight (fun unit => valueA unit - valueB unit) =
      hajekMean sample weight valueA - hajekMean sample weight valueB := by
  unfold hajekMean
  rw [weightedSum_sub]
  field_simp [hden]

theorem hajekMean_neg (sample : Finset Unit)
    (weight value : Unit -> Real)
    (hden : weightedDenominator sample weight ≠ 0) :
    hajekMean sample weight (fun unit => -value unit) =
      -hajekMean sample weight value := by
  unfold hajekMean
  rw [weightedSum_neg]
  field_simp [hden]

theorem hajekMean_smul_const (sample : Finset Unit)
    (weight value : Unit -> Real) (scale : Real)
    (hden : weightedDenominator sample weight ≠ 0) :
    hajekMean sample weight (fun unit => scale * value unit) =
      scale * hajekMean sample weight value := by
  unfold hajekMean
  rw [weightedSum_smul_const]
  field_simp [hden]

theorem hajekMean_eq_zero_of_weightedSum_zero (sample : Finset Unit)
    (weight value : Unit -> Real)
    (hzero : weightedSum sample weight value = 0) :
    hajekMean sample weight value = 0 := by
  simp [hajekMean, hzero]

theorem hajekMean_nonneg (sample : Finset Unit)
    (weight value : Unit -> Real)
    (hweight_nonneg : ∀ unit, unit ∈ sample -> 0 ≤ weight unit)
    (hvalue_nonneg : ∀ unit, unit ∈ sample -> 0 ≤ value unit)
    (hden_pos : 0 < weightedDenominator sample weight) :
    0 ≤ hajekMean sample weight value := by
  unfold hajekMean
  exact div_nonneg
    (weightedSum_nonneg sample weight value hweight_nonneg hvalue_nonneg)
    hden_pos.le

theorem weightedSum_sub_const (sample : Finset Unit)
    (weight value : Unit -> Real) (target : Real) :
    weightedSum sample weight (fun unit => value unit - target) =
      weightedSum sample weight value -
        target * weightedDenominator sample weight := by
  unfold weightedSum weightedDenominator
  calc
    (∑ unit ∈ sample, weight unit * (value unit - target))
        = (∑ unit ∈ sample,
            (weight unit * value unit - weight unit * target)) := by
          exact Finset.sum_congr rfl
            (fun unit _hunit => by ring)
    _ = (∑ unit ∈ sample, weight unit * value unit) -
          (∑ unit ∈ sample, weight unit * target) := by
        rw [Finset.sum_sub_distrib]
    _ = (∑ unit ∈ sample, weight unit * value unit) -
          (∑ unit ∈ sample, weight unit) * target := by
        rw [Finset.sum_mul]
    _ = (∑ unit ∈ sample, weight unit * value unit) -
          target * (∑ unit ∈ sample, weight unit) := by
        ring

theorem hajekMean_sub_const (sample : Finset Unit)
    (weight value : Unit -> Real) (target : Real)
    (hden : weightedDenominator sample weight ≠ 0) :
    hajekMean sample weight value - target =
      weightedSum sample weight (fun unit => value unit - target) /
        weightedDenominator sample weight := by
  unfold hajekMean
  rw [weightedSum_sub_const]
  field_simp [hden]

theorem weightedSum_four_decomposition (sample : Finset Unit)
    (weight first second third fourth : Unit -> Real) :
    weightedSum sample weight
        (fun unit => first unit + second unit - third unit + fourth unit) =
      weightedSum sample weight first +
        weightedSum sample weight second -
          weightedSum sample weight third +
            weightedSum sample weight fourth := by
  unfold weightedSum
  calc
    (∑ unit ∈ sample,
        weight unit * (first unit + second unit - third unit + fourth unit))
        = (∑ unit ∈ sample,
            (((weight unit * first unit + weight unit * second unit) -
              weight unit * third unit) +
                weight unit * fourth unit)) := by
          exact Finset.sum_congr rfl
            (fun unit _hunit => by ring)
    _ = ((∑ unit ∈ sample, (weight unit * first unit + weight unit * second unit)) -
          (∑ unit ∈ sample, weight unit * third unit)) +
            (∑ unit ∈ sample, weight unit * fourth unit) := by
        rw [Finset.sum_add_distrib]
        rw [Finset.sum_sub_distrib]
    _ = ((∑ unit ∈ sample, weight unit * first unit) +
          (∑ unit ∈ sample, weight unit * second unit) -
            (∑ unit ∈ sample, weight unit * third unit)) +
              (∑ unit ∈ sample, weight unit * fourth unit) := by
        rw [Finset.sum_add_distrib]
    _ = (∑ unit ∈ sample, weight unit * first unit) +
          (∑ unit ∈ sample, weight unit * second unit) -
            (∑ unit ∈ sample, weight unit * third unit) +
              (∑ unit ∈ sample, weight unit * fourth unit) := by
        ring

/--
Pointwise WDSM decomposition lifted to a weighted finite sum.

The signs match the appendix convention:
`contrast - target = heterogeneity + ownResidual - matchedResidual + discrepancy`.
-/
theorem weightedSum_pointwise_decomposition (sample : Finset Unit)
    (weight contrast heterogeneity ownResidual matchedResidual discrepancy :
      Unit -> Real)
    (target : Real)
    (hpoint : ∀ unit, unit ∈ sample ->
      contrast unit - target =
        heterogeneity unit + ownResidual unit -
          matchedResidual unit + discrepancy unit) :
    weightedSum sample weight (fun unit => contrast unit - target) =
      weightedSum sample weight heterogeneity +
        weightedSum sample weight ownResidual -
          weightedSum sample weight matchedResidual +
            weightedSum sample weight discrepancy := by
  calc
    weightedSum sample weight (fun unit => contrast unit - target)
        = weightedSum sample weight
            (fun unit =>
              heterogeneity unit + ownResidual unit -
                matchedResidual unit + discrepancy unit) := by
          unfold weightedSum
          exact Finset.sum_congr rfl
            (fun unit hunit => by
              simp [hpoint unit hunit])
    _ = weightedSum sample weight heterogeneity +
          weightedSum sample weight ownResidual -
            weightedSum sample weight matchedResidual +
              weightedSum sample weight discrepancy := by
        exact weightedSum_four_decomposition sample weight heterogeneity
          ownResidual matchedResidual discrepancy

/--
Hajek-normalized aggregate decomposition.

This is the algebraic bridge from the exact finite WDSM decomposition to later
probability-limit and CLT statements for the four aggregate components.
-/
theorem hajekMean_pointwise_decomposition (sample : Finset Unit)
    (weight contrast heterogeneity ownResidual matchedResidual discrepancy :
      Unit -> Real)
    (target : Real)
    (hden : weightedDenominator sample weight ≠ 0)
    (hpoint : ∀ unit, unit ∈ sample ->
      contrast unit - target =
        heterogeneity unit + ownResidual unit -
          matchedResidual unit + discrepancy unit) :
    hajekMean sample weight contrast - target =
      (weightedSum sample weight heterogeneity +
        weightedSum sample weight ownResidual -
          weightedSum sample weight matchedResidual +
            weightedSum sample weight discrepancy) /
        weightedDenominator sample weight := by
  rw [hajekMean_sub_const sample weight contrast target hden]
  rw [weightedSum_pointwise_decomposition sample weight contrast
    heterogeneity ownResidual matchedResidual discrepancy target hpoint]

end WDSM
end Matching
end StatInference
