import StatInference.Matching.WDSM.FiniteCellIndicatorGCComponentPositiveVarianceAdapter
import StatInference.Matching.WDSM.FiniteCellIndicatorPairedEstimatedScoreComponentPositiveVarianceWaldCoverage

/-!
# GC-backed component-positive Wald coverage bridge

This module connects the Glivenko-Cantelli finite score-cell adapter to the
component-positive Wald coverage layer.  It exposes fixed-law strict
projection-slack routes for paired absolute and two-sided PATE/PATT Wald
coverage, plus the corresponding nonfixed strict-slack absolute and two-sided
routes, including the cross-calibrated routes between absolute and two-sided
calibration inputs, and weak projection-slack positive-drift routes.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter MeasureTheory
open scoped Topology

variable {Unit PATECell PATTCell Index Sample LimitSample : Type*}
variable [DecidableEq PATECell] [DecidableEq PATTCell]
variable {PATEParam PATTParam : Type*}
variable [DecidableEq PATEParam] [DecidableEq PATTParam]
variable [MeasurableSpace Sample] [MeasurableSpace LimitSample]
variable {sampleLaw : MeasureTheory.Measure Sample}
variable {limitLaw : MeasureTheory.Measure LimitSample}
variable [MeasureTheory.IsProbabilityMeasure sampleLaw]
variable [MeasureTheory.IsProbabilityMeasure limitLaw]
variable {l : Filter Index}
variable [l.IsCountablyGenerated]

/--
Attach paired GC-backed score-cell mass LLNs to an already derived absolute
positive-variance Wald conclusion.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    (pateCells : Finset PATECell)
    (pattCells : Finset PATTCell)
    (pateReferenceShare : PATECell -> Real)
    (pattReferenceShare : PATTCell -> Real)
    (pateSample pattSample : ℕ -> Finset Unit)
    (pateWeight pattWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
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
      PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge
        PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
        b) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) pateCells pateSample
        pateWeight pateScore pateReferenceShare ∧
      cellwiseScoreCellMassLLN (l := atTop) pattCells pattSample
        pattWeight pattScore pattReferenceShare := by
  have hmass :=
    paired_cellwise_mass_lln_of_glivenkoCantelli_bridge
      pateCells pattCells pateReferenceShare pattReferenceShare pateSample
      pattSample pateWeight pattWeight pateScore pattScore hpateGC hpattGC
  exact ⟨hcoverage, hmass.1, hmass.2⟩

/--
Attach paired GC-backed score-cell mass LLNs to an already derived two-sided
positive-variance Wald conclusion.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    (pateCells : Finset PATECell)
    (pattCells : Finset PATTCell)
    (pateReferenceShare : PATECell -> Real)
    (pattReferenceShare : PATTCell -> Real)
    (pateSample pattSample : ℕ -> Finset Unit)
    (pateWeight pattWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
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
      PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge
        PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
        b) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) pateCells pateSample
        pateWeight pateScore pateReferenceShare ∧
      cellwiseScoreCellMassLLN (l := atTop) pattCells pattSample
        pattWeight pattScore pattReferenceShare := by
  have hmass :=
    paired_cellwise_mass_lln_of_glivenkoCantelli_bridge
      pateCells pattCells pateReferenceShare pattReferenceShare pateSample
      pattSample pateWeight pattWeight pateScore pattScore hpateGC hpattGC
  exact ⟨hcoverage, hmass.1, hmass.2⟩

theorem
    pate_patt_absolutePositiveVarianceWaldConclusion_and_mass_lln_of_l1BracketingNumber_obligations
    {PATEBracket PATTBracket : Type*}
    [Fintype PATEBracket] [Fintype PATTBracket]
    (pateCells : Finset PATECell)
    (pattCells : Finset PATTCell)
    (pateReferenceShare : PATECell -> Real)
    (pattReferenceShare : PATTCell -> Real)
    (pateSample pattSample : ℕ -> Finset Unit)
    (pateWeight pattWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
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
      PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge
        PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
        b) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) pateCells pateSample
        pateWeight pateScore pateReferenceShare ∧
      cellwiseScoreCellMassLLN (l := atTop) pattCells pattSample
        pattWeight pattScore pattReferenceShare :=
  pate_patt_absolutePositiveVarianceWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    pateCells pattCells pateReferenceShare pattReferenceShare pateSample
    pattSample pateWeight pattWeight pateScore pattScore
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      pateCells pateReferenceShare pateSample pateWeight pateScore
      pateObligations)
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      pattCells pattReferenceShare pattSample pattWeight pattScore
      pattObligations)
    hcoverage

theorem
    pate_patt_absolutePositiveVarianceWaldConclusion_and_mass_lln_of_vdvw241_endpoint_assembly
    {PATEBracket PATTBracket : Type*}
    [Fintype PATEBracket] [Fintype PATTBracket]
    (pateCells : Finset PATECell)
    (pattCells : Finset PATTCell)
    (pateReferenceShare : PATECell -> Real)
    (pattReferenceShare : PATTCell -> Real)
    (pateSample pattSample : ℕ -> Finset Unit)
    (pateWeight pattWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
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
      PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge
        PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
        b) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) pateCells pateSample
        pateWeight pateScore pateReferenceShare ∧
      cellwiseScoreCellMassLLN (l := atTop) pattCells pattSample
        pattWeight pattScore pattReferenceShare :=
  pate_patt_absolutePositiveVarianceWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    pateCells pattCells pateReferenceShare pattReferenceShare pateSample
    pattSample pateWeight pattWeight pateScore pattScore
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      pateCells pateReferenceShare pateSample pateWeight pateScore
      pateAssembly)
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      pattCells pattReferenceShare pattSample pattWeight pattScore
      pattAssembly)
    hcoverage

theorem
    pate_patt_twoSidedPositiveVarianceWaldConclusion_and_mass_lln_of_l1BracketingNumber_obligations
    {PATEBracket PATTBracket : Type*}
    [Fintype PATEBracket] [Fintype PATTBracket]
    (pateCells : Finset PATECell)
    (pattCells : Finset PATTCell)
    (pateReferenceShare : PATECell -> Real)
    (pattReferenceShare : PATTCell -> Real)
    (pateSample pattSample : ℕ -> Finset Unit)
    (pateWeight pattWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
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
      PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge
        PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
        b) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) pateCells pateSample
        pateWeight pateScore pateReferenceShare ∧
      cellwiseScoreCellMassLLN (l := atTop) pattCells pattSample
        pattWeight pattScore pattReferenceShare :=
  pate_patt_twoSidedPositiveVarianceWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    pateCells pattCells pateReferenceShare pattReferenceShare pateSample
    pattSample pateWeight pattWeight pateScore pattScore
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      pateCells pateReferenceShare pateSample pateWeight pateScore
      pateObligations)
    (weighted_indicator_array_lln_of_l1BracketingNumber_obligations
      pattCells pattReferenceShare pattSample pattWeight pattScore
      pattObligations)
    hcoverage

theorem
    pate_patt_twoSidedPositiveVarianceWaldConclusion_and_mass_lln_of_vdvw241_endpoint_assembly
    {PATEBracket PATTBracket : Type*}
    [Fintype PATEBracket] [Fintype PATTBracket]
    (pateCells : Finset PATECell)
    (pattCells : Finset PATTCell)
    (pateReferenceShare : PATECell -> Real)
    (pattReferenceShare : PATTCell -> Real)
    (pateSample pattSample : ℕ -> Finset Unit)
    (pateWeight pattWeight : ℕ -> Unit -> Real)
    (pateScore : ℕ -> Unit -> PATECell)
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
      PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge
        PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l}
    (hcoverage :
      PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
        b) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
        b ∧
      cellwiseScoreCellMassLLN (l := atTop) pateCells pateSample
        pateWeight pateScore pateReferenceShare ∧
      cellwiseScoreCellMassLLN (l := atTop) pattCells pattSample
        pattWeight pattScore pattReferenceShare :=
  pate_patt_twoSidedPositiveVarianceWaldConclusion_and_mass_lln_of_glivenkoCantelli_bridge
    pateCells pattCells pateReferenceShare pattReferenceShare pateSample
    pattSample pateWeight pattWeight pateScore pattScore
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      pateCells pateReferenceShare pateSample pateWeight pateScore
      pateAssembly)
    (weighted_indicator_array_lln_of_vdvw241_endpoint_assembly
      pattCells pattReferenceShare pattSample pattWeight pattScore
      pattAssembly)
    hcoverage

/--
Build the paired absolute positive-variance Wald bridge from GC-backed finite
score-cell inputs, using fixed-law strict projection slack with zero target
drift for both PATE and PATT.
-/
def
    patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction : Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction : Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit
    (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
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
      pattKnownScoreToEstimatedScoreInput)
    pate_scaledStatistic pate_oracle pate_projectionReduction pate_limit
    pate_oracleLimit pate_projectionLimit hpate_oracle hpate_projection
    hpate_projectionLimit_lt_oracle hpate_inverse_meas
    pateEstimatedScoreToScaledTendsto patt_scaledStatistic patt_oracle
    patt_projectionReduction patt_limit patt_oracleLimit patt_projectionLimit
    hpatt_oracle hpatt_projection hpatt_projectionLimit_lt_oracle
    hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
    pate_coverage_input patt_coverage_input

