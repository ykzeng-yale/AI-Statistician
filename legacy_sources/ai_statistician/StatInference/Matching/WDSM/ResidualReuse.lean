import StatInference.Matching.WDSM.EstimatorAlgebra

/-!
# Residual reuse algebra for WDSM

The WDSM residual decomposition contains direct observed residuals minus
matched-donor residual imputations.  This module proves the donor-side rewrite
for that signed residual term.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit : Type*}

/--
Direct residual contribution minus focal-side imputed residuals equals a
donor-side residual sum with direct weight minus reuse contribution.
-/
theorem direct_minus_imputed_sum_eq_matching_weight_difference
    (focalSet donorSet : Finset Unit)
    (coefficient : Unit -> Unit -> Real)
    (directWeight focalWeight residual : Unit -> Real) :
    (∑ donor ∈ donorSet, directWeight donor * residual donor) -
      (∑ focal ∈ focalSet,
        focalWeight focal *
          imputedOutcome donorSet coefficient residual focal) =
      ∑ donor ∈ donorSet,
        (directWeight donor -
          reuseContribution focalSet coefficient focalWeight donor) *
          residual donor := by
  rw [focal_weighted_imputation_sum_eq_reuse_sum]
  rw [← Finset.sum_sub_distrib]
  exact Finset.sum_congr rfl
    (fun donor _hdonor => by ring)

end WDSM
end Matching
end StatInference
