import StatInference.Matching.WDSM.FiniteCellIndicatorLinearProjectionCardinalityMomentBounds

/-!
# Tail bounds for finite linear score-cell indicator projections

The preceding modules bound finite centered score-cell linear projections and
their squares.  This module records the deterministic "large jump is absent"
step used by finite-dimensional CLT/Lindeberg routes: if the uniform
cardinality envelope is below a threshold, then every truncated large-jump
square is zero.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit Cell PropensityCell TreatedProgCell ControlProgCell PATTProgCell : Type*}
  [DecidableEq Cell] [DecidableEq PropensityCell]
  [DecidableEq TreatedProgCell] [DecidableEq ControlProgCell]
  [DecidableEq PATTProgCell]

/-- Squared summand kept only on the large-jump event `threshold < |term|`. -/
noncomputable def largeJumpSquare (term threshold : Real) : Real :=
  if threshold < |term| then term * term else 0

/-- A term below the threshold has zero large-jump square. -/
theorem largeJumpSquare_eq_zero_of_abs_le
    (term threshold : Real) (hterm : |term| ≤ threshold) :
    largeJumpSquare term threshold = 0 := by
  unfold largeJumpSquare
  exact if_neg (not_lt_of_ge hterm)

/-- If every sample term is below the threshold, the finite large-jump sum is zero. -/
theorem sum_largeJumpSquare_eq_zero_of_forall_abs_le
    (sample : Finset Unit) (term : Unit -> Real) (threshold : Real)
    (hterm : ∀ unit, unit ∈ sample -> |term unit| ≤ threshold) :
    (∑ unit ∈ sample, largeJumpSquare (term unit) threshold) = 0 := by
  exact Finset.sum_eq_zero
    (fun unit hunit =>
      largeJumpSquare_eq_zero_of_abs_le
        (term unit) threshold (hterm unit hunit))

/--
Uniform weight and finite-cardinality loading bounds make every weighted
centered score-cell projection fall below the threshold, so the large-jump
square sum vanishes.
-/
theorem
    sum_largeJumpSquare_weight_mul_scoreCellLinearCenteredIndicator_eq_zero_of_bound_le_threshold
    (sample : Finset Unit) (cells : Finset Cell)
    (weight : Unit -> Real) (score : Unit -> Cell)
    (referenceShare loading : Cell -> Real)
    (weightBound loadingBound threshold : Real)
    (hloading_nonneg : 0 ≤ loadingBound)
    (hweight : ∀ unit, unit ∈ sample -> |weight unit| ≤ weightBound)
    (hloading :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ loadingBound)
    (hshare :
      ∀ cell, cell ∈ cells -> |referenceShare cell| ≤ 1)
    (hthreshold :
      weightBound * ((cells.card : Real) * (loadingBound * 2)) ≤
        threshold) :
    (∑ unit ∈ sample,
      largeJumpSquare
        (weight unit *
          scoreCellLinearCenteredIndicator cells score referenceShare loading
            unit)
        threshold) = 0 := by
  refine sum_largeJumpSquare_eq_zero_of_forall_abs_le sample
    (fun unit =>
      weight unit *
        scoreCellLinearCenteredIndicator cells score referenceShare loading
          unit)
    threshold ?_
  intro unit hunit
  have hcard_nonneg :
      0 ≤ (cells.card : Real) * (loadingBound * 2) :=
    card_mul_loadingBound_two_nonneg cells loadingBound hloading_nonneg
  have hweighted :
      |weight unit *
          scoreCellLinearCenteredIndicator cells score referenceShare loading
            unit| ≤
        |weight unit| * ((cells.card : Real) * (loadingBound * 2)) :=
    abs_weight_mul_scoreCellLinearCenteredIndicator_le_abs_weight_mul_card_mul_loadingBound_two
      cells weight score referenceShare loading unit loadingBound
      hloading_nonneg hloading hshare
  have hbound :
      |weight unit| * ((cells.card : Real) * (loadingBound * 2)) ≤
        weightBound * ((cells.card : Real) * (loadingBound * 2)) :=
    mul_le_mul_of_nonneg_right (hweight unit hunit) hcard_nonneg
  exact hweighted.trans (hbound.trans hthreshold)

