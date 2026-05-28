import StatInference.Matching.WDSM.EstimatorAlgebra

/-!
# Unit-level decomposition for WDSM matching imputation

The WDSM appendix decomposes each imputed treatment-effect contrast into a
heterogeneity term, an observed residual term, a matched-donor residual term,
and a matching-discrepancy term.  This file proves the finite algebra behind
that decomposition for one focal unit in each treatment arm.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit : Type*}

/--
Treated focal unit decomposition.

For a treated focal unit, `mu1 focal + residual focal` is observed directly and
the control potential outcome is imputed from control donors.  If the donor
coefficients sum to one, the contrast decomposes into treatment heterogeneity,
own residual, matched residual reuse, and control-mean discrepancy.
-/
theorem treated_unit_imputation_decomposition
    (donorSet : Finset Unit)
    (coefficient : Unit -> Unit -> Real)
    (mu0 mu1 residual : Unit -> Real) (tau : Real) (focal : Unit)
    (hsum : (∑ donor ∈ donorSet, coefficient focal donor) = 1) :
    mu1 focal + residual focal -
        imputedOutcome donorSet coefficient
          (fun donor => mu0 donor + residual donor) focal - tau =
      (mu1 focal - mu0 focal - tau) + residual focal -
        imputedOutcome donorSet coefficient residual focal +
          ∑ donor ∈ donorSet,
            coefficient focal donor * (mu0 focal - mu0 donor) := by
  have hsplit :
      (∑ donor ∈ donorSet,
          coefficient focal donor * (mu0 donor + residual donor)) =
        (∑ donor ∈ donorSet, coefficient focal donor * mu0 donor) +
          (∑ donor ∈ donorSet,
            coefficient focal donor * residual donor) := by
    calc
      (∑ donor ∈ donorSet,
          coefficient focal donor * (mu0 donor + residual donor))
          = (∑ donor ∈ donorSet,
              ((coefficient focal donor * mu0 donor) +
                (coefficient focal donor * residual donor))) := by
            exact Finset.sum_congr rfl
              (fun donor _hdonor => by ring)
      _ = (∑ donor ∈ donorSet, coefficient focal donor * mu0 donor) +
            (∑ donor ∈ donorSet,
              coefficient focal donor * residual donor) := by
          rw [Finset.sum_add_distrib]
  have hdisc :
      (∑ donor ∈ donorSet,
          coefficient focal donor * (mu0 focal - mu0 donor)) =
        mu0 focal -
          (∑ donor ∈ donorSet, coefficient focal donor * mu0 donor) := by
    calc
      (∑ donor ∈ donorSet,
          coefficient focal donor * (mu0 focal - mu0 donor))
          = (∑ donor ∈ donorSet,
              (coefficient focal donor * mu0 focal -
                coefficient focal donor * mu0 donor)) := by
            exact Finset.sum_congr rfl
              (fun donor _hdonor => by ring)
      _ = (∑ donor ∈ donorSet, coefficient focal donor * mu0 focal) -
            (∑ donor ∈ donorSet,
              coefficient focal donor * mu0 donor) := by
          rw [Finset.sum_sub_distrib]
      _ = (∑ donor ∈ donorSet, coefficient focal donor) * mu0 focal -
            (∑ donor ∈ donorSet,
              coefficient focal donor * mu0 donor) := by
          rw [Finset.sum_mul]
      _ = mu0 focal -
            (∑ donor ∈ donorSet,
              coefficient focal donor * mu0 donor) := by
          rw [hsum]
          ring
  unfold imputedOutcome
  rw [hsplit, hdisc]
  ring

/--
Control focal unit decomposition.

For a control focal unit, the treated potential outcome is imputed from treated
donors and the control outcome is observed directly.  The same coefficient
sum-to-one condition gives the sign-reversed discrepancy formula used in the
appendix.
-/
theorem control_unit_imputation_decomposition
    (donorSet : Finset Unit)
    (coefficient : Unit -> Unit -> Real)
    (mu0 mu1 residual : Unit -> Real) (tau : Real) (focal : Unit)
    (hsum : (∑ donor ∈ donorSet, coefficient focal donor) = 1) :
    imputedOutcome donorSet coefficient
        (fun donor => mu1 donor + residual donor) focal -
        (mu0 focal + residual focal) - tau =
      (mu1 focal - mu0 focal - tau) - residual focal +
        imputedOutcome donorSet coefficient residual focal -
          ∑ donor ∈ donorSet,
            coefficient focal donor * (mu1 focal - mu1 donor) := by
  have hsplit :
      (∑ donor ∈ donorSet,
          coefficient focal donor * (mu1 donor + residual donor)) =
        (∑ donor ∈ donorSet, coefficient focal donor * mu1 donor) +
          (∑ donor ∈ donorSet,
            coefficient focal donor * residual donor) := by
    calc
      (∑ donor ∈ donorSet,
          coefficient focal donor * (mu1 donor + residual donor))
          = (∑ donor ∈ donorSet,
              ((coefficient focal donor * mu1 donor) +
                (coefficient focal donor * residual donor))) := by
            exact Finset.sum_congr rfl
              (fun donor _hdonor => by ring)
      _ = (∑ donor ∈ donorSet, coefficient focal donor * mu1 donor) +
            (∑ donor ∈ donorSet,
              coefficient focal donor * residual donor) := by
          rw [Finset.sum_add_distrib]
  have hdisc :
      (∑ donor ∈ donorSet,
          coefficient focal donor * (mu1 focal - mu1 donor)) =
        mu1 focal -
          (∑ donor ∈ donorSet, coefficient focal donor * mu1 donor) := by
    calc
      (∑ donor ∈ donorSet,
          coefficient focal donor * (mu1 focal - mu1 donor))
          = (∑ donor ∈ donorSet,
              (coefficient focal donor * mu1 focal -
                coefficient focal donor * mu1 donor)) := by
            exact Finset.sum_congr rfl
              (fun donor _hdonor => by ring)
      _ = (∑ donor ∈ donorSet, coefficient focal donor * mu1 focal) -
            (∑ donor ∈ donorSet,
              coefficient focal donor * mu1 donor) := by
          rw [Finset.sum_sub_distrib]
      _ = (∑ donor ∈ donorSet, coefficient focal donor) * mu1 focal -
            (∑ donor ∈ donorSet,
              coefficient focal donor * mu1 donor) := by
          rw [Finset.sum_mul]
      _ = mu1 focal -
            (∑ donor ∈ donorSet,
              coefficient focal donor * mu1 donor) := by
          rw [hsum]
          ring
  unfold imputedOutcome
  rw [hsplit, hdisc]
  ring

end WDSM
end Matching
end StatInference
