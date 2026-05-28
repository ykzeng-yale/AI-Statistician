import StatInference.Matching.WDSM.DiscreteMeanRecovery
import StatInference.Matching.WDSM.DiscreteBalancingAlgebra

/-!
# Finite score-cell approximation error bounds for WDSM

Exact score-cell identification is too strong for asymptotic work.  This
module proves deterministic finite bounds showing that uniformly small
cellwise mean errors imply small weighted mean errors.  These are the finite
targets later radius, balancing, or stochastic convergence arguments should
feed into.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Cell : Type*} [DecidableEq Cell]

/-- Generic weighted aggregate over a finite set of cells. -/
noncomputable def cellShareAggregate
    (cells : Finset Cell) (share cellMean : Cell -> Real) : Real :=
  ∑ cell ∈ cells, share cell * cellMean cell

omit [DecidableEq Cell] in
theorem abs_cellShareAggregate_sub_le_of_uniform_error
    (cells : Finset Cell) (share candidate trueMean : Cell -> Real)
    (radius : Real)
    (hshare_nonneg : ∀ cell, cell ∈ cells -> 0 ≤ share cell)
    (hsum : (∑ cell ∈ cells, share cell) = 1)
    (herror :
      ∀ cell, cell ∈ cells -> |candidate cell - trueMean cell| ≤ radius) :
    |cellShareAggregate cells share candidate -
        cellShareAggregate cells share trueMean| ≤ radius := by
  unfold cellShareAggregate
  calc
    |(∑ cell ∈ cells, share cell * candidate cell) -
        (∑ cell ∈ cells, share cell * trueMean cell)| =
        |∑ cell ∈ cells,
          share cell * (candidate cell - trueMean cell)| := by
          congr 1
          rw [← Finset.sum_sub_distrib]
          exact Finset.sum_congr rfl
            (fun cell _ => by ring)
    _ ≤ ∑ cell ∈ cells,
          |share cell * (candidate cell - trueMean cell)| := by
        exact Finset.abs_sum_le_sum_abs _ _
    _ = ∑ cell ∈ cells,
          share cell * |candidate cell - trueMean cell| := by
        exact Finset.sum_congr rfl
          (fun cell hcell => by
            rw [abs_mul, abs_of_nonneg (hshare_nonneg cell hcell)])
    _ ≤ ∑ cell ∈ cells, share cell * radius := by
        exact Finset.sum_le_sum
          (fun cell hcell =>
            mul_le_mul_of_nonneg_left (herror cell hcell)
              (hshare_nonneg cell hcell))
    _ = radius := by
        rw [← Finset.sum_mul, hsum]
        ring

variable {Unit : Type*}

theorem candidateCellMeanShareAggregate_eq_cellShareAggregate
    (sample : Finset Unit) (cells : Finset Cell)
    (weight : Unit -> Real) (score : Unit -> Cell)
    (candidateMean : Cell -> Real) :
    candidateCellMeanShareAggregate sample cells weight score candidateMean =
      cellShareAggregate cells
        (fun cell => scoreCellShare sample weight score cell)
        candidateMean := by
  unfold candidateCellMeanShareAggregate cellShareAggregate scoreCellShare
  exact Finset.sum_congr rfl
    (fun cell _ => by ring)

theorem scoreCellMeanAggregate_eq_scoreCellMeanShareAggregate
    (sample : Finset Unit) (cells : Finset Cell)
    (weight outcome : Unit -> Real) (score : Unit -> Cell) :
    scoreCellMeanAggregate sample cells weight outcome score =
      cellShareAggregate cells
        (fun cell => scoreCellShare sample weight score cell)
        (fun cell => scoreCellMean sample weight outcome score cell) := by
  unfold scoreCellMeanAggregate scoreCellMeanNumerator
    cellShareAggregate scoreCellShare
  calc
    (∑ cell ∈ cells,
        scoreCellMean sample weight outcome score cell *
          scoreCellMass sample weight score cell) /
        weightedSampleTotal sample weight =
        ∑ cell ∈ cells,
          (scoreCellMean sample weight outcome score cell *
            scoreCellMass sample weight score cell) /
            weightedSampleTotal sample weight := by
          rw [Finset.sum_div]
    _ = ∑ cell ∈ cells,
          scoreCellMass sample weight score cell /
            weightedSampleTotal sample weight *
            scoreCellMean sample weight outcome score cell := by
        exact Finset.sum_congr rfl
          (fun cell _ => by ring)

