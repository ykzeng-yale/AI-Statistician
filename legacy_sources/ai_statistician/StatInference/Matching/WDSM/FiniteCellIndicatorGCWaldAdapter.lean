import StatInference.Matching.WDSM.FiniteCellIndicatorGCAdapter
import StatInference.Matching.WDSM.FiniteCellIndicatorPairedEstimatedScoreWaldBridge
import StatInference.Matching.WDSM.WaldCriticalRegionCalibration

/-!
# GC adapter for paired plain Wald inference

This module connects the GC-backed finite score-cell estimated-score
plain studentized bridge to the paired plain Wald
coverage layer.
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

/--
The paired absolute plain Wald conclusion used by the GC adapter.
-/
def PATEPATTFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
    (b :
      PATEPATTFiniteScoreCellEstimatedScoreAbsoluteWaldBridge
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
      l (nhds b.patt_coverage_input.coverageLimit)

/--
Build a paired absolute plain Wald bridge whose finite score-cell
layer is backed by GC certificates on the LLN side.
-/
def
    patePattFiniteScoreCellEstimatedScoreAbsoluteWaldBridgeOfGlivenkoCantelli
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pateKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pattKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pateScaledApproximationToMatchingDiscrepancy :
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        pateKnownScoreBridge.matching_discrepancy_negligible)
    (pattScaledApproximationToMatchingDiscrepancy :
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        pattKnownScoreBridge.matching_discrepancy_negligible)
    (pateEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pattEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pateKnownScoreToEstimatedScoreInput :
      pateKnownScoreBridge.asymptotic_normality ->
        pateEstimatedScoreBridge.known_score_asymptotic_normality)
    (pattKnownScoreToEstimatedScoreInput :
      pattKnownScoreBridge.asymptotic_normality ->
        pattEstimatedScoreBridge.known_score_asymptotic_normality)
    (pateStudentizationInput :
      EstimatedScoreStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (pattStudentizationInput :
      EstimatedScoreStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pateStudentizationInput.scaledStatistic l
          pateStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pattStudentizationInput.scaledStatistic l
          pattStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (pateCoverageInput : AbsoluteWaldCoverageInput Index Sample l)
    (pattCoverageInput : AbsoluteWaldCoverageInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsoluteWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l where
  studentized_bridge :=
    patePattFiniteScoreCellEstimatedScoreStudentizedBridgeOfGlivenkoCantelli
      pateCells pateReferenceShare pateSample pateWeight pateScore
      pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
      pateFiniteConditionsToScaled pateEnvelopeToScaled
      pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
      pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
      pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
      pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
      pateScaledApproximationToMatchingDiscrepancy
      pattScaledApproximationToMatchingDiscrepancy pateEstimatedScoreBridge
      pattEstimatedScoreBridge pateKnownScoreToEstimatedScoreInput
      pattKnownScoreToEstimatedScoreInput sampleLaw limitLaw l
      pateStudentizationInput pattStudentizationInput
      pateEstimatedScoreToScaledTendsto pattEstimatedScoreToScaledTendsto
  pate_coverage_input := pateCoverageInput
  patt_coverage_input := pattCoverageInput

/--
The GC-backed plain studentized route yields paired absolute Wald
coverage once the finite-cell, known-score, estimated-score, studentization,
and Wald coverage obligations are supplied.
-/
theorem
    pate_patt_absoluteWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pateKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pattKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pateScaledApproximationToMatchingDiscrepancy :
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        pateKnownScoreBridge.matching_discrepancy_negligible)
    (pattScaledApproximationToMatchingDiscrepancy :
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        pattKnownScoreBridge.matching_discrepancy_negligible)
    (pateEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pattEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pateKnownScoreToEstimatedScoreInput :
      pateKnownScoreBridge.asymptotic_normality ->
        pateEstimatedScoreBridge.known_score_asymptotic_normality)
    (pattKnownScoreToEstimatedScoreInput :
      pattKnownScoreBridge.asymptotic_normality ->
        pattEstimatedScoreBridge.known_score_asymptotic_normality)
    (pateStudentizationInput :
      EstimatedScoreStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (pattStudentizationInput :
      EstimatedScoreStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pateStudentizationInput.scaledStatistic l
          pateStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pattStudentizationInput.scaledStatistic l
          pattStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (pateCoverageInput : AbsoluteWaldCoverageInput Index Sample l)
    (pattCoverageInput : AbsoluteWaldCoverageInput Index Sample l)
    (hpateGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).weighted_indicator_array_lln)
    (hpateFinite : pateIndicatorBridge.eventual_finite_conditions)
    (hpateEnvelope : pateIndicatorBridge.envelope_convergence)
    (hpateSimplex : pateCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpateLinear :
      pateCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpateMatrix :
      pateCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpattGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).weighted_indicator_array_lln)
    (hpattFinite : pattIndicatorBridge.eventual_finite_conditions)
    (hpattEnvelope : pattIndicatorBridge.envelope_convergence)
    (hpattSimplex : pattCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpattLinear :
      pattCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpattMatrix :
      pattCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpateDecomp : pateKnownScoreBridge.aggregate_hajek_decomposition)
    (hpateDenominator : pateKnownScoreBridge.denominator_stabilization)
    (hpateHeterogeneity : pateKnownScoreBridge.heterogeneity_clt)
    (hpateResidual : pateKnownScoreBridge.residual_clt)
    (hpattDecomp : pattKnownScoreBridge.aggregate_hajek_decomposition)
    (hpattDenominator : pattKnownScoreBridge.denominator_stabilization)
    (hpattHeterogeneity : pattKnownScoreBridge.heterogeneity_clt)
    (hpattResidual : pattKnownScoreBridge.residual_clt)
    (hpateFirst :
      pateEstimatedScoreBridge.first_step_asymptotic_linearization)
    (hpateLocal :
      pateEstimatedScoreBridge.matching_functional_local_expansion)
    (hpateGodambe : pateEstimatedScoreBridge.godambe_variance_identity)
    (hpattFirst :
      pattEstimatedScoreBridge.first_step_asymptotic_linearization)
    (hpattLocal :
      pattEstimatedScoreBridge.matching_functional_local_expansion)
    (hpattGodambe : pattEstimatedScoreBridge.godambe_variance_identity) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
      (patePattFiniteScoreCellEstimatedScoreAbsoluteWaldBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight pateScore
        pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
        pateFiniteConditionsToScaled pateEnvelopeToScaled
        pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
        pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
        pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
        pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
        pateScaledApproximationToMatchingDiscrepancy
        pattScaledApproximationToMatchingDiscrepancy pateEstimatedScoreBridge
        pattEstimatedScoreBridge pateKnownScoreToEstimatedScoreInput
        pattKnownScoreToEstimatedScoreInput pateStudentizationInput
        pattStudentizationInput pateEstimatedScoreToScaledTendsto
        pattEstimatedScoreToScaledTendsto pateCoverageInput
        pattCoverageInput) := by
  have hpateDesign :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).survey_design_regularity := by
    simpa [finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli] using hpateGC
  have hpattDesign :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).survey_design_regularity := by
    simpa [finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli] using hpattGC
  simpa
    [PATEPATTFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli,
      patePattFiniteScoreCellEstimatedScoreAbsoluteWaldBridgeOfGlivenkoCantelli]
    using
      pate_patt_absoluteWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score
        (patePattFiniteScoreCellEstimatedScoreAbsoluteWaldBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy pateEstimatedScoreBridge
          pattEstimatedScoreBridge pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput pateStudentizationInput
          pattStudentizationInput pateEstimatedScoreToScaledTendsto
          pattEstimatedScoreToScaledTendsto pateCoverageInput
          pattCoverageInput)
        hpateDesign
        (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
          pateCells pateReferenceShare pateSample pateWeight pateScore)
        hpateGC hpateFinite hpateEnvelope hpateSimplex hpateLinear hpateMatrix
        hpattDesign
        (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
          pattCells pattReferenceShare pattSample pattWeight pattScore)
        hpattGC hpattFinite hpattEnvelope hpattSimplex hpattLinear hpattMatrix
        hpateDecomp hpateDenominator hpateHeterogeneity hpateResidual
        hpattDecomp hpattDenominator hpattHeterogeneity hpattResidual
        hpateFirst hpateLocal hpateGodambe hpattFirst hpattLocal hpattGodambe

