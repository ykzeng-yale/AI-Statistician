import StatInference.EmpiricalProcess.GlivenkoCantelli
import StatInference.EmpiricalProcess.OuterExpectation
import StatInference.ProbabilityMeasure.Tail
import Mathlib.MeasureTheory.Function.UniformIntegrable

/-!
# Bridges between VdV&W outer probability and outer expectation

This module connects the empirical-process outer-probability vocabulary with
the Chapter 1.2 event-indicator outer-expectation layer.
-/

namespace StatInference

open MeasureTheory Filter

open scoped ENNReal NNReal Topology

universe u v

/--
VdV&W outer probability is the nonnegative outer expectation of the event
indicator.

This is the local bridge between the empirical-process notation
`VdVWOuterProbability` and the Chapter 1.2 indicator identity
`E* 1_B = P* B`.
-/
theorem VdVWOuterProbability_eq_outerExpectation_eventIndicator
    {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω) (event : Set Ω) :
    VdVWOuterProbability μ event =
      VdVWOuterExpectation μ (VdVWEventIndicator event) := by
  rw [VdVWOuterProbability, VdVWOuterExpectation_eventIndicator_eq_measure]

/--
Outer-almost-sure truth can be read as zero outer expectation of the
exceptional event indicator.
-/
theorem VdVWOuterAlmostSure_iff_outerExpectation_exceptional_eq_zero
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω} {predicate : Ω -> Prop} :
    VdVWOuterAlmostSure μ predicate ↔
      VdVWOuterExpectation μ (VdVWEventIndicator {ω | ¬ predicate ω}) = 0 := by
  rw [VdVWOuterAlmostSure,
    VdVWOuterProbability_eq_outerExpectation_eventIndicator]

/--
Markov-style outer-probability bound using a supplied measurable cover.

This is a Chapter 1.2 bridge from the VdV&W outer-probability notation to the
nonnegative outer-expectation/measurable-cover layer.
-/
theorem VdVWOuterProbability_lt_le_outerExpectation_div_cover
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {T : Ω -> ℝ≥0∞} (U : VdVWMeasurableCover μ T)
    {epsilon : ℝ≥0∞} (hepsilon_ne_zero : epsilon ≠ 0)
    (hepsilon_ne_top : epsilon ≠ ∞) :
    VdVWOuterProbability μ {ω | epsilon < T ω} ≤
      VdVWOuterExpectation μ T / epsilon := by
  rw [VdVWOuterProbability, VdVWOuterExpectation_eq_lintegral_cover U]
  exact
    (measure_mono fun ω hω => (le_of_lt hω).trans (U.majorizes ω)).trans
      (meas_ge_le_lintegral_div U.measurable_toFun.aemeasurable
        hepsilon_ne_zero hepsilon_ne_top)

/--
Markov-style convergence bridge from vanishing nonnegative outer expectation
to convergence in outer probability.

The theorem is stated for nonnegative real-valued processes so that the
measurable covers needed by the outer-expectation side are exactly the
`ENNReal.ofReal` covers used in the Theorem 2.4.3 finite-net assembly.
-/
theorem
    VdVWConvergesInOuterProbability_zero_of_outerExpectation_tendsto_zero_ofReal
    {Ω : Type u} {ι : Type v} [MeasurableSpace Ω] {μ : Measure Ω}
    {l : Filter ι} {Y : ι -> Ω -> ℝ}
    (hY_nonneg : ∀ i ω, 0 ≤ Y i ω)
    (U :
      ∀ i, VdVWMeasurableCover μ (fun ω => ENNReal.ofReal (Y i ω)))
    (hE :
      Tendsto
        (fun i =>
          VdVWOuterExpectation μ (fun ω => ENNReal.ofReal (Y i ω)))
        l (𝓝 0)) :
    VdVWConvergesInOuterProbability μ Y l (fun _ => 0) := by
  intro epsilon hepsilon
  have hupper :
      Tendsto
        (fun i =>
          VdVWOuterExpectation μ (fun ω => ENNReal.ofReal (Y i ω)) /
            ENNReal.ofReal epsilon)
        l (𝓝 0) := by
    have hdiv :
        Tendsto
          (fun i =>
            VdVWOuterExpectation μ (fun ω => ENNReal.ofReal (Y i ω)) /
              ENNReal.ofReal epsilon)
          l (𝓝 (0 / ENNReal.ofReal epsilon)) :=
      ENNReal.Tendsto.div_const hE
        (Or.inr (ENNReal.ofReal_ne_zero_iff.mpr hepsilon))
    simpa using hdiv
  refine
    tendsto_of_tendsto_of_tendsto_of_le_of_le'
      (show Tendsto (fun _ : ι => (0 : ℝ≥0∞)) l (𝓝 0) from
        tendsto_const_nhds)
      hupper
      (Eventually.of_forall fun _ => bot_le)
      ?_
  exact Eventually.of_forall fun i => by
    calc
      VdVWOuterProbability μ {ω | epsilon < dist (Y i ω) 0}
          =
        VdVWOuterProbability μ
          {ω | ENNReal.ofReal epsilon < ENNReal.ofReal (Y i ω)} := by
            congr 1
            ext ω
            simp only [Set.mem_setOf_eq]
            rw [Real.dist_eq, sub_zero, abs_of_nonneg (hY_nonneg i ω),
              ENNReal.ofReal_lt_ofReal_iff_of_nonneg hepsilon.le]
      _ ≤
        VdVWOuterExpectation μ (fun ω => ENNReal.ofReal (Y i ω)) /
          ENNReal.ofReal epsilon :=
            VdVWOuterProbability_lt_le_outerExpectation_div_cover (U i)
              (ENNReal.ofReal_ne_zero_iff.mpr hepsilon)
              ENNReal.ofReal_ne_top

/--
Common-domain Markov bridge from vanishing ordinary means to convergence in
outer probability for nonnegative measurable real processes.

