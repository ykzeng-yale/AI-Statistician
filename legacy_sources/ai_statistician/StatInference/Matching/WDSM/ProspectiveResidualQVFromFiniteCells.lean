import StatInference.Matching.WDSM.FiniteCellQuadraticVariationConvergence
import StatInference.Matching.WDSM.ProspectiveResidualQVStabilization

/-!
# Prospective residual-QV stabilization from finite score cells

This module composes two checked deterministic layers:

1. finite score-cell mass convergence gives arm-level quadratic-variation
   convergence when `coefficient^2 * variance` is score-cell measurable;
2. arm-level quadratic-variation convergence gives the prospective PATE/PATT
   residual quadratic-variation limits used in the appendix.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Treated Control TreatedCell ControlCell : Type*}
  {l : Filter Index} [DecidableEq TreatedCell] [DecidableEq ControlCell]

/--
Prospective PATE residual quadratic-variation stabilization from treated and
control finite score-cell mass convergence.
-/
theorem tendsto_prospectivePATEResidualQuadraticVariation_of_cellwiseScoreCellMassLLN_counting
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSet : Index -> Finset Treated)
    (controlSet : Index -> Finset Control)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficient treatedVariance : Index -> Treated -> Real)
    (controlCoefficient controlVariance : Index -> Control -> Real)
    (treatedLoading treatedMassLimit : TreatedCell -> Real)
    (controlLoading controlMassLimit : ControlCell -> Real)
    (denominator normalizer : Index -> Real)
    (denominatorLimit normalizerLimit : Real)
    (htreatedCover :
      ∀ index unit, unit ∈ treatedSet index ->
        treatedScore index unit ∈ treatedCells)
    (hcontrolCover :
      ∀ index unit, unit ∈ controlSet index ->
        controlScore index unit ∈ controlCells)
    (htreatedLoading :
      ∀ index unit, unit ∈ treatedSet index ->
        treatedLoading (treatedScore index unit) =
          treatedCoefficient index unit ^ 2 * treatedVariance index unit)
    (hcontrolLoading :
      ∀ index unit, unit ∈ controlSet index ->
        controlLoading (controlScore index unit) =
          controlCoefficient index unit ^ 2 * controlVariance index unit)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSet
        (fun _index _unit => 1) treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSet
        (fun _index _unit => 1) controlScore controlMassLimit)
    (hdenominator : Tendsto denominator l (nhds denominatorLimit))
    (hnormalizer : Tendsto normalizer l (nhds normalizerLimit))
    (hdenominatorLimit : denominatorLimit ≠ 0) :
    Tendsto
      (fun index =>
        prospectivePATEResidualQuadraticVariation (treatedSet index)
          (controlSet index) (treatedCoefficient index)
          (treatedVariance index) (controlCoefficient index)
          (controlVariance index) (denominator index) (normalizer index))
      l
      (nhds
        (normalizerLimit *
          ((weightedScoreCellMomentLimit treatedCells treatedLoading
                treatedMassLimit +
              weightedScoreCellMomentLimit controlCells controlLoading
                controlMassLimit) /
            denominatorLimit ^ 2))) := by
  have htreatedQV :
      Tendsto
        (fun index =>
          quadraticVariation (treatedSet index)
            (treatedCoefficient index) (treatedVariance index))
        l
        (nhds
          (weightedScoreCellMomentLimit treatedCells treatedLoading
            treatedMassLimit)) :=
    tendsto_quadraticVariation_of_cellwiseScoreCellMassLLN_counting
      treatedCells treatedSet treatedScore treatedCoefficient
      treatedVariance treatedLoading treatedMassLimit
      htreatedCover htreatedLoading htreatedMass
  have hcontrolQV :
      Tendsto
        (fun index =>
          quadraticVariation (controlSet index)
            (controlCoefficient index) (controlVariance index))
        l
        (nhds
          (weightedScoreCellMomentLimit controlCells controlLoading
            controlMassLimit)) :=
    tendsto_quadraticVariation_of_cellwiseScoreCellMassLLN_counting
      controlCells controlSet controlScore controlCoefficient
      controlVariance controlLoading controlMassLimit
      hcontrolCover hcontrolLoading hcontrolMass
  exact
    tendsto_prospectivePATEResidualQuadraticVariation_of_tendsto
      treatedSet controlSet treatedCoefficient treatedVariance
      controlCoefficient controlVariance denominator normalizer
      (weightedScoreCellMomentLimit treatedCells treatedLoading
        treatedMassLimit)
      (weightedScoreCellMomentLimit controlCells controlLoading
        controlMassLimit)
      denominatorLimit normalizerLimit htreatedQV hcontrolQV hdenominator
      hnormalizer hdenominatorLimit