/--
The paired GC-backed absolute ordinary Wald route with the PATE and PATT local
expansion/Godambe obligations packaged as compact estimated-score cores.
-/
theorem
    pate_patt_absoluteWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli_estimated_score_core
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pateKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pattKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pateScaledApproximationToMatchingDiscrepancy :
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        pateKnownScoreBridge.matching_discrepancy_negligible)
    (pattScaledApproximationToMatchingDiscrepancy :
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        pattKnownScoreBridge.matching_discrepancy_negligible)
    (pateEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pattEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pateCore : EstimatedScoreAsymptoticBridgeCore pateEstimatedScoreBridge)
    (pattCore : EstimatedScoreAsymptoticBridgeCore pattEstimatedScoreBridge)
    (pateKnownScoreToEstimatedScoreInput :
      pateKnownScoreBridge.asymptotic_normality ->
        pateEstimatedScoreBridge.known_score_asymptotic_normality)
    (pattKnownScoreToEstimatedScoreInput :
      pattKnownScoreBridge.asymptotic_normality ->
        pattEstimatedScoreBridge.known_score_asymptotic_normality)
    (pateStudentizationInput :
      EstimatedScoreStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (pattStudentizationInput :
      EstimatedScoreStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pateStudentizationInput.scaledStatistic l
          pateStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pattStudentizationInput.scaledStatistic l
          pattStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (pateCoverageInput : AbsoluteWaldCoverageInput Index Sample l)
    (pattCoverageInput : AbsoluteWaldCoverageInput Index Sample l)
    (hpateGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).weighted_indicator_array_lln)
    (hpateFinite : pateIndicatorBridge.eventual_finite_conditions)
    (hpateEnvelope : pateIndicatorBridge.envelope_convergence)
    (hpateSimplex : pateCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpateLinear :
      pateCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpateMatrix :
      pateCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpattGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).weighted_indicator_array_lln)
    (hpattFinite : pattIndicatorBridge.eventual_finite_conditions)
    (hpattEnvelope : pattIndicatorBridge.envelope_convergence)
    (hpattSimplex : pattCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpattLinear :
      pattCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpattMatrix :
      pattCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpateDecomp : pateKnownScoreBridge.aggregate_hajek_decomposition)
    (hpateDenominator : pateKnownScoreBridge.denominator_stabilization)
    (hpateHeterogeneity : pateKnownScoreBridge.heterogeneity_clt)
    (hpateResidual : pateKnownScoreBridge.residual_clt)
    (hpattDecomp : pattKnownScoreBridge.aggregate_hajek_decomposition)
    (hpattDenominator : pattKnownScoreBridge.denominator_stabilization)
    (hpattHeterogeneity : pattKnownScoreBridge.heterogeneity_clt)
    (hpattResidual : pattKnownScoreBridge.residual_clt)
    (hpateFirst :
      pateEstimatedScoreBridge.first_step_asymptotic_linearization)
    (hpattFirst :
      pattEstimatedScoreBridge.first_step_asymptotic_linearization) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
      (patePattFiniteScoreCellEstimatedScoreAbsoluteWaldBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight pateScore
        pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
        pateFiniteConditionsToScaled pateEnvelopeToScaled
        pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
        pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
        pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
        pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
        pateScaledApproximationToMatchingDiscrepancy
        pattScaledApproximationToMatchingDiscrepancy pateEstimatedScoreBridge
        pattEstimatedScoreBridge pateKnownScoreToEstimatedScoreInput
        pattKnownScoreToEstimatedScoreInput pateStudentizationInput
        pattStudentizationInput pateEstimatedScoreToScaledTendsto
        pattEstimatedScoreToScaledTendsto pateCoverageInput
        pattCoverageInput) :=
  pate_patt_absoluteWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli
    pateCells pateReferenceShare pateSample pateWeight pateScore
    pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
    pateFiniteConditionsToScaled pateEnvelopeToScaled pateIndicatorLLNToScaled
    pattCells pattReferenceShare pattSample pattWeight pattScore
    pattIndicatorBridge pattFiniteLLNToIndicatorLLN pattCLTBridge
    pattFiniteConditionsToScaled pattEnvelopeToScaled pattIndicatorLLNToScaled
    pateKnownScoreBridge pattKnownScoreBridge
    pateScaledApproximationToMatchingDiscrepancy
    pattScaledApproximationToMatchingDiscrepancy pateEstimatedScoreBridge
    pattEstimatedScoreBridge pateKnownScoreToEstimatedScoreInput
    pattKnownScoreToEstimatedScoreInput pateStudentizationInput
    pattStudentizationInput pateEstimatedScoreToScaledTendsto
    pattEstimatedScoreToScaledTendsto pateCoverageInput pattCoverageInput
    hpateGC hpateFinite hpateEnvelope hpateSimplex hpateLinear hpateMatrix
    hpattGC hpattFinite hpattEnvelope hpattSimplex hpattLinear hpattMatrix
    hpateDecomp hpateDenominator hpateHeterogeneity hpateResidual
    hpattDecomp hpattDenominator hpattHeterogeneity hpattResidual
    hpateFirst pateCore.matching_functional_local_expansion
    pateCore.godambe_variance_identity hpattFirst
    pattCore.matching_functional_local_expansion
    pattCore.godambe_variance_identity

