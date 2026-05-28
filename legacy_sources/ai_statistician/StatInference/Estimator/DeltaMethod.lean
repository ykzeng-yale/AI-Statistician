import StatInference.Estimator.Basic
import StatInference.Asymptotics.Convergence

/-!
# Delta-method estimator transformations

This module lifts the generic delta-method bridge to estimator transformations.
It keeps the analytic content explicit: concrete developments must supply the
estimator-transform relation, the first-order linearization, convergence of the
linear part, and negligibility of the remainder.
-/

namespace StatInference

universe u v w x y

/-- A deterministic transformation of a parameter or target space. -/
structure ParameterTransformation (Parameter : Type v) (Transformed : Type w) where
  transform : Parameter -> Transformed

/--
Proof-carrying delta-method route for a transformed estimator.

The route states that a transformed estimator is related to a base estimator,
that this relation has a first-order linearization, and that the usual
delta-method convergence conclusion follows from the linear-part convergence
and negligible remainder.
-/
structure DeltaMethodEstimatorRoute
    (Sample : ℕ -> Type u) (Parameter : Type v) (Transformed : Type w)
    (LinearPart : Type x) (Remainder : Type y) where
  base_estimator : IndexedEstimator Sample Parameter
  transformation : ParameterTransformation Parameter Transformed
  transformed_estimator : IndexedEstimator Sample Transformed
  target : Parameter
  transformed_target : Transformed
  estimator_transformation_statement : Prop
  first_order_linearization : Prop
  linear_part : ∀ n, Sample n -> LinearPart
  remainder : ∀ n, Sample n -> Remainder
  linear_part_convergence : ConvergenceInDistributionSpec
  remainder_small : SmallOInProbabilitySpec
  transformed_convergence : Prop
  certify_linearization :
    estimator_transformation_statement ->
    first_order_linearization
  bridge :
    first_order_linearization ->
    linear_part_convergence.statement ->
    remainder_small.statement ->
    transformed_convergence

namespace DeltaMethodEstimatorRoute

/-- Certify the first-order linearization from the estimator-transform relation. -/
theorem linearization
    {Sample : ℕ -> Type u} {Parameter : Type v} {Transformed : Type w}
    {LinearPart : Type x} {Remainder : Type y}
    (route :
      DeltaMethodEstimatorRoute Sample Parameter Transformed LinearPart Remainder)
    (h_transform : route.estimator_transformation_statement) :
    route.first_order_linearization :=
  route.certify_linearization h_transform

/-- Expose the estimator route as the generic delta-method bridge. -/
def toDeltaMethodBridge
    {Sample : ℕ -> Type u} {Parameter : Type v} {Transformed : Type w}
    {LinearPart : Type x} {Remainder : Type y}
    (route :
      DeltaMethodEstimatorRoute Sample Parameter Transformed LinearPart Remainder) :
    DeltaMethodBridge where
  linearization_statement := route.first_order_linearization
  linear_part_convergence := route.linear_part_convergence
  remainder_small := route.remainder_small
  transformed_convergence := route.transformed_convergence
  bridge := route.bridge

/--
Estimator-level delta method: transformation relation, linear-part convergence,
and negligible remainder imply transformed-estimator convergence.
-/
theorem transformedConvergence
    {Sample : ℕ -> Type u} {Parameter : Type v} {Transformed : Type w}
    {LinearPart : Type x} {Remainder : Type y}
    (route :
      DeltaMethodEstimatorRoute Sample Parameter Transformed LinearPart Remainder)
    (h_transform : route.estimator_transformation_statement)
    (h_linear_convergence : route.linear_part_convergence.statement)
    (h_remainder : route.remainder_small.statement) :
    route.transformed_convergence :=
  convergence_of_delta_method_bridge route.toDeltaMethodBridge
    (route.linearization h_transform)
    h_linear_convergence
    h_remainder

end DeltaMethodEstimatorRoute

end StatInference
