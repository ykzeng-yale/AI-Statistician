import StatInference.Matching.WDSM.AsymptoticInterfaces
import StatInference.Estimator.ZLinearization

/-!
# First-step score-estimator bridge for WDSM

The WDSM estimated-score route needs first-step asymptotic linearity for the
score estimators and a local-linearity statement for the estimated score map.
This module connects those WDSM assumptions to the generic `ZEstimator`
linearization interface.

The module does not prove model-specific M-estimation regularity.  Instead, it
turns differentiability, estimating-equation, moment-linearization, expansion,
and negligible-remainder evidence for each score estimator into explicit
component asymptotic-linearity statements.  Separate PATE and PATT assembly
bridges then combine the component statements into the WDSM first-step
assumptions.  The weighting choice for each component, such as survey-weighted
retrospective propensity estimation or unweighted prognostic estimation, remains
an explicit named design premise.
-/

namespace StatInference
namespace Matching
namespace WDSM

universe u v w x y z

/--
One first-step score component certified by a `ZEstimatorLinearizationBridge`.

The `weighting_design` field is the named place where the manuscript records
whether this component is fit with survey weights or without survey weights.
The component bridge may use that design premise together with the generic
Z-estimator asymptotic linearity statement.
-/
structure FirstStepScoreComponentZBridge
    (Sample : ℕ -> Type u) (Parameter : Type v) (Moment : Type w)
    (InfluenceFunction : Type x) (LinearPart : Type y)
    (Remainder : Type z) where
  linearization :
    ZEstimatorLinearizationBridge Sample Parameter Moment InfluenceFunction
      LinearPart Remainder
  weighting_design : Prop
  component_asymptotic_linearity : Prop
  component_bridge :
    linearization.asymptotic_linear_statement ->
    weighting_design ->
    component_asymptotic_linearity

/--
Certify one first-step component from generic Z-estimator linearization evidence
and the component's named weighting-design premise.
-/
theorem component_asymptotic_linearity_of_z_bridge
    {Sample : ℕ -> Type u} {Parameter : Type v} {Moment : Type w}
    {InfluenceFunction : Type x} {LinearPart : Type y} {Remainder : Type z}
    (b :
      FirstStepScoreComponentZBridge Sample Parameter Moment InfluenceFunction
        LinearPart Remainder)
    (h_differentiability : b.linearization.differentiability_statement)
    (h_estimating_equation : b.linearization.estimating_equation_statement)
    (h_moment_linearization : b.linearization.moment_linearization_statement)
    (h_expansion : b.linearization.expansion.expansion_statement)
    (h_remainder : b.linearization.remainder_negligible.statement)
    (h_weighting : b.weighting_design) :
    b.component_asymptotic_linearity :=
  b.component_bridge
    (ZEstimatorLinearizationBridge.asymptoticLinear b.linearization
      h_differentiability h_estimating_equation h_moment_linearization
      h_expansion h_remainder)
    h_weighting

/--
Concrete evidence package for one first-step score component.
-/
structure FirstStepScoreComponentZEvidence
    (Sample : ℕ -> Type u) (Parameter : Type v) (Moment : Type w)
    (InfluenceFunction : Type x) (LinearPart : Type y)
    (Remainder : Type z) where
  component :
    FirstStepScoreComponentZBridge Sample Parameter Moment InfluenceFunction
      LinearPart Remainder
  differentiability : component.linearization.differentiability_statement
  estimating_equation :
    component.linearization.estimating_equation_statement
  moment_linearization :
    component.linearization.moment_linearization_statement
  expansion : component.linearization.expansion.expansion_statement
  remainder : component.linearization.remainder_negligible.statement
  weighting : component.weighting_design

/--
Extract component asymptotic linearity from a bundled Z-estimator
linearization certificate.
-/
theorem component_asymptotic_linearity_of_z_evidence
    {Sample : ℕ -> Type u} {Parameter : Type v} {Moment : Type w}
    {InfluenceFunction : Type x} {LinearPart : Type y} {Remainder : Type z}
    (e :
      FirstStepScoreComponentZEvidence Sample Parameter Moment
        InfluenceFunction LinearPart Remainder) :
    e.component.component_asymptotic_linearity :=
  component_asymptotic_linearity_of_z_bridge e.component
    e.differentiability e.estimating_equation e.moment_linearization
    e.expansion e.remainder e.weighting

/--
Assembly interface for the PATE double-score first step.

The three component propositions correspond to propensity, treated-prognostic,
and control-prognostic score estimation.  Their weighting-design choices are
kept as separate fields so retrospective and prospective variants cannot reuse
the wrong weighting route silently.
-/
structure PATEDoubleScoreFirstStepAssembly where
  propensity_weighting_design : Prop
  treated_prognostic_weighting_design : Prop
  control_prognostic_weighting_design : Prop
  propensity_component_asymptotic_linearity : Prop
  treated_prognostic_component_asymptotic_linearity : Prop
  control_prognostic_component_asymptotic_linearity : Prop
  first_step_asymptotic_linearization : Prop
  score_estimator_local_asymptotic_linearity : Prop
  assemble_first_step :
    propensity_weighting_design ->
    treated_prognostic_weighting_design ->
    control_prognostic_weighting_design ->
    propensity_component_asymptotic_linearity ->
    treated_prognostic_component_asymptotic_linearity ->
    control_prognostic_component_asymptotic_linearity ->
    first_step_asymptotic_linearization
  assemble_score_local :
    propensity_weighting_design ->
    treated_prognostic_weighting_design ->
    control_prognostic_weighting_design ->
    propensity_component_asymptotic_linearity ->
    treated_prognostic_component_asymptotic_linearity ->
    control_prognostic_component_asymptotic_linearity ->
    score_estimator_local_asymptotic_linearity

/--
Assemble PATE first-step and score-local linearity from component
asymptotic-linearity statements and the named weighting-design premises.
-/
theorem pate_first_step_and_score_local_linearity_of_components
    (b : PATEDoubleScoreFirstStepAssembly)
    (h_prop_weight : b.propensity_weighting_design)
    (h_treated_weight : b.treated_prognostic_weighting_design)
    (h_control_weight : b.control_prognostic_weighting_design)
    (h_prop : b.propensity_component_asymptotic_linearity)
    (h_treated : b.treated_prognostic_component_asymptotic_linearity)
    (h_control : b.control_prognostic_component_asymptotic_linearity) :
    b.first_step_asymptotic_linearization ∧
      b.score_estimator_local_asymptotic_linearity :=
  ⟨b.assemble_first_step h_prop_weight h_treated_weight h_control_weight
      h_prop h_treated h_control,
    b.assemble_score_local h_prop_weight h_treated_weight h_control_weight
      h_prop h_treated h_control⟩

