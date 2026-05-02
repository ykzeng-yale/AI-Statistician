import StatInference.EmpiricalProcess.L1Bracketing

/-!
# Primitive L1 bracketing-number signatures

This module adds proof-carrying signatures for the primitive `L1(P)`
bracketing-number layer needed by the VdV&W 2.4.1 route.

The key design choice is intentional: a finite bracketing-number assumption is
represented by explicit finite bracket cover data, not by a bare natural number.
This keeps the future empirical-process constructor honest about the lower and
upper endpoint functions whose finite strong-law obligations must be proved.
-/

namespace StatInference

open Filter
open scoped Topology

/--
A finite `L1(P)` bracketing-number witness at one requested scale.

The witness packages a finite bracket type together with an explicit
`FiniteL1BracketingFamily`.  The bound `family.scale ≤ scale` is the primitive
finite-cover assertion corresponding to VdV&W Definition 2.1.6 at one positive
radius.
-/
structure L1BracketingNumberWitness {Index : Type*}
    (indexClass : Set Index) (populationRisk : Index -> ℝ) (scale : ℝ) where
  Bracket : Type
  finite : Fintype Bracket
  family :
    @FiniteL1BracketingFamily Index Bracket finite
      indexClass populationRisk
  scale_bound : family.scale ≤ scale

namespace L1BracketingNumberWitness

/-- Project the finite-marker evidence carried by a bracketing-number witness. -/
def finiteBracketMarker {Index : Type*}
    {indexClass : Set Index} {populationRisk : Index -> ℝ} {scale : ℝ}
    (witness : L1BracketingNumberWitness indexClass populationRisk scale) :
    FiniteClassMarker (Set.univ : Set witness.Bracket) := by
  letI := witness.finite
  exact { finite := Set.finite_univ }

/-- Restate the scale bound in theorem form for premise retrieval. -/
theorem family_scale_le {Index : Type*}
    {indexClass : Set Index} {populationRisk : Index -> ℝ} {scale : ℝ}
    (witness : L1BracketingNumberWitness indexClass populationRisk scale) :
    (letI := witness.finite; witness.family.scale ≤ scale) :=
  witness.scale_bound

end L1BracketingNumberWitness

/--
There is a finite `L1(P)` bracketing-number witness at the requested scale.

This is a proposition-level wrapper around the explicit witness, useful for
textbook-style theorem statements while preserving access to cover data.
-/
def L1BracketingNumberFiniteAt {Index : Type*}
    (indexClass : Set Index) (populationRisk : Index -> ℝ)
    (scale : ℝ) : Prop :=
  Nonempty (L1BracketingNumberWitness indexClass populationRisk scale)

/--
VdV&W Definition 2.1.6 style finite bracketing at every positive scale, stated
against the current abstract population-risk interface.
-/
structure FiniteL1BracketingNumberAtEveryScale {Index : Type*}
    (indexClass : Set Index) (populationRisk : Index -> ℝ) where
  witness :
    ∀ scale, 0 < scale ->
      L1BracketingNumberWitness indexClass populationRisk scale

namespace FiniteL1BracketingNumberAtEveryScale

/-- Select explicit finite cover data at a positive scale. -/
def witnessAt {Index : Type*}
    {indexClass : Set Index} {populationRisk : Index -> ℝ}
    (hfinite : FiniteL1BracketingNumberAtEveryScale
      indexClass populationRisk)
    (scale : ℝ) (hscale : 0 < scale) :
    L1BracketingNumberWitness indexClass populationRisk scale :=
  hfinite.witness scale hscale

/-- Project the proposition-level finite-at-scale assertion. -/
theorem finiteAt {Index : Type*}
    {indexClass : Set Index} {populationRisk : Index -> ℝ}
    (hfinite : FiniteL1BracketingNumberAtEveryScale
      indexClass populationRisk)
    (scale : ℝ) (hscale : 0 < scale) :
    L1BracketingNumberFiniteAt indexClass populationRisk scale :=
  ⟨hfinite.witnessAt scale hscale⟩

end FiniteL1BracketingNumberAtEveryScale

/--
Constructor obligations for turning primitive finite L1 bracketing-number data
into the current shrinking finite-bracketing GC handoff.

This is still not the exact VdV&W 2.4.1 theorem: endpoint strong-law events,
outer measurability, and exact sample-average semantics remain separate
formalization layers.  The structure only records the deterministic data needed
to build the existing `L1BracketingSequenceRoute`.
-/
structure L1BracketingNumberConstructorObligations {Index Bracket : Type*}
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

namespace L1BracketingNumberConstructorObligations

/--
Build the existing finite-L1-bracketing sequence route from constructor
obligations.
-/
def toSequenceRoute {Index Bracket : Type*} [Fintype Bracket]
    {indexClass : Set Index} {populationRisk : Index -> ℝ}
    {empiricalRisk : ℕ -> Index -> ℝ}
    (obligations :
      L1BracketingNumberConstructorObligations (Bracket := Bracket)
        indexClass populationRisk empiricalRisk) :
    L1BracketingSequenceRoute (Bracket := Bracket)
      indexClass populationRisk empiricalRisk where
  family := obligations.family
  lowerEmpirical := obligations.lowerEmpirical
  upperEmpirical := obligations.upperEmpirical
  endpointRadius := obligations.endpointRadius
  empirical_lower := obligations.empirical_lower
  empirical_upper := obligations.empirical_upper
  upper_endpoint_bound := obligations.upper_endpoint_bound
  lower_endpoint_bound := obligations.lower_endpoint_bound
  endpoint_tendsto_zero := obligations.endpoint_tendsto_zero
  scale_tendsto_zero := obligations.scale_tendsto_zero

/-- Project the uniform empirical-deviation sequence induced by the obligations. -/
theorem toEmpiricalDeviationSequenceOn {Index Bracket : Type*}
    [Fintype Bracket] {indexClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (obligations :
      L1BracketingNumberConstructorObligations (Bracket := Bracket)
        indexClass populationRisk empiricalRisk) :
    EmpiricalDeviationSequenceOn indexClass populationRisk empiricalRisk
      (fun sampleSize =>
        obligations.endpointRadius sampleSize +
          (obligations.family sampleSize).scale) :=
  obligations.toSequenceRoute.toEmpiricalDeviationSequenceOn

/-- Convert constructor obligations into the current GC-class interface. -/
def toGlivenkoCantelliClass {Index Bracket : Type*} [Fintype Bracket]
    {indexClass : Set Index} {populationRisk : Index -> ℝ}
    {empiricalRisk : ℕ -> Index -> ℝ}
    (obligations :
      L1BracketingNumberConstructorObligations (Bracket := Bracket)
        indexClass populationRisk empiricalRisk) :
    GlivenkoCantelliClass indexClass populationRisk empiricalRisk :=
  obligations.toSequenceRoute.toGlivenkoCantelliClass

end L1BracketingNumberConstructorObligations

end StatInference