/--
The fixed-law strict projection-slack GC route yields paired absolute Wald
coverage after the finite-cell, known-score, estimated-score, studentization,
and Wald coverage obligations are supplied.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_fixedLaw_projection_lt_limit_glivenkoCantelli
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction : Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction : Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_limit pate_oracleLimit
        pate_projectionLimit hpate_oracle hpate_projection
        hpate_projectionLimit_lt_oracle hpate_inverse_meas
        pateEstimatedScoreToScaledTendsto patt_scaledStatistic patt_oracle
        patt_projectionReduction patt_limit patt_oracleLimit
        patt_projectionLimit hpatt_oracle hpatt_projection
        hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
        pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli]
    using
      pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          pateEstimatedScoreBridge pattEstimatedScoreBridge
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction pate_limit
        pate_oracleLimit pate_projectionLimit hpate_oracle
        hpate_projection hpate_projectionLimit_lt_oracle
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_limit patt_oracleLimit patt_projectionLimit hpatt_oracle
        hpatt_projection hpatt_projectionLimit_lt_oracle
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
The fixed-law strict projection-slack paired GC absolute component-positive
Wald route with the PATE and PATT local expansion/Godambe obligations packaged
as compact estimated-score cores.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_fixedLaw_projection_lt_limit_glivenkoCantelli_estimated_score_core
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction : Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction : Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_limit pate_oracleLimit
        pate_projectionLimit hpate_oracle hpate_projection
        hpate_projectionLimit_lt_oracle hpate_inverse_meas
        pateEstimatedScoreToScaledTendsto patt_scaledStatistic patt_oracle
        patt_projectionReduction patt_limit patt_oracleLimit
        patt_projectionLimit hpatt_oracle hpatt_projection
        hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
        pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli]
    using
      pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          pateEstimatedScoreBridge pattEstimatedScoreBridge
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction pate_limit
        pate_oracleLimit pate_projectionLimit hpate_oracle
        hpate_projection hpate_projectionLimit_lt_oracle
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_limit patt_oracleLimit patt_projectionLimit hpatt_oracle
        hpatt_projection hpatt_projectionLimit_lt_oracle
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
        hpateFirst pateCore.matching_functional_local_expansion
        pateCore.godambe_variance_identity hpattFirst
        pattCore.matching_functional_local_expansion
        pattCore.godambe_variance_identity

/--
The fixed-law strict projection-slack paired GC absolute component-positive
Wald route with the PATE and PATT local experiment obligations packaged as
compact local-experiment cores.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_fixedLaw_projection_lt_limit_glivenkoCantelli_local_experiment_core
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction : Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction : Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_limit pate_oracleLimit
        pate_projectionLimit hpate_oracle hpate_projection
        hpate_projectionLimit_lt_oracle hpate_inverse_meas
        pateEstimatedScoreToScaledTendsto patt_scaledStatistic patt_oracle
        patt_projectionReduction patt_limit patt_oracleLimit
        patt_projectionLimit hpatt_oracle hpatt_projection
        hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
        pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli]
    using
      pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          (estimatedScoreAsymptoticBridgeOfLocalExperimentInput pateEstimated) (estimatedScoreAsymptoticBridgeOfLocalExperimentInput pattEstimated)
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction pate_limit
        pate_oracleLimit pate_projectionLimit hpate_oracle
        hpate_projection hpate_projectionLimit_lt_oracle
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_limit patt_oracleLimit patt_projectionLimit hpatt_oracle
        hpatt_projection hpatt_projectionLimit_lt_oracle
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
        hpateFirst
        ⟨hpateScore, pateCore.matching_functional_local_derivative,
          pateCore.local_stochastic_equicontinuity⟩
        pateCore.godambe_variance_identity hpattFirst
        ⟨hpattScore, pattCore.matching_functional_local_derivative,
          pattCore.local_stochastic_equicontinuity⟩
        pattCore.godambe_variance_identity

/--
Build the paired two-sided positive-variance Wald bridge from GC-backed finite
score-cell inputs, using fixed-law strict projection slack with zero target
drift for both PATE and PATT.
-/
def
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction : Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction : Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit
    (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
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
      pattKnownScoreToEstimatedScoreInput)
    pate_scaledStatistic pate_oracle pate_projectionReduction pate_limit
    pate_oracleLimit pate_projectionLimit hpate_oracle hpate_projection
    hpate_projectionLimit_lt_oracle hpate_inverse_meas
    pateEstimatedScoreToScaledTendsto patt_scaledStatistic patt_oracle
    patt_projectionReduction patt_limit patt_oracleLimit patt_projectionLimit
    hpatt_oracle hpatt_projection hpatt_projectionLimit_lt_oracle
    hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
    pate_coverage_input patt_coverage_input

/--
The fixed-law strict projection-slack GC route yields paired two-sided Wald
coverage after the finite-cell, known-score, estimated-score, studentization,
and Wald coverage obligations are supplied.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_fixedLaw_projection_lt_limit_glivenkoCantelli
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction : Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction : Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_limit pate_oracleLimit
        pate_projectionLimit hpate_oracle hpate_projection
        hpate_projectionLimit_lt_oracle hpate_inverse_meas
        pateEstimatedScoreToScaledTendsto patt_scaledStatistic patt_oracle
        patt_projectionReduction patt_limit patt_oracleLimit
        patt_projectionLimit hpatt_oracle hpatt_projection
        hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
        pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli]
    using
      pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          pateEstimatedScoreBridge pattEstimatedScoreBridge
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction pate_limit
        pate_oracleLimit pate_projectionLimit hpate_oracle
        hpate_projection hpate_projectionLimit_lt_oracle
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_limit patt_oracleLimit patt_projectionLimit hpatt_oracle
        hpatt_projection hpatt_projectionLimit_lt_oracle
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
The fixed-law strict projection-slack paired GC two-sided component-positive
Wald route with the PATE and PATT local expansion/Godambe obligations packaged
as compact estimated-score cores.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_fixedLaw_projection_lt_limit_glivenkoCantelli_estimated_score_core
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction : Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction : Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_limit pate_oracleLimit
        pate_projectionLimit hpate_oracle hpate_projection
        hpate_projectionLimit_lt_oracle hpate_inverse_meas
        pateEstimatedScoreToScaledTendsto patt_scaledStatistic patt_oracle
        patt_projectionReduction patt_limit patt_oracleLimit
        patt_projectionLimit hpatt_oracle hpatt_projection
        hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
        pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli]
    using
      pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          pateEstimatedScoreBridge pattEstimatedScoreBridge
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction pate_limit
        pate_oracleLimit pate_projectionLimit hpate_oracle
        hpate_projection hpate_projectionLimit_lt_oracle
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_limit patt_oracleLimit patt_projectionLimit hpatt_oracle
        hpatt_projection hpatt_projectionLimit_lt_oracle
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
        hpateFirst pateCore.matching_functional_local_expansion
        pateCore.godambe_variance_identity hpattFirst
        pattCore.matching_functional_local_expansion
        pattCore.godambe_variance_identity

/--
The fixed-law strict projection-slack paired GC two-sided component-positive
Wald route with the PATE and PATT local experiment obligations packaged as
compact local-experiment cores.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_fixedLaw_projection_lt_limit_glivenkoCantelli_local_experiment_core
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction : Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction : Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_limit pate_oracleLimit
        pate_projectionLimit hpate_oracle hpate_projection
        hpate_projectionLimit_lt_oracle hpate_inverse_meas
        pateEstimatedScoreToScaledTendsto patt_scaledStatistic patt_oracle
        patt_projectionReduction patt_limit patt_oracleLimit
        patt_projectionLimit hpatt_oracle hpatt_projection
        hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
        pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli]
    using
      pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          (estimatedScoreAsymptoticBridgeOfLocalExperimentInput pateEstimated) (estimatedScoreAsymptoticBridgeOfLocalExperimentInput pattEstimated)
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction pate_limit
        pate_oracleLimit pate_projectionLimit hpate_oracle
        hpate_projection hpate_projectionLimit_lt_oracle
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_limit patt_oracleLimit patt_projectionLimit hpatt_oracle
        hpatt_projection hpatt_projectionLimit_lt_oracle
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
        hpateFirst
        ⟨hpateScore, pateCore.matching_functional_local_derivative,
          pateCore.local_stochastic_equicontinuity⟩
        pateCore.godambe_variance_identity hpattFirst
        ⟨hpattScore, pattCore.matching_functional_local_derivative,
          pattCore.local_stochastic_equicontinuity⟩
        pattCore.godambe_variance_identity

/--
Build the paired two-sided positive-variance Wald bridge from GC-backed finite
score-cell inputs and absolute variance-calibration inputs, using fixed-law
strict projection slack with zero target drift for both PATE and PATT.
-/
def
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_fixedLaw_projection_lt_limit_glivenkoCantelli
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction : Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction : Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_fixedLaw_projection_lt_limit
    (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
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
      pattKnownScoreToEstimatedScoreInput)
    pate_scaledStatistic pate_oracle pate_projectionReduction pate_limit
    pate_oracleLimit pate_projectionLimit hpate_oracle hpate_projection
    hpate_projectionLimit_lt_oracle hpate_inverse_meas
    pateEstimatedScoreToScaledTendsto patt_scaledStatistic patt_oracle
    patt_projectionReduction patt_limit patt_oracleLimit patt_projectionLimit
    hpatt_oracle hpatt_projection hpatt_projectionLimit_lt_oracle
    hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
    pate_coverage_input patt_coverage_input

/--
The fixed-law strict projection-slack GC route yields paired two-sided Wald
coverage from absolute variance-calibration inputs after the finite-cell,
known-score, estimated-score, studentization, and Wald coverage obligations
are supplied.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_absolute_fixedLaw_projection_lt_limit_glivenkoCantelli
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction : Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction : Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_fixedLaw_projection_lt_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_limit pate_oracleLimit
        pate_projectionLimit hpate_oracle hpate_projection
        hpate_projectionLimit_lt_oracle hpate_inverse_meas
        pateEstimatedScoreToScaledTendsto patt_scaledStatistic patt_oracle
        patt_projectionReduction patt_limit patt_oracleLimit
        patt_projectionLimit hpatt_oracle hpatt_projection
        hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
        pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_fixedLaw_projection_lt_limit_glivenkoCantelli]
    using
      pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_fixedLaw_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          pateEstimatedScoreBridge pattEstimatedScoreBridge
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction pate_limit
        pate_oracleLimit pate_projectionLimit hpate_oracle
        hpate_projection hpate_projectionLimit_lt_oracle
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_limit patt_oracleLimit patt_projectionLimit hpatt_oracle
        hpatt_projection hpatt_projectionLimit_lt_oracle
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
The fixed-law strict projection-slack paired GC cross-calibrated two-sided
component-positive Wald route with the PATE and PATT local expansion/Godambe
obligations packaged as compact estimated-score cores.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_absolute_fixedLaw_projection_lt_limit_glivenkoCantelli_estimated_score_core
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction : Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction : Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_fixedLaw_projection_lt_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_limit pate_oracleLimit
        pate_projectionLimit hpate_oracle hpate_projection
        hpate_projectionLimit_lt_oracle hpate_inverse_meas
        pateEstimatedScoreToScaledTendsto patt_scaledStatistic patt_oracle
        patt_projectionReduction patt_limit patt_oracleLimit
        patt_projectionLimit hpatt_oracle hpatt_projection
        hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
        pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_fixedLaw_projection_lt_limit_glivenkoCantelli]
    using
      pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_fixedLaw_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          pateEstimatedScoreBridge pattEstimatedScoreBridge
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction pate_limit
        pate_oracleLimit pate_projectionLimit hpate_oracle
        hpate_projection hpate_projectionLimit_lt_oracle
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_limit patt_oracleLimit patt_projectionLimit hpatt_oracle
        hpatt_projection hpatt_projectionLimit_lt_oracle
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
        hpateFirst pateCore.matching_functional_local_expansion
        pateCore.godambe_variance_identity hpattFirst
        pattCore.matching_functional_local_expansion
        pattCore.godambe_variance_identity

