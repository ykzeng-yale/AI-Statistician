import StatInference.Matching.WDSM.FiniteCellIndicatorPairedEstimatedScoreComponentPositiveVarianceWaldBridge

/-!
# Direct paired Wald coverage from component-positive estimated-score variance

This module removes the final manual bridge-construction step for paired
finite score-cell estimated-score Wald coverage.  The first direct theorem
handles the strict projection-slack route for absolute Wald regions.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open Filter
open scoped Topology

variable {PATECell PATTCell Index Sample LimitSample : Type*}
variable [DecidableEq PATECell] [DecidableEq PATTCell]
variable {PATEParam PATTParam : Type*}
variable [MeasurableSpace Sample] [MeasurableSpace LimitSample]
variable {sampleLaw : MeasureTheory.Measure Sample}
variable {limitLaw : MeasureTheory.Measure LimitSample}
variable [MeasureTheory.IsProbabilityMeasure sampleLaw]
variable [MeasureTheory.IsProbabilityMeasure limitLaw]
variable {l : Filter Index}
variable [l.IsCountablyGenerated]

/--
Paired absolute finite score-cell estimated-score Wald coverage directly from
strict projection slack and nonnegative target drift in both the PATE and PATT
estimated-score variance components.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit
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
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
    let b :=
      patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_lt_limit
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
        pate_coverage_input patt_coverage_input
    b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.pate_double_score_approximation_negligible ∧
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.clt_bridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.pate_known_score_bridge.asymptotic_normality ∧
      b.studentized_bridge.finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ∧
      TendstoInDistribution
        (fun index sample =>
          b.studentized_bridge.pate_studentization_input.scaledStatistic index sample *
            (standardError
              (b.studentized_bridge.pate_studentization_input.varianceEstimate
                index sample))⁻¹)
        l
        (fun limitSample =>
          b.studentized_bridge.pate_studentization_input.limit limitSample *
            (standardError
              b.studentized_bridge.pate_studentization_input.varianceLimit)⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      Tendsto
        (fun index =>
          eventProbabilityReal (b.pate_coverage_input.sampleLawSeq index)
            (fun sample =>
              waldCovers (b.pate_coverage_input.estimator index sample)
                (b.pate_coverage_input.target index)
                (b.pate_coverage_input.criticalValue index)
                (standardError
                  (b.pate_coverage_input.varianceEstimate index sample))
                (b.pate_coverage_input.scale index)))
        l (nhds b.pate_coverage_input.coverageLimit) ∧
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.clt_bridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.patt_known_score_bridge.asymptotic_normality ∧
      b.studentized_bridge.finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ∧
      TendstoInDistribution
        (fun index sample =>
          b.studentized_bridge.patt_studentization_input.scaledStatistic index sample *
            (standardError
              (b.studentized_bridge.patt_studentization_input.varianceEstimate
                index sample))⁻¹)
        l
        (fun limitSample =>
          b.studentized_bridge.patt_studentization_input.limit limitSample *
            (standardError
              b.studentized_bridge.patt_studentization_input.varianceLimit)⁻¹)
        (fun _index => sampleLaw) limitLaw ∧
      Tendsto
        (fun index =>
          eventProbabilityReal (b.patt_coverage_input.sampleLawSeq index)
            (fun sample =>
              waldCovers (b.patt_coverage_input.estimator index sample)
                (b.patt_coverage_input.target index)
                (b.patt_coverage_input.criticalValue index)
                (standardError
                  (b.patt_coverage_input.varianceEstimate index sample))
                (b.patt_coverage_input.scale index)))
        l (nhds b.patt_coverage_input.coverageLimit) := by
  let b :=
    patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_lt_limit
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
      pate_coverage_input patt_coverage_input
  simpa [b] using
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score
      b hpate_design hpate_bounded hpate_array_lln hpate_finite
      hpate_envelope hpate_simplex hpate_linear hpate_matrix hpatt_design
      hpatt_bounded hpatt_array_lln hpatt_finite hpatt_envelope
      hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      hpate_local hpate_godambe hpatt_first hpatt_local hpatt_godambe

/--
The paired absolute positive-variance Wald conclusion used by direct
component-positive wrappers.
-/
def PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
    (b :
      PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge
        PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l) :
    Prop :=
  b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.pate_double_score_approximation_negligible ∧
    b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.clt_bridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
    b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.pate_known_score_bridge.asymptotic_normality ∧
    b.studentized_bridge.finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ∧
    TendstoInDistribution
      (fun index sample =>
        b.studentized_bridge.pate_studentization_input.scaledStatistic index sample *
          (standardError
            (b.studentized_bridge.pate_studentization_input.varianceEstimate
              index sample))⁻¹)
      l
      (fun limitSample =>
        b.studentized_bridge.pate_studentization_input.limit limitSample *
          (standardError
            b.studentized_bridge.pate_studentization_input.varianceLimit)⁻¹)
      (fun _index => sampleLaw) limitLaw ∧
    Tendsto
      (fun index =>
        eventProbabilityReal (b.pate_coverage_input.sampleLawSeq index)
          (fun sample =>
            waldCovers (b.pate_coverage_input.estimator index sample)
              (b.pate_coverage_input.target index)
              (b.pate_coverage_input.criticalValue index)
              (standardError
                (b.pate_coverage_input.varianceEstimate index sample))
              (b.pate_coverage_input.scale index)))
      l (nhds b.pate_coverage_input.coverageLimit) ∧
    b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
    b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.clt_bridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
    b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.patt_known_score_bridge.asymptotic_normality ∧
    b.studentized_bridge.finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ∧
    TendstoInDistribution
      (fun index sample =>
        b.studentized_bridge.patt_studentization_input.scaledStatistic index sample *
          (standardError
            (b.studentized_bridge.patt_studentization_input.varianceEstimate
              index sample))⁻¹)
      l
      (fun limitSample =>
        b.studentized_bridge.patt_studentization_input.limit limitSample *
          (standardError
            b.studentized_bridge.patt_studentization_input.varianceLimit)⁻¹)
      (fun _index => sampleLaw) limitLaw ∧
    Tendsto
      (fun index =>
        eventProbabilityReal (b.patt_coverage_input.sampleLawSeq index)
          (fun sample =>
            waldCovers (b.patt_coverage_input.estimator index sample)
              (b.patt_coverage_input.target index)
              (b.patt_coverage_input.criticalValue index)
              (standardError
                (b.patt_coverage_input.varianceEstimate index sample))
              (b.patt_coverage_input.scale index)))
      l (nhds b.patt_coverage_input.coverageLimit)

/--
Paired absolute finite score-cell estimated-score Wald coverage directly from
weak projection slack and positive target drift in both the PATE and PATT
estimated-score variance components.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit
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
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_le_drift_pos_limit
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
        pate_coverage_input patt_coverage_input) := by
  let b :=
    patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_le_drift_pos_limit
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
      pate_coverage_input patt_coverage_input
  simpa [PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion, b] using
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score
      b hpate_design hpate_bounded hpate_array_lln hpate_finite
      hpate_envelope hpate_simplex hpate_linear hpate_matrix hpatt_design
      hpatt_bounded hpatt_array_lln hpatt_finite hpatt_envelope
      hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      hpate_local hpate_godambe hpatt_first hpatt_local hpatt_godambe

/--
The paired two-sided positive-variance Wald conclusion used by direct
component-positive wrappers.
-/
def PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
    (b :
      PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge
        PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l) :
    Prop :=
  b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.pate_double_score_approximation_negligible ∧
    b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.clt_bridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ∧
    b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.pate_known_score_bridge.asymptotic_normality ∧
    b.studentized_bridge.finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ∧
    TendstoInDistribution
      (fun index sample =>
        b.studentized_bridge.pate_studentization_input.scaledStatistic index sample *
          (standardError
            (b.studentized_bridge.pate_studentization_input.varianceEstimate
              index sample))⁻¹)
      l
      (fun limitSample =>
        b.studentized_bridge.pate_studentization_input.limit limitSample *
          (standardError
            b.studentized_bridge.pate_studentization_input.varianceLimit)⁻¹)
      (fun _index => sampleLaw) limitLaw ∧
    Tendsto
      (fun index =>
        eventProbabilityReal (b.pate_coverage_input.sampleLawSeq index)
          (fun sample =>
            waldCovers (b.pate_coverage_input.estimator index sample)
              (b.pate_coverage_input.target index)
              (b.pate_coverage_input.criticalValue index)
              (standardError
                (b.pate_coverage_input.varianceEstimate index sample))
              (b.pate_coverage_input.scale index)))
      l (nhds b.pate_coverage_input.coverageLimit) ∧
    b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
    b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.clt_bridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ∧
    b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.patt_known_score_bridge.asymptotic_normality ∧
    b.studentized_bridge.finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ∧
    TendstoInDistribution
      (fun index sample =>
        b.studentized_bridge.patt_studentization_input.scaledStatistic index sample *
          (standardError
            (b.studentized_bridge.patt_studentization_input.varianceEstimate
              index sample))⁻¹)
      l
      (fun limitSample =>
        b.studentized_bridge.patt_studentization_input.limit limitSample *
          (standardError
            b.studentized_bridge.patt_studentization_input.varianceLimit)⁻¹)
      (fun _index => sampleLaw) limitLaw ∧
    Tendsto
      (fun index =>
        eventProbabilityReal (b.patt_coverage_input.sampleLawSeq index)
          (fun sample =>
            waldCovers (b.patt_coverage_input.estimator index sample)
              (b.patt_coverage_input.target index)
              (b.patt_coverage_input.criticalValue index)
              (standardError
                (b.patt_coverage_input.varianceEstimate index sample))
              (b.patt_coverage_input.scale index)))
      l (nhds b.patt_coverage_input.coverageLimit)

/--
Common paired Wald coverage gates for a positive-variance estimated-score
studentized bridge.  This lets constructor-specific coverage wrappers expose
one compact assumption object instead of repeating the full LLN/CLT,
known-score, and first-step interface list.
-/
structure PATEPATTFiniteScoreCellEstimatedScorePositiveVarianceWaldAssumptions
    (studentized_bridge :
      PATEPATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge
        PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l) :
    Prop where
  hpate_design :
    studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.survey_design_regularity
  hpate_bounded :
    studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators
  hpate_array_lln :
    studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln
  hpate_finite :
    studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions
  hpate_envelope :
    studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.envelope_convergence
  hpate_simplex :
    studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares
  hpate_linear :
    studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance
  hpate_matrix :
    studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified
  hpatt_design :
    studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.survey_design_regularity
  hpatt_bounded :
    studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators
  hpatt_array_lln :
    studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln
  hpatt_finite :
    studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions
  hpatt_envelope :
    studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.envelope_convergence
  hpatt_simplex :
    studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares
  hpatt_linear :
    studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance
  hpatt_matrix :
    studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified
  hpate_decomp :
    studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.pate_known_score_bridge.aggregate_hajek_decomposition
  hpate_denominator :
    studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.pate_known_score_bridge.denominator_stabilization
  hpate_heterogeneity :
    studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.pate_known_score_bridge.heterogeneity_clt
  hpate_residual :
    studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.pate_known_score_bridge.residual_clt
  hpatt_decomp :
    studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.patt_known_score_bridge.aggregate_hajek_decomposition
  hpatt_denominator :
    studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.patt_known_score_bridge.denominator_stabilization
  hpatt_heterogeneity :
    studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.patt_known_score_bridge.heterogeneity_clt
  hpatt_residual :
    studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.patt_known_score_bridge.residual_clt
  hpate_first :
    studentized_bridge.finite_estimated_bridge.pate_estimated_score_bridge.first_step_asymptotic_linearization
  hpate_local :
    studentized_bridge.finite_estimated_bridge.pate_estimated_score_bridge.matching_functional_local_expansion
  hpate_godambe :
    studentized_bridge.finite_estimated_bridge.pate_estimated_score_bridge.godambe_variance_identity
  hpatt_first :
    studentized_bridge.finite_estimated_bridge.patt_estimated_score_bridge.first_step_asymptotic_linearization
  hpatt_local :
    studentized_bridge.finite_estimated_bridge.patt_estimated_score_bridge.matching_functional_local_expansion
  hpatt_godambe :
    studentized_bridge.finite_estimated_bridge.patt_estimated_score_bridge.godambe_variance_identity

/-- Absolute paired Wald coverage conclusion from the compact gate bundle. -/
theorem PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion_of_assumptions
    (b :
      PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge
        PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l)
    (h :
      PATEPATTFiniteScoreCellEstimatedScorePositiveVarianceWaldAssumptions
        b.studentized_bridge) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion b := by
  simpa [PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion] using
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score
      b h.hpate_design h.hpate_bounded h.hpate_array_lln h.hpate_finite
      h.hpate_envelope h.hpate_simplex h.hpate_linear h.hpate_matrix
      h.hpatt_design h.hpatt_bounded h.hpatt_array_lln h.hpatt_finite
      h.hpatt_envelope h.hpatt_simplex h.hpatt_linear h.hpatt_matrix
      h.hpate_decomp h.hpate_denominator h.hpate_heterogeneity
      h.hpate_residual h.hpatt_decomp h.hpatt_denominator
      h.hpatt_heterogeneity h.hpatt_residual h.hpate_first h.hpate_local
      h.hpate_godambe h.hpatt_first h.hpatt_local h.hpatt_godambe

/-- Two-sided paired Wald coverage conclusion from the compact gate bundle. -/
theorem PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion_of_assumptions
    (b :
      PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge
        PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l)
    (h :
      PATEPATTFiniteScoreCellEstimatedScorePositiveVarianceWaldAssumptions
        b.studentized_bridge) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b := by
  simpa [PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion] using
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score
      b h.hpate_design h.hpate_bounded h.hpate_array_lln h.hpate_finite
      h.hpate_envelope h.hpate_simplex h.hpate_linear h.hpate_matrix
      h.hpatt_design h.hpatt_bounded h.hpatt_array_lln h.hpatt_finite
      h.hpatt_envelope h.hpatt_simplex h.hpatt_linear h.hpatt_matrix
      h.hpate_decomp h.hpate_denominator h.hpate_heterogeneity
      h.hpate_residual h.hpatt_decomp h.hpatt_denominator
      h.hpatt_heterogeneity h.hpatt_residual h.hpate_first h.hpate_local
      h.hpate_godambe h.hpatt_first h.hpatt_local h.hpatt_godambe

/--
Paired two-sided finite score-cell estimated-score Wald coverage directly from
strict projection slack and nonnegative target drift in both the PATE and PATT
estimated-score variance components.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit
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
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_lt_limit
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
        pate_coverage_input patt_coverage_input) := by
  let b :=
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_lt_limit
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
      pate_coverage_input patt_coverage_input
  simpa [PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion, b] using
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score
      b hpate_design hpate_bounded hpate_array_lln hpate_finite
      hpate_envelope hpate_simplex hpate_linear hpate_matrix hpatt_design
      hpatt_bounded hpatt_array_lln hpatt_finite hpatt_envelope
      hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      hpate_local hpate_godambe hpatt_first hpatt_local hpatt_godambe

/--
Paired two-sided finite score-cell estimated-score Wald coverage directly from
absolute variance-calibration inputs, strict projection slack, and nonnegative
target drift in both the PATE and PATT estimated-score variance components.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_lt_limit
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
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_lt_limit
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
        pate_coverage_input patt_coverage_input) := by
  let b :=
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_lt_limit
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
      pate_coverage_input patt_coverage_input
  simpa [PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion, b] using
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score
      b hpate_design hpate_bounded hpate_array_lln hpate_finite
      hpate_envelope hpate_simplex hpate_linear hpate_matrix hpatt_design
      hpatt_bounded hpatt_array_lln hpatt_finite hpatt_envelope
      hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      hpate_local hpate_godambe hpatt_first hpatt_local hpatt_godambe

