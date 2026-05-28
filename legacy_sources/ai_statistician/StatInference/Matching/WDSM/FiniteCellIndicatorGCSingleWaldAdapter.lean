import StatInference.Matching.WDSM.FiniteCellIndicatorGCAdapter
import StatInference.Matching.WDSM.FiniteCellIndicatorEstimatedScoreWaldBridge
import StatInference.Matching.WDSM.WaldCriticalRegionCalibration

/-!
# GC adapter for single-arm plain Wald inference

This module connects the GC-backed single-arm finite score-cell
estimated-score studentized bridge to the single-arm plain Wald coverage layer.
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
The PATE absolute plain Wald conclusion used by the single-arm GC adapter.
-/
def PATEFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
    (b :
      PATEFiniteScoreCellEstimatedScoreAbsoluteWaldBridge Cell Index Sample
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
                  (b.coverage_input.standardError index sample)
                  (b.coverage_input.scale index)))
          l (nhds b.coverage_input.coverageLimit)

/--
Build a PATE absolute plain Wald bridge whose finite score-cell layer is backed
by a GC certificate on the LLN side.
-/
def pateFiniteScoreCellEstimatedScoreAbsoluteWaldBridgeOfGlivenkoCantelli
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
    (coverageInput : AbsoluteWaldCoverageInput Index Sample l) :
    PATEFiniteScoreCellEstimatedScoreAbsoluteWaldBridge Cell Index Sample
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
The GC-backed single-arm PATE route yields absolute Wald coverage once the
finite-cell, known-score, estimated-score, studentization, and Wald coverage
obligations are supplied.
-/
theorem
    pate_absoluteWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli
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
    (coverageInput : AbsoluteWaldCoverageInput Index Sample l)
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
    PATEFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreAbsoluteWaldBridgeOfGlivenkoCantelli
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
    [PATEFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli,
      pateFiniteScoreCellEstimatedScoreAbsoluteWaldBridgeOfGlivenkoCantelli]
    using
      pate_absoluteWaldCoverage_tendsto_of_finite_score_cell_estimated_score
        (pateFiniteScoreCellEstimatedScoreAbsoluteWaldBridgeOfGlivenkoCantelli
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
The GC-backed single-arm PATE absolute Wald route with the estimated-score
local expansion and Godambe obligations packaged as one compact core.
-/
theorem
    pate_absoluteWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli_estimated_score_core
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
    (coverageInput : AbsoluteWaldCoverageInput Index Sample l)
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
    PATEFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreAbsoluteWaldBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput studentizationInput
        estimatedScoreToScaledTendsto coverageInput) :=
  pate_absoluteWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli
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
The PATE two-sided plain Wald conclusion used by the single-arm GC adapter.
It is stated through the equivalent absolute coverage record because the final
coverage event is the common Wald interval event.
-/
def PATEFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli
    (b :
      PATEFiniteScoreCellEstimatedScoreTwoSidedWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l) :
    Prop :=
  PATEFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
    ({ studentized_bridge := b.studentized_bridge
       coverage_input :=
        absoluteWaldCoverageInput_of_twoSided b.coverage_input } :
      PATEFiniteScoreCellEstimatedScoreAbsoluteWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l)

