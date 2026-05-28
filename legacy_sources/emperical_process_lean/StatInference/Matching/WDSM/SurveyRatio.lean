import Mathlib

/-!
# Survey-weighted ratio identities for WDSM

The WDSM manuscript repeatedly uses a common population-representation pattern:
an inverse-selection weighted selected-sample expectation equals the
population expectation divided by the sampling probability, and the matching
or causal estimand is then recovered by a Hájek ratio.  This file proves the
deterministic algebraic core of that step.
-/

namespace StatInference
namespace Matching
namespace WDSM

/--
Abstract inverse-selection representation for one target variable.

`selected_weighted_target` is the selected-sample weighted expectation of the
target variable; `population_target` is its population expectation; `sampling_mass`
is `P(S = 1)`.
-/
structure InverseSelectionIdentity where
  selected_weighted_target : Real
  selected_weighted_one : Real
  population_target : Real
  sampling_mass : Real
  target_identity :
    selected_weighted_target = population_target / sampling_mass
  one_identity :
    selected_weighted_one = 1 / sampling_mass

namespace InverseSelectionIdentity

/--
Hájek ratio recovery: if the weighted selected-sample target and denominator
share the same inverse-selection normalization, the ratio equals the
population target.
-/
theorem hajekRatio_eq_populationTarget (identity : InverseSelectionIdentity)
    (hsampling : identity.sampling_mass ≠ 0) :
    identity.selected_weighted_target / identity.selected_weighted_one =
      identity.population_target := by
  rw [identity.target_identity, identity.one_identity]
  field_simp [hsampling]

end InverseSelectionIdentity

/--
Two-arm PATE representation identity.  Each arm-specific potential-outcome
mean is recovered from its own inverse-selection ratio.
-/
structure PATERepresentation where
  treated : InverseSelectionIdentity
  control : InverseSelectionIdentity

namespace PATERepresentation

/-- Population PATE recovered by subtracting the two recovered arm means. -/
def populationPATE (repr : PATERepresentation) : Real :=
  repr.treated.population_target - repr.control.population_target

/-- Selected-sample Hájek PATE recovered by subtracting the two weighted ratios. -/
noncomputable def selectedHajekPATE (repr : PATERepresentation) : Real :=
  repr.treated.selected_weighted_target / repr.treated.selected_weighted_one -
    repr.control.selected_weighted_target / repr.control.selected_weighted_one

/-- The selected-sample Hájek PATE equals the population PATE under both arm identities. -/
theorem selectedHajekPATE_eq_populationPATE (repr : PATERepresentation)
    (htreated : repr.treated.sampling_mass ≠ 0)
    (hcontrol : repr.control.sampling_mass ≠ 0) :
    repr.selectedHajekPATE = repr.populationPATE := by
  simp [selectedHajekPATE, populationPATE,
    InverseSelectionIdentity.hajekRatio_eq_populationTarget,
    htreated, hcontrol]

end PATERepresentation

/--
PATT representation identity: the target numerator and treated-mass
denominator share the same inverse-selection normalization.
-/
structure PATTRepresentation where
  selected_weighted_treated_effect : Real
  selected_weighted_treated_mass : Real
  population_treated_effect_numerator : Real
  population_treated_mass : Real
  sampling_mass : Real
  numerator_identity :
    selected_weighted_treated_effect =
      population_treated_effect_numerator / sampling_mass
  denominator_identity :
    selected_weighted_treated_mass =
      population_treated_mass / sampling_mass

namespace PATTRepresentation

/-- Population PATT as numerator divided by treated population mass. -/
noncomputable def populationPATT (repr : PATTRepresentation) : Real :=
  repr.population_treated_effect_numerator / repr.population_treated_mass

/-- Selected-sample survey-weighted Hájek PATT. -/
noncomputable def selectedHajekPATT (repr : PATTRepresentation) : Real :=
  repr.selected_weighted_treated_effect / repr.selected_weighted_treated_mass

/-- The selected-sample Hájek PATT equals the population PATT. -/
theorem selectedHajekPATT_eq_populationPATT (repr : PATTRepresentation)
    (hsampling : repr.sampling_mass ≠ 0)
    (htreated : repr.population_treated_mass ≠ 0) :
    repr.selectedHajekPATT = repr.populationPATT := by
  simp [selectedHajekPATT, populationPATT, repr.numerator_identity,
    repr.denominator_identity]
  field_simp [hsampling, htreated]

end PATTRepresentation

end WDSM
end Matching
end StatInference
