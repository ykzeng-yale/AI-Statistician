import StatInference.EmpiricalProcess.PMeasurable
import StatInference.EmpiricalProcess.Theorem243
import StatInference.ProbabilityMeasure.StrongLaw
import StatInference.ProbabilityTheory.Martingale
import Mathlib.MeasureTheory.Measure.MeasuredSets

/-!
# Durrett 2019 backwards martingale wrappers

This module packages Durrett Section 4.7 reverse-time martingales around the
shared `ℕᵒᵈ` submartingale convergence primitive developed for the VdV&W
empirical-process lane.
-/

namespace StatInference
namespace ProbabilityTheory

open Filter MeasureTheory _root_.ProbabilityTheory

open scoped BigOperators ENNReal Function NNReal ProbabilityTheory symmDiff Topology

/-! ## Durrett, Section 4.7 -/

/--
Durrett 2019, Section 4.7: a decreasing natural family of sigma-fields,
read as an increasing filtration on the dual natural order.
-/
abbrev durrett2019_backwardsFiltration
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    (𝒢 : ℕ -> MeasurableSpace Ω) (h𝒢_mono : Antitone 𝒢)
    (h𝒢_le : ∀ n, 𝒢 n ≤ mΩ) :
    Filtration ℕᵒᵈ mΩ where
  seq n := 𝒢 (OrderDual.ofDual n)
  mono' := by
    intro n m hnm
    exact h𝒢_mono (show OrderDual.ofDual m ≤ OrderDual.ofDual n from hnm)
  le' n := h𝒢_le (OrderDual.ofDual n)

/-- Display form of `durrett2019_backwardsFiltration`. -/
theorem durrett2019_backwardsFiltration_apply
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    (𝒢 : ℕ -> MeasurableSpace Ω) (h𝒢_mono : Antitone 𝒢)
    (h𝒢_le : ∀ n, 𝒢 n ≤ mΩ) (n : ℕᵒᵈ) :
    durrett2019_backwardsFiltration 𝒢 h𝒢_mono h𝒢_le n =
      𝒢 (OrderDual.ofDual n) :=
  rfl

/--
Durrett 2019, Section 4.7: the textbook backwards martingale data, indexed by
ordinary `n` as `X_{-n}`, is a mathlib martingale over the dual natural order.
-/
theorem durrett2019_backwards_martingale_of_condExp_nat
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} {𝒢 : ℕ -> MeasurableSpace Ω} {X : ℕ -> Ω -> ℝ}
    (h𝒢_mono : Antitone 𝒢) (h𝒢_le : ∀ n, 𝒢 n ≤ mΩ)
    (hX_meas : ∀ n, StronglyMeasurable[𝒢 n] (X n))
    (hX_cond :
      ∀ {m n : ℕ}, m ≤ n -> P[X m | 𝒢 n] =ᵐ[P] X n) :
    Martingale
      (fun n : ℕᵒᵈ => X (OrderDual.ofDual n))
      (durrett2019_backwardsFiltration 𝒢 h𝒢_mono h𝒢_le) P := by
  refine ⟨?_, ?_⟩
  · intro n
    exact hX_meas (OrderDual.ofDual n)
  · intro n m hnm
    exact hX_cond (show OrderDual.ofDual m ≤ OrderDual.ofDual n from hnm)

/--
Durrett 2019, Theorem 4.7.1 source identity: a backwards martingale is the
conditional expectation of its terminal value at every reverse time.
-/
theorem durrett2019_theorem_4_7_1_backwards_martingale_ae_eq_condExp_terminal
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} {ℱ : Filtration ℕᵒᵈ mΩ}
    {X : ℕᵒᵈ -> Ω -> ℝ} (hX : Martingale X ℱ P) (n : ℕ) :
    X (OrderDual.toDual n) =ᵐ[P]
      P[X (OrderDual.toDual 0) | ℱ (OrderDual.toDual n)] := by
  exact
    (hX.condExp_ae_eq
      (show OrderDual.toDual n ≤ OrderDual.toDual 0 by
        change (0 : ℕ) ≤ n
        exact Nat.zero_le n)).symm

/--
Durrett 2019, Theorem 4.7.1 uniform-integrability input.  The backwards
martingale representation by conditional expectations of the terminal value
implies uniform integrability.
-/
theorem durrett2019_theorem_4_7_1_uniformIntegrable_of_backwards_martingale
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} [IsFiniteMeasure P] {ℱ : Filtration ℕᵒᵈ mΩ}
    {X : ℕᵒᵈ -> Ω -> ℝ} (hX : Martingale X ℱ P) :
    UniformIntegrable X 1 P := by
  have hterminal_int : Integrable (X (OrderDual.toDual 0)) P :=
    hX.integrable (OrderDual.toDual 0)
  have hcond_ui :
      UniformIntegrable
        (fun n : ℕᵒᵈ => P[X (OrderDual.toDual 0) | ℱ n]) 1 P :=
    hterminal_int.uniformIntegrable_condExp (fun n => ℱ.le n)
  refine hcond_ui.ae_eq ?_
  intro n
  exact
    hX.condExp_ae_eq
      (show n ≤ OrderDual.toDual 0 by
        change (0 : ℕ) ≤ OrderDual.ofDual n
        exact Nat.zero_le (OrderDual.ofDual n))

/--
Durrett 2019, Theorem 4.7.1, a.s. reverse-time convergence for an
`L¹`-bounded `ℕᵒᵈ` submartingale.  This is the shared VdV&W order-dual
convergence theorem, exposed with Durrett naming.
-/
theorem durrett2019_theorem_4_7_1_ae_exists_limit_of_eLpNorm_one_bdd
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} [IsFiniteMeasure P] {ℱ : Filtration ℕᵒᵈ mΩ}
    {X : ℕᵒᵈ -> Ω -> ℝ} {R : ℝ≥0}
    (hX : Submartingale X ℱ P)
    (hbdd : ∀ n : ℕᵒᵈ, eLpNorm (X n) 1 P ≤ (R : ℝ≥0∞)) :
    ∀ᵐ ω ∂P, ∃ limit : ℝ,
      Tendsto (fun n : ℕ => X (OrderDual.toDual n) ω) atTop (𝓝 limit) :=
  (StatInference.VdVWOrderDualSubmartingaleConvergenceHandoff.proved
    (Ω := Ω) (μ := P)) hX hbdd

/--
Durrett 2019, Theorem 4.7.1, a.s. existence of the backwards martingale limit.
-/
theorem durrett2019_theorem_4_7_1_ae_exists_limit_of_backwards_martingale
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} [IsFiniteMeasure P] {ℱ : Filtration ℕᵒᵈ mΩ}
    {X : ℕᵒᵈ -> Ω -> ℝ} (hX : Martingale X ℱ P) :
    ∀ᵐ ω ∂P, ∃ limit : ℝ,
      Tendsto (fun n : ℕ => X (OrderDual.toDual n) ω) atTop (𝓝 limit) := by
  have hUI :=
    durrett2019_theorem_4_7_1_uniformIntegrable_of_backwards_martingale
      (P := P) (ℱ := ℱ) (X := X) hX
  obtain ⟨R, hR⟩ := hUI.2.2
  exact
    durrett2019_theorem_4_7_1_ae_exists_limit_of_eLpNorm_one_bdd
      (P := P) (ℱ := ℱ) (X := X) (R := R) hX.submartingale hR

/--
Durrett 2019, Theorem 4.7.1, `L¹` convergence consumer.  Once the reverse-time
limit is identified as `Y`, uniform integrability upgrades a.s. convergence to
`L¹` convergence.
-/
theorem durrett2019_theorem_4_7_1_eLpNorm_one_tendsto_of_ae_tendsto_uniformIntegrable
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} [IsFiniteMeasure P]
    {X : ℕᵒᵈ -> Ω -> ℝ} {Y : Ω -> ℝ}
    (hAe :
      ∀ᵐ ω ∂P,
        Tendsto (fun n : ℕ => X (OrderDual.toDual n) ω) atTop (𝓝 (Y ω)))
    (hUI : UniformIntegrable (fun n : ℕ => X (OrderDual.toDual n)) 1 P) :
    Tendsto
      (fun n : ℕ => eLpNorm (X (OrderDual.toDual n) - Y) 1 P)
      atTop (𝓝 0) := by
  have hprob :
      TendstoInMeasure P
        (fun n : ℕ => X (OrderDual.toDual n)) atTop Y :=
    tendstoInMeasure_of_tendsto_ae
      (μ := P) (f := fun n : ℕ => X (OrderDual.toDual n)) (g := Y)
      (fun n => hUI.aestronglyMeasurable n) hAe
  exact
    durrett2019_theorem_4_6_3_eLpNorm_one_tendsto_zero_of_tendstoInMeasure_uniformIntegrable
      (P := P) (X := fun n : ℕ => X (OrderDual.toDual n)) (Y := Y)
      hprob hUI

/--
Durrett 2019, Theorem 4.7.1, read a backwards martingale along ordinary
natural time.  The reverse-time process is uniformly integrable.
-/
theorem durrett2019_theorem_4_7_1_read_uniformIntegrable_of_backwards_martingale
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} [IsFiniteMeasure P] {ℱ : Filtration ℕᵒᵈ mΩ}
    {X : ℕᵒᵈ -> Ω -> ℝ} (hX : Martingale X ℱ P) :
    UniformIntegrable (fun n : ℕ => X (OrderDual.toDual n)) 1 P := by
  have hterminal_int : Integrable (X (OrderDual.toDual 0)) P :=
    hX.integrable (OrderDual.toDual 0)
  have hcond_ui :
      UniformIntegrable
        (fun n : ℕ => P[X (OrderDual.toDual 0) | ℱ (OrderDual.toDual n)])
        1 P :=
    hterminal_int.uniformIntegrable_condExp (fun n => ℱ.le (OrderDual.toDual n))
  refine hcond_ui.ae_eq ?_
  intro n
  exact
    hX.condExp_ae_eq
      (show OrderDual.toDual n ≤ OrderDual.toDual 0 by
        change (0 : ℕ) ≤ n
        exact Nat.zero_le n)

/--
Durrett 2019, Theorem 4.7.1, integrability of an identified reverse-time
limit.  This is the integrability input needed for the tail conditional
expectation identification in Theorem 4.7.2.
-/
theorem durrett2019_theorem_4_7_1_integrable_limit_of_ae_tendsto_backwards_martingale
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} [IsFiniteMeasure P] {ℱ : Filtration ℕᵒᵈ mΩ}
    {X : ℕᵒᵈ -> Ω -> ℝ} {Y : Ω -> ℝ}
    (hX : Martingale X ℱ P)
    (hAe :
      ∀ᵐ ω ∂P,
        Tendsto (fun n : ℕ => X (OrderDual.toDual n) ω) atTop (𝓝 (Y ω))) :
    Integrable Y P := by
  have hread_ui :
      UniformIntegrable (fun n : ℕ => X (OrderDual.toDual n)) 1 P :=
    durrett2019_theorem_4_7_1_read_uniformIntegrable_of_backwards_martingale
      (P := P) (ℱ := ℱ) (X := X) hX
  exact hread_ui.integrable_of_ae_tendsto hAe

/--
Durrett 2019, Theorem 4.7.1, `L¹` convergence for a backwards martingale once
the reverse-time a.s. limit has been identified.
-/
theorem durrett2019_theorem_4_7_1_eLpNorm_one_tendsto_of_ae_tendsto_backwards_martingale
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} [IsFiniteMeasure P] {ℱ : Filtration ℕᵒᵈ mΩ}
    {X : ℕᵒᵈ -> Ω -> ℝ} {Y : Ω -> ℝ}
    (hX : Martingale X ℱ P)
    (hAe :
      ∀ᵐ ω ∂P,
        Tendsto (fun n : ℕ => X (OrderDual.toDual n) ω) atTop (𝓝 (Y ω))) :
    Tendsto
      (fun n : ℕ => eLpNorm (X (OrderDual.toDual n) - Y) 1 P)
      atTop (𝓝 0) := by
  have hread_ui :
      UniformIntegrable (fun n : ℕ => X (OrderDual.toDual n)) 1 P := by
    exact
      durrett2019_theorem_4_7_1_read_uniformIntegrable_of_backwards_martingale
        (P := P) (ℱ := ℱ) (X := X) hX
  exact
    durrett2019_theorem_4_7_1_eLpNorm_one_tendsto_of_ae_tendsto_uniformIntegrable
      (P := P) (X := X) (Y := Y) hAe hread_ui

/--
Durrett 2019, Theorem 4.7.2, tail measurability of the identified backwards
martingale limit.

The proof uses the canonical real-valued modification
`limsup_n X_{-n}`.  For every fixed reverse time `m`, shifting the tail by
`m` makes the same limsup measurable with respect to `F_{-m}`; measurability
with respect to every `F_{-m}` gives measurability with respect to their
intersection.
-/
theorem durrett2019_theorem_4_7_2_limit_aestronglyMeasurable_tail_of_ae_tendsto
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} {ℱ : Filtration ℕᵒᵈ mΩ}
    {X : ℕᵒᵈ -> Ω -> ℝ} {Y : Ω -> ℝ}
    (hX : Martingale X ℱ P)
    (hAe :
      ∀ᵐ ω ∂P,
        Tendsto (fun n : ℕ => X (OrderDual.toDual n) ω) atTop (𝓝 (Y ω))) :
    AEStronglyMeasurable[⨅ n : ℕ, ℱ (OrderDual.toDual n)] Y P := by
  let Z : Ω -> ℝ := fun ω =>
    limsup (fun n : ℕ => X (OrderDual.toDual n) ω) atTop
  have hZ_meas_each :
      ∀ m : ℕ, Measurable[ℱ (OrderDual.toDual m)] Z := by
    intro m
    have hshift_meas :
        Measurable[ℱ (OrderDual.toDual m)] fun ω =>
          limsup (fun n : ℕ => X (OrderDual.toDual (n + m)) ω) atTop := by
      refine
        Measurable.limsup
          (mδ := ℱ (OrderDual.toDual m))
          (f := fun n : ℕ => fun ω => X (OrderDual.toDual (n + m)) ω)
          ?_
      intro n
      exact
        ((hX.stronglyMeasurable (OrderDual.toDual (n + m))).mono
          (ℱ.mono
            (show OrderDual.toDual (n + m) ≤ OrderDual.toDual m by
              change m ≤ n + m
              exact Nat.le_add_left m n))).measurable
    have hshift_eq :
        (fun ω =>
          limsup
            (fun n : ℕ => X (OrderDual.toDual n + OrderDual.toDual m) ω)
            atTop) = Z := by
      funext ω
      have hseq :
          (fun n : ℕ => X (OrderDual.toDual n + OrderDual.toDual m) ω) =
            fun n : ℕ => X (OrderDual.toDual (n + m)) ω := by
        funext n
        rw [show OrderDual.toDual n + OrderDual.toDual m =
          OrderDual.toDual (n + m) from rfl]
      rw [hseq]
      exact Filter.limsup_nat_add (fun n : ℕ => X (OrderDual.toDual n) ω) m
    simpa [hshift_eq] using hshift_meas
  have hZ_meas_tail :
      Measurable[⨅ n : ℕ, ℱ (OrderDual.toDual n)] Z := by
    intro s hs
    exact
      MeasurableSpace.measurableSet_iInf.mpr
        (fun n => hZ_meas_each n hs)
  have hZ_eq_Y : Z =ᵐ[P] Y := by
    filter_upwards [hAe] with ω hω
    exact hω.limsup_eq
  exact hZ_meas_tail.stronglyMeasurable.aestronglyMeasurable.congr hZ_eq_Y

/--
Durrett 2019, Theorem 4.7.2, conditional-expectation identification of a
reverse-time `L¹` limit.  If the limit is measurable with respect to the tail
sigma-field, then the martingale set-integral identities identify it as
`E[X_0 | F_{-\infty}]`.
-/
theorem durrett2019_theorem_4_7_2_ae_eq_condExp_tail_of_L1_tendsto
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} [IsFiniteMeasure P] {ℱ : Filtration ℕᵒᵈ mΩ}
    {X : ℕᵒᵈ -> Ω -> ℝ} {Y : Ω -> ℝ}
    (hX : Martingale X ℱ P)
    (hY_int : Integrable Y P)
    (hY_tail :
      AEStronglyMeasurable[⨅ n : ℕ, ℱ (OrderDual.toDual n)] Y P)
    (hL1 :
      Tendsto
        (fun n : ℕ => eLpNorm (X (OrderDual.toDual n) - Y) 1 P)
        atTop (𝓝 0)) :
    Y =ᵐ[P] P[X (OrderDual.toDual 0) |
      ⨅ n : ℕ, ℱ (OrderDual.toDual n)] := by
  let ℱtail : MeasurableSpace Ω := ⨅ n : ℕ, ℱ (OrderDual.toDual n)
  have htail_le : ℱtail ≤ mΩ := by
    exact
      (iInf_le (fun n : ℕ => ℱ (OrderDual.toDual n)) 0).trans
        (ℱ.le (OrderDual.toDual 0))
  haveI : SigmaFinite (P.trim htail_le) := inferInstance
  refine
    ae_eq_condExp_of_forall_setIntegral_eq
      (μ := P) (m := ℱtail) (m₀ := mΩ)
      (f := X (OrderDual.toDual 0)) (g := Y)
      htail_le (hX.integrable (OrderDual.toDual 0)) ?_ ?_ ?_
  · intro _s _hs _hμs
    exact hY_int.integrableOn
  · intro s hs _hμs
    have hs_each :
        ∀ n : ℕ, MeasurableSet[ℱ (OrderDual.toDual n)] s := by
      simpa [ℱtail] using (MeasurableSpace.measurableSet_iInf.mp hs)
    have htend :
        Tendsto
          (fun n : ℕ => ∫ ω in s, X (OrderDual.toDual n) ω ∂P)
          atTop (𝓝 (∫ ω in s, Y ω ∂P)) :=
      durrett2019_lemma_4_6_5_tendsto_setIntegral_of_eLpNorm_one_tendsto_zero
        (mΩ := mΩ) (P := P)
        (X := fun n : ℕ => X (OrderDual.toDual n)) (Y := Y)
        (fun n => hX.integrable (OrderDual.toDual n)) hY_int hL1 s
    have hsame :
        ∀ n : ℕ,
          ∫ ω in s, X (OrderDual.toDual n) ω ∂P =
            ∫ ω in s, X (OrderDual.toDual 0) ω ∂P := by
      intro n
      exact
        hX.setIntegral_eq
          (show OrderDual.toDual n ≤ OrderDual.toDual 0 by
            change (0 : ℕ) ≤ n
            exact Nat.zero_le n)
          (hs_each n)
    have hconst :
        Tendsto
          (fun n : ℕ => ∫ ω in s, X (OrderDual.toDual n) ω ∂P)
          atTop (𝓝 (∫ ω in s, X (OrderDual.toDual 0) ω ∂P)) := by
      have hevent :
          ∀ᶠ n in atTop,
            ∫ ω in s, X (OrderDual.toDual 0) ω ∂P =
              ∫ ω in s, X (OrderDual.toDual n) ω ∂P :=
        Eventually.of_forall fun n => (hsame n).symm
      exact tendsto_const_nhds.congr' hevent
    exact tendsto_nhds_unique htend hconst
  · simpa [ℱtail] using hY_tail

