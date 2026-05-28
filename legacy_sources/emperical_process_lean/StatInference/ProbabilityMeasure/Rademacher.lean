import Mathlib.Probability.HasLawExists
import Mathlib.Probability.IdentDistrib
import Mathlib.Probability.Moments.SubGaussian
import Mathlib.Probability.ProbabilityMassFunction.Integrals

/-!
# Rademacher-sign probability wrappers

This module records reusable probability/measure primitives for iid
Rademacher signs.  The immediate downstream consumer is the empirical-process
symmetrization lane for VdV&W Theorem 2.4.3, but the declarations live under
the content-based Billingsley/ProbabilityMeasure folder because they are basic
probability infrastructure.

These are compiled local wrappers, not yet source-audited exact Billingsley
theorem reports.
-/

namespace StatInference
namespace ProbabilityMeasure

open MeasureTheory ProbabilityTheory

open scoped ENNReal NNReal

universe u

/-- The fair Bernoulli PMF used to generate textbook Rademacher signs. -/
noncomputable def rademacherBoolPMF : PMF Bool :=
  PMF.bernoulli (1 / 2 : ℝ≥0) (by norm_num)

/-- The Bool-to-real sign map sending the Bernoulli outcome to `±1`. -/
def boolToRademacherSign (b : Bool) : ℝ :=
  cond b (1 : ℝ) (-1)

/-- The probability law of the fair Bernoulli source for Rademacher signs. -/
noncomputable def rademacherBoolLaw : Measure Bool :=
  rademacherBoolPMF.toMeasure

instance : IsProbabilityMeasure rademacherBoolLaw := by
  unfold rademacherBoolLaw rademacherBoolPMF
  infer_instance

/-- The Bool-to-real Rademacher sign map is measurable. -/
theorem measurable_boolToRademacherSign :
    Measurable boolToRademacherSign := by
  fun_prop

/-- The Bool-to-real Rademacher sign has support contained in `{−1, 1}`. -/
theorem boolToRademacherSign_eq_neg_one_or_one (b : Bool) :
    boolToRademacherSign b = -1 ∨ boolToRademacherSign b = 1 := by
  cases b <;> simp [boolToRademacherSign]

/-- The Bool-to-real Rademacher sign is bounded by one in absolute value. -/
theorem abs_boolToRademacherSign_le_one (b : Bool) :
    |boolToRademacherSign b| ≤ 1 := by
  rcases boolToRademacherSign_eq_neg_one_or_one b with hneg | hpos
  · simp [hneg]
  · simp [hpos]

/-- The square of a Bool-to-real Rademacher sign is one. -/
theorem boolToRademacherSign_sq (b : Bool) :
    boolToRademacherSign b ^ 2 = 1 := by
  rcases boolToRademacherSign_eq_neg_one_or_one b with hneg | hpos
  · simp [hneg]
  · simp [hpos]

/-- The fair Bool-to-real Rademacher sign has mean zero. -/
theorem integral_boolToRademacherSign_eq_zero :
    ∫ b, boolToRademacherSign b ∂rademacherBoolLaw = 0 := by
  unfold rademacherBoolLaw
  rw [PMF.integral_eq_sum]
  norm_num [rademacherBoolPMF, boolToRademacherSign, PMF.bernoulli_apply]

/-- The fair Bool-to-real Rademacher sign has second moment one. -/
theorem integral_boolToRademacherSign_sq_eq_one :
    ∫ b, boolToRademacherSign b ^ 2 ∂rademacherBoolLaw = 1 := by
  unfold rademacherBoolLaw
  rw [PMF.integral_eq_sum]
  norm_num [rademacherBoolPMF, boolToRademacherSign, PMF.bernoulli_apply]

/-- The pushed-forward real-valued Rademacher PMF on `{−1, 1}`. -/
noncomputable def rademacherPMF : PMF ℝ :=
  PMF.map boolToRademacherSign rademacherBoolPMF

/-- The real-valued Rademacher probability law on `{−1, 1}`. -/
noncomputable def rademacherLaw : Measure ℝ :=
  rademacherPMF.toMeasure

instance : IsProbabilityMeasure rademacherLaw := by
  unfold rademacherLaw rademacherPMF
  infer_instance

