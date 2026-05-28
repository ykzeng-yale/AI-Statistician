import StatInference.Matching.WDSM.FiniteCellIndicatorGCSingleComponentPositiveVarianceWaldAdapter
import StatInference.Matching.WDSM.FiniteCellIndicatorGCSinglePositiveVarianceWaldAdapter

/-!
# GC-backed single-arm component-positive Wald coverage

This module proves direct coverage wrappers for the single-arm GC-backed
component-positive Wald bridge constructors.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter MeasureTheory
open scoped Topology

variable {Unit Cell Index Sample LimitSample : Type*}
variable [DecidableEq Cell]
variable [MeasurableSpace Sample] [MeasurableSpace LimitSample]
variable {sampleLaw : MeasureTheory.Measure Sample}
variable {limitLaw : MeasureTheory.Measure LimitSample}
variable [MeasureTheory.IsProbabilityMeasure sampleLaw]
variable [MeasureTheory.IsProbabilityMeasure limitLaw]
variable {l : Filter Index}
variable [l.IsCountablyGenerated]

/-! ## PATE absolute projection_lt_limit -/

/--
The GC-backed single-arm PATE component-positive route yields
absolute positive-variance Wald coverage from strict projection slack and nonnegative target drift.
-/
theorem
    pate_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit_glivenkoCantelli
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hdriftLimit_nonneg : 0 ≤ targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
      (pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) := by
  simpa
    [PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_lt_limit_glivenkoCantelli,
      pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_lt_limit,
      pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_lt_limit,
      estimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit]
    using
      pate_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit
        (pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          cells referenceShare sample weight score indicatorBridge
          finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
          envelopeToScaled indicatorLLNToScaled knownScoreBridge
          scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
          knownScoreToEstimatedScoreInput)
        scaledStatistic oracle projectionReduction targetDrift limit
        oracleLimit projectionLimit targetDriftLimit horacle hprojection
        hdrift hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
        estimatedScoreToScaledTendsto coverageInput hgc
        (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
          cells referenceShare sample weight score)
        hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
        hdenominator hheterogeneity hresidual hfirst hlocal hgodambe

/--
The strict projection-slack GC-backed single-arm PATE absolute
component-positive route with local expansion and Godambe obligations packaged
as one compact core.
-/
theorem
    pate_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit_glivenkoCantelli_estimated_score_core
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hdriftLimit_nonneg : 0 ≤ targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
      (pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  pate_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    estimatedScoreBridge knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction targetDrift limit oracleLimit projectionLimit
    targetDriftLimit horacle hprojection hdrift hprojectionLimit_lt_oracle
    hdriftLimit_nonneg hinverse_meas estimatedScoreToScaledTendsto coverageInput
    hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp hdenominator
    hheterogeneity hresidual hfirst core.matching_functional_local_expansion
    core.godambe_variance_identity

/--
The strict projection-slack GC-backed single-arm PATE absolute
component-positive route with local expansion and Godambe obligations packaged
as one compact local-experiment core.
-/
theorem
    pate_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit_glivenkoCantelli_local_experiment_core
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
    (estimated : EstimatedScoreLocalExperimentInput)
    (core : EstimatedScoreLocalExperimentCore estimated)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hdriftLimit_nonneg : 0 ≤ targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity) :
    PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated)
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  pate_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated) knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction targetDrift limit oracleLimit projectionLimit
    targetDriftLimit horacle hprojection hdrift hprojectionLimit_lt_oracle
    hdriftLimit_nonneg hinverse_meas estimatedScoreToScaledTendsto coverageInput
    hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp hdenominator
    hheterogeneity hresidual hfirst
    ⟨hscore, core.matching_functional_local_derivative,
      core.local_stochastic_equicontinuity⟩
    core.godambe_variance_identity

/-! ## PATE two-sided projection_lt_limit -/

/--
The GC-backed single-arm PATE component-positive route yields
two-sided positive-variance Wald coverage from strict projection slack and nonnegative target drift.
-/
theorem
    pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit_glivenkoCantelli
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hdriftLimit_nonneg : 0 ≤ targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
      (pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) := by
  simpa
    [PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli,
      PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      absoluteWaldCoverageVarianceInput_of_twoSided,
      pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_lt_limit_glivenkoCantelli,
      pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_lt_limit,
      pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_lt_limit,
      estimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit]
    using
      pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit
        (pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          cells referenceShare sample weight score indicatorBridge
          finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
          envelopeToScaled indicatorLLNToScaled knownScoreBridge
          scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
          knownScoreToEstimatedScoreInput)
        scaledStatistic oracle projectionReduction targetDrift limit
        oracleLimit projectionLimit targetDriftLimit horacle hprojection
        hdrift hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
        estimatedScoreToScaledTendsto coverageInput hgc
        (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
          cells referenceShare sample weight score)
        hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
        hdenominator hheterogeneity hresidual hfirst hlocal hgodambe

/--
The strict projection-slack GC-backed single-arm PATE two-sided
component-positive route with local expansion and Godambe obligations packaged
as one compact core.
-/
theorem
    pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit_glivenkoCantelli_estimated_score_core
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hdriftLimit_nonneg : 0 ≤ targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
      (pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    estimatedScoreBridge knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction targetDrift limit oracleLimit projectionLimit
    targetDriftLimit horacle hprojection hdrift hprojectionLimit_lt_oracle
    hdriftLimit_nonneg hinverse_meas estimatedScoreToScaledTendsto coverageInput
    hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp hdenominator
    hheterogeneity hresidual hfirst core.matching_functional_local_expansion
    core.godambe_variance_identity

/--
The strict projection-slack GC-backed single-arm PATE two-sided
component-positive route with local expansion and Godambe obligations packaged
as one compact local-experiment core.
-/
theorem
    pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit_glivenkoCantelli_local_experiment_core
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
    (estimated : EstimatedScoreLocalExperimentInput)
    (core : EstimatedScoreLocalExperimentCore estimated)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hdriftLimit_nonneg : 0 ≤ targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity) :
    PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated)
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated) knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction targetDrift limit oracleLimit projectionLimit
    targetDriftLimit horacle hprojection hdrift hprojectionLimit_lt_oracle
    hdriftLimit_nonneg hinverse_meas estimatedScoreToScaledTendsto coverageInput
    hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp hdenominator
    hheterogeneity hresidual hfirst
    ⟨hscore, core.matching_functional_local_derivative,
      core.local_stochastic_equicontinuity⟩
    core.godambe_variance_identity

/-! ## PATE absolute projection_le_drift_pos_limit -/

/--
The GC-backed single-arm PATE component-positive route yields
absolute positive-variance Wald coverage from weak projection slack and positive target drift.
-/
theorem
    pate_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit_glivenkoCantelli
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_le_oracle : projectionLimit ≤ oracleLimit)
    (hdriftLimit_pos : 0 < targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
      (pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_le_drift_pos_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) := by
  simpa
    [PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_le_drift_pos_limit_glivenkoCantelli,
      pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_le_drift_pos_limit,
      pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_le_drift_pos_limit,
      estimatedScorePositiveVarianceStudentizationInput_of_projection_le_drift_pos_limit]
    using
      pate_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit
        (pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          cells referenceShare sample weight score indicatorBridge
          finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
          envelopeToScaled indicatorLLNToScaled knownScoreBridge
          scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
          knownScoreToEstimatedScoreInput)
        scaledStatistic oracle projectionReduction targetDrift limit
        oracleLimit projectionLimit targetDriftLimit horacle hprojection
        hdrift hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
        estimatedScoreToScaledTendsto coverageInput hgc
        (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
          cells referenceShare sample weight score)
        hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
        hdenominator hheterogeneity hresidual hfirst hlocal hgodambe

/--
The weak projection-slack, positive-drift GC-backed single-arm PATE absolute
component-positive route with local expansion and Godambe obligations packaged
as one compact core.
-/
theorem
    pate_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit_glivenkoCantelli_estimated_score_core
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_le_oracle : projectionLimit ≤ oracleLimit)
    (hdriftLimit_pos : 0 < targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
      (pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_le_drift_pos_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  pate_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    estimatedScoreBridge knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction targetDrift limit oracleLimit projectionLimit
    targetDriftLimit horacle hprojection hdrift hprojectionLimit_le_oracle
    hdriftLimit_pos hinverse_meas estimatedScoreToScaledTendsto coverageInput
    hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp hdenominator
    hheterogeneity hresidual hfirst core.matching_functional_local_expansion
    core.godambe_variance_identity

/--
The weak projection-slack, positive-drift GC-backed single-arm PATE absolute
component-positive route with local expansion and Godambe obligations packaged
as one compact local-experiment core.
-/
theorem
    pate_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit_glivenkoCantelli_local_experiment_core
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
    (estimated : EstimatedScoreLocalExperimentInput)
    (core : EstimatedScoreLocalExperimentCore estimated)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_le_oracle : projectionLimit ≤ oracleLimit)
    (hdriftLimit_pos : 0 < targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity) :
    PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_le_drift_pos_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated)
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  pate_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated) knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction targetDrift limit oracleLimit projectionLimit
    targetDriftLimit horacle hprojection hdrift hprojectionLimit_le_oracle
    hdriftLimit_pos hinverse_meas estimatedScoreToScaledTendsto coverageInput
    hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp hdenominator
    hheterogeneity hresidual hfirst
    ⟨hscore, core.matching_functional_local_derivative,
      core.local_stochastic_equicontinuity⟩
    core.godambe_variance_identity

/-! ## PATE two-sided projection_le_drift_pos_limit -/

