import StatInference.Matching.WDSM.FiniteCellVaryingMomentConvergence

/-!
# Finite score-cell quadratic-variation loadings from scaled coefficients

This module removes one deterministic adapter from the residual martingale
interface.  If a residual coefficient is a shrinking/common scale times a
finite score-cell loading, and the conditional variance is also score-cell
measurable, then the quadratic-variation contribution
`coefficient^2 * variance` is a scaled finite score-cell loading.

The result is algebraic, but it is a useful WDSM bridge: later probability
work can prove coefficient and variance score-cell representations, while this
module supplies the QV loading representation and its finite-cell limit.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Unit Cell : Type*} {l : Filter Index}

/--
Pointwise QV-loading identity from a scaled score-cell coefficient and a
score-cell variance representation.
-/
theorem scoreCellQVLoading_eq_of_scaled_coefficient_and_scoreCellVariance
    (coefficient variance : Unit -> Real)
    (score : Unit -> Cell)
    (scale : Real)
    (baseCoefficientLoading varianceLoading : Cell -> Real)
    (unit : Unit)
    (hcoefficient :
      coefficient unit = scale * baseCoefficientLoading (score unit))
    (hvariance :
      variance unit = varianceLoading (score unit)) :
    scale ^ 2 *
        (baseCoefficientLoading (score unit) ^ 2 *
          varianceLoading (score unit)) =
      coefficient unit ^ 2 * variance unit := by
  rw [hcoefficient, hvariance]
  ring

/--
If the base coefficient loading and score-cell variance loading converge on a
fixed finite cell, then their QV base loading converges.
-/
theorem tendsto_scoreCellQVBaseLoading_of_tendsto
    (baseCoefficientLoading varianceLoading : Index -> Cell -> Real)
    (baseCoefficientLimit varianceLimit : Cell -> Real)
    (cell : Cell)
    (hbase :
      Tendsto (fun index => baseCoefficientLoading index cell)
        l (nhds (baseCoefficientLimit cell)))
    (hvariance :
      Tendsto (fun index => varianceLoading index cell)
        l (nhds (varianceLimit cell))) :
    Tendsto
      (fun index =>
        baseCoefficientLoading index cell ^ 2 * varianceLoading index cell)
      l
      (nhds (baseCoefficientLimit cell ^ 2 * varianceLimit cell)) := by
  exact (hbase.pow 2).mul hvariance

/--
One-arm weighted QV convergence from scaled score-cell coefficients,
score-cell conditional variance, finite-cell loading convergence, and
cellwise score-cell mass convergence.
-/
theorem tendsto_weightedQuadraticVariation_of_scaled_coefficients_scoreCellVariance
    [DecidableEq Cell]
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (coefficient variance : Index -> Unit -> Real)
    (coefficientScale : Index -> Real)
    (baseCoefficientLoading varianceLoading : Index -> Cell -> Real)
    (coefficientScaleLimit : Real)
    (baseCoefficientLimit varianceLimit massLimit : Cell -> Real)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hcoefficient :
      ∀ index unit, unit ∈ sample index ->
        coefficient index unit =
          coefficientScale index *
            baseCoefficientLoading index (score index unit))
    (hvariance :
      ∀ index unit, unit ∈ sample index ->
        variance index unit = varianceLoading index (score index unit))
    (hscale :
      Tendsto coefficientScale l (nhds coefficientScaleLimit))
    (hbase :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index => baseCoefficientLoading index cell)
          l (nhds (baseCoefficientLimit cell)))
    (hvarianceLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index => varianceLoading index cell)
          l (nhds (varianceLimit cell)))
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample weight score
        massLimit) :
    Tendsto
      (fun index =>
        weightedQuadraticVariation (sample index) (weight index)
          (coefficient index) (variance index))
      l
      (nhds
        (weightedScoreCellMomentLimit cells
          (fun cell =>
            coefficientScaleLimit ^ 2 *
              (baseCoefficientLimit cell ^ 2 * varianceLimit cell))
          massLimit)) := by
  exact
    tendsto_weightedQuadraticVariation_of_scaled_loading_cellwiseScoreCellMassLLN
      cells sample weight score coefficient variance
      (fun index => coefficientScale index ^ 2)
      (fun index cell =>
        baseCoefficientLoading index cell ^ 2 *
          varianceLoading index cell)
      (coefficientScaleLimit ^ 2)
      (fun cell => baseCoefficientLimit cell ^ 2 * varianceLimit cell)
      massLimit hcover
      (fun index unit hunit =>
        scoreCellQVLoading_eq_of_scaled_coefficient_and_scoreCellVariance
          (coefficient index) (variance index) (score index)
          (coefficientScale index) (baseCoefficientLoading index)
          (varianceLoading index) unit
          (hcoefficient index unit hunit)
          (hvariance index unit hunit))
      (hscale.pow 2)
      (fun cell hcell =>
        tendsto_scoreCellQVBaseLoading_of_tendsto
          baseCoefficientLoading varianceLoading baseCoefficientLimit
          varianceLimit cell (hbase cell hcell)
          (hvarianceLimit cell hcell))
      hmass

