import Mathlib.MeasureTheory.Integral.Layercake
import Mathlib.MeasureTheory.Integral.Lebesgue.Markov
import Mathlib.MeasureTheory.Integral.DominatedConvergence

/-!
# Tail and layer-cake wrappers

Content-based probability/measure tail-control wrappers for Billingsley
Sections 15-16 and the VdV&W empirical-process envelope-tail route.

These declarations package existing mathlib measure-theory APIs under the
`StatInference.ProbabilityMeasure` namespace.  They are support lemmas, not
source-exact Billingsley theorem reports.
-/

namespace StatInference
namespace ProbabilityMeasure

open MeasureTheory Filter
open scoped ENNReal Topology

universe u v

/-- Layer-cake / tail-probability formula with strict real tail events. -/
theorem integral_eq_integral_tail_lt
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω} {X : Ω -> ℝ}
    (hX_integrable : Integrable X μ) (hX_nonneg : 0 ≤ᵐ[μ] X) :
    ∫ ω, X ω ∂μ =
      ∫ t in Set.Ioi (0 : ℝ), μ.real {ω : Ω | t < X ω} := by
  exact hX_integrable.integral_eq_integral_meas_lt hX_nonneg

/-- Layer-cake / tail-probability formula with non-strict real tail events. -/
theorem integral_eq_integral_tail_le
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω} {X : Ω -> ℝ}
    (hX_integrable : Integrable X μ) (hX_nonneg : 0 ≤ᵐ[μ] X) :
    ∫ ω, X ω ∂μ =
      ∫ t in Set.Ioi (0 : ℝ), μ.real {ω : Ω | t ≤ X ω} := by
  exact hX_integrable.integral_eq_integral_meas_le hX_nonneg

/-- Lebesgue-integral layer-cake formula with strict real tail events. -/
theorem lintegral_eq_lintegral_tail_lt
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω} {X : Ω -> ℝ}
    (hX_nonneg : 0 ≤ᵐ[μ] X) (hX_measurable : AEMeasurable X μ) :
    (∫⁻ ω, ENNReal.ofReal (X ω) ∂μ) =
      ∫⁻ t in Set.Ioi (0 : ℝ), μ {ω : Ω | t < X ω} := by
  exact MeasureTheory.lintegral_eq_lintegral_meas_lt μ hX_nonneg hX_measurable

/-- Lebesgue-integral layer-cake formula with non-strict real tail events. -/
theorem lintegral_eq_lintegral_tail_le
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω} {X : Ω -> ℝ}
    (hX_nonneg : 0 ≤ᵐ[μ] X) (hX_measurable : AEMeasurable X μ) :
    (∫⁻ ω, ENNReal.ofReal (X ω) ∂μ) =
      ∫⁻ t in Set.Ioi (0 : ℝ), μ {ω : Ω | t ≤ X ω} := by
  exact MeasureTheory.lintegral_eq_lintegral_meas_le μ hX_nonneg hX_measurable

/--
Tail-integral monotonicity: a pointwise tail majorant over `t > 0` bounds the
expectation of a nonnegative integrable random variable.
-/
theorem integral_le_integral_tail_bound
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {X : Ω -> ℝ} {tailBound : ℝ -> ℝ}
    (hX_integrable : Integrable X μ)
    (hX_nonneg : 0 ≤ᵐ[μ] X)
    (hbound_integrable : IntegrableOn tailBound (Set.Ioi (0 : ℝ)) volume)
    (hbound : ∀ t ∈ Set.Ioi (0 : ℝ),
      μ.real {ω : Ω | t ≤ X ω} ≤ tailBound t) :
    ∫ ω, X ω ∂μ ≤ ∫ t in Set.Ioi (0 : ℝ), tailBound t := by
  rw [integral_eq_integral_tail_le hX_integrable hX_nonneg]
  refine integral_mono_of_nonneg
    (μ := volume.restrict (Set.Ioi (0 : ℝ)))
    (f := fun t => μ.real {ω : Ω | t ≤ X ω})
    (g := tailBound) ?_ hbound_integrable ?_
  · exact ae_of_all _ fun _ => measureReal_nonneg
  · exact (ae_restrict_mem measurableSet_Ioi).mono fun t ht => hbound t ht

/--
Split-at-radius tail-integral bound for a probability measure.