/--
The GC-backed single-arm PATE component-positive route yields
two-sided positive-variance Wald coverage from weak projection slack and positive target drift.
-/
theorem
    pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit_glivenkoCantelli
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_le_oracle : projectionLimit ≤ oracleLimit)
    (hdriftLimit_pos : 0 < targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
      (pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_le_drift_pos_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) := by
  simpa
    [PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli,
      PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      absoluteWaldCoverageVarianceInput_of_twoSided,
      pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_le_drift_pos_limit_glivenkoCantelli,
      pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_le_drift_pos_limit,
      pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_le_drift_pos_limit,
      estimatedScorePositiveVarianceStudentizationInput_of_projection_le_drift_pos_limit]
    using
      pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit
        (pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          cells referenceShare sample weight score indicatorBridge
          finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
          envelopeToScaled indicatorLLNToScaled knownScoreBridge
          scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
          knownScoreToEstimatedScoreInput)
        scaledStatistic oracle projectionReduction targetDrift limit
        oracleLimit projectionLimit targetDriftLimit horacle hprojection
        hdrift hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
        estimatedScoreToScaledTendsto coverageInput hgc
        (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
          cells referenceShare sample weight score)
        hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
        hdenominator hheterogeneity hresidual hfirst hlocal hgodambe

/--
The weak projection-slack, positive-drift GC-backed single-arm PATE two-sided
component-positive route with local expansion and Godambe obligations packaged
as one compact core.
-/
theorem
    pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit_glivenkoCantelli_estimated_score_core
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_le_oracle : projectionLimit ≤ oracleLimit)
    (hdriftLimit_pos : 0 < targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
      (pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_le_drift_pos_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    estimatedScoreBridge knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction targetDrift limit oracleLimit projectionLimit
    targetDriftLimit horacle hprojection hdrift hprojectionLimit_le_oracle
    hdriftLimit_pos hinverse_meas estimatedScoreToScaledTendsto coverageInput
    hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp hdenominator
    hheterogeneity hresidual hfirst core.matching_functional_local_expansion
    core.godambe_variance_identity

/--
The weak projection-slack, positive-drift GC-backed single-arm PATE two-sided
component-positive route with local expansion and Godambe obligations packaged
as one compact local-experiment core.
-/
theorem
    pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit_glivenkoCantelli_local_experiment_core
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
    (estimated : EstimatedScoreLocalExperimentInput)
    (core : EstimatedScoreLocalExperimentCore estimated)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_le_oracle : projectionLimit ≤ oracleLimit)
    (hdriftLimit_pos : 0 < targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity) :
    PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_le_drift_pos_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated)
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated) knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction targetDrift limit oracleLimit projectionLimit
    targetDriftLimit horacle hprojection hdrift hprojectionLimit_le_oracle
    hdriftLimit_pos hinverse_meas estimatedScoreToScaledTendsto coverageInput
    hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp hdenominator
    hheterogeneity hresidual hfirst
    ⟨hscore, core.matching_functional_local_derivative,
      core.local_stochastic_equicontinuity⟩
    core.godambe_variance_identity

/-! ## PATE absolute fixedLaw_projection_lt_limit -/

/--
The GC-backed single-arm PATE component-positive route yields
absolute positive-variance Wald coverage from fixed-law strict projection slack.
-/
theorem
    pate_absolutePositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit_glivenkoCantelli
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
      (pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction limit oracleLimit projectionLimit horacle
        hprojection hprojectionLimit_lt_oracle hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) := by
  simpa
    [PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli,
      pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit,
      pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_fixedLaw_projection_lt_limit,
      fixedLawEstimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit]
    using
      pate_absolutePositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit
        (pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          cells referenceShare sample weight score indicatorBridge
          finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
          envelopeToScaled indicatorLLNToScaled knownScoreBridge
          scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
          knownScoreToEstimatedScoreInput)
        scaledStatistic oracle projectionReduction limit oracleLimit
        projectionLimit horacle hprojection hprojectionLimit_lt_oracle
        hinverse_meas estimatedScoreToScaledTendsto coverageInput hgc
        (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
          cells referenceShare sample weight score)
        hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
        hdenominator hheterogeneity hresidual hfirst hlocal hgodambe

/--
The fixed-law strict projection-slack GC-backed single-arm PATE absolute
component-positive route with local expansion and Godambe obligations packaged
as one compact core.
-/
theorem
    pate_absolutePositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit_glivenkoCantelli_estimated_score_core
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
      (pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction limit oracleLimit projectionLimit horacle
        hprojection hprojectionLimit_lt_oracle hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  pate_absolutePositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    estimatedScoreBridge knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction limit oracleLimit projectionLimit horacle hprojection
    hprojectionLimit_lt_oracle hinverse_meas estimatedScoreToScaledTendsto
    coverageInput hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
    hdenominator hheterogeneity hresidual hfirst
    core.matching_functional_local_expansion core.godambe_variance_identity

/--
The fixed-law strict projection-slack GC-backed single-arm PATE absolute
component-positive route with local expansion and Godambe obligations packaged
as one compact local-experiment core.
-/
theorem
    pate_absolutePositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit_glivenkoCantelli_local_experiment_core
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
    (estimated : EstimatedScoreLocalExperimentInput)
    (core : EstimatedScoreLocalExperimentCore estimated)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity) :
    PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated)
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction limit oracleLimit projectionLimit horacle
        hprojection hprojectionLimit_lt_oracle hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  pate_absolutePositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated) knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction limit oracleLimit projectionLimit horacle hprojection
    hprojectionLimit_lt_oracle hinverse_meas estimatedScoreToScaledTendsto
    coverageInput hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
    hdenominator hheterogeneity hresidual hfirst
    ⟨hscore, core.matching_functional_local_derivative,
      core.local_stochastic_equicontinuity⟩
    core.godambe_variance_identity

/-! ## PATE two-sided fixedLaw_projection_lt_limit -/

/--
The GC-backed single-arm PATE component-positive route yields
two-sided positive-variance Wald coverage from fixed-law strict projection slack.
-/
theorem
    pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit_glivenkoCantelli
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
      (pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction limit oracleLimit projectionLimit horacle
        hprojection hprojectionLimit_lt_oracle hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) := by
  simpa
    [PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli,
      PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      absoluteWaldCoverageVarianceInput_of_twoSided,
      pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli,
      pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit,
      pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_fixedLaw_projection_lt_limit,
      fixedLawEstimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit]
    using
      pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit
        (pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          cells referenceShare sample weight score indicatorBridge
          finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
          envelopeToScaled indicatorLLNToScaled knownScoreBridge
          scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
          knownScoreToEstimatedScoreInput)
        scaledStatistic oracle projectionReduction limit oracleLimit
        projectionLimit horacle hprojection hprojectionLimit_lt_oracle
        hinverse_meas estimatedScoreToScaledTendsto coverageInput hgc
        (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
          cells referenceShare sample weight score)
        hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
        hdenominator hheterogeneity hresidual hfirst hlocal hgodambe

/--
The fixed-law strict projection-slack GC-backed single-arm PATE two-sided
component-positive route with local expansion and Godambe obligations packaged
as one compact core.
-/
theorem
    pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit_glivenkoCantelli_estimated_score_core
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
      (pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction limit oracleLimit projectionLimit horacle
        hprojection hprojectionLimit_lt_oracle hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    estimatedScoreBridge knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction limit oracleLimit projectionLimit horacle hprojection
    hprojectionLimit_lt_oracle hinverse_meas estimatedScoreToScaledTendsto
    coverageInput hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
    hdenominator hheterogeneity hresidual hfirst
    core.matching_functional_local_expansion core.godambe_variance_identity

/--
The fixed-law strict projection-slack GC-backed single-arm PATE two-sided
component-positive route with local expansion and Godambe obligations packaged
as one compact local-experiment core.
-/
theorem
    pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit_glivenkoCantelli_local_experiment_core
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
    (estimated : EstimatedScoreLocalExperimentInput)
    (core : EstimatedScoreLocalExperimentCore estimated)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity) :
    PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated)
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction limit oracleLimit projectionLimit horacle
        hprojection hprojectionLimit_lt_oracle hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated) knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction limit oracleLimit projectionLimit horacle hprojection
    hprojectionLimit_lt_oracle hinverse_meas estimatedScoreToScaledTendsto
    coverageInput hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
    hdenominator hheterogeneity hresidual hfirst
    ⟨hscore, core.matching_functional_local_derivative,
      core.local_stochastic_equicontinuity⟩
    core.godambe_variance_identity

/-! ## PATT absolute projection_lt_limit -/

/--
The GC-backed single-arm PATT component-positive route yields
absolute positive-variance Wald coverage from strict projection slack and nonnegative target drift.
-/
theorem
    patt_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit_glivenkoCantelli
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hdriftLimit_nonneg : 0 ≤ targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
      (pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) := by
  simpa
    [PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_lt_limit_glivenkoCantelli,
      pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_lt_limit,
      pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_lt_limit,
      estimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit]
    using
      patt_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit
        (pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          cells referenceShare sample weight score indicatorBridge
          finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
          envelopeToScaled indicatorLLNToScaled knownScoreBridge
          scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
          knownScoreToEstimatedScoreInput)
        scaledStatistic oracle projectionReduction targetDrift limit
        oracleLimit projectionLimit targetDriftLimit horacle hprojection
        hdrift hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
        estimatedScoreToScaledTendsto coverageInput hgc
        (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
          cells referenceShare sample weight score)
        hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
        hdenominator hheterogeneity hresidual hfirst hlocal hgodambe

