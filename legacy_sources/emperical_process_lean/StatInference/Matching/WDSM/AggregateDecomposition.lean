import StatInference.Matching.WDSM.BiasDecomposition

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