/--
The paired GC-backed absolute plain Wald route with the PATE and PATT local
experiment obligations packaged as compact local-experiment cores.
-/
theorem
    pate_patt_absoluteWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli_local_experiment_core
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pateKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pattKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pateScaledApproximationToMatchingDiscrepancy :
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        pateKnownScoreBridge.matching_discrepancy_negligible)
    (pattScaledApproximationToMatchingDiscrepancy :
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        pattKnownScoreBridge.matching_discrepancy_negligible)
(pateEstimated : EstimatedScoreLocalExperimentInput)
(pattEstimated : EstimatedScoreLocalExperimentInput)
(pateCore : EstimatedScoreLocalExperimentCore pateEstimated)
(pattCore : EstimatedScoreLocalExperimentCore pattEstimated)
    (pateKnownScoreToEstimatedScoreInput :
      pateKnownScoreBridge.asymptotic_normality ->
        pateEstimated.known_score_asymptotic_normality)
    (pattKnownScoreToEstimatedScoreInput :
      pattKnownScoreBridge.asymptotic_normality ->
        pattEstimated.known_score_asymptotic_normality)
    (pateStudentizationInput :
      EstimatedScoreStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (pattStudentizationInput :
      EstimatedScoreStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution pateStudentizationInput.scaledStatistic l
          pateStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution pattStudentizationInput.scaledStatistic l
          pattStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (pateCoverageInput : AbsoluteWaldCoverageInput Index Sample l)
    (pattCoverageInput : AbsoluteWaldCoverageInput Index Sample l)
    (hpateGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).weighted_indicator_array_lln)
    (hpateFinite : pateIndicatorBridge.eventual_finite_conditions)
    (hpateEnvelope : pateIndicatorBridge.envelope_convergence)
    (hpateSimplex : pateCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpateLinear :
      pateCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpateMatrix :
      pateCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpattGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).weighted_indicator_array_lln)
    (hpattFinite : pattIndicatorBridge.eventual_finite_conditions)
    (hpattEnvelope : pattIndicatorBridge.envelope_convergence)
    (hpattSimplex : pattCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpattLinear :
      pattCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpattMatrix :
      pattCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpateDecomp : pateKnownScoreBridge.aggregate_hajek_decomposition)
    (hpateDenominator : pateKnownScoreBridge.denominator_stabilization)
    (hpateHeterogeneity : pateKnownScoreBridge.heterogeneity_clt)
    (hpateResidual : pateKnownScoreBridge.residual_clt)
    (hpattDecomp : pattKnownScoreBridge.aggregate_hajek_decomposition)
    (hpattDenominator : pattKnownScoreBridge.denominator_stabilization)
    (hpattHeterogeneity : pattKnownScoreBridge.heterogeneity_clt)
    (hpattResidual : pattKnownScoreBridge.residual_clt)
    (hpateFirst :
      pateEstimated.first_step_asymptotic_linearization)
    (hpateScore :
      pateEstimated.score_estimator_local_asymptotic_linearity)
    (hpattFirst :
      pattEstimated.first_step_asymptotic_linearization)
    (hpattScore :
      pattEstimated.score_estimator_local_asymptotic_linearity) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
      (patePattFiniteScoreCellEstimatedScoreAbsoluteWaldBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight pateScore
        pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
        pateFiniteConditionsToScaled pateEnvelopeToScaled
        pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
        pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
        pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
        pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
        pateScaledApproximationToMatchingDiscrepancy
        pattScaledApproximationToMatchingDiscrepancy (estimatedScoreAsymptoticBridgeOfLocalExperimentInput pateEstimated)
        (estimatedScoreAsymptoticBridgeOfLocalExperimentInput pattEstimated) pateKnownScoreToEstimatedScoreInput
        pattKnownScoreToEstimatedScoreInput pateStudentizationInput
        pattStudentizationInput pateEstimatedScoreToScaledTendsto
        pattEstimatedScoreToScaledTendsto pateCoverageInput
        pattCoverageInput) :=
  pate_patt_absoluteWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli
    pateCells pateReferenceShare pateSample pateWeight pateScore
    pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
    pateFiniteConditionsToScaled pateEnvelopeToScaled pateIndicatorLLNToScaled
    pattCells pattReferenceShare pattSample pattWeight pattScore
    pattIndicatorBridge pattFiniteLLNToIndicatorLLN pattCLTBridge
    pattFiniteConditionsToScaled pattEnvelopeToScaled pattIndicatorLLNToScaled
    pateKnownScoreBridge pattKnownScoreBridge
    pateScaledApproximationToMatchingDiscrepancy
    pattScaledApproximationToMatchingDiscrepancy (estimatedScoreAsymptoticBridgeOfLocalExperimentInput pateEstimated)
    (estimatedScoreAsymptoticBridgeOfLocalExperimentInput pattEstimated) pateKnownScoreToEstimatedScoreInput
    pattKnownScoreToEstimatedScoreInput pateStudentizationInput
    pattStudentizationInput pateEstimatedScoreToScaledTendsto
    pattEstimatedScoreToScaledTendsto pateCoverageInput pattCoverageInput
    hpateGC hpateFinite hpateEnvelope hpateSimplex hpateLinear hpateMatrix
    hpattGC hpattFinite hpattEnvelope hpattSimplex hpattLinear hpattMatrix
    hpateDecomp hpateDenominator hpateHeterogeneity hpateResidual
    hpattDecomp hpattDenominator hpattHeterogeneity hpattResidual
    hpateFirst
    ⟨hpateScore, pateCore.matching_functional_local_derivative,
      pateCore.local_stochastic_equicontinuity⟩
    pateCore.godambe_variance_identity hpattFirst
    ⟨hpattScore, pattCore.matching_functional_local_derivative,
      pattCore.local_stochastic_equicontinuity⟩
    pattCore.godambe_variance_identity


/--
The paired two-sided plain Wald conclusion used by the GC adapter.
It is stated through the equivalent absolute coverage record because the final
coverage event is the common Wald interval event.
-/
def PATEPATTFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli
    (b :
      PATEPATTFiniteScoreCellEstimatedScoreTwoSidedWaldBridge
        PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l) :
    Prop :=
  PATEPATTFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
    ({ studentized_bridge := b.studentized_bridge
       pate_coverage_input :=
        absoluteWaldCoverageInput_of_twoSided b.pate_coverage_input
       patt_coverage_input :=
        absoluteWaldCoverageInput_of_twoSided b.patt_coverage_input } :
      PATEPATTFiniteScoreCellEstimatedScoreAbsoluteWaldBridge
        PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l)

