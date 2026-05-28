import StatInference.EmpiricalProcess.GlivenkoCantelli
import StatInference.EmpiricalProcess.OuterExpectation
import StatInference.EmpiricalProcess.OuterProbabilityExpectation
import Mathlib.MeasureTheory.Function.ConvergenceInDistribution
import Mathlib.MeasureTheory.Measure.FiniteMeasurePi
import Mathlib.MeasureTheory.Measure.FiniteMeasureProd
import Mathlib.MeasureTheory.Measure.ProbabilityMeasure
import Mathlib.MeasureTheory.Measure.Prokhorov
import Mathlib.MeasureTheory.Measure.TightNormed

/-!
# Weak-convergence foundation wrappers

This module records Chapter 1 weak-convergence primitives from van der Vaart
and Wellner in names local to this project, while reusing pinned mathlib
theorems as the proof authority whenever the statement is the classical
measure-level or measurable-random-variable version.
-/

namespace StatInference

open Filter MeasureTheory ProbabilityTheory TopologicalSpace

open scoped BoundedContinuousFunction ENNReal Topology InnerProductSpace

universe u v w x

/--
Nonnegative outer/inner expectation gap for a possibly nonmeasurable test
composition.

This is a scoped Chapter 1 primitive on the way to VdV&W asymptotic
measurability.  It intentionally uses the already formalized nonnegative
outer/inner expectations; the full signed extended-real textbook layer remains
separate.
-/
noncomputable def VdVWNonnegativeOuterInnerExpectationGap
    {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω)
    (T : Ω -> ℝ≥0∞) : ℝ≥0∞ :=
  VdVWOuterExpectation μ T - VdVWInnerExpectation μ T

/--
The nonnegative outer/inner expectation gap vanishes exactly when the outer and
inner expectations coincide.
-/
theorem VdVWNonnegativeOuterInnerExpectationGap_eq_zero_iff_outer_eq_inner
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {T : Ω -> ℝ≥0∞} :
    VdVWNonnegativeOuterInnerExpectationGap μ T = 0 ↔
      VdVWOuterExpectation μ T = VdVWInnerExpectation μ T := by
  constructor
  · intro hgap
    have hle :
        VdVWOuterExpectation μ T ≤ VdVWInnerExpectation μ T := by
      simpa [VdVWNonnegativeOuterInnerExpectationGap] using
        (tsub_eq_zero_iff_le.mp hgap)
    exact le_antisymm hle VdVWInnerExpectation_le_outerExpectation
  · intro hEq
    simp [VdVWNonnegativeOuterInnerExpectationGap, hEq]

/--
Measurable nonnegative maps have zero VdV&W nonnegative outer/inner
expectation gap.
-/
theorem VdVWNonnegativeOuterInnerExpectationGap_eq_zero_of_measurable
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {T : Ω -> ℝ≥0∞} (hT : Measurable T) :
    VdVWNonnegativeOuterInnerExpectationGap μ T = 0 := by
  unfold VdVWNonnegativeOuterInnerExpectationGap
  rw [VdVWOuterExpectation_eq_innerExpectation_of_measurable hT]
  simp

/--
A.e.-measurable nonnegative maps have zero VdV&W nonnegative outer/inner
expectation gap.
-/
theorem VdVWNonnegativeOuterInnerExpectationGap_eq_zero_of_aemeasurable
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {T : Ω -> ℝ≥0∞} (hT : AEMeasurable T μ) :
    VdVWNonnegativeOuterInnerExpectationGap μ T = 0 := by
  unfold VdVWNonnegativeOuterInnerExpectationGap
  rw [VdVWOuterExpectation_eq_innerExpectation_of_aemeasurable hT]
  simp

/--
Signed positive/negative VdV&W outer expectation of a real-valued map.

This is the signed Chapter 1 bridge available from the current nonnegative
outer-expectation primitive.  It is deliberately named as a positive/negative
outer construction: the full arbitrary-map signed outer/inner expectation
textbook API still has to track finiteness and nonmeasurable cover clauses
separately.
-/
noncomputable def VdVWSignedOuterExpectationPosNeg
    {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω)
    (Y : Ω -> ℝ) : ℝ :=
  ENNReal.toReal (VdVWOuterExpectation μ (fun ω => ENNReal.ofReal (Y ω))) -
    ENNReal.toReal (VdVWOuterExpectation μ (fun ω => ENNReal.ofReal (-Y ω)))

/--
For a measurable integrable real map, the signed positive/negative VdV&W
outer expectation agrees with the ordinary Bochner integral.
-/
theorem VdVWSignedOuterExpectationPosNeg_eq_integral_of_measurable
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {Y : Ω -> ℝ} (hY_meas : Measurable Y) (hY_int : Integrable Y μ) :
    VdVWSignedOuterExpectationPosNeg μ Y = ∫ ω, Y ω ∂μ := by
  simpa [VdVWSignedOuterExpectationPosNeg] using
    VdVWOuterExpectation_posPart_sub_negPart_eq_integral_of_measurable
      hY_meas hY_int

/--
For an a.e.-measurable integrable real map, the signed positive/negative
VdV&W outer expectation agrees with the ordinary Bochner integral.
-/
theorem VdVWSignedOuterExpectationPosNeg_eq_integral_of_aemeasurable
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {Y : Ω -> ℝ} (hY_aemeas : AEMeasurable Y μ)
    (hY_int : Integrable Y μ) :
    VdVWSignedOuterExpectationPosNeg μ Y = ∫ ω, Y ω ∂μ := by
  simpa [VdVWSignedOuterExpectationPosNeg] using
    VdVWOuterExpectation_posPart_sub_negPart_eq_integral_of_aemeasurable
      hY_aemeas hY_int

/--
For a null-measurable integrable real map, the signed positive/negative VdV&W
outer expectation agrees with the ordinary Bochner integral.
-/
theorem VdVWSignedOuterExpectationPosNeg_eq_integral_of_nullMeasurable
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {Y : Ω -> ℝ} (hY_null : NullMeasurable Y μ) (hY_int : Integrable Y μ) :
    VdVWSignedOuterExpectationPosNeg μ Y = ∫ ω, Y ω ∂μ :=
  VdVWSignedOuterExpectationPosNeg_eq_integral_of_aemeasurable
    hY_null.aemeasurable hY_int

/--
Composable form of the measurable signed positive/negative outer-expectation
bridge.
-/
theorem VdVWSignedOuterExpectationPosNeg_eq_integral_of_measurable_comp
    {Ω : Type u} {S : Type v} [MeasurableSpace Ω] [MeasurableSpace S]
    {μ : Measure Ω} {X : Ω -> S} {f : S -> ℝ}
    (hX : Measurable X) (hf : Measurable f)
    (hint : Integrable (fun ω => f (X ω)) μ) :
    VdVWSignedOuterExpectationPosNeg μ (fun ω => f (X ω)) =
      ∫ ω, f (X ω) ∂μ :=
  VdVWSignedOuterExpectationPosNeg_eq_integral_of_measurable
    (hf.comp hX) hint

/--
Composable form of the a.e.-measurable signed positive/negative
outer-expectation bridge.
-/
theorem VdVWSignedOuterExpectationPosNeg_eq_integral_of_aemeasurable_comp
    {Ω : Type u} {S : Type v} [MeasurableSpace Ω] [MeasurableSpace S]
    {μ : Measure Ω} {X : Ω -> S} {f : S -> ℝ}
    (hX : AEMeasurable X μ) (hf : Measurable f)
    (hint : Integrable (fun ω => f (X ω)) μ) :
    VdVWSignedOuterExpectationPosNeg μ (fun ω => f (X ω)) =
      ∫ ω, f (X ω) ∂μ :=
  VdVWSignedOuterExpectationPosNeg_eq_integral_of_aemeasurable
    (hf.comp_aemeasurable hX) hint

/--
Bounded-continuous tests composed with measurable maps have the expected
signed positive/negative VdV&W outer expectation on finite measure spaces.

This is the measurable-map specialization needed by the Chapter 1 weak-
convergence lane before replacing the current lower-shifted proxy by a full
signed arbitrary-map outer/inner expectation API.
-/
theorem VdVWSignedOuterExpectationPosNeg_eq_integral_of_boundedContinuous_comp
    {Ω : Type u} {S : Type v} [MeasurableSpace Ω] [MeasurableSpace S]
    [TopologicalSpace S] [OpensMeasurableSpace S]
    {μ : Measure Ω} [IsFiniteMeasure μ] {X : Ω -> S}
    (hX : Measurable X) (f : S →ᵇ ℝ) :
    VdVWSignedOuterExpectationPosNeg μ (fun ω => f (X ω)) =
      ∫ ω, f (X ω) ∂μ :=
  VdVWSignedOuterExpectationPosNeg_eq_integral_of_measurable_comp hX
    f.continuous.measurable
    (Integrable.of_bound
      ((f.continuous.measurable.comp hX).aestronglyMeasurable) ‖f‖
      (Eventually.of_forall fun ω => f.norm_coe_le_norm (X ω)))

/--
Bounded-continuous tests composed with a.e.-measurable maps have the expected
signed positive/negative VdV&W outer expectation on finite measure spaces.
-/
theorem VdVWSignedOuterExpectationPosNeg_eq_integral_of_boundedContinuous_comp_aemeasurable
    {Ω : Type u} {S : Type v} [MeasurableSpace Ω] [MeasurableSpace S]
    [TopologicalSpace S] [OpensMeasurableSpace S]
    {μ : Measure Ω} [IsFiniteMeasure μ] {X : Ω -> S}
    (hX : AEMeasurable X μ) (f : S →ᵇ ℝ) :
    VdVWSignedOuterExpectationPosNeg μ (fun ω => f (X ω)) =
      ∫ ω, f (X ω) ∂μ :=
  VdVWSignedOuterExpectationPosNeg_eq_integral_of_aemeasurable_comp hX
    f.continuous.measurable
    (Integrable.of_bound
      ((f.continuous.measurable.comp_aemeasurable hX).aestronglyMeasurable)
      ‖f‖
      (Eventually.of_forall fun ω => f.norm_coe_le_norm (X ω)))

/--
Bounded-continuous tests composed with null-measurable maps have the expected
signed positive/negative VdV&W outer expectation on finite measure spaces.
-/
theorem VdVWSignedOuterExpectationPosNeg_eq_integral_of_boundedContinuous_comp_nullMeasurable
    {Ω : Type u} {S : Type v} [MeasurableSpace Ω] [MeasurableSpace S]
    [TopologicalSpace S] [OpensMeasurableSpace S]
    {μ : Measure Ω} [IsFiniteMeasure μ] {X : Ω -> S}
    (hX : NullMeasurable X μ) (f : S →ᵇ ℝ) :
    VdVWSignedOuterExpectationPosNeg μ (fun ω => f (X ω)) =
      ∫ ω, f (X ω) ∂μ := by
  have hY_null : NullMeasurable (fun ω => f (X ω)) μ :=
    f.continuous.measurable.comp_nullMeasurable hX
  exact
    VdVWSignedOuterExpectationPosNeg_eq_integral_of_aemeasurable hY_null.aemeasurable
      (Integrable.of_bound hY_null.aemeasurable.aestronglyMeasurable ‖f‖
        (Eventually.of_forall fun ω => f.norm_coe_le_norm (X ω)))

/--
First-coordinate probability-product invariance for the signed
positive/negative VdV&W outer expectation.

Adjoining an ignored probability coordinate does not change the signed
outer-expectation value of an a.e.-measurable real statistic.
-/
theorem VdVWSignedOuterExpectationPosNeg_prod_fst_eq_of_aemeasurable
    {Ω : Type u} {S : Type v} [MeasurableSpace Ω] [MeasurableSpace S]
    {μ : Measure Ω} {ν : Measure S} [SFinite μ] [SFinite ν]
    [IsProbabilityMeasure ν]
    {Y : Ω -> ℝ} (hY : AEMeasurable Y μ) :
    VdVWSignedOuterExpectationPosNeg (μ.prod ν) (fun z : Ω × S => Y z.1) =
      VdVWSignedOuterExpectationPosNeg μ Y := by
  simp [VdVWSignedOuterExpectationPosNeg,
    VdVWOuterExpectation_prod_fst_eq_of_aemeasurable hY.ennreal_ofReal,
    VdVWOuterExpectation_prod_fst_eq_of_aemeasurable hY.neg.ennreal_ofReal]

/--
Second-coordinate probability-product invariance for the signed
positive/negative VdV&W outer expectation.
-/
theorem VdVWSignedOuterExpectationPosNeg_prod_snd_eq_of_aemeasurable
    {Ω : Type u} {S : Type v} [MeasurableSpace Ω] [MeasurableSpace S]
    {μ : Measure Ω} {ν : Measure S} [SFinite μ] [SFinite ν]
    [IsProbabilityMeasure μ]
    {Y : S -> ℝ} (hY : AEMeasurable Y ν) :
    VdVWSignedOuterExpectationPosNeg (μ.prod ν) (fun z : Ω × S => Y z.2) =
      VdVWSignedOuterExpectationPosNeg ν Y := by
  simp [VdVWSignedOuterExpectationPosNeg,
    VdVWOuterExpectation_prod_snd_eq_of_aemeasurable hY.ennreal_ofReal,
    VdVWOuterExpectation_prod_snd_eq_of_aemeasurable hY.neg.ennreal_ofReal]

/--
Signed-outer bounded-continuous weak convergence for possibly arbitrary maps.

This is the current honest Chapter 1 bridge toward VdV&W Definition 1.3.3 for
arbitrary maps: bounded continuous tests are evaluated through the local
positive/negative outer-expectation construction.  It is intentionally a
separate predicate from the already proved probability-measure weak
convergence wrapper, because exact nonmeasurable-map clauses still need
additional outer-cover support.
-/
def VdVWWeakConvergenceSignedOuterBoundedContinuous
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S]
    (μs : ι -> Measure Ω) (X : ι -> Ω -> S) (l : Filter ι)
    (μ : ProbabilityMeasure S) : Prop :=
  ∀ f : S →ᵇ ℝ,
    Tendsto
      (fun i => VdVWSignedOuterExpectationPosNeg (μs i)
        (fun ω => f (X i ω)))
      l (𝓝 (∫ s, f s ∂(μ : Measure S)))

/--
Continuous maps preserve signed-outer bounded-continuous weak convergence.

This is the direct VdV&W arbitrary-map analogue of the continuous-mapping
theorem for the current signed-outer bounded-continuous weak-convergence
predicate.
-/
theorem VdVWWeakConvergenceSignedOuterBoundedContinuous.comp_continuous
    {Ω : Type u} {S : Type v} {T : Type w} {ι : Type x}
    [MeasurableSpace Ω]
    [MeasurableSpace S] [TopologicalSpace S] [OpensMeasurableSpace S]
    [MeasurableSpace T] [TopologicalSpace T] [BorelSpace T]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S} {l : Filter ι}
    {μ : ProbabilityMeasure S}
    (h : VdVWWeakConvergenceSignedOuterBoundedContinuous μs X l μ)
    {g : S -> T} (hg : Continuous g) :
    VdVWWeakConvergenceSignedOuterBoundedContinuous μs
      (fun i ω => g (X i ω)) l (μ.map hg.measurable.aemeasurable) := by
  intro f
  let gC : C(S, T) := ⟨g, hg⟩
  have hbase := h (f.compContinuous gC)
  have htarget :
      (∫ t, f t ∂((μ.map hg.measurable.aemeasurable : ProbabilityMeasure T) :
        Measure T)) =
        ∫ s, f (g s) ∂(μ : Measure S) := by
    simpa [gC] using
      (integral_map hg.measurable.aemeasurable
        f.continuous.measurable.aestronglyMeasurable :
        ∫ t, f t ∂Measure.map g (μ : Measure S) =
          ∫ s, f (g s) ∂(μ : Measure S))
  rw [htarget]
  simpa [VdVWWeakConvergenceSignedOuterBoundedContinuous, gC] using hbase

/--
Signed-outer bounded-continuous weak convergence is stable under passing to a
finer index filter.
-/
theorem VdVWWeakConvergenceSignedOuterBoundedContinuous.mono_filter
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S}
    {l l' : Filter ι} {μ : ProbabilityMeasure S}
    (h : VdVWWeakConvergenceSignedOuterBoundedContinuous μs X l μ)
    (hl : l' ≤ l) :
    VdVWWeakConvergenceSignedOuterBoundedContinuous μs X l' μ := by
  intro f
  exact (h f).mono_left hl

/--
Signed-outer bounded-continuous weak convergence is unchanged by eventually
equal measure families and eventually equal arbitrary maps.
-/
theorem VdVWWeakConvergenceSignedOuterBoundedContinuous.congr_eventually
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S]
    {μs νs : ι -> Measure Ω} {X Y : ι -> Ω -> S}
    {l : Filter ι} {μ : ProbabilityMeasure S}
    (h : VdVWWeakConvergenceSignedOuterBoundedContinuous μs X l μ)
    (hμ : ∀ᶠ i in l, νs i = μs i)
    (hX : ∀ᶠ i in l, Y i = X i) :
    VdVWWeakConvergenceSignedOuterBoundedContinuous νs Y l μ := by
  intro f
  refine Tendsto.congr' ?_ (h f)
  filter_upwards [hμ, hX] with i hνμ hYX
  simp [hνμ, hYX]

/--
Signed-outer bounded-continuous weak convergence is stable under reindexing
along a map that tends to the original index filter.
-/
theorem VdVWWeakConvergenceSignedOuterBoundedContinuous.comp_tendsto
    {Ω : Type u} {S : Type v} {ι : Type w} {κ : Type x}
    [MeasurableSpace Ω] [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S}
    {l : Filter ι} {l' : Filter κ} {μ : ProbabilityMeasure S}
    (h : VdVWWeakConvergenceSignedOuterBoundedContinuous μs X l μ)
    {u : κ -> ι} (hu : Tendsto u l' l) :
    VdVWWeakConvergenceSignedOuterBoundedContinuous
      (fun k => μs (u k)) (fun k ω => X (u k) ω) l' μ := by
  intro f
  exact (h f).comp hu

/--
Signed bounded-continuous outer/inner expectation gap for an arbitrary real
map.

The current Chapter 1.2 layer is nonnegative, so the signed gap is represented
by the two nonnegative gaps of the positive and negative parts.  This is the
honest bridge needed before stating VdV&W arbitrary-map asymptotic
measurability for bounded-continuous real tests.
-/
noncomputable def VdVWSignedBoundedContinuousOuterInnerExpectationGap
    {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω)
    (Y : Ω -> ℝ) : ℝ≥0∞ :=
  VdVWNonnegativeOuterInnerExpectationGap μ (fun ω => ENNReal.ofReal (Y ω)) +
    VdVWNonnegativeOuterInnerExpectationGap μ (fun ω => ENNReal.ofReal (-Y ω))

/--
The signed positive/negative outer/inner expectation gap vanishes exactly when
both nonnegative positive-part and negative-part outer expectations coincide
with their corresponding inner expectations.
-/
theorem VdVWSignedBoundedContinuousOuterInnerExpectationGap_eq_zero_iff
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {Y : Ω -> ℝ} :
    VdVWSignedBoundedContinuousOuterInnerExpectationGap μ Y = 0 ↔
      (VdVWOuterExpectation μ (fun ω => ENNReal.ofReal (Y ω)) =
          VdVWInnerExpectation μ (fun ω => ENNReal.ofReal (Y ω))) ∧
        (VdVWOuterExpectation μ (fun ω => ENNReal.ofReal (-Y ω)) =
          VdVWInnerExpectation μ (fun ω => ENNReal.ofReal (-Y ω))) := by
  simp [VdVWSignedBoundedContinuousOuterInnerExpectationGap,
    VdVWNonnegativeOuterInnerExpectationGap_eq_zero_iff_outer_eq_inner]

/--
Measurable real maps have zero signed positive/negative outer/inner
expectation gap.
-/
theorem VdVWSignedBoundedContinuousOuterInnerExpectationGap_eq_zero_of_measurable
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {Y : Ω -> ℝ} (hY : Measurable Y) :
    VdVWSignedBoundedContinuousOuterInnerExpectationGap μ Y = 0 := by
  simp [VdVWSignedBoundedContinuousOuterInnerExpectationGap,
    VdVWNonnegativeOuterInnerExpectationGap_eq_zero_of_measurable hY.ennreal_ofReal,
    VdVWNonnegativeOuterInnerExpectationGap_eq_zero_of_measurable hY.neg.ennreal_ofReal]

/--
Null-measurable real maps have zero signed positive/negative outer/inner
expectation gap.
-/
theorem VdVWSignedBoundedContinuousOuterInnerExpectationGap_eq_zero_of_nullMeasurable
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {Y : Ω -> ℝ} (hY : NullMeasurable Y μ) :
    VdVWSignedBoundedContinuousOuterInnerExpectationGap μ Y = 0 := by
  simp [VdVWSignedBoundedContinuousOuterInnerExpectationGap,
    VdVWNonnegativeOuterInnerExpectationGap_eq_zero_of_aemeasurable
      (hY.aemeasurable.ennreal_ofReal),
    VdVWNonnegativeOuterInnerExpectationGap_eq_zero_of_aemeasurable
      (hY.aemeasurable.neg.ennreal_ofReal)]

/--
A.e.-measurable real maps have zero signed positive/negative outer/inner
expectation gap.
-/
theorem VdVWSignedBoundedContinuousOuterInnerExpectationGap_eq_zero_of_aemeasurable
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {Y : Ω -> ℝ} (hY : AEMeasurable Y μ) :
    VdVWSignedBoundedContinuousOuterInnerExpectationGap μ Y = 0 := by
  simp [VdVWSignedBoundedContinuousOuterInnerExpectationGap,
    VdVWNonnegativeOuterInnerExpectationGap_eq_zero_of_aemeasurable
      hY.ennreal_ofReal,
    VdVWNonnegativeOuterInnerExpectationGap_eq_zero_of_aemeasurable
      hY.neg.ennreal_ofReal]

/--
First-coordinate probability-product invariance for the signed
outer/inner expectation gap.

This is the asymptotic-measurability counterpart of
`VdVWSignedOuterExpectationPosNeg_prod_fst_eq_of_aemeasurable`.
-/
theorem VdVWSignedBoundedContinuousOuterInnerExpectationGap_prod_fst_eq_of_aemeasurable
    {Ω : Type u} {S : Type v} [MeasurableSpace Ω] [MeasurableSpace S]
    {μ : Measure Ω} {ν : Measure S} [SFinite μ] [SFinite ν]
    [IsProbabilityMeasure ν]
    {Y : Ω -> ℝ} (hY : AEMeasurable Y μ) :
    VdVWSignedBoundedContinuousOuterInnerExpectationGap (μ.prod ν)
        (fun z : Ω × S => Y z.1) =
      VdVWSignedBoundedContinuousOuterInnerExpectationGap μ Y := by
  simp [VdVWSignedBoundedContinuousOuterInnerExpectationGap,
    VdVWNonnegativeOuterInnerExpectationGap,
    VdVWOuterExpectation_prod_fst_eq_of_aemeasurable hY.ennreal_ofReal,
    VdVWInnerExpectation_prod_fst_eq_of_aemeasurable hY.ennreal_ofReal,
    VdVWOuterExpectation_prod_fst_eq_of_aemeasurable hY.neg.ennreal_ofReal,
    VdVWInnerExpectation_prod_fst_eq_of_aemeasurable hY.neg.ennreal_ofReal]

/--
Second-coordinate probability-product invariance for the signed
outer/inner expectation gap.
-/
theorem VdVWSignedBoundedContinuousOuterInnerExpectationGap_prod_snd_eq_of_aemeasurable
    {Ω : Type u} {S : Type v} [MeasurableSpace Ω] [MeasurableSpace S]
    {μ : Measure Ω} {ν : Measure S} [SFinite μ] [SFinite ν]
    [IsProbabilityMeasure μ]
    {Y : S -> ℝ} (hY : AEMeasurable Y ν) :
    VdVWSignedBoundedContinuousOuterInnerExpectationGap (μ.prod ν)
        (fun z : Ω × S => Y z.2) =
      VdVWSignedBoundedContinuousOuterInnerExpectationGap ν Y := by
  simp [VdVWSignedBoundedContinuousOuterInnerExpectationGap,
    VdVWNonnegativeOuterInnerExpectationGap,
    VdVWOuterExpectation_prod_snd_eq_of_aemeasurable hY.ennreal_ofReal,
    VdVWInnerExpectation_prod_snd_eq_of_aemeasurable hY.ennreal_ofReal,
    VdVWOuterExpectation_prod_snd_eq_of_aemeasurable hY.neg.ennreal_ofReal,
    VdVWInnerExpectation_prod_snd_eq_of_aemeasurable hY.neg.ennreal_ofReal]

/--
Signed bounded-continuous asymptotic measurability for arbitrary maps.

This is the closest local predicate to the signed part of VdV&W Definition
1.3.7: every bounded continuous real test has vanishing positive/negative
outer/inner expectation gap along the process.
-/
def VdVWAsymptoticallyMeasurableSignedBoundedContinuous
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [TopologicalSpace S]
    (μs : ι -> Measure Ω) (X : ι -> Ω -> S) (l : Filter ι) : Prop :=
  ∀ f : S →ᵇ ℝ,
    Tendsto
      (fun i =>
        VdVWSignedBoundedContinuousOuterInnerExpectationGap (μs i)
          (fun ω => f (X i ω)))
      l (𝓝 0)

/--
Measurable maps into a topological measurable state space are signed
bounded-continuous asymptotically measurable.
-/
theorem VdVWAsymptoticallyMeasurableSignedBoundedContinuous.of_forall_measurable
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S} {l : Filter ι}
    (hX : ∀ i, Measurable (X i)) :
    VdVWAsymptoticallyMeasurableSignedBoundedContinuous μs X l := by
  intro f
  have hzero :
      (fun i =>
        VdVWSignedBoundedContinuousOuterInnerExpectationGap (μs i)
          (fun ω => f (X i ω))) = fun _ => 0 := by
    funext i
    exact
      VdVWSignedBoundedContinuousOuterInnerExpectationGap_eq_zero_of_measurable
        (f.continuous.measurable.comp (hX i))
  simpa [hzero] using
    (tendsto_const_nhds :
      Tendsto (fun _ : ι => (0 : ℝ≥0∞)) l (𝓝 0))

/--
Null-measurable maps into a topological measurable state space are signed
bounded-continuous asymptotically measurable.
-/
theorem VdVWAsymptoticallyMeasurableSignedBoundedContinuous.of_forall_nullMeasurable
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S} {l : Filter ι}
    (hX : ∀ i, NullMeasurable (X i) (μs i)) :
    VdVWAsymptoticallyMeasurableSignedBoundedContinuous μs X l := by
  intro f
  have hzero :
      (fun i =>
        VdVWSignedBoundedContinuousOuterInnerExpectationGap (μs i)
          (fun ω => f (X i ω))) = fun _ => 0 := by
    funext i
    exact
      VdVWSignedBoundedContinuousOuterInnerExpectationGap_eq_zero_of_nullMeasurable
        (f.continuous.measurable.comp_nullMeasurable (hX i))
  simpa [hzero] using
    (tendsto_const_nhds :
      Tendsto (fun _ : ι => (0 : ℝ≥0∞)) l (𝓝 0))

/--
A.e.-measurable maps into a topological measurable state space are signed
bounded-continuous asymptotically measurable.
-/
theorem VdVWAsymptoticallyMeasurableSignedBoundedContinuous.of_forall_aemeasurable
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [MeasurableSpace S]
    [TopologicalSpace S] [OpensMeasurableSpace S]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S} {l : Filter ι}
    (hX : ∀ i, AEMeasurable (X i) (μs i)) :
    VdVWAsymptoticallyMeasurableSignedBoundedContinuous μs X l := by
  intro f
  have hzero :
      (fun i =>
        VdVWSignedBoundedContinuousOuterInnerExpectationGap (μs i)
          (fun ω => f (X i ω))) = fun _ => 0 := by
    funext i
    exact
      VdVWSignedBoundedContinuousOuterInnerExpectationGap_eq_zero_of_aemeasurable
        (f.continuous.measurable.comp_aemeasurable (hX i))
  simpa [hzero] using
    (tendsto_const_nhds :
      Tendsto (fun _ : ι => (0 : ℝ≥0∞)) l (𝓝 0))

/--
Continuous maps preserve signed bounded-continuous asymptotic measurability.
-/
theorem VdVWAsymptoticallyMeasurableSignedBoundedContinuous.comp_continuous
    {Ω : Type u} {S : Type v} {T : Type w} {ι : Type x}
    [MeasurableSpace Ω] [TopologicalSpace S] [TopologicalSpace T]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S} {l : Filter ι}
    (h : VdVWAsymptoticallyMeasurableSignedBoundedContinuous μs X l)
    {g : S -> T} (hg : Continuous g) :
    VdVWAsymptoticallyMeasurableSignedBoundedContinuous
      μs (fun i ω => g (X i ω)) l := by
  intro f
  let gC : C(S, T) := ⟨g, hg⟩
  simpa [gC] using h (f.compContinuous gC)

