import StatInference.Matching.WDSM.FiniteCellIndicatorGCAdapter
import StatInference.Matching.WDSM.FiniteCellIndicatorEstimatedScoreComponentPositiveVarianceStudentizedBridge

/-!
# GC-backed single-arm component-positive studentized bridges

This module connects the single-arm Glivenko-Cantelli finite score-cell
adapter to the component-positive estimated-score studentization constructors.
It avoids routing PATE-only or PATT-only conclusions through a paired bridge.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter MeasureTheory
open scoped Topology

variable {Unit Cell Index Sample LimitSample : Type*}
variable [DecidableEq Cell]
variable {Param : Type*} [DecidableEq Param]
variable [MeasurableSpace Sample] [MeasurableSpace LimitSample]
variable {sampleLaw : MeasureTheory.Measure Sample}
variable {limitLaw : MeasureTheory.Measure LimitSample}
variable [MeasureTheory.IsProbabilityMeasure sampleLaw]
variable [MeasureTheory.IsProbabilityMeasure limitLaw]
variable {l : Filter Index}
variable [l.IsCountablyGenerated]

/-! ## PATE constructors -/

/--
Build a PATE component-positive estimated-score studentized bridge from
GC-backed finite score-cell inputs, strict projection slack, and nonnegative
target drift.
-/
def
    pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_lt_limit_glivenkoCantelli
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (finiteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicatorBridge.weighted_indicator_sum_lln)
    (cltBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge Cell)
    (finiteConditionsToScaled :
      indicatorBridge.eventual_finite_conditions ->
        cltBridge.indicator_bridge.eventual_finite_conditions)
    (envelopeToScaled :
      indicatorBridge.envelope_convergence ->
        cltBridge.indicator_bridge.envelope_convergence)
    (indicatorLLNToScaled :
      indicatorBridge.weighted_indicator_sum_lln ->
        cltBridge.indicator_bridge.weighted_indicator_sum_lln)
    (knownScoreBridge : KnownScoreAsymptoticBridge)
    (scaledApproximationToMatchingDiscrepancy :
      cltBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        knownScoreBridge.matching_discrepancy_negligible)
    (estimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimatedScoreBridge.known_score_asymptotic_normality)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hdriftLimit_nonneg : 0 ≤ targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw) :
    PATEFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_lt_limit
    (pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    scaledStatistic oracle projectionReduction targetDrift limit oracleLimit
    projectionLimit targetDriftLimit horacle hprojection hdrift
    hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
    estimatedScoreToScaledTendsto

/--
Build a PATE component-positive estimated-score studentized bridge from
GC-backed finite score-cell inputs, weak projection slack, and positive target
drift.
-/
def
    pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_le_drift_pos_limit_glivenkoCantelli
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (finiteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicatorBridge.weighted_indicator_sum_lln)
    (cltBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge Cell)
    (finiteConditionsToScaled :
      indicatorBridge.eventual_finite_conditions ->
        cltBridge.indicator_bridge.eventual_finite_conditions)
    (envelopeToScaled :
      indicatorBridge.envelope_convergence ->
        cltBridge.indicator_bridge.envelope_convergence)
    (indicatorLLNToScaled :
      indicatorBridge.weighted_indicator_sum_lln ->
        cltBridge.indicator_bridge.weighted_indicator_sum_lln)
    (knownScoreBridge : KnownScoreAsymptoticBridge)
    (scaledApproximationToMatchingDiscrepancy :
      cltBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        knownScoreBridge.matching_discrepancy_negligible)
    (estimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimatedScoreBridge.known_score_asymptotic_normality)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_le_oracle : projectionLimit ≤ oracleLimit)
    (hdriftLimit_pos : 0 < targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw) :
    PATEFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_le_drift_pos_limit
    (pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    scaledStatistic oracle projectionReduction targetDrift limit oracleLimit
    projectionLimit targetDriftLimit horacle hprojection hdrift
    hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
    estimatedScoreToScaledTendsto

/--
Build a fixed-law PATE component-positive estimated-score studentized bridge
from GC-backed finite score-cell inputs and strict projection slack.
-/
def
    pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (finiteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicatorBridge.weighted_indicator_sum_lln)
    (cltBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge Cell)
    (finiteConditionsToScaled :
      indicatorBridge.eventual_finite_conditions ->
        cltBridge.indicator_bridge.eventual_finite_conditions)
    (envelopeToScaled :
      indicatorBridge.envelope_convergence ->
        cltBridge.indicator_bridge.envelope_convergence)
    (indicatorLLNToScaled :
      indicatorBridge.weighted_indicator_sum_lln ->
        cltBridge.indicator_bridge.weighted_indicator_sum_lln)
    (knownScoreBridge : KnownScoreAsymptoticBridge)
    (scaledApproximationToMatchingDiscrepancy :
      cltBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        knownScoreBridge.matching_discrepancy_negligible)
    (estimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimatedScoreBridge.known_score_asymptotic_normality)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw) :
    PATEFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_fixedLaw_projection_lt_limit
    (pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    scaledStatistic oracle projectionReduction limit oracleLimit
    projectionLimit horacle hprojection hprojectionLimit_lt_oracle
    hinverse_meas estimatedScoreToScaledTendsto

/--
Build a PATE component-positive estimated-score studentized bridge from
GC-backed finite score-cell inputs and score-quadratic strict projection slack.
-/
noncomputable def
    pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_projection_lt_limit_glivenkoCantelli
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (finiteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicatorBridge.weighted_indicator_sum_lln)
    (cltBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge Cell)
    (finiteConditionsToScaled :
      indicatorBridge.eventual_finite_conditions ->
        cltBridge.indicator_bridge.eventual_finite_conditions)
    (envelopeToScaled :
      indicatorBridge.envelope_convergence ->
        cltBridge.indicator_bridge.envelope_convergence)
    (indicatorLLNToScaled :
      indicatorBridge.weighted_indicator_sum_lln ->
        cltBridge.indicator_bridge.weighted_indicator_sum_lln)
    (knownScoreBridge : KnownScoreAsymptoticBridge)
    (scaledApproximationToMatchingDiscrepancy :
      cltBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        knownScoreBridge.matching_discrepancy_negligible)
    (estimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimatedScoreBridge.known_score_asymptotic_normality)
    (parameters : Finset Param)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle : Index -> Sample -> Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Index -> Sample -> Param -> Param -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm parameters firstStepLoading
            (scoreCovariance index sample))
        l (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm parameters targetDriftLoading
            (scoreCovariance index sample))
        l (fun _sample => targetDriftLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hdriftLimit_nonneg : 0 ≤ targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (scoreQuadraticForm parameters firstStepLoading
                  (scoreCovariance index sample))
                (scoreQuadraticForm parameters targetDriftLoading
                  (scoreCovariance index sample))))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw) :
    PATEFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_projection_lt_limit
    (pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    parameters scaledStatistic oracle firstStepLoading targetDriftLoading
    scoreCovariance limit oracleLimit projectionLimit targetDriftLimit
    horacle hprojection hdrift hprojectionLimit_lt_oracle
    hdriftLimit_nonneg hinverse_meas estimatedScoreToScaledTendsto

/--
Build a PATE score-adjusted strict projection-slack bridge from a
local-experiment estimated-score input instead of an opaque packaged bridge.
-/
noncomputable def
    pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_projection_lt_limit_glivenkoCantelli_local_experiment_input
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (finiteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicatorBridge.weighted_indicator_sum_lln)
    (cltBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge Cell)
    (finiteConditionsToScaled :
      indicatorBridge.eventual_finite_conditions ->
        cltBridge.indicator_bridge.eventual_finite_conditions)
    (envelopeToScaled :
      indicatorBridge.envelope_convergence ->
        cltBridge.indicator_bridge.envelope_convergence)
    (indicatorLLNToScaled :
      indicatorBridge.weighted_indicator_sum_lln ->
        cltBridge.indicator_bridge.weighted_indicator_sum_lln)
    (knownScoreBridge : KnownScoreAsymptoticBridge)
    (scaledApproximationToMatchingDiscrepancy :
      cltBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        knownScoreBridge.matching_discrepancy_negligible)
    (estimated : EstimatedScoreLocalExperimentInput)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (parameters : Finset Param)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle : Index -> Sample -> Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Index -> Sample -> Param -> Param -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm parameters firstStepLoading
            (scoreCovariance index sample))
        l (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm parameters targetDriftLoading
            (scoreCovariance index sample))
        l (fun _sample => targetDriftLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hdriftLimit_nonneg : 0 ≤ targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (scoreQuadraticForm parameters firstStepLoading
                  (scoreCovariance index sample))
                (scoreQuadraticForm parameters targetDriftLoading
                  (scoreCovariance index sample))))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw) :
    PATEFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
    envelopeToScaled indicatorLLNToScaled knownScoreBridge
    scaledApproximationToMatchingDiscrepancy
    (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated)
    knownScoreToEstimatedScoreInput parameters scaledStatistic oracle
    firstStepLoading targetDriftLoading scoreCovariance limit oracleLimit
    projectionLimit targetDriftLimit horacle hprojection hdrift
    hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
    estimatedScoreToScaledTendsto

