import Mathlib.Data.Fintype.Pi
import Mathlib.Algebra.Order.Round
import Mathlib.Topology.MetricSpace.CoveringNumbers
import StatInference.EmpiricalProcess.Average

/-!
# Primitive covering numbers

This module records the VdV&W Definition 2.1.5 covering-number layer using the
pinned mathlib covering-number API.

Mathlib's `Metric.externalCoveringNumber` is the closest existing primitive to
the textbook convention: the cover centers live in the ambient space and need
not belong to the target class.  Mathlib uses closed extended-metric balls
(`edist x y ≤ ε`).  Textbook displays often use open norm balls
(`‖x - y‖ < ε`), so exact textbook statements can insert the usual slack in
the radius when that distinction matters.
-/

namespace StatInference

open EMetric Metric Set
open scoped ENNReal NNReal

universe u v

/--
VdV&W-style external covering number.

For a target set `target` in a pseudo-emetric ambient space, this is the
minimal cardinality, in `ℕ∞`, of a cover by closed balls of radius `epsilon`.
The centers are arbitrary ambient points, matching the textbook convention that
centers need not belong to the class being covered.
-/
noncomputable def vdVWCoveringNumber {Space : Type u} [PseudoEMetricSpace Space]
    (epsilon : ℝ≥0) (target : Set Space) : ℕ∞ :=
  Metric.externalCoveringNumber epsilon target

/-- A finite closed-ball cover with an explicit cardinality. -/
structure FiniteMetricCoverAtCard {Space : Type u} [PseudoEMetricSpace Space]
    (target : Set Space) (epsilon : ℝ≥0) (cardinality : ℕ) where
  center : Fin cardinality -> Space
  centerOf : ∀ x, x ∈ target -> Fin cardinality
  edist_le :
    ∀ x hx,
      edist x (center (centerOf x hx)) ≤ epsilon

namespace FiniteMetricCoverAtCard

/-- The finite set of centers supplied by an explicit-cardinality cover. -/
def centerSet {Space : Type u} [PseudoEMetricSpace Space]
    {target : Set Space} {epsilon : ℝ≥0} {cardinality : ℕ}
    (cover : FiniteMetricCoverAtCard target epsilon cardinality) : Set Space :=
  Set.range cover.center

/-- The supplied center set is finite. -/
theorem finite_centerSet {Space : Type u} [PseudoEMetricSpace Space]
    {target : Set Space} {epsilon : ℝ≥0} {cardinality : ℕ}
    (cover : FiniteMetricCoverAtCard target epsilon cardinality) :
    cover.centerSet.Finite :=
  Set.finite_range cover.center

/-- The supplied center set is a mathlib closed-ball cover. -/
theorem isCover_centerSet {Space : Type u} [PseudoEMetricSpace Space]
    {target : Set Space} {epsilon : ℝ≥0} {cardinality : ℕ}
    (cover : FiniteMetricCoverAtCard target epsilon cardinality) :
    Metric.IsCover epsilon target cover.centerSet := by
  intro x hx
  exact ⟨cover.center (cover.centerOf x hx), ⟨cover.centerOf x hx, rfl⟩,
    cover.edist_le x hx⟩

/--
An explicit finite VdV&W cover makes the mathlib external covering number
finite.
-/
theorem vdVWCoveringNumber_lt_top {Space : Type u} [PseudoEMetricSpace Space]
    {target : Set Space} {epsilon : ℝ≥0} {cardinality : ℕ}
    (cover : FiniteMetricCoverAtCard target epsilon cardinality) :
    vdVWCoveringNumber epsilon target < ⊤ := by
  unfold vdVWCoveringNumber
  exact lt_of_le_of_lt
    (Metric.IsCover.externalCoveringNumber_le_encard cover.isCover_centerSet)
    cover.finite_centerSet.encard_lt_top

end FiniteMetricCoverAtCard

/--
Finite covering-number hypothesis in witness form: there exists a finite
closed-ball cover at the given radius.
-/
def HasFiniteMetricCover {Space : Type u} [PseudoEMetricSpace Space]
    (target : Set Space) (epsilon : ℝ≥0) : Prop :=
  ∃ cardinality : ℕ,
    Nonempty (FiniteMetricCoverAtCard target epsilon cardinality)

/-- A finite-cover witness makes the VdV&W covering number finite. -/
theorem vdVWCoveringNumber_lt_top_of_hasFiniteMetricCover
    {Space : Type u} [PseudoEMetricSpace Space]
    {target : Set Space} {epsilon : ℝ≥0}
    (hfinite : HasFiniteMetricCover target epsilon) :
    vdVWCoveringNumber epsilon target < ⊤ := by
  rcases hfinite with ⟨cardinality, hcover⟩
  exact hcover.elim fun cover => cover.vdVWCoveringNumber_lt_top

/-- A finite target set has finite VdV&W covering number at every radius. -/
theorem vdVWCoveringNumber_lt_top_of_finite
    {Space : Type u} [PseudoEMetricSpace Space]
    {target : Set Space} (epsilon : ℝ≥0)
    (htarget : target.Finite) :
    vdVWCoveringNumber epsilon target < ⊤ := by
  unfold vdVWCoveringNumber
  exact lt_of_le_of_lt
    (Metric.externalCoveringNumber_le_encard_self target)
    htarget.encard_lt_top

/-- A totally bounded target has finite VdV&W covering number at every positive radius. -/
theorem vdVWCoveringNumber_lt_top_of_totallyBounded
    {Space : Type u} [PseudoEMetricSpace Space]
    {target : Set Space} {epsilon : ℝ≥0}
    (hepsilon : epsilon ≠ 0) (htarget : TotallyBounded target) :
    vdVWCoveringNumber epsilon target < ⊤ := by
  rcases Metric.exists_finite_isCover_of_totallyBounded hepsilon htarget with
    ⟨centers, _hcenters_subset, hcenters_finite, hcover⟩
  unfold vdVWCoveringNumber
  exact lt_of_le_of_lt
    (Metric.IsCover.externalCoveringNumber_le_encard hcover)
    hcenters_finite.encard_lt_top

/-- Larger radii cannot increase the external covering number. -/
theorem vdVWCoveringNumber_anti
    {Space : Type u} [PseudoEMetricSpace Space]
    {target : Set Space} {epsilon delta : ℝ≥0}
    (h : epsilon ≤ delta) :
    vdVWCoveringNumber delta target ≤ vdVWCoveringNumber epsilon target := by
  exact Metric.externalCoveringNumber_anti h

/-- Covering a subset is no harder than covering the larger set. -/
theorem vdVWCoveringNumber_mono_set
    {Space : Type u} [PseudoEMetricSpace Space]
    {target larger : Set Space} {epsilon : ℝ≥0}
    (hsubset : target ⊆ larger) :
    vdVWCoveringNumber epsilon target ≤ vdVWCoveringNumber epsilon larger := by
  exact Metric.externalCoveringNumber_mono_set hsubset

/-!
## Deterministic empirical `L1(P_n)` covering numbers

Theorem 2.4.3 uses the random covering number
`N(epsilon, F_M, L1(P_n))`.  The definitions in this section provide the
fixed-sample surface: once a random sample path is fixed, `P_n` is just the
finite empirical average over that sample.
-/

/-- Empirical `L1(P_n)` distance between two real-valued functions on a fixed sample. -/
noncomputable def empiricalL1Distance {Observation : Type u} {n : ℕ}
    (sample : SampleAt Observation n)
    (f g : Observation -> ℝ) : ℝ :=
  empiricalAverage sample fun observation => |f observation - g observation|

/-- Empirical `L1(P_n)` distance is measurable in the sample for measurable endpoints. -/
theorem measurable_empiricalL1Distance_of_measurable
    {Observation : Type u} [MeasurableSpace Observation] {n : ℕ}
    {f g : Observation -> ℝ}
    (hf : Measurable f) (hg : Measurable g) :
    Measurable fun sample : SampleAt Observation n =>
      empiricalL1Distance sample f g := by
  unfold empiricalL1Distance empiricalAverage
  exact
    (Finset.measurable_fun_sum Finset.univ fun i _hi =>
      continuous_abs.measurable.comp
        ((hf.comp (measurable_pi_apply i)).sub
          (hg.comp (measurable_pi_apply i)))).div_const (n : ℝ)

/-- Empirical `L1(P_n)` distances are nonnegative. -/
theorem empiricalL1Distance_nonneg {Observation : Type u} {n : ℕ}
    (sample : SampleAt Observation n)
    (f g : Observation -> ℝ) :
    0 ≤ empiricalL1Distance sample f g := by
  unfold empiricalL1Distance empiricalAverage
  exact div_nonneg
    (Finset.sum_nonneg fun i _hi => abs_nonneg (f (sample i) - g (sample i)))
    (Nat.cast_nonneg n)

/-- The empirical `L1(P_n)` distance from a function to itself is zero. -/
theorem empiricalL1Distance_self {Observation : Type u} {n : ℕ}
    (sample : SampleAt Observation n)
    (f : Observation -> ℝ) :
    empiricalL1Distance sample f f = 0 := by
  simp [empiricalL1Distance, empiricalAverage]

/--
The fixed-sample trace of an indexed function on the empirical sample.

This is the deterministic object behind later finite-trace and VC/Sauer-style
empirical-cover arguments: two class members with the same trace on the sample
have empirical `L1(P_n)` distance zero.
-/
def empiricalTrace {Observation : Type u} {Index : Type v} {n : ℕ}
    (sample : SampleAt Observation n)
    (classFun : Index -> Observation -> ℝ) (index : Index) : Fin n -> ℝ :=
  fun sampleIndex => classFun index (sample sampleIndex)

/-- Equal fixed-sample traces have zero empirical `L1(P_n)` distance. -/
theorem empiricalL1Distance_eq_zero_of_empiricalTrace_eq
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {classFun : Index -> Observation -> ℝ} {index center : Index}
    (htrace :
      empiricalTrace sample classFun index =
        empiricalTrace sample classFun center) :
    empiricalL1Distance sample (classFun index) (classFun center) = 0 := by
  unfold empiricalL1Distance empiricalAverage
  have hsum :
      (∑ sampleIndex : Fin n,
        |classFun index (sample sampleIndex) -
          classFun center (sample sampleIndex)|) = 0 := by
    refine Finset.sum_eq_zero fun sampleIndex _hsampleIndex => ?_
    have hpoint := congrFun htrace sampleIndex
    simp [empiricalTrace] at hpoint
    simp [hpoint]
  simp [hsum]

/--
Equal fixed-sample traces give an empirical `L1(P_n)` cover at every
nonnegative radius.
-/
theorem empiricalL1Distance_le_of_empiricalTrace_eq
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {classFun : Index -> Observation -> ℝ} {index center : Index}
    {epsilon : ℝ}
    (hepsilon_nonneg : 0 ≤ epsilon)
    (htrace :
      empiricalTrace sample classFun index =
        empiricalTrace sample classFun center) :
    empiricalL1Distance sample (classFun index) (classFun center) ≤
      epsilon := by
  rw [empiricalL1Distance_eq_zero_of_empiricalTrace_eq htrace]
  exact hepsilon_nonneg

/--
Pointwise sample-coordinate error bounds control the empirical `L1(P_n)`
distance.

