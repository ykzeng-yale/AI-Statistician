import StatInference.Matching.WDSM.BiasBounds
import StatInference.Matching.WDSM.LipschitzBiasBound

/-!
# Aggregate Lipschitz matching-bias bounds for WDSM

This module lifts the unit-level Lipschitz score-radius bound to the finite
Hájek aggregate used by the WDSM matching-discrepancy term.
-/

namespace StatInference
namespace Matching
namespace WDSM

variable {Unit : Type*}

/--
Survey-weighted aggregate mean discrepancy is bounded by the survey-weighted
average of Lipschitz constants times local match radii.
-/
theorem abs_aggregate_meanDiscrepancy_le_lipschitz_radius_average
    (sample : Finset Unit) (donorSet : Unit -> Finset Unit)
    (coefficient : Unit -> Unit -> Real)
    (focalWeight mean : Unit -> Real) (scoreDistance : Unit -> Unit -> Real)
    (lipschitzConstant : Real) (radius : Unit -> Real)
    (hden_pos : 0 < weightedDenominator sample focalWeight)
    (hfocalWeight_nonneg :
      ∀ focal, focal ∈ sample -> 0 ≤ focalWeight focal)
    (hcoeff_nonneg :
      ∀ focal, focal ∈ sample ->
        ∀ donor, donor ∈ donorSet focal -> 0 ≤ coefficient focal donor)
    (hsum :
      ∀ focal, focal ∈ sample ->
        (∑ donor ∈ donorSet focal, coefficient focal donor) = 1)
    (hlipschitz :
      ∀ focal, focal ∈ sample ->
        ∀ donor, donor ∈ donorSet focal ->
          |mean focal - mean donor| ≤
            lipschitzConstant * scoreDistance focal donor)
    (hradius :
      ∀ focal, focal ∈ sample ->
        ∀ donor, donor ∈ donorSet focal ->
          scoreDistance focal donor ≤ radius focal)
    (hlipschitz_nonneg : 0 ≤ lipschitzConstant) :
    |weightedSum sample focalWeight
        (fun focal => meanDiscrepancy (donorSet focal) coefficient mean focal) /
        weightedDenominator sample focalWeight| ≤
      weightedSum sample focalWeight
        (fun focal => lipschitzConstant * radius focal) /
        weightedDenominator sample focalWeight := by
  exact abs_weightedAverage_le_weightedAverage_bound sample focalWeight
    (fun focal => meanDiscrepancy (donorSet focal) coefficient mean focal)
    (fun focal => lipschitzConstant * radius focal)
    hden_pos hfocalWeight_nonneg
    (fun focal hfocal =>
      abs_meanDiscrepancy_le_lipschitz_radius
        (donorSet focal) coefficient mean scoreDistance focal
        lipschitzConstant (radius focal)
        (hcoeff_nonneg focal hfocal)
        (hsum focal hfocal)
        (hlipschitz focal hfocal)
        (hradius focal hfocal)
        hlipschitz_nonneg)

/--
If all local match radii are bounded by a common radius, the aggregate
matching-discrepancy term is bounded by `lipschitzConstant * uniformRadius`.
-/
theorem abs_aggregate_meanDiscrepancy_le_lipschitz_uniform_radius
    (sample : Finset Unit) (donorSet : Unit -> Finset Unit)
    (coefficient : Unit -> Unit -> Real)
    (focalWeight mean : Unit -> Real) (scoreDistance : Unit -> Unit -> Real)
    (lipschitzConstant uniformRadius : Real) (radius : Unit -> Real)
    (hden_pos : 0 < weightedDenominator sample focalWeight)
    (hfocalWeight_nonneg :
      ∀ focal, focal ∈ sample -> 0 ≤ focalWeight focal)
    (hcoeff_nonneg :
      ∀ focal, focal ∈ sample ->
        ∀ donor, donor ∈ donorSet focal -> 0 ≤ coefficient focal donor)
    (hsum :
      ∀ focal, focal ∈ sample ->
        (∑ donor ∈ donorSet focal, coefficient focal donor) = 1)
    (hlipschitz :
      ∀ focal, focal ∈ sample ->
        ∀ donor, donor ∈ donorSet focal ->
          |mean focal - mean donor| ≤
            lipschitzConstant * scoreDistance focal donor)
    (hradius :
      ∀ focal, focal ∈ sample ->
        ∀ donor, donor ∈ donorSet focal ->
          scoreDistance focal donor ≤ radius focal)
    (hradius_uniform :
      ∀ focal, focal ∈ sample -> radius focal ≤ uniformRadius)
    (hlipschitz_nonneg : 0 ≤ lipschitzConstant) :
    |weightedSum sample focalWeight
        (fun focal => meanDiscrepancy (donorSet focal) coefficient mean focal) /
        weightedDenominator sample focalWeight| ≤
      lipschitzConstant * uniformRadius := by
  exact abs_weightedAverage_le_uniform_bound sample focalWeight
    (fun focal => meanDiscrepancy (donorSet focal) coefficient mean focal)
    (lipschitzConstant * uniformRadius)
    hden_pos hfocalWeight_nonneg
    (fun focal hfocal =>
      le_trans
        (abs_meanDiscrepancy_le_lipschitz_radius
          (donorSet focal) coefficient mean scoreDistance focal
          lipschitzConstant (radius focal)
          (hcoeff_nonneg focal hfocal)
          (hsum focal hfocal)
          (hlipschitz focal hfocal)
          (hradius focal hfocal)
          hlipschitz_nonneg)
        (mul_le_mul_of_nonneg_left (hradius_uniform focal hfocal)
          hlipschitz_nonneg))

end WDSM
end Matching
end StatInference
