import StatInference.Causal.IPW

/-!
# Concrete estimator proof chain

This module gives a placeholder-free, paper-facing proof chain for a concrete
IPW/Hajek estimator route.  The route is intentionally deterministic: it
checks that the current library can compose identification, exact target
recovery, residual control, and scaled linearization into one verified
estimator-level theorem.
-/

namespace StatInference

/-- Unit-rate sequence used by the concrete IPW/Hajek proof-chain witness. -/
def paperQualityIPWHajekRate : ℕ -> ℝ :=
  fun _ => 1

/-- Concrete constant-mass IPW/Hajek route used for the P8 proof-chain demo. -/
def paperQualityIPWHajekRoute (target : ℝ) : IPWHajekLinearizationRoute :=
  constantIPWHajekLinearizationRoute target paperQualityIPWHajekRate

/--
Concrete placeholder-free proof chain for a constant IPW/Hajek estimator.

The theorem composes four reusable library facts:
causal IPW identification, exact target recovery, zero residual, and the
scaled deterministic linearization identity used by asymptotic arguments.
-/
theorem paperQualityIPWHajekConcreteEstimatorChain (target : ℝ) :
    (paperQualityIPWHajekRoute target).identification.bridge.ipw_identifies_estimand ∧
      (∀ n, (paperQualityIPWHajekRoute target).sequence.estimate n = target) ∧
      (∀ n, (paperQualityIPWHajekRoute target).sequence.residual n = 0) ∧
      (∀ n,
        (paperQualityIPWHajekRoute target).rate n *
            ((paperQualityIPWHajekRoute target).sequence.estimate n -
              (paperQualityIPWHajekRoute target).sequence.target) =
          (paperQualityIPWHajekRoute target).rate n *
            (paperQualityIPWHajekRoute target).sequence.residual n /
              (paperQualityIPWHajekRoute target).sequence.weightedMass n) := by
  constructor
  · exact (paperQualityIPWHajekRoute target).identifies
  constructor
  · intro n
    simpa [paperQualityIPWHajekRoute] using
      constantIPWHajekSequence_estimate_eq_target target n
  constructor
  · intro n
    simpa [paperQualityIPWHajekRoute] using
      constantIPWHajekSequence_residual_eq_zero target n
  · exact (paperQualityIPWHajekRoute target).scaledLinearization

end StatInference
