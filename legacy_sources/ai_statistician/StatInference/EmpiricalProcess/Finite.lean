import StatInference.EmpiricalProcess.Average

/-!
# Finite-class deviation and finite-union interfaces

Finite-class empirical-process proofs often proceed by controlling every
single-index deviation and then taking a finite union over failure events.
This file isolates that handoff: later probabilistic bounds can prove that the
finite-union failure event does not occur, while downstream ERM/GC theorems
consume the resulting uniform-deviation interface.
-/

namespace StatInference

open Filter
open scoped Topology

/--
The finite-union failure event for a restricted class: at least one in-class
index has deviation strictly larger than the radius.
-/
def DeviationFailureEventOn {Index : Type*} (indexClass : Set Index)
    (populationRisk empiricalRisk : Index -> ℝ) (radius : ℝ) : Prop :=
  ∃ index, index ∈ indexClass ∧ radius < |empiricalRisk index - populationRisk index|

/--
If the finite-union failure event does not occur, all in-class deviations are
bounded by the radius.
-/
theorem empiricalDeviationBoundOn_of_not_deviationFailureEventOn
    {Index : Type*} {indexClass : Set Index}
    {populationRisk empiricalRisk : Index -> ℝ} {radius : ℝ}
    (hno_failure :
      ¬ DeviationFailureEventOn indexClass populationRisk empiricalRisk radius) :
    EmpiricalDeviationBoundOn indexClass populationRisk empiricalRisk radius := by
  intro index hindex
  exact not_lt.mp (fun hlt => hno_failure ⟨index, hindex, hlt⟩)

/--
A uniform deviation bound rules out the corresponding finite-union failure
event.
-/
theorem not_deviationFailureEventOn_of_empiricalDeviationBoundOn
    {Index : Type*} {indexClass : Set Index}
    {populationRisk empiricalRisk : Index -> ℝ} {radius : ℝ}
    (hbound : EmpiricalDeviationBoundOn indexClass populationRisk empiricalRisk radius) :
    ¬ DeviationFailureEventOn indexClass populationRisk empiricalRisk radius := by
  rintro ⟨index, hindex, hlt⟩
  exact not_lt_of_ge (hbound index hindex) hlt

/--
Proof-carrying finite-union certificate for a single finite-sample deviation
bound.  The `finite_class` field records the finite union regime; the
`no_deviation_failure` field is the deterministic payload.
-/
structure FiniteUnionDeviationCertificate {Index : Type*}
    (indexClass : Set Index) (populationRisk empiricalRisk : Index -> ℝ)
    (radius : ℝ) where
  finite_class : FiniteClassMarker indexClass
  no_deviation_failure :
    ¬ DeviationFailureEventOn indexClass populationRisk empiricalRisk radius

namespace FiniteUnionDeviationCertificate

theorem finite {Index : Type*} {indexClass : Set Index}
    {populationRisk empiricalRisk : Index -> ℝ} {radius : ℝ}
    (certificate :
      FiniteUnionDeviationCertificate indexClass populationRisk empiricalRisk radius) :
    indexClass.Finite :=
  certificate.finite_class.finite

theorem toEmpiricalDeviationBoundOn {Index : Type*} {indexClass : Set Index}
    {populationRisk empiricalRisk : Index -> ℝ} {radius : ℝ}
    (certificate :
      FiniteUnionDeviationCertificate indexClass populationRisk empiricalRisk radius) :
    EmpiricalDeviationBoundOn indexClass populationRisk empiricalRisk radius :=
  empiricalDeviationBoundOn_of_not_deviationFailureEventOn
    certificate.no_deviation_failure

end FiniteUnionDeviationCertificate

/--
Sequence-level finite-union certificate.  Each sample size supplies a
no-failure proof, producing a uniform-deviation sequence over the finite class.
-/
structure FiniteUnionDeviationSequence {Index : Type*}
    (indexClass : Set Index) (populationRisk : Index -> ℝ)
    (empiricalRisk : ℕ -> Index -> ℝ) where
  finite_class : FiniteClassMarker indexClass
  radius : ℕ -> ℝ
  no_deviation_failure :
    ∀ sampleSize,
      ¬ DeviationFailureEventOn indexClass populationRisk
        (empiricalRisk sampleSize) (radius sampleSize)

namespace FiniteUnionDeviationSequence

theorem finite {Index : Type*} {indexClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (certificate :
      FiniteUnionDeviationSequence indexClass populationRisk empiricalRisk) :
    indexClass.Finite :=
  certificate.finite_class.finite

def toEmpiricalDeviationSequenceOn {Index : Type*} {indexClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (certificate :
      FiniteUnionDeviationSequence indexClass populationRisk empiricalRisk) :
    EmpiricalDeviationSequenceOn indexClass populationRisk empiricalRisk
      certificate.radius := by
  intro sampleSize
  exact empiricalDeviationBoundOn_of_not_deviationFailureEventOn
    (certificate.no_deviation_failure sampleSize)

def toFiniteClassUniformConvergence {Index : Type*} {indexClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (certificate :
      FiniteUnionDeviationSequence indexClass populationRisk empiricalRisk)
    (hradius : Tendsto certificate.radius atTop (𝓝 0)) :
    FiniteClassUniformConvergence indexClass populationRisk empiricalRisk where
  finite_class := certificate.finite_class
  radius := certificate.radius
  uniform_deviation := certificate.toEmpiricalDeviationSequenceOn
  radius_tendsto_zero := hradius

/--
Use a sequence of finite-union no-failure certificates as the uniform-deviation
input to the approximate-ERM excess-risk theorem.
-/
theorem excessRiskBound {Index : Type*} {indexClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (certificate :
      FiniteUnionDeviationSequence indexClass populationRisk empiricalRisk)
    (fhat : ℕ -> Index) (comparator : Index) (eps : ℕ -> ℝ)
    (hfhat : ∀ sampleSize, fhat sampleSize ∈ indexClass)
    (hcomparator : comparator ∈ indexClass)
    (h_erm :
      ∀ sampleSize,
        empiricalRisk sampleSize (fhat sampleSize) ≤
          empiricalRisk sampleSize comparator + eps sampleSize) :
    ∀ sampleSize,
      populationRisk (fhat sampleSize) - populationRisk comparator ≤
        2 * certificate.radius sampleSize + eps sampleSize :=
  oracle_excess_sequence_bound_on populationRisk empiricalRisk fhat comparator
    eps certificate.radius hfhat hcomparator
    certificate.toEmpiricalDeviationSequenceOn h_erm

end FiniteUnionDeviationSequence

end StatInference