/--
Scaled version with threshold `epsilon * scale`, matching Lindeberg-style
finite projection arguments.
-/
theorem
    sum_largeJumpSquare_weight_mul_scoreCellLinearCenteredIndicator_eq_zero_of_bound_le_epsilon_scale
    (sample : Finset Unit) (cells : Finset Cell)
    (weight : Unit -> Real) (score : Unit -> Cell)
    (referenceShare loading : Cell -> Real)
    (weightBound loadingBound epsilon scale : Real)
    (hloading_nonneg : 0 ≤ loadingBound)
    (hweight : ∀ unit, unit ∈ sample -> |weight unit| ≤ weightBound)
    (hloading :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ loadingBound)
    (hshare :
      ∀ cell, cell ∈ cells -> |referenceShare cell| ≤ 1)
    (hthreshold :
      weightBound * ((cells.card : Real) * (loadingBound * 2)) ≤
        epsilon * scale) :
    (∑ unit ∈ sample,
      largeJumpSquare
        (weight unit *
          scoreCellLinearCenteredIndicator cells score referenceShare loading
            unit)
        (epsilon * scale)) = 0 :=
  sum_largeJumpSquare_weight_mul_scoreCellLinearCenteredIndicator_eq_zero_of_bound_le_threshold
    sample cells weight score referenceShare loading weightBound loadingBound
    (epsilon * scale) hloading_nonneg hweight hloading hshare hthreshold

/-- PATE double-score large-jump sum vanishes under the finite-cardinality bound. -/
theorem
    sum_largeJumpSquare_weight_mul_pateDoubleScoreLinearCenteredIndicator_eq_zero_of_bound_le_threshold
    (sample : Finset Unit)
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (weight : Unit -> Real)
    (propensityScore : Unit -> PropensityCell)
    (treatedPrognosticScore : Unit -> TreatedProgCell)
    (controlPrognosticScore : Unit -> ControlProgCell)
    (referenceShare loading :
      ((PropensityCell × TreatedProgCell) × ControlProgCell) -> Real)
    (weightBound loadingBound threshold : Real)
    (hloading_nonneg : 0 ≤ loadingBound)
    (hweight : ∀ unit, unit ∈ sample -> |weight unit| ≤ weightBound)
    (hloading :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ loadingBound)
    (hshare :
      ∀ cell, cell ∈ cells -> |referenceShare cell| ≤ 1)
    (hthreshold :
      weightBound * ((cells.card : Real) * (loadingBound * 2)) ≤
        threshold) :
    (∑ unit ∈ sample,
      largeJumpSquare
        (weight unit *
          scoreCellLinearCenteredIndicator cells
            (pateDoubleScore propensityScore treatedPrognosticScore
              controlPrognosticScore)
            referenceShare loading unit)
        threshold) = 0 :=
  sum_largeJumpSquare_weight_mul_scoreCellLinearCenteredIndicator_eq_zero_of_bound_le_threshold
    sample cells weight
    (pateDoubleScore propensityScore treatedPrognosticScore
      controlPrognosticScore)
    referenceShare loading weightBound loadingBound threshold hloading_nonneg
    hweight hloading hshare hthreshold

/-- PATT double-score large-jump sum vanishes under the finite-cardinality bound. -/
theorem
    sum_largeJumpSquare_weight_mul_pattDoubleScoreLinearCenteredIndicator_eq_zero_of_bound_le_threshold
    (sample : Finset Unit) (cells : Finset (PropensityCell × PATTProgCell))
    (weight : Unit -> Real)
    (propensityScore : Unit -> PropensityCell)
    (controlPrognosticScore : Unit -> PATTProgCell)
    (referenceShare loading : (PropensityCell × PATTProgCell) -> Real)
    (weightBound loadingBound threshold : Real)
    (hloading_nonneg : 0 ≤ loadingBound)
    (hweight : ∀ unit, unit ∈ sample -> |weight unit| ≤ weightBound)
    (hloading :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ loadingBound)
    (hshare :
      ∀ cell, cell ∈ cells -> |referenceShare cell| ≤ 1)
    (hthreshold :
      weightBound * ((cells.card : Real) * (loadingBound * 2)) ≤
        threshold) :
    (∑ unit ∈ sample,
      largeJumpSquare
        (weight unit *
          scoreCellLinearCenteredIndicator cells
            (pattDoubleScore propensityScore controlPrognosticScore)
            referenceShare loading unit)
        threshold) = 0 :=
  sum_largeJumpSquare_weight_mul_scoreCellLinearCenteredIndicator_eq_zero_of_bound_le_threshold
    sample cells weight
    (pattDoubleScore propensityScore controlPrognosticScore)
    referenceShare loading weightBound loadingBound threshold hloading_nonneg
    hweight hloading hshare hthreshold

