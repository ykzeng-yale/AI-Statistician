import StatInference.Matching.WDSM.DiscreteMeanRecovery

/-!
# Discrete score-cell balancing algebra for WDSM

This module proves the deterministic finite algebra behind a discrete
balancing route.  If two weighted samples have the same normalized score-cell
shares and a common candidate score-cell mean function, their candidate
score-cell aggregates are equal.  If that candidate function is also equal to
each sample's true finite score-cell mean, then the two survey-weighted sample
means agree.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit UnitA UnitB Cell : Type*} [DecidableEq Cell]

/-- Normalized weighted mass of one discrete score cell. -/
noncomputable def scoreCellShare
    (sample : Finset Unit) (weight : Unit -> Real)
    (score : Unit -> Cell) (cell : Cell) : Real :=
  scoreCellMass sample weight score cell / weightedSampleTotal sample weight

/-- Candidate-cell aggregate written directly in normalized-share form. -/
noncomputable def candidateCellMeanShareAggregate
    (sample : Finset Unit) (cells : Finset Cell)
    (weight : Unit -> Real) (score : Unit -> Cell)
    (candidateMean : Cell -> Real) : Real :=
  ∑ cell ∈ cells,
    candidateMean cell * scoreCellShare sample weight score cell

theorem sum_scoreCellShare_eq_one_of_mapsTo
    (sample : Finset Unit) (cells : Finset Cell)
    (weight : Unit -> Real) (score : Unit -> Cell)
    (hcover : ∀ unit, unit ∈ sample -> score unit ∈ cells)
    (htotal : weightedSampleTotal sample weight ≠ 0) :
    (∑ cell ∈ cells, scoreCellShare sample weight score cell) = 1 := by
  unfold scoreCellShare
  rw [← Finset.sum_div]
  rw [sum_scoreCellMass_eq_weightedSampleTotal_of_mapsTo
    sample cells weight score hcover]
  exact div_self htotal

theorem scoreCellShare_nonneg
    (sample : Finset Unit) (weight : Unit -> Real)
    (score : Unit -> Cell) (cell : Cell)
    (htotal_nonneg : 0 ≤ weightedSampleTotal sample weight)
    (hweight :
      ∀ unit, unit ∈ sample -> score unit = cell -> 0 ≤ weight unit) :
    0 ≤ scoreCellShare sample weight score cell := by
  unfold scoreCellShare
  exact div_nonneg
    (scoreCellMass_nonneg sample weight score cell hweight)
    htotal_nonneg

theorem candidateCellMeanAggregate_eq_candidateCellMeanShareAggregate
    (sample : Finset Unit) (cells : Finset Cell)
    (weight : Unit -> Real) (score : Unit -> Cell)
    (candidateMean : Cell -> Real) :
    candidateCellMeanAggregate sample cells weight score candidateMean =
      candidateCellMeanShareAggregate sample cells weight score
        candidateMean := by
  unfold candidateCellMeanAggregate candidateCellMeanNumerator
    candidateCellMeanShareAggregate scoreCellShare
  calc
    (∑ cell ∈ cells,
        candidateMean cell * scoreCellMass sample weight score cell) /
        weightedSampleTotal sample weight =
        ∑ cell ∈ cells,
          (candidateMean cell * scoreCellMass sample weight score cell) /
            weightedSampleTotal sample weight := by
          rw [Finset.sum_div]
    _ = ∑ cell ∈ cells,
          candidateMean cell *
            (scoreCellMass sample weight score cell /
              weightedSampleTotal sample weight) := by
        exact Finset.sum_congr rfl
          (fun cell _ => by ring)

theorem candidateCellMeanShareAggregate_eq_of_scoreCellShare_eq
    (sampleA : Finset UnitA) (sampleB : Finset UnitB)
    (cells : Finset Cell)
    (weightA : UnitA -> Real) (weightB : UnitB -> Real)
    (scoreA : UnitA -> Cell) (scoreB : UnitB -> Cell)
    (candidateMean : Cell -> Real)
    (hshare :
      ∀ cell, cell ∈ cells ->
        scoreCellShare sampleA weightA scoreA cell =
          scoreCellShare sampleB weightB scoreB cell) :
    candidateCellMeanShareAggregate sampleA cells weightA scoreA
        candidateMean =
      candidateCellMeanShareAggregate sampleB cells weightB scoreB
        candidateMean := by
  unfold candidateCellMeanShareAggregate
  exact Finset.sum_congr rfl
    (fun cell hcell => by
      rw [hshare cell hcell])