/--
Signed bounded-continuous asymptotic measurability is stable under passing to
a finer index filter.
-/
theorem VdVWAsymptoticallyMeasurableSignedBoundedContinuous.mono_filter
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [TopologicalSpace S]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S}
    {l l' : Filter ι}
    (h : VdVWAsymptoticallyMeasurableSignedBoundedContinuous μs X l)
    (hl : l' ≤ l) :
    VdVWAsymptoticallyMeasurableSignedBoundedContinuous μs X l' := by
  intro f
  exact (h f).mono_left hl

/--
Signed bounded-continuous asymptotic measurability is unchanged by eventually
equal measure families and eventually equal arbitrary maps.
-/
theorem VdVWAsymptoticallyMeasurableSignedBoundedContinuous.congr_eventually
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [TopologicalSpace S]
    {μs νs : ι -> Measure Ω} {X Y : ι -> Ω -> S}
    {l : Filter ι}
    (h : VdVWAsymptoticallyMeasurableSignedBoundedContinuous μs X l)
    (hμ : ∀ᶠ i in l, νs i = μs i)
    (hX : ∀ᶠ i in l, Y i = X i) :
    VdVWAsymptoticallyMeasurableSignedBoundedContinuous νs Y l := by
  intro f
  refine Tendsto.congr' ?_ (h f)
  filter_upwards [hμ, hX] with i hνμ hYX
  simp [hνμ, hYX]

/--
Signed bounded-continuous asymptotic measurability is stable under reindexing
along a map that tends to the original index filter.
-/
theorem VdVWAsymptoticallyMeasurableSignedBoundedContinuous.comp_tendsto
    {Ω : Type u} {S : Type v} {ι : Type w} {κ : Type x}
    [MeasurableSpace Ω] [TopologicalSpace S]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S}
    {l : Filter ι} {l' : Filter κ}
    (h : VdVWAsymptoticallyMeasurableSignedBoundedContinuous μs X l)
    {u : κ -> ι} (hu : Tendsto u l' l) :
    VdVWAsymptoticallyMeasurableSignedBoundedContinuous
      (fun k => μs (u k)) (fun k ω => X (u k) ω) l' := by
  intro f
  exact (h f).comp hu

/--
Proof-carrying signed bounded-continuous arbitrary-map weak convergence.

The structure packages the signed-outer bounded-continuous convergence
predicate together with the signed outer/inner asymptotic-measurability
predicate above.  It is still a local Chapter 1 bridge: exact VdV&W
nonmeasurable cover and asymptotic-tightness clauses remain separate.
-/
structure VdVWWeakConvergenceSignedBoundedContinuousArbitraryMap
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S]
    (μs : ι -> Measure Ω) (X : ι -> Ω -> S) (l : Filter ι)
    (μ : ProbabilityMeasure S) : Prop where
  weakConvergence :
    VdVWWeakConvergenceSignedOuterBoundedContinuous μs X l μ
  asymptoticMeasurability :
    VdVWAsymptoticallyMeasurableSignedBoundedContinuous μs X l

/--
Continuous maps preserve the proof-carrying signed bounded-continuous
arbitrary-map weak-convergence layer.
-/
theorem VdVWWeakConvergenceSignedBoundedContinuousArbitraryMap.comp_continuous
    {Ω : Type u} {S : Type v} {T : Type w} {ι : Type x}
    [MeasurableSpace Ω]
    [MeasurableSpace S] [TopologicalSpace S] [OpensMeasurableSpace S]
    [MeasurableSpace T] [TopologicalSpace T] [BorelSpace T]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S} {l : Filter ι}
    {μ : ProbabilityMeasure S}
    (h :
      VdVWWeakConvergenceSignedBoundedContinuousArbitraryMap μs X l μ)
    {g : S -> T} (hg : Continuous g) :
    VdVWWeakConvergenceSignedBoundedContinuousArbitraryMap μs
      (fun i ω => g (X i ω)) l (μ.map hg.measurable.aemeasurable) :=
  { weakConvergence := h.weakConvergence.comp_continuous hg
    asymptoticMeasurability := h.asymptoticMeasurability.comp_continuous hg }

/--
The proof-carrying signed bounded-continuous arbitrary-map weak-convergence
package is stable under passing to a finer index filter.
-/
theorem VdVWWeakConvergenceSignedBoundedContinuousArbitraryMap.mono_filter
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S}
    {l l' : Filter ι} {μ : ProbabilityMeasure S}
    (h : VdVWWeakConvergenceSignedBoundedContinuousArbitraryMap μs X l μ)
    (hl : l' ≤ l) :
    VdVWWeakConvergenceSignedBoundedContinuousArbitraryMap μs X l' μ :=
  { weakConvergence := h.weakConvergence.mono_filter hl
    asymptoticMeasurability := h.asymptoticMeasurability.mono_filter hl }

/--
The proof-carrying signed arbitrary-map weak-convergence package is unchanged
by eventually equal measure families and eventually equal arbitrary maps.
-/
theorem VdVWWeakConvergenceSignedBoundedContinuousArbitraryMap.congr_eventually
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S]
    {μs νs : ι -> Measure Ω} {X Y : ι -> Ω -> S}
    {l : Filter ι} {μ : ProbabilityMeasure S}
    (h : VdVWWeakConvergenceSignedBoundedContinuousArbitraryMap μs X l μ)
    (hμ : ∀ᶠ i in l, νs i = μs i)
    (hX : ∀ᶠ i in l, Y i = X i) :
    VdVWWeakConvergenceSignedBoundedContinuousArbitraryMap νs Y l μ :=
  { weakConvergence := h.weakConvergence.congr_eventually hμ hX
    asymptoticMeasurability :=
      h.asymptoticMeasurability.congr_eventually hμ hX }

/--
The proof-carrying signed arbitrary-map weak-convergence package is stable
under reindexing along a map that tends to the original index filter.
-/
theorem VdVWWeakConvergenceSignedBoundedContinuousArbitraryMap.comp_tendsto
    {Ω : Type u} {S : Type v} {ι : Type w} {κ : Type x}
    [MeasurableSpace Ω] [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S}
    {l : Filter ι} {l' : Filter κ} {μ : ProbabilityMeasure S}
    (h : VdVWWeakConvergenceSignedBoundedContinuousArbitraryMap μs X l μ)
    {u : κ -> ι} (hu : Tendsto u l' l) :
    VdVWWeakConvergenceSignedBoundedContinuousArbitraryMap
      (fun k => μs (u k)) (fun k ω => X (u k) ω) l' μ :=
  { weakConvergence := h.weakConvergence.comp_tendsto hu
    asymptoticMeasurability := h.asymptoticMeasurability.comp_tendsto hu }

/--
First-coordinate product lift for signed-outer bounded-continuous weak
convergence.

If the original maps converge in the local signed-outer sense and are
a.e.-measurable, adjoining an ignored probability coordinate preserves the
same convergence target.
-/
theorem VdVWWeakConvergenceSignedOuterBoundedContinuous.prod_fst_of_aemeasurable
    {Ω : Type u} {S : Type v} {T : Type w} {ι : Type x}
    [MeasurableSpace Ω] [MeasurableSpace S]
    [MeasurableSpace T] [TopologicalSpace T] [OpensMeasurableSpace T]
    {μs : ι -> Measure Ω} [∀ i, SFinite (μs i)]
    {ν : Measure S} [SFinite ν] [IsProbabilityMeasure ν]
    {X : ι -> Ω -> T} {l : Filter ι} {μ : ProbabilityMeasure T}
    (h : VdVWWeakConvergenceSignedOuterBoundedContinuous μs X l μ)
    (hX : ∀ i, AEMeasurable (X i) (μs i)) :
    VdVWWeakConvergenceSignedOuterBoundedContinuous
      (fun i => (μs i).prod ν) (fun i z => X i z.1) l μ := by
  intro f
  have houter :
      (fun i =>
        VdVWSignedOuterExpectationPosNeg ((μs i).prod ν)
          (fun z : Ω × S => f (X i z.1))) =
        fun i =>
          VdVWSignedOuterExpectationPosNeg (μs i)
            (fun ω => f (X i ω)) := by
    funext i
    exact
      VdVWSignedOuterExpectationPosNeg_prod_fst_eq_of_aemeasurable
        (ν := ν) (f.continuous.measurable.comp_aemeasurable (hX i))
  simpa [VdVWWeakConvergenceSignedOuterBoundedContinuous, houter] using h f

/--
Second-coordinate product lift for signed-outer bounded-continuous weak
convergence.
-/
theorem VdVWWeakConvergenceSignedOuterBoundedContinuous.prod_snd_of_aemeasurable
    {Ω : Type u} {S : Type v} {T : Type w} {ι : Type x}
    [MeasurableSpace Ω] [MeasurableSpace S]
    [MeasurableSpace T] [TopologicalSpace T] [OpensMeasurableSpace T]
    {ν : Measure Ω} [SFinite ν] [IsProbabilityMeasure ν]
    {μs : ι -> Measure S} [∀ i, SFinite (μs i)]
    {X : ι -> S -> T} {l : Filter ι} {μ : ProbabilityMeasure T}
    (h : VdVWWeakConvergenceSignedOuterBoundedContinuous μs X l μ)
    (hX : ∀ i, AEMeasurable (X i) (μs i)) :
    VdVWWeakConvergenceSignedOuterBoundedContinuous
      (fun i => ν.prod (μs i)) (fun i z => X i z.2) l μ := by
  intro f
  have houter :
      (fun i =>
        VdVWSignedOuterExpectationPosNeg (ν.prod (μs i))
          (fun z : Ω × S => f (X i z.2))) =
        fun i =>
          VdVWSignedOuterExpectationPosNeg (μs i)
            (fun s => f (X i s)) := by
    funext i
    exact
      VdVWSignedOuterExpectationPosNeg_prod_snd_eq_of_aemeasurable
        (μ := ν) (f.continuous.measurable.comp_aemeasurable (hX i))
  simpa [VdVWWeakConvergenceSignedOuterBoundedContinuous, houter] using h f

/--
First-coordinate product lift for the proof-carrying signed arbitrary-map
weak-convergence package.
-/
theorem VdVWWeakConvergenceSignedBoundedContinuousArbitraryMap.prod_fst_of_aemeasurable
    {Ω : Type u} {S : Type v} {T : Type w} {ι : Type x}
    [MeasurableSpace Ω] [MeasurableSpace S]
    [MeasurableSpace T] [TopologicalSpace T] [OpensMeasurableSpace T]
    {μs : ι -> Measure Ω} [∀ i, SFinite (μs i)]
    {ν : Measure S} [SFinite ν] [IsProbabilityMeasure ν]
    {X : ι -> Ω -> T} {l : Filter ι} {μ : ProbabilityMeasure T}
    (h : VdVWWeakConvergenceSignedBoundedContinuousArbitraryMap μs X l μ)
    (hX : ∀ i, AEMeasurable (X i) (μs i)) :
    VdVWWeakConvergenceSignedBoundedContinuousArbitraryMap
      (fun i => (μs i).prod ν) (fun i z => X i z.1) l μ :=
  { weakConvergence := h.weakConvergence.prod_fst_of_aemeasurable hX
    asymptoticMeasurability :=
      VdVWAsymptoticallyMeasurableSignedBoundedContinuous.of_forall_aemeasurable
        (fun i => (hX i).comp_fst) }

/--
Second-coordinate product lift for the proof-carrying signed arbitrary-map
weak-convergence package.
-/
theorem VdVWWeakConvergenceSignedBoundedContinuousArbitraryMap.prod_snd_of_aemeasurable
    {Ω : Type u} {S : Type v} {T : Type w} {ι : Type x}
    [MeasurableSpace Ω] [MeasurableSpace S]
    [MeasurableSpace T] [TopologicalSpace T] [OpensMeasurableSpace T]
    {ν : Measure Ω} [SFinite ν] [IsProbabilityMeasure ν]
    {μs : ι -> Measure S} [∀ i, SFinite (μs i)]
    {X : ι -> S -> T} {l : Filter ι} {μ : ProbabilityMeasure T}
    (h : VdVWWeakConvergenceSignedBoundedContinuousArbitraryMap μs X l μ)
    (hX : ∀ i, AEMeasurable (X i) (μs i)) :
    VdVWWeakConvergenceSignedBoundedContinuousArbitraryMap
      (fun i => ν.prod (μs i)) (fun i z => X i z.2) l μ :=
  { weakConvergence := h.weakConvergence.prod_snd_of_aemeasurable hX
    asymptoticMeasurability :=
      VdVWAsymptoticallyMeasurableSignedBoundedContinuous.of_forall_aemeasurable
        (fun i => (hX i).comp_snd) }

/--
Varying-domain signed-outer bounded-continuous weak convergence.

This is the same signed-outer bounded-continuous test formulation as
`VdVWWeakConvergenceSignedOuterBoundedContinuous`, but with sample spaces
`Ω i` depending on the index.  It is the natural target for Theorem 2.4.3
finite-product endpoints such as `SampleAt Observation n`.
-/
def VdVWWeakConvergenceSignedOuterBoundedContinuousVaryingDomains
    {ι : Type w} (Ω : ι -> Type u) {S : Type v}
    [∀ i, MeasurableSpace (Ω i)]
    [MeasurableSpace S] [TopologicalSpace S] [OpensMeasurableSpace S]
    (μs : (i : ι) -> Measure (Ω i)) (X : (i : ι) -> Ω i -> S)
    (l : Filter ι) (μ : ProbabilityMeasure S) : Prop :=
  ∀ f : S →ᵇ ℝ,
    Tendsto
      (fun i => VdVWSignedOuterExpectationPosNeg (μs i)
        (fun ω => f (X i ω)))
      l (𝓝 (∫ s, f s ∂(μ : Measure S)))

/--
Continuous maps preserve varying-domain signed-outer bounded-continuous weak
convergence.

This is the sample-size-varying analogue of
`VdVWWeakConvergenceSignedOuterBoundedContinuous.comp_continuous`, needed when
Theorem 2.4.3 endpoints are pushed forward by a continuous map.
-/
theorem
    VdVWWeakConvergenceSignedOuterBoundedContinuousVaryingDomains.comp_continuous
    {ι : Type w} {Ω : ι -> Type u} {S : Type v} {T : Type x}
    [∀ i, MeasurableSpace (Ω i)]
    [MeasurableSpace S] [TopologicalSpace S] [OpensMeasurableSpace S]
    [MeasurableSpace T] [TopologicalSpace T] [BorelSpace T]
    {μs : (i : ι) -> Measure (Ω i)} {X : (i : ι) -> Ω i -> S}
    {l : Filter ι} {μ : ProbabilityMeasure S}
    (h :
      VdVWWeakConvergenceSignedOuterBoundedContinuousVaryingDomains
        Ω μs X l μ)
    {g : S -> T} (hg : Continuous g) :
    VdVWWeakConvergenceSignedOuterBoundedContinuousVaryingDomains Ω μs
      (fun i ω => g (X i ω)) l
      (μ.map hg.measurable.aemeasurable) := by
  intro f
  let gC : C(S, T) := ⟨g, hg⟩
  have hbase := h (f.compContinuous gC)
  have htarget :
      (∫ t, f t ∂((μ.map hg.measurable.aemeasurable : ProbabilityMeasure T) :
        Measure T)) =
        ∫ s, f (g s) ∂(μ : Measure S) := by
    simpa [gC] using
      (integral_map hg.measurable.aemeasurable
        f.continuous.measurable.aestronglyMeasurable :
        ∫ t, f t ∂Measure.map g (μ : Measure S) =
          ∫ s, f (g s) ∂(μ : Measure S))
  rw [htarget]
  simpa [VdVWWeakConvergenceSignedOuterBoundedContinuousVaryingDomains, gC]
    using hbase

/--
Varying-domain signed-outer bounded-continuous weak convergence is stable
under passing to a finer index filter.
-/
theorem
    VdVWWeakConvergenceSignedOuterBoundedContinuousVaryingDomains.mono_filter
    {ι : Type w} {Ω : ι -> Type u} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)]
    [MeasurableSpace S] [TopologicalSpace S] [OpensMeasurableSpace S]
    {μs : (i : ι) -> Measure (Ω i)} {X : (i : ι) -> Ω i -> S}
    {l l' : Filter ι} {μ : ProbabilityMeasure S}
    (h :
      VdVWWeakConvergenceSignedOuterBoundedContinuousVaryingDomains
        Ω μs X l μ)
    (hl : l' ≤ l) :
    VdVWWeakConvergenceSignedOuterBoundedContinuousVaryingDomains
      Ω μs X l' μ := by
  intro f
  exact (h f).mono_left hl

/--
Varying-domain signed-outer bounded-continuous weak convergence is unchanged by
eventually equal measure families and eventually equal arbitrary maps.
-/
theorem
    VdVWWeakConvergenceSignedOuterBoundedContinuousVaryingDomains.congr_eventually
    {ι : Type w} {Ω : ι -> Type u} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)]
    [MeasurableSpace S] [TopologicalSpace S] [OpensMeasurableSpace S]
    {μs νs : (i : ι) -> Measure (Ω i)}
    {X Y : (i : ι) -> Ω i -> S}
    {l : Filter ι} {μ : ProbabilityMeasure S}
    (h :
      VdVWWeakConvergenceSignedOuterBoundedContinuousVaryingDomains Ω μs X l μ)
    (hμ : ∀ᶠ i in l, νs i = μs i)
    (hX : ∀ᶠ i in l, Y i = X i) :
    VdVWWeakConvergenceSignedOuterBoundedContinuousVaryingDomains Ω νs Y l μ := by
  intro f
  refine Tendsto.congr' ?_ (h f)
  filter_upwards [hμ, hX] with i hνμ hYX
  simp [hνμ, hYX]

/--
Varying-domain signed-outer bounded-continuous weak convergence is stable
under reindexing along a map that tends to the original index filter.
-/
theorem
    VdVWWeakConvergenceSignedOuterBoundedContinuousVaryingDomains.comp_tendsto
    {ι : Type w} {κ : Type x} {Ω : ι -> Type u} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)]
    [MeasurableSpace S] [TopologicalSpace S] [OpensMeasurableSpace S]
    {μs : (i : ι) -> Measure (Ω i)}
    {X : (i : ι) -> Ω i -> S}
    {l : Filter ι} {l' : Filter κ} {μ : ProbabilityMeasure S}
    (h :
      VdVWWeakConvergenceSignedOuterBoundedContinuousVaryingDomains Ω μs X l μ)
    {u : κ -> ι} (hu : Tendsto u l' l) :
    VdVWWeakConvergenceSignedOuterBoundedContinuousVaryingDomains
      (fun k => Ω (u k)) (fun k => μs (u k))
      (fun k ω => X (u k) ω) l' μ := by
  intro f
  exact (h f).comp hu

/--
Varying-domain signed bounded-continuous asymptotic measurability.
-/
def VdVWAsymptoticallyMeasurableSignedBoundedContinuousVaryingDomains
    {ι : Type w} (Ω : ι -> Type u) {S : Type v}
    [∀ i, MeasurableSpace (Ω i)] [TopologicalSpace S]
    (μs : (i : ι) -> Measure (Ω i)) (X : (i : ι) -> Ω i -> S)
    (l : Filter ι) : Prop :=
  ∀ f : S →ᵇ ℝ,
    Tendsto
      (fun i =>
        VdVWSignedBoundedContinuousOuterInnerExpectationGap (μs i)
          (fun ω => f (X i ω)))
      l (𝓝 0)

/--
Measurable varying-domain maps are signed bounded-continuous asymptotically
measurable.
-/
theorem
    VdVWAsymptoticallyMeasurableSignedBoundedContinuousVaryingDomains.of_forall_measurable
    {ι : Type w} {Ω : ι -> Type u} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)]
    [MeasurableSpace S] [TopologicalSpace S] [OpensMeasurableSpace S]
    {μs : (i : ι) -> Measure (Ω i)} {X : (i : ι) -> Ω i -> S}
    {l : Filter ι}
    (hX : ∀ i, Measurable (X i)) :
    VdVWAsymptoticallyMeasurableSignedBoundedContinuousVaryingDomains
      Ω μs X l := by
  intro f
  have hzero :
      (fun i =>
        VdVWSignedBoundedContinuousOuterInnerExpectationGap (μs i)
          (fun ω => f (X i ω))) = fun _ => 0 := by
    funext i
    exact
      VdVWSignedBoundedContinuousOuterInnerExpectationGap_eq_zero_of_measurable
        (f.continuous.measurable.comp (hX i))
  simpa [hzero] using
    (tendsto_const_nhds :
      Tendsto (fun _ : ι => (0 : ℝ≥0∞)) l (𝓝 0))

/--
Varying-domain null-measurable maps are signed bounded-continuous
asymptotically measurable.
-/
theorem
    VdVWAsymptoticallyMeasurableSignedBoundedContinuousVaryingDomains.of_forall_nullMeasurable
    {ι : Type w} {Ω : ι -> Type u} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)]
    [MeasurableSpace S]
    [TopologicalSpace S] [OpensMeasurableSpace S]
    {μs : (i : ι) -> Measure (Ω i)} {X : (i : ι) -> Ω i -> S}
    {l : Filter ι}
    (hX : ∀ i, NullMeasurable (X i) (μs i)) :
    VdVWAsymptoticallyMeasurableSignedBoundedContinuousVaryingDomains
      Ω μs X l := by
  intro f
  have hzero :
      (fun i =>
        VdVWSignedBoundedContinuousOuterInnerExpectationGap (μs i)
          (fun ω => f (X i ω))) = fun _ => 0 := by
    funext i
    exact
      VdVWSignedBoundedContinuousOuterInnerExpectationGap_eq_zero_of_nullMeasurable
        (f.continuous.measurable.comp_nullMeasurable (hX i))
  simpa [hzero] using
    (tendsto_const_nhds :
      Tendsto (fun _ : ι => (0 : ℝ≥0∞)) l (𝓝 0))

/--
Varying-domain a.e.-measurable maps are signed bounded-continuous
asymptotically measurable.
-/
theorem
    VdVWAsymptoticallyMeasurableSignedBoundedContinuousVaryingDomains.of_forall_aemeasurable
    {ι : Type w} {Ω : ι -> Type u} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)]
    [MeasurableSpace S]
    [TopologicalSpace S] [OpensMeasurableSpace S]
    {μs : (i : ι) -> Measure (Ω i)} {X : (i : ι) -> Ω i -> S}
    {l : Filter ι}
    (hX : ∀ i, AEMeasurable (X i) (μs i)) :
    VdVWAsymptoticallyMeasurableSignedBoundedContinuousVaryingDomains
      Ω μs X l := by
  intro f
  have hzero :
      (fun i =>
        VdVWSignedBoundedContinuousOuterInnerExpectationGap (μs i)
          (fun ω => f (X i ω))) = fun _ => 0 := by
    funext i
    exact
      VdVWSignedBoundedContinuousOuterInnerExpectationGap_eq_zero_of_aemeasurable
        (f.continuous.measurable.comp_aemeasurable (hX i))
  simpa [hzero] using
    (tendsto_const_nhds :
      Tendsto (fun _ : ι => (0 : ℝ≥0∞)) l (𝓝 0))

/--
Continuous maps preserve varying-domain signed bounded-continuous asymptotic
measurability.
-/
theorem
    VdVWAsymptoticallyMeasurableSignedBoundedContinuousVaryingDomains.comp_continuous
    {ι : Type w} {Ω : ι -> Type u} {S : Type v} {T : Type x}
    [∀ i, MeasurableSpace (Ω i)]
    [TopologicalSpace S] [TopologicalSpace T]
    {μs : (i : ι) -> Measure (Ω i)} {X : (i : ι) -> Ω i -> S}
    {l : Filter ι}
    (h :
      VdVWAsymptoticallyMeasurableSignedBoundedContinuousVaryingDomains
        Ω μs X l)
    {g : S -> T} (hg : Continuous g) :
    VdVWAsymptoticallyMeasurableSignedBoundedContinuousVaryingDomains Ω μs
      (fun i ω => g (X i ω)) l := by
  intro f
  let gC : C(S, T) := ⟨g, hg⟩
  simpa [gC] using h (f.compContinuous gC)

/--
Varying-domain signed bounded-continuous asymptotic measurability is stable
under passing to a finer index filter.
-/
theorem
    VdVWAsymptoticallyMeasurableSignedBoundedContinuousVaryingDomains.mono_filter
    {ι : Type w} {Ω : ι -> Type u} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)] [TopologicalSpace S]
    {μs : (i : ι) -> Measure (Ω i)} {X : (i : ι) -> Ω i -> S}
    {l l' : Filter ι}
    (h :
      VdVWAsymptoticallyMeasurableSignedBoundedContinuousVaryingDomains
        Ω μs X l)
    (hl : l' ≤ l) :
    VdVWAsymptoticallyMeasurableSignedBoundedContinuousVaryingDomains
      Ω μs X l' := by
  intro f
  exact (h f).mono_left hl

/--
Varying-domain signed bounded-continuous asymptotic measurability is unchanged
by eventually equal measure families and eventually equal arbitrary maps.
-/
theorem
    VdVWAsymptoticallyMeasurableSignedBoundedContinuousVaryingDomains.congr_eventually
    {ι : Type w} {Ω : ι -> Type u} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)] [TopologicalSpace S]
    {μs νs : (i : ι) -> Measure (Ω i)}
    {X Y : (i : ι) -> Ω i -> S}
    {l : Filter ι}
    (h :
      VdVWAsymptoticallyMeasurableSignedBoundedContinuousVaryingDomains Ω μs X l)
    (hμ : ∀ᶠ i in l, νs i = μs i)
    (hX : ∀ᶠ i in l, Y i = X i) :
    VdVWAsymptoticallyMeasurableSignedBoundedContinuousVaryingDomains Ω νs Y l := by
  intro f
  refine Tendsto.congr' ?_ (h f)
  filter_upwards [hμ, hX] with i hνμ hYX
  simp [hνμ, hYX]

/--
Varying-domain signed bounded-continuous asymptotic measurability is stable
under reindexing along a map that tends to the original index filter.
-/
theorem
    VdVWAsymptoticallyMeasurableSignedBoundedContinuousVaryingDomains.comp_tendsto
    {ι : Type w} {κ : Type x} {Ω : ι -> Type u} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)] [TopologicalSpace S]
    {μs : (i : ι) -> Measure (Ω i)}
    {X : (i : ι) -> Ω i -> S}
    {l : Filter ι} {l' : Filter κ}
    (h :
      VdVWAsymptoticallyMeasurableSignedBoundedContinuousVaryingDomains
        Ω μs X l)
    {u : κ -> ι} (hu : Tendsto u l' l) :
    VdVWAsymptoticallyMeasurableSignedBoundedContinuousVaryingDomains
      (fun k => Ω (u k)) (fun k => μs (u k))
      (fun k ω => X (u k) ω) l' := by
  intro f
  exact (h f).comp hu

/--
Proof-carrying varying-domain signed bounded-continuous weak convergence.

This packages the varying-domain weak-convergence and asymptotic-measurability
fields needed to consume sample-size-varying Theorem 2.4.3 endpoints.
-/
structure VdVWWeakConvergenceSignedBoundedContinuousVaryingDomains
    {ι : Type w} (Ω : ι -> Type u) {S : Type v}
    [∀ i, MeasurableSpace (Ω i)]
    [MeasurableSpace S] [TopologicalSpace S] [OpensMeasurableSpace S]
    (μs : (i : ι) -> Measure (Ω i)) (X : (i : ι) -> Ω i -> S)
    (l : Filter ι) (μ : ProbabilityMeasure S) : Prop where
  weakConvergence :
    VdVWWeakConvergenceSignedOuterBoundedContinuousVaryingDomains Ω μs X l μ
  asymptoticMeasurability :
    VdVWAsymptoticallyMeasurableSignedBoundedContinuousVaryingDomains Ω μs X l

/--
Continuous maps preserve the proof-carrying varying-domain signed
bounded-continuous weak-convergence package.
-/
theorem
    VdVWWeakConvergenceSignedBoundedContinuousVaryingDomains.comp_continuous
    {ι : Type w} {Ω : ι -> Type u} {S : Type v} {T : Type x}
    [∀ i, MeasurableSpace (Ω i)]
    [MeasurableSpace S] [TopologicalSpace S] [OpensMeasurableSpace S]
    [MeasurableSpace T] [TopologicalSpace T] [BorelSpace T]
    {μs : (i : ι) -> Measure (Ω i)} {X : (i : ι) -> Ω i -> S}
    {l : Filter ι} {μ : ProbabilityMeasure S}
    (h :
      VdVWWeakConvergenceSignedBoundedContinuousVaryingDomains Ω μs X l μ)
    {g : S -> T} (hg : Continuous g) :
    VdVWWeakConvergenceSignedBoundedContinuousVaryingDomains Ω μs
      (fun i ω => g (X i ω)) l
      (μ.map hg.measurable.aemeasurable) :=
  { weakConvergence := h.weakConvergence.comp_continuous hg
    asymptoticMeasurability :=
      h.asymptoticMeasurability.comp_continuous hg }

/--
The proof-carrying varying-domain signed bounded-continuous weak-convergence
package is stable under passing to a finer index filter.
-/
theorem
    VdVWWeakConvergenceSignedBoundedContinuousVaryingDomains.mono_filter
    {ι : Type w} {Ω : ι -> Type u} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)]
    [MeasurableSpace S] [TopologicalSpace S] [OpensMeasurableSpace S]
    {μs : (i : ι) -> Measure (Ω i)} {X : (i : ι) -> Ω i -> S}
    {l l' : Filter ι} {μ : ProbabilityMeasure S}
    (h : VdVWWeakConvergenceSignedBoundedContinuousVaryingDomains Ω μs X l μ)
    (hl : l' ≤ l) :
    VdVWWeakConvergenceSignedBoundedContinuousVaryingDomains Ω μs X l' μ :=
  { weakConvergence := h.weakConvergence.mono_filter hl
    asymptoticMeasurability :=
      h.asymptoticMeasurability.mono_filter hl }

/--
The proof-carrying varying-domain signed bounded-continuous weak-convergence
package is unchanged by eventually equal measure families and eventually equal
arbitrary maps.
-/
theorem
    VdVWWeakConvergenceSignedBoundedContinuousVaryingDomains.congr_eventually
    {ι : Type w} {Ω : ι -> Type u} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)]
    [MeasurableSpace S] [TopologicalSpace S] [OpensMeasurableSpace S]
    {μs νs : (i : ι) -> Measure (Ω i)}
    {X Y : (i : ι) -> Ω i -> S}
    {l : Filter ι} {μ : ProbabilityMeasure S}
    (h : VdVWWeakConvergenceSignedBoundedContinuousVaryingDomains Ω μs X l μ)
    (hμ : ∀ᶠ i in l, νs i = μs i)
    (hX : ∀ᶠ i in l, Y i = X i) :
    VdVWWeakConvergenceSignedBoundedContinuousVaryingDomains Ω νs Y l μ :=
  { weakConvergence := h.weakConvergence.congr_eventually hμ hX
    asymptoticMeasurability :=
      h.asymptoticMeasurability.congr_eventually hμ hX }

/--
The proof-carrying varying-domain signed bounded-continuous weak-convergence
package is stable under reindexing along a map that tends to the original
index filter.
-/
theorem
    VdVWWeakConvergenceSignedBoundedContinuousVaryingDomains.comp_tendsto
    {ι : Type w} {κ : Type x} {Ω : ι -> Type u} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)]
    [MeasurableSpace S] [TopologicalSpace S] [OpensMeasurableSpace S]
    {μs : (i : ι) -> Measure (Ω i)}
    {X : (i : ι) -> Ω i -> S}
    {l : Filter ι} {l' : Filter κ} {μ : ProbabilityMeasure S}
    (h : VdVWWeakConvergenceSignedBoundedContinuousVaryingDomains Ω μs X l μ)
    {u : κ -> ι} (hu : Tendsto u l' l) :
    VdVWWeakConvergenceSignedBoundedContinuousVaryingDomains
      (fun k => Ω (u k)) (fun k => μs (u k))
      (fun k ω => X (u k) ω) l' μ :=
  { weakConvergence := h.weakConvergence.comp_tendsto hu
    asymptoticMeasurability := h.asymptoticMeasurability.comp_tendsto hu }

/--
First-coordinate product lift for varying-domain signed-outer
bounded-continuous weak convergence.

This is the sample-size-varying analogue of
`VdVWWeakConvergenceSignedOuterBoundedContinuous.prod_fst_of_aemeasurable`.
-/
theorem
    VdVWWeakConvergenceSignedOuterBoundedContinuousVaryingDomains.prod_fst_of_aemeasurable
    {ι : Type w} {Ω : ι -> Type u} {S : Type v} {T : Type x}
    [∀ i, MeasurableSpace (Ω i)] [MeasurableSpace S]
    [MeasurableSpace T] [TopologicalSpace T] [OpensMeasurableSpace T]
    {μs : (i : ι) -> Measure (Ω i)} [∀ i, SFinite (μs i)]
    {ν : Measure S} [SFinite ν] [IsProbabilityMeasure ν]
    {X : (i : ι) -> Ω i -> T} {l : Filter ι} {μ : ProbabilityMeasure T}
    (h :
      VdVWWeakConvergenceSignedOuterBoundedContinuousVaryingDomains
        Ω μs X l μ)
    (hX : ∀ i, AEMeasurable (X i) (μs i)) :
    VdVWWeakConvergenceSignedOuterBoundedContinuousVaryingDomains
      (fun i => Ω i × S) (fun i => (μs i).prod ν)
      (fun i z => X i z.1) l μ := by
  intro f
  have houter :
      (fun i =>
        VdVWSignedOuterExpectationPosNeg ((μs i).prod ν)
          (fun z : Ω i × S => f (X i z.1))) =
        fun i =>
          VdVWSignedOuterExpectationPosNeg (μs i)
            (fun ω => f (X i ω)) := by
    funext i
    exact
      VdVWSignedOuterExpectationPosNeg_prod_fst_eq_of_aemeasurable
        (ν := ν) (f.continuous.measurable.comp_aemeasurable (hX i))
  simpa [VdVWWeakConvergenceSignedOuterBoundedContinuousVaryingDomains,
    houter] using h f

/--
Second-coordinate product lift for varying-domain signed-outer
bounded-continuous weak convergence.
-/
theorem
    VdVWWeakConvergenceSignedOuterBoundedContinuousVaryingDomains.prod_snd_of_aemeasurable
    {ι : Type w} {Ω : ι -> Type u} {S : Type v} {T : Type x}
    [∀ i, MeasurableSpace (Ω i)] [MeasurableSpace S]
    [MeasurableSpace T] [TopologicalSpace T] [OpensMeasurableSpace T]
    {ν : Measure S} [SFinite ν] [IsProbabilityMeasure ν]
    {μs : (i : ι) -> Measure (Ω i)} [∀ i, SFinite (μs i)]
    {X : (i : ι) -> Ω i -> T} {l : Filter ι} {μ : ProbabilityMeasure T}
    (h :
      VdVWWeakConvergenceSignedOuterBoundedContinuousVaryingDomains
        Ω μs X l μ)
    (hX : ∀ i, AEMeasurable (X i) (μs i)) :
    VdVWWeakConvergenceSignedOuterBoundedContinuousVaryingDomains
      (fun i => S × Ω i) (fun i => ν.prod (μs i))
      (fun i z => X i z.2) l μ := by
  intro f
  have houter :
      (fun i =>
        VdVWSignedOuterExpectationPosNeg (ν.prod (μs i))
          (fun z : S × Ω i => f (X i z.2))) =
        fun i =>
          VdVWSignedOuterExpectationPosNeg (μs i)
            (fun ω => f (X i ω)) := by
    funext i
    exact
      VdVWSignedOuterExpectationPosNeg_prod_snd_eq_of_aemeasurable
        (μ := ν) (f.continuous.measurable.comp_aemeasurable (hX i))
  simpa [VdVWWeakConvergenceSignedOuterBoundedContinuousVaryingDomains,
    houter] using h f

/--
First-coordinate product lift for the proof-carrying varying-domain signed
bounded-continuous weak-convergence package.
-/
theorem
    VdVWWeakConvergenceSignedBoundedContinuousVaryingDomains.prod_fst_of_aemeasurable
    {ι : Type w} {Ω : ι -> Type u} {S : Type v} {T : Type x}
    [∀ i, MeasurableSpace (Ω i)] [MeasurableSpace S]
    [MeasurableSpace T] [TopologicalSpace T] [OpensMeasurableSpace T]
    {μs : (i : ι) -> Measure (Ω i)} [∀ i, SFinite (μs i)]
    {ν : Measure S} [SFinite ν] [IsProbabilityMeasure ν]
    {X : (i : ι) -> Ω i -> T} {l : Filter ι} {μ : ProbabilityMeasure T}
    (h :
      VdVWWeakConvergenceSignedBoundedContinuousVaryingDomains Ω μs X l μ)
    (hX : ∀ i, AEMeasurable (X i) (μs i)) :
    VdVWWeakConvergenceSignedBoundedContinuousVaryingDomains
      (fun i => Ω i × S) (fun i => (μs i).prod ν)
      (fun i z => X i z.1) l μ :=
  { weakConvergence := h.weakConvergence.prod_fst_of_aemeasurable hX
    asymptoticMeasurability :=
      VdVWAsymptoticallyMeasurableSignedBoundedContinuousVaryingDomains.of_forall_aemeasurable
        (Ω := fun i => Ω i × S) (μs := fun i => (μs i).prod ν)
        (X := fun i z => X i z.1) (fun i => (hX i).comp_fst) }

/--
Second-coordinate product lift for the proof-carrying varying-domain signed
bounded-continuous weak-convergence package.
-/
theorem
    VdVWWeakConvergenceSignedBoundedContinuousVaryingDomains.prod_snd_of_aemeasurable
    {ι : Type w} {Ω : ι -> Type u} {S : Type v} {T : Type x}
    [∀ i, MeasurableSpace (Ω i)] [MeasurableSpace S]
    [MeasurableSpace T] [TopologicalSpace T] [OpensMeasurableSpace T]
    {ν : Measure S} [SFinite ν] [IsProbabilityMeasure ν]
    {μs : (i : ι) -> Measure (Ω i)} [∀ i, SFinite (μs i)]
    {X : (i : ι) -> Ω i -> T} {l : Filter ι} {μ : ProbabilityMeasure T}
    (h :
      VdVWWeakConvergenceSignedBoundedContinuousVaryingDomains Ω μs X l μ)
    (hX : ∀ i, AEMeasurable (X i) (μs i)) :
    VdVWWeakConvergenceSignedBoundedContinuousVaryingDomains
      (fun i => S × Ω i) (fun i => ν.prod (μs i))
      (fun i z => X i z.2) l μ :=
  { weakConvergence := h.weakConvergence.prod_snd_of_aemeasurable hX
    asymptoticMeasurability :=
      VdVWAsymptoticallyMeasurableSignedBoundedContinuousVaryingDomains.of_forall_aemeasurable
        (Ω := fun i => S × Ω i) (μs := fun i => ν.prod (μs i))
        (X := fun i z => X i z.2) (fun i => (hX i).comp_snd) }

/--
Nonnegative version of VdV&W asymptotic measurability for a family of
possibly arbitrary maps and a chosen class of nonnegative test functions.

For exact textbook weak convergence this must later be upgraded to the signed
bounded-continuous test-function formulation.  This primitive isolates the
outer/inner expectation-gap mechanism without adding a proof hole.
-/
def VdVWAsymptoticallyMeasurableNonnegative
    {Ω : Type u} {S : Type v} {ι : Type w} [MeasurableSpace Ω]
    (μs : ι -> Measure Ω) (X : ι -> Ω -> S) (l : Filter ι)
    (tests : (S -> ℝ≥0∞) -> Prop) : Prop :=
  ∀ T, tests T ->
    Tendsto
      (fun i => VdVWNonnegativeOuterInnerExpectationGap (μs i)
        (fun ω => T (X i ω)))
      l (𝓝 0)

/--
If every selected nonnegative test composition is measurable, then the
nonnegative VdV&W asymptotic-measurability gap is identically zero.
-/
theorem VdVWAsymptoticallyMeasurableNonnegative.of_forall_measurable_comp
    {Ω : Type u} {S : Type v} {ι : Type w} [MeasurableSpace Ω]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S} {l : Filter ι}
    {tests : (S -> ℝ≥0∞) -> Prop}
    (hmeas : ∀ i T, tests T -> Measurable (fun ω => T (X i ω))) :
    VdVWAsymptoticallyMeasurableNonnegative μs X l tests := by
  intro T hT
  have hzero :
      (fun i => VdVWNonnegativeOuterInnerExpectationGap (μs i)
        (fun ω => T (X i ω))) = fun _ => 0 := by
    funext i
    exact VdVWNonnegativeOuterInnerExpectationGap_eq_zero_of_measurable
      (hmeas i T hT)
  simpa [hzero] using (tendsto_const_nhds : Tendsto (fun _ : ι => (0 : ℝ≥0∞)) l (𝓝 0))

/--
Measurable maps into a measurable state space are nonnegatively
asymptotically measurable for every selected measurable nonnegative test.
-/
theorem VdVWAsymptoticallyMeasurableNonnegative.of_forall_measurable
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [MeasurableSpace S]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S} {l : Filter ι}
    {tests : (S -> ℝ≥0∞) -> Prop}
    (hX : ∀ i, Measurable (X i))
    (hT : ∀ T, tests T -> Measurable T) :
    VdVWAsymptoticallyMeasurableNonnegative μs X l tests :=
  VdVWAsymptoticallyMeasurableNonnegative.of_forall_measurable_comp
    (fun i T htest => (hT T htest).comp (hX i))

