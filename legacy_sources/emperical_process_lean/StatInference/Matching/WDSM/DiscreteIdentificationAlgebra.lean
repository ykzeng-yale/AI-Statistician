import Mathlib

/-!
# Discrete score-cell identification algebra for WDSM

This module proves the finite, deterministic algebra behind a discrete
conditional-mean route to WDSM identification.  It does not assert conditional
independence or balancing.  Instead, it provides the exact cell-mass,
cell-numerator, and cell-mean identities that later probability-layer
arguments can target.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit Cell : Type*} [DecidableEq Cell]

/-- Weighted total mass of a finite sample. -/
noncomputable def weightedSampleTotal
    (sample : Finset Unit) (weight : Unit -> Real) : Real :=
  ∑ unit ∈ sample, weight unit

/-- Weighted sample numerator for an arbitrary real-valued outcome. -/
noncomputable def weightedSampleSum
    (sample : Finset Unit) (weight outcome : Unit -> Real) : Real :=
  ∑ unit ∈ sample, weight unit * outcome unit

/-- Weighted mass inside one discrete score cell. -/
noncomputable def scoreCellMass
    (sample : Finset Unit) (weight : Unit -> Real)
    (score : Unit -> Cell) (cell : Cell) : Real :=
  ∑ unit ∈ sample with score unit = cell, weight unit

/-- Weighted numerator inside one discrete score cell. -/
noncomputable def scoreCellWeightedSum
    (sample : Finset Unit) (weight outcome : Unit -> Real)
    (score : Unit -> Cell) (cell : Cell) : Real :=
  ∑ unit ∈ sample with score unit = cell, weight unit * outcome unit

/-- Finite weighted cell mean, represented as numerator divided by cell mass. -/
noncomputable def scoreCellMean
    (sample : Finset Unit) (weight outcome : Unit -> Real)
    (score : Unit -> Cell) (cell : Cell) : Real :=
  scoreCellWeightedSum sample weight outcome score cell /
    scoreCellMass sample weight score cell

theorem scoreCellMass_nonneg
    (sample : Finset Unit) (weight : Unit -> Real)
    (score : Unit -> Cell) (cell : Cell)
    (hweight :
      ∀ unit, unit ∈ sample -> score unit = cell -> 0 ≤ weight unit) :
    0 ≤ scoreCellMass sample weight score cell := by
  unfold scoreCellMass
  exact Finset.sum_nonneg
    (fun unit hunit => by
      exact hweight unit (Finset.mem_filter.mp hunit).1
        (Finset.mem_filter.mp hunit).2)

theorem scoreCellWeightedSum_congr_on_cell
    (sample : Finset Unit) (weight outcomeA outcomeB : Unit -> Real)
    (score : Unit -> Cell) (cell : Cell)
    (h :
      ∀ unit, unit ∈ sample -> score unit = cell ->
        outcomeA unit = outcomeB unit) :
    scoreCellWeightedSum sample weight outcomeA score cell =
      scoreCellWeightedSum sample weight outcomeB score cell := by
  unfold scoreCellWeightedSum
  exact Finset.sum_congr rfl
    (fun unit hunit => by
      rw [h unit (Finset.mem_filter.mp hunit).1
        (Finset.mem_filter.mp hunit).2])

theorem scoreCellWeightedSum_eq_const_mul_mass_of_eq_on_cell
    (sample : Finset Unit) (weight outcome : Unit -> Real)
    (score : Unit -> Cell) (cell : Cell) (value : Real)
    (h :
      ∀ unit, unit ∈ sample -> score unit = cell -> outcome unit = value) :
    scoreCellWeightedSum sample weight outcome score cell =
      value * scoreCellMass sample weight score cell := by
  unfold scoreCellWeightedSum scoreCellMass
  calc
    (∑ unit ∈ sample with score unit = cell, weight unit * outcome unit)
        = ∑ unit ∈ sample with score unit = cell, weight unit * value := by
          exact Finset.sum_congr rfl
            (fun unit hunit => by
              rw [h unit (Finset.mem_filter.mp hunit).1
                (Finset.mem_filter.mp hunit).2])
    _ = value * ∑ unit ∈ sample with score unit = cell, weight unit := by
        rw [Finset.mul_sum]
        exact Finset.sum_congr rfl
          (fun unit _ => by ring)

theorem scoreCellMean_mul_mass
    (sample : Finset Unit) (weight outcome : Unit -> Real)
    (score : Unit -> Cell) (cell : Cell)
    (hmass : scoreCellMass sample weight score cell ≠ 0) :
    scoreCellMean sample weight outcome score cell *
      scoreCellMass sample weight score cell =
      scoreCellWeightedSum sample weight outcome score cell := by
  unfold scoreCellMean
  field_simp [hmass]

theorem scoreCellWeightedSum_eq_scoreCellMean_mul_mass
    (sample : Finset Unit) (weight outcome : Unit -> Real)
    (score : Unit -> Cell) (cell : Cell)
    (hmass : scoreCellMass sample weight score cell ≠ 0) :
    scoreCellWeightedSum sample weight outcome score cell =
      scoreCellMean sample weight outcome score cell *
        scoreCellMass sample weight score cell :=
  (scoreCellMean_mul_mass sample weight outcome score cell hmass).symm

