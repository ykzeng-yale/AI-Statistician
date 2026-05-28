import StatInference.Matching.WDSM.DiscreteDoubleScoreSurveyZeroError
import StatInference.Matching.WDSM.ExactZeroInDistributionAlgebra

/-!
# Distributional limit transfer across exact double-score survey identities

This module turns exact finite WDSM survey-identification equalities into
asymptotic transfer rules.  If the target-sample contrast has a distributional
limit after centering and scaling, then the selected inverse-survey-weighted
contrast has the same limit whenever the exact double-score survey identity
holds pointwise.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open Filter
open scoped Topology

variable {Index Sample Unit PropensityCell TreatedProgCell ControlProgCell :
  Type*}
variable [MeasurableSpace Sample]
variable {sampleLaw : MeasureTheory.Measure Sample}
variable [MeasureTheory.IsProbabilityMeasure sampleLaw]
variable {LimitSample : Type*} [MeasurableSpace LimitSample]
variable {limitLaw : MeasureTheory.Measure LimitSample}
variable [MeasureTheory.IsProbabilityMeasure limitLaw]
variable {l : Filter Index}
variable [DecidableEq PropensityCell] [DecidableEq TreatedProgCell]
  [DecidableEq ControlProgCell]

/--
If the scaled and centered target PATE contrast has a weak limit, then the
retrospective selected-sample double-score survey weighted PATE contrast has
the same weak limit under the exact finite survey-identification assumptions.
-/
theorem tendstoInDistribution_retrospectivePATEDoubleScoreWeight_selected_of_target_limit
    (scale center : Index -> Sample -> Real)
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
    (limit : LimitSample -> Real)
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
            (controlPrognosticScore index sample unit))
    (htargetLimit :
      TendstoInDistribution
        (fun index sample =>
          scale index sample *
            (weightedSampleMeanContrast (targetSample index sample)
              (baseWeight index sample) (targetOutcomeT index sample)
              (targetOutcomeC index sample) -
            center index sample))
        l limit (fun _index => sampleLaw) limitLaw) :
    TendstoInDistribution
      (fun index sample =>
        scale index sample *
          (weightedSampleMeanContrast (selectedSample index sample)
            (retrospectiveInverseSamplingWeight (baseWeight index sample)
              (pateDoubleScore (propensityScore index sample)
                (treatedPrognosticScore index sample)
                (controlPrognosticScore index sample))
              (treatment index sample) (samplingIfTreated index sample)
              (samplingIfControl index sample))
            (selectedOutcomeT index sample) (selectedOutcomeC index sample) -
          center index sample))
      l limit (fun _index => sampleLaw) limitLaw := by
  refine tendstoInDistribution_of_ae_eq
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    (fun index sample =>
      scale index sample *
        (weightedSampleMeanContrast (selectedSample index sample)
          (retrospectiveInverseSamplingWeight (baseWeight index sample)
            (pateDoubleScore (propensityScore index sample)
              (treatedPrognosticScore index sample)
              (controlPrognosticScore index sample))
            (treatment index sample) (samplingIfTreated index sample)
            (samplingIfControl index sample))
          (selectedOutcomeT index sample) (selectedOutcomeC index sample) -
        center index sample))
    (fun index sample =>
      scale index sample *
        (weightedSampleMeanContrast (targetSample index sample)
          (baseWeight index sample) (targetOutcomeT index sample)
          (targetOutcomeC index sample) -
        center index sample))
    limit ?_ htargetLimit
  intro index
  exact Eventually.of_forall (fun sample => by
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
    have htarget_eq_selected :
        weightedSampleMeanContrast (targetSample index sample)
            (baseWeight index sample) (targetOutcomeT index sample)
            (targetOutcomeC index sample) =
          weightedSampleMeanContrast (selectedSample index sample)
            (retrospectiveInverseSamplingWeight (baseWeight index sample)
              (pateDoubleScore (propensityScore index sample)
                (treatedPrognosticScore index sample)
                (controlPrognosticScore index sample))
              (treatment index sample) (samplingIfTreated index sample)
              (samplingIfControl index sample))
            (selectedOutcomeT index sample)
            (selectedOutcomeC index sample) := by
      exact sub_eq_zero.mp hzero
    change scale index sample *
          (weightedSampleMeanContrast (selectedSample index sample)
            (retrospectiveInverseSamplingWeight (baseWeight index sample)
              (pateDoubleScore (propensityScore index sample)
                (treatedPrognosticScore index sample)
                (controlPrognosticScore index sample))
              (treatment index sample) (samplingIfTreated index sample)
              (samplingIfControl index sample))
            (selectedOutcomeT index sample) (selectedOutcomeC index sample) -
          center index sample) =
        scale index sample *
          (weightedSampleMeanContrast (targetSample index sample)
            (baseWeight index sample) (targetOutcomeT index sample)
            (targetOutcomeC index sample) -
          center index sample)
    rw [← htarget_eq_selected])

