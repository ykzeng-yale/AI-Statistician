import StatInference.Matching.WDSM.FiniteCellMomentConvergence
import StatInference.Matching.WDSM.QuadraticVariation
import Mathlib.Tactic.Ring

/-!
# Finite score-cell quadratic-variation convergence

This module connects the residual quadratic-variation premise to finite
score-cell mass convergence.  When the conditional variance contribution
`coefficient^2 * variance` is score-cell measurable, the weighted quadratic
variation is exactly a finite score-cell loading moment.  Consequently,
cellwise score-cell mass convergence supplies the quadratic-variation limit.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter
open scoped BigOperators

variable {Index Unit Cell : Type*} {l : Filter Index} [DecidableEq Cell]

/-- Weighted finite quadratic variation for residual coefficients. -/
noncomputable def weightedQuadraticVariation
    (sample : Finset Unit)
    (weight coefficient variance : Unit -> Real) : Real :=
  weightedSampleSum sample weight
    (fun unit => coefficient unit ^ 2 * variance unit)

/-- The unweighted quadratic variation is the weighted version with unit weights. -/
theorem weightedQuadraticVariation_one_eq_quadraticVariation
    (sample : Finset Unit) (coefficient variance : Unit -> Real) :
    weightedQuadraticVariation sample (fun _unit => 1) coefficient variance =
      quadraticVariation sample coefficient variance := by
  unfold weightedQuadraticVariation weightedSampleSum quadraticVariation
  exact Finset.sum_congr rfl (fun _unit _hunit => by ring)

/--
A finite score-cell loading moment is the same as the weighted sum of the
score-measurable unit-level loading.
-/
theorem weightedScoreCellMoment_eq_weightedSampleSum_scoreFunction_of_mapsTo
    (cells : Finset Cell)
    (sample : Finset Unit)
    (weight : Unit -> Real)
    (score : Unit -> Cell)
    (loading : Cell -> Real)
    (hcover : ∀ unit, unit ∈ sample -> score unit ∈ cells) :
    weightedScoreCellMoment cells sample weight score loading =
      weightedSampleSum sample weight (fun unit => loading (score unit)) := by
  unfold weightedScoreCellMoment
  exact
    (weightedSampleSum_scoreFunction_eq_sum_cellValue_mul_mass
      sample cells weight score loading hcover).symm

/--
If `coefficient^2 * variance` is a function of the finite score cell, weighted
quadratic variation is exactly the corresponding finite loading moment.
-/
theorem weightedQuadraticVariation_eq_weightedScoreCellMoment_of_scoreMeasurable
    (cells : Finset Cell)
    (sample : Finset Unit)
    (weight coefficient variance : Unit -> Real)
    (score : Unit -> Cell)
    (loading : Cell -> Real)
    (hcover : ∀ unit, unit ∈ sample -> score unit ∈ cells)
    (hloading :
      ∀ unit, unit ∈ sample ->
        loading (score unit) = coefficient unit ^ 2 * variance unit) :
    weightedQuadraticVariation sample weight coefficient variance =
      weightedScoreCellMoment cells sample weight score loading := by
  calc
    weightedQuadraticVariation sample weight coefficient variance =
        weightedSampleSum sample weight (fun unit => loading (score unit)) := by
          unfold weightedQuadraticVariation weightedSampleSum
          exact Finset.sum_congr rfl
            (fun unit hunit => by
              simpa using
                congrArg (fun value => weight unit * value)
                  (hloading unit hunit).symm)
    _ = weightedScoreCellMoment cells sample weight score loading := by
        exact
          (weightedScoreCellMoment_eq_weightedSampleSum_scoreFunction_of_mapsTo
            cells sample weight score loading hcover).symm

/--
Cellwise score-cell mass convergence implies convergence of weighted
quadratic variation whenever the conditional variance loading is score-cell
measurable.
-/
theorem tendsto_weightedQuadraticVariation_of_cellwiseScoreCellMassLLN
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (coefficient variance : Index -> Unit -> Real)
    (loading massLimit : Cell -> Real)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hloading :
      ∀ index unit, unit ∈ sample index ->
        loading (score index unit) =
          coefficient index unit ^ 2 * variance index unit)
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample weight score massLimit) :
    Tendsto
      (fun index =>
        weightedQuadraticVariation (sample index) (weight index)
          (coefficient index) (variance index))
      l (nhds (weightedScoreCellMomentLimit cells loading massLimit)) := by
  have hmom :
      Tendsto
        (fun index =>
          weightedScoreCellMoment cells (sample index) (weight index)
            (score index) loading)
        l (nhds (weightedScoreCellMomentLimit cells loading massLimit)) :=
    tendsto_weightedScoreCellMoment_of_cellwiseScoreCellMassLLN
      cells sample weight score loading massLimit hmass
  convert hmom using 1
  ext index
  exact
    weightedQuadraticVariation_eq_weightedScoreCellMoment_of_scoreMeasurable
      cells (sample index) (weight index) (coefficient index)
      (variance index) (score index) loading
      (hcover index) (hloading index)