This is the arithmetic bridge used by quantized-code covers: if two functions
are within `epsilon` at every observed sample coordinate, then their empirical
average absolute difference is at most `epsilon`.
-/
theorem empiricalL1Distance_le_of_forall_abs_le
    {Observation : Type u} {n : ℕ}
    {sample : SampleAt Observation n}
    {f g : Observation -> ℝ} {epsilon : ℝ}
    (hepsilon_nonneg : 0 ≤ epsilon)
    (hpoint :
      ∀ sampleIndex : Fin n,
        |f (sample sampleIndex) - g (sample sampleIndex)| ≤ epsilon) :
    empiricalL1Distance sample f g ≤ epsilon := by
  unfold empiricalL1Distance empiricalAverage
  by_cases hn : n = 0
  · subst n
    simpa using hepsilon_nonneg
  · have hn_pos_nat : 0 < n := Nat.pos_of_ne_zero hn
    have hn_pos : 0 < (n : ℝ) := Nat.cast_pos.mpr hn_pos_nat
    have hsum :
        (∑ sampleIndex : Fin n,
          |f (sample sampleIndex) - g (sample sampleIndex)|) ≤
          ∑ _sampleIndex : Fin n, epsilon := by
      exact Finset.sum_le_sum fun sampleIndex _hsampleIndex =>
        hpoint sampleIndex
    calc
      (∑ sampleIndex : Fin n,
          |f (sample sampleIndex) - g (sample sampleIndex)|) / (n : ℝ)
          ≤ (∑ _sampleIndex : Fin n, epsilon) / (n : ℝ) :=
        div_le_div_of_nonneg_right hsum (Nat.cast_nonneg n)
      _ = epsilon := by
        simp [Finset.sum_const, Fintype.card_fin, nsmul_eq_mul, hn_pos.ne']

/-- Empirical `L1(P_n)` distance is symmetric. -/
theorem empiricalL1Distance_comm {Observation : Type u} {n : ℕ}
    (sample : SampleAt Observation n)
    (f g : Observation -> ℝ) :
    empiricalL1Distance sample f g =
      empiricalL1Distance sample g f := by
  unfold empiricalL1Distance empiricalAverage
  congr 1
  exact Finset.sum_congr rfl fun i _hi => abs_sub_comm (f (sample i)) (g (sample i))

/-- Empirical `L1(P_n)` distance satisfies the triangle inequality. -/
theorem empiricalL1Distance_triangle {Observation : Type u} {n : ℕ}
    (sample : SampleAt Observation n)
    (f g h : Observation -> ℝ) :
    empiricalL1Distance sample f h ≤
      empiricalL1Distance sample f g + empiricalL1Distance sample g h := by
  unfold empiricalL1Distance empiricalAverage
  have hsum :
      (∑ i : Fin n, |f (sample i) - h (sample i)|) ≤
        ∑ i : Fin n,
          (|f (sample i) - g (sample i)| +
            |g (sample i) - h (sample i)|) := by
    exact Finset.sum_le_sum fun i _hi => by
      have hdecomp :
          f (sample i) - h (sample i) =
            (f (sample i) - g (sample i)) +
              (g (sample i) - h (sample i)) := by
        ring
      rw [hdecomp]
      exact abs_add_le _ _
  calc
    (∑ i : Fin n, |f (sample i) - h (sample i)|) / (n : ℝ)
        ≤
      (∑ i : Fin n,
          (|f (sample i) - g (sample i)| +
            |g (sample i) - h (sample i)|)) / (n : ℝ) :=
        div_le_div_of_nonneg_right hsum (Nat.cast_nonneg n)
    _ =
      (∑ i : Fin n, |f (sample i) - g (sample i)|) / (n : ℝ) +
        (∑ i : Fin n, |g (sample i) - h (sample i)|) / (n : ℝ) := by
        rw [Finset.sum_add_distrib]
        ring

/--
The index type equipped with the fixed-sample empirical `L1(P_n)`
pseudometric generated by a class map.

This wrapper keeps the empirical pseudometric instance local to the fixed
sample and class map, avoiding global typeclass pollution on the raw index
type.
-/
structure EmpiricalL1Index (Observation : Type u) (Index : Type v) (n : ℕ)
    (sample : SampleAt Observation n)
    (classFun : Index -> Observation -> ℝ) where
  toIndex : Index

namespace EmpiricalL1Index

/-- Embed a raw class index into the fixed-sample empirical pseudometric space. -/
def ofIndex {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {classFun : Index -> Observation -> ℝ}
    (index : Index) :
    EmpiricalL1Index Observation Index n sample classFun :=
  ⟨index⟩

@[simp]
theorem toIndex_ofIndex {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {classFun : Index -> Observation -> ℝ}
    (index : Index) :
    (ofIndex (sample := sample) (classFun := classFun) index).toIndex = index :=
  rfl

/-- Lift a class of raw indices to the empirical pseudometric wrapper. -/
def liftSet {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {classFun : Index -> Observation -> ℝ}
    (indexClass : Set Index) :
    Set (EmpiricalL1Index Observation Index n sample classFun) :=
  {index | index.toIndex ∈ indexClass}

@[simp]
theorem mem_liftSet {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {classFun : Index -> Observation -> ℝ}
    {indexClass : Set Index}
    {index : EmpiricalL1Index Observation Index n sample classFun} :
    index ∈ liftSet (sample := sample) (classFun := classFun) indexClass ↔
      index.toIndex ∈ indexClass :=
  Iff.rfl

/--
The fixed-sample empirical `L1(P_n)` distance gives a pseudo-emetric on the
wrapped index type.
-/
noncomputable instance instPseudoEMetricSpace
    {Observation : Type u} {Index : Type v} {n : ℕ}
    (sample : SampleAt Observation n)
    (classFun : Index -> Observation -> ℝ) :
    PseudoEMetricSpace
      (EmpiricalL1Index Observation Index n sample classFun) :=
  PseudoEMetricSpace.ofEDist
    (fun i j =>
      ENNReal.ofReal
        (empiricalL1Distance sample (classFun i.toIndex) (classFun j.toIndex)))
    (by
      intro i
      simp [empiricalL1Distance_self])
    (by
      intro i j
      simp [empiricalL1Distance_comm])
    (by
      intro i j k
      have htriangle :
          empiricalL1Distance sample (classFun i.toIndex) (classFun k.toIndex) ≤
            empiricalL1Distance sample (classFun i.toIndex) (classFun j.toIndex) +
              empiricalL1Distance sample (classFun j.toIndex) (classFun k.toIndex) :=
        empiricalL1Distance_triangle sample
          (classFun i.toIndex) (classFun j.toIndex) (classFun k.toIndex)
      calc
        ENNReal.ofReal
            (empiricalL1Distance sample (classFun i.toIndex) (classFun k.toIndex))
            ≤
          ENNReal.ofReal
            (empiricalL1Distance sample (classFun i.toIndex) (classFun j.toIndex) +
              empiricalL1Distance sample (classFun j.toIndex) (classFun k.toIndex)) :=
            ENNReal.ofReal_le_ofReal htriangle
        _ ≤
          ENNReal.ofReal
              (empiricalL1Distance sample (classFun i.toIndex) (classFun j.toIndex)) +
            ENNReal.ofReal
              (empiricalL1Distance sample (classFun j.toIndex) (classFun k.toIndex)) :=
            ENNReal.ofReal_add_le)

@[simp]
theorem edist_eq {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {classFun : Index -> Observation -> ℝ}
    (i j : EmpiricalL1Index Observation Index n sample classFun) :
    edist i j =
      ENNReal.ofReal
        (empiricalL1Distance sample (classFun i.toIndex) (classFun j.toIndex)) :=
  rfl

/--
An internal metric-cover distance bound in the empirical wrapper is exactly an
empirical `L1(P_n)` distance bound on the raw index functions.
-/
theorem empiricalL1Distance_le_coe_radius_of_edist_le
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {classFun : Index -> Observation -> ℝ}
    {radius : ℝ≥0}
    {i j : EmpiricalL1Index Observation Index n sample classFun}
    (h : edist i j ≤ (radius : ℝ≥0∞)) :
    empiricalL1Distance sample (classFun i.toIndex) (classFun j.toIndex) ≤
      (radius : ℝ) := by
  have hofReal :
      ENNReal.ofReal
          (empiricalL1Distance sample (classFun i.toIndex) (classFun j.toIndex)) ≤
        ENNReal.ofReal (radius : ℝ) := by
    simpa [edist_eq] using h
  exact (ENNReal.ofReal_le_ofReal_iff radius.2).1 hofReal

@[simp]
theorem ofIndex_injective {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {classFun : Index -> Observation -> ℝ} :
    Function.Injective
      (ofIndex (sample := sample) (classFun := classFun)) := by
  intro index index' h
  exact congrArg toIndex h

@[simp]
theorem image_ofIndex_eq_liftSet {Observation : Type u} {Index : Type v}
    {n : ℕ} {sample : SampleAt Observation n}
    {classFun : Index -> Observation -> ℝ} (indexClass : Set Index) :
    (ofIndex (sample := sample) (classFun := classFun)) '' indexClass =
      liftSet (sample := sample) (classFun := classFun) indexClass := by
  ext index
  constructor
  · rintro ⟨rawIndex, hrawIndex, rfl⟩
    simpa [liftSet] using hrawIndex
  · intro hindex
    exact ⟨index.toIndex, hindex, by cases index; rfl⟩

@[simp]
theorem encard_liftSet_eq {Observation : Type u} {Index : Type v}
    {n : ℕ} {sample : SampleAt Observation n}
    {classFun : Index -> Observation -> ℝ} (indexClass : Set Index) :
    (liftSet (sample := sample) (classFun := classFun) indexClass).encard =
      indexClass.encard := by
  rw [← image_ofIndex_eq_liftSet (sample := sample) (classFun := classFun)
    indexClass]
  exact (ofIndex_injective (sample := sample)
    (classFun := classFun)).encard_image indexClass

theorem finite_liftSet {Observation : Type u} {Index : Type v}
    {n : ℕ} {sample : SampleAt Observation n}
    {classFun : Index -> Observation -> ℝ} {indexClass : Set Index}
    (hindex_finite : indexClass.Finite) :
    (liftSet (sample := sample) (classFun := classFun) indexClass).Finite := by
  rw [← image_ofIndex_eq_liftSet (sample := sample) (classFun := classFun)
    indexClass]
  exact hindex_finite.image
    (ofIndex (sample := sample) (classFun := classFun))

end EmpiricalL1Index

/--
An explicit finite empirical `L1(P_n)` net over a class.

Centers are required to belong to the target class, matching the finite net
`G ⊂ F_M` used in the proof of VdV&W Theorem 2.4.3.
-/
structure FiniteEmpiricalL1CoverAtCard {Observation : Type u} {Index : Type v}
    {n : ℕ} (sample : SampleAt Observation n)
    (indexClass : Set Index) (classFun : Index -> Observation -> ℝ)
    (epsilon : ℝ) (cardinality : ℕ) where
  center : Fin cardinality -> Index
  center_mem : ∀ centerIndex, center centerIndex ∈ indexClass
  centerOf : ∀ index, index ∈ indexClass -> Fin cardinality
  dist_le :
    ∀ index hindex,
      empiricalL1Distance sample (classFun index)
        (classFun (center (centerOf index hindex))) ≤ epsilon

namespace FiniteEmpiricalL1CoverAtCard

/-- The finite center set of a supplied empirical `L1(P_n)` net. -/
def centerSet {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality : ℕ}
    (cover :
      FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon cardinality) :
    Set Index :=
  Set.range cover.center

/-- The supplied empirical-net center set is finite. -/
theorem finite_centerSet {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality : ℕ}
    (cover :
      FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon cardinality) :
    cover.centerSet.Finite :=
  Set.finite_range cover.center

/-- The supplied empirical-net centers lie in the target class. -/
theorem centerSet_subset {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality : ℕ}
    (cover :
      FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon cardinality) :
    cover.centerSet ⊆ indexClass := by
  intro index hindex
  rcases hindex with ⟨centerIndex, rfl⟩
  exact cover.center_mem centerIndex

/-- Every target index has a supplied empirical-net center within `epsilon`. -/
theorem exists_center {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality : ℕ}
    (cover :
      FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon cardinality)
    {index : Index} (hindex : index ∈ indexClass) :
    ∃ center, center ∈ cover.centerSet ∧ center ∈ indexClass ∧
      empiricalL1Distance sample (classFun index) (classFun center) ≤ epsilon := by
  refine ⟨cover.center (cover.centerOf index hindex), ?_, ?_, ?_⟩
  · exact ⟨cover.centerOf index hindex, rfl⟩
  · exact cover.center_mem (cover.centerOf index hindex)
  · exact cover.dist_le index hindex

/--
A supplied empirical cover of a nonempty class has positive cardinality.

This packages the `centerOf` field as the positivity bridge needed by
finite-center maximal and tail bounds that use a nonempty `Fin cardinality`
index type.
-/
theorem cardinality_pos_of_nonempty {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality : ℕ}
    (cover :
      FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon cardinality)
    (hindexClass : ∃ index, index ∈ indexClass) :
    0 < cardinality := by
  rcases hindexClass with ⟨index, hindex⟩
  exact lt_of_le_of_lt (Nat.zero_le _) (cover.centerOf index hindex).isLt

/--
Pad a supplied empirical cover to any larger cardinality.

The extra slots are filled with an arbitrary class member, so this is only
available for nonempty classes.  This bridges least-cardinality `Nat.find`
covers to externally supplied cardinality bounds.
-/
noncomputable def pad_cardinality {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality largerCardinality : ℕ}
    (cover :
      FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon cardinality)
    (hindexClass : ∃ index, index ∈ indexClass)
    (hle : cardinality ≤ largerCardinality) :
    FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
      largerCardinality := by
  classical
  let baseIndex : Index := hindexClass.choose
  have hbaseIndex : baseIndex ∈ indexClass := hindexClass.choose_spec
  refine
    { center := fun centerIndex =>
        if hlt : (centerIndex : ℕ) < cardinality then
          cover.center ⟨centerIndex, hlt⟩
        else
          baseIndex
      center_mem := ?_
      centerOf := fun index hindex => Fin.castLE hle (cover.centerOf index hindex)
      dist_le := ?_ }
  · intro centerIndex
    by_cases hlt : (centerIndex : ℕ) < cardinality
    · simp [hlt, cover.center_mem]
    · simp [hlt, hbaseIndex]
  · intro index hindex
    have hlt :
        ((Fin.castLE hle (cover.centerOf index hindex) :
          Fin largerCardinality) : ℕ) < cardinality := by
      exact (cover.centerOf index hindex).isLt
    simpa [hlt] using cover.dist_le index hindex

end FiniteEmpiricalL1CoverAtCard

/-- Finite empirical `L1(P_n)` covering hypothesis in witness form. -/
def HasFiniteEmpiricalL1Cover {Observation : Type u} {Index : Type v}
    {n : ℕ} (sample : SampleAt Observation n)
    (indexClass : Set Index) (classFun : Index -> Observation -> ℝ)
    (epsilon : ℝ) : Prop :=
  ∃ cardinality : ℕ,
    Nonempty
      (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon cardinality)

/-- The least supplied finite empirical `L1(P_n)` cover cardinality. -/
noncomputable def finiteEmpiricalL1CoveringNumberCard
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    (hfinite :
      HasFiniteEmpiricalL1Cover sample indexClass classFun epsilon) : ℕ :=
  by
    classical
    exact Nat.find hfinite

/-- The least finite empirical-cover cardinality is invariant under sample equality. -/
theorem finiteEmpiricalL1CoveringNumberCard_congr_sample
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample sample' : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    (hsample : sample = sample')
    (hfinite :
      HasFiniteEmpiricalL1Cover sample indexClass classFun epsilon)
    (hfinite' :
      HasFiniteEmpiricalL1Cover sample' indexClass classFun epsilon) :
    finiteEmpiricalL1CoveringNumberCard hfinite =
      finiteEmpiricalL1CoveringNumberCard hfinite' := by
  subst hsample
  simp [finiteEmpiricalL1CoveringNumberCard]

/--
The deterministic empirical `L1(P_n)` covering number.

If a finite empirical `epsilon`-net exists, this is the least supplied
cardinality, coerced to `ℕ∞`; otherwise it is `⊤`.
-/
noncomputable def empiricalL1CoveringNumber
    {Observation : Type u} {Index : Type v} {n : ℕ}
    (sample : SampleAt Observation n)
    (indexClass : Set Index) (classFun : Index -> Observation -> ℝ)
    (epsilon : ℝ) : ℕ∞ :=
  by
    classical
    exact
      if hfinite :
          HasFiniteEmpiricalL1Cover sample indexClass classFun epsilon then
        (finiteEmpiricalL1CoveringNumberCard hfinite : ℕ∞)
      else
        ⊤

/-- In the finite case, the empirical covering number is the `Nat.find` cardinality. -/
theorem empiricalL1CoveringNumber_eq_find
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    (hfinite :
      HasFiniteEmpiricalL1Cover sample indexClass classFun epsilon) :
    empiricalL1CoveringNumber sample indexClass classFun epsilon =
      (finiteEmpiricalL1CoveringNumberCard hfinite : ℕ∞) := by
  classical
  simp [empiricalL1CoveringNumber, hfinite]

/--
The least finite empirical-cover cardinality is bounded by any supplied finite
upper bound on the numeric empirical covering number.
-/
theorem finiteEmpiricalL1CoveringNumberCard_le_of_empiricalL1CoveringNumber_le
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality : ℕ}
    (hfinite :
      HasFiniteEmpiricalL1Cover sample indexClass classFun epsilon)
    (hcovering_le :
      empiricalL1CoveringNumber sample indexClass classFun epsilon ≤
        (cardinality : ℕ∞)) :
    finiteEmpiricalL1CoveringNumberCard hfinite ≤ cardinality := by
  have hfind_le_card_enat :
      (finiteEmpiricalL1CoveringNumberCard hfinite : ℕ∞) ≤
        (cardinality : ℕ∞) := by
    rwa [empiricalL1CoveringNumber_eq_find hfinite] at hcovering_le
  exact_mod_cast hfind_le_card_enat

/-- The minimizing empirical cover cardinality has an explicit supplied cover. -/
theorem empiricalL1CoveringNumber_find_spec
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    (hfinite :
      HasFiniteEmpiricalL1Cover sample indexClass classFun epsilon) :
    Nonempty
      (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
        (finiteEmpiricalL1CoveringNumberCard hfinite)) :=
  by
    classical
    simpa [finiteEmpiricalL1CoveringNumberCard] using Nat.find_spec hfinite

/--
Any explicit fixed-cardinality empirical cover bounds the numeric empirical
covering number.

This is the forward handoff from proof-carrying finite nets back to the
`ℕ∞`-valued entropy displays used in VdV&W.
-/
theorem empiricalL1CoveringNumber_le_of_coverAtCard
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality : ℕ}
    (hcover :
      Nonempty
        (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
          cardinality)) :
    empiricalL1CoveringNumber sample indexClass classFun epsilon ≤
      (cardinality : ℕ∞) := by
  classical
  let hfinite :
      HasFiniteEmpiricalL1Cover sample indexClass classFun epsilon :=
    ⟨cardinality, hcover⟩
  have hcard :
      finiteEmpiricalL1CoveringNumberCard hfinite ≤ cardinality := by
    simpa [finiteEmpiricalL1CoveringNumberCard] using
      (Nat.find_min' hfinite hcover)
  rw [empiricalL1CoveringNumber_eq_find hfinite]
  exact_mod_cast hcard

/-- A finite empirical-cover witness makes the numeric covering number finite. -/
theorem empiricalL1CoveringNumber_lt_top_of_hasFinite
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    (hfinite :
      HasFiniteEmpiricalL1Cover sample indexClass classFun epsilon) :
    empiricalL1CoveringNumber sample indexClass classFun epsilon < ⊤ := by
  rw [empiricalL1CoveringNumber_eq_find hfinite]
  exact WithTop.coe_lt_top (finiteEmpiricalL1CoveringNumberCard hfinite)

/-- If the numeric empirical covering number is finite, a finite witness exists. -/
theorem hasFinite_of_empiricalL1CoveringNumber_lt_top
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    (hfinite_number :
      empiricalL1CoveringNumber sample indexClass classFun epsilon < ⊤) :
    HasFiniteEmpiricalL1Cover sample indexClass classFun epsilon := by
  by_contra hnot
  have htop :
      empiricalL1CoveringNumber sample indexClass classFun epsilon = ⊤ := by
    classical
    simp [empiricalL1CoveringNumber, hnot]
  rw [htop] at hfinite_number
  exact (lt_irrefl (⊤ : ℕ∞)) hfinite_number

/--
Witness-free characterization of a fixed-cardinality empirical `L1(P_n)` cover.

This removes the proof-carrying `centerOf` field from measurable event
arguments: a cover exists iff there is a finite center map whose centers lie in
the class and every class member is within `epsilon` of one of those centers.
-/
theorem nonempty_finiteEmpiricalL1CoverAtCard_iff_exists_centers
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality : ℕ} :
    Nonempty
        (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
          cardinality) ↔
      ∃ center : Fin cardinality -> Index,
        (∀ centerIndex, center centerIndex ∈ indexClass) ∧
          ∀ index, index ∈ indexClass ->
            ∃ centerIndex,
              empiricalL1Distance sample (classFun index)
                (classFun (center centerIndex)) ≤ epsilon := by
  constructor
  · rintro ⟨cover⟩
    exact
      ⟨cover.center, cover.center_mem, fun index hindex =>
        ⟨cover.centerOf index hindex, cover.dist_le index hindex⟩⟩
  · rintro ⟨center, hcenter_mem, hcover⟩
    classical
    let centerOf : ∀ index, index ∈ indexClass -> Fin cardinality :=
      fun index hindex => Classical.choose (hcover index hindex)
    have hdist :
        ∀ index hindex,
          empiricalL1Distance sample (classFun index)
              (classFun (center (centerOf index hindex))) ≤
            epsilon :=
      fun index hindex => Classical.choose_spec (hcover index hindex)
    exact
      ⟨{ center := center
         center_mem := hcenter_mem
         centerOf := centerOf
         dist_le := hdist }⟩

/--
Enumerate a finite internal empirical-net center set as a
`FiniteEmpiricalL1CoverAtCard`.

This is the set-level adapter needed for later bridges from mathlib internal
metric covers or maximal separated sets: once a finite set of indices lies in
the class and covers every class member in empirical `L1(P_n)`, it can be
converted to the local proof-carrying finite-net structure whose centers are
indexed by `Fin`.
-/
theorem nonempty_finiteEmpiricalL1CoverAtCard_of_finite_centerSet
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass centerSet : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    (hcenter_finite : centerSet.Finite)
    (hcenter_subset : centerSet ⊆ indexClass)
    (hcover :
      ∀ index, index ∈ indexClass ->
        ∃ center, center ∈ centerSet ∧
          empiricalL1Distance sample (classFun index) (classFun center) ≤
            epsilon) :
    Nonempty
      (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
        hcenter_finite.toFinset.card) := by
  classical
  let center : Fin hcenter_finite.toFinset.card -> Index :=
    fun centerIndex =>
      ((hcenter_finite.toFinset.equivFin).symm centerIndex).1
  let centerOf :
      ∀ index, index ∈ indexClass -> Fin hcenter_finite.toFinset.card :=
    fun index hindex =>
      hcenter_finite.toFinset.equivFin
        ⟨Classical.choose (hcover index hindex),
          (hcenter_finite.mem_toFinset).2
            (Classical.choose_spec (hcover index hindex)).1⟩
  have hcenter_mem : ∀ centerIndex, center centerIndex ∈ indexClass := by
    intro centerIndex
    have hmem_finset :
        (((hcenter_finite.toFinset.equivFin).symm centerIndex).1 : Index) ∈
          hcenter_finite.toFinset :=
      ((hcenter_finite.toFinset.equivFin).symm centerIndex).2
    exact hcenter_subset ((hcenter_finite.mem_toFinset).1 hmem_finset)
  have hdist :
      ∀ index hindex,
        empiricalL1Distance sample (classFun index)
          (classFun (center (centerOf index hindex))) ≤ epsilon := by
    intro index hindex
    have hchosen := Classical.choose_spec (hcover index hindex)
    have hcenter_eq :
        center (centerOf index hindex) =
          Classical.choose (hcover index hindex) := by
      simp [center, centerOf]
    simpa [hcenter_eq] using hchosen.2
  exact
    ⟨{ center := center
       center_mem := hcenter_mem
       centerOf := centerOf
       dist_le := hdist }⟩

/--
Padded-cardinality form of
`nonempty_finiteEmpiricalL1CoverAtCard_of_finite_centerSet`.

This is useful after a geometric packing or grid argument gives only an upper
bound on the finite center-set cardinality.  The padding uses a supplied
nonempty class member, matching the existing `pad_cardinality` bridge.
-/
theorem nonempty_finiteEmpiricalL1CoverAtCard_of_finite_centerSet_card_le
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass centerSet : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality : ℕ}
    (hcenter_finite : centerSet.Finite)
    (hcenter_subset : centerSet ⊆ indexClass)
    (hcover :
      ∀ index, index ∈ indexClass ->
        ∃ center, center ∈ centerSet ∧
          empiricalL1Distance sample (classFun index) (classFun center) ≤
            epsilon)
    (hindexClass : ∃ index, index ∈ indexClass)
    (hcard_le : hcenter_finite.toFinset.card ≤ cardinality) :
    Nonempty
      (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
        cardinality) := by
  exact
    (nonempty_finiteEmpiricalL1CoverAtCard_of_finite_centerSet
      hcenter_finite hcenter_subset hcover).elim fun cover =>
      ⟨cover.pad_cardinality hindexClass hcard_le⟩

/--
A finite internal center set also bounds the numeric empirical covering number.
-/
theorem empiricalL1CoveringNumber_le_of_finite_centerSet
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass centerSet : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    (hcenter_finite : centerSet.Finite)
    (hcenter_subset : centerSet ⊆ indexClass)
    (hcover :
      ∀ index, index ∈ indexClass ->
        ∃ center, center ∈ centerSet ∧
          empiricalL1Distance sample (classFun index) (classFun center) ≤
            epsilon) :
    empiricalL1CoveringNumber sample indexClass classFun epsilon ≤
      (hcenter_finite.toFinset.card : ℕ∞) := by
  exact
    empiricalL1CoveringNumber_le_of_coverAtCard
      (nonempty_finiteEmpiricalL1CoverAtCard_of_finite_centerSet
        hcenter_finite hcenter_subset hcover)

/--
Cardinality-padded finite-center-set bound for the numeric empirical covering
number.
-/
theorem empiricalL1CoveringNumber_le_of_finite_centerSet_card_le
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass centerSet : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality : ℕ}
    (hcenter_finite : centerSet.Finite)
    (hcenter_subset : centerSet ⊆ indexClass)
    (hcover :
      ∀ index, index ∈ indexClass ->
        ∃ center, center ∈ centerSet ∧
          empiricalL1Distance sample (classFun index) (classFun center) ≤
            epsilon)
    (hcard_le : hcenter_finite.toFinset.card ≤ cardinality) :
    empiricalL1CoveringNumber sample indexClass classFun epsilon ≤
      (cardinality : ℕ∞) := by
  exact
    (empiricalL1CoveringNumber_le_of_finite_centerSet
      hcenter_finite hcenter_subset hcover).trans (by exact_mod_cast hcard_le)

/--
A finite set of representatives for fixed-sample traces gives a local empirical
`L1(P_n)` cover.

This is the theorem-facing fixed-sample bridge needed by finite-trace,
VC/Sauer, and discretization routes: it separates the combinatorial task
(choose finitely many trace representatives) from the empirical-cover witness.
-/
theorem nonempty_finiteEmpiricalL1CoverAtCard_of_finite_trace_centerSet
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass centerSet : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    (hcenter_finite : centerSet.Finite)
    (hcenter_subset : centerSet ⊆ indexClass)
    (htrace_cover :
      ∀ index, index ∈ indexClass ->
        ∃ center, center ∈ centerSet ∧
          empiricalTrace sample classFun index =
            empiricalTrace sample classFun center)
    (hepsilon_nonneg : 0 ≤ epsilon) :
    Nonempty
      (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
        hcenter_finite.toFinset.card) := by
  refine
    nonempty_finiteEmpiricalL1CoverAtCard_of_finite_centerSet
      hcenter_finite hcenter_subset ?_
  intro index hindex
  rcases htrace_cover index hindex with ⟨center, hcenter, htrace⟩
  exact
    ⟨center, hcenter,
      empiricalL1Distance_le_of_empiricalTrace_eq hepsilon_nonneg htrace⟩

/--
Padded-cardinality fixed-sample trace cover.  This is useful when a
combinatorial argument controls the number of distinct traces by a simpler
terminal bound such as a polynomial in the sample size.
-/
theorem nonempty_finiteEmpiricalL1CoverAtCard_of_finite_trace_centerSet_card_le
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass centerSet : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality : ℕ}
    (hcenter_finite : centerSet.Finite)
    (hcenter_subset : centerSet ⊆ indexClass)
    (htrace_cover :
      ∀ index, index ∈ indexClass ->
        ∃ center, center ∈ centerSet ∧
          empiricalTrace sample classFun index =
            empiricalTrace sample classFun center)
    (hepsilon_nonneg : 0 ≤ epsilon)
    (hindexClass : ∃ index, index ∈ indexClass)
    (hcard_le : hcenter_finite.toFinset.card ≤ cardinality) :
    Nonempty
      (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
        cardinality) := by
  exact
    (nonempty_finiteEmpiricalL1CoverAtCard_of_finite_trace_centerSet
      hcenter_finite hcenter_subset htrace_cover hepsilon_nonneg).elim
      fun cover => ⟨cover.pad_cardinality hindexClass hcard_le⟩

/-- Numeric empirical-covering-number bound from finite trace representatives. -/
theorem empiricalL1CoveringNumber_le_of_finite_trace_centerSet
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass centerSet : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    (hcenter_finite : centerSet.Finite)
    (hcenter_subset : centerSet ⊆ indexClass)
    (htrace_cover :
      ∀ index, index ∈ indexClass ->
        ∃ center, center ∈ centerSet ∧
          empiricalTrace sample classFun index =
            empiricalTrace sample classFun center)
    (hepsilon_nonneg : 0 ≤ epsilon) :
    empiricalL1CoveringNumber sample indexClass classFun epsilon ≤
      (hcenter_finite.toFinset.card : ℕ∞) := by
  exact
    empiricalL1CoveringNumber_le_of_coverAtCard
      (nonempty_finiteEmpiricalL1CoverAtCard_of_finite_trace_centerSet
        hcenter_finite hcenter_subset htrace_cover hepsilon_nonneg)

/--
Cardinality-padded numeric empirical-covering-number bound from finite trace
representatives.
-/
theorem empiricalL1CoveringNumber_le_of_finite_trace_centerSet_card_le
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass centerSet : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality : ℕ}
    (hcenter_finite : centerSet.Finite)
    (hcenter_subset : centerSet ⊆ indexClass)
    (htrace_cover :
      ∀ index, index ∈ indexClass ->
        ∃ center, center ∈ centerSet ∧
          empiricalTrace sample classFun index =
            empiricalTrace sample classFun center)
    (hepsilon_nonneg : 0 ≤ epsilon)
    (hcard_le : hcenter_finite.toFinset.card ≤ cardinality) :
    empiricalL1CoveringNumber sample indexClass classFun epsilon ≤
      (cardinality : ℕ∞) := by
  exact
    (empiricalL1CoveringNumber_le_of_finite_trace_centerSet
      hcenter_finite hcenter_subset htrace_cover hepsilon_nonneg).trans
      (by exact_mod_cast hcard_le)

/--
If only finitely many fixed-sample traces occur on the class, then those traces
choose representatives that form an empirical `L1(P_n)` cover.

This removes the explicit representative-set hypothesis from
`nonempty_finiteEmpiricalL1CoverAtCard_of_finite_trace_centerSet` and is the
direct fixed-sample trace-count primitive used by finite-trace/VC arguments.
-/
theorem nonempty_finiteEmpiricalL1CoverAtCard_of_finite_trace_image
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    (htrace_finite :
      (empiricalTrace sample classFun '' indexClass).Finite)
    (hepsilon_nonneg : 0 ≤ epsilon) :
    Nonempty
      (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
        htrace_finite.toFinset.card) := by
  classical
  let traceSet : Set (Fin n -> ℝ) :=
    empiricalTrace sample classFun '' indexClass
  let traceFinset := htrace_finite.toFinset
  let center : Fin htrace_finite.toFinset.card -> Index :=
    fun centerIndex =>
      Classical.choose
        ((htrace_finite.mem_toFinset).1
          (((htrace_finite.toFinset.equivFin).symm centerIndex).2))
  let centerOf :
      ∀ index, index ∈ indexClass -> Fin htrace_finite.toFinset.card :=
    fun index hindex =>
      htrace_finite.toFinset.equivFin
        ⟨empiricalTrace sample classFun index,
          (htrace_finite.mem_toFinset).2 ⟨index, hindex, rfl⟩⟩
  have hcenter_mem :
      ∀ centerIndex, center centerIndex ∈ indexClass := by
    intro centerIndex
    have hchosen :=
      Classical.choose_spec
        ((htrace_finite.mem_toFinset).1
          (((htrace_finite.toFinset.equivFin).symm centerIndex).2))
    exact hchosen.1
  have hdist :
      ∀ index hindex,
        empiricalL1Distance sample (classFun index)
          (classFun (center (centerOf index hindex))) ≤ epsilon := by
    intro index hindex
    have hchosen :=
      Classical.choose_spec
        ((htrace_finite.mem_toFinset).1
          (((htrace_finite.toFinset.equivFin).symm
            (centerOf index hindex)).2))
    have htrace :
        empiricalTrace sample classFun index =
          empiricalTrace sample classFun (center (centerOf index hindex)) := by
      simpa [center, centerOf] using hchosen.2.symm
    exact empiricalL1Distance_le_of_empiricalTrace_eq hepsilon_nonneg htrace
  exact
    ⟨{ center := center
       center_mem := hcenter_mem
       centerOf := centerOf
       dist_le := hdist }⟩

/--
Padded-cardinality empirical cover from a finite approximate code.

This is the approximate analogue of
`nonempty_finiteEmpiricalL1CoverAtCard_of_finite_trace_image`: instead of
requiring equal empirical traces, it is enough that two class indices with the
same finite code are within `epsilon` in empirical `L1(P_n)`.  This is the
primitive needed for quantized-trace/grid entropy arguments, where exact trace
equality is too strong.
-/
theorem nonempty_finiteEmpiricalL1CoverAtCard_of_finite_approx_code
    {Observation : Type u} {Index : Type v} {Code : Type*} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    (code : Index -> Code)
    (hcode_finite : (code '' indexClass).Finite)
    (happrox :
      ∀ index, index ∈ indexClass ->
        ∀ center, center ∈ indexClass ->
          code index = code center ->
            empiricalL1Distance sample (classFun index) (classFun center) ≤
              epsilon) :
    Nonempty
      (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
        hcode_finite.toFinset.card) := by
  classical
  let center : Fin hcode_finite.toFinset.card -> Index :=
    fun codeIndex =>
      Classical.choose
        ((hcode_finite.mem_toFinset).1
          (((hcode_finite.toFinset.equivFin).symm codeIndex).2))
  let centerOf :
      ∀ index, index ∈ indexClass -> Fin hcode_finite.toFinset.card :=
    fun index hindex =>
      hcode_finite.toFinset.equivFin
        ⟨code index, (hcode_finite.mem_toFinset).2 ⟨index, hindex, rfl⟩⟩
  have hcenter_mem : ∀ codeIndex, center codeIndex ∈ indexClass := by
    intro codeIndex
    have hchosen :=
      Classical.choose_spec
        ((hcode_finite.mem_toFinset).1
          (((hcode_finite.toFinset.equivFin).symm codeIndex).2))
    exact hchosen.1
  have hdist :
      ∀ index hindex,
        empiricalL1Distance sample (classFun index)
          (classFun (center (centerOf index hindex))) ≤ epsilon := by
    intro index hindex
    have hchosen :=
      Classical.choose_spec
        ((hcode_finite.mem_toFinset).1
          (((hcode_finite.toFinset.equivFin).symm
            (centerOf index hindex)).2))
    have hcode_eq : code index = code (center (centerOf index hindex)) := by
      simpa [center, centerOf] using hchosen.2.symm
    exact happrox index hindex (center (centerOf index hindex))
      (hcenter_mem (centerOf index hindex)) hcode_eq
  exact
    ⟨{ center := center
       center_mem := hcenter_mem
       centerOf := centerOf
       dist_le := hdist }⟩

/--
Numeric empirical-covering-number bound by the number of distinct fixed-sample
traces.
-/
theorem empiricalL1CoveringNumber_le_of_finite_trace_image
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    (htrace_finite :
      (empiricalTrace sample classFun '' indexClass).Finite)
    (hepsilon_nonneg : 0 ≤ epsilon) :
    empiricalL1CoveringNumber sample indexClass classFun epsilon ≤
      (htrace_finite.toFinset.card : ℕ∞) := by
  exact
    empiricalL1CoveringNumber_le_of_coverAtCard
      (nonempty_finiteEmpiricalL1CoverAtCard_of_finite_trace_image
        htrace_finite hepsilon_nonneg)

/--
Numeric empirical-covering-number bound from a finite approximate code.
-/
theorem empiricalL1CoveringNumber_le_of_finite_approx_code
    {Observation : Type u} {Index : Type v} {Code : Type*} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    (code : Index -> Code)
    (hcode_finite : (code '' indexClass).Finite)
    (happrox :
      ∀ index, index ∈ indexClass ->
        ∀ center, center ∈ indexClass ->
          code index = code center ->
            empiricalL1Distance sample (classFun index) (classFun center) ≤
              epsilon) :
    empiricalL1CoveringNumber sample indexClass classFun epsilon ≤
      (hcode_finite.toFinset.card : ℕ∞) := by
  exact
    empiricalL1CoveringNumber_le_of_coverAtCard
      (nonempty_finiteEmpiricalL1CoverAtCard_of_finite_approx_code
        code hcode_finite happrox)

/--
Padded-cardinality cover from a finite approximate code and a terminal
cardinality bound.
-/
theorem nonempty_finiteEmpiricalL1CoverAtCard_of_finite_approx_code_card_le
    {Observation : Type u} {Index : Type v} {Code : Type*} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality : ℕ}
    (code : Index -> Code)
    (hcode_finite : (code '' indexClass).Finite)
    (happrox :
      ∀ index, index ∈ indexClass ->
        ∀ center, center ∈ indexClass ->
          code index = code center ->
            empiricalL1Distance sample (classFun index) (classFun center) ≤
              epsilon)
    (hindexClass : ∃ index, index ∈ indexClass)
    (hcard_le : hcode_finite.toFinset.card ≤ cardinality) :
    Nonempty
      (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
        cardinality) := by
  exact
    (nonempty_finiteEmpiricalL1CoverAtCard_of_finite_approx_code
      code hcode_finite happrox).elim fun cover =>
      ⟨cover.pad_cardinality hindexClass hcard_le⟩

