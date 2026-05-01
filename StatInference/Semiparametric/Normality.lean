import StatInference.Causal.AIPW
import StatInference.Estimator.Normality

/-!
# Influence-function asymptotic normality routes

This module connects semiparametric influence-function verification to the
generic estimator asymptotic-normality handoff.  The route is intentionally
proof-carrying: concrete developments must provide verified mean-zero,
pathwise-derivative, target, regularity, CLT, and negligible-remainder
obligations before obtaining asymptotic normality.
-/

namespace StatInference

/--
Generic semiparametric route from a verified influence function to an
asymptotic-normality statement.
-/
structure InfluenceFunctionNormalityRoute
    (Model Parameter Observation EstimatorObj : Type*) where
  influence_bridge :
    InfluenceFunctionAsymptoticLinearBridge
      Model Parameter Observation EstimatorObj
  estimator_targets_parameter :
    VerifiedByLean influence_bridge.estimator_targets_parameter
  regularity : VerifiedByLean influence_bridge.regularity
  clt : CentralLimitTheoremSpec
  negligible_remainder : SmallOInProbabilitySpec
  asymptotic_normality : Prop
  normality_bridge :
    influence_bridge.estimator.statement ->
    clt.statement ->
    negligible_remainder.statement ->
    asymptotic_normality

namespace InfluenceFunctionNormalityRoute

/-- Extract the asymptotic-linearity statement from the verified influence function. -/
theorem asymptoticLinear
    {Model Parameter Observation EstimatorObj : Type*}
    (route :
      InfluenceFunctionNormalityRoute
        Model Parameter Observation EstimatorObj) :
    route.influence_bridge.estimator.statement :=
  asymptotic_linear_of_influence_function_bridge
    route.influence_bridge
    route.estimator_targets_parameter
    route.regularity

/-- Expose the route as the generic asymptotic-linearity plus CLT bridge. -/
def toAsymptoticLinearCLTBridge
    {Model Parameter Observation EstimatorObj : Type*}
    (route :
      InfluenceFunctionNormalityRoute
        Model Parameter Observation EstimatorObj) :
    AsymptoticLinearCLTBridge where
  asymptotic_linear_statement := route.influence_bridge.estimator.statement
  clt := route.clt
  negligible_remainder := route.negligible_remainder
  asymptotic_normality := route.asymptotic_normality
  bridge := route.normality_bridge

/--
Main semiparametric handoff: verified influence function, target/regularity,
CLT, and negligible remainder imply asymptotic normality.
-/
theorem asymptoticNormal
    {Model Parameter Observation EstimatorObj : Type*}
    (route :
      InfluenceFunctionNormalityRoute
        Model Parameter Observation EstimatorObj)
    (h_clt : route.clt.statement)
    (h_remainder : route.negligible_remainder.statement) :
    route.asymptotic_normality :=
  asymptotic_normality_of_asymptoticLinear_clt_bridge
    route.toAsymptoticLinearCLTBridge
    route.asymptoticLinear
    h_clt
    h_remainder

end InfluenceFunctionNormalityRoute

/--
AIPW-specific influence-function route.  It first verifies an influence function
from the AIPW causal identification and orthogonality bridge, then hands the
verified influence function to the generic semiparametric normality route.
-/
structure AIPWInfluenceFunctionNormalityRoute
    (Model Parameter Observation EstimatorObj : Type*) where
  aipw_bridge : AIPWInfluenceFunctionBridge Model Parameter Observation
  aipw_identification : VerifiedByLean aipw_bridge.aipw_identification
  aipw_score : VerifiedByLean aipw_bridge.aipw_score_statement
  orthogonality :
    VerifiedByLean aipw_bridge.orthogonality.orthogonality_statement
  mean_zero : VerifiedByLean aipw_bridge.influence.mean_zero
  pathwise_derivative :
    VerifiedByLean aipw_bridge.influence.pathwise_derivative
  estimator :
    AsymptoticLinearEstimator EstimatorObj (Observation -> Parameter)
  estimator_targets_parameter : Prop
  regularity : Prop
  clt : CentralLimitTheoremSpec
  negligible_remainder : SmallOInProbabilitySpec
  asymptotic_normality : Prop
  estimator_bridge :
    aipw_bridge.influence.mean_zero ->
    aipw_bridge.influence.pathwise_derivative ->
    estimator_targets_parameter ->
    regularity ->
    estimator.statement
  estimator_targets_verified : VerifiedByLean estimator_targets_parameter
  regularity_verified : VerifiedByLean regularity
  normality_bridge :
    estimator.statement ->
    clt.statement ->
    negligible_remainder.statement ->
    asymptotic_normality

namespace AIPWInfluenceFunctionNormalityRoute

/-- Verify the AIPW influence-function certificate carried by the route. -/
def verifiedInfluenceFunction
    {Model Parameter Observation EstimatorObj : Type*}
    (route :
      AIPWInfluenceFunctionNormalityRoute
        Model Parameter Observation EstimatorObj) :
    VerifiedInfluenceFunction Model Parameter Observation :=
  verified_influence_function_of_aipw_bridge
    route.aipw_bridge
    route.aipw_identification
    route.aipw_score
    route.orthogonality
    route.mean_zero
    route.pathwise_derivative