/--
Paired absolute finite score-cell estimated-score Wald coverage directly from
two-sided variance-calibration inputs, strict projection slack, and nonnegative
target drift in both the PATE and PATT estimated-score variance components.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_lt_limit
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
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_lt_limit
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
        pate_coverage_input patt_coverage_input) := by
  let b :=
    patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_lt_limit
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
      pate_coverage_input patt_coverage_input
  simpa [PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion, b] using
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score
      b hpate_design hpate_bounded hpate_array_lln hpate_finite
      hpate_envelope hpate_simplex hpate_linear hpate_matrix hpatt_design
      hpatt_bounded hpatt_array_lln hpatt_finite hpatt_envelope
      hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      hpate_local hpate_godambe hpatt_first hpatt_local hpatt_godambe

/--
Paired two-sided finite score-cell estimated-score Wald coverage directly from
weak projection slack and positive target drift in both the PATE and PATT
estimated-score variance components.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit
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
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_le_drift_pos_limit
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
        pate_coverage_input patt_coverage_input) := by
  let b :=
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_le_drift_pos_limit
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
      pate_coverage_input patt_coverage_input
  simpa [PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion, b] using
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score
      b hpate_design hpate_bounded hpate_array_lln hpate_finite
      hpate_envelope hpate_simplex hpate_linear hpate_matrix hpatt_design
      hpatt_bounded hpatt_array_lln hpatt_finite hpatt_envelope
      hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      hpate_local hpate_godambe hpatt_first hpatt_local hpatt_godambe

/--
Paired two-sided finite score-cell estimated-score Wald coverage directly from
absolute variance-calibration inputs, weak projection slack, and positive
target drift in both the PATE and PATT estimated-score variance components.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_le_drift_pos_limit
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
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_le_drift_pos_limit
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
        pate_coverage_input patt_coverage_input) := by
  let b :=
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_le_drift_pos_limit
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
      pate_coverage_input patt_coverage_input
  simpa [PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion, b] using
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score
      b hpate_design hpate_bounded hpate_array_lln hpate_finite
      hpate_envelope hpate_simplex hpate_linear hpate_matrix hpatt_design
      hpatt_bounded hpatt_array_lln hpatt_finite hpatt_envelope
      hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      hpate_local hpate_godambe hpatt_first hpatt_local hpatt_godambe

/--
Paired absolute finite score-cell estimated-score Wald coverage directly from
two-sided variance-calibration inputs, weak projection slack, and positive
target drift in both the PATE and PATT estimated-score variance components.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_le_drift_pos_limit
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
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_le_drift_pos_limit
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
        pate_coverage_input patt_coverage_input) := by
  let b :=
    patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_le_drift_pos_limit
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
      pate_coverage_input patt_coverage_input
  simpa [PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion, b] using
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score
      b hpate_design hpate_bounded hpate_array_lln hpate_finite
      hpate_envelope hpate_simplex hpate_linear hpate_matrix hpatt_design
      hpatt_bounded hpatt_array_lln hpatt_finite hpatt_envelope
      hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      hpate_local hpate_godambe hpatt_first hpatt_local hpatt_godambe

/--
Paired absolute finite score-cell estimated-score Wald coverage directly from
fixed-law strict projection slack in both the PATE and PATT estimated-score
variance components.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit
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
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit
        finite_estimated_bridge pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_limit pate_oracleLimit
        pate_projectionLimit hpate_oracle hpate_projection
        hpate_projectionLimit_lt_oracle hpate_inverse_meas
        pate_estimated_score_to_scaled_tendsto patt_scaledStatistic
        patt_oracle patt_projectionReduction patt_limit patt_oracleLimit
        patt_projectionLimit hpatt_oracle hpatt_projection
        hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
        patt_estimated_score_to_scaled_tendsto
        pate_coverage_input patt_coverage_input) := by
  let b :=
    patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit
      finite_estimated_bridge pate_scaledStatistic pate_oracle
      pate_projectionReduction pate_limit pate_oracleLimit
      pate_projectionLimit hpate_oracle hpate_projection
      hpate_projectionLimit_lt_oracle hpate_inverse_meas
      pate_estimated_score_to_scaled_tendsto patt_scaledStatistic
      patt_oracle patt_projectionReduction patt_limit patt_oracleLimit
      patt_projectionLimit hpatt_oracle hpatt_projection
      hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
      patt_estimated_score_to_scaled_tendsto
      pate_coverage_input patt_coverage_input
  simpa [PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion, b] using
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score
      b hpate_design hpate_bounded hpate_array_lln hpate_finite
      hpate_envelope hpate_simplex hpate_linear hpate_matrix hpatt_design
      hpatt_bounded hpatt_array_lln hpatt_finite hpatt_envelope
      hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      hpate_local hpate_godambe hpatt_first hpatt_local hpatt_godambe

/--
Paired two-sided finite score-cell estimated-score Wald coverage directly from
fixed-law strict projection slack in both the PATE and PATT estimated-score
variance components.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit
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
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit
        finite_estimated_bridge pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_limit pate_oracleLimit
        pate_projectionLimit hpate_oracle hpate_projection
        hpate_projectionLimit_lt_oracle hpate_inverse_meas
        pate_estimated_score_to_scaled_tendsto patt_scaledStatistic
        patt_oracle patt_projectionReduction patt_limit patt_oracleLimit
        patt_projectionLimit hpatt_oracle hpatt_projection
        hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
        patt_estimated_score_to_scaled_tendsto
        pate_coverage_input patt_coverage_input) := by
  let b :=
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit
      finite_estimated_bridge pate_scaledStatistic pate_oracle
      pate_projectionReduction pate_limit pate_oracleLimit
      pate_projectionLimit hpate_oracle hpate_projection
      hpate_projectionLimit_lt_oracle hpate_inverse_meas
      pate_estimated_score_to_scaled_tendsto patt_scaledStatistic
      patt_oracle patt_projectionReduction patt_limit patt_oracleLimit
      patt_projectionLimit hpatt_oracle hpatt_projection
      hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
      patt_estimated_score_to_scaled_tendsto
      pate_coverage_input patt_coverage_input
  simpa [PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion, b] using
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score
      b hpate_design hpate_bounded hpate_array_lln hpate_finite
      hpate_envelope hpate_simplex hpate_linear hpate_matrix hpatt_design
      hpatt_bounded hpatt_array_lln hpatt_finite hpatt_envelope
      hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      hpate_local hpate_godambe hpatt_first hpatt_local hpatt_godambe

/--
Paired two-sided finite score-cell estimated-score Wald coverage directly from
absolute variance-calibration inputs and fixed-law strict projection slack in
both the PATE and PATT estimated-score variance components.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_fixedLaw_projection_lt_limit
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
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_fixedLaw_projection_lt_limit
        finite_estimated_bridge pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_limit pate_oracleLimit
        pate_projectionLimit hpate_oracle hpate_projection
        hpate_projectionLimit_lt_oracle hpate_inverse_meas
        pate_estimated_score_to_scaled_tendsto patt_scaledStatistic
        patt_oracle patt_projectionReduction patt_limit patt_oracleLimit
        patt_projectionLimit hpatt_oracle hpatt_projection
        hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
        patt_estimated_score_to_scaled_tendsto
        pate_coverage_input patt_coverage_input) := by
  let b :=
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_fixedLaw_projection_lt_limit
      finite_estimated_bridge pate_scaledStatistic pate_oracle
      pate_projectionReduction pate_limit pate_oracleLimit
      pate_projectionLimit hpate_oracle hpate_projection
      hpate_projectionLimit_lt_oracle hpate_inverse_meas
      pate_estimated_score_to_scaled_tendsto patt_scaledStatistic
      patt_oracle patt_projectionReduction patt_limit patt_oracleLimit
      patt_projectionLimit hpatt_oracle hpatt_projection
      hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
      patt_estimated_score_to_scaled_tendsto
      pate_coverage_input patt_coverage_input
  simpa [PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion, b] using
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score
      b hpate_design hpate_bounded hpate_array_lln hpate_finite
      hpate_envelope hpate_simplex hpate_linear hpate_matrix hpatt_design
      hpatt_bounded hpatt_array_lln hpatt_finite hpatt_envelope
      hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      hpate_local hpate_godambe hpatt_first hpatt_local hpatt_godambe

/--
Paired absolute finite score-cell estimated-score Wald coverage directly from
two-sided variance-calibration inputs and fixed-law strict projection slack in
both the PATE and PATT estimated-score variance components.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_fixedLaw_projection_lt_limit
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
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_fixedLaw_projection_lt_limit
        finite_estimated_bridge pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_limit pate_oracleLimit
        pate_projectionLimit hpate_oracle hpate_projection
        hpate_projectionLimit_lt_oracle hpate_inverse_meas
        pate_estimated_score_to_scaled_tendsto patt_scaledStatistic
        patt_oracle patt_projectionReduction patt_limit patt_oracleLimit
        patt_projectionLimit hpatt_oracle hpatt_projection
        hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
        patt_estimated_score_to_scaled_tendsto
        pate_coverage_input patt_coverage_input) := by
  let b :=
    patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_fixedLaw_projection_lt_limit
      finite_estimated_bridge pate_scaledStatistic pate_oracle
      pate_projectionReduction pate_limit pate_oracleLimit
      pate_projectionLimit hpate_oracle hpate_projection
      hpate_projectionLimit_lt_oracle hpate_inverse_meas
      pate_estimated_score_to_scaled_tendsto patt_scaledStatistic
      patt_oracle patt_projectionReduction patt_limit patt_oracleLimit
      patt_projectionLimit hpatt_oracle hpatt_projection
      hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
      patt_estimated_score_to_scaled_tendsto
      pate_coverage_input patt_coverage_input
  simpa [PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion, b] using
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score
      b hpate_design hpate_bounded hpate_array_lln hpate_finite
      hpate_envelope hpate_simplex hpate_linear hpate_matrix hpatt_design
      hpatt_bounded hpatt_array_lln hpatt_finite hpatt_envelope
      hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      hpate_local hpate_godambe hpatt_first hpatt_local hpatt_godambe

/-! ## Score-adjusted paired coverage wrappers -/

/--
Paired absolute Wald coverage from score-quadratic projection and target-drift
reductions under strict projection slack.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_scoreAdjusted_projection_lt_limit
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
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (h :
      let b :=
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
          pate_coverage_input patt_coverage_input
      PATEPATTFiniteScoreCellEstimatedScorePositiveVarianceWaldAssumptions
        b.studentized_bridge) :
    let b :=
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
        pate_coverage_input patt_coverage_input
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion b := by
  let b :=
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
      pate_coverage_input patt_coverage_input
  simpa [b] using
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion_of_assumptions
      b h

/--
Paired two-sided Wald coverage from score-quadratic projection and target-drift
reductions under strict projection slack.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_scoreAdjusted_projection_lt_limit
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
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (h :
      let b :=
        patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_scoreAdjusted_projection_lt_limit
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
          pate_coverage_input patt_coverage_input
      PATEPATTFiniteScoreCellEstimatedScorePositiveVarianceWaldAssumptions
        b.studentized_bridge) :
    let b :=
      patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_scoreAdjusted_projection_lt_limit
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
        pate_coverage_input patt_coverage_input
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b := by
  let b :=
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_scoreAdjusted_projection_lt_limit
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
      pate_coverage_input patt_coverage_input
  simpa [b] using
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion_of_assumptions
      b h

/--
Paired two-sided Wald coverage from absolute calibration inputs and
score-quadratic reductions under strict projection slack.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_scoreAdjusted_projection_lt_limit
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
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (h :
      let b :=
        patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_scoreAdjusted_projection_lt_limit
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
          pate_coverage_input patt_coverage_input
      PATEPATTFiniteScoreCellEstimatedScorePositiveVarianceWaldAssumptions
        b.studentized_bridge) :
    let b :=
      patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_scoreAdjusted_projection_lt_limit
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
        pate_coverage_input patt_coverage_input
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b := by
  let b :=
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_scoreAdjusted_projection_lt_limit
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
      pate_coverage_input patt_coverage_input
  simpa [b] using
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion_of_assumptions
      b h

section ScoreAdjustedStrictTwoSidedToAbsoluteCoverage

variable
    (finite_estimated_bridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell PATTCell)
variable (pateParameters : Finset PATEParam)
variable (pattParameters : Finset PATTParam)
variable (pate_scaledStatistic patt_scaledStatistic : Index -> Sample -> Real)
variable (pate_oracle patt_oracle : Index -> Sample -> Real)
variable (pateFirstStepLoading pateTargetDriftLoading : PATEParam -> Real)
variable (pattFirstStepLoading pattTargetDriftLoading : PATTParam -> Real)
variable (pateScoreCovariance :
  Index -> Sample -> PATEParam -> PATEParam -> Real)
variable (pattScoreCovariance :
  Index -> Sample -> PATTParam -> PATTParam -> Real)
