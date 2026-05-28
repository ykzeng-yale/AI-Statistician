import StatInference.Matching.WDSM.BootstrapAlgebra
import StatInference.Matching.WDSM.FiniteCellVaryingMomentConvergence

/-!
# Bootstrap finite-cell variance bridge

This module connects the finite bootstrap centered-square variance target to
the existing finite score-cell quadratic-variation convergence route.  It
discharges the deterministic part of bootstrap conditional-variance
convergence: once the centered bootstrap contribution is score-cell
measurable and score-cell masses converge, the centered-square target has a
checked finite-cell limit.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter
open scoped BigOperators

variable {Index Unit Cell : Type*} {l : Filter Index}

/--
The centered-square bootstrap numerator is a quadratic variation with unit
conditional variance proxy.
-/
theorem centeredSquareSum_eq_quadraticVariation_centered
    (sample : Finset Unit) (contribution weight : Unit -> Real)
    (target : Real) :
    centeredSquareSum sample contribution weight target =
      quadraticVariation sample
        (fun unit => contribution unit - target * weight unit)
        (fun _unit => 1) := by
  unfold centeredSquareSum quadraticVariation
  exact Finset.sum_congr rfl
    (fun unit _hunit => by ring)

/--
The normalized bootstrap centered-square target is a fixed scalar multiple of
the centered quadratic variation.
-/
theorem bootstrapCenteredVarianceTarget_eq_scaled_quadraticVariation_centered
    (sample : Finset Unit) (contribution weight : Unit -> Real)
    (target denominator normalizer : Real) :
    bootstrapCenteredVarianceTarget sample contribution weight target
        denominator normalizer =
      (1 / denominator ^ 2) * (1 / normalizer) *
        quadraticVariation sample
          (fun unit => contribution unit - target * weight unit)
          (fun _unit => 1) := by
  unfold bootstrapCenteredVarianceTarget
  rw [centeredSquareSum_eq_quadraticVariation_centered]

/--
Finite-cell route for the bootstrap centered variance target.  The remaining
probabilistic task is to supply the score-cell mass convergence and
score-cell-measurable centered-square loading.
-/
theorem tendsto_bootstrapCenteredVarianceTarget_of_cellwiseScoreCellMassLLN
    [DecidableEq Cell]
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer : Real)
    (loading massLimit : Cell -> Real)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hloading :
      ∀ index unit, unit ∈ sample index ->
        loading (score index unit) =
          (contribution index unit - target * weight index unit) ^ 2)
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample
        (fun _index _unit => 1) score massLimit) :
    Tendsto
      (fun index =>
        bootstrapCenteredVarianceTarget (sample index)
          (contribution index) (weight index) target denominator normalizer)
      l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells loading massLimit)) := by
  let scale : Real := (1 / denominator ^ 2) * (1 / normalizer)
  have hqv :
      Tendsto
        (fun index =>
          quadraticVariation (sample index)
            (fun unit =>
              contribution index unit - target * weight index unit)
            (fun _unit => 1))
        l (nhds (weightedScoreCellMomentLimit cells loading massLimit)) :=
    tendsto_quadraticVariation_of_cellwiseScoreCellMassLLN_counting
      cells sample score
      (fun index unit =>
        contribution index unit - target * weight index unit)
      (fun _index _unit => 1) loading massLimit hcover
      (fun index unit hunit => by
        have h := hloading index unit hunit
        simpa using h)
      hmass
  have hscaled :
      Tendsto
        (fun index =>
          scale *
            quadraticVariation (sample index)
              (fun unit =>
                contribution index unit - target * weight index unit)
              (fun _unit => 1))
        l
        (nhds
          (scale * weightedScoreCellMomentLimit cells loading massLimit)) :=
    (tendsto_const_nhds.mul hqv)
  convert hscaled using 1
  ext index
  dsimp [scale]
  rw [bootstrapCenteredVarianceTarget_eq_scaled_quadraticVariation_centered]

