import StatInference.Matching.WDSM.FiniteCellIndicatorSimplexBounds

/-!
# Entrywise bounds for finite score-cell covariance kernels

The finite score-cell covariance kernel has entries
`p_a * (1 - p_a)` on the diagonal and `-p_a * p_b` off the diagonal.  Under
simplex nonnegative reference shares, every entry has absolute value at most
one.  This gives a reusable finite matrix envelope for later score-cell CLT
interfaces.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Cell : Type*} [DecidableEq Cell]

/-- A diagonal covariance-kernel entry is nonnegative under simplex shares. -/
theorem scoreCellIndicatorCovarianceKernel_self_nonneg_of_mem_of_nonneg_sum_one
    (cells : Finset Cell) (referenceShare : Cell -> Real) (cell : Cell)
    (hcell : cell ∈ cells)
    (hshare_nonneg : ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    0 ≤ scoreCellIndicatorCovarianceKernel referenceShare cell cell := by
  have hshare_cell_nonneg : 0 ≤ referenceShare cell :=
    hshare_nonneg cell hcell
  have hshare_cell_le_one : referenceShare cell ≤ 1 :=
    referenceShare_le_one_of_mem_of_nonneg_sum_one
      cells referenceShare cell hcell hshare_nonneg hshare_sum
  simp [scoreCellIndicatorCovarianceKernel,
    mul_nonneg hshare_cell_nonneg (sub_nonneg.mpr hshare_cell_le_one)]

/-- A diagonal covariance-kernel entry is bounded by one in absolute value. -/
theorem abs_scoreCellIndicatorCovarianceKernel_self_le_one_of_mem_of_nonneg_sum_one
    (cells : Finset Cell) (referenceShare : Cell -> Real) (cell : Cell)
    (hcell : cell ∈ cells)
    (hshare_nonneg : ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    |scoreCellIndicatorCovarianceKernel referenceShare cell cell| ≤ 1 := by
  have hshare_cell_nonneg : 0 ≤ referenceShare cell :=
    hshare_nonneg cell hcell
  have hshare_cell_le_one : referenceShare cell ≤ 1 :=
    referenceShare_le_one_of_mem_of_nonneg_sum_one
      cells referenceShare cell hcell hshare_nonneg hshare_sum
  have hcomp_nonneg : 0 ≤ 1 - referenceShare cell :=
    sub_nonneg.mpr hshare_cell_le_one
  have hcomp_le_one : 1 - referenceShare cell ≤ 1 := by
    linarith
  have hprod_nonneg :
      0 ≤ referenceShare cell * (1 - referenceShare cell) :=
    mul_nonneg hshare_cell_nonneg hcomp_nonneg
  have hprod_le_one :
      referenceShare cell * (1 - referenceShare cell) ≤ 1 := by
    have hmul :
        referenceShare cell * (1 - referenceShare cell) ≤ (1 : Real) * 1 :=
      mul_le_mul hshare_cell_le_one hcomp_le_one hcomp_nonneg zero_le_one
    simpa using hmul
  simpa [scoreCellIndicatorCovarianceKernel, abs_of_nonneg hprod_nonneg]
    using hprod_le_one

/-- An off-diagonal covariance-kernel entry is bounded by one in absolute value. -/
theorem abs_scoreCellIndicatorCovarianceKernel_of_ne_le_one_of_mem_of_nonneg_sum_one
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    (cellA cellB : Cell) (hne : cellA ≠ cellB)
    (hcellA : cellA ∈ cells) (hcellB : cellB ∈ cells)
    (hshare_nonneg : ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    |scoreCellIndicatorCovarianceKernel referenceShare cellA cellB| ≤ 1 := by
  have hshareA_nonneg : 0 ≤ referenceShare cellA :=
    hshare_nonneg cellA hcellA
  have hshareB_nonneg : 0 ≤ referenceShare cellB :=
    hshare_nonneg cellB hcellB
  have hshareA_le_one : referenceShare cellA ≤ 1 :=
    referenceShare_le_one_of_mem_of_nonneg_sum_one
      cells referenceShare cellA hcellA hshare_nonneg hshare_sum
  have hshareB_le_one : referenceShare cellB ≤ 1 :=
    referenceShare_le_one_of_mem_of_nonneg_sum_one
      cells referenceShare cellB hcellB hshare_nonneg hshare_sum
  have hprod_le_one : referenceShare cellA * referenceShare cellB ≤ 1 := by
    have hmul :
        referenceShare cellA * referenceShare cellB ≤ (1 : Real) * 1 :=
      mul_le_mul hshareA_le_one hshareB_le_one hshareB_nonneg zero_le_one
    simpa using hmul
  simpa [scoreCellIndicatorCovarianceKernel, hne, abs_mul,
    abs_of_nonneg hshareA_nonneg, abs_of_nonneg hshareB_nonneg]
    using hprod_le_one

/-- Every covariance-kernel entry over a finite simplex is bounded by one. -/
theorem abs_scoreCellIndicatorCovarianceKernel_le_one_of_mem_of_nonneg_sum_one
    (cells : Finset Cell) (referenceShare : Cell -> Real)
    (cellA cellB : Cell)
    (hcellA : cellA ∈ cells) (hcellB : cellB ∈ cells)
    (hshare_nonneg : ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    |scoreCellIndicatorCovarianceKernel referenceShare cellA cellB| ≤ 1 := by
  by_cases h : cellA = cellB
  · subst cellB
    exact
      abs_scoreCellIndicatorCovarianceKernel_self_le_one_of_mem_of_nonneg_sum_one
        cells referenceShare cellA hcellA hshare_nonneg hshare_sum
  · exact
      abs_scoreCellIndicatorCovarianceKernel_of_ne_le_one_of_mem_of_nonneg_sum_one
        cells referenceShare cellA cellB h hcellA hcellB hshare_nonneg
        hshare_sum

/-- A finite covariance-kernel row has `L1` norm bounded by the number of cells. -/
theorem sum_abs_scoreCellIndicatorCovarianceKernel_le_card_of_mem_of_nonneg_sum_one
    (cells : Finset Cell) (referenceShare : Cell -> Real) (cellA : Cell)
    (hcellA : cellA ∈ cells)
    (hshare_nonneg : ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    (∑ cellB ∈ cells,
        |scoreCellIndicatorCovarianceKernel referenceShare cellA cellB|) ≤
      (cells.card : Real) := by
  calc
    (∑ cellB ∈ cells,
        |scoreCellIndicatorCovarianceKernel referenceShare cellA cellB|) ≤
        ∑ _cellB ∈ cells, (1 : Real) := by
          exact Finset.sum_le_sum
            (fun cellB hcellB =>
              abs_scoreCellIndicatorCovarianceKernel_le_one_of_mem_of_nonneg_sum_one
                cells referenceShare cellA cellB hcellA hcellB
                hshare_nonneg hshare_sum)
    _ = (cells.card : Real) := by
          simp

end WDSM
end Matching
end StatInference