/--
Padded numeric empirical-covering-number bound from a finite approximate code
and a terminal cardinality estimate.
-/
theorem empiricalL1CoveringNumber_le_of_finite_approx_code_card_le
    {Observation : Type u} {Index : Type v} {Code : Type*} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality : ℕ}
    (code : Index -> Code)
    (hcode_finite : (code '' indexClass).Finite)
    (happrox :
      ∀ index, index ∈ indexClass ->
        ∀ center, center ∈ indexClass ->
          code index = code center ->
            empiricalL1Distance sample (classFun index) (classFun center) ≤
              epsilon)
    (hcard_le : hcode_finite.toFinset.card ≤ cardinality) :
    empiricalL1CoveringNumber sample indexClass classFun epsilon ≤
      (cardinality : ℕ∞) := by
  exact
    (empiricalL1CoveringNumber_le_of_finite_approx_code
      code hcode_finite happrox).trans (by exact_mod_cast hcard_le)

/--
Padded-cardinality cover from a finite code whose equal-code classes are
pointwise close on the empirical sample.
-/
theorem nonempty_finiteEmpiricalL1CoverAtCard_of_finite_pointwise_approx_code_card_le
    {Observation : Type u} {Index : Type v} {Code : Type*} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality : ℕ}
    (code : Index -> Code)
    (hcode_finite : (code '' indexClass).Finite)
    (hepsilon_nonneg : 0 ≤ epsilon)
    (hpoint :
      ∀ index, index ∈ indexClass ->
        ∀ center, center ∈ indexClass ->
          code index = code center ->
            ∀ sampleIndex : Fin n,
              |classFun index (sample sampleIndex) -
                classFun center (sample sampleIndex)| ≤ epsilon)
    (hindexClass : ∃ index, index ∈ indexClass)
    (hcard_le : hcode_finite.toFinset.card ≤ cardinality) :
    Nonempty
      (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
        cardinality) := by
  exact
    nonempty_finiteEmpiricalL1CoverAtCard_of_finite_approx_code_card_le
      code hcode_finite
      (fun index hindex center hcenter hcode =>
        empiricalL1Distance_le_of_forall_abs_le hepsilon_nonneg
          (hpoint index hindex center hcenter hcode))
      hindexClass hcard_le

/--
Padded numeric empirical-covering-number bound from a finite pointwise
approximation code.
-/
theorem empiricalL1CoveringNumber_le_of_finite_pointwise_approx_code_card_le
    {Observation : Type u} {Index : Type v} {Code : Type*} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality : ℕ}
    (code : Index -> Code)
    (hcode_finite : (code '' indexClass).Finite)
    (hepsilon_nonneg : 0 ≤ epsilon)
    (hpoint :
      ∀ index, index ∈ indexClass ->
        ∀ center, center ∈ indexClass ->
          code index = code center ->
            ∀ sampleIndex : Fin n,
              |classFun index (sample sampleIndex) -
                classFun center (sample sampleIndex)| ≤ epsilon)
    (hcard_le : hcode_finite.toFinset.card ≤ cardinality) :
    empiricalL1CoveringNumber sample indexClass classFun epsilon ≤
      (cardinality : ℕ∞) := by
  exact
    empiricalL1CoveringNumber_le_of_finite_approx_code_card_le
      code hcode_finite
      (fun index hindex center hcenter hcode =>
        empiricalL1Distance_le_of_forall_abs_le hepsilon_nonneg
          (hpoint index hindex center hcenter hcode))
      hcard_le

