import StatInference.Matching.WDSM.FiniteCellLoadingEnvelope

/-!
# Finite score-cell scaled loading convergence

WDSM residual coefficients usually carry a shrinking normalization, while the
cellwise reuse/loading factors have finite limits.  This module proves the
deterministic reduction:

`scale -> 0` and `baseLoading cell -> finiteLimit cell`
imply `scale * baseLoading cell -> 0`.

It then feeds that scaled-loading convergence into the finite-cell residual
Lindeberg and residual martingale CLT bridges.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Unit Treated Control Cell TreatedCell ControlCell : Type*}
  {l : Filter Index}

/--
If the common scale vanishes and each fixed finite-cell base loading converges,
then each scaled finite-cell loading converges to zero.
-/
theorem tendsto_scaled_scoreCellLoading_zero_of_tendsto_base
    (cells : Finset Cell)
    (scale : Index -> Real)
    (baseLoading : Index -> Cell -> Real)
    (baseLimit : Cell -> Real)
    (hscale : Tendsto scale l (nhds 0))
    (hbase :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => baseLoading index cell)
          l (nhds (baseLimit cell))) :
    ∀ cell, cell ∈ cells ->
      Tendsto
        (fun index => scale index * baseLoading index cell)
        l (nhds 0) := by
  intro cell hcell
  have hmul := hscale.mul (hbase cell hcell)
  simpa using hmul

/--
The finite absolute-sum envelope of scaled cell loadings vanishes when the
common scale vanishes and every fixed base loading has a finite limit.
-/
theorem tendsto_scoreCellLoadingAbsSumEnvelope_zero_of_scaled_tendsto_base
    [DecidableEq Cell]
    (cells : Finset Cell)
    (scale : Index -> Real)
    (baseLoading : Index -> Cell -> Real)
    (baseLimit : Cell -> Real)
    (hscale : Tendsto scale l (nhds 0))
    (hbase :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => baseLoading index cell)
          l (nhds (baseLimit cell))) :
    Tendsto
      (fun index =>
        scoreCellLoadingAbsSumEnvelope cells
          (fun index cell => scale index * baseLoading index cell) index)
      l (nhds 0) :=
  tendsto_scoreCellLoadingAbsSumEnvelope_zero cells
    (fun index cell => scale index * baseLoading index cell)
    (tendsto_scaled_scoreCellLoading_zero_of_tendsto_base
      cells scale baseLoading baseLimit hscale hbase)

/--
One-arm residual Lindeberg condition from scaled finite-cell base loadings,
finite-cell residual third-moment convergence, and score-measurability.
-/
theorem residualLindebergCondition_of_scaled_scoreCellLoading_tendsto_base_and_thirdMoment
    [DecidableEq Cell]
    (cells : Finset Cell)
    (sample : Index -> Finset Unit)
    (weight : Index -> Unit -> Real)
    (score : Index -> Unit -> Cell)
    (coefficient residual : Index -> Unit -> Real)
    (scale : Index -> Real)
    (baseCoefficientLoading : Index -> Cell -> Real)
    (baseCoefficientLimit : Cell -> Real)
    (thirdMomentLoading massLimit : Cell -> Real)
    (hscale : Tendsto scale l (nhds 0))
    (hweight_nonneg :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> 0 ≤ weight index unit)
    (hcover_eventually :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells)
    (hcover :
      ∀ index unit, unit ∈ sample index -> score index unit ∈ cells)
    (hcoefficient :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          coefficient index unit =
            scale index * baseCoefficientLoading index (score index unit))
    (hbase :
      ∀ cell, cell ∈ cells ->
        Tendsto (fun index => baseCoefficientLoading index cell)
          l (nhds (baseCoefficientLimit cell)))
    (hthirdLoading :
      ∀ index unit, unit ∈ sample index ->
        thirdMomentLoading (score index unit) = |residual index unit| ^ 3)
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample weight score massLimit) :
    residualLindebergCondition (l := l) sample weight coefficient residual :=
  residualLindebergCondition_of_scoreCellLoading_tendsto_zero_and_thirdMoment
    cells sample weight score coefficient residual
    (fun index cell => scale index * baseCoefficientLoading index cell)
    thirdMomentLoading massLimit hweight_nonneg hcover_eventually hcover
    hcoefficient
    (tendsto_scaled_scoreCellLoading_zero_of_tendsto_base
      cells scale baseCoefficientLoading baseCoefficientLimit hscale hbase)
    hthirdLoading hmass

