import StatInference.Matching.WDSM.FiniteCellIndicatorGCAdapter
import StatInference.Matching.WDSM.FiniteCellIndicatorEstimatedScorePositiveVarianceWaldBridge
import StatInference.Matching.WDSM.WaldVarianceCriticalRegionCalibration

/-!
# GC adapter for single-arm positive-variance Wald inference

This module connects the GC-backed single-arm finite score-cell
estimated-score studentized bridge to the single-arm positive-variance Wald coverage layer.
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

/--
The PATE absolute positive-variance Wald conclusion used by the single-arm GC adapter.
-/
def PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
    (b :
      PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l) :
    Prop :=
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
          l (nhds b.coverage_input.coverageLimit)

/--
Build a PATE absolute positive-variance Wald bridge whose finite score-cell layer is backed
by a GC certificate on the LLN side.
-/
def pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridgeOfGlivenkoCantelli
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
    (studentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample LimitSample sampleLaw
        limitLaw l)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution studentizationInput.scaledStatistic l
          studentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (coverageInput : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell Index Sample
      LimitSample sampleLaw limitLaw l where
  studentized_bridge :=
    pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput sampleLaw limitLaw l
      studentizationInput estimatedScoreToScaledTendsto
  coverage_input := coverageInput

/--
The GC-backed single-arm PATE route yields absolute positive-variance Wald coverage once the
finite-cell, known-score, estimated-score, studentization, and variance Wald coverage
obligations are supplied.
-/
theorem
    pate_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli
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
    (studentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample LimitSample sampleLaw
        limitLaw l)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution studentizationInput.scaledStatistic l
          studentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (coverageInput : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    (hfinite : indicatorBridge.eventual_finite_conditions)
    (henvelope : indicatorBridge.envelope_convergence)
    (hsimplex : cltBridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      cltBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      cltBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp : knownScoreBridge.aggregate_hajek_decomposition)
    (hdenominator : knownScoreBridge.denominator_stabilization)
    (hheterogeneity : knownScoreBridge.heterogeneity_clt)
    (hresidual : knownScoreBridge.residual_clt)
    (hfirst : estimatedScoreBridge.first_step_asymptotic_linearization)
    (hlocal : estimatedScoreBridge.matching_functional_local_expansion)
    (hgodambe : estimatedScoreBridge.godambe_variance_identity) :
    PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput studentizationInput
        estimatedScoreToScaledTendsto coverageInput) := by
  have hdesign :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).survey_design_regularity := by
    exact hgc
  simpa
    [PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridgeOfGlivenkoCantelli]
    using
      pate_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score
        (pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridgeOfGlivenkoCantelli
          cells referenceShare sample weight score indicatorBridge
          finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
          envelopeToScaled indicatorLLNToScaled knownScoreBridge
          scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
          knownScoreToEstimatedScoreInput studentizationInput
          estimatedScoreToScaledTendsto coverageInput)
        hdesign
        (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
          cells referenceShare sample weight score)
        hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp hdenominator
        hheterogeneity hresidual hfirst hlocal hgodambe

/--
The GC-backed single-arm PATE absolute positive-variance Wald route with the
estimated-score local expansion and Godambe obligations packaged as one
compact core.
-/
theorem
    pate_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli_estimated_score_core
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
    (core : EstimatedScoreAsymptoticBridgeCore estimatedScoreBridge)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimatedScoreBridge.known_score_asymptotic_normality)
    (studentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample LimitSample sampleLaw
        limitLaw l)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution studentizationInput.scaledStatistic l
          studentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (coverageInput : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    (hfinite : indicatorBridge.eventual_finite_conditions)
    (henvelope : indicatorBridge.envelope_convergence)
    (hsimplex : cltBridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      cltBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      cltBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp : knownScoreBridge.aggregate_hajek_decomposition)
    (hdenominator : knownScoreBridge.denominator_stabilization)
    (hheterogeneity : knownScoreBridge.heterogeneity_clt)
    (hresidual : knownScoreBridge.residual_clt)
    (hfirst : estimatedScoreBridge.first_step_asymptotic_linearization) :
    PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput studentizationInput
        estimatedScoreToScaledTendsto coverageInput) :=
  pate_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
    envelopeToScaled indicatorLLNToScaled knownScoreBridge
    scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
    knownScoreToEstimatedScoreInput studentizationInput
    estimatedScoreToScaledTendsto coverageInput hgc hfinite henvelope
    hsimplex hlinear hmatrix hdecomp hdenominator hheterogeneity hresidual
    hfirst core.matching_functional_local_expansion
    core.godambe_variance_identity

