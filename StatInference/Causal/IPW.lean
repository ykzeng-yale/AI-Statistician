import StatInference.Causal.ATE
import StatInference.Estimator.Ratio

/-!
# IPW and Hajek ratio linearization

This module connects the causal IPW identification interface to the deterministic
ratio algebra.  The objects here are still finite-sample and deterministic:
probabilistic convergence assumptions are supplied by later asymptotic modules.
-/

namespace StatInference

/--
Proof-carrying certificate that an IPW identification bridge is usable with
verified causal assumptions, correct propensity weights, and finite-weight
moments.
-/
structure VerifiedIPWIdentification where
  bridge : IPWIdentificationBridge
  consistency : VerifiedConsistency
  overlap : VerifiedOverlap
  unconfoundedness : VerifiedUnconfoundedness
  propensity_correct : VerifiedByLean bridge.propensity_correct
  finite_weight_moments : VerifiedByLean bridge.finite_weight_moments
  consistency_matches : consistency.assumption = bridge.consistency
  overlap_matches : overlap.assumption = bridge.overlap
  unconfoundedness_matches : unconfoundedness.assumption = bridge.unconfoundedness

namespace VerifiedIPWIdentification

/-- Extract the verified IPW identification conclusion. -/
theorem identifies (certificate : VerifiedIPWIdentification) :
    certificate.bridge.ipw_identifies_estimand := by
  exact ipw_identification_of_bridge certificate.bridge
    (by
      simpa [certificate.consistency_matches] using
        certificate.consistency.proof)
    (by
      simpa [certificate.overlap_matches] using
        certificate.overlap.proof)
    (by
      simpa [certificate.unconfoundedness_matches] using
        certificate.unconfoundedness.proof)
    certificate.propensity_correct
    certificate.finite_weight_moments

end VerifiedIPWIdentification

/-- Sample-size-indexed IPW/Hajek ratio sequence with an explicit target. -/
structure IPWHajekEstimatorSequence where
  weightedOutcome : ℕ -> ℝ
  weightedMass : ℕ -> ℝ
  target : ℝ

namespace IPWHajekEstimatorSequence

/-- The IPW/Hajek ratio estimate. -/
noncomputable def estimate (seq : IPWHajekEstimatorSequence) (n : ℕ) : ℝ :=
  hajekRatio seq.weightedOutcome seq.weightedMass n

/-- Centered numerator residual against the sequence target. -/
def residual (seq : IPWHajekEstimatorSequence) (n : ℕ) : ℝ :=
  hajekResidual seq.weightedOutcome seq.weightedMass seq.target n

/-- View the IPW/Hajek sequence as the generic deterministic ratio sequence. -/
def toRatioEstimatorSequence (seq : IPWHajekEstimatorSequence) :
    RatioEstimatorSequence where
  numerator := seq.weightedOutcome
  denominator := seq.weightedMass

/-- The IPW/Hajek estimate agrees with the generic ratio-sequence estimate. -/
theorem estimate_eq_ratioEstimate (seq : IPWHajekEstimatorSequence) (n : ℕ) :
    seq.estimate n = seq.toRatioEstimatorSequence.estimate n :=
  rfl

/-- The IPW/Hajek residual agrees with the generic ratio-sequence residual. -/
theorem residual_eq_ratioResidual (seq : IPWHajekEstimatorSequence) (n : ℕ) :
    seq.residual n = seq.toRatioEstimatorSequence.residual seq.target n :=
  rfl

/-- Exact one-step IPW/Hajek ratio-error identity. -/
theorem sub_target_eq_residual_div
    (seq : IPWHajekEstimatorSequence)
    (hmass : ∀ n, seq.weightedMass n ≠ 0) :
    ∀ n,
      seq.estimate n - seq.target =
        seq.residual n / seq.weightedMass n := by
  intro n
  exact hajekRatio_sub_target_eq_residual_div
    seq.weightedOutcome seq.weightedMass seq.target hmass n

/-- Scaled IPW/Hajek ratio-error identity for asymptotic-rate handoff. -/
theorem scaled_sub_target_eq_residual_div
    (seq : IPWHajekEstimatorSequence) (rate : ℕ -> ℝ)
    (hmass : ∀ n, seq.weightedMass n ≠ 0) :
    ∀ n,
      rate n * (seq.estimate n - seq.target) =
        rate n * seq.residual n / seq.weightedMass n := by
  intro n
  exact scaled_hajekRatio_sub_target_eq_residual_div
    seq.weightedOutcome seq.weightedMass seq.target rate hmass n

end IPWHajekEstimatorSequence

/--
Route object combining a proof-carrying IPW identification certificate with the
finite-sample Hajek ratio linearization needed by later asymptotic arguments.
-/
structure IPWHajekLinearizationRoute where
  sequence : IPWHajekEstimatorSequence
  rate : ℕ -> ℝ
  denominator_nonzero : ∀ n, sequence.weightedMass n ≠ 0
  identification : VerifiedIPWIdentification

namespace IPWHajekLinearizationRoute

/-- The causal identification conclusion carried by the route. -/
theorem identifies (route : IPWHajekLinearizationRoute) :
    route.identification.bridge.ipw_identifies_estimand :=
  route.identification.identifies

