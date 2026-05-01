import StatInference.EmpiricalProcess.Finite

/-!
# GC and finite-deviation preservation

This module collects subclass/projection rules for empirical-process
interfaces.  These rules are the deterministic glue needed to reuse a GC or
finite-union certificate on a smaller hypothesis class.
-/

namespace StatInference

open Filter
open scoped Topology

namespace FiniteClassMarker

/-- A subclass of a finite class is finite. -/
def project {Index : Type*} {largerClass smallerClass : Set Index}
    (marker : FiniteClassMarker largerClass)
    (hsubset : smallerClass ⊆ largerClass) :
    FiniteClassMarker smallerClass where
  finite := marker.finite.subset hsubset

end FiniteClassMarker

namespace DeviationFailureEventOn

/-- A deviation failure on a subclass is also a deviation failure on the larger class. -/
theorem mono {Index : Type*} {largerClass smallerClass : Set Index}
    {populationRisk empiricalRisk : Index -> ℝ} {radius : ℝ}
    (hsubset : smallerClass ⊆ largerClass) :
    DeviationFailureEventOn smallerClass populationRisk empiricalRisk radius ->
      DeviationFailureEventOn largerClass populationRisk empiricalRisk radius := by
  rintro ⟨index, hindex, hfailure⟩
  exact ⟨index, hsubset hindex, hfailure⟩

/-- No deviation failure on a larger class implies no deviation failure on a subclass. -/
theorem not_of_not_larger {Index : Type*} {largerClass smallerClass : Set Index}
    {populationRisk empiricalRisk : Index -> ℝ} {radius : ℝ}
    (hsubset : smallerClass ⊆ largerClass)
    (hno_failure :
      ¬ DeviationFailureEventOn largerClass populationRisk empiricalRisk radius) :
    ¬ DeviationFailureEventOn smallerClass populationRisk empiricalRisk radius := by
  intro hfailure
  exact hno_failure (mono hsubset hfailure)

end DeviationFailureEventOn

namespace FiniteUnionDeviationCertificate

/-- Project a single finite-union deviation certificate to a subclass. -/
def project {Index : Type*} {largerClass smallerClass : Set Index}
    {populationRisk empiricalRisk : Index -> ℝ} {radius : ℝ}
    (certificate :
      FiniteUnionDeviationCertificate largerClass populationRisk empiricalRisk radius)
    (hsubset : smallerClass ⊆ largerClass) :
    FiniteUnionDeviationCertificate smallerClass populationRisk empiricalRisk radius where
  finite_class := certificate.finite_class.project hsubset
  no_deviation_failure :=
    DeviationFailureEventOn.not_of_not_larger hsubset
      certificate.no_deviation_failure

end FiniteUnionDeviationCertificate

namespace FiniteUnionDeviationSequence

/-- Project a sequence of finite-union deviation certificates to a subclass. -/
def project {Index : Type*} {largerClass smallerClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (certificate :
      FiniteUnionDeviationSequence largerClass populationRisk empiricalRisk)
    (hsubset : smallerClass ⊆ largerClass) :
    FiniteUnionDeviationSequence smallerClass populationRisk empiricalRisk where
  finite_class := certificate.finite_class.project hsubset
  radius := certificate.radius
  no_deviation_failure := by
    intro sampleSize
    exact DeviationFailureEventOn.not_of_not_larger hsubset
      (certificate.no_deviation_failure sampleSize)

/--
Projection preserves the induced finite-class uniform-convergence certificate
when the same radius tends to zero.
-/
def projectToFiniteClassUniformConvergence
    {Index : Type*} {largerClass smallerClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (certificate :
      FiniteUnionDeviationSequence largerClass populationRisk empiricalRisk)
    (hsubset : smallerClass ⊆ largerClass)
    (hradius : Tendsto certificate.radius atTop (𝓝 0)) :
    FiniteClassUniformConvergence smallerClass populationRisk empiricalRisk :=
  (certificate.project hsubset).toFiniteClassUniformConvergence hradius

end FiniteUnionDeviationSequence

namespace FiniteClassUniformConvergence

/-- Project finite-class uniform convergence to a subclass. -/
def project {Index : Type*} {largerClass smallerClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (finite_gc :
      FiniteClassUniformConvergence largerClass populationRisk empiricalRisk)
    (hsubset : smallerClass ⊆ largerClass) :
    FiniteClassUniformConvergence smallerClass populationRisk empiricalRisk where
  finite_class := finite_gc.finite_class.project hsubset
  radius := finite_gc.radius
  uniform_deviation :=
    EmpiricalDeviationSequenceOn.mono finite_gc.uniform_deviation hsubset
  radius_tendsto_zero := finite_gc.radius_tendsto_zero

/-- Project finite-class uniform convergence and expose it as a GC class. -/
def projectToGlivenkoCantelliClass
    {Index : Type*} {largerClass smallerClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (finite_gc :
      FiniteClassUniformConvergence largerClass populationRisk empiricalRisk)
    (hsubset : smallerClass ⊆ largerClass) :
    GlivenkoCantelliClass smallerClass populationRisk empiricalRisk :=
  (finite_gc.project hsubset).toGlivenkoCantelliClass

end FiniteClassUniformConvergence

namespace FiniteClassProjection

/-- Build a finite-class projection from a finite larger class and a subset relation. -/
def ofSubsetFinite {Index : Type*} {largerClass projectedClass : Set Index}
    (largerFinite : FiniteClassMarker largerClass)
    (hsubset : projectedClass ⊆ largerClass) :
    FiniteClassProjection largerClass projectedClass where
  subset := hsubset
  finite_projected := largerFinite.project hsubset

/-- Project a finite-class uniform-convergence certificate through a projection marker. -/
def finiteClassUniformConvergence {Index : Type*}
    {largerClass projectedClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (projection : FiniteClassProjection largerClass projectedClass)
    (finite_gc :
      FiniteClassUniformConvergence largerClass populationRisk empiricalRisk) :
    FiniteClassUniformConvergence projectedClass populationRisk empiricalRisk :=
  finite_gc.project projection.subset

end FiniteClassProjection

end StatInference