/--
The PATE two-sided positive-variance Wald conclusion used by the single-arm GC adapter.
It is stated through the equivalent absolute coverage record because the final
coverage event is the common Wald interval event.
-/
def PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
    (b :
      PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l) :
    Prop :=
  PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
    ({ studentized_bridge := b.studentized_bridge
       coverage_input :=
        absoluteWaldCoverageVarianceInput_of_twoSided b.coverage_input } :
      PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l)

/--
Build a PATE two-sided positive-variance Wald bridge whose finite score-cell layer is
backed by a GC certificate on the LLN side.
-/
def pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridgeOfGlivenkoCantelli
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
    (studentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample LimitSample sampleLaw
        limitLaw l)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution studentizationInput.scaledStatistic l
          studentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (coverageInput : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell Index Sample
      LimitSample sampleLaw limitLaw l where
  studentized_bridge :=
    pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput sampleLaw limitLaw l
      studentizationInput estimatedScoreToScaledTendsto
  coverage_input := coverageInput

/--
The GC-backed single-arm PATE route yields two-sided positive-variance Wald coverage once the
finite-cell, known-score, estimated-score, studentization, and variance Wald coverage
obligations are supplied.
-/
theorem
    pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli
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
    (studentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample LimitSample sampleLaw
        limitLaw l)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution studentizationInput.scaledStatistic l
          studentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (coverageInput : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    (hfinite : indicatorBridge.eventual_finite_conditions)
    (henvelope : indicatorBridge.envelope_convergence)
    (hsimplex : cltBridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      cltBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      cltBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp : knownScoreBridge.aggregate_hajek_decomposition)
    (hdenominator : knownScoreBridge.denominator_stabilization)
    (hheterogeneity : knownScoreBridge.heterogeneity_clt)
    (hresidual : knownScoreBridge.residual_clt)
    (hfirst : estimatedScoreBridge.first_step_asymptotic_linearization)
    (hlocal : estimatedScoreBridge.matching_functional_local_expansion)
    (hgodambe : estimatedScoreBridge.godambe_variance_identity) :
    PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput studentizationInput
        estimatedScoreToScaledTendsto coverageInput) := by
  have hdesign :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).survey_design_regularity := by
    exact hgc
  simpa
    [PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli,
      PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridgeOfGlivenkoCantelli,
      absoluteWaldCoverageVarianceInput_of_twoSided]
    using
      pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score
        (pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridgeOfGlivenkoCantelli
          cells referenceShare sample weight score indicatorBridge
          finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
          envelopeToScaled indicatorLLNToScaled knownScoreBridge
          scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
          knownScoreToEstimatedScoreInput studentizationInput
          estimatedScoreToScaledTendsto coverageInput)
        hdesign
        (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
          cells referenceShare sample weight score)
        hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp hdenominator
        hheterogeneity hresidual hfirst hlocal hgodambe

/--
The GC-backed single-arm PATE two-sided positive-variance Wald route with the
estimated-score local expansion and Godambe obligations packaged as one
compact core.
-/
theorem
    pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli_estimated_score_core
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
    (core : EstimatedScoreAsymptoticBridgeCore estimatedScoreBridge)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimatedScoreBridge.known_score_asymptotic_normality)
    (studentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample LimitSample sampleLaw
        limitLaw l)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution studentizationInput.scaledStatistic l
          studentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (coverageInput : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    (hfinite : indicatorBridge.eventual_finite_conditions)
    (henvelope : indicatorBridge.envelope_convergence)
    (hsimplex : cltBridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      cltBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      cltBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp : knownScoreBridge.aggregate_hajek_decomposition)
    (hdenominator : knownScoreBridge.denominator_stabilization)
    (hheterogeneity : knownScoreBridge.heterogeneity_clt)
    (hresidual : knownScoreBridge.residual_clt)
    (hfirst : estimatedScoreBridge.first_step_asymptotic_linearization) :
    PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput studentizationInput
        estimatedScoreToScaledTendsto coverageInput) :=
  pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
    envelopeToScaled indicatorLLNToScaled knownScoreBridge
    scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
    knownScoreToEstimatedScoreInput studentizationInput
    estimatedScoreToScaledTendsto coverageInput hgc hfinite henvelope
    hsimplex hlinear hmatrix hdecomp hdenominator hheterogeneity hresidual
    hfirst core.matching_functional_local_expansion
    core.godambe_variance_identity

