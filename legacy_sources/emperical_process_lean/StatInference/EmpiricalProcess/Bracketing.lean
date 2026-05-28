import StatInference.EmpiricalProcess.Complexity

/-!
# Deterministic bracketing inequalities

This file formalizes the deterministic inequality at the core of the
bracketing Glivenko-Cantelli proof in van der Vaart and Wellner, Theorem 2.4.1.

The probabilistic theorem also needs finite bracketing numbers, endpoint laws
of large numbers, measurability, and outer-probability bookkeeping.  Those are
not asserted here.  Instead, this module proves the reusable deterministic
handoff: if every class member lies between bracket endpoints for both
population and empirical risks, the endpoint deviations are controlled, and the
population bracket width is small, then the whole class has a uniform
empirical-deviation bound.
-/

namespace StatInference

open Filter
open scoped Topology

/--
Single-sample deterministic bracketing bound.

This is the Lean form of the inequality used in the proof of VdV&W 2.4.1:
for `f` in a bracket `[l, u]`,

`|Pₙ f - P f| ≤ max(endpoint errors) + P(u - l)`.

The theorem is stated for abstract real-valued population and empirical risks
so that later measure-theoretic modules can instantiate the endpoint-order and
width assumptions with integrals of lower and upper bracket functions.
-/
theorem empiricalDeviationBoundOn_of_bracket_endpoint_bounds
    {Index Bracket : Type*} {indexClass : Set Index}
    (populationRisk empiricalRisk : Index -> ℝ)
    (lowerPopulation upperPopulation lowerEmpirical upperEmpirical :
      Bracket -> ℝ)
    (bracketOf : ∀ index, index ∈ indexClass -> Bracket)
    (endpointRadius widthRadius : ℝ)
    (h_emp_lower :
      ∀ index hindex,
        lowerEmpirical (bracketOf index hindex) ≤ empiricalRisk index)
    (h_emp_upper :
      ∀ index hindex,
        empiricalRisk index ≤ upperEmpirical (bracketOf index hindex))
    (h_pop_lower :
      ∀ index hindex,
        lowerPopulation (bracketOf index hindex) ≤ populationRisk index)
    (h_pop_upper :
      ∀ index hindex,
        populationRisk index ≤ upperPopulation (bracketOf index hindex))
    (h_width :
      ∀ index hindex,
        upperPopulation (bracketOf index hindex) -
            lowerPopulation (bracketOf index hindex) ≤ widthRadius)
    (h_upper_endpoint :
      ∀ index hindex,
        upperEmpirical (bracketOf index hindex) -
            upperPopulation (bracketOf index hindex) ≤ endpointRadius)
    (h_lower_endpoint :
      ∀ index hindex,
        lowerPopulation (bracketOf index hindex) -
            lowerEmpirical (bracketOf index hindex) ≤ endpointRadius) :
    EmpiricalDeviationBoundOn indexClass populationRisk empiricalRisk
      (endpointRadius + widthRadius) := by
  intro index hindex
  let bracket := bracketOf index hindex
  have h_upper :
      empiricalRisk index - populationRisk index ≤
        endpointRadius + widthRadius := by
    have h_order :
        empiricalRisk index - populationRisk index ≤
          upperEmpirical bracket - lowerPopulation bracket := by
      dsimp [bracket]
      nlinarith [h_emp_upper index hindex, h_pop_lower index hindex]
    have h_endpoint :
        upperEmpirical bracket - upperPopulation bracket ≤ endpointRadius := by
      dsimp [bracket]
      exact h_upper_endpoint index hindex
    have h_width_bound :
        upperPopulation bracket - lowerPopulation bracket ≤ widthRadius := by
      dsimp [bracket]
      exact h_width index hindex
    nlinarith
  have h_lower :
      populationRisk index - empiricalRisk index ≤
        endpointRadius + widthRadius := by
    have h_order :
        populationRisk index - empiricalRisk index ≤
          upperPopulation bracket - lowerEmpirical bracket := by
      dsimp [bracket]
      nlinarith [h_pop_upper index hindex, h_emp_lower index hindex]
    have h_endpoint :
        lowerPopulation bracket - lowerEmpirical bracket ≤ endpointRadius := by
      dsimp [bracket]
      exact h_lower_endpoint index hindex
    have h_width_bound :
        upperPopulation bracket - lowerPopulation bracket ≤ widthRadius := by
      dsimp [bracket]
      exact h_width index hindex
    nlinarith
  exact abs_le.mpr ⟨by nlinarith, h_upper⟩

