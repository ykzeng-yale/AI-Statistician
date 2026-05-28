import StatInference.Matching.WDSM.FiniteCellIndicatorCovarianceKernelBounds

/-!
# Matrix-level bounds for finite score-cell covariance kernels

Target 353 bounded individual covariance-kernel entries and row `L1` norms.
This module records the corresponding column and full finite matrix `L1`
envelopes, giving later finite-dimensional CLT interfaces a simple deterministic
matrix-size bound.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Cell : Type*} [DecidableEq Cell]

/-- A finite covariance-kernel column has `L1` norm bounded by the number of cells. -/
theorem
    sum_abs_scoreCellIndicatorCovarianceKernel_left_le_card_of_mem_of_nonneg_sum_one
    (cells : Finset Cell) (referenceShare : Cell -> Real) (cellB : Cell)
    (hcellB : cellB ∈ cells)
    (hshare_nonneg : ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    (∑ cellA ∈ cells,
        |scoreCellIndicatorCovarianceKernel referenceShare cellA cellB|) ≤
      (cells.card : Real) := by
  calc
    (∑ cellA ∈ cells,
        |scoreCellIndicatorCovarianceKernel referenceShare cellA cellB|) =
        ∑ cellA ∈ cells,
          |scoreCellIndicatorCovarianceKernel referenceShare cellB cellA| := by
          exact Finset.sum_congr rfl
            (fun cellA _hcellA => by
              rw [scoreCellIndicatorCovarianceKernel_comm])
    _ ≤ (cells.card : Real) :=
        sum_abs_scoreCellIndicatorCovarianceKernel_le_card_of_mem_of_nonneg_sum_one
          cells referenceShare cellB hcellB hshare_nonneg hshare_sum

/--
The full finite covariance-kernel matrix has `L1` norm bounded by the square
of the number of score cells.
-/
theorem sum_sum_abs_scoreCellIndicatorCovarianceKernel_le_card_mul_card
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    (hshare_nonneg : ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    (∑ cellA ∈ cells, ∑ cellB ∈ cells,
        |scoreCellIndicatorCovarianceKernel referenceShare cellA cellB|) ≤
      (cells.card : Real) * (cells.card : Real) := by
  calc
    (∑ cellA ∈ cells, ∑ cellB ∈ cells,
        |scoreCellIndicatorCovarianceKernel referenceShare cellA cellB|) ≤
        ∑ _cellA ∈ cells, (cells.card : Real) := by
          exact Finset.sum_le_sum
            (fun cellA hcellA =>
              sum_abs_scoreCellIndicatorCovarianceKernel_le_card_of_mem_of_nonneg_sum_one
                cells referenceShare cellA hcellA hshare_nonneg hshare_sum)
    _ = (cells.card : Real) * (cells.card : Real) := by
          simp [nsmul_eq_mul]

end WDSM
end Matching
end StatInference
