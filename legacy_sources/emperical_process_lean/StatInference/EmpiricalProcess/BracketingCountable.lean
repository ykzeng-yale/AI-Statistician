import StatInference.EmpiricalProcess.BracketingPrimitive

/-!
# Countable finite-bracketing routes

This module packages the deterministic decreasing-radius part of the
finite-bracketing Glivenko-Cantelli proof using a countable sequence of finite
bracket covers.  This is the shape needed for almost-sure arguments: fixed
finite covers can be handled by the strong law, and countably many such covers
can be intersected almost surely.
-/

namespace StatInference

open MeasureTheory Filter
open scoped Topology

universe u v w

/--
A countable primitive finite-bracketing route: for each natural scale there is
a finite primitive `L1(P)` bracket cover, with cover widths tending to zero and
endpoint empirical-deviation radii tending to zero.
-/
structure CountablePrimitiveFiniteBracketingGCRoute
    {Observation : Type u} {Index : Type v}
    [MeasurableSpace Observation] (μ : Measure Observation)
    (indexClass : Set Index)
    (classFun : Index -> Observation -> ℝ)
    (samples : ∀ sampleSize, SampleAt Observation sampleSize) where
  Bracket : ℕ -> Type w
  finiteBracket : ∀ scale, Fintype (Bracket scale)
  width : ℕ -> ℝ
  width_tendsto_zero : Tendsto width atTop (𝓝 0)
  cover :
    ∀ scale,
      @FiniteL1BracketCover Observation Index (Bracket scale)
        (finiteBracket scale) _ μ indexClass classFun (width scale)
  endpointRadius : ∀ _scale, ℕ -> ℝ
  endpoint_tendsto_zero :
    ∀ scale, Tendsto (endpointRadius scale) atTop (𝓝 0)
  upper_endpoint_bound :
    ∀ scale sampleSize (bracketIndex : Bracket scale),
      empiricalAverage (samples sampleSize)
          ((cover scale).cover.bracket bracketIndex).upper -
          ((cover scale).cover.bracket bracketIndex).upperIntegral μ ≤
        endpointRadius scale sampleSize
  lower_endpoint_bound :
    ∀ scale sampleSize (bracketIndex : Bracket scale),
      ((cover scale).cover.bracket bracketIndex).lowerIntegral μ -
          empiricalAverage (samples sampleSize)
            ((cover scale).cover.bracket bracketIndex).lower ≤
        endpointRadius scale sampleSize

namespace CountablePrimitiveFiniteBracketingGCRoute

/--
Build a countable route from countably many finite primitive covers and endpoint
convergence for every endpoint in every cover.
-/
noncomputable def ofFiniteCoverSequenceAndEndpointTendsto
    {Observation : Type u} {Index : Type v}
    [MeasurableSpace Observation] {μ : Measure Observation}
    {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ}
    {samples : ∀ sampleSize, SampleAt Observation sampleSize}
    (Bracket : ℕ -> Type w)
    (finiteBracket : ∀ scale, Fintype (Bracket scale))
    (width : ℕ -> ℝ)
    (h_width_tendsto : Tendsto width atTop (𝓝 0))
    (cover :
      ∀ scale,
        @FiniteL1BracketCover Observation Index (Bracket scale)
          (finiteBracket scale) _ μ indexClass classFun (width scale))
    (h_upper :
      ∀ scale (bracketIndex : Bracket scale),
        Tendsto
          (fun sampleSize =>
            empiricalAverage (samples sampleSize)
                ((cover scale).cover.bracket bracketIndex).upper -
              ((cover scale).cover.bracket bracketIndex).upperIntegral μ)
          atTop (𝓝 0))
    (h_lower :
      ∀ scale (bracketIndex : Bracket scale),
        Tendsto
          (fun sampleSize =>
            ((cover scale).cover.bracket bracketIndex).lowerIntegral μ -
              empiricalAverage (samples sampleSize)
                ((cover scale).cover.bracket bracketIndex).lower)
          atTop (𝓝 0)) :
    CountablePrimitiveFiniteBracketingGCRoute μ indexClass classFun samples where
  Bracket := Bracket
  finiteBracket := finiteBracket
  width := width
  width_tendsto_zero := h_width_tendsto
  cover := cover
  endpointRadius := by
    intro scale
    letI := finiteBracket scale
    exact (cover scale).endpointRadius samples
  endpoint_tendsto_zero := by
    intro scale
    letI := finiteBracket scale
    exact
      (cover scale).endpointRadius_tendsto_zero_of_endpoint_tendsto
        samples (h_upper scale) (h_lower scale)
  upper_endpoint_bound := by
    intro scale sampleSize bracketIndex
    letI := finiteBracket scale
    exact
      (cover scale).upper_endpoint_error_le_endpointRadius
        samples sampleSize bracketIndex
  lower_endpoint_bound := by
    intro scale sampleSize bracketIndex
    letI := finiteBracket scale
    exact
      (cover scale).lower_endpoint_error_le_endpointRadius
        samples sampleSize bracketIndex

/--
A countable sequence of finite primitive covers with vanishing width and
vanishing endpoint radii implies uniform deviation convergence to zero.
-/
theorem uniformDeviationTendstoZeroOn
    {Observation : Type u} {Index : Type v}
    [MeasurableSpace Observation] {μ : Measure Observation}
    {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ}
    {samples : ∀ sampleSize, SampleAt Observation sampleSize}
    (route :
      CountablePrimitiveFiniteBracketingGCRoute μ indexClass classFun samples) :
    UniformDeviationTendstoZeroOn indexClass
      (fun index => populationRiskOfFunction μ (classFun index))
      (fun sampleSize index =>
        empiricalAverage (samples sampleSize) (classFun index)) := by
  intro tolerance htolerance
  have h_width_eventually :
      ∀ᶠ scale in atTop, route.width scale < tolerance / 2 :=
    route.width_tendsto_zero.eventually_lt_const (by linarith)
  rcases (eventually_atTop.1 h_width_eventually) with
    ⟨scale, hscale⟩
  letI := route.finiteBracket scale
  have hwidth_lt : route.width scale < tolerance / 2 :=
    hscale scale le_rfl
  have h_endpoint_eventually :
      ∀ᶠ sampleSize in atTop,
        route.endpointRadius scale sampleSize < tolerance / 2 :=
    (route.endpoint_tendsto_zero scale).eventually_lt_const (by linarith)
  filter_upwards [h_endpoint_eventually] with sampleSize h_endpoint_lt
  have hbound :
      EmpiricalDeviationBoundOn indexClass
        (fun index => populationRiskOfFunction μ (classFun index))
        (fun index => empiricalAverage (samples sampleSize) (classFun index))
        (route.endpointRadius scale sampleSize + route.width scale) :=
    (route.cover scale).empiricalDeviationBoundOn_of_endpoint_bounds
      (samples sampleSize)
      (route.endpointRadius scale sampleSize) (route.width scale)
      le_rfl
      (route.upper_endpoint_bound scale sampleSize)
      (route.lower_endpoint_bound scale sampleSize)
  intro index hindex
  have hdev := hbound index hindex
  have hradius :
      route.endpointRadius scale sampleSize + route.width scale ≤
        tolerance := by
    linarith
  exact le_trans hdev hradius

end CountablePrimitiveFiniteBracketingGCRoute

end StatInference
