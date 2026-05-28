import StatInference.Matching.WDSM.FiniteCellIndicatorPairedEstimatedScoreStudentizedBridge
import StatInference.Matching.WDSM.FiniteCellIndicatorEstimatedScorePositiveVarianceStudentizedBridge
import StatInference.Matching.WDSM.FiniteCellIndicatorEstimatedScoreComponentPositiveVarianceStudentizedBridge

/-!
# Paired estimated-score studentization from positive limiting variances

This module removes the separate nonzero limiting-standard-error premise from
the paired finite score-cell estimated-score studentization layer.  It accepts
positive PATE/PATT limiting variances and converts them into the paired
studentization input already used by the checked weak-limit bridge.
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

/--
Paired finite score-cell estimated-score bridge with PATE/PATT studentization
positivity stated through the limiting variances.
-/
structure PATEPATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge
    (PATECell PATTCell Index Sample LimitSample : Type*)
    [DecidableEq PATECell] [DecidableEq PATTCell]
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : MeasureTheory.Measure Sample)
    (limitLaw : MeasureTheory.Measure LimitSample) (l : Filter Index)
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw] [l.IsCountablyGenerated] where
  finite_estimated_bridge :
    PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell PATTCell
  pate_studentization_input :
    EstimatedScorePositiveVarianceStudentizationInput Index Sample LimitSample
      sampleLaw limitLaw l
  patt_studentization_input :
    EstimatedScorePositiveVarianceStudentizationInput Index Sample LimitSample
      sampleLaw limitLaw l
  pate_estimated_score_to_scaled_tendsto :
    finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ->
      TendstoInDistribution pate_studentization_input.scaledStatistic l
        pate_studentization_input.limit (fun _index => sampleLaw) limitLaw
  patt_estimated_score_to_scaled_tendsto :
    finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ->
      TendstoInDistribution patt_studentization_input.scaledStatistic l
        patt_studentization_input.limit (fun _index => sampleLaw) limitLaw

/--
Convert a paired positive-limiting-variance studentized bridge to the generic
paired nonzero-standard-error studentized bridge.
-/
noncomputable def patePATTFiniteScoreCellEstimatedScoreStudentizedBridge_of_positiveVariance
    (b :
      PATEPATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge
        PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l) :
    PATEPATTFiniteScoreCellEstimatedScoreStudentizedBridge PATECell PATTCell
      Index Sample LimitSample sampleLaw limitLaw l where
  finite_estimated_bridge := b.finite_estimated_bridge
  pate_studentization_input :=
    estimatedScoreStudentizationInput_of_positiveVariance
      b.pate_studentization_input
  patt_studentization_input :=
    estimatedScoreStudentizationInput_of_positiveVariance
      b.patt_studentization_input
  pate_estimated_score_to_scaled_tendsto :=
    b.pate_estimated_score_to_scaled_tendsto
  patt_estimated_score_to_scaled_tendsto :=
    b.patt_estimated_score_to_scaled_tendsto

