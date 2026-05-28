import StatInference.Matching.WDSM.FiniteCellIndicatorLinearProjectionTailBounds

/-!
# Tail convergence for finite linear score-cell indicator projections

This module lifts the deterministic large-jump tail bounds to asymptotic
filters.  When the finite-cardinality loading envelope times the uniform
absolute-weight bound is eventually below the threshold, the large-jump sum is
eventually exactly zero and therefore tends to zero.
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

/-- An eventually zero real sequence tends to zero. -/
theorem tendsto_zero_of_eventually_eq_zero
    (value : Index -> Real)
    (hzero : ∀ᶠ index in l, value index = 0) :
    Tendsto value l (nhds 0) := by
  have heq : value =ᶠ[l] fun _index => (0 : Real) := hzero
  exact
    (tendsto_const_nhds :
      Tendsto (fun _index : Index => (0 : Real)) l (nhds 0)).congr'
        heq.symm

/--
Eventual envelope domination implies the weighted centered-projection
large-jump sum is eventually zero.
-/
theorem
    eventually_sum_largeJumpSquare_weight_mul_scoreCellLinearCenteredIndicator_eq_zero_of_eventually_bound_le_threshold
    (sample : Index -> Finset Unit) (cells : Index -> Finset Cell)
    (weight : Index -> Unit -> Real) (score : Index -> Unit -> Cell)
    (referenceShare loading : Index -> Cell -> Real)
    (weightBound loadingBound threshold : Index -> Real)
    (hloading_nonneg : ∀ᶠ index in l, 0 ≤ loadingBound index)
    (hweight :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> |weight index unit| ≤
          weightBound index)
    (hloading :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index -> |loading index cell| ≤
          loadingBound index)
    (hshare :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index -> |referenceShare index cell| ≤ 1)
    (hthreshold :
      ∀ᶠ index in l,
        weightBound index *
            (((cells index).card : Real) * (loadingBound index * 2)) ≤
          threshold index) :
    ∀ᶠ index in l,
      (∑ unit ∈ sample index,
        largeJumpSquare
          (weight index unit *
            scoreCellLinearCenteredIndicator (cells index) (score index)
              (referenceShare index) (loading index) unit)
          (threshold index)) = 0 := by
  filter_upwards
    [hloading_nonneg, hweight, hloading, hshare, hthreshold]
    with index hnonneg hweight_index hloading_index hshare_index
      hthreshold_index
  exact
    sum_largeJumpSquare_weight_mul_scoreCellLinearCenteredIndicator_eq_zero_of_bound_le_threshold
      (sample index) (cells index) (weight index) (score index)
      (referenceShare index) (loading index) (weightBound index)
      (loadingBound index) (threshold index) hnonneg hweight_index
      hloading_index hshare_index hthreshold_index

/--
Eventual envelope domination implies the weighted centered-projection
large-jump sum tends to zero.
-/
theorem
    tendsto_sum_largeJumpSquare_weight_mul_scoreCellLinearCenteredIndicator_zero_of_eventually_bound_le_threshold
    (sample : Index -> Finset Unit) (cells : Index -> Finset Cell)
    (weight : Index -> Unit -> Real) (score : Index -> Unit -> Cell)
    (referenceShare loading : Index -> Cell -> Real)
    (weightBound loadingBound threshold : Index -> Real)
    (hloading_nonneg : ∀ᶠ index in l, 0 ≤ loadingBound index)
    (hweight :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> |weight index unit| ≤
          weightBound index)
    (hloading :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index -> |loading index cell| ≤
          loadingBound index)
    (hshare :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index -> |referenceShare index cell| ≤ 1)
    (hthreshold :
      ∀ᶠ index in l,
        weightBound index *
            (((cells index).card : Real) * (loadingBound index * 2)) ≤
          threshold index) :
    Tendsto
      (fun index =>
        ∑ unit ∈ sample index,
          largeJumpSquare
            (weight index unit *
              scoreCellLinearCenteredIndicator (cells index) (score index)
                (referenceShare index) (loading index) unit)
            (threshold index))
      l (nhds 0) := by
  exact tendsto_zero_of_eventually_eq_zero
    (fun index =>
      ∑ unit ∈ sample index,
        largeJumpSquare
          (weight index unit *
            scoreCellLinearCenteredIndicator (cells index) (score index)
              (referenceShare index) (loading index) unit)
          (threshold index))
    (eventually_sum_largeJumpSquare_weight_mul_scoreCellLinearCenteredIndicator_eq_zero_of_eventually_bound_le_threshold
      sample cells weight score referenceShare loading weightBound
      loadingBound threshold hloading_nonneg hweight hloading hshare
      hthreshold)

