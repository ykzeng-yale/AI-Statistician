import StatInference.Asymptotics.Basic

/-!
# Empirical process interfaces

This file keeps empirical-process results as Lean-facing interfaces.  The
definitions below expose the propositions that downstream theorem statements
need, while the theorems only project supplied evidence or apply deterministic
oracle inequalities from `StatInference.Asymptotics.Basic`.
-/

namespace StatInference

open Filter
open scoped Topology

/-- A uniform finite-sample deviation bound over an entire empirical-process index type. -/
def EmpiricalDeviationBound {Index : Type*}
    (populationRisk empiricalRisk : Index -> ℝ) (radius : ℝ) : Prop :=
  ∀ index, |empiricalRisk index - populationRisk index| ≤ radius

/-- A uniform finite-sample deviation bound restricted to an indexed class. -/
def EmpiricalDeviationBoundOn {Index : Type*} (indexClass : Set Index)
    (populationRisk empiricalRisk : Index -> ℝ) (radius : ℝ) : Prop :=
  ∀ index, index ∈ indexClass ->
    |empiricalRisk index - populationRisk index| ≤ radius

namespace EmpiricalDeviationBound

theorem apply_at {Index : Type*} {populationRisk empiricalRisk : Index -> ℝ}
    {radius : ℝ} (h : EmpiricalDeviationBound populationRisk empiricalRisk radius)
    (index : Index) :
    |empiricalRisk index - populationRisk index| ≤ radius :=
  h index

theorem toOn {Index : Type*} {populationRisk empiricalRisk : Index -> ℝ}
    {radius : ℝ}
    (h : EmpiricalDeviationBound populationRisk empiricalRisk radius)
    (indexClass : Set Index) :
    EmpiricalDeviationBoundOn indexClass populationRisk empiricalRisk radius := by
  intro index _hindex
  exact h index

end EmpiricalDeviationBound

namespace EmpiricalDeviationBoundOn

theorem apply_at {Index : Type*} {indexClass : Set Index}
    {populationRisk empiricalRisk : Index -> ℝ} {radius : ℝ}
    (h : EmpiricalDeviationBoundOn indexClass populationRisk empiricalRisk radius)
    {index : Index} (hindex : index ∈ indexClass) :
    |empiricalRisk index - populationRisk index| ≤ radius :=
  h index hindex

theorem mono {Index : Type*} {largerClass smallerClass : Set Index}
    {populationRisk empiricalRisk : Index -> ℝ} {radius : ℝ}
    (h : EmpiricalDeviationBoundOn largerClass populationRisk empiricalRisk radius)
    (hsubset : smallerClass ⊆ largerClass) :
    EmpiricalDeviationBoundOn smallerClass populationRisk empiricalRisk radius := by
  intro index hindex
  exact h index (hsubset hindex)

end EmpiricalDeviationBoundOn

/--
Restricted-class ERM oracle inequality from a uniform deviation bound on that
class. This is the deterministic core used after finite-class uniform
convergence has supplied a deviation radius.
-/
theorem oracle_ineq_of_uniform_deviation_on
    {Index : Type*} {indexClass : Set Index}
    (populationRisk empiricalRisk : Index -> ℝ) (fhat comparator : Index)
    (eps radius : ℝ)
    (hfhat : fhat ∈ indexClass)
    (hcomparator : comparator ∈ indexClass)
    (h_uniform :
      EmpiricalDeviationBoundOn indexClass populationRisk empiricalRisk radius)
    (h_erm : empiricalRisk fhat ≤ empiricalRisk comparator + eps) :
    populationRisk fhat ≤ populationRisk comparator + 2 * radius + eps := by
  have h_left := (abs_le.mp (h_uniform fhat hfhat)).1
  have h_right := (abs_le.mp (h_uniform comparator hcomparator)).2
  nlinarith

