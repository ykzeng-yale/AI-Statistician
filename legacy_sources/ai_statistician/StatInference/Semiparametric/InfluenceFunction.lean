import StatInference.Estimator.AsymptoticLinear

/-!
# Semiparametric inference seed interfaces
-/

namespace StatInference

structure InfluenceFunctionSpec (Model Parameter Observation : Type*) where
  model : Model
  parameter : Parameter
  influence : Observation -> Parameter
  mean_zero : Prop
  pathwise_derivative : Prop

structure NeymanOrthogonalitySpec where
  score_statement : Prop
  nuisance_perturbation_statement : Prop
  orthogonality_statement : Prop

end StatInference

