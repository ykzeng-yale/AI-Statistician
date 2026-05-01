import StatInference.Estimator.AsymptoticLinear

/-!
# Semiparametric inference interfaces

The records in this file are intentionally abstract: they provide verified
interfaces for later mathlib-backed definitions of pathwise derivatives,
tangent spaces, estimating equations, and influence functions. Bridge records
carry the proof obligations connecting primitive assumptions to the statistical
claim they expose.
-/

namespace StatInference

/-- A target functional and candidate influence function at a model. -/
structure InfluenceFunctionSpec (Model Parameter Observation : Type*) where
  model : Model
  parameter : Parameter
  influence : Observation -> Parameter
  mean_zero : Prop
  pathwise_derivative : Prop

/-- A proof-carrying influence-function certificate. -/
structure VerifiedInfluenceFunction (Model Parameter Observation : Type*) where
  spec : InfluenceFunctionSpec Model Parameter Observation
  mean_zero_verified : VerifiedByLean spec.mean_zero
  pathwise_derivative_verified : VerifiedByLean spec.pathwise_derivative

theorem mean_zero_of_verified_influence_function
    {Model Parameter Observation : Type*}
    (v : VerifiedInfluenceFunction Model Parameter Observation) :
    v.spec.mean_zero :=
  v.mean_zero_verified

theorem pathwise_derivative_of_verified_influence_function
    {Model Parameter Observation : Type*}
    (v : VerifiedInfluenceFunction Model Parameter Observation) :
    v.spec.pathwise_derivative :=
  v.pathwise_derivative_verified

/--
Abstract bridge from mean-zero and pathwise-derivative obligations to a
verified influence-function certificate.
-/
structure InfluenceFunctionVerificationBridge
    (Model Parameter Observation : Type*) where
  spec : InfluenceFunctionSpec Model Parameter Observation
  bridge :
    spec.mean_zero ->
    spec.pathwise_derivative ->
    VerifiedInfluenceFunction Model Parameter Observation

def verified_influence_function_of_bridge
    {Model Parameter Observation : Type*}
    (b : InfluenceFunctionVerificationBridge Model Parameter Observation)
    (hmean : b.spec.mean_zero)
    (hderiv : b.spec.pathwise_derivative) :
    VerifiedInfluenceFunction Model Parameter Observation :=
  b.bridge hmean hderiv

/-- Generic semiparametric score interface for estimating equations. -/
structure EstimatingEquationSpec (Observation Parameter Moment : Type*) where
  target : Parameter
  moment : Parameter -> Observation -> Moment
  moment_condition : Prop
  differentiability : Prop
  nonsingularity : Prop

/--
A bridge from an estimating equation and regularity conditions to an influence
function specification. Concrete Z-estimation developments should instantiate
this record with actual derivatives and inverse-information operators.
-/
structure EstimatingEquationInfluenceBridge
    (Model Observation Parameter Moment : Type*) where
  equation : EstimatingEquationSpec Observation Parameter Moment
  influence : InfluenceFunctionSpec Model Parameter Observation
  regularity : Prop
  bridge :
    equation.moment_condition ->
    equation.differentiability ->
    equation.nonsingularity ->
    regularity ->
    influence.mean_zero ->
    influence.pathwise_derivative

theorem pathwise_derivative_of_estimating_equation_bridge
    {Model Observation Parameter Moment : Type*}
    (b : EstimatingEquationInfluenceBridge Model Observation Parameter Moment)
    (hmoment : b.equation.moment_condition)
    (hdiff : b.equation.differentiability)
    (hnonsing : b.equation.nonsingularity)
    (hreg : b.regularity)
    (hmean : b.influence.mean_zero) :
    b.influence.pathwise_derivative :=
  b.bridge hmoment hdiff hnonsing hreg hmean

/-- Abstract Neyman-orthogonality obligations for a score and nuisance path. -/
structure NeymanOrthogonalitySpec where
  score_statement : Prop
  nuisance_perturbation_statement : Prop
  orthogonality_statement : Prop

