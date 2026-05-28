import StatInference.EmpiricalProcess.Bracketing
import StatInference.ProbabilityMeasure.StrongLaw

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
  exact ProbabilityMeasure.centeredStrongLaw_ae_real X hint hindep hident

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
  exact ProbabilityMeasure.finite_centeredStrongLaw_ae_real X hint hindep hident

end StatInference