/--
Build a PATE two-sided plain Wald bridge whose finite score-cell layer is
backed by a GC certificate on the LLN side.
-/
def pateFiniteScoreCellEstimatedScoreTwoSidedWaldBridgeOfGlivenkoCantelli
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
    (coverageInput : TwoSidedWaldCoverageInput Index Sample l) :
    PATEFiniteScoreCellEstimatedScoreTwoSidedWaldBridge Cell Index Sample
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
The GC-backed single-arm PATE route yields two-sided Wald coverage once the
finite-cell, known-score, estimated-score, studentization, and Wald coverage
obligations are supplied.
-/
theorem
    pate_twoSidedWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli
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
    (coverageInput : TwoSidedWaldCoverageInput Index Sample l)
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
    PATEFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreTwoSidedWaldBridgeOfGlivenkoCantelli
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
    [PATEFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli,
      PATEFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli,
      pateFiniteScoreCellEstimatedScoreTwoSidedWaldBridgeOfGlivenkoCantelli,
      absoluteWaldCoverageInput_of_twoSided]
    using
      pate_twoSidedWaldCoverage_tendsto_of_finite_score_cell_estimated_score
        (pateFiniteScoreCellEstimatedScoreTwoSidedWaldBridgeOfGlivenkoCantelli
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
The GC-backed single-arm PATE two-sided Wald route with the estimated-score
local expansion and Godambe obligations packaged as one compact core.
-/
theorem
    pate_twoSidedWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli_estimated_score_core
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
    (coverageInput : TwoSidedWaldCoverageInput Index Sample l)
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
    PATEFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreTwoSidedWaldBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput studentizationInput
        estimatedScoreToScaledTendsto coverageInput) :=
  pate_twoSidedWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli
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
The PATT absolute plain Wald conclusion used by the single-arm GC adapter.
-/
def PATTFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
    (b :
      PATTFiniteScoreCellEstimatedScoreAbsoluteWaldBridge Cell Index Sample
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
                  (b.coverage_input.standardError index sample)
                  (b.coverage_input.scale index)))
          l (nhds b.coverage_input.coverageLimit)

/--
Build a PATT absolute plain Wald bridge whose finite score-cell layer is backed
by a GC certificate on the LLN side.
-/
def pattFiniteScoreCellEstimatedScoreAbsoluteWaldBridgeOfGlivenkoCantelli
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
    (coverageInput : AbsoluteWaldCoverageInput Index Sample l) :
    PATTFiniteScoreCellEstimatedScoreAbsoluteWaldBridge Cell Index Sample
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
The GC-backed single-arm PATT route yields absolute Wald coverage once the
finite-cell, known-score, estimated-score, studentization, and Wald coverage
obligations are supplied.
-/
theorem
    patt_absoluteWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli
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
    (coverageInput : AbsoluteWaldCoverageInput Index Sample l)
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
    PATTFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreAbsoluteWaldBridgeOfGlivenkoCantelli
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
    [PATTFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli,
      pattFiniteScoreCellEstimatedScoreAbsoluteWaldBridgeOfGlivenkoCantelli]
    using
      patt_absoluteWaldCoverage_tendsto_of_finite_score_cell_estimated_score
        (pattFiniteScoreCellEstimatedScoreAbsoluteWaldBridgeOfGlivenkoCantelli
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
The GC-backed single-arm PATT absolute Wald route with the estimated-score
local expansion and Godambe obligations packaged as one compact core.
-/
theorem
    patt_absoluteWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli_estimated_score_core
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
    (coverageInput : AbsoluteWaldCoverageInput Index Sample l)
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
    PATTFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreAbsoluteWaldBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput studentizationInput
        estimatedScoreToScaledTendsto coverageInput) :=
  patt_absoluteWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli
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
The PATT two-sided plain Wald conclusion used by the single-arm GC adapter.
It is stated through the equivalent absolute coverage record because the final
coverage event is the common Wald interval event.
-/
def PATTFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli
    (b :
      PATTFiniteScoreCellEstimatedScoreTwoSidedWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l) :
    Prop :=
  PATTFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
    ({ studentized_bridge := b.studentized_bridge
       coverage_input :=
        absoluteWaldCoverageInput_of_twoSided b.coverage_input } :
      PATTFiniteScoreCellEstimatedScoreAbsoluteWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l)

