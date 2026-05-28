import StatInference.Asymptotics.Basic

/-!
# Two-stage surrogate ERM experiment

This module is a self-contained smoke experiment for forward deductive
reasoning in Lean.  The target problem is a deterministic surrogate-risk
version of the standard ERM oracle inequality.

The generated foundation is intentionally small:

* `populationRisk` is the target risk.
* `empiricalRisk` is the finite-sample risk.
* `surrogateRisk` is the risk actually minimized by an algorithm.
* `delta` controls the empirical-to-population uniform deviation.
* `eta` controls the surrogate-to-empirical uniform deviation.
* `eps` controls approximate surrogate ERM error.

The forward chain is:

1. empirical-to-population deviation plus surrogate-to-empirical deviation
   implies surrogate-to-population deviation by the triangle inequality;
2. a generated deterministic ERM oracle step applies to the surrogate risk;
3. expanding the resulting bound gives the two-stage excess-risk statement.
-/

namespace StatInference

open Filter
open scoped Topology

/--
Two uniform deviation facts needed by a two-stage surrogate ERM argument.

`empiricalRisk` is uniformly within `delta` of `populationRisk`; `surrogateRisk`
is uniformly within `eta` of `empiricalRisk`.
-/
def TwoStageUniformDeviation {Candidate : Type*}
    (populationRisk empiricalRisk surrogateRisk : Candidate -> ℝ)
    (delta eta : ℝ) : Prop :=
  (∀ candidate, |empiricalRisk candidate - populationRisk candidate| ≤ delta) ∧
    (∀ candidate, |surrogateRisk candidate - empiricalRisk candidate| ≤ eta)

/--
Forward deduction step 1: the surrogate risk is uniformly close to the
population risk when both links of the two-stage approximation chain are
uniformly controlled.
-/
theorem surrogate_uniform_deviation_of_twoStage
    {Candidate : Type*}
    (populationRisk empiricalRisk surrogateRisk : Candidate -> ℝ)
    (delta eta : ℝ)
    (h_two_stage :
      TwoStageUniformDeviation populationRisk empiricalRisk surrogateRisk
        delta eta) :
    ∀ candidate, |surrogateRisk candidate - populationRisk candidate| ≤
      delta + eta := by
  intro candidate
  have h_empirical_population :
      |empiricalRisk candidate - populationRisk candidate| ≤ delta :=
    h_two_stage.1 candidate
  have h_surrogate_empirical :
      |surrogateRisk candidate - empiricalRisk candidate| ≤ eta :=
    h_two_stage.2 candidate
  have h_decompose :
      surrogateRisk candidate - populationRisk candidate =
        (surrogateRisk candidate - empiricalRisk candidate) +
          (empiricalRisk candidate - populationRisk candidate) := by
    ring
  rw [h_decompose]
  calc
    |(surrogateRisk candidate - empiricalRisk candidate) +
        (empiricalRisk candidate - populationRisk candidate)|
        ≤ |surrogateRisk candidate - empiricalRisk candidate| +
          |empiricalRisk candidate - populationRisk candidate| :=
      abs_add_le _ _
    _ ≤ eta + delta :=
      add_le_add h_surrogate_empirical h_empirical_population
    _ = delta + eta := by ring

/--
Generated oracle step for the experiment: if the risk that is optimized is
uniformly close to population risk, approximate ERM for that optimized risk
implies a population excess-risk bound.
-/
theorem surrogate_erm_excess_bound_of_uniform_deviation
    {Candidate : Type*}
    (populationRisk surrogateRisk : Candidate -> ℝ)
    (fhat comparator : Candidate) (eps radius : ℝ)
    (h_uniform :
      ∀ candidate, |surrogateRisk candidate - populationRisk candidate| ≤
        radius)
    (h_surrogate_erm :
      surrogateRisk fhat ≤ surrogateRisk comparator + eps) :
    populationRisk fhat - populationRisk comparator ≤ 2 * radius + eps := by
  have h_fhat_left := (abs_le.mp (h_uniform fhat)).1
  have h_comparator_right := (abs_le.mp (h_uniform comparator)).2
  nlinarith

