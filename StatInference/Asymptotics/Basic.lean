import Mathlib

/-!
# Statistics-facing asymptotic interfaces

This file starts with small, verified interfaces and a reusable deterministic
oracle inequality. Deeper probability-specific wrappers should be built on top
of mathlib convergence, CLT, and Slutsky-style theorems rather than by adding
new axioms.
-/

namespace StatInference

open Filter
open scoped Topology

/-- A marker that a proposition has been verified by Lean. This is intentionally
definitionally equal to the proposition itself. -/
def VerifiedByLean (p : Prop) : Prop := p

theorem verifiedByLean_iff {p : Prop} : VerifiedByLean p <-> p := Iff.rfl

/--
Core ERM oracle inequality from a uniform deviation bound.

This is a deterministic reduction used throughout statistical learning theory:
if empirical risks are uniformly within `delta` of population risks and `fhat`
is an `eps`-approximate ERM relative to comparator `f`, then the population
risk of `fhat` is within `2 * delta + eps` of the comparator risk.
-/
theorem oracle_ineq_of_uniform_deviation
    {ι : Type*} (R Rn : ι -> ℝ) (fhat f : ι) (eps delta : ℝ)
    (h_uniform : ∀ g, |Rn g - R g| ≤ delta)
    (h_erm : Rn fhat ≤ Rn f + eps) :
    R fhat ≤ R f + 2 * delta + eps := by
  have h_left_abs := h_uniform fhat
  have h_right_abs := h_uniform f
  have h_left := (abs_le.mp h_left_abs).1
  have h_right := (abs_le.mp h_right_abs).2
  nlinarith

/-- Excess-risk form of `oracle_ineq_of_uniform_deviation`. -/
theorem excess_risk_bound_of_uniform_deviation
    {ι : Type*} (R Rn : ι -> ℝ) (fhat f : ι) (eps delta : ℝ)
    (h_uniform : ∀ g, |Rn g - R g| ≤ delta)
    (h_erm : Rn fhat ≤ Rn f + eps) :
    R fhat - R f ≤ 2 * delta + eps := by
  have h := oracle_ineq_of_uniform_deviation R Rn fhat f eps delta h_uniform h_erm
  nlinarith

/-- Sequence-level excess-risk bound for approximate ERM under uniform deviation. -/
theorem oracle_excess_sequence_bound
    {ι : Type*} (R : ι -> ℝ) (Rn : ℕ -> ι -> ℝ) (fhat : ℕ -> ι) (f : ι)
    (eps delta : ℕ -> ℝ)
    (h_uniform : ∀ n g, |Rn n g - R g| ≤ delta n)
    (h_erm : ∀ n, Rn n (fhat n) ≤ Rn n f + eps n) :
    ∀ n, R (fhat n) - R f ≤ 2 * delta n + eps n := by
  intro n
  exact excess_risk_bound_of_uniform_deviation
    R (Rn n) (fhat n) f (eps n) (delta n) (h_uniform n) (h_erm n)

/-- If uniform-deviation and ERM-error bounds vanish, then their oracle bound vanishes. -/
theorem oracle_bound_tendsto_zero
    (eps delta : ℕ -> ℝ)
    (h_delta : Tendsto delta atTop (𝓝 0))
    (h_eps : Tendsto eps atTop (𝓝 0)) :
    Tendsto (fun n => 2 * delta n + eps n) atTop (𝓝 0) := by
  simpa using (h_delta.const_mul 2).add h_eps

end StatInference
