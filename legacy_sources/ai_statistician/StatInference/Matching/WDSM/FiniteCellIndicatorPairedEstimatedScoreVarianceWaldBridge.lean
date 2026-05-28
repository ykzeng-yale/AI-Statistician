import StatInference.Matching.WDSM.FiniteCellIndicatorPairedEstimatedScoreWaldBridge
import StatInference.Matching.WDSM.WaldStandardErrorPositivity

/-!
# Paired finite score-cell estimated-score Wald inference from variance estimates

This module composes the paired finite score-cell estimated-score Wald bridge
with the variance-to-standard-error positivity bridge.  The final paired Wald
inputs can be stated directly in terms of positive PATE/PATT variance estimates.
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

/-- Paired estimated-score Wald bridge with absolute regions and variance estimates. -/
structure PATEPATTFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridge
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
  pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l
  patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l

/-- Convert a paired absolute variance-Wald bridge to the standard-error Wald bridge. -/
noncomputable def patePATTFiniteScoreCellEstimatedScoreAbsoluteWaldBridge_of_variance
    (b :
      PATEPATTFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridge
        PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsoluteWaldBridge PATECell PATTCell
      Index Sample LimitSample sampleLaw limitLaw l :=
  { studentized_bridge := b.studentized_bridge
    pate_coverage_input :=
      absoluteWaldCoverageInput_of_variance b.pate_coverage_input
    patt_coverage_input :=
      absoluteWaldCoverageInput_of_variance b.patt_coverage_input }

theorem
    pate_patt_absoluteVarianceWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score
    (b :
      PATEPATTFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridge
        PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l)
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
  let converted :=
    patePATTFiniteScoreCellEstimatedScoreAbsoluteWaldBridge_of_variance b
  simpa [converted] using
    pate_patt_absoluteWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score
      converted hpate_design hpate_bounded hpate_array_lln hpate_finite
      hpate_envelope hpate_simplex hpate_linear hpate_matrix hpatt_design
      hpatt_bounded hpatt_array_lln hpatt_finite hpatt_envelope
      hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      hpate_local hpate_godambe hpatt_first hpatt_local hpatt_godambe

/-- Paired estimated-score Wald bridge with two-sided regions and variance estimates. -/
structure PATEPATTFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldBridge
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
  pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l
  patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l

/-- Convert a paired two-sided variance-Wald bridge to the standard-error Wald bridge. -/
noncomputable def patePATTFiniteScoreCellEstimatedScoreTwoSidedWaldBridge_of_variance
    (b :
      PATEPATTFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldBridge
        PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedWaldBridge PATECell PATTCell
      Index Sample LimitSample sampleLaw limitLaw l :=
  { studentized_bridge := b.studentized_bridge
    pate_coverage_input :=
      twoSidedWaldCoverageInput_of_variance b.pate_coverage_input
    patt_coverage_input :=
      twoSidedWaldCoverageInput_of_variance b.patt_coverage_input }

theorem
    pate_patt_twoSidedVarianceWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score
    (b :
      PATEPATTFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldBridge
        PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l)
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
  let converted :=
    patePATTFiniteScoreCellEstimatedScoreTwoSidedWaldBridge_of_variance b
  simpa [converted] using
    pate_patt_twoSidedWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score
      converted hpate_design hpate_bounded hpate_array_lln hpate_finite
      hpate_envelope hpate_simplex hpate_linear hpate_matrix hpatt_design
      hpatt_bounded hpatt_array_lln hpatt_finite hpatt_envelope
      hpatt_simplex hpatt_linear hpatt_matrix hpate_decomp
      hpate_denominator hpate_heterogeneity hpate_residual hpatt_decomp
      hpatt_denominator hpatt_heterogeneity hpatt_residual hpate_first
      hpate_local hpate_godambe hpatt_first hpatt_local hpatt_godambe

/--
Paired finite score-cell estimated-score absolute variance-Wald coverage from
explicit local experiments, with one compact local-experiment core per
estimand and variance-based Wald calibration kept explicit.
-/
theorem
    pate_patt_absoluteVarianceWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score_local_experiment_core
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
    (pateCoverageInput : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (pattCoverageInput : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
                (standardError
                  (pateCoverageInput.varianceEstimate index sample))
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
                (standardError
                  (pattCoverageInput.varianceEstimate index sample))
                (pattCoverageInput.scale index)))
        l (nhds pattCoverageInput.coverageLimit) := by
  simpa [absoluteWaldCoverageInput_of_variance] using
    pate_patt_absoluteWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score_local_experiment_core
      known pateEstimated pattEstimated pateStudentizationInput
      pattStudentizationInput (absoluteWaldCoverageInput_of_variance
        pateCoverageInput) (absoluteWaldCoverageInput_of_variance
        pattCoverageInput) hpate_known_to_estimated
      hpatt_known_to_estimated hpate_scaled hpatt_scaled hpate_design
      hpate_bounded hpate_array_lln hpate_finite hpate_envelope
      hpate_simplex hpate_linear hpate_matrix hpatt_design hpatt_bounded
      hpatt_array_lln hpatt_finite hpatt_envelope hpatt_simplex
      hpatt_linear hpatt_matrix hpate_decomp hpate_denominator
      hpate_heterogeneity hpate_residual hpatt_decomp hpatt_denominator
      hpatt_heterogeneity hpatt_residual hpate_first hpate_score
      hpate_core hpatt_first hpatt_score hpatt_core

/--
Paired finite score-cell estimated-score two-sided variance-Wald coverage from
explicit local experiments, with one compact local-experiment core per
estimand and variance-based Wald calibration kept explicit.
-/
theorem
    pate_patt_twoSidedVarianceWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score_local_experiment_core
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
    (pateCoverageInput : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (pattCoverageInput : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
                (standardError
                  (pateCoverageInput.varianceEstimate index sample))
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
                (standardError
                  (pattCoverageInput.varianceEstimate index sample))
                (pattCoverageInput.scale index)))
        l (nhds pattCoverageInput.coverageLimit) := by
  simpa [twoSidedWaldCoverageInput_of_variance] using
    pate_patt_twoSidedWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score_local_experiment_core
      known pateEstimated pattEstimated pateStudentizationInput
      pattStudentizationInput (twoSidedWaldCoverageInput_of_variance
        pateCoverageInput) (twoSidedWaldCoverageInput_of_variance
        pattCoverageInput) hpate_known_to_estimated
      hpatt_known_to_estimated hpate_scaled hpatt_scaled hpate_design
      hpate_bounded hpate_array_lln hpate_finite hpate_envelope
      hpate_simplex hpate_linear hpate_matrix hpatt_design hpatt_bounded
      hpatt_array_lln hpatt_finite hpatt_envelope hpatt_simplex
      hpatt_linear hpatt_matrix hpate_decomp hpate_denominator
      hpate_heterogeneity hpate_residual hpatt_decomp hpatt_denominator
      hpatt_heterogeneity hpatt_residual hpate_first hpate_score
      hpate_core hpatt_first hpatt_score hpatt_core

end WDSM
end Matching
end StatInference