/--
Target problem, solved by forward deduction: an approximate minimizer of a
surrogate risk has population excess risk bounded by the empirical deviation,
the surrogate approximation error, and the approximate optimization error.
-/
theorem twoStage_surrogate_erm_excess_bound
    {Candidate : Type*}
    (populationRisk empiricalRisk surrogateRisk : Candidate -> ℝ)
    (fhat comparator : Candidate) (eps delta eta : ℝ)
    (h_two_stage :
      TwoStageUniformDeviation populationRisk empiricalRisk surrogateRisk
        delta eta)
    (h_surrogate_erm :
      surrogateRisk fhat ≤ surrogateRisk comparator + eps) :
    populationRisk fhat - populationRisk comparator ≤
      2 * delta + 2 * eta + eps := by
  have h_surrogate_population :
      ∀ candidate, |surrogateRisk candidate - populationRisk candidate| ≤
        delta + eta :=
    surrogate_uniform_deviation_of_twoStage populationRisk empiricalRisk
      surrogateRisk delta eta h_two_stage
  have h_oracle :
      populationRisk fhat - populationRisk comparator ≤
        2 * (delta + eta) + eps :=
    surrogate_erm_excess_bound_of_uniform_deviation populationRisk surrogateRisk
      fhat comparator eps (delta + eta) h_surrogate_population
      h_surrogate_erm
  nlinarith

/-- Sequence-level version of the two-stage uniform-deviation interface. -/
def TwoStageUniformDeviationSequence {Candidate : Type*}
    (populationRisk : Candidate -> ℝ)
    (empiricalRisk surrogateRisk : ℕ -> Candidate -> ℝ)
    (delta eta : ℕ -> ℝ) : Prop :=
  ∀ sampleSize,
    TwoStageUniformDeviation populationRisk (empiricalRisk sampleSize)
      (surrogateRisk sampleSize) (delta sampleSize) (eta sampleSize)

/--
Sequence-level target: the same two-stage excess-risk bound holds at every
sample size.
-/
theorem twoStage_surrogate_erm_sequence_excess_bound
    {Candidate : Type*}
    (populationRisk : Candidate -> ℝ)
    (empiricalRisk surrogateRisk : ℕ -> Candidate -> ℝ)
    (fhat : ℕ -> Candidate) (comparator : Candidate)
    (eps delta eta : ℕ -> ℝ)
    (h_two_stage :
      TwoStageUniformDeviationSequence populationRisk empiricalRisk
        surrogateRisk delta eta)
    (h_surrogate_erm :
      ∀ sampleSize,
        surrogateRisk sampleSize (fhat sampleSize) ≤
          surrogateRisk sampleSize comparator + eps sampleSize) :
    ∀ sampleSize,
      populationRisk (fhat sampleSize) - populationRisk comparator ≤
        2 * delta sampleSize + 2 * eta sampleSize + eps sampleSize := by
  intro sampleSize
  exact twoStage_surrogate_erm_excess_bound populationRisk
    (empiricalRisk sampleSize) (surrogateRisk sampleSize)
    (fhat sampleSize) comparator (eps sampleSize) (delta sampleSize)
    (eta sampleSize) (h_two_stage sampleSize)
    (h_surrogate_erm sampleSize)

/--
The two-stage deterministic oracle bound vanishes when all three contributing
error sequences vanish.
-/
theorem twoStage_oracle_bound_tendsto_zero
    (eps delta eta : ℕ -> ℝ)
    (h_delta : Tendsto delta atTop (𝓝 0))
    (h_eta : Tendsto eta atTop (𝓝 0))
    (h_eps : Tendsto eps atTop (𝓝 0)) :
    Tendsto (fun sampleSize =>
      2 * delta sampleSize + 2 * eta sampleSize + eps sampleSize)
      atTop (𝓝 0) := by
  have h_delta_scaled :
      Tendsto (fun sampleSize => 2 * delta sampleSize) atTop (𝓝 0) :=
    by simpa using h_delta.const_mul 2
  have h_eta_scaled :
      Tendsto (fun sampleSize => 2 * eta sampleSize) atTop (𝓝 0) :=
    by simpa using h_eta.const_mul 2
  simpa [add_assoc] using (h_delta_scaled.add h_eta_scaled).add h_eps