/--
The fixed-law strict projection-slack paired GC two-sided component-positive
Wald route from absolute calibration inputs, with the PATE and PATT local
experiment obligations packaged as compact local-experiment cores.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_absolute_fixedLaw_projection_lt_limit_glivenkoCantelli_local_experiment_core
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction : Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction : Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_fixedLaw_projection_lt_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_limit pate_oracleLimit
        pate_projectionLimit hpate_oracle hpate_projection
        hpate_projectionLimit_lt_oracle hpate_inverse_meas
        pateEstimatedScoreToScaledTendsto patt_scaledStatistic patt_oracle
        patt_projectionReduction patt_limit patt_oracleLimit
        patt_projectionLimit hpatt_oracle hpatt_projection
        hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
        pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_fixedLaw_projection_lt_limit_glivenkoCantelli]
    using
      pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_fixedLaw_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          (estimatedScoreAsymptoticBridgeOfLocalExperimentInput pateEstimated) (estimatedScoreAsymptoticBridgeOfLocalExperimentInput pattEstimated)
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction pate_limit
        pate_oracleLimit pate_projectionLimit hpate_oracle
        hpate_projection hpate_projectionLimit_lt_oracle
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_limit patt_oracleLimit patt_projectionLimit hpatt_oracle
        hpatt_projection hpatt_projectionLimit_lt_oracle
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
        hpateFirst
        ⟨hpateScore, pateCore.matching_functional_local_derivative,
          pateCore.local_stochastic_equicontinuity⟩
        pateCore.godambe_variance_identity hpattFirst
        ⟨hpattScore, pattCore.matching_functional_local_derivative,
          pattCore.local_stochastic_equicontinuity⟩
        pattCore.godambe_variance_identity

/--
Build the paired absolute positive-variance Wald bridge from GC-backed finite
score-cell inputs and two-sided variance-calibration inputs, using fixed-law
strict projection slack with zero target drift for both PATE and PATT.
-/
def
    patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_fixedLaw_projection_lt_limit_glivenkoCantelli
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction : Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction : Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_fixedLaw_projection_lt_limit
    (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
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
      pattKnownScoreToEstimatedScoreInput)
    pate_scaledStatistic pate_oracle pate_projectionReduction pate_limit
    pate_oracleLimit pate_projectionLimit hpate_oracle hpate_projection
    hpate_projectionLimit_lt_oracle hpate_inverse_meas
    pateEstimatedScoreToScaledTendsto patt_scaledStatistic patt_oracle
    patt_projectionReduction patt_limit patt_oracleLimit patt_projectionLimit
    hpatt_oracle hpatt_projection hpatt_projectionLimit_lt_oracle
    hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
    pate_coverage_input patt_coverage_input

/--
The fixed-law strict projection-slack GC route yields paired absolute Wald
coverage from two-sided variance-calibration inputs after the finite-cell,
known-score, estimated-score, studentization, and Wald coverage obligations
are supplied.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_twoSided_fixedLaw_projection_lt_limit_glivenkoCantelli
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction : Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction : Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_fixedLaw_projection_lt_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_limit pate_oracleLimit
        pate_projectionLimit hpate_oracle hpate_projection
        hpate_projectionLimit_lt_oracle hpate_inverse_meas
        pateEstimatedScoreToScaledTendsto patt_scaledStatistic patt_oracle
        patt_projectionReduction patt_limit patt_oracleLimit
        patt_projectionLimit hpatt_oracle hpatt_projection
        hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
        pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_fixedLaw_projection_lt_limit_glivenkoCantelli]
    using
      pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_fixedLaw_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          pateEstimatedScoreBridge pattEstimatedScoreBridge
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction pate_limit
        pate_oracleLimit pate_projectionLimit hpate_oracle
        hpate_projection hpate_projectionLimit_lt_oracle
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_limit patt_oracleLimit patt_projectionLimit hpatt_oracle
        hpatt_projection hpatt_projectionLimit_lt_oracle
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
The fixed-law strict projection-slack paired GC cross-calibrated absolute
component-positive Wald route with the PATE and PATT local expansion/Godambe
obligations packaged as compact estimated-score cores.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_twoSided_fixedLaw_projection_lt_limit_glivenkoCantelli_estimated_score_core
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction : Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction : Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_fixedLaw_projection_lt_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_limit pate_oracleLimit
        pate_projectionLimit hpate_oracle hpate_projection
        hpate_projectionLimit_lt_oracle hpate_inverse_meas
        pateEstimatedScoreToScaledTendsto patt_scaledStatistic patt_oracle
        patt_projectionReduction patt_limit patt_oracleLimit
        patt_projectionLimit hpatt_oracle hpatt_projection
        hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
        pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_fixedLaw_projection_lt_limit_glivenkoCantelli]
    using
      pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_fixedLaw_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          pateEstimatedScoreBridge pattEstimatedScoreBridge
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction pate_limit
        pate_oracleLimit pate_projectionLimit hpate_oracle
        hpate_projection hpate_projectionLimit_lt_oracle
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_limit patt_oracleLimit patt_projectionLimit hpatt_oracle
        hpatt_projection hpatt_projectionLimit_lt_oracle
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
        hpateFirst pateCore.matching_functional_local_expansion
        pateCore.godambe_variance_identity hpattFirst
        pattCore.matching_functional_local_expansion
        pattCore.godambe_variance_identity

/--
The fixed-law strict projection-slack paired GC absolute component-positive
Wald route from two-sided calibration inputs, with the PATE and PATT local
experiment obligations packaged as compact local-experiment cores.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_twoSided_fixedLaw_projection_lt_limit_glivenkoCantelli_local_experiment_core
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction : Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction : Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample) 0))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_fixedLaw_projection_lt_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_limit pate_oracleLimit
        pate_projectionLimit hpate_oracle hpate_projection
        hpate_projectionLimit_lt_oracle hpate_inverse_meas
        pateEstimatedScoreToScaledTendsto patt_scaledStatistic patt_oracle
        patt_projectionReduction patt_limit patt_oracleLimit
        patt_projectionLimit hpatt_oracle hpatt_projection
        hpatt_projectionLimit_lt_oracle hpatt_inverse_meas
        pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_fixedLaw_projection_lt_limit_glivenkoCantelli]
    using
      pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_fixedLaw_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          (estimatedScoreAsymptoticBridgeOfLocalExperimentInput pateEstimated) (estimatedScoreAsymptoticBridgeOfLocalExperimentInput pattEstimated)
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction pate_limit
        pate_oracleLimit pate_projectionLimit hpate_oracle
        hpate_projection hpate_projectionLimit_lt_oracle
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_limit patt_oracleLimit patt_projectionLimit hpatt_oracle
        hpatt_projection hpatt_projectionLimit_lt_oracle
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
        hpateFirst
        ⟨hpateScore, pateCore.matching_functional_local_derivative,
          pateCore.local_stochastic_equicontinuity⟩
        pateCore.godambe_variance_identity hpattFirst
        ⟨hpattScore, pattCore.matching_functional_local_derivative,
          pattCore.local_stochastic_equicontinuity⟩
        pattCore.godambe_variance_identity

/--
Build the paired absolute positive-variance Wald bridge from GC-backed finite
score-cell inputs, using strict projection slack and nonnegative target drift
for both PATE and PATT.
-/
def
    patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_lt_limit_glivenkoCantelli
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_driftLimit_nonneg : 0 ≤ pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_driftLimit_nonneg : 0 ≤ patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_lt_limit
    (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
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
      pattKnownScoreToEstimatedScoreInput)
    pate_scaledStatistic pate_oracle pate_projectionReduction
    pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
    pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
    hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
    hpate_inverse_meas pateEstimatedScoreToScaledTendsto
    patt_scaledStatistic patt_oracle patt_projectionReduction
    patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
    patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
    hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
    hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
    pate_coverage_input patt_coverage_input

/--
The strict projection-slack GC route yields paired absolute Wald coverage
after the finite-cell, known-score, estimated-score, studentization, and Wald
coverage obligations are supplied.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_projection_lt_limit_glivenkoCantelli
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_driftLimit_nonneg : 0 ≤ pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_driftLimit_nonneg : 0 ≤ patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_lt_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_targetDrift pate_limit
        pate_oracleLimit pate_projectionLimit pate_targetDriftLimit
        hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_lt_limit_glivenkoCantelli]
    using
      pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          pateEstimatedScoreBridge pattEstimatedScoreBridge
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
        pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
The strict projection-slack paired GC absolute component-positive Wald route
with the PATE and PATT local expansion/Godambe obligations packaged as compact
estimated-score cores.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_projection_lt_limit_glivenkoCantelli_estimated_score_core
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_driftLimit_nonneg : 0 ≤ pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_driftLimit_nonneg : 0 ≤ patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_lt_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_targetDrift pate_limit
        pate_oracleLimit pate_projectionLimit pate_targetDriftLimit
        hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_lt_limit_glivenkoCantelli]
    using
      pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          pateEstimatedScoreBridge pattEstimatedScoreBridge
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
        pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
        hpateFirst pateCore.matching_functional_local_expansion
        pateCore.godambe_variance_identity hpattFirst
        pattCore.matching_functional_local_expansion
        pattCore.godambe_variance_identity