/-- The Bool-to-real sign map has the real-valued Rademacher law. -/
theorem boolToRademacherSign_hasLaw :
    HasLaw boolToRademacherSign rademacherLaw rademacherBoolLaw := by
  refine ⟨measurable_boolToRademacherSign.aemeasurable, ?_⟩
  exact PMF.toMeasure_map (p := rademacherBoolPMF)
    (f := boolToRademacherSign) measurable_boolToRademacherSign

/-- The identity under the real Rademacher law has mean zero. -/
theorem integral_id_rademacherLaw_eq_zero :
    ∫ x, x ∂rademacherLaw = 0 := by
  rw [← boolToRademacherSign_hasLaw.integral_eq]
  exact integral_boolToRademacherSign_eq_zero

/-- The identity under the real Rademacher law has second moment one. -/
theorem integral_id_sq_rademacherLaw_eq_one :
    ∫ x, x ^ 2 ∂rademacherLaw = 1 := by
  have h :=
    boolToRademacherSign_hasLaw.integral_comp
      (f := fun x : ℝ => x ^ 2) (by fun_prop)
  rw [← h]
  exact integral_boolToRademacherSign_sq_eq_one

/-- The canonical fair Bool-to-real Rademacher sign is sub-Gaussian. -/
theorem boolToRademacherSign_hasSubgaussianMGF :
    HasSubgaussianMGF boolToRademacherSign 1 rademacherBoolLaw := by
  have hmeas : AEMeasurable boolToRademacherSign rademacherBoolLaw :=
    measurable_boolToRademacherSign.aemeasurable
  have hbound : ∀ᵐ b ∂rademacherBoolLaw,
      boolToRademacherSign b ∈ Set.Icc (-1 : ℝ) 1 := by
    exact ae_of_all _ (fun b => by
      cases b <;> simp [boolToRademacherSign])
  have hzero : ∫ b, boolToRademacherSign b ∂rademacherBoolLaw = 0 :=
    integral_boolToRademacherSign_eq_zero
  have h := hasSubgaussianMGF_of_mem_Icc_of_integral_eq_zero
    (X := boolToRademacherSign) (μ := rademacherBoolLaw)
    (a := (-1 : ℝ)) (b := 1) hmeas hbound hzero
  convert h using 1
  norm_num

/-- The identity map under the real-valued Rademacher law is sub-Gaussian. -/
theorem id_rademacherLaw_hasSubgaussianMGF :
    HasSubgaussianMGF id 1 rademacherLaw := by
  exact boolToRademacherSign_hasSubgaussianMGF.congr_identDistrib
    (boolToRademacherSign_hasLaw.identDistrib HasLaw.id)

/-- The canonical Bool-to-real Rademacher sign is in `L^2`. -/
theorem boolToRademacherSign_memLp_two :
    MemLp boolToRademacherSign (2 : ℝ≥0∞) rademacherBoolLaw := by
  simp

/-- The identity under the real Rademacher law is in `L^2`. -/
theorem id_rademacherLaw_memLp_two :
    MemLp id (2 : ℝ≥0∞) rademacherLaw := by
  exact id_rademacherLaw_hasSubgaussianMGF.memLp (2 : ℝ≥0)

/-- A random variable with the real Rademacher law has mean zero. -/
theorem hasLaw_rademacher_integral_eq_zero
    {Ω : Type*} [MeasurableSpace Ω] {P : Measure Ω} {X : Ω -> ℝ}
    (hX : HasLaw X rademacherLaw P) :
    ∫ ω, X ω ∂P = 0 := by
  rw [hX.integral_eq, integral_id_rademacherLaw_eq_zero]

/-- A random variable with the real Rademacher law has second moment one. -/
theorem hasLaw_rademacher_integral_sq_eq_one
    {Ω : Type*} [MeasurableSpace Ω] {P : Measure Ω} {X : Ω -> ℝ}
    (hX : HasLaw X rademacherLaw P) :
    ∫ ω, X ω ^ 2 ∂P = 1 := by
  have h :=
    hX.integral_comp (f := fun x : ℝ => x ^ 2) (by fun_prop)
  change ∫ ω, ((fun x : ℝ => x ^ 2) ∘ X) ω ∂P = 1
  rw [h, integral_id_sq_rademacherLaw_eq_one]