/--
Proof-carrying route for the whole two-stage surrogate ERM argument.  The
fields are exactly the generated foundational facts needed by the forward
deduction.
-/
structure TwoStageERMRoute {Candidate : Type*}
    (populationRisk : Candidate -> ℝ) where
  empiricalRisk : ℕ -> Candidate -> ℝ
  surrogateRisk : ℕ -> Candidate -> ℝ
  fhat : ℕ -> Candidate
  comparator : Candidate
  eps : ℕ -> ℝ
  delta : ℕ -> ℝ
  eta : ℕ -> ℝ
  two_stage_deviation :
    TwoStageUniformDeviationSequence populationRisk empiricalRisk
      surrogateRisk delta eta
  surrogate_erm :
    ∀ sampleSize,
      surrogateRisk sampleSize (fhat sampleSize) ≤
        surrogateRisk sampleSize comparator + eps sampleSize
  delta_tendsto_zero : Tendsto delta atTop (𝓝 0)
  eta_tendsto_zero : Tendsto eta atTop (𝓝 0)
  eps_tendsto_zero : Tendsto eps atTop (𝓝 0)

namespace TwoStageERMRoute

/-- Population excess-risk sequence induced by a two-stage ERM route. -/
def excessRiskSequence {Candidate : Type*} {populationRisk : Candidate -> ℝ}
    (route : TwoStageERMRoute populationRisk) : ℕ -> ℝ :=
  fun sampleSize =>
    populationRisk (route.fhat sampleSize) - populationRisk route.comparator

/-- Deterministic oracle-bound sequence induced by a two-stage ERM route. -/
def oracleBoundSequence {Candidate : Type*} {populationRisk : Candidate -> ℝ}
    (route : TwoStageERMRoute populationRisk) : ℕ -> ℝ :=
  fun sampleSize =>
    2 * route.delta sampleSize + 2 * route.eta sampleSize +
      route.eps sampleSize

/-- The route's excess risk is bounded by its generated oracle bound. -/
theorem excessRiskBound {Candidate : Type*} {populationRisk : Candidate -> ℝ}
    (route : TwoStageERMRoute populationRisk) :
    ∀ sampleSize,
      route.excessRiskSequence sampleSize ≤
        route.oracleBoundSequence sampleSize := by
  intro sampleSize
  simpa [excessRiskSequence, oracleBoundSequence] using
    twoStage_surrogate_erm_sequence_excess_bound populationRisk
      route.empiricalRisk route.surrogateRisk route.fhat route.comparator
      route.eps route.delta route.eta route.two_stage_deviation
      route.surrogate_erm sampleSize

/-- The route's generated oracle bound vanishes. -/
theorem oracleBoundTendstoZero
    {Candidate : Type*} {populationRisk : Candidate -> ℝ}
    (route : TwoStageERMRoute populationRisk) :
    Tendsto route.oracleBoundSequence atTop (𝓝 0) := by
  simpa [oracleBoundSequence] using
    twoStage_oracle_bound_tendsto_zero route.eps route.delta route.eta
      route.delta_tendsto_zero route.eta_tendsto_zero
      route.eps_tendsto_zero

/--
Final forward-deduction conclusion: under a two-stage route with vanishing
empirical deviation, surrogate approximation error, and approximate ERM error,
the population excess risk is eventually below every positive tolerance.
-/
theorem eventually_excessRisk_lt
    {Candidate : Type*} {populationRisk : Candidate -> ℝ}
    (route : TwoStageERMRoute populationRisk) :
    ∀ tolerance > 0,
      ∀ᶠ sampleSize in atTop,
        route.excessRiskSequence sampleSize < tolerance := by
  intro tolerance htolerance
  filter_upwards [route.oracleBoundTendstoZero.eventually_lt_const htolerance]
    with sampleSize h_bound
  exact lt_of_le_of_lt (route.excessRiskBound sampleSize) h_bound

end TwoStageERMRoute

end StatInference
