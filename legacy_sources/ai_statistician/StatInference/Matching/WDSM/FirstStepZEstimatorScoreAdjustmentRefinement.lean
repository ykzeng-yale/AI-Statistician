import StatInference.Matching.WDSM.FirstStepZEstimatorBridge
import StatInference.Matching.WDSM.EstimatedScoreLocalExperimentVarianceRefinement

/-!
# First-step Z-estimator routes with concrete score-adjustment algebra

This module connects the first-step Z-estimator component routes to the
target-1321 score-adjustment refinement.  The older first-step routes accept the
abstract `EstimatedScoreLocalExperimentVarianceInput.score_adjustment_algebra`
premise directly.  The lemmas here discharge that premise from the fixed-law or
changing-law finite score-adjustment identities proved in
`ScoreAdjustmentAlgebra`, plus a small interpretation bridge into the local
experiment.
-/

namespace StatInference
namespace Matching
namespace WDSM

universe u v w x y z

variable {Param : Type*}

/--
PATE estimated-score normality and variance formula from component
Z-estimator certificates, with the score-adjustment premise supplied by the
fixed-law finite quadratic-form identity.
-/
theorem
    estimated_score_normality_and_variance_formula_of_pate_z_components_fixedLaw_score_adjustment_identity
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
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
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
    (hgodambe : estimated.godambe_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula := by
  exact
    estimated_score_normality_and_variance_formula_of_pate_z_components
      firstStep estimated propensity treated control hfirst_transfer
      hscore_transfer hknown hknown_variance h_prop_weight h_treated_weight
      h_control_weight h_prop_component h_treated_component h_control_component
      hfunctional hequicontinuity
      (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
        estimated.score_adjustment_algebra parameters oracleVariance
        firstStepLoading scoreCovariance hinterpret)
      hgodambe

/--
PATE estimated-score normality and variance formula from component
Z-estimator certificates, with the score-adjustment premise supplied by the
changing-law finite quadratic-form identity.
-/
theorem
    estimated_score_normality_and_variance_formula_of_pate_z_components_changingLaw_score_adjustment_identity
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
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
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
    (hgodambe : estimated.godambe_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula := by
  exact
    estimated_score_normality_and_variance_formula_of_pate_z_components
      firstStep estimated propensity treated control hfirst_transfer
      hscore_transfer hknown hknown_variance h_prop_weight h_treated_weight
      h_control_weight h_prop_component h_treated_component h_control_component
      hfunctional hequicontinuity
      (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
        estimated.score_adjustment_algebra parameters oracleVariance
        firstStepLoading targetDriftLoading scoreCovariance hinterpret)
      hgodambe

/--
PATT estimated-score normality and variance formula from component
Z-estimator certificates, with the score-adjustment premise supplied by the
fixed-law finite quadratic-form identity.
-/
theorem
    estimated_score_normality_and_variance_formula_of_patt_z_components_fixedLaw_score_adjustment_identity
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (firstStep : PATTDoubleScoreFirstStepAssembly)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
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
    (hgodambe : estimated.godambe_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula := by
  exact
    estimated_score_normality_and_variance_formula_of_patt_z_components
      firstStep estimated propensity control hfirst_transfer hscore_transfer
      hknown hknown_variance h_prop_weight h_control_weight h_prop_component
      h_control_component hfunctional hequicontinuity
      (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
        estimated.score_adjustment_algebra parameters oracleVariance
        firstStepLoading scoreCovariance hinterpret)
      hgodambe

/--
PATT estimated-score normality and variance formula from component
Z-estimator certificates, with the score-adjustment premise supplied by the
changing-law finite quadratic-form identity.
-/
theorem
    estimated_score_normality_and_variance_formula_of_patt_z_components_changingLaw_score_adjustment_identity
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (firstStep : PATTDoubleScoreFirstStepAssembly)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
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
    (hgodambe : estimated.godambe_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula := by
  exact
    estimated_score_normality_and_variance_formula_of_patt_z_components
      firstStep estimated propensity control hfirst_transfer hscore_transfer
      hknown hknown_variance h_prop_weight h_control_weight h_prop_component
      h_control_component hfunctional hequicontinuity
      (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
        estimated.score_adjustment_algebra parameters oracleVariance
        firstStepLoading targetDriftLoading scoreCovariance hinterpret)
      hgodambe

/--
PATE estimated-score normality and variance formula from component
Z-estimator certificates, fixed-law score-adjustment algebra, and the compact
WDSM-specific local-experiment core.
-/
theorem
    estimated_score_normality_and_variance_formula_of_pate_z_components_fixedLaw_score_adjustment_identity_and_local_experiment_core
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
    (core : EstimatedScoreLocalExperimentVarianceCore estimated)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
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
        firstStep.control_prognostic_component_asymptotic_linearity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_normality_and_variance_formula_of_pate_z_components_fixedLaw_score_adjustment_identity
    firstStep estimated parameters oracleVariance firstStepLoading
    scoreCovariance hinterpret propensity treated control hfirst_transfer
    hscore_transfer hknown hknown_variance h_prop_weight h_treated_weight
    h_control_weight h_prop_component h_treated_component h_control_component
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

/--
PATE estimated-score normality and variance formula from component
Z-estimator certificates, changing-law score-adjustment algebra, and the
compact WDSM-specific local-experiment core.
-/
theorem
    estimated_score_normality_and_variance_formula_of_pate_z_components_changingLaw_score_adjustment_identity_and_local_experiment_core
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
    (core : EstimatedScoreLocalExperimentVarianceCore estimated)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
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
        firstStep.control_prognostic_component_asymptotic_linearity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_normality_and_variance_formula_of_pate_z_components_changingLaw_score_adjustment_identity
    firstStep estimated parameters oracleVariance firstStepLoading
    targetDriftLoading scoreCovariance hinterpret propensity treated control
    hfirst_transfer hscore_transfer hknown hknown_variance h_prop_weight
    h_treated_weight h_control_weight h_prop_component h_treated_component
    h_control_component core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

/--
PATT estimated-score normality and variance formula from component
Z-estimator certificates, fixed-law score-adjustment algebra, and the compact
WDSM-specific local-experiment core.
-/
theorem
    estimated_score_normality_and_variance_formula_of_patt_z_components_fixedLaw_score_adjustment_identity_and_local_experiment_core
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (firstStep : PATTDoubleScoreFirstStepAssembly)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (core : EstimatedScoreLocalExperimentVarianceCore estimated)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
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
        firstStep.control_prognostic_component_asymptotic_linearity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_normality_and_variance_formula_of_patt_z_components_fixedLaw_score_adjustment_identity
    firstStep estimated parameters oracleVariance firstStepLoading
    scoreCovariance hinterpret propensity control hfirst_transfer
    hscore_transfer hknown hknown_variance h_prop_weight h_control_weight
    h_prop_component h_control_component
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

/--
PATT estimated-score normality and variance formula from component
Z-estimator certificates, changing-law score-adjustment algebra, and the
compact WDSM-specific local-experiment core.
-/
theorem
    estimated_score_normality_and_variance_formula_of_patt_z_components_changingLaw_score_adjustment_identity_and_local_experiment_core
    {PSample : ℕ -> Type u} {PParameter : Type v} {PMoment : Type w}
    {PInfluenceFunction : Type x} {PLinearPart : Type y}
    {PRemainder : Type z}
    {CSample : ℕ -> Type u} {CParameter : Type v} {CMoment : Type w}
    {CInfluenceFunction : Type x} {CLinearPart : Type y}
    {CRemainder : Type z}
    (firstStep : PATTDoubleScoreFirstStepAssembly)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (core : EstimatedScoreLocalExperimentVarianceCore estimated)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
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
        firstStep.control_prognostic_component_asymptotic_linearity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_normality_and_variance_formula_of_patt_z_components_changingLaw_score_adjustment_identity
    firstStep estimated parameters oracleVariance firstStepLoading
    targetDriftLoading scoreCovariance hinterpret propensity control
    hfirst_transfer hscore_transfer hknown hknown_variance h_prop_weight
    h_control_weight h_prop_component h_control_component
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

/--
PATE estimated-score normality and variance formula from first-step component
linearity, with the score-adjustment premise supplied by the fixed-law finite
quadratic-form identity.
-/
theorem
    estimated_score_normality_and_variance_formula_of_pate_first_step_components_fixedLaw_score_adjustment_identity
    (firstStep : PATEDoubleScoreFirstStepAssembly)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
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
    (hgodambe : estimated.godambe_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula := by
  exact
    estimated_score_normality_and_variance_formula_of_pate_first_step_components
      firstStep estimated hfirst_transfer hscore_transfer hknown
      hknown_variance h_prop_weight h_treated_weight h_control_weight h_prop
      h_treated h_control hfunctional hequicontinuity
      (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
        estimated.score_adjustment_algebra parameters oracleVariance
        firstStepLoading scoreCovariance hinterpret)
      hgodambe

/--
PATE estimated-score normality and variance formula from first-step component
linearity, with the score-adjustment premise supplied by the changing-law
finite quadratic-form identity.
-/
theorem
    estimated_score_normality_and_variance_formula_of_pate_first_step_components_changingLaw_score_adjustment_identity
    (firstStep : PATEDoubleScoreFirstStepAssembly)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
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
    (hgodambe : estimated.godambe_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula := by
  exact
    estimated_score_normality_and_variance_formula_of_pate_first_step_components
      firstStep estimated hfirst_transfer hscore_transfer hknown
      hknown_variance h_prop_weight h_treated_weight h_control_weight h_prop
      h_treated h_control hfunctional hequicontinuity
      (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
        estimated.score_adjustment_algebra parameters oracleVariance
        firstStepLoading targetDriftLoading scoreCovariance hinterpret)
      hgodambe

/--
PATT estimated-score normality and variance formula from first-step component
linearity, with the score-adjustment premise supplied by the fixed-law finite
quadratic-form identity.
-/
theorem
    estimated_score_normality_and_variance_formula_of_patt_first_step_components_fixedLaw_score_adjustment_identity
    (firstStep : PATTDoubleScoreFirstStepAssembly)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
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
    (hgodambe : estimated.godambe_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula := by
  exact
    estimated_score_normality_and_variance_formula_of_patt_first_step_components
      firstStep estimated hfirst_transfer hscore_transfer hknown
      hknown_variance h_prop_weight h_control_weight h_prop h_control
      hfunctional hequicontinuity
      (score_adjustment_algebra_of_fixedLaw_score_adjustment_identity
        estimated.score_adjustment_algebra parameters oracleVariance
        firstStepLoading scoreCovariance hinterpret)
      hgodambe

/--
PATT estimated-score normality and variance formula from first-step component
linearity, with the score-adjustment premise supplied by the changing-law
finite quadratic-form identity.
-/
theorem
    estimated_score_normality_and_variance_formula_of_patt_first_step_components_changingLaw_score_adjustment_identity
    (firstStep : PATTDoubleScoreFirstStepAssembly)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
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
    (hgodambe : estimated.godambe_identity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula := by
  exact
    estimated_score_normality_and_variance_formula_of_patt_first_step_components
      firstStep estimated hfirst_transfer hscore_transfer hknown
      hknown_variance h_prop_weight h_control_weight h_prop h_control
      hfunctional hequicontinuity
      (score_adjustment_algebra_of_changingLaw_score_adjustment_identity
        estimated.score_adjustment_algebra parameters oracleVariance
        firstStepLoading targetDriftLoading scoreCovariance hinterpret)
      hgodambe

/--
PATE estimated-score normality and variance formula from first-step component
linearity, fixed-law score-adjustment algebra, and the compact WDSM-specific
local-experiment core.
-/
theorem
    estimated_score_normality_and_variance_formula_of_pate_first_step_components_fixedLaw_score_adjustment_identity_and_local_experiment_core
    (firstStep : PATEDoubleScoreFirstStepAssembly)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (core : EstimatedScoreLocalExperimentVarianceCore estimated)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
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
      firstStep.control_prognostic_component_asymptotic_linearity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_normality_and_variance_formula_of_pate_first_step_components_fixedLaw_score_adjustment_identity
    firstStep estimated parameters oracleVariance firstStepLoading
    scoreCovariance hinterpret hfirst_transfer hscore_transfer hknown
    hknown_variance h_prop_weight h_treated_weight h_control_weight h_prop
    h_treated h_control core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

/--
PATE estimated-score normality and variance formula from first-step component
linearity, changing-law score-adjustment algebra, and the compact WDSM-specific
local-experiment core.
-/
theorem
    estimated_score_normality_and_variance_formula_of_pate_first_step_components_changingLaw_score_adjustment_identity_and_local_experiment_core
    (firstStep : PATEDoubleScoreFirstStepAssembly)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (core : EstimatedScoreLocalExperimentVarianceCore estimated)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
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
      firstStep.control_prognostic_component_asymptotic_linearity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_normality_and_variance_formula_of_pate_first_step_components_changingLaw_score_adjustment_identity
    firstStep estimated parameters oracleVariance firstStepLoading
    targetDriftLoading scoreCovariance hinterpret hfirst_transfer
    hscore_transfer hknown hknown_variance h_prop_weight h_treated_weight
    h_control_weight h_prop h_treated h_control
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

/--
PATT estimated-score normality and variance formula from first-step component
linearity, fixed-law score-adjustment algebra, and the compact WDSM-specific
local-experiment core.
-/
theorem
    estimated_score_normality_and_variance_formula_of_patt_first_step_components_fixedLaw_score_adjustment_identity_and_local_experiment_core
    (firstStep : PATTDoubleScoreFirstStepAssembly)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (core : EstimatedScoreLocalExperimentVarianceCore estimated)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      fixedLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading scoreCovariance =
        oracleVariance -
          scoreQuadraticForm parameters firstStepLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
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
      firstStep.control_prognostic_component_asymptotic_linearity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_normality_and_variance_formula_of_patt_first_step_components_fixedLaw_score_adjustment_identity
    firstStep estimated parameters oracleVariance firstStepLoading
    scoreCovariance hinterpret hfirst_transfer hscore_transfer hknown
    hknown_variance h_prop_weight h_control_weight h_prop h_control
    core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

/--
PATT estimated-score normality and variance formula from first-step component
linearity, changing-law score-adjustment algebra, and the compact WDSM-specific
local-experiment core.
-/
theorem
    estimated_score_normality_and_variance_formula_of_patt_first_step_components_changingLaw_score_adjustment_identity_and_local_experiment_core
    (firstStep : PATTDoubleScoreFirstStepAssembly)
    (estimated : EstimatedScoreLocalExperimentVarianceInput)
    (core : EstimatedScoreLocalExperimentVarianceCore estimated)
    (parameters : Finset Param) (oracleVariance : Real)
    (firstStepLoading targetDriftLoading : Param -> Real)
    (scoreCovariance : Param -> Param -> Real)
    (hinterpret :
      changingLawScoreAdjustedVariance parameters oracleVariance
          firstStepLoading targetDriftLoading scoreCovariance =
        fixedLawScoreAdjustedVariance parameters oracleVariance
            firstStepLoading scoreCovariance +
          scoreQuadraticForm parameters targetDriftLoading scoreCovariance ->
        estimated.score_adjustment_algebra)
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
      firstStep.control_prognostic_component_asymptotic_linearity) :
    estimated.estimated_score_asymptotic_normality ∧
      estimated.estimated_score_variance_formula :=
  estimated_score_normality_and_variance_formula_of_patt_first_step_components_changingLaw_score_adjustment_identity
    firstStep estimated parameters oracleVariance firstStepLoading
    targetDriftLoading scoreCovariance hinterpret hfirst_transfer
    hscore_transfer hknown hknown_variance h_prop_weight h_control_weight
    h_prop h_control core.matching_functional_local_derivative
    core.local_stochastic_equicontinuity core.godambe_identity

/--
Paired PATE/PATT estimated-score normality and variance formula from component
Z-estimator certificates, with both score-adjustment premises supplied by
fixed-law finite quadratic-form identities.
-/
theorem
    estimated_score_normality_and_variance_formula_of_paired_z_components_fixedLaw_score_adjustment_identities
    {PATEParam PATTParam : Type*}
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
    (pateParameters : Finset PATEParam) (pateOracleVariance : Real)
    (pateFirstStepLoading : PATEParam -> Real)
    (pateScoreCovariance : PATEParam -> PATEParam -> Real)
    (hpate_interpret :
      fixedLawScoreAdjustedVariance pateParameters pateOracleVariance
          pateFirstStepLoading pateScoreCovariance =
        pateOracleVariance -
          scoreQuadraticForm pateParameters pateFirstStepLoading
            pateScoreCovariance ->
        pateEstimated.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattScoreCovariance =
        pattOracleVariance -
          scoreQuadraticForm pattParameters pattFirstStepLoading
            pattScoreCovariance ->
        pattEstimated.score_adjustment_algebra)
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
    (hpate_godambe : pateEstimated.godambe_identity)
    (hpatt_functional : pattEstimated.matching_functional_local_derivative)
    (hpatt_equicontinuity :
      pattEstimated.local_stochastic_equicontinuity)
    (hpatt_godambe : pattEstimated.godambe_identity) :
    pateEstimated.estimated_score_asymptotic_normality ∧
      pateEstimated.estimated_score_variance_formula ∧
      pattEstimated.estimated_score_asymptotic_normality ∧
      pattEstimated.estimated_score_variance_formula := by
  have hpate :
      pateEstimated.estimated_score_asymptotic_normality ∧
        pateEstimated.estimated_score_variance_formula :=
    estimated_score_normality_and_variance_formula_of_pate_z_components_fixedLaw_score_adjustment_identity
      pateFirstStep pateEstimated pateParameters pateOracleVariance
      pateFirstStepLoading pateScoreCovariance hpate_interpret
      patePropensity pateTreated pateControl hpate_first_transfer
      hpate_score_transfer hpate_known hpate_known_variance
      hpate_prop_weight hpate_treated_weight hpate_control_weight
      hpate_prop_component hpate_treated_component hpate_control_component
      hpate_functional hpate_equicontinuity hpate_godambe
  have hpatt :
      pattEstimated.estimated_score_asymptotic_normality ∧
        pattEstimated.estimated_score_variance_formula :=
    estimated_score_normality_and_variance_formula_of_patt_z_components_fixedLaw_score_adjustment_identity
      pattFirstStep pattEstimated pattParameters pattOracleVariance
      pattFirstStepLoading pattScoreCovariance hpatt_interpret pattPropensity
      pattControl hpatt_first_transfer hpatt_score_transfer hpatt_known
      hpatt_known_variance hpatt_prop_weight hpatt_control_weight
      hpatt_prop_component hpatt_control_component hpatt_functional
      hpatt_equicontinuity hpatt_godambe
  exact ⟨hpate.1, hpate.2, hpatt.1, hpatt.2⟩

/--
Paired PATE/PATT estimated-score normality and variance formula from component
Z-estimator certificates, with both score-adjustment premises supplied by
changing-law finite quadratic-form identities.
-/
theorem
    estimated_score_normality_and_variance_formula_of_paired_z_components_changingLaw_score_adjustment_identities
    {PATEParam PATTParam : Type*}
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
    (pateParameters : Finset PATEParam) (pateOracleVariance : Real)
    (pateFirstStepLoading pateTargetDriftLoading : PATEParam -> Real)
    (pateScoreCovariance : PATEParam -> PATEParam -> Real)
    (hpate_interpret :
      changingLawScoreAdjustedVariance pateParameters pateOracleVariance
          pateFirstStepLoading pateTargetDriftLoading pateScoreCovariance =
        fixedLawScoreAdjustedVariance pateParameters pateOracleVariance
            pateFirstStepLoading pateScoreCovariance +
          scoreQuadraticForm pateParameters pateTargetDriftLoading
            pateScoreCovariance ->
        pateEstimated.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading pattTargetDriftLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      changingLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattTargetDriftLoading pattScoreCovariance =
        fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
            pattFirstStepLoading pattScoreCovariance +
          scoreQuadraticForm pattParameters pattTargetDriftLoading
            pattScoreCovariance ->
        pattEstimated.score_adjustment_algebra)
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
    (hpate_godambe : pateEstimated.godambe_identity)
    (hpatt_functional : pattEstimated.matching_functional_local_derivative)
    (hpatt_equicontinuity :
      pattEstimated.local_stochastic_equicontinuity)
    (hpatt_godambe : pattEstimated.godambe_identity) :
    pateEstimated.estimated_score_asymptotic_normality ∧
      pateEstimated.estimated_score_variance_formula ∧
      pattEstimated.estimated_score_asymptotic_normality ∧
      pattEstimated.estimated_score_variance_formula := by
  have hpate :
      pateEstimated.estimated_score_asymptotic_normality ∧
        pateEstimated.estimated_score_variance_formula :=
    estimated_score_normality_and_variance_formula_of_pate_z_components_changingLaw_score_adjustment_identity
      pateFirstStep pateEstimated pateParameters pateOracleVariance
      pateFirstStepLoading pateTargetDriftLoading pateScoreCovariance
      hpate_interpret patePropensity pateTreated pateControl
      hpate_first_transfer hpate_score_transfer hpate_known
      hpate_known_variance hpate_prop_weight hpate_treated_weight
      hpate_control_weight hpate_prop_component hpate_treated_component
      hpate_control_component hpate_functional hpate_equicontinuity
      hpate_godambe
  have hpatt :
      pattEstimated.estimated_score_asymptotic_normality ∧
        pattEstimated.estimated_score_variance_formula :=
    estimated_score_normality_and_variance_formula_of_patt_z_components_changingLaw_score_adjustment_identity
      pattFirstStep pattEstimated pattParameters pattOracleVariance
      pattFirstStepLoading pattTargetDriftLoading pattScoreCovariance
      hpatt_interpret pattPropensity pattControl hpatt_first_transfer
      hpatt_score_transfer hpatt_known hpatt_known_variance hpatt_prop_weight
      hpatt_control_weight hpatt_prop_component hpatt_control_component
      hpatt_functional hpatt_equicontinuity hpatt_godambe
  exact ⟨hpate.1, hpate.2, hpatt.1, hpatt.2⟩

/--
Paired PATE/PATT estimated-score normality and variance formula from
component Z-estimator certificates, fixed-law score-adjustment algebra, and
compact WDSM-specific local-experiment cores for both arms.
-/
theorem
    estimated_score_normality_and_variance_formula_of_paired_z_components_fixedLaw_score_adjustment_identities_and_local_experiment_cores
    {PATEParam PATTParam : Type*}
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
    (pateCore : EstimatedScoreLocalExperimentVarianceCore pateEstimated)
    (pattCore : EstimatedScoreLocalExperimentVarianceCore pattEstimated)
    (pateParameters : Finset PATEParam) (pateOracleVariance : Real)
    (pateFirstStepLoading : PATEParam -> Real)
    (pateScoreCovariance : PATEParam -> PATEParam -> Real)
    (hpate_interpret :
      fixedLawScoreAdjustedVariance pateParameters pateOracleVariance
          pateFirstStepLoading pateScoreCovariance =
        pateOracleVariance -
          scoreQuadraticForm pateParameters pateFirstStepLoading
            pateScoreCovariance ->
        pateEstimated.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattScoreCovariance =
        pattOracleVariance -
          scoreQuadraticForm pattParameters pattFirstStepLoading
            pattScoreCovariance ->
        pattEstimated.score_adjustment_algebra)
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
        pattFirstStep.control_prognostic_component_asymptotic_linearity) :
    pateEstimated.estimated_score_asymptotic_normality ∧
      pateEstimated.estimated_score_variance_formula ∧
      pattEstimated.estimated_score_asymptotic_normality ∧
      pattEstimated.estimated_score_variance_formula :=
  estimated_score_normality_and_variance_formula_of_paired_z_components_fixedLaw_score_adjustment_identities
    pateFirstStep pattFirstStep pateEstimated pattEstimated pateParameters
    pateOracleVariance pateFirstStepLoading pateScoreCovariance
    hpate_interpret pattParameters pattOracleVariance pattFirstStepLoading
    pattScoreCovariance hpatt_interpret patePropensity pateTreated
    pateControl pattPropensity pattControl hpate_first_transfer
    hpate_score_transfer hpatt_first_transfer hpatt_score_transfer
    hpate_known hpate_known_variance hpatt_known hpatt_known_variance
    hpate_prop_weight hpate_treated_weight hpate_control_weight
    hpate_prop_component hpate_treated_component hpate_control_component
    hpatt_prop_weight hpatt_control_weight hpatt_prop_component
    hpatt_control_component pateCore.matching_functional_local_derivative
    pateCore.local_stochastic_equicontinuity pateCore.godambe_identity
    pattCore.matching_functional_local_derivative
    pattCore.local_stochastic_equicontinuity pattCore.godambe_identity

/--
Paired PATE/PATT estimated-score normality and variance formula from
component Z-estimator certificates, changing-law score-adjustment algebra, and
compact WDSM-specific local-experiment cores for both arms.
-/
theorem
    estimated_score_normality_and_variance_formula_of_paired_z_components_changingLaw_score_adjustment_identities_and_local_experiment_cores
    {PATEParam PATTParam : Type*}
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
    (pateCore : EstimatedScoreLocalExperimentVarianceCore pateEstimated)
    (pattCore : EstimatedScoreLocalExperimentVarianceCore pattEstimated)
    (pateParameters : Finset PATEParam) (pateOracleVariance : Real)
    (pateFirstStepLoading pateTargetDriftLoading : PATEParam -> Real)
    (pateScoreCovariance : PATEParam -> PATEParam -> Real)
    (hpate_interpret :
      changingLawScoreAdjustedVariance pateParameters pateOracleVariance
          pateFirstStepLoading pateTargetDriftLoading pateScoreCovariance =
        fixedLawScoreAdjustedVariance pateParameters pateOracleVariance
            pateFirstStepLoading pateScoreCovariance +
          scoreQuadraticForm pateParameters pateTargetDriftLoading
            pateScoreCovariance ->
        pateEstimated.score_adjustment_algebra)
    (pattParameters : Finset PATTParam) (pattOracleVariance : Real)
    (pattFirstStepLoading pattTargetDriftLoading : PATTParam -> Real)
    (pattScoreCovariance : PATTParam -> PATTParam -> Real)
    (hpatt_interpret :
      changingLawScoreAdjustedVariance pattParameters pattOracleVariance
          pattFirstStepLoading pattTargetDriftLoading pattScoreCovariance =
        fixedLawScoreAdjustedVariance pattParameters pattOracleVariance
            pattFirstStepLoading pattScoreCovariance +
          scoreQuadraticForm pattParameters pattTargetDriftLoading
            pattScoreCovariance ->
        pattEstimated.score_adjustment_algebra)
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
        pattFirstStep.control_prognostic_component_asymptotic_linearity) :
    pateEstimated.estimated_score_asymptotic_normality ∧
      pateEstimated.estimated_score_variance_formula ∧
      pattEstimated.estimated_score_asymptotic_normality ∧
      pattEstimated.estimated_score_variance_formula :=
  estimated_score_normality_and_variance_formula_of_paired_z_components_changingLaw_score_adjustment_identities
    pateFirstStep pattFirstStep pateEstimated pattEstimated pateParameters
    pateOracleVariance pateFirstStepLoading pateTargetDriftLoading
    pateScoreCovariance hpate_interpret pattParameters pattOracleVariance
    pattFirstStepLoading pattTargetDriftLoading pattScoreCovariance
    hpatt_interpret patePropensity pateTreated pateControl pattPropensity
    pattControl hpate_first_transfer hpate_score_transfer hpatt_first_transfer
    hpatt_score_transfer hpate_known hpate_known_variance hpatt_known
    hpatt_known_variance hpate_prop_weight hpate_treated_weight
    hpate_control_weight hpate_prop_component hpate_treated_component
    hpate_control_component hpatt_prop_weight hpatt_control_weight
    hpatt_prop_component hpatt_control_component
    pateCore.matching_functional_local_derivative
    pateCore.local_stochastic_equicontinuity pateCore.godambe_identity
    pattCore.matching_functional_local_derivative
    pattCore.local_stochastic_equicontinuity pattCore.godambe_identity

end WDSM
end Matching
end StatInference