/--
Durrett 2019, Theorem 4.7.2, source-shaped conditional-expectation
identification.  Once a backwards martingale has an a.s. reverse-time limit
which is tail measurable, the limit is the conditional expectation of the
terminal value with respect to the tail sigma-field.
-/
theorem durrett2019_theorem_4_7_2_ae_eq_condExp_tail_of_ae_tendsto
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} [IsFiniteMeasure P] {ℱ : Filtration ℕᵒᵈ mΩ}
    {X : ℕᵒᵈ -> Ω -> ℝ} {Y : Ω -> ℝ}
    (hX : Martingale X ℱ P)
    (hY_tail :
      AEStronglyMeasurable[⨅ n : ℕ, ℱ (OrderDual.toDual n)] Y P)
    (hAe :
      ∀ᵐ ω ∂P,
        Tendsto (fun n : ℕ => X (OrderDual.toDual n) ω) atTop (𝓝 (Y ω))) :
    Y =ᵐ[P] P[X (OrderDual.toDual 0) |
      ⨅ n : ℕ, ℱ (OrderDual.toDual n)] := by
  have hY_int :
      Integrable Y P :=
    durrett2019_theorem_4_7_1_integrable_limit_of_ae_tendsto_backwards_martingale
      (P := P) (ℱ := ℱ) (X := X) (Y := Y) hX hAe
  have hL1 :
      Tendsto
        (fun n : ℕ => eLpNorm (X (OrderDual.toDual n) - Y) 1 P)
        atTop (𝓝 0) :=
    durrett2019_theorem_4_7_1_eLpNorm_one_tendsto_of_ae_tendsto_backwards_martingale
      (P := P) (ℱ := ℱ) (X := X) (Y := Y) hX hAe
  exact
    durrett2019_theorem_4_7_2_ae_eq_condExp_tail_of_L1_tendsto
      (P := P) (ℱ := ℱ) (X := X) (Y := Y) hX hY_int hY_tail hL1

/--
Durrett 2019, Theorem 4.7.2.  A backwards martingale limit is the conditional
expectation of the terminal value with respect to the reverse tail
sigma-field.
-/
theorem durrett2019_theorem_4_7_2_ae_eq_condExp_tail_of_ae_tendsto_backwards_martingale
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} [IsFiniteMeasure P] {ℱ : Filtration ℕᵒᵈ mΩ}
    {X : ℕᵒᵈ -> Ω -> ℝ} {Y : Ω -> ℝ}
    (hX : Martingale X ℱ P)
    (hAe :
      ∀ᵐ ω ∂P,
        Tendsto (fun n : ℕ => X (OrderDual.toDual n) ω) atTop (𝓝 (Y ω))) :
    Y =ᵐ[P] P[X (OrderDual.toDual 0) |
      ⨅ n : ℕ, ℱ (OrderDual.toDual n)] := by
  have hY_tail :
      AEStronglyMeasurable[⨅ n : ℕ, ℱ (OrderDual.toDual n)] Y P :=
    durrett2019_theorem_4_7_2_limit_aestronglyMeasurable_tail_of_ae_tendsto
      (P := P) (ℱ := ℱ) (X := X) (Y := Y) hX hAe
  exact
    durrett2019_theorem_4_7_2_ae_eq_condExp_tail_of_ae_tendsto
      (P := P) (ℱ := ℱ) (X := X) (Y := Y) hX hY_tail hAe

/--
Durrett 2019, Theorem 4.7.3, backwards Lévy setup.  Conditional
expectations along a reverse-time filtration form a backwards martingale.
-/
theorem durrett2019_theorem_4_7_3_backwards_condExp_martingale
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} [IsFiniteMeasure P] {ℱ : Filtration ℕᵒᵈ mΩ}
    (f : Ω -> ℝ) :
    Martingale (fun n : ℕᵒᵈ => P[f | ℱ n]) ℱ P := by
  exact martingale_condExp f ℱ P

/--
Durrett 2019, Theorem 4.7.3, backwards Lévy theorem in a.s. form.

Conditional expectations along a decreasing filtration converge a.s. to the
conditional expectation on the reverse tail sigma-field.
-/
theorem durrett2019_theorem_4_7_3_condExp_ae_tendsto_tail_condExp
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} [IsFiniteMeasure P] {ℱ : Filtration ℕᵒᵈ mΩ}
    (f : Ω -> ℝ) :
    ∀ᵐ ω ∂P,
      Tendsto
        (fun n : ℕ => P[f | ℱ (OrderDual.toDual n)] ω)
        atTop
        (𝓝 (P[f | ⨅ n : ℕ, ℱ (OrderDual.toDual n)] ω)) := by
  let X : ℕᵒᵈ -> Ω -> ℝ := fun n => P[f | ℱ n]
  have hX : Martingale X ℱ P :=
    durrett2019_theorem_4_7_3_backwards_condExp_martingale
      (P := P) (ℱ := ℱ) f
  have hExists :
      ∀ᵐ ω ∂P, ∃ limit : ℝ,
        Tendsto (fun n : ℕ => X (OrderDual.toDual n) ω) atTop (𝓝 limit) :=
    durrett2019_theorem_4_7_1_ae_exists_limit_of_backwards_martingale
      (P := P) (ℱ := ℱ) (X := X) hX
  obtain ⟨Y, _hY_meas, hY_tendsto⟩ :
      ∃ Y : Ω -> ℝ, Measurable Y ∧
        ∀ᵐ ω ∂P,
          Tendsto (fun n : ℕ => X (OrderDual.toDual n) ω) atTop (𝓝 (Y ω)) :=
    measurable_limit_of_tendsto_metrizable_ae
      (μ := P) (f := fun n : ℕ => fun ω => X (OrderDual.toDual n) ω)
      (L := atTop)
      (fun n => StronglyMeasurable.aemeasurable (μ := P)
        ((stronglyMeasurable_condExp (μ := P)
          (m := ℱ (OrderDual.toDual n)) (f := f)).mono
            (ℱ.le (OrderDual.toDual n))))
      hExists
  have hY_eq_terminal_tail :
      Y =ᵐ[P] P[X (OrderDual.toDual 0) |
        ⨅ n : ℕ, ℱ (OrderDual.toDual n)] := by
    simpa [X] using
      (durrett2019_theorem_4_7_2_ae_eq_condExp_tail_of_ae_tendsto_backwards_martingale
        (P := P) (ℱ := ℱ) (X := X) (Y := Y) hX hY_tendsto)
  have htail_le_zero :
      (⨅ n : ℕ, ℱ (OrderDual.toDual n)) ≤ ℱ (OrderDual.toDual 0) := by
    exact iInf_le (fun n : ℕ => ℱ (OrderDual.toDual n)) 0
  have hterminal_tail :
      P[X (OrderDual.toDual 0) |
          ⨅ n : ℕ, ℱ (OrderDual.toDual n)] =ᵐ[P]
        P[f | ⨅ n : ℕ, ℱ (OrderDual.toDual n)] := by
    simpa [X] using
      (condExp_condExp_of_le (μ := P) (f := f)
        htail_le_zero (ℱ.le (OrderDual.toDual 0)))
  have hY_eq_tail :
      Y =ᵐ[P] P[f | ⨅ n : ℕ, ℱ (OrderDual.toDual n)] :=
    hY_eq_terminal_tail.trans hterminal_tail
  filter_upwards [hY_tendsto, hY_eq_tail] with ω hlim hYω
  simpa [X, hYω] using hlim

/--
Durrett 2019, Theorem 4.7.3, backwards Lévy theorem in `L¹` form.
-/
theorem durrett2019_theorem_4_7_3_condExp_eLpNorm_one_tendsto_tail_condExp
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} [IsFiniteMeasure P] {ℱ : Filtration ℕᵒᵈ mΩ}
    (f : Ω -> ℝ) :
    Tendsto
      (fun n : ℕ =>
        eLpNorm
          (P[f | ℱ (OrderDual.toDual n)] -
            P[f | ⨅ n : ℕ, ℱ (OrderDual.toDual n)])
          1 P)
      atTop (𝓝 0) := by
  let X : ℕᵒᵈ -> Ω -> ℝ := fun n => P[f | ℱ n]
  have hX : Martingale X ℱ P :=
    durrett2019_theorem_4_7_3_backwards_condExp_martingale
      (P := P) (ℱ := ℱ) f
  have hAe :
      ∀ᵐ ω ∂P,
        Tendsto
          (fun n : ℕ => X (OrderDual.toDual n) ω)
          atTop
          (𝓝 (P[f | ⨅ n : ℕ, ℱ (OrderDual.toDual n)] ω)) := by
    simpa [X] using
      (durrett2019_theorem_4_7_3_condExp_ae_tendsto_tail_condExp
        (P := P) (ℱ := ℱ) f)
  simpa [X] using
    (durrett2019_theorem_4_7_1_eLpNorm_one_tendsto_of_ae_tendsto_backwards_martingale
      (P := P) (ℱ := ℱ) (X := X)
      (Y := fun ω => P[f | ⨅ n : ℕ, ℱ (OrderDual.toDual n)] ω) hX hAe)

/--
Durrett 2019, Theorem 4.7.3, textbook decreasing-filtration display form.
-/
theorem durrett2019_theorem_4_7_3_condExp_nat_ae_tendsto_tail_condExp
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} [IsFiniteMeasure P] {𝒢 : ℕ -> MeasurableSpace Ω}
    (h𝒢_mono : Antitone 𝒢) (h𝒢_le : ∀ n, 𝒢 n ≤ mΩ)
    (f : Ω -> ℝ) :
    ∀ᵐ ω ∂P,
      Tendsto
        (fun n : ℕ => P[f | 𝒢 n] ω)
        atTop
        (𝓝 (P[f | ⨅ n : ℕ, 𝒢 n] ω)) := by
  simpa [durrett2019_backwardsFiltration] using
    (durrett2019_theorem_4_7_3_condExp_ae_tendsto_tail_condExp
      (P := P) (ℱ := durrett2019_backwardsFiltration 𝒢 h𝒢_mono h𝒢_le) f)

/--
Durrett 2019, Theorem 4.7.3, textbook decreasing-filtration `L¹` display form.
-/
theorem durrett2019_theorem_4_7_3_condExp_nat_eLpNorm_one_tendsto_tail_condExp
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} [IsFiniteMeasure P] {𝒢 : ℕ -> MeasurableSpace Ω}
    (h𝒢_mono : Antitone 𝒢) (h𝒢_le : ∀ n, 𝒢 n ≤ mΩ)
    (f : Ω -> ℝ) :
    Tendsto
      (fun n : ℕ =>
        eLpNorm
          (P[f | 𝒢 n] - P[f | ⨅ n : ℕ, 𝒢 n])
          1 P)
      atTop (𝓝 0) := by
  simpa [durrett2019_backwardsFiltration] using
    (durrett2019_theorem_4_7_3_condExp_eLpNorm_one_tendsto_tail_condExp
      (P := P) (ℱ := durrett2019_backwardsFiltration 𝒢 h𝒢_mono h𝒢_le) f)

/--
Durrett 2019, Theorem 4.7.3 consumer.  If the reverse tail conditional
expectation is a.e. constant, the backwards Lévy limit is that constant.
-/
theorem durrett2019_theorem_4_7_3_condExp_nat_ae_tendsto_const_of_tail_condExp_ae_eq_const
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} [IsFiniteMeasure P] {𝒢 : ℕ -> MeasurableSpace Ω}
    (h𝒢_mono : Antitone 𝒢) (h𝒢_le : ∀ n, 𝒢 n ≤ mΩ)
    (f : Ω -> ℝ) (c : ℝ)
    (hTail : P[f | ⨅ n : ℕ, 𝒢 n] =ᵐ[P] fun _ => c) :
    ∀ᵐ ω ∂P,
      Tendsto
        (fun n : ℕ => P[f | 𝒢 n] ω)
        atTop
        (𝓝 c) := by
  filter_upwards
    [durrett2019_theorem_4_7_3_condExp_nat_ae_tendsto_tail_condExp
      (P := P) (𝒢 := 𝒢) h𝒢_mono h𝒢_le f, hTail] with ω hlim htail
  simpa [htail] using hlim

/--
Durrett 2019, Example 4.7.4 tail-triviality bridge.  If a random variable is
measurable with respect to a sigma-field independent of the reverse tail, then
its reverse-tail conditional expectation is its ordinary expectation.
-/
theorem durrett2019_example_4_7_4_tail_condExp_ae_eq_integral_of_independent
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} [IsFiniteMeasure P] {mX : MeasurableSpace Ω}
    {𝒢 : ℕ -> MeasurableSpace Ω} {f : Ω -> ℝ}
    (hmX : mX ≤ mΩ) (h𝒢_le : ∀ n, 𝒢 n ≤ mΩ)
    (hf_meas : StronglyMeasurable[mX] f)
    (hindep : Indep mX (⨅ n : ℕ, 𝒢 n) P) :
    P[f | ⨅ n : ℕ, 𝒢 n] =ᵐ[P] fun _ => ∫ ω, f ω ∂P := by
  have htail_le : (⨅ n : ℕ, 𝒢 n) ≤ mΩ :=
    (iInf_le (fun n : ℕ => 𝒢 n) 0).trans (h𝒢_le 0)
  exact _root_.MeasureTheory.condExp_indep_eq
    (μ := P) (m₁ := mX) (m₂ := ⨅ n : ℕ, 𝒢 n) (m := mΩ)
    (f := f) hmX htail_le hf_meas hindep

/--
Durrett 2019, Example 4.7.4 tail-triviality bridge.  If every event in the
reverse tail sigma-field has probability zero or one, then conditioning any
integrable real random variable on that reverse tail gives its expectation.
-/
theorem durrett2019_example_4_7_4_tail_condExp_ae_eq_integral_of_tail_zero_or_one
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {𝒢 : ℕ -> MeasurableSpace Ω} {f : Ω -> ℝ}
    (h𝒢_le : ∀ n, 𝒢 n ≤ mΩ)
    (hf_int : Integrable f P)
    (hzeroOne :
      ∀ A : Set Ω, MeasurableSet[⨅ n : ℕ, 𝒢 n] A -> P A = 0 ∨ P A = 1) :
    P[f | ⨅ n : ℕ, 𝒢 n] =ᵐ[P] fun _ => ∫ ω, f ω ∂P := by
  let 𝒯 : MeasurableSpace Ω := ⨅ n : ℕ, 𝒢 n
  have htail_le : 𝒯 ≤ mΩ :=
    (iInf_le (fun n : ℕ => 𝒢 n) 0).trans (h𝒢_le 0)
  have hconst :
      (fun _ : Ω => ∫ ω, f ω ∂P) =ᵐ[P] P[f | 𝒯] := by
    refine
      ae_eq_condExp_of_forall_setIntegral_eq
        (μ := P) (m := 𝒯) (m₀ := mΩ)
        (f := f) (g := fun _ : Ω => ∫ ω, f ω ∂P)
        htail_le hf_int ?_ ?_ ?_
    · intro _A _hA hμA
      exact integrableOn_const hμA.ne
    · intro A hA _hμA
      have hA_ambient : @MeasurableSet Ω mΩ A := htail_le A hA
      rcases hzeroOne A hA with hA_zero | hA_one
      · rw [setIntegral_measure_zero (fun _ : Ω => ∫ ω, f ω ∂P) hA_zero,
          setIntegral_measure_zero f hA_zero]
      · have hA_ae : ∀ᵐ ω ∂P, ω ∈ A :=
          (mem_ae_iff_prob_eq_one (μ := P) hA_ambient).2 hA_one
        have hcompl_zero :
            ∀ᵐ ω ∂P, ω ∉ A -> f ω = 0 := by
          filter_upwards [hA_ae] with ω hω hω_not
          exact False.elim (hω_not hω)
        rw [setIntegral_const, measureReal_def, hA_one, ENNReal.toReal_one,
          one_smul, setIntegral_eq_integral_of_ae_compl_eq_zero hcompl_zero]
    · exact stronglyMeasurable_const.aestronglyMeasurable
  exact hconst.symm

/--
Durrett 2019, Example 4.7.4 zero-one support.  If the reverse filtration is
the tail-block filtration generated by an independent sequence of
sigma-fields, then every event in the reverse tail sigma-field has probability
zero or one.
-/
theorem durrett2019_example_4_7_4_tail_zero_or_one_of_iIndep_tailBlocks
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} {s 𝒢 : ℕ -> MeasurableSpace Ω}
    (hs_le : ∀ n, s n ≤ mΩ)
    (hs_indep : _root_.ProbabilityTheory.iIndep s P)
    (h𝒢_tail :
      ∀ n, 𝒢 n = ⨆ i : ℕ, ⨆ _ : i ≥ n, s i) :
    ∀ A : Set Ω, MeasurableSet[⨅ n : ℕ, 𝒢 n] A ->
      P A = 0 ∨ P A = 1 := by
  intro A hA
  refine
    durrett2019_theorem_4_3_8_tail_event_measure_zero_or_one
      (ν := P) (s := s) (A := A) hs_le hs_indep ?_
  refine
    durrett2019_theorem_4_3_8_tail_event_measurable_of_forall_tailBlock_measurable
      (s := s) (A := A) ?_
  intro n
  have hA_each : MeasurableSet[𝒢 n] A :=
    (MeasurableSpace.measurableSet_iInf.mp hA) n
  rw [h𝒢_tail n] at hA_each
  exact hA_each

/--
Durrett 2019, Example 4.7.4 tail-triviality bridge with the zero-one side
discharged by Kolmogorov's zero-one law for independent tail blocks.
-/
theorem durrett2019_example_4_7_4_tail_condExp_ae_eq_integral_of_iIndep_tailBlocks
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} {s 𝒢 : ℕ -> MeasurableSpace Ω} {f : Ω -> ℝ}
    (h𝒢_le : ∀ n, 𝒢 n ≤ mΩ)
    (hs_le : ∀ n, s n ≤ mΩ)
    (hs_indep : _root_.ProbabilityTheory.iIndep s P)
    (h𝒢_tail :
      ∀ n, 𝒢 n = ⨆ i : ℕ, ⨆ _ : i ≥ n, s i)
    (hf_int : Integrable f P) :
    P[f | ⨅ n : ℕ, 𝒢 n] =ᵐ[P] fun _ => ∫ ω, f ω ∂P := by
  haveI : IsProbabilityMeasure P := hs_indep.isProbabilityMeasure
  exact
    durrett2019_example_4_7_4_tail_condExp_ae_eq_integral_of_tail_zero_or_one
      (P := P) (𝒢 := 𝒢) (f := f) h𝒢_le hf_int
      (durrett2019_example_4_7_4_tail_zero_or_one_of_iIndep_tailBlocks
        (P := P) (s := s) (𝒢 := 𝒢) hs_le hs_indep h𝒢_tail)

/--
Durrett 2019, Example 4.7.4 route bridge.  A process that is a.e. equal to
reverse-time conditional expectations converges once the reverse tail
conditional expectation is a.e. constant.
-/
theorem durrett2019_example_4_7_4_ae_tendsto_of_ae_eq_condExp_nat_and_tail_const
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} [IsFiniteMeasure P] {𝒢 : ℕ -> MeasurableSpace Ω}
    (h𝒢_mono : Antitone 𝒢) (h𝒢_le : ∀ n, 𝒢 n ≤ mΩ)
    (A : ℕ -> Ω -> ℝ) (f : Ω -> ℝ) (c : ℝ)
    (hA :
      ∀ n, A n =ᵐ[P] P[f | 𝒢 n])
    (hTail : P[f | ⨅ n : ℕ, 𝒢 n] =ᵐ[P] fun _ => c) :
    ∀ᵐ ω ∂P,
      Tendsto
        (fun n : ℕ => A n ω)
        atTop
        (𝓝 c) := by
  have hCond :
      ∀ᵐ ω ∂P,
        Tendsto
          (fun n : ℕ => P[f | 𝒢 n] ω)
          atTop
          (𝓝 c) :=
    durrett2019_theorem_4_7_3_condExp_nat_ae_tendsto_const_of_tail_condExp_ae_eq_const
      (P := P) (𝒢 := 𝒢) h𝒢_mono h𝒢_le f c hTail
  have hA_all :
      ∀ᵐ ω ∂P, ∀ n : ℕ, A n ω = P[f | 𝒢 n] ω :=
    ae_all_iff.2 hA
  filter_upwards [hCond, hA_all] with ω hlim hAω
  exact Tendsto.congr'
    (Eventually.of_forall (fun n : ℕ => (hAω n).symm)) hlim