/--
The PATT absolute positive-variance Wald conclusion used by the single-arm GC adapter.
-/
def PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
    (b :
      PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l) :
    Prop :=
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
          l (nhds b.coverage_input.coverageLimit)

/--
Build a PATT absolute positive-variance Wald bridge whose finite score-cell layer is backed
by a GC certificate on the LLN side.
-/
def pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridgeOfGlivenkoCantelli
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
    (studentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample LimitSample sampleLaw
        limitLaw l)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution studentizationInput.scaledStatistic l
          studentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (coverageInput : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell Index Sample
      LimitSample sampleLaw limitLaw l where
  studentized_bridge :=
    pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput sampleLaw limitLaw l
      studentizationInput estimatedScoreToScaledTendsto
  coverage_input := coverageInput

/--
The GC-backed single-arm PATT route yields absolute positive-variance Wald coverage once the
finite-cell, known-score, estimated-score, studentization, and variance Wald coverage
obligations are supplied.
-/
theorem
    patt_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli
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
    (studentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample LimitSample sampleLaw
        limitLaw l)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution studentizationInput.scaledStatistic l
          studentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (coverageInput : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    (hfinite : indicatorBridge.eventual_finite_conditions)
    (henvelope : indicatorBridge.envelope_convergence)
    (hsimplex : cltBridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      cltBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      cltBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp : knownScoreBridge.aggregate_hajek_decomposition)
    (hdenominator : knownScoreBridge.denominator_stabilization)
    (hheterogeneity : knownScoreBridge.heterogeneity_clt)
    (hresidual : knownScoreBridge.residual_clt)
    (hfirst : estimatedScoreBridge.first_step_asymptotic_linearization)
    (hlocal : estimatedScoreBridge.matching_functional_local_expansion)
    (hgodambe : estimatedScoreBridge.godambe_variance_identity) :
    PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput studentizationInput
        estimatedScoreToScaledTendsto coverageInput) := by
  have hdesign :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).survey_design_regularity := by
    exact hgc
  simpa
    [PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridgeOfGlivenkoCantelli]
    using
      patt_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score
        (pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridgeOfGlivenkoCantelli
          cells referenceShare sample weight score indicatorBridge
          finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
          envelopeToScaled indicatorLLNToScaled knownScoreBridge
          scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
          knownScoreToEstimatedScoreInput studentizationInput
          estimatedScoreToScaledTendsto coverageInput)
        hdesign
        (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
          cells referenceShare sample weight score)
        hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp hdenominator
        hheterogeneity hresidual hfirst hlocal hgodambe

/--
The GC-backed single-arm PATT absolute positive-variance Wald route with the
estimated-score local expansion and Godambe obligations packaged as one
compact core.
-/
theorem
    patt_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli_estimated_score_core
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
    (core : EstimatedScoreAsymptoticBridgeCore estimatedScoreBridge)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimatedScoreBridge.known_score_asymptotic_normality)
    (studentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample LimitSample sampleLaw
        limitLaw l)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution studentizationInput.scaledStatistic l
          studentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (coverageInput : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    (hfinite : indicatorBridge.eventual_finite_conditions)
    (henvelope : indicatorBridge.envelope_convergence)
    (hsimplex : cltBridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      cltBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      cltBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp : knownScoreBridge.aggregate_hajek_decomposition)
    (hdenominator : knownScoreBridge.denominator_stabilization)
    (hheterogeneity : knownScoreBridge.heterogeneity_clt)
    (hresidual : knownScoreBridge.residual_clt)
    (hfirst : estimatedScoreBridge.first_step_asymptotic_linearization) :
    PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput studentizationInput
        estimatedScoreToScaledTendsto coverageInput) :=
  patt_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
    envelopeToScaled indicatorLLNToScaled knownScoreBridge
    scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
    knownScoreToEstimatedScoreInput studentizationInput
    estimatedScoreToScaledTendsto coverageInput hgc hfinite henvelope
    hsimplex hlinear hmatrix hdecomp hdenominator hheterogeneity hresidual
    hfirst core.matching_functional_local_expansion
    core.godambe_variance_identity

