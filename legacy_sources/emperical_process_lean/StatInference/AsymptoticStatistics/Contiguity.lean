import StatInference.AsymptoticStatistics.Basic
import Mathlib.MeasureTheory.Measure.LogLikelihoodRatio
import Mathlib.Probability.Notation

/-!
# van der Vaart 1998 Chapter 6 contiguity interfaces

This module opens the Chapter 6 lane with source-shaped definitions over
mathlib's measure and Radon-Nikodym APIs.  The first layer keeps the textbook
definition of contiguity as an event-sequence zero-probability transfer, then
records the likelihood-ratio notation used by Le Cam lemmas and LAN.
-/

noncomputable section

namespace StatInference
namespace AsymptoticStatistics

open Filter MeasureTheory ProbabilityTheory
open scoped ENNReal ProbabilityTheory Topology

/--
van der Vaart 1998, Chapter 6: `P_n` is contiguous with respect to `Q_n` if
every event sequence whose `Q_n`-probability tends to zero also has
`P_n`-probability tending to zero.

The definition is stated with `Measure.real` because the existing Vaart lane
uses real-valued probabilities for convergence-in-probability and
outer-probability handoffs.
-/
def Vaart1998Contiguous
    {Ω : Type*} [MeasurableSpace Ω]
    (P Q : ℕ -> Measure Ω) : Prop :=
  ∀ A : ℕ -> Set Ω,
    (∀ n : ℕ, MeasurableSet (A n)) ->
      Tendsto (fun n : ℕ => (Q n).real (A n)) atTop (𝓝 0) ->
        Tendsto (fun n : ℕ => (P n).real (A n)) atTop (𝓝 0)

/--
Bundled source certificate for one-sided contiguity.
-/
structure Vaart1998ContiguitySource
    {Ω : Type*} [MeasurableSpace Ω]
    (P Q : ℕ -> Measure Ω) where
  /-- The textbook event-sequence zero-probability transfer. -/
  contiguous : Vaart1998Contiguous P Q

/--
van der Vaart 1998, Chapter 6: mutual contiguity of two sequences of measures.
-/
structure Vaart1998MutuallyContiguous
    {Ω : Type*} [MeasurableSpace Ω]
    (P Q : ℕ -> Measure Ω) where
  /-- `P_n` is contiguous with respect to `Q_n`. -/
  left_contiguous : Vaart1998Contiguous P Q
  /-- `Q_n` is contiguous with respect to `P_n`. -/
  right_contiguous : Vaart1998Contiguous Q P

/--
Contiguity is reflexive.
-/
theorem vaart1998_contiguous_refl
    {Ω : Type*} [MeasurableSpace Ω]
    (P : ℕ -> Measure Ω) :
    Vaart1998Contiguous P P := by
  intro A hA hP
  exact hP

/--
The reflexive contiguity source.
-/
theorem Vaart1998ContiguitySource.refl
    {Ω : Type*} [MeasurableSpace Ω]
    (P : ℕ -> Measure Ω) :
    Vaart1998ContiguitySource P P :=
  { contiguous := vaart1998_contiguous_refl P }

/--
Contiguity is transitive in the textbook direction:
if `P_n` is contiguous with respect to `Q_n` and `Q_n` is contiguous with
respect to `R_n`, then `P_n` is contiguous with respect to `R_n`.
-/
theorem vaart1998_contiguous_trans
    {Ω : Type*} [MeasurableSpace Ω]
    {P Q R : ℕ -> Measure Ω}
    (hPQ : Vaart1998Contiguous P Q)
    (hQR : Vaart1998Contiguous Q R) :
    Vaart1998Contiguous P R := by
  intro A hA hR
  exact hPQ A hA (hQR A hA hR)

/--
Transitivity for bundled contiguity sources.
-/
theorem Vaart1998ContiguitySource.trans
    {Ω : Type*} [MeasurableSpace Ω]
    {P Q R : ℕ -> Measure Ω}
    (hPQ : Vaart1998ContiguitySource P Q)
    (hQR : Vaart1998ContiguitySource Q R) :
    Vaart1998ContiguitySource P R :=
  { contiguous := vaart1998_contiguous_trans hPQ.contiguous hQR.contiguous }