/--
Durrett 2019, Example 4.7.4 route bridge with the initial finite prefix
ignored.  This is the form needed for averages whose conditional-expectation
display starts at positive `n`.
-/
theorem durrett2019_example_4_7_4_ae_tendsto_of_eventually_ae_eq_condExp_nat_and_tail_const
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} [IsFiniteMeasure P] {𝒢 : ℕ -> MeasurableSpace Ω}
    (h𝒢_mono : Antitone 𝒢) (h𝒢_le : ∀ n, 𝒢 n ≤ mΩ)
    (A : ℕ -> Ω -> ℝ) (f : Ω -> ℝ) (c : ℝ) (N : ℕ)
    (hA :
      ∀ n, N ≤ n -> A n =ᵐ[P] P[f | 𝒢 n])
    (hTail : P[f | ⨅ n : ℕ, 𝒢 n] =ᵐ[P] fun _ => c) :
    ∀ᵐ ω ∂P,
      Tendsto
        (fun n : ℕ => A n ω)
        atTop
        (𝓝 c) := by
  have hCond :
      ∀ᵐ ω ∂P,
        Tendsto
          (fun n : ℕ => P[f | 𝒢 n] ω)
          atTop
          (𝓝 c) :=
    durrett2019_theorem_4_7_3_condExp_nat_ae_tendsto_const_of_tail_condExp_ae_eq_const
      (P := P) (𝒢 := 𝒢) h𝒢_mono h𝒢_le f c hTail
  have hA_all :
      ∀ᵐ ω ∂P, ∀ n : ℕ, N ≤ n -> A n ω = P[f | 𝒢 n] ω := by
    refine ae_all_iff.2 ?_
    intro n
    by_cases hn : N ≤ n
    · filter_upwards [hA n hn] with ω hω
      intro _hn
      exact hω
    · exact Eventually.of_forall fun _ω hNn => False.elim (hn hNn)
  filter_upwards [hCond, hA_all] with ω hlim hAω
  exact Tendsto.congr'
    (eventually_atTop.2 ⟨N, fun n hn => (hAω n hn).symm⟩) hlim

/--
Durrett 2019, Example 4.7.4 route bridge with the tail-constant side
discharged from a zero-one law for the reverse tail sigma-field.
-/
theorem durrett2019_example_4_7_4_ae_tendsto_of_ae_eq_condExp_nat_and_tail_zero_or_one
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {𝒢 : ℕ -> MeasurableSpace Ω}
    (h𝒢_mono : Antitone 𝒢) (h𝒢_le : ∀ n, 𝒢 n ≤ mΩ)
    (A : ℕ -> Ω -> ℝ) (f : Ω -> ℝ)
    (hf_int : Integrable f P)
    (hA : ∀ n, A n =ᵐ[P] P[f | 𝒢 n])
    (hzeroOne :
      ∀ B : Set Ω, MeasurableSet[⨅ n : ℕ, 𝒢 n] B -> P B = 0 ∨ P B = 1) :
    ∀ᵐ ω ∂P,
      Tendsto
        (fun n : ℕ => A n ω)
        atTop
        (𝓝 (∫ ω, f ω ∂P)) := by
  exact
    durrett2019_example_4_7_4_ae_tendsto_of_ae_eq_condExp_nat_and_tail_const
      (Ω := Ω) (mΩ := mΩ) (P := P) (𝒢 := 𝒢)
      h𝒢_mono h𝒢_le A f (∫ ω, f ω ∂P) hA
      (durrett2019_example_4_7_4_tail_condExp_ae_eq_integral_of_tail_zero_or_one
        (Ω := Ω) (mΩ := mΩ) (P := P) (𝒢 := 𝒢) (f := f)
        h𝒢_le hf_int hzeroOne)

/--
Durrett 2019, Example 4.7.4 route bridge with an ignored finite prefix and the
tail-constant side discharged from a zero-one law for the reverse tail
sigma-field.
-/
theorem durrett2019_example_4_7_4_ae_tendsto_of_eventually_ae_eq_condExp_nat_and_tail_zero_or_one
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} [IsProbabilityMeasure P]
    {𝒢 : ℕ -> MeasurableSpace Ω}
    (h𝒢_mono : Antitone 𝒢) (h𝒢_le : ∀ n, 𝒢 n ≤ mΩ)
    (A : ℕ -> Ω -> ℝ) (f : Ω -> ℝ)
    (hf_int : Integrable f P) (N : ℕ)
    (hA : ∀ n, N ≤ n -> A n =ᵐ[P] P[f | 𝒢 n])
    (hzeroOne :
      ∀ B : Set Ω, MeasurableSet[⨅ n : ℕ, 𝒢 n] B -> P B = 0 ∨ P B = 1) :
    ∀ᵐ ω ∂P,
      Tendsto
        (fun n : ℕ => A n ω)
        atTop
        (𝓝 (∫ ω, f ω ∂P)) := by
  exact
    durrett2019_example_4_7_4_ae_tendsto_of_eventually_ae_eq_condExp_nat_and_tail_const
      (Ω := Ω) (mΩ := mΩ) (P := P) (𝒢 := 𝒢)
      h𝒢_mono h𝒢_le A f (∫ ω, f ω ∂P) N hA
      (durrett2019_example_4_7_4_tail_condExp_ae_eq_integral_of_tail_zero_or_one
        (Ω := Ω) (mΩ := mΩ) (P := P) (𝒢 := 𝒢) (f := f)
        h𝒢_le hf_int hzeroOne)

/--
Durrett 2019, Example 4.7.4 route bridge with the tail-constant side
discharged from independent tail-block sigma-fields.
-/
theorem durrett2019_example_4_7_4_ae_tendsto_of_ae_eq_condExp_nat_and_iIndep_tailBlocks
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} {s 𝒢 : ℕ -> MeasurableSpace Ω}
    (h𝒢_mono : Antitone 𝒢) (h𝒢_le : ∀ n, 𝒢 n ≤ mΩ)
    (hs_le : ∀ n, s n ≤ mΩ)
    (hs_indep : _root_.ProbabilityTheory.iIndep s P)
    (h𝒢_tail :
      ∀ n, 𝒢 n = ⨆ i : ℕ, ⨆ _ : i ≥ n, s i)
    (A : ℕ -> Ω -> ℝ) (f : Ω -> ℝ)
    (hf_int : Integrable f P)
    (hA : ∀ n, A n =ᵐ[P] P[f | 𝒢 n]) :
    ∀ᵐ ω ∂P,
      Tendsto
        (fun n : ℕ => A n ω)
        atTop
        (𝓝 (∫ ω, f ω ∂P)) := by
  haveI : IsProbabilityMeasure P := hs_indep.isProbabilityMeasure
  exact
    durrett2019_example_4_7_4_ae_tendsto_of_ae_eq_condExp_nat_and_tail_zero_or_one
      (Ω := Ω) (mΩ := mΩ) (P := P) (𝒢 := 𝒢)
      h𝒢_mono h𝒢_le A f hf_int hA
      (durrett2019_example_4_7_4_tail_zero_or_one_of_iIndep_tailBlocks
        (P := P) (s := s) (𝒢 := 𝒢) hs_le hs_indep h𝒢_tail)

/--
Durrett 2019, Example 4.7.4 route bridge with the tail-constant side
discharged from independence of the source sigma-field and the reverse tail.
-/
theorem durrett2019_example_4_7_4_ae_tendsto_of_ae_eq_condExp_nat_and_tail_independent
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} [IsFiniteMeasure P] {mX : MeasurableSpace Ω}
    {𝒢 : ℕ -> MeasurableSpace Ω}
    (h𝒢_mono : Antitone 𝒢) (h𝒢_le : ∀ n, 𝒢 n ≤ mΩ)
    (A : ℕ -> Ω -> ℝ) (f : Ω -> ℝ)
    (hmX : mX ≤ mΩ)
    (hf_meas : StronglyMeasurable[mX] f)
    (hA : ∀ n, A n =ᵐ[P] P[f | 𝒢 n])
    (hindep : Indep mX (⨅ n : ℕ, 𝒢 n) P) :
    ∀ᵐ ω ∂P,
      Tendsto
        (fun n : ℕ => A n ω)
        atTop
        (𝓝 (∫ ω, f ω ∂P)) := by
  exact
    durrett2019_example_4_7_4_ae_tendsto_of_ae_eq_condExp_nat_and_tail_const
      (Ω := Ω) (mΩ := mΩ) (P := P) (𝒢 := 𝒢)
      h𝒢_mono h𝒢_le A f (∫ ω, f ω ∂P) hA
      (durrett2019_example_4_7_4_tail_condExp_ae_eq_integral_of_independent
        (Ω := Ω) (mΩ := mΩ) (P := P) (mX := mX) (𝒢 := 𝒢) (f := f)
        hmX h𝒢_le hf_meas hindep)

/-- Durrett 2019, Example 4.7.4 prefix sum `S_n`. -/
@[reducible]
def durrett2019_example_4_7_4_prefixSum
    {Ω : Type*} (ξ : ℕ -> Ω -> ℝ) (n : ℕ) : Ω -> ℝ :=
  fun ω => ∑ i ∈ Finset.range n, ξ i ω

/--
Durrett 2019, Example 4.7.4 reverse-average sigma-field
`sigma(S_n, xi_n, xi_{n+1}, ...)` in zero-based Lean indexing.

This is the concrete sigma-field used to feed the prefix-average conditional
expectation bridge below.  It is written as a supremum of comaps so that the
measurability obligations are direct.
-/
@[reducible]
def durrett2019_example_4_7_4_reverseAverageSigma
    {Ω : Type*} (ξ : ℕ -> Ω -> ℝ) (n : ℕ) : MeasurableSpace Ω :=
  MeasurableSpace.comap
      (durrett2019_example_4_7_4_prefixSum ξ n)
      (inferInstance : MeasurableSpace ℝ) ⊔
    ⨆ i : ℕ, ⨆ _ : i ≥ n,
      MeasurableSpace.comap (ξ i) (inferInstance : MeasurableSpace ℝ)

