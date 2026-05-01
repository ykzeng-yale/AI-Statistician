import StatInference.Estimator.Basic

/-!
# Ratio and Hajek/IPW estimator algebra

This file contains deterministic algebra used by ratio, Hajek, and IPW
estimators.  Probability, measurability, and causal identification assumptions
belong in later layers; the core identities here make the linearization
residual explicit.
-/

namespace StatInference

/-- Scalar ratio estimator `numerator / denominator`. -/
noncomputable def ratioEstimate (numerator denominator : ℝ) : ℝ :=
  numerator / denominator

/-- Residual obtained after centering a ratio numerator at `target`. -/
def ratioResidual (numerator denominator target : ℝ) : ℝ :=
  numerator - target * denominator

/-- A Hajek/IPW-style sequence of weighted numerators and normalizing masses. -/
structure RatioEstimatorSequence where
  numerator : ℕ -> ℝ
  denominator : ℕ -> ℝ

namespace RatioEstimatorSequence

/-- The sample-size-indexed ratio/Hajek estimate. -/
noncomputable def estimate (seq : RatioEstimatorSequence) (n : ℕ) : ℝ :=
  ratioEstimate (seq.numerator n) (seq.denominator n)

/-- The centered numerator residual for target `target`. -/
def residual (seq : RatioEstimatorSequence) (target : ℝ) (n : ℕ) : ℝ :=
  ratioResidual (seq.numerator n) (seq.denominator n) target

end RatioEstimatorSequence

/--
Basic ratio linearization identity: ratio error equals the centered numerator
residual divided by the denominator.
-/
theorem ratio_sub_target_eq_residual_div
    (numerator denominator target : ℝ) (hden : denominator ≠ 0) :
    ratioEstimate numerator denominator - target =
      ratioResidual numerator denominator target / denominator := by
  unfold ratioEstimate ratioResidual
  field_simp [hden]

/-- Exact target recovery when the centered ratio residual is zero. -/
theorem ratioEstimate_eq_target_of_residual_eq_zero
    (numerator denominator target : ℝ)
    (hden : denominator ≠ 0)
    (hres : ratioResidual numerator denominator target = 0) :
    ratioEstimate numerator denominator = target := by
  have h :=
    ratio_sub_target_eq_residual_div numerator denominator target hden
  have hdiff : ratioEstimate numerator denominator - target = 0 := by
    simpa [hres] using h
  linarith

/-- Sequence-level ratio error identity. -/
theorem ratio_sequence_sub_target_eq_residual_div
    (seq : RatioEstimatorSequence) (target : ℝ)
    (hden : ∀ n, seq.denominator n ≠ 0) :
    ∀ n,
      seq.estimate n - target =
        seq.residual target n / seq.denominator n := by
  intro n
  exact ratio_sub_target_eq_residual_div
    (seq.numerator n) (seq.denominator n) target (hden n)

/-- Scaled sequence-level ratio error identity, used for asymptotic rates. -/
theorem scaled_ratio_sequence_sub_target_eq_residual_div
    (seq : RatioEstimatorSequence) (target : ℝ) (rate : ℕ -> ℝ)
    (hden : ∀ n, seq.denominator n ≠ 0) :
    ∀ n,
      rate n * (seq.estimate n - target) =
        rate n * seq.residual target n / seq.denominator n := by
  intro n
  rw [ratio_sequence_sub_target_eq_residual_div seq target hden n]
  ring

/-- A named alias for the Hajek/IPW ratio estimate. -/
noncomputable def hajekRatio (weightedOutcome weightedMass : ℕ -> ℝ) (n : ℕ) : ℝ :=
  ratioEstimate (weightedOutcome n) (weightedMass n)

/-- The centered numerator residual for a Hajek/IPW ratio. -/
def hajekResidual
    (weightedOutcome weightedMass : ℕ -> ℝ) (target : ℝ) (n : ℕ) : ℝ :=
  ratioResidual (weightedOutcome n) (weightedMass n) target

/-- Hajek/IPW ratio error identity. -/
theorem hajekRatio_sub_target_eq_residual_div
    (weightedOutcome weightedMass : ℕ -> ℝ) (target : ℝ)
    (hmass : ∀ n, weightedMass n ≠ 0) :
    ∀ n,
      hajekRatio weightedOutcome weightedMass n - target =
        hajekResidual weightedOutcome weightedMass target n / weightedMass n := by
  intro n
  exact ratio_sub_target_eq_residual_div
    (weightedOutcome n) (weightedMass n) target (hmass n)

/-- Scaled Hajek/IPW ratio error identity. -/
theorem scaled_hajekRatio_sub_target_eq_residual_div
    (weightedOutcome weightedMass : ℕ -> ℝ) (target : ℝ) (rate : ℕ -> ℝ)
    (hmass : ∀ n, weightedMass n ≠ 0) :
    ∀ n,
      rate n * (hajekRatio weightedOutcome weightedMass n - target) =
        rate n * hajekResidual weightedOutcome weightedMass target n / weightedMass n := by
  intro n
  rw [hajekRatio_sub_target_eq_residual_div weightedOutcome weightedMass target hmass n]
  ring

end StatInference