/--
Build a paired two-sided plain Wald bridge whose finite score-cell
layer is backed by GC certificates on the LLN side.
-/
def
    patePattFiniteScoreCellEstimatedScoreTwoSidedWaldBridgeOfGlivenkoCantelli
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pateKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pattKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pateScaledApproximationToMatchingDiscrepancy :
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        pateKnownScoreBridge.matching_discrepancy_negligible)
    (pattScaledApproximationToMatchingDiscrepancy :
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        pattKnownScoreBridge.matching_discrepancy_negligible)
    (pateEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pattEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pateKnownScoreToEstimatedScoreInput :
      pateKnownScoreBridge.asymptotic_normality ->
        pateEstimatedScoreBridge.known_score_asymptotic_normality)
    (pattKnownScoreToEstimatedScoreInput :
      pattKnownScoreBridge.asymptotic_normality ->
        pattEstimatedScoreBridge.known_score_asymptotic_normality)
    (pateStudentizationInput :
      EstimatedScoreStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (pattStudentizationInput :
      EstimatedScoreStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pateStudentizationInput.scaledStatistic l
          pateStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pattStudentizationInput.scaledStatistic l
          pattStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (pateCoverageInput : TwoSidedWaldCoverageInput Index Sample l)
    (pattCoverageInput : TwoSidedWaldCoverageInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l where
  studentized_bridge :=
    patePattFiniteScoreCellEstimatedScoreStudentizedBridgeOfGlivenkoCantelli
      pateCells pateReferenceShare pateSample pateWeight pateScore
      pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
      pateFiniteConditionsToScaled pateEnvelopeToScaled
      pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
      pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
      pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
      pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
      pateScaledApproximationToMatchingDiscrepancy
      pattScaledApproximationToMatchingDiscrepancy pateEstimatedScoreBridge
      pattEstimatedScoreBridge pateKnownScoreToEstimatedScoreInput
      pattKnownScoreToEstimatedScoreInput sampleLaw limitLaw l
      pateStudentizationInput pattStudentizationInput
      pateEstimatedScoreToScaledTendsto pattEstimatedScoreToScaledTendsto
  pate_coverage_input := pateCoverageInput
  patt_coverage_input := pattCoverageInput

/--
The GC-backed plain studentized route yields paired two-sided Wald
coverage once the finite-cell, known-score, estimated-score, studentization,
and Wald coverage obligations are supplied.
-/
theorem
    pate_patt_twoSidedWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pateKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pattKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pateScaledApproximationToMatchingDiscrepancy :
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        pateKnownScoreBridge.matching_discrepancy_negligible)
    (pattScaledApproximationToMatchingDiscrepancy :
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        pattKnownScoreBridge.matching_discrepancy_negligible)
    (pateEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pattEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pateKnownScoreToEstimatedScoreInput :
      pateKnownScoreBridge.asymptotic_normality ->
        pateEstimatedScoreBridge.known_score_asymptotic_normality)
    (pattKnownScoreToEstimatedScoreInput :
      pattKnownScoreBridge.asymptotic_normality ->
        pattEstimatedScoreBridge.known_score_asymptotic_normality)
    (pateStudentizationInput :
      EstimatedScoreStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (pattStudentizationInput :
      EstimatedScoreStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pateStudentizationInput.scaledStatistic l
          pateStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pattStudentizationInput.scaledStatistic l
          pattStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (pateCoverageInput : TwoSidedWaldCoverageInput Index Sample l)
    (pattCoverageInput : TwoSidedWaldCoverageInput Index Sample l)
    (hpateGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).weighted_indicator_array_lln)
    (hpateFinite : pateIndicatorBridge.eventual_finite_conditions)
    (hpateEnvelope : pateIndicatorBridge.envelope_convergence)
    (hpateSimplex : pateCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpateLinear :
      pateCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpateMatrix :
      pateCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpattGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).weighted_indicator_array_lln)
    (hpattFinite : pattIndicatorBridge.eventual_finite_conditions)
    (hpattEnvelope : pattIndicatorBridge.envelope_convergence)
    (hpattSimplex : pattCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpattLinear :
      pattCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpattMatrix :
      pattCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpateDecomp : pateKnownScoreBridge.aggregate_hajek_decomposition)
    (hpateDenominator : pateKnownScoreBridge.denominator_stabilization)
    (hpateHeterogeneity : pateKnownScoreBridge.heterogeneity_clt)
    (hpateResidual : pateKnownScoreBridge.residual_clt)
    (hpattDecomp : pattKnownScoreBridge.aggregate_hajek_decomposition)
    (hpattDenominator : pattKnownScoreBridge.denominator_stabilization)
    (hpattHeterogeneity : pattKnownScoreBridge.heterogeneity_clt)
    (hpattResidual : pattKnownScoreBridge.residual_clt)
    (hpateFirst :
      pateEstimatedScoreBridge.first_step_asymptotic_linearization)
    (hpateLocal :
      pateEstimatedScoreBridge.matching_functional_local_expansion)
    (hpateGodambe : pateEstimatedScoreBridge.godambe_variance_identity)
    (hpattFirst :
      pattEstimatedScoreBridge.first_step_asymptotic_linearization)
    (hpattLocal :
      pattEstimatedScoreBridge.matching_functional_local_expansion)
    (hpattGodambe : pattEstimatedScoreBridge.godambe_variance_identity) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli
      (patePattFiniteScoreCellEstimatedScoreTwoSidedWaldBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight pateScore
        pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
        pateFiniteConditionsToScaled pateEnvelopeToScaled
        pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
        pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
        pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
        pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
        pateScaledApproximationToMatchingDiscrepancy
        pattScaledApproximationToMatchingDiscrepancy pateEstimatedScoreBridge
        pattEstimatedScoreBridge pateKnownScoreToEstimatedScoreInput
        pattKnownScoreToEstimatedScoreInput pateStudentizationInput
        pattStudentizationInput pateEstimatedScoreToScaledTendsto
        pattEstimatedScoreToScaledTendsto pateCoverageInput
        pattCoverageInput) := by
  have hpateDesign :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).survey_design_regularity := by
    simpa [finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli] using hpateGC
  have hpattDesign :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).survey_design_regularity := by
    simpa [finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli] using hpattGC
  simpa
    [PATEPATTFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli,
      PATEPATTFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli,
      patePattFiniteScoreCellEstimatedScoreTwoSidedWaldBridgeOfGlivenkoCantelli,
      absoluteWaldCoverageInput_of_twoSided]
    using
      pate_patt_twoSidedWaldCoverage_tendsto_of_paired_finite_score_cell_estimated_score
        (patePattFiniteScoreCellEstimatedScoreTwoSidedWaldBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy pateEstimatedScoreBridge
          pattEstimatedScoreBridge pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput pateStudentizationInput
          pattStudentizationInput pateEstimatedScoreToScaledTendsto
          pattEstimatedScoreToScaledTendsto pateCoverageInput
          pattCoverageInput)
        hpateDesign
        (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
          pateCells pateReferenceShare pateSample pateWeight pateScore)
        hpateGC hpateFinite hpateEnvelope hpateSimplex hpateLinear hpateMatrix
        hpattDesign
        (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
          pattCells pattReferenceShare pattSample pattWeight pattScore)
        hpattGC hpattFinite hpattEnvelope hpattSimplex hpattLinear hpattMatrix
        hpateDecomp hpateDenominator hpateHeterogeneity hpateResidual
        hpattDecomp hpattDenominator hpattHeterogeneity hpattResidual
        hpateFirst hpateLocal hpateGodambe hpattFirst hpattLocal hpattGodambe

