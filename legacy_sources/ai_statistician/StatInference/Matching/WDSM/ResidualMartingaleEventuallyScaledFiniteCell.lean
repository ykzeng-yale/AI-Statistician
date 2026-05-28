import StatInference.Matching.WDSM.FiniteCellScaledLoadingEventually
import StatInference.Matching.WDSM.FiniteCellQVLoading
import StatInference.Matching.WDSM.ResidualMartingaleDifferenceBridge

/-!
# Residual martingale bridge from eventually valid finite-cell premises

This module composes the eventual finite-cell Lindeberg route with the
eventual finite-cell quadratic-variation route.  It keeps the Lindeberg
coefficient representation separate from the QV coefficient representation:
the former uses a shrinking scale to prove tail negligibility, while the
latter identifies the predictable quadratic-variation limit through
score-cell variance loadings.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter MeasureTheory
open scoped MeasureTheory

variable {Index Treated Control TreatedCell ControlCell : Type*}
  {l : Filter Index} [DecidableEq TreatedCell] [DecidableEq ControlCell]

/--
Residual CLT and variance formula from eventual scaled finite-cell Lindeberg
premises plus eventual scaled finite-cell QV premises.

The actual residual coefficients are shared, but the two representations are
allowed to use different finite-cell base loadings: a shrinking loading for
Lindeberg and a QV loading paired with score-cell conditional variances.
-/
theorem residual_clt_and_variance_formula_of_eventually_scaled_finiteCell_lindeberg_qv_bridge
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
    (treatedLindebergScale controlLindebergScale : Index -> Real)
    (treatedLindebergBaseLoading : Index -> TreatedCell -> Real)
    (controlLindebergBaseLoading : Index -> ControlCell -> Real)
    (treatedLindebergBaseLimit : TreatedCell -> Real)
    (controlLindebergBaseLimit : ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedVariance : Index -> Treated -> Real)
    (controlVariance : Index -> Control -> Real)
    (treatedQVScale controlQVScale : Index -> Real)
    (treatedQVBaseCoefficientLoading : Index -> TreatedCell -> Real)
    (controlQVBaseCoefficientLoading : Index -> ControlCell -> Real)
    (treatedVarianceLoading : Index -> TreatedCell -> Real)
    (controlVarianceLoading : Index -> ControlCell -> Real)
    (treatedQVScaleLimit controlQVScaleLimit : Real)
    (treatedQVBaseCoefficientLimit : TreatedCell -> Real)
    (controlQVBaseCoefficientLimit : ControlCell -> Real)
    (treatedVarianceLimit : TreatedCell -> Real)
    (controlVarianceLimit : ControlCell -> Real)
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        input.conditional_lindeberg)
    (hinputQV :
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
                treatedQVScaleLimit ^ 2 *
                  (treatedQVBaseCoefficientLimit cell ^ 2 *
                    treatedVarianceLimit cell))
              treatedMassLimit +
            weightedScoreCellMomentLimit controlCells
              (fun cell =>
                controlQVScaleLimit ^ 2 *
                  (controlQVBaseCoefficientLimit cell ^ 2 *
                    controlVarianceLimit cell))
              controlMassLimit)) ->
        input.predictable_quadratic_variation_stabilization)
    (hexact : input.exact_weighted_reuse_moment_limits)
    (hregularity : input.residual_moment_regularity)
    (hmartingale : input.martingale_difference_array)
    (htreatedLindebergScale :
      Tendsto treatedLindebergScale l (nhds 0))
    (hcontrolLindebergScale :
      Tendsto controlLindebergScale l (nhds 0))
    (htreatedQVScale :
      Tendsto treatedQVScale l (nhds treatedQVScaleLimit))
    (hcontrolQVScale :
      Tendsto controlQVScale l (nhds controlQVScaleLimit))
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
    (htreatedLindebergCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedLindebergScale index *
              treatedLindebergBaseLoading index
                (treatedScore index treated))
    (hcontrolLindebergCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlLindebergScale index *
              controlLindebergBaseLoading index
                (controlScore index control))
    (htreatedLindebergBase :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedLindebergBaseLoading index cell)
          l (nhds (treatedLindebergBaseLimit cell)))
    (hcontrolLindebergBase :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlLindebergBaseLoading index cell)
          l (nhds (controlLindebergBaseLimit cell)))
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
    (htreatedQVCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedQVScale index *
              treatedQVBaseCoefficientLoading index
                (treatedScore index treated))
    (hcontrolQVCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlQVScale index *
              controlQVBaseCoefficientLoading index
                (controlScore index control))
    (htreatedVariance :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedVariance index treated =
            treatedVarianceLoading index (treatedScore index treated))
    (hcontrolVariance :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlVariance index control =
            controlVarianceLoading index (controlScore index control))
    (htreatedQVBase :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedQVBaseCoefficientLoading index cell)
          l (nhds (treatedQVBaseCoefficientLimit cell)))
    (hcontrolQVBase :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlQVBaseCoefficientLoading index cell)
          l (nhds (controlQVBaseCoefficientLimit cell)))
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
    input.residual_clt ∧ input.residual_variance_formula := by
  have hlindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual :=
    twoArmResidualLindebergCondition_of_eventually_scaled_scoreCellLoading_tendsto_base_and_thirdMoments
      treatedCells controlCells treatedSample controlSample treatedWeight
      treatedCoefficient treatedResidual controlWeight controlCoefficient
      controlResidual treatedScore controlScore treatedLindebergScale
      controlLindebergScale treatedLindebergBaseLoading
      controlLindebergBaseLoading treatedLindebergBaseLimit
      controlLindebergBaseLimit treatedThirdMomentLoading treatedMassLimit
      controlThirdMomentLoading controlMassLimit htreatedLindebergScale
      hcontrolLindebergScale htreatedWeightNonneg hcontrolWeightNonneg
      htreatedCover hcontrolCover htreatedLindebergCoefficient
      hcontrolLindebergCoefficient htreatedLindebergBase
      hcontrolLindebergBase htreatedThirdLoading hcontrolThirdLoading
      htreatedMass hcontrolMass
  have hqv :
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
                treatedQVScaleLimit ^ 2 *
                  (treatedQVBaseCoefficientLimit cell ^ 2 *
                    treatedVarianceLimit cell))
              treatedMassLimit +
            weightedScoreCellMomentLimit controlCells
              (fun cell =>
                controlQVScaleLimit ^ 2 *
                  (controlQVBaseCoefficientLimit cell ^ 2 *
                    controlVarianceLimit cell))
              controlMassLimit)) :=
    tendsto_twoArm_weightedQuadraticVariation_of_eventually_scaled_coefficients_scoreCellVariance_hetero
      treatedCells controlCells treatedSample controlSample treatedWeight
      controlWeight treatedScore controlScore treatedCoefficient
      treatedVariance controlCoefficient controlVariance treatedQVScale
      controlQVScale treatedQVBaseCoefficientLoading
      controlQVBaseCoefficientLoading treatedVarianceLoading
      controlVarianceLoading treatedQVScaleLimit controlQVScaleLimit
      treatedQVBaseCoefficientLimit controlQVBaseCoefficientLimit
      treatedVarianceLimit treatedMassLimit controlVarianceLimit
      controlMassLimit htreatedCover hcontrolCover htreatedQVCoefficient
      hcontrolQVCoefficient htreatedVariance hcontrolVariance
      htreatedQVScale hcontrolQVScale htreatedQVBase hcontrolQVBase
      htreatedVarianceLimit hcontrolVarianceLimit htreatedMass hcontrolMass
  exact
    residual_clt_and_variance_formula_of_martingale_array_input input
      hexact hregularity hmartingale (hinputLindeberg hlindeberg)
      (hinputQV hqv)

/--
Close the conditional-Lindeberg field of a residual martingale-array input from
eventually valid finite-cell coefficient loadings and finite residual third
moments.  This exposes the reusable Lindeberg half of the larger finite-cell
residual CLT route.
-/
theorem input_conditional_lindeberg_of_eventually_scaled_finiteCell_thirdMoment
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
    (treatedLindebergScale controlLindebergScale : Index -> Real)
    (treatedLindebergBaseLoading : Index -> TreatedCell -> Real)
    (controlLindebergBaseLoading : Index -> ControlCell -> Real)
    (treatedLindebergBaseLimit : TreatedCell -> Real)
    (controlLindebergBaseLimit : ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        input.conditional_lindeberg)
    (htreatedLindebergScale :
      Tendsto treatedLindebergScale l (nhds 0))
    (hcontrolLindebergScale :
      Tendsto controlLindebergScale l (nhds 0))
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
    (htreatedLindebergCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedLindebergScale index *
              treatedLindebergBaseLoading index
                (treatedScore index treated))
    (hcontrolLindebergCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlLindebergScale index *
              controlLindebergBaseLoading index
                (controlScore index control))
    (htreatedLindebergBase :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedLindebergBaseLoading index cell)
          l (nhds (treatedLindebergBaseLimit cell)))
    (hcontrolLindebergBase :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlLindebergBaseLoading index cell)
          l (nhds (controlLindebergBaseLimit cell)))
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
    input.conditional_lindeberg :=
  hinputLindeberg
    (twoArmResidualLindebergCondition_of_eventually_scaled_scoreCellLoading_tendsto_base_and_thirdMoments
      treatedCells controlCells treatedSample controlSample treatedWeight
      treatedCoefficient treatedResidual controlWeight controlCoefficient
      controlResidual treatedScore controlScore treatedLindebergScale
      controlLindebergScale treatedLindebergBaseLoading
      controlLindebergBaseLoading treatedLindebergBaseLimit
      controlLindebergBaseLimit treatedThirdMomentLoading treatedMassLimit
      controlThirdMomentLoading controlMassLimit htreatedLindebergScale
      hcontrolLindebergScale htreatedWeightNonneg hcontrolWeightNonneg
      htreatedCover hcontrolCover htreatedLindebergCoefficient
      hcontrolLindebergCoefficient htreatedLindebergBase
      hcontrolLindebergBase htreatedThirdLoading hcontrolThirdLoading
      htreatedMass hcontrolMass)

/--
Close the conditional-Lindeberg field of an explicit triangular
martingale-array CLT bridge from eventually scaled finite-cell coefficient
loadings and finite residual third moments.

This is the field-level analogue of
`input_conditional_lindeberg_of_eventually_scaled_finiteCell_thirdMoment`:
it targets the imported triangular CLT bridge directly, matching the existing
martingale-difference and predictable-QV triangular field reducers.
-/
theorem triangular_conditional_lindeberg_of_eventually_scaled_finiteCell_thirdMoment
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
    (treatedLindebergScale controlLindebergScale : Index -> Real)
    (treatedLindebergBaseLoading : Index -> TreatedCell -> Real)
    (controlLindebergBaseLoading : Index -> ControlCell -> Real)
    (treatedLindebergBaseLimit : TreatedCell -> Real)
    (controlLindebergBaseLimit : ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (hbridgeLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        martingaleCLT.conditional_lindeberg)
    (htreatedLindebergScale :
      Tendsto treatedLindebergScale l (nhds 0))
    (hcontrolLindebergScale :
      Tendsto controlLindebergScale l (nhds 0))
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
    (htreatedLindebergCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedLindebergScale index *
              treatedLindebergBaseLoading index
                (treatedScore index treated))
    (hcontrolLindebergCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlLindebergScale index *
              controlLindebergBaseLoading index
                (controlScore index control))
    (htreatedLindebergBase :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedLindebergBaseLoading index cell)
          l (nhds (treatedLindebergBaseLimit cell)))
    (hcontrolLindebergBase :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlLindebergBaseLoading index cell)
          l (nhds (controlLindebergBaseLimit cell)))
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
    martingaleCLT.conditional_lindeberg :=
  hbridgeLindeberg
    (twoArmResidualLindebergCondition_of_eventually_scaled_scoreCellLoading_tendsto_base_and_thirdMoments
      treatedCells controlCells treatedSample controlSample treatedWeight
      treatedCoefficient treatedResidual controlWeight controlCoefficient
      controlResidual treatedScore controlScore treatedLindebergScale
      controlLindebergScale treatedLindebergBaseLoading
      controlLindebergBaseLoading treatedLindebergBaseLimit
      controlLindebergBaseLimit treatedThirdMomentLoading treatedMassLimit
      controlThirdMomentLoading controlMassLimit htreatedLindebergScale
      hcontrolLindebergScale htreatedWeightNonneg hcontrolWeightNonneg
      htreatedCover hcontrolCover htreatedLindebergCoefficient
      hcontrolLindebergCoefficient htreatedLindebergBase
      hcontrolLindebergBase htreatedThirdLoading hcontrolThirdLoading
      htreatedMass hcontrolMass)

/--
Close the predictable quadratic-variation field of a residual martingale-array
input from eventually valid finite-cell QV loadings and score-cell mass
convergence.  This exposes the reusable QV half of the larger finite-cell
residual CLT route.
-/
theorem input_predictable_quadratic_variation_stabilization_of_eventually_scaled_finiteCell_qv
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient : Index -> Treated -> Real)
    (controlWeight controlCoefficient : Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedVariance : Index -> Treated -> Real)
    (controlVariance : Index -> Control -> Real)
    (treatedQVScale controlQVScale : Index -> Real)
    (treatedQVBaseCoefficientLoading : Index -> TreatedCell -> Real)
    (controlQVBaseCoefficientLoading : Index -> ControlCell -> Real)
    (treatedVarianceLoading : Index -> TreatedCell -> Real)
    (controlVarianceLoading : Index -> ControlCell -> Real)
    (treatedQVScaleLimit controlQVScaleLimit : Real)
    (treatedQVBaseCoefficientLimit : TreatedCell -> Real)
    (controlQVBaseCoefficientLimit : ControlCell -> Real)
    (treatedVarianceLimit : TreatedCell -> Real)
    (controlVarianceLimit : ControlCell -> Real)
    (treatedMassLimit : TreatedCell -> Real)
    (controlMassLimit : ControlCell -> Real)
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (hinputQV :
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
                treatedQVScaleLimit ^ 2 *
                  (treatedQVBaseCoefficientLimit cell ^ 2 *
                    treatedVarianceLimit cell))
              treatedMassLimit +
            weightedScoreCellMomentLimit controlCells
              (fun cell =>
                controlQVScaleLimit ^ 2 *
                  (controlQVBaseCoefficientLimit cell ^ 2 *
                    controlVarianceLimit cell))
              controlMassLimit)) ->
        input.predictable_quadratic_variation_stabilization)
    (htreatedQVScale :
      Tendsto treatedQVScale l (nhds treatedQVScaleLimit))
    (hcontrolQVScale :
      Tendsto controlQVScale l (nhds controlQVScaleLimit))
    (htreatedCover :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedQVCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedQVScale index *
              treatedQVBaseCoefficientLoading index
                (treatedScore index treated))
    (hcontrolQVCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlQVScale index *
              controlQVBaseCoefficientLoading index
                (controlScore index control))
    (htreatedVariance :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedVariance index treated =
            treatedVarianceLoading index (treatedScore index treated))
    (hcontrolVariance :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlVariance index control =
            controlVarianceLoading index (controlScore index control))
    (htreatedQVBase :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedQVBaseCoefficientLoading index cell)
          l (nhds (treatedQVBaseCoefficientLimit cell)))
    (hcontrolQVBase :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlQVBaseCoefficientLoading index cell)
          l (nhds (controlQVBaseCoefficientLimit cell)))
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
    input.predictable_quadratic_variation_stabilization :=
  hinputQV
    (tendsto_twoArm_weightedQuadraticVariation_of_eventually_scaled_coefficients_scoreCellVariance_hetero
      treatedCells controlCells treatedSample controlSample treatedWeight
      controlWeight treatedScore controlScore treatedCoefficient
      treatedVariance controlCoefficient controlVariance treatedQVScale
      controlQVScale treatedQVBaseCoefficientLoading
      controlQVBaseCoefficientLoading treatedVarianceLoading
      controlVarianceLoading treatedQVScaleLimit controlQVScaleLimit
      treatedQVBaseCoefficientLimit controlQVBaseCoefficientLimit
      treatedVarianceLimit treatedMassLimit controlVarianceLimit
      controlMassLimit htreatedCover hcontrolCover htreatedQVCoefficient
      hcontrolQVCoefficient htreatedVariance hcontrolVariance
      htreatedQVScale hcontrolQVScale htreatedQVBase hcontrolQVBase
      htreatedVarianceLimit hcontrolVarianceLimit htreatedMass hcontrolMass)

