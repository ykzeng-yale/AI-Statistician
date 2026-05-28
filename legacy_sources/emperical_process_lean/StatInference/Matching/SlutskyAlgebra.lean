import Mathlib.MeasureTheory.Function.ConvergenceInDistribution

/-!
# Mathlib-backed Slutsky algebra for WDSM

The WDSM asymptotic proof repeatedly needs the step: a statistic with an
asymptotic distribution keeps the same distributional limit after adding a
remainder that converges to zero in probability.  Mathlib already proves this
as a Slutsky theorem for `TendstoInDistribution` and `TendstoInMeasure`; this
module exposes the exact real-valued wrapper used by the WDSM proof plan.
-/

namespace StatInference
namespace Matching
namespace WDSM

open MeasureTheory
open scoped Topology

variable {Index Sample LimitSample : Type*}
variable [MeasurableSpace Sample] [MeasurableSpace LimitSample]
variable {sampleLaw : MeasureTheory.Measure Sample}
variable {limitLaw : MeasureTheory.Measure LimitSample}
variable [MeasureTheory.IsProbabilityMeasure sampleLaw]
variable [MeasureTheory.IsProbabilityMeasure limitLaw]
variable {l : Filter Index}
variable [l.IsCountablyGenerated]

/--
Slutsky addition wrapper: adding a real-valued remainder converging to zero in
probability preserves the distributional limit of the main statistic.
-/
theorem tendstoInDistribution_add_negligible_zero
    (main remainder : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hmain :
      TendstoInDistribution main l limit (fun _index => sampleLaw) limitLaw)
    (hremainder :
      TendstoInMeasure sampleLaw remainder l (fun _sample => (0 : Real)))
    (hremainder_meas :
      ∀ index, AEMeasurable (remainder index) sampleLaw) :
    TendstoInDistribution
      (fun index sample => main index sample + remainder index sample)
      l limit (fun _index => sampleLaw) limitLaw := by
  simpa using
    hmain.add_of_tendstoInMeasure_const
      (Y := remainder)
      (c := (0 : Real))
      hremainder hremainder_meas

omit [MeasureTheory.IsProbabilityMeasure sampleLaw] [l.IsCountablyGenerated] in
/-- Negating a real-valued remainder that converges to zero in probability
still converges to zero in probability. -/
theorem tendstoInMeasure_neg_zero
    (remainder : Index -> Sample -> Real)
    (hremainder :
      TendstoInMeasure sampleLaw remainder l (fun _sample => (0 : Real))) :
    TendstoInMeasure sampleLaw
      (fun index sample => -remainder index sample) l
      (fun _sample => (0 : Real)) := by
  rw [tendstoInMeasure_iff_norm] at hremainder ⊢
  intro ε hε
  have hsame :
      (fun index =>
        sampleLaw {sample | ε ≤ ‖-remainder index sample - 0‖}) =
        (fun index =>
          sampleLaw {sample | ε ≤ ‖remainder index sample - 0‖}) := by
    funext index
    congr 1
    ext sample
    simp only [Set.mem_setOf_eq]
    rw [sub_zero, sub_zero, norm_neg]
  rw [hsame]
  exact hremainder ε hε

