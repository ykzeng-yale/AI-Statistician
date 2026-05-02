import StatInference.EmpiricalProcess.Complexity

/-!
# VC-subgraph proof-obligation scaffolding

This module records the proof obligations needed before a future
VC-subgraph-to-GC theorem can be claimed.  VdV&W Chapter 2.6 separates the
route into combinatorial growth bounds, entropy translation, measurability,
envelope, and separability assumptions.  The structures below make those
obligations explicit while keeping every downstream GC conversion
proof-carrying.
-/

namespace StatInference

open Filter
open scoped Topology

/--
Proof-obligation metadata for a VC-subgraph empirical-process route.

The propositions are deliberately separate so generated theorem statements do
not collapse the full VC route into a single opaque assumption.
-/
structure VCSubgraphProofObligations {Index : Type*}
    (indexClass : Set Index) where
  vc_dimension_bound : ℕ
  measurable_subgraph_statement : Prop
  shatter_coefficient_statement : Prop
  sauer_shelah_statement : Prop
  entropy_translation_statement : Prop
  envelope_statement : Prop
  separability_statement : Prop

namespace VCSubgraphProofObligations

/-- Project VC-subgraph proof obligations into the older compact metadata API. -/
def toVCSubgraphSpec {Index : Type*} {indexClass : Set Index}
    (obligations : VCSubgraphProofObligations indexClass) :
    VCSubgraphSpec indexClass where
  vc_dimension_bound := obligations.vc_dimension_bound
  measurable_subgraph_statement := obligations.measurable_subgraph_statement
  shatter_coefficient_statement :=
    obligations.shatter_coefficient_statement ∧
      obligations.sauer_shelah_statement ∧
        obligations.entropy_translation_statement
  envelope_statement :=
    obligations.envelope_statement ∧ obligations.separability_statement

end VCSubgraphProofObligations

/--
Proof-carrying GC route from explicit VC-subgraph obligations.

The `assumptions` field is where the future Sauer/entropy/measurability proof
bundle is attached.  This structure is a scaffold, not a primitive constructor
from VC dimension alone.
-/
structure VCSubgraphGCRoute {Index : Type*}
    (indexClass : Set Index) (populationRisk : Index -> ℝ)
    (empiricalRisk : ℕ -> Index -> ℝ) where
  obligations : VCSubgraphProofObligations indexClass
  radius : ℕ -> ℝ
  assumptions : Prop
  derive_uniform_deviation :
    assumptions ->
      EmpiricalDeviationSequenceOn indexClass populationRisk empiricalRisk radius
  derive_radius_tendsto_zero :
    assumptions -> Tendsto radius atTop (𝓝 0)

namespace VCSubgraphGCRoute

/-- Convert explicit VC-subgraph route obligations into a proof-carrying certificate. -/
def toVCDeviationCertificate {Index : Type*} {indexClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (route : VCSubgraphGCRoute indexClass populationRisk empiricalRisk) :
    VCDeviationCertificate indexClass populationRisk empiricalRisk where
  vc := route.obligations.toVCSubgraphSpec
  radius := route.radius
  assumptions := route.assumptions
  derive_uniform_deviation := route.derive_uniform_deviation
  derive_radius_tendsto_zero := route.derive_radius_tendsto_zero

/-- Convert a verified VC-subgraph route into the GC-class interface. -/
def toGlivenkoCantelliClass {Index : Type*} {indexClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (route : VCSubgraphGCRoute indexClass populationRisk empiricalRisk)
    (hassumptions : route.assumptions) :
    GlivenkoCantelliClass indexClass populationRisk empiricalRisk :=
  (route.toVCDeviationCertificate).toGlivenkoCantelliClass hassumptions

end VCSubgraphGCRoute

/-- Concrete one-point VC-subgraph obligation witness for interface non-vacuity. -/
def trivialVCSubgraphProofObligations :
    VCSubgraphProofObligations (Set.univ : Set PUnit) where
  vc_dimension_bound := 0
  measurable_subgraph_statement := True
  shatter_coefficient_statement := True
  sauer_shelah_statement := True
  entropy_translation_statement := True
  envelope_statement := True
  separability_statement := True

/--
A concrete proof-carrying VC-subgraph GC route.  This witnesses that the route
API is inhabited without asserting any nontrivial VC theorem: the class has one
index and both population and empirical risks are identically zero.
-/
def trivialVCSubgraphGCRoute :
    VCSubgraphGCRoute (Set.univ : Set PUnit)
      (fun _ : PUnit => (0 : ℝ)) (fun _ (_ : PUnit) => (0 : ℝ)) where
  obligations := trivialVCSubgraphProofObligations
  radius := fun _ => 0
  assumptions := True
  derive_uniform_deviation := by
    intro _hassumptions sampleSize index hindex
    simp
  derive_radius_tendsto_zero := by
    intro _hassumptions
    simp

/-- Concrete non-vacuity witness for the VC-subgraph-to-GC handoff. -/
def trivialVCSubgraphGlivenkoCantelliClass :
    GlivenkoCantelliClass (Set.univ : Set PUnit)
      (fun _ : PUnit => (0 : ℝ)) (fun _ (_ : PUnit) => (0 : ℝ)) :=
  trivialVCSubgraphGCRoute.toGlivenkoCantelliClass True.intro

end StatInference
