import StatInference.EmpiricalProcess.WeakConvergence

/-!
# Probability-measure weak-convergence wrappers

This module provides a content-based probability-measure foundation layer for
textbook weak-convergence work, especially Section 25-style material.  The proof
authority is pinned mathlib, usually through the
existing `StatInference.EmpiricalProcess` weak-convergence wrappers already
used by the empirical-process lane.

The declarations here are intentionally theorem-report neutral: they are
compiled local wrappers, not yet source-audited exact textbook theorem reports.
-/

namespace StatInference
namespace ProbabilityMeasure

open Filter MeasureTheory ProbabilityTheory TopologicalSpace

open scoped BoundedContinuousFunction Topology

universe u v w x

/--
Textbook-style weak convergence of probability measures.

This is the measure-level topology on probability measures, matching the
already proved local VdV&W wrapper and mathlib's `ProbabilityMeasure` topology.
-/
def WeakConvergenceProbabilityMeasures
    {S : Type u} {ι : Type v} [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S]
    (μs : ι -> ProbabilityMeasure S) (l : Filter ι)
    (μ : ProbabilityMeasure S) : Prop :=
  StatInference.VdVWWeakConvergenceProbabilityMeasures μs l μ

/--
Weak convergence tested by bounded continuous real functions.

This wraps mathlib's probability-measure integral characterization through the
local empirical-process weak-convergence layer.
-/
theorem weakConvergence_iff_forall_integral_tendsto
    {S : Type u} {ι : Type v} [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S]
    {μs : ι -> ProbabilityMeasure S} {l : Filter ι}
    {μ : ProbabilityMeasure S} :
    WeakConvergenceProbabilityMeasures μs l μ ↔
      ∀ f : S →ᵇ ℝ,
        Tendsto (fun i => ∫ s, f s ∂(μs i : Measure S)) l
          (𝓝 (∫ s, f s ∂(μ : Measure S))) := by
  exact StatInference.vdVWWeakConvergenceProbabilityMeasures_iff_forall_integral_tendsto

/--
Portmanteau bounded-Lipschitz test-function criterion, in the
metric-space form already supplied by mathlib.
-/
theorem weakConvergence_iff_forall_bounded_lipschitz_integral_tendsto
    {S : Type u} {ι : Type v} [MeasurableSpace S] [PseudoEMetricSpace S]
    [OpensMeasurableSpace S]
    {μs : ι -> ProbabilityMeasure S} {l : Filter ι} [l.IsCountablyGenerated]
    {μ : ProbabilityMeasure S} :
    WeakConvergenceProbabilityMeasures μs l μ ↔
      ∀ f : S -> ℝ, (∃ C : ℝ, ∀ x y, dist (f x) (f y) ≤ C) ->
        (∃ L, LipschitzWith L f) ->
          Tendsto (fun i => ∫ s, f s ∂(μs i : Measure S)) l
            (𝓝 (∫ s, f s ∂(μ : Measure S))) := by
  exact
    StatInference.vdVWWeakConvergenceProbabilityMeasures_iff_forall_bounded_lipschitz_integral_tendsto

/-- Closed-set Portmanteau implication for probability-measure weak convergence. -/
theorem WeakConvergenceProbabilityMeasures.limsup_measure_closed_le
    {S : Type u} {ι : Type v} [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S] [HasOuterApproxClosed S]
    {μs : ι -> ProbabilityMeasure S} {l : Filter ι}
    {μ : ProbabilityMeasure S}
    (h : WeakConvergenceProbabilityMeasures μs l μ)
    {F : Set S} (hF : IsClosed F) :
    (l.limsup fun i => (μs i : Measure S) F) ≤ (μ : Measure S) F := by
  exact StatInference.VdVWWeakConvergenceProbabilityMeasures.limsup_measure_closed_le h hF

/-- Open-set Portmanteau implication for probability-measure weak convergence. -/
theorem WeakConvergenceProbabilityMeasures.le_liminf_measure_open
    {S : Type u} {ι : Type v} [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S] [HasOuterApproxClosed S]
    {μs : ι -> ProbabilityMeasure S} {l : Filter ι}
    {μ : ProbabilityMeasure S}
    (h : WeakConvergenceProbabilityMeasures μs l μ)
    {G : Set S} (hG : IsOpen G) :
    (μ : Measure S) G ≤ l.liminf fun i => (μs i : Measure S) G := by
  exact StatInference.VdVWWeakConvergenceProbabilityMeasures.le_liminf_measure_open h hG

/--
Continuity-set Portmanteau implication for probability-measure weak
convergence.