variable (pate_limit patt_limit : LimitSample -> Real)
variable (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
variable (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
variable (hpate_oracle :
  TendstoInMeasure sampleLaw pate_oracle l
    (fun _sample => pate_oracleLimit))
variable (hpate_projection :
  TendstoInMeasure sampleLaw
    (fun index sample =>
      scoreQuadraticForm pateParameters pateFirstStepLoading
        (pateScoreCovariance index sample))
    l (fun _sample => pate_projectionLimit))
variable (hpate_drift :
  TendstoInMeasure sampleLaw
    (fun index sample =>
      scoreQuadraticForm pateParameters pateTargetDriftLoading
        (pateScoreCovariance index sample))
    l (fun _sample => pate_targetDriftLimit))
variable (hpate_projectionLimit_lt_oracle :
  pate_projectionLimit < pate_oracleLimit)
variable (hpate_driftLimit_nonneg : 0 ≤ pate_targetDriftLimit)
variable (hpate_inverse_meas :
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
variable (pate_estimated_score_to_scaled_tendsto :
  finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ->
    TendstoInDistribution pate_scaledStatistic l pate_limit
      (fun _index => sampleLaw) limitLaw)
variable (hpatt_oracle :
  TendstoInMeasure sampleLaw patt_oracle l
    (fun _sample => patt_oracleLimit))
variable (hpatt_projection :
  TendstoInMeasure sampleLaw
    (fun index sample =>
      scoreQuadraticForm pattParameters pattFirstStepLoading
        (pattScoreCovariance index sample))
    l (fun _sample => patt_projectionLimit))
variable (hpatt_drift :
  TendstoInMeasure sampleLaw
    (fun index sample =>
      scoreQuadraticForm pattParameters pattTargetDriftLoading
        (pattScoreCovariance index sample))
    l (fun _sample => patt_targetDriftLimit))
variable (hpatt_projectionLimit_lt_oracle :
  patt_projectionLimit < patt_oracleLimit)
variable (hpatt_driftLimit_nonneg : 0 ≤ patt_targetDriftLimit)
variable (hpatt_inverse_meas :
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
variable (patt_estimated_score_to_scaled_tendsto :
  finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ->
    TendstoInDistribution patt_scaledStatistic l patt_limit
      (fun _index => sampleLaw) limitLaw)

/--
Paired absolute Wald coverage from two-sided calibration inputs and
score-quadratic reductions under strict projection slack.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_scoreAdjusted_projection_lt_limit
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (h :
      let b :=
        patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_scoreAdjusted_projection_lt_limit
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
          pate_coverage_input patt_coverage_input
      PATEPATTFiniteScoreCellEstimatedScorePositiveVarianceWaldAssumptions
        b.studentized_bridge) :
    let b :=
      patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_scoreAdjusted_projection_lt_limit
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
        pate_coverage_input patt_coverage_input
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion b := by
  let b :=
    patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_scoreAdjusted_projection_lt_limit
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
      pate_coverage_input patt_coverage_input
  simpa [b] using
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion_of_assumptions
      b h

end ScoreAdjustedStrictTwoSidedToAbsoluteCoverage

section ScoreAdjustedWeakCoverage

variable
    (finite_estimated_bridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell PATTCell)
variable (pateParameters : Finset PATEParam)
variable (pattParameters : Finset PATTParam)
variable (pate_scaledStatistic patt_scaledStatistic : Index -> Sample -> Real)
variable (pate_oracle patt_oracle : Index -> Sample -> Real)
variable (pateFirstStepLoading pateTargetDriftLoading : PATEParam -> Real)
variable (pattFirstStepLoading pattTargetDriftLoading : PATTParam -> Real)
variable (pateScoreCovariance :
  Index -> Sample -> PATEParam -> PATEParam -> Real)
variable (pattScoreCovariance :
  Index -> Sample -> PATTParam -> PATTParam -> Real)
variable (pate_limit patt_limit : LimitSample -> Real)
variable (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
variable (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
variable (hpate_oracle :
  TendstoInMeasure sampleLaw pate_oracle l
    (fun _sample => pate_oracleLimit))
variable (hpate_projection :
  TendstoInMeasure sampleLaw
    (fun index sample =>
      scoreQuadraticForm pateParameters pateFirstStepLoading
        (pateScoreCovariance index sample))
    l (fun _sample => pate_projectionLimit))
variable (hpate_drift :
  TendstoInMeasure sampleLaw
    (fun index sample =>
      scoreQuadraticForm pateParameters pateTargetDriftLoading
        (pateScoreCovariance index sample))
    l (fun _sample => pate_targetDriftLimit))
variable (hpate_projectionLimit_le_oracle :
  pate_projectionLimit ≤ pate_oracleLimit)
variable (hpate_driftLimit_pos : 0 < pate_targetDriftLimit)
variable (hpate_inverse_meas :
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
variable (pate_estimated_score_to_scaled_tendsto :
  finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ->
    TendstoInDistribution pate_scaledStatistic l pate_limit
      (fun _index => sampleLaw) limitLaw)
variable (hpatt_oracle :
  TendstoInMeasure sampleLaw patt_oracle l
    (fun _sample => patt_oracleLimit))
variable (hpatt_projection :
  TendstoInMeasure sampleLaw
    (fun index sample =>
      scoreQuadraticForm pattParameters pattFirstStepLoading
        (pattScoreCovariance index sample))
    l (fun _sample => patt_projectionLimit))
variable (hpatt_drift :
  TendstoInMeasure sampleLaw
    (fun index sample =>
      scoreQuadraticForm pattParameters pattTargetDriftLoading
        (pattScoreCovariance index sample))
    l (fun _sample => patt_targetDriftLimit))
variable (hpatt_projectionLimit_le_oracle :
  patt_projectionLimit ≤ patt_oracleLimit)
variable (hpatt_driftLimit_pos : 0 < patt_targetDriftLimit)
variable (hpatt_inverse_meas :
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
variable (patt_estimated_score_to_scaled_tendsto :
  finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ->
    TendstoInDistribution patt_scaledStatistic l patt_limit
      (fun _index => sampleLaw) limitLaw)

/--
Paired absolute Wald coverage from score-quadratic reductions under weak
projection slack and positive target-drift limits.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_scoreAdjusted_projection_le_drift_pos_limit
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (h :
      let b :=
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
          pate_coverage_input patt_coverage_input
      PATEPATTFiniteScoreCellEstimatedScorePositiveVarianceWaldAssumptions
        b.studentized_bridge) :
    let b :=
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
        pate_coverage_input patt_coverage_input
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion b := by
  let b :=
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
      pate_coverage_input patt_coverage_input
  simpa [b] using
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion_of_assumptions
      b h

/--
Paired two-sided Wald coverage from score-quadratic reductions under weak
projection slack and positive target-drift limits.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_scoreAdjusted_projection_le_drift_pos_limit
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (h :
      let b :=
        patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_scoreAdjusted_projection_le_drift_pos_limit
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
          pate_coverage_input patt_coverage_input
      PATEPATTFiniteScoreCellEstimatedScorePositiveVarianceWaldAssumptions
        b.studentized_bridge) :
    let b :=
      patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_scoreAdjusted_projection_le_drift_pos_limit
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
        pate_coverage_input patt_coverage_input
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b := by
  let b :=
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_scoreAdjusted_projection_le_drift_pos_limit
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
      pate_coverage_input patt_coverage_input
  simpa [b] using
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion_of_assumptions
      b h

/--
Paired two-sided Wald coverage from absolute calibration inputs and
score-quadratic reductions under weak projection slack.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_scoreAdjusted_projection_le_drift_pos_limit
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (h :
      let b :=
        patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_scoreAdjusted_projection_le_drift_pos_limit
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
          pate_coverage_input patt_coverage_input
      PATEPATTFiniteScoreCellEstimatedScorePositiveVarianceWaldAssumptions
        b.studentized_bridge) :
    let b :=
      patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_scoreAdjusted_projection_le_drift_pos_limit
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
        pate_coverage_input patt_coverage_input
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b := by
  let b :=
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_scoreAdjusted_projection_le_drift_pos_limit
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
      pate_coverage_input patt_coverage_input
  simpa [b] using
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion_of_assumptions
      b h

/--
Paired absolute Wald coverage from two-sided calibration inputs and
score-quadratic reductions under weak projection slack.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_scoreAdjusted_projection_le_drift_pos_limit
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (h :
      let b :=
        patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_scoreAdjusted_projection_le_drift_pos_limit
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
          pate_coverage_input patt_coverage_input
      PATEPATTFiniteScoreCellEstimatedScorePositiveVarianceWaldAssumptions
        b.studentized_bridge) :
    let b :=
      patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_scoreAdjusted_projection_le_drift_pos_limit
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
        pate_coverage_input patt_coverage_input
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion b := by
  let b :=
    patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_scoreAdjusted_projection_le_drift_pos_limit
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
      pate_coverage_input patt_coverage_input
  simpa [b] using
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion_of_assumptions
      b h

end ScoreAdjustedWeakCoverage

section ScoreAdjustedFixedLawCoverage

variable
    (finite_estimated_bridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell PATTCell)
variable (pateParameters : Finset PATEParam)
variable (pattParameters : Finset PATTParam)
variable (pate_scaledStatistic patt_scaledStatistic : Index -> Sample -> Real)
variable (pate_oracle patt_oracle : Index -> Sample -> Real)
variable (pateFirstStepLoading : PATEParam -> Real)
variable (pattFirstStepLoading : PATTParam -> Real)
variable (pateScoreCovariance :
  Index -> Sample -> PATEParam -> PATEParam -> Real)
variable (pattScoreCovariance :
  Index -> Sample -> PATTParam -> PATTParam -> Real)
variable (pate_limit patt_limit : LimitSample -> Real)
variable (pate_oracleLimit pate_projectionLimit : Real)
variable (patt_oracleLimit patt_projectionLimit : Real)
variable (hpate_oracle :
  TendstoInMeasure sampleLaw pate_oracle l
    (fun _sample => pate_oracleLimit))
variable (hpate_projection :
  TendstoInMeasure sampleLaw
    (fun index sample =>
      scoreQuadraticForm pateParameters pateFirstStepLoading
        (pateScoreCovariance index sample))
    l (fun _sample => pate_projectionLimit))
variable (hpate_projectionLimit_lt_oracle :
  pate_projectionLimit < pate_oracleLimit)
variable (hpate_inverse_meas :
  ∀ index,
    AEMeasurable
      (fun sample =>
        (standardError
          (estimatedScoreVariance (pate_oracle index sample)
            (scoreQuadraticForm pateParameters pateFirstStepLoading
              (pateScoreCovariance index sample)) 0))⁻¹)
      sampleLaw)
variable (pate_estimated_score_to_scaled_tendsto :
  finite_estimated_bridge.pate_estimated_score_bridge.estimated_score_asymptotic_normality ->
    TendstoInDistribution pate_scaledStatistic l pate_limit
      (fun _index => sampleLaw) limitLaw)
variable (hpatt_oracle :
  TendstoInMeasure sampleLaw patt_oracle l
    (fun _sample => patt_oracleLimit))
variable (hpatt_projection :
  TendstoInMeasure sampleLaw
    (fun index sample =>
      scoreQuadraticForm pattParameters pattFirstStepLoading
        (pattScoreCovariance index sample))
    l (fun _sample => patt_projectionLimit))
variable (hpatt_projectionLimit_lt_oracle :
  patt_projectionLimit < patt_oracleLimit)
variable (hpatt_inverse_meas :
  ∀ index,
    AEMeasurable
      (fun sample =>
        (standardError
          (estimatedScoreVariance (patt_oracle index sample)
            (scoreQuadraticForm pattParameters pattFirstStepLoading
              (pattScoreCovariance index sample)) 0))⁻¹)
      sampleLaw)
variable (patt_estimated_score_to_scaled_tendsto :
  finite_estimated_bridge.patt_estimated_score_bridge.estimated_score_asymptotic_normality ->
    TendstoInDistribution patt_scaledStatistic l patt_limit
      (fun _index => sampleLaw) limitLaw)

/--
Paired absolute Wald coverage from fixed-law score-quadratic projection
reductions under strict projection slack.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_scoreAdjusted_fixedLaw_projection_lt_limit
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (h :
      let b :=
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
          pate_coverage_input patt_coverage_input
      PATEPATTFiniteScoreCellEstimatedScorePositiveVarianceWaldAssumptions
        b.studentized_bridge) :
    let b :=
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
        pate_coverage_input patt_coverage_input
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion b := by
  let b :=
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
      pate_coverage_input patt_coverage_input
  simpa [b] using
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion_of_assumptions
      b h

/--
Paired two-sided Wald coverage from fixed-law score-quadratic projection
reductions under strict projection slack.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_scoreAdjusted_fixedLaw_projection_lt_limit
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (h :
      let b :=
        patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_scoreAdjusted_fixedLaw_projection_lt_limit
          finite_estimated_bridge pateParameters pattParameters
          pate_scaledStatistic patt_scaledStatistic pate_oracle patt_oracle
          pateFirstStepLoading pattFirstStepLoading pateScoreCovariance
          pattScoreCovariance pate_limit patt_limit pate_oracleLimit
          pate_projectionLimit patt_oracleLimit patt_projectionLimit
          hpate_oracle hpate_projection hpate_projectionLimit_lt_oracle
          hpate_inverse_meas pate_estimated_score_to_scaled_tendsto
          hpatt_oracle hpatt_projection hpatt_projectionLimit_lt_oracle
          hpatt_inverse_meas patt_estimated_score_to_scaled_tendsto
          pate_coverage_input patt_coverage_input
      PATEPATTFiniteScoreCellEstimatedScorePositiveVarianceWaldAssumptions
        b.studentized_bridge) :
    let b :=
      patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_scoreAdjusted_fixedLaw_projection_lt_limit
        finite_estimated_bridge pateParameters pattParameters
        pate_scaledStatistic patt_scaledStatistic pate_oracle patt_oracle
        pateFirstStepLoading pattFirstStepLoading pateScoreCovariance
        pattScoreCovariance pate_limit patt_limit pate_oracleLimit
        pate_projectionLimit patt_oracleLimit patt_projectionLimit
        hpate_oracle hpate_projection hpate_projectionLimit_lt_oracle
        hpate_inverse_meas pate_estimated_score_to_scaled_tendsto
        hpatt_oracle hpatt_projection hpatt_projectionLimit_lt_oracle
        hpatt_inverse_meas patt_estimated_score_to_scaled_tendsto
        pate_coverage_input patt_coverage_input
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b := by
  let b :=
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_scoreAdjusted_fixedLaw_projection_lt_limit
      finite_estimated_bridge pateParameters pattParameters
      pate_scaledStatistic patt_scaledStatistic pate_oracle patt_oracle
      pateFirstStepLoading pattFirstStepLoading pateScoreCovariance
      pattScoreCovariance pate_limit patt_limit pate_oracleLimit
      pate_projectionLimit patt_oracleLimit patt_projectionLimit
      hpate_oracle hpate_projection hpate_projectionLimit_lt_oracle
      hpate_inverse_meas pate_estimated_score_to_scaled_tendsto
      hpatt_oracle hpatt_projection hpatt_projectionLimit_lt_oracle
      hpatt_inverse_meas patt_estimated_score_to_scaled_tendsto
      pate_coverage_input patt_coverage_input
  simpa [b] using
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion_of_assumptions
      b h

/--
Paired two-sided Wald coverage from absolute calibration inputs and fixed-law
score-quadratic projection reductions.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_scoreAdjusted_fixedLaw_projection_lt_limit
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (h :
      let b :=
        patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_scoreAdjusted_fixedLaw_projection_lt_limit
          finite_estimated_bridge pateParameters pattParameters
          pate_scaledStatistic patt_scaledStatistic pate_oracle patt_oracle
          pateFirstStepLoading pattFirstStepLoading pateScoreCovariance
          pattScoreCovariance pate_limit patt_limit pate_oracleLimit
          pate_projectionLimit patt_oracleLimit patt_projectionLimit
          hpate_oracle hpate_projection hpate_projectionLimit_lt_oracle
          hpate_inverse_meas pate_estimated_score_to_scaled_tendsto
          hpatt_oracle hpatt_projection hpatt_projectionLimit_lt_oracle
          hpatt_inverse_meas patt_estimated_score_to_scaled_tendsto
          pate_coverage_input patt_coverage_input
      PATEPATTFiniteScoreCellEstimatedScorePositiveVarianceWaldAssumptions
        b.studentized_bridge) :
    let b :=
      patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_scoreAdjusted_fixedLaw_projection_lt_limit
        finite_estimated_bridge pateParameters pattParameters
        pate_scaledStatistic patt_scaledStatistic pate_oracle patt_oracle
        pateFirstStepLoading pattFirstStepLoading pateScoreCovariance
        pattScoreCovariance pate_limit patt_limit pate_oracleLimit
        pate_projectionLimit patt_oracleLimit patt_projectionLimit
        hpate_oracle hpate_projection hpate_projectionLimit_lt_oracle
        hpate_inverse_meas pate_estimated_score_to_scaled_tendsto
        hpatt_oracle hpatt_projection hpatt_projectionLimit_lt_oracle
        hpatt_inverse_meas patt_estimated_score_to_scaled_tendsto
        pate_coverage_input patt_coverage_input
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion b := by
  let b :=
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_scoreAdjusted_fixedLaw_projection_lt_limit
      finite_estimated_bridge pateParameters pattParameters
      pate_scaledStatistic patt_scaledStatistic pate_oracle patt_oracle
      pateFirstStepLoading pattFirstStepLoading pateScoreCovariance
      pattScoreCovariance pate_limit patt_limit pate_oracleLimit
      pate_projectionLimit patt_oracleLimit patt_projectionLimit
      hpate_oracle hpate_projection hpate_projectionLimit_lt_oracle
      hpate_inverse_meas pate_estimated_score_to_scaled_tendsto
      hpatt_oracle hpatt_projection hpatt_projectionLimit_lt_oracle
      hpatt_inverse_meas patt_estimated_score_to_scaled_tendsto
      pate_coverage_input patt_coverage_input
  simpa [b] using
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion_of_assumptions
      b h

/--
Paired absolute Wald coverage from two-sided calibration inputs and fixed-law
score-quadratic projection reductions.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_scoreAdjusted_fixedLaw_projection_lt_limit
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (h :
      let b :=
        patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_scoreAdjusted_fixedLaw_projection_lt_limit
          finite_estimated_bridge pateParameters pattParameters
          pate_scaledStatistic patt_scaledStatistic pate_oracle patt_oracle
          pateFirstStepLoading pattFirstStepLoading pateScoreCovariance
          pattScoreCovariance pate_limit patt_limit pate_oracleLimit
          pate_projectionLimit patt_oracleLimit patt_projectionLimit
          hpate_oracle hpate_projection hpate_projectionLimit_lt_oracle
          hpate_inverse_meas pate_estimated_score_to_scaled_tendsto
          hpatt_oracle hpatt_projection hpatt_projectionLimit_lt_oracle
          hpatt_inverse_meas patt_estimated_score_to_scaled_tendsto
          pate_coverage_input patt_coverage_input
      PATEPATTFiniteScoreCellEstimatedScorePositiveVarianceWaldAssumptions
        b.studentized_bridge) :
    let b :=
      patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_scoreAdjusted_fixedLaw_projection_lt_limit
        finite_estimated_bridge pateParameters pattParameters
        pate_scaledStatistic patt_scaledStatistic pate_oracle patt_oracle
        pateFirstStepLoading pattFirstStepLoading pateScoreCovariance
        pattScoreCovariance pate_limit patt_limit pate_oracleLimit
        pate_projectionLimit patt_oracleLimit patt_projectionLimit
        hpate_oracle hpate_projection hpate_projectionLimit_lt_oracle
        hpate_inverse_meas pate_estimated_score_to_scaled_tendsto
        hpatt_oracle hpatt_projection hpatt_projectionLimit_lt_oracle
        hpatt_inverse_meas patt_estimated_score_to_scaled_tendsto
        pate_coverage_input patt_coverage_input
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion b := by
  let b :=
    patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_scoreAdjusted_fixedLaw_projection_lt_limit
      finite_estimated_bridge pateParameters pattParameters
      pate_scaledStatistic patt_scaledStatistic pate_oracle patt_oracle
      pateFirstStepLoading pattFirstStepLoading pateScoreCovariance
      pattScoreCovariance pate_limit patt_limit pate_oracleLimit
      pate_projectionLimit patt_oracleLimit patt_projectionLimit
      hpate_oracle hpate_projection hpate_projectionLimit_lt_oracle
      hpate_inverse_meas pate_estimated_score_to_scaled_tendsto
      hpatt_oracle hpatt_projection hpatt_projectionLimit_lt_oracle
      hpatt_inverse_meas patt_estimated_score_to_scaled_tendsto
      pate_coverage_input patt_coverage_input
  simpa [b] using
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion_of_assumptions
      b h

end ScoreAdjustedFixedLawCoverage

/--
Paired absolute finite score-cell estimated-score Wald coverage directly from
strict projection slack and nonnegative target drift, with the PATE/PATT
local-experiment derivative, equicontinuity, and Godambe obligations packaged
as one compact core per estimand.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit_local_experiment_core
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
    (hpate_estimated_score_to_scaled_tendsto :
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
    (hpatt_estimated_score_to_scaled_tendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
    let pateStudentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l :=
      estimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
        pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
        hpate_inverse_meas
    let pattStudentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l :=
      estimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
        hpatt_inverse_meas
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
      Tendsto
        (fun index =>
          eventProbabilityReal (pate_coverage_input.sampleLawSeq index)
            (fun sample =>
              waldCovers (pate_coverage_input.estimator index sample)
                (pate_coverage_input.target index)
                (pate_coverage_input.criticalValue index)
                (standardError
                  (pate_coverage_input.varianceEstimate index sample))
                (pate_coverage_input.scale index)))
        l (nhds pate_coverage_input.coverageLimit) ∧
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
        (fun _index => sampleLaw) limitLaw ∧
      Tendsto
        (fun index =>
          eventProbabilityReal (patt_coverage_input.sampleLawSeq index)
            (fun sample =>
              waldCovers (patt_coverage_input.estimator index sample)
                (patt_coverage_input.target index)
                (patt_coverage_input.criticalValue index)
                (standardError
                  (patt_coverage_input.varianceEstimate index sample))
                (patt_coverage_input.scale index)))
        l (nhds patt_coverage_input.coverageLimit) := by
  let pateStudentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l :=
    estimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit
      pate_scaledStatistic pate_oracle pate_projectionReduction
      pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
      pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
      hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
      hpate_inverse_meas
  let pattStudentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l :=
    estimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit
      patt_scaledStatistic patt_oracle patt_projectionReduction
      patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
      patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
      hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
      hpatt_inverse_meas
  simpa [pateStudentizationInput, pattStudentizationInput] using
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score_local_experiment_core
      known pateEstimated pattEstimated pateStudentizationInput
      pattStudentizationInput pate_coverage_input patt_coverage_input
      hpate_known_to_estimated hpatt_known_to_estimated
      hpate_estimated_score_to_scaled_tendsto
      hpatt_estimated_score_to_scaled_tendsto hpate_design hpate_bounded
      hpate_array_lln hpate_finite hpate_envelope hpate_simplex
      hpate_linear hpate_matrix hpatt_design hpatt_bounded
      hpatt_array_lln hpatt_finite hpatt_envelope hpatt_simplex
        hpatt_linear hpatt_matrix hpate_decomp hpate_denominator
        hpate_heterogeneity hpate_residual hpatt_decomp hpatt_denominator
        hpatt_heterogeneity hpatt_residual hpate_first hpate_score
        hpate_core hpatt_first hpatt_score hpatt_core

/--
Paired two-sided finite score-cell estimated-score Wald coverage directly from
strict projection slack and nonnegative target drift, with the PATE/PATT
local-experiment derivative, equicontinuity, and Godambe obligations packaged
as one compact core per estimand.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit_local_experiment_core
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
    (hpate_estimated_score_to_scaled_tendsto :
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
    (hpatt_estimated_score_to_scaled_tendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    let pateStudentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l :=
      estimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
        pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
        hpate_inverse_meas
    let pattStudentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l :=
      estimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
        hpatt_inverse_meas
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
      Tendsto
        (fun index =>
          eventProbabilityReal (pate_coverage_input.sampleLawSeq index)
            (fun sample =>
              waldCovers (pate_coverage_input.estimator index sample)
                (pate_coverage_input.target index)
                (pate_coverage_input.criticalValue index)
                (standardError
                  (pate_coverage_input.varianceEstimate index sample))
                (pate_coverage_input.scale index)))
        l (nhds pate_coverage_input.coverageLimit) ∧
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
        (fun _index => sampleLaw) limitLaw ∧
      Tendsto
        (fun index =>
          eventProbabilityReal (patt_coverage_input.sampleLawSeq index)
            (fun sample =>
              waldCovers (patt_coverage_input.estimator index sample)
                (patt_coverage_input.target index)
                (patt_coverage_input.criticalValue index)
                (standardError
                  (patt_coverage_input.varianceEstimate index sample))
                (patt_coverage_input.scale index)))
        l (nhds patt_coverage_input.coverageLimit) := by
  let pateStudentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l :=
    estimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit
      pate_scaledStatistic pate_oracle pate_projectionReduction
      pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
      pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
      hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
      hpate_inverse_meas
  let pattStudentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l :=
    estimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit
      patt_scaledStatistic patt_oracle patt_projectionReduction
      patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
      patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
      hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
      hpatt_inverse_meas
  simpa [pateStudentizationInput, pattStudentizationInput] using
      pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score_local_experiment_core
        known pateEstimated pattEstimated pateStudentizationInput
        pattStudentizationInput pate_coverage_input patt_coverage_input
        hpate_known_to_estimated hpatt_known_to_estimated
        hpate_estimated_score_to_scaled_tendsto
        hpatt_estimated_score_to_scaled_tendsto hpate_design hpate_bounded
        hpate_array_lln hpate_finite hpate_envelope hpate_simplex
        hpate_linear hpate_matrix hpatt_design hpatt_bounded
        hpatt_array_lln hpatt_finite hpatt_envelope hpatt_simplex
        hpatt_linear hpatt_matrix hpate_decomp hpate_denominator
        hpate_heterogeneity hpate_residual hpatt_decomp hpatt_denominator
        hpatt_heterogeneity hpatt_residual hpate_first hpate_score
        hpate_core hpatt_first hpatt_score hpatt_core

  /--
  Paired absolute finite score-cell estimated-score Wald coverage directly from
  weak projection slack and positive target drift, with the PATE/PATT
  local-experiment derivative, equicontinuity, and Godambe obligations packaged
  as one compact core per estimand.
  -/
  theorem
      pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit_local_experiment_core
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
      (hpate_estimated_score_to_scaled_tendsto :
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
      (hpatt_estimated_score_to_scaled_tendsto :
        pattEstimated.estimated_score_asymptotic_normality ->
          TendstoInDistribution patt_scaledStatistic l patt_limit
            (fun _index => sampleLaw) limitLaw)
      (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
      (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
      let pateStudentizationInput :
        EstimatedScorePositiveVarianceStudentizationInput Index Sample
          LimitSample sampleLaw limitLaw l :=
        estimatedScorePositiveVarianceStudentizationInput_of_projection_le_drift_pos_limit
          pate_scaledStatistic pate_oracle pate_projectionReduction
          pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
          pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
          hpate_projectionLimit_le_oracle hpate_driftLimit_pos
          hpate_inverse_meas
      let pattStudentizationInput :
        EstimatedScorePositiveVarianceStudentizationInput Index Sample
          LimitSample sampleLaw limitLaw l :=
        estimatedScorePositiveVarianceStudentizationInput_of_projection_le_drift_pos_limit
          patt_scaledStatistic patt_oracle patt_projectionReduction
          patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
          patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
          hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
          hpatt_inverse_meas
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
        Tendsto
          (fun index =>
            eventProbabilityReal (pate_coverage_input.sampleLawSeq index)
              (fun sample =>
                waldCovers (pate_coverage_input.estimator index sample)
                  (pate_coverage_input.target index)
                  (pate_coverage_input.criticalValue index)
                  (standardError
                    (pate_coverage_input.varianceEstimate index sample))
                  (pate_coverage_input.scale index)))
          l (nhds pate_coverage_input.coverageLimit) ∧
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
          (fun _index => sampleLaw) limitLaw ∧
        Tendsto
          (fun index =>
            eventProbabilityReal (patt_coverage_input.sampleLawSeq index)
              (fun sample =>
                waldCovers (patt_coverage_input.estimator index sample)
                  (patt_coverage_input.target index)
                  (patt_coverage_input.criticalValue index)
                  (standardError
                    (patt_coverage_input.varianceEstimate index sample))
                  (patt_coverage_input.scale index)))
          l (nhds patt_coverage_input.coverageLimit) := by
    let pateStudentizationInput :
        EstimatedScorePositiveVarianceStudentizationInput Index Sample
          LimitSample sampleLaw limitLaw l :=
      estimatedScorePositiveVarianceStudentizationInput_of_projection_le_drift_pos_limit
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
        pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_le_oracle hpate_driftLimit_pos
        hpate_inverse_meas
    let pattStudentizationInput :
        EstimatedScorePositiveVarianceStudentizationInput Index Sample
          LimitSample sampleLaw limitLaw l :=
      estimatedScorePositiveVarianceStudentizationInput_of_projection_le_drift_pos_limit
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
        hpatt_inverse_meas
    simpa [pateStudentizationInput, pattStudentizationInput] using
      pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score_local_experiment_core
        known pateEstimated pattEstimated pateStudentizationInput
        pattStudentizationInput pate_coverage_input patt_coverage_input
        hpate_known_to_estimated hpatt_known_to_estimated
        hpate_estimated_score_to_scaled_tendsto
        hpatt_estimated_score_to_scaled_tendsto hpate_design hpate_bounded
        hpate_array_lln hpate_finite hpate_envelope hpate_simplex
        hpate_linear hpate_matrix hpatt_design hpatt_bounded
        hpatt_array_lln hpatt_finite hpatt_envelope hpatt_simplex
        hpatt_linear hpatt_matrix hpate_decomp hpate_denominator
        hpate_heterogeneity hpate_residual hpatt_decomp hpatt_denominator
        hpatt_heterogeneity hpatt_residual hpate_first hpate_score
              hpate_core hpatt_first hpatt_score hpatt_core

/--
Paired two-sided finite score-cell estimated-score Wald coverage directly from
weak projection slack and positive target drift, with the PATE/PATT
local-experiment derivative, equicontinuity, and Godambe obligations packaged
as one compact core per estimand.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit_local_experiment_core
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
    (hpate_estimated_score_to_scaled_tendsto :
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
    (hpatt_estimated_score_to_scaled_tendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    let pateStudentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l :=
      estimatedScorePositiveVarianceStudentizationInput_of_projection_le_drift_pos_limit
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
        pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_le_oracle hpate_driftLimit_pos
        hpate_inverse_meas
    let pattStudentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l :=
      estimatedScorePositiveVarianceStudentizationInput_of_projection_le_drift_pos_limit
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
        hpatt_inverse_meas
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
      Tendsto
        (fun index =>
          eventProbabilityReal (pate_coverage_input.sampleLawSeq index)
            (fun sample =>
              waldCovers (pate_coverage_input.estimator index sample)
                (pate_coverage_input.target index)
                (pate_coverage_input.criticalValue index)
                (standardError
                  (pate_coverage_input.varianceEstimate index sample))
                (pate_coverage_input.scale index)))
        l (nhds pate_coverage_input.coverageLimit) ∧
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
        (fun _index => sampleLaw) limitLaw ∧
      Tendsto
        (fun index =>
          eventProbabilityReal (patt_coverage_input.sampleLawSeq index)
            (fun sample =>
              waldCovers (patt_coverage_input.estimator index sample)
                (patt_coverage_input.target index)
                (patt_coverage_input.criticalValue index)
                (standardError
                  (patt_coverage_input.varianceEstimate index sample))
                (patt_coverage_input.scale index)))
        l (nhds patt_coverage_input.coverageLimit) := by
  let pateStudentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l :=
    estimatedScorePositiveVarianceStudentizationInput_of_projection_le_drift_pos_limit
      pate_scaledStatistic pate_oracle pate_projectionReduction
      pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
      pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
      hpate_projectionLimit_le_oracle hpate_driftLimit_pos
      hpate_inverse_meas
  let pattStudentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l :=
    estimatedScorePositiveVarianceStudentizationInput_of_projection_le_drift_pos_limit
      patt_scaledStatistic patt_oracle patt_projectionReduction
      patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
      patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
      hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
      hpatt_inverse_meas
  simpa [pateStudentizationInput, pattStudentizationInput] using
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score_local_experiment_core
      known pateEstimated pattEstimated pateStudentizationInput
      pattStudentizationInput pate_coverage_input patt_coverage_input
      hpate_known_to_estimated hpatt_known_to_estimated
      hpate_estimated_score_to_scaled_tendsto
      hpatt_estimated_score_to_scaled_tendsto hpate_design hpate_bounded
      hpate_array_lln hpate_finite hpate_envelope hpate_simplex
      hpate_linear hpate_matrix hpatt_design hpatt_bounded
      hpatt_array_lln hpatt_finite hpatt_envelope hpatt_simplex
      hpatt_linear hpatt_matrix hpate_decomp hpate_denominator
      hpate_heterogeneity hpate_residual hpatt_decomp hpatt_denominator
      hpatt_heterogeneity hpatt_residual hpate_first hpate_score
      hpate_core hpatt_first hpatt_score hpatt_core

/--
Paired absolute finite score-cell estimated-score Wald coverage directly from
fixed-law strict projection slack, with the PATE/PATT local-experiment
derivative, equicontinuity, and Godambe obligations packaged as one compact core
per estimand.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit_local_experiment_core
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
    (hpate_estimated_score_to_scaled_tendsto :
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
    (hpatt_estimated_score_to_scaled_tendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
          known pateEstimated pattEstimated hpate_known_to_estimated
          hpatt_known_to_estimated)
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_limit pate_oracleLimit pate_projectionLimit hpate_oracle
        hpate_projection hpate_projectionLimit_lt_oracle hpate_inverse_meas
        hpate_estimated_score_to_scaled_tendsto patt_scaledStatistic
        patt_oracle patt_projectionReduction patt_limit patt_oracleLimit
        patt_projectionLimit hpatt_oracle hpatt_projection
        hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
        hpatt_estimated_score_to_scaled_tendsto pate_coverage_input
        patt_coverage_input) := by
  let finiteBridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell
        PATTCell :=
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
      known pateEstimated pattEstimated hpate_known_to_estimated
      hpatt_known_to_estimated
  simpa [finiteBridge,
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit
      finiteBridge pate_scaledStatistic pate_oracle pate_projectionReduction
      pate_limit pate_oracleLimit pate_projectionLimit hpate_oracle
      hpate_projection hpate_projectionLimit_lt_oracle hpate_inverse_meas
      hpate_estimated_score_to_scaled_tendsto patt_scaledStatistic patt_oracle
      patt_projectionReduction patt_limit patt_oracleLimit patt_projectionLimit
      hpatt_oracle hpatt_projection hpatt_projectionLimit_lt_oracle
      hpatt_inverse_meas hpatt_estimated_score_to_scaled_tendsto
      pate_coverage_input patt_coverage_input hpate_design hpate_bounded
      hpate_array_lln hpate_finite hpate_envelope hpate_simplex hpate_linear
      hpate_matrix hpatt_design hpatt_bounded hpatt_array_lln hpatt_finite
      hpatt_envelope hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      ⟨hpate_score, hpate_core.matching_functional_local_derivative,
        hpate_core.local_stochastic_equicontinuity⟩
      hpate_core.godambe_variance_identity hpatt_first
      ⟨hpatt_score, hpatt_core.matching_functional_local_derivative,
        hpatt_core.local_stochastic_equicontinuity⟩
      hpatt_core.godambe_variance_identity

/--
Paired two-sided finite score-cell estimated-score Wald coverage directly from
fixed-law strict projection slack, with the PATE/PATT local-experiment
derivative, equicontinuity, and Godambe obligations packaged as one compact core
per estimand.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit_local_experiment_core
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
    (hpate_estimated_score_to_scaled_tendsto :
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
    (hpatt_estimated_score_to_scaled_tendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
          known pateEstimated pattEstimated hpate_known_to_estimated
          hpatt_known_to_estimated)
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_limit pate_oracleLimit pate_projectionLimit hpate_oracle
        hpate_projection hpate_projectionLimit_lt_oracle hpate_inverse_meas
        hpate_estimated_score_to_scaled_tendsto patt_scaledStatistic
        patt_oracle patt_projectionReduction patt_limit patt_oracleLimit
        patt_projectionLimit hpatt_oracle hpatt_projection
        hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
        hpatt_estimated_score_to_scaled_tendsto pate_coverage_input
        patt_coverage_input) := by
  let finiteBridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell
        PATTCell :=
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
      known pateEstimated pattEstimated hpate_known_to_estimated
      hpatt_known_to_estimated
  simpa [finiteBridge,
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit
      finiteBridge pate_scaledStatistic pate_oracle pate_projectionReduction
      pate_limit pate_oracleLimit pate_projectionLimit hpate_oracle
      hpate_projection hpate_projectionLimit_lt_oracle hpate_inverse_meas
      hpate_estimated_score_to_scaled_tendsto patt_scaledStatistic patt_oracle
      patt_projectionReduction patt_limit patt_oracleLimit patt_projectionLimit
      hpatt_oracle hpatt_projection hpatt_projectionLimit_lt_oracle
      hpatt_inverse_meas hpatt_estimated_score_to_scaled_tendsto
      pate_coverage_input patt_coverage_input hpate_design hpate_bounded
      hpate_array_lln hpate_finite hpate_envelope hpate_simplex hpate_linear
      hpate_matrix hpatt_design hpatt_bounded hpatt_array_lln hpatt_finite
      hpatt_envelope hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      ⟨hpate_score, hpate_core.matching_functional_local_derivative,
        hpate_core.local_stochastic_equicontinuity⟩
      hpate_core.godambe_variance_identity hpatt_first
      ⟨hpatt_score, hpatt_core.matching_functional_local_derivative,
        hpatt_core.local_stochastic_equicontinuity⟩
      hpatt_core.godambe_variance_identity

/--
Paired two-sided finite score-cell estimated-score Wald coverage directly from
absolute variance-calibration inputs, strict projection slack, and nonnegative
target drift, with the PATE/PATT local-experiment derivative, equicontinuity,
and Godambe obligations packaged as one compact core per estimand.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_lt_limit_local_experiment_core
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
    (hpate_estimated_score_to_scaled_tendsto :
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
    (hpatt_estimated_score_to_scaled_tendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
          known pateEstimated pattEstimated hpate_known_to_estimated
          hpatt_known_to_estimated)
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
        pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
        hpate_inverse_meas hpate_estimated_score_to_scaled_tendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
        hpatt_inverse_meas hpatt_estimated_score_to_scaled_tendsto
        pate_coverage_input patt_coverage_input) := by
  let finiteBridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell
        PATTCell :=
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
      known pateEstimated pattEstimated hpate_known_to_estimated
      hpatt_known_to_estimated
  simpa [finiteBridge,
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_lt_limit
      finiteBridge pate_scaledStatistic pate_oracle pate_projectionReduction
      pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
      pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
      hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
      hpate_inverse_meas hpate_estimated_score_to_scaled_tendsto
      patt_scaledStatistic patt_oracle patt_projectionReduction
      patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
      patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
      hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
      hpatt_inverse_meas hpatt_estimated_score_to_scaled_tendsto
      pate_coverage_input patt_coverage_input hpate_design hpate_bounded
      hpate_array_lln hpate_finite hpate_envelope hpate_simplex hpate_linear
      hpate_matrix hpatt_design hpatt_bounded hpatt_array_lln hpatt_finite
      hpatt_envelope hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      ⟨hpate_score, hpate_core.matching_functional_local_derivative,
        hpate_core.local_stochastic_equicontinuity⟩
      hpate_core.godambe_variance_identity hpatt_first
      ⟨hpatt_score, hpatt_core.matching_functional_local_derivative,
        hpatt_core.local_stochastic_equicontinuity⟩
      hpatt_core.godambe_variance_identity

/--
Paired absolute finite score-cell estimated-score Wald coverage directly from
two-sided variance-calibration inputs, strict projection slack, and nonnegative
target drift, with the PATE/PATT local-experiment derivative, equicontinuity,
and Godambe obligations packaged as one compact core per estimand.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_lt_limit_local_experiment_core
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
    (hpate_estimated_score_to_scaled_tendsto :
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
    (hpatt_estimated_score_to_scaled_tendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
          known pateEstimated pattEstimated hpate_known_to_estimated
          hpatt_known_to_estimated)
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
        pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
        hpate_inverse_meas hpate_estimated_score_to_scaled_tendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
        hpatt_inverse_meas hpatt_estimated_score_to_scaled_tendsto
        pate_coverage_input patt_coverage_input) := by
  let finiteBridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell
        PATTCell :=
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
      known pateEstimated pattEstimated hpate_known_to_estimated
      hpatt_known_to_estimated
  simpa [finiteBridge,
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_lt_limit
      finiteBridge pate_scaledStatistic pate_oracle pate_projectionReduction
      pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
      pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
      hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
      hpate_inverse_meas hpate_estimated_score_to_scaled_tendsto
      patt_scaledStatistic patt_oracle patt_projectionReduction
      patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
      patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
      hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
      hpatt_inverse_meas hpatt_estimated_score_to_scaled_tendsto
      pate_coverage_input patt_coverage_input hpate_design hpate_bounded
      hpate_array_lln hpate_finite hpate_envelope hpate_simplex hpate_linear
      hpate_matrix hpatt_design hpatt_bounded hpatt_array_lln hpatt_finite
      hpatt_envelope hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      ⟨hpate_score, hpate_core.matching_functional_local_derivative,
        hpate_core.local_stochastic_equicontinuity⟩
      hpate_core.godambe_variance_identity hpatt_first
      ⟨hpatt_score, hpatt_core.matching_functional_local_derivative,
        hpatt_core.local_stochastic_equicontinuity⟩
      hpatt_core.godambe_variance_identity

/--
Paired two-sided finite score-cell estimated-score Wald coverage directly from
absolute variance-calibration inputs, weak projection slack and positive
target drift, with the PATE/PATT local-experiment derivative, equicontinuity,
and Godambe obligations packaged as one compact core per estimand.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_le_drift_pos_limit_local_experiment_core
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
    (hpate_estimated_score_to_scaled_tendsto :
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
    (hpatt_estimated_score_to_scaled_tendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_le_drift_pos_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
          known pateEstimated pattEstimated hpate_known_to_estimated
          hpatt_known_to_estimated)
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
        pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_le_oracle hpate_driftLimit_pos
        hpate_inverse_meas hpate_estimated_score_to_scaled_tendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
        hpatt_inverse_meas hpatt_estimated_score_to_scaled_tendsto
        pate_coverage_input patt_coverage_input) := by
  let finiteBridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell
        PATTCell :=
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
      known pateEstimated pattEstimated hpate_known_to_estimated
      hpatt_known_to_estimated
  simpa [finiteBridge,
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_le_drift_pos_limit
      finiteBridge pate_scaledStatistic pate_oracle pate_projectionReduction
      pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
      pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
      hpate_projectionLimit_le_oracle hpate_driftLimit_pos
      hpate_inverse_meas hpate_estimated_score_to_scaled_tendsto
      patt_scaledStatistic patt_oracle patt_projectionReduction
      patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
      patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
      hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
      hpatt_inverse_meas hpatt_estimated_score_to_scaled_tendsto
      pate_coverage_input patt_coverage_input hpate_design hpate_bounded
      hpate_array_lln hpate_finite hpate_envelope hpate_simplex hpate_linear
      hpate_matrix hpatt_design hpatt_bounded hpatt_array_lln hpatt_finite
      hpatt_envelope hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      ⟨hpate_score, hpate_core.matching_functional_local_derivative,
        hpate_core.local_stochastic_equicontinuity⟩
      hpate_core.godambe_variance_identity hpatt_first
      ⟨hpatt_score, hpatt_core.matching_functional_local_derivative,
        hpatt_core.local_stochastic_equicontinuity⟩
      hpatt_core.godambe_variance_identity

/--
Paired absolute finite score-cell estimated-score Wald coverage directly from
two-sided variance-calibration inputs, weak projection slack and positive
target drift, with the PATE/PATT local-experiment derivative, equicontinuity,
and Godambe obligations packaged as one compact core per estimand.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_le_drift_pos_limit_local_experiment_core
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
    (hpate_estimated_score_to_scaled_tendsto :
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
    (hpatt_estimated_score_to_scaled_tendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_le_drift_pos_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
          known pateEstimated pattEstimated hpate_known_to_estimated
          hpatt_known_to_estimated)
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
        pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_le_oracle hpate_driftLimit_pos
        hpate_inverse_meas hpate_estimated_score_to_scaled_tendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
        hpatt_inverse_meas hpatt_estimated_score_to_scaled_tendsto
        pate_coverage_input patt_coverage_input) := by
  let finiteBridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell
        PATTCell :=
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
      known pateEstimated pattEstimated hpate_known_to_estimated
      hpatt_known_to_estimated
  simpa [finiteBridge,
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_le_drift_pos_limit
      finiteBridge pate_scaledStatistic pate_oracle pate_projectionReduction
      pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
      pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
      hpate_projectionLimit_le_oracle hpate_driftLimit_pos
      hpate_inverse_meas hpate_estimated_score_to_scaled_tendsto
      patt_scaledStatistic patt_oracle patt_projectionReduction
      patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
      patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
      hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
      hpatt_inverse_meas hpatt_estimated_score_to_scaled_tendsto
      pate_coverage_input patt_coverage_input hpate_design hpate_bounded
      hpate_array_lln hpate_finite hpate_envelope hpate_simplex hpate_linear
      hpate_matrix hpatt_design hpatt_bounded hpatt_array_lln hpatt_finite
      hpatt_envelope hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      ⟨hpate_score, hpate_core.matching_functional_local_derivative,
        hpate_core.local_stochastic_equicontinuity⟩
      hpate_core.godambe_variance_identity hpatt_first
      ⟨hpatt_score, hpatt_core.matching_functional_local_derivative,
        hpatt_core.local_stochastic_equicontinuity⟩
      hpatt_core.godambe_variance_identity

/--
Paired two-sided finite score-cell estimated-score Wald coverage directly from
absolute variance-calibration inputs and fixed-law strict projection slack, with
the PATE/PATT local-experiment derivative, equicontinuity, and Godambe
obligations packaged as one compact core per estimand.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_fixedLaw_projection_lt_limit_local_experiment_core
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
    (hpate_estimated_score_to_scaled_tendsto :
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
    (hpatt_estimated_score_to_scaled_tendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_fixedLaw_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
          known pateEstimated pattEstimated hpate_known_to_estimated
          hpatt_known_to_estimated)
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_limit pate_oracleLimit pate_projectionLimit hpate_oracle
        hpate_projection hpate_projectionLimit_lt_oracle hpate_inverse_meas
        hpate_estimated_score_to_scaled_tendsto patt_scaledStatistic
        patt_oracle patt_projectionReduction patt_limit patt_oracleLimit
        patt_projectionLimit hpatt_oracle hpatt_projection
        hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
        hpatt_estimated_score_to_scaled_tendsto pate_coverage_input
        patt_coverage_input) := by
  let finiteBridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell
        PATTCell :=
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
      known pateEstimated pattEstimated hpate_known_to_estimated
      hpatt_known_to_estimated
  simpa [finiteBridge,
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_fixedLaw_projection_lt_limit
      finiteBridge pate_scaledStatistic pate_oracle pate_projectionReduction
      pate_limit pate_oracleLimit pate_projectionLimit hpate_oracle
      hpate_projection hpate_projectionLimit_lt_oracle hpate_inverse_meas
      hpate_estimated_score_to_scaled_tendsto patt_scaledStatistic patt_oracle
      patt_projectionReduction patt_limit patt_oracleLimit patt_projectionLimit
      hpatt_oracle hpatt_projection hpatt_projectionLimit_lt_oracle
      hpatt_inverse_meas hpatt_estimated_score_to_scaled_tendsto
      pate_coverage_input patt_coverage_input hpate_design hpate_bounded
      hpate_array_lln hpate_finite hpate_envelope hpate_simplex hpate_linear
      hpate_matrix hpatt_design hpatt_bounded hpatt_array_lln hpatt_finite
      hpatt_envelope hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      ⟨hpate_score, hpate_core.matching_functional_local_derivative,
        hpate_core.local_stochastic_equicontinuity⟩
      hpate_core.godambe_variance_identity hpatt_first
      ⟨hpatt_score, hpatt_core.matching_functional_local_derivative,
        hpatt_core.local_stochastic_equicontinuity⟩
      hpatt_core.godambe_variance_identity

/--
Paired absolute finite score-cell estimated-score Wald coverage directly from
two-sided variance-calibration inputs and fixed-law strict projection slack,
with the PATE/PATT local-experiment derivative, equicontinuity, and Godambe
obligations packaged as one compact core per estimand.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_fixedLaw_projection_lt_limit_local_experiment_core
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
    (hpate_estimated_score_to_scaled_tendsto :
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
    (hpatt_estimated_score_to_scaled_tendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_fixedLaw_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
          known pateEstimated pattEstimated hpate_known_to_estimated
          hpatt_known_to_estimated)
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_limit pate_oracleLimit pate_projectionLimit hpate_oracle
        hpate_projection hpate_projectionLimit_lt_oracle hpate_inverse_meas
        hpate_estimated_score_to_scaled_tendsto patt_scaledStatistic
        patt_oracle patt_projectionReduction patt_limit patt_oracleLimit
        patt_projectionLimit hpatt_oracle hpatt_projection
        hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
        hpatt_estimated_score_to_scaled_tendsto pate_coverage_input
        patt_coverage_input) := by
  let finiteBridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell
        PATTCell :=
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
      known pateEstimated pattEstimated hpate_known_to_estimated
      hpatt_known_to_estimated
  simpa [finiteBridge,
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_fixedLaw_projection_lt_limit
      finiteBridge pate_scaledStatistic pate_oracle pate_projectionReduction
      pate_limit pate_oracleLimit pate_projectionLimit hpate_oracle
      hpate_projection hpate_projectionLimit_lt_oracle hpate_inverse_meas
      hpate_estimated_score_to_scaled_tendsto patt_scaledStatistic patt_oracle
      patt_projectionReduction patt_limit patt_oracleLimit patt_projectionLimit
      hpatt_oracle hpatt_projection hpatt_projectionLimit_lt_oracle
      hpatt_inverse_meas hpatt_estimated_score_to_scaled_tendsto
      pate_coverage_input patt_coverage_input hpate_design hpate_bounded
      hpate_array_lln hpate_finite hpate_envelope hpate_simplex hpate_linear
      hpate_matrix hpatt_design hpatt_bounded hpatt_array_lln hpatt_finite
      hpatt_envelope hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      ⟨hpate_score, hpate_core.matching_functional_local_derivative,
        hpate_core.local_stochastic_equicontinuity⟩
      hpate_core.godambe_variance_identity hpatt_first
      ⟨hpatt_score, hpatt_core.matching_functional_local_derivative,
        hpatt_core.local_stochastic_equicontinuity⟩
      hpatt_core.godambe_variance_identity

/--
Paired absolute Wald coverage from fixed-law score-quadratic projection
reductions, with the PATE/PATT local-experiment derivative, equicontinuity,
and Godambe obligations packaged as one compact core per estimand.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_scoreAdjusted_fixedLaw_projection_lt_limit_local_experiment_core
    (known :
      PATEPATTFiniteScoreCellKnownScoreAsymptoticBridge PATECell PATTCell)
    (pateEstimated : EstimatedScoreLocalExperimentInput)
    (pattEstimated : EstimatedScoreLocalExperimentInput)
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
    (hpate_estimated_score_to_scaled_tendsto :
      pateEstimated.estimated_score_asymptotic_normality ->
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
    (hpatt_estimated_score_to_scaled_tendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_scoreAdjusted_fixedLaw_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
          known pateEstimated pattEstimated hpate_known_to_estimated
          hpatt_known_to_estimated)
        pateParameters pattParameters pate_scaledStatistic
        patt_scaledStatistic pate_oracle patt_oracle pateFirstStepLoading
        pattFirstStepLoading pateScoreCovariance pattScoreCovariance
        pate_limit patt_limit pate_oracleLimit pate_projectionLimit
        patt_oracleLimit patt_projectionLimit hpate_oracle
        hpate_projection hpate_projectionLimit_lt_oracle hpate_inverse_meas
        hpate_estimated_score_to_scaled_tendsto hpatt_oracle
        hpatt_projection hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
        hpatt_estimated_score_to_scaled_tendsto pate_coverage_input
        patt_coverage_input) := by
  let finiteBridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell
        PATTCell :=
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
      known pateEstimated pattEstimated hpate_known_to_estimated
      hpatt_known_to_estimated
  let h :
      (let b :=
        patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_scoreAdjusted_fixedLaw_projection_lt_limit
          finiteBridge pateParameters pattParameters pate_scaledStatistic
          patt_scaledStatistic pate_oracle patt_oracle pateFirstStepLoading
          pattFirstStepLoading pateScoreCovariance pattScoreCovariance
          pate_limit patt_limit pate_oracleLimit pate_projectionLimit
          patt_oracleLimit patt_projectionLimit hpate_oracle
          hpate_projection hpate_projectionLimit_lt_oracle hpate_inverse_meas
          hpate_estimated_score_to_scaled_tendsto hpatt_oracle
          hpatt_projection hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
          hpatt_estimated_score_to_scaled_tendsto pate_coverage_input
          patt_coverage_input;
        PATEPATTFiniteScoreCellEstimatedScorePositiveVarianceWaldAssumptions
          b.studentized_bridge) := by
    dsimp
    refine
      { hpate_design := by
          simpa [finiteBridge,
            patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
            estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
            hpate_design
        hpate_bounded := by
          simpa [finiteBridge,
            patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
            estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
            hpate_bounded
        hpate_array_lln := by
          simpa [finiteBridge,
            patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
            estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
            hpate_array_lln
        hpate_finite := by
          simpa [finiteBridge,
            patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
            estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
            hpate_finite
        hpate_envelope := by
          simpa [finiteBridge,
            patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
            estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
            hpate_envelope
        hpate_simplex := by
          simpa [finiteBridge,
            patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
            estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
            hpate_simplex
        hpate_linear := by
          simpa [finiteBridge,
            patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
            estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
            hpate_linear
        hpate_matrix := by
          simpa [finiteBridge,
            patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
            estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
            hpate_matrix
        hpatt_design := by
          simpa [finiteBridge,
            patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
            estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
            hpatt_design
        hpatt_bounded := by
          simpa [finiteBridge,
            patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
            estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
            hpatt_bounded
        hpatt_array_lln := by
          simpa [finiteBridge,
            patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
            estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
            hpatt_array_lln
        hpatt_finite := by
          simpa [finiteBridge,
            patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
            estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
            hpatt_finite
        hpatt_envelope := by
          simpa [finiteBridge,
            patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
            estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
            hpatt_envelope
        hpatt_simplex := by
          simpa [finiteBridge,
            patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
            estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
            hpatt_simplex
        hpatt_linear := by
          simpa [finiteBridge,
            patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
            estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
            hpatt_linear
        hpatt_matrix := by
          simpa [finiteBridge,
            patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
            estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
            hpatt_matrix
        hpate_decomp := by
          simpa [finiteBridge,
            patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
            estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
            hpate_decomp
        hpate_denominator := by
          simpa [finiteBridge,
            patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
            estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
            hpate_denominator
        hpate_heterogeneity := by
          simpa [finiteBridge,
            patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
            estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
            hpate_heterogeneity
        hpate_residual := by
          simpa [finiteBridge,
            patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
            estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
            hpate_residual
        hpatt_decomp := by
          simpa [finiteBridge,
            patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
            estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
            hpatt_decomp
        hpatt_denominator := by
          simpa [finiteBridge,
            patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
            estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
            hpatt_denominator
        hpatt_heterogeneity := by
          simpa [finiteBridge,
            patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
            estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
            hpatt_heterogeneity
        hpatt_residual := by
          simpa [finiteBridge,
            patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
            estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
            hpatt_residual
        hpate_first := by
          simpa [finiteBridge,
            patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
            estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
            hpate_first
        hpate_local := by
          simpa [finiteBridge,
            patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
            estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
            ⟨hpate_score,
              hpate_core.matching_functional_local_derivative,
              hpate_core.local_stochastic_equicontinuity⟩
        hpate_godambe := by
          simpa [finiteBridge,
            patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
            estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
            hpate_core.godambe_variance_identity
        hpatt_first := by
          simpa [finiteBridge,
            patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
            estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
            hpatt_first
        hpatt_local := by
          simpa [finiteBridge,
            patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
            estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
            ⟨hpatt_score,
              hpatt_core.matching_functional_local_derivative,
              hpatt_core.local_stochastic_equicontinuity⟩
        hpatt_godambe := by
          simpa [finiteBridge,
            patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
            estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
            hpatt_core.godambe_variance_identity }
  simpa [finiteBridge,
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_scoreAdjusted_fixedLaw_projection_lt_limit
      finiteBridge pateParameters pattParameters pate_scaledStatistic
      patt_scaledStatistic pate_oracle patt_oracle pateFirstStepLoading
      pattFirstStepLoading pateScoreCovariance pattScoreCovariance
      pate_limit patt_limit pate_oracleLimit pate_projectionLimit
      patt_oracleLimit patt_projectionLimit hpate_oracle hpate_projection
      hpate_projectionLimit_lt_oracle hpate_inverse_meas
      hpate_estimated_score_to_scaled_tendsto hpatt_oracle
      hpatt_projection hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
      hpatt_estimated_score_to_scaled_tendsto pate_coverage_input
      patt_coverage_input h

/--
Paired two-sided Wald coverage from fixed-law score-quadratic projection
reductions, with the PATE/PATT local-experiment derivative, equicontinuity,
and Godambe obligations packaged as one compact core per estimand.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_scoreAdjusted_fixedLaw_projection_lt_limit_local_experiment_core
    (known :
      PATEPATTFiniteScoreCellKnownScoreAsymptoticBridge PATECell PATTCell)
    (pateEstimated : EstimatedScoreLocalExperimentInput)
    (pattEstimated : EstimatedScoreLocalExperimentInput)
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
    (hpate_estimated_score_to_scaled_tendsto :
      pateEstimated.estimated_score_asymptotic_normality ->
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
    (hpatt_estimated_score_to_scaled_tendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_scoreAdjusted_fixedLaw_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
          known pateEstimated pattEstimated hpate_known_to_estimated
          hpatt_known_to_estimated)
        pateParameters pattParameters pate_scaledStatistic
        patt_scaledStatistic pate_oracle patt_oracle pateFirstStepLoading
        pattFirstStepLoading pateScoreCovariance pattScoreCovariance
        pate_limit patt_limit pate_oracleLimit pate_projectionLimit
        patt_oracleLimit patt_projectionLimit hpate_oracle
        hpate_projection hpate_projectionLimit_lt_oracle hpate_inverse_meas
        hpate_estimated_score_to_scaled_tendsto hpatt_oracle
        hpatt_projection hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
        hpatt_estimated_score_to_scaled_tendsto pate_coverage_input
        patt_coverage_input) := by
  let finiteBridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell
        PATTCell :=
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
      known pateEstimated pattEstimated hpate_known_to_estimated
      hpatt_known_to_estimated
  let pateStudentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l :=
    fixedLawEstimatedScorePositiveVarianceStudentizationInput_of_scoreAdjusted_projection_lt_limit
      pateParameters pate_scaledStatistic pate_oracle pateFirstStepLoading
      pateScoreCovariance pate_limit pate_oracleLimit pate_projectionLimit
      hpate_oracle hpate_projection hpate_projectionLimit_lt_oracle
      hpate_inverse_meas
  let pattStudentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l :=
    fixedLawEstimatedScorePositiveVarianceStudentizationInput_of_scoreAdjusted_projection_lt_limit
      pattParameters patt_scaledStatistic patt_oracle pattFirstStepLoading
      pattScoreCovariance patt_limit patt_oracleLimit patt_projectionLimit
      hpatt_oracle hpatt_projection hpatt_projectionLimit_lt_oracle
      hpatt_inverse_meas
  simpa [PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion,
    finiteBridge, pateStudentizationInput, pattStudentizationInput,
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    estimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_scoreAdjusted_fixedLaw_projection_lt_limit,
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_studentized,
    patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_fixedLaw_projection_lt_limit,
    fixedLawEstimatedScorePositiveVarianceStudentizationInput_of_scoreAdjusted_projection_lt_limit] using
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score_local_experiment_core
      known pateEstimated pattEstimated pateStudentizationInput
      pattStudentizationInput pate_coverage_input patt_coverage_input
      hpate_known_to_estimated hpatt_known_to_estimated
      (by
        intro hnormal
        simpa [pateStudentizationInput] using
          hpate_estimated_score_to_scaled_tendsto hnormal)
      (by
        intro hnormal
        simpa [pattStudentizationInput] using
          hpatt_estimated_score_to_scaled_tendsto hnormal)
      hpate_design hpate_bounded hpate_array_lln hpate_finite
      hpate_envelope hpate_simplex hpate_linear hpate_matrix hpatt_design
      hpatt_bounded hpatt_array_lln hpatt_finite hpatt_envelope
      hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      hpate_score hpate_core hpatt_first hpatt_score hpatt_core

/--
Paired two-sided Wald coverage from absolute calibration inputs and fixed-law
score-quadratic projection reductions, with the PATE/PATT local-experiment
derivative, equicontinuity, and Godambe obligations packaged as one compact core
per estimand.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_scoreAdjusted_fixedLaw_projection_lt_limit_local_experiment_core
    (known :
      PATEPATTFiniteScoreCellKnownScoreAsymptoticBridge PATECell PATTCell)
    (pateEstimated : EstimatedScoreLocalExperimentInput)
    (pattEstimated : EstimatedScoreLocalExperimentInput)
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
    (hpate_estimated_score_to_scaled_tendsto :
      pateEstimated.estimated_score_asymptotic_normality ->
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
    (hpatt_estimated_score_to_scaled_tendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_scoreAdjusted_fixedLaw_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
          known pateEstimated pattEstimated hpate_known_to_estimated
          hpatt_known_to_estimated)
        pateParameters pattParameters pate_scaledStatistic
        patt_scaledStatistic pate_oracle patt_oracle pateFirstStepLoading
        pattFirstStepLoading pateScoreCovariance pattScoreCovariance
        pate_limit patt_limit pate_oracleLimit pate_projectionLimit
        patt_oracleLimit patt_projectionLimit hpate_oracle
        hpate_projection hpate_projectionLimit_lt_oracle hpate_inverse_meas
        hpate_estimated_score_to_scaled_tendsto hpatt_oracle
        hpatt_projection hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
        hpatt_estimated_score_to_scaled_tendsto pate_coverage_input
        patt_coverage_input) := by
  let finiteBridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell
        PATTCell :=
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
      known pateEstimated pattEstimated hpate_known_to_estimated
      hpatt_known_to_estimated
  let pateStudentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l :=
    fixedLawEstimatedScorePositiveVarianceStudentizationInput_of_scoreAdjusted_projection_lt_limit
      pateParameters pate_scaledStatistic pate_oracle pateFirstStepLoading
      pateScoreCovariance pate_limit pate_oracleLimit pate_projectionLimit
      hpate_oracle hpate_projection hpate_projectionLimit_lt_oracle
      hpate_inverse_meas
  let pattStudentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l :=
    fixedLawEstimatedScorePositiveVarianceStudentizationInput_of_scoreAdjusted_projection_lt_limit
      pattParameters patt_scaledStatistic patt_oracle pattFirstStepLoading
      pattScoreCovariance patt_limit patt_oracleLimit patt_projectionLimit
      hpatt_oracle hpatt_projection hpatt_projectionLimit_lt_oracle
      hpatt_inverse_meas
  simpa [PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion,
    finiteBridge, pateStudentizationInput, pattStudentizationInput,
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    estimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_scoreAdjusted_fixedLaw_projection_lt_limit,
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute,
    patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_scoreAdjusted_fixedLaw_projection_lt_limit,
    patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_studentized,
    patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_fixedLaw_projection_lt_limit,
    fixedLawEstimatedScorePositiveVarianceStudentizationInput_of_scoreAdjusted_projection_lt_limit] using
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score_local_experiment_core
      known pateEstimated pattEstimated pateStudentizationInput
      pattStudentizationInput
      (twoSidedWaldCoverageVarianceInput_of_absolute pate_coverage_input)
      (twoSidedWaldCoverageVarianceInput_of_absolute patt_coverage_input)
      hpate_known_to_estimated hpatt_known_to_estimated
      (by
        intro hnormal
        simpa [pateStudentizationInput] using
          hpate_estimated_score_to_scaled_tendsto hnormal)
      (by
        intro hnormal
        simpa [pattStudentizationInput] using
          hpatt_estimated_score_to_scaled_tendsto hnormal)
      hpate_design hpate_bounded hpate_array_lln hpate_finite
      hpate_envelope hpate_simplex hpate_linear hpate_matrix hpatt_design
      hpatt_bounded hpatt_array_lln hpatt_finite hpatt_envelope
      hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      hpate_score hpate_core hpatt_first hpatt_score hpatt_core

/--
Paired absolute Wald coverage from two-sided calibration inputs and fixed-law
score-quadratic projection reductions, with the PATE/PATT local-experiment
derivative, equicontinuity, and Godambe obligations packaged as one compact
core per estimand.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_scoreAdjusted_fixedLaw_projection_lt_limit_local_experiment_core
    (known :
      PATEPATTFiniteScoreCellKnownScoreAsymptoticBridge PATECell PATTCell)
    (pateEstimated : EstimatedScoreLocalExperimentInput)
    (pattEstimated : EstimatedScoreLocalExperimentInput)
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
    (hpate_estimated_score_to_scaled_tendsto :
      pateEstimated.estimated_score_asymptotic_normality ->
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
    (hpatt_estimated_score_to_scaled_tendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_scoreAdjusted_fixedLaw_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
          known pateEstimated pattEstimated hpate_known_to_estimated
          hpatt_known_to_estimated)
        pateParameters pattParameters pate_scaledStatistic
        patt_scaledStatistic pate_oracle patt_oracle pateFirstStepLoading
        pattFirstStepLoading pateScoreCovariance pattScoreCovariance
        pate_limit patt_limit pate_oracleLimit pate_projectionLimit
        patt_oracleLimit patt_projectionLimit hpate_oracle
        hpate_projection hpate_projectionLimit_lt_oracle hpate_inverse_meas
        hpate_estimated_score_to_scaled_tendsto hpatt_oracle
        hpatt_projection hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
        hpatt_estimated_score_to_scaled_tendsto pate_coverage_input
        patt_coverage_input) := by
  let finiteBridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell
        PATTCell :=
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
      known pateEstimated pattEstimated hpate_known_to_estimated
      hpatt_known_to_estimated
  simpa [finiteBridge,
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    estimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_scoreAdjusted_fixedLaw_projection_lt_limit,
    patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_fixedLaw_projection_lt_limit] using
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_fixedLaw_projection_lt_limit_local_experiment_core
      known pateEstimated pattEstimated pate_scaledStatistic pate_oracle
      (fun index sample =>
        scoreQuadraticForm pateParameters pateFirstStepLoading
          (pateScoreCovariance index sample))
      pate_limit pate_oracleLimit pate_projectionLimit hpate_oracle
      hpate_projection hpate_projectionLimit_lt_oracle hpate_inverse_meas
      hpate_estimated_score_to_scaled_tendsto patt_scaledStatistic patt_oracle
      (fun index sample =>
        scoreQuadraticForm pattParameters pattFirstStepLoading
          (pattScoreCovariance index sample))
      patt_limit patt_oracleLimit patt_projectionLimit hpatt_oracle
      hpatt_projection hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
      hpatt_estimated_score_to_scaled_tendsto pate_coverage_input
      patt_coverage_input hpate_known_to_estimated hpatt_known_to_estimated
      hpate_design hpate_bounded hpate_array_lln hpate_finite
      hpate_envelope hpate_simplex hpate_linear hpate_matrix hpatt_design
      hpatt_bounded hpatt_array_lln hpatt_finite hpatt_envelope
      hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      hpate_score hpate_core hpatt_first hpatt_score hpatt_core

/--
Paired absolute Wald coverage from changing-law score-quadratic projection and
target-drift reductions, with the PATE/PATT local-experiment derivative,
equicontinuity, and Godambe obligations packaged as one compact core per
estimand.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_scoreAdjusted_projection_lt_limit_local_experiment_core
    (known :
      PATEPATTFiniteScoreCellKnownScoreAsymptoticBridge PATECell PATTCell)
    (pateEstimated : EstimatedScoreLocalExperimentInput)
    (pattEstimated : EstimatedScoreLocalExperimentInput)
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
    (hpate_estimated_score_to_scaled_tendsto :
      pateEstimated.estimated_score_asymptotic_normality ->
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
    (hpatt_estimated_score_to_scaled_tendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_scoreAdjusted_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
          known pateEstimated pattEstimated hpate_known_to_estimated
          hpatt_known_to_estimated)
        pateParameters pattParameters pate_scaledStatistic
        patt_scaledStatistic pate_oracle patt_oracle pateFirstStepLoading
        pateTargetDriftLoading pattFirstStepLoading pattTargetDriftLoading
        pateScoreCovariance pattScoreCovariance pate_limit patt_limit
        pate_oracleLimit pate_projectionLimit pate_targetDriftLimit
        patt_oracleLimit patt_projectionLimit patt_targetDriftLimit
        hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
        hpate_inverse_meas hpate_estimated_score_to_scaled_tendsto
        hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
        hpatt_inverse_meas hpatt_estimated_score_to_scaled_tendsto
        pate_coverage_input patt_coverage_input) := by
  let finiteBridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell
        PATTCell :=
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
      known pateEstimated pattEstimated hpate_known_to_estimated
      hpatt_known_to_estimated
  simpa [PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion,
    finiteBridge,
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    estimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_scoreAdjusted_projection_lt_limit,
    patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_studentized,
    patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_projection_lt_limit,
    estimatedScorePositiveVarianceStudentizationInput_of_scoreAdjusted_projection_lt_limit] using
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit_local_experiment_core
      known pateEstimated pattEstimated pate_scaledStatistic pate_oracle
      (fun index sample =>
        scoreQuadraticForm pateParameters pateFirstStepLoading
          (pateScoreCovariance index sample))
      (fun index sample =>
        scoreQuadraticForm pateParameters pateTargetDriftLoading
          (pateScoreCovariance index sample))
      pate_limit pate_oracleLimit pate_projectionLimit
      pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
      hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
      hpate_inverse_meas hpate_estimated_score_to_scaled_tendsto
      patt_scaledStatistic patt_oracle
      (fun index sample =>
        scoreQuadraticForm pattParameters pattFirstStepLoading
          (pattScoreCovariance index sample))
      (fun index sample =>
        scoreQuadraticForm pattParameters pattTargetDriftLoading
          (pattScoreCovariance index sample))
      patt_limit patt_oracleLimit patt_projectionLimit
      patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
      hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
      hpatt_inverse_meas hpatt_estimated_score_to_scaled_tendsto
      pate_coverage_input patt_coverage_input hpate_known_to_estimated
      hpatt_known_to_estimated hpate_design hpate_bounded hpate_array_lln
      hpate_finite hpate_envelope hpate_simplex hpate_linear hpate_matrix
      hpatt_design hpatt_bounded hpatt_array_lln hpatt_finite
        hpatt_envelope hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
        hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
        hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
        hpate_score hpate_core hpatt_first hpatt_score hpatt_core

/--
Paired two-sided Wald coverage from changing-law score-quadratic projection and
target-drift reductions, with the PATE/PATT local-experiment derivative,
equicontinuity, and Godambe obligations packaged as one compact core per
estimand.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_scoreAdjusted_projection_lt_limit_local_experiment_core
    (known :
      PATEPATTFiniteScoreCellKnownScoreAsymptoticBridge PATECell PATTCell)
    (pateEstimated : EstimatedScoreLocalExperimentInput)
    (pattEstimated : EstimatedScoreLocalExperimentInput)
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
    (hpate_estimated_score_to_scaled_tendsto :
      pateEstimated.estimated_score_asymptotic_normality ->
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
    (hpatt_estimated_score_to_scaled_tendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_scoreAdjusted_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
          known pateEstimated pattEstimated hpate_known_to_estimated
          hpatt_known_to_estimated)
        pateParameters pattParameters pate_scaledStatistic
        patt_scaledStatistic pate_oracle patt_oracle pateFirstStepLoading
        pateTargetDriftLoading pattFirstStepLoading pattTargetDriftLoading
        pateScoreCovariance pattScoreCovariance pate_limit patt_limit
        pate_oracleLimit pate_projectionLimit pate_targetDriftLimit
        patt_oracleLimit patt_projectionLimit patt_targetDriftLimit
        hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
        hpate_inverse_meas hpate_estimated_score_to_scaled_tendsto
        hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
        hpatt_inverse_meas hpatt_estimated_score_to_scaled_tendsto
        pate_coverage_input patt_coverage_input) := by
  let finiteBridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell
        PATTCell :=
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
      known pateEstimated pattEstimated hpate_known_to_estimated
      hpatt_known_to_estimated
  simpa [PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion,
    finiteBridge,
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    estimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_scoreAdjusted_projection_lt_limit,
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_studentized,
    patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_projection_lt_limit,
    estimatedScorePositiveVarianceStudentizationInput_of_scoreAdjusted_projection_lt_limit] using
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit_local_experiment_core
      known pateEstimated pattEstimated pate_scaledStatistic pate_oracle
      (fun index sample =>
        scoreQuadraticForm pateParameters pateFirstStepLoading
          (pateScoreCovariance index sample))
      (fun index sample =>
        scoreQuadraticForm pateParameters pateTargetDriftLoading
          (pateScoreCovariance index sample))
      pate_limit pate_oracleLimit pate_projectionLimit
      pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
      hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
      hpate_inverse_meas hpate_estimated_score_to_scaled_tendsto
      patt_scaledStatistic patt_oracle
      (fun index sample =>
        scoreQuadraticForm pattParameters pattFirstStepLoading
          (pattScoreCovariance index sample))
      (fun index sample =>
        scoreQuadraticForm pattParameters pattTargetDriftLoading
          (pattScoreCovariance index sample))
      patt_limit patt_oracleLimit patt_projectionLimit
      patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
      hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
      hpatt_inverse_meas hpatt_estimated_score_to_scaled_tendsto
      pate_coverage_input patt_coverage_input hpate_known_to_estimated
      hpatt_known_to_estimated hpate_design hpate_bounded hpate_array_lln
      hpate_finite hpate_envelope hpate_simplex hpate_linear hpate_matrix
      hpatt_design hpatt_bounded hpatt_array_lln hpatt_finite
      hpatt_envelope hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      hpate_score hpate_core hpatt_first hpatt_score hpatt_core

/--
Paired absolute Wald coverage from changing-law score-quadratic projection and
target-drift reductions under weak projection slack and positive target drift,
with the PATE/PATT local-experiment derivative, equicontinuity, and Godambe
obligations packaged as one compact core per estimand.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_scoreAdjusted_projection_le_drift_pos_limit_local_experiment_core
    (known :
      PATEPATTFiniteScoreCellKnownScoreAsymptoticBridge PATECell PATTCell)
    (pateEstimated : EstimatedScoreLocalExperimentInput)
    (pattEstimated : EstimatedScoreLocalExperimentInput)
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
    (hpate_estimated_score_to_scaled_tendsto :
      pateEstimated.estimated_score_asymptotic_normality ->
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
    (hpatt_estimated_score_to_scaled_tendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_scoreAdjusted_projection_le_drift_pos_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
          known pateEstimated pattEstimated hpate_known_to_estimated
          hpatt_known_to_estimated)
        pateParameters pattParameters pate_scaledStatistic
        patt_scaledStatistic pate_oracle patt_oracle pateFirstStepLoading
        pateTargetDriftLoading pattFirstStepLoading pattTargetDriftLoading
        pateScoreCovariance pattScoreCovariance pate_limit patt_limit
        pate_oracleLimit pate_projectionLimit pate_targetDriftLimit
        patt_oracleLimit patt_projectionLimit patt_targetDriftLimit
        hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_le_oracle hpate_driftLimit_pos
        hpate_inverse_meas hpate_estimated_score_to_scaled_tendsto
        hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
        hpatt_inverse_meas hpatt_estimated_score_to_scaled_tendsto
        pate_coverage_input patt_coverage_input) := by
  let finiteBridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell
        PATTCell :=
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
      known pateEstimated pattEstimated hpate_known_to_estimated
      hpatt_known_to_estimated
  simpa [PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion,
    finiteBridge,
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    estimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_scoreAdjusted_projection_le_drift_pos_limit,
    patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_studentized,
    patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_projection_le_drift_pos_limit,
    estimatedScorePositiveVarianceStudentizationInput_of_scoreAdjusted_projection_le_drift_pos_limit] using
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit_local_experiment_core
      known pateEstimated pattEstimated pate_scaledStatistic pate_oracle
      (fun index sample =>
        scoreQuadraticForm pateParameters pateFirstStepLoading
          (pateScoreCovariance index sample))
      (fun index sample =>
        scoreQuadraticForm pateParameters pateTargetDriftLoading
          (pateScoreCovariance index sample))
      pate_limit pate_oracleLimit pate_projectionLimit
      pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
      hpate_projectionLimit_le_oracle hpate_driftLimit_pos
      hpate_inverse_meas hpate_estimated_score_to_scaled_tendsto
      patt_scaledStatistic patt_oracle
      (fun index sample =>
        scoreQuadraticForm pattParameters pattFirstStepLoading
          (pattScoreCovariance index sample))
      (fun index sample =>
        scoreQuadraticForm pattParameters pattTargetDriftLoading
          (pattScoreCovariance index sample))
      patt_limit patt_oracleLimit patt_projectionLimit
      patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
      hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
      hpatt_inverse_meas hpatt_estimated_score_to_scaled_tendsto
      pate_coverage_input patt_coverage_input hpate_known_to_estimated
      hpatt_known_to_estimated hpate_design hpate_bounded hpate_array_lln
      hpate_finite hpate_envelope hpate_simplex hpate_linear hpate_matrix
      hpatt_design hpatt_bounded hpatt_array_lln hpatt_finite
      hpatt_envelope hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      hpate_score hpate_core hpatt_first hpatt_score hpatt_core

/--
Paired two-sided Wald coverage from changing-law score-quadratic projection and
target-drift reductions under weak projection slack and positive target drift,
with the PATE/PATT local-experiment derivative, equicontinuity, and Godambe
obligations packaged as one compact core per estimand.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_scoreAdjusted_projection_le_drift_pos_limit_local_experiment_core
    (known :
      PATEPATTFiniteScoreCellKnownScoreAsymptoticBridge PATECell PATTCell)
    (pateEstimated : EstimatedScoreLocalExperimentInput)
    (pattEstimated : EstimatedScoreLocalExperimentInput)
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
    (hpate_estimated_score_to_scaled_tendsto :
      pateEstimated.estimated_score_asymptotic_normality ->
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
    (hpatt_estimated_score_to_scaled_tendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_scoreAdjusted_projection_le_drift_pos_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
          known pateEstimated pattEstimated hpate_known_to_estimated
          hpatt_known_to_estimated)
        pateParameters pattParameters pate_scaledStatistic
        patt_scaledStatistic pate_oracle patt_oracle pateFirstStepLoading
        pateTargetDriftLoading pattFirstStepLoading pattTargetDriftLoading
        pateScoreCovariance pattScoreCovariance pate_limit patt_limit
        pate_oracleLimit pate_projectionLimit pate_targetDriftLimit
        patt_oracleLimit patt_projectionLimit patt_targetDriftLimit
        hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_le_oracle hpate_driftLimit_pos
        hpate_inverse_meas hpate_estimated_score_to_scaled_tendsto
        hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
        hpatt_inverse_meas hpatt_estimated_score_to_scaled_tendsto
        pate_coverage_input patt_coverage_input) := by
  let finiteBridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell
        PATTCell :=
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
      known pateEstimated pattEstimated hpate_known_to_estimated
      hpatt_known_to_estimated
  simpa [PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion,
    finiteBridge,
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    estimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_scoreAdjusted_projection_le_drift_pos_limit,
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_studentized,
    patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_projection_le_drift_pos_limit,
    estimatedScorePositiveVarianceStudentizationInput_of_scoreAdjusted_projection_le_drift_pos_limit] using
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit_local_experiment_core
      known pateEstimated pattEstimated pate_scaledStatistic pate_oracle
      (fun index sample =>
        scoreQuadraticForm pateParameters pateFirstStepLoading
          (pateScoreCovariance index sample))
      (fun index sample =>
        scoreQuadraticForm pateParameters pateTargetDriftLoading
          (pateScoreCovariance index sample))
      pate_limit pate_oracleLimit pate_projectionLimit
      pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
      hpate_projectionLimit_le_oracle hpate_driftLimit_pos
      hpate_inverse_meas hpate_estimated_score_to_scaled_tendsto
      patt_scaledStatistic patt_oracle
      (fun index sample =>
        scoreQuadraticForm pattParameters pattFirstStepLoading
          (pattScoreCovariance index sample))
      (fun index sample =>
        scoreQuadraticForm pattParameters pattTargetDriftLoading
          (pattScoreCovariance index sample))
      patt_limit patt_oracleLimit patt_projectionLimit
      patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
      hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
      hpatt_inverse_meas hpatt_estimated_score_to_scaled_tendsto
      pate_coverage_input patt_coverage_input hpate_known_to_estimated
      hpatt_known_to_estimated hpate_design hpate_bounded hpate_array_lln
      hpate_finite hpate_envelope hpate_simplex hpate_linear hpate_matrix
      hpatt_design hpatt_bounded hpatt_array_lln hpatt_finite
      hpatt_envelope hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      hpate_score hpate_core hpatt_first hpatt_score hpatt_core

/--
Paired two-sided Wald coverage from absolute calibration inputs and
changing-law score-quadratic projection and target-drift reductions under weak
projection slack and positive target drift, with the PATE/PATT local-experiment
derivative, equicontinuity, and Godambe obligations packaged as one compact
core per estimand.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_scoreAdjusted_projection_le_drift_pos_limit_local_experiment_core
    (known :
      PATEPATTFiniteScoreCellKnownScoreAsymptoticBridge PATECell PATTCell)
    (pateEstimated : EstimatedScoreLocalExperimentInput)
    (pattEstimated : EstimatedScoreLocalExperimentInput)
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
    (hpate_estimated_score_to_scaled_tendsto :
      pateEstimated.estimated_score_asymptotic_normality ->
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
    (hpatt_estimated_score_to_scaled_tendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_scoreAdjusted_projection_le_drift_pos_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
          known pateEstimated pattEstimated hpate_known_to_estimated
          hpatt_known_to_estimated)
        pateParameters pattParameters pate_scaledStatistic
        patt_scaledStatistic pate_oracle patt_oracle pateFirstStepLoading
        pateTargetDriftLoading pattFirstStepLoading pattTargetDriftLoading
        pateScoreCovariance pattScoreCovariance pate_limit patt_limit
        pate_oracleLimit pate_projectionLimit pate_targetDriftLimit
        patt_oracleLimit patt_projectionLimit patt_targetDriftLimit
        hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_le_oracle hpate_driftLimit_pos
        hpate_inverse_meas hpate_estimated_score_to_scaled_tendsto
        hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
        hpatt_inverse_meas hpatt_estimated_score_to_scaled_tendsto
        pate_coverage_input patt_coverage_input) := by
  let finiteBridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell
        PATTCell :=
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
      known pateEstimated pattEstimated hpate_known_to_estimated
      hpatt_known_to_estimated
  simpa [PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion,
    finiteBridge,
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    estimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_scoreAdjusted_projection_le_drift_pos_limit,
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_le_drift_pos_limit,
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute,
    patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_scoreAdjusted_projection_le_drift_pos_limit,
    patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_studentized,
    patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_projection_le_drift_pos_limit,
    estimatedScorePositiveVarianceStudentizationInput_of_scoreAdjusted_projection_le_drift_pos_limit] using
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_le_drift_pos_limit_local_experiment_core
      known pateEstimated pattEstimated pate_scaledStatistic pate_oracle
      (fun index sample =>
        scoreQuadraticForm pateParameters pateFirstStepLoading
          (pateScoreCovariance index sample))
      (fun index sample =>
        scoreQuadraticForm pateParameters pateTargetDriftLoading
          (pateScoreCovariance index sample))
      pate_limit pate_oracleLimit pate_projectionLimit
      pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
      hpate_projectionLimit_le_oracle hpate_driftLimit_pos
      hpate_inverse_meas hpate_estimated_score_to_scaled_tendsto
      patt_scaledStatistic patt_oracle
      (fun index sample =>
        scoreQuadraticForm pattParameters pattFirstStepLoading
          (pattScoreCovariance index sample))
      (fun index sample =>
        scoreQuadraticForm pattParameters pattTargetDriftLoading
          (pattScoreCovariance index sample))
      patt_limit patt_oracleLimit patt_projectionLimit
      patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
      hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
      hpatt_inverse_meas hpatt_estimated_score_to_scaled_tendsto
      pate_coverage_input patt_coverage_input hpate_known_to_estimated
      hpatt_known_to_estimated hpate_design hpate_bounded hpate_array_lln
      hpate_finite hpate_envelope hpate_simplex hpate_linear hpate_matrix
      hpatt_design hpatt_bounded hpatt_array_lln hpatt_finite
      hpatt_envelope hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      hpate_score hpate_core hpatt_first hpatt_score hpatt_core

/--
Paired absolute Wald coverage from two-sided calibration inputs and
changing-law score-quadratic projection and target-drift reductions under weak
projection slack and positive target drift, with the PATE/PATT local-experiment
derivative, equicontinuity, and Godambe obligations packaged as one compact
core per estimand.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_scoreAdjusted_projection_le_drift_pos_limit_local_experiment_core
    (known :
      PATEPATTFiniteScoreCellKnownScoreAsymptoticBridge PATECell PATTCell)
    (pateEstimated : EstimatedScoreLocalExperimentInput)
    (pattEstimated : EstimatedScoreLocalExperimentInput)
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
    (hpate_estimated_score_to_scaled_tendsto :
      pateEstimated.estimated_score_asymptotic_normality ->
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
    (hpatt_estimated_score_to_scaled_tendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_scoreAdjusted_projection_le_drift_pos_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
          known pateEstimated pattEstimated hpate_known_to_estimated
          hpatt_known_to_estimated)
        pateParameters pattParameters pate_scaledStatistic
        patt_scaledStatistic pate_oracle patt_oracle pateFirstStepLoading
        pateTargetDriftLoading pattFirstStepLoading pattTargetDriftLoading
        pateScoreCovariance pattScoreCovariance pate_limit patt_limit
        pate_oracleLimit pate_projectionLimit pate_targetDriftLimit
        patt_oracleLimit patt_projectionLimit patt_targetDriftLimit
        hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_le_oracle hpate_driftLimit_pos
        hpate_inverse_meas hpate_estimated_score_to_scaled_tendsto
        hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
        hpatt_inverse_meas hpatt_estimated_score_to_scaled_tendsto
        pate_coverage_input patt_coverage_input) := by
  let finiteBridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell
        PATTCell :=
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
      known pateEstimated pattEstimated hpate_known_to_estimated
      hpatt_known_to_estimated
  simpa [PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion,
    finiteBridge,
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    estimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_scoreAdjusted_projection_le_drift_pos_limit,
    patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_le_drift_pos_limit,
    patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided,
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_scoreAdjusted_projection_le_drift_pos_limit,
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_studentized,
    patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_projection_le_drift_pos_limit,
    estimatedScorePositiveVarianceStudentizationInput_of_scoreAdjusted_projection_le_drift_pos_limit] using
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_le_drift_pos_limit_local_experiment_core
      known pateEstimated pattEstimated pate_scaledStatistic pate_oracle
      (fun index sample =>
        scoreQuadraticForm pateParameters pateFirstStepLoading
          (pateScoreCovariance index sample))
      (fun index sample =>
        scoreQuadraticForm pateParameters pateTargetDriftLoading
          (pateScoreCovariance index sample))
      pate_limit pate_oracleLimit pate_projectionLimit
      pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
      hpate_projectionLimit_le_oracle hpate_driftLimit_pos
      hpate_inverse_meas hpate_estimated_score_to_scaled_tendsto
      patt_scaledStatistic patt_oracle
      (fun index sample =>
        scoreQuadraticForm pattParameters pattFirstStepLoading
          (pattScoreCovariance index sample))
      (fun index sample =>
        scoreQuadraticForm pattParameters pattTargetDriftLoading
          (pattScoreCovariance index sample))
      patt_limit patt_oracleLimit patt_projectionLimit
      patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
      hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
      hpatt_inverse_meas hpatt_estimated_score_to_scaled_tendsto
      pate_coverage_input patt_coverage_input hpate_known_to_estimated
      hpatt_known_to_estimated hpate_design hpate_bounded hpate_array_lln
      hpate_finite hpate_envelope hpate_simplex hpate_linear hpate_matrix
      hpatt_design hpatt_bounded hpatt_array_lln hpatt_finite
      hpatt_envelope hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      hpate_score hpate_core hpatt_first hpatt_score hpatt_core

/--
Paired two-sided Wald coverage from absolute calibration inputs and
changing-law score-quadratic projection and target-drift reductions, with the
PATE/PATT local-experiment derivative, equicontinuity, and Godambe obligations
packaged as one compact core per estimand.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_scoreAdjusted_projection_lt_limit_local_experiment_core
    (known :
      PATEPATTFiniteScoreCellKnownScoreAsymptoticBridge PATECell PATTCell)
    (pateEstimated : EstimatedScoreLocalExperimentInput)
    (pattEstimated : EstimatedScoreLocalExperimentInput)
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
    (hpate_estimated_score_to_scaled_tendsto :
      pateEstimated.estimated_score_asymptotic_normality ->
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
    (hpatt_estimated_score_to_scaled_tendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_scoreAdjusted_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
          known pateEstimated pattEstimated hpate_known_to_estimated
          hpatt_known_to_estimated)
        pateParameters pattParameters pate_scaledStatistic
        patt_scaledStatistic pate_oracle patt_oracle pateFirstStepLoading
        pateTargetDriftLoading pattFirstStepLoading pattTargetDriftLoading
        pateScoreCovariance pattScoreCovariance pate_limit patt_limit
        pate_oracleLimit pate_projectionLimit pate_targetDriftLimit
        patt_oracleLimit patt_projectionLimit patt_targetDriftLimit
        hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
        hpate_inverse_meas hpate_estimated_score_to_scaled_tendsto
        hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
        hpatt_inverse_meas hpatt_estimated_score_to_scaled_tendsto
        pate_coverage_input patt_coverage_input) := by
  let finiteBridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell
        PATTCell :=
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
      known pateEstimated pattEstimated hpate_known_to_estimated
      hpatt_known_to_estimated
  simpa [PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion,
    finiteBridge,
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    estimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_scoreAdjusted_projection_lt_limit,
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute,
    patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_scoreAdjusted_projection_lt_limit,
    patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_studentized,
    patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_projection_lt_limit,
    estimatedScorePositiveVarianceStudentizationInput_of_scoreAdjusted_projection_lt_limit] using
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_lt_limit_local_experiment_core
      known pateEstimated pattEstimated pate_scaledStatistic pate_oracle
      (fun index sample =>
        scoreQuadraticForm pateParameters pateFirstStepLoading
          (pateScoreCovariance index sample))
      (fun index sample =>
        scoreQuadraticForm pateParameters pateTargetDriftLoading
          (pateScoreCovariance index sample))
      pate_limit pate_oracleLimit pate_projectionLimit
      pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
      hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
      hpate_inverse_meas hpate_estimated_score_to_scaled_tendsto
      patt_scaledStatistic patt_oracle
      (fun index sample =>
        scoreQuadraticForm pattParameters pattFirstStepLoading
          (pattScoreCovariance index sample))
      (fun index sample =>
        scoreQuadraticForm pattParameters pattTargetDriftLoading
          (pattScoreCovariance index sample))
      patt_limit patt_oracleLimit patt_projectionLimit
      patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
      hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
      hpatt_inverse_meas hpatt_estimated_score_to_scaled_tendsto
      pate_coverage_input patt_coverage_input hpate_known_to_estimated
      hpatt_known_to_estimated hpate_design hpate_bounded hpate_array_lln
      hpate_finite hpate_envelope hpate_simplex hpate_linear hpate_matrix
      hpatt_design hpatt_bounded hpatt_array_lln hpatt_finite
      hpatt_envelope hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      hpate_score hpate_core hpatt_first hpatt_score hpatt_core

/--
Paired absolute Wald coverage from two-sided calibration inputs and
changing-law score-quadratic projection and target-drift reductions, with the
PATE/PATT local-experiment derivative, equicontinuity, and Godambe obligations
packaged as one compact core per estimand.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_scoreAdjusted_projection_lt_limit_local_experiment_core
    (known :
      PATEPATTFiniteScoreCellKnownScoreAsymptoticBridge PATECell PATTCell)
    (pateEstimated : EstimatedScoreLocalExperimentInput)
    (pattEstimated : EstimatedScoreLocalExperimentInput)
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
    (hpate_estimated_score_to_scaled_tendsto :
      pateEstimated.estimated_score_asymptotic_normality ->
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
    (hpatt_estimated_score_to_scaled_tendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_scoreAdjusted_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
          known pateEstimated pattEstimated hpate_known_to_estimated
          hpatt_known_to_estimated)
        pateParameters pattParameters pate_scaledStatistic
        patt_scaledStatistic pate_oracle patt_oracle pateFirstStepLoading
        pateTargetDriftLoading pattFirstStepLoading pattTargetDriftLoading
        pateScoreCovariance pattScoreCovariance pate_limit patt_limit
        pate_oracleLimit pate_projectionLimit pate_targetDriftLimit
        patt_oracleLimit patt_projectionLimit patt_targetDriftLimit
        hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
        hpate_inverse_meas hpate_estimated_score_to_scaled_tendsto
        hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
        hpatt_inverse_meas hpatt_estimated_score_to_scaled_tendsto
        pate_coverage_input patt_coverage_input) := by
  let finiteBridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell
        PATTCell :=
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
      known pateEstimated pattEstimated hpate_known_to_estimated
      hpatt_known_to_estimated
  simpa [PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion,
    finiteBridge,
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    estimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_scoreAdjusted_projection_lt_limit,
    patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_lt_limit,
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_scoreAdjusted_projection_lt_limit,
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_studentized,
    patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_projection_lt_limit,
    estimatedScorePositiveVarianceStudentizationInput_of_scoreAdjusted_projection_lt_limit] using
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_lt_limit_local_experiment_core
      known pateEstimated pattEstimated pate_scaledStatistic pate_oracle
      (fun index sample =>
        scoreQuadraticForm pateParameters pateFirstStepLoading
          (pateScoreCovariance index sample))
      (fun index sample =>
        scoreQuadraticForm pateParameters pateTargetDriftLoading
          (pateScoreCovariance index sample))
      pate_limit pate_oracleLimit pate_projectionLimit
      pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
      hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
      hpate_inverse_meas hpate_estimated_score_to_scaled_tendsto
      patt_scaledStatistic patt_oracle
      (fun index sample =>
        scoreQuadraticForm pattParameters pattFirstStepLoading
          (pattScoreCovariance index sample))
      (fun index sample =>
        scoreQuadraticForm pattParameters pattTargetDriftLoading
          (pattScoreCovariance index sample))
      patt_limit patt_oracleLimit patt_projectionLimit
      patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
      hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
      hpatt_inverse_meas hpatt_estimated_score_to_scaled_tendsto
      pate_coverage_input patt_coverage_input hpate_known_to_estimated
      hpatt_known_to_estimated hpate_design hpate_bounded hpate_array_lln
      hpate_finite hpate_envelope hpate_simplex hpate_linear hpate_matrix
      hpatt_design hpatt_bounded hpatt_array_lln hpatt_finite
      hpatt_envelope hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      hpate_score hpate_core hpatt_first hpatt_score hpatt_core


end WDSM
end Matching
end StatInference