/-- The route's unscaled deterministic IPW/Hajek linearization identity. -/
theorem linearization (route : IPWHajekLinearizationRoute) :
    ∀ n,
      route.sequence.estimate n - route.sequence.target =
        route.sequence.residual n / route.sequence.weightedMass n :=
  route.sequence.sub_target_eq_residual_div route.denominator_nonzero

/-- The route's scaled deterministic IPW/Hajek linearization identity. -/
theorem scaledLinearization (route : IPWHajekLinearizationRoute) :
    ∀ n,
      route.rate n * (route.sequence.estimate n - route.sequence.target) =
        route.rate n * route.sequence.residual n /
          route.sequence.weightedMass n :=
  route.sequence.scaled_sub_target_eq_residual_div
    route.rate route.denominator_nonzero

end IPWHajekLinearizationRoute

/--
Promotion target for the theorem-hole benchmark: a single reusable constructor
bundles IPW identification with the scaled Hajek linearization handoff.
-/
theorem ipw_hajek_linearization_constructor
    (route : IPWHajekLinearizationRoute) :
    route.identification.bridge.ipw_identifies_estimand ∧
      (∀ n,
        route.rate n * (route.sequence.estimate n - route.sequence.target) =
          route.rate n * route.sequence.residual n /
            route.sequence.weightedMass n) := by
  constructor
  · exact route.identifies
  · exact route.scaledLinearization

/-- Trivial consistency assumption used only for non-vacuity sanity examples. -/
def trivialIPWConsistencyAssumption : ConsistencyAssumption where
  statement := True

/-- Trivial overlap assumption used only for non-vacuity sanity examples. -/
def trivialIPWOverlapAssumption : OverlapAssumption where
  statement := True

/-- Trivial unconfoundedness assumption used only for non-vacuity sanity examples. -/
def trivialIPWUnconfoundednessAssumption : UnconfoundednessAssumption where
  statement := True

/--
Trivial IPW bridge used as a concrete inhabitant of the API.  It is not a
statistical identification theorem; it prevents the interface from becoming
vacuous while measure-theoretic bridges are added later.
-/
def trivialIPWIdentificationBridge : IPWIdentificationBridge where
  consistency := trivialIPWConsistencyAssumption
  overlap := trivialIPWOverlapAssumption
  unconfoundedness := trivialIPWUnconfoundednessAssumption
  propensity_correct := True
  finite_weight_moments := True
  ipw_identifies_estimand := True
  bridge := fun _hconsistency _hoverlap _hunconf _hpropensity _hmoments =>
    trivial

/-- Verified trivial IPW identification certificate for sanity examples. -/
def verifiedTrivialIPWIdentification : VerifiedIPWIdentification where
  bridge := trivialIPWIdentificationBridge
  consistency := { assumption := trivialIPWConsistencyAssumption, proof := trivial }
  overlap := { assumption := trivialIPWOverlapAssumption, proof := trivial }
  unconfoundedness :=
    { assumption := trivialIPWUnconfoundednessAssumption, proof := trivial }
  propensity_correct := trivial
  finite_weight_moments := trivial
  consistency_matches := rfl
  overlap_matches := rfl
  unconfoundedness_matches := rfl

/-- Constant one-mass IPW/Hajek sequence used as a non-vacuity witness. -/
def constantIPWHajekSequence (target : ℝ) : IPWHajekEstimatorSequence where
  weightedOutcome := fun _ => target
  weightedMass := fun _ => 1
  target := target

/-- The constant sanity sequence estimates its target exactly. -/
theorem constantIPWHajekSequence_estimate_eq_target (target : ℝ) (n : ℕ) :
    (constantIPWHajekSequence target).estimate n = target := by
  simp [constantIPWHajekSequence, IPWHajekEstimatorSequence.estimate,
    hajekRatio, ratioEstimate]

/-- The constant sanity sequence has zero centered residual. -/
theorem constantIPWHajekSequence_residual_eq_zero (target : ℝ) (n : ℕ) :
    (constantIPWHajekSequence target).residual n = 0 := by
  simp [constantIPWHajekSequence, IPWHajekEstimatorSequence.residual,
    hajekResidual, ratioResidual]

/-- Concrete non-vacuity route for the IPW/Hajek linearization API. -/
def constantIPWHajekLinearizationRoute
    (target : ℝ) (rate : ℕ -> ℝ) : IPWHajekLinearizationRoute where
  sequence := constantIPWHajekSequence target
  rate := rate
  denominator_nonzero := by
    intro _n
    exact one_ne_zero
  identification := verifiedTrivialIPWIdentification

/-- The concrete sanity route satisfies the scaled linearization identity. -/
theorem constantIPWHajekLinearizationRoute_scaled
    (target : ℝ) (rate : ℕ -> ℝ) :
    ∀ n,
      (constantIPWHajekLinearizationRoute target rate).rate n *
        ((constantIPWHajekLinearizationRoute target rate).sequence.estimate n -
          (constantIPWHajekLinearizationRoute target rate).sequence.target) =
        (constantIPWHajekLinearizationRoute target rate).rate n *
          (constantIPWHajekLinearizationRoute target rate).sequence.residual n /
            (constantIPWHajekLinearizationRoute target rate).sequence.weightedMass n :=
  (constantIPWHajekLinearizationRoute target rate).scaledLinearization

end StatInference