/--
The strict projection-slack paired GC absolute component-positive Wald route
with the PATE and PATT local experiment obligations packaged as compact
local-experiment cores.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_projection_lt_limit_glivenkoCantelli_local_experiment_core
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_driftLimit_nonneg : 0 ≤ pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_driftLimit_nonneg : 0 ≤ patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_lt_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_targetDrift pate_limit
        pate_oracleLimit pate_projectionLimit pate_targetDriftLimit
        hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_lt_limit_glivenkoCantelli]
    using
      pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          (estimatedScoreAsymptoticBridgeOfLocalExperimentInput pateEstimated) (estimatedScoreAsymptoticBridgeOfLocalExperimentInput pattEstimated)
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
        pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
        hpateFirst
        ⟨hpateScore, pateCore.matching_functional_local_derivative,
          pateCore.local_stochastic_equicontinuity⟩
        pateCore.godambe_variance_identity hpattFirst
        ⟨hpattScore, pattCore.matching_functional_local_derivative,
          pattCore.local_stochastic_equicontinuity⟩
        pattCore.godambe_variance_identity

/--
Build the paired two-sided positive-variance Wald bridge from GC-backed finite
score-cell inputs, using strict projection slack and nonnegative target drift
for both PATE and PATT.
-/
def
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_lt_limit_glivenkoCantelli
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_driftLimit_nonneg : 0 ≤ pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_driftLimit_nonneg : 0 ≤ patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_lt_limit
    (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
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
      pattKnownScoreToEstimatedScoreInput)
    pate_scaledStatistic pate_oracle pate_projectionReduction
    pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
    pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
    hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
    hpate_inverse_meas pateEstimatedScoreToScaledTendsto
    patt_scaledStatistic patt_oracle patt_projectionReduction
    patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
    patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
    hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
    hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
    pate_coverage_input patt_coverage_input

/--
The strict projection-slack GC route yields paired two-sided Wald coverage
after the finite-cell, known-score, estimated-score, studentization, and Wald
coverage obligations are supplied.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_projection_lt_limit_glivenkoCantelli
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_driftLimit_nonneg : 0 ≤ pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_driftLimit_nonneg : 0 ≤ patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_lt_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_targetDrift pate_limit
        pate_oracleLimit pate_projectionLimit pate_targetDriftLimit
        hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_lt_limit_glivenkoCantelli]
    using
      pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          pateEstimatedScoreBridge pattEstimatedScoreBridge
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
        pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
The strict projection-slack paired GC two-sided component-positive Wald route
with the PATE and PATT local expansion/Godambe obligations packaged as compact
estimated-score cores.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_projection_lt_limit_glivenkoCantelli_estimated_score_core
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_driftLimit_nonneg : 0 ≤ pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_driftLimit_nonneg : 0 ≤ patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_lt_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_targetDrift pate_limit
        pate_oracleLimit pate_projectionLimit pate_targetDriftLimit
        hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_lt_limit_glivenkoCantelli]
    using
      pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          pateEstimatedScoreBridge pattEstimatedScoreBridge
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
        pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
        hpateFirst pateCore.matching_functional_local_expansion
        pateCore.godambe_variance_identity hpattFirst
        pattCore.matching_functional_local_expansion
        pattCore.godambe_variance_identity

/--
The strict projection-slack paired GC two-sided component-positive Wald route
with the PATE and PATT local experiment obligations packaged as compact
local-experiment cores.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_projection_lt_limit_glivenkoCantelli_local_experiment_core
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_driftLimit_nonneg : 0 ≤ pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_driftLimit_nonneg : 0 ≤ patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_lt_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_targetDrift pate_limit
        pate_oracleLimit pate_projectionLimit pate_targetDriftLimit
        hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_lt_limit_glivenkoCantelli]
    using
      pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          (estimatedScoreAsymptoticBridgeOfLocalExperimentInput pateEstimated) (estimatedScoreAsymptoticBridgeOfLocalExperimentInput pattEstimated)
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
        pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
        hpateFirst
        ⟨hpateScore, pateCore.matching_functional_local_derivative,
          pateCore.local_stochastic_equicontinuity⟩
        pateCore.godambe_variance_identity hpattFirst
        ⟨hpattScore, pattCore.matching_functional_local_derivative,
          pattCore.local_stochastic_equicontinuity⟩
        pattCore.godambe_variance_identity

/--
Build the paired two-sided positive-variance Wald bridge from GC-backed finite
score-cell inputs and absolute variance-calibration inputs, using strict
projection slack and nonnegative target drift for both PATE and PATT.
-/
def
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_lt_limit_glivenkoCantelli
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_driftLimit_nonneg : 0 ≤ pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_driftLimit_nonneg : 0 ≤ patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_lt_limit
    (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
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
      pattKnownScoreToEstimatedScoreInput)
    pate_scaledStatistic pate_oracle pate_projectionReduction
    pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
    pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
    hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
    hpate_inverse_meas pateEstimatedScoreToScaledTendsto
    patt_scaledStatistic patt_oracle patt_projectionReduction
    patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
    patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
    hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
    hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
    pate_coverage_input patt_coverage_input

/--
The strict projection-slack GC route yields paired two-sided Wald coverage
from absolute variance-calibration inputs after the finite-cell, known-score,
estimated-score, studentization, and Wald coverage obligations are supplied.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_absolute_projection_lt_limit_glivenkoCantelli
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_driftLimit_nonneg : 0 ≤ pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_driftLimit_nonneg : 0 ≤ patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_lt_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_targetDrift pate_limit
        pate_oracleLimit pate_projectionLimit pate_targetDriftLimit
        hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_lt_limit_glivenkoCantelli]
    using
      pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          pateEstimatedScoreBridge pattEstimatedScoreBridge
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
        pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
The strict projection-slack paired GC cross-calibrated two-sided
component-positive Wald route with the PATE and PATT local expansion/Godambe
obligations packaged as compact estimated-score cores.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_absolute_projection_lt_limit_glivenkoCantelli_estimated_score_core
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_driftLimit_nonneg : 0 ≤ pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_driftLimit_nonneg : 0 ≤ patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_lt_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_targetDrift pate_limit
        pate_oracleLimit pate_projectionLimit pate_targetDriftLimit
        hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_lt_limit_glivenkoCantelli]
    using
      pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          pateEstimatedScoreBridge pattEstimatedScoreBridge
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
        pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
        hpateFirst pateCore.matching_functional_local_expansion
        pateCore.godambe_variance_identity hpattFirst
        pattCore.matching_functional_local_expansion
        pattCore.godambe_variance_identity

/--
The strict projection-slack paired GC two-sided component-positive Wald route
from absolute calibration inputs, with the PATE and PATT local experiment
obligations packaged as compact local-experiment cores.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_absolute_projection_lt_limit_glivenkoCantelli_local_experiment_core
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_driftLimit_nonneg : 0 ≤ pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_driftLimit_nonneg : 0 ≤ patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_lt_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_targetDrift pate_limit
        pate_oracleLimit pate_projectionLimit pate_targetDriftLimit
        hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_lt_limit_glivenkoCantelli]
    using
      pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          (estimatedScoreAsymptoticBridgeOfLocalExperimentInput pateEstimated) (estimatedScoreAsymptoticBridgeOfLocalExperimentInput pattEstimated)
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
        pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
        hpateFirst
        ⟨hpateScore, pateCore.matching_functional_local_derivative,
          pateCore.local_stochastic_equicontinuity⟩
        pateCore.godambe_variance_identity hpattFirst
        ⟨hpattScore, pattCore.matching_functional_local_derivative,
          pattCore.local_stochastic_equicontinuity⟩
        pattCore.godambe_variance_identity

/--
Build the paired absolute positive-variance Wald bridge from GC-backed finite
score-cell inputs and two-sided variance-calibration inputs, using strict
projection slack and nonnegative target drift for both PATE and PATT.
-/
def
    patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_lt_limit_glivenkoCantelli
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_driftLimit_nonneg : 0 ≤ pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_driftLimit_nonneg : 0 ≤ patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_lt_limit
    (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
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
      pattKnownScoreToEstimatedScoreInput)
    pate_scaledStatistic pate_oracle pate_projectionReduction
    pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
    pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
    hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
    hpate_inverse_meas pateEstimatedScoreToScaledTendsto
    patt_scaledStatistic patt_oracle patt_projectionReduction
    patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
    patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
    hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
    hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
    pate_coverage_input patt_coverage_input

/--
The strict projection-slack GC route yields paired absolute Wald coverage from
two-sided variance-calibration inputs after the finite-cell, known-score,
estimated-score, studentization, and Wald coverage obligations are supplied.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_twoSided_projection_lt_limit_glivenkoCantelli
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_driftLimit_nonneg : 0 ≤ pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_driftLimit_nonneg : 0 ≤ patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_lt_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_targetDrift pate_limit
        pate_oracleLimit pate_projectionLimit pate_targetDriftLimit
        hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_lt_limit_glivenkoCantelli]
    using
      pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          pateEstimatedScoreBridge pattEstimatedScoreBridge
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
        pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
The strict projection-slack paired GC cross-calibrated absolute
component-positive Wald route with the PATE and PATT local expansion/Godambe
obligations packaged as compact estimated-score cores.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_twoSided_projection_lt_limit_glivenkoCantelli_estimated_score_core
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_driftLimit_nonneg : 0 ≤ pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_driftLimit_nonneg : 0 ≤ patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_lt_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_targetDrift pate_limit
        pate_oracleLimit pate_projectionLimit pate_targetDriftLimit
        hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_lt_limit_glivenkoCantelli]
    using
      pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          pateEstimatedScoreBridge pattEstimatedScoreBridge
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
        pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
        hpateFirst pateCore.matching_functional_local_expansion
        pateCore.godambe_variance_identity hpattFirst
        pattCore.matching_functional_local_expansion
        pattCore.godambe_variance_identity