This is the Billingsley Section 25.8 `(i) -> (iii)` shape for ordinary
Borel probability measures: sets whose frontier has zero limiting mass have
convergent probabilities.
-/
theorem WeakConvergenceProbabilityMeasures.tendsto_measure_of_null_frontier
    {S : Type u} {ι : Type v} [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S] [HasOuterApproxClosed S]
    {μs : ι -> ProbabilityMeasure S} {l : Filter ι}
    {μ : ProbabilityMeasure S}
    (h : WeakConvergenceProbabilityMeasures μs l μ)
    {E : Set S} (hE : (μ : Measure S) (frontier E) = 0) :
    Tendsto (fun i => (μs i : Measure S) E) l
      (𝓝 ((μ : Measure S) E)) := by
  exact
    MeasureTheory.ProbabilityMeasure.tendsto_measure_of_null_frontier_of_tendsto'
      h hE

/--
Closed-set Portmanteau converse for probability-measure weak convergence.

This is the reverse direction to
`WeakConvergenceProbabilityMeasures.limsup_measure_closed_le`, under the
countably generated filter hypothesis used by mathlib's Portmanteau API.
-/
theorem weakConvergence_of_forall_isClosed_limsup_measure_le
    {S : Type u} {ι : Type v} [MeasurableSpace S] [TopologicalSpace S]
    [OpensMeasurableSpace S]
    {μs : ι -> ProbabilityMeasure S} {l : Filter ι} [l.IsCountablyGenerated]
    {μ : ProbabilityMeasure S}
    (h : ∀ F : Set S, IsClosed F ->
      l.limsup (fun i => (μs i : Measure S) F) ≤ (μ : Measure S) F) :
    WeakConvergenceProbabilityMeasures μs l μ := by
  exact MeasureTheory.tendsto_of_forall_isClosed_limsup_le' h

/--
Pi-system convergence criterion for probability-measure weak convergence.

This packages mathlib's convergence-determining-class criterion in the
Billingsley/ProbabilityMeasure namespace.  It is useful for Section 25
source crosswalks and for finite-dimensional/cylinder event arguments.
-/
theorem weakConvergence_of_piSystem_tendsto
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
    WeakConvergenceProbabilityMeasures μs l μ := by
  exact hC.tendsto_probabilityMeasure_of_tendsto_of_mem hmeas hlocal h

/--
Tightness of probability measures, backed by mathlib's
`IsTightMeasureSet` via the local empirical-process wrapper.
-/
def ProbabilityMeasuresTight
    {S : Type u} [MeasurableSpace S] [TopologicalSpace S]
    (A : Set (ProbabilityMeasure S)) : Prop :=
  StatInference.VdVWProbabilityMeasuresTight A

/-- Compact-set characterization of probability-measure tightness. -/
theorem probabilityMeasuresTight_iff_exists_compact_measure_compl_le
    {S : Type u} [MeasurableSpace S] [TopologicalSpace S]
    {A : Set (ProbabilityMeasure S)} :
    ProbabilityMeasuresTight A ↔
      ∀ ε, 0 < ε ->
        ∃ K : Set S, IsCompact K ∧
          ∀ μ : ProbabilityMeasure S, μ ∈ A -> (μ : Measure S) (Kᶜ) ≤ ε := by
  exact StatInference.vdVWProbabilityMeasuresTight_iff_exists_compact_measure_compl_le

/-- Prokhorov compactness wrapper for tight sets of probability measures. -/
theorem ProbabilityMeasuresTight.isCompact_closure
    {S : Type u} [MeasurableSpace S] [TopologicalSpace S] [T2Space S]
    [BorelSpace S] {A : Set (ProbabilityMeasure S)}
    (hA : ProbabilityMeasuresTight A) :
    IsCompact (closure A) := by
  exact StatInference.VdVWProbabilityMeasuresTight.isCompact_closure hA

/--
Levy-Prokhorov characterization of weak convergence on separable
pseudometric spaces.
-/
theorem weakConvergence_iff_levyProkhorov_tendsto
    {S : Type u} {ι : Type v} [MeasurableSpace S] [PseudoMetricSpace S]
    [OpensMeasurableSpace S] [SeparableSpace S]
    {μs : ι -> ProbabilityMeasure S} {l : Filter ι}
    {μ : ProbabilityMeasure S} :
    WeakConvergenceProbabilityMeasures μs l μ ↔
      Tendsto (fun i => LevyProkhorov.ofMeasure (μs i)) l
        (𝓝 (LevyProkhorov.ofMeasure μ)) := by
  exact StatInference.vdVWWeakConvergenceProbabilityMeasures_iff_levyProkhorov_tendsto

/-- Levy-Prokhorov distance-to-zero form of weak convergence. -/
theorem weakConvergence_iff_levyProkhorovDist_tendsto_zero
    {S : Type u} {ι : Type v} [MeasurableSpace S] [PseudoMetricSpace S]
    [OpensMeasurableSpace S] [SeparableSpace S]
    {μs : ι -> ProbabilityMeasure S} {l : Filter ι}
    {μ : ProbabilityMeasure S} :
    WeakConvergenceProbabilityMeasures μs l μ ↔
      Tendsto (fun i => levyProkhorovDist (μs i : Measure S) (μ : Measure S)) l (𝓝 0) := by
  exact StatInference.vdVWWeakConvergenceProbabilityMeasures_iff_levyProkhorovDist_tendsto_zero