/--
The paired GC-backed two-sided ordinary Wald route with the PATE and PATT local
expansion/Godambe obligations packaged as compact estimated-score cores.
-/
theorem
    pate_patt_twoSidedWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli_estimated_score_core
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pateKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pattKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pateScaledApproximationToMatchingDiscrepancy :
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        pateKnownScoreBridge.matching_discrepancy_negligible)
    (pattScaledApproximationToMatchingDiscrepancy :
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        pattKnownScoreBridge.matching_discrepancy_negligible)
    (pateEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pattEstimatedScoreBridge : EstimatedScoreAsymptoticBridge)
    (pateCore : EstimatedScoreAsymptoticBridgeCore pateEstimatedScoreBridge)
    (pattCore : EstimatedScoreAsymptoticBridgeCore pattEstimatedScoreBridge)
    (pateKnownScoreToEstimatedScoreInput :
      pateKnownScoreBridge.asymptotic_normality ->
        pateEstimatedScoreBridge.known_score_asymptotic_normality)
    (pattKnownScoreToEstimatedScoreInput :
      pattKnownScoreBridge.asymptotic_normality ->
        pattEstimatedScoreBridge.known_score_asymptotic_normality)
    (pateStudentizationInput :
      EstimatedScoreStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (pattStudentizationInput :
      EstimatedScoreStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pateStudentizationInput.scaledStatistic l
          pateStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pattStudentizationInput.scaledStatistic l
          pattStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (pateCoverageInput : TwoSidedWaldCoverageInput Index Sample l)
    (pattCoverageInput : TwoSidedWaldCoverageInput Index Sample l)
    (hpateGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).weighted_indicator_array_lln)
    (hpateFinite : pateIndicatorBridge.eventual_finite_conditions)
    (hpateEnvelope : pateIndicatorBridge.envelope_convergence)
    (hpateSimplex : pateCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpateLinear :
      pateCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpateMatrix :
      pateCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpattGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).weighted_indicator_array_lln)
    (hpattFinite : pattIndicatorBridge.eventual_finite_conditions)
    (hpattEnvelope : pattIndicatorBridge.envelope_convergence)
    (hpattSimplex : pattCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpattLinear :
      pattCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpattMatrix :
      pattCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpateDecomp : pateKnownScoreBridge.aggregate_hajek_decomposition)
    (hpateDenominator : pateKnownScoreBridge.denominator_stabilization)
    (hpateHeterogeneity : pateKnownScoreBridge.heterogeneity_clt)
    (hpateResidual : pateKnownScoreBridge.residual_clt)
    (hpattDecomp : pattKnownScoreBridge.aggregate_hajek_decomposition)
    (hpattDenominator : pattKnownScoreBridge.denominator_stabilization)
    (hpattHeterogeneity : pattKnownScoreBridge.heterogeneity_clt)
    (hpattResidual : pattKnownScoreBridge.residual_clt)
    (hpateFirst :
      pateEstimatedScoreBridge.first_step_asymptotic_linearization)
    (hpattFirst :
      pattEstimatedScoreBridge.first_step_asymptotic_linearization) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli
      (patePattFiniteScoreCellEstimatedScoreTwoSidedWaldBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight pateScore
        pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
        pateFiniteConditionsToScaled pateEnvelopeToScaled
        pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
        pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
        pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
        pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
        pateScaledApproximationToMatchingDiscrepancy
        pattScaledApproximationToMatchingDiscrepancy pateEstimatedScoreBridge
        pattEstimatedScoreBridge pateKnownScoreToEstimatedScoreInput
        pattKnownScoreToEstimatedScoreInput pateStudentizationInput
        pattStudentizationInput pateEstimatedScoreToScaledTendsto
        pattEstimatedScoreToScaledTendsto pateCoverageInput
        pattCoverageInput) :=
  pate_patt_twoSidedWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli
    pateCells pateReferenceShare pateSample pateWeight pateScore
    pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
    pateFiniteConditionsToScaled pateEnvelopeToScaled pateIndicatorLLNToScaled
    pattCells pattReferenceShare pattSample pattWeight pattScore
    pattIndicatorBridge pattFiniteLLNToIndicatorLLN pattCLTBridge
    pattFiniteConditionsToScaled pattEnvelopeToScaled pattIndicatorLLNToScaled
    pateKnownScoreBridge pattKnownScoreBridge
    pateScaledApproximationToMatchingDiscrepancy
    pattScaledApproximationToMatchingDiscrepancy pateEstimatedScoreBridge
    pattEstimatedScoreBridge pateKnownScoreToEstimatedScoreInput
    pattKnownScoreToEstimatedScoreInput pateStudentizationInput
    pattStudentizationInput pateEstimatedScoreToScaledTendsto
    pattEstimatedScoreToScaledTendsto pateCoverageInput pattCoverageInput
    hpateGC hpateFinite hpateEnvelope hpateSimplex hpateLinear hpateMatrix
    hpattGC hpattFinite hpattEnvelope hpattSimplex hpattLinear hpattMatrix
    hpateDecomp hpateDenominator hpateHeterogeneity hpateResidual
    hpattDecomp hpattDenominator hpattHeterogeneity hpattResidual
    hpateFirst pateCore.matching_functional_local_expansion
    pateCore.godambe_variance_identity hpattFirst
    pattCore.matching_functional_local_expansion
    pattCore.godambe_variance_identity

