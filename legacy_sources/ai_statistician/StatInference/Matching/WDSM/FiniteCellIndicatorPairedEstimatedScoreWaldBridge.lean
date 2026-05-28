import StatInference.Matching.WDSM.FiniteCellIndicatorPairedEstimatedScoreStudentizedBridge
import StatInference.Matching.WDSM.WaldInferenceBridge

/-!
# Paired finite score-cell approximation to estimated-score WDSM Wald inference

This module composes the paired finite score-cell estimated-score studentized
bridge with the existing Wald coverage bridge for PATE and PATT.  Critical-value
calibration remains explicit through separate PATE/PATT absolute or two-sided
coverage inputs.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open Filter
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

/-- Paired estimated-score Wald bridge for absolute critical regions. -/
structure PATEPATTFiniteScoreCellEstimatedScoreAbsoluteWaldBridge
    (PATECell PATTCell Index Sample LimitSample : Type*)
    [DecidableEq PATECell] [DecidableEq PATTCell]
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : MeasureTheory.Measure Sample)
    (limitLaw : MeasureTheory.Measure LimitSample) (l : Filter Index)
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw] [l.IsCountablyGenerated] where
  studentized_bridge :
    PATEPATTFiniteScoreCellEstimatedScoreStudentizedBridge PATECell PATTCell
      Index Sample LimitSample sampleLaw limitLaw l
  pate_coverage_input : AbsoluteWaldCoverageInput Index Sample l
  patt_coverage_input : AbsoluteWaldCoverageInput Index Sample l

theorem
    pate_patt_absoluteWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score
    (b :
      PATEPATTFiniteScoreCellEstimatedScoreAbsoluteWaldBridge PATECell PATTCell
        Index Sample LimitSample sampleLaw limitLaw l)
    (hpate_design :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hpate_bounded :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (hpate_array_lln :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hpate_finite :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (hpate_envelope :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hpate_simplex :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hpate_linear :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpate_matrix :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpatt_design :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hpatt_bounded :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (hpatt_array_lln :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hpatt_finite :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (hpatt_envelope :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hpatt_simplex :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hpatt_linear :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpatt_matrix :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpate_decomp :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.pate_known_score_bridge.aggregate_hajek_decomposition)
    (hpate_denominator :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.pate_known_score_bridge.denominator_stabilization)
    (hpate_heterogeneity :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.pate_known_score_bridge.heterogeneity_clt)
    (hpate_residual :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.pate_known_score_bridge.residual_clt)
    (hpatt_decomp :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.patt_known_score_bridge.aggregate_hajek_decomposition)
    (hpatt_denominator :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.patt_known_score_bridge.denominator_stabilization)
    (hpatt_heterogeneity :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.patt_known_score_bridge.heterogeneity_clt)
    (hpatt_residual :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.patt_known_score_bridge.residual_clt)
    (hpate_first :
      b.studentized_bridge.finite_estimated_bridge.pate_estimated_score_bridge.first_step_asymptotic_linearization)
    (hpate_local :
      b.studentized_bridge.finite_estimated_bridge.pate_estimated_score_bridge.matching_functional_local_expansion)
    (hpate_godambe :
      b.studentized_bridge.finite_estimated_bridge.pate_estimated_score_bridge.godambe_variance_identity)
    (hpatt_first :
      b.studentized_bridge.finite_estimated_bridge.patt_estimated_score_bridge.first_step_asymptotic_linearization)
    (hpatt_local :
      b.studentized_bridge.finite_estimated_bridge.patt_estimated_score_bridge.matching_functional_local_expansion)
    (hpatt_godambe :
      b.studentized_bridge.finite_estimated_bridge.patt_estimated_score_bridge.godambe_variance_identity) :
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
                (b.pate_coverage_input.standardError index sample)
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
                (b.patt_coverage_input.standardError index sample)
                (b.patt_coverage_input.scale index)))
        l (nhds b.patt_coverage_input.coverageLimit) := by
  have hstudentized_pair :=
    pate_patt_studentized_tendstoInDistribution_of_paired_finite_score_cell_estimated_score
      b.studentized_bridge hpate_design hpate_bounded hpate_array_lln
      hpate_finite hpate_envelope hpate_simplex hpate_linear hpate_matrix
      hpatt_design hpatt_bounded hpatt_array_lln hpatt_finite
      hpatt_envelope hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      hpate_local hpate_godambe hpatt_first hpatt_local hpatt_godambe
  rcases hstudentized_pair with
    ⟨hpate_unscaled, hpate_scaled, hpate_known, hpate_estimated,
      hpate_studentized, hpatt_unscaled, hpatt_scaled, hpatt_known,
      hpatt_estimated, hpatt_studentized⟩
  have hpate_coverage :=
    absoluteWaldCoverage_tendsto_of_input b.pate_coverage_input
  have hpatt_coverage :=
    absoluteWaldCoverage_tendsto_of_input b.patt_coverage_input
  exact ⟨hpate_unscaled, hpate_scaled, hpate_known, hpate_estimated,
    hpate_studentized, hpate_coverage, hpatt_unscaled, hpatt_scaled,
    hpatt_known, hpatt_estimated, hpatt_studentized, hpatt_coverage⟩

/-- Paired estimated-score Wald bridge for two-sided critical regions. -/
structure PATEPATTFiniteScoreCellEstimatedScoreTwoSidedWaldBridge
    (PATECell PATTCell Index Sample LimitSample : Type*)
    [DecidableEq PATECell] [DecidableEq PATTCell]
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : MeasureTheory.Measure Sample)
    (limitLaw : MeasureTheory.Measure LimitSample) (l : Filter Index)
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw] [l.IsCountablyGenerated] where
  studentized_bridge :
    PATEPATTFiniteScoreCellEstimatedScoreStudentizedBridge PATECell PATTCell
      Index Sample LimitSample sampleLaw limitLaw l
  pate_coverage_input : TwoSidedWaldCoverageInput Index Sample l
  patt_coverage_input : TwoSidedWaldCoverageInput Index Sample l

