import Mathlib

/-!
# Score relations for survey-weighted double-score matching

This module formalizes the algebraic core of the WDSM paper's selected-sample
propensity relations.  The probabilistic Bayes step is represented by the
definition `selectedPropensity`; the theorems prove the real-algebra
consequences needed to translate between selected-sample and population
propensity scores.
-/

namespace StatInference
namespace Matching
namespace WDSM

/--
Selected-sample propensity under retrospective sampling.

If `populationPropensity = P_Omega(Z = 1 | X)`,
`samplingIfTreated = pi1(X)`, and `samplingIfControl = pi0(X)`,
Bayes' rule gives this expression for
`P_s(Z = 1 | X)`.
-/
noncomputable def selectedPropensity
    (populationPropensity samplingIfTreated samplingIfControl : Real) : Real :=
  populationPropensity * samplingIfTreated /
    (populationPropensity * samplingIfTreated +
      (1 - populationPropensity) * samplingIfControl)

/--
Population propensity recovered from the selected-sample propensity and
treatment-specific inverse-inclusion weights.
-/
noncomputable def populationPropensityFromSelected
    (treatedWeight controlWeight selectedPropensity : Real) : Real :=
  treatedWeight * selectedPropensity /
    (treatedWeight * selectedPropensity +
      controlWeight * (1 - selectedPropensity))

theorem selectedPropensity_den_pos {e pi1 pi0 : Real}
    (he_pos : 0 < e) (he_lt_one : e < 1)
    (hpi1_pos : 0 < pi1) (hpi0_pos : 0 < pi0) :
    0 < e * pi1 + (1 - e) * pi0 := by
  exact add_pos (mul_pos he_pos hpi1_pos)
    (mul_pos (sub_pos.mpr he_lt_one) hpi0_pos)

theorem selectedPropensity_pos {e pi1 pi0 : Real}
    (he_pos : 0 < e) (he_lt_one : e < 1)
    (hpi1_pos : 0 < pi1) (hpi0_pos : 0 < pi0) :
    0 < selectedPropensity e pi1 pi0 := by
  exact div_pos (mul_pos he_pos hpi1_pos)
    (selectedPropensity_den_pos he_pos he_lt_one hpi1_pos hpi0_pos)

theorem selectedPropensity_lt_one {e pi1 pi0 : Real}
    (he_pos : 0 < e) (he_lt_one : e < 1)
    (hpi1_pos : 0 < pi1) (hpi0_pos : 0 < pi0) :
    selectedPropensity e pi1 pi0 < 1 := by
  have hcontrol : 0 < (1 - e) * pi0 :=
    mul_pos (sub_pos.mpr he_lt_one) hpi0_pos
  have hden : 0 < e * pi1 + (1 - e) * pi0 :=
    selectedPropensity_den_pos he_pos he_lt_one hpi1_pos hpi0_pos
  rw [selectedPropensity]
  rw [div_lt_one hden]
  exact lt_add_of_pos_right (e * pi1) hcontrol

