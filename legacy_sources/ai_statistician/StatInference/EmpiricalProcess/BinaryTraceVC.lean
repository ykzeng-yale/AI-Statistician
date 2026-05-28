import StatInference.EmpiricalProcess.CoveringPrimitive
import StatInference.EmpiricalProcess.VCSauer

/-!
# Binary empirical traces and VC/Sauer bounds

This file connects `{0,1}`-valued empirical traces to the finite set-family
Sauer bridge.  It is the first concrete path from VdV&W trace images to the
polynomial cardinality shape consumed by Theorem 2.4.3.
-/

namespace StatInference

open scoped BigOperators

/-- The subset of sample coordinates where an indexed function takes value `1`. -/
noncomputable def empiricalBinaryTraceSet
    {Observation : Type u} {Index : Type v} {n : ℕ}
    (sample : SampleAt Observation n)
    (classFun : Index -> Observation -> ℝ) (index : Index) :
    Finset (Fin n) :=
  Finset.univ.filter fun sampleIndex =>
    classFun index (sample sampleIndex) = 1

/--
The finite family of binary trace sets realized by `indexClass` on a fixed
sample.
-/
noncomputable def empiricalBinaryTraceSetFamily
    {Observation : Type u} {Index : Type v} {n : ℕ}
    (sample : SampleAt Observation n)
    (indexClass : Set Index) (classFun : Index -> Observation -> ℝ) :
    Finset (Finset (Fin n)) :=
  by
    classical
    exact
      Finset.univ.filter fun traceSet =>
        ∃ index, index ∈ indexClass ∧
          empiricalBinaryTraceSet sample classFun index = traceSet

/-- Real-valued characteristic function associated to a binary trace set. -/
noncomputable def empiricalBinaryTraceFunction {n : ℕ}
    (traceSet : Finset (Fin n)) : Fin n -> ℝ :=
  fun sampleIndex => if sampleIndex ∈ traceSet then 1 else 0

theorem empiricalBinaryTraceSet_mem_family
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {index : Index} (hindex : index ∈ indexClass) :
    empiricalBinaryTraceSet sample classFun index ∈
      empiricalBinaryTraceSetFamily sample indexClass classFun := by
  classical
  simp [empiricalBinaryTraceSetFamily]
  exact ⟨index, hindex, rfl⟩