/-- Scaled PATE double-score large-jump sum vanishes below `epsilon * scale`. -/
theorem
    sum_largeJumpSquare_weight_mul_pateDoubleScoreLinearCenteredIndicator_eq_zero_of_bound_le_epsilon_scale
    (sample : Finset Unit)
    (cells :
      Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (weight : Unit -> Real)
    (propensityScore : Unit -> PropensityCell)
    (treatedPrognosticScore : Unit -> TreatedProgCell)
    (controlPrognosticScore : Unit -> ControlProgCell)
    (referenceShare loading :
      ((PropensityCell × TreatedProgCell) × ControlProgCell) -> Real)
    (weightBound loadingBound epsilon scale : Real)
    (hloading_nonneg : 0 ≤ loadingBound)
    (hweight : ∀ unit, unit ∈ sample -> |weight unit| ≤ weightBound)
    (hloading :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ loadingBound)
    (hshare :
      ∀ cell, cell ∈ cells -> |referenceShare cell| ≤ 1)
    (hthreshold :
      weightBound * ((cells.card : Real) * (loadingBound * 2)) ≤
        epsilon * scale) :
    (∑ unit ∈ sample,
      largeJumpSquare
        (weight unit *
          scoreCellLinearCenteredIndicator cells
            (pateDoubleScore propensityScore treatedPrognosticScore
              controlPrognosticScore)
            referenceShare loading unit)
        (epsilon * scale)) = 0 :=
  sum_largeJumpSquare_weight_mul_pateDoubleScoreLinearCenteredIndicator_eq_zero_of_bound_le_threshold
    sample cells weight propensityScore treatedPrognosticScore
    controlPrognosticScore referenceShare loading weightBound loadingBound
    (epsilon * scale) hloading_nonneg hweight hloading hshare hthreshold

/-- Scaled PATT double-score large-jump sum vanishes below `epsilon * scale`. -/
theorem
    sum_largeJumpSquare_weight_mul_pattDoubleScoreLinearCenteredIndicator_eq_zero_of_bound_le_epsilon_scale
    (sample : Finset Unit) (cells : Finset (PropensityCell × PATTProgCell))
    (weight : Unit -> Real)
    (propensityScore : Unit -> PropensityCell)
    (controlPrognosticScore : Unit -> PATTProgCell)
    (referenceShare loading : (PropensityCell × PATTProgCell) -> Real)
    (weightBound loadingBound epsilon scale : Real)
    (hloading_nonneg : 0 ≤ loadingBound)
    (hweight : ∀ unit, unit ∈ sample -> |weight unit| ≤ weightBound)
    (hloading :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ loadingBound)
    (hshare :
      ∀ cell, cell ∈ cells -> |referenceShare cell| ≤ 1)
    (hthreshold :
      weightBound * ((cells.card : Real) * (loadingBound * 2)) ≤
        epsilon * scale) :
    (∑ unit ∈ sample,
      largeJumpSquare
        (weight unit *
          scoreCellLinearCenteredIndicator cells
            (pattDoubleScore propensityScore controlPrognosticScore)
            referenceShare loading unit)
        (epsilon * scale)) = 0 :=
  sum_largeJumpSquare_weight_mul_pattDoubleScoreLinearCenteredIndicator_eq_zero_of_bound_le_threshold
    sample cells weight propensityScore controlPrognosticScore referenceShare
    loading weightBound loadingBound (epsilon * scale) hloading_nonneg hweight
    hloading hshare hthreshold

end WDSM
end Matching
end StatInference