/--
Build a PATT two-sided plain Wald bridge whose finite score-cell layer is
backed by a GC certificate on the LLN side.
-/
def pattFiniteScoreCellEstimatedScoreTwoSidedWaldBridgeOfGlivenkoCantelli
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
    (coverageInput : TwoSidedWaldCoverageInput Index Sample l) :
    PATTFiniteScoreCellEstimatedScoreTwoSidedWaldBridge Cell Index Sample
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
The GC-backed single-arm PATT route yields two-sided Wald coverage once the
finite-cell, known-score, estimated-score, studentization, and Wald coverage
obligations are supplied.
-/
theorem
    patt_twoSidedWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli
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
    (coverageInput : TwoSidedWaldCoverageInput Index Sample l)
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
    PATTFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreTwoSidedWaldBridgeOfGlivenkoCantelli
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
    [PATTFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli,
      PATTFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli,
      pattFiniteScoreCellEstimatedScoreTwoSidedWaldBridgeOfGlivenkoCantelli,
      absoluteWaldCoverageInput_of_twoSided]
    using
      patt_twoSidedWaldCoverage_tendsto_of_finite_score_cell_estimated_score
        (pattFiniteScoreCellEstimatedScoreTwoSidedWaldBridgeOfGlivenkoCantelli
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
The GC-backed single-arm PATT two-sided Wald route with the estimated-score
local expansion and Godambe obligations packaged as one compact core.
-/
theorem
    patt_twoSidedWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli_estimated_score_core
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
    (coverageInput : TwoSidedWaldCoverageInput Index Sample l)
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
    PATTFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreTwoSidedWaldBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput studentizationInput
        estimatedScoreToScaledTendsto coverageInput) :=
  patt_twoSidedWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli
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
Convert a GC-backed PATE absolute Wald bridge into the corresponding two-sided
Wald bridge by calibrating the critical region.
-/
def PATEFiniteScoreCellEstimatedScoreTwoSidedWaldBridgeOfAbsoluteCoverage
    (b :
      PATEFiniteScoreCellEstimatedScoreAbsoluteWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l) :
    PATEFiniteScoreCellEstimatedScoreTwoSidedWaldBridge Cell Index Sample
      LimitSample sampleLaw limitLaw l where
  studentized_bridge := b.studentized_bridge
  coverage_input := twoSidedWaldCoverageInput_of_absolute b.coverage_input

/--
Absolute-region PATE Wald calibration also yields the two-sided Wald
conclusion for the same GC-backed finite score-cell bridge.
-/
theorem
    pate_twoSidedWaldCoverage_tendsto_of_absolute_finite_score_cell_estimated_score_glivenkoCantelli
    (b :
      PATEFiniteScoreCellEstimatedScoreAbsoluteWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l)
    (h :
      PATEFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
        b) :
    PATEFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli
      (PATEFiniteScoreCellEstimatedScoreTwoSidedWaldBridgeOfAbsoluteCoverage
        b) := by
  simpa
    [PATEFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli,
      PATEFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli,
      PATEFiniteScoreCellEstimatedScoreTwoSidedWaldBridgeOfAbsoluteCoverage,
      twoSidedWaldCoverageInput_of_absolute,
      absoluteWaldCoverageInput_of_twoSided]
    using h

/--
Convert a GC-backed PATE two-sided Wald bridge into the corresponding absolute
Wald bridge by calibrating the critical region.
-/
def PATEFiniteScoreCellEstimatedScoreAbsoluteWaldBridgeOfTwoSidedCoverage
    (b :
      PATEFiniteScoreCellEstimatedScoreTwoSidedWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l) :
    PATEFiniteScoreCellEstimatedScoreAbsoluteWaldBridge Cell Index Sample
      LimitSample sampleLaw limitLaw l where
  studentized_bridge := b.studentized_bridge
  coverage_input := absoluteWaldCoverageInput_of_twoSided b.coverage_input

/--
Two-sided PATE Wald calibration also yields the absolute Wald conclusion for
the same GC-backed finite score-cell bridge.
-/
theorem
    pate_absoluteWaldCoverage_tendsto_of_twoSided_finite_score_cell_estimated_score_glivenkoCantelli
    (b :
      PATEFiniteScoreCellEstimatedScoreTwoSidedWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l)
    (h :
      PATEFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli
        b) :
    PATEFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
      (PATEFiniteScoreCellEstimatedScoreAbsoluteWaldBridgeOfTwoSidedCoverage
        b) := by
  simpa
    [PATEFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli,
      PATEFiniteScoreCellEstimatedScoreAbsoluteWaldBridgeOfTwoSidedCoverage]
    using h