/--
Varying-loading finite-cell route for the bootstrap centered variance target.
This is the form needed when centered bootstrap contributions depend on the
sample index through estimated scores, normalizations, or reuse weights.
-/
theorem tendsto_bootstrapCenteredVarianceTarget_of_cellwiseScoreCellMassLLN_of_tendsto_loading
    [DecidableEq Cell]
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer : Real)
    (loading : Index -> Cell -> Real)
    (loadingLimit massLimit : Cell -> Real)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hloading :
      ∀ index unit, unit ∈ sample index ->
        loading index (score index unit) =
          (contribution index unit - target * weight index unit) ^ 2)
    (hloadingLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => loading index cell)
          l (nhds (loadingLimit cell)))
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample
        (fun _index _unit => 1) score massLimit) :
    Tendsto
      (fun index =>
        bootstrapCenteredVarianceTarget (sample index)
          (contribution index) (weight index) target denominator normalizer)
      l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells loadingLimit massLimit)) := by
  let scale : Real := (1 / denominator ^ 2) * (1 / normalizer)
  have hweighted :
      Tendsto
        (fun index =>
          weightedQuadraticVariation (sample index) (fun _unit => 1)
            (fun unit =>
              contribution index unit - target * weight index unit)
            (fun _unit => 1))
        l (nhds (weightedScoreCellMomentLimit cells loadingLimit massLimit)) :=
    tendsto_weightedQuadraticVariation_of_cellwiseScoreCellMassLLN_of_tendsto_loading
      cells sample (fun _index _unit => 1) score
      (fun index unit =>
        contribution index unit - target * weight index unit)
      (fun _index _unit => 1) loading loadingLimit massLimit hcover
      (fun index unit hunit => by
        rw [hloading index unit hunit]
        ring)
      hloadingLimit hmass
  have hqv :
      Tendsto
        (fun index =>
          quadraticVariation (sample index)
            (fun unit =>
              contribution index unit - target * weight index unit)
            (fun _unit => 1))
        l (nhds (weightedScoreCellMomentLimit cells loadingLimit massLimit)) := by
    convert hweighted using 1
    ext index
    exact
      (weightedQuadraticVariation_one_eq_quadraticVariation
        (sample index)
        (fun unit =>
          contribution index unit - target * weight index unit)
        (fun _unit => 1)).symm
  have hscaled :
      Tendsto
        (fun index =>
          scale *
            quadraticVariation (sample index)
              (fun unit =>
                contribution index unit - target * weight index unit)
              (fun _unit => 1))
        l
        (nhds
          (scale * weightedScoreCellMomentLimit cells loadingLimit
            massLimit)) :=
    (tendsto_const_nhds.mul hqv)
  convert hscaled using 1
  ext index
  dsimp [scale]
  rw [bootstrapCenteredVarianceTarget_eq_scaled_quadraticVariation_centered]

/--
Cellwise convergence of score-cell contribution and denominator-weight
representations implies convergence of the centered-square loading.
-/
theorem tendsto_centeredSquareLoading_of_tendsto_cell_contribution_weight
    (cells : Finset Cell)
    (cellContribution cellWeight loading : Index -> Cell -> Real)
    (contributionLimit weightLimit : Cell -> Real)
    (target : Real)
    (hloading :
      ∀ index cell, cell ∈ cells ->
        loading index cell =
          (cellContribution index cell - target * cellWeight index cell) ^ 2)
    (hcontributionLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellContribution index cell)
          l (nhds (contributionLimit cell)))
    (hweightLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellWeight index cell)
          l (nhds (weightLimit cell))) :
    ∀ cell, cell ∈ cells ->
      Tendsto (fun index => loading index cell)
        l (nhds ((contributionLimit cell - target * weightLimit cell) ^ 2)) :=
  fun cell hcell => by
    have hcenter :
        Tendsto
          (fun index =>
            cellContribution index cell - target * cellWeight index cell)
          l
          (nhds (contributionLimit cell - target * weightLimit cell)) :=
      (hcontributionLimit cell hcell).sub
        (tendsto_const_nhds.mul (hweightLimit cell hcell))
    have hsquare :
        Tendsto
          (fun index =>
            (cellContribution index cell - target * cellWeight index cell) ^ 2)
          l
          (nhds ((contributionLimit cell - target * weightLimit cell) ^ 2)) := by
      have hmul := hcenter.mul hcenter
      convert hmul using 1
      · ext index
        ring_nf
      · ring_nf
    convert hsquare using 1
    ext index
    rw [hloading index cell hcell]

/--
Bootstrap centered-square variance convergence from score-cell contribution
and denominator-weight limits.  This packages the common WDSM route:
contribution and denominator weights are score-cell representable, their
cellwise limits exist, and score-cell masses converge.
-/
theorem tendsto_bootstrapCenteredVarianceTarget_of_cellwiseScoreCellMassLLN_of_cell_contribution_weight_limits
    [DecidableEq Cell]
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hcontributionCell :
      ∀ index unit, unit ∈ sample index ->
        cellContribution index (score index unit) = contribution index unit)
    (hweightCell :
      ∀ index unit, unit ∈ sample index ->
        cellWeight index (score index unit) = weight index unit)
    (hcontributionLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellContribution index cell)
          l (nhds (contributionLimit cell)))
    (hweightLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellWeight index cell)
          l (nhds (weightLimit cell)))
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample
        (fun _index _unit => 1) score massLimit) :
    Tendsto
      (fun index =>
        bootstrapCenteredVarianceTarget (sample index)
          (contribution index) (weight index) target denominator normalizer)
      l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) :=
  tendsto_bootstrapCenteredVarianceTarget_of_cellwiseScoreCellMassLLN_of_tendsto_loading
    (l := l) cells sample score contribution weight target denominator
    normalizer
    (fun index cell =>
      (cellContribution index cell - target * cellWeight index cell) ^ 2)
    (fun cell =>
      (contributionLimit cell - target * weightLimit cell) ^ 2)
    massLimit hcover
    (fun index unit hunit => by
      dsimp
      rw [hcontributionCell index unit hunit, hweightCell index unit hunit])
    (tendsto_centeredSquareLoading_of_tendsto_cell_contribution_weight
      (l := l) cells cellContribution cellWeight
      (fun index cell =>
        (cellContribution index cell - target * cellWeight index cell) ^ 2)
      contributionLimit weightLimit target
      (fun _index _cell _hcell => rfl)
      hcontributionLimit hweightLimit)
    hmass