/-- PATE first-step asymptotic linearization from component evidence. -/
theorem pate_first_step_linearity_of_components
    (b : PATEDoubleScoreFirstStepAssembly)
    (h_prop_weight : b.propensity_weighting_design)
    (h_treated_weight : b.treated_prognostic_weighting_design)
    (h_control_weight : b.control_prognostic_weighting_design)
    (h_prop : b.propensity_component_asymptotic_linearity)
    (h_treated : b.treated_prognostic_component_asymptotic_linearity)
    (h_control : b.control_prognostic_component_asymptotic_linearity) :
    b.first_step_asymptotic_linearization :=
  (pate_first_step_and_score_local_linearity_of_components b h_prop_weight
    h_treated_weight h_control_weight h_prop h_treated h_control).1

/-- PATE score-estimator local asymptotic linearity from component evidence. -/
theorem pate_score_local_linearity_of_components
    (b : PATEDoubleScoreFirstStepAssembly)
    (h_prop_weight : b.propensity_weighting_design)
    (h_treated_weight : b.treated_prognostic_weighting_design)
    (h_control_weight : b.control_prognostic_weighting_design)
    (h_prop : b.propensity_component_asymptotic_linearity)
    (h_treated : b.treated_prognostic_component_asymptotic_linearity)
    (h_control : b.control_prognostic_component_asymptotic_linearity) :
    b.score_estimator_local_asymptotic_linearity :=
  (pate_first_step_and_score_local_linearity_of_components b h_prop_weight
    h_treated_weight h_control_weight h_prop h_treated h_control).2

/--
PATE first-step and score-local linearity directly from three component
Z-estimator certificates, plus the transfers that identify each component with
the PATE assembly fields.
-/
theorem pate_first_step_and_score_local_linearity_of_z_components
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {TSample : ℕ -> Type u} {TParameter : Type v} {TMoment : Type w}
    {TInfluenceFunction : Type x} {TLinearPart : Type y}
    {TRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b : PATEDoubleScoreFirstStepAssembly)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
    (treated :
      FirstStepScoreComponentZEvidence TSample TParameter TMoment
        TInfluenceFunction TLinearPart TRemainder)
    (control :
      FirstStepScoreComponentZEvidence CSample CParameter CMoment
        CInfluenceFunction CLinearPart CRemainder)
    (h_prop_weight :
      propensity.component.weighting_design ->
        b.propensity_weighting_design)
    (h_treated_weight :
      treated.component.weighting_design ->
        b.treated_prognostic_weighting_design)
    (h_control_weight :
      control.component.weighting_design ->
        b.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        b.propensity_component_asymptotic_linearity)
    (h_treated_component :
      treated.component.component_asymptotic_linearity ->
        b.treated_prognostic_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        b.control_prognostic_component_asymptotic_linearity) :
    b.first_step_asymptotic_linearization ∧
      b.score_estimator_local_asymptotic_linearity :=
  pate_first_step_and_score_local_linearity_of_components b
    (h_prop_weight propensity.weighting)
    (h_treated_weight treated.weighting)
    (h_control_weight control.weighting)
    (h_prop_component
      (component_asymptotic_linearity_of_z_evidence propensity))
    (h_treated_component
      (component_asymptotic_linearity_of_z_evidence treated))
    (h_control_component
      (component_asymptotic_linearity_of_z_evidence control))

/--
Assembly interface for the one-sided PATT double-score first step.

PATT uses the propensity score and the control-prognostic score in the
one-sided double score.
-/
structure PATTDoubleScoreFirstStepAssembly where
  propensity_weighting_design : Prop
  control_prognostic_weighting_design : Prop
  propensity_component_asymptotic_linearity : Prop
  control_prognostic_component_asymptotic_linearity : Prop
  first_step_asymptotic_linearization : Prop
  score_estimator_local_asymptotic_linearity : Prop
  assemble_first_step :
    propensity_weighting_design ->
    control_prognostic_weighting_design ->
    propensity_component_asymptotic_linearity ->
    control_prognostic_component_asymptotic_linearity ->
    first_step_asymptotic_linearization
  assemble_score_local :
    propensity_weighting_design ->
    control_prognostic_weighting_design ->
    propensity_component_asymptotic_linearity ->
    control_prognostic_component_asymptotic_linearity ->
    score_estimator_local_asymptotic_linearity

/--
Assemble PATT first-step and score-local linearity from component
asymptotic-linearity statements and the named weighting-design premises.
-/
theorem patt_first_step_and_score_local_linearity_of_components
    (b : PATTDoubleScoreFirstStepAssembly)
    (h_prop_weight : b.propensity_weighting_design)
    (h_control_weight : b.control_prognostic_weighting_design)
    (h_prop : b.propensity_component_asymptotic_linearity)
    (h_control : b.control_prognostic_component_asymptotic_linearity) :
    b.first_step_asymptotic_linearization ∧
      b.score_estimator_local_asymptotic_linearity :=
  ⟨b.assemble_first_step h_prop_weight h_control_weight h_prop h_control,
    b.assemble_score_local h_prop_weight h_control_weight h_prop h_control⟩

/-- PATT first-step asymptotic linearization from component evidence. -/
theorem patt_first_step_linearity_of_components
    (b : PATTDoubleScoreFirstStepAssembly)
    (h_prop_weight : b.propensity_weighting_design)
    (h_control_weight : b.control_prognostic_weighting_design)
    (h_prop : b.propensity_component_asymptotic_linearity)
    (h_control : b.control_prognostic_component_asymptotic_linearity) :
    b.first_step_asymptotic_linearization :=
  (patt_first_step_and_score_local_linearity_of_components b h_prop_weight
    h_control_weight h_prop h_control).1

/-- PATT score-estimator local asymptotic linearity from component evidence. -/
theorem patt_score_local_linearity_of_components
    (b : PATTDoubleScoreFirstStepAssembly)
    (h_prop_weight : b.propensity_weighting_design)
    (h_control_weight : b.control_prognostic_weighting_design)
    (h_prop : b.propensity_component_asymptotic_linearity)
    (h_control : b.control_prognostic_component_asymptotic_linearity) :
    b.score_estimator_local_asymptotic_linearity :=
  (patt_first_step_and_score_local_linearity_of_components b h_prop_weight
    h_control_weight h_prop h_control).2

