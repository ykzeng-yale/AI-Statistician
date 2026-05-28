import StatInference.Matching.WDSM.DiscreteBalancingAlgebra

/-!
# Discrete score-cell share mean decomposition

This module makes explicit the normalized-share form of the finite
score-cell mean decomposition.  It is the discrete analogue of the
law-of-total-expectation step that later measure-theoretic identification
work must prove under conditional-expectation assumptions.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit Cell : Type*} [DecidableEq Cell]

/-- Weighted sample mean reconstructed from true score-cell means and normalized shares. -/
noncomputable def scoreCellMeanShareAggregate
    (sample : Finset Unit) (cells : Finset Cell)
    (weight outcome : Unit -> Real) (score : Unit -> Cell) : Real :=
  ∑ cell ∈ cells,
    scoreCellMean sample weight outcome score cell *
      scoreCellShare sample weight score cell

/--
True score-cell means aggregated against normalized cell shares recover the
finite weighted sample mean.
-/
theorem scoreCellMeanShareAggregate_eq_weightedSampleMean_of_mapsTo
    (sample : Finset Unit) (cells : Finset Cell)
    (weight outcome : Unit -> Real) (score : Unit -> Cell)
    (hcover : ∀ unit, unit ∈ sample -> score unit ∈ cells)
    (hmass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sample weight score cell ≠ 0) :
    scoreCellMeanShareAggregate sample cells weight outcome score =
      weightedSampleMean sample weight outcome := by
  change
    candidateCellMeanShareAggregate sample cells weight score
        (fun cell => scoreCellMean sample weight outcome score cell) =
      weightedSampleMean sample weight outcome
  rw [← candidateCellMeanAggregate_eq_candidateCellMeanShareAggregate
    sample cells weight score
    (fun cell => scoreCellMean sample weight outcome score cell)]
  exact candidateCellMeanAggregate_eq_weightedSampleMean_of_eq
    sample cells weight outcome score
    (fun cell => scoreCellMean sample weight outcome score cell)
    hcover hmass (fun _cell _hcell => rfl)

/--
Weighted sample mean written directly as a finite sum of score-cell means
times score-cell shares.
-/
theorem weightedSampleMean_eq_sum_scoreCellMean_mul_share_of_mapsTo
    (sample : Finset Unit) (cells : Finset Cell)
    (weight outcome : Unit -> Real) (score : Unit -> Cell)
    (hcover : ∀ unit, unit ∈ sample -> score unit ∈ cells)
    (hmass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sample weight score cell ≠ 0) :
    weightedSampleMean sample weight outcome =
      ∑ cell ∈ cells,
        scoreCellMean sample weight outcome score cell *
          scoreCellShare sample weight score cell :=
  (scoreCellMeanShareAggregate_eq_weightedSampleMean_of_mapsTo
    sample cells weight outcome score hcover hmass).symm

/--
If a candidate cell-mean function equals the true finite cell mean on every
included cell, then its normalized-share aggregate recovers the weighted
sample mean.
-/
theorem candidateCellMeanShareAggregate_eq_weightedSampleMean_of_eq
    (sample : Finset Unit) (cells : Finset Cell)
    (weight outcome : Unit -> Real) (score : Unit -> Cell)
    (candidateMean : Cell -> Real)
    (hcover : ∀ unit, unit ∈ sample -> score unit ∈ cells)
    (hmass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sample weight score cell ≠ 0)
    (hcandidate :
      ∀ cell, cell ∈ cells ->
        candidateMean cell =
          scoreCellMean sample weight outcome score cell) :
    candidateCellMeanShareAggregate sample cells weight score candidateMean =
      weightedSampleMean sample weight outcome := by
  rw [← candidateCellMeanAggregate_eq_candidateCellMeanShareAggregate
    sample cells weight score candidateMean]
  exact candidateCellMeanAggregate_eq_weightedSampleMean_of_eq
    sample cells weight outcome score candidateMean hcover hmass hcandidate

/-- Contrast between two true score-cell mean share aggregates. -/
noncomputable def scoreCellMeanShareAggregateContrast
    (sample : Finset Unit) (cells : Finset Cell)
    (weight outcomeA outcomeB : Unit -> Real) (score : Unit -> Cell) : Real :=
  scoreCellMeanShareAggregate sample cells weight outcomeA score -
    scoreCellMeanShareAggregate sample cells weight outcomeB score

/-- Contrast between two candidate cell-mean normalized-share aggregates. -/
noncomputable def candidateCellMeanShareAggregateContrast
    (sample : Finset Unit) (cells : Finset Cell)
    (weight : Unit -> Real) (score : Unit -> Cell)
    (candidateA candidateB : Cell -> Real) : Real :=
  candidateCellMeanShareAggregate sample cells weight score candidateA -
    candidateCellMeanShareAggregate sample cells weight score candidateB

/-- Difference of true cell-mean share aggregates recovers the weighted mean contrast. -/
theorem scoreCellMeanShareAggregateContrast_eq_weightedSampleMeanContrast_of_mapsTo
    (sample : Finset Unit) (cells : Finset Cell)
    (weight outcomeA outcomeB : Unit -> Real) (score : Unit -> Cell)
    (hcover : ∀ unit, unit ∈ sample -> score unit ∈ cells)
    (hmass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sample weight score cell ≠ 0) :
    scoreCellMeanShareAggregateContrast sample cells weight outcomeA
        outcomeB score =
      weightedSampleMeanContrast sample weight outcomeA outcomeB := by
  unfold scoreCellMeanShareAggregateContrast weightedSampleMeanContrast
  rw [scoreCellMeanShareAggregate_eq_weightedSampleMean_of_mapsTo
    sample cells weight outcomeA score hcover hmass]
  rw [scoreCellMeanShareAggregate_eq_weightedSampleMean_of_mapsTo
    sample cells weight outcomeB score hcover hmass]

/--
Difference of candidate normalized-share aggregates recovers the weighted mean
contrast when both candidate cell-mean functions match the true cell means.
-/
theorem candidateCellMeanShareAggregateContrast_eq_weightedSampleMeanContrast_of_eq
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
    candidateCellMeanShareAggregateContrast sample cells weight score
        candidateA candidateB =
      weightedSampleMeanContrast sample weight outcomeA outcomeB := by
  unfold candidateCellMeanShareAggregateContrast weightedSampleMeanContrast
  rw [candidateCellMeanShareAggregate_eq_weightedSampleMean_of_eq
    sample cells weight outcomeA score candidateA hcover hmass hcandidateA]
  rw [candidateCellMeanShareAggregate_eq_weightedSampleMean_of_eq
    sample cells weight outcomeB score candidateB hcover hmass hcandidateB]

end WDSM
end Matching
end StatInference
