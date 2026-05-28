import StatInference.Matching.WDSM.DiscreteDoubleScoreSurveyZeroError
import StatInference.Matching.WDSM.ExactZeroLimitAlgebra

/-!
# Limit consequences of double-score survey zero-error identification

The finite double-score survey zero-error theorems show exact equality between
target contrasts and selected-sample inverse-weighted contrasts.  This module
lifts those equalities to deterministic asymptotic remainders: after arbitrary
deterministic scaling, the target-minus-selected survey contrast tends to zero.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter

variable {Index Unit PropensityCell TreatedProgCell ControlProgCell PATTProgCell :
  Type*}
variable [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
  [DecidableEq ControlProgCell] [DecidableEq PATTProgCell]
variable {l : Filter Index}

/--
Retrospective selected-sample PATE double-score survey identification gives a
scaled negligible target-minus-selected contrast.
-/
theorem tendsto_scaled_retrospectivePATEDoubleScoreWeight_error_zero
    (scale : Index -> Real)
    (targetSample selectedSample : Index -> Finset Unit)
    (cells :
      Index -> Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (baseWeight : Index -> Unit -> Real)
    (targetOutcomeT targetOutcomeC selectedOutcomeT selectedOutcomeC :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (treatment : Index -> Unit -> Prop)
    [∀ index, DecidablePred (treatment index)]
    (samplingIfTreated samplingIfControl :
      Index -> (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (treatedValue : Index -> TreatedProgCell -> Real)
    (controlValue : Index -> ControlProgCell -> Real)
    (hcoverTarget :
      ∀ index unit, unit ∈ targetSample index ->
        pateDoubleScore (propensityScore index) (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells index)
    (hcoverSelected :
      ∀ index unit, unit ∈ selectedSample index ->
        pateDoubleScore (propensityScore index) (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells index)
    (hmassTarget :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (targetSample index) (baseWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index) (controlPrognosticScore index))
          cell ≠ 0)
    (hsamplingTreated :
      ∀ index cell, cell ∈ cells index -> samplingIfTreated index cell ≠ 0)
    (hsamplingControl :
      ∀ index cell, cell ∈ cells index -> samplingIfControl index cell ≠ 0)
    (htreatedMass :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass ((selectedSample index).filter (treatment index))
            (baseWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index) (controlPrognosticScore index))
            cell =
          samplingIfTreated index cell *
            scoreCellMass ((targetSample index).filter (treatment index))
              (baseWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index) (controlPrognosticScore index))
              cell)
    (hcontrolMass :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass
            ((selectedSample index).filter
              (fun unit => ¬ treatment index unit))
            (baseWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index) (controlPrognosticScore index))
            cell =
          samplingIfControl index cell *
            scoreCellMass
              ((targetSample index).filter
                (fun unit => ¬ treatment index unit))
              (baseWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index) (controlPrognosticScore index))
              cell)
    (hscoreMeasTargetT :
      ∀ index unit, unit ∈ targetSample index ->
        targetOutcomeT index unit =
          treatedValue index (treatedPrognosticScore index unit))
    (hscoreMeasSelectedT :
      ∀ index unit, unit ∈ selectedSample index ->
        selectedOutcomeT index unit =
          treatedValue index (treatedPrognosticScore index unit))
    (hscoreMeasTargetC :
      ∀ index unit, unit ∈ targetSample index ->
        targetOutcomeC index unit =
          controlValue index (controlPrognosticScore index unit))
    (hscoreMeasSelectedC :
      ∀ index unit, unit ∈ selectedSample index ->
        selectedOutcomeC index unit =
          controlValue index (controlPrognosticScore index unit)) :
    Tendsto
      (fun index =>
        scale index *
          (weightedSampleMeanContrast (targetSample index)
            (baseWeight index) (targetOutcomeT index)
            (targetOutcomeC index) -
          weightedSampleMeanContrast (selectedSample index)
            (retrospectiveInverseSamplingWeight (baseWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index))
              (treatment index) (samplingIfTreated index)
              (samplingIfControl index))
            (selectedOutcomeT index) (selectedOutcomeC index)))
      l (nhds 0) := by
  exact tendsto_scaled_zero_of_abs_eq_zero scale
    (fun index =>
      weightedSampleMeanContrast (targetSample index) (baseWeight index)
          (targetOutcomeT index) (targetOutcomeC index) -
        weightedSampleMeanContrast (selectedSample index)
          (retrospectiveInverseSamplingWeight (baseWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index) (controlPrognosticScore index))
            (treatment index) (samplingIfTreated index)
            (samplingIfControl index))
          (selectedOutcomeT index) (selectedOutcomeC index))
    (fun index =>
      abs_target_sub_retrospectivePATEDoubleScoreWeight_eq_zero
        (targetSample index) (selectedSample index) (cells index)
        (baseWeight index) (targetOutcomeT index) (targetOutcomeC index)
        (selectedOutcomeT index) (selectedOutcomeC index)
        (propensityScore index) (treatedPrognosticScore index)
        (controlPrognosticScore index) (treatment index)
        (samplingIfTreated index) (samplingIfControl index)
        (treatedValue index) (controlValue index) (hcoverTarget index)
        (hcoverSelected index) (hmassTarget index) (hsamplingTreated index)
        (hsamplingControl index) (htreatedMass index) (hcontrolMass index)
        (hscoreMeasTargetT index) (hscoreMeasSelectedT index)
        (hscoreMeasTargetC index) (hscoreMeasSelectedC index))