/--
Build a PATE component-positive estimated-score studentized bridge from
GC-backed finite score-cell inputs, score-quadratic weak projection slack, and
positive target-drift limit.
-/
noncomputable def
    pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_projection_le_drift_pos_limit_glivenkoCantelli
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (finiteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicatorBridge.weighted_indicator_sum_lln)
    (cltBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge Cell)
    (finiteConditionsToScaled :
      indicatorBridge.eventual_finite_conditions ->
        cltBridge.indicator_bridge.eventual_finite_conditions)
    (envelopeToScaled :
      indicatorBridge.envelope_convergence ->
        cltBridge.indicator_bridge.envelope_convergence)
    (indicatorLLNToScaled :
      indicatorBridge.weighted_indicator_sum_lln ->
        cltBridge.indicator_bridge.weighted_indicator_sum_lln)
    (knownScoreBridge : KnownScoreAsymptoticBridge)
    (scaledApproximationToMatchingDiscrepancy :
      cltBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        knownScoreBridge.matching_discrepancy_negligible)
    (estimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimatedScoreBridge.known_score_asymptotic_normality)
    (parameters : Finset Param)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle : Index -> Sample -> Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Index -> Sample -> Param -> Param -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm parameters firstStepLoading
            (scoreCovariance index sample))
        l (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm parameters targetDriftLoading
            (scoreCovariance index sample))
        l (fun _sample => targetDriftLimit))
    (hprojectionLimit_le_oracle : projectionLimit ≤ oracleLimit)
    (hdriftLimit_pos : 0 < targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (scoreQuadraticForm parameters firstStepLoading
                  (scoreCovariance index sample))
                (scoreQuadraticForm parameters targetDriftLoading
                  (scoreCovariance index sample))))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw) :
    PATEFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_projection_le_drift_pos_limit
    (pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    parameters scaledStatistic oracle firstStepLoading targetDriftLoading
    scoreCovariance limit oracleLimit projectionLimit targetDriftLimit
    horacle hprojection hdrift hprojectionLimit_le_oracle
    hdriftLimit_pos hinverse_meas estimatedScoreToScaledTendsto

/--
Build a PATE score-adjusted weak projection-slack positive-drift bridge from a
local-experiment estimated-score input instead of an opaque packaged bridge.
-/
noncomputable def
    pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_projection_le_drift_pos_limit_glivenkoCantelli_local_experiment_input
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (finiteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicatorBridge.weighted_indicator_sum_lln)
    (cltBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge Cell)
    (finiteConditionsToScaled :
      indicatorBridge.eventual_finite_conditions ->
        cltBridge.indicator_bridge.eventual_finite_conditions)
    (envelopeToScaled :
      indicatorBridge.envelope_convergence ->
        cltBridge.indicator_bridge.envelope_convergence)
    (indicatorLLNToScaled :
      indicatorBridge.weighted_indicator_sum_lln ->
        cltBridge.indicator_bridge.weighted_indicator_sum_lln)
    (knownScoreBridge : KnownScoreAsymptoticBridge)
    (scaledApproximationToMatchingDiscrepancy :
      cltBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        knownScoreBridge.matching_discrepancy_negligible)
    (estimated : EstimatedScoreLocalExperimentInput)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (parameters : Finset Param)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle : Index -> Sample -> Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Index -> Sample -> Param -> Param -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm parameters firstStepLoading
            (scoreCovariance index sample))
        l (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm parameters targetDriftLoading
            (scoreCovariance index sample))
        l (fun _sample => targetDriftLimit))
    (hprojectionLimit_le_oracle : projectionLimit ≤ oracleLimit)
    (hdriftLimit_pos : 0 < targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (scoreQuadraticForm parameters firstStepLoading
                  (scoreCovariance index sample))
                (scoreQuadraticForm parameters targetDriftLoading
                  (scoreCovariance index sample))))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw) :
    PATEFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_projection_le_drift_pos_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
    envelopeToScaled indicatorLLNToScaled knownScoreBridge
    scaledApproximationToMatchingDiscrepancy
    (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated)
    knownScoreToEstimatedScoreInput parameters scaledStatistic oracle
    firstStepLoading targetDriftLoading scoreCovariance limit oracleLimit
    projectionLimit targetDriftLimit horacle hprojection hdrift
    hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
    estimatedScoreToScaledTendsto