/--
Mutual contiguity is symmetric.
-/
theorem Vaart1998MutuallyContiguous.symm
    {Ω : Type*} [MeasurableSpace Ω]
    {P Q : ℕ -> Measure Ω}
    (h : Vaart1998MutuallyContiguous P Q) :
    Vaart1998MutuallyContiguous Q P :=
  { left_contiguous := h.right_contiguous
    right_contiguous := h.left_contiguous }

/--
A uniform real-probability domination bound implies contiguity.

This is a first elementary source lemma for Chapter 6: if eventually every
measurable event has `P_n`-probability at most a fixed multiple of its
`Q_n`-probability, then `P_n` is contiguous with respect to `Q_n`.
-/
theorem vaart1998_contiguous_of_eventually_measureReal_le_mul
    {Ω : Type*} [MeasurableSpace Ω]
    {P Q : ℕ -> Measure Ω} {C : ℝ}
    (_hC_nonneg : 0 ≤ C)
    (hbound : ∀ᶠ n in atTop,
      ∀ A : Set Ω, MeasurableSet A ->
        (P n).real A ≤ C * (Q n).real A) :
    Vaart1998Contiguous P Q := by
  intro A hA hQ
  have hupper :
      Tendsto (fun n : ℕ => C * (Q n).real (A n)) atTop (𝓝 0) := by
    simpa using tendsto_const_nhds.mul hQ
  refine squeeze_zero'
    (Eventually.of_forall fun _ => measureReal_nonneg) ?_ hupper
  filter_upwards [hbound] with n hn
  exact hn (A n) (hA n)

/--
The domination criterion with multiplicative constant `1`.
-/
theorem vaart1998_contiguous_of_eventually_measureReal_le
    {Ω : Type*} [MeasurableSpace Ω]
    {P Q : ℕ -> Measure Ω}
    (hbound : ∀ᶠ n in atTop,
      ∀ A : Set Ω, MeasurableSet A ->
        (P n).real A ≤ (Q n).real A) :
    Vaart1998Contiguous P Q :=
  vaart1998_contiguous_of_eventually_measureReal_le_mul
    (P := P) (Q := Q) (C := 1) (by norm_num) (by
      filter_upwards [hbound] with n hn
      intro A hA
      simpa using hn A hA)

/--
van der Vaart 1998 Chapter 6 likelihood-ratio notation, backed by mathlib's
Radon-Nikodym derivative.
-/
noncomputable def vaart1998_likelihoodRatio
    {Ω : Type*} [MeasurableSpace Ω]
    (P Q : Measure Ω) (ω : Ω) : ℝ≥0∞ :=
  P.rnDeriv Q ω

/--
van der Vaart 1998 Chapter 6 log-likelihood ratio, backed by mathlib's
`MeasureTheory.llr`.
-/
noncomputable def vaart1998_logLikelihoodRatio
    {Ω : Type*} [MeasurableSpace Ω]
    (P Q : Measure Ω) (ω : Ω) : ℝ :=
  MeasureTheory.llr P Q ω

/--
The Vaart log-likelihood-ratio notation is the real logarithm of the
Radon-Nikodym likelihood ratio.
-/
theorem vaart1998_logLikelihoodRatio_eq_log_likelihoodRatio_toReal
    {Ω : Type*} [MeasurableSpace Ω]
    (P Q : Measure Ω) :
    vaart1998_logLikelihoodRatio P Q =
      fun ω => Real.log ((vaart1998_likelihoodRatio P Q ω).toReal) := by
  rfl

/--
The likelihood ratio is measurable.
-/
theorem vaart1998_likelihoodRatio_measurable
    {Ω : Type*} [MeasurableSpace Ω]
    (P Q : Measure Ω) :
    Measurable (vaart1998_likelihoodRatio P Q) :=
  Measure.measurable_rnDeriv P Q

/--
A bounded likelihood ratio gives measure domination.

