import StatInference.Matching.WDSM.FiniteCellIndicatorEstimatedScorePositiveVarianceStudentizedBridge
import StatInference.Matching.WDSM.WaldStandardErrorPositivity

/-!
# Estimated-score Wald inference from positive limiting variance

This module composes the positive-variance studentization bridge with the
variance-estimate Wald coverage inputs.  It is the final finite score-cell
wrapper needed to state PATE/PATT estimated-score Wald conclusions without a
separate nonzero limiting-standard-error premise.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open Filter
open scoped Topology

variable {Cell Index Sample LimitSample : Type*}
variable [DecidableEq Cell]
variable [MeasurableSpace Sample] [MeasurableSpace LimitSample]
variable {sampleLaw : MeasureTheory.Measure Sample}
variable {limitLaw : MeasureTheory.Measure LimitSample}
variable [MeasureTheory.IsProbabilityMeasure sampleLaw]
variable [MeasureTheory.IsProbabilityMeasure limitLaw]
variable {l : Filter Index}
variable [l.IsCountablyGenerated]

/-! ## PATE -/

/-- PATE positive-variance studentized bridge plus absolute Wald coverage data. -/
structure PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge
    (Cell Index Sample LimitSample : Type*) [DecidableEq Cell]
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : MeasureTheory.Measure Sample)
    (limitLaw : MeasureTheory.Measure LimitSample) (l : Filter Index)
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw] [l.IsCountablyGenerated] where
  studentized_bridge :
    PATEFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l
  coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l

theorem
    pate_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score
    (b :
      PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell
        Index Sample LimitSample sampleLaw limitLaw l)
    (hdesign :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.aggregate_hajek_decomposition)
    (hdenominator :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.denominator_stabilization)
    (hheterogeneity :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.heterogeneity_clt)
    (hresidual :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.residual_clt)
    (hfirst :
      b.studentized_bridge.finite_estimated_bridge.estimated_score_bridge.first_step_asymptotic_linearization)
    (hlocal :
      b.studentized_bridge.finite_estimated_bridge.estimated_score_bridge.matching_functional_local_expansion)
    (hgodambe :
      b.studentized_bridge.finite_estimated_bridge.estimated_score_bridge.godambe_variance_identity) :
    b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.pate_double_score_approximation_negligible ∧
      b.studentized_bridge.finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ∧
        TendstoInDistribution
          (fun index sample =>
            b.studentized_bridge.studentization_input.scaledStatistic index sample *
              (standardError
                (b.studentized_bridge.studentization_input.varianceEstimate
                  index sample))⁻¹)
          l
          (fun limitSample =>
            b.studentized_bridge.studentization_input.limit limitSample *
              (standardError
                b.studentized_bridge.studentization_input.varianceLimit)⁻¹)
          (fun _index => sampleLaw) limitLaw ∧
          Tendsto
            (fun index =>
              eventProbabilityReal (b.coverage_input.sampleLawSeq index)
                (fun sample =>
                  waldCovers (b.coverage_input.estimator index sample)
                    (b.coverage_input.target index)
                    (b.coverage_input.criticalValue index)
                    (standardError
                      (b.coverage_input.varianceEstimate index sample))
                    (b.coverage_input.scale index)))
            l (nhds b.coverage_input.coverageLimit) := by
  have hstudentized :=
    pate_studentized_tendstoInDistribution_of_finite_score_cell_estimated_score_positiveVariance
      b.studentized_bridge hdesign hbounded harray_lln hfinite henvelope
      hsimplex hlinear hmatrix hdecomp hdenominator hheterogeneity hresidual
      hfirst hlocal hgodambe
  have hcoverage :=
    absoluteWaldCoverage_tendsto_of_variance_input b.coverage_input
  exact ⟨hstudentized.1, hstudentized.2.1, hstudentized.2.2, hcoverage⟩