omit [MeasureTheory.IsProbabilityMeasure sampleLaw] [l.IsCountablyGenerated] in
/--
Multiplying a real-valued remainder that converges to zero in probability by a
fixed scalar preserves convergence to zero in probability.
-/
theorem tendstoInMeasure_const_mul_zero
    (scale : Real) (remainder : Index -> Sample -> Real)
    (hremainder :
      TendstoInMeasure sampleLaw remainder l (fun _sample => (0 : Real))) :
    TendstoInMeasure sampleLaw
      (fun index sample => scale * remainder index sample) l
      (fun _sample => (0 : Real)) := by
  by_cases hscale : scale = 0
  · subst scale
    rw [tendstoInMeasure_iff_norm]
    intro ε hε
    have hfalse : ¬ ε ≤ (0 : Real) := not_le.mpr hε
    have hfun :
        (fun index =>
          sampleLaw {sample |
            ε ≤ ‖(0 : Real) * remainder index sample - 0‖}) =
          (fun _index : Index => (0 : ENNReal)) := by
      funext index
      have hempty :
          {sample |
            ε ≤ ‖(0 : Real) * remainder index sample - 0‖} =
            (∅ : Set Sample) := by
        ext sample
        simp [hfalse]
      rw [hempty]
      simp
    rw [hfun]
    exact tendsto_const_nhds
  · rw [tendstoInMeasure_iff_norm] at hremainder ⊢
    intro ε hε
    have hnorm_pos : 0 < ‖scale‖ := norm_pos_iff.mpr hscale
    have hdelta_pos : 0 < ε / ‖scale‖ := div_pos hε hnorm_pos
    have hbase := hremainder (ε / ‖scale‖) hdelta_pos
    have hsame :
        (fun index =>
          sampleLaw {sample |
            ε ≤ ‖scale * remainder index sample - 0‖}) =
          (fun index =>
            sampleLaw {sample |
              ε / ‖scale‖ ≤ ‖remainder index sample - 0‖}) := by
      funext index
      congr 1
      ext sample
      simp only [Set.mem_setOf_eq, sub_zero]
      rw [norm_mul, div_le_iff₀ hnorm_pos]
      rw [mul_comm]
    rw [hsame]
    exact hbase

omit [MeasureTheory.IsProbabilityMeasure sampleLaw] [l.IsCountablyGenerated] in
/--
The sum of two real-valued remainders that converge to zero in probability
also converges to zero in probability.
-/
theorem tendstoInMeasure_add_zero
    (first second : Index -> Sample -> Real)
    (hfirst :
      TendstoInMeasure sampleLaw first l (fun _sample => (0 : Real)))
    (hsecond :
      TendstoInMeasure sampleLaw second l (fun _sample => (0 : Real))) :
    TendstoInMeasure sampleLaw
      (fun index sample => first index sample + second index sample) l
      (fun _sample => (0 : Real)) := by
  rw [tendstoInMeasure_iff_norm] at hfirst hsecond ⊢
  intro ε hε
  have hhalf_pos : 0 < ε / 2 := by positivity
  have hfirst_half := hfirst (ε / 2) hhalf_pos
  have hsecond_half := hsecond (ε / 2) hhalf_pos
  have hsum :
      Filter.Tendsto
        (fun index =>
          sampleLaw {sample | ε / 2 ≤ ‖first index sample - 0‖} +
            sampleLaw {sample | ε / 2 ≤ ‖second index sample - 0‖})
        l (𝓝 (0 + 0 : ENNReal)) :=
    hfirst_half.add hsecond_half
  have hsum_zero :
      Filter.Tendsto
        (fun index =>
          sampleLaw {sample | ε / 2 ≤ ‖first index sample - 0‖} +
            sampleLaw {sample | ε / 2 ≤ ‖second index sample - 0‖})
        l (𝓝 (0 : ENNReal)) := by
    simpa using hsum
  refine tendsto_of_tendsto_of_tendsto_of_le_of_le
    tendsto_const_nhds hsum_zero (fun _index => zero_le) ?_
  intro index
  calc
    sampleLaw {sample |
        ε ≤ ‖first index sample + second index sample - 0‖}
        ≤ sampleLaw
            ({sample | ε / 2 ≤ ‖first index sample - 0‖} ∪
              {sample | ε / 2 ≤ ‖second index sample - 0‖}) := by
          refine measure_mono ?_
          intro sample hlarge
          by_contra hnot
          have hnot_or :
              ¬ (sample ∈ {sample |
                    ε / 2 ≤ ‖first index sample - 0‖} ∨
                  sample ∈ {sample |
                    ε / 2 ≤ ‖second index sample - 0‖}) := by
            simpa [Set.mem_union] using hnot
          have hsmall := not_or.mp hnot_or
          have hfirst_lt : ‖first index sample - 0‖ < ε / 2 :=
            not_le.mp hsmall.1
          have hsecond_lt : ‖second index sample - 0‖ < ε / 2 :=
            not_le.mp hsmall.2
          have htri :
              ‖first index sample + second index sample - 0‖ ≤
                ‖first index sample - 0‖ +
                  ‖second index sample - 0‖ := by
            simpa [sub_zero] using
              norm_add_le (first index sample) (second index sample)
          have hsum_lt :
              ‖first index sample - 0‖ +
                  ‖second index sample - 0‖ < ε := by
            linarith
          exact (not_lt_of_ge hlarge) (lt_of_le_of_lt htri hsum_lt)
    _ ≤ sampleLaw {sample | ε / 2 ≤ ‖first index sample - 0‖} +
          sampleLaw {sample | ε / 2 ≤ ‖second index sample - 0‖} :=
        measure_union_le _ _