/--
The strict projection-slack paired GC absolute component-positive Wald route
from two-sided calibration inputs, with the PATE and PATT local experiment
obligations packaged as compact local-experiment cores.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_twoSided_projection_lt_limit_glivenkoCantelli_local_experiment_core
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_driftLimit_nonneg : 0 ≤ pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_driftLimit_nonneg : 0 ≤ patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_lt_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_targetDrift pate_limit
        pate_oracleLimit pate_projectionLimit pate_targetDriftLimit
        hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_lt_limit_glivenkoCantelli]
    using
      pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_lt_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          (estimatedScoreAsymptoticBridgeOfLocalExperimentInput pateEstimated) (estimatedScoreAsymptoticBridgeOfLocalExperimentInput pattEstimated)
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
        pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
        hpateFirst
        ⟨hpateScore, pateCore.matching_functional_local_derivative,
          pateCore.local_stochastic_equicontinuity⟩
        pateCore.godambe_variance_identity hpattFirst
        ⟨hpattScore, pattCore.matching_functional_local_derivative,
          pattCore.local_stochastic_equicontinuity⟩
        pattCore.godambe_variance_identity

/--
Build the paired absolute positive-variance Wald bridge from GC-backed finite
score-cell inputs, using weak projection slack and positive target drift for
both PATE and PATT.
-/
def
    patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_le_drift_pos_limit_glivenkoCantelli
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_le_oracle :
      pate_projectionLimit ≤ pate_oracleLimit)
    (hpate_driftLimit_pos : 0 < pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_le_oracle :
      patt_projectionLimit ≤ patt_oracleLimit)
    (hpatt_driftLimit_pos : 0 < patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_le_drift_pos_limit
    (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
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
      pattKnownScoreToEstimatedScoreInput)
    pate_scaledStatistic pate_oracle pate_projectionReduction
    pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
    pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
    hpate_projectionLimit_le_oracle hpate_driftLimit_pos
    hpate_inverse_meas pateEstimatedScoreToScaledTendsto
    patt_scaledStatistic patt_oracle patt_projectionReduction
    patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
    patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
    hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
    hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
    pate_coverage_input patt_coverage_input

/--
The weak projection-slack positive-drift GC route yields paired absolute Wald
coverage after the finite-cell, known-score, estimated-score, studentization,
and Wald coverage obligations are supplied.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_projection_le_drift_pos_limit_glivenkoCantelli
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_le_oracle :
      pate_projectionLimit ≤ pate_oracleLimit)
    (hpate_driftLimit_pos : 0 < pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_le_oracle :
      patt_projectionLimit ≤ patt_oracleLimit)
    (hpatt_driftLimit_pos : 0 < patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_le_drift_pos_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_targetDrift pate_limit
        pate_oracleLimit pate_projectionLimit pate_targetDriftLimit
        hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_le_oracle hpate_driftLimit_pos
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_le_drift_pos_limit_glivenkoCantelli]
    using
      pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          pateEstimatedScoreBridge pattEstimatedScoreBridge
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
        pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_le_oracle hpate_driftLimit_pos
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
The weak projection-slack positive-drift paired GC absolute component-positive
Wald route with the PATE and PATT local expansion/Godambe obligations packaged
as compact estimated-score cores.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_projection_le_drift_pos_limit_glivenkoCantelli_estimated_score_core
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_le_oracle :
      pate_projectionLimit ≤ pate_oracleLimit)
    (hpate_driftLimit_pos : 0 < pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_le_oracle :
      patt_projectionLimit ≤ patt_oracleLimit)
    (hpatt_driftLimit_pos : 0 < patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_le_drift_pos_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_targetDrift pate_limit
        pate_oracleLimit pate_projectionLimit pate_targetDriftLimit
        hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_le_oracle hpate_driftLimit_pos
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_le_drift_pos_limit_glivenkoCantelli]
    using
      pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          pateEstimatedScoreBridge pattEstimatedScoreBridge
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
        pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_le_oracle hpate_driftLimit_pos
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
        hpateFirst pateCore.matching_functional_local_expansion
        pateCore.godambe_variance_identity hpattFirst
        pattCore.matching_functional_local_expansion
        pattCore.godambe_variance_identity

/--
The weak projection-slack positive-drift paired GC absolute component-positive
Wald route with the PATE and PATT local expansion/Godambe obligations packaged
as compact local-experiment cores.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_projection_le_drift_pos_limit_glivenkoCantelli_local_experiment_core
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_le_oracle :
      pate_projectionLimit ≤ pate_oracleLimit)
    (hpate_driftLimit_pos : 0 < pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_le_oracle :
      patt_projectionLimit ≤ patt_oracleLimit)
    (hpatt_driftLimit_pos : 0 < patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_le_drift_pos_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_targetDrift pate_limit
        pate_oracleLimit pate_projectionLimit pate_targetDriftLimit
        hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_le_oracle hpate_driftLimit_pos
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_le_drift_pos_limit_glivenkoCantelli]
    using
      pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          (estimatedScoreAsymptoticBridgeOfLocalExperimentInput pateEstimated) (estimatedScoreAsymptoticBridgeOfLocalExperimentInput pattEstimated)
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
        pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_le_oracle hpate_driftLimit_pos
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
        hpateFirst
        ⟨hpateScore, pateCore.matching_functional_local_derivative,
          pateCore.local_stochastic_equicontinuity⟩
        pateCore.godambe_variance_identity hpattFirst
        ⟨hpattScore, pattCore.matching_functional_local_derivative,
          pattCore.local_stochastic_equicontinuity⟩
        pattCore.godambe_variance_identity

/--
Build the paired two-sided positive-variance Wald bridge from GC-backed finite
score-cell inputs, using weak projection slack and positive target drift for
both PATE and PATT.
-/
def
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_le_drift_pos_limit_glivenkoCantelli
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_le_oracle :
      pate_projectionLimit ≤ pate_oracleLimit)
    (hpate_driftLimit_pos : 0 < pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_le_oracle :
      patt_projectionLimit ≤ patt_oracleLimit)
    (hpatt_driftLimit_pos : 0 < patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_le_drift_pos_limit
    (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
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
      pattKnownScoreToEstimatedScoreInput)
    pate_scaledStatistic pate_oracle pate_projectionReduction
    pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
    pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
    hpate_projectionLimit_le_oracle hpate_driftLimit_pos
    hpate_inverse_meas pateEstimatedScoreToScaledTendsto
    patt_scaledStatistic patt_oracle patt_projectionReduction
    patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
    patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
    hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
    hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
    pate_coverage_input patt_coverage_input

/--
The weak projection-slack positive-drift GC route yields paired two-sided Wald
coverage after the finite-cell, known-score, estimated-score, studentization,
and Wald coverage obligations are supplied.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_projection_le_drift_pos_limit_glivenkoCantelli
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_le_oracle :
      pate_projectionLimit ≤ pate_oracleLimit)
    (hpate_driftLimit_pos : 0 < pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_le_oracle :
      patt_projectionLimit ≤ patt_oracleLimit)
    (hpatt_driftLimit_pos : 0 < patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_le_drift_pos_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_targetDrift pate_limit
        pate_oracleLimit pate_projectionLimit pate_targetDriftLimit
        hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_le_oracle hpate_driftLimit_pos
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_le_drift_pos_limit_glivenkoCantelli]
    using
      pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          pateEstimatedScoreBridge pattEstimatedScoreBridge
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
        pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_le_oracle hpate_driftLimit_pos
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
The weak projection-slack positive-drift paired GC two-sided component-positive
Wald route with the PATE and PATT local expansion/Godambe obligations packaged
as compact estimated-score cores.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_projection_le_drift_pos_limit_glivenkoCantelli_estimated_score_core
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_le_oracle :
      pate_projectionLimit ≤ pate_oracleLimit)
    (hpate_driftLimit_pos : 0 < pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_le_oracle :
      patt_projectionLimit ≤ patt_oracleLimit)
    (hpatt_driftLimit_pos : 0 < patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_le_drift_pos_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_targetDrift pate_limit
        pate_oracleLimit pate_projectionLimit pate_targetDriftLimit
        hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_le_oracle hpate_driftLimit_pos
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_le_drift_pos_limit_glivenkoCantelli]
    using
      pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          pateEstimatedScoreBridge pattEstimatedScoreBridge
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
        pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_le_oracle hpate_driftLimit_pos
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
        hpateFirst pateCore.matching_functional_local_expansion
        pateCore.godambe_variance_identity hpattFirst
        pattCore.matching_functional_local_expansion
        pattCore.godambe_variance_identity

/--
The weak projection-slack positive-drift paired GC two-sided component-positive
Wald route with the PATE and PATT local expansion/Godambe obligations packaged
as compact local-experiment cores.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_projection_le_drift_pos_limit_glivenkoCantelli_local_experiment_core
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_le_oracle :
      pate_projectionLimit ≤ pate_oracleLimit)
    (hpate_driftLimit_pos : 0 < pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_le_oracle :
      patt_projectionLimit ≤ patt_oracleLimit)
    (hpatt_driftLimit_pos : 0 < patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_le_drift_pos_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_targetDrift pate_limit
        pate_oracleLimit pate_projectionLimit pate_targetDriftLimit
        hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_le_oracle hpate_driftLimit_pos
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_le_drift_pos_limit_glivenkoCantelli]
    using
      pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          (estimatedScoreAsymptoticBridgeOfLocalExperimentInput pateEstimated) (estimatedScoreAsymptoticBridgeOfLocalExperimentInput pattEstimated)
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
        pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_le_oracle hpate_driftLimit_pos
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
        hpateFirst
        ⟨hpateScore, pateCore.matching_functional_local_derivative,
          pateCore.local_stochastic_equicontinuity⟩
        pateCore.godambe_variance_identity hpattFirst
        ⟨hpattScore, pattCore.matching_functional_local_derivative,
          pattCore.local_stochastic_equicontinuity⟩
        pattCore.godambe_variance_identity

