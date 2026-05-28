import StatInference.Estimator.AsymptoticLinear
import StatInference.Asymptotics.Convergence

/-!
# Asymptotic linearity plus CLT route

This module makes the standard statistical inference handoff explicit:
an estimator expansion, a negligible remainder, and a CLT for the linear part
are sufficient to expose the estimator's asymptotic-normality statement.
-/

namespace StatInference

universe u v w x y

/--
Proof-carrying route from an indexed asymptotically linear estimator to
asymptotic normality.  The fields separate the estimator expansion obligations
from the CLT and the final Slutsky/normality bridge.
-/
structure IndexedAsymptoticLinearCLTRoute
    (Sample : ℕ -> Type u) (Parameter : Type v) (InfluenceFunction : Type w)
    (LinearPart : Type x) (Remainder : Type y) where
  estimator :
    IndexedAsymptoticLinearEstimator Sample Parameter InfluenceFunction
      LinearPart Remainder
  clt : CentralLimitTheoremSpec
  asymptotic_normality : Prop
  normality_bridge :
    estimator.asymptotic_linear_statement ->
    clt.statement ->
    estimator.remainder_negligible.statement ->
    asymptotic_normality

namespace IndexedAsymptoticLinearCLTRoute

/-- Extract the asymptotic-linearity statement from the expansion obligations. -/
theorem asymptoticLinear
    {Sample : ℕ -> Type u} {Parameter : Type v} {InfluenceFunction : Type w}
    {LinearPart : Type x} {Remainder : Type y}
    (route :
      IndexedAsymptoticLinearCLTRoute Sample Parameter InfluenceFunction
        LinearPart Remainder)
    (h_match : route.estimator.estimator_matches_expansion)
    (h_expansion : route.estimator.expansion.expansion_statement)
    (h_remainder : route.estimator.remainder_negligible.statement) :
    route.estimator.asymptotic_linear_statement :=
  indexed_asymptotic_linear_of_marker route.estimator
    h_match h_expansion h_remainder

/--
Main P3 handoff theorem: estimator expansion + negligible remainder + CLT imply
the asymptotic-normality statement recorded by the route.
-/
theorem asymptoticNormal
    {Sample : ℕ -> Type u} {Parameter : Type v} {InfluenceFunction : Type w}
    {LinearPart : Type x} {Remainder : Type y}
    (route :
      IndexedAsymptoticLinearCLTRoute Sample Parameter InfluenceFunction
        LinearPart Remainder)
    (h_match : route.estimator.estimator_matches_expansion)
    (h_expansion : route.estimator.expansion.expansion_statement)
    (h_remainder : route.estimator.remainder_negligible.statement)
    (h_clt : route.clt.statement) :
    route.asymptotic_normality :=
  route.normality_bridge
    (route.asymptoticLinear h_match h_expansion h_remainder)
    h_clt
    h_remainder

/--
Expose a route as the generic `AsymptoticLinearCLTBridge`, retaining the same
asymptotic-linearity, CLT, remainder, and normality propositions.
-/
def toAsymptoticLinearCLTBridge
    {Sample : ℕ -> Type u} {Parameter : Type v} {InfluenceFunction : Type w}
    {LinearPart : Type x} {Remainder : Type y}
    (route :
      IndexedAsymptoticLinearCLTRoute Sample Parameter InfluenceFunction
        LinearPart Remainder) :
    AsymptoticLinearCLTBridge where
  asymptotic_linear_statement := route.estimator.asymptotic_linear_statement
  clt := route.clt
  negligible_remainder := route.estimator.remainder_negligible
  asymptotic_normality := route.asymptotic_normality
  bridge := route.normality_bridge

/-- Apply the generic bridge generated from an explicit route. -/
theorem asymptoticNormal_via_bridge
    {Sample : ℕ -> Type u} {Parameter : Type v} {InfluenceFunction : Type w}
    {LinearPart : Type x} {Remainder : Type y}
    (route :
      IndexedAsymptoticLinearCLTRoute Sample Parameter InfluenceFunction
        LinearPart Remainder)
    (h_asymptotic_linear : route.estimator.asymptotic_linear_statement)
    (h_clt : route.clt.statement)
    (h_remainder : route.estimator.remainder_negligible.statement) :
    route.asymptotic_normality :=
  asymptotic_normality_of_asymptoticLinear_clt_bridge
    route.toAsymptoticLinearCLTBridge
    h_asymptotic_linear
    h_clt
    h_remainder

end IndexedAsymptoticLinearCLTRoute

end StatInference
