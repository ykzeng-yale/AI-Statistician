import StatInference.Matching.WDSM.FiniteCellIndicatorGCAdapter
import StatInference.Matching.WDSM.FiniteCellIndicatorEstimatedScoreVarianceWaldBridge
import StatInference.Matching.WDSM.WaldVarianceCriticalRegionCalibration

/-!
# GC adapter for single-arm variance-estimate Wald inference

This module connects the GC-backed single-arm finite score-cell
estimated-score studentized bridge to the single-arm variance-estimate Wald coverage layer.
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
The PATE absolute variance-estimate Wald conclusion used by the single-arm GC adapter.
-/
def PATEFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldConclusionOfGlivenkoCantelli
    (b :
      PATEFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridge Cell Index Sample
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
Build a PATE absolute variance-estimate Wald bridge whose finite score-cell layer is backed
by a GC certificate on the LLN side.
-/
def pateFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridgeOfGlivenkoCantelli
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
      EstimatedScoreStudentizationInput Index Sample LimitSample sampleLaw
        limitLaw l)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution studentizationInput.scaledStatistic l
          studentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (coverageInput : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATEFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridge Cell Index Sample
      LimitSample sampleLaw limitLaw l where
  studentized_bridge :=
    pateFiniteScoreCellEstimatedScoreStudentizedBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput sampleLaw limitLaw l
      studentizationInput estimatedScoreToScaledTendsto
  coverage_input := coverageInput

/--
The GC-backed single-arm PATE route yields absolute variance-estimate Wald coverage once the
finite-cell, known-score, estimated-score, studentization, and variance Wald coverage
obligations are supplied.
-/
theorem
    pate_absoluteVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli
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
      EstimatedScoreStudentizationInput Index Sample LimitSample sampleLaw
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
    PATEFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridgeOfGlivenkoCantelli
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
    [PATEFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldConclusionOfGlivenkoCantelli,
      pateFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridgeOfGlivenkoCantelli]
    using
      pate_absoluteVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score
        (pateFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridgeOfGlivenkoCantelli
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
The GC-backed single-arm PATE absolute variance-estimate Wald route with the
estimated-score local expansion and Godambe obligations packaged as one
compact core.
-/
theorem
    pate_absoluteVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli_estimated_score_core
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
      EstimatedScoreStudentizationInput Index Sample LimitSample sampleLaw
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
    PATEFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput studentizationInput
        estimatedScoreToScaledTendsto coverageInput) :=
  pate_absoluteVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli
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
The PATE two-sided variance-estimate Wald conclusion used by the single-arm GC adapter.
It is stated through the equivalent absolute coverage record because the final
coverage event is the common Wald interval event.
-/
def PATEFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldConclusionOfGlivenkoCantelli
    (b :
      PATEFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l) :
    Prop :=
  PATEFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldConclusionOfGlivenkoCantelli
    ({ studentized_bridge := b.studentized_bridge
       coverage_input :=
        absoluteWaldCoverageVarianceInput_of_twoSided b.coverage_input } :
      PATEFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l)

/--
Build a PATE two-sided variance-estimate Wald bridge whose finite score-cell layer is
backed by a GC certificate on the LLN side.
-/
def pateFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldBridgeOfGlivenkoCantelli
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
      EstimatedScoreStudentizationInput Index Sample LimitSample sampleLaw
        limitLaw l)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution studentizationInput.scaledStatistic l
          studentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (coverageInput : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATEFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldBridge Cell Index Sample
      LimitSample sampleLaw limitLaw l where
  studentized_bridge :=
    pateFiniteScoreCellEstimatedScoreStudentizedBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput sampleLaw limitLaw l
      studentizationInput estimatedScoreToScaledTendsto
  coverage_input := coverageInput

/--
The GC-backed single-arm PATE route yields two-sided variance-estimate Wald coverage once the
finite-cell, known-score, estimated-score, studentization, and variance Wald coverage
obligations are supplied.
-/
theorem
    pate_twoSidedVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli
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
      EstimatedScoreStudentizationInput Index Sample LimitSample sampleLaw
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
    PATEFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldBridgeOfGlivenkoCantelli
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
    [PATEFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldConclusionOfGlivenkoCantelli,
      PATEFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldConclusionOfGlivenkoCantelli,
      pateFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldBridgeOfGlivenkoCantelli,
      absoluteWaldCoverageVarianceInput_of_twoSided]
    using
      pate_twoSidedVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score
        (pateFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldBridgeOfGlivenkoCantelli
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
The GC-backed single-arm PATE two-sided variance-estimate Wald route with the
estimated-score local expansion and Godambe obligations packaged as one
compact core.
-/
theorem
    pate_twoSidedVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli_estimated_score_core
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
      EstimatedScoreStudentizationInput Index Sample LimitSample sampleLaw
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
    PATEFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput studentizationInput
        estimatedScoreToScaledTendsto coverageInput) :=
  pate_twoSidedVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli
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
The PATT absolute variance-estimate Wald conclusion used by the single-arm GC adapter.
-/
def PATTFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldConclusionOfGlivenkoCantelli
    (b :
      PATTFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridge Cell Index Sample
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
Build a PATT absolute variance-estimate Wald bridge whose finite score-cell layer is backed
by a GC certificate on the LLN side.
-/
def pattFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridgeOfGlivenkoCantelli
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
      EstimatedScoreStudentizationInput Index Sample LimitSample sampleLaw
        limitLaw l)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution studentizationInput.scaledStatistic l
          studentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (coverageInput : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATTFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridge Cell Index Sample
      LimitSample sampleLaw limitLaw l where
  studentized_bridge :=
    pattFiniteScoreCellEstimatedScoreStudentizedBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput sampleLaw limitLaw l
      studentizationInput estimatedScoreToScaledTendsto
  coverage_input := coverageInput

/--
The GC-backed single-arm PATT route yields absolute variance-estimate Wald coverage once the
finite-cell, known-score, estimated-score, studentization, and variance Wald coverage
obligations are supplied.
-/
theorem
    patt_absoluteVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli
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
      EstimatedScoreStudentizationInput Index Sample LimitSample sampleLaw
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
    PATTFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridgeOfGlivenkoCantelli
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
    [PATTFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldConclusionOfGlivenkoCantelli,
      pattFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridgeOfGlivenkoCantelli]
    using
      patt_absoluteVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score
        (pattFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridgeOfGlivenkoCantelli
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
The GC-backed single-arm PATT absolute variance-estimate Wald route with the
estimated-score local expansion and Godambe obligations packaged as one
compact core.
-/
theorem
    patt_absoluteVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli_estimated_score_core
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
      EstimatedScoreStudentizationInput Index Sample LimitSample sampleLaw
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
    PATTFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput studentizationInput
        estimatedScoreToScaledTendsto coverageInput) :=
  patt_absoluteVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli
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
The PATT two-sided variance-estimate Wald conclusion used by the single-arm GC adapter.
It is stated through the equivalent absolute coverage record because the final
coverage event is the common Wald interval event.
-/
def PATTFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldConclusionOfGlivenkoCantelli
    (b :
      PATTFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l) :
    Prop :=
  PATTFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldConclusionOfGlivenkoCantelli
    ({ studentized_bridge := b.studentized_bridge
       coverage_input :=
        absoluteWaldCoverageVarianceInput_of_twoSided b.coverage_input } :
      PATTFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l)

/--
Build a PATT two-sided variance-estimate Wald bridge whose finite score-cell layer is
backed by a GC certificate on the LLN side.
-/
def pattFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldBridgeOfGlivenkoCantelli
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
      EstimatedScoreStudentizationInput Index Sample LimitSample sampleLaw
        limitLaw l)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution studentizationInput.scaledStatistic l
          studentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (coverageInput : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATTFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldBridge Cell Index Sample
      LimitSample sampleLaw limitLaw l where
  studentized_bridge :=
    pattFiniteScoreCellEstimatedScoreStudentizedBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput sampleLaw limitLaw l
      studentizationInput estimatedScoreToScaledTendsto
  coverage_input := coverageInput

/--
The GC-backed single-arm PATT route yields two-sided variance-estimate Wald coverage once the
finite-cell, known-score, estimated-score, studentization, and variance Wald coverage
obligations are supplied.
-/
theorem
    patt_twoSidedVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli
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
      EstimatedScoreStudentizationInput Index Sample LimitSample sampleLaw
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
    PATTFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldBridgeOfGlivenkoCantelli
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
    [PATTFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldConclusionOfGlivenkoCantelli,
      PATTFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldConclusionOfGlivenkoCantelli,
      pattFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldBridgeOfGlivenkoCantelli,
      absoluteWaldCoverageVarianceInput_of_twoSided]
    using
      patt_twoSidedVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score
        (pattFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldBridgeOfGlivenkoCantelli
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
The GC-backed single-arm PATT two-sided variance-estimate Wald route with the
estimated-score local expansion and Godambe obligations packaged as one
compact core.
-/
theorem
    patt_twoSidedVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli_estimated_score_core
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
      EstimatedScoreStudentizationInput Index Sample LimitSample sampleLaw
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
    PATTFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput studentizationInput
        estimatedScoreToScaledTendsto coverageInput) :=
  patt_twoSidedVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli
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
Convert a GC-backed PATE absolute variance-estimate Wald bridge into the corresponding two-sided
variance Wald bridge by calibrating the critical region.
-/
def PATEFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldBridgeOfAbsoluteCoverage
    (b :
      PATEFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l) :
    PATEFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldBridge Cell Index Sample
      LimitSample sampleLaw limitLaw l where
  studentized_bridge := b.studentized_bridge
  coverage_input := twoSidedWaldCoverageVarianceInput_of_absolute b.coverage_input

/--
Absolute-region PATE Wald calibration also yields the two-sided Wald
conclusion for the same GC-backed finite score-cell bridge.
-/
theorem
    pate_twoSidedVarianceWaldCoverage_tendsto_of_absolute_finite_score_cell_estimated_score_glivenkoCantelli
    (b :
      PATEFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l)
    (h :
      PATEFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldConclusionOfGlivenkoCantelli
        b) :
    PATEFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldConclusionOfGlivenkoCantelli
      (PATEFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldBridgeOfAbsoluteCoverage
        b) := by
  simpa
    [PATEFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldConclusionOfGlivenkoCantelli,
      PATEFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldConclusionOfGlivenkoCantelli,
      PATEFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldBridgeOfAbsoluteCoverage,
      twoSidedWaldCoverageVarianceInput_of_absolute,
      absoluteWaldCoverageVarianceInput_of_twoSided]
    using h

/--
Convert a GC-backed PATE two-sided variance-estimate Wald bridge into the corresponding absolute
variance Wald bridge by calibrating the critical region.
-/
def PATEFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridgeOfTwoSidedCoverage
    (b :
      PATEFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l) :
    PATEFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridge Cell Index Sample
      LimitSample sampleLaw limitLaw l where
  studentized_bridge := b.studentized_bridge
  coverage_input := absoluteWaldCoverageVarianceInput_of_twoSided b.coverage_input

/--
Two-sided PATE Wald calibration also yields the absolute Wald conclusion for
the same GC-backed finite score-cell bridge.
-/
theorem
    pate_absoluteVarianceWaldCoverage_tendsto_of_twoSided_finite_score_cell_estimated_score_glivenkoCantelli
    (b :
      PATEFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l)
    (h :
      PATEFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldConclusionOfGlivenkoCantelli
        b) :
    PATEFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldConclusionOfGlivenkoCantelli
      (PATEFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridgeOfTwoSidedCoverage
        b) := by
  simpa
    [PATEFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldConclusionOfGlivenkoCantelli,
      PATEFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridgeOfTwoSidedCoverage]
    using h

/--
Convert a GC-backed PATT absolute variance-estimate Wald bridge into the corresponding two-sided
variance Wald bridge by calibrating the critical region.
-/
def PATTFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldBridgeOfAbsoluteCoverage
    (b :
      PATTFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l) :
    PATTFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldBridge Cell Index Sample
      LimitSample sampleLaw limitLaw l where
  studentized_bridge := b.studentized_bridge
  coverage_input := twoSidedWaldCoverageVarianceInput_of_absolute b.coverage_input

/--
Absolute-region PATT Wald calibration also yields the two-sided Wald
conclusion for the same GC-backed finite score-cell bridge.
-/
theorem
    patt_twoSidedVarianceWaldCoverage_tendsto_of_absolute_finite_score_cell_estimated_score_glivenkoCantelli
    (b :
      PATTFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l)
    (h :
      PATTFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldConclusionOfGlivenkoCantelli
        b) :
    PATTFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldConclusionOfGlivenkoCantelli
      (PATTFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldBridgeOfAbsoluteCoverage
        b) := by
  simpa
    [PATTFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldConclusionOfGlivenkoCantelli,
      PATTFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldConclusionOfGlivenkoCantelli,
      PATTFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldBridgeOfAbsoluteCoverage,
      twoSidedWaldCoverageVarianceInput_of_absolute,
      absoluteWaldCoverageVarianceInput_of_twoSided]
    using h

/--
Convert a GC-backed PATT two-sided variance-estimate Wald bridge into the corresponding absolute
variance Wald bridge by calibrating the critical region.
-/
def PATTFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridgeOfTwoSidedCoverage
    (b :
      PATTFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l) :
    PATTFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridge Cell Index Sample
      LimitSample sampleLaw limitLaw l where
  studentized_bridge := b.studentized_bridge
  coverage_input := absoluteWaldCoverageVarianceInput_of_twoSided b.coverage_input

/--
Two-sided PATT Wald calibration also yields the absolute Wald conclusion for
the same GC-backed finite score-cell bridge.
-/
theorem
    patt_absoluteVarianceWaldCoverage_tendsto_of_twoSided_finite_score_cell_estimated_score_glivenkoCantelli
    (b :
      PATTFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l)
    (h :
      PATTFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldConclusionOfGlivenkoCantelli
        b) :
    PATTFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldConclusionOfGlivenkoCantelli
      (PATTFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridgeOfTwoSidedCoverage
        b) := by
  simpa
    [PATTFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldConclusionOfGlivenkoCantelli,
      PATTFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridgeOfTwoSidedCoverage]
    using h

/--
Attach the GC-backed score-cell mass LLN to an already derived PATE absolute
variance-estimate Wald conclusion.
-/
theorem pate_absoluteVarianceWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    {b :
      PATEFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATEFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldConclusionOfGlivenkoCantelli
        b) :
    PATEFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  ⟨hcoverage,
    cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells referenceShare sample weight score hgc⟩

/--
Attach the GC-backed score-cell mass LLN to an already derived PATE two-sided
variance-estimate Wald conclusion.
-/
theorem pate_twoSidedVarianceWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    {b :
      PATEFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATEFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldConclusionOfGlivenkoCantelli
        b) :
    PATEFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  ⟨hcoverage,
    cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells referenceShare sample weight score hgc⟩

/--
Attach the GC-backed score-cell mass LLN to an already derived PATT absolute
variance-estimate Wald conclusion.
-/
theorem patt_absoluteVarianceWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    {b :
      PATTFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATTFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldConclusionOfGlivenkoCantelli
        b) :
    PATTFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  ⟨hcoverage,
    cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells referenceShare sample weight score hgc⟩

/--
Attach the GC-backed score-cell mass LLN to an already derived PATT two-sided
variance-estimate Wald conclusion.
-/
theorem patt_twoSidedVarianceWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    {b :
      PATTFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATTFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldConclusionOfGlivenkoCantelli
        b) :
    PATTFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  ⟨hcoverage,
    cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells referenceShare sample weight score hgc⟩

theorem
    pate_absoluteVarianceWaldConclusion_and_mass_lln_of_l1BracketingNumber_obligations
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
      PATEFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATEFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldConclusionOfGlivenkoCantelli
        b) :
    PATEFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  pate_absoluteVarianceWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    cells referenceShare sample weight score
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      cells referenceShare sample weight score obligations)
    hcoverage