This is the fixed-space version of
`VdVWConvergesInOuterProbabilityConst_zero_of_integral_tendsto_zero_nonneg`.
-/
theorem
    VdVWConvergesInOuterProbability_zero_of_integral_tendsto_zero_nonneg
    {Ω : Type u} {ι : Type v} [MeasurableSpace Ω] {μ : Measure Ω}
    {l : Filter ι} {Y : ι -> Ω -> ℝ}
    (hY_meas : ∀ i, Measurable (Y i))
    (hY_integrable : ∀ i, Integrable (Y i) μ)
    (hY_nonneg : ∀ i ω, 0 ≤ Y i ω)
    (hIntegral : Tendsto (fun i => ∫ ω, Y i ω ∂μ) l (𝓝 0)) :
    VdVWConvergesInOuterProbability μ Y l (fun _ => 0) := by
  let U : ∀ i, VdVWMeasurableCover μ (fun ω => ENNReal.ofReal (Y i ω)) :=
    fun i =>
      VdVWMeasurableCover.ofNullMeasurable_ofReal μ ((hY_meas i).nullMeasurable)
  refine
    VdVWConvergesInOuterProbability_zero_of_outerExpectation_tendsto_zero_ofReal
      hY_nonneg U ?_
  have hE_eq :
      (fun i => VdVWOuterExpectation μ (fun ω => ENNReal.ofReal (Y i ω))) =
        (fun i => ENNReal.ofReal (∫ ω, Y i ω ∂μ)) := by
    funext i
    exact
      VdVWOuterExpectation_eq_ofReal_integral_of_cover_integrable_nonneg
        (U i) (hY_integrable i) (ae_of_all _ (hY_nonneg i))
  rw [hE_eq]
  simpa [ENNReal.ofReal_zero] using ENNReal.tendsto_ofReal hIntegral

/--
Markov-style convergence bridge with a supplied vanishing upper bound for the
nonnegative outer expectations.
-/
theorem
    VdVWConvergesInOuterProbability_zero_of_outerExpectation_le_tendsto_zero_ofReal
    {Ω : Type u} {ι : Type v} [MeasurableSpace Ω] {μ : Measure Ω}
    {l : Filter ι} {Y : ι -> Ω -> ℝ} {bound : ι -> ℝ≥0∞}
    (hY_nonneg : ∀ i ω, 0 ≤ Y i ω)
    (U :
      ∀ i, VdVWMeasurableCover μ (fun ω => ENNReal.ofReal (Y i ω)))
    (hE_le :
      ∀ᶠ i in l,
        VdVWOuterExpectation μ (fun ω => ENNReal.ofReal (Y i ω)) ≤
          bound i)
    (hbound : Tendsto bound l (𝓝 0)) :
    VdVWConvergesInOuterProbability μ Y l (fun _ => 0) := by
  have hE :
      Tendsto
        (fun i =>
          VdVWOuterExpectation μ (fun ω => ENNReal.ofReal (Y i ω)))
        l (𝓝 0) := by
    exact
      tendsto_of_tendsto_of_tendsto_of_le_of_le'
        (show Tendsto (fun _ : ι => (0 : ℝ≥0∞)) l (𝓝 0) from
          tendsto_const_nhds)
        hbound
        (Eventually.of_forall fun _ => bot_le)
        hE_le
  exact
    VdVWConvergesInOuterProbability_zero_of_outerExpectation_tendsto_zero_ofReal
      hY_nonneg U hE

/--
Varying-sample-space version of the Markov-style convergence bridge from
vanishing nonnegative outer expectation to convergence in outer probability.
-/
theorem
    VdVWConvergesInOuterProbabilityConst_zero_of_outerExpectation_tendsto_zero_ofReal
    {ι : Type v} {Ω : ι -> Type u}
    (mΩ : (i : ι) -> MeasurableSpace (Ω i))
    (μ : (i : ι) -> @Measure (Ω i) (mΩ i))
    {l : Filter ι} {Y : (i : ι) -> Ω i -> ℝ}
    (hY_nonneg : ∀ i (ω : Ω i), 0 ≤ Y i ω)
    (U :
      ∀ i,
        @VdVWMeasurableCover (Ω i) (mΩ i) (μ i)
          (fun ω => ENNReal.ofReal (Y i ω)))
    (hE :
      Tendsto
        (fun i =>
          @VdVWOuterExpectation (Ω i) (mΩ i) (μ i)
            (fun ω => ENNReal.ofReal (Y i ω)))
        l (𝓝 0)) :
    VdVWConvergesInOuterProbabilityConst Ω mΩ μ Y l (0 : ℝ) := by
  intro epsilon hepsilon
  have hupper :
      Tendsto
        (fun i =>
          @VdVWOuterExpectation (Ω i) (mΩ i) (μ i)
              (fun ω => ENNReal.ofReal (Y i ω)) /
            ENNReal.ofReal epsilon)
        l (𝓝 0) := by
    have hdiv :
        Tendsto
          (fun i =>
            @VdVWOuterExpectation (Ω i) (mΩ i) (μ i)
                (fun ω => ENNReal.ofReal (Y i ω)) /
              ENNReal.ofReal epsilon)
          l (𝓝 (0 / ENNReal.ofReal epsilon)) :=
      ENNReal.Tendsto.div_const hE
        (Or.inr (ENNReal.ofReal_ne_zero_iff.mpr hepsilon))
    simpa using hdiv
  refine
    tendsto_of_tendsto_of_tendsto_of_le_of_le'
      (show Tendsto (fun _ : ι => (0 : ℝ≥0∞)) l (𝓝 0) from
        tendsto_const_nhds)
      hupper
      (Eventually.of_forall fun _ => bot_le)
      ?_
  exact Eventually.of_forall fun i => by
    calc
      @VdVWOuterProbability (Ω i) (mΩ i) (μ i)
          {ω | epsilon < dist (Y i ω) 0}
          =
        @VdVWOuterProbability (Ω i) (mΩ i) (μ i)
          {ω | ENNReal.ofReal epsilon < ENNReal.ofReal (Y i ω)} := by
            congr 1
            ext ω
            simp only [Set.mem_setOf_eq]
            rw [Real.dist_eq, sub_zero, abs_of_nonneg (hY_nonneg i ω),
              ENNReal.ofReal_lt_ofReal_iff_of_nonneg hepsilon.le]
      _ ≤
        @VdVWOuterExpectation (Ω i) (mΩ i) (μ i)
            (fun ω => ENNReal.ofReal (Y i ω)) /
          ENNReal.ofReal epsilon :=
            @VdVWOuterProbability_lt_le_outerExpectation_div_cover
              (Ω i) (mΩ i) (μ i)
              (fun ω => ENNReal.ofReal (Y i ω)) (U i)
              (ENNReal.ofReal epsilon)
              (ENNReal.ofReal_ne_zero_iff.mpr hepsilon)
              ENNReal.ofReal_ne_top

