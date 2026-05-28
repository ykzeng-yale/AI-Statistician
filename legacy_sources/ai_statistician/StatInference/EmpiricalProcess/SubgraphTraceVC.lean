import StatInference.EmpiricalProcess.BinaryTraceVC

/-!
# Threshold/subgraph empirical trace bridges

This file exposes the first subgraph-style entry point for VC entropy routes:
every fixed threshold of a real-valued class is a binary class, so its
empirical traces can be controlled by the binary Sauer bridge.
-/

namespace StatInference

/-- The `{0,1}` indicator of the strict threshold event `threshold < f_i x`. -/
noncomputable def thresholdIndicatorClassFun
    {Observation : Type u} {Index : Type v}
    (classFun : Index -> Observation -> ℝ) (threshold : ℝ) :
    Index -> Observation -> ℝ :=
  fun index observation =>
    if threshold < classFun index observation then 1 else 0

/-- Threshold indicators are samplewise binary-valued. -/
theorem thresholdIndicatorClassFun_sample_binary
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {classFun : Index -> Observation -> ℝ} {threshold : ℝ}
    (index : Index) :
    ∀ sampleIndex : Fin n,
      thresholdIndicatorClassFun classFun threshold index (sample sampleIndex) = 0 ∨
        thresholdIndicatorClassFun classFun threshold index (sample sampleIndex) = 1 := by
  intro sampleIndex
  unfold thresholdIndicatorClassFun
  by_cases h : threshold < classFun index (sample sampleIndex)
  · right
    simp [h]
  · left
    simp [h]

/--
The binary trace set of a thresholded class is exactly the sample coordinates
where the original real-valued function exceeds the threshold.
-/
theorem empiricalBinaryTraceSet_thresholdIndicatorClassFun_eq
    {Observation : Type u} {Index : Type v} {n : ℕ}
    (sample : SampleAt Observation n)
    (classFun : Index -> Observation -> ℝ) (threshold : ℝ)
    (index : Index) :
    empiricalBinaryTraceSet sample
        (thresholdIndicatorClassFun classFun threshold) index =
      Finset.univ.filter fun sampleIndex : Fin n =>
        threshold < classFun index (sample sampleIndex) := by
  classical
  ext sampleIndex
  by_cases h : threshold < classFun index (sample sampleIndex)
  · simp [empiricalBinaryTraceSet, thresholdIndicatorClassFun, h]
  · simp [empiricalBinaryTraceSet, thresholdIndicatorClassFun, h]

/--
The empirical trace set of the subgraph class
`{(x,t) | t < f_i x}` on a finite sample of pairs `(x,t)`.
-/
noncomputable def empiricalSubgraphTraceSet
    {Observation : Type u} {Index : Type v} {n : ℕ}
    (sample : SampleAt (Observation × ℝ) n)
    (classFun : Index -> Observation -> ℝ) (index : Index) :
    Finset (Fin n) :=
  Finset.univ.filter fun sampleIndex =>
    (sample sampleIndex).2 < classFun index (sample sampleIndex).1

/--
The finite family of subgraph trace sets realized by `indexClass` on a sample
of observation/threshold pairs.
-/
noncomputable def empiricalSubgraphTraceSetFamily
    {Observation : Type u} {Index : Type v} {n : ℕ}
    (sample : SampleAt (Observation × ℝ) n)
    (indexClass : Set Index) (classFun : Index -> Observation -> ℝ) :
    Finset (Finset (Fin n)) :=
  by
    classical
    exact
      Finset.univ.filter fun traceSet =>
        ∃ index, index ∈ indexClass ∧
          empiricalSubgraphTraceSet sample classFun index = traceSet

/--
Fixed-threshold binary traces are exactly subgraph traces on the lifted sample
`i ↦ (x_i, threshold)`.
-/
theorem empiricalBinaryTraceSet_thresholdIndicatorClassFun_eq_empiricalSubgraphTraceSet
    {Observation : Type u} {Index : Type v} {n : ℕ}
    (sample : SampleAt Observation n)
    (classFun : Index -> Observation -> ℝ) (threshold : ℝ)
    (index : Index) :
    empiricalBinaryTraceSet sample
        (thresholdIndicatorClassFun classFun threshold) index =
      empiricalSubgraphTraceSet
        (fun sampleIndex : Fin n => (sample sampleIndex, threshold))
        classFun index := by
  classical
  ext sampleIndex
  by_cases h : threshold < classFun index (sample sampleIndex)
  · simp [empiricalBinaryTraceSet, thresholdIndicatorClassFun,
      empiricalSubgraphTraceSet, h]
  · simp [empiricalBinaryTraceSet, thresholdIndicatorClassFun,
      empiricalSubgraphTraceSet, h]

