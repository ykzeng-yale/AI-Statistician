import StatInference.Semiparametric.InfluenceFunction

/-!
# Causal inference interfaces

This file keeps causal inference statements abstract while making the bridge
obligations explicit. The structures separate potential-outcome objects,
identification assumptions, IPW/AIPW scores, and influence-function handoff
claims without adding trusted constants or assuming the final theorem as a
premise.
-/

namespace StatInference

/-- Binary potential outcomes with covariates. -/
structure PotentialOutcomeModel (Unit Outcome Covariate : Type*) where
  y0 : Unit -> Outcome
  y1 : Unit -> Outcome
  x : Unit -> Covariate

/-- Observed-data wrapper around a potential-outcome model. -/
structure ObservedPotentialOutcomeModel
    (Unit Outcome Covariate : Type*) where
  potential : PotentialOutcomeModel Unit Outcome Covariate
  treatment : Unit -> Bool
  observedOutcome : Unit -> Outcome
  consistency : Prop

/-- A causal estimand associated with a potential-outcome model. -/
structure PotentialOutcomeEstimand
    (Model Parameter : Type*) where
  model : Model
  value : Parameter
  definition_statement : Prop

/-- Abstract consistency assumption connecting observed and potential outcomes. -/
structure ConsistencyAssumption where
  statement : Prop

/-- Positivity/common-support requirement for treatment assignment. -/
structure OverlapAssumption where
  statement : Prop

/-- Conditional exchangeability/no-unmeasured-confounding requirement. -/
structure UnconfoundednessAssumption where
  statement : Prop

/-- Proof-carrying consistency certificate. -/
structure VerifiedConsistency where
  assumption : ConsistencyAssumption
  proof : VerifiedByLean assumption.statement

/-- Proof-carrying overlap certificate. -/
structure VerifiedOverlap where
  assumption : OverlapAssumption
  proof : VerifiedByLean assumption.statement

/-- Proof-carrying unconfoundedness certificate. -/
structure VerifiedUnconfoundedness where
  assumption : UnconfoundednessAssumption
  proof : VerifiedByLean assumption.statement

/-- Propensity-score interface for binary treatment. -/
structure PropensityScoreSpec
    (Unit Covariate Propensity : Type*) where
  treatment : Unit -> Bool
  covariate : Unit -> Covariate
  propensity : Covariate -> Propensity
  propensity_statement : Prop

/-- Outcome-regression interface for the two potential-outcome regressions. -/
structure OutcomeRegressionSpec
    (Unit Outcome Covariate Regression : Type*) where
  potential : PotentialOutcomeModel Unit Outcome Covariate
  regression0 : Covariate -> Regression
  regression1 : Covariate -> Regression
  regression_statement : Prop

/-- Bridge from primitive positivity/support obligations to overlap. -/
structure OverlapBridge where
  positivity_statement : Prop
  common_support_statement : Prop
  overlap : OverlapAssumption
  bridge :
    positivity_statement ->
    common_support_statement ->
    overlap.statement

theorem overlap_of_bridge (b : OverlapBridge)
    (hpos : b.positivity_statement)
    (hsupport : b.common_support_statement) :
    b.overlap.statement :=
  b.bridge hpos hsupport

def verified_overlap_of_bridge (b : OverlapBridge)
    (hpos : b.positivity_statement)
    (hsupport : b.common_support_statement) :
    VerifiedOverlap where
  assumption := b.overlap
  proof := b.bridge hpos hsupport

/-- Bridge from conditional-exchangeability obligations to unconfoundedness. -/
structure UnconfoundednessBridge where
  exchangeability_y0 : Prop
  exchangeability_y1 : Prop
  conditioned_on_covariates : Prop
  unconfoundedness : UnconfoundednessAssumption
  bridge :
    exchangeability_y0 ->
    exchangeability_y1 ->
    conditioned_on_covariates ->
    unconfoundedness.statement

