import StatInference.Matching.WDSM.FiniteCellIndicatorCovariance

/-!
# Closed-form finite score-cell indicator covariance kernel for WDSM

This module turns the centered score-cell indicator product expansion into the
finite multinomial-style covariance kernel whenever the observed weighted cell
masses equal the reference cell shares times the total survey weight.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit Cell : Type*} [DecidableEq Cell]

/-- Finite multinomial-style covariance kernel for score-cell indicators. -/
noncomputable def scoreCellIndicatorCovarianceKernel
    (referenceShare : Cell -> Real) (cellA cellB : Cell) : Real :=
  if cellA = cellB then
    referenceShare cellA * (1 - referenceShare cellA)
  else
    -referenceShare cellA * referenceShare cellB

/--
Same-cell centered indicator products collapse to the finite covariance kernel
when the weighted cell mass matches the reference share.
-/
theorem weightedSampleSum_centeredIndicator_sq_eq_covarianceKernel_mul_total
    (sample : Finset Unit) (weight : Unit -> Real)
    (score : Unit -> Cell) (referenceShare : Cell -> Real) (cell : Cell)
    (hmass :
      scoreCellMass sample weight score cell =
        referenceShare cell * weightedSampleTotal sample weight) :
    weightedSampleSum sample weight
        (fun unit =>
          centeredScoreCellIndicator score referenceShare cell unit *
            centeredScoreCellIndicator score referenceShare cell unit) =
      scoreCellIndicatorCovarianceKernel referenceShare cell cell *
        weightedSampleTotal sample weight := by
  rw [weightedSampleSum_centeredIndicator_sq_eq]
  rw [hmass]
  simp [scoreCellIndicatorCovarianceKernel]
  ring

/--
Distinct-cell centered indicator products collapse to the off-diagonal finite
covariance kernel when both weighted cell masses match their reference shares.
-/
theorem
    weightedSampleSum_centeredIndicator_mul_of_ne_eq_covarianceKernel_mul_total
    (sample : Finset Unit) (weight : Unit -> Real)
    (score : Unit -> Cell) (referenceShare : Cell -> Real)
    (cellA cellB : Cell) (hne : cellA ≠ cellB)
    (hmassA :
      scoreCellMass sample weight score cellA =
        referenceShare cellA * weightedSampleTotal sample weight)
    (hmassB :
      scoreCellMass sample weight score cellB =
        referenceShare cellB * weightedSampleTotal sample weight) :
    weightedSampleSum sample weight
        (fun unit =>
          centeredScoreCellIndicator score referenceShare cellA unit *
            centeredScoreCellIndicator score referenceShare cellB unit) =
      scoreCellIndicatorCovarianceKernel referenceShare cellA cellB *
        weightedSampleTotal sample weight := by
  rw [weightedSampleSum_centeredIndicator_mul_centeredIndicator_of_ne_eq
    sample weight score referenceShare cellA cellB hne]
  rw [hmassA, hmassB]
  simp [scoreCellIndicatorCovarianceKernel, hne]
  ring

/--
Unified centered-indicator covariance-kernel formula, with the mass assumption
needed only for the cells that appear in the covariance entry.
-/
theorem weightedSampleSum_centeredIndicator_mul_eq_covarianceKernel_mul_total
    (sample : Finset Unit) (weight : Unit -> Real)
    (score : Unit -> Cell) (referenceShare : Cell -> Real)
    (cellA cellB : Cell)
    (hmass :
      ∀ cell, cell = cellA ∨ cell = cellB ->
        scoreCellMass sample weight score cell =
          referenceShare cell * weightedSampleTotal sample weight) :
    weightedSampleSum sample weight
        (fun unit =>
          centeredScoreCellIndicator score referenceShare cellA unit *
            centeredScoreCellIndicator score referenceShare cellB unit) =
      scoreCellIndicatorCovarianceKernel referenceShare cellA cellB *
        weightedSampleTotal sample weight := by
  by_cases h : cellA = cellB
  · subst cellB
    exact weightedSampleSum_centeredIndicator_sq_eq_covarianceKernel_mul_total
      sample weight score referenceShare cellA
      (hmass cellA (Or.inl rfl))
  · exact
      weightedSampleSum_centeredIndicator_mul_of_ne_eq_covarianceKernel_mul_total
        sample weight score referenceShare cellA cellB h
        (hmass cellA (Or.inl rfl))
        (hmass cellB (Or.inr rfl))

/--
Normalized finite covariance-kernel formula.  This is the deterministic target
that later weighted indicator LLN/CLT arguments must approximate.
-/
theorem weightedSampleSum_centeredIndicator_mul_div_total_eq_covarianceKernel
    (sample : Finset Unit) (weight : Unit -> Real)
    (score : Unit -> Cell) (referenceShare : Cell -> Real)
    (cellA cellB : Cell)
    (htotal : weightedSampleTotal sample weight ≠ 0)
    (hmass :
      ∀ cell, cell = cellA ∨ cell = cellB ->
        scoreCellMass sample weight score cell =
          referenceShare cell * weightedSampleTotal sample weight) :
    weightedSampleSum sample weight
        (fun unit =>
          centeredScoreCellIndicator score referenceShare cellA unit *
            centeredScoreCellIndicator score referenceShare cellB unit) /
        weightedSampleTotal sample weight =
      scoreCellIndicatorCovarianceKernel referenceShare cellA cellB := by
  rw [weightedSampleSum_centeredIndicator_mul_eq_covarianceKernel_mul_total
    sample weight score referenceShare cellA cellB hmass]
  field_simp [htotal]

end WDSM
end Matching
end StatInference
