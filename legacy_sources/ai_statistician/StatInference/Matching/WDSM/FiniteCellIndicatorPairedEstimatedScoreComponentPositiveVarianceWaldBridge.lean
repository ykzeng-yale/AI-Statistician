import StatInference.Matching.WDSM.FiniteCellIndicatorPairedEstimatedScoreComponentPositiveVarianceStudentizedBridge
import StatInference.Matching.WDSM.FiniteCellIndicatorPairedEstimatedScorePositiveVarianceWaldBridge

/-!
# Paired estimated-score Wald bridges from component positivity

This module packages the paired component-positive estimated-score
studentization constructors into the paired finite score-cell Wald bridge
objects.  It lets the final paired Wald layer start from PATE/PATT
component-level variance positivity rather than from a manually assembled
paired positive-variance studentization bridge.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open scoped Topology

variable {PATECell PATTCell Index Sample LimitSample : Type*}
variable [DecidableEq PATECell] [DecidableEq PATTCell]
variable {PATEParam PATTParam : Type*}
variable [DecidableEq PATEParam] [DecidableEq PATTParam]
variable [MeasurableSpace Sample] [MeasurableSpace LimitSample]
variable {sampleLaw : MeasureTheory.Measure Sample}
variable {limitLaw : MeasureTheory.Measure LimitSample}
variable [MeasureTheory.IsProbabilityMeasure sampleLaw]
variable [MeasureTheory.IsProbabilityMeasure limitLaw]
variable {l : Filter Index}
variable [l.IsCountablyGenerated]

