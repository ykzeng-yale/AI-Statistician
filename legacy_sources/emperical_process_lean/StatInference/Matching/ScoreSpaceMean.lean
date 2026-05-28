import StatInference.Matching.WDSM.EstimatorAlgebra

/-!
# Score-space mean algebra for WDSM matched sets

This module proves deterministic finite facts behind the WDSM score-space mean
and matching-bias arguments.  If donor means are equal to the focal mean on a
matched set, the imputed mean is exact.  More generally, with nonnegative
sum-to-one coefficients, the absolute mean discrepancy is bounded by the
largest donor-side mean discrepancy radius.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit : Type*}

/-- Weighted mean discrepancy induced by one focal unit's matched donor set. -/
noncomputable def meanDiscrepancy (donorSet : Finset Unit)
    (coefficient : Unit -> Unit -> Real) (mean : Unit -> Real)
    (focal : Unit) : Real :=
  ∑ donor ∈ donorSet, coefficient focal donor * (mean focal - mean donor)

theorem imputed_mean_eq_of_exact_mean_match
    (donorSet : Finset Unit)
    (coefficient : Unit -> Unit -> Real) (mean : Unit -> Real)
    (focal : Unit)
    (hsum : (∑ donor ∈ donorSet, coefficient focal donor) = 1)
    (hmean : ∀ donor, donor ∈ donorSet -> mean donor = mean focal) :
    imputedOutcome donorSet coefficient mean focal = mean focal := by
  unfold imputedOutcome
  calc
    (∑ donor ∈ donorSet, coefficient focal donor * mean donor)
        = ∑ donor ∈ donorSet,
            coefficient focal donor * mean focal := by
          exact Finset.sum_congr rfl
            (fun donor hdonor => by
              rw [hmean donor hdonor])
    _ = (∑ donor ∈ donorSet, coefficient focal donor) * mean focal := by
        rw [Finset.sum_mul]
    _ = mean focal := by
        rw [hsum]
        ring

theorem meanDiscrepancy_zero_of_exact_mean_match
    (donorSet : Finset Unit)
    (coefficient : Unit -> Unit -> Real) (mean : Unit -> Real)
    (focal : Unit)
    (hmean : ∀ donor, donor ∈ donorSet -> mean donor = mean focal) :
    meanDiscrepancy donorSet coefficient mean focal = 0 := by
  unfold meanDiscrepancy
  exact Finset.sum_eq_zero
    (fun donor hdonor => by
      rw [hmean donor hdonor]
      ring)

theorem abs_meanDiscrepancy_le_radius
    (donorSet : Finset Unit)
    (coefficient : Unit -> Unit -> Real) (mean : Unit -> Real)
    (focal : Unit) (radius : Real)
    (hcoeff_nonneg :
      ∀ donor, donor ∈ donorSet -> 0 ≤ coefficient focal donor)
    (hsum : (∑ donor ∈ donorSet, coefficient focal donor) = 1)
    (hbound :
      ∀ donor, donor ∈ donorSet -> |mean focal - mean donor| ≤ radius) :
    |meanDiscrepancy donorSet coefficient mean focal| ≤ radius := by
  unfold meanDiscrepancy
  calc
    |∑ donor ∈ donorSet,
        coefficient focal donor * (mean focal - mean donor)|
        ≤ ∑ donor ∈ donorSet,
            |coefficient focal donor * (mean focal - mean donor)| := by
          exact Finset.abs_sum_le_sum_abs _ _
    _ = ∑ donor ∈ donorSet,
          coefficient focal donor * |mean focal - mean donor| := by
        exact Finset.sum_congr rfl
          (fun donor hdonor => by
            rw [abs_mul, abs_of_nonneg (hcoeff_nonneg donor hdonor)])
    _ ≤ ∑ donor ∈ donorSet, coefficient focal donor * radius := by
        exact Finset.sum_le_sum
          (fun donor hdonor =>
            mul_le_mul_of_nonneg_left (hbound donor hdonor)
              (hcoeff_nonneg donor hdonor))
    _ = (∑ donor ∈ donorSet, coefficient focal donor) * radius := by
        rw [Finset.sum_mul]
    _ = radius := by
        rw [hsum]
        ring

end WDSM
end Matching
end StatInference