This is the Radon-Nikodym core of the first Chapter 6 contiguity criterion:
if `dP/dQ ≤ C` almost surely under `Q`, then `P ≤ C • Q`.
-/
theorem vaart1998_measure_le_smul_of_likelihoodRatio_le
    {Ω : Type*} [MeasurableSpace Ω]
    {P Q : Measure Ω} [P.HaveLebesgueDecomposition Q]
    {C : ℝ≥0∞}
    (hAC : P ≪ Q)
    (hLR : vaart1998_likelihoodRatio P Q ≤ᵐ[Q] fun _ => C) :
    P ≤ C • Q := by
  calc
    P = Q.withDensity (vaart1998_likelihoodRatio P Q) := by
      change P = Q.withDensity (P.rnDeriv Q)
      exact (Measure.withDensity_rnDeriv_eq P Q hAC).symm
    _ ≤ Q.withDensity (fun _ => C) := by
      exact withDensity_mono hLR
    _ = C • Q := by
      simp

/--
Real-probability form of bounded likelihood-ratio domination.
-/
theorem vaart1998_measureReal_le_mul_of_likelihoodRatio_le_ofReal
    {Ω : Type*} [MeasurableSpace Ω]
    {P Q : Measure Ω} [P.HaveLebesgueDecomposition Q] [IsFiniteMeasure Q]
    {C : ℝ}
    (hC_nonneg : 0 ≤ C)
    (hAC : P ≪ Q)
    (hLR : vaart1998_likelihoodRatio P Q ≤ᵐ[Q] fun _ => ENNReal.ofReal C)
    (A : Set Ω) :
    P.real A ≤ C * Q.real A := by
  have hleMeasure : P ≤ ENNReal.ofReal C • Q :=
    vaart1998_measure_le_smul_of_likelihoodRatio_le
      (P := P) (Q := Q) (C := ENNReal.ofReal C) hAC hLR
  haveI : IsFiniteMeasure (ENNReal.ofReal C • Q) :=
    Measure.smul_finite Q ENNReal.ofReal_ne_top
  calc
    P.real A ≤ ((ENNReal.ofReal C) • Q).real A := by
      exact ENNReal.toReal_mono (by finiteness) (hleMeasure A)
    _ = C * Q.real A := by
      simp [hC_nonneg]

/--
Event split behind the Le Cam likelihood-ratio criterion.