/--
Paired PATE/PATT finite score-cell estimated-score positive-variance
studentized bridge with score-quadratic projection and target-drift reductions
for both arms under strict projection slack.
-/
noncomputable def patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_projection_lt_limit
    (finite_estimated_bridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell PATTCell)
    (pateParameters : Finset PATEParam)
    (pattParameters : Finset PATTParam)
    (pateScaledStatistic pattScaledStatistic : Index -> Sample -> Real)
    (pateOracle pattOracle : Index -> Sample -> Real)
    (pateFirstStepLoading pateTargetDriftLoading : PATEParam -> Real)
    (pattFirstStepLoading pattTargetDriftLoading : PATTParam -> Real)
    (pateScoreCovariance : Index -> Sample -> PATEParam -> PATEParam -> Real)
    (pattScoreCovariance : Index -> Sample -> PATTParam -> PATTParam -> Real)
    (pateLimit pattLimit : LimitSample -> Real)
    (pateOracleLimit pateProjectionLimit pateTargetDriftLimit : Real)
    (pattOracleLimit pattProjectionLimit pattTargetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pateOracle l
        (fun _sample => pateOracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pateParameters pateFirstStepLoading
            (pateScoreCovariance index sample))
        l (fun _sample => pateProjectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pateParameters pateTargetDriftLoading
            (pateScoreCovariance index sample))
        l (fun _sample => pateTargetDriftLimit))
    (hpate_projection_lt_oracle :
      pateProjectionLimit < pateOracleLimit)
    (hpate_drift_nonneg : 0 ≤ pateTargetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pateOracle index sample)
                (scoreQuadraticForm pateParameters pateFirstStepLoading
                  (pateScoreCovariance index sample))
                (scoreQuadraticForm pateParameters pateTargetDriftLoading
                  (pateScoreCovariance index sample))))⁻¹)
          sampleLaw)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw pattOracle l
        (fun _sample => pattOracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pattParameters pattFirstStepLoading
            (pattScoreCovariance index sample))
        l (fun _sample => pattProjectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pattParameters pattTargetDriftLoading
            (pattScoreCovariance index sample))
        l (fun _sample => pattTargetDriftLimit))
    (hpatt_projection_lt_oracle :
      pattProjectionLimit < pattOracleLimit)
    (hpatt_drift_nonneg : 0 ≤ pattTargetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pattOracle index sample)
                (scoreQuadraticForm pattParameters pattFirstStepLoading
                  (pattScoreCovariance index sample))
                (scoreQuadraticForm pattParameters pattTargetDriftLoading
                  (pattScoreCovariance index sample))))⁻¹)
          sampleLaw)
    (hpate_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pateScaledStatistic l pateLimit
          (fun _index => sampleLaw) limitLaw)
    (hpatt_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pattScaledStatistic l pattLimit
          (fun _index => sampleLaw) limitLaw) :
    PATEPATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l where
  finite_estimated_bridge := finite_estimated_bridge
  pate_studentization_input :=
    estimatedScorePositiveVarianceStudentizationInput_of_scoreAdjusted_projection_lt_limit
      pateParameters pateScaledStatistic pateOracle pateFirstStepLoading
      pateTargetDriftLoading pateScoreCovariance pateLimit pateOracleLimit
      pateProjectionLimit pateTargetDriftLimit hpate_oracle
      hpate_projection hpate_drift hpate_projection_lt_oracle
      hpate_drift_nonneg hpate_inverse_meas
  patt_studentization_input :=
    estimatedScorePositiveVarianceStudentizationInput_of_scoreAdjusted_projection_lt_limit
      pattParameters pattScaledStatistic pattOracle pattFirstStepLoading
      pattTargetDriftLoading pattScoreCovariance pattLimit pattOracleLimit
      pattProjectionLimit pattTargetDriftLimit hpatt_oracle
      hpatt_projection hpatt_drift hpatt_projection_lt_oracle
      hpatt_drift_nonneg hpatt_inverse_meas
  pate_estimated_score_to_scaled_tendsto :=
    hpate_estimated_score_to_scaled_tendsto
  patt_estimated_score_to_scaled_tendsto :=
    hpatt_estimated_score_to_scaled_tendsto