/--
PATT first-step and score-local linearity directly from propensity and control
component Z-estimator certificates, plus the transfers that identify each
component with the PATT assembly fields.
-/
theorem patt_first_step_and_score_local_linearity_of_z_components
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (b : PATTDoubleScoreFirstStepAssembly)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
    (control :
      FirstStepScoreComponentZEvidence CSample CParameter CMoment
        CInfluenceFunction CLinearPart CRemainder)
    (h_prop_weight :
      propensity.component.weighting_design ->
        b.propensity_weighting_design)
    (h_control_weight :
      control.component.weighting_design ->
        b.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        b.propensity_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        b.control_prognostic_component_asymptotic_linearity) :
    b.first_step_asymptotic_linearization ∧
      b.score_estimator_local_asymptotic_linearity :=
  patt_first_step_and_score_local_linearity_of_components b
    (h_prop_weight propensity.weighting)
    (h_control_weight control.weighting)
    (h_prop_component
      (component_asymptotic_linearity_of_z_evidence propensity))
    (h_control_component
      (component_asymptotic_linearity_of_z_evidence control))

/--
Project PATE Z-estimator component evidence into the first-step and score-local
fields of an estimated-score local-experiment input.
-/
theorem estimated_score_local_experiment_input_first_step_and_score_local_of_pate_z_components
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {TSample : ℕ -> Type u} {TParameter : Type v} {TMoment : Type w}
    {TInfluenceFunction : Type x} {TLinearPart : Type y}
    {TRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (firstStep : PATEDoubleScoreFirstStepAssembly)
    (estimated : EstimatedScoreLocalExperimentInput)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
    (treated :
      FirstStepScoreComponentZEvidence TSample TParameter TMoment
        TInfluenceFunction TLinearPart TRemainder)
    (control :
      FirstStepScoreComponentZEvidence CSample CParameter CMoment
        CInfluenceFunction CLinearPart CRemainder)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        estimated.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        estimated.score_estimator_local_asymptotic_linearity)
    (h_prop_weight :
      propensity.component.weighting_design ->
        firstStep.propensity_weighting_design)
    (h_treated_weight :
      treated.component.weighting_design ->
        firstStep.treated_prognostic_weighting_design)
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_treated_component :
      treated.component.component_asymptotic_linearity ->
        firstStep.treated_prognostic_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity) :
    estimated.first_step_asymptotic_linearization ∧
      estimated.score_estimator_local_asymptotic_linearity := by
  have hfirst_score :
      firstStep.first_step_asymptotic_linearization ∧
        firstStep.score_estimator_local_asymptotic_linearity :=
    pate_first_step_and_score_local_linearity_of_z_components firstStep
      propensity treated control h_prop_weight h_treated_weight
      h_control_weight h_prop_component h_treated_component
      h_control_component
  exact ⟨hfirst_transfer hfirst_score.1,
    hscore_transfer hfirst_score.2⟩

/--
Project PATT Z-estimator component evidence into the first-step and score-local
fields of an estimated-score local-experiment input.
-/
theorem estimated_score_local_experiment_input_first_step_and_score_local_of_patt_z_components
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (firstStep : PATTDoubleScoreFirstStepAssembly)
    (estimated : EstimatedScoreLocalExperimentInput)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
    (control :
      FirstStepScoreComponentZEvidence CSample CParameter CMoment
        CInfluenceFunction CLinearPart CRemainder)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        estimated.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        estimated.score_estimator_local_asymptotic_linearity)
    (h_prop_weight :
      propensity.component.weighting_design ->
        firstStep.propensity_weighting_design)
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity) :
    estimated.first_step_asymptotic_linearization ∧
      estimated.score_estimator_local_asymptotic_linearity := by
  have hfirst_score :
      firstStep.first_step_asymptotic_linearization ∧
        firstStep.score_estimator_local_asymptotic_linearity :=
    patt_first_step_and_score_local_linearity_of_z_components firstStep
      propensity control h_prop_weight h_control_weight h_prop_component
      h_control_component
  exact ⟨hfirst_transfer hfirst_score.1,
    hscore_transfer hfirst_score.2⟩

/--
Project PATE Z-estimator component evidence into the first-step and score-local
fields of an estimated-score local-experiment variance input.
-/
theorem estimated_score_local_experiment_variance_input_first_step_and_score_local_of_pate_z_components
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {TSample : ℕ -> Type u} {TParameter : Type v} {TMoment : Type w}
    {TInfluenceFunction : Type x} {TLinearPart : Type y}
    {TRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (firstStep : PATEDoubleScoreFirstStepAssembly)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
    (treated :
      FirstStepScoreComponentZEvidence TSample TParameter TMoment
        TInfluenceFunction TLinearPart TRemainder)
    (control :
      FirstStepScoreComponentZEvidence CSample CParameter CMoment
        CInfluenceFunction CLinearPart CRemainder)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        estimated.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        estimated.score_estimator_local_asymptotic_linearity)
    (h_prop_weight :
      propensity.component.weighting_design ->
        firstStep.propensity_weighting_design)
    (h_treated_weight :
      treated.component.weighting_design ->
        firstStep.treated_prognostic_weighting_design)
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_treated_component :
      treated.component.component_asymptotic_linearity ->
        firstStep.treated_prognostic_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity) :
    estimated.first_step_asymptotic_linearization ∧
      estimated.score_estimator_local_asymptotic_linearity := by
  have hfirst_score :
      firstStep.first_step_asymptotic_linearization ∧
        firstStep.score_estimator_local_asymptotic_linearity :=
    pate_first_step_and_score_local_linearity_of_z_components firstStep
      propensity treated control h_prop_weight h_treated_weight
      h_control_weight h_prop_component h_treated_component
      h_control_component
  exact ⟨hfirst_transfer hfirst_score.1,
    hscore_transfer hfirst_score.2⟩

