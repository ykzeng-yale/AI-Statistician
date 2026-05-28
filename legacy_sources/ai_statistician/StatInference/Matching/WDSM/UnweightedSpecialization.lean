import StatInference.Matching.WDSM.FiniteMatching

/-!
# Unweighted specialization of WDSM matching coefficients

When all matched-donor survey weights are one, the exact WDSM within-match
coefficient reduces to the ordinary equal matching coefficient `1 / M`, where
`M` is the matched-set cardinality.  This connects the WDSM finite algebra back
to the unweighted Abadie-Imbens/Yang-Zhang matching representation.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit : Type*}

/-- The sum of unit weights over a finite matched set is its cardinality. -/
theorem sum_const_one_eq_card (matchSet : Finset Unit) :
    (∑ _unit ∈ matchSet, (1 : Real)) = (matchSet.card : Real) := by
  simp

variable [DecidableEq Unit]

/-- Inside a match set, constant donor weights give coefficient `1 / |matchSet|`. -/
theorem withinMatchCoefficient_const_one_of_mem
    {matchSet : Finset Unit} {unit : Unit} (hmem : unit ∈ matchSet) :
    withinMatchCoefficient matchSet (fun _unit => (1 : Real)) unit =
      1 / (matchSet.card : Real) := by
  rw [withinMatchCoefficient_of_mem hmem]
  rw [sum_const_one_eq_card]

/-- Outside a match set, the unweighted coefficient is still zero. -/
theorem withinMatchCoefficient_const_one_of_not_mem
    {matchSet : Finset Unit} {unit : Unit} (hmem : unit ∉ matchSet) :
    withinMatchCoefficient matchSet (fun _unit => (1 : Real)) unit = 0 := by
  exact withinMatchCoefficient_of_not_mem hmem

/-- The unweighted coefficients sum to one when the matched-set cardinality is nonzero. -/
theorem sum_withinMatchCoefficient_const_one_matchSet
    (matchSet : Finset Unit) (hcard : (matchSet.card : Real) ≠ 0) :
    (∑ unit ∈ matchSet,
      withinMatchCoefficient matchSet (fun _unit => (1 : Real)) unit) = 1 := by
  exact sum_withinMatchCoefficient_matchSet matchSet (fun _unit => (1 : Real))
    (by simpa [sum_const_one_eq_card] using hcard)

/--
With constant donor weights, a focal unit allocates equal `focalWeight / M`
amounts to each matched donor.
-/
theorem allocatedFocalWeight_const_one_of_mem
    {matchSet : Finset Unit} {unit : Unit} (hmem : unit ∈ matchSet)
    (focalWeight : Real) :
    allocatedFocalWeight matchSet (fun _unit => (1 : Real)) focalWeight unit =
      focalWeight / (matchSet.card : Real) := by
  simp [allocatedFocalWeight, withinMatchCoefficient_const_one_of_mem hmem]
  ring

end WDSM
end Matching
end StatInference
