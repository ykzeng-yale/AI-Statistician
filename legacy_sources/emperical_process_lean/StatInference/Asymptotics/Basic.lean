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

/-- From a uniform deviation bound, population risk is bounded by empirical risk plus `delta`. -/
theorem population_le_empirical_add_of_uniform_deviation
    {ι : Type*} (R Rn : ι -> ℝ) (g : ι) (delta : ℝ)
    (h_uniform : ∀ h, |Rn h - R h| ≤ delta) :
    R g ≤ Rn g + delta := by
  have h_left := (abs_le.mp (h_uniform g)).1
  nlinarith

/-- From a uniform deviation bound, empirical risk is bounded by population risk plus `delta`. -/
theorem empirical_le_population_add_of_uniform_deviation
    {ι : Type*} (R Rn : ι -> ℝ) (g : ι) (delta : ℝ)
    (h_uniform : ∀ h, |Rn h - R h| ≤ delta) :
    Rn g ≤ R g + delta := by
  have h_right := (abs_le.mp (h_uniform g)).2
  nlinarith

/-- A uniform deviation radius over a nonempty class is necessarily nonnegative. -/
theorem uniform_deviation_nonneg
    {ι : Type*} [Nonempty ι] (R Rn : ι -> ℝ) (delta : ℝ)
    (h_uniform : ∀ g, |Rn g - R g| ≤ delta) :
    0 ≤ delta := by
  obtain ⟨g⟩ := (inferInstance : Nonempty ι)
  exact le_trans (abs_nonneg (Rn g - R g)) (h_uniform g)

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

/-- Oracle inequality for a globally approximate empirical minimizer. -/
theorem oracle_ineq_of_uniform_deviation_approx_erm
    {ι : Type*} (R Rn : ι -> ℝ) (fhat : ι) (eps delta : ℝ)
    (h_uniform : ∀ g, |Rn g - R g| ≤ delta)
    (h_erm : ∀ g, Rn fhat ≤ Rn g + eps) :
    ∀ f, R fhat ≤ R f + 2 * delta + eps := by
  intro f
  exact oracle_ineq_of_uniform_deviation R Rn fhat f eps delta h_uniform (h_erm f)

/-- Exact empirical minimizer version of the oracle inequality. -/
theorem oracle_ineq_of_uniform_deviation_exact_erm
    {ι : Type*} (R Rn : ι -> ℝ) (fhat f : ι) (delta : ℝ)
    (h_uniform : ∀ g, |Rn g - R g| ≤ delta)
    (h_erm : Rn fhat ≤ Rn f) :
    R fhat ≤ R f + 2 * delta := by
  have h := oracle_ineq_of_uniform_deviation R Rn fhat f 0 delta h_uniform (by simpa using h_erm)
  nlinarith

/-- Oracle inequality for a globally exact empirical minimizer. -/
theorem oracle_ineq_of_uniform_deviation_exact_erm_all
    {ι : Type*} (R Rn : ι -> ℝ) (fhat : ι) (delta : ℝ)
    (h_uniform : ∀ g, |Rn g - R g| ≤ delta)
    (h_erm : ∀ g, Rn fhat ≤ Rn g) :
    ∀ f, R fhat ≤ R f + 2 * delta := by
  intro f
  exact oracle_ineq_of_uniform_deviation_exact_erm R Rn fhat f delta h_uniform (h_erm f)

/-- Excess-risk form of `oracle_ineq_of_uniform_deviation`. -/
theorem excess_risk_bound_of_uniform_deviation
    {ι : Type*} (R Rn : ι -> ℝ) (fhat f : ι) (eps delta : ℝ)
    (h_uniform : ∀ g, |Rn g - R g| ≤ delta)
    (h_erm : Rn fhat ≤ Rn f + eps) :
    R fhat - R f ≤ 2 * delta + eps := by
  have h := oracle_ineq_of_uniform_deviation R Rn fhat f eps delta h_uniform h_erm
  nlinarith

/-- Excess-risk bound for a globally approximate empirical minimizer. -/
theorem excess_risk_bound_of_uniform_deviation_approx_erm
    {ι : Type*} (R Rn : ι -> ℝ) (fhat : ι) (eps delta : ℝ)
    (h_uniform : ∀ g, |Rn g - R g| ≤ delta)
    (h_erm : ∀ g, Rn fhat ≤ Rn g + eps) :
    ∀ f, R fhat - R f ≤ 2 * delta + eps := by
  intro f
  exact excess_risk_bound_of_uniform_deviation R Rn fhat f eps delta h_uniform (h_erm f)

