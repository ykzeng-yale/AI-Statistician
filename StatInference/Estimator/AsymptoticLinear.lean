import StatInference.Estimator.Basic
import StatInference.Asymptotics.AsymptoticNormal

/-!
# Asymptotic linearity interfaces
-/

namespace StatInference

structure InfluenceExpansion (Statistic LinearPart Remainder : Type*) where
  statistic : Statistic
  linear_part : LinearPart
  remainder : Remainder
  expansion_statement : Prop

structure AsymptoticLinearEstimator (EstimatorObj InfluenceFunction : Type*) where
  estimator : EstimatorObj
  influence_function : InfluenceFunction
  statement : Prop

end StatInference

