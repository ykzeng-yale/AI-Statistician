import Mathlib.Data.Fintype.BigOperators
import StatInference.EmpiricalProcess.TraceCoding
import StatInference.EmpiricalProcess.SubgraphTraceVC

/-!
# Finite threshold coding of empirical traces

This file packages the next structural step after fixed-threshold VC/Sauer
bounds.  A finite set of thresholds gives each real-valued empirical trace a
threshold signature.  If those signatures separate the realized traces, then
the real trace image is bounded by the finite set of realized threshold
signatures.
-/

namespace StatInference

open scoped BigOperators

/--
The finite-threshold signature of a fixed real empirical trace: for each
threshold, record the sample coordinates where the trace is above that
threshold.
-/
noncomputable def thresholdTraceCode {n : ℕ}
    (thresholds : Finset ℝ) (trace : Fin n -> ℝ) :
    {threshold // threshold ∈ thresholds} -> Finset (Fin n) :=
  fun threshold =>
    Finset.univ.filter fun sampleIndex : Fin n =>
      threshold.1 < trace sampleIndex

/--
The finite set of threshold signatures whose coordinates are realized by the
corresponding threshold-indicator classes.
-/
noncomputable def thresholdTraceCodeSet
    {Observation : Type u} {Index : Type v} {n : ℕ}
    (sample : SampleAt Observation n)
    (indexClass : Set Index) (classFun : Index -> Observation -> ℝ)
    (thresholds : Finset ℝ) :
    Finset ({threshold // threshold ∈ thresholds} -> Finset (Fin n)) :=
  by
    classical
    exact
      Finset.univ.filter fun code =>
        ∀ threshold : {threshold // threshold ∈ thresholds},
          code threshold ∈
            empiricalBinaryTraceSetFamily sample indexClass
              (thresholdIndicatorClassFun classFun threshold.1)

/--
On an empirical trace, the finite-threshold signature agrees coordinatewise
with the binary trace set of the threshold-indicator class.
-/
theorem thresholdTraceCode_empiricalTrace_eq_binaryTraceSet
    {Observation : Type u} {Index : Type v} {n : ℕ}
    (sample : SampleAt Observation n)
    (classFun : Index -> Observation -> ℝ)
    (thresholds : Finset ℝ) (index : Index)
    (threshold : {threshold // threshold ∈ thresholds}) :
    thresholdTraceCode thresholds (empiricalTrace sample classFun index) threshold =
      empiricalBinaryTraceSet sample
        (thresholdIndicatorClassFun classFun threshold.1) index := by
  classical
  ext sampleIndex
  by_cases h : threshold.1 < classFun index (sample sampleIndex)
  · simp [thresholdTraceCode, empiricalTrace, empiricalBinaryTraceSet,
      thresholdIndicatorClassFun, h]
  · simp [thresholdTraceCode, empiricalTrace, empiricalBinaryTraceSet,
      thresholdIndicatorClassFun, h]

/--
Equality of finite-threshold signatures is exactly pointwise equality of all
threshold comparisons on the sample.
-/
theorem thresholdTraceCode_eq_iff_forall_threshold_sample
    {n : ℕ} {thresholds : Finset ℝ}
    {trace₁ trace₂ : Fin n -> ℝ} :
    thresholdTraceCode thresholds trace₁ = thresholdTraceCode thresholds trace₂ ↔
      ∀ threshold : {threshold // threshold ∈ thresholds},
        ∀ sampleIndex : Fin n,
          (threshold.1 < trace₁ sampleIndex ↔
            threshold.1 < trace₂ sampleIndex) := by
  classical
  constructor
  · intro hcode threshold sampleIndex
    have hset :
        thresholdTraceCode thresholds trace₁ threshold =
          thresholdTraceCode thresholds trace₂ threshold :=
      congrFun hcode threshold
    have hmem :
        sampleIndex ∈ thresholdTraceCode thresholds trace₁ threshold ↔
          sampleIndex ∈ thresholdTraceCode thresholds trace₂ threshold := by
      simpa using congrArg (fun s : Finset (Fin n) => sampleIndex ∈ s) hset
    simpa [thresholdTraceCode] using hmem
  · intro hpoint
    funext threshold
    ext sampleIndex
    simpa [thresholdTraceCode] using hpoint threshold sampleIndex

/--
Pointwise threshold-comparison separation is enough to supply the finite-code
separation hypothesis used by the threshold-cardinality handoffs.
-/
theorem thresholdTraceCode_separates_of_pointwise_thresholds_separate
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {thresholds : Finset ℝ}
    (hpoint :
      ∀ index₁, index₁ ∈ indexClass ->
        ∀ index₂, index₂ ∈ indexClass ->
          (∀ sampleIndex : Fin n,
            ∀ threshold : {threshold // threshold ∈ thresholds},
              (threshold.1 < classFun index₁ (sample sampleIndex) ↔
                threshold.1 < classFun index₂ (sample sampleIndex))) ->
          empiricalTrace sample classFun index₁ =
            empiricalTrace sample classFun index₂) :
    ∀ index₁, index₁ ∈ indexClass ->
      ∀ index₂, index₂ ∈ indexClass ->
        (∀ threshold : {threshold // threshold ∈ thresholds},
          thresholdTraceCode thresholds
              (empiricalTrace sample classFun index₁) threshold =
            thresholdTraceCode thresholds
              (empiricalTrace sample classFun index₂) threshold) ->
        empiricalTrace sample classFun index₁ =
          empiricalTrace sample classFun index₂ := by
  intro index₁ hindex₁ index₂ hindex₂ hcode
  apply hpoint index₁ hindex₁ index₂ hindex₂
  intro sampleIndex threshold
  have hcodeFun :
      thresholdTraceCode thresholds (empiricalTrace sample classFun index₁) =
        thresholdTraceCode thresholds (empiricalTrace sample classFun index₂) := by
    funext threshold
    exact hcode threshold
  have hpointCode :=
    (thresholdTraceCode_eq_iff_forall_threshold_sample.mp hcodeFun)
      threshold sampleIndex
  simpa [empiricalTrace] using hpointCode

/--
A coordinatewise threshold-separation criterion supplies the pointwise
threshold-separation hypothesis.  This is the local shape expected from
geometric arguments: at every sample coordinate, matching all threshold
predicates forces equality of the two realized real values.
-/
theorem pointwise_thresholds_separate_of_coordinate_thresholds_separate
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {thresholds : Finset ℝ}
    (hcoordinate :
      ∀ sampleIndex : Fin n,
        ∀ index₁, index₁ ∈ indexClass ->
          ∀ index₂, index₂ ∈ indexClass ->
            (∀ threshold : {threshold // threshold ∈ thresholds},
              (threshold.1 < classFun index₁ (sample sampleIndex) ↔
                threshold.1 < classFun index₂ (sample sampleIndex))) ->
            classFun index₁ (sample sampleIndex) =
              classFun index₂ (sample sampleIndex)) :
    ∀ index₁, index₁ ∈ indexClass ->
      ∀ index₂, index₂ ∈ indexClass ->
        (∀ sampleIndex : Fin n,
          ∀ threshold : {threshold // threshold ∈ thresholds},
            (threshold.1 < classFun index₁ (sample sampleIndex) ↔
              threshold.1 < classFun index₂ (sample sampleIndex))) ->
        empiricalTrace sample classFun index₁ =
          empiricalTrace sample classFun index₂ := by
  intro index₁ hindex₁ index₂ hindex₂ hthresholds
  funext sampleIndex
  simpa [empiricalTrace] using
    hcoordinate sampleIndex index₁ hindex₁ index₂ hindex₂
      (hthresholds sampleIndex)

/--
Coordinatewise threshold separation supplies the finite-code separation
hypothesis used by the threshold-cardinality handoffs.
-/
theorem thresholdTraceCode_separates_of_coordinate_thresholds_separate
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {thresholds : Finset ℝ}
    (hcoordinate :
      ∀ sampleIndex : Fin n,
        ∀ index₁, index₁ ∈ indexClass ->
          ∀ index₂, index₂ ∈ indexClass ->
            (∀ threshold : {threshold // threshold ∈ thresholds},
              (threshold.1 < classFun index₁ (sample sampleIndex) ↔
                threshold.1 < classFun index₂ (sample sampleIndex))) ->
            classFun index₁ (sample sampleIndex) =
              classFun index₂ (sample sampleIndex)) :
    ∀ index₁, index₁ ∈ indexClass ->
      ∀ index₂, index₂ ∈ indexClass ->
        (∀ threshold : {threshold // threshold ∈ thresholds},
          thresholdTraceCode thresholds
              (empiricalTrace sample classFun index₁) threshold =
            thresholdTraceCode thresholds
              (empiricalTrace sample classFun index₂) threshold) ->
        empiricalTrace sample classFun index₁ =
          empiricalTrace sample classFun index₂ := by
  exact
    thresholdTraceCode_separates_of_pointwise_thresholds_separate
      (pointwise_thresholds_separate_of_coordinate_thresholds_separate hcoordinate)

/--
If the finite threshold set contains every realized value at every sample
coordinate, then it separates those coordinate values: taking the threshold to
be one of the two candidate values rules out strict inequality in either
direction.
-/
theorem coordinate_thresholds_separate_of_values_mem_thresholds
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {thresholds : Finset ℝ}
    (hvalues :
      ∀ sampleIndex : Fin n,
        ∀ index, index ∈ indexClass ->
          classFun index (sample sampleIndex) ∈ thresholds) :
    ∀ sampleIndex : Fin n,
      ∀ index₁, index₁ ∈ indexClass ->
        ∀ index₂, index₂ ∈ indexClass ->
          (∀ threshold : {threshold // threshold ∈ thresholds},
            (threshold.1 < classFun index₁ (sample sampleIndex) ↔
              threshold.1 < classFun index₂ (sample sampleIndex))) ->
          classFun index₁ (sample sampleIndex) =
            classFun index₂ (sample sampleIndex) := by
  intro sampleIndex index₁ hindex₁ index₂ hindex₂ hthresholds
  let value₁ : ℝ := classFun index₁ (sample sampleIndex)
  let value₂ : ℝ := classFun index₂ (sample sampleIndex)
  have hvalue₁_mem : value₁ ∈ thresholds := hvalues sampleIndex index₁ hindex₁
  have hvalue₂_mem : value₂ ∈ thresholds := hvalues sampleIndex index₂ hindex₂
  have hnot_value₁_lt_value₂ : ¬ value₁ < value₂ := by
    intro hlt
    have hiff := hthresholds ⟨value₁, hvalue₁_mem⟩
    exact (lt_irrefl value₁) (hiff.mpr hlt)
  have hnot_value₂_lt_value₁ : ¬ value₂ < value₁ := by
    intro hlt
    have hiff := hthresholds ⟨value₂, hvalue₂_mem⟩
    exact (lt_irrefl value₂) (hiff.mp hlt)
  exact
    le_antisymm (le_of_not_gt hnot_value₂_lt_value₁)
      (le_of_not_gt hnot_value₁_lt_value₂)

/--
When all realized sample-coordinate values lie in the threshold set, finite
threshold signatures separate realized empirical traces.
-/
theorem thresholdTraceCode_separates_of_values_mem_thresholds
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {thresholds : Finset ℝ}
    (hvalues :
      ∀ sampleIndex : Fin n,
        ∀ index, index ∈ indexClass ->
          classFun index (sample sampleIndex) ∈ thresholds) :
    ∀ index₁, index₁ ∈ indexClass ->
      ∀ index₂, index₂ ∈ indexClass ->
        (∀ threshold : {threshold // threshold ∈ thresholds},
          thresholdTraceCode thresholds
              (empiricalTrace sample classFun index₁) threshold =
            thresholdTraceCode thresholds
              (empiricalTrace sample classFun index₂) threshold) ->
        empiricalTrace sample classFun index₁ =
          empiricalTrace sample classFun index₂ := by
  exact
    thresholdTraceCode_separates_of_coordinate_thresholds_separate
      (coordinate_thresholds_separate_of_values_mem_thresholds hvalues)

/-- Every realized empirical trace has a threshold code in the realized-code set. -/
theorem thresholdTraceCode_mem_thresholdTraceCodeSet
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {thresholds : Finset ℝ} {index : Index} (hindex : index ∈ indexClass) :
    thresholdTraceCode thresholds (empiricalTrace sample classFun index) ∈
      thresholdTraceCodeSet sample indexClass classFun thresholds := by
  classical
  rw [thresholdTraceCodeSet]
  simp only [Finset.mem_filter, Finset.mem_univ, true_and]
  intro threshold
  rw [thresholdTraceCode_empiricalTrace_eq_binaryTraceSet
    (sample := sample) (classFun := classFun)
    (thresholds := thresholds) (index := index) threshold]
  exact empiricalBinaryTraceSet_mem_family hindex

/--
If finite threshold signatures separate the realized empirical traces, then the
threshold-code map is injective on the trace image.
-/
theorem thresholdTraceCode_injOn_empiricalTrace_image_of_separates
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {thresholds : Finset ℝ}
    (hseparate :
      ∀ index₁, index₁ ∈ indexClass ->
        ∀ index₂, index₂ ∈ indexClass ->
          (∀ threshold : {threshold // threshold ∈ thresholds},
            thresholdTraceCode thresholds
                (empiricalTrace sample classFun index₁) threshold =
              thresholdTraceCode thresholds
                (empiricalTrace sample classFun index₂) threshold) ->
          empiricalTrace sample classFun index₁ =
            empiricalTrace sample classFun index₂) :
    Set.InjOn (thresholdTraceCode thresholds)
      (empiricalTrace sample classFun '' indexClass) := by
  intro trace₁ htrace₁ trace₂ htrace₂ hcode
  rcases htrace₁ with ⟨index₁, hindex₁, rfl⟩
  rcases htrace₂ with ⟨index₂, hindex₂, rfl⟩
  exact hseparate index₁ hindex₁ index₂ hindex₂ fun threshold =>
    congrFun hcode threshold

/--
Finite threshold signatures give a finite empirical trace image whenever they
separate the realized traces.
-/
theorem finite_empiricalTrace_image_of_thresholdTraceCode_separates
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {thresholds : Finset ℝ}
    (hseparate :
      ∀ index₁, index₁ ∈ indexClass ->
        ∀ index₂, index₂ ∈ indexClass ->
          (∀ threshold : {threshold // threshold ∈ thresholds},
            thresholdTraceCode thresholds
                (empiricalTrace sample classFun index₁) threshold =
              thresholdTraceCode thresholds
                (empiricalTrace sample classFun index₂) threshold) ->
          empiricalTrace sample classFun index₁ =
            empiricalTrace sample classFun index₂) :
    (empiricalTrace sample classFun '' indexClass).Finite := by
  exact
    finite_empiricalTrace_image_of_finite_code
      (sample := sample) (indexClass := indexClass) (classFun := classFun)
      (code := thresholdTraceCode thresholds)
      (codeSet := thresholdTraceCodeSet sample indexClass classFun thresholds)
      (by
        intro index hindex
        exact thresholdTraceCode_mem_thresholdTraceCodeSet hindex)
      (thresholdTraceCode_injOn_empiricalTrace_image_of_separates hseparate)

/--
Pointwise threshold-comparison separation gives a finite empirical trace image
through the finite threshold-code layer.
-/
theorem finite_empiricalTrace_image_of_pointwise_thresholds_separate
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {thresholds : Finset ℝ}
    (hpoint :
      ∀ index₁, index₁ ∈ indexClass ->
        ∀ index₂, index₂ ∈ indexClass ->
          (∀ sampleIndex : Fin n,
            ∀ threshold : {threshold // threshold ∈ thresholds},
              (threshold.1 < classFun index₁ (sample sampleIndex) ↔
                threshold.1 < classFun index₂ (sample sampleIndex))) ->
          empiricalTrace sample classFun index₁ =
            empiricalTrace sample classFun index₂) :
    (empiricalTrace sample classFun '' indexClass).Finite := by
  exact
    finite_empiricalTrace_image_of_thresholdTraceCode_separates
      (thresholdTraceCode_separates_of_pointwise_thresholds_separate hpoint)

/--
Coordinatewise threshold separation gives a finite empirical trace image
through the finite threshold-code layer.
-/
theorem finite_empiricalTrace_image_of_coordinate_thresholds_separate
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {thresholds : Finset ℝ}
    (hcoordinate :
      ∀ sampleIndex : Fin n,
        ∀ index₁, index₁ ∈ indexClass ->
          ∀ index₂, index₂ ∈ indexClass ->
            (∀ threshold : {threshold // threshold ∈ thresholds},
              (threshold.1 < classFun index₁ (sample sampleIndex) ↔
                threshold.1 < classFun index₂ (sample sampleIndex))) ->
            classFun index₁ (sample sampleIndex) =
              classFun index₂ (sample sampleIndex)) :
    (empiricalTrace sample classFun '' indexClass).Finite := by
  exact
    finite_empiricalTrace_image_of_thresholdTraceCode_separates
      (thresholdTraceCode_separates_of_coordinate_thresholds_separate hcoordinate)

/--
If all realized sample-coordinate values lie in the finite threshold set, then
the empirical trace image is finite.
-/
theorem finite_empiricalTrace_image_of_values_mem_thresholds
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {thresholds : Finset ℝ}
    (hvalues :
      ∀ sampleIndex : Fin n,
        ∀ index, index ∈ indexClass ->
          classFun index (sample sampleIndex) ∈ thresholds) :
    (empiricalTrace sample classFun '' indexClass).Finite := by
  exact
    finite_empiricalTrace_image_of_thresholdTraceCode_separates
      (thresholdTraceCode_separates_of_values_mem_thresholds hvalues)

/--
The cardinality of a trace image separated by finite threshold signatures is
bounded by the number of realized threshold signatures.
-/
theorem empiricalTrace_image_toFinset_card_le_thresholdTraceCodeSet_card
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {thresholds : Finset ℝ}
    (hseparate :
      ∀ index₁, index₁ ∈ indexClass ->
        ∀ index₂, index₂ ∈ indexClass ->
          (∀ threshold : {threshold // threshold ∈ thresholds},
            thresholdTraceCode thresholds
                (empiricalTrace sample classFun index₁) threshold =
              thresholdTraceCode thresholds
                (empiricalTrace sample classFun index₂) threshold) ->
          empiricalTrace sample classFun index₁ =
            empiricalTrace sample classFun index₂) :
    (finite_empiricalTrace_image_of_thresholdTraceCode_separates hseparate).toFinset.card ≤
      (thresholdTraceCodeSet sample indexClass classFun thresholds).card := by
  exact
    empiricalTrace_image_toFinset_card_le_finite_code
      (sample := sample) (indexClass := indexClass) (classFun := classFun)
      (code := thresholdTraceCode thresholds)
      (codeSet := thresholdTraceCodeSet sample indexClass classFun thresholds)
      (by
        intro index hindex
        exact thresholdTraceCode_mem_thresholdTraceCodeSet hindex)
      (thresholdTraceCode_injOn_empiricalTrace_image_of_separates hseparate)

/--
The realized threshold-signature set is bounded by the Cartesian product of the
realized binary trace families at the individual thresholds.
-/
theorem thresholdTraceCodeSet_card_le_pi_binaryTraceSetFamily_card
    {Observation : Type u} {Index : Type v} {n : ℕ}
    (sample : SampleAt Observation n)
    (indexClass : Set Index) (classFun : Index -> Observation -> ℝ)
    (thresholds : Finset ℝ) :
    (thresholdTraceCodeSet sample indexClass classFun thresholds).card ≤
      ∏ threshold ∈ thresholds.attach,
        (empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)).card := by
  classical
  let piSet :
      Finset (∀ threshold, threshold ∈ thresholds.attach -> Finset (Fin n)) :=
    thresholds.attach.pi fun threshold =>
      empiricalBinaryTraceSetFamily sample indexClass
        (thresholdIndicatorClassFun classFun threshold.1)
  let restrictCode :
      ({threshold // threshold ∈ thresholds} -> Finset (Fin n)) ->
        (∀ threshold, threshold ∈ thresholds.attach -> Finset (Fin n)) :=
    fun code threshold _hthreshold => code threshold
  have hmaps :
      Set.MapsTo restrictCode
        (thresholdTraceCodeSet sample indexClass classFun thresholds : Set
          ({threshold // threshold ∈ thresholds} -> Finset (Fin n)))
        (piSet : Set (∀ threshold, threshold ∈ thresholds.attach -> Finset (Fin n))) := by
    intro code hcode
    change restrictCode code ∈
      thresholds.attach.pi fun threshold =>
        empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)
    exact Finset.mem_pi.mpr fun threshold _hthreshold =>
      (Finset.mem_filter.mp hcode).2 threshold
  have hinj :
      Set.InjOn restrictCode
        (thresholdTraceCodeSet sample indexClass classFun thresholds : Set
          ({threshold // threshold ∈ thresholds} -> Finset (Fin n))) := by
    intro code₁ _hcode₁ code₂ _hcode₂ hrestrict
    funext threshold
    exact congrFun (congrFun hrestrict threshold) (Finset.mem_attach thresholds threshold)
  have hcard :
      (thresholdTraceCodeSet sample indexClass classFun thresholds).card ≤
        piSet.card :=
    Finset.card_le_card_of_injOn restrictCode hmaps hinj
  simpa [piSet] using hcard

/--
The set of finite-threshold codes realized by `indexClass` is finite.  Unlike
the exact-separation trace-image route, this keeps only the threshold
signature image; later approximate-grid arguments use it as a finite
approximation code.
-/
theorem finite_thresholdTraceCode_image
    {Observation : Type u} {Index : Type v} {n : ℕ}
    (sample : SampleAt Observation n)
    (indexClass : Set Index) (classFun : Index -> Observation -> ℝ)
    (thresholds : Finset ℝ) :
    ((fun index =>
        thresholdTraceCode thresholds (empiricalTrace sample classFun index)) ''
      indexClass).Finite := by
  classical
  have hsubset :
      ((fun index =>
          thresholdTraceCode thresholds (empiricalTrace sample classFun index)) ''
        indexClass) ⊆
        (thresholdTraceCodeSet sample indexClass classFun thresholds : Set
          ({threshold // threshold ∈ thresholds} -> Finset (Fin n))) := by
    rintro code ⟨index, hindex, rfl⟩
    exact thresholdTraceCode_mem_thresholdTraceCodeSet hindex
  exact
    (thresholdTraceCodeSet sample indexClass classFun thresholds).finite_toSet.subset
      hsubset

/--
The realized finite-threshold code image has cardinality bounded by the
ambient realized-code set.
-/
theorem thresholdTraceCode_image_toFinset_card_le_thresholdTraceCodeSet_card
    {Observation : Type u} {Index : Type v} {n : ℕ}
    (sample : SampleAt Observation n)
    (indexClass : Set Index) (classFun : Index -> Observation -> ℝ)
    (thresholds : Finset ℝ) :
    (finite_thresholdTraceCode_image sample indexClass classFun thresholds).toFinset.card ≤
      (thresholdTraceCodeSet sample indexClass classFun thresholds).card := by
  classical
  let codeImage : Set ({threshold // threshold ∈ thresholds} -> Finset (Fin n)) :=
    (fun index =>
        thresholdTraceCode thresholds (empiricalTrace sample classFun index)) ''
      indexClass
  let codeSet : Finset ({threshold // threshold ∈ thresholds} -> Finset (Fin n)) :=
    thresholdTraceCodeSet sample indexClass classFun thresholds
  have hsubset : codeImage ⊆ (codeSet : Set
      ({threshold // threshold ∈ thresholds} -> Finset (Fin n))) := by
    rintro code ⟨index, hindex, rfl⟩
    exact thresholdTraceCode_mem_thresholdTraceCodeSet hindex
  have hfinite : codeImage.Finite :=
    finite_thresholdTraceCode_image sample indexClass classFun thresholds
  have hle :
      codeImage.ncard ≤ (codeSet : Set
        ({threshold // threshold ∈ thresholds} -> Finset (Fin n))).ncard :=
    Set.ncard_le_ncard hsubset codeSet.finite_toSet
  simpa [codeImage, codeSet, Set.ncard_eq_toFinset_card codeImage hfinite]
    using hle

/--
Approximate empirical-cover bridge from finite threshold signatures.  If
matching all threshold comparisons on a coordinate forces the two realized
values to be within `epsilon`, then the threshold signature is a finite
`L1(P_n)` approximation code.
-/
theorem nonempty_finiteEmpiricalL1CoverAtCard_of_thresholdTraceCode_coordinate_approx_card_le
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {thresholds : Finset ℝ} {epsilon : ℝ} {cardinality : ℕ}
    (hepsilon_nonneg : 0 ≤ epsilon)
    (hcoordinate :
      ∀ sampleIndex : Fin n,
        ∀ index, index ∈ indexClass ->
          ∀ center, center ∈ indexClass ->
            (∀ threshold : {threshold // threshold ∈ thresholds},
              (threshold.1 < classFun index (sample sampleIndex) ↔
                threshold.1 < classFun center (sample sampleIndex))) ->
            |classFun index (sample sampleIndex) -
              classFun center (sample sampleIndex)| ≤ epsilon)
    (hindexClass : ∃ index, index ∈ indexClass)
    (hcard_le :
      (finite_thresholdTraceCode_image sample indexClass classFun thresholds).toFinset.card ≤
        cardinality) :
    Nonempty
      (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
        cardinality) := by
  exact
    nonempty_finiteEmpiricalL1CoverAtCard_of_finite_pointwise_approx_code_card_le
      (fun index =>
        thresholdTraceCode thresholds (empiricalTrace sample classFun index))
      (finite_thresholdTraceCode_image sample indexClass classFun thresholds)
      hepsilon_nonneg
      (fun index hindex center hcenter hcode sampleIndex =>
        hcoordinate sampleIndex index hindex center hcenter
          (fun threshold =>
            by
              have hiff :=
                (thresholdTraceCode_eq_iff_forall_threshold_sample.mp hcode)
                  threshold sampleIndex
              simpa [empiricalTrace] using hiff))
      hindexClass hcard_le

/--
Approximate empirical-cover witness from threshold signatures with the terminal
cardinality bounded directly by the full finite threshold-code set.
-/
theorem nonempty_finiteEmpiricalL1CoverAtCard_of_thresholdTraceCode_coordinate_approx_codeSet_card_le
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {thresholds : Finset ℝ} {epsilon : ℝ} {cardinality : ℕ}
    (hepsilon_nonneg : 0 ≤ epsilon)
    (hcoordinate :
      ∀ sampleIndex : Fin n,
        ∀ index, index ∈ indexClass ->
          ∀ center, center ∈ indexClass ->
            (∀ threshold : {threshold // threshold ∈ thresholds},
              (threshold.1 < classFun index (sample sampleIndex) ↔
                threshold.1 < classFun center (sample sampleIndex))) ->
            |classFun index (sample sampleIndex) -
              classFun center (sample sampleIndex)| ≤ epsilon)
    (hindexClass : ∃ index, index ∈ indexClass)
    (hcard_le :
      (thresholdTraceCodeSet sample indexClass classFun thresholds).card ≤
        cardinality) :
    Nonempty
      (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
        cardinality) := by
  exact
    nonempty_finiteEmpiricalL1CoverAtCard_of_thresholdTraceCode_coordinate_approx_card_le
      (sample := sample) (indexClass := indexClass) (classFun := classFun)
      (thresholds := thresholds) hepsilon_nonneg hcoordinate hindexClass
      ((thresholdTraceCode_image_toFinset_card_le_thresholdTraceCodeSet_card
        sample indexClass classFun thresholds).trans hcard_le)

/--
Numeric empirical-covering-number bound from finite threshold signatures and a
coordinatewise approximate-separation hypothesis.
-/
theorem empiricalL1CoveringNumber_le_of_thresholdTraceCode_coordinate_approx_card_le
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {thresholds : Finset ℝ} {epsilon : ℝ} {cardinality : ℕ}
    (hepsilon_nonneg : 0 ≤ epsilon)
    (hcoordinate :
      ∀ sampleIndex : Fin n,
        ∀ index, index ∈ indexClass ->
          ∀ center, center ∈ indexClass ->
            (∀ threshold : {threshold // threshold ∈ thresholds},
              (threshold.1 < classFun index (sample sampleIndex) ↔
                threshold.1 < classFun center (sample sampleIndex))) ->
            |classFun index (sample sampleIndex) -
              classFun center (sample sampleIndex)| ≤ epsilon)
    (hcard_le :
      (finite_thresholdTraceCode_image sample indexClass classFun thresholds).toFinset.card ≤
        cardinality) :
    empiricalL1CoveringNumber sample indexClass classFun epsilon ≤
      (cardinality : ℕ∞) := by
  exact
    empiricalL1CoveringNumber_le_of_finite_pointwise_approx_code_card_le
      (fun index =>
        thresholdTraceCode thresholds (empiricalTrace sample classFun index))
      (finite_thresholdTraceCode_image sample indexClass classFun thresholds)
      hepsilon_nonneg
      (fun index hindex center hcenter hcode sampleIndex =>
        hcoordinate sampleIndex index hindex center hcenter
          (fun threshold =>
            by
              have hiff :=
                (thresholdTraceCode_eq_iff_forall_threshold_sample.mp hcode)
                  threshold sampleIndex
              simpa [empiricalTrace] using hiff))
      hcard_le

/--
Approximate empirical-cover bridge from threshold signatures with the terminal
cardinality bounded directly by the full finite threshold-code set.

This is the code-set form of
`empiricalL1CoveringNumber_le_of_thresholdTraceCode_coordinate_approx_card_le`;
it lets later VC/grid arguments consume `thresholdTraceCodeSet` cardinality
estimates without reopening the product-of-threshold-families proof.
-/
theorem empiricalL1CoveringNumber_le_of_thresholdTraceCode_coordinate_approx_codeSet_card_le
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {thresholds : Finset ℝ} {epsilon : ℝ} {cardinality : ℕ}
    (hepsilon_nonneg : 0 ≤ epsilon)
    (hcoordinate :
      ∀ sampleIndex : Fin n,
        ∀ index, index ∈ indexClass ->
          ∀ center, center ∈ indexClass ->
            (∀ threshold : {threshold // threshold ∈ thresholds},
              (threshold.1 < classFun index (sample sampleIndex) ↔
                threshold.1 < classFun center (sample sampleIndex))) ->
            |classFun index (sample sampleIndex) -
              classFun center (sample sampleIndex)| ≤ epsilon)
    (hcard_le :
      (thresholdTraceCodeSet sample indexClass classFun thresholds).card ≤
        cardinality) :
    empiricalL1CoveringNumber sample indexClass classFun epsilon ≤
      (cardinality : ℕ∞) := by
  exact
    empiricalL1CoveringNumber_le_of_thresholdTraceCode_coordinate_approx_card_le
      (sample := sample) (indexClass := indexClass) (classFun := classFun)
      (thresholds := thresholds) hepsilon_nonneg hcoordinate
      ((thresholdTraceCode_image_toFinset_card_le_thresholdTraceCodeSet_card
        sample indexClass classFun thresholds).trans hcard_le)

/--
Approximate empirical-cover bridge from threshold signatures with the terminal
cardinality bounded by the product of the fixed-threshold binary trace-family
cardinalities.
-/
theorem empiricalL1CoveringNumber_le_of_thresholdTraceCode_coordinate_approx_product_card_le
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {thresholds : Finset ℝ} {epsilon : ℝ} {cardinality : ℕ}
    (hepsilon_nonneg : 0 ≤ epsilon)
    (hcoordinate :
      ∀ sampleIndex : Fin n,
        ∀ index, index ∈ indexClass ->
          ∀ center, center ∈ indexClass ->
            (∀ threshold : {threshold // threshold ∈ thresholds},
              (threshold.1 < classFun index (sample sampleIndex) ↔
                threshold.1 < classFun center (sample sampleIndex))) ->
            |classFun index (sample sampleIndex) -
              classFun center (sample sampleIndex)| ≤ epsilon)
    (hcard_le :
      (∏ threshold ∈ thresholds.attach,
          (empiricalBinaryTraceSetFamily sample indexClass
            (thresholdIndicatorClassFun classFun threshold.1)).card) ≤
        cardinality) :
    empiricalL1CoveringNumber sample indexClass classFun epsilon ≤
      (cardinality : ℕ∞) := by
  refine
    empiricalL1CoveringNumber_le_of_thresholdTraceCode_coordinate_approx_card_le
      (sample := sample) (indexClass := indexClass) (classFun := classFun)
      (thresholds := thresholds) hepsilon_nonneg hcoordinate ?_
  exact
    (thresholdTraceCode_image_toFinset_card_le_thresholdTraceCodeSet_card
      sample indexClass classFun thresholds).trans
      ((thresholdTraceCodeSet_card_le_pi_binaryTraceSetFamily_card
        sample indexClass classFun thresholds).trans hcard_le)

/--
If every interval of length greater than `epsilon` contains a threshold, then
two real values with the same threshold comparisons are within `epsilon`.
This is the deterministic grid lemma behind approximate threshold coding.
-/
theorem abs_sub_le_of_forall_gap_exists_threshold
    {thresholds : Finset ℝ} {epsilon x y : ℝ}
    (hepsilon_nonneg : 0 ≤ epsilon)
    (hgrid :
      ∀ a b : ℝ, a < b -> epsilon < b - a ->
        ∃ threshold : {threshold // threshold ∈ thresholds},
          a ≤ threshold.1 ∧ threshold.1 < b)
    (hcompare :
      ∀ threshold : {threshold // threshold ∈ thresholds},
        (threshold.1 < x ↔ threshold.1 < y)) :
    |x - y| ≤ epsilon := by
  by_cases hxy : x ≤ y
  · have hyx_le : y - x ≤ epsilon := by
      by_contra hnot
      have hgap : epsilon < y - x := lt_of_not_ge hnot
      have hlt : x < y := by
        by_contra hnot_lt
        have hyx : y ≤ x := le_of_not_gt hnot_lt
        have hsub_nonpos : y - x ≤ 0 := sub_nonpos.mpr hyx
        linarith
      rcases hgrid x y hlt hgap with ⟨threshold, hx_le_t, ht_lt_y⟩
      have ht_lt_x : threshold.1 < x := (hcompare threshold).mpr ht_lt_y
      exact (not_lt_of_ge hx_le_t) ht_lt_x
    rw [abs_of_nonpos (sub_nonpos.mpr hxy)]
    linarith
  · have hyx : y < x := lt_of_not_ge hxy
    have hxy_le : x - y ≤ epsilon := by
      by_contra hnot
      have hgap : epsilon < x - y := lt_of_not_ge hnot
      rcases hgrid y x hyx hgap with ⟨threshold, hy_le_t, ht_lt_x⟩
      have ht_lt_y : threshold.1 < y := (hcompare threshold).mp ht_lt_x
      exact (not_lt_of_ge hy_le_t) ht_lt_y
    rw [abs_of_pos (sub_pos.mpr hyx)]
    exact hxy_le

/--
Finite arithmetic threshold grid made of integer multiples of `epsilon` inside
the symmetric integer interval `[-bound, bound]`.
-/
noncomputable def integerMultipleThresholdGrid (epsilon : ℝ) (bound : ℤ) :
    Finset ℝ := by
  classical
  exact (Finset.Icc (-bound) bound).image fun gridIndex : ℤ =>
    epsilon * (gridIndex : ℝ)

/-- The integer-multiple threshold grid has no more points than its source
integer interval. -/
theorem integerMultipleThresholdGrid_card_le (epsilon : ℝ) (bound : ℤ) :
    (integerMultipleThresholdGrid epsilon bound).card ≤ (2 * bound + 1).toNat := by
  classical
  dsimp [integerMultipleThresholdGrid]
  exact Finset.card_image_le.trans_eq (card_int_symmetric_Icc bound)

/-- Natural-number version of the symmetric integer-multiple grid-cardinality
bound. -/
theorem integerMultipleThresholdGrid_nat_card_le (epsilon : ℝ) (bound : ℕ) :
    (integerMultipleThresholdGrid epsilon (bound : ℤ)).card ≤ 2 * bound + 1 := by
  simpa using integerMultipleThresholdGrid_card_le epsilon (bound : ℤ)

/--
If `a` and `b` lie in the bounded interval covered by the integer-multiple
threshold grid and `b - a > epsilon`, then one grid threshold lies in
`[a, b)`.
-/
theorem exists_integerMultipleThresholdGrid_between_of_bounds
    {epsilon a b : ℝ} {bound : ℤ}
    (hepsilon_pos : 0 < epsilon)
    (ha_bound : (-(bound : ℝ)) * epsilon ≤ a)
    (hb_bound : b ≤ (bound : ℝ) * epsilon)
    (_hab : a < b) (hgap : epsilon < b - a) :
    ∃ threshold : {threshold // threshold ∈
        integerMultipleThresholdGrid epsilon bound},
      a ≤ threshold.1 ∧ threshold.1 < b := by
  classical
  let gridIndex : ℤ := ⌈a / epsilon⌉
  have hepsilon_ne : epsilon ≠ 0 := ne_of_gt hepsilon_pos
  have hneg_bound_le_div : -(bound : ℝ) ≤ a / epsilon := by
    rw [le_div_iff₀ hepsilon_pos]
    simpa using ha_bound
  have hceil_ge : a / epsilon ≤ (gridIndex : ℝ) := by
    simpa [gridIndex] using (Int.le_ceil (a / epsilon))
  have hgridIndex_lower_real : ((-bound : ℤ) : ℝ) ≤ (gridIndex : ℝ) := by
    have hcast : ((-bound : ℤ) : ℝ) = -(bound : ℝ) := by norm_num
    rw [hcast]
    exact hneg_bound_le_div.trans hceil_ge
  have hgridIndex_lower : -bound ≤ gridIndex := by
    exact_mod_cast hgridIndex_lower_real
  have ha_add_epsilon_lt_b : a + epsilon < b := by
    linarith
  have hdiv_upper : a / epsilon + 1 < (bound : ℝ) := by
    have hmul : a + epsilon < (bound : ℝ) * epsilon :=
      ha_add_epsilon_lt_b.trans_le hb_bound
    have hdiv : (a + epsilon) / epsilon < (bound : ℝ) := by
      rw [div_lt_iff₀ hepsilon_pos]
      simpa [mul_comm] using hmul
    have hrewrite : (a + epsilon) / epsilon = a / epsilon + 1 := by
      field_simp [hepsilon_ne]
    simpa [hrewrite] using hdiv
  have hceil_lt_add : (gridIndex : ℝ) < a / epsilon + 1 := by
    simpa [gridIndex] using (Int.ceil_lt_add_one (a / epsilon))
  have hgridIndex_upper_real : (gridIndex : ℝ) < (bound : ℝ) :=
    hceil_lt_add.trans hdiv_upper
  have hgridIndex_upper : gridIndex ≤ bound := by
    exact_mod_cast le_of_lt hgridIndex_upper_real
  let threshold : ℝ := epsilon * (gridIndex : ℝ)
  have hthreshold_mem :
      threshold ∈ integerMultipleThresholdGrid epsilon bound := by
    refine Finset.mem_image.mpr ?_
    exact ⟨gridIndex, Finset.mem_Icc.mpr
      ⟨hgridIndex_lower, hgridIndex_upper⟩, rfl⟩
  refine ⟨⟨threshold, hthreshold_mem⟩, ?_, ?_⟩
  · dsimp [threshold]
    have hmul := mul_le_mul_of_nonneg_left hceil_ge hepsilon_pos.le
    have hleft : epsilon * (a / epsilon) = a := by
      field_simp [hepsilon_ne]
    linarith
  · dsimp [threshold]
    have hceil_lt : (gridIndex : ℝ) < a / epsilon + 1 := hceil_lt_add
    have hmul := mul_lt_mul_of_pos_left hceil_lt hepsilon_pos
    have hright : epsilon * (a / epsilon + 1) = a + epsilon := by
      field_simp [hepsilon_ne]
    linarith

/--
Bounded variant of the deterministic threshold-grid lemma.  If `x` and `y`
are known to lie in `[lower, upper]`, it is enough for the threshold grid to
hit gaps inside that interval.
-/
theorem abs_sub_le_of_forall_bounded_gap_exists_threshold
    {thresholds : Finset ℝ} {epsilon lower upper x y : ℝ}
    (hepsilon_nonneg : 0 ≤ epsilon)
    (hx_bounds : lower ≤ x ∧ x ≤ upper)
    (hy_bounds : lower ≤ y ∧ y ≤ upper)
    (hgrid :
      ∀ a b : ℝ, lower ≤ a -> b ≤ upper -> a < b ->
        epsilon < b - a ->
          ∃ threshold : {threshold // threshold ∈ thresholds},
            a ≤ threshold.1 ∧ threshold.1 < b)
    (hcompare :
      ∀ threshold : {threshold // threshold ∈ thresholds},
        (threshold.1 < x ↔ threshold.1 < y)) :
    |x - y| ≤ epsilon := by
  by_cases hxy : x ≤ y
  · have hyx_le : y - x ≤ epsilon := by
      by_contra hnot
      have hgap : epsilon < y - x := lt_of_not_ge hnot
      have hlt : x < y := by
        by_contra hnot_lt
        have hyx : y ≤ x := le_of_not_gt hnot_lt
        have hsub_nonpos : y - x ≤ 0 := sub_nonpos.mpr hyx
        linarith
      rcases hgrid x y hx_bounds.1 hy_bounds.2 hlt hgap with
        ⟨threshold, hx_le_t, ht_lt_y⟩
      have ht_lt_x : threshold.1 < x := (hcompare threshold).mpr ht_lt_y
      exact (not_lt_of_ge hx_le_t) ht_lt_x
    rw [abs_of_nonpos (sub_nonpos.mpr hxy)]
    linarith
  · have hyx : y < x := lt_of_not_ge hxy
    have hxy_le : x - y ≤ epsilon := by
      by_contra hnot
      have hgap : epsilon < x - y := lt_of_not_ge hnot
      rcases hgrid y x hy_bounds.1 hx_bounds.2 hyx hgap with
        ⟨threshold, hy_le_t, ht_lt_x⟩
      have ht_lt_y : threshold.1 < y := (hcompare threshold).mp ht_lt_x
      exact (not_lt_of_ge hy_le_t) ht_lt_y
    rw [abs_of_pos (sub_pos.mpr hyx)]
    exact hxy_le

/--
Threshold-grid empirical-covering-number bound: a finite threshold grid whose
points hit every gap wider than `epsilon` makes matching threshold signatures
an `epsilon`-accurate empirical `L1(P_n)` code.
-/
theorem empiricalL1CoveringNumber_le_of_thresholdTraceCode_gap_grid_product_card_le
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {thresholds : Finset ℝ} {epsilon : ℝ} {cardinality : ℕ}
    (hepsilon_nonneg : 0 ≤ epsilon)
    (hgrid :
      ∀ a b : ℝ, a < b -> epsilon < b - a ->
        ∃ threshold : {threshold // threshold ∈ thresholds},
          a ≤ threshold.1 ∧ threshold.1 < b)
    (hcard_le :
      (∏ threshold ∈ thresholds.attach,
          (empiricalBinaryTraceSetFamily sample indexClass
            (thresholdIndicatorClassFun classFun threshold.1)).card) ≤
        cardinality) :
    empiricalL1CoveringNumber sample indexClass classFun epsilon ≤
      (cardinality : ℕ∞) := by
  exact
    empiricalL1CoveringNumber_le_of_thresholdTraceCode_coordinate_approx_product_card_le
      (sample := sample) (indexClass := indexClass) (classFun := classFun)
      (thresholds := thresholds) hepsilon_nonneg
      (fun sampleIndex index hindex center hcenter hcompare =>
        abs_sub_le_of_forall_gap_exists_threshold hepsilon_nonneg hgrid
          hcompare)
      hcard_le

/--
Composed threshold-coding cardinality bound for real empirical traces:
if finite threshold signatures separate the trace image, then the trace-image
cardinality is bounded by the product of the individual threshold binary trace
family cardinalities.
-/
theorem empiricalTrace_image_toFinset_card_le_pi_binaryTraceSetFamily_card
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {thresholds : Finset ℝ}
    (hseparate :
      ∀ index₁, index₁ ∈ indexClass ->
        ∀ index₂, index₂ ∈ indexClass ->
          (∀ threshold : {threshold // threshold ∈ thresholds},
            thresholdTraceCode thresholds
                (empiricalTrace sample classFun index₁) threshold =
              thresholdTraceCode thresholds
                (empiricalTrace sample classFun index₂) threshold) ->
          empiricalTrace sample classFun index₁ =
            empiricalTrace sample classFun index₂) :
    (finite_empiricalTrace_image_of_thresholdTraceCode_separates hseparate).toFinset.card ≤
      ∏ threshold ∈ thresholds.attach,
        (empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)).card :=
  (empiricalTrace_image_toFinset_card_le_thresholdTraceCodeSet_card hseparate).trans
    (thresholdTraceCodeSet_card_le_pi_binaryTraceSetFamily_card
      sample indexClass classFun thresholds)

/--
Pointwise threshold-comparison separation bounds the empirical trace-image
cardinality by the product of the fixed-threshold binary trace-family
cardinalities.
-/
theorem empiricalTrace_image_toFinset_card_le_pi_binaryTraceSetFamily_card_of_pointwise_thresholds_separate
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {thresholds : Finset ℝ}
    (hpoint :
      ∀ index₁, index₁ ∈ indexClass ->
        ∀ index₂, index₂ ∈ indexClass ->
          (∀ sampleIndex : Fin n,
            ∀ threshold : {threshold // threshold ∈ thresholds},
              (threshold.1 < classFun index₁ (sample sampleIndex) ↔
                threshold.1 < classFun index₂ (sample sampleIndex))) ->
          empiricalTrace sample classFun index₁ =
            empiricalTrace sample classFun index₂) :
    (finite_empiricalTrace_image_of_pointwise_thresholds_separate hpoint).toFinset.card ≤
      ∏ threshold ∈ thresholds.attach,
        (empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)).card :=
  empiricalTrace_image_toFinset_card_le_pi_binaryTraceSetFamily_card
    (thresholdTraceCode_separates_of_pointwise_thresholds_separate hpoint)

/--
Coordinatewise threshold separation bounds the empirical trace-image
cardinality by the product of the fixed-threshold binary trace-family
cardinalities.
-/
theorem empiricalTrace_image_toFinset_card_le_pi_binaryTraceSetFamily_card_of_coordinate_thresholds_separate
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {thresholds : Finset ℝ}
    (hcoordinate :
      ∀ sampleIndex : Fin n,
        ∀ index₁, index₁ ∈ indexClass ->
          ∀ index₂, index₂ ∈ indexClass ->
            (∀ threshold : {threshold // threshold ∈ thresholds},
              (threshold.1 < classFun index₁ (sample sampleIndex) ↔
                threshold.1 < classFun index₂ (sample sampleIndex))) ->
            classFun index₁ (sample sampleIndex) =
              classFun index₂ (sample sampleIndex)) :
    (finite_empiricalTrace_image_of_coordinate_thresholds_separate hcoordinate).toFinset.card ≤
      ∏ threshold ∈ thresholds.attach,
        (empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)).card :=
  empiricalTrace_image_toFinset_card_le_pi_binaryTraceSetFamily_card
    (thresholdTraceCode_separates_of_coordinate_thresholds_separate hcoordinate)

/--
Threshold-product cardinality estimates feed directly into the real
natural-polynomial trace-cardinality shape used by the Theorem 2.4.3 entropy
constructors.
-/
theorem empiricalTrace_image_card_add_one_real_le_of_thresholdTraceCode_product_bound
    {Observation : Type u} {Index : Type v} {n d : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {thresholds : Finset ℝ} {C : ℝ}
    (hseparate :
      ∀ index₁, index₁ ∈ indexClass ->
        ∀ index₂, index₂ ∈ indexClass ->
          (∀ threshold : {threshold // threshold ∈ thresholds},
            thresholdTraceCode thresholds
                (empiricalTrace sample classFun index₁) threshold =
              thresholdTraceCode thresholds
                (empiricalTrace sample classFun index₂) threshold) ->
          empiricalTrace sample classFun index₁ =
            empiricalTrace sample classFun index₂)
    (hproduct_bound :
      (((∏ threshold ∈ thresholds.attach,
        (empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)).card : ℕ) : ℝ) + 1) ≤
        C * (((n + 1 : ℕ) : ℝ) ^ d)) :
    (((finite_empiricalTrace_image_of_thresholdTraceCode_separates hseparate).toFinset.card : ℝ) + 1) ≤
      C * (((n + 1 : ℕ) : ℝ) ^ d) := by
  have htrace_le :
      (finite_empiricalTrace_image_of_thresholdTraceCode_separates hseparate).toFinset.card ≤
        ∏ threshold ∈ thresholds.attach,
          (empiricalBinaryTraceSetFamily sample indexClass
            (thresholdIndicatorClassFun classFun threshold.1)).card :=
    empiricalTrace_image_toFinset_card_le_pi_binaryTraceSetFamily_card hseparate
  have htrace_le_real :
      (((finite_empiricalTrace_image_of_thresholdTraceCode_separates hseparate).toFinset.card : ℝ) + 1) ≤
        ((∏ threshold ∈ thresholds.attach,
          (empiricalBinaryTraceSetFamily sample indexClass
            (thresholdIndicatorClassFun classFun threshold.1)).card : ℕ) : ℝ) + 1 := by
    exact_mod_cast Nat.add_le_add_right htrace_le 1
  exact htrace_le_real.trans hproduct_bound

/--
Factorwise cardinality bounds for the fixed-threshold binary trace families
produce the corresponding product bound.
-/
theorem threshold_binaryTraceSetFamily_product_card_le_of_forall_card_le
    {Observation : Type u} {Index : Type v} {n : ℕ}
    (sample : SampleAt Observation n)
    (indexClass : Set Index) (classFun : Index -> Observation -> ℝ)
    (thresholds : Finset ℝ)
    (bound : {threshold // threshold ∈ thresholds} -> ℕ)
    (hbound :
      ∀ threshold : {threshold // threshold ∈ thresholds},
        (empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)).card ≤
          bound threshold) :
    (∏ threshold ∈ thresholds.attach,
        (empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)).card) ≤
      ∏ threshold ∈ thresholds.attach, bound threshold :=
  Finset.prod_le_prod' fun threshold _hthreshold => hbound threshold

/--
Per-threshold cardinality bounds plus a polynomial estimate on their product
feed the threshold-coded empirical trace image into the Theorem 2.4.3
natural-polynomial entropy shape.
-/
theorem empiricalTrace_image_card_add_one_real_le_of_thresholdTraceCode_factor_bound
    {Observation : Type u} {Index : Type v} {n d : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {thresholds : Finset ℝ} {C : ℝ}
    (bound : {threshold // threshold ∈ thresholds} -> ℕ)
    (hseparate :
      ∀ index₁, index₁ ∈ indexClass ->
        ∀ index₂, index₂ ∈ indexClass ->
          (∀ threshold : {threshold // threshold ∈ thresholds},
            thresholdTraceCode thresholds
                (empiricalTrace sample classFun index₁) threshold =
              thresholdTraceCode thresholds
                (empiricalTrace sample classFun index₂) threshold) ->
          empiricalTrace sample classFun index₁ =
            empiricalTrace sample classFun index₂)
    (hfactor_bound :
      ∀ threshold : {threshold // threshold ∈ thresholds},
        (empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)).card ≤
          bound threshold)
    (hbound_product :
      (((∏ threshold ∈ thresholds.attach, bound threshold : ℕ) : ℝ) + 1) ≤
        C * (((n + 1 : ℕ) : ℝ) ^ d)) :
    (((finite_empiricalTrace_image_of_thresholdTraceCode_separates hseparate).toFinset.card : ℝ) + 1) ≤
      C * (((n + 1 : ℕ) : ℝ) ^ d) := by
  have hproduct_nat :
      (∏ threshold ∈ thresholds.attach,
          (empiricalBinaryTraceSetFamily sample indexClass
            (thresholdIndicatorClassFun classFun threshold.1)).card) ≤
        ∏ threshold ∈ thresholds.attach, bound threshold :=
    threshold_binaryTraceSetFamily_product_card_le_of_forall_card_le
      sample indexClass classFun thresholds bound hfactor_bound
  have hproduct_real :
      (((∏ threshold ∈ thresholds.attach,
        (empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)).card : ℕ) : ℝ) + 1) ≤
        ((∏ threshold ∈ thresholds.attach, bound threshold : ℕ) : ℝ) + 1 := by
    exact_mod_cast Nat.add_le_add_right hproduct_nat 1
  exact
    empiricalTrace_image_card_add_one_real_le_of_thresholdTraceCode_product_bound
      (sample := sample) (indexClass := indexClass) (classFun := classFun)
      (thresholds := thresholds) (C := C) hseparate
      (hproduct_real.trans hbound_product)

/--
A common cardinality bound for every fixed-threshold binary trace family gives
the simple product bound `base ^ #thresholds`.
-/
theorem threshold_binaryTraceSetFamily_product_card_le_const_pow
    {Observation : Type u} {Index : Type v} {n : ℕ}
    (sample : SampleAt Observation n)
    (indexClass : Set Index) (classFun : Index -> Observation -> ℝ)
    (thresholds : Finset ℝ) (base : ℕ)
    (hbase :
      ∀ threshold : {threshold // threshold ∈ thresholds},
        (empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)).card ≤
          base) :
    (∏ threshold ∈ thresholds.attach,
        (empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)).card) ≤
      base ^ thresholds.card := by
  have hprod :
      (∏ threshold ∈ thresholds.attach,
          (empiricalBinaryTraceSetFamily sample indexClass
            (thresholdIndicatorClassFun classFun threshold.1)).card) ≤
        ∏ threshold ∈ thresholds.attach, base :=
    threshold_binaryTraceSetFamily_product_card_le_of_forall_card_le
      sample indexClass classFun thresholds (fun _ => base) hbase
  simpa using hprod

/--
Common fixed-threshold cardinality bounds plus a polynomial estimate on
`base ^ #thresholds` feed the threshold-coded trace image into the
Theorem 2.4.3 natural-polynomial entropy shape.
-/
theorem empiricalTrace_image_card_add_one_real_le_of_thresholdTraceCode_const_factor_bound
    {Observation : Type u} {Index : Type v} {n d : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {thresholds : Finset ℝ} {C : ℝ} {base : ℕ}
    (hseparate :
      ∀ index₁, index₁ ∈ indexClass ->
        ∀ index₂, index₂ ∈ indexClass ->
          (∀ threshold : {threshold // threshold ∈ thresholds},
            thresholdTraceCode thresholds
                (empiricalTrace sample classFun index₁) threshold =
              thresholdTraceCode thresholds
                (empiricalTrace sample classFun index₂) threshold) ->
          empiricalTrace sample classFun index₁ =
            empiricalTrace sample classFun index₂)
    (hbase :
      ∀ threshold : {threshold // threshold ∈ thresholds},
        (empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)).card ≤
          base)
    (hpow_bound :
      (((base ^ thresholds.card : ℕ) : ℝ) + 1) ≤
        C * (((n + 1 : ℕ) : ℝ) ^ d)) :
    (((finite_empiricalTrace_image_of_thresholdTraceCode_separates hseparate).toFinset.card : ℝ) + 1) ≤
      C * (((n + 1 : ℕ) : ℝ) ^ d) := by
  have hproduct_nat :
      (∏ threshold ∈ thresholds.attach,
          (empiricalBinaryTraceSetFamily sample indexClass
            (thresholdIndicatorClassFun classFun threshold.1)).card) ≤
        base ^ thresholds.card :=
    threshold_binaryTraceSetFamily_product_card_le_const_pow
      sample indexClass classFun thresholds base hbase
  have hproduct_real :
      (((∏ threshold ∈ thresholds.attach,
        (empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)).card : ℕ) : ℝ) + 1) ≤
        ((base ^ thresholds.card : ℕ) : ℝ) + 1 := by
    exact_mod_cast Nat.add_le_add_right hproduct_nat 1
  exact
    empiricalTrace_image_card_add_one_real_le_of_thresholdTraceCode_product_bound
      (sample := sample) (indexClass := indexClass) (classFun := classFun)
      (thresholds := thresholds) (C := C) hseparate
      (hproduct_real.trans hpow_bound)

/--
If the number of thresholds is bounded by `k`, a common fixed-threshold
cardinality bound gives the cleaner product bound `base ^ k`.
-/
theorem threshold_binaryTraceSetFamily_product_card_le_const_pow_of_card_le
    {Observation : Type u} {Index : Type v} {n : ℕ}
    (sample : SampleAt Observation n)
    (indexClass : Set Index) (classFun : Index -> Observation -> ℝ)
    (thresholds : Finset ℝ) {base k : ℕ}
    (hbase_pos : 0 < base) (hthresholds_card : thresholds.card ≤ k)
    (hbase :
      ∀ threshold : {threshold // threshold ∈ thresholds},
        (empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)).card ≤
          base) :
    (∏ threshold ∈ thresholds.attach,
        (empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)).card) ≤
      base ^ k :=
  (threshold_binaryTraceSetFamily_product_card_le_const_pow
    sample indexClass classFun thresholds base hbase).trans
    (Nat.pow_le_pow_right hbase_pos hthresholds_card)

/--
Common fixed-threshold cardinality bounds and a threshold-count bound reduce
the theorem-facing entropy estimate to a bound on `base ^ k`.
-/
theorem empiricalTrace_image_card_add_one_real_le_of_thresholdTraceCode_const_factor_card_le
    {Observation : Type u} {Index : Type v} {n d : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {thresholds : Finset ℝ} {C : ℝ} {base k : ℕ}
    (hseparate :
      ∀ index₁, index₁ ∈ indexClass ->
        ∀ index₂, index₂ ∈ indexClass ->
          (∀ threshold : {threshold // threshold ∈ thresholds},
            thresholdTraceCode thresholds
                (empiricalTrace sample classFun index₁) threshold =
              thresholdTraceCode thresholds
                (empiricalTrace sample classFun index₂) threshold) ->
          empiricalTrace sample classFun index₁ =
            empiricalTrace sample classFun index₂)
    (hbase_pos : 0 < base) (hthresholds_card : thresholds.card ≤ k)
    (hbase :
      ∀ threshold : {threshold // threshold ∈ thresholds},
        (empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)).card ≤
          base)
    (hpow_bound :
      (((base ^ k : ℕ) : ℝ) + 1) ≤
        C * (((n + 1 : ℕ) : ℝ) ^ d)) :
    (((finite_empiricalTrace_image_of_thresholdTraceCode_separates hseparate).toFinset.card : ℝ) + 1) ≤
      C * (((n + 1 : ℕ) : ℝ) ^ d) := by
  have hproduct_nat :
      (∏ threshold ∈ thresholds.attach,
          (empiricalBinaryTraceSetFamily sample indexClass
            (thresholdIndicatorClassFun classFun threshold.1)).card) ≤
        base ^ k :=
    threshold_binaryTraceSetFamily_product_card_le_const_pow_of_card_le
      sample indexClass classFun thresholds hbase_pos hthresholds_card hbase
  have hproduct_real :
      (((∏ threshold ∈ thresholds.attach,
        (empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)).card : ℕ) : ℝ) + 1) ≤
        ((base ^ k : ℕ) : ℝ) + 1 := by
    exact_mod_cast Nat.add_le_add_right hproduct_nat 1
  exact
    empiricalTrace_image_card_add_one_real_le_of_thresholdTraceCode_product_bound
      (sample := sample) (indexClass := indexClass) (classFun := classFun)
      (thresholds := thresholds) (C := C) hseparate
      (hproduct_real.trans hpow_bound)

/--
Arithmetic bridge: a polynomial real bound on a natural base gives a
polynomial real bound on `base ^ k + 1`.
-/
theorem nat_pow_add_one_real_le_nat_poly_of_base_le
    {base n a k : ℕ} {B : ℝ}
    (hB_nonneg : 0 ≤ B)
    (hbase_le : (base : ℝ) ≤ B * (((n + 1 : ℕ) : ℝ) ^ a)) :
    (((base ^ k : ℕ) : ℝ) + 1) ≤
      (B ^ k + 1) * (((n + 1 : ℕ) : ℝ) ^ (a * k)) := by
  let sampleSize : ℝ := ((n + 1 : ℕ) : ℝ)
  have hbase_nonneg : 0 ≤ (base : ℝ) := Nat.cast_nonneg _
  have hsample_ge_one : 1 ≤ sampleSize := by
    dsimp [sampleSize]
    exact_mod_cast Nat.succ_le_succ (Nat.zero_le n)
  have hsample_pow_nonneg : 0 ≤ sampleSize ^ a :=
    pow_nonneg (by linarith : 0 ≤ sampleSize) a
  have htarget_pow_ge_one : 1 ≤ sampleSize ^ (a * k) :=
    one_le_pow₀ hsample_ge_one
  have hpow_le :
      ((base : ℝ) ^ k) ≤ (B * sampleSize ^ a) ^ k :=
    pow_le_pow_left₀ hbase_nonneg hbase_le k
  have hpow_rewrite :
      (B * sampleSize ^ a) ^ k =
        B ^ k * sampleSize ^ (a * k) := by
    rw [mul_pow, pow_mul]
  have hcast_pow :
      ((base ^ k : ℕ) : ℝ) = (base : ℝ) ^ k := by
    norm_num [Nat.cast_pow]
  have hbase_pow_le :
      ((base ^ k : ℕ) : ℝ) ≤ B ^ k * sampleSize ^ (a * k) := by
    calc
      ((base ^ k : ℕ) : ℝ) = (base : ℝ) ^ k := hcast_pow
      _ ≤ (B * sampleSize ^ a) ^ k := hpow_le
      _ = B ^ k * sampleSize ^ (a * k) := hpow_rewrite
  have hBpow_nonneg : 0 ≤ B ^ k := pow_nonneg hB_nonneg k
  have hmain :
      ((base ^ k : ℕ) : ℝ) + 1 ≤
        B ^ k * sampleSize ^ (a * k) + sampleSize ^ (a * k) := by
    nlinarith
  calc
    ((base ^ k : ℕ) : ℝ) + 1
        ≤ B ^ k * sampleSize ^ (a * k) + sampleSize ^ (a * k) := hmain
    _ = (B ^ k + 1) * sampleSize ^ (a * k) := by ring

/--
If the common fixed-threshold cardinality bound itself has polynomial growth,
then the threshold-count route supplies the Theorem 2.4.3 trace-cardinality
polynomial shape.
-/
theorem empiricalTrace_image_card_add_one_real_le_of_thresholdTraceCode_base_le_nat_poly
    {Observation : Type u} {Index : Type v} {n a k : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {thresholds : Finset ℝ} {base : ℕ} {B : ℝ}
    (hseparate :
      ∀ index₁, index₁ ∈ indexClass ->
        ∀ index₂, index₂ ∈ indexClass ->
          (∀ threshold : {threshold // threshold ∈ thresholds},
            thresholdTraceCode thresholds
                (empiricalTrace sample classFun index₁) threshold =
              thresholdTraceCode thresholds
                (empiricalTrace sample classFun index₂) threshold) ->
          empiricalTrace sample classFun index₁ =
            empiricalTrace sample classFun index₂)
    (hbase_pos : 0 < base) (hthresholds_card : thresholds.card ≤ k)
    (hbase :
      ∀ threshold : {threshold // threshold ∈ thresholds},
        (empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)).card ≤
          base)
    (hB_nonneg : 0 ≤ B)
    (hbase_growth : (base : ℝ) ≤ B * (((n + 1 : ℕ) : ℝ) ^ a)) :
    (((finite_empiricalTrace_image_of_thresholdTraceCode_separates hseparate).toFinset.card : ℝ) + 1) ≤
      (B ^ k + 1) * (((n + 1 : ℕ) : ℝ) ^ (a * k)) := by
  exact
    empiricalTrace_image_card_add_one_real_le_of_thresholdTraceCode_const_factor_card_le
      (sample := sample) (indexClass := indexClass) (classFun := classFun)
      (thresholds := thresholds) (C := B ^ k + 1) (base := base) (k := k)
      (d := a * k) hseparate hbase_pos hthresholds_card hbase
      (nat_pow_add_one_real_le_nat_poly_of_base_le
        (base := base) (n := n) (a := a) (k := k)
        hB_nonneg hbase_growth)

/--
Sauer-Shelah supplies a common natural-polynomial cardinality bound for every
fixed-threshold binary trace family under a uniform VC-dimension bound.
-/
theorem threshold_binaryTraceSetFamily_card_le_vc_nat_poly
    {Observation : Type u} {Index : Type v} {n d : ℕ}
    (sample : SampleAt Observation n)
    (indexClass : Set Index) (classFun : Index -> Observation -> ℝ)
    {thresholds : Finset ℝ}
    (hvc :
      ∀ threshold : {threshold // threshold ∈ thresholds},
        (empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)).vcDim ≤ d)
    (threshold : {threshold // threshold ∈ thresholds}) :
    (empiricalBinaryTraceSetFamily sample indexClass
      (thresholdIndicatorClassFun classFun threshold.1)).card ≤
      (d + 2) * (n + 1) ^ d := by
  have hadd_one :
      (empiricalBinaryTraceSetFamily sample indexClass
        (thresholdIndicatorClassFun classFun threshold.1)).card + 1 ≤
        (d + 2) * (n + 1) ^ d :=
    vdVWSauerShelah_card_add_one_le_nat_poly_of_vcDim_le
      (empiricalBinaryTraceSetFamily sample indexClass
        (thresholdIndicatorClassFun classFun threshold.1))
      (N := n) (d := d) (by simp) (hvc threshold)
  exact (Nat.le_succ _).trans hadd_one

/--
Uniform fixed-threshold VC/Sauer bounds control the product of the
fixed-threshold binary trace-family cardinalities.
-/
theorem threshold_binaryTraceSetFamily_product_card_le_uniform_vc
    {Observation : Type u} {Index : Type v} {n d k : ℕ}
    (sample : SampleAt Observation n)
    (indexClass : Set Index) (classFun : Index -> Observation -> ℝ)
    {thresholds : Finset ℝ}
    (hthresholds_card : thresholds.card ≤ k)
    (hvc :
      ∀ threshold : {threshold // threshold ∈ thresholds},
        (empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)).vcDim ≤ d) :
    (∏ threshold ∈ thresholds.attach,
        (empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)).card) ≤
      (((d + 2) * (n + 1) ^ d) ^ k) := by
  let base : ℕ := (d + 2) * (n + 1) ^ d
  have hbase_pos : 0 < base := by
    dsimp [base]
    exact Nat.mul_pos (Nat.succ_pos (d + 1)) (pow_pos (Nat.succ_pos n) d)
  have hbase :
      ∀ threshold : {threshold // threshold ∈ thresholds},
        (empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)).card ≤
          base := by
    intro threshold
    exact threshold_binaryTraceSetFamily_card_le_vc_nat_poly
      sample indexClass classFun hvc threshold
  simpa [base] using
    threshold_binaryTraceSetFamily_product_card_le_const_pow_of_card_le
      sample indexClass classFun thresholds hbase_pos hthresholds_card hbase

/--
The finite threshold-code set itself satisfies the same natural-polynomial
cardinality shape as the threshold-code image when every fixed-threshold
binary trace family has VC dimension at most `d`.

This is the code-set cardinality estimate consumed by finite trace-code-set
Theorem 2.4.3 routes: it bounds the whole finite target code set, not only the
realized threshold-code image.
-/
theorem thresholdTraceCodeSet_card_add_one_real_le_uniform_vc
    {Observation : Type u} {Index : Type v} {n d k : ℕ}
    (sample : SampleAt Observation n)
    (indexClass : Set Index) (classFun : Index -> Observation -> ℝ)
    {thresholds : Finset ℝ}
    (hthresholds_card : thresholds.card ≤ k)
    (hvc :
      ∀ threshold : {threshold // threshold ∈ thresholds},
        (empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)).vcDim ≤ d) :
    (((thresholdTraceCodeSet sample indexClass classFun thresholds).card : ℝ) + 1) ≤
      ((((d + 2 : ℕ) : ℝ) ^ k) + 1) *
        (((n + 1 : ℕ) : ℝ) ^ (d * k)) := by
  let base : ℕ := (d + 2) * (n + 1) ^ d
  have hproduct_nat :
      (∏ threshold ∈ thresholds.attach,
          (empiricalBinaryTraceSetFamily sample indexClass
            (thresholdIndicatorClassFun classFun threshold.1)).card) ≤
        base ^ k := by
    simpa [base] using
      threshold_binaryTraceSetFamily_product_card_le_uniform_vc
        sample indexClass classFun hthresholds_card hvc
  have hcode_nat :
      (thresholdTraceCodeSet sample indexClass classFun thresholds).card ≤
        base ^ k :=
    (thresholdTraceCodeSet_card_le_pi_binaryTraceSetFamily_card
      sample indexClass classFun thresholds).trans hproduct_nat
  have hcode_real :
      (((thresholdTraceCodeSet sample indexClass classFun thresholds).card : ℝ) + 1) ≤
        (((base ^ k : ℕ) : ℝ) + 1) := by
    exact_mod_cast Nat.add_le_add_right hcode_nat 1
  have hbase_growth :
      (base : ℝ) ≤ ((d + 2 : ℕ) : ℝ) * (((n + 1 : ℕ) : ℝ) ^ d) := by
    dsimp [base]
    norm_num [Nat.cast_mul, Nat.cast_pow]
  exact hcode_real.trans
    (nat_pow_add_one_real_le_nat_poly_of_base_le
      (base := base) (n := n) (a := d) (k := k)
      (B := ((d + 2 : ℕ) : ℝ)) (Nat.cast_nonneg _) hbase_growth)

/--
Uniform full-subgraph VC/Sauer bounds control the full finite
threshold-code-set cardinality, not just the realized code image.

This is the raw code-set cardinality input for finite trace-code-set
Theorem 2.4.3 routes whose code set is `thresholdTraceCodeSet`.
-/
theorem thresholdTraceCodeSet_card_add_one_real_le_uniform_subgraph_vc_nat_poly
    {Observation : Type u} {Index : Type v} {n d k : ℕ}
    (sample : SampleAt Observation n)
    (indexClass : Set Index) (classFun : Index -> Observation -> ℝ)
    {thresholds : Finset ℝ}
    (hthresholds_card : thresholds.card ≤ k)
    (hvc : VdVWUniformSubgraphVCBound indexClass classFun d) :
    (((thresholdTraceCodeSet sample indexClass classFun thresholds).card : ℝ) + 1) ≤
      ((((d + 2 : ℕ) : ℝ) ^ k) + 1) *
        (((n + 1 : ℕ) : ℝ) ^ (d * k)) := by
  exact
    thresholdTraceCodeSet_card_add_one_real_le_uniform_vc
      sample indexClass classFun hthresholds_card
      (fun threshold =>
        VdVWUniformThresholdVCSubgraphBound.empiricalBinaryTraceSetFamily_vcDim_le
          (sample := sample)
          (VdVWUniformSubgraphVCBound.toUniformThresholdVCSubgraphBound hvc)
          threshold.1)

/--
Uniform fixed-threshold VC/Sauer bounds give the natural-polynomial `+ 1`
real cardinality estimate for the realized threshold-code image.

This is the realized-image form consumed by entropy interfaces whose
cardinality estimates are stated as `card + 1 <= C * (n + 1)^d`.
-/
theorem thresholdTraceCode_image_toFinset_card_add_one_real_le_uniform_vc
    {Observation : Type u} {Index : Type v} {n d k : ℕ}
    (sample : SampleAt Observation n)
    (indexClass : Set Index) (classFun : Index -> Observation -> ℝ)
    {thresholds : Finset ℝ}
    (hthresholds_card : thresholds.card ≤ k)
    (hvc :
      ∀ threshold : {threshold // threshold ∈ thresholds},
        (empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)).vcDim ≤ d) :
    (((finite_thresholdTraceCode_image sample indexClass classFun thresholds).toFinset.card : ℝ) + 1) ≤
      ((((d + 2 : ℕ) : ℝ) ^ k) + 1) *
        (((n + 1 : ℕ) : ℝ) ^ (d * k)) := by
  have himage_nat :
      (finite_thresholdTraceCode_image sample indexClass classFun thresholds).toFinset.card ≤
        (thresholdTraceCodeSet sample indexClass classFun thresholds).card :=
    thresholdTraceCode_image_toFinset_card_le_thresholdTraceCodeSet_card
      sample indexClass classFun thresholds
  have himage_real :
      (((finite_thresholdTraceCode_image sample indexClass classFun thresholds).toFinset.card : ℝ) + 1) ≤
        (((thresholdTraceCodeSet sample indexClass classFun thresholds).card : ℝ) + 1) := by
    exact_mod_cast Nat.add_le_add_right himage_nat 1
  exact himage_real.trans
    (thresholdTraceCodeSet_card_add_one_real_le_uniform_vc
      sample indexClass classFun hthresholds_card hvc)

/--
Uniform full-subgraph VC/Sauer bounds give the natural-polynomial `+ 1` real
cardinality estimate for the realized threshold-code image.
-/
theorem thresholdTraceCode_image_toFinset_card_add_one_real_le_uniform_subgraph_vc_nat_poly
    {Observation : Type u} {Index : Type v} {n d k : ℕ}
    (sample : SampleAt Observation n)
    (indexClass : Set Index) (classFun : Index -> Observation -> ℝ)
    {thresholds : Finset ℝ}
    (hthresholds_card : thresholds.card ≤ k)
    (hvc : VdVWUniformSubgraphVCBound indexClass classFun d) :
    (((finite_thresholdTraceCode_image sample indexClass classFun thresholds).toFinset.card : ℝ) + 1) ≤
      ((((d + 2 : ℕ) : ℝ) ^ k) + 1) *
        (((n + 1 : ℕ) : ℝ) ^ (d * k)) := by
  exact
    thresholdTraceCode_image_toFinset_card_add_one_real_le_uniform_vc
      sample indexClass classFun hthresholds_card
      (fun threshold =>
        VdVWUniformThresholdVCSubgraphBound.empiricalBinaryTraceSetFamily_vcDim_le
          (sample := sample)
          (VdVWUniformSubgraphVCBound.toUniformThresholdVCSubgraphBound hvc)
          threshold.1)

/--
Uniform full-subgraph VC/Sauer bounds control the realized threshold-code
image cardinality.

This is the raw structural cardinality handoff behind the threshold-grid
Theorem 2.4.3 route: a full-subgraph VC bound gives a uniform bound for each
fixed threshold trace family, the product code bounds the threshold-code image,
and Sauer-Shelah supplies the polynomial growth rate.
-/
theorem thresholdTraceCode_image_toFinset_card_le_uniform_subgraph_vc_nat_poly
    {Observation : Type u} {Index : Type v} {n d k : ℕ}
    (sample : SampleAt Observation n)
    (indexClass : Set Index) (classFun : Index -> Observation -> ℝ)
    {thresholds : Finset ℝ}
    (hthresholds_card : thresholds.card ≤ k)
    (hvc : VdVWUniformSubgraphVCBound indexClass classFun d) :
    (finite_thresholdTraceCode_image sample indexClass classFun thresholds).toFinset.card ≤
      (((d + 2) * (n + 1) ^ d) ^ k) := by
  refine
    (thresholdTraceCode_image_toFinset_card_le_thresholdTraceCodeSet_card
      sample indexClass classFun thresholds).trans ?_
  refine
    (thresholdTraceCodeSet_card_le_pi_binaryTraceSetFamily_card
      sample indexClass classFun thresholds).trans ?_
  exact
    threshold_binaryTraceSetFamily_product_card_le_uniform_vc
      sample indexClass classFun hthresholds_card
      (fun threshold =>
        VdVWUniformThresholdVCSubgraphBound.empiricalBinaryTraceSetFamily_vcDim_le
          (sample := sample)
          (VdVWUniformSubgraphVCBound.toUniformThresholdVCSubgraphBound hvc)
          threshold.1)

/--
Finite threshold grids plus uniform fixed-threshold VC/Sauer bounds yield a
numeric empirical covering-number bound through approximate threshold coding.
-/
theorem empiricalL1CoveringNumber_le_of_thresholdTraceCode_gap_grid_uniform_vc_card_le
    {Observation : Type u} {Index : Type v} {n d k : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {thresholds : Finset ℝ} {epsilon : ℝ} {cardinality : ℕ}
    (hepsilon_nonneg : 0 ≤ epsilon)
    (hgrid :
      ∀ a b : ℝ, a < b -> epsilon < b - a ->
        ∃ threshold : {threshold // threshold ∈ thresholds},
          a ≤ threshold.1 ∧ threshold.1 < b)
    (hthresholds_card : thresholds.card ≤ k)
    (hvc :
      ∀ threshold : {threshold // threshold ∈ thresholds},
        (empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)).vcDim ≤ d)
    (hcard_le : (((d + 2) * (n + 1) ^ d) ^ k) ≤ cardinality) :
    empiricalL1CoveringNumber sample indexClass classFun epsilon ≤
      (cardinality : ℕ∞) := by
  exact
    empiricalL1CoveringNumber_le_of_thresholdTraceCode_gap_grid_product_card_le
      (sample := sample) (indexClass := indexClass) (classFun := classFun)
      (thresholds := thresholds) hepsilon_nonneg hgrid
      ((threshold_binaryTraceSetFamily_product_card_le_uniform_vc
        sample indexClass classFun hthresholds_card hvc).trans hcard_le)

/--
Bounded threshold-grid empirical-covering-number bound.  The threshold grid
only has to hit gaps inside a deterministic range containing all realized
sample coordinates of the class.
-/
theorem empiricalL1CoveringNumber_le_of_thresholdTraceCode_bounded_gap_grid_product_card_le
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {thresholds : Finset ℝ} {epsilon lower upper : ℝ} {cardinality : ℕ}
    (hepsilon_nonneg : 0 ≤ epsilon)
    (hbounded :
      ∀ index, index ∈ indexClass ->
        ∀ sampleIndex : Fin n,
          lower ≤ classFun index (sample sampleIndex) ∧
            classFun index (sample sampleIndex) ≤ upper)
    (hgrid :
      ∀ a b : ℝ, lower ≤ a -> b ≤ upper -> a < b ->
        epsilon < b - a ->
          ∃ threshold : {threshold // threshold ∈ thresholds},
            a ≤ threshold.1 ∧ threshold.1 < b)
    (hcard_le :
      (∏ threshold ∈ thresholds.attach,
          (empiricalBinaryTraceSetFamily sample indexClass
            (thresholdIndicatorClassFun classFun threshold.1)).card) ≤
        cardinality) :
    empiricalL1CoveringNumber sample indexClass classFun epsilon ≤
      (cardinality : ℕ∞) := by
  exact
    empiricalL1CoveringNumber_le_of_thresholdTraceCode_coordinate_approx_product_card_le
      (sample := sample) (indexClass := indexClass) (classFun := classFun)
      (thresholds := thresholds) hepsilon_nonneg
      (fun sampleIndex index hindex center hcenter hcompare =>
        abs_sub_le_of_forall_bounded_gap_exists_threshold hepsilon_nonneg
          (hbounded index hindex sampleIndex)
          (hbounded center hcenter sampleIndex) hgrid hcompare)
      hcard_le

/--
Bounded finite threshold grids plus uniform fixed-threshold VC/Sauer bounds
yield a numeric empirical covering-number bound.
-/
theorem empiricalL1CoveringNumber_le_of_thresholdTraceCode_bounded_gap_grid_uniform_vc_card_le
    {Observation : Type u} {Index : Type v} {n d k : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {thresholds : Finset ℝ} {epsilon lower upper : ℝ} {cardinality : ℕ}
    (hepsilon_nonneg : 0 ≤ epsilon)
    (hbounded :
      ∀ index, index ∈ indexClass ->
        ∀ sampleIndex : Fin n,
          lower ≤ classFun index (sample sampleIndex) ∧
            classFun index (sample sampleIndex) ≤ upper)
    (hgrid :
      ∀ a b : ℝ, lower ≤ a -> b ≤ upper -> a < b ->
        epsilon < b - a ->
          ∃ threshold : {threshold // threshold ∈ thresholds},
            a ≤ threshold.1 ∧ threshold.1 < b)
    (hthresholds_card : thresholds.card ≤ k)
    (hvc :
      ∀ threshold : {threshold // threshold ∈ thresholds},
        (empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)).vcDim ≤ d)
    (hcard_le : (((d + 2) * (n + 1) ^ d) ^ k) ≤ cardinality) :
    empiricalL1CoveringNumber sample indexClass classFun epsilon ≤
      (cardinality : ℕ∞) := by
  exact
    empiricalL1CoveringNumber_le_of_thresholdTraceCode_bounded_gap_grid_product_card_le
      (sample := sample) (indexClass := indexClass) (classFun := classFun)
      (thresholds := thresholds) hepsilon_nonneg hbounded hgrid
      ((threshold_binaryTraceSetFamily_product_card_le_uniform_vc
        sample indexClass classFun hthresholds_card hvc).trans hcard_le)

/--
Concrete bounded empirical-covering-number bound using the integer-multiple
threshold grid.
-/
theorem empiricalL1CoveringNumber_le_of_integerMultipleThresholdGrid_uniform_vc_card_le
    {Observation : Type u} {Index : Type v} {n d k : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {epsilon : ℝ} {bound : ℤ} {cardinality : ℕ}
    (hepsilon_pos : 0 < epsilon)
    (hbounded :
      ∀ index, index ∈ indexClass ->
        ∀ sampleIndex : Fin n,
          (-(bound : ℝ)) * epsilon ≤ classFun index (sample sampleIndex) ∧
            classFun index (sample sampleIndex) ≤ (bound : ℝ) * epsilon)
    (hthresholds_card : (integerMultipleThresholdGrid epsilon bound).card ≤ k)
    (hvc :
      ∀ threshold : {threshold // threshold ∈
          integerMultipleThresholdGrid epsilon bound},
        (empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)).vcDim ≤ d)
    (hcard_le : (((d + 2) * (n + 1) ^ d) ^ k) ≤ cardinality) :
    empiricalL1CoveringNumber sample indexClass classFun epsilon ≤
      (cardinality : ℕ∞) := by
  exact
    empiricalL1CoveringNumber_le_of_thresholdTraceCode_bounded_gap_grid_uniform_vc_card_le
      (sample := sample) (indexClass := indexClass) (classFun := classFun)
      (thresholds := integerMultipleThresholdGrid epsilon bound)
      (epsilon := epsilon) (lower := (-(bound : ℝ)) * epsilon)
      (upper := (bound : ℝ) * epsilon) hepsilon_pos.le hbounded
      (fun a b ha hb hab hgap =>
        exists_integerMultipleThresholdGrid_between_of_bounds
          hepsilon_pos ha hb hab hgap)
      hthresholds_card hvc hcard_le

/--
Concrete bounded empirical-covering-number bound using the integer-multiple
threshold grid, with the grid-cardinality bound discharged for a natural
symmetric radius.
-/
theorem empiricalL1CoveringNumber_le_of_integerMultipleThresholdGrid_nat_uniform_vc_card_le
    {Observation : Type u} {Index : Type v} {n d : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {epsilon : ℝ} {bound cardinality : ℕ}
    (hepsilon_pos : 0 < epsilon)
    (hbounded :
      ∀ index, index ∈ indexClass ->
        ∀ sampleIndex : Fin n,
          (-(bound : ℤ) : ℝ) * epsilon ≤ classFun index (sample sampleIndex) ∧
            classFun index (sample sampleIndex) ≤ ((bound : ℤ) : ℝ) * epsilon)
    (hvc :
      ∀ threshold : {threshold // threshold ∈
          integerMultipleThresholdGrid epsilon (bound : ℤ)},
        (empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)).vcDim ≤ d)
    (hcard_le :
      (((d + 2) * (n + 1) ^ d) ^ (2 * bound + 1)) ≤ cardinality) :
    empiricalL1CoveringNumber sample indexClass classFun epsilon ≤
      (cardinality : ℕ∞) := by
  exact
    empiricalL1CoveringNumber_le_of_integerMultipleThresholdGrid_uniform_vc_card_le
      (sample := sample) (indexClass := indexClass) (classFun := classFun)
      (epsilon := epsilon) (bound := (bound : ℤ))
      (k := 2 * bound + 1) hepsilon_pos hbounded
      (integerMultipleThresholdGrid_nat_card_le epsilon bound) hvc hcard_le

/--
Absolute-value bounded variant of the natural integer-multiple threshold-grid
covering bound.  This is the form used by truncated classes with an envelope
bound.
-/
theorem empiricalL1CoveringNumber_le_of_integerMultipleThresholdGrid_nat_uniform_abs_bound_vc_card_le
    {Observation : Type u} {Index : Type v} {n d : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {epsilon : ℝ} {bound cardinality : ℕ}
    (hepsilon_pos : 0 < epsilon)
    (hbounded_abs :
      ∀ index, index ∈ indexClass ->
        ∀ sampleIndex : Fin n,
          |classFun index (sample sampleIndex)| ≤
            ((bound : ℤ) : ℝ) * epsilon)
    (hvc :
      ∀ threshold : {threshold // threshold ∈
          integerMultipleThresholdGrid epsilon (bound : ℤ)},
        (empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)).vcDim ≤ d)
    (hcard_le :
      (((d + 2) * (n + 1) ^ d) ^ (2 * bound + 1)) ≤ cardinality) :
    empiricalL1CoveringNumber sample indexClass classFun epsilon ≤
      (cardinality : ℕ∞) := by
  apply
    empiricalL1CoveringNumber_le_of_integerMultipleThresholdGrid_nat_uniform_vc_card_le
      (sample := sample) (indexClass := indexClass) (classFun := classFun)
      (epsilon := epsilon) (bound := bound) hepsilon_pos
  · intro index hindex sampleIndex
    have hbounds := abs_le.mp (hbounded_abs index hindex sampleIndex)
    constructor
    · have hleft : -(((bound : ℤ) : ℝ) * epsilon) ≤
          classFun index (sample sampleIndex) := hbounds.1
      simpa [neg_mul] using hleft
    · exact hbounds.2
  · exact hvc
  · exact hcard_le

/--
Uniform fixed-threshold VC/Sauer bounds, finite threshold separation, and a
threshold-count bound give the natural-polynomial empirical trace-cardinality
shape needed by the Theorem 2.4.3 entropy route.
-/
theorem empiricalTrace_image_card_add_one_real_le_of_thresholdTraceCode_uniform_vc
    {Observation : Type u} {Index : Type v} {n d k : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {thresholds : Finset ℝ}
    (hseparate :
      ∀ index₁, index₁ ∈ indexClass ->
        ∀ index₂, index₂ ∈ indexClass ->
          (∀ threshold : {threshold // threshold ∈ thresholds},
            thresholdTraceCode thresholds
                (empiricalTrace sample classFun index₁) threshold =
              thresholdTraceCode thresholds
                (empiricalTrace sample classFun index₂) threshold) ->
          empiricalTrace sample classFun index₁ =
            empiricalTrace sample classFun index₂)
    (hthresholds_card : thresholds.card ≤ k)
    (hvc :
      ∀ threshold : {threshold // threshold ∈ thresholds},
        (empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)).vcDim ≤ d) :
    (((finite_empiricalTrace_image_of_thresholdTraceCode_separates hseparate).toFinset.card : ℝ) + 1) ≤
      ((((d + 2 : ℕ) : ℝ) ^ k) + 1) *
        (((n + 1 : ℕ) : ℝ) ^ (d * k)) := by
  let base : ℕ := (d + 2) * (n + 1) ^ d
  have hbase_pos : 0 < base := by
    dsimp [base]
    exact Nat.mul_pos (Nat.succ_pos (d + 1)) (pow_pos (Nat.succ_pos n) d)
  have hbase :
      ∀ threshold : {threshold // threshold ∈ thresholds},
        (empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)).card ≤
          base := by
    intro threshold
    exact threshold_binaryTraceSetFamily_card_le_vc_nat_poly
      sample indexClass classFun hvc threshold
  have hbase_growth :
      (base : ℝ) ≤ ((d + 2 : ℕ) : ℝ) * (((n + 1 : ℕ) : ℝ) ^ d) := by
    dsimp [base]
    norm_num [Nat.cast_mul, Nat.cast_pow]
  exact
    empiricalTrace_image_card_add_one_real_le_of_thresholdTraceCode_base_le_nat_poly
      (sample := sample) (indexClass := indexClass) (classFun := classFun)
      (thresholds := thresholds) (base := base)
      (B := ((d + 2 : ℕ) : ℝ)) (a := d) (k := k)
      hseparate hbase_pos hthresholds_card hbase
      (Nat.cast_nonneg _) hbase_growth

/--
Pointwise threshold separation, threshold-count, and uniform fixed-threshold
VC/Sauer bounds give the same natural-polynomial empirical trace-cardinality
bound.  This is the form expected from later subgraph/truncated-class geometry:
the geometry only has to show that matching all threshold predicates on the
sample identifies the realized trace.
-/
theorem empiricalTrace_image_card_add_one_real_le_of_pointwise_thresholds_separate_uniform_vc
    {Observation : Type u} {Index : Type v} {n d k : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {thresholds : Finset ℝ}
    (hpoint :
      ∀ index₁, index₁ ∈ indexClass ->
        ∀ index₂, index₂ ∈ indexClass ->
          (∀ sampleIndex : Fin n,
            ∀ threshold : {threshold // threshold ∈ thresholds},
              (threshold.1 < classFun index₁ (sample sampleIndex) ↔
                threshold.1 < classFun index₂ (sample sampleIndex))) ->
          empiricalTrace sample classFun index₁ =
            empiricalTrace sample classFun index₂)
    (hthresholds_card : thresholds.card ≤ k)
    (hvc :
      ∀ threshold : {threshold // threshold ∈ thresholds},
        (empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)).vcDim ≤ d) :
    (((finite_empiricalTrace_image_of_thresholdTraceCode_separates
      (thresholdTraceCode_separates_of_pointwise_thresholds_separate hpoint)).toFinset.card : ℝ) + 1) ≤
      ((((d + 2 : ℕ) : ℝ) ^ k) + 1) *
        (((n + 1 : ℕ) : ℝ) ^ (d * k)) := by
  exact
    empiricalTrace_image_card_add_one_real_le_of_thresholdTraceCode_uniform_vc
      (sample := sample) (indexClass := indexClass) (classFun := classFun)
      (thresholds := thresholds) (d := d) (k := k)
      (thresholdTraceCode_separates_of_pointwise_thresholds_separate hpoint)
      hthresholds_card hvc

/--
Coordinatewise threshold separation, threshold-count, and uniform
fixed-threshold VC/Sauer bounds give the natural-polynomial empirical
trace-cardinality bound.  This is the most local finite-threshold interface:
later geometry can work one sample coordinate at a time.
-/
theorem empiricalTrace_image_card_add_one_real_le_of_coordinate_thresholds_separate_uniform_vc
    {Observation : Type u} {Index : Type v} {n d k : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {thresholds : Finset ℝ}
    (hcoordinate :
      ∀ sampleIndex : Fin n,
        ∀ index₁, index₁ ∈ indexClass ->
          ∀ index₂, index₂ ∈ indexClass ->
            (∀ threshold : {threshold // threshold ∈ thresholds},
              (threshold.1 < classFun index₁ (sample sampleIndex) ↔
                threshold.1 < classFun index₂ (sample sampleIndex))) ->
            classFun index₁ (sample sampleIndex) =
              classFun index₂ (sample sampleIndex))
    (hthresholds_card : thresholds.card ≤ k)
    (hvc :
      ∀ threshold : {threshold // threshold ∈ thresholds},
        (empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)).vcDim ≤ d) :
    (((finite_empiricalTrace_image_of_thresholdTraceCode_separates
      (thresholdTraceCode_separates_of_coordinate_thresholds_separate hcoordinate)).toFinset.card : ℝ) + 1) ≤
      ((((d + 2 : ℕ) : ℝ) ^ k) + 1) *
        (((n + 1 : ℕ) : ℝ) ^ (d * k)) := by
  exact
    empiricalTrace_image_card_add_one_real_le_of_thresholdTraceCode_uniform_vc
      (sample := sample) (indexClass := indexClass) (classFun := classFun)
      (thresholds := thresholds) (d := d) (k := k)
      (thresholdTraceCode_separates_of_coordinate_thresholds_separate hcoordinate)
      hthresholds_card hvc

/--
If all realized sample-coordinate values lie in the finite threshold set, then
threshold-count and uniform fixed-threshold VC/Sauer bounds give the
natural-polynomial empirical trace-cardinality bound.
-/
theorem empiricalTrace_image_card_add_one_real_le_of_values_mem_thresholds_uniform_vc
    {Observation : Type u} {Index : Type v} {n d k : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    {thresholds : Finset ℝ}
    (hvalues :
      ∀ sampleIndex : Fin n,
        ∀ index, index ∈ indexClass ->
          classFun index (sample sampleIndex) ∈ thresholds)
    (hthresholds_card : thresholds.card ≤ k)
    (hvc :
      ∀ threshold : {threshold // threshold ∈ thresholds},
        (empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)).vcDim ≤ d) :
    (((finite_empiricalTrace_image_of_thresholdTraceCode_separates
      (thresholdTraceCode_separates_of_values_mem_thresholds hvalues)).toFinset.card : ℝ) + 1) ≤
      ((((d + 2 : ℕ) : ℝ) ^ k) + 1) *
        (((n + 1 : ℕ) : ℝ) ^ (d * k)) := by
  exact
    empiricalTrace_image_card_add_one_real_le_of_thresholdTraceCode_uniform_vc
      (sample := sample) (indexClass := indexClass) (classFun := classFun)
      (thresholds := thresholds) (d := d) (k := k)
      (thresholdTraceCode_separates_of_values_mem_thresholds hvalues)
      hthresholds_card hvc

/--
Finite realized sample-coordinate value sets supply the finite threshold set
used by the value-membership threshold route.

This is a structural bridge toward the Theorem 2.4.3 finite-threshold route:
instead of requiring an externally chosen threshold finset, it uses the finite
set of all values actually realized on the current empirical sample by the
class.
-/
theorem empiricalTrace_image_card_add_one_real_le_of_sample_valueSet_finite_uniform_vc
    {Observation : Type u} {Index : Type v} {n d k : ℕ}
    {sample : SampleAt Observation n}
    {indexClass : Set Index} {classFun : Index -> Observation -> ℝ}
    (hvalues_finite :
      ({value : ℝ |
        ∃ sampleIndex : Fin n, ∃ index, index ∈ indexClass ∧
          classFun index (sample sampleIndex) = value} : Set ℝ).Finite)
    (hvalues_card : hvalues_finite.toFinset.card ≤ k)
    (hvc :
      ∀ threshold : {threshold // threshold ∈ hvalues_finite.toFinset},
        (empiricalBinaryTraceSetFamily sample indexClass
          (thresholdIndicatorClassFun classFun threshold.1)).vcDim ≤ d) :
    (((finite_empiricalTrace_image_of_thresholdTraceCode_separates
      (thresholdTraceCode_separates_of_values_mem_thresholds
        (thresholds := hvalues_finite.toFinset)
        (by
          intro sampleIndex index hindex
          exact
            (hvalues_finite.mem_toFinset).2
              ⟨sampleIndex, index, hindex, rfl⟩))).toFinset.card : ℝ) + 1) ≤
      ((((d + 2 : ℕ) : ℝ) ^ k) + 1) *
        (((n + 1 : ℕ) : ℝ) ^ (d * k)) := by
  classical
  let hvalues :
      ∀ sampleIndex : Fin n,
        ∀ index, index ∈ indexClass ->
          classFun index (sample sampleIndex) ∈ hvalues_finite.toFinset := by
    intro sampleIndex index hindex
    exact
      (hvalues_finite.mem_toFinset).2
        ⟨sampleIndex, index, hindex, rfl⟩
  exact
    empiricalTrace_image_card_add_one_real_le_of_values_mem_thresholds_uniform_vc
      (sample := sample) (indexClass := indexClass) (classFun := classFun)
      (thresholds := hvalues_finite.toFinset) (d := d) (k := k)
      hvalues hvalues_card hvc

end StatInference
