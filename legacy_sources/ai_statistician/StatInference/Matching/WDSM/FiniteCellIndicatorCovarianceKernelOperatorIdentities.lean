import StatInference.Matching.WDSM.FiniteCellIndicatorCovarianceKernelOperatorBounds

/-!
# Operator identities for finite score-cell covariance kernels

The finite covariance-kernel row action is a centered loading.  Target 355
proved the corresponding left-action bounds by symmetry.  This module records
the exact left-action identity and reduces the bilinear covariance-kernel form
to single finite sums against centered loadings.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Cell : Type*} [DecidableEq Cell]

/-- The covariance-kernel left action is the reference share times the centered loading. -/
theorem sum_loading_mul_scoreCellIndicatorCovarianceKernel_eq_share_mul_centered
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    (cellB : Cell) (hcellB : cellB ∈ cells) :
    (∑ cellA ∈ cells,
        loading cellA *
          scoreCellIndicatorCovarianceKernel referenceShare cellA cellB) =
      referenceShare cellB *
        (loading cellB -
          scoreCellLoadingReferenceMean cells referenceShare loading) := by
  rw [sum_loading_mul_scoreCellIndicatorCovarianceKernel_eq_sum_kernel_mul_loading]
  exact
    sum_scoreCellIndicatorCovarianceKernel_mul_loading_eq_share_mul_centered
      cells referenceShare loading cellB hcellB

/--
The bilinear covariance-kernel form is a single finite sum of the left loading
against the centered right loading.
-/
theorem scoreCellBilinearCovarianceKernelForm_eq_sum_left_mul_share_mul_centered_right
    (cells : Finset Cell) (referenceShare loadingA loadingB : Cell -> Real) :
    scoreCellBilinearCovarianceKernelForm
        cells referenceShare loadingA loadingB =
      ∑ cellA ∈ cells,
        loadingA cellA *
          (referenceShare cellA *
            (loadingB cellA -
              scoreCellLoadingReferenceMean cells referenceShare loadingB)) := by
  unfold scoreCellBilinearCovarianceKernelForm
  calc
    (∑ cellA ∈ cells, ∑ cellB ∈ cells,
        loadingA cellA * loadingB cellB *
          scoreCellIndicatorCovarianceKernel referenceShare cellA cellB) =
        ∑ cellA ∈ cells,
          loadingA cellA *
            (∑ cellB ∈ cells,
              scoreCellIndicatorCovarianceKernel referenceShare cellA cellB *
                loadingB cellB) := by
          exact Finset.sum_congr rfl
            (fun cellA _hcellA => by
              rw [Finset.mul_sum]
              exact Finset.sum_congr rfl
                (fun cellB _hcellB => by ring))
    _ =
        ∑ cellA ∈ cells,
          loadingA cellA *
            (referenceShare cellA *
              (loadingB cellA -
                scoreCellLoadingReferenceMean cells referenceShare loadingB)) := by
          exact Finset.sum_congr rfl
            (fun cellA hcellA => by
              rw [
                sum_scoreCellIndicatorCovarianceKernel_mul_loading_eq_share_mul_centered
                  cells referenceShare loadingB cellA hcellA])

/--
The bilinear covariance-kernel form is also a single finite sum of the right
loading against the centered left loading.
-/
theorem scoreCellBilinearCovarianceKernelForm_eq_sum_right_mul_share_mul_centered_left
    (cells : Finset Cell) (referenceShare loadingA loadingB : Cell -> Real) :
    scoreCellBilinearCovarianceKernelForm
        cells referenceShare loadingA loadingB =
      ∑ cellB ∈ cells,
        loadingB cellB *
          (referenceShare cellB *
            (loadingA cellB -
              scoreCellLoadingReferenceMean cells referenceShare loadingA)) := by
  rw [scoreCellBilinearCovarianceKernelForm_comm]
  exact
    scoreCellBilinearCovarianceKernelForm_eq_sum_left_mul_share_mul_centered_right
      cells referenceShare loadingB loadingA

end WDSM
end Matching
end StatInference