/--
Project PATT Z-estimator component evidence into the first-step and score-local
fields of an estimated-score local-experiment variance input.
-/
theorem estimated_score_local_experiment_variance_input_first_step_and_score_local_of_patt_z_components
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (firstStep : PATTDoubleScoreFirstStepAssembly)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
    (control :
      FirstStepScoreComponentZEvidence CSample CParameter CMoment
        CInfluenceFunction CLinearPart CRemainder)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        estimated.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        estimated.score_estimator_local_asymptotic_linearity)
    (h_prop_weight :
      propensity.component.weighting_design ->
        firstStep.propensity_weighting_design)
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity) :
    estimated.first_step_asymptotic_linearization ∧
      estimated.score_estimator_local_asymptotic_linearity := by
  have hfirst_score :
      firstStep.first_step_asymptotic_linearization ∧
        firstStep.score_estimator_local_asymptotic_linearity :=
    patt_first_step_and_score_local_linearity_of_z_components firstStep
      propensity control h_prop_weight h_control_weight h_prop_component
      h_control_component
  exact ⟨hfirst_transfer hfirst_score.1,
    hscore_transfer hfirst_score.2⟩

/--
PATE estimated-score asymptotic normality using first-step component
linearity assembled from the PATE double-score first-step interface.
-/
theorem estimated_score_asymptotic_normality_of_pate_first_step_components
    (firstStep : PATEDoubleScoreFirstStepAssembly)
    (estimated : EstimatedScoreLocalExperimentInput)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        estimated.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        estimated.score_estimator_local_asymptotic_linearity)
    (hknown : estimated.known_score_asymptotic_normality)
    (h_prop_weight : firstStep.propensity_weighting_design)
    (h_treated_weight : firstStep.treated_prognostic_weighting_design)
    (h_control_weight : firstStep.control_prognostic_weighting_design)
    (h_prop : firstStep.propensity_component_asymptotic_linearity)
    (h_treated :
      firstStep.treated_prognostic_component_asymptotic_linearity)
    (h_control :
      firstStep.control_prognostic_component_asymptotic_linearity)
    (hfunctional : estimated.matching_functional_local_derivative)
    (hequicontinuity : estimated.local_stochastic_equicontinuity)
    (hgodambe : estimated.godambe_variance_identity) :
    estimated.estimated_score_asymptotic_normality := by
  have hfirst_score :
      firstStep.first_step_asymptotic_linearization ∧
        firstStep.score_estimator_local_asymptotic_linearity :=
    pate_first_step_and_score_local_linearity_of_components firstStep
      h_prop_weight h_treated_weight h_control_weight h_prop h_treated
      h_control
  exact
    estimated_score_asymptotic_normality_of_local_experiment_input
      estimated hknown (hfirst_transfer hfirst_score.1)
      (hscore_transfer hfirst_score.2) hfunctional hequicontinuity
      hgodambe

/--
PATT estimated-score asymptotic normality using first-step component
linearity assembled from the PATT double-score first-step interface.
-/
theorem estimated_score_asymptotic_normality_of_patt_first_step_components
    (firstStep : PATTDoubleScoreFirstStepAssembly)
    (estimated : EstimatedScoreLocalExperimentInput)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        estimated.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        estimated.score_estimator_local_asymptotic_linearity)
    (hknown : estimated.known_score_asymptotic_normality)
    (h_prop_weight : firstStep.propensity_weighting_design)
    (h_control_weight : firstStep.control_prognostic_weighting_design)
    (h_prop : firstStep.propensity_component_asymptotic_linearity)
    (h_control :
      firstStep.control_prognostic_component_asymptotic_linearity)
    (hfunctional : estimated.matching_functional_local_derivative)
    (hequicontinuity : estimated.local_stochastic_equicontinuity)
    (hgodambe : estimated.godambe_variance_identity) :
    estimated.estimated_score_asymptotic_normality := by
  have hfirst_score :
      firstStep.first_step_asymptotic_linearization ∧
        firstStep.score_estimator_local_asymptotic_linearity :=
    patt_first_step_and_score_local_linearity_of_components firstStep
      h_prop_weight h_control_weight h_prop h_control
  exact
    estimated_score_asymptotic_normality_of_local_experiment_input
      estimated hknown (hfirst_transfer hfirst_score.1)
      (hscore_transfer hfirst_score.2) hfunctional hequicontinuity
      hgodambe

/--
PATE estimated-score asymptotic normality using first-step component
linearity, with the local-experiment/Godambe obligations packaged as a
compact core.
-/
theorem
    estimated_score_asymptotic_normality_of_pate_first_step_components_and_local_experiment_core
    (firstStep : PATEDoubleScoreFirstStepAssembly)
    (estimated : EstimatedScoreLocalExperimentInput)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        estimated.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        estimated.score_estimator_local_asymptotic_linearity)
    (hknown : estimated.known_score_asymptotic_normality)
    (h_prop_weight : firstStep.propensity_weighting_design)
    (h_treated_weight : firstStep.treated_prognostic_weighting_design)
    (h_control_weight : firstStep.control_prognostic_weighting_design)
    (h_prop : firstStep.propensity_component_asymptotic_linearity)
    (h_treated :
      firstStep.treated_prognostic_component_asymptotic_linearity)
    (h_control :
      firstStep.control_prognostic_component_asymptotic_linearity)
    (core : EstimatedScoreLocalExperimentCore estimated) :
    estimated.estimated_score_asymptotic_normality :=
  estimated_score_asymptotic_normality_of_pate_first_step_components
    firstStep estimated hfirst_transfer hscore_transfer hknown
    h_prop_weight h_treated_weight h_control_weight h_prop h_treated
    h_control core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_variance_identity

/--
PATT estimated-score asymptotic normality using first-step component
linearity, with the local-experiment/Godambe obligations packaged as a
compact core.
-/
theorem
    estimated_score_asymptotic_normality_of_patt_first_step_components_and_local_experiment_core
    (firstStep : PATTDoubleScoreFirstStepAssembly)
    (estimated : EstimatedScoreLocalExperimentInput)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        estimated.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        estimated.score_estimator_local_asymptotic_linearity)
    (hknown : estimated.known_score_asymptotic_normality)
    (h_prop_weight : firstStep.propensity_weighting_design)
    (h_control_weight : firstStep.control_prognostic_weighting_design)
    (h_prop : firstStep.propensity_component_asymptotic_linearity)
    (h_control :
      firstStep.control_prognostic_component_asymptotic_linearity)
    (core : EstimatedScoreLocalExperimentCore estimated) :
    estimated.estimated_score_asymptotic_normality :=
  estimated_score_asymptotic_normality_of_patt_first_step_components
    firstStep estimated hfirst_transfer hscore_transfer hknown
    h_prop_weight h_control_weight h_prop h_control
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_variance_identity

