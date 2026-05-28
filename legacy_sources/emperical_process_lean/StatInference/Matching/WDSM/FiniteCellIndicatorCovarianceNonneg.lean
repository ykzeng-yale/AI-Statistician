import StatInference.Matching.WDSM.FiniteCellIndicatorCovarianceQuadraticForm

/-!
# Nonnegativity of finite score-cell covariance quadratic forms

After the covariance-kernel quadratic form is reduced to `second moment -
mean^2`, the usual probability-simplex condition on reference shares turns it
into an explicit centered second moment.  This module proves that deterministic
nonnegativity layer for finite score-cell indicator projections.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit Cell : Type*} [DecidableEq Cell]

/-- Reference-share centered second moment of a finite cell loading. -/
noncomputable def scoreCellLoadingReferenceCenteredSecondMoment
    (cells : Finset Cell) (referenceShare loading : Cell -> Real) : Real :=
  ∑ cell ∈ cells,
    referenceShare cell *
      (loading cell -
        scoreCellLoadingReferenceMean cells referenceShare loading) ^ 2

omit [DecidableEq Cell] in
/--
Under total reference share one, the centered second moment equals the finite
variance expression `second moment - mean^2`.
-/
theorem scoreCellLoadingReferenceCenteredSecondMoment_eq_secondMoment_sub_mean_sq
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare loading =
      scoreCellLoadingReferenceSecondMoment cells referenceShare loading -
        scoreCellLoadingReferenceMean cells referenceShare loading ^ 2 := by
  unfold scoreCellLoadingReferenceCenteredSecondMoment
  calc
    (∑ cell ∈ cells,
        referenceShare cell *
          (loading cell -
            scoreCellLoadingReferenceMean cells referenceShare loading) ^ 2) =
        ∑ cell ∈ cells,
          (referenceShare cell * loading cell ^ 2 -
            2 * scoreCellLoadingReferenceMean cells referenceShare loading *
              (referenceShare cell * loading cell) +
            scoreCellLoadingReferenceMean cells referenceShare loading ^ 2 *
              referenceShare cell) := by
          exact Finset.sum_congr rfl
            (fun cell _hcell => by
              ring)
    _ =
        (∑ cell ∈ cells, referenceShare cell * loading cell ^ 2) -
          2 * scoreCellLoadingReferenceMean cells referenceShare loading *
            (∑ cell ∈ cells, referenceShare cell * loading cell) +
          scoreCellLoadingReferenceMean cells referenceShare loading ^ 2 *
            (∑ cell ∈ cells, referenceShare cell) := by
          calc
            (∑ cell ∈ cells,
              (referenceShare cell * loading cell ^ 2 -
                2 * scoreCellLoadingReferenceMean cells referenceShare loading *
                  (referenceShare cell * loading cell) +
                scoreCellLoadingReferenceMean cells referenceShare loading ^ 2 *
                  referenceShare cell)) =
                (∑ cell ∈ cells,
                  (referenceShare cell * loading cell ^ 2 -
                    2 * scoreCellLoadingReferenceMean cells referenceShare loading *
                      (referenceShare cell * loading cell))) +
                  (∑ cell ∈ cells,
                    scoreCellLoadingReferenceMean cells referenceShare loading ^ 2 *
                      referenceShare cell) := by
                  rw [Finset.sum_add_distrib]
            _ =
                ((∑ cell ∈ cells, referenceShare cell * loading cell ^ 2) -
                  (∑ cell ∈ cells,
                    2 * scoreCellLoadingReferenceMean cells referenceShare loading *
                      (referenceShare cell * loading cell))) +
                  (∑ cell ∈ cells,
                    scoreCellLoadingReferenceMean cells referenceShare loading ^ 2 *
                      referenceShare cell) := by
                  rw [Finset.sum_sub_distrib]
            _ =
                ((∑ cell ∈ cells, referenceShare cell * loading cell ^ 2) -
                  2 * scoreCellLoadingReferenceMean cells referenceShare loading *
                    (∑ cell ∈ cells, referenceShare cell * loading cell)) +
                  scoreCellLoadingReferenceMean cells referenceShare loading ^ 2 *
                    (∑ cell ∈ cells, referenceShare cell) := by
                  rw [← Finset.mul_sum]
                  rw [← Finset.mul_sum]
            _ =
                (∑ cell ∈ cells, referenceShare cell * loading cell ^ 2) -
                  2 * scoreCellLoadingReferenceMean cells referenceShare loading *
                    (∑ cell ∈ cells, referenceShare cell * loading cell) +
                  scoreCellLoadingReferenceMean cells referenceShare loading ^ 2 *
                    (∑ cell ∈ cells, referenceShare cell) := by
                  ring
    _ =
        scoreCellLoadingReferenceSecondMoment cells referenceShare loading -
          scoreCellLoadingReferenceMean cells referenceShare loading ^ 2 := by
          rw [← scoreCellLoadingReferenceSecondMoment]
          rw [← scoreCellLoadingReferenceMean]
          rw [hshare_sum]
          ring

