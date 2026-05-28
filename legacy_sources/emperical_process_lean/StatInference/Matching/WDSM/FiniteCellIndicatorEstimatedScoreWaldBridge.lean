import StatInference.Matching.WDSM.FiniteCellIndicatorEstimatedScoreStudentizedBridge
import StatInference.Matching.WDSM.WaldInferenceBridge

/-!
# Finite score-cell approximation to estimated-score WDSM Wald inference

This module composes the finite score-cell estimated-score studentized bridge
with the existing Wald coverage bridge.  Critical-value calibration remains an
explicit field of the absolute or two-sided Wald coverage input.
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

/-- PATE estimated-score Wald bridge for an absolute critical region. -/
structure PATEFiniteScoreCellEstimatedScoreAbsoluteWaldBridge
    (Cell Index Sample LimitSample : Type*) [DecidableEq Cell]
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : MeasureTheory.Measure Sample)
    (limitLaw : MeasureTheory.Measure LimitSample) (l : Filter Index)
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw] [l.IsCountablyGenerated] where
  studentized_bridge :
    PATEFiniteScoreCellEstimatedScoreStudentizedBridge Cell Index Sample
      LimitSample sampleLaw limitLaw l
  coverage_input : AbsoluteWaldCoverageInput Index Sample l

theorem
    pate_absoluteWaldCoverage_tendsto_of_finite_score_cell_estimated_score
    (b :
      PATEFiniteScoreCellEstimatedScoreAbsoluteWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l)
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
                    (b.coverage_input.standardError index sample)
                    (b.coverage_input.scale index)))
            l (nhds b.coverage_input.coverageLimit) := by
  have hstudentized :=
    pate_studentized_tendstoInDistribution_of_finite_score_cell_estimated_score
      b.studentized_bridge hdesign hbounded harray_lln hfinite henvelope
      hsimplex hlinear hmatrix hdecomp hdenominator hheterogeneity hresidual
      hfirst hlocal hgodambe
  have hcoverage := absoluteWaldCoverage_tendsto_of_input b.coverage_input
  exact ⟨hstudentized.1, hstudentized.2.1, hstudentized.2.2, hcoverage⟩

/-- PATE estimated-score Wald bridge for a two-sided critical region. -/
structure PATEFiniteScoreCellEstimatedScoreTwoSidedWaldBridge
    (Cell Index Sample LimitSample : Type*) [DecidableEq Cell]
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : MeasureTheory.Measure Sample)
    (limitLaw : MeasureTheory.Measure LimitSample) (l : Filter Index)
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw] [l.IsCountablyGenerated] where
  studentized_bridge :
    PATEFiniteScoreCellEstimatedScoreStudentizedBridge Cell Index Sample
      LimitSample sampleLaw limitLaw l
  coverage_input : TwoSidedWaldCoverageInput Index Sample l

theorem
    pate_twoSidedWaldCoverage_tendsto_of_finite_score_cell_estimated_score
    (b :
      PATEFiniteScoreCellEstimatedScoreTwoSidedWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l)
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
                    (b.coverage_input.standardError index sample)
                    (b.coverage_input.scale index)))
            l (nhds b.coverage_input.coverageLimit) := by
  have hstudentized :=
    pate_studentized_tendstoInDistribution_of_finite_score_cell_estimated_score
      b.studentized_bridge hdesign hbounded harray_lln hfinite henvelope
      hsimplex hlinear hmatrix hdecomp hdenominator hheterogeneity hresidual
      hfirst hlocal hgodambe
  have hcoverage := twoSidedWaldCoverage_tendsto_of_input b.coverage_input
  exact ⟨hstudentized.1, hstudentized.2.1, hstudentized.2.2, hcoverage⟩

/-- PATT estimated-score Wald bridge for an absolute critical region. -/
structure PATTFiniteScoreCellEstimatedScoreAbsoluteWaldBridge
    (Cell Index Sample LimitSample : Type*) [DecidableEq Cell]
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : MeasureTheory.Measure Sample)
    (limitLaw : MeasureTheory.Measure LimitSample) (l : Filter Index)
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw] [l.IsCountablyGenerated] where
  studentized_bridge :
    PATTFiniteScoreCellEstimatedScoreStudentizedBridge Cell Index Sample
      LimitSample sampleLaw limitLaw l
  coverage_input : AbsoluteWaldCoverageInput Index Sample l

theorem
    patt_absoluteWaldCoverage_tendsto_of_finite_score_cell_estimated_score
    (b :
      PATTFiniteScoreCellEstimatedScoreAbsoluteWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l)
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
                    (b.coverage_input.standardError index sample)
                    (b.coverage_input.scale index)))
            l (nhds b.coverage_input.coverageLimit) := by
  have hstudentized :=
    patt_studentized_tendstoInDistribution_of_finite_score_cell_estimated_score
      b.studentized_bridge hdesign hbounded harray_lln hfinite henvelope
      hsimplex hlinear hmatrix hdecomp hdenominator hheterogeneity hresidual
      hfirst hlocal hgodambe
  have hcoverage := absoluteWaldCoverage_tendsto_of_input b.coverage_input
  exact ⟨hstudentized.1, hstudentized.2.1, hstudentized.2.2, hcoverage⟩

/-- PATT estimated-score Wald bridge for a two-sided critical region. -/
structure PATTFiniteScoreCellEstimatedScoreTwoSidedWaldBridge
    (Cell Index Sample LimitSample : Type*) [DecidableEq Cell]
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : MeasureTheory.Measure Sample)
    (limitLaw : MeasureTheory.Measure LimitSample) (l : Filter Index)
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw] [l.IsCountablyGenerated] where
  studentized_bridge :
    PATTFiniteScoreCellEstimatedScoreStudentizedBridge Cell Index Sample
      LimitSample sampleLaw limitLaw l
  coverage_input : TwoSidedWaldCoverageInput Index Sample l

theorem
    patt_twoSidedWaldCoverage_tendsto_of_finite_score_cell_estimated_score
    (b :
      PATTFiniteScoreCellEstimatedScoreTwoSidedWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l)
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
                    (b.coverage_input.standardError index sample)
                    (b.coverage_input.scale index)))
            l (nhds b.coverage_input.coverageLimit) := by
  have hstudentized :=
    patt_studentized_tendstoInDistribution_of_finite_score_cell_estimated_score
      b.studentized_bridge hdesign hbounded harray_lln hfinite henvelope
      hsimplex hlinear hmatrix hdecomp hdenominator hheterogeneity hresidual
      hfirst hlocal hgodambe
  have hcoverage := twoSidedWaldCoverage_tendsto_of_input b.coverage_input
  exact ⟨hstudentized.1, hstudentized.2.1, hstudentized.2.2, hcoverage⟩

end WDSM
end Matching
end StatInference