/--
The nonnegative asymptotic-measurability predicate is monotone in the selected
test class.
-/
theorem VdVWAsymptoticallyMeasurableNonnegative.mono_tests
    {Ω : Type u} {S : Type v} {ι : Type w} [MeasurableSpace Ω]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S} {l : Filter ι}
    {tests tests' : (S -> ℝ≥0∞) -> Prop}
    (h : VdVWAsymptoticallyMeasurableNonnegative μs X l tests)
    (hsub : ∀ T, tests' T -> tests T) :
    VdVWAsymptoticallyMeasurableNonnegative μs X l tests' := by
  intro T hT
  exact h T (hsub T hT)

/--
Arbitrary-map pullback for the nonnegative asymptotic-measurability predicate.

If every selected target test pulls back to a selected source test, then
asymptotic measurability transfers to the composed maps.
-/
theorem VdVWAsymptoticallyMeasurableNonnegative.comp_map
    {Ω : Type u} {S : Type v} {T : Type w} {ι : Type x}
    [MeasurableSpace Ω]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S} {l : Filter ι}
    {testsS : (S -> ℝ≥0∞) -> Prop} {testsT : (T -> ℝ≥0∞) -> Prop}
    (h : VdVWAsymptoticallyMeasurableNonnegative μs X l testsS)
    {g : S -> T}
    (hpull : ∀ φ, testsT φ -> testsS (fun s => φ (g s))) :
    VdVWAsymptoticallyMeasurableNonnegative
      μs (fun i ω => g (X i ω)) l testsT := by
  intro φ hφ
  exact h (fun s => φ (g s)) (hpull φ hφ)

/--
The nonnegative asymptotic-measurability predicate is stable under passing to
a finer index filter, e.g. a subsequence filter.
-/
theorem VdVWAsymptoticallyMeasurableNonnegative.mono_filter
    {Ω : Type u} {S : Type v} {ι : Type w} [MeasurableSpace Ω]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S}
    {l l' : Filter ι} {tests : (S -> ℝ≥0∞) -> Prop}
    (h : VdVWAsymptoticallyMeasurableNonnegative μs X l tests)
    (hl : l' ≤ l) :
    VdVWAsymptoticallyMeasurableNonnegative μs X l' tests := by
  intro T hT
  exact (h T hT).mono_left hl

/--
The nonnegative asymptotic-measurability predicate is unchanged by eventually
equal measure families and eventually equal arbitrary maps.
-/
theorem VdVWAsymptoticallyMeasurableNonnegative.congr_eventually
    {Ω : Type u} {S : Type v} {ι : Type w} [MeasurableSpace Ω]
    {μs νs : ι -> Measure Ω} {X Y : ι -> Ω -> S}
    {l : Filter ι} {tests : (S -> ℝ≥0∞) -> Prop}
    (h : VdVWAsymptoticallyMeasurableNonnegative μs X l tests)
    (hμ : ∀ᶠ i in l, νs i = μs i)
    (hX : ∀ᶠ i in l, Y i = X i) :
    VdVWAsymptoticallyMeasurableNonnegative νs Y l tests := by
  intro T hT
  refine Tendsto.congr' ?_ (h T hT)
  filter_upwards [hμ, hX] with i hνμ hYX
  simp [hνμ, hYX]

/--
The nonnegative asymptotic-measurability predicate is stable under reindexing
along a map that tends to the original index filter.
-/
theorem VdVWAsymptoticallyMeasurableNonnegative.comp_tendsto
    {Ω : Type u} {S : Type v} {ι : Type w} {κ : Type x} [MeasurableSpace Ω]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S}
    {l : Filter ι} {l' : Filter κ} {tests : (S -> ℝ≥0∞) -> Prop}
    (h : VdVWAsymptoticallyMeasurableNonnegative μs X l tests)
    {u : κ -> ι} (hu : Tendsto u l' l) :
    VdVWAsymptoticallyMeasurableNonnegative
      (fun k => μs (u k)) (fun k ω => X (u k) ω) l' tests := by
  intro T hT
  exact (h T hT).comp hu

/--
Lower-shifted real outer/inner expectation gap.

For a real-valued test `Y` with lower bound `c`, `ENNReal.ofReal (Y - c)` is
the nonnegative proxy used by the local outer/inner expectation layer.  The
lower-bound hypothesis is carried by the higher-level predicates; the gap
itself is defined for every shift.
-/
noncomputable def VdVWLowerShiftedRealOuterInnerExpectationGap
    {Ω : Type u} [MeasurableSpace Ω] (μ : Measure Ω)
    (Y : Ω -> ℝ) (c : ℝ) : ℝ≥0∞ :=
  VdVWNonnegativeOuterInnerExpectationGap μ
    (fun ω => ENNReal.ofReal (Y ω - c))

/--
The lower-shifted real outer/inner expectation gap vanishes exactly when the
outer and inner expectations of its nonnegative shifted proxy coincide.
-/
theorem VdVWLowerShiftedRealOuterInnerExpectationGap_eq_zero_iff
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {Y : Ω -> ℝ} {c : ℝ} :
    VdVWLowerShiftedRealOuterInnerExpectationGap μ Y c = 0 ↔
      VdVWOuterExpectation μ (fun ω => ENNReal.ofReal (Y ω - c)) =
        VdVWInnerExpectation μ (fun ω => ENNReal.ofReal (Y ω - c)) := by
  simp [VdVWLowerShiftedRealOuterInnerExpectationGap,
    VdVWNonnegativeOuterInnerExpectationGap_eq_zero_iff_outer_eq_inner]

/--
Measurable real-valued maps have zero lower-shifted VdV&W nonnegative
outer/inner expectation gap.
-/
theorem VdVWLowerShiftedRealOuterInnerExpectationGap_eq_zero_of_measurable
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {Y : Ω -> ℝ} {c : ℝ} (hY : Measurable Y) :
    VdVWLowerShiftedRealOuterInnerExpectationGap μ Y c = 0 := by
  unfold VdVWLowerShiftedRealOuterInnerExpectationGap
  exact
    VdVWNonnegativeOuterInnerExpectationGap_eq_zero_of_measurable
      ((hY.sub measurable_const).ennreal_ofReal)

/--
Lower-shifted real-test version of VdV&W asymptotic measurability.

The predicate quantifies over selected real tests and every supplied lower
shift along the process.  This is still a local bridge, not the full signed
outer-expectation definition from the textbook.
-/
def VdVWAsymptoticallyMeasurableLowerShiftedReal
    {Ω : Type u} {S : Type v} {ι : Type w} [MeasurableSpace Ω]
    (μs : ι -> Measure Ω) (X : ι -> Ω -> S) (l : Filter ι)
    (tests : (S -> ℝ) -> Prop) : Prop :=
  ∀ f c, tests f -> (∀ i ω, c ≤ f (X i ω)) ->
    Tendsto
      (fun i => VdVWLowerShiftedRealOuterInnerExpectationGap (μs i)
        (fun ω => f (X i ω)) c)
      l (𝓝 0)

/--
If every selected real test composition is measurable, then the lower-shifted
real VdV&W asymptotic-measurability gap is identically zero.
-/
theorem VdVWAsymptoticallyMeasurableLowerShiftedReal.of_forall_measurable_comp
    {Ω : Type u} {S : Type v} {ι : Type w} [MeasurableSpace Ω]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S} {l : Filter ι}
    {tests : (S -> ℝ) -> Prop}
    (hmeas : ∀ i f, tests f -> Measurable (fun ω => f (X i ω))) :
    VdVWAsymptoticallyMeasurableLowerShiftedReal μs X l tests := by
  intro f c hf _hlower
  have hzero :
      (fun i => VdVWLowerShiftedRealOuterInnerExpectationGap (μs i)
        (fun ω => f (X i ω)) c) = fun _ => 0 := by
    funext i
    exact VdVWLowerShiftedRealOuterInnerExpectationGap_eq_zero_of_measurable
      (hmeas i f hf)
  simpa [hzero] using (tendsto_const_nhds : Tendsto (fun _ : ι => (0 : ℝ≥0∞)) l (𝓝 0))

/--
Measurable maps into a measurable state space are lower-shifted real
asymptotically measurable for every selected measurable real test.
-/
theorem VdVWAsymptoticallyMeasurableLowerShiftedReal.of_forall_measurable
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [MeasurableSpace S]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S} {l : Filter ι}
    {tests : (S -> ℝ) -> Prop}
    (hX : ∀ i, Measurable (X i))
    (hT : ∀ T, tests T -> Measurable T) :
    VdVWAsymptoticallyMeasurableLowerShiftedReal μs X l tests :=
  VdVWAsymptoticallyMeasurableLowerShiftedReal.of_forall_measurable_comp
    (fun i T htest => (hT T htest).comp (hX i))

/--
The lower-shifted real asymptotic-measurability predicate is monotone in the
selected real test class.
-/
theorem VdVWAsymptoticallyMeasurableLowerShiftedReal.mono_tests
    {Ω : Type u} {S : Type v} {ι : Type w} [MeasurableSpace Ω]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S} {l : Filter ι}
    {tests tests' : (S -> ℝ) -> Prop}
    (h : VdVWAsymptoticallyMeasurableLowerShiftedReal μs X l tests)
    (hsub : ∀ f, tests' f -> tests f) :
    VdVWAsymptoticallyMeasurableLowerShiftedReal μs X l tests' := by
  intro f c hf hlower
  exact h f c (hsub f hf) hlower

/--
Arbitrary-map pullback for the lower-shifted real
asymptotic-measurability predicate.
-/
theorem VdVWAsymptoticallyMeasurableLowerShiftedReal.comp_map
    {Ω : Type u} {S : Type v} {T : Type w} {ι : Type x}
    [MeasurableSpace Ω]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S} {l : Filter ι}
    {testsS : (S -> ℝ) -> Prop} {testsT : (T -> ℝ) -> Prop}
    (h : VdVWAsymptoticallyMeasurableLowerShiftedReal μs X l testsS)
    {g : S -> T}
    (hpull : ∀ φ, testsT φ -> testsS (fun s => φ (g s))) :
    VdVWAsymptoticallyMeasurableLowerShiftedReal
      μs (fun i ω => g (X i ω)) l testsT := by
  intro φ c hφ hlower
  exact h (fun s => φ (g s)) c (hpull φ hφ) hlower

/--
The lower-shifted real asymptotic-measurability predicate is stable under
passing to a finer index filter, e.g. a subsequence filter.
-/
theorem VdVWAsymptoticallyMeasurableLowerShiftedReal.mono_filter
    {Ω : Type u} {S : Type v} {ι : Type w} [MeasurableSpace Ω]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S}
    {l l' : Filter ι} {tests : (S -> ℝ) -> Prop}
    (h : VdVWAsymptoticallyMeasurableLowerShiftedReal μs X l tests)
    (hl : l' ≤ l) :
    VdVWAsymptoticallyMeasurableLowerShiftedReal μs X l' tests := by
  intro f c hf hlower
  exact (h f c hf hlower).mono_left hl

/--
The lower-shifted real asymptotic-measurability predicate is unchanged by
eventually equal measure families and pointwise equal arbitrary maps.

The map equality is pointwise because the lower-bound side condition is
global in the index.
-/
theorem VdVWAsymptoticallyMeasurableLowerShiftedReal.congr_eventually
    {Ω : Type u} {S : Type v} {ι : Type w} [MeasurableSpace Ω]
    {μs νs : ι -> Measure Ω} {X Y : ι -> Ω -> S}
    {l : Filter ι} {tests : (S -> ℝ) -> Prop}
    (h : VdVWAsymptoticallyMeasurableLowerShiftedReal μs X l tests)
    (hμ : ∀ᶠ i in l, νs i = μs i)
    (hX : ∀ i, Y i = X i) :
    VdVWAsymptoticallyMeasurableLowerShiftedReal νs Y l tests := by
  intro f c hf hlower
  refine Tendsto.congr' ?_ (h f c hf ?_)
  · filter_upwards [hμ] with i hνμ
    simp [hνμ, hX i]
  · intro i ω
    simpa [← hX i] using hlower i ω

/--
Reindexing for the lower-shifted real asymptotic-measurability predicate when
the all-index lower-bound side condition can be lifted back from the reindexed
subfamily.

The extra hypothesis is necessary: the target predicate only supplies a lower
bound along the reindexed family, while the source predicate requires one for
all original indices.
-/
theorem VdVWAsymptoticallyMeasurableLowerShiftedReal.comp_tendsto_of_lower_bound
    {Ω : Type u} {S : Type v} {ι : Type w} {κ : Type x}
    [MeasurableSpace Ω]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S}
    {l : Filter ι} {l' : Filter κ} {tests : (S -> ℝ) -> Prop}
    (h : VdVWAsymptoticallyMeasurableLowerShiftedReal μs X l tests)
    {u : κ -> ι} (hu : Tendsto u l' l)
    (hlift :
      ∀ f c, tests f ->
        (∀ k ω, c ≤ f (X (u k) ω)) -> ∀ i ω, c ≤ f (X i ω)) :
    VdVWAsymptoticallyMeasurableLowerShiftedReal
      (fun k => μs (u k)) (fun k ω => X (u k) ω) l' tests := by
  intro f c hf hlower
  exact (h f c hf (hlift f c hf hlower)).comp hu

/--
Bounded-continuous lower-shifted asymptotic measurability.

This is the closest current local bridge to VdV&W Definition 1.3.7: it ranges
over bounded continuous real tests, but uses the nonnegative shifted
outer/inner expectation gap until the full signed outer expectation is
formalized.
-/
def VdVWAsymptoticallyMeasurableBoundedContinuousLowerShifted
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [TopologicalSpace S] (μs : ι -> Measure Ω)
    (X : ι -> Ω -> S) (l : Filter ι) : Prop :=
  ∀ f : S →ᵇ ℝ, ∀ c,
    (∀ i ω, c ≤ f (X i ω)) ->
      Tendsto
        (fun i => VdVWLowerShiftedRealOuterInnerExpectationGap (μs i)
          (fun ω => f (X i ω)) c)
        l (𝓝 0)

/--
Measurable maps into a topological measurable state space are lower-shifted
asymptotically measurable for all bounded continuous real tests.
-/
theorem VdVWAsymptoticallyMeasurableBoundedContinuousLowerShifted.of_forall_measurable
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S} {l : Filter ι}
    (hX : ∀ i, Measurable (X i)) :
    VdVWAsymptoticallyMeasurableBoundedContinuousLowerShifted μs X l := by
  intro f c _hlower
  have hzero :
      (fun i => VdVWLowerShiftedRealOuterInnerExpectationGap (μs i)
        (fun ω => f (X i ω)) c) = fun _ => 0 := by
    funext i
    exact VdVWLowerShiftedRealOuterInnerExpectationGap_eq_zero_of_measurable
      (f.continuous.measurable.comp (hX i))
  simpa [hzero] using (tendsto_const_nhds : Tendsto (fun _ : ι => (0 : ℝ≥0∞)) l (𝓝 0))

/--
Continuous maps preserve the lower-shifted bounded-continuous
asymptotic-measurability layer.

This is the local arbitrary-map analogue of the continuous-mapping theorem for
the current shifted outer/inner expectation primitive: every bounded
continuous test on the target pulls back to a bounded continuous test on the
source.
-/
theorem VdVWAsymptoticallyMeasurableBoundedContinuousLowerShifted.comp_continuous
    {Ω : Type u} {S : Type v} {T : Type w} {ι : Type x}
    [MeasurableSpace Ω] [TopologicalSpace S] [TopologicalSpace T]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S} {l : Filter ι}
    (h : VdVWAsymptoticallyMeasurableBoundedContinuousLowerShifted μs X l)
    {g : S -> T} (hg : Continuous g) :
    VdVWAsymptoticallyMeasurableBoundedContinuousLowerShifted
      μs (fun i ω => g (X i ω)) l := by
  intro f c hlower
  let gC : C(S, T) := ⟨g, hg⟩
  simpa [gC] using h (f.compContinuous gC) c hlower

/--
The bounded-continuous lower-shifted asymptotic-measurability predicate is
stable under passing to a finer index filter.
-/
theorem VdVWAsymptoticallyMeasurableBoundedContinuousLowerShifted.mono_filter
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [TopologicalSpace S]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S}
    {l l' : Filter ι}
    (h : VdVWAsymptoticallyMeasurableBoundedContinuousLowerShifted μs X l)
    (hl : l' ≤ l) :
    VdVWAsymptoticallyMeasurableBoundedContinuousLowerShifted μs X l' := by
  intro f c hlower
  exact (h f c hlower).mono_left hl

/--
The bounded-continuous lower-shifted asymptotic-measurability predicate is
unchanged by eventually equal measure families and pointwise equal arbitrary
maps.

The map equality is kept pointwise, not merely eventual, because the
lower-shifted predicate carries an all-index lower-bound hypothesis.
-/
theorem VdVWAsymptoticallyMeasurableBoundedContinuousLowerShifted.congr_eventually
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [TopologicalSpace S]
    {μs νs : ι -> Measure Ω} {X Y : ι -> Ω -> S}
    {l : Filter ι}
    (h : VdVWAsymptoticallyMeasurableBoundedContinuousLowerShifted μs X l)
    (hμ : ∀ᶠ i in l, νs i = μs i)
    (hX : ∀ i, Y i = X i) :
    VdVWAsymptoticallyMeasurableBoundedContinuousLowerShifted νs Y l := by
  intro f c hlower
  refine Tendsto.congr' ?_ (h f c ?_)
  · filter_upwards [hμ] with i hνμ
    simp [hνμ, hX i]
  · intro i ω
    simpa [← hX i] using hlower i ω

/--
Reindexing for the bounded-continuous lower-shifted asymptotic-measurability
predicate when lower bounds along the reindexed subfamily lift to all original
indices.
-/
theorem
    VdVWAsymptoticallyMeasurableBoundedContinuousLowerShifted.comp_tendsto_of_lower_bound
    {Ω : Type u} {S : Type v} {ι : Type w} {κ : Type x}
    [MeasurableSpace Ω] [TopologicalSpace S]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S}
    {l : Filter ι} {l' : Filter κ}
    (h : VdVWAsymptoticallyMeasurableBoundedContinuousLowerShifted μs X l)
    {u : κ -> ι} (hu : Tendsto u l' l)
    (hlift :
      ∀ (f : S →ᵇ ℝ) c,
        (∀ k ω, c ≤ f (X (u k) ω)) -> ∀ i ω, c ≤ f (X i ω)) :
    VdVWAsymptoticallyMeasurableBoundedContinuousLowerShifted
      (fun k => μs (u k)) (fun k ω => X (u k) ω) l' := by
  intro f c hlower
  exact (h f c (hlift f c hlower)).comp hu

/--
Bounded-continuous asymptotic measurability with the canonical lower shift
`-‖f‖`.

This removes the explicit lower-bound argument from the local
bounded-continuous layer.  The shift is valid for every bounded continuous
real-valued test by `BoundedContinuousFunction.neg_norm_le_apply`.
-/
def VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShifted
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [TopologicalSpace S] (μs : ι -> Measure Ω)
    (X : ι -> Ω -> S) (l : Filter ι) : Prop :=
  ∀ f : S →ᵇ ℝ,
    Tendsto
      (fun i => VdVWLowerShiftedRealOuterInnerExpectationGap (μs i)
        (fun ω => f (X i ω)) (-‖f‖))
      l (𝓝 0)

/--
The explicit lower-shifted bounded-continuous layer implies the canonical
`-‖f‖` version.
-/
theorem VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShifted.of_lowerShifted
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [TopologicalSpace S]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S} {l : Filter ι}
    (h :
      VdVWAsymptoticallyMeasurableBoundedContinuousLowerShifted μs X l) :
    VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShifted μs X l := by
  intro f
  exact h f (-‖f‖) fun i ω =>
    BoundedContinuousFunction.neg_norm_le_apply f (X i ω)

/--
Measurable maps into a topological measurable state space are canonically
lower-shifted asymptotically measurable for all bounded continuous real tests.
-/
theorem VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShifted.of_forall_measurable
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S} {l : Filter ι}
    (hX : ∀ i, Measurable (X i)) :
    VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShifted μs X l :=
  VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShifted.of_lowerShifted
    (VdVWAsymptoticallyMeasurableBoundedContinuousLowerShifted.of_forall_measurable
      hX)

/--
Continuous maps preserve the canonical bounded-continuous shifted
asymptotic-measurability predicate whenever the source has the stronger
all-lower-shifts version.
-/
theorem
    VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShifted.comp_continuous_of_lowerShifted
    {Ω : Type u} {S : Type v} {T : Type w} {ι : Type x}
    [MeasurableSpace Ω] [TopologicalSpace S] [TopologicalSpace T]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S} {l : Filter ι}
    (h : VdVWAsymptoticallyMeasurableBoundedContinuousLowerShifted μs X l)
    {g : S -> T} (hg : Continuous g) :
    VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShifted
      μs (fun i ω => g (X i ω)) l :=
  VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShifted.of_lowerShifted
    (h.comp_continuous hg)

/--
The canonical bounded-continuous shifted asymptotic-measurability predicate is
stable under passing to a finer index filter.
-/
theorem VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShifted.mono_filter
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [TopologicalSpace S]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S}
    {l l' : Filter ι}
    (h : VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShifted μs X l)
    (hl : l' ≤ l) :
    VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShifted μs X l' := by
  intro f
  exact (h f).mono_left hl

/--
The canonical bounded-continuous shifted asymptotic-measurability predicate is
unchanged by eventually equal measure families and eventually equal arbitrary
maps.
-/
theorem VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShifted.congr_eventually
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [TopologicalSpace S]
    {μs νs : ι -> Measure Ω} {X Y : ι -> Ω -> S}
    {l : Filter ι}
    (h : VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShifted μs X l)
    (hμ : ∀ᶠ i in l, νs i = μs i)
    (hX : ∀ᶠ i in l, Y i = X i) :
    VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShifted νs Y l := by
  intro f
  refine Tendsto.congr' ?_ (h f)
  filter_upwards [hμ, hX] with i hνμ hYX
  simp [hνμ, hYX]

/--
The canonical bounded-continuous shifted asymptotic-measurability predicate is
stable under reindexing along a map that tends to the original index filter.
-/
theorem VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShifted.comp_tendsto
    {Ω : Type u} {S : Type v} {ι : Type w} {κ : Type x}
    [MeasurableSpace Ω] [TopologicalSpace S]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S}
    {l : Filter ι} {l' : Filter κ}
    (h : VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShifted μs X l)
    {u : κ -> ι} (hu : Tendsto u l' l) :
    VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShifted
      (fun k => μs (u k)) (fun k ω => X (u k) ω) l' := by
  intro f
  exact (h f).comp hu

/--
The lower-shifted nonnegative gap is one half of the signed
positive/negative gap after subtracting the lower shift.
-/
theorem VdVWLowerShiftedRealOuterInnerExpectationGap_le_signed_sub_const
    {Ω : Type u} [MeasurableSpace Ω] {μ : Measure Ω}
    {Y : Ω -> ℝ} {c : ℝ} :
    VdVWLowerShiftedRealOuterInnerExpectationGap μ Y c ≤
      VdVWSignedBoundedContinuousOuterInnerExpectationGap μ
        (fun ω => Y ω - c) := by
  simp [VdVWLowerShiftedRealOuterInnerExpectationGap,
    VdVWSignedBoundedContinuousOuterInnerExpectationGap]

/--
Signed bounded-continuous asymptotic measurability implies the older
lower-shifted bounded-continuous layer.

This connects the current signed Chapter 1 arbitrary-map predicate back to the
previous nonnegative shifted predicate without adding a new primitive
assumption.
-/
theorem VdVWAsymptoticallyMeasurableSignedBoundedContinuous.to_lowerShifted
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [TopologicalSpace S]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S} {l : Filter ι}
    (h : VdVWAsymptoticallyMeasurableSignedBoundedContinuous μs X l) :
    VdVWAsymptoticallyMeasurableBoundedContinuousLowerShifted μs X l := by
  intro f c _hlower
  let fc : S →ᵇ ℝ := f - BoundedContinuousFunction.const S c
  have hsigned := h fc
  refine
    tendsto_of_tendsto_of_tendsto_of_le_of_le'
      (show Tendsto (fun _ : ι => (0 : ℝ≥0∞)) l (𝓝 0) from
        tendsto_const_nhds)
      hsigned
      (Eventually.of_forall fun _ => bot_le)
      ?_
  refine Eventually.of_forall fun i => ?_
  simpa [fc] using
    (VdVWLowerShiftedRealOuterInnerExpectationGap_le_signed_sub_const
      (μ := μs i) (Y := fun ω => f (X i ω)) (c := c))

/--
Signed bounded-continuous asymptotic measurability implies the canonical
`-‖f‖` shifted layer.
-/
theorem VdVWAsymptoticallyMeasurableSignedBoundedContinuous.to_canonicalShifted
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [TopologicalSpace S]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S} {l : Filter ι}
    (h : VdVWAsymptoticallyMeasurableSignedBoundedContinuous μs X l) :
    VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShifted μs X l :=
  VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShifted.of_lowerShifted
    h.to_lowerShifted

/--
Null-measurable maps are lower-shifted asymptotically measurable for all
bounded continuous real tests.
-/
theorem VdVWAsymptoticallyMeasurableBoundedContinuousLowerShifted.of_forall_nullMeasurable
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [MeasurableSpace S]
    [TopologicalSpace S] [OpensMeasurableSpace S]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S} {l : Filter ι}
    (hX : ∀ i, NullMeasurable (X i) (μs i)) :
    VdVWAsymptoticallyMeasurableBoundedContinuousLowerShifted μs X l :=
  (VdVWAsymptoticallyMeasurableSignedBoundedContinuous.of_forall_nullMeasurable
    hX).to_lowerShifted

/--
A.e.-measurable maps are lower-shifted asymptotically measurable for all
bounded continuous real tests.
-/
theorem VdVWAsymptoticallyMeasurableBoundedContinuousLowerShifted.of_forall_aemeasurable
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [MeasurableSpace S]
    [TopologicalSpace S] [OpensMeasurableSpace S]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S} {l : Filter ι}
    (hX : ∀ i, AEMeasurable (X i) (μs i)) :
    VdVWAsymptoticallyMeasurableBoundedContinuousLowerShifted μs X l :=
  (VdVWAsymptoticallyMeasurableSignedBoundedContinuous.of_forall_aemeasurable
    hX).to_lowerShifted

/--
Null-measurable maps are canonically shifted asymptotically measurable for all
bounded continuous real tests.
-/
theorem VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShifted.of_forall_nullMeasurable
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [MeasurableSpace S]
    [TopologicalSpace S] [OpensMeasurableSpace S]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S} {l : Filter ι}
    (hX : ∀ i, NullMeasurable (X i) (μs i)) :
    VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShifted μs X l :=
  (VdVWAsymptoticallyMeasurableSignedBoundedContinuous.of_forall_nullMeasurable
    hX).to_canonicalShifted

/--
A.e.-measurable maps are canonically shifted asymptotically measurable for all
bounded continuous real tests.
-/
theorem VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShifted.of_forall_aemeasurable
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [MeasurableSpace S]
    [TopologicalSpace S] [OpensMeasurableSpace S]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S} {l : Filter ι}
    (hX : ∀ i, AEMeasurable (X i) (μs i)) :
    VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShifted μs X l :=
  (VdVWAsymptoticallyMeasurableSignedBoundedContinuous.of_forall_aemeasurable
    hX).to_canonicalShifted

/--
Varying-domain bounded-continuous lower-shifted asymptotic measurability.

This is the sample-size-varying analogue of
`VdVWAsymptoticallyMeasurableBoundedContinuousLowerShifted`, used for
empirical-process endpoints over spaces such as `SampleAt Observation n`.
-/
def VdVWAsymptoticallyMeasurableBoundedContinuousLowerShiftedVaryingDomains
    {ι : Type w} (Ω : ι -> Type u) {S : Type v}
    [∀ i, MeasurableSpace (Ω i)] [TopologicalSpace S]
    (μs : (i : ι) -> Measure (Ω i)) (X : (i : ι) -> Ω i -> S)
    (l : Filter ι) : Prop :=
  ∀ f : S →ᵇ ℝ, ∀ c,
    (∀ i ω, c ≤ f (X i ω)) ->
      Tendsto
        (fun i => VdVWLowerShiftedRealOuterInnerExpectationGap (μs i)
          (fun ω => f (X i ω)) c)
        l (𝓝 0)

/--
Varying-domain bounded-continuous asymptotic measurability with the canonical
lower shift `-‖f‖`.
-/
def VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShiftedVaryingDomains
    {ι : Type w} (Ω : ι -> Type u) {S : Type v}
    [∀ i, MeasurableSpace (Ω i)] [TopologicalSpace S]
    (μs : (i : ι) -> Measure (Ω i)) (X : (i : ι) -> Ω i -> S)
    (l : Filter ι) : Prop :=
  ∀ f : S →ᵇ ℝ,
    Tendsto
      (fun i => VdVWLowerShiftedRealOuterInnerExpectationGap (μs i)
        (fun ω => f (X i ω)) (-‖f‖))
      l (𝓝 0)

