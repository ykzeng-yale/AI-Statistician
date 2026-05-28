import StatInference.Matching.WDSM.SurveyRatio

/-!
# Identification interfaces for WDSM double-score matching

The current WDSM proof uses two conceptually separate identification steps.
First, treatment-specific double scores must be balancing scores in the sense
of Antonelli/Yang-Zhang.  Second, the survey-weighted matched score-space mean
must recover the corresponding population arm mean.  The probability-kernel
proofs of those statements are not yet formalized here, so this module records
them as explicit bridge interfaces and proves the downstream real algebra for
PATE and PATT once the arm-level identifications are supplied.
-/

namespace StatInference
namespace Matching
namespace WDSM

/--
Bridge interface for the treatment-specific double-score balancing claim.

`propensity_route` corresponds to the route where the propensity-score
component is correct.  `prognostic_route` corresponds to the route where the
arm-specific prognostic component is sufficient/correct.
-/
structure DoubleScoreBalancingBridge where
  treatment_unconfoundedness : Prop
  propensity_component_balances : Prop
  prognostic_component_balances : Prop
  double_score_balancing : Prop
  propensity_route :
    treatment_unconfoundedness ->
    propensity_component_balances ->
    double_score_balancing
  prognostic_route :
    treatment_unconfoundedness ->
    prognostic_component_balances ->
    double_score_balancing

theorem double_score_balancing_of_propensity_route
    (b : DoubleScoreBalancingBridge)
    (hunconfounded : b.treatment_unconfoundedness)
    (hpropensity : b.propensity_component_balances) :
    b.double_score_balancing :=
  b.propensity_route hunconfounded hpropensity

theorem double_score_balancing_of_prognostic_route
    (b : DoubleScoreBalancingBridge)
    (hunconfounded : b.treatment_unconfoundedness)
    (hprognostic : b.prognostic_component_balances) :
    b.double_score_balancing :=
  b.prognostic_route hunconfounded hprognostic

/--
Bridge interface for the WDSM score-space mean target.  It separates the
balancing-score statement from the survey-weighted matched-mean representation.
-/
structure SurveyWeightedScoreMeanBridge where
  double_score_balancing : Prop
  survey_weighted_score_mean_representation : Prop
  score_space_identification : Prop
  bridge :
    double_score_balancing ->
    survey_weighted_score_mean_representation ->
    score_space_identification

theorem score_space_identification_of_bridge
    (b : SurveyWeightedScoreMeanBridge)
    (hbalance : b.double_score_balancing)
    (hweighted_mean : b.survey_weighted_score_mean_representation) :
    b.score_space_identification :=
  b.bridge hbalance hweighted_mean

/--
Concrete arm-mean algebra for PATE once both treatment-arm means have been
identified on the WDSM score scale.
-/
structure PATEArmMeanIdentification where
  treated_population_mean : Real
  control_population_mean : Real
  treated_score_mean : Real
  control_score_mean : Real
  treated_identification : treated_score_mean = treated_population_mean
  control_identification : control_score_mean = control_population_mean

namespace PATEArmMeanIdentification

def populationPATE (id : PATEArmMeanIdentification) : Real :=
  id.treated_population_mean - id.control_population_mean

def scorePATE (id : PATEArmMeanIdentification) : Real :=
  id.treated_score_mean - id.control_score_mean

theorem scorePATE_eq_populationPATE (id : PATEArmMeanIdentification) :
    id.scorePATE = id.populationPATE := by
  simp [scorePATE, populationPATE, id.treated_identification,
    id.control_identification]

end PATEArmMeanIdentification

/--
Concrete one-sided PATT algebra once the treated numerator and treated mass
have been identified on the WDSM score scale.
-/
structure PATTMeanIdentification where
  population_treated_effect_numerator : Real
  population_treated_mass : Real
  score_treated_effect_numerator : Real
  score_treated_mass : Real
  numerator_identification :
    score_treated_effect_numerator = population_treated_effect_numerator
  mass_identification :
    score_treated_mass = population_treated_mass

namespace PATTMeanIdentification

noncomputable def populationPATT (id : PATTMeanIdentification) : Real :=
  id.population_treated_effect_numerator / id.population_treated_mass

noncomputable def scorePATT (id : PATTMeanIdentification) : Real :=
  id.score_treated_effect_numerator / id.score_treated_mass

theorem scorePATT_eq_populationPATT (id : PATTMeanIdentification) :
    id.scorePATT = id.populationPATT := by
  simp [scorePATT, populationPATT, id.numerator_identification,
    id.mass_identification]

end PATTMeanIdentification

end WDSM
end Matching
end StatInference
