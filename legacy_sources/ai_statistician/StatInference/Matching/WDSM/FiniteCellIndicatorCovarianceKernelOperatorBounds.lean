import StatInference.Matching.WDSM.FiniteCellIndicatorCovarianceKernelMatrixBounds

/-!
# Operator bounds for finite score-cell covariance kernels

The row action of the finite score-cell covariance kernel on a bounded loading
was bounded in `FiniteCellIndicatorSimplexBounds`.  This module records the
corresponding left/column action bound, obtained by kernel symmetry.  It is a
small deterministic bridge for later finite-dimensional CLT covariance-vector
arguments.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Cell : Type*} [DecidableEq Cell]

/-- Left multiplication by a loading is the symmetric row action. -/
theorem sum_loading_mul_scoreCellIndicatorCovarianceKernel_eq_sum_kernel_mul_loading
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    (cellB : Cell) :
    (∑ cellA ∈ cells,
        loading cellA *
          scoreCellIndicatorCovarianceKernel referenceShare cellA cellB) =
      ∑ cellA ∈ cells,
        scoreCellIndicatorCovarianceKernel referenceShare cellB cellA *
          loading cellA := by
  exact Finset.sum_congr rfl
    (fun cellA _hcellA => by
      rw [scoreCellIndicatorCovarianceKernel_comm]
      ring)

/--
The covariance-kernel left action on a bounded loading is bounded by the
column's reference share times the two-sided loading envelope.
-/
theorem
    abs_sum_loading_mul_scoreCellIndicatorCovarianceKernel_le_referenceShare_mul_loadingBound_two
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    (cellB : Cell) (loadingBound : Real)
    (hcellB : cellB ∈ cells)
    (hshare_nonneg : ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hloading :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ loadingBound) :
    |∑ cellA ∈ cells,
        loading cellA *
          scoreCellIndicatorCovarianceKernel referenceShare cellA cellB| ≤
      referenceShare cellB * (loadingBound * 2) := by
  rw [sum_loading_mul_scoreCellIndicatorCovarianceKernel_eq_sum_kernel_mul_loading]
  exact
    abs_sum_scoreCellIndicatorCovarianceKernel_mul_loading_le_referenceShare_mul_loadingBound_two
      cells referenceShare loading cellB loadingBound hcellB hshare_nonneg
      hshare_sum hloading

/--
The covariance-kernel left action on a bounded loading is uniformly bounded by
the two-sided loading envelope under simplex reference shares.
-/
theorem
    abs_sum_loading_mul_scoreCellIndicatorCovarianceKernel_le_loadingBound_two
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    (cellB : Cell) (loadingBound : Real)
    (hloading_nonneg : 0 ≤ loadingBound)
    (hcellB : cellB ∈ cells)
    (hshare_nonneg : ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hloading :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ loadingBound) :
    |∑ cellA ∈ cells,
        loading cellA *
          scoreCellIndicatorCovarianceKernel referenceShare cellA cellB| ≤
      loadingBound * 2 := by
  rw [sum_loading_mul_scoreCellIndicatorCovarianceKernel_eq_sum_kernel_mul_loading]
  exact
    abs_sum_scoreCellIndicatorCovarianceKernel_mul_loading_le_loadingBound_two
      cells referenceShare loading cellB loadingBound hloading_nonneg hcellB
      hshare_nonneg hshare_sum hloading

end WDSM
end Matching
end StatInference