/-- PATE positive-variance studentized bridge plus two-sided Wald coverage data. -/
structure PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge
    (Cell Index Sample LimitSample : Type*) [DecidableEq Cell]
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : MeasureTheory.Measure Sample)
    (limitLaw : MeasureTheory.Measure LimitSample) (l : Filter Index)
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw] [l.IsCountablyGenerated] where
  studentized_bridge :
    PATEFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l
  coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l

theorem
    pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score
    (b :
      PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell
        Index Sample LimitSample sampleLaw limitLaw l)
    (hdesign :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.aggregate_hajek_decomposition)
    (hdenominator :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.denominator_stabilization)
    (hheterogeneity :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.heterogeneity_clt)
    (hresidual :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.residual_clt)
    (hfirst :
      b.studentized_bridge.finite_estimated_bridge.estimated_score_bridge.first_step_asymptotic_linearization)
    (hlocal :
      b.studentized_bridge.finite_estimated_bridge.estimated_score_bridge.matching_functional_local_expansion)
    (hgodambe :
      b.studentized_bridge.finite_estimated_bridge.estimated_score_bridge.godambe_variance_identity) :
    b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.pate_double_score_approximation_negligible ∧
      b.studentized_bridge.finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ∧
        TendstoInDistribution
          (fun index sample =>
            b.studentized_bridge.studentization_input.scaledStatistic index sample *
              (standardError
                (b.studentized_bridge.studentization_input.varianceEstimate
                  index sample))⁻¹)
          l
          (fun limitSample =>
            b.studentized_bridge.studentization_input.limit limitSample *
              (standardError
                b.studentized_bridge.studentization_input.varianceLimit)⁻¹)
          (fun _index => sampleLaw) limitLaw ∧
          Tendsto
            (fun index =>
              eventProbabilityReal (b.coverage_input.sampleLawSeq index)
                (fun sample =>
                  waldCovers (b.coverage_input.estimator index sample)
                    (b.coverage_input.target index)
                    (b.coverage_input.criticalValue index)
                    (standardError
                      (b.coverage_input.varianceEstimate index sample))
                    (b.coverage_input.scale index)))
            l (nhds b.coverage_input.coverageLimit) := by
  have hstudentized :=
    pate_studentized_tendstoInDistribution_of_finite_score_cell_estimated_score_positiveVariance
      b.studentized_bridge hdesign hbounded harray_lln hfinite henvelope
      hsimplex hlinear hmatrix hdecomp hdenominator hheterogeneity hresidual
      hfirst hlocal hgodambe
  have hcoverage :=
    twoSidedWaldCoverage_tendsto_of_variance_input b.coverage_input
  exact ⟨hstudentized.1, hstudentized.2.1, hstudentized.2.2, hcoverage⟩

/-! ## PATT -/

/-- PATT positive-variance studentized bridge plus absolute Wald coverage data. -/
structure PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge
    (Cell Index Sample LimitSample : Type*) [DecidableEq Cell]
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : MeasureTheory.Measure Sample)
    (limitLaw : MeasureTheory.Measure LimitSample) (l : Filter Index)
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw] [l.IsCountablyGenerated] where
  studentized_bridge :
    PATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l
  coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l