theorem unconfoundedness_of_bridge (b : UnconfoundednessBridge)
    (hy0 : b.exchangeability_y0)
    (hy1 : b.exchangeability_y1)
    (hx : b.conditioned_on_covariates) :
    b.unconfoundedness.statement :=
  b.bridge hy0 hy1 hx

def verified_unconfoundedness_of_bridge (b : UnconfoundednessBridge)
    (hy0 : b.exchangeability_y0)
    (hy1 : b.exchangeability_y1)
    (hx : b.conditioned_on_covariates) :
    VerifiedUnconfoundedness where
  assumption := b.unconfoundedness
  proof := b.bridge hy0 hy1 hx

/--
Legacy ATE identification bridge. It is kept as a thin abstract interface:
instances must provide the proof that overlap plus unconfoundedness identify
the estimand.
-/
structure ATEIdentificationBridge where
  overlap : OverlapAssumption
  unconfoundedness : UnconfoundednessAssumption
  identification : Prop
  prove_identification :
    overlap.statement -> unconfoundedness.statement -> identification

theorem ate_identification_of_bridge (b : ATEIdentificationBridge)
    (hoverlap : b.overlap.statement)
    (hunconf : b.unconfoundedness.statement) :
    b.identification :=
  b.prove_identification hoverlap hunconf

/--
ATE identification bridge with consistency kept as an explicit observed-data
premise.
-/
structure ObservedATEIdentificationBridge where
  consistency : ConsistencyAssumption
  overlap : OverlapAssumption
  unconfoundedness : UnconfoundednessAssumption
  identification : Prop
  bridge :
    consistency.statement ->
    overlap.statement ->
    unconfoundedness.statement ->
    identification

theorem observed_ate_identification_of_bridge
    (b : ObservedATEIdentificationBridge)
    (hconsistency : b.consistency.statement)
    (hoverlap : b.overlap.statement)
    (hunconf : b.unconfoundedness.statement) :
    b.identification :=
  b.bridge hconsistency hoverlap hunconf

theorem observed_ate_identification_of_verified_bridge
    (b : ObservedATEIdentificationBridge)
    (hconsistency : VerifiedConsistency)
    (hoverlap : VerifiedOverlap)
    (hunconf : VerifiedUnconfoundedness)
    (hc_same : hconsistency.assumption = b.consistency)
    (ho_same : hoverlap.assumption = b.overlap)
    (hu_same : hunconf.assumption = b.unconfoundedness) :
    b.identification := by
  exact b.bridge
    (by simpa [hc_same] using hconsistency.proof)
    (by simpa [ho_same] using hoverlap.proof)
    (by simpa [hu_same] using hunconf.proof)

/-- Abstract IPW score interface. -/
structure IPWScoreSpec
    (Observation Weight ScoreValue Parameter : Type*) where
  target : Parameter
  treatment_weight : Observation -> Weight
  control_weight : Observation -> Weight
  score : Observation -> ScoreValue
  score_statement : Prop
  finite_moment_statement : Prop

/-- Bridge from causal assumptions and correct propensity weights to IPW. -/
structure IPWIdentificationBridge where
  consistency : ConsistencyAssumption
  overlap : OverlapAssumption
  unconfoundedness : UnconfoundednessAssumption
  propensity_correct : Prop
  finite_weight_moments : Prop
  ipw_identifies_estimand : Prop
  bridge :
    consistency.statement ->
    overlap.statement ->
    unconfoundedness.statement ->
    propensity_correct ->
    finite_weight_moments ->
    ipw_identifies_estimand

theorem ipw_identification_of_bridge (b : IPWIdentificationBridge)
    (hconsistency : b.consistency.statement)
    (hoverlap : b.overlap.statement)
    (hunconf : b.unconfoundedness.statement)
    (hpropensity : b.propensity_correct)
    (hmoments : b.finite_weight_moments) :
    b.ipw_identifies_estimand :=
  b.bridge hconsistency hoverlap hunconf hpropensity hmoments