/--
Varying-sample-space Markov bridge from vanishing ordinary means to convergence
in outer probability for nonnegative measurable real processes.

This packages the Chapter 1.2 measurable-cover equality
`E* (ofReal Y_i) = ofReal (∫ Y_i)` with the outer-probability Markov bridge.
It is a source-side helper for Theorem 2.4.3 finite-net routes whose
Hoeffding-scale upper bounds are ordinary measurable nonnegative random
variables.
-/
theorem
    VdVWConvergesInOuterProbabilityConst_zero_of_integral_tendsto_zero_nonneg
    {ι : Type v} {Ω : ι -> Type u}
    [(i : ι) -> MeasurableSpace (Ω i)]
    (μ : (i : ι) -> Measure (Ω i))
    {l : Filter ι} {Y : (i : ι) -> Ω i -> ℝ}
    (hY_meas : ∀ i, Measurable (Y i))
    (hY_integrable : ∀ i, Integrable (Y i) (μ i))
    (hY_nonneg : ∀ i (ω : Ω i), 0 ≤ Y i ω)
    (hIntegral : Tendsto (fun i => ∫ ω, Y i ω ∂(μ i)) l (𝓝 0)) :
    VdVWConvergesInOuterProbabilityConst Ω (fun _ => inferInstance) μ Y l (0 : ℝ) := by
  let U :
      ∀ i,
        @VdVWMeasurableCover (Ω i) inferInstance (μ i)
          (fun ω => ENNReal.ofReal (Y i ω)) := fun i =>
    VdVWMeasurableCover.ofNullMeasurable_ofReal (μ i) ((hY_meas i).nullMeasurable)
  refine
    VdVWConvergesInOuterProbabilityConst_zero_of_outerExpectation_tendsto_zero_ofReal
      (fun _ => inferInstance) μ hY_nonneg U ?_
  have hE_eq :
      (fun i =>
          @VdVWOuterExpectation (Ω i) inferInstance (μ i)
            (fun ω => ENNReal.ofReal (Y i ω))) =
        (fun i => ENNReal.ofReal (∫ ω, Y i ω ∂(μ i))) := by
    funext i
    exact
      VdVWOuterExpectation_eq_ofReal_integral_of_cover_integrable_nonneg
        (U i) (hY_integrable i) (ae_of_all _ (hY_nonneg i))
  rw [hE_eq]
  simpa [ENNReal.ofReal_zero] using ENNReal.tendsto_ofReal hIntegral

/--
Varying-sample-space Markov bridge with a supplied vanishing upper bound for
the nonnegative outer expectations.
-/
theorem
    VdVWConvergesInOuterProbabilityConst_zero_of_outerExpectation_le_tendsto_zero_ofReal
    {ι : Type v} {Ω : ι -> Type u}
    (mΩ : (i : ι) -> MeasurableSpace (Ω i))
    (μ : (i : ι) -> @Measure (Ω i) (mΩ i))
    {l : Filter ι} {Y : (i : ι) -> Ω i -> ℝ} {bound : ι -> ℝ≥0∞}
    (hY_nonneg : ∀ i (ω : Ω i), 0 ≤ Y i ω)
    (U :
      ∀ i,
        @VdVWMeasurableCover (Ω i) (mΩ i) (μ i)
          (fun ω => ENNReal.ofReal (Y i ω)))
    (hE_le :
      ∀ᶠ i in l,
        @VdVWOuterExpectation (Ω i) (mΩ i) (μ i)
            (fun ω => ENNReal.ofReal (Y i ω)) ≤
          bound i)
    (hbound : Tendsto bound l (𝓝 0)) :
    VdVWConvergesInOuterProbabilityConst Ω mΩ μ Y l (0 : ℝ) := by
  have hE :
      Tendsto
        (fun i =>
          @VdVWOuterExpectation (Ω i) (mΩ i) (μ i)
            (fun ω => ENNReal.ofReal (Y i ω)))
        l (𝓝 0) := by
    exact
      tendsto_of_tendsto_of_tendsto_of_le_of_le'
        (show Tendsto (fun _ : ι => (0 : ℝ≥0∞)) l (𝓝 0) from
          tendsto_const_nhds)
        hbound
        (Eventually.of_forall fun _ => bot_le)
        hE_le
  exact
    VdVWConvergesInOuterProbabilityConst_zero_of_outerExpectation_tendsto_zero_ofReal
      mΩ μ hY_nonneg U hE

/--
Nonnegative variable-domain convergence in outer probability is monotone.

