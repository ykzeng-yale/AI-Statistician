import Mathlib.Probability.StrongLaw

/-!
# Strong-law wrappers

This module records Billingsley-facing support wrappers around mathlib's
`ProbabilityTheory.strong_law_ae_real`.  The declarations are content-based
local wrappers for Section 6 source crosswalks and empirical-process endpoint
arguments; they are not yet a source-audited exact Billingsley Theorem 6.1
report.
-/

namespace StatInference
namespace ProbabilityMeasure

open MeasureTheory ProbabilityTheory Filter

open scoped BigOperators Topology Function

universe u v

/--
Real-valued strong law of large numbers in Billingsley-facing namespace.

This is a thin wrapper around `ProbabilityTheory.strong_law_ae_real`.
-/
theorem strongLaw_ae_real
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    (X : ℕ -> Ω -> ℝ)
    (hint : Integrable (X 0) μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X))
    (hident : ∀ i, IdentDistrib (X i) (X 0) μ μ) :
    ∀ᵐ ω ∂μ,
      Tendsto
        (fun n : ℕ => (∑ i ∈ Finset.range n, X i ω) / n)
        atTop (𝓝 μ[X 0]) := by
  exact ProbabilityTheory.strong_law_ae_real X hint hindep hident

/--
Centered real-valued strong law.

The empirical average minus the population integral tends to zero almost
surely under the same hypotheses as `strongLaw_ae_real`.
-/
theorem centeredStrongLaw_ae_real
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    (X : ℕ -> Ω -> ℝ)
    (hint : Integrable (X 0) μ)
    (hindep : Pairwise ((· ⟂ᵢ[μ] ·) on X))
    (hident : ∀ i, IdentDistrib (X i) (X 0) μ μ) :
    ∀ᵐ ω ∂μ,
      Tendsto
        (fun n : ℕ =>
          (∑ i ∈ Finset.range n, X i ω) / n - μ[X 0])
        atTop (𝓝 0) := by
  filter_upwards [strongLaw_ae_real X hint hindep hident] with ω hω
  have hconst :
      Tendsto (fun _ : ℕ => μ[X 0]) atTop (𝓝 μ[X 0]) :=
    tendsto_const_nhds
  simpa using hω.sub hconst

/--
Finite-family centered strong law.

This packages the finite intersection step used for endpoint families in
empirical-distribution and bracketing arguments.
-/
theorem finite_centeredStrongLaw_ae_real
    {Endpoint : Type v} {Ω : Type u} [Fintype Endpoint] [MeasurableSpace Ω]
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
      centeredStrongLaw_ae_real (X endpoint) (hint endpoint)
        (hindep endpoint) (hident endpoint))

end ProbabilityMeasure
end StatInference