theorem candidateCellMeanAggregate_eq_of_scoreCellShare_eq
    (sampleA : Finset UnitA) (sampleB : Finset UnitB)
    (cells : Finset Cell)
    (weightA : UnitA -> Real) (weightB : UnitB -> Real)
    (scoreA : UnitA -> Cell) (scoreB : UnitB -> Cell)
    (candidateMean : Cell -> Real)
    (hshare :
      ∀ cell, cell ∈ cells ->
        scoreCellShare sampleA weightA scoreA cell =
          scoreCellShare sampleB weightB scoreB cell) :
    candidateCellMeanAggregate sampleA cells weightA scoreA
        candidateMean =
      candidateCellMeanAggregate sampleB cells weightB scoreB
        candidateMean := by
  rw [candidateCellMeanAggregate_eq_candidateCellMeanShareAggregate
    sampleA cells weightA scoreA candidateMean]
  rw [candidateCellMeanAggregate_eq_candidateCellMeanShareAggregate
    sampleB cells weightB scoreB candidateMean]
  exact candidateCellMeanShareAggregate_eq_of_scoreCellShare_eq
    sampleA sampleB cells weightA weightB scoreA scoreB candidateMean hshare

/--
Finite discrete balancing theorem: equal score-cell shares plus a common
candidate cell-mean function that equals each sample's finite cell mean imply
equality of the two survey-weighted sample means.
-/
theorem weightedSampleMean_eq_of_scoreCellShare_eq_and_candidateCellMean_eq
    (sampleA : Finset UnitA) (sampleB : Finset UnitB)
    (cells : Finset Cell)
    (weightA : UnitA -> Real) (weightB : UnitB -> Real)
    (outcomeA : UnitA -> Real) (outcomeB : UnitB -> Real)
    (scoreA : UnitA -> Cell) (scoreB : UnitB -> Cell)
    (candidateMean : Cell -> Real)
    (hcoverA : ∀ unit, unit ∈ sampleA -> scoreA unit ∈ cells)
    (hcoverB : ∀ unit, unit ∈ sampleB -> scoreB unit ∈ cells)
    (hmassA :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sampleA weightA scoreA cell ≠ 0)
    (hmassB :
      ∀ cell, cell ∈ cells ->
        scoreCellMass sampleB weightB scoreB cell ≠ 0)
    (hshare :
      ∀ cell, cell ∈ cells ->
        scoreCellShare sampleA weightA scoreA cell =
          scoreCellShare sampleB weightB scoreB cell)
    (hcandidateA :
      ∀ cell, cell ∈ cells ->
        candidateMean cell =
          scoreCellMean sampleA weightA outcomeA scoreA cell)
    (hcandidateB :
      ∀ cell, cell ∈ cells ->
        candidateMean cell =
          scoreCellMean sampleB weightB outcomeB scoreB cell) :
    weightedSampleMean sampleA weightA outcomeA =
      weightedSampleMean sampleB weightB outcomeB := by
  calc
    weightedSampleMean sampleA weightA outcomeA =
        candidateCellMeanAggregate sampleA cells weightA scoreA
          candidateMean := by
          exact (candidateCellMeanAggregate_eq_weightedSampleMean_of_eq
            sampleA cells weightA outcomeA scoreA candidateMean
            hcoverA hmassA hcandidateA).symm
    _ = candidateCellMeanAggregate sampleB cells weightB scoreB
          candidateMean := by
          exact candidateCellMeanAggregate_eq_of_scoreCellShare_eq
            sampleA sampleB cells weightA weightB scoreA scoreB
            candidateMean hshare
    _ = weightedSampleMean sampleB weightB outcomeB := by
          exact candidateCellMeanAggregate_eq_weightedSampleMean_of_eq
            sampleB cells weightB outcomeB scoreB candidateMean
            hcoverB hmassB hcandidateB

end WDSM
end Matching
end StatInference
