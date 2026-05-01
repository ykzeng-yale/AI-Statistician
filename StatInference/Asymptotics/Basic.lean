import Mathlib

/-!
# Statistics-facing asymptotic interfaces

This file starts with small, verified interfaces and a reusable deterministic
oracle inequality. Deeper probability-specific wrappers should be built on top
of mathlib convergence, CLT, and Slutsky-style theorems rather than by adding
new axioms.
-/

namespace StatInference

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

end StatInference