theorem
    pate_absoluteVarianceWaldConclusion_and_mass_lln_of_vdvw241_endpoint_assembly
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
      PATEFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATEFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldConclusionOfGlivenkoCantelli
        b) :
    PATEFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  pate_absoluteVarianceWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    cells referenceShare sample weight score
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      cells referenceShare sample weight score assembly)
    hcoverage

theorem
    pate_twoSidedVarianceWaldConclusion_and_mass_lln_of_l1BracketingNumber_obligations
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
      PATEFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATEFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldConclusionOfGlivenkoCantelli
        b) :
    PATEFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  pate_twoSidedVarianceWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    cells referenceShare sample weight score
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      cells referenceShare sample weight score obligations)
    hcoverage

theorem
    pate_twoSidedVarianceWaldConclusion_and_mass_lln_of_vdvw241_endpoint_assembly
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
      PATEFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATEFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldConclusionOfGlivenkoCantelli
        b) :
    PATEFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  pate_twoSidedVarianceWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    cells referenceShare sample weight score
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      cells referenceShare sample weight score assembly)
    hcoverage

theorem
    patt_absoluteVarianceWaldConclusion_and_mass_lln_of_l1BracketingNumber_obligations
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
      PATTFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATTFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldConclusionOfGlivenkoCantelli
        b) :
    PATTFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  patt_absoluteVarianceWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    cells referenceShare sample weight score
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      cells referenceShare sample weight score obligations)
    hcoverage