/--
The paired GC-backed two-sided plain Wald route with the PATE and PATT local
experiment obligations packaged as compact local-experiment cores.
-/
theorem
    pate_patt_twoSidedWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli_local_experiment_core
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pateIndicatorBridge : PATEDoubleScoreIndicatorSumConvergenceBridge)
    (pateFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).cellwise_weighted_indicator_sum_lln ->
        pateIndicatorBridge.weighted_indicator_sum_lln)
    (pateCLTBridge : ScaledPATEFiniteScoreCellCLTApproximationBridge PATECell)
    (pateFiniteConditionsToScaled :
      pateIndicatorBridge.eventual_finite_conditions ->
        pateCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pateEnvelopeToScaled :
      pateIndicatorBridge.envelope_convergence ->
        pateCLTBridge.indicator_bridge.envelope_convergence)
    (pateIndicatorLLNToScaled :
      pateIndicatorBridge.weighted_indicator_sum_lln ->
        pateCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pattIndicatorBridge : PATTDoubleScoreIndicatorSumConvergenceBridge)
    (pattFiniteLLNToIndicatorLLN :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).cellwise_weighted_indicator_sum_lln ->
        pattIndicatorBridge.weighted_indicator_sum_lln)
    (pattCLTBridge : ScaledPATTFiniteScoreCellCLTApproximationBridge PATTCell)
    (pattFiniteConditionsToScaled :
      pattIndicatorBridge.eventual_finite_conditions ->
        pattCLTBridge.indicator_bridge.eventual_finite_conditions)
    (pattEnvelopeToScaled :
      pattIndicatorBridge.envelope_convergence ->
        pattCLTBridge.indicator_bridge.envelope_convergence)
    (pattIndicatorLLNToScaled :
      pattIndicatorBridge.weighted_indicator_sum_lln ->
        pattCLTBridge.indicator_bridge.weighted_indicator_sum_lln)
    (pateKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pattKnownScoreBridge : KnownScoreAsymptoticBridge)
    (pateScaledApproximationToMatchingDiscrepancy :
      pateCLTBridge.indicator_bridge.scaled_pate_double_score_approximation_negligible ->
        pateKnownScoreBridge.matching_discrepancy_negligible)
    (pattScaledApproximationToMatchingDiscrepancy :
      pattCLTBridge.indicator_bridge.scaled_patt_double_score_approximation_negligible ->
        pattKnownScoreBridge.matching_discrepancy_negligible)
(pateEstimated : EstimatedScoreLocalExperimentInput)
(pattEstimated : EstimatedScoreLocalExperimentInput)
(pateCore : EstimatedScoreLocalExperimentCore pateEstimated)
(pattCore : EstimatedScoreLocalExperimentCore pattEstimated)
    (pateKnownScoreToEstimatedScoreInput :
      pateKnownScoreBridge.asymptotic_normality ->
        pateEstimated.known_score_asymptotic_normality)
    (pattKnownScoreToEstimatedScoreInput :
      pattKnownScoreBridge.asymptotic_normality ->
        pattEstimated.known_score_asymptotic_normality)
    (pateStudentizationInput :
      EstimatedScoreStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (pattStudentizationInput :
      EstimatedScoreStudentizationInput Index Sample
        LimitSample sampleLaw limitLaw l)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution pateStudentizationInput.scaledStatistic l
          pateStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution pattStudentizationInput.scaledStatistic l
          pattStudentizationInput.limit (fun _index => sampleLaw) limitLaw)
    (pateCoverageInput : TwoSidedWaldCoverageInput Index Sample l)
    (pattCoverageInput : TwoSidedWaldCoverageInput Index Sample l)
    (hpateGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).weighted_indicator_array_lln)
    (hpateFinite : pateIndicatorBridge.eventual_finite_conditions)
    (hpateEnvelope : pateIndicatorBridge.envelope_convergence)
    (hpateSimplex : pateCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpateLinear :
      pateCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpateMatrix :
      pateCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpattGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).weighted_indicator_array_lln)
    (hpattFinite : pattIndicatorBridge.eventual_finite_conditions)
    (hpattEnvelope : pattIndicatorBridge.envelope_convergence)
    (hpattSimplex : pattCLTBridge.vector_clt_bridge.simplex_reference_shares)
    (hpattLinear :
      pattCLTBridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hpattMatrix :
      pattCLTBridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hpateDecomp : pateKnownScoreBridge.aggregate_hajek_decomposition)
    (hpateDenominator : pateKnownScoreBridge.denominator_stabilization)
    (hpateHeterogeneity : pateKnownScoreBridge.heterogeneity_clt)
    (hpateResidual : pateKnownScoreBridge.residual_clt)
    (hpattDecomp : pattKnownScoreBridge.aggregate_hajek_decomposition)
    (hpattDenominator : pattKnownScoreBridge.denominator_stabilization)
    (hpattHeterogeneity : pattKnownScoreBridge.heterogeneity_clt)
    (hpattResidual : pattKnownScoreBridge.residual_clt)
    (hpateFirst :
      pateEstimated.first_step_asymptotic_linearization)
    (hpateScore :
      pateEstimated.score_estimator_local_asymptotic_linearity)
    (hpattFirst :
      pattEstimated.first_step_asymptotic_linearization)
    (hpattScore :
      pattEstimated.score_estimator_local_asymptotic_linearity) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli
      (patePattFiniteScoreCellEstimatedScoreTwoSidedWaldBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight pateScore
        pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
        pateFiniteConditionsToScaled pateEnvelopeToScaled
        pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
        pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
        pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
        pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
        pateScaledApproximationToMatchingDiscrepancy
        pattScaledApproximationToMatchingDiscrepancy (estimatedScoreAsymptoticBridgeOfLocalExperimentInput pateEstimated)
        (estimatedScoreAsymptoticBridgeOfLocalExperimentInput pattEstimated) pateKnownScoreToEstimatedScoreInput
        pattKnownScoreToEstimatedScoreInput pateStudentizationInput
        pattStudentizationInput pateEstimatedScoreToScaledTendsto
        pattEstimatedScoreToScaledTendsto pateCoverageInput
        pattCoverageInput) :=
  pate_patt_twoSidedWaldCoverage_tendsto_of_finite_score_cell_estimated_score_glivenkoCantelli
    pateCells pateReferenceShare pateSample pateWeight pateScore
    pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
    pateFiniteConditionsToScaled pateEnvelopeToScaled pateIndicatorLLNToScaled
    pattCells pattReferenceShare pattSample pattWeight pattScore
    pattIndicatorBridge pattFiniteLLNToIndicatorLLN pattCLTBridge
    pattFiniteConditionsToScaled pattEnvelopeToScaled pattIndicatorLLNToScaled
    pateKnownScoreBridge pattKnownScoreBridge
    pateScaledApproximationToMatchingDiscrepancy
    pattScaledApproximationToMatchingDiscrepancy (estimatedScoreAsymptoticBridgeOfLocalExperimentInput pateEstimated)
    (estimatedScoreAsymptoticBridgeOfLocalExperimentInput pattEstimated) pateKnownScoreToEstimatedScoreInput
    pattKnownScoreToEstimatedScoreInput pateStudentizationInput
    pattStudentizationInput pateEstimatedScoreToScaledTendsto
    pattEstimatedScoreToScaledTendsto pateCoverageInput pattCoverageInput
    hpateGC hpateFinite hpateEnvelope hpateSimplex hpateLinear hpateMatrix
    hpattGC hpattFinite hpattEnvelope hpattSimplex hpattLinear hpattMatrix
    hpateDecomp hpateDenominator hpateHeterogeneity hpateResidual
    hpattDecomp hpattDenominator hpattHeterogeneity hpattResidual
    hpateFirst
    ⟨hpateScore, pateCore.matching_functional_local_derivative,
      pateCore.local_stochastic_equicontinuity⟩
    pateCore.godambe_variance_identity hpattFirst
    ⟨hpattScore, pattCore.matching_functional_local_derivative,
      pattCore.local_stochastic_equicontinuity⟩
    pattCore.godambe_variance_identity


