import StatInference.Matching.WDSM.FiniteCellIndicatorCovarianceBounds
import StatInference.Matching.WDSM.FiniteCellIndicatorCovarianceCenteredBilinear

/-!
# Bounds for bilinear finite score-cell covariance targets

Target 350 bounded diagonal finite covariance targets.  This module proves the
corresponding absolute bound for bilinear covariance entries induced by two
bounded finite loadings.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Cell : Type*} [DecidableEq Cell]

omit [DecidableEq Cell] in
/--
The reference-share centered cross moment of two bounded finite loadings is
bounded by the product of their two-sided loading envelopes.
-/
theorem
    abs_scoreCellLoadingReferenceCenteredCrossMoment_le_loadingBound_two_mul_loadingBound_two
    (cells : Finset Cell) (referenceShare loadingA loadingB : Cell -> Real)
    (loadingBoundA loadingBoundB : Real)
    (hloadingA_nonneg : 0 ≤ loadingBoundA)
    (hloadingB_nonneg : 0 ≤ loadingBoundB)
    (hshare_nonneg : ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hloadingA :
      ∀ cell, cell ∈ cells -> |loadingA cell| ≤ loadingBoundA)
    (hloadingB :
      ∀ cell, cell ∈ cells -> |loadingB cell| ≤ loadingBoundB) :
    |scoreCellLoadingReferenceCenteredCrossMoment
        cells referenceShare loadingA loadingB| ≤
      (loadingBoundA * 2) * (loadingBoundB * 2) := by
  let boundA := loadingBoundA * 2
  let boundB := loadingBoundB * 2
  have hboundA_nonneg : 0 ≤ boundA := by
    dsimp [boundA]
    exact mul_nonneg hloadingA_nonneg (by norm_num)
  have hboundB_nonneg : 0 ≤ boundB := by
    dsimp [boundB]
    exact mul_nonneg hloadingB_nonneg (by norm_num)
  unfold scoreCellLoadingReferenceCenteredCrossMoment
  calc
    |∑ cell ∈ cells,
        referenceShare cell *
          (loadingA cell -
            scoreCellLoadingReferenceMean cells referenceShare loadingA) *
          (loadingB cell -
            scoreCellLoadingReferenceMean cells referenceShare loadingB)| ≤
        ∑ cell ∈ cells,
          |referenceShare cell *
            (loadingA cell -
              scoreCellLoadingReferenceMean cells referenceShare loadingA) *
            (loadingB cell -
              scoreCellLoadingReferenceMean cells referenceShare loadingB)| := by
          exact Finset.abs_sum_le_sum_abs _ _
    _ =
        ∑ cell ∈ cells,
          referenceShare cell *
            |loadingA cell -
              scoreCellLoadingReferenceMean cells referenceShare loadingA| *
            |loadingB cell -
              scoreCellLoadingReferenceMean cells referenceShare loadingB| := by
          exact Finset.sum_congr rfl
            (fun cell hcell => by
              rw [abs_mul, abs_mul,
                abs_of_nonneg (hshare_nonneg cell hcell)])
    _ ≤
        ∑ cell ∈ cells,
          referenceShare cell * boundA * boundB := by
          exact Finset.sum_le_sum
            (fun cell hcell => by
              let centeredA :=
                loadingA cell -
                  scoreCellLoadingReferenceMean cells referenceShare loadingA
              let centeredB :=
                loadingB cell -
                  scoreCellLoadingReferenceMean cells referenceShare loadingB
              have hA :
                  |centeredA| ≤ boundA := by
                dsimp [centeredA, boundA]
                exact
                  abs_loading_sub_scoreCellLoadingReferenceMean_le_two_loadingBound
                    cells referenceShare loadingA cell loadingBoundA hcell
                    hshare_nonneg hshare_sum hloadingA
              have hB :
                  |centeredB| ≤ boundB := by
                dsimp [centeredB, boundB]
                exact
                  abs_loading_sub_scoreCellLoadingReferenceMean_le_two_loadingBound
                    cells referenceShare loadingB cell loadingBoundB hcell
                    hshare_nonneg hshare_sum hloadingB
              have hleft :
                  referenceShare cell * |centeredA| ≤
                    referenceShare cell * boundA :=
                mul_le_mul_of_nonneg_left hA
                  (hshare_nonneg cell hcell)
              have hleft_mul :
                  referenceShare cell * |centeredA| * |centeredB| ≤
                    referenceShare cell * boundA * |centeredB| :=
                mul_le_mul_of_nonneg_right hleft (abs_nonneg centeredB)
              have hcoef_nonneg :
                  0 ≤ referenceShare cell * boundA :=
                mul_nonneg (hshare_nonneg cell hcell) hboundA_nonneg
              have hright :
                  referenceShare cell * boundA * |centeredB| ≤
                    referenceShare cell * boundA * boundB :=
                mul_le_mul_of_nonneg_left hB hcoef_nonneg
              exact hleft_mul.trans hright)
    _ = (loadingBoundA * 2) * (loadingBoundB * 2) := by
          calc
            (∑ cell ∈ cells, referenceShare cell * boundA * boundB) =
                ∑ cell ∈ cells, referenceShare cell * (boundA * boundB) := by
                  exact Finset.sum_congr rfl
                    (fun cell _hcell => by ring)
            _ = boundA * boundB := by
                  rw [← Finset.sum_mul, hshare_sum, one_mul]
            _ = (loadingBoundA * 2) * (loadingBoundB * 2) := by
                  rfl

/--
The bilinear covariance-kernel target has the same absolute bound under
simplex reference shares.
-/
theorem
    abs_scoreCellBilinearCovarianceKernelForm_le_loadingBound_two_mul_loadingBound_two
    (cells : Finset Cell) (referenceShare loadingA loadingB : Cell -> Real)
    (loadingBoundA loadingBoundB : Real)
    (hloadingA_nonneg : 0 ≤ loadingBoundA)
    (hloadingB_nonneg : 0 ≤ loadingBoundB)
    (hshare_nonneg : ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hloadingA :
      ∀ cell, cell ∈ cells -> |loadingA cell| ≤ loadingBoundA)
    (hloadingB :
      ∀ cell, cell ∈ cells -> |loadingB cell| ≤ loadingBoundB) :
    |scoreCellBilinearCovarianceKernelForm
        cells referenceShare loadingA loadingB| ≤
      (loadingBoundA * 2) * (loadingBoundB * 2) := by
  rw [scoreCellBilinearCovarianceKernelForm_eq_centeredCrossMoment
    cells referenceShare loadingA loadingB hshare_sum]
  exact
    abs_scoreCellLoadingReferenceCenteredCrossMoment_le_loadingBound_two_mul_loadingBound_two
      cells referenceShare loadingA loadingB loadingBoundA loadingBoundB
      hloadingA_nonneg hloadingB_nonneg hshare_nonneg hshare_sum hloadingA
      hloadingB

end WDSM
end Matching
end StatInference
