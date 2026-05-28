import StatInference.Matching.WDSM.FiniteCellIndicatorLinearProjectionSampleBounds

/-!
# Moment bounds for finite linear score-cell indicator projections

The sample-level CLT route also needs deterministic square envelopes for
finite centered score-cell linear projections.  This module turns the absolute
projection envelope into pointwise and weighted-sample second-moment bounds.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter
open scoped BigOperators

variable {Unit Cell PropensityCell TreatedProgCell ControlProgCell PATTProgCell : Type*}
  [DecidableEq Cell] [DecidableEq PropensityCell]
  [DecidableEq TreatedProgCell] [DecidableEq ControlProgCell]
  [DecidableEq PATTProgCell]

/--
The square of a centered finite score-cell linear projection is bounded by the
square of its deterministic loading envelope.
-/
theorem abs_scoreCellLinearCenteredIndicator_mul_self_le_envelope_sq
    (cells : Finset Cell) (score : Unit -> Cell)
    (referenceShare loading : Cell -> Real) (unit : Unit) :
    |scoreCellLinearCenteredIndicator cells score referenceShare loading unit *
        scoreCellLinearCenteredIndicator cells score referenceShare loading
          unit| ≤
      scoreCellLinearCenteredIndicatorEnvelope
        cells referenceShare loading ^ 2 := by
  let projection :=
    scoreCellLinearCenteredIndicator cells score referenceShare loading unit
  let envelope :=
    scoreCellLinearCenteredIndicatorEnvelope cells referenceShare loading
  have hprojection : |projection| ≤ envelope := by
    dsimp [projection, envelope]
    exact abs_scoreCellLinearCenteredIndicator_le_envelope
      cells score referenceShare loading unit
  have henvelope : 0 ≤ envelope := by
    dsimp [envelope]
    exact scoreCellLinearCenteredIndicatorEnvelope_nonneg
      cells referenceShare loading
  have hdiff :
      0 ≤ (envelope - |projection|) * (envelope + |projection|) := by
    exact mul_nonneg (sub_nonneg.mpr hprojection)
      (add_nonneg henvelope (abs_nonneg projection))
  have hsquare : |projection| * |projection| ≤ envelope ^ 2 := by
    nlinarith
  calc
    |scoreCellLinearCenteredIndicator cells score referenceShare loading unit *
        scoreCellLinearCenteredIndicator cells score referenceShare loading
          unit| =
        |projection * projection| := by
          rfl
    _ = |projection| * |projection| := by
          rw [abs_mul]
    _ ≤ envelope ^ 2 := hsquare

/--
A weighted squared centered linear projection is bounded by absolute weight
times the squared loading envelope.
-/
theorem
    abs_weight_mul_scoreCellLinearCenteredIndicator_mul_self_le_abs_weight_mul_envelope_sq
    (cells : Finset Cell) (weight : Unit -> Real) (score : Unit -> Cell)
    (referenceShare loading : Cell -> Real) (unit : Unit) :
    |weight unit *
        (scoreCellLinearCenteredIndicator cells score referenceShare loading
            unit *
          scoreCellLinearCenteredIndicator cells score referenceShare loading
            unit)| ≤
      |weight unit| *
        scoreCellLinearCenteredIndicatorEnvelope
          cells referenceShare loading ^ 2 := by
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
          scoreCellLinearCenteredIndicatorEnvelope
            cells referenceShare loading ^ 2 := by
          exact mul_le_mul_of_nonneg_left
            (abs_scoreCellLinearCenteredIndicator_mul_self_le_envelope_sq
              cells score referenceShare loading unit)
            (abs_nonneg (weight unit))