/-- Excess-risk version of `oracle_ineq_of_uniform_deviation_on`. -/
theorem excess_risk_bound_of_uniform_deviation_on
    {Index : Type*} {indexClass : Set Index}
    (populationRisk empiricalRisk : Index -> ℝ) (fhat comparator : Index)
    (eps radius : ℝ)
    (hfhat : fhat ∈ indexClass)
    (hcomparator : comparator ∈ indexClass)
    (h_uniform :
      EmpiricalDeviationBoundOn indexClass populationRisk empiricalRisk radius)
    (h_erm : empiricalRisk fhat ≤ empiricalRisk comparator + eps) :
    populationRisk fhat - populationRisk comparator ≤ 2 * radius + eps := by
  have h := oracle_ineq_of_uniform_deviation_on
    populationRisk empiricalRisk fhat comparator eps radius
    hfhat hcomparator h_uniform h_erm
  nlinarith

/-- A sequence of uniform deviation bounds over an entire index type. -/
def EmpiricalDeviationSequence {Index : Type*}
    (populationRisk : Index -> ℝ) (empiricalRisk : ℕ -> Index -> ℝ)
    (radius : ℕ -> ℝ) : Prop :=
  ∀ sampleSize,
    EmpiricalDeviationBound populationRisk (empiricalRisk sampleSize)
      (radius sampleSize)

/-- A sequence of uniform deviation bounds restricted to an indexed class. -/
def EmpiricalDeviationSequenceOn {Index : Type*} (indexClass : Set Index)
    (populationRisk : Index -> ℝ) (empiricalRisk : ℕ -> Index -> ℝ)
    (radius : ℕ -> ℝ) : Prop :=
  ∀ sampleSize,
    EmpiricalDeviationBoundOn indexClass populationRisk
      (empiricalRisk sampleSize) (radius sampleSize)

namespace EmpiricalDeviationSequence

theorem apply_at {Index : Type*} {populationRisk : Index -> ℝ}
    {empiricalRisk : ℕ -> Index -> ℝ} {radius : ℕ -> ℝ}
    (h : EmpiricalDeviationSequence populationRisk empiricalRisk radius)
    (sampleSize : ℕ) (index : Index) :
    |empiricalRisk sampleSize index - populationRisk index| ≤
      radius sampleSize :=
  h sampleSize index

theorem toOn {Index : Type*} {populationRisk : Index -> ℝ}
    {empiricalRisk : ℕ -> Index -> ℝ} {radius : ℕ -> ℝ}
    (h : EmpiricalDeviationSequence populationRisk empiricalRisk radius)
    (indexClass : Set Index) :
    EmpiricalDeviationSequenceOn indexClass populationRisk empiricalRisk radius := by
  intro sampleSize
  exact EmpiricalDeviationBound.toOn (h sampleSize) indexClass

end EmpiricalDeviationSequence

namespace EmpiricalDeviationSequenceOn