theorem
    patt_absoluteVarianceWaldConclusion_and_mass_lln_of_vdvw241_endpoint_assembly
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
      PATTFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATTFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldConclusionOfGlivenkoCantelli
        b) :
    PATTFiniteScoreCellEstimatedScoreAbsoluteVarianceWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  patt_absoluteVarianceWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    cells referenceShare sample weight score
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      cells referenceShare sample weight score assembly)
    hcoverage

theorem
    patt_twoSidedVarianceWaldConclusion_and_mass_lln_of_l1BracketingNumber_obligations
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
      PATTFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATTFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldConclusionOfGlivenkoCantelli
        b) :
    PATTFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  patt_twoSidedVarianceWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    cells referenceShare sample weight score
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      cells referenceShare sample weight score obligations)
    hcoverage

theorem
    patt_twoSidedVarianceWaldConclusion_and_mass_lln_of_vdvw241_endpoint_assembly
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
      PATTFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATTFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldConclusionOfGlivenkoCantelli
        b) :
    PATTFiniteScoreCellEstimatedScoreTwoSidedVarianceWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  patt_twoSidedVarianceWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    cells referenceShare sample weight score
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      cells referenceShare sample weight score assembly)
    hcoverage

end WDSM
end Matching
end StatInference