/--
PATE estimated-score asymptotic normality directly from first-step
Z-estimator component evidence, with the local-experiment/Godambe obligations
packaged as a compact core.
-/
theorem
    estimated_score_asymptotic_normality_of_pate_z_components_and_local_experiment_core
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {TSample : ℕ -> Type u} {TParameter : Type v} {TMoment : Type w}
    {TInfluenceFunction : Type x} {TLinearPart : Type y}
    {TRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (firstStep : PATEDoubleScoreFirstStepAssembly)
    (estimated : EstimatedScoreLocalExperimentInput)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
    (treated :
      FirstStepScoreComponentZEvidence TSample TParameter TMoment
        TInfluenceFunction TLinearPart TRemainder)
    (control :
      FirstStepScoreComponentZEvidence CSample CParameter CMoment
        CInfluenceFunction CLinearPart CRemainder)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        estimated.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        estimated.score_estimator_local_asymptotic_linearity)
    (hknown : estimated.known_score_asymptotic_normality)
    (h_prop_weight :
      propensity.component.weighting_design ->
        firstStep.propensity_weighting_design)
    (h_treated_weight :
      treated.component.weighting_design ->
        firstStep.treated_prognostic_weighting_design)
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_treated_component :
      treated.component.component_asymptotic_linearity ->
        firstStep.treated_prognostic_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity)
    (core : EstimatedScoreLocalExperimentCore estimated) :
    estimated.estimated_score_asymptotic_normality := by
  have hfirst_score :
      estimated.first_step_asymptotic_linearization ∧
        estimated.score_estimator_local_asymptotic_linearity :=
    estimated_score_local_experiment_input_first_step_and_score_local_of_pate_z_components
      firstStep estimated propensity treated control hfirst_transfer
      hscore_transfer h_prop_weight h_treated_weight h_control_weight
      h_prop_component h_treated_component h_control_component
  exact
    estimated_score_asymptotic_normality_of_local_experiment_core
      estimated core hknown hfirst_score.1 hfirst_score.2

/--
PATT estimated-score asymptotic normality directly from first-step
Z-estimator component evidence, with the local-experiment/Godambe obligations
packaged as a compact core.
-/
theorem
    estimated_score_asymptotic_normality_of_patt_z_components_and_local_experiment_core
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (firstStep : PATTDoubleScoreFirstStepAssembly)
    (estimated : EstimatedScoreLocalExperimentInput)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
    (control :
      FirstStepScoreComponentZEvidence CSample CParameter CMoment
        CInfluenceFunction CLinearPart CRemainder)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        estimated.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        estimated.score_estimator_local_asymptotic_linearity)
    (hknown : estimated.known_score_asymptotic_normality)
    (h_prop_weight :
      propensity.component.weighting_design ->
        firstStep.propensity_weighting_design)
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity)
    (core : EstimatedScoreLocalExperimentCore estimated) :
    estimated.estimated_score_asymptotic_normality := by
  have hfirst_score :
      estimated.first_step_asymptotic_linearization ∧
        estimated.score_estimator_local_asymptotic_linearity :=
    estimated_score_local_experiment_input_first_step_and_score_local_of_patt_z_components
      firstStep estimated propensity control hfirst_transfer hscore_transfer
      h_prop_weight h_control_weight h_prop_component h_control_component
  exact
    estimated_score_asymptotic_normality_of_local_experiment_core
      estimated core hknown hfirst_score.1 hfirst_score.2

