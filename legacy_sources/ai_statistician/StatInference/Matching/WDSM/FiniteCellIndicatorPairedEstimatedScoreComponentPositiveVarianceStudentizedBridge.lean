import StatInference.Matching.WDSM.FiniteCellIndicatorPairedEstimatedScorePositiveVarianceStudentizedBridge
import StatInference.Matching.WDSM.FiniteCellIndicatorEstimatedScoreComponentPositiveVarianceStudentizedBridge

/-!
# Paired estimated-score studentization from component positivity

This module packages the component-positive estimated-score studentization
inputs for PATE and PATT into the paired finite score-cell bridge.  It removes
the remaining manual assembly step between component-level variance positivity
and the paired positive-variance studentized inference layer.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open scoped Topology

variable {PATECell PATTCell Index Sample LimitSample : Type*}
variable [DecidableEq PATECell] [DecidableEq PATTCell]
variable [MeasurableSpace Sample] [MeasurableSpace LimitSample]
variable {sampleLaw : MeasureTheory.Measure Sample}
variable {limitLaw : MeasureTheory.Measure LimitSample}
variable [MeasureTheory.IsProbabilityMeasure sampleLaw]
variable [MeasureTheory.IsProbabilityMeasure limitLaw]
variable {l : Filter Index}
variable [l.IsCountablyGenerated]

/--
Package independently derived PATE and PATT positive-variance studentization
inputs into the paired finite score-cell estimated-score bridge.
-/
def patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_inputs
    (finite_estimated_bridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell PATTCell)
    (pate_studentization_input :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (patt_studentization_input :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (pate_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_studentization_input.scaledStatistic l
          pate_studentization_input.limit (fun _index => sampleLaw) limitLaw)
    (patt_estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_studentization_input.scaledStatistic l
          patt_studentization_input.limit (fun _index => sampleLaw) limitLaw) :
    PATEPATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l where
  finite_estimated_bridge := finite_estimated_bridge
  pate_studentization_input := pate_studentization_input
  patt_studentization_input := patt_studentization_input
  pate_estimated_score_to_scaled_tendsto :=
    pate_estimated_score_to_scaled_tendsto
  patt_estimated_score_to_scaled_tendsto :=
    patt_estimated_score_to_scaled_tendsto

/--
Paired PATE/PATT studentized bridge where both estimated-score limiting
variances are positive by strict projection slack and nonnegative target drift.
-/
def patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_lt_limit
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
          (fun _index => sampleLaw) limitLaw) :
    PATEPATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_inputs
    finite_estimated_bridge
    (estimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit
      pate_scaledStatistic pate_oracle pate_projectionReduction
      pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
      pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
      hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
      hpate_inverse_meas)
    (estimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit
      patt_scaledStatistic patt_oracle patt_projectionReduction
      patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
      patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
      hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
      hpatt_inverse_meas)
    pate_estimated_score_to_scaled_tendsto
    patt_estimated_score_to_scaled_tendsto

/--
Paired PATE/PATT studentized bridge where both estimated-score limiting
variances are positive by weak projection slack plus positive target drift.
-/
def patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_le_drift_pos_limit
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
          (fun _index => sampleLaw) limitLaw) :
    PATEPATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_inputs
    finite_estimated_bridge
    (estimatedScorePositiveVarianceStudentizationInput_of_projection_le_drift_pos_limit
      pate_scaledStatistic pate_oracle pate_projectionReduction
      pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
      pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
      hpate_projectionLimit_le_oracle hpate_driftLimit_pos
      hpate_inverse_meas)
    (estimatedScorePositiveVarianceStudentizationInput_of_projection_le_drift_pos_limit
      patt_scaledStatistic patt_oracle patt_projectionReduction
      patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
      patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
      hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
      hpatt_inverse_meas)
    pate_estimated_score_to_scaled_tendsto
    patt_estimated_score_to_scaled_tendsto

