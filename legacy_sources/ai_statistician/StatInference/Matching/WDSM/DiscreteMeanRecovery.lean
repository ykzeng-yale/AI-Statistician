import StatInference.Matching.WDSM.DiscreteIdentificationAlgebra

/-!
# Discrete score-cell mean recovery for WDSM

This module builds on the finite score-cell algebra.  It proves that once a
candidate score-cell mean agrees with the true finite cell mean on each
included cell, the cell-mass weighted aggregate recovers the corresponding
survey-weighted sample mean.  This is the deterministic core of the
survey-weighted score-space mean recovery step; balancing and conditional
expectation assumptions must still prove the candidate-cell equality.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit Cell : Type*} [DecidableEq Cell]

/-- Survey-weighted finite sample mean as a Hájek ratio. -/
noncomputable def weightedSampleMean
    (sample : Finset Unit) (weight outcome : Unit -> Real) : Real :=
  weightedSampleSum sample weight outcome / weightedSampleTotal sample weight

/-- Numerator obtained by aggregating true score-cell means against cell masses. -/
noncomputable def scoreCellMeanNumerator
    (sample : Finset Unit) (cells : Finset Cell)
    (weight outcome : Unit -> Real) (score : Unit -> Cell) : Real :=
  ∑ cell ∈ cells,
    scoreCellMean sample weight outcome score cell *
      scoreCellMass sample weight score cell

/-- Hájek mean obtained from true score-cell means and score-cell masses. -/
noncomputable def scoreCellMeanAggregate
    (sample : Finset Unit) (cells : Finset Cell)
    (weight outcome : Unit -> Real) (score : Unit -> Cell) : Real :=
  scoreCellMeanNumerator sample cells weight outcome score /
    weightedSampleTotal sample weight

/-- Numerator obtained by aggregating an externally supplied score-cell mean. -/
noncomputable def candidateCellMeanNumerator
    (sample : Finset Unit) (cells : Finset Cell)
    (weight : Unit -> Real) (score : Unit -> Cell)
    (candidateMean : Cell -> Real) : Real :=
  ∑ cell ∈ cells,
    candidateMean cell * scoreCellMass sample weight score cell

/-- Hájek mean obtained from an externally supplied score-cell mean. -/
noncomputable def candidateCellMeanAggregate
    (sample : Finset Unit) (cells : Finset Cell)
    (weight : Unit -> Real) (score : Unit -> Cell)
    (candidateMean : Cell -> Real) : Real :=
  candidateCellMeanNumerator sample cells weight score candidateMean /
    weightedSampleTotal sample weight

theorem scoreCellMeanNumerator_eq_weightedSampleSum_of_mapsTo
    (sample : Finset Unit) (cells : Finset Cell)
    (weight outcome : Unit -> Real) (score : Unit -> Cell)
    (hcover : ∀ unit, unit ∈ sample -> score unit ∈ cells)
    (hmass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sample weight score cell ≠ 0) :
    scoreCellMeanNumerator sample cells weight outcome score =
      weightedSampleSum sample weight outcome := by
  unfold scoreCellMeanNumerator
  exact (weightedSampleSum_eq_sum_scoreCellMean_mul_mass_of_mapsTo
    sample cells weight outcome score hcover hmass).symm

theorem scoreCellMeanAggregate_eq_weightedSampleMean_of_mapsTo
    (sample : Finset Unit) (cells : Finset Cell)
    (weight outcome : Unit -> Real) (score : Unit -> Cell)
    (hcover : ∀ unit, unit ∈ sample -> score unit ∈ cells)
    (hmass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sample weight score cell ≠ 0) :
    scoreCellMeanAggregate sample cells weight outcome score =
      weightedSampleMean sample weight outcome := by
  unfold scoreCellMeanAggregate weightedSampleMean
  rw [scoreCellMeanNumerator_eq_weightedSampleSum_of_mapsTo
    sample cells weight outcome score hcover hmass]

theorem candidateCellMeanNumerator_eq_scoreCellMeanNumerator_of_eq
    (sample : Finset Unit) (cells : Finset Cell)
    (weight outcome : Unit -> Real) (score : Unit -> Cell)
    (candidateMean : Cell -> Real)
    (hcandidate :
      ∀ cell, cell ∈ cells ->
        candidateMean cell = scoreCellMean sample weight outcome score cell) :
    candidateCellMeanNumerator sample cells weight score candidateMean =
      scoreCellMeanNumerator sample cells weight outcome score := by
  unfold candidateCellMeanNumerator scoreCellMeanNumerator
  exact Finset.sum_congr rfl
    (fun cell hcell => by
      rw [hcandidate cell hcell])

theorem candidateCellMeanAggregate_eq_weightedSampleMean_of_eq
    (sample : Finset Unit) (cells : Finset Cell)
    (weight outcome : Unit -> Real) (score : Unit -> Cell)
    (candidateMean : Cell -> Real)
    (hcover : ∀ unit, unit ∈ sample -> score unit ∈ cells)
    (hmass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sample weight score cell ≠ 0)
    (hcandidate :
      ∀ cell, cell ∈ cells ->
        candidateMean cell = scoreCellMean sample weight outcome score cell) :
    candidateCellMeanAggregate sample cells weight score candidateMean =
      weightedSampleMean sample weight outcome := by
  unfold candidateCellMeanAggregate
  rw [candidateCellMeanNumerator_eq_scoreCellMeanNumerator_of_eq
    sample cells weight outcome score candidateMean hcandidate]
  exact scoreCellMeanAggregate_eq_weightedSampleMean_of_mapsTo
    sample cells weight outcome score hcover hmass

/-- Difference of two weighted finite sample means. -/
noncomputable def weightedSampleMeanContrast
    (sample : Finset Unit) (weight outcomeA outcomeB : Unit -> Real) : Real :=
  weightedSampleMean sample weight outcomeA -
    weightedSampleMean sample weight outcomeB

/-- Difference of two candidate score-cell mean aggregates. -/
noncomputable def candidateCellMeanAggregateContrast
    (sample : Finset Unit) (cells : Finset Cell)
    (weight : Unit -> Real) (score : Unit -> Cell)
    (candidateA candidateB : Cell -> Real) : Real :=
  candidateCellMeanAggregate sample cells weight score candidateA -
    candidateCellMeanAggregate sample cells weight score candidateB

theorem candidateCellMeanAggregateContrast_eq_weightedSampleMeanContrast_of_eq
    (sample : Finset Unit) (cells : Finset Cell)
    (weight outcomeA outcomeB : Unit -> Real) (score : Unit -> Cell)
    (candidateA candidateB : Cell -> Real)
    (hcover : ∀ unit, unit ∈ sample -> score unit ∈ cells)
    (hmass :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sample weight score cell ≠ 0)
    (hcandidateA :
      ∀ cell, cell ∈ cells ->
        candidateA cell = scoreCellMean sample weight outcomeA score cell)
    (hcandidateB :
      ∀ cell, cell ∈ cells ->
        candidateB cell = scoreCellMean sample weight outcomeB score cell) :
    candidateCellMeanAggregateContrast sample cells weight score
        candidateA candidateB =
      weightedSampleMeanContrast sample weight outcomeA outcomeB := by
  unfold candidateCellMeanAggregateContrast weightedSampleMeanContrast
  rw [candidateCellMeanAggregate_eq_weightedSampleMean_of_eq
    sample cells weight outcomeA score candidateA hcover hmass hcandidateA]
  rw [candidateCellMeanAggregate_eq_weightedSampleMean_of_eq
    sample cells weight outcomeB score candidateB hcover hmass hcandidateB]

end WDSM
end Matching
end StatInference