/--
Build the paired two-sided positive-variance Wald bridge from GC-backed finite
score-cell inputs and absolute variance-calibration inputs, using weak
projection slack and positive target drift for both PATE and PATT.
-/
def
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_le_drift_pos_limit_glivenkoCantelli
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_le_oracle :
      pate_projectionLimit ≤ pate_oracleLimit)
    (hpate_driftLimit_pos : 0 < pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_le_oracle :
      patt_projectionLimit ≤ patt_oracleLimit)
    (hpatt_driftLimit_pos : 0 < patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_le_drift_pos_limit
    (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
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
      pattKnownScoreToEstimatedScoreInput)
    pate_scaledStatistic pate_oracle pate_projectionReduction
    pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
    pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
    hpate_projectionLimit_le_oracle hpate_driftLimit_pos
    hpate_inverse_meas pateEstimatedScoreToScaledTendsto
    patt_scaledStatistic patt_oracle patt_projectionReduction
    patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
    patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
    hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
    hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
    pate_coverage_input patt_coverage_input

/--
The weak projection-slack positive-drift GC route yields paired two-sided Wald
coverage from absolute variance-calibration inputs after the finite-cell,
known-score, estimated-score, studentization, and Wald coverage obligations
are supplied.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_absolute_projection_le_drift_pos_limit_glivenkoCantelli
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_le_oracle :
      pate_projectionLimit ≤ pate_oracleLimit)
    (hpate_driftLimit_pos : 0 < pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_le_oracle :
      patt_projectionLimit ≤ patt_oracleLimit)
    (hpatt_driftLimit_pos : 0 < patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_le_drift_pos_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_targetDrift pate_limit
        pate_oracleLimit pate_projectionLimit pate_targetDriftLimit
        hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_le_oracle hpate_driftLimit_pos
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_le_drift_pos_limit_glivenkoCantelli]
    using
      pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_le_drift_pos_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          pateEstimatedScoreBridge pattEstimatedScoreBridge
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
        pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_le_oracle hpate_driftLimit_pos
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
The weak projection-slack positive-drift paired GC cross-calibrated
two-sided component-positive Wald route with the PATE and PATT local
expansion/Godambe obligations packaged as compact estimated-score cores.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_absolute_projection_le_drift_pos_limit_glivenkoCantelli_estimated_score_core
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_le_oracle :
      pate_projectionLimit ≤ pate_oracleLimit)
    (hpate_driftLimit_pos : 0 < pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_le_oracle :
      patt_projectionLimit ≤ patt_oracleLimit)
    (hpatt_driftLimit_pos : 0 < patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_le_drift_pos_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_targetDrift pate_limit
        pate_oracleLimit pate_projectionLimit pate_targetDriftLimit
        hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_le_oracle hpate_driftLimit_pos
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_le_drift_pos_limit_glivenkoCantelli]
    using
      pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_le_drift_pos_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          pateEstimatedScoreBridge pattEstimatedScoreBridge
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
        pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_le_oracle hpate_driftLimit_pos
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
        hpateFirst pateCore.matching_functional_local_expansion
        pateCore.godambe_variance_identity hpattFirst
        pattCore.matching_functional_local_expansion
        pattCore.godambe_variance_identity

/--
The weak projection-slack positive-drift paired GC cross-calibrated
two-sided component-positive Wald route with the PATE and PATT local
expansion/Godambe obligations packaged as compact local-experiment cores.
-/
theorem
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_absolute_projection_le_drift_pos_limit_glivenkoCantelli_local_experiment_core
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_le_oracle :
      pate_projectionLimit ≤ pate_oracleLimit)
    (hpate_driftLimit_pos : 0 < pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_le_oracle :
      patt_projectionLimit ≤ patt_oracleLimit)
    (hpatt_driftLimit_pos : 0 < patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_le_drift_pos_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_targetDrift pate_limit
        pate_oracleLimit pate_projectionLimit pate_targetDriftLimit
        hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_le_oracle hpate_driftLimit_pos
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_le_drift_pos_limit_glivenkoCantelli]
    using
      pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_le_drift_pos_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          (estimatedScoreAsymptoticBridgeOfLocalExperimentInput pateEstimated) (estimatedScoreAsymptoticBridgeOfLocalExperimentInput pattEstimated)
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
        pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_le_oracle hpate_driftLimit_pos
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
        hpateFirst
        ⟨hpateScore, pateCore.matching_functional_local_derivative,
          pateCore.local_stochastic_equicontinuity⟩
        pateCore.godambe_variance_identity hpattFirst
        ⟨hpattScore, pattCore.matching_functional_local_derivative,
          pattCore.local_stochastic_equicontinuity⟩
        pattCore.godambe_variance_identity

/--
Build the paired absolute positive-variance Wald bridge from GC-backed finite
score-cell inputs and two-sided variance-calibration inputs, using weak
projection slack and positive target drift for both PATE and PATT.
-/
def
    patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_le_drift_pos_limit_glivenkoCantelli
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_le_oracle :
      pate_projectionLimit ≤ pate_oracleLimit)
    (hpate_driftLimit_pos : 0 < pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_le_oracle :
      patt_projectionLimit ≤ patt_oracleLimit)
    (hpatt_driftLimit_pos : 0 < patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_le_drift_pos_limit
    (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
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
      pattKnownScoreToEstimatedScoreInput)
    pate_scaledStatistic pate_oracle pate_projectionReduction
    pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
    pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
    hpate_projectionLimit_le_oracle hpate_driftLimit_pos
    hpate_inverse_meas pateEstimatedScoreToScaledTendsto
    patt_scaledStatistic patt_oracle patt_projectionReduction
    patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
    patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
    hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
    hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
    pate_coverage_input patt_coverage_input

/--
The weak projection-slack positive-drift GC route yields paired absolute Wald
coverage from two-sided variance-calibration inputs after the finite-cell,
known-score, estimated-score, studentization, and Wald coverage obligations
are supplied.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_twoSided_projection_le_drift_pos_limit_glivenkoCantelli
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_le_oracle :
      pate_projectionLimit ≤ pate_oracleLimit)
    (hpate_driftLimit_pos : 0 < pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_le_oracle :
      patt_projectionLimit ≤ patt_oracleLimit)
    (hpatt_driftLimit_pos : 0 < patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_le_drift_pos_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_targetDrift pate_limit
        pate_oracleLimit pate_projectionLimit pate_targetDriftLimit
        hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_le_oracle hpate_driftLimit_pos
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_le_drift_pos_limit_glivenkoCantelli]
    using
      pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_le_drift_pos_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          pateEstimatedScoreBridge pattEstimatedScoreBridge
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
        pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_le_oracle hpate_driftLimit_pos
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
The weak projection-slack positive-drift paired GC cross-calibrated absolute
component-positive Wald route with the PATE and PATT local expansion/Godambe
obligations packaged as compact estimated-score cores.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_twoSided_projection_le_drift_pos_limit_glivenkoCantelli_estimated_score_core
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_le_oracle :
      pate_projectionLimit ≤ pate_oracleLimit)
    (hpate_driftLimit_pos : 0 < pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_le_oracle :
      patt_projectionLimit ≤ patt_oracleLimit)
    (hpatt_driftLimit_pos : 0 < patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_le_drift_pos_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_targetDrift pate_limit
        pate_oracleLimit pate_projectionLimit pate_targetDriftLimit
        hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_le_oracle hpate_driftLimit_pos
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_le_drift_pos_limit_glivenkoCantelli]
    using
      pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_le_drift_pos_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          pateEstimatedScoreBridge pattEstimatedScoreBridge
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
        pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_le_oracle hpate_driftLimit_pos
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
        hpateFirst pateCore.matching_functional_local_expansion
        pateCore.godambe_variance_identity hpattFirst
        pattCore.matching_functional_local_expansion
        pattCore.godambe_variance_identity