/--
If all pointwise approximation codes lie in a supplied finite code set, then
the realized code image is finite.
-/
theorem finite_pointwiseApproxCode_image_of_mem_codeSet
    {Index : Type v} {Code : Type*} {indexClass : Set Index}
    (code : Index -> Code) (codeSet : Finset Code)
    (hcode_mem : ∀ index, index ∈ indexClass -> code index ∈ codeSet) :
    (code '' indexClass).Finite := by
  classical
  refine codeSet.finite_toSet.subset ?_
  rintro coded ⟨index, hindex, rfl⟩
  exact hcode_mem index hindex

/--
The realized code-image cardinality is bounded by the supplied finite code-set
cardinality.
-/
theorem pointwiseApproxCode_image_toFinset_card_le_codeSet
    {Index : Type v} {Code : Type*} {indexClass : Set Index}
    (code : Index -> Code) (codeSet : Finset Code)
    (hcode_mem : ∀ index, index ∈ indexClass -> code index ∈ codeSet) :
    (finite_pointwiseApproxCode_image_of_mem_codeSet code codeSet hcode_mem).toFinset.card ≤
      codeSet.card := by
  classical
  apply Finset.card_le_card
  intro coded hcoded
  have hcoded_set :
      coded ∈ code '' indexClass :=
    ((finite_pointwiseApproxCode_image_of_mem_codeSet code codeSet hcode_mem).mem_toFinset).1
      hcoded
  rcases hcoded_set with ⟨index, hindex, rfl⟩
  exact hcode_mem index hindex

/--
Padded-cardinality cover from a finite code set whose equal-code classes are
pointwise close on the empirical sample.
-/
theorem nonempty_finiteEmpiricalL1CoverAtCard_of_finite_pointwise_approx_codeSet_card_le
    {Observation : Type u} {Index : Type v} {Code : Type*} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality : ℕ}
    (code : Index -> Code) (codeSet : Finset Code)
    (hcode_mem : ∀ index, index ∈ indexClass -> code index ∈ codeSet)
    (hepsilon_nonneg : 0 ≤ epsilon)
    (hpoint :
      ∀ index, index ∈ indexClass ->
        ∀ center, center ∈ indexClass ->
          code index = code center ->
            ∀ sampleIndex : Fin n,
              |classFun index (sample sampleIndex) -
                classFun center (sample sampleIndex)| ≤ epsilon)
    (hindexClass : ∃ index, index ∈ indexClass)
    (hcard_le : codeSet.card ≤ cardinality) :
    Nonempty
      (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
        cardinality) := by
  exact
    nonempty_finiteEmpiricalL1CoverAtCard_of_finite_pointwise_approx_code_card_le
      code
      (finite_pointwiseApproxCode_image_of_mem_codeSet code codeSet hcode_mem)
      hepsilon_nonneg hpoint hindexClass
      ((pointwiseApproxCode_image_toFinset_card_le_codeSet code codeSet hcode_mem).trans
        hcard_le)

/--
Numeric empirical-covering-number bound from a finite code set whose equal-code
classes are pointwise close on the empirical sample.
-/
theorem empiricalL1CoveringNumber_le_of_finite_pointwise_approx_codeSet_card_le
    {Observation : Type u} {Index : Type v} {Code : Type*} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality : ℕ}
    (code : Index -> Code) (codeSet : Finset Code)
    (hcode_mem : ∀ index, index ∈ indexClass -> code index ∈ codeSet)
    (hepsilon_nonneg : 0 ≤ epsilon)
    (hpoint :
      ∀ index, index ∈ indexClass ->
        ∀ center, center ∈ indexClass ->
          code index = code center ->
            ∀ sampleIndex : Fin n,
              |classFun index (sample sampleIndex) -
                classFun center (sample sampleIndex)| ≤ epsilon)
    (hcard_le : codeSet.card ≤ cardinality) :
    empiricalL1CoveringNumber sample indexClass classFun epsilon ≤
      (cardinality : ℕ∞) := by
  exact
    empiricalL1CoveringNumber_le_of_finite_pointwise_approx_code_card_le
      code
      (finite_pointwiseApproxCode_image_of_mem_codeSet code codeSet hcode_mem)
      hepsilon_nonneg hpoint
      ((pointwiseApproxCode_image_toFinset_card_le_codeSet code codeSet hcode_mem).trans
        hcard_le)

/--
If each sample coordinate of a code takes values in a finite coordinate code
set, then the realized vector-code image is finite.
-/
theorem finite_coordinateCode_image
    {Index : Type v} {CoordCode : Type*} [DecidableEq CoordCode] {n : ℕ}
    {indexClass : Set Index}
    (code : Index -> Fin n -> CoordCode)
    (codeSets : Fin n -> Finset CoordCode)
    (hcode_mem :
      ∀ index, index ∈ indexClass ->
        ∀ sampleIndex : Fin n, code index sampleIndex ∈ codeSets sampleIndex) :
    (code '' indexClass).Finite := by
  classical
  let vectorCodeSet : Finset (Fin n -> CoordCode) :=
    Fintype.piFinset codeSets
  have himage_subset : code '' indexClass ⊆
      (vectorCodeSet : Set (Fin n -> CoordCode)) := by
    rintro coded ⟨index, hindex, rfl⟩
    exact Fintype.mem_piFinset.2 fun sampleIndex =>
      hcode_mem index hindex sampleIndex
  exact vectorCodeSet.finite_toSet.subset himage_subset

/--
The cardinality of the realized vector-code image is bounded by the product
of the coordinate code-set cardinalities.
-/
theorem coordinateCode_image_toFinset_card_le_prod
    {Index : Type v} {CoordCode : Type*} [DecidableEq CoordCode] {n : ℕ}
    {indexClass : Set Index}
    (code : Index -> Fin n -> CoordCode)
    (codeSets : Fin n -> Finset CoordCode)
    (hcode_mem :
      ∀ index, index ∈ indexClass ->
        ∀ sampleIndex : Fin n, code index sampleIndex ∈ codeSets sampleIndex) :
    (finite_coordinateCode_image code codeSets hcode_mem).toFinset.card ≤
      ∏ sampleIndex : Fin n, (codeSets sampleIndex).card := by
  classical
  let codeImage : Set (Fin n -> CoordCode) := code '' indexClass
  let vectorCodeSet : Finset (Fin n -> CoordCode) :=
    Fintype.piFinset codeSets
  have hcode_finite : codeImage.Finite :=
    finite_coordinateCode_image
      (indexClass := indexClass) code codeSets hcode_mem
  have himage_subset : codeImage ⊆
      (vectorCodeSet : Set (Fin n -> CoordCode)) := by
    rintro coded ⟨index, hindex, rfl⟩
    exact Fintype.mem_piFinset.2 fun sampleIndex =>
      hcode_mem index hindex sampleIndex
  have hle :
      codeImage.ncard ≤ (vectorCodeSet : Set (Fin n -> CoordCode)).ncard :=
    Set.ncard_le_ncard_of_injOn
      (s := codeImage) (t := (vectorCodeSet : Set (Fin n -> CoordCode)))
      id (fun coded hcoded => himage_subset hcoded)
      (by
        intro coded₁ _ coded₂ _ hcoded
        simpa using hcoded)
      vectorCodeSet.finite_toSet
  have htarget :
      (vectorCodeSet : Set (Fin n -> CoordCode)).ncard =
        vectorCodeSet.card := by
    exact Set.ncard_coe_finset vectorCodeSet
  have htarget_card :
      vectorCodeSet.card =
        ∏ sampleIndex : Fin n, (codeSets sampleIndex).card := by
    simp [vectorCodeSet]
  rw [Set.ncard_eq_toFinset_card codeImage hcode_finite, htarget,
    htarget_card] at hle
  simpa [codeImage] using hle

/--
Padded-cardinality cover from a coordinatewise finite code whose equal-code
classes are pointwise close on the empirical sample.
-/
theorem nonempty_finiteEmpiricalL1CoverAtCard_of_coordinate_pointwise_approx_code_card_le
    {Observation : Type u} {Index : Type v} {CoordCode : Type*}
    [DecidableEq CoordCode] {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality : ℕ}
    (code : Index -> Fin n -> CoordCode)
    (codeSets : Fin n -> Finset CoordCode)
    (hcode_mem :
      ∀ index, index ∈ indexClass ->
        ∀ sampleIndex : Fin n, code index sampleIndex ∈ codeSets sampleIndex)
    (hepsilon_nonneg : 0 ≤ epsilon)
    (hpoint :
      ∀ index, index ∈ indexClass ->
        ∀ center, center ∈ indexClass ->
          code index = code center ->
            ∀ sampleIndex : Fin n,
              |classFun index (sample sampleIndex) -
                classFun center (sample sampleIndex)| ≤ epsilon)
    (hindexClass : ∃ index, index ∈ indexClass)
    (hcard_le :
      (∏ sampleIndex : Fin n, (codeSets sampleIndex).card) ≤ cardinality) :
    Nonempty
      (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
        cardinality) := by
  let hcode_finite :
      (code '' indexClass).Finite :=
    finite_coordinateCode_image code codeSets hcode_mem
  exact
    nonempty_finiteEmpiricalL1CoverAtCard_of_finite_pointwise_approx_code_card_le
      code hcode_finite hepsilon_nonneg hpoint hindexClass
      ((coordinateCode_image_toFinset_card_le_prod code codeSets hcode_mem).trans
        hcard_le)

/--
Numeric empirical-covering-number bound from a coordinatewise finite pointwise
approximation code.
-/
theorem empiricalL1CoveringNumber_le_of_coordinate_pointwise_approx_code_card_le
    {Observation : Type u} {Index : Type v} {CoordCode : Type*}
    [DecidableEq CoordCode] {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality : ℕ}
    (code : Index -> Fin n -> CoordCode)
    (codeSets : Fin n -> Finset CoordCode)
    (hcode_mem :
      ∀ index, index ∈ indexClass ->
        ∀ sampleIndex : Fin n, code index sampleIndex ∈ codeSets sampleIndex)
    (hepsilon_nonneg : 0 ≤ epsilon)
    (hpoint :
      ∀ index, index ∈ indexClass ->
        ∀ center, center ∈ indexClass ->
          code index = code center ->
            ∀ sampleIndex : Fin n,
              |classFun index (sample sampleIndex) -
                classFun center (sample sampleIndex)| ≤ epsilon)
    (hcard_le :
      (∏ sampleIndex : Fin n, (codeSets sampleIndex).card) ≤ cardinality) :
    empiricalL1CoveringNumber sample indexClass classFun epsilon ≤
      (cardinality : ℕ∞) := by
  let hcode_finite :
      (code '' indexClass).Finite :=
    finite_coordinateCode_image code codeSets hcode_mem
  exact
    empiricalL1CoveringNumber_le_of_finite_pointwise_approx_code_card_le
      code hcode_finite hepsilon_nonneg hpoint
      ((coordinateCode_image_toFinset_card_le_prod code codeSets hcode_mem).trans
        hcard_le)

/--
Padded-cardinality cover from a scalar quantizer applied coordinatewise to the
empirical sample.  Equal vector codes reduce to equal coordinate quantizer
codes, so the caller only has to prove the coordinatewise error bound for the
scalar quantizer.
-/
theorem nonempty_finiteEmpiricalL1CoverAtCard_of_coordinate_scalarQuantizer_card_le
    {Observation : Type u} {Index : Type v} {CoordCode : Type*}
    [DecidableEq CoordCode] {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality : ℕ}
    (quantizer : Fin n -> ℝ -> CoordCode)
    (codeSets : Fin n -> Finset CoordCode)
    (hquantizer_mem :
      ∀ index, index ∈ indexClass ->
        ∀ sampleIndex : Fin n,
          quantizer sampleIndex (classFun index (sample sampleIndex)) ∈
            codeSets sampleIndex)
    (hepsilon_nonneg : 0 ≤ epsilon)
    (hquantizer_close :
      ∀ sampleIndex : Fin n,
        ∀ index, index ∈ indexClass ->
          ∀ center, center ∈ indexClass ->
            quantizer sampleIndex (classFun index (sample sampleIndex)) =
              quantizer sampleIndex (classFun center (sample sampleIndex)) ->
            |classFun index (sample sampleIndex) -
              classFun center (sample sampleIndex)| ≤ epsilon)
    (hindexClass : ∃ index, index ∈ indexClass)
    (hcard_le :
      (∏ sampleIndex : Fin n, (codeSets sampleIndex).card) ≤ cardinality) :
    Nonempty
      (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
        cardinality) := by
  let code : Index -> Fin n -> CoordCode :=
    fun index sampleIndex =>
      quantizer sampleIndex (classFun index (sample sampleIndex))
  exact
    nonempty_finiteEmpiricalL1CoverAtCard_of_coordinate_pointwise_approx_code_card_le
      code codeSets hquantizer_mem hepsilon_nonneg
      (fun index hindex center hcenter hcode sampleIndex =>
        hquantizer_close sampleIndex index hindex center hcenter
          (congrFun hcode sampleIndex))
      hindexClass hcard_le

/--
Numeric empirical-covering-number bound from a scalar quantizer applied
coordinatewise to the empirical sample.
-/
theorem empiricalL1CoveringNumber_le_of_coordinate_scalarQuantizer_card_le
    {Observation : Type u} {Index : Type v} {CoordCode : Type*}
    [DecidableEq CoordCode] {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality : ℕ}
    (quantizer : Fin n -> ℝ -> CoordCode)
    (codeSets : Fin n -> Finset CoordCode)
    (hquantizer_mem :
      ∀ index, index ∈ indexClass ->
        ∀ sampleIndex : Fin n,
          quantizer sampleIndex (classFun index (sample sampleIndex)) ∈
            codeSets sampleIndex)
    (hepsilon_nonneg : 0 ≤ epsilon)
    (hquantizer_close :
      ∀ sampleIndex : Fin n,
        ∀ index, index ∈ indexClass ->
          ∀ center, center ∈ indexClass ->
            quantizer sampleIndex (classFun index (sample sampleIndex)) =
              quantizer sampleIndex (classFun center (sample sampleIndex)) ->
            |classFun index (sample sampleIndex) -
              classFun center (sample sampleIndex)| ≤ epsilon)
    (hcard_le :
      (∏ sampleIndex : Fin n, (codeSets sampleIndex).card) ≤ cardinality) :
    empiricalL1CoveringNumber sample indexClass classFun epsilon ≤
      (cardinality : ℕ∞) := by
  let code : Index -> Fin n -> CoordCode :=
    fun index sampleIndex =>
      quantizer sampleIndex (classFun index (sample sampleIndex))
  exact
    empiricalL1CoveringNumber_le_of_coordinate_pointwise_approx_code_card_le
      code codeSets hquantizer_mem hepsilon_nonneg
      (fun index hindex center hcenter hcode sampleIndex =>
        hquantizer_close sampleIndex index hindex center hcenter
          (congrFun hcode sampleIndex))
      hcard_le

/--
If two real values are both within `epsilon / 2` of a common decoded center,
then they are within `epsilon` of each other.
-/
theorem abs_sub_le_of_abs_sub_decode_le_half
    {x y center epsilon : ℝ}
    (hx : |x - center| ≤ epsilon / 2)
    (hy : |y - center| ≤ epsilon / 2) :
    |x - y| ≤ epsilon := by
  calc
    |x - y| = |(x - center) + (center - y)| := by ring_nf
    _ ≤ |x - center| + |center - y| := abs_add_le _ _
    _ = |x - center| + |y - center| := by rw [abs_sub_comm center y]
    _ ≤ epsilon / 2 + epsilon / 2 := add_le_add hx hy
    _ = epsilon := by ring

/--
Padded-cardinality cover from a scalar quantizer plus a decoder-error bound.
This is the grid-friendly form: once every sampled value is within
`epsilon / 2` of its decoded grid representative, equal quantizer codes give
the pointwise `epsilon`-closeness needed for an empirical `L1(P_n)` cover.
-/
theorem nonempty_finiteEmpiricalL1CoverAtCard_of_coordinate_scalarQuantizer_decode_error_card_le
    {Observation : Type u} {Index : Type v} {CoordCode : Type*}
    [DecidableEq CoordCode] {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality : ℕ}
    (quantizer : Fin n -> ℝ -> CoordCode)
    (decode : Fin n -> CoordCode -> ℝ)
    (codeSets : Fin n -> Finset CoordCode)
    (hquantizer_mem :
      ∀ index, index ∈ indexClass ->
        ∀ sampleIndex : Fin n,
          quantizer sampleIndex (classFun index (sample sampleIndex)) ∈
            codeSets sampleIndex)
    (hdecode_close :
      ∀ index, index ∈ indexClass ->
        ∀ sampleIndex : Fin n,
          |classFun index (sample sampleIndex) -
            decode sampleIndex
              (quantizer sampleIndex
                (classFun index (sample sampleIndex)))| ≤ epsilon / 2)
    (hepsilon_nonneg : 0 ≤ epsilon)
    (hindexClass : ∃ index, index ∈ indexClass)
    (hcard_le :
      (∏ sampleIndex : Fin n, (codeSets sampleIndex).card) ≤ cardinality) :
    Nonempty
      (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
        cardinality) := by
  exact
    nonempty_finiteEmpiricalL1CoverAtCard_of_coordinate_scalarQuantizer_card_le
      quantizer codeSets hquantizer_mem hepsilon_nonneg
      (fun sampleIndex index hindex center hcenter hcode =>
        by
          have hcenter_close :
              |classFun center (sample sampleIndex) -
                decode sampleIndex
                  (quantizer sampleIndex
                    (classFun index (sample sampleIndex)))| ≤ epsilon / 2 := by
            simpa [hcode] using hdecode_close center hcenter sampleIndex
          exact
            abs_sub_le_of_abs_sub_decode_le_half
              (hdecode_close index hindex sampleIndex) hcenter_close)
      hindexClass hcard_le