/--
The strict projection-slack GC-backed single-arm PATT absolute
component-positive route with local expansion and Godambe obligations packaged
as one compact core.
-/
theorem
    patt_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit_glivenkoCantelli_estimated_score_core
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hdriftLimit_nonneg : 0 ≤ targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
      (pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  patt_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    estimatedScoreBridge knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction targetDrift limit oracleLimit projectionLimit
    targetDriftLimit horacle hprojection hdrift hprojectionLimit_lt_oracle
    hdriftLimit_nonneg hinverse_meas estimatedScoreToScaledTendsto coverageInput
    hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp hdenominator
    hheterogeneity hresidual hfirst core.matching_functional_local_expansion
    core.godambe_variance_identity

/--
The strict projection-slack GC-backed single-arm PATT absolute
component-positive route with local expansion and Godambe obligations packaged
as one compact local-experiment core.
-/
theorem
    patt_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit_glivenkoCantelli_local_experiment_core
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
    (estimated : EstimatedScoreLocalExperimentInput)
    (core : EstimatedScoreLocalExperimentCore estimated)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hdriftLimit_nonneg : 0 ≤ targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity) :
    PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated)
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  patt_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated) knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction targetDrift limit oracleLimit projectionLimit
    targetDriftLimit horacle hprojection hdrift hprojectionLimit_lt_oracle
    hdriftLimit_nonneg hinverse_meas estimatedScoreToScaledTendsto coverageInput
    hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp hdenominator
    hheterogeneity hresidual hfirst
    ⟨hscore, core.matching_functional_local_derivative,
      core.local_stochastic_equicontinuity⟩
    core.godambe_variance_identity

/-! ## PATT two-sided projection_lt_limit -/

/--
The GC-backed single-arm PATT component-positive route yields
two-sided positive-variance Wald coverage from strict projection slack and nonnegative target drift.
-/
theorem
    patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit_glivenkoCantelli
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hdriftLimit_nonneg : 0 ≤ targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
      (pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) := by
  simpa
    [PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli,
      PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      absoluteWaldCoverageVarianceInput_of_twoSided,
      pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_lt_limit_glivenkoCantelli,
      pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_lt_limit,
      pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_lt_limit,
      estimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit]
    using
      patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit
        (pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          cells referenceShare sample weight score indicatorBridge
          finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
          envelopeToScaled indicatorLLNToScaled knownScoreBridge
          scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
          knownScoreToEstimatedScoreInput)
        scaledStatistic oracle projectionReduction targetDrift limit
        oracleLimit projectionLimit targetDriftLimit horacle hprojection
        hdrift hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
        estimatedScoreToScaledTendsto coverageInput hgc
        (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
          cells referenceShare sample weight score)
        hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
        hdenominator hheterogeneity hresidual hfirst hlocal hgodambe

/--
The strict projection-slack GC-backed single-arm PATT two-sided
component-positive route with local expansion and Godambe obligations packaged
as one compact core.
-/
theorem
    patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit_glivenkoCantelli_estimated_score_core
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hdriftLimit_nonneg : 0 ≤ targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
      (pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    estimatedScoreBridge knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction targetDrift limit oracleLimit projectionLimit
    targetDriftLimit horacle hprojection hdrift hprojectionLimit_lt_oracle
    hdriftLimit_nonneg hinverse_meas estimatedScoreToScaledTendsto coverageInput
    hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp hdenominator
    hheterogeneity hresidual hfirst core.matching_functional_local_expansion
    core.godambe_variance_identity

/--
The strict projection-slack GC-backed single-arm PATT two-sided
component-positive route with local expansion and Godambe obligations packaged
as one compact local-experiment core.
-/
theorem
    patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit_glivenkoCantelli_local_experiment_core
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
    (estimated : EstimatedScoreLocalExperimentInput)
    (core : EstimatedScoreLocalExperimentCore estimated)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hdriftLimit_nonneg : 0 ≤ targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity) :
    PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated)
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated) knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction targetDrift limit oracleLimit projectionLimit
    targetDriftLimit horacle hprojection hdrift hprojectionLimit_lt_oracle
    hdriftLimit_nonneg hinverse_meas estimatedScoreToScaledTendsto coverageInput
    hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp hdenominator
    hheterogeneity hresidual hfirst
    ⟨hscore, core.matching_functional_local_derivative,
      core.local_stochastic_equicontinuity⟩
    core.godambe_variance_identity

/-! ## PATT absolute projection_le_drift_pos_limit -/

/--
The GC-backed single-arm PATT component-positive route yields
absolute positive-variance Wald coverage from weak projection slack and positive target drift.
-/
theorem
    patt_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit_glivenkoCantelli
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_le_oracle : projectionLimit ≤ oracleLimit)
    (hdriftLimit_pos : 0 < targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
      (pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_le_drift_pos_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) := by
  simpa
    [PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_le_drift_pos_limit_glivenkoCantelli,
      pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_le_drift_pos_limit,
      pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_le_drift_pos_limit,
      estimatedScorePositiveVarianceStudentizationInput_of_projection_le_drift_pos_limit]
    using
      patt_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit
        (pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          cells referenceShare sample weight score indicatorBridge
          finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
          envelopeToScaled indicatorLLNToScaled knownScoreBridge
          scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
          knownScoreToEstimatedScoreInput)
        scaledStatistic oracle projectionReduction targetDrift limit
        oracleLimit projectionLimit targetDriftLimit horacle hprojection
        hdrift hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
        estimatedScoreToScaledTendsto coverageInput hgc
        (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
          cells referenceShare sample weight score)
        hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
        hdenominator hheterogeneity hresidual hfirst hlocal hgodambe

/--
The weak projection-slack, positive-drift GC-backed single-arm PATT absolute
component-positive route with local expansion and Godambe obligations packaged
as one compact core.
-/
theorem
    patt_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit_glivenkoCantelli_estimated_score_core
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_le_oracle : projectionLimit ≤ oracleLimit)
    (hdriftLimit_pos : 0 < targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
      (pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_le_drift_pos_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  patt_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    estimatedScoreBridge knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction targetDrift limit oracleLimit projectionLimit
    targetDriftLimit horacle hprojection hdrift hprojectionLimit_le_oracle
    hdriftLimit_pos hinverse_meas estimatedScoreToScaledTendsto coverageInput
    hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp hdenominator
    hheterogeneity hresidual hfirst core.matching_functional_local_expansion
    core.godambe_variance_identity

/--
The weak projection-slack, positive-drift GC-backed single-arm PATT absolute
component-positive route with local expansion and Godambe obligations packaged
as one compact local-experiment core.
-/
theorem
    patt_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit_glivenkoCantelli_local_experiment_core
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
    (estimated : EstimatedScoreLocalExperimentInput)
    (core : EstimatedScoreLocalExperimentCore estimated)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_le_oracle : projectionLimit ≤ oracleLimit)
    (hdriftLimit_pos : 0 < targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity) :
    PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_le_drift_pos_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated)
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  patt_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated) knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction targetDrift limit oracleLimit projectionLimit
    targetDriftLimit horacle hprojection hdrift hprojectionLimit_le_oracle
    hdriftLimit_pos hinverse_meas estimatedScoreToScaledTendsto coverageInput
    hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp hdenominator
    hheterogeneity hresidual hfirst
    ⟨hscore, core.matching_functional_local_derivative,
      core.local_stochastic_equicontinuity⟩
    core.godambe_variance_identity

/-! ## PATT two-sided projection_le_drift_pos_limit -/

/--
The GC-backed single-arm PATT component-positive route yields
two-sided positive-variance Wald coverage from weak projection slack and positive target drift.
-/
theorem
    patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit_glivenkoCantelli
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_le_oracle : projectionLimit ≤ oracleLimit)
    (hdriftLimit_pos : 0 < targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
      (pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_le_drift_pos_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) := by
  simpa
    [PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli,
      PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      absoluteWaldCoverageVarianceInput_of_twoSided,
      pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_le_drift_pos_limit_glivenkoCantelli,
      pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_le_drift_pos_limit,
      pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_le_drift_pos_limit,
      estimatedScorePositiveVarianceStudentizationInput_of_projection_le_drift_pos_limit]
    using
      patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit
        (pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          cells referenceShare sample weight score indicatorBridge
          finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
          envelopeToScaled indicatorLLNToScaled knownScoreBridge
          scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
          knownScoreToEstimatedScoreInput)
        scaledStatistic oracle projectionReduction targetDrift limit
        oracleLimit projectionLimit targetDriftLimit horacle hprojection
        hdrift hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
        estimatedScoreToScaledTendsto coverageInput hgc
        (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
          cells referenceShare sample weight score)
        hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
        hdenominator hheterogeneity hresidual hfirst hlocal hgodambe

/--
The weak projection-slack, positive-drift GC-backed single-arm PATT two-sided
component-positive route with local expansion and Godambe obligations packaged
as one compact core.
-/
theorem
    patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit_glivenkoCantelli_estimated_score_core
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_le_oracle : projectionLimit ≤ oracleLimit)
    (hdriftLimit_pos : 0 < targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
      (pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_le_drift_pos_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    estimatedScoreBridge knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction targetDrift limit oracleLimit projectionLimit
    targetDriftLimit horacle hprojection hdrift hprojectionLimit_le_oracle
    hdriftLimit_pos hinverse_meas estimatedScoreToScaledTendsto coverageInput
    hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp hdenominator
    hheterogeneity hresidual hfirst core.matching_functional_local_expansion
    core.godambe_variance_identity

/--
The weak projection-slack, positive-drift GC-backed single-arm PATT two-sided
component-positive route with local expansion and Godambe obligations packaged
as one compact local-experiment core.
-/
theorem
    patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit_glivenkoCantelli_local_experiment_core
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
    (estimated : EstimatedScoreLocalExperimentInput)
    (core : EstimatedScoreLocalExperimentCore estimated)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_le_oracle : projectionLimit ≤ oracleLimit)
    (hdriftLimit_pos : 0 < targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity) :
    PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_le_drift_pos_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated)
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated) knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction targetDrift limit oracleLimit projectionLimit
    targetDriftLimit horacle hprojection hdrift hprojectionLimit_le_oracle
    hdriftLimit_pos hinverse_meas estimatedScoreToScaledTendsto coverageInput
    hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp hdenominator
    hheterogeneity hresidual hfirst
    ⟨hscore, core.matching_functional_local_derivative,
      core.local_stochastic_equicontinuity⟩
    core.godambe_variance_identity