/-- Continuous mapping theorem for probability measures. -/
theorem WeakConvergenceProbabilityMeasures.map_continuous
    {S : Type u} {T : Type v} {ι : Type w}
    [MeasurableSpace S] [TopologicalSpace S] [OpensMeasurableSpace S]
    [MeasurableSpace T] [TopologicalSpace T] [BorelSpace T]
    {μs : ι -> ProbabilityMeasure S} {l : Filter ι}
    {μ : ProbabilityMeasure S} {g : S -> T}
    (h : WeakConvergenceProbabilityMeasures μs l μ)
    (hg : Continuous g) :
    WeakConvergenceProbabilityMeasures
      (fun i => (μs i).map hg.measurable.aemeasurable) l
      (μ.map hg.measurable.aemeasurable) := by
  exact StatInference.VdVWWeakConvergenceProbabilityMeasures.map_continuous h hg

/-- Binary product-law weak convergence for probability measures. -/
theorem WeakConvergenceProbabilityMeasures.prod
    {S : Type u} {T : Type v} {ι : Type w}
    [MeasurableSpace S] [TopologicalSpace S] [SecondCountableTopology S]
    [PseudoMetrizableSpace S] [OpensMeasurableSpace S]
    [MeasurableSpace T] [TopologicalSpace T] [SecondCountableTopology T]
    [PseudoMetrizableSpace T] [OpensMeasurableSpace T]
    {μs : ι -> ProbabilityMeasure S} {νs : ι -> ProbabilityMeasure T}
    {l : Filter ι} {μ : ProbabilityMeasure S} {ν : ProbabilityMeasure T}
    (hμ : WeakConvergenceProbabilityMeasures μs l μ)
    (hν : WeakConvergenceProbabilityMeasures νs l ν) :
    WeakConvergenceProbabilityMeasures
      (fun i => (μs i).prod (νs i)) l (μ.prod ν) := by
  exact StatInference.VdVWWeakConvergenceProbabilityMeasures.prod hμ hν

/-- Finite product-law weak convergence for probability measures. -/
theorem WeakConvergenceProbabilityMeasures.pi
    {J : Type u} [Fintype J] {S : J -> Type v} {ι : Type w}
    [∀ j, MeasurableSpace (S j)] [∀ j, TopologicalSpace (S j)]
    [∀ j, SecondCountableTopology (S j)] [∀ j, PseudoMetrizableSpace (S j)]
    [∀ j, OpensMeasurableSpace (S j)]
    {μs : ι -> (j : J) -> ProbabilityMeasure (S j)}
    {l : Filter ι} {μ : (j : J) -> ProbabilityMeasure (S j)}
    (hμ : ∀ j, WeakConvergenceProbabilityMeasures (fun n => μs n j) l (μ j)) :
    WeakConvergenceProbabilityMeasures
      (fun n => ProbabilityMeasure.pi (μs n)) l (ProbabilityMeasure.pi μ) := by
  exact StatInference.VdVWWeakConvergenceProbabilityMeasures.pi hμ

/-- Finite-dimensional restriction of a weakly convergent product-process law. -/
theorem WeakConvergenceProbabilityMeasures.finiteDimensionalRestrict
    {I : Type u} {S : I -> Type v} {ι : Type w}
    [∀ i, MeasurableSpace (S i)] [∀ i, TopologicalSpace (S i)]
    [∀ i, OpensMeasurableSpace (S i)]
    [MeasurableSpace ((i : I) -> S i)] [OpensMeasurableSpace ((i : I) -> S i)]
    {μs : ι -> ProbabilityMeasure ((i : I) -> S i)}
    {l : Filter ι} {μ : ProbabilityMeasure ((i : I) -> S i)}
    (hμ : WeakConvergenceProbabilityMeasures μs l μ)
    (s : Finset I)
    [MeasurableSpace ((i : s) -> S i)] [BorelSpace ((i : s) -> S i)] :
    WeakConvergenceProbabilityMeasures
      (fun n => (μs n).map ((Finset.continuous_restrict s).measurable.aemeasurable)) l
      (μ.map ((Finset.continuous_restrict s).measurable.aemeasurable)) := by
  exact StatInference.VdVWWeakConvergenceProbabilityMeasures.finiteDimensionalRestrict hμ s

/--
Continuous mapping theorem for convergence in distribution of
measurable random variables.
-/
theorem tendstoInDistribution_continuous_comp
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
  StatInference.vdVWTendstoInDistribution_continuous_comp h hg

/--
Slutsky product theorem for a convergence-in-distribution term and
a same-domain convergence-in-probability term to a constant.
-/
theorem tendstoInDistribution_prodMk_of_tendstoInMeasure_const
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
  StatInference.vdVWTendstoInDistribution_prodMk_of_tendstoInMeasure_const
    hXZ hY hY_meas

end ProbabilityMeasure
end StatInference