/--
Durrett 2019, Example 4.7.4 generator set for
`sigma(S_n, xi_n, xi_{n+1}, ...)`.
-/
@[reducible]
def durrett2019_example_4_7_4_reverseAverageGeneratorSet
    {Ω : Type*} (ξ : ℕ -> Ω -> ℝ) (n : ℕ) : Set (Set Ω) :=
  {s | ∃ t : Set ℝ, MeasurableSet t ∧
      s = durrett2019_example_4_7_4_prefixSum ξ n ⁻¹' t} ∪
    {s | ∃ i : ℕ, n ≤ i ∧ ∃ t : Set ℝ, MeasurableSet t ∧ s = ξ i ⁻¹' t}

/-- The prefix sum is measurable in Durrett's reverse-average sigma-field. -/
theorem durrett2019_example_4_7_4_prefixSum_measurable_reverseAverageSigma
    {Ω : Type*} {ξ : ℕ -> Ω -> ℝ} (n : ℕ) :
    Measurable[durrett2019_example_4_7_4_reverseAverageSigma ξ n]
      (durrett2019_example_4_7_4_prefixSum ξ n) :=
  Measurable.of_comap_le le_sup_left

/-- The prefix sum is strongly measurable in Durrett's reverse-average sigma-field. -/
theorem durrett2019_example_4_7_4_prefixSum_stronglyMeasurable_reverseAverageSigma
    {Ω : Type*} {ξ : ℕ -> Ω -> ℝ} (n : ℕ) :
    StronglyMeasurable[durrett2019_example_4_7_4_reverseAverageSigma ξ n]
      (durrett2019_example_4_7_4_prefixSum ξ n) :=
  (durrett2019_example_4_7_4_prefixSum_measurable_reverseAverageSigma
    (ξ := ξ) n).stronglyMeasurable

/-- Tail coordinates are measurable in Durrett's reverse-average sigma-field. -/
theorem durrett2019_example_4_7_4_tailCoordinate_measurable_reverseAverageSigma
    {Ω : Type*} {ξ : ℕ -> Ω -> ℝ} {n i : ℕ} (hi : i ≥ n) :
    Measurable[durrett2019_example_4_7_4_reverseAverageSigma ξ n] (ξ i) := by
  refine Measurable.of_comap_le ?_
  have htail :
      MeasurableSpace.comap (ξ i) (inferInstance : MeasurableSpace ℝ) ≤
        (⨆ j : ℕ, ⨆ _ : j ≥ n,
          MeasurableSpace.comap (ξ j) (inferInstance : MeasurableSpace ℝ)) :=
    le_iSup_of_le i (le_iSup_of_le hi le_rfl)
  exact htail.trans le_sup_right

/--
Durrett's reverse-average sigma-field is a sub-sigma-field of the ambient
space whenever the coordinates are ambient-measurable.
-/
theorem durrett2019_example_4_7_4_reverseAverageSigma_le
    {Ω : Type*} [mΩ : MeasurableSpace Ω] {ξ : ℕ -> Ω -> ℝ} {n : ℕ}
    (hξ_meas : ∀ i, Measurable (ξ i)) :
    durrett2019_example_4_7_4_reverseAverageSigma ξ n ≤ mΩ := by
  refine sup_le ?_ ?_
  · have hsum_meas :
        Measurable (durrett2019_example_4_7_4_prefixSum ξ n) := by
      dsimp [durrett2019_example_4_7_4_prefixSum]
      exact Finset.measurable_fun_sum (Finset.range n) fun i _hi => hξ_meas i
    exact hsum_meas.comap_le
  · exact iSup_le fun i => iSup_le fun _hi => (hξ_meas i).comap_le

/--
The concrete reverse-average sigma-field is equivalently generated by the
prefix-sum preimages and the tail-coordinate preimages.
-/
theorem durrett2019_example_4_7_4_reverseAverageSigma_eq_generateFrom
    {Ω : Type*} {ξ : ℕ -> Ω -> ℝ} {n : ℕ} :
    durrett2019_example_4_7_4_reverseAverageSigma ξ n =
      MeasurableSpace.generateFrom
        (durrett2019_example_4_7_4_reverseAverageGeneratorSet ξ n) := by
  let generator :=
    durrett2019_example_4_7_4_reverseAverageGeneratorSet ξ n
  refine le_antisymm ?_ ?_
  · dsimp [durrett2019_example_4_7_4_reverseAverageSigma]
    refine sup_le ?_ ?_
    · have hprefix :
          Measurable[MeasurableSpace.generateFrom generator]
            (durrett2019_example_4_7_4_prefixSum ξ n) := by
        intro t ht
        exact MeasurableSpace.measurableSet_generateFrom
          (show durrett2019_example_4_7_4_prefixSum ξ n ⁻¹' t ∈ generator from
            Or.inl ⟨t, ht, rfl⟩)
      exact hprefix.comap_le
    · refine iSup_le fun i => iSup_le fun hi => ?_
      have htail :
          Measurable[MeasurableSpace.generateFrom generator] (ξ i) := by
        intro t ht
        exact MeasurableSpace.measurableSet_generateFrom
          (show ξ i ⁻¹' t ∈ generator from
            Or.inr ⟨i, hi, t, ht, rfl⟩)
      exact htail.comap_le
  · refine MeasurableSpace.generateFrom_le ?_
    intro s hs
    rcases hs with
      ⟨t, ht, rfl⟩ | ⟨i, hi, t, ht, rfl⟩
    · exact
        durrett2019_example_4_7_4_prefixSum_measurable_reverseAverageSigma
          (ξ := ξ) n ht
    · exact
        durrett2019_example_4_7_4_tailCoordinate_measurable_reverseAverageSigma
          (ξ := ξ) (n := n) (i := i) hi ht

/--
Later prefix sums are measurable with respect to earlier reverse-average
sigma-fields.  Algebraically, `S_m = S_n + sum_{n <= i < m} xi_i`.
-/
theorem durrett2019_example_4_7_4_prefixSum_measurable_reverseAverageSigma_of_le
    {Ω : Type*} {ξ : ℕ -> Ω -> ℝ} {n m : ℕ} (hnm : n ≤ m) :
    Measurable[durrett2019_example_4_7_4_reverseAverageSigma ξ n]
      (durrett2019_example_4_7_4_prefixSum ξ m) := by
  have hprefix :
      Measurable[durrett2019_example_4_7_4_reverseAverageSigma ξ n]
        (durrett2019_example_4_7_4_prefixSum ξ n) :=
    durrett2019_example_4_7_4_prefixSum_measurable_reverseAverageSigma
      (ξ := ξ) n
  have htail :
      Measurable[durrett2019_example_4_7_4_reverseAverageSigma ξ n]
        (fun ω => ∑ i ∈ Finset.Ico n m, ξ i ω) := by
    exact Finset.measurable_fun_sum (Finset.Ico n m) fun i hi =>
      durrett2019_example_4_7_4_tailCoordinate_measurable_reverseAverageSigma
        (ξ := ξ) (n := n) (i := i) (Finset.mem_Ico.mp hi).1
  have hsum := hprefix.add htail
  have hsum_eq :
      (fun ω =>
        durrett2019_example_4_7_4_prefixSum ξ n ω +
          ∑ i ∈ Finset.Ico n m, ξ i ω) =
        durrett2019_example_4_7_4_prefixSum ξ m := by
    ext ω
    exact Finset.sum_range_add_sum_Ico (fun i => ξ i ω) hnm
  rwa [hsum_eq] at hsum

/--
Durrett's concrete reverse-average sigma-fields decrease with `n`.
-/
theorem durrett2019_example_4_7_4_reverseAverageSigma_antitone
    {Ω : Type*} (ξ : ℕ -> Ω -> ℝ) :
    Antitone (fun n : ℕ =>
      durrett2019_example_4_7_4_reverseAverageSigma ξ n) := by
  intro n m hnm
  change
    durrett2019_example_4_7_4_reverseAverageSigma ξ m ≤
      durrett2019_example_4_7_4_reverseAverageSigma ξ n
  dsimp [durrett2019_example_4_7_4_reverseAverageSigma]
  refine sup_le ?_ ?_
  · exact
      (durrett2019_example_4_7_4_prefixSum_measurable_reverseAverageSigma_of_le
        (ξ := ξ) hnm).comap_le
  · refine iSup_le fun i => iSup_le fun hi => ?_
    exact
      (durrett2019_example_4_7_4_tailCoordinate_measurable_reverseAverageSigma
        (ξ := ξ) (n := n) (i := i) (hnm.trans hi)).comap_le

/--
Every event in Durrett's reverse-average sigma-field is fixed by a measurable
equivalence that leaves the prefix sum and all tail coordinates unchanged.
-/
theorem durrett2019_example_4_7_4_preimage_reverseAverageSigma_eq_of_prefixSum_tail_invariant
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {ξ : ℕ -> Ω -> ℝ} {n : ℕ}
    (T : Ω ≃ᵐ Ω)
    (hprefix :
      (fun ω => durrett2019_example_4_7_4_prefixSum ξ n (T ω)) =
        durrett2019_example_4_7_4_prefixSum ξ n)
    (htail : ∀ i : ℕ, n ≤ i -> (fun ω => ξ i (T ω)) = ξ i) :
    ∀ s : Set Ω,
      MeasurableSet[durrett2019_example_4_7_4_reverseAverageSigma ξ n] s ->
        T ⁻¹' s = s := by
  let generator :=
    durrett2019_example_4_7_4_reverseAverageGeneratorSet ξ n
  intro s hs
  rw [durrett2019_example_4_7_4_reverseAverageSigma_eq_generateFrom] at hs
  refine
    MeasurableSpace.generateFrom_induction generator
      (fun t _ht => T ⁻¹' t = t) ?_ ?_ ?_ ?_ s hs
  · intro t ht _hmeas_t
    rcases ht with
      ⟨target, _htarget, rfl⟩ | ⟨i, hi, target, _htarget, rfl⟩
    · ext ω
      change
        durrett2019_example_4_7_4_prefixSum ξ n (T ω) ∈ target ↔
          durrett2019_example_4_7_4_prefixSum ξ n ω ∈ target
      rw [show
        durrett2019_example_4_7_4_prefixSum ξ n (T ω) =
          durrett2019_example_4_7_4_prefixSum ξ n ω from congrFun hprefix ω]
    · ext ω
      change ξ i (T ω) ∈ target ↔ ξ i ω ∈ target
      rw [show ξ i (T ω) = ξ i ω from congrFun (htail i hi) ω]
  · simp
  · intro t _ht hpre
    ext ω
    simp [hpre]
  · intro sets _hsets hpre
    ext ω
    simp [hpre]

/--
Durrett 2019, Example 4.7.4 conditional-expectation algebra core.  If the
prefix sum is measurable with respect to the reverse sigma-field and the
conditional expectations of all prefix coordinates are the same as that of the
first coordinate, then the conditional expectation of the first coordinate is
the empirical average of the prefix.

The remaining textbook-specific work is to prove the symmetry hypothesis
`hsym` from the concrete sigma-field
`sigma(S_n, xi_{n+1}, xi_{n+2}, ...)`.
-/
theorem durrett2019_example_4_7_4_condExp_first_eq_invNat_prefixAverage
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} [IsFiniteMeasure P]
    {𝒢 : ℕ -> MeasurableSpace Ω} {ξ : ℕ -> Ω -> ℝ} {n : ℕ}
    (hn : 0 < n)
    (h𝒢_le : ∀ n, 𝒢 n ≤ mΩ)
    (hξ_int : ∀ i ∈ Finset.range n, Integrable (ξ i) P)
    (hsum_meas :
      StronglyMeasurable[𝒢 n] (∑ i ∈ Finset.range n, ξ i))
    (hsym :
      ∀ i ∈ Finset.range n, P[ξ i | 𝒢 n] =ᵐ[P] P[ξ 0 | 𝒢 n]) :
    P[ξ 0 | 𝒢 n] =ᵐ[P]
      fun ω => ((n : ℝ)⁻¹) * ∑ i ∈ Finset.range n, ξ i ω := by
  classical
  have hn_ne : (n : ℝ) ≠ 0 := by exact_mod_cast hn.ne'
  have hsum_int :
      Integrable (∑ i ∈ Finset.range n, ξ i) P :=
    integrable_finsetSum' (μ := P) (Finset.range n) hξ_int
  have hcond_sum :
      P[∑ i ∈ Finset.range n, ξ i | 𝒢 n] =ᵐ[P]
        ∑ i ∈ Finset.range n, P[ξ i | 𝒢 n] :=
    condExp_finsetSum (μ := P) (s := Finset.range n)
      (f := ξ) hξ_int (𝒢 n)
  have hcond_sum_meas :
      P[∑ i ∈ Finset.range n, ξ i | 𝒢 n] =ᵐ[P]
        ∑ i ∈ Finset.range n, ξ i := by
    exact
      (condExp_of_stronglyMeasurable (μ := P) (h𝒢_le n)
        hsum_meas hsum_int).eventuallyEq
  have hsym_sum :
      (∑ i ∈ Finset.range n, P[ξ i | 𝒢 n]) =ᵐ[P]
        ∑ i ∈ Finset.range n, P[ξ 0 | 𝒢 n] :=
    eventuallyEq_sum fun i hi => hsym i hi
  have hsum_const :
      (∑ i ∈ Finset.range n, P[ξ 0 | 𝒢 n]) =
        fun ω => (n : ℝ) * P[ξ 0 | 𝒢 n] ω := by
    ext ω
    simp [Finset.sum_apply, Finset.sum_const, nsmul_eq_mul]
  have hprefix_eq_mul :
      (∑ i ∈ Finset.range n, ξ i) =ᵐ[P]
        fun ω => (n : ℝ) * P[ξ 0 | 𝒢 n] ω :=
    hcond_sum_meas.symm.trans
      (hcond_sum.trans (hsym_sum.trans (EventuallyEq.of_eq hsum_const)))
  filter_upwards [hprefix_eq_mul] with ω hω
  have hω' : (n : ℝ) * P[ξ 0 | 𝒢 n] ω =
      ∑ i ∈ Finset.range n, ξ i ω := by
    simpa [Finset.sum_apply] using hω.symm
  calc
    P[ξ 0 | 𝒢 n] ω =
        ((n : ℝ)⁻¹) * ((n : ℝ) * P[ξ 0 | 𝒢 n] ω) := by
          rw [← mul_assoc, inv_mul_cancel₀ hn_ne, one_mul]
    _ = ((n : ℝ)⁻¹) * ∑ i ∈ Finset.range n, ξ i ω := by
          rw [hω']

/--
Durrett 2019, Example 4.7.4 conditional-expectation algebra core in the
textbook division display `S_n / n`.
-/
theorem durrett2019_example_4_7_4_condExp_first_eq_prefixAverage_div
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} [IsFiniteMeasure P]
    {𝒢 : ℕ -> MeasurableSpace Ω} {ξ : ℕ -> Ω -> ℝ} {n : ℕ}
    (hn : 0 < n)
    (h𝒢_le : ∀ n, 𝒢 n ≤ mΩ)
    (hξ_int : ∀ i ∈ Finset.range n, Integrable (ξ i) P)
    (hsum_meas :
      StronglyMeasurable[𝒢 n] (∑ i ∈ Finset.range n, ξ i))
    (hsym :
      ∀ i ∈ Finset.range n, P[ξ i | 𝒢 n] =ᵐ[P] P[ξ 0 | 𝒢 n]) :
    P[ξ 0 | 𝒢 n] =ᵐ[P]
      fun ω => (∑ i ∈ Finset.range n, ξ i ω) / (n : ℝ) := by
  filter_upwards
    [durrett2019_example_4_7_4_condExp_first_eq_invNat_prefixAverage
      (P := P) (𝒢 := 𝒢) (ξ := ξ) (n := n)
      hn h𝒢_le hξ_int hsum_meas hsym] with ω hω
  simpa [div_eq_mul_inv, mul_comm] using hω

/--
Durrett 2019, Example 4.7.4 conditional-expectation calculation specialized
to the concrete reverse-average sigma-field.  After V291/V292, the only
remaining source-specific input is the finite-prefix symmetry statement
`hsym`.
-/
theorem durrett2019_example_4_7_4_condExp_first_eq_reverseAverageSigma_prefixAverage_div
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} [IsFiniteMeasure P]
    {ξ : ℕ -> Ω -> ℝ} {n : ℕ}
    (hn : 0 < n)
    (hξ_meas : ∀ i, Measurable (ξ i))
    (hξ_int : ∀ i ∈ Finset.range n, Integrable (ξ i) P)
    (hsym :
      ∀ i ∈ Finset.range n,
        P[ξ i | durrett2019_example_4_7_4_reverseAverageSigma ξ n] =ᵐ[P]
          P[ξ 0 | durrett2019_example_4_7_4_reverseAverageSigma ξ n]) :
    P[ξ 0 | durrett2019_example_4_7_4_reverseAverageSigma ξ n] =ᵐ[P]
      fun ω => (∑ i ∈ Finset.range n, ξ i ω) / (n : ℝ) := by
  refine
    durrett2019_example_4_7_4_condExp_first_eq_prefixAverage_div
      (P := P)
      (𝒢 := fun k : ℕ =>
        durrett2019_example_4_7_4_reverseAverageSigma ξ k)
      (ξ := ξ) (n := n) hn
      (fun k =>
        durrett2019_example_4_7_4_reverseAverageSigma_le
          (ξ := ξ) (n := k) hξ_meas)
      hξ_int ?_ hsym
  convert
    (durrett2019_example_4_7_4_prefixSum_stronglyMeasurable_reverseAverageSigma
      (ξ := ξ) n) using 1
  ext ω
  simp [durrett2019_example_4_7_4_prefixSum, Finset.sum_apply]

/--
Conditional-expectation symmetry from an invariant measurable equivalence.
This is the reusable handoff from a finite-exchangeability transport proof to
the `hsym` hypothesis used in Durrett Example 4.7.4.
-/
theorem durrett2019_condExp_eq_of_invariant_measurableEquiv
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} [IsFiniteMeasure P]
    {m : MeasurableSpace Ω} (hm : m ≤ mΩ)
    {f g : Ω -> ℝ}
    (hf_int : Integrable f P) (hg_int : Integrable g P)
    (T : @MeasurableEquiv Ω Ω mΩ mΩ)
    (hT_pres : @MeasurePreserving Ω Ω mΩ mΩ T P P)
    (hT_sets : ∀ s : Set Ω, MeasurableSet[m] s -> T ⁻¹' s = s)
    (hfg : f = fun ω => g (T ω)) :
    P[f | m] =ᵐ[P] P[g | m] := by
  refine
    vdVW_condExp_eq_of_forall_setIntegral_eq
      (Ω := Ω) (mΩ := mΩ) (μ := P) (m := m) hm hf_int hg_int ?_
  intro s hs
  calc
    (∫ ω in s, f ω ∂P)
        = ∫ ω in s, g (T ω) ∂P := by rw [hfg]
    _ = ∫ ω in T ⁻¹' s, g (T ω) ∂P := by rw [hT_sets s hs]
    _ = ∫ ω in s, g ω ∂(@MeasureTheory.Measure.map Ω Ω mΩ mΩ T P) := by
          exact
            (@setIntegral_map_equiv Ω ℝ mΩ _ _ P Ω mΩ T g s).symm
    _ = ∫ ω in s, g ω ∂P := by
          rw [show @MeasureTheory.Measure.map Ω Ω mΩ mΩ T P = P from
            @MeasureTheory.MeasurePreserving.map_eq Ω Ω mΩ mΩ T P P hT_pres]

/--
Durrett 2019, Example 4.7.4 source-symmetry handoff specialized to the
concrete reverse-average sigma-field.  A transformation preserving `P`, fixing
the reverse-average events, and sending coordinate `i` to coordinate `0`
identifies the corresponding conditional expectations.
-/
theorem durrett2019_example_4_7_4_condExp_eq_zero_of_reverseAverage_invariant_equiv
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} [IsFiniteMeasure P]
    {ξ : ℕ -> Ω -> ℝ} {n i : ℕ}
    (hξ_meas : ∀ k, Measurable (ξ k))
    (hi_int : Integrable (ξ i) P)
    (h0_int : Integrable (ξ 0) P)
    (T : Ω ≃ᵐ Ω)
    (hT_pres : MeasurePreserving T P P)
    (hT_sets :
      ∀ s : Set Ω,
        MeasurableSet[durrett2019_example_4_7_4_reverseAverageSigma ξ n] s ->
          T ⁻¹' s = s)
    (hcoord : (fun ω => ξ i ω) = fun ω => ξ 0 (T ω)) :
    P[ξ i | durrett2019_example_4_7_4_reverseAverageSigma ξ n] =ᵐ[P]
      P[ξ 0 | durrett2019_example_4_7_4_reverseAverageSigma ξ n] := by
  exact
    durrett2019_condExp_eq_of_invariant_measurableEquiv
      (P := P)
      (m := durrett2019_example_4_7_4_reverseAverageSigma ξ n)
      (f := ξ i) (g := ξ 0)
      (durrett2019_example_4_7_4_reverseAverageSigma_le
        (ξ := ξ) (n := n) hξ_meas)
      hi_int h0_int T hT_pres hT_sets hcoord

/--
Durrett 2019, Example 4.7.4 vectorized finite-prefix symmetry constructor.
Once each prefix coordinate has a reverse-average-preserving exchangeability
transport to coordinate `0`, this returns exactly the `hsym` input consumed by
`durrett2019_example_4_7_4_condExp_first_eq_reverseAverageSigma_prefixAverage_div`.
-/
theorem durrett2019_example_4_7_4_reverseAverageSigma_prefix_condExp_symmetry
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} [IsFiniteMeasure P]
    {ξ : ℕ -> Ω -> ℝ} {n : ℕ}
    (hξ_meas : ∀ k, Measurable (ξ k))
    (hξ_int : ∀ i ∈ Finset.range n, Integrable (ξ i) P)
    (T : ℕ -> Ω ≃ᵐ Ω)
    (hT_pres :
      ∀ i ∈ Finset.range n, MeasurePreserving (T i) P P)
    (hT_sets :
      ∀ i ∈ Finset.range n, ∀ s : Set Ω,
        MeasurableSet[durrett2019_example_4_7_4_reverseAverageSigma ξ n] s ->
          (T i) ⁻¹' s = s)
    (hcoord :
      ∀ i ∈ Finset.range n, (fun ω => ξ i ω) = fun ω => ξ 0 ((T i) ω)) :
    ∀ i ∈ Finset.range n,
      P[ξ i | durrett2019_example_4_7_4_reverseAverageSigma ξ n] =ᵐ[P]
        P[ξ 0 | durrett2019_example_4_7_4_reverseAverageSigma ξ n] := by
  intro i hi
  exact
    durrett2019_example_4_7_4_condExp_eq_zero_of_reverseAverage_invariant_equiv
      (P := P) (ξ := ξ) (n := n) (i := i)
      hξ_meas (hξ_int i hi)
      (hξ_int 0
        (Finset.mem_range.mpr
          (Nat.lt_of_le_of_lt (Nat.zero_le i) (Finset.mem_range.mp hi))))
      (T i) (hT_pres i hi) (hT_sets i hi) (hcoord i hi)

/--
Durrett 2019, Example 4.7.4 finite-prefix symmetry from source-shaped
transport invariants.  After V294, the remaining exchangeability task is to
construct the measurable equivalences `T i`; preservation of the concrete
reverse-average sigma-field is discharged by prefix-sum and tail-coordinate
invariance.
-/
theorem durrett2019_example_4_7_4_reverseAverageSigma_prefix_condExp_symmetry_of_prefixSum_tail_invariant
    {Ω : Type*} [mΩ : MeasurableSpace Ω]
    {P : Measure Ω} [IsFiniteMeasure P]
    {ξ : ℕ -> Ω -> ℝ} {n : ℕ}
    (hξ_meas : ∀ k, Measurable (ξ k))
    (hξ_int : ∀ i ∈ Finset.range n, Integrable (ξ i) P)
    (T : ℕ -> Ω ≃ᵐ Ω)
    (hT_pres :
      ∀ i ∈ Finset.range n, MeasurePreserving (T i) P P)
    (hprefix :
      ∀ i ∈ Finset.range n,
        (fun ω => durrett2019_example_4_7_4_prefixSum ξ n ((T i) ω)) =
          durrett2019_example_4_7_4_prefixSum ξ n)
    (htail :
      ∀ i ∈ Finset.range n, ∀ j : ℕ, n ≤ j ->
        (fun ω => ξ j ((T i) ω)) = ξ j)
    (hcoord :
      ∀ i ∈ Finset.range n, (fun ω => ξ i ω) = fun ω => ξ 0 ((T i) ω)) :
    ∀ i ∈ Finset.range n,
      P[ξ i | durrett2019_example_4_7_4_reverseAverageSigma ξ n] =ᵐ[P]
        P[ξ 0 | durrett2019_example_4_7_4_reverseAverageSigma ξ n] := by
  exact
    durrett2019_example_4_7_4_reverseAverageSigma_prefix_condExp_symmetry
      (P := P) (ξ := ξ) (n := n)
      hξ_meas hξ_int T hT_pres
      (fun i hi =>
        durrett2019_example_4_7_4_preimage_reverseAverageSigma_eq_of_prefixSum_tail_invariant
          (ξ := ξ) (n := n) (T i) (hprefix i hi) (htail i hi))
      hcoord

/--
Durrett 2019, Example 4.7.4 product-space source algebra: finite coordinate
permutations preserve the prefix sum of the coordinate-evaluation process.
-/
theorem durrett2019_example_4_7_4_eval_prefixSum_comp_natPermOfFin
    {n : ℕ} (perm : Equiv.Perm (Fin n)) :
    (fun sequence : ℕ -> ℝ =>
      durrett2019_example_4_7_4_prefixSum (fun k sequence => sequence k) n
        (vdVWNatCoordinatePermMeasurableEquiv (Observation := ℝ)
          (vdVWNatPermOfFin perm) sequence)) =
      durrett2019_example_4_7_4_prefixSum
        (fun k sequence => sequence k) n := by
  ext sequence
  rw [vdVWNatCoordinatePermMeasurableEquiv_eq_vdVWPermuteNatSequence]
  dsimp [durrett2019_example_4_7_4_prefixSum]
  rw [← Fin.sum_univ_eq_sum_range
    (fun k => vdVWPermuteNatSequence (vdVWNatPermOfFin perm) sequence k) n]
  rw [← Fin.sum_univ_eq_sum_range (fun k => sequence k) n]
  have hfirst :=
    vdVWFirstNSample_permuteNatSequence_natPermOfFin
      (Observation := ℝ) perm sequence
  change
    (∑ i : Fin n,
        vdVWFirstNSample n
          (vdVWPermuteNatSequence (vdVWNatPermOfFin perm) sequence) i) =
      ∑ i : Fin n, vdVWFirstNSample n sequence i
  rw [hfirst]
  let g : Fin n -> ℝ := fun i => vdVWFirstNSample n sequence i
  calc
    (∑ i : Fin n,
        vdVWFinCoordinatePermMeasurableEquiv perm
          (vdVWFirstNSample n sequence) i)
        = ∑ i : Fin n, g (perm.symm i) := by
            apply Finset.sum_congr rfl
            intro i _hi
            have hcoord :=
              vdVWFinCoordinatePermMeasurableEquiv_apply_apply
                (Observation := ℝ) perm
                (vdVWFirstNSample n sequence) (perm.symm i)
            simpa [g] using hcoord
    _ = ∑ i : Fin n, g i := by
          simpa using Equiv.sum_comp perm.symm g

/--
Durrett 2019, Example 4.7.4 product-space source algebra: every coordinate
permutation fixing coordinates from `n` onward preserves the first-`n` prefix
sum.
-/
theorem durrett2019_example_4_7_4_eval_prefixSum_comp_tailFixingPerm
    {n : ℕ} (perm : Equiv.Perm ℕ) (hfix : VdVWNatPermFixesFrom n perm) :
    (fun sequence : ℕ -> ℝ =>
      durrett2019_example_4_7_4_prefixSum (fun k sequence => sequence k) n
        (vdVWPermuteNatSequence (Observation := ℝ) perm sequence)) =
      durrett2019_example_4_7_4_prefixSum
        (fun k sequence => sequence k) n := by
  ext sequence
  dsimp [durrett2019_example_4_7_4_prefixSum]
  rw [← Fin.sum_univ_eq_sum_range
    (fun k => vdVWPermuteNatSequence (Observation := ℝ) perm sequence k) n]
  rw [← Fin.sum_univ_eq_sum_range (fun k => sequence k) n]
  have hfirst :=
    vdVWFirstNSample_permuteNatSequence
      (Observation := ℝ) perm hfix sequence
  change
    (∑ i : Fin n,
        vdVWFirstNSample n
          (vdVWPermuteNatSequence (Observation := ℝ) perm sequence) i) =
      ∑ i : Fin n, vdVWFirstNSample n sequence i
  rw [hfirst]
  let restricted : Equiv.Perm (Fin n) := vdVWNatPermRestrictFin perm hfix
  let g : Fin n -> ℝ := fun i => vdVWFirstNSample n sequence i
  calc
    (∑ i : Fin n,
        vdVWFinCoordinatePermMeasurableEquiv restricted
          (vdVWFirstNSample n sequence) i)
        = ∑ i : Fin n, g (restricted.symm i) := by
            apply Finset.sum_congr rfl
            intro i _hi
            have hcoord :=
              vdVWFinCoordinatePermMeasurableEquiv_apply_apply
                (Observation := ℝ) restricted
                (vdVWFirstNSample n sequence) (restricted.symm i)
            simpa [g] using hcoord
    _ = ∑ i : Fin n, g i := by
          simpa using Equiv.sum_comp restricted.symm g

/--
Durrett 2019, Example 4.7.4 product-space source algebra: finite coordinate
permutations extended by identity outside the first `n` fix every tail
coordinate from `n` onward.
-/
theorem durrett2019_example_4_7_4_eval_tail_comp_natPermOfFin
    {n j : ℕ} (hj : n ≤ j) (perm : Equiv.Perm (Fin n)) :
    (fun sequence : ℕ -> ℝ =>
      (vdVWNatCoordinatePermMeasurableEquiv (Observation := ℝ)
        (vdVWNatPermOfFin perm) sequence) j) =
      fun sequence => sequence j := by
  ext sequence
  rw [vdVWNatCoordinatePermMeasurableEquiv_eq_vdVWPermuteNatSequence]
  dsimp [vdVWPermuteNatSequence]
  have hfix := VdVWNatPermFixesFrom_natPermOfFin perm
  have hsymm : (vdVWNatPermOfFin perm).symm j = j := by
    apply (vdVWNatPermOfFin perm).injective
    rw [Equiv.apply_symm_apply]
    exact (hfix j hj).symm
  rw [hsymm]

/--
Durrett 2019, Example 4.7.4 product-space source algebra: every coordinate
permutation fixing coordinates from `n` onward fixes every tail coordinate
from `n` onward.
-/
theorem durrett2019_example_4_7_4_eval_tail_comp_tailFixingPerm
    {n j : ℕ} (hj : n ≤ j)
    (perm : Equiv.Perm ℕ) (hfix : VdVWNatPermFixesFrom n perm) :
    (fun sequence : ℕ -> ℝ =>
      vdVWPermuteNatSequence (Observation := ℝ) perm sequence j) =
      fun sequence => sequence j := by
  ext sequence
  dsimp [vdVWPermuteNatSequence]
  have hsymm : perm.symm j = j := by
    apply perm.injective
    rw [Equiv.apply_symm_apply]
    exact (hfix j hj).symm
  rw [hsymm]

/--
Durrett 2019, Example 4.7.4 product-space permutation-symmetry source:
the first-`n` prefix sum is symmetric under every permutation fixing the tail
from `n` onward.
-/
theorem durrett2019_example_4_7_4_eval_prefixSum_permutationSymmetricFrom
    (n : ℕ) :
    VdVWPermutationSymmetricFrom n
      (durrett2019_example_4_7_4_prefixSum
        (fun k (sequence : ℕ -> ℝ) => sequence k) n) := by
  intro perm hfix sequence
  exact congrFun
    (durrett2019_example_4_7_4_eval_prefixSum_comp_tailFixingPerm
      (n := n) perm hfix) sequence

/--
Durrett 2019, Example 4.7.4 product-space permutation-symmetry source:
tail coordinates are symmetric under every permutation fixing the tail from
`n` onward.
-/
theorem durrett2019_example_4_7_4_eval_tailCoordinate_permutationSymmetricFrom
    {n i : ℕ} (hi : n ≤ i) :
    VdVWPermutationSymmetricFrom n (fun sequence : ℕ -> ℝ => sequence i) := by
  intro perm hfix sequence
  exact congrFun
    (durrett2019_example_4_7_4_eval_tail_comp_tailFixingPerm
      (n := n) (j := i) hi perm hfix) sequence

/--
Durrett 2019, Example 4.7.4 product-space permutation-symmetric
measurability of the first-`n` prefix sum.
-/
theorem durrett2019_example_4_7_4_eval_prefixSum_measurable_permutationSymmetric
    (n : ℕ) :
    Measurable[vdVWPermutationSymmetricMeasurableSpace ℝ n]
      (durrett2019_example_4_7_4_prefixSum
        (fun k (sequence : ℕ -> ℝ) => sequence k) n) := by
  refine measurable_vdVWPermutationSymmetricMeasurableSpace_of_symmetric ?_ ?_
  · dsimp [durrett2019_example_4_7_4_prefixSum]
    exact Finset.measurable_fun_sum (Finset.range n) fun i _hi =>
      measurable_pi_apply i
  · exact durrett2019_example_4_7_4_eval_prefixSum_permutationSymmetricFrom n

/--
Durrett 2019, Example 4.7.4 product-space permutation-symmetric
measurability of every tail coordinate.
-/
theorem durrett2019_example_4_7_4_eval_tailCoordinate_measurable_permutationSymmetric
    {n i : ℕ} (hi : n ≤ i) :
    Measurable[vdVWPermutationSymmetricMeasurableSpace ℝ n]
      (fun sequence : ℕ -> ℝ => sequence i) := by
  refine measurable_vdVWPermutationSymmetricMeasurableSpace_of_symmetric ?_ ?_
  · exact measurable_pi_apply i
  · exact durrett2019_example_4_7_4_eval_tailCoordinate_permutationSymmetricFrom hi

/--
Durrett 2019, Example 4.7.4 product-space bridge: Durrett's concrete
reverse-average sigma-field is contained in the VdV&W permutation-symmetric
sigma-field with the same cutoff.
-/
theorem durrett2019_example_4_7_4_eval_reverseAverageSigma_le_permutationSymmetric
    (n : ℕ) :
    durrett2019_example_4_7_4_reverseAverageSigma
        (fun k (sequence : ℕ -> ℝ) => sequence k) n ≤
      vdVWPermutationSymmetricMeasurableSpace ℝ n := by
  dsimp [durrett2019_example_4_7_4_reverseAverageSigma]
  refine sup_le ?_ ?_
  · exact
      (durrett2019_example_4_7_4_eval_prefixSum_measurable_permutationSymmetric
        n).comap_le
  · refine iSup_le fun i => iSup_le fun hi => ?_
    exact
      (durrett2019_example_4_7_4_eval_tailCoordinate_measurable_permutationSymmetric
        (n := n) (i := i) hi).comap_le

/--
Durrett 2019, Example 4.7.4 product-space bridge: the reverse-average tail is
contained in the VdV&W permutation-symmetric tail.
-/
theorem durrett2019_example_4_7_4_eval_reverseAverageTail_le_permutationSymmetricTail :
    (⨅ n : ℕ,
        durrett2019_example_4_7_4_reverseAverageSigma
          (fun k (sequence : ℕ -> ℝ) => sequence k) n) ≤
      ⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n := by
  exact iInf_mono fun n =>
    durrett2019_example_4_7_4_eval_reverseAverageSigma_le_permutationSymmetric n

/--
Durrett 2019, Example 4.7.4 product-space zero-one transport.  Once the VdVW
permutation-symmetric tail is zero-one, the reverse-average tail is zero-one
by V298's sigma-field containment.
-/
theorem durrett2019_example_4_7_4_eval_reverseAverage_tail_zero_or_one_of_permutationSymmetric_tail
    {P : Measure ℝ} [IsProbabilityMeasure P]
    (hzeroOne :
      ∀ B : Set (ℕ -> ℝ),
        MeasurableSet[⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n] B ->
          vdVWInfiniteProductMeasure P B = 0 ∨ vdVWInfiniteProductMeasure P B = 1) :
    ∀ B : Set (ℕ -> ℝ),
      MeasurableSet[
        ⨅ n : ℕ,
          durrett2019_example_4_7_4_reverseAverageSigma
            (fun k (sequence : ℕ -> ℝ) => sequence k) n] B ->
        vdVWInfiniteProductMeasure P B = 0 ∨ vdVWInfiniteProductMeasure P B = 1 := by
  intro B hB
  exact hzeroOne B
    (durrett2019_example_4_7_4_eval_reverseAverageTail_le_permutationSymmetricTail
      B hB)

/--
Durrett 2019, Example 4.7.4 / Hewitt-Savage route support.  Events in the
VdVW permutation-symmetric tail are invariant under every finite-prefix
coordinate permutation of the iid real product space.
-/
theorem durrett2019_example_4_7_4_eval_permutationSymmetricTail_preimage_natPermOfFin_eq
    {n : ℕ} (perm : Equiv.Perm (Fin n)) {A : Set (ℕ -> ℝ)}
    (hA :
      MeasurableSet[⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n] A) :
    vdVWPermuteNatSequence (Observation := ℝ) (vdVWNatPermOfFin perm) ⁻¹' A = A := by
  exact
    StatInference.preimage_vdVWPermuteNatSequence_natPermOfFin_eq_of_measurableSet_permutationSymmetricTail
      (Observation := ℝ) perm hA

/--
Durrett 2019, Example 4.7.4 / Hewitt-Savage route support.  Set integrals over
events in the VdVW permutation-symmetric tail are invariant under finite-prefix
coordinate permutations.
-/
theorem durrett2019_example_4_7_4_eval_permutationSymmetricTail_setIntegral_natPermOfFin_eq
    {P : Measure ℝ} [IsProbabilityMeasure P] {n : ℕ}
    (perm : Equiv.Perm (Fin n)) {A : Set (ℕ -> ℝ)}
    (hA :
      MeasurableSet[⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n] A)
    (f : (ℕ -> ℝ) -> ℝ) :
    (∫ sequence in A,
        f (vdVWPermuteNatSequence (Observation := ℝ) (vdVWNatPermOfFin perm) sequence)
          ∂(vdVWInfiniteProductMeasure P)) =
      ∫ sequence in A, f sequence ∂(vdVWInfiniteProductMeasure P) := by
  exact
    StatInference.setIntegral_vdVWInfiniteProductMeasure_comp_permuteNatSequence_of_measurableSet_permutationSymmetricTail
      (Observation := ℝ) P (vdVWNatPermOfFin perm)
      (VdVWNatPermFixesFrom_natPermOfFin perm) hA f

/--
Durrett 2019, Example 4.7.4 / Hewitt-Savage route support.  Once the
VdVW permutation-symmetric tail is independent of itself under the iid real
product law, every event in that tail has probability zero or one.
-/
theorem durrett2019_example_4_7_4_eval_permutationSymmetricTail_zero_or_one_of_indep_self
    {P : Measure ℝ} [IsProbabilityMeasure P]
    (hindep :
      Indep
        (⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n)
        (⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n)
        (vdVWInfiniteProductMeasure P)) :
    ∀ B : Set (ℕ -> ℝ),
      MeasurableSet[⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n] B ->
        vdVWInfiniteProductMeasure P B = 0 ∨ vdVWInfiniteProductMeasure P B = 1 := by
  exact
    StatInference.vdVWPermutationSymmetricTail_measure_zero_or_one_all_of_indep_self
      (Observation := ℝ) P hindep

/--
Durrett 2019, Example 4.7.4 / Hewitt-Savage route support.  Self-independence
of the VdVW permutation-symmetric tail transports zero-one triviality to
Durrett's concrete reverse-average tail.
-/
theorem durrett2019_example_4_7_4_eval_reverseAverage_tail_zero_or_one_of_permutationSymmetric_tail_indep_self
    {P : Measure ℝ} [IsProbabilityMeasure P]
    (hindep :
      Indep
        (⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n)
        (⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n)
        (vdVWInfiniteProductMeasure P)) :
    ∀ B : Set (ℕ -> ℝ),
      MeasurableSet[
        ⨅ n : ℕ,
          durrett2019_example_4_7_4_reverseAverageSigma
            (fun k (sequence : ℕ -> ℝ) => sequence k) n] B ->
        vdVWInfiniteProductMeasure P B = 0 ∨ vdVWInfiniteProductMeasure P B = 1 := by
  exact
    durrett2019_example_4_7_4_eval_reverseAverage_tail_zero_or_one_of_permutationSymmetric_tail
      (P := P)
      (durrett2019_example_4_7_4_eval_permutationSymmetricTail_zero_or_one_of_indep_self
        (P := P) hindep)

/--
Durrett 2019, Example 4.7.4 / Hewitt-Savage route support.  In the iid real
product space, the finite prefix filtration is independent of the ordinary
future-coordinate tail sigma-field.
-/
theorem durrett2019_example_4_7_4_eval_prefixFiltration_indep_tailCoordinateSigma
    {P : Measure ℝ} [IsProbabilityMeasure P] (n : ℕ) :
    Indep
      (durrett2019_theorem_4_3_8_prefixFiltration ℝ n)
      (durrett2019_theorem_4_3_8_tailCoordinateSigma ℝ n)
      (vdVWInfiniteProductMeasure P) := by
  let mAmbient : MeasurableSpace (ℕ -> ℝ) := inferInstance
  let prefixSigma : MeasurableSpace (ℕ -> ℝ) :=
    ⨆ i : ℕ, ⨆ _ : i < n, durrett2019_theorem_4_3_8_coordinateSigma ℝ i
  have hprefix_le :
      durrett2019_theorem_4_3_8_prefixFiltration ℝ n ≤ prefixSigma := by
    have hrestrict :
        Measurable[prefixSigma]
          ((Finset.range n).restrict : (ℕ -> ℝ) -> ↥(Finset.range n) -> ℝ) := by
      rw [measurable_pi_iff]
      intro i
      have hi : (i : ℕ) < n := Finset.mem_range.mp i.property
      have hcoord :
          Measurable[durrett2019_theorem_4_3_8_coordinateSigma ℝ (i : ℕ)]
            (fun sequence : ℕ -> ℝ => sequence (i : ℕ)) :=
        comap_measurable (fun sequence : ℕ -> ℝ => sequence (i : ℕ))
      exact Measurable.iSup' (i : ℕ) (Measurable.iSup' hi hcoord)
    simpa [durrett2019_theorem_4_3_8_prefixFiltration, prefixSigma] using
      hrestrict.comap_le
  have hindep_prefix_tail :
      @_root_.ProbabilityTheory.Indep (ℕ -> ℝ)
        prefixSigma
        (durrett2019_theorem_4_3_8_tailCoordinateSigma ℝ n)
        mAmbient
        (vdVWInfiniteProductMeasure P) := by
    let prefixSet : Set ℕ := {i | i < n}
    let tailSet : Set ℕ := {i | i ≥ n}
    have hdisjoint : Disjoint prefixSet tailSet := by
      rw [Set.disjoint_left]
      intro i hi htail
      have htail' : n ≤ i := by
        simpa [tailSet] using htail
      exact (not_le_of_gt hi) htail'
    have hcoord_le :
        ∀ i, durrett2019_theorem_4_3_8_coordinateSigma ℝ i ≤
          mAmbient := by
      intro i
      simpa [mAmbient] using
        (durrett2019_theorem_4_3_8_coordinateSigma_le (S := ℝ) i)
    have hindep :
        _root_.ProbabilityTheory.iIndep
          (fun i => durrett2019_theorem_4_3_8_coordinateSigma ℝ i)
          (Measure.infinitePi fun _ : ℕ => P) :=
      durrett2019_theorem_4_3_8_coordinateSigma_iIndep_infinitePi
    simpa [vdVWInfiniteProductMeasure, durrett2019_theorem_4_3_8_tailCoordinateSigma,
      prefixSigma, prefixSet, tailSet] using
      (_root_.ProbabilityTheory.indep_iSup_of_disjoint
        (_mΩ := mAmbient)
        (m := fun i => durrett2019_theorem_4_3_8_coordinateSigma ℝ i)
        hcoord_le hindep hdisjoint)
  exact
    _root_.ProbabilityTheory.indep_of_indep_of_le_left
      hindep_prefix_tail hprefix_le