For `0 <= r`, the interval `(0, r]` contributes at most `r`, and the tail over
`(r, ∞)` is controlled by the supplied tail majorant.
-/
theorem probability_integral_le_radius_add_integral_tail_bound
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ]
    {X : Ω -> ℝ} {tailBound : ℝ -> ℝ} {r : ℝ}
    (hr : 0 ≤ r)
    (hX_integrable : Integrable X μ)
    (hX_nonneg : 0 ≤ᵐ[μ] X)
    (hbound_integrable : IntegrableOn tailBound (Set.Ioi r) volume)
    (hbound : ∀ t ∈ Set.Ioi r,
      μ.real {ω : Ω | t ≤ X ω} ≤ tailBound t) :
    ∫ ω, X ω ∂μ ≤ r + ∫ t in Set.Ioi r, tailBound t := by
  let tail : ℝ -> ℝ := fun t => μ.real {ω : Ω | t ≤ X ω}
  have htailMeasurable : Measurable tail := by
    refine Antitone.measurable ?_
    intro s t hst
    exact measureReal_mono (fun ω hω => le_trans hst hω)
  have htailAEStrongly : AEStronglyMeasurable tail volume :=
    htailMeasurable.aestronglyMeasurable
  have htailLeftIntegrable : IntegrableOn tail (Set.Ioc (0 : ℝ) r) volume := by
    refine Measure.integrableOn_of_bounded
      (μ := volume) (s := Set.Ioc (0 : ℝ) r) (M := 1)
      measure_Ioc_lt_top.ne htailAEStrongly ?_
    exact ae_of_all _ fun _ => by
      rw [Real.norm_of_nonneg measureReal_nonneg]
      exact measureReal_le_one
  have htailRightIntegrable : IntegrableOn tail (Set.Ioi r) volume := by
    refine Integrable.mono' hbound_integrable htailAEStrongly.restrict ?_
    exact (ae_restrict_mem measurableSet_Ioi).mono fun t ht => by
      rw [Real.norm_of_nonneg measureReal_nonneg]
      exact hbound t ht
  have hsplit :
      (∫ t in Set.Ioi (0 : ℝ), tail t) =
        (∫ t in Set.Ioc (0 : ℝ) r, tail t) +
          (∫ t in Set.Ioi r, tail t) := by
    have hU : Set.Ioc (0 : ℝ) r ∪ Set.Ioi r = Set.Ioi (0 : ℝ) :=
      Set.Ioc_union_Ioi_eq_Ioi hr
    have h := setIntegral_union (μ := volume) (f := tail)
      (s := Set.Ioc (0 : ℝ) r) (t := Set.Ioi r)
      (Set.Ioc_disjoint_Ioi le_rfl) measurableSet_Ioi
      htailLeftIntegrable htailRightIntegrable
    rwa [hU] at h
  have hleft : (∫ t in Set.Ioc (0 : ℝ) r, tail t) ≤ r := by
    calc
      (∫ t in Set.Ioc (0 : ℝ) r, tail t)
          ≤ ∫ _t in Set.Ioc (0 : ℝ) r, (1 : ℝ) := by
              refine setIntegral_mono_on htailLeftIntegrable
                (integrableOn_const measure_Ioc_lt_top.ne) measurableSet_Ioc ?_
              intro _ _
              exact measureReal_le_one
      _ = volume.real (Set.Ioc (0 : ℝ) r) := by
              rw [setIntegral_one_eq_measureReal]
      _ = r := by
              rw [Real.volume_real_Ioc_of_le hr]
              ring
  have hright :
      (∫ t in Set.Ioi r, tail t) ≤ ∫ t in Set.Ioi r, tailBound t := by
    refine setIntegral_mono_on htailRightIntegrable hbound_integrable
      measurableSet_Ioi ?_
    intro t ht
    exact hbound t ht
  calc
    ∫ ω, X ω ∂μ = ∫ t in Set.Ioi (0 : ℝ), tail t := by
        rw [integral_eq_integral_tail_le hX_integrable hX_nonneg]
    _ = (∫ t in Set.Ioc (0 : ℝ) r, tail t) +
          (∫ t in Set.Ioi r, tail t) := hsplit
    _ ≤ r + ∫ t in Set.Ioi r, tailBound t := add_le_add hleft hright

/--
Bounded expectation controlled by one tail probability.