/--
Input-level eventual finite-cell Lindeberg/QV endpoint with the
martingale-difference field supplied by concrete treated/control Mathlib
martingales.

This packages the three lower pieces needed by
`ResidualMartingaleArrayCLTVarianceInput`: Mathlib martingales for the
martingale-difference field, finite-cell third-moment evidence for
conditional Lindeberg, and finite-cell variance-loading evidence for
predictable quadratic variation.
-/
theorem
    residual_clt_and_variance_formula_of_eventually_scaled_finiteCell_lindeberg_qv_mathlib_martingales_input
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
    (treatedLindebergScale controlLindebergScale : Index -> Real)
    (treatedLindebergBaseLoading : Index -> TreatedCell -> Real)
    (controlLindebergBaseLoading : Index -> ControlCell -> Real)
    (treatedLindebergBaseLimit : TreatedCell -> Real)
    (controlLindebergBaseLimit : ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedVariance : Index -> Treated -> Real)
    (controlVariance : Index -> Control -> Real)
    (treatedQVScale controlQVScale : Index -> Real)
    (treatedQVBaseCoefficientLoading : Index -> TreatedCell -> Real)
    (controlQVBaseCoefficientLoading : Index -> ControlCell -> Real)
    (treatedVarianceLoading : Index -> TreatedCell -> Real)
    (controlVarianceLoading : Index -> ControlCell -> Real)
    (treatedQVScaleLimit controlQVScaleLimit : Real)
    (treatedQVBaseCoefficientLimit : TreatedCell -> Real)
    (controlQVBaseCoefficientLimit : ControlCell -> Real)
    (treatedVarianceLimit : TreatedCell -> Real)
    (controlVarianceLimit : ControlCell -> Real)
    (input : ResidualMartingaleArrayCLTVarianceInput)
    {Ω E ι : Type*} [Preorder ι] {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} {ℱ : Filtration ι m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (treatedProcess controlProcess : ι -> Ω -> E)
    (htreatedMartingale : Martingale treatedProcess ℱ μ)
    (hcontrolMartingale : Martingale controlProcess ℱ μ)
    (hmartingaleMap :
      Martingale treatedProcess ℱ μ ->
        Martingale controlProcess ℱ μ ->
          input.martingale_difference_array)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        input.conditional_lindeberg)
    (hinputQV :
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
                treatedQVScaleLimit ^ 2 *
                  (treatedQVBaseCoefficientLimit cell ^ 2 *
                    treatedVarianceLimit cell))
              treatedMassLimit +
            weightedScoreCellMomentLimit controlCells
              (fun cell =>
                controlQVScaleLimit ^ 2 *
                  (controlQVBaseCoefficientLimit cell ^ 2 *
                    controlVarianceLimit cell))
              controlMassLimit)) ->
        input.predictable_quadratic_variation_stabilization)
    (hexact : input.exact_weighted_reuse_moment_limits)
    (hregularity : input.residual_moment_regularity)
    (htreatedLindebergScale :
      Tendsto treatedLindebergScale l (nhds 0))
    (hcontrolLindebergScale :
      Tendsto controlLindebergScale l (nhds 0))
    (htreatedQVScale :
      Tendsto treatedQVScale l (nhds treatedQVScaleLimit))
    (hcontrolQVScale :
      Tendsto controlQVScale l (nhds controlQVScaleLimit))
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
    (htreatedLindebergCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedLindebergScale index *
              treatedLindebergBaseLoading index
                (treatedScore index treated))
    (hcontrolLindebergCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlLindebergScale index *
              controlLindebergBaseLoading index
                (controlScore index control))
    (htreatedLindebergBase :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedLindebergBaseLoading index cell)
          l (nhds (treatedLindebergBaseLimit cell)))
    (hcontrolLindebergBase :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlLindebergBaseLoading index cell)
          l (nhds (controlLindebergBaseLimit cell)))
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
    (htreatedQVCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedQVScale index *
              treatedQVBaseCoefficientLoading index
                (treatedScore index treated))
    (hcontrolQVCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlQVScale index *
              controlQVBaseCoefficientLoading index
                (controlScore index control))
    (htreatedVariance :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedVariance index treated =
            treatedVarianceLoading index (treatedScore index treated))
    (hcontrolVariance :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlVariance index control =
            controlVarianceLoading index (controlScore index control))
    (htreatedQVBase :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedQVBaseCoefficientLoading index cell)
          l (nhds (treatedQVBaseCoefficientLimit cell)))
    (hcontrolQVBase :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlQVBaseCoefficientLoading index cell)
          l (nhds (controlQVBaseCoefficientLimit cell)))
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
    input.residual_clt ∧ input.residual_variance_formula := by
  have hlindeberg : input.conditional_lindeberg :=
    input_conditional_lindeberg_of_eventually_scaled_finiteCell_thirdMoment
      treatedCells controlCells treatedSample controlSample treatedWeight
      treatedCoefficient treatedResidual controlWeight controlCoefficient
      controlResidual treatedScore controlScore treatedLindebergScale
      controlLindebergScale treatedLindebergBaseLoading
      controlLindebergBaseLoading treatedLindebergBaseLimit
      controlLindebergBaseLimit treatedThirdMomentLoading treatedMassLimit
      controlThirdMomentLoading controlMassLimit input hinputLindeberg
      htreatedLindebergScale hcontrolLindebergScale htreatedWeightNonneg
      hcontrolWeightNonneg htreatedCover hcontrolCover
      htreatedLindebergCoefficient hcontrolLindebergCoefficient
      htreatedLindebergBase hcontrolLindebergBase htreatedThirdLoading
      hcontrolThirdLoading htreatedMass hcontrolMass
  have hqv : input.predictable_quadratic_variation_stabilization :=
    input_predictable_quadratic_variation_stabilization_of_eventually_scaled_finiteCell_qv
      treatedCells controlCells treatedSample controlSample treatedWeight
      treatedCoefficient controlWeight controlCoefficient treatedScore
      controlScore treatedVariance controlVariance treatedQVScale
      controlQVScale treatedQVBaseCoefficientLoading
      controlQVBaseCoefficientLoading treatedVarianceLoading
      controlVarianceLoading treatedQVScaleLimit controlQVScaleLimit
      treatedQVBaseCoefficientLimit controlQVBaseCoefficientLimit
      treatedVarianceLimit controlVarianceLimit treatedMassLimit
      controlMassLimit input hinputQV htreatedQVScale hcontrolQVScale
      htreatedCover hcontrolCover htreatedQVCoefficient
      hcontrolQVCoefficient htreatedVariance hcontrolVariance htreatedQVBase
      hcontrolQVBase htreatedVarianceLimit hcontrolVarianceLimit
      htreatedMass hcontrolMass
  exact
    residual_clt_and_variance_formula_of_martingale_array_input input
      hexact hregularity
      (hmartingaleMap htreatedMartingale hcontrolMartingale) hlindeberg hqv

/--
Input-level eventual finite-cell Lindeberg/QV endpoint from two adapted
Nat-indexed partial-sum arrays with conditionally mean-zero increments.

This is the finite-cell composite version of the generic two-arm
`condExp_sub_eq_zero` martingale route: it derives the concrete Mathlib
martingales from lower adaptedness, integrability, and conditional mean-zero
evidence before closing the residual martingale-array input.
-/
theorem
    residual_clt_and_variance_formula_of_eventually_scaled_finiteCell_lindeberg_qv_condExp_sub_eq_zero_nat_input
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
    (treatedLindebergScale controlLindebergScale : Index -> Real)
    (treatedLindebergBaseLoading : Index -> TreatedCell -> Real)
    (controlLindebergBaseLoading : Index -> ControlCell -> Real)
    (treatedLindebergBaseLimit : TreatedCell -> Real)
    (controlLindebergBaseLimit : ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedVariance : Index -> Treated -> Real)
    (controlVariance : Index -> Control -> Real)
    (treatedQVScale controlQVScale : Index -> Real)
    (treatedQVBaseCoefficientLoading : Index -> TreatedCell -> Real)
    (controlQVBaseCoefficientLoading : Index -> ControlCell -> Real)
    (treatedVarianceLoading : Index -> TreatedCell -> Real)
    (controlVarianceLoading : Index -> ControlCell -> Real)
    (treatedQVScaleLimit controlQVScaleLimit : Real)
    (treatedQVBaseCoefficientLimit : TreatedCell -> Real)
    (controlQVBaseCoefficientLimit : ControlCell -> Real)
    (treatedVarianceLimit : TreatedCell -> Real)
    (controlVarianceLimit : ControlCell -> Real)
    (input : ResidualMartingaleArrayCLTVarianceInput)
    {Ω E : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (treatedPartialSum controlPartialSum : ℕ -> Ω -> E)
    (htreatedAdapted : StronglyAdapted ℱ treatedPartialSum)
    (hcontrolAdapted : StronglyAdapted ℱ controlPartialSum)
    (htreatedIntegrable : ∀ i, Integrable (treatedPartialSum i) μ)
    (hcontrolIntegrable : ∀ i, Integrable (controlPartialSum i) μ)
    (htreatedCondZero :
      ∀ i, μ[treatedPartialSum (i + 1) - treatedPartialSum i | ℱ i] =ᵐ[μ] 0)
    (hcontrolCondZero :
      ∀ i, μ[controlPartialSum (i + 1) - controlPartialSum i | ℱ i] =ᵐ[μ] 0)
    (hmartingaleMap :
      Martingale treatedPartialSum ℱ μ ->
        Martingale controlPartialSum ℱ μ ->
          input.martingale_difference_array)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        input.conditional_lindeberg)
    (hinputQV :
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
                treatedQVScaleLimit ^ 2 *
                  (treatedQVBaseCoefficientLimit cell ^ 2 *
                    treatedVarianceLimit cell))
              treatedMassLimit +
            weightedScoreCellMomentLimit controlCells
              (fun cell =>
                controlQVScaleLimit ^ 2 *
                  (controlQVBaseCoefficientLimit cell ^ 2 *
                    controlVarianceLimit cell))
              controlMassLimit)) ->
        input.predictable_quadratic_variation_stabilization)
    (hexact : input.exact_weighted_reuse_moment_limits)
    (hregularity : input.residual_moment_regularity)
    (htreatedLindebergScale :
      Tendsto treatedLindebergScale l (nhds 0))
    (hcontrolLindebergScale :
      Tendsto controlLindebergScale l (nhds 0))
    (htreatedQVScale :
      Tendsto treatedQVScale l (nhds treatedQVScaleLimit))
    (hcontrolQVScale :
      Tendsto controlQVScale l (nhds controlQVScaleLimit))
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
    (htreatedLindebergCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedLindebergScale index *
              treatedLindebergBaseLoading index
                (treatedScore index treated))
    (hcontrolLindebergCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlLindebergScale index *
              controlLindebergBaseLoading index
                (controlScore index control))
    (htreatedLindebergBase :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedLindebergBaseLoading index cell)
          l (nhds (treatedLindebergBaseLimit cell)))
    (hcontrolLindebergBase :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlLindebergBaseLoading index cell)
          l (nhds (controlLindebergBaseLimit cell)))
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
    (htreatedQVCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedQVScale index *
              treatedQVBaseCoefficientLoading index
                (treatedScore index treated))
    (hcontrolQVCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlQVScale index *
              controlQVBaseCoefficientLoading index
                (controlScore index control))
    (htreatedVariance :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedVariance index treated =
            treatedVarianceLoading index (treatedScore index treated))
    (hcontrolVariance :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlVariance index control =
            controlVarianceLoading index (controlScore index control))
    (htreatedQVBase :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedQVBaseCoefficientLoading index cell)
          l (nhds (treatedQVBaseCoefficientLimit cell)))
    (hcontrolQVBase :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlQVBaseCoefficientLoading index cell)
          l (nhds (controlQVBaseCoefficientLimit cell)))
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
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_eventually_scaled_finiteCell_lindeberg_qv_mathlib_martingales_input
    treatedCells controlCells treatedSample controlSample treatedWeight
    treatedCoefficient treatedResidual controlWeight controlCoefficient
    controlResidual treatedScore controlScore treatedLindebergScale
    controlLindebergScale treatedLindebergBaseLoading
    controlLindebergBaseLoading treatedLindebergBaseLimit
    controlLindebergBaseLimit treatedThirdMomentLoading treatedMassLimit
    controlThirdMomentLoading controlMassLimit treatedVariance
    controlVariance treatedQVScale controlQVScale
    treatedQVBaseCoefficientLoading controlQVBaseCoefficientLoading
    treatedVarianceLoading controlVarianceLoading treatedQVScaleLimit
    controlQVScaleLimit treatedQVBaseCoefficientLimit
    controlQVBaseCoefficientLimit treatedVarianceLimit controlVarianceLimit
    input treatedPartialSum controlPartialSum
    (martingale_of_condExp_sub_eq_zero_nat htreatedAdapted
      htreatedIntegrable htreatedCondZero)
    (martingale_of_condExp_sub_eq_zero_nat hcontrolAdapted
      hcontrolIntegrable hcontrolCondZero)
    hmartingaleMap hinputLindeberg hinputQV hexact hregularity
    htreatedLindebergScale hcontrolLindebergScale htreatedQVScale
    hcontrolQVScale htreatedWeightNonneg hcontrolWeightNonneg htreatedCover
    hcontrolCover htreatedLindebergCoefficient
    hcontrolLindebergCoefficient htreatedLindebergBase
    hcontrolLindebergBase htreatedThirdLoading hcontrolThirdLoading
    htreatedQVCoefficient hcontrolQVCoefficient htreatedVariance
    hcontrolVariance htreatedQVBase hcontrolQVBase htreatedVarianceLimit
    hcontrolVarianceLimit htreatedMass hcontrolMass