/-! ## PATT absolute fixedLaw_projection_lt_limit -/

/--
The GC-backed single-arm PATT component-positive route yields
absolute positive-variance Wald coverage from fixed-law strict projection slack.
-/
theorem
    patt_absolutePositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit_glivenkoCantelli
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
      (pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction limit oracleLimit projectionLimit horacle
        hprojection hprojectionLimit_lt_oracle hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) := by
  simpa
    [PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli,
      pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit,
      pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_fixedLaw_projection_lt_limit,
      fixedLawEstimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit]
    using
      patt_absolutePositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit
        (pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          cells referenceShare sample weight score indicatorBridge
          finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
          envelopeToScaled indicatorLLNToScaled knownScoreBridge
          scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
          knownScoreToEstimatedScoreInput)
        scaledStatistic oracle projectionReduction limit oracleLimit
        projectionLimit horacle hprojection hprojectionLimit_lt_oracle
        hinverse_meas estimatedScoreToScaledTendsto coverageInput hgc
        (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
          cells referenceShare sample weight score)
        hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
        hdenominator hheterogeneity hresidual hfirst hlocal hgodambe

/-! ## PATT two-sided fixedLaw_projection_lt_limit -/

/--
The GC-backed single-arm PATT component-positive route yields
two-sided positive-variance Wald coverage from fixed-law strict projection slack.
-/
theorem
    patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit_glivenkoCantelli
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
      (pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction limit oracleLimit projectionLimit horacle
        hprojection hprojectionLimit_lt_oracle hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) := by
  simpa
    [PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli,
      PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      absoluteWaldCoverageVarianceInput_of_twoSided,
      pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli,
      pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit,
      pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_fixedLaw_projection_lt_limit,
      fixedLawEstimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit]
    using
      patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit
        (pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          cells referenceShare sample weight score indicatorBridge
          finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
          envelopeToScaled indicatorLLNToScaled knownScoreBridge
          scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
          knownScoreToEstimatedScoreInput)
        scaledStatistic oracle projectionReduction limit oracleLimit
        projectionLimit horacle hprojection hprojectionLimit_lt_oracle
        hinverse_meas estimatedScoreToScaledTendsto coverageInput hgc
        (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
          cells referenceShare sample weight score)
        hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
        hdenominator hheterogeneity hresidual hfirst hlocal hgodambe

/--
The fixed-law strict projection-slack GC-backed single-arm PATT absolute
component-positive route with local expansion and Godambe obligations packaged
as one compact core.
-/
theorem
    patt_absolutePositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit_glivenkoCantelli_estimated_score_core
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
      (pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction limit oracleLimit projectionLimit horacle
        hprojection hprojectionLimit_lt_oracle hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  patt_absolutePositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    estimatedScoreBridge knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction limit oracleLimit projectionLimit horacle hprojection
    hprojectionLimit_lt_oracle hinverse_meas estimatedScoreToScaledTendsto
    coverageInput hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
    hdenominator hheterogeneity hresidual hfirst
    core.matching_functional_local_expansion core.godambe_variance_identity

/--
The fixed-law strict projection-slack GC-backed single-arm PATT absolute
component-positive route with local expansion and Godambe obligations packaged
as one compact local-experiment core.
-/
theorem
    patt_absolutePositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit_glivenkoCantelli_local_experiment_core
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
    (estimated : EstimatedScoreLocalExperimentInput)
    (core : EstimatedScoreLocalExperimentCore estimated)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity) :
    PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated)
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction limit oracleLimit projectionLimit horacle
        hprojection hprojectionLimit_lt_oracle hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  patt_absolutePositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated) knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction limit oracleLimit projectionLimit horacle hprojection
    hprojectionLimit_lt_oracle hinverse_meas estimatedScoreToScaledTendsto
    coverageInput hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
    hdenominator hheterogeneity hresidual hfirst
    ⟨hscore, core.matching_functional_local_derivative,
      core.local_stochastic_equicontinuity⟩
    core.godambe_variance_identity

/--
The fixed-law strict projection-slack GC-backed single-arm PATT two-sided
component-positive route with local expansion and Godambe obligations packaged
as one compact core.
-/
theorem
    patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit_glivenkoCantelli_estimated_score_core
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
      (pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction limit oracleLimit projectionLimit horacle
        hprojection hprojectionLimit_lt_oracle hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    estimatedScoreBridge knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction limit oracleLimit projectionLimit horacle hprojection
    hprojectionLimit_lt_oracle hinverse_meas estimatedScoreToScaledTendsto
    coverageInput hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
    hdenominator hheterogeneity hresidual hfirst
    core.matching_functional_local_expansion core.godambe_variance_identity

/--
The fixed-law strict projection-slack GC-backed single-arm PATT two-sided
component-positive route with local expansion and Godambe obligations packaged
as one compact local-experiment core.
-/
theorem
    patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit_glivenkoCantelli_local_experiment_core
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
    (estimated : EstimatedScoreLocalExperimentInput)
    (core : EstimatedScoreLocalExperimentCore estimated)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity) :
    PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated)
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction limit oracleLimit projectionLimit horacle
        hprojection hprojectionLimit_lt_oracle hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated) knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction limit oracleLimit projectionLimit horacle hprojection
    hprojectionLimit_lt_oracle hinverse_meas estimatedScoreToScaledTendsto
    coverageInput hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
    hdenominator hheterogeneity hresidual hfirst
    ⟨hscore, core.matching_functional_local_derivative,
      core.local_stochastic_equicontinuity⟩
    core.godambe_variance_identity


/-! ## Cross-calibrated coverage wrappers -/

/-! ## Cross-calibrated PATE two-sided from absolute projection_lt_limit -/

/--
The GC-backed single-arm PATE component-positive route yields
two-sided positive-variance Wald coverage from absolute variance-based
calibration inputs and strict projection slack and nonnegative target drift.
-/
theorem
    pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_lt_limit_glivenkoCantelli
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hdriftLimit_nonneg : 0 ≤ targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) := by
  simpa
    [PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli,
      PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_lt_limit_glivenkoCantelli,
      pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_lt_limit,
      pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_lt_limit,
      estimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit,
      twoSidedWaldCoverageVarianceInput_of_absolute,
      absoluteWaldCoverageVarianceInput_of_twoSided]
    using
      pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_lt_limit
        (pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          cells referenceShare sample weight score indicatorBridge
          finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
          envelopeToScaled indicatorLLNToScaled knownScoreBridge
          scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
          knownScoreToEstimatedScoreInput)
        scaledStatistic oracle projectionReduction targetDrift limit
        oracleLimit projectionLimit targetDriftLimit horacle hprojection
        hdrift hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
        estimatedScoreToScaledTendsto coverageInput hgc
        (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
          cells referenceShare sample weight score)
        hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
        hdenominator hheterogeneity hresidual hfirst hlocal hgodambe

/-! ## Cross-calibrated PATE absolute from two-sided projection_lt_limit -/

/--
The GC-backed single-arm PATE component-positive route yields
absolute positive-variance Wald coverage from two-sided variance-based
calibration inputs and strict projection slack and nonnegative target drift.
-/
theorem
    pate_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_lt_limit_glivenkoCantelli
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hdriftLimit_nonneg : 0 ≤ targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) := by
  simpa
    [PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_lt_limit_glivenkoCantelli,
      pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_lt_limit,
      pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_lt_limit,
      estimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit,
      twoSidedWaldCoverageVarianceInput_of_absolute,
      absoluteWaldCoverageVarianceInput_of_twoSided]
    using
      pate_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_lt_limit
        (pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          cells referenceShare sample weight score indicatorBridge
          finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
          envelopeToScaled indicatorLLNToScaled knownScoreBridge
          scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
          knownScoreToEstimatedScoreInput)
        scaledStatistic oracle projectionReduction targetDrift limit
        oracleLimit projectionLimit targetDriftLimit horacle hprojection
        hdrift hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
        estimatedScoreToScaledTendsto coverageInput hgc
        (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
          cells referenceShare sample weight score)
        hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
        hdenominator hheterogeneity hresidual hfirst hlocal hgodambe

/--
The strict projection-slack GC-backed single-arm PATE cross-calibrated route
from absolute calibration to two-sided component-positive coverage with local
expansion and Godambe obligations packaged as one compact core.
-/
theorem
    pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_lt_limit_glivenkoCantelli_estimated_score_core
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hdriftLimit_nonneg : 0 ≤ targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    estimatedScoreBridge knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction targetDrift limit oracleLimit projectionLimit
    targetDriftLimit horacle hprojection hdrift hprojectionLimit_lt_oracle
    hdriftLimit_nonneg hinverse_meas estimatedScoreToScaledTendsto
    coverageInput hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
    hdenominator hheterogeneity hresidual hfirst
    core.matching_functional_local_expansion core.godambe_variance_identity