theorem
    pate_patt_twoSidedWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score
    (b :
      PATEPATTFiniteScoreCellEstimatedScoreTwoSidedWaldBridge PATECell PATTCell
        Index Sample LimitSample sampleLaw limitLaw l)
    (hpate_design :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hpate_bounded :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (hpate_array_lln :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hpate_finite :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (hpate_envelope :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hpate_simplex :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hpate_linear :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpate_matrix :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.pate_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpatt_design :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hpatt_bounded :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (hpatt_array_lln :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hpatt_finite :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (hpatt_envelope :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hpatt_simplex :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hpatt_linear :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpatt_matrix :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.patt_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpate_decomp :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.pate_known_score_bridge.aggregate_hajek_decomposition)
    (hpate_denominator :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.pate_known_score_bridge.denominator_stabilization)
    (hpate_heterogeneity :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.pate_known_score_bridge.heterogeneity_clt)
    (hpate_residual :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.pate_known_score_bridge.residual_clt)
    (hpatt_decomp :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.patt_known_score_bridge.aggregate_hajek_decomposition)
    (hpatt_denominator :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.patt_known_score_bridge.denominator_stabilization)
    (hpatt_heterogeneity :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.patt_known_score_bridge.heterogeneity_clt)
    (hpatt_residual :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.patt_known_score_bridge.residual_clt)
    (hpate_first :
      b.studentized_bridge.finite_estimated_bridge.pate_estimated_score_bridge.first_step_asymptotic_linearization)
    (hpate_local :
      b.studentized_bridge.finite_estimated_bridge.pate_estimated_score_bridge.matching_functional_local_expansion)
    (hpate_godambe :
      b.studentized_bridge.finite_estimated_bridge.pate_estimated_score_bridge.godambe_variance_identity)
    (hpatt_first :
      b.studentized_bridge.finite_estimated_bridge.patt_estimated_score_bridge.first_step_asymptotic_linearization)
    (hpatt_local :
      b.studentized_bridge.finite_estimated_bridge.patt_estimated_score_bridge.matching_functional_local_expansion)
    (hpatt_godambe :
      b.studentized_bridge.finite_estimated_bridge.patt_estimated_score_bridge.godambe_variance_identity) :
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
                (b.pate_coverage_input.standardError index sample)
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
                (b.patt_coverage_input.standardError index sample)
                (b.patt_coverage_input.scale index)))
        l (nhds b.patt_coverage_input.coverageLimit) := by
  have hstudentized_pair :=
    pate_patt_studentized_tendstoInDistribution_of_paired_finite_score_cell_estimated_score
      b.studentized_bridge hpate_design hpate_bounded hpate_array_lln
      hpate_finite hpate_envelope hpate_simplex hpate_linear hpate_matrix
      hpatt_design hpatt_bounded hpatt_array_lln hpatt_finite
      hpatt_envelope hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      hpate_local hpate_godambe hpatt_first hpatt_local hpatt_godambe
  rcases hstudentized_pair with
    ⟨hpate_unscaled, hpate_scaled, hpate_known, hpate_estimated,
      hpate_studentized, hpatt_unscaled, hpatt_scaled, hpatt_known,
      hpatt_estimated, hpatt_studentized⟩
  have hpate_coverage :=
    twoSidedWaldCoverage_tendsto_of_input b.pate_coverage_input
  have hpatt_coverage :=
    twoSidedWaldCoverage_tendsto_of_input b.patt_coverage_input
  exact ⟨hpate_unscaled, hpate_scaled, hpate_known, hpate_estimated,
    hpate_studentized, hpate_coverage, hpatt_unscaled, hpatt_scaled,
    hpatt_known, hpatt_estimated, hpatt_studentized, hpatt_coverage⟩

/--
Paired finite score-cell estimated-score absolute Wald coverage from explicit
local experiments, with the PATE/PATT derivative, equicontinuity, and Godambe
obligations packaged into one compact core per estimand.
-/
theorem
    pate_patt_absoluteWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score_local_experiment_core
    (known :
      PATEPATTFiniteScoreCellKnownScoreAsymptoticBridge PATECell PATTCell)
    (pateEstimated : EstimatedScoreLocalExperimentInput)
    (pattEstimated : EstimatedScoreLocalExperimentInput)
    (pateStudentizationInput :
      EstimatedScoreStudentizationInput Index Sample LimitSample sampleLaw
        limitLaw l)
    (pattStudentizationInput :
      EstimatedScoreStudentizationInput Index Sample LimitSample sampleLaw
        limitLaw l)
    (pateCoverageInput : AbsoluteWaldCoverageInput Index Sample l)
    (pattCoverageInput : AbsoluteWaldCoverageInput Index Sample l)
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
      Tendsto
        (fun index =>
          eventProbabilityReal (pateCoverageInput.sampleLawSeq index)
            (fun sample =>
              waldCovers (pateCoverageInput.estimator index sample)
                (pateCoverageInput.target index)
                (pateCoverageInput.criticalValue index)
                (pateCoverageInput.standardError index sample)
                (pateCoverageInput.scale index)))
        l (nhds pateCoverageInput.coverageLimit) ∧
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
          eventProbabilityReal (pattCoverageInput.sampleLawSeq index)
            (fun sample =>
              waldCovers (pattCoverageInput.estimator index sample)
                (pattCoverageInput.target index)
                (pattCoverageInput.criticalValue index)
                (pattCoverageInput.standardError index sample)
                (pattCoverageInput.scale index)))
        l (nhds pattCoverageInput.coverageLimit) := by
  let finiteBridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell
        PATTCell :=
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
      known pateEstimated pattEstimated hpate_known_to_estimated
      hpatt_known_to_estimated
  let studentizedBridge :
      PATEPATTFiniteScoreCellEstimatedScoreStudentizedBridge PATECell
        PATTCell Index Sample LimitSample sampleLaw limitLaw l := {
    finite_estimated_bridge := finiteBridge
    pate_studentization_input := pateStudentizationInput
    patt_studentization_input := pattStudentizationInput
    pate_estimated_score_to_scaled_tendsto := hpate_scaled
    patt_estimated_score_to_scaled_tendsto := hpatt_scaled }
  let b :
      PATEPATTFiniteScoreCellEstimatedScoreAbsoluteWaldBridge PATECell
        PATTCell Index Sample LimitSample sampleLaw limitLaw l := {
    studentized_bridge := studentizedBridge
    pate_coverage_input := pateCoverageInput
    patt_coverage_input := pattCoverageInput }
  simpa [b, studentizedBridge, finiteBridge,
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
    pate_patt_absoluteWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score
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

/--
Paired finite score-cell estimated-score two-sided Wald coverage from explicit
local experiments, with the PATE/PATT derivative, equicontinuity, and Godambe
obligations packaged into one compact core per estimand.
-/
theorem
    pate_patt_twoSidedWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score_local_experiment_core
    (known :
      PATEPATTFiniteScoreCellKnownScoreAsymptoticBridge PATECell PATTCell)
    (pateEstimated : EstimatedScoreLocalExperimentInput)
    (pattEstimated : EstimatedScoreLocalExperimentInput)
    (pateStudentizationInput :
      EstimatedScoreStudentizationInput Index Sample LimitSample sampleLaw
        limitLaw l)
    (pattStudentizationInput :
      EstimatedScoreStudentizationInput Index Sample LimitSample sampleLaw
        limitLaw l)
    (pateCoverageInput : TwoSidedWaldCoverageInput Index Sample l)
    (pattCoverageInput : TwoSidedWaldCoverageInput Index Sample l)
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
      Tendsto
        (fun index =>
          eventProbabilityReal (pateCoverageInput.sampleLawSeq index)
            (fun sample =>
              waldCovers (pateCoverageInput.estimator index sample)
                (pateCoverageInput.target index)
                (pateCoverageInput.criticalValue index)
                (pateCoverageInput.standardError index sample)
                (pateCoverageInput.scale index)))
        l (nhds pateCoverageInput.coverageLimit) ∧
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
          eventProbabilityReal (pattCoverageInput.sampleLawSeq index)
            (fun sample =>
              waldCovers (pattCoverageInput.estimator index sample)
                (pattCoverageInput.target index)
                (pattCoverageInput.criticalValue index)
                (pattCoverageInput.standardError index sample)
                (pattCoverageInput.scale index)))
        l (nhds pattCoverageInput.coverageLimit) := by
  let finiteBridge :
      PATEPATTFiniteScoreCellEstimatedScoreAsymptoticBridge PATECell
        PATTCell :=
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
      known pateEstimated pattEstimated hpate_known_to_estimated
      hpatt_known_to_estimated
  let studentizedBridge :
      PATEPATTFiniteScoreCellEstimatedScoreStudentizedBridge PATECell
        PATTCell Index Sample LimitSample sampleLaw limitLaw l := {
    finite_estimated_bridge := finiteBridge
    pate_studentization_input := pateStudentizationInput
    patt_studentization_input := pattStudentizationInput
    pate_estimated_score_to_scaled_tendsto := hpate_scaled
    patt_estimated_score_to_scaled_tendsto := hpatt_scaled }
  let b :
      PATEPATTFiniteScoreCellEstimatedScoreTwoSidedWaldBridge PATECell
        PATTCell Index Sample LimitSample sampleLaw limitLaw l := {
    studentized_bridge := studentizedBridge
    pate_coverage_input := pateCoverageInput
    patt_coverage_input := pattCoverageInput }
  simpa [b, studentizedBridge, finiteBridge,
    patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
    pate_patt_twoSidedWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score
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