/--
If the target PATE contrast has a weak limit, then the retrospective
selected-sample double-score survey weighted PATE contrast has the same weak
limit under the exact finite survey-identification assumptions.
-/
theorem tendstoInDistribution_retrospectivePATEDoubleScoreWeight_selected_contrast_of_target_contrast
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
    (limit : LimitSample -> Real)
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
            (controlPrognosticScore index sample unit))
    (htargetLimit :
      TendstoInDistribution
        (fun index sample =>
          weightedSampleMeanContrast (targetSample index sample)
            (baseWeight index sample) (targetOutcomeT index sample)
            (targetOutcomeC index sample))
        l limit (fun _index => sampleLaw) limitLaw) :
    TendstoInDistribution
      (fun index sample =>
        weightedSampleMeanContrast (selectedSample index sample)
          (retrospectiveInverseSamplingWeight (baseWeight index sample)
            (pateDoubleScore (propensityScore index sample)
              (treatedPrognosticScore index sample)
              (controlPrognosticScore index sample))
            (treatment index sample) (samplingIfTreated index sample)
            (samplingIfControl index sample))
          (selectedOutcomeT index sample) (selectedOutcomeC index sample))
      l limit (fun _index => sampleLaw) limitLaw := by
  simpa using
    (tendstoInDistribution_retrospectivePATEDoubleScoreWeight_selected_of_target_limit
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      (fun _index _sample => (1 : Real)) (fun _index _sample => (0 : Real))
      targetSample selectedSample cells baseWeight targetOutcomeT
      targetOutcomeC selectedOutcomeT selectedOutcomeC propensityScore
      treatedPrognosticScore controlPrognosticScore treatment
      samplingIfTreated samplingIfControl treatedValue controlValue limit
      hcoverTarget hcoverSelected hmassTarget hsamplingTreated
      hsamplingControl htreatedMass hcontrolMass hscoreMeasTargetT
      hscoreMeasSelectedT hscoreMeasTargetC hscoreMeasSelectedC
      (by simpa using htargetLimit))

