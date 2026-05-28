import StatInference.Matching.WDSM.FiniteCellIndicatorBounds
import StatInference.Matching.WDSM.FiniteCellIndicatorLinearCovariance

/-!
# Bounds for finite linear score-cell indicator projections

Finite-dimensional CLT arguments test the centered score-cell indicator vector
against finite loadings.  This module proves deterministic envelopes for those
linear projections from the bounded `0/1` indicator facts.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit Cell PropensityCell TreatedProgCell ControlProgCell PATTProgCell : Type*}
  [DecidableEq Cell] [DecidableEq PropensityCell]
  [DecidableEq TreatedProgCell] [DecidableEq ControlProgCell]
  [DecidableEq PATTProgCell]

/-- A finite absolute envelope for a centered score-cell linear projection. -/
def scoreCellLinearCenteredIndicatorEnvelope
    (cells : Finset Cell) (referenceShare loading : Cell -> Real) : Real :=
  ∑ cell ∈ cells, |loading cell| * (1 + |referenceShare cell|)

omit [DecidableEq Cell] in
/-- The finite centered-linear-projection envelope is nonnegative. -/
theorem scoreCellLinearCenteredIndicatorEnvelope_nonneg
    (cells : Finset Cell) (referenceShare loading : Cell -> Real) :
    0 ≤ scoreCellLinearCenteredIndicatorEnvelope
      cells referenceShare loading := by
  unfold scoreCellLinearCenteredIndicatorEnvelope
  exact Finset.sum_nonneg
    (fun cell _hcell =>
      mul_nonneg (abs_nonneg (loading cell))
        (add_nonneg zero_le_one (abs_nonneg (referenceShare cell))))

/-- A centered score-cell indicator is bounded by `1 + |referenceShare cell|`. -/
theorem abs_centeredScoreCellIndicator_le_one_add_abs_referenceShare
    (score : Unit -> Cell) (referenceShare : Cell -> Real)
    (cell : Cell) (unit : Unit) :
    |centeredScoreCellIndicator score referenceShare cell unit| ≤
      1 + |referenceShare cell| := by
  unfold centeredScoreCellIndicator
  apply abs_le.mpr
  constructor
  · have hind_nonneg : 0 ≤ scoreCellIndicator score cell unit :=
      scoreCellIndicator_nonneg score cell unit
    have href_le_abs : referenceShare cell ≤ |referenceShare cell| :=
      le_abs_self (referenceShare cell)
    linarith
  · have hind_le_one : scoreCellIndicator score cell unit ≤ 1 :=
      scoreCellIndicator_le_one score cell unit
    have hneg_abs_le : -|referenceShare cell| ≤ referenceShare cell :=
      neg_abs_le (referenceShare cell)
    linarith

/-- Each loaded centered indicator is bounded by its envelope term. -/
theorem abs_loading_mul_centeredScoreCellIndicator_le_envelope_term
    (score : Unit -> Cell) (referenceShare loading : Cell -> Real)
    (cell : Cell) (unit : Unit) :
    |loading cell *
        centeredScoreCellIndicator score referenceShare cell unit| ≤
      |loading cell| * (1 + |referenceShare cell|) := by
  calc
    |loading cell *
        centeredScoreCellIndicator score referenceShare cell unit| =
        |loading cell| *
          |centeredScoreCellIndicator score referenceShare cell unit| := by
          rw [abs_mul]
    _ ≤ |loading cell| * (1 + |referenceShare cell|) := by
          exact mul_le_mul_of_nonneg_left
            (abs_centeredScoreCellIndicator_le_one_add_abs_referenceShare
              score referenceShare cell unit)
            (abs_nonneg (loading cell))

/-- A finite centered score-cell linear projection is bounded by its envelope. -/
theorem abs_scoreCellLinearCenteredIndicator_le_envelope
    (cells : Finset Cell) (score : Unit -> Cell)
    (referenceShare loading : Cell -> Real) (unit : Unit) :
    |scoreCellLinearCenteredIndicator cells score referenceShare loading unit| ≤
      scoreCellLinearCenteredIndicatorEnvelope cells referenceShare loading := by
  unfold scoreCellLinearCenteredIndicator
  unfold scoreCellLinearCenteredIndicatorEnvelope
  calc
    |∑ cell ∈ cells,
        loading cell *
          centeredScoreCellIndicator score referenceShare cell unit| ≤
        ∑ cell ∈ cells,
          |loading cell *
            centeredScoreCellIndicator score referenceShare cell unit| := by
          exact Finset.abs_sum_le_sum_abs _ _
    _ ≤
        ∑ cell ∈ cells,
          |loading cell| * (1 + |referenceShare cell|) := by
          exact Finset.sum_le_sum
            (fun cell _hcell =>
              abs_loading_mul_centeredScoreCellIndicator_le_envelope_term
                score referenceShare loading cell unit)

