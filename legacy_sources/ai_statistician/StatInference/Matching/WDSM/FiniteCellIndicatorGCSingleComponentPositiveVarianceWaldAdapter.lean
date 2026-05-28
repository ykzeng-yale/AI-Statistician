import StatInference.Matching.WDSM.FiniteCellIndicatorGCSingleComponentPositiveVarianceAdapter
import StatInference.Matching.WDSM.FiniteCellIndicatorEstimatedScoreComponentPositiveVarianceWaldBridge

/-!
# GC-backed single-arm component-positive Wald bridge constructors

This module connects single-arm GC finite score-cell estimated-score bridges to
component-positive positive-variance Wald bridge constructors.  It provides
bridge objects only; direct coverage wrappers are kept for a separate layer.
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

/-! ## PATE absolute strict route -/

/--
Build a PATE absolute component-positive Wald bridge from GC-backed
finite score-cell inputs, strict projection slack and nonnegative target drift.
-/
def pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_lt_limit_glivenkoCantelli
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
    (coverageInput : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_lt_limit
    (pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    scaledStatistic oracle projectionReduction targetDrift limit oracleLimit
    projectionLimit targetDriftLimit horacle hprojection hdrift
    hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
    estimatedScoreToScaledTendsto coverageInput

/-! ## PATE two-sided strict route -/

/--
Build a PATE two-sided component-positive Wald bridge from GC-backed
finite score-cell inputs, strict projection slack and nonnegative target drift.
-/
def pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_lt_limit_glivenkoCantelli
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
    (coverageInput : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_lt_limit
    (pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    scaledStatistic oracle projectionReduction targetDrift limit oracleLimit
    projectionLimit targetDriftLimit horacle hprojection hdrift
    hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
    estimatedScoreToScaledTendsto coverageInput

/-! ## PATE absolute weak route -/

/--
Build a PATE absolute component-positive Wald bridge from GC-backed
finite score-cell inputs, weak projection slack and positive target drift.
-/
def pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_le_drift_pos_limit_glivenkoCantelli
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
    (coverageInput : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_le_drift_pos_limit
    (pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    scaledStatistic oracle projectionReduction targetDrift limit oracleLimit
    projectionLimit targetDriftLimit horacle hprojection hdrift
    hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
    estimatedScoreToScaledTendsto coverageInput

/-! ## PATE two-sided weak route -/

/--
Build a PATE two-sided component-positive Wald bridge from GC-backed
finite score-cell inputs, weak projection slack and positive target drift.
-/
def pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_le_drift_pos_limit_glivenkoCantelli
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
    (coverageInput : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_le_drift_pos_limit
    (pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    scaledStatistic oracle projectionReduction targetDrift limit oracleLimit
    projectionLimit targetDriftLimit horacle hprojection hdrift
    hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
    estimatedScoreToScaledTendsto coverageInput

/-! ## PATE absolute fixed route -/

/--
Build a PATE absolute component-positive Wald bridge from GC-backed
finite score-cell inputs, fixed-law strict projection slack.
-/
def pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli
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
    (coverageInput : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit
    (pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    scaledStatistic oracle projectionReduction limit oracleLimit
    projectionLimit horacle hprojection hprojectionLimit_lt_oracle
    hinverse_meas estimatedScoreToScaledTendsto coverageInput

/-! ## PATE two-sided fixed route -/

/--
Build a PATE two-sided component-positive Wald bridge from GC-backed
finite score-cell inputs, fixed-law strict projection slack.
-/
def pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli
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
    (coverageInput : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit
    (pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    scaledStatistic oracle projectionReduction limit oracleLimit
    projectionLimit horacle hprojection hprojectionLimit_lt_oracle
    hinverse_meas estimatedScoreToScaledTendsto coverageInput

/-! ## PATT absolute strict route -/

/--
Build a PATT absolute component-positive Wald bridge from GC-backed
finite score-cell inputs, strict projection slack and nonnegative target drift.
-/
def pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_lt_limit_glivenkoCantelli
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
    (coverageInput : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_lt_limit
    (pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    scaledStatistic oracle projectionReduction targetDrift limit oracleLimit
    projectionLimit targetDriftLimit horacle hprojection hdrift
    hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
    estimatedScoreToScaledTendsto coverageInput

/-! ## PATT two-sided strict route -/

/--
Build a PATT two-sided component-positive Wald bridge from GC-backed
finite score-cell inputs, strict projection slack and nonnegative target drift.
-/
def pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_lt_limit_glivenkoCantelli
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
    (coverageInput : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_lt_limit
    (pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    scaledStatistic oracle projectionReduction targetDrift limit oracleLimit
    projectionLimit targetDriftLimit horacle hprojection hdrift
    hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
    estimatedScoreToScaledTendsto coverageInput

/-! ## PATT absolute weak route -/

/--
Build a PATT absolute component-positive Wald bridge from GC-backed
finite score-cell inputs, weak projection slack and positive target drift.
-/
def pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_le_drift_pos_limit_glivenkoCantelli
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
    (coverageInput : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_le_drift_pos_limit
    (pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    scaledStatistic oracle projectionReduction targetDrift limit oracleLimit
    projectionLimit targetDriftLimit horacle hprojection hdrift
    hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
    estimatedScoreToScaledTendsto coverageInput

/-! ## PATT two-sided weak route -/

/--
Build a PATT two-sided component-positive Wald bridge from GC-backed
finite score-cell inputs, weak projection slack and positive target drift.
-/
def pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_le_drift_pos_limit_glivenkoCantelli
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
    (coverageInput : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_le_drift_pos_limit
    (pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    scaledStatistic oracle projectionReduction targetDrift limit oracleLimit
    projectionLimit targetDriftLimit horacle hprojection hdrift
    hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
    estimatedScoreToScaledTendsto coverageInput

/-! ## PATT absolute fixed route -/

/--
Build a PATT absolute component-positive Wald bridge from GC-backed
finite score-cell inputs, fixed-law strict projection slack.
-/
def pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli
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
    (coverageInput : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit
    (pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    scaledStatistic oracle projectionReduction limit oracleLimit
    projectionLimit horacle hprojection hprojectionLimit_lt_oracle
    hinverse_meas estimatedScoreToScaledTendsto coverageInput

/-! ## PATT two-sided fixed route -/

/--
Build a PATT two-sided component-positive Wald bridge from GC-backed
finite score-cell inputs, fixed-law strict projection slack.
-/
def pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit_glivenkoCantelli
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
    (coverageInput : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit
    (pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    scaledStatistic oracle projectionReduction limit oracleLimit
    projectionLimit horacle hprojection hprojectionLimit_lt_oracle
    hinverse_meas estimatedScoreToScaledTendsto coverageInput


/-! ## Cross-calibrated bridge constructors -/

/-! ## PATE two-sided from absolute projection_lt_limit -/

/--
Build a PATE two-sided component-positive Wald bridge from absolute
variance-based calibration inputs, GC-backed finite score-cell inputs, and
strict projection slack and nonnegative target drift.
-/
def pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_lt_limit_glivenkoCantelli
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
    (coverageInput : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_lt_limit
    (pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    scaledStatistic oracle projectionReduction targetDrift limit oracleLimit
    projectionLimit targetDriftLimit horacle hprojection hdrift
    hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
    estimatedScoreToScaledTendsto coverageInput

/-! ## PATE absolute from two-sided projection_lt_limit -/

/--
Build a PATE absolute component-positive Wald bridge from two-sided
variance-based calibration inputs, GC-backed finite score-cell inputs, and
strict projection slack and nonnegative target drift.
-/
def pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_lt_limit_glivenkoCantelli
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
    (coverageInput : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_lt_limit
    (pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    scaledStatistic oracle projectionReduction targetDrift limit oracleLimit
    projectionLimit targetDriftLimit horacle hprojection hdrift
    hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
    estimatedScoreToScaledTendsto coverageInput

/-! ## PATE two-sided from absolute projection_le_drift_pos_limit -/

/--
Build a PATE two-sided component-positive Wald bridge from absolute
variance-based calibration inputs, GC-backed finite score-cell inputs, and
weak projection slack and positive target drift.
-/
def pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_le_drift_pos_limit_glivenkoCantelli
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
    (coverageInput : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_le_drift_pos_limit
    (pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    scaledStatistic oracle projectionReduction targetDrift limit oracleLimit
    projectionLimit targetDriftLimit horacle hprojection hdrift
    hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
    estimatedScoreToScaledTendsto coverageInput

/-! ## PATE absolute from two-sided projection_le_drift_pos_limit -/

/--
Build a PATE absolute component-positive Wald bridge from two-sided
variance-based calibration inputs, GC-backed finite score-cell inputs, and
weak projection slack and positive target drift.
-/
def pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_le_drift_pos_limit_glivenkoCantelli
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
    (coverageInput : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_le_drift_pos_limit
    (pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    scaledStatistic oracle projectionReduction targetDrift limit oracleLimit
    projectionLimit targetDriftLimit horacle hprojection hdrift
    hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
    estimatedScoreToScaledTendsto coverageInput

/-! ## PATE two-sided from absolute fixedLaw_projection_lt_limit -/

/--
Build a PATE two-sided component-positive Wald bridge from absolute
variance-based calibration inputs, GC-backed finite score-cell inputs, and
fixed-law strict projection slack.
-/
def pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_fixedLaw_projection_lt_limit_glivenkoCantelli
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
    (coverageInput : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_fixedLaw_projection_lt_limit
    (pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    scaledStatistic oracle projectionReduction limit oracleLimit
    projectionLimit horacle hprojection hprojectionLimit_lt_oracle
    hinverse_meas estimatedScoreToScaledTendsto coverageInput

/-! ## PATE absolute from two-sided fixedLaw_projection_lt_limit -/

/--
Build a PATE absolute component-positive Wald bridge from two-sided
variance-based calibration inputs, GC-backed finite score-cell inputs, and
fixed-law strict projection slack.
-/
def pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_fixedLaw_projection_lt_limit_glivenkoCantelli
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
    (coverageInput : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_fixedLaw_projection_lt_limit
    (pateFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    scaledStatistic oracle projectionReduction limit oracleLimit
    projectionLimit horacle hprojection hprojectionLimit_lt_oracle
    hinverse_meas estimatedScoreToScaledTendsto coverageInput

/-! ## PATT two-sided from absolute projection_lt_limit -/

/--
Build a PATT two-sided component-positive Wald bridge from absolute
variance-based calibration inputs, GC-backed finite score-cell inputs, and
strict projection slack and nonnegative target drift.
-/
def pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_lt_limit_glivenkoCantelli
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
    (coverageInput : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_lt_limit
    (pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    scaledStatistic oracle projectionReduction targetDrift limit oracleLimit
    projectionLimit targetDriftLimit horacle hprojection hdrift
    hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
    estimatedScoreToScaledTendsto coverageInput

/-! ## PATT absolute from two-sided projection_lt_limit -/

/--
Build a PATT absolute component-positive Wald bridge from two-sided
variance-based calibration inputs, GC-backed finite score-cell inputs, and
strict projection slack and nonnegative target drift.
-/
def pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_lt_limit_glivenkoCantelli
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
    (coverageInput : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_lt_limit
    (pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    scaledStatistic oracle projectionReduction targetDrift limit oracleLimit
    projectionLimit targetDriftLimit horacle hprojection hdrift
    hprojectionLimit_lt_oracle hdriftLimit_nonneg hinverse_meas
    estimatedScoreToScaledTendsto coverageInput

/-! ## PATT two-sided from absolute projection_le_drift_pos_limit -/

/--
Build a PATT two-sided component-positive Wald bridge from absolute
variance-based calibration inputs, GC-backed finite score-cell inputs, and
weak projection slack and positive target drift.
-/
def pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_le_drift_pos_limit_glivenkoCantelli
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
    (coverageInput : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_projection_le_drift_pos_limit
    (pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    scaledStatistic oracle projectionReduction targetDrift limit oracleLimit
    projectionLimit targetDriftLimit horacle hprojection hdrift
    hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
    estimatedScoreToScaledTendsto coverageInput

/-! ## PATT absolute from two-sided projection_le_drift_pos_limit -/

/--
Build a PATT absolute component-positive Wald bridge from two-sided
variance-based calibration inputs, GC-backed finite score-cell inputs, and
weak projection slack and positive target drift.
-/
def pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_le_drift_pos_limit_glivenkoCantelli
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
    (coverageInput : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_projection_le_drift_pos_limit
    (pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    scaledStatistic oracle projectionReduction targetDrift limit oracleLimit
    projectionLimit targetDriftLimit horacle hprojection hdrift
    hprojectionLimit_le_oracle hdriftLimit_pos hinverse_meas
    estimatedScoreToScaledTendsto coverageInput

/-! ## PATT two-sided from absolute fixedLaw_projection_lt_limit -/

/--
Build a PATT two-sided component-positive Wald bridge from absolute
variance-based calibration inputs, GC-backed finite score-cell inputs, and
fixed-law strict projection slack.
-/
def pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_fixedLaw_projection_lt_limit_glivenkoCantelli
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
    (coverageInput : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_absolute_fixedLaw_projection_lt_limit
    (pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    scaledStatistic oracle projectionReduction limit oracleLimit
    projectionLimit horacle hprojection hprojectionLimit_lt_oracle
    hinverse_meas estimatedScoreToScaledTendsto coverageInput

/-! ## PATT absolute from two-sided fixedLaw_projection_lt_limit -/

/--
Build a PATT absolute component-positive Wald bridge from two-sided
variance-based calibration inputs, GC-backed finite score-cell inputs, and
fixed-law strict projection slack.
-/
def pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_fixedLaw_projection_lt_limit_glivenkoCantelli
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
    (coverageInput : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l :=
  pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_twoSided_fixedLaw_projection_lt_limit
    (pattFiniteScoreCellEstimatedScoreAsymptoticBridgeOfGlivenkoCantelli
      cells referenceShare sample weight score indicatorBridge
      finiteLLNToIndicatorLLN cltBridge finiteConditionsToScaled
      envelopeToScaled indicatorLLNToScaled knownScoreBridge
      scaledApproximationToMatchingDiscrepancy estimatedScoreBridge
      knownScoreToEstimatedScoreInput)
    scaledStatistic oracle projectionReduction limit oracleLimit
    projectionLimit horacle hprojection hprojectionLimit_lt_oracle
    hinverse_meas estimatedScoreToScaledTendsto coverageInput


end WDSM
end Matching
end StatInference