If `0 <= X_i <= Y_i` eventually pointwise and `Y_i -> 0` in outer
probability, then `X_i -> 0` in outer probability.  This is a small
Theorem 2.4.3 support primitive for replacing an externally supplied empirical
cover cardinality by the selected least finite-cover cardinality.
-/
theorem
    VdVWConvergesInOuterProbabilityConst_zero_of_nonneg_le
    {ι : Type v} {Ω : ι -> Type u}
    (mΩ : (i : ι) -> MeasurableSpace (Ω i))
    (μ : (i : ι) -> @Measure (Ω i) (mΩ i))
    {l : Filter ι} {X Y : (i : ι) -> Ω i -> ℝ}
    (hX_nonneg : ∀ i (ω : Ω i), 0 ≤ X i ω)
    (hXY : ∀ᶠ i in l, ∀ ω : Ω i, X i ω ≤ Y i ω)
    (hY :
      VdVWConvergesInOuterProbabilityConst Ω mΩ μ Y l (0 : ℝ)) :
    VdVWConvergesInOuterProbabilityConst Ω mΩ μ X l (0 : ℝ) := by
  intro epsilon hepsilon
  have hY_epsilon := hY epsilon hepsilon
  refine
    tendsto_of_tendsto_of_tendsto_of_le_of_le'
      (show Tendsto (fun _ : ι => (0 : ℝ≥0∞)) l (𝓝 0) from
        tendsto_const_nhds)
      hY_epsilon
      (Eventually.of_forall fun _ => bot_le)
      ?_
  filter_upwards [hXY] with i hXY_i
  dsimp [VdVWOuterProbability]
  refine measure_mono ?_
  intro ω hω
  have hX_lt : epsilon < X i ω := by
    simpa [Real.dist_eq, sub_zero, abs_of_nonneg (hX_nonneg i ω)] using hω
  have hY_lt : epsilon < Y i ω := lt_of_lt_of_le hX_lt (hXY_i ω)
  have hY_abs : epsilon < |Y i ω| := lt_of_lt_of_le hY_lt (le_abs_self _)
  simpa [Real.dist_eq, sub_zero] using hY_abs

/--
Bounded nonnegative convergence in varying-domain outer probability implies
ordinary mean convergence.

This is a uniform-integrability-style bridge for bounded nonnegative real
processes.  It is intentionally stated with an explicit deterministic bound:
outer-probability convergence alone is not enough to force convergence of
expectations.
-/
theorem
    tendsto_integral_of_VdVWConvergesInOuterProbabilityConst_zero_of_bounded_nonneg
    {ι : Type v} {Ω : ι -> Type u}
    [(i : ι) -> MeasurableSpace (Ω i)]
    (μ : (i : ι) -> Measure (Ω i))
    (hμ_prob : ∀ i, IsProbabilityMeasure (μ i))
    {l : Filter ι} {Y : (i : ι) -> Ω i -> ℝ} {C : ℝ}
    (hY :
      VdVWConvergesInOuterProbabilityConst Ω (fun _ => inferInstance) μ Y l
        (0 : ℝ))
    (hY_meas : ∀ i, Measurable (Y i))
    (hY_integrable : ∀ i, Integrable (Y i) (μ i))
    (hY_nonneg : ∀ i (ω : Ω i), 0 ≤ Y i ω)
    (hY_le : ∀ i (ω : Ω i), Y i ω ≤ C) :
    Tendsto (fun i => ∫ ω, Y i ω ∂(μ i)) l (𝓝 0) := by
  rw [tendsto_order]
  constructor
  · intro a ha
    exact Eventually.of_forall fun i =>
      lt_of_lt_of_le ha
        (integral_nonneg (μ := μ i) fun ω => hY_nonneg i ω)
  · intro a ha
    set r : ℝ := a / 2 with hr_def
    have hr_pos : 0 < r := by
      rw [hr_def]
      linarith
    have hr_nonneg : 0 ≤ r := hr_pos.le
    let tail : ι -> ℝ :=
      fun i => (μ i).real {ω : Ω i | r < Y i ω}
    have htail_enn :
        Tendsto
          (fun i =>
            @VdVWOuterProbability (Ω i) inferInstance (μ i)
              {ω : Ω i | r < Y i ω})
          l (𝓝 0) := by
      have hdist :
          (fun i =>
            @VdVWOuterProbability (Ω i) inferInstance (μ i)
              {ω : Ω i | r < Y i ω}) =
          (fun i =>
            @VdVWOuterProbability (Ω i) inferInstance (μ i)
              {ω : Ω i | r < dist (Y i ω) (0 : ℝ)}) := by
        funext i
        congr 1
        ext ω
        simp only [Set.mem_setOf_eq]
        rw [Real.dist_eq, sub_zero, abs_of_nonneg (hY_nonneg i ω)]
      simpa [hdist] using hY r hr_pos
    have htail_real : Tendsto tail l (𝓝 0) := by
      have htoReal :
          Tendsto
            (fun i =>
              ENNReal.toReal
                (@VdVWOuterProbability (Ω i) inferInstance (μ i)
                  {ω : Ω i | r < Y i ω}))
            l (𝓝 0) :=
        (ENNReal.tendsto_toReal ENNReal.zero_ne_top).comp htail_enn
      simpa [tail, VdVWOuterProbability, measureReal_def] using htoReal
    have hbound_tend :
        Tendsto (fun i => r + C * tail i) l (𝓝 r) := by
      simpa using tendsto_const_nhds.add (htail_real.const_mul C)
    have heventually_bound :
        ∀ᶠ i in l, r + C * tail i < a :=
      hbound_tend.eventually (eventually_lt_nhds (by linarith))
    filter_upwards [heventually_bound] with i hi
    haveI : IsProbabilityMeasure (μ i) := hμ_prob i
    exact
      lt_of_le_of_lt
        (_root_.StatInference.ProbabilityMeasure.probability_integral_le_threshold_add_bound_mul_tail
          (μ := μ i) (X := Y i) (r := r) (C := C) hr_nonneg
          (hY_meas i) (hY_integrable i) (hY_le i))
        hi

/--
A uniform deterministic bound supplies the variable-domain tail-expectation
condition used by the explicit UI route below.

