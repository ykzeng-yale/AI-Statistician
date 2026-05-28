import StatInference.Matching.WDSM.FiniteMatching
import Mathlib.Algebra.BigOperators.Group.Finset.Sigma

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

theorem imputedOutcome_congr_on_donorSet (donorSet : Finset Unit)
    (coefficient : Unit -> Unit -> Real) (outcomeA outcomeB : Unit -> Real)
    (focal : Unit)
    (h : ∀ donor, donor ∈ donorSet -> outcomeA donor = outcomeB donor) :
    imputedOutcome donorSet coefficient outcomeA focal =
      imputedOutcome donorSet coefficient outcomeB focal := by
  unfold imputedOutcome
  exact Finset.sum_congr rfl
    (fun donor hdonor => by rw [h donor hdonor])

theorem reuseContribution_congr_on_focalSet (focalSet : Finset Unit)
    (coefficient : Unit -> Unit -> Real)
    (focalWeightA focalWeightB : Unit -> Real) (donor : Unit)
    (h : ∀ focal, focal ∈ focalSet ->
      focalWeightA focal = focalWeightB focal) :
    reuseContribution focalSet coefficient focalWeightA donor =
      reuseContribution focalSet coefficient focalWeightB donor := by
  unfold reuseContribution
  exact Finset.sum_congr rfl
    (fun focal hfocal => by rw [h focal hfocal])

theorem imputedOutcome_zero (donorSet : Finset Unit)
    (coefficient : Unit -> Unit -> Real) (focal : Unit) :
    imputedOutcome donorSet coefficient (fun _donor => 0) focal = 0 := by
  simp [imputedOutcome]

theorem reuseContribution_zero_focalWeight (focalSet : Finset Unit)
    (coefficient : Unit -> Unit -> Real) (donor : Unit) :
    reuseContribution focalSet coefficient (fun _focal => 0) donor = 0 := by
  simp [reuseContribution]

theorem reuseContribution_zero_coefficient (focalSet : Finset Unit)
    (focalWeight : Unit -> Real) (donor : Unit) :
    reuseContribution focalSet (fun _focal _donor => 0) focalWeight donor = 0 := by
  simp [reuseContribution]

theorem imputedOutcome_add (donorSet : Finset Unit)
    (coefficient : Unit -> Unit -> Real) (outcomeA outcomeB : Unit -> Real)
    (focal : Unit) :
    imputedOutcome donorSet coefficient
        (fun donor => outcomeA donor + outcomeB donor) focal =
      imputedOutcome donorSet coefficient outcomeA focal +
        imputedOutcome donorSet coefficient outcomeB focal := by
  unfold imputedOutcome
  simp [mul_add, Finset.sum_add_distrib]

theorem imputedOutcome_sub (donorSet : Finset Unit)
    (coefficient : Unit -> Unit -> Real) (outcomeA outcomeB : Unit -> Real)
    (focal : Unit) :
    imputedOutcome donorSet coefficient
        (fun donor => outcomeA donor - outcomeB donor) focal =
      imputedOutcome donorSet coefficient outcomeA focal -
        imputedOutcome donorSet coefficient outcomeB focal := by
  unfold imputedOutcome
  simp [mul_sub, Finset.sum_sub_distrib]

theorem imputedOutcome_neg (donorSet : Finset Unit)
    (coefficient : Unit -> Unit -> Real) (outcome : Unit -> Real)
    (focal : Unit) :
    imputedOutcome donorSet coefficient (fun donor => -outcome donor) focal =
      -imputedOutcome donorSet coefficient outcome focal := by
  unfold imputedOutcome
  calc
    (∑ donor ∈ donorSet, coefficient focal donor * (fun donor => -outcome donor) donor)
        = ∑ donor ∈ donorSet,
            -(coefficient focal donor * outcome donor) := by
          exact Finset.sum_congr rfl (fun donor _hdonor => by ring)
    _ = -(∑ donor ∈ donorSet, coefficient focal donor * outcome donor) := by
          rw [Finset.sum_neg_distrib]