/--
The strict projection-slack GC-backed single-arm PATE cross-calibrated route
from absolute calibration to two-sided component-positive coverage with local
expansion and Godambe obligations packaged as one compact local-experiment
core.
-/
theorem
    pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_lt_limit_glivenkoCantelli_local_experiment_core
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
    (estimated : EstimatedScoreLocalExperimentInput)
    (core : EstimatedScoreLocalExperimentCore estimated)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hdriftLimit_nonneg : 0 ≤ targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity) :
    PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated)
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated) knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction targetDrift limit oracleLimit projectionLimit
    targetDriftLimit horacle hprojection hdrift hprojectionLimit_lt_oracle
    hdriftLimit_nonneg hinverse_meas estimatedScoreToScaledTendsto
    coverageInput hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
    hdenominator hheterogeneity hresidual hfirst
    ⟨hscore, core.matching_functional_local_derivative,
      core.local_stochastic_equicontinuity⟩
    core.godambe_variance_identity

/--
The strict projection-slack GC-backed single-arm PATE cross-calibrated route
from two-sided calibration to absolute component-positive coverage with local
expansion and Godambe obligations packaged as one compact core.
-/
theorem
    pate_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_lt_limit_glivenkoCantelli_estimated_score_core
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hdriftLimit_nonneg : 0 ≤ targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  pate_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    estimatedScoreBridge knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction targetDrift limit oracleLimit projectionLimit
    targetDriftLimit horacle hprojection hdrift hprojectionLimit_lt_oracle
    hdriftLimit_nonneg hinverse_meas estimatedScoreToScaledTendsto
    coverageInput hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
    hdenominator hheterogeneity hresidual hfirst
    core.matching_functional_local_expansion core.godambe_variance_identity

/--
The strict projection-slack GC-backed single-arm PATE cross-calibrated route
from two-sided calibration to absolute component-positive coverage with local
expansion and Godambe obligations packaged as one compact local-experiment
core.
-/
theorem
    pate_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_lt_limit_glivenkoCantelli_local_experiment_core
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
    (estimated : EstimatedScoreLocalExperimentInput)
    (core : EstimatedScoreLocalExperimentCore estimated)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hdriftLimit_nonneg : 0 ≤ targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity) :
    PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated)
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  pate_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated) knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction targetDrift limit oracleLimit projectionLimit
    targetDriftLimit horacle hprojection hdrift hprojectionLimit_lt_oracle
    hdriftLimit_nonneg hinverse_meas estimatedScoreToScaledTendsto
    coverageInput hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
    hdenominator hheterogeneity hresidual hfirst
    ⟨hscore, core.matching_functional_local_derivative,
      core.local_stochastic_equicontinuity⟩
    core.godambe_variance_identity

/-! ## Cross-calibrated PATE two-sided from absolute projection_le_drift_pos_limit -/

/--
The GC-backed single-arm PATE component-positive route yields
two-sided positive-variance Wald coverage from absolute variance-based
calibration inputs and weak projection slack and positive target drift.
-/
theorem
    pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_le_drift_pos_limit_glivenkoCantelli
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_le_oracle : projectionLimit ≤ oracleLimit)
    (hdriftLimit_pos : 0 < targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_le_drift_pos_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) := by
  simpa
    [PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli,
      PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_le_drift_pos_limit_glivenkoCantelli,
      pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_le_drift_pos_limit,
      pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_le_drift_pos_limit,
      estimatedScorePositiveVarianceStudentizationInput_of_projection_le_drift_pos_limit,
      twoSidedWaldCoverageVarianceInput_of_absolute,
      absoluteWaldCoverageVarianceInput_of_twoSided]
    using
      pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_le_drift_pos_limit
        (pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          cells referenceShare sample weight score indicatorBridge
          finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
          envelopeToScaled indicatorLLNToScaled knownScoreBridge
          scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
          knownScoreToEstimatedScoreInput)
        scaledStatistic oracle projectionReduction targetDrift limit
        oracleLimit projectionLimit targetDriftLimit horacle hprojection
        hdrift hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
        estimatedScoreToScaledTendsto coverageInput hgc
        (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
          cells referenceShare sample weight score)
        hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
        hdenominator hheterogeneity hresidual hfirst hlocal hgodambe

/-! ## Cross-calibrated PATE absolute from two-sided projection_le_drift_pos_limit -/

/--
The GC-backed single-arm PATE component-positive route yields
absolute positive-variance Wald coverage from two-sided variance-based
calibration inputs and weak projection slack and positive target drift.
-/
theorem
    pate_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_le_drift_pos_limit_glivenkoCantelli
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_le_oracle : projectionLimit ≤ oracleLimit)
    (hdriftLimit_pos : 0 < targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_le_drift_pos_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) := by
  simpa
    [PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_le_drift_pos_limit_glivenkoCantelli,
      pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_le_drift_pos_limit,
      pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_le_drift_pos_limit,
      estimatedScorePositiveVarianceStudentizationInput_of_projection_le_drift_pos_limit,
      twoSidedWaldCoverageVarianceInput_of_absolute,
      absoluteWaldCoverageVarianceInput_of_twoSided]
    using
      pate_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_le_drift_pos_limit
        (pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          cells referenceShare sample weight score indicatorBridge
          finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
          envelopeToScaled indicatorLLNToScaled knownScoreBridge
          scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
          knownScoreToEstimatedScoreInput)
        scaledStatistic oracle projectionReduction targetDrift limit
        oracleLimit projectionLimit targetDriftLimit horacle hprojection
        hdrift hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
        estimatedScoreToScaledTendsto coverageInput hgc
        (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
          cells referenceShare sample weight score)
        hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
        hdenominator hheterogeneity hresidual hfirst hlocal hgodambe

/--
The weak projection-slack positive-drift GC-backed single-arm PATE
cross-calibrated route from absolute calibration to two-sided
component-positive coverage with local expansion and Godambe obligations
packaged as one compact core.
-/
theorem
    pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_le_drift_pos_limit_glivenkoCantelli_estimated_score_core
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_le_oracle : projectionLimit ≤ oracleLimit)
    (hdriftLimit_pos : 0 < targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_le_drift_pos_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_le_drift_pos_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    estimatedScoreBridge knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction targetDrift limit oracleLimit projectionLimit
    targetDriftLimit horacle hprojection hdrift hprojectionLimit_le_oracle
    hdriftLimit_pos hinverse_meas estimatedScoreToScaledTendsto coverageInput
    hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp hdenominator
    hheterogeneity hresidual hfirst core.matching_functional_local_expansion
    core.godambe_variance_identity

/--
The weak projection-slack positive-drift GC-backed single-arm PATE
cross-calibrated route from absolute calibration to two-sided
component-positive coverage with local expansion and Godambe obligations
packaged as one compact local-experiment core.
-/
theorem
    pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_le_drift_pos_limit_glivenkoCantelli_local_experiment_core
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
    (estimated : EstimatedScoreLocalExperimentInput)
    (core : EstimatedScoreLocalExperimentCore estimated)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_le_oracle : projectionLimit ≤ oracleLimit)
    (hdriftLimit_pos : 0 < targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity) :
    PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_le_drift_pos_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated)
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_le_drift_pos_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated) knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction targetDrift limit oracleLimit projectionLimit
    targetDriftLimit horacle hprojection hdrift hprojectionLimit_le_oracle
    hdriftLimit_pos hinverse_meas estimatedScoreToScaledTendsto coverageInput
    hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp hdenominator
    hheterogeneity hresidual hfirst
    ⟨hscore, core.matching_functional_local_derivative,
      core.local_stochastic_equicontinuity⟩
    core.godambe_variance_identity

/--
The weak projection-slack positive-drift GC-backed single-arm PATE
cross-calibrated route from two-sided calibration to absolute
component-positive coverage with local expansion and Godambe obligations
packaged as one compact core.
-/
theorem
    pate_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_le_drift_pos_limit_glivenkoCantelli_estimated_score_core
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_le_oracle : projectionLimit ≤ oracleLimit)
    (hdriftLimit_pos : 0 < targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_le_drift_pos_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  pate_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_le_drift_pos_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    estimatedScoreBridge knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction targetDrift limit oracleLimit projectionLimit
    targetDriftLimit horacle hprojection hdrift hprojectionLimit_le_oracle
    hdriftLimit_pos hinverse_meas estimatedScoreToScaledTendsto coverageInput
    hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp hdenominator
    hheterogeneity hresidual hfirst core.matching_functional_local_expansion
    core.godambe_variance_identity

/--
The weak projection-slack positive-drift GC-backed single-arm PATE
cross-calibrated route from two-sided calibration to absolute
component-positive coverage with local expansion and Godambe obligations
packaged as one compact local-experiment core.
-/
theorem
    pate_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_le_drift_pos_limit_glivenkoCantelli_local_experiment_core
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
    (estimated : EstimatedScoreLocalExperimentInput)
    (core : EstimatedScoreLocalExperimentCore estimated)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_le_oracle : projectionLimit ≤ oracleLimit)
    (hdriftLimit_pos : 0 < targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity) :
    PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_le_drift_pos_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated)
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  pate_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_le_drift_pos_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated) knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction targetDrift limit oracleLimit projectionLimit
    targetDriftLimit horacle hprojection hdrift hprojectionLimit_le_oracle
    hdriftLimit_pos hinverse_meas estimatedScoreToScaledTendsto coverageInput
    hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp hdenominator
    hheterogeneity hresidual hfirst
    ⟨hscore, core.matching_functional_local_derivative,
      core.local_stochastic_equicontinuity⟩
    core.godambe_variance_identity

