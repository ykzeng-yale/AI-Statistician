import StatInference.Matching.WDSM.FiniteCellScaledLoading
import StatInference.Matching.WDSM.FiniteCellVaryingMomentConvergence

/-!
# Residual martingale bridge from scaled finite-cell premises

This module composes two deterministic finite-cell routes:

* scaled coefficient loadings plus residual third moments imply the concrete
  two-arm residual Lindeberg condition;
* scaled QV loadings plus score-cell mass convergence imply the two-arm
  weighted quadratic-variation convergence.

The generic martingale CLT theorem remains an explicit probability input, but
the residual martingale interface can now be fed by one coherent bundle of
finite-cell WDSM premises.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Treated Control TreatedCell ControlCell : Type*}
  {l : Filter Index} [DecidableEq TreatedCell] [DecidableEq ControlCell]

/--
Residual CLT and variance formula from scaled finite-cell coefficient
loadings, scaled finite-cell QV loadings, finite residual third moments, and
score-cell mass convergence.
-/
theorem residual_clt_and_variance_formula_of_scaled_finiteCell_lindeberg_qv_bridge
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
    (treatedCoeffScale controlCoeffScale : Index -> Real)
    (treatedBaseCoeffLoading : Index -> TreatedCell -> Real)
    (controlBaseCoeffLoading : Index -> ControlCell -> Real)
    (treatedBaseCoeffLimit : TreatedCell -> Real)
    (controlBaseCoeffLimit : ControlCell -> Real)
    (treatedThirdMomentLoading treatedMassLimit : TreatedCell -> Real)
    (controlThirdMomentLoading controlMassLimit : ControlCell -> Real)
    (treatedVariance : Index -> Treated -> Real)
    (controlVariance : Index -> Control -> Real)
    (treatedQVScale controlQVScale : Index -> Real)
    (treatedBaseQVLoading : Index -> TreatedCell -> Real)
    (controlBaseQVLoading : Index -> ControlCell -> Real)
    (treatedQVScaleLimit controlQVScaleLimit : Real)
    (treatedBaseQVLimit : TreatedCell -> Real)
    (controlBaseQVLimit : ControlCell -> Real)
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
              (fun cell => treatedQVScaleLimit * treatedBaseQVLimit cell)
              treatedMassLimit +
            weightedScoreCellMomentLimit controlCells
              (fun cell => controlQVScaleLimit * controlBaseQVLimit cell)
              controlMassLimit)) ->
        input.predictable_quadratic_variation_stabilization)
    (hexact : input.exact_weighted_reuse_moment_limits)
    (hregularity : input.residual_moment_regularity)
    (hmartingale : input.martingale_difference_array)
    (htreatedCoeffScale : Tendsto treatedCoeffScale l (nhds 0))
    (hcontrolCoeffScale : Tendsto controlCoeffScale l (nhds 0))
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
            treatedCoeffScale index *
              treatedBaseCoeffLoading index (treatedScore index treated))
    (hcontrolCoefficient :
      ∀ᶠ index in l,
        ∀ control, control ∈ controlSample index ->
          controlCoefficient index control =
            controlCoeffScale index *
              controlBaseCoeffLoading index (controlScore index control))
    (htreatedBaseCoeff :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedBaseCoeffLoading index cell)
          l (nhds (treatedBaseCoeffLimit cell)))
    (hcontrolBaseCoeff :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlBaseCoeffLoading index cell)
          l (nhds (controlBaseCoeffLimit cell)))
    (htreatedThirdLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedThirdMomentLoading (treatedScore index treated) =
          |treatedResidual index treated| ^ 3)
    (hcontrolThirdLoading :
      ∀ index control, control ∈ controlSample index ->
        controlThirdMomentLoading (controlScore index control) =
          |controlResidual index control| ^ 3)
    (htreatedQVLoading :
      ∀ index treated, treated ∈ treatedSample index ->
        treatedQVScale index *
            treatedBaseQVLoading index (treatedScore index treated) =
          treatedCoefficient index treated ^ 2 *
            treatedVariance index treated)
    (hcontrolQVLoading :
      ∀ index control, control ∈ controlSample index ->
        controlQVScale index *
            controlBaseQVLoading index (controlScore index control) =
          controlCoefficient index control ^ 2 *
            controlVariance index control)
    (htreatedBaseQV :
      ∀ cell, cell ∈ treatedCells ->
        Tendsto
          (fun index => treatedBaseQVLoading index cell)
          l (nhds (treatedBaseQVLimit cell)))
    (hcontrolBaseQV :
      ∀ cell, cell ∈ controlCells ->
        Tendsto
          (fun index => controlBaseQVLoading index cell)
          l (nhds (controlBaseQVLimit cell)))
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
    twoArmResidualLindebergCondition_of_scaled_scoreCellLoading_tendsto_base_and_thirdMoments
      treatedCells controlCells treatedSample controlSample
      treatedWeight treatedCoefficient treatedResidual
      controlWeight controlCoefficient controlResidual
      treatedScore controlScore treatedCoeffScale controlCoeffScale
      treatedBaseCoeffLoading controlBaseCoeffLoading treatedBaseCoeffLimit
      controlBaseCoeffLimit treatedThirdMomentLoading treatedMassLimit
      controlThirdMomentLoading controlMassLimit htreatedCoeffScale
      hcontrolCoeffScale htreatedWeightNonneg hcontrolWeightNonneg
      htreatedCoverEventually hcontrolCoverEventually htreatedCover
      hcontrolCover htreatedCoefficient hcontrolCoefficient
      htreatedBaseCoeff hcontrolBaseCoeff htreatedThirdLoading
      hcontrolThirdLoading htreatedMass hcontrolMass
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
              (fun cell => treatedQVScaleLimit * treatedBaseQVLimit cell)
              treatedMassLimit +
            weightedScoreCellMomentLimit controlCells
              (fun cell => controlQVScaleLimit * controlBaseQVLimit cell)
              controlMassLimit)) :=
    tendsto_twoArm_weightedQuadraticVariation_of_scaled_loading_cellwiseScoreCellMassLLN_hetero
      treatedCells controlCells treatedSample controlSample treatedWeight
      controlWeight treatedScore controlScore treatedCoefficient
      treatedVariance controlCoefficient controlVariance treatedQVScale
      controlQVScale treatedBaseQVLoading controlBaseQVLoading
      treatedQVScaleLimit controlQVScaleLimit treatedBaseQVLimit
      treatedMassLimit controlBaseQVLimit controlMassLimit htreatedCover
      hcontrolCover htreatedQVLoading hcontrolQVLoading htreatedQVScale
      hcontrolQVScale htreatedBaseQV hcontrolBaseQV htreatedMass
      hcontrolMass
  exact
    residual_clt_and_variance_formula_of_martingale_array_input input
      hexact hregularity hmartingale (hinputLindeberg hlindeberg)
      (hinputQV hqv)

end WDSM
end Matching
end StatInference