/--
The varying-domain explicit lower-shifted layer implies the canonical
`-‖f‖` version.
-/
theorem
    VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShiftedVaryingDomains.of_lowerShifted
    {ι : Type w} {Ω : ι -> Type u} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)] [TopologicalSpace S]
    {μs : (i : ι) -> Measure (Ω i)} {X : (i : ι) -> Ω i -> S}
    {l : Filter ι}
    (h :
      VdVWAsymptoticallyMeasurableBoundedContinuousLowerShiftedVaryingDomains
        Ω μs X l) :
    VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShiftedVaryingDomains
      Ω μs X l := by
  intro f
  exact h f (-‖f‖) fun i ω =>
    BoundedContinuousFunction.neg_norm_le_apply f (X i ω)

/--
Continuous maps preserve varying-domain lower-shifted bounded-continuous
asymptotic measurability.

This is the sample-size-varying analogue of
`VdVWAsymptoticallyMeasurableBoundedContinuousLowerShifted.comp_continuous`.
-/
theorem
    VdVWAsymptoticallyMeasurableBoundedContinuousLowerShiftedVaryingDomains.comp_continuous
    {ι : Type w} {Ω : ι -> Type u} {S : Type v} {T : Type x}
    [∀ i, MeasurableSpace (Ω i)] [TopologicalSpace S] [TopologicalSpace T]
    {μs : (i : ι) -> Measure (Ω i)} {X : (i : ι) -> Ω i -> S}
    {l : Filter ι}
    (h :
      VdVWAsymptoticallyMeasurableBoundedContinuousLowerShiftedVaryingDomains
        Ω μs X l)
    {g : S -> T} (hg : Continuous g) :
    VdVWAsymptoticallyMeasurableBoundedContinuousLowerShiftedVaryingDomains
      Ω μs (fun i ω => g (X i ω)) l := by
  intro f c hlower
  let gC : C(S, T) := ⟨g, hg⟩
  simpa [gC] using h (f.compContinuous gC) c hlower

/--
Continuous maps preserve the varying-domain canonical shifted predicate when
the source has the stronger all-lower-shifts version.
-/
theorem
    VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShiftedVaryingDomains.comp_continuous_of_lowerShifted
    {ι : Type w} {Ω : ι -> Type u} {S : Type v} {T : Type x}
    [∀ i, MeasurableSpace (Ω i)] [TopologicalSpace S] [TopologicalSpace T]
    {μs : (i : ι) -> Measure (Ω i)} {X : (i : ι) -> Ω i -> S}
    {l : Filter ι}
    (h :
      VdVWAsymptoticallyMeasurableBoundedContinuousLowerShiftedVaryingDomains
        Ω μs X l)
    {g : S -> T} (hg : Continuous g) :
    VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShiftedVaryingDomains
      Ω μs (fun i ω => g (X i ω)) l :=
  VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShiftedVaryingDomains.of_lowerShifted
    (h.comp_continuous hg)

/--
The varying-domain lower-shifted predicate is stable under passing to a finer
index filter.
-/
theorem
    VdVWAsymptoticallyMeasurableBoundedContinuousLowerShiftedVaryingDomains.mono_filter
    {ι : Type w} {Ω : ι -> Type u} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)] [TopologicalSpace S]
    {μs : (i : ι) -> Measure (Ω i)} {X : (i : ι) -> Ω i -> S}
    {l l' : Filter ι}
    (h :
      VdVWAsymptoticallyMeasurableBoundedContinuousLowerShiftedVaryingDomains
        Ω μs X l)
    (hl : l' ≤ l) :
    VdVWAsymptoticallyMeasurableBoundedContinuousLowerShiftedVaryingDomains
      Ω μs X l' := by
  intro f c hlower
  exact (h f c hlower).mono_left hl

/--
The varying-domain lower-shifted bounded-continuous asymptotic-measurability
predicate is unchanged by eventually equal measure families and pointwise equal
arbitrary maps.

The map equality is kept pointwise, not merely eventual, because the
lower-shifted predicate carries an all-index lower-bound hypothesis.
-/
theorem
    VdVWAsymptoticallyMeasurableBoundedContinuousLowerShiftedVaryingDomains.congr_eventually
    {ι : Type w} {Ω : ι -> Type u} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)] [TopologicalSpace S]
    {μs νs : (i : ι) -> Measure (Ω i)}
    {X Y : (i : ι) -> Ω i -> S}
    {l : Filter ι}
    (h :
      VdVWAsymptoticallyMeasurableBoundedContinuousLowerShiftedVaryingDomains
        Ω μs X l)
    (hμ : ∀ᶠ i in l, νs i = μs i)
    (hX : ∀ i, Y i = X i) :
    VdVWAsymptoticallyMeasurableBoundedContinuousLowerShiftedVaryingDomains
      Ω νs Y l := by
  intro f c hlower
  refine Tendsto.congr' ?_ (h f c ?_)
  · filter_upwards [hμ] with i hνμ
    simp [hνμ, hX i]
  · intro i ω
    simpa [← hX i] using hlower i ω

/--
Reindexing for the varying-domain lower-shifted bounded-continuous
asymptotic-measurability predicate when the reindexed lower-bound side
condition can be lifted to all original domains.
-/
theorem
    VdVWAsymptoticallyMeasurableBoundedContinuousLowerShiftedVaryingDomains.comp_tendsto_of_lower_bound
    {ι : Type w} {κ : Type x} {Ω : ι -> Type u} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)] [TopologicalSpace S]
    {μs : (i : ι) -> Measure (Ω i)}
    {X : (i : ι) -> Ω i -> S}
    {l : Filter ι} {l' : Filter κ}
    (h :
      VdVWAsymptoticallyMeasurableBoundedContinuousLowerShiftedVaryingDomains
        Ω μs X l)
    {u : κ -> ι} (hu : Tendsto u l' l)
    (hlift :
      ∀ (f : S →ᵇ ℝ) c,
        (∀ k (ω : Ω (u k)), c ≤ f (X (u k) ω)) ->
          ∀ i (ω : Ω i), c ≤ f (X i ω)) :
    VdVWAsymptoticallyMeasurableBoundedContinuousLowerShiftedVaryingDomains
      (fun k => Ω (u k)) (fun k => μs (u k))
      (fun k ω => X (u k) ω) l' := by
  intro f c hlower
  exact (h f c (hlift f c hlower)).comp hu

/--
The varying-domain canonical shifted predicate is stable under passing to a
finer index filter.
-/
theorem
    VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShiftedVaryingDomains.mono_filter
    {ι : Type w} {Ω : ι -> Type u} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)] [TopologicalSpace S]
    {μs : (i : ι) -> Measure (Ω i)} {X : (i : ι) -> Ω i -> S}
    {l l' : Filter ι}
    (h :
      VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShiftedVaryingDomains
        Ω μs X l)
    (hl : l' ≤ l) :
    VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShiftedVaryingDomains
      Ω μs X l' := by
  intro f
  exact (h f).mono_left hl

/--
The varying-domain canonical shifted bounded-continuous asymptotic-measurability
predicate is unchanged by eventually equal measure families and eventually
equal arbitrary maps.
-/
theorem
    VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShiftedVaryingDomains.congr_eventually
    {ι : Type w} {Ω : ι -> Type u} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)] [TopologicalSpace S]
    {μs νs : (i : ι) -> Measure (Ω i)}
    {X Y : (i : ι) -> Ω i -> S}
    {l : Filter ι}
    (h :
      VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShiftedVaryingDomains
        Ω μs X l)
    (hμ : ∀ᶠ i in l, νs i = μs i)
    (hX : ∀ᶠ i in l, Y i = X i) :
    VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShiftedVaryingDomains
      Ω νs Y l := by
  intro f
  refine Tendsto.congr' ?_ (h f)
  filter_upwards [hμ, hX] with i hνμ hYX
  simp [hνμ, hYX]

/--
The varying-domain canonical shifted bounded-continuous asymptotic-
measurability predicate is stable under reindexing along a map that tends to
the original index filter.
-/
theorem
    VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShiftedVaryingDomains.comp_tendsto
    {ι : Type w} {κ : Type x} {Ω : ι -> Type u} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)] [TopologicalSpace S]
    {μs : (i : ι) -> Measure (Ω i)}
    {X : (i : ι) -> Ω i -> S}
    {l : Filter ι} {l' : Filter κ}
    (h :
      VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShiftedVaryingDomains
        Ω μs X l)
    {u : κ -> ι} (hu : Tendsto u l' l) :
    VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShiftedVaryingDomains
      (fun k => Ω (u k)) (fun k => μs (u k))
      (fun k ω => X (u k) ω) l' := by
  intro f
  exact (h f).comp hu

/--
Varying-domain signed bounded-continuous asymptotic measurability implies the
varying-domain lower-shifted bounded-continuous layer.
-/
theorem
    VdVWAsymptoticallyMeasurableSignedBoundedContinuousVaryingDomains.to_lowerShifted
    {ι : Type w} {Ω : ι -> Type u} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)] [TopologicalSpace S]
    {μs : (i : ι) -> Measure (Ω i)} {X : (i : ι) -> Ω i -> S}
    {l : Filter ι}
    (h :
      VdVWAsymptoticallyMeasurableSignedBoundedContinuousVaryingDomains
        Ω μs X l) :
    VdVWAsymptoticallyMeasurableBoundedContinuousLowerShiftedVaryingDomains
      Ω μs X l := by
  intro f c _hlower
  let fc : S →ᵇ ℝ := f - BoundedContinuousFunction.const S c
  have hsigned := h fc
  refine
    tendsto_of_tendsto_of_tendsto_of_le_of_le'
      (show Tendsto (fun _ : ι => (0 : ℝ≥0∞)) l (𝓝 0) from
        tendsto_const_nhds)
      hsigned
      (Eventually.of_forall fun _ => bot_le)
      ?_
  refine Eventually.of_forall fun i => ?_
  simpa [fc] using
    (VdVWLowerShiftedRealOuterInnerExpectationGap_le_signed_sub_const
      (μ := μs i) (Y := fun ω => f (X i ω)) (c := c))

/--
Varying-domain signed bounded-continuous asymptotic measurability implies the
varying-domain canonical shifted layer.
-/
theorem
    VdVWAsymptoticallyMeasurableSignedBoundedContinuousVaryingDomains.to_canonicalShifted
    {ι : Type w} {Ω : ι -> Type u} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)] [TopologicalSpace S]
    {μs : (i : ι) -> Measure (Ω i)} {X : (i : ι) -> Ω i -> S}
    {l : Filter ι}
    (h :
      VdVWAsymptoticallyMeasurableSignedBoundedContinuousVaryingDomains
        Ω μs X l) :
    VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShiftedVaryingDomains
      Ω μs X l :=
  VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShiftedVaryingDomains.of_lowerShifted
    h.to_lowerShifted

/--
Measurable varying-domain maps are lower-shifted asymptotically measurable for
all bounded continuous real tests.
-/
theorem
    VdVWAsymptoticallyMeasurableBoundedContinuousLowerShiftedVaryingDomains.of_forall_measurable
    {ι : Type w} {Ω : ι -> Type u} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)]
    [MeasurableSpace S] [TopologicalSpace S] [OpensMeasurableSpace S]
    {μs : (i : ι) -> Measure (Ω i)} {X : (i : ι) -> Ω i -> S}
    {l : Filter ι}
    (hX : ∀ i, Measurable (X i)) :
    VdVWAsymptoticallyMeasurableBoundedContinuousLowerShiftedVaryingDomains
      Ω μs X l :=
  (VdVWAsymptoticallyMeasurableSignedBoundedContinuousVaryingDomains.of_forall_measurable
    hX).to_lowerShifted

/--
Measurable varying-domain maps are canonically shifted asymptotically
measurable for all bounded continuous real tests.
-/
theorem
    VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShiftedVaryingDomains.of_forall_measurable
    {ι : Type w} {Ω : ι -> Type u} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)]
    [MeasurableSpace S] [TopologicalSpace S] [OpensMeasurableSpace S]
    {μs : (i : ι) -> Measure (Ω i)} {X : (i : ι) -> Ω i -> S}
    {l : Filter ι}
    (hX : ∀ i, Measurable (X i)) :
    VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShiftedVaryingDomains
      Ω μs X l :=
  VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShiftedVaryingDomains.of_lowerShifted
    (VdVWAsymptoticallyMeasurableBoundedContinuousLowerShiftedVaryingDomains.of_forall_measurable
      hX)

/--
Null-measurable varying-domain maps are lower-shifted asymptotically
measurable for all bounded continuous real tests.
-/
theorem
    VdVWAsymptoticallyMeasurableBoundedContinuousLowerShiftedVaryingDomains.of_forall_nullMeasurable
    {ι : Type w} {Ω : ι -> Type u} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)]
    [MeasurableSpace S]
    [TopologicalSpace S] [OpensMeasurableSpace S]
    {μs : (i : ι) -> Measure (Ω i)} {X : (i : ι) -> Ω i -> S}
    {l : Filter ι}
    (hX : ∀ i, NullMeasurable (X i) (μs i)) :
    VdVWAsymptoticallyMeasurableBoundedContinuousLowerShiftedVaryingDomains
      Ω μs X l :=
  (VdVWAsymptoticallyMeasurableSignedBoundedContinuousVaryingDomains.of_forall_nullMeasurable
    hX).to_lowerShifted

/--
Null-measurable varying-domain maps are canonically shifted asymptotically
measurable for all bounded continuous real tests.
-/
theorem
    VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShiftedVaryingDomains.of_forall_nullMeasurable
    {ι : Type w} {Ω : ι -> Type u} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)]
    [MeasurableSpace S]
    [TopologicalSpace S] [OpensMeasurableSpace S]
    {μs : (i : ι) -> Measure (Ω i)} {X : (i : ι) -> Ω i -> S}
    {l : Filter ι}
    (hX : ∀ i, NullMeasurable (X i) (μs i)) :
    VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShiftedVaryingDomains
      Ω μs X l :=
  VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShiftedVaryingDomains.of_lowerShifted
    (VdVWAsymptoticallyMeasurableBoundedContinuousLowerShiftedVaryingDomains.of_forall_nullMeasurable
      hX)

/--
A.e.-measurable varying-domain maps are lower-shifted asymptotically
measurable for all bounded continuous real tests.
-/
theorem
    VdVWAsymptoticallyMeasurableBoundedContinuousLowerShiftedVaryingDomains.of_forall_aemeasurable
    {ι : Type w} {Ω : ι -> Type u} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)]
    [MeasurableSpace S]
    [TopologicalSpace S] [OpensMeasurableSpace S]
    {μs : (i : ι) -> Measure (Ω i)} {X : (i : ι) -> Ω i -> S}
    {l : Filter ι}
    (hX : ∀ i, AEMeasurable (X i) (μs i)) :
    VdVWAsymptoticallyMeasurableBoundedContinuousLowerShiftedVaryingDomains
      Ω μs X l :=
  (VdVWAsymptoticallyMeasurableSignedBoundedContinuousVaryingDomains.of_forall_aemeasurable
    hX).to_lowerShifted

/--
A.e.-measurable varying-domain maps are canonically shifted asymptotically
measurable for all bounded continuous real tests.
-/
theorem
    VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShiftedVaryingDomains.of_forall_aemeasurable
    {ι : Type w} {Ω : ι -> Type u} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)]
    [MeasurableSpace S]
    [TopologicalSpace S] [OpensMeasurableSpace S]
    {μs : (i : ι) -> Measure (Ω i)} {X : (i : ι) -> Ω i -> S}
    {l : Filter ι}
    (hX : ∀ i, AEMeasurable (X i) (μs i)) :
    VdVWAsymptoticallyMeasurableBoundedContinuousCanonicalShiftedVaryingDomains
      Ω μs X l :=
  (VdVWAsymptoticallyMeasurableSignedBoundedContinuousVaryingDomains.of_forall_aemeasurable
    hX).to_canonicalShifted

/--
Measure-level weak convergence of probability measures.

This is the mathlib-backed part of VdV&W Definition 1.3.3, specialized to
ordinary Borel probability measures rather than arbitrary nonmeasurable maps.
-/
def VdVWWeakConvergenceProbabilityMeasures
    {S : Type u} {ι : Type v} [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S]
    (μs : ι -> ProbabilityMeasure S) (l : Filter ι)
    (μ : ProbabilityMeasure S) : Prop :=
  Tendsto μs l (𝓝 μ)

/--
Measure-level weak convergence is stable under passing to a finer index
filter.
-/
theorem VdVWWeakConvergenceProbabilityMeasures.mono_filter
    {S : Type u} {ι : Type v} [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S]
    {μs : ι -> ProbabilityMeasure S} {l l' : Filter ι}
    {μ : ProbabilityMeasure S}
    (h : VdVWWeakConvergenceProbabilityMeasures μs l μ) (hl : l' ≤ l) :
    VdVWWeakConvergenceProbabilityMeasures μs l' μ :=
  h.mono_left hl

/--
Measure-level weak convergence is unchanged by eventually equal
probability-measure families.
-/
theorem VdVWWeakConvergenceProbabilityMeasures.congr_eventually
    {S : Type u} {ι : Type v} [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S]
    {μs νs : ι -> ProbabilityMeasure S} {l : Filter ι}
    {μ : ProbabilityMeasure S}
    (h : VdVWWeakConvergenceProbabilityMeasures μs l μ)
    (h_eq : ∀ᶠ i in l, νs i = μs i) :
    VdVWWeakConvergenceProbabilityMeasures νs l μ :=
  Tendsto.congr' (h_eq.mono fun _ hi => hi.symm) h

/--
Measure-level weak convergence is unchanged by replacing the limiting
probability measure by an equal one.
-/
theorem VdVWWeakConvergenceProbabilityMeasures.congr_limit
    {S : Type u} {ι : Type v} [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S]
    {μs : ι -> ProbabilityMeasure S} {l : Filter ι}
    {μ ν : ProbabilityMeasure S}
    (h : VdVWWeakConvergenceProbabilityMeasures μs l μ)
    (h_eq : ν = μ) :
    VdVWWeakConvergenceProbabilityMeasures μs l ν := by
  simpa [h_eq] using h

/--
Measure-level weak convergence is unchanged by eventually equal source
families and an equal limiting probability measure.
-/
theorem VdVWWeakConvergenceProbabilityMeasures.congr_eventually_limit
    {S : Type u} {ι : Type v} [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S]
    {μs νs : ι -> ProbabilityMeasure S} {l : Filter ι}
    {μ ν : ProbabilityMeasure S}
    (h : VdVWWeakConvergenceProbabilityMeasures μs l μ)
    (h_src : ∀ᶠ i in l, νs i = μs i)
    (h_lim : ν = μ) :
    VdVWWeakConvergenceProbabilityMeasures νs l ν :=
  (h.congr_eventually h_src).congr_limit h_lim

/--
Measure-level weak convergence is stable under reindexing along a map that
tends to the original index filter.
-/
theorem VdVWWeakConvergenceProbabilityMeasures.comp_tendsto
    {S : Type u} {ι : Type v} {κ : Type w}
    [MeasurableSpace S] [TopologicalSpace S] [OpensMeasurableSpace S]
    {μs : ι -> ProbabilityMeasure S} {l : Filter ι} {l' : Filter κ}
    {μ : ProbabilityMeasure S}
    (h : VdVWWeakConvergenceProbabilityMeasures μs l μ)
    {u : κ -> ι} (hu : Tendsto u l' l) :
    VdVWWeakConvergenceProbabilityMeasures (fun k => μs (u k)) l' μ :=
  h.comp hu

/--
VdV&W weak convergence of probability measures is characterized by convergence
of integrals of all bounded continuous real-valued test functions.

This is the direct pinned-mathlib foundation for the measure-level part of
Chapter 1.3.
-/
theorem vdVWWeakConvergenceProbabilityMeasures_iff_forall_integral_tendsto
    {S : Type u} {ι : Type v} [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S]
    {μs : ι -> ProbabilityMeasure S} {l : Filter ι}
    {μ : ProbabilityMeasure S} :
    VdVWWeakConvergenceProbabilityMeasures μs l μ ↔
      ∀ f : S →ᵇ ℝ,
        Tendsto (fun i => ∫ s, f s ∂(μs i : Measure S)) l
          (𝓝 (∫ s, f s ∂(μ : Measure S))) := by
  exact ProbabilityMeasure.tendsto_iff_forall_integral_tendsto

/--
Measure-level weak convergence implies the signed-outer bounded-continuous
formulation for the identity maps.

This connects the new signed positive/negative outer-expectation bridge back
to the pinned mathlib weak-convergence theorem: on measurable probability
spaces, the signed outer test integral is the ordinary bounded-continuous
test integral.
-/
theorem VdVWWeakConvergenceProbabilityMeasures.to_signedOuterBoundedContinuous_id
    {S : Type u} {ι : Type v} [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S]
    {μs : ι -> ProbabilityMeasure S} {l : Filter ι}
    {μ : ProbabilityMeasure S}
    (h : VdVWWeakConvergenceProbabilityMeasures μs l μ) :
    VdVWWeakConvergenceSignedOuterBoundedContinuous
      (fun i => (μs i : Measure S)) (fun _ s => s) l μ := by
  intro f
  have houter :
      (fun i =>
        VdVWSignedOuterExpectationPosNeg (μs i : Measure S)
          (fun s => f ((fun s => s) s))) =
        fun i => ∫ s, f s ∂(μs i : Measure S) := by
    funext i
    simpa using
      (VdVWSignedOuterExpectationPosNeg_eq_integral_of_boundedContinuous_comp
        (μ := (μs i : Measure S)) (X := fun s : S => s) measurable_id f)
  simpa [VdVWWeakConvergenceSignedOuterBoundedContinuous, houter] using
    (vdVWWeakConvergenceProbabilityMeasures_iff_forall_integral_tendsto.mp h f)

/--
Map-law form of the signed-outer bounded-continuous weak-convergence bridge.

If measurable maps have laws `νs i` under the source measures `μs i`, and
those laws converge weakly, then the original maps converge in the local
signed-outer bounded-continuous sense.  This is the measurable arbitrary-map
analogue of the identity-map bridge.
-/
theorem VdVWWeakConvergenceProbabilityMeasures.to_signedOuterBoundedContinuous_of_map_eq
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S]
    {μs : ι -> Measure Ω} [∀ i, IsFiniteMeasure (μs i)]
    {X : ι -> Ω -> S} (hX : ∀ i, Measurable (X i))
    {νs : ι -> ProbabilityMeasure S} {l : Filter ι}
    {μ : ProbabilityMeasure S}
    (hν : VdVWWeakConvergenceProbabilityMeasures νs l μ)
    (hmap : ∀ i, (νs i : Measure S) = Measure.map (X i) (μs i)) :
    VdVWWeakConvergenceSignedOuterBoundedContinuous μs X l μ := by
  intro f
  have houter :
      (fun i =>
        VdVWSignedOuterExpectationPosNeg (μs i) (fun ω => f (X i ω))) =
        fun i => ∫ s, f s ∂(νs i : Measure S) := by
    funext i
    calc
      VdVWSignedOuterExpectationPosNeg (μs i) (fun ω => f (X i ω))
          = ∫ ω, f (X i ω) ∂μs i := by
            exact VdVWSignedOuterExpectationPosNeg_eq_integral_of_boundedContinuous_comp
              (μ := μs i) (X := X i) (hX i) f
      _ = ∫ s, f s ∂Measure.map (X i) (μs i) := by
            exact (integral_map (hX i).aemeasurable
              f.continuous.measurable.aestronglyMeasurable).symm
      _ = ∫ s, f s ∂(νs i : Measure S) := by
            rw [← hmap i]
  simpa [VdVWWeakConvergenceSignedOuterBoundedContinuous, houter] using
    (vdVWWeakConvergenceProbabilityMeasures_iff_forall_integral_tendsto.mp hν f)

/--
Measurable law-level weak convergence gives the proof-carrying signed
bounded-continuous arbitrary-map layer.
-/
theorem
    VdVWWeakConvergenceProbabilityMeasures.to_signedBoundedContinuousArbitraryMap_of_map_eq
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S]
    {μs : ι -> Measure Ω} [∀ i, IsFiniteMeasure (μs i)]
    {X : ι -> Ω -> S} (hX : ∀ i, Measurable (X i))
    {νs : ι -> ProbabilityMeasure S} {l : Filter ι}
    {μ : ProbabilityMeasure S}
    (hweak : VdVWWeakConvergenceProbabilityMeasures νs l μ)
    (hmap : ∀ i, (νs i : Measure S) = Measure.map (X i) (μs i)) :
    VdVWWeakConvergenceSignedBoundedContinuousArbitraryMap μs X l μ :=
  { weakConvergence :=
      hweak.to_signedOuterBoundedContinuous_of_map_eq hX hmap
    asymptoticMeasurability :=
      VdVWAsymptoticallyMeasurableSignedBoundedContinuous.of_forall_measurable hX }

/--
A.e.-measurable map-law form of the signed-outer bounded-continuous
weak-convergence bridge.

This is the direct a.e.-measurable analogue of
`to_signedOuterBoundedContinuous_of_map_eq`; it avoids strengthening the target
space to a countably generated space merely to pass through
`NullMeasurable`.
-/
theorem
    VdVWWeakConvergenceProbabilityMeasures.to_signedOuterBoundedContinuous_of_map_eq_aemeasurable
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S]
    {μs : ι -> Measure Ω} [∀ i, IsFiniteMeasure (μs i)]
    {X : ι -> Ω -> S} (hX : ∀ i, AEMeasurable (X i) (μs i))
    {νs : ι -> ProbabilityMeasure S} {l : Filter ι}
    {μ : ProbabilityMeasure S}
    (hν : VdVWWeakConvergenceProbabilityMeasures νs l μ)
    (hmap : ∀ i, (νs i : Measure S) = Measure.map (X i) (μs i)) :
    VdVWWeakConvergenceSignedOuterBoundedContinuous μs X l μ := by
  intro f
  have houter :
      (fun i =>
        VdVWSignedOuterExpectationPosNeg (μs i) (fun ω => f (X i ω))) =
        fun i => ∫ s, f s ∂(νs i : Measure S) := by
    funext i
    calc
      VdVWSignedOuterExpectationPosNeg (μs i) (fun ω => f (X i ω))
          = ∫ ω, f (X i ω) ∂μs i := by
            exact VdVWSignedOuterExpectationPosNeg_eq_integral_of_boundedContinuous_comp_aemeasurable
              (μ := μs i) (X := X i) (hX i) f
      _ = ∫ s, f s ∂Measure.map (X i) (μs i) := by
            exact (integral_map (hX i)
              f.continuous.measurable.aestronglyMeasurable).symm
      _ = ∫ s, f s ∂(νs i : Measure S) := by
            rw [← hmap i]
  simpa [VdVWWeakConvergenceSignedOuterBoundedContinuous, houter] using
    (vdVWWeakConvergenceProbabilityMeasures_iff_forall_integral_tendsto.mp hν f)

/--
A.e.-measurable law-level weak convergence gives the proof-carrying signed
bounded-continuous arbitrary-map layer.
-/
theorem
    VdVWWeakConvergenceProbabilityMeasures.to_signedBoundedContinuousArbitraryMap_of_map_eq_aemeasurable
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S]
    {μs : ι -> Measure Ω} [∀ i, IsFiniteMeasure (μs i)]
    {X : ι -> Ω -> S} (hX : ∀ i, AEMeasurable (X i) (μs i))
    {νs : ι -> ProbabilityMeasure S} {l : Filter ι}
    {μ : ProbabilityMeasure S}
    (hweak : VdVWWeakConvergenceProbabilityMeasures νs l μ)
    (hmap : ∀ i, (νs i : Measure S) = Measure.map (X i) (μs i)) :
    VdVWWeakConvergenceSignedBoundedContinuousArbitraryMap μs X l μ :=
  { weakConvergence :=
      hweak.to_signedOuterBoundedContinuous_of_map_eq_aemeasurable hX hmap
    asymptoticMeasurability :=
      VdVWAsymptoticallyMeasurableSignedBoundedContinuous.of_forall_aemeasurable hX }

/--
Common-domain null-measurable map-law form of the signed-outer
bounded-continuous weak-convergence bridge.

This is the completion-measurable analogue of
`to_signedOuterBoundedContinuous_of_map_eq`.  It is useful for VdV&W
`P`-measurable statistics before replacing them by measurable representatives.
-/
theorem
    VdVWWeakConvergenceProbabilityMeasures.to_signedOuterBoundedContinuous_of_map_eq_nullMeasurable
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [MeasurableSpace S] [MeasurableSpace.CountablyGenerated S]
    [TopologicalSpace S] [OpensMeasurableSpace S]
    {μs : ι -> Measure Ω} [∀ i, IsFiniteMeasure (μs i)]
    {X : ι -> Ω -> S} (hX : ∀ i, NullMeasurable (X i) (μs i))
    {νs : ι -> ProbabilityMeasure S} {l : Filter ι}
    {μ : ProbabilityMeasure S}
    (hν : VdVWWeakConvergenceProbabilityMeasures νs l μ)
    (hmap : ∀ i, (νs i : Measure S) = Measure.map (X i) (μs i)) :
    VdVWWeakConvergenceSignedOuterBoundedContinuous μs X l μ := by
  intro f
  have houter :
      (fun i =>
        VdVWSignedOuterExpectationPosNeg (μs i) (fun ω => f (X i ω))) =
        fun i => ∫ s, f s ∂(νs i : Measure S) := by
    funext i
    calc
      VdVWSignedOuterExpectationPosNeg (μs i) (fun ω => f (X i ω))
          = ∫ ω, f (X i ω) ∂μs i := by
            exact VdVWSignedOuterExpectationPosNeg_eq_integral_of_boundedContinuous_comp_nullMeasurable
              (μ := μs i) (X := X i) (hX i) f
      _ = ∫ s, f s ∂Measure.map (X i) (μs i) := by
            exact (integral_map (hX i).aemeasurable
              f.continuous.measurable.aestronglyMeasurable).symm
      _ = ∫ s, f s ∂(νs i : Measure S) := by
            rw [← hmap i]
  simpa [VdVWWeakConvergenceSignedOuterBoundedContinuous, houter] using
    (vdVWWeakConvergenceProbabilityMeasures_iff_forall_integral_tendsto.mp hν f)

/--
Common-domain null-measurable law-level weak convergence gives the
proof-carrying signed bounded-continuous arbitrary-map layer.
-/
theorem
    VdVWWeakConvergenceProbabilityMeasures.to_signedBoundedContinuousArbitraryMap_of_map_eq_nullMeasurable
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [MeasurableSpace S] [MeasurableSpace.CountablyGenerated S]
    [TopologicalSpace S] [OpensMeasurableSpace S]
    {μs : ι -> Measure Ω} [∀ i, IsFiniteMeasure (μs i)]
    {X : ι -> Ω -> S} (hX : ∀ i, NullMeasurable (X i) (μs i))
    {νs : ι -> ProbabilityMeasure S} {l : Filter ι}
    {μ : ProbabilityMeasure S}
    (hweak : VdVWWeakConvergenceProbabilityMeasures νs l μ)
    (hmap : ∀ i, (νs i : Measure S) = Measure.map (X i) (μs i)) :
    VdVWWeakConvergenceSignedBoundedContinuousArbitraryMap μs X l μ :=
  { weakConvergence :=
      hweak.to_signedOuterBoundedContinuous_of_map_eq_nullMeasurable hX hmap
    asymptoticMeasurability :=
      VdVWAsymptoticallyMeasurableSignedBoundedContinuous.of_forall_nullMeasurable hX }

/--
Automatic-pushforward common-domain signed bounded-continuous weak-convergence
bridge for null-measurable maps.
-/
theorem
    VdVWWeakConvergenceProbabilityMeasures.to_signedBoundedContinuousArbitraryMap_of_maps_nullMeasurable
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [MeasurableSpace S] [MeasurableSpace.CountablyGenerated S]
    [TopologicalSpace S] [OpensMeasurableSpace S]
    {μs : ι -> Measure Ω} [∀ i, IsProbabilityMeasure (μs i)]
    {X : ι -> Ω -> S} (hX : ∀ i, NullMeasurable (X i) (μs i))
    {l : Filter ι} {μ : ProbabilityMeasure S}
    (hweak :
      VdVWWeakConvergenceProbabilityMeasures
        (fun i =>
          ⟨Measure.map (X i) (μs i),
            Measure.isProbabilityMeasure_map ((hX i).aemeasurable)⟩)
        l μ) :
    VdVWWeakConvergenceSignedBoundedContinuousArbitraryMap μs X l μ :=
  VdVWWeakConvergenceProbabilityMeasures.to_signedBoundedContinuousArbitraryMap_of_map_eq_nullMeasurable
    (μs := μs) (X := X) hX hweak (fun _ => rfl)

