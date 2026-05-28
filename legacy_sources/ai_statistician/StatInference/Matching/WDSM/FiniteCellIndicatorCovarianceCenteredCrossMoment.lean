import StatInference.Matching.WDSM.FiniteCellIndicatorCovarianceCenteredBilinear
import StatInference.Matching.WDSM.FiniteCellIndicatorCovarianceCenteredLoadings

/-!
# Centered-loadings cross moments for finite score-cell covariance targets

This module connects ordinary reference-share cross moments of explicitly
centered loadings to the centered cross-moment and bilinear covariance-kernel
forms.  These identities are the finite deterministic algebra used to state
later CLT covariance limits with centered loadings.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Cell : Type*} [DecidableEq Cell]

omit [DecidableEq Cell] in
/--
The ordinary cross moment of both centered loadings is exactly the centered
cross moment.
-/
theorem scoreCellLoadingReferenceCrossMoment_center_both_eq_centeredCrossMoment
    (cells : Finset Cell) (referenceShare loadingA loadingB : Cell -> Real) :
    scoreCellLoadingReferenceCrossMoment cells referenceShare
        (fun cell =>
          loadingA cell -
            scoreCellLoadingReferenceMean cells referenceShare loadingA)
        (fun cell =>
          loadingB cell -
            scoreCellLoadingReferenceMean cells referenceShare loadingB) =
      scoreCellLoadingReferenceCenteredCrossMoment
        cells referenceShare loadingA loadingB := by
  unfold scoreCellLoadingReferenceCrossMoment
  unfold scoreCellLoadingReferenceCenteredCrossMoment
  exact Finset.sum_congr rfl
    (fun cell _hcell => by ring)

omit [DecidableEq Cell] in
/--
Under simplex reference shares, centering only the left loading gives the same
cross moment as centering both loadings.
-/
theorem scoreCellLoadingReferenceCrossMoment_center_left_eq_centeredCrossMoment
    (cells : Finset Cell) (referenceShare loadingA loadingB : Cell -> Real)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    scoreCellLoadingReferenceCrossMoment cells referenceShare
        (fun cell =>
          loadingA cell -
            scoreCellLoadingReferenceMean cells referenceShare loadingA)
        loadingB =
      scoreCellLoadingReferenceCenteredCrossMoment
        cells referenceShare loadingA loadingB := by
  let centeredA : Cell -> Real := fun cell =>
    loadingA cell -
      scoreCellLoadingReferenceMean cells referenceShare loadingA
  have hmeanA :
      scoreCellLoadingReferenceMean cells referenceShare centeredA = 0 := by
    dsimp [centeredA]
    exact scoreCellLoadingReferenceMean_centered_eq_zero
      cells referenceShare loadingA hshare_sum
  have hshift :
      scoreCellLoadingReferenceCrossMoment cells referenceShare centeredA
          (fun cell =>
            loadingB cell +
              (-scoreCellLoadingReferenceMean cells referenceShare loadingB)) =
        scoreCellLoadingReferenceCrossMoment
            cells referenceShare centeredA loadingB +
          (-scoreCellLoadingReferenceMean cells referenceShare loadingB) *
            scoreCellLoadingReferenceMean cells referenceShare centeredA :=
    scoreCellLoadingReferenceCrossMoment_add_const_right
      cells referenceShare centeredA loadingB
      (-scoreCellLoadingReferenceMean cells referenceShare loadingB)
  calc
    scoreCellLoadingReferenceCrossMoment cells referenceShare centeredA
        loadingB =
        scoreCellLoadingReferenceCrossMoment cells referenceShare centeredA
          loadingB +
          (-scoreCellLoadingReferenceMean cells referenceShare loadingB) *
            scoreCellLoadingReferenceMean cells referenceShare centeredA := by
          rw [hmeanA]
          ring
    _ =
        scoreCellLoadingReferenceCrossMoment cells referenceShare centeredA
          (fun cell =>
            loadingB cell +
              (-scoreCellLoadingReferenceMean cells referenceShare loadingB)) := by
          exact hshift.symm
    _ =
        scoreCellLoadingReferenceCenteredCrossMoment
          cells referenceShare loadingA loadingB := by
          dsimp [centeredA]
          simpa [sub_eq_add_neg] using
            scoreCellLoadingReferenceCrossMoment_center_both_eq_centeredCrossMoment
              cells referenceShare loadingA loadingB

omit [DecidableEq Cell] in
/--
Under simplex reference shares, centering only the right loading gives the same
cross moment as centering both loadings.
-/
theorem scoreCellLoadingReferenceCrossMoment_center_right_eq_centeredCrossMoment
    (cells : Finset Cell) (referenceShare loadingA loadingB : Cell -> Real)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    scoreCellLoadingReferenceCrossMoment cells referenceShare loadingA
        (fun cell =>
          loadingB cell -
            scoreCellLoadingReferenceMean cells referenceShare loadingB) =
      scoreCellLoadingReferenceCenteredCrossMoment
        cells referenceShare loadingA loadingB := by
  rw [scoreCellLoadingReferenceCrossMoment_comm]
  rw [
    scoreCellLoadingReferenceCrossMoment_center_left_eq_centeredCrossMoment
      cells referenceShare loadingB loadingA hshare_sum]
  exact scoreCellLoadingReferenceCenteredCrossMoment_comm
    cells referenceShare loadingB loadingA

