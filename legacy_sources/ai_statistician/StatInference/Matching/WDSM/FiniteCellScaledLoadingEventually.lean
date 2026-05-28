import StatInference.Matching.WDSM.FiniteCellScaledLoading
import StatInference.Matching.WDSM.FiniteCellResidualThirdMomentEventually

/-!
# Eventually valid scaled finite-cell residual Lindeberg bridges

This module combines scaled score-cell coefficient loadings with the eventual
finite-cell residual third-moment bridges.  It is the asymptotic version of
`FiniteCellScaledLoading`: coefficient representations, cell coverage, and
third-moment score-measurability only need to hold eventually.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Unit Treated Control Cell TreatedCell ControlCell : Type*}
  {l : Filter Index}

/--
One-arm residual Lindeberg condition from an eventually valid scaled
finite-cell coefficient representation, eventual residual third-moment
score-measurability, and cellwise mass convergence.
-/
theorem residualLindebergCondition_of_eventually_scaled_scoreCellLoading_tendsto_base_and_thirdMoment
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
    (hcover :
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index -> score index unit ∈ cells)
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
      ∀ᶠ index in l,
        ∀ unit, unit ∈ sample index ->
          thirdMomentLoading (score index unit) =
            |residual index unit| ^ 3)
    (hmass :
      cellwiseScoreCellMassLLN (l := l) cells sample weight score
        massLimit) :
    residualLindebergCondition (l := l) sample weight coefficient residual :=
  residualLindebergCondition_of_eventually_scoreCellLoading_envelope_and_thirdMoment_of_tendsto_envelope_zero
    cells sample weight score coefficient residual
    (fun index cell => scale index * baseCoefficientLoading index cell)
    thirdMomentLoading massLimit
    (fun index =>
      scoreCellLoadingAbsSumEnvelope cells
        (fun index cell => scale index * baseCoefficientLoading index cell)
        index)
    hweight_nonneg hcover hcoefficient
    (eventually_scoreCellLoadingAbsSumEnvelope_bound cells
      (fun index cell => scale index * baseCoefficientLoading index cell))
    hthirdLoading hmass
    (tendsto_scoreCellLoadingAbsSumEnvelope_zero_of_scaled_tendsto_base
      cells scale baseCoefficientLoading baseCoefficientLimit hscale hbase)

/--
Two-arm residual Lindeberg condition from eventually valid scaled finite-cell
coefficient representations in both arms.
-/
theorem twoArmResidualLindebergCondition_of_eventually_scaled_scoreCellLoading_tendsto_base_and_thirdMoments
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
    (htreatedCover :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
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
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedThirdMomentLoading (treatedScore index treated) =
            |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
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
  twoArmResidualLindebergCondition_of_eventually_scoreCellLoading_envelopes_and_thirdMoments_of_tendsto_envelopes_zero
    treatedCells controlCells treatedSample controlSample treatedWeight
    treatedCoefficient treatedResidual controlWeight controlCoefficient
    controlResidual treatedScore controlScore
    (fun index cell =>
      treatedScale index * treatedBaseCoefficientLoading index cell)
    (fun index cell =>
      controlScale index * controlBaseCoefficientLoading index cell)
    treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
    controlMassLimit
    (fun index =>
      scoreCellLoadingAbsSumEnvelope treatedCells
        (fun index cell =>
          treatedScale index * treatedBaseCoefficientLoading index cell)
        index)
    (fun index =>
      scoreCellLoadingAbsSumEnvelope controlCells
        (fun index cell =>
          controlScale index * controlBaseCoefficientLoading index cell)
        index)
    htreatedWeightNonneg hcontrolWeightNonneg htreatedCover hcontrolCover
    htreatedCoefficient hcontrolCoefficient
    (eventually_scoreCellLoadingAbsSumEnvelope_bound treatedCells
      (fun index cell =>
        treatedScale index * treatedBaseCoefficientLoading index cell))
    (eventually_scoreCellLoadingAbsSumEnvelope_bound controlCells
      (fun index cell =>
        controlScale index * controlBaseCoefficientLoading index cell))
    htreatedThirdLoading hcontrolThirdLoading htreatedMass hcontrolMass
    (tendsto_scoreCellLoadingAbsSumEnvelope_zero_of_scaled_tendsto_base
      treatedCells treatedScale treatedBaseCoefficientLoading
      treatedBaseCoefficientLimit htreatedScale htreatedBase)
    (tendsto_scoreCellLoadingAbsSumEnvelope_zero_of_scaled_tendsto_base
      controlCells controlScale controlBaseCoefficientLoading
      controlBaseCoefficientLimit hcontrolScale hcontrolBase)

/--
Residual CLT and variance formula from eventually valid scaled finite-cell
base loadings, eventual finite-cell residual third-moment measurability, and
the explicit residual martingale-array probability inputs.
-/
theorem residual_clt_and_variance_formula_of_twoArm_eventually_scaled_scoreCellLoading_tendsto_base_thirdMoment_bridge
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
    (htreatedCover :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
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
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedThirdMomentLoading (treatedScore index treated) =
            |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlThirdMomentLoading (controlScore index control) =
            |controlResidual index control| ^ 3)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSample
        treatedWeight treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSample
        controlWeight controlScore controlMassLimit) :
    input.residual_clt ∧ input.residual_variance_formula := by
  have hlindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual :=
    twoArmResidualLindebergCondition_of_eventually_scaled_scoreCellLoading_tendsto_base_and_thirdMoments
      treatedCells controlCells treatedSample controlSample treatedWeight
      treatedCoefficient treatedResidual controlWeight controlCoefficient
      controlResidual treatedScore controlScore treatedScale controlScale
      treatedBaseCoefficientLoading controlBaseCoefficientLoading
      treatedBaseCoefficientLimit controlBaseCoefficientLimit
      treatedThirdMomentLoading treatedMassLimit controlThirdMomentLoading
      controlMassLimit htreatedScale hcontrolScale htreatedWeightNonneg
      hcontrolWeightNonneg htreatedCover hcontrolCover htreatedCoefficient
      hcontrolCoefficient htreatedBase hcontrolBase htreatedThirdLoading
      hcontrolThirdLoading htreatedMass hcontrolMass
  exact
    residual_clt_and_variance_formula_of_martingale_array_input input
      hexact hregularity hmartingale (hinputLindeberg hlindeberg) hqv

end WDSM
end Matching
end StatInference