/--
Two-arm heterogeneous weighted QV convergence from arm-specific scaled
score-cell coefficients and score-cell variance representations.
-/
theorem tendsto_twoArm_weightedQuadraticVariation_of_scaled_coefficients_scoreCellVariance_hetero
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
    (treatedCoefficientScale controlCoefficientScale : Index -> Real)
    (treatedBaseCoefficientLoading : Index -> TreatedCell -> Real)
    (controlBaseCoefficientLoading : Index -> ControlCell -> Real)
    (treatedVarianceLoading : Index -> TreatedCell -> Real)
    (controlVarianceLoading : Index -> ControlCell -> Real)
    (treatedCoefficientScaleLimit controlCoefficientScaleLimit : Real)
    (treatedBaseCoefficientLimit : TreatedCell -> Real)
    (controlBaseCoefficientLimit : ControlCell -> Real)
    (treatedVarianceLimit treatedMassLimit : TreatedCell -> Real)
    (controlVarianceLimit controlMassLimit : ControlCell -> Real)
    (htreatedCover :
      ∀ index unit, unit ∈ treatedSample index ->
        treatedScore index unit ∈ treatedCells)
    (hcontrolCover :
      ∀ index unit, unit ∈ controlSample index ->
        controlScore index unit ∈ controlCells)
    (htreatedCoefficient :
      ∀ index unit, unit ∈ treatedSample index ->
        treatedCoefficient index unit =
          treatedCoefficientScale index *
            treatedBaseCoefficientLoading index (treatedScore index unit))
    (hcontrolCoefficient :
      ∀ index unit, unit ∈ controlSample index ->
        controlCoefficient index unit =
          controlCoefficientScale index *
            controlBaseCoefficientLoading index (controlScore index unit))
    (htreatedVariance :
      ∀ index unit, unit ∈ treatedSample index ->
        treatedVariance index unit =
          treatedVarianceLoading index (treatedScore index unit))
    (hcontrolVariance :
      ∀ index unit, unit ∈ controlSample index ->
        controlVariance index unit =
          controlVarianceLoading index (controlScore index unit))
    (htreatedScale :
      Tendsto treatedCoefficientScale l
        (nhds treatedCoefficientScaleLimit))
    (hcontrolScale :
      Tendsto controlCoefficientScale l
        (nhds controlCoefficientScaleLimit))
    (htreatedBase :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedBaseCoefficientLoading index cell)
          l (nhds (treatedBaseCoefficientLimit cell)))
    (hcontrolBase :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlBaseCoefficientLoading index cell)
          l (nhds (controlBaseCoefficientLimit cell)))
    (htreatedVarianceLimit :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedVarianceLoading index cell)
          l (nhds (treatedVarianceLimit cell)))
    (hcontrolVarianceLimit :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlVarianceLoading index cell)
          l (nhds (controlVarianceLimit cell)))
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
            (fun cell =>
              treatedCoefficientScaleLimit ^ 2 *
                (treatedBaseCoefficientLimit cell ^ 2 *
                  treatedVarianceLimit cell))
            treatedMassLimit +
          weightedScoreCellMomentLimit controlCells
            (fun cell =>
              controlCoefficientScaleLimit ^ 2 *
                (controlBaseCoefficientLimit cell ^ 2 *
                  controlVarianceLimit cell))
            controlMassLimit)) :=
  (tendsto_weightedQuadraticVariation_of_scaled_coefficients_scoreCellVariance
    treatedCells treatedSample treatedWeight treatedScore treatedCoefficient
    treatedVariance treatedCoefficientScale treatedBaseCoefficientLoading
    treatedVarianceLoading treatedCoefficientScaleLimit
    treatedBaseCoefficientLimit treatedVarianceLimit treatedMassLimit
    htreatedCover htreatedCoefficient htreatedVariance htreatedScale
    htreatedBase htreatedVarianceLimit htreatedMass).add
  (tendsto_weightedQuadraticVariation_of_scaled_coefficients_scoreCellVariance
    controlCells controlSample controlWeight controlScore controlCoefficient
    controlVariance controlCoefficientScale controlBaseCoefficientLoading
    controlVarianceLoading controlCoefficientScaleLimit
    controlBaseCoefficientLimit controlVarianceLimit controlMassLimit
    hcontrolCover hcontrolCoefficient hcontrolVariance hcontrolScale
    hcontrolBase hcontrolVarianceLimit hcontrolMass)

