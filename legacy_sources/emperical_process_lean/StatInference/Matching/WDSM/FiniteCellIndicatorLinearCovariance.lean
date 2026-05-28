import StatInference.Matching.WDSM.FiniteCellIndicatorCovarianceFormula

/-!
# Finite linear score-cell indicator covariance algebra for WDSM

Finite-dimensional CLT arguments test cell-indicator vectors against arbitrary
loadings.  This module proves the deterministic variance identity for those
linear projections using the closed-form score-cell covariance kernel.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit Cell : Type*} [DecidableEq Cell]

/-- A finite linear projection of centered score-cell indicators. -/
noncomputable def scoreCellLinearCenteredIndicator
    (cells : Finset Cell) (score : Unit -> Cell)
    (referenceShare : Cell -> Real) (loading : Cell -> Real)
    (unit : Unit) : Real :=
  ∑ cell ∈ cells,
    loading cell * centeredScoreCellIndicator score referenceShare cell unit

/-- The finite covariance-kernel quadratic form for a cell loading. -/
noncomputable def scoreCellLinearCovarianceKernelForm
    (cells : Finset Cell) (referenceShare loading : Cell -> Real) : Real :=
  ∑ cellA ∈ cells, ∑ cellB ∈ cells,
    loading cellA * loading cellB *
      scoreCellIndicatorCovarianceKernel referenceShare cellA cellB

/--
The weighted sum of a finite linear centered indicator projection is the
corresponding linear combination of cell-mass deviations from reference shares.
-/
theorem weightedSampleSum_scoreCellLinearCenteredIndicator_eq
    (sample : Finset Unit) (weight : Unit -> Real)
    (cells : Finset Cell) (score : Unit -> Cell)
    (referenceShare loading : Cell -> Real) :
    weightedSampleSum sample weight
        (scoreCellLinearCenteredIndicator cells score referenceShare loading) =
      ∑ cell ∈ cells,
        loading cell *
          (scoreCellMass sample weight score cell -
            referenceShare cell * weightedSampleTotal sample weight) := by
  unfold scoreCellLinearCenteredIndicator
  calc
    weightedSampleSum sample weight
        (fun unit =>
          ∑ cell ∈ cells,
            loading cell *
              centeredScoreCellIndicator score referenceShare cell unit) =
        ∑ cell ∈ cells,
          loading cell *
            weightedSampleSum sample weight
              (centeredScoreCellIndicator score referenceShare cell) := by
          unfold weightedSampleSum
          calc
            (∑ unit ∈ sample,
                weight unit *
                  (∑ cell ∈ cells,
                    loading cell *
                      centeredScoreCellIndicator score referenceShare cell
                        unit)) =
                ∑ unit ∈ sample, ∑ cell ∈ cells,
                  weight unit *
                    (loading cell *
                      centeredScoreCellIndicator score referenceShare cell
                        unit) := by
                  exact Finset.sum_congr rfl
                    (fun unit _hunit => by
                      rw [Finset.mul_sum])
            _ =
                ∑ cell ∈ cells, ∑ unit ∈ sample,
                  weight unit *
                    (loading cell *
                      centeredScoreCellIndicator score referenceShare cell
                        unit) := by
                  rw [Finset.sum_comm]
            _ =
                ∑ cell ∈ cells,
                  loading cell *
                    (∑ unit ∈ sample,
                      weight unit *
                        centeredScoreCellIndicator score referenceShare cell
                          unit) := by
                  exact Finset.sum_congr rfl
                    (fun cell _hcell => by
                      rw [Finset.mul_sum]
                      exact Finset.sum_congr rfl
                        (fun unit _hunit => by ring))
    _ =
        ∑ cell ∈ cells,
          loading cell *
            (scoreCellMass sample weight score cell -
              referenceShare cell * weightedSampleTotal sample weight) := by
          exact Finset.sum_congr rfl
            (fun cell _hcell => by
              rw [weightedSampleSum_centeredScoreCellIndicator_eq])

/--
Exact reference-share cell masses force every finite centered indicator
projection to have zero weighted sum.
-/
theorem weightedSampleSum_scoreCellLinearCenteredIndicator_eq_zero
    (sample : Finset Unit) (weight : Unit -> Real)
    (cells : Finset Cell) (score : Unit -> Cell)
    (referenceShare loading : Cell -> Real)
    (hmass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sample weight score cell =
          referenceShare cell * weightedSampleTotal sample weight) :
    weightedSampleSum sample weight
        (scoreCellLinearCenteredIndicator cells score referenceShare loading) =
      0 := by
  rw [weightedSampleSum_scoreCellLinearCenteredIndicator_eq]
  exact Finset.sum_eq_zero
    (fun cell hcell => by
      rw [hmass cell hcell]
      ring)

