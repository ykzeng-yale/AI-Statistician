import StatInference.Estimator.ZEstimator
import StatInference.Estimator.Normality

/-!
# Z-estimator linearization route

This module records the standard Z-estimator path as explicit proof data:
estimating-equation evidence plus a differentiability/linearization argument
certify the estimator expansion, which then feeds the generic asymptotic
linearity plus CLT route.
-/

namespace StatInference

universe u v w x y z

/--
Proof-carrying bridge from a Z-estimator to an asymptotically linear estimator.

The mathematical content is deliberately explicit: concrete developments must
provide the differentiability/Taylor statement, the estimating-equation
statement, and the moment-linearization statement used to certify that the
Z-estimator matches its influence expansion.
-/
structure ZEstimatorLinearizationBridge
    (Sample : ℕ -> Type u) (Parameter : Type v) (Moment : Type w)
    (InfluenceFunction : Type x) (LinearPart : Type y) (Remainder : Type z) where
  z_estimator : ZEstimator Sample Parameter Moment
  target : Parameter
  influence_function : InfluenceFunction
  expansion : IndexedInfluenceExpansion Sample Parameter LinearPart Remainder
  differentiability_statement : Prop
  estimating_equation_statement : Prop
  moment_linearization_statement : Prop
  estimator_matches_expansion : Prop
  remainder_negligible : SmallOInProbabilitySpec
  asymptotic_linear_statement : Prop
  certify_estimator_matches_expansion :
    differentiability_statement ->
    estimating_equation_statement ->
    moment_linearization_statement ->
    estimator_matches_expansion
  certify_asymptotic_linear :
    estimator_matches_expansion ->
    expansion.expansion_statement ->
    remainder_negligible.statement ->
    asymptotic_linear_statement

namespace ZEstimatorLinearizationBridge

/-- View the Z-linearization bridge as the generic indexed asymptotic-linear marker. -/
def toIndexedAsymptoticLinearEstimator
    {Sample : ℕ -> Type u} {Parameter : Type v} {Moment : Type w}
    {InfluenceFunction : Type x} {LinearPart : Type y} {Remainder : Type z}
    (bridge :
      ZEstimatorLinearizationBridge Sample Parameter Moment InfluenceFunction
        LinearPart Remainder) :
    IndexedAsymptoticLinearEstimator Sample Parameter InfluenceFunction
      LinearPart Remainder where
  estimator := bridge.z_estimator.estimator
  target := bridge.target
  influence_function := bridge.influence_function
  expansion := bridge.expansion
  estimator_matches_expansion := bridge.estimator_matches_expansion
  remainder_negligible := bridge.remainder_negligible
  asymptotic_linear_statement := bridge.asymptotic_linear_statement
  certify_asymptotic_linear := bridge.certify_asymptotic_linear

/-- Certify that differentiability and estimating-equation evidence imply the expansion match. -/
theorem estimatorMatchesExpansion
    {Sample : ℕ -> Type u} {Parameter : Type v} {Moment : Type w}
    {InfluenceFunction : Type x} {LinearPart : Type y} {Remainder : Type z}
    (bridge :
      ZEstimatorLinearizationBridge Sample Parameter Moment InfluenceFunction
        LinearPart Remainder)
    (h_differentiability : bridge.differentiability_statement)
    (h_estimating_equation : bridge.estimating_equation_statement)
    (h_moment_linearization : bridge.moment_linearization_statement) :
    bridge.estimator_matches_expansion :=
  bridge.certify_estimator_matches_expansion
    h_differentiability h_estimating_equation h_moment_linearization

/--
The core P3.M2 theorem: differentiability/estimating-equation evidence plus
the expansion and negligible remainder certify asymptotic linearity.
-/
theorem asymptoticLinear
    {Sample : ℕ -> Type u} {Parameter : Type v} {Moment : Type w}
    {InfluenceFunction : Type x} {LinearPart : Type y} {Remainder : Type z}
    (bridge :
      ZEstimatorLinearizationBridge Sample Parameter Moment InfluenceFunction
        LinearPart Remainder)
    (h_differentiability : bridge.differentiability_statement)
    (h_estimating_equation : bridge.estimating_equation_statement)
    (h_moment_linearization : bridge.moment_linearization_statement)
    (h_expansion : bridge.expansion.expansion_statement)
    (h_remainder : bridge.remainder_negligible.statement) :
    bridge.asymptotic_linear_statement :=
  indexed_asymptotic_linear_of_marker
    bridge.toIndexedAsymptoticLinearEstimator
    (bridge.estimatorMatchesExpansion h_differentiability
      h_estimating_equation h_moment_linearization)
    h_expansion
    h_remainder

end ZEstimatorLinearizationBridge

/--
Full Z-estimator route to asymptotic normality: the linearization bridge plus a
CLT and the final negligible-remainder normality bridge.
-/
structure ZEstimatorAsymptoticNormalRoute
    (Sample : ℕ -> Type u) (Parameter : Type v) (Moment : Type w)
    (InfluenceFunction : Type x) (LinearPart : Type y) (Remainder : Type z) where
  linearization :
    ZEstimatorLinearizationBridge Sample Parameter Moment InfluenceFunction
      LinearPart Remainder
  clt : CentralLimitTheoremSpec
  asymptotic_normality : Prop
  normality_bridge :
    linearization.asymptotic_linear_statement ->
    clt.statement ->
    linearization.remainder_negligible.statement ->
    asymptotic_normality

namespace ZEstimatorAsymptoticNormalRoute

/-- Project the Z-estimator route to the generic indexed asymptotic-normality route. -/
def toIndexedAsymptoticLinearCLTRoute
    {Sample : ℕ -> Type u} {Parameter : Type v} {Moment : Type w}
    {InfluenceFunction : Type x} {LinearPart : Type y} {Remainder : Type z}
    (route :
      ZEstimatorAsymptoticNormalRoute Sample Parameter Moment InfluenceFunction
        LinearPart Remainder) :
    IndexedAsymptoticLinearCLTRoute Sample Parameter InfluenceFunction
      LinearPart Remainder where
  estimator := route.linearization.toIndexedAsymptoticLinearEstimator
  clt := route.clt
  asymptotic_normality := route.asymptotic_normality
  normality_bridge := route.normality_bridge

/--
Apply the full Z-estimator theorem: differentiability, estimating equation,
moment linearization, expansion, negligible remainder, and CLT imply the
route's asymptotic-normality statement.
-/
theorem asymptoticNormal
    {Sample : ℕ -> Type u} {Parameter : Type v} {Moment : Type w}
    {InfluenceFunction : Type x} {LinearPart : Type y} {Remainder : Type z}
    (route :
      ZEstimatorAsymptoticNormalRoute Sample Parameter Moment InfluenceFunction
        LinearPart Remainder)
    (h_differentiability : route.linearization.differentiability_statement)
    (h_estimating_equation : route.linearization.estimating_equation_statement)
    (h_moment_linearization : route.linearization.moment_linearization_statement)
    (h_expansion : route.linearization.expansion.expansion_statement)
    (h_remainder : route.linearization.remainder_negligible.statement)
    (h_clt : route.clt.statement) :
    route.asymptotic_normality :=
  IndexedAsymptoticLinearCLTRoute.asymptoticNormal
    route.toIndexedAsymptoticLinearCLTRoute
    (route.linearization.estimatorMatchesExpansion h_differentiability
      h_estimating_equation h_moment_linearization)
    h_expansion
    h_remainder
    h_clt

end ZEstimatorAsymptoticNormalRoute

end StatInference
