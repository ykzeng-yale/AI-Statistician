import StatInference.Matching.WDSM.FiniteCellIndicatorCovarianceKernelOperatorIdentities

/-!
# Shift invariance for bilinear finite score-cell covariance forms

Constant shifts should not affect covariance targets.  The quadratic
shift-invariance theorem is already available for variance forms; this module
adds the corresponding bilinear covariance-kernel invariance needed by later
covariance-matrix and CLT simplifications.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Cell : Type*} [DecidableEq Cell]

omit [DecidableEq Cell] in
/-- Reference-share centered loadings have zero finite reference-share sum. -/
theorem sum_referenceShare_mul_loading_sub_referenceMean_eq_zero
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    (∑ cell ∈ cells,
        referenceShare cell *
          (loading cell -
            scoreCellLoadingReferenceMean cells referenceShare loading)) =
      0 := by
  calc
    (∑ cell ∈ cells,
        referenceShare cell *
          (loading cell -
            scoreCellLoadingReferenceMean cells referenceShare loading)) =
        ∑ cell ∈ cells,
          (referenceShare cell * loading cell -
            referenceShare cell *
              scoreCellLoadingReferenceMean cells referenceShare loading) := by
          exact Finset.sum_congr rfl
            (fun cell _hcell => by ring)
    _ =
        (∑ cell ∈ cells, referenceShare cell * loading cell) -
          (∑ cell ∈ cells,
            referenceShare cell *
              scoreCellLoadingReferenceMean cells referenceShare loading) := by
          rw [Finset.sum_sub_distrib]
    _ =
        scoreCellLoadingReferenceMean cells referenceShare loading -
          (∑ cell ∈ cells, referenceShare cell) *
            scoreCellLoadingReferenceMean cells referenceShare loading := by
          unfold scoreCellLoadingReferenceMean
          rw [← Finset.sum_mul]
    _ = 0 := by
          rw [hshare_sum]
          ring

omit [DecidableEq Cell] in
/-- Adding a constant to the left loading shifts the cross moment by that constant times the right mean. -/
theorem scoreCellLoadingReferenceCrossMoment_add_const_left
    (cells : Finset Cell) (referenceShare loadingA loadingB : Cell -> Real)
    (constant : Real) :
    scoreCellLoadingReferenceCrossMoment cells referenceShare
        (fun cell => loadingA cell + constant) loadingB =
      scoreCellLoadingReferenceCrossMoment
          cells referenceShare loadingA loadingB +
        constant *
          scoreCellLoadingReferenceMean cells referenceShare loadingB := by
  unfold scoreCellLoadingReferenceCrossMoment scoreCellLoadingReferenceMean
  calc
    (∑ cell ∈ cells,
        referenceShare cell * (loadingA cell + constant) * loadingB cell) =
        ∑ cell ∈ cells,
          (referenceShare cell * loadingA cell * loadingB cell +
            constant * (referenceShare cell * loadingB cell)) := by
          exact Finset.sum_congr rfl
            (fun cell _hcell => by ring)
    _ =
        (∑ cell ∈ cells,
          referenceShare cell * loadingA cell * loadingB cell) +
          (∑ cell ∈ cells,
            constant * (referenceShare cell * loadingB cell)) := by
          rw [Finset.sum_add_distrib]
    _ =
        (∑ cell ∈ cells,
          referenceShare cell * loadingA cell * loadingB cell) +
          constant *
            (∑ cell ∈ cells, referenceShare cell * loadingB cell) := by
          rw [Finset.mul_sum]

omit [DecidableEq Cell] in
/-- Adding a constant to the right loading shifts the cross moment by that constant times the left mean. -/
theorem scoreCellLoadingReferenceCrossMoment_add_const_right
    (cells : Finset Cell) (referenceShare loadingA loadingB : Cell -> Real)
    (constant : Real) :
    scoreCellLoadingReferenceCrossMoment cells referenceShare loadingA
        (fun cell => loadingB cell + constant) =
      scoreCellLoadingReferenceCrossMoment
          cells referenceShare loadingA loadingB +
        constant *
          scoreCellLoadingReferenceMean cells referenceShare loadingA := by
  rw [scoreCellLoadingReferenceCrossMoment_comm]
  rw [scoreCellLoadingReferenceCrossMoment_add_const_left]
  rw [scoreCellLoadingReferenceCrossMoment_comm cells referenceShare loadingB loadingA]

/-- Bilinear covariance-kernel forms are invariant under left constant shifts. -/
theorem scoreCellBilinearCovarianceKernelForm_add_const_left_eq
    (cells : Finset Cell) (referenceShare loadingA loadingB : Cell -> Real)
    (constant : Real)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    scoreCellBilinearCovarianceKernelForm cells referenceShare
        (fun cell => loadingA cell + constant) loadingB =
      scoreCellBilinearCovarianceKernelForm
        cells referenceShare loadingA loadingB := by
  rw [scoreCellBilinearCovarianceKernelForm_eq_crossMoment_sub_mean_mul_mean]
  rw [scoreCellBilinearCovarianceKernelForm_eq_crossMoment_sub_mean_mul_mean]
  rw [scoreCellLoadingReferenceCrossMoment_add_const_left]
  rw [scoreCellLoadingReferenceMean_add_const
    cells referenceShare loadingA constant hshare_sum]
  ring

/-- Bilinear covariance-kernel forms are invariant under right constant shifts. -/
theorem scoreCellBilinearCovarianceKernelForm_add_const_right_eq
    (cells : Finset Cell) (referenceShare loadingA loadingB : Cell -> Real)
    (constant : Real)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    scoreCellBilinearCovarianceKernelForm cells referenceShare loadingA
        (fun cell => loadingB cell + constant) =
      scoreCellBilinearCovarianceKernelForm
        cells referenceShare loadingA loadingB := by
  rw [scoreCellBilinearCovarianceKernelForm_comm]
  rw [scoreCellBilinearCovarianceKernelForm_add_const_left_eq
    cells referenceShare loadingB loadingA constant hshare_sum]
  rw [scoreCellBilinearCovarianceKernelForm_comm]

end WDSM
end Matching
end StatInference
