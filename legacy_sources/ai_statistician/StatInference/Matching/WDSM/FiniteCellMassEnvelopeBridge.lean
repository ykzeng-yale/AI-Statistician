import StatInference.Matching.WDSM.FiniteCellIndicatorLLNFromMass
import StatInference.Matching.WDSM.SqueezeAlgebra

/-!
# Finite score-cell mass convergence from shrinking envelopes

This module closes a reusable deterministic step for WDSM finite-cell
arguments.  Instead of assuming score-cell mass convergence directly, later
probability arguments can prove eventual absolute error bounds for each cell
and show that those bounds shrink to zero.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Unit Cell : Type*} {l : Filter Index} [DecidableEq Cell]

/--
A single score-cell mass converges to its limit when its absolute error is
eventually bounded by a deterministic sequence tending to zero.
-/
theorem tendsto_scoreCellMass_of_eventually_abs_sub_le_bound
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (cell : Cell)
    (massLimit : Real)
    (bound : Index -> Real)
    (hbound :
      ∀ᶠ index in l,
        |scoreCellMass (sample index) (weight index)
            (score index) cell - massLimit| ≤ bound index)
    (hbound_tendsto :
      Tendsto bound l (nhds 0)) :
    Tendsto
      (fun index =>
        scoreCellMass (sample index) (weight index)
          (score index) cell)
      l (nhds massLimit) := by
  have hdiff :
      Tendsto
        (fun index =>
          scoreCellMass (sample index) (weight index)
            (score index) cell - massLimit)
        l (nhds 0) :=
    tendsto_zero_of_eventually_abs_le_bound
      (fun index =>
        scoreCellMass (sample index) (weight index)
          (score index) cell - massLimit)
      bound hbound hbound_tendsto
  have hsum :
      Tendsto
        (fun index =>
          (scoreCellMass (sample index) (weight index)
              (score index) cell - massLimit) + massLimit)
        l (nhds (0 + massLimit)) :=
    hdiff.add tendsto_const_nhds
  simpa using hsum

/--
Cellwise score-cell mass convergence from cell-specific shrinking absolute
error bounds.
-/
theorem cellwiseScoreCellMassLLN_of_eventually_abs_sub_le_bounds
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (massLimit : Cell -> Real)
    (bound : Index -> Cell -> Real)
    (hbound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sample index) (weight index)
              (score index) cell - massLimit cell| ≤ bound index cell)
    (hbound_tendsto :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => bound index cell) l (nhds 0)) :
    cellwiseScoreCellMassLLN (l := l) cells sample weight score massLimit :=
  fun cell hcell =>
    tendsto_scoreCellMass_of_eventually_abs_sub_le_bound
      (l := l) sample weight score cell (massLimit cell)
      (fun index => bound index cell) (hbound cell hcell)
      (hbound_tendsto cell hcell)

/--
Cellwise score-cell mass convergence from one shrinking envelope multiplied by
fixed cell scales.
-/
theorem cellwiseScoreCellMassLLN_of_eventually_abs_sub_le_envelope
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (massLimit cellScale : Cell -> Real)
    (envelope : Index -> Real)
    (hbound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sample index) (weight index)
              (score index) cell - massLimit cell| ≤
            cellScale cell * envelope index)
    (henvelope_tendsto :
      Tendsto envelope l (nhds 0)) :
    cellwiseScoreCellMassLLN (l := l) cells sample weight score massLimit :=
  cellwiseScoreCellMassLLN_of_eventually_abs_sub_le_bounds
    (l := l) cells sample weight score massLimit
    (fun index cell => cellScale cell * envelope index)
    hbound
    (fun cell _hcell => by
      simpa using
        ((tendsto_const_nhds :
          Tendsto (fun _index : Index => cellScale cell) l
            (nhds (cellScale cell))).mul henvelope_tendsto))

/--
Weighted score-cell indicator-sum LLNs follow from score-cell mass envelope
bounds through the existing mass/indicator equivalence.
-/
theorem cellwiseWeightedIndicatorSumLLN_of_eventually_abs_scoreCellMass_sub_le_envelope
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (massLimit cellScale : Cell -> Real)
    (envelope : Index -> Real)
    (hbound :
      ∀ cell, cell ∈ cells ->
        ∀ᶠ index in l,
          |scoreCellMass (sample index) (weight index)
              (score index) cell - massLimit cell| ≤
            cellScale cell * envelope index)
    (henvelope_tendsto :
      Tendsto envelope l (nhds 0)) :
    cellwiseWeightedIndicatorSumLLN (l := l) cells sample weight score
      massLimit :=
  cellwiseWeightedIndicatorSumLLN_of_mass
    (l := l) cells sample weight score massLimit
    (cellwiseScoreCellMassLLN_of_eventually_abs_sub_le_envelope
      (l := l) cells sample weight score massLimit cellScale envelope
      hbound henvelope_tendsto)

end WDSM
end Matching
end StatInference
