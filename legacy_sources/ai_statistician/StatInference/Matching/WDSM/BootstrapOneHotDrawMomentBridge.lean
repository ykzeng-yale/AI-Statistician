import Mathlib.Data.Finset.Basic
import StatInference.Matching.WDSM.BootstrapMultinomialDrawBridge
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Ring

/-!
# One-hot draw moment bridge

This module proves the finite algebra that turns iid equal-probability
one-hot draw moments into the draw-level moment sums consumed by
`BootstrapMultinomialDrawBridge`.

The remaining probability input is now the elementary one-draw law:
same-draw one-hot moments and cross-draw independence/product moments.
-/

namespace StatInference
namespace Matching
namespace WDSM

open scoped BigOperators

variable {Unit Draw Omega : Type*}

/-- A finite sum of a constant real value. -/
theorem finset_sum_const_real {Alpha : Type*}
    (s : Finset Alpha) (constant : Real) :
    (∑ _x ∈ s, constant) = (s.card : Real) * constant := by
  simp [Finset.sum_const, nsmul_eq_mul]

/-- A diagonal finite indicator sum over a set containing the distinguished element. -/
theorem finset_sum_diag_indicator_real {Alpha : Type*} [DecidableEq Alpha]
    (s : Finset Alpha) (a : Alpha) (constant : Real) (ha : a ∈ s) :
    (∑ b ∈ s, if a = b then constant else 0) = constant := by
  let summand : Alpha -> Real := fun b => if a = b then constant else 0
  have hsingle : (∑ b ∈ s, summand b) = summand a := by
    apply Finset.sum_eq_single a
    · intro b _hb hne
      have hne' : a ≠ b := fun h => hne h.symm
      simp [summand, hne']
    · intro hnot_mem
      exact False.elim (hnot_mem ha)
  simpa [summand] using hsingle

/-- Double sum whose value depends only on whether the two draw indices agree. -/
theorem double_sum_if_eq_const_real {Alpha : Type*} [DecidableEq Alpha]
    (s : Finset Alpha) (diagonal offDiagonal : Real) :
    (∑ left ∈ s, ∑ right ∈ s,
        if left = right then diagonal else offDiagonal) =
      (s.card : Real) ^ 2 * offDiagonal +
        (s.card : Real) * (diagonal - offDiagonal) := by
  have hinner :
      ∀ left ∈ s,
        (∑ right ∈ s, if left = right then diagonal else offDiagonal) =
          (s.card : Real) * offDiagonal + (diagonal - offDiagonal) := by
    intro left hleft
    calc
      (∑ right ∈ s, if left = right then diagonal else offDiagonal) =
          ∑ right ∈ s,
            (offDiagonal +
              if left = right then diagonal - offDiagonal else 0) := by
            exact Finset.sum_congr rfl
              (fun right _hright => by
                by_cases h : left = right
                · simp [h]
                · simp [h])
      _ =
          (∑ _right ∈ s, offDiagonal) +
            (∑ right ∈ s,
              if left = right then diagonal - offDiagonal else 0) := by
            rw [Finset.sum_add_distrib]
      _ =
          (s.card : Real) * offDiagonal + (diagonal - offDiagonal) := by
            rw [finset_sum_const_real]
            rw [finset_sum_diag_indicator_real s left
              (diagonal - offDiagonal) hleft]
  calc
    (∑ left ∈ s, ∑ right ∈ s,
        if left = right then diagonal else offDiagonal) =
        ∑ left ∈ s,
          ((s.card : Real) * offDiagonal +
            (diagonal - offDiagonal)) := by
          exact Finset.sum_congr rfl hinner
    _ =
        (s.card : Real) *
          ((s.card : Real) * offDiagonal +
            (diagonal - offDiagonal)) := by
          rw [finset_sum_const_real]
    _ =
        (s.card : Real) ^ 2 * offDiagonal +
          (s.card : Real) * (diagonal - offDiagonal) := by
          ring

/--
IID equal-probability one-hot draw moments imply the draw-level moment sums
needed for multinomial counts.
-/
theorem oneHot_draw_moment_sums_of_iid_equal_probability_moments
    [DecidableEq Unit] [DecidableEq Draw]
    (support : Finset Omega) (mass : Omega -> Real)
    (sample : Finset Unit) (draws : Finset Draw)
    (drawIndicator : Omega -> Draw -> Unit -> Real)
    (sampleSize : Real)
    (hdraws_card : (draws.card : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hmean_one_draw :
      ∀ draw ∈ draws, ∀ unit ∈ sample,
        finiteExpectation support mass
          (fun omega => drawIndicator omega draw unit) =
            1 / sampleSize)
    (hsame_draw_cross :
      ∀ draw ∈ draws, ∀ left ∈ sample, ∀ right ∈ sample,
        finiteExpectation support mass
          (fun omega =>
            drawIndicator omega draw left *
              drawIndicator omega draw right) =
          if left = right then 1 / sampleSize else 0)
    (hdifferent_draw_cross :
      ∀ drawA ∈ draws, ∀ drawB ∈ draws, drawA ≠ drawB ->
        ∀ left ∈ sample, ∀ right ∈ sample,
          finiteExpectation support mass
            (fun omega =>
              drawIndicator omega drawA left *
                drawIndicator omega drawB right) =
            1 / sampleSize ^ 2) :
    (∀ unit ∈ sample,
        (∑ draw ∈ draws,
          finiteExpectation support mass
            (fun omega => drawIndicator omega draw unit)) = 1) ∧
      (∀ left ∈ sample, ∀ right ∈ sample,
        (∑ drawA ∈ draws, ∑ drawB ∈ draws,
          finiteExpectation support mass
            (fun omega =>
              drawIndicator omega drawA left *
                drawIndicator omega drawB right)) =
          if left = right then 2 - 1 / sampleSize else 1 - 1 / sampleSize) := by
  constructor
  · intro unit hunit
    calc
      (∑ draw ∈ draws,
          finiteExpectation support mass
            (fun omega => drawIndicator omega draw unit)) =
          ∑ _draw ∈ draws, 1 / sampleSize := by
          exact Finset.sum_congr rfl
            (fun draw hdraw => by rw [hmean_one_draw draw hdraw unit hunit])
      _ = (draws.card : Real) * (1 / sampleSize) := by
          rw [finset_sum_const_real]
      _ = sampleSize * (1 / sampleSize) := by
          rw [hdraws_card]
      _ = 1 := by
          field_simp [hsampleSize_ne]
  · intro left hleft right hright
    have hmoment_to_if :
        (∑ drawA ∈ draws, ∑ drawB ∈ draws,
          finiteExpectation support mass
            (fun omega =>
              drawIndicator omega drawA left *
                drawIndicator omega drawB right)) =
          ∑ drawA ∈ draws, ∑ drawB ∈ draws,
            if drawA = drawB then
              (if left = right then 1 / sampleSize else 0)
            else
              1 / sampleSize ^ 2 := by
      exact Finset.sum_congr rfl
        (fun drawA hdrawA =>
          Finset.sum_congr rfl
            (fun drawB hdrawB => by
              by_cases hdraw_eq : drawA = drawB
              · subst drawB
                rw [hsame_draw_cross drawA hdrawA left hleft right hright]
                simp
              · rw [
                  hdifferent_draw_cross drawA hdrawA drawB hdrawB hdraw_eq
                    left hleft right hright]
                simp [hdraw_eq]))
    rw [hmoment_to_if]
    rw [double_sum_if_eq_const_real]
    rw [hdraws_card]
    by_cases hunit_eq : left = right
    · simp [hunit_eq]
      field_simp [hsampleSize_ne]
      ring
    · simp [hunit_eq]
      field_simp [hsampleSize_ne]
      ring

/--
IID equal-probability one-hot draw moments imply the raw multinomial count
moments directly.
-/
theorem multinomialCountFromDrawIndicators_raw_count_moments_of_iid_oneHot_draw_moments
    [DecidableEq Unit] [DecidableEq Draw]
    (support : Finset Omega) (mass : Omega -> Real)
    (sample : Finset Unit) (draws : Finset Draw)
    (drawIndicator : Omega -> Draw -> Unit -> Real)
    (sampleSize : Real)
    (hdraws_card : (draws.card : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hmean_one_draw :
      ∀ draw ∈ draws, ∀ unit ∈ sample,
        finiteExpectation support mass
          (fun omega => drawIndicator omega draw unit) =
            1 / sampleSize)
    (hsame_draw_cross :
      ∀ draw ∈ draws, ∀ left ∈ sample, ∀ right ∈ sample,
        finiteExpectation support mass
          (fun omega =>
            drawIndicator omega draw left *
              drawIndicator omega draw right) =
          if left = right then 1 / sampleSize else 0)
    (hdifferent_draw_cross :
      ∀ drawA ∈ draws, ∀ drawB ∈ draws, drawA ≠ drawB ->
        ∀ left ∈ sample, ∀ right ∈ sample,
          finiteExpectation support mass
            (fun omega =>
              drawIndicator omega drawA left *
                drawIndicator omega drawB right) =
            1 / sampleSize ^ 2) :
    (∀ unit ∈ sample,
        finiteExpectation support mass
          (fun omega =>
            multinomialCountFromDrawIndicators draws drawIndicator omega unit) =
          1) ∧
      (∀ left ∈ sample, ∀ right ∈ sample,
        finiteExpectation support mass
          (fun omega =>
            multinomialCountFromDrawIndicators draws drawIndicator omega left *
              multinomialCountFromDrawIndicators draws drawIndicator omega right) =
          if left = right then 2 - 1 / sampleSize else 1 - 1 / sampleSize) := by
  have hsums :=
    oneHot_draw_moment_sums_of_iid_equal_probability_moments
      support mass sample draws drawIndicator sampleSize hdraws_card
      hsampleSize_ne hmean_one_draw hsame_draw_cross hdifferent_draw_cross
  exact
    multinomialCountFromDrawIndicators_raw_count_moments_of_draw_moment_sums
      support mass sample draws drawIndicator sampleSize hsums.1 hsums.2

/--
One-hot draw moment version of the normalized multinomial bootstrap variance
target.
-/
theorem multiplierPerturbationSecondMoment_normalized_eq_bootstrapCenteredVarianceTarget_of_iid_oneHot_draw_moments_of_base_ratio
    [DecidableEq Unit] [DecidableEq Draw]
    (support : Finset Omega) (mass : Omega -> Real)
    (sample : Finset Unit) (draws : Finset Draw)
    (drawIndicator : Omega -> Draw -> Unit -> Real)
    (contribution weight : Unit -> Real)
    (target denominator normalizer sampleSize : Real)
    (hmass :
      finiteExpectation support mass (fun _omega => (1 : Real)) = 1)
    (hdraws_card : (draws.card : Real) = sampleSize)
    (hsampleSize_ne : sampleSize ≠ 0)
    (hmean_one_draw :
      ∀ draw ∈ draws, ∀ unit ∈ sample,
        finiteExpectation support mass
          (fun omega => drawIndicator omega draw unit) =
            1 / sampleSize)
    (hsame_draw_cross :
      ∀ draw ∈ draws, ∀ left ∈ sample, ∀ right ∈ sample,
        finiteExpectation support mass
          (fun omega =>
            drawIndicator omega draw left *
              drawIndicator omega draw right) =
          if left = right then 1 / sampleSize else 0)
    (hdifferent_draw_cross :
      ∀ drawA ∈ draws, ∀ drawB ∈ draws, drawA ≠ drawB ->
        ∀ left ∈ sample, ∀ right ∈ sample,
          finiteExpectation support mass
            (fun omega =>
              drawIndicator omega drawA left *
                drawIndicator omega drawB right) =
            1 / sampleSize ^ 2)
    (hbase :
      baseLinearizedSum sample contribution =
        target * baseLinearizedSum sample weight) :
    (1 / denominator ^ 2) * (1 / normalizer) *
        multiplierPerturbationSecondMoment support mass sample
          (fun omega unit =>
            multinomialCountFromDrawIndicators draws drawIndicator omega unit)
          (fun unit => contribution unit - target * weight unit) =
      bootstrapCenteredVarianceTarget sample contribution weight target
        denominator normalizer := by
  have hsums :=
    oneHot_draw_moment_sums_of_iid_equal_probability_moments
      support mass sample draws drawIndicator sampleSize hdraws_card
      hsampleSize_ne hmean_one_draw hsame_draw_cross hdifferent_draw_cross
  exact
    multiplierPerturbationSecondMoment_normalized_eq_bootstrapCenteredVarianceTarget_of_multinomial_draw_moment_sums_of_base_ratio
      support mass sample draws drawIndicator contribution weight target
      denominator normalizer sampleSize hmass hsums.1 hsums.2 hbase

end WDSM
end Matching
end StatInference