/--
Sequence-level deterministic bracketing bound.

Endpoint deviations and empirical bracket endpoints may depend on sample size;
the population bracket endpoints and population width are fixed.  This is the
deterministic part needed before endpoint LLNs can turn finite bracketing into
a GC theorem.
-/
theorem empiricalDeviationSequenceOn_of_bracket_endpoint_bounds
    {Index Bracket : Type*} {indexClass : Set Index}
    (populationRisk : Index -> ℝ) (empiricalRisk : ℕ -> Index -> ℝ)
    (lowerPopulation upperPopulation : Bracket -> ℝ)
    (lowerEmpirical upperEmpirical : ℕ -> Bracket -> ℝ)
    (bracketOf : ∀ _sampleSize index, index ∈ indexClass -> Bracket)
    (endpointRadius widthRadius : ℕ -> ℝ)
    (h_emp_lower :
      ∀ sampleSize index hindex,
        lowerEmpirical sampleSize (bracketOf sampleSize index hindex) ≤
          empiricalRisk sampleSize index)
    (h_emp_upper :
      ∀ sampleSize index hindex,
        empiricalRisk sampleSize index ≤
          upperEmpirical sampleSize (bracketOf sampleSize index hindex))
    (h_pop_lower :
      ∀ sampleSize index hindex,
        lowerPopulation (bracketOf sampleSize index hindex) ≤
          populationRisk index)
    (h_pop_upper :
      ∀ sampleSize index hindex,
        populationRisk index ≤
          upperPopulation (bracketOf sampleSize index hindex))
    (h_width :
      ∀ sampleSize index hindex,
        upperPopulation (bracketOf sampleSize index hindex) -
            lowerPopulation (bracketOf sampleSize index hindex) ≤
          widthRadius sampleSize)
    (h_upper_endpoint :
      ∀ sampleSize index hindex,
        upperEmpirical sampleSize (bracketOf sampleSize index hindex) -
            upperPopulation (bracketOf sampleSize index hindex) ≤
          endpointRadius sampleSize)
    (h_lower_endpoint :
      ∀ sampleSize index hindex,
        lowerPopulation (bracketOf sampleSize index hindex) -
            lowerEmpirical sampleSize (bracketOf sampleSize index hindex) ≤
          endpointRadius sampleSize) :
    EmpiricalDeviationSequenceOn indexClass populationRisk empiricalRisk
      (fun sampleSize => endpointRadius sampleSize + widthRadius sampleSize) := by
  intro sampleSize
  exact empiricalDeviationBoundOn_of_bracket_endpoint_bounds
    populationRisk (empiricalRisk sampleSize)
    lowerPopulation upperPopulation
    (lowerEmpirical sampleSize) (upperEmpirical sampleSize)
    (bracketOf sampleSize) (endpointRadius sampleSize)
    (widthRadius sampleSize)
    (h_emp_lower sampleSize) (h_emp_upper sampleSize)
    (h_pop_lower sampleSize) (h_pop_upper sampleSize)
    (h_width sampleSize) (h_upper_endpoint sampleSize)
    (h_lower_endpoint sampleSize)

/--
Turn deterministic bracketing endpoint control into a GC-class interface once
the endpoint-error and bracket-width radii both vanish.