/--
Under simplex reference shares, the ordinary cross moment of both centered
loadings is the bilinear covariance-kernel form.
-/
theorem scoreCellLoadingReferenceCrossMoment_center_both_eq_bilinearCovarianceKernelForm
    (cells : Finset Cell) (referenceShare loadingA loadingB : Cell -> Real)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    scoreCellLoadingReferenceCrossMoment cells referenceShare
        (fun cell =>
          loadingA cell -
            scoreCellLoadingReferenceMean cells referenceShare loadingA)
        (fun cell =>
          loadingB cell -
            scoreCellLoadingReferenceMean cells referenceShare loadingB) =
      scoreCellBilinearCovarianceKernelForm
        cells referenceShare loadingA loadingB := by
  rw [scoreCellLoadingReferenceCrossMoment_center_both_eq_centeredCrossMoment]
  exact
    (scoreCellBilinearCovarianceKernelForm_eq_centeredCrossMoment
      cells referenceShare loadingA loadingB hshare_sum).symm

/--
Under simplex reference shares, the ordinary cross moment with only the left
loading centered is the bilinear covariance-kernel form.
-/
theorem scoreCellLoadingReferenceCrossMoment_center_left_eq_bilinearCovarianceKernelForm
    (cells : Finset Cell) (referenceShare loadingA loadingB : Cell -> Real)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    scoreCellLoadingReferenceCrossMoment cells referenceShare
        (fun cell =>
          loadingA cell -
            scoreCellLoadingReferenceMean cells referenceShare loadingA)
        loadingB =
      scoreCellBilinearCovarianceKernelForm
        cells referenceShare loadingA loadingB := by
  rw [
    scoreCellLoadingReferenceCrossMoment_center_left_eq_centeredCrossMoment
      cells referenceShare loadingA loadingB hshare_sum]
  exact
    (scoreCellBilinearCovarianceKernelForm_eq_centeredCrossMoment
      cells referenceShare loadingA loadingB hshare_sum).symm

/--
Under simplex reference shares, the ordinary cross moment with only the right
loading centered is the bilinear covariance-kernel form.
-/
theorem scoreCellLoadingReferenceCrossMoment_center_right_eq_bilinearCovarianceKernelForm
    (cells : Finset Cell) (referenceShare loadingA loadingB : Cell -> Real)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    scoreCellLoadingReferenceCrossMoment cells referenceShare loadingA
        (fun cell =>
          loadingB cell -
            scoreCellLoadingReferenceMean cells referenceShare loadingB) =
      scoreCellBilinearCovarianceKernelForm
        cells referenceShare loadingA loadingB := by
  rw [
    scoreCellLoadingReferenceCrossMoment_center_right_eq_centeredCrossMoment
      cells referenceShare loadingA loadingB hshare_sum]
  exact
    (scoreCellBilinearCovarianceKernelForm_eq_centeredCrossMoment
      cells referenceShare loadingA loadingB hshare_sum).symm

omit [DecidableEq Cell] in
/--
The ordinary cross moment of a loading centered against itself is the centered
second moment.
-/
theorem scoreCellLoadingReferenceCrossMoment_center_self_eq_centeredSecondMoment
    (cells : Finset Cell) (referenceShare loading : Cell -> Real) :
    scoreCellLoadingReferenceCrossMoment cells referenceShare
        (fun cell =>
          loading cell -
            scoreCellLoadingReferenceMean cells referenceShare loading)
        (fun cell =>
          loading cell -
            scoreCellLoadingReferenceMean cells referenceShare loading) =
      scoreCellLoadingReferenceCenteredSecondMoment
        cells referenceShare loading := by
  rw [scoreCellLoadingReferenceCrossMoment_center_both_eq_centeredCrossMoment]
  exact scoreCellLoadingReferenceCenteredCrossMoment_self_eq_centeredSecondMoment
    cells referenceShare loading

/--
Under simplex reference shares, the ordinary cross moment of a centered loading
with itself is the quadratic covariance-kernel form.
-/
theorem scoreCellLoadingReferenceCrossMoment_center_self_eq_linearCovarianceKernelForm
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    scoreCellLoadingReferenceCrossMoment cells referenceShare
        (fun cell =>
          loading cell -
            scoreCellLoadingReferenceMean cells referenceShare loading)
        (fun cell =>
          loading cell -
            scoreCellLoadingReferenceMean cells referenceShare loading) =
      scoreCellLinearCovarianceKernelForm cells referenceShare loading := by
  rw [scoreCellLoadingReferenceCrossMoment_center_self_eq_centeredSecondMoment]
  exact
    (scoreCellLinearCovarianceKernelForm_eq_centeredSecondMoment
      cells referenceShare loading hshare_sum).symm

end WDSM
end Matching
end StatInference
