import StatInference.Matching.WDSM.FiniteCellIndicatorCovarianceCenteredBilinear

/-!
# Finite score-cell covariance matrix algebra

This module records matrix-level facts for the finite multinomial-style
score-cell covariance kernel.  The kernel action on a loading is
`p_a * (f_a - E_p f)`, and therefore rows and columns sum to zero on a finite
score-cell simplex.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Cell : Type*} [DecidableEq Cell]

/-- The score-cell covariance kernel is symmetric. -/
theorem scoreCellIndicatorCovarianceKernel_comm
    (referenceShare : Cell -> Real) (cellA cellB : Cell) :
    scoreCellIndicatorCovarianceKernel referenceShare cellA cellB =
      scoreCellIndicatorCovarianceKernel referenceShare cellB cellA := by
  by_cases h : cellA = cellB
  · subst cellB
    simp [scoreCellIndicatorCovarianceKernel]
  · have hsym : cellB ≠ cellA := fun hba => h hba.symm
    simp [scoreCellIndicatorCovarianceKernel, h, hsym]
    ring

/--
Pointwise row-action decomposition: one diagonal contribution minus the
outer-product reference-share mean contribution.
-/
theorem scoreCellIndicatorCovarianceKernel_mul_loading_eq_diag_sub_outer
    (referenceShare loading : Cell -> Real) (cellA cellB : Cell) :
    scoreCellIndicatorCovarianceKernel referenceShare cellA cellB *
        loading cellB =
      (if cellA = cellB then referenceShare cellA * loading cellA else 0) -
        referenceShare cellA * (referenceShare cellB * loading cellB) := by
  by_cases h : cellA = cellB
  · subst cellB
    simp [scoreCellIndicatorCovarianceKernel]
    ring
  · simp [scoreCellIndicatorCovarianceKernel, h]
    ring

/--
The row action of the covariance kernel on a finite loading is the reference
share times the centered loading.
-/
theorem sum_scoreCellIndicatorCovarianceKernel_mul_loading_eq_share_mul_centered
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    (cellA : Cell) (hmem : cellA ∈ cells) :
    (∑ cellB ∈ cells,
        scoreCellIndicatorCovarianceKernel referenceShare cellA cellB *
          loading cellB) =
      referenceShare cellA *
        (loading cellA -
          scoreCellLoadingReferenceMean cells referenceShare loading) := by
  calc
    (∑ cellB ∈ cells,
        scoreCellIndicatorCovarianceKernel referenceShare cellA cellB *
          loading cellB) =
        ∑ cellB ∈ cells,
          ((if cellA = cellB then referenceShare cellA * loading cellA else 0) -
            referenceShare cellA *
              (referenceShare cellB * loading cellB)) := by
          exact Finset.sum_congr rfl
            (fun cellB _hcellB => by
              rw [scoreCellIndicatorCovarianceKernel_mul_loading_eq_diag_sub_outer])
    _ =
        (∑ cellB ∈ cells,
          if cellA = cellB then referenceShare cellA * loading cellA else 0) -
          (∑ cellB ∈ cells,
            referenceShare cellA *
              (referenceShare cellB * loading cellB)) := by
          rw [Finset.sum_sub_distrib]
    _ =
        referenceShare cellA * loading cellA -
          referenceShare cellA *
            (∑ cellB ∈ cells, referenceShare cellB * loading cellB) := by
          let diagonal : Cell -> Real := fun cellB =>
            if cellA = cellB then referenceShare cellA * loading cellA else 0
          have hdiag :
              (∑ cellB ∈ cells, diagonal cellB) =
                diagonal cellA := by
            apply Finset.sum_eq_single cellA
            · intro cellB _hcellB hne
              have hne' : cellA ≠ cellB := fun h => hne h.symm
              simp [diagonal, hne']
            · intro hnot_mem
              exact False.elim (hnot_mem hmem)
          rw [← Finset.mul_sum]
          simpa [diagonal]
            using congrArg
              (fun value =>
                value -
                  referenceShare cellA *
                    (∑ cellB ∈ cells,
                      referenceShare cellB * loading cellB))
              hdiag
    _ =
        referenceShare cellA *
          (loading cellA -
            scoreCellLoadingReferenceMean cells referenceShare loading) := by
          unfold scoreCellLoadingReferenceMean
          ring

/-- Every covariance-kernel row sums to zero on a finite simplex. -/
theorem sum_scoreCellIndicatorCovarianceKernel_right_eq_zero_of_mem
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    (cellA : Cell) (hmem : cellA ∈ cells)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    (∑ cellB ∈ cells,
        scoreCellIndicatorCovarianceKernel referenceShare cellA cellB) =
      0 := by
  have hrow :=
    sum_scoreCellIndicatorCovarianceKernel_mul_loading_eq_share_mul_centered
      cells referenceShare (fun _cell => (1 : Real)) cellA hmem
  rw [scoreCellLoadingReferenceMean_const cells referenceShare (1 : Real)
    hshare_sum] at hrow
  simpa using hrow

/-- Every covariance-kernel column sums to zero on a finite simplex. -/
theorem sum_scoreCellIndicatorCovarianceKernel_left_eq_zero_of_mem
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    (cellB : Cell) (hmem : cellB ∈ cells)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    (∑ cellA ∈ cells,
        scoreCellIndicatorCovarianceKernel referenceShare cellA cellB) =
      0 := by
  calc
    (∑ cellA ∈ cells,
        scoreCellIndicatorCovarianceKernel referenceShare cellA cellB) =
        ∑ cellA ∈ cells,
          scoreCellIndicatorCovarianceKernel referenceShare cellB cellA := by
          exact Finset.sum_congr rfl
            (fun cellA _hcellA => by
              rw [scoreCellIndicatorCovarianceKernel_comm])
    _ = 0 :=
        sum_scoreCellIndicatorCovarianceKernel_right_eq_zero_of_mem
          cells referenceShare cellB hmem hshare_sum

/-- The total finite covariance-kernel sum is zero on a finite simplex. -/
theorem sum_scoreCellIndicatorCovarianceKernel_all_eq_zero
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    (∑ cellA ∈ cells, ∑ cellB ∈ cells,
        scoreCellIndicatorCovarianceKernel referenceShare cellA cellB) =
      0 := by
  exact Finset.sum_eq_zero
    (fun cellA hcellA =>
      sum_scoreCellIndicatorCovarianceKernel_right_eq_zero_of_mem
        cells referenceShare cellA hcellA hshare_sum)

end WDSM
end Matching
end StatInference