/-! ## Cross-calibrated PATE two-sided from absolute fixedLaw_projection_lt_limit -/

/--
The GC-backed single-arm PATE component-positive route yields
two-sided positive-variance Wald coverage from absolute variance-based
calibration inputs and fixed-law strict projection slack.
-/
theorem
    pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_fixedLaw_projection_lt_limit_glivenkoCantelli
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_fixedLaw_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction limit oracleLimit projectionLimit horacle
        hprojection hprojectionLimit_lt_oracle hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) := by
  simpa
    [PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli,
      PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_fixedLaw_projection_lt_limit_glivenkoCantelli,
      pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_fixedLaw_projection_lt_limit,
      pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_fixedLaw_projection_lt_limit,
      fixedLawEstimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit,
      twoSidedWaldCoverageVarianceInput_of_absolute,
      absoluteWaldCoverageVarianceInput_of_twoSided]
    using
      pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_fixedLaw_projection_lt_limit
        (pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          cells referenceShare sample weight score indicatorBridge
          finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
          envelopeToScaled indicatorLLNToScaled knownScoreBridge
          scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
          knownScoreToEstimatedScoreInput)
        scaledStatistic oracle projectionReduction limit oracleLimit
        projectionLimit horacle hprojection hprojectionLimit_lt_oracle
        hinverse_meas estimatedScoreToScaledTendsto coverageInput hgc
        (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
          cells referenceShare sample weight score)
        hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
        hdenominator hheterogeneity hresidual hfirst hlocal hgodambe

/-! ## Cross-calibrated PATE absolute from two-sided fixedLaw_projection_lt_limit -/

/--
The GC-backed single-arm PATE component-positive route yields
absolute positive-variance Wald coverage from two-sided variance-based
calibration inputs and fixed-law strict projection slack.
-/
theorem
    pate_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_fixedLaw_projection_lt_limit_glivenkoCantelli
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_fixedLaw_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction limit oracleLimit projectionLimit horacle
        hprojection hprojectionLimit_lt_oracle hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) := by
  simpa
    [PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_fixedLaw_projection_lt_limit_glivenkoCantelli,
      pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_fixedLaw_projection_lt_limit,
      pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_fixedLaw_projection_lt_limit,
      fixedLawEstimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit,
      twoSidedWaldCoverageVarianceInput_of_absolute,
      absoluteWaldCoverageVarianceInput_of_twoSided]
    using
      pate_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_fixedLaw_projection_lt_limit
        (pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          cells referenceShare sample weight score indicatorBridge
          finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
          envelopeToScaled indicatorLLNToScaled knownScoreBridge
          scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
          knownScoreToEstimatedScoreInput)
        scaledStatistic oracle projectionReduction limit oracleLimit
        projectionLimit horacle hprojection hprojectionLimit_lt_oracle
        hinverse_meas estimatedScoreToScaledTendsto coverageInput hgc
        (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
          cells referenceShare sample weight score)
        hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
        hdenominator hheterogeneity hresidual hfirst hlocal hgodambe

/--
The fixed-law strict projection-slack GC-backed single-arm PATE
cross-calibrated route from absolute calibration to two-sided
component-positive coverage with local expansion and Godambe obligations
packaged as one compact core.
-/
theorem
    pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_fixedLaw_projection_lt_limit_glivenkoCantelli_estimated_score_core
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_fixedLaw_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction limit oracleLimit projectionLimit horacle
        hprojection hprojectionLimit_lt_oracle hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_fixedLaw_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    estimatedScoreBridge knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction limit oracleLimit projectionLimit horacle hprojection
    hprojectionLimit_lt_oracle hinverse_meas estimatedScoreToScaledTendsto
    coverageInput hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
    hdenominator hheterogeneity hresidual hfirst
    core.matching_functional_local_expansion core.godambe_variance_identity

/--
The fixed-law strict projection-slack GC-backed single-arm PATE
cross-calibrated route from absolute calibration to two-sided
component-positive coverage with local expansion and Godambe obligations
packaged as one compact local-experiment core.
-/
theorem
    pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_fixedLaw_projection_lt_limit_glivenkoCantelli_local_experiment_core
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
    (estimated : EstimatedScoreLocalExperimentInput)
    (core : EstimatedScoreLocalExperimentCore estimated)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity) :
    PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_fixedLaw_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated)
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction limit oracleLimit projectionLimit horacle
        hprojection hprojectionLimit_lt_oracle hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_fixedLaw_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated) knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction limit oracleLimit projectionLimit horacle hprojection
    hprojectionLimit_lt_oracle hinverse_meas estimatedScoreToScaledTendsto
    coverageInput hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
    hdenominator hheterogeneity hresidual hfirst
    ⟨hscore, core.matching_functional_local_derivative,
      core.local_stochastic_equicontinuity⟩
    core.godambe_variance_identity

/--
The fixed-law strict projection-slack GC-backed single-arm PATE
cross-calibrated route from two-sided calibration to absolute
component-positive coverage with local expansion and Godambe obligations
packaged as one compact core.
-/
theorem
    pate_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_fixedLaw_projection_lt_limit_glivenkoCantelli_estimated_score_core
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_fixedLaw_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction limit oracleLimit projectionLimit horacle
        hprojection hprojectionLimit_lt_oracle hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  pate_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_fixedLaw_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    estimatedScoreBridge knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction limit oracleLimit projectionLimit horacle hprojection
    hprojectionLimit_lt_oracle hinverse_meas estimatedScoreToScaledTendsto
    coverageInput hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
    hdenominator hheterogeneity hresidual hfirst
    core.matching_functional_local_expansion core.godambe_variance_identity

/--
The fixed-law strict projection-slack GC-backed single-arm PATE
cross-calibrated route from two-sided calibration to absolute
component-positive coverage with local expansion and Godambe obligations
packaged as one compact local-experiment core.
-/
theorem
    pate_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_fixedLaw_projection_lt_limit_glivenkoCantelli_local_experiment_core
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
    (estimated : EstimatedScoreLocalExperimentInput)
    (core : EstimatedScoreLocalExperimentCore estimated)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity) :
    PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_fixedLaw_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated)
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction limit oracleLimit projectionLimit horacle
        hprojection hprojectionLimit_lt_oracle hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  pate_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_fixedLaw_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated) knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction limit oracleLimit projectionLimit horacle hprojection
    hprojectionLimit_lt_oracle hinverse_meas estimatedScoreToScaledTendsto
    coverageInput hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
    hdenominator hheterogeneity hresidual hfirst
    ⟨hscore, core.matching_functional_local_derivative,
      core.local_stochastic_equicontinuity⟩
    core.godambe_variance_identity

/-! ## Cross-calibrated PATT two-sided from absolute projection_lt_limit -/

/--
The GC-backed single-arm PATT component-positive route yields
two-sided positive-variance Wald coverage from absolute variance-based
calibration inputs and strict projection slack and nonnegative target drift.
-/
theorem
    patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_lt_limit_glivenkoCantelli
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hdriftLimit_nonneg : 0 ≤ targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) := by
  simpa
    [PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli,
      PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_lt_limit_glivenkoCantelli,
      pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_lt_limit,
      pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_lt_limit,
      estimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit,
      twoSidedWaldCoverageVarianceInput_of_absolute,
      absoluteWaldCoverageVarianceInput_of_twoSided]
    using
      patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_lt_limit
        (pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          cells referenceShare sample weight score indicatorBridge
          finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
          envelopeToScaled indicatorLLNToScaled knownScoreBridge
          scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
          knownScoreToEstimatedScoreInput)
        scaledStatistic oracle projectionReduction targetDrift limit
        oracleLimit projectionLimit targetDriftLimit horacle hprojection
        hdrift hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
        estimatedScoreToScaledTendsto coverageInput hgc
        (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
          cells referenceShare sample weight score)
        hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
        hdenominator hheterogeneity hresidual hfirst hlocal hgodambe

/-! ## Cross-calibrated PATT absolute from two-sided projection_lt_limit -/

/--
The GC-backed single-arm PATT component-positive route yields
absolute positive-variance Wald coverage from two-sided variance-based
calibration inputs and strict projection slack and nonnegative target drift.
-/
theorem
    patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_lt_limit_glivenkoCantelli
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hdriftLimit_nonneg : 0 ≤ targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) := by
  simpa
    [PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_lt_limit_glivenkoCantelli,
      pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_lt_limit,
      pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_lt_limit,
      estimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit,
      twoSidedWaldCoverageVarianceInput_of_absolute,
      absoluteWaldCoverageVarianceInput_of_twoSided]
    using
      patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_lt_limit
        (pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          cells referenceShare sample weight score indicatorBridge
          finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
          envelopeToScaled indicatorLLNToScaled knownScoreBridge
          scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
          knownScoreToEstimatedScoreInput)
        scaledStatistic oracle projectionReduction targetDrift limit
        oracleLimit projectionLimit targetDriftLimit horacle hprojection
        hdrift hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
        estimatedScoreToScaledTendsto coverageInput hgc
        (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
          cells referenceShare sample weight score)
        hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
        hdenominator hheterogeneity hresidual hfirst hlocal hgodambe