/--
Numeric empirical-covering-number bound from a scalar quantizer plus a
decoder-error bound.
-/
theorem empiricalL1CoveringNumber_le_of_coordinate_scalarQuantizer_decode_error_card_le
    {Observation : Type u} {Index : Type v} {CoordCode : Type*}
    [DecidableEq CoordCode] {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality : ℕ}
    (quantizer : Fin n -> ℝ -> CoordCode)
    (decode : Fin n -> CoordCode -> ℝ)
    (codeSets : Fin n -> Finset CoordCode)
    (hquantizer_mem :
      ∀ index, index ∈ indexClass ->
        ∀ sampleIndex : Fin n,
          quantizer sampleIndex (classFun index (sample sampleIndex)) ∈
            codeSets sampleIndex)
    (hdecode_close :
      ∀ index, index ∈ indexClass ->
        ∀ sampleIndex : Fin n,
          |classFun index (sample sampleIndex) -
            decode sampleIndex
              (quantizer sampleIndex
                (classFun index (sample sampleIndex)))| ≤ epsilon / 2)
    (hepsilon_nonneg : 0 ≤ epsilon)
    (hcard_le :
      (∏ sampleIndex : Fin n, (codeSets sampleIndex).card) ≤ cardinality) :
    empiricalL1CoveringNumber sample indexClass classFun epsilon ≤
      (cardinality : ℕ∞) := by
  exact
    empiricalL1CoveringNumber_le_of_coordinate_scalarQuantizer_card_le
      quantizer codeSets hquantizer_mem hepsilon_nonneg
      (fun sampleIndex index hindex center hcenter hcode =>
        by
          have hcenter_close :
              |classFun center (sample sampleIndex) -
                decode sampleIndex
                  (quantizer sampleIndex
                    (classFun index (sample sampleIndex)))| ≤ epsilon / 2 := by
            simpa [hcode] using hdecode_close center hcenter sampleIndex
          exact
            abs_sub_le_of_abs_sub_decode_le_half
              (hdecode_close index hindex sampleIndex) hcenter_close)
      hcard_le

/--
Rounding to the nearest multiple of a positive grid step has decoding error at
most half the step.
-/
theorem abs_sub_mul_round_div_le_half
    {x step : ℝ} (hstep_pos : 0 < step) :
    |x - step * (round (x / step) : ℝ)| ≤ step / 2 := by
  have hstep_ne : step ≠ 0 := ne_of_gt hstep_pos
  calc
    |x - step * (round (x / step) : ℝ)|
        = |step * (x / step - (round (x / step) : ℝ))| := by
          field_simp [hstep_ne]
    _ = step * |x / step - (round (x / step) : ℝ)| := by
      rw [abs_mul, abs_of_pos hstep_pos]
    _ ≤ step * (1 / 2) :=
      mul_le_mul_of_nonneg_left (abs_sub_round (x / step))
        hstep_pos.le
    _ = step / 2 := by ring

/--
If the upper half-step endpoint of a real point is below an integer bound,
then its nearest-integer rounding is below that bound.
-/
theorem round_le_int_of_add_half_le
    {z : ℝ} {bound : ℤ}
    (h : z + 1 / 2 ≤ (bound : ℝ)) :
    round z ≤ bound := by
  have hround : (round z : ℝ) ≤ z + 1 / 2 :=
    round_le_add_half z
  exact_mod_cast hround.trans h

/--
If an integer lower bound is below the lower half-step endpoint of a real
point, then it is below the nearest-integer rounding.
-/
theorem int_neg_le_round_of_le_sub_half
    {z : ℝ} {bound : ℤ}
    (h : ((-bound : ℤ) : ℝ) ≤ z - 1 / 2) :
    -bound ≤ round z := by
  have hround : z - 1 / 2 < (round z : ℝ) :=
    sub_half_lt_round z
  have hlt : ((-bound : ℤ) : ℝ) < (round z : ℝ) :=
    lt_of_le_of_lt h hround
  exact_mod_cast le_of_lt hlt

/--
A bounded real value has nearest-integer `epsilon`-grid code in the symmetric
integer interval determined by any supplied bound above `M / epsilon + 1/2`.
-/
theorem round_div_mem_intInterval_of_abs_le
    {x epsilon M : ℝ} {bound : ℤ}
    (hepsilon_pos : 0 < epsilon)
    (habs : |x| ≤ M)
    (hbound : M / epsilon + 1 / 2 ≤ (bound : ℝ)) :
    -bound ≤ round (x / epsilon) ∧
      round (x / epsilon) ≤ bound := by
  have hdiv_abs : |x / epsilon| ≤ M / epsilon := by
    rw [abs_div, abs_of_pos hepsilon_pos]
    exact div_le_div_of_nonneg_right habs hepsilon_pos.le
  have hdiv := abs_le.mp hdiv_abs
  constructor
  · apply int_neg_le_round_of_le_sub_half
    have hcast : ((-bound : ℤ) : ℝ) = -(bound : ℝ) := by norm_num
    rw [hcast]
    linarith
  · apply round_le_int_of_add_half_le
    linarith

/-- Cardinality of the symmetric integer interval used by the rounding code. -/
theorem card_int_symmetric_Icc (bound : ℤ) :
    (Finset.Icc (-bound) bound).card = (2 * bound + 1).toNat := by
  rw [Int.card_Icc]
  ring_nf

/--
Padded-cardinality empirical cover from coordinatewise nearest-integer
rounding at grid step `epsilon`.  The finite code-set membership and product
cardinality bound are kept explicit; the rounding decoding error is proved
from mathlib's `Int.abs_sub_round`.
-/
theorem nonempty_finiteEmpiricalL1CoverAtCard_of_coordinate_roundingQuantizer_card_le
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality : ℕ}
    (codeSets : Fin n -> Finset ℤ)
    (hepsilon_pos : 0 < epsilon)
    (hround_mem :
      ∀ index, index ∈ indexClass ->
        ∀ sampleIndex : Fin n,
          round (classFun index (sample sampleIndex) / epsilon) ∈
            codeSets sampleIndex)
    (hindexClass : ∃ index, index ∈ indexClass)
    (hcard_le :
      (∏ sampleIndex : Fin n, (codeSets sampleIndex).card) ≤ cardinality) :
    Nonempty
      (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
        cardinality) := by
  exact
    nonempty_finiteEmpiricalL1CoverAtCard_of_coordinate_scalarQuantizer_decode_error_card_le
      (fun _sampleIndex x => round (x / epsilon))
      (fun _sampleIndex code => epsilon * (code : ℝ))
      codeSets hround_mem
      (fun index hindex sampleIndex =>
        abs_sub_mul_round_div_le_half
          (x := classFun index (sample sampleIndex))
          (step := epsilon) hepsilon_pos)
      hepsilon_pos.le
      hindexClass hcard_le

/--
Numeric empirical-covering-number bound from coordinatewise nearest-integer
rounding at grid step `epsilon`.
-/
theorem empiricalL1CoveringNumber_le_of_coordinate_roundingQuantizer_card_le
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality : ℕ}
    (codeSets : Fin n -> Finset ℤ)
    (hepsilon_pos : 0 < epsilon)
    (hround_mem :
      ∀ index, index ∈ indexClass ->
        ∀ sampleIndex : Fin n,
          round (classFun index (sample sampleIndex) / epsilon) ∈
            codeSets sampleIndex)
    (hcard_le :
      (∏ sampleIndex : Fin n, (codeSets sampleIndex).card) ≤ cardinality) :
    empiricalL1CoveringNumber sample indexClass classFun epsilon ≤
      (cardinality : ℕ∞) := by
  exact
    empiricalL1CoveringNumber_le_of_coordinate_scalarQuantizer_decode_error_card_le
      (fun _sampleIndex x => round (x / epsilon))
      (fun _sampleIndex code => epsilon * (code : ℝ))
      codeSets hround_mem
      (fun index hindex sampleIndex =>
        abs_sub_mul_round_div_le_half
          (x := classFun index (sample sampleIndex))
          (step := epsilon) hepsilon_pos)
      hepsilon_pos.le
      hcard_le

/--
Padded-cardinality empirical cover from nearest-integer rounding when the
rounded coordinate codes are known to lie in finite symmetric integer
intervals.
-/
theorem nonempty_finiteEmpiricalL1CoverAtCard_of_coordinate_roundingQuantizer_interval_card_le
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality : ℕ}
    (bound : Fin n -> ℤ)
    (hepsilon_pos : 0 < epsilon)
    (hround_lower :
      ∀ index, index ∈ indexClass ->
        ∀ sampleIndex : Fin n,
          -bound sampleIndex ≤
            round (classFun index (sample sampleIndex) / epsilon))
    (hround_upper :
      ∀ index, index ∈ indexClass ->
        ∀ sampleIndex : Fin n,
          round (classFun index (sample sampleIndex) / epsilon) ≤
            bound sampleIndex)
    (hindexClass : ∃ index, index ∈ indexClass)
    (hcard_le :
      (∏ sampleIndex : Fin n,
          (Finset.Icc (-bound sampleIndex) (bound sampleIndex)).card) ≤
        cardinality) :
    Nonempty
      (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
        cardinality) := by
  exact
    nonempty_finiteEmpiricalL1CoverAtCard_of_coordinate_roundingQuantizer_card_le
      (fun sampleIndex => Finset.Icc (-bound sampleIndex) (bound sampleIndex))
      hepsilon_pos
      (fun index hindex sampleIndex =>
        Finset.mem_Icc.mpr
          ⟨hround_lower index hindex sampleIndex,
            hround_upper index hindex sampleIndex⟩)
      hindexClass hcard_le

/--
Numeric empirical-covering-number bound from nearest-integer rounding and
finite symmetric integer intervals for the coordinate codes.
-/
theorem empiricalL1CoveringNumber_le_of_coordinate_roundingQuantizer_interval_card_le
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality : ℕ}
    (bound : Fin n -> ℤ)
    (hepsilon_pos : 0 < epsilon)
    (hround_lower :
      ∀ index, index ∈ indexClass ->
        ∀ sampleIndex : Fin n,
          -bound sampleIndex ≤
            round (classFun index (sample sampleIndex) / epsilon))
    (hround_upper :
      ∀ index, index ∈ indexClass ->
        ∀ sampleIndex : Fin n,
          round (classFun index (sample sampleIndex) / epsilon) ≤
            bound sampleIndex)
    (hcard_le :
      (∏ sampleIndex : Fin n,
          (Finset.Icc (-bound sampleIndex) (bound sampleIndex)).card) ≤
        cardinality) :
    empiricalL1CoveringNumber sample indexClass classFun epsilon ≤
      (cardinality : ℕ∞) := by
  exact
    empiricalL1CoveringNumber_le_of_coordinate_roundingQuantizer_card_le
      (fun sampleIndex => Finset.Icc (-bound sampleIndex) (bound sampleIndex))
      hepsilon_pos
      (fun index hindex sampleIndex =>
        Finset.mem_Icc.mpr
          ⟨hround_lower index hindex sampleIndex,
            hround_upper index hindex sampleIndex⟩)
      hcard_le

/--
Padded-cardinality empirical cover from nearest-integer rounding when bounded
sample coordinates imply membership in supplied finite symmetric integer
intervals.
-/
theorem nonempty_finiteEmpiricalL1CoverAtCard_of_coordinate_roundingQuantizer_abs_bound_interval_card_le
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality : ℕ}
    (bound : Fin n -> ℤ) (M : Fin n -> ℝ)
    (hepsilon_pos : 0 < epsilon)
    (habs :
      ∀ index, index ∈ indexClass ->
        ∀ sampleIndex : Fin n,
          |classFun index (sample sampleIndex)| ≤ M sampleIndex)
    (hbound :
      ∀ sampleIndex : Fin n,
        M sampleIndex / epsilon + 1 / 2 ≤ (bound sampleIndex : ℝ))
    (hindexClass : ∃ index, index ∈ indexClass)
    (hcard_le :
      (∏ sampleIndex : Fin n,
          (Finset.Icc (-bound sampleIndex) (bound sampleIndex)).card) ≤
        cardinality) :
    Nonempty
      (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
        cardinality) := by
  exact
    nonempty_finiteEmpiricalL1CoverAtCard_of_coordinate_roundingQuantizer_interval_card_le
      bound hepsilon_pos
      (fun index hindex sampleIndex =>
        (round_div_mem_intInterval_of_abs_le
          (x := classFun index (sample sampleIndex))
          (epsilon := epsilon) (M := M sampleIndex)
          (bound := bound sampleIndex) hepsilon_pos
          (habs index hindex sampleIndex) (hbound sampleIndex)).1)
      (fun index hindex sampleIndex =>
        (round_div_mem_intInterval_of_abs_le
          (x := classFun index (sample sampleIndex))
          (epsilon := epsilon) (M := M sampleIndex)
          (bound := bound sampleIndex) hepsilon_pos
          (habs index hindex sampleIndex) (hbound sampleIndex)).2)
      hindexClass hcard_le

/--
Numeric empirical-covering-number bound from nearest-integer rounding when
bounded sample coordinates imply membership in supplied finite symmetric
integer intervals.
-/
theorem empiricalL1CoveringNumber_le_of_coordinate_roundingQuantizer_abs_bound_interval_card_le
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality : ℕ}
    (bound : Fin n -> ℤ) (M : Fin n -> ℝ)
    (hepsilon_pos : 0 < epsilon)
    (habs :
      ∀ index, index ∈ indexClass ->
        ∀ sampleIndex : Fin n,
          |classFun index (sample sampleIndex)| ≤ M sampleIndex)
    (hbound :
      ∀ sampleIndex : Fin n,
        M sampleIndex / epsilon + 1 / 2 ≤ (bound sampleIndex : ℝ))
    (hcard_le :
      (∏ sampleIndex : Fin n,
          (Finset.Icc (-bound sampleIndex) (bound sampleIndex)).card) ≤
        cardinality) :
    empiricalL1CoveringNumber sample indexClass classFun epsilon ≤
      (cardinality : ℕ∞) := by
  exact
    empiricalL1CoveringNumber_le_of_coordinate_roundingQuantizer_interval_card_le
      bound hepsilon_pos
      (fun index hindex sampleIndex =>
        (round_div_mem_intInterval_of_abs_le
          (x := classFun index (sample sampleIndex))
          (epsilon := epsilon) (M := M sampleIndex)
          (bound := bound sampleIndex) hepsilon_pos
          (habs index hindex sampleIndex) (hbound sampleIndex)).1)
      (fun index hindex sampleIndex =>
        (round_div_mem_intInterval_of_abs_le
          (x := classFun index (sample sampleIndex))
          (epsilon := epsilon) (M := M sampleIndex)
          (bound := bound sampleIndex) hepsilon_pos
          (habs index hindex sampleIndex) (hbound sampleIndex)).2)
      hcard_le

/--
Padded-cardinality empirical cover from bounded nearest-integer rounding, with
the symmetric integer-interval cardinalities normalized to `(2 * B + 1).toNat`.
-/
theorem nonempty_finiteEmpiricalL1CoverAtCard_of_coordinate_roundingQuantizer_abs_bound_symmetric_card_le
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality : ℕ}
    (bound : Fin n -> ℤ) (M : Fin n -> ℝ)
    (hepsilon_pos : 0 < epsilon)
    (habs :
      ∀ index, index ∈ indexClass ->
        ∀ sampleIndex : Fin n,
          |classFun index (sample sampleIndex)| ≤ M sampleIndex)
    (hbound :
      ∀ sampleIndex : Fin n,
        M sampleIndex / epsilon + 1 / 2 ≤ (bound sampleIndex : ℝ))
    (hindexClass : ∃ index, index ∈ indexClass)
    (hcard_le :
      (∏ sampleIndex : Fin n, (2 * bound sampleIndex + 1).toNat) ≤
        cardinality) :
    Nonempty
      (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
        cardinality) := by
  refine
    nonempty_finiteEmpiricalL1CoverAtCard_of_coordinate_roundingQuantizer_abs_bound_interval_card_le
      bound M hepsilon_pos habs hbound hindexClass ?_
  simpa [card_int_symmetric_Icc, two_mul, add_assoc, add_left_comm, add_comm]
    using hcard_le

/--
Numeric empirical-covering-number bound from bounded nearest-integer rounding,
with symmetric integer-interval cardinalities normalized to
`(2 * B + 1).toNat`.
-/
theorem empiricalL1CoveringNumber_le_of_coordinate_roundingQuantizer_abs_bound_symmetric_card_le
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality : ℕ}
    (bound : Fin n -> ℤ) (M : Fin n -> ℝ)
    (hepsilon_pos : 0 < epsilon)
    (habs :
      ∀ index, index ∈ indexClass ->
        ∀ sampleIndex : Fin n,
          |classFun index (sample sampleIndex)| ≤ M sampleIndex)
    (hbound :
      ∀ sampleIndex : Fin n,
        M sampleIndex / epsilon + 1 / 2 ≤ (bound sampleIndex : ℝ))
    (hcard_le :
      (∏ sampleIndex : Fin n, (2 * bound sampleIndex + 1).toNat) ≤
        cardinality) :
    empiricalL1CoveringNumber sample indexClass classFun epsilon ≤
      (cardinality : ℕ∞) := by
  refine
    empiricalL1CoveringNumber_le_of_coordinate_roundingQuantizer_abs_bound_interval_card_le
      bound M hepsilon_pos habs hbound ?_
  simpa [card_int_symmetric_Icc, two_mul, add_assoc, add_left_comm, add_comm]
    using hcard_le

/--
Padded-cardinality empirical cover from nearest-integer rounding under a
single uniform absolute bound on all sampled truncated values.  The terminal
cardinality is the usual grid count `(2 * B + 1)^n`.
-/
theorem nonempty_finiteEmpiricalL1CoverAtCard_of_roundingQuantizer_uniform_abs_bound_card_le
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon M : ℝ}
    {cardinality : ℕ}
    (bound : ℤ)
    (hepsilon_pos : 0 < epsilon)
    (habs :
      ∀ index, index ∈ indexClass ->
        ∀ sampleIndex : Fin n,
          |classFun index (sample sampleIndex)| ≤ M)
    (hbound : M / epsilon + 1 / 2 ≤ (bound : ℝ))
    (hindexClass : ∃ index, index ∈ indexClass)
    (hcard_le : ((2 * bound + 1).toNat) ^ n ≤ cardinality) :
    Nonempty
      (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
        cardinality) := by
  refine
    nonempty_finiteEmpiricalL1CoverAtCard_of_coordinate_roundingQuantizer_abs_bound_symmetric_card_le
      (fun _ => bound) (fun _ => M) hepsilon_pos ?_ ?_ hindexClass ?_
  · intro index hindex sampleIndex
    exact habs index hindex sampleIndex
  · intro sampleIndex
    exact hbound
  · simpa using hcard_le

