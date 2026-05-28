import Mathlib.MeasureTheory.Integral.Prod
import Mathlib.MeasureTheory.Integral.Pi
import Mathlib.MeasureTheory.Measure.FiniteMeasureProd
import Mathlib.Probability.HasLaw
import Mathlib.Probability.Independence.Integration

/-!
# Product-measure and Fubini wrappers

This module records a content-based product-measure layer for textbook
probability/measure work.  The immediate downstream use is empirical-process
symmetrization and finite independent-copy arguments, so the wrappers stay close
to pinned mathlib APIs instead of developing a broader product-space theory.
-/

namespace StatInference
namespace ProbabilityMeasure

open MeasureTheory ProbabilityTheory

open scoped BigOperators ENNReal MeasureTheory

universe u v w

/-- Product probability measures evaluated on a measurable set. -/
theorem probability_prod_apply
    {α : Type u} [MeasurableSpace α] {β : Type v} [MeasurableSpace β]
    (μ : MeasureTheory.ProbabilityMeasure α)
    (ν : MeasureTheory.ProbabilityMeasure β)
    (s : Set (α × β)) (hs : MeasurableSet s) :
    μ.prod ν s =
      ENNReal.toNNReal (∫⁻ x, ν.toMeasure (Prod.mk x ⁻¹' s) ∂(μ : Measure α)) := by
  exact MeasureTheory.ProbabilityMeasure.prod_apply μ ν s hs

/-- Product probability measures on measurable rectangles. -/
theorem probability_prod_prod
    {α : Type u} [MeasurableSpace α] {β : Type v} [MeasurableSpace β]
    (μ : MeasureTheory.ProbabilityMeasure α)
    (ν : MeasureTheory.ProbabilityMeasure β)
    (s : Set α) (t : Set β) :
    μ.prod ν (s ×ˢ t) = μ s * ν t := by
  exact MeasureTheory.ProbabilityMeasure.prod_prod μ ν s t

/-- Mapping both coordinates commutes with taking product probability measures. -/
theorem probability_map_prod_map
    {α : Type u} [MeasurableSpace α] {β : Type v} [MeasurableSpace β]
    {α' : Type w} [MeasurableSpace α'] {β' : Type*} [MeasurableSpace β']
    (μ : MeasureTheory.ProbabilityMeasure α)
    (ν : MeasureTheory.ProbabilityMeasure β)
    {f : α -> α'} {g : β -> β'}
    (hf : Measurable f) (hg : Measurable g) :
    (μ.map hf.aemeasurable).prod (ν.map hg.aemeasurable)
      = (μ.prod ν).map (hf.prodMap hg).aemeasurable := by
  exact MeasureTheory.ProbabilityMeasure.map_prod_map μ ν hf hg

/--
The two coordinates on `P × P` are independent copies with common law `P`.

This is the product-space handoff used by symmetrization arguments: instead of
constructing an abstract ghost sample, one can work on the binary product
probability space and use the coordinate projections.
-/
theorem probability_prod_independent_self_copies
    {α : Type u} [MeasurableSpace α]
    (P : MeasureTheory.ProbabilityMeasure α) :
    HasLaw (fun z : α × α => z.1) (P : Measure α)
        ((P : Measure α).prod (P : Measure α)) ∧
      HasLaw (fun z : α × α => z.2) (P : Measure α)
        ((P : Measure α).prod (P : Measure α)) ∧
      (fun z : α × α => z.1) ⟂ᵢ[((P : Measure α).prod (P : Measure α))]
        (fun z : α × α => z.2) := by
  refine ⟨?_, ?_, ?_⟩
  · exact MeasureTheory.measurePreserving_fst.hasLaw
  · exact MeasureTheory.measurePreserving_snd.hasLaw
  · simpa using
      (ProbabilityTheory.indepFun_prod
        (μ := (P : Measure α)) (ν := (P : Measure α))
        (X := id) (Y := id) measurable_id measurable_id)

/--
Measurable functions of the two product coordinates are independent, with
their marginal laws and joint product law.

This is the reusable Billingsley Section 18 / empirical-process symmetrization
handoff for replacing abstract independent copies by concrete product-space
coordinates and then mapping those coordinates through measurable statistics.
-/
theorem probability_prod_independent_mapped_copies_with_joint_law
    {α : Type u} [MeasurableSpace α]
    {β : Type v} [MeasurableSpace β]
    {γ : Type w} [MeasurableSpace γ]
    {δ : Type*} [MeasurableSpace δ]
    (P : MeasureTheory.ProbabilityMeasure α)
    (Q : MeasureTheory.ProbabilityMeasure β)
    {X : α -> γ} {Y : β -> δ}
    (hX : Measurable X) (hY : Measurable Y) :
    HasLaw (fun z : α × β => X z.1) ((P : Measure α).map X)
        ((P : Measure α).prod (Q : Measure β)) ∧
      HasLaw (fun z : α × β => Y z.2) ((Q : Measure β).map Y)
        ((P : Measure α).prod (Q : Measure β)) ∧
      HasLaw (fun z : α × β => (X z.1, Y z.2))
        (((P : Measure α).map X).prod ((Q : Measure β).map Y))
        ((P : Measure α).prod (Q : Measure β)) ∧
      (fun z : α × β => X z.1) ⟂ᵢ[((P : Measure α).prod (Q : Measure β))]
        (fun z : α × β => Y z.2) := by
  let hXLaw : HasLaw (fun z : α × β => X z.1) ((P : Measure α).map X)
      ((P : Measure α).prod (Q : Measure β)) :=
    HasLaw.comp (Y := X) (ν := (P : Measure α).map X)
      ⟨hX.aemeasurable, rfl⟩ MeasureTheory.measurePreserving_fst.hasLaw
  let hYLaw : HasLaw (fun z : α × β => Y z.2) ((Q : Measure β).map Y)
      ((P : Measure α).prod (Q : Measure β)) :=
    HasLaw.comp (Y := Y) (ν := (Q : Measure β).map Y)
      ⟨hY.aemeasurable, rfl⟩ MeasureTheory.measurePreserving_snd.hasLaw
  let hInd :
      (fun z : α × β => X z.1) ⟂ᵢ[((P : Measure α).prod (Q : Measure β))]
        (fun z : α × β => Y z.2) :=
    ProbabilityTheory.indepFun_prod
      (μ := (P : Measure α)) (ν := (Q : Measure β))
      (X := X) (Y := Y) hX hY
  exact ⟨hXLaw, hYLaw, hInd.hasLaw_prod hXLaw hYLaw, hInd⟩

/--
Mapping every coordinate of a finite product probability measure commutes with
taking the finite product.
-/
theorem probability_pi_map_mapped_coordinates_eq
    {ι : Type w} [Fintype ι]
    {α : ι -> Type u} [∀ i, MeasurableSpace (α i)]
    {β : ι -> Type v} [∀ i, MeasurableSpace (β i)]
    (P : (i : ι) -> MeasureTheory.ProbabilityMeasure (α i))
    {X : (i : ι) -> α i -> β i}
    (hX : ∀ i, Measurable (X i)) :
    (Measure.pi fun i => (P i : Measure (α i))).map
        (fun sample : (j : ι) -> α j => fun i => X i (sample i)) =
      Measure.pi fun i => ((P i : Measure (α i)).map (X i)) := by
  exact Measure.pi_map_pi (fun i => (hX i).aemeasurable)

/--
Finite-product coordinate maps are independent, with their coordinate laws and
joint product law.

This is the finite-`Pi` version of the mapped-coordinate product-copy handoff.
It is the reusable support layer for iid sample spaces such as
`SampleAt Observation n = Fin n -> Observation`.
-/
theorem probability_pi_independent_mapped_coordinates_with_joint_law
    {ι : Type w} [Fintype ι]
    {α : ι -> Type u} [∀ i, MeasurableSpace (α i)]
    {β : ι -> Type v} [∀ i, MeasurableSpace (β i)]
    (P : (i : ι) -> MeasureTheory.ProbabilityMeasure (α i))
    {X : (i : ι) -> α i -> β i}
    (hX : ∀ i, Measurable (X i)) :
    (∀ i,
      HasLaw (fun sample : (∀ i, α i) => X i (sample i))
        (((P i : Measure (α i)).map (X i)))
        (Measure.pi fun i => (P i : Measure (α i)))) ∧
      iIndepFun (fun i => fun sample : (∀ i, α i) => X i (sample i))
        (Measure.pi fun i => (P i : Measure (α i))) ∧
      HasLaw (fun sample : (∀ i, α i) => fun i => X i (sample i))
        (Measure.pi fun i => ((P i : Measure (α i)).map (X i)))
        (Measure.pi fun i => (P i : Measure (α i))) := by
  let μ : (i : ι) -> Measure (α i) := fun i => (P i : Measure (α i))
  have hcoordLaw : ∀ i,
      HasLaw (fun sample : (∀ i, α i) => X i (sample i))
        ((μ i).map (X i)) (Measure.pi μ) := by
    intro i
    exact HasLaw.comp (Y := X i) (ν := (μ i).map (X i))
      ⟨(hX i).aemeasurable, rfl⟩ (MeasureTheory.measurePreserving_eval μ i).hasLaw
  have hind :
      iIndepFun (fun i => fun sample : (∀ i, α i) => X i (sample i))
        (Measure.pi μ) := by
    exact ProbabilityTheory.iIndepFun_pi
      (μ := μ) (X := X) (fun i => (hX i).aemeasurable)
  have hjoint :
      HasLaw (fun sample : (∀ i, α i) => fun i => X i (sample i))
        (Measure.pi fun i => (μ i).map (X i)) (Measure.pi μ) :=
    hind.hasLaw_pi hcoordLaw
  exact ⟨by simpa [μ] using hcoordLaw, by simpa [μ] using hind,
    by simpa [μ] using hjoint⟩

/--
Canonical iid finite-product coordinates.

On the product probability space `∏ i, ν`, the coordinate projections are
independent, all have law `ν`, and the full coordinate vector has joint law
`∏ i, ν`.
-/
theorem probability_pi_iid_coordinates_with_joint_law
    {ι : Type w} [Fintype ι]
    {S : Type u} [MeasurableSpace S]
    (ν : MeasureTheory.ProbabilityMeasure S) :
    (∀ i,
      HasLaw (fun sample : (ι -> S) => sample i) (ν : Measure S)
        (Measure.pi fun _ : ι => (ν : Measure S))) ∧
      iIndepFun (fun i => fun sample : (ι -> S) => sample i)
        (Measure.pi fun _ : ι => (ν : Measure S)) ∧
      HasLaw (fun sample : (ι -> S) => sample)
        (Measure.pi fun _ : ι => (ν : Measure S))
        (Measure.pi fun _ : ι => (ν : Measure S)) := by
  let P : ι -> MeasureTheory.ProbabilityMeasure S := fun _ => ν
  have h :=
    probability_pi_independent_mapped_coordinates_with_joint_law
      (P := P) (X := fun _ => id) (fun _ => measurable_id)
  refine ⟨?_, ?_, ?_⟩
  · intro i
    simpa [P] using h.1 i
  · simpa [P] using h.2.1
  · simpa [P] using h.2.2

/--
Splitting every coordinate of a finite product of binary product probability
spaces sends `∏ i (Pᵢ × Qᵢ)` to `(∏ i Pᵢ) × (∏ i Qᵢ)`.

This is the finite-product projection wrapper needed when an
independent-copy argument moves between a sample of product-coordinate pairs
and a pair of independent samples.
-/
theorem probability_pi_prod_coordinates_measurePreserving
    {ι : Type w} [Fintype ι]
    {α : Type u} [MeasurableSpace α]
    {β : Type v} [MeasurableSpace β]
    (P : ι -> MeasureTheory.ProbabilityMeasure α)
    (Q : ι -> MeasureTheory.ProbabilityMeasure β) :
    MeasurePreserving
      (fun sample : ι -> α × β =>
        (fun i : ι => (sample i).1, fun i : ι => (sample i).2))
      (Measure.pi fun i : ι => ((P i : Measure α).prod (Q i : Measure β)))
      ((Measure.pi fun i : ι => (P i : Measure α)).prod
        (Measure.pi fun i : ι => (Q i : Measure β))) := by
  simpa [MeasurableEquiv.arrowProdEquivProdArrow] using
    (MeasureTheory.measurePreserving_arrowProdEquivProdArrow
      α β ι
      (fun i : ι => (P i : Measure α))
      (fun i : ι => (Q i : Measure β)))

/--
Finite-product expectation of a weighted coordinatewise sum.

This is the reusable finite-`Pi` Fubini bridge used when a symmetrization
argument integrates empirical sums over an independent product sample.
-/
theorem probability_pi_integral_weighted_sum
    {ι : Type w} [Fintype ι]
    {α : ι -> Type u} [∀ i, MeasurableSpace (α i)]
    (P : (i : ι) -> MeasureTheory.ProbabilityMeasure (α i))
    {f : (i : ι) -> α i -> ℝ} {weights : ι -> ℝ}
    (hf : ∀ i, Integrable (f i) (P i : Measure (α i))) :
    ∫ sample : (i : ι) -> α i,
        (∑ i : ι, weights i * f i (sample i))
          ∂(Measure.pi fun i => (P i : Measure (α i))) =
      ∑ i : ι, weights i * ∫ x, f i x ∂(P i : Measure (α i)) := by
  let μ : (i : ι) -> Measure (α i) := fun i => (P i : Measure (α i))
  have hterm :
      ∀ i ∈ (Finset.univ : Finset ι),
        Integrable
          (fun sample : (j : ι) -> α j => weights i * f i (sample i))
          (Measure.pi μ) := by
    intro i _hi
    have hcomp :
        Integrable (fun sample : (j : ι) -> α j => f i (sample i))
          (Measure.pi μ) := by
      simpa [Function.comp_def, μ] using
        (MeasureTheory.integrable_comp_eval (μ := μ) (i := i) (hf i))
    exact hcomp.const_mul (weights i)
  calc
    ∫ sample : (i : ι) -> α i,
        (∑ i : ι, weights i * f i (sample i)) ∂(Measure.pi μ)
        = ∑ i : ι,
            ∫ sample : (j : ι) -> α j,
              weights i * f i (sample i) ∂(Measure.pi μ) := by
          simpa using
            (integral_finsetSum (μ := Measure.pi μ)
              (s := Finset.univ)
              (f := fun i sample => weights i * f i (sample i)) hterm)
    _ = ∑ i : ι, weights i * ∫ x, f i x ∂(P i : Measure (α i)) := by
          refine Finset.sum_congr rfl ?_
          intro i _hi
          calc
            ∫ sample : (j : ι) -> α j,
                weights i * f i (sample i) ∂(Measure.pi μ)
                = weights i *
                    ∫ sample : (j : ι) -> α j,
                      f i (sample i) ∂(Measure.pi μ) := by
                  rw [integral_const_mul]
            _ = weights i * ∫ x, f i x ∂(P i : Measure (α i)) := by
                  rw [MeasureTheory.integral_comp_eval
                    (μ := μ) (i := i) (hf i).aestronglyMeasurable]

/--
Finite-product expectation of a weighted ghost-copy difference with the first
sample held fixed.

This is the conditional finite-`Pi` Fubini identity used in symmetrization:
integrating only over the ghost sample replaces each ghost coordinate by its
mean while leaving the fixed coordinate value untouched.
-/
theorem probability_pi_integral_weighted_sum_const_sub
    {ι : Type w} [Fintype ι]
    {α : ι -> Type u} [∀ i, MeasurableSpace (α i)]
    (P : (i : ι) -> MeasureTheory.ProbabilityMeasure (α i))
    {f : (i : ι) -> α i -> ℝ} {weights : ι -> ℝ}
    (fixedSample : (i : ι) -> α i)
    (hf : ∀ i, Integrable (f i) (P i : Measure (α i))) :
    ∫ ghostSample : (i : ι) -> α i,
        (∑ i : ι, weights i * (f i (fixedSample i) - f i (ghostSample i)))
          ∂(Measure.pi fun i => (P i : Measure (α i))) =
      ∑ i : ι,
        weights i * (f i (fixedSample i) - ∫ x, f i x ∂(P i : Measure (α i))) := by
  let g : (i : ι) -> α i -> ℝ :=
    fun i x => f i (fixedSample i) - f i x
  have hg : ∀ i, Integrable (g i) (P i : Measure (α i)) := by
    intro i
    exact (integrable_const (f i (fixedSample i))).sub (hf i)
  rw [probability_pi_integral_weighted_sum P (f := g) (weights := weights) hg]
  refine Finset.sum_congr rfl ?_
  intro i _hi
  congr 1
  unfold g
  rw [integral_sub (integrable_const (f i (fixedSample i))) (hf i)]
  simp

/--
Finite-product weighted sums have mean zero when every coordinate summand has
mean zero.
-/
theorem probability_pi_integral_weighted_sum_eq_zero
    {ι : Type w} [Fintype ι]
    {α : ι -> Type u} [∀ i, MeasurableSpace (α i)]
    (P : (i : ι) -> MeasureTheory.ProbabilityMeasure (α i))
    {f : (i : ι) -> α i -> ℝ} {weights : ι -> ℝ}
    (hf : ∀ i, Integrable (f i) (P i : Measure (α i)))
    (hzero : ∀ i, ∫ x, f i x ∂(P i : Measure (α i)) = 0) :
    ∫ sample : (i : ι) -> α i,
        (∑ i : ι, weights i * f i (sample i))
          ∂(Measure.pi fun i => (P i : Measure (α i))) =
      0 := by
  rw [probability_pi_integral_weighted_sum P hf]
  exact Finset.sum_eq_zero fun i _hi => by simp [hzero i]

/-- Tonelli's theorem for an `ℝ≥0∞`-valued function on a product space. -/
theorem lintegral_prod
    {α : Type u} [MeasurableSpace α] {β : Type v} [MeasurableSpace β]
    {μ : Measure α} {ν : Measure β} [SFinite ν]
    {f : α × β -> ℝ≥0∞}
    (hf : AEMeasurable f (μ.prod ν)) :
    ∫⁻ z, f z ∂μ.prod ν = ∫⁻ x, ∫⁻ y, f (x, y) ∂ν ∂μ := by
  exact MeasureTheory.lintegral_prod f hf

/-- Reversed Tonelli theorem for a curried `ℝ≥0∞`-valued function. -/
theorem lintegral_lintegral
    {α : Type u} [MeasurableSpace α] {β : Type v} [MeasurableSpace β]
    {μ : Measure α} {ν : Measure β} [SFinite ν]
    {f : α -> β -> ℝ≥0∞}
    (hf : AEMeasurable (Function.uncurry f) (μ.prod ν)) :
    ∫⁻ x, ∫⁻ y, f x y ∂ν ∂μ = ∫⁻ z, f z.1 z.2 ∂μ.prod ν := by
  exact MeasureTheory.lintegral_lintegral hf

/-- Swap the order of Tonelli integration for a curried nonnegative function. -/
theorem lintegral_lintegral_swap
    {α : Type u} [MeasurableSpace α] {β : Type v} [MeasurableSpace β]
    {μ : Measure α} {ν : Measure β} [SFinite μ] [SFinite ν]
    {f : α -> β -> ℝ≥0∞}
    (hf : AEMeasurable (Function.uncurry f) (μ.prod ν)) :
    ∫⁻ x, ∫⁻ y, f x y ∂ν ∂μ = ∫⁻ y, ∫⁻ x, f x y ∂μ ∂ν := by
  exact MeasureTheory.lintegral_lintegral_swap hf

/-- Fubini's theorem for an integrable Bochner-valued function on a product space. -/
theorem integral_prod
    {α : Type u} [MeasurableSpace α] {β : Type v} [MeasurableSpace β]
    {E : Type w} [NormedAddCommGroup E] [NormedSpace ℝ E]
    {μ : Measure α} {ν : Measure β} [SFinite μ] [SFinite ν]
    (f : α × β -> E) (hf : Integrable f (μ.prod ν)) :
    ∫ z, f z ∂μ.prod ν = ∫ x, ∫ y, f (x, y) ∂ν ∂μ := by
  exact MeasureTheory.integral_prod f hf

/-- Reversed Fubini theorem for an integrable curried function. -/
theorem integral_integral
    {α : Type u} [MeasurableSpace α] {β : Type v} [MeasurableSpace β]
    {E : Type w} [NormedAddCommGroup E] [NormedSpace ℝ E]
    {μ : Measure α} {ν : Measure β} [SFinite μ] [SFinite ν]
    {f : α -> β -> E}
    (hf : Integrable (Function.uncurry f) (μ.prod ν)) :
    ∫ x, ∫ y, f x y ∂ν ∂μ = ∫ z, f z.1 z.2 ∂μ.prod ν := by
  exact MeasureTheory.integral_integral hf

/-- Swap the order of Bochner integration for an integrable curried function. -/
theorem integral_integral_swap
    {α : Type u} [MeasurableSpace α] {β : Type v} [MeasurableSpace β]
    {E : Type w} [NormedAddCommGroup E] [NormedSpace ℝ E]
    {μ : Measure α} {ν : Measure β} [SFinite μ] [SFinite ν]
    {f : α -> β -> E}
    (hf : Integrable (Function.uncurry f) (μ.prod ν)) :
    ∫ x, ∫ y, f x y ∂ν ∂μ = ∫ y, ∫ x, f x y ∂μ ∂ν := by
  exact MeasureTheory.integral_integral_swap hf

/--
In a product of probability spaces, a function of the second coordinate
integrates to its marginal expectation.

This is the finite-product/Fubini shape used when a later empirical-process
argument conditions on one coordinate and integrates out an independent copy.
-/
theorem probability_integral_prod_snd
    {α : Type u} [MeasurableSpace α] {β : Type v} [MeasurableSpace β]
    {E : Type w} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (μ : MeasureTheory.ProbabilityMeasure α)
    (ν : MeasureTheory.ProbabilityMeasure β)
    (f : β -> E) :
    ∫ z, f z.2 ∂((μ : Measure α).prod (ν : Measure β)) =
      ∫ y, f y ∂(ν : Measure β) := by
  simpa using
    (MeasureTheory.integral_fun_snd
      (μ := (μ : Measure α)) (ν := (ν : Measure β)) f)

/--
In a product of probability spaces, a function of the first coordinate
integrates to its marginal expectation.
-/
theorem probability_integral_prod_fst
    {α : Type u} [MeasurableSpace α] {β : Type v} [MeasurableSpace β]
    {E : Type w} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (μ : MeasureTheory.ProbabilityMeasure α)
    (ν : MeasureTheory.ProbabilityMeasure β)
    (f : α -> E) :
    ∫ z, f z.1 ∂((μ : Measure α).prod (ν : Measure β)) =
      ∫ x, f x ∂(μ : Measure α) := by
  simpa using
    (MeasureTheory.integral_fun_fst
      (μ := (μ : Measure α)) (ν := (ν : Measure β)) f)

/--
On `P × P`, the two product-coordinate copies of an integrable function have
zero mean difference.

This is the small Fubini bridge used by symmetrization: the ghost copy can
replace the marginal expectation because the two coordinate expectations
cancel exactly.
-/
theorem probability_integral_prod_fst_sub_snd_eq_zero
    {α : Type u} [MeasurableSpace α]
    {E : Type w} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (μ : MeasureTheory.ProbabilityMeasure α) (f : α -> E)
    (hf : Integrable f (μ : Measure α)) :
    ∫ z, f z.1 - f z.2 ∂((μ : Measure α).prod (μ : Measure α)) = 0 := by
  have hfst :
      Integrable (fun z : α × α => f z.1)
        ((μ : Measure α).prod (μ : Measure α)) := by
    simpa [Function.comp_def] using
      (MeasureTheory.measurePreserving_fst
        (μ := (μ : Measure α)) (ν := (μ : Measure α))).integrable_comp_of_integrable
        hf
  have hsnd :
      Integrable (fun z : α × α => f z.2)
        ((μ : Measure α).prod (μ : Measure α)) := by
    simpa [Function.comp_def] using
      (MeasureTheory.measurePreserving_snd
        (μ := (μ : Measure α)) (ν := (μ : Measure α))).integrable_comp_of_integrable
        hf
  calc
    ∫ z, f z.1 - f z.2 ∂((μ : Measure α).prod (μ : Measure α))
        = (∫ z, f z.1 ∂((μ : Measure α).prod (μ : Measure α))) -
            ∫ z, f z.2 ∂((μ : Measure α).prod (μ : Measure α)) := by
          exact integral_sub hfst hsnd
    _ = (∫ x, f x ∂(μ : Measure α)) - ∫ x, f x ∂(μ : Measure α) := by
          rw [probability_integral_prod_fst μ μ f,
            probability_integral_prod_snd μ μ f]
    _ = 0 := sub_self _

/--
Finite-product weighted sums of product-copy pair differences have mean zero.

This packages the common symmetrization pattern over `(P × P)^n`: each
coordinate contributes a centered difference of two independent copies, and
finite linearity preserves the zero expectation.
-/
theorem probability_pi_integral_prod_fst_sub_snd_weighted_sum_eq_zero
    {α : Type u} [MeasurableSpace α]
    (P : MeasureTheory.ProbabilityMeasure α) {n : ℕ}
    {f : α -> ℝ} (weights : Fin n -> ℝ)
    (hf : Integrable f (P : Measure α)) :
    ∫ sample : Fin n -> α × α,
        (∑ i : Fin n, weights i * (f (sample i).1 - f (sample i).2))
          ∂(Measure.pi fun _ : Fin n =>
            ((P : Measure α).prod (P : Measure α))) =
      0 := by
  have hpairIntegrable :
      Integrable
        (fun z : α × α => f z.1 - f z.2)
        ((P : Measure α).prod (P : Measure α)) := by
    have hfst :
        Integrable (fun z : α × α => f z.1)
          ((P : Measure α).prod (P : Measure α)) := by
      simpa [Function.comp_def] using
        (MeasureTheory.measurePreserving_fst
          (μ := (P : Measure α)) (ν := (P : Measure α))).integrable_comp_of_integrable
          hf
    have hsnd :
        Integrable (fun z : α × α => f z.2)
          ((P : Measure α).prod (P : Measure α)) := by
      simpa [Function.comp_def] using
        (MeasureTheory.measurePreserving_snd
          (μ := (P : Measure α)) (ν := (P : Measure α))).integrable_comp_of_integrable
          hf
    exact hfst.sub hsnd
  simpa using
    (probability_pi_integral_weighted_sum_eq_zero
      (P := fun _ : Fin n =>
        (⟨(P : Measure α).prod (P : Measure α), inferInstance⟩ :
          MeasureTheory.ProbabilityMeasure (α × α)))
      (f := fun _ : Fin n => fun z : α × α => f z.1 - f z.2)
      (weights := weights)
      (fun _ => hpairIntegrable)
      (fun _ =>
        probability_integral_prod_fst_sub_snd_eq_zero (μ := P) (f := f) hf))

/--
Product expectation for separated scalar functions under a product probability
measure.

This is the product-space version of the independent expectation factorization
used by symmetrization and independent-copy handoffs.
-/
theorem probability_integral_prod_mul
    {α : Type u} [MeasurableSpace α] {β : Type v} [MeasurableSpace β]
    {𝕜 : Type w} [RCLike 𝕜]
    (μ : MeasureTheory.ProbabilityMeasure α)
    (ν : MeasureTheory.ProbabilityMeasure β)
    (f : α -> 𝕜) (g : β -> 𝕜) :
    ∫ z, f z.1 * g z.2 ∂((μ : Measure α).prod (ν : Measure β)) =
      (∫ x, f x ∂(μ : Measure α)) *
        ∫ y, g y ∂(ν : Measure β) := by
  exact
    MeasureTheory.integral_prod_mul
      (μ := (μ : Measure α)) (ν := (ν : Measure β)) f g

/-- Product of expectations for two independent scalar random variables. -/
theorem indepFun_integral_mul_eq_mul_integral
    {Ω : Type u} {𝕜 : Type v} [RCLike 𝕜] {mΩ : MeasurableSpace Ω}
    {μ : Measure Ω} {X Y : Ω -> 𝕜}
    (hXY : X ⟂ᵢ[μ] Y)
    (hX : AEStronglyMeasurable X μ) (hY : AEStronglyMeasurable Y μ) :
    ∫ ω, X ω * Y ω ∂μ = (∫ ω, X ω ∂μ) * ∫ ω, Y ω ∂μ := by
  exact hXY.integral_fun_mul_eq_mul_integral hX hY

/-- Product of expectations for a finite independent family of scalar random variables. -/
theorem iIndepFun_integral_prod_eq_prod_integral
    {Ω : Type u} {𝕜 : Type v} {ι : Type w} [RCLike 𝕜] [Fintype ι]
    {mΩ : MeasurableSpace Ω} {μ : Measure Ω} {X : ι -> Ω -> 𝕜}
    (hX : iIndepFun X μ)
    (mX : ∀ i, AEStronglyMeasurable (X i) μ) :
    ∫ ω, ∏ i, X i ω ∂μ = ∏ i, ∫ ω, X i ω ∂μ := by
  exact hX.integral_fun_prod_eq_prod_integral mX

end ProbabilityMeasure
end StatInference