This is the small support lemma that keeps later empirical-process finite-net
arguments honest: boundedness is a sufficient tail/UI input, but it is recorded
as such instead of being hidden inside a fixed-domain Vitali theorem.
-/
theorem tailExpectation_condition_of_eventual_bound
    {ι : Type v} {Ω : ι -> Type u}
    [(i : ι) -> MeasurableSpace (Ω i)]
    (μ : (i : ι) -> Measure (Ω i))
    {l : Filter ι} {Y : (i : ι) -> Ω i -> ℝ} {C : ℝ}
    (hC_nonneg : 0 ≤ C)
    (hY_le : ∀ᶠ i in l, ∀ ω : Ω i, Y i ω ≤ C) :
    ∀ ε > 0, ∃ R, 0 ≤ R ∧
      ∀ᶠ i in l,
        ∫ ω,
          Set.indicator {ω' : Ω i | R < Y i ω'} (Y i) ω ∂(μ i) ≤ ε := by
  intro ε hε_pos
  refine ⟨C, hC_nonneg, ?_⟩
  filter_upwards [hY_le] with i hi
  have hzero :
      (fun ω : Ω i =>
        Set.indicator {ω' : Ω i | C < Y i ω'} (Y i) ω) =
        fun _ => 0 := by
    funext ω
    have hnot : ¬ C < Y i ω := not_lt_of_ge (hi ω)
    simp [Set.indicator, hnot]
  rw [hzero]
  simpa using hε_pos.le

/--
A uniform pointwise `nnnorm` bound supplies the fixed-domain `eLpNorm` large
tail condition used by mathlib's `MeasureTheory.unifIntegrable_of`.

This records the deterministic support route separately from the theorem
endpoint: if later entropy/cardinality arguments give a uniform bound on a
family of real-valued statistics, then the large-tail `L¹` input for uniform
integrability is immediate.
-/
theorem eLpNorm_one_tail_condition_of_nnnorm_bound
    {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω)
    {Y : ℕ -> Ω -> ℝ}
    (hY_bound : ∃ K : ℝ≥0, ∀ n ω, ‖Y n ω‖₊ ≤ K) :
    ∀ ε : ℝ, 0 < ε -> ∃ C : ℝ≥0,
      ∀ n,
        eLpNorm ({ω : Ω | C ≤ ‖Y n ω‖₊}.indicator (Y n))
          (1 : ℝ≥0∞) μ ≤ ENNReal.ofReal ε := by
  obtain ⟨K, hK⟩ := hY_bound
  intro ε hε_pos
  refine ⟨K + 1, ?_⟩
  intro n
  have hzero :
      ({ω : Ω | K + 1 ≤ ‖Y n ω‖₊}.indicator (Y n)) =
        fun _ => 0 := by
    funext ω
    have hK_lt : K < K + 1 := lt_add_of_pos_right K zero_lt_one
    have hnot : ¬ K + 1 ≤ ‖Y n ω‖₊ := by
      exact fun htail => not_le_of_gt (lt_of_le_of_lt (hK n ω) hK_lt) htail
    simp [Set.indicator, hnot]
  rw [hzero]
  simp

/--
Vanishing ordinary means supply the varying-domain tail-expectation
condition for nonnegative processes.

This is the L1-strengthened alternative to the bounded-tail route: if
`∫ Y_i -> 0` and `0 <= Y_i`, then the large-tail expectation is small by
taking cutoff `R = 0`.
-/
theorem tailExpectation_condition_of_integral_tendsto_zero_nonneg
    {ι : Type v} {Ω : ι -> Type u}
    [(i : ι) -> MeasurableSpace (Ω i)]
    (μ : (i : ι) -> Measure (Ω i))
    {l : Filter ι} {Y : (i : ι) -> Ω i -> ℝ}
    (hY_nonneg : ∀ i (ω : Ω i), 0 ≤ Y i ω)
    (hIntegral : Tendsto (fun i => ∫ ω, Y i ω ∂(μ i)) l (𝓝 0)) :
    ∀ ε > 0, ∃ R, 0 ≤ R ∧
      ∀ᶠ i in l,
        ∫ ω,
          Set.indicator {ω' : Ω i | R < Y i ω'} (Y i) ω ∂(μ i) ≤ ε := by
  intro ε hε_pos
  refine ⟨0, le_rfl, ?_⟩
  have heventually :
      ∀ᶠ i in l, ∫ ω, Y i ω ∂(μ i) < ε :=
    hIntegral.eventually (eventually_lt_nhds hε_pos)
  filter_upwards [heventually] with i hi
  have hindicator_eq :
      (fun ω : Ω i =>
        Set.indicator {ω' : Ω i | (0 : ℝ) < Y i ω'} (Y i) ω) =
        Y i := by
    funext ω
    by_cases hpos : 0 < Y i ω
    · simp [Set.indicator, hpos]
    · have hzero : Y i ω = 0 := le_antisymm (le_of_not_gt hpos) (hY_nonneg i ω)
      simp [Set.indicator, hzero]
  rw [hindicator_eq]
  exact hi.le

/--
Fixed-domain Vitali bridge in VdV&W notation.

On one probability space, common-domain convergence in outer probability plus
mathlib uniform integrability gives `L1` convergence to zero.  This records the
usable fixed-domain theorem exposed by the search-first gate; the
Theorem 2.4.3 random-entropy problem is harder because its empirical-cover
cardinalities live on varying sample spaces.
-/
theorem tendsto_eLpNorm_one_of_VdVWConvergesInOuterProbability_zero_of_unifIntegrable
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω} [IsFiniteMeasure μ]
    {Y : ℕ -> Ω -> ℝ}
    (hY : VdVWConvergesInOuterProbability μ Y atTop (fun _ => (0 : ℝ)))
    (hY_meas : ∀ n, AEStronglyMeasurable (Y n) μ)
    (hY_ui : UnifIntegrable Y 1 μ) :
    Tendsto (fun n => eLpNorm (Y n) 1 μ) atTop (𝓝 0) := by
  have hInMeasure :
      MeasureTheory.TendstoInMeasure μ Y atTop (fun _ => (0 : ℝ)) :=
    tendstoInMeasure_of_vdVWConvergesInOuterProbability hY
  have hLp :
      Tendsto (fun n => eLpNorm (Y n - fun _ => (0 : ℝ)) 1 μ) atTop (𝓝 0) :=
    MeasureTheory.tendsto_Lp_finite_of_tendstoInMeasure
      (μ := μ) (p := (1 : ℝ≥0∞)) (g := fun _ => (0 : ℝ))
      le_rfl ENNReal.one_ne_top hY_meas MemLp.zero' hY_ui hInMeasure
  have hEq :
      (fun n => eLpNorm (Y n - fun _ => (0 : ℝ)) 1 μ) =
        fun n => eLpNorm (Y n) 1 μ := by
    funext n
    exact eLpNorm_congr_ae (Eventually.of_forall fun ω => by simp)
  simpa [hEq] using hLp