/--
Numeric empirical-covering-number bound from nearest-integer rounding under a
single uniform absolute bound on all sampled truncated values.
-/
theorem empiricalL1CoveringNumber_le_of_roundingQuantizer_uniform_abs_bound_card_le
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon M : ℝ}
    {cardinality : ℕ}
    (bound : ℤ)
    (hepsilon_pos : 0 < epsilon)
    (habs :
      ∀ index, index ∈ indexClass ->
        ∀ sampleIndex : Fin n,
          |classFun index (sample sampleIndex)| ≤ M)
    (hbound : M / epsilon + 1 / 2 ≤ (bound : ℝ))
    (hcard_le : ((2 * bound + 1).toNat) ^ n ≤ cardinality) :
    empiricalL1CoveringNumber sample indexClass classFun epsilon ≤
      (cardinality : ℕ∞) := by
  refine
    empiricalL1CoveringNumber_le_of_coordinate_roundingQuantizer_abs_bound_symmetric_card_le
      (fun _ => bound) (fun _ => M) hepsilon_pos ?_ ?_ ?_
  · intro index hindex sampleIndex
    exact habs index hindex sampleIndex
  · intro sampleIndex
    exact hbound
  · simpa using hcard_le

/--
Padded-cardinality cover from a finite fixed-sample trace image.  Later
combinatorial arguments can supply a terminal bound on the number of distinct
traces and reuse this cover witness directly.
-/
theorem nonempty_finiteEmpiricalL1CoverAtCard_of_finite_trace_image_card_le
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality : ℕ}
    (htrace_finite :
      (empiricalTrace sample classFun '' indexClass).Finite)
    (hepsilon_nonneg : 0 ≤ epsilon)
    (hindexClass : ∃ index, index ∈ indexClass)
    (hcard_le : htrace_finite.toFinset.card ≤ cardinality) :
    Nonempty
      (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
        cardinality) := by
  exact
    (nonempty_finiteEmpiricalL1CoverAtCard_of_finite_trace_image
      htrace_finite hepsilon_nonneg).elim fun cover =>
      ⟨cover.pad_cardinality hindexClass hcard_le⟩

/--
Padded numeric empirical-covering-number bound from a finite fixed-sample trace
image and a terminal cardinality estimate.
-/
theorem empiricalL1CoveringNumber_le_of_finite_trace_image_card_le
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality : ℕ}
    (htrace_finite :
      (empiricalTrace sample classFun '' indexClass).Finite)
    (hepsilon_nonneg : 0 ≤ epsilon)
    (hcard_le : htrace_finite.toFinset.card ≤ cardinality) :
    empiricalL1CoveringNumber sample indexClass classFun epsilon ≤
      (cardinality : ℕ∞) := by
  exact
    (empiricalL1CoveringNumber_le_of_finite_trace_image
      htrace_finite hepsilon_nonneg).trans (by exact_mod_cast hcard_le)

/--
Convert a mathlib internal metric cover into a local empirical `L1(P_n)` cover
through a supplied compatibility bound.

The metric cover supplies centers in `centerSet`; the `hdist` hypothesis is the
problem-specific bridge from the index semimetric to empirical `L1(P_n)`.
-/
theorem nonempty_finiteEmpiricalL1CoverAtCard_of_metric_isCover
    {Observation : Type u} {Index : Type v} [PseudoEMetricSpace Index] {n : ℕ}
    {sample : SampleAt Observation n} {indexClass centerSet : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ} {radius : ℝ≥0}
    (hcenter_finite : centerSet.Finite)
    (hcenter_subset : centerSet ⊆ indexClass)
    (hmetric_cover : Metric.IsCover radius indexClass centerSet)
    (hdist :
      ∀ index center, index ∈ indexClass -> center ∈ centerSet ->
        edist index center ≤ radius ->
          empiricalL1Distance sample (classFun index) (classFun center) ≤
            epsilon) :
    Nonempty
      (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
        hcenter_finite.toFinset.card) := by
  refine
    nonempty_finiteEmpiricalL1CoverAtCard_of_finite_centerSet
      hcenter_finite hcenter_subset ?_
  intro index hindex
  obtain ⟨center, hcenter, hdist_metric⟩ := hmetric_cover hindex
  exact ⟨center, hcenter, hdist index center hindex hcenter hdist_metric⟩

/--
Numeric empirical-covering bound induced by a mathlib internal metric cover and
a compatibility estimate with empirical `L1(P_n)`.
-/
theorem empiricalL1CoveringNumber_le_of_metric_isCover
    {Observation : Type u} {Index : Type v} [PseudoEMetricSpace Index] {n : ℕ}
    {sample : SampleAt Observation n} {indexClass centerSet : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ} {radius : ℝ≥0}
    (hcenter_finite : centerSet.Finite)
    (hcenter_subset : centerSet ⊆ indexClass)
    (hmetric_cover : Metric.IsCover radius indexClass centerSet)
    (hdist :
      ∀ index center, index ∈ indexClass -> center ∈ centerSet ->
        edist index center ≤ radius ->
          empiricalL1Distance sample (classFun index) (classFun center) ≤
            epsilon) :
    empiricalL1CoveringNumber sample indexClass classFun epsilon ≤
      (hcenter_finite.toFinset.card : ℕ∞) := by
  exact
    empiricalL1CoveringNumber_le_of_coverAtCard
      (nonempty_finiteEmpiricalL1CoverAtCard_of_metric_isCover
        hcenter_finite hcenter_subset hmetric_cover hdist)

/--
Use mathlib's finite minimal internal cover as a local empirical-net witness.
-/
theorem nonempty_finiteEmpiricalL1CoverAtCard_of_metric_minimalCover
    {Observation : Type u} {Index : Type v} [PseudoEMetricSpace Index] {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ} {radius : ℝ≥0}
    (hcovering_finite : Metric.coveringNumber radius indexClass ≠ ⊤)
    (hdist :
      ∀ index center, index ∈ indexClass ->
        center ∈ Metric.minimalCover radius indexClass ->
          edist index center ≤ radius ->
            empiricalL1Distance sample (classFun index) (classFun center) ≤
              epsilon) :
    Nonempty
      (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
        (Metric.finite_minimalCover (ε := radius)
          (A := indexClass)).toFinset.card) := by
  exact
    nonempty_finiteEmpiricalL1CoverAtCard_of_metric_isCover
      (Metric.finite_minimalCover (ε := radius) (A := indexClass))
      (Metric.minimalCover_subset (ε := radius) (A := indexClass))
      (Metric.isCover_minimalCover (ε := radius) (A := indexClass)
        hcovering_finite)
      hdist

/--
Numeric empirical-covering bound induced by mathlib's finite minimal internal
metric cover and a compatibility estimate with empirical `L1(P_n)`.
-/
theorem empiricalL1CoveringNumber_le_of_metric_minimalCover
    {Observation : Type u} {Index : Type v} [PseudoEMetricSpace Index] {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ} {radius : ℝ≥0}
    (hcovering_finite : Metric.coveringNumber radius indexClass ≠ ⊤)
    (hdist :
      ∀ index center, index ∈ indexClass ->
        center ∈ Metric.minimalCover radius indexClass ->
          edist index center ≤ radius ->
            empiricalL1Distance sample (classFun index) (classFun center) ≤
              epsilon) :
    empiricalL1CoveringNumber sample indexClass classFun epsilon ≤
      ((Metric.finite_minimalCover (ε := radius)
        (A := indexClass)).toFinset.card : ℕ∞) := by
  exact
    empiricalL1CoveringNumber_le_of_coverAtCard
      (nonempty_finiteEmpiricalL1CoverAtCard_of_metric_minimalCover
        hcovering_finite hdist)

/--
Convert a mathlib internal cover in the empirical `L1(P_n)` wrapper into a
local finite empirical `L1(P_n)` cover over the original class.

The output cardinality is the finite image of the wrapper centers under
`toIndex`; duplicate centers are collapsed, which is harmless for the local
finite-net witness.
-/
theorem nonempty_finiteEmpiricalL1CoverAtCard_of_empiricalL1Index_isCover
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {radius : ℝ≥0}
    {centerSet :
      Set (EmpiricalL1Index Observation Index n sample classFun)}
    (hcenter_finite : centerSet.Finite)
    (hcenter_subset :
      centerSet ⊆
        EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
          indexClass)
    (hmetric_cover :
      Metric.IsCover radius
        (EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
          indexClass)
        centerSet) :
    Nonempty
      (FiniteEmpiricalL1CoverAtCard sample indexClass classFun (radius : ℝ)
        ((hcenter_finite.image EmpiricalL1Index.toIndex).toFinset.card)) := by
  let rawCenterSet : Set Index := EmpiricalL1Index.toIndex '' centerSet
  have hraw_finite : rawCenterSet.Finite :=
    hcenter_finite.image EmpiricalL1Index.toIndex
  refine
    nonempty_finiteEmpiricalL1CoverAtCard_of_finite_centerSet
      (sample := sample) (indexClass := indexClass) (classFun := classFun)
      (epsilon := (radius : ℝ)) hraw_finite ?_ ?_
  · intro center hcenter
    rcases hcenter with ⟨wrappedCenter, hwrappedCenter, rfl⟩
    exact hcenter_subset hwrappedCenter
  · intro index hindex
    have hlifted :
        EmpiricalL1Index.ofIndex (sample := sample) (classFun := classFun)
          index ∈
          EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
            indexClass := by
      simpa [EmpiricalL1Index.liftSet] using hindex
    obtain ⟨wrappedCenter, hwrappedCenter, hdist⟩ :=
      hmetric_cover hlifted
    refine ⟨wrappedCenter.toIndex, ⟨wrappedCenter, hwrappedCenter, rfl⟩, ?_⟩
    exact
      EmpiricalL1Index.empiricalL1Distance_le_coe_radius_of_edist_le
        (sample := sample) (classFun := classFun) hdist

/--
The empirical wrapper's minimal internal cover gives a local finite empirical
`L1(P_n)` net over the original class.
-/
theorem nonempty_finiteEmpiricalL1CoverAtCard_of_empiricalL1Index_minimalCover
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {radius : ℝ≥0}
    (hcovering_finite :
      Metric.coveringNumber radius
        (EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
          indexClass) ≠ ⊤) :
    Nonempty
      (FiniteEmpiricalL1CoverAtCard sample indexClass classFun (radius : ℝ)
        (((Metric.finite_minimalCover (ε := radius)
          (A :=
            EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
              indexClass)).image EmpiricalL1Index.toIndex).toFinset.card)) := by
  exact
    nonempty_finiteEmpiricalL1CoverAtCard_of_empiricalL1Index_isCover
      (sample := sample) (indexClass := indexClass) (classFun := classFun)
      (radius := radius)
      (Metric.finite_minimalCover (ε := radius)
        (A :=
          EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
            indexClass))
      (Metric.minimalCover_subset (ε := radius)
        (A :=
          EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
            indexClass))
      (Metric.isCover_minimalCover (ε := radius)
        (A :=
          EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
            indexClass) hcovering_finite)

/--
Numeric empirical-covering bound induced by an internal cover in the empirical
`L1(P_n)` wrapper.
-/
theorem empiricalL1CoveringNumber_le_of_empiricalL1Index_isCover
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {radius : ℝ≥0}
    {centerSet :
      Set (EmpiricalL1Index Observation Index n sample classFun)}
    (hcenter_finite : centerSet.Finite)
    (hcenter_subset :
      centerSet ⊆
        EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
          indexClass)
    (hmetric_cover :
      Metric.IsCover radius
        (EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
          indexClass)
        centerSet) :
    empiricalL1CoveringNumber sample indexClass classFun (radius : ℝ) ≤
      (((hcenter_finite.image EmpiricalL1Index.toIndex).toFinset.card) : ℕ∞) := by
  exact
    empiricalL1CoveringNumber_le_of_coverAtCard
      (nonempty_finiteEmpiricalL1CoverAtCard_of_empiricalL1Index_isCover
        (sample := sample) (indexClass := indexClass) (classFun := classFun)
        hcenter_finite hcenter_subset hmetric_cover)

/--
Collapsing duplicate empirical-wrapper centers by `toIndex` cannot increase
finite cardinality.
-/
theorem empiricalL1Index_image_toFinset_card_le
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n}
    {classFun : Index -> Observation -> ℝ}
    {centerSet :
      Set (EmpiricalL1Index Observation Index n sample classFun)}
    (hcenter_finite : centerSet.Finite) :
    (hcenter_finite.image EmpiricalL1Index.toIndex).toFinset.card ≤
      hcenter_finite.toFinset.card := by
  classical
  have hle :
      (EmpiricalL1Index.toIndex '' centerSet).ncard ≤ centerSet.ncard :=
    Set.ncard_image_le (f := EmpiricalL1Index.toIndex)
      (s := centerSet) hcenter_finite
  simpa [Set.ncard_eq_toFinset_card
      (EmpiricalL1Index.toIndex '' centerSet)
      (hcenter_finite.image EmpiricalL1Index.toIndex),
    Set.ncard_eq_toFinset_card centerSet hcenter_finite] using hle

/--
Numeric empirical-covering bound induced by an internal cover in the empirical
`L1(P_n)` wrapper, bounded by the original wrapper center count.
-/
theorem empiricalL1CoveringNumber_le_of_empiricalL1Index_isCover_card
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {radius : ℝ≥0}
    {centerSet :
      Set (EmpiricalL1Index Observation Index n sample classFun)}
    (hcenter_finite : centerSet.Finite)
    (hcenter_subset :
      centerSet ⊆
        EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
          indexClass)
    (hmetric_cover :
      Metric.IsCover radius
        (EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
          indexClass)
        centerSet) :
    empiricalL1CoveringNumber sample indexClass classFun (radius : ℝ) ≤
      (hcenter_finite.toFinset.card : ℕ∞) := by
  exact
    (empiricalL1CoveringNumber_le_of_empiricalL1Index_isCover
      (sample := sample) (indexClass := indexClass) (classFun := classFun)
      hcenter_finite hcenter_subset hmetric_cover).trans
      (by
        exact_mod_cast
          empiricalL1Index_image_toFinset_card_le
            (sample := sample) (classFun := classFun) hcenter_finite)

/--
Numeric empirical-covering bound induced by the empirical wrapper's minimal
internal cover.
-/
theorem empiricalL1CoveringNumber_le_of_empiricalL1Index_minimalCover
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {radius : ℝ≥0}
    (hcovering_finite :
      Metric.coveringNumber radius
        (EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
          indexClass) ≠ ⊤) :
    empiricalL1CoveringNumber sample indexClass classFun (radius : ℝ) ≤
      ((((Metric.finite_minimalCover (ε := radius)
        (A :=
          EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
            indexClass)).image EmpiricalL1Index.toIndex).toFinset.card) : ℕ∞) := by
  exact
    empiricalL1CoveringNumber_le_of_coverAtCard
      (nonempty_finiteEmpiricalL1CoverAtCard_of_empiricalL1Index_minimalCover
        (sample := sample) (indexClass := indexClass) (classFun := classFun)
        (radius := radius) hcovering_finite)

/--
Numeric empirical-covering bound induced by the empirical wrapper's minimal
internal cover, bounded by the minimal wrapper-cover cardinality.
-/
theorem empiricalL1CoveringNumber_le_of_empiricalL1Index_minimalCover_card
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {radius : ℝ≥0}
    (hcovering_finite :
      Metric.coveringNumber radius
        (EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
          indexClass) ≠ ⊤) :
    empiricalL1CoveringNumber sample indexClass classFun (radius : ℝ) ≤
      ((Metric.finite_minimalCover (ε := radius)
        (A :=
          EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
            indexClass)).toFinset.card : ℕ∞) := by
  exact
    empiricalL1CoveringNumber_le_of_empiricalL1Index_isCover_card
      (sample := sample) (indexClass := indexClass) (classFun := classFun)
      (radius := radius)
      (Metric.finite_minimalCover (ε := radius)
        (A :=
          EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
            indexClass))
      (Metric.minimalCover_subset (ε := radius)
        (A :=
          EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
            indexClass))
      (Metric.isCover_minimalCover (ε := radius)
        (A :=
          EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
            indexClass) hcovering_finite)

/--
The local empirical `L1(P_n)` covering number is bounded by mathlib's internal
covering number for the induced empirical pseudometric on the wrapped index
class.
-/
theorem empiricalL1CoveringNumber_le_empiricalL1Index_coveringNumber
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {radius : ℝ≥0}
    (hcovering_finite :
      Metric.coveringNumber radius
        (EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
          indexClass) ≠ ⊤) :
    empiricalL1CoveringNumber sample indexClass classFun (radius : ℝ) ≤
      Metric.coveringNumber radius
        (EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
          indexClass) := by
  have hbound :=
    empiricalL1CoveringNumber_le_of_empiricalL1Index_minimalCover_card
      (sample := sample) (indexClass := indexClass) (classFun := classFun)
      (radius := radius) hcovering_finite
  have hcard_eq :
      ((Metric.finite_minimalCover (ε := radius)
        (A :=
          EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
            indexClass)).toFinset.card : ℕ∞) =
        Metric.coveringNumber radius
          (EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
            indexClass) := by
    rw [← Set.Finite.encard_eq_coe_toFinset_card
      (Metric.finite_minimalCover (ε := radius)
        (A :=
          EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
            indexClass))]
    exact Metric.encard_minimalCover (ε := radius)
      (A :=
        EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
          indexClass) hcovering_finite
  simpa [hcard_eq] using hbound

/--
An explicit local empirical `L1(P_n)` cover also gives an internal mathlib
cover for the induced empirical pseudometric wrapper.