/--
Input-level eventual finite-cell Lindeberg/QV endpoint from concrete
Nat-indexed increment arrays with conditionally mean-zero increments.

The theorem constructs the treated/control partial-sum martingales from
increment-level measurability and integrability, then applies the checked
partial-sum finite-cell route.
-/
theorem
    residual_clt_and_variance_formula_of_eventually_scaled_finiteCell_lindeberg_qv_increment_condExp_eq_zero_nat_input
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
    (treatedLindebergScale controlLindebergScale : Index -> Real)
    (treatedLindebergBaseLoading : Index -> TreatedCell -> Real)
    (controlLindebergBaseLoading : Index -> ControlCell -> Real)
    (treatedLindebergBaseLimit : TreatedCell -> Real)
    (controlLindebergBaseLimit : ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedVariance : Index -> Treated -> Real)
    (controlVariance : Index -> Control -> Real)
    (treatedQVScale controlQVScale : Index -> Real)
    (treatedQVBaseCoefficientLoading : Index -> TreatedCell -> Real)
    (controlQVBaseCoefficientLoading : Index -> ControlCell -> Real)
    (treatedVarianceLoading : Index -> TreatedCell -> Real)
    (controlVarianceLoading : Index -> ControlCell -> Real)
    (treatedQVScaleLimit controlQVScaleLimit : Real)
    (treatedQVBaseCoefficientLimit : TreatedCell -> Real)
    (controlQVBaseCoefficientLimit : ControlCell -> Real)
    (treatedVarianceLimit : TreatedCell -> Real)
    (controlVarianceLimit : ControlCell -> Real)
    (input : ResidualMartingaleArrayCLTVarianceInput)
    {Ω E : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (treatedIncrement controlIncrement : ℕ -> Ω -> E)
    (htreatedMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (treatedIncrement i))
    (hcontrolMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (controlIncrement i))
    (htreatedIntegrable : ∀ i, Integrable (treatedIncrement i) μ)
    (hcontrolIntegrable : ∀ i, Integrable (controlIncrement i) μ)
    (htreatedCondZero :
      ∀ i, μ[treatedIncrement i | ℱ i] =ᵐ[μ] 0)
    (hcontrolCondZero :
      ∀ i, μ[controlIncrement i | ℱ i] =ᵐ[μ] 0)
    (hmartingaleMap :
      Martingale (fun n ω => ∑ k ∈ Finset.range n, treatedIncrement k ω)
          ℱ μ ->
        Martingale (fun n ω => ∑ k ∈ Finset.range n, controlIncrement k ω)
          ℱ μ ->
          input.martingale_difference_array)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        input.conditional_lindeberg)
    (hinputQV :
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
                treatedQVScaleLimit ^ 2 *
                  (treatedQVBaseCoefficientLimit cell ^ 2 *
                    treatedVarianceLimit cell))
              treatedMassLimit +
            weightedScoreCellMomentLimit controlCells
              (fun cell =>
                controlQVScaleLimit ^ 2 *
                  (controlQVBaseCoefficientLimit cell ^ 2 *
                    controlVarianceLimit cell))
              controlMassLimit)) ->
        input.predictable_quadratic_variation_stabilization)
    (hexact : input.exact_weighted_reuse_moment_limits)
    (hregularity : input.residual_moment_regularity)
    (htreatedLindebergScale :
      Tendsto treatedLindebergScale l (nhds 0))
    (hcontrolLindebergScale :
      Tendsto controlLindebergScale l (nhds 0))
    (htreatedQVScale :
      Tendsto treatedQVScale l (nhds treatedQVScaleLimit))
    (hcontrolQVScale :
      Tendsto controlQVScale l (nhds controlQVScaleLimit))
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
    (htreatedLindebergCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedLindebergScale index *
              treatedLindebergBaseLoading index
                (treatedScore index treated))
    (hcontrolLindebergCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlLindebergScale index *
              controlLindebergBaseLoading index
                (controlScore index control))
    (htreatedLindebergBase :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedLindebergBaseLoading index cell)
          l (nhds (treatedLindebergBaseLimit cell)))
    (hcontrolLindebergBase :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlLindebergBaseLoading index cell)
          l (nhds (controlLindebergBaseLimit cell)))
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
    (htreatedQVCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedQVScale index *
              treatedQVBaseCoefficientLoading index
                (treatedScore index treated))
    (hcontrolQVCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlQVScale index *
              controlQVBaseCoefficientLoading index
                (controlScore index control))
    (htreatedVariance :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedVariance index treated =
            treatedVarianceLoading index (treatedScore index treated))
    (hcontrolVariance :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlVariance index control =
            controlVarianceLoading index (controlScore index control))
    (htreatedQVBase :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedQVBaseCoefficientLoading index cell)
          l (nhds (treatedQVBaseCoefficientLimit cell)))
    (hcontrolQVBase :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlQVBaseCoefficientLoading index cell)
          l (nhds (controlQVBaseCoefficientLimit cell)))
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
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_eventually_scaled_finiteCell_lindeberg_qv_condExp_sub_eq_zero_nat_input
    treatedCells controlCells treatedSample controlSample treatedWeight
    treatedCoefficient treatedResidual controlWeight controlCoefficient
    controlResidual treatedScore controlScore treatedLindebergScale
    controlLindebergScale treatedLindebergBaseLoading
    controlLindebergBaseLoading treatedLindebergBaseLimit
    controlLindebergBaseLimit treatedThirdMomentLoading treatedMassLimit
    controlThirdMomentLoading controlMassLimit treatedVariance
    controlVariance treatedQVScale controlQVScale
    treatedQVBaseCoefficientLoading controlQVBaseCoefficientLoading
    treatedVarianceLoading controlVarianceLoading treatedQVScaleLimit
    controlQVScaleLimit treatedQVBaseCoefficientLimit
    controlQVBaseCoefficientLimit treatedVarianceLimit controlVarianceLimit
    input
    (fun n ω => ∑ k ∈ Finset.range n, treatedIncrement k ω)
    (fun n ω => ∑ k ∈ Finset.range n, controlIncrement k ω)
    (fun n =>
      Finset.stronglyMeasurable_fun_sum (Finset.range n) fun k hk =>
        (htreatedMeas k).mono (ℱ.mono (Finset.mem_range.mp hk)))
    (fun n =>
      Finset.stronglyMeasurable_fun_sum (Finset.range n) fun k hk =>
        (hcontrolMeas k).mono (ℱ.mono (Finset.mem_range.mp hk)))
    (fun n => integrable_finsetSum (Finset.range n) fun k _ =>
      htreatedIntegrable k)
    (fun n => integrable_finsetSum (Finset.range n) fun k _ =>
      hcontrolIntegrable k)
    (fun i =>
      (condExp_congr_ae
        (ae_of_all _ fun ω => by
          simp [Finset.sum_range_succ])).trans
        (htreatedCondZero i))
    (fun i =>
      (condExp_congr_ae
        (ae_of_all _ fun ω => by
          simp [Finset.sum_range_succ])).trans
        (hcontrolCondZero i))
    hmartingaleMap hinputLindeberg hinputQV hexact hregularity
    htreatedLindebergScale hcontrolLindebergScale htreatedQVScale
    hcontrolQVScale htreatedWeightNonneg hcontrolWeightNonneg htreatedCover
    hcontrolCover htreatedLindebergCoefficient
    hcontrolLindebergCoefficient htreatedLindebergBase
    hcontrolLindebergBase htreatedThirdLoading hcontrolThirdLoading
    htreatedQVCoefficient hcontrolQVCoefficient htreatedVariance
    hcontrolVariance htreatedQVBase hcontrolQVBase htreatedVarianceLimit
    hcontrolVarianceLimit htreatedMass hcontrolMass

/--
Close the predictable quadratic-variation field of an explicit triangular
martingale-array CLT bridge from eventually valid finite-cell QV loadings and
score-cell mass convergence.

This is the field-level version of
`input_predictable_quadratic_variation_stabilization_of_eventually_scaled_finiteCell_qv`:
it targets `TriangularMartingaleArrayCLTVarianceBridge` directly, before the
bridge is packaged as a WDSM residual input.
-/
theorem triangular_predictable_quadratic_variation_stabilization_of_eventually_scaled_finiteCell_qv
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSample : Index -> Finset Treated)
    (controlSample : Index -> Finset Control)
    (treatedWeight treatedCoefficient : Index -> Treated -> Real)
    (controlWeight controlCoefficient : Index -> Control -> Real)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedVariance : Index -> Treated -> Real)
    (controlVariance : Index -> Control -> Real)
    (treatedQVScale controlQVScale : Index -> Real)
    (treatedQVBaseCoefficientLoading : Index -> TreatedCell -> Real)
    (controlQVBaseCoefficientLoading : Index -> ControlCell -> Real)
    (treatedVarianceLoading : Index -> TreatedCell -> Real)
    (controlVarianceLoading : Index -> ControlCell -> Real)
    (treatedQVScaleLimit controlQVScaleLimit : Real)
    (treatedQVBaseCoefficientLimit : TreatedCell -> Real)
    (controlQVBaseCoefficientLimit : ControlCell -> Real)
    (treatedVarianceLimit : TreatedCell -> Real)
    (controlVarianceLimit : ControlCell -> Real)
    (treatedMassLimit : TreatedCell -> Real)
    (controlMassLimit : ControlCell -> Real)
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (hbridgeQV :
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
                treatedQVScaleLimit ^ 2 *
                  (treatedQVBaseCoefficientLimit cell ^ 2 *
                    treatedVarianceLimit cell))
              treatedMassLimit +
            weightedScoreCellMomentLimit controlCells
              (fun cell =>
                controlQVScaleLimit ^ 2 *
                  (controlQVBaseCoefficientLimit cell ^ 2 *
                    controlVarianceLimit cell))
              controlMassLimit)) ->
        martingaleCLT.predictable_quadratic_variation_stabilization)
    (htreatedQVScale :
      Tendsto treatedQVScale l (nhds treatedQVScaleLimit))
    (hcontrolQVScale :
      Tendsto controlQVScale l (nhds controlQVScaleLimit))
    (htreatedCover :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedScore index treated ∈ treatedCells)
    (hcontrolCover :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlScore index control ∈ controlCells)
    (htreatedQVCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedQVScale index *
              treatedQVBaseCoefficientLoading index
                (treatedScore index treated))
    (hcontrolQVCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlQVScale index *
              controlQVBaseCoefficientLoading index
                (controlScore index control))
    (htreatedVariance :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedVariance index treated =
            treatedVarianceLoading index (treatedScore index treated))
    (hcontrolVariance :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlVariance index control =
            controlVarianceLoading index (controlScore index control))
    (htreatedQVBase :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedQVBaseCoefficientLoading index cell)
          l (nhds (treatedQVBaseCoefficientLimit cell)))
    (hcontrolQVBase :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlQVBaseCoefficientLoading index cell)
          l (nhds (controlQVBaseCoefficientLimit cell)))
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
    martingaleCLT.predictable_quadratic_variation_stabilization :=
  hbridgeQV
    (tendsto_twoArm_weightedQuadraticVariation_of_eventually_scaled_coefficients_scoreCellVariance_hetero
      treatedCells controlCells treatedSample controlSample treatedWeight
      controlWeight treatedScore controlScore treatedCoefficient
      treatedVariance controlCoefficient controlVariance treatedQVScale
      controlQVScale treatedQVBaseCoefficientLoading
      controlQVBaseCoefficientLoading treatedVarianceLoading
      controlVarianceLoading treatedQVScaleLimit controlQVScaleLimit
      treatedQVBaseCoefficientLimit controlQVBaseCoefficientLimit
      treatedVarianceLimit treatedMassLimit controlVarianceLimit
      controlMassLimit htreatedCover hcontrolCover htreatedQVCoefficient
      hcontrolQVCoefficient htreatedVariance hcontrolVariance
      htreatedQVScale hcontrolQVScale htreatedQVBase hcontrolQVBase
      htreatedVarianceLimit hcontrolVarianceLimit htreatedMass hcontrolMass)

/--
Triangular eventual finite-cell Lindeberg/QV endpoint with the
martingale-difference field supplied by concrete treated/control Mathlib
martingales.