/--
Fixed-domain nonnegative mean-convergence consumer for the Vitali/UI bridge.

This is the ordinary-expectation version of
`tendsto_eLpNorm_one_of_VdVWConvergesInOuterProbability_zero_of_unifIntegrable`:
for nonnegative integrable processes on one sample space, the `L1` convergence
from Vitali is exactly convergence of ordinary means to zero.
-/
theorem tendsto_integral_of_VdVWConvergesInOuterProbability_zero_of_unifIntegrable_nonneg
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω} [IsFiniteMeasure μ]
    {Y : ℕ -> Ω -> ℝ}
    (hY : VdVWConvergesInOuterProbability μ Y atTop (fun _ => (0 : ℝ)))
    (hY_meas : ∀ n, AEStronglyMeasurable (Y n) μ)
    (hY_integrable : ∀ n, Integrable (Y n) μ)
    (hY_nonneg : ∀ n ω, 0 ≤ Y n ω)
    (hY_ui : UnifIntegrable Y 1 μ) :
    Tendsto (fun n => ∫ ω, Y n ω ∂μ) atTop (𝓝 0) := by
  have hLp :
      Tendsto (fun n => eLpNorm (Y n) 1 μ) atTop (𝓝 0) :=
    tendsto_eLpNorm_one_of_VdVWConvergesInOuterProbability_zero_of_unifIntegrable
      hY hY_meas hY_ui
  have hLpReal :
      Tendsto (fun n => (eLpNorm (Y n) 1 μ).toReal) atTop (𝓝 0) :=
    (ENNReal.tendsto_toReal ENNReal.zero_ne_top).comp hLp
  have hEq :
      (fun n => (eLpNorm (Y n) 1 μ).toReal) =
        fun n => ∫ ω, Y n ω ∂μ := by
    funext n
    have h_nonneg_ae : 0 ≤ᵐ[μ] Y n :=
      ae_of_all μ (hY_nonneg n)
    have h_integral_nonneg : 0 ≤ ∫ ω, Y n ω ∂μ :=
      integral_nonneg (μ := μ) (hY_nonneg n)
    have h_norm :
        (∫⁻ ω, ‖Y n ω‖ₑ ∂μ) =
          ∫⁻ ω, ENNReal.ofReal (Y n ω) ∂μ := by
      refine lintegral_congr_ae ?_
      filter_upwards with ω
      rw [Real.enorm_eq_ofReal_abs, abs_of_nonneg (hY_nonneg n ω)]
    have h_ofReal :
        ENNReal.ofReal (∫ ω, Y n ω ∂μ) = eLpNorm (Y n) 1 μ := by
      rw [eLpNorm_one_eq_lintegral_enorm, h_norm]
      exact (MeasureTheory.ofReal_integral_eq_lintegral_ofReal
        (hY_integrable n) h_nonneg_ae)
    rw [← ENNReal.toReal_ofReal h_integral_nonneg, h_ofReal]
  simpa [hEq] using hLpReal

/--
Fixed-domain signed mean-convergence consumer for the Vitali/UI bridge.

For integrable real processes on one sample space, common-domain convergence in
outer probability to zero plus uniform integrability implies convergence of
ordinary signed means to zero.  The proof uses the preceding `L1` bridge and
the standard bound `‖∫ Y_n‖ ≤ ∫ ‖Y_n‖`.
-/
theorem tendsto_integral_of_VdVWConvergesInOuterProbability_zero_of_unifIntegrable
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω} [IsFiniteMeasure μ]
    {Y : ℕ -> Ω -> ℝ}
    (hY : VdVWConvergesInOuterProbability μ Y atTop (fun _ => (0 : ℝ)))
    (hY_meas : ∀ n, AEStronglyMeasurable (Y n) μ)
    (hY_integrable : ∀ n, Integrable (Y n) μ)
    (hY_ui : UnifIntegrable Y 1 μ) :
    Tendsto (fun n => ∫ ω, Y n ω ∂μ) atTop (𝓝 0) := by
  have hLp :
      Tendsto (fun n => eLpNorm (Y n) 1 μ) atTop (𝓝 0) :=
    tendsto_eLpNorm_one_of_VdVWConvergesInOuterProbability_zero_of_unifIntegrable
      hY hY_meas hY_ui
  have hLpReal :
      Tendsto (fun n => (eLpNorm (Y n) 1 μ).toReal) atTop (𝓝 0) :=
    (ENNReal.tendsto_toReal ENNReal.zero_ne_top).comp hLp
  rw [tendsto_zero_iff_norm_tendsto_zero]
  refine squeeze_zero (fun n => norm_nonneg _) ?_ hLpReal
  intro n
  have h_norm_eq :
      ∫ ω, ‖Y n ω‖ ∂μ = (eLpNorm (Y n) 1 μ).toReal := by
    have h_integral_norm_nonneg : 0 ≤ ∫ ω, ‖Y n ω‖ ∂μ :=
      integral_nonneg (μ := μ) fun ω => norm_nonneg (Y n ω)
    have h_ofReal :
        ENNReal.ofReal (∫ ω, ‖Y n ω‖ ∂μ) = eLpNorm (Y n) 1 μ := by
      rw [eLpNorm_one_eq_lintegral_enorm]
      exact MeasureTheory.ofReal_integral_norm_eq_lintegral_enorm (hY_integrable n)
    rw [← ENNReal.toReal_ofReal h_integral_norm_nonneg, h_ofReal]
  calc
    ‖∫ ω, Y n ω ∂μ‖ ≤ ∫ ω, ‖Y n ω‖ ∂μ :=
      norm_integral_le_integral_norm _
    _ = (eLpNorm (Y n) 1 μ).toReal := h_norm_eq