/--
Eventual variant of the score-cell contribution/weight route.  Coverage and
score-cell representations only need to hold eventually, which matches
asymptotic WDSM proofs where estimated-score partitions and denominators are
only valid after a finite burn-in.
-/
theorem tendsto_bootstrapCenteredVarianceTarget_of_eventually_cell_contribution_weight_limits
    [DecidableEq Cell]
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (score : Index -> Unit -> Cell)
    (contribution weight : Index -> Unit -> Real)
    (target denominator normalizer : Real)
    (cellContribution cellWeight : Index -> Cell -> Real)
    (contributionLimit weightLimit massLimit : Cell -> Real)
    (hcover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells)
    (hcontributionCell :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          cellContribution index (score index unit) =
            contribution index unit)
    (hweightCell :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          cellWeight index (score index unit) = weight index unit)
    (hcontributionLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellContribution index cell)
          l (nhds (contributionLimit cell)))
    (hweightLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => cellWeight index cell)
          l (nhds (weightLimit cell)))
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample
        (fun _index _unit => 1) score massLimit) :
    Tendsto
      (fun index =>
        bootstrapCenteredVarianceTarget (sample index)
          (contribution index) (weight index) target denominator normalizer)
      l
      (nhds
        ((1 / denominator ^ 2) * (1 / normalizer) *
          weightedScoreCellMomentLimit cells
            (fun cell =>
              (contributionLimit cell - target * weightLimit cell) ^ 2)
            massLimit)) := by
  let loading : Index -> Cell -> Real :=
    fun index cell =>
      (cellContribution index cell - target * cellWeight index cell) ^ 2
  let loadingLimit : Cell -> Real :=
    fun cell => (contributionLimit cell - target * weightLimit cell) ^ 2
  let scale : Real := (1 / denominator ^ 2) * (1 / normalizer)
  have hloadingLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => loading index cell)
          l (nhds (loadingLimit cell)) :=
    tendsto_centeredSquareLoading_of_tendsto_cell_contribution_weight
      (l := l) cells cellContribution cellWeight loading
      contributionLimit weightLimit target
      (fun _index _cell _hcell => rfl)
      hcontributionLimit hweightLimit
  have hmom :
      Tendsto
        (fun index =>
          weightedScoreCellMoment cells (sample index)
            (fun _unit => 1) (score index) (loading index))
        l
        (nhds
          (weightedScoreCellMomentLimit cells loadingLimit massLimit)) :=
    tendsto_weightedScoreCellMoment_of_cellwiseScoreCellMassLLN_of_tendsto_loading
      cells sample (fun _index _unit => 1) score loading loadingLimit
      massLimit hloadingLimit hmass
  have hscaled :
      Tendsto
        (fun index =>
          scale *
            weightedScoreCellMoment cells (sample index)
              (fun _unit => 1) (score index) (loading index))
        l
        (nhds
          (scale * weightedScoreCellMomentLimit cells loadingLimit
            massLimit)) :=
    tendsto_const_nhds.mul hmom
  have heq :
      (fun index =>
        bootstrapCenteredVarianceTarget (sample index)
          (contribution index) (weight index) target denominator normalizer)
        =ᶠ[l]
      (fun index =>
        scale *
          weightedScoreCellMoment cells (sample index)
            (fun _unit => 1) (score index) (loading index)) := by
    filter_upwards [hcover, hcontributionCell, hweightCell] with index
      hcoverIndex hcontributionIndex hweightIndex
    rw [bootstrapCenteredVarianceTarget_eq_scaled_quadraticVariation_centered]
    dsimp [scale]
    congr 1
    rw [← weightedQuadraticVariation_one_eq_quadraticVariation]
    exact
      weightedQuadraticVariation_eq_weightedScoreCellMoment_of_scoreMeasurable
        cells (sample index) (fun _unit => 1)
        (fun unit => contribution index unit - target * weight index unit)
        (fun _unit => 1) (score index) (loading index) hcoverIndex
        (fun unit hunit => by
          dsimp [loading]
          rw [hcontributionIndex unit hunit, hweightIndex unit hunit]
          ring)
  convert hscaled.congr' heq.symm using 1

end WDSM
end Matching
end StatInference