For a probability measure, if `X ≤ C`, then
`E X ≤ r + C * P(r < X)` for every nonnegative threshold `r`.
-/
theorem probability_integral_le_threshold_add_bound_mul_tail
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ]
    {X : Ω -> ℝ} {r C : ℝ}
    (hr : 0 ≤ r)
    (hX_meas : Measurable X) (hX_integrable : Integrable X μ)
    (hX_le : ∀ ω, X ω ≤ C) :
    ∫ ω, X ω ∂μ ≤ r + C * μ.real {ω : Ω | r < X ω} := by
  let event : Set Ω := {ω : Ω | r < X ω}
  have hevent : MeasurableSet event :=
    measurableSet_lt measurable_const hX_meas
  have hsplit :
      ∫ ω, X ω ∂μ =
        ∫ ω in event, X ω ∂μ + ∫ ω in eventᶜ, X ω ∂μ := by
    simpa [add_comm] using (integral_add_compl hevent hX_integrable).symm
  have htail :
      ∫ ω in event, X ω ∂μ ≤ ∫ ω in event, (fun _ : Ω => C) ω ∂μ := by
    refine setIntegral_mono_on hX_integrable.integrableOn
      (integrableOn_const (measure_ne_top μ event)) hevent ?_
    intro ω _
    exact hX_le ω
  have htail_eval :
      ∫ ω in event, (fun _ : Ω => C) ω ∂μ = μ.real event * C := by
    simp [smul_eq_mul, mul_comm]
  have htail_le :
      ∫ ω in event, X ω ∂μ ≤ C * μ.real event := by
    calc
      ∫ ω in event, X ω ∂μ ≤ ∫ ω in event, (fun _ : Ω => C) ω ∂μ := htail
      _ = μ.real event * C := htail_eval
      _ = C * μ.real event := by ring
  have hcompl :
      ∫ ω in eventᶜ, X ω ∂μ ≤ ∫ ω in eventᶜ, (fun _ : Ω => r) ω ∂μ := by
    refine setIntegral_mono_on hX_integrable.integrableOn
      (integrableOn_const (measure_ne_top μ eventᶜ)) hevent.compl ?_
    intro ω hω
    exact le_of_not_gt hω
  have hcompl_eval :
      ∫ ω in eventᶜ, (fun _ : Ω => r) ω ∂μ = μ.real eventᶜ * r := by
    simp [smul_eq_mul, mul_comm]
  have hcompl_le :
      ∫ ω in eventᶜ, X ω ∂μ ≤ r := by
    calc
      ∫ ω in eventᶜ, X ω ∂μ ≤
          ∫ ω in eventᶜ, (fun _ : Ω => r) ω ∂μ := hcompl
      _ = μ.real eventᶜ * r := hcompl_eval
      _ ≤ 1 * r := by
          exact mul_le_mul_of_nonneg_right measureReal_le_one hr
      _ = r := by ring
  calc
    ∫ ω, X ω ∂μ =
        ∫ ω in event, X ω ∂μ + ∫ ω in eventᶜ, X ω ∂μ := hsplit
    _ ≤ C * μ.real event + r := add_le_add htail_le hcompl_le
    _ = r + C * μ.real {ω : Ω | r < X ω} := by
        simp [event, add_comm]

/--
Varying-domain bounded nonnegative mean convergence from vanishing ordinary
tail probabilities.

This is a probability-measure version of the bounded part of the empirical
process outer-probability-to-mean bridge: once every process is measurable,
nonnegative, and uniformly bounded by a deterministic constant, it is enough
to show that every fixed positive tail probability tends to zero.
-/
theorem tendsto_integral_of_tendsto_measureReal_tail_zero_of_bounded_nonneg
    {ι : Type v} {Ω : ι -> Type u}
    [(i : ι) -> MeasurableSpace (Ω i)]
    (μ : (i : ι) -> Measure (Ω i))
    (hμ_prob : ∀ i, IsProbabilityMeasure (μ i))
    {l : Filter ι} {X : (i : ι) -> Ω i -> ℝ} {C : ℝ}
    (h_tail :
      ∀ r > 0,
        Tendsto (fun i => (μ i).real {ω : Ω i | r < X i ω}) l (𝓝 0))
    (hX_meas : ∀ i, Measurable (X i))
    (hX_nonneg : ∀ i (ω : Ω i), 0 ≤ X i ω)
    (hX_le : ∀ i (ω : Ω i), X i ω ≤ C) :
    Tendsto (fun i => ∫ ω, X i ω ∂(μ i)) l (𝓝 0) := by
  rw [tendsto_order]
  constructor
  · intro a ha
    exact Eventually.of_forall fun i =>
      lt_of_lt_of_le ha
        (integral_nonneg (μ := μ i) fun ω => hX_nonneg i ω)
  · intro a ha
    set r : ℝ := a / 2 with hr_def
    have hr_pos : 0 < r := by
      rw [hr_def]
      linarith
    have hr_nonneg : 0 ≤ r := hr_pos.le
    have hbound_tend :
        Tendsto
          (fun i => r + C * (μ i).real {ω : Ω i | r < X i ω})
          l (𝓝 r) := by
      simpa using tendsto_const_nhds.add ((h_tail r hr_pos).const_mul C)
    have heventually_bound :
        ∀ᶠ i in l,
          r + C * (μ i).real {ω : Ω i | r < X i ω} < a :=
      hbound_tend.eventually (eventually_lt_nhds (by linarith))
    filter_upwards [heventually_bound] with i hi
    haveI : IsProbabilityMeasure (μ i) := hμ_prob i
    have hX_integrable : Integrable (X i) (μ i) := by
      refine Integrable.of_bound (hX_meas i).aestronglyMeasurable |C| ?_
      exact ae_of_all _ fun ω => by
        rw [Real.norm_of_nonneg (hX_nonneg i ω)]
        exact (hX_le i ω).trans (le_abs_self C)
    exact
      lt_of_le_of_lt
        (probability_integral_le_threshold_add_bound_mul_tail
          (μ := μ i) (X := X i) (r := r) (C := C) hr_nonneg
          (hX_meas i) hX_integrable (hX_le i))
        hi