/--
Automatic-pushforward common-domain signed bounded-continuous weak-convergence
bridge for a.e.-measurable maps.
-/
theorem
    VdVWWeakConvergenceProbabilityMeasures.to_signedBoundedContinuousArbitraryMap_of_maps_aemeasurable
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S]
    {μs : ι -> Measure Ω} [∀ i, IsProbabilityMeasure (μs i)]
    {X : ι -> Ω -> S} (hX : ∀ i, AEMeasurable (X i) (μs i))
    {l : Filter ι} {μ : ProbabilityMeasure S}
    (hweak :
      VdVWWeakConvergenceProbabilityMeasures
        (fun i =>
          ⟨Measure.map (X i) (μs i),
            Measure.isProbabilityMeasure_map (hX i)⟩)
        l μ) :
    VdVWWeakConvergenceSignedBoundedContinuousArbitraryMap μs X l μ :=
  VdVWWeakConvergenceProbabilityMeasures.to_signedBoundedContinuousArbitraryMap_of_map_eq_aemeasurable
    (μs := μs) (X := X) (νs := fun i =>
      ⟨Measure.map (X i) (μs i), Measure.isProbabilityMeasure_map (hX i)⟩)
    hX hweak (fun _ => rfl)

/--
Varying-domain map-law form of the signed bounded-continuous
weak-convergence bridge.

This is the law-convergence feeder for sample-size-varying spaces such as
`SampleAt Observation n`: once the pushforward laws on the common state space
converge weakly, the varying-domain maps satisfy the proof-carrying signed
bounded-continuous weak-convergence package.
-/
theorem
    VdVWWeakConvergenceProbabilityMeasures.to_signedBoundedContinuousVaryingDomains_of_map_eq
    {ι : Type w} {Ω : ι -> Type u} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)]
    [MeasurableSpace S] [TopologicalSpace S] [OpensMeasurableSpace S]
    {μs : (i : ι) -> Measure (Ω i)} [∀ i, IsFiniteMeasure (μs i)]
    {X : (i : ι) -> Ω i -> S} (hX : ∀ i, Measurable (X i))
    {νs : ι -> ProbabilityMeasure S} {l : Filter ι}
    {μ : ProbabilityMeasure S}
    (hweak : VdVWWeakConvergenceProbabilityMeasures νs l μ)
    (hmap : ∀ i, (νs i : Measure S) = Measure.map (X i) (μs i)) :
    VdVWWeakConvergenceSignedBoundedContinuousVaryingDomains Ω μs X l μ := by
  refine ⟨?_, ?_⟩
  · intro f
    have houter :
        (fun i =>
          VdVWSignedOuterExpectationPosNeg (μs i) (fun ω => f (X i ω))) =
          fun i => ∫ s, f s ∂(νs i : Measure S) := by
      funext i
      calc
        VdVWSignedOuterExpectationPosNeg (μs i) (fun ω => f (X i ω))
            = ∫ ω, f (X i ω) ∂μs i := by
              exact
                VdVWSignedOuterExpectationPosNeg_eq_integral_of_boundedContinuous_comp
                  (μ := μs i) (X := X i) (hX i) f
        _ = ∫ s, f s ∂Measure.map (X i) (μs i) := by
              exact (integral_map (hX i).aemeasurable
                f.continuous.measurable.aestronglyMeasurable).symm
        _ = ∫ s, f s ∂(νs i : Measure S) := by
              rw [← hmap i]
    simpa [VdVWWeakConvergenceSignedOuterBoundedContinuousVaryingDomains,
      houter] using
      (vdVWWeakConvergenceProbabilityMeasures_iff_forall_integral_tendsto.mp
        hweak f)
  · exact
      VdVWAsymptoticallyMeasurableSignedBoundedContinuousVaryingDomains.of_forall_measurable
        hX

/--
Varying-domain null-measurable map-law form of the signed bounded-continuous
weak-convergence bridge.

This is the arbitrary-map version used when the source statistics are only
measurable on the completion, as in VdV&W Definition 2.3.3.
-/
theorem
    VdVWWeakConvergenceProbabilityMeasures.to_signedBoundedContinuousVaryingDomains_of_map_eq_nullMeasurable
    {ι : Type w} {Ω : ι -> Type u} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)]
    [MeasurableSpace S] [MeasurableSpace.CountablyGenerated S]
    [TopologicalSpace S] [OpensMeasurableSpace S]
    {μs : (i : ι) -> Measure (Ω i)} [∀ i, IsFiniteMeasure (μs i)]
    {X : (i : ι) -> Ω i -> S} (hX : ∀ i, NullMeasurable (X i) (μs i))
    {νs : ι -> ProbabilityMeasure S} {l : Filter ι}
    {μ : ProbabilityMeasure S}
    (hweak : VdVWWeakConvergenceProbabilityMeasures νs l μ)
    (hmap : ∀ i, (νs i : Measure S) = Measure.map (X i) (μs i)) :
    VdVWWeakConvergenceSignedBoundedContinuousVaryingDomains Ω μs X l μ := by
  refine ⟨?_, ?_⟩
  · intro f
    have houter :
        (fun i =>
          VdVWSignedOuterExpectationPosNeg (μs i) (fun ω => f (X i ω))) =
          fun i => ∫ s, f s ∂(νs i : Measure S) := by
      funext i
      calc
        VdVWSignedOuterExpectationPosNeg (μs i) (fun ω => f (X i ω))
            = ∫ ω, f (X i ω) ∂μs i := by
              exact
                VdVWSignedOuterExpectationPosNeg_eq_integral_of_boundedContinuous_comp_nullMeasurable
                  (μ := μs i) (X := X i) (hX i) f
        _ = ∫ s, f s ∂Measure.map (X i) (μs i) := by
              exact (integral_map (hX i).aemeasurable
                f.continuous.measurable.aestronglyMeasurable).symm
        _ = ∫ s, f s ∂(νs i : Measure S) := by
              rw [← hmap i]
    simpa [VdVWWeakConvergenceSignedOuterBoundedContinuousVaryingDomains,
      houter] using
      (vdVWWeakConvergenceProbabilityMeasures_iff_forall_integral_tendsto.mp
        hweak f)
  · exact
      VdVWAsymptoticallyMeasurableSignedBoundedContinuousVaryingDomains.of_forall_nullMeasurable
        hX

/--
Varying-domain a.e.-measurable map-law form of the signed
bounded-continuous weak-convergence bridge.

This avoids passing through null-measurability and therefore does not require
the target measurable space to be countably generated.
-/
theorem
    VdVWWeakConvergenceProbabilityMeasures.to_signedBoundedContinuousVaryingDomains_of_map_eq_aemeasurable
    {ι : Type w} {Ω : ι -> Type u} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)]
    [MeasurableSpace S] [TopologicalSpace S] [OpensMeasurableSpace S]
    {μs : (i : ι) -> Measure (Ω i)} [∀ i, IsFiniteMeasure (μs i)]
    {X : (i : ι) -> Ω i -> S} (hX : ∀ i, AEMeasurable (X i) (μs i))
    {νs : ι -> ProbabilityMeasure S} {l : Filter ι}
    {μ : ProbabilityMeasure S}
    (hweak : VdVWWeakConvergenceProbabilityMeasures νs l μ)
    (hmap : ∀ i, (νs i : Measure S) = Measure.map (X i) (μs i)) :
    VdVWWeakConvergenceSignedBoundedContinuousVaryingDomains Ω μs X l μ := by
  refine ⟨?_, ?_⟩
  · intro f
    have houter :
        (fun i =>
          VdVWSignedOuterExpectationPosNeg (μs i) (fun ω => f (X i ω))) =
          fun i => ∫ s, f s ∂(νs i : Measure S) := by
      funext i
      calc
        VdVWSignedOuterExpectationPosNeg (μs i) (fun ω => f (X i ω))
            = ∫ ω, f (X i ω) ∂μs i := by
              exact
                VdVWSignedOuterExpectationPosNeg_eq_integral_of_boundedContinuous_comp_aemeasurable
                  (μ := μs i) (X := X i) (hX i) f
        _ = ∫ s, f s ∂Measure.map (X i) (μs i) := by
              exact (integral_map (hX i)
                f.continuous.measurable.aestronglyMeasurable).symm
        _ = ∫ s, f s ∂(νs i : Measure S) := by
              rw [← hmap i]
    simpa [VdVWWeakConvergenceSignedOuterBoundedContinuousVaryingDomains,
      houter] using
      (vdVWWeakConvergenceProbabilityMeasures_iff_forall_integral_tendsto.mp
        hweak f)
  · exact
      VdVWAsymptoticallyMeasurableSignedBoundedContinuousVaryingDomains.of_forall_aemeasurable
        hX

/--
Automatic-pushforward version of the varying-domain signed
bounded-continuous weak-convergence bridge.
-/
theorem
    VdVWWeakConvergenceProbabilityMeasures.to_signedBoundedContinuousVaryingDomains_of_maps
    {ι : Type w} {Ω : ι -> Type u} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)]
    [MeasurableSpace S] [TopologicalSpace S] [OpensMeasurableSpace S]
    {μs : (i : ι) -> Measure (Ω i)} [∀ i, IsProbabilityMeasure (μs i)]
    {X : (i : ι) -> Ω i -> S} (hX : ∀ i, Measurable (X i))
    {l : Filter ι} {μ : ProbabilityMeasure S}
    (hweak :
      VdVWWeakConvergenceProbabilityMeasures
        (fun i =>
          ⟨Measure.map (X i) (μs i),
            Measure.isProbabilityMeasure_map (hX i).aemeasurable⟩)
        l μ) :
    VdVWWeakConvergenceSignedBoundedContinuousVaryingDomains Ω μs X l μ :=
  VdVWWeakConvergenceProbabilityMeasures.to_signedBoundedContinuousVaryingDomains_of_map_eq
    (μs := μs) (X := X) hX hweak (fun _ => rfl)

/--
Automatic-pushforward version of the varying-domain signed bounded-continuous
weak-convergence bridge for null-measurable maps.
-/
theorem
    VdVWWeakConvergenceProbabilityMeasures.to_signedBoundedContinuousVaryingDomains_of_maps_nullMeasurable
    {ι : Type w} {Ω : ι -> Type u} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)]
    [MeasurableSpace S] [MeasurableSpace.CountablyGenerated S]
    [TopologicalSpace S] [OpensMeasurableSpace S]
    {μs : (i : ι) -> Measure (Ω i)} [∀ i, IsProbabilityMeasure (μs i)]
    {X : (i : ι) -> Ω i -> S} (hX : ∀ i, NullMeasurable (X i) (μs i))
    {l : Filter ι} {μ : ProbabilityMeasure S}
    (hweak :
      VdVWWeakConvergenceProbabilityMeasures
        (fun i =>
          ⟨Measure.map (X i) (μs i),
            Measure.isProbabilityMeasure_map ((hX i).aemeasurable)⟩)
        l μ) :
    VdVWWeakConvergenceSignedBoundedContinuousVaryingDomains Ω μs X l μ :=
  VdVWWeakConvergenceProbabilityMeasures.to_signedBoundedContinuousVaryingDomains_of_map_eq_nullMeasurable
    (μs := μs) (X := X) hX hweak (fun _ => rfl)

/--
Automatic-pushforward version of the varying-domain signed bounded-continuous
weak-convergence bridge for a.e.-measurable maps.
-/
theorem
    VdVWWeakConvergenceProbabilityMeasures.to_signedBoundedContinuousVaryingDomains_of_maps_aemeasurable
    {ι : Type w} {Ω : ι -> Type u} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)]
    [MeasurableSpace S] [TopologicalSpace S] [OpensMeasurableSpace S]
    {μs : (i : ι) -> Measure (Ω i)} [∀ i, IsProbabilityMeasure (μs i)]
    {X : (i : ι) -> Ω i -> S} (hX : ∀ i, AEMeasurable (X i) (μs i))
    {l : Filter ι} {μ : ProbabilityMeasure S}
    (hweak :
      VdVWWeakConvergenceProbabilityMeasures
        (fun i =>
          ⟨Measure.map (X i) (μs i),
            Measure.isProbabilityMeasure_map (hX i)⟩)
        l μ) :
    VdVWWeakConvergenceSignedBoundedContinuousVaryingDomains Ω μs X l μ :=
  VdVWWeakConvergenceProbabilityMeasures.to_signedBoundedContinuousVaryingDomains_of_map_eq_aemeasurable
    (μs := μs) (X := X) (νs := fun i =>
      ⟨Measure.map (X i) (μs i), Measure.isProbabilityMeasure_map (hX i)⟩)
    hX hweak (fun _ => rfl)

/--
Common-domain has-law weak convergence gives the signed-outer
bounded-continuous weak-convergence layer without a separate pointwise
measurability hypothesis.

Mathlib's `HasLaw` already contains the a.e.-measurability and map-law
identity needed for the local null-measurable signed outer-expectation bridge.
-/
theorem VdVWWeakConvergenceProbabilityMeasures.to_signedOuterBoundedContinuous_of_hasLaw_aemeasurable
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S}
    {νs : ι -> ProbabilityMeasure S} {l : Filter ι}
    {μ : ProbabilityMeasure S}
    (hν : VdVWWeakConvergenceProbabilityMeasures νs l μ)
    (hlaw : ∀ i, HasLaw (X i) (νs i : Measure S) (μs i)) :
    VdVWWeakConvergenceSignedOuterBoundedContinuous μs X l μ := by
  haveI : ∀ i, IsFiniteMeasure (μs i) := fun i => (hlaw i).isFiniteMeasure
  exact
    VdVWWeakConvergenceProbabilityMeasures.to_signedOuterBoundedContinuous_of_map_eq_aemeasurable
      (μs := μs) (X := X) (νs := νs)
      (fun i => (hlaw i).aemeasurable)
      hν (fun i => (hlaw i).map_eq.symm)

/--
Common-domain has-law weak convergence gives the proof-carrying signed
bounded-continuous arbitrary-map layer without a separate pointwise
measurability hypothesis.
-/
theorem
    VdVWWeakConvergenceProbabilityMeasures.to_signedBoundedContinuousArbitraryMap_of_hasLaw_aemeasurable
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S}
    {νs : ι -> ProbabilityMeasure S} {l : Filter ι}
    {μ : ProbabilityMeasure S}
    (hweak : VdVWWeakConvergenceProbabilityMeasures νs l μ)
    (hlaw : ∀ i, HasLaw (X i) (νs i : Measure S) (μs i)) :
    VdVWWeakConvergenceSignedBoundedContinuousArbitraryMap μs X l μ := by
  haveI : ∀ i, IsFiniteMeasure (μs i) := fun i => (hlaw i).isFiniteMeasure
  exact
    VdVWWeakConvergenceProbabilityMeasures.to_signedBoundedContinuousArbitraryMap_of_map_eq_aemeasurable
      (μs := μs) (X := X) (νs := νs)
      (fun i => (hlaw i).aemeasurable)
      hweak (fun i => (hlaw i).map_eq.symm)

/--
Varying-domain has-law weak convergence gives the proof-carrying signed
bounded-continuous weak-convergence package without a separate pointwise
measurability hypothesis.
-/
theorem
    VdVWWeakConvergenceProbabilityMeasures.to_signedBoundedContinuousVaryingDomains_of_hasLaw_aemeasurable
    {ι : Type w} {Ω : ι -> Type u} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)]
    [MeasurableSpace S] [TopologicalSpace S] [OpensMeasurableSpace S]
    {μs : (i : ι) -> Measure (Ω i)} {X : (i : ι) -> Ω i -> S}
    {νs : ι -> ProbabilityMeasure S} {l : Filter ι}
    {μ : ProbabilityMeasure S}
    (hweak : VdVWWeakConvergenceProbabilityMeasures νs l μ)
    (hlaw : ∀ i, HasLaw (X i) (νs i : Measure S) (μs i)) :
    VdVWWeakConvergenceSignedBoundedContinuousVaryingDomains Ω μs X l μ := by
  haveI : ∀ i, IsFiniteMeasure (μs i) := fun i => (hlaw i).isFiniteMeasure
  exact
    VdVWWeakConvergenceProbabilityMeasures.to_signedBoundedContinuousVaryingDomains_of_map_eq_aemeasurable
      (Ω := Ω) (μs := μs) (X := X) (νs := νs)
      (fun i => (hlaw i).aemeasurable)
      hweak (fun i => (hlaw i).map_eq.symm)

/--
Varying-domain convergence in distribution implies the local signed-outer
bounded-continuous weak-convergence formulation.