/--
The strict projection-slack GC-backed single-arm PATT cross-calibrated route
from absolute calibration to two-sided component-positive coverage with local
expansion and Godambe obligations packaged as one compact core.
-/
theorem
    patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_lt_limit_glivenkoCantelli_estimated_score_core
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hdriftLimit_nonneg : 0 ≤ targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    estimatedScoreBridge knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction targetDrift limit oracleLimit projectionLimit
    targetDriftLimit horacle hprojection hdrift hprojectionLimit_lt_oracle
    hdriftLimit_nonneg hinverse_meas estimatedScoreToScaledTendsto
    coverageInput hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
    hdenominator hheterogeneity hresidual hfirst
    core.matching_functional_local_expansion core.godambe_variance_identity

/--
The strict projection-slack GC-backed single-arm PATT cross-calibrated route
from absolute calibration to two-sided component-positive coverage with local
expansion and Godambe obligations packaged as one compact local-experiment
core.
-/
theorem
    patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_lt_limit_glivenkoCantelli_local_experiment_core
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
    (estimated : EstimatedScoreLocalExperimentInput)
    (core : EstimatedScoreLocalExperimentCore estimated)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hdriftLimit_nonneg : 0 ≤ targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity) :
    PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated)
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated) knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction targetDrift limit oracleLimit projectionLimit
    targetDriftLimit horacle hprojection hdrift hprojectionLimit_lt_oracle
    hdriftLimit_nonneg hinverse_meas estimatedScoreToScaledTendsto
    coverageInput hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
    hdenominator hheterogeneity hresidual hfirst
    ⟨hscore, core.matching_functional_local_derivative,
      core.local_stochastic_equicontinuity⟩
    core.godambe_variance_identity

/--
The strict projection-slack GC-backed single-arm PATT cross-calibrated route
from two-sided calibration to absolute component-positive coverage with local
expansion and Godambe obligations packaged as one compact core.
-/
theorem
    patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_lt_limit_glivenkoCantelli_estimated_score_core
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hdriftLimit_nonneg : 0 ≤ targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    estimatedScoreBridge knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction targetDrift limit oracleLimit projectionLimit
    targetDriftLimit horacle hprojection hdrift hprojectionLimit_lt_oracle
    hdriftLimit_nonneg hinverse_meas estimatedScoreToScaledTendsto
    coverageInput hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
    hdenominator hheterogeneity hresidual hfirst
    core.matching_functional_local_expansion core.godambe_variance_identity

/--
The strict projection-slack GC-backed single-arm PATT cross-calibrated route
from two-sided calibration to absolute component-positive coverage with local
expansion and Godambe obligations packaged as one compact local-experiment
core.
-/
theorem
    patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_lt_limit_glivenkoCantelli_local_experiment_core
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
    (estimated : EstimatedScoreLocalExperimentInput)
    (core : EstimatedScoreLocalExperimentCore estimated)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hdriftLimit_nonneg : 0 ≤ targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity) :
    PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated)
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated) knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction targetDrift limit oracleLimit projectionLimit
    targetDriftLimit horacle hprojection hdrift hprojectionLimit_lt_oracle
    hdriftLimit_nonneg hinverse_meas estimatedScoreToScaledTendsto
    coverageInput hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
    hdenominator hheterogeneity hresidual hfirst
    ⟨hscore, core.matching_functional_local_derivative,
      core.local_stochastic_equicontinuity⟩
    core.godambe_variance_identity

/-! ## Cross-calibrated PATT two-sided from absolute projection_le_drift_pos_limit -/

/--
The GC-backed single-arm PATT component-positive route yields
two-sided positive-variance Wald coverage from absolute variance-based
calibration inputs and weak projection slack and positive target drift.
-/
theorem
    patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_le_drift_pos_limit_glivenkoCantelli
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_le_oracle : projectionLimit ≤ oracleLimit)
    (hdriftLimit_pos : 0 < targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_le_drift_pos_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) := by
  simpa
    [PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli,
      PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_le_drift_pos_limit_glivenkoCantelli,
      pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_le_drift_pos_limit,
      pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_le_drift_pos_limit,
      estimatedScorePositiveVarianceStudentizationInput_of_projection_le_drift_pos_limit,
      twoSidedWaldCoverageVarianceInput_of_absolute,
      absoluteWaldCoverageVarianceInput_of_twoSided]
    using
      patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_le_drift_pos_limit
        (pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          cells referenceShare sample weight score indicatorBridge
          finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
          envelopeToScaled indicatorLLNToScaled knownScoreBridge
          scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
          knownScoreToEstimatedScoreInput)
        scaledStatistic oracle projectionReduction targetDrift limit
        oracleLimit projectionLimit targetDriftLimit horacle hprojection
        hdrift hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
        estimatedScoreToScaledTendsto coverageInput hgc
        (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
          cells referenceShare sample weight score)
        hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
        hdenominator hheterogeneity hresidual hfirst hlocal hgodambe

/-! ## Cross-calibrated PATT absolute from two-sided projection_le_drift_pos_limit -/

/--
The GC-backed single-arm PATT component-positive route yields
absolute positive-variance Wald coverage from two-sided variance-based
calibration inputs and weak projection slack and positive target drift.
-/
theorem
    patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_le_drift_pos_limit_glivenkoCantelli
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_le_oracle : projectionLimit ≤ oracleLimit)
    (hdriftLimit_pos : 0 < targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_le_drift_pos_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) := by
  simpa
    [PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_le_drift_pos_limit_glivenkoCantelli,
      pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_le_drift_pos_limit,
      pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_le_drift_pos_limit,
      estimatedScorePositiveVarianceStudentizationInput_of_projection_le_drift_pos_limit,
      twoSidedWaldCoverageVarianceInput_of_absolute,
      absoluteWaldCoverageVarianceInput_of_twoSided]
    using
      patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_le_drift_pos_limit
        (pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          cells referenceShare sample weight score indicatorBridge
          finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
          envelopeToScaled indicatorLLNToScaled knownScoreBridge
          scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
          knownScoreToEstimatedScoreInput)
        scaledStatistic oracle projectionReduction targetDrift limit
        oracleLimit projectionLimit targetDriftLimit horacle hprojection
        hdrift hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
        estimatedScoreToScaledTendsto coverageInput hgc
        (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
          cells referenceShare sample weight score)
        hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
        hdenominator hheterogeneity hresidual hfirst hlocal hgodambe

/--
The weak projection-slack positive-drift GC-backed single-arm PATT
cross-calibrated route from absolute calibration to two-sided
component-positive coverage with local expansion and Godambe obligations
packaged as one compact core.
-/
theorem
    patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_le_drift_pos_limit_glivenkoCantelli_estimated_score_core
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_le_oracle : projectionLimit ≤ oracleLimit)
    (hdriftLimit_pos : 0 < targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_le_drift_pos_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_le_drift_pos_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    estimatedScoreBridge knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction targetDrift limit oracleLimit projectionLimit
    targetDriftLimit horacle hprojection hdrift hprojectionLimit_le_oracle
    hdriftLimit_pos hinverse_meas estimatedScoreToScaledTendsto coverageInput
    hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp hdenominator
    hheterogeneity hresidual hfirst core.matching_functional_local_expansion
    core.godambe_variance_identity

/--
The weak projection-slack positive-drift GC-backed single-arm PATT
cross-calibrated route from absolute calibration to two-sided
component-positive coverage with local expansion and Godambe obligations
packaged as one compact local-experiment core.
-/
theorem
    patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_le_drift_pos_limit_glivenkoCantelli_local_experiment_core
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
    (estimated : EstimatedScoreLocalExperimentInput)
    (core : EstimatedScoreLocalExperimentCore estimated)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_le_oracle : projectionLimit ≤ oracleLimit)
    (hdriftLimit_pos : 0 < targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity) :
    PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_le_drift_pos_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated)
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_le_drift_pos_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated) knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction targetDrift limit oracleLimit projectionLimit
    targetDriftLimit horacle hprojection hdrift hprojectionLimit_le_oracle
    hdriftLimit_pos hinverse_meas estimatedScoreToScaledTendsto coverageInput
    hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp hdenominator
    hheterogeneity hresidual hfirst
    ⟨hscore, core.matching_functional_local_derivative,
      core.local_stochastic_equicontinuity⟩
    core.godambe_variance_identity

/--
The weak projection-slack positive-drift GC-backed single-arm PATT
cross-calibrated route from two-sided calibration to absolute
component-positive coverage with local expansion and Godambe obligations
packaged as one compact core.
-/
theorem
    patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_le_drift_pos_limit_glivenkoCantelli_estimated_score_core
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_le_oracle : projectionLimit ≤ oracleLimit)
    (hdriftLimit_pos : 0 < targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_le_drift_pos_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_le_drift_pos_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    estimatedScoreBridge knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction targetDrift limit oracleLimit projectionLimit
    targetDriftLimit horacle hprojection hdrift hprojectionLimit_le_oracle
    hdriftLimit_pos hinverse_meas estimatedScoreToScaledTendsto coverageInput
    hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp hdenominator
    hheterogeneity hresidual hfirst core.matching_functional_local_expansion
    core.godambe_variance_identity

/--
The weak projection-slack positive-drift GC-backed single-arm PATT
cross-calibrated route from two-sided calibration to absolute
component-positive coverage with local expansion and Godambe obligations
packaged as one compact local-experiment core.
-/
theorem
    patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_le_drift_pos_limit_glivenkoCantelli_local_experiment_core
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
    (estimated : EstimatedScoreLocalExperimentInput)
    (core : EstimatedScoreLocalExperimentCore estimated)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction targetDrift : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit targetDriftLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hdrift :
      TendstoInMeasure sampleLaw targetDrift l
        (fun _sample => targetDriftLimit))
    (hprojectionLimit_le_oracle : projectionLimit ≤ oracleLimit)
    (hdriftLimit_pos : 0 < targetDriftLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample)
                (targetDrift index sample)))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity) :
    PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_le_drift_pos_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated)
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction targetDrift limit oracleLimit projectionLimit
        targetDriftLimit horacle hprojection hdrift
        hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_le_drift_pos_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated) knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction targetDrift limit oracleLimit projectionLimit
    targetDriftLimit horacle hprojection hdrift hprojectionLimit_le_oracle
    hdriftLimit_pos hinverse_meas estimatedScoreToScaledTendsto coverageInput
    hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp hdenominator
    hheterogeneity hresidual hfirst
    ⟨hscore, core.matching_functional_local_derivative,
      core.local_stochastic_equicontinuity⟩
    core.godambe_variance_identity