This is the direct triangular counterpart of
`residual_clt_and_variance_formula_of_eventually_scaled_finiteCell_lindeberg_qv_mathlib_martingales_input`.
It closes the triangular martingale-difference, conditional-Lindeberg, and
predictable-QV fields from lower WDSM evidence before invoking the explicit
triangular CLT bridge.
-/
theorem
    residual_clt_and_variance_formula_of_eventually_scaled_finiteCell_lindeberg_qv_mathlib_martingales_triangular
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
    (treatedLindebergScale controlLindebergScale : Index -> Real)
    (treatedLindebergBaseLoading : Index -> TreatedCell -> Real)
    (controlLindebergBaseLoading : Index -> ControlCell -> Real)
    (treatedLindebergBaseLimit : TreatedCell -> Real)
    (controlLindebergBaseLimit : ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedVariance : Index -> Treated -> Real)
    (controlVariance : Index -> Control -> Real)
    (treatedQVScale controlQVScale : Index -> Real)
    (treatedQVBaseCoefficientLoading : Index -> TreatedCell -> Real)
    (controlQVBaseCoefficientLoading : Index -> ControlCell -> Real)
    (treatedVarianceLoading : Index -> TreatedCell -> Real)
    (controlVarianceLoading : Index -> ControlCell -> Real)
    (treatedQVScaleLimit controlQVScaleLimit : Real)
    (treatedQVBaseCoefficientLimit : TreatedCell -> Real)
    (controlQVBaseCoefficientLimit : ControlCell -> Real)
    (treatedVarianceLimit : TreatedCell -> Real)
    (controlVarianceLimit : ControlCell -> Real)
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    {Ω E ι : Type*} [Preorder ι] {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} {ℱ : Filtration ι m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (treatedProcess controlProcess : ι -> Ω -> E)
    (htreatedMartingale : Martingale treatedProcess ℱ μ)
    (hcontrolMartingale : Martingale controlProcess ℱ μ)
    (hmartingaleMap :
      Martingale treatedProcess ℱ μ ->
        Martingale controlProcess ℱ μ ->
          martingaleCLT.martingale_difference_array)
    (hbridgeLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        martingaleCLT.conditional_lindeberg)
    (hbridgeQV :
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
                treatedQVScaleLimit ^ 2 *
                  (treatedQVBaseCoefficientLimit cell ^ 2 *
                    treatedVarianceLimit cell))
              treatedMassLimit +
            weightedScoreCellMomentLimit controlCells
              (fun cell =>
                controlQVScaleLimit ^ 2 *
                  (controlQVBaseCoefficientLimit cell ^ 2 *
                    controlVarianceLimit cell))
              controlMassLimit)) ->
        martingaleCLT.predictable_quadratic_variation_stabilization)
    (htreatedLindebergScale :
      Tendsto treatedLindebergScale l (nhds 0))
    (hcontrolLindebergScale :
      Tendsto controlLindebergScale l (nhds 0))
    (htreatedQVScale :
      Tendsto treatedQVScale l (nhds treatedQVScaleLimit))
    (hcontrolQVScale :
      Tendsto controlQVScale l (nhds controlQVScaleLimit))
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
    (htreatedLindebergCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedLindebergScale index *
              treatedLindebergBaseLoading index
                (treatedScore index treated))
    (hcontrolLindebergCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlLindebergScale index *
              controlLindebergBaseLoading index
                (controlScore index control))
    (htreatedLindebergBase :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedLindebergBaseLoading index cell)
          l (nhds (treatedLindebergBaseLimit cell)))
    (hcontrolLindebergBase :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlLindebergBaseLoading index cell)
          l (nhds (controlLindebergBaseLimit cell)))
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
    (htreatedQVCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedQVScale index *
              treatedQVBaseCoefficientLoading index
                (treatedScore index treated))
    (hcontrolQVCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlQVScale index *
              controlQVBaseCoefficientLoading index
                (controlScore index control))
    (htreatedVariance :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedVariance index treated =
            treatedVarianceLoading index (treatedScore index treated))
    (hcontrolVariance :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlVariance index control =
            controlVarianceLoading index (controlScore index control))
    (htreatedQVBase :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedQVBaseCoefficientLoading index cell)
          l (nhds (treatedQVBaseCoefficientLimit cell)))
    (hcontrolQVBase :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlQVBaseCoefficientLoading index cell)
          l (nhds (controlQVBaseCoefficientLimit cell)))
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
    martingaleCLT.residual_clt ∧
      martingaleCLT.residual_variance_formula := by
  have hlindeberg : martingaleCLT.conditional_lindeberg :=
    triangular_conditional_lindeberg_of_eventually_scaled_finiteCell_thirdMoment
      treatedCells controlCells treatedSample controlSample treatedWeight
      treatedCoefficient treatedResidual controlWeight controlCoefficient
      controlResidual treatedScore controlScore treatedLindebergScale
      controlLindebergScale treatedLindebergBaseLoading
      controlLindebergBaseLoading treatedLindebergBaseLimit
      controlLindebergBaseLimit treatedThirdMomentLoading treatedMassLimit
      controlThirdMomentLoading controlMassLimit martingaleCLT
      hbridgeLindeberg htreatedLindebergScale hcontrolLindebergScale
      htreatedWeightNonneg hcontrolWeightNonneg htreatedCover hcontrolCover
      htreatedLindebergCoefficient hcontrolLindebergCoefficient
      htreatedLindebergBase hcontrolLindebergBase htreatedThirdLoading
      hcontrolThirdLoading htreatedMass hcontrolMass
  have hqv : martingaleCLT.predictable_quadratic_variation_stabilization :=
    triangular_predictable_quadratic_variation_stabilization_of_eventually_scaled_finiteCell_qv
      treatedCells controlCells treatedSample controlSample treatedWeight
      treatedCoefficient controlWeight controlCoefficient treatedScore
      controlScore treatedVariance controlVariance treatedQVScale
      controlQVScale treatedQVBaseCoefficientLoading
      controlQVBaseCoefficientLoading treatedVarianceLoading
      controlVarianceLoading treatedQVScaleLimit controlQVScaleLimit
      treatedQVBaseCoefficientLimit controlQVBaseCoefficientLimit
      treatedVarianceLimit controlVarianceLimit treatedMassLimit
      controlMassLimit martingaleCLT hbridgeQV htreatedQVScale
      hcontrolQVScale htreatedCover hcontrolCover htreatedQVCoefficient
      hcontrolQVCoefficient htreatedVariance hcontrolVariance
      htreatedQVBase hcontrolQVBase htreatedVarianceLimit
      hcontrolVarianceLimit htreatedMass hcontrolMass
  exact
    residual_clt_and_variance_formula_of_triangular_martingale_array_clt_bridge
      martingaleCLT
      (hmartingaleMap htreatedMartingale hcontrolMartingale) hlindeberg hqv

/--
Triangular eventual finite-cell Lindeberg/QV endpoint from two adapted
Nat-indexed partial-sum arrays with conditionally mean-zero increments.

This closes the triangular martingale-difference field through Mathlib's
partial-sum martingale construction, while the finite-cell reducers close the
triangular Lindeberg and QV fields.
-/
theorem
    residual_clt_and_variance_formula_of_eventually_scaled_finiteCell_lindeberg_qv_condExp_sub_eq_zero_nat_triangular
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
    (treatedLindebergScale controlLindebergScale : Index -> Real)
    (treatedLindebergBaseLoading : Index -> TreatedCell -> Real)
    (controlLindebergBaseLoading : Index -> ControlCell -> Real)
    (treatedLindebergBaseLimit : TreatedCell -> Real)
    (controlLindebergBaseLimit : ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedVariance : Index -> Treated -> Real)
    (controlVariance : Index -> Control -> Real)
    (treatedQVScale controlQVScale : Index -> Real)
    (treatedQVBaseCoefficientLoading : Index -> TreatedCell -> Real)
    (controlQVBaseCoefficientLoading : Index -> ControlCell -> Real)
    (treatedVarianceLoading : Index -> TreatedCell -> Real)
    (controlVarianceLoading : Index -> ControlCell -> Real)
    (treatedQVScaleLimit controlQVScaleLimit : Real)
    (treatedQVBaseCoefficientLimit : TreatedCell -> Real)
    (controlQVBaseCoefficientLimit : ControlCell -> Real)
    (treatedVarianceLimit : TreatedCell -> Real)
    (controlVarianceLimit : ControlCell -> Real)
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    {Ω E : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (treatedPartialSum controlPartialSum : ℕ -> Ω -> E)
    (htreatedAdapted : StronglyAdapted ℱ treatedPartialSum)
    (hcontrolAdapted : StronglyAdapted ℱ controlPartialSum)
    (htreatedIntegrable : ∀ i, Integrable (treatedPartialSum i) μ)
    (hcontrolIntegrable : ∀ i, Integrable (controlPartialSum i) μ)
    (htreatedCondZero :
      ∀ i, μ[treatedPartialSum (i + 1) - treatedPartialSum i | ℱ i] =ᵐ[μ] 0)
    (hcontrolCondZero :
      ∀ i, μ[controlPartialSum (i + 1) - controlPartialSum i | ℱ i] =ᵐ[μ] 0)
    (hmartingaleMap :
      Martingale treatedPartialSum ℱ μ ->
        Martingale controlPartialSum ℱ μ ->
          martingaleCLT.martingale_difference_array)
    (hbridgeLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        martingaleCLT.conditional_lindeberg)
    (hbridgeQV :
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
                treatedQVScaleLimit ^ 2 *
                  (treatedQVBaseCoefficientLimit cell ^ 2 *
                    treatedVarianceLimit cell))
              treatedMassLimit +
            weightedScoreCellMomentLimit controlCells
              (fun cell =>
                controlQVScaleLimit ^ 2 *
                  (controlQVBaseCoefficientLimit cell ^ 2 *
                    controlVarianceLimit cell))
              controlMassLimit)) ->
        martingaleCLT.predictable_quadratic_variation_stabilization)
    (htreatedLindebergScale :
      Tendsto treatedLindebergScale l (nhds 0))
    (hcontrolLindebergScale :
      Tendsto controlLindebergScale l (nhds 0))
    (htreatedQVScale :
      Tendsto treatedQVScale l (nhds treatedQVScaleLimit))
    (hcontrolQVScale :
      Tendsto controlQVScale l (nhds controlQVScaleLimit))
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
    (htreatedLindebergCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedLindebergScale index *
              treatedLindebergBaseLoading index
                (treatedScore index treated))
    (hcontrolLindebergCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlLindebergScale index *
              controlLindebergBaseLoading index
                (controlScore index control))
    (htreatedLindebergBase :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedLindebergBaseLoading index cell)
          l (nhds (treatedLindebergBaseLimit cell)))
    (hcontrolLindebergBase :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlLindebergBaseLoading index cell)
          l (nhds (controlLindebergBaseLimit cell)))
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
    (htreatedQVCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedQVScale index *
              treatedQVBaseCoefficientLoading index
                (treatedScore index treated))
    (hcontrolQVCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlQVScale index *
              controlQVBaseCoefficientLoading index
                (controlScore index control))
    (htreatedVariance :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedVariance index treated =
            treatedVarianceLoading index (treatedScore index treated))
    (hcontrolVariance :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlVariance index control =
            controlVarianceLoading index (controlScore index control))
    (htreatedQVBase :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedQVBaseCoefficientLoading index cell)
          l (nhds (treatedQVBaseCoefficientLimit cell)))
    (hcontrolQVBase :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlQVBaseCoefficientLoading index cell)
          l (nhds (controlQVBaseCoefficientLimit cell)))
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
    martingaleCLT.residual_clt ∧
      martingaleCLT.residual_variance_formula :=
  residual_clt_and_variance_formula_of_eventually_scaled_finiteCell_lindeberg_qv_mathlib_martingales_triangular
    treatedCells controlCells treatedSample controlSample treatedWeight
    treatedCoefficient treatedResidual controlWeight controlCoefficient
    controlResidual treatedScore controlScore treatedLindebergScale
    controlLindebergScale treatedLindebergBaseLoading
    controlLindebergBaseLoading treatedLindebergBaseLimit
    controlLindebergBaseLimit treatedThirdMomentLoading treatedMassLimit
    controlThirdMomentLoading controlMassLimit treatedVariance
    controlVariance treatedQVScale controlQVScale
    treatedQVBaseCoefficientLoading controlQVBaseCoefficientLoading
    treatedVarianceLoading controlVarianceLoading treatedQVScaleLimit
    controlQVScaleLimit treatedQVBaseCoefficientLimit
    controlQVBaseCoefficientLimit treatedVarianceLimit controlVarianceLimit
    martingaleCLT treatedPartialSum controlPartialSum
    (martingale_of_condExp_sub_eq_zero_nat htreatedAdapted
      htreatedIntegrable htreatedCondZero)
    (martingale_of_condExp_sub_eq_zero_nat hcontrolAdapted
      hcontrolIntegrable hcontrolCondZero)
    hmartingaleMap hbridgeLindeberg hbridgeQV htreatedLindebergScale
    hcontrolLindebergScale htreatedQVScale hcontrolQVScale
    htreatedWeightNonneg hcontrolWeightNonneg htreatedCover hcontrolCover
    htreatedLindebergCoefficient hcontrolLindebergCoefficient
    htreatedLindebergBase hcontrolLindebergBase htreatedThirdLoading
    hcontrolThirdLoading htreatedQVCoefficient hcontrolQVCoefficient
    htreatedVariance hcontrolVariance htreatedQVBase hcontrolQVBase
    htreatedVarianceLimit hcontrolVarianceLimit htreatedMass hcontrolMass

/--
Triangular eventual finite-cell Lindeberg/QV endpoint from concrete Nat-indexed
increment arrays with conditionally mean-zero increments.

It constructs the two partial-sum martingales from increment-level evidence,
then applies the checked partial-sum triangular finite-cell route.
-/
theorem
    residual_clt_and_variance_formula_of_eventually_scaled_finiteCell_lindeberg_qv_increment_condExp_eq_zero_nat_triangular
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
    (treatedLindebergScale controlLindebergScale : Index -> Real)
    (treatedLindebergBaseLoading : Index -> TreatedCell -> Real)
    (controlLindebergBaseLoading : Index -> ControlCell -> Real)
    (treatedLindebergBaseLimit : TreatedCell -> Real)
    (controlLindebergBaseLimit : ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedVariance : Index -> Treated -> Real)
    (controlVariance : Index -> Control -> Real)
    (treatedQVScale controlQVScale : Index -> Real)
    (treatedQVBaseCoefficientLoading : Index -> TreatedCell -> Real)
    (controlQVBaseCoefficientLoading : Index -> ControlCell -> Real)
    (treatedVarianceLoading : Index -> TreatedCell -> Real)
    (controlVarianceLoading : Index -> ControlCell -> Real)
    (treatedQVScaleLimit controlQVScaleLimit : Real)
    (treatedQVBaseCoefficientLimit : TreatedCell -> Real)
    (controlQVBaseCoefficientLimit : ControlCell -> Real)
    (treatedVarianceLimit : TreatedCell -> Real)
    (controlVarianceLimit : ControlCell -> Real)
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    {Ω E : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (treatedIncrement controlIncrement : ℕ -> Ω -> E)
    (htreatedMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (treatedIncrement i))
    (hcontrolMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (controlIncrement i))
    (htreatedIntegrable : ∀ i, Integrable (treatedIncrement i) μ)
    (hcontrolIntegrable : ∀ i, Integrable (controlIncrement i) μ)
    (htreatedCondZero :
      ∀ i, μ[treatedIncrement i | ℱ i] =ᵐ[μ] 0)
    (hcontrolCondZero :
      ∀ i, μ[controlIncrement i | ℱ i] =ᵐ[μ] 0)
    (hmartingaleMap :
      Martingale (fun n ω => ∑ k ∈ Finset.range n, treatedIncrement k ω)
          ℱ μ ->
        Martingale (fun n ω => ∑ k ∈ Finset.range n, controlIncrement k ω)
          ℱ μ ->
          martingaleCLT.martingale_difference_array)
    (hbridgeLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        martingaleCLT.conditional_lindeberg)
    (hbridgeQV :
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
                treatedQVScaleLimit ^ 2 *
                  (treatedQVBaseCoefficientLimit cell ^ 2 *
                    treatedVarianceLimit cell))
              treatedMassLimit +
            weightedScoreCellMomentLimit controlCells
              (fun cell =>
                controlQVScaleLimit ^ 2 *
                  (controlQVBaseCoefficientLimit cell ^ 2 *
                    controlVarianceLimit cell))
              controlMassLimit)) ->
        martingaleCLT.predictable_quadratic_variation_stabilization)
    (htreatedLindebergScale :
      Tendsto treatedLindebergScale l (nhds 0))
    (hcontrolLindebergScale :
      Tendsto controlLindebergScale l (nhds 0))
    (htreatedQVScale :
      Tendsto treatedQVScale l (nhds treatedQVScaleLimit))
    (hcontrolQVScale :
      Tendsto controlQVScale l (nhds controlQVScaleLimit))
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
    (htreatedLindebergCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedLindebergScale index *
              treatedLindebergBaseLoading index
                (treatedScore index treated))
    (hcontrolLindebergCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlLindebergScale index *
              controlLindebergBaseLoading index
                (controlScore index control))
    (htreatedLindebergBase :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedLindebergBaseLoading index cell)
          l (nhds (treatedLindebergBaseLimit cell)))
    (hcontrolLindebergBase :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlLindebergBaseLoading index cell)
          l (nhds (controlLindebergBaseLimit cell)))
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
    (htreatedQVCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedQVScale index *
              treatedQVBaseCoefficientLoading index
                (treatedScore index treated))
    (hcontrolQVCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlQVScale index *
              controlQVBaseCoefficientLoading index
                (controlScore index control))
    (htreatedVariance :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedVariance index treated =
            treatedVarianceLoading index (treatedScore index treated))
    (hcontrolVariance :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlVariance index control =
            controlVarianceLoading index (controlScore index control))
    (htreatedQVBase :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedQVBaseCoefficientLoading index cell)
          l (nhds (treatedQVBaseCoefficientLimit cell)))
    (hcontrolQVBase :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlQVBaseCoefficientLoading index cell)
          l (nhds (controlQVBaseCoefficientLimit cell)))
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
    martingaleCLT.residual_clt ∧
      martingaleCLT.residual_variance_formula :=
  residual_clt_and_variance_formula_of_eventually_scaled_finiteCell_lindeberg_qv_condExp_sub_eq_zero_nat_triangular
    treatedCells controlCells treatedSample controlSample treatedWeight
    treatedCoefficient treatedResidual controlWeight controlCoefficient
    controlResidual treatedScore controlScore treatedLindebergScale
    controlLindebergScale treatedLindebergBaseLoading
    controlLindebergBaseLoading treatedLindebergBaseLimit
    controlLindebergBaseLimit treatedThirdMomentLoading treatedMassLimit
    controlThirdMomentLoading controlMassLimit treatedVariance
    controlVariance treatedQVScale controlQVScale
    treatedQVBaseCoefficientLoading controlQVBaseCoefficientLoading
    treatedVarianceLoading controlVarianceLoading treatedQVScaleLimit
    controlQVScaleLimit treatedQVBaseCoefficientLimit
    controlQVBaseCoefficientLimit treatedVarianceLimit controlVarianceLimit
    martingaleCLT
    (fun n ω => ∑ k ∈ Finset.range n, treatedIncrement k ω)
    (fun n ω => ∑ k ∈ Finset.range n, controlIncrement k ω)
    (fun n =>
      Finset.stronglyMeasurable_fun_sum (Finset.range n) fun k hk =>
        (htreatedMeas k).mono (ℱ.mono (Finset.mem_range.mp hk)))
    (fun n =>
      Finset.stronglyMeasurable_fun_sum (Finset.range n) fun k hk =>
        (hcontrolMeas k).mono (ℱ.mono (Finset.mem_range.mp hk)))
    (fun n => integrable_finsetSum (Finset.range n) fun k _ =>
      htreatedIntegrable k)
    (fun n => integrable_finsetSum (Finset.range n) fun k _ =>
      hcontrolIntegrable k)
    (fun i =>
      (condExp_congr_ae
        (ae_of_all _ fun ω => by
          simp [Finset.sum_range_succ])).trans
        (htreatedCondZero i))
    (fun i =>
      (condExp_congr_ae
        (ae_of_all _ fun ω => by
          simp [Finset.sum_range_succ])).trans
        (hcontrolCondZero i))
    hmartingaleMap hbridgeLindeberg hbridgeQV htreatedLindebergScale
    hcontrolLindebergScale htreatedQVScale hcontrolQVScale
    htreatedWeightNonneg hcontrolWeightNonneg htreatedCover hcontrolCover
    htreatedLindebergCoefficient hcontrolLindebergCoefficient
    htreatedLindebergBase hcontrolLindebergBase htreatedThirdLoading
    hcontrolThirdLoading htreatedQVCoefficient hcontrolQVCoefficient
    htreatedVariance hcontrolVariance htreatedQVBase hcontrolQVBase
    htreatedVarianceLimit hcontrolVarianceLimit htreatedMass hcontrolMass