/--
PATE estimated-score normality and variance formula using first-step component
linearity assembled from the PATE double-score first-step interface.
-/
theorem
    estimated_score_normality_and_variance_formula_of_pate_first_step_components
    (firstStep : PATEDoubleScoreFirstStepAssembly)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        estimated.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        estimated.score_estimator_local_asymptotic_linearity)
    (hknown : estimated.known_score_asymptotic_normality)
    (hknown_variance : estimated.known_score_variance_formula)
    (h_prop_weight : firstStep.propensity_weighting_design)
    (h_treated_weight : firstStep.treated_prognostic_weighting_design)
    (h_control_weight : firstStep.control_prognostic_weighting_design)
    (h_prop : firstStep.propensity_component_asymptotic_linearity)
    (h_treated :
      firstStep.treated_prognostic_component_asymptotic_linearity)
    (h_control :
      firstStep.control_prognostic_component_asymptotic_linearity)
    (hfunctional : estimated.matching_functional_local_derivative)
    (hequicontinuity : estimated.local_stochastic_equicontinuity)
    (hadjustment : estimated.score_adjustment_algebra)
    (hgodambe : estimated.godambe_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula := by
  have hfirst_score :
      firstStep.first_step_asymptotic_linearization ∧
        firstStep.score_estimator_local_asymptotic_linearity :=
    pate_first_step_and_score_local_linearity_of_components firstStep
      h_prop_weight h_treated_weight h_control_weight h_prop h_treated
      h_control
  exact
    estimated_score_asymptotic_normality_and_variance_formula_of_local_experiment_variance_input
      estimated hknown hknown_variance (hfirst_transfer hfirst_score.1)
      (hscore_transfer hfirst_score.2) hfunctional hequicontinuity
      hadjustment hgodambe

/--
PATE estimated-score normality and variance formula directly from three
component Z-estimator certificates.
-/
theorem
    estimated_score_normality_and_variance_formula_of_pate_z_components
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {TSample : ℕ -> Type u} {TParameter : Type v} {TMoment : Type w}
    {TInfluenceFunction : Type x} {TLinearPart : Type y}
    {TRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (firstStep : PATEDoubleScoreFirstStepAssembly)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
    (treated :
      FirstStepScoreComponentZEvidence TSample TParameter TMoment
        TInfluenceFunction TLinearPart TRemainder)
    (control :
      FirstStepScoreComponentZEvidence CSample CParameter CMoment
        CInfluenceFunction CLinearPart CRemainder)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        estimated.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        estimated.score_estimator_local_asymptotic_linearity)
    (hknown : estimated.known_score_asymptotic_normality)
    (hknown_variance : estimated.known_score_variance_formula)
    (h_prop_weight :
      propensity.component.weighting_design ->
        firstStep.propensity_weighting_design)
    (h_treated_weight :
      treated.component.weighting_design ->
        firstStep.treated_prognostic_weighting_design)
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_treated_component :
      treated.component.component_asymptotic_linearity ->
        firstStep.treated_prognostic_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity)
    (hfunctional : estimated.matching_functional_local_derivative)
    (hequicontinuity : estimated.local_stochastic_equicontinuity)
    (hadjustment : estimated.score_adjustment_algebra)
    (hgodambe : estimated.godambe_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula := by
  have hfirst_score :
      firstStep.first_step_asymptotic_linearization ∧
        firstStep.score_estimator_local_asymptotic_linearity :=
    pate_first_step_and_score_local_linearity_of_z_components firstStep
      propensity treated control h_prop_weight h_treated_weight
      h_control_weight h_prop_component h_treated_component
      h_control_component
  exact
    estimated_score_asymptotic_normality_and_variance_formula_of_local_experiment_variance_input
      estimated hknown hknown_variance (hfirst_transfer hfirst_score.1)
      (hscore_transfer hfirst_score.2) hfunctional hequicontinuity
      hadjustment hgodambe

/--
PATT estimated-score normality and variance formula using first-step component
linearity assembled from the PATT double-score first-step interface.
-/
theorem
    estimated_score_normality_and_variance_formula_of_patt_first_step_components
    (firstStep : PATTDoubleScoreFirstStepAssembly)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        estimated.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        estimated.score_estimator_local_asymptotic_linearity)
    (hknown : estimated.known_score_asymptotic_normality)
    (hknown_variance : estimated.known_score_variance_formula)
    (h_prop_weight : firstStep.propensity_weighting_design)
    (h_control_weight : firstStep.control_prognostic_weighting_design)
    (h_prop : firstStep.propensity_component_asymptotic_linearity)
    (h_control :
      firstStep.control_prognostic_component_asymptotic_linearity)
    (hfunctional : estimated.matching_functional_local_derivative)
    (hequicontinuity : estimated.local_stochastic_equicontinuity)
    (hadjustment : estimated.score_adjustment_algebra)
    (hgodambe : estimated.godambe_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula := by
  have hfirst_score :
      firstStep.first_step_asymptotic_linearization ∧
        firstStep.score_estimator_local_asymptotic_linearity :=
    patt_first_step_and_score_local_linearity_of_components firstStep
      h_prop_weight h_control_weight h_prop h_control
  exact
    estimated_score_asymptotic_normality_and_variance_formula_of_local_experiment_variance_input
      estimated hknown hknown_variance (hfirst_transfer hfirst_score.1)
      (hscore_transfer hfirst_score.2) hfunctional hequicontinuity
      hadjustment hgodambe

/--
PATT estimated-score normality and variance formula directly from propensity
and control component Z-estimator certificates.
-/
theorem
    estimated_score_normality_and_variance_formula_of_patt_z_components
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (firstStep : PATTDoubleScoreFirstStepAssembly)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
    (control :
      FirstStepScoreComponentZEvidence CSample CParameter CMoment
        CInfluenceFunction CLinearPart CRemainder)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        estimated.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        estimated.score_estimator_local_asymptotic_linearity)
    (hknown : estimated.known_score_asymptotic_normality)
    (hknown_variance : estimated.known_score_variance_formula)
    (h_prop_weight :
      propensity.component.weighting_design ->
        firstStep.propensity_weighting_design)
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity)
    (hfunctional : estimated.matching_functional_local_derivative)
    (hequicontinuity : estimated.local_stochastic_equicontinuity)
    (hadjustment : estimated.score_adjustment_algebra)
    (hgodambe : estimated.godambe_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula := by
  have hfirst_score :
      firstStep.first_step_asymptotic_linearization ∧
        firstStep.score_estimator_local_asymptotic_linearity :=
    patt_first_step_and_score_local_linearity_of_z_components firstStep
      propensity control h_prop_weight h_control_weight h_prop_component
      h_control_component
  exact
    estimated_score_asymptotic_normality_and_variance_formula_of_local_experiment_variance_input
      estimated hknown hknown_variance (hfirst_transfer hfirst_score.1)
      (hscore_transfer hfirst_score.2) hfunctional hequicontinuity
      hadjustment hgodambe

/--
Paired PATE/PATT first-step and score-local asymptotic linearity from their
component evidence.
-/
theorem paired_pate_patt_first_step_and_score_local_linearity_of_components
    (pate : PATEDoubleScoreFirstStepAssembly)
    (patt : PATTDoubleScoreFirstStepAssembly)
    (hpate_prop_weight : pate.propensity_weighting_design)
    (hpate_treated_weight : pate.treated_prognostic_weighting_design)
    (hpate_control_weight : pate.control_prognostic_weighting_design)
    (hpate_prop : pate.propensity_component_asymptotic_linearity)
    (hpate_treated :
      pate.treated_prognostic_component_asymptotic_linearity)
    (hpate_control :
      pate.control_prognostic_component_asymptotic_linearity)
    (hpatt_prop_weight : patt.propensity_weighting_design)
    (hpatt_control_weight : patt.control_prognostic_weighting_design)
    (hpatt_prop : patt.propensity_component_asymptotic_linearity)
    (hpatt_control :
      patt.control_prognostic_component_asymptotic_linearity) :
    pate.first_step_asymptotic_linearization ∧
      pate.score_estimator_local_asymptotic_linearity ∧
      patt.first_step_asymptotic_linearization ∧
      patt.score_estimator_local_asymptotic_linearity := by
  have hpate :
      pate.first_step_asymptotic_linearization ∧
        pate.score_estimator_local_asymptotic_linearity :=
    pate_first_step_and_score_local_linearity_of_components
      pate hpate_prop_weight hpate_treated_weight hpate_control_weight
      hpate_prop hpate_treated hpate_control
  have hpatt :
      patt.first_step_asymptotic_linearization ∧
        patt.score_estimator_local_asymptotic_linearity :=
    patt_first_step_and_score_local_linearity_of_components
      patt hpatt_prop_weight hpatt_control_weight hpatt_prop hpatt_control
  exact ⟨hpate.1, hpate.2, hpatt.1, hpatt.2⟩

/--
Paired PATE/PATT estimated-score normality and variance formula directly from
their first-step Z-estimator component certificates.
-/
theorem
    estimated_score_normality_and_variance_formula_of_paired_z_components
    {PATEPropSample : ℕ -> Type u} {PATEPropParameter : Type v}
    {PATEPropMoment : Type w} {PATEPropInfluenceFunction : Type x}
    {PATEPropLinearPart : Type y} {PATEPropRemainder : Type z}
    {PATETreatedSample : ℕ -> Type u} {PATETreatedParameter : Type v}
    {PATETreatedMoment : Type w} {PATETreatedInfluenceFunction : Type x}
    {PATETreatedLinearPart : Type y} {PATETreatedRemainder : Type z}
    {PATEControlSample : ℕ -> Type u} {PATEControlParameter : Type v}
    {PATEControlMoment : Type w} {PATEControlInfluenceFunction : Type x}
    {PATEControlLinearPart : Type y} {PATEControlRemainder : Type z}
    {PATTPropSample : ℕ -> Type u} {PATTPropParameter : Type v}
    {PATTPropMoment : Type w} {PATTPropInfluenceFunction : Type x}
    {PATTPropLinearPart : Type y} {PATTPropRemainder : Type z}
    {PATTControlSample : ℕ -> Type u} {PATTControlParameter : Type v}
    {PATTControlMoment : Type w} {PATTControlInfluenceFunction : Type x}
    {PATTControlLinearPart : Type y} {PATTControlRemainder : Type z}
    (pateFirstStep : PATEDoubleScoreFirstStepAssembly)
    (pattFirstStep : PATTDoubleScoreFirstStepAssembly)
    (pateEstimated : EstimatedScoreLocalExperimentVarianceInput)
    (pattEstimated : EstimatedScoreLocalExperimentVarianceInput)
    (patePropensity :
      FirstStepScoreComponentZEvidence PATEPropSample PATEPropParameter
        PATEPropMoment PATEPropInfluenceFunction PATEPropLinearPart
        PATEPropRemainder)
    (pateTreated :
      FirstStepScoreComponentZEvidence PATETreatedSample PATETreatedParameter
        PATETreatedMoment PATETreatedInfluenceFunction PATETreatedLinearPart
        PATETreatedRemainder)
    (pateControl :
      FirstStepScoreComponentZEvidence PATEControlSample PATEControlParameter
        PATEControlMoment PATEControlInfluenceFunction PATEControlLinearPart
        PATEControlRemainder)
    (pattPropensity :
      FirstStepScoreComponentZEvidence PATTPropSample PATTPropParameter
        PATTPropMoment PATTPropInfluenceFunction PATTPropLinearPart
        PATTPropRemainder)
    (pattControl :
      FirstStepScoreComponentZEvidence PATTControlSample PATTControlParameter
        PATTControlMoment PATTControlInfluenceFunction PATTControlLinearPart
        PATTControlRemainder)
    (hpate_first_transfer :
      pateFirstStep.first_step_asymptotic_linearization ->
        pateEstimated.first_step_asymptotic_linearization)
    (hpate_score_transfer :
      pateFirstStep.score_estimator_local_asymptotic_linearity ->
        pateEstimated.score_estimator_local_asymptotic_linearity)
    (hpatt_first_transfer :
      pattFirstStep.first_step_asymptotic_linearization ->
        pattEstimated.first_step_asymptotic_linearization)
    (hpatt_score_transfer :
      pattFirstStep.score_estimator_local_asymptotic_linearity ->
        pattEstimated.score_estimator_local_asymptotic_linearity)
    (hpate_known : pateEstimated.known_score_asymptotic_normality)
    (hpate_known_variance : pateEstimated.known_score_variance_formula)
    (hpatt_known : pattEstimated.known_score_asymptotic_normality)
    (hpatt_known_variance : pattEstimated.known_score_variance_formula)
    (hpate_prop_weight :
      patePropensity.component.weighting_design ->
        pateFirstStep.propensity_weighting_design)
    (hpate_treated_weight :
      pateTreated.component.weighting_design ->
        pateFirstStep.treated_prognostic_weighting_design)
    (hpate_control_weight :
      pateControl.component.weighting_design ->
        pateFirstStep.control_prognostic_weighting_design)
    (hpate_prop_component :
      patePropensity.component.component_asymptotic_linearity ->
        pateFirstStep.propensity_component_asymptotic_linearity)
    (hpate_treated_component :
      pateTreated.component.component_asymptotic_linearity ->
        pateFirstStep.treated_prognostic_component_asymptotic_linearity)
    (hpate_control_component :
      pateControl.component.component_asymptotic_linearity ->
        pateFirstStep.control_prognostic_component_asymptotic_linearity)
    (hpatt_prop_weight :
      pattPropensity.component.weighting_design ->
        pattFirstStep.propensity_weighting_design)
    (hpatt_control_weight :
      pattControl.component.weighting_design ->
        pattFirstStep.control_prognostic_weighting_design)
    (hpatt_prop_component :
      pattPropensity.component.component_asymptotic_linearity ->
        pattFirstStep.propensity_component_asymptotic_linearity)
    (hpatt_control_component :
      pattControl.component.component_asymptotic_linearity ->
        pattFirstStep.control_prognostic_component_asymptotic_linearity)
    (hpate_functional : pateEstimated.matching_functional_local_derivative)
    (hpate_equicontinuity :
      pateEstimated.local_stochastic_equicontinuity)
    (hpate_adjustment : pateEstimated.score_adjustment_algebra)
    (hpate_godambe : pateEstimated.godambe_identity)
    (hpatt_functional : pattEstimated.matching_functional_local_derivative)
    (hpatt_equicontinuity :
      pattEstimated.local_stochastic_equicontinuity)
    (hpatt_adjustment : pattEstimated.score_adjustment_algebra)
    (hpatt_godambe : pattEstimated.godambe_identity) :
    pateEstimated.estimated_score_asymptotic_normality ∧
      pateEstimated.estimated_score_variance_formula ∧
      pattEstimated.estimated_score_asymptotic_normality ∧
      pattEstimated.estimated_score_variance_formula := by
  have hpate :
      pateEstimated.estimated_score_asymptotic_normality ∧
        pateEstimated.estimated_score_variance_formula :=
    estimated_score_normality_and_variance_formula_of_pate_z_components
      pateFirstStep pateEstimated patePropensity pateTreated pateControl
      hpate_first_transfer hpate_score_transfer hpate_known
      hpate_known_variance hpate_prop_weight hpate_treated_weight
      hpate_control_weight hpate_prop_component hpate_treated_component
      hpate_control_component hpate_functional hpate_equicontinuity
      hpate_adjustment hpate_godambe
  have hpatt :
      pattEstimated.estimated_score_asymptotic_normality ∧
        pattEstimated.estimated_score_variance_formula :=
    estimated_score_normality_and_variance_formula_of_patt_z_components
      pattFirstStep pattEstimated pattPropensity pattControl
      hpatt_first_transfer hpatt_score_transfer hpatt_known
      hpatt_known_variance hpatt_prop_weight hpatt_control_weight
      hpatt_prop_component hpatt_control_component hpatt_functional
      hpatt_equicontinuity hpatt_adjustment hpatt_godambe
  exact ⟨hpate.1, hpate.2, hpatt.1, hpatt.2⟩

/--
PATE estimated-score normality and variance formula using first-step component
linearity assembled from the PATE double-score first-step interface, with the
local-experiment/Godambe obligations packaged as a compact core.
-/
theorem
    estimated_score_normality_and_variance_formula_of_pate_first_step_components_and_local_experiment_core
    (firstStep : PATEDoubleScoreFirstStepAssembly)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        estimated.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        estimated.score_estimator_local_asymptotic_linearity)
    (hknown : estimated.known_score_asymptotic_normality)
    (hknown_variance : estimated.known_score_variance_formula)
    (h_prop_weight : firstStep.propensity_weighting_design)
    (h_treated_weight : firstStep.treated_prognostic_weighting_design)
    (h_control_weight : firstStep.control_prognostic_weighting_design)
    (h_prop : firstStep.propensity_component_asymptotic_linearity)
    (h_treated :
      firstStep.treated_prognostic_component_asymptotic_linearity)
    (h_control :
      firstStep.control_prognostic_component_asymptotic_linearity)
    (core : EstimatedScoreLocalExperimentVarianceCore estimated)
    (hadjustment : estimated.score_adjustment_algebra) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_normality_and_variance_formula_of_pate_first_step_components
    firstStep estimated hfirst_transfer hscore_transfer hknown
    hknown_variance h_prop_weight h_treated_weight h_control_weight h_prop
    h_treated h_control core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity hadjustment core.godambe_identity

