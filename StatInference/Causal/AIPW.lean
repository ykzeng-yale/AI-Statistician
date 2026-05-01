import StatInference.Causal.IPW
import StatInference.Asymptotics.Op

/-!
# AIPW orthogonality and product-rate bridges

This module builds the proof-carrying AIPW layer needed before asymptotic
normality.  It separates three obligations:

* double-robust identification from causal assumptions,
* Neyman orthogonality of the score,
* product-rate control of the nuisance-induced second-order remainder.

Concrete probability and empirical-process rates can instantiate these
interfaces later without changing downstream theorem statements.
-/

namespace StatInference

/--
Proof-carrying certificate that an AIPW double-robust bridge identifies the
estimand under verified causal assumptions, regularity, and at least one
correct nuisance route.
-/
structure VerifiedAIPWDoubleRobustIdentification where
  bridge : AIPWDoubleRobustBridge
  consistency : VerifiedConsistency
  overlap : VerifiedOverlap
  unconfoundedness : VerifiedUnconfoundedness
  regularity : VerifiedByLean bridge.regularity
  model_correct :
    VerifiedByLean (bridge.propensity_correct ∨ bridge.outcome_regression_correct)
  consistency_matches : consistency.assumption = bridge.consistency
  overlap_matches : overlap.assumption = bridge.overlap
  unconfoundedness_matches : unconfoundedness.assumption = bridge.unconfoundedness

namespace VerifiedAIPWDoubleRobustIdentification

/-- Extract the verified AIPW double-robust identification conclusion. -/
theorem identifies (certificate : VerifiedAIPWDoubleRobustIdentification) :
    certificate.bridge.aipw_identifies_estimand := by
  exact aipw_identification_of_double_robust_bridge certificate.bridge
    (by
      simpa [certificate.consistency_matches] using
        certificate.consistency.proof)
    (by
      simpa [certificate.overlap_matches] using
        certificate.overlap.proof)
    (by
      simpa [certificate.unconfoundedness_matches] using
        certificate.unconfoundedness.proof)
    certificate.model_correct
    certificate.regularity

end VerifiedAIPWDoubleRobustIdentification

/--
Product-rate interface for AIPW nuisance errors.  The proposition
`product_rate_statement` can later be instantiated by concrete norm/rate
inequalities, while `product_remainder_small` is the small-o handoff used by
asymptotic linearity.
-/
structure AIPWNuisanceProductRate where
  propensity_error_small : SmallOInProbabilitySpec
  outcome_error_small : SmallOInProbabilitySpec
  product_rate_statement : Prop
  product_remainder_small : SmallOInProbabilitySpec
  product_rule :
    propensity_error_small.statement ->
    outcome_error_small.statement ->
    product_rate_statement ->
    product_remainder_small.statement

/-- Proof-carrying product-rate certificate. -/
structure VerifiedAIPWNuisanceProductRate where
  product_rate : AIPWNuisanceProductRate
  propensity_error_verified :
    VerifiedByLean product_rate.propensity_error_small.statement
  outcome_error_verified :
    VerifiedByLean product_rate.outcome_error_small.statement
  product_rate_verified :
    VerifiedByLean product_rate.product_rate_statement

namespace VerifiedAIPWNuisanceProductRate

/-- Extract the verified small-o second-order product remainder. -/
theorem remainderSmall (certificate : VerifiedAIPWNuisanceProductRate) :
    certificate.product_rate.product_remainder_small.statement :=
  certificate.product_rate.product_rule
    certificate.propensity_error_verified
    certificate.outcome_error_verified
    certificate.product_rate_verified

end VerifiedAIPWNuisanceProductRate

/--
Route combining AIPW identification, score orthogonality, and a product-rate
certificate into the second-order remainder claim used by later asymptotic
normality routes.
-/
structure AIPWOrthogonalProductRateRoute
    (Observation Propensity Regression ScoreValue Parameter : Type*) where
  score : AIPWScoreSpec Observation Propensity Regression ScoreValue Parameter
  identification : VerifiedAIPWDoubleRobustIdentification
  orthogonality : VerifiedNeymanOrthogonality
  nuisance_product_rate : VerifiedAIPWNuisanceProductRate
  score_verified : VerifiedByLean score.score_statement
  score_orthogonal_matches :
    orthogonality.spec.orthogonality_statement ->
    score.orthogonal_score_statement
  second_order_remainder : SmallOInProbabilitySpec
  remainder_bridge :
    score.score_statement ->
    score.orthogonal_score_statement ->
    nuisance_product_rate.product_rate.product_remainder_small.statement ->
    second_order_remainder.statement

namespace AIPWOrthogonalProductRateRoute

/-- The route carries a verified AIPW identification conclusion. -/
theorem identifies
    {Observation Propensity Regression ScoreValue Parameter : Type*}
    (route :
      AIPWOrthogonalProductRateRoute
        Observation Propensity Regression ScoreValue Parameter) :
    route.identification.bridge.aipw_identifies_estimand :=
  route.identification.identifies