/--
A varying-domain perturbation rule for convergence in outer probability to
zero.

If `X_i` is eventually bounded in distance by two real error processes
`Y_i + Z_i`, and both errors converge to zero in VdV&W outer probability, then
`X_i` converges to zero as well.  This is the local replacement for the
missing VdV&W arbitrary-map perturbation API needed by the Theorem 2.4.3
untruncation step.
-/
theorem
    VdVWConvergesInOuterProbabilityConst_zero_of_eventual_dist_le_add_errors
    {ι : Type v} {Ω : ι -> Type u}
    [(i : ι) -> MeasurableSpace (Ω i)]
    (μ : (i : ι) -> Measure (Ω i))
    {l : Filter ι} {X Y Z : (i : ι) -> Ω i -> ℝ}
    (hY :
      VdVWConvergesInOuterProbabilityConst Ω (fun _ => inferInstance) μ Y l
        (0 : ℝ))
    (hZ :
      VdVWConvergesInOuterProbabilityConst Ω (fun _ => inferInstance) μ Z l
        (0 : ℝ))
    (hbound :
      ∀ᶠ i in l, ∀ ω : Ω i, dist (X i ω) (0 : ℝ) ≤ Y i ω + Z i ω) :
    VdVWConvergesInOuterProbabilityConst Ω (fun _ => inferInstance) μ X l
      (0 : ℝ) := by
  intro ε hε
  have hε2 : 0 < ε / 2 := half_pos hε
  have hYt := hY (ε / 2) hε2
  have hZt := hZ (ε / 2) hε2
  have hsum :
      Tendsto
        (fun i =>
          @VdVWOuterProbability (Ω i) inferInstance (μ i)
              {ω | ε / 2 < dist (Y i ω) (0 : ℝ)} +
            @VdVWOuterProbability (Ω i) inferInstance (μ i)
              {ω | ε / 2 < dist (Z i ω) (0 : ℝ)})
        l (𝓝 0) := by
    simpa using hYt.add hZt
  refine
    tendsto_of_tendsto_of_tendsto_of_le_of_le'
      (show Tendsto (fun _ : ι => (0 : ℝ≥0∞)) l (𝓝 0) from
        tendsto_const_nhds)
      hsum
      (Eventually.of_forall fun _ => bot_le)
      ?_
  filter_upwards [hbound] with i hi
  calc
    @VdVWOuterProbability (Ω i) inferInstance (μ i)
        {ω | ε < dist (X i ω) (0 : ℝ)}
        ≤ @VdVWOuterProbability (Ω i) inferInstance (μ i)
            ({ω | ε / 2 < dist (Y i ω) (0 : ℝ)} ∪
              {ω | ε / 2 < dist (Z i ω) (0 : ℝ)}) := by
            dsimp [VdVWOuterProbability]
            refine measure_mono ?_
            intro ω hω
            by_cases hYbad : ε / 2 < dist (Y i ω) (0 : ℝ)
            · exact Or.inl hYbad
            · refine Or.inr ?_
              by_contra hZbad
              have hXlt : ε < dist (X i ω) (0 : ℝ) := by simpa using hω
              have hYle : Y i ω ≤ ε / 2 := by
                calc
                  Y i ω ≤ |Y i ω| := le_abs_self _
                  _ = dist (Y i ω) (0 : ℝ) := by
                        rw [Real.dist_eq, sub_zero]
                  _ ≤ ε / 2 := le_of_not_gt hYbad
              have hZle : Z i ω ≤ ε / 2 := by
                calc
                  Z i ω ≤ |Z i ω| := le_abs_self _
                  _ = dist (Z i ω) (0 : ℝ) := by
                        rw [Real.dist_eq, sub_zero]
                  _ ≤ ε / 2 := le_of_not_gt hZbad
              have hXle : dist (X i ω) (0 : ℝ) ≤ Y i ω + Z i ω :=
                hi ω
              linarith
    _ ≤ @VdVWOuterProbability (Ω i) inferInstance (μ i)
            {ω | ε / 2 < dist (Y i ω) (0 : ℝ)} +
          @VdVWOuterProbability (Ω i) inferInstance (μ i)
            {ω | ε / 2 < dist (Z i ω) (0 : ℝ)} := by
            dsimp [VdVWOuterProbability]
            exact measure_union_le _ _

/--
Variable-domain tail-expectation convergence in outer probability implies
ordinary mean convergence for nonnegative real processes.

