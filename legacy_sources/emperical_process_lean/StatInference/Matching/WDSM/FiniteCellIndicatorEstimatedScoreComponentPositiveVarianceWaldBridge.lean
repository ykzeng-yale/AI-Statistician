import StatInference.Matching.WDSM.FiniteCellIndicatorEstimatedScoreComponentPositiveVarianceStudentizedBridge
import StatInference.Matching.WDSM.FiniteCellIndicatorEstimatedScorePositiveVarianceWaldBridge

/-!
# Estimated-score Wald bridge constructors from component positivity

This module packages the component-positive estimated-score studentization
constructors into the finite score-cell PATE/PATT Wald bridge objects.  It
removes another manual assembly step from the final estimated-score inference
layer.
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

/-! ## PATE absolute Wald bridge constructors -/

/-- PATE absolute Wald bridge from strict projection slack and nonnegative drift. -/
def pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_lt_limit
    (finite_estimated_bridge :
      PATEFiniteScoreCellEstimatedScoreAsymptoticBridge Cell)
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
    (estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
    (coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l where
  studentized_bridge :=
    pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_lt_limit
      finite_estimated_bridge scaledStatistic oracle projectionReduction
      targetDrift limit oracleLimit projectionLimit targetDriftLimit horacle
      hprojection hdrift hprojectionLimit_lt_oracle hdriftLimit_nonneg
      hinverse_meas estimated_score_to_scaled_tendsto
  coverage_input := coverage_input

/-- PATE absolute Wald bridge from weak projection slack and positive drift. -/
def pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_le_drift_pos_limit
    (finite_estimated_bridge :
      PATEFiniteScoreCellEstimatedScoreAsymptoticBridge Cell)
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
    (estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
    (coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l where
  studentized_bridge :=
    pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_le_drift_pos_limit
      finite_estimated_bridge scaledStatistic oracle projectionReduction
      targetDrift limit oracleLimit projectionLimit targetDriftLimit horacle
      hprojection hdrift hprojectionLimit_le_oracle hdriftLimit_pos
      hinverse_meas estimated_score_to_scaled_tendsto
  coverage_input := coverage_input

/-- PATE absolute Wald bridge from fixed-law strict projection slack. -/
def pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit
    (finite_estimated_bridge :
      PATEFiniteScoreCellEstimatedScoreAsymptoticBridge Cell)
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
    (estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
    (coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATEFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l where
  studentized_bridge :=
    pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_fixedLaw_projection_lt_limit
      finite_estimated_bridge scaledStatistic oracle projectionReduction limit
      oracleLimit projectionLimit horacle hprojection
      hprojectionLimit_lt_oracle hinverse_meas
      estimated_score_to_scaled_tendsto
  coverage_input := coverage_input

/-! ## PATT two-sided Wald bridge constructors -/

/-- PATT two-sided Wald bridge from weak projection slack and positive drift. -/
def pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_le_drift_pos_limit
    (finite_estimated_bridge :
      PATTFiniteScoreCellEstimatedScoreAsymptoticBridge Cell)
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
    (estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
    (coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l where
  studentized_bridge :=
    pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_le_drift_pos_limit
      finite_estimated_bridge scaledStatistic oracle projectionReduction
      targetDrift limit oracleLimit projectionLimit targetDriftLimit horacle
      hprojection hdrift hprojectionLimit_le_oracle hdriftLimit_pos
      hinverse_meas estimated_score_to_scaled_tendsto
  coverage_input := coverage_input

/-- PATT two-sided Wald bridge from fixed-law strict projection slack. -/
def pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit
    (finite_estimated_bridge :
      PATTFiniteScoreCellEstimatedScoreAsymptoticBridge Cell)
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
    (estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
    (coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l where
  studentized_bridge :=
    pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_fixedLaw_projection_lt_limit
      finite_estimated_bridge scaledStatistic oracle projectionReduction limit
      oracleLimit projectionLimit horacle hprojection
      hprojectionLimit_lt_oracle hinverse_meas
      estimated_score_to_scaled_tendsto
  coverage_input := coverage_input

/-- PATE two-sided Wald bridge from strict projection slack and nonnegative drift. -/
def pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_lt_limit
    (finite_estimated_bridge :
      PATEFiniteScoreCellEstimatedScoreAsymptoticBridge Cell)
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
    (estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
    (coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l where
  studentized_bridge :=
    pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_lt_limit
      finite_estimated_bridge scaledStatistic oracle projectionReduction
      targetDrift limit oracleLimit projectionLimit targetDriftLimit horacle
      hprojection hdrift hprojectionLimit_lt_oracle hdriftLimit_nonneg
      hinverse_meas estimated_score_to_scaled_tendsto
  coverage_input := coverage_input

/-- PATE two-sided Wald bridge from weak projection slack and positive drift. -/
def pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_le_drift_pos_limit
    (finite_estimated_bridge :
      PATEFiniteScoreCellEstimatedScoreAsymptoticBridge Cell)
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
    (estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
    (coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l where
  studentized_bridge :=
    pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_le_drift_pos_limit
      finite_estimated_bridge scaledStatistic oracle projectionReduction
      targetDrift limit oracleLimit projectionLimit targetDriftLimit horacle
      hprojection hdrift hprojectionLimit_le_oracle hdriftLimit_pos
      hinverse_meas estimated_score_to_scaled_tendsto
  coverage_input := coverage_input

/-- PATE two-sided Wald bridge from fixed-law strict projection slack. -/
def pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit
    (finite_estimated_bridge :
      PATEFiniteScoreCellEstimatedScoreAsymptoticBridge Cell)
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
    (estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
    (coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATEFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l where
  studentized_bridge :=
    pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_fixedLaw_projection_lt_limit
      finite_estimated_bridge scaledStatistic oracle projectionReduction limit
      oracleLimit projectionLimit horacle hprojection
      hprojectionLimit_lt_oracle hinverse_meas
      estimated_score_to_scaled_tendsto
  coverage_input := coverage_input

/-! ## PATT absolute Wald bridge constructors -/

/-- PATT absolute Wald bridge from strict projection slack and nonnegative drift. -/
def pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_lt_limit
    (finite_estimated_bridge :
      PATTFiniteScoreCellEstimatedScoreAsymptoticBridge Cell)
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
    (estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
    (coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l where
  studentized_bridge :=
    pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_lt_limit
      finite_estimated_bridge scaledStatistic oracle projectionReduction
      targetDrift limit oracleLimit projectionLimit targetDriftLimit horacle
      hprojection hdrift hprojectionLimit_lt_oracle hdriftLimit_nonneg
      hinverse_meas estimated_score_to_scaled_tendsto
  coverage_input := coverage_input

/-- PATT absolute Wald bridge from weak projection slack and positive drift. -/
def pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_le_drift_pos_limit
    (finite_estimated_bridge :
      PATTFiniteScoreCellEstimatedScoreAsymptoticBridge Cell)
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
    (estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
    (coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l where
  studentized_bridge :=
    pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_le_drift_pos_limit
      finite_estimated_bridge scaledStatistic oracle projectionReduction
      targetDrift limit oracleLimit projectionLimit targetDriftLimit horacle
      hprojection hdrift hprojectionLimit_le_oracle hdriftLimit_pos
      hinverse_meas estimated_score_to_scaled_tendsto
  coverage_input := coverage_input

/-- PATT absolute Wald bridge from fixed-law strict projection slack. -/
def pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit
    (finite_estimated_bridge :
      PATTFiniteScoreCellEstimatedScoreAsymptoticBridge Cell)
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
    (estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
    (coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l) :
    PATTFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l where
  studentized_bridge :=
    pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_fixedLaw_projection_lt_limit
      finite_estimated_bridge scaledStatistic oracle projectionReduction limit
      oracleLimit projectionLimit horacle hprojection
      hprojectionLimit_lt_oracle hinverse_meas
      estimated_score_to_scaled_tendsto
  coverage_input := coverage_input

/-! ## PATT two-sided Wald bridge constructors -/

/-- PATT two-sided Wald bridge from strict projection slack and nonnegative drift. -/
def pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_lt_limit
    (finite_estimated_bridge :
      PATTFiniteScoreCellEstimatedScoreAsymptoticBridge Cell)
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
    (estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
    (coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l) :
    PATTFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge Cell
      Index Sample LimitSample sampleLaw limitLaw l where
  studentized_bridge :=
    pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_lt_limit
      finite_estimated_bridge scaledStatistic oracle projectionReduction
      targetDrift limit oracleLimit projectionLimit targetDriftLimit horacle
      hprojection hdrift hprojectionLimit_lt_oracle hdriftLimit_nonneg
      hinverse_meas estimated_score_to_scaled_tendsto
  coverage_input := coverage_input

/-! ## Direct PATE coverage theorems -/

/--
PATE absolute finite score-cell estimated-score Wald coverage directly from
strict projection slack and nonnegative target drift.
-/
theorem
    pate_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit
    (finite_estimated_bridge :
      PATEFiniteScoreCellEstimatedScoreAsymptoticBridge Cell)
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
    (estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
    (coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (hdesign :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.aggregate_hajek_decomposition)
    (hdenominator :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.denominator_stabilization)
    (hheterogeneity :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.heterogeneity_clt)
    (hresidual :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.residual_clt)
    (hfirst :
      finite_estimated_bridge.estimated_score_bridge.first_step_asymptotic_linearization)
    (hlocal :
      finite_estimated_bridge.estimated_score_bridge.matching_functional_local_expansion)
    (hgodambe :
      finite_estimated_bridge.estimated_score_bridge.godambe_variance_identity) :
    finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.pate_double_score_approximation_negligible ∧
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ∧
        TendstoInDistribution
          (fun index sample =>
            scaledStatistic index sample *
              (standardError
                (estimatedScoreVariance (oracle index sample)
                  (projectionReduction index sample)
                  (targetDrift index sample)))⁻¹)
          l
          (fun limitSample =>
            limit limitSample *
              (standardError
                (estimatedScoreVariance oracleLimit projectionLimit
                  targetDriftLimit))⁻¹)
          (fun _index => sampleLaw) limitLaw ∧
          Tendsto
            (fun index =>
              eventProbabilityReal (coverage_input.sampleLawSeq index)
                (fun sample =>
                  waldCovers (coverage_input.estimator index sample)
                    (coverage_input.target index)
                    (coverage_input.criticalValue index)
                    (standardError
                      (coverage_input.varianceEstimate index sample))
                    (coverage_input.scale index)))
            l (nhds coverage_input.coverageLimit) := by
  let b :=
    pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_lt_limit
      finite_estimated_bridge scaledStatistic oracle projectionReduction
      targetDrift limit oracleLimit projectionLimit targetDriftLimit horacle
      hprojection hdrift hprojectionLimit_lt_oracle hdriftLimit_nonneg
      hinverse_meas estimated_score_to_scaled_tendsto coverage_input
  have h :=
    pate_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score
      b hdesign hbounded harray_lln hfinite henvelope hsimplex hlinear
      hmatrix hdecomp hdenominator hheterogeneity hresidual hfirst hlocal
      hgodambe
  simpa [b,
    pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_lt_limit,
    pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_lt_limit,
    estimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit]
    using h

/--
PATE absolute finite score-cell estimated-score Wald coverage directly from
weak projection slack and positive target drift.
-/
theorem
    pate_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit
    (finite_estimated_bridge :
      PATEFiniteScoreCellEstimatedScoreAsymptoticBridge Cell)
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
    (estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
    (coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (hdesign :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.aggregate_hajek_decomposition)
    (hdenominator :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.denominator_stabilization)
    (hheterogeneity :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.heterogeneity_clt)
    (hresidual :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.residual_clt)
    (hfirst :
      finite_estimated_bridge.estimated_score_bridge.first_step_asymptotic_linearization)
    (hlocal :
      finite_estimated_bridge.estimated_score_bridge.matching_functional_local_expansion)
    (hgodambe :
      finite_estimated_bridge.estimated_score_bridge.godambe_variance_identity) :
    finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.pate_double_score_approximation_negligible ∧
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ∧
        TendstoInDistribution
          (fun index sample =>
            scaledStatistic index sample *
              (standardError
                (estimatedScoreVariance (oracle index sample)
                  (projectionReduction index sample)
                  (targetDrift index sample)))⁻¹)
          l
          (fun limitSample =>
            limit limitSample *
              (standardError
                (estimatedScoreVariance oracleLimit projectionLimit
                  targetDriftLimit))⁻¹)
          (fun _index => sampleLaw) limitLaw ∧
          Tendsto
            (fun index =>
              eventProbabilityReal (coverage_input.sampleLawSeq index)
                (fun sample =>
                  waldCovers (coverage_input.estimator index sample)
                    (coverage_input.target index)
                    (coverage_input.criticalValue index)
                    (standardError
                      (coverage_input.varianceEstimate index sample))
                    (coverage_input.scale index)))
            l (nhds coverage_input.coverageLimit) := by
  let b :=
    pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_le_drift_pos_limit
      finite_estimated_bridge scaledStatistic oracle projectionReduction
      targetDrift limit oracleLimit projectionLimit targetDriftLimit horacle
      hprojection hdrift hprojectionLimit_le_oracle hdriftLimit_pos
      hinverse_meas estimated_score_to_scaled_tendsto coverage_input
  have h :=
    pate_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score
      b hdesign hbounded harray_lln hfinite henvelope hsimplex hlinear
      hmatrix hdecomp hdenominator hheterogeneity hresidual hfirst hlocal
      hgodambe
  simpa [b,
    pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_le_drift_pos_limit,
    pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_le_drift_pos_limit,
    estimatedScorePositiveVarianceStudentizationInput_of_projection_le_drift_pos_limit]
    using h

/--
PATE absolute finite score-cell estimated-score Wald coverage directly from
fixed-law strict projection slack.
-/
theorem
    pate_absolutePositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit
    (finite_estimated_bridge :
      PATEFiniteScoreCellEstimatedScoreAsymptoticBridge Cell)
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
    (estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
    (coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (hdesign :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.aggregate_hajek_decomposition)
    (hdenominator :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.denominator_stabilization)
    (hheterogeneity :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.heterogeneity_clt)
    (hresidual :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.residual_clt)
    (hfirst :
      finite_estimated_bridge.estimated_score_bridge.first_step_asymptotic_linearization)
    (hlocal :
      finite_estimated_bridge.estimated_score_bridge.matching_functional_local_expansion)
    (hgodambe :
      finite_estimated_bridge.estimated_score_bridge.godambe_variance_identity) :
    finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.pate_double_score_approximation_negligible ∧
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ∧
        TendstoInDistribution
          (fun index sample =>
            scaledStatistic index sample *
              (standardError
                (estimatedScoreVariance (oracle index sample)
                  (projectionReduction index sample) 0))⁻¹)
          l
          (fun limitSample =>
            limit limitSample *
              (standardError
                (estimatedScoreVariance oracleLimit projectionLimit 0))⁻¹)
          (fun _index => sampleLaw) limitLaw ∧
          Tendsto
            (fun index =>
              eventProbabilityReal (coverage_input.sampleLawSeq index)
                (fun sample =>
                  waldCovers (coverage_input.estimator index sample)
                    (coverage_input.target index)
                    (coverage_input.criticalValue index)
                    (standardError
                      (coverage_input.varianceEstimate index sample))
                    (coverage_input.scale index)))
            l (nhds coverage_input.coverageLimit) := by
  let b :=
    pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit
      finite_estimated_bridge scaledStatistic oracle projectionReduction limit
      oracleLimit projectionLimit horacle hprojection hprojectionLimit_lt_oracle
      hinverse_meas estimated_score_to_scaled_tendsto coverage_input
  have h :=
    pate_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score
      b hdesign hbounded harray_lln hfinite henvelope hsimplex hlinear
      hmatrix hdecomp hdenominator hheterogeneity hresidual hfirst hlocal
      hgodambe
  simpa [b,
    pateFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit,
    pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_fixedLaw_projection_lt_limit,
    fixedLawEstimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit]
    using h

/--
PATE two-sided finite score-cell estimated-score Wald coverage directly from
strict projection slack and nonnegative target drift.
-/
theorem
    pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit
    (finite_estimated_bridge :
      PATEFiniteScoreCellEstimatedScoreAsymptoticBridge Cell)
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
    (estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
    (coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (hdesign :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.aggregate_hajek_decomposition)
    (hdenominator :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.denominator_stabilization)
    (hheterogeneity :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.heterogeneity_clt)
    (hresidual :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.residual_clt)
    (hfirst :
      finite_estimated_bridge.estimated_score_bridge.first_step_asymptotic_linearization)
    (hlocal :
      finite_estimated_bridge.estimated_score_bridge.matching_functional_local_expansion)
    (hgodambe :
      finite_estimated_bridge.estimated_score_bridge.godambe_variance_identity) :
    finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.pate_double_score_approximation_negligible ∧
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ∧
        TendstoInDistribution
          (fun index sample =>
            scaledStatistic index sample *
              (standardError
                (estimatedScoreVariance (oracle index sample)
                  (projectionReduction index sample)
                  (targetDrift index sample)))⁻¹)
          l
          (fun limitSample =>
            limit limitSample *
              (standardError
                (estimatedScoreVariance oracleLimit projectionLimit
                  targetDriftLimit))⁻¹)
          (fun _index => sampleLaw) limitLaw ∧
          Tendsto
            (fun index =>
              eventProbabilityReal (coverage_input.sampleLawSeq index)
                (fun sample =>
                  waldCovers (coverage_input.estimator index sample)
                    (coverage_input.target index)
                    (coverage_input.criticalValue index)
                    (standardError
                      (coverage_input.varianceEstimate index sample))
                    (coverage_input.scale index)))
            l (nhds coverage_input.coverageLimit) := by
  let b :=
    pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_lt_limit
      finite_estimated_bridge scaledStatistic oracle projectionReduction
      targetDrift limit oracleLimit projectionLimit targetDriftLimit horacle
      hprojection hdrift hprojectionLimit_lt_oracle hdriftLimit_nonneg
      hinverse_meas estimated_score_to_scaled_tendsto coverage_input
  have h :=
    pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score
      b hdesign hbounded harray_lln hfinite henvelope hsimplex hlinear
      hmatrix hdecomp hdenominator hheterogeneity hresidual hfirst hlocal
      hgodambe
  simpa [b,
    pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_lt_limit,
    pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_lt_limit,
    estimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit]
    using h

/--
PATE two-sided finite score-cell estimated-score Wald coverage directly from
weak projection slack and positive target drift.
-/
theorem
    pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit
    (finite_estimated_bridge :
      PATEFiniteScoreCellEstimatedScoreAsymptoticBridge Cell)
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
    (estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
    (coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (hdesign :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.aggregate_hajek_decomposition)
    (hdenominator :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.denominator_stabilization)
    (hheterogeneity :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.heterogeneity_clt)
    (hresidual :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.residual_clt)
    (hfirst :
      finite_estimated_bridge.estimated_score_bridge.first_step_asymptotic_linearization)
    (hlocal :
      finite_estimated_bridge.estimated_score_bridge.matching_functional_local_expansion)
    (hgodambe :
      finite_estimated_bridge.estimated_score_bridge.godambe_variance_identity) :
    finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.pate_double_score_approximation_negligible ∧
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ∧
        TendstoInDistribution
          (fun index sample =>
            scaledStatistic index sample *
              (standardError
                (estimatedScoreVariance (oracle index sample)
                  (projectionReduction index sample)
                  (targetDrift index sample)))⁻¹)
          l
          (fun limitSample =>
            limit limitSample *
              (standardError
                (estimatedScoreVariance oracleLimit projectionLimit
                  targetDriftLimit))⁻¹)
          (fun _index => sampleLaw) limitLaw ∧
          Tendsto
            (fun index =>
              eventProbabilityReal (coverage_input.sampleLawSeq index)
                (fun sample =>
                  waldCovers (coverage_input.estimator index sample)
                    (coverage_input.target index)
                    (coverage_input.criticalValue index)
                    (standardError
                      (coverage_input.varianceEstimate index sample))
                    (coverage_input.scale index)))
            l (nhds coverage_input.coverageLimit) := by
  let b :=
    pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_le_drift_pos_limit
      finite_estimated_bridge scaledStatistic oracle projectionReduction
      targetDrift limit oracleLimit projectionLimit targetDriftLimit horacle
      hprojection hdrift hprojectionLimit_le_oracle hdriftLimit_pos
      hinverse_meas estimated_score_to_scaled_tendsto coverage_input
  have h :=
    pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score
      b hdesign hbounded harray_lln hfinite henvelope hsimplex hlinear
      hmatrix hdecomp hdenominator hheterogeneity hresidual hfirst hlocal
      hgodambe
  simpa [b,
    pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_le_drift_pos_limit,
    pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_le_drift_pos_limit,
    estimatedScorePositiveVarianceStudentizationInput_of_projection_le_drift_pos_limit]
    using h

/--
PATE two-sided finite score-cell estimated-score Wald coverage directly from
fixed-law strict projection slack.
-/
theorem
    pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit
    (finite_estimated_bridge :
      PATEFiniteScoreCellEstimatedScoreAsymptoticBridge Cell)
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
    (estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
    (coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (hdesign :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.aggregate_hajek_decomposition)
    (hdenominator :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.denominator_stabilization)
    (hheterogeneity :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.heterogeneity_clt)
    (hresidual :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.residual_clt)
    (hfirst :
      finite_estimated_bridge.estimated_score_bridge.first_step_asymptotic_linearization)
    (hlocal :
      finite_estimated_bridge.estimated_score_bridge.matching_functional_local_expansion)
    (hgodambe :
      finite_estimated_bridge.estimated_score_bridge.godambe_variance_identity) :
    finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.pate_double_score_approximation_negligible ∧
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ∧
        TendstoInDistribution
          (fun index sample =>
            scaledStatistic index sample *
              (standardError
                (estimatedScoreVariance (oracle index sample)
                  (projectionReduction index sample) 0))⁻¹)
          l
          (fun limitSample =>
            limit limitSample *
              (standardError
                (estimatedScoreVariance oracleLimit projectionLimit 0))⁻¹)
          (fun _index => sampleLaw) limitLaw ∧
          Tendsto
            (fun index =>
              eventProbabilityReal (coverage_input.sampleLawSeq index)
                (fun sample =>
                  waldCovers (coverage_input.estimator index sample)
                    (coverage_input.target index)
                    (coverage_input.criticalValue index)
                    (standardError
                      (coverage_input.varianceEstimate index sample))
                    (coverage_input.scale index)))
            l (nhds coverage_input.coverageLimit) := by
  let b :=
    pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit
      finite_estimated_bridge scaledStatistic oracle projectionReduction limit
      oracleLimit projectionLimit horacle hprojection hprojectionLimit_lt_oracle
      hinverse_meas estimated_score_to_scaled_tendsto coverage_input
  have h :=
    pate_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score
      b hdesign hbounded harray_lln hfinite henvelope hsimplex hlinear
      hmatrix hdecomp hdenominator hheterogeneity hresidual hfirst hlocal
      hgodambe
  simpa [b,
    pateFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit,
    pateFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_fixedLaw_projection_lt_limit,
    fixedLawEstimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit]
    using h

/-! ## Direct PATT coverage theorems -/

/--
PATT absolute finite score-cell estimated-score Wald coverage directly from
strict projection slack and nonnegative target drift.
-/
theorem
    patt_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit
    (finite_estimated_bridge :
      PATTFiniteScoreCellEstimatedScoreAsymptoticBridge Cell)
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
    (estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
    (coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (hdesign :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.aggregate_hajek_decomposition)
    (hdenominator :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.denominator_stabilization)
    (hheterogeneity :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.heterogeneity_clt)
    (hresidual :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.residual_clt)
    (hfirst :
      finite_estimated_bridge.estimated_score_bridge.first_step_asymptotic_linearization)
    (hlocal :
      finite_estimated_bridge.estimated_score_bridge.matching_functional_local_expansion)
    (hgodambe :
      finite_estimated_bridge.estimated_score_bridge.godambe_variance_identity) :
    finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ∧
        TendstoInDistribution
          (fun index sample =>
            scaledStatistic index sample *
              (standardError
                (estimatedScoreVariance (oracle index sample)
                  (projectionReduction index sample)
                  (targetDrift index sample)))⁻¹)
          l
          (fun limitSample =>
            limit limitSample *
              (standardError
                (estimatedScoreVariance oracleLimit projectionLimit
                  targetDriftLimit))⁻¹)
          (fun _index => sampleLaw) limitLaw ∧
          Tendsto
            (fun index =>
              eventProbabilityReal (coverage_input.sampleLawSeq index)
                (fun sample =>
                  waldCovers (coverage_input.estimator index sample)
                    (coverage_input.target index)
                    (coverage_input.criticalValue index)
                    (standardError
                      (coverage_input.varianceEstimate index sample))
                    (coverage_input.scale index)))
            l (nhds coverage_input.coverageLimit) := by
  let b :=
    pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_lt_limit
      finite_estimated_bridge scaledStatistic oracle projectionReduction
      targetDrift limit oracleLimit projectionLimit targetDriftLimit horacle
      hprojection hdrift hprojectionLimit_lt_oracle hdriftLimit_nonneg
      hinverse_meas estimated_score_to_scaled_tendsto coverage_input
  have h :=
    patt_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score
      b hdesign hbounded harray_lln hfinite henvelope hsimplex hlinear
      hmatrix hdecomp hdenominator hheterogeneity hresidual hfirst hlocal
      hgodambe
  simpa [b,
    pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_lt_limit,
    pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_lt_limit,
    estimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit]
    using h

/--
PATT absolute finite score-cell estimated-score Wald coverage directly from
weak projection slack and positive target drift.
-/
theorem
    patt_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit
    (finite_estimated_bridge :
      PATTFiniteScoreCellEstimatedScoreAsymptoticBridge Cell)
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
    (estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
    (coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (hdesign :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.aggregate_hajek_decomposition)
    (hdenominator :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.denominator_stabilization)
    (hheterogeneity :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.heterogeneity_clt)
    (hresidual :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.residual_clt)
    (hfirst :
      finite_estimated_bridge.estimated_score_bridge.first_step_asymptotic_linearization)
    (hlocal :
      finite_estimated_bridge.estimated_score_bridge.matching_functional_local_expansion)
    (hgodambe :
      finite_estimated_bridge.estimated_score_bridge.godambe_variance_identity) :
    finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ∧
        TendstoInDistribution
          (fun index sample =>
            scaledStatistic index sample *
              (standardError
                (estimatedScoreVariance (oracle index sample)
                  (projectionReduction index sample)
                  (targetDrift index sample)))⁻¹)
          l
          (fun limitSample =>
            limit limitSample *
              (standardError
                (estimatedScoreVariance oracleLimit projectionLimit
                  targetDriftLimit))⁻¹)
          (fun _index => sampleLaw) limitLaw ∧
          Tendsto
            (fun index =>
              eventProbabilityReal (coverage_input.sampleLawSeq index)
                (fun sample =>
                  waldCovers (coverage_input.estimator index sample)
                    (coverage_input.target index)
                    (coverage_input.criticalValue index)
                    (standardError
                      (coverage_input.varianceEstimate index sample))
                    (coverage_input.scale index)))
            l (nhds coverage_input.coverageLimit) := by
  let b :=
    pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_le_drift_pos_limit
      finite_estimated_bridge scaledStatistic oracle projectionReduction
      targetDrift limit oracleLimit projectionLimit targetDriftLimit horacle
      hprojection hdrift hprojectionLimit_le_oracle hdriftLimit_pos
      hinverse_meas estimated_score_to_scaled_tendsto coverage_input
  have h :=
    patt_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score
      b hdesign hbounded harray_lln hfinite henvelope hsimplex hlinear
      hmatrix hdecomp hdenominator hheterogeneity hresidual hfirst hlocal
      hgodambe
  simpa [b,
    pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_projection_le_drift_pos_limit,
    pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_le_drift_pos_limit,
    estimatedScorePositiveVarianceStudentizationInput_of_projection_le_drift_pos_limit]
    using h

/--
PATT absolute finite score-cell estimated-score Wald coverage directly from
fixed-law strict projection slack.
-/
theorem
    patt_absolutePositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit
    (finite_estimated_bridge :
      PATTFiniteScoreCellEstimatedScoreAsymptoticBridge Cell)
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
    (estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
    (coverage_input : AbsoluteWaldCoverageVarianceInput Index Sample l)
    (hdesign :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.aggregate_hajek_decomposition)
    (hdenominator :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.denominator_stabilization)
    (hheterogeneity :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.heterogeneity_clt)
    (hresidual :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.residual_clt)
    (hfirst :
      finite_estimated_bridge.estimated_score_bridge.first_step_asymptotic_linearization)
    (hlocal :
      finite_estimated_bridge.estimated_score_bridge.matching_functional_local_expansion)
    (hgodambe :
      finite_estimated_bridge.estimated_score_bridge.godambe_variance_identity) :
    finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ∧
        TendstoInDistribution
          (fun index sample =>
            scaledStatistic index sample *
              (standardError
                (estimatedScoreVariance (oracle index sample)
                  (projectionReduction index sample) 0))⁻¹)
          l
          (fun limitSample =>
            limit limitSample *
              (standardError
                (estimatedScoreVariance oracleLimit projectionLimit 0))⁻¹)
          (fun _index => sampleLaw) limitLaw ∧
          Tendsto
            (fun index =>
              eventProbabilityReal (coverage_input.sampleLawSeq index)
                (fun sample =>
                  waldCovers (coverage_input.estimator index sample)
                    (coverage_input.target index)
                    (coverage_input.criticalValue index)
                    (standardError
                      (coverage_input.varianceEstimate index sample))
                    (coverage_input.scale index)))
            l (nhds coverage_input.coverageLimit) := by
  let b :=
    pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit
      finite_estimated_bridge scaledStatistic oracle projectionReduction limit
      oracleLimit projectionLimit horacle hprojection hprojectionLimit_lt_oracle
      hinverse_meas estimated_score_to_scaled_tendsto coverage_input
  have h :=
    patt_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score
      b hdesign hbounded harray_lln hfinite henvelope hsimplex hlinear
      hmatrix hdecomp hdenominator hheterogeneity hresidual hfirst hlocal
      hgodambe
  simpa [b,
    pattFiniteScoreCellEstimatedScoreAbsolutePositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit,
    pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_fixedLaw_projection_lt_limit,
    fixedLawEstimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit]
    using h

/--
PATT two-sided finite score-cell estimated-score Wald coverage directly from
strict projection slack and nonnegative target drift.
-/
theorem
    patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit
    (finite_estimated_bridge :
      PATTFiniteScoreCellEstimatedScoreAsymptoticBridge Cell)
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
    (estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
    (coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (hdesign :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.aggregate_hajek_decomposition)
    (hdenominator :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.denominator_stabilization)
    (hheterogeneity :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.heterogeneity_clt)
    (hresidual :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.residual_clt)
    (hfirst :
      finite_estimated_bridge.estimated_score_bridge.first_step_asymptotic_linearization)
    (hlocal :
      finite_estimated_bridge.estimated_score_bridge.matching_functional_local_expansion)
    (hgodambe :
      finite_estimated_bridge.estimated_score_bridge.godambe_variance_identity) :
    finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ∧
        TendstoInDistribution
          (fun index sample =>
            scaledStatistic index sample *
              (standardError
                (estimatedScoreVariance (oracle index sample)
                  (projectionReduction index sample)
                  (targetDrift index sample)))⁻¹)
          l
          (fun limitSample =>
            limit limitSample *
              (standardError
                (estimatedScoreVariance oracleLimit projectionLimit
                  targetDriftLimit))⁻¹)
          (fun _index => sampleLaw) limitLaw ∧
          Tendsto
            (fun index =>
              eventProbabilityReal (coverage_input.sampleLawSeq index)
                (fun sample =>
                  waldCovers (coverage_input.estimator index sample)
                    (coverage_input.target index)
                    (coverage_input.criticalValue index)
                    (standardError
                      (coverage_input.varianceEstimate index sample))
                    (coverage_input.scale index)))
            l (nhds coverage_input.coverageLimit) := by
  let b :=
    pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_lt_limit
      finite_estimated_bridge scaledStatistic oracle projectionReduction
      targetDrift limit oracleLimit projectionLimit targetDriftLimit horacle
      hprojection hdrift hprojectionLimit_lt_oracle hdriftLimit_nonneg
      hinverse_meas estimated_score_to_scaled_tendsto coverage_input
  have h :=
    patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score
      b hdesign hbounded harray_lln hfinite henvelope hsimplex hlinear
      hmatrix hdecomp hdenominator hheterogeneity hresidual hfirst hlocal
      hgodambe
  simpa [b,
    pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_lt_limit,
    pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_lt_limit,
    estimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit]
    using h

/--
PATT two-sided finite score-cell estimated-score Wald coverage directly from
weak projection slack and positive target drift.
-/
theorem
    patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit
    (finite_estimated_bridge :
      PATTFiniteScoreCellEstimatedScoreAsymptoticBridge Cell)
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
    (estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
    (coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (hdesign :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.aggregate_hajek_decomposition)
    (hdenominator :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.denominator_stabilization)
    (hheterogeneity :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.heterogeneity_clt)
    (hresidual :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.residual_clt)
    (hfirst :
      finite_estimated_bridge.estimated_score_bridge.first_step_asymptotic_linearization)
    (hlocal :
      finite_estimated_bridge.estimated_score_bridge.matching_functional_local_expansion)
    (hgodambe :
      finite_estimated_bridge.estimated_score_bridge.godambe_variance_identity) :
    finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ∧
        TendstoInDistribution
          (fun index sample =>
            scaledStatistic index sample *
              (standardError
                (estimatedScoreVariance (oracle index sample)
                  (projectionReduction index sample)
                  (targetDrift index sample)))⁻¹)
          l
          (fun limitSample =>
            limit limitSample *
              (standardError
                (estimatedScoreVariance oracleLimit projectionLimit
                  targetDriftLimit))⁻¹)
          (fun _index => sampleLaw) limitLaw ∧
          Tendsto
            (fun index =>
              eventProbabilityReal (coverage_input.sampleLawSeq index)
                (fun sample =>
                  waldCovers (coverage_input.estimator index sample)
                    (coverage_input.target index)
                    (coverage_input.criticalValue index)
                    (standardError
                      (coverage_input.varianceEstimate index sample))
                    (coverage_input.scale index)))
            l (nhds coverage_input.coverageLimit) := by
  let b :=
    pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_le_drift_pos_limit
      finite_estimated_bridge scaledStatistic oracle projectionReduction
      targetDrift limit oracleLimit projectionLimit targetDriftLimit horacle
      hprojection hdrift hprojectionLimit_le_oracle hdriftLimit_pos
      hinverse_meas estimated_score_to_scaled_tendsto coverage_input
  have h :=
    patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score
      b hdesign hbounded harray_lln hfinite henvelope hsimplex hlinear
      hmatrix hdecomp hdenominator hheterogeneity hresidual hfirst hlocal
      hgodambe
  simpa [b,
    pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_projection_le_drift_pos_limit,
    pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_projection_le_drift_pos_limit,
    estimatedScorePositiveVarianceStudentizationInput_of_projection_le_drift_pos_limit]
    using h

/--
PATT two-sided finite score-cell estimated-score Wald coverage directly from
fixed-law strict projection slack.
-/
theorem
    patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit
    (finite_estimated_bridge :
      PATTFiniteScoreCellEstimatedScoreAsymptoticBridge Cell)
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
    (estimated_score_to_scaled_tendsto :
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ->
        TendstoInDistribution scaledStatistic l limit
          (fun _index => sampleLaw) limitLaw)
    (coverage_input : TwoSidedWaldCoverageVarianceInput Index Sample l)
    (hdesign :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.survey_design_regularity)
    (hbounded :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.bounded_score_cell_indicators)
    (harray_lln :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.lln_bridge.weighted_indicator_array_lln)
    (hfinite :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.eventual_finite_conditions)
    (henvelope :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.envelope_convergence)
    (hsimplex :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.simplex_reference_shares)
    (hlinear :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.all_linear_projection_clts_with_verified_variance)
    (hmatrix :
      finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.clt_bridge.vector_clt_bridge.covariance_matrix_tangent_space_verified)
    (hdecomp :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.aggregate_hajek_decomposition)
    (hdenominator :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.denominator_stabilization)
    (hheterogeneity :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.heterogeneity_clt)
    (hresidual :
      finite_estimated_bridge.known_score_finite_cell_bridge.known_score_bridge.residual_clt)
    (hfirst :
      finite_estimated_bridge.estimated_score_bridge.first_step_asymptotic_linearization)
    (hlocal :
      finite_estimated_bridge.estimated_score_bridge.matching_functional_local_expansion)
    (hgodambe :
      finite_estimated_bridge.estimated_score_bridge.godambe_variance_identity) :
    finite_estimated_bridge.known_score_finite_cell_bridge.stochastic_bridge.lln_bridge.indicator_bridge.patt_double_score_approximation_negligible ∧
      finite_estimated_bridge.estimated_score_bridge.estimated_score_asymptotic_normality ∧
        TendstoInDistribution
          (fun index sample =>
            scaledStatistic index sample *
              (standardError
                (estimatedScoreVariance (oracle index sample)
                  (projectionReduction index sample) 0))⁻¹)
          l
          (fun limitSample =>
            limit limitSample *
              (standardError
                (estimatedScoreVariance oracleLimit projectionLimit 0))⁻¹)
          (fun _index => sampleLaw) limitLaw ∧
          Tendsto
            (fun index =>
              eventProbabilityReal (coverage_input.sampleLawSeq index)
                (fun sample =>
                  waldCovers (coverage_input.estimator index sample)
                    (coverage_input.target index)
                    (coverage_input.criticalValue index)
                    (standardError
                      (coverage_input.varianceEstimate index sample))
                    (coverage_input.scale index)))
            l (nhds coverage_input.coverageLimit) := by
  let b :=
    pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit
      finite_estimated_bridge scaledStatistic oracle projectionReduction limit
      oracleLimit projectionLimit horacle hprojection hprojectionLimit_lt_oracle
      hinverse_meas estimated_score_to_scaled_tendsto coverage_input
  have h :=
    patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score
      b hdesign hbounded harray_lln hfinite henvelope hsimplex hlinear
      hmatrix hdecomp hdenominator hheterogeneity hresidual hfirst hlocal
      hgodambe
  simpa [b,
    pattFiniteScoreCellEstimatedScoreTwoSidedPositiveVarianceWaldBridge_of_fixedLaw_projection_lt_limit,
    pattFiniteScoreCellEstimatedScorePositiveVarianceStudentizedBridge_of_fixedLaw_projection_lt_limit,
    fixedLawEstimatedScorePositiveVarianceStudentizationInput_of_projection_lt_limit]
    using h

end WDSM
end Matching
end StatInference
