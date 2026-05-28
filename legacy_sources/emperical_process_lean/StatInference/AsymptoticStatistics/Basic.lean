import StatInference.Asymptotics.Basic
import StatInference.ProbabilityMeasure.WeakConvergence
import Mathlib.Probability.CentralLimitTheorem

/-!
# van der Vaart 1998 asymptotic statistics interfaces

This module starts the source-shaped Lean lane for A. W. van der Vaart,
*Asymptotic Statistics* (1998).  The first layer packages Chapter 2
stochastic-convergence theorems and the Chapter 3 delta-method handoff over
mathlib/local convergence APIs.

The intent is to reuse `MeasureTheory.TendstoInDistribution`,
`MeasureTheory.TendstoInMeasure`, local weak-convergence wrappers, and existing
probability/empirical-process infrastructure rather than introduce parallel
foundations.
-/

noncomputable section

namespace StatInference
namespace AsymptoticStatistics

open Filter MeasureTheory ProbabilityTheory
open scoped BigOperators ENNReal Real Topology

universe u v w x y

/-- van der Vaart Chapter 2 notation: convergence in probability is mathlib
`TendstoInMeasure` along `atTop`. -/
abbrev ConvergesInProbability
    {Ω E : Type*} [MeasurableSpace Ω] [EDist E]
    (P : Measure Ω) (X : ℕ -> Ω -> E) (Z : Ω -> E) : Prop :=
  TendstoInMeasure P X atTop Z

