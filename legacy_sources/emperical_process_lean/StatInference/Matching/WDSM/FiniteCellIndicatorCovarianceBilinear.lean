import StatInference.Matching.WDSM.FiniteCellIndicatorCovarianceDegeneracy

/-!
# Bilinear finite score-cell covariance algebra

The previous modules proved variance identities for one finite loading.  This
module proves the corresponding covariance identity for two loadings:
`loadingA^T K loadingB = E_p[loadingA * loadingB] - E_p[loadingA] E_p[loadingB]`.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit Cell : Type*} [DecidableEq Cell]

/-- Reference-share cross moment of two finite cell loadings. -/
noncomputable def scoreCellLoadingReferenceCrossMoment
    (cells : Finset Cell) (referenceShare loadingA loadingB : Cell -> Real) :
    Real :=
  ∑ cell ∈ cells, referenceShare cell * loadingA cell * loadingB cell

/-- Bilinear covariance-kernel form for two finite cell loadings. -/
noncomputable def scoreCellBilinearCovarianceKernelForm
    (cells : Finset Cell) (referenceShare loadingA loadingB : Cell -> Real) :
    Real :=
  ∑ cellA ∈ cells, ∑ cellB ∈ cells,
    loadingA cellA * loadingB cellB *
      scoreCellIndicatorCovarianceKernel referenceShare cellA cellB

/--
Pointwise bilinear version of the covariance kernel: a diagonal cross-moment
contribution minus the outer product of the two reference-share means.
-/
theorem scoreCellIndicatorCovarianceKernel_bilinear_mul_eq_diag_sub_outer
    (referenceShare loadingA loadingB : Cell -> Real) (cellA cellB : Cell) :
    loadingA cellA * loadingB cellB *
        scoreCellIndicatorCovarianceKernel referenceShare cellA cellB =
      (if cellA = cellB then
          referenceShare cellA * loadingA cellA * loadingB cellA
        else 0) -
        (referenceShare cellA * loadingA cellA) *
          (referenceShare cellB * loadingB cellB) := by
  by_cases h : cellA = cellB
  · subst cellB
    simp [scoreCellIndicatorCovarianceKernel]
    ring
  · simp [scoreCellIndicatorCovarianceKernel, h]
    ring

omit [DecidableEq Cell] in
/-- Product of two reference-share means as a finite double sum. -/
theorem scoreCellLoadingReferenceMean_mul_mean_eq_double_sum
    (cells : Finset Cell) (referenceShare loadingA loadingB : Cell -> Real) :
    scoreCellLoadingReferenceMean cells referenceShare loadingA *
        scoreCellLoadingReferenceMean cells referenceShare loadingB =
      ∑ cellA ∈ cells, ∑ cellB ∈ cells,
        (referenceShare cellA * loadingA cellA) *
          (referenceShare cellB * loadingB cellB) := by
  unfold scoreCellLoadingReferenceMean
  calc
    (∑ cellA ∈ cells, referenceShare cellA * loadingA cellA) *
        (∑ cellB ∈ cells, referenceShare cellB * loadingB cellB) =
        ∑ cellA ∈ cells,
          (referenceShare cellA * loadingA cellA) *
            (∑ cellB ∈ cells, referenceShare cellB * loadingB cellB) := by
          rw [Finset.sum_mul]
    _ =
        ∑ cellA ∈ cells, ∑ cellB ∈ cells,
          (referenceShare cellA * loadingA cellA) *
            (referenceShare cellB * loadingB cellB) := by
          exact Finset.sum_congr rfl
            (fun cellA _hcellA => by
              rw [Finset.mul_sum])

