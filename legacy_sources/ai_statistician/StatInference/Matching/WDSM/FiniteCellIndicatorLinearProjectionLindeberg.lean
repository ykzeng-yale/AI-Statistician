import StatInference.Matching.WDSM.FiniteCellIndicatorLinearProjectionTailConvergence

/-!
# Lindeberg-style tails for finite linear score-cell indicator projections

This module closes the deterministic part of a bounded finite-projection
Lindeberg argument.  A fixed finite cardinality/loading envelope is eventually
below every positive `epsilon * scale` threshold whenever `scale -> atTop`.
Combined with the tail-convergence module, this gives zero large-jump limits
for bounded weighted centered score-cell projections.
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

/--
A diverging positive scale eventually dominates every fixed real constant
after multiplication by a positive epsilon.
-/
theorem eventually_const_le_epsilon_mul_of_tendsto_atTop
    (scale : Index -> Real) (constant epsilon : Real)
    (hepsilon : 0 < epsilon)
    (hscale : Tendsto scale l atTop) :
    ∀ᶠ index in l, constant ≤ epsilon * scale index := by
  have hge :
      ∀ᶠ index in l, constant / epsilon ≤ scale index :=
    hscale.eventually (eventually_ge_atTop (constant / epsilon))
  filter_upwards [hge] with index hscale_ge
  have hmul :
      epsilon * (constant / epsilon) ≤ epsilon * scale index :=
    mul_le_mul_of_nonneg_left hscale_ge hepsilon.le
  have heq : epsilon * (constant / epsilon) = constant := by
    have hepsilon_ne : epsilon ≠ 0 := ne_of_gt hepsilon
    field_simp [hepsilon_ne]
  simpa [heq] using hmul

/--
For a fixed finite partition and bounded loadings, scale divergence gives
large-jump tail convergence for every positive epsilon.
-/
theorem
    tendsto_sum_largeJumpSquare_weight_mul_scoreCellLinearCenteredIndicator_zero_of_tendsto_scale_atTop
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
    Tendsto
      (fun index =>
        ∑ unit ∈ sample index,
          largeJumpSquare
            (weight index unit *
              scoreCellLinearCenteredIndicator cells (score index)
                referenceShare loading unit)
            (epsilon * scale index))
      l (nhds 0) := by
  have hthreshold :
      ∀ᶠ index in l,
        weightBound * ((cells.card : Real) * (loadingBound * 2)) ≤
          epsilon * scale index :=
    eventually_const_le_epsilon_mul_of_tendsto_atTop
      scale (weightBound * ((cells.card : Real) * (loadingBound * 2)))
      epsilon hepsilon hscale
  simpa using
    tendsto_sum_largeJumpSquare_weight_mul_scoreCellLinearCenteredIndicator_zero_of_eventually_bound_le_epsilon_scale
      (l := l) sample (fun _index => cells) weight score
      (fun _index => referenceShare) (fun _index => loading)
      (fun _index => weightBound) (fun _index => loadingBound)
      (fun _index => epsilon) scale
      (Eventually.of_forall (fun _index => hloading_nonneg))
      hweight
      (Eventually.of_forall (fun _index => hloading))
      (Eventually.of_forall (fun _index => hshare))
      hthreshold

/-- PATE double-score finite-projection Lindeberg-style tail convergence. -/
theorem
    tendsto_sum_largeJumpSquare_weight_mul_pateDoubleScoreLinearCenteredIndicator_zero_of_tendsto_scale_atTop
    (sample : Index -> Finset Unit)
    (cells : Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (weight : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (referenceShare loading :
      ((PropensityCell × TreatedProgCell) × ControlProgCell) -> Real)
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
    Tendsto
      (fun index =>
        ∑ unit ∈ sample index,
          largeJumpSquare
            (weight index unit *
              scoreCellLinearCenteredIndicator cells
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index))
                referenceShare loading unit)
            (epsilon * scale index))
      l (nhds 0) :=
  tendsto_sum_largeJumpSquare_weight_mul_scoreCellLinearCenteredIndicator_zero_of_tendsto_scale_atTop
    (l := l) sample cells weight
    (fun index =>
      pateDoubleScore (propensityScore index) (treatedPrognosticScore index)
        (controlPrognosticScore index))
    referenceShare loading weightBound loadingBound epsilon scale hepsilon
    hscale hloading_nonneg hweight hloading hshare

/-- PATT double-score finite-projection Lindeberg-style tail convergence. -/
theorem
    tendsto_sum_largeJumpSquare_weight_mul_pattDoubleScoreLinearCenteredIndicator_zero_of_tendsto_scale_atTop
    (sample : Index -> Finset Unit)
    (cells : Finset (PropensityCell × PATTProgCell))
    (weight : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (referenceShare loading : (PropensityCell × PATTProgCell) -> Real)
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
    Tendsto
      (fun index =>
        ∑ unit ∈ sample index,
          largeJumpSquare
            (weight index unit *
              scoreCellLinearCenteredIndicator cells
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index))
                referenceShare loading unit)
            (epsilon * scale index))
      l (nhds 0) :=
  tendsto_sum_largeJumpSquare_weight_mul_scoreCellLinearCenteredIndicator_zero_of_tendsto_scale_atTop
    (l := l) sample cells weight
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    referenceShare loading weightBound loadingBound epsilon scale hepsilon
    hscale hloading_nonneg hweight hloading hshare

end WDSM
end Matching
end StatInference