This theorem is still not the full VdV&W 2.4.1 theorem: it is the deterministic
final step after a future LLN/finite-bracketing module has proved the endpoint
control assumptions.
-/
def bracketingGlivenkoCantelliClass_of_endpoint_and_width_tendsto_zero
    {Index Bracket : Type*} {indexClass : Set Index}
    (populationRisk : Index -> ℝ) (empiricalRisk : ℕ -> Index -> ℝ)
    (lowerPopulation upperPopulation : Bracket -> ℝ)
    (lowerEmpirical upperEmpirical : ℕ -> Bracket -> ℝ)
    (bracketOf : ∀ _sampleSize index, index ∈ indexClass -> Bracket)
    (endpointRadius widthRadius : ℕ -> ℝ)
    (h_emp_lower :
      ∀ sampleSize index hindex,
        lowerEmpirical sampleSize (bracketOf sampleSize index hindex) ≤
          empiricalRisk sampleSize index)
    (h_emp_upper :
      ∀ sampleSize index hindex,
        empiricalRisk sampleSize index ≤
          upperEmpirical sampleSize (bracketOf sampleSize index hindex))
    (h_pop_lower :
      ∀ sampleSize index hindex,
        lowerPopulation (bracketOf sampleSize index hindex) ≤
          populationRisk index)
    (h_pop_upper :
      ∀ sampleSize index hindex,
        populationRisk index ≤
          upperPopulation (bracketOf sampleSize index hindex))
    (h_width :
      ∀ sampleSize index hindex,
        upperPopulation (bracketOf sampleSize index hindex) -
            lowerPopulation (bracketOf sampleSize index hindex) ≤
          widthRadius sampleSize)
    (h_upper_endpoint :
      ∀ sampleSize index hindex,
        upperEmpirical sampleSize (bracketOf sampleSize index hindex) -
            upperPopulation (bracketOf sampleSize index hindex) ≤
          endpointRadius sampleSize)
    (h_lower_endpoint :
      ∀ sampleSize index hindex,
        lowerPopulation (bracketOf sampleSize index hindex) -
            lowerEmpirical sampleSize (bracketOf sampleSize index hindex) ≤
          endpointRadius sampleSize)
    (h_endpoint_tendsto :
      Tendsto endpointRadius atTop (𝓝 0))
    (h_width_tendsto :
      Tendsto widthRadius atTop (𝓝 0)) :
    GlivenkoCantelliClass indexClass populationRisk empiricalRisk where
  radius := fun sampleSize => endpointRadius sampleSize + widthRadius sampleSize
  uniform_deviation :=
    empiricalDeviationSequenceOn_of_bracket_endpoint_bounds
      populationRisk empiricalRisk lowerPopulation upperPopulation
      lowerEmpirical upperEmpirical bracketOf endpointRadius widthRadius
      h_emp_lower h_emp_upper h_pop_lower h_pop_upper h_width
      h_upper_endpoint h_lower_endpoint
  radius_tendsto_zero := by
    simpa using h_endpoint_tendsto.add h_width_tendsto

/--
Proof-carrying finite-bracketing route for the deterministic handoff in
VdV&W 2.4.1.

The finite bracket type records the finite-cover regime.  The fields after
`bracketOf` are exactly the endpoint-order, width, and endpoint-convergence
obligations produced by the textbook proof after choosing a finite family of
brackets and applying endpoint LLNs.  This structure deliberately does not
assert those LLNs; it packages the downstream theorem so the next
measure-theoretic module can fill them against mathlib's strong law.
-/
structure FiniteBracketingEndpointRoute {Index Bracket : Type*}
    [Fintype Bracket] (indexClass : Set Index)
    (populationRisk : Index -> ℝ)
    (empiricalRisk : ℕ -> Index -> ℝ) where
  lowerPopulation : Bracket -> ℝ
  upperPopulation : Bracket -> ℝ
  lowerEmpirical : ℕ -> Bracket -> ℝ
  upperEmpirical : ℕ -> Bracket -> ℝ
  bracketOf : ∀ _sampleSize index, index ∈ indexClass -> Bracket
  endpointRadius : ℕ -> ℝ
  widthRadius : ℕ -> ℝ
  empirical_lower :
    ∀ sampleSize index hindex,
      lowerEmpirical sampleSize (bracketOf sampleSize index hindex) ≤
        empiricalRisk sampleSize index
  empirical_upper :
    ∀ sampleSize index hindex,
      empiricalRisk sampleSize index ≤
        upperEmpirical sampleSize (bracketOf sampleSize index hindex)
  population_lower :
    ∀ sampleSize index hindex,
      lowerPopulation (bracketOf sampleSize index hindex) ≤
        populationRisk index
  population_upper :
    ∀ sampleSize index hindex,
      populationRisk index ≤
        upperPopulation (bracketOf sampleSize index hindex)
  width_bound :
    ∀ sampleSize index hindex,
      upperPopulation (bracketOf sampleSize index hindex) -
          lowerPopulation (bracketOf sampleSize index hindex) ≤
        widthRadius sampleSize
  upper_endpoint_bound :
    ∀ sampleSize index hindex,
      upperEmpirical sampleSize (bracketOf sampleSize index hindex) -
          upperPopulation (bracketOf sampleSize index hindex) ≤
        endpointRadius sampleSize
  lower_endpoint_bound :
    ∀ sampleSize index hindex,
      lowerPopulation (bracketOf sampleSize index hindex) -
          lowerEmpirical sampleSize (bracketOf sampleSize index hindex) ≤
        endpointRadius sampleSize
  endpoint_tendsto_zero :
    Tendsto endpointRadius atTop (𝓝 0)
  width_tendsto_zero :
    Tendsto widthRadius atTop (𝓝 0)