theorem abs_candidateCellMeanAggregate_sub_scoreCellMeanAggregate_le
    (sample : Finset Unit) (cells : Finset Cell)
    (weight outcome : Unit -> Real) (score : Unit -> Cell)
    (candidateMean : Cell -> Real) (radius : Real)
    (hshare_nonneg :
      ∀ cell, cell ∈ cells ->
        0 ≤ scoreCellShare sample weight score cell)
    (hshare_sum :
      (∑ cell ∈ cells, scoreCellShare sample weight score cell) = 1)
    (herror :
      ∀ cell, cell ∈ cells ->
        |candidateMean cell -
          scoreCellMean sample weight outcome score cell| ≤ radius) :
    |candidateCellMeanAggregate sample cells weight score candidateMean -
        scoreCellMeanAggregate sample cells weight outcome score| ≤ radius := by
  rw [candidateCellMeanAggregate_eq_candidateCellMeanShareAggregate]
  rw [candidateCellMeanShareAggregate_eq_cellShareAggregate]
  rw [scoreCellMeanAggregate_eq_scoreCellMeanShareAggregate]
  exact abs_cellShareAggregate_sub_le_of_uniform_error
    cells (fun cell => scoreCellShare sample weight score cell)
    candidateMean
    (fun cell => scoreCellMean sample weight outcome score cell)
    radius hshare_nonneg hshare_sum herror

theorem abs_candidateCellMeanAggregate_sub_weightedSampleMean_le
    (sample : Finset Unit) (cells : Finset Cell)
    (weight outcome : Unit -> Real) (score : Unit -> Cell)
    (candidateMean : Cell -> Real) (radius : Real)
    (hcover : ∀ unit, unit ∈ sample -> score unit ∈ cells)
    (hmass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sample weight score cell ≠ 0)
    (hshare_nonneg :
      ∀ cell, cell ∈ cells ->
        0 ≤ scoreCellShare sample weight score cell)
    (hshare_sum :
      (∑ cell ∈ cells, scoreCellShare sample weight score cell) = 1)
    (herror :
      ∀ cell, cell ∈ cells ->
        |candidateMean cell -
          scoreCellMean sample weight outcome score cell| ≤ radius) :
    |candidateCellMeanAggregate sample cells weight score candidateMean -
        weightedSampleMean sample weight outcome| ≤ radius := by
  rw [← scoreCellMeanAggregate_eq_weightedSampleMean_of_mapsTo
    sample cells weight outcome score hcover hmass]
  exact abs_candidateCellMeanAggregate_sub_scoreCellMeanAggregate_le
    sample cells weight outcome score candidateMean radius hshare_nonneg
    hshare_sum herror

theorem abs_candidateCellMeanAggregate_sub_weightedSampleMean_le_of_nonneg_weights
    (sample : Finset Unit) (cells : Finset Cell)
    (weight outcome : Unit -> Real) (score : Unit -> Cell)
    (candidateMean : Cell -> Real) (radius : Real)
    (hcover : ∀ unit, unit ∈ sample -> score unit ∈ cells)
    (hmass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sample weight score cell ≠ 0)
    (htotal_ne : weightedSampleTotal sample weight ≠ 0)
    (htotal_nonneg : 0 ≤ weightedSampleTotal sample weight)
    (hweight_nonneg : ∀ unit, unit ∈ sample -> 0 ≤ weight unit)
    (herror :
      ∀ cell, cell ∈ cells ->
        |candidateMean cell -
          scoreCellMean sample weight outcome score cell| ≤ radius) :
    |candidateCellMeanAggregate sample cells weight score candidateMean -
        weightedSampleMean sample weight outcome| ≤ radius := by
  exact abs_candidateCellMeanAggregate_sub_weightedSampleMean_le
    sample cells weight outcome score candidateMean radius
    hcover hmass
    (fun cell _ =>
      scoreCellShare_nonneg sample weight score cell htotal_nonneg
        (fun unit hunit _ => hweight_nonneg unit hunit))
    (sum_scoreCellShare_eq_one_of_mapsTo sample cells weight score
      hcover htotal_ne)
    herror

end WDSM
end Matching
end StatInference
