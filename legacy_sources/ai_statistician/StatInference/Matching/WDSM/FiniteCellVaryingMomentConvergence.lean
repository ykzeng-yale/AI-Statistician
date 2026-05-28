import StatInference.Matching.WDSM.FiniteCellQuadraticVariationConvergence

/-!
# Finite score-cell moment convergence with varying loadings

Earlier finite-cell moment bridges handle fixed cell loadings.  WDSM residual
quadratic-variation terms often have loadings that depend on the sample index,
for example through estimated matching coefficients.  This module proves the
deterministic finite-cell upgrade:

if every fixed cell loading converges and every fixed cell mass converges, then
the finite weighted loading moment converges to the corresponding limiting
moment.  The same upgrade is then specialized to weighted residual quadratic
variation under score-measurability.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Unit Cell : Type*} {l : Filter Index} [DecidableEq Cell]

/--
Cellwise mass convergence plus cellwise loading convergence implies convergence
of the finite loading moment with index-dependent loadings.
-/
theorem tendsto_weightedScoreCellMoment_of_cellwiseScoreCellMassLLN_of_tendsto_loading
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (loading : Index -> Cell -> Real)
    (loadingLimit massLimit : Cell -> Real)
    (hloading :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => loading index cell)
          l (nhds (loadingLimit cell)))
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample weight score massLimit) :
    Tendsto
      (fun index =>
        weightedScoreCellMoment cells (sample index) (weight index)
          (score index) (loading index))
      l (nhds (weightedScoreCellMomentLimit cells loadingLimit massLimit)) := by
  unfold weightedScoreCellMoment weightedScoreCellMomentLimit
  exact tendsto_sum_cell_values cells
    (fun index cell =>
      loading index cell *
        scoreCellMass (sample index) (weight index) (score index) cell)
    (fun cell => loadingLimit cell * massLimit cell)
    (fun cell hcell => (hloading cell hcell).mul (hmass cell hcell))

/--
Score-cell measurable weighted quadratic variation converges when its
index-dependent score-cell loading converges cellwise and cell masses converge.
-/
theorem tendsto_weightedQuadraticVariation_of_cellwiseScoreCellMassLLN_of_tendsto_loading
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (coefficient variance : Index -> Unit -> Real)
    (loading : Index -> Cell -> Real)
    (loadingLimit massLimit : Cell -> Real)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hloadingMeasurable :
      ∀ index unit, unit ∈ sample index ->
        loading index (score index unit) =
          coefficient index unit ^ 2 * variance index unit)
    (hloadingLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => loading index cell)
          l (nhds (loadingLimit cell)))
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample weight score massLimit) :
    Tendsto
      (fun index =>
        weightedQuadraticVariation (sample index) (weight index)
          (coefficient index) (variance index))
      l (nhds (weightedScoreCellMomentLimit cells loadingLimit massLimit)) := by
  have hmom :
      Tendsto
        (fun index =>
          weightedScoreCellMoment cells (sample index) (weight index)
            (score index) (loading index))
        l (nhds (weightedScoreCellMomentLimit cells loadingLimit massLimit)) :=
    tendsto_weightedScoreCellMoment_of_cellwiseScoreCellMassLLN_of_tendsto_loading
      cells sample weight score loading loadingLimit massLimit
      hloadingLimit hmass
  convert hmom using 1
  ext index
  exact
    weightedQuadraticVariation_eq_weightedScoreCellMoment_of_scoreMeasurable
      cells (sample index) (weight index) (coefficient index)
      (variance index) (score index) (loading index)
      (hcover index) (hloadingMeasurable index)

/--
Score-cell measurable weighted quadratic variation converges when its
index-dependent loading is a common scale times a finite-cell base loading.
-/
theorem tendsto_weightedQuadraticVariation_of_scaled_loading_cellwiseScoreCellMassLLN
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (coefficient variance : Index -> Unit -> Real)
    (scale : Index -> Real)
    (baseLoading : Index -> Cell -> Real)
    (scaleLimit : Real)
    (baseLoadingLimit massLimit : Cell -> Real)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hloadingMeasurable :
      ∀ index unit, unit ∈ sample index ->
        scale index * baseLoading index (score index unit) =
          coefficient index unit ^ 2 * variance index unit)
    (hscale : Tendsto scale l (nhds scaleLimit))
    (hbaseLoadingLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => baseLoading index cell)
          l (nhds (baseLoadingLimit cell)))
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample weight score massLimit) :
    Tendsto
      (fun index =>
        weightedQuadraticVariation (sample index) (weight index)
          (coefficient index) (variance index))
      l
      (nhds
        (weightedScoreCellMomentLimit cells
          (fun cell => scaleLimit * baseLoadingLimit cell) massLimit)) := by
  exact
    tendsto_weightedQuadraticVariation_of_cellwiseScoreCellMassLLN_of_tendsto_loading
      cells sample weight score coefficient variance
      (fun index cell => scale index * baseLoading index cell)
      (fun cell => scaleLimit * baseLoadingLimit cell) massLimit hcover
      hloadingMeasurable
      (fun cell hcell => hscale.mul (hbaseLoadingLimit cell hcell))
      hmass

