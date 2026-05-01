import StatInference.Asymptotics.Basic

/-!
# Estimator interfaces
-/

namespace StatInference

/-- A finite-sample estimator from samples to parameters. -/
structure Estimator (Sample Parameter : Type*) where
  estimate : Sample -> Parameter

/-- A sequence of estimators indexed by sample size. -/
structure EstimatorSequence (Sample Parameter : Type*) where
  estimate : ℕ -> Sample -> Parameter

/-- A target parameter functional. -/
structure TargetParameter (Model Parameter : Type*) where
  value : Model -> Parameter

end StatInference

