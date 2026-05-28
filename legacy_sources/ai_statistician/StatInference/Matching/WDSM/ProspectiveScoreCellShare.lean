import StatInference.Matching.WDSM.ProspectiveWeightedSampleMean
import StatInference.Matching.WDSM.DiscreteBalancingAlgebra

/-!
# Prospective/common-weight score-cell shares for WDSM

This module proves that, under a common survey weight, finite WDSM score-cell
masses and normalized score-cell shares reduce to ordinary finite cell counts
and cell-count ratios.  This is the deterministic bridge from survey-weighted
score-cell shares to the unweighted fixed-cell proportions used by prospective
sampling arguments.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit Cell : Type*} [DecidableEq Cell]

/-- A constant survey weight factors out of a finite score-cell mass. -/
theorem scoreCellMass_constant_weight_eq
    (sample : Finset Unit) (score : Unit -> Cell) (cell : Cell)
    (commonWeight : Real) :
    scoreCellMass sample (fun _unit => commonWeight) score cell =
      commonWeight *
        (∑ unit ∈ sample with score unit = cell, (1 : Real)) := by
  unfold scoreCellMass
  calc
    (∑ unit ∈ sample with score unit = cell, commonWeight) =
        (∑ unit ∈ sample with score unit = cell,
          commonWeight * (1 : Real)) := by
          exact Finset.sum_congr rfl
            (fun _unit _hunit => by ring)
    _ = commonWeight *
        (∑ unit ∈ sample with score unit = cell, (1 : Real)) := by
          rw [← Finset.mul_sum]

/-- The finite unit mass of a score cell is its finite cardinality. -/
theorem finiteScoreCellUnitMass_eq_card
    (sample : Finset Unit) (score : Unit -> Cell) (cell : Cell) :
    (∑ unit ∈ sample with score unit = cell, (1 : Real)) =
      ((sample.filter (fun unit => score unit = cell)).card : Real) := by
  simp

/-- A constant survey weight makes a score-cell mass equal weight times count. -/
theorem scoreCellMass_constant_weight_eq_card
    (sample : Finset Unit) (score : Unit -> Cell) (cell : Cell)
    (commonWeight : Real) :
    scoreCellMass sample (fun _unit => commonWeight) score cell =
      commonWeight *
        ((sample.filter (fun unit => score unit = cell)).card : Real) := by
  rw [scoreCellMass_constant_weight_eq,
    finiteScoreCellUnitMass_eq_card]

/--
With a nonzero common survey weight and nonzero finite unit mass, a WDSM
score-cell share is the ordinary finite cell-count ratio written with `sum 1`.
-/
theorem scoreCellShare_constant_weight_eq_unit_mass_ratio
    (sample : Finset Unit) (score : Unit -> Cell) (cell : Cell)
    (commonWeight : Real)
    (hweight : commonWeight ≠ 0)
    (hmass : (∑ _unit ∈ sample, (1 : Real)) ≠ 0) :
    scoreCellShare sample (fun _unit => commonWeight) score cell =
      (∑ unit ∈ sample with score unit = cell, (1 : Real)) /
        (∑ _unit ∈ sample, (1 : Real)) := by
  unfold scoreCellShare
  rw [scoreCellMass_constant_weight_eq]
  rw [weightedSampleTotal_eq_weightedDenominator]
  rw [weightedDenominator_constant_weight_eq]
  field_simp [hweight, hmass]

/--
With a nonzero common survey weight and nonzero sample cardinality, a WDSM
score-cell share is the ordinary finite cell-count ratio.
-/
theorem scoreCellShare_constant_weight_eq_card_ratio
    (sample : Finset Unit) (score : Unit -> Cell) (cell : Cell)
    (commonWeight : Real)
    (hweight : commonWeight ≠ 0)
    (hcard : (sample.card : Real) ≠ 0) :
    scoreCellShare sample (fun _unit => commonWeight) score cell =
      ((sample.filter (fun unit => score unit = cell)).card : Real) /
        (sample.card : Real) := by
  rw [scoreCellShare_constant_weight_eq_unit_mass_ratio
    sample score cell commonWeight hweight _]
  · rw [finiteScoreCellUnitMass_eq_card, finiteUnitMass_eq_card]
  · simpa [finiteUnitMass_eq_card] using hcard

/--
With a nonzero common survey weight and a nonempty sample, a WDSM score-cell
share is the ordinary finite cell-count ratio.
-/
theorem scoreCellShare_constant_weight_eq_card_ratio_of_nonempty
    (sample : Finset Unit) (score : Unit -> Cell) (cell : Cell)
    (commonWeight : Real)
    (hweight : commonWeight ≠ 0)
    (hnonempty : sample.Nonempty) :
    scoreCellShare sample (fun _unit => commonWeight) score cell =
      ((sample.filter (fun unit => score unit = cell)).card : Real) /
        (sample.card : Real) :=
  scoreCellShare_constant_weight_eq_card_ratio sample score cell commonWeight
    hweight (sampleCard_ne_zero_of_nonempty sample hnonempty)

/--
Positive common survey weights are enough for the nonempty score-cell count
ratio specialization.
-/
theorem scoreCellShare_constant_weight_eq_card_ratio_of_pos_nonempty
    (sample : Finset Unit) (score : Unit -> Cell) (cell : Cell)
    (commonWeight : Real)
    (hweight_pos : 0 < commonWeight)
    (hnonempty : sample.Nonempty) :
    scoreCellShare sample (fun _unit => commonWeight) score cell =
      ((sample.filter (fun unit => score unit = cell)).card : Real) /
        (sample.card : Real) :=
  scoreCellShare_constant_weight_eq_card_ratio_of_nonempty sample score cell
    commonWeight hweight_pos.ne' hnonempty

end WDSM
end Matching
end StatInference