For a fixed event `A` and threshold `C`, split `A` into the part where the
likelihood ratio is at most `C` and its likelihood-ratio tail.  The bounded
part is controlled by `C * Q(A)`, and the tail is measured under `P`.
-/
theorem vaart1998_measureReal_le_mul_add_likelihoodRatio_tail_ofReal
    {Ω : Type*} [MeasurableSpace Ω]
    {P Q : Measure Ω} [P.HaveLebesgueDecomposition Q]
    [IsFiniteMeasure P] [IsFiniteMeasure Q]
    {C : ℝ}
    (hC_nonneg : 0 ≤ C)
    (hAC : P ≪ Q)
    {A : Set Ω} (hA : MeasurableSet A) :
    P.real A ≤ C * Q.real A +
      P.real {ω | ENNReal.ofReal C < vaart1998_likelihoodRatio P Q ω} := by
  let B : Set Ω := {ω | vaart1998_likelihoodRatio P Q ω ≤ ENNReal.ofReal C}
  let T : Set Ω := {ω | ENNReal.ofReal C < vaart1998_likelihoodRatio P Q ω}
  have hB_meas : MeasurableSet B := by
    exact measurableSet_le (vaart1998_likelihoodRatio_measurable P Q) measurable_const
  have hAB_meas : MeasurableSet (A ∩ B) := hA.inter hB_meas
  have hP_eq : P = Q.withDensity (vaart1998_likelihoodRatio P Q) := by
    change P = Q.withDensity (P.rnDeriv Q)
    exact (Measure.withDensity_rnDeriv_eq P Q hAC).symm
  have hbounded_enn : P (A ∩ B) ≤ ENNReal.ofReal C * Q (A ∩ B) := by
    calc
      P (A ∩ B) = Q.withDensity (vaart1998_likelihoodRatio P Q) (A ∩ B) := by
        exact congrArg (fun μ : Measure Ω => μ (A ∩ B)) hP_eq
      _ = ∫⁻ ω in A ∩ B, vaart1998_likelihoodRatio P Q ω ∂Q := by
        rw [withDensity_apply _ hAB_meas]
      _ ≤ ∫⁻ _ in A ∩ B, ENNReal.ofReal C ∂Q := by
        refine setLIntegral_mono_ae' hAB_meas ?_
        exact Eventually.of_forall (fun _ hω => hω.2)
      _ = ENNReal.ofReal C * Q (A ∩ B) := by
        rw [setLIntegral_const]
  have hbounded_measure : P (A ∩ B) ≤ ((ENNReal.ofReal C) • Q) (A ∩ B) := by
    simpa [Measure.smul_apply, smul_eq_mul] using hbounded_enn
  have hbounded_real : P.real (A ∩ B) ≤ C * Q.real A := by
    haveI : IsFiniteMeasure (ENNReal.ofReal C • Q) :=
      Measure.smul_finite Q ENNReal.ofReal_ne_top
    calc
      P.real (A ∩ B) ≤ ((ENNReal.ofReal C) • Q).real (A ∩ B) := by
        exact ENNReal.toReal_mono (by finiteness) hbounded_measure
      _ = C * Q.real (A ∩ B) := by
        simp [hC_nonneg]
      _ ≤ C * Q.real A := by
        exact mul_le_mul_of_nonneg_left (measureReal_mono Set.inter_subset_left) hC_nonneg
  have hsplit : A = (A ∩ B) ∪ (A ∩ T) := by
    ext ω
    constructor
    · intro hωA
      by_cases hle : vaart1998_likelihoodRatio P Q ω ≤ ENNReal.ofReal C
      · exact Or.inl ⟨hωA, hle⟩
      · exact Or.inr ⟨hωA, lt_of_not_ge hle⟩
    · intro hω
      exact hω.elim (fun h => h.1) (fun h => h.1)
  have htail_mono : P.real (A ∩ T) ≤ P.real T := by
    exact measureReal_mono Set.inter_subset_right
  calc
    P.real A = P.real ((A ∩ B) ∪ (A ∩ T)) := by
      exact congrArg P.real hsplit
    _ ≤ P.real (A ∩ B) + P.real (A ∩ T) := measureReal_union_le _ _
    _ ≤ C * Q.real A + P.real T := by
      exact add_le_add hbounded_real htail_mono

/--
Chapter 6 bounded-likelihood-ratio contiguity criterion.

If eventually `P_n` is absolutely continuous with respect to `Q_n` and the
likelihood ratios `dP_n/dQ_n` are eventually bounded by a fixed finite real
constant, then `P_n` is contiguous with respect to `Q_n`.
-/
theorem vaart1998_contiguous_of_eventually_likelihoodRatio_le_ofReal
    {Ω : Type*} [MeasurableSpace Ω]
    {P Q : ℕ -> Measure Ω} {C : ℝ}
    [∀ n : ℕ, (P n).HaveLebesgueDecomposition (Q n)]
    [∀ n : ℕ, IsFiniteMeasure (Q n)]
    (hC_nonneg : 0 ≤ C)
    (hAC : ∀ᶠ n in atTop, P n ≪ Q n)
    (hLR : ∀ᶠ n in atTop,
      vaart1998_likelihoodRatio (P n) (Q n) ≤ᵐ[Q n] fun _ => ENNReal.ofReal C) :
    Vaart1998Contiguous P Q := by
  refine vaart1998_contiguous_of_eventually_measureReal_le_mul
    (P := P) (Q := Q) (C := C) hC_nonneg ?_
  filter_upwards [hAC, hLR] with n hnAC hnLR
  intro A _hA
  exact vaart1998_measureReal_le_mul_of_likelihoodRatio_le_ofReal
    (P := P n) (Q := Q n) (C := C) hC_nonneg hnAC hnLR A