/--
If the scaled and centered target PATE contrast has a weak limit, then the
prospective selected-sample double-score survey weighted PATE contrast has the
same weak limit under the exact finite survey-identification assumptions.
-/
theorem tendstoInDistribution_prospectivePATEDoubleScoreWeight_selected_of_target_limit
    (scale center : Index -> Sample -> Real)
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
    (limit : LimitSample -> Real)
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
            (controlPrognosticScore index sample unit))
    (htargetLimit :
      TendstoInDistribution
        (fun index sample =>
          scale index sample *
            (weightedSampleMeanContrast (targetSample index sample)
              (baseWeight index sample) (targetOutcomeT index sample)
              (targetOutcomeC index sample) -
            center index sample))
        l limit (fun _index => sampleLaw) limitLaw) :
    TendstoInDistribution
      (fun index sample =>
        scale index sample *
          (weightedSampleMeanContrast (selectedSample index sample)
            (prospectiveInverseSamplingWeight (baseWeight index sample)
              (pateDoubleScore (propensityScore index sample)
                (treatedPrognosticScore index sample)
                (controlPrognosticScore index sample))
              (samplingMass index sample))
            (selectedOutcomeT index sample) (selectedOutcomeC index sample) -
          center index sample))
      l limit (fun _index => sampleLaw) limitLaw := by
  refine tendstoInDistribution_of_ae_eq
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    (fun index sample =>
      scale index sample *
        (weightedSampleMeanContrast (selectedSample index sample)
          (prospectiveInverseSamplingWeight (baseWeight index sample)
            (pateDoubleScore (propensityScore index sample)
              (treatedPrognosticScore index sample)
              (controlPrognosticScore index sample))
            (samplingMass index sample))
          (selectedOutcomeT index sample) (selectedOutcomeC index sample) -
        center index sample))
    (fun index sample =>
      scale index sample *
        (weightedSampleMeanContrast (targetSample index sample)
          (baseWeight index sample) (targetOutcomeT index sample)
          (targetOutcomeC index sample) -
        center index sample))
    limit ?_ htargetLimit
  intro index
  exact Eventually.of_forall (fun sample => by
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
    have htarget_eq_selected :
        weightedSampleMeanContrast (targetSample index sample)
            (baseWeight index sample) (targetOutcomeT index sample)
            (targetOutcomeC index sample) =
          weightedSampleMeanContrast (selectedSample index sample)
            (prospectiveInverseSamplingWeight (baseWeight index sample)
              (pateDoubleScore (propensityScore index sample)
                (treatedPrognosticScore index sample)
                (controlPrognosticScore index sample))
              (samplingMass index sample))
            (selectedOutcomeT index sample)
            (selectedOutcomeC index sample) := by
      exact sub_eq_zero.mp hzero
    change scale index sample *
          (weightedSampleMeanContrast (selectedSample index sample)
            (prospectiveInverseSamplingWeight (baseWeight index sample)
              (pateDoubleScore (propensityScore index sample)
                (treatedPrognosticScore index sample)
                (controlPrognosticScore index sample))
              (samplingMass index sample))
            (selectedOutcomeT index sample) (selectedOutcomeC index sample) -
          center index sample) =
        scale index sample *
          (weightedSampleMeanContrast (targetSample index sample)
            (baseWeight index sample) (targetOutcomeT index sample)
            (targetOutcomeC index sample) -
          center index sample)
    rw [← htarget_eq_selected])

/--
If the target PATE contrast has a weak limit, then the prospective
selected-sample double-score survey weighted PATE contrast has the same weak
limit under the exact finite survey-identification assumptions.
-/
theorem tendstoInDistribution_prospectivePATEDoubleScoreWeight_selected_contrast_of_target_contrast
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
    (limit : LimitSample -> Real)
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
            (controlPrognosticScore index sample unit))
    (htargetLimit :
      TendstoInDistribution
        (fun index sample =>
          weightedSampleMeanContrast (targetSample index sample)
            (baseWeight index sample) (targetOutcomeT index sample)
            (targetOutcomeC index sample))
        l limit (fun _index => sampleLaw) limitLaw) :
    TendstoInDistribution
      (fun index sample =>
        weightedSampleMeanContrast (selectedSample index sample)
          (prospectiveInverseSamplingWeight (baseWeight index sample)
            (pateDoubleScore (propensityScore index sample)
              (treatedPrognosticScore index sample)
              (controlPrognosticScore index sample))
            (samplingMass index sample))
          (selectedOutcomeT index sample) (selectedOutcomeC index sample))
      l limit (fun _index => sampleLaw) limitLaw := by
  simpa using
    (tendstoInDistribution_prospectivePATEDoubleScoreWeight_selected_of_target_limit
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      (fun _index _sample => (1 : Real)) (fun _index _sample => (0 : Real))
      targetSample selectedSample cells baseWeight targetOutcomeT
      targetOutcomeC selectedOutcomeT selectedOutcomeC propensityScore
      treatedPrognosticScore controlPrognosticScore treatment samplingMass
      treatedValue controlValue limit hcoverTarget hcoverSelected
      hmassTarget hsampling htreatedMass hcontrolMass hscoreMeasTargetT
      hscoreMeasSelectedT hscoreMeasTargetC hscoreMeasSelectedC
      (by simpa using htargetLimit))

