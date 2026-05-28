import StatInference.EmpiricalProcess.EndpointStrongLaw

/-!
# Finite L1 bracketing routes

This module adds an explicit finite `L1(P)` bracketing layer for the
VdV&W 2.4.1 route.  The definitions remain abstract over population and
empirical risks: a future measure-theoretic module should instantiate
`populationRisk`, `lowerPopulation`, and `upperPopulation` with integrals.

The main handoff proved here is deterministic and proof-carrying:
finite bracket families with shrinking L1 width, together with shrinking
endpoint empirical-process control, induce the current `GlivenkoCantelliClass`
interface.  No bracketing theorem, measurability theorem, or endpoint LLN is
asserted as a primitive assumption.
-/

namespace StatInference

open Filter
open scoped Topology

/--
An explicit finite `L1(P)` bracket family at one scale.

The `scale` field represents the population `L1(P)` bracket width bound after
lower and upper bracket endpoint functions have been integrated.  The bracket
type is required to be finite at use sites through `[Fintype Bracket]`.
-/
structure FiniteL1BracketingFamily {Index Bracket : Type*}
    [Fintype Bracket] (indexClass : Set Index)
    (populationRisk : Index -> ℝ) where
  scale : ℝ
  lowerPopulation : Bracket -> ℝ
  upperPopulation : Bracket -> ℝ
  bracketOf : ∀ index, index ∈ indexClass -> Bracket
  population_lower :
    ∀ index hindex,
      lowerPopulation (bracketOf index hindex) ≤ populationRisk index
  population_upper :
    ∀ index hindex,
      populationRisk index ≤ upperPopulation (bracketOf index hindex)
  l1_width_bound :
    ∀ index hindex,
      upperPopulation (bracketOf index hindex) -
          lowerPopulation (bracketOf index hindex) ≤ scale

namespace FiniteL1BracketingFamily

/-- The finite bracket family carries a concrete finite marker. -/
def finiteBracketMarker {Index Bracket : Type*} [Fintype Bracket]
    {indexClass : Set Index} {populationRisk : Index -> ℝ}
    (_family :
      FiniteL1BracketingFamily (Bracket := Bracket)
        indexClass populationRisk) :
    FiniteClassMarker (Set.univ : Set Bracket) where
  finite := Set.finite_univ

/--
One-scale deterministic handoff from finite L1 bracketing and endpoint control
to a uniform empirical-deviation bound.
-/
theorem empiricalDeviationBoundOn_of_endpoint_bounds
    {Index Bracket : Type*} [Fintype Bracket]
    {indexClass : Set Index} {populationRisk : Index -> ℝ}
    (family :
      FiniteL1BracketingFamily (Bracket := Bracket)
        indexClass populationRisk)
    (empiricalRisk : Index -> ℝ)
    (lowerEmpirical upperEmpirical : Bracket -> ℝ)
    (endpointRadius : ℝ)
    (h_emp_lower :
      ∀ index hindex,
        lowerEmpirical (family.bracketOf index hindex) ≤ empiricalRisk index)
    (h_emp_upper :
      ∀ index hindex,
        empiricalRisk index ≤ upperEmpirical (family.bracketOf index hindex))
    (h_upper_endpoint :
      ∀ index hindex,
        upperEmpirical (family.bracketOf index hindex) -
            family.upperPopulation (family.bracketOf index hindex) ≤
          endpointRadius)
    (h_lower_endpoint :
      ∀ index hindex,
        family.lowerPopulation (family.bracketOf index hindex) -
            lowerEmpirical (family.bracketOf index hindex) ≤
          endpointRadius) :
    EmpiricalDeviationBoundOn indexClass populationRisk empiricalRisk
      (endpointRadius + family.scale) :=
  empiricalDeviationBoundOn_of_bracket_endpoint_bounds
    populationRisk empiricalRisk family.lowerPopulation family.upperPopulation
    lowerEmpirical upperEmpirical family.bracketOf endpointRadius family.scale
    h_emp_lower h_emp_upper family.population_lower family.population_upper
    family.l1_width_bound h_upper_endpoint h_lower_endpoint

end FiniteL1BracketingFamily

/--
A sequence of finite `L1(P)` bracket families plus endpoint empirical-process
control.  This is the explicit shrinking-scale route toward VdV&W 2.4.1:
the bracket family may change with sample size, and its L1 width must tend to
zero.
-/
structure L1BracketingSequenceRoute {Index Bracket : Type*}
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
  upper_endpoint_bound :
    ∀ sampleSize index hindex,
      upperEmpirical sampleSize
          ((family sampleSize).bracketOf index hindex) -
          (family sampleSize).upperPopulation
            ((family sampleSize).bracketOf index hindex) ≤
        endpointRadius sampleSize
  lower_endpoint_bound :
    ∀ sampleSize index hindex,
      (family sampleSize).lowerPopulation
          ((family sampleSize).bracketOf index hindex) -
          lowerEmpirical sampleSize
            ((family sampleSize).bracketOf index hindex) ≤
        endpointRadius sampleSize
  endpoint_tendsto_zero :
    Tendsto endpointRadius atTop (𝓝 0)
  scale_tendsto_zero :
    Tendsto (fun sampleSize => (family sampleSize).scale) atTop (𝓝 0)

namespace L1BracketingSequenceRoute

/-- Deterministic uniform-deviation sequence induced by the L1 bracketing route. -/
theorem toEmpiricalDeviationSequenceOn {Index Bracket : Type*}
    [Fintype Bracket] {indexClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (route :
      L1BracketingSequenceRoute (Bracket := Bracket)
        indexClass populationRisk empiricalRisk) :
    EmpiricalDeviationSequenceOn indexClass populationRisk empiricalRisk
      (fun sampleSize =>
        route.endpointRadius sampleSize + (route.family sampleSize).scale) := by
  intro sampleSize
  exact (route.family sampleSize).empiricalDeviationBoundOn_of_endpoint_bounds
    (empiricalRisk sampleSize) (route.lowerEmpirical sampleSize)
    (route.upperEmpirical sampleSize) (route.endpointRadius sampleSize)
    (route.empirical_lower sampleSize) (route.empirical_upper sampleSize)
    (route.upper_endpoint_bound sampleSize)
    (route.lower_endpoint_bound sampleSize)

/--
Convert a shrinking finite-L1-bracketing route into the GC-class interface.

This is the current explicit endpoint/finite-bracketing handoff.  The next
formalization layer should construct `L1BracketingSequenceRoute` from concrete
bracketing-number assumptions and endpoint strong-law events.
-/
def toGlivenkoCantelliClass {Index Bracket : Type*} [Fintype Bracket]
    {indexClass : Set Index} {populationRisk : Index -> ℝ}
    {empiricalRisk : ℕ -> Index -> ℝ}
    (route :
      L1BracketingSequenceRoute (Bracket := Bracket)
        indexClass populationRisk empiricalRisk) :
    GlivenkoCantelliClass indexClass populationRisk empiricalRisk where
  radius := fun sampleSize =>
    route.endpointRadius sampleSize + (route.family sampleSize).scale
  uniform_deviation := route.toEmpiricalDeviationSequenceOn
  radius_tendsto_zero := by
    simpa using route.endpoint_tendsto_zero.add route.scale_tendsto_zero

end L1BracketingSequenceRoute

end StatInference