/-- A random variable with the real Rademacher law is in `L^2`. -/
theorem hasLaw_rademacher_memLp_two
    {Ω : Type*} [MeasurableSpace Ω] {P : Measure Ω} {X : Ω -> ℝ}
    (hX : HasLaw X rademacherLaw P) :
    MemLp X (2 : ℝ≥0∞) P := by
  have hid_map : MemLp id (2 : ℝ≥0∞) (Measure.map X P) := by
    simpa [hX.map_eq] using id_rademacherLaw_memLp_two
  have hcomp :
      MemLp (id ∘ X) (2 : ℝ≥0∞) P :=
    (memLp_map_measure_iff aestronglyMeasurable_id hX.aemeasurable).1 hid_map
  simpa [Function.comp_def] using hcomp

/-! ## Canonical infinite iid Rademacher sequence -/

/-- The canonical infinite product law of fair Bool Rademacher sources. -/
noncomputable def rademacherBoolSequenceLaw : Measure (ℕ -> Bool) :=
  Measure.infinitePi fun _ : ℕ => rademacherBoolLaw

instance : IsProbabilityMeasure rademacherBoolSequenceLaw := by
  unfold rademacherBoolSequenceLaw
  infer_instance

/-- The real-valued Rademacher coordinate on the canonical Bool product space. -/
def rademacherSequenceCoordinate (n : ℕ) (ω : ℕ -> Bool) : ℝ :=
  boolToRademacherSign (ω n)

/-- Canonical infinite-product Rademacher coordinates are measurable. -/
theorem measurable_rademacherSequenceCoordinate (n : ℕ) :
    Measurable (rademacherSequenceCoordinate n) := by
  exact measurable_boolToRademacherSign.comp (measurable_pi_apply n)

/-- Canonical infinite-product Rademacher coordinates are strongly measurable. -/
theorem stronglyMeasurable_rademacherSequenceCoordinate (n : ℕ) :
    StronglyMeasurable (rademacherSequenceCoordinate n) :=
  (measurable_rademacherSequenceCoordinate n).stronglyMeasurable

/-- Each canonical infinite-product Rademacher coordinate has Rademacher law. -/
theorem rademacherSequenceCoordinate_hasLaw (n : ℕ) :
    HasLaw (rademacherSequenceCoordinate n) rademacherLaw
      rademacherBoolSequenceLaw := by
  have hbool :
      HasLaw (fun ω : ℕ -> Bool => ω n) rademacherBoolLaw
        rademacherBoolSequenceLaw := by
    simpa [rademacherBoolSequenceLaw] using
      (measurePreserving_eval_infinitePi
        (μ := fun _ : ℕ => rademacherBoolLaw) n).hasLaw
  simpa [rademacherSequenceCoordinate, Function.comp_def] using
    boolToRademacherSign_hasLaw.comp hbool

/-- The canonical infinite-product Rademacher coordinates are independent. -/
theorem rademacherSequenceCoordinate_iIndepFun :
    iIndepFun rademacherSequenceCoordinate rademacherBoolSequenceLaw := by
  have hbool_indep :
      iIndepFun (fun n (ω : ℕ -> Bool) => ω n)
        rademacherBoolSequenceLaw := by
    simpa [rademacherBoolSequenceLaw] using
      (iIndepFun_infinitePi
        (P := fun _ : ℕ => rademacherBoolLaw)
        (X := fun _ (b : Bool) => b)
        (fun _ => measurable_id))
  simpa [rademacherSequenceCoordinate, Function.comp_def] using
    hbool_indep.comp (fun _ => boolToRademacherSign)
      (fun _ => measurable_boolToRademacherSign)