theorem
    patt_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score
    (b :
      PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell
        Index Sample LimitSample sampleLaw limitLaw l)
    (hdesign :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.aggregate_hajek_decomposition)
    (hdenominator :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.denominator_stabilization)
    (hheterogeneity :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.heterogeneity_clt)
    (hresidual :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.residual_clt)
    (hfirst :
      b.studentized_bridge.finite_estimated_bridge.estimated_score_bridge.first_step_asymptotic_linearization)
    (hlocal :
      b.studentized_bridge.finite_estimated_bridge.estimated_score_bridge.matching_functional_local_expansion)
    (hgodambe :
      b.studentized_bridge.finite_estimated_bridge.estimated_score_bridge.godambe_variance_identity) :
    b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
      b.studentized_bridge.finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ∧
        TendstoInDistribution
          (fun index sample =>
            b.studentized_bridge.studentization_input.scaledStatistic index sample *
              (standardError
                (b.studentized_bridge.studentization_input.varianceEstimate
                  index sample))⁻¹)
          l
          (fun limitSample =>
            b.studentized_bridge.studentization_input.limit limitSample *
              (standardError
                b.studentized_bridge.studentization_input.varianceLimit)⁻¹)
          (fun _index => sampleLaw) limitLaw ∧
          Tendsto
            (fun index =>
              eventProbabilityReal (b.coverage_input.sampleLawSeq index)
                (fun sample =>
                  waldCovers (b.coverage_input.estimator index sample)
                    (b.coverage_input.target index)
                    (b.coverage_input.criticalValue index)
                    (standardError
                      (b.coverage_input.varianceEstimate index sample))
                    (b.coverage_input.scale index)))
            l (nhds b.coverage_input.coverageLimit) := by
  have hstudentized :=
    patt_studentized_tendstoInDistribution_of_finite_score_cell_estimated_score_positiveVariance
      b.studentized_bridge hdesign hbounded harray_lln hfinite henvelope
      hsimplex hlinear hmatrix hdecomp hdenominator hheterogeneity hresidual
      hfirst hlocal hgodambe
  have hcoverage :=
    absoluteWaldCoverage_tendsto_of_variance_input b.coverage_input
  exact ⟨hstudentized.1, hstudentized.2.1, hstudentized.2.2, hcoverage⟩

/-- PATT positive-variance studentized bridge plus two-sided Wald coverage data. -/
structure PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge
    (Cell Index Sample LimitSample : Type*) [DecidableEq Cell]
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : MeasureTheory.Measure Sample)
    (limitLaw : MeasureTheory.Measure LimitSample) (l : Filter Index)
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw] [l.IsCountablyGenerated] where
  studentized_bridge :
    PATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l
  coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l

theorem
    patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score
    (b :
      PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell
        Index Sample LimitSample sampleLaw limitLaw l)
    (hdesign :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.aggregate_hajek_decomposition)
    (hdenominator :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.denominator_stabilization)
    (hheterogeneity :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.heterogeneity_clt)
    (hresidual :
      b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.residual_clt)
    (hfirst :
      b.studentized_bridge.finite_estimated_bridge.estimated_score_bridge.first_step_asymptotic_linearization)
    (hlocal :
      b.studentized_bridge.finite_estimated_bridge.estimated_score_bridge.matching_functional_local_expansion)
    (hgodambe :
      b.studentized_bridge.finite_estimated_bridge.estimated_score_bridge.godambe_variance_identity) :
    b.studentized_bridge.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
      b.studentized_bridge.finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ∧
        TendstoInDistribution
          (fun index sample =>
            b.studentized_bridge.studentization_input.scaledStatistic index sample *
              (standardError
                (b.studentized_bridge.studentization_input.varianceEstimate
                  index sample))⁻¹)
          l
          (fun limitSample =>
            b.studentized_bridge.studentization_input.limit limitSample *
              (standardError
                b.studentized_bridge.studentization_input.varianceLimit)⁻¹)
          (fun _index => sampleLaw) limitLaw ∧
          Tendsto
            (fun index =>
              eventProbabilityReal (b.coverage_input.sampleLawSeq index)
                (fun sample =>
                  waldCovers (b.coverage_input.estimator index sample)
                    (b.coverage_input.target index)
                    (b.coverage_input.criticalValue index)
                    (standardError
                      (b.coverage_input.varianceEstimate index sample))
                    (b.coverage_input.scale index)))
            l (nhds b.coverage_input.coverageLimit) := by
  have hstudentized :=
    patt_studentized_tendstoInDistribution_of_finite_score_cell_estimated_score_positiveVariance
      b.studentized_bridge hdesign hbounded harray_lln hfinite henvelope
      hsimplex hlinear hmatrix hdecomp hdenominator hheterogeneity hresidual
      hfirst hlocal hgodambe
  have hcoverage :=
    twoSidedWaldCoverage_tendsto_of_variance_input b.coverage_input
  exact ⟨hstudentized.1, hstudentized.2.1, hstudentized.2.2, hcoverage⟩

