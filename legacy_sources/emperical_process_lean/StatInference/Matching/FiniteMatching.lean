import Mathlib

/-!
# Finite survey-weighted matching algebra

This module formalizes the first deterministic algebraic layer used in the
WDSM paper appendix: within a matched set, donor survey weights are normalized
to coefficients that sum to one.  The same coefficient system is the local
building block for survey-weighted reuse frequencies and matching-weight
representations.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit : Type*} [DecidableEq Unit]

/--
Exact within-match survey-weight-normalized coefficient.

For a finite matched donor set `matchSet`, donor `unit` receives its survey
weight divided by the total donor survey weight when it belongs to the set,
and receives coefficient zero otherwise.
-/
noncomputable def withinMatchCoefficient (matchSet : Finset Unit)
    (surveyWeight : Unit -> Real) (unit : Unit) : Real :=
  if unit ∈ matchSet then
    surveyWeight unit / (∑ matchedUnit ∈ matchSet, surveyWeight matchedUnit)
  else
    0

theorem withinMatchCoefficient_of_mem {matchSet : Finset Unit}
    {surveyWeight : Unit -> Real} {unit : Unit} (hmem : unit ∈ matchSet) :
    withinMatchCoefficient matchSet surveyWeight unit =
      surveyWeight unit /
        (∑ matchedUnit ∈ matchSet, surveyWeight matchedUnit) := by
  simp [withinMatchCoefficient, hmem]

theorem withinMatchCoefficient_of_not_mem {matchSet : Finset Unit}
    {surveyWeight : Unit -> Real} {unit : Unit} (hmem : unit ∉ matchSet) :
    withinMatchCoefficient matchSet surveyWeight unit = 0 := by
  simp [withinMatchCoefficient, hmem]

/--
The exact within-match coefficients sum to one over the matched set whenever
the total matched-donor survey weight is nonzero.
-/
theorem sum_withinMatchCoefficient_matchSet (matchSet : Finset Unit)
    (surveyWeight : Unit -> Real)
    (hden :
      (∑ matchedUnit ∈ matchSet, surveyWeight matchedUnit) ≠ 0) :
    (∑ unit ∈ matchSet, withinMatchCoefficient matchSet surveyWeight unit) = 1 := by
  calc
    (∑ unit ∈ matchSet, withinMatchCoefficient matchSet surveyWeight unit)
        = ∑ unit ∈ matchSet,
            surveyWeight unit /
              (∑ matchedUnit ∈ matchSet, surveyWeight matchedUnit) := by
          exact Finset.sum_congr rfl
            (fun unit hunit => by
              simp [withinMatchCoefficient, hunit])
    _ = (∑ unit ∈ matchSet, surveyWeight unit) /
          (∑ matchedUnit ∈ matchSet, surveyWeight matchedUnit) := by
          rw [Finset.sum_div]
    _ = 1 := by
          exact div_self hden

/--
The exact within-match coefficients also sum to one over the full finite unit
universe, because units outside the matched set have coefficient zero.
-/
theorem sum_withinMatchCoefficient_univ [Fintype Unit]
    (matchSet : Finset Unit) (surveyWeight : Unit -> Real)
    (hden :
      (∑ matchedUnit ∈ matchSet, surveyWeight matchedUnit) ≠ 0) :
    (∑ unit, withinMatchCoefficient matchSet surveyWeight unit) = 1 := by
  classical
  have hsubset : matchSet ⊆ Finset.univ := by
    intro unit _hunit
    simp
  have hsum_subset :
      (∑ unit ∈ matchSet, withinMatchCoefficient matchSet surveyWeight unit) =
        ∑ unit, withinMatchCoefficient matchSet surveyWeight unit :=
    Finset.sum_subset hsubset
      (fun unit _huniv hnot_mem => by
        simp [withinMatchCoefficient, hnot_mem])
  rw [← hsum_subset]
  exact sum_withinMatchCoefficient_matchSet matchSet surveyWeight hden

/-- Coefficients are nonnegative under nonnegative donor weights and positive total weight. -/
theorem withinMatchCoefficient_nonneg {matchSet : Finset Unit}
    {surveyWeight : Unit -> Real}
    (hweight_nonneg : ∀ unit, unit ∈ matchSet -> 0 ≤ surveyWeight unit)
    (hden_pos : 0 < ∑ matchedUnit ∈ matchSet, surveyWeight matchedUnit)
    (unit : Unit) :
    0 ≤ withinMatchCoefficient matchSet surveyWeight unit := by
  by_cases hmem : unit ∈ matchSet
  · simp [withinMatchCoefficient, hmem]
    exact div_nonneg (hweight_nonneg unit hmem) hden_pos.le
  · simp [withinMatchCoefficient, hmem]

/--
Amount of a focal unit's survey weight allocated to a donor through one matched
set.  This is the finite algebraic contribution used by the survey-weighted
reuse frequency.
-/
noncomputable def allocatedFocalWeight (matchSet : Finset Unit)
    (surveyWeight : Unit -> Real) (focalWeight : Real) (unit : Unit) : Real :=
  focalWeight * withinMatchCoefficient matchSet surveyWeight unit

/--
The allocated donor contributions over a matched set recover exactly the focal
unit's survey weight.
-/
theorem sum_allocatedFocalWeight_matchSet (matchSet : Finset Unit)
    (surveyWeight : Unit -> Real) (focalWeight : Real)
    (hden :
      (∑ matchedUnit ∈ matchSet, surveyWeight matchedUnit) ≠ 0) :
    (∑ unit ∈ matchSet,
      allocatedFocalWeight matchSet surveyWeight focalWeight unit) =
        focalWeight := by
  simp only [allocatedFocalWeight]
  rw [← Finset.mul_sum,
    sum_withinMatchCoefficient_matchSet matchSet surveyWeight hden]
  ring

/--
The allocated donor contributions over the whole finite unit universe recover
the focal unit's survey weight.
-/
theorem sum_allocatedFocalWeight_univ [Fintype Unit]
    (matchSet : Finset Unit) (surveyWeight : Unit -> Real) (focalWeight : Real)
    (hden :
      (∑ matchedUnit ∈ matchSet, surveyWeight matchedUnit) ≠ 0) :
    (∑ unit, allocatedFocalWeight matchSet surveyWeight focalWeight unit) =
      focalWeight := by
  simp only [allocatedFocalWeight]
  rw [← Finset.mul_sum,
    sum_withinMatchCoefficient_univ matchSet surveyWeight hden]
  ring

end WDSM
end Matching
end StatInference