/--
PATT estimated-score normality and variance formula using first-step component
linearity assembled from the PATT double-score first-step interface, with the
local-experiment/Godambe obligations packaged as a compact core.
-/
theorem
    estimated_score_normality_and_variance_formula_of_patt_first_step_components_and_local_experiment_core
    (firstStep : PATTDoubleScoreFirstStepAssembly)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        estimated.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        estimated.score_estimator_local_asymptotic_linearity)
    (hknown : estimated.known_score_asymptotic_normality)
    (hknown_variance : estimated.known_score_variance_formula)
    (h_prop_weight : firstStep.propensity_weighting_design)
    (h_control_weight : firstStep.control_prognostic_weighting_design)
    (h_prop : firstStep.propensity_component_asymptotic_linearity)
    (h_control :
      firstStep.control_prognostic_component_asymptotic_linearity)
    (core : EstimatedScoreLocalExperimentVarianceCore estimated)
    (hadjustment : estimated.score_adjustment_algebra) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_normality_and_variance_formula_of_patt_first_step_components
    firstStep estimated hfirst_transfer hscore_transfer hknown
    hknown_variance h_prop_weight h_control_weight h_prop h_control
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity hadjustment core.godambe_identity

/--
PATE estimated-score normality and variance formula directly from three
component Z-estimator certificates, with the local-experiment/Godambe
obligations packaged as a compact core.
-/
theorem
    estimated_score_normality_and_variance_formula_of_pate_z_components_and_local_experiment_core
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {TSample : ℕ -> Type u} {TParameter : Type v} {TMoment : Type w}
    {TInfluenceFunction : Type x} {TLinearPart : Type y}
    {TRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (firstStep : PATEDoubleScoreFirstStepAssembly)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
    (treated :
      FirstStepScoreComponentZEvidence TSample TParameter TMoment
        TInfluenceFunction TLinearPart TRemainder)
    (control :
      FirstStepScoreComponentZEvidence CSample CParameter CMoment
        CInfluenceFunction CLinearPart CRemainder)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        estimated.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        estimated.score_estimator_local_asymptotic_linearity)
    (hknown : estimated.known_score_asymptotic_normality)
    (hknown_variance : estimated.known_score_variance_formula)
    (h_prop_weight :
      propensity.component.weighting_design ->
        firstStep.propensity_weighting_design)
    (h_treated_weight :
      treated.component.weighting_design ->
        firstStep.treated_prognostic_weighting_design)
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_treated_component :
      treated.component.component_asymptotic_linearity ->
        firstStep.treated_prognostic_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity)
    (core : EstimatedScoreLocalExperimentVarianceCore estimated)
    (hadjustment : estimated.score_adjustment_algebra) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_normality_and_variance_formula_of_pate_z_components
    firstStep estimated propensity treated control hfirst_transfer
    hscore_transfer hknown hknown_variance h_prop_weight h_treated_weight
    h_control_weight h_prop_component h_treated_component h_control_component
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity hadjustment core.godambe_identity

