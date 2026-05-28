import StatInference.Matching.WDSM.SurveyRatio
import StatInference.Matching.WDSM.RatioLinearization

/-!
# Centering algebra for WDSM Hájek terms

The WDSM asymptotic decomposition uses centered weighted terms such as
`E_s[w H] - target * E_s[w]`.  Once the corresponding Hájek ratio equals the
target, the centered numerator is exactly zero.  This file records that
deterministic algebra.
-/

namespace StatInference
namespace Matching
namespace WDSM

/--
If a weighted numerator divided by its denominator equals the target, then the
centered numerator is exactly zero.
-/
theorem centeredNumerator_eq_zero_of_ratio_eq
    (numerator denominator target : Real)
    (hden : denominator ≠ 0)
    (hratio : numerator / denominator = target) :
    numerator - target * denominator = 0 := by
  rw [← hratio]
  field_simp [hden]
  ring

/--
The ratio error is zero under the same hypothesis, expressed through the
centered-numerator linearization used by WDSM Hájek decompositions.
-/
theorem ratio_sub_target_eq_zero_of_ratio_eq
    (numerator denominator target : Real)
    (hratio : numerator / denominator = target) :
    numerator / denominator - target = 0 := by
  rw [hratio]
  ring

namespace InverseSelectionIdentity

/--
An inverse-selection identity centers its selected weighted target exactly at
the recovered population target.
-/
theorem centered_selected_target_eq_zero
    (identity : InverseSelectionIdentity)
    (hsampling : identity.sampling_mass ≠ 0) :
    identity.selected_weighted_target -
        identity.population_target * identity.selected_weighted_one = 0 := by
  exact centeredNumerator_eq_zero_of_ratio_eq
    identity.selected_weighted_target identity.selected_weighted_one
    identity.population_target
    (by
      rw [identity.one_identity]
      exact one_div_ne_zero hsampling)
    (identity.hajekRatio_eq_populationTarget hsampling)

end InverseSelectionIdentity

end WDSM
end Matching
end StatInference
