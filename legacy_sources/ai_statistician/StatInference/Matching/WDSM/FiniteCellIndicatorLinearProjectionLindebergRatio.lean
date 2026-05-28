import StatInference.Matching.WDSM.FiniteCellIndicatorLinearProjectionLindeberg

/-!
# Normalized Lindeberg tails for finite linear score-cell projections

The previous module proves that bounded finite centered score-cell projection
large-jump sums tend to zero when the comparison scale diverges.  Here we use
the stronger fact that the large-jump sums are eventually exactly zero, so any
deterministic normalization of the tail sum is also negligible.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter
open scoped BigOperators

variable {Index Unit Cell PropensityCell TreatedProgCell ControlProgCell PATTProgCell : Type*}
  {l : Filter Index}
  [DecidableEq Cell] [DecidableEq PropensityCell]
  [DecidableEq TreatedProgCell] [DecidableEq ControlProgCell]
  [DecidableEq PATTProgCell]

/-- Multiplying an eventually zero real sequence by any normalizer still tends to zero. -/
theorem tendsto_normalizer_mul_zero_of_eventually_eq_zero
    (normalizer value : Index -> Real)
    (hzero : ∀ᶠ index in l, value index = 0) :
    Tendsto (fun index => normalizer index * value index) l (nhds 0) := by
  exact tendsto_zero_of_eventually_eq_zero
    (fun index => normalizer index * value index)
    (hzero.mono
      (fun index hvalue => by
        change normalizer index * value index = 0
        rw [hvalue, mul_zero]))

/--
For fixed finite projection envelopes, scale divergence gives eventual exact
zero of the finite large-jump tail sum.
-/
theorem
    eventually_sum_largeJumpSquare_weight_mul_scoreCellLinearCenteredIndicator_eq_zero_of_tendsto_scale_atTop
    (sample : Index -> Finset Unit) (cells : Finset Cell)
    (weight : Index -> Unit -> Real) (score : Index -> Unit -> Cell)
    (referenceShare loading : Cell -> Real)
    (weightBound loadingBound epsilon : Real) (scale : Index -> Real)
    (hepsilon : 0 < epsilon)
    (hscale : Tendsto scale l atTop)
    (hloading_nonneg : 0 ≤ loadingBound)
    (hweight :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> |weight index unit| ≤ weightBound)
    (hloading :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ loadingBound)
    (hshare :
      ∀ cell, cell ∈ cells -> |referenceShare cell| ≤ 1) :
    ∀ᶠ index in l,
      (∑ unit ∈ sample index,
        largeJumpSquare
          (weight index unit *
            scoreCellLinearCenteredIndicator cells (score index)
              referenceShare loading unit)
          (epsilon * scale index)) = 0 := by
  have hthreshold :
      ∀ᶠ index in l,
        weightBound * ((cells.card : Real) * (loadingBound * 2)) ≤
          epsilon * scale index :=
    eventually_const_le_epsilon_mul_of_tendsto_atTop
      scale (weightBound * ((cells.card : Real) * (loadingBound * 2)))
      epsilon hepsilon hscale
  simpa using
    eventually_sum_largeJumpSquare_weight_mul_scoreCellLinearCenteredIndicator_eq_zero_of_eventually_bound_le_epsilon_scale
      (l := l) sample (fun _index => cells) weight score
      (fun _index => referenceShare) (fun _index => loading)
      (fun _index => weightBound) (fun _index => loadingBound)
      (fun _index => epsilon) scale
      (Eventually.of_forall (fun _index => hloading_nonneg))
      hweight
      (Eventually.of_forall (fun _index => hloading))
      (Eventually.of_forall (fun _index => hshare))
      hthreshold

