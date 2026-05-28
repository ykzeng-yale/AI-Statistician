import StatInference.Matching.WDSM.FiniteCellIndicatorCovarianceBilinearShift

/-!
# Centered-loadings for bilinear finite score-cell covariance forms

Covariance kernels only see loadings modulo constants.  This module turns the
constant-shift invariance into explicit centered-loading replacements for
finite bilinear covariance targets.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Cell : Type*} [DecidableEq Cell]

omit [DecidableEq Cell] in
/-- The reference-share mean of a centered finite loading is zero. -/
theorem scoreCellLoadingReferenceMean_centered_eq_zero
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    scoreCellLoadingReferenceMean cells referenceShare
        (fun cell =>
          loading cell -
            scoreCellLoadingReferenceMean cells referenceShare loading) =
      0 := by
  unfold scoreCellLoadingReferenceMean
  exact
    sum_referenceShare_mul_loading_sub_referenceMean_eq_zero
      cells referenceShare loading hshare_sum

/-- Centering the left loading leaves the bilinear covariance-kernel form unchanged. -/
theorem scoreCellBilinearCovarianceKernelForm_center_left_eq
    (cells : Finset Cell) (referenceShare loadingA loadingB : Cell -> Real)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    scoreCellBilinearCovarianceKernelForm cells referenceShare
        (fun cell =>
          loadingA cell -
            scoreCellLoadingReferenceMean cells referenceShare loadingA)
        loadingB =
      scoreCellBilinearCovarianceKernelForm
        cells referenceShare loadingA loadingB := by
  simpa [sub_eq_add_neg] using
    scoreCellBilinearCovarianceKernelForm_add_const_left_eq
      cells referenceShare loadingA loadingB
      (-scoreCellLoadingReferenceMean cells referenceShare loadingA)
      hshare_sum

/-- Centering the right loading leaves the bilinear covariance-kernel form unchanged. -/
theorem scoreCellBilinearCovarianceKernelForm_center_right_eq
    (cells : Finset Cell) (referenceShare loadingA loadingB : Cell -> Real)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    scoreCellBilinearCovarianceKernelForm cells referenceShare loadingA
        (fun cell =>
          loadingB cell -
            scoreCellLoadingReferenceMean cells referenceShare loadingB) =
      scoreCellBilinearCovarianceKernelForm
        cells referenceShare loadingA loadingB := by
  simpa [sub_eq_add_neg] using
    scoreCellBilinearCovarianceKernelForm_add_const_right_eq
      cells referenceShare loadingA loadingB
      (-scoreCellLoadingReferenceMean cells referenceShare loadingB)
      hshare_sum

/-- Centering both loadings leaves the bilinear covariance-kernel form unchanged. -/
theorem scoreCellBilinearCovarianceKernelForm_center_both_eq
    (cells : Finset Cell) (referenceShare loadingA loadingB : Cell -> Real)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    scoreCellBilinearCovarianceKernelForm cells referenceShare
        (fun cell =>
          loadingA cell -
            scoreCellLoadingReferenceMean cells referenceShare loadingA)
        (fun cell =>
          loadingB cell -
            scoreCellLoadingReferenceMean cells referenceShare loadingB) =
      scoreCellBilinearCovarianceKernelForm
        cells referenceShare loadingA loadingB := by
  rw [scoreCellBilinearCovarianceKernelForm_center_left_eq
    cells referenceShare loadingA
    (fun cell =>
      loadingB cell -
        scoreCellLoadingReferenceMean cells referenceShare loadingB)
    hshare_sum]
  exact
    scoreCellBilinearCovarianceKernelForm_center_right_eq
      cells referenceShare loadingA loadingB hshare_sum

end WDSM
end Matching
end StatInference