/--
Triangular residual CLT and variance formula from the three concrete
field-level reducers now available in this lane.

The martingale-difference field is closed from two-arm predictable weighted
residual increments; the conditional-Lindeberg and predictable-QV fields are
closed from eventual finite-cell loading, third-moment, variance, and
mass-convergence evidence.  The only remaining probability input is the
`TriangularMartingaleArrayCLTVarianceBridge.bridge` theorem itself.
-/
theorem residual_clt_and_variance_formula_of_triangular_predictable_finiteCell_lindeberg_qv_bridge
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
    (treatedLindebergScale controlLindebergScale : Index -> Real)
    (treatedLindebergBaseLoading : Index -> TreatedCell -> Real)
    (controlLindebergBaseLoading : Index -> ControlCell -> Real)
    (treatedLindebergBaseLimit : TreatedCell -> Real)
    (controlLindebergBaseLimit : ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedVariance : Index -> Treated -> Real)
    (controlVariance : Index -> Control -> Real)
    (treatedQVScale controlQVScale : Index -> Real)
    (treatedQVBaseCoefficientLoading : Index -> TreatedCell -> Real)
    (controlQVBaseCoefficientLoading : Index -> ControlCell -> Real)
    (treatedVarianceLoading : Index -> TreatedCell -> Real)
    (controlVarianceLoading : Index -> ControlCell -> Real)
    (treatedQVScaleLimit controlQVScaleLimit : Real)
    (treatedQVBaseCoefficientLimit : TreatedCell -> Real)
    (controlQVBaseCoefficientLimit : ControlCell -> Real)
    (treatedVarianceLimit : TreatedCell -> Real)
    (controlVarianceLimit : ControlCell -> Real)
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    (treatedMartingaleCoefficient treatedMartingaleResidual :
      ℕ -> Ω -> Real)
    (controlMartingaleCoefficient controlMartingaleResidual :
      ℕ -> Ω -> Real)
    (htreatedCoefficientMeas :
      ∀ i, StronglyMeasurable[ℱ i] (treatedMartingaleCoefficient i))
    (hcontrolCoefficientMeas :
      ∀ i, StronglyMeasurable[ℱ i] (controlMartingaleCoefficient i))
    (htreatedResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (treatedMartingaleResidual i))
    (hcontrolResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (controlMartingaleResidual i))
    (htreatedProductIntegrable :
      ∀ i, Integrable
        (fun ω =>
          treatedMartingaleCoefficient i ω *
            treatedMartingaleResidual i ω) μ)
    (hcontrolProductIntegrable :
      ∀ i, Integrable
        (fun ω =>
          controlMartingaleCoefficient i ω *
            controlMartingaleResidual i ω) μ)
    (htreatedResidualIntegrable :
      ∀ i, Integrable (treatedMartingaleResidual i) μ)
    (hcontrolResidualIntegrable :
      ∀ i, Integrable (controlMartingaleResidual i) μ)
    (htreatedResidualCondZero :
      ∀ i, μ[treatedMartingaleResidual i | ℱ i] =ᵐ[μ] 0)
    (hcontrolResidualCondZero :
      ∀ i, μ[controlMartingaleResidual i | ℱ i] =ᵐ[μ] 0)
    (hmartingaleMap :
      Martingale
          (fun n ω =>
            ∑ k ∈ Finset.range n,
              treatedMartingaleCoefficient k ω *
                treatedMartingaleResidual k ω)
          ℱ μ ->
        Martingale
            (fun n ω =>
              ∑ k ∈ Finset.range n,
                controlMartingaleCoefficient k ω *
                  controlMartingaleResidual k ω)
            ℱ μ ->
          martingaleCLT.martingale_difference_array)
    (hbridgeLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        martingaleCLT.conditional_lindeberg)
    (hbridgeQV :
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
                treatedQVScaleLimit ^ 2 *
                  (treatedQVBaseCoefficientLimit cell ^ 2 *
                    treatedVarianceLimit cell))
              treatedMassLimit +
            weightedScoreCellMomentLimit controlCells
              (fun cell =>
                controlQVScaleLimit ^ 2 *
                  (controlQVBaseCoefficientLimit cell ^ 2 *
                    controlVarianceLimit cell))
              controlMassLimit)) ->
        martingaleCLT.predictable_quadratic_variation_stabilization)
    (htreatedLindebergScale :
      Tendsto treatedLindebergScale l (nhds 0))
    (hcontrolLindebergScale :
      Tendsto controlLindebergScale l (nhds 0))
    (htreatedQVScale :
      Tendsto treatedQVScale l (nhds treatedQVScaleLimit))
    (hcontrolQVScale :
      Tendsto controlQVScale l (nhds controlQVScaleLimit))
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
    (htreatedLindebergCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedLindebergScale index *
              treatedLindebergBaseLoading index
                (treatedScore index treated))
    (hcontrolLindebergCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlLindebergScale index *
              controlLindebergBaseLoading index
                (controlScore index control))
    (htreatedLindebergBase :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedLindebergBaseLoading index cell)
          l (nhds (treatedLindebergBaseLimit cell)))
    (hcontrolLindebergBase :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlLindebergBaseLoading index cell)
          l (nhds (controlLindebergBaseLimit cell)))
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
    (htreatedQVCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedQVScale index *
              treatedQVBaseCoefficientLoading index
                (treatedScore index treated))
    (hcontrolQVCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlQVScale index *
              controlQVBaseCoefficientLoading index
                (controlScore index control))
    (htreatedVariance :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedVariance index treated =
            treatedVarianceLoading index (treatedScore index treated))
    (hcontrolVariance :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlVariance index control =
            controlVarianceLoading index (controlScore index control))
    (htreatedQVBase :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedQVBaseCoefficientLoading index cell)
          l (nhds (treatedQVBaseCoefficientLimit cell)))
    (hcontrolQVBase :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlQVBaseCoefficientLoading index cell)
          l (nhds (controlQVBaseCoefficientLimit cell)))
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
    martingaleCLT.residual_clt ∧ martingaleCLT.residual_variance_formula := by
  have hmartingale :
      martingaleCLT.martingale_difference_array :=
    hmartingaleMap
      (martingale_of_condExp_sub_eq_zero_nat
        (fun n =>
          Finset.stronglyMeasurable_fun_sum (Finset.range n) fun k hk =>
            ((htreatedCoefficientMeas k).mono
                (ℱ.mono (Nat.le_of_lt (Finset.mem_range.mp hk)))).mul
              ((htreatedResidualNextMeas k).mono
                (ℱ.mono (Nat.succ_le_of_lt (Finset.mem_range.mp hk)))))
        (fun n =>
          integrable_finsetSum (Finset.range n) fun k _ =>
            htreatedProductIntegrable k)
        (fun i =>
          (condExp_congr_ae
            (ae_of_all _ fun ω => by
              simp [Finset.sum_range_succ])).trans
            ((condExp_predictable_mul_residual_ae_eq_zero_nat
                treatedMartingaleCoefficient treatedMartingaleResidual
                htreatedCoefficientMeas htreatedProductIntegrable
                htreatedResidualIntegrable htreatedResidualCondZero) i)))
      (martingale_of_condExp_sub_eq_zero_nat
        (fun n =>
          Finset.stronglyMeasurable_fun_sum (Finset.range n) fun k hk =>
            ((hcontrolCoefficientMeas k).mono
                (ℱ.mono (Nat.le_of_lt (Finset.mem_range.mp hk)))).mul
              ((hcontrolResidualNextMeas k).mono
                (ℱ.mono (Nat.succ_le_of_lt (Finset.mem_range.mp hk)))))
        (fun n =>
          integrable_finsetSum (Finset.range n) fun k _ =>
            hcontrolProductIntegrable k)
        (fun i =>
          (condExp_congr_ae
            (ae_of_all _ fun ω => by
              simp [Finset.sum_range_succ])).trans
            ((condExp_predictable_mul_residual_ae_eq_zero_nat
                controlMartingaleCoefficient controlMartingaleResidual
                hcontrolCoefficientMeas hcontrolProductIntegrable
                hcontrolResidualIntegrable hcontrolResidualCondZero) i)))
  have hlindeberg :
      martingaleCLT.conditional_lindeberg :=
    triangular_conditional_lindeberg_of_eventually_scaled_finiteCell_thirdMoment
      treatedCells controlCells treatedSample controlSample treatedWeight
      treatedCoefficient treatedResidual controlWeight controlCoefficient
      controlResidual treatedScore controlScore treatedLindebergScale
      controlLindebergScale treatedLindebergBaseLoading
      controlLindebergBaseLoading treatedLindebergBaseLimit
      controlLindebergBaseLimit treatedThirdMomentLoading treatedMassLimit
      controlThirdMomentLoading controlMassLimit martingaleCLT
      hbridgeLindeberg htreatedLindebergScale hcontrolLindebergScale
      htreatedWeightNonneg hcontrolWeightNonneg htreatedCover hcontrolCover
      htreatedLindebergCoefficient hcontrolLindebergCoefficient
      htreatedLindebergBase hcontrolLindebergBase htreatedThirdLoading
      hcontrolThirdLoading htreatedMass hcontrolMass
  have hqv :
      martingaleCLT.predictable_quadratic_variation_stabilization :=
    triangular_predictable_quadratic_variation_stabilization_of_eventually_scaled_finiteCell_qv
      treatedCells controlCells treatedSample controlSample treatedWeight
      treatedCoefficient controlWeight controlCoefficient treatedScore
      controlScore treatedVariance controlVariance treatedQVScale
      controlQVScale treatedQVBaseCoefficientLoading
      controlQVBaseCoefficientLoading treatedVarianceLoading
      controlVarianceLoading treatedQVScaleLimit controlQVScaleLimit
      treatedQVBaseCoefficientLimit controlQVBaseCoefficientLimit
      treatedVarianceLimit controlVarianceLimit treatedMassLimit
      controlMassLimit martingaleCLT hbridgeQV htreatedQVScale
      hcontrolQVScale htreatedCover hcontrolCover htreatedQVCoefficient
      hcontrolQVCoefficient htreatedVariance hcontrolVariance
      htreatedQVBase hcontrolQVBase htreatedVarianceLimit
      hcontrolVarianceLimit htreatedMass hcontrolMass
  exact
    residual_clt_and_variance_formula_of_triangular_martingale_array_clt_bridge
      martingaleCLT hmartingale hlindeberg hqv

/--
Triangular residual CLT and variance formula from the three concrete
field-level reducers now available in this lane.