/-- The route exposes the score's orthogonality statement. -/
theorem orthogonalScore
    {Observation Propensity Regression ScoreValue Parameter : Type*}
    (route :
      AIPWOrthogonalProductRateRoute
        Observation Propensity Regression ScoreValue Parameter) :
    route.score.orthogonal_score_statement :=
  route.score_orthogonal_matches route.orthogonality.orthogonality_verified

/-- The route exposes the product-rate small-o remainder statement. -/
theorem productRemainderSmall
    {Observation Propensity Regression ScoreValue Parameter : Type*}
    (route :
      AIPWOrthogonalProductRateRoute
        Observation Propensity Regression ScoreValue Parameter) :
    route.nuisance_product_rate.product_rate.product_remainder_small.statement :=
  route.nuisance_product_rate.remainderSmall

/-- Orthogonality plus product-rate control imply the second-order remainder claim. -/
theorem secondOrderRemainderSmall
    {Observation Propensity Regression ScoreValue Parameter : Type*}
    (route :
      AIPWOrthogonalProductRateRoute
        Observation Propensity Regression ScoreValue Parameter) :
    route.second_order_remainder.statement :=
  route.remainder_bridge
    route.score_verified
    route.orthogonalScore
    route.productRemainderSmall

end AIPWOrthogonalProductRateRoute

/-- Trivial AIPW double-robust bridge used only for non-vacuity sanity tests. -/
def trivialAIPWDoubleRobustBridge : AIPWDoubleRobustBridge where
  consistency := trivialIPWConsistencyAssumption
  overlap := trivialIPWOverlapAssumption
  unconfoundedness := trivialIPWUnconfoundednessAssumption
  propensity_correct := True
  outcome_regression_correct := True
  regularity := True
  aipw_identifies_estimand := True
  bridge_of_propensity :=
    fun _hconsistency _hoverlap _hunconf _hpropensity _hregularity =>
      trivial
  bridge_of_outcome_regression :=
    fun _hconsistency _hoverlap _hunconf _houtcome _hregularity =>
      trivial

/-- Verified trivial AIPW double-robust identification certificate. -/
def verifiedTrivialAIPWDoubleRobustIdentification :
    VerifiedAIPWDoubleRobustIdentification where
  bridge := trivialAIPWDoubleRobustBridge
  consistency := { assumption := trivialIPWConsistencyAssumption, proof := trivial }
  overlap := { assumption := trivialIPWOverlapAssumption, proof := trivial }
  unconfoundedness :=
    { assumption := trivialIPWUnconfoundednessAssumption, proof := trivial }
  regularity := trivial
  model_correct := Or.inl trivial
  consistency_matches := rfl
  overlap_matches := rfl
  unconfoundedness_matches := rfl

/-- Trivial product-rate object used only for non-vacuity sanity tests. -/
def trivialAIPWNuisanceProductRate : AIPWNuisanceProductRate where
  propensity_error_small := { statement := True }
  outcome_error_small := { statement := True }
  product_rate_statement := True
  product_remainder_small := { statement := True }
  product_rule := fun _hpropensity _houtcome _hproduct => trivial

/-- Verified trivial product-rate certificate. -/
def verifiedTrivialAIPWNuisanceProductRate :
    VerifiedAIPWNuisanceProductRate where
  product_rate := trivialAIPWNuisanceProductRate
  propensity_error_verified := trivial
  outcome_error_verified := trivial
  product_rate_verified := trivial

/-- Trivial AIPW score used only for non-vacuity sanity tests. -/
def trivialAIPWScoreSpec :
    AIPWScoreSpec Unit Unit Unit Unit Unit where
  target := ()
  propensity := fun _ => ()
  outcome_regression0 := fun _ => ()
  outcome_regression1 := fun _ => ()
  score := fun _ => ()
  score_statement := True
  orthogonal_score_statement := True

/-- Trivial verified Neyman orthogonality used only for non-vacuity sanity tests. -/
def verifiedTrivialAIPWOrthogonality : VerifiedNeymanOrthogonality where
  spec :=
    { score_statement := True
      nuisance_perturbation_statement := True
      orthogonality_statement := True }
  score_verified := trivial
  nuisance_perturbation_verified := trivial
  orthogonality_verified := trivial

/-- Concrete non-vacuity route for the AIPW orthogonal product-rate API. -/
def trivialAIPWOrthogonalProductRateRoute :
    AIPWOrthogonalProductRateRoute Unit Unit Unit Unit Unit where
  score := trivialAIPWScoreSpec
  identification := verifiedTrivialAIPWDoubleRobustIdentification
  orthogonality := verifiedTrivialAIPWOrthogonality
  nuisance_product_rate := verifiedTrivialAIPWNuisanceProductRate
  score_verified := trivial
  score_orthogonal_matches := fun _hortho => trivial
  second_order_remainder := { statement := True }
  remainder_bridge := fun _hscore _hortho _hremainder => trivial

/-- The concrete AIPW sanity route has a checked second-order remainder claim. -/
theorem trivialAIPWOrthogonalProductRateRoute_secondOrderRemainderSmall :
    trivialAIPWOrthogonalProductRateRoute.second_order_remainder.statement :=
  trivialAIPWOrthogonalProductRateRoute.secondOrderRemainderSmall

end StatInference
