import StatInference.EmpiricalProcess.Bracketing
import Mathlib.Probability.StrongLaw

/-!
# Endpoint strong-law wrappers

This file connects the finite-bracketing route to mathlib's strong law of
large numbers.  The wrappers here are intentionally endpoint-level: they prove
the convergence needed for each bracket endpoint, and for every endpoint in a
finite endpoint family, without yet encoding the full bracketing-number
construction.
-/

namespace StatInference

open MeasureTheory ProbabilityTheory Filter
open scoped BigOperators Topology Function

/--
Endpoint strong law centered at the endpoint population integral.

This is a statistics-facing wrapper around mathlib's
`ProbabilityTheory.strong_law_ae_real`.
-/
theorem endpoint_strong_law_ae_real
    {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω}
    (X : ℕ -> Ω -> ℝ)
    (hint : Integrable (X 0) μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X))
    (hident : ∀ i, IdentDistrib (X i) (X 0) μ μ) :
    ∀ᵐ ω ∂μ,
      Tendsto
        (fun n : ℕ =>
          (∑ i ∈ Finset.range n, X i ω) / n - μ[X 0])
        atTop (𝓝 0) := by
  filter_upwards [ProbabilityTheory.strong_law_ae_real X hint hindep hident]
    with ω hω
  have hconst :
      Tendsto (fun _ : ℕ => μ[X 0]) atTop (𝓝 μ[X 0]) :=
    tendsto_const_nhds
  simpa using hω.sub hconst

/--
Finite-family endpoint strong law.

For a finite bracket-endpoint index type, every endpoint empirical average
converges almost surely to its population integral.  This is the finite
intersection step used in the proof of VdV&W 2.4.1 after a finite bracketing
family has been chosen.
-/
theorem finite_endpoint_strong_law_ae_real
    {Endpoint Ω : Type*} [Fintype Endpoint] [MeasurableSpace Ω]
    {μ : Measure Ω}
    (X : Endpoint -> ℕ -> Ω -> ℝ)
    (hint : ∀ endpoint, Integrable (X endpoint 0) μ)
    (hindep :
      ∀ endpoint, Pairwise ((· ⟂ᵢ[μ] ·) on X endpoint))
    (hident :
      ∀ endpoint i, IdentDistrib (X endpoint i) (X endpoint 0) μ μ) :
    ∀ᵐ ω ∂μ, ∀ endpoint,
      Tendsto
        (fun n : ℕ =>
          (∑ i ∈ Finset.range n, X endpoint i ω) / n -
            μ[X endpoint 0])
        atTop (𝓝 0) := by
  classical
  exact ae_all_iff.2
    (fun endpoint =>
      endpoint_strong_law_ae_real (X endpoint) (hint endpoint)
        (hindep endpoint) (hident endpoint))

/--
Finite-family endpoint strong law as an eventual absolute-error bound.

This is the exact shape needed before constructing endpoint-control obligations
for finite bracketing: for every fixed positive tolerance, almost surely all
finite endpoint empirical averages are eventually within that tolerance of
their population integrals.
-/
theorem finite_endpoint_strong_law_eventually_abs_le_real
    {Endpoint Ω : Type*} [Fintype Endpoint] [MeasurableSpace Ω]
    {μ : Measure Ω}
    (X : Endpoint -> ℕ -> Ω -> ℝ)
    (hint : ∀ endpoint, Integrable (X endpoint 0) μ)
    (hindep :
      ∀ endpoint, Pairwise ((· ⟂ᵢ[μ] ·) on X endpoint))
    (hident :
      ∀ endpoint i, IdentDistrib (X endpoint i) (X endpoint 0) μ μ)
    (tolerance : ℝ) (htolerance : 0 < tolerance) :
    ∀ᵐ ω ∂μ, ∀ᶠ n : ℕ in atTop, ∀ endpoint,
      |(∑ i ∈ Finset.range n, X endpoint i ω) / n -
          μ[X endpoint 0]| ≤ tolerance := by
  classical
  filter_upwards
    [finite_endpoint_strong_law_ae_real X hint hindep hident] with ω hω
  exact eventually_all.2
    (fun endpoint =>
      ((Metric.tendsto_nhds.1 (hω endpoint)) tolerance htolerance).mono
        (fun _sampleSize hdist => by
          simpa [Real.dist_eq] using le_of_lt hdist))

end StatInference