/--
Paired PATE/PATT finite score-cell estimated-score positive-variance
studentized bridge with score-quadratic reductions for both arms under weak
projection slack and positive target-drift limits.
-/
noncomputable def patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_projection_le_drift_pos_limit
    (finite_estimated_bridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell PATTCell)
    (pateParameters : Finset PATEParam)
    (pattParameters : Finset PATTParam)
    (pateScaledStatistic pattScaledStatistic : Index -> Sample -> Real)
    (pateOracle pattOracle : Index -> Sample -> Real)
    (pateFirstStepLoading pateTargetDriftLoading : PATEParam -> Real)
    (pattFirstStepLoading pattTargetDriftLoading : PATTParam -> Real)
    (pateScoreCovariance : Index -> Sample -> PATEParam -> PATEParam -> Real)
    (pattScoreCovariance : Index -> Sample -> PATTParam -> PATTParam -> Real)
    (pateLimit pattLimit : LimitSample -> Real)
    (pateOracleLimit pateProjectionLimit pateTargetDriftLimit : Real)
    (pattOracleLimit pattProjectionLimit pattTargetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pateOracle l
        (fun _sample => pateOracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pateParameters pateFirstStepLoading
            (pateScoreCovariance index sample))
        l (fun _sample => pateProjectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pateParameters pateTargetDriftLoading
            (pateScoreCovariance index sample))
        l (fun _sample => pateTargetDriftLimit))
    (hpate_projection_le_oracle :
      pateProjectionLimit ≤ pateOracleLimit)
    (hpate_drift_pos : 0 < pateTargetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pateOracle index sample)
                (scoreQuadraticForm pateParameters pateFirstStepLoading
                  (pateScoreCovariance index sample))
                (scoreQuadraticForm pateParameters pateTargetDriftLoading
                  (pateScoreCovariance index sample))))⁻¹)
          sampleLaw)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw pattOracle l
        (fun _sample => pattOracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pattParameters pattFirstStepLoading
            (pattScoreCovariance index sample))
        l (fun _sample => pattProjectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pattParameters pattTargetDriftLoading
            (pattScoreCovariance index sample))
        l (fun _sample => pattTargetDriftLimit))
    (hpatt_projection_le_oracle :
      pattProjectionLimit ≤ pattOracleLimit)
    (hpatt_drift_pos : 0 < pattTargetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pattOracle index sample)
                (scoreQuadraticForm pattParameters pattFirstStepLoading
                  (pattScoreCovariance index sample))
                (scoreQuadraticForm pattParameters pattTargetDriftLoading
                  (pattScoreCovariance index sample))))⁻¹)
          sampleLaw)
    (hpate_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pateScaledStatistic l pateLimit
          (fun _index => sampleLaw) limitLaw)
    (hpatt_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pattScaledStatistic l pattLimit
          (fun _index => sampleLaw) limitLaw) :
    PATEPATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l where
  finite_estimated_bridge := finite_estimated_bridge
  pate_studentization_input :=
    estimatedScorePositiveVarianceStudentizationInput_of_scoreAdjusted_projection_le_drift_pos_limit
      pateParameters pateScaledStatistic pateOracle pateFirstStepLoading
      pateTargetDriftLoading pateScoreCovariance pateLimit pateOracleLimit
      pateProjectionLimit pateTargetDriftLimit hpate_oracle
      hpate_projection hpate_drift hpate_projection_le_oracle
      hpate_drift_pos hpate_inverse_meas
  patt_studentization_input :=
    estimatedScorePositiveVarianceStudentizationInput_of_scoreAdjusted_projection_le_drift_pos_limit
      pattParameters pattScaledStatistic pattOracle pattFirstStepLoading
      pattTargetDriftLoading pattScoreCovariance pattLimit pattOracleLimit
      pattProjectionLimit pattTargetDriftLimit hpatt_oracle
      hpatt_projection hpatt_drift hpatt_projection_le_oracle
      hpatt_drift_pos hpatt_inverse_meas
  pate_estimated_score_to_scaled_tendsto :=
    hpate_estimated_score_to_scaled_tendsto
  patt_estimated_score_to_scaled_tendsto :=
    hpatt_estimated_score_to_scaled_tendsto