The martingale-difference field is closed from two-arm strongly-predictable
weighted residual increments; the conditional-Lindeberg and predictable-QV
fields are closed from eventual finite-cell loading, third-moment, variance,
and mass-convergence evidence.  The only remaining probability input is the
`TriangularMartingaleArrayCLTVarianceBridge.bridge` theorem itself.
-/
theorem residual_clt_and_variance_formula_of_triangular_stronglyPredictable_finiteCell_lindeberg_qv_bridge
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
    (treatedLindebergScale controlLindebergScale : Index -> Real)
    (treatedLindebergBaseLoading : Index -> TreatedCell -> Real)
    (controlLindebergBaseLoading : Index -> ControlCell -> Real)
    (treatedLindebergBaseLimit : TreatedCell -> Real)
    (controlLindebergBaseLimit : ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedVariance : Index -> Treated -> Real)
    (controlVariance : Index -> Control -> Real)
    (treatedQVScale controlQVScale : Index -> Real)
    (treatedQVBaseCoefficientLoading : Index -> TreatedCell -> Real)
    (controlQVBaseCoefficientLoading : Index -> ControlCell -> Real)
    (treatedVarianceLoading : Index -> TreatedCell -> Real)
    (controlVarianceLoading : Index -> ControlCell -> Real)
    (treatedQVScaleLimit controlQVScaleLimit : Real)
    (treatedQVBaseCoefficientLimit : TreatedCell -> Real)
    (controlQVBaseCoefficientLimit : ControlCell -> Real)
    (treatedVarianceLimit : TreatedCell -> Real)
    (controlVarianceLimit : ControlCell -> Real)
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    (treatedMartingaleCoefficient treatedMartingaleResidual :
      ℕ -> Ω -> Real)
    (controlMartingaleCoefficient controlMartingaleResidual :
      ℕ -> Ω -> Real)
    (htreatedCoefficientPredictable :
      IsStronglyPredictable ℱ treatedMartingaleCoefficient)
    (hcontrolCoefficientPredictable :
      IsStronglyPredictable ℱ controlMartingaleCoefficient)
    (htreatedResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (treatedMartingaleResidual i))
    (hcontrolResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (controlMartingaleResidual i))
    (htreatedProductIntegrable :
      ∀ i, Integrable
        (fun ω =>
          treatedMartingaleCoefficient (i + 1) ω *
            treatedMartingaleResidual i ω) μ)
    (hcontrolProductIntegrable :
      ∀ i, Integrable
        (fun ω =>
          controlMartingaleCoefficient (i + 1) ω *
            controlMartingaleResidual i ω) μ)
    (htreatedResidualIntegrable :
      ∀ i, Integrable (treatedMartingaleResidual i) μ)
    (hcontrolResidualIntegrable :
      ∀ i, Integrable (controlMartingaleResidual i) μ)
    (htreatedResidualCondZero :
      ∀ i, μ[treatedMartingaleResidual i | ℱ i] =ᵐ[μ] 0)
    (hcontrolResidualCondZero :
      ∀ i, μ[controlMartingaleResidual i | ℱ i] =ᵐ[μ] 0)
    (hmartingaleMap :
      Martingale
          (fun n ω =>
            ∑ k ∈ Finset.range n,
              treatedMartingaleCoefficient (k + 1) ω *
                treatedMartingaleResidual k ω)
          ℱ μ ->
        Martingale
            (fun n ω =>
              ∑ k ∈ Finset.range n,
                controlMartingaleCoefficient (k + 1) ω *
                  controlMartingaleResidual k ω)
            ℱ μ ->
          martingaleCLT.martingale_difference_array)
    (hbridgeLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        martingaleCLT.conditional_lindeberg)
    (hbridgeQV :
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
                treatedQVScaleLimit ^ 2 *
                  (treatedQVBaseCoefficientLimit cell ^ 2 *
                    treatedVarianceLimit cell))
              treatedMassLimit +
            weightedScoreCellMomentLimit controlCells
              (fun cell =>
                controlQVScaleLimit ^ 2 *
                  (controlQVBaseCoefficientLimit cell ^ 2 *
                    controlVarianceLimit cell))
              controlMassLimit)) ->
        martingaleCLT.predictable_quadratic_variation_stabilization)
    (htreatedLindebergScale :
      Tendsto treatedLindebergScale l (nhds 0))
    (hcontrolLindebergScale :
      Tendsto controlLindebergScale l (nhds 0))
    (htreatedQVScale :
      Tendsto treatedQVScale l (nhds treatedQVScaleLimit))
    (hcontrolQVScale :
      Tendsto controlQVScale l (nhds controlQVScaleLimit))
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
    (htreatedLindebergCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedLindebergScale index *
              treatedLindebergBaseLoading index
                (treatedScore index treated))
    (hcontrolLindebergCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlLindebergScale index *
              controlLindebergBaseLoading index
                (controlScore index control))
    (htreatedLindebergBase :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedLindebergBaseLoading index cell)
          l (nhds (treatedLindebergBaseLimit cell)))
    (hcontrolLindebergBase :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlLindebergBaseLoading index cell)
          l (nhds (controlLindebergBaseLimit cell)))
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
    (htreatedQVCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedQVScale index *
              treatedQVBaseCoefficientLoading index
                (treatedScore index treated))
    (hcontrolQVCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlQVScale index *
              controlQVBaseCoefficientLoading index
                (controlScore index control))
    (htreatedVariance :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedVariance index treated =
            treatedVarianceLoading index (treatedScore index treated))
    (hcontrolVariance :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlVariance index control =
            controlVarianceLoading index (controlScore index control))
    (htreatedQVBase :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedQVBaseCoefficientLoading index cell)
          l (nhds (treatedQVBaseCoefficientLimit cell)))
    (hcontrolQVBase :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlQVBaseCoefficientLoading index cell)
          l (nhds (controlQVBaseCoefficientLimit cell)))
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
    martingaleCLT.residual_clt ∧ martingaleCLT.residual_variance_formula := by
  have hmartingale :
      martingaleCLT.martingale_difference_array :=
    hmartingaleMap
      (martingale_of_condExp_sub_eq_zero_nat
        (fun n =>
          Finset.stronglyMeasurable_fun_sum (Finset.range n) fun k hk =>
            ((htreatedCoefficientPredictable.measurable_add_one k).mono
                (ℱ.mono (Nat.le_of_lt (Finset.mem_range.mp hk)))).mul
              ((htreatedResidualNextMeas k).mono
                (ℱ.mono (Nat.succ_le_of_lt (Finset.mem_range.mp hk)))))
        (fun n =>
          integrable_finsetSum (Finset.range n) fun k _ =>
            htreatedProductIntegrable k)
        (fun i =>
          (condExp_congr_ae
            (ae_of_all _ fun ω => by
              simp [Finset.sum_range_succ])).trans
            ((condExp_predictable_mul_residual_ae_eq_zero_nat
                (fun i ω => treatedMartingaleCoefficient (i + 1) ω)
                treatedMartingaleResidual
                (fun i => htreatedCoefficientPredictable.measurable_add_one i)
                htreatedProductIntegrable htreatedResidualIntegrable
                htreatedResidualCondZero) i)))
      (martingale_of_condExp_sub_eq_zero_nat
        (fun n =>
          Finset.stronglyMeasurable_fun_sum (Finset.range n) fun k hk =>
            ((hcontrolCoefficientPredictable.measurable_add_one k).mono
                (ℱ.mono (Nat.le_of_lt (Finset.mem_range.mp hk)))).mul
              ((hcontrolResidualNextMeas k).mono
                (ℱ.mono (Nat.succ_le_of_lt (Finset.mem_range.mp hk)))))
        (fun n =>
          integrable_finsetSum (Finset.range n) fun k _ =>
            hcontrolProductIntegrable k)
        (fun i =>
          (condExp_congr_ae
            (ae_of_all _ fun ω => by
              simp [Finset.sum_range_succ])).trans
            ((condExp_predictable_mul_residual_ae_eq_zero_nat
                (fun i ω => controlMartingaleCoefficient (i + 1) ω)
                controlMartingaleResidual
                (fun i => hcontrolCoefficientPredictable.measurable_add_one i)
                hcontrolProductIntegrable hcontrolResidualIntegrable
                hcontrolResidualCondZero) i)))
  have hlindeberg :
      martingaleCLT.conditional_lindeberg :=
    triangular_conditional_lindeberg_of_eventually_scaled_finiteCell_thirdMoment
      treatedCells controlCells treatedSample controlSample treatedWeight
      treatedCoefficient treatedResidual controlWeight controlCoefficient
      controlResidual treatedScore controlScore treatedLindebergScale
      controlLindebergScale treatedLindebergBaseLoading
      controlLindebergBaseLoading treatedLindebergBaseLimit
      controlLindebergBaseLimit treatedThirdMomentLoading treatedMassLimit
      controlThirdMomentLoading controlMassLimit martingaleCLT
      hbridgeLindeberg htreatedLindebergScale hcontrolLindebergScale
      htreatedWeightNonneg hcontrolWeightNonneg htreatedCover hcontrolCover
      htreatedLindebergCoefficient hcontrolLindebergCoefficient
      htreatedLindebergBase hcontrolLindebergBase htreatedThirdLoading
      hcontrolThirdLoading htreatedMass hcontrolMass
  have hqv :
      martingaleCLT.predictable_quadratic_variation_stabilization :=
    triangular_predictable_quadratic_variation_stabilization_of_eventually_scaled_finiteCell_qv
      treatedCells controlCells treatedSample controlSample treatedWeight
      treatedCoefficient controlWeight controlCoefficient treatedScore
      controlScore treatedVariance controlVariance treatedQVScale
      controlQVScale treatedQVBaseCoefficientLoading
      controlQVBaseCoefficientLoading treatedVarianceLoading
      controlVarianceLoading treatedQVScaleLimit controlQVScaleLimit
      treatedQVBaseCoefficientLimit controlQVBaseCoefficientLimit
      treatedVarianceLimit controlVarianceLimit treatedMassLimit
      controlMassLimit martingaleCLT hbridgeQV htreatedQVScale
      hcontrolQVScale htreatedCover hcontrolCover htreatedQVCoefficient
      hcontrolQVCoefficient htreatedVariance hcontrolVariance
      htreatedQVBase hcontrolQVBase htreatedVarianceLimit
      hcontrolVarianceLimit htreatedMass hcontrolMass
  exact
    residual_clt_and_variance_formula_of_triangular_martingale_array_clt_bridge
      martingaleCLT hmartingale hlindeberg hqv

/--
Residual CLT and variance formula for a
`ResidualMartingaleArrayCLTVarianceInput` from two-arm predictable martingale
evidence and finite-cell Lindeberg/QV evidence.

This is the input-level counterpart of
`residual_clt_and_variance_formula_of_triangular_predictable_finiteCell_lindeberg_qv_bridge`:
it only assumes explicit `ℱ i`-measurability of each coefficient at index `i`,
constructs the two Mathlib partial-sum martingales, then delegates the
finite-cell Lindeberg and QV fields to the checked reducers.
-/
theorem residual_clt_and_variance_formula_of_input_predictable_finiteCell_lindeberg_qv_bridge
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
    (treatedLindebergScale controlLindebergScale : Index -> Real)
    (treatedLindebergBaseLoading : Index -> TreatedCell -> Real)
    (controlLindebergBaseLoading : Index -> ControlCell -> Real)
    (treatedLindebergBaseLimit : TreatedCell -> Real)
    (controlLindebergBaseLimit : ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedVariance : Index -> Treated -> Real)
    (controlVariance : Index -> Control -> Real)
    (treatedQVScale controlQVScale : Index -> Real)
    (treatedQVBaseCoefficientLoading : Index -> TreatedCell -> Real)
    (controlQVBaseCoefficientLoading : Index -> ControlCell -> Real)
    (treatedVarianceLoading : Index -> TreatedCell -> Real)
    (controlVarianceLoading : Index -> ControlCell -> Real)
    (treatedQVScaleLimit controlQVScaleLimit : Real)
    (treatedQVBaseCoefficientLimit : TreatedCell -> Real)
    (controlQVBaseCoefficientLimit : ControlCell -> Real)
    (treatedVarianceLimit : TreatedCell -> Real)
    (controlVarianceLimit : ControlCell -> Real)
    (input : ResidualMartingaleArrayCLTVarianceInput)
    {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    (treatedMartingaleCoefficient treatedMartingaleResidual :
      ℕ -> Ω -> Real)
    (controlMartingaleCoefficient controlMartingaleResidual :
      ℕ -> Ω -> Real)
    (htreatedCoefficientMeas :
      ∀ i, StronglyMeasurable[ℱ i] (treatedMartingaleCoefficient i))
    (hcontrolCoefficientMeas :
      ∀ i, StronglyMeasurable[ℱ i] (controlMartingaleCoefficient i))
    (htreatedResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (treatedMartingaleResidual i))
    (hcontrolResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (controlMartingaleResidual i))
    (htreatedProductIntegrable :
      ∀ i, Integrable
        (fun ω =>
          treatedMartingaleCoefficient i ω *
            treatedMartingaleResidual i ω) μ)
    (hcontrolProductIntegrable :
      ∀ i, Integrable
        (fun ω =>
          controlMartingaleCoefficient i ω *
            controlMartingaleResidual i ω) μ)
    (htreatedResidualIntegrable :
      ∀ i, Integrable (treatedMartingaleResidual i) μ)
    (hcontrolResidualIntegrable :
      ∀ i, Integrable (controlMartingaleResidual i) μ)
    (htreatedResidualCondZero :
      ∀ i, μ[treatedMartingaleResidual i | ℱ i] =ᵐ[μ] 0)
    (hcontrolResidualCondZero :
      ∀ i, μ[controlMartingaleResidual i | ℱ i] =ᵐ[μ] 0)
    (hmartingaleMap :
      Martingale
          (fun n ω =>
            ∑ k ∈ Finset.range n,
              treatedMartingaleCoefficient k ω *
                treatedMartingaleResidual k ω)
          ℱ μ ->
        Martingale
            (fun n ω =>
              ∑ k ∈ Finset.range n,
                controlMartingaleCoefficient k ω *
                  controlMartingaleResidual k ω)
            ℱ μ ->
          input.martingale_difference_array)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        input.conditional_lindeberg)
    (hinputQV :
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
                treatedQVScaleLimit ^ 2 *
                  (treatedQVBaseCoefficientLimit cell ^ 2 *
                    treatedVarianceLimit cell))
              treatedMassLimit +
            weightedScoreCellMomentLimit controlCells
              (fun cell =>
                controlQVScaleLimit ^ 2 *
                  (controlQVBaseCoefficientLimit cell ^ 2 *
                    controlVarianceLimit cell))
              controlMassLimit)) ->
        input.predictable_quadratic_variation_stabilization)
    (hexact : input.exact_weighted_reuse_moment_limits)
    (hregularity : input.residual_moment_regularity)
    (htreatedLindebergScale :
      Tendsto treatedLindebergScale l (nhds 0))
    (hcontrolLindebergScale :
      Tendsto controlLindebergScale l (nhds 0))
    (htreatedQVScale :
      Tendsto treatedQVScale l (nhds treatedQVScaleLimit))
    (hcontrolQVScale :
      Tendsto controlQVScale l (nhds controlQVScaleLimit))
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
    (htreatedLindebergCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedLindebergScale index *
              treatedLindebergBaseLoading index
                (treatedScore index treated))
    (hcontrolLindebergCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlLindebergScale index *
              controlLindebergBaseLoading index
                (controlScore index control))
    (htreatedLindebergBase :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedLindebergBaseLoading index cell)
          l (nhds (treatedLindebergBaseLimit cell)))
    (hcontrolLindebergBase :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlLindebergBaseLoading index cell)
          l (nhds (controlLindebergBaseLimit cell)))
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
    (htreatedQVCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedQVScale index *
              treatedQVBaseCoefficientLoading index
                (treatedScore index treated))
    (hcontrolQVCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlQVScale index *
              controlQVBaseCoefficientLoading index
                (controlScore index control))
    (htreatedVariance :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedVariance index treated =
            treatedVarianceLoading index (treatedScore index treated))
    (hcontrolVariance :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlVariance index control =
            controlVarianceLoading index (controlScore index control))
    (htreatedQVBase :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedQVBaseCoefficientLoading index cell)
          l (nhds (treatedQVBaseCoefficientLimit cell)))
    (hcontrolQVBase :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlQVBaseCoefficientLoading index cell)
          l (nhds (controlQVBaseCoefficientLimit cell)))
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
    input.residual_clt ∧ input.residual_variance_formula := by
  have hmartingale :
      input.martingale_difference_array :=
    hmartingaleMap
      (martingale_of_condExp_sub_eq_zero_nat
        (fun n =>
          Finset.stronglyMeasurable_fun_sum (Finset.range n) fun k hk =>
            ((htreatedCoefficientMeas k).mono
                (ℱ.mono (Nat.le_of_lt (Finset.mem_range.mp hk)))).mul
              ((htreatedResidualNextMeas k).mono
                (ℱ.mono (Nat.succ_le_of_lt (Finset.mem_range.mp hk)))))
        (fun n =>
          integrable_finsetSum (Finset.range n) fun k _ =>
            htreatedProductIntegrable k)
        (fun i =>
          (condExp_congr_ae
            (ae_of_all _ fun ω => by
              simp [Finset.sum_range_succ])).trans
            ((condExp_predictable_mul_residual_ae_eq_zero_nat
                treatedMartingaleCoefficient treatedMartingaleResidual
                htreatedCoefficientMeas htreatedProductIntegrable
                htreatedResidualIntegrable htreatedResidualCondZero) i)))
      (martingale_of_condExp_sub_eq_zero_nat
        (fun n =>
          Finset.stronglyMeasurable_fun_sum (Finset.range n) fun k hk =>
            ((hcontrolCoefficientMeas k).mono
                (ℱ.mono (Nat.le_of_lt (Finset.mem_range.mp hk)))).mul
              ((hcontrolResidualNextMeas k).mono
                (ℱ.mono (Nat.succ_le_of_lt (Finset.mem_range.mp hk)))))
        (fun n =>
          integrable_finsetSum (Finset.range n) fun k _ =>
            hcontrolProductIntegrable k)
        (fun i =>
          (condExp_congr_ae
            (ae_of_all _ fun ω => by
              simp [Finset.sum_range_succ])).trans
            ((condExp_predictable_mul_residual_ae_eq_zero_nat
                controlMartingaleCoefficient controlMartingaleResidual
                hcontrolCoefficientMeas hcontrolProductIntegrable
                hcontrolResidualIntegrable hcontrolResidualCondZero) i)))
  exact
    residual_clt_and_variance_formula_of_eventually_scaled_finiteCell_lindeberg_qv_bridge
      treatedCells controlCells treatedSample controlSample treatedWeight
      treatedCoefficient treatedResidual controlWeight controlCoefficient
      controlResidual treatedScore controlScore treatedLindebergScale
      controlLindebergScale treatedLindebergBaseLoading
      controlLindebergBaseLoading treatedLindebergBaseLimit
      controlLindebergBaseLimit treatedThirdMomentLoading treatedMassLimit
      controlThirdMomentLoading controlMassLimit treatedVariance
      controlVariance treatedQVScale controlQVScale
      treatedQVBaseCoefficientLoading controlQVBaseCoefficientLoading
      treatedVarianceLoading controlVarianceLoading treatedQVScaleLimit
      controlQVScaleLimit treatedQVBaseCoefficientLimit
      controlQVBaseCoefficientLimit treatedVarianceLimit controlVarianceLimit
      input hinputLindeberg hinputQV hexact hregularity hmartingale
      htreatedLindebergScale hcontrolLindebergScale htreatedQVScale
      hcontrolQVScale htreatedWeightNonneg hcontrolWeightNonneg
      htreatedCover hcontrolCover htreatedLindebergCoefficient
      hcontrolLindebergCoefficient htreatedLindebergBase
      hcontrolLindebergBase htreatedThirdLoading hcontrolThirdLoading
      htreatedQVCoefficient hcontrolQVCoefficient htreatedVariance
      hcontrolVariance htreatedQVBase hcontrolQVBase htreatedVarianceLimit
      hcontrolVarianceLimit htreatedMass hcontrolMass

