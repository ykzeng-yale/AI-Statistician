import StatInference.Matching.WDSM.EstimatorAlgebra

/-!
# One-sided PATT estimator algebra for WDSM

PATT uses a one-sided treated numerator: treated observed outcomes minus
matched-control imputations, normalized by treated survey mass.  This module
proves the finite donor-side rewrite for that one-sided numerator.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit : Type*}

/--
One-sided PATT numerator rewrite: the treated-side weighted observed outcome
sum minus treated-side weighted matched-control imputation can be rewritten as
the treated direct sum minus a control donor-side reuse sum.
-/
theorem patt_treated_minus_control_imputation_eq_reuse_sum
    (treatedSet controlSet : Finset Unit)
    (coefficient : Unit -> Unit -> Real)
    (treatedWeight treatedOutcome controlOutcome : Unit -> Real) :
    (∑ treated ∈ treatedSet,
        treatedWeight treated * treatedOutcome treated) -
      (∑ treated ∈ treatedSet,
        treatedWeight treated *
          imputedOutcome controlSet coefficient controlOutcome treated) =
      (∑ treated ∈ treatedSet,
        treatedWeight treated * treatedOutcome treated) -
        (∑ control ∈ controlSet,
          reuseContribution treatedSet coefficient treatedWeight control *
            controlOutcome control) := by
  rw [focal_weighted_imputation_sum_eq_reuse_sum]

end WDSM
end Matching
end StatInference