/--
Any deterministic normalization of a bounded finite-projection large-jump tail
sum is negligible when the comparison scale diverges.
-/
theorem
    tendsto_normalizer_mul_sum_largeJumpSquare_weight_mul_scoreCellLinearCenteredIndicator_zero_of_tendsto_scale_atTop
    (sample : Index -> Finset Unit) (cells : Finset Cell)
    (weight : Index -> Unit -> Real) (score : Index -> Unit -> Cell)
    (referenceShare loading : Cell -> Real)
    (weightBound loadingBound epsilon : Real) (scale normalizer : Index -> Real)
    (hepsilon : 0 < epsilon)
    (hscale : Tendsto scale l atTop)
    (hloading_nonneg : 0 ≤ loadingBound)
    (hweight :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> |weight index unit| ≤ weightBound)
    (hloading :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ loadingBound)
    (hshare :
      ∀ cell, cell ∈ cells -> |referenceShare cell| ≤ 1) :
    Tendsto
      (fun index =>
        normalizer index *
          (∑ unit ∈ sample index,
            largeJumpSquare
              (weight index unit *
                scoreCellLinearCenteredIndicator cells (score index)
                  referenceShare loading unit)
              (epsilon * scale index)))
      l (nhds 0) := by
  let tail : Index -> Real := fun index =>
    ∑ unit ∈ sample index,
      largeJumpSquare
        (weight index unit *
          scoreCellLinearCenteredIndicator cells (score index)
            referenceShare loading unit)
        (epsilon * scale index)
  have hzero : ∀ᶠ index in l, tail index = 0 := by
    dsimp [tail]
    exact
      eventually_sum_largeJumpSquare_weight_mul_scoreCellLinearCenteredIndicator_eq_zero_of_tendsto_scale_atTop
        sample cells weight score referenceShare loading weightBound
        loadingBound epsilon scale hepsilon hscale hloading_nonneg hweight
        hloading hshare
  simpa [tail] using
    tendsto_normalizer_mul_zero_of_eventually_eq_zero normalizer tail hzero

/-- PATE double-score normalized finite-projection Lindeberg tail convergence. -/
theorem
    tendsto_normalizer_mul_sum_largeJumpSquare_weight_mul_pateDoubleScoreLinearCenteredIndicator_zero_of_tendsto_scale_atTop
    (sample : Index -> Finset Unit)
    (cells : Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (weight : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (referenceShare loading :
      ((PropensityCell × TreatedProgCell) × ControlProgCell) -> Real)
    (weightBound loadingBound epsilon : Real) (scale normalizer : Index -> Real)
    (hepsilon : 0 < epsilon)
    (hscale : Tendsto scale l atTop)
    (hloading_nonneg : 0 ≤ loadingBound)
    (hweight :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> |weight index unit| ≤ weightBound)
    (hloading :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ loadingBound)
    (hshare :
      ∀ cell, cell ∈ cells -> |referenceShare cell| ≤ 1) :
    Tendsto
      (fun index =>
        normalizer index *
          (∑ unit ∈ sample index,
            largeJumpSquare
              (weight index unit *
                scoreCellLinearCenteredIndicator cells
                  (pateDoubleScore (propensityScore index)
                    (treatedPrognosticScore index)
                    (controlPrognosticScore index))
                  referenceShare loading unit)
              (epsilon * scale index)))
      l (nhds 0) :=
  tendsto_normalizer_mul_sum_largeJumpSquare_weight_mul_scoreCellLinearCenteredIndicator_zero_of_tendsto_scale_atTop
    (l := l) sample cells weight
    (fun index =>
      pateDoubleScore (propensityScore index) (treatedPrognosticScore index)
        (controlPrognosticScore index))
    referenceShare loading weightBound loadingBound epsilon scale normalizer
    hepsilon hscale hloading_nonneg hweight hloading hshare

/-- PATT double-score normalized finite-projection Lindeberg tail convergence. -/
theorem
    tendsto_normalizer_mul_sum_largeJumpSquare_weight_mul_pattDoubleScoreLinearCenteredIndicator_zero_of_tendsto_scale_atTop
    (sample : Index -> Finset Unit)
    (cells : Finset (PropensityCell × PATTProgCell))
    (weight : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (referenceShare loading : (PropensityCell × PATTProgCell) -> Real)
    (weightBound loadingBound epsilon : Real) (scale normalizer : Index -> Real)
    (hepsilon : 0 < epsilon)
    (hscale : Tendsto scale l atTop)
    (hloading_nonneg : 0 ≤ loadingBound)
    (hweight :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> |weight index unit| ≤ weightBound)
    (hloading :
      ∀ cell, cell ∈ cells -> |loading cell| ≤ loadingBound)
    (hshare :
      ∀ cell, cell ∈ cells -> |referenceShare cell| ≤ 1) :
    Tendsto
      (fun index =>
        normalizer index *
          (∑ unit ∈ sample index,
            largeJumpSquare
              (weight index unit *
                scoreCellLinearCenteredIndicator cells
                  (pattDoubleScore (propensityScore index)
                    (controlPrognosticScore index))
                  referenceShare loading unit)
              (epsilon * scale index)))
      l (nhds 0) :=
  tendsto_normalizer_mul_sum_largeJumpSquare_weight_mul_scoreCellLinearCenteredIndicator_zero_of_tendsto_scale_atTop
    (l := l) sample cells weight
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    referenceShare loading weightBound loadingBound epsilon scale normalizer
    hepsilon hscale hloading_nonneg hweight hloading hshare

end WDSM
end Matching
end StatInference