theorem imputedOutcome_smul_const (donorSet : Finset Unit)
    (coefficient : Unit -> Unit -> Real) (outcome : Unit -> Real)
    (scale : Real) (focal : Unit) :
    imputedOutcome donorSet coefficient (fun donor => scale * outcome donor) focal =
      scale * imputedOutcome donorSet coefficient outcome focal := by
  unfold imputedOutcome
  calc
    (∑ donor ∈ donorSet, coefficient focal donor * (scale * outcome donor))
        = ∑ donor ∈ donorSet,
            scale * (coefficient focal donor * outcome donor) := by
          exact Finset.sum_congr rfl (fun donor _hdonor => by ring)
    _ = scale * (∑ donor ∈ donorSet,
            coefficient focal donor * outcome donor) := by
          rw [Finset.mul_sum]

theorem imputedOutcome_const_of_coeff_sum_one (donorSet : Finset Unit)
    (coefficient : Unit -> Unit -> Real) (value : Real) (focal : Unit)
    (hsum : (∑ donor ∈ donorSet, coefficient focal donor) = 1) :
    imputedOutcome donorSet coefficient (fun _donor => value) focal = value := by
  unfold imputedOutcome
  calc
    (∑ donor ∈ donorSet, coefficient focal donor * (fun _donor => value) donor)
        = (∑ donor ∈ donorSet, coefficient focal donor) * value := by
          rw [Finset.sum_mul]
    _ = value := by
          rw [hsum]
          ring

theorem reuseContribution_add_focalWeight (focalSet : Finset Unit)
    (coefficient : Unit -> Unit -> Real)
    (focalWeightA focalWeightB : Unit -> Real) (donor : Unit) :
    reuseContribution focalSet coefficient
        (fun focal => focalWeightA focal + focalWeightB focal) donor =
      reuseContribution focalSet coefficient focalWeightA donor +
        reuseContribution focalSet coefficient focalWeightB donor := by
  unfold reuseContribution
  simp [add_mul, Finset.sum_add_distrib]

theorem reuseContribution_smul_const_focalWeight (focalSet : Finset Unit)
    (coefficient : Unit -> Unit -> Real) (focalWeight : Unit -> Real)
    (scale : Real) (donor : Unit) :
    reuseContribution focalSet coefficient
        (fun focal => scale * focalWeight focal) donor =
      scale * reuseContribution focalSet coefficient focalWeight donor := by
  unfold reuseContribution
  calc
    (∑ focal ∈ focalSet, (scale * focalWeight focal) * coefficient focal donor)
        = ∑ focal ∈ focalSet,
            scale * (focalWeight focal * coefficient focal donor) := by
          exact Finset.sum_congr rfl (fun focal _hfocal => by ring)
    _ = scale * (∑ focal ∈ focalSet,
            focalWeight focal * coefficient focal donor) := by
          rw [Finset.mul_sum]

theorem reuseContribution_zero_of_focalWeight_zero_on_focalSet
    (focalSet : Finset Unit) (coefficient : Unit -> Unit -> Real)
    (focalWeight : Unit -> Real) (donor : Unit)
    (hzero : ∀ focal, focal ∈ focalSet -> focalWeight focal = 0) :
    reuseContribution focalSet coefficient focalWeight donor = 0 := by
  unfold reuseContribution
  exact Finset.sum_eq_zero
    (fun focal hfocal => by rw [hzero focal hfocal]; ring)

theorem sum_reuseContribution_eq_sum_focalWeight_of_coeff_sum_one
    (focalSet donorSet : Finset Unit)
    (coefficient : Unit -> Unit -> Real) (focalWeight : Unit -> Real)
    (hcoeff : ∀ focal, focal ∈ focalSet ->
      (∑ donor ∈ donorSet, coefficient focal donor) = 1) :
    (∑ donor ∈ donorSet,
      reuseContribution focalSet coefficient focalWeight donor) =
        ∑ focal ∈ focalSet, focalWeight focal := by
  unfold reuseContribution
  calc
    (∑ donor ∈ donorSet,
      ∑ focal ∈ focalSet, focalWeight focal * coefficient focal donor)
        = ∑ focal ∈ focalSet,
            ∑ donor ∈ donorSet, focalWeight focal * coefficient focal donor := by
          rw [Finset.sum_comm]
    _ = ∑ focal ∈ focalSet, focalWeight focal := by
          exact Finset.sum_congr rfl
            (fun focal hfocal => by
              calc
                (∑ donor ∈ donorSet, focalWeight focal * coefficient focal donor)
                    = focalWeight focal *
                        (∑ donor ∈ donorSet, coefficient focal donor) := by
                      rw [Finset.mul_sum]
                _ = focalWeight focal := by
                      rw [hcoeff focal hfocal]
                      ring)

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