/--
A weighted centered score-cell linear projection is bounded by the absolute
weight times the finite loading envelope.
-/
theorem
    abs_weight_mul_scoreCellLinearCenteredIndicator_le_abs_weight_mul_envelope
    (cells : Finset Cell) (weight : Unit -> Real) (score : Unit -> Cell)
    (referenceShare loading : Cell -> Real) (unit : Unit) :
    |weight unit *
        scoreCellLinearCenteredIndicator cells score referenceShare loading
          unit| ≤
      |weight unit| *
        scoreCellLinearCenteredIndicatorEnvelope
          cells referenceShare loading := by
  calc
    |weight unit *
        scoreCellLinearCenteredIndicator cells score referenceShare loading
          unit| =
        |weight unit| *
          |scoreCellLinearCenteredIndicator
            cells score referenceShare loading unit| := by
          rw [abs_mul]
    _ ≤
        |weight unit| *
          scoreCellLinearCenteredIndicatorEnvelope
            cells referenceShare loading := by
          exact mul_le_mul_of_nonneg_left
            (abs_scoreCellLinearCenteredIndicator_le_envelope
              cells score referenceShare loading unit)
            (abs_nonneg (weight unit))

/-- A weight envelope bounds a weighted centered linear projection. -/
theorem abs_weight_mul_scoreCellLinearCenteredIndicator_le_bound_mul_envelope
    (cells : Finset Cell) (weight : Unit -> Real) (score : Unit -> Cell)
    (referenceShare loading : Cell -> Real) (unit : Unit)
    (weightBound : Real) (hweight : |weight unit| ≤ weightBound) :
    |weight unit *
        scoreCellLinearCenteredIndicator cells score referenceShare loading
          unit| ≤
      weightBound *
        scoreCellLinearCenteredIndicatorEnvelope
          cells referenceShare loading := by
  exact
    (abs_weight_mul_scoreCellLinearCenteredIndicator_le_abs_weight_mul_envelope
      cells weight score referenceShare loading unit).trans
      (mul_le_mul_of_nonneg_right hweight
        (scoreCellLinearCenteredIndicatorEnvelope_nonneg
          cells referenceShare loading))

/--
A uniform weight envelope bounds every weighted centered linear projection over
the sample units.
-/
theorem forall_abs_weight_mul_scoreCellLinearCenteredIndicator_le_bound_mul_envelope
    (cells : Finset Cell) (weight : Unit -> Real) (score : Unit -> Cell)
    (referenceShare loading : Cell -> Real) (weightBound : Real)
    (hweight : ∀ unit, |weight unit| ≤ weightBound) :
    ∀ unit,
      |weight unit *
          scoreCellLinearCenteredIndicator cells score referenceShare loading
            unit| ≤
        weightBound *
          scoreCellLinearCenteredIndicatorEnvelope
            cells referenceShare loading := by
  intro unit
  exact abs_weight_mul_scoreCellLinearCenteredIndicator_le_bound_mul_envelope
    cells weight score referenceShare loading unit weightBound
    (hweight unit)

/-- PATE double-score centered linear projection bound. -/
theorem
    forall_abs_weight_mul_pateDoubleScoreLinearCenteredIndicator_le_bound_mul_envelope
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (weight : Unit -> Real)
    (propensityScore : Unit -> PropensityCell)
    (treatedPrognosticScore : Unit -> TreatedProgCell)
    (controlPrognosticScore : Unit -> ControlProgCell)
    (referenceShare loading :
      ((PropensityCell × TreatedProgCell) × ControlProgCell) -> Real)
    (weightBound : Real)
    (hweight : ∀ unit, |weight unit| ≤ weightBound) :
    ∀ unit,
      |weight unit *
          scoreCellLinearCenteredIndicator cells
            (pateDoubleScore propensityScore treatedPrognosticScore
              controlPrognosticScore)
            referenceShare loading unit| ≤
        weightBound *
          scoreCellLinearCenteredIndicatorEnvelope
            cells referenceShare loading :=
  forall_abs_weight_mul_scoreCellLinearCenteredIndicator_le_bound_mul_envelope
    cells weight
    (pateDoubleScore propensityScore treatedPrognosticScore
      controlPrognosticScore)
    referenceShare loading weightBound hweight

/-- PATT double-score centered linear projection bound. -/
theorem
    forall_abs_weight_mul_pattDoubleScoreLinearCenteredIndicator_le_bound_mul_envelope
    (cells : Finset (PropensityCell × PATTProgCell))
    (weight : Unit -> Real)
    (propensityScore : Unit -> PropensityCell)
    (controlPrognosticScore : Unit -> PATTProgCell)
    (referenceShare loading : (PropensityCell × PATTProgCell) -> Real)
    (weightBound : Real)
    (hweight : ∀ unit, |weight unit| ≤ weightBound) :
    ∀ unit,
      |weight unit *
          scoreCellLinearCenteredIndicator cells
            (pattDoubleScore propensityScore controlPrognosticScore)
            referenceShare loading unit| ≤
        weightBound *
          scoreCellLinearCenteredIndicatorEnvelope
            cells referenceShare loading :=
  forall_abs_weight_mul_scoreCellLinearCenteredIndicator_le_bound_mul_envelope
    cells weight (pattDoubleScore propensityScore controlPrognosticScore)
    referenceShare loading weightBound hweight

end WDSM
end Matching
end StatInference
