import StatInference.Matching.WDSM.QuadraticVariation

/-!
# Heterogeneity variance algebra for WDSM

The WDSM appendix rewrites heterogeneity variance terms as normalized variances
of weighted centered treatment-effect contrasts, for example
`w * (m_1(D_1) - m_0(D_0) - tau)`.  This module records the finite
sum-of-squares algebra behind that display before any measure-theoretic
variance limit is invoked.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit : Type*}

/-- Finite sum of squared weighted centered treatment-effect contrasts. -/
noncomputable def heterogeneitySquareSum (sample : Finset Unit)
    (weight effect : Unit -> Real) (target : Real) : Real :=
  ∑ unit ∈ sample, (weight unit * (effect unit - target)) ^ 2

/-- Denominator-normalized finite heterogeneity square target. -/
noncomputable def normalizedHeterogeneitySquareTarget (sample : Finset Unit)
    (weight effect : Unit -> Real) (target denominator : Real) : Real :=
  heterogeneitySquareSum sample weight effect target / denominator ^ 2

/--
The weighted centered-effect square sum is a quadratic variation with
coefficient `weight` and variance proxy `(effect - target)^2`.
-/
theorem heterogeneitySquareSum_eq_quadraticVariation
    (sample : Finset Unit) (weight effect : Unit -> Real) (target : Real) :
    heterogeneitySquareSum sample weight effect target =
      quadraticVariation sample weight
        (fun unit => (effect unit - target) ^ 2) := by
  unfold heterogeneitySquareSum quadraticVariation
  exact Finset.sum_congr rfl
    (fun unit _hunit => by ring)

/-- The finite heterogeneity square sum is nonnegative. -/
theorem heterogeneitySquareSum_nonneg
    (sample : Finset Unit) (weight effect : Unit -> Real) (target : Real) :
    0 ≤ heterogeneitySquareSum sample weight effect target := by
  unfold heterogeneitySquareSum
  exact Finset.sum_nonneg
    (fun unit _hunit => sq_nonneg (weight unit * (effect unit - target)))

/-- The denominator-normalized heterogeneity square target is nonnegative. -/
theorem normalizedHeterogeneitySquareTarget_nonneg
    (sample : Finset Unit) (weight effect : Unit -> Real)
    (target denominator : Real) :
    0 ≤ normalizedHeterogeneitySquareTarget sample weight effect target
      denominator := by
  unfold normalizedHeterogeneitySquareTarget
  exact div_nonneg
    (heterogeneitySquareSum_nonneg sample weight effect target)
    (sq_nonneg denominator)

/-- Inverse-square form of the normalized heterogeneity square target. -/
theorem normalizedHeterogeneitySquareTarget_eq_inv_sq_mul
    (sample : Finset Unit) (weight effect : Unit -> Real)
    (target denominator : Real) :
    normalizedHeterogeneitySquareTarget sample weight effect target
        denominator =
      (1 / denominator ^ 2) *
        heterogeneitySquareSum sample weight effect target := by
  unfold normalizedHeterogeneitySquareTarget
  ring

/--
With a nonzero denominator, the normalized heterogeneity square target is the
quadratic variation formed with denominator-scaled survey weights.
-/
theorem normalizedHeterogeneitySquareTarget_eq_quadraticVariation_scaled_weight
    (sample : Finset Unit) (weight effect : Unit -> Real)
    (target denominator : Real) (hdenominator : denominator ≠ 0) :
    normalizedHeterogeneitySquareTarget sample weight effect target
        denominator =
      quadraticVariation sample
        (fun unit => weight unit / denominator)
        (fun unit => (effect unit - target) ^ 2) := by
  unfold normalizedHeterogeneitySquareTarget
  rw [heterogeneitySquareSum_eq_quadraticVariation]
  unfold quadraticVariation
  rw [Finset.sum_div]
  exact Finset.sum_congr rfl
    (fun unit _hunit => by
      field_simp [hdenominator])

/-- If the effect equals the target on the sample, the heterogeneity square sum is zero. -/
theorem heterogeneitySquareSum_eq_zero_of_effect_eq_target
    (sample : Finset Unit) (weight effect : Unit -> Real) (target : Real)
    (heffect : ∀ unit, unit ∈ sample -> effect unit = target) :
    heterogeneitySquareSum sample weight effect target = 0 := by
  unfold heterogeneitySquareSum
  exact Finset.sum_eq_zero
    (fun unit hunit => by
      rw [heffect unit hunit]
      ring)