/--
Build a fixed-law PATE component-positive estimated-score studentized bridge
from GC-backed finite score-cell inputs and score-quadratic strict projection
slack.
-/
noncomputable def
    pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_fixedLaw_projection_lt_limit_glivenkoCantelli
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (finiteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicatorBridge.weighted_indicator_sum_lln)
    (cltBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge Cell)
    (finiteConditionsToScaled :
      indicatorBridge.eventual_finite_conditions ->
        cltBridge.indicator_bridge.eventual_finite_conditions)
    (envelopeToScaled :
      indicatorBridge.envelope_convergence ->
        cltBridge.indicator_bridge.envelope_convergence)
    (indicatorLLNToScaled :
      indicatorBridge.weighted_indicator_sum_lln ->
        cltBridge.indicator_bridge.weighted_indicator_sum_lln)
    (knownScoreBridge : KnownScoreAsymptoticBridge)
    (scaledApproximationToMatchingDiscrepancy :
      cltBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        knownScoreBridge.matching_discrepancy_negligible)
    (estimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimatedScoreBridge.known_score_asymptotic_normality)
    (parameters : Finset Param)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle : Index -> Sample -> Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Index -> Sample -> Param -> Param -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm parameters firstStepLoading
            (scoreCovariance index sample))
        l (fun _sample => projectionLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (scoreQuadraticForm parameters firstStepLoading
                  (scoreCovariance index sample)) 0))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw) :
    PATEFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_fixedLaw_projection_lt_limit
    (pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    parameters scaledStatistic oracle firstStepLoading scoreCovariance limit
    oracleLimit projectionLimit horacle hprojection
    hprojectionLimit_lt_oracle hinverse_meas estimatedScoreToScaledTendsto

/--
Build a fixed-law PATE score-adjusted strict projection-slack bridge from a
local-experiment estimated-score input instead of an opaque packaged bridge.
-/
noncomputable def
    pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_fixedLaw_projection_lt_limit_glivenkoCantelli_local_experiment_input
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (finiteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicatorBridge.weighted_indicator_sum_lln)
    (cltBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge Cell)
    (finiteConditionsToScaled :
      indicatorBridge.eventual_finite_conditions ->
        cltBridge.indicator_bridge.eventual_finite_conditions)
    (envelopeToScaled :
      indicatorBridge.envelope_convergence ->
        cltBridge.indicator_bridge.envelope_convergence)
    (indicatorLLNToScaled :
      indicatorBridge.weighted_indicator_sum_lln ->
        cltBridge.indicator_bridge.weighted_indicator_sum_lln)
    (knownScoreBridge : KnownScoreAsymptoticBridge)
    (scaledApproximationToMatchingDiscrepancy :
      cltBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        knownScoreBridge.matching_discrepancy_negligible)
    (estimated : EstimatedScoreLocalExperimentInput)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (parameters : Finset Param)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle : Index -> Sample -> Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Index -> Sample -> Param -> Param -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm parameters firstStepLoading
            (scoreCovariance index sample))
        l (fun _sample => projectionLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (scoreQuadraticForm parameters firstStepLoading
                  (scoreCovariance index sample)) 0))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw) :
    PATEFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_fixedLaw_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
    envelopeToScaled indicatorLLNToScaled knownScoreBridge
    scaledApproximationToMatchingDiscrepancy
    (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated)
    knownScoreToEstimatedScoreInput parameters scaledStatistic oracle
    firstStepLoading scoreCovariance limit oracleLimit projectionLimit
    horacle hprojection hprojectionLimit_lt_oracle hinverse_meas
    estimatedScoreToScaledTendsto

