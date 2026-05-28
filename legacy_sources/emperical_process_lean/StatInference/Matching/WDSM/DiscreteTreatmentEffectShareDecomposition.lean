import StatInference.Matching.WDSM.DiscreteShareMeanDecomposition

/-!
# Discrete treatment-effect share decomposition

This module turns the normalized-share mean decomposition into the target
contrast form used by PATE/PATT identification: a weighted mean contrast is a
finite average of score-cell mean contrasts under the target score-cell
shares.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit Cell : Type*} [DecidableEq Cell]

/--
Target score-cell treatment-effect aggregate using true finite cell means and
target score-cell shares.
-/
noncomputable def scoreCellMeanEffectShareAggregate
    (sample : Finset Unit) (cells : Finset Cell)
    (weight outcomeA outcomeB : Unit -> Real) (score : Unit -> Cell) : Real :=
  ∑ cell ∈ cells,
    (scoreCellMean sample weight outcomeA score cell -
        scoreCellMean sample weight outcomeB score cell) *
      scoreCellShare sample weight score cell

/--
The target weighted mean contrast equals the normalized-share aggregate of
true finite score-cell mean contrasts.
-/
theorem scoreCellMeanEffectShareAggregate_eq_weightedSampleMeanContrast_of_mapsTo
    (sample : Finset Unit) (cells : Finset Cell)
    (weight outcomeA outcomeB : Unit -> Real) (score : Unit -> Cell)
    (hcover : ∀ unit, unit ∈ sample -> score unit ∈ cells)
    (hmass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sample weight score cell ≠ 0) :
    scoreCellMeanEffectShareAggregate sample cells weight outcomeA
        outcomeB score =
      weightedSampleMeanContrast sample weight outcomeA outcomeB := by
  unfold scoreCellMeanEffectShareAggregate weightedSampleMeanContrast
  rw [weightedSampleMean_eq_sum_scoreCellMean_mul_share_of_mapsTo
    sample cells weight outcomeA score hcover hmass]
  rw [weightedSampleMean_eq_sum_scoreCellMean_mul_share_of_mapsTo
    sample cells weight outcomeB score hcover hmass]
  rw [← Finset.sum_sub_distrib]
  exact Finset.sum_congr rfl
    (fun cell _hcell => by ring)

/-- Candidate score-cell treatment-effect aggregate under target score-cell shares. -/
noncomputable def candidateCellEffectShareAggregate
    (sample : Finset Unit) (cells : Finset Cell)
    (weight : Unit -> Real) (score : Unit -> Cell)
    (candidateEffect : Cell -> Real) : Real :=
  ∑ cell ∈ cells,
    candidateEffect cell * scoreCellShare sample weight score cell

/--
If a candidate cell-effect function equals the finite true cell-mean
contrast on every included cell, then its target-share aggregate recovers the
weighted sample mean contrast.
-/
theorem candidateCellEffectShareAggregate_eq_weightedSampleMeanContrast_of_eq
    (sample : Finset Unit) (cells : Finset Cell)
    (weight outcomeA outcomeB : Unit -> Real) (score : Unit -> Cell)
    (candidateEffect : Cell -> Real)
    (hcover : ∀ unit, unit ∈ sample -> score unit ∈ cells)
    (hmass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sample weight score cell ≠ 0)
    (hcandidate :
      ∀ cell, cell ∈ cells ->
        candidateEffect cell =
          scoreCellMean sample weight outcomeA score cell -
            scoreCellMean sample weight outcomeB score cell) :
    candidateCellEffectShareAggregate sample cells weight score
        candidateEffect =
      weightedSampleMeanContrast sample weight outcomeA outcomeB := by
  unfold candidateCellEffectShareAggregate
  rw [← scoreCellMeanEffectShareAggregate_eq_weightedSampleMeanContrast_of_mapsTo
    sample cells weight outcomeA outcomeB score hcover hmass]
  unfold scoreCellMeanEffectShareAggregate
  exact Finset.sum_congr rfl
    (fun cell hcell => by
      rw [hcandidate cell hcell])

/--
Candidate potential-outcome cell means induce a candidate cell-effect
aggregate.
-/
noncomputable def candidateCellMeanEffectShareAggregate
    (sample : Finset Unit) (cells : Finset Cell)
    (weight : Unit -> Real) (score : Unit -> Cell)
    (candidateA candidateB : Cell -> Real) : Real :=
  ∑ cell ∈ cells,
    (candidateA cell - candidateB cell) *
      scoreCellShare sample weight score cell

/--
If candidate potential-outcome cell means agree with true finite cell means,
their difference aggregated under target score-cell shares recovers the
weighted sample mean contrast.
-/
theorem candidateCellMeanEffectShareAggregate_eq_weightedSampleMeanContrast_of_eq
    (sample : Finset Unit) (cells : Finset Cell)
    (weight outcomeA outcomeB : Unit -> Real) (score : Unit -> Cell)
    (candidateA candidateB : Cell -> Real)
    (hcover : ∀ unit, unit ∈ sample -> score unit ∈ cells)
    (hmass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sample weight score cell ≠ 0)
    (hcandidateA :
      ∀ cell, cell ∈ cells ->
        candidateA cell =
          scoreCellMean sample weight outcomeA score cell)
    (hcandidateB :
      ∀ cell, cell ∈ cells ->
        candidateB cell =
          scoreCellMean sample weight outcomeB score cell) :
    candidateCellMeanEffectShareAggregate sample cells weight score
        candidateA candidateB =
      weightedSampleMeanContrast sample weight outcomeA outcomeB := by
  unfold candidateCellMeanEffectShareAggregate
  rw [← scoreCellMeanEffectShareAggregate_eq_weightedSampleMeanContrast_of_mapsTo
    sample cells weight outcomeA outcomeB score hcover hmass]
  unfold scoreCellMeanEffectShareAggregate
  exact Finset.sum_congr rfl
    (fun cell hcell => by
      rw [hcandidateA cell hcell, hcandidateB cell hcell])

end WDSM
end Matching
end StatInference