/--
Two-arm residual Lindeberg condition from scaled finite-cell base loadings in
both arms, finite-cell residual third-moment convergence, and
score-measurability.
-/
theorem twoArmResidualLindebergCondition_of_scaled_scoreCellLoading_tendsto_base_and_thirdMoments
    [DecidableEq TreatedCell] [DecidableEq ControlCell]
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedScale controlScale : Index -> Real)
    (treatedBaseCoefficientLoading : Index -> TreatedCell -> Real)
    (controlBaseCoefficientLoading : Index -> ControlCell -> Real)
    (treatedBaseCoefficientLimit : TreatedCell -> Real)
    (controlBaseCoefficientLimit : ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (htreatedScale : Tendsto treatedScale l (nhds 0))
    (hcontrolScale : Tendsto controlScale l (nhds 0))
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoverEventually :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCoverEventually :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCover :
      ∀ index treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ index control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedScale index *
              treatedBaseCoefficientLoading index
                (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlScale index *
              controlBaseCoefficientLoading index
                (controlScore index control))
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
    (htreatedThirdLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedThirdMomentLoading (treatedScore index treated) =
          |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ index control, control ∈ controlSample index ->
        controlThirdMomentLoading (controlScore index control) =
          |controlResidual index control| ^ 3)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit) :
    twoArmResidualLindebergCondition (l := l) treatedSample controlSample
      treatedWeight treatedCoefficient treatedResidual
      controlWeight controlCoefficient controlResidual :=
  twoArmResidualLindebergCondition_of_scoreCellLoading_tendsto_zero_and_thirdMoments
    treatedCells controlCells treatedSample controlSample treatedWeight
    treatedCoefficient treatedResidual controlWeight controlCoefficient
    controlResidual treatedScore controlScore
    (fun index cell =>
      treatedScale index * treatedBaseCoefficientLoading index cell)
    (fun index cell =>
      controlScale index * controlBaseCoefficientLoading index cell)
    treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
    controlMassLimit htreatedWeightNonneg hcontrolWeightNonneg
    htreatedCoverEventually hcontrolCoverEventually htreatedCover
    hcontrolCover htreatedCoefficient hcontrolCoefficient
    (tendsto_scaled_scoreCellLoading_zero_of_tendsto_base
      treatedCells treatedScale treatedBaseCoefficientLoading
      treatedBaseCoefficientLimit htreatedScale htreatedBase)
    (tendsto_scaled_scoreCellLoading_zero_of_tendsto_base
      controlCells controlScale controlBaseCoefficientLoading
      controlBaseCoefficientLimit hcontrolScale hcontrolBase)
    htreatedThirdLoading hcontrolThirdLoading htreatedMass hcontrolMass

/--
Residual CLT and variance formula from scaled finite-cell base loadings,
finite-cell residual third-moment convergence, and the explicit residual
martingale-array probability inputs.
-/
theorem residual_clt_and_variance_formula_of_twoArm_scaled_scoreCellLoading_tendsto_base_thirdMoment_bridge
    [DecidableEq TreatedCell] [DecidableEq ControlCell]
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient treatedResidual :
      Index -> Treated -> Real)
    (controlWeight controlCoefficient controlResidual :
      Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedScale controlScale : Index -> Real)
    (treatedBaseCoefficientLoading : Index -> TreatedCell -> Real)
    (controlBaseCoefficientLoading : Index -> ControlCell -> Real)
    (treatedBaseCoefficientLimit : TreatedCell -> Real)
    (controlBaseCoefficientLimit : ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        input.conditional_lindeberg)
    (hexact : input.exact_weighted_reuse_moment_limits)
    (hregularity : input.residual_moment_regularity)
    (hmartingale : input.martingale_difference_array)
    (hqv : input.predictable_quadratic_variation_stabilization)
    (htreatedScale : Tendsto treatedScale l (nhds 0))
    (hcontrolScale : Tendsto controlScale l (nhds 0))
    (htreatedWeightNonneg :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          0 ≤ treatedWeight index treated)
    (hcontrolWeightNonneg :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          0 ≤ controlWeight index control)
    (htreatedCoverEventually :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCoverEventually :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedCover :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ index control, control ∈ controlSample index ->
        controlScore index control ∈ controlCells)
    (htreatedCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedScale index *
              treatedBaseCoefficientLoading index
                (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlScale index *
              controlBaseCoefficientLoading index
                (controlScore index control))
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
    (htreatedThirdLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedThirdMomentLoading (treatedScore index treated) =
          |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ index control, control ∈ controlSample index ->
        controlThirdMomentLoading (controlScore index control) =
          |controlResidual index control| ^ 3)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit) :
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_twoArm_scoreCellLoading_tendsto_zero_thirdMoment_bridge
    treatedCells controlCells treatedSample controlSample treatedWeight
    treatedCoefficient treatedResidual controlWeight controlCoefficient
    controlResidual treatedScore controlScore
    (fun index cell =>
      treatedScale index * treatedBaseCoefficientLoading index cell)
    (fun index cell =>
      controlScale index * controlBaseCoefficientLoading index cell)
    treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
    controlMassLimit input hinputLindeberg hexact hregularity hmartingale
    hqv htreatedWeightNonneg hcontrolWeightNonneg htreatedCoverEventually
    hcontrolCoverEventually htreatedCover hcontrolCover htreatedCoefficient
    hcontrolCoefficient
    (tendsto_scaled_scoreCellLoading_zero_of_tendsto_base
      treatedCells treatedScale treatedBaseCoefficientLoading
      treatedBaseCoefficientLimit htreatedScale htreatedBase)
    (tendsto_scaled_scoreCellLoading_zero_of_tendsto_base
      controlCells controlScale controlBaseCoefficientLoading
      controlBaseCoefficientLimit hcontrolScale hcontrolBase)
    htreatedThirdLoading hcontrolThirdLoading htreatedMass hcontrolMass

end WDSM
end Matching
end StatInference