/--
PATE finite score-cell estimated-score absolute positive-variance Wald
coverage from an explicit local experiment, with the local derivative,
stochastic equicontinuity, and Godambe identity packaged in the compact core.
-/
theorem
    pate_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_local_experiment_core
    (known :
      PATEFiniteScoreCellKnownScoreAsymptoticBridge Cell)
    (estimated : EstimatedScoreLocalExperimentInput)
    (studentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (coverageInput : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (hknown_to_estimated :
      known.known_score_bridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hscaled :
      estimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution studentizationInput.scaledStatistic l
          studentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (hdesign :
      known.stochastic_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded :
      known.stochastic_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln :
      known.stochastic_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite :
      known.stochastic_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope :
      known.stochastic_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp : known.known_score_bridge.aggregate_hajek_decomposition)
    (hdenominator : known.known_score_bridge.denominator_stabilization)
    (hheterogeneity : known.known_score_bridge.heterogeneity_clt)
    (hresidual : known.known_score_bridge.residual_clt)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (core : EstimatedScoreLocalExperimentCore estimated) :
    known.stochastic_bridge.lln_bridge.indicator_bridge.pate_double_score_approximation_negligible ∧
      estimated.estimated_score_asymptotic_normality ∧
        TendstoInDistribution
          (fun index sample =>
            studentizationInput.scaledStatistic index sample *
              (standardError
                (studentizationInput.varianceEstimate index sample))⁻¹)
          l
          (fun limitSample =>
            studentizationInput.limit limitSample *
              (standardError studentizationInput.varianceLimit)⁻¹)
          (fun _index => sampleLaw) limitLaw ∧
          Tendsto
            (fun index =>
              eventProbabilityReal (coverageInput.sampleLawSeq index)
                (fun sample =>
                  waldCovers (coverageInput.estimator index sample)
                    (coverageInput.target index)
                    (coverageInput.criticalValue index)
                    (standardError
                      (coverageInput.varianceEstimate index sample))
                    (coverageInput.scale index)))
            l (nhds coverageInput.coverageLimit) := by
  let finiteBridge :
      PATEFiniteScoreCellEstimatedScoreAsymptoticBridge Cell :=
    pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
      known estimated hknown_to_estimated
  let studentizedBridge :
      PATEFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge Cell
        Index Sample LimitSample sampleLaw limitLaw l := {
    finite_estimated_bridge := finiteBridge
    studentization_input := studentizationInput
    estimated_score_to_scaled_tendsto := hscaled }
  let b :
      PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell
        Index Sample LimitSample sampleLaw limitLaw l := {
    studentized_bridge := studentizedBridge
    coverage_input := coverageInput }
  simpa [b, studentizedBridge, finiteBridge,
    pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
    pate_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score
      b hdesign hbounded harray_lln hfinite henvelope hsimplex hlinear
      hmatrix hdecomp hdenominator hheterogeneity hresidual hfirst
      ⟨hscore, core.matching_functional_local_derivative,
        core.local_stochastic_equicontinuity⟩
      core.godambe_variance_identity

/--
PATE finite score-cell estimated-score two-sided positive-variance Wald
coverage from an explicit local experiment, with the remaining
local-experiment obligations packaged in the compact core.
-/
theorem
    pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_local_experiment_core
    (known :
      PATEFiniteScoreCellKnownScoreAsymptoticBridge Cell)
    (estimated : EstimatedScoreLocalExperimentInput)
    (studentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (coverageInput : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (hknown_to_estimated :
      known.known_score_bridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hscaled :
      estimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution studentizationInput.scaledStatistic l
          studentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (hdesign :
      known.stochastic_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded :
      known.stochastic_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln :
      known.stochastic_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite :
      known.stochastic_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope :
      known.stochastic_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp : known.known_score_bridge.aggregate_hajek_decomposition)
    (hdenominator : known.known_score_bridge.denominator_stabilization)
    (hheterogeneity : known.known_score_bridge.heterogeneity_clt)
    (hresidual : known.known_score_bridge.residual_clt)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (core : EstimatedScoreLocalExperimentCore estimated) :
    known.stochastic_bridge.lln_bridge.indicator_bridge.pate_double_score_approximation_negligible ∧
      estimated.estimated_score_asymptotic_normality ∧
        TendstoInDistribution
          (fun index sample =>
            studentizationInput.scaledStatistic index sample *
              (standardError
                (studentizationInput.varianceEstimate index sample))⁻¹)
          l
          (fun limitSample =>
            studentizationInput.limit limitSample *
              (standardError studentizationInput.varianceLimit)⁻¹)
          (fun _index => sampleLaw) limitLaw ∧
          Tendsto
            (fun index =>
              eventProbabilityReal (coverageInput.sampleLawSeq index)
                (fun sample =>
                  waldCovers (coverageInput.estimator index sample)
                    (coverageInput.target index)
                    (coverageInput.criticalValue index)
                    (standardError
                      (coverageInput.varianceEstimate index sample))
                    (coverageInput.scale index)))
            l (nhds coverageInput.coverageLimit) := by
  let finiteBridge :
      PATEFiniteScoreCellEstimatedScoreAsymptoticBridge Cell :=
    pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
      known estimated hknown_to_estimated
  let studentizedBridge :
      PATEFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge Cell
        Index Sample LimitSample sampleLaw limitLaw l := {
    finite_estimated_bridge := finiteBridge
    studentization_input := studentizationInput
    estimated_score_to_scaled_tendsto := hscaled }
  let b :
      PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell
        Index Sample LimitSample sampleLaw limitLaw l := {
    studentized_bridge := studentizedBridge
    coverage_input := coverageInput }
  simpa [b, studentizedBridge, finiteBridge,
    pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
    pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score
      b hdesign hbounded harray_lln hfinite henvelope hsimplex hlinear
      hmatrix hdecomp hdenominator hheterogeneity hresidual hfirst
      ⟨hscore, core.matching_functional_local_derivative,
        core.local_stochastic_equicontinuity⟩
      core.godambe_variance_identity

/--
PATT finite score-cell estimated-score absolute positive-variance Wald
coverage from an explicit local experiment, with the local derivative,
stochastic equicontinuity, and Godambe identity packaged in the compact core.
-/
theorem
    patt_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_local_experiment_core
    (known :
      PATTFiniteScoreCellKnownScoreAsymptoticBridge Cell)
    (estimated : EstimatedScoreLocalExperimentInput)
    (studentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (coverageInput : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (hknown_to_estimated :
      known.known_score_bridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hscaled :
      estimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution studentizationInput.scaledStatistic l
          studentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (hdesign :
      known.stochastic_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded :
      known.stochastic_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln :
      known.stochastic_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite :
      known.stochastic_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope :
      known.stochastic_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp : known.known_score_bridge.aggregate_hajek_decomposition)
    (hdenominator : known.known_score_bridge.denominator_stabilization)
    (hheterogeneity : known.known_score_bridge.heterogeneity_clt)
    (hresidual : known.known_score_bridge.residual_clt)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (core : EstimatedScoreLocalExperimentCore estimated) :
    known.stochastic_bridge.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
      estimated.estimated_score_asymptotic_normality ∧
        TendstoInDistribution
          (fun index sample =>
            studentizationInput.scaledStatistic index sample *
              (standardError
                (studentizationInput.varianceEstimate index sample))⁻¹)
          l
          (fun limitSample =>
            studentizationInput.limit limitSample *
              (standardError studentizationInput.varianceLimit)⁻¹)
          (fun _index => sampleLaw) limitLaw ∧
          Tendsto
            (fun index =>
              eventProbabilityReal (coverageInput.sampleLawSeq index)
                (fun sample =>
                  waldCovers (coverageInput.estimator index sample)
                    (coverageInput.target index)
                    (coverageInput.criticalValue index)
                    (standardError
                      (coverageInput.varianceEstimate index sample))
                    (coverageInput.scale index)))
            l (nhds coverageInput.coverageLimit) := by
  let finiteBridge :
      PATTFiniteScoreCellEstimatedScoreAsymptoticBridge Cell :=
    pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
      known estimated hknown_to_estimated
  let studentizedBridge :
      PATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge Cell
        Index Sample LimitSample sampleLaw limitLaw l := {
    finite_estimated_bridge := finiteBridge
    studentization_input := studentizationInput
    estimated_score_to_scaled_tendsto := hscaled }
  let b :
      PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell
        Index Sample LimitSample sampleLaw limitLaw l := {
    studentized_bridge := studentizedBridge
    coverage_input := coverageInput }
  simpa [b, studentizedBridge, finiteBridge,
    pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
    patt_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score
      b hdesign hbounded harray_lln hfinite henvelope hsimplex hlinear
      hmatrix hdecomp hdenominator hheterogeneity hresidual hfirst
      ⟨hscore, core.matching_functional_local_derivative,
        core.local_stochastic_equicontinuity⟩
      core.godambe_variance_identity

/--
PATT finite score-cell estimated-score two-sided positive-variance Wald
coverage from an explicit local experiment, with the remaining
local-experiment obligations packaged in the compact core.
-/
theorem
    patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_local_experiment_core
    (known :
      PATTFiniteScoreCellKnownScoreAsymptoticBridge Cell)
    (estimated : EstimatedScoreLocalExperimentInput)
    (studentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (coverageInput : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (hknown_to_estimated :
      known.known_score_bridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (hscaled :
      estimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution studentizationInput.scaledStatistic l
          studentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (hdesign :
      known.stochastic_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded :
      known.stochastic_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln :
      known.stochastic_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite :
      known.stochastic_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope :
      known.stochastic_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      known.stochastic_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp : known.known_score_bridge.aggregate_hajek_decomposition)
    (hdenominator : known.known_score_bridge.denominator_stabilization)
    (hheterogeneity : known.known_score_bridge.heterogeneity_clt)
    (hresidual : known.known_score_bridge.residual_clt)
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity)
    (core : EstimatedScoreLocalExperimentCore estimated) :
    known.stochastic_bridge.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
      estimated.estimated_score_asymptotic_normality ∧
        TendstoInDistribution
          (fun index sample =>
            studentizationInput.scaledStatistic index sample *
              (standardError
                (studentizationInput.varianceEstimate index sample))⁻¹)
          l
          (fun limitSample =>
            studentizationInput.limit limitSample *
              (standardError studentizationInput.varianceLimit)⁻¹)
          (fun _index => sampleLaw) limitLaw ∧
          Tendsto
            (fun index =>
              eventProbabilityReal (coverageInput.sampleLawSeq index)
                (fun sample =>
                  waldCovers (coverageInput.estimator index sample)
                    (coverageInput.target index)
                    (coverageInput.criticalValue index)
                    (standardError
                      (coverageInput.varianceEstimate index sample))
                    (coverageInput.scale index)))
            l (nhds coverageInput.coverageLimit) := by
  let finiteBridge :
      PATTFiniteScoreCellEstimatedScoreAsymptoticBridge Cell :=
    pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput
      known estimated hknown_to_estimated
  let studentizedBridge :
      PATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge Cell
        Index Sample LimitSample sampleLaw limitLaw l := {
    finite_estimated_bridge := finiteBridge
    studentization_input := studentizationInput
    estimated_score_to_scaled_tendsto := hscaled }
  let b :
      PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell
        Index Sample LimitSample sampleLaw limitLaw l := {
    studentized_bridge := studentizedBridge
    coverage_input := coverageInput }
  simpa [b, studentizedBridge, finiteBridge,
    pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfLocalExperimentInput,
    estimatedScoreAsymptoticBridgeOfLocalExperimentInput] using
    patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score
      b hdesign hbounded harray_lln hfinite henvelope hsimplex hlinear
      hmatrix hdecomp hdenominator hheterogeneity hresidual hfirst
      ⟨hscore, core.matching_functional_local_derivative,
        core.local_stochastic_equicontinuity⟩
      core.godambe_variance_identity

end WDSM
end Matching
end StatInference