/--
Bundled source form of the bounded-likelihood-ratio contiguity criterion.
-/
theorem Vaart1998ContiguitySource.of_eventually_likelihoodRatio_le_ofReal
    {Ω : Type*} [MeasurableSpace Ω]
    {P Q : ℕ -> Measure Ω} {C : ℝ}
    [∀ n : ℕ, (P n).HaveLebesgueDecomposition (Q n)]
    [∀ n : ℕ, IsFiniteMeasure (Q n)]
    (hC_nonneg : 0 ≤ C)
    (hAC : ∀ᶠ n in atTop, P n ≪ Q n)
    (hLR : ∀ᶠ n in atTop,
      vaart1998_likelihoodRatio (P n) (Q n) ≤ᵐ[Q n] fun _ => ENNReal.ofReal C) :
    Vaart1998ContiguitySource P Q :=
  { contiguous :=
      vaart1998_contiguous_of_eventually_likelihoodRatio_le_ofReal
        (P := P) (Q := Q) (C := C) hC_nonneg hAC hLR }

/--
Le Cam-style likelihood-ratio tail criterion for contiguity.

If the likelihood-ratio tails are eventually small under `P_n`, then every
`Q_n`-null event sequence is also `P_n`-null.  This is the non-uniform
version of the bounded-likelihood-ratio criterion: choose a fixed truncation
level for a given error tolerance, use the bounded part on
`{dP_n/dQ_n ≤ C}`, and absorb the tail under `P_n`.
-/
theorem vaart1998_contiguous_of_likelihoodRatio_tail_tight_ofReal
    {Ω : Type*} [MeasurableSpace Ω]
    {P Q : ℕ -> Measure Ω}
    [∀ n : ℕ, (P n).HaveLebesgueDecomposition (Q n)]
    [∀ n : ℕ, IsFiniteMeasure (P n)]
    [∀ n : ℕ, IsFiniteMeasure (Q n)]
    (hAC : ∀ᶠ n in atTop, P n ≪ Q n)
    (htail : ∀ ε : ℝ, 0 < ε ->
      ∃ C : ℝ, 0 ≤ C ∧
        ∀ᶠ n in atTop,
          (P n).real
            {ω | ENNReal.ofReal C < vaart1998_likelihoodRatio (P n) (Q n) ω} < ε) :
    Vaart1998Contiguous P Q := by
  intro A hA hQ
  rw [tendsto_order]
  constructor
  · intro a ha
    exact Eventually.of_forall fun _ => lt_of_lt_of_le ha measureReal_nonneg
  · intro ε hε
    have hε2 : 0 < ε / 2 := half_pos hε
    rcases htail (ε / 2) hε2 with ⟨C, hC_nonneg, htail_event⟩
    have hbounded_tendsto :
        Tendsto (fun n : ℕ => C * (Q n).real (A n)) atTop (𝓝 0) := by
      simpa using tendsto_const_nhds.mul hQ
    have hbounded_event :
        ∀ᶠ n : ℕ in atTop, C * (Q n).real (A n) < ε / 2 :=
      (tendsto_order.1 hbounded_tendsto).2 (ε / 2) hε2
    filter_upwards [hAC, htail_event, hbounded_event] with n hnAC hnTail hnBound
    have hsplit_bound :=
      vaart1998_measureReal_le_mul_add_likelihoodRatio_tail_ofReal
        (P := P n) (Q := Q n) (C := C) hC_nonneg hnAC (hA n)
    calc
      (P n).real (A n) ≤ C * (Q n).real (A n) +
          (P n).real
            {ω | ENNReal.ofReal C < vaart1998_likelihoodRatio (P n) (Q n) ω} :=
        hsplit_bound
      _ < ε := by linarith