/--
The absolute weighted sample sum of squared centered finite score-cell linear
projections is bounded by total absolute weight times the squared envelope.
-/
theorem
    abs_weightedSampleSum_scoreCellLinearCenteredIndicator_mul_self_le_sum_abs_weight_mul_envelope_sq
    (sample : Finset Unit) (cells : Finset Cell)
    (weight : Unit -> Real) (score : Unit -> Cell)
    (referenceShare loading : Cell -> Real) :
    |weightedSampleSum sample weight
        (fun unit =>
          scoreCellLinearCenteredIndicator cells score referenceShare loading
              unit *
            scoreCellLinearCenteredIndicator cells score referenceShare loading
              unit)| ≤
      (∑ unit ∈ sample, |weight unit|) *
        scoreCellLinearCenteredIndicatorEnvelope
          cells referenceShare loading ^ 2 := by
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
            scoreCellLinearCenteredIndicatorEnvelope
              cells referenceShare loading ^ 2 := by
          exact Finset.sum_le_sum
            (fun unit _hunit =>
              abs_weight_mul_scoreCellLinearCenteredIndicator_mul_self_le_abs_weight_mul_envelope_sq
                cells weight score referenceShare loading unit)
    _ =
        (∑ unit ∈ sample, |weight unit|) *
          scoreCellLinearCenteredIndicatorEnvelope
            cells referenceShare loading ^ 2 := by
          rw [Finset.sum_mul]

/-- Sample second-moment bound from a total absolute-weight bound. -/
theorem
    abs_weightedSampleSum_scoreCellLinearCenteredIndicator_mul_self_le_bound_mul_envelope_sq
    (sample : Finset Unit) (cells : Finset Cell)
    (weight : Unit -> Real) (score : Unit -> Cell)
    (referenceShare loading : Cell -> Real) (weightTotalBound : Real)
    (hweight :
      (∑ unit ∈ sample, |weight unit|) ≤ weightTotalBound) :
    |weightedSampleSum sample weight
        (fun unit =>
          scoreCellLinearCenteredIndicator cells score referenceShare loading
              unit *
            scoreCellLinearCenteredIndicator cells score referenceShare loading
              unit)| ≤
      weightTotalBound *
        scoreCellLinearCenteredIndicatorEnvelope
          cells referenceShare loading ^ 2 := by
  exact
    (abs_weightedSampleSum_scoreCellLinearCenteredIndicator_mul_self_le_sum_abs_weight_mul_envelope_sq
      sample cells weight score referenceShare loading).trans
      (mul_le_mul_of_nonneg_right hweight
        (sq_nonneg
        (scoreCellLinearCenteredIndicatorEnvelope
            cells referenceShare loading)))

/--
Concrete eventual second-moment bound for one finite score-cell linear
projection.

This is the deterministic "bounded score-cell indicator" evidence used by
scalar projection CLT interfaces: the weighted sample second moment of the
centered projection is eventually bounded by the total absolute weight bound
times the squared finite loading envelope.
-/
def finiteScoreCellWeightedCenteredSecondMomentBound
    {Index : Type*} (l : Filter Index)
    (sample : Index -> Finset Unit) (cells : Finset Cell)
    (weight : Index -> Unit -> Real) (score : Index -> Unit -> Cell)
    (referenceShare loading : Cell -> Real)
    (weightTotalBound : Index -> Real) : Prop :=
  ∀ᶠ index in l,
    |weightedSampleSum (sample index) (weight index)
        (fun unit =>
          scoreCellLinearCenteredIndicator cells (score index)
              referenceShare loading unit *
            scoreCellLinearCenteredIndicator cells (score index)
              referenceShare loading unit)| ≤
      weightTotalBound index *
        scoreCellLinearCenteredIndicatorEnvelope
          cells referenceShare loading ^ 2

/--
An eventual total absolute-weight bound proves the concrete eventual
second-moment bound for a finite score-cell linear projection.
-/
theorem finiteScoreCellWeightedCenteredSecondMomentBound_of_eventually_total_abs_weight_bound
    {Index : Type*} {l : Filter Index}
    (sample : Index -> Finset Unit) (cells : Finset Cell)
    (weight : Index -> Unit -> Real) (score : Index -> Unit -> Cell)
    (referenceShare loading : Cell -> Real)
    (weightTotalBound : Index -> Real)
    (hweight :
      ∀ᶠ index in l,
        (∑ unit ∈ sample index, |weight index unit|) ≤
          weightTotalBound index) :
    finiteScoreCellWeightedCenteredSecondMomentBound
      l sample cells weight score referenceShare loading weightTotalBound := by
  filter_upwards [hweight] with index hweight_index
  exact
    abs_weightedSampleSum_scoreCellLinearCenteredIndicator_mul_self_le_bound_mul_envelope_sq
      (sample index) cells (weight index) (score index) referenceShare
      loading (weightTotalBound index) hweight_index