/--
One-arm weighted QV convergence when the coefficient, variance, and cover
representations hold eventually.  This is the asymptotic form needed when
denominators or score partitions are only eventually well-defined.
-/
theorem tendsto_weightedQuadraticVariation_of_eventually_scaled_coefficients_scoreCellVariance
    [DecidableEq Cell]
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (coefficient variance : Index -> Unit -> Real)
    (coefficientScale : Index -> Real)
    (baseCoefficientLoading varianceLoading : Index -> Cell -> Real)
    (coefficientScaleLimit : Real)
    (baseCoefficientLimit varianceLimit massLimit : Cell -> Real)
    (hcover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells)
    (hcoefficient :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          coefficient index unit =
            coefficientScale index *
              baseCoefficientLoading index (score index unit))
    (hvariance :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          variance index unit = varianceLoading index (score index unit))
    (hscale :
      Tendsto coefficientScale l (nhds coefficientScaleLimit))
    (hbase :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index => baseCoefficientLoading index cell)
          l (nhds (baseCoefficientLimit cell)))
    (hvarianceLimit :
      ∀ cell, cell ∈ cells ->
        Tendsto
          (fun index => varianceLoading index cell)
          l (nhds (varianceLimit cell)))
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample weight score
        massLimit) :
    Tendsto
      (fun index =>
        weightedQuadraticVariation (sample index) (weight index)
          (coefficient index) (variance index))
      l
      (nhds
        (weightedScoreCellMomentLimit cells
          (fun cell =>
            coefficientScaleLimit ^ 2 *
              (baseCoefficientLimit cell ^ 2 * varianceLimit cell))
          massLimit)) := by
  have hmom :
      Tendsto
        (fun index =>
          weightedScoreCellMoment cells (sample index) (weight index)
            (score index)
            (fun cell =>
              coefficientScale index ^ 2 *
                (baseCoefficientLoading index cell ^ 2 *
                  varianceLoading index cell)))
        l
        (nhds
          (weightedScoreCellMomentLimit cells
            (fun cell =>
              coefficientScaleLimit ^ 2 *
                (baseCoefficientLimit cell ^ 2 * varianceLimit cell))
            massLimit)) :=
    tendsto_weightedScoreCellMoment_of_cellwiseScoreCellMassLLN_of_tendsto_loading
      cells sample weight score
      (fun index cell =>
        coefficientScale index ^ 2 *
          (baseCoefficientLoading index cell ^ 2 *
            varianceLoading index cell))
      (fun cell =>
        coefficientScaleLimit ^ 2 *
          (baseCoefficientLimit cell ^ 2 * varianceLimit cell))
      massLimit
      (fun cell hcell =>
        (hscale.pow 2).mul
          (tendsto_scoreCellQVBaseLoading_of_tendsto
            baseCoefficientLoading varianceLoading baseCoefficientLimit
            varianceLimit cell (hbase cell hcell)
            (hvarianceLimit cell hcell)))
      hmass
  have heq :
      (fun index =>
        weightedQuadraticVariation (sample index) (weight index)
          (coefficient index) (variance index)) =ᶠ[l]
      (fun index =>
        weightedScoreCellMoment cells (sample index) (weight index)
          (score index)
          (fun cell =>
            coefficientScale index ^ 2 *
              (baseCoefficientLoading index cell ^ 2 *
                varianceLoading index cell))) := by
    filter_upwards [hcover, hcoefficient, hvariance] with index hcoverIndex
      hcoefficientIndex hvarianceIndex
    exact
      weightedQuadraticVariation_eq_weightedScoreCellMoment_of_scoreMeasurable
        cells (sample index) (weight index) (coefficient index)
        (variance index) (score index)
        (fun cell =>
          coefficientScale index ^ 2 *
            (baseCoefficientLoading index cell ^ 2 *
              varianceLoading index cell))
        hcoverIndex
        (fun unit hunit =>
          scoreCellQVLoading_eq_of_scaled_coefficient_and_scoreCellVariance
            (coefficient index) (variance index) (score index)
            (coefficientScale index) (baseCoefficientLoading index)
            (varianceLoading index) unit
            (hcoefficientIndex unit hunit)
            (hvarianceIndex unit hunit))
  exact hmom.congr' heq.symm

