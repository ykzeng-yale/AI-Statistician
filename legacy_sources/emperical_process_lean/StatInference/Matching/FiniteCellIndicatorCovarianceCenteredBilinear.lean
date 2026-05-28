import StatInference.Matching.WDSM.FiniteCellIndicatorCovarianceBilinear

/-!
# Centered bilinear finite score-cell covariance algebra

This module rewrites the bilinear score-cell covariance target as a centered
cross moment `E_p[(f - E_p f) (g - E_p g)]`.  That is the finite covariance
matrix entry used by later finite-dimensional CLT interfaces.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit Cell : Type*} [DecidableEq Cell]

/-- Reference-share centered cross moment of two finite cell loadings. -/
noncomputable def scoreCellLoadingReferenceCenteredCrossMoment
    (cells : Finset Cell) (referenceShare loadingA loadingB : Cell -> Real) :
    Real :=
  ∑ cell ∈ cells,
    referenceShare cell *
      (loadingA cell -
        scoreCellLoadingReferenceMean cells referenceShare loadingA) *
      (loadingB cell -
        scoreCellLoadingReferenceMean cells referenceShare loadingB)

omit [DecidableEq Cell] in
/--
Under total reference share one, the centered cross moment equals the finite
covariance expression `cross moment - mean product`.
-/
theorem scoreCellLoadingReferenceCenteredCrossMoment_eq_crossMoment_sub_mean_mul_mean
    (cells : Finset Cell) (referenceShare loadingA loadingB : Cell -> Real)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    scoreCellLoadingReferenceCenteredCrossMoment
        cells referenceShare loadingA loadingB =
      scoreCellLoadingReferenceCrossMoment
          cells referenceShare loadingA loadingB -
        scoreCellLoadingReferenceMean cells referenceShare loadingA *
          scoreCellLoadingReferenceMean cells referenceShare loadingB := by
  unfold scoreCellLoadingReferenceCenteredCrossMoment
  calc
    (∑ cell ∈ cells,
        referenceShare cell *
          (loadingA cell -
            scoreCellLoadingReferenceMean cells referenceShare loadingA) *
          (loadingB cell -
            scoreCellLoadingReferenceMean cells referenceShare loadingB)) =
        ∑ cell ∈ cells,
          (referenceShare cell * loadingA cell * loadingB cell -
            scoreCellLoadingReferenceMean cells referenceShare loadingB *
              (referenceShare cell * loadingA cell) -
            scoreCellLoadingReferenceMean cells referenceShare loadingA *
              (referenceShare cell * loadingB cell) +
            scoreCellLoadingReferenceMean cells referenceShare loadingA *
              scoreCellLoadingReferenceMean cells referenceShare loadingB *
              referenceShare cell) := by
          exact Finset.sum_congr rfl
            (fun cell _hcell => by ring)
    _ =
        (∑ cell ∈ cells,
          referenceShare cell * loadingA cell * loadingB cell) -
          scoreCellLoadingReferenceMean cells referenceShare loadingB *
            (∑ cell ∈ cells, referenceShare cell * loadingA cell) -
          scoreCellLoadingReferenceMean cells referenceShare loadingA *
            (∑ cell ∈ cells, referenceShare cell * loadingB cell) +
          scoreCellLoadingReferenceMean cells referenceShare loadingA *
            scoreCellLoadingReferenceMean cells referenceShare loadingB *
            (∑ cell ∈ cells, referenceShare cell) := by
          calc
            (∑ cell ∈ cells,
              (referenceShare cell * loadingA cell * loadingB cell -
                scoreCellLoadingReferenceMean cells referenceShare loadingB *
                  (referenceShare cell * loadingA cell) -
                scoreCellLoadingReferenceMean cells referenceShare loadingA *
                  (referenceShare cell * loadingB cell) +
                scoreCellLoadingReferenceMean cells referenceShare loadingA *
                  scoreCellLoadingReferenceMean cells referenceShare loadingB *
                  referenceShare cell)) =
                (∑ cell ∈ cells,
                  ((referenceShare cell * loadingA cell * loadingB cell -
                    scoreCellLoadingReferenceMean cells referenceShare loadingB *
                      (referenceShare cell * loadingA cell)) -
                    scoreCellLoadingReferenceMean cells referenceShare loadingA *
                      (referenceShare cell * loadingB cell))) +
                  (∑ cell ∈ cells,
                    scoreCellLoadingReferenceMean cells referenceShare loadingA *
                      scoreCellLoadingReferenceMean cells referenceShare loadingB *
                      referenceShare cell) := by
                  rw [Finset.sum_add_distrib]
            _ =
                ((∑ cell ∈ cells,
                  (referenceShare cell * loadingA cell * loadingB cell -
                    scoreCellLoadingReferenceMean cells referenceShare loadingB *
                      (referenceShare cell * loadingA cell))) -
                  (∑ cell ∈ cells,
                    scoreCellLoadingReferenceMean cells referenceShare loadingA *
                      (referenceShare cell * loadingB cell))) +
                  (∑ cell ∈ cells,
                    scoreCellLoadingReferenceMean cells referenceShare loadingA *
                      scoreCellLoadingReferenceMean cells referenceShare loadingB *
                      referenceShare cell) := by
                  rw [Finset.sum_sub_distrib]
            _ =
                (((∑ cell ∈ cells,
                  referenceShare cell * loadingA cell * loadingB cell) -
                  (∑ cell ∈ cells,
                    scoreCellLoadingReferenceMean cells referenceShare loadingB *
                      (referenceShare cell * loadingA cell))) -
                  (∑ cell ∈ cells,
                    scoreCellLoadingReferenceMean cells referenceShare loadingA *
                      (referenceShare cell * loadingB cell))) +
                  (∑ cell ∈ cells,
                    scoreCellLoadingReferenceMean cells referenceShare loadingA *
                      scoreCellLoadingReferenceMean cells referenceShare loadingB *
                      referenceShare cell) := by
                  rw [Finset.sum_sub_distrib]
            _ =
                (((∑ cell ∈ cells,
                  referenceShare cell * loadingA cell * loadingB cell) -
                  scoreCellLoadingReferenceMean cells referenceShare loadingB *
                    (∑ cell ∈ cells, referenceShare cell * loadingA cell)) -
                  scoreCellLoadingReferenceMean cells referenceShare loadingA *
                    (∑ cell ∈ cells, referenceShare cell * loadingB cell)) +
                  scoreCellLoadingReferenceMean cells referenceShare loadingA *
                    scoreCellLoadingReferenceMean cells referenceShare loadingB *
                    (∑ cell ∈ cells, referenceShare cell) := by
                  rw [← Finset.mul_sum]
                  rw [← Finset.mul_sum]
                  rw [← Finset.mul_sum]
            _ =
                (∑ cell ∈ cells,
                  referenceShare cell * loadingA cell * loadingB cell) -
                  scoreCellLoadingReferenceMean cells referenceShare loadingB *
                    (∑ cell ∈ cells, referenceShare cell * loadingA cell) -
                  scoreCellLoadingReferenceMean cells referenceShare loadingA *
                    (∑ cell ∈ cells, referenceShare cell * loadingB cell) +
                  scoreCellLoadingReferenceMean cells referenceShare loadingA *
                    scoreCellLoadingReferenceMean cells referenceShare loadingB *
                    (∑ cell ∈ cells, referenceShare cell) := by
                  ring
    _ =
        scoreCellLoadingReferenceCrossMoment
            cells referenceShare loadingA loadingB -
          scoreCellLoadingReferenceMean cells referenceShare loadingA *
            scoreCellLoadingReferenceMean cells referenceShare loadingB := by
          rw [← scoreCellLoadingReferenceCrossMoment]
          rw [← scoreCellLoadingReferenceMean]
          rw [← scoreCellLoadingReferenceMean]
          rw [hshare_sum]
          ring