/--
The PATT two-sided positive-variance Wald conclusion used by the single-arm GC adapter.
It is stated through the equivalent absolute coverage record because the final
coverage event is the common Wald interval event.
-/
def PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
    (b :
      PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l) :
    Prop :=
  PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
    ({ studentized_bridge := b.studentized_bridge
       coverage_input :=
        absoluteWaldCoverageVarianceInput_of_twoSided b.coverage_input } :
      PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l)

/--
Build a PATT two-sided positive-variance Wald bridge whose finite score-cell layer is
backed by a GC certificate on the LLN side.
-/
def pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridgeOfGlivenkoCantelli
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
    (studentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample LimitSample sampleLaw
        limitLaw l)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution studentizationInput.scaledStatistic l
          studentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (coverageInput : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell Index Sample
      LimitSample sampleLaw limitLaw l where
  studentized_bridge :=
    pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput sampleLaw limitLaw l
      studentizationInput estimatedScoreToScaledTendsto
  coverage_input := coverageInput

/--
The GC-backed single-arm PATT route yields two-sided positive-variance Wald coverage once the
finite-cell, known-score, estimated-score, studentization, and variance Wald coverage
obligations are supplied.
-/
theorem
    patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli
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
    (studentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample LimitSample sampleLaw
        limitLaw l)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution studentizationInput.scaledStatistic l
          studentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (coverageInput : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    (hfinite : indicatorBridge.eventual_finite_conditions)
    (henvelope : indicatorBridge.envelope_convergence)
    (hsimplex : cltBridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      cltBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      cltBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp : knownScoreBridge.aggregate_hajek_decomposition)
    (hdenominator : knownScoreBridge.denominator_stabilization)
    (hheterogeneity : knownScoreBridge.heterogeneity_clt)
    (hresidual : knownScoreBridge.residual_clt)
    (hfirst : estimatedScoreBridge.first_step_asymptotic_linearization)
    (hlocal : estimatedScoreBridge.matching_functional_local_expansion)
    (hgodambe : estimatedScoreBridge.godambe_variance_identity) :
    PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput studentizationInput
        estimatedScoreToScaledTendsto coverageInput) := by
  have hdesign :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).survey_design_regularity := by
    exact hgc
  simpa
    [PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli,
      PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridgeOfGlivenkoCantelli,
      absoluteWaldCoverageVarianceInput_of_twoSided]
    using
      patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score
        (pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridgeOfGlivenkoCantelli
          cells referenceShare sample weight score indicatorBridge
          finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
          envelopeToScaled indicatorLLNToScaled knownScoreBridge
          scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
          knownScoreToEstimatedScoreInput studentizationInput
          estimatedScoreToScaledTendsto coverageInput)
        hdesign
        (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
          cells referenceShare sample weight score)
        hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp hdenominator
        hheterogeneity hresidual hfirst hlocal hgodambe

/--
The GC-backed single-arm PATT two-sided positive-variance Wald route with the
estimated-score local expansion and Godambe obligations packaged as one
compact core.
-/
theorem
    patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli_estimated_score_core
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
    (core : EstimatedScoreAsymptoticBridgeCore estimatedScoreBridge)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimatedScoreBridge.known_score_asymptotic_normality)
    (studentizationInput :
      EstimatedScorePositiveVarianceStudentizationInput Index Sample LimitSample sampleLaw
        limitLaw l)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution studentizationInput.scaledStatistic l
          studentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (coverageInput : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    (hfinite : indicatorBridge.eventual_finite_conditions)
    (henvelope : indicatorBridge.envelope_convergence)
    (hsimplex : cltBridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      cltBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      cltBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp : knownScoreBridge.aggregate_hajek_decomposition)
    (hdenominator : knownScoreBridge.denominator_stabilization)
    (hheterogeneity : knownScoreBridge.heterogeneity_clt)
    (hresidual : knownScoreBridge.residual_clt)
    (hfirst : estimatedScoreBridge.first_step_asymptotic_linearization) :
    PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput studentizationInput
        estimatedScoreToScaledTendsto coverageInput) :=
  patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
    envelopeToScaled indicatorLLNToScaled knownScoreBridge
    scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
    knownScoreToEstimatedScoreInput studentizationInput
    estimatedScoreToScaledTendsto coverageInput hgc hfinite henvelope
    hsimplex hlinear hmatrix hdecomp hdenominator hheterogeneity hresidual
    hfirst core.matching_functional_local_expansion
    core.godambe_variance_identity

