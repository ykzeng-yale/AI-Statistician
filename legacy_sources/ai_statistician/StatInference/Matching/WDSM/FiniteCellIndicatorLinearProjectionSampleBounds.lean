import StatInference.Matching.WDSM.FiniteCellIndicatorLinearProjectionBounds

/-!
# Sample bounds for finite linear score-cell indicator projections

Pointwise envelopes for centered finite score-cell linear projections imply
finite-sample bounds for the corresponding weighted sums.  These estimates are
the deterministic sample-level bounds needed before supplying LLN/CLT
arguments for the projected indicator arrays.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit Cell PropensityCell TreatedProgCell ControlProgCell PATTProgCell : Type*}
  [DecidableEq Cell] [DecidableEq PropensityCell]
  [DecidableEq TreatedProgCell] [DecidableEq ControlProgCell]
  [DecidableEq PATTProgCell]

/--
The absolute weighted sample sum of a centered finite score-cell linear
projection is bounded by the total absolute weight times the loading envelope.
-/
theorem
    abs_weightedSampleSum_scoreCellLinearCenteredIndicator_le_sum_abs_weight_mul_envelope
    (sample : Finset Unit) (cells : Finset Cell)
    (weight : Unit -> Real) (score : Unit -> Cell)
    (referenceShare loading : Cell -> Real) :
    |weightedSampleSum sample weight
        (scoreCellLinearCenteredIndicator
          cells score referenceShare loading)| ≤
      (∑ unit ∈ sample, |weight unit|) *
        scoreCellLinearCenteredIndicatorEnvelope
          cells referenceShare loading := by
  unfold weightedSampleSum
  calc
    |∑ unit ∈ sample,
        weight unit *
          scoreCellLinearCenteredIndicator
            cells score referenceShare loading unit| ≤
        ∑ unit ∈ sample,
          |weight unit *
            scoreCellLinearCenteredIndicator
              cells score referenceShare loading unit| := by
          exact Finset.abs_sum_le_sum_abs _ _
    _ ≤
        ∑ unit ∈ sample,
          |weight unit| *
            scoreCellLinearCenteredIndicatorEnvelope
              cells referenceShare loading := by
          exact Finset.sum_le_sum
            (fun unit _hunit =>
              abs_weight_mul_scoreCellLinearCenteredIndicator_le_abs_weight_mul_envelope
                cells weight score referenceShare loading unit)
    _ =
        (∑ unit ∈ sample, |weight unit|) *
          scoreCellLinearCenteredIndicatorEnvelope
            cells referenceShare loading := by
          rw [Finset.sum_mul]

/--
If the total absolute sample weight is bounded, then the weighted sample sum is
bounded by that total-weight bound times the loading envelope.
-/
theorem
    abs_weightedSampleSum_scoreCellLinearCenteredIndicator_le_bound_mul_envelope
    (sample : Finset Unit) (cells : Finset Cell)
    (weight : Unit -> Real) (score : Unit -> Cell)
    (referenceShare loading : Cell -> Real) (weightTotalBound : Real)
    (hweight :
      (∑ unit ∈ sample, |weight unit|) ≤ weightTotalBound) :
    |weightedSampleSum sample weight
        (scoreCellLinearCenteredIndicator
          cells score referenceShare loading)| ≤
      weightTotalBound *
        scoreCellLinearCenteredIndicatorEnvelope
          cells referenceShare loading := by
  exact
    (abs_weightedSampleSum_scoreCellLinearCenteredIndicator_le_sum_abs_weight_mul_envelope
      sample cells weight score referenceShare loading).trans
      (mul_le_mul_of_nonneg_right hweight
        (scoreCellLinearCenteredIndicatorEnvelope_nonneg
          cells referenceShare loading))