/-- Excess-risk bound for an exact empirical minimizer. -/
theorem excess_risk_bound_of_uniform_deviation_exact_erm
    {ι : Type*} (R Rn : ι -> ℝ) (fhat f : ι) (delta : ℝ)
    (h_uniform : ∀ g, |Rn g - R g| ≤ delta)
    (h_erm : Rn fhat ≤ Rn f) :
    R fhat - R f ≤ 2 * delta := by
  have h := oracle_ineq_of_uniform_deviation_exact_erm R Rn fhat f delta h_uniform h_erm
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

/-- Sequence-level excess-risk bound for globally approximate ERM. -/
theorem oracle_excess_sequence_bound_of_approx_erm
    {ι : Type*} (R : ι -> ℝ) (Rn : ℕ -> ι -> ℝ) (fhat : ℕ -> ι)
    (eps delta : ℕ -> ℝ)
    (h_uniform : ∀ n g, |Rn n g - R g| ≤ delta n)
    (h_erm : ∀ n g, Rn n (fhat n) ≤ Rn n g + eps n) :
    ∀ n f, R (fhat n) - R f ≤ 2 * delta n + eps n := by
  intro n f
  exact excess_risk_bound_of_uniform_deviation
    R (Rn n) (fhat n) f (eps n) (delta n) (h_uniform n) (h_erm n f)

/-- Sequence-level excess-risk bound for globally exact ERM. -/
theorem oracle_excess_sequence_bound_of_exact_erm
    {ι : Type*} (R : ι -> ℝ) (Rn : ℕ -> ι -> ℝ) (fhat : ℕ -> ι)
    (delta : ℕ -> ℝ)
    (h_uniform : ∀ n g, |Rn n g - R g| ≤ delta n)
    (h_erm : ∀ n g, Rn n (fhat n) ≤ Rn n g) :
    ∀ n f, R (fhat n) - R f ≤ 2 * delta n := by
  intro n f
  exact excess_risk_bound_of_uniform_deviation_exact_erm
    R (Rn n) (fhat n) f (delta n) (h_uniform n) (h_erm n f)

/--
Eventual version of the sequence oracle bound, useful when asymptotic
assumptions are only known for all sufficiently large sample sizes.
-/
theorem eventually_oracle_excess_bound
    {ι : Type*} (R : ι -> ℝ) (Rn : ℕ -> ι -> ℝ) (fhat : ℕ -> ι) (f : ι)
    (eps delta : ℕ -> ℝ)
    (h_uniform : ∀ᶠ n in atTop, ∀ g, |Rn n g - R g| ≤ delta n)
    (h_erm : ∀ᶠ n in atTop, Rn n (fhat n) ≤ Rn n f + eps n) :
    ∀ᶠ n in atTop, R (fhat n) - R f ≤ 2 * delta n + eps n := by
  filter_upwards [h_uniform, h_erm] with n h_uniform_n h_erm_n
  exact excess_risk_bound_of_uniform_deviation
    R (Rn n) (fhat n) f (eps n) (delta n) h_uniform_n h_erm_n

/-- If uniform-deviation and ERM-error bounds vanish, then their oracle bound vanishes. -/
theorem oracle_bound_tendsto_zero
    (eps delta : ℕ -> ℝ)
    (h_delta : Tendsto delta atTop (𝓝 0))
    (h_eps : Tendsto eps atTop (𝓝 0)) :
    Tendsto (fun n => 2 * delta n + eps n) atTop (𝓝 0) := by
  simpa using (h_delta.const_mul 2).add h_eps

/-- Sum of two deterministic error sequences that both vanish also vanishes. -/
theorem tendsto_add_zero
    (a b : ℕ -> ℝ)
    (ha : Tendsto a atTop (𝓝 0))
    (hb : Tendsto b atTop (𝓝 0)) :
    Tendsto (fun n => a n + b n) atTop (𝓝 0) := by
  simpa using ha.add hb

/-- A fixed scalar multiple of a vanishing deterministic error sequence vanishes. -/
theorem tendsto_const_mul_zero
    (c : ℝ) (a : ℕ -> ℝ)
    (ha : Tendsto a atTop (𝓝 0)) :
    Tendsto (fun n => c * a n) atTop (𝓝 0) := by
  simpa using ha.const_mul c

/-- Sum of three deterministic error sequences that vanish also vanishes. -/
theorem tendsto_add_three_zero
    (a b c : ℕ -> ℝ)
    (ha : Tendsto a atTop (𝓝 0))
    (hb : Tendsto b atTop (𝓝 0))
    (hc : Tendsto c atTop (𝓝 0)) :
    Tendsto (fun n => a n + b n + c n) atTop (𝓝 0) := by
  simpa [add_assoc] using (ha.add hb).add hc

end StatInference