/-- Canonical infinite-product Rademacher coordinates are sub-Gaussian. -/
theorem rademacherSequenceCoordinate_hasSubgaussianMGF (n : ℕ) :
    HasSubgaussianMGF (rademacherSequenceCoordinate n) 1
      rademacherBoolSequenceLaw := by
  have hident :
      IdentDistrib boolToRademacherSign (rademacherSequenceCoordinate n)
        rademacherBoolLaw rademacherBoolSequenceLaw :=
    boolToRademacherSign_hasLaw.identDistrib
      (rademacherSequenceCoordinate_hasLaw n)
  exact boolToRademacherSign_hasSubgaussianMGF.congr_identDistrib hident

/--
Canonical infinite iid real-valued Rademacher signs on the Bool product space.

This packages the concrete sample space used by simple random-walk statements.
-/
theorem canonical_iid_rademacherSequence :
    (∀ n, Measurable (rademacherSequenceCoordinate n)) ∧
      (∀ n, HasLaw (rademacherSequenceCoordinate n) rademacherLaw
        rademacherBoolSequenceLaw) ∧
      iIndepFun rademacherSequenceCoordinate rademacherBoolSequenceLaw ∧
      IsProbabilityMeasure rademacherBoolSequenceLaw ∧
      (∀ n, HasSubgaussianMGF (rademacherSequenceCoordinate n) 1
        rademacherBoolSequenceLaw) := by
  exact
    ⟨measurable_rademacherSequenceCoordinate,
      rademacherSequenceCoordinate_hasLaw,
      rademacherSequenceCoordinate_iIndepFun,
      inferInstance,
      rademacherSequenceCoordinate_hasSubgaussianMGF⟩

/-- A deterministic sign vector supported on `{-1, 1}`. -/
def RademacherSignVector {n : ℕ} (sign : Fin n -> ℝ) : Prop :=
  ∀ i, sign i = -1 ∨ sign i = 1

/-- Rademacher sign vectors are uniformly bounded by one in absolute value. -/
theorem RademacherSignVector.abs_le_one
    {n : ℕ} {sign : Fin n -> ℝ}
    (hsign : RademacherSignVector sign) :
    ∀ i, |sign i| ≤ 1 := by
  intro i
  rcases hsign i with hneg | hpos
  · simp [hneg]
  · simp [hpos]

/--
Existence of finitely many iid real-valued Rademacher signs.

This is the reusable probability-space construction needed for
symmetrization: mathlib supplies iid Bool variables, and this wrapper pushes
them through `boolToRademacherSign`.
-/
theorem exists_iid_rademacherSigns (n : ℕ) :
    ∃ Ω : Type, ∃ _ : MeasurableSpace Ω, ∃ P : Measure Ω,
      ∃ sign : Fin n -> Ω -> ℝ,
        (∀ i, Measurable (sign i)) ∧
        (∀ i, HasLaw (sign i) rademacherLaw P) ∧
        iIndepFun sign P ∧ IsProbabilityMeasure P ∧
        (∀ i, HasSubgaussianMGF (sign i) 1 P) ∧
        (∀ᵐ ω ∂P, RademacherSignVector (fun i => sign i ω)) := by
  obtain ⟨Ω, mΩ, P, boolSign, hmeas, hlaw, hindep, hprob⟩ :=
    ProbabilityTheory.exists_iid (Fin n) rademacherBoolLaw
  letI : MeasurableSpace Ω := mΩ
  let sign : Fin n -> Ω -> ℝ :=
    fun i => boolToRademacherSign ∘ boolSign i
  refine ⟨Ω, mΩ, P, sign, ?_, ?_, ?_, hprob, ?_, ?_⟩
  · intro i
    exact measurable_boolToRademacherSign.comp (hmeas i)
  · intro i
    exact boolToRademacherSign_hasLaw.comp (hlaw i)
  · exact hindep.comp (fun _ => boolToRademacherSign)
      (fun _ => measurable_boolToRademacherSign)
  · intro i
    have hident :
        IdentDistrib boolToRademacherSign (sign i) rademacherBoolLaw P :=
      boolToRademacherSign_hasLaw.identDistrib
        (boolToRademacherSign_hasLaw.comp (hlaw i))
    exact boolToRademacherSign_hasSubgaussianMGF.congr_identDistrib hident
  · exact ae_of_all _ (fun ω i =>
      boolToRademacherSign_eq_neg_one_or_one (boolSign i ω))

end ProbabilityMeasure
end StatInference