/--
Convert a GC-backed paired absolute Wald bridge into the corresponding
two-sided Wald bridge by calibrating the critical region.
-/
def
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedWaldBridgeOfAbsoluteCoverage
    (b :
      PATEPATTFiniteScoreCellEstimatedScoreAbsoluteWaldBridge
        PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l where
  studentized_bridge := b.studentized_bridge
  pate_coverage_input :=
    twoSidedWaldCoverageInput_of_absolute b.pate_coverage_input
  patt_coverage_input :=
    twoSidedWaldCoverageInput_of_absolute b.patt_coverage_input

/--
Absolute-region Wald calibration also yields the paired two-sided Wald
conclusion for the same GC-backed finite score-cell bridge.
-/
theorem
    pate_patt_twoSidedWaldCoverage_tendsto_of_absolute_finite_score_cell_estimated_score_glivenkoCantelli
    (b :
      PATEPATTFiniteScoreCellEstimatedScoreAbsoluteWaldBridge
        PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l)
    (h :
      PATEPATTFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
        b) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli
      (PATEPATTFiniteScoreCellEstimatedScoreTwoSidedWaldBridgeOfAbsoluteCoverage
        b) := by
  simpa
    [PATEPATTFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli,
      PATEPATTFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli,
      PATEPATTFiniteScoreCellEstimatedScoreTwoSidedWaldBridgeOfAbsoluteCoverage,
      twoSidedWaldCoverageInput_of_absolute,
      absoluteWaldCoverageInput_of_twoSided]
    using h

/--
Convert a GC-backed paired two-sided Wald bridge into the corresponding
absolute Wald bridge by calibrating the critical region.
-/
def
    PATEPATTFiniteScoreCellEstimatedScoreAbsoluteWaldBridgeOfTwoSidedCoverage
    (b :
      PATEPATTFiniteScoreCellEstimatedScoreTwoSidedWaldBridge
        PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsoluteWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l where
  studentized_bridge := b.studentized_bridge
  pate_coverage_input :=
    absoluteWaldCoverageInput_of_twoSided b.pate_coverage_input
  patt_coverage_input :=
    absoluteWaldCoverageInput_of_twoSided b.patt_coverage_input

/--
Two-sided Wald calibration also yields the paired absolute Wald conclusion for
the same GC-backed finite score-cell bridge.
-/
theorem
    pate_patt_absoluteWaldCoverage_tendsto_of_twoSided_finite_score_cell_estimated_score_glivenkoCantelli
    (b :
      PATEPATTFiniteScoreCellEstimatedScoreTwoSidedWaldBridge
        PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l)
    (h :
      PATEPATTFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli
        b) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
      (PATEPATTFiniteScoreCellEstimatedScoreAbsoluteWaldBridgeOfTwoSidedCoverage
        b) := by
  simpa
    [PATEPATTFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli,
      PATEPATTFiniteScoreCellEstimatedScoreAbsoluteWaldBridgeOfTwoSidedCoverage]
    using h

/--
Attach paired GC-backed score-cell mass LLNs to an already derived paired
absolute ordinary Wald conclusion.
-/
theorem
    pate_patt_absoluteWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (hpateGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).weighted_indicator_array_lln)
    (hpattGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).weighted_indicator_array_lln)
    {b :
      PATEPATTFiniteScoreCellEstimatedScoreAbsoluteWaldBridge
        PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATEPATTFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
        b) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) pateCells pateSample
        pateWeight pateScore pateReferenceShare ∧
      cellwiseScoreCellMassLLN (l := atTop) pattCells pattSample
        pattWeight pattScore pattReferenceShare :=
  paired_output_and_mass_lln_of_glivenkoCantelli_bridge
    pateCells pattCells pateReferenceShare pattReferenceShare pateSample
    pattSample pateWeight pattWeight pateScore pattScore hpateGC hpattGC
    hcoverage

/--
Attach paired GC-backed score-cell mass LLNs to an already derived paired
two-sided ordinary Wald conclusion.
-/
theorem
    pate_patt_twoSidedWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (hpateGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pateCells pateReferenceShare pateSample pateWeight
        pateScore).weighted_indicator_array_lln)
    (hpattGC :
      (finiteScoreCellIndicatorLLNBridgeOfGlivenkoCantelli
        pattCells pattReferenceShare pattSample pattWeight
        pattScore).weighted_indicator_array_lln)
    {b :
      PATEPATTFiniteScoreCellEstimatedScoreTwoSidedWaldBridge
        PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATEPATTFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli
        b) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) pateCells pateSample
        pateWeight pateScore pateReferenceShare ∧
      cellwiseScoreCellMassLLN (l := atTop) pattCells pattSample
        pattWeight pattScore pattReferenceShare :=
  paired_output_and_mass_lln_of_glivenkoCantelli_bridge
    pateCells pattCells pateReferenceShare pattReferenceShare pateSample
    pattSample pateWeight pattWeight pateScore pattScore hpateGC hpattGC
    hcoverage