/--
Durrett 2019, Example 4.7.4 / Hewitt-Savage route support.  If a coordinate
permutation moves the first `n` coordinates into the future block starting at
`m`, then the pulled-back prefix filtration is measurable from the future
coordinate tail.
-/
theorem durrett2019_example_4_7_4_permuteNatSequence_prefixFiltration_tailCoordinateSigma_measurable
    {S : Type*} [MeasurableSpace S] {n m : ℕ} (perm : Equiv.Perm ℕ)
    (hmove : ∀ i : ℕ, i < n -> m ≤ perm.symm i) :
    Measurable[durrett2019_theorem_4_3_8_tailCoordinateSigma S m,
      durrett2019_theorem_4_3_8_prefixFiltration S n]
      (vdVWPermuteNatSequence (Observation := S) perm) := by
  let I : Finset ℕ := Finset.range n
  have hrestrict :
      @Measurable (ℕ -> S) (I -> S)
        (durrett2019_theorem_4_3_8_tailCoordinateSigma S m) inferInstance
        (fun sequence : ℕ -> S =>
          (I.restrict : (ℕ -> S) -> I -> S)
            (vdVWPermuteNatSequence (Observation := S) perm sequence)) := by
    refine
      (@measurable_pi_iff (ℕ -> S) I (fun _ : I => S)
        (durrett2019_theorem_4_3_8_tailCoordinateSigma S m)
        (fun _ : I => inferInstance)
        (g := fun sequence : ℕ -> S =>
          (I.restrict : (ℕ -> S) -> I -> S)
            (vdVWPermuteNatSequence (Observation := S) perm sequence))).mpr ?_
    intro i
    have hi : (i : ℕ) < n := Finset.mem_range.mp i.property
    have hcoord :
        Measurable[durrett2019_theorem_4_3_8_tailCoordinateSigma S m]
          (fun sequence : ℕ -> S => sequence (perm.symm (i : ℕ))) :=
      durrett2019_theorem_4_3_8_coordinate_tailCoordinateSigma_measurable
        (S := S) (n := m) (i := perm.symm (i : ℕ)) (hmove (i : ℕ) hi)
    simpa [I, vdVWPermuteNatSequence] using hcoord
  change Measurable[durrett2019_theorem_4_3_8_tailCoordinateSigma S m,
    MeasurableSpace.pi.comap (I.restrict : (ℕ -> S) -> I -> S)]
    (vdVWPermuteNatSequence (Observation := S) perm)
  intro C hC
  rcases (MeasurableSpace.measurableSet_comap.mp hC) with ⟨B, hB, hBC⟩
  rw [← hBC]
  exact hrestrict hB