variable {PATTProgCell : Type*} [DecidableEq PATTProgCell]

/--
If the scaled and centered target PATT contrast has a weak limit, then the
retrospective selected-sample double-score survey weighted PATT contrast has
the same weak limit under the exact finite survey-identification assumptions.
-/
theorem tendstoInDistribution_retrospectivePATTDoubleScoreWeight_selected_of_target_limit
    (scale center : Index -> Sample -> Real)
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
    (limit : LimitSample -> Real)
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
            (controlPrognosticScore index sample unit))
    (htargetLimit :
      TendstoInDistribution
        (fun index sample =>
          scale index sample *
            (weightedSampleMeanContrast (targetSample index sample)
              (baseWeight index sample) (treatedTargetOutcome index sample)
              (targetControlOutcome index sample) -
            center index sample))
        l limit (fun _index => sampleLaw) limitLaw) :
    TendstoInDistribution
      (fun index sample =>
        scale index sample *
          (pattWeightedMeanContrast (targetSample index sample)
            (selectedSample index sample) (baseWeight index sample)
            (retrospectiveInverseSamplingWeight (baseWeight index sample)
              (pattDoubleScore (propensityScore index sample)
                (controlPrognosticScore index sample))
              (treatment index sample) (samplingIfTreated index sample)
              (samplingIfControl index sample))
            (treatedTargetOutcome index sample)
            (selectedControlOutcome index sample) -
          center index sample))
      l limit (fun _index => sampleLaw) limitLaw := by
  refine tendstoInDistribution_of_ae_eq
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    (fun index sample =>
      scale index sample *
        (pattWeightedMeanContrast (targetSample index sample)
          (selectedSample index sample) (baseWeight index sample)
          (retrospectiveInverseSamplingWeight (baseWeight index sample)
            (pattDoubleScore (propensityScore index sample)
              (controlPrognosticScore index sample))
            (treatment index sample) (samplingIfTreated index sample)
            (samplingIfControl index sample))
          (treatedTargetOutcome index sample)
          (selectedControlOutcome index sample) -
        center index sample))
    (fun index sample =>
      scale index sample *
        (weightedSampleMeanContrast (targetSample index sample)
          (baseWeight index sample) (treatedTargetOutcome index sample)
          (targetControlOutcome index sample) -
        center index sample))
    limit ?_ htargetLimit
  intro index
  exact Eventually.of_forall (fun sample => by
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
    have htarget_eq_selected :
        weightedSampleMeanContrast (targetSample index sample)
            (baseWeight index sample) (treatedTargetOutcome index sample)
            (targetControlOutcome index sample) =
          pattWeightedMeanContrast (targetSample index sample)
            (selectedSample index sample) (baseWeight index sample)
            (retrospectiveInverseSamplingWeight (baseWeight index sample)
              (pattDoubleScore (propensityScore index sample)
                (controlPrognosticScore index sample))
              (treatment index sample) (samplingIfTreated index sample)
              (samplingIfControl index sample))
            (treatedTargetOutcome index sample)
            (selectedControlOutcome index sample) := by
      exact sub_eq_zero.mp hzero
    change scale index sample *
          (pattWeightedMeanContrast (targetSample index sample)
            (selectedSample index sample) (baseWeight index sample)
            (retrospectiveInverseSamplingWeight (baseWeight index sample)
              (pattDoubleScore (propensityScore index sample)
                (controlPrognosticScore index sample))
              (treatment index sample) (samplingIfTreated index sample)
              (samplingIfControl index sample))
            (treatedTargetOutcome index sample)
            (selectedControlOutcome index sample) -
          center index sample) =
        scale index sample *
          (weightedSampleMeanContrast (targetSample index sample)
            (baseWeight index sample) (treatedTargetOutcome index sample)
            (targetControlOutcome index sample) -
          center index sample)
    rw [← htarget_eq_selected])