theorem apply_at {Index : Type*} {indexClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    {radius : ℕ -> ℝ}
    (h : EmpiricalDeviationSequenceOn indexClass populationRisk empiricalRisk radius)
    (sampleSize : ℕ) {index : Index} (hindex : index ∈ indexClass) :
    |empiricalRisk sampleSize index - populationRisk index| ≤
      radius sampleSize :=
  h sampleSize index hindex

theorem mono {Index : Type*} {largerClass smallerClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    {radius : ℕ -> ℝ}
    (h : EmpiricalDeviationSequenceOn largerClass populationRisk empiricalRisk radius)
    (hsubset : smallerClass ⊆ largerClass) :
    EmpiricalDeviationSequenceOn smallerClass populationRisk empiricalRisk radius := by
  intro sampleSize
  exact EmpiricalDeviationBoundOn.mono (h sampleSize) hsubset

end EmpiricalDeviationSequenceOn

/--
Sequence-level excess-risk bound for approximate ERM over a restricted class.
-/
theorem oracle_excess_sequence_bound_on
    {Index : Type*} {indexClass : Set Index}
    (populationRisk : Index -> ℝ)
    (empiricalRisk : ℕ -> Index -> ℝ)
    (fhat : ℕ -> Index) (comparator : Index)
    (eps radius : ℕ -> ℝ)
    (hfhat : ∀ sampleSize, fhat sampleSize ∈ indexClass)
    (hcomparator : comparator ∈ indexClass)
    (h_uniform :
      EmpiricalDeviationSequenceOn indexClass populationRisk empiricalRisk radius)
    (h_erm :
      ∀ sampleSize,
        empiricalRisk sampleSize (fhat sampleSize) ≤
          empiricalRisk sampleSize comparator + eps sampleSize) :
    ∀ sampleSize,
      populationRisk (fhat sampleSize) - populationRisk comparator ≤
        2 * radius sampleSize + eps sampleSize := by
  intro sampleSize
  exact excess_risk_bound_of_uniform_deviation_on
    populationRisk (empiricalRisk sampleSize) (fhat sampleSize) comparator
    (eps sampleSize) (radius sampleSize) (hfhat sampleSize) hcomparator
    (h_uniform sampleSize) (h_erm sampleSize)

structure EmpiricalProcessSpec (Index Observation Value : Type*) where
  process : Index -> Observation -> Value
  measurability_statement : Prop
  complexity_statement : Prop

structure GlivenkoCantelliSpec where
  uniform_law_statement : Prop

structure DonskerSpec where
  weak_convergence_statement : Prop

/--
Glivenko-Cantelli-style interface for an indexed class.

The record stores a concrete radius sequence and the verified facts needed to
use it.  It does not claim that a class is GC unless those fields are supplied.
-/
structure GlivenkoCantelliClass {Index : Type*} (indexClass : Set Index)
    (populationRisk : Index -> ℝ) (empiricalRisk : ℕ -> Index -> ℝ) where
  radius : ℕ -> ℝ
  uniform_deviation :
    EmpiricalDeviationSequenceOn indexClass populationRisk empiricalRisk radius
  radius_tendsto_zero : Tendsto radius atTop (𝓝 0)

namespace GlivenkoCantelliClass

theorem deviation {Index : Type*} {indexClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (gc : GlivenkoCantelliClass indexClass populationRisk empiricalRisk)
    (sampleSize : ℕ) {index : Index} (hindex : index ∈ indexClass) :
    |empiricalRisk sampleSize index - populationRisk index| ≤
      gc.radius sampleSize :=
  gc.uniform_deviation sampleSize index hindex

def project {Index : Type*} {largerClass smallerClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (gc : GlivenkoCantelliClass largerClass populationRisk empiricalRisk)
    (hsubset : smallerClass ⊆ largerClass) :
    GlivenkoCantelliClass smallerClass populationRisk empiricalRisk where
  radius := gc.radius
  uniform_deviation := EmpiricalDeviationSequenceOn.mono gc.uniform_deviation hsubset
  radius_tendsto_zero := gc.radius_tendsto_zero

theorem toEmpiricalDeviationSequence {Index : Type*}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (gc : GlivenkoCantelliClass (Set.univ : Set Index)
      populationRisk empiricalRisk) :
    EmpiricalDeviationSequence populationRisk empiricalRisk gc.radius := by
  intro sampleSize index
  exact gc.uniform_deviation sampleSize index trivial

end GlivenkoCantelliClass

/-- Marker that an indexed class is finite. -/
structure FiniteClassMarker {Index : Type*} (indexClass : Set Index) : Prop where
  finite : indexClass.Finite

namespace FiniteClassMarker

theorem finite_set {Index : Type*} {indexClass : Set Index}
    (marker : FiniteClassMarker indexClass) :
    indexClass.Finite :=
  marker.finite

end FiniteClassMarker

/--
Finite-class uniform convergence certificate.

The finiteness field records the statistical-learning-theory regime; the
uniform-deviation and vanishing-radius fields are the verified payload consumed
by downstream ERM consistency theorems.
-/
structure FiniteClassUniformConvergence {Index : Type*}
    (indexClass : Set Index) (populationRisk : Index -> ℝ)
    (empiricalRisk : ℕ -> Index -> ℝ) where
  finite_class : FiniteClassMarker indexClass
  radius : ℕ -> ℝ
  uniform_deviation :
    EmpiricalDeviationSequenceOn indexClass populationRisk empiricalRisk radius
  radius_tendsto_zero : Tendsto radius atTop (𝓝 0)

namespace FiniteClassUniformConvergence

def toGlivenkoCantelliClass {Index : Type*} {indexClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (finite_gc :
      FiniteClassUniformConvergence indexClass populationRisk empiricalRisk) :
    GlivenkoCantelliClass indexClass populationRisk empiricalRisk where
  radius := finite_gc.radius
  uniform_deviation := finite_gc.uniform_deviation
  radius_tendsto_zero := finite_gc.radius_tendsto_zero

theorem finite {Index : Type*} {indexClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (finite_gc :
      FiniteClassUniformConvergence indexClass populationRisk empiricalRisk) :
    indexClass.Finite :=
  finite_gc.finite_class.finite

theorem deviation {Index : Type*} {indexClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (finite_gc :
      FiniteClassUniformConvergence indexClass populationRisk empiricalRisk)
    (sampleSize : ℕ) {index : Index} (hindex : index ∈ indexClass) :
    |empiricalRisk sampleSize index - populationRisk index| ≤
      finite_gc.radius sampleSize :=
  finite_gc.uniform_deviation sampleSize index hindex

/--
ERM consistency corollary for a finite class: if the finite class has a
vanishing uniform-deviation radius and the approximate ERM error vanishes, then
the excess risk against any fixed in-class comparator is eventually below every
positive tolerance.
-/
theorem eventually_excessRisk_lt_of_approx_erm
    {Index : Type*} {indexClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (finite_gc :
      FiniteClassUniformConvergence indexClass populationRisk empiricalRisk)
    (fhat : ℕ -> Index) (comparator : Index) (eps : ℕ -> ℝ)
    (hfhat : ∀ sampleSize, fhat sampleSize ∈ indexClass)
    (hcomparator : comparator ∈ indexClass)
    (h_erm :
      ∀ sampleSize,
        empiricalRisk sampleSize (fhat sampleSize) ≤
          empiricalRisk sampleSize comparator + eps sampleSize)
    (h_eps : Tendsto eps atTop (𝓝 0)) :
    ∀ tolerance > 0,
      ∀ᶠ sampleSize in atTop,
        populationRisk (fhat sampleSize) - populationRisk comparator <
          tolerance := by
  intro tolerance htolerance
  have h_bound_tendsto :
      Tendsto (fun sampleSize => 2 * finite_gc.radius sampleSize + eps sampleSize)
        atTop (𝓝 0) :=
    oracle_bound_tendsto_zero eps finite_gc.radius
      finite_gc.radius_tendsto_zero h_eps
  filter_upwards [h_bound_tendsto.eventually_lt_const htolerance] with sampleSize h_bound_lt
  have h_excess_le :=
    oracle_excess_sequence_bound_on populationRisk empiricalRisk fhat comparator
      eps finite_gc.radius hfhat hcomparator finite_gc.uniform_deviation h_erm
      sampleSize
  exact lt_of_le_of_lt h_excess_le h_bound_lt

end FiniteClassUniformConvergence

/--
Marker for a finite projected class inside a larger class.

This is intentionally only a marker: it records subset and finiteness evidence,
and separate theorems explain which uniform-deviation interfaces can be
projected through it.
-/
structure FiniteClassProjection {Index : Type*}
    (largerClass projectedClass : Set Index) : Prop where
  subset : projectedClass ⊆ largerClass
  finite_projected : FiniteClassMarker projectedClass

namespace FiniteClassProjection

theorem projectedFinite {Index : Type*} {largerClass projectedClass : Set Index}
    (projection : FiniteClassProjection largerClass projectedClass) :
    projectedClass.Finite :=
  projection.finite_projected.finite

theorem uniformDeviation {Index : Type*}
    {largerClass projectedClass : Set Index}
    {populationRisk empiricalRisk : Index -> ℝ} {radius : ℝ}
    (projection : FiniteClassProjection largerClass projectedClass)
    (h :
      EmpiricalDeviationBoundOn largerClass populationRisk empiricalRisk radius) :
    EmpiricalDeviationBoundOn projectedClass populationRisk empiricalRisk radius :=
  EmpiricalDeviationBoundOn.mono h projection.subset

theorem uniformDeviationSequence {Index : Type*}
    {largerClass projectedClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    {radius : ℕ -> ℝ}
    (projection : FiniteClassProjection largerClass projectedClass)
    (h :
      EmpiricalDeviationSequenceOn largerClass populationRisk empiricalRisk radius) :
    EmpiricalDeviationSequenceOn projectedClass populationRisk empiricalRisk radius :=
  EmpiricalDeviationSequenceOn.mono h projection.subset

def glivenkoCantelli {Index : Type*}
    {largerClass projectedClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (projection : FiniteClassProjection largerClass projectedClass)
    (gc : GlivenkoCantelliClass largerClass populationRisk empiricalRisk) :
    GlivenkoCantelliClass projectedClass populationRisk empiricalRisk :=
  GlivenkoCantelliClass.project gc projection.subset

end FiniteClassProjection

/--
Benchmarkable skeleton for a future theorem that derives uniform deviation
from named assumptions.
-/
structure UniformDeviationTheoremSkeleton {Index : Type*}
    (indexClass : Set Index) (populationRisk : Index -> ℝ)
    (empiricalRisk : ℕ -> Index -> ℝ) where
  radius : ℕ -> ℝ
  assumptions : Prop
  derive_uniform_deviation :
    assumptions ->
      EmpiricalDeviationSequenceOn indexClass populationRisk empiricalRisk radius

namespace UniformDeviationTheoremSkeleton

def run {Index : Type*} {indexClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (skeleton :
      UniformDeviationTheoremSkeleton indexClass populationRisk empiricalRisk)
    (hassumptions : skeleton.assumptions) :
    EmpiricalDeviationSequenceOn indexClass populationRisk empiricalRisk
      skeleton.radius :=
  skeleton.derive_uniform_deviation hassumptions

end UniformDeviationTheoremSkeleton

/--
Benchmarkable skeleton for a theorem that derives a GC-style interface from
named assumptions.
-/
structure GlivenkoCantelliTheoremSkeleton {Index : Type*}
    (indexClass : Set Index) (populationRisk : Index -> ℝ)
    (empiricalRisk : ℕ -> Index -> ℝ) where
  radius : ℕ -> ℝ
  assumptions : Prop
  derive_uniform_deviation :
    assumptions ->
      EmpiricalDeviationSequenceOn indexClass populationRisk empiricalRisk radius
  derive_radius_tendsto_zero :
    assumptions -> Tendsto radius atTop (𝓝 0)

namespace GlivenkoCantelliTheoremSkeleton

def run {Index : Type*} {indexClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (skeleton :
      GlivenkoCantelliTheoremSkeleton indexClass populationRisk empiricalRisk)
    (hassumptions : skeleton.assumptions) :
    GlivenkoCantelliClass indexClass populationRisk empiricalRisk where
  radius := skeleton.radius
  uniform_deviation := skeleton.derive_uniform_deviation hassumptions
  radius_tendsto_zero := skeleton.derive_radius_tendsto_zero hassumptions

end GlivenkoCantelliTheoremSkeleton

/--
Benchmarkable deterministic oracle skeleton powered by a uniform-deviation
sequence.  The conclusion is an excess-risk bound, not a probabilistic claim.
-/
structure UniformDeviationOracleBenchmark (Index : Type*) where
  populationRisk : Index -> ℝ
  empiricalRisk : ℕ -> Index -> ℝ
  estimator : ℕ -> Index
  comparator : Index
  ermError : ℕ -> ℝ
  deviation : ℕ -> ℝ
  uniform_deviation :
    EmpiricalDeviationSequence populationRisk empiricalRisk deviation
  approximateERM :
    ∀ sampleSize,
      empiricalRisk sampleSize (estimator sampleSize) ≤
        empiricalRisk sampleSize comparator + ermError sampleSize

namespace UniformDeviationOracleBenchmark

theorem excessRiskBound {Index : Type*}
    (benchmark : UniformDeviationOracleBenchmark Index) :
    ∀ sampleSize,
      benchmark.populationRisk (benchmark.estimator sampleSize) -
          benchmark.populationRisk benchmark.comparator ≤
        2 * benchmark.deviation sampleSize + benchmark.ermError sampleSize :=
  oracle_excess_sequence_bound benchmark.populationRisk benchmark.empiricalRisk
    benchmark.estimator benchmark.comparator benchmark.ermError
    benchmark.deviation
    (fun sampleSize index =>
      benchmark.uniform_deviation sampleSize index)
    benchmark.approximateERM

theorem oracleBoundTendstoZero {Index : Type*}
    (benchmark : UniformDeviationOracleBenchmark Index)
    (hdeviation : Tendsto benchmark.deviation atTop (𝓝 0))
    (herm : Tendsto benchmark.ermError atTop (𝓝 0)) :
    Tendsto
      (fun sampleSize =>
        2 * benchmark.deviation sampleSize + benchmark.ermError sampleSize)
      atTop (𝓝 0) :=
  oracle_bound_tendsto_zero benchmark.ermError benchmark.deviation
    hdeviation herm

end UniformDeviationOracleBenchmark

/--
Oracle benchmark specialized to a GC interface on the full index type.
It reuses the GC radius as the uniform-deviation radius.
-/
structure GlivenkoCantelliOracleBenchmark (Index : Type*) where
  populationRisk : Index -> ℝ
  empiricalRisk : ℕ -> Index -> ℝ
  estimator : ℕ -> Index
  comparator : Index
  ermError : ℕ -> ℝ
  gc :
    GlivenkoCantelliClass (Set.univ : Set Index) populationRisk empiricalRisk
  approximateERM :
    ∀ sampleSize,
      empiricalRisk sampleSize (estimator sampleSize) ≤
        empiricalRisk sampleSize comparator + ermError sampleSize

namespace GlivenkoCantelliOracleBenchmark

theorem excessRiskBound {Index : Type*}
    (benchmark : GlivenkoCantelliOracleBenchmark Index) :
    ∀ sampleSize,
      benchmark.populationRisk (benchmark.estimator sampleSize) -
          benchmark.populationRisk benchmark.comparator ≤
        2 * benchmark.gc.radius sampleSize + benchmark.ermError sampleSize :=
  oracle_excess_sequence_bound benchmark.populationRisk benchmark.empiricalRisk
    benchmark.estimator benchmark.comparator benchmark.ermError
    benchmark.gc.radius
    (fun sampleSize index =>
      benchmark.gc.uniform_deviation sampleSize index trivial)
    benchmark.approximateERM

theorem oracleBoundTendstoZero {Index : Type*}
    (benchmark : GlivenkoCantelliOracleBenchmark Index)
    (herm : Tendsto benchmark.ermError atTop (𝓝 0)) :
    Tendsto
      (fun sampleSize =>
        2 * benchmark.gc.radius sampleSize + benchmark.ermError sampleSize)
      atTop (𝓝 0) :=
  oracle_bound_tendsto_zero benchmark.ermError benchmark.gc.radius
    benchmark.gc.radius_tendsto_zero herm

end GlivenkoCantelliOracleBenchmark

end StatInference