/--
Bundled source form of the likelihood-ratio tail criterion.
-/
theorem Vaart1998ContiguitySource.of_likelihoodRatio_tail_tight_ofReal
    {Ω : Type*} [MeasurableSpace Ω]
    {P Q : ℕ -> Measure Ω}
    [∀ n : ℕ, (P n).HaveLebesgueDecomposition (Q n)]
    [∀ n : ℕ, IsFiniteMeasure (P n)]
    [∀ n : ℕ, IsFiniteMeasure (Q n)]
    (hAC : ∀ᶠ n in atTop, P n ≪ Q n)
    (htail : ∀ ε : ℝ, 0 < ε ->
      ∃ C : ℝ, 0 ≤ C ∧
        ∀ᶠ n in atTop,
          (P n).real
            {ω | ENNReal.ofReal C < vaart1998_likelihoodRatio (P n) (Q n) ω} < ε) :
    Vaart1998ContiguitySource P Q :=
  { contiguous :=
      vaart1998_contiguous_of_likelihoodRatio_tail_tight_ofReal
        (P := P) (Q := Q) hAC htail }

/--
Likelihood-ratio tails are controlled by log-likelihood-ratio tails.

Under absolute continuity, the possible `∞` values of `dP/dQ` are `P`-null,
so the pointwise implication `dP/dQ > exp r -> log (dP/dQ) > r` gives the
real-measure comparison needed by log-likelihood-ratio tail criteria.
-/
theorem vaart1998_likelihoodRatio_tail_measureReal_le_logLikelihoodRatio_tail_ofReal
    {Ω : Type*} [MeasurableSpace Ω]
    {P Q : Measure Ω} [P.HaveLebesgueDecomposition Q] [IsFiniteMeasure P]
    (hAC : P ≪ Q) (r : ℝ) :
    P.real {ω | ENNReal.ofReal (Real.exp r) < vaart1998_likelihoodRatio P Q ω} ≤
      P.real {ω | r < vaart1998_logLikelihoodRatio P Q ω} := by
  have hfinite : ∀ᵐ ω ∂P, vaart1998_likelihoodRatio P Q ω ≠ ∞ := by
    have hlt : ∀ᵐ ω ∂P, vaart1998_likelihoodRatio P Q ω < ∞ := by
      change {ω | (P.rnDeriv Q) ω < ∞} ∈ ae P
      exact hAC.ae_le (Measure.rnDeriv_lt_top P Q)
    filter_upwards [hlt] with ω hω
    exact ne_of_lt hω
  have hset_le :
      {ω | ENNReal.ofReal (Real.exp r) < vaart1998_likelihoodRatio P Q ω} ≤ᶠ[ae P]
        {ω | r < vaart1998_logLikelihoodRatio P Q ω} := by
    filter_upwards [hfinite] with ω hωfinite hωtail
    have htoReal : Real.exp r < (vaart1998_likelihoodRatio P Q ω).toReal := by
      exact
        (ENNReal.ofReal_lt_iff_lt_toReal (le_of_lt (Real.exp_pos r)) hωfinite).1 hωtail
    have hlog :
        Real.log (Real.exp r) < Real.log ((vaart1998_likelihoodRatio P Q ω).toReal) := by
      exact Real.log_lt_log (Real.exp_pos r) htoReal
    change r < Real.log ((P.rnDeriv Q) ω).toReal
    simpa [vaart1998_likelihoodRatio] using hlog
  have hmeasure_le :
      P {ω | ENNReal.ofReal (Real.exp r) < vaart1998_likelihoodRatio P Q ω} ≤
        P {ω | r < vaart1998_logLikelihoodRatio P Q ω} :=
    MeasureTheory.measure_mono_ae hset_le
  exact ENNReal.toReal_mono (by finiteness) hmeasure_le

/--
Le Cam-style log-likelihood-ratio tail criterion for contiguity.