omit [MeasureTheory.IsProbabilityMeasure sampleLaw] [l.IsCountablyGenerated] in
/--
The difference of two real-valued remainders that converge to zero in
probability also converges to zero in probability.
-/
theorem tendstoInMeasure_sub_zero
    (first second : Index -> Sample -> Real)
    (hfirst :
      TendstoInMeasure sampleLaw first l (fun _sample => (0 : Real)))
    (hsecond :
      TendstoInMeasure sampleLaw second l (fun _sample => (0 : Real))) :
    TendstoInMeasure sampleLaw
      (fun index sample => first index sample - second index sample) l
      (fun _sample => (0 : Real)) := by
  have hneg :=
    tendstoInMeasure_neg_zero
      (sampleLaw := sampleLaw) (l := l) second hsecond
  simpa [sub_eq_add_neg] using
    tendstoInMeasure_add_zero
      (sampleLaw := sampleLaw) (l := l)
      first (fun index sample => -second index sample) hfirst hneg

omit [MeasureTheory.IsProbabilityMeasure sampleLaw] [l.IsCountablyGenerated] in
/--
Any fixed two-term real linear combination of negligible-in-probability
remainders is negligible in probability.
-/
theorem tendstoInMeasure_const_mul_add_const_mul_zero
    (firstScale secondScale : Real)
    (first second : Index -> Sample -> Real)
    (hfirst :
      TendstoInMeasure sampleLaw first l (fun _sample => (0 : Real)))
    (hsecond :
      TendstoInMeasure sampleLaw second l (fun _sample => (0 : Real))) :
    TendstoInMeasure sampleLaw
      (fun index sample =>
        firstScale * first index sample + secondScale * second index sample) l
      (fun _sample => (0 : Real)) := by
  have hfirst_scaled :=
    tendstoInMeasure_const_mul_zero
      (sampleLaw := sampleLaw) (l := l) firstScale first hfirst
  have hsecond_scaled :=
    tendstoInMeasure_const_mul_zero
      (sampleLaw := sampleLaw) (l := l) secondScale second hsecond
  exact tendstoInMeasure_add_zero
    (sampleLaw := sampleLaw) (l := l)
    (fun index sample => firstScale * first index sample)
    (fun index sample => secondScale * second index sample)
    hfirst_scaled hsecond_scaled

/--
A real-valued remainder that converges to zero in probability also converges in
distribution to the zero random variable.
-/
theorem tendstoInDistribution_zero_of_tendstoInMeasure_zero
    (remainder : Index -> Sample -> Real)
    (hremainder :
      TendstoInMeasure sampleLaw remainder l (fun _sample => (0 : Real)))
    (hremainder_meas :
      ∀ index, AEMeasurable (remainder index) sampleLaw) :
    TendstoInDistribution remainder l (fun _sample => (0 : Real))
      (fun _index => sampleLaw) sampleLaw := by
  exact hremainder.tendstoInDistribution_of_aemeasurable
    hremainder_meas (by fun_prop)