theorem one_sub_selectedPropensity_eq {e pi1 pi0 : Real}
    (he_pos : 0 < e) (he_lt_one : e < 1)
    (hpi1_pos : 0 < pi1) (hpi0_pos : 0 < pi0) :
    1 - selectedPropensity e pi1 pi0 =
      (1 - e) * pi0 /
        (e * pi1 + (1 - e) * pi0) := by
  have hden_pos : 0 < e * pi1 + (1 - e) * pi0 :=
    selectedPropensity_den_pos he_pos he_lt_one hpi1_pos hpi0_pos
  unfold selectedPropensity
  field_simp [hden_pos.ne']
  ring

/--
The selected-sample odds equal the population odds multiplied by the relative
sampling probability ratio `pi1 / pi0`.
-/
theorem selected_odds_eq_population_odds_mul_sampling_ratio
    {e pi1 pi0 : Real}
    (he_pos : 0 < e) (he_lt_one : e < 1)
    (hpi1_pos : 0 < pi1) (hpi0_pos : 0 < pi0) :
    selectedPropensity e pi1 pi0 /
        (1 - selectedPropensity e pi1 pi0) =
      (e / (1 - e)) * (pi1 / pi0) := by
  have hden_pos : 0 < e * pi1 + (1 - e) * pi0 :=
    selectedPropensity_den_pos he_pos he_lt_one hpi1_pos hpi0_pos
  have hselected_lt_one :
      selectedPropensity e pi1 pi0 < 1 :=
    selectedPropensity_lt_one he_pos he_lt_one hpi1_pos hpi0_pos
  have hselected_sub_ne : 1 - selectedPropensity e pi1 pi0 ≠ 0 := by
    linarith
  have he_sub_ne : 1 - e ≠ 0 := by
    linarith
  unfold selectedPropensity at hselected_sub_ne ⊢
  field_simp [hden_pos.ne', hselected_sub_ne, he_sub_ne, hpi0_pos.ne']
  ring_nf

/--
Retrospective Bayes odds relation in the WDSM appendix: the population
propensity odds are recovered by multiplying selected-sample odds by the
treatment-specific survey-weight ratio `w1 / w0`.
-/
theorem population_odds_eq_weight_ratio_mul_selected_odds
    {e pi1 pi0 : Real}
    (he_pos : 0 < e) (he_lt_one : e < 1)
    (hpi1_pos : 0 < pi1) (hpi0_pos : 0 < pi0) :
    e / (1 - e) =
      ((1 / pi1) / (1 / pi0)) *
        (selectedPropensity e pi1 pi0 /
          (1 - selectedPropensity e pi1 pi0)) := by
  rw [selected_odds_eq_population_odds_mul_sampling_ratio
    he_pos he_lt_one hpi1_pos hpi0_pos]
  field_simp [hpi1_pos.ne', hpi0_pos.ne']

/--
Equivalent retrospective Bayes level relation: using `w1 = 1 / pi1` and
`w0 = 1 / pi0`, the population propensity is recovered from the selected-sample
propensity by the weighted fraction used in the WDSM score-estimation section.
-/
theorem populationPropensityFromSelected_inverse_sampling_eq
    {e pi1 pi0 : Real}
    (he_pos : 0 < e) (he_lt_one : e < 1)
    (hpi1_pos : 0 < pi1) (hpi0_pos : 0 < pi0) :
    populationPropensityFromSelected (1 / pi1) (1 / pi0)
        (selectedPropensity e pi1 pi0) = e := by
  have hden_pos : 0 < e * pi1 + (1 - e) * pi0 :=
    selectedPropensity_den_pos he_pos he_lt_one hpi1_pos hpi0_pos
  have hselected_lt_one :
      selectedPropensity e pi1 pi0 < 1 :=
    selectedPropensity_lt_one he_pos he_lt_one hpi1_pos hpi0_pos
  have hselected_sub_ne : 1 - selectedPropensity e pi1 pi0 ≠ 0 := by
    linarith
  have hone_sub :
      1 - selectedPropensity e pi1 pi0 =
        (1 - e) * pi0 /
          (e * pi1 + (1 - e) * pi0) :=
    one_sub_selectedPropensity_eq he_pos he_lt_one hpi1_pos hpi0_pos
  unfold populationPropensityFromSelected
  rw [hone_sub]
  unfold selectedPropensity
  have hden_alt : pi1 * e - e * pi0 + pi0 ≠ 0 := by
    have hden_alt_pos : 0 < pi1 * e - e * pi0 + pi0 := by
      nlinarith [hden_pos]
    exact hden_alt_pos.ne'
  field_simp [hpi1_pos.ne', hpi0_pos.ne', hden_pos.ne',
    hselected_sub_ne, hden_alt]
  have hden_comm : pi1 * e + (1 - e) * pi0 ≠ 0 := by
    have hden_comm_pos : 0 < pi1 * e + (1 - e) * pi0 := by
      nlinarith [hden_pos]
    exact hden_comm_pos.ne'
  rw [div_self hden_comm]
  ring

/--
Prospective sampling identity: when treated and control units share the same
sampling probability, the selected-sample propensity equals the population
propensity.
-/
theorem selectedPropensity_eq_population_of_common_sampling
    {e pi : Real} (hpi_ne : pi ≠ 0) :
    selectedPropensity e pi pi = e := by
  unfold selectedPropensity
  field_simp [hpi_ne]
  ring

end WDSM
end Matching
end StatInference