/--
Convert a GC-backed PATE absolute positive-variance Wald bridge into the corresponding two-sided
variance Wald bridge by calibrating the critical region.
-/
def PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridgeOfAbsoluteCoverage
    (b :
      PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l) :
    PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell Index Sample
      LimitSample sampleLaw limitLaw l where
  studentized_bridge := b.studentized_bridge
  coverage_input := twoSidedWaldCoverageVarianceInput_of_absolute b.coverage_input

/--
Absolute-region PATE Wald calibration also yields the two-sided Wald
conclusion for the same GC-backed finite score-cell bridge.
-/
theorem
    pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_finite_score_cell_estimated_score_glivenkoCantelli
    (b :
      PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l)
    (h :
      PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
        b) :
    PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
      (PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridgeOfAbsoluteCoverage
        b) := by
  simpa
    [PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli,
      PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridgeOfAbsoluteCoverage,
      twoSidedWaldCoverageVarianceInput_of_absolute,
      absoluteWaldCoverageVarianceInput_of_twoSided]
    using h

/--
Convert a GC-backed PATE two-sided positive-variance Wald bridge into the corresponding absolute
variance Wald bridge by calibrating the critical region.
-/
def PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridgeOfTwoSidedCoverage
    (b :
      PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l) :
    PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell Index Sample
      LimitSample sampleLaw limitLaw l where
  studentized_bridge := b.studentized_bridge
  coverage_input := absoluteWaldCoverageVarianceInput_of_twoSided b.coverage_input

/--
Two-sided PATE Wald calibration also yields the absolute Wald conclusion for
the same GC-backed finite score-cell bridge.
-/
theorem
    pate_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_finite_score_cell_estimated_score_glivenkoCantelli
    (b :
      PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l)
    (h :
      PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
        b) :
    PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
      (PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridgeOfTwoSidedCoverage
        b) := by
  simpa
    [PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli,
      PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridgeOfTwoSidedCoverage]
    using h

/--
Convert a GC-backed PATT absolute positive-variance Wald bridge into the corresponding two-sided
variance Wald bridge by calibrating the critical region.
-/
def PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridgeOfAbsoluteCoverage
    (b :
      PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l) :
    PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell Index Sample
      LimitSample sampleLaw limitLaw l where
  studentized_bridge := b.studentized_bridge
  coverage_input := twoSidedWaldCoverageVarianceInput_of_absolute b.coverage_input

/--
Absolute-region PATT Wald calibration also yields the two-sided Wald
conclusion for the same GC-backed finite score-cell bridge.
-/
theorem
    patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_finite_score_cell_estimated_score_glivenkoCantelli
    (b :
      PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l)
    (h :
      PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
        b) :
    PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
      (PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridgeOfAbsoluteCoverage
        b) := by
  simpa
    [PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli,
      PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridgeOfAbsoluteCoverage,
      twoSidedWaldCoverageVarianceInput_of_absolute,
      absoluteWaldCoverageVarianceInput_of_twoSided]
    using h

/--
Convert a GC-backed PATT two-sided positive-variance Wald bridge into the corresponding absolute
variance Wald bridge by calibrating the critical region.
-/
def PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridgeOfTwoSidedCoverage
    (b :
      PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l) :
    PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell Index Sample
      LimitSample sampleLaw limitLaw l where
  studentized_bridge := b.studentized_bridge
  coverage_input := absoluteWaldCoverageVarianceInput_of_twoSided b.coverage_input

/--
Two-sided PATT Wald calibration also yields the absolute Wald conclusion for
the same GC-backed finite score-cell bridge.
-/
theorem
    patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_finite_score_cell_estimated_score_glivenkoCantelli
    (b :
      PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l)
    (h :
      PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
        b) :
    PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
      (PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridgeOfTwoSidedCoverage
        b) := by
  simpa
    [PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli,
      PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridgeOfTwoSidedCoverage]
    using h

/--
Attach the GC-backed score-cell mass LLN to an already derived PATE absolute
positive-variance Wald conclusion.
-/
theorem
    pate_absolutePositiveVarianceWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    {b :
      PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell
        Index Sample LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
        b) :
    PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  ⟨hcoverage,
    cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells referenceShare sample weight score hgc⟩

/--
Attach the GC-backed score-cell mass LLN to an already derived PATE two-sided
positive-variance Wald conclusion.
-/
theorem
    pate_twoSidedPositiveVarianceWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    {b :
      PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell
        Index Sample LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
        b) :
    PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  ⟨hcoverage,
    cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells referenceShare sample weight score hgc⟩