/-- PATE double-score sample bound by total absolute weight. -/
theorem
    abs_weightedSampleSum_pateDoubleScoreLinearCenteredIndicator_le_sum_abs_weight_mul_envelope
    (sample : Finset Unit)
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (weight : Unit -> Real)
    (propensityScore : Unit -> PropensityCell)
    (treatedPrognosticScore : Unit -> TreatedProgCell)
    (controlPrognosticScore : Unit -> ControlProgCell)
    (referenceShare loading :
      ((PropensityCell × TreatedProgCell) × ControlProgCell) -> Real) :
    |weightedSampleSum sample weight
        (scoreCellLinearCenteredIndicator cells
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore)
          referenceShare loading)| ≤
      (∑ unit ∈ sample, |weight unit|) *
        scoreCellLinearCenteredIndicatorEnvelope
          cells referenceShare loading :=
  abs_weightedSampleSum_scoreCellLinearCenteredIndicator_le_sum_abs_weight_mul_envelope
    sample cells weight
    (pateDoubleScore propensityScore treatedPrognosticScore
      controlPrognosticScore)
    referenceShare loading

/-- PATT double-score sample bound by total absolute weight. -/
theorem
    abs_weightedSampleSum_pattDoubleScoreLinearCenteredIndicator_le_sum_abs_weight_mul_envelope
    (sample : Finset Unit) (cells : Finset (PropensityCell × PATTProgCell))
    (weight : Unit -> Real)
    (propensityScore : Unit -> PropensityCell)
    (controlPrognosticScore : Unit -> PATTProgCell)
    (referenceShare loading : (PropensityCell × PATTProgCell) -> Real) :
    |weightedSampleSum sample weight
        (scoreCellLinearCenteredIndicator cells
          (pattDoubleScore propensityScore controlPrognosticScore)
          referenceShare loading)| ≤
      (∑ unit ∈ sample, |weight unit|) *
        scoreCellLinearCenteredIndicatorEnvelope
          cells referenceShare loading :=
  abs_weightedSampleSum_scoreCellLinearCenteredIndicator_le_sum_abs_weight_mul_envelope
    sample cells weight
    (pattDoubleScore propensityScore controlPrognosticScore)
    referenceShare loading

/-- PATE double-score sample bound from a total absolute-weight bound. -/
theorem
    abs_weightedSampleSum_pateDoubleScoreLinearCenteredIndicator_le_bound_mul_envelope
    (sample : Finset Unit)
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (weight : Unit -> Real)
    (propensityScore : Unit -> PropensityCell)
    (treatedPrognosticScore : Unit -> TreatedProgCell)
    (controlPrognosticScore : Unit -> ControlProgCell)
    (referenceShare loading :
      ((PropensityCell × TreatedProgCell) × ControlProgCell) -> Real)
    (weightTotalBound : Real)
    (hweight :
      (∑ unit ∈ sample, |weight unit|) ≤ weightTotalBound) :
    |weightedSampleSum sample weight
        (scoreCellLinearCenteredIndicator cells
          (pateDoubleScore propensityScore treatedPrognosticScore
            controlPrognosticScore)
          referenceShare loading)| ≤
      weightTotalBound *
        scoreCellLinearCenteredIndicatorEnvelope
          cells referenceShare loading :=
  abs_weightedSampleSum_scoreCellLinearCenteredIndicator_le_bound_mul_envelope
    sample cells weight
    (pateDoubleScore propensityScore treatedPrognosticScore
      controlPrognosticScore)
    referenceShare loading weightTotalBound hweight

/-- PATT double-score sample bound from a total absolute-weight bound. -/
theorem
    abs_weightedSampleSum_pattDoubleScoreLinearCenteredIndicator_le_bound_mul_envelope
    (sample : Finset Unit) (cells : Finset (PropensityCell × PATTProgCell))
    (weight : Unit -> Real)
    (propensityScore : Unit -> PropensityCell)
    (controlPrognosticScore : Unit -> PATTProgCell)
    (referenceShare loading : (PropensityCell × PATTProgCell) -> Real)
    (weightTotalBound : Real)
    (hweight :
      (∑ unit ∈ sample, |weight unit|) ≤ weightTotalBound) :
    |weightedSampleSum sample weight
        (scoreCellLinearCenteredIndicator cells
          (pattDoubleScore propensityScore controlPrognosticScore)
          referenceShare loading)| ≤
      weightTotalBound *
        scoreCellLinearCenteredIndicatorEnvelope
          cells referenceShare loading :=
  abs_weightedSampleSum_scoreCellLinearCenteredIndicator_le_bound_mul_envelope
    sample cells weight
    (pattDoubleScore propensityScore controlPrognosticScore)
    referenceShare loading weightTotalBound hweight

end WDSM
end Matching
end StatInference