/-! ## PATT constructors -/

/--
Build a PATT component-positive estimated-score studentized bridge from
GC-backed finite score-cell inputs, strict projection slack, and nonnegative
target drift.
-/
def
    pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_lt_limit_glivenkoCantelli
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (finiteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicatorBridge.weighted_indicator_sum_lln)
    (cltBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge Cell)
    (finiteConditionsToScaled :
      indicatorBridge.eventual_finite_conditions ->
        cltBridge.indicator_bridge.eventual_finite_conditions)
    (envelopeToScaled :
      indicatorBridge.envelope_convergence ->
        cltBridge.indicator_bridge.envelope_convergence)
    (indicatorLLNToScaled :
      indicatorBridge.weighted_indicator_sum_lln ->
        cltBridge.indicator_bridge.weighted_indicator_sum_lln)
    (knownScoreBridge : KnownScoreAsymptoticBridge)
    (scaledApproximationToMatchingDiscrepancy :
      cltBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        knownScoreBridge.matching_discrepancy_negligible)
    (estimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimatedScoreBridge.known_score_asymptotic_normality)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hdriftLimit_nonneg : 0 ≤ targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw) :
    PATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_lt_limit
    (pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    scaledStatistic oracle projectionReduction targetDrift limit oracleLimit
    projectionLimit targetDriftLimit horacle hprojection hdrift
    hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
    estimatedScoreToScaledTendsto

/--
Build a PATT component-positive estimated-score studentized bridge from
GC-backed finite score-cell inputs, weak projection slack, and positive target
drift.
-/
def
    pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_le_drift_pos_limit_glivenkoCantelli
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (finiteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicatorBridge.weighted_indicator_sum_lln)
    (cltBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge Cell)
    (finiteConditionsToScaled :
      indicatorBridge.eventual_finite_conditions ->
        cltBridge.indicator_bridge.eventual_finite_conditions)
    (envelopeToScaled :
      indicatorBridge.envelope_convergence ->
        cltBridge.indicator_bridge.envelope_convergence)
    (indicatorLLNToScaled :
      indicatorBridge.weighted_indicator_sum_lln ->
        cltBridge.indicator_bridge.weighted_indicator_sum_lln)
    (knownScoreBridge : KnownScoreAsymptoticBridge)
    (scaledApproximationToMatchingDiscrepancy :
      cltBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        knownScoreBridge.matching_discrepancy_negligible)
    (estimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimatedScoreBridge.known_score_asymptotic_normality)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_le_oracle : projectionLimit ≤ oracleLimit)
    (hdriftLimit_pos : 0 < targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw) :
    PATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_le_drift_pos_limit
    (pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    scaledStatistic oracle projectionReduction targetDrift limit oracleLimit
    projectionLimit targetDriftLimit horacle hprojection hdrift
    hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
    estimatedScoreToScaledTendsto

/--
Build a fixed-law PATT component-positive estimated-score studentized bridge
from GC-backed finite score-cell inputs and strict projection slack.
-/
def
    pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (finiteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicatorBridge.weighted_indicator_sum_lln)
    (cltBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge Cell)
    (finiteConditionsToScaled :
      indicatorBridge.eventual_finite_conditions ->
        cltBridge.indicator_bridge.eventual_finite_conditions)
    (envelopeToScaled :
      indicatorBridge.envelope_convergence ->
        cltBridge.indicator_bridge.envelope_convergence)
    (indicatorLLNToScaled :
      indicatorBridge.weighted_indicator_sum_lln ->
        cltBridge.indicator_bridge.weighted_indicator_sum_lln)
    (knownScoreBridge : KnownScoreAsymptoticBridge)
    (scaledApproximationToMatchingDiscrepancy :
      cltBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        knownScoreBridge.matching_discrepancy_negligible)
    (estimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimatedScoreBridge.known_score_asymptotic_normality)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw) :
    PATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_fixedLaw_projection_lt_limit
    (pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    scaledStatistic oracle projectionReduction limit oracleLimit
    projectionLimit horacle hprojection hprojectionLimit_lt_oracle
    hinverse_meas estimatedScoreToScaledTendsto

/--
Build a PATT component-positive estimated-score studentized bridge from
GC-backed finite score-cell inputs and score-quadratic strict projection slack.
-/
noncomputable def
    pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_projection_lt_limit_glivenkoCantelli
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (finiteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicatorBridge.weighted_indicator_sum_lln)
    (cltBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge Cell)
    (finiteConditionsToScaled :
      indicatorBridge.eventual_finite_conditions ->
        cltBridge.indicator_bridge.eventual_finite_conditions)
    (envelopeToScaled :
      indicatorBridge.envelope_convergence ->
        cltBridge.indicator_bridge.envelope_convergence)
    (indicatorLLNToScaled :
      indicatorBridge.weighted_indicator_sum_lln ->
        cltBridge.indicator_bridge.weighted_indicator_sum_lln)
    (knownScoreBridge : KnownScoreAsymptoticBridge)
    (scaledApproximationToMatchingDiscrepancy :
      cltBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        knownScoreBridge.matching_discrepancy_negligible)
    (estimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimatedScoreBridge.known_score_asymptotic_normality)
    (parameters : Finset Param)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle : Index -> Sample -> Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Index -> Sample -> Param -> Param -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm parameters firstStepLoading
            (scoreCovariance index sample))
        l (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm parameters targetDriftLoading
            (scoreCovariance index sample))
        l (fun _sample => targetDriftLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hdriftLimit_nonneg : 0 ≤ targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (scoreQuadraticForm parameters firstStepLoading
                  (scoreCovariance index sample))
                (scoreQuadraticForm parameters targetDriftLoading
                  (scoreCovariance index sample))))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw) :
    PATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_projection_lt_limit
    (pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    parameters scaledStatistic oracle firstStepLoading targetDriftLoading
    scoreCovariance limit oracleLimit projectionLimit targetDriftLimit
    horacle hprojection hdrift hprojectionLimit_lt_oracle
    hdriftLimit_nonneg hinverse_meas estimatedScoreToScaledTendsto

/--
Build a PATT score-adjusted strict projection-slack bridge from a
local-experiment estimated-score input instead of an opaque packaged bridge.
-/
noncomputable def
    pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_projection_lt_limit_glivenkoCantelli_local_experiment_input
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (finiteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicatorBridge.weighted_indicator_sum_lln)
    (cltBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge Cell)
    (finiteConditionsToScaled :
      indicatorBridge.eventual_finite_conditions ->
        cltBridge.indicator_bridge.eventual_finite_conditions)
    (envelopeToScaled :
      indicatorBridge.envelope_convergence ->
        cltBridge.indicator_bridge.envelope_convergence)
    (indicatorLLNToScaled :
      indicatorBridge.weighted_indicator_sum_lln ->
        cltBridge.indicator_bridge.weighted_indicator_sum_lln)
    (knownScoreBridge : KnownScoreAsymptoticBridge)
    (scaledApproximationToMatchingDiscrepancy :
      cltBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        knownScoreBridge.matching_discrepancy_negligible)
    (estimated : EstimatedScoreLocalExperimentInput)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (parameters : Finset Param)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle : Index -> Sample -> Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Index -> Sample -> Param -> Param -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm parameters firstStepLoading
            (scoreCovariance index sample))
        l (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm parameters targetDriftLoading
            (scoreCovariance index sample))
        l (fun _sample => targetDriftLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hdriftLimit_nonneg : 0 ≤ targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (scoreQuadraticForm parameters firstStepLoading
                  (scoreCovariance index sample))
                (scoreQuadraticForm parameters targetDriftLoading
                  (scoreCovariance index sample))))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw) :
    PATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
    envelopeToScaled indicatorLLNToScaled knownScoreBridge
    scaledApproximationToMatchingDiscrepancy
    (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated)
    knownScoreToEstimatedScoreInput parameters scaledStatistic oracle
    firstStepLoading targetDriftLoading scoreCovariance limit oracleLimit
    projectionLimit targetDriftLimit horacle hprojection hdrift
    hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
    estimatedScoreToScaledTendsto

