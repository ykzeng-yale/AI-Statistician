import StatInference.Matching.WDSM.FiniteCellIndicatorLinearCovariance

/-!
# Closed-form quadratic forms for finite score-cell indicator covariances

This module reduces the finite score-cell covariance-kernel quadratic form to
the familiar scalar expression `second moment - mean^2` for any finite loading.
It is the deterministic variance-target simplification needed before invoking
finite-dimensional weighted indicator CLTs.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit Cell : Type*} [DecidableEq Cell]

/-- Reference-share mean of a finite cell loading. -/
noncomputable def scoreCellLoadingReferenceMean
    (cells : Finset Cell) (referenceShare loading : Cell -> Real) : Real :=
  ∑ cell ∈ cells, referenceShare cell * loading cell

/-- Reference-share second moment of a finite cell loading. -/
noncomputable def scoreCellLoadingReferenceSecondMoment
    (cells : Finset Cell) (referenceShare loading : Cell -> Real) : Real :=
  ∑ cell ∈ cells, referenceShare cell * loading cell ^ 2

/--
Pointwise loading version of the covariance kernel: diagonal second-moment
contribution minus the outer-product mean contribution.
-/
theorem scoreCellIndicatorCovarianceKernel_loading_mul_eq_diag_sub_outer
    (referenceShare loading : Cell -> Real) (cellA cellB : Cell) :
    loading cellA * loading cellB *
        scoreCellIndicatorCovarianceKernel referenceShare cellA cellB =
      (if cellA = cellB then referenceShare cellA * loading cellA ^ 2 else 0) -
        (referenceShare cellA * loading cellA) *
          (referenceShare cellB * loading cellB) := by
  by_cases h : cellA = cellB
  · subst cellB
    simp [scoreCellIndicatorCovarianceKernel]
    ring
  · simp [scoreCellIndicatorCovarianceKernel, h]
    ring

omit [DecidableEq Cell] in
/-- The squared reference-share mean is the corresponding finite double sum. -/
theorem scoreCellLoadingReferenceMean_sq_eq_double_sum
    (cells : Finset Cell) (referenceShare loading : Cell -> Real) :
    scoreCellLoadingReferenceMean cells referenceShare loading ^ 2 =
      ∑ cellA ∈ cells, ∑ cellB ∈ cells,
        (referenceShare cellA * loading cellA) *
          (referenceShare cellB * loading cellB) := by
  unfold scoreCellLoadingReferenceMean
  calc
    (∑ cellA ∈ cells, referenceShare cellA * loading cellA) ^ 2 =
        (∑ cellA ∈ cells, referenceShare cellA * loading cellA) *
          (∑ cellB ∈ cells, referenceShare cellB * loading cellB) := by
          ring
    _ =
        ∑ cellA ∈ cells,
          (referenceShare cellA * loading cellA) *
            (∑ cellB ∈ cells, referenceShare cellB * loading cellB) := by
          rw [Finset.sum_mul]
    _ =
        ∑ cellA ∈ cells, ∑ cellB ∈ cells,
          (referenceShare cellA * loading cellA) *
            (referenceShare cellB * loading cellB) := by
          exact Finset.sum_congr rfl
            (fun cellA _hcellA => by
              rw [Finset.mul_sum])