/--
PATT estimated-score normality and variance formula directly from propensity
and control component Z-estimator certificates, with the
local-experiment/Godambe obligations packaged as a compact core.
-/
theorem
    estimated_score_normality_and_variance_formula_of_patt_z_components_and_local_experiment_core
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (firstStep : PATTDoubleScoreFirstStepAssembly)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (propensity :
      FirstStepScoreComponentZEvidence PSample PParameter PMoment
        PInfluenceFunction PLinearPart PRemainder)
    (control :
      FirstStepScoreComponentZEvidence CSample CParameter CMoment
        CInfluenceFunction CLinearPart CRemainder)
    (hfirst_transfer :
      firstStep.first_step_asymptotic_linearization ->
        estimated.first_step_asymptotic_linearization)
    (hscore_transfer :
      firstStep.score_estimator_local_asymptotic_linearity ->
        estimated.score_estimator_local_asymptotic_linearity)
    (hknown : estimated.known_score_asymptotic_normality)
    (hknown_variance : estimated.known_score_variance_formula)
    (h_prop_weight :
      propensity.component.weighting_design ->
        firstStep.propensity_weighting_design)
    (h_control_weight :
      control.component.weighting_design ->
        firstStep.control_prognostic_weighting_design)
    (h_prop_component :
      propensity.component.component_asymptotic_linearity ->
        firstStep.propensity_component_asymptotic_linearity)
    (h_control_component :
      control.component.component_asymptotic_linearity ->
        firstStep.control_prognostic_component_asymptotic_linearity)
    (core : EstimatedScoreLocalExperimentVarianceCore estimated)
    (hadjustment : estimated.score_adjustment_algebra) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_normality_and_variance_formula_of_patt_z_components
    firstStep estimated propensity control hfirst_transfer hscore_transfer
    hknown hknown_variance h_prop_weight h_control_weight h_prop_component
    h_control_component core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity hadjustment core.godambe_identity

end WDSM
end Matching
end StatInference
