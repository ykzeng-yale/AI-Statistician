import StatInference.Matching.WDSM.FiniteCellIndicatorCovarianceNonneg

/-!
# Degeneracy and shift invariance of finite score-cell covariance forms

The multinomial-style score-cell covariance lives on the simplex tangent space.
This module proves the deterministic finite algebra: constant loadings have
zero covariance-kernel quadratic form, and adding a constant to a loading does
not change the centered variance target.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit Cell : Type*} [DecidableEq Cell]

omit [DecidableEq Cell] in
/-- The reference-share mean of a constant loading is that constant. -/
theorem scoreCellLoadingReferenceMean_const
    (cells : Finset Cell) (referenceShare : Cell -> Real) (constant : Real)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    scoreCellLoadingReferenceMean cells referenceShare
        (fun _cell => constant) =
      constant := by
  unfold scoreCellLoadingReferenceMean
  rw [← Finset.sum_mul]
  rw [hshare_sum]
  ring

omit [DecidableEq Cell] in
/-- The reference-share second moment of a constant loading is its square. -/
theorem scoreCellLoadingReferenceSecondMoment_const
    (cells : Finset Cell) (referenceShare : Cell -> Real) (constant : Real)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    scoreCellLoadingReferenceSecondMoment cells referenceShare
        (fun _cell => constant) =
      constant ^ 2 := by
  unfold scoreCellLoadingReferenceSecondMoment
  rw [← Finset.sum_mul]
  rw [hshare_sum]
  ring

/-- Constant loadings have zero covariance-kernel quadratic form. -/
theorem scoreCellLinearCovarianceKernelForm_const_eq_zero
    (cells : Finset Cell) (referenceShare : Cell -> Real) (constant : Real)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    scoreCellLinearCovarianceKernelForm cells referenceShare
        (fun _cell => constant) =
      0 := by
  rw [scoreCellLinearCovarianceKernelForm_eq_secondMoment_sub_mean_sq]
  rw [scoreCellLoadingReferenceSecondMoment_const cells referenceShare constant
    hshare_sum]
  rw [scoreCellLoadingReferenceMean_const cells referenceShare constant
    hshare_sum]
  ring

omit [DecidableEq Cell] in
/-- Adding a constant shifts the reference-share mean by that constant. -/
theorem scoreCellLoadingReferenceMean_add_const
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    (constant : Real)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    scoreCellLoadingReferenceMean cells referenceShare
        (fun cell => loading cell + constant) =
      scoreCellLoadingReferenceMean cells referenceShare loading + constant := by
  unfold scoreCellLoadingReferenceMean
  calc
    (∑ cell ∈ cells,
        referenceShare cell * (loading cell + constant)) =
        ∑ cell ∈ cells,
          (referenceShare cell * loading cell +
            referenceShare cell * constant) := by
          exact Finset.sum_congr rfl
            (fun cell _hcell => by ring)
    _ =
        (∑ cell ∈ cells, referenceShare cell * loading cell) +
          (∑ cell ∈ cells, referenceShare cell * constant) := by
          rw [Finset.sum_add_distrib]
    _ =
        (∑ cell ∈ cells, referenceShare cell * loading cell) +
          (∑ cell ∈ cells, referenceShare cell) * constant := by
          rw [← Finset.sum_mul]
    _ =
        (∑ cell ∈ cells, referenceShare cell * loading cell) + constant := by
          rw [hshare_sum]
          ring

omit [DecidableEq Cell] in
/-- Constant loadings have zero centered second moment. -/
theorem scoreCellLoadingReferenceCenteredSecondMoment_const_eq_zero
    (cells : Finset Cell) (referenceShare : Cell -> Real) (constant : Real)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare
        (fun _cell => constant) =
      0 := by
  rw [scoreCellLoadingReferenceCenteredSecondMoment_eq_secondMoment_sub_mean_sq]
  · rw [scoreCellLoadingReferenceSecondMoment_const cells referenceShare
      constant hshare_sum]
    rw [scoreCellLoadingReferenceMean_const cells referenceShare constant
      hshare_sum]
    ring
  · exact hshare_sum