/--
The finite second moment is the diagonal part of the covariance-kernel double
sum.
-/
theorem scoreCellLoadingReferenceSecondMoment_eq_double_diag_sum
    (cells : Finset Cell) (referenceShare loading : Cell -> Real) :
    scoreCellLoadingReferenceSecondMoment cells referenceShare loading =
      ∑ cellA ∈ cells, ∑ cellB ∈ cells,
        if cellA = cellB then referenceShare cellA * loading cellA ^ 2 else 0 := by
  unfold scoreCellLoadingReferenceSecondMoment
  exact Finset.sum_congr rfl
    (fun cellA hcellA => by
      let summand : Cell -> Real := fun cellB =>
        if cellA = cellB then
          referenceShare cellA * loading cellA ^ 2
        else 0
      have hsingle :
          (∑ cellB ∈ cells, summand cellB) = summand cellA := by
        apply Finset.sum_eq_single cellA
        · intro cellB _hcellB hne
          have hne' : cellA ≠ cellB := fun h => hne h.symm
          simp [summand, hne']
        · intro hnot_mem
          exact False.elim (hnot_mem hcellA)
      simpa [summand] using hsingle.symm)

/--
Closed-form finite quadratic form for score-cell indicator covariances:
`loading^T K loading = E_p[loading^2] - E_p[loading]^2`.
-/
theorem scoreCellLinearCovarianceKernelForm_eq_secondMoment_sub_mean_sq
    (cells : Finset Cell) (referenceShare loading : Cell -> Real) :
    scoreCellLinearCovarianceKernelForm cells referenceShare loading =
      scoreCellLoadingReferenceSecondMoment cells referenceShare loading -
        scoreCellLoadingReferenceMean cells referenceShare loading ^ 2 := by
  calc
    scoreCellLinearCovarianceKernelForm cells referenceShare loading =
        ∑ cellA ∈ cells, ∑ cellB ∈ cells,
          ((if cellA = cellB then
                referenceShare cellA * loading cellA ^ 2
              else 0) -
              (referenceShare cellA * loading cellA) *
                (referenceShare cellB * loading cellB)) := by
          unfold scoreCellLinearCovarianceKernelForm
          exact Finset.sum_congr rfl
            (fun cellA _hcellA =>
              Finset.sum_congr rfl
                (fun cellB _hcellB => by
                  rw [
                    scoreCellIndicatorCovarianceKernel_loading_mul_eq_diag_sub_outer]))
    _ =
        (∑ cellA ∈ cells, ∑ cellB ∈ cells,
          if cellA = cellB then
            referenceShare cellA * loading cellA ^ 2
          else 0) -
        (∑ cellA ∈ cells, ∑ cellB ∈ cells,
          (referenceShare cellA * loading cellA) *
            (referenceShare cellB * loading cellB)) := by
          calc
            (∑ cellA ∈ cells, ∑ cellB ∈ cells,
              ((if cellA = cellB then
                    referenceShare cellA * loading cellA ^ 2
                  else 0) -
                  (referenceShare cellA * loading cellA) *
                    (referenceShare cellB * loading cellB))) =
                ∑ cellA ∈ cells,
                  ((∑ cellB ∈ cells,
                    if cellA = cellB then
                      referenceShare cellA * loading cellA ^ 2
                    else 0) -
                    (∑ cellB ∈ cells,
                      (referenceShare cellA * loading cellA) *
                        (referenceShare cellB * loading cellB))) := by
                  exact Finset.sum_congr rfl
                    (fun cellA _hcellA => by
                      rw [Finset.sum_sub_distrib])
            _ =
                (∑ cellA ∈ cells, ∑ cellB ∈ cells,
                  if cellA = cellB then
                    referenceShare cellA * loading cellA ^ 2
                  else 0) -
                (∑ cellA ∈ cells, ∑ cellB ∈ cells,
                  (referenceShare cellA * loading cellA) *
                    (referenceShare cellB * loading cellB)) := by
                  rw [Finset.sum_sub_distrib]
    _ =
        scoreCellLoadingReferenceSecondMoment cells referenceShare loading -
          scoreCellLoadingReferenceMean cells referenceShare loading ^ 2 := by
          rw [← scoreCellLoadingReferenceSecondMoment_eq_double_diag_sum]
          rw [scoreCellLoadingReferenceMean_sq_eq_double_sum]

/--
If the loading has zero reference-share mean over the finite cells, the
covariance-kernel form reduces to the reference-share second moment.
-/
theorem scoreCellLinearCovarianceKernelForm_eq_secondMoment_of_mean_zero
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    (hmean : scoreCellLoadingReferenceMean cells referenceShare loading = 0) :
    scoreCellLinearCovarianceKernelForm cells referenceShare loading =
      scoreCellLoadingReferenceSecondMoment cells referenceShare loading := by
  rw [scoreCellLinearCovarianceKernelForm_eq_secondMoment_sub_mean_sq]
  rw [hmean]
  ring

/--
Normalized finite linear centered-indicator variances equal the closed-form
`second moment - mean^2` target under exact reference-share cell masses.
-/
theorem
    weightedSampleSum_scoreCellLinearCenteredIndicator_sq_div_total_eq_secondMoment_sub_mean_sq
    (sample : Finset Unit) (weight : Unit -> Real)
    (cells : Finset Cell) (score : Unit -> Cell)
    (referenceShare loading : Cell -> Real)
    (htotal : weightedSampleTotal sample weight ≠ 0)
    (hmass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sample weight score cell =
          referenceShare cell * weightedSampleTotal sample weight) :
    weightedSampleSum sample weight
        (fun unit =>
          scoreCellLinearCenteredIndicator cells score referenceShare loading unit *
            scoreCellLinearCenteredIndicator cells score referenceShare loading
              unit) /
        weightedSampleTotal sample weight =
      scoreCellLoadingReferenceSecondMoment cells referenceShare loading -
        scoreCellLoadingReferenceMean cells referenceShare loading ^ 2 := by
  rw [
    weightedSampleSum_scoreCellLinearCenteredIndicator_sq_div_total_eq_kernelForm
      sample weight cells score referenceShare loading htotal hmass]
  rw [scoreCellLinearCovarianceKernelForm_eq_secondMoment_sub_mean_sq]

end WDSM
end Matching
end StatInference
