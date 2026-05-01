import StatInference.EmpiricalProcess.Preservation

/-!
# Covering-number and Rademacher-compatible interfaces

This file does not assert entropy or Rademacher theorems as axioms.  Instead it
packages the statements and proof-carrying handoff points that future
probabilistic formalizations must fill before a class can be used as a
Glivenko-Cantelli class.
-/

namespace StatInference

open Filter
open scoped Topology

/-- Metadata for a covering-number route to uniform deviation. -/
structure CoveringNumberSpec {Index : Type*} (indexClass : Set Index) where
  scale : ℕ -> ℝ
  coveringNumber : ℕ -> ℕ
  finite_cover_statement : Prop
  entropy_bound_statement : Prop

/--
Proof-carrying covering-number deviation certificate.  The assumptions field is
where future entropy/discretization/probability arguments are attached.
-/
structure CoveringNumberDeviationCertificate {Index : Type*}
    (indexClass : Set Index) (populationRisk : Index -> ℝ)
    (empiricalRisk : ℕ -> Index -> ℝ) where
  covering : CoveringNumberSpec indexClass
  radius : ℕ -> ℝ
  assumptions : Prop
  derive_uniform_deviation :
    assumptions ->
      EmpiricalDeviationSequenceOn indexClass populationRisk empiricalRisk radius
  derive_radius_tendsto_zero :
    assumptions -> Tendsto radius atTop (𝓝 0)

namespace CoveringNumberDeviationCertificate

/-- Convert a verified covering-number certificate into a GC-class interface. -/
def toGlivenkoCantelliClass {Index : Type*} {indexClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (certificate :
      CoveringNumberDeviationCertificate indexClass populationRisk empiricalRisk)
    (hassumptions : certificate.assumptions) :
    GlivenkoCantelliClass indexClass populationRisk empiricalRisk where
  radius := certificate.radius
  uniform_deviation := certificate.derive_uniform_deviation hassumptions
  radius_tendsto_zero := certificate.derive_radius_tendsto_zero hassumptions

/-- Extract the uniform-deviation sequence from a covering-number certificate. -/
def uniformDeviation {Index : Type*} {indexClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (certificate :
      CoveringNumberDeviationCertificate indexClass populationRisk empiricalRisk)
    (hassumptions : certificate.assumptions) :
    EmpiricalDeviationSequenceOn indexClass populationRisk empiricalRisk
      certificate.radius :=
  certificate.derive_uniform_deviation hassumptions

end CoveringNumberDeviationCertificate

/-- Metadata for a Rademacher-complexity route to uniform deviation. -/
structure RademacherComplexitySpec (Index : Type*) where
  complexity : ℕ -> ℝ
  symmetrization_statement : Prop
  contraction_statement : Prop
  concentration_statement : Prop

/--
Proof-carrying Rademacher deviation certificate.  The radius is explicitly
tracked as `2 * complexity + slack`, the usual deterministic shape of
Rademacher-style high-probability bounds.
-/
structure RademacherDeviationCertificate {Index : Type*}
    (indexClass : Set Index) (populationRisk : Index -> ℝ)
    (empiricalRisk : ℕ -> Index -> ℝ) where
  rademacher : RademacherComplexitySpec Index
  slack : ℕ -> ℝ
  radius : ℕ -> ℝ
  radius_eq :
    ∀ sampleSize,
      radius sampleSize =
        2 * rademacher.complexity sampleSize + slack sampleSize
  uniform_deviation :
    EmpiricalDeviationSequenceOn indexClass populationRisk empiricalRisk radius

namespace RademacherDeviationCertificate

/-- If complexity and slack vanish, the induced Rademacher radius vanishes. -/
theorem radius_tendsto_zero {Index : Type*} {indexClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (certificate :
      RademacherDeviationCertificate indexClass populationRisk empiricalRisk)
    (hcomplexity : Tendsto certificate.rademacher.complexity atTop (𝓝 0))
    (hslack : Tendsto certificate.slack atTop (𝓝 0)) :
    Tendsto certificate.radius atTop (𝓝 0) := by
  have htarget :=
    oracle_bound_tendsto_zero certificate.slack
      certificate.rademacher.complexity hcomplexity hslack
  exact Tendsto.congr'
    (Eventually.of_forall (fun sampleSize =>
      (certificate.radius_eq sampleSize).symm))
    htarget

/-- Convert a verified Rademacher certificate into a GC-class interface. -/
def toGlivenkoCantelliClass {Index : Type*} {indexClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (certificate :
      RademacherDeviationCertificate indexClass populationRisk empiricalRisk)
    (hcomplexity : Tendsto certificate.rademacher.complexity atTop (𝓝 0))
    (hslack : Tendsto certificate.slack atTop (𝓝 0)) :
    GlivenkoCantelliClass indexClass populationRisk empiricalRisk where
  radius := certificate.radius
  uniform_deviation := certificate.uniform_deviation
  radius_tendsto_zero :=
    certificate.radius_tendsto_zero hcomplexity hslack

end RademacherDeviationCertificate

end StatInference