/-! ## Cross-calibrated PATT two-sided from absolute fixedLaw_projection_lt_limit -/

/--
The GC-backed single-arm PATT component-positive route yields
two-sided positive-variance Wald coverage from absolute variance-based
calibration inputs and fixed-law strict projection slack.
-/
theorem
    patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_fixedLaw_projection_lt_limit_glivenkoCantelli
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_fixedLaw_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction limit oracleLimit projectionLimit horacle
        hprojection hprojectionLimit_lt_oracle hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) := by
  simpa
    [PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli,
      PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_fixedLaw_projection_lt_limit_glivenkoCantelli,
      pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_fixedLaw_projection_lt_limit,
      pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_fixedLaw_projection_lt_limit,
      fixedLawEstimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit,
      twoSidedWaldCoverageVarianceInput_of_absolute,
      absoluteWaldCoverageVarianceInput_of_twoSided]
    using
      patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_fixedLaw_projection_lt_limit
        (pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          cells referenceShare sample weight score indicatorBridge
          finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
          envelopeToScaled indicatorLLNToScaled knownScoreBridge
          scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
          knownScoreToEstimatedScoreInput)
        scaledStatistic oracle projectionReduction limit oracleLimit
        projectionLimit horacle hprojection hprojectionLimit_lt_oracle
        hinverse_meas estimatedScoreToScaledTendsto coverageInput hgc
        (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
          cells referenceShare sample weight score)
        hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
        hdenominator hheterogeneity hresidual hfirst hlocal hgodambe

/-! ## Cross-calibrated PATT absolute from two-sided fixedLaw_projection_lt_limit -/

/--
The GC-backed single-arm PATT component-positive route yields
absolute positive-variance Wald coverage from two-sided variance-based
calibration inputs and fixed-law strict projection slack.
-/
theorem
    patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_fixedLaw_projection_lt_limit_glivenkoCantelli
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_fixedLaw_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction limit oracleLimit projectionLimit horacle
        hprojection hprojectionLimit_lt_oracle hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) := by
  simpa
    [PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli,
      pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_fixedLaw_projection_lt_limit_glivenkoCantelli,
      pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_fixedLaw_projection_lt_limit,
      pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_fixedLaw_projection_lt_limit,
      fixedLawEstimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit,
      twoSidedWaldCoverageVarianceInput_of_absolute,
      absoluteWaldCoverageVarianceInput_of_twoSided]
    using
      patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_fixedLaw_projection_lt_limit
        (pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          cells referenceShare sample weight score indicatorBridge
          finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
          envelopeToScaled indicatorLLNToScaled knownScoreBridge
          scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
          knownScoreToEstimatedScoreInput)
        scaledStatistic oracle projectionReduction limit oracleLimit
        projectionLimit horacle hprojection hprojectionLimit_lt_oracle
        hinverse_meas estimatedScoreToScaledTendsto coverageInput hgc
        (bounded_score_cell_indicators_of_glivenkoCantelli_bridge
          cells referenceShare sample weight score)
        hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
        hdenominator hheterogeneity hresidual hfirst hlocal hgodambe

/--
The fixed-law strict projection-slack GC-backed single-arm PATT
cross-calibrated route from absolute calibration to two-sided
component-positive coverage with local expansion and Godambe obligations
packaged as one compact core.
-/
theorem
    patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_fixedLaw_projection_lt_limit_glivenkoCantelli_estimated_score_core
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_fixedLaw_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction limit oracleLimit projectionLimit horacle
        hprojection hprojectionLimit_lt_oracle hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_fixedLaw_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    estimatedScoreBridge knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction limit oracleLimit projectionLimit horacle hprojection
    hprojectionLimit_lt_oracle hinverse_meas estimatedScoreToScaledTendsto
    coverageInput hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
    hdenominator hheterogeneity hresidual hfirst
    core.matching_functional_local_expansion core.godambe_variance_identity

/--
The fixed-law strict projection-slack GC-backed single-arm PATT
cross-calibrated route from absolute calibration to two-sided
component-positive coverage with local expansion and Godambe obligations
packaged as one compact local-experiment core.
-/
theorem
    patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_fixedLaw_projection_lt_limit_glivenkoCantelli_local_experiment_core
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
    (estimated : EstimatedScoreLocalExperimentInput)
    (core : EstimatedScoreLocalExperimentCore estimated)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity) :
    PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_fixedLaw_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated)
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction limit oracleLimit projectionLimit horacle
        hprojection hprojectionLimit_lt_oracle hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_fixedLaw_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated) knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction limit oracleLimit projectionLimit horacle hprojection
    hprojectionLimit_lt_oracle hinverse_meas estimatedScoreToScaledTendsto
    coverageInput hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
    hdenominator hheterogeneity hresidual hfirst
    ⟨hscore, core.matching_functional_local_derivative,
      core.local_stochastic_equicontinuity⟩
    core.godambe_variance_identity

/--
The fixed-law strict projection-slack GC-backed single-arm PATT
cross-calibrated route from two-sided calibration to absolute
component-positive coverage with local expansion and Godambe obligations
packaged as one compact core.
-/
theorem
    patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_fixedLaw_projection_lt_limit_glivenkoCantelli_estimated_score_core
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
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_fixedLaw_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction limit oracleLimit projectionLimit horacle
        hprojection hprojectionLimit_lt_oracle hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_fixedLaw_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    estimatedScoreBridge knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction limit oracleLimit projectionLimit horacle hprojection
    hprojectionLimit_lt_oracle hinverse_meas estimatedScoreToScaledTendsto
    coverageInput hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
    hdenominator hheterogeneity hresidual hfirst
    core.matching_functional_local_expansion core.godambe_variance_identity

/--
The fixed-law strict projection-slack GC-backed single-arm PATT
cross-calibrated route from two-sided calibration to absolute
component-positive coverage with local expansion and Godambe obligations
packaged as one compact local-experiment core.
-/
theorem
    patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_fixedLaw_projection_lt_limit_glivenkoCantelli_local_experiment_core
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
    (estimated : EstimatedScoreLocalExperimentInput)
    (core : EstimatedScoreLocalExperimentCore estimated)
    (knownScoreToEstimatedScoreInput :
      knownScoreBridge.asymptotic_normality ->
        estimated.known_score_asymptotic_normality)
    (scaledStatistic : Index -> Sample -> Real)
    (oracle projectionReduction : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (oracleLimit projectionLimit : Real)
    (horacle :
      TendstoInMeasure sampleLaw oracle l (fun _sample => oracleLimit))
    (hprojection :
      TendstoInMeasure sampleLaw projectionReduction l
        (fun _sample => projectionLimit))
    (hprojectionLimit_lt_oracle : projectionLimit < oracleLimit)
    (hinverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (oracle index sample)
                (projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (estimatedScoreToScaledTendsto :
      estimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
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
    (hfirst : estimated.first_step_asymptotic_linearization)
    (hscore : estimated.score_estimator_local_asymptotic_linearity) :
    PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusionOfGlivenkoCantelli
      (pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_fixedLaw_projection_lt_limit_glivenkoCantelli
        cells referenceShare sample weight score indicatorBridge
        finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
        envelopeToScaled indicatorLLNToScaled knownScoreBridge
        scaledApproximationToMatchingDiscrepancy (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated)
        knownScoreToEstimatedScoreInput scaledStatistic oracle
        projectionReduction limit oracleLimit projectionLimit horacle
        hprojection hprojectionLimit_lt_oracle hinverse_meas
        estimatedScoreToScaledTendsto coverageInput) :=
  patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_fixedLaw_projection_lt_limit_glivenkoCantelli
    cells referenceShare sample weight score indicatorBridge
    finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled envelopeToScaled
    indicatorLLNToScaled knownScoreBridge scaledApproximationToMatchingDiscrepancy
    (estimatedScoreAsymptoticBridgeOfLocalExperimentInput estimated) knownScoreToEstimatedScoreInput scaledStatistic oracle
    projectionReduction limit oracleLimit projectionLimit horacle hprojection
    hprojectionLimit_lt_oracle hinverse_meas estimatedScoreToScaledTendsto
    coverageInput hgc hfinite henvelope hsimplex hlinear hmatrix hdecomp
    hdenominator hheterogeneity hresidual hfirst
    ⟨hscore, core.matching_functional_local_derivative,
      core.local_stochastic_equicontinuity⟩
    core.godambe_variance_identity


end WDSM
end Matching
end StatInference
