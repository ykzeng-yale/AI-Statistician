import StatInference.EmpiricalProcess.CoveringPrimitive

/-!
# Finite-code empirical trace bridges

This file records a reusable finite-coding layer for fixed-sample empirical
traces.  It is meant to sit between structural trace encodings (VC/subgraph,
finite grids, quantization, or maximal-separated codes) and the entropy
side-condition constructors used in Theorem 2.4.3.
-/

namespace StatInference

/--
If every empirical trace has a code in a finite set and the code is injective on
the realized trace image, then the realized trace image is finite.
-/
theorem finite_empiricalTrace_image_of_finite_code
    {Observation : Type u} {Index : Type v} {Code : Type w} {n : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {code : (Fin n -> ℝ) -> Code} {codeSet : Finset Code}
    (hcode_mem :
      ∀ index, index ∈ indexClass ->
        code (empiricalTrace sample classFun index) ∈ codeSet)
    (hinj : Set.InjOn code (empiricalTrace sample classFun '' indexClass)) :
    (empiricalTrace sample classFun '' indexClass).Finite := by
  classical
  let traceImage : Set (Fin n -> ℝ) :=
    empiricalTrace sample classFun '' indexClass
  have himage_subset : code '' traceImage ⊆ (codeSet : Set Code) := by
    rintro coded ⟨trace, htrace, rfl⟩
    rcases htrace with ⟨index, hindex, rfl⟩
    exact hcode_mem index hindex
  have himage_finite : (code '' traceImage).Finite :=
    codeSet.finite_toSet.subset himage_subset
  exact
    Set.Finite.of_finite_image (s := traceImage) (f := code)
      himage_finite (by simpa [traceImage] using hinj)

/--
The cardinality of a finitely coded empirical trace image is bounded by the
cardinality of the finite code set.
-/
theorem empiricalTrace_image_toFinset_card_le_finite_code
    {Observation : Type u} {Index : Type v} {Code : Type w} {n : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {code : (Fin n -> ℝ) -> Code} {codeSet : Finset Code}
    (hcode_mem :
      ∀ index, index ∈ indexClass ->
        code (empiricalTrace sample classFun index) ∈ codeSet)
    (hinj : Set.InjOn code (empiricalTrace sample classFun '' indexClass)) :
    (finite_empiricalTrace_image_of_finite_code hcode_mem hinj).toFinset.card ≤
      codeSet.card := by
  classical
  let traceImage : Set (Fin n -> ℝ) :=
    empiricalTrace sample classFun '' indexClass
  have htrace_finite : traceImage.Finite :=
    finite_empiricalTrace_image_of_finite_code
      (sample := sample) (indexClass := indexClass)
      (classFun := classFun) (code := code) (codeSet := codeSet)
      hcode_mem hinj
  have hcode_target : ∀ trace ∈ traceImage, code trace ∈ (codeSet : Set Code) := by
    intro trace htrace
    rcases htrace with ⟨index, hindex, rfl⟩
    exact hcode_mem index hindex
  have hle :
      traceImage.ncard ≤ (codeSet : Set Code).ncard :=
    Set.ncard_le_ncard_of_injOn
      (s := traceImage) (t := (codeSet : Set Code)) code
      hcode_target (by simpa [traceImage] using hinj) codeSet.finite_toSet
  simpa [traceImage, Set.ncard_eq_toFinset_card traceImage htrace_finite] using hle

/--
A finitely coded empirical trace image inherits any supplied polynomial
cardinality bound on its finite code set.
-/
theorem empiricalTrace_image_card_add_one_real_le_of_finite_code_nat_poly
    {Observation : Type u} {Index : Type v} {Code : Type w} {n d : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {code : (Fin n -> ℝ) -> Code} {codeSet : Finset Code}
    {C : ℝ}
    (hcode_mem :
      ∀ index, index ∈ indexClass ->
        code (empiricalTrace sample classFun index) ∈ codeSet)
    (hinj : Set.InjOn code (empiricalTrace sample classFun '' indexClass))
    (hcode_card :
      ((codeSet.card : ℝ) + 1) ≤ C * (((n + 1 : ℕ) : ℝ) ^ d)) :
    (((finite_empiricalTrace_image_of_finite_code hcode_mem hinj).toFinset.card : ℝ) + 1) ≤
      C * (((n + 1 : ℕ) : ℝ) ^ d) := by
  have htrace_le :
      (finite_empiricalTrace_image_of_finite_code hcode_mem hinj).toFinset.card ≤
        codeSet.card :=
    empiricalTrace_image_toFinset_card_le_finite_code hcode_mem hinj
  have htrace_le_real :
      (((finite_empiricalTrace_image_of_finite_code hcode_mem hinj).toFinset.card : ℝ) + 1) ≤
        (codeSet.card : ℝ) + 1 := by
    exact_mod_cast Nat.add_le_add_right htrace_le 1
  exact htrace_le_real.trans hcode_card

end StatInference
