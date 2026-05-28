import StatInference.Matching.WDSM.FiniteCellIndicatorLinearProjectionCardinalityBounds
import StatInference.Matching.WDSM.FiniteCellIndicatorLinearProjectionMomentBounds

/-!
# Cardinality moment bounds for finite linear score-cell projections

This module combines the finite-cardinality envelope from
`FiniteCellIndicatorLinearProjectionCardinalityBounds` with the square/moment
bounds from `FiniteCellIndicatorLinearProjectionMomentBounds`.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit Cell PropensityCell TreatedProgCell ControlProgCell PATTProgCell : Type*}
  [DecidableEq Cell] [DecidableEq PropensityCell]
  [DecidableEq TreatedProgCell] [DecidableEq ControlProgCell]
  [DecidableEq PATTProgCell]

omit [DecidableEq Cell] in
/-- The finite-cardinality loading envelope is nonnegative. -/
theorem card_mul_loadingBound_two_nonneg
    (cells : Finset Cell) (loadingBound : Real)
    (hloading_nonneg : 0 ≤ loadingBound) :
    0 ≤ (cells.card : Real) * (loadingBound * 2) := by
  have hcard_nonneg : 0 ≤ (cells.card : Real) := by
    exact_mod_cast Nat.zero_le cells.card
  exact mul_nonneg hcard_nonneg
    (mul_nonneg hloading_nonneg (by norm_num))

/--
The squared centered projection is bounded by the squared finite-cardinality
loading envelope.
-/
theorem
    abs_scoreCellLinearCenteredIndicator_mul_self_le_card_mul_loadingBound_two_sq
    (cells : Finset Cell) (score : Unit -> Cell)
    (referenceShare loading : Cell -> Real) (unit : Unit)
    (loadingBound : Real) (hloading_nonneg : 0 ≤ loadingBound)
    (hloading :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ loadingBound)
    (hshare :
      ∀ cell, cell ∈ cells -> |referenceShare cell| ≤ 1) :
    |scoreCellLinearCenteredIndicator cells score referenceShare loading unit *
        scoreCellLinearCenteredIndicator cells score referenceShare loading
          unit| ≤
      ((cells.card : Real) * (loadingBound * 2)) ^ 2 := by
  let projection :=
    scoreCellLinearCenteredIndicator cells score referenceShare loading unit
  let cardEnvelope := (cells.card : Real) * (loadingBound * 2)
  have hprojection : |projection| ≤ cardEnvelope := by
    dsimp [projection, cardEnvelope]
    exact abs_scoreCellLinearCenteredIndicator_le_card_mul_loadingBound_two
      cells score referenceShare loading unit loadingBound hloading_nonneg
      hloading hshare
  have hcardEnvelope : 0 ≤ cardEnvelope := by
    dsimp [cardEnvelope]
    exact card_mul_loadingBound_two_nonneg cells loadingBound hloading_nonneg
  have hdiff :
      0 ≤ (cardEnvelope - |projection|) *
        (cardEnvelope + |projection|) := by
    exact mul_nonneg (sub_nonneg.mpr hprojection)
      (add_nonneg hcardEnvelope (abs_nonneg projection))
  have hsquare : |projection| * |projection| ≤ cardEnvelope ^ 2 := by
    nlinarith
  calc
    |scoreCellLinearCenteredIndicator cells score referenceShare loading unit *
        scoreCellLinearCenteredIndicator cells score referenceShare loading
          unit| =
        |projection * projection| := by
          rfl
    _ = |projection| * |projection| := by
          rw [abs_mul]
    _ ≤ cardEnvelope ^ 2 := hsquare

/--
Weighted squared projections are bounded by absolute weight times the squared
finite-cardinality loading envelope.
-/
theorem
    abs_weight_mul_scoreCellLinearCenteredIndicator_mul_self_le_abs_weight_mul_card_mul_loadingBound_two_sq
    (cells : Finset Cell) (weight : Unit -> Real) (score : Unit -> Cell)
    (referenceShare loading : Cell -> Real) (unit : Unit)
    (loadingBound : Real) (hloading_nonneg : 0 ≤ loadingBound)
    (hloading :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ loadingBound)
    (hshare :
      ∀ cell, cell ∈ cells -> |referenceShare cell| ≤ 1) :
    |weight unit *
        (scoreCellLinearCenteredIndicator cells score referenceShare loading
            unit *
          scoreCellLinearCenteredIndicator cells score referenceShare loading
            unit)| ≤
      |weight unit| *
        ((cells.card : Real) * (loadingBound * 2)) ^ 2 := by
  calc
    |weight unit *
        (scoreCellLinearCenteredIndicator cells score referenceShare loading
            unit *
          scoreCellLinearCenteredIndicator cells score referenceShare loading
            unit)| =
        |weight unit| *
          |scoreCellLinearCenteredIndicator
              cells score referenceShare loading unit *
            scoreCellLinearCenteredIndicator
              cells score referenceShare loading unit| := by
          rw [abs_mul]
    _ ≤
        |weight unit| *
          ((cells.card : Real) * (loadingBound * 2)) ^ 2 := by
          exact mul_le_mul_of_nonneg_left
            (abs_scoreCellLinearCenteredIndicator_mul_self_le_card_mul_loadingBound_two_sq
              cells score referenceShare loading unit loadingBound
              hloading_nonneg hloading hshare)
            (abs_nonneg (weight unit))