/--
With nonzero sample weights, the heterogeneity square sum is zero exactly when
the effect is samplewise equal to the target.
-/
theorem heterogeneitySquareSum_eq_zero_iff_effect_eq_target_of_weight_ne_zero
    (sample : Finset Unit) (weight effect : Unit -> Real) (target : Real)
    (hweight : ∀ unit, unit ∈ sample -> weight unit ≠ 0) :
    heterogeneitySquareSum sample weight effect target = 0 ↔
      ∀ unit, unit ∈ sample -> effect unit = target := by
  constructor
  · intro hzero unit hunit
    have hzero' :
        (∑ unit ∈ sample,
          (weight unit * (effect unit - target)) ^ 2) = 0 := by
      simpa [heterogeneitySquareSum] using hzero
    have hterms :
        ∀ unit, unit ∈ sample ->
          (weight unit * (effect unit - target)) ^ 2 = 0 :=
      (Finset.sum_eq_zero_iff_of_nonneg
        (s := sample)
        (f := fun unit => (weight unit * (effect unit - target)) ^ 2)
        (fun unit _hunit =>
          sq_nonneg (weight unit * (effect unit - target)))).mp hzero'
    have hmul :
        weight unit * (effect unit - target) = 0 :=
      sq_eq_zero_iff.mp (hterms unit hunit)
    have hdiff : effect unit - target = 0 := by
      rcases mul_eq_zero.mp hmul with hweight_zero | hdiff_zero
      · exact False.elim ((hweight unit hunit) hweight_zero)
      · exact hdiff_zero
    linarith
  · intro heffect
    exact heterogeneitySquareSum_eq_zero_of_effect_eq_target
      sample weight effect target heffect

/--
If the effect equals the target on the sample, the normalized heterogeneity
square target is zero.
-/
theorem normalizedHeterogeneitySquareTarget_eq_zero_of_effect_eq_target
    (sample : Finset Unit) (weight effect : Unit -> Real)
    (target denominator : Real)
    (heffect : ∀ unit, unit ∈ sample -> effect unit = target) :
    normalizedHeterogeneitySquareTarget sample weight effect target
      denominator = 0 := by
  unfold normalizedHeterogeneitySquareTarget
  rw [heterogeneitySquareSum_eq_zero_of_effect_eq_target
    sample weight effect target heffect]
  ring

/--
With nonzero sample weights and nonzero denominator, the normalized
heterogeneity square target is zero exactly when the effect is samplewise equal
to the target.
-/
theorem normalizedHeterogeneitySquareTarget_eq_zero_iff_effect_eq_target_of_weight_ne_zero
    (sample : Finset Unit) (weight effect : Unit -> Real)
    (target denominator : Real)
    (hweight : ∀ unit, unit ∈ sample -> weight unit ≠ 0)
    (hdenominator : denominator ≠ 0) :
    normalizedHeterogeneitySquareTarget sample weight effect target
        denominator = 0 ↔
      ∀ unit, unit ∈ sample -> effect unit = target := by
  constructor
  · intro hzero
    apply
      (heterogeneitySquareSum_eq_zero_iff_effect_eq_target_of_weight_ne_zero
        sample weight effect target hweight).mp
    unfold normalizedHeterogeneitySquareTarget at hzero
    rcases div_eq_zero_iff.mp hzero with hsum | hdenominator_sq_zero
    · exact hsum
    · exact False.elim ((pow_ne_zero 2 hdenominator) hdenominator_sq_zero)
  · intro heffect
    exact normalizedHeterogeneitySquareTarget_eq_zero_of_effect_eq_target
      sample weight effect target denominator heffect

/--
With nonzero sample weights, one nonzero centered effect makes the finite
heterogeneity square sum strictly positive.
-/
theorem heterogeneitySquareSum_pos_of_exists_effect_ne_target_of_weight_ne_zero
    (sample : Finset Unit) (weight effect : Unit -> Real) (target : Real)
    (hweight : ∀ unit, unit ∈ sample -> weight unit ≠ 0)
    (hexists : ∃ unit, unit ∈ sample ∧ effect unit ≠ target) :
    0 < heterogeneitySquareSum sample weight effect target := by
  have hne :
      heterogeneitySquareSum sample weight effect target ≠ 0 := by
    intro hzero
    obtain ⟨unit, hunit, heffect_ne⟩ := hexists
    have heffect_eq :
        effect unit = target :=
      (heterogeneitySquareSum_eq_zero_iff_effect_eq_target_of_weight_ne_zero
        sample weight effect target hweight).mp hzero unit hunit
    exact heffect_ne heffect_eq
  exact lt_of_le_of_ne'
    (heterogeneitySquareSum_nonneg sample weight effect target) hne

/--
With nonzero sample weights and nonzero denominator, one nonzero centered
effect makes the normalized finite heterogeneity square target strictly
positive.
-/
theorem normalizedHeterogeneitySquareTarget_pos_of_exists_effect_ne_target_of_weight_ne_zero
    (sample : Finset Unit) (weight effect : Unit -> Real)
    (target denominator : Real)
    (hweight : ∀ unit, unit ∈ sample -> weight unit ≠ 0)
    (hdenominator : denominator ≠ 0)
    (hexists : ∃ unit, unit ∈ sample ∧ effect unit ≠ target) :
    0 < normalizedHeterogeneitySquareTarget sample weight effect target
      denominator := by
  have hne :
      normalizedHeterogeneitySquareTarget sample weight effect target
        denominator ≠ 0 := by
    intro hzero
    obtain ⟨unit, hunit, heffect_ne⟩ := hexists
    have heffect_eq :
        effect unit = target :=
      (normalizedHeterogeneitySquareTarget_eq_zero_iff_effect_eq_target_of_weight_ne_zero
        sample weight effect target denominator hweight hdenominator).mp
        hzero unit hunit
    exact heffect_ne heffect_eq
  exact lt_of_le_of_ne'
    (normalizedHeterogeneitySquareTarget_nonneg sample weight effect target
      denominator) hne

end WDSM
end Matching
end StatInference