/-- Abstract AIPW score interface with propensity and outcome nuisance parts. -/
structure AIPWScoreSpec
    (Observation Propensity Regression ScoreValue Parameter : Type*) where
  target : Parameter
  propensity : Observation -> Propensity
  outcome_regression0 : Observation -> Regression
  outcome_regression1 : Observation -> Regression
  score : Observation -> ScoreValue
  score_statement : Prop
  orthogonal_score_statement : Prop

/--
Double-robust bridge for AIPW identification: under the shared causal
assumptions and regularity, either a correct propensity score or correct
outcome regressions identify the same target.
-/
structure AIPWDoubleRobustBridge where
  consistency : ConsistencyAssumption
  overlap : OverlapAssumption
  unconfoundedness : UnconfoundednessAssumption
  propensity_correct : Prop
  outcome_regression_correct : Prop
  regularity : Prop
  aipw_identifies_estimand : Prop
  bridge_of_propensity :
    consistency.statement ->
    overlap.statement ->
    unconfoundedness.statement ->
    propensity_correct ->
    regularity ->
    aipw_identifies_estimand
  bridge_of_outcome_regression :
    consistency.statement ->
    overlap.statement ->
    unconfoundedness.statement ->
    outcome_regression_correct ->
    regularity ->
    aipw_identifies_estimand

theorem aipw_identification_of_correct_propensity
    (b : AIPWDoubleRobustBridge)
    (hconsistency : b.consistency.statement)
    (hoverlap : b.overlap.statement)
    (hunconf : b.unconfoundedness.statement)
    (hpropensity : b.propensity_correct)
    (hreg : b.regularity) :
    b.aipw_identifies_estimand :=
  b.bridge_of_propensity hconsistency hoverlap hunconf hpropensity hreg

theorem aipw_identification_of_correct_outcome_regression
    (b : AIPWDoubleRobustBridge)
    (hconsistency : b.consistency.statement)
    (hoverlap : b.overlap.statement)
    (hunconf : b.unconfoundedness.statement)
    (houtcome : b.outcome_regression_correct)
    (hreg : b.regularity) :
    b.aipw_identifies_estimand :=
  b.bridge_of_outcome_regression hconsistency hoverlap hunconf houtcome hreg

theorem aipw_identification_of_double_robust_bridge
    (b : AIPWDoubleRobustBridge)
    (hconsistency : b.consistency.statement)
    (hoverlap : b.overlap.statement)
    (hunconf : b.unconfoundedness.statement)
    (hmodel : b.propensity_correct ∨ b.outcome_regression_correct)
    (hreg : b.regularity) :
    b.aipw_identifies_estimand := by
  cases hmodel with
  | inl hpropensity =>
      exact b.bridge_of_propensity
        hconsistency hoverlap hunconf hpropensity hreg
  | inr houtcome =>
      exact b.bridge_of_outcome_regression
        hconsistency hoverlap hunconf houtcome hreg

/--
Bridge from an AIPW causal identification statement to a semiparametric
influence-function certificate.
-/
structure AIPWInfluenceFunctionBridge
    (Model Parameter Observation : Type*) where
  aipw_identification : Prop
  aipw_score_statement : Prop
  orthogonality : NeymanOrthogonalitySpec
  influence : InfluenceFunctionSpec Model Parameter Observation
  bridge :
    aipw_identification ->
    aipw_score_statement ->
    orthogonality.orthogonality_statement ->
    influence.mean_zero ->
    influence.pathwise_derivative ->
    VerifiedInfluenceFunction Model Parameter Observation

def verified_influence_function_of_aipw_bridge
    {Model Parameter Observation : Type*}
    (b : AIPWInfluenceFunctionBridge Model Parameter Observation)
    (hid : b.aipw_identification)
    (hscore : b.aipw_score_statement)
    (hortho : b.orthogonality.orthogonality_statement)
    (hmean : b.influence.mean_zero)
    (hderiv : b.influence.pathwise_derivative) :
    VerifiedInfluenceFunction Model Parameter Observation :=
  b.bridge hid hscore hortho hmean hderiv

end StatInference