/--
Prospective selected-sample PATE double-score survey identification gives a
scaled negligible target-minus-selected contrast.
-/
theorem tendsto_scaled_prospectivePATEDoubleScoreWeight_error_zero
    (scale : Index -> Real)
    (targetSample selectedSample : Index -> Finset Unit)
    (cells :
      Index -> Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (baseWeight : Index -> Unit -> Real)
    (targetOutcomeT targetOutcomeC selectedOutcomeT selectedOutcomeC :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Unit -> ControlProgCell)
    (treatment : Index -> Unit -> Prop)
    [∀ index, DecidablePred (treatment index)]
    (samplingMass :
      Index -> (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (treatedValue : Index -> TreatedProgCell -> Real)
    (controlValue : Index -> ControlProgCell -> Real)
    (hcoverTarget :
      ∀ index unit, unit ∈ targetSample index ->
        pateDoubleScore (propensityScore index) (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells index)
    (hcoverSelected :
      ∀ index unit, unit ∈ selectedSample index ->
        pateDoubleScore (propensityScore index) (treatedPrognosticScore index)
          (controlPrognosticScore index) unit ∈ cells index)
    (hmassTarget :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (targetSample index) (baseWeight index)
          (pateDoubleScore (propensityScore index)
            (treatedPrognosticScore index) (controlPrognosticScore index))
          cell ≠ 0)
    (hsampling :
      ∀ index cell, cell ∈ cells index -> samplingMass index cell ≠ 0)
    (htreatedMass :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass ((selectedSample index).filter (treatment index))
            (baseWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index) (controlPrognosticScore index))
            cell =
          samplingMass index cell *
            scoreCellMass ((targetSample index).filter (treatment index))
              (baseWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index) (controlPrognosticScore index))
              cell)
    (hcontrolMass :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass
            ((selectedSample index).filter
              (fun unit => ¬ treatment index unit))
            (baseWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index) (controlPrognosticScore index))
            cell =
          samplingMass index cell *
            scoreCellMass
              ((targetSample index).filter
                (fun unit => ¬ treatment index unit))
              (baseWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index) (controlPrognosticScore index))
              cell)
    (hscoreMeasTargetT :
      ∀ index unit, unit ∈ targetSample index ->
        targetOutcomeT index unit =
          treatedValue index (treatedPrognosticScore index unit))
    (hscoreMeasSelectedT :
      ∀ index unit, unit ∈ selectedSample index ->
        selectedOutcomeT index unit =
          treatedValue index (treatedPrognosticScore index unit))
    (hscoreMeasTargetC :
      ∀ index unit, unit ∈ targetSample index ->
        targetOutcomeC index unit =
          controlValue index (controlPrognosticScore index unit))
    (hscoreMeasSelectedC :
      ∀ index unit, unit ∈ selectedSample index ->
        selectedOutcomeC index unit =
          controlValue index (controlPrognosticScore index unit)) :
    Tendsto
      (fun index =>
        scale index *
          (weightedSampleMeanContrast (targetSample index)
            (baseWeight index) (targetOutcomeT index)
            (targetOutcomeC index) -
          weightedSampleMeanContrast (selectedSample index)
            (prospectiveInverseSamplingWeight (baseWeight index)
              (pateDoubleScore (propensityScore index)
                (treatedPrognosticScore index)
                (controlPrognosticScore index))
              (samplingMass index))
            (selectedOutcomeT index) (selectedOutcomeC index)))
      l (nhds 0) := by
  exact tendsto_scaled_zero_of_abs_eq_zero scale
    (fun index =>
      weightedSampleMeanContrast (targetSample index) (baseWeight index)
          (targetOutcomeT index) (targetOutcomeC index) -
        weightedSampleMeanContrast (selectedSample index)
          (prospectiveInverseSamplingWeight (baseWeight index)
            (pateDoubleScore (propensityScore index)
              (treatedPrognosticScore index) (controlPrognosticScore index))
            (samplingMass index))
          (selectedOutcomeT index) (selectedOutcomeC index))
    (fun index =>
      abs_target_sub_prospectivePATEDoubleScoreWeight_eq_zero
        (targetSample index) (selectedSample index) (cells index)
        (baseWeight index) (targetOutcomeT index) (targetOutcomeC index)
        (selectedOutcomeT index) (selectedOutcomeC index)
        (propensityScore index) (treatedPrognosticScore index)
        (controlPrognosticScore index) (treatment index)
        (samplingMass index) (treatedValue index) (controlValue index)
        (hcoverTarget index) (hcoverSelected index) (hmassTarget index)
        (hsampling index) (htreatedMass index) (hcontrolMass index)
        (hscoreMeasTargetT index) (hscoreMeasSelectedT index)
        (hscoreMeasTargetC index) (hscoreMeasSelectedC index))