/--
The weighted sample sum of squared centered projections is bounded by total
absolute weight times the squared finite-cardinality loading envelope.
-/
theorem
    abs_weightedSampleSum_scoreCellLinearCenteredIndicator_mul_self_le_sum_abs_weight_mul_card_mul_loadingBound_two_sq
    (sample : Finset Unit) (cells : Finset Cell)
    (weight : Unit -> Real) (score : Unit -> Cell)
    (referenceShare loading : Cell -> Real)
    (loadingBound : Real) (hloading_nonneg : 0 ≤ loadingBound)
    (hloading :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ loadingBound)
    (hshare :
      ∀ cell, cell ∈ cells -> |referenceShare cell| ≤ 1) :
    |weightedSampleSum sample weight
        (fun unit =>
          scoreCellLinearCenteredIndicator cells score referenceShare loading
              unit *
            scoreCellLinearCenteredIndicator cells score referenceShare loading
              unit)| ≤
      (∑ unit ∈ sample, |weight unit|) *
        ((cells.card : Real) * (loadingBound * 2)) ^ 2 := by
  unfold weightedSampleSum
  calc
    |∑ unit ∈ sample,
        weight unit *
          (scoreCellLinearCenteredIndicator cells score referenceShare loading
              unit *
            scoreCellLinearCenteredIndicator cells score referenceShare loading
              unit)| ≤
        ∑ unit ∈ sample,
          |weight unit *
            (scoreCellLinearCenteredIndicator cells score referenceShare loading
                unit *
              scoreCellLinearCenteredIndicator cells score referenceShare loading
                unit)| := by
          exact Finset.abs_sum_le_sum_abs _ _
    _ ≤
        ∑ unit ∈ sample,
          |weight unit| *
            ((cells.card : Real) * (loadingBound * 2)) ^ 2 := by
          exact Finset.sum_le_sum
            (fun unit _hunit =>
              abs_weight_mul_scoreCellLinearCenteredIndicator_mul_self_le_abs_weight_mul_card_mul_loadingBound_two_sq
                cells weight score referenceShare loading unit loadingBound
                hloading_nonneg hloading hshare)
    _ =
        (∑ unit ∈ sample, |weight unit|) *
          ((cells.card : Real) * (loadingBound * 2)) ^ 2 := by
          rw [Finset.sum_mul]

/-- PATE double-score cardinality second-moment sample bound. -/
theorem
    abs_weightedSampleSum_pateDoubleScoreLinearCenteredIndicator_mul_self_le_sum_abs_weight_mul_card_mul_loadingBound_two_sq
    (sample : Finset Unit)
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (weight : Unit -> Real)
    (propensityScore : Unit -> PropensityCell)
    (treatedPrognosticScore : Unit -> TreatedProgCell)
    (controlPrognosticScore : Unit -> ControlProgCell)
    (referenceShare loading :
      ((PropensityCell × TreatedProgCell) × ControlProgCell) -> Real)
    (loadingBound : Real) (hloading_nonneg : 0 ≤ loadingBound)
    (hloading :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ loadingBound)
    (hshare :
      ∀ cell, cell ∈ cells -> |referenceShare cell| ≤ 1) :
    |weightedSampleSum sample weight
        (fun unit =>
          scoreCellLinearCenteredIndicator cells
              (pateDoubleScore propensityScore treatedPrognosticScore
                controlPrognosticScore)
              referenceShare loading unit *
            scoreCellLinearCenteredIndicator cells
              (pateDoubleScore propensityScore treatedPrognosticScore
                controlPrognosticScore)
              referenceShare loading unit)| ≤
      (∑ unit ∈ sample, |weight unit|) *
        ((cells.card : Real) * (loadingBound * 2)) ^ 2 :=
  abs_weightedSampleSum_scoreCellLinearCenteredIndicator_mul_self_le_sum_abs_weight_mul_card_mul_loadingBound_two_sq
    sample cells weight
    (pateDoubleScore propensityScore treatedPrognosticScore
      controlPrognosticScore)
    referenceShare loading loadingBound hloading_nonneg hloading hshare

/-- PATT double-score cardinality second-moment sample bound. -/
theorem
    abs_weightedSampleSum_pattDoubleScoreLinearCenteredIndicator_mul_self_le_sum_abs_weight_mul_card_mul_loadingBound_two_sq
    (sample : Finset Unit) (cells : Finset (PropensityCell × PATTProgCell))
    (weight : Unit -> Real)
    (propensityScore : Unit -> PropensityCell)
    (controlPrognosticScore : Unit -> PATTProgCell)
    (referenceShare loading : (PropensityCell × PATTProgCell) -> Real)
    (loadingBound : Real) (hloading_nonneg : 0 ≤ loadingBound)
    (hloading :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ loadingBound)
    (hshare :
      ∀ cell, cell ∈ cells -> |referenceShare cell| ≤ 1) :
    |weightedSampleSum sample weight
        (fun unit =>
          scoreCellLinearCenteredIndicator cells
              (pattDoubleScore propensityScore controlPrognosticScore)
              referenceShare loading unit *
            scoreCellLinearCenteredIndicator cells
              (pattDoubleScore propensityScore controlPrognosticScore)
              referenceShare loading unit)| ≤
      (∑ unit ∈ sample, |weight unit|) *
        ((cells.card : Real) * (loadingBound * 2)) ^ 2 :=
  abs_weightedSampleSum_scoreCellLinearCenteredIndicator_mul_self_le_sum_abs_weight_mul_card_mul_loadingBound_two_sq
    sample cells weight
    (pattDoubleScore propensityScore controlPrognosticScore)
    referenceShare loading loadingBound hloading_nonneg hloading hshare

end WDSM
end Matching
end StatInference