/--
Counting-measure specialization of score-cell quadratic-variation convergence.
-/
theorem tendsto_quadraticVariation_of_cellwiseScoreCellMassLLN_counting
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (coefficient variance : Index -> Unit -> Real)
    (loading massLimit : Cell -> Real)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hloading :
      ∀ index unit, unit ∈ sample index ->
        loading (score index unit) =
          coefficient index unit ^ 2 * variance index unit)
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample
        (fun _index _unit => 1) score massLimit) :
    Tendsto
      (fun index =>
        quadraticVariation (sample index)
          (coefficient index) (variance index))
      l (nhds (weightedScoreCellMomentLimit cells loading massLimit)) := by
  have hweighted :
      Tendsto
        (fun index =>
          weightedQuadraticVariation (sample index) (fun _unit => 1)
            (coefficient index) (variance index))
        l (nhds (weightedScoreCellMomentLimit cells loading massLimit)) :=
    tendsto_weightedQuadraticVariation_of_cellwiseScoreCellMassLLN
      cells sample (fun _index _unit => 1) score coefficient variance
      loading massLimit hcover hloading hmass
  convert hweighted using 1
  ext index
  exact
    (weightedQuadraticVariation_one_eq_quadraticVariation
      (sample index) (coefficient index) (variance index)).symm

/--
Two-arm weighted quadratic-variation convergence follows by adding the two
finite score-cell loading-moment limits.
-/
theorem tendsto_twoArm_weightedQuadraticVariation_of_cellwiseScoreCellMassLLN
    (cellsT cellsC : Finset Cell)
    (sampleT sampleC : Index -> Finset Unit)
    (weightT weightC : Index -> Unit -> Real)
    (scoreT scoreC : Index -> Unit -> Cell)
    (coefficientT coefficientC varianceT varianceC : Index -> Unit -> Real)
    (loadingT loadingC massLimitT massLimitC : Cell -> Real)
    (hcoverT :
      ∀ index unit, unit ∈ sampleT index -> scoreT index unit ∈ cellsT)
    (hcoverC :
      ∀ index unit, unit ∈ sampleC index -> scoreC index unit ∈ cellsC)
    (hloadingT :
      ∀ index unit, unit ∈ sampleT index ->
        loadingT (scoreT index unit) =
          coefficientT index unit ^ 2 * varianceT index unit)
    (hloadingC :
      ∀ index unit, unit ∈ sampleC index ->
        loadingC (scoreC index unit) =
          coefficientC index unit ^ 2 * varianceC index unit)
    (hmassT :
      cellwiseScoreCellMassLLN (l := l) cellsT sampleT weightT scoreT
        massLimitT)
    (hmassC :
      cellwiseScoreCellMassLLN (l := l) cellsC sampleC weightC scoreC
        massLimitC) :
    Tendsto
      (fun index =>
        weightedQuadraticVariation (sampleT index) (weightT index)
            (coefficientT index) (varianceT index) +
          weightedQuadraticVariation (sampleC index) (weightC index)
            (coefficientC index) (varianceC index))
      l
      (nhds
        (weightedScoreCellMomentLimit cellsT loadingT massLimitT +
          weightedScoreCellMomentLimit cellsC loadingC massLimitC)) := by
  exact
    (tendsto_weightedQuadraticVariation_of_cellwiseScoreCellMassLLN
      cellsT sampleT weightT scoreT coefficientT varianceT
      loadingT massLimitT hcoverT hloadingT hmassT).add
    (tendsto_weightedQuadraticVariation_of_cellwiseScoreCellMassLLN
      cellsC sampleC weightC scoreC coefficientC varianceC
      loadingC massLimitC hcoverC hloadingC hmassC)

end WDSM
end Matching
end StatInference