/-- Scaled-threshold eventual tail zero for finite centered projections. -/
theorem
    eventually_sum_largeJumpSquare_weight_mul_scoreCellLinearCenteredIndicator_eq_zero_of_eventually_bound_le_epsilon_scale
    (sample : Index -> Finset Unit) (cells : Index -> Finset Cell)
    (weight : Index -> Unit -> Real) (score : Index -> Unit -> Cell)
    (referenceShare loading : Index -> Cell -> Real)
    (weightBound loadingBound epsilon scale : Index -> Real)
    (hloading_nonneg : ∀ᶠ index in l, 0 ≤ loadingBound index)
    (hweight :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> |weight index unit| ≤
          weightBound index)
    (hloading :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index -> |loading index cell| ≤
          loadingBound index)
    (hshare :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index -> |referenceShare index cell| ≤ 1)
    (hthreshold :
      ∀ᶠ index in l,
        weightBound index *
            (((cells index).card : Real) * (loadingBound index * 2)) ≤
          epsilon index * scale index) :
    ∀ᶠ index in l,
      (∑ unit ∈ sample index,
        largeJumpSquare
          (weight index unit *
            scoreCellLinearCenteredIndicator (cells index) (score index)
              (referenceShare index) (loading index) unit)
          (epsilon index * scale index)) = 0 :=
  eventually_sum_largeJumpSquare_weight_mul_scoreCellLinearCenteredIndicator_eq_zero_of_eventually_bound_le_threshold
    sample cells weight score referenceShare loading weightBound loadingBound
    (fun index => epsilon index * scale index) hloading_nonneg hweight
    hloading hshare hthreshold

/-- Scaled-threshold tail convergence for finite centered projections. -/
theorem
    tendsto_sum_largeJumpSquare_weight_mul_scoreCellLinearCenteredIndicator_zero_of_eventually_bound_le_epsilon_scale
    (sample : Index -> Finset Unit) (cells : Index -> Finset Cell)
    (weight : Index -> Unit -> Real) (score : Index -> Unit -> Cell)
    (referenceShare loading : Index -> Cell -> Real)
    (weightBound loadingBound epsilon scale : Index -> Real)
    (hloading_nonneg : ∀ᶠ index in l, 0 ≤ loadingBound index)
    (hweight :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> |weight index unit| ≤
          weightBound index)
    (hloading :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index -> |loading index cell| ≤
          loadingBound index)
    (hshare :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index -> |referenceShare index cell| ≤ 1)
    (hthreshold :
      ∀ᶠ index in l,
        weightBound index *
            (((cells index).card : Real) * (loadingBound index * 2)) ≤
          epsilon index * scale index) :
    Tendsto
      (fun index =>
        ∑ unit ∈ sample index,
          largeJumpSquare
            (weight index unit *
              scoreCellLinearCenteredIndicator (cells index) (score index)
                (referenceShare index) (loading index) unit)
            (epsilon index * scale index))
      l (nhds 0) := by
  exact tendsto_zero_of_eventually_eq_zero
    (fun index =>
      ∑ unit ∈ sample index,
        largeJumpSquare
          (weight index unit *
            scoreCellLinearCenteredIndicator (cells index) (score index)
              (referenceShare index) (loading index) unit)
          (epsilon index * scale index))
    (eventually_sum_largeJumpSquare_weight_mul_scoreCellLinearCenteredIndicator_eq_zero_of_eventually_bound_le_epsilon_scale
      sample cells weight score referenceShare loading weightBound
      loadingBound epsilon scale hloading_nonneg hweight hloading hshare
      hthreshold)