/--
Retrospective selected-sample PATT double-score survey identification gives a
scaled negligible target-minus-selected contrast.
-/
theorem tendsto_scaled_retrospectivePATTDoubleScoreWeight_error_zero
    (scale : Index -> Real)
    (targetSample selectedSample : Index -> Finset Unit)
    (cells : Index -> Finset (PropensityCell × PATTProgCell))
    (baseWeight : Index -> Unit -> Real)
    (treatedTargetOutcome targetControlOutcome selectedControlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (treatment : Index -> Unit -> Prop)
    [∀ index, DecidablePred (treatment index)]
    (samplingIfTreated samplingIfControl :
      Index -> PropensityCell × PATTProgCell -> Real)
    (treatedCellValue : Index -> PropensityCell × PATTProgCell -> Real)
    (controlValue : Index -> PATTProgCell -> Real)
    (hcoverTarget :
      ∀ index unit, unit ∈ targetSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells index)
    (hcoverSelected :
      ∀ index unit, unit ∈ selectedSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells index)
    (hmassTarget :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (targetSample index) (baseWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hsamplingTreated :
      ∀ index cell, cell ∈ cells index -> samplingIfTreated index cell ≠ 0)
    (hsamplingControl :
      ∀ index cell, cell ∈ cells index -> samplingIfControl index cell ≠ 0)
    (htreatedMass :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass ((selectedSample index).filter (treatment index))
            (baseWeight index)
            (pattDoubleScore (propensityScore index)
              (controlPrognosticScore index)) cell =
          samplingIfTreated index cell *
            scoreCellMass ((targetSample index).filter (treatment index))
              (baseWeight index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell)
    (hcontrolMass :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass
            ((selectedSample index).filter
              (fun unit => ¬ treatment index unit))
            (baseWeight index)
            (pattDoubleScore (propensityScore index)
              (controlPrognosticScore index)) cell =
          samplingIfControl index cell *
            scoreCellMass
              ((targetSample index).filter
                (fun unit => ¬ treatment index unit))
              (baseWeight index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell)
    (hscoreMeasTargetT :
      ∀ index unit, unit ∈ targetSample index ->
        treatedTargetOutcome index unit =
          treatedCellValue index
            (pattDoubleScore (propensityScore index)
              (controlPrognosticScore index) unit))
    (hscoreMeasTargetC :
      ∀ index unit, unit ∈ targetSample index ->
        targetControlOutcome index unit =
          controlValue index (controlPrognosticScore index unit))
    (hscoreMeasSelectedC :
      ∀ index unit, unit ∈ selectedSample index ->
        selectedControlOutcome index unit =
          controlValue index (controlPrognosticScore index unit)) :
    Tendsto
      (fun index =>
        scale index *
          (weightedSampleMeanContrast (targetSample index)
            (baseWeight index) (treatedTargetOutcome index)
            (targetControlOutcome index) -
          pattWeightedMeanContrast (targetSample index)
            (selectedSample index) (baseWeight index)
            (retrospectiveInverseSamplingWeight (baseWeight index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index))
              (treatment index) (samplingIfTreated index)
              (samplingIfControl index))
            (treatedTargetOutcome index) (selectedControlOutcome index)))
      l (nhds 0) := by
  exact tendsto_scaled_zero_of_abs_eq_zero scale
    (fun index =>
      weightedSampleMeanContrast (targetSample index) (baseWeight index)
          (treatedTargetOutcome index) (targetControlOutcome index) -
        pattWeightedMeanContrast (targetSample index) (selectedSample index)
          (baseWeight index)
          (retrospectiveInverseSamplingWeight (baseWeight index)
            (pattDoubleScore (propensityScore index)
              (controlPrognosticScore index))
            (treatment index) (samplingIfTreated index)
            (samplingIfControl index))
          (treatedTargetOutcome index) (selectedControlOutcome index))
    (fun index =>
      abs_target_sub_retrospectivePATTDoubleScoreWeight_eq_zero
        (targetSample index) (selectedSample index) (cells index)
        (baseWeight index) (treatedTargetOutcome index)
        (targetControlOutcome index) (selectedControlOutcome index)
        (propensityScore index) (controlPrognosticScore index)
        (treatment index) (samplingIfTreated index)
        (samplingIfControl index) (treatedCellValue index)
        (controlValue index) (hcoverTarget index) (hcoverSelected index)
        (hmassTarget index) (hsamplingTreated index)
        (hsamplingControl index) (htreatedMass index) (hcontrolMass index)
        (hscoreMeasTargetT index) (hscoreMeasTargetC index)
        (hscoreMeasSelectedC index))

/--
Prospective selected-sample PATT double-score survey identification gives a
scaled negligible target-minus-selected contrast.
-/
theorem tendsto_scaled_prospectivePATTDoubleScoreWeight_error_zero
    (scale : Index -> Real)
    (targetSample selectedSample : Index -> Finset Unit)
    (cells : Index -> Finset (PropensityCell × PATTProgCell))
    (baseWeight : Index -> Unit -> Real)
    (treatedTargetOutcome targetControlOutcome selectedControlOutcome :
      Index -> Unit -> Real)
    (propensityScore : Index -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Unit -> PATTProgCell)
    (treatment : Index -> Unit -> Prop)
    [∀ index, DecidablePred (treatment index)]
    (samplingMass : Index -> PropensityCell × PATTProgCell -> Real)
    (treatedCellValue : Index -> PropensityCell × PATTProgCell -> Real)
    (controlValue : Index -> PATTProgCell -> Real)
    (hcoverTarget :
      ∀ index unit, unit ∈ targetSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells index)
    (hcoverSelected :
      ∀ index unit, unit ∈ selectedSample index ->
        pattDoubleScore (propensityScore index)
          (controlPrognosticScore index) unit ∈ cells index)
    (hmassTarget :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass (targetSample index) (baseWeight index)
          (pattDoubleScore (propensityScore index)
            (controlPrognosticScore index)) cell ≠ 0)
    (hsampling :
      ∀ index cell, cell ∈ cells index -> samplingMass index cell ≠ 0)
    (htreatedMass :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass ((selectedSample index).filter (treatment index))
            (baseWeight index)
            (pattDoubleScore (propensityScore index)
              (controlPrognosticScore index)) cell =
          samplingMass index cell *
            scoreCellMass ((targetSample index).filter (treatment index))
              (baseWeight index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell)
    (hcontrolMass :
      ∀ index cell, cell ∈ cells index ->
        scoreCellMass
            ((selectedSample index).filter
              (fun unit => ¬ treatment index unit))
            (baseWeight index)
            (pattDoubleScore (propensityScore index)
              (controlPrognosticScore index)) cell =
          samplingMass index cell *
            scoreCellMass
              ((targetSample index).filter
                (fun unit => ¬ treatment index unit))
              (baseWeight index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index)) cell)
    (hscoreMeasTargetT :
      ∀ index unit, unit ∈ targetSample index ->
        treatedTargetOutcome index unit =
          treatedCellValue index
            (pattDoubleScore (propensityScore index)
              (controlPrognosticScore index) unit))
    (hscoreMeasTargetC :
      ∀ index unit, unit ∈ targetSample index ->
        targetControlOutcome index unit =
          controlValue index (controlPrognosticScore index unit))
    (hscoreMeasSelectedC :
      ∀ index unit, unit ∈ selectedSample index ->
        selectedControlOutcome index unit =
          controlValue index (controlPrognosticScore index unit)) :
    Tendsto
      (fun index =>
        scale index *
          (weightedSampleMeanContrast (targetSample index)
            (baseWeight index) (treatedTargetOutcome index)
            (targetControlOutcome index) -
          pattWeightedMeanContrast (targetSample index)
            (selectedSample index) (baseWeight index)
            (prospectiveInverseSamplingWeight (baseWeight index)
              (pattDoubleScore (propensityScore index)
                (controlPrognosticScore index))
              (samplingMass index))
            (treatedTargetOutcome index) (selectedControlOutcome index)))
      l (nhds 0) := by
  exact tendsto_scaled_zero_of_abs_eq_zero scale
    (fun index =>
      weightedSampleMeanContrast (targetSample index) (baseWeight index)
          (treatedTargetOutcome index) (targetControlOutcome index) -
        pattWeightedMeanContrast (targetSample index) (selectedSample index)
          (baseWeight index)
          (prospectiveInverseSamplingWeight (baseWeight index)
            (pattDoubleScore (propensityScore index)
              (controlPrognosticScore index))
            (samplingMass index))
          (treatedTargetOutcome index) (selectedControlOutcome index))
    (fun index =>
      abs_target_sub_prospectivePATTDoubleScoreWeight_eq_zero
        (targetSample index) (selectedSample index) (cells index)
        (baseWeight index) (treatedTargetOutcome index)
        (targetControlOutcome index) (selectedControlOutcome index)
        (propensityScore index) (controlPrognosticScore index)
        (treatment index) (samplingMass index) (treatedCellValue index)
        (controlValue index) (hcoverTarget index) (hcoverSelected index)
        (hmassTarget index) (hsampling index) (htreatedMass index)
        (hcontrolMass index) (hscoreMeasTargetT index)
        (hscoreMeasTargetC index) (hscoreMeasSelectedC index))

end WDSM
end Matching
end StatInference