omit [DecidableEq Cell] in
/--
The centered cross moment agrees with the centered second moment when the two
loadings are the same.
-/
theorem scoreCellLoadingReferenceCenteredCrossMoment_self_eq_centeredSecondMoment
    (cells : Finset Cell) (referenceShare loading : Cell -> Real) :
    scoreCellLoadingReferenceCenteredCrossMoment
        cells referenceShare loading loading =
      scoreCellLoadingReferenceCenteredSecondMoment
        cells referenceShare loading := by
  unfold scoreCellLoadingReferenceCenteredCrossMoment
  unfold scoreCellLoadingReferenceCenteredSecondMoment
  exact Finset.sum_congr rfl
    (fun cell _hcell => by ring)

omit [DecidableEq Cell] in
/-- Reference-share centered cross moments are symmetric. -/
theorem scoreCellLoadingReferenceCenteredCrossMoment_comm
    (cells : Finset Cell) (referenceShare loadingA loadingB : Cell -> Real) :
    scoreCellLoadingReferenceCenteredCrossMoment
        cells referenceShare loadingA loadingB =
      scoreCellLoadingReferenceCenteredCrossMoment
        cells referenceShare loadingB loadingA := by
  unfold scoreCellLoadingReferenceCenteredCrossMoment
  exact Finset.sum_congr rfl
    (fun cell _hcell => by ring)

/--
Under simplex reference shares, the bilinear covariance-kernel form is the
centered cross moment of the two loadings.
-/
theorem scoreCellBilinearCovarianceKernelForm_eq_centeredCrossMoment
    (cells : Finset Cell) (referenceShare loadingA loadingB : Cell -> Real)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    scoreCellBilinearCovarianceKernelForm
        cells referenceShare loadingA loadingB =
      scoreCellLoadingReferenceCenteredCrossMoment
        cells referenceShare loadingA loadingB := by
  rw [scoreCellBilinearCovarianceKernelForm_eq_crossMoment_sub_mean_mul_mean]
  rw [scoreCellLoadingReferenceCenteredCrossMoment_eq_crossMoment_sub_mean_mul_mean
    cells referenceShare loadingA loadingB hshare_sum]

/--
Normalized finite bilinear centered-indicator covariances equal the centered
cross moment under exact reference-share cell masses and simplex shares.
-/
theorem
    weightedSampleSum_scoreCellLinearCenteredIndicator_mul_div_total_eq_centeredCrossMoment
    (sample : Finset Unit) (weight : Unit -> Real)
    (cells : Finset Cell) (score : Unit -> Cell)
    (referenceShare loadingA loadingB : Cell -> Real)
    (htotal : weightedSampleTotal sample weight ≠ 0)
    (hmass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sample weight score cell =
          referenceShare cell * weightedSampleTotal sample weight)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    weightedSampleSum sample weight
        (fun unit =>
          scoreCellLinearCenteredIndicator cells score referenceShare loadingA
              unit *
            scoreCellLinearCenteredIndicator cells score referenceShare loadingB
              unit) /
        weightedSampleTotal sample weight =
      scoreCellLoadingReferenceCenteredCrossMoment
        cells referenceShare loadingA loadingB := by
  rw [
    weightedSampleSum_scoreCellLinearCenteredIndicator_mul_div_total_eq_crossMoment_sub_mean_mul_mean
      sample weight cells score referenceShare loadingA loadingB htotal hmass]
  rw [← scoreCellLoadingReferenceCenteredCrossMoment_eq_crossMoment_sub_mean_mul_mean
    cells referenceShare loadingA loadingB hshare_sum]

end WDSM
end Matching
end StatInference