/--
Paired PATE/PATT finite score-cell estimated-score positive-variance
studentized bridge with fixed-law score-quadratic projection reductions for
both arms under strict projection slack.
-/
noncomputable def patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_fixedLaw_projection_lt_limit
    (finite_estimated_bridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell PATTCell)
    (pateParameters : Finset PATEParam)
    (pattParameters : Finset PATTParam)
    (pateScaledStatistic pattScaledStatistic : Index -> Sample -> Real)
    (pateOracle pattOracle : Index -> Sample -> Real)
    (pateFirstStepLoading : PATEParam -> Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pateScoreCovariance : Index -> Sample -> PATEParam -> PATEParam -> Real)
    (pattScoreCovariance : Index -> Sample -> PATTParam -> PATTParam -> Real)
    (pateLimit pattLimit : LimitSample -> Real)
    (pateOracleLimit pateProjectionLimit : Real)
    (pattOracleLimit pattProjectionLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pateOracle l
        (fun _sample => pateOracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pateParameters pateFirstStepLoading
            (pateScoreCovariance index sample))
        l (fun _sample => pateProjectionLimit))
    (hpate_projection_lt_oracle :
      pateProjectionLimit < pateOracleLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pateOracle index sample)
                (scoreQuadraticForm pateParameters pateFirstStepLoading
                  (pateScoreCovariance index sample)) 0))⁻¹)
          sampleLaw)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw pattOracle l
        (fun _sample => pattOracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pattParameters pattFirstStepLoading
            (pattScoreCovariance index sample))
        l (fun _sample => pattProjectionLimit))
    (hpatt_projection_lt_oracle :
      pattProjectionLimit < pattOracleLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pattOracle index sample)
                (scoreQuadraticForm pattParameters pattFirstStepLoading
                  (pattScoreCovariance index sample)) 0))⁻¹)
          sampleLaw)
    (hpate_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pateScaledStatistic l pateLimit
          (fun _index => sampleLaw) limitLaw)
    (hpatt_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pattScaledStatistic l pattLimit
          (fun _index => sampleLaw) limitLaw) :
    PATEPATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l where
  finite_estimated_bridge := finite_estimated_bridge
  pate_studentization_input :=
    fixedLawEstimatedScorePositiveVarianceStudentizationInput_of_scoreAdjusted_projection_lt_limit
      pateParameters pateScaledStatistic pateOracle pateFirstStepLoading
      pateScoreCovariance pateLimit pateOracleLimit pateProjectionLimit
      hpate_oracle hpate_projection hpate_projection_lt_oracle
      hpate_inverse_meas
  patt_studentization_input :=
    fixedLawEstimatedScorePositiveVarianceStudentizationInput_of_scoreAdjusted_projection_lt_limit
      pattParameters pattScaledStatistic pattOracle pattFirstStepLoading
      pattScoreCovariance pattLimit pattOracleLimit pattProjectionLimit
      hpatt_oracle hpatt_projection hpatt_projection_lt_oracle
      hpatt_inverse_meas
  pate_estimated_score_to_scaled_tendsto :=
    hpate_estimated_score_to_scaled_tendsto
  patt_estimated_score_to_scaled_tendsto :=
    hpatt_estimated_score_to_scaled_tendsto