/--
Paired PATE/PATT studentized bridge where both fixed-law estimated-score
limiting variances are positive by strict projection slack.
-/
def patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_fixedLaw_projection_lt_limit
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
          (fun _index => sampleLaw) limitLaw) :
    PATEPATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_inputs
    finite_estimated_bridge
    (fixedLawEstimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit
      pate_scaledStatistic pate_oracle pate_projectionReduction pate_limit
      pate_oracleLimit pate_projectionLimit hpate_oracle hpate_projection
      hpate_projectionLimit_lt_oracle hpate_inverse_meas)
    (fixedLawEstimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit
      patt_scaledStatistic patt_oracle patt_projectionReduction patt_limit
      patt_oracleLimit patt_projectionLimit hpatt_oracle hpatt_projection
      hpatt_projectionLimit_lt_oracle hpatt_inverse_meas)
    pate_estimated_score_to_scaled_tendsto
    patt_estimated_score_to_scaled_tendsto

/--
The strict projection-slack component route yields the paired studentized weak
limits after the finite-cell, known-score, estimated-score, and
component-variance obligations are supplied.
-/
theorem
    pate_patt_studentized_tendstoInDistribution_of_projection_lt_limit
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
    (hpate_design :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hpate_bounded :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (hpate_array_lln :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hpate_finite :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (hpate_envelope :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hpate_simplex :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hpate_linear :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpate_matrix :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpatt_design :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hpatt_bounded :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (hpatt_array_lln :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hpatt_finite :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (hpatt_envelope :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hpatt_simplex :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hpatt_linear :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpatt_matrix :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpate_decomp :
      finite_estimated_bridge.known_score_finite_cell_bridge.pate_known_score_bridge.aggregate_hajek_decomposition)
    (hpate_denominator :
      finite_estimated_bridge.known_score_finite_cell_bridge.pate_known_score_bridge.denominator_stabilization)
    (hpate_heterogeneity :
      finite_estimated_bridge.known_score_finite_cell_bridge.pate_known_score_bridge.heterogeneity_clt)
    (hpate_residual :
      finite_estimated_bridge.known_score_finite_cell_bridge.pate_known_score_bridge.residual_clt)
    (hpatt_decomp :
      finite_estimated_bridge.known_score_finite_cell_bridge.patt_known_score_bridge.aggregate_hajek_decomposition)
    (hpatt_denominator :
      finite_estimated_bridge.known_score_finite_cell_bridge.patt_known_score_bridge.denominator_stabilization)
    (hpatt_heterogeneity :
      finite_estimated_bridge.known_score_finite_cell_bridge.patt_known_score_bridge.heterogeneity_clt)
    (hpatt_residual :
      finite_estimated_bridge.known_score_finite_cell_bridge.patt_known_score_bridge.residual_clt)
    (hpate_first :
      finite_estimated_bridge.pate_estimated_score_bridge.first_step_asymptotic_linearization)
    (hpate_local :
      finite_estimated_bridge.pate_estimated_score_bridge.matching_functional_local_expansion)
    (hpate_godambe :
      finite_estimated_bridge.pate_estimated_score_bridge.godambe_variance_identity)
    (hpatt_first :
      finite_estimated_bridge.patt_estimated_score_bridge.first_step_asymptotic_linearization)
    (hpatt_local :
      finite_estimated_bridge.patt_estimated_score_bridge.matching_functional_local_expansion)
    (hpatt_godambe :
      finite_estimated_bridge.patt_estimated_score_bridge.godambe_variance_identity) :
    finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.pate_double_score_approximation_negligible ∧
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.clt_bridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      finite_estimated_bridge.known_score_finite_cell_bridge.pate_known_score_bridge.asymptotic_normality ∧
      finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ∧
      TendstoInDistribution
        (fun index sample =>
          pate_scaledStatistic index sample *
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
        l
        (fun limitSample =>
          pate_limit limitSample *
            (standardError
              (estimatedScoreVariance pate_oracleLimit pate_projectionLimit
                pate_targetDriftLimit))⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.clt_bridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      finite_estimated_bridge.known_score_finite_cell_bridge.patt_known_score_bridge.asymptotic_normality ∧
      finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ∧
      TendstoInDistribution
        (fun index sample =>
          patt_scaledStatistic index sample *
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
        l
        (fun limitSample =>
          patt_limit limitSample *
            (standardError
              (estimatedScoreVariance patt_oracleLimit patt_projectionLimit
                patt_targetDriftLimit))⁻¹)
        (fun _index => sampleLaw) limitLaw := by
  let b :=
    patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_lt_limit
      finite_estimated_bridge pate_scaledStatistic pate_oracle
      pate_projectionReduction pate_targetDrift pate_limit
      pate_oracleLimit pate_projectionLimit pate_targetDriftLimit
      hpate_oracle hpate_projection hpate_drift
      hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
      hpate_inverse_meas pate_estimated_score_to_scaled_tendsto
      patt_scaledStatistic patt_oracle patt_projectionReduction
      patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
      patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
      hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
      hpatt_inverse_meas patt_estimated_score_to_scaled_tendsto
  simpa [b] using
    pate_patt_studentized_tendstoInDistribution_of_paired_finite_score_cell_estimated_score_positiveVariance
      b hpate_design hpate_bounded hpate_array_lln hpate_finite
      hpate_envelope hpate_simplex hpate_linear hpate_matrix hpatt_design
      hpatt_bounded hpatt_array_lln hpatt_finite hpatt_envelope
      hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      hpate_local hpate_godambe hpatt_first hpatt_local hpatt_godambe

/--
The strict projection-slack component route from explicit local experiments,
with the local derivative, stochastic equicontinuity, and Godambe identity
packaged as one compact core per estimand.
-/
theorem
    pate_patt_studentized_tendstoInDistribution_of_projection_lt_limit_local_experiment_core
    (known :
      PATEPATTFiniteScoreCellKnownScoreAsymptoticBridge PATECell PATTCell)
    (pateEstimated : EstimatedScoreLocalExperimentInput)
    (pattEstimated : EstimatedScoreLocalExperimentInput)
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
    (hpate_scaled :
      pateEstimated.estimated_score_asymptotic_normality ->
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
    (hpatt_scaled :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (hpate_known_to_estimated :
      known.pate_known_score_bridge.asymptotic_normality ->
        pateEstimated.known_score_asymptotic_normality)
    (hpatt_known_to_estimated :
      known.patt_known_score_bridge.asymptotic_normality ->
        pattEstimated.known_score_asymptotic_normality)
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
          pate_scaledStatistic index sample *
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
        l
        (fun limitSample =>
          pate_limit limitSample *
            (standardError
              (estimatedScoreVariance pate_oracleLimit pate_projectionLimit
                pate_targetDriftLimit))⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      known.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
      known.stochastic_bridge.patt_bridge.clt_bridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      known.patt_known_score_bridge.asymptotic_normality ∧
      pattEstimated.estimated_score_asymptotic_normality ∧
      TendstoInDistribution
        (fun index sample =>
          patt_scaledStatistic index sample *
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
        l
        (fun limitSample =>
          patt_limit limitSample *
            (standardError
              (estimatedScoreVariance patt_oracleLimit patt_projectionLimit
                patt_targetDriftLimit))⁻¹)
        (fun _index => sampleLaw) limitLaw := by
  let finiteBridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell
        PATTCell :=
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
      known pateEstimated pattEstimated hpate_known_to_estimated
      hpatt_known_to_estimated
  simpa [finiteBridge,
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
    pate_patt_studentized_tendstoInDistribution_of_projection_lt_limit
      finiteBridge pate_scaledStatistic pate_oracle pate_projectionReduction
      pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
      pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
      hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
      hpate_inverse_meas hpate_scaled patt_scaledStatistic patt_oracle
      patt_projectionReduction patt_targetDrift patt_limit patt_oracleLimit
      patt_projectionLimit patt_targetDriftLimit hpatt_oracle
      hpatt_projection hpatt_drift hpatt_projectionLimit_lt_oracle
      hpatt_driftLimit_nonneg hpatt_inverse_meas hpatt_scaled
      hpate_design hpate_bounded hpate_array_lln hpate_finite
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

/--
The weak projection-slack plus positive-drift component route yields the paired
studentized weak limits after the finite-cell, known-score, estimated-score,
and component-variance obligations are supplied.
-/
theorem
    pate_patt_studentized_tendstoInDistribution_of_projection_le_drift_pos_limit
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
    (hpate_design :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hpate_bounded :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (hpate_array_lln :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hpate_finite :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (hpate_envelope :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hpate_simplex :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hpate_linear :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpate_matrix :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpatt_design :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hpatt_bounded :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (hpatt_array_lln :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hpatt_finite :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (hpatt_envelope :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hpatt_simplex :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hpatt_linear :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpatt_matrix :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpate_decomp :
      finite_estimated_bridge.known_score_finite_cell_bridge.pate_known_score_bridge.aggregate_hajek_decomposition)
    (hpate_denominator :
      finite_estimated_bridge.known_score_finite_cell_bridge.pate_known_score_bridge.denominator_stabilization)
    (hpate_heterogeneity :
      finite_estimated_bridge.known_score_finite_cell_bridge.pate_known_score_bridge.heterogeneity_clt)
    (hpate_residual :
      finite_estimated_bridge.known_score_finite_cell_bridge.pate_known_score_bridge.residual_clt)
    (hpatt_decomp :
      finite_estimated_bridge.known_score_finite_cell_bridge.patt_known_score_bridge.aggregate_hajek_decomposition)
    (hpatt_denominator :
      finite_estimated_bridge.known_score_finite_cell_bridge.patt_known_score_bridge.denominator_stabilization)
    (hpatt_heterogeneity :
      finite_estimated_bridge.known_score_finite_cell_bridge.patt_known_score_bridge.heterogeneity_clt)
    (hpatt_residual :
      finite_estimated_bridge.known_score_finite_cell_bridge.patt_known_score_bridge.residual_clt)
    (hpate_first :
      finite_estimated_bridge.pate_estimated_score_bridge.first_step_asymptotic_linearization)
    (hpate_local :
      finite_estimated_bridge.pate_estimated_score_bridge.matching_functional_local_expansion)
    (hpate_godambe :
      finite_estimated_bridge.pate_estimated_score_bridge.godambe_variance_identity)
    (hpatt_first :
      finite_estimated_bridge.patt_estimated_score_bridge.first_step_asymptotic_linearization)
    (hpatt_local :
      finite_estimated_bridge.patt_estimated_score_bridge.matching_functional_local_expansion)
    (hpatt_godambe :
      finite_estimated_bridge.patt_estimated_score_bridge.godambe_variance_identity) :
    finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.pate_double_score_approximation_negligible ∧
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.clt_bridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      finite_estimated_bridge.known_score_finite_cell_bridge.pate_known_score_bridge.asymptotic_normality ∧
      finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ∧
      TendstoInDistribution
        (fun index sample =>
          pate_scaledStatistic index sample *
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
        l
        (fun limitSample =>
          pate_limit limitSample *
            (standardError
              (estimatedScoreVariance pate_oracleLimit pate_projectionLimit
                pate_targetDriftLimit))⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.clt_bridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      finite_estimated_bridge.known_score_finite_cell_bridge.patt_known_score_bridge.asymptotic_normality ∧
      finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ∧
      TendstoInDistribution
        (fun index sample =>
          patt_scaledStatistic index sample *
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
        l
        (fun limitSample =>
          patt_limit limitSample *
            (standardError
              (estimatedScoreVariance patt_oracleLimit patt_projectionLimit
                patt_targetDriftLimit))⁻¹)
        (fun _index => sampleLaw) limitLaw := by
  let b :=
    patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_le_drift_pos_limit
      finite_estimated_bridge pate_scaledStatistic pate_oracle
      pate_projectionReduction pate_targetDrift pate_limit
      pate_oracleLimit pate_projectionLimit pate_targetDriftLimit
      hpate_oracle hpate_projection hpate_drift
      hpate_projectionLimit_le_oracle hpate_driftLimit_pos
      hpate_inverse_meas pate_estimated_score_to_scaled_tendsto
      patt_scaledStatistic patt_oracle patt_projectionReduction
      patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
      patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
      hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
      hpatt_inverse_meas patt_estimated_score_to_scaled_tendsto
  simpa [b] using
    pate_patt_studentized_tendstoInDistribution_of_paired_finite_score_cell_estimated_score_positiveVariance
      b hpate_design hpate_bounded hpate_array_lln hpate_finite
      hpate_envelope hpate_simplex hpate_linear hpate_matrix hpatt_design
      hpatt_bounded hpatt_array_lln hpatt_finite hpatt_envelope
      hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      hpate_local hpate_godambe hpatt_first hpatt_local hpatt_godambe

/--
The weak projection-slack plus positive-drift component route from explicit
local experiments, with the local derivative, stochastic equicontinuity, and
Godambe identity packaged as one compact core per estimand.
-/
theorem
    pate_patt_studentized_tendstoInDistribution_of_projection_le_drift_pos_limit_local_experiment_core
    (known :
      PATEPATTFiniteScoreCellKnownScoreAsymptoticBridge PATECell PATTCell)
    (pateEstimated : EstimatedScoreLocalExperimentInput)
    (pattEstimated : EstimatedScoreLocalExperimentInput)
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
    (hpate_scaled :
      pateEstimated.estimated_score_asymptotic_normality ->
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
    (hpatt_scaled :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (hpate_known_to_estimated :
      known.pate_known_score_bridge.asymptotic_normality ->
        pateEstimated.known_score_asymptotic_normality)
    (hpatt_known_to_estimated :
      known.patt_known_score_bridge.asymptotic_normality ->
        pattEstimated.known_score_asymptotic_normality)
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
          pate_scaledStatistic index sample *
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
        l
        (fun limitSample =>
          pate_limit limitSample *
            (standardError
              (estimatedScoreVariance pate_oracleLimit pate_projectionLimit
                pate_targetDriftLimit))⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      known.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
      known.stochastic_bridge.patt_bridge.clt_bridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      known.patt_known_score_bridge.asymptotic_normality ∧
      pattEstimated.estimated_score_asymptotic_normality ∧
      TendstoInDistribution
        (fun index sample =>
          patt_scaledStatistic index sample *
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
        l
        (fun limitSample =>
          patt_limit limitSample *
            (standardError
              (estimatedScoreVariance patt_oracleLimit patt_projectionLimit
                patt_targetDriftLimit))⁻¹)
        (fun _index => sampleLaw) limitLaw := by
  let finiteBridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell
        PATTCell :=
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
      known pateEstimated pattEstimated hpate_known_to_estimated
      hpatt_known_to_estimated
  simpa [finiteBridge,
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
    pate_patt_studentized_tendstoInDistribution_of_projection_le_drift_pos_limit
      finiteBridge pate_scaledStatistic pate_oracle pate_projectionReduction
      pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
      pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
      hpate_projectionLimit_le_oracle hpate_driftLimit_pos
      hpate_inverse_meas hpate_scaled patt_scaledStatistic patt_oracle
      patt_projectionReduction patt_targetDrift patt_limit patt_oracleLimit
      patt_projectionLimit patt_targetDriftLimit hpatt_oracle
      hpatt_projection hpatt_drift hpatt_projectionLimit_le_oracle
      hpatt_driftLimit_pos hpatt_inverse_meas hpatt_scaled hpate_design
      hpate_bounded hpate_array_lln hpate_finite hpate_envelope
      hpate_simplex hpate_linear hpate_matrix hpatt_design hpatt_bounded
      hpatt_array_lln hpatt_finite hpatt_envelope hpatt_simplex
      hpatt_linear hpatt_matrix hpate_decomp hpate_denominator
      hpate_heterogeneity hpate_residual hpatt_decomp hpatt_denominator
      hpatt_heterogeneity hpatt_residual hpate_first
      ⟨hpate_score, hpate_core.matching_functional_local_derivative,
        hpate_core.local_stochastic_equicontinuity⟩
      hpate_core.godambe_variance_identity hpatt_first
      ⟨hpatt_score, hpatt_core.matching_functional_local_derivative,
        hpatt_core.local_stochastic_equicontinuity⟩
      hpatt_core.godambe_variance_identity

/--
The fixed-law strict projection-slack component route yields the paired
studentized weak limits after the finite-cell, known-score, estimated-score,
and component-variance obligations are supplied.
-/
theorem
    pate_patt_studentized_tendstoInDistribution_of_fixedLaw_projection_lt_limit
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
    (hpate_design :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hpate_bounded :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (hpate_array_lln :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hpate_finite :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (hpate_envelope :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hpate_simplex :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hpate_linear :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpate_matrix :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpatt_design :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hpatt_bounded :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (hpatt_array_lln :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hpatt_finite :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (hpatt_envelope :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hpatt_simplex :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hpatt_linear :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpatt_matrix :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpate_decomp :
      finite_estimated_bridge.known_score_finite_cell_bridge.pate_known_score_bridge.aggregate_hajek_decomposition)
    (hpate_denominator :
      finite_estimated_bridge.known_score_finite_cell_bridge.pate_known_score_bridge.denominator_stabilization)
    (hpate_heterogeneity :
      finite_estimated_bridge.known_score_finite_cell_bridge.pate_known_score_bridge.heterogeneity_clt)
    (hpate_residual :
      finite_estimated_bridge.known_score_finite_cell_bridge.pate_known_score_bridge.residual_clt)
    (hpatt_decomp :
      finite_estimated_bridge.known_score_finite_cell_bridge.patt_known_score_bridge.aggregate_hajek_decomposition)
    (hpatt_denominator :
      finite_estimated_bridge.known_score_finite_cell_bridge.patt_known_score_bridge.denominator_stabilization)
    (hpatt_heterogeneity :
      finite_estimated_bridge.known_score_finite_cell_bridge.patt_known_score_bridge.heterogeneity_clt)
    (hpatt_residual :
      finite_estimated_bridge.known_score_finite_cell_bridge.patt_known_score_bridge.residual_clt)
    (hpate_first :
      finite_estimated_bridge.pate_estimated_score_bridge.first_step_asymptotic_linearization)
    (hpate_local :
      finite_estimated_bridge.pate_estimated_score_bridge.matching_functional_local_expansion)
    (hpate_godambe :
      finite_estimated_bridge.pate_estimated_score_bridge.godambe_variance_identity)
    (hpatt_first :
      finite_estimated_bridge.patt_estimated_score_bridge.first_step_asymptotic_linearization)
    (hpatt_local :
      finite_estimated_bridge.patt_estimated_score_bridge.matching_functional_local_expansion)
    (hpatt_godambe :
      finite_estimated_bridge.patt_estimated_score_bridge.godambe_variance_identity) :
    finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.pate_double_score_approximation_negligible ∧
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.clt_bridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      finite_estimated_bridge.known_score_finite_cell_bridge.pate_known_score_bridge.asymptotic_normality ∧
      finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ∧
      TendstoInDistribution
        (fun index sample =>
          pate_scaledStatistic index sample *
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample) 0))⁻¹)
        l
        (fun limitSample =>
          pate_limit limitSample *
            (standardError
              (estimatedScoreVariance pate_oracleLimit pate_projectionLimit
                0))⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.clt_bridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      finite_estimated_bridge.known_score_finite_cell_bridge.patt_known_score_bridge.asymptotic_normality ∧
      finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ∧
      TendstoInDistribution
        (fun index sample =>
          patt_scaledStatistic index sample *
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample) 0))⁻¹)
        l
        (fun limitSample =>
          patt_limit limitSample *
            (standardError
              (estimatedScoreVariance patt_oracleLimit patt_projectionLimit
                0))⁻¹)
        (fun _index => sampleLaw) limitLaw := by
  let b :=
    patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_fixedLaw_projection_lt_limit
      finite_estimated_bridge pate_scaledStatistic pate_oracle
      pate_projectionReduction pate_limit pate_oracleLimit
      pate_projectionLimit hpate_oracle hpate_projection
      hpate_projectionLimit_lt_oracle hpate_inverse_meas
      pate_estimated_score_to_scaled_tendsto patt_scaledStatistic
      patt_oracle patt_projectionReduction patt_limit patt_oracleLimit
      patt_projectionLimit hpatt_oracle hpatt_projection
      hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
      patt_estimated_score_to_scaled_tendsto
  simpa [b] using
    pate_patt_studentized_tendstoInDistribution_of_paired_finite_score_cell_estimated_score_positiveVariance
      b hpate_design hpate_bounded hpate_array_lln hpate_finite
      hpate_envelope hpate_simplex hpate_linear hpate_matrix hpatt_design
      hpatt_bounded hpatt_array_lln hpatt_finite hpatt_envelope
      hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      hpate_local hpate_godambe hpatt_first hpatt_local hpatt_godambe

/--
The fixed-law strict projection-slack component route from explicit local
experiments, with the local derivative, stochastic equicontinuity, and Godambe
identity packaged as one compact core per estimand.
-/
theorem
    pate_patt_studentized_tendstoInDistribution_of_fixedLaw_projection_lt_limit_local_experiment_core
    (known :
      PATEPATTFiniteScoreCellKnownScoreAsymptoticBridge PATECell PATTCell)
    (pateEstimated : EstimatedScoreLocalExperimentInput)
    (pattEstimated : EstimatedScoreLocalExperimentInput)
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
    (hpate_scaled :
      pateEstimated.estimated_score_asymptotic_normality ->
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
    (hpatt_scaled :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (hpate_known_to_estimated :
      known.pate_known_score_bridge.asymptotic_normality ->
        pateEstimated.known_score_asymptotic_normality)
    (hpatt_known_to_estimated :
      known.patt_known_score_bridge.asymptotic_normality ->
        pattEstimated.known_score_asymptotic_normality)
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
          pate_scaledStatistic index sample *
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample) 0))⁻¹)
        l
        (fun limitSample =>
          pate_limit limitSample *
            (standardError
              (estimatedScoreVariance pate_oracleLimit pate_projectionLimit
                0))⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      known.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
      known.stochastic_bridge.patt_bridge.clt_bridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      known.patt_known_score_bridge.asymptotic_normality ∧
      pattEstimated.estimated_score_asymptotic_normality ∧
      TendstoInDistribution
        (fun index sample =>
          patt_scaledStatistic index sample *
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample) 0))⁻¹)
        l
        (fun limitSample =>
          patt_limit limitSample *
            (standardError
              (estimatedScoreVariance patt_oracleLimit patt_projectionLimit
                0))⁻¹)
        (fun _index => sampleLaw) limitLaw := by
  let finiteBridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell
        PATTCell :=
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
      known pateEstimated pattEstimated hpate_known_to_estimated
      hpatt_known_to_estimated
  simpa [finiteBridge,
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
    pate_patt_studentized_tendstoInDistribution_of_fixedLaw_projection_lt_limit
      finiteBridge pate_scaledStatistic pate_oracle pate_projectionReduction
      pate_limit pate_oracleLimit pate_projectionLimit hpate_oracle
      hpate_projection hpate_projectionLimit_lt_oracle hpate_inverse_meas
      hpate_scaled patt_scaledStatistic patt_oracle patt_projectionReduction
      patt_limit patt_oracleLimit patt_projectionLimit hpatt_oracle
      hpatt_projection hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
      hpatt_scaled hpate_design hpate_bounded hpate_array_lln
      hpate_finite hpate_envelope hpate_simplex hpate_linear hpate_matrix
      hpatt_design hpatt_bounded hpatt_array_lln hpatt_finite
      hpatt_envelope hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
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