theorem
    pate_patt_absoluteWaldConclusion_and_mass_lln_of_l1BracketingNumber_obligations
    {PATEBracket PATTBracket : Type*}
    [Fintype PATEBracket] [Fintype PATTBracket]
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pateObligations :
      L1BracketingNumberConstructorObligations (Bracket := PATEBracket)
        {cell : PATECell | cell ∈ pateCells} pateReferenceShare
        (fun sampleSize cell =>
          weightedSampleSum (pateSample sampleSize) (pateWeight sampleSize)
            (scoreCellIndicator (pateScore sampleSize) cell)))
    (pattObligations :
      L1BracketingNumberConstructorObligations (Bracket := PATTBracket)
        {cell : PATTCell | cell ∈ pattCells} pattReferenceShare
        (fun sampleSize cell =>
          weightedSampleSum (pattSample sampleSize) (pattWeight sampleSize)
            (scoreCellIndicator (pattScore sampleSize) cell)))
    {b :
      PATEPATTFiniteScoreCellEstimatedScoreAbsoluteWaldBridge
        PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATEPATTFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
        b) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) pateCells pateSample
        pateWeight pateScore pateReferenceShare ∧
      cellwiseScoreCellMassLLN (l := atTop) pattCells pattSample
        pattWeight pattScore pattReferenceShare :=
  pate_patt_absoluteWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    pateCells pateReferenceShare pateSample pateWeight pateScore pattCells
    pattReferenceShare pattSample pattWeight pattScore
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      pateCells pateReferenceShare pateSample pateWeight pateScore
      pateObligations)
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      pattCells pattReferenceShare pattSample pattWeight pattScore
      pattObligations)
    hcoverage

theorem
    pate_patt_absoluteWaldConclusion_and_mass_lln_of_vdvw241_endpoint_assembly
    {PATEBracket PATTBracket : Type*}
    [Fintype PATEBracket] [Fintype PATTBracket]
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pateAssembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := PATEBracket)
        {cell : PATECell | cell ∈ pateCells} pateReferenceShare
        (fun sampleSize cell =>
          weightedSampleSum (pateSample sampleSize) (pateWeight sampleSize)
            (scoreCellIndicator (pateScore sampleSize) cell)))
    (pattAssembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := PATTBracket)
        {cell : PATTCell | cell ∈ pattCells} pattReferenceShare
        (fun sampleSize cell =>
          weightedSampleSum (pattSample sampleSize) (pattWeight sampleSize)
            (scoreCellIndicator (pattScore sampleSize) cell)))
    {b :
      PATEPATTFiniteScoreCellEstimatedScoreAbsoluteWaldBridge
        PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATEPATTFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
        b) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsoluteWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) pateCells pateSample
        pateWeight pateScore pateReferenceShare ∧
      cellwiseScoreCellMassLLN (l := atTop) pattCells pattSample
        pattWeight pattScore pattReferenceShare :=
  pate_patt_absoluteWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    pateCells pateReferenceShare pateSample pateWeight pateScore pattCells
    pattReferenceShare pattSample pattWeight pattScore
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      pateCells pateReferenceShare pateSample pateWeight pateScore
      pateAssembly)
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      pattCells pattReferenceShare pattSample pattWeight pattScore
      pattAssembly)
    hcoverage

theorem
    pate_patt_twoSidedWaldConclusion_and_mass_lln_of_l1BracketingNumber_obligations
    {PATEBracket PATTBracket : Type*}
    [Fintype PATEBracket] [Fintype PATTBracket]
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pateObligations :
      L1BracketingNumberConstructorObligations (Bracket := PATEBracket)
        {cell : PATECell | cell ∈ pateCells} pateReferenceShare
        (fun sampleSize cell =>
          weightedSampleSum (pateSample sampleSize) (pateWeight sampleSize)
            (scoreCellIndicator (pateScore sampleSize) cell)))
    (pattObligations :
      L1BracketingNumberConstructorObligations (Bracket := PATTBracket)
        {cell : PATTCell | cell ∈ pattCells} pattReferenceShare
        (fun sampleSize cell =>
          weightedSampleSum (pattSample sampleSize) (pattWeight sampleSize)
            (scoreCellIndicator (pattScore sampleSize) cell)))
    {b :
      PATEPATTFiniteScoreCellEstimatedScoreTwoSidedWaldBridge
        PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATEPATTFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli
        b) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) pateCells pateSample
        pateWeight pateScore pateReferenceShare ∧
      cellwiseScoreCellMassLLN (l := atTop) pattCells pattSample
        pattWeight pattScore pattReferenceShare :=
  pate_patt_twoSidedWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    pateCells pateReferenceShare pateSample pateWeight pateScore pattCells
    pattReferenceShare pattSample pattWeight pattScore
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      pateCells pateReferenceShare pateSample pateWeight pateScore
      pateObligations)
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      pattCells pattReferenceShare pattSample pattWeight pattScore
      pattObligations)
    hcoverage

theorem
    pate_patt_twoSidedWaldConclusion_and_mass_lln_of_vdvw241_endpoint_assembly
    {PATEBracket PATTBracket : Type*}
    [Fintype PATEBracket] [Fintype PATTBracket]
    (pateCells : Finset PATECell)
    (pateReferenceShare : PATECell -> Real)
    (pateSample : ℕ -> Finset Unit)
    (pateWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
    (pattCells : Finset PATTCell)
    (pattReferenceShare : PATTCell -> Real)
    (pattSample : ℕ -> Finset Unit)
    (pattWeight : ℕ -> Unit -> Real)
    (pattScore : ℕ -> Unit -> PATTCell)
    (pateAssembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := PATEBracket)
        {cell : PATECell | cell ∈ pateCells} pateReferenceShare
        (fun sampleSize cell =>
          weightedSampleSum (pateSample sampleSize) (pateWeight sampleSize)
            (scoreCellIndicator (pateScore sampleSize) cell)))
    (pattAssembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := PATTBracket)
        {cell : PATTCell | cell ∈ pattCells} pattReferenceShare
        (fun sampleSize cell =>
          weightedSampleSum (pattSample sampleSize) (pattWeight sampleSize)
            (scoreCellIndicator (pattScore sampleSize) cell)))
    {b :
      PATEPATTFiniteScoreCellEstimatedScoreTwoSidedWaldBridge
        PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATEPATTFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli
        b) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedWaldConclusionOfGlivenkoCantelli
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) pateCells pateSample
        pateWeight pateScore pateReferenceShare ∧
      cellwiseScoreCellMassLLN (l := atTop) pattCells pattSample
        pattWeight pattScore pattReferenceShare :=
  pate_patt_twoSidedWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    pateCells pateReferenceShare pateSample pateWeight pateScore pattCells
    pattReferenceShare pattSample pattWeight pattScore
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      pateCells pateReferenceShare pateSample pateWeight pateScore
      pateAssembly)
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      pattCells pattReferenceShare pattSample pattWeight pattScore
      pattAssembly)
    hcoverage

end WDSM
end Matching
end StatInference