This source-shaped version is often the form used in LAN and local asymptotic
normality arguments: if the upper tails of `log (dP_n/dQ_n)` are eventually
small under `P_n`, then `P_n` is contiguous with respect to `Q_n`.
-/
theorem vaart1998_contiguous_of_logLikelihoodRatio_tail_tight_ofReal
    {Ω : Type*} [MeasurableSpace Ω]
    {P Q : ℕ -> Measure Ω}
    [∀ n : ℕ, (P n).HaveLebesgueDecomposition (Q n)]
    [∀ n : ℕ, IsFiniteMeasure (P n)]
    [∀ n : ℕ, IsFiniteMeasure (Q n)]
    (hAC : ∀ᶠ n in atTop, P n ≪ Q n)
    (htail : ∀ ε : ℝ, 0 < ε ->
      ∃ r : ℝ,
        ∀ᶠ n in atTop,
          (P n).real
            {ω | r < vaart1998_logLikelihoodRatio (P n) (Q n) ω} < ε) :
    Vaart1998Contiguous P Q := by
  refine vaart1998_contiguous_of_likelihoodRatio_tail_tight_ofReal
    (P := P) (Q := Q) hAC ?_
  intro ε hε
  rcases htail ε hε with ⟨r, htail_event⟩
  refine ⟨Real.exp r, le_of_lt (Real.exp_pos r), ?_⟩
  filter_upwards [hAC, htail_event] with n hnAC hnTail
  have hle :=
    vaart1998_likelihoodRatio_tail_measureReal_le_logLikelihoodRatio_tail_ofReal
      (P := P n) (Q := Q n) hnAC r
  exact lt_of_le_of_lt hle hnTail

/--
Bundled source form of the log-likelihood-ratio tail criterion.
-/
theorem Vaart1998ContiguitySource.of_logLikelihoodRatio_tail_tight_ofReal
    {Ω : Type*} [MeasurableSpace Ω]
    {P Q : ℕ -> Measure Ω}
    [∀ n : ℕ, (P n).HaveLebesgueDecomposition (Q n)]
    [∀ n : ℕ, IsFiniteMeasure (P n)]
    [∀ n : ℕ, IsFiniteMeasure (Q n)]
    (hAC : ∀ᶠ n in atTop, P n ≪ Q n)
    (htail : ∀ ε : ℝ, 0 < ε ->
      ∃ r : ℝ,
        ∀ᶠ n in atTop,
          (P n).real
            {ω | r < vaart1998_logLikelihoodRatio (P n) (Q n) ω} < ε) :
    Vaart1998ContiguitySource P Q :=
  { contiguous :=
      vaart1998_contiguous_of_logLikelihoodRatio_tail_tight_ofReal
        (P := P) (Q := Q) hAC htail }

/--
Stochastic boundedness for statistics whose underlying measure can vary with
`n`.  This is the triangular-array form used by Le Cam/LAN arguments.
-/
def Vaart1998MeasureSeqStochasticBounded
    {Ω E : Type*} [MeasurableSpace Ω] [SeminormedAddCommGroup E]
    (P : ℕ -> Measure Ω) (X : ℕ -> Ω -> E) : Prop :=
  ∀ ε : ℝ, 0 < ε ->
    ∃ M : ℝ, 0 < M ∧
      ∀ᶠ n in atTop, (P n).real {ω | M ≤ ‖X n ω‖} < ε

/--
An `O_{P_n}(1)` log-likelihood-ratio sequence has small upper tails.
-/
theorem vaart1998_logLikelihoodRatio_tail_tight_of_stochasticBounded
    {Ω : Type*} [MeasurableSpace Ω]
    {P Q : ℕ -> Measure Ω}
    [∀ n : ℕ, IsFiniteMeasure (P n)]
    (hbounded : Vaart1998MeasureSeqStochasticBounded P
      (fun n ω => vaart1998_logLikelihoodRatio (P n) (Q n) ω)) :
    ∀ ε : ℝ, 0 < ε ->
      ∃ r : ℝ,
        ∀ᶠ n in atTop,
          (P n).real
            {ω | r < vaart1998_logLikelihoodRatio (P n) (Q n) ω} < ε := by
  intro ε hε
  rcases hbounded ε hε with ⟨M, _hMpos, htail⟩
  refine ⟨M, ?_⟩
  filter_upwards [htail] with n hn
  have hmono :
      (P n).real {ω | M < vaart1998_logLikelihoodRatio (P n) (Q n) ω} ≤
        (P n).real {ω | M ≤ ‖vaart1998_logLikelihoodRatio (P n) (Q n) ω‖} := by
    exact measureReal_mono (by
      intro ω hω
      change M < vaart1998_logLikelihoodRatio (P n) (Q n) ω at hω
      change M ≤ ‖vaart1998_logLikelihoodRatio (P n) (Q n) ω‖
      exact le_trans (le_of_lt hω) (le_abs_self _))
  exact lt_of_le_of_lt hmono hn