/--
Residual CLT and variance formula for a
`ResidualMartingaleArrayCLTVarianceInput` from the same strongly-predictable
two-arm martingale evidence and finite-cell Lindeberg/QV evidence used by the
triangular composite endpoint.

This closes the input's martingale-difference field locally from Mathlib
partial-sum martingales, then delegates the Lindeberg and QV fields to
`residual_clt_and_variance_formula_of_eventually_scaled_finiteCell_lindeberg_qv_bridge`.
-/
theorem residual_clt_and_variance_formula_of_input_stronglyPredictable_finiteCell_lindeberg_qv_bridge
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
    (treatedLindebergScale controlLindebergScale : Index -> Real)
    (treatedLindebergBaseLoading : Index -> TreatedCell -> Real)
    (controlLindebergBaseLoading : Index -> ControlCell -> Real)
    (treatedLindebergBaseLimit : TreatedCell -> Real)
    (controlLindebergBaseLimit : ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedVariance : Index -> Treated -> Real)
    (controlVariance : Index -> Control -> Real)
    (treatedQVScale controlQVScale : Index -> Real)
    (treatedQVBaseCoefficientLoading : Index -> TreatedCell -> Real)
    (controlQVBaseCoefficientLoading : Index -> ControlCell -> Real)
    (treatedVarianceLoading : Index -> TreatedCell -> Real)
    (controlVarianceLoading : Index -> ControlCell -> Real)
    (treatedQVScaleLimit controlQVScaleLimit : Real)
    (treatedQVBaseCoefficientLimit : TreatedCell -> Real)
    (controlQVBaseCoefficientLimit : ControlCell -> Real)
    (treatedVarianceLimit : TreatedCell -> Real)
    (controlVarianceLimit : ControlCell -> Real)
    (input : ResidualMartingaleArrayCLTVarianceInput)
    {Ω : Type*} {m0 : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ] {ℱ : Filtration ℕ m0}
    (treatedMartingaleCoefficient treatedMartingaleResidual :
      ℕ -> Ω -> Real)
    (controlMartingaleCoefficient controlMartingaleResidual :
      ℕ -> Ω -> Real)
    (htreatedCoefficientPredictable :
      IsStronglyPredictable ℱ treatedMartingaleCoefficient)
    (hcontrolCoefficientPredictable :
      IsStronglyPredictable ℱ controlMartingaleCoefficient)
    (htreatedResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (treatedMartingaleResidual i))
    (hcontrolResidualNextMeas :
      ∀ i, StronglyMeasurable[ℱ (i + 1)] (controlMartingaleResidual i))
    (htreatedProductIntegrable :
      ∀ i, Integrable
        (fun ω =>
          treatedMartingaleCoefficient (i + 1) ω *
            treatedMartingaleResidual i ω) μ)
    (hcontrolProductIntegrable :
      ∀ i, Integrable
        (fun ω =>
          controlMartingaleCoefficient (i + 1) ω *
            controlMartingaleResidual i ω) μ)
    (htreatedResidualIntegrable :
      ∀ i, Integrable (treatedMartingaleResidual i) μ)
    (hcontrolResidualIntegrable :
      ∀ i, Integrable (controlMartingaleResidual i) μ)
    (htreatedResidualCondZero :
      ∀ i, μ[treatedMartingaleResidual i | ℱ i] =ᵐ[μ] 0)
    (hcontrolResidualCondZero :
      ∀ i, μ[controlMartingaleResidual i | ℱ i] =ᵐ[μ] 0)
    (hmartingaleMap :
      Martingale
          (fun n ω =>
            ∑ k ∈ Finset.range n,
              treatedMartingaleCoefficient (k + 1) ω *
                treatedMartingaleResidual k ω)
          ℱ μ ->
        Martingale
            (fun n ω =>
              ∑ k ∈ Finset.range n,
                controlMartingaleCoefficient (k + 1) ω *
                  controlMartingaleResidual k ω)
            ℱ μ ->
          input.martingale_difference_array)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        input.conditional_lindeberg)
    (hinputQV :
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
                treatedQVScaleLimit ^ 2 *
                  (treatedQVBaseCoefficientLimit cell ^ 2 *
                    treatedVarianceLimit cell))
              treatedMassLimit +
            weightedScoreCellMomentLimit controlCells
              (fun cell =>
                controlQVScaleLimit ^ 2 *
                  (controlQVBaseCoefficientLimit cell ^ 2 *
                    controlVarianceLimit cell))
              controlMassLimit)) ->
        input.predictable_quadratic_variation_stabilization)
    (hexact : input.exact_weighted_reuse_moment_limits)
    (hregularity : input.residual_moment_regularity)
    (htreatedLindebergScale :
      Tendsto treatedLindebergScale l (nhds 0))
    (hcontrolLindebergScale :
      Tendsto controlLindebergScale l (nhds 0))
    (htreatedQVScale :
      Tendsto treatedQVScale l (nhds treatedQVScaleLimit))
    (hcontrolQVScale :
      Tendsto controlQVScale l (nhds controlQVScaleLimit))
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
    (htreatedLindebergCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedLindebergScale index *
              treatedLindebergBaseLoading index
                (treatedScore index treated))
    (hcontrolLindebergCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlLindebergScale index *
              controlLindebergBaseLoading index
                (controlScore index control))
    (htreatedLindebergBase :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedLindebergBaseLoading index cell)
          l (nhds (treatedLindebergBaseLimit cell)))
    (hcontrolLindebergBase :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlLindebergBaseLoading index cell)
          l (nhds (controlLindebergBaseLimit cell)))
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
    (htreatedQVCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedQVScale index *
              treatedQVBaseCoefficientLoading index
                (treatedScore index treated))
    (hcontrolQVCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlQVScale index *
              controlQVBaseCoefficientLoading index
                (controlScore index control))
    (htreatedVariance :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedVariance index treated =
            treatedVarianceLoading index (treatedScore index treated))
    (hcontrolVariance :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlVariance index control =
            controlVarianceLoading index (controlScore index control))
    (htreatedQVBase :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedQVBaseCoefficientLoading index cell)
          l (nhds (treatedQVBaseCoefficientLimit cell)))
    (hcontrolQVBase :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlQVBaseCoefficientLoading index cell)
          l (nhds (controlQVBaseCoefficientLimit cell)))
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
    input.residual_clt ∧ input.residual_variance_formula := by
  have hmartingale :
      input.martingale_difference_array :=
    hmartingaleMap
      (martingale_of_condExp_sub_eq_zero_nat
        (fun n =>
          Finset.stronglyMeasurable_fun_sum (Finset.range n) fun k hk =>
            ((htreatedCoefficientPredictable.measurable_add_one k).mono
                (ℱ.mono (Nat.le_of_lt (Finset.mem_range.mp hk)))).mul
              ((htreatedResidualNextMeas k).mono
                (ℱ.mono (Nat.succ_le_of_lt (Finset.mem_range.mp hk)))))
        (fun n =>
          integrable_finsetSum (Finset.range n) fun k _ =>
            htreatedProductIntegrable k)
        (fun i =>
          (condExp_congr_ae
            (ae_of_all _ fun ω => by
              simp [Finset.sum_range_succ])).trans
            ((condExp_predictable_mul_residual_ae_eq_zero_nat
                (fun i ω => treatedMartingaleCoefficient (i + 1) ω)
                treatedMartingaleResidual
                (fun i => htreatedCoefficientPredictable.measurable_add_one i)
                htreatedProductIntegrable htreatedResidualIntegrable
                htreatedResidualCondZero) i)))
      (martingale_of_condExp_sub_eq_zero_nat
        (fun n =>
          Finset.stronglyMeasurable_fun_sum (Finset.range n) fun k hk =>
            ((hcontrolCoefficientPredictable.measurable_add_one k).mono
                (ℱ.mono (Nat.le_of_lt (Finset.mem_range.mp hk)))).mul
              ((hcontrolResidualNextMeas k).mono
                (ℱ.mono (Nat.succ_le_of_lt (Finset.mem_range.mp hk)))))
        (fun n =>
          integrable_finsetSum (Finset.range n) fun k _ =>
            hcontrolProductIntegrable k)
        (fun i =>
          (condExp_congr_ae
            (ae_of_all _ fun ω => by
              simp [Finset.sum_range_succ])).trans
            ((condExp_predictable_mul_residual_ae_eq_zero_nat
                (fun i ω => controlMartingaleCoefficient (i + 1) ω)
                controlMartingaleResidual
                (fun i => hcontrolCoefficientPredictable.measurable_add_one i)
                hcontrolProductIntegrable hcontrolResidualIntegrable
                hcontrolResidualCondZero) i)))
  exact
    residual_clt_and_variance_formula_of_eventually_scaled_finiteCell_lindeberg_qv_bridge
      treatedCells controlCells treatedSample controlSample treatedWeight
      treatedCoefficient treatedResidual controlWeight controlCoefficient
      controlResidual treatedScore controlScore treatedLindebergScale
      controlLindebergScale treatedLindebergBaseLoading
      controlLindebergBaseLoading treatedLindebergBaseLimit
      controlLindebergBaseLimit treatedThirdMomentLoading treatedMassLimit
      controlThirdMomentLoading controlMassLimit treatedVariance
      controlVariance treatedQVScale controlQVScale
      treatedQVBaseCoefficientLoading controlQVBaseCoefficientLoading
      treatedVarianceLoading controlVarianceLoading treatedQVScaleLimit
      controlQVScaleLimit treatedQVBaseCoefficientLimit
      controlQVBaseCoefficientLimit treatedVarianceLimit controlVarianceLimit
      input hinputLindeberg hinputQV hexact hregularity hmartingale
      htreatedLindebergScale hcontrolLindebergScale htreatedQVScale
      hcontrolQVScale htreatedWeightNonneg hcontrolWeightNonneg
      htreatedCover hcontrolCover htreatedLindebergCoefficient
      hcontrolLindebergCoefficient htreatedLindebergBase
      hcontrolLindebergBase htreatedThirdLoading hcontrolThirdLoading
      htreatedQVCoefficient hcontrolQVCoefficient htreatedVariance
      hcontrolVariance htreatedQVBase hcontrolQVBase htreatedVarianceLimit
      hcontrolVarianceLimit htreatedMass hcontrolMass

/--
Triangular residual CLT and variance formula from eventual finite-cell
Lindeberg/QV premises plus an explicit two-arm martingale-difference bridge
and two-arm sampling/filtration bridge.