/--
Pointwise expansion of a finite linear centered-indicator square into a double
sum of centered indicator products.
-/
theorem scoreCellLinearCenteredIndicator_mul_eq_sum
    (cells : Finset Cell) (score : Unit -> Cell)
    (referenceShare loading : Cell -> Real) (unit : Unit) :
    scoreCellLinearCenteredIndicator cells score referenceShare loading unit *
        scoreCellLinearCenteredIndicator cells score referenceShare loading unit =
      ∑ cellA ∈ cells, ∑ cellB ∈ cells,
        loading cellA * loading cellB *
          (centeredScoreCellIndicator score referenceShare cellA unit *
            centeredScoreCellIndicator score referenceShare cellB unit) := by
  unfold scoreCellLinearCenteredIndicator
  calc
    (∑ cellA ∈ cells,
        loading cellA *
          centeredScoreCellIndicator score referenceShare cellA unit) *
        (∑ cellB ∈ cells,
          loading cellB *
            centeredScoreCellIndicator score referenceShare cellB unit) =
        ∑ cellA ∈ cells,
          (loading cellA *
            centeredScoreCellIndicator score referenceShare cellA unit) *
            (∑ cellB ∈ cells,
              loading cellB *
                centeredScoreCellIndicator score referenceShare cellB unit) := by
          rw [Finset.sum_mul]
    _ =
        ∑ cellA ∈ cells, ∑ cellB ∈ cells,
          (loading cellA *
            centeredScoreCellIndicator score referenceShare cellA unit) *
            (loading cellB *
              centeredScoreCellIndicator score referenceShare cellB unit) := by
          exact Finset.sum_congr rfl
            (fun cellA _hcellA => by
              rw [Finset.mul_sum])
    _ =
        ∑ cellA ∈ cells, ∑ cellB ∈ cells,
          loading cellA * loading cellB *
            (centeredScoreCellIndicator score referenceShare cellA unit *
              centeredScoreCellIndicator score referenceShare cellB unit) := by
          exact Finset.sum_congr rfl
            (fun cellA _hcellA =>
              Finset.sum_congr rfl
                (fun cellB _hcellB => by ring))

/--
The weighted square of a finite linear centered indicator projection equals
the covariance-kernel quadratic form times the total weight when all included
cell masses match their reference shares.
-/
theorem
    weightedSampleSum_scoreCellLinearCenteredIndicator_sq_eq_kernelForm_mul_total
    (sample : Finset Unit) (weight : Unit -> Real)
    (cells : Finset Cell) (score : Unit -> Cell)
    (referenceShare loading : Cell -> Real)
    (hmass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sample weight score cell =
          referenceShare cell * weightedSampleTotal sample weight) :
    weightedSampleSum sample weight
        (fun unit =>
          scoreCellLinearCenteredIndicator cells score referenceShare loading unit *
            scoreCellLinearCenteredIndicator cells score referenceShare loading
              unit) =
      scoreCellLinearCovarianceKernelForm cells referenceShare loading *
        weightedSampleTotal sample weight := by
  unfold weightedSampleSum
  calc
    (∑ unit ∈ sample,
        weight unit *
          (scoreCellLinearCenteredIndicator cells score referenceShare loading
              unit *
            scoreCellLinearCenteredIndicator cells score referenceShare loading
              unit)) =
        ∑ unit ∈ sample,
          weight unit *
            (∑ cellA ∈ cells, ∑ cellB ∈ cells,
              loading cellA * loading cellB *
                (centeredScoreCellIndicator score referenceShare cellA unit *
                  centeredScoreCellIndicator score referenceShare cellB unit)) := by
          exact Finset.sum_congr rfl
            (fun unit _hunit => by
              rw [scoreCellLinearCenteredIndicator_mul_eq_sum])
    _ =
        ∑ unit ∈ sample, ∑ cellA ∈ cells, ∑ cellB ∈ cells,
          weight unit *
            (loading cellA * loading cellB *
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
            (loading cellA * loading cellB *
              (centeredScoreCellIndicator score referenceShare cellA unit *
                centeredScoreCellIndicator score referenceShare cellB unit)) := by
          rw [Finset.sum_comm]
    _ =
        ∑ cellA ∈ cells, ∑ cellB ∈ cells, ∑ unit ∈ sample,
          weight unit *
            (loading cellA * loading cellB *
              (centeredScoreCellIndicator score referenceShare cellA unit *
                centeredScoreCellIndicator score referenceShare cellB unit)) := by
          exact Finset.sum_congr rfl
            (fun cellA _hcellA => by
              rw [Finset.sum_comm])
    _ =
        ∑ cellA ∈ cells, ∑ cellB ∈ cells,
          loading cellA * loading cellB *
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
          loading cellA * loading cellB *
            (scoreCellIndicatorCovarianceKernel referenceShare cellA cellB *
              weightedSampleTotal sample weight) := by
          exact Finset.sum_congr rfl
            (fun cellA hcellA =>
              Finset.sum_congr rfl
                (fun cellB hcellB => by
                  change
                    loading cellA * loading cellB *
                        weightedSampleSum sample weight
                          (fun unit =>
                            centeredScoreCellIndicator score referenceShare
                                cellA unit *
                              centeredScoreCellIndicator score referenceShare
                                cellB unit) =
                      loading cellA * loading cellB *
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
        scoreCellLinearCovarianceKernelForm cells referenceShare loading *
          weightedSampleTotal sample weight := by
          unfold scoreCellLinearCovarianceKernelForm
          rw [Finset.sum_mul]
          exact Finset.sum_congr rfl
            (fun cellA _hcellA => by
              rw [Finset.sum_mul]
              exact Finset.sum_congr rfl
                (fun cellB _hcellB => by ring))

/-- Normalized finite linear covariance-kernel formula. -/
theorem
    weightedSampleSum_scoreCellLinearCenteredIndicator_sq_div_total_eq_kernelForm
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
      scoreCellLinearCovarianceKernelForm cells referenceShare loading := by
  rw [
    weightedSampleSum_scoreCellLinearCenteredIndicator_sq_eq_kernelForm_mul_total
      sample weight cells score referenceShare loading hmass]
  field_simp [htotal]

end WDSM
end Matching
end StatInference