/--
Convert a GC-backed PATT absolute Wald bridge into the corresponding two-sided
Wald bridge by calibrating the critical region.
-/
def PATTFiniteScoreCellEstimatedScoreTwoSidedWaldBridgeOfAbsoluteCoverage
    (b :
      PATTFiniteScoreCellEstimatedScoreAbsoluteWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l) :
    PATTFiniteScoreCellEstimatedScoreTwoSidedWaldBridge Cell Index Sample
      LimitSample sampleLaw limitLaw l where
  studentized_bridge := b.studentized_bridge
  coverage_input := twoSidedWaldCoverageInput_of_absolute b.coverage_input

/--
Absolute-region PATT Wald calibration also yields the two-sided Wald
conclusion for the same GC-backed finite score-cell bridge.
-/
theorem
    patt_twoSidedWaldCoverage_tendsto_of_absolute_finite_score_cell_estimated_score_glivenkoCantelli
    (b :
      PATTFiniteScoreCellEstimatedScoreAbsoluteWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l)
    (h :
      PATTFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
        b) :
    PATTFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli
      (PATTFiniteScoreCellEstimatedScoreTwoSidedWaldBridgeOfAbsoluteCoverage
        b) := by
  simpa
    [PATTFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli,
      PATTFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli,
      PATTFiniteScoreCellEstimatedScoreTwoSidedWaldBridgeOfAbsoluteCoverage,
      twoSidedWaldCoverageInput_of_absolute,
      absoluteWaldCoverageInput_of_twoSided]
    using h

/--
Convert a GC-backed PATT two-sided Wald bridge into the corresponding absolute
Wald bridge by calibrating the critical region.
-/
def PATTFiniteScoreCellEstimatedScoreAbsoluteWaldBridgeOfTwoSidedCoverage
    (b :
      PATTFiniteScoreCellEstimatedScoreTwoSidedWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l) :
    PATTFiniteScoreCellEstimatedScoreAbsoluteWaldBridge Cell Index Sample
      LimitSample sampleLaw limitLaw l where
  studentized_bridge := b.studentized_bridge
  coverage_input := absoluteWaldCoverageInput_of_twoSided b.coverage_input

/--
Two-sided PATT Wald calibration also yields the absolute Wald conclusion for
the same GC-backed finite score-cell bridge.
-/
theorem
    patt_absoluteWaldCoverage_tendsto_of_twoSided_finite_score_cell_estimated_score_glivenkoCantelli
    (b :
      PATTFiniteScoreCellEstimatedScoreTwoSidedWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l)
    (h :
      PATTFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli
        b) :
    PATTFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
      (PATTFiniteScoreCellEstimatedScoreAbsoluteWaldBridgeOfTwoSidedCoverage
        b) := by
  simpa
    [PATTFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli,
      PATTFiniteScoreCellEstimatedScoreAbsoluteWaldBridgeOfTwoSidedCoverage]
    using h

/--
Attach the GC-backed score-cell mass LLN to an already derived PATE absolute
plain Wald conclusion.
-/
theorem pate_absoluteWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    {b :
      PATEFiniteScoreCellEstimatedScoreAbsoluteWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATEFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
        b) :
    PATEFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  ⟨hcoverage,
    cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells referenceShare sample weight score hgc⟩

/--
Attach the GC-backed score-cell mass LLN to an already derived PATE two-sided
plain Wald conclusion.
-/
theorem pate_twoSidedWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    {b :
      PATEFiniteScoreCellEstimatedScoreTwoSidedWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATEFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli
        b) :
    PATEFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  ⟨hcoverage,
    cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells referenceShare sample weight score hgc⟩