/--
Build a PATT component-positive estimated-score studentized bridge from
GC-backed finite score-cell inputs, score-quadratic weak projection slack, and
positive target-drift limit.
-/
noncomputable def
    pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_projection_le_drift_pos_limit_glivenkoCantelli
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (finiteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicatorBridge.weighted_indicator_sum_lln)
    (cltBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge Cell)
    (finiteConditionsToScaled :
      indicatorBridge.eventual_finite_conditions ->
        cltBridge.indicator_bridge.eventual_finite_conditions)
    (envelopeToScaled :
      indicatorBridge.envelope_convergence ->
        cltBridge.indicator_bridge.envelope_convergence)
    (indicatorLLNToScaled :
      indicatorBridge.weighted_indicator_sum_lln ->
        cltBridge.indicator_bridge.weighted_indicator_sum_lln)
    (knownScoreBridge : KnownScoreAsymptoticBridge)
    (scaledApproximationToMatchingDiscrepancy :
      cltBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        knownScoreBridge.matching_discrepancy_negligible)
    (estimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimatedScoreBridge.known_score_asymptotic_normality)
    (parameters : Finset Param)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle : Index -> Sample -> Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Index -> Sample -> Param -> Param -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm parameters firstStepLoading
            (scoreCovariance index sample))
        l (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm parameters targetDriftLoading
            (scoreCovariance index sample))
        l (fun _sample => targetDriftLimit))
    (hprojectionLimit_le_oracle : projectionLimit ≤ oracleLimit)
    (hdriftLimit_pos : 0 < targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (scoreQuadraticForm parameters firstStepLoading
                  (scoreCovariance index sample))
                (scoreQuadraticForm parameters targetDriftLoading
                  (scoreCovariance index sample))))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw) :
    PATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_projection_le_drift_pos_limit
    (pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    parameters scaledStatistic oracle firstStepLoading targetDriftLoading
    scoreCovariance limit oracleLimit projectionLimit targetDriftLimit
    horacle hprojection hdrift hprojectionLimit_le_oracle
    hdriftLimit_pos hinverse_meas estimatedScoreToScaledTendsto

/--
Build a PATT score-adjusted weak projection-slack positive-drift bridge from a
local-experiment estimated-score input instead of an opaque packaged bridge.
-/
noncomputable def
    pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_projection_le_drift_pos_limit_glivenkoCantelli_local_experiment_input
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (finiteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicatorBridge.weighted_indicator_sum_lln)
    (cltBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge Cell)
    (finiteConditionsToScaled :
      indicatorBridge.eventual_finite_conditions ->
        cltBridge.indicator_bridge.eventual_finite_conditions)
    (envelopeToScaled :
      indicatorBridge.envelope_convergence ->
        cltBridge.indicator_bridge.envelope_convergence)
    (indicatorLLNToScaled :
      indicatorBridge.weighted_indicator_sum_lln ->
        cltBridge.indicator_bridge.weighted_indicator_sum_lln)
    (knownScoreBridge : KnownScoreAsymptoticBridge)
    (scaledApproximationToMatchingDiscrepancy :
      cltBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        knownScoreBridge.matching_discrepancy_negligible)
    (estimated : EstimatedScoreLocalExperimentInput)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (parameters : Finset Param)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle : Index -> Sample -> Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Index -> Sample -> Param -> Param -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm parameters firstStepLoading
            (scoreCovariance index sample))
        l (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm parameters targetDriftLoading
            (scoreCovariance index sample))
        l (fun _sample => targetDriftLimit))
    (hprojectionLimit_le_oracle : projectionLimit ≤ oracleLimit)
    (hdriftLimit_pos : 0 < targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (scoreQuadraticForm parameters firstStepLoading
                  (scoreCovariance index sample))
                (scoreQuadraticForm parameters targetDriftLoading
                  (scoreCovariance index sample))))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw) :
    PATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_projection_le_drift_pos_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
    envelopeToScaled indicatorLLNToScaled knownScoreBridge
    scaledApproximationToMatchingDiscrepancy
    (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated)
    knownScoreToEstimatedScoreInput parameters scaledStatistic oracle
    firstStepLoading targetDriftLoading scoreCovariance limit oracleLimit
    projectionLimit targetDriftLimit horacle hprojection hdrift
    hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
    estimatedScoreToScaledTendsto