This is the reverse comparison to
`empiricalL1CoveringNumber_le_empiricalL1Index_coveringNumber`: it lets later
entropy arguments move from a proof-carrying VdV&W finite empirical net back
to `Metric.coveringNumber` on `EmpiricalL1Index.liftSet`.
-/
theorem empiricalL1Index_coveringNumber_le_of_finiteEmpiricalL1CoverAtCard
    {Observation : Type u} {Index : Type v} {n cardinality : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    (hepsilon_nonneg : 0 ≤ epsilon)
    (cover :
      FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
        cardinality) :
    Metric.coveringNumber (⟨epsilon, hepsilon_nonneg⟩ : ℝ≥0)
        (EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
          indexClass) ≤
      (cardinality : ℕ∞) := by
  let centerSet :
      Set (EmpiricalL1Index Observation Index n sample classFun) :=
    Set.range fun centerIndex : Fin cardinality =>
      EmpiricalL1Index.ofIndex (sample := sample) (classFun := classFun)
        (cover.center centerIndex)
  have hcenter_finite : centerSet.Finite :=
    Set.finite_range fun centerIndex : Fin cardinality =>
      EmpiricalL1Index.ofIndex (sample := sample) (classFun := classFun)
        (cover.center centerIndex)
  have hcenter_subset :
      centerSet ⊆
        EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
          indexClass := by
    intro center hcenter
    rcases hcenter with ⟨centerIndex, rfl⟩
    simpa [EmpiricalL1Index.liftSet] using cover.center_mem centerIndex
  have hmetric_cover :
      Metric.IsCover (⟨epsilon, hepsilon_nonneg⟩ : ℝ≥0)
        (EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
          indexClass) centerSet := by
    intro index hindex
    let centerIndex := cover.centerOf index.toIndex hindex
    refine
      ⟨EmpiricalL1Index.ofIndex (sample := sample) (classFun := classFun)
        (cover.center centerIndex), ⟨centerIndex, rfl⟩, ?_⟩
    have hdist :
        empiricalL1Distance sample (classFun index.toIndex)
          (classFun (cover.center centerIndex)) ≤ epsilon :=
      cover.dist_le index.toIndex hindex
    simpa [EmpiricalL1Index.edist_eq, centerIndex] using hdist
  have hcovering :
      Metric.coveringNumber (⟨epsilon, hepsilon_nonneg⟩ : ℝ≥0)
          (EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
            indexClass) ≤
        centerSet.encard :=
    Metric.IsCover.coveringNumber_le_encard hcenter_subset hmetric_cover
  have hcenter_encard :
      centerSet.encard ≤ (cardinality : ℕ∞) := by
    calc
      centerSet.encard ≤ (Set.univ : Set (Fin cardinality)).encard := by
        simpa [centerSet] using
          Set.encard_image_le
          (fun centerIndex : Fin cardinality =>
            EmpiricalL1Index.ofIndex (sample := sample) (classFun := classFun)
              (cover.center centerIndex))
          Set.univ
      _ = (cardinality : ℕ∞) := by simp
  exact hcovering.trans hcenter_encard

/--
If a finite local empirical cover exists, the internal mathlib covering number
for the induced empirical pseudometric is bounded by the local VdV&W empirical
covering number.
-/
theorem empiricalL1Index_coveringNumber_le_empiricalL1CoveringNumber
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    (hepsilon_nonneg : 0 ≤ epsilon)
    (hfinite :
      HasFiniteEmpiricalL1Cover sample indexClass classFun epsilon) :
    Metric.coveringNumber (⟨epsilon, hepsilon_nonneg⟩ : ℝ≥0)
        (EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
          indexClass) ≤
      empiricalL1CoveringNumber sample indexClass classFun epsilon := by
  rcases empiricalL1CoveringNumber_find_spec hfinite with ⟨cover⟩
  have hcovering :
      Metric.coveringNumber (⟨epsilon, hepsilon_nonneg⟩ : ℝ≥0)
          (EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
            indexClass) ≤
        (finiteEmpiricalL1CoveringNumberCard hfinite : ℕ∞) :=
    empiricalL1Index_coveringNumber_le_of_finiteEmpiricalL1CoverAtCard
      (sample := sample) (indexClass := indexClass) (classFun := classFun)
      hepsilon_nonneg cover
  simpa [empiricalL1CoveringNumber_eq_find hfinite] using hcovering

/--
For finite local empirical covers, the VdV&W empirical `L1(P_n)` covering
number agrees with mathlib's internal covering number on the induced empirical
pseudometric wrapper.
-/
theorem empiricalL1CoveringNumber_eq_empiricalL1Index_coveringNumber
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    (hepsilon_nonneg : 0 ≤ epsilon)
    (hfinite :
      HasFiniteEmpiricalL1Cover sample indexClass classFun epsilon) :
    empiricalL1CoveringNumber sample indexClass classFun epsilon =
      Metric.coveringNumber (⟨epsilon, hepsilon_nonneg⟩ : ℝ≥0)
        (EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
          indexClass) := by
  have hmetric_le :
      Metric.coveringNumber (⟨epsilon, hepsilon_nonneg⟩ : ℝ≥0)
          (EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
            indexClass) ≤
        empiricalL1CoveringNumber sample indexClass classFun epsilon :=
    empiricalL1Index_coveringNumber_le_empiricalL1CoveringNumber
      (sample := sample) (indexClass := indexClass) (classFun := classFun)
      hepsilon_nonneg hfinite
  have hmetric_lt :
      Metric.coveringNumber (⟨epsilon, hepsilon_nonneg⟩ : ℝ≥0)
          (EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
            indexClass) < ⊤ :=
    lt_of_le_of_lt hmetric_le
      (empiricalL1CoveringNumber_lt_top_of_hasFinite hfinite)
  have hlocal_le :
      empiricalL1CoveringNumber sample indexClass classFun epsilon ≤
        Metric.coveringNumber (⟨epsilon, hepsilon_nonneg⟩ : ℝ≥0)
          (EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
            indexClass) := by
    simpa using
      empiricalL1CoveringNumber_le_empiricalL1Index_coveringNumber
        (sample := sample) (indexClass := indexClass) (classFun := classFun)
        (radius := (⟨epsilon, hepsilon_nonneg⟩ : ℝ≥0))
        (ne_of_lt hmetric_lt)
  exact le_antisymm hlocal_le hmetric_le

/--
If the induced empirical internal covering number is bounded by a finite
cardinality, then the local empirical finite-cover witness can be padded to
that cardinality.
-/
theorem nonempty_finiteEmpiricalL1CoverAtCard_of_empiricalL1Index_coveringNumber_le
    {Observation : Type u} {Index : Type v} {n cardinality : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {radius : ℝ≥0}
    (hcovering_le :
      Metric.coveringNumber radius
        (EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
          indexClass) ≤ (cardinality : ℕ∞))
    (hindexClass : ∃ index, index ∈ indexClass) :
    Nonempty
      (FiniteEmpiricalL1CoverAtCard sample indexClass classFun (radius : ℝ)
        cardinality) := by
  have hcovering_finite :
      Metric.coveringNumber radius
        (EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
          indexClass) ≠ ⊤ :=
    ne_top_of_le_ne_top (by simp) hcovering_le
  rcases
    nonempty_finiteEmpiricalL1CoverAtCard_of_empiricalL1Index_minimalCover
      (sample := sample) (indexClass := indexClass) (classFun := classFun)
      (radius := radius) hcovering_finite with
  ⟨cover⟩
  have himage_le_minimal :
      (((Metric.finite_minimalCover (ε := radius)
        (A :=
          EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
            indexClass)).image EmpiricalL1Index.toIndex).toFinset.card) ≤
        (Metric.finite_minimalCover (ε := radius)
          (A :=
            EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
              indexClass)).toFinset.card :=
    empiricalL1Index_image_toFinset_card_le
      (sample := sample) (classFun := classFun)
      (Metric.finite_minimalCover (ε := radius)
        (A :=
          EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
            indexClass))
  have hminimal_card_eq :
      ((Metric.finite_minimalCover (ε := radius)
        (A :=
          EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
            indexClass)).toFinset.card : ℕ∞) =
        Metric.coveringNumber radius
          (EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
            indexClass) := by
    rw [← Set.Finite.encard_eq_coe_toFinset_card
      (Metric.finite_minimalCover (ε := radius)
        (A :=
          EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
            indexClass))]
    exact Metric.encard_minimalCover (ε := radius)
      (A :=
        EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
          indexClass) hcovering_finite
  have hcover_card_le :
      (((Metric.finite_minimalCover (ε := radius)
        (A :=
          EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
            indexClass)).image EmpiricalL1Index.toIndex).toFinset.card) ≤
        cardinality := by
    have himage_le_minimal_enat :
        ((((Metric.finite_minimalCover (ε := radius)
          (A :=
            EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
              indexClass)).image EmpiricalL1Index.toIndex).toFinset.card) :
            ℕ∞) ≤
          ((Metric.finite_minimalCover (ε := radius)
            (A :=
              EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
                indexClass)).toFinset.card : ℕ∞) := by
      exact_mod_cast himage_le_minimal
    have hle_enat :
        ((((Metric.finite_minimalCover (ε := radius)
          (A :=
            EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
              indexClass)).image EmpiricalL1Index.toIndex).toFinset.card) :
            ℕ∞) ≤ (cardinality : ℕ∞) := by
      exact himage_le_minimal_enat.trans
        (by simpa [hminimal_card_eq] using hcovering_le)
    exact_mod_cast hle_enat
  exact
    ⟨cover.pad_cardinality hindexClass hcover_card_le⟩

/--
Numeric local empirical-covering bound obtained from a finite bound on the
induced empirical internal covering number.
-/
theorem empiricalL1CoveringNumber_le_of_empiricalL1Index_coveringNumber_le
    {Observation : Type u} {Index : Type v} {n cardinality : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {radius : ℝ≥0}
    (hcovering_le :
      Metric.coveringNumber radius
        (EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
          indexClass) ≤ (cardinality : ℕ∞))
    (hindexClass : ∃ index, index ∈ indexClass) :
    empiricalL1CoveringNumber sample indexClass classFun (radius : ℝ) ≤
      (cardinality : ℕ∞) := by
  exact
    empiricalL1CoveringNumber_le_of_coverAtCard
      (nonempty_finiteEmpiricalL1CoverAtCard_of_empiricalL1Index_coveringNumber_le
        (sample := sample) (indexClass := indexClass) (classFun := classFun)
        (radius := radius) hcovering_le hindexClass)

/--
The induced empirical internal covering number is bounded by the cardinality of
the original index class.  This is the finite-class geometric input behind the
current Theorem 2.4.3 fixed-radius route.
-/
theorem empiricalL1Index_coveringNumber_le_indexClass_encard
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {radius : ℝ≥0} :
    Metric.coveringNumber radius
        (EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
          indexClass) ≤
      indexClass.encard := by
  calc
    Metric.coveringNumber radius
        (EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
          indexClass) ≤
      (EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
        indexClass).encard :=
        Metric.coveringNumber_le_encard_self
          (ε := radius)
          (A := EmpiricalL1Index.liftSet
            (sample := sample) (classFun := classFun) indexClass)
    _ = indexClass.encard := by
        simp

/--
Finite-class form of
`empiricalL1Index_coveringNumber_le_indexClass_encard`, with the bound written
as the finite `toFinset` cardinality used by local empirical-cover packages.
-/
theorem empiricalL1Index_coveringNumber_le_indexClass_toFinset_card
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {radius : ℝ≥0}
    (hindex_finite : indexClass.Finite) :
    Metric.coveringNumber radius
        (EmpiricalL1Index.liftSet (sample := sample) (classFun := classFun)
          indexClass) ≤
      (hindex_finite.toFinset.card : ℕ∞) := by
  simpa [hindex_finite.encard_eq_coe_toFinset_card] using
    empiricalL1Index_coveringNumber_le_indexClass_encard
      (sample := sample) (indexClass := indexClass)
      (classFun := classFun) (radius := radius)

/--
For finite nonempty classes, the local empirical `L1(P_n)` covering number is
bounded by the class cardinality at every fixed sample and radius.
-/
theorem empiricalL1CoveringNumber_le_indexClass_toFinset_card
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {radius : ℝ≥0}
    (hindex_finite : indexClass.Finite)
    (hindexClass : ∃ index, index ∈ indexClass) :
    empiricalL1CoveringNumber sample indexClass classFun (radius : ℝ) ≤
      (hindex_finite.toFinset.card : ℕ∞) := by
  exact
    empiricalL1CoveringNumber_le_of_empiricalL1Index_coveringNumber_le
      (sample := sample) (indexClass := indexClass)
      (classFun := classFun) (radius := radius)
      (empiricalL1Index_coveringNumber_le_indexClass_toFinset_card
        (sample := sample) (indexClass := indexClass)
        (classFun := classFun) (radius := radius) hindex_finite)
      hindexClass

/--
Fixed-cardinality cover-existence events are measurable for countable classes
once every pairwise empirical distance process is measurable.

This is the countable-center selection primitive feeding
`measurable_empiricalL1CoveringNumber_of_cover_event_measurable` and
`measurable_finiteEmpiricalL1CoveringNumberCard_of_cover_event_measurable`.
-/
theorem measurableSet_finiteEmpiricalL1CoverAtCard_of_countable
    {Observation : Type u} {Index : Type v} [MeasurableSpace Observation]
    [Countable Index] {n : ℕ} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    (cardinality : ℕ)
    (hdist :
      ∀ index, index ∈ indexClass ->
        ∀ center, center ∈ indexClass ->
          Measurable fun sample : SampleAt Observation n =>
            empiricalL1Distance sample (classFun index) (classFun center)) :
    MeasurableSet
      {sample : SampleAt Observation n |
        Nonempty
          (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
            cardinality)} := by
  classical
  let centerEvent : (Fin cardinality -> Index) -> Set (SampleAt Observation n) :=
    fun center =>
      {sample : SampleAt Observation n |
        (∀ centerIndex, center centerIndex ∈ indexClass) ∧
          ∀ index, index ∈ indexClass ->
            ∃ centerIndex,
              empiricalL1Distance sample (classFun index)
                (classFun (center centerIndex)) ≤ epsilon}
  have hcenterEvent_measurable :
      ∀ center, MeasurableSet (centerEvent center) := by
    intro center
    by_cases hcenter_mem : ∀ centerIndex, center centerIndex ∈ indexClass
    · have hcover_measurable :
          MeasurableSet
            (⋂ index : Index,
              {sample : SampleAt Observation n |
                index ∈ indexClass ->
                  ∃ centerIndex,
                    empiricalL1Distance sample (classFun index)
                      (classFun (center centerIndex)) ≤ epsilon}) := by
        refine MeasurableSet.iInter fun index => ?_
        by_cases hindex : index ∈ indexClass
        · have hset :
              {sample : SampleAt Observation n |
                index ∈ indexClass ->
                  ∃ centerIndex,
                    empiricalL1Distance sample (classFun index)
                      (classFun (center centerIndex)) ≤ epsilon} =
              ⋃ centerIndex : Fin cardinality,
                {sample : SampleAt Observation n |
                  empiricalL1Distance sample (classFun index)
                    (classFun (center centerIndex)) ≤ epsilon} := by
            ext sample
            simp [hindex]
          rw [hset]
          exact
            MeasurableSet.iUnion fun centerIndex =>
              measurableSet_le
                (hdist index hindex (center centerIndex)
                  (hcenter_mem centerIndex))
                measurable_const
        · have hset :
              {sample : SampleAt Observation n |
                index ∈ indexClass ->
                  ∃ centerIndex,
                    empiricalL1Distance sample (classFun index)
                      (classFun (center centerIndex)) ≤ epsilon} =
              Set.univ := by
            ext sample
            simp [hindex]
          rw [hset]
          exact MeasurableSet.univ
      have hcenterEvent_eq :
          centerEvent center =
            ⋂ index : Index,
              {sample : SampleAt Observation n |
                index ∈ indexClass ->
                  ∃ centerIndex,
                    empiricalL1Distance sample (classFun index)
                      (classFun (center centerIndex)) ≤ epsilon} := by
        ext sample
        simp [centerEvent, hcenter_mem, Set.mem_iInter]
      rw [hcenterEvent_eq]
      exact hcover_measurable
    · have hcenterEvent_eq : centerEvent center = Set.univᶜ := by
        ext sample
        simp [centerEvent, hcenter_mem]
      rw [hcenterEvent_eq]
      exact MeasurableSet.univ.compl
  have htarget_eq :
      {sample : SampleAt Observation n |
        Nonempty
          (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
            cardinality)} =
        ⋃ center : Fin cardinality -> Index, centerEvent center := by
    ext sample
    simp [centerEvent,
      nonempty_finiteEmpiricalL1CoverAtCard_iff_exists_centers]
  rw [htarget_eq]
  exact MeasurableSet.iUnion hcenterEvent_measurable

/--
Fixed-cardinality cover-existence events are measurable for countable classes of
measurable functions.
-/
theorem measurableSet_finiteEmpiricalL1CoverAtCard_of_countable_of_measurable
    {Observation : Type u} {Index : Type v} [MeasurableSpace Observation]
    [Countable Index] {n : ℕ} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    (cardinality : ℕ)
    (hclass : ∀ index, index ∈ indexClass -> Measurable (classFun index)) :
    MeasurableSet
      {sample : SampleAt Observation n |
        Nonempty
          (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
            cardinality)} :=
  measurableSet_finiteEmpiricalL1CoverAtCard_of_countable cardinality
    (fun index hindex center hcenter =>
      measurable_empiricalL1Distance_of_measurable
        (hclass index hindex) (hclass center hcenter))

/--
Measurability of the empirical `L1(P_n)` covering number from measurable
fixed-cardinality cover-existence events.

This isolates the genuine selection/measurability work.  For arbitrary
uncountable index classes, measurability of the cover-existence event is not
automatic; countable or finite center-selection hypotheses can be proved
separately and then fed through this lemma.
-/
theorem measurable_empiricalL1CoveringNumber_of_cover_event_measurable
    {Observation : Type u} {Index : Type v} [MeasurableSpace Observation]
    {n : ℕ} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    (hcover :
      ∀ cardinality : ℕ,
        MeasurableSet
          {sample : SampleAt Observation n |
            Nonempty
              (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
                cardinality)}) :
    Measurable fun sample : SampleAt Observation n =>
      empiricalL1CoveringNumber sample indexClass classFun epsilon := by
  classical
  rw [ENat.measurable_iff]
  intro cardinality
  let coverEvent : ℕ -> Set (SampleAt Observation n) :=
    fun k =>
      {sample : SampleAt Observation n |
        Nonempty
          (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon k)}
  have hcoverEvent : ∀ k, MeasurableSet (coverEvent k) := by
    intro k
    simpa [coverEvent] using hcover k
  have hpreimage :
      (fun sample : SampleAt Observation n =>
        empiricalL1CoveringNumber sample indexClass classFun epsilon) ⁻¹'
          {(cardinality : ℕ∞)} =
        coverEvent cardinality ∩
          {sample : SampleAt Observation n |
            ∀ smaller < cardinality,
              ¬Nonempty
                (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
                  smaller)} := by
    ext sample
    simp only [Set.mem_preimage, Set.mem_singleton_iff, Set.mem_inter_iff,
      Set.mem_setOf_eq, coverEvent]
    constructor
    · intro hnumber
      have hfinite :
          HasFiniteEmpiricalL1Cover sample indexClass classFun epsilon := by
        exact
          hasFinite_of_empiricalL1CoveringNumber_lt_top
            (by
              rw [hnumber]
              exact WithTop.coe_lt_top cardinality)
      have hfind_eq :
          finiteEmpiricalL1CoveringNumberCard hfinite = cardinality := by
        have hnumber_find :
            (finiteEmpiricalL1CoveringNumberCard hfinite : ℕ∞) =
              (cardinality : ℕ∞) := by
          simpa [empiricalL1CoveringNumber_eq_find hfinite] using hnumber
        exact WithTop.coe_injective hnumber_find
      have hfind_characterization :
          Nonempty
              (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
                cardinality) ∧
            ∀ smaller < cardinality,
              ¬Nonempty
                (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
                  smaller) := by
        simpa [finiteEmpiricalL1CoveringNumberCard] using
          (Nat.find_eq_iff hfinite).1 hfind_eq
      exact ⟨hfind_characterization.1, hfind_characterization.2⟩
    · rintro ⟨hcover_cardinality, hminimal⟩
      have hfinite :
          HasFiniteEmpiricalL1Cover sample indexClass classFun epsilon :=
        ⟨cardinality, hcover_cardinality⟩
      have hfind_eq :
          finiteEmpiricalL1CoveringNumberCard hfinite = cardinality := by
        simpa [finiteEmpiricalL1CoveringNumberCard] using
          (Nat.find_eq_iff hfinite).2 ⟨hcover_cardinality, hminimal⟩
      rw [empiricalL1CoveringNumber_eq_find hfinite, hfind_eq]
  rw [hpreimage]
  refine (hcoverEvent cardinality).inter ?_
  have hminimal_measurable :
      MeasurableSet
        (⋂ smaller : ℕ,
          {sample : SampleAt Observation n |
            smaller < cardinality ->
              ¬Nonempty
                (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
                  smaller)}) := by
    refine MeasurableSet.iInter fun smaller => ?_
    by_cases hlt : smaller < cardinality
    · have hset :
          {sample : SampleAt Observation n |
            smaller < cardinality ->
              ¬Nonempty
                (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
                  smaller)} = (coverEvent smaller)ᶜ := by
        ext sample
        simp [coverEvent, hlt]
      rw [hset]
      exact (hcoverEvent smaller).compl
    · have hset :
          {sample : SampleAt Observation n |
            smaller < cardinality ->
              ¬Nonempty
                (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
                  smaller)} = Set.univ := by
        ext sample
        simp [hlt]
      rw [hset]
      exact MeasurableSet.univ
  convert hminimal_measurable using 1
  ext sample
  simp [Set.mem_iInter]

/--
Measurability of the least finite empirical-cover cardinality from
fixed-cardinality cover-existence events.

This is the finite-valued companion to
`measurable_empiricalL1CoveringNumber_of_cover_event_measurable`: once every
sample has a finite empirical cover, the `Nat.find` cardinality itself is a
measurable `ℕ`-valued random variable.
-/
theorem measurable_finiteEmpiricalL1CoveringNumberCard_of_cover_event_measurable
    {Observation : Type u} {Index : Type v} [MeasurableSpace Observation]
    {n : ℕ} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    (hfinite :
      ∀ sample : SampleAt Observation n,
        HasFiniteEmpiricalL1Cover sample indexClass classFun epsilon)
    (hcover :
      ∀ cardinality : ℕ,
        MeasurableSet
          {sample : SampleAt Observation n |
            Nonempty
              (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
                cardinality)}) :
    Measurable fun sample : SampleAt Observation n =>
      finiteEmpiricalL1CoveringNumberCard (hfinite sample) := by
  classical
  unfold finiteEmpiricalL1CoveringNumberCard
  exact
    measurable_find
      (p := fun sample cardinality =>
        Nonempty
          (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
            cardinality))
      hfinite hcover

/--
For countable classes, pairwise empirical-distance measurability makes the
empirical `L1(P_n)` covering number measurable.
-/
theorem measurable_empiricalL1CoveringNumber_of_countable
    {Observation : Type u} {Index : Type v} [MeasurableSpace Observation]
    [Countable Index] {n : ℕ} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    (hdist :
      ∀ index center,
        Measurable fun sample : SampleAt Observation n =>
          empiricalL1Distance sample (classFun index) (classFun center)) :
    Measurable fun sample : SampleAt Observation n =>
      empiricalL1CoveringNumber sample indexClass classFun epsilon := by
  exact
    measurable_empiricalL1CoveringNumber_of_cover_event_measurable
      (fun cardinality =>
        measurableSet_finiteEmpiricalL1CoverAtCard_of_countable cardinality
          (fun index _hindex center _hcenter => hdist index center))

/--
The empirical `L1(P_n)` covering number is measurable for countable classes of
measurable functions.
-/
theorem measurable_empiricalL1CoveringNumber_of_countable_of_measurable
    {Observation : Type u} {Index : Type v} [MeasurableSpace Observation]
    [Countable Index] {n : ℕ} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    (hclass : ∀ index, index ∈ indexClass -> Measurable (classFun index)) :
    Measurable fun sample : SampleAt Observation n =>
      empiricalL1CoveringNumber sample indexClass classFun epsilon :=
  measurable_empiricalL1CoveringNumber_of_cover_event_measurable
    (fun cardinality =>
      measurableSet_finiteEmpiricalL1CoverAtCard_of_countable cardinality
        (fun index hindex center hcenter =>
          measurable_empiricalL1Distance_of_measurable
            (hclass index hindex) (hclass center hcenter)))

/--
For countable classes with finite empirical covers, pairwise empirical-distance
measurability makes the least finite cover cardinality measurable.
-/
theorem measurable_finiteEmpiricalL1CoveringNumberCard_of_countable
    {Observation : Type u} {Index : Type v} [MeasurableSpace Observation]
    [Countable Index] {n : ℕ} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    (hfinite :
      ∀ sample : SampleAt Observation n,
        HasFiniteEmpiricalL1Cover sample indexClass classFun epsilon)
    (hdist :
      ∀ index center,
        Measurable fun sample : SampleAt Observation n =>
          empiricalL1Distance sample (classFun index) (classFun center)) :
    Measurable fun sample : SampleAt Observation n =>
      finiteEmpiricalL1CoveringNumberCard (hfinite sample) := by
  exact
    measurable_finiteEmpiricalL1CoveringNumberCard_of_cover_event_measurable
      hfinite
      (fun cardinality =>
        measurableSet_finiteEmpiricalL1CoverAtCard_of_countable cardinality
          (fun index _hindex center _hcenter => hdist index center))

/--
The least finite empirical-cover cardinality is measurable for countable classes
of measurable functions, once every sample has a finite empirical cover.
-/
theorem measurable_finiteEmpiricalL1CoveringNumberCard_of_countable_of_measurable
    {Observation : Type u} {Index : Type v} [MeasurableSpace Observation]
    [Countable Index] {n : ℕ} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    (hfinite :
      ∀ sample : SampleAt Observation n,
        HasFiniteEmpiricalL1Cover sample indexClass classFun epsilon)
    (hclass : ∀ index, index ∈ indexClass -> Measurable (classFun index)) :
    Measurable fun sample : SampleAt Observation n =>
      finiteEmpiricalL1CoveringNumberCard (hfinite sample) :=
  measurable_finiteEmpiricalL1CoveringNumberCard_of_cover_event_measurable
    hfinite
    (fun cardinality =>
      measurableSet_finiteEmpiricalL1CoverAtCard_of_countable cardinality
        (fun index hindex center hcenter =>
          measurable_empiricalL1Distance_of_measurable
            (hclass index hindex) (hclass center hcenter)))

/--
A finite upper bound on the numeric empirical covering number produces an
explicit empirical-cover witness at that supplied cardinality.

This is the cardinality handoff needed when the entropy hypothesis bounds
`N(epsilon, F, L1(P_n))` by a finite deterministic or random cardinality.
-/
theorem exists_finiteEmpiricalL1CoverAtCard_of_empiricalL1CoveringNumber_le
    {Observation : Type u} {Index : Type v} {n : ℕ}
    {sample : SampleAt Observation n} {indexClass : Set Index}
    {classFun : Index -> Observation -> ℝ} {epsilon : ℝ}
    {cardinality : ℕ}
    (hcovering_le :
      empiricalL1CoveringNumber sample indexClass classFun epsilon ≤
        (cardinality : ℕ∞))
    (hindexClass : ∃ index, index ∈ indexClass) :
    Nonempty
      (FiniteEmpiricalL1CoverAtCard sample indexClass classFun epsilon
        cardinality) := by
  have hfinite_number :
      empiricalL1CoveringNumber sample indexClass classFun epsilon < ⊤ :=
    lt_of_le_of_lt hcovering_le (WithTop.coe_lt_top cardinality)
  let hfinite :=
    hasFinite_of_empiricalL1CoveringNumber_lt_top hfinite_number
  have hfind_cover := empiricalL1CoveringNumber_find_spec hfinite
  have hfind_le_card_enat :
      (finiteEmpiricalL1CoveringNumberCard hfinite : ℕ∞) ≤
        (cardinality : ℕ∞) := by
    rwa [empiricalL1CoveringNumber_eq_find hfinite] at hcovering_le
  have hfind_le_card :
      finiteEmpiricalL1CoveringNumberCard hfinite ≤ cardinality := by
    exact
      finiteEmpiricalL1CoveringNumberCard_le_of_empiricalL1CoveringNumber_le
        hfinite hcovering_le
  exact
    hfind_cover.elim fun cover =>
      ⟨cover.pad_cardinality hindexClass hfind_le_card⟩

/-- The external covering number is bounded by the internal mathlib covering number. -/
theorem vdVWCoveringNumber_le_internalCoveringNumber
    {Space : Type u} [PseudoEMetricSpace Space]
    (epsilon : ℝ≥0) (target : Set Space) :
    vdVWCoveringNumber epsilon target ≤ Metric.coveringNumber epsilon target := by
  exact Metric.externalCoveringNumber_le_coveringNumber epsilon target

/--
The packing number at doubled radius is bounded by the VdV&W external covering
number.  This is the first local bridge toward VdV&W Definition 2.2.3.
-/
theorem packingNumber_two_mul_le_vdVWCoveringNumber
    {Space : Type u} [PseudoEMetricSpace Space]
    (epsilon : ℝ≥0) (target : Set Space) :
    Metric.packingNumber (2 * epsilon) target ≤
      vdVWCoveringNumber epsilon target := by
  exact Metric.packingNumber_two_mul_le_externalCoveringNumber epsilon target

/-!
## Semimetric-space covering and packing numbers

VdV&W Definition 2.2.3 applies the same covering-number idea to an arbitrary
semimetric index space `(T, d)`, using all of `T` as the target.  In Lean we
represent the semimetric by a `PseudoEMetricSpace` instance and cover
`Set.univ`.
-/

/-- VdV&W semimetric covering number `N(epsilon, d)` for the whole index space. -/
noncomputable def vdVWSemimetricCoveringNumber
    (Space : Type u) [PseudoEMetricSpace Space] (epsilon : ℝ≥0) : ℕ∞ :=
  vdVWCoveringNumber epsilon (Set.univ : Set Space)

/-- VdV&W semimetric packing number `D(epsilon, d)` for the whole index space. -/
noncomputable def vdVWSemimetricPackingNumber
    (Space : Type u) [PseudoEMetricSpace Space] (epsilon : ℝ≥0) : ℕ∞ :=
  Metric.packingNumber epsilon (Set.univ : Set Space)

/-- A finite cover of the whole semimetric space at a fixed radius. -/
abbrev HasFiniteSemimetricCover
    (Space : Type u) [PseudoEMetricSpace Space] (epsilon : ℝ≥0) : Prop :=
  HasFiniteMetricCover (Set.univ : Set Space) epsilon

/-- A finite whole-space cover makes `N(epsilon, d)` finite. -/
theorem vdVWSemimetricCoveringNumber_lt_top_of_hasFiniteCover
    {Space : Type u} [PseudoEMetricSpace Space] {epsilon : ℝ≥0}
    (hfinite : HasFiniteSemimetricCover Space epsilon) :
    vdVWSemimetricCoveringNumber Space epsilon < ⊤ :=
  vdVWCoveringNumber_lt_top_of_hasFiniteMetricCover hfinite

/-- A finite type has finite semimetric covering number at every radius. -/
theorem vdVWSemimetricCoveringNumber_lt_top_of_finite
    (Space : Type u) [PseudoEMetricSpace Space] [Finite Space]
    (epsilon : ℝ≥0) :
    vdVWSemimetricCoveringNumber Space epsilon < ⊤ :=
  vdVWCoveringNumber_lt_top_of_finite epsilon (Set.toFinite Set.univ)

/-- A totally bounded semimetric space has finite covering number at every positive radius. -/
theorem vdVWSemimetricCoveringNumber_lt_top_of_totallyBounded
    (Space : Type u) [PseudoEMetricSpace Space] {epsilon : ℝ≥0}
    (hepsilon : epsilon ≠ 0)
    (hspace : TotallyBounded (Set.univ : Set Space)) :
    vdVWSemimetricCoveringNumber Space epsilon < ⊤ :=
  vdVWCoveringNumber_lt_top_of_totallyBounded hepsilon hspace

/--
VdV&W's first covering-packing comparison, in mathlib's closed-ball
convention: `N(epsilon, d) <= D(epsilon, d)`.
-/
theorem vdVWSemimetricCoveringNumber_le_packingNumber
    (Space : Type u) [PseudoEMetricSpace Space] (epsilon : ℝ≥0) :
    vdVWSemimetricCoveringNumber Space epsilon ≤
      vdVWSemimetricPackingNumber Space epsilon := by
  unfold vdVWSemimetricCoveringNumber vdVWSemimetricPackingNumber
  exact
    (Metric.externalCoveringNumber_le_coveringNumber epsilon
      (Set.univ : Set Space)).trans
      (Metric.coveringNumber_le_packingNumber epsilon (Set.univ : Set Space))

/--
VdV&W's second covering-packing comparison, in mathlib's closed-ball
convention: `D(epsilon, d) <= N(epsilon / 2, d)`.
-/
theorem vdVWSemimetricPackingNumber_le_coveringNumber_half
    (Space : Type u) [PseudoEMetricSpace Space] (epsilon : ℝ≥0) :
    vdVWSemimetricPackingNumber Space epsilon ≤
      vdVWSemimetricCoveringNumber Space (epsilon / 2) := by
  simpa [vdVWSemimetricPackingNumber, vdVWSemimetricCoveringNumber,
    vdVWCoveringNumber, show (2 : ℝ≥0) * (epsilon / 2) = epsilon by ring] using
    Metric.packingNumber_two_mul_le_externalCoveringNumber (epsilon / 2)
      (Set.univ : Set Space)

/--
Finiteness of the semimetric covering number at half radius implies finiteness
of the packing number at the original radius.
-/
theorem vdVWSemimetricPackingNumber_lt_top_of_coveringNumber_half_lt_top
    (Space : Type u) [PseudoEMetricSpace Space] {epsilon : ℝ≥0}
    (hcover :
      vdVWSemimetricCoveringNumber Space (epsilon / 2) < ⊤) :
    vdVWSemimetricPackingNumber Space epsilon < ⊤ :=
  lt_of_le_of_lt
    (vdVWSemimetricPackingNumber_le_coveringNumber_half Space epsilon)
    hcover

/--
If all positive-radius semimetric covering numbers are finite, then all
positive-radius semimetric packing numbers are finite.
-/
theorem vdVWSemimetricPackingNumber_lt_top_forall_of_coveringNumber_lt_top_forall
    (Space : Type u) [PseudoEMetricSpace Space]
    (hcover :
      ∀ epsilon : ℝ≥0, epsilon ≠ 0 ->
        vdVWSemimetricCoveringNumber Space epsilon < ⊤) :
    ∀ epsilon : ℝ≥0, epsilon ≠ 0 ->
      vdVWSemimetricPackingNumber Space epsilon < ⊤ := by
  intro epsilon hepsilon
  exact
    vdVWSemimetricPackingNumber_lt_top_of_coveringNumber_half_lt_top Space
      (hcover (epsilon / 2) (by positivity))

/-- A totally bounded semimetric space has finite packing number at every positive radius. -/
theorem vdVWSemimetricPackingNumber_lt_top_of_totallyBounded
    (Space : Type u) [PseudoEMetricSpace Space] {epsilon : ℝ≥0}
    (hepsilon : epsilon ≠ 0)
    (hspace : TotallyBounded (Set.univ : Set Space)) :
    vdVWSemimetricPackingNumber Space epsilon < ⊤ :=
  vdVWSemimetricPackingNumber_lt_top_of_coveringNumber_half_lt_top Space
    (vdVWSemimetricCoveringNumber_lt_top_of_totallyBounded Space
      (by positivity) hspace)

end StatInference