/-- PATE double-score scaled-threshold tail convergence. -/
theorem
    tendsto_sum_largeJumpSquare_weight_mul_pateDoubleScoreLinearCenteredIndicator_zero_of_eventually_bound_le_epsilon_scale
    (sample : Index -> Finset Unit)
    (cells :
      Index -> Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (weight : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (referenceShare loading :
      Index -> ((PropensityCell × TreatedProgCell) × ControlProgCell) -> Real)
    (weightBound loadingBound epsilon scale : Index -> Real)
    (hloading_nonneg : ∀ᶠ index in l, 0 ≤ loadingBound index)
    (hweight :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> |weight index unit| ≤
          weightBound index)
    (hloading :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index -> |loading index cell| ≤
          loadingBound index)
    (hshare :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index -> |referenceShare index cell| ≤ 1)
    (hthreshold :
      ∀ᶠ index in l,
        weightBound index *
            (((cells index).card : Real) * (loadingBound index * 2)) ≤
          epsilon index * scale index) :
    Tendsto
      (fun index =>
        ∑ unit ∈ sample index,
          largeJumpSquare
            (weight index unit *
              scoreCellLinearCenteredIndicator (cells index)
                (pateDoubleScore (propensityScore index)
                  (treatedPrognosticScore index)
                  (controlPrognosticScore index))
                (referenceShare index) (loading index) unit)
            (epsilon index * scale index))
      l (nhds 0) :=
  tendsto_sum_largeJumpSquare_weight_mul_scoreCellLinearCenteredIndicator_zero_of_eventually_bound_le_epsilon_scale
    sample cells weight
    (fun index =>
      pateDoubleScore (propensityScore index) (treatedPrognosticScore index)
        (controlPrognosticScore index))
    referenceShare loading weightBound loadingBound epsilon scale
    hloading_nonneg hweight hloading hshare hthreshold

/-- PATT double-score scaled-threshold tail convergence. -/
theorem
    tendsto_sum_largeJumpSquare_weight_mul_pattDoubleScoreLinearCenteredIndicator_zero_of_eventually_bound_le_epsilon_scale
    (sample : Index -> Finset Unit)
    (cells : Index -> Finset (PropensityCell × PATTProgCell))
    (weight : Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (referenceShare loading :
      Index -> (PropensityCell × PATTProgCell) -> Real)
    (weightBound loadingBound epsilon scale : Index -> Real)
    (hloading_nonneg : ∀ᶠ index in l, 0 ≤ loadingBound index)
    (hweight :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> |weight index unit| ≤
          weightBound index)
    (hloading :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index -> |loading index cell| ≤
          loadingBound index)
    (hshare :
      ∀ᶠ index in l,
        ∀ cell, cell ∈ cells index -> |referenceShare index cell| ≤ 1)
    (hthreshold :
      ∀ᶠ index in l,
        weightBound index *
            (((cells index).card : Real) * (loadingBound index * 2)) ≤
          epsilon index * scale index) :
    Tendsto
      (fun index =>
        ∑ unit ∈ sample index,
          largeJumpSquare
            (weight index unit *
              scoreCellLinearCenteredIndicator (cells index)
                (pattDoubleScore (propensityScore index)
                  (controlPrognosticScore index))
                (referenceShare index) (loading index) unit)
            (epsilon index * scale index))
      l (nhds 0) :=
  tendsto_sum_largeJumpSquare_weight_mul_scoreCellLinearCenteredIndicator_zero_of_eventually_bound_le_epsilon_scale
    sample cells weight
    (fun index =>
      pattDoubleScore (propensityScore index) (controlPrognosticScore index))
    referenceShare loading weightBound loadingBound epsilon scale
    hloading_nonneg hweight hloading hshare hthreshold

end WDSM
end Matching
end StatInference