/-- van der Vaart Chapter 2 notation: convergence in distribution is weak
convergence of laws of random variables. -/
abbrev ConvergesInDistribution
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [TopologicalSpace E] [MeasurableSpace E] [OpensMeasurableSpace E]
    (P : Measure Ω) (Q : Measure Ω') [IsProbabilityMeasure P]
    [IsProbabilityMeasure Q] (X : ℕ -> Ω -> E) (Z : Ω' -> E) : Prop :=
  TendstoInDistribution X atTop Z (fun _ => P) Q

/--
Convergence in distribution is unchanged by dropping a finite prefix of a
sequence.  This `Nat.succ` form is the reindexing bridge used when a textbook
statement is naturally written for positive sample sizes.
-/
theorem vaart1998_tendstoInDistribution_succ
    {Ω : ℕ -> Type*} {Ω' E : Type*}
    [∀ n : ℕ, MeasurableSpace (Ω n)]
    [MeasurableSpace Ω']
    [TopologicalSpace E] [MeasurableSpace E] [OpensMeasurableSpace E]
    {μ : (n : ℕ) -> Measure (Ω n)} [∀ n : ℕ, IsProbabilityMeasure (μ n)]
    {Q : Measure Ω'} [IsProbabilityMeasure Q]
    {X : (n : ℕ) -> Ω n -> E} {Z : Ω' -> E}
    (hX : TendstoInDistribution X atTop Z μ Q) :
    TendstoInDistribution
      (fun n : ℕ => X (n + 1)) atTop Z
      (fun n : ℕ => μ (n + 1)) Q where
  forall_aemeasurable n := hX.forall_aemeasurable (n + 1)
  aemeasurable_limit := hX.aemeasurable_limit
  tendsto := by
    simpa [Function.comp_def] using
      hX.tendsto.comp (tendsto_add_atTop_nat 1)

/--
Constant-measure specialization of
`vaart1998_tendstoInDistribution_succ`.
-/
theorem vaart1998_tendstoInDistribution_constMeasure_succ
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [TopologicalSpace E] [MeasurableSpace E] [OpensMeasurableSpace E]
    {P : Measure Ω} {Q : Measure Ω'} [IsProbabilityMeasure P]
    [IsProbabilityMeasure Q]
    {X : ℕ -> Ω -> E} {Z : Ω' -> E}
    (hX : TendstoInDistribution X atTop Z (fun _ : ℕ => P) Q) :
    TendstoInDistribution
      (fun n : ℕ => X (n + 1)) atTop Z (fun _ : ℕ => P) Q := by
  simpa using
    (vaart1998_tendstoInDistribution_succ
      (Ω := fun _ : ℕ => Ω) (μ := fun _ : ℕ => P) hX)

/--
Convergence in measure is unchanged by inserting one finite prefix value.
This is the probability-convergence analogue of the positive-sample-size
`Nat.succ` distribution bridge above.
-/
theorem vaart1998_tendstoInMeasure_zero_prepend
    {Ω E : Type*} [MeasurableSpace Ω] [EDist E]
    {P : Measure Ω} {X : ℕ -> Ω -> E} {x0 Z : Ω -> E}
    (hX : TendstoInMeasure P X atTop Z) :
    TendstoInMeasure P
      (fun n ω =>
        match n with
        | 0 => x0 ω
        | Nat.succ k => X k ω)
      atTop Z := by
  intro ε hε
  refine
    (tendsto_add_atTop_iff_nat
      (f := fun n : ℕ =>
        P {ω | ε ≤ edist
          ((fun n ω =>
            match n with
            | 0 => x0 ω
            | Nat.succ k => X k ω) n ω)
          (Z ω)}) 1).mp ?_
  simpa using hX ε hε

/-- van der Vaart Chapter 2 stochastic `o_P(1)`: convergence in probability
to zero. -/
abbrev StochasticLittleO
    {Ω E : Type*} [MeasurableSpace Ω] [SeminormedAddCommGroup E]
    (P : Measure Ω) (X : ℕ -> Ω -> E) : Prop :=
  TendstoInMeasure P X atTop 0

/-- van der Vaart Chapter 2 stochastic boundedness, `O_P(1)`, in the common
tail-probability form. -/
def StochasticBounded
    {Ω E : Type*} [MeasurableSpace Ω] [SeminormedAddCommGroup E]
    (P : Measure Ω) (X : ℕ -> Ω -> E) : Prop :=
  ∀ ε : ℝ, 0 < ε ->
    ∃ M : ℝ, 0 < M ∧
      ∀ᶠ n in atTop, P.real {ω | M ≤ ‖X n ω‖} < ε

/--
Stochastic boundedness is invariant under a.e.-equal versions of each
statistic in the sequence.

This is the Chapter 2 bookkeeping bridge used by later textbook displays such
as `scaledEstimator_n = r_n • (estimator_n - theta0_n)`: once an `O_P(1)`
bound is proved for the displayed version, the chosen a.e. representative
inherits it without reopening the tail-probability proof.
-/
theorem vaart1998_stochasticBounded_congr_ae
    {Ω E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [SeminormedAddCommGroup E]
    {X Y : ℕ -> Ω -> E}
    (hXY : ∀ n : ℕ, X n =ᵐ[P] Y n)
    (hY : StochasticBounded P Y) :
    StochasticBounded P X := by
  intro ε hε
  rcases hY ε hε with ⟨M, hMpos, htail⟩
  refine ⟨M, hMpos, ?_⟩
  filter_upwards [htail] with n hn
  have hset :
      {ω : Ω | M ≤ ‖X n ω‖} =ᵐ[P] {ω : Ω | M ≤ ‖Y n ω‖} := by
    exact (hXY n).mono fun ω hω => by
      apply propext
      change M ≤ ‖X n ω‖ ↔ M ≤ ‖Y n ω‖
      rw [hω]
  have hmeasure :
      P.real {ω : Ω | M ≤ ‖X n ω‖} =
        P.real {ω : Ω | M ≤ ‖Y n ω‖} := by
    rw [measureReal_def, measureReal_def, measure_congr hset]
  simpa [hmeasure] using hn

/--
Almost-sure convergence implies convergence in probability.

This is the Chapter 2 bridge that lets strong-law outputs feed later
probability-localization arguments, including the method-of-moments existence
step in Chapter 4.
-/
theorem vaart1998_tendstoInMeasure_of_tendsto_ae
    {Ω E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [PseudoEMetricSpace E]
    {X : ℕ -> Ω -> E} {Z : Ω -> E}
    (hX : ∀ n : ℕ, AEStronglyMeasurable (X n) P)
    (hAE : ∀ᵐ ω ∂P, Tendsto (fun n : ℕ => X n ω) atTop (𝓝 (Z ω))) :
    TendstoInMeasure P X atTop Z :=
  MeasureTheory.tendstoInMeasure_of_tendsto_ae hX hAE

/--
Law-tail criterion for stochastic boundedness.

This is the random-variable/law specialization needed after measure-level
tightness has produced norm-tail bounds for the laws `P.map X_n`.
-/
theorem vaart1998_stochasticBounded_of_law_real_norm_tail
    {Ω E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [SeminormedAddCommGroup E] [MeasurableSpace E] [BorelSpace E]
    {X : ℕ -> Ω -> E}
    (hX : ∀ n, AEMeasurable (X n) P)
    (hlaw_tail : ∀ ε : ℝ, 0 < ε ->
      ∃ M : ℝ, 0 < M ∧
        ∀ᶠ n in atTop, (P.map (X n)).real {x : E | M ≤ ‖x‖} < ε) :
    StochasticBounded P X := by
  intro ε hε
  rcases hlaw_tail ε hε with ⟨M, hMpos, htail⟩
  refine ⟨M, hMpos, ?_⟩
  filter_upwards [htail] with n hn
  have hset : MeasurableSet {x : E | M ≤ ‖x‖} :=
    (isClosed_le continuous_const continuous_norm).measurableSet
  have hmap :
      (P.map (X n)).real {x : E | M ≤ ‖x‖} =
        P.real {ω : Ω | M ≤ ‖X n ω‖} := by
    rw [measureReal_def, measureReal_def]
    rw [Measure.map_apply_of_aemeasurable (hX n) hset]
    rfl
  exact hmap ▸ hn

/--
Stochastic boundedness gives the corresponding law-tail criterion.

This is the converse bookkeeping bridge to
`vaart1998_stochasticBounded_of_law_real_norm_tail`: once `X_n` is
a.e.-measurable, the `O_P(1)` tail bound can be stated equivalently as a tail
bound for the laws `P.map X_n`.
-/
theorem vaart1998_law_real_norm_tail_of_stochasticBounded
    {Ω E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [SeminormedAddCommGroup E] [MeasurableSpace E] [BorelSpace E]
    {X : ℕ -> Ω -> E}
    (hX : ∀ n, AEMeasurable (X n) P)
    (hOP : StochasticBounded P X) :
    ∀ ε : ℝ, 0 < ε ->
      ∃ M : ℝ, 0 < M ∧
        ∀ᶠ n in atTop, (P.map (X n)).real {x : E | M ≤ ‖x‖} < ε := by
  intro ε hε
  rcases hOP ε hε with ⟨M, hMpos, htail⟩
  refine ⟨M, hMpos, ?_⟩
  filter_upwards [htail] with n hn
  have hset : MeasurableSet {x : E | M ≤ ‖x‖} :=
    (isClosed_le continuous_const continuous_norm).measurableSet
  have hmap :
      (P.map (X n)).real {x : E | M ≤ ‖x‖} =
        P.real {ω : Ω | M ≤ ‖X n ω‖} := by
    rw [measureReal_def, measureReal_def]
    rw [Measure.map_apply_of_aemeasurable (hX n) hset]
    rfl
  exact hmap ▸ hn

/--
Convergence in probability to a fixed finite value implies stochastic
boundedness.

This is the Chapter 2 `O_P(1)` bridge used when a scalar empirical average has
already been shown to converge in probability to its population value.
-/
theorem vaart1998_stochasticBounded_of_tendstoInMeasure_const
    {Ω E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsFiniteMeasure P]
    [SeminormedAddCommGroup E]
    {X : ℕ -> Ω -> E} (c : E)
    (hX : TendstoInMeasure P X atTop (fun _ : Ω => c)) :
    StochasticBounded P X := by
  intro ε hε
  let M : ℝ := ‖c‖ + 1
  have hMpos : 0 < M := by
    have hnorm_nonneg : 0 ≤ ‖c‖ := norm_nonneg c
    linarith
  refine ⟨M, hMpos, ?_⟩
  have htail :
      Tendsto
        (fun n : ℕ => P.real {ω : Ω | 1 ≤ ‖X n ω - c‖})
        atTop (𝓝 0) := by
    simpa using
      (MeasureTheory.tendstoInMeasure_iff_measureReal_norm.mp hX)
        1 (by norm_num : (0 : ℝ) < 1)
  filter_upwards [htail.eventually_lt_const hε] with n hn
  have hsubset :
      {ω : Ω | M ≤ ‖X n ω‖} ⊆
        {ω : Ω | 1 ≤ ‖X n ω - c‖} := by
    intro ω hω
    have hnorm_le :
        ‖X n ω‖ ≤ ‖X n ω - c‖ + ‖c‖ := by
      simpa [sub_add_cancel] using
        norm_add_le (X n ω - c) c
    have : 1 ≤ ‖X n ω - c‖ := by
      dsimp [M] at hω
      linarith
    exact this
  exact lt_of_le_of_lt (measureReal_mono hsubset) hn

/--
Convergence in probability to a fixed value implies convergence in probability
of the norm residual to zero.

This is the Chapter 2 bridge used to turn an operator-valued LLN into the
scalar norm-residual form consumed by later asymptotic normality packets.
-/
theorem vaart1998_tendstoInMeasure_norm_sub_const_zero_of_tendstoInMeasure_const
    {ι Ω E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsFiniteMeasure P] [SeminormedAddCommGroup E]
    {l : Filter ι} {X : ι -> Ω -> E} (c : E)
    (hX : TendstoInMeasure P X l (fun _ : Ω => c)) :
    TendstoInMeasure P (fun i ω => ‖X i ω - c‖) l 0 := by
  rw [MeasureTheory.tendstoInMeasure_iff_measureReal_norm]
  intro ε hε
  have htail :
      Tendsto
        (fun i : ι => P.real {ω : Ω | ε ≤ ‖X i ω - c‖})
        l (𝓝 0) :=
    (MeasureTheory.tendstoInMeasure_iff_measureReal_norm.mp hX) ε hε
  simpa [sub_zero] using htail

/--
Convergence in probability of the norm residual to zero implies convergence
in probability to the fixed value.

Together with
`vaart1998_tendstoInMeasure_norm_sub_const_zero_of_tendstoInMeasure_const`,
this packages the standard Chapter 2 equivalence between vector consistency
and the scalar norm-residual formulation used in later estimator theorems.
-/
theorem vaart1998_tendstoInMeasure_const_of_norm_sub_const_zero
    {ι Ω E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [SeminormedAddCommGroup E]
    {l : Filter ι} {X : ι -> Ω -> E} (c : E)
    (hXnorm : TendstoInMeasure P (fun i ω => ‖X i ω - c‖) l 0) :
    TendstoInMeasure P X l (fun _ : Ω => c) := by
  rw [MeasureTheory.tendstoInMeasure_iff_norm]
  intro ε hε
  have htail :
      Tendsto
        (fun i : ι =>
          P {ω : Ω | ε ≤ ‖‖X i ω - c‖ - (0 : ℝ)‖})
        l (𝓝 0) :=
    (MeasureTheory.tendstoInMeasure_iff_norm.mp hXnorm) ε hε
  simpa [sub_zero, Real.norm_eq_abs] using htail

/--
Continuous mapping for convergence in probability to a constant.

This Chapter 2 form is intentionally local at the limit point: if `X_i`
converges in measure to the constant `c`, then any map continuous at `c`
preserves the convergence in measure.
-/
theorem vaart1998_tendstoInMeasure_continuousAt_const
    {ι Ω E F : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [PseudoMetricSpace E] [PseudoMetricSpace F]
    {l : Filter ι} {X : ι -> Ω -> E} {c : E} {g : E -> F}
    (hg : ContinuousAt g c)
    (hX : TendstoInMeasure P X l (fun _ : Ω => c)) :
    TendstoInMeasure P (fun i ω => g (X i ω)) l
      (fun _ : Ω => g c) := by
  rw [MeasureTheory.tendstoInMeasure_iff_dist]
  intro ε hε
  rw [Metric.continuousAt_iff] at hg
  rcases hg ε hε with ⟨δ, hδpos, hδ⟩
  have hXδ :
      Tendsto
        (fun i => P {ω : Ω | δ ≤ dist (X i ω) c})
        l (𝓝 0) :=
    (MeasureTheory.tendstoInMeasure_iff_dist.mp hX) δ hδpos
  refine
    tendsto_of_tendsto_of_tendsto_of_le_of_le tendsto_const_nhds hXδ
      (fun _ => zero_le) ?_
  intro i
  exact measure_mono (by
    intro ω hω
    exact not_lt.mp (by
      intro hdist
      exact not_lt_of_ge hω (hδ (x := X i ω) hdist)))

/--
Continuity at a point gives the local `edist` stability field used by the
source-shaped Z-estimator endpoints.
-/
theorem vaart1998_edist_local_of_continuousAt
    {E F : Type*} [PseudoEMetricSpace E] [PseudoEMetricSpace F]
    {g : E -> F} {c : E} {y0 : F}
    (hg : ContinuousAt g c) (hg_value : g c = y0) :
    ∀ ε : ℝ≥0∞, 0 < ε ->
      ∃ δ : ℝ≥0∞, 0 < δ ∧
        ∀ y : E, edist y c < δ -> edist (g y) y0 < ε := by
  intro ε hε
  rw [EMetric.continuousAt_iff] at hg
  rcases hg ε hε with ⟨δ, hδpos, hδ⟩
  exact ⟨δ, hδpos, fun y hy => by
    simpa [hg_value] using hδ hy⟩

/--
VdV&W tightness of a sequence of laws gives the real-valued norm-tail bound
used by van der Vaart's `O_P(1)` criterion.

The VdV&W/mathlib tightness API is stated with `ℝ≥0∞` measures and strict
norm tails.  This wrapper chooses a slightly larger radius and converts the
result to the `Measure.real` closed-tail form used throughout the Vaart lane.
-/
theorem vaart1998_law_real_norm_tail_of_tight_range
    {E : Type*} [MeasurableSpace E] [NormedAddCommGroup E]
    {μ : ℕ -> ProbabilityMeasure E}
    (hμ : VdVWProbabilityMeasuresTight (Set.range μ)) :
    ∀ ε : ℝ, 0 < ε ->
      ∃ M : ℝ, 0 < M ∧
        ∀ᶠ n in atTop,
          ((μ n : ProbabilityMeasure E) : Measure E).real
            {x : E | M ≤ ‖x‖} < ε := by
  intro ε hε
  have hε_en : (0 : ENNReal) < ENNReal.ofReal ε :=
    ENNReal.ofReal_pos.mpr hε
  have htail := hμ.tendsto_norm_tail
  have hevent_tail :
      ∀ᶠ r : ℝ in atTop,
        (⨆ ν ∈ {((ρ : ProbabilityMeasure E) : Measure E) | ρ ∈ Set.range μ},
          ν {x : E | r < ‖x‖}) < ENNReal.ofReal ε :=
    (tendsto_order.1 htail).2 (ENNReal.ofReal ε) hε_en
  have hevent_pos : ∀ᶠ r : ℝ in atTop, 0 < r := eventually_gt_atTop 0
  rcases (hevent_tail.and hevent_pos).exists with ⟨r, hr_tail, hr_pos⟩
  let M : ℝ := r + 1
  have hr_lt_M : r < M := by
    simp [M]
  have hMpos : 0 < M := by
    linarith
  refine ⟨M, hMpos, Eventually.of_forall ?_⟩
  intro n
  have hsubset : {x : E | M ≤ ‖x‖} ⊆ {x : E | r < ‖x‖} := by
    intro x hx
    exact hr_lt_M.trans_le hx
  have hmeasure_le :
      ((μ n : ProbabilityMeasure E) : Measure E) {x : E | M ≤ ‖x‖} ≤
        ((μ n : ProbabilityMeasure E) : Measure E) {x : E | r < ‖x‖} :=
    measure_mono hsubset
  have hmem :
      ((μ n : ProbabilityMeasure E) : Measure E) ∈
        {((ρ : ProbabilityMeasure E) : Measure E) | ρ ∈ Set.range μ} :=
    ⟨μ n, ⟨n, rfl⟩, rfl⟩
  have hmeasure_le_sup :
      ((μ n : ProbabilityMeasure E) : Measure E) {x : E | r < ‖x‖} ≤
        (⨆ ν ∈ {((ρ : ProbabilityMeasure E) : Measure E) | ρ ∈ Set.range μ},
          ν {x : E | r < ‖x‖}) :=
    le_iSup₂_of_le ((μ n : ProbabilityMeasure E) : Measure E) hmem le_rfl
  have hmeasure_lt :
      ((μ n : ProbabilityMeasure E) : Measure E) {x : E | M ≤ ‖x‖} <
        ENNReal.ofReal ε :=
    (hmeasure_le.trans hmeasure_le_sup).trans_lt hr_tail
  rw [measureReal_def]
  exact ENNReal.toReal_lt_of_lt_ofReal hmeasure_lt

/--
Tightness of the range of the laws of random variables implies stochastic
boundedness.  This is the Vaart-facing `O_P(1)` bridge after VdV&W tightness
has been proved at the measure level.
-/
theorem vaart1998_stochasticBounded_of_tight_law_range
    {Ω E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P]
    [NormedAddCommGroup E] [MeasurableSpace E] [BorelSpace E]
    {X : ℕ -> Ω -> E}
    (hX : ∀ n, AEMeasurable (X n) P)
    (htight :
      VdVWProbabilityMeasuresTight
        (Set.range fun n : ℕ =>
          (⟨P.map (X n), Measure.isProbabilityMeasure_map (hX n)⟩ :
            ProbabilityMeasure E))) :
    StochasticBounded P X := by
  refine vaart1998_stochasticBounded_of_law_real_norm_tail hX ?_
  intro ε hε
  rcases vaart1998_law_real_norm_tail_of_tight_range htight ε hε with
    ⟨M, hMpos, htail⟩
  refine ⟨M, hMpos, ?_⟩
  filter_upwards [htail] with n hn
  simpa using hn

/--
Sequential weak convergence of probability laws gives the real-valued norm-tail
bound used by Vaart's stochastic boundedness criterion.

This packages the Prokhorov/tightness consequence already available in the
VdV&W weak-convergence lane and then applies
`vaart1998_law_real_norm_tail_of_tight_range`.
-/
theorem vaart1998_law_real_norm_tail_of_weak_convergence
    {E : Type*} [MeasurableSpace E] [NormedAddCommGroup E]
    [OpensMeasurableSpace E] [BorelSpace E]
    [SecondCountableTopology E] [CompleteSpace E]
    {μ : ℕ -> ProbabilityMeasure E} {ν : ProbabilityMeasure E}
    (hμ : VdVWWeakConvergenceProbabilityMeasures μ atTop ν) :
    ∀ ε : ℝ, 0 < ε ->
      ∃ M : ℝ, 0 < M ∧
        ∀ᶠ n in atTop,
          ((μ n : ProbabilityMeasure E) : Measure E).real
            {x : E | M ≤ ‖x‖} < ε := by
  have hcompact_insert : IsCompact (insert ν (Set.range μ)) :=
    hμ.isCompact_insert_range
  have hclosed_insert : IsClosed (insert ν (Set.range μ)) :=
    hcompact_insert.isClosed
  have hclosure_subset : closure (Set.range μ) ⊆ insert ν (Set.range μ) :=
    closure_minimal (Set.subset_insert ν (Set.range μ)) hclosed_insert
  have hcompact_closure : IsCompact (closure (Set.range μ)) :=
    hcompact_insert.of_isClosed_subset isClosed_closure hclosure_subset
  have htight : VdVWProbabilityMeasuresTight (Set.range μ) := by
    simpa [VdVWProbabilityMeasuresTight] using
      (MeasureTheory.isTightMeasureSet_of_isCompact_closure
        (𝓧 := E) (S := Set.range μ) hcompact_closure)
  exact vaart1998_law_real_norm_tail_of_tight_range htight

/--
Convergence in distribution implies stochastic boundedness (`O_P(1)`).

This is the direct van der Vaart Chapter 2 handoff: convergence in distribution
is weak convergence of laws; weak convergence makes the law range tight; tight
law ranges give the real tail criterion for `O_P(1)`.
-/
theorem vaart1998_stochasticBounded_of_tendstoInDistribution
    {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    {P : Measure Ω} {Q : Measure Ω'} [IsProbabilityMeasure P]
    [IsProbabilityMeasure Q]
    [MeasurableSpace E] [NormedAddCommGroup E]
    [OpensMeasurableSpace E] [BorelSpace E]
    [SecondCountableTopology E] [CompleteSpace E]
    {X : ℕ -> Ω -> E} {Z : Ω' -> E}
    (hX : TendstoInDistribution X atTop Z (fun _ => P) Q) :
    StochasticBounded P X := by
  let μ : ℕ -> ProbabilityMeasure E := fun n =>
    ⟨P.map (X n), Measure.isProbabilityMeasure_map (hX.forall_aemeasurable n)⟩
  let ν : ProbabilityMeasure E :=
    ⟨Q.map Z, Measure.isProbabilityMeasure_map hX.aemeasurable_limit⟩
  have hweak : VdVWWeakConvergenceProbabilityMeasures μ atTop ν := by
    simpa [VdVWWeakConvergenceProbabilityMeasures, μ, ν] using hX.tendsto
  refine vaart1998_stochasticBounded_of_law_real_norm_tail hX.forall_aemeasurable ?_
  intro ε hε
  rcases vaart1998_law_real_norm_tail_of_weak_convergence hweak ε hε with
    ⟨M, hMpos, htail⟩
  refine ⟨M, hMpos, ?_⟩
  filter_upwards [htail] with n hn
  simpa [μ] using hn

/--
van der Vaart 1998, Theorem 2.3, continuous mapping theorem.

This source wrapper keeps the theorem in the Vaart namespace while delegating
the proof to mathlib's convergence-in-distribution API.
-/
theorem vaart1998_theorem_2_3_continuous_mapping
    {ι : Type u} {E : Type v} {F : Type w}
    {Ω : ι -> Type x} {Ω' : Type y}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    {μ : (i : ι) -> @Measure (Ω i) (mΩ i)}
    [∀ i, IsProbabilityMeasure (μ i)]
    [MeasurableSpace Ω'] {μ' : Measure Ω'} [IsProbabilityMeasure μ']
    [TopologicalSpace E] [MeasurableSpace E] [OpensMeasurableSpace E]
    [TopologicalSpace F] [MeasurableSpace F] [BorelSpace F]
    {X : (i : ι) -> Ω i -> E} {Z : Ω' -> E} {l : Filter ι}
    {g : E -> F}
    (hX : TendstoInDistribution X l Z μ μ') (hg : Continuous g) :
    TendstoInDistribution (fun i => g ∘ X i) l (g ∘ Z) μ μ' :=
  TendstoInDistribution.continuous_comp hg hX

/--
van der Vaart 1998, Lemma 2.8, Slutsky theorem, product form.
-/
theorem vaart1998_lemma_2_8_slutsky_product
    {ι : Type u} {E : Type v} {E' : Type w}
    {Ω : Type x} {Ω' : Type y}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [MeasurableSpace E] [SeminormedAddCommGroup E]
    [SecondCountableTopology E] [BorelSpace E] [OpensMeasurableSpace E]
    [MeasurableSpace E'] [SeminormedAddCommGroup E']
    [SecondCountableTopology E'] [BorelSpace E']
    {X : ι -> Ω -> E} {Y : ι -> Ω -> E'} {Z : Ω' -> E}
    {l : Filter ι} [l.IsCountablyGenerated] {c : E'}
    (hXZ : TendstoInDistribution X l Z (fun _ => P) Q)
    (hY : TendstoInMeasure P Y l (fun _ => c))
    (hY_meas : ∀ i, AEMeasurable (Y i) P) :
    TendstoInDistribution (fun i ω => (X i ω, Y i ω)) l
      (fun ω => (Z ω, c)) (fun _ => P) Q :=
  hXZ.prodMk_of_tendstoInMeasure_const X Y Z hY hY_meas

/--
van der Vaart 1998, Lemma 2.8, Slutsky theorem through a continuous map.
-/
theorem vaart1998_lemma_2_8_slutsky_continuous
    {ι : Type u} {E : Type v} {E' : Type w} {F : Type x}
    {Ω : Type y} {Ω' : Type*}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [MeasurableSpace E] [SeminormedAddCommGroup E]
    [SecondCountableTopology E] [BorelSpace E] [OpensMeasurableSpace E]
    [MeasurableSpace E'] [SeminormedAddCommGroup E']
    [SecondCountableTopology E'] [BorelSpace E']
    [TopologicalSpace F] [MeasurableSpace F] [BorelSpace F]
    {X : ι -> Ω -> E} {Y : ι -> Ω -> E'} {Z : Ω' -> E}
    {l : Filter ι} [l.IsCountablyGenerated] {c : E'}
    {g : E × E' -> F}
    (hXZ : TendstoInDistribution X l Z (fun _ => P) Q)
    (hY : TendstoInMeasure P Y l (fun _ => c))
    (hY_meas : ∀ i, AEMeasurable (Y i) P)
    (hg : Continuous g) :
    TendstoInDistribution (fun n ω => g (X n ω, Y n ω)) l
      (fun ω => g (Z ω, c)) (fun _ => P) Q :=
  hXZ.continuous_comp_prodMk_of_tendstoInMeasure_const
    (g := g) hg hY hY_meas

/--
van der Vaart 1998, Lemma 2.8, additive Slutsky form.
-/
theorem vaart1998_lemma_2_8_slutsky_add
    {ι : Type u} {E : Type v} {Ω : Type w} {Ω' : Type x}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [MeasurableSpace E] [SeminormedAddCommGroup E]
    [SecondCountableTopology E] [BorelSpace E] [OpensMeasurableSpace E]
    {X Y : ι -> Ω -> E} {Z : Ω' -> E} {l : Filter ι}
    [l.IsCountablyGenerated] {c : E}
    (hXZ : TendstoInDistribution X l Z (fun _ => P) Q)
    (hY : TendstoInMeasure P Y l (fun _ => c))
    (hY_meas : ∀ i, AEMeasurable (Y i) P) :
    TendstoInDistribution (fun n => X n + Y n) l
      (fun ω => Z ω + c) (fun _ => P) Q :=
  hXZ.add_of_tendstoInMeasure_const hY hY_meas

/--
If a high-probability event is contained in another event pointwise, then the
larger event also has probability tending to one.
-/
theorem vaart1998_probability_tending_to_one_of_subset
    {ι Ω : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] {l : Filter ι} {A B : ι -> Set Ω}
    (hA : Tendsto (fun i : ι => P.real (A i)) l (𝓝 1))
    (hAB : ∀ i : ι, A i ⊆ B i) :
    Tendsto (fun i : ι => P.real (B i)) l (𝓝 1) := by
  refine tendsto_of_tendsto_of_tendsto_of_le_of_le
    hA tendsto_const_nhds ?_ ?_
  · intro i
    exact measureReal_mono (hAB i)
  · intro i
    have hle : P.real (B i) ≤ P.real Set.univ :=
      measureReal_mono (μ := P) (Set.subset_univ _)
    simpa using hle

/--
Equality with probability tending to one gives a zero convergence-in-probability
difference.

This is the basic asymptotic-equivalence bookkeeping used when a textbook
estimator is only specified on a high-probability event.
-/
theorem vaart1998_tendstoInMeasure_zero_of_eq_with_probability_tending_to_one
    {ι Ω E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] [SeminormedAddCommGroup E]
    {X Y : ι -> Ω -> E} {l : Filter ι}
    (hEq_meas : ∀ i : ι, MeasurableSet {ω : Ω | X i ω = Y i ω})
    (hEq_prob : Tendsto (fun i : ι => P.real {ω : Ω | X i ω = Y i ω})
      l (𝓝 1)) :
    TendstoInMeasure P (fun i ω => X i ω - Y i ω) l 0 := by
  have hcompl :
      Tendsto (fun i : ι =>
        P.real ({ω : Ω | X i ω = Y i ω}ᶜ)) l (𝓝 0) := by
    have hsub :
        Tendsto (fun i : ι =>
          (1 : ℝ) - P.real {ω : Ω | X i ω = Y i ω}) l (𝓝 0) := by
      have hconst : Tendsto (fun _ : ι => (1 : ℝ)) l (𝓝 1) :=
        tendsto_const_nhds
      simpa using (hconst.sub hEq_prob)
    refine hsub.congr' ?_
    exact Eventually.of_forall fun i => by
      have hsum :
          P.real {ω : Ω | X i ω = Y i ω} +
              P.real ({ω : Ω | X i ω = Y i ω}ᶜ) = 1 :=
        probReal_add_probReal_compl (μ := P) (hEq_meas i)
      linarith
  rw [MeasureTheory.tendstoInMeasure_iff_measureReal_norm]
  intro ε hε
  refine tendsto_of_tendsto_of_tendsto_of_le_of_le
    tendsto_const_nhds hcompl ?_ ?_
  · intro i
    exact measureReal_nonneg
  · intro i
    refine measureReal_mono ?_
    intro ω htail
    show ¬ X i ω = Y i ω
    intro heq
    have hzero : X i ω - Y i ω = 0 := by
      simp [heq]
    have hle_zero : ε ≤ 0 := by
      simpa [hzero] using htail
    exact (not_le_of_gt hε) hle_zero

/--
Asymptotic-equivalence transfer for convergence in distribution.

If `Y_i = X_i` with probability tending to one and `X_i` has a weak limit,
then `Y_i` has the same weak limit.  This is a Slutsky consequence of the
previous convergence-in-probability difference lemma.
-/
theorem vaart1998_tendstoInDistribution_of_eq_with_probability_tending_to_one
    {ι : Type u} {E : Type v} {Ω : Type w} {Ω' : Type x}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [MeasurableSpace E] [SeminormedAddCommGroup E]
    [SecondCountableTopology E] [BorelSpace E] [OpensMeasurableSpace E]
    {X Y : ι -> Ω -> E} {Z : Ω' -> E} {l : Filter ι}
    [l.IsCountablyGenerated]
    (hX : TendstoInDistribution X l Z (fun _ => P) Q)
    (hEq_meas : ∀ i : ι, MeasurableSet {ω : Ω | Y i ω = X i ω})
    (hEq_prob : Tendsto (fun i : ι => P.real {ω : Ω | Y i ω = X i ω})
      l (𝓝 1))
    (hDiff_meas : ∀ i : ι, AEMeasurable (fun ω : Ω => Y i ω - X i ω) P) :
    TendstoInDistribution Y l Z (fun _ => P) Q := by
  have hdiff :
      TendstoInMeasure P (fun i ω => Y i ω - X i ω) l 0 :=
    vaart1998_tendstoInMeasure_zero_of_eq_with_probability_tending_to_one
      (P := P) (X := Y) (Y := X) hEq_meas hEq_prob
  have hsum :
      TendstoInDistribution
        (fun i ω => X i ω + (Y i ω - X i ω)) l
        (fun ω => Z ω + 0) (fun _ => P) Q :=
    vaart1998_lemma_2_8_slutsky_add
      (P := P) (Q := Q) (X := X)
      (Y := fun i ω => Y i ω - X i ω) (Z := Z) (c := 0)
      hX hdiff hDiff_meas
  refine hsum.congr (fun i => ?_) ?_
  · exact ae_of_all _ fun ω => by
      change X i ω + (Y i ω - X i ω) = Y i ω
      abel
  · exact ae_of_all _ fun ω => by
      simp

/--
van der Vaart 1998, Proposition 2.17, iid centered unit-variance CLT.

This is the standard real-valued mathlib CLT repackaged with the Vaart source
numbering.
-/
theorem vaart1998_proposition_2_17_clt_iid_centered_unit_variance
    {Ω Ω' : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    {P : Measure Ω} {Q : Measure Ω'} [IsProbabilityMeasure P]
    [IsProbabilityMeasure Q] {X : ℕ -> Ω -> ℝ} {Y : Ω' -> ℝ}
    (hY : HasLaw Y (gaussianReal 0 1) Q)
    (h0 : P[X 0] = 0) (h1 : P[X 0 ^ 2] = 1)
    (hindep : iIndepFun X P)
    (hident : ∀ i : ℕ, IdentDistrib (X i) (X 0) P P) :
    TendstoInDistribution
      (fun (n : ℕ) ω => (√(n : ℝ))⁻¹ * ∑ k ∈ Finset.range n, X k ω)
      atTop Y (fun _ => P) Q :=
  ProbabilityTheory.tendstoInDistribution_inv_sqrt_mul_sum
    hY h0 h1 hindep hident

/--
If a random sequence is uniformly dominated by a deterministic sequence
converging to zero, then it is `o_P(1)`.

This small bridge is useful for Chapter 2 stochastic-o notation and for later
delta-method remainder packages.
-/
theorem vaart1998_stochastic_littleO_of_uniform_norm_bound
    {Ω E : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [SeminormedAddCommGroup E]
    {X : ℕ -> Ω -> E} {a : ℕ -> ℝ}
    (ha : Tendsto a atTop (𝓝 0))
    (hbound : ∀ᶠ n in atTop, ∀ ω, ‖X n ω‖ ≤ a n) :
    StochasticLittleO P X := by
  rw [StochasticLittleO, MeasureTheory.tendstoInMeasure_iff_norm]
  intro ε hε
  refine (tendsto_congr' ?_).mpr tendsto_const_nhds
  filter_upwards [hbound, ha.eventually_lt_const hε] with n hb hlt
  have hset : {ω | ε ≤ ‖X n ω‖} = (∅ : Set Ω) := by
    ext ω
    simp only [Set.mem_setOf_eq, Set.mem_empty_iff_false, iff_false]
    have hnorm_lt : ‖X n ω‖ < ε := lt_of_le_of_lt (hb ω) hlt
    exact not_le_of_gt hnorm_lt
  simp [hset]

/--
Localization criterion for stochastic `o_P(1)`.

If every fixed deviation event for `X` is eventually contained in a tail event
for a tight/localizing statistic `W`, and those `W` tails can be made uniformly
small, then `X` converges to zero in probability.  This is the probability
bookkeeping used by the delta method after differentiability supplies the local
remainder inequality.
-/
theorem vaart1998_tendstoInMeasure_zero_of_eventually_subset_tight
    {ι Ω E F : Type*} [MeasurableSpace Ω] {P : Measure Ω} [IsFiniteMeasure P]
    [SeminormedAddCommGroup E] [SeminormedAddCommGroup F]
    {X : ι -> Ω -> E} {W : ι -> Ω -> F} {l : Filter ι}
    (hlocal : ∀ ε : ℝ, 0 < ε -> ∀ M : ℝ, 0 < M ->
      ∀ᶠ i in l, {ω | ε ≤ ‖X i ω‖} ⊆ {ω | M ≤ ‖W i ω‖})
    (hW_tight : ∀ ε : ℝ, 0 < ε ->
      ∃ M : ℝ, 0 < M ∧
        ∀ᶠ i in l, P.real {ω | M ≤ ‖W i ω‖} < ε) :
    TendstoInMeasure P X l 0 := by
  rw [MeasureTheory.tendstoInMeasure_iff_measureReal_norm]
  intro ε hε
  rw [tendsto_order]
  constructor
  · intro a ha
    exact Eventually.of_forall fun _ =>
      lt_of_lt_of_le ha measureReal_nonneg
  · intro a ha
    rcases hW_tight a ha with ⟨M, hMpos, hW_tail⟩
    filter_upwards [hlocal ε hε M hMpos, hW_tail] with i hsubset htail
    have hle :
        P.real {ω | ε ≤ ‖X i ω - 0‖} ≤
          P.real {ω | M ≤ ‖W i ω‖} := by
      refine measureReal_mono ?_
      intro ω hω
      exact hsubset (by simpa using hω)
    exact lt_of_le_of_lt hle htail

/--
van der Vaart 1998, Theorem 3.1 deterministic differentiability display.

This is the source line
`phi(theta + h) - phi(theta) = phi'_theta h + o(||h||)`,
packaged from mathlib's Fréchet derivative API.
-/
theorem vaart1998_hasFDerivAt_delta_remainder_isLittleO
    {E F : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    [NormedAddCommGroup F] [NormedSpace ℝ F]
    {phi : E -> F} {theta : E} {L : E →L[ℝ] F}
    (hphi : HasFDerivAt phi L theta) :
    (fun h : E => phi (theta + h) - phi theta - L h) =o[𝓝 0] fun h => h := by
  exact (hasFDerivAt_iff_isLittleO_nhds_zero.mp hphi)

/--
van der Vaart 1998, Theorem 3.1, delta method, supplied-linearization
certificate form.

The analytic differentiability proof will later produce the decomposition
`output = L (scaled input) + remainder`; this theorem already closes the
probabilistic handoff from a linearized distributional limit plus an
`o_P(1)` remainder.
-/
theorem vaart1998_theorem_3_1_delta_method_linearized
    {ι : Type u} {Ω : Type v} {Ω' : Type w} {E : Type x} {F : Type y}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    [NormedAddCommGroup F] [NormedSpace ℝ F]
    [MeasurableSpace F] [SecondCountableTopology F] [BorelSpace F]
    [OpensMeasurableSpace F]
    {W : ι -> Ω -> E} {R : ι -> Ω -> F} {T : Ω' -> E}
    {l : Filter ι} [l.IsCountablyGenerated]
    (L : E →L[ℝ] F)
    (hW : TendstoInDistribution W l T (fun _ => P) Q)
    (hR : TendstoInMeasure P R l 0)
    (hR_meas : ∀ i, AEMeasurable (R i) P) :
    TendstoInDistribution (fun n ω => L (W n ω) + R n ω) l
      (fun ω => L (T ω)) (fun _ => P) Q := by
  have hLW :
      TendstoInDistribution (fun n => (fun x => L x) ∘ W n) l
        ((fun x => L x) ∘ T) (fun _ => P) Q :=
    TendstoInDistribution.continuous_comp (g := fun x => L x)
      L.continuous hW
  have hsum :
      TendstoInDistribution
        (fun n => ((fun x => L x) ∘ W n) + R n) l
        (fun ω => ((fun x => L x) ∘ T) ω + (0 : F))
        (fun _ => P) Q :=
    hLW.add_of_tendstoInMeasure_const (c := (0 : F)) hR hR_meas
  simpa [Function.comp_def] using hsum

/--
van der Vaart 1998, Theorem 3.1, source-shaped delta-method handoff.

If the linear statistic `r_n • (T_n - theta)` converges in distribution and the
scaled differentiability remainder is `o_P(1)`, then
`r_n • (phi(T_n) - phi(theta))` has the derivative-pushforward weak limit.
The next layer should discharge the supplied remainder field from
`vaart1998_hasFDerivAt_delta_remainder_isLittleO` plus tightness.
-/
theorem vaart1998_theorem_3_1_delta_method_of_scaled_remainder
    {ι : Type u} {Ω : Type v} {Ω' : Type w} {E : Type x} {F : Type y}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    [NormedAddCommGroup F] [NormedSpace ℝ F]
    [MeasurableSpace F] [SecondCountableTopology F] [BorelSpace F]
    [OpensMeasurableSpace F]
    {Tn : ι -> Ω -> E} {T : Ω' -> E} {phi : E -> F} {theta : E}
    {r : ι -> ℝ} {l : Filter ι} [l.IsCountablyGenerated]
    (L : E →L[ℝ] F)
    (hW : TendstoInDistribution
      (fun n ω => r n • (Tn n ω - theta)) l T (fun _ => P) Q)
    (hR : TendstoInMeasure P
      (fun n ω => r n • (phi (Tn n ω) - phi theta - L (Tn n ω - theta)))
      l 0)
    (hR_meas : ∀ n, AEMeasurable
      (fun ω => r n • (phi (Tn n ω) - phi theta - L (Tn n ω - theta))) P) :
    TendstoInDistribution
      (fun n ω => r n • (phi (Tn n ω) - phi theta)) l
      (fun ω => L (T ω)) (fun _ => P) Q := by
  have hlin :
      TendstoInDistribution
        (fun n ω =>
          L (r n • (Tn n ω - theta)) +
            r n • (phi (Tn n ω) - phi theta - L (Tn n ω - theta))) l
        (fun ω => L (T ω)) (fun _ => P) Q :=
    vaart1998_theorem_3_1_delta_method_linearized
      (L := L) hW hR hR_meas
  refine hlin.congr (fun n => ?_) (ae_of_all _ fun _ => rfl)
  exact ae_of_all _ fun ω => by
    change L (r n • (Tn n ω - theta)) +
        r n • (phi (Tn n ω) - phi theta - L (Tn n ω - theta)) =
      r n • (phi (Tn n ω) - phi theta)
    rw [map_smul]
    simp [sub_eq_add_neg, add_assoc, add_left_comm]

/--
van der Vaart 1998, Theorem 3.1, delta method with a tight scaled statistic and
a local remainder certificate.

This packages the standard proof step: once the differentiability remainder is
localized so that its large-deviation event is controlled by the tail of
`r_n • (T_n - theta)`, stochastic boundedness/tightness of that scaled statistic
turns the remainder into `o_P(1)`.  The result then feeds the compiled
scaled-remainder delta handoff.
-/
theorem vaart1998_theorem_3_1_delta_method_of_localization_tight
    {ι : Type u} {Ω : Type v} {Ω' : Type w} {E : Type x} {F : Type y}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    [NormedAddCommGroup F] [NormedSpace ℝ F]
    [MeasurableSpace F] [SecondCountableTopology F] [BorelSpace F]
    [OpensMeasurableSpace F]
    {Tn : ι -> Ω -> E} {T : Ω' -> E} {phi : E -> F} {theta : E}
    {r : ι -> ℝ} {l : Filter ι} [l.IsCountablyGenerated]
    (L : E →L[ℝ] F)
    (hW : TendstoInDistribution
      (fun n ω => r n • (Tn n ω - theta)) l T (fun _ => P) Q)
    (hR_local : ∀ ε : ℝ, 0 < ε -> ∀ M : ℝ, 0 < M ->
      ∀ᶠ n in l,
        {ω |
          ε ≤ ‖r n • (phi (Tn n ω) - phi theta - L (Tn n ω - theta))‖} ⊆
        {ω | M ≤ ‖r n • (Tn n ω - theta)‖})
    (hW_tight : ∀ ε : ℝ, 0 < ε ->
      ∃ M : ℝ, 0 < M ∧
        ∀ᶠ n in l, P.real {ω | M ≤ ‖r n • (Tn n ω - theta)‖} < ε)
    (hR_meas : ∀ n, AEMeasurable
      (fun ω => r n • (phi (Tn n ω) - phi theta - L (Tn n ω - theta))) P) :
    TendstoInDistribution
      (fun n ω => r n • (phi (Tn n ω) - phi theta)) l
      (fun ω => L (T ω)) (fun _ => P) Q := by
  have hR : TendstoInMeasure P
      (fun n ω => r n • (phi (Tn n ω) - phi theta - L (Tn n ω - theta)))
      l 0 :=
    vaart1998_tendstoInMeasure_zero_of_eventually_subset_tight
      (P := P) (X := fun n ω =>
        r n • (phi (Tn n ω) - phi theta - L (Tn n ω - theta)))
      (W := fun n ω => r n • (Tn n ω - theta))
      hR_local hW_tight
  exact vaart1998_theorem_3_1_delta_method_of_scaled_remainder
    (L := L) hW hR hR_meas

/--
Convert a scaled-ball remainder estimate into the local event-subset
certificate used by the delta-method localization theorem.

This is the set-theoretic form of the textbook proof sentence: on the event
where the tight statistic `r_n • (T_n - theta)` stays in a fixed ball, the
scaled differentiability remainder is eventually smaller than any fixed
epsilon.
-/
theorem vaart1998_delta_remainder_local_subset_of_eventually_small_on_scaled_ball
    {ι Ω E F : Type*} [MeasurableSpace Ω]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [NormedAddCommGroup F] [NormedSpace ℝ F]
    {Tn : ι -> Ω -> E} {phi : E -> F} {theta : E}
    {r : ι -> ℝ} {l : Filter ι} (L : E →L[ℝ] F)
    (hsmall : ∀ ε : ℝ, 0 < ε -> ∀ M : ℝ, 0 < M ->
      ∀ᶠ n in l, ∀ ω,
        ‖r n • (Tn n ω - theta)‖ < M ->
        ‖r n • (phi (Tn n ω) - phi theta - L (Tn n ω - theta))‖ < ε) :
    ∀ ε : ℝ, 0 < ε -> ∀ M : ℝ, 0 < M ->
      ∀ᶠ n in l,
        {ω |
          ε ≤ ‖r n • (phi (Tn n ω) - phi theta - L (Tn n ω - theta))‖} ⊆
        {ω | M ≤ ‖r n • (Tn n ω - theta)‖} := by
  intro ε hε M hM
  filter_upwards [hsmall ε hε M hM] with n hn
  intro ω hω
  by_contra hnot
  have hW_lt : ‖r n • (Tn n ω - theta)‖ < M := not_le.mp hnot
  exact (not_le_of_gt (hn ω hW_lt)) hω

/--
An `o(‖h‖)` deterministic remainder is uniformly small on every fixed scaled
ball once the scaling norms diverge.

This is the analytic core of Vaart's delta-method proof.  On the event
`‖r_n • h_n‖ < M`, divergence of `‖r_n‖` forces `h_n` into the derivative
neighborhood; the little-o bound then gives
`‖r_n • remainder(h_n)‖ < ε`.
-/
theorem vaart1998_delta_remainder_small_on_scaled_ball_of_isLittleO
    {Ω E F : Type*}
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [NormedAddCommGroup F] [NormedSpace ℝ F]
    {Tn : ℕ -> Ω -> E} {phi : E -> F} {theta : E}
    {r : ℕ -> ℝ} (L : E →L[ℝ] F)
    (hrem :
      (fun h : E => phi (theta + h) - phi theta - L h) =o[𝓝 0]
        fun h => h)
    (hr : Tendsto (fun n => ‖r n‖) atTop atTop) :
    ∀ ε : ℝ, 0 < ε -> ∀ M : ℝ, 0 < M ->
      ∀ᶠ n in atTop, ∀ ω,
        ‖r n • (Tn n ω - theta)‖ < M ->
        ‖r n • (phi (Tn n ω) - phi theta - L (Tn n ω - theta))‖ < ε := by
  intro ε hε M hM
  let c : ℝ := ε / (2 * M)
  have hc : 0 < c := by
    positivity
  have hbound_nhds :
      ∀ᶠ h : E in 𝓝 0,
        ‖phi (theta + h) - phi theta - L h‖ ≤ c * ‖h‖ :=
    hrem.bound hc
  rcases Metric.eventually_nhds_iff.mp hbound_nhds with
    ⟨δ, hδ, hδ_bound⟩
  have hscale_event : ∀ᶠ n in atTop, M / δ < ‖r n‖ :=
    hr (eventually_gt_atTop (M / δ))
  filter_upwards [hscale_event] with n hn ω hscaled
  let h : E := Tn n ω - theta
  have hM_lt_rδ : M < ‖r n‖ * δ := by
    exact (div_lt_iff₀ hδ).mp hn
  have hnorm_h_lt : ‖h‖ < δ := by
    by_contra hnot
    have hδ_le : δ ≤ ‖h‖ := not_lt.mp hnot
    have hM_lt_scaled : M < ‖r n • h‖ := by
      calc
        M < ‖r n‖ * δ := hM_lt_rδ
        _ ≤ ‖r n‖ * ‖h‖ :=
          mul_le_mul_of_nonneg_left hδ_le (norm_nonneg (r n))
        _ = ‖r n • h‖ := (norm_smul (r n) h).symm
    exact (not_lt_of_ge hscaled.le) hM_lt_scaled
  have hrem_bound :
      ‖phi (Tn n ω) - phi theta - L h‖ ≤ c * ‖h‖ := by
    have hlocal := hδ_bound (by simpa [dist_eq_norm] using hnorm_h_lt)
    simpa [h, sub_eq_add_neg, add_assoc, add_left_comm, add_comm] using hlocal
  have hscaled_norm : ‖r n‖ * ‖h‖ < M := by
    simpa [h, norm_smul] using hscaled
  have hmul_le :
      ‖r n • (phi (Tn n ω) - phi theta - L h)‖ ≤
        c * (‖r n‖ * ‖h‖) := by
    calc
      ‖r n • (phi (Tn n ω) - phi theta - L h)‖
          = ‖r n‖ * ‖phi (Tn n ω) - phi theta - L h‖ := by
            rw [norm_smul]
      _ ≤ ‖r n‖ * (c * ‖h‖) :=
          mul_le_mul_of_nonneg_left hrem_bound (norm_nonneg (r n))
      _ = c * (‖r n‖ * ‖h‖) := by ring
  have hcM_lt : c * M < ε := by
    have hMne : M ≠ 0 := ne_of_gt hM
    have hcM_eq : c * M = ε / 2 := by
      dsimp [c]
      field_simp [hMne]
    linarith
  have hmul_lt : c * (‖r n‖ * ‖h‖) < ε := by
    exact (mul_lt_mul_of_pos_left hscaled_norm hc).trans hcM_lt
  exact lt_of_le_of_lt (by simpa [h] using hmul_le) hmul_lt

/--
Fréchet differentiability gives the scaled-ball smallness field used by the
delta-method wrapper, assuming the scalar rates diverge in norm.
-/
theorem vaart1998_delta_remainder_small_on_scaled_ball_of_hasFDerivAt_norm_atTop
    {Ω E F : Type*}
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [NormedAddCommGroup F] [NormedSpace ℝ F]
    {Tn : ℕ -> Ω -> E} {phi : E -> F} {theta : E}
    {r : ℕ -> ℝ} (L : E →L[ℝ] F)
    (hphi : HasFDerivAt phi L theta)
    (hr : Tendsto (fun n => ‖r n‖) atTop atTop) :
    ∀ ε : ℝ, 0 < ε -> ∀ M : ℝ, 0 < M ->
      ∀ᶠ n in atTop, ∀ ω,
        ‖r n • (Tn n ω - theta)‖ < M ->
        ‖r n • (phi (Tn n ω) - phi theta - L (Tn n ω - theta))‖ < ε :=
  vaart1998_delta_remainder_small_on_scaled_ball_of_isLittleO
    (L := L) (vaart1998_hasFDerivAt_delta_remainder_isLittleO hphi) hr

/--
Fréchet differentiability gives the scaled-ball smallness field used by the
delta-method wrapper, in the textbook rate form `r_n -> ∞`.
-/
theorem vaart1998_delta_remainder_small_on_scaled_ball_of_hasFDerivAt
    {Ω E F : Type*}
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [NormedAddCommGroup F] [NormedSpace ℝ F]
    {Tn : ℕ -> Ω -> E} {phi : E -> F} {theta : E}
    {r : ℕ -> ℝ} (L : E →L[ℝ] F)
    (hphi : HasFDerivAt phi L theta)
    (hr : Tendsto r atTop atTop) :
    ∀ ε : ℝ, 0 < ε -> ∀ M : ℝ, 0 < M ->
      ∀ᶠ n in atTop, ∀ ω,
        ‖r n • (Tn n ω - theta)‖ < M ->
        ‖r n • (phi (Tn n ω) - phi theta - L (Tn n ω - theta))‖ < ε := by
  have hr_norm : Tendsto (fun n => ‖r n‖) atTop atTop := by
    simpa [Real.norm_eq_abs] using (tendsto_abs_atTop_atTop.comp hr)
  exact
    vaart1998_delta_remainder_small_on_scaled_ball_of_hasFDerivAt_norm_atTop
      (L := L) hphi hr_norm

/--
van der Vaart 1998, Theorem 3.1, sequence form with an `O_P(1)` scaled
statistic and a scaled-ball remainder estimate.

This packages the two probabilistic ingredients used in the proof: tightness of
`r_n • (T_n - theta)` and negligibility of the scaled remainder on every fixed
tight ball.
-/
theorem vaart1998_theorem_3_1_delta_method_of_scaled_ball_stochasticBounded
    {Ω : Type v} {Ω' : Type w} {E : Type x} {F : Type y}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    [NormedAddCommGroup F] [NormedSpace ℝ F]
    [MeasurableSpace F] [SecondCountableTopology F] [BorelSpace F]
    [OpensMeasurableSpace F]
    {Tn : ℕ -> Ω -> E} {T : Ω' -> E} {phi : E -> F} {theta : E}
    {r : ℕ -> ℝ}
    (L : E →L[ℝ] F)
    (hW : TendstoInDistribution
      (fun n ω => r n • (Tn n ω - theta)) atTop T (fun _ => P) Q)
    (hsmall : ∀ ε : ℝ, 0 < ε -> ∀ M : ℝ, 0 < M ->
      ∀ᶠ n in atTop, ∀ ω,
        ‖r n • (Tn n ω - theta)‖ < M ->
        ‖r n • (phi (Tn n ω) - phi theta - L (Tn n ω - theta))‖ < ε)
    (hW_OP : StochasticBounded P
      (fun n ω => r n • (Tn n ω - theta)))
    (hR_meas : ∀ n, AEMeasurable
      (fun ω => r n • (phi (Tn n ω) - phi theta - L (Tn n ω - theta))) P) :
    TendstoInDistribution
      (fun n ω => r n • (phi (Tn n ω) - phi theta)) atTop
      (fun ω => L (T ω)) (fun _ => P) Q :=
  vaart1998_theorem_3_1_delta_method_of_localization_tight
    (L := L) hW
    (vaart1998_delta_remainder_local_subset_of_eventually_small_on_scaled_ball
      (L := L) hsmall)
    hW_OP hR_meas

/--
van der Vaart 1998, Theorem 3.1, sequence scaled-ball form with stochastic
boundedness derived from convergence in distribution.

This removes the explicit `O_P(1)` scaled-statistic hypothesis from
`vaart1998_theorem_3_1_delta_method_of_scaled_ball_stochasticBounded` by using
the Chapter 2 fact that convergence in distribution implies stochastic
boundedness.
-/
theorem vaart1998_theorem_3_1_delta_method_of_scaled_ball_distribution
    {Ω : Type v} {Ω' : Type w} {E : Type x} {F : Type y}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E] [CompleteSpace E]
    [NormedAddCommGroup F] [NormedSpace ℝ F]
    [MeasurableSpace F] [SecondCountableTopology F] [BorelSpace F]
    [OpensMeasurableSpace F]
    {Tn : ℕ -> Ω -> E} {T : Ω' -> E} {phi : E -> F} {theta : E}
    {r : ℕ -> ℝ}
    (L : E →L[ℝ] F)
    (hW : TendstoInDistribution
      (fun n ω => r n • (Tn n ω - theta)) atTop T (fun _ => P) Q)
    (hsmall : ∀ ε : ℝ, 0 < ε -> ∀ M : ℝ, 0 < M ->
      ∀ᶠ n in atTop, ∀ ω,
        ‖r n • (Tn n ω - theta)‖ < M ->
        ‖r n • (phi (Tn n ω) - phi theta - L (Tn n ω - theta))‖ < ε)
    (hR_meas : ∀ n, AEMeasurable
      (fun ω => r n • (phi (Tn n ω) - phi theta - L (Tn n ω - theta))) P) :
    TendstoInDistribution
      (fun n ω => r n • (phi (Tn n ω) - phi theta)) atTop
      (fun ω => L (T ω)) (fun _ => P) Q :=
  vaart1998_theorem_3_1_delta_method_of_scaled_ball_stochasticBounded
    (L := L) hW hsmall
    (vaart1998_stochasticBounded_of_tendstoInDistribution hW)
    hR_meas

/--
van der Vaart 1998, Theorem 3.1, sequence form with differentiability and
distributional convergence of the scaled statistic.

This is the most compact compiled Chapter 3.1 wrapper in the current lane:
the scaled-statistic tightness is derived from convergence in distribution,
and the local scaled-ball remainder field is derived from Fréchet
differentiability plus `r_n -> ∞`.
-/
theorem vaart1998_theorem_3_1_delta_method_of_hasFDerivAt_distribution
    {Ω : Type v} {Ω' : Type w} {E : Type x} {F : Type y}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E] [CompleteSpace E]
    [NormedAddCommGroup F] [NormedSpace ℝ F]
    [MeasurableSpace F] [SecondCountableTopology F] [BorelSpace F]
    [OpensMeasurableSpace F]
    {Tn : ℕ -> Ω -> E} {T : Ω' -> E} {phi : E -> F} {theta : E}
    {r : ℕ -> ℝ}
    (L : E →L[ℝ] F)
    (hphi : HasFDerivAt phi L theta)
    (hr : Tendsto r atTop atTop)
    (hW : TendstoInDistribution
      (fun n ω => r n • (Tn n ω - theta)) atTop T (fun _ => P) Q)
    (hR_meas : ∀ n, AEMeasurable
      (fun ω => r n • (phi (Tn n ω) - phi theta - L (Tn n ω - theta))) P) :
    TendstoInDistribution
      (fun n ω => r n • (phi (Tn n ω) - phi theta)) atTop
      (fun ω => L (T ω)) (fun _ => P) Q :=
  vaart1998_theorem_3_1_delta_method_of_scaled_ball_distribution
    (L := L) hW
    (vaart1998_delta_remainder_small_on_scaled_ball_of_hasFDerivAt
      (Tn := Tn) (L := L) hphi hr)
    hR_meas

/--
A.e.-measurability of the scaled delta-method remainder from the two natural
composition measurability fields.

This discharges the technical `hR_meas` side condition in the compact
Theorem 3.1 wrappers whenever `T_n` and `phi ∘ T_n` are a.e.-measurable.
-/
theorem vaart1998_delta_remainder_aemeasurable
    {Ω E F : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    [NormedAddCommGroup F] [NormedSpace ℝ F]
    [MeasurableSpace F] [SecondCountableTopology F] [BorelSpace F]
    [OpensMeasurableSpace F]
    {Tn : ℕ -> Ω -> E} {phi : E -> F} {theta : E}
    {r : ℕ -> ℝ} (L : E →L[ℝ] F)
    (hTn : ∀ n, AEMeasurable (Tn n) P)
    (hphiTn : ∀ n, AEMeasurable (fun ω => phi (Tn n ω)) P) :
    ∀ n, AEMeasurable
      (fun ω => r n • (phi (Tn n ω) - phi theta - L (Tn n ω - theta))) P := by
  intro n
  have hTdiff : AEMeasurable (fun ω => Tn n ω - theta) P :=
    (hTn n).sub aemeasurable_const
  have hL : AEMeasurable (fun ω => L (Tn n ω - theta)) P :=
    L.continuous.measurable.comp_aemeasurable hTdiff
  exact (((hphiTn n).sub aemeasurable_const).sub hL).const_smul (r n)

/--
Measurable-function version of
`vaart1998_delta_remainder_aemeasurable`.
-/
theorem vaart1998_delta_remainder_aemeasurable_of_measurable
    {Ω E F : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    [NormedAddCommGroup F] [NormedSpace ℝ F]
    [MeasurableSpace F] [SecondCountableTopology F] [BorelSpace F]
    [OpensMeasurableSpace F]
    {Tn : ℕ -> Ω -> E} {phi : E -> F} {theta : E}
    {r : ℕ -> ℝ} (L : E →L[ℝ] F)
    (hTn : ∀ n, AEMeasurable (Tn n) P) (hphi : Measurable phi) :
    ∀ n, AEMeasurable
      (fun ω => r n • (phi (Tn n ω) - phi theta - L (Tn n ω - theta))) P :=
  vaart1998_delta_remainder_aemeasurable (Tn := Tn) (phi := phi)
    (theta := theta) (r := r) L hTn
    (fun n => hphi.comp_aemeasurable (hTn n))

/--
van der Vaart 1998, Theorem 3.1, compact sequence form with a.e.-measurability
of the remainder derived from `T_n` and `phi ∘ T_n`.
-/
theorem vaart1998_theorem_3_1_delta_method_of_hasFDerivAt_distribution_aemeasurable
    {Ω : Type v} {Ω' : Type w} {E : Type x} {F : Type y}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E] [CompleteSpace E]
    [NormedAddCommGroup F] [NormedSpace ℝ F]
    [MeasurableSpace F] [SecondCountableTopology F] [BorelSpace F]
    [OpensMeasurableSpace F]
    {Tn : ℕ -> Ω -> E} {T : Ω' -> E} {phi : E -> F} {theta : E}
    {r : ℕ -> ℝ}
    (L : E →L[ℝ] F)
    (hphi : HasFDerivAt phi L theta)
    (hr : Tendsto r atTop atTop)
    (hW : TendstoInDistribution
      (fun n ω => r n • (Tn n ω - theta)) atTop T (fun _ => P) Q)
    (hTn : ∀ n, AEMeasurable (Tn n) P)
    (hphiTn : ∀ n, AEMeasurable (fun ω => phi (Tn n ω)) P) :
    TendstoInDistribution
      (fun n ω => r n • (phi (Tn n ω) - phi theta)) atTop
      (fun ω => L (T ω)) (fun _ => P) Q :=
  vaart1998_theorem_3_1_delta_method_of_hasFDerivAt_distribution
    (L := L) hphi hr hW
    (vaart1998_delta_remainder_aemeasurable (Tn := Tn) (phi := phi)
      (theta := theta) (r := r) L hTn hphiTn)

/--
van der Vaart 1998, Theorem 3.1, compact sequence form with the remainder's
a.e.-measurability derived from measurability of `phi`.
-/
theorem vaart1998_theorem_3_1_delta_method_of_hasFDerivAt_distribution_measurable
    {Ω : Type v} {Ω' : Type w} {E : Type x} {F : Type y}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E] [CompleteSpace E]
    [NormedAddCommGroup F] [NormedSpace ℝ F]
    [MeasurableSpace F] [SecondCountableTopology F] [BorelSpace F]
    [OpensMeasurableSpace F]
    {Tn : ℕ -> Ω -> E} {T : Ω' -> E} {phi : E -> F} {theta : E}
    {r : ℕ -> ℝ}
    (L : E →L[ℝ] F)
    (hphi_deriv : HasFDerivAt phi L theta)
    (hphi_meas : Measurable phi)
    (hr : Tendsto r atTop atTop)
    (hW : TendstoInDistribution
      (fun n ω => r n • (Tn n ω - theta)) atTop T (fun _ => P) Q)
    (hTn : ∀ n, AEMeasurable (Tn n) P) :
    TendstoInDistribution
      (fun n ω => r n • (phi (Tn n ω) - phi theta)) atTop
      (fun ω => L (T ω)) (fun _ => P) Q :=
  vaart1998_theorem_3_1_delta_method_of_hasFDerivAt_distribution_aemeasurable
    (Tn := Tn) (T := T) (phi := phi) (theta := theta) (r := r)
    (L := L) hphi_deriv hr hW hTn
    (fun n => hphi_meas.comp_aemeasurable (hTn n))

/--
van der Vaart 1998, Theorem 3.1, sequence form with an `O_P(1)` scaled
statistic.

For ordinary sequences, the real-tail tightness field in
`vaart1998_theorem_3_1_delta_method_of_localization_tight` is exactly the local
`StochasticBounded` predicate.
-/
theorem vaart1998_theorem_3_1_delta_method_of_localization_stochasticBounded
    {Ω : Type v} {Ω' : Type w} {E : Type x} {F : Type y}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    [NormedAddCommGroup F] [NormedSpace ℝ F]
    [MeasurableSpace F] [SecondCountableTopology F] [BorelSpace F]
    [OpensMeasurableSpace F]
    {Tn : ℕ -> Ω -> E} {T : Ω' -> E} {phi : E -> F} {theta : E}
    {r : ℕ -> ℝ}
    (L : E →L[ℝ] F)
    (hW : TendstoInDistribution
      (fun n ω => r n • (Tn n ω - theta)) atTop T (fun _ => P) Q)
    (hR_local : ∀ ε : ℝ, 0 < ε -> ∀ M : ℝ, 0 < M ->
      ∀ᶠ n in atTop,
        {ω |
          ε ≤ ‖r n • (phi (Tn n ω) - phi theta - L (Tn n ω - theta))‖} ⊆
        {ω | M ≤ ‖r n • (Tn n ω - theta)‖})
    (hW_OP : StochasticBounded P
      (fun n ω => r n • (Tn n ω - theta)))
    (hR_meas : ∀ n, AEMeasurable
      (fun ω => r n • (phi (Tn n ω) - phi theta - L (Tn n ω - theta))) P) :
    TendstoInDistribution
      (fun n ω => r n • (phi (Tn n ω) - phi theta)) atTop
      (fun ω => L (T ω)) (fun _ => P) Q :=
  vaart1998_theorem_3_1_delta_method_of_localization_tight
    (L := L) hW hR_local hW_OP hR_meas

/--
van der Vaart 1998, Theorem 3.1, sequence localization form with stochastic
boundedness derived from convergence in distribution.
-/
theorem vaart1998_theorem_3_1_delta_method_of_localization_distribution
    {Ω : Type v} {Ω' : Type w} {E : Type x} {F : Type y}
    [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
    [MeasurableSpace Ω'] {Q : Measure Ω'} [IsProbabilityMeasure Q]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E] [CompleteSpace E]
    [NormedAddCommGroup F] [NormedSpace ℝ F]
    [MeasurableSpace F] [SecondCountableTopology F] [BorelSpace F]
    [OpensMeasurableSpace F]
    {Tn : ℕ -> Ω -> E} {T : Ω' -> E} {phi : E -> F} {theta : E}
    {r : ℕ -> ℝ}
    (L : E →L[ℝ] F)
    (hW : TendstoInDistribution
      (fun n ω => r n • (Tn n ω - theta)) atTop T (fun _ => P) Q)
    (hR_local : ∀ ε : ℝ, 0 < ε -> ∀ M : ℝ, 0 < M ->
      ∀ᶠ n in atTop,
        {ω |
          ε ≤ ‖r n • (phi (Tn n ω) - phi theta - L (Tn n ω - theta))‖} ⊆
        {ω | M ≤ ‖r n • (Tn n ω - theta)‖})
    (hR_meas : ∀ n, AEMeasurable
      (fun ω => r n • (phi (Tn n ω) - phi theta - L (Tn n ω - theta))) P) :
    TendstoInDistribution
      (fun n ω => r n • (phi (Tn n ω) - phi theta)) atTop
      (fun ω => L (T ω)) (fun _ => P) Q :=
  vaart1998_theorem_3_1_delta_method_of_localization_stochasticBounded
    (L := L) hW hR_local
    (vaart1998_stochasticBounded_of_tendstoInDistribution hW)
    hR_meas

end AsymptoticStatistics
end StatInference