/-- The finite cross moment is the diagonal part of the bilinear double sum. -/
theorem scoreCellLoadingReferenceCrossMoment_eq_double_diag_sum
    (cells : Finset Cell) (referenceShare loadingA loadingB : Cell -> Real) :
    scoreCellLoadingReferenceCrossMoment cells referenceShare loadingA loadingB =
      ∑ cellA ∈ cells, ∑ cellB ∈ cells,
        if cellA = cellB then
          referenceShare cellA * loadingA cellA * loadingB cellA
        else 0 := by
  unfold scoreCellLoadingReferenceCrossMoment
  exact Finset.sum_congr rfl
    (fun cellA hcellA => by
      let summand : Cell -> Real := fun cellB =>
        if cellA = cellB then
          referenceShare cellA * loadingA cellA * loadingB cellA
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
Closed-form bilinear covariance-kernel identity:
`loadingA^T K loadingB = E_p[loadingA * loadingB] -
E_p[loadingA] E_p[loadingB]`.
-/
theorem scoreCellBilinearCovarianceKernelForm_eq_crossMoment_sub_mean_mul_mean
    (cells : Finset Cell) (referenceShare loadingA loadingB : Cell -> Real) :
    scoreCellBilinearCovarianceKernelForm
        cells referenceShare loadingA loadingB =
      scoreCellLoadingReferenceCrossMoment
          cells referenceShare loadingA loadingB -
        scoreCellLoadingReferenceMean cells referenceShare loadingA *
          scoreCellLoadingReferenceMean cells referenceShare loadingB := by
  calc
    scoreCellBilinearCovarianceKernelForm
        cells referenceShare loadingA loadingB =
        ∑ cellA ∈ cells, ∑ cellB ∈ cells,
          ((if cellA = cellB then
              referenceShare cellA * loadingA cellA * loadingB cellA
            else 0) -
            (referenceShare cellA * loadingA cellA) *
              (referenceShare cellB * loadingB cellB)) := by
          unfold scoreCellBilinearCovarianceKernelForm
          exact Finset.sum_congr rfl
            (fun cellA _hcellA =>
              Finset.sum_congr rfl
                (fun cellB _hcellB => by
                  rw [
                    scoreCellIndicatorCovarianceKernel_bilinear_mul_eq_diag_sub_outer]))
    _ =
        (∑ cellA ∈ cells, ∑ cellB ∈ cells,
          if cellA = cellB then
            referenceShare cellA * loadingA cellA * loadingB cellA
          else 0) -
        (∑ cellA ∈ cells, ∑ cellB ∈ cells,
          (referenceShare cellA * loadingA cellA) *
            (referenceShare cellB * loadingB cellB)) := by
          calc
            (∑ cellA ∈ cells, ∑ cellB ∈ cells,
              ((if cellA = cellB then
                  referenceShare cellA * loadingA cellA * loadingB cellA
                else 0) -
                (referenceShare cellA * loadingA cellA) *
                  (referenceShare cellB * loadingB cellB))) =
                ∑ cellA ∈ cells,
                  ((∑ cellB ∈ cells,
                    if cellA = cellB then
                      referenceShare cellA * loadingA cellA * loadingB cellA
                    else 0) -
                    (∑ cellB ∈ cells,
                      (referenceShare cellA * loadingA cellA) *
                        (referenceShare cellB * loadingB cellB))) := by
                  exact Finset.sum_congr rfl
                    (fun cellA _hcellA => by
                      rw [Finset.sum_sub_distrib])
            _ =
                (∑ cellA ∈ cells, ∑ cellB ∈ cells,
                  if cellA = cellB then
                    referenceShare cellA * loadingA cellA * loadingB cellA
                  else 0) -
                (∑ cellA ∈ cells, ∑ cellB ∈ cells,
                  (referenceShare cellA * loadingA cellA) *
                    (referenceShare cellB * loadingB cellB)) := by
                  rw [Finset.sum_sub_distrib]
    _ =
        scoreCellLoadingReferenceCrossMoment
            cells referenceShare loadingA loadingB -
          scoreCellLoadingReferenceMean cells referenceShare loadingA *
            scoreCellLoadingReferenceMean cells referenceShare loadingB := by
          rw [← scoreCellLoadingReferenceCrossMoment_eq_double_diag_sum]
          rw [scoreCellLoadingReferenceMean_mul_mean_eq_double_sum]

/-- The bilinear covariance-kernel form agrees with the quadratic form on the diagonal. -/
theorem scoreCellBilinearCovarianceKernelForm_self_eq_linear
    (cells : Finset Cell) (referenceShare loading : Cell -> Real) :
    scoreCellBilinearCovarianceKernelForm cells referenceShare loading loading =
      scoreCellLinearCovarianceKernelForm cells referenceShare loading := by
  unfold scoreCellBilinearCovarianceKernelForm
  unfold scoreCellLinearCovarianceKernelForm
  exact Finset.sum_congr rfl
    (fun cellA _hcellA =>
      Finset.sum_congr rfl
        (fun cellB _hcellB => by ring))

omit [DecidableEq Cell] in
/-- Reference-share cross moments are symmetric in the two loadings. -/
theorem scoreCellLoadingReferenceCrossMoment_comm
    (cells : Finset Cell) (referenceShare loadingA loadingB : Cell -> Real) :
    scoreCellLoadingReferenceCrossMoment cells referenceShare loadingA loadingB =
      scoreCellLoadingReferenceCrossMoment
        cells referenceShare loadingB loadingA := by
  unfold scoreCellLoadingReferenceCrossMoment
  exact Finset.sum_congr rfl
    (fun cell _hcell => by ring)

/-- The bilinear covariance-kernel form is symmetric. -/
theorem scoreCellBilinearCovarianceKernelForm_comm
    (cells : Finset Cell) (referenceShare loadingA loadingB : Cell -> Real) :
    scoreCellBilinearCovarianceKernelForm
        cells referenceShare loadingA loadingB =
      scoreCellBilinearCovarianceKernelForm
        cells referenceShare loadingB loadingA := by
  rw [scoreCellBilinearCovarianceKernelForm_eq_crossMoment_sub_mean_mul_mean]
  rw [scoreCellBilinearCovarianceKernelForm_eq_crossMoment_sub_mean_mul_mean]
  rw [scoreCellLoadingReferenceCrossMoment_comm]
  ring

omit [DecidableEq Cell] in
/-- A constant left loading has cross moment equal to constant times the right mean. -/
theorem scoreCellLoadingReferenceCrossMoment_const_left
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    (constant : Real) :
    scoreCellLoadingReferenceCrossMoment cells referenceShare
        (fun _cell => constant) loading =
      constant * scoreCellLoadingReferenceMean cells referenceShare loading := by
  unfold scoreCellLoadingReferenceCrossMoment scoreCellLoadingReferenceMean
  rw [Finset.mul_sum]
  exact Finset.sum_congr rfl
    (fun cell _hcell => by ring)

omit [DecidableEq Cell] in
/-- A constant right loading has cross moment equal to constant times the left mean. -/
theorem scoreCellLoadingReferenceCrossMoment_const_right
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    (constant : Real) :
    scoreCellLoadingReferenceCrossMoment cells referenceShare loading
        (fun _cell => constant) =
      constant * scoreCellLoadingReferenceMean cells referenceShare loading := by
  rw [scoreCellLoadingReferenceCrossMoment_comm]
  exact scoreCellLoadingReferenceCrossMoment_const_left
    cells referenceShare loading constant

/-- A constant left loading has zero bilinear covariance under simplex shares. -/
theorem scoreCellBilinearCovarianceKernelForm_const_left_eq_zero
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    (constant : Real)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    scoreCellBilinearCovarianceKernelForm cells referenceShare
        (fun _cell => constant) loading =
      0 := by
  rw [scoreCellBilinearCovarianceKernelForm_eq_crossMoment_sub_mean_mul_mean]
  rw [scoreCellLoadingReferenceCrossMoment_const_left]
  rw [scoreCellLoadingReferenceMean_const cells referenceShare constant
    hshare_sum]
  ring

/-- A constant right loading has zero bilinear covariance under simplex shares. -/
theorem scoreCellBilinearCovarianceKernelForm_const_right_eq_zero
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    (constant : Real)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    scoreCellBilinearCovarianceKernelForm cells referenceShare loading
        (fun _cell => constant) =
      0 := by
  rw [scoreCellBilinearCovarianceKernelForm_comm]
  exact scoreCellBilinearCovarianceKernelForm_const_left_eq_zero
    cells referenceShare loading constant hshare_sum

/--
Pointwise product of two finite linear centered-indicator projections as a
double sum of centered indicator products.
-/
theorem scoreCellLinearCenteredIndicator_mul_eq_bilinear_sum
    (cells : Finset Cell) (score : Unit -> Cell)
    (referenceShare loadingA loadingB : Cell -> Real) (unit : Unit) :
    scoreCellLinearCenteredIndicator cells score referenceShare loadingA unit *
        scoreCellLinearCenteredIndicator cells score referenceShare loadingB unit =
      ∑ cellA ∈ cells, ∑ cellB ∈ cells,
        loadingA cellA * loadingB cellB *
          (centeredScoreCellIndicator score referenceShare cellA unit *
            centeredScoreCellIndicator score referenceShare cellB unit) := by
  unfold scoreCellLinearCenteredIndicator
  calc
    (∑ cellA ∈ cells,
        loadingA cellA *
          centeredScoreCellIndicator score referenceShare cellA unit) *
        (∑ cellB ∈ cells,
          loadingB cellB *
            centeredScoreCellIndicator score referenceShare cellB unit) =
        ∑ cellA ∈ cells,
          (loadingA cellA *
            centeredScoreCellIndicator score referenceShare cellA unit) *
            (∑ cellB ∈ cells,
              loadingB cellB *
                centeredScoreCellIndicator score referenceShare cellB unit) := by
          rw [Finset.sum_mul]
    _ =
        ∑ cellA ∈ cells, ∑ cellB ∈ cells,
          (loadingA cellA *
            centeredScoreCellIndicator score referenceShare cellA unit) *
            (loadingB cellB *
              centeredScoreCellIndicator score referenceShare cellB unit) := by
          exact Finset.sum_congr rfl
            (fun cellA _hcellA => by
              rw [Finset.mul_sum])
    _ =
        ∑ cellA ∈ cells, ∑ cellB ∈ cells,
          loadingA cellA * loadingB cellB *
            (centeredScoreCellIndicator score referenceShare cellA unit *
              centeredScoreCellIndicator score referenceShare cellB unit) := by
          exact Finset.sum_congr rfl
            (fun cellA _hcellA =>
              Finset.sum_congr rfl
                (fun cellB _hcellB => by ring))

/--
The weighted product of two finite linear centered-indicator projections equals
the bilinear covariance-kernel form times the total weight when all included
cell masses match their reference shares.
-/
theorem
    weightedSampleSum_scoreCellLinearCenteredIndicator_mul_eq_bilinearKernelForm_mul_total
    (sample : Finset Unit) (weight : Unit -> Real)
    (cells : Finset Cell) (score : Unit -> Cell)
    (referenceShare loadingA loadingB : Cell -> Real)
    (hmass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sample weight score cell =
          referenceShare cell * weightedSampleTotal sample weight) :
    weightedSampleSum sample weight
        (fun unit =>
          scoreCellLinearCenteredIndicator cells score referenceShare loadingA
              unit *
            scoreCellLinearCenteredIndicator cells score referenceShare loadingB
              unit) =
      scoreCellBilinearCovarianceKernelForm
          cells referenceShare loadingA loadingB *
        weightedSampleTotal sample weight := by
  unfold weightedSampleSum
  calc
    (∑ unit ∈ sample,
        weight unit *
          (scoreCellLinearCenteredIndicator cells score referenceShare loadingA
              unit *
            scoreCellLinearCenteredIndicator cells score referenceShare loadingB
              unit)) =
        ∑ unit ∈ sample,
          weight unit *
            (∑ cellA ∈ cells, ∑ cellB ∈ cells,
              loadingA cellA * loadingB cellB *
                (centeredScoreCellIndicator score referenceShare cellA unit *
                  centeredScoreCellIndicator score referenceShare cellB unit)) := by
          exact Finset.sum_congr rfl
            (fun unit _hunit => by
              rw [scoreCellLinearCenteredIndicator_mul_eq_bilinear_sum])
    _ =
        ∑ unit ∈ sample, ∑ cellA ∈ cells, ∑ cellB ∈ cells,
          weight unit *
            (loadingA cellA * loadingB cellB *
              (centeredScoreCellIndicator score referenceShare cellA unit *
                centeredScoreCellIndicator score referenceShare cellB unit)) := by
          exact Finset.sum_congr rfl
            (fun unit _hunit => by
              rw [Finset.mul_sum]
              exact Finset.sum_congr rfl
                (fun cellA _hcellA => by
                  rw [Finset.mul_sum]))
    _ =
        ∑ cellA ∈ cells, ∑ unit ∈ sample, ∑ cellB ∈ cells,
          weight unit *
            (loadingA cellA * loadingB cellB *
              (centeredScoreCellIndicator score referenceShare cellA unit *
                centeredScoreCellIndicator score referenceShare cellB unit)) := by
          rw [Finset.sum_comm]
    _ =
        ∑ cellA ∈ cells, ∑ cellB ∈ cells, ∑ unit ∈ sample,
          weight unit *
            (loadingA cellA * loadingB cellB *
              (centeredScoreCellIndicator score referenceShare cellA unit *
                centeredScoreCellIndicator score referenceShare cellB unit)) := by
          exact Finset.sum_congr rfl
            (fun cellA _hcellA => by
              rw [Finset.sum_comm])
    _ =
        ∑ cellA ∈ cells, ∑ cellB ∈ cells,
          loadingA cellA * loadingB cellB *
            (∑ unit ∈ sample,
              weight unit *
                (centeredScoreCellIndicator score referenceShare cellA unit *
                  centeredScoreCellIndicator score referenceShare cellB unit)) := by
          exact Finset.sum_congr rfl
            (fun cellA _hcellA =>
              Finset.sum_congr rfl
                (fun cellB _hcellB => by
                  rw [Finset.mul_sum]
                  exact Finset.sum_congr rfl
                    (fun unit _hunit => by ring)))
    _ =
        ∑ cellA ∈ cells, ∑ cellB ∈ cells,
          loadingA cellA * loadingB cellB *
            (scoreCellIndicatorCovarianceKernel referenceShare cellA cellB *
              weightedSampleTotal sample weight) := by
          exact Finset.sum_congr rfl
            (fun cellA hcellA =>
              Finset.sum_congr rfl
                (fun cellB hcellB => by
                  change
                    loadingA cellA * loadingB cellB *
                        weightedSampleSum sample weight
                          (fun unit =>
                            centeredScoreCellIndicator score referenceShare
                                cellA unit *
                              centeredScoreCellIndicator score referenceShare
                                cellB unit) =
                      loadingA cellA * loadingB cellB *
                        (scoreCellIndicatorCovarianceKernel referenceShare
                            cellA cellB *
                          weightedSampleTotal sample weight)
                  rw [
                    weightedSampleSum_centeredIndicator_mul_eq_covarianceKernel_mul_total
                      sample weight score referenceShare cellA cellB
                      (fun cell hcell => by
                        rcases hcell with h | h
                        · subst cell
                          exact hmass cellA hcellA
                        · subst cell
                          exact hmass cellB hcellB)]))
    _ =
        scoreCellBilinearCovarianceKernelForm
            cells referenceShare loadingA loadingB *
          weightedSampleTotal sample weight := by
          unfold scoreCellBilinearCovarianceKernelForm
          rw [Finset.sum_mul]
          exact Finset.sum_congr rfl
            (fun cellA _hcellA => by
              rw [Finset.sum_mul]
              exact Finset.sum_congr rfl
                (fun cellB _hcellB => by ring))

/-- Normalized finite bilinear covariance-kernel formula. -/
theorem
    weightedSampleSum_scoreCellLinearCenteredIndicator_mul_div_total_eq_bilinearKernelForm
    (sample : Finset Unit) (weight : Unit -> Real)
    (cells : Finset Cell) (score : Unit -> Cell)
    (referenceShare loadingA loadingB : Cell -> Real)
    (htotal : weightedSampleTotal sample weight ≠ 0)
    (hmass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sample weight score cell =
          referenceShare cell * weightedSampleTotal sample weight) :
    weightedSampleSum sample weight
        (fun unit =>
          scoreCellLinearCenteredIndicator cells score referenceShare loadingA
              unit *
            scoreCellLinearCenteredIndicator cells score referenceShare loadingB
              unit) /
        weightedSampleTotal sample weight =
      scoreCellBilinearCovarianceKernelForm
        cells referenceShare loadingA loadingB := by
  rw [
    weightedSampleSum_scoreCellLinearCenteredIndicator_mul_eq_bilinearKernelForm_mul_total
      sample weight cells score referenceShare loadingA loadingB hmass]
  field_simp [htotal]

/--
Normalized finite bilinear centered-indicator covariances equal the closed-form
`cross moment - mean product` target under exact reference-share cell masses.
-/
theorem
    weightedSampleSum_scoreCellLinearCenteredIndicator_mul_div_total_eq_crossMoment_sub_mean_mul_mean
    (sample : Finset Unit) (weight : Unit -> Real)
    (cells : Finset Cell) (score : Unit -> Cell)
    (referenceShare loadingA loadingB : Cell -> Real)
    (htotal : weightedSampleTotal sample weight ≠ 0)
    (hmass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sample weight score cell =
          referenceShare cell * weightedSampleTotal sample weight) :
    weightedSampleSum sample weight
        (fun unit =>
          scoreCellLinearCenteredIndicator cells score referenceShare loadingA
              unit *
            scoreCellLinearCenteredIndicator cells score referenceShare loadingB
              unit) /
        weightedSampleTotal sample weight =
      scoreCellLoadingReferenceCrossMoment
          cells referenceShare loadingA loadingB -
        scoreCellLoadingReferenceMean cells referenceShare loadingA *
          scoreCellLoadingReferenceMean cells referenceShare loadingB := by
  rw [
    weightedSampleSum_scoreCellLinearCenteredIndicator_mul_div_total_eq_bilinearKernelForm
      sample weight cells score referenceShare loadingA loadingB htotal hmass]
  rw [scoreCellBilinearCovarianceKernelForm_eq_crossMoment_sub_mean_mul_mean]

end WDSM
end Matching
end StatInference