/-- Package a paired positive-variance studentized bridge with absolute Wald inputs. -/
def patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_studentized
    (studentized_bridge :
      PATEPATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge
        PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l where
  studentized_bridge := studentized_bridge
  pate_coverage_input := pate_coverage_input
  patt_coverage_input := patt_coverage_input

/-- Package a paired positive-variance studentized bridge with two-sided Wald inputs. -/
def patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_studentized
    (studentized_bridge :
      PATEPATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge
        PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l where
  studentized_bridge := studentized_bridge
  pate_coverage_input := pate_coverage_input
  patt_coverage_input := patt_coverage_input

/--
Paired absolute Wald bridge where both estimated-score limiting variances are
positive by strict projection slack and nonnegative target drift.
-/
def patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_lt_limit
    (finite_estimated_bridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell PATTCell)
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_driftLimit_nonneg : 0 ≤ pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pate_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_driftLimit_nonneg : 0 ≤ patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (patt_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_studentized
    (patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_lt_limit
      finite_estimated_bridge pate_scaledStatistic pate_oracle
      pate_projectionReduction pate_targetDrift pate_limit pate_oracleLimit
      pate_projectionLimit pate_targetDriftLimit hpate_oracle
      hpate_projection hpate_drift hpate_projectionLimit_lt_oracle
      hpate_driftLimit_nonneg hpate_inverse_meas
      pate_estimated_score_to_scaled_tendsto patt_scaledStatistic patt_oracle
      patt_projectionReduction patt_targetDrift patt_limit patt_oracleLimit
      patt_projectionLimit patt_targetDriftLimit hpatt_oracle
      hpatt_projection hpatt_drift hpatt_projectionLimit_lt_oracle
      hpatt_driftLimit_nonneg hpatt_inverse_meas
      patt_estimated_score_to_scaled_tendsto)
    pate_coverage_input patt_coverage_input

/--
Paired absolute Wald bridge with score-quadratic projection and target-drift
reductions for both arms under strict projection slack.
-/
noncomputable def patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_scoreAdjusted_projection_lt_limit
    (finite_estimated_bridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell PATTCell)
    (pateParameters : Finset PATEParam)
    (pattParameters : Finset PATTParam)
    (pate_scaledStatistic patt_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle patt_oracle : Index -> Sample -> Real)
    (pateFirstStepLoading pateTargetDriftLoading : PATEParam -> Real)
    (pattFirstStepLoading pattTargetDriftLoading : PATTParam -> Real)
    (pateScoreCovariance :
      Index -> Sample -> PATEParam -> PATEParam -> Real)
    (pattScoreCovariance :
      Index -> Sample -> PATTParam -> PATTParam -> Real)
    (pate_limit patt_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pateParameters pateFirstStepLoading
            (pateScoreCovariance index sample))
        l (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pateParameters pateTargetDriftLoading
            (pateScoreCovariance index sample))
        l (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_driftLimit_nonneg : 0 ≤ pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (scoreQuadraticForm pateParameters pateFirstStepLoading
                  (pateScoreCovariance index sample))
                (scoreQuadraticForm pateParameters pateTargetDriftLoading
                  (pateScoreCovariance index sample))))⁻¹)
          sampleLaw)
    (pate_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pattParameters pattFirstStepLoading
            (pattScoreCovariance index sample))
        l (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pattParameters pattTargetDriftLoading
            (pattScoreCovariance index sample))
        l (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_driftLimit_nonneg : 0 ≤ patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (scoreQuadraticForm pattParameters pattFirstStepLoading
                  (pattScoreCovariance index sample))
                (scoreQuadraticForm pattParameters pattTargetDriftLoading
                  (pattScoreCovariance index sample))))⁻¹)
          sampleLaw)
    (patt_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_studentized
    (patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_projection_lt_limit
      finite_estimated_bridge pateParameters pattParameters
      pate_scaledStatistic patt_scaledStatistic pate_oracle patt_oracle
      pateFirstStepLoading pateTargetDriftLoading pattFirstStepLoading
      pattTargetDriftLoading pateScoreCovariance pattScoreCovariance
      pate_limit patt_limit pate_oracleLimit pate_projectionLimit
      pate_targetDriftLimit patt_oracleLimit patt_projectionLimit
      patt_targetDriftLimit hpate_oracle hpate_projection hpate_drift
      hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
      hpate_inverse_meas hpatt_oracle hpatt_projection hpatt_drift
      hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
      hpatt_inverse_meas pate_estimated_score_to_scaled_tendsto
      patt_estimated_score_to_scaled_tendsto)
    pate_coverage_input patt_coverage_input

/--
Paired two-sided Wald bridge from absolute calibration inputs, with
score-quadratic projection and target-drift reductions for both arms under
strict projection slack.
-/
noncomputable def patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_scoreAdjusted_projection_lt_limit
    (finite_estimated_bridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell PATTCell)
    (pateParameters : Finset PATEParam)
    (pattParameters : Finset PATTParam)
    (pate_scaledStatistic patt_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle patt_oracle : Index -> Sample -> Real)
    (pateFirstStepLoading pateTargetDriftLoading : PATEParam -> Real)
    (pattFirstStepLoading pattTargetDriftLoading : PATTParam -> Real)
    (pateScoreCovariance :
      Index -> Sample -> PATEParam -> PATEParam -> Real)
    (pattScoreCovariance :
      Index -> Sample -> PATTParam -> PATTParam -> Real)
    (pate_limit patt_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pateParameters pateFirstStepLoading
            (pateScoreCovariance index sample))
        l (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pateParameters pateTargetDriftLoading
            (pateScoreCovariance index sample))
        l (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_driftLimit_nonneg : 0 ≤ pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (scoreQuadraticForm pateParameters pateFirstStepLoading
                  (pateScoreCovariance index sample))
                (scoreQuadraticForm pateParameters pateTargetDriftLoading
                  (pateScoreCovariance index sample))))⁻¹)
          sampleLaw)
    (pate_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pattParameters pattFirstStepLoading
            (pattScoreCovariance index sample))
        l (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pattParameters pattTargetDriftLoading
            (pattScoreCovariance index sample))
        l (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_driftLimit_nonneg : 0 ≤ patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (scoreQuadraticForm pattParameters pattFirstStepLoading
                  (pattScoreCovariance index sample))
                (scoreQuadraticForm pattParameters pattTargetDriftLoading
                  (pattScoreCovariance index sample))))⁻¹)
          sampleLaw)
    (patt_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute
    (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_scoreAdjusted_projection_lt_limit
      finite_estimated_bridge pateParameters pattParameters
      pate_scaledStatistic patt_scaledStatistic pate_oracle patt_oracle
      pateFirstStepLoading pateTargetDriftLoading pattFirstStepLoading
      pattTargetDriftLoading pateScoreCovariance pattScoreCovariance
      pate_limit patt_limit pate_oracleLimit pate_projectionLimit
      pate_targetDriftLimit patt_oracleLimit patt_projectionLimit
      patt_targetDriftLimit hpate_oracle hpate_projection hpate_drift
      hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
      hpate_inverse_meas pate_estimated_score_to_scaled_tendsto
      hpatt_oracle hpatt_projection hpatt_drift
      hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
      hpatt_inverse_meas patt_estimated_score_to_scaled_tendsto
      pate_coverage_input patt_coverage_input)

/--
Paired two-sided Wald bridge with score-quadratic projection and target-drift
reductions for both arms under strict projection slack.
-/
noncomputable def patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_scoreAdjusted_projection_lt_limit
    (finite_estimated_bridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell PATTCell)
    (pateParameters : Finset PATEParam)
    (pattParameters : Finset PATTParam)
    (pate_scaledStatistic patt_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle patt_oracle : Index -> Sample -> Real)
    (pateFirstStepLoading pateTargetDriftLoading : PATEParam -> Real)
    (pattFirstStepLoading pattTargetDriftLoading : PATTParam -> Real)
    (pateScoreCovariance :
      Index -> Sample -> PATEParam -> PATEParam -> Real)
    (pattScoreCovariance :
      Index -> Sample -> PATTParam -> PATTParam -> Real)
    (pate_limit patt_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pateParameters pateFirstStepLoading
            (pateScoreCovariance index sample))
        l (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pateParameters pateTargetDriftLoading
            (pateScoreCovariance index sample))
        l (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_driftLimit_nonneg : 0 ≤ pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (scoreQuadraticForm pateParameters pateFirstStepLoading
                  (pateScoreCovariance index sample))
                (scoreQuadraticForm pateParameters pateTargetDriftLoading
                  (pateScoreCovariance index sample))))⁻¹)
          sampleLaw)
    (pate_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pattParameters pattFirstStepLoading
            (pattScoreCovariance index sample))
        l (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pattParameters pattTargetDriftLoading
            (pattScoreCovariance index sample))
        l (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_driftLimit_nonneg : 0 ≤ patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (scoreQuadraticForm pattParameters pattFirstStepLoading
                  (pattScoreCovariance index sample))
                (scoreQuadraticForm pattParameters pattTargetDriftLoading
                  (pattScoreCovariance index sample))))⁻¹)
          sampleLaw)
    (patt_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_studentized
    (patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_projection_lt_limit
      finite_estimated_bridge pateParameters pattParameters
      pate_scaledStatistic patt_scaledStatistic pate_oracle patt_oracle
      pateFirstStepLoading pateTargetDriftLoading pattFirstStepLoading
      pattTargetDriftLoading pateScoreCovariance pattScoreCovariance
      pate_limit patt_limit pate_oracleLimit pate_projectionLimit
      pate_targetDriftLimit patt_oracleLimit patt_projectionLimit
      patt_targetDriftLimit hpate_oracle hpate_projection hpate_drift
      hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
      hpate_inverse_meas hpatt_oracle hpatt_projection hpatt_drift
      hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
      hpatt_inverse_meas pate_estimated_score_to_scaled_tendsto
      patt_estimated_score_to_scaled_tendsto)
    pate_coverage_input patt_coverage_input

/--
Paired absolute Wald bridge with score-quadratic reductions for both arms
under weak projection slack and positive target-drift limits.
-/
noncomputable def patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_scoreAdjusted_projection_le_drift_pos_limit
    (finite_estimated_bridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell PATTCell)
    (pateParameters : Finset PATEParam)
    (pattParameters : Finset PATTParam)
    (pate_scaledStatistic patt_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle patt_oracle : Index -> Sample -> Real)
    (pateFirstStepLoading pateTargetDriftLoading : PATEParam -> Real)
    (pattFirstStepLoading pattTargetDriftLoading : PATTParam -> Real)
    (pateScoreCovariance :
      Index -> Sample -> PATEParam -> PATEParam -> Real)
    (pattScoreCovariance :
      Index -> Sample -> PATTParam -> PATTParam -> Real)
    (pate_limit patt_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pateParameters pateFirstStepLoading
            (pateScoreCovariance index sample))
        l (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pateParameters pateTargetDriftLoading
            (pateScoreCovariance index sample))
        l (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_le_oracle :
      pate_projectionLimit ≤ pate_oracleLimit)
    (hpate_driftLimit_pos : 0 < pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (scoreQuadraticForm pateParameters pateFirstStepLoading
                  (pateScoreCovariance index sample))
                (scoreQuadraticForm pateParameters pateTargetDriftLoading
                  (pateScoreCovariance index sample))))⁻¹)
          sampleLaw)
    (pate_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pattParameters pattFirstStepLoading
            (pattScoreCovariance index sample))
        l (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pattParameters pattTargetDriftLoading
            (pattScoreCovariance index sample))
        l (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_le_oracle :
      patt_projectionLimit ≤ patt_oracleLimit)
    (hpatt_driftLimit_pos : 0 < patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (scoreQuadraticForm pattParameters pattFirstStepLoading
                  (pattScoreCovariance index sample))
                (scoreQuadraticForm pattParameters pattTargetDriftLoading
                  (pattScoreCovariance index sample))))⁻¹)
          sampleLaw)
    (patt_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_studentized
    (patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_projection_le_drift_pos_limit
      finite_estimated_bridge pateParameters pattParameters
      pate_scaledStatistic patt_scaledStatistic pate_oracle patt_oracle
      pateFirstStepLoading pateTargetDriftLoading pattFirstStepLoading
      pattTargetDriftLoading pateScoreCovariance pattScoreCovariance
      pate_limit patt_limit pate_oracleLimit pate_projectionLimit
      pate_targetDriftLimit patt_oracleLimit patt_projectionLimit
      patt_targetDriftLimit hpate_oracle hpate_projection hpate_drift
      hpate_projectionLimit_le_oracle hpate_driftLimit_pos
      hpate_inverse_meas hpatt_oracle hpatt_projection hpatt_drift
      hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
      hpatt_inverse_meas pate_estimated_score_to_scaled_tendsto
      patt_estimated_score_to_scaled_tendsto)
    pate_coverage_input patt_coverage_input

/--
Paired two-sided Wald bridge from absolute calibration inputs, with
score-quadratic reductions for both arms under weak projection slack and
positive target-drift limits.
-/
noncomputable def patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_scoreAdjusted_projection_le_drift_pos_limit
    (finite_estimated_bridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell PATTCell)
    (pateParameters : Finset PATEParam)
    (pattParameters : Finset PATTParam)
    (pate_scaledStatistic patt_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle patt_oracle : Index -> Sample -> Real)
    (pateFirstStepLoading pateTargetDriftLoading : PATEParam -> Real)
    (pattFirstStepLoading pattTargetDriftLoading : PATTParam -> Real)
    (pateScoreCovariance :
      Index -> Sample -> PATEParam -> PATEParam -> Real)
    (pattScoreCovariance :
      Index -> Sample -> PATTParam -> PATTParam -> Real)
    (pate_limit patt_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pateParameters pateFirstStepLoading
            (pateScoreCovariance index sample))
        l (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pateParameters pateTargetDriftLoading
            (pateScoreCovariance index sample))
        l (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_le_oracle :
      pate_projectionLimit ≤ pate_oracleLimit)
    (hpate_driftLimit_pos : 0 < pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (scoreQuadraticForm pateParameters pateFirstStepLoading
                  (pateScoreCovariance index sample))
                (scoreQuadraticForm pateParameters pateTargetDriftLoading
                  (pateScoreCovariance index sample))))⁻¹)
          sampleLaw)
    (pate_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pattParameters pattFirstStepLoading
            (pattScoreCovariance index sample))
        l (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pattParameters pattTargetDriftLoading
            (pattScoreCovariance index sample))
        l (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_le_oracle :
      patt_projectionLimit ≤ patt_oracleLimit)
    (hpatt_driftLimit_pos : 0 < patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (scoreQuadraticForm pattParameters pattFirstStepLoading
                  (pattScoreCovariance index sample))
                (scoreQuadraticForm pattParameters pattTargetDriftLoading
                  (pattScoreCovariance index sample))))⁻¹)
          sampleLaw)
    (patt_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute
    (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_scoreAdjusted_projection_le_drift_pos_limit
      finite_estimated_bridge pateParameters pattParameters
      pate_scaledStatistic patt_scaledStatistic pate_oracle patt_oracle
      pateFirstStepLoading pateTargetDriftLoading pattFirstStepLoading
      pattTargetDriftLoading pateScoreCovariance pattScoreCovariance
      pate_limit patt_limit pate_oracleLimit pate_projectionLimit
      pate_targetDriftLimit patt_oracleLimit patt_projectionLimit
      patt_targetDriftLimit hpate_oracle hpate_projection hpate_drift
      hpate_projectionLimit_le_oracle hpate_driftLimit_pos
      hpate_inverse_meas pate_estimated_score_to_scaled_tendsto
      hpatt_oracle hpatt_projection hpatt_drift
      hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
      hpatt_inverse_meas patt_estimated_score_to_scaled_tendsto
      pate_coverage_input patt_coverage_input)

/--
Paired two-sided Wald bridge with score-quadratic reductions for both arms
under weak projection slack and positive target-drift limits.
-/
noncomputable def patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_scoreAdjusted_projection_le_drift_pos_limit
    (finite_estimated_bridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell PATTCell)
    (pateParameters : Finset PATEParam)
    (pattParameters : Finset PATTParam)
    (pate_scaledStatistic patt_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle patt_oracle : Index -> Sample -> Real)
    (pateFirstStepLoading pateTargetDriftLoading : PATEParam -> Real)
    (pattFirstStepLoading pattTargetDriftLoading : PATTParam -> Real)
    (pateScoreCovariance :
      Index -> Sample -> PATEParam -> PATEParam -> Real)
    (pattScoreCovariance :
      Index -> Sample -> PATTParam -> PATTParam -> Real)
    (pate_limit patt_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pateParameters pateFirstStepLoading
            (pateScoreCovariance index sample))
        l (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pateParameters pateTargetDriftLoading
            (pateScoreCovariance index sample))
        l (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_le_oracle :
      pate_projectionLimit ≤ pate_oracleLimit)
    (hpate_driftLimit_pos : 0 < pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (scoreQuadraticForm pateParameters pateFirstStepLoading
                  (pateScoreCovariance index sample))
                (scoreQuadraticForm pateParameters pateTargetDriftLoading
                  (pateScoreCovariance index sample))))⁻¹)
          sampleLaw)
    (pate_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pattParameters pattFirstStepLoading
            (pattScoreCovariance index sample))
        l (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pattParameters pattTargetDriftLoading
            (pattScoreCovariance index sample))
        l (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_le_oracle :
      patt_projectionLimit ≤ patt_oracleLimit)
    (hpatt_driftLimit_pos : 0 < patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (scoreQuadraticForm pattParameters pattFirstStepLoading
                  (pattScoreCovariance index sample))
                (scoreQuadraticForm pattParameters pattTargetDriftLoading
                  (pattScoreCovariance index sample))))⁻¹)
          sampleLaw)
    (patt_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_studentized
    (patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_projection_le_drift_pos_limit
      finite_estimated_bridge pateParameters pattParameters
      pate_scaledStatistic patt_scaledStatistic pate_oracle patt_oracle
      pateFirstStepLoading pateTargetDriftLoading pattFirstStepLoading
      pattTargetDriftLoading pateScoreCovariance pattScoreCovariance
      pate_limit patt_limit pate_oracleLimit pate_projectionLimit
      pate_targetDriftLimit patt_oracleLimit patt_projectionLimit
      patt_targetDriftLimit hpate_oracle hpate_projection hpate_drift
      hpate_projectionLimit_le_oracle hpate_driftLimit_pos
      hpate_inverse_meas hpatt_oracle hpatt_projection hpatt_drift
      hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
      hpatt_inverse_meas pate_estimated_score_to_scaled_tendsto
      patt_estimated_score_to_scaled_tendsto)
    pate_coverage_input patt_coverage_input

/--
Paired absolute Wald bridge with fixed-law score-quadratic projection
reductions for both arms under strict projection slack.
-/
noncomputable def patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_scoreAdjusted_fixedLaw_projection_lt_limit
    (finite_estimated_bridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell PATTCell)
    (pateParameters : Finset PATEParam)
    (pattParameters : Finset PATTParam)
    (pate_scaledStatistic patt_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle patt_oracle : Index -> Sample -> Real)
    (pateFirstStepLoading : PATEParam -> Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pateScoreCovariance :
      Index -> Sample -> PATEParam -> PATEParam -> Real)
    (pattScoreCovariance :
      Index -> Sample -> PATTParam -> PATTParam -> Real)
    (pate_limit patt_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit : Real)
    (patt_oracleLimit patt_projectionLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pateParameters pateFirstStepLoading
            (pateScoreCovariance index sample))
        l (fun _sample => pate_projectionLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (scoreQuadraticForm pateParameters pateFirstStepLoading
                  (pateScoreCovariance index sample)) 0))⁻¹)
          sampleLaw)
    (pate_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pattParameters pattFirstStepLoading
            (pattScoreCovariance index sample))
        l (fun _sample => patt_projectionLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (scoreQuadraticForm pattParameters pattFirstStepLoading
                  (pattScoreCovariance index sample)) 0))⁻¹)
          sampleLaw)
    (patt_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_studentized
    (patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_fixedLaw_projection_lt_limit
      finite_estimated_bridge pateParameters pattParameters
      pate_scaledStatistic patt_scaledStatistic pate_oracle patt_oracle
      pateFirstStepLoading pattFirstStepLoading pateScoreCovariance
      pattScoreCovariance pate_limit patt_limit pate_oracleLimit
      pate_projectionLimit patt_oracleLimit patt_projectionLimit
      hpate_oracle hpate_projection hpate_projectionLimit_lt_oracle
      hpate_inverse_meas hpatt_oracle hpatt_projection
      hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
      pate_estimated_score_to_scaled_tendsto
      patt_estimated_score_to_scaled_tendsto)
    pate_coverage_input patt_coverage_input

/--
Paired two-sided Wald bridge from absolute calibration inputs, with fixed-law
score-quadratic projection reductions for both arms under strict projection
slack.
-/
noncomputable def patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_scoreAdjusted_fixedLaw_projection_lt_limit
    (finite_estimated_bridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell PATTCell)
    (pateParameters : Finset PATEParam)
    (pattParameters : Finset PATTParam)
    (pate_scaledStatistic patt_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle patt_oracle : Index -> Sample -> Real)
    (pateFirstStepLoading : PATEParam -> Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pateScoreCovariance :
      Index -> Sample -> PATEParam -> PATEParam -> Real)
    (pattScoreCovariance :
      Index -> Sample -> PATTParam -> PATTParam -> Real)
    (pate_limit patt_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit : Real)
    (patt_oracleLimit patt_projectionLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pateParameters pateFirstStepLoading
            (pateScoreCovariance index sample))
        l (fun _sample => pate_projectionLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (scoreQuadraticForm pateParameters pateFirstStepLoading
                  (pateScoreCovariance index sample)) 0))⁻¹)
          sampleLaw)
    (pate_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pattParameters pattFirstStepLoading
            (pattScoreCovariance index sample))
        l (fun _sample => patt_projectionLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (scoreQuadraticForm pattParameters pattFirstStepLoading
                  (pattScoreCovariance index sample)) 0))⁻¹)
          sampleLaw)
    (patt_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute
    (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_scoreAdjusted_fixedLaw_projection_lt_limit
      finite_estimated_bridge pateParameters pattParameters
      pate_scaledStatistic patt_scaledStatistic pate_oracle patt_oracle
      pateFirstStepLoading pattFirstStepLoading pateScoreCovariance
      pattScoreCovariance pate_limit patt_limit pate_oracleLimit
      pate_projectionLimit patt_oracleLimit patt_projectionLimit
      hpate_oracle hpate_projection hpate_projectionLimit_lt_oracle
      hpate_inverse_meas pate_estimated_score_to_scaled_tendsto
      hpatt_oracle hpatt_projection hpatt_projectionLimit_lt_oracle
      hpatt_inverse_meas patt_estimated_score_to_scaled_tendsto
      pate_coverage_input patt_coverage_input)

/--
Paired two-sided Wald bridge with fixed-law score-quadratic projection
reductions for both arms under strict projection slack.
-/
noncomputable def patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_scoreAdjusted_fixedLaw_projection_lt_limit
    (finite_estimated_bridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell PATTCell)
    (pateParameters : Finset PATEParam)
    (pattParameters : Finset PATTParam)
    (pate_scaledStatistic patt_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle patt_oracle : Index -> Sample -> Real)
    (pateFirstStepLoading : PATEParam -> Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pateScoreCovariance :
      Index -> Sample -> PATEParam -> PATEParam -> Real)
    (pattScoreCovariance :
      Index -> Sample -> PATTParam -> PATTParam -> Real)
    (pate_limit patt_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit : Real)
    (patt_oracleLimit patt_projectionLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pateParameters pateFirstStepLoading
            (pateScoreCovariance index sample))
        l (fun _sample => pate_projectionLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (scoreQuadraticForm pateParameters pateFirstStepLoading
                  (pateScoreCovariance index sample)) 0))⁻¹)
          sampleLaw)
    (pate_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pattParameters pattFirstStepLoading
            (pattScoreCovariance index sample))
        l (fun _sample => patt_projectionLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (scoreQuadraticForm pattParameters pattFirstStepLoading
                  (pattScoreCovariance index sample)) 0))⁻¹)
          sampleLaw)
    (patt_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_studentized
    (patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_fixedLaw_projection_lt_limit
      finite_estimated_bridge pateParameters pattParameters
      pate_scaledStatistic patt_scaledStatistic pate_oracle patt_oracle
      pateFirstStepLoading pattFirstStepLoading pateScoreCovariance
      pattScoreCovariance pate_limit patt_limit pate_oracleLimit
      pate_projectionLimit patt_oracleLimit patt_projectionLimit
      hpate_oracle hpate_projection hpate_projectionLimit_lt_oracle
      hpate_inverse_meas hpatt_oracle hpatt_projection
      hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
      pate_estimated_score_to_scaled_tendsto
      patt_estimated_score_to_scaled_tendsto)
    pate_coverage_input patt_coverage_input

/--
Paired absolute Wald bridge from two-sided calibration inputs, with
score-quadratic projection and target-drift reductions for both arms under
strict projection slack.
-/
noncomputable def patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_scoreAdjusted_projection_lt_limit
    (finite_estimated_bridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell PATTCell)
    (pateParameters : Finset PATEParam)
    (pattParameters : Finset PATTParam)
    (pate_scaledStatistic patt_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle patt_oracle : Index -> Sample -> Real)
    (pateFirstStepLoading pateTargetDriftLoading : PATEParam -> Real)
    (pattFirstStepLoading pattTargetDriftLoading : PATTParam -> Real)
    (pateScoreCovariance :
      Index -> Sample -> PATEParam -> PATEParam -> Real)
    (pattScoreCovariance :
      Index -> Sample -> PATTParam -> PATTParam -> Real)
    (pate_limit patt_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pateParameters pateFirstStepLoading
            (pateScoreCovariance index sample))
        l (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pateParameters pateTargetDriftLoading
            (pateScoreCovariance index sample))
        l (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_driftLimit_nonneg : 0 ≤ pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (scoreQuadraticForm pateParameters pateFirstStepLoading
                  (pateScoreCovariance index sample))
                (scoreQuadraticForm pateParameters pateTargetDriftLoading
                  (pateScoreCovariance index sample))))⁻¹)
          sampleLaw)
    (pate_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pattParameters pattFirstStepLoading
            (pattScoreCovariance index sample))
        l (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pattParameters pattTargetDriftLoading
            (pattScoreCovariance index sample))
        l (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_driftLimit_nonneg : 0 ≤ patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (scoreQuadraticForm pattParameters pattFirstStepLoading
                  (pattScoreCovariance index sample))
                (scoreQuadraticForm pattParameters pattTargetDriftLoading
                  (pattScoreCovariance index sample))))⁻¹)
          sampleLaw)
    (patt_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_scoreAdjusted_projection_lt_limit
    finite_estimated_bridge pateParameters pattParameters
    pate_scaledStatistic patt_scaledStatistic pate_oracle patt_oracle
    pateFirstStepLoading pateTargetDriftLoading pattFirstStepLoading
    pattTargetDriftLoading pateScoreCovariance pattScoreCovariance
    pate_limit patt_limit pate_oracleLimit pate_projectionLimit
    pate_targetDriftLimit patt_oracleLimit patt_projectionLimit
    patt_targetDriftLimit hpate_oracle hpate_projection hpate_drift
    hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
    hpate_inverse_meas pate_estimated_score_to_scaled_tendsto
    hpatt_oracle hpatt_projection hpatt_drift
    hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
    hpatt_inverse_meas patt_estimated_score_to_scaled_tendsto
    (absoluteWaldCoverageVarianceInput_of_twoSided pate_coverage_input)
    (absoluteWaldCoverageVarianceInput_of_twoSided patt_coverage_input)

/--
Paired absolute Wald bridge from two-sided calibration inputs, with
score-quadratic reductions for both arms under weak projection slack and
positive target-drift limits.
-/
noncomputable def patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_scoreAdjusted_projection_le_drift_pos_limit
    (finite_estimated_bridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell PATTCell)
    (pateParameters : Finset PATEParam)
    (pattParameters : Finset PATTParam)
    (pate_scaledStatistic patt_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle patt_oracle : Index -> Sample -> Real)
    (pateFirstStepLoading pateTargetDriftLoading : PATEParam -> Real)
    (pattFirstStepLoading pattTargetDriftLoading : PATTParam -> Real)
    (pateScoreCovariance :
      Index -> Sample -> PATEParam -> PATEParam -> Real)
    (pattScoreCovariance :
      Index -> Sample -> PATTParam -> PATTParam -> Real)
    (pate_limit patt_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pateParameters pateFirstStepLoading
            (pateScoreCovariance index sample))
        l (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pateParameters pateTargetDriftLoading
            (pateScoreCovariance index sample))
        l (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_le_oracle :
      pate_projectionLimit ≤ pate_oracleLimit)
    (hpate_driftLimit_pos : 0 < pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (scoreQuadraticForm pateParameters pateFirstStepLoading
                  (pateScoreCovariance index sample))
                (scoreQuadraticForm pateParameters pateTargetDriftLoading
                  (pateScoreCovariance index sample))))⁻¹)
          sampleLaw)
    (pate_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pattParameters pattFirstStepLoading
            (pattScoreCovariance index sample))
        l (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pattParameters pattTargetDriftLoading
            (pattScoreCovariance index sample))
        l (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_le_oracle :
      patt_projectionLimit ≤ patt_oracleLimit)
    (hpatt_driftLimit_pos : 0 < patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (scoreQuadraticForm pattParameters pattFirstStepLoading
                  (pattScoreCovariance index sample))
                (scoreQuadraticForm pattParameters pattTargetDriftLoading
                  (pattScoreCovariance index sample))))⁻¹)
          sampleLaw)
    (patt_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_scoreAdjusted_projection_le_drift_pos_limit
    finite_estimated_bridge pateParameters pattParameters
    pate_scaledStatistic patt_scaledStatistic pate_oracle patt_oracle
    pateFirstStepLoading pateTargetDriftLoading pattFirstStepLoading
    pattTargetDriftLoading pateScoreCovariance pattScoreCovariance
    pate_limit patt_limit pate_oracleLimit pate_projectionLimit
    pate_targetDriftLimit patt_oracleLimit patt_projectionLimit
    patt_targetDriftLimit hpate_oracle hpate_projection hpate_drift
    hpate_projectionLimit_le_oracle hpate_driftLimit_pos
    hpate_inverse_meas pate_estimated_score_to_scaled_tendsto
    hpatt_oracle hpatt_projection hpatt_drift
    hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
    hpatt_inverse_meas patt_estimated_score_to_scaled_tendsto
    (absoluteWaldCoverageVarianceInput_of_twoSided pate_coverage_input)
    (absoluteWaldCoverageVarianceInput_of_twoSided patt_coverage_input)

/--
Paired absolute Wald bridge from two-sided calibration inputs, with fixed-law
score-quadratic projection reductions for both arms under strict projection
slack.
-/
noncomputable def patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_scoreAdjusted_fixedLaw_projection_lt_limit
    (finite_estimated_bridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell PATTCell)
    (pateParameters : Finset PATEParam)
    (pattParameters : Finset PATTParam)
    (pate_scaledStatistic patt_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle patt_oracle : Index -> Sample -> Real)
    (pateFirstStepLoading : PATEParam -> Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pateScoreCovariance :
      Index -> Sample -> PATEParam -> PATEParam -> Real)
    (pattScoreCovariance :
      Index -> Sample -> PATTParam -> PATTParam -> Real)
    (pate_limit patt_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit : Real)
    (patt_oracleLimit patt_projectionLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pateParameters pateFirstStepLoading
            (pateScoreCovariance index sample))
        l (fun _sample => pate_projectionLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (scoreQuadraticForm pateParameters pateFirstStepLoading
                  (pateScoreCovariance index sample)) 0))⁻¹)
          sampleLaw)
    (pate_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pattParameters pattFirstStepLoading
            (pattScoreCovariance index sample))
        l (fun _sample => patt_projectionLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (scoreQuadraticForm pattParameters pattFirstStepLoading
                  (pattScoreCovariance index sample)) 0))⁻¹)
          sampleLaw)
    (patt_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_scoreAdjusted_fixedLaw_projection_lt_limit
    finite_estimated_bridge pateParameters pattParameters
    pate_scaledStatistic patt_scaledStatistic pate_oracle patt_oracle
    pateFirstStepLoading pattFirstStepLoading pateScoreCovariance
    pattScoreCovariance pate_limit patt_limit pate_oracleLimit
    pate_projectionLimit patt_oracleLimit patt_projectionLimit
    hpate_oracle hpate_projection hpate_projectionLimit_lt_oracle
    hpate_inverse_meas pate_estimated_score_to_scaled_tendsto
    hpatt_oracle hpatt_projection hpatt_projectionLimit_lt_oracle
    hpatt_inverse_meas patt_estimated_score_to_scaled_tendsto
    (absoluteWaldCoverageVarianceInput_of_twoSided pate_coverage_input)
    (absoluteWaldCoverageVarianceInput_of_twoSided patt_coverage_input)

/--
Paired absolute Wald bridge where both estimated-score limiting variances are
positive by weak projection slack plus positive target drift.
-/
def patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_le_drift_pos_limit
    (finite_estimated_bridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell PATTCell)
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_le_oracle :
      pate_projectionLimit ≤ pate_oracleLimit)
    (hpate_driftLimit_pos : 0 < pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pate_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_le_oracle :
      patt_projectionLimit ≤ patt_oracleLimit)
    (hpatt_driftLimit_pos : 0 < patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (patt_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_studentized
    (patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_le_drift_pos_limit
      finite_estimated_bridge pate_scaledStatistic pate_oracle
      pate_projectionReduction pate_targetDrift pate_limit pate_oracleLimit
      pate_projectionLimit pate_targetDriftLimit hpate_oracle
      hpate_projection hpate_drift hpate_projectionLimit_le_oracle
      hpate_driftLimit_pos hpate_inverse_meas
      pate_estimated_score_to_scaled_tendsto patt_scaledStatistic patt_oracle
      patt_projectionReduction patt_targetDrift patt_limit patt_oracleLimit
      patt_projectionLimit patt_targetDriftLimit hpatt_oracle
      hpatt_projection hpatt_drift hpatt_projectionLimit_le_oracle
      hpatt_driftLimit_pos hpatt_inverse_meas
      patt_estimated_score_to_scaled_tendsto)
    pate_coverage_input patt_coverage_input

/--
Paired absolute Wald bridge where both fixed-law estimated-score limiting
variances are positive by strict projection slack.
-/
def patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit
    (finite_estimated_bridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell PATTCell)
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction : Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pate_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction : Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (patt_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_studentized
    (patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_fixedLaw_projection_lt_limit
      finite_estimated_bridge pate_scaledStatistic pate_oracle
      pate_projectionReduction pate_limit pate_oracleLimit
      pate_projectionLimit hpate_oracle hpate_projection
      hpate_projectionLimit_lt_oracle hpate_inverse_meas
      pate_estimated_score_to_scaled_tendsto patt_scaledStatistic patt_oracle
      patt_projectionReduction patt_limit patt_oracleLimit patt_projectionLimit
      hpatt_oracle hpatt_projection
      hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
      patt_estimated_score_to_scaled_tendsto)
    pate_coverage_input patt_coverage_input

/--
Paired two-sided Wald bridge where both estimated-score limiting variances are
positive by strict projection slack and nonnegative target drift.
-/
def patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_lt_limit
    (finite_estimated_bridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell PATTCell)
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_driftLimit_nonneg : 0 ≤ pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pate_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_driftLimit_nonneg : 0 ≤ patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (patt_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_studentized
    (patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_lt_limit
      finite_estimated_bridge pate_scaledStatistic pate_oracle
      pate_projectionReduction pate_targetDrift pate_limit pate_oracleLimit
      pate_projectionLimit pate_targetDriftLimit hpate_oracle
      hpate_projection hpate_drift hpate_projectionLimit_lt_oracle
      hpate_driftLimit_nonneg hpate_inverse_meas
      pate_estimated_score_to_scaled_tendsto patt_scaledStatistic patt_oracle
      patt_projectionReduction patt_targetDrift patt_limit patt_oracleLimit
      patt_projectionLimit patt_targetDriftLimit hpatt_oracle
      hpatt_projection hpatt_drift hpatt_projectionLimit_lt_oracle
      hpatt_driftLimit_nonneg hpatt_inverse_meas
      patt_estimated_score_to_scaled_tendsto)
    pate_coverage_input patt_coverage_input

/--
Paired two-sided Wald bridge from absolute variance-based calibration inputs,
where both estimated-score limiting variances are positive by strict projection
slack and nonnegative target drift.
-/
def patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_lt_limit
    (finite_estimated_bridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell PATTCell)
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_driftLimit_nonneg : 0 ≤ pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pate_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_driftLimit_nonneg : 0 ≤ patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (patt_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_studentized
    (patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_lt_limit
      finite_estimated_bridge pate_scaledStatistic pate_oracle
      pate_projectionReduction pate_targetDrift pate_limit pate_oracleLimit
      pate_projectionLimit pate_targetDriftLimit hpate_oracle
      hpate_projection hpate_drift hpate_projectionLimit_lt_oracle
      hpate_driftLimit_nonneg hpate_inverse_meas
      pate_estimated_score_to_scaled_tendsto patt_scaledStatistic patt_oracle
      patt_projectionReduction patt_targetDrift patt_limit patt_oracleLimit
      patt_projectionLimit patt_targetDriftLimit hpatt_oracle
      hpatt_projection hpatt_drift hpatt_projectionLimit_lt_oracle
      hpatt_driftLimit_nonneg hpatt_inverse_meas
      patt_estimated_score_to_scaled_tendsto)
    (twoSidedWaldCoverageVarianceInput_of_absolute pate_coverage_input)
    (twoSidedWaldCoverageVarianceInput_of_absolute patt_coverage_input)

/--
Paired absolute Wald bridge from two-sided variance-based calibration inputs,
where both estimated-score limiting variances are positive by strict projection
slack and nonnegative target drift.
-/
def patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_lt_limit
    (finite_estimated_bridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell PATTCell)
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_driftLimit_nonneg : 0 ≤ pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pate_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_driftLimit_nonneg : 0 ≤ patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (patt_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_studentized
    (patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_lt_limit
      finite_estimated_bridge pate_scaledStatistic pate_oracle
      pate_projectionReduction pate_targetDrift pate_limit pate_oracleLimit
      pate_projectionLimit pate_targetDriftLimit hpate_oracle
      hpate_projection hpate_drift hpate_projectionLimit_lt_oracle
      hpate_driftLimit_nonneg hpate_inverse_meas
      pate_estimated_score_to_scaled_tendsto patt_scaledStatistic patt_oracle
      patt_projectionReduction patt_targetDrift patt_limit patt_oracleLimit
      patt_projectionLimit patt_targetDriftLimit hpatt_oracle
      hpatt_projection hpatt_drift hpatt_projectionLimit_lt_oracle
      hpatt_driftLimit_nonneg hpatt_inverse_meas
      patt_estimated_score_to_scaled_tendsto)
    (absoluteWaldCoverageVarianceInput_of_twoSided pate_coverage_input)
    (absoluteWaldCoverageVarianceInput_of_twoSided patt_coverage_input)

/--
Paired two-sided Wald bridge where both estimated-score limiting variances are
positive by weak projection slack plus positive target drift.
-/
def patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_le_drift_pos_limit
    (finite_estimated_bridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell PATTCell)
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_le_oracle :
      pate_projectionLimit ≤ pate_oracleLimit)
    (hpate_driftLimit_pos : 0 < pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pate_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_le_oracle :
      patt_projectionLimit ≤ patt_oracleLimit)
    (hpatt_driftLimit_pos : 0 < patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (patt_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_studentized
    (patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_le_drift_pos_limit
      finite_estimated_bridge pate_scaledStatistic pate_oracle
      pate_projectionReduction pate_targetDrift pate_limit pate_oracleLimit
      pate_projectionLimit pate_targetDriftLimit hpate_oracle
      hpate_projection hpate_drift hpate_projectionLimit_le_oracle
      hpate_driftLimit_pos hpate_inverse_meas
      pate_estimated_score_to_scaled_tendsto patt_scaledStatistic patt_oracle
      patt_projectionReduction patt_targetDrift patt_limit patt_oracleLimit
      patt_projectionLimit patt_targetDriftLimit hpatt_oracle
      hpatt_projection hpatt_drift hpatt_projectionLimit_le_oracle
      hpatt_driftLimit_pos hpatt_inverse_meas
      patt_estimated_score_to_scaled_tendsto)
    pate_coverage_input patt_coverage_input

/--
Paired two-sided Wald bridge from absolute variance-based calibration inputs,
where both estimated-score limiting variances are positive by weak projection
slack plus positive target drift.
-/
def patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_le_drift_pos_limit
    (finite_estimated_bridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell PATTCell)
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_le_oracle :
      pate_projectionLimit ≤ pate_oracleLimit)
    (hpate_driftLimit_pos : 0 < pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pate_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_le_oracle :
      patt_projectionLimit ≤ patt_oracleLimit)
    (hpatt_driftLimit_pos : 0 < patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (patt_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_studentized
    (patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_le_drift_pos_limit
      finite_estimated_bridge pate_scaledStatistic pate_oracle
      pate_projectionReduction pate_targetDrift pate_limit pate_oracleLimit
      pate_projectionLimit pate_targetDriftLimit hpate_oracle
      hpate_projection hpate_drift hpate_projectionLimit_le_oracle
      hpate_driftLimit_pos hpate_inverse_meas
      pate_estimated_score_to_scaled_tendsto patt_scaledStatistic patt_oracle
      patt_projectionReduction patt_targetDrift patt_limit patt_oracleLimit
      patt_projectionLimit patt_targetDriftLimit hpatt_oracle
      hpatt_projection hpatt_drift hpatt_projectionLimit_le_oracle
      hpatt_driftLimit_pos hpatt_inverse_meas
      patt_estimated_score_to_scaled_tendsto)
    (twoSidedWaldCoverageVarianceInput_of_absolute pate_coverage_input)
    (twoSidedWaldCoverageVarianceInput_of_absolute patt_coverage_input)

/--
Paired absolute Wald bridge from two-sided variance-based calibration inputs,
where both estimated-score limiting variances are positive by weak projection
slack plus positive target drift.
-/
def patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_le_drift_pos_limit
    (finite_estimated_bridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell PATTCell)
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_le_oracle :
      pate_projectionLimit ≤ pate_oracleLimit)
    (hpate_driftLimit_pos : 0 < pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pate_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_le_oracle :
      patt_projectionLimit ≤ patt_oracleLimit)
    (hpatt_driftLimit_pos : 0 < patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (patt_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_studentized
    (patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_le_drift_pos_limit
      finite_estimated_bridge pate_scaledStatistic pate_oracle
      pate_projectionReduction pate_targetDrift pate_limit pate_oracleLimit
      pate_projectionLimit pate_targetDriftLimit hpate_oracle
      hpate_projection hpate_drift hpate_projectionLimit_le_oracle
      hpate_driftLimit_pos hpate_inverse_meas
      pate_estimated_score_to_scaled_tendsto patt_scaledStatistic patt_oracle
      patt_projectionReduction patt_targetDrift patt_limit patt_oracleLimit
      patt_projectionLimit patt_targetDriftLimit hpatt_oracle
      hpatt_projection hpatt_drift hpatt_projectionLimit_le_oracle
      hpatt_driftLimit_pos hpatt_inverse_meas
      patt_estimated_score_to_scaled_tendsto)
    (absoluteWaldCoverageVarianceInput_of_twoSided pate_coverage_input)
    (absoluteWaldCoverageVarianceInput_of_twoSided patt_coverage_input)

/--
Paired two-sided Wald bridge where both fixed-law estimated-score limiting
variances are positive by strict projection slack.
-/
def patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit
    (finite_estimated_bridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell PATTCell)
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction : Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pate_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction : Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (patt_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_studentized
    (patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_fixedLaw_projection_lt_limit
      finite_estimated_bridge pate_scaledStatistic pate_oracle
      pate_projectionReduction pate_limit pate_oracleLimit
      pate_projectionLimit hpate_oracle hpate_projection
      hpate_projectionLimit_lt_oracle hpate_inverse_meas
      pate_estimated_score_to_scaled_tendsto patt_scaledStatistic patt_oracle
      patt_projectionReduction patt_limit patt_oracleLimit patt_projectionLimit
      hpatt_oracle hpatt_projection
      hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
      patt_estimated_score_to_scaled_tendsto)
    pate_coverage_input patt_coverage_input

/--
Paired two-sided Wald bridge from absolute variance-based calibration inputs,
where both fixed-law estimated-score limiting variances are positive by strict
projection slack.
-/
def patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_fixedLaw_projection_lt_limit
    (finite_estimated_bridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell PATTCell)
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction : Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pate_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction : Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (patt_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit
    finite_estimated_bridge pate_scaledStatistic pate_oracle
    pate_projectionReduction pate_limit pate_oracleLimit
    pate_projectionLimit hpate_oracle hpate_projection
    hpate_projectionLimit_lt_oracle hpate_inverse_meas
    pate_estimated_score_to_scaled_tendsto patt_scaledStatistic patt_oracle
    patt_projectionReduction patt_limit patt_oracleLimit patt_projectionLimit
    hpatt_oracle hpatt_projection
    hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
    patt_estimated_score_to_scaled_tendsto
    (twoSidedWaldCoverageVarianceInput_of_absolute pate_coverage_input)
    (twoSidedWaldCoverageVarianceInput_of_absolute patt_coverage_input)

/--
Paired absolute Wald bridge from two-sided variance-based calibration inputs,
where both fixed-law estimated-score limiting variances are positive by strict
projection slack.
-/
def patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_fixedLaw_projection_lt_limit
    (finite_estimated_bridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell PATTCell)
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction : Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pate_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction : Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (patt_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit
    finite_estimated_bridge pate_scaledStatistic pate_oracle
    pate_projectionReduction pate_limit pate_oracleLimit
    pate_projectionLimit hpate_oracle hpate_projection
    hpate_projectionLimit_lt_oracle hpate_inverse_meas
    pate_estimated_score_to_scaled_tendsto patt_scaledStatistic patt_oracle
    patt_projectionReduction patt_limit patt_oracleLimit patt_projectionLimit
    hpatt_oracle hpatt_projection
    hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
    patt_estimated_score_to_scaled_tendsto
    (absoluteWaldCoverageVarianceInput_of_twoSided pate_coverage_input)
    (absoluteWaldCoverageVarianceInput_of_twoSided patt_coverage_input)

end WDSM
end Matching
end StatInference