omit [DecidableEq Cell] in
/-- Centered second moments are invariant under adding a constant loading. -/
theorem scoreCellLoadingReferenceCenteredSecondMoment_add_const_eq
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    (constant : Real)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    scoreCellLoadingReferenceCenteredSecondMoment cells referenceShare
        (fun cell => loading cell + constant) =
      scoreCellLoadingReferenceCenteredSecondMoment
        cells referenceShare loading := by
  unfold scoreCellLoadingReferenceCenteredSecondMoment
  rw [scoreCellLoadingReferenceMean_add_const cells referenceShare loading
    constant hshare_sum]
  exact Finset.sum_congr rfl
    (fun cell _hcell => by ring)

/-- Covariance-kernel quadratic forms are invariant under adding a constant. -/
theorem scoreCellLinearCovarianceKernelForm_add_const_eq
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    (constant : Real)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    scoreCellLinearCovarianceKernelForm cells referenceShare
        (fun cell => loading cell + constant) =
      scoreCellLinearCovarianceKernelForm cells referenceShare loading := by
  rw [scoreCellLinearCovarianceKernelForm_eq_centeredSecondMoment
    cells referenceShare (fun cell => loading cell + constant) hshare_sum]
  rw [scoreCellLinearCovarianceKernelForm_eq_centeredSecondMoment
    cells referenceShare loading hshare_sum]
  exact scoreCellLoadingReferenceCenteredSecondMoment_add_const_eq
    cells referenceShare loading constant hshare_sum

/--
The normalized finite centered-indicator variance is zero for constant
loadings under exact reference-share cell masses.
-/
theorem
    weightedSampleSum_scoreCellLinearCenteredIndicator_const_sq_div_total_eq_zero
    (sample : Finset Unit) (weight : Unit -> Real)
    (cells : Finset Cell) (score : Unit -> Cell)
    (referenceShare : Cell -> Real) (constant : Real)
    (htotal : weightedSampleTotal sample weight ≠ 0)
    (hmass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sample weight score cell =
          referenceShare cell * weightedSampleTotal sample weight)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    weightedSampleSum sample weight
        (fun unit =>
          scoreCellLinearCenteredIndicator cells score referenceShare
              (fun _cell => constant) unit *
            scoreCellLinearCenteredIndicator cells score referenceShare
              (fun _cell => constant) unit) /
        weightedSampleTotal sample weight =
      0 := by
  rw [
    weightedSampleSum_scoreCellLinearCenteredIndicator_sq_div_total_eq_centeredSecondMoment
      sample weight cells score referenceShare (fun _cell => constant) htotal
      hmass hshare_sum]
  exact scoreCellLoadingReferenceCenteredSecondMoment_const_eq_zero
    cells referenceShare constant hshare_sum

/--
The normalized finite centered-indicator variance is invariant under adding a
constant to the loading.
-/
theorem
    weightedSampleSum_scoreCellLinearCenteredIndicator_add_const_sq_div_total_eq
    (sample : Finset Unit) (weight : Unit -> Real)
    (cells : Finset Cell) (score : Unit -> Cell)
    (referenceShare loading : Cell -> Real) (constant : Real)
    (htotal : weightedSampleTotal sample weight ≠ 0)
    (hmass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sample weight score cell =
          referenceShare cell * weightedSampleTotal sample weight)
    (hshare_sum : (∑ cell ∈ cells, referenceShare cell) = 1) :
    weightedSampleSum sample weight
        (fun unit =>
          scoreCellLinearCenteredIndicator cells score referenceShare
              (fun cell => loading cell + constant) unit *
            scoreCellLinearCenteredIndicator cells score referenceShare
              (fun cell => loading cell + constant) unit) /
        weightedSampleTotal sample weight =
      weightedSampleSum sample weight
        (fun unit =>
          scoreCellLinearCenteredIndicator cells score referenceShare loading
              unit *
            scoreCellLinearCenteredIndicator cells score referenceShare loading
              unit) /
        weightedSampleTotal sample weight := by
  rw [
    weightedSampleSum_scoreCellLinearCenteredIndicator_sq_div_total_eq_centeredSecondMoment
      sample weight cells score referenceShare
      (fun cell => loading cell + constant) htotal hmass hshare_sum]
  rw [
    weightedSampleSum_scoreCellLinearCenteredIndicator_sq_div_total_eq_centeredSecondMoment
      sample weight cells score referenceShare loading htotal hmass hshare_sum]
  exact scoreCellLoadingReferenceCenteredSecondMoment_add_const_eq
    cells referenceShare loading constant hshare_sum

end WDSM
end Matching
end StatInference