theorem scoreCellMean_eq_const_of_eq_on_cell
    (sample : Finset Unit) (weight outcome : Unit -> Real)
    (score : Unit -> Cell) (cell : Cell) (value : Real)
    (hmass : scoreCellMass sample weight score cell ≠ 0)
    (h :
      ∀ unit, unit ∈ sample -> score unit = cell -> outcome unit = value) :
    scoreCellMean sample weight outcome score cell = value := by
  unfold scoreCellMean
  rw [scoreCellWeightedSum_eq_const_mul_mass_of_eq_on_cell
    sample weight outcome score cell value h]
  field_simp [hmass]

/--
If an outcome is a function of the discrete score cell, the cell numerator is
that cell value times the cell mass.
-/
theorem scoreCellWeightedSum_of_scoreFunction
    (sample : Finset Unit) (weight : Unit -> Real)
    (score : Unit -> Cell) (cellValue : Cell -> Real) (cell : Cell) :
    scoreCellWeightedSum sample weight (fun unit => cellValue (score unit))
        score cell =
      cellValue cell * scoreCellMass sample weight score cell := by
  exact scoreCellWeightedSum_eq_const_mul_mass_of_eq_on_cell
    sample weight (fun unit => cellValue (score unit)) score cell
    (cellValue cell)
    (fun unit _ hscore => by
      simpa using congrArg cellValue hscore)

/--
If every sampled unit's score lies in `cells`, the sum of cell masses over
`cells` equals the total sample weight.
-/
theorem sum_scoreCellMass_eq_weightedSampleTotal_of_mapsTo
    (sample : Finset Unit) (cells : Finset Cell)
    (weight : Unit -> Real) (score : Unit -> Cell)
    (hcover : ∀ unit, unit ∈ sample -> score unit ∈ cells) :
    (∑ cell ∈ cells, scoreCellMass sample weight score cell) =
      weightedSampleTotal sample weight := by
  unfold scoreCellMass weightedSampleTotal
  exact Finset.sum_fiberwise_of_maps_to hcover weight

/--
If every sampled unit's score lies in `cells`, the full weighted numerator
decomposes into the sum of its score-cell numerators.
-/
theorem weightedSampleSum_eq_sum_scoreCellWeightedSums_of_mapsTo
    (sample : Finset Unit) (cells : Finset Cell)
    (weight outcome : Unit -> Real) (score : Unit -> Cell)
    (hcover : ∀ unit, unit ∈ sample -> score unit ∈ cells) :
    weightedSampleSum sample weight outcome =
      ∑ cell ∈ cells, scoreCellWeightedSum sample weight outcome score cell := by
  unfold weightedSampleSum scoreCellWeightedSum
  exact (Finset.sum_fiberwise_of_maps_to hcover
    (fun unit => weight unit * outcome unit)).symm

/--
For a score-measurable outcome, the full weighted numerator decomposes into
cell values times cell masses.
-/
theorem weightedSampleSum_scoreFunction_eq_sum_cellValue_mul_mass
    (sample : Finset Unit) (cells : Finset Cell)
    (weight : Unit -> Real) (score : Unit -> Cell)
    (cellValue : Cell -> Real)
    (hcover : ∀ unit, unit ∈ sample -> score unit ∈ cells) :
    weightedSampleSum sample weight (fun unit => cellValue (score unit)) =
      ∑ cell ∈ cells,
        cellValue cell * scoreCellMass sample weight score cell := by
  rw [weightedSampleSum_eq_sum_scoreCellWeightedSums_of_mapsTo
    sample cells weight (fun unit => cellValue (score unit)) score hcover]
  exact Finset.sum_congr rfl
    (fun cell _ => by
      rw [scoreCellWeightedSum_of_scoreFunction sample weight score
        cellValue cell])

/--
The full weighted numerator is the sum of finite cell means times cell masses,
provided the included cells have nonzero mass.
-/
theorem weightedSampleSum_eq_sum_scoreCellMean_mul_mass_of_mapsTo
    (sample : Finset Unit) (cells : Finset Cell)
    (weight outcome : Unit -> Real) (score : Unit -> Cell)
    (hcover : ∀ unit, unit ∈ sample -> score unit ∈ cells)
    (hmass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sample weight score cell ≠ 0) :
    weightedSampleSum sample weight outcome =
      ∑ cell ∈ cells,
        scoreCellMean sample weight outcome score cell *
          scoreCellMass sample weight score cell := by
  rw [weightedSampleSum_eq_sum_scoreCellWeightedSums_of_mapsTo
    sample cells weight outcome score hcover]
  exact Finset.sum_congr rfl
    (fun cell hcell =>
      scoreCellWeightedSum_eq_scoreCellMean_mul_mass
        sample weight outcome score cell (hmass cell hcell))

end WDSM
end Matching
end StatInference
