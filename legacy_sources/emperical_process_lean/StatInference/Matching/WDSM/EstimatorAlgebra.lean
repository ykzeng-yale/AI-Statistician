import StatInference.Matching.WDSM.FiniteMatching

/-!
# Finite estimator algebra for WDSM

This module proves the deterministic finite-sum rewrite behind the WDSM
matching-weight representation.  It is independent of nearest-neighbor
geometry and probability: once a coefficient system assigns each focal unit's
imputed outcome to donors, the focal-side imputation sum can be rewritten as a
donor-side reuse-frequency sum.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit : Type*}

/-- Imputed outcome for one focal unit from a finite donor set and coefficients. -/
noncomputable def imputedOutcome (donorSet : Finset Unit)
    (coefficient : Unit -> Unit -> Real) (outcome : Unit -> Real)
    (focal : Unit) : Real :=
  ∑ donor ∈ donorSet, coefficient focal donor * outcome donor

/--
Total donor-side reuse contribution accumulated from all focal units.

This abstracts the survey-weighted reuse frequency: each focal unit contributes
its focal survey weight times the coefficient assigned to this donor.
-/
noncomputable def reuseContribution (focalSet : Finset Unit)
    (coefficient : Unit -> Unit -> Real) (focalWeight : Unit -> Real)
    (donor : Unit) : Real :=
  ∑ focal ∈ focalSet, focalWeight focal * coefficient focal donor

/--
Finite Fubini step for WDSM imputation: summing weighted imputed outcomes over
focal units is the same as summing observed donor outcomes weighted by their
total reuse contribution.
-/
theorem focal_weighted_imputation_sum_eq_reuse_sum
    (focalSet donorSet : Finset Unit)
    (coefficient : Unit -> Unit -> Real)
    (focalWeight outcome : Unit -> Real) :
    (∑ focal ∈ focalSet,
      focalWeight focal *
        imputedOutcome donorSet coefficient outcome focal) =
      ∑ donor ∈ donorSet,
        reuseContribution focalSet coefficient focalWeight donor *
          outcome donor := by
  calc
    (∑ focal ∈ focalSet,
      focalWeight focal *
        imputedOutcome donorSet coefficient outcome focal)
        = ∑ focal ∈ focalSet, ∑ donor ∈ donorSet,
            (focalWeight focal * coefficient focal donor) *
              outcome donor := by
          exact Finset.sum_congr rfl
            (fun focal _hfocal => by
              simp [imputedOutcome, Finset.mul_sum, mul_assoc])
    _ = ∑ donor ∈ donorSet, ∑ focal ∈ focalSet,
          (focalWeight focal * coefficient focal donor) *
            outcome donor := by
          rw [Finset.sum_comm]
    _ = ∑ donor ∈ donorSet,
          reuseContribution focalSet coefficient focalWeight donor *
            outcome donor := by
          exact Finset.sum_congr rfl
            (fun donor _hdonor => by
              unfold reuseContribution
              calc
                (∑ focal ∈ focalSet,
                  (focalWeight focal * coefficient focal donor) *
                    outcome donor)
                    = (∑ focal ∈ focalSet,
                        focalWeight focal * coefficient focal donor) *
                        outcome donor := by
                      rw [← Finset.sum_mul]
                _ = (∑ focal ∈ focalSet,
                        focalWeight focal * coefficient focal donor) *
                        outcome donor := rfl)

/--
Arm-specific matching-weight representation.  A donor-side direct weighted
outcome sum plus the focal-side imputation sum equals one donor-side sum with
direct weight plus reuse contribution.
-/
theorem direct_plus_imputed_sum_eq_matching_weight_sum
    (focalSet donorSet : Finset Unit)
    (coefficient : Unit -> Unit -> Real)
    (directWeight focalWeight outcome : Unit -> Real) :
    (∑ donor ∈ donorSet, directWeight donor * outcome donor) +
      (∑ focal ∈ focalSet,
        focalWeight focal *
          imputedOutcome donorSet coefficient outcome focal) =
      ∑ donor ∈ donorSet,
        (directWeight donor +
          reuseContribution focalSet coefficient focalWeight donor) *
          outcome donor := by
  rw [focal_weighted_imputation_sum_eq_reuse_sum]
  rw [← Finset.sum_add_distrib]
  exact Finset.sum_congr rfl
    (fun donor _hdonor => by ring)

end WDSM
end Matching
end StatInference
