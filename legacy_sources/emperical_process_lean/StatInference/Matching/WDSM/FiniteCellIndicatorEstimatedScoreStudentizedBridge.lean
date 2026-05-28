import StatInference.Matching.WDSM.FiniteCellIndicatorEstimatedScoreAsymptoticBridge
import StatInference.Matching.WDSM.StudentizedLimitAlgebra

/-!
# Finite score-cell approximation to estimated-score studentized WDSM limits

This module composes the finite score-cell estimated-score asymptotic bridge
with the variance-consistency studentization layer.  It keeps the conversion
from the paper-level estimated-score asymptotic-normality proposition to an
actual `TendstoInDistribution` statement explicit.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open scoped Topology

/--
Variance-consistency and measurability input for studentizing an estimated-score
WDSM statistic, excluding the scaled-statistic distributional limit itself.
-/
structure EstimatedScoreStudentizationInput
    (Index Sample LimitSample : Type*) [MeasurableSpace Sample]
    [MeasurableSpace LimitSample] (sampleLaw : MeasureTheory.Measure Sample)
    (limitLaw : MeasureTheory.Measure LimitSample) (l : Filter Index)
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw] [l.IsCountablyGenerated] where
  scaledStatistic : Index -> Sample -> Real
  varianceEstimate : Index -> Sample -> Real
  limit : LimitSample -> Real
  varianceLimit : Real
  variance_tendsto :
    TendstoInMeasure sampleLaw varianceEstimate l
      (fun _sample => varianceLimit)
  standardErrorLimit_ne_zero :
    standardError varianceLimit ≠ 0
  inverseStandardError_measurable :
    ∀ index,
      AEMeasurable
        (fun sample => (standardError (varianceEstimate index sample))⁻¹)
        sampleLaw

variable {Cell Index Sample LimitSample : Type*}
variable [DecidableEq Cell]
variable [MeasurableSpace Sample] [MeasurableSpace LimitSample]
variable {sampleLaw : MeasureTheory.Measure Sample}
variable {limitLaw : MeasureTheory.Measure LimitSample}
variable [MeasureTheory.IsProbabilityMeasure sampleLaw]
variable [MeasureTheory.IsProbabilityMeasure limitLaw]
variable {l : Filter Index}
variable [l.IsCountablyGenerated]

/-- Variance-consistency input turns a scaled weak limit into a studentized weak limit. -/
theorem studentized_tendstoInDistribution_of_estimated_score_studentization_input
    (input :
      EstimatedScoreStudentizationInput Index Sample LimitSample sampleLaw
        limitLaw l)
    (hscaled :
      TendstoInDistribution input.scaledStatistic l input.limit
        (fun _index => sampleLaw) limitLaw) :
    TendstoInDistribution
      (fun index sample =>
        input.scaledStatistic index sample *
          (standardError (input.varianceEstimate index sample))⁻¹)
      l
      (fun limitSample =>
        input.limit limitSample * (standardError input.varianceLimit)⁻¹)
      (fun _index => sampleLaw) limitLaw :=
  tendstoInDistribution_studentized_of_variance_consistency
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    input.scaledStatistic input.varianceEstimate input.limit
    input.varianceLimit hscaled input.variance_tendsto
    input.standardErrorLimit_ne_zero input.inverseStandardError_measurable

/-- PATE finite score-cell estimated-score bridge plus variance-consistency data. -/
structure PATEFiniteScoreCellEstimatedScoreStudentizedBridge
    (Cell Index Sample LimitSample : Type*) [DecidableEq Cell]
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : MeasureTheory.Measure Sample)
    (limitLaw : MeasureTheory.Measure LimitSample) (l : Filter Index)
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw] [l.IsCountablyGenerated] where
  finite_estimated_bridge :
    PATEFiniteScoreCellEstimatedScoreAsymptoticBridge Cell
  studentization_input :
    EstimatedScoreStudentizationInput Index Sample LimitSample sampleLaw
      limitLaw l
  estimated_score_to_scaled_tendsto :
    finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ->
      TendstoInDistribution studentization_input.scaledStatistic l
        studentization_input.limit (fun _index => sampleLaw) limitLaw

