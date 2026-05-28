import StatInference.Matching.WDSM.FiniteCellIndicatorGCComponentPositiveVarianceWaldAdapter

/-!
# Paired GC component-positive Wald coverage aliases

This module gives the paired PATE/PATT component-positive GC coverage routes
the same concise public naming surface as the single-arm coverage wrappers.
The proofs are aliases of the already-verified paired GC adapter theorems.
-/

namespace StatInference
namespace Matching
namespace WDSM

open Filter MeasureTheory
open scoped Topology

variable {Unit PATECell PATTCell Index Sample LimitSample : Type*}
variable [DecidableEq PATECell] [DecidableEq PATTCell]
variable [MeasurableSpace Sample] [MeasurableSpace LimitSample]
variable {sampleLaw : MeasureTheory.Measure Sample}
variable {limitLaw : MeasureTheory.Measure LimitSample}
variable [MeasureTheory.IsProbabilityMeasure sampleLaw]
variable [MeasureTheory.IsProbabilityMeasure limitLaw]
variable {l : Filter Index}
variable [l.IsCountablyGenerated]

def
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit_glivenkoCantelli :=
  pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_projection_lt_limit_glivenkoCantelli
    (Unit := Unit) (PATECell := PATECell) (PATTCell := PATTCell)
    (Index := Index) (Sample := Sample) (LimitSample := LimitSample)
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)

def
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_lt_limit_glivenkoCantelli :=
  pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_projection_lt_limit_glivenkoCantelli
    (Unit := Unit) (PATECell := PATECell) (PATTCell := PATTCell)
    (Index := Index) (Sample := Sample) (LimitSample := LimitSample)
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)

def
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_lt_limit_glivenkoCantelli :=
  pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_absolute_projection_lt_limit_glivenkoCantelli
    (Unit := Unit) (PATECell := PATECell) (PATTCell := PATTCell)
    (Index := Index) (Sample := Sample) (LimitSample := LimitSample)
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)

def
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_lt_limit_glivenkoCantelli :=
  pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_twoSided_projection_lt_limit_glivenkoCantelli
    (Unit := Unit) (PATECell := PATECell) (PATTCell := PATTCell)
    (Index := Index) (Sample := Sample) (LimitSample := LimitSample)
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)

def
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit_glivenkoCantelli :=
  pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_projection_le_drift_pos_limit_glivenkoCantelli
    (Unit := Unit) (PATECell := PATECell) (PATTCell := PATTCell)
    (Index := Index) (Sample := Sample) (LimitSample := LimitSample)
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)

def
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_projection_le_drift_pos_limit_glivenkoCantelli :=
  pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_projection_le_drift_pos_limit_glivenkoCantelli
    (Unit := Unit) (PATECell := PATECell) (PATTCell := PATTCell)
    (Index := Index) (Sample := Sample) (LimitSample := LimitSample)
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)

def
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_projection_le_drift_pos_limit_glivenkoCantelli :=
  pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_absolute_projection_le_drift_pos_limit_glivenkoCantelli
    (Unit := Unit) (PATECell := PATECell) (PATTCell := PATTCell)
    (Index := Index) (Sample := Sample) (LimitSample := LimitSample)
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)

def
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_projection_le_drift_pos_limit_glivenkoCantelli :=
  pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_twoSided_projection_le_drift_pos_limit_glivenkoCantelli
    (Unit := Unit) (PATECell := PATECell) (PATTCell := PATTCell)
    (Index := Index) (Sample := Sample) (LimitSample := LimitSample)
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)

def
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit_glivenkoCantelli :=
  pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_fixedLaw_projection_lt_limit_glivenkoCantelli
    (Unit := Unit) (PATECell := PATECell) (PATTCell := PATTCell)
    (Index := Index) (Sample := Sample) (LimitSample := LimitSample)
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)

def
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_fixedLaw_projection_lt_limit_glivenkoCantelli :=
  pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_fixedLaw_projection_lt_limit_glivenkoCantelli
    (Unit := Unit) (PATECell := PATECell) (PATTCell := PATTCell)
    (Index := Index) (Sample := Sample) (LimitSample := LimitSample)
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)

def
    pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_absolute_fixedLaw_projection_lt_limit_glivenkoCantelli :=
  pate_patt_twoSidedPositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_absolute_fixedLaw_projection_lt_limit_glivenkoCantelli
    (Unit := Unit) (PATECell := PATECell) (PATTCell := PATTCell)
    (Index := Index) (Sample := Sample) (LimitSample := LimitSample)
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)

def
    pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_twoSided_fixedLaw_projection_lt_limit_glivenkoCantelli :=
  pate_patt_absolutePositiveVarianceWaldCoverage_tendsto_of_finite_score_cell_estimated_score_twoSided_fixedLaw_projection_lt_limit_glivenkoCantelli
    (Unit := Unit) (PATECell := PATECell) (PATTCell := PATTCell)
    (Index := Index) (Sample := Sample) (LimitSample := LimitSample)
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)

end WDSM
end Matching
end StatInference
