import Mathlib.Data.Finset.Basic
import StatInference.Matching.WDSM.PATTAlgebra
import Mathlib.Tactic.Ring

/-!
# Retrospective PATT survey-weighted reuse-transfer identities

This module gives manuscript-facing finite algebra for the retrospective PATT
estimator.  PATT has a one-sided structure: treated outcomes enter directly
with treated-side survey weights, while matched controls enter only through
their treated-weight reuse contributions.  No probability or asymptotics are
used here.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit : Type*}

/--
Exact retrospective PATT transfer to the control-donor reuse-frequency
representation with treated-side survey weights.

This is the finite algebra behind the manuscript rewrite

`(sum treated w1 Y - sum matched controls K0 Y) / sum treated w1`.
-/
theorem retrospective_patt_ratio_eq_matching_weight_ratio
    (treatedSet controlSet : Finset Unit)
    (controlCoefficient : Unit -> Unit -> Real)
    (treatedWeight treatedOutcome controlOutcome : Unit -> Real) :
    ((∑ treated ∈ treatedSet,
        treatedWeight treated * treatedOutcome treated) -
      (∑ treated ∈ treatedSet,
        treatedWeight treated *
          imputedOutcome controlSet controlCoefficient controlOutcome
            treated)) /
        (∑ treated ∈ treatedSet, treatedWeight treated) =
      ((∑ treated ∈ treatedSet,
        treatedWeight treated * treatedOutcome treated) -
        (∑ control ∈ controlSet,
          reuseContribution treatedSet controlCoefficient treatedWeight
            control *
            controlOutcome control)) /
        (∑ treated ∈ treatedSet, treatedWeight treated) := by
  exact patt_treated_mass_hajek_matching_weight_rewrite
    treatedSet controlSet controlCoefficient treatedWeight treatedOutcome
    controlOutcome

/--
The retrospective PATT imputation estimator has zero finite algebraic error
relative to its one-sided control-donor reuse-frequency representation.
-/
theorem retrospective_patt_matching_weight_error_eq_zero
    (treatedSet controlSet : Finset Unit)
    (controlCoefficient : Unit -> Unit -> Real)
    (treatedWeight treatedOutcome controlOutcome : Unit -> Real) :
    ((∑ treated ∈ treatedSet,
        treatedWeight treated * treatedOutcome treated) -
      (∑ treated ∈ treatedSet,
        treatedWeight treated *
          imputedOutcome controlSet controlCoefficient controlOutcome
            treated)) /
        (∑ treated ∈ treatedSet, treatedWeight treated) -
      ((∑ treated ∈ treatedSet,
        treatedWeight treated * treatedOutcome treated) -
        (∑ control ∈ controlSet,
          reuseContribution treatedSet controlCoefficient treatedWeight
            control *
            controlOutcome control)) /
        (∑ treated ∈ treatedSet, treatedWeight treated) =
      0 := by
  rw [retrospective_patt_ratio_eq_matching_weight_ratio]
  ring

end WDSM
end Matching
end StatInference