/--
A fixed scalar multiple of a real-valued `o_p(1)` remainder converges in
distribution to the zero random variable.
-/
theorem tendstoInDistribution_const_mul_zero_of_tendstoInMeasure_zero
    (scale : Real) (remainder : Index -> Sample -> Real)
    (hremainder :
      TendstoInMeasure sampleLaw remainder l (fun _sample => (0 : Real)))
    (hremainder_meas :
      ∀ index, AEMeasurable (remainder index) sampleLaw) :
    TendstoInDistribution
      (fun index sample => scale * remainder index sample) l
      (fun _sample => (0 : Real)) (fun _index => sampleLaw) sampleLaw := by
  have hscaled :=
    tendstoInMeasure_const_mul_zero
      (sampleLaw := sampleLaw) (l := l) scale remainder hremainder
  have hscaled_meas :
      ∀ index, AEMeasurable
        (fun sample => scale * remainder index sample) sampleLaw :=
    fun index => (hremainder_meas index).const_mul scale
  exact tendstoInDistribution_zero_of_tendstoInMeasure_zero
    (sampleLaw := sampleLaw) (l := l)
    (fun index sample => scale * remainder index sample)
    hscaled hscaled_meas

/--
Any fixed two-term real linear combination of two `o_p(1)` remainders
converges in distribution to the zero random variable.
-/
theorem tendstoInDistribution_const_mul_add_const_mul_zero
    (firstScale secondScale : Real)
    (first second : Index -> Sample -> Real)
    (hfirst :
      TendstoInMeasure sampleLaw first l (fun _sample => (0 : Real)))
    (hsecond :
      TendstoInMeasure sampleLaw second l (fun _sample => (0 : Real)))
    (hfirst_meas :
      ∀ index, AEMeasurable (first index) sampleLaw)
    (hsecond_meas :
      ∀ index, AEMeasurable (second index) sampleLaw) :
    TendstoInDistribution
      (fun index sample =>
        firstScale * first index sample + secondScale * second index sample) l
      (fun _sample => (0 : Real)) (fun _index => sampleLaw) sampleLaw := by
  have hlinear :=
    tendstoInMeasure_const_mul_add_const_mul_zero
      (sampleLaw := sampleLaw) (l := l)
      firstScale secondScale first second hfirst hsecond
  have hlinear_meas :
      ∀ index, AEMeasurable
        (fun sample =>
          firstScale * first index sample + secondScale * second index sample)
        sampleLaw := by
    intro index
    exact ((hfirst_meas index).const_mul firstScale).add
      ((hsecond_meas index).const_mul secondScale)
  exact tendstoInDistribution_zero_of_tendstoInMeasure_zero
    (sampleLaw := sampleLaw) (l := l)
    (fun index sample =>
      firstScale * first index sample + secondScale * second index sample)
    hlinear hlinear_meas