/-- Convert an AIPW IF route to the generic influence-function normality route. -/
def toInfluenceFunctionNormalityRoute
    {Model Parameter Observation EstimatorObj : Type*}
    (route :
      AIPWInfluenceFunctionNormalityRoute
        Model Parameter Observation EstimatorObj) :
    InfluenceFunctionNormalityRoute Model Parameter Observation EstimatorObj where
  influence_bridge :=
    { verified_if := route.verifiedInfluenceFunction
      estimator := route.estimator
      estimator_targets_parameter := route.estimator_targets_parameter
      regularity := route.regularity
      bridge := fun _hmean _hderiv htarget hregularity =>
        route.estimator_bridge
          route.mean_zero
          route.pathwise_derivative
          htarget
          hregularity }
  estimator_targets_parameter := route.estimator_targets_verified
  regularity := route.regularity_verified
  clt := route.clt
  negligible_remainder := route.negligible_remainder
  asymptotic_normality := route.asymptotic_normality
  normality_bridge := route.normality_bridge

/-- The AIPW route exposes the estimator's asymptotic-linearity statement. -/
theorem asymptoticLinear
    {Model Parameter Observation EstimatorObj : Type*}
    (route :
      AIPWInfluenceFunctionNormalityRoute
        Model Parameter Observation EstimatorObj) :
    route.estimator.statement :=
  route.toInfluenceFunctionNormalityRoute.asymptoticLinear

/-- The full AIPW influence-function route implies asymptotic normality. -/
theorem asymptoticNormal
    {Model Parameter Observation EstimatorObj : Type*}
    (route :
      AIPWInfluenceFunctionNormalityRoute
        Model Parameter Observation EstimatorObj)
    (h_clt : route.clt.statement)
    (h_remainder : route.negligible_remainder.statement) :
    route.asymptotic_normality :=
  route.toInfluenceFunctionNormalityRoute.asymptoticNormal h_clt h_remainder

end AIPWInfluenceFunctionNormalityRoute

/-- Trivial influence-function specification used only as a non-vacuity witness. -/
def trivialInfluenceFunctionSpec :
    InfluenceFunctionSpec Unit Unit Unit where
  model := ()
  parameter := ()
  influence := fun _ => ()
  mean_zero := True
  pathwise_derivative := True

/-- Verified trivial influence function used only as a non-vacuity witness. -/
def verifiedTrivialInfluenceFunction :
    VerifiedInfluenceFunction Unit Unit Unit where
  spec := trivialInfluenceFunctionSpec
  mean_zero_verified := trivial
  pathwise_derivative_verified := trivial

/-- Trivial asymptotic-linear estimator used only as a non-vacuity witness. -/
def trivialAsymptoticLinearEstimator :
    AsymptoticLinearEstimator Unit (Unit -> Unit) where
  estimator := ()
  influence_function := fun _ => ()
  statement := True

/-- Trivial IF-to-asymptotic-linearity bridge used only for non-vacuity tests. -/
def trivialInfluenceFunctionAsymptoticLinearBridge :
    InfluenceFunctionAsymptoticLinearBridge Unit Unit Unit Unit where
  verified_if := verifiedTrivialInfluenceFunction
  estimator := trivialAsymptoticLinearEstimator
  estimator_targets_parameter := True
  regularity := True
  bridge := fun _hmean _hderiv _htarget _hregularity => trivial

/-- Concrete non-vacuity route for semiparametric IF normality. -/
def trivialInfluenceFunctionNormalityRoute :
    InfluenceFunctionNormalityRoute Unit Unit Unit Unit where
  influence_bridge := trivialInfluenceFunctionAsymptoticLinearBridge
  estimator_targets_parameter := trivial
  regularity := trivial
  clt := { statement := True }
  negligible_remainder := { statement := True }
  asymptotic_normality := True
  normality_bridge := fun _hal _hclt _hrem => trivial

/-- The concrete IF normality route has a checked asymptotic-normality conclusion. -/
theorem trivialInfluenceFunctionNormalityRoute_asymptoticNormal :
    trivialInfluenceFunctionNormalityRoute.asymptotic_normality :=
  trivialInfluenceFunctionNormalityRoute.asymptoticNormal trivial trivial

/-- Trivial AIPW influence-function bridge used only for non-vacuity tests. -/
def trivialAIPWInfluenceFunctionBridge :
    AIPWInfluenceFunctionBridge Unit Unit Unit where
  aipw_identification := True
  aipw_score_statement := True
  orthogonality := verifiedTrivialAIPWOrthogonality.spec
  influence := trivialInfluenceFunctionSpec
  bridge := fun _hid _hscore _hortho hmean hderiv =>
    { spec := trivialInfluenceFunctionSpec
      mean_zero_verified := hmean
      pathwise_derivative_verified := hderiv }

/-- Concrete non-vacuity route for AIPW IF asymptotic normality. -/
def trivialAIPWInfluenceFunctionNormalityRoute :
    AIPWInfluenceFunctionNormalityRoute Unit Unit Unit Unit where
  aipw_bridge := trivialAIPWInfluenceFunctionBridge
  aipw_identification := trivial
  aipw_score := trivial
  orthogonality := trivial
  mean_zero := trivial
  pathwise_derivative := trivial
  estimator := trivialAsymptoticLinearEstimator
  estimator_targets_parameter := True
  regularity := True
  clt := { statement := True }
  negligible_remainder := { statement := True }
  asymptotic_normality := True
  estimator_bridge := fun _hmean _hderiv _htarget _hregularity => trivial
  estimator_targets_verified := trivial
  regularity_verified := trivial
  normality_bridge := fun _hal _hclt _hrem => trivial

/-- The concrete AIPW IF route has a checked asymptotic-normality conclusion. -/
theorem trivialAIPWInfluenceFunctionNormalityRoute_asymptoticNormal :
    trivialAIPWInfluenceFunctionNormalityRoute.asymptotic_normality :=
  trivialAIPWInfluenceFunctionNormalityRoute.asymptoticNormal trivial trivial

end StatInference
