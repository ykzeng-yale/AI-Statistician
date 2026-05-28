import StatInference.Matching.WDSM.FiniteCellIndicatorCovarianceBounds
import StatInference.Matching.WDSM.FiniteCellIndicatorCovarianceMatrix
import StatInference.Matching.WDSM.FiniteCellIndicatorLinearProjectionCardinalityBounds

/-!
# Simplex-derived finite score-cell bounds

Several finite-indicator CLT envelopes assume reference shares are bounded by
one in absolute value.  For WDSM score partitions this follows from the
simplex hypotheses: nonnegative reference shares over the finite cells summing
to one.  This module records that reduction and uses it to bound covariance
row actions under bounded finite loadings.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit Cell : Type*} [DecidableEq Cell]

omit [DecidableEq Cell] in
/-- A nonnegative reference share in a finite simplex is at most one. -/
theorem referenceShare_le_one_of_mem_of_nonneg_sum_one
    (cells : Finset Cell) (referenceShare : Cell -> Real) (cell : Cell)
    (hcell : cell ∈ cells)
    (hshare_nonneg : ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    referenceShare cell ≤ 1 := by
  have hle_sum : referenceShare cell ≤ ∑ cell ∈ cells, referenceShare cell :=
    Finset.single_le_sum (fun other hother => hshare_nonneg other hother)
      hcell
  rwa [hshare_sum] at hle_sum

omit [DecidableEq Cell] in
/-- A nonnegative reference share in a finite simplex has absolute value at most one. -/
theorem abs_referenceShare_le_one_of_mem_of_nonneg_sum_one
    (cells : Finset Cell) (referenceShare : Cell -> Real) (cell : Cell)
    (hcell : cell ∈ cells)
    (hshare_nonneg : ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    |referenceShare cell| ≤ 1 := by
  have hnonneg : 0 ≤ referenceShare cell := hshare_nonneg cell hcell
  have hle :
      referenceShare cell ≤ 1 :=
    referenceShare_le_one_of_mem_of_nonneg_sum_one
      cells referenceShare cell hcell hshare_nonneg hshare_sum
  rwa [abs_of_nonneg hnonneg]

omit [DecidableEq Cell] in
/--
The centered-linear-projection envelope cardinality bound follows directly
from simplex reference shares, without a separate `|referenceShare| ≤ 1`
assumption.
-/
theorem
    scoreCellLinearCenteredIndicatorEnvelope_le_card_mul_loadingBound_two_of_simplex
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    (loadingBound : Real) (hloading_nonneg : 0 ≤ loadingBound)
    (hshare_nonneg : ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hloading :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ loadingBound) :
    scoreCellLinearCenteredIndicatorEnvelope cells referenceShare loading ≤
      (cells.card : Real) * (loadingBound * 2) :=
  scoreCellLinearCenteredIndicatorEnvelope_le_card_mul_loadingBound_two
    cells referenceShare loading loadingBound hloading_nonneg hloading
    (fun cell hcell =>
      abs_referenceShare_le_one_of_mem_of_nonneg_sum_one
        cells referenceShare cell hcell hshare_nonneg hshare_sum)

/-- Simplex-form cardinality bound for a centered finite score-cell projection. -/
theorem abs_scoreCellLinearCenteredIndicator_le_card_mul_loadingBound_two_of_simplex
    (cells : Finset Cell) (score : Unit -> Cell)
    (referenceShare loading : Cell -> Real) (unit : Unit)
    (loadingBound : Real) (hloading_nonneg : 0 ≤ loadingBound)
    (hshare_nonneg : ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hloading :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ loadingBound) :
    |scoreCellLinearCenteredIndicator cells score referenceShare loading unit| ≤
      (cells.card : Real) * (loadingBound * 2) :=
  abs_scoreCellLinearCenteredIndicator_le_card_mul_loadingBound_two
    cells score referenceShare loading unit loadingBound hloading_nonneg
    hloading
    (fun cell hcell =>
      abs_referenceShare_le_one_of_mem_of_nonneg_sum_one
        cells referenceShare cell hcell hshare_nonneg hshare_sum)

/--
Simplex-form sample weighted-sum bound for a centered finite score-cell
projection.
-/
theorem
    abs_weightedSampleSum_scoreCellLinearCenteredIndicator_le_sum_abs_weight_mul_card_mul_loadingBound_two_of_simplex
    (sample : Finset Unit) (cells : Finset Cell)
    (weight : Unit -> Real) (score : Unit -> Cell)
    (referenceShare loading : Cell -> Real)
    (loadingBound : Real) (hloading_nonneg : 0 ≤ loadingBound)
    (hshare_nonneg : ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hloading :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ loadingBound) :
    |weightedSampleSum sample weight
        (scoreCellLinearCenteredIndicator
          cells score referenceShare loading)| ≤
      (∑ unit ∈ sample, |weight unit|) *
        ((cells.card : Real) * (loadingBound * 2)) :=
  abs_weightedSampleSum_scoreCellLinearCenteredIndicator_le_sum_abs_weight_mul_card_mul_loadingBound_two
    sample cells weight score referenceShare loading loadingBound
    hloading_nonneg hloading
    (fun cell hcell =>
      abs_referenceShare_le_one_of_mem_of_nonneg_sum_one
        cells referenceShare cell hcell hshare_nonneg hshare_sum)

/--
The covariance-kernel row action on a bounded loading is bounded by the row's
reference share times the two-sided loading envelope.
-/
theorem
    abs_sum_scoreCellIndicatorCovarianceKernel_mul_loading_le_referenceShare_mul_loadingBound_two
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    (cellA : Cell) (loadingBound : Real)
    (hcellA : cellA ∈ cells)
    (hshare_nonneg : ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hloading :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ loadingBound) :
    |∑ cellB ∈ cells,
        scoreCellIndicatorCovarianceKernel referenceShare cellA cellB *
          loading cellB| ≤
      referenceShare cellA * (loadingBound * 2) := by
  rw [
    sum_scoreCellIndicatorCovarianceKernel_mul_loading_eq_share_mul_centered
      cells referenceShare loading cellA hcellA]
  rw [abs_mul, abs_of_nonneg (hshare_nonneg cellA hcellA)]
  exact mul_le_mul_of_nonneg_left
    (abs_loading_sub_scoreCellLoadingReferenceMean_le_two_loadingBound
      cells referenceShare loading cellA loadingBound hcellA hshare_nonneg
      hshare_sum hloading)
    (hshare_nonneg cellA hcellA)

/--
The covariance-kernel row action on a bounded loading is uniformly bounded by
the two-sided loading envelope under simplex reference shares.
-/
theorem
    abs_sum_scoreCellIndicatorCovarianceKernel_mul_loading_le_loadingBound_two
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    (cellA : Cell) (loadingBound : Real)
    (hloading_nonneg : 0 ≤ loadingBound)
    (hcellA : cellA ∈ cells)
    (hshare_nonneg : ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hloading :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ loadingBound) :
    |∑ cellB ∈ cells,
        scoreCellIndicatorCovarianceKernel referenceShare cellA cellB *
          loading cellB| ≤
      loadingBound * 2 := by
  have hrow :
      |∑ cellB ∈ cells,
          scoreCellIndicatorCovarianceKernel referenceShare cellA cellB *
            loading cellB| ≤
        referenceShare cellA * (loadingBound * 2) :=
    abs_sum_scoreCellIndicatorCovarianceKernel_mul_loading_le_referenceShare_mul_loadingBound_two
      cells referenceShare loading cellA loadingBound hcellA hshare_nonneg
      hshare_sum hloading
  have hshare_le_one :
      referenceShare cellA ≤ 1 :=
    referenceShare_le_one_of_mem_of_nonneg_sum_one
      cells referenceShare cellA hcellA hshare_nonneg hshare_sum
  have hbound_nonneg : 0 ≤ loadingBound * 2 :=
    mul_nonneg hloading_nonneg (by norm_num)
  calc
    |∑ cellB ∈ cells,
        scoreCellIndicatorCovarianceKernel referenceShare cellA cellB *
          loading cellB| ≤
        referenceShare cellA * (loadingBound * 2) := hrow
    _ ≤ 1 * (loadingBound * 2) := by
          exact mul_le_mul_of_nonneg_right hshare_le_one hbound_nonneg
    _ = loadingBound * 2 := by ring

end WDSM
end Matching
end StatInference