/--
If the target PATT contrast has a weak limit, then the retrospective
selected-sample double-score survey weighted PATT contrast has the same weak
limit under the exact finite survey-identification assumptions.
-/
theorem tendstoInDistribution_retrospectivePATTDoubleScoreWeight_selected_contrast_of_target_contrast
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
    (limit : LimitSample -> Real)
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
            (controlPrognosticScore index sample unit))
    (htargetLimit :
      TendstoInDistribution
        (fun index sample =>
          weightedSampleMeanContrast (targetSample index sample)
            (baseWeight index sample) (treatedTargetOutcome index sample)
            (targetControlOutcome index sample))
        l limit (fun _index => sampleLaw) limitLaw) :
    TendstoInDistribution
      (fun index sample =>
        pattWeightedMeanContrast (targetSample index sample)
          (selectedSample index sample) (baseWeight index sample)
          (retrospectiveInverseSamplingWeight (baseWeight index sample)
            (pattDoubleScore (propensityScore index sample)
              (controlPrognosticScore index sample))
            (treatment index sample) (samplingIfTreated index sample)
            (samplingIfControl index sample))
          (treatedTargetOutcome index sample)
          (selectedControlOutcome index sample))
      l limit (fun _index => sampleLaw) limitLaw := by
  simpa using
    (tendstoInDistribution_retrospectivePATTDoubleScoreWeight_selected_of_target_limit
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      (fun _index _sample => (1 : Real)) (fun _index _sample => (0 : Real))
      targetSample selectedSample cells baseWeight treatedTargetOutcome
      targetControlOutcome selectedControlOutcome propensityScore
      controlPrognosticScore treatment samplingIfTreated samplingIfControl
      treatedCellValue controlValue limit hcoverTarget hcoverSelected
      hmassTarget hsamplingTreated hsamplingControl htreatedMass
      hcontrolMass hscoreMeasTargetT hscoreMeasTargetC hscoreMeasSelectedC
      (by simpa using htargetLimit))