/--
Two-arm weighted quadratic-variation convergence with index-dependent finite
score-cell loadings.
-/
theorem tendsto_twoArm_weightedQuadraticVariation_of_cellwiseScoreCellMassLLN_of_tendsto_loading
    (cellsT cellsC : Finset Cell)
    (sampleT sampleC : Index -> Finset Unit)
    (weightT weightC : Index -> Unit -> Real)
    (scoreT scoreC : Index -> Unit -> Cell)
    (coefficientT coefficientC varianceT varianceC : Index -> Unit -> Real)
    (loadingT loadingC : Index -> Cell -> Real)
    (loadingLimitT loadingLimitC massLimitT massLimitC : Cell -> Real)
    (hcoverT :
      ∀ index unit, unit ∈ sampleT index -> scoreT index unit ∈ cellsT)
    (hcoverC :
      ∀ index unit, unit ∈ sampleC index -> scoreC index unit ∈ cellsC)
    (hloadingT :
      ∀ index unit, unit ∈ sampleT index ->
        loadingT index (scoreT index unit) =
          coefficientT index unit ^ 2 * varianceT index unit)
    (hloadingC :
      ∀ index unit, unit ∈ sampleC index ->
        loadingC index (scoreC index unit) =
          coefficientC index unit ^ 2 * varianceC index unit)
    (hloadingLimitT :
      ∀ cell, cell ∈ cellsT ->
        Tendsto (fun index => loadingT index cell)
          l (nhds (loadingLimitT cell)))
    (hloadingLimitC :
      ∀ cell, cell ∈ cellsC ->
        Tendsto (fun index => loadingC index cell)
          l (nhds (loadingLimitC cell)))
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
        (weightedScoreCellMomentLimit cellsT loadingLimitT massLimitT +
          weightedScoreCellMomentLimit cellsC loadingLimitC massLimitC)) :=
  (tendsto_weightedQuadraticVariation_of_cellwiseScoreCellMassLLN_of_tendsto_loading
    cellsT sampleT weightT scoreT coefficientT varianceT loadingT
    loadingLimitT massLimitT hcoverT hloadingT hloadingLimitT hmassT).add
  (tendsto_weightedQuadraticVariation_of_cellwiseScoreCellMassLLN_of_tendsto_loading
    cellsC sampleC weightC scoreC coefficientC varianceC loadingC
    loadingLimitC massLimitC hcoverC hloadingC hloadingLimitC hmassC)

/--
Two-arm weighted quadratic-variation convergence with separate treated/control
unit and score-cell types.  This is the form needed by WDSM PATE/PATT
instantiations where arm-specific score partitions are not definitionally the
same type.
-/
theorem tendsto_twoArm_weightedQuadraticVariation_of_cellwiseScoreCellMassLLN_of_tendsto_loading_hetero
    {Treated Control TreatedCell ControlCell : Type*}
    [DecidableEq TreatedCell] [DecidableEq ControlCell]
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight : Index -> Treated -> Real)
    (controlWeight : Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficient treatedVariance : Index -> Treated -> Real)
    (controlCoefficient controlVariance : Index -> Control -> Real)
    (treatedLoading : Index -> TreatedCell -> Real)
    (controlLoading : Index -> ControlCell -> Real)
    (treatedLoadingLimit treatedMassLimit : TreatedCell -> Real)
    (controlLoadingLimit controlMassLimit : ControlCell -> Real)
    (htreatedCover :
      ∀ index unit, unit ∈ treatedSample index ->
        treatedScore index unit ∈ treatedCells)
    (hcontrolCover :
      ∀ index unit, unit ∈ controlSample index ->
        controlScore index unit ∈ controlCells)
    (htreatedLoading :
      ∀ index unit, unit ∈ treatedSample index ->
        treatedLoading index (treatedScore index unit) =
          treatedCoefficient index unit ^ 2 * treatedVariance index unit)
    (hcontrolLoading :
      ∀ index unit, unit ∈ controlSample index ->
        controlLoading index (controlScore index unit) =
          controlCoefficient index unit ^ 2 * controlVariance index unit)
    (htreatedLoadingLimit :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto (fun index => treatedLoading index cell)
          l (nhds (treatedLoadingLimit cell)))
    (hcontrolLoadingLimit :
      ∀ cell, cell ∈ controlCells ->
        Tendsto (fun index => controlLoading index cell)
          l (nhds (controlLoadingLimit cell)))
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit) :
    Tendsto
      (fun index =>
        weightedQuadraticVariation (treatedSample index)
            (treatedWeight index) (treatedCoefficient index)
            (treatedVariance index) +
          weightedQuadraticVariation (controlSample index)
            (controlWeight index) (controlCoefficient index)
            (controlVariance index))
      l
      (nhds
        (weightedScoreCellMomentLimit treatedCells treatedLoadingLimit
            treatedMassLimit +
          weightedScoreCellMomentLimit controlCells controlLoadingLimit
            controlMassLimit)) :=
  (tendsto_weightedQuadraticVariation_of_cellwiseScoreCellMassLLN_of_tendsto_loading
    treatedCells treatedSample treatedWeight treatedScore treatedCoefficient
    treatedVariance treatedLoading treatedLoadingLimit treatedMassLimit
    htreatedCover htreatedLoading htreatedLoadingLimit htreatedMass).add
  (tendsto_weightedQuadraticVariation_of_cellwiseScoreCellMassLLN_of_tendsto_loading
    controlCells controlSample controlWeight controlScore controlCoefficient
    controlVariance controlLoading controlLoadingLimit controlMassLimit
    hcontrolCover hcontrolLoading hcontrolLoadingLimit hcontrolMass)