This is the varying-sample-space replacement for a fixed-domain Vitali/UI
argument.  The tail-expectation condition is explicit: after a large cutoff,
the expectations of the upper tails are eventually uniformly small.
-/
theorem
    tendsto_integral_of_VdVWConvergesInOuterProbabilityConst_zero_of_tailExpectation_nonneg
    {ι : Type v} {Ω : ι -> Type u}
    [(i : ι) -> MeasurableSpace (Ω i)]
    (μ : (i : ι) -> Measure (Ω i))
    (hμ_prob : ∀ i, IsProbabilityMeasure (μ i))
    {l : Filter ι} {Y : (i : ι) -> Ω i -> ℝ}
    (hY :
      VdVWConvergesInOuterProbabilityConst Ω (fun _ => inferInstance) μ Y l
        (0 : ℝ))
    (hY_meas : ∀ i, Measurable (Y i))
    (hY_integrable : ∀ i, Integrable (Y i) (μ i))
    (hY_nonneg : ∀ i (ω : Ω i), 0 ≤ Y i ω)
    (hTail :
      ∀ ε > 0, ∃ R, 0 ≤ R ∧
        ∀ᶠ i in l,
          ∫ ω, Set.indicator {ω' : Ω i | R < Y i ω'} (Y i) ω ∂(μ i) ≤ ε) :
    Tendsto (fun i => ∫ ω, Y i ω ∂(μ i)) l (𝓝 0) := by
  rw [tendsto_order]
  constructor
  · intro a ha
    exact Eventually.of_forall fun i =>
      lt_of_lt_of_le ha
        (integral_nonneg (μ := μ i) fun ω => hY_nonneg i ω)
  · intro a ha
    set η : ℝ := a / 4 with hη_def
    have hη_pos : 0 < η := by
      rw [hη_def]
      linarith
    have hη_nonneg : 0 ≤ η := hη_pos.le
    obtain ⟨R, hR_nonneg, htail_eventually⟩ := hTail η hη_pos
    let probTail : ι -> ℝ := fun i => (μ i).real {ω : Ω i | η < Y i ω}
    have hprob_enn :
        Tendsto
          (fun i =>
            @VdVWOuterProbability (Ω i) inferInstance (μ i)
              {ω : Ω i | η < Y i ω})
          l (𝓝 0) := by
      have hdist :
          (fun i =>
            @VdVWOuterProbability (Ω i) inferInstance (μ i)
              {ω : Ω i | η < Y i ω}) =
          (fun i =>
            @VdVWOuterProbability (Ω i) inferInstance (μ i)
              {ω : Ω i | η < dist (Y i ω) (0 : ℝ)}) := by
        funext i
        congr 1
        ext ω
        simp only [Set.mem_setOf_eq]
        rw [Real.dist_eq, sub_zero, abs_of_nonneg (hY_nonneg i ω)]
      simpa [hdist] using hY η hη_pos
    have hprob_real : Tendsto probTail l (𝓝 0) := by
      have htoReal :
          Tendsto
            (fun i =>
              ENNReal.toReal
                (@VdVWOuterProbability (Ω i) inferInstance (μ i)
                  {ω : Ω i | η < Y i ω}))
            l (𝓝 0) :=
        (ENNReal.tendsto_toReal ENNReal.zero_ne_top).comp hprob_enn
      simpa [probTail, VdVWOuterProbability, measureReal_def] using htoReal
    have hbody_prob_small :
        ∀ᶠ i in l, R * probTail i < η :=
      (hprob_real.const_mul R).eventually
        (eventually_lt_nhds (by simpa [η] using hη_pos))
    filter_upwards [htail_eventually, hbody_prob_small] with i htail_i hprob_i
    haveI : IsProbabilityMeasure (μ i) := hμ_prob i
    let tailSet : Set (Ω i) := {ω : Ω i | R < Y i ω}
    let body : Ω i -> ℝ := Set.indicator tailSetᶜ (Y i)
    have htailSet : MeasurableSet tailSet :=
      measurableSet_lt measurable_const (hY_meas i)
    have hbody_meas : Measurable body :=
      (hY_meas i).indicator htailSet.compl
    have hbody_integrable : Integrable body (μ i) :=
      (hY_integrable i).indicator htailSet.compl
    have hbody_le : ∀ ω, body ω ≤ R := by
      intro ω
      by_cases hω : ω ∈ tailSetᶜ
      · have hnot : ¬ R < Y i ω := by
          simpa [tailSet] using hω
        simpa [body, Set.indicator_of_mem hω] using le_of_not_gt hnot
      · simpa [body, Set.indicator_of_notMem hω] using hR_nonneg
    have hbody_tail_subset :
        {ω : Ω i | η < body ω} ⊆ {ω : Ω i | η < Y i ω} := by
      intro ω hω
      by_cases hmem : ω ∈ tailSetᶜ
      · simpa [body, Set.indicator_of_mem hmem] using hω
      · have hzero : body ω = 0 := by
          simp [body, Set.indicator_of_notMem hmem]
        have hlt_body : η < body ω := by
          simpa using hω
        rw [hzero] at hlt_body
        exact (not_lt_of_ge hη_nonneg hlt_body).elim
    have hbody_prob_le :
        (μ i).real {ω : Ω i | η < body ω} ≤ probTail i :=
      measureReal_mono hbody_tail_subset
    have hbody_bound :
        ∫ ω, body ω ∂(μ i) < a / 2 := by
      have hraw :
          ∫ ω, body ω ∂(μ i) ≤
            η + R * (μ i).real {ω : Ω i | η < body ω} :=
        _root_.StatInference.ProbabilityMeasure.probability_integral_le_threshold_add_bound_mul_tail
          (μ := μ i) (X := body) (r := η) (C := R) hη_nonneg
          hbody_meas hbody_integrable hbody_le
      have hmul :
          R * (μ i).real {ω : Ω i | η < body ω} ≤ R * probTail i :=
        mul_le_mul_of_nonneg_left hbody_prob_le hR_nonneg
      have hlt :
          η + R * (μ i).real {ω : Ω i | η < body ω} < a / 2 := by
        rw [hη_def]
        nlinarith [hmul, hprob_i]
      exact lt_of_le_of_lt hraw hlt
    have htail_part_le :
        ∫ ω in tailSet, Y i ω ∂(μ i) ≤ η := by
      rw [← integral_indicator htailSet]
      simpa [tailSet, η] using htail_i
    have hbody_part_eq :
        ∫ ω in tailSetᶜ, Y i ω ∂(μ i) = ∫ ω, body ω ∂(μ i) := by
      rw [← integral_indicator htailSet.compl]
    have hsplit :
        ∫ ω, Y i ω ∂(μ i) =
          ∫ ω in tailSet, Y i ω ∂(μ i) +
            ∫ ω in tailSetᶜ, Y i ω ∂(μ i) := by
      simpa [add_comm] using (integral_add_compl htailSet (hY_integrable i)).symm
    rw [hsplit, hbody_part_eq]
    rw [hη_def] at htail_part_le
    nlinarith [htail_part_le, hbody_bound]

end StatInference