/-- Proof-carrying Neyman-orthogonality certificate. -/
structure VerifiedNeymanOrthogonality where
  spec : NeymanOrthogonalitySpec
  score_verified : VerifiedByLean spec.score_statement
  nuisance_perturbation_verified :
    VerifiedByLean spec.nuisance_perturbation_statement
  orthogonality_verified : VerifiedByLean spec.orthogonality_statement

/--
Bridge from score validity, nuisance perturbation validity, and a zero Gateaux
derivative statement to Neyman orthogonality.
-/
structure NeymanOrthogonalityBridge where
  spec : NeymanOrthogonalitySpec
  derivative_vanishes : Prop
  bridge :
    spec.score_statement ->
    spec.nuisance_perturbation_statement ->
    derivative_vanishes ->
    spec.orthogonality_statement

theorem neyman_orthogonality_of_bridge (b : NeymanOrthogonalityBridge)
    (hscore : b.spec.score_statement)
    (hnuisance : b.spec.nuisance_perturbation_statement)
    (hderiv : b.derivative_vanishes) :
    b.spec.orthogonality_statement :=
  b.bridge hscore hnuisance hderiv

def verified_neyman_orthogonality_of_bridge
    (b : NeymanOrthogonalityBridge)
    (hscore : VerifiedByLean b.spec.score_statement)
    (hnuisance : VerifiedByLean b.spec.nuisance_perturbation_statement)
    (hderiv : b.derivative_vanishes) :
    VerifiedNeymanOrthogonality where
  spec := b.spec
  score_verified := hscore
  nuisance_perturbation_verified := hnuisance
  orthogonality_verified := b.bridge hscore hnuisance hderiv

/--
Bridge from a verified influence function to an asymptotic-linear estimator
interface. This keeps the probabilistic CLT/remainder obligations outside this
file while making the interface between IF calculations and estimator theory
explicit.
-/
structure InfluenceFunctionAsymptoticLinearBridge
    (Model Parameter Observation EstimatorObj : Type*) where
  verified_if : VerifiedInfluenceFunction Model Parameter Observation
  estimator :
    AsymptoticLinearEstimator EstimatorObj (Observation -> Parameter)
  estimator_targets_parameter : Prop
  regularity : Prop
  bridge :
    verified_if.spec.mean_zero ->
    verified_if.spec.pathwise_derivative ->
    estimator_targets_parameter ->
    regularity ->
    estimator.statement

theorem asymptotic_linear_of_influence_function_bridge
    {Model Parameter Observation EstimatorObj : Type*}
    (b :
      InfluenceFunctionAsymptoticLinearBridge
        Model Parameter Observation EstimatorObj)
    (htarget : b.estimator_targets_parameter)
    (hreg : b.regularity) :
    b.estimator.statement :=
  b.bridge
    b.verified_if.mean_zero_verified
    b.verified_if.pathwise_derivative_verified
    htarget
    hreg

/-- Efficiency-facing bridge for canonical-gradient calculations. -/
structure EfficientInfluenceFunctionBridge
    (Model Parameter Observation : Type*) where
  verified_if : VerifiedInfluenceFunction Model Parameter Observation
  tangent_space_membership : Prop
  nuisance_orthogonality : Prop
  efficiency_bound_statement : Prop
  bridge :
    verified_if.spec.mean_zero ->
    verified_if.spec.pathwise_derivative ->
    tangent_space_membership ->
    nuisance_orthogonality ->
    efficiency_bound_statement

theorem efficiency_bound_of_influence_function_bridge
    {Model Parameter Observation : Type*}
    (b : EfficientInfluenceFunctionBridge Model Parameter Observation)
    (htangent : b.tangent_space_membership)
    (hnuisance : b.nuisance_orthogonality) :
    b.efficiency_bound_statement :=
  b.bridge
    b.verified_if.mean_zero_verified
    b.verified_if.pathwise_derivative_verified
    htangent
    hnuisance

end StatInference