/--
Prospective PATT residual quadratic-variation stabilization from treated and
one-sided control finite score-cell mass convergence.
-/
theorem tendsto_prospectivePATTResidualQuadraticVariation_of_cellwiseScoreCellMassLLN_counting
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSet : Index -> Finset Treated)
    (controlSet : Index -> Finset Control)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficient treatedVariance : Index -> Treated -> Real)
    (controlReuseCoefficient controlVariance : Index -> Control -> Real)
    (treatedLoading treatedMassLimit : TreatedCell -> Real)
    (controlLoading controlMassLimit : ControlCell -> Real)
    (denominator normalizer : Index -> Real)
    (denominatorLimit normalizerLimit : Real)
    (htreatedCover :
      ∀ index unit, unit ∈ treatedSet index ->
        treatedScore index unit ∈ treatedCells)
    (hcontrolCover :
      ∀ index unit, unit ∈ controlSet index ->
        controlScore index unit ∈ controlCells)
    (htreatedLoading :
      ∀ index unit, unit ∈ treatedSet index ->
        treatedLoading (treatedScore index unit) =
          treatedCoefficient index unit ^ 2 * treatedVariance index unit)
    (hcontrolLoading :
      ∀ index unit, unit ∈ controlSet index ->
        controlLoading (controlScore index unit) =
          controlReuseCoefficient index unit ^ 2 * controlVariance index unit)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSet
        (fun _index _unit => 1) treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSet
        (fun _index _unit => 1) controlScore controlMassLimit)
    (hdenominator : Tendsto denominator l (nhds denominatorLimit))
    (hnormalizer : Tendsto normalizer l (nhds normalizerLimit))
    (hdenominatorLimit : denominatorLimit ≠ 0) :
    Tendsto
      (fun index =>
        prospectivePATTResidualQuadraticVariation (treatedSet index)
          (controlSet index) (treatedCoefficient index)
          (treatedVariance index) (controlReuseCoefficient index)
          (controlVariance index) (denominator index) (normalizer index))
      l
      (nhds
        (normalizerLimit *
          ((weightedScoreCellMomentLimit treatedCells treatedLoading
                treatedMassLimit +
              weightedScoreCellMomentLimit controlCells controlLoading
                controlMassLimit) /
            denominatorLimit ^ 2))) := by
  have htreatedQV :
      Tendsto
        (fun index =>
          quadraticVariation (treatedSet index)
            (treatedCoefficient index) (treatedVariance index))
        l
        (nhds
          (weightedScoreCellMomentLimit treatedCells treatedLoading
            treatedMassLimit)) :=
    tendsto_quadraticVariation_of_cellwiseScoreCellMassLLN_counting
      treatedCells treatedSet treatedScore treatedCoefficient
      treatedVariance treatedLoading treatedMassLimit
      htreatedCover htreatedLoading htreatedMass
  have hcontrolQV :
      Tendsto
        (fun index =>
          quadraticVariation (controlSet index)
            (controlReuseCoefficient index) (controlVariance index))
        l
        (nhds
          (weightedScoreCellMomentLimit controlCells controlLoading
            controlMassLimit)) :=
    tendsto_quadraticVariation_of_cellwiseScoreCellMassLLN_counting
      controlCells controlSet controlScore controlReuseCoefficient
      controlVariance controlLoading controlMassLimit
      hcontrolCover hcontrolLoading hcontrolMass
  exact
    tendsto_prospectivePATTResidualQuadraticVariation_of_tendsto
      treatedSet controlSet treatedCoefficient treatedVariance
      controlReuseCoefficient controlVariance denominator normalizer
      (weightedScoreCellMomentLimit treatedCells treatedLoading
        treatedMassLimit)
      (weightedScoreCellMomentLimit controlCells controlLoading
        controlMassLimit)
      denominatorLimit normalizerLimit htreatedQV hcontrolQV hdenominator
      hnormalizer hdenominatorLimit