This is the triangular counterpart of
`residual_clt_and_variance_formula_of_eventually_scaled_finiteCell_lindeberg_qv_sampling_bridge`:
the martingale-difference field is closed through the named two-arm residual
and sampling bridges, while the conditional-Lindeberg and predictable-QV
fields are closed by the finite-cell reducers in this module.
-/
theorem residual_clt_and_variance_formula_of_triangular_eventually_scaled_finiteCell_lindeberg_qv_sampling_bridge
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
    (treatedLindebergScale controlLindebergScale : Index -> Real)
    (treatedLindebergBaseLoading : Index -> TreatedCell -> Real)
    (controlLindebergBaseLoading : Index -> ControlCell -> Real)
    (treatedLindebergBaseLimit : TreatedCell -> Real)
    (controlLindebergBaseLimit : ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedVariance : Index -> Treated -> Real)
    (controlVariance : Index -> Control -> Real)
    (treatedQVScale controlQVScale : Index -> Real)
    (treatedQVBaseCoefficientLoading : Index -> TreatedCell -> Real)
    (controlQVBaseCoefficientLoading : Index -> ControlCell -> Real)
    (treatedVarianceLoading : Index -> TreatedCell -> Real)
    (controlVarianceLoading : Index -> ControlCell -> Real)
    (treatedQVScaleLimit controlQVScaleLimit : Real)
    (treatedQVBaseCoefficientLimit : TreatedCell -> Real)
    (controlQVBaseCoefficientLimit : ControlCell -> Real)
    (treatedVarianceLimit : TreatedCell -> Real)
    (controlVarianceLimit : ControlCell -> Real)
    (martingaleCLT : TriangularMartingaleArrayCLTVarianceBridge)
    (martingaleBridge : TwoArmResidualMartingaleDifferenceBridge)
    (regularityBridge : TwoArmResidualSamplingFiltrationRegularityBridge)
    (harrayMap :
      martingaleBridge.martingale_difference_array ->
        martingaleCLT.martingale_difference_array)
    (htreatedPredictable :
      martingaleBridge.treated_coefficient_predictability)
    (hcontrolPredictable :
      martingaleBridge.control_coefficient_predictability)
    (htreatedZero :
      martingaleBridge.treated_residual_conditional_mean_zero)
    (hcontrolZero :
      martingaleBridge.control_residual_conditional_mean_zero)
    (hregularityMap :
      regularityBridge.arm_sampling_or_filtration_regular ->
        martingaleBridge.arm_sampling_or_filtration_regular)
    (hfiltration : regularityBridge.array_filtration_defined)
    (htreatedAdapted :
      regularityBridge.treated_coefficient_adapted_to_past)
    (hcontrolAdapted :
      regularityBridge.control_coefficient_adapted_to_past)
    (htreatedInnovation :
      regularityBridge.treated_residual_innovation_measurable)
    (hcontrolInnovation :
      regularityBridge.control_residual_innovation_measurable)
    (horder : regularityBridge.arm_order_regular)
    (hcross : regularityBridge.cross_arm_sampling_regular)
    (hdesign : regularityBridge.conditional_design_regular)
    (hintegrable : martingaleBridge.finite_array_integrability)
    (hbridgeLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        martingaleCLT.conditional_lindeberg)
    (hbridgeQV :
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
                treatedQVScaleLimit ^ 2 *
                  (treatedQVBaseCoefficientLimit cell ^ 2 *
                    treatedVarianceLimit cell))
              treatedMassLimit +
            weightedScoreCellMomentLimit controlCells
              (fun cell =>
                controlQVScaleLimit ^ 2 *
                  (controlQVBaseCoefficientLimit cell ^ 2 *
                    controlVarianceLimit cell))
              controlMassLimit)) ->
        martingaleCLT.predictable_quadratic_variation_stabilization)
    (htreatedLindebergScale :
      Tendsto treatedLindebergScale l (nhds 0))
    (hcontrolLindebergScale :
      Tendsto controlLindebergScale l (nhds 0))
    (htreatedQVScale :
      Tendsto treatedQVScale l (nhds treatedQVScaleLimit))
    (hcontrolQVScale :
      Tendsto controlQVScale l (nhds controlQVScaleLimit))
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
    (htreatedLindebergCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedLindebergScale index *
              treatedLindebergBaseLoading index
                (treatedScore index treated))
    (hcontrolLindebergCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlLindebergScale index *
              controlLindebergBaseLoading index
                (controlScore index control))
    (htreatedLindebergBase :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedLindebergBaseLoading index cell)
          l (nhds (treatedLindebergBaseLimit cell)))
    (hcontrolLindebergBase :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlLindebergBaseLoading index cell)
          l (nhds (controlLindebergBaseLimit cell)))
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
    (htreatedQVCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedQVScale index *
              treatedQVBaseCoefficientLoading index
                (treatedScore index treated))
    (hcontrolQVCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlQVScale index *
              controlQVBaseCoefficientLoading index
                (controlScore index control))
    (htreatedVariance :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedVariance index treated =
            treatedVarianceLoading index (treatedScore index treated))
    (hcontrolVariance :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlVariance index control =
            controlVarianceLoading index (controlScore index control))
    (htreatedQVBase :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedQVBaseCoefficientLoading index cell)
          l (nhds (treatedQVBaseCoefficientLimit cell)))
    (hcontrolQVBase :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlQVBaseCoefficientLoading index cell)
          l (nhds (controlQVBaseCoefficientLimit cell)))
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
    martingaleCLT.residual_clt ∧ martingaleCLT.residual_variance_formula := by
  have hmartingale :
      martingaleCLT.martingale_difference_array :=
    harrayMap
      (martingaleBridge.bridge htreatedPredictable hcontrolPredictable
        htreatedZero hcontrolZero
        (hregularityMap
          (regularityBridge.bridge hfiltration htreatedAdapted
            hcontrolAdapted htreatedInnovation hcontrolInnovation horder
            hcross hdesign))
        hintegrable)
  have hlindeberg :
      martingaleCLT.conditional_lindeberg :=
    triangular_conditional_lindeberg_of_eventually_scaled_finiteCell_thirdMoment
      treatedCells controlCells treatedSample controlSample treatedWeight
      treatedCoefficient treatedResidual controlWeight controlCoefficient
      controlResidual treatedScore controlScore treatedLindebergScale
      controlLindebergScale treatedLindebergBaseLoading
      controlLindebergBaseLoading treatedLindebergBaseLimit
      controlLindebergBaseLimit treatedThirdMomentLoading treatedMassLimit
      controlThirdMomentLoading controlMassLimit martingaleCLT
      hbridgeLindeberg htreatedLindebergScale hcontrolLindebergScale
      htreatedWeightNonneg hcontrolWeightNonneg htreatedCover hcontrolCover
      htreatedLindebergCoefficient hcontrolLindebergCoefficient
      htreatedLindebergBase hcontrolLindebergBase htreatedThirdLoading
      hcontrolThirdLoading htreatedMass hcontrolMass
  have hqv :
      martingaleCLT.predictable_quadratic_variation_stabilization :=
    triangular_predictable_quadratic_variation_stabilization_of_eventually_scaled_finiteCell_qv
      treatedCells controlCells treatedSample controlSample treatedWeight
      treatedCoefficient controlWeight controlCoefficient treatedScore
      controlScore treatedVariance controlVariance treatedQVScale
      controlQVScale treatedQVBaseCoefficientLoading
      controlQVBaseCoefficientLoading treatedVarianceLoading
      controlVarianceLoading treatedQVScaleLimit controlQVScaleLimit
      treatedQVBaseCoefficientLimit controlQVBaseCoefficientLimit
      treatedVarianceLimit controlVarianceLimit treatedMassLimit
      controlMassLimit martingaleCLT hbridgeQV htreatedQVScale
      hcontrolQVScale htreatedCover hcontrolCover htreatedQVCoefficient
      hcontrolQVCoefficient htreatedVariance hcontrolVariance
      htreatedQVBase hcontrolQVBase htreatedVarianceLimit
      hcontrolVarianceLimit htreatedMass hcontrolMass
  exact
    residual_clt_and_variance_formula_of_triangular_martingale_array_clt_bridge
      martingaleCLT hmartingale hlindeberg hqv

/--
Residual CLT and variance formula from eventual finite-cell Lindeberg/QV
premises plus an explicit two-arm martingale-difference bridge.

This is the same finite-cell route as
`residual_clt_and_variance_formula_of_eventually_scaled_finiteCell_lindeberg_qv_bridge`,
but it closes the martingale-difference input through named two-arm
predictability, residual mean-zero, sampling/filtration, and integrability
components.
-/
theorem residual_clt_and_variance_formula_of_eventually_scaled_finiteCell_lindeberg_qv_sampling_bridge
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
    (treatedLindebergScale controlLindebergScale : Index -> Real)
    (treatedLindebergBaseLoading : Index -> TreatedCell -> Real)
    (controlLindebergBaseLoading : Index -> ControlCell -> Real)
    (treatedLindebergBaseLimit : TreatedCell -> Real)
    (controlLindebergBaseLimit : ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedVariance : Index -> Treated -> Real)
    (controlVariance : Index -> Control -> Real)
    (treatedQVScale controlQVScale : Index -> Real)
    (treatedQVBaseCoefficientLoading : Index -> TreatedCell -> Real)
    (controlQVBaseCoefficientLoading : Index -> ControlCell -> Real)
    (treatedVarianceLoading : Index -> TreatedCell -> Real)
    (controlVarianceLoading : Index -> ControlCell -> Real)
    (treatedQVScaleLimit controlQVScaleLimit : Real)
    (treatedQVBaseCoefficientLimit : TreatedCell -> Real)
    (controlQVBaseCoefficientLimit : ControlCell -> Real)
    (treatedVarianceLimit : TreatedCell -> Real)
    (controlVarianceLimit : ControlCell -> Real)
    (input : ResidualMartingaleArrayCLTVarianceInput)
    (martingaleBridge : TwoArmResidualMartingaleDifferenceBridge)
    (regularityBridge : TwoArmResidualSamplingFiltrationRegularityBridge)
    (harrayMap :
      martingaleBridge.martingale_difference_array ->
        input.martingale_difference_array)
    (htreatedPredictable :
      martingaleBridge.treated_coefficient_predictability)
    (hcontrolPredictable :
      martingaleBridge.control_coefficient_predictability)
    (htreatedZero :
      martingaleBridge.treated_residual_conditional_mean_zero)
    (hcontrolZero :
      martingaleBridge.control_residual_conditional_mean_zero)
    (hregularityMap :
      regularityBridge.arm_sampling_or_filtration_regular ->
        martingaleBridge.arm_sampling_or_filtration_regular)
    (hfiltration : regularityBridge.array_filtration_defined)
    (htreatedAdapted :
      regularityBridge.treated_coefficient_adapted_to_past)
    (hcontrolAdapted :
      regularityBridge.control_coefficient_adapted_to_past)
    (htreatedInnovation :
      regularityBridge.treated_residual_innovation_measurable)
    (hcontrolInnovation :
      regularityBridge.control_residual_innovation_measurable)
    (horder : regularityBridge.arm_order_regular)
    (hcross : regularityBridge.cross_arm_sampling_regular)
    (hdesign : regularityBridge.conditional_design_regular)
    (hintegrable : martingaleBridge.finite_array_integrability)
    (hinputLindeberg :
      twoArmResidualLindebergCondition (l := l) treatedSample controlSample
        treatedWeight treatedCoefficient treatedResidual
        controlWeight controlCoefficient controlResidual ->
        input.conditional_lindeberg)
    (hinputQV :
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
                treatedQVScaleLimit ^ 2 *
                  (treatedQVBaseCoefficientLimit cell ^ 2 *
                    treatedVarianceLimit cell))
              treatedMassLimit +
            weightedScoreCellMomentLimit controlCells
              (fun cell =>
                controlQVScaleLimit ^ 2 *
                  (controlQVBaseCoefficientLimit cell ^ 2 *
                    controlVarianceLimit cell))
              controlMassLimit)) ->
        input.predictable_quadratic_variation_stabilization)
    (hexact : input.exact_weighted_reuse_moment_limits)
    (hregularity : input.residual_moment_regularity)
    (htreatedLindebergScale :
      Tendsto treatedLindebergScale l (nhds 0))
    (hcontrolLindebergScale :
      Tendsto controlLindebergScale l (nhds 0))
    (htreatedQVScale :
      Tendsto treatedQVScale l (nhds treatedQVScaleLimit))
    (hcontrolQVScale :
      Tendsto controlQVScale l (nhds controlQVScaleLimit))
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
    (htreatedLindebergCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedLindebergScale index *
              treatedLindebergBaseLoading index
                (treatedScore index treated))
    (hcontrolLindebergCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlLindebergScale index *
              controlLindebergBaseLoading index
                (controlScore index control))
    (htreatedLindebergBase :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedLindebergBaseLoading index cell)
          l (nhds (treatedLindebergBaseLimit cell)))
    (hcontrolLindebergBase :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlLindebergBaseLoading index cell)
          l (nhds (controlLindebergBaseLimit cell)))
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
    (htreatedQVCoefficient :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedCoefficient index treated =
            treatedQVScale index *
              treatedQVBaseCoefficientLoading index
                (treatedScore index treated))
    (hcontrolQVCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlQVScale index *
              controlQVBaseCoefficientLoading index
                (controlScore index control))
    (htreatedVariance :
      ∀ᶠ index in l,
        ∀ treated, treated ∈ treatedSample index ->
          treatedVariance index treated =
            treatedVarianceLoading index (treatedScore index treated))
    (hcontrolVariance :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlVariance index control =
            controlVarianceLoading index (controlScore index control))
    (htreatedQVBase :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedQVBaseCoefficientLoading index cell)
          l (nhds (treatedQVBaseCoefficientLimit cell)))
    (hcontrolQVBase :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlQVBaseCoefficientLoading index cell)
          l (nhds (controlQVBaseCoefficientLimit cell)))
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
    input.residual_clt ∧ input.residual_variance_formula :=
  residual_clt_and_variance_formula_of_eventually_scaled_finiteCell_lindeberg_qv_bridge
    treatedCells controlCells treatedSample controlSample treatedWeight
    treatedCoefficient treatedResidual controlWeight controlCoefficient
    controlResidual treatedScore controlScore treatedLindebergScale
    controlLindebergScale treatedLindebergBaseLoading
    controlLindebergBaseLoading treatedLindebergBaseLimit
    controlLindebergBaseLimit treatedThirdMomentLoading treatedMassLimit
    controlThirdMomentLoading controlMassLimit treatedVariance
    controlVariance treatedQVScale controlQVScale
    treatedQVBaseCoefficientLoading controlQVBaseCoefficientLoading
    treatedVarianceLoading controlVarianceLoading treatedQVScaleLimit
    controlQVScaleLimit treatedQVBaseCoefficientLimit
    controlQVBaseCoefficientLimit treatedVarianceLimit controlVarianceLimit
    input hinputLindeberg hinputQV hexact hregularity
    (input_martingale_difference_array_of_twoArm_residual_sampling_bridge
      input martingaleBridge regularityBridge harrayMap htreatedPredictable
      hcontrolPredictable htreatedZero hcontrolZero hregularityMap
      hfiltration htreatedAdapted hcontrolAdapted htreatedInnovation
      hcontrolInnovation horder hcross hdesign hintegrable)
    htreatedLindebergScale hcontrolLindebergScale htreatedQVScale
    hcontrolQVScale htreatedWeightNonneg hcontrolWeightNonneg htreatedCover
    hcontrolCover htreatedLindebergCoefficient
    hcontrolLindebergCoefficient htreatedLindebergBase
    hcontrolLindebergBase htreatedThirdLoading hcontrolThirdLoading
    htreatedQVCoefficient hcontrolQVCoefficient htreatedVariance
    hcontrolVariance htreatedQVBase hcontrolQVBase htreatedVarianceLimit
    hcontrolVarianceLimit htreatedMass hcontrolMass

end WDSM
end Matching
end StatInference