/--
Heterogeneous two-arm weighted quadratic-variation convergence when each
arm's score-cell QV loading is a common arm-specific scale times a finite-cell
base loading.
-/
theorem tendsto_twoArm_weightedQuadraticVariation_of_scaled_loading_cellwiseScoreCellMassLLN_hetero
    {Treated Control TreatedCell ControlCell : Type*}
    [DecidableEq TreatedCell] [DecidableEq ControlCell]
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight : Index -> Treated -> Real)
    (controlWeight : Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficient treatedVariance : Index -> Treated -> Real)
    (controlCoefficient controlVariance : Index -> Control -> Real)
    (treatedScale controlScale : Index -> Real)
    (treatedBaseLoading : Index -> TreatedCell -> Real)
    (controlBaseLoading : Index -> ControlCell -> Real)
    (treatedScaleLimit controlScaleLimit : Real)
    (treatedBaseLoadingLimit treatedMassLimit : TreatedCell -> Real)
    (controlBaseLoadingLimit controlMassLimit : ControlCell -> Real)
    (htreatedCover :
      ∀ index unit, unit ∈ treatedSample index ->
        treatedScore index unit ∈ treatedCells)
    (hcontrolCover :
      ∀ index unit, unit ∈ controlSample index ->
        controlScore index unit ∈ controlCells)
    (htreatedLoading :
      ∀ index unit, unit ∈ treatedSample index ->
        treatedScale index *
            treatedBaseLoading index (treatedScore index unit) =
          treatedCoefficient index unit ^ 2 * treatedVariance index unit)
    (hcontrolLoading :
      ∀ index unit, unit ∈ controlSample index ->
        controlScale index *
            controlBaseLoading index (controlScore index unit) =
          controlCoefficient index unit ^ 2 * controlVariance index unit)
    (htreatedScale : Tendsto treatedScale l (nhds treatedScaleLimit))
    (hcontrolScale : Tendsto controlScale l (nhds controlScaleLimit))
    (htreatedBaseLoadingLimit :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto (fun index => treatedBaseLoading index cell)
          l (nhds (treatedBaseLoadingLimit cell)))
    (hcontrolBaseLoadingLimit :
      ∀ cell, cell ∈ controlCells ->
        Tendsto (fun index => controlBaseLoading index cell)
          l (nhds (controlBaseLoadingLimit cell)))
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit) :
    Tendsto
      (fun index =>
        weightedQuadraticVariation (treatedSample index)
            (treatedWeight index) (treatedCoefficient index)
            (treatedVariance index) +
          weightedQuadraticVariation (controlSample index)
            (controlWeight index) (controlCoefficient index)
            (controlVariance index))
      l
      (nhds
        (weightedScoreCellMomentLimit treatedCells
            (fun cell => treatedScaleLimit * treatedBaseLoadingLimit cell)
            treatedMassLimit +
          weightedScoreCellMomentLimit controlCells
            (fun cell => controlScaleLimit * controlBaseLoadingLimit cell)
            controlMassLimit)) :=
  (tendsto_weightedQuadraticVariation_of_scaled_loading_cellwiseScoreCellMassLLN
    treatedCells treatedSample treatedWeight treatedScore treatedCoefficient
    treatedVariance treatedScale treatedBaseLoading treatedScaleLimit
    treatedBaseLoadingLimit treatedMassLimit htreatedCover htreatedLoading
    htreatedScale htreatedBaseLoadingLimit htreatedMass).add
  (tendsto_weightedQuadraticVariation_of_scaled_loading_cellwiseScoreCellMassLLN
    controlCells controlSample controlWeight controlScore controlCoefficient
    controlVariance controlScale controlBaseLoading controlScaleLimit
    controlBaseLoadingLimit controlMassLimit hcontrolCover hcontrolLoading
    hcontrolScale hcontrolBaseLoadingLimit hcontrolMass)

end WDSM
end Matching
end StatInference
