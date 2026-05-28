import StatInference.Matching.WDSM.FiniteCellIndicatorCovarianceNonneg

/-!
# Bounds for finite score-cell covariance targets

Finite-dimensional CLT assumptions need not only the exact covariance target,
but also finite deterministic bounds on that target.  This module proves that
bounded finite loadings and simplex reference shares bound the centered
second-moment target by the square of the two-sided loading envelope.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Cell : Type*} [DecidableEq Cell]

omit [DecidableEq Cell] in
/-- A bounded loading has a bounded reference-share mean under simplex nonnegative shares. -/
theorem abs_scoreCellLoadingReferenceMean_le_loadingBound
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    (loadingBound : Real)
    (hshare_nonneg : ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hloading :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ loadingBound) :
    |scoreCellLoadingReferenceMean cells referenceShare loading| ≤
      loadingBound := by
  unfold scoreCellLoadingReferenceMean
  calc
    |∑ cell ∈ cells, referenceShare cell * loading cell| ≤
        ∑ cell ∈ cells, |referenceShare cell * loading cell| := by
          exact Finset.abs_sum_le_sum_abs _ _
    _ =
        ∑ cell ∈ cells, referenceShare cell * |loading cell| := by
          exact Finset.sum_congr rfl
            (fun cell hcell => by
              rw [abs_mul, abs_of_nonneg (hshare_nonneg cell hcell)])
    _ ≤ ∑ cell ∈ cells, referenceShare cell * loadingBound := by
          exact Finset.sum_le_sum
            (fun cell hcell =>
              mul_le_mul_of_nonneg_left (hloading cell hcell)
                (hshare_nonneg cell hcell))
    _ = loadingBound := by
          rw [← Finset.sum_mul, hshare_sum, one_mul]

omit [DecidableEq Cell] in
/-- A bounded loading differs from its reference-share mean by at most twice the bound. -/
theorem abs_loading_sub_scoreCellLoadingReferenceMean_le_two_loadingBound
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    (cell : Cell) (loadingBound : Real)
    (hcell : cell ∈ cells)
    (hshare_nonneg : ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hloading :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ loadingBound) :
    |loading cell -
        scoreCellLoadingReferenceMean cells referenceShare loading| ≤
      loadingBound * 2 := by
  have hmean :
      |scoreCellLoadingReferenceMean cells referenceShare loading| ≤
        loadingBound :=
    abs_scoreCellLoadingReferenceMean_le_loadingBound
      cells referenceShare loading loadingBound hshare_nonneg hshare_sum
      hloading
  have htri :
      |loading cell -
          scoreCellLoadingReferenceMean cells referenceShare loading| ≤
        |loading cell| +
          |scoreCellLoadingReferenceMean cells referenceShare loading| := by
    simpa [sub_eq_add_neg] using
      abs_add_le (loading cell)
        (-scoreCellLoadingReferenceMean cells referenceShare loading)
  have hsum :
      |loading cell| +
          |scoreCellLoadingReferenceMean cells referenceShare loading| ≤
        loadingBound + loadingBound :=
    add_le_add (hloading cell hcell) hmean
  linarith

omit [DecidableEq Cell] in
/--
The centered second-moment variance target is bounded by the square of the
two-sided loading envelope.
-/
theorem scoreCellLoadingReferenceCenteredSecondMoment_le_loadingBound_two_sq
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    (loadingBound : Real)
    (hloading_nonneg : 0 ≤ loadingBound)
    (hshare_nonneg : ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hloading :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ loadingBound) :
    scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare loading ≤
      (loadingBound * 2) ^ 2 := by
  unfold scoreCellLoadingReferenceCenteredSecondMoment
  calc
    (∑ cell ∈ cells,
        referenceShare cell *
          (loading cell -
            scoreCellLoadingReferenceMean cells referenceShare loading) ^ 2) ≤
        ∑ cell ∈ cells, referenceShare cell * (loadingBound * 2) ^ 2 := by
          exact Finset.sum_le_sum
            (fun cell hcell => by
              let centered :=
                loading cell -
                  scoreCellLoadingReferenceMean cells referenceShare loading
              have habs :
                  |centered| ≤ loadingBound * 2 := by
                dsimp [centered]
                exact
                  abs_loading_sub_scoreCellLoadingReferenceMean_le_two_loadingBound
                    cells referenceShare loading cell loadingBound
                    hcell hshare_nonneg hshare_sum hloading
              have hbound_nonneg : 0 ≤ loadingBound * 2 :=
                mul_nonneg hloading_nonneg (by norm_num)
              have hsquare : centered ^ 2 ≤ (loadingBound * 2) ^ 2 := by
                rw [← sq_abs centered]
                nlinarith [abs_nonneg centered]
              exact mul_le_mul_of_nonneg_left hsquare
                (hshare_nonneg cell hcell))
    _ = (loadingBound * 2) ^ 2 := by
          rw [← Finset.sum_mul, hshare_sum, one_mul]

/-- The covariance-kernel quadratic-form variance target has the same bound. -/
theorem scoreCellLinearCovarianceKernelForm_le_loadingBound_two_sq
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    (loadingBound : Real)
    (hloading_nonneg : 0 ≤ loadingBound)
    (hshare_nonneg : ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1)
    (hloading :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ loadingBound) :
    scoreCellLinearCovarianceKernelForm cells referenceShare loading ≤
      (loadingBound * 2) ^ 2 := by
  rw [scoreCellLinearCovarianceKernelForm_eq_centeredSecondMoment
    cells referenceShare loading hshare_sum]
  exact
    scoreCellLoadingReferenceCenteredSecondMoment_le_loadingBound_two_sq
      cells referenceShare loading loadingBound hloading_nonneg hshare_nonneg
      hshare_sum hloading

end WDSM
end Matching
end StatInference