/--
Two-arm heterogeneous weighted QV convergence from eventually valid
arm-specific scaled coefficient and score-cell variance representations.
-/
theorem tendsto_twoArm_weightedQuadraticVariation_of_eventually_scaled_coefficients_scoreCellVariance_hetero
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
    (treatedCoefficientScale controlCoefficientScale : Index -> Real)
    (treatedBaseCoefficientLoading : Index -> TreatedCell -> Real)
    (controlBaseCoefficientLoading : Index -> ControlCell -> Real)
    (treatedVarianceLoading : Index -> TreatedCell -> Real)
    (controlVarianceLoading : Index -> ControlCell -> Real)
    (treatedCoefficientScaleLimit controlCoefficientScaleLimit : Real)
    (treatedBaseCoefficientLimit : TreatedCell -> Real)
    (controlBaseCoefficientLimit : ControlCell -> Real)
    (treatedVarianceLimit treatedMassLimit : TreatedCell -> Real)
    (controlVarianceLimit controlMassLimit : ControlCell -> Real)
    (htreatedCover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ treatedSample index ->
          treatedScore index unit ∈ treatedCells)
    (hcontrolCover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          controlScore index unit ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ treatedSample index ->
          treatedCoefficient index unit =
            treatedCoefficientScale index *
              treatedBaseCoefficientLoading index (treatedScore index unit))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          controlCoefficient index unit =
            controlCoefficientScale index *
              controlBaseCoefficientLoading index (controlScore index unit))
    (htreatedVariance :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ treatedSample index ->
          treatedVariance index unit =
            treatedVarianceLoading index (treatedScore index unit))
    (hcontrolVariance :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ controlSample index ->
          controlVariance index unit =
            controlVarianceLoading index (controlScore index unit))
    (htreatedScale :
      Tendsto treatedCoefficientScale l
        (nhds treatedCoefficientScaleLimit))
    (hcontrolScale :
      Tendsto controlCoefficientScale l
        (nhds controlCoefficientScaleLimit))
    (htreatedBase :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedBaseCoefficientLoading index cell)
          l (nhds (treatedBaseCoefficientLimit cell)))
    (hcontrolBase :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlBaseCoefficientLoading index cell)
          l (nhds (controlBaseCoefficientLimit cell)))
    (htreatedVarianceLimit :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedVarianceLoading index cell)
          l (nhds (treatedVarianceLimit cell)))
    (hcontrolVarianceLimit :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlVarianceLoading index cell)
          l (nhds (controlVarianceLimit cell)))
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
            (fun cell =>
              treatedCoefficientScaleLimit ^ 2 *
                (treatedBaseCoefficientLimit cell ^ 2 *
                  treatedVarianceLimit cell))
            treatedMassLimit +
          weightedScoreCellMomentLimit controlCells
            (fun cell =>
              controlCoefficientScaleLimit ^ 2 *
                (controlBaseCoefficientLimit cell ^ 2 *
                  controlVarianceLimit cell))
            controlMassLimit)) :=
  (tendsto_weightedQuadraticVariation_of_eventually_scaled_coefficients_scoreCellVariance
    treatedCells treatedSample treatedWeight treatedScore treatedCoefficient
    treatedVariance treatedCoefficientScale treatedBaseCoefficientLoading
    treatedVarianceLoading treatedCoefficientScaleLimit
    treatedBaseCoefficientLimit treatedVarianceLimit treatedMassLimit
    htreatedCover htreatedCoefficient htreatedVariance htreatedScale
    htreatedBase htreatedVarianceLimit htreatedMass).add
  (tendsto_weightedQuadraticVariation_of_eventually_scaled_coefficients_scoreCellVariance
    controlCells controlSample controlWeight controlScore controlCoefficient
    controlVariance controlCoefficientScale controlBaseCoefficientLoading
    controlVarianceLoading controlCoefficientScaleLimit
    controlBaseCoefficientLimit controlVarianceLimit controlMassLimit
    hcontrolCover hcontrolCoefficient hcontrolVariance hcontrolScale
    hcontrolBase hcontrolVarianceLimit hcontrolMass)

end WDSM
end Matching
end StatInference