/--
Paired prospective PATE/PATT residual quadratic-variation stabilization from
the same treated finite-cell LLN and PATE/PATT-specific control loadings.
-/
theorem tendsto_prospectivePATE_PATTResidualQuadraticVariation_of_cellwiseScoreCellMassLLN_counting
    (treatedCells : Finset TreatedCell)
    (controlCells : Finset ControlCell)
    (treatedSet : Index -> Finset Treated)
    (controlSet : Index -> Finset Control)
    (treatedScore : Index -> Treated -> TreatedCell)
    (controlScore : Index -> Control -> ControlCell)
    (treatedCoefficient treatedVariance : Index -> Treated -> Real)
    (controlCoefficient controlReuseCoefficient controlVariance :
      Index -> Control -> Real)
    (treatedLoading treatedMassLimit : TreatedCell -> Real)
    (pateControlLoading pattControlLoading controlMassLimit :
      ControlCell -> Real)
    (denominator normalizer : Index -> Real)
    (denominatorLimit normalizerLimit : Real)
    (htreatedCover :
      ∀ index unit, unit ∈ treatedSet index ->
        treatedScore index unit ∈ treatedCells)
    (hcontrolCover :
      ∀ index unit, unit ∈ controlSet index ->
        controlScore index unit ∈ controlCells)
    (htreatedLoading :
      ∀ index unit, unit ∈ treatedSet index ->
        treatedLoading (treatedScore index unit) =
          treatedCoefficient index unit ^ 2 * treatedVariance index unit)
    (hpateControlLoading :
      ∀ index unit, unit ∈ controlSet index ->
        pateControlLoading (controlScore index unit) =
          controlCoefficient index unit ^ 2 * controlVariance index unit)
    (hpattControlLoading :
      ∀ index unit, unit ∈ controlSet index ->
        pattControlLoading (controlScore index unit) =
          controlReuseCoefficient index unit ^ 2 * controlVariance index unit)
    (htreatedMass :
      cellwiseScoreCellMassLLN (l := l) treatedCells treatedSet
        (fun _index _unit => 1) treatedScore treatedMassLimit)
    (hcontrolMass :
      cellwiseScoreCellMassLLN (l := l) controlCells controlSet
        (fun _index _unit => 1) controlScore controlMassLimit)
    (hdenominator : Tendsto denominator l (nhds denominatorLimit))
    (hnormalizer : Tendsto normalizer l (nhds normalizerLimit))
    (hdenominatorLimit : denominatorLimit ≠ 0) :
    Tendsto
      (fun index =>
        prospectivePATEResidualQuadraticVariation (treatedSet index)
          (controlSet index) (treatedCoefficient index)
          (treatedVariance index) (controlCoefficient index)
          (controlVariance index) (denominator index) (normalizer index))
      l
      (nhds
        (normalizerLimit *
          ((weightedScoreCellMomentLimit treatedCells treatedLoading
                treatedMassLimit +
              weightedScoreCellMomentLimit controlCells pateControlLoading
                controlMassLimit) /
            denominatorLimit ^ 2))) ∧
    Tendsto
      (fun index =>
        prospectivePATTResidualQuadraticVariation (treatedSet index)
          (controlSet index) (treatedCoefficient index)
          (treatedVariance index) (controlReuseCoefficient index)
          (controlVariance index) (denominator index) (normalizer index))
      l
      (nhds
        (normalizerLimit *
          ((weightedScoreCellMomentLimit treatedCells treatedLoading
                treatedMassLimit +
              weightedScoreCellMomentLimit controlCells pattControlLoading
                controlMassLimit) /
            denominatorLimit ^ 2))) := by
  constructor
  · exact
      tendsto_prospectivePATEResidualQuadraticVariation_of_cellwiseScoreCellMassLLN_counting
        treatedCells controlCells treatedSet controlSet treatedScore controlScore
        treatedCoefficient treatedVariance controlCoefficient controlVariance
        treatedLoading treatedMassLimit pateControlLoading controlMassLimit
        denominator normalizer denominatorLimit normalizerLimit
        htreatedCover hcontrolCover htreatedLoading hpateControlLoading
        htreatedMass hcontrolMass hdenominator hnormalizer hdenominatorLimit
  · exact
      tendsto_prospectivePATTResidualQuadraticVariation_of_cellwiseScoreCellMassLLN_counting
        treatedCells controlCells treatedSet controlSet treatedScore controlScore
        treatedCoefficient treatedVariance controlReuseCoefficient controlVariance
        treatedLoading treatedMassLimit pattControlLoading controlMassLimit
        denominator normalizer denominatorLimit normalizerLimit
        htreatedCover hcontrolCover htreatedLoading hpattControlLoading
        htreatedMass hcontrolMass hdenominator hnormalizer hdenominatorLimit

end WDSM
end Matching
end StatInference
