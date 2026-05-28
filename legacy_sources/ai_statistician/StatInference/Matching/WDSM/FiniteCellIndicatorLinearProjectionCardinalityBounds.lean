import StatInference.Matching.WDSM.FiniteCellIndicatorLinearProjectionSampleBounds

/-!
# Cardinality bounds for finite linear score-cell projection envelopes

The exact centered-linear-projection envelope is a finite sum over score cells.
For later CLT assumptions it is often more convenient to expose a simple
finite-cardinality bound under bounded loadings and reference shares.
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
/--
If finite loadings are bounded by `loadingBound` and reference shares are in
absolute value at most one, then the exact projection envelope is bounded by
`#cells * (2 * loadingBound)`.
-/
theorem scoreCellLinearCenteredIndicatorEnvelope_le_card_mul_loadingBound_two
    (cells : Finset Cell) (referenceShare loading : Cell -> Real)
    (loadingBound : Real) (hloading_nonneg : 0 ≤ loadingBound)
    (hloading :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ loadingBound)
    (hshare :
      ∀ cell, cell ∈ cells -> |referenceShare cell| ≤ 1) :
    scoreCellLinearCenteredIndicatorEnvelope cells referenceShare loading ≤
      (cells.card : Real) * (loadingBound * 2) := by
  unfold scoreCellLinearCenteredIndicatorEnvelope
  calc
    (∑ cell ∈ cells, |loading cell| * (1 + |referenceShare cell|)) ≤
        ∑ _cell ∈ cells, loadingBound * 2 := by
          exact Finset.sum_le_sum
            (fun cell hcell => by
              have hshare_two : 1 + |referenceShare cell| ≤ 2 := by
                linarith [hshare cell hcell]
              have hshare_nonneg :
                  0 ≤ 1 + |referenceShare cell| :=
                add_nonneg zero_le_one (abs_nonneg (referenceShare cell))
              exact mul_le_mul (hloading cell hcell) hshare_two
                hshare_nonneg hloading_nonneg)
    _ = (cells.card : Real) * (loadingBound * 2) := by
          simp [nsmul_eq_mul]

/-- Cardinality bound for the centered finite score-cell linear projection. -/
theorem abs_scoreCellLinearCenteredIndicator_le_card_mul_loadingBound_two
    (cells : Finset Cell) (score : Unit -> Cell)
    (referenceShare loading : Cell -> Real) (unit : Unit)
    (loadingBound : Real) (hloading_nonneg : 0 ≤ loadingBound)
    (hloading :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ loadingBound)
    (hshare :
      ∀ cell, cell ∈ cells -> |referenceShare cell| ≤ 1) :
    |scoreCellLinearCenteredIndicator cells score referenceShare loading unit| ≤
      (cells.card : Real) * (loadingBound * 2) :=
  (abs_scoreCellLinearCenteredIndicator_le_envelope
    cells score referenceShare loading unit).trans
    (scoreCellLinearCenteredIndicatorEnvelope_le_card_mul_loadingBound_two
      cells referenceShare loading loadingBound hloading_nonneg hloading hshare)

/--
A weighted centered projection is bounded by absolute weight times the
finite-cardinality loading envelope.
-/
theorem
    abs_weight_mul_scoreCellLinearCenteredIndicator_le_abs_weight_mul_card_mul_loadingBound_two
    (cells : Finset Cell) (weight : Unit -> Real) (score : Unit -> Cell)
    (referenceShare loading : Cell -> Real) (unit : Unit)
    (loadingBound : Real) (hloading_nonneg : 0 ≤ loadingBound)
    (hloading :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ loadingBound)
    (hshare :
      ∀ cell, cell ∈ cells -> |referenceShare cell| ≤ 1) :
    |weight unit *
        scoreCellLinearCenteredIndicator cells score referenceShare loading
          unit| ≤
      |weight unit| * ((cells.card : Real) * (loadingBound * 2)) := by
  exact
    (abs_weight_mul_scoreCellLinearCenteredIndicator_le_abs_weight_mul_envelope
      cells weight score referenceShare loading unit).trans
      (mul_le_mul_of_nonneg_left
        (scoreCellLinearCenteredIndicatorEnvelope_le_card_mul_loadingBound_two
          cells referenceShare loading loadingBound hloading_nonneg
          hloading hshare)
        (abs_nonneg (weight unit)))

/--
The weighted sample sum is bounded by total absolute weight times the
finite-cardinality loading envelope.
-/
theorem
    abs_weightedSampleSum_scoreCellLinearCenteredIndicator_le_sum_abs_weight_mul_card_mul_loadingBound_two
    (sample : Finset Unit) (cells : Finset Cell)
    (weight : Unit -> Real) (score : Unit -> Cell)
    (referenceShare loading : Cell -> Real)
    (loadingBound : Real) (hloading_nonneg : 0 ≤ loadingBound)
    (hloading :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ loadingBound)
    (hshare :
      ∀ cell, cell ∈ cells -> |referenceShare cell| ≤ 1) :
    |weightedSampleSum sample weight
        (scoreCellLinearCenteredIndicator
          cells score referenceShare loading)| ≤
      (∑ unit ∈ sample, |weight unit|) *
        ((cells.card : Real) * (loadingBound * 2)) := by
  have hsum_nonneg : 0 ≤ ∑ unit ∈ sample, |weight unit| :=
    Finset.sum_nonneg (fun unit _hunit => abs_nonneg (weight unit))
  exact
    (abs_weightedSampleSum_scoreCellLinearCenteredIndicator_le_sum_abs_weight_mul_envelope
      sample cells weight score referenceShare loading).trans
      (mul_le_mul_of_nonneg_left
        (scoreCellLinearCenteredIndicatorEnvelope_le_card_mul_loadingBound_two
          cells referenceShare loading loadingBound hloading_nonneg
          hloading hshare)
        hsum_nonneg)

/-- PATE double-score sample bound by finite cardinality and loading bound. -/
theorem
    abs_weightedSampleSum_pateDoubleScoreLinearCenteredIndicator_le_sum_abs_weight_mul_card_mul_loadingBound_two
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
        (scoreCellLinearCenteredIndicator cells
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore)
          referenceShare loading)| ≤
      (∑ unit ∈ sample, |weight unit|) *
        ((cells.card : Real) * (loadingBound * 2)) :=
  abs_weightedSampleSum_scoreCellLinearCenteredIndicator_le_sum_abs_weight_mul_card_mul_loadingBound_two
    sample cells weight
    (pateDoubleScore propensityScore treatedPrognosticScore
      controlPrognosticScore)
    referenceShare loading loadingBound hloading_nonneg hloading hshare

/-- PATT double-score sample bound by finite cardinality and loading bound. -/
theorem
    abs_weightedSampleSum_pattDoubleScoreLinearCenteredIndicator_le_sum_abs_weight_mul_card_mul_loadingBound_two
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
        (scoreCellLinearCenteredIndicator cells
          (pattDoubleScore propensityScore controlPrognosticScore)
          referenceShare loading)| ≤
      (∑ unit ∈ sample, |weight unit|) *
        ((cells.card : Real) * (loadingBound * 2)) :=
  abs_weightedSampleSum_scoreCellLinearCenteredIndicator_le_sum_abs_weight_mul_card_mul_loadingBound_two
    sample cells weight (pattDoubleScore propensityScore controlPrognosticScore)
    referenceShare loading loadingBound hloading_nonneg hloading hshare

end WDSM
end Matching
end StatInference