/-- Markov tail bound for extended nonnegative random variables. -/
theorem measure_tail_le_lintegral_div
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {X : Ω -> ℝ≥0∞} (hX_measurable : AEMeasurable X μ)
    {epsilon : ℝ≥0∞} (h_epsilon_ne_zero : epsilon ≠ 0)
    (h_epsilon_ne_top : epsilon ≠ ∞) :
    μ {ω : Ω | epsilon ≤ X ω} ≤ (∫⁻ ω, X ω ∂μ) / epsilon := by
  exact
    MeasureTheory.meas_ge_le_lintegral_div hX_measurable
      h_epsilon_ne_zero h_epsilon_ne_top

/--
Dominated-convergence tail cutoff: the ordinary integral of the upper-tail
indicator of an integrable real random variable vanishes as the cutoff tends to
infinity.

This is the reusable Section 16 support lemma needed by empirical-process
envelope truncation: once an envelope is integrable, its measurable upper-tail
ordinary integral has no residual mass at infinity.
-/
theorem integral_indicator_tail_lt_tendsto_zero_of_integrable
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω} {X : Ω -> ℝ}
    (hX_integrable : Integrable X μ) :
    Tendsto
      (fun M : ℝ => ∫ ω, Set.indicator {ω : Ω | M < X ω} X ω ∂μ)
      atTop (nhds 0) := by
  have hlim :
      ∀ᵐ ω ∂μ,
        Tendsto
          (fun M : ℝ => Set.indicator {ω' : Ω | M < X ω'} X ω)
          atTop (nhds (0 : ℝ)) := by
    refine ae_of_all μ ?_
    intro ω
    refine tendsto_const_nhds.congr' ?_
    filter_upwards [eventually_ge_atTop (X ω)] with M hM
    rw [Set.indicator_of_notMem]
    exact not_lt.mpr hM
  have hmeas :
      ∀ᶠ M in (atTop : Filter ℝ),
        AEStronglyMeasurable
          (fun ω => Set.indicator {ω' : Ω | M < X ω'} X ω) μ := by
    refine Eventually.of_forall ?_
    intro M
    exact hX_integrable.aestronglyMeasurable.indicator₀
      (nullMeasurableSet_lt
        (aemeasurable_const : AEMeasurable (fun _ : Ω => M) μ)
        hX_integrable.aemeasurable)
  have hbound :
      ∀ᶠ M in (atTop : Filter ℝ),
        ∀ᵐ ω ∂μ,
          ‖Set.indicator {ω' : Ω | M < X ω'} X ω‖ ≤ ‖X ω‖ := by
    refine Eventually.of_forall ?_
    intro M
    refine ae_of_all μ ?_
    intro ω
    by_cases hω : M < X ω
    · change ‖(if ω ∈ {ω' : Ω | M < X ω'} then X ω else 0)‖ ≤ ‖X ω‖
      simp [hω]
    · change ‖(if ω ∈ {ω' : Ω | M < X ω'} then X ω else 0)‖ ≤ ‖X ω‖
      simp [hω]
  simpa using
    (MeasureTheory.tendsto_integral_filter_of_dominated_convergence
      (μ := μ) (G := ℝ) (bound := fun ω => ‖X ω‖)
      (F := fun M ω => Set.indicator {ω' : Ω | M < X ω'} X ω)
      (f := fun _ => (0 : ℝ))
      hmeas hbound hX_integrable.norm hlim)

end ProbabilityMeasure
end StatInference