/--
The fixed-threshold binary trace family is the subgraph trace family of the
lifted constant-threshold sample.
-/
theorem empiricalBinaryTraceSetFamily_thresholdIndicatorClassFun_eq_empiricalSubgraphTraceSetFamily
    {Observation : Type u} {Index : Type v} {n : ℕ}
    (sample : SampleAt Observation n)
    (indexClass : Set Index) (classFun : Index -> Observation -> ℝ)
    (threshold : ℝ) :
    empiricalBinaryTraceSetFamily sample indexClass
        (thresholdIndicatorClassFun classFun threshold) =
      empiricalSubgraphTraceSetFamily
        (fun sampleIndex : Fin n => (sample sampleIndex, threshold))
        indexClass classFun := by
  classical
  ext traceSet
  simp [empiricalBinaryTraceSetFamily, empiricalSubgraphTraceSetFamily,
    empiricalBinaryTraceSet_thresholdIndicatorClassFun_eq_empiricalSubgraphTraceSet]

/--
Uniform empirical VC bound for every fixed threshold subgraph of a real-valued
class.

This is the local theorem-facing version of the VC-subgraph input used by the
Theorem 2.4.3 integer-grid route: every finite sample and every real threshold
has threshold-indicator trace VC dimension at most `d`.
-/
def VdVWUniformThresholdVCSubgraphBound
    {Observation : Type u} {Index : Type v}
    (indexClass : Set Index) (classFun : Index -> Observation -> ℝ)
    (d : ℕ) : Prop :=
  ∀ {n : ℕ} (sample : SampleAt Observation n) (threshold : ℝ),
    (empiricalBinaryTraceSetFamily sample indexClass
      (thresholdIndicatorClassFun classFun threshold)).vcDim ≤ d

/--
The uniform threshold/subgraph VC predicate immediately supplies the
samplewise fixed-threshold VC inequality used by the threshold-grid entropy
route.
-/
theorem VdVWUniformThresholdVCSubgraphBound.empiricalBinaryTraceSetFamily_vcDim_le
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {d : ℕ}
    (hvc : VdVWUniformThresholdVCSubgraphBound indexClass classFun d)
    (threshold : ℝ) :
    (empiricalBinaryTraceSetFamily sample indexClass
      (thresholdIndicatorClassFun classFun threshold)).vcDim ≤ d :=
  hvc sample threshold

/--
Uniform empirical VC bound for the full subgraph class
`{(x,t) | t < f_i x}` over arbitrary finite samples of observation/threshold
pairs.
-/
def VdVWUniformSubgraphVCBound
    {Observation : Type u} {Index : Type v}
    (indexClass : Set Index) (classFun : Index -> Observation -> ℝ)
    (d : ℕ) : Prop :=
  ∀ {n : ℕ} (sample : SampleAt (Observation × ℝ) n),
    (empiricalSubgraphTraceSetFamily sample indexClass classFun).vcDim ≤ d

/--
A uniform VC bound for the full subgraph class implies the all-threshold
empirical VC predicate used by the Theorem 2.4.3 threshold-grid route.
-/
theorem VdVWUniformSubgraphVCBound.toUniformThresholdVCSubgraphBound
    {Observation : Type u} {Index : Type v}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {d : ℕ}
    (hvc : VdVWUniformSubgraphVCBound indexClass classFun d) :
    VdVWUniformThresholdVCSubgraphBound indexClass classFun d := by
  intro n sample threshold
  rw [empiricalBinaryTraceSetFamily_thresholdIndicatorClassFun_eq_empiricalSubgraphTraceSetFamily]
  exact hvc (fun sampleIndex : Fin n => (sample sampleIndex, threshold))

/--
For a fixed threshold, the empirical trace image of the threshold-indicator
class satisfies the Sauer polynomial bound whenever the realized threshold
trace family has VC dimension at most `d`.
-/
theorem thresholdIndicator_trace_card_add_one_real_le_vc_nat_poly
    {Observation : Type u} {Index : Type v} {n d : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {threshold : ℝ}
    (hvc :
      (empiricalBinaryTraceSetFamily sample indexClass
        (thresholdIndicatorClassFun classFun threshold)).vcDim ≤ d) :
    (((finite_empiricalTrace_image_of_sample_binary
      (sample := sample) (indexClass := indexClass)
      (classFun := thresholdIndicatorClassFun classFun threshold)
      (by
        intro index _hindex
        exact thresholdIndicatorClassFun_sample_binary index)).toFinset.card : ℝ) + 1) ≤
      ((d + 2 : ℕ) : ℝ) * (((n + 1 : ℕ) : ℝ) ^ d) := by
  exact
    empiricalTrace_image_card_add_one_real_le_vc_nat_poly_of_sample_binary
      (sample := sample) (indexClass := indexClass)
      (classFun := thresholdIndicatorClassFun classFun threshold)
      (by
        intro index _hindex
        exact thresholdIndicatorClassFun_sample_binary index)
      hvc

end StatInference