This is the sample-size-varying analogue of
`vdVWTendstoInDistribution_to_signedOuterBoundedContinuous_aemeasurable`.
It uses the a.e.-measurability carried by mathlib's
`TendstoInDistribution` and the local VdV&W signed outer-expectation bridge.
-/
theorem vdVWTendstoInDistribution_to_signedOuterBoundedContinuousVaryingDomains_aemeasurable
    {ι : Type w} {Ω : ι -> Type u} {Ω' : Type x} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)]
    [MeasurableSpace Ω'] {μ' : Measure Ω'} [IsProbabilityMeasure μ']
    [MeasurableSpace S] [MeasurableSpace.CountablyGenerated S]
    [TopologicalSpace S] [OpensMeasurableSpace S]
    {μs : (i : ι) -> Measure (Ω i)} [∀ i, IsProbabilityMeasure (μs i)]
    {X : (i : ι) -> Ω i -> S} {Z : Ω' -> S} {l : Filter ι}
    (h : TendstoInDistribution X l Z μs μ') :
    VdVWWeakConvergenceSignedOuterBoundedContinuousVaryingDomains Ω μs X l
      ⟨μ'.map Z, Measure.isProbabilityMeasure_map h.aemeasurable_limit⟩ :=
  (VdVWWeakConvergenceProbabilityMeasures.to_signedBoundedContinuousVaryingDomains_of_maps_aemeasurable
    (Ω := Ω) (μs := μs) (X := X)
    (fun i => h.forall_aemeasurable i) h.tendsto).weakConvergence

/--
Varying-domain convergence in distribution gives the proof-carrying signed
bounded-continuous weak-convergence package.
-/
theorem vdVWTendstoInDistribution_to_signedBoundedContinuousVaryingDomains_aemeasurable
    {ι : Type w} {Ω : ι -> Type u} {Ω' : Type x} {S : Type v}
    [∀ i, MeasurableSpace (Ω i)]
    [MeasurableSpace Ω'] {μ' : Measure Ω'} [IsProbabilityMeasure μ']
    [MeasurableSpace S] [MeasurableSpace.CountablyGenerated S]
    [TopologicalSpace S] [OpensMeasurableSpace S]
    {μs : (i : ι) -> Measure (Ω i)} [∀ i, IsProbabilityMeasure (μs i)]
    {X : (i : ι) -> Ω i -> S} {Z : Ω' -> S} {l : Filter ι}
    (h : TendstoInDistribution X l Z μs μ') :
    VdVWWeakConvergenceSignedBoundedContinuousVaryingDomains Ω μs X l
      ⟨μ'.map Z, Measure.isProbabilityMeasure_map h.aemeasurable_limit⟩ :=
  VdVWWeakConvergenceProbabilityMeasures.to_signedBoundedContinuousVaryingDomains_of_maps_aemeasurable
    (Ω := Ω) (μs := μs) (X := X)
    (fun i => h.forall_aemeasurable i) h.tendsto

/--
Varying-domain convergence in VdV&W outer probability is invariant under
sample-wise almost-everywhere equality.

This is the basic bridge needed when a textbook `P`-measurable object is only
available as a null-measurable statistic on the completed product space: it may
be replaced by an a.e.-equal measurable representative without changing the
outer-probability convergence assertion.
-/
theorem VdVWConvergesInOuterProbabilityConst.congr_ae
    {ι : Type w} {Ω : ι -> Type u} {D : Type v}
    [PseudoMetricSpace D] [∀ i, MeasurableSpace (Ω i)]
    {μs : (i : ι) -> Measure (Ω i)}
    {X Y : (i : ι) -> Ω i -> D} {l : Filter ι} {c : D}
    (hXY : ∀ i, X i =ᵐ[μs i] Y i)
    (hX_outer :
      VdVWConvergesInOuterProbabilityConst Ω (fun _ => inferInstance) μs X l c) :
    VdVWConvergesInOuterProbabilityConst Ω (fun _ => inferInstance) μs Y l c := by
  intro ε hε
  have hprob :
      (fun i =>
        @VdVWOuterProbability (Ω i) inferInstance (μs i)
          {ω | ε < dist (Y i ω) c}) =
      (fun i =>
        @VdVWOuterProbability (Ω i) inferInstance (μs i)
          {ω | ε < dist (X i ω) c}) := by
    funext i
    unfold VdVWOuterProbability
    exact measure_congr ((hXY i).mono fun ω hω => by
      apply propext
      change (ε < dist (Y i ω) c) ↔ (ε < dist (X i ω) c)
      rw [← hω])
  simpa [hprob] using hX_outer ε hε

/--
Real-valued varying-domain convergence in VdV&W outer probability to a
constant implies weak convergence of the pushforward laws to the Dirac law.

This is the law-convergence bridge needed for sample-size-varying endpoints
such as the finite-product centered suprema in Theorem 2.4.3.  The proof uses
bounded-continuous test functions: continuity turns outer-probability
convergence of `X_i` into outer-probability convergence of
`|f(X_i)-f(c)|`, and the existing bounded nonnegative expectation bridge
upgrades that to convergence of test integrals.
-/
theorem
    VdVWConvergesInOuterProbabilityConst.to_weakConvergenceProbabilityMeasures_map_dirac_real
    {ι : Type w} {Ω : ι -> Type u}
    [∀ i, MeasurableSpace (Ω i)]
    {μs : (i : ι) -> Measure (Ω i)} [∀ i, IsProbabilityMeasure (μs i)]
    {X : (i : ι) -> Ω i -> ℝ} {l : Filter ι} {c : ℝ}
    (hX_outer :
      VdVWConvergesInOuterProbabilityConst Ω (fun _ => inferInstance) μs X l c)
    (hX_meas : ∀ i, Measurable (X i)) :
    VdVWWeakConvergenceProbabilityMeasures
      (fun i =>
        ⟨Measure.map (X i) (μs i),
          Measure.isProbabilityMeasure_map (hX_meas i).aemeasurable⟩)
      l
      ⟨Measure.dirac c, Measure.dirac.isProbabilityMeasure⟩ := by
  classical
  rw [vdVWWeakConvergenceProbabilityMeasures_iff_forall_integral_tendsto]
  intro f
  let Y : (i : ι) -> Ω i -> ℝ :=
    fun i ω => |f (X i ω) - f c|
  have hY_outer :
      VdVWConvergesInOuterProbabilityConst Ω (fun _ => inferInstance) μs
        Y l (0 : ℝ) := by
    intro ε hε
    rcases Metric.continuousAt_iff.mp f.continuous.continuousAt ε hε with
      ⟨δ, hδ_pos, hδ⟩
    have hδ_half_pos : 0 < δ / 2 := half_pos hδ_pos
    have htail := hX_outer (δ / 2) hδ_half_pos
    refine
      tendsto_of_tendsto_of_tendsto_of_le_of_le'
        (show Tendsto (fun _ : ι => (0 : ℝ≥0∞)) l (𝓝 0) from
          tendsto_const_nhds)
        htail
        (Eventually.of_forall fun _ => bot_le)
        ?_
    exact Eventually.of_forall fun i => by
      dsimp [VdVWOuterProbability]
      refine measure_mono ?_
      intro ω hω
      have hY_bad : ε < |f (X i ω) - f c| := by
        simpa [Y, Real.dist_eq, sub_zero, abs_of_nonneg (abs_nonneg _)] using hω
      have hnot_small : ¬ dist (X i ω) c < δ := by
        intro hsmall
        have hf_small : dist (f (X i ω)) (f c) < ε := hδ hsmall
        have habs_small : |f (X i ω) - f c| < ε := by
          simpa [Real.dist_eq] using hf_small
        exact (not_lt_of_ge hY_bad.le) habs_small
      have hδ_le : δ ≤ dist (X i ω) c := le_of_not_gt hnot_small
      have hδ_half_lt_delta : δ / 2 < δ := by linarith
      have hδ_half_lt : δ / 2 < dist (X i ω) c :=
        lt_of_lt_of_le hδ_half_lt_delta hδ_le
      simpa [Real.dist_eq] using hδ_half_lt
  have hY_meas : ∀ i, Measurable (Y i) := by
    intro i
    exact ((f.continuous.measurable.comp (hX_meas i)).sub measurable_const).abs
  have hY_nonneg : ∀ i (ω : Ω i), 0 ≤ Y i ω := by
    intro i ω
    exact abs_nonneg _
  have hY_le : ∀ i (ω : Ω i), Y i ω ≤ 2 * ‖f‖ := by
    intro i ω
    simpa [Y, Real.dist_eq] using f.dist_le_two_norm (X i ω) c
  have hY_integrable : ∀ i, Integrable (Y i) (μs i) := by
    intro i
    exact Integrable.of_bound (hY_meas i).aestronglyMeasurable (2 * ‖f‖)
      (Eventually.of_forall fun ω => by
        simpa [Real.norm_eq_abs, abs_of_nonneg (hY_nonneg i ω)] using
          hY_le i ω)
  have hY_int_tendsto :
      Tendsto (fun i => ∫ ω, Y i ω ∂(μs i)) l (𝓝 0) :=
    tendsto_integral_of_VdVWConvergesInOuterProbabilityConst_zero_of_bounded_nonneg
      μs (fun i => inferInstance) hY_outer hY_meas hY_integrable hY_nonneg hY_le
  have hdiff_tendsto :
      Tendsto
        (fun i => ∫ ω, (f (X i ω) - f c) ∂(μs i))
        l (𝓝 0) := by
    rw [tendsto_zero_iff_norm_tendsto_zero]
    refine squeeze_zero (fun i => norm_nonneg _) ?_ hY_int_tendsto
    intro i
    calc
      ‖∫ ω, (f (X i ω) - f c) ∂(μs i)‖
          ≤ ∫ ω, ‖f (X i ω) - f c‖ ∂(μs i) :=
            norm_integral_le_integral_norm _
      _ = ∫ ω, Y i ω ∂(μs i) := by
            simp [Y, Real.norm_eq_abs]
  have hsource_tendsto :
      Tendsto (fun i => ∫ ω, f (X i ω) ∂(μs i)) l (𝓝 (f c)) := by
    have hdiff_eq :
        (fun i => ∫ ω, (f (X i ω) - f c) ∂(μs i)) =
          fun i => (∫ ω, f (X i ω) ∂(μs i)) - f c := by
      funext i
      have hfX_int : Integrable (fun ω => f (X i ω)) (μs i) :=
        Integrable.of_bound
          ((f.continuous.measurable.comp (hX_meas i)).aestronglyMeasurable)
          ‖f‖
          (Eventually.of_forall fun ω => f.norm_coe_le_norm (X i ω))
      have hconst_int : Integrable (fun _ : Ω i => f c) (μs i) :=
        integrable_const (f c)
      haveI : IsProbabilityMeasure (μs i) := inferInstance
      rw [integral_sub hfX_int hconst_int]
      simp
    have hdiff' :
        Tendsto (fun i => (∫ ω, f (X i ω) ∂(μs i)) - f c) l (𝓝 0) := by
      simpa [hdiff_eq] using hdiff_tendsto
    have hadd :=
      hdiff'.add
        (show Tendsto (fun _ : ι => f c) l (𝓝 (f c)) from
          tendsto_const_nhds)
    simpa [sub_add_cancel] using hadd
  have hsource_map :
      (fun i => ∫ s, f s ∂(Measure.map (X i) (μs i))) =
        fun i => ∫ ω, f (X i ω) ∂(μs i) := by
    funext i
    exact integral_map (hX_meas i).aemeasurable
      f.continuous.measurable.aestronglyMeasurable
  have htarget_dirac :
      (∫ s, f s ∂(Measure.dirac c : Measure ℝ)) = f c := by
    exact
      (integral_dirac' (fun s : ℝ => f s) c
        f.continuous.stronglyMeasurable)
  change
    Tendsto (fun i => ∫ s, f s ∂(Measure.map (X i) (μs i))) l
      (𝓝 (∫ s, f s ∂(Measure.dirac c : Measure ℝ)))
  simpa [hsource_map, htarget_dirac] using hsource_tendsto

/--
Null-measurable real-valued varying-domain convergence in VdV&W outer
probability to a constant implies weak convergence of the pushforward laws to
the Dirac law.

The proof replaces each statistic by its mathlib `AEMeasurable.mk`
representative, uses `VdVWConvergesInOuterProbabilityConst.congr_ae`, and then
transports the pushforward laws back by `Measure.map_congr`.
-/
theorem
    VdVWConvergesInOuterProbabilityConst.to_weakConvergenceProbabilityMeasures_map_dirac_real_of_nullMeasurable
    {ι : Type w} {Ω : ι -> Type u}
    [∀ i, MeasurableSpace (Ω i)]
    {μs : (i : ι) -> Measure (Ω i)} [∀ i, IsProbabilityMeasure (μs i)]
    {X : (i : ι) -> Ω i -> ℝ} {l : Filter ι} {c : ℝ}
    (hX_outer :
      VdVWConvergesInOuterProbabilityConst Ω (fun _ => inferInstance) μs X l c)
    (hX_null : ∀ i, NullMeasurable (X i) (μs i)) :
    VdVWWeakConvergenceProbabilityMeasures
      (fun i =>
        ⟨Measure.map (X i) (μs i),
          Measure.isProbabilityMeasure_map ((hX_null i).aemeasurable)⟩)
      l
      ⟨Measure.dirac c, Measure.dirac.isProbabilityMeasure⟩ := by
  classical
  let Xmk : (i : ι) -> Ω i -> ℝ :=
    fun i => ((hX_null i).aemeasurable).mk (X i)
  have hXmk_meas : ∀ i, Measurable (Xmk i) := by
    intro i
    exact ((hX_null i).aemeasurable).measurable_mk
  have hX_to_mk : ∀ i, X i =ᵐ[μs i] Xmk i := by
    intro i
    exact ((hX_null i).aemeasurable).ae_eq_mk
  have hXmk_outer :
      VdVWConvergesInOuterProbabilityConst Ω (fun _ => inferInstance) μs
        Xmk l c :=
    VdVWConvergesInOuterProbabilityConst.congr_ae hX_to_mk hX_outer
  have hweak_mk :
      VdVWWeakConvergenceProbabilityMeasures
        (fun i =>
          ⟨Measure.map (Xmk i) (μs i),
            Measure.isProbabilityMeasure_map (hXmk_meas i).aemeasurable⟩)
        l
        ⟨Measure.dirac c, Measure.dirac.isProbabilityMeasure⟩ :=
    VdVWConvergesInOuterProbabilityConst.to_weakConvergenceProbabilityMeasures_map_dirac_real
      hXmk_outer hXmk_meas
  have hprob_eq :
      (fun i =>
        (⟨Measure.map (Xmk i) (μs i),
          Measure.isProbabilityMeasure_map (hXmk_meas i).aemeasurable⟩ :
            ProbabilityMeasure ℝ)) =
      (fun i =>
        (⟨Measure.map (X i) (μs i),
          Measure.isProbabilityMeasure_map ((hX_null i).aemeasurable)⟩ :
            ProbabilityMeasure ℝ)) := by
    funext i
    ext s hs
    change Measure.map (Xmk i) (μs i) s = Measure.map (X i) (μs i) s
    rw [Measure.map_congr (hX_to_mk i)]
  simpa [hprob_eq] using hweak_mk

/--
A.e.-measurable real-valued varying-domain convergence in VdV&W outer
probability to a constant implies weak convergence of the pushforward laws to
the Dirac law.

This is the direct a.e.-measurable convenience form of
`...map_dirac_real_of_nullMeasurable`; it avoids forcing callers to manually
convert `AEMeasurable` statistics to `NullMeasurable` before using the
Chapter 1 Dirac-law bridge.
-/
theorem
    VdVWConvergesInOuterProbabilityConst.to_weakConvergenceProbabilityMeasures_map_dirac_real_of_aemeasurable
    {ι : Type w} {Ω : ι -> Type u}
    [∀ i, MeasurableSpace (Ω i)]
    {μs : (i : ι) -> Measure (Ω i)} [∀ i, IsProbabilityMeasure (μs i)]
    {X : (i : ι) -> Ω i -> ℝ} {l : Filter ι} {c : ℝ}
    (hX_outer :
      VdVWConvergesInOuterProbabilityConst Ω (fun _ => inferInstance) μs X l c)
    (hX_aemeas : ∀ i, AEMeasurable (X i) (μs i)) :
    VdVWWeakConvergenceProbabilityMeasures
      (fun i =>
        ⟨Measure.map (X i) (μs i),
          Measure.isProbabilityMeasure_map (hX_aemeas i)⟩)
      l
      ⟨Measure.dirac c, Measure.dirac.isProbabilityMeasure⟩ := by
  simpa using
    (VdVWConvergesInOuterProbabilityConst.to_weakConvergenceProbabilityMeasures_map_dirac_real_of_nullMeasurable
      (Ω := Ω) (μs := μs) (X := X) hX_outer
      (fun i => (hX_aemeas i).nullMeasurable))

/--
Real-valued varying-domain convergence in outer probability to a constant
feeds the proof-carrying signed bounded-continuous varying-domain
weak-convergence package.
-/
theorem
    VdVWConvergesInOuterProbabilityConst.to_signedBoundedContinuousVaryingDomains_real
    {ι : Type w} {Ω : ι -> Type u}
    [∀ i, MeasurableSpace (Ω i)]
    {μs : (i : ι) -> Measure (Ω i)} [∀ i, IsProbabilityMeasure (μs i)]
    {X : (i : ι) -> Ω i -> ℝ} {l : Filter ι} {c : ℝ}
    (hX_outer :
      VdVWConvergesInOuterProbabilityConst Ω (fun _ => inferInstance) μs X l c)
    (hX_meas : ∀ i, Measurable (X i)) :
    VdVWWeakConvergenceSignedBoundedContinuousVaryingDomains Ω μs X l
      ⟨Measure.dirac c, Measure.dirac.isProbabilityMeasure⟩ :=
  VdVWWeakConvergenceProbabilityMeasures.to_signedBoundedContinuousVaryingDomains_of_maps
    hX_meas
    (VdVWConvergesInOuterProbabilityConst.to_weakConvergenceProbabilityMeasures_map_dirac_real
      hX_outer hX_meas)

/--
Null-measurable real-valued varying-domain convergence in outer probability to
a constant feeds the proof-carrying signed bounded-continuous varying-domain
weak-convergence package.
-/
theorem
    VdVWConvergesInOuterProbabilityConst.to_signedBoundedContinuousVaryingDomains_real_of_nullMeasurable
    {ι : Type w} {Ω : ι -> Type u}
    [∀ i, MeasurableSpace (Ω i)]
    {μs : (i : ι) -> Measure (Ω i)} [∀ i, IsProbabilityMeasure (μs i)]
    {X : (i : ι) -> Ω i -> ℝ} {l : Filter ι} {c : ℝ}
    (hX_outer :
      VdVWConvergesInOuterProbabilityConst Ω (fun _ => inferInstance) μs X l c)
    (hX_null : ∀ i, NullMeasurable (X i) (μs i)) :
    VdVWWeakConvergenceSignedBoundedContinuousVaryingDomains Ω μs X l
      ⟨Measure.dirac c, Measure.dirac.isProbabilityMeasure⟩ :=
  VdVWWeakConvergenceProbabilityMeasures.to_signedBoundedContinuousVaryingDomains_of_maps_nullMeasurable
    hX_null
    (VdVWConvergesInOuterProbabilityConst.to_weakConvergenceProbabilityMeasures_map_dirac_real_of_nullMeasurable
      hX_outer hX_null)

/--
A.e.-measurable real-valued varying-domain convergence in outer probability to
a constant feeds the proof-carrying signed bounded-continuous varying-domain
weak-convergence package.

This is the a.e.-measurable endpoint form needed for sample-size-varying
statistics whose mathlib law statements carry `AEMeasurable` hypotheses rather
than ordinary measurability.
-/
theorem
    VdVWConvergesInOuterProbabilityConst.to_signedBoundedContinuousVaryingDomains_real_of_aemeasurable
    {ι : Type w} {Ω : ι -> Type u}
    [∀ i, MeasurableSpace (Ω i)]
    {μs : (i : ι) -> Measure (Ω i)} [∀ i, IsProbabilityMeasure (μs i)]
    {X : (i : ι) -> Ω i -> ℝ} {l : Filter ι} {c : ℝ}
    (hX_outer :
      VdVWConvergesInOuterProbabilityConst Ω (fun _ => inferInstance) μs X l c)
    (hX_aemeas : ∀ i, AEMeasurable (X i) (μs i)) :
    VdVWWeakConvergenceSignedBoundedContinuousVaryingDomains Ω μs X l
      ⟨Measure.dirac c, Measure.dirac.isProbabilityMeasure⟩ :=
  VdVWWeakConvergenceProbabilityMeasures.to_signedBoundedContinuousVaryingDomains_of_maps_aemeasurable
    hX_aemeas
    (VdVWConvergesInOuterProbabilityConst.to_weakConvergenceProbabilityMeasures_map_dirac_real_of_aemeasurable
      hX_outer hX_aemeas)

/--
Has-law form of the signed-outer bounded-continuous weak-convergence bridge.

This is the most convenient form for probability-theory arguments: the law
assumption supplies the measure-map identity, while measurability supplies the
ordinary integral collapse of the signed outer expectation.
-/
theorem VdVWWeakConvergenceProbabilityMeasures.to_signedOuterBoundedContinuous_of_hasLaw
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S}
    (hX : ∀ i, Measurable (X i))
    {νs : ι -> ProbabilityMeasure S} {l : Filter ι}
    {μ : ProbabilityMeasure S}
    (hν : VdVWWeakConvergenceProbabilityMeasures νs l μ)
    (hlaw : ∀ i, HasLaw (X i) (νs i : Measure S) (μs i)) :
    VdVWWeakConvergenceSignedOuterBoundedContinuous μs X l μ := by
  intro f
  have houter :
      (fun i =>
        VdVWSignedOuterExpectationPosNeg (μs i) (fun ω => f (X i ω))) =
        fun i => ∫ s, f s ∂(νs i : Measure S) := by
    funext i
    haveI : IsFiniteMeasure (μs i) := (hlaw i).isFiniteMeasure
    calc
      VdVWSignedOuterExpectationPosNeg (μs i) (fun ω => f (X i ω))
          = ∫ ω, f (X i ω) ∂μs i := by
            exact VdVWSignedOuterExpectationPosNeg_eq_integral_of_boundedContinuous_comp
              (μ := μs i) (X := X i) (hX i) f
      _ = ∫ s, f s ∂Measure.map (X i) (μs i) := by
            exact (integral_map (hX i).aemeasurable
              f.continuous.measurable.aestronglyMeasurable).symm
      _ = ∫ s, f s ∂(νs i : Measure S) := by
            rw [(hlaw i).map_eq]
  simpa [VdVWWeakConvergenceSignedOuterBoundedContinuous, houter] using
    (vdVWWeakConvergenceProbabilityMeasures_iff_forall_integral_tendsto.mp hν f)

/--
Has-law weak convergence gives the proof-carrying signed bounded-continuous
arbitrary-map layer.
-/
theorem
    VdVWWeakConvergenceProbabilityMeasures.to_signedBoundedContinuousArbitraryMap_of_hasLaw
    {Ω : Type u} {S : Type v} {ι : Type w}
    [MeasurableSpace Ω] [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S]
    {μs : ι -> Measure Ω} {X : ι -> Ω -> S}
    (hX : ∀ i, Measurable (X i))
    {νs : ι -> ProbabilityMeasure S} {l : Filter ι}
    {μ : ProbabilityMeasure S}
    (hweak : VdVWWeakConvergenceProbabilityMeasures νs l μ)
    (hlaw : ∀ i, HasLaw (X i) (νs i : Measure S) (μs i)) :
    VdVWWeakConvergenceSignedBoundedContinuousArbitraryMap μs X l μ :=
  { weakConvergence :=
      hweak.to_signedOuterBoundedContinuous_of_hasLaw hX hlaw
    asymptoticMeasurability :=
      VdVWAsymptoticallyMeasurableSignedBoundedContinuous.of_forall_measurable hX }

/--
VdV&W bounded-Lipschitz test-function criterion for measure-level weak
convergence.

The boundedness hypothesis is the mathlib one: the real-valued test function
has bounded range diameter.  This is a proof-hole-free wrapper around the
pinned portmanteau API.
-/
theorem vdVWWeakConvergenceProbabilityMeasures_iff_forall_bounded_lipschitz_integral_tendsto
    {S : Type u} {ι : Type v} [MeasurableSpace S] [PseudoEMetricSpace S]
    [OpensMeasurableSpace S]
    {μs : ι -> ProbabilityMeasure S} {l : Filter ι} [l.IsCountablyGenerated]
    {μ : ProbabilityMeasure S} :
    VdVWWeakConvergenceProbabilityMeasures μs l μ ↔
      ∀ f : S → ℝ, (∃ C : ℝ, ∀ x y, dist (f x) (f y) ≤ C) →
        (∃ L, LipschitzWith L f) →
          Tendsto (fun i => ∫ s, f s ∂(μs i : Measure S)) l
            (𝓝 (∫ s, f s ∂(μ : Measure S))) := by
  exact MeasureTheory.tendsto_iff_forall_lipschitz_integral_tendsto

/--
VdV&W Lemma 1.3.1, closed-set step: if every bounded-continuous real test is
measurable for a sigma-field `m`, then every closed set is `m`-measurable.

The proof follows the textbook distance-to-a-closed-set argument using
`x ↦ min (Metric.infDist x F) 1`.
-/
theorem vdVW131_measurableSet_isClosed_of_forall_boundedContinuous_measurable
    {S : Type u} [PseudoMetricSpace S] {m : MeasurableSpace S}
    (h : ∀ f : S →ᵇ ℝ, @Measurable S ℝ m (borel ℝ) f)
    {F : Set S} (hF : IsClosed F) :
    MeasurableSet[m] F := by
  by_cases hFne : F.Nonempty
  · let g : S →ᵇ ℝ :=
      BoundedContinuousFunction.ofNormedAddCommGroup
        (fun x => min (Metric.infDist x F) 1)
        ((Metric.continuous_infDist_pt F).min continuous_const)
        1
        (by
          intro x
          rw [Real.norm_eq_abs]
          have hnonneg : 0 ≤ min (Metric.infDist x F) 1 :=
            le_min Metric.infDist_nonneg zero_le_one
          exact abs_le.mpr
            ⟨le_trans (by norm_num : (-1 : ℝ) ≤ 0) hnonneg,
              min_le_right _ _⟩)
    have hg_meas : @Measurable S ℝ m (borel ℝ) g := h g
    have hpre : MeasurableSet[m] (g ⁻¹' ({0} : Set ℝ)) :=
      hg_meas (measurableSet_singleton (0 : ℝ))
    have hEq : F = g ⁻¹' ({0} : Set ℝ) := by
      ext x
      simp only [Set.mem_preimage, Set.mem_singleton_iff]
      constructor
      · intro hx
        have hzero : Metric.infDist x F = 0 := Metric.infDist_zero_of_mem hx
        simp [g, hzero]
      · intro hx
        have hmin : min (Metric.infDist x F) 1 = 0 := by simpa [g] using hx
        have hdistzero : Metric.infDist x F = 0 := by
          by_contra hne
          have hpos : 0 < Metric.infDist x F :=
            lt_of_le_of_ne Metric.infDist_nonneg (Ne.symm hne)
          have hminpos : 0 < min (Metric.infDist x F) 1 :=
            lt_min hpos zero_lt_one
          linarith
        exact (hF.mem_iff_infDist_zero hFne).2 hdistzero
    simpa [hEq] using hpre
  · have hEmpty : F = ∅ := by
      ext x
      constructor
      · intro hx
        exact (hFne ⟨x, hx⟩).elim
      · intro hx
        cases hx
    simp [hEmpty]

/--
VdV&W Lemma 1.3.1: on a metric space, the Borel sigma-field is contained in
any sigma-field that makes every bounded-continuous real function measurable.
-/
theorem vdVW131_borel_le_of_forall_boundedContinuous_measurable
    {S : Type u} [PseudoMetricSpace S] {m : MeasurableSpace S}
    (h : ∀ f : S →ᵇ ℝ, @Measurable S ℝ m (borel ℝ) f) :
    borel S ≤ m := by
  rw [borel_eq_generateFrom_isClosed]
  exact MeasurableSpace.generateFrom_le fun F hF =>
    vdVW131_measurableSet_isClosed_of_forall_boundedContinuous_measurable h hF

/--
VdV&W Lemma 1.3.1, least-sigma-field formulation: the Borel sigma-field on a
metric space is the least sigma-field making all bounded-continuous real
functions measurable.
-/
theorem vdVW131_borel_le_iff_forall_boundedContinuous_measurable
    {S : Type u} [PseudoMetricSpace S] {m : MeasurableSpace S} :
    borel S ≤ m ↔
      ∀ f : S →ᵇ ℝ, @Measurable S ℝ m (borel ℝ) f := by
  constructor
  · intro hm f
    have hf : @Measurable S ℝ (borel S) (borel ℝ) f :=
      f.continuous.borel_measurable
    exact hf.mono hm le_rfl
  · exact vdVW131_borel_le_of_forall_boundedContinuous_measurable

/--
VdV&W Lemma 1.3.12(i): finite Borel measures are determined by their
bounded-continuous real integrals.

This is the exact finite-measure uniqueness direction available in pinned
mathlib under the `HasOuterApproxClosed` regularity assumption.
-/
theorem vdVW1312_measure_ext_of_forall_boundedContinuous_integral_eq
    {S : Type u} [MeasurableSpace S] [TopologicalSpace S]
    [HasOuterApproxClosed S] [BorelSpace S]
    {μ ν : Measure S} [IsFiniteMeasure μ] [IsFiniteMeasure ν]
    (h : ∀ f : S →ᵇ ℝ, ∫ s, f s ∂μ = ∫ s, f s ∂ν) :
    μ = ν := by
  exact MeasureTheory.ext_of_forall_integral_eq_of_IsFiniteMeasure h

/--
Portmanteau closed-set implication for the measure-level VdV&W weak convergence
wrapper.

This is the pinned-mathlib implication `(T) -> (C)` for probability measures.
The exact arbitrary-map/outer-probability Portmanteau theorem remains a
separate VdV&W-specific layer.
-/
theorem VdVWWeakConvergenceProbabilityMeasures.limsup_measure_closed_le
    {S : Type u} {ι : Type v} [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S] [HasOuterApproxClosed S]
    {μs : ι -> ProbabilityMeasure S} {l : Filter ι}
    {μ : ProbabilityMeasure S}
    (h : VdVWWeakConvergenceProbabilityMeasures μs l μ)
    {F : Set S} (hF : IsClosed F) :
    (l.limsup fun i => (μs i : Measure S) F) ≤ (μ : Measure S) F := by
  exact ProbabilityMeasure.limsup_measure_closed_le_of_tendsto h hF

/--
Portmanteau open-set implication for the measure-level VdV&W weak convergence
wrapper.

This is the pinned-mathlib implication `(T) -> (O)` for probability measures.
-/
theorem VdVWWeakConvergenceProbabilityMeasures.le_liminf_measure_open
    {S : Type u} {ι : Type v} [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S] [HasOuterApproxClosed S]
    {μs : ι -> ProbabilityMeasure S} {l : Filter ι}
    {μ : ProbabilityMeasure S}
    (h : VdVWWeakConvergenceProbabilityMeasures μs l μ)
    {G : Set S} (hG : IsOpen G) :
    (μ : Measure S) G ≤ l.liminf fun i => (μs i : Measure S) G := by
  exact ProbabilityMeasure.le_liminf_measure_open_of_tendsto h hG

/--
Portmanteau continuity-set implication for the measure-level VdV&W weak
convergence wrapper.

If the limiting probability gives zero mass to the frontier of a set, then the
probabilities of that set converge.  This is the ordinary measurable
probability-measure layer; arbitrary-map and outer-probability continuity-set
forms remain separate VdV&W-specific primitives.
-/
theorem VdVWWeakConvergenceProbabilityMeasures.tendsto_measure_of_null_frontier
    {S : Type u} {ι : Type v} [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S] [HasOuterApproxClosed S]
    {μs : ι -> ProbabilityMeasure S} {l : Filter ι}
    {μ : ProbabilityMeasure S}
    (h : VdVWWeakConvergenceProbabilityMeasures μs l μ)
    {E : Set S} (hE : (μ : Measure S) (frontier E) = 0) :
    Tendsto (fun i => (μs i : Measure S) E) l
      (𝓝 ((μ : Measure S) E)) := by
  exact ProbabilityMeasure.tendsto_measure_of_null_frontier_of_tendsto' h hE

/--
Closed-set Portmanteau converse for the measure-level VdV&W weak-convergence
wrapper.

For countably generated filters, the limsup inequality for every closed set
implies weak convergence of probability measures.  This is the pinned-mathlib
`(C) -> (T)` direction in VdV&W-local notation.
-/
theorem vdVWWeakConvergenceProbabilityMeasures_of_forall_isClosed_limsup_measure_le
    {S : Type u} {ι : Type v} [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S]
    {μs : ι -> ProbabilityMeasure S} {l : Filter ι} [l.IsCountablyGenerated]
    {μ : ProbabilityMeasure S}
    (h : ∀ F : Set S, IsClosed F ->
      l.limsup (fun i => (μs i : Measure S) F) ≤ (μ : Measure S) F) :
    VdVWWeakConvergenceProbabilityMeasures μs l μ := by
  exact MeasureTheory.tendsto_of_forall_isClosed_limsup_le' h

/--
Open-set Portmanteau converse for the measure-level VdV&W weak-convergence
wrapper.

For countably generated filters, the liminf inequality for every open set
implies weak convergence of probability measures.
-/
theorem vdVWWeakConvergenceProbabilityMeasures_of_forall_isOpen_measure_le_liminf
    {S : Type u} {ι : Type v} [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S]
    {μs : ι -> ProbabilityMeasure S} {l : Filter ι} [l.IsCountablyGenerated]
    {μ : ProbabilityMeasure S}
    (h : ∀ G : Set S, IsOpen G ->
      (μ : Measure S) G ≤ l.liminf (fun i => (μs i : Measure S) G)) :
    VdVWWeakConvergenceProbabilityMeasures μs l μ := by
  exact MeasureTheory.tendsto_of_forall_isOpen_le_liminf' h

/--
Convergence-determining π-system criterion for the measure-level VdV&W weak
convergence wrapper.

If a π-system consists of measurable sets, locally approximates open
neighborhoods, and the probabilities of all π-system sets converge, then the
probability measures converge weakly.  This is the ordinary measure-level
cylinder/π-system tool used before FDD and product-space arguments; arbitrary
nonmeasurable process statements remain separate primitives.
-/
theorem vdVWWeakConvergenceProbabilityMeasures_of_piSystem_tendsto
    {S : Type u} {ι : Type v} [MeasurableSpace S] [TopologicalSpace S]
    [SecondCountableTopology S] [OpensMeasurableSpace S]
    {C : Set (Set S)} (hC : IsPiSystem C)
    {μs : ι -> ProbabilityMeasure S} {l : Filter ι} [l.IsCountablyGenerated]
    {μ : ProbabilityMeasure S}
    (hmeas : ∀ s ∈ C, MeasurableSet s)
    (hlocal :
      ∀ u : Set S, IsOpen u -> ∀ x ∈ u,
        ∃ s ∈ C, s ∈ 𝓝 x ∧ s ⊆ u)
    (h : ∀ s ∈ C, Tendsto (fun i => μs i s) l (𝓝 (μ s))) :
    VdVWWeakConvergenceProbabilityMeasures μs l μ := by
  exact hC.tendsto_probabilityMeasure_of_tendsto_of_mem hmeas hlocal h

/--
Tightness of a family of probability measures, expressed through mathlib's
`IsTightMeasureSet` on the underlying measures.

This names the measure-level foundation used by VdV&W Prokhorov/tightness
statements.  Stochastic-process asymptotic tightness of arbitrary maps is a
separate local primitive.
-/
def VdVWProbabilityMeasuresTight
    {S : Type u} [MeasurableSpace S] [TopologicalSpace S]
    (A : Set (ProbabilityMeasure S)) : Prop :=
  IsTightMeasureSet {((μ : ProbabilityMeasure S) : Measure S) | μ ∈ A}

/--
Measure-level asymptotic tightness of a family of probability measures along a
filter: eventually, all measures put arbitrarily small mass outside one compact
set.

This is the ordinary probability-measure foundation.  The VdV&W arbitrary-map
and nonmeasurable process asymptotic-tightness clauses remain separate
primitives.
-/
def VdVWProbabilityMeasuresAsymptoticallyTight
    {ι : Type v} {S : Type u} [MeasurableSpace S] [TopologicalSpace S]
    (μs : ι -> ProbabilityMeasure S) (l : Filter ι) : Prop :=
  ∀ ε, 0 < ε ->
    ∃ K : Set S, IsCompact K ∧
      ∀ᶠ i in l, ((μs i : ProbabilityMeasure S) : Measure S) (Kᶜ) ≤ ε

/--
Measure-level asymptotic tightness is stable under passing to a finer index
filter.
-/
theorem VdVWProbabilityMeasuresAsymptoticallyTight.mono_filter
    {ι : Type v} {S : Type u} [MeasurableSpace S] [TopologicalSpace S]
    {μs : ι -> ProbabilityMeasure S} {l l' : Filter ι}
    (hμs : VdVWProbabilityMeasuresAsymptoticallyTight μs l)
    (hl : l' ≤ l) :
    VdVWProbabilityMeasuresAsymptoticallyTight μs l' := by
  intro ε hε
  rcases hμs ε hε with ⟨K, hK, htail⟩
  exact ⟨K, hK, htail.filter_mono hl⟩

/--
Measure-level asymptotic tightness is unchanged by eventually equal
probability-measure families.
-/
theorem VdVWProbabilityMeasuresAsymptoticallyTight.congr_eventually
    {ι : Type v} {S : Type u} [MeasurableSpace S] [TopologicalSpace S]
    {μs νs : ι -> ProbabilityMeasure S} {l : Filter ι}
    (hμs : VdVWProbabilityMeasuresAsymptoticallyTight μs l)
    (h_eq : ∀ᶠ i in l, νs i = μs i) :
    VdVWProbabilityMeasuresAsymptoticallyTight νs l := by
  intro ε hε
  rcases hμs ε hε with ⟨K, hK, htail⟩
  refine ⟨K, hK, ?_⟩
  filter_upwards [htail, h_eq] with i hi hνμ
  simpa [hνμ] using hi

/--
Measure-level asymptotic tightness is stable under reindexing along a map that
tends to the original index filter.  This is the basic net/subsequence handoff
for the ordinary probability-measure asymptotic-tightness layer.
-/
theorem VdVWProbabilityMeasuresAsymptoticallyTight.comp_tendsto
    {ι : Type v} {κ : Type w} {S : Type u}
    [MeasurableSpace S] [TopologicalSpace S]
    {μs : ι -> ProbabilityMeasure S} {l : Filter ι}
    {φ : κ -> ι} {l' : Filter κ}
    (hμs : VdVWProbabilityMeasuresAsymptoticallyTight μs l)
    (hφ : Tendsto φ l' l) :
    VdVWProbabilityMeasuresAsymptoticallyTight (fun j => μs (φ j)) l' := by
  intro ε hε
  rcases hμs ε hε with ⟨K, hK, htail⟩
  exact ⟨K, hK, hφ.eventually htail⟩

/--
A singleton family of probability measures is tight on complete separable
metric-type spaces.

This is the local VdV&W tightness wrapper around mathlib's singleton tightness
theorem for finite measures.
-/
theorem vdVWProbabilityMeasuresTight_singleton
    {S : Type u} [MeasurableSpace S] [TopologicalSpace S]
    [IsCompletelyPseudoMetrizableSpace S] [SecondCountableTopology S] [BorelSpace S]
    (μ : ProbabilityMeasure S) :
    VdVWProbabilityMeasuresTight ({μ} : Set (ProbabilityMeasure S)) := by
  simpa [VdVWProbabilityMeasuresTight] using
    (isTightMeasureSet_singleton (μ := (μ : Measure S)))

/--
VdV&W Lemma 1.3.2 tightness component: on complete separable metric-type
Borel spaces, every Borel probability measure is tight.

The full VdV&W pre-tight/separable/Polish-measure equivalence still needs
local definitions for those measure-level notions; this theorem records the
compiled mathlib-backed tightness direction already available for probability
measures.
-/
theorem vdVW132_complete_separable_probabilityMeasure_tight
    {S : Type u} [MeasurableSpace S] [TopologicalSpace S]
    [IsCompletelyPseudoMetrizableSpace S] [SecondCountableTopology S] [BorelSpace S]
    (μ : ProbabilityMeasure S) :
    VdVWProbabilityMeasuresTight ({μ} : Set (ProbabilityMeasure S)) :=
  vdVWProbabilityMeasuresTight_singleton μ

/--
Compact-set characterization of the VdV&W-local probability-measure tightness
wrapper.
-/
theorem vdVWProbabilityMeasuresTight_iff_exists_compact_measure_compl_le
    {S : Type u} [MeasurableSpace S] [TopologicalSpace S]
    {A : Set (ProbabilityMeasure S)} :
    VdVWProbabilityMeasuresTight A ↔
      ∀ ε, 0 < ε ->
        ∃ K : Set S, IsCompact K ∧
          ∀ μ : ProbabilityMeasure S, μ ∈ A -> (μ : Measure S) (Kᶜ) ≤ ε := by
  constructor
  · intro h ε hε
    rcases
        (isTightMeasureSet_iff_exists_isCompact_measure_compl_le.mp h) ε hε with
      ⟨K, hK, hKμ⟩
    exact ⟨K, hK, fun μ hμA => hKμ (μ : Measure S) ⟨μ, hμA, rfl⟩⟩
  · intro h
    refine isTightMeasureSet_iff_exists_isCompact_measure_compl_le.mpr ?_
    intro ε hε
    rcases h ε hε with ⟨K, hK, hKμ⟩
    refine ⟨K, hK, ?_⟩
    rintro ν ⟨μ, hμA, rfl⟩
    exact hKμ μ hμA

/--
Tightness of an ambient probability-measure family gives asymptotic tightness
for any net that is eventually inside that family.
-/
theorem VdVWProbabilityMeasuresTight.asymptoticallyTight_of_eventually_mem
    {ι : Type v} {S : Type u} [MeasurableSpace S] [TopologicalSpace S]
    {A : Set (ProbabilityMeasure S)} {μs : ι -> ProbabilityMeasure S}
    {l : Filter ι}
    (hA : VdVWProbabilityMeasuresTight A)
    (hmem : ∀ᶠ i in l, μs i ∈ A) :
    VdVWProbabilityMeasuresAsymptoticallyTight μs l := by
  intro ε hε
  rcases
      (vdVWProbabilityMeasuresTight_iff_exists_compact_measure_compl_le.mp hA)
        ε hε with
    ⟨K, hK, hKμ⟩
  refine ⟨K, hK, ?_⟩
  filter_upwards [hmem] with i hi
  exact hKμ (μs i) hi

/--
Tightness of the range of a probability-measure family gives asymptotic
tightness along every filter.
-/
theorem VdVWProbabilityMeasuresAsymptoticallyTight.of_tight_range
    {ι : Type v} {S : Type u} [MeasurableSpace S] [TopologicalSpace S]
    {μs : ι -> ProbabilityMeasure S} {l : Filter ι}
    (hμs : VdVWProbabilityMeasuresTight (Set.range μs)) :
    VdVWProbabilityMeasuresAsymptoticallyTight μs l :=
  hμs.asymptoticallyTight_of_eventually_mem (Eventually.of_forall fun i => ⟨i, rfl⟩)

/--
Sequential weak convergence of ordinary probability measures implies
measure-level asymptotic tightness.

This is the VdV&W-local Prokhorov/tightness consequence for sequences on
complete second-countable pseudo-metric Borel spaces.  It remains
measure-level and does not assert stochastic-process asymptotic tightness for
arbitrary nonmeasurable maps.
-/
theorem VdVWWeakConvergenceProbabilityMeasures.asymptoticallyTight_atTop
    {S : Type u} [MeasurableSpace S] [PseudoMetricSpace S]
    [OpensMeasurableSpace S] [BorelSpace S] [SecondCountableTopology S] [CompleteSpace S]
    {μs : ℕ -> ProbabilityMeasure S} {μ : ProbabilityMeasure S}
    (hμ : VdVWWeakConvergenceProbabilityMeasures μs atTop μ) :
    VdVWProbabilityMeasuresAsymptoticallyTight μs atTop := by
  have hcompact_insert : IsCompact (insert μ (Set.range μs)) :=
    hμ.isCompact_insert_range
  have hclosed_insert : IsClosed (insert μ (Set.range μs)) :=
    hcompact_insert.isClosed
  have hclosure_subset : closure (Set.range μs) ⊆ insert μ (Set.range μs) :=
    closure_minimal (Set.subset_insert μ (Set.range μs)) hclosed_insert
  have hcompact_closure : IsCompact (closure (Set.range μs)) :=
    hcompact_insert.of_isClosed_subset isClosed_closure hclosure_subset
  exact
    VdVWProbabilityMeasuresAsymptoticallyTight.of_tight_range
      (μs := μs) (l := atTop)
      (hμs := by
        simpa [VdVWProbabilityMeasuresTight] using
          (MeasureTheory.isTightMeasureSet_of_isCompact_closure
          (𝓧 := S) (S := Set.range μs) hcompact_closure))

/--
Sequential weak convergence also gives asymptotic tightness after any
subsequence or, more generally, after any reindexing map tending to `atTop`.

This is the ordinary probability-law version of the VdV&W subsequence
tightness handoff.  It remains measure-level, not an arbitrary-map
asymptotic-tightness theorem.
-/
theorem VdVWWeakConvergenceProbabilityMeasures.asymptoticallyTight_comp_tendsto_atTop
    {κ : Type v} {S : Type u} [MeasurableSpace S] [PseudoMetricSpace S]
    [OpensMeasurableSpace S] [BorelSpace S] [SecondCountableTopology S] [CompleteSpace S]
    {μs : ℕ -> ProbabilityMeasure S} {μ : ProbabilityMeasure S}
    {φ : κ -> ℕ} {l : Filter κ}
    (hμ : VdVWWeakConvergenceProbabilityMeasures μs atTop μ)
    (hφ : Tendsto φ l atTop) :
    VdVWProbabilityMeasuresAsymptoticallyTight (fun k => μs (φ k)) l :=
  hμ.asymptoticallyTight_atTop.comp_tendsto hφ

/--
Measure-level asymptotic tightness is preserved by continuous maps.

This is the ordinary continuous-image tightness step used by finite-dimensional
and continuous-mapping arguments.  It does not assert the VdV&W arbitrary-map
process asymptotic-tightness theorem.
-/
theorem VdVWProbabilityMeasuresAsymptoticallyTight.map_continuous
    {ι : Type v} {S : Type u} {T : Type w}
    [MeasurableSpace S] [TopologicalSpace S] [OpensMeasurableSpace S]
    [MeasurableSpace T] [TopologicalSpace T] [BorelSpace T] [T2Space T]
    {μs : ι -> ProbabilityMeasure S} {l : Filter ι}
    {g : S -> T}
    (hμs : VdVWProbabilityMeasuresAsymptoticallyTight μs l)
    (hg : Continuous g) :
    VdVWProbabilityMeasuresAsymptoticallyTight
      (fun i => (μs i).map hg.measurable.aemeasurable) l := by
  intro ε hε
  rcases hμs ε hε with ⟨K, hK, htail⟩
  refine ⟨g '' K, hK.image hg, ?_⟩
  have hmeas : MeasurableSet ((g '' K)ᶜ) :=
    (hK.image hg).isClosed.measurableSet.compl
  have hpre : g ⁻¹' ((g '' K)ᶜ) ⊆ Kᶜ := by
    intro x hx hxK
    exact hx ⟨x, hxK, rfl⟩
  filter_upwards [htail] with i hi
  calc
    (((μs i).map hg.measurable.aemeasurable : ProbabilityMeasure T) : Measure T) ((g '' K)ᶜ)
        = ((μs i : ProbabilityMeasure S) : Measure S) (g ⁻¹' ((g '' K)ᶜ)) := by
          exact ProbabilityMeasure.map_apply' (μs i) hg.measurable.aemeasurable hmeas
    _ ≤ ((μs i : ProbabilityMeasure S) : Measure S) (Kᶜ) := measure_mono hpre
    _ ≤ ε := hi

/--
Continuous images of a weakly convergent sequence are asymptotically tight at
`atTop`.

This is a measure-level Chapter 1 continuous-mapping/tightness foundation.  It
does not assert the full VdV&W arbitrary-map asymptotic-tightness theorem.
-/
theorem VdVWWeakConvergenceProbabilityMeasures.map_asymptoticallyTight_atTop
    {S : Type u} {T : Type v}
    [MeasurableSpace S] [PseudoMetricSpace S] [OpensMeasurableSpace S]
    [BorelSpace S] [SecondCountableTopology S] [CompleteSpace S]
    [MeasurableSpace T] [TopologicalSpace T] [BorelSpace T] [T2Space T]
    {μs : ℕ -> ProbabilityMeasure S} {μ : ProbabilityMeasure S}
    {g : S -> T}
    (hμ : VdVWWeakConvergenceProbabilityMeasures μs atTop μ)
    (hg : Continuous g) :
    VdVWProbabilityMeasuresAsymptoticallyTight
      (fun n => (μs n).map hg.measurable.aemeasurable) atTop :=
  hμ.asymptoticallyTight_atTop.map_continuous hg

/--
Reindexed continuous images of a weakly convergent sequence are
asymptotically tight along any filter tending to `atTop`.

This packages the two standard measure-level steps needed by subsequence and
finite-dimensional process arguments: weak convergence gives asymptotic
tightness, then continuous images and reindexing preserve it.
-/
theorem VdVWWeakConvergenceProbabilityMeasures.map_asymptoticallyTight_comp_tendsto_atTop
    {S : Type u} {T : Type v} {ι : Type w}
    [MeasurableSpace S] [PseudoMetricSpace S] [OpensMeasurableSpace S]
    [BorelSpace S] [SecondCountableTopology S] [CompleteSpace S]
    [MeasurableSpace T] [TopologicalSpace T] [BorelSpace T] [T2Space T]
    {μs : ℕ -> ProbabilityMeasure S} {μ : ProbabilityMeasure S}
    {g : S -> T} {φ : ι -> ℕ} {l : Filter ι}
    (hμ : VdVWWeakConvergenceProbabilityMeasures μs atTop μ)
    (hg : Continuous g) (hφ : Tendsto φ l atTop) :
    VdVWProbabilityMeasuresAsymptoticallyTight
      (fun i => (μs (φ i)).map hg.measurable.aemeasurable) l :=
  (hμ.map_asymptoticallyTight_atTop hg).comp_tendsto hφ

/--
Binary product stability for measure-level asymptotic tightness.

If two probability-measure families are asymptotically tight along the same
filter, then their product laws are asymptotically tight.  This is the
ordinary probability-measure product/tightness foundation behind Chapter 1
product-space arguments; it is not the VdV&W arbitrary-map
asymptotic-independence theorem.
-/
theorem VdVWProbabilityMeasuresAsymptoticallyTight.prod
    {ι : Type v} {S : Type u} {T : Type w}
    [MeasurableSpace S] [TopologicalSpace S] [BorelSpace S] [T2Space S]
    [MeasurableSpace T] [TopologicalSpace T] [BorelSpace T] [T2Space T]
    {μs : ι -> ProbabilityMeasure S} {νs : ι -> ProbabilityMeasure T}
    {l : Filter ι}
    (hμ : VdVWProbabilityMeasuresAsymptoticallyTight μs l)
    (hν : VdVWProbabilityMeasuresAsymptoticallyTight νs l) :
    VdVWProbabilityMeasuresAsymptoticallyTight
      (fun i => (μs i).prod (νs i)) l := by
  intro ε hε
  have hε_ne : ε ≠ 0 := ne_of_gt hε
  rcases hμ (ε / 2) (ENNReal.half_pos hε_ne) with ⟨K, hK, hKtail⟩
  rcases hν (ε / 2) (ENNReal.half_pos hε_ne) with ⟨L, hL, hLtail⟩
  refine ⟨K ×ˢ L, hK.prod hL, ?_⟩
  filter_upwards [hKtail, hLtail] with i hiK hiL
  calc
    (((μs i).prod (νs i) : ProbabilityMeasure (S × T)) : Measure (S × T)) ((K ×ˢ L)ᶜ)
        = (((μs i : ProbabilityMeasure S) : Measure S).prod
            ((νs i : ProbabilityMeasure T) : Measure T)) ((K ×ˢ L)ᶜ) := by
          rfl
    _ = (((μs i : ProbabilityMeasure S) : Measure S).prod
            ((νs i : ProbabilityMeasure T) : Measure T))
          ((Kᶜ ×ˢ Set.univ) ∪ (Set.univ ×ˢ Lᶜ)) := by
          rw [Set.compl_prod_eq_union]
    _ ≤ (((μs i : ProbabilityMeasure S) : Measure S).prod
            ((νs i : ProbabilityMeasure T) : Measure T)) (Kᶜ ×ˢ Set.univ) +
          (((μs i : ProbabilityMeasure S) : Measure S).prod
            ((νs i : ProbabilityMeasure T) : Measure T)) (Set.univ ×ˢ Lᶜ) := by
          exact measure_union_le _ _
    _ = ((μs i : ProbabilityMeasure S) : Measure S) (Kᶜ) +
          ((νs i : ProbabilityMeasure T) : Measure T) (Lᶜ) := by
          simp [Measure.prod_prod]
    _ ≤ ε / 2 + ε / 2 := add_le_add hiK hiL
    _ = ε := ENNReal.add_halves ε

/--
Measure-level Prokhorov compactness wrapper: the closure of a tight family of
probability measures is compact.
-/
theorem VdVWProbabilityMeasuresTight.isCompact_closure
    {S : Type u} [MeasurableSpace S] [TopologicalSpace S] [T2Space S]
    [BorelSpace S] {A : Set (ProbabilityMeasure S)}
    (hA : VdVWProbabilityMeasuresTight A) :
    IsCompact (closure A) := by
  exact isCompact_closure_of_isTightMeasureSet hA

/--
Closed-ball tightness characterization, forward direction: tight families of
probability measures have uniformly vanishing mass outside closed balls.

This is the direct VdV&W-local wrapper around mathlib's pseudo-metric
tightness API and is the closed-ball form behind the later norm-tail wrappers.
-/
theorem VdVWProbabilityMeasuresTight.tendsto_closedBall_compl
    {S : Type u} [MeasurableSpace S] [PseudoMetricSpace S]
    {A : Set (ProbabilityMeasure S)}
    (hA : VdVWProbabilityMeasuresTight A) (x : S) :
    Tendsto
      (fun r : ℝ =>
        ⨆ μ ∈ {((ν : ProbabilityMeasure S) : Measure S) | ν ∈ A},
          μ (Metric.closedBall x r)ᶜ)
      atTop (𝓝 0) := by
  simpa [VdVWProbabilityMeasuresTight] using
    (MeasureTheory.tendsto_measure_compl_closedBall_of_isTightMeasureSet
      (S := {((ν : ProbabilityMeasure S) : Measure S) | ν ∈ A}) hA x)

/--
Closed-ball tightness criterion, converse direction: in a proper pseudo-metric
space, uniformly vanishing mass outside closed balls implies tightness.
-/
theorem vdVWProbabilityMeasuresTight_of_tendsto_closedBall_compl
    {S : Type u} [MeasurableSpace S] [PseudoMetricSpace S] [ProperSpace S]
    {A : Set (ProbabilityMeasure S)} {x : S}
    (h :
      Tendsto
        (fun r : ℝ =>
          ⨆ μ ∈ {((ν : ProbabilityMeasure S) : Measure S) | ν ∈ A},
            μ (Metric.closedBall x r)ᶜ)
        atTop (𝓝 0)) :
    VdVWProbabilityMeasuresTight A := by
  simpa [VdVWProbabilityMeasuresTight] using
    (MeasureTheory.isTightMeasureSet_of_tendsto_measure_compl_closedBall
      (S := {((ν : ProbabilityMeasure S) : Measure S) | ν ∈ A}) h)

/--
In a proper pseudo-metric space, the VdV&W-local tightness predicate is
equivalent to uniformly vanishing mass outside closed balls around any fixed
center.
-/
theorem vdVWProbabilityMeasuresTight_iff_tendsto_closedBall_compl
    {S : Type u} [MeasurableSpace S] [PseudoMetricSpace S] [ProperSpace S]
    {A : Set (ProbabilityMeasure S)} (x : S) :
    VdVWProbabilityMeasuresTight A ↔
      Tendsto
        (fun r : ℝ =>
          ⨆ μ ∈ {((ν : ProbabilityMeasure S) : Measure S) | ν ∈ A},
            μ (Metric.closedBall x r)ᶜ)
        atTop (𝓝 0) :=
  ⟨fun hA => hA.tendsto_closedBall_compl x,
    vdVWProbabilityMeasuresTight_of_tendsto_closedBall_compl⟩

/--
Norm-tail characterization, forward direction: tight families of probability
measures on a normed group have uniformly vanishing norm tails.

This is a VdV&W-local wrapper around mathlib's normed-space tightness API.  The
statement is written over the underlying set of ordinary measures to match the
local definition `VdVWProbabilityMeasuresTight`.
-/
theorem VdVWProbabilityMeasuresTight.tendsto_norm_tail
    {S : Type u} [MeasurableSpace S] [NormedAddCommGroup S]
    {A : Set (ProbabilityMeasure S)}
    (hA : VdVWProbabilityMeasuresTight A) :
    Tendsto
      (fun r : ℝ =>
        ⨆ μ ∈ {((ν : ProbabilityMeasure S) : Measure S) | ν ∈ A},
          μ {x : S | r < ‖x‖})
      atTop (𝓝 0) := by
  simpa [VdVWProbabilityMeasuresTight] using
    (MeasureTheory.tendsto_measure_norm_gt_of_isTightMeasureSet (E := S)
      (S := {((μ : ProbabilityMeasure S) : Measure S) | μ ∈ A}) hA)

/--
Norm-tail characterization, converse direction: in a proper normed group,
uniformly vanishing norm tails imply tightness of the probability-measure
family.
-/
theorem vdVWProbabilityMeasuresTight_of_tendsto_norm_tail
    {S : Type u} [MeasurableSpace S] [NormedAddCommGroup S] [ProperSpace S]
    {A : Set (ProbabilityMeasure S)}
    (h :
      Tendsto
        (fun r : ℝ =>
          ⨆ μ ∈ {((ν : ProbabilityMeasure S) : Measure S) | ν ∈ A},
            μ {x : S | r < ‖x‖})
        atTop (𝓝 0)) :
    VdVWProbabilityMeasuresTight A := by
  simpa [VdVWProbabilityMeasuresTight] using
    (MeasureTheory.isTightMeasureSet_of_tendsto_measure_norm_gt (E := S)
      (S := {((μ : ProbabilityMeasure S) : Measure S) | μ ∈ A}) h)

/--
In a proper normed group, the VdV&W-local tightness predicate is equivalent to
uniformly vanishing norm tails.
-/
theorem vdVWProbabilityMeasuresTight_iff_tendsto_norm_tail
    {S : Type u} [MeasurableSpace S] [NormedAddCommGroup S] [ProperSpace S]
    {A : Set (ProbabilityMeasure S)} :
    VdVWProbabilityMeasuresTight A ↔
      Tendsto
        (fun r : ℝ =>
          ⨆ μ ∈ {((ν : ProbabilityMeasure S) : Measure S) | ν ∈ A},
            μ {x : S | r < ‖x‖})
        atTop (𝓝 0) :=
  ⟨fun hA => hA.tendsto_norm_tail, vdVWProbabilityMeasuresTight_of_tendsto_norm_tail⟩

/--
Sequential norm-tail tightness criterion, converse direction: for a sequence
of probability measures on a proper normed group, vanishing limsup norm tails
imply tightness of the range.

This is the VdV&W-local wrapper around mathlib's sequence form of the normed
tightness API.  It is useful for Chapter 1 Prokhorov/tightness arguments where
the family is presented as a sequence rather than an arbitrary set.
-/
theorem vdVWProbabilityMeasuresTight_range_of_tendsto_limsup_norm_tail
    {S : Type u} [MeasurableSpace S] [NormedAddCommGroup S] [ProperSpace S] [BorelSpace S]
    (μ : ℕ -> ProbabilityMeasure S)
    (h :
      Tendsto
        (fun r : ℝ =>
          limsup
            (fun n : ℕ => ((μ n : ProbabilityMeasure S) : Measure S) {x : S | r < ‖x‖})
            atTop)
        atTop (𝓝 0)) :
    VdVWProbabilityMeasuresTight (Set.range μ) := by
  have hset :
      {((ν : ProbabilityMeasure S) : Measure S) | ν ∈ Set.range μ} =
        Set.range (fun n : ℕ => ((μ n : ProbabilityMeasure S) : Measure S)) := by
    ext ν
    constructor
    · rintro ⟨ρ, hρ, rfl⟩
      rcases hρ with ⟨n, rfl⟩
      exact ⟨n, rfl⟩
    · rintro ⟨n, rfl⟩
      exact ⟨μ n, ⟨n, rfl⟩, rfl⟩
  simpa [VdVWProbabilityMeasuresTight, hset] using
    (MeasureTheory.isTightMeasureSet_range_of_tendsto_limsup_measure_norm_gt
      (μ := fun n : ℕ => ((μ n : ProbabilityMeasure S) : Measure S)) h)

/--
Sequential norm-tail tightness characterization: for a sequence of probability
measures on a proper normed group, tightness of the range is equivalent to
vanishing limsup norm tails.
-/
theorem vdVWProbabilityMeasuresTight_range_iff_tendsto_limsup_norm_tail
    {S : Type u} [MeasurableSpace S] [NormedAddCommGroup S] [ProperSpace S] [BorelSpace S]
    {μ : ℕ -> ProbabilityMeasure S} :
    VdVWProbabilityMeasuresTight (Set.range μ) ↔
      Tendsto
        (fun r : ℝ =>
          limsup
            (fun n : ℕ => ((μ n : ProbabilityMeasure S) : Measure S) {x : S | r < ‖x‖})
            atTop)
        atTop (𝓝 0) := by
  have hset :
      {((ν : ProbabilityMeasure S) : Measure S) | ν ∈ Set.range μ} =
        Set.range (fun n : ℕ => ((μ n : ProbabilityMeasure S) : Measure S)) := by
    ext ν
    constructor
    · rintro ⟨ρ, hρ, rfl⟩
      rcases hρ with ⟨n, rfl⟩
      exact ⟨n, rfl⟩
    · rintro ⟨n, rfl⟩
      exact ⟨μ n, ⟨n, rfl⟩, rfl⟩
  simpa [VdVWProbabilityMeasuresTight, hset] using
    (MeasureTheory.isTightMeasureSet_range_iff_tendsto_limsup_measure_norm_gt
      (μ := fun n : ℕ => ((μ n : ProbabilityMeasure S) : Measure S)))

/--
Finite-dimensional inner-product tightness criterion, converse direction: a
family of probability measures is tight when all one-dimensional inner-product
tails vanish uniformly.

This is a VdV&W-local wrapper around mathlib's inner-product tightness API and
is useful for finite-dimensional and Hilbert-coordinate Chapter 1 arguments.
-/
theorem vdVWProbabilityMeasuresTight_of_forall_inner_tendsto
    {𝕜 E ι : Type*} [RCLike 𝕜] [Fintype ι]
    [MeasurableSpace E] [NormedAddCommGroup E] [InnerProductSpace 𝕜 E]
    [FiniteDimensional 𝕜 E]
    {A : Set (ProbabilityMeasure E)}
    (h :
      ∀ y : E,
        Tendsto
          (fun r : ℝ =>
            ⨆ μ ∈ {((ν : ProbabilityMeasure E) : Measure E) | ν ∈ A},
              μ {x : E | r < ‖⟪y, x⟫_𝕜‖})
          atTop (𝓝 0)) :
    VdVWProbabilityMeasuresTight A := by
  simpa [VdVWProbabilityMeasuresTight] using
    (MeasureTheory.isTightMeasureSet_of_inner_tendsto (𝕜 := 𝕜)
      (S := {((ν : ProbabilityMeasure E) : Measure E) | ν ∈ A}) h)

/--
Finite-dimensional inner-product tightness characterization for probability
measure families.
-/
theorem vdVWProbabilityMeasuresTight_iff_forall_inner_tendsto
    {𝕜 E ι : Type*} [RCLike 𝕜] [Fintype ι]
    [MeasurableSpace E] [NormedAddCommGroup E] [InnerProductSpace 𝕜 E]
    [FiniteDimensional 𝕜 E]
    {A : Set (ProbabilityMeasure E)} :
    VdVWProbabilityMeasuresTight A ↔
      ∀ y : E,
        Tendsto
          (fun r : ℝ =>
            ⨆ μ ∈ {((ν : ProbabilityMeasure E) : Measure E) | ν ∈ A},
              μ {x : E | r < ‖⟪y, x⟫_𝕜‖})
          atTop (𝓝 0) := by
  simpa [VdVWProbabilityMeasuresTight] using
    (MeasureTheory.isTightMeasureSet_iff_inner_tendsto (𝕜 := 𝕜)
      (S := {((ν : ProbabilityMeasure E) : Measure E) | ν ∈ A}))

/--
Sequential finite-dimensional inner-product tightness criterion: for a
sequence of probability measures, vanishing limsup tails of every
one-dimensional inner product imply tightness of the range.
-/
theorem vdVWProbabilityMeasuresTight_range_of_tendsto_limsup_inner
    {𝕜 E ι : Type*} [RCLike 𝕜] [Fintype ι]
    [MeasurableSpace E] [NormedAddCommGroup E] [InnerProductSpace 𝕜 E]
    [FiniteDimensional 𝕜 E] [BorelSpace E]
    (μ : ℕ -> ProbabilityMeasure E)
    (h :
      ∀ y : E,
        Tendsto
          (fun r : ℝ =>
            limsup
              (fun n : ℕ =>
                ((μ n : ProbabilityMeasure E) : Measure E)
                  {x : E | r < ‖⟪y, x⟫_𝕜‖})
              atTop)
          atTop (𝓝 0)) :
    VdVWProbabilityMeasuresTight (Set.range μ) := by
  have hset :
      {((ν : ProbabilityMeasure E) : Measure E) | ν ∈ Set.range μ} =
        Set.range (fun n : ℕ => ((μ n : ProbabilityMeasure E) : Measure E)) := by
    ext ν
    constructor
    · rintro ⟨ρ, hρ, rfl⟩
      rcases hρ with ⟨n, rfl⟩
      exact ⟨n, rfl⟩
    · rintro ⟨n, rfl⟩
      exact ⟨μ n, ⟨n, rfl⟩, rfl⟩
  simpa [VdVWProbabilityMeasuresTight, hset] using
    (MeasureTheory.isTightMeasureSet_range_of_tendsto_limsup_inner (𝕜 := 𝕜)
      (μ := fun n : ℕ => ((μ n : ProbabilityMeasure E) : Measure E)) h)

/--
Sequential finite-dimensional inner-product tightness characterization for
probability-measure ranges.
-/
theorem vdVWProbabilityMeasuresTight_range_iff_tendsto_limsup_inner
    {𝕜 E ι : Type*} [RCLike 𝕜] [Fintype ι]
    [MeasurableSpace E] [NormedAddCommGroup E] [InnerProductSpace 𝕜 E]
    [FiniteDimensional 𝕜 E] [BorelSpace E]
    {μ : ℕ -> ProbabilityMeasure E} :
    VdVWProbabilityMeasuresTight (Set.range μ) ↔
      ∀ y : E,
        Tendsto
          (fun r : ℝ =>
            limsup
              (fun n : ℕ =>
                ((μ n : ProbabilityMeasure E) : Measure E)
                  {x : E | r < ‖⟪y, x⟫_𝕜‖})
              atTop)
          atTop (𝓝 0) := by
  have hset :
      {((ν : ProbabilityMeasure E) : Measure E) | ν ∈ Set.range μ} =
        Set.range (fun n : ℕ => ((μ n : ProbabilityMeasure E) : Measure E)) := by
    ext ν
    constructor
    · rintro ⟨ρ, hρ, rfl⟩
      rcases hρ with ⟨n, rfl⟩
      exact ⟨n, rfl⟩
    · rintro ⟨n, rfl⟩
      exact ⟨μ n, ⟨n, rfl⟩, rfl⟩
  simpa [VdVWProbabilityMeasuresTight, hset] using
    (MeasureTheory.isTightMeasureSet_range_iff_tendsto_limsup_inner (𝕜 := 𝕜)
      (μ := fun n : ℕ => ((μ n : ProbabilityMeasure E) : Measure E)))

/--
Sequential finite-dimensional inner-product tightness criterion restricted to
unit directions.  In finite dimensions, limsup tail control for all
one-dimensional projections along unit vectors implies tightness of the
probability-measure range.
-/
theorem vdVWProbabilityMeasuresTight_range_of_tendsto_limsup_inner_of_norm_eq_one
    {𝕜 E ι : Type*} [RCLike 𝕜] [Fintype ι]
    [MeasurableSpace E] [NormedAddCommGroup E] [InnerProductSpace 𝕜 E]
    [FiniteDimensional 𝕜 E] [BorelSpace E]
    (μ : ℕ -> ProbabilityMeasure E)
    (h :
      ∀ y : E, ‖y‖ = 1 ->
        Tendsto
          (fun r : ℝ =>
            limsup
              (fun n : ℕ =>
                ((μ n : ProbabilityMeasure E) : Measure E)
                  {x : E | r < ‖⟪y, x⟫_𝕜‖})
              atTop)
          atTop (𝓝 0)) :
    VdVWProbabilityMeasuresTight (Set.range μ) := by
  have hset :
      {((ν : ProbabilityMeasure E) : Measure E) | ν ∈ Set.range μ} =
        Set.range (fun n : ℕ => ((μ n : ProbabilityMeasure E) : Measure E)) := by
    ext ν
    constructor
    · rintro ⟨ρ, hρ, rfl⟩
      rcases hρ with ⟨n, rfl⟩
      exact ⟨n, rfl⟩
    · rintro ⟨n, rfl⟩
      exact ⟨μ n, ⟨n, rfl⟩, rfl⟩
  simpa [VdVWProbabilityMeasuresTight, hset] using
    (MeasureTheory.isTightMeasureSet_range_of_tendsto_limsup_inner_of_norm_eq_one
      (𝕜 := 𝕜)
      (μ := fun n : ℕ => ((μ n : ProbabilityMeasure E) : Measure E)) h)

/--
Sequential finite-dimensional inner-product tightness criterion in real-valued
measure notation.  For probability measures the uniform total-mass bound
required by mathlib's finite-measure statement is discharged by total mass
one.
-/
theorem
    vdVWProbabilityMeasuresTight_range_of_tendsto_limsup_measureReal_inner_of_norm_eq_one
    {𝕜 E ι : Type*} [RCLike 𝕜] [Fintype ι]
    [MeasurableSpace E] [NormedAddCommGroup E] [InnerProductSpace 𝕜 E]
    [FiniteDimensional 𝕜 E] [BorelSpace E]
    (μ : ℕ -> ProbabilityMeasure E)
    (h :
      ∀ y : E, ‖y‖ = 1 ->
        Tendsto
          (fun r : ℝ =>
            limsup
              (fun n : ℕ =>
                (((μ n : ProbabilityMeasure E) : Measure E).real
                  {x : E | r < ‖⟪y, x⟫_𝕜‖}))
              atTop)
          atTop (𝓝 0)) :
    VdVWProbabilityMeasuresTight (Set.range μ) := by
  have hset :
      {((ν : ProbabilityMeasure E) : Measure E) | ν ∈ Set.range μ} =
        Set.range (fun n : ℕ => ((μ n : ProbabilityMeasure E) : Measure E)) := by
    ext ν
    constructor
    · rintro ⟨ρ, hρ, rfl⟩
      rcases hρ with ⟨n, rfl⟩
      exact ⟨n, rfl⟩
    · rintro ⟨n, rfl⟩
      exact ⟨μ n, ⟨n, rfl⟩, rfl⟩
  have hmass :
      ∀ᶠ n in atTop,
        (((μ n : ProbabilityMeasure E) : Measure E) Set.univ) ≤ (1 : ENNReal) :=
    Eventually.of_forall (fun n => by simp)
  simpa [VdVWProbabilityMeasuresTight, hset] using
    (MeasureTheory.isTightMeasureSet_range_of_tendsto_limsup_measureReal_inner_of_norm_eq_one
      (𝕜 := 𝕜)
      (μ := fun n : ℕ => ((μ n : ProbabilityMeasure E) : Measure E)) h
      (1 : NNReal) hmass)

/--
Levy-Prokhorov characterization of the measure-level weak-convergence wrapper
on separable pseudometric spaces.

This packages mathlib's homeomorphism between probability measures with their
weak-convergence topology and the Levy-Prokhorov metric topology.
-/
theorem vdVWWeakConvergenceProbabilityMeasures_iff_levyProkhorov_tendsto
    {S : Type u} {ι : Type v} [MeasurableSpace S] [PseudoMetricSpace S]
    [OpensMeasurableSpace S] [SeparableSpace S]
    {μs : ι -> ProbabilityMeasure S} {l : Filter ι}
    {μ : ProbabilityMeasure S} :
    VdVWWeakConvergenceProbabilityMeasures μs l μ ↔
      Tendsto (fun i => LevyProkhorov.ofMeasure (μs i)) l
        (𝓝 (LevyProkhorov.ofMeasure μ)) := by
  exact (LevyProkhorov.probabilityMeasureHomeomorph (Ω := S)).isEmbedding.tendsto_nhds_iff

/--
Levy-Prokhorov distance-to-zero form of measure-level weak convergence on
separable pseudometric spaces.
-/
theorem vdVWWeakConvergenceProbabilityMeasures_iff_levyProkhorovDist_tendsto_zero
    {S : Type u} {ι : Type v} [MeasurableSpace S] [PseudoMetricSpace S]
    [OpensMeasurableSpace S] [SeparableSpace S]
    {μs : ι -> ProbabilityMeasure S} {l : Filter ι}
    {μ : ProbabilityMeasure S} :
    VdVWWeakConvergenceProbabilityMeasures μs l μ ↔
      Tendsto (fun i => levyProkhorovDist (μs i : Measure S) (μ : Measure S)) l (𝓝 0) := by
  change Tendsto μs l (𝓝 μ) ↔ _
  rw [(LevyProkhorov.probabilityMeasureHomeomorph (Ω := S)).isEmbedding.tendsto_nhds_iff]
  simpa [LevyProkhorov.dist_probabilityMeasure_def] using
    (tendsto_iff_dist_tendsto_zero :
      Tendsto (fun i => LevyProkhorov.ofMeasure (μs i)) l
        (𝓝 (LevyProkhorov.ofMeasure μ)) ↔
      Tendsto (fun i => dist (LevyProkhorov.ofMeasure (μs i))
        (LevyProkhorov.ofMeasure μ)) l (𝓝 0))

/--
Measure-level continuous mapping theorem.

This is the mathlib-backed probability-measure version of the Chapter 1
continuous mapping theorem.  The full VdV&W arbitrary-map statement still needs
the local outer-expectation/asymptotic-measurability layer.
-/
theorem VdVWWeakConvergenceProbabilityMeasures.map_continuous
    {S : Type u} {T : Type v} {ι : Type w}
    [MeasurableSpace S] [TopologicalSpace S] [OpensMeasurableSpace S]
    [MeasurableSpace T] [TopologicalSpace T] [BorelSpace T]
    {μs : ι -> ProbabilityMeasure S} {l : Filter ι}
    {μ : ProbabilityMeasure S} {g : S -> T}
    (h : VdVWWeakConvergenceProbabilityMeasures μs l μ)
    (hg : Continuous g) :
    VdVWWeakConvergenceProbabilityMeasures
      (fun i => (μs i).map hg.measurable.aemeasurable) l
      (μ.map hg.measurable.aemeasurable) := by
  exact ProbabilityMeasure.tendsto_map_of_tendsto_of_continuous μs μ h hg

/--
Binary product-law weak convergence.

This is the measure-level product-space foundation for VdV&W Section 1.4,
proved by mathlib's continuity of the product-probability-measure map.
-/
theorem VdVWWeakConvergenceProbabilityMeasures.prod
    {S : Type u} {T : Type v} {ι : Type w}
    [MeasurableSpace S] [TopologicalSpace S] [SecondCountableTopology S]
    [PseudoMetrizableSpace S] [OpensMeasurableSpace S]
    [MeasurableSpace T] [TopologicalSpace T] [SecondCountableTopology T]
    [PseudoMetrizableSpace T] [OpensMeasurableSpace T]
    {μs : ι -> ProbabilityMeasure S} {νs : ι -> ProbabilityMeasure T}
    {l : Filter ι} {μ : ProbabilityMeasure S} {ν : ProbabilityMeasure T}
    (hμ : VdVWWeakConvergenceProbabilityMeasures μs l μ)
    (hν : VdVWWeakConvergenceProbabilityMeasures νs l ν) :
    VdVWWeakConvergenceProbabilityMeasures
      (fun i => (μs i).prod (νs i)) l (μ.prod ν) := by
  have hp : Tendsto (fun i => (μs i, νs i)) l (𝓝 (μ, ν)) :=
    hμ.prodMk_nhds hν
  exact ProbabilityMeasure.continuous_prod.tendsto (μ, ν) |>.comp hp

/--
Finite product-law weak convergence.

This wraps mathlib's continuity of the finite product probability-measure map.
It is the finite-coordinate product-law foundation used before the full
finite-dimensional-distribution criterion is developed.
-/
theorem VdVWWeakConvergenceProbabilityMeasures.pi
    {J : Type u} [Fintype J] {S : J -> Type v} {ι : Type w}
    [∀ j, MeasurableSpace (S j)] [∀ j, TopologicalSpace (S j)]
    [∀ j, SecondCountableTopology (S j)] [∀ j, PseudoMetrizableSpace (S j)]
    [∀ j, OpensMeasurableSpace (S j)]
    {μs : ι -> (j : J) -> ProbabilityMeasure (S j)}
    {l : Filter ι} {μ : (j : J) -> ProbabilityMeasure (S j)}
    (hμ : ∀ j, VdVWWeakConvergenceProbabilityMeasures (fun n => μs n j) l (μ j)) :
    VdVWWeakConvergenceProbabilityMeasures
      (fun n => ProbabilityMeasure.pi (μs n)) l (ProbabilityMeasure.pi μ) := by
  have hp : Tendsto μs l (𝓝 μ) := tendsto_pi_nhds.mpr hμ
  exact ProbabilityMeasure.continuous_pi.tendsto μ |>.comp hp

/--
Finite product-law weak convergence implies measure-level asymptotic tightness
of the finite product laws.

This combines the finite product-law weak-convergence wrapper with the
sequential Prokhorov/tightness consequence above.  It supplies the ordinary
finite-dimensional product tightness direction needed before the full VdV&W
arbitrary-index FDD converse and process asymptotic-tightness theorem.
-/
theorem VdVWWeakConvergenceProbabilityMeasures.pi_asymptoticallyTight_atTop
    {J : Type u} [Fintype J] {S : J -> Type v}
    [∀ j, MeasurableSpace (S j)] [∀ j, PseudoMetricSpace (S j)]
    [∀ j, SecondCountableTopology (S j)] [∀ j, OpensMeasurableSpace (S j)]
    [OpensMeasurableSpace ((j : J) -> S j)]
    [BorelSpace ((j : J) -> S j)] [SecondCountableTopology ((j : J) -> S j)]
    [CompleteSpace ((j : J) -> S j)]
    {μs : ℕ -> (j : J) -> ProbabilityMeasure (S j)}
    {μ : (j : J) -> ProbabilityMeasure (S j)}
    (hμ : ∀ j, VdVWWeakConvergenceProbabilityMeasures (fun n => μs n j) atTop (μ j)) :
    VdVWProbabilityMeasuresAsymptoticallyTight
      (fun n => ProbabilityMeasure.pi (μs n)) atTop :=
  (VdVWWeakConvergenceProbabilityMeasures.pi hμ).asymptoticallyTight_atTop

/--
Binary product-law weak convergence implies measure-level asymptotic tightness
of the product laws.

This is the binary analogue of `pi_asymptoticallyTight_atTop`.  It remains an
ordinary probability-measure statement, not the full VdV&W arbitrary-map
asymptotic-independence theorem.
-/
theorem VdVWWeakConvergenceProbabilityMeasures.prod_asymptoticallyTight_atTop
    {S : Type u} {T : Type v}
    [MeasurableSpace S] [PseudoMetricSpace S] [SecondCountableTopology S]
    [OpensMeasurableSpace S]
    [MeasurableSpace T] [PseudoMetricSpace T] [SecondCountableTopology T]
    [OpensMeasurableSpace T]
    [OpensMeasurableSpace (S × T)] [BorelSpace (S × T)]
    [SecondCountableTopology (S × T)] [CompleteSpace (S × T)]
    {μs : ℕ -> ProbabilityMeasure S} {νs : ℕ -> ProbabilityMeasure T}
    {μ : ProbabilityMeasure S} {ν : ProbabilityMeasure T}
    (hμ : VdVWWeakConvergenceProbabilityMeasures μs atTop μ)
    (hν : VdVWWeakConvergenceProbabilityMeasures νs atTop ν) :
    VdVWProbabilityMeasuresAsymptoticallyTight
      (fun n => (μs n).prod (νs n)) atTop :=
  (VdVWWeakConvergenceProbabilityMeasures.prod hμ hν).asymptoticallyTight_atTop

/--
Reindexed binary product-law weak convergence gives measure-level asymptotic
tightness along any filter tending to `atTop`.

This packages the product-law weak convergence, Prokhorov tightness, and
subsequence/reindexing steps used in Chapter 1 product arguments.
-/
theorem VdVWWeakConvergenceProbabilityMeasures.prod_asymptoticallyTight_comp_tendsto_atTop
    {S : Type u} {T : Type v} {κ : Type w}
    [MeasurableSpace S] [PseudoMetricSpace S] [SecondCountableTopology S]
    [OpensMeasurableSpace S]
    [MeasurableSpace T] [PseudoMetricSpace T] [SecondCountableTopology T]
    [OpensMeasurableSpace T]
    [OpensMeasurableSpace (S × T)] [BorelSpace (S × T)]
    [SecondCountableTopology (S × T)] [CompleteSpace (S × T)]
    {μs : ℕ -> ProbabilityMeasure S} {νs : ℕ -> ProbabilityMeasure T}
    {μ : ProbabilityMeasure S} {ν : ProbabilityMeasure T}
    {φ : κ -> ℕ} {l : Filter κ}
    (hμ : VdVWWeakConvergenceProbabilityMeasures μs atTop μ)
    (hν : VdVWWeakConvergenceProbabilityMeasures νs atTop ν)
    (hφ : Tendsto φ l atTop) :
    VdVWProbabilityMeasuresAsymptoticallyTight
      (fun k => (μs (φ k)).prod (νs (φ k))) l :=
  (hμ.prod_asymptoticallyTight_atTop hν).comp_tendsto hφ

/--
Reindexed finite product-law weak convergence gives measure-level asymptotic
tightness along any filter tending to `atTop`.

This is the finite-coordinate/FDD tightness feeder for subsequences and other
sample-size reindexing maps.  It does not assert the arbitrary-index process
FDD converse.
-/
theorem VdVWWeakConvergenceProbabilityMeasures.pi_asymptoticallyTight_comp_tendsto_atTop
    {J : Type u} [Fintype J] {S : J -> Type v} {κ : Type w}
    [∀ j, MeasurableSpace (S j)] [∀ j, PseudoMetricSpace (S j)]
    [∀ j, SecondCountableTopology (S j)] [∀ j, OpensMeasurableSpace (S j)]
    [OpensMeasurableSpace ((j : J) -> S j)]
    [BorelSpace ((j : J) -> S j)] [SecondCountableTopology ((j : J) -> S j)]
    [CompleteSpace ((j : J) -> S j)]
    {μs : ℕ -> (j : J) -> ProbabilityMeasure (S j)}
    {μ : (j : J) -> ProbabilityMeasure (S j)}
    {φ : κ -> ℕ} {l : Filter κ}
    (hμ : ∀ j, VdVWWeakConvergenceProbabilityMeasures (fun n => μs n j) atTop (μ j))
    (hφ : Tendsto φ l atTop) :
    VdVWProbabilityMeasuresAsymptoticallyTight
      (fun k => ProbabilityMeasure.pi (μs (φ k))) l :=
  (VdVWWeakConvergenceProbabilityMeasures.pi_asymptoticallyTight_atTop hμ).comp_tendsto hφ

/--
Independent random-variable product-law convergence.

This is the measurable random-variable form of the VdV&W Section 1.4
independent-coordinate product-space principle: if the two marginals converge
in distribution and the coordinates are independent at every index, then the
joint laws converge weakly to the product of the two limiting laws.

The full VdV&W arbitrary-map/asymptotic-independence statement remains a
separate nonmeasurable primitive.
-/
theorem vdVWTendstoInDistribution_prodMk_laws_of_indepFun
    {ι : Type u} {Ω : ι -> Type v} {ΩE : Type w} {ΩF : Type x}
    {E : Type*} {F : Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    {μ : (i : ι) -> @Measure (Ω i) (mΩ i)}
    [∀ i, IsProbabilityMeasure (μ i)]
    [MeasurableSpace ΩE] {μE : Measure ΩE} [IsProbabilityMeasure μE]
    [MeasurableSpace ΩF] {μF : Measure ΩF} [IsProbabilityMeasure μF]
    [MeasurableSpace E] [TopologicalSpace E] [SecondCountableTopology E]
    [PseudoMetrizableSpace E] [OpensMeasurableSpace E]
    [MeasurableSpace F] [TopologicalSpace F] [SecondCountableTopology F]
    [PseudoMetrizableSpace F] [OpensMeasurableSpace F]
    {X : (i : ι) -> Ω i -> E} {Y : (i : ι) -> Ω i -> F}
    {Z : ΩE -> E} {W : ΩF -> F} {l : Filter ι}
    (hX : TendstoInDistribution X l Z μ μE)
    (hY : TendstoInDistribution Y l W μ μF)
    (hInd : ∀ i, X i ⟂ᵢ[μ i] Y i) :
    VdVWWeakConvergenceProbabilityMeasures
      (fun i : ι =>
        (⟨(μ i).map (fun ω => (X i ω, Y i ω)),
            Measure.isProbabilityMeasure_map
              ((hX.forall_aemeasurable i).prodMk
                (hY.forall_aemeasurable i))⟩ :
          ProbabilityMeasure (E × F)))
      l
      (ProbabilityMeasure.prod
        (⟨μE.map Z,
          Measure.isProbabilityMeasure_map hX.aemeasurable_limit⟩ :
          ProbabilityMeasure E)
        (⟨μF.map W,
          Measure.isProbabilityMeasure_map hY.aemeasurable_limit⟩ :
          ProbabilityMeasure F)) := by
  let μX : ι -> ProbabilityMeasure E := fun i =>
    ⟨(μ i).map (X i),
      Measure.isProbabilityMeasure_map (hX.forall_aemeasurable i)⟩
  let μY : ι -> ProbabilityMeasure F := fun i =>
    ⟨(μ i).map (Y i),
      Measure.isProbabilityMeasure_map (hY.forall_aemeasurable i)⟩
  let νX : ProbabilityMeasure E :=
    ⟨μE.map Z, Measure.isProbabilityMeasure_map hX.aemeasurable_limit⟩
  let νY : ProbabilityMeasure F :=
    ⟨μF.map W, Measure.isProbabilityMeasure_map hY.aemeasurable_limit⟩
  have hprod : VdVWWeakConvergenceProbabilityMeasures
      (fun i => (μX i).prod (μY i)) l (νX.prod νY) := by
    exact VdVWWeakConvergenceProbabilityMeasures.prod (S := E) (T := F)
      (μs := μX) (νs := μY) (μ := νX) (ν := νY)
      hX.tendsto hY.tendsto
  have hseq_eq :
      (fun i : ι =>
        (⟨(μ i).map (fun ω => (X i ω, Y i ω)),
            Measure.isProbabilityMeasure_map
              ((hX.forall_aemeasurable i).prodMk
                (hY.forall_aemeasurable i))⟩ :
          ProbabilityMeasure (E × F))) =
        fun i : ι => (μX i).prod (μY i) := by
    funext i
    ext s hs
    change (Measure.map (fun ω => (X i ω, Y i ω)) (μ i)) s =
      (((μ i).map (X i)).prod ((μ i).map (Y i))) s
    have hXLaw : HasLaw (X i) ((μ i).map (X i)) (μ i) :=
      ⟨hX.forall_aemeasurable i, rfl⟩
    have hYLaw : HasLaw (Y i) ((μ i).map (Y i)) (μ i) :=
      ⟨hY.forall_aemeasurable i, rfl⟩
    rw [((hInd i).hasLaw_prod hXLaw hYLaw).map_eq]
  simpa [hseq_eq, μX, μY, νX, νY] using hprod

/--
Independent-coordinate convergence in distribution for binary products.

This consumes the law-level product wrapper
`vdVWTendstoInDistribution_prodMk_laws_of_indepFun` and repackages it as a
`TendstoInDistribution` statement for the paired random variables.  It is the
ordinary measurable random-variable version of the VdV&W 1.4.6 independent
product statement: marginal convergence plus finite-stage independence and
independence of the limiting coordinates imply joint convergence.

The full arbitrary-map/asymptotic-independence VdV&W statement remains a
separate nonmeasurable primitive.
-/
theorem vdVWTendstoInDistribution_prodMk_of_indepFun
    {ι : Type u} {Ω : ι -> Type v} {Ωlim : Type w}
    {E : Type*} {F : Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    {μ : (i : ι) -> @Measure (Ω i) (mΩ i)}
    [∀ i, IsProbabilityMeasure (μ i)]
    [MeasurableSpace Ωlim] {μlim : Measure Ωlim} [IsProbabilityMeasure μlim]
    [MeasurableSpace E] [TopologicalSpace E] [SecondCountableTopology E]
    [PseudoMetrizableSpace E] [OpensMeasurableSpace E]
    [MeasurableSpace F] [TopologicalSpace F] [SecondCountableTopology F]
    [PseudoMetrizableSpace F] [OpensMeasurableSpace F]
    {X : (i : ι) -> Ω i -> E} {Y : (i : ι) -> Ω i -> F}
    {Z : Ωlim -> E} {W : Ωlim -> F} {l : Filter ι}
    (hX : TendstoInDistribution X l Z μ μlim)
    (hY : TendstoInDistribution Y l W μ μlim)
    (hInd : ∀ i, X i ⟂ᵢ[μ i] Y i)
    (hLimitInd : Z ⟂ᵢ[μlim] W) :
    TendstoInDistribution
      (fun i ω => (X i ω, Y i ω)) l (fun ω => (Z ω, W ω)) μ μlim := by
  have hweak :=
    vdVWTendstoInDistribution_prodMk_laws_of_indepFun
      (μE := μlim) (μF := μlim) hX hY hInd
  refine
    { forall_aemeasurable := fun i =>
        (hX.forall_aemeasurable i).prodMk (hY.forall_aemeasurable i)
      aemeasurable_limit := hX.aemeasurable_limit.prodMk hY.aemeasurable_limit
      tendsto := ?_ }
  have htarget_eq :
      (ProbabilityMeasure.prod
        (⟨μlim.map Z,
          Measure.isProbabilityMeasure_map hX.aemeasurable_limit⟩ :
          ProbabilityMeasure E)
        (⟨μlim.map W,
          Measure.isProbabilityMeasure_map hY.aemeasurable_limit⟩ :
          ProbabilityMeasure F)) =
        (⟨μlim.map (fun ω => (Z ω, W ω)),
          Measure.isProbabilityMeasure_map
            (hX.aemeasurable_limit.prodMk hY.aemeasurable_limit)⟩ :
          ProbabilityMeasure (E × F)) := by
    ext s hs
    change (μlim.map Z).prod (μlim.map W) s =
      μlim.map (fun ω => (Z ω, W ω)) s
    have hZLaw : HasLaw Z (μlim.map Z) μlim :=
      ⟨hX.aemeasurable_limit, rfl⟩
    have hWLaw : HasLaw W (μlim.map W) μlim :=
      ⟨hY.aemeasurable_limit, rfl⟩
    rw [((hLimitInd.hasLaw_prod hZLaw hWLaw).map_eq)]
  simpa [VdVWWeakConvergenceProbabilityMeasures, htarget_eq] using hweak

/--
Finite independent-coordinate product-law convergence.

This is the finite-product extension of
`vdVWTendstoInDistribution_prodMk_laws_of_indepFun`: marginal convergence in
distribution for each coordinate, plus finite-stage independence of the
coordinates, implies weak convergence of the joint finite-product laws to the
product of the limiting laws.

This is still the ordinary measurable random-variable foundation.  The
arbitrary-map/asymptotic-independence and countable-product VdV&W statements
remain separate Chapter 1 primitives.
-/
theorem vdVWTendstoInDistribution_pi_laws_of_iIndepFun
    {J : Type u} [Fintype J]
    {ι : Type v} {Ω : ι -> Type w} {Ωlim : J -> Type x}
    {S : J -> Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    {μ : (i : ι) -> @Measure (Ω i) (mΩ i)}
    [∀ i, IsProbabilityMeasure (μ i)]
    [∀ j, MeasurableSpace (Ωlim j)]
    {μlim : (j : J) -> Measure (Ωlim j)}
    [∀ j, IsProbabilityMeasure (μlim j)]
    [∀ j, MeasurableSpace (S j)] [∀ j, TopologicalSpace (S j)]
    [∀ j, SecondCountableTopology (S j)] [∀ j, PseudoMetrizableSpace (S j)]
    [∀ j, OpensMeasurableSpace (S j)]
    {X : (i : ι) -> (j : J) -> Ω i -> S j}
    {Z : (j : J) -> Ωlim j -> S j} {l : Filter ι}
    (hX :
      ∀ j,
        TendstoInDistribution (fun i ω => X i j ω) l (Z j) μ
          (μlim j))
    (hInd : ∀ i, iIndepFun (fun j => X i j) (μ i)) :
    VdVWWeakConvergenceProbabilityMeasures
      (fun i : ι =>
        (⟨(μ i).map (fun ω => fun j => X i j ω),
          Measure.isProbabilityMeasure_map
            (aemeasurable_pi_lambda _ fun j =>
              (hX j).forall_aemeasurable i)⟩ :
          ProbabilityMeasure ((j : J) -> S j)))
      l
      (ProbabilityMeasure.pi fun j =>
        (⟨(μlim j).map (Z j),
          Measure.isProbabilityMeasure_map (hX j).aemeasurable_limit⟩ :
          ProbabilityMeasure (S j))) := by
  let μX : ι -> (j : J) -> ProbabilityMeasure (S j) := fun i j =>
    ⟨(μ i).map (X i j),
      Measure.isProbabilityMeasure_map ((hX j).forall_aemeasurable i)⟩
  let ν : (j : J) -> ProbabilityMeasure (S j) := fun j =>
    ⟨(μlim j).map (Z j),
      Measure.isProbabilityMeasure_map (hX j).aemeasurable_limit⟩
  have hprod : VdVWWeakConvergenceProbabilityMeasures
      (fun i => ProbabilityMeasure.pi (μX i)) l (ProbabilityMeasure.pi ν) := by
    exact VdVWWeakConvergenceProbabilityMeasures.pi (J := J) (S := S)
      (μs := μX) (μ := ν) (fun j => (hX j).tendsto)
  have hseq_eq :
      (fun i : ι =>
        (⟨(μ i).map (fun ω => fun j => X i j ω),
          Measure.isProbabilityMeasure_map
            (aemeasurable_pi_lambda _ fun j =>
              (hX j).forall_aemeasurable i)⟩ :
          ProbabilityMeasure ((j : J) -> S j))) =
        fun i : ι => ProbabilityMeasure.pi (μX i) := by
    funext i
    ext s hs
    change (Measure.map (fun ω => fun j => X i j ω) (μ i)) s =
      (Measure.pi fun j => (μ i).map (X i j)) s
    have hcoordLaw :
        ∀ j, HasLaw (X i j) ((μ i).map (X i j)) (μ i) := by
      intro j
      exact ⟨(hX j).forall_aemeasurable i, rfl⟩
    rw [(hInd i).hasLaw_pi hcoordLaw |>.map_eq]
  simpa [hseq_eq, μX, ν] using hprod

/--
Finite independent-coordinate convergence in distribution.

This is the finite-coordinate `TendstoInDistribution` counterpart of
`vdVWTendstoInDistribution_pi_laws_of_iIndepFun`: marginal convergence in
distribution for each coordinate, finite-stage independence, and independence
of the limiting coordinate family imply joint finite-product convergence in
distribution.

This remains the ordinary measurable random-variable layer.  Arbitrary-map,
asymptotic-independence, and arbitrary-index process criteria are separate
Chapter 1 primitives.
-/
theorem vdVWTendstoInDistribution_pi_of_iIndepFun
    {J : Type u} [Fintype J]
    {ι : Type v} {Ω : ι -> Type w} {Ωlim : Type x}
    {S : J -> Type*}
    {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    {μ : (i : ι) -> @Measure (Ω i) (mΩ i)}
    [∀ i, IsProbabilityMeasure (μ i)]
    [MeasurableSpace Ωlim] {μlim : Measure Ωlim} [IsProbabilityMeasure μlim]
    [∀ j, MeasurableSpace (S j)] [∀ j, TopologicalSpace (S j)]
    [∀ j, SecondCountableTopology (S j)] [∀ j, PseudoMetrizableSpace (S j)]
    [∀ j, OpensMeasurableSpace (S j)]
    {X : (i : ι) -> (j : J) -> Ω i -> S j}
    {Z : (j : J) -> Ωlim -> S j} {l : Filter ι}
    (hX :
      ∀ j,
        TendstoInDistribution (fun i ω => X i j ω) l (Z j) μ μlim)
    (hInd : ∀ i, iIndepFun (fun j => X i j) (μ i))
    (hLimitInd : iIndepFun Z μlim) :
    TendstoInDistribution
      (fun i ω => fun j => X i j ω) l (fun ω => fun j => Z j ω) μ μlim := by
  have hweak :=
    vdVWTendstoInDistribution_pi_laws_of_iIndepFun
      (Ωlim := fun _ : J => Ωlim) (μlim := fun _ : J => μlim)
      hX hInd
  refine
    { forall_aemeasurable := fun i =>
        aemeasurable_pi_lambda _ fun j => (hX j).forall_aemeasurable i
      aemeasurable_limit :=
        aemeasurable_pi_lambda _ fun j => (hX j).aemeasurable_limit
      tendsto := ?_ }
  have htarget_eq :
      (ProbabilityMeasure.pi fun j =>
        (⟨μlim.map (Z j),
          Measure.isProbabilityMeasure_map (hX j).aemeasurable_limit⟩ :
          ProbabilityMeasure (S j))) =
        (⟨μlim.map (fun ω => fun j => Z j ω),
          Measure.isProbabilityMeasure_map
            (aemeasurable_pi_lambda _ fun j =>
              (hX j).aemeasurable_limit)⟩ :
          ProbabilityMeasure ((j : J) -> S j)) := by
    ext s hs
    change (Measure.pi fun j => μlim.map (Z j)) s =
      μlim.map (fun ω => fun j => Z j ω) s
    have hcoordLaw :
        ∀ j, HasLaw (Z j) (μlim.map (Z j)) μlim := by
      intro j
      exact ⟨(hX j).aemeasurable_limit, rfl⟩
    rw [(hLimitInd.hasLaw_pi hcoordLaw |>.map_eq)]
  simpa [VdVWWeakConvergenceProbabilityMeasures, htarget_eq] using hweak

/--
Finite-dimensional restriction of a weakly convergent process law.

This is the forward FDD direction: weak convergence of laws on a product space
implies weak convergence of every finite-coordinate restriction.
-/
theorem VdVWWeakConvergenceProbabilityMeasures.finiteDimensionalRestrict
    {I : Type u} {S : I -> Type v} {ι : Type w}
    [∀ i, MeasurableSpace (S i)] [∀ i, TopologicalSpace (S i)]
    [∀ i, OpensMeasurableSpace (S i)]
    [MeasurableSpace ((i : I) -> S i)] [OpensMeasurableSpace ((i : I) -> S i)]
    {μs : ι -> ProbabilityMeasure ((i : I) -> S i)}
    {l : Filter ι} {μ : ProbabilityMeasure ((i : I) -> S i)}
    (hμ : VdVWWeakConvergenceProbabilityMeasures μs l μ)
    (s : Finset I)
    [MeasurableSpace ((i : s) -> S i)] [BorelSpace ((i : s) -> S i)] :
    VdVWWeakConvergenceProbabilityMeasures
      (fun n => (μs n).map ((Finset.continuous_restrict s).measurable.aemeasurable)) l
      (μ.map ((Finset.continuous_restrict s).measurable.aemeasurable)) := by
  exact hμ.map_continuous (Finset.continuous_restrict s)

/--
Reindexed finite-dimensional restriction of a weakly convergent process law.

This packages the forward FDD direction with the standard subsequence/filter
reindexing step.  It remains a measure-level statement and does not assert the
full VdV&W arbitrary-index FDD converse.
-/
theorem VdVWWeakConvergenceProbabilityMeasures.finiteDimensionalRestrict_comp_tendsto
    {I : Type u} {S : I -> Type v} {ι : Type w} {κ : Type x}
    [∀ i, MeasurableSpace (S i)] [∀ i, TopologicalSpace (S i)]
    [∀ i, OpensMeasurableSpace (S i)]
    [MeasurableSpace ((i : I) -> S i)] [OpensMeasurableSpace ((i : I) -> S i)]
    {μs : ι -> ProbabilityMeasure ((i : I) -> S i)}
    {l : Filter ι} {l' : Filter κ} {μ : ProbabilityMeasure ((i : I) -> S i)}
    (hμ : VdVWWeakConvergenceProbabilityMeasures μs l μ)
    {φ : κ -> ι} (hφ : Tendsto φ l' l)
    (s : Finset I)
    [MeasurableSpace ((i : s) -> S i)] [BorelSpace ((i : s) -> S i)] :
    VdVWWeakConvergenceProbabilityMeasures
      (fun k => (μs (φ k)).map ((Finset.continuous_restrict s).measurable.aemeasurable)) l'
      (μ.map ((Finset.continuous_restrict s).measurable.aemeasurable)) := by
  exact (hμ.finiteDimensionalRestrict s).comp_tendsto hφ

/--
Finite-dimensional restriction of an asymptotically tight process-law family.

This is the measure-level tightness analogue of the forward FDD direction:
ordinary asymptotic tightness of laws on a product space implies asymptotic
tightness of every finite-coordinate restriction.  It does not assert the
full VdV&W arbitrary-map/process asymptotic-tightness criterion.
-/
theorem VdVWProbabilityMeasuresAsymptoticallyTight.finiteDimensionalRestrict
    {I : Type u} {S : I -> Type v} {ι : Type w}
    [∀ i, MeasurableSpace (S i)] [∀ i, TopologicalSpace (S i)]
    [∀ i, OpensMeasurableSpace (S i)]
    [MeasurableSpace ((i : I) -> S i)] [OpensMeasurableSpace ((i : I) -> S i)]
    {μs : ι -> ProbabilityMeasure ((i : I) -> S i)}
    {l : Filter ι}
    (hμ : VdVWProbabilityMeasuresAsymptoticallyTight μs l)
    (s : Finset I)
    [MeasurableSpace ((i : s) -> S i)] [BorelSpace ((i : s) -> S i)]
    [T2Space ((i : s) -> S i)] :
    VdVWProbabilityMeasuresAsymptoticallyTight
      (fun n => (μs n).map ((Finset.continuous_restrict s).measurable.aemeasurable)) l := by
  exact hμ.map_continuous (Finset.continuous_restrict s)

/--
Reindexed finite-dimensional restriction of an asymptotically tight
process-law family.

This is the tightness analogue of
`VdVWWeakConvergenceProbabilityMeasures.finiteDimensionalRestrict_comp_tendsto`.
It supplies a reusable subsequence/filter handoff for finite FDD tightness
without claiming the full arbitrary-index process tightness theorem.
-/
theorem VdVWProbabilityMeasuresAsymptoticallyTight.finiteDimensionalRestrict_comp_tendsto
    {I : Type u} {S : I -> Type v} {ι : Type w} {κ : Type x}
    [∀ i, MeasurableSpace (S i)] [∀ i, TopologicalSpace (S i)]
    [∀ i, OpensMeasurableSpace (S i)]
    [MeasurableSpace ((i : I) -> S i)] [OpensMeasurableSpace ((i : I) -> S i)]
    {μs : ι -> ProbabilityMeasure ((i : I) -> S i)}
    {l : Filter ι} {l' : Filter κ}
    (hμ : VdVWProbabilityMeasuresAsymptoticallyTight μs l)
    {φ : κ -> ι} (hφ : Tendsto φ l' l)
    (s : Finset I)
    [MeasurableSpace ((i : s) -> S i)] [BorelSpace ((i : s) -> S i)]
    [T2Space ((i : s) -> S i)] :
    VdVWProbabilityMeasuresAsymptoticallyTight
      (fun k => (μs (φ k)).map ((Finset.continuous_restrict s).measurable.aemeasurable)) l' := by
  exact (hμ.finiteDimensionalRestrict s).comp_tendsto hφ

/--
Measurable-random-variable continuous mapping theorem for convergence in
distribution.

This wraps mathlib's `TendstoInDistribution.continuous_comp` with a VdV&W local
name for the Chapter 1.11 foundation lane.  It proves the fixed continuous-map
case; varying maps and nonmeasurable outer-probability formulations remain
separate local primitives.
-/
theorem vdVWTendstoInDistribution_continuous_comp
    {ι : Type u} {E : Type v} {F : Type w} {Ω : ι -> Type x}
    {Ω' : Type x} {mΩ : (i : ι) -> MeasurableSpace (Ω i)}
    {μ : (i : ι) -> @Measure (Ω i) (mΩ i)}
    [∀ i, IsProbabilityMeasure (μ i)]
    {mΩ' : MeasurableSpace Ω'} {μ' : @Measure Ω' mΩ'}
    [IsProbabilityMeasure μ']
    [TopologicalSpace E] [MeasurableSpace E] [OpensMeasurableSpace E]
    [TopologicalSpace F] [MeasurableSpace F] [BorelSpace F]
    {X : (i : ι) -> Ω i -> E} {Z : Ω' -> E} {l : Filter ι}
    {g : E -> F}
    (h : TendstoInDistribution X l Z μ μ')
    (hg : Continuous g) :
    TendstoInDistribution (fun i => g ∘ X i) l (g ∘ Z) μ μ' :=
  h.continuous_comp hg

/--
Measurable common-domain convergence in distribution implies the local
signed-outer bounded-continuous weak-convergence formulation for the original
maps.

Mathlib's `TendstoInDistribution` is convergence of the pushed-forward laws.
This theorem transports that law convergence through the signed
positive/negative VdV&W outer-expectation bridge.  The explicit measurability
hypothesis upgrades the a.e.-measurable law statement to the pointwise
measurable-map collapse used by the current signed outer expectation layer.
-/
theorem vdVWTendstoInDistribution_to_signedOuterBoundedContinuous
    {ι : Type u} {Ω : Type v} {Ω' : Type w} {S : Type x}
    [MeasurableSpace Ω] {μs : ι -> Measure Ω} [∀ i, IsProbabilityMeasure (μs i)]
    [MeasurableSpace Ω'] {μ' : Measure Ω'} [IsProbabilityMeasure μ']
    [MeasurableSpace S] [TopologicalSpace S] [OpensMeasurableSpace S]
    {X : ι -> Ω -> S} {Z : Ω' -> S} {l : Filter ι}
    (h : TendstoInDistribution X l Z μs μ')
    (hX : ∀ i, Measurable (X i)) :
    VdVWWeakConvergenceSignedOuterBoundedContinuous μs X l
      ⟨μ'.map Z, Measure.isProbabilityMeasure_map h.aemeasurable_limit⟩ := by
  exact
    VdVWWeakConvergenceProbabilityMeasures.to_signedOuterBoundedContinuous_of_map_eq
      hX h.tendsto (fun _ => rfl)

/--
Measurable common-domain convergence in distribution gives the proof-carrying
signed bounded-continuous arbitrary-map layer.
-/
theorem vdVWTendstoInDistribution_to_signedBoundedContinuousArbitraryMap
    {ι : Type u} {Ω : Type v} {Ω' : Type w} {S : Type x}
    [MeasurableSpace Ω] {μs : ι -> Measure Ω} [∀ i, IsProbabilityMeasure (μs i)]
    [MeasurableSpace Ω'] {μ' : Measure Ω'} [IsProbabilityMeasure μ']
    [MeasurableSpace S] [TopologicalSpace S] [OpensMeasurableSpace S]
    {X : ι -> Ω -> S} {Z : Ω' -> S} {l : Filter ι}
    (h : TendstoInDistribution X l Z μs μ')
    (hX : ∀ i, Measurable (X i)) :
    VdVWWeakConvergenceSignedBoundedContinuousArbitraryMap μs X l
      ⟨μ'.map Z, Measure.isProbabilityMeasure_map h.aemeasurable_limit⟩ :=
  { weakConvergence :=
      vdVWTendstoInDistribution_to_signedOuterBoundedContinuous h hX
    asymptoticMeasurability :=
      VdVWAsymptoticallyMeasurableSignedBoundedContinuous.of_forall_measurable hX }

/--
A.e.-measurable common-domain convergence in distribution implies the local
signed-outer bounded-continuous weak-convergence formulation.

This removes the previous pointwise-measurability strengthening from the
mathlib-to-VdV&W bridge: `TendstoInDistribution` already carries the
a.e.-measurability needed for its pushforward laws.
-/
theorem vdVWTendstoInDistribution_to_signedOuterBoundedContinuous_aemeasurable
    {ι : Type u} {Ω : Type v} {Ω' : Type w} {S : Type x}
    [MeasurableSpace Ω] {μs : ι -> Measure Ω} [∀ i, IsProbabilityMeasure (μs i)]
    [MeasurableSpace Ω'] {μ' : Measure Ω'} [IsProbabilityMeasure μ']
    [MeasurableSpace S] [MeasurableSpace.CountablyGenerated S]
    [TopologicalSpace S] [OpensMeasurableSpace S]
    {X : ι -> Ω -> S} {Z : Ω' -> S} {l : Filter ι}
    (h : TendstoInDistribution X l Z μs μ') :
    VdVWWeakConvergenceSignedOuterBoundedContinuous μs X l
      ⟨μ'.map Z, Measure.isProbabilityMeasure_map h.aemeasurable_limit⟩ :=
  (VdVWWeakConvergenceProbabilityMeasures.to_signedBoundedContinuousArbitraryMap_of_maps_aemeasurable
    (μs := μs) (X := X) (fun i => h.forall_aemeasurable i) h.tendsto).weakConvergence

/--
A.e.-measurable common-domain convergence in distribution gives the
proof-carrying signed bounded-continuous arbitrary-map layer.
-/
theorem vdVWTendstoInDistribution_to_signedBoundedContinuousArbitraryMap_aemeasurable
    {ι : Type u} {Ω : Type v} {Ω' : Type w} {S : Type x}
    [MeasurableSpace Ω] {μs : ι -> Measure Ω} [∀ i, IsProbabilityMeasure (μs i)]
    [MeasurableSpace Ω'] {μ' : Measure Ω'} [IsProbabilityMeasure μ']
    [MeasurableSpace S] [MeasurableSpace.CountablyGenerated S]
    [TopologicalSpace S] [OpensMeasurableSpace S]
    {X : ι -> Ω -> S} {Z : Ω' -> S} {l : Filter ι}
    (h : TendstoInDistribution X l Z μs μ') :
    VdVWWeakConvergenceSignedBoundedContinuousArbitraryMap μs X l
      ⟨μ'.map Z, Measure.isProbabilityMeasure_map h.aemeasurable_limit⟩ :=
  VdVWWeakConvergenceProbabilityMeasures.to_signedBoundedContinuousArbitraryMap_of_maps_aemeasurable
    (μs := μs) (X := X) (fun i => h.forall_aemeasurable i) h.tendsto

/--
Common-domain outer-probability convergence implies the proof-carrying signed
bounded-continuous arbitrary-map weak-convergence layer.

This composes the existing VdV&W Lemma 1.10.2 measurable common-domain bridge
from outer probability to mathlib `TendstoInDistribution` with the signed
bounded-continuous arbitrary-map package above.
-/
theorem
    VdVWConvergesInOuterProbability.to_signedBoundedContinuousArbitraryMap
    {ι : Type u} {Ω : Type v} {D : Type w}
    [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ]
    [MeasurableSpace D] [SeminormedAddCommGroup D]
    [SecondCountableTopology D] [BorelSpace D] [OpensMeasurableSpace D]
    {X : ι -> Ω -> D} {limit : Ω -> D} {l : Filter ι}
    [l.NeBot] [l.IsCountablyGenerated]
    (h : VdVWConvergesInOuterProbability μ X l limit)
    (hX : ∀ i, Measurable (X i)) :
    VdVWWeakConvergenceSignedBoundedContinuousArbitraryMap
      (fun _ : ι => μ) X l
      ⟨μ.map limit,
        Measure.isProbabilityMeasure_map
          (tendstoInDistribution_of_vdVWConvergesInOuterProbability h
            (fun i => (hX i).aemeasurable)).aemeasurable_limit⟩ := by
  have hdist :
      TendstoInDistribution X l limit (fun _ : ι => μ) μ :=
    tendstoInDistribution_of_vdVWConvergesInOuterProbability h
      (fun i => (hX i).aemeasurable)
  exact vdVWTendstoInDistribution_to_signedBoundedContinuousArbitraryMap hdist hX

/--
Common-domain outer-probability convergence with only a.e.-measurable
statistics implies the proof-carrying signed bounded-continuous arbitrary-map
weak-convergence layer.
-/
theorem
    VdVWConvergesInOuterProbability.to_signedBoundedContinuousArbitraryMap_aemeasurable
    {ι : Type u} {Ω : Type v} {D : Type w}
    [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ]
    [MeasurableSpace D] [MeasurableSpace.CountablyGenerated D]
    [SeminormedAddCommGroup D] [SecondCountableTopology D]
    [BorelSpace D] [OpensMeasurableSpace D]
    {X : ι -> Ω -> D} {limit : Ω -> D} {l : Filter ι}
    [l.NeBot] [l.IsCountablyGenerated]
    (h : VdVWConvergesInOuterProbability μ X l limit)
    (hX : ∀ i, AEMeasurable (X i) μ) :
    VdVWWeakConvergenceSignedBoundedContinuousArbitraryMap
      (fun _ : ι => μ) X l
      ⟨μ.map limit,
        Measure.isProbabilityMeasure_map
          (tendstoInDistribution_of_vdVWConvergesInOuterProbability h
            hX).aemeasurable_limit⟩ := by
  have hdist :
      TendstoInDistribution X l limit (fun _ : ι => μ) μ :=
    tendstoInDistribution_of_vdVWConvergesInOuterProbability h hX
  exact vdVWTendstoInDistribution_to_signedBoundedContinuousArbitraryMap_aemeasurable hdist

/--
Measurable common-domain Slutsky/product theorem.

This is the mathlib-backed product-convergence foundation for VdV&W Section
1.4 in the ordinary measurable random-variable setting.  The exact
nonmeasurable/asymptotic-independence VdV&W formulations still need separate
local primitives.
-/
theorem vdVWTendstoInDistribution_prodMk_of_tendstoInMeasure_const
    {ι : Type u} {E : Type v} {E' : Type w}
    {Ω : Type x} {Ω' : Type x}
    [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ]
    [MeasurableSpace Ω'] {μ' : Measure Ω'} [IsProbabilityMeasure μ']
    [MeasurableSpace E] [SeminormedAddCommGroup E]
    [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    [MeasurableSpace E'] [SeminormedAddCommGroup E']
    [SecondCountableTopology E'] [BorelSpace E']
    {X : ι -> Ω -> E} {Y : ι -> Ω -> E'} {Z : Ω' -> E}
    {l : Filter ι} [l.IsCountablyGenerated] {c : E'}
    (hXZ : TendstoInDistribution X l Z (fun _ => μ) μ')
    (hY : TendstoInMeasure μ Y l (fun _ => c))
    (hY_meas : ∀ i, AEMeasurable (Y i) μ) :
    TendstoInDistribution (fun i ω => (X i ω, Y i ω)) l
      (fun ω => (Z ω, c)) (fun _ => μ) μ' :=
  hXZ.prodMk_of_tendstoInMeasure_const X Y Z hY hY_meas

end StatInference