/--
Attach the GC-backed score-cell mass LLN to an already derived PATT absolute
positive-variance Wald conclusion.
-/
theorem
    patt_absolutePositiveVarianceWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    {b :
      PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell
        Index Sample LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
        b) :
    PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  ⟨hcoverage,
    cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells referenceShare sample weight score hgc⟩

/--
Attach the GC-backed score-cell mass LLN to an already derived PATT two-sided
positive-variance Wald conclusion.
-/
theorem
    patt_twoSidedPositiveVarianceWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    {b :
      PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell
        Index Sample LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
        b) :
    PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  ⟨hcoverage,
    cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells referenceShare sample weight score hgc⟩

theorem
    pate_absolutePositiveVarianceWaldConclusion_and_mass_lln_of_l1BracketingNumber_obligations
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (obligations :
      L1BracketingNumberConstructorObligations (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} referenceShare
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    {b :
      PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell
        Index Sample LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
        b) :
    PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  pate_absolutePositiveVarianceWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    cells referenceShare sample weight score
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      cells referenceShare sample weight score obligations)
    hcoverage

theorem
    pate_absolutePositiveVarianceWaldConclusion_and_mass_lln_of_vdvw241_endpoint_assembly
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (assembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} referenceShare
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    {b :
      PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell
        Index Sample LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
        b) :
    PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  pate_absolutePositiveVarianceWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    cells referenceShare sample weight score
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      cells referenceShare sample weight score assembly)
    hcoverage

theorem
    pate_twoSidedPositiveVarianceWaldConclusion_and_mass_lln_of_l1BracketingNumber_obligations
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (obligations :
      L1BracketingNumberConstructorObligations (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} referenceShare
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    {b :
      PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell
        Index Sample LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
        b) :
    PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  pate_twoSidedPositiveVarianceWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    cells referenceShare sample weight score
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      cells referenceShare sample weight score obligations)
    hcoverage

theorem
    pate_twoSidedPositiveVarianceWaldConclusion_and_mass_lln_of_vdvw241_endpoint_assembly
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (assembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} referenceShare
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    {b :
      PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell
        Index Sample LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
        b) :
    PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  pate_twoSidedPositiveVarianceWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    cells referenceShare sample weight score
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      cells referenceShare sample weight score assembly)
    hcoverage

theorem
    patt_absolutePositiveVarianceWaldConclusion_and_mass_lln_of_l1BracketingNumber_obligations
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (obligations :
      L1BracketingNumberConstructorObligations (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} referenceShare
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    {b :
      PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell
        Index Sample LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
        b) :
    PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  patt_absolutePositiveVarianceWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    cells referenceShare sample weight score
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      cells referenceShare sample weight score obligations)
    hcoverage

theorem
    patt_absolutePositiveVarianceWaldConclusion_and_mass_lln_of_vdvw241_endpoint_assembly
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (assembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} referenceShare
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    {b :
      PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell
        Index Sample LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
        b) :
    PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  patt_absolutePositiveVarianceWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    cells referenceShare sample weight score
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      cells referenceShare sample weight score assembly)
    hcoverage

theorem
    patt_twoSidedPositiveVarianceWaldConclusion_and_mass_lln_of_l1BracketingNumber_obligations
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (obligations :
      L1BracketingNumberConstructorObligations (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} referenceShare
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    {b :
      PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell
        Index Sample LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
        b) :
    PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  patt_twoSidedPositiveVarianceWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    cells referenceShare sample weight score
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      cells referenceShare sample weight score obligations)
    hcoverage

theorem
    patt_twoSidedPositiveVarianceWaldConclusion_and_mass_lln_of_vdvw241_endpoint_assembly
    {Bracket : Type*} [Fintype Bracket]
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (assembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := Bracket)
        {cell : Cell | cell ∈ cells} referenceShare
        (fun sampleSize cell =>
          weightedSampleSum (sample sampleSize) (weight sampleSize)
            (scoreCellIndicator (score sampleSize) cell)))
    {b :
      PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell
        Index Sample LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
        b) :
    PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  patt_twoSidedPositiveVarianceWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    cells referenceShare sample weight score
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      cells referenceShare sample weight score assembly)
    hcoverage

end WDSM
end Matching
end StatInference