/--
Slutsky subtraction wrapper: subtracting a real-valued remainder converging to
zero in probability preserves the distributional limit of the main statistic.
-/
theorem tendstoInDistribution_sub_negligible_zero
    (main remainder : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hmain :
      TendstoInDistribution main l limit (fun _index => sampleLaw) limitLaw)
    (hremainder :
      TendstoInMeasure sampleLaw remainder l (fun _sample => (0 : Real)))
    (hremainder_meas :
      ∀ index, AEMeasurable (remainder index) sampleLaw) :
    TendstoInDistribution
      (fun index sample => main index sample - remainder index sample)
      l limit (fun _index => sampleLaw) limitLaw := by
  have hneg :=
    tendstoInMeasure_neg_zero
      (sampleLaw := sampleLaw) (l := l) remainder hremainder
  have hneg_meas :
      ∀ index, AEMeasurable (fun sample => -remainder index sample)
        sampleLaw := fun index => (hremainder_meas index).neg
  simpa [sub_eq_add_neg] using
    tendstoInDistribution_add_negligible_zero
      (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
      main (fun index sample => -remainder index sample) limit
      hmain hneg hneg_meas

/--
Adding a fixed scalar multiple of a negligible-in-probability remainder
preserves the distributional limit of the main statistic.
-/
theorem tendstoInDistribution_add_const_mul_negligible_zero
    (scale : Real) (main remainder : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hmain :
      TendstoInDistribution main l limit (fun _index => sampleLaw) limitLaw)
    (hremainder :
      TendstoInMeasure sampleLaw remainder l (fun _sample => (0 : Real)))
    (hremainder_meas :
      ∀ index, AEMeasurable (remainder index) sampleLaw) :
    TendstoInDistribution
      (fun index sample => main index sample + scale * remainder index sample)
      l limit (fun _index => sampleLaw) limitLaw := by
  have hscaled :=
    tendstoInMeasure_const_mul_zero
      (sampleLaw := sampleLaw) (l := l) scale remainder hremainder
  have hscaled_meas :
      ∀ index, AEMeasurable
        (fun sample => scale * remainder index sample) sampleLaw :=
    fun index => (hremainder_meas index).const_mul scale
  exact tendstoInDistribution_add_negligible_zero
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    main (fun index sample => scale * remainder index sample) limit
    hmain hscaled hscaled_meas

/--
Subtracting a fixed scalar multiple of a negligible-in-probability remainder
preserves the distributional limit of the main statistic.
-/
theorem tendstoInDistribution_sub_const_mul_negligible_zero
    (scale : Real) (main remainder : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hmain :
      TendstoInDistribution main l limit (fun _index => sampleLaw) limitLaw)
    (hremainder :
      TendstoInMeasure sampleLaw remainder l (fun _sample => (0 : Real)))
    (hremainder_meas :
      ∀ index, AEMeasurable (remainder index) sampleLaw) :
    TendstoInDistribution
      (fun index sample => main index sample - scale * remainder index sample)
      l limit (fun _index => sampleLaw) limitLaw := by
  have hscaled :=
    tendstoInMeasure_const_mul_zero
      (sampleLaw := sampleLaw) (l := l) scale remainder hremainder
  have hscaled_meas :
      ∀ index, AEMeasurable
        (fun sample => scale * remainder index sample) sampleLaw :=
    fun index => (hremainder_meas index).const_mul scale
  exact tendstoInDistribution_sub_negligible_zero
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    main (fun index sample => scale * remainder index sample) limit
    hmain hscaled hscaled_meas

/--
Adding a fixed two-term real linear combination of negligible-in-probability
remainders preserves the distributional limit of the main statistic.
-/
theorem tendstoInDistribution_add_const_mul_add_const_mul_negligible_zero
    (firstScale secondScale : Real)
    (main first second : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hmain :
      TendstoInDistribution main l limit (fun _index => sampleLaw) limitLaw)
    (hfirst :
      TendstoInMeasure sampleLaw first l (fun _sample => (0 : Real)))
    (hsecond :
      TendstoInMeasure sampleLaw second l (fun _sample => (0 : Real)))
    (hfirst_meas :
      ∀ index, AEMeasurable (first index) sampleLaw)
    (hsecond_meas :
      ∀ index, AEMeasurable (second index) sampleLaw) :
    TendstoInDistribution
      (fun index sample =>
        main index sample +
          (firstScale * first index sample + secondScale * second index sample))
      l limit (fun _index => sampleLaw) limitLaw := by
  have hlinear :=
    tendstoInMeasure_const_mul_add_const_mul_zero
      (sampleLaw := sampleLaw) (l := l)
      firstScale secondScale first second hfirst hsecond
  have hlinear_meas :
      ∀ index, AEMeasurable
        (fun sample =>
          firstScale * first index sample + secondScale * second index sample)
        sampleLaw := by
    intro index
    exact ((hfirst_meas index).const_mul firstScale).add
      ((hsecond_meas index).const_mul secondScale)
  exact tendstoInDistribution_add_negligible_zero
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    main
    (fun index sample =>
      firstScale * first index sample + secondScale * second index sample)
    limit hmain hlinear hlinear_meas

/--
Subtracting a fixed two-term real linear combination of
negligible-in-probability remainders preserves the distributional limit of the
main statistic.
-/
theorem tendstoInDistribution_sub_const_mul_add_const_mul_negligible_zero
    (firstScale secondScale : Real)
    (main first second : Index -> Sample -> Real)
    (limit : LimitSample -> Real)
    (hmain :
      TendstoInDistribution main l limit (fun _index => sampleLaw) limitLaw)
    (hfirst :
      TendstoInMeasure sampleLaw first l (fun _sample => (0 : Real)))
    (hsecond :
      TendstoInMeasure sampleLaw second l (fun _sample => (0 : Real)))
    (hfirst_meas :
      ∀ index, AEMeasurable (first index) sampleLaw)
    (hsecond_meas :
      ∀ index, AEMeasurable (second index) sampleLaw) :
    TendstoInDistribution
      (fun index sample =>
        main index sample -
          (firstScale * first index sample + secondScale * second index sample))
      l limit (fun _index => sampleLaw) limitLaw := by
  have hlinear :=
    tendstoInMeasure_const_mul_add_const_mul_zero
      (sampleLaw := sampleLaw) (l := l)
      firstScale secondScale first second hfirst hsecond
  have hlinear_meas :
      ∀ index, AEMeasurable
        (fun sample =>
          firstScale * first index sample + secondScale * second index sample)
        sampleLaw := by
    intro index
    exact ((hfirst_meas index).const_mul firstScale).add
      ((hsecond_meas index).const_mul secondScale)
  exact tendstoInDistribution_sub_negligible_zero
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    main
    (fun index sample =>
      firstScale * first index sample + secondScale * second index sample)
    limit hmain hlinear hlinear_meas

/--
Multiplying a statistic with a distributional limit by a second statistic that
converges in probability to a constant gives the corresponding product limit.
This is the Slutsky step used by studentized WDSM statistics once an inverse
standard-error estimate has a probability limit.
-/
theorem tendstoInDistribution_mul_tendstoInMeasure_const
    (main multiplier : Index -> Sample -> Real)
    (limit : LimitSample -> Real) (constant : Real)
    (hmain :
      TendstoInDistribution main l limit (fun _index => sampleLaw) limitLaw)
    (hmultiplier :
      TendstoInMeasure sampleLaw multiplier l (fun _sample => constant))
    (hmultiplier_meas :
      ∀ index, AEMeasurable (multiplier index) sampleLaw) :
    TendstoInDistribution
      (fun index sample => main index sample * multiplier index sample)
      l (fun limitSample => limit limitSample * constant)
      (fun _index => sampleLaw) limitLaw := by
  exact hmain.continuous_comp_prodMk_of_tendstoInMeasure_const
    (g := fun pair : Real × Real => pair.1 * pair.2)
    (by fun_prop) hmultiplier hmultiplier_meas

/--
Studentization wrapper: if the scaled WDSM statistic has a distributional
limit and an inverse standard-error estimate converges in probability to a
constant, then the studentized statistic has the scaled distributional limit.
-/
theorem tendstoInDistribution_studentized_of_inverseStandardError
    (scaledStatistic inverseStandardError : Index -> Sample -> Real)
    (limit : LimitSample -> Real) (inverseStandardErrorLimit : Real)
    (hscaled :
      TendstoInDistribution scaledStatistic l limit
        (fun _index => sampleLaw) limitLaw)
    (hinverse :
      TendstoInMeasure sampleLaw inverseStandardError l
        (fun _sample => inverseStandardErrorLimit))
    (hinverse_meas :
      ∀ index, AEMeasurable (inverseStandardError index) sampleLaw) :
    TendstoInDistribution
      (fun index sample =>
        scaledStatistic index sample * inverseStandardError index sample)
      l (fun limitSample => limit limitSample * inverseStandardErrorLimit)
      (fun _index => sampleLaw) limitLaw := by
  exact tendstoInDistribution_mul_tendstoInMeasure_const
    (sampleLaw := sampleLaw) (limitLaw := limitLaw) (l := l)
    scaledStatistic inverseStandardError limit inverseStandardErrorLimit
    hscaled hinverse hinverse_meas

end WDSM
end Matching
end StatInference