namespace FiniteBracketingEndpointRoute

/--
The finite bracket index set carried by a bracketing endpoint route.

This is a small projection lemma, but it matters for audits: the route records
an actual finite bracket type rather than an unverified textual claim that a
finite bracket family exists.
-/
def finiteBracketMarker {Index Bracket : Type*} [Fintype Bracket]
    {indexClass : Set Index} {populationRisk : Index -> ℝ}
    {empiricalRisk : ℕ -> Index -> ℝ}
    (_route :
      FiniteBracketingEndpointRoute (Bracket := Bracket)
        indexClass populationRisk empiricalRisk) :
    FiniteClassMarker (Set.univ : Set Bracket) where
  finite := Set.finite_univ

/-- Extract the deterministic uniform-deviation sequence from the route. -/
theorem toEmpiricalDeviationSequenceOn {Index Bracket : Type*}
    [Fintype Bracket] {indexClass : Set Index}
    {populationRisk : Index -> ℝ} {empiricalRisk : ℕ -> Index -> ℝ}
    (route :
      FiniteBracketingEndpointRoute (Bracket := Bracket)
        indexClass populationRisk empiricalRisk) :
    EmpiricalDeviationSequenceOn indexClass populationRisk empiricalRisk
      (fun sampleSize =>
        route.endpointRadius sampleSize + route.widthRadius sampleSize) :=
  empiricalDeviationSequenceOn_of_bracket_endpoint_bounds
    populationRisk empiricalRisk route.lowerPopulation route.upperPopulation
    route.lowerEmpirical route.upperEmpirical route.bracketOf
    route.endpointRadius route.widthRadius route.empirical_lower
    route.empirical_upper route.population_lower route.population_upper
    route.width_bound route.upper_endpoint_bound route.lower_endpoint_bound

/--
Convert a verified finite-bracketing endpoint route into the current
Glivenko-Cantelli class interface.

This is the compiled proof-complete theorem currently corresponding to the
formalized part of VdV&W 2.4.1.  The remaining work for the literal textbook
statement is to construct this route from `N_[](ε, F, L1(P)) < ∞` plus the
endpoint strong law.
-/
def toGlivenkoCantelliClass {Index Bracket : Type*} [Fintype Bracket]
    {indexClass : Set Index} {populationRisk : Index -> ℝ}
    {empiricalRisk : ℕ -> Index -> ℝ}
    (route :
      FiniteBracketingEndpointRoute (Bracket := Bracket)
        indexClass populationRisk empiricalRisk) :
    GlivenkoCantelliClass indexClass populationRisk empiricalRisk where
  radius := fun sampleSize =>
    route.endpointRadius sampleSize + route.widthRadius sampleSize
  uniform_deviation := route.toEmpiricalDeviationSequenceOn
  radius_tendsto_zero := by
    simpa using route.endpoint_tendsto_zero.add route.width_tendsto_zero

/-- Pointwise deviation bound exported from the route's GC conversion. -/
theorem deviation {Index Bracket : Type*} [Fintype Bracket]
    {indexClass : Set Index} {populationRisk : Index -> ℝ}
    {empiricalRisk : ℕ -> Index -> ℝ}
    (route :
      FiniteBracketingEndpointRoute (Bracket := Bracket)
        indexClass populationRisk empiricalRisk)
    (sampleSize : ℕ) {index : Index} (hindex : index ∈ indexClass) :
    |empiricalRisk sampleSize index - populationRisk index| ≤
      route.endpointRadius sampleSize + route.widthRadius sampleSize :=
  route.toEmpiricalDeviationSequenceOn sampleSize index hindex

end FiniteBracketingEndpointRoute

end StatInference