/--
The weak projection-slack positive-drift paired GC cross-calibrated absolute
component-positive Wald route with the PATE and PATT local expansion/Godambe
obligations packaged as compact local-experiment cores.
-/
theorem
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_twoSided_projection_le_drift_pos_limit_glivenkoCantelli_local_experiment_core
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
    (pate_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle pate_projectionReduction pate_targetDrift :
      Index -> Sample -> Real)
    (pate_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw pate_projectionReduction l
        (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw pate_targetDrift l
        (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_le_oracle :
      pate_projectionLimit ≤ pate_oracleLimit)
    (hpate_driftLimit_pos : 0 < pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (pate_projectionReduction index sample)
                (pate_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pateEstimatedScoreToScaledTendsto :
      pateEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (patt_scaledStatistic : Index -> Sample -> Real)
    (patt_oracle patt_projectionReduction patt_targetDrift :
      Index -> Sample -> Real)
    (patt_limit : LimitSample -> Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw patt_projectionReduction l
        (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw patt_targetDrift l
        (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_le_oracle :
      patt_projectionLimit ≤ patt_oracleLimit)
    (hpatt_driftLimit_pos : 0 < patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (patt_projectionReduction index sample)
                (patt_targetDrift index sample)))⁻¹)
          sampleLaw)
    (pattEstimatedScoreToScaledTendsto :
      pattEstimated.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
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
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldConclusion
      (patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_le_drift_pos_limit_glivenkoCantelli
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
        pattKnownScoreToEstimatedScoreInput pate_scaledStatistic pate_oracle
        pate_projectionReduction pate_targetDrift pate_limit
        pate_oracleLimit pate_projectionLimit pate_targetDriftLimit
        hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_le_oracle hpate_driftLimit_pos
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input) := by
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
    [patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_le_drift_pos_limit_glivenkoCantelli]
    using
      pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_le_drift_pos_limit
        (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
          pateCells pateReferenceShare pateSample pateWeight pateScore
          pateIndicatorBridge pateFiniteLLNToIndicatorLLN pateCLTBridge
          pateFiniteConditionsToScaled pateEnvelopeToScaled
          pateIndicatorLLNToScaled pattCells pattReferenceShare pattSample
          pattWeight pattScore pattIndicatorBridge pattFiniteLLNToIndicatorLLN
          pattCLTBridge pattFiniteConditionsToScaled pattEnvelopeToScaled
          pattIndicatorLLNToScaled pateKnownScoreBridge pattKnownScoreBridge
          pateScaledApproximationToMatchingDiscrepancy
          pattScaledApproximationToMatchingDiscrepancy
          (estimatedScoreAsymptoticBridgeOfLocalExperimentInput pateEstimated) (estimatedScoreAsymptoticBridgeOfLocalExperimentInput pattEstimated)
          pateKnownScoreToEstimatedScoreInput
          pattKnownScoreToEstimatedScoreInput)
        pate_scaledStatistic pate_oracle pate_projectionReduction
        pate_targetDrift pate_limit pate_oracleLimit pate_projectionLimit
        pate_targetDriftLimit hpate_oracle hpate_projection hpate_drift
        hpate_projectionLimit_le_oracle hpate_driftLimit_pos
        hpate_inverse_meas pateEstimatedScoreToScaledTendsto
        patt_scaledStatistic patt_oracle patt_projectionReduction
        patt_targetDrift patt_limit patt_oracleLimit patt_projectionLimit
        patt_targetDriftLimit hpatt_oracle hpatt_projection hpatt_drift
        hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
        hpatt_inverse_meas pattEstimatedScoreToScaledTendsto
        pate_coverage_input patt_coverage_input
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
        hpateFirst
        ⟨hpateScore, pateCore.matching_functional_local_derivative,
          pateCore.local_stochastic_equicontinuity⟩
        pateCore.godambe_variance_identity hpattFirst
        ⟨hpattScore, pattCore.matching_functional_local_derivative,
          pattCore.local_stochastic_equicontinuity⟩
        pattCore.godambe_variance_identity

/--
Build the paired absolute positive-variance Wald bridge from GC-backed finite
score-cell inputs and score-quadratic strict projection slack for both arms.
-/
noncomputable def
    patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_scoreAdjusted_projection_lt_limit_glivenkoCantelli
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
    (pateParameters : Finset PATEParam)
    (pattParameters : Finset PATTParam)
    (pate_scaledStatistic patt_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle patt_oracle : Index -> Sample -> Real)
    (pateFirstStepLoading pateTargetDriftLoading : PATEParam -> Real)
    (pattFirstStepLoading pattTargetDriftLoading : PATTParam -> Real)
    (pateScoreCovariance :
      Index -> Sample -> PATEParam -> PATEParam -> Real)
    (pattScoreCovariance :
      Index -> Sample -> PATTParam -> PATTParam -> Real)
    (pate_limit patt_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pateParameters pateFirstStepLoading
            (pateScoreCovariance index sample))
        l (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pateParameters pateTargetDriftLoading
            (pateScoreCovariance index sample))
        l (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_driftLimit_nonneg : 0 ≤ pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (scoreQuadraticForm pateParameters pateFirstStepLoading
                  (pateScoreCovariance index sample))
                (scoreQuadraticForm pateParameters pateTargetDriftLoading
                  (pateScoreCovariance index sample))))⁻¹)
          sampleLaw)
    (pate_estimated_score_to_scaled_tendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pattParameters pattFirstStepLoading
            (pattScoreCovariance index sample))
        l (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pattParameters pattTargetDriftLoading
            (pattScoreCovariance index sample))
        l (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_driftLimit_nonneg : 0 ≤ patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (scoreQuadraticForm pattParameters pattFirstStepLoading
                  (pattScoreCovariance index sample))
                (scoreQuadraticForm pattParameters pattTargetDriftLoading
                  (pattScoreCovariance index sample))))⁻¹)
          sampleLaw)
    (patt_estimated_score_to_scaled_tendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_studentized
    (patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_projection_lt_limit_glivenkoCantelli
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
      pattKnownScoreToEstimatedScoreInput pateParameters pattParameters
      pate_scaledStatistic patt_scaledStatistic pate_oracle patt_oracle
      pateFirstStepLoading pateTargetDriftLoading pattFirstStepLoading
      pattTargetDriftLoading pateScoreCovariance pattScoreCovariance
      pate_limit patt_limit pate_oracleLimit pate_projectionLimit
      pate_targetDriftLimit patt_oracleLimit patt_projectionLimit
      patt_targetDriftLimit hpate_oracle hpate_projection hpate_drift
      hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
      hpate_inverse_meas hpatt_oracle hpatt_projection hpatt_drift
      hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
      hpatt_inverse_meas pate_estimated_score_to_scaled_tendsto
      patt_estimated_score_to_scaled_tendsto)
    pate_coverage_input patt_coverage_input

/--
Build the paired two-sided positive-variance Wald bridge from GC-backed finite
score-cell inputs and score-quadratic strict projection slack for both arms.
-/
noncomputable def
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_scoreAdjusted_projection_lt_limit_glivenkoCantelli
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
    (pateParameters : Finset PATEParam)
    (pattParameters : Finset PATTParam)
    (pate_scaledStatistic patt_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle patt_oracle : Index -> Sample -> Real)
    (pateFirstStepLoading pateTargetDriftLoading : PATEParam -> Real)
    (pattFirstStepLoading pattTargetDriftLoading : PATTParam -> Real)
    (pateScoreCovariance :
      Index -> Sample -> PATEParam -> PATEParam -> Real)
    (pattScoreCovariance :
      Index -> Sample -> PATTParam -> PATTParam -> Real)
    (pate_limit patt_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pateParameters pateFirstStepLoading
            (pateScoreCovariance index sample))
        l (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pateParameters pateTargetDriftLoading
            (pateScoreCovariance index sample))
        l (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_lt_oracle :
      pate_projectionLimit < pate_oracleLimit)
    (hpate_driftLimit_nonneg : 0 ≤ pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (scoreQuadraticForm pateParameters pateFirstStepLoading
                  (pateScoreCovariance index sample))
                (scoreQuadraticForm pateParameters pateTargetDriftLoading
                  (pateScoreCovariance index sample))))⁻¹)
          sampleLaw)
    (pate_estimated_score_to_scaled_tendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pattParameters pattFirstStepLoading
            (pattScoreCovariance index sample))
        l (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pattParameters pattTargetDriftLoading
            (pattScoreCovariance index sample))
        l (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_lt_oracle :
      patt_projectionLimit < patt_oracleLimit)
    (hpatt_driftLimit_nonneg : 0 ≤ patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (scoreQuadraticForm pattParameters pattFirstStepLoading
                  (pattScoreCovariance index sample))
                (scoreQuadraticForm pattParameters pattTargetDriftLoading
                  (pattScoreCovariance index sample))))⁻¹)
          sampleLaw)
    (patt_estimated_score_to_scaled_tendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_studentized
    (patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_projection_lt_limit_glivenkoCantelli
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
      pattKnownScoreToEstimatedScoreInput pateParameters pattParameters
      pate_scaledStatistic patt_scaledStatistic pate_oracle patt_oracle
      pateFirstStepLoading pateTargetDriftLoading pattFirstStepLoading
      pattTargetDriftLoading pateScoreCovariance pattScoreCovariance
      pate_limit patt_limit pate_oracleLimit pate_projectionLimit
      pate_targetDriftLimit patt_oracleLimit patt_projectionLimit
      patt_targetDriftLimit hpate_oracle hpate_projection hpate_drift
      hpate_projectionLimit_lt_oracle hpate_driftLimit_nonneg
      hpate_inverse_meas hpatt_oracle hpatt_projection hpatt_drift
      hpatt_projectionLimit_lt_oracle hpatt_driftLimit_nonneg
      hpatt_inverse_meas pate_estimated_score_to_scaled_tendsto
      patt_estimated_score_to_scaled_tendsto)
    pate_coverage_input patt_coverage_input

/--
Build the paired absolute positive-variance Wald bridge from GC-backed finite
score-cell inputs, score-quadratic weak projection slack, and positive
target-drift limits for both arms.
-/
noncomputable def
    patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_scoreAdjusted_projection_le_drift_pos_limit_glivenkoCantelli
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
    (pateParameters : Finset PATEParam)
    (pattParameters : Finset PATTParam)
    (pate_scaledStatistic patt_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle patt_oracle : Index -> Sample -> Real)
    (pateFirstStepLoading pateTargetDriftLoading : PATEParam -> Real)
    (pattFirstStepLoading pattTargetDriftLoading : PATTParam -> Real)
    (pateScoreCovariance :
      Index -> Sample -> PATEParam -> PATEParam -> Real)
    (pattScoreCovariance :
      Index -> Sample -> PATTParam -> PATTParam -> Real)
    (pate_limit patt_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pateParameters pateFirstStepLoading
            (pateScoreCovariance index sample))
        l (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pateParameters pateTargetDriftLoading
            (pateScoreCovariance index sample))
        l (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_le_oracle :
      pate_projectionLimit ≤ pate_oracleLimit)
    (hpate_driftLimit_pos : 0 < pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (scoreQuadraticForm pateParameters pateFirstStepLoading
                  (pateScoreCovariance index sample))
                (scoreQuadraticForm pateParameters pateTargetDriftLoading
                  (pateScoreCovariance index sample))))⁻¹)
          sampleLaw)
    (pate_estimated_score_to_scaled_tendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pattParameters pattFirstStepLoading
            (pattScoreCovariance index sample))
        l (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pattParameters pattTargetDriftLoading
            (pattScoreCovariance index sample))
        l (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_le_oracle :
      patt_projectionLimit ≤ patt_oracleLimit)
    (hpatt_driftLimit_pos : 0 < patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (scoreQuadraticForm pattParameters pattFirstStepLoading
                  (pattScoreCovariance index sample))
                (scoreQuadraticForm pattParameters pattTargetDriftLoading
                  (pattScoreCovariance index sample))))⁻¹)
          sampleLaw)
    (patt_estimated_score_to_scaled_tendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_studentized
    (patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_projection_le_drift_pos_limit_glivenkoCantelli
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
      pattKnownScoreToEstimatedScoreInput pateParameters pattParameters
      pate_scaledStatistic patt_scaledStatistic pate_oracle patt_oracle
      pateFirstStepLoading pateTargetDriftLoading pattFirstStepLoading
      pattTargetDriftLoading pateScoreCovariance pattScoreCovariance
      pate_limit patt_limit pate_oracleLimit pate_projectionLimit
      pate_targetDriftLimit patt_oracleLimit patt_projectionLimit
      patt_targetDriftLimit hpate_oracle hpate_projection hpate_drift
      hpate_projectionLimit_le_oracle hpate_driftLimit_pos
      hpate_inverse_meas hpatt_oracle hpatt_projection hpatt_drift
      hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
      hpatt_inverse_meas pate_estimated_score_to_scaled_tendsto
      patt_estimated_score_to_scaled_tendsto)
    pate_coverage_input patt_coverage_input

/--
Build the paired two-sided positive-variance Wald bridge from GC-backed finite
score-cell inputs, score-quadratic weak projection slack, and positive
target-drift limits for both arms.
-/
noncomputable def
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_scoreAdjusted_projection_le_drift_pos_limit_glivenkoCantelli
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
    (pateParameters : Finset PATEParam)
    (pattParameters : Finset PATTParam)
    (pate_scaledStatistic patt_scaledStatistic : Index -> Sample -> Real)
    (pate_oracle patt_oracle : Index -> Sample -> Real)
    (pateFirstStepLoading pateTargetDriftLoading : PATEParam -> Real)
    (pattFirstStepLoading pattTargetDriftLoading : PATTParam -> Real)
    (pateScoreCovariance :
      Index -> Sample -> PATEParam -> PATEParam -> Real)
    (pattScoreCovariance :
      Index -> Sample -> PATTParam -> PATTParam -> Real)
    (pate_limit patt_limit : LimitSample -> Real)
    (pate_oracleLimit pate_projectionLimit pate_targetDriftLimit : Real)
    (patt_oracleLimit patt_projectionLimit patt_targetDriftLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pate_oracle l
        (fun _sample => pate_oracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pateParameters pateFirstStepLoading
            (pateScoreCovariance index sample))
        l (fun _sample => pate_projectionLimit))
    (hpate_drift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pateParameters pateTargetDriftLoading
            (pateScoreCovariance index sample))
        l (fun _sample => pate_targetDriftLimit))
    (hpate_projectionLimit_le_oracle :
      pate_projectionLimit ≤ pate_oracleLimit)
    (hpate_driftLimit_pos : 0 < pate_targetDriftLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pate_oracle index sample)
                (scoreQuadraticForm pateParameters pateFirstStepLoading
                  (pateScoreCovariance index sample))
                (scoreQuadraticForm pateParameters pateTargetDriftLoading
                  (pateScoreCovariance index sample))))⁻¹)
          sampleLaw)
    (pate_estimated_score_to_scaled_tendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pate_scaledStatistic l pate_limit
          (fun _index => sampleLaw) limitLaw)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw patt_oracle l
        (fun _sample => patt_oracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pattParameters pattFirstStepLoading
            (pattScoreCovariance index sample))
        l (fun _sample => patt_projectionLimit))
    (hpatt_drift :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pattParameters pattTargetDriftLoading
            (pattScoreCovariance index sample))
        l (fun _sample => patt_targetDriftLimit))
    (hpatt_projectionLimit_le_oracle :
      patt_projectionLimit ≤ patt_oracleLimit)
    (hpatt_driftLimit_pos : 0 < patt_targetDriftLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (patt_oracle index sample)
                (scoreQuadraticForm pattParameters pattFirstStepLoading
                  (pattScoreCovariance index sample))
                (scoreQuadraticForm pattParameters pattTargetDriftLoading
                  (pattScoreCovariance index sample))))⁻¹)
          sampleLaw)
    (patt_estimated_score_to_scaled_tendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution patt_scaledStatistic l patt_limit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_studentized
    (patePATTFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_scoreAdjusted_projection_le_drift_pos_limit_glivenkoCantelli
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
      pattKnownScoreToEstimatedScoreInput pateParameters pattParameters
      pate_scaledStatistic patt_scaledStatistic pate_oracle patt_oracle
      pateFirstStepLoading pateTargetDriftLoading pattFirstStepLoading
      pattTargetDriftLoading pateScoreCovariance pattScoreCovariance
      pate_limit patt_limit pate_oracleLimit pate_projectionLimit
      pate_targetDriftLimit patt_oracleLimit patt_projectionLimit
      patt_targetDriftLimit hpate_oracle hpate_projection hpate_drift
      hpate_projectionLimit_le_oracle hpate_driftLimit_pos
      hpate_inverse_meas hpatt_oracle hpatt_projection hpatt_drift
      hpatt_projectionLimit_le_oracle hpatt_driftLimit_pos
      hpatt_inverse_meas pate_estimated_score_to_scaled_tendsto
      patt_estimated_score_to_scaled_tendsto)
    pate_coverage_input patt_coverage_input

/--
Build the paired absolute positive-variance Wald bridge from GC-backed finite
score-cell inputs and fixed-law score-quadratic strict projection slack for
both arms.
-/
noncomputable def
    patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_scoreAdjusted_fixedLaw_projection_lt_limit_glivenkoCantelli
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
    (pateParameters : Finset PATEParam)
    (pattParameters : Finset PATTParam)
    (pateScaledStatistic pattScaledStatistic : Index -> Sample -> Real)
    (pateOracle pattOracle : Index -> Sample -> Real)
    (pateFirstStepLoading : PATEParam -> Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pateScoreCovariance : Index -> Sample -> PATEParam -> PATEParam -> Real)
    (pattScoreCovariance : Index -> Sample -> PATTParam -> PATTParam -> Real)
    (pateLimit pattLimit : LimitSample -> Real)
    (pateOracleLimit pateProjectionLimit : Real)
    (pattOracleLimit pattProjectionLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pateOracle l
        (fun _sample => pateOracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pateParameters pateFirstStepLoading
            (pateScoreCovariance index sample))
        l (fun _sample => pateProjectionLimit))
    (hpate_projection_lt_oracle :
      pateProjectionLimit < pateOracleLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pateOracle index sample)
                (scoreQuadraticForm pateParameters pateFirstStepLoading
                  (pateScoreCovariance index sample)) 0))⁻¹)
          sampleLaw)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw pattOracle l
        (fun _sample => pattOracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pattParameters pattFirstStepLoading
            (pattScoreCovariance index sample))
        l (fun _sample => pattProjectionLimit))
    (hpatt_projection_lt_oracle :
      pattProjectionLimit < pattOracleLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pattOracle index sample)
                (scoreQuadraticForm pattParameters pattFirstStepLoading
                  (pattScoreCovariance index sample)) 0))⁻¹)
          sampleLaw)
    (hpate_estimated_score_to_scaled_tendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pateScaledStatistic l pateLimit
          (fun _index => sampleLaw) limitLaw)
    (hpatt_estimated_score_to_scaled_tendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pattScaledStatistic l pattLimit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_scoreAdjusted_fixedLaw_projection_lt_limit
    (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
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
      pattKnownScoreToEstimatedScoreInput)
    pateParameters pattParameters pateScaledStatistic pattScaledStatistic
    pateOracle pattOracle pateFirstStepLoading pattFirstStepLoading
    pateScoreCovariance pattScoreCovariance pateLimit pattLimit
    pateOracleLimit pateProjectionLimit pattOracleLimit pattProjectionLimit
    hpate_oracle hpate_projection hpate_projection_lt_oracle
    hpate_inverse_meas hpate_estimated_score_to_scaled_tendsto
    hpatt_oracle hpatt_projection hpatt_projection_lt_oracle
    hpatt_inverse_meas hpatt_estimated_score_to_scaled_tendsto
    pate_coverage_input patt_coverage_input

/--
Build the paired two-sided positive-variance Wald bridge from GC-backed finite
score-cell inputs and fixed-law score-quadratic strict projection slack for
both arms.
-/
noncomputable def
    patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_scoreAdjusted_fixedLaw_projection_lt_limit_glivenkoCantelli
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
    (pateParameters : Finset PATEParam)
    (pattParameters : Finset PATTParam)
    (pateScaledStatistic pattScaledStatistic : Index -> Sample -> Real)
    (pateOracle pattOracle : Index -> Sample -> Real)
    (pateFirstStepLoading : PATEParam -> Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pateScoreCovariance : Index -> Sample -> PATEParam -> PATEParam -> Real)
    (pattScoreCovariance : Index -> Sample -> PATTParam -> PATTParam -> Real)
    (pateLimit pattLimit : LimitSample -> Real)
    (pateOracleLimit pateProjectionLimit : Real)
    (pattOracleLimit pattProjectionLimit : Real)
    (hpate_oracle :
      TendstoInMeasure sampleLaw pateOracle l
        (fun _sample => pateOracleLimit))
    (hpate_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pateParameters pateFirstStepLoading
            (pateScoreCovariance index sample))
        l (fun _sample => pateProjectionLimit))
    (hpate_projection_lt_oracle :
      pateProjectionLimit < pateOracleLimit)
    (hpate_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pateOracle index sample)
                (scoreQuadraticForm pateParameters pateFirstStepLoading
                  (pateScoreCovariance index sample)) 0))⁻¹)
          sampleLaw)
    (hpatt_oracle :
      TendstoInMeasure sampleLaw pattOracle l
        (fun _sample => pattOracleLimit))
    (hpatt_projection :
      TendstoInMeasure sampleLaw
        (fun index sample =>
          scoreQuadraticForm pattParameters pattFirstStepLoading
            (pattScoreCovariance index sample))
        l (fun _sample => pattProjectionLimit))
    (hpatt_projection_lt_oracle :
      pattProjectionLimit < pattOracleLimit)
    (hpatt_inverse_meas :
      ∀ index,
        AEMeasurable
          (fun sample =>
            (standardError
              (estimatedScoreVariance (pattOracle index sample)
                (scoreQuadraticForm pattParameters pattFirstStepLoading
                  (pattScoreCovariance index sample)) 0))⁻¹)
          sampleLaw)
    (hpate_estimated_score_to_scaled_tendsto :
      pateEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pateScaledStatistic l pateLimit
          (fun _index => sampleLaw) limitLaw)
    (hpatt_estimated_score_to_scaled_tendsto :
      pattEstimatedScoreBridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution pattScaledStatistic l pattLimit
          (fun _index => sampleLaw) limitLaw)
    (pate_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (patt_coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATEPATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge
      PATECell PATTCell Index Sample LimitSample sampleLaw limitLaw l :=
  patePATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_scoreAdjusted_fixedLaw_projection_lt_limit
    (patePattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
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
      pattKnownScoreToEstimatedScoreInput)
    pateParameters pattParameters pateScaledStatistic pattScaledStatistic
    pateOracle pattOracle pateFirstStepLoading pattFirstStepLoading
    pateScoreCovariance pattScoreCovariance pateLimit pattLimit
    pateOracleLimit pateProjectionLimit pattOracleLimit pattProjectionLimit
    hpate_oracle hpate_projection hpate_projection_lt_oracle
    hpate_inverse_meas hpate_estimated_score_to_scaled_tendsto
    hpatt_oracle hpatt_projection hpatt_projection_lt_oracle
    hpatt_inverse_meas hpatt_estimated_score_to_scaled_tendsto
    pate_coverage_input patt_coverage_input

end WDSM
end Matching
end StatInference