/--
Le Cam-style stochastic-boundedness criterion for one-sided contiguity.

If `P_n ≪ Q_n` eventually and the log-likelihood ratios
`log (dP_n/dQ_n)` are `O_{P_n}(1)`, then `P_n` is contiguous with respect to
`Q_n`.
-/
theorem vaart1998_contiguous_of_logLikelihoodRatio_stochasticBounded
    {Ω : Type*} [MeasurableSpace Ω]
    {P Q : ℕ -> Measure Ω}
    [∀ n : ℕ, (P n).HaveLebesgueDecomposition (Q n)]
    [∀ n : ℕ, IsFiniteMeasure (P n)]
    [∀ n : ℕ, IsFiniteMeasure (Q n)]
    (hAC : ∀ᶠ n in atTop, P n ≪ Q n)
    (hbounded : Vaart1998MeasureSeqStochasticBounded P
      (fun n ω => vaart1998_logLikelihoodRatio (P n) (Q n) ω)) :
    Vaart1998Contiguous P Q :=
  vaart1998_contiguous_of_logLikelihoodRatio_tail_tight_ofReal
    (P := P) (Q := Q) hAC
    (vaart1998_logLikelihoodRatio_tail_tight_of_stochasticBounded
      (P := P) (Q := Q) hbounded)

/--
Source package for the Le Cam log-likelihood-ratio stochastic-boundedness
criterion.
-/
structure Vaart1998LogLikelihoodStochasticBoundedContiguitySource
    {Ω : Type*} [MeasurableSpace Ω]
    (P Q : ℕ -> Measure Ω) where
  /-- Eventual absolute continuity of the local alternatives. -/
  ac_eventually : ∀ᶠ n in atTop, P n ≪ Q n
  /-- The log-likelihood ratios are `O_{P_n}(1)`. -/
  logLikelihoodRatio_stochasticallyBounded :
    Vaart1998MeasureSeqStochasticBounded P
      (fun n ω => vaart1998_logLikelihoodRatio (P n) (Q n) ω)

/--
The bundled Le Cam log-likelihood-ratio source yields a contiguity source.
-/
theorem Vaart1998LogLikelihoodStochasticBoundedContiguitySource.contiguitySource
    {Ω : Type*} [MeasurableSpace Ω]
    {P Q : ℕ -> Measure Ω}
    [∀ n : ℕ, (P n).HaveLebesgueDecomposition (Q n)]
    [∀ n : ℕ, IsFiniteMeasure (P n)]
    [∀ n : ℕ, IsFiniteMeasure (Q n)]
    (S : Vaart1998LogLikelihoodStochasticBoundedContiguitySource P Q) :
    Vaart1998ContiguitySource P Q :=
  { contiguous :=
      vaart1998_contiguous_of_logLikelihoodRatio_stochasticBounded
        (P := P) (Q := Q)
        S.ac_eventually S.logLikelihoodRatio_stochasticallyBounded }

/--
The log-likelihood ratio is measurable.
-/
theorem vaart1998_logLikelihoodRatio_measurable
    {Ω : Type*} [MeasurableSpace Ω]
    (P Q : Measure Ω) :
    Measurable (vaart1998_logLikelihoodRatio P Q) :=
  MeasureTheory.measurable_llr P Q

/--
The self log-likelihood ratio is zero almost surely.
-/
theorem vaart1998_logLikelihoodRatio_self_ae_eq_zero
    {Ω : Type*} [MeasurableSpace Ω]
    (P : Measure Ω) [SigmaFinite P] :
    vaart1998_logLikelihoodRatio P P =ᵐ[P] fun _ => 0 := by
  change MeasureTheory.llr P P =ᵐ[P] (0 : Ω -> ℝ)
  exact MeasureTheory.llr_self P

end AsymptoticStatistics
end StatInference