/-- PATE double-score sample second-moment bound by total absolute weight. -/
theorem
    abs_weightedSampleSum_pateDoubleScoreLinearCenteredIndicator_mul_self_le_sum_abs_weight_mul_envelope_sq
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
        scoreCellLinearCenteredIndicatorEnvelope
          cells referenceShare loading ^ 2 :=
  abs_weightedSampleSum_scoreCellLinearCenteredIndicator_mul_self_le_sum_abs_weight_mul_envelope_sq
    sample cells weight
    (pateDoubleScore propensityScore treatedPrognosticScore
      controlPrognosticScore)
    referenceShare loading

/-- PATT double-score sample second-moment bound by total absolute weight. -/
theorem
    abs_weightedSampleSum_pattDoubleScoreLinearCenteredIndicator_mul_self_le_sum_abs_weight_mul_envelope_sq
    (sample : Finset Unit) (cells : Finset (PropensityCell × PATTProgCell))
    (weight : Unit -> Real)
    (propensityScore : Unit -> PropensityCell)
    (controlPrognosticScore : Unit -> PATTProgCell)
    (referenceShare loading : (PropensityCell × PATTProgCell) -> Real) :
    |weightedSampleSum sample weight
        (fun unit =>
          scoreCellLinearCenteredIndicator cells
              (pattDoubleScore propensityScore controlPrognosticScore)
              referenceShare loading unit *
            scoreCellLinearCenteredIndicator cells
              (pattDoubleScore propensityScore controlPrognosticScore)
              referenceShare loading unit)| ≤
      (∑ unit ∈ sample, |weight unit|) *
        scoreCellLinearCenteredIndicatorEnvelope
          cells referenceShare loading ^ 2 :=
  abs_weightedSampleSum_scoreCellLinearCenteredIndicator_mul_self_le_sum_abs_weight_mul_envelope_sq
    sample cells weight
    (pattDoubleScore propensityScore controlPrognosticScore)
    referenceShare loading

/-- PATE double-score sample second-moment bound from a total weight bound. -/
theorem
    abs_weightedSampleSum_pateDoubleScoreLinearCenteredIndicator_mul_self_le_bound_mul_envelope_sq
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
        (fun unit =>
          scoreCellLinearCenteredIndicator cells
              (pateDoubleScore propensityScore treatedPrognosticScore
                controlPrognosticScore)
              referenceShare loading unit *
            scoreCellLinearCenteredIndicator cells
              (pateDoubleScore propensityScore treatedPrognosticScore
                controlPrognosticScore)
              referenceShare loading unit)| ≤
      weightTotalBound *
        scoreCellLinearCenteredIndicatorEnvelope
          cells referenceShare loading ^ 2 :=
  abs_weightedSampleSum_scoreCellLinearCenteredIndicator_mul_self_le_bound_mul_envelope_sq
    sample cells weight
    (pateDoubleScore propensityScore treatedPrognosticScore
      controlPrognosticScore)
    referenceShare loading weightTotalBound hweight

/-- PATT double-score sample second-moment bound from a total weight bound. -/
theorem
    abs_weightedSampleSum_pattDoubleScoreLinearCenteredIndicator_mul_self_le_bound_mul_envelope_sq
    (sample : Finset Unit) (cells : Finset (PropensityCell × PATTProgCell))
    (weight : Unit -> Real)
    (propensityScore : Unit -> PropensityCell)
    (controlPrognosticScore : Unit -> PATTProgCell)
    (referenceShare loading : (PropensityCell × PATTProgCell) -> Real)
    (weightTotalBound : Real)
    (hweight :
      (∑ unit ∈ sample, |weight unit|) ≤ weightTotalBound) :
    |weightedSampleSum sample weight
        (fun unit =>
          scoreCellLinearCenteredIndicator cells
              (pattDoubleScore propensityScore controlPrognosticScore)
              referenceShare loading unit *
            scoreCellLinearCenteredIndicator cells
              (pattDoubleScore propensityScore controlPrognosticScore)
              referenceShare loading unit)| ≤
      weightTotalBound *
        scoreCellLinearCenteredIndicatorEnvelope
          cells referenceShare loading ^ 2 :=
  abs_weightedSampleSum_scoreCellLinearCenteredIndicator_mul_self_le_bound_mul_envelope_sq
    sample cells weight
    (pattDoubleScore propensityScore controlPrognosticScore)
    referenceShare loading weightTotalBound hweight

end WDSM
end Matching
end StatInference
