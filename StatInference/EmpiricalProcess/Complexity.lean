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

/-- Metadata for a bracketing-number route to uniform deviation. -/
structure BracketingNumberSpec {Index : Type*} (indexClass : Set Index) where
  scale : ℕ -> ℝ
  bracketingNumber : ℕ -> ℕ
  finite_bracketing_statement : Prop
  bracket_envelope_statement : Prop
  bracketing_entropy_statement : Prop

/--
Proof-carrying bracketing deviation certificate.  This interface scopes the
future empirical-process theorem without asserting any entropy result as an
unreviewed primitive assumption.
-/
structure BracketingDeviationCertificate {Index : Type*}
    (indexClass : Set Index) (populationRisk : Index -> ℝ)
    (empiricalRisk : ℕ -> Index -> ℝ) where
  bracketing : BracketingNumberSpec indexClass
  radius : ℕ -> ℝ
  assumptions : Prop
  derive_uniform_deviation :
    assumptions ->
      EmpiricalDeviationSequenceOn indexClass populationRisk empiricalRisk radius
  derive_radius_tendsto_zero :
    assumptions -> Tendsto radius atTop (𝓝 0)

namespace BracketingDeviationCertificate

/-- Convert a verified bracketing certificate into a GC-class interface. -/
def toGlivenkoCantelliClass {Index : Type*} {indexClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (certificate :
      BracketingDeviationCertificate indexClass populationRisk empiricalRisk)
    (hassumptions : certificate.assumptions) :
    GlivenkoCantelliClass indexClass populationRisk empiricalRisk where
  radius := certificate.radius
  uniform_deviation := certificate.derive_uniform_deviation hassumptions
  radius_tendsto_zero := certificate.derive_radius_tendsto_zero hassumptions

/-- Extract the uniform-deviation sequence from a bracketing certificate. -/
def uniformDeviation {Index : Type*} {indexClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (certificate :
      BracketingDeviationCertificate indexClass populationRisk empiricalRisk)
    (hassumptions : certificate.assumptions) :
    EmpiricalDeviationSequenceOn indexClass populationRisk empiricalRisk
      certificate.radius :=
  certificate.derive_uniform_deviation hassumptions

end BracketingDeviationCertificate

/--
Metadata for a VC-subgraph route to uniform deviation.  The fields are
proof-carrying placeholders for the combinatorial and measurability facts that
future VC formalizations must provide.
-/
structure VCSubgraphSpec {Index : Type*} (indexClass : Set Index) where
  vc_dimension_bound : ℕ
  measurable_subgraph_statement : Prop
  shatter_coefficient_statement : Prop
  envelope_statement : Prop

/-- Proof-carrying VC-subgraph deviation certificate. -/
structure VCDeviationCertificate {Index : Type*}
    (indexClass : Set Index) (populationRisk : Index -> ℝ)
    (empiricalRisk : ℕ -> Index -> ℝ) where
  vc : VCSubgraphSpec indexClass
  radius : ℕ -> ℝ
  assumptions : Prop
  derive_uniform_deviation :
    assumptions ->
      EmpiricalDeviationSequenceOn indexClass populationRisk empiricalRisk radius
  derive_radius_tendsto_zero :
    assumptions -> Tendsto radius atTop (𝓝 0)

namespace VCDeviationCertificate

/-- Convert a verified VC-subgraph certificate into a GC-class interface. -/
def toGlivenkoCantelliClass {Index : Type*} {indexClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (certificate :
      VCDeviationCertificate indexClass populationRisk empiricalRisk)
    (hassumptions : certificate.assumptions) :
    GlivenkoCantelliClass indexClass populationRisk empiricalRisk where
  radius := certificate.radius
  uniform_deviation := certificate.derive_uniform_deviation hassumptions
  radius_tendsto_zero := certificate.derive_radius_tendsto_zero hassumptions

/-- Extract the uniform-deviation sequence from a VC-subgraph certificate. -/
def uniformDeviation {Index : Type*} {indexClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (certificate :
      VCDeviationCertificate indexClass populationRisk empiricalRisk)
    (hassumptions : certificate.assumptions) :
    EmpiricalDeviationSequenceOn indexClass populationRisk empiricalRisk
      certificate.radius :=
  certificate.derive_uniform_deviation hassumptions

end VCDeviationCertificate

/--
Bridge from a verified GC class to a Donsker specification.  The GC component is
explicit because most statistical inference routes use Donsker assumptions only
after a uniform-law-of-large-numbers handoff has already been established.
-/
structure DonskerBridgeCertificate {Index : Type*}
    (indexClass : Set Index) (populationRisk : Index -> ℝ)
    (empiricalRisk : ℕ -> Index -> ℝ) where
  gc : GlivenkoCantelliClass indexClass populationRisk empiricalRisk
  donsker : DonskerSpec
  asymptotic_equipartition_statement : Prop
  weak_limit_identification_statement : Prop
  weak_convergence_proof : donsker.weak_convergence_statement

namespace DonskerBridgeCertificate

/-- Extract the GC component from a Donsker bridge. -/
def toGlivenkoCantelliClass {Index : Type*} {indexClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (certificate :
      DonskerBridgeCertificate indexClass populationRisk empiricalRisk) :
    GlivenkoCantelliClass indexClass populationRisk empiricalRisk :=
  certificate.gc

/-- Extract the weak-convergence statement carried by a Donsker bridge. -/
theorem weakConvergence {Index : Type*} {indexClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (certificate :
      DonskerBridgeCertificate indexClass populationRisk empiricalRisk) :
    certificate.donsker.weak_convergence_statement :=
  certificate.weak_convergence_proof

end DonskerBridgeCertificate

end StatInference