/--
Build a fixed-law PATT component-positive estimated-score studentized bridge
from GC-backed finite score-cell inputs and score-quadratic strict projection
slack.
-/
noncomputable def
    pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_fixedLaw_projection_lt_limit_glivenkoCantelli
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (finiteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicatorBridge.weighted_indicator_sum_lln)
    (cltBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge Cell)
    (finiteConditionsToScaled :
      indicatorBridge.eventual_finite_conditions ->
        cltBridge.indicator_bridge.eventual_finite_conditions)
    (envelopeToScaled :
      indicatorBridge.envelope_convergence ->
        cltBridge.indicator_bridge.envelope_convergence)
    (indicatorLLNToScaled :
      indicatorBridge.weighted_indicator_sum_lln ->
        cltBridge.indicator_bridge.weighted_indicator_sum_lln)
    (knownScoreBridge : KnownScoreAsymptoticBridge)
    (scaledApproximationToMatchingDiscrepancy :
      cltBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        knownScoreBridge.matching_discrepancy_negligible)
    (estimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimatedScoreBridge.known_score_asymptotic_normality)
    (parameters : Finset Param)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle : Index -> Sample -> Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Index -> Sample -> Param -> Param -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm parameters firstStepLoading
            (scoreCovariance index sample))
        l (fun _sample => projectionLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (scoreQuadraticForm parameters firstStepLoading
                  (scoreCovariance index sample)) 0))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw) :
    PATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_fixedLaw_projection_lt_limit
    (pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    parameters scaledStatistic oracle firstStepLoading scoreCovariance limit
    oracleLimit projectionLimit horacle hprojection
    hprojectionLimit_lt_oracle hinverse_meas estimatedScoreToScaledTendsto

/--
Build a fixed-law PATT component-positive estimated-score studentized bridge
from a local-experiment estimated-score input instead of an opaque packaged
bridge.
-/
noncomputable def
    pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_fixedLaw_projection_lt_limit_glivenkoCantelli_local_experiment_input
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (indicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (finiteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).cellwise_weighted_indicator_sum_lln ->
        indicatorBridge.weighted_indicator_sum_lln)
    (cltBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge Cell)
    (finiteConditionsToScaled :
      indicatorBridge.eventual_finite_conditions ->
        cltBridge.indicator_bridge.eventual_finite_conditions)
    (envelopeToScaled :
      indicatorBridge.envelope_convergence ->
        cltBridge.indicator_bridge.envelope_convergence)
    (indicatorLLNToScaled :
      indicatorBridge.weighted_indicator_sum_lln ->
        cltBridge.indicator_bridge.weighted_indicator_sum_lln)
    (knownScoreBridge : KnownScoreAsymptoticBridge)
    (scaledApproximationToMatchingDiscrepancy :
      cltBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        knownScoreBridge.matching_discrepancy_negligible)
    (estimated : EstimatedScoreLocalExperimentInput)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (parameters : Finset Param)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle : Index -> Sample -> Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Index -> Sample -> Param -> Param -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm parameters firstStepLoading
            (scoreCovariance index sample))
        l (fun _sample => projectionLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (scoreQuadraticForm parameters firstStepLoading
                  (scoreCovariance index sample)) 0))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw) :
    PATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_fixedLaw_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
    envelopeToScaled indicatorLLNToScaled knownScoreBridge
    scaledApproximationToMatchingDiscrepancy
    (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated)
    knownScoreToEstimatedScoreInput parameters scaledStatistic oracle
    firstStepLoading scoreCovariance limit oracleLimit projectionLimit
    horacle hprojection hprojectionLimit_lt_oracle hinverse_meas
    estimatedScoreToScaledTendsto

end WDSM
end Matching
end StatInference