/--
Set form of the previous lemma: a moved finite-prefix event is measurable in
the future-coordinate tail.
-/
theorem durrett2019_example_4_7_4_preimage_permuteNatSequence_prefixFiltration_tailCoordinateSigma
    {S : Type*} [MeasurableSpace S] {n m : ℕ} (perm : Equiv.Perm ℕ)
    (hmove : ∀ i : ℕ, i < n -> m ≤ perm.symm i)
    {C : Set (ℕ -> S)}
    (hC : MeasurableSet[durrett2019_theorem_4_3_8_prefixFiltration S n] C) :
    MeasurableSet[durrett2019_theorem_4_3_8_tailCoordinateSigma S m]
      (vdVWPermuteNatSequence (Observation := S) perm ⁻¹' C) :=
  (durrett2019_example_4_7_4_permuteNatSequence_prefixFiltration_tailCoordinateSigma_measurable
    (S := S) (n := n) (m := m) perm hmove) hC

/--
Durrett 2019, Example 4.7.4 / Hewitt-Savage route support.  A prefix event is
independent of a second prefix event after that second event is transported
into the future coordinate tail.
-/
theorem durrett2019_example_4_7_4_eval_prefixFiltration_indep_permuted_prefix
    {P : Measure ℝ} [IsProbabilityMeasure P] {n m : ℕ} (hnm : n ≤ m)
    (perm : Equiv.Perm ℕ)
    (hmove : ∀ i : ℕ, i < n -> m ≤ perm.symm i)
    {C D : Set (ℕ -> ℝ)}
    (hC : MeasurableSet[durrett2019_theorem_4_3_8_prefixFiltration ℝ n] C)
    (hD : MeasurableSet[durrett2019_theorem_4_3_8_prefixFiltration ℝ n] D) :
    IndepSet C (vdVWPermuteNatSequence (Observation := ℝ) perm ⁻¹' D)
      (vdVWInfiniteProductMeasure P) := by
  have hC_m :
      MeasurableSet[durrett2019_theorem_4_3_8_prefixFiltration ℝ m] C :=
    (durrett2019_theorem_4_3_8_prefixFiltration ℝ).mono hnm C hC
  have hD_tail :
      MeasurableSet[durrett2019_theorem_4_3_8_tailCoordinateSigma ℝ m]
        (vdVWPermuteNatSequence (Observation := ℝ) perm ⁻¹' D) :=
    durrett2019_example_4_7_4_preimage_permuteNatSequence_prefixFiltration_tailCoordinateSigma
      (S := ℝ) (n := n) (m := m) perm hmove hD
  exact
    (durrett2019_example_4_7_4_eval_prefixFiltration_indep_tailCoordinateSigma
      (P := P) m).indepSet_of_measurableSet hC_m hD_tail

/--
Measure form of the transported-prefix independence lemma.  The right-hand
factor is stated before transport, using invariance of the iid product law
under coordinate permutations.
-/
theorem durrett2019_example_4_7_4_eval_prefix_inter_permuted_prefix_measure_eq_mul
    {P : Measure ℝ} [IsProbabilityMeasure P] {n m : ℕ} (hnm : n ≤ m)
    (perm : Equiv.Perm ℕ)
    (hmove : ∀ i : ℕ, i < n -> m ≤ perm.symm i)
    {C D : Set (ℕ -> ℝ)}
    (hC : MeasurableSet[durrett2019_theorem_4_3_8_prefixFiltration ℝ n] C)
    (hD : MeasurableSet[durrett2019_theorem_4_3_8_prefixFiltration ℝ n] D) :
    vdVWInfiniteProductMeasure P
        (C ∩ (vdVWPermuteNatSequence (Observation := ℝ) perm ⁻¹' D)) =
      vdVWInfiniteProductMeasure P C * vdVWInfiniteProductMeasure P D := by
  let T : (ℕ -> ℝ) -> (ℕ -> ℝ) :=
    vdVWPermuteNatSequence (Observation := ℝ) perm
  let μ : Measure (ℕ -> ℝ) := vdVWInfiniteProductMeasure P
  have hD_ambient : MeasurableSet D :=
    (durrett2019_theorem_4_3_8_prefixFiltration ℝ).le n D hD
  have hmp : MeasurePreserving T μ μ := by
    simpa [T, μ] using
      (vdVWInfiniteProductMeasure_measurePreserving_permuteNatSequence
        (Observation := ℝ) P perm)
  have hD_measure :
      μ (T ⁻¹' D) = μ D := by
    have hmap_apply : Measure.map T μ D = μ (T ⁻¹' D) :=
      Measure.map_apply hmp.measurable hD_ambient
    calc
      μ (T ⁻¹' D) = Measure.map T μ D := hmap_apply.symm
      _ = μ D := by rw [hmp.map_eq]
  have hindep :
      IndepSet C (T ⁻¹' D) μ := by
    simpa [T, μ] using
      (durrett2019_example_4_7_4_eval_prefixFiltration_indep_permuted_prefix
        (P := P) (n := n) (m := m) hnm perm hmove hC hD)
  calc
    μ (C ∩ (T ⁻¹' D)) = μ C * μ (T ⁻¹' D) :=
      hindep.measure_inter_eq_mul
    _ = μ C * μ D := by rw [hD_measure]

/--
Durrett 2019, Example 4.7.4 / Hewitt-Savage route support.  Intersections of a
permutation-symmetric-tail event with a prefix event are unchanged when the
prefix event is pulled back by any finite-tail-fixing coordinate permutation.
-/
theorem durrett2019_example_4_7_4_eval_permutationSymmetricTail_inter_prefix_eq_inter_permuted_prefix
    {P : Measure ℝ} [IsProbabilityMeasure P] {n N : ℕ}
    (perm : Equiv.Perm ℕ) (hfix : VdVWNatPermFixesFrom N perm)
    {A C : Set (ℕ -> ℝ)}
    (hA :
      MeasurableSet[⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n] A)
    (hC : MeasurableSet[durrett2019_theorem_4_3_8_prefixFiltration ℝ n] C) :
    vdVWInfiniteProductMeasure P (A ∩ C) =
      vdVWInfiniteProductMeasure P
        (A ∩ (vdVWPermuteNatSequence (Observation := ℝ) perm ⁻¹' C)) := by
  let T : (ℕ -> ℝ) -> (ℕ -> ℝ) :=
    vdVWPermuteNatSequence (Observation := ℝ) perm
  let μ : Measure (ℕ -> ℝ) := vdVWInfiniteProductMeasure P
  have htail_le :
      (⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n) ≤
        (inferInstance : MeasurableSpace (ℕ -> ℝ)) := by
    refine (iInf_le (fun n : ℕ => vdVWPermutationSymmetricMeasurableSpace ℝ n) 0).trans ?_
    refine MeasurableSpace.generateFrom_le ?_
    intro s hs
    rcases hs with ⟨statistic, hmeas, _hsymm, target, htarget, rfl⟩
    exact hmeas htarget
  have hA_ambient : MeasurableSet A :=
    htail_le A hA
  have hC_ambient : MeasurableSet C :=
    (durrett2019_theorem_4_3_8_prefixFiltration ℝ).le n C hC
  have hE : MeasurableSet (A ∩ C) := hA_ambient.inter hC_ambient
  have hmp : MeasurePreserving T μ μ := by
    simpa [T, μ] using
      (vdVWInfiniteProductMeasure_measurePreserving_permuteNatSequence
        (Observation := ℝ) P perm)
  have hpre_A : T ⁻¹' A = A := by
    simpa [T] using
      (StatInference.preimage_vdVWPermuteNatSequence_eq_of_measurableSet_permutationSymmetricTail
        (Observation := ℝ) hA perm hfix)
  calc
    μ (A ∩ C) = Measure.map T μ (A ∩ C) := by
      rw [hmp.map_eq]
    _ = μ (T ⁻¹' (A ∩ C)) := by
      rw [Measure.map_apply hmp.measurable hE]
    _ = μ ((T ⁻¹' A) ∩ (T ⁻¹' C)) := by
      rfl
    _ = μ (A ∩ (T ⁻¹' C)) := by
      rw [hpre_A]

/--
Durrett 2019, Example 4.7.4 / Hewitt-Savage route support.  If a tail event
has prefix approximants whose intersections with a transported prefix event
converge to the target intersection, then V303's transported-prefix
independence gives the product formula for that target intersection.

This isolates the limit algebra from the remaining measurable-approximation
argument.
-/
theorem durrett2019_example_4_7_4_eval_tail_prefix_product_of_permuted_prefix_limit
    {P : Measure ℝ} [IsProbabilityMeasure P]
    {A D : Set (ℕ -> ℝ)}
    (C : ℕ -> Set (ℕ -> ℝ)) (cutoff future : ℕ -> ℕ)
    (perm : ℕ -> Equiv.Perm ℕ)
    (hfuture : ∀ k, cutoff k ≤ future k)
    (hmove : ∀ k i : ℕ, i < cutoff k -> future k ≤ (perm k).symm i)
    (hC :
      ∀ k, MeasurableSet[durrett2019_theorem_4_3_8_prefixFiltration ℝ (cutoff k)] (C k))
    (hD :
      ∀ k, MeasurableSet[durrett2019_theorem_4_3_8_prefixFiltration ℝ (cutoff k)] D)
    (hinter :
      Tendsto
        (fun k =>
          vdVWInfiniteProductMeasure P
            (C k ∩ (vdVWPermuteNatSequence (Observation := ℝ) (perm k) ⁻¹' D)))
        atTop (𝓝 (vdVWInfiniteProductMeasure P (A ∩ D))))
    (hmeasure :
      Tendsto (fun k => vdVWInfiniteProductMeasure P (C k)) atTop
        (𝓝 (vdVWInfiniteProductMeasure P A))) :
    vdVWInfiniteProductMeasure P (A ∩ D) =
      vdVWInfiniteProductMeasure P A * vdVWInfiniteProductMeasure P D := by
  let μ : Measure (ℕ -> ℝ) := vdVWInfiniteProductMeasure P
  have hproduct_tendsto :
      Tendsto
        (fun k =>
          μ (C k ∩ (vdVWPermuteNatSequence (Observation := ℝ) (perm k) ⁻¹' D)))
        atTop (𝓝 (μ A * μ D)) := by
    have hseq_eq :
        (fun k =>
          μ (C k ∩ (vdVWPermuteNatSequence (Observation := ℝ) (perm k) ⁻¹' D))) =
          fun k => μ (C k) * μ D := by
      funext k
      simpa [μ] using
        (durrett2019_example_4_7_4_eval_prefix_inter_permuted_prefix_measure_eq_mul
          (P := P) (n := cutoff k) (m := future k) (hfuture k) (perm k)
          (hmove k) (hC k) (hD k))
    rw [hseq_eq]
    exact
      ENNReal.Tendsto.mul_const (by simpa [μ] using hmeasure)
        (Or.inr (measure_ne_top μ D))
  exact tendsto_nhds_unique (by simpa [μ] using hinter) hproduct_tendsto

/--
Durrett 2019, Example 4.7.4 / Hewitt-Savage approximation support.  The
finite-prefix event family consists of all events measurable with respect to
some finite prefix filtration.
-/
def durrett2019_example_4_7_4_finitePrefixEventSet
    (S : Type*) [MeasurableSpace S] : Set (Set (ℕ -> S)) :=
  {A | ∃ n : ℕ, MeasurableSet[durrett2019_theorem_4_3_8_prefixFiltration S n] A}

/-- The finite-prefix event family contains `∅`. -/
theorem durrett2019_example_4_7_4_finitePrefixEventSet_empty_mem
    (S : Type*) [MeasurableSpace S] :
    (∅ : Set (ℕ -> S)) ∈
      durrett2019_example_4_7_4_finitePrefixEventSet S :=
  ⟨0, by
    exact
      (@MeasurableSet.empty (ℕ -> S)
        ((durrett2019_theorem_4_3_8_prefixFiltration S) 0))⟩

/-- The finite-prefix event family contains the whole space. -/
theorem durrett2019_example_4_7_4_finitePrefixEventSet_univ_mem
    (S : Type*) [MeasurableSpace S] :
    (Set.univ : Set (ℕ -> S)) ∈
      durrett2019_example_4_7_4_finitePrefixEventSet S :=
  ⟨0, by
    exact
      (@MeasurableSet.univ (ℕ -> S)
        ((durrett2019_theorem_4_3_8_prefixFiltration S) 0))⟩

/--
Every finite-prefix event is ambiently measurable in the product
sigma-field.
-/
theorem durrett2019_example_4_7_4_finitePrefixEventSet_measurableSet
    {S : Type*} [MeasurableSpace S] {A : Set (ℕ -> S)}
    (hA : A ∈ durrett2019_example_4_7_4_finitePrefixEventSet S) :
    MeasurableSet A := by
  rcases hA with ⟨n, hA⟩
  exact (durrett2019_theorem_4_3_8_prefixFiltration S).le n A hA

/--
The finite-prefix event family is a ring of sets.  This packages the closure
properties needed by Mathlib's measured-set density theorem.
-/
theorem durrett2019_example_4_7_4_finitePrefixEventSet_isSetRing
    (S : Type*) [MeasurableSpace S] :
    IsSetRing (durrett2019_example_4_7_4_finitePrefixEventSet S) where
  empty_mem := durrett2019_example_4_7_4_finitePrefixEventSet_empty_mem S
  union_mem := by
    rintro A B ⟨n, hA⟩ ⟨m, hB⟩
    refine ⟨max n m, ?_⟩
    exact
      ((durrett2019_theorem_4_3_8_prefixFiltration S).mono
          (le_max_left n m) A hA).union
        ((durrett2019_theorem_4_3_8_prefixFiltration S).mono
          (le_max_right n m) B hB)
  diff_mem := by
    rintro A B ⟨n, hA⟩ ⟨m, hB⟩
    refine ⟨max n m, ?_⟩
    exact
      ((durrett2019_theorem_4_3_8_prefixFiltration S).mono
          (le_max_left n m) A hA).diff
        ((durrett2019_theorem_4_3_8_prefixFiltration S).mono
          (le_max_right n m) B hB)

/--
The finite-prefix event family satisfies the coverage side condition in
Mathlib's measured-set density theorem: the singleton cover `{univ}` already
covers the product space exactly.
-/
theorem durrett2019_example_4_7_4_finitePrefixEventSet_countable_cover
    (S : Type*) [MeasurableSpace S] (μ : Measure (ℕ -> S)) :
    ∃ D : Set (Set (ℕ -> S)),
      D.Countable ∧ D ⊆ durrett2019_example_4_7_4_finitePrefixEventSet S ∧
        μ (⋃₀ D)ᶜ = 0 := by
  refine ⟨{Set.univ}, Set.countable_singleton Set.univ, ?_, ?_⟩
  · intro A hA
    rw [Set.mem_singleton_iff] at hA
    rw [hA]
    exact durrett2019_example_4_7_4_finitePrefixEventSet_univ_mem S
  · simp

/--
Every measurable finite cylinder is a finite-prefix event, after enlarging the
prefix to contain all cylinder coordinates.
-/
theorem durrett2019_example_4_7_4_cylinder_mem_finitePrefixEventSet
    {S : Type*} [MeasurableSpace S] {I : Finset ℕ} {T : Set (I -> S)}
    (hT : MeasurableSet T) :
    MeasureTheory.cylinder (α := fun _ : ℕ => S) I T ∈
      durrett2019_example_4_7_4_finitePrefixEventSet S := by
  let n : ℕ := I.sup id + 1
  have hI : I ⊆ Finset.range n := by
    intro i hi
    rw [Finset.mem_range]
    exact Nat.lt_succ_of_le (Finset.le_sup (s := I) (f := id) hi)
  refine ⟨n, ?_⟩
  have hmeas_restrict :
      Measurable[durrett2019_theorem_4_3_8_prefixFiltration S n]
        (I.restrict : (ℕ -> S) -> I -> S) := by
    have hcomap_le :
        MeasurableSpace.pi.comap (I.restrict : (ℕ -> S) -> I -> S) ≤
          MeasurableSpace.pi.comap
            ((Finset.range n).restrict : (ℕ -> S) -> Finset.range n -> S) := by
      rw [← Finset.restrict₂_comp_restrict hI, ← MeasurableSpace.comap_comp]
      exact MeasurableSpace.comap_mono (Finset.measurable_restrict₂ hI).comap_le
    simpa [durrett2019_theorem_4_3_8_prefixFiltration] using
      Measurable.of_comap_le hcomap_le
  change MeasurableSet[durrett2019_theorem_4_3_8_prefixFiltration S n]
    ((I.restrict : (ℕ -> S) -> I -> S) ⁻¹' T)
  exact hmeas_restrict hT

/--
The finite-prefix event ring generates the ambient countable product
sigma-field.  This discharges the generation hypothesis in the measured-set
density wrapper by reusing Mathlib's measurable-cylinder generation theorem.
-/
theorem durrett2019_example_4_7_4_finitePrefixEventSet_generateFrom
    (S : Type*) [MeasurableSpace S] :
    (inferInstance : MeasurableSpace (ℕ -> S)) =
      MeasurableSpace.generateFrom
        (durrett2019_example_4_7_4_finitePrefixEventSet S) := by
  apply le_antisymm
  · rw [← MeasureTheory.generateFrom_measurableCylinders (α := fun _ : ℕ => S)]
    refine MeasurableSpace.generateFrom_le ?_
    intro A hA
    rcases (MeasureTheory.mem_measurableCylinders A).mp hA with ⟨I, T, hT, rfl⟩
    exact
      MeasurableSpace.measurableSet_generateFrom
        (durrett2019_example_4_7_4_cylinder_mem_finitePrefixEventSet (S := S) hT)
  · refine MeasurableSpace.generateFrom_le ?_
    intro A hA
    exact durrett2019_example_4_7_4_finitePrefixEventSet_measurableSet hA

/--
Durrett 2019, Example 4.7.4 / Hewitt-Savage approximation support.  If the
finite-prefix event ring generates the ambient product sigma-field, then every
ambient measurable event is approximable in symmetric-difference measure by a
finite-prefix event.
-/
theorem durrett2019_example_4_7_4_exists_measure_symmDiff_lt_of_finitePrefixEventSet_generateFrom
    {S : Type*} [MeasurableSpace S] {μ : Measure (ℕ -> S)} [IsFiniteMeasure μ]
    (hgenerate :
      (inferInstance : MeasurableSpace (ℕ -> S)) =
        MeasurableSpace.generateFrom
          (durrett2019_example_4_7_4_finitePrefixEventSet S))
    {B : Set (ℕ -> S)} (hB : MeasurableSet B) {ε : ℝ≥0∞} (hε : 0 < ε) :
    ∃ D ∈ durrett2019_example_4_7_4_finitePrefixEventSet S, μ (D ∆ B) < ε :=
  MeasureTheory.exists_measure_symmDiff_lt_of_generateFrom_isSetRing
    (durrett2019_example_4_7_4_finitePrefixEventSet_isSetRing S)
    (durrett2019_example_4_7_4_finitePrefixEventSet_countable_cover S μ)
    hgenerate hB hε

/--
Finite-prefix events approximate every ambient measurable event in
symmetric-difference measure.
-/
theorem durrett2019_example_4_7_4_exists_measure_symmDiff_lt_finitePrefixEventSet
    {S : Type*} [MeasurableSpace S] {μ : Measure (ℕ -> S)} [IsFiniteMeasure μ]
    {B : Set (ℕ -> S)} (hB : MeasurableSet B) {ε : ℝ≥0∞} (hε : 0 < ε) :
    ∃ D ∈ durrett2019_example_4_7_4_finitePrefixEventSet S, μ (D ∆ B) < ε :=
  durrett2019_example_4_7_4_exists_measure_symmDiff_lt_of_finitePrefixEventSet_generateFrom
    (μ := μ)
    (durrett2019_example_4_7_4_finitePrefixEventSet_generateFrom S) hB hε

/--
Durrett 2019, Example 4.7.4 / Hewitt-Savage approximation support.  The
finite-prefix event-ring density theorem can be packaged as a sequence whose
symmetric-difference measure tends to zero.
-/
theorem durrett2019_example_4_7_4_exists_prefix_symmDiff_tendsto_zero_of_finitePrefixEventSet_generateFrom
    {S : Type*} [MeasurableSpace S] {μ : Measure (ℕ -> S)} [IsFiniteMeasure μ]
    (hgenerate :
      (inferInstance : MeasurableSpace (ℕ -> S)) =
        MeasurableSpace.generateFrom
          (durrett2019_example_4_7_4_finitePrefixEventSet S))
    {B : Set (ℕ -> S)} (hB : MeasurableSet B) :
    ∃ D : ℕ -> Set (ℕ -> S), ∃ cutoff : ℕ -> ℕ,
      (∀ k,
        MeasurableSet[durrett2019_theorem_4_3_8_prefixFiltration S (cutoff k)]
          (D k)) ∧
      Tendsto (fun k => μ (D k ∆ B)) atTop (𝓝 0) := by
  classical
  have hexists :
      ∀ k : ℕ, ∃ D ∈ durrett2019_example_4_7_4_finitePrefixEventSet S,
        μ (D ∆ B) < ((k : ℝ≥0∞)⁻¹) := by
    intro k
    exact
      durrett2019_example_4_7_4_exists_measure_symmDiff_lt_of_finitePrefixEventSet_generateFrom
        (μ := μ) hgenerate hB (ENNReal.inv_pos.mpr (ENNReal.natCast_ne_top k))
  choose D hD_mem hD_bound using hexists
  choose cutoff hD_prefix using hD_mem
  refine ⟨D, cutoff, hD_prefix, ?_⟩
  rw [ENNReal.tendsto_nhds_zero]
  intro ε hε
  have hinv := ENNReal.tendsto_inv_nat_nhds_zero
  rw [ENNReal.tendsto_nhds_zero] at hinv
  filter_upwards [hinv ε hε] with k hk
  exact (le_of_lt (hD_bound k)).trans hk

/--
Finite-prefix events can be chosen as a sequence whose symmetric-difference
measure tends to zero for any ambient measurable event.
-/
theorem durrett2019_example_4_7_4_exists_prefix_symmDiff_tendsto_zero
    {S : Type*} [MeasurableSpace S] {μ : Measure (ℕ -> S)} [IsFiniteMeasure μ]
    {B : Set (ℕ -> S)} (hB : MeasurableSet B) :
    ∃ D : ℕ -> Set (ℕ -> S), ∃ cutoff : ℕ -> ℕ,
      (∀ k,
        MeasurableSet[durrett2019_theorem_4_3_8_prefixFiltration S (cutoff k)]
          (D k)) ∧
      Tendsto (fun k => μ (D k ∆ B)) atTop (𝓝 0) :=
  durrett2019_example_4_7_4_exists_prefix_symmDiff_tendsto_zero_of_finitePrefixEventSet_generateFrom
    (μ := μ)
    (durrett2019_example_4_7_4_finitePrefixEventSet_generateFrom S) hB

/--
Durrett 2019, Example 4.7.4 / Hewitt-Savage approximation support.  Under the
finite-prefix event-ring generation statement, every VdVW
permutation-symmetric-tail event has the prefix symmetric-difference
approximants required by V305.
-/
theorem durrett2019_example_4_7_4_eval_prefixApprox_of_finitePrefixEventSet_generateFrom
    {P : Measure ℝ} [IsProbabilityMeasure P]
    (hgenerate :
      (inferInstance : MeasurableSpace (ℕ -> ℝ)) =
        MeasurableSpace.generateFrom
          (durrett2019_example_4_7_4_finitePrefixEventSet ℝ)) :
    ∀ {B : Set (ℕ -> ℝ)},
      MeasurableSet[⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n] B ->
        ∃ D : ℕ -> Set (ℕ -> ℝ), ∃ cutoff : ℕ -> ℕ,
          (∀ k,
            MeasurableSet[durrett2019_theorem_4_3_8_prefixFiltration ℝ (cutoff k)]
              (D k)) ∧
          Tendsto (fun k => vdVWInfiniteProductMeasure P (D k ∆ B)) atTop (𝓝 0) := by
  intro B hB
  have htail_le :
      (⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n) ≤
        (inferInstance : MeasurableSpace (ℕ -> ℝ)) := by
    refine (iInf_le (fun n : ℕ => vdVWPermutationSymmetricMeasurableSpace ℝ n) 0).trans ?_
    refine MeasurableSpace.generateFrom_le ?_
    intro s hs
    rcases hs with ⟨statistic, hmeas, _hsymm, target, htarget, rfl⟩
    exact hmeas htarget
  exact
    durrett2019_example_4_7_4_exists_prefix_symmDiff_tendsto_zero_of_finitePrefixEventSet_generateFrom
      (μ := vdVWInfiniteProductMeasure P) hgenerate (htail_le B hB)

/--
Every VdVW permutation-symmetric-tail event has finite-prefix approximants in
the symmetric-difference metric required by V305.
-/
theorem durrett2019_example_4_7_4_eval_prefixApprox
    {P : Measure ℝ} [IsProbabilityMeasure P] :
    ∀ {B : Set (ℕ -> ℝ)},
      MeasurableSet[⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n] B ->
        ∃ D : ℕ -> Set (ℕ -> ℝ), ∃ cutoff : ℕ -> ℕ,
          (∀ k,
            MeasurableSet[durrett2019_theorem_4_3_8_prefixFiltration ℝ (cutoff k)]
              (D k)) ∧
          Tendsto (fun k => vdVWInfiniteProductMeasure P (D k ∆ B)) atTop (𝓝 0) :=
  durrett2019_example_4_7_4_eval_prefixApprox_of_finitePrefixEventSet_generateFrom
    (P := P) (durrett2019_example_4_7_4_finitePrefixEventSet_generateFrom ℝ)

/--
Durrett 2019, Example 4.7.4 / Hewitt-Savage approximation support.  If a
sequence of measurable sets converges to a target in the symmetric-difference
measure metric, then their measures converge.

This is the `MeasuredSets` continuity primitive in the exact source shape used
by the prefix-approximation route.
-/
theorem durrett2019_example_4_7_4_tendsto_measure_of_symmDiff_tendsto_zero
    {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω}
    {B : Set Ω} {D : ℕ -> Set Ω}
    (hB : MeasurableSet B) (hD : ∀ k, MeasurableSet (D k))
    (hsymm : Tendsto (fun k => μ (D k ∆ B)) atTop (𝓝 0)) :
    Tendsto (fun k => μ (D k)) atTop (𝓝 (μ B)) := by
  let target : MeasuredSets μ := ⟨B, hB⟩
  let approx : ℕ -> MeasuredSets μ := fun k => ⟨D k, hD k⟩
  have happrox : Tendsto approx atTop (𝓝 target) := by
    rw [tendsto_iff_edist_tendsto_0]
    simpa [approx, target, MeasuredSets.edist_def] using hsymm
  exact MeasuredSets.continuous_measure.tendsto target |>.comp happrox

/--
Durrett 2019, Example 4.7.4 / Hewitt-Savage approximation support.  Symmetric
difference convergence of finite-prefix approximants is stable after
intersecting with a fixed measurable event.
-/
theorem durrett2019_example_4_7_4_tendsto_measure_inter_of_symmDiff_tendsto_zero
    {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω}
    {A B : Set Ω} {D : ℕ -> Set Ω}
    (hA : MeasurableSet A) (hB : MeasurableSet B)
    (hD : ∀ k, MeasurableSet (D k))
    (hsymm : Tendsto (fun k => μ (D k ∆ B)) atTop (𝓝 0)) :
    Tendsto (fun k => μ (A ∩ D k)) atTop (𝓝 (μ (A ∩ B))) := by
  refine
    durrett2019_example_4_7_4_tendsto_measure_of_symmDiff_tendsto_zero
      (μ := μ) (B := A ∩ B) (D := fun k => A ∩ D k)
      (hA.inter hB) (fun k => hA.inter (hD k)) ?_
  rw [ENNReal.tendsto_nhds_zero] at hsymm ⊢
  intro ε hε
  filter_upwards [hsymm ε hε] with k hk
  have hsubset : (A ∩ D k) ∆ (A ∩ B) ⊆ D k ∆ B := by
    rw [← Set.inter_symmDiff_distrib_left A (D k) B]
    exact Set.inter_subset_right
  exact (measure_mono hsubset).trans hk

/--
Durrett 2019, Example 4.7.4 / Hewitt-Savage route support.  A
prefix-approximation theorem stated in the natural symmetric-difference metric
implies exactly the two measure-coordinate limits consumed by the V304
self-independence bridge.
-/
theorem durrett2019_example_4_7_4_eval_prefixLimit_of_symmDiff_prefix_approx
    {P : Measure ℝ} [IsProbabilityMeasure P]
    (hprefixApprox :
      ∀ {B : Set (ℕ -> ℝ)},
        MeasurableSet[⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n] B ->
          ∃ D : ℕ -> Set (ℕ -> ℝ), ∃ cutoff : ℕ -> ℕ,
            (∀ k,
              MeasurableSet[durrett2019_theorem_4_3_8_prefixFiltration ℝ (cutoff k)]
                (D k)) ∧
            Tendsto (fun k => vdVWInfiniteProductMeasure P (D k ∆ B)) atTop (𝓝 0)) :
      ∀ {A B : Set (ℕ -> ℝ)},
        MeasurableSet[⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n] A ->
        MeasurableSet[⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n] B ->
          ∃ D : ℕ -> Set (ℕ -> ℝ), ∃ cutoff : ℕ -> ℕ,
            (∀ k,
              MeasurableSet[durrett2019_theorem_4_3_8_prefixFiltration ℝ (cutoff k)]
                (D k)) ∧
            Tendsto (fun k => vdVWInfiniteProductMeasure P (A ∩ D k)) atTop
              (𝓝 (vdVWInfiniteProductMeasure P (A ∩ B))) ∧
            Tendsto (fun k => vdVWInfiniteProductMeasure P (D k)) atTop
              (𝓝 (vdVWInfiniteProductMeasure P B)) := by
  intro A B hA hB
  let μ : Measure (ℕ -> ℝ) := vdVWInfiniteProductMeasure P
  have htail_le :
      (⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n) ≤
        (inferInstance : MeasurableSpace (ℕ -> ℝ)) := by
    refine (iInf_le (fun n : ℕ => vdVWPermutationSymmetricMeasurableSpace ℝ n) 0).trans ?_
    refine MeasurableSpace.generateFrom_le ?_
    intro s hs
    rcases hs with ⟨statistic, hmeas, _hsymm, target, htarget, rfl⟩
    exact hmeas htarget
  rcases hprefixApprox hB with ⟨D, cutoff, hD_prefix, hsymm⟩
  refine ⟨D, cutoff, hD_prefix, ?_, ?_⟩
  · have hA_ambient : MeasurableSet A := htail_le A hA
    have hB_ambient : MeasurableSet B := htail_le B hB
    have hD_ambient : ∀ k, MeasurableSet (D k) := by
      intro k
      exact (durrett2019_theorem_4_3_8_prefixFiltration ℝ).le (cutoff k) (D k)
        (hD_prefix k)
    simpa [μ] using
      (durrett2019_example_4_7_4_tendsto_measure_inter_of_symmDiff_tendsto_zero
        (μ := μ) (A := A) (B := B) (D := D)
        hA_ambient hB_ambient hD_ambient (by simpa [μ] using hsymm))
  · have hB_ambient : MeasurableSet B := htail_le B hB
    have hD_ambient : ∀ k, MeasurableSet (D k) := by
      intro k
      exact (durrett2019_theorem_4_3_8_prefixFiltration ℝ).le (cutoff k) (D k)
        (hD_prefix k)
    simpa [μ] using
      (durrett2019_example_4_7_4_tendsto_measure_of_symmDiff_tendsto_zero
        (μ := μ) (B := B) (D := D)
        hB_ambient hD_ambient (by simpa [μ] using hsymm))

/--
Durrett 2019, Example 4.7.4 / Hewitt-Savage route support.  Once every
permutation-symmetric-tail event has the product formula against every finite
prefix event, and tail events are limits of finite-prefix events in the two
measure coordinates needed below, the VdVW permutation-symmetric tail is
independent of itself.
-/
theorem durrett2019_example_4_7_4_eval_permutationSymmetricTail_indep_self_of_prefix_product_limit
    {P : Measure ℝ} [IsProbabilityMeasure P]
    (hprefixProduct :
      ∀ {A D : Set (ℕ -> ℝ)} {n : ℕ},
        MeasurableSet[⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n] A ->
        MeasurableSet[durrett2019_theorem_4_3_8_prefixFiltration ℝ n] D ->
          vdVWInfiniteProductMeasure P (A ∩ D) =
            vdVWInfiniteProductMeasure P A * vdVWInfiniteProductMeasure P D)
    (hprefixLimit :
      ∀ {A B : Set (ℕ -> ℝ)},
        MeasurableSet[⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n] A ->
        MeasurableSet[⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n] B ->
          ∃ D : ℕ -> Set (ℕ -> ℝ), ∃ cutoff : ℕ -> ℕ,
            (∀ k,
              MeasurableSet[durrett2019_theorem_4_3_8_prefixFiltration ℝ (cutoff k)]
                (D k)) ∧
            Tendsto (fun k => vdVWInfiniteProductMeasure P (A ∩ D k)) atTop
              (𝓝 (vdVWInfiniteProductMeasure P (A ∩ B))) ∧
            Tendsto (fun k => vdVWInfiniteProductMeasure P (D k)) atTop
              (𝓝 (vdVWInfiniteProductMeasure P B))) :
    Indep
      (⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n)
      (⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n)
      (vdVWInfiniteProductMeasure P) := by
  let tailSigma : MeasurableSpace (ℕ -> ℝ) :=
    ⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n
  let μ : @Measure (ℕ -> ℝ) MeasurableSpace.pi :=
    vdVWInfiniteProductMeasure P
  change @_root_.ProbabilityTheory.Indep (ℕ -> ℝ) tailSigma tailSigma MeasurableSpace.pi μ
  refine
    (_root_.ProbabilityTheory.indep_iff_forall_indepSet
      (m₁ := tailSigma) (m₂ := tailSigma) (μ := μ)).mpr ?_
  intro A B hA hB
  have htail_le :
      tailSigma ≤ MeasurableSpace.pi := by
    refine (iInf_le (fun n : ℕ => vdVWPermutationSymmetricMeasurableSpace ℝ n) 0).trans ?_
    refine MeasurableSpace.generateFrom_le ?_
    intro s hs
    rcases hs with ⟨statistic, hmeas, _hsymm, target, htarget, rfl⟩
    exact hmeas htarget
  have hA_ambient : @MeasurableSet (ℕ -> ℝ) MeasurableSpace.pi A := htail_le A hA
  have hB_ambient : @MeasurableSet (ℕ -> ℝ) MeasurableSpace.pi B := htail_le B hB
  refine
    (_root_.ProbabilityTheory.indepSet_iff_measure_inter_eq_mul
      (μ := μ) hA_ambient hB_ambient).mpr ?_
  rcases hprefixLimit (A := A) (B := B) (by simpa [tailSigma] using hA)
      (by simpa [tailSigma] using hB) with
    ⟨D, cutoff, hD_prefix, hinter, hmeasure⟩
  have hproduct_tendsto :
      Tendsto (fun k => μ (A ∩ D k)) atTop (𝓝 (μ A * μ B)) := by
    have hseq_eq :
        (fun k => μ (A ∩ D k)) = fun k => μ A * μ (D k) := by
      funext k
      simpa [μ, tailSigma] using
        (hprefixProduct (A := A) (D := D k) (n := cutoff k)
          (by simpa [tailSigma] using hA) (hD_prefix k))
    rw [hseq_eq]
    exact
      ENNReal.Tendsto.const_mul (by simpa [μ] using hmeasure)
        (Or.inr (measure_ne_top μ A))
  exact tendsto_nhds_unique (by simpa [μ] using hinter) hproduct_tendsto

/--
Durrett 2019, Example 4.7.4 / Hewitt-Savage route support.  This is the
source-shaped self-independence consumer after V305: product formulas against
finite-prefix events plus symmetric-difference prefix approximation of each
tail event imply self-independence of the VdVW permutation-symmetric tail.
-/
theorem durrett2019_example_4_7_4_eval_permutationSymmetricTail_indep_self_of_prefix_product_symmDiff_approx
    {P : Measure ℝ} [IsProbabilityMeasure P]
    (hprefixProduct :
      ∀ {A D : Set (ℕ -> ℝ)} {n : ℕ},
        MeasurableSet[⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n] A ->
        MeasurableSet[durrett2019_theorem_4_3_8_prefixFiltration ℝ n] D ->
          vdVWInfiniteProductMeasure P (A ∩ D) =
            vdVWInfiniteProductMeasure P A * vdVWInfiniteProductMeasure P D)
    (hprefixApprox :
      ∀ {B : Set (ℕ -> ℝ)},
        MeasurableSet[⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n] B ->
          ∃ D : ℕ -> Set (ℕ -> ℝ), ∃ cutoff : ℕ -> ℕ,
            (∀ k,
              MeasurableSet[durrett2019_theorem_4_3_8_prefixFiltration ℝ (cutoff k)]
                (D k)) ∧
            Tendsto (fun k => vdVWInfiniteProductMeasure P (D k ∆ B)) atTop (𝓝 0)) :
    Indep
      (⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n)
      (⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n)
      (vdVWInfiniteProductMeasure P) :=
  durrett2019_example_4_7_4_eval_permutationSymmetricTail_indep_self_of_prefix_product_limit
    (P := P) hprefixProduct
    (durrett2019_example_4_7_4_eval_prefixLimit_of_symmDiff_prefix_approx
      (P := P) hprefixApprox)

/--
Durrett 2019, Example 4.7.4 / Hewitt-Savage route support.  After the
finite-prefix event-ring generation theorem is available, V305 reduces
self-independence to the prefix-product formula alone.
-/
theorem durrett2019_example_4_7_4_eval_permutationSymmetricTail_indep_self_of_prefix_product_generateFrom
    {P : Measure ℝ} [IsProbabilityMeasure P]
    (hgenerate :
      (inferInstance : MeasurableSpace (ℕ -> ℝ)) =
        MeasurableSpace.generateFrom
          (durrett2019_example_4_7_4_finitePrefixEventSet ℝ))
    (hprefixProduct :
      ∀ {A D : Set (ℕ -> ℝ)} {n : ℕ},
        MeasurableSet[⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n] A ->
        MeasurableSet[durrett2019_theorem_4_3_8_prefixFiltration ℝ n] D ->
          vdVWInfiniteProductMeasure P (A ∩ D) =
            vdVWInfiniteProductMeasure P A * vdVWInfiniteProductMeasure P D) :
    Indep
      (⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n)
      (⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n)
      (vdVWInfiniteProductMeasure P) :=
  durrett2019_example_4_7_4_eval_permutationSymmetricTail_indep_self_of_prefix_product_symmDiff_approx
    (P := P) hprefixProduct
    (durrett2019_example_4_7_4_eval_prefixApprox_of_finitePrefixEventSet_generateFrom
      (P := P) hgenerate)

/--
Durrett 2019, Example 4.7.4 / Hewitt-Savage route support.  With the
finite-prefix approximation theorem discharged, self-independence now reduces
to the product formula against finite-prefix events.
-/
theorem durrett2019_example_4_7_4_eval_permutationSymmetricTail_indep_self_of_prefix_product
    {P : Measure ℝ} [IsProbabilityMeasure P]
    (hprefixProduct :
      ∀ {A D : Set (ℕ -> ℝ)} {n : ℕ},
        MeasurableSet[⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n] A ->
        MeasurableSet[durrett2019_theorem_4_3_8_prefixFiltration ℝ n] D ->
          vdVWInfiniteProductMeasure P (A ∩ D) =
            vdVWInfiniteProductMeasure P A * vdVWInfiniteProductMeasure P D) :
    Indep
      (⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n)
      (⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n)
      (vdVWInfiniteProductMeasure P) :=
  durrett2019_example_4_7_4_eval_permutationSymmetricTail_indep_self_of_prefix_product_generateFrom
    (P := P) (durrett2019_example_4_7_4_finitePrefixEventSet_generateFrom ℝ)
    hprefixProduct

/--
Durrett 2019, Example 4.7.4 product-space source algebra: the finite swap of
prefix coordinate `i` and coordinate `0` transports `xi_i` to `xi_0`.
-/
theorem durrett2019_example_4_7_4_eval_coordinate_eq_zero_comp_prefixSwap
    {n i : ℕ} (hi : i < n) :
    (fun sequence : ℕ -> ℝ => sequence i) =
      fun sequence =>
        (vdVWNatCoordinatePermMeasurableEquiv (Observation := ℝ)
          (vdVWNatPermOfFin (Equiv.swap (⟨i, hi⟩ : Fin n)
            (⟨0, Nat.lt_of_le_of_lt (Nat.zero_le i) hi⟩ : Fin n)))
          sequence) 0 := by
  ext sequence
  let iFin : Fin n := ⟨i, hi⟩
  let zeroFin : Fin n := ⟨0, Nat.lt_of_le_of_lt (Nat.zero_le i) hi⟩
  let permFin : Equiv.Perm (Fin n) := Equiv.swap iFin zeroFin
  let permNat : Equiv.Perm ℕ := vdVWNatPermOfFin permFin
  have hnat : permNat i = 0 := by
    change vdVWNatPermOfFin permFin (iFin : ℕ) = (zeroFin : ℕ)
    rw [vdVWNatPermOfFin_apply_fin]
    simp [permFin, iFin, zeroFin]
  have hcoord :=
    vdVWNatCoordinatePermMeasurableEquiv_apply_apply
      (Observation := ℝ) permNat sequence i
  rw [hnat] at hcoord
  exact hcoord.symm

set_option maxHeartbeats 800000 in
/--
Durrett 2019, Example 4.7.4 product-space finite-prefix conditional
symmetry.  On the iid infinite product sequence space, finite coordinate swaps
provide the exchangeability transports required by V294.
-/
theorem durrett2019_example_4_7_4_eval_condExp_eq_zero_of_prefixSwap
    {P : Measure ℝ} [IsProbabilityMeasure P]
    {n i : ℕ} (hi : i < n)
    (hi_int : Integrable (fun sequence : ℕ -> ℝ => sequence i)
      (vdVWInfiniteProductMeasure P))
    (h0_int : Integrable (fun sequence : ℕ -> ℝ => sequence 0)
      (vdVWInfiniteProductMeasure P)) :
    (vdVWInfiniteProductMeasure P)[
        (fun sequence : ℕ -> ℝ => sequence i) |
        durrett2019_example_4_7_4_reverseAverageSigma
          (fun k sequence => sequence k) n] =ᵐ[vdVWInfiniteProductMeasure P]
      (vdVWInfiniteProductMeasure P)[
        (fun sequence : ℕ -> ℝ => sequence 0) |
        durrett2019_example_4_7_4_reverseAverageSigma
          (fun k sequence => sequence k) n] := by
  let zeroFin : Fin n := ⟨0, Nat.lt_of_le_of_lt (Nat.zero_le i) hi⟩
  let iFin : Fin n := ⟨i, hi⟩
  let permFin : Equiv.Perm (Fin n) := Equiv.swap iFin zeroFin
  let permNat : Equiv.Perm ℕ := vdVWNatPermOfFin permFin
  let T : (ℕ -> ℝ) ≃ᵐ (ℕ -> ℝ) :=
    vdVWNatCoordinatePermMeasurableEquiv (Observation := ℝ) permNat
  have hT_pres :
      MeasurePreserving T
        (vdVWInfiniteProductMeasure P) (vdVWInfiniteProductMeasure P) := by
    simpa [T, permNat] using
      vdVWInfiniteProductMeasure_measurePreserving_natCoordinatePerm
        (Observation := ℝ) P permNat
  have hprefix :
      (fun sequence : ℕ -> ℝ =>
        durrett2019_example_4_7_4_prefixSum
          (fun k sequence => sequence k) n (T sequence)) =
        durrett2019_example_4_7_4_prefixSum
          (fun k sequence => sequence k) n := by
    simpa [T, permNat, permFin] using
      durrett2019_example_4_7_4_eval_prefixSum_comp_natPermOfFin
        (n := n) permFin
  have htail :
      ∀ j : ℕ, n ≤ j ->
        (fun sequence : ℕ -> ℝ => (T sequence) j) =
          fun sequence => sequence j := by
    intro j hj
    simpa [T, permNat, permFin] using
      durrett2019_example_4_7_4_eval_tail_comp_natPermOfFin
        (n := n) (j := j) hj permFin
  have hT_sets :
      ∀ s : Set (ℕ -> ℝ),
        MeasurableSet[
          durrett2019_example_4_7_4_reverseAverageSigma
            (fun k sequence => sequence k) n] s ->
          T ⁻¹' s = s :=
    durrett2019_example_4_7_4_preimage_reverseAverageSigma_eq_of_prefixSum_tail_invariant
      (ξ := fun k sequence => sequence k) (n := n) T hprefix htail
  have hcoord :
      (fun sequence : ℕ -> ℝ => sequence i) =
        fun sequence => (fun sequence : ℕ -> ℝ => sequence 0) (T sequence) := by
    simpa [T, permNat, permFin, iFin, zeroFin] using
      durrett2019_example_4_7_4_eval_coordinate_eq_zero_comp_prefixSwap
        (n := n) (i := i) hi
  exact
    durrett2019_example_4_7_4_condExp_eq_zero_of_reverseAverage_invariant_equiv
      (P := vdVWInfiniteProductMeasure P)
      (ξ := fun k sequence => sequence k)
      (n := n) (i := i)
      (fun k => measurable_pi_apply k)
      hi_int h0_int T hT_pres hT_sets hcoord

/--
Durrett 2019, Example 4.7.4 product-space finite-prefix conditional symmetry,
vectorized over all prefix coordinates.
-/
theorem durrett2019_example_4_7_4_eval_prefix_condExp_symmetry_of_prefixSwaps
    {P : Measure ℝ} [IsProbabilityMeasure P] {n : ℕ}
    (hξ_int :
      ∀ i ∈ Finset.range n,
        Integrable (fun sequence : ℕ -> ℝ => sequence i)
          (vdVWInfiniteProductMeasure P)) :
    ∀ i ∈ Finset.range n,
      (vdVWInfiniteProductMeasure P)[
          (fun sequence : ℕ -> ℝ => sequence i) |
          durrett2019_example_4_7_4_reverseAverageSigma
            (fun k sequence => sequence k) n] =ᵐ[vdVWInfiniteProductMeasure P]
        (vdVWInfiniteProductMeasure P)[
          (fun sequence : ℕ -> ℝ => sequence 0) |
          durrett2019_example_4_7_4_reverseAverageSigma
            (fun k sequence => sequence k) n] := by
  intro i hi
  exact
    durrett2019_example_4_7_4_eval_condExp_eq_zero_of_prefixSwap
      (P := P) (n := n) (i := i) (Finset.mem_range.mp hi)
      (hξ_int i hi)
      (hξ_int 0
        (Finset.mem_range.mpr
          (Nat.lt_of_le_of_lt (Nat.zero_le i) (Finset.mem_range.mp hi))))

/--
Durrett 2019, Example 4.7.4 product-space conditional-average display.
For the coordinate-evaluation process on the iid infinite product sequence
space, finite coordinate swaps prove the finite-prefix symmetry input, so the
compiled V292 average calculation gives `E(xi_0 | G_n) = S_n / n`.
-/
theorem durrett2019_example_4_7_4_eval_condExp_first_eq_prefixAverage_div_product
    {P : Measure ℝ} [IsProbabilityMeasure P] {n : ℕ}
    (hn : 0 < n)
    (hξ_int :
      ∀ i ∈ Finset.range n,
        Integrable (fun sequence : ℕ -> ℝ => sequence i)
          (vdVWInfiniteProductMeasure P)) :
    (vdVWInfiniteProductMeasure P)[
        (fun sequence : ℕ -> ℝ => sequence 0) |
        durrett2019_example_4_7_4_reverseAverageSigma
          (fun k sequence => sequence k) n] =ᵐ[vdVWInfiniteProductMeasure P]
      fun sequence : ℕ -> ℝ =>
        (∑ i ∈ Finset.range n, sequence i) / (n : ℝ) := by
  exact
    durrett2019_example_4_7_4_condExp_first_eq_reverseAverageSigma_prefixAverage_div
      (P := vdVWInfiniteProductMeasure P)
      (ξ := fun k sequence => sequence k)
      (n := n) hn
      (fun k => measurable_pi_apply k)
      hξ_int
      (durrett2019_example_4_7_4_eval_prefix_condExp_symmetry_of_prefixSwaps
        (P := P) (n := n) hξ_int)

/--
Durrett 2019, Example 4.7.4 product-space integrability source bridge.
Coordinate evaluations on the iid infinite product sequence space are
integrable whenever the one-dimensional identity random variable is integrable.
-/
theorem durrett2019_example_4_7_4_eval_integrable_of_integrable_id
    {P : Measure ℝ} [IsProbabilityMeasure P] (hid : Integrable id P) (i : ℕ) :
    Integrable (fun sequence : ℕ -> ℝ => sequence i)
      (vdVWInfiniteProductMeasure P) := by
  have hmp :
      MeasurePreserving (fun sequence : ℕ -> ℝ => sequence i)
        (vdVWInfiniteProductMeasure P) P := by
    simpa [vdVWInfiniteProductMeasure] using
      measurePreserving_eval_infinitePi (μ := fun _ : ℕ => P) i
  simpa [vdVWInfiniteProductMeasure, Function.comp_def] using
    hmp.integrable_comp_of_integrable hid

/--
Durrett 2019, Example 4.7.4 product-space conditional-average display with the
source moment assumption on the one-dimensional law.  This removes the
coordinate-by-coordinate integrability hypothesis from V295.
-/
theorem durrett2019_example_4_7_4_eval_condExp_first_eq_prefixAverage_div_product_of_integrable_id
    {P : Measure ℝ} [IsProbabilityMeasure P] {n : ℕ}
    (hn : 0 < n) (hid : Integrable id P) :
    (vdVWInfiniteProductMeasure P)[
        (fun sequence : ℕ -> ℝ => sequence 0) |
        durrett2019_example_4_7_4_reverseAverageSigma
          (fun k sequence => sequence k) n] =ᵐ[vdVWInfiniteProductMeasure P]
      fun sequence : ℕ -> ℝ =>
        (∑ i ∈ Finset.range n, sequence i) / (n : ℝ) := by
  exact
    durrett2019_example_4_7_4_eval_condExp_first_eq_prefixAverage_div_product
      (P := P) (n := n) hn
      (fun i _hi =>
        durrett2019_example_4_7_4_eval_integrable_of_integrable_id
          (P := P) hid i)

/--
Durrett 2019, Example 4.7.4 product-space backwards-martingale route under
reverse-tail zero-one triviality.  The proof uses the conditional-average
display from V296 and the backwards Levy/tail-constant handoff, rather than
the direct strong-law primitive.
-/
theorem durrett2019_example_4_7_4_eval_prefixAverage_ae_tendsto_of_integrable_id_and_tail_zero_or_one
    {P : Measure ℝ} [IsProbabilityMeasure P] (hid : Integrable id P)
    (hzeroOne :
      ∀ B : Set (ℕ -> ℝ),
        MeasurableSet[
          ⨅ n : ℕ,
            durrett2019_example_4_7_4_reverseAverageSigma
              (fun k (sequence : ℕ -> ℝ) => sequence k) n] B ->
          vdVWInfiniteProductMeasure P B = 0 ∨ vdVWInfiniteProductMeasure P B = 1) :
    ∀ᵐ sequence ∂(vdVWInfiniteProductMeasure P),
      Tendsto
        (fun n : ℕ => (∑ i ∈ Finset.range n, sequence i) / (n : ℝ))
        atTop
        (𝓝 (∫ x : ℝ, x ∂P)) := by
  let μ : Measure (ℕ -> ℝ) := vdVWInfiniteProductMeasure P
  let ξ : ℕ -> (ℕ -> ℝ) -> ℝ := fun k sequence => sequence k
  let 𝒢 : ℕ -> MeasurableSpace (ℕ -> ℝ) :=
    fun n => durrett2019_example_4_7_4_reverseAverageSigma ξ n
  let A : ℕ -> (ℕ -> ℝ) -> ℝ :=
    fun n sequence => (∑ i ∈ Finset.range n, sequence i) / (n : ℝ)
  have hroute :
      ∀ᵐ sequence ∂μ,
        Tendsto
          (fun n : ℕ => A n sequence)
          atTop
          (𝓝 (∫ sequence, sequence 0 ∂μ)) := by
    refine
      durrett2019_example_4_7_4_ae_tendsto_of_eventually_ae_eq_condExp_nat_and_tail_zero_or_one
        (P := μ) (𝒢 := 𝒢) (A := A)
        (f := fun sequence : ℕ -> ℝ => sequence 0)
        (durrett2019_example_4_7_4_reverseAverageSigma_antitone ξ)
        ?h𝒢_le ?hf_int 1 ?hA ?hzeroOne
    · intro n
      exact
        durrett2019_example_4_7_4_reverseAverageSigma_le
          (ξ := ξ) (n := n) (fun i => measurable_pi_apply i)
    · exact
        durrett2019_example_4_7_4_eval_integrable_of_integrable_id
          (P := P) hid 0
    · intro n hn
      have hn_pos : 0 < n := Nat.succ_le_iff.mp hn
      exact
        (durrett2019_example_4_7_4_eval_condExp_first_eq_prefixAverage_div_product_of_integrable_id
          (P := P) (n := n) hn_pos hid).symm
    · simpa [𝒢, ξ, μ] using hzeroOne
  have hmean :
      (∫ sequence, sequence 0 ∂μ) = ∫ x : ℝ, x ∂P := by
    simpa [μ, id] using
      (vdVWInfiniteProductMeasure_coordinate_hasLaw (P := P) 0).integral_eq
  filter_upwards [hroute] with sequence hseq
  simpa [A, μ, hmean] using hseq

/--
Durrett 2019, Example 4.7.4 product-space backwards-martingale route with the
tail zero-one side stated on the VdVW permutation-symmetric tail.  V298
transports that zero-one theorem to Durrett's reverse-average tail, then V297
supplies the backwards Levy endpoint.
-/
theorem durrett2019_example_4_7_4_eval_prefixAverage_ae_tendsto_of_integrable_id_and_permutationSymmetric_tail_zero_or_one
    {P : Measure ℝ} [IsProbabilityMeasure P] (hid : Integrable id P)
    (hzeroOne :
      ∀ B : Set (ℕ -> ℝ),
        MeasurableSet[⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n] B ->
          vdVWInfiniteProductMeasure P B = 0 ∨ vdVWInfiniteProductMeasure P B = 1) :
    ∀ᵐ sequence ∂(vdVWInfiniteProductMeasure P),
      Tendsto
        (fun n : ℕ => (∑ i ∈ Finset.range n, sequence i) / (n : ℝ))
        atTop
        (𝓝 (∫ x : ℝ, x ∂P)) := by
  exact
    durrett2019_example_4_7_4_eval_prefixAverage_ae_tendsto_of_integrable_id_and_tail_zero_or_one
      (P := P) hid
      (durrett2019_example_4_7_4_eval_reverseAverage_tail_zero_or_one_of_permutationSymmetric_tail
        (P := P) hzeroOne)

/--
Durrett 2019, Example 4.7.4 product-space backwards-martingale route with the
Hewitt-Savage side reduced to self-independence of the VdVW
permutation-symmetric tail.
-/
theorem durrett2019_example_4_7_4_eval_prefixAverage_ae_tendsto_of_integrable_id_and_permutationSymmetric_tail_indep_self
    {P : Measure ℝ} [IsProbabilityMeasure P] (hid : Integrable id P)
    (hindep :
      Indep
        (⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n)
        (⨅ n : ℕ, vdVWPermutationSymmetricMeasurableSpace ℝ n)
        (vdVWInfiniteProductMeasure P)) :
    ∀ᵐ sequence ∂(vdVWInfiniteProductMeasure P),
      Tendsto
        (fun n : ℕ => (∑ i ∈ Finset.range n, sequence i) / (n : ℝ))
        atTop
        (𝓝 (∫ x : ℝ, x ∂P)) := by
  exact
    durrett2019_example_4_7_4_eval_prefixAverage_ae_tendsto_of_integrable_id_and_permutationSymmetric_tail_zero_or_one
      (P := P) hid
      (durrett2019_example_4_7_4_eval_permutationSymmetricTail_zero_or_one_of_indep_self
        (P := P) hindep)

/--
Durrett 2019, Example 4.7.4, final strong-law endpoint using the compiled
local strong-law primitive.
-/
theorem durrett2019_example_4_7_4_strongLaw_ae_real
    {Ω : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    (ξ : ℕ -> Ω -> ℝ)
    (hint : Integrable (ξ 0) P)
    (hindep : Pairwise ((· ⟂ᵢ[P] ·) on ξ))
    (hident : ∀ i, _root_.ProbabilityTheory.IdentDistrib (ξ i) (ξ 0) P P) :
    ∀ᵐ ω ∂P,
      Tendsto
        (fun n : ℕ => (∑ i ∈ Finset.range n, ξ i ω) / n)
        atTop
        (𝓝 (∫ ω, ξ 0 ω ∂P)) := by
  exact StatInference.ProbabilityMeasure.strongLaw_ae_real ξ hint hindep hident

/--
Durrett 2019, Example 4.7.4 product-space strong-law endpoint for the
coordinate-evaluation process.  The source moment assumption is integrability
of the identity under the one-dimensional law.
-/
theorem durrett2019_example_4_7_4_eval_strongLaw_ae_real_of_integrable_id
    {P : Measure ℝ} [IsProbabilityMeasure P] (hid : Integrable id P) :
    ∀ᵐ sequence ∂(vdVWInfiniteProductMeasure P),
      Tendsto
        (fun n : ℕ => (∑ i ∈ Finset.range n, sequence i) / (n : ℝ))
        atTop
        (𝓝 (∫ x : ℝ, x ∂P)) := by
  have h0_int :
      Integrable (fun sequence : ℕ -> ℝ => sequence 0)
        (vdVWInfiniteProductMeasure P) :=
    durrett2019_example_4_7_4_eval_integrable_of_integrable_id
      (P := P) hid 0
  have hindep :
      Pairwise
        ((· ⟂ᵢ[vdVWInfiniteProductMeasure P] ·) on
          (fun i => fun sequence : ℕ -> ℝ => sequence i)) := by
    intro i j hij
    exact (vdVWInfiniteProductMeasure_iIndepFun_coordinates
      (P := P)).indepFun hij
  have hident :
      ∀ i,
        _root_.ProbabilityTheory.IdentDistrib
          (fun sequence : ℕ -> ℝ => sequence i)
          (fun sequence : ℕ -> ℝ => sequence 0)
          (vdVWInfiniteProductMeasure P) (vdVWInfiniteProductMeasure P) := by
    intro i
    exact
      (vdVWInfiniteProductMeasure_coordinate_hasLaw (P := P) i).identDistrib
        (vdVWInfiniteProductMeasure_coordinate_hasLaw (P := P) 0)
  have hsl :=
    durrett2019_example_4_7_4_strongLaw_ae_real
      (P := vdVWInfiniteProductMeasure P)
      (ξ := fun i sequence => sequence i)
      h0_int hindep hident
  have hmean :
      (∫ sequence, sequence 0 ∂(vdVWInfiniteProductMeasure P)) =
        ∫ x : ℝ, x ∂P := by
    simpa [id] using
      (vdVWInfiniteProductMeasure_coordinate_hasLaw (P := P) 0).integral_eq
  filter_upwards [hsl] with sequence hseq
  simpa [hmean] using hseq

end ProbabilityTheory
end StatInference