/--
For a `{0,1}`-valued function on the sample, the real empirical trace is the
characteristic function of its binary trace set.
-/
theorem empiricalTrace_eq_binaryTraceFunction_of_sample_binary
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {classFun : Index -> Observation -> ℝ} {index : Index}
    (hbinary :
      ∀ sampleIndex : Fin n,
        classFun index (sample sampleIndex) = 0 ∨
          classFun index (sample sampleIndex) = 1) :
    empiricalTrace sample classFun index =
      empiricalBinaryTraceFunction
        (empiricalBinaryTraceSet sample classFun index) := by
  classical
  ext sampleIndex
  by_cases hone : classFun index (sample sampleIndex) = 1
  · simp [empiricalTrace, empiricalBinaryTraceFunction,
      empiricalBinaryTraceSet, hone]
  · rcases hbinary sampleIndex with hzero | hone'
    · simp [empiricalTrace, empiricalBinaryTraceFunction,
        empiricalBinaryTraceSet, hzero]
    · exact (hone hone').elim

/--
The real empirical trace image of a `{0,1}`-valued class is contained in the
image of the finite binary trace-set family.
-/
theorem empiricalTrace_image_subset_binaryTraceFunction_image_family
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    (hbinary :
      ∀ index, index ∈ indexClass -> ∀ sampleIndex : Fin n,
        classFun index (sample sampleIndex) = 0 ∨
          classFun index (sample sampleIndex) = 1) :
    empiricalTrace sample classFun '' indexClass ⊆
      empiricalBinaryTraceFunction ''
        (empiricalBinaryTraceSetFamily sample indexClass classFun : Set (Finset (Fin n))) := by
  classical
  rintro trace ⟨index, hindex, rfl⟩
  refine ⟨empiricalBinaryTraceSet sample classFun index, ?_, ?_⟩
  · exact empiricalBinaryTraceSet_mem_family hindex
  · exact (empiricalTrace_eq_binaryTraceFunction_of_sample_binary
      (hbinary index hindex)).symm

/-- Binary-valued empirical traces form a finite real trace image. -/
theorem finite_empiricalTrace_image_of_sample_binary
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    (hbinary :
      ∀ index, index ∈ indexClass -> ∀ sampleIndex : Fin n,
        classFun index (sample sampleIndex) = 0 ∨
          classFun index (sample sampleIndex) = 1) :
    (empiricalTrace sample classFun '' indexClass).Finite := by
  classical
  exact
    ((empiricalBinaryTraceSetFamily sample indexClass classFun).finite_toSet.image
      empiricalBinaryTraceFunction).subset
      (empiricalTrace_image_subset_binaryTraceFunction_image_family hbinary)

/--
The real trace-image cardinality is bounded by the binary trace-family
cardinality.
-/
theorem empiricalTrace_image_toFinset_card_le_binaryTraceSetFamily_card
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    (hbinary :
      ∀ index, index ∈ indexClass -> ∀ sampleIndex : Fin n,
        classFun index (sample sampleIndex) = 0 ∨
          classFun index (sample sampleIndex) = 1) :
    (finite_empiricalTrace_image_of_sample_binary hbinary).toFinset.card ≤
      (empiricalBinaryTraceSetFamily sample indexClass classFun).card := by
  classical
  let traceImage : Set (Fin n -> ℝ) :=
    empiricalTrace sample classFun '' indexClass
  let binaryFamily : Finset (Finset (Fin n)) :=
    empiricalBinaryTraceSetFamily sample indexClass classFun
  have hsubset :
      traceImage ⊆
        empiricalBinaryTraceFunction '' (binaryFamily : Set (Finset (Fin n))) := by
    simpa [traceImage, binaryFamily] using
      empiricalTrace_image_subset_binaryTraceFunction_image_family
        (sample := sample) (indexClass := indexClass)
        (classFun := classFun) hbinary
  have htarget_finite :
      (empiricalBinaryTraceFunction '' (binaryFamily : Set (Finset (Fin n)))).Finite :=
    binaryFamily.finite_toSet.image empiricalBinaryTraceFunction
  have htrace_finite : traceImage.Finite :=
    (finite_empiricalTrace_image_of_sample_binary
      (sample := sample) (indexClass := indexClass)
      (classFun := classFun) hbinary)
  have hle_subset :
      traceImage.ncard ≤
        (empiricalBinaryTraceFunction '' (binaryFamily : Set (Finset (Fin n)))).ncard :=
    Set.ncard_le_ncard hsubset htarget_finite
  have hle_image :
      (empiricalBinaryTraceFunction '' (binaryFamily : Set (Finset (Fin n)))).ncard ≤
        (binaryFamily : Set (Finset (Fin n))).ncard :=
    Set.ncard_image_le (f := empiricalBinaryTraceFunction)
      (s := (binaryFamily : Set (Finset (Fin n)))) binaryFamily.finite_toSet
  have hle := hle_subset.trans hle_image
  simpa [traceImage, binaryFamily,
      Set.ncard_eq_toFinset_card traceImage htrace_finite] using hle

/--
Binary trace images satisfy a Sauer polynomial real-cardinality bound whenever
their realized binary trace family has VC dimension at most `d`.
-/
theorem empiricalTrace_image_card_add_one_real_le_vc_nat_poly_of_sample_binary
    {Observation : Type u} {Index : Type v} {n d : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    (hbinary :
      ∀ index, index ∈ indexClass -> ∀ sampleIndex : Fin n,
        classFun index (sample sampleIndex) = 0 ∨
          classFun index (sample sampleIndex) = 1)
    (hvc :
      (empiricalBinaryTraceSetFamily sample indexClass classFun).vcDim ≤ d) :
    (((finite_empiricalTrace_image_of_sample_binary hbinary).toFinset.card : ℝ) + 1) ≤
      ((d + 2 : ℕ) : ℝ) * (((n + 1 : ℕ) : ℝ) ^ d) := by
  classical
  have htrace_le :
      (finite_empiricalTrace_image_of_sample_binary hbinary).toFinset.card ≤
        (empiricalBinaryTraceSetFamily sample indexClass classFun).card :=
    empiricalTrace_image_toFinset_card_le_binaryTraceSetFamily_card hbinary
  have htrace_le_real :
      (((finite_empiricalTrace_image_of_sample_binary hbinary).toFinset.card : ℝ) + 1) ≤
        ((empiricalBinaryTraceSetFamily sample indexClass classFun).card : ℝ) + 1 := by
    exact_mod_cast Nat.add_le_add_right htrace_le 1
  exact htrace_le_real.trans
    (vdVWSauerShelah_card_add_one_real_le_nat_poly_of_vcDim_le
      (empiricalBinaryTraceSetFamily sample indexClass classFun)
      (N := n) (d := d) (by simp) hvc)

end StatInference