theorem
    pate_studentized_tendstoInDistribution_of_finite_score_cell_estimated_score
    (b :
      PATEFiniteScoreCellEstimatedScoreStudentizedBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l)
    (hdesign :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.aggregate_hajek_decomposition)
    (hdenominator :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.denominator_stabilization)
    (hheterogeneity :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.heterogeneity_clt)
    (hresidual :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.residual_clt)
    (hfirst :
      b.finite_estimated_bridge.estimated_score_bridge.first_step_asymptotic_linearization)
    (hlocal :
      b.finite_estimated_bridge.estimated_score_bridge.matching_functional_local_expansion)
    (hgodambe :
      b.finite_estimated_bridge.estimated_score_bridge.godambe_variance_identity) :
    b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.pate_double_score_approximation_negligible ∧
      b.finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ∧
        TendstoInDistribution
          (fun index sample =>
            b.studentization_input.scaledStatistic index sample *
              (standardError
                (b.studentization_input.varianceEstimate index sample))⁻¹)
          l
          (fun limitSample =>
            b.studentization_input.limit limitSample *
              (standardError b.studentization_input.varianceLimit)⁻¹)
          (fun _index => sampleLaw) limitLaw := by
  have hestimated_pair :=
    pate_estimated_score_asymptotic_normality_of_finite_score_cell_stochastic
      b.finite_estimated_bridge hdesign hbounded harray_lln hfinite henvelope
      hsimplex hlinear hmatrix hdecomp hdenominator hheterogeneity hresidual
      hfirst hlocal hgodambe
  have hscaled :
      TendstoInDistribution b.studentization_input.scaledStatistic l
        b.studentization_input.limit (fun _index => sampleLaw) limitLaw :=
    b.estimated_score_to_scaled_tendsto hestimated_pair.2
  have hstudentized :=
    studentized_tendstoInDistribution_of_estimated_score_studentization_input
      b.studentization_input hscaled
  exact ⟨hestimated_pair.1, hestimated_pair.2, hstudentized⟩

/-- PATT finite score-cell estimated-score bridge plus variance-consistency data. -/
structure PATTFiniteScoreCellEstimatedScoreStudentizedBridge
    (Cell Index Sample LimitSample : Type*) [DecidableEq Cell]
    [MeasurableSpace Sample] [MeasurableSpace LimitSample]
    (sampleLaw : MeasureTheory.Measure Sample)
    (limitLaw : MeasureTheory.Measure LimitSample) (l : Filter Index)
    [MeasureTheory.IsProbabilityMeasure sampleLaw]
    [MeasureTheory.IsProbabilityMeasure limitLaw] [l.IsCountablyGenerated] where
  finite_estimated_bridge :
    PATTFiniteScoreCellEstimatedScoreAsymptoticBridge Cell
  studentization_input :
    EstimatedScoreStudentizationInput Index Sample LimitSample sampleLaw
      limitLaw l
  estimated_score_to_scaled_tendsto :
    finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ->
      TendstoInDistribution studentization_input.scaledStatistic l
        studentization_input.limit (fun _index => sampleLaw) limitLaw

theorem
    patt_studentized_tendstoInDistribution_of_finite_score_cell_estimated_score
    (b :
      PATTFiniteScoreCellEstimatedScoreStudentizedBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l)
    (hdesign :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.aggregate_hajek_decomposition)
    (hdenominator :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.denominator_stabilization)
    (hheterogeneity :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.heterogeneity_clt)
    (hresidual :
      b.finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.residual_clt)
    (hfirst :
      b.finite_estimated_bridge.estimated_score_bridge.first_step_asymptotic_linearization)
    (hlocal :
      b.finite_estimated_bridge.estimated_score_bridge.matching_functional_local_expansion)
    (hgodambe :
      b.finite_estimated_bridge.estimated_score_bridge.godambe_variance_identity) :
    b.finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
      b.finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ∧
        TendstoInDistribution
          (fun index sample =>
            b.studentization_input.scaledStatistic index sample *
              (standardError
                (b.studentization_input.varianceEstimate index sample))⁻¹)
          l
          (fun limitSample =>
            b.studentization_input.limit limitSample *
              (standardError b.studentization_input.varianceLimit)⁻¹)
          (fun _index => sampleLaw) limitLaw := by
  have hestimated_pair :=
    patt_estimated_score_asymptotic_normality_of_finite_score_cell_stochastic
      b.finite_estimated_bridge hdesign hbounded harray_lln hfinite henvelope
      hsimplex hlinear hmatrix hdecomp hdenominator hheterogeneity hresidual
      hfirst hlocal hgodambe
  have hscaled :
      TendstoInDistribution b.studentization_input.scaledStatistic l
        b.studentization_input.limit (fun _index => sampleLaw) limitLaw :=
    b.estimated_score_to_scaled_tendsto hestimated_pair.2
  have hstudentized :=
    studentized_tendstoInDistribution_of_estimated_score_studentization_input
      b.studentization_input hscaled
  exact ⟨hestimated_pair.1, hestimated_pair.2, hstudentized⟩

end WDSM
end Matching
end StatInference
