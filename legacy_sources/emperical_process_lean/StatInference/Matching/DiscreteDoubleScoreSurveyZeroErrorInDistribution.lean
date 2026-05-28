import StatInference.Matching.WDSM.DiscreteDoubleScoreSurveyZeroError
import StatInference.Matching.WDSM.ExactZeroInDistributionAlgebra

/-!
# Distributional zero-error consequences of double-score survey identification

This module packages exact finite double-score survey identification errors as
degenerate weak limits when the finite samples are random objects.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open scoped Topology

variable {Index Sample Unit PropensityCell TreatedProgCell ControlProgCell :
  Type*}
variable [MeasurableSpace Sample]
variable {sampleLaw : MeasureTheory.Measure Sample}
variable [MeasureTheory.IsProbabilityMeasure sampleLaw]
variable {l : Filter Index}
variable [l.IsCountablyGenerated]
variable [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
  [DecidableEq ControlProgCell]

/--
Random-sample retrospective PATE double-score survey identification gives a
scaled degenerate weak limit for the target-minus-selected contrast.
-/
theorem tendstoInDistribution_random_scaled_retrospectivePATEDoubleScoreWeight_error_zero
    (scale : Index -> Sample -> Real)
    (targetSample selectedSample : Index -> Sample -> Finset Unit)
    (cells :
      Index -> Sample ->
        Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (baseWeight : Index -> Sample -> Unit -> Real)
    (targetOutcomeT targetOutcomeC selectedOutcomeT selectedOutcomeC :
      Index -> Sample -> Unit -> Real)
    (propensityScore : Index -> Sample -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Sample -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Sample -> Unit -> ControlProgCell)
    (treatment : Index -> Sample -> Unit -> Prop)
    [∀ index sample, DecidablePred (treatment index sample)]
    (samplingIfTreated samplingIfControl :
      Index -> Sample ->
        (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (treatedValue : Index -> Sample -> TreatedProgCell -> Real)
    (controlValue : Index -> Sample -> ControlProgCell -> Real)
    (hcoverTarget :
      ∀ index sample unit, unit ∈ targetSample index sample ->
        pateDoubleScore (propensityScore index sample)
          (treatedPrognosticScore index sample)
          (controlPrognosticScore index sample) unit ∈ cells index sample)
    (hcoverSelected :
      ∀ index sample unit, unit ∈ selectedSample index sample ->
        pateDoubleScore (propensityScore index sample)
          (treatedPrognosticScore index sample)
          (controlPrognosticScore index sample) unit ∈ cells index sample)
    (hmassTarget :
      ∀ index sample cell, cell ∈ cells index sample ->
        scoreCellMass (targetSample index sample) (baseWeight index sample)
          (pateDoubleScore (propensityScore index sample)
            (treatedPrognosticScore index sample)
            (controlPrognosticScore index sample)) cell ≠ 0)
    (hsamplingTreated :
      ∀ index sample cell, cell ∈ cells index sample ->
        samplingIfTreated index sample cell ≠ 0)
    (hsamplingControl :
      ∀ index sample cell, cell ∈ cells index sample ->
        samplingIfControl index sample cell ≠ 0)
    (htreatedMass :
      ∀ index sample cell, cell ∈ cells index sample ->
        scoreCellMass
            ((selectedSample index sample).filter (treatment index sample))
            (baseWeight index sample)
            (pateDoubleScore (propensityScore index sample)
              (treatedPrognosticScore index sample)
              (controlPrognosticScore index sample)) cell =
          samplingIfTreated index sample cell *
            scoreCellMass
              ((targetSample index sample).filter (treatment index sample))
              (baseWeight index sample)
              (pateDoubleScore (propensityScore index sample)
                (treatedPrognosticScore index sample)
                (controlPrognosticScore index sample)) cell)
    (hcontrolMass :
      ∀ index sample cell, cell ∈ cells index sample ->
        scoreCellMass
            ((selectedSample index sample).filter
              (fun unit => ¬ treatment index sample unit))
            (baseWeight index sample)
            (pateDoubleScore (propensityScore index sample)
              (treatedPrognosticScore index sample)
              (controlPrognosticScore index sample)) cell =
          samplingIfControl index sample cell *
            scoreCellMass
              ((targetSample index sample).filter
                (fun unit => ¬ treatment index sample unit))
              (baseWeight index sample)
              (pateDoubleScore (propensityScore index sample)
                (treatedPrognosticScore index sample)
                (controlPrognosticScore index sample)) cell)
    (hscoreMeasTargetT :
      ∀ index sample unit, unit ∈ targetSample index sample ->
        targetOutcomeT index sample unit =
          treatedValue index sample
            (treatedPrognosticScore index sample unit))
    (hscoreMeasSelectedT :
      ∀ index sample unit, unit ∈ selectedSample index sample ->
        selectedOutcomeT index sample unit =
          treatedValue index sample
            (treatedPrognosticScore index sample unit))
    (hscoreMeasTargetC :
      ∀ index sample unit, unit ∈ targetSample index sample ->
        targetOutcomeC index sample unit =
          controlValue index sample
            (controlPrognosticScore index sample unit))
    (hscoreMeasSelectedC :
      ∀ index sample unit, unit ∈ selectedSample index sample ->
        selectedOutcomeC index sample unit =
          controlValue index sample
            (controlPrognosticScore index sample unit)) :
    TendstoInDistribution
      (fun index sample =>
        scale index sample *
          (weightedSampleMeanContrast (targetSample index sample)
            (baseWeight index sample) (targetOutcomeT index sample)
            (targetOutcomeC index sample) -
          weightedSampleMeanContrast (selectedSample index sample)
            (retrospectiveInverseSamplingWeight (baseWeight index sample)
              (pateDoubleScore (propensityScore index sample)
                (treatedPrognosticScore index sample)
                (controlPrognosticScore index sample))
              (treatment index sample) (samplingIfTreated index sample)
              (samplingIfControl index sample))
            (selectedOutcomeT index sample) (selectedOutcomeC index sample)))
      l (fun _sample => (0 : Real)) (fun _index => sampleLaw)
      sampleLaw := by
  exact tendstoInDistribution_zero_of_forall_eq_zero
    (sampleLaw := sampleLaw) (l := l)
    (fun index sample =>
      scale index sample *
        (weightedSampleMeanContrast (targetSample index sample)
          (baseWeight index sample) (targetOutcomeT index sample)
          (targetOutcomeC index sample) -
        weightedSampleMeanContrast (selectedSample index sample)
          (retrospectiveInverseSamplingWeight (baseWeight index sample)
            (pateDoubleScore (propensityScore index sample)
              (treatedPrognosticScore index sample)
              (controlPrognosticScore index sample))
            (treatment index sample) (samplingIfTreated index sample)
            (samplingIfControl index sample))
          (selectedOutcomeT index sample) (selectedOutcomeC index sample)))
    (fun index sample => by
      have hzero :=
        abs_eq_zero.mp
          (abs_target_sub_retrospectivePATEDoubleScoreWeight_eq_zero
            (targetSample index sample) (selectedSample index sample)
            (cells index sample) (baseWeight index sample)
            (targetOutcomeT index sample) (targetOutcomeC index sample)
            (selectedOutcomeT index sample) (selectedOutcomeC index sample)
            (propensityScore index sample)
            (treatedPrognosticScore index sample)
            (controlPrognosticScore index sample) (treatment index sample)
            (samplingIfTreated index sample) (samplingIfControl index sample)
            (treatedValue index sample) (controlValue index sample)
            (hcoverTarget index sample) (hcoverSelected index sample)
            (hmassTarget index sample) (hsamplingTreated index sample)
            (hsamplingControl index sample) (htreatedMass index sample)
            (hcontrolMass index sample) (hscoreMeasTargetT index sample)
            (hscoreMeasSelectedT index sample)
            (hscoreMeasTargetC index sample)
            (hscoreMeasSelectedC index sample))
      change scale index sample *
          (weightedSampleMeanContrast (targetSample index sample)
            (baseWeight index sample) (targetOutcomeT index sample)
            (targetOutcomeC index sample) -
          weightedSampleMeanContrast (selectedSample index sample)
            (retrospectiveInverseSamplingWeight (baseWeight index sample)
              (pateDoubleScore (propensityScore index sample)
                (treatedPrognosticScore index sample)
                (controlPrognosticScore index sample))
              (treatment index sample) (samplingIfTreated index sample)
              (samplingIfControl index sample))
            (selectedOutcomeT index sample) (selectedOutcomeC index sample)) =
        0
      rw [hzero, mul_zero])

/--
Random-sample prospective PATE double-score survey identification gives a
scaled degenerate weak limit for the target-minus-selected contrast.
-/
theorem tendstoInDistribution_random_scaled_prospectivePATEDoubleScoreWeight_error_zero
    (scale : Index -> Sample -> Real)
    (targetSample selectedSample : Index -> Sample -> Finset Unit)
    (cells :
      Index -> Sample ->
        Finset ((PropensityCell × TreatedProgCell) × ControlProgCell))
    (baseWeight : Index -> Sample -> Unit -> Real)
    (targetOutcomeT targetOutcomeC selectedOutcomeT selectedOutcomeC :
      Index -> Sample -> Unit -> Real)
    (propensityScore : Index -> Sample -> Unit -> PropensityCell)
    (treatedPrognosticScore : Index -> Sample -> Unit -> TreatedProgCell)
    (controlPrognosticScore : Index -> Sample -> Unit -> ControlProgCell)
    (treatment : Index -> Sample -> Unit -> Prop)
    [∀ index sample, DecidablePred (treatment index sample)]
    (samplingMass :
      Index -> Sample ->
        (PropensityCell × TreatedProgCell) × ControlProgCell -> Real)
    (treatedValue : Index -> Sample -> TreatedProgCell -> Real)
    (controlValue : Index -> Sample -> ControlProgCell -> Real)
    (hcoverTarget :
      ∀ index sample unit, unit ∈ targetSample index sample ->
        pateDoubleScore (propensityScore index sample)
          (treatedPrognosticScore index sample)
          (controlPrognosticScore index sample) unit ∈ cells index sample)
    (hcoverSelected :
      ∀ index sample unit, unit ∈ selectedSample index sample ->
        pateDoubleScore (propensityScore index sample)
          (treatedPrognosticScore index sample)
          (controlPrognosticScore index sample) unit ∈ cells index sample)
    (hmassTarget :
      ∀ index sample cell, cell ∈ cells index sample ->
        scoreCellMass (targetSample index sample) (baseWeight index sample)
          (pateDoubleScore (propensityScore index sample)
            (treatedPrognosticScore index sample)
            (controlPrognosticScore index sample)) cell ≠ 0)
    (hsampling :
      ∀ index sample cell, cell ∈ cells index sample ->
        samplingMass index sample cell ≠ 0)
    (htreatedMass :
      ∀ index sample cell, cell ∈ cells index sample ->
        scoreCellMass
            ((selectedSample index sample).filter (treatment index sample))
            (baseWeight index sample)
            (pateDoubleScore (propensityScore index sample)
              (treatedPrognosticScore index sample)
              (controlPrognosticScore index sample)) cell =
          samplingMass index sample cell *
            scoreCellMass
              ((targetSample index sample).filter (treatment index sample))
              (baseWeight index sample)
              (pateDoubleScore (propensityScore index sample)
                (treatedPrognosticScore index sample)
                (controlPrognosticScore index sample)) cell)
    (hcontrolMass :
      ∀ index sample cell, cell ∈ cells index sample ->
        scoreCellMass
            ((selectedSample index sample).filter
              (fun unit => ¬ treatment index sample unit))
            (baseWeight index sample)
            (pateDoubleScore (propensityScore index sample)
              (treatedPrognosticScore index sample)
              (controlPrognosticScore index sample)) cell =
          samplingMass index sample cell *
            scoreCellMass
              ((targetSample index sample).filter
                (fun unit => ¬ treatment index sample unit))
              (baseWeight index sample)
              (pateDoubleScore (propensityScore index sample)
                (treatedPrognosticScore index sample)
                (controlPrognosticScore index sample)) cell)
    (hscoreMeasTargetT :
      ∀ index sample unit, unit ∈ targetSample index sample ->
        targetOutcomeT index sample unit =
          treatedValue index sample
            (treatedPrognosticScore index sample unit))
    (hscoreMeasSelectedT :
      ∀ index sample unit, unit ∈ selectedSample index sample ->
        selectedOutcomeT index sample unit =
          treatedValue index sample
            (treatedPrognosticScore index sample unit))
    (hscoreMeasTargetC :
      ∀ index sample unit, unit ∈ targetSample index sample ->
        targetOutcomeC index sample unit =
          controlValue index sample
            (controlPrognosticScore index sample unit))
    (hscoreMeasSelectedC :
      ∀ index sample unit, unit ∈ selectedSample index sample ->
        selectedOutcomeC index sample unit =
          controlValue index sample
            (controlPrognosticScore index sample unit)) :
    TendstoInDistribution
      (fun index sample =>
        scale index sample *
          (weightedSampleMeanContrast (targetSample index sample)
            (baseWeight index sample) (targetOutcomeT index sample)
            (targetOutcomeC index sample) -
          weightedSampleMeanContrast (selectedSample index sample)
            (prospectiveInverseSamplingWeight (baseWeight index sample)
              (pateDoubleScore (propensityScore index sample)
                (treatedPrognosticScore index sample)
                (controlPrognosticScore index sample))
              (samplingMass index sample))
            (selectedOutcomeT index sample) (selectedOutcomeC index sample)))
      l (fun _sample => (0 : Real)) (fun _index => sampleLaw)
      sampleLaw := by
  exact tendstoInDistribution_zero_of_forall_eq_zero
    (sampleLaw := sampleLaw) (l := l)
    (fun index sample =>
      scale index sample *
        (weightedSampleMeanContrast (targetSample index sample)
          (baseWeight index sample) (targetOutcomeT index sample)
          (targetOutcomeC index sample) -
        weightedSampleMeanContrast (selectedSample index sample)
          (prospectiveInverseSamplingWeight (baseWeight index sample)
            (pateDoubleScore (propensityScore index sample)
              (treatedPrognosticScore index sample)
              (controlPrognosticScore index sample))
            (samplingMass index sample))
          (selectedOutcomeT index sample) (selectedOutcomeC index sample)))
    (fun index sample => by
      have hzero :=
        abs_eq_zero.mp
          (abs_target_sub_prospectivePATEDoubleScoreWeight_eq_zero
            (targetSample index sample) (selectedSample index sample)
            (cells index sample) (baseWeight index sample)
            (targetOutcomeT index sample) (targetOutcomeC index sample)
            (selectedOutcomeT index sample) (selectedOutcomeC index sample)
            (propensityScore index sample)
            (treatedPrognosticScore index sample)
            (controlPrognosticScore index sample) (treatment index sample)
            (samplingMass index sample) (treatedValue index sample)
            (controlValue index sample) (hcoverTarget index sample)
            (hcoverSelected index sample) (hmassTarget index sample)
            (hsampling index sample) (htreatedMass index sample)
            (hcontrolMass index sample) (hscoreMeasTargetT index sample)
            (hscoreMeasSelectedT index sample)
            (hscoreMeasTargetC index sample)
            (hscoreMeasSelectedC index sample))
      change scale index sample *
          (weightedSampleMeanContrast (targetSample index sample)
            (baseWeight index sample) (targetOutcomeT index sample)
            (targetOutcomeC index sample) -
          weightedSampleMeanContrast (selectedSample index sample)
            (prospectiveInverseSamplingWeight (baseWeight index sample)
              (pateDoubleScore (propensityScore index sample)
                (treatedPrognosticScore index sample)
                (controlPrognosticScore index sample))
              (samplingMass index sample))
            (selectedOutcomeT index sample) (selectedOutcomeC index sample)) =
        0
      rw [hzero, mul_zero])

variable {PATTProgCell : Type*} [DecidableEq PATTProgCell]

/--
Random-sample retrospective PATT double-score survey identification gives a
scaled degenerate weak limit for the target-minus-selected one-sided contrast.
-/
theorem tendstoInDistribution_random_scaled_retrospectivePATTDoubleScoreWeight_error_zero
    (scale : Index -> Sample -> Real)
    (targetSample selectedSample : Index -> Sample -> Finset Unit)
    (cells : Index -> Sample -> Finset (PropensityCell × PATTProgCell))
    (baseWeight : Index -> Sample -> Unit -> Real)
    (treatedTargetOutcome targetControlOutcome selectedControlOutcome :
      Index -> Sample -> Unit -> Real)
    (propensityScore : Index -> Sample -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Sample -> Unit -> PATTProgCell)
    (treatment : Index -> Sample -> Unit -> Prop)
    [∀ index sample, DecidablePred (treatment index sample)]
    (samplingIfTreated samplingIfControl :
      Index -> Sample -> PropensityCell × PATTProgCell -> Real)
    (treatedCellValue :
      Index -> Sample -> PropensityCell × PATTProgCell -> Real)
    (controlValue : Index -> Sample -> PATTProgCell -> Real)
    (hcoverTarget :
      ∀ index sample unit, unit ∈ targetSample index sample ->
        pattDoubleScore (propensityScore index sample)
          (controlPrognosticScore index sample) unit ∈ cells index sample)
    (hcoverSelected :
      ∀ index sample unit, unit ∈ selectedSample index sample ->
        pattDoubleScore (propensityScore index sample)
          (controlPrognosticScore index sample) unit ∈ cells index sample)
    (hmassTarget :
      ∀ index sample cell, cell ∈ cells index sample ->
        scoreCellMass (targetSample index sample) (baseWeight index sample)
          (pattDoubleScore (propensityScore index sample)
            (controlPrognosticScore index sample)) cell ≠ 0)
    (hsamplingTreated :
      ∀ index sample cell, cell ∈ cells index sample ->
        samplingIfTreated index sample cell ≠ 0)
    (hsamplingControl :
      ∀ index sample cell, cell ∈ cells index sample ->
        samplingIfControl index sample cell ≠ 0)
    (htreatedMass :
      ∀ index sample cell, cell ∈ cells index sample ->
        scoreCellMass
            ((selectedSample index sample).filter (treatment index sample))
            (baseWeight index sample)
            (pattDoubleScore (propensityScore index sample)
              (controlPrognosticScore index sample)) cell =
          samplingIfTreated index sample cell *
            scoreCellMass
              ((targetSample index sample).filter (treatment index sample))
              (baseWeight index sample)
              (pattDoubleScore (propensityScore index sample)
                (controlPrognosticScore index sample)) cell)
    (hcontrolMass :
      ∀ index sample cell, cell ∈ cells index sample ->
        scoreCellMass
            ((selectedSample index sample).filter
              (fun unit => ¬ treatment index sample unit))
            (baseWeight index sample)
            (pattDoubleScore (propensityScore index sample)
              (controlPrognosticScore index sample)) cell =
          samplingIfControl index sample cell *
            scoreCellMass
              ((targetSample index sample).filter
                (fun unit => ¬ treatment index sample unit))
              (baseWeight index sample)
              (pattDoubleScore (propensityScore index sample)
                (controlPrognosticScore index sample)) cell)
    (hscoreMeasTargetT :
      ∀ index sample unit, unit ∈ targetSample index sample ->
        treatedTargetOutcome index sample unit =
          treatedCellValue index sample
            (pattDoubleScore (propensityScore index sample)
              (controlPrognosticScore index sample) unit))
    (hscoreMeasTargetC :
      ∀ index sample unit, unit ∈ targetSample index sample ->
        targetControlOutcome index sample unit =
          controlValue index sample
            (controlPrognosticScore index sample unit))
    (hscoreMeasSelectedC :
      ∀ index sample unit, unit ∈ selectedSample index sample ->
        selectedControlOutcome index sample unit =
          controlValue index sample
            (controlPrognosticScore index sample unit)) :
    TendstoInDistribution
      (fun index sample =>
        scale index sample *
          (weightedSampleMeanContrast (targetSample index sample)
            (baseWeight index sample) (treatedTargetOutcome index sample)
            (targetControlOutcome index sample) -
          pattWeightedMeanContrast (targetSample index sample)
            (selectedSample index sample) (baseWeight index sample)
            (retrospectiveInverseSamplingWeight (baseWeight index sample)
              (pattDoubleScore (propensityScore index sample)
                (controlPrognosticScore index sample))
              (treatment index sample) (samplingIfTreated index sample)
              (samplingIfControl index sample))
            (treatedTargetOutcome index sample)
            (selectedControlOutcome index sample)))
      l (fun _sample => (0 : Real)) (fun _index => sampleLaw)
      sampleLaw := by
  exact tendstoInDistribution_zero_of_forall_eq_zero
    (sampleLaw := sampleLaw) (l := l)
    (fun index sample =>
      scale index sample *
        (weightedSampleMeanContrast (targetSample index sample)
          (baseWeight index sample) (treatedTargetOutcome index sample)
          (targetControlOutcome index sample) -
        pattWeightedMeanContrast (targetSample index sample)
          (selectedSample index sample) (baseWeight index sample)
          (retrospectiveInverseSamplingWeight (baseWeight index sample)
            (pattDoubleScore (propensityScore index sample)
              (controlPrognosticScore index sample))
            (treatment index sample) (samplingIfTreated index sample)
            (samplingIfControl index sample))
          (treatedTargetOutcome index sample)
          (selectedControlOutcome index sample)))
    (fun index sample => by
      have hzero :=
        abs_eq_zero.mp
          (abs_target_sub_retrospectivePATTDoubleScoreWeight_eq_zero
            (targetSample index sample) (selectedSample index sample)
            (cells index sample) (baseWeight index sample)
            (treatedTargetOutcome index sample)
            (targetControlOutcome index sample)
            (selectedControlOutcome index sample)
            (propensityScore index sample)
            (controlPrognosticScore index sample) (treatment index sample)
            (samplingIfTreated index sample) (samplingIfControl index sample)
            (treatedCellValue index sample) (controlValue index sample)
            (hcoverTarget index sample) (hcoverSelected index sample)
            (hmassTarget index sample) (hsamplingTreated index sample)
            (hsamplingControl index sample) (htreatedMass index sample)
            (hcontrolMass index sample) (hscoreMeasTargetT index sample)
            (hscoreMeasTargetC index sample)
            (hscoreMeasSelectedC index sample))
      change scale index sample *
          (weightedSampleMeanContrast (targetSample index sample)
            (baseWeight index sample) (treatedTargetOutcome index sample)
            (targetControlOutcome index sample) -
          pattWeightedMeanContrast (targetSample index sample)
            (selectedSample index sample) (baseWeight index sample)
            (retrospectiveInverseSamplingWeight (baseWeight index sample)
              (pattDoubleScore (propensityScore index sample)
                (controlPrognosticScore index sample))
              (treatment index sample) (samplingIfTreated index sample)
              (samplingIfControl index sample))
            (treatedTargetOutcome index sample)
            (selectedControlOutcome index sample)) =
        0
      rw [hzero, mul_zero])

/--
Random-sample prospective PATT double-score survey identification gives a
scaled degenerate weak limit for the target-minus-selected one-sided contrast.
-/
theorem tendstoInDistribution_random_scaled_prospectivePATTDoubleScoreWeight_error_zero
    (scale : Index -> Sample -> Real)
    (targetSample selectedSample : Index -> Sample -> Finset Unit)
    (cells : Index -> Sample -> Finset (PropensityCell × PATTProgCell))
    (baseWeight : Index -> Sample -> Unit -> Real)
    (treatedTargetOutcome targetControlOutcome selectedControlOutcome :
      Index -> Sample -> Unit -> Real)
    (propensityScore : Index -> Sample -> Unit -> PropensityCell)
    (controlPrognosticScore : Index -> Sample -> Unit -> PATTProgCell)
    (treatment : Index -> Sample -> Unit -> Prop)
    [∀ index sample, DecidablePred (treatment index sample)]
    (samplingMass :
      Index -> Sample -> PropensityCell × PATTProgCell -> Real)
    (treatedCellValue :
      Index -> Sample -> PropensityCell × PATTProgCell -> Real)
    (controlValue : Index -> Sample -> PATTProgCell -> Real)
    (hcoverTarget :
      ∀ index sample unit, unit ∈ targetSample index sample ->
        pattDoubleScore (propensityScore index sample)
          (controlPrognosticScore index sample) unit ∈ cells index sample)
    (hcoverSelected :
      ∀ index sample unit, unit ∈ selectedSample index sample ->
        pattDoubleScore (propensityScore index sample)
          (controlPrognosticScore index sample) unit ∈ cells index sample)
    (hmassTarget :
      ∀ index sample cell, cell ∈ cells index sample ->
        scoreCellMass (targetSample index sample) (baseWeight index sample)
          (pattDoubleScore (propensityScore index sample)
            (controlPrognosticScore index sample)) cell ≠ 0)
    (hsampling :
      ∀ index sample cell, cell ∈ cells index sample ->
        samplingMass index sample cell ≠ 0)
    (htreatedMass :
      ∀ index sample cell, cell ∈ cells index sample ->
        scoreCellMass
            ((selectedSample index sample).filter (treatment index sample))
            (baseWeight index sample)
            (pattDoubleScore (propensityScore index sample)
              (controlPrognosticScore index sample)) cell =
          samplingMass index sample cell *
            scoreCellMass
              ((targetSample index sample).filter (treatment index sample))
              (baseWeight index sample)
              (pattDoubleScore (propensityScore index sample)
                (controlPrognosticScore index sample)) cell)
    (hcontrolMass :
      ∀ index sample cell, cell ∈ cells index sample ->
        scoreCellMass
            ((selectedSample index sample).filter
              (fun unit => ¬ treatment index sample unit))
            (baseWeight index sample)
            (pattDoubleScore (propensityScore index sample)
              (controlPrognosticScore index sample)) cell =
          samplingMass index sample cell *
            scoreCellMass
              ((targetSample index sample).filter
                (fun unit => ¬ treatment index sample unit))
              (baseWeight index sample)
              (pattDoubleScore (propensityScore index sample)
                (controlPrognosticScore index sample)) cell)
    (hscoreMeasTargetT :
      ∀ index sample unit, unit ∈ targetSample index sample ->
        treatedTargetOutcome index sample unit =
          treatedCellValue index sample
            (pattDoubleScore (propensityScore index sample)
              (controlPrognosticScore index sample) unit))
    (hscoreMeasTargetC :
      ∀ index sample unit, unit ∈ targetSample index sample ->
        targetControlOutcome index sample unit =
          controlValue index sample
            (controlPrognosticScore index sample unit))
    (hscoreMeasSelectedC :
      ∀ index sample unit, unit ∈ selectedSample index sample ->
        selectedControlOutcome index sample unit =
          controlValue index sample
            (controlPrognosticScore index sample unit)) :
    TendstoInDistribution
      (fun index sample =>
        scale index sample *
          (weightedSampleMeanContrast (targetSample index sample)
            (baseWeight index sample) (treatedTargetOutcome index sample)
            (targetControlOutcome index sample) -
          pattWeightedMeanContrast (targetSample index sample)
            (selectedSample index sample) (baseWeight index sample)
            (prospectiveInverseSamplingWeight (baseWeight index sample)
              (pattDoubleScore (propensityScore index sample)
                (controlPrognosticScore index sample))
              (samplingMass index sample))
            (treatedTargetOutcome index sample)
            (selectedControlOutcome index sample)))
      l (fun _sample => (0 : Real)) (fun _index => sampleLaw)
      sampleLaw := by
  exact tendstoInDistribution_zero_of_forall_eq_zero
    (sampleLaw := sampleLaw) (l := l)
    (fun index sample =>
      scale index sample *
        (weightedSampleMeanContrast (targetSample index sample)
          (baseWeight index sample) (treatedTargetOutcome index sample)
          (targetControlOutcome index sample) -
        pattWeightedMeanContrast (targetSample index sample)
          (selectedSample index sample) (baseWeight index sample)
          (prospectiveInverseSamplingWeight (baseWeight index sample)
            (pattDoubleScore (propensityScore index sample)
              (controlPrognosticScore index sample))
            (samplingMass index sample))
          (treatedTargetOutcome index sample)
          (selectedControlOutcome index sample)))
    (fun index sample => by
      have hzero :=
        abs_eq_zero.mp
          (abs_target_sub_prospectivePATTDoubleScoreWeight_eq_zero
            (targetSample index sample) (selectedSample index sample)
            (cells index sample) (baseWeight index sample)
            (treatedTargetOutcome index sample)
            (targetControlOutcome index sample)
            (selectedControlOutcome index sample)
            (propensityScore index sample)
            (controlPrognosticScore index sample) (treatment index sample)
            (samplingMass index sample) (treatedCellValue index sample)
            (controlValue index sample) (hcoverTarget index sample)
            (hcoverSelected index sample) (hmassTarget index sample)
            (hsampling index sample) (htreatedMass index sample)
            (hcontrolMass index sample) (hscoreMeasTargetT index sample)
            (hscoreMeasTargetC index sample)
            (hscoreMeasSelectedC index sample))
      change scale index sample *
          (weightedSampleMeanContrast (targetSample index sample)
            (baseWeight index sample) (treatedTargetOutcome index sample)
            (targetControlOutcome index sample) -
          pattWeightedMeanContrast (targetSample index sample)
            (selectedSample index sample) (baseWeight index sample)
            (prospectiveInverseSamplingWeight (baseWeight index sample)
              (pattDoubleScore (propensityScore index sample)
                (controlPrognosticScore index sample))
              (samplingMass index sample))
            (treatedTargetOutcome index sample)
            (selectedControlOutcome index sample)) =
        0
      rw [hzero, mul_zero])

end WDSM
end Matching
end StatInference