/--
Attach the GC-backed score-cell mass LLN to an already derived PATT absolute
plain Wald conclusion.
-/
theorem patt_absoluteWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    {b :
      PATTFiniteScoreCellEstimatedScoreAbsoluteWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATTFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
        b) :
    PATTFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  ⟨hcoverage,
    cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells referenceShare sample weight score hgc⟩

/--
Attach the GC-backed score-cell mass LLN to an already derived PATT two-sided
plain Wald conclusion.
-/
theorem patt_twoSidedWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    (cells : Finset Cell)
    (referenceShare : Cell -> Real)
    (sample : ℕ -> Finset Unit)
    (weight : ℕ -> Unit -> Real)
    (score : ℕ -> Unit -> Cell)
    (hgc :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        cells referenceShare sample weight score).weighted_indicator_array_lln)
    {b :
      PATTFiniteScoreCellEstimatedScoreTwoSidedWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATTFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli
        b) :
    PATTFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  ⟨hcoverage,
    cellwise_mass_lln_of_glivenkoCantelli_bridge
      cells referenceShare sample weight score hgc⟩

theorem pate_absoluteWaldConclusion_and_mass_lln_of_l1BracketingNumber_obligations
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
      PATEFiniteScoreCellEstimatedScoreAbsoluteWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATEFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
        b) :
    PATEFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  pate_absoluteWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    cells referenceShare sample weight score
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      cells referenceShare sample weight score obligations)
    hcoverage

theorem pate_absoluteWaldConclusion_and_mass_lln_of_vdvw241_endpoint_assembly
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
      PATEFiniteScoreCellEstimatedScoreAbsoluteWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATEFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
        b) :
    PATEFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  pate_absoluteWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    cells referenceShare sample weight score
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      cells referenceShare sample weight score assembly)
    hcoverage

theorem pate_twoSidedWaldConclusion_and_mass_lln_of_l1BracketingNumber_obligations
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
      PATEFiniteScoreCellEstimatedScoreTwoSidedWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATEFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli
        b) :
    PATEFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  pate_twoSidedWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    cells referenceShare sample weight score
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      cells referenceShare sample weight score obligations)
    hcoverage

theorem pate_twoSidedWaldConclusion_and_mass_lln_of_vdvw241_endpoint_assembly
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
      PATEFiniteScoreCellEstimatedScoreTwoSidedWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATEFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli
        b) :
    PATEFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  pate_twoSidedWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    cells referenceShare sample weight score
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      cells referenceShare sample weight score assembly)
    hcoverage

theorem patt_absoluteWaldConclusion_and_mass_lln_of_l1BracketingNumber_obligations
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
      PATTFiniteScoreCellEstimatedScoreAbsoluteWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATTFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
        b) :
    PATTFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  patt_absoluteWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    cells referenceShare sample weight score
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      cells referenceShare sample weight score obligations)
    hcoverage

theorem patt_absoluteWaldConclusion_and_mass_lln_of_vdvw241_endpoint_assembly
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
      PATTFiniteScoreCellEstimatedScoreAbsoluteWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATTFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
        b) :
    PATTFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  patt_absoluteWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    cells referenceShare sample weight score
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      cells referenceShare sample weight score assembly)
    hcoverage

theorem patt_twoSidedWaldConclusion_and_mass_lln_of_l1BracketingNumber_obligations
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
      PATTFiniteScoreCellEstimatedScoreTwoSidedWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATTFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli
        b) :
    PATTFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  patt_twoSidedWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    cells referenceShare sample weight score
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      cells referenceShare sample weight score obligations)
    hcoverage

theorem patt_twoSidedWaldConclusion_and_mass_lln_of_vdvw241_endpoint_assembly
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
      PATTFiniteScoreCellEstimatedScoreTwoSidedWaldBridge Cell Index Sample
        LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATTFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli
        b) :
    PATTFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) cells sample weight score
        referenceShare :=
  patt_twoSidedWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    cells referenceShare sample weight score
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      cells referenceShare sample weight score assembly)
    hcoverage

end WDSM
end Matching
end StatInference
