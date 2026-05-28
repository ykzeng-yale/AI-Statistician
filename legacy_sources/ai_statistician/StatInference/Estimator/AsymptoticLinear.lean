import StatInference.Estimator.Basic
import StatInference.Asymptotics.AsymptoticNormal

/-!
# Asymptotic linearity interfaces
-/

namespace StatInference

universe u v w x y

structure InfluenceExpansion (Statistic LinearPart Remainder : Type*) where
  statistic : Statistic
  linear_part : LinearPart
  remainder : Remainder
  expansion_statement : Prop

/--
A sample-size-indexed influence expansion.  The proposition fields are kept
abstract so concrete developments can choose the relevant algebra, topology,
and probability mode without changing this interface.
-/
structure IndexedInfluenceExpansion
    (Sample : ℕ -> Type u) (Statistic : Type v) (LinearPart : Type w)
    (Remainder : Type x) where
  statistic : ∀ n, Sample n -> Statistic
  linear_part : ∀ n, Sample n -> LinearPart
  remainder : ∀ n, Sample n -> Remainder
  expansion_statement : Prop

structure AsymptoticLinearEstimator (EstimatorObj InfluenceFunction : Type*) where
  estimator : EstimatorObj
  influence_function : InfluenceFunction
  statement : Prop

/--
Marker for an indexed estimator admitting an asymptotically linear expansion.
The actual expansion equation and negligibility claim remain explicit
propositions, while `certify_asymptotic_linear` records the intended bridge.
-/
structure IndexedAsymptoticLinearEstimator
    (Sample : ℕ -> Type u) (Parameter : Type v) (InfluenceFunction : Type w)
    (LinearPart : Type x) (Remainder : Type y) where
  estimator : IndexedEstimator Sample Parameter
  target : Parameter
  influence_function : InfluenceFunction
  expansion : IndexedInfluenceExpansion Sample Parameter LinearPart Remainder
  estimator_matches_expansion : Prop
  remainder_negligible : SmallOInProbabilitySpec
  asymptotic_linear_statement : Prop
  certify_asymptotic_linear :
    estimator_matches_expansion ->
    expansion.expansion_statement ->
    remainder_negligible.statement ->
    asymptotic_linear_statement

/-- Extract the verified asymptotic-linearity statement from the marker fields. -/
theorem indexed_asymptotic_linear_of_marker
    {Sample : ℕ -> Type u} {Parameter : Type v} {InfluenceFunction : Type w}
    {LinearPart : Type x} {Remainder : Type y}
    (marker :
      IndexedAsymptoticLinearEstimator Sample Parameter InfluenceFunction
        LinearPart Remainder)
    (h_match : marker.estimator_matches_expansion)
    (h_expansion : marker.expansion.expansion_statement)
    (h_remainder : marker.remainder_negligible.statement) :
    marker.asymptotic_linear_statement :=
  marker.certify_asymptotic_linear h_match h_expansion h_remainder

/--
Marker for the common route from asymptotic linearity to asymptotic normality:
an indexed asymptotically linear estimator, a CLT for the linear part, and a
Slutsky/negligible-remainder bridge.
-/
structure AsymptoticLinearNormalityMarker
    (Sample : ℕ -> Type u) (Parameter : Type v) (InfluenceFunction : Type w)
    (LinearPart : Type x) (Remainder : Type y) where
  asymptotic_linear :
    IndexedAsymptoticLinearEstimator Sample Parameter InfluenceFunction
      LinearPart Remainder
  clt_for_linear_part : Prop
  asymptotic_normality : Prop
  bridge :
    asymptotic_linear.asymptotic_linear_statement ->
    clt_for_linear_part ->
    asymptotic_normality

/-- Apply an asymptotic-linear normality marker. -/
theorem asymptotic_normality_of_asymptoticLinear_marker
    {Sample : ℕ -> Type u} {Parameter : Type v} {InfluenceFunction : Type w}
    {LinearPart : Type x} {Remainder : Type y}
    (marker :
      AsymptoticLinearNormalityMarker Sample Parameter InfluenceFunction
        LinearPart Remainder)
    (h_asymptotic_linear :
      marker.asymptotic_linear.asymptotic_linear_statement)
    (h_clt : marker.clt_for_linear_part) :
    marker.asymptotic_normality :=
  marker.bridge h_asymptotic_linear h_clt

end StatInference