omit [DecidableEq Cell] in
/-- Centered second moments are nonnegative under nonnegative reference shares. -/
theorem scoreCellLoadingReferenceCenteredSecondMoment_nonneg
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    (hshare_nonneg : ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell) :
    0 ≤ scoreCellLoadingReferenceCenteredSecondMoment
      cells referenceShare loading := by
  unfold scoreCellLoadingReferenceCenteredSecondMoment
  exact Finset.sum_nonneg
    (fun cell hcell =>
      mul_nonneg (hshare_nonneg cell hcell)
        (sq_nonneg
          (loading cell -
            scoreCellLoadingReferenceMean cells referenceShare loading)))

/--
Under simplex reference shares, the covariance-kernel quadratic form is the
centered second moment of the loading.
-/
theorem scoreCellLinearCovarianceKernelForm_eq_centeredSecondMoment
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    scoreCellLinearCovarianceKernelForm cells referenceShare loading =
      scoreCellLoadingReferenceCenteredSecondMoment
        cells referenceShare loading := by
  rw [scoreCellLinearCovarianceKernelForm_eq_secondMoment_sub_mean_sq]
  rw [scoreCellLoadingReferenceCenteredSecondMoment_eq_secondMoment_sub_mean_sq
    cells referenceShare loading hshare_sum]

/--
The finite covariance-kernel quadratic form is nonnegative under nonnegative
reference shares summing to one.
-/
theorem scoreCellLinearCovarianceKernelForm_nonneg
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    (hshare_nonneg : ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    0 ≤ scoreCellLinearCovarianceKernelForm cells referenceShare loading := by
  rw [scoreCellLinearCovarianceKernelForm_eq_centeredSecondMoment
    cells referenceShare loading hshare_sum]
  exact scoreCellLoadingReferenceCenteredSecondMoment_nonneg
    cells referenceShare loading hshare_nonneg

/--
Normalized finite linear centered-indicator variances equal an explicit
centered second moment under exact reference-share cell masses and simplex
reference shares.
-/
theorem
    weightedSampleSum_scoreCellLinearCenteredIndicator_sq_div_total_eq_centeredSecondMoment
    (sample : Finset Unit) (weight : Unit -> Real)
    (cells : Finset Cell) (score : Unit -> Cell)
    (referenceShare loading : Cell -> Real)
    (htotal : weightedSampleTotal sample weight ≠ 0)
    (hmass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sample weight score cell =
          referenceShare cell * weightedSampleTotal sample weight)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    weightedSampleSum sample weight
        (fun unit =>
          scoreCellLinearCenteredIndicator cells score referenceShare loading unit *
            scoreCellLinearCenteredIndicator cells score referenceShare loading
              unit) /
        weightedSampleTotal sample weight =
      scoreCellLoadingReferenceCenteredSecondMoment
        cells referenceShare loading := by
  rw [
    weightedSampleSum_scoreCellLinearCenteredIndicator_sq_div_total_eq_secondMoment_sub_mean_sq
      sample weight cells score referenceShare loading htotal hmass]
  rw [← scoreCellLoadingReferenceCenteredSecondMoment_eq_secondMoment_sub_mean_sq
    cells referenceShare loading hshare_sum]

/--
The normalized finite linear centered-indicator variance target is nonnegative
under exact reference-share cell masses and simplex nonnegative shares.
-/
theorem weightedSampleSum_scoreCellLinearCenteredIndicator_sq_div_total_nonneg
    (sample : Finset Unit) (weight : Unit -> Real)
    (cells : Finset Cell) (score : Unit -> Cell)
    (referenceShare loading : Cell -> Real)
    (htotal : weightedSampleTotal sample weight ≠ 0)
    (hmass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sample weight score cell =
          referenceShare cell * weightedSampleTotal sample weight)
    (hshare_nonneg : ∀ cell, cell ∈ cells -> 0 ≤ referenceShare cell)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    0 ≤
      weightedSampleSum sample weight
        (fun unit =>
          scoreCellLinearCenteredIndicator cells score referenceShare loading unit *
            scoreCellLinearCenteredIndicator cells score referenceShare loading
              unit) /
        weightedSampleTotal sample weight := by
  rw [
    weightedSampleSum_scoreCellLinearCenteredIndicator_sq_div_total_eq_centeredSecondMoment
      sample weight cells score referenceShare loading htotal hmass hshare_sum]
  exact scoreCellLoadingReferenceCenteredSecondMoment_nonneg
    cells referenceShare loading hshare_nonneg

end WDSM
end Matching
end StatInference