theorem
    pate_patt_studentized_tendstoInDistribution_of_paired_finite_score_cell_estimated_score_positiveVariance
    (b :
      PATEPATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge
        PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l)
    (hpate_design :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hpate_bounded :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (hpate_array_lln :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hpate_finite :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (hpate_envelope :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hpate_simplex :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hpate_linear :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpate_matrix :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpatt_design :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hpatt_bounded :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (hpatt_array_lln :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hpatt_finite :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (hpatt_envelope :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hpatt_simplex :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hpatt_linear :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpatt_matrix :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpate_decomp :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.pate_known_score_bridge.aggregate_hajek_decomposition)
    (hpate_denominator :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.pate_known_score_bridge.denominator_stabilization)
    (hpate_heterogeneity :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.pate_known_score_bridge.heterogeneity_clt)
    (hpate_residual :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.pate_known_score_bridge.residual_clt)
    (hpatt_decomp :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.patt_known_score_bridge.aggregate_hajek_decomposition)
    (hpatt_denominator :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.patt_known_score_bridge.denominator_stabilization)
    (hpatt_heterogeneity :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.patt_known_score_bridge.heterogeneity_clt)
    (hpatt_residual :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.patt_known_score_bridge.residual_clt)
    (hpate_first :
      b.finite_estimated_bridge.pate_estimated_score_bridge.first_step_asymptotic_linearization)
    (hpate_local :
      b.finite_estimated_bridge.pate_estimated_score_bridge.matching_functional_local_expansion)
    (hpate_godambe :
      b.finite_estimated_bridge.pate_estimated_score_bridge.godambe_variance_identity)
    (hpatt_first :
      b.finite_estimated_bridge.patt_estimated_score_bridge.first_step_asymptotic_linearization)
    (hpatt_local :
      b.finite_estimated_bridge.patt_estimated_score_bridge.matching_functional_local_expansion)
    (hpatt_godambe :
      b.finite_estimated_bridge.patt_estimated_score_bridge.godambe_variance_identity) :
    b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.pate_double_score_approximation_negligible ∧
      b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.clt_bridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      b.finite_estimated_bridge.known_score_finite_cell_bridge.pate_known_score_bridge.asymptotic_normality ∧
      b.finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ∧
      TendstoInDistribution
        (fun index sample =>
          b.pate_studentization_input.scaledStatistic index sample *
            (standardError
              (b.pate_studentization_input.varianceEstimate index sample))⁻¹)
        l
        (fun limitSample =>
          b.pate_studentization_input.limit limitSample *
            (standardError b.pate_studentization_input.varianceLimit)⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
      b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.clt_bridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      b.finite_estimated_bridge.known_score_finite_cell_bridge.patt_known_score_bridge.asymptotic_normality ∧
      b.finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ∧
      TendstoInDistribution
        (fun index sample =>
          b.patt_studentization_input.scaledStatistic index sample *
            (standardError
              (b.patt_studentization_input.varianceEstimate index sample))⁻¹)
        l
        (fun limitSample =>
          b.patt_studentization_input.limit limitSample *
            (standardError b.patt_studentization_input.varianceLimit)⁻¹)
        (fun _index => sampleLaw) limitLaw := by
  let converted :=
    patePATTFiniteScoreCellEstimatedScoreStudentizedBridge_of_positiveVariance b
  simpa [converted, estimatedScoreStudentizationInput_of_positiveVariance] using
    pate_patt_studentized_tendstoInDistribution_of_paired_finite_score_cell_estimated_score
      converted hpate_design hpate_bounded hpate_array_lln hpate_finite
      hpate_envelope hpate_simplex hpate_linear hpate_matrix hpatt_design
      hpatt_bounded hpatt_array_lln hpatt_finite hpatt_envelope
      hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      hpate_local hpate_godambe hpatt_first hpatt_local hpatt_godambe

/--
Paired finite score-cell estimated-score positive-variance studentized weak
limits from explicit local experiments, with one compact local-experiment core
per estimand.
-/
theorem
    pate_patt_studentized_tendstoInDistribution_of_paired_finite_score_cell_estimated_score_positiveVariance_local_experiment_core
    (known :
      PATEPATTFiniteScoreCellKnownScoreAsymptoticBridge PATECell PATTCell)
    (pateEstimated : EstimatedScoreLocalExperimentInput)
    (pattEstimated : EstimatedScoreLocalExperimentInput)
    (pateStudentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (pattStudentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (hpate_known_to_estimated :
      known.pate_known_score_bridge.asymptotic_normality ->
        pateEstimated.known_score_asymptotic_normality)
    (hpatt_known_to_estimated :
      known.patt_known_score_bridge.asymptotic_normality ->
        pattEstimated.known_score_asymptotic_normality)
    (hpate_scaled :
      pateEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution pateStudentizationInput.scaledStatistic l
          pateStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (hpatt_scaled :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution pattStudentizationInput.scaledStatistic l
          pattStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (hpate_design :
      known.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hpate_bounded :
      known.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (hpate_array_lln :
      known.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hpate_finite :
      known.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (hpate_envelope :
      known.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hpate_simplex :
      known.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hpate_linear :
      known.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpate_matrix :
      known.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpatt_design :
      known.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hpatt_bounded :
      known.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (hpatt_array_lln :
      known.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hpatt_finite :
      known.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (hpatt_envelope :
      known.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hpatt_simplex :
      known.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hpatt_linear :
      known.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpatt_matrix :
      known.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpate_decomp :
      known.pate_known_score_bridge.aggregate_hajek_decomposition)
    (hpate_denominator :
      known.pate_known_score_bridge.denominator_stabilization)
    (hpate_heterogeneity :
      known.pate_known_score_bridge.heterogeneity_clt)
    (hpate_residual : known.pate_known_score_bridge.residual_clt)
    (hpatt_decomp :
      known.patt_known_score_bridge.aggregate_hajek_decomposition)
    (hpatt_denominator :
      known.patt_known_score_bridge.denominator_stabilization)
    (hpatt_heterogeneity :
      known.patt_known_score_bridge.heterogeneity_clt)
    (hpatt_residual : known.patt_known_score_bridge.residual_clt)
    (hpate_first : pateEstimated.first_step_asymptotic_linearization)
    (hpate_score :
      pateEstimated.score_estimator_local_asymptotic_linearity)
    (hpate_core : EstimatedScoreLocalExperimentCore pateEstimated)
    (hpatt_first : pattEstimated.first_step_asymptotic_linearization)
    (hpatt_score :
      pattEstimated.score_estimator_local_asymptotic_linearity)
    (hpatt_core : EstimatedScoreLocalExperimentCore pattEstimated) :
    known.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.pate_double_score_approximation_negligible ∧
      known.stochastic_bridge.pate_bridge.clt_bridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      known.pate_known_score_bridge.asymptotic_normality ∧
      pateEstimated.estimated_score_asymptotic_normality ∧
      TendstoInDistribution
        (fun index sample =>
          pateStudentizationInput.scaledStatistic index sample *
            (standardError
              (pateStudentizationInput.varianceEstimate index sample))⁻¹)
        l
        (fun limitSample =>
          pateStudentizationInput.limit limitSample *
            (standardError pateStudentizationInput.varianceLimit)⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      known.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
      known.stochastic_bridge.patt_bridge.clt_bridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      known.patt_known_score_bridge.asymptotic_normality ∧
      pattEstimated.estimated_score_asymptotic_normality ∧
      TendstoInDistribution
        (fun index sample =>
          pattStudentizationInput.scaledStatistic index sample *
            (standardError
              (pattStudentizationInput.varianceEstimate index sample))⁻¹)
        l
        (fun limitSample =>
          pattStudentizationInput.limit limitSample *
            (standardError pattStudentizationInput.varianceLimit)⁻¹)
        (fun _index => sampleLaw) limitLaw := by
  let finiteBridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell
        PATTCell :=
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
      known pateEstimated pattEstimated hpate_known_to_estimated
      hpatt_known_to_estimated
  let b :
      PATEPATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge
        PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l := {
    finite_estimated_bridge := finiteBridge
    pate_studentization_input := pateStudentizationInput
    patt_studentization_input := pattStudentizationInput
    pate_estimated_score_to_scaled_tendsto := hpate_scaled
    patt_estimated_score_to_scaled_tendsto := hpatt_scaled }
  simpa [b, finiteBridge,
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
    pate_patt_studentized_tendstoInDistribution_of_paired_finite_score_cell_estimated_score_positiveVariance
      b hpate_design hpate_bounded hpate_array_lln hpate_finite
      hpate_envelope hpate_simplex hpate_linear hpate_matrix hpatt_design
      hpatt_bounded hpatt_array_lln hpatt_finite hpatt_envelope
      hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      ⟨hpate_score, hpate_core.matching_functional_local_derivative,
        hpate_core.local_stochastic_equicontinuity⟩
      hpate_core.godambe_variance_identity hpatt_first
      ⟨hpatt_score, hpatt_core.matching_functional_local_derivative,
        hpatt_core.local_stochastic_equicontinuity⟩
      hpatt_core.godambe_variance_identity

end WDSM
end Matching
end StatInference