/--
If the scaled and centered target PATT contrast has a weak limit, then the
prospective selected-sample double-score survey weighted PATT contrast has the
same weak limit under the exact finite survey-identification assumptions.
-/
theorem tendstoInDistribution_prospectivePATTDoubleScoreWeight_selected_of_target_limit
    (scale center : Index -> Sample -> Real)
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
    (limit : LimitSample -> Real)
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
            (controlPrognosticScore index sample unit))
    (htargetLimit :
      TendstoInDistribution
        (fun index sample =>
          scale index sample *
            (weightedSampleMeanContrast (targetSample index sample)
              (baseWeight index sample) (treatedTargetOutcome index sample)
              (targetControlOutcome index sample) -
            center index sample))
        l limit (fun _index => sampleLaw) limitLaw) :
    TendstoInDistribution
      (fun index sample =>
        scale index sample *
          (pattWeightedMeanContrast (targetSample index sample)
            (selectedSample index sample) (baseWeight index sample)
            (prospectiveInverseSamplingWeight (baseWeight index sample)
              (pattDoubleScore (propensityScore index sample)
                (controlPrognosticScore index sample))
              (samplingMass index sample))
            (treatedTargetOutcome index sample)
            (selectedControlOutcome index sample) -
          center index sample))
      l limit (fun _index => sampleLaw) limitLaw := by
  refine tendstoInDistribution_of_ae_eq
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    (fun index sample =>
      scale index sample *
        (pattWeightedMeanContrast (targetSample index sample)
          (selectedSample index sample) (baseWeight index sample)
          (prospectiveInverseSamplingWeight (baseWeight index sample)
            (pattDoubleScore (propensityScore index sample)
              (controlPrognosticScore index sample))
            (samplingMass index sample))
          (treatedTargetOutcome index sample)
          (selectedControlOutcome index sample) -
        center index sample))
    (fun index sample =>
      scale index sample *
        (weightedSampleMeanContrast (targetSample index sample)
          (baseWeight index sample) (treatedTargetOutcome index sample)
          (targetControlOutcome index sample) -
        center index sample))
    limit ?_ htargetLimit
  intro index
  exact Eventually.of_forall (fun sample => by
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
    have htarget_eq_selected :
        weightedSampleMeanContrast (targetSample index sample)
            (baseWeight index sample) (treatedTargetOutcome index sample)
            (targetControlOutcome index sample) =
          pattWeightedMeanContrast (targetSample index sample)
            (selectedSample index sample) (baseWeight index sample)
            (prospectiveInverseSamplingWeight (baseWeight index sample)
              (pattDoubleScore (propensityScore index sample)
                (controlPrognosticScore index sample))
              (samplingMass index sample))
            (treatedTargetOutcome index sample)
            (selectedControlOutcome index sample) := by
      exact sub_eq_zero.mp hzero
    change scale index sample *
          (pattWeightedMeanContrast (targetSample index sample)
            (selectedSample index sample) (baseWeight index sample)
            (prospectiveInverseSamplingWeight (baseWeight index sample)
              (pattDoubleScore (propensityScore index sample)
                (controlPrognosticScore index sample))
              (samplingMass index sample))
            (treatedTargetOutcome index sample)
            (selectedControlOutcome index sample) -
          center index sample) =
        scale index sample *
          (weightedSampleMeanContrast (targetSample index sample)
            (baseWeight index sample) (treatedTargetOutcome index sample)
            (targetControlOutcome index sample) -
          center index sample)
    rw [← htarget_eq_selected])

/--
If the target PATT contrast has a weak limit, then the prospective
selected-sample double-score survey weighted PATT contrast has the same weak
limit under the exact finite survey-identification assumptions.
-/
theorem tendstoInDistribution_prospectivePATTDoubleScoreWeight_selected_contrast_of_target_contrast
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
    (limit : LimitSample -> Real)
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
            (controlPrognosticScore index sample unit))
    (htargetLimit :
      TendstoInDistribution
        (fun index sample =>
          weightedSampleMeanContrast (targetSample index sample)
            (baseWeight index sample) (treatedTargetOutcome index sample)
            (targetControlOutcome index sample))
        l limit (fun _index => sampleLaw) limitLaw) :
    TendstoInDistribution
      (fun index sample =>
        pattWeightedMeanContrast (targetSample index sample)
          (selectedSample index sample) (baseWeight index sample)
          (prospectiveInverseSamplingWeight (baseWeight index sample)
            (pattDoubleScore (propensityScore index sample)
              (controlPrognosticScore index sample))
            (samplingMass index sample))
          (treatedTargetOutcome index sample)
          (selectedControlOutcome index sample))
      l limit (fun _index => sampleLaw) limitLaw := by
  simpa using
    (tendstoInDistribution_prospectivePATTDoubleScoreWeight_selected_of_target_limit
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      (fun _index _sample => (1 : Real)) (fun _index _sample => (0 : Real))
      targetSample selectedSample cells baseWeight treatedTargetOutcome
      targetControlOutcome selectedControlOutcome propensityScore
      controlPrognosticScore treatment samplingMass treatedCellValue
      controlValue limit hcoverTarget hcoverSelected hmassTarget hsampling
      htreatedMass hcontrolMass hscoreMeasTargetT hscoreMeasTargetC
      hscoreMeasSelectedC (by simpa using htargetLimit))

end WDSM
end Matching
end StatInference
