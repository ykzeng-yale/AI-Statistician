import StatInference.EmpiricalProcess.EndpointStrongLaw
import StatInference.EmpiricalProcess.L1BracketingNumber

/-!
# VdV&W 2.4.1 current-GC assembly layer

This module adds the endpoint-control assembly layer for the dependency-minimal
route toward van der Vaart and Wellner Theorem 2.4.1.

The declarations here still target the repository's current
`GlivenkoCantelliClass` interface.  They are not the exact textbook theorem:
outer probability, outer almost-sure convergence, and concrete empirical-measure
semantics remain separate primitive layers.
-/

namespace StatInference

open Filter
open scoped Topology

/--
Endpoint strong-law assembly data for a selected finite bracketing sequence.

The fields are proof-carrying: endpoint empirical averages are represented by
`lowerEmpirical` and `upperEmpirical`, while the finite endpoint SLLN work is
summarized as absolute endpoint-error bounds with a radius tending to zero.
This is the finite-endpoint handoff needed before constructing
`L1BracketingNumberConstructorObligations`.
-/
structure FiniteBracketEndpointStrongLawAssembly {Index Bracket : Type*}
    [Fintype Bracket] (indexClass : Set Index)
    (populationRisk : Index -> ℝ)
    (empiricalRisk : ℕ -> Index -> ℝ) where
  family :
    ℕ ->
      FiniteL1BracketingFamily (Bracket := Bracket)
        indexClass populationRisk
  lowerEmpirical : ℕ -> Bracket -> ℝ
  upperEmpirical : ℕ -> Bracket -> ℝ
  endpointRadius : ℕ -> ℝ
  empirical_lower :
    ∀ sampleSize index hindex,
      lowerEmpirical sampleSize
          ((family sampleSize).bracketOf index hindex) ≤
        empiricalRisk sampleSize index
  empirical_upper :
    ∀ sampleSize index hindex,
      empiricalRisk sampleSize index ≤
        upperEmpirical sampleSize
          ((family sampleSize).bracketOf index hindex)
  upper_endpoint_abs_bound :
    ∀ sampleSize bracket,
      |upperEmpirical sampleSize bracket -
          (family sampleSize).upperPopulation bracket| ≤
        endpointRadius sampleSize
  lower_endpoint_abs_bound :
    ∀ sampleSize bracket,
      |(family sampleSize).lowerPopulation bracket -
          lowerEmpirical sampleSize bracket| ≤
        endpointRadius sampleSize
  endpoint_tendsto_zero :
    Tendsto endpointRadius atTop (𝓝 0)
  scale_tendsto_zero :
    Tendsto (fun sampleSize => (family sampleSize).scale) atTop (𝓝 0)

namespace FiniteBracketEndpointStrongLawAssembly

/--
Turn finite endpoint absolute-error control into constructor obligations for the
current finite-L1-bracketing GC handoff.
-/
def toConstructorObligations {Index Bracket : Type*} [Fintype Bracket]
    {indexClass : Set Index} {populationRisk : Index -> ℝ}
    {empiricalRisk : ℕ -> Index -> ℝ}
    (assembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := Bracket)
        indexClass populationRisk empiricalRisk) :
    L1BracketingNumberConstructorObligations (Bracket := Bracket)
      indexClass populationRisk empiricalRisk where
  family := assembly.family
  lowerEmpirical := assembly.lowerEmpirical
  upperEmpirical := assembly.upperEmpirical
  endpointRadius := assembly.endpointRadius
  empirical_lower := assembly.empirical_lower
  empirical_upper := assembly.empirical_upper
  upper_endpoint_bound := by
    intro sampleSize index hindex
    exact
      (abs_le.mp
        (assembly.upper_endpoint_abs_bound sampleSize
          ((assembly.family sampleSize).bracketOf index hindex))).2
  lower_endpoint_bound := by
    intro sampleSize index hindex
    exact
      (abs_le.mp
        (assembly.lower_endpoint_abs_bound sampleSize
          ((assembly.family sampleSize).bracketOf index hindex))).2
  endpoint_tendsto_zero := assembly.endpoint_tendsto_zero
  scale_tendsto_zero := assembly.scale_tendsto_zero

/-- Build the current shrinking finite-bracketing sequence route. -/
def toSequenceRoute {Index Bracket : Type*} [Fintype Bracket]
    {indexClass : Set Index} {populationRisk : Index -> ℝ}
    {empiricalRisk : ℕ -> Index -> ℝ}
    (assembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := Bracket)
        indexClass populationRisk empiricalRisk) :
    L1BracketingSequenceRoute (Bracket := Bracket)
      indexClass populationRisk empiricalRisk :=
  assembly.toConstructorObligations.toSequenceRoute

/-- Build the current `GlivenkoCantelliClass` interface from endpoint assembly. -/
def toGlivenkoCantelliClass {Index Bracket : Type*} [Fintype Bracket]
    {indexClass : Set Index} {populationRisk : Index -> ℝ}
    {empiricalRisk : ℕ -> Index -> ℝ}
    (assembly :
      FiniteBracketEndpointStrongLawAssembly (Bracket := Bracket)
        indexClass populationRisk empiricalRisk) :
    GlivenkoCantelliClass indexClass populationRisk empiricalRisk :=
  assembly.toConstructorObligations.toGlivenkoCantelliClass

end FiniteBracketEndpointStrongLawAssembly

end StatInference
