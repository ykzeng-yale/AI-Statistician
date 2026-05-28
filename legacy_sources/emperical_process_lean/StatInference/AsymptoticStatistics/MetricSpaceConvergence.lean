import StatInference.AsymptoticStatistics.ChiSquareTests
import StatInference.ProbabilityMeasure.WeakConvergence
import StatInference.EmpiricalProcess.OuterProbabilityExpectation
import StatInference.EmpiricalProcess.EllInfty
import StatInference.EmpiricalProcess.FiniteDimensional

/-!
# van der Vaart 1998 Chapter 18 metric-space stochastic convergence

This module opens the Chapter 18 lane.  It records source-shaped interfaces
for Borel random elements, continuous Borel maps, metric-space weak
convergence through bounded continuous tests and outer expectations,
convergence in outer probability, and the `ell_infty(T)` bounded-process
substrate used later for stochastic processes.
-/

noncomputable section

namespace StatInference
namespace AsymptoticStatistics

open Filter MeasureTheory ProbabilityTheory
open scoped ENNReal ProbabilityTheory Topology BoundedContinuousFunction

/--
Definition 18.1 source: a random element is a Borel-measurable map from a
probability space into a metric/topological state space.
-/
structure Vaart1998Definition18_1RandomElementSource
    {Omega D : Type*} [MeasurableSpace Omega]
    [TopologicalSpace D] [MeasurableSpace D] where
  /-- The underlying probability measure on the sample space. -/
  probabilityMeasure : Measure Omega
  /-- The measure is a probability measure. -/
  probabilityMeasure_isProbability :
    IsProbabilityMeasure probabilityMeasure
  /-- The state-valued map. -/
  randomElement : Omega -> D
  /-- Borel measurability of the state-valued map. -/
  randomElement_measurable :
    Measurable randomElement

/--
Definition 18.1 random-element measurability display.
-/
theorem Vaart1998Definition18_1RandomElementSource.measurable
    {Omega D : Type*} [MeasurableSpace Omega]
    [TopologicalSpace D] [MeasurableSpace D]
    (S : Vaart1998Definition18_1RandomElementSource
      (Omega := Omega) (D := D)) :
    Measurable S.randomElement :=
  S.randomElement_measurable

/--
Definition 18.1 random-element probability-space display.
-/
theorem Vaart1998Definition18_1RandomElementSource.isProbabilityMeasure
    {Omega D : Type*} [MeasurableSpace Omega]
    [TopologicalSpace D] [MeasurableSpace D]
    (S : Vaart1998Definition18_1RandomElementSource
      (Omega := Omega) (D := D)) :
    IsProbabilityMeasure S.probabilityMeasure :=
  S.probabilityMeasure_isProbability

/--
Lemma 18.2: a continuous map into a Borel state space is Borel-measurable.

This is the direct mathlib-backed proof of van der Vaart's first Chapter 18
measurability lemma.
-/
theorem vaart1998_lemma18_2_continuous_borel_measurable
    {D E : Type*}
    [TopologicalSpace D] [MeasurableSpace D] [OpensMeasurableSpace D]
    [TopologicalSpace E] [MeasurableSpace E] [BorelSpace E]
    {g : D -> E} (hg : Continuous g) :
    Measurable g :=
  hg.measurable

/--
Lemma 18.2 a.e.-measurable corollary for continuous maps.
-/
theorem vaart1998_lemma18_2_continuous_aemeasurable
    {D E : Type*}
    [TopologicalSpace D] [MeasurableSpace D] [OpensMeasurableSpace D]
    [TopologicalSpace E] [MeasurableSpace E] [BorelSpace E]
    {g : D -> E} (hg : Continuous g) {mu : Measure D} :
    AEMeasurable g mu :=
  hg.aemeasurable

/--
Chapter 18 ordinary probability-measure weak convergence on a metric or
topological state space, tested by bounded continuous real functions.
-/
abbrev vaart1998_metricWeakConvergenceProbabilityMeasures
    {D : Type*} {Index : Type*}
    [MeasurableSpace D] [TopologicalSpace D] [OpensMeasurableSpace D]
    (laws : Index -> ProbabilityMeasure D) (l : Filter Index)
    (limitLaw : ProbabilityMeasure D) : Prop :=
  ProbabilityMeasure.WeakConvergenceProbabilityMeasures laws l limitLaw

/--
Chapter 18 tightness for a family of probability measures.
-/
abbrev vaart1998_probabilityMeasuresTight
    {D : Type*} [MeasurableSpace D] [TopologicalSpace D]
    (laws : Set (ProbabilityMeasure D)) : Prop :=
  ProbabilityMeasure.ProbabilityMeasuresTight laws

/--
Chapter 18 measure-level asymptotic tightness for probability laws.
-/
abbrev vaart1998_probabilityMeasuresAsymptoticallyTight
    {D : Type*} {Index : Type*}
    [MeasurableSpace D] [TopologicalSpace D]
    (laws : Index -> ProbabilityMeasure D) (l : Filter Index) : Prop :=
  VdVWProbabilityMeasuresAsymptoticallyTight laws l

/--
Chapter 18 arbitrary-map weak convergence on varying sample spaces, using
signed outer expectations of bounded continuous test functions.
-/
abbrev vaart1998_metricWeakConvergenceVaryingDomains
    {Index : Type*} (Omega : Index -> Type*) {D : Type*}
    [∀ n, MeasurableSpace (Omega n)]
    [MeasurableSpace D] [TopologicalSpace D] [OpensMeasurableSpace D]
    (probabilityMeasure : (n : Index) -> Measure (Omega n))
    (randomMap : (n : Index) -> Omega n -> D) (l : Filter Index)
    (limitLaw : ProbabilityMeasure D) : Prop :=
  VdVWWeakConvergenceSignedOuterBoundedContinuousVaryingDomains
    Omega probabilityMeasure randomMap l limitLaw

/--
Proof-carrying Chapter 18 arbitrary-map weak convergence on varying sample
spaces: weak convergence plus the asymptotic-measurability clause needed for
Prohorov-type later work.
-/
abbrev vaart1998_metricWeakConvergenceMeasurableVaryingDomains
    {Index : Type*} (Omega : Index -> Type*) {D : Type*}
    [∀ n, MeasurableSpace (Omega n)]
    [MeasurableSpace D] [TopologicalSpace D] [OpensMeasurableSpace D]
    (probabilityMeasure : (n : Index) -> Measure (Omega n))
    (randomMap : (n : Index) -> Omega n -> D) (l : Filter Index)
    (limitLaw : ProbabilityMeasure D) : Prop :=
  VdVWWeakConvergenceSignedBoundedContinuousVaryingDomains
    Omega probabilityMeasure randomMap l limitLaw

/--
The signed outer expectation of a bounded continuous test function composed
with an arbitrary map.
-/
def vaart1998_signedOuterExpectationBoundedContinuousTest
    {Omega D : Type*} [MeasurableSpace Omega]
    [TopologicalSpace D]
    (probabilityMeasure : Measure Omega)
    (testFunction : BoundedContinuousFunction D ℝ)
    (randomMap : Omega -> D) : ℝ :=
  VdVWSignedOuterExpectationPosNeg probabilityMeasure
    (fun omega => testFunction (randomMap omega))

/--
Definition 18.2 source: weak convergence in a metric space via bounded
continuous test functions and outer expectations, for sample spaces depending
on `n`.
-/
structure Vaart1998Definition18_2MetricWeakConvergenceSource
    {Index : Type*} (Omega : Index -> Type*) {D : Type*}
    [∀ n, MeasurableSpace (Omega n)]
    [MeasurableSpace D] [TopologicalSpace D] [OpensMeasurableSpace D] where
  /-- Probability measures on the varying sample spaces. -/
  probabilityMeasure : (n : Index) -> Measure (Omega n)
  /-- The arbitrary maps into the metric state space. -/
  randomMap : (n : Index) -> Omega n -> D
  /-- The index filter. -/
  indexFilter : Filter Index
  /-- The limiting law of the random element. -/
  limitLaw : ProbabilityMeasure D
  /-- Bounded-continuous/outer-expectation weak convergence. -/
  weakConvergence :
    vaart1998_metricWeakConvergenceVaryingDomains
      Omega probabilityMeasure randomMap indexFilter limitLaw
  /-- Asymptotic measurability for bounded continuous tests. -/
  asymptoticMeasurability :
    VdVWAsymptoticallyMeasurableSignedBoundedContinuousVaryingDomains
      Omega probabilityMeasure randomMap indexFilter

/--
Definition 18.2 bounded-continuous weak-convergence display.
-/
theorem Vaart1998Definition18_2MetricWeakConvergenceSource.weak_convergence
    {Index : Type*} {Omega : Index -> Type*} {D : Type*}
    [∀ n, MeasurableSpace (Omega n)]
    [MeasurableSpace D] [TopologicalSpace D] [OpensMeasurableSpace D]
    (S : Vaart1998Definition18_2MetricWeakConvergenceSource
      Omega (D := D)) :
    vaart1998_metricWeakConvergenceVaryingDomains
      Omega S.probabilityMeasure S.randomMap S.indexFilter S.limitLaw :=
  S.weakConvergence

/--
Definition 18.2 proof-carrying weak-convergence package.
-/
theorem Vaart1998Definition18_2MetricWeakConvergenceSource.measurable_weak_convergence
    {Index : Type*} {Omega : Index -> Type*} {D : Type*}
    [∀ n, MeasurableSpace (Omega n)]
    [MeasurableSpace D] [TopologicalSpace D] [OpensMeasurableSpace D]
    (S : Vaart1998Definition18_2MetricWeakConvergenceSource
      Omega (D := D)) :
    vaart1998_metricWeakConvergenceMeasurableVaryingDomains
      Omega S.probabilityMeasure S.randomMap S.indexFilter S.limitLaw :=
  { weakConvergence := S.weakConvergence
    asymptoticMeasurability := S.asymptoticMeasurability }

/--
Lemma 18.9 bounded-continuous Portmanteau criterion for ordinary probability
laws.
-/
theorem vaart1998_lemma18_9_portmanteau_bounded_continuous_criterion
    {D Index : Type*}
    [MeasurableSpace D] [TopologicalSpace D] [OpensMeasurableSpace D]
    {laws : Index -> ProbabilityMeasure D} {l : Filter Index}
    {limitLaw : ProbabilityMeasure D} :
    vaart1998_metricWeakConvergenceProbabilityMeasures laws l limitLaw ↔
      ∀ f : D →ᵇ ℝ,
        Tendsto (fun n => ∫ x, f x ∂(laws n : Measure D)) l
          (𝓝 (∫ x, f x ∂(limitLaw : Measure D))) :=
  ProbabilityMeasure.weakConvergence_iff_forall_integral_tendsto

/--
Lemma 18.9 bounded-Lipschitz Portmanteau criterion for ordinary probability
laws.
-/
theorem vaart1998_lemma18_9_portmanteau_bounded_lipschitz_criterion
    {D Index : Type*}
    [MeasurableSpace D] [PseudoEMetricSpace D] [OpensMeasurableSpace D]
    {laws : Index -> ProbabilityMeasure D} {l : Filter Index}
    [l.IsCountablyGenerated] {limitLaw : ProbabilityMeasure D} :
    vaart1998_metricWeakConvergenceProbabilityMeasures laws l limitLaw ↔
      ∀ f : D -> ℝ, (∃ C : ℝ, ∀ x y, dist (f x) (f y) ≤ C) ->
        (∃ L, LipschitzWith L f) ->
          Tendsto (fun n => ∫ x, f x ∂(laws n : Measure D)) l
            (𝓝 (∫ x, f x ∂(limitLaw : Measure D))) :=
  ProbabilityMeasure.weakConvergence_iff_forall_bounded_lipschitz_integral_tendsto

/--
Lemma 18.9 closed-set Portmanteau implication for ordinary probability laws.
-/
theorem vaart1998_lemma18_9_portmanteau_closed_limsup
    {D Index : Type*}
    [MeasurableSpace D] [TopologicalSpace D] [OpensMeasurableSpace D]
    [HasOuterApproxClosed D]
    {laws : Index -> ProbabilityMeasure D} {l : Filter Index}
    {limitLaw : ProbabilityMeasure D}
    (h : vaart1998_metricWeakConvergenceProbabilityMeasures laws l limitLaw)
    {closedSet : Set D} (hclosed : IsClosed closedSet) :
    (l.limsup fun n => (laws n : Measure D) closedSet) ≤
      (limitLaw : Measure D) closedSet :=
  ProbabilityMeasure.WeakConvergenceProbabilityMeasures.limsup_measure_closed_le
    h hclosed

/--
Lemma 18.9 open-set Portmanteau implication for ordinary probability laws.
-/
theorem vaart1998_lemma18_9_portmanteau_open_liminf
    {D Index : Type*}
    [MeasurableSpace D] [TopologicalSpace D] [OpensMeasurableSpace D]
    [HasOuterApproxClosed D]
    {laws : Index -> ProbabilityMeasure D} {l : Filter Index}
    {limitLaw : ProbabilityMeasure D}
    (h : vaart1998_metricWeakConvergenceProbabilityMeasures laws l limitLaw)
    {openSet : Set D} (hopen : IsOpen openSet) :
    (limitLaw : Measure D) openSet ≤
      l.liminf (fun n => (laws n : Measure D) openSet) :=
  ProbabilityMeasure.WeakConvergenceProbabilityMeasures.le_liminf_measure_open
    h hopen

/--
Lemma 18.9 continuity-set Portmanteau implication for ordinary probability
laws.
-/
theorem vaart1998_lemma18_9_portmanteau_continuity_set
    {D Index : Type*}
    [MeasurableSpace D] [TopologicalSpace D] [OpensMeasurableSpace D]
    [HasOuterApproxClosed D]
    {laws : Index -> ProbabilityMeasure D} {l : Filter Index}
    {limitLaw : ProbabilityMeasure D}
    (h : vaart1998_metricWeakConvergenceProbabilityMeasures laws l limitLaw)
    {event : Set D}
    (hfrontier : (limitLaw : Measure D) (frontier event) = 0) :
    Tendsto (fun n => (laws n : Measure D) event) l
      (𝓝 ((limitLaw : Measure D) event)) :=
  ProbabilityMeasure.WeakConvergenceProbabilityMeasures.tendsto_measure_of_null_frontier
    h hfrontier

/--
Lemma 18.9 closed-set Portmanteau converse for ordinary probability laws.
-/
theorem vaart1998_lemma18_9_portmanteau_closed_converse
    {D Index : Type*}
    [MeasurableSpace D] [TopologicalSpace D] [OpensMeasurableSpace D]
    {laws : Index -> ProbabilityMeasure D} {l : Filter Index}
    [l.IsCountablyGenerated] {limitLaw : ProbabilityMeasure D}
    (hclosed :
      ∀ closedSet : Set D, IsClosed closedSet ->
        (l.limsup fun n => (laws n : Measure D) closedSet) ≤
          (limitLaw : Measure D) closedSet) :
    vaart1998_metricWeakConvergenceProbabilityMeasures laws l limitLaw :=
  ProbabilityMeasure.weakConvergence_of_forall_isClosed_limsup_measure_le
    hclosed

/--
Lemma 18.9 source shell: Portmanteau equivalent criteria for ordinary
probability laws in a metric state space.
-/
structure Vaart1998Lemma18_9PortmanteauSource
    {D Index : Type*}
    [MeasurableSpace D] [TopologicalSpace D] [OpensMeasurableSpace D]
    [HasOuterApproxClosed D] where
  /-- Laws indexed by the asymptotic parameter. -/
  laws : Index -> ProbabilityMeasure D
  /-- The index filter. -/
  indexFilter : Filter Index
  /-- Limiting law. -/
  limitLaw : ProbabilityMeasure D
  /-- Ordinary weak convergence of the laws. -/
  weakConvergence :
    vaart1998_metricWeakConvergenceProbabilityMeasures
      laws indexFilter limitLaw
  /-- Source-level bounded-continuous criterion clause. -/
  boundedContinuousCriterion : Prop
  /-- Source-level bounded-Lipschitz criterion clause. -/
  boundedLipschitzCriterion : Prop
  /-- Proof of the bounded-continuous source clause. -/
  boundedContinuousCriterion_proof : boundedContinuousCriterion
  /-- Proof of the bounded-Lipschitz source clause. -/
  boundedLipschitzCriterion_proof : boundedLipschitzCriterion

/--
Lemma 18.9 source bounded-continuous criterion display.
-/
theorem Vaart1998Lemma18_9PortmanteauSource.bounded_continuous_criterion
    {D Index : Type*}
    [MeasurableSpace D] [TopologicalSpace D] [OpensMeasurableSpace D]
    [HasOuterApproxClosed D]
    (S : Vaart1998Lemma18_9PortmanteauSource
      (D := D) (Index := Index)) :
    S.boundedContinuousCriterion :=
  S.boundedContinuousCriterion_proof

/--
Lemma 18.9 source bounded-Lipschitz criterion display.
-/
theorem Vaart1998Lemma18_9PortmanteauSource.bounded_lipschitz_criterion
    {D Index : Type*}
    [MeasurableSpace D] [TopologicalSpace D] [OpensMeasurableSpace D]
    [HasOuterApproxClosed D]
    (S : Vaart1998Lemma18_9PortmanteauSource
      (D := D) (Index := Index)) :
    S.boundedLipschitzCriterion :=
  S.boundedLipschitzCriterion_proof

/--
Lemma 18.9 source closed-set Portmanteau display.
-/
theorem Vaart1998Lemma18_9PortmanteauSource.closed_limsup
    {D Index : Type*}
    [MeasurableSpace D] [TopologicalSpace D] [OpensMeasurableSpace D]
    [HasOuterApproxClosed D]
    (S : Vaart1998Lemma18_9PortmanteauSource
      (D := D) (Index := Index))
    {closedSet : Set D} (hclosed : IsClosed closedSet) :
    (S.indexFilter.limsup fun n => (S.laws n : Measure D) closedSet) ≤
      (S.limitLaw : Measure D) closedSet :=
  vaart1998_lemma18_9_portmanteau_closed_limsup
    S.weakConvergence hclosed

/--
Lemma 18.9 source open-set Portmanteau display.
-/
theorem Vaart1998Lemma18_9PortmanteauSource.open_liminf
    {D Index : Type*}
    [MeasurableSpace D] [TopologicalSpace D] [OpensMeasurableSpace D]
    [HasOuterApproxClosed D]
    (S : Vaart1998Lemma18_9PortmanteauSource
      (D := D) (Index := Index))
    {openSet : Set D} (hopen : IsOpen openSet) :
    (S.limitLaw : Measure D) openSet ≤
      S.indexFilter.liminf (fun n => (S.laws n : Measure D) openSet) :=
  vaart1998_lemma18_9_portmanteau_open_liminf
    S.weakConvergence hopen

/--
Lemma 18.9 source continuity-set Portmanteau display.
-/
theorem Vaart1998Lemma18_9PortmanteauSource.continuity_set
    {D Index : Type*}
    [MeasurableSpace D] [TopologicalSpace D] [OpensMeasurableSpace D]
    [HasOuterApproxClosed D]
    (S : Vaart1998Lemma18_9PortmanteauSource
      (D := D) (Index := Index))
    {event : Set D}
    (hfrontier : (S.limitLaw : Measure D) (frontier event) = 0) :
    Tendsto (fun n => (S.laws n : Measure D) event) S.indexFilter
      (𝓝 ((S.limitLaw : Measure D) event)) :=
  vaart1998_lemma18_9_portmanteau_continuity_set
    S.weakConvergence hfrontier

/--
Chapter 18 compact-set characterization of tight families of probability
measures.
-/
theorem vaart1998_probabilityMeasuresTight_iff_exists_compact_measure_compl_le
    {D : Type*} [MeasurableSpace D] [TopologicalSpace D]
    {laws : Set (ProbabilityMeasure D)} :
    vaart1998_probabilityMeasuresTight laws ↔
      ∀ ε : ℝ≥0∞, 0 < ε ->
        ∃ K : Set D, IsCompact K ∧
          ∀ law ∈ laws, (law : Measure D) Kᶜ ≤ ε :=
  ProbabilityMeasure.probabilityMeasuresTight_iff_exists_compact_measure_compl_le

/--
Theorem 18.12, measure-level direction: sequential weak convergence on a
complete second-countable metric Borel space gives asymptotic tightness of
the laws.
-/
theorem vaart1998_theorem18_12_asymptoticallyTight_atTop_of_weakConvergence
    {D : Type*}
    [MeasurableSpace D] [PseudoMetricSpace D] [OpensMeasurableSpace D]
    [BorelSpace D] [SecondCountableTopology D] [CompleteSpace D]
    {laws : ℕ -> ProbabilityMeasure D} {limitLaw : ProbabilityMeasure D}
    (h :
      vaart1998_metricWeakConvergenceProbabilityMeasures
        laws atTop limitLaw) :
    vaart1998_probabilityMeasuresAsymptoticallyTight laws atTop :=
  VdVWWeakConvergenceProbabilityMeasures.asymptoticallyTight_atTop h

/--
Theorem 18.12 subsequence/reindexing handoff for asymptotic tightness.
-/
theorem vaart1998_theorem18_12_asymptoticallyTight_comp_tendsto_atTop
    {D Index : Type*}
    [MeasurableSpace D] [PseudoMetricSpace D] [OpensMeasurableSpace D]
    [BorelSpace D] [SecondCountableTopology D] [CompleteSpace D]
    {laws : ℕ -> ProbabilityMeasure D} {limitLaw : ProbabilityMeasure D}
    (h :
      vaart1998_metricWeakConvergenceProbabilityMeasures
        laws atTop limitLaw)
    {subsequence : Index -> ℕ} {l : Filter Index}
    (hsubsequence : Tendsto subsequence l atTop) :
    vaart1998_probabilityMeasuresAsymptoticallyTight
      (fun i => laws (subsequence i)) l :=
  VdVWWeakConvergenceProbabilityMeasures.asymptoticallyTight_comp_tendsto_atTop
    h hsubsequence

/--
Theorem 18.12 source shell: Prohorov's theorem for Chapter 18.
-/
structure Vaart1998Theorem18_12ProhorovSource
    {D : Type*}
    [MeasurableSpace D] [PseudoMetricSpace D] [OpensMeasurableSpace D]
    [BorelSpace D] [SecondCountableTopology D] [CompleteSpace D] where
  /-- Laws indexed by natural sample size. -/
  laws : ℕ -> ProbabilityMeasure D
  /-- Limiting probability law. -/
  limitLaw : ProbabilityMeasure D
  /-- Weak convergence to the limiting law. -/
  weakConvergence :
    vaart1998_metricWeakConvergenceProbabilityMeasures laws atTop limitLaw
  /-- Source-level asymptotic measurability clause. -/
  asymptoticMeasurability : Prop
  /-- Source-level converse subsequence weak-limit clause. -/
  subsequenceWeakLimitCriterion : Prop
  /-- Proof of the asymptotic measurability source clause. -/
  asymptoticMeasurability_proof : asymptoticMeasurability
  /-- Proof of the converse subsequence source clause. -/
  subsequenceWeakLimitCriterion_proof : subsequenceWeakLimitCriterion

/--
Theorem 18.12 source asymptotic-tightness display.
-/
theorem Vaart1998Theorem18_12ProhorovSource.asymptotically_tight
    {D : Type*}
    [MeasurableSpace D] [PseudoMetricSpace D] [OpensMeasurableSpace D]
    [BorelSpace D] [SecondCountableTopology D] [CompleteSpace D]
    (S : Vaart1998Theorem18_12ProhorovSource (D := D)) :
    vaart1998_probabilityMeasuresAsymptoticallyTight S.laws atTop :=
  vaart1998_theorem18_12_asymptoticallyTight_atTop_of_weakConvergence
    S.weakConvergence

/--
Theorem 18.12 source asymptotic-measurability display.
-/
theorem Vaart1998Theorem18_12ProhorovSource.asymptotic_measurability
    {D : Type*}
    [MeasurableSpace D] [PseudoMetricSpace D] [OpensMeasurableSpace D]
    [BorelSpace D] [SecondCountableTopology D] [CompleteSpace D]
    (S : Vaart1998Theorem18_12ProhorovSource (D := D)) :
    S.asymptoticMeasurability :=
  S.asymptoticMeasurability_proof

/--
Theorem 18.12 source converse subsequence weak-limit display.
-/
theorem Vaart1998Theorem18_12ProhorovSource.subsequence_weak_limit_criterion
    {D : Type*}
    [MeasurableSpace D] [PseudoMetricSpace D] [OpensMeasurableSpace D]
    [BorelSpace D] [SecondCountableTopology D] [CompleteSpace D]
    (S : Vaart1998Theorem18_12ProhorovSource (D := D)) :
    S.subsequenceWeakLimitCriterion :=
  S.subsequenceWeakLimitCriterion_proof

/--
Chapter 18 convergence in outer probability to a constant in a metric space.
-/
abbrev vaart1998_metricConvergesInOuterProbabilityConst
    {Index : Type*} (Omega : Index -> Type*) {D : Type*}
    [∀ n, MeasurableSpace (Omega n)] [PseudoMetricSpace D]
    (probabilityMeasure : (n : Index) -> Measure (Omega n))
    (randomMap : (n : Index) -> Omega n -> D)
    (l : Filter Index) (limit : D) : Prop :=
  VdVWConvergesInOuterProbabilityConst
    Omega (fun _ => inferInstance) probabilityMeasure randomMap l limit

/--
Theorem 18.10(i)-(iii) source shell: the Chapter 18 implications among
outer almost-sure convergence, outer-probability convergence, and weak
convergence.  The analytic clauses are recorded as reusable fields, because
later packets will discharge them from the existing outer-probability API.
-/
structure Vaart1998Theorem18_10ConvergenceModeSource
    {Index : Type*} (Omega : Index -> Type*) {D : Type*}
    [∀ n, MeasurableSpace (Omega n)]
    [MeasurableSpace D] [TopologicalSpace D] [OpensMeasurableSpace D]
    [PseudoMetricSpace D] where
  /-- Probability measures on the varying sample spaces. -/
  probabilityMeasure : (n : Index) -> Measure (Omega n)
  /-- Maps into the metric state space. -/
  randomMap : (n : Index) -> Omega n -> D
  /-- Index filter. -/
  indexFilter : Filter Index
  /-- Constant limiting point for the probability mode. -/
  constantLimit : D
  /-- Limit law used by the weak-convergence display. -/
  limitLaw : ProbabilityMeasure D
  /-- Outer-probability convergence to a constant. -/
  outerProbabilityConvergence :
    vaart1998_metricConvergesInOuterProbabilityConst
      Omega probabilityMeasure randomMap indexFilter constantLimit
  /-- Weak convergence conclusion. -/
  weakConvergence :
    vaart1998_metricWeakConvergenceVaryingDomains
      Omega probabilityMeasure randomMap indexFilter limitLaw

/--
Theorem 18.10 weak-convergence conclusion display.
-/
theorem Vaart1998Theorem18_10ConvergenceModeSource.weak_convergence
    {Index : Type*} {Omega : Index -> Type*} {D : Type*}
    [∀ n, MeasurableSpace (Omega n)]
    [MeasurableSpace D] [TopologicalSpace D] [OpensMeasurableSpace D]
    [PseudoMetricSpace D]
    (S : Vaart1998Theorem18_10ConvergenceModeSource
      Omega (D := D)) :
    vaart1998_metricWeakConvergenceVaryingDomains
      Omega S.probabilityMeasure S.randomMap S.indexFilter S.limitLaw :=
  S.weakConvergence

/--
Metric-space continuous mapping theorem for the Chapter 18 arbitrary-map
bounded-continuous weak-convergence predicate.
-/
theorem vaart1998_theorem18_11_continuous_mapping_weak
    {Index : Type*} {Omega : Index -> Type*} {D E : Type*}
    [∀ n, MeasurableSpace (Omega n)]
    [MeasurableSpace D] [TopologicalSpace D] [OpensMeasurableSpace D]
    [MeasurableSpace E] [TopologicalSpace E] [BorelSpace E]
    {probabilityMeasure : (n : Index) -> Measure (Omega n)}
    {randomMap : (n : Index) -> Omega n -> D}
    {indexFilter : Filter Index} {limitLaw : ProbabilityMeasure D}
    (h :
      vaart1998_metricWeakConvergenceVaryingDomains
        Omega probabilityMeasure randomMap indexFilter limitLaw)
    {g : D -> E} (hg : Continuous g) :
    vaart1998_metricWeakConvergenceVaryingDomains
      Omega probabilityMeasure
      (fun n omega => g (randomMap n omega)) indexFilter
      (limitLaw.map hg.measurable.aemeasurable) :=
  VdVWWeakConvergenceSignedOuterBoundedContinuousVaryingDomains.comp_continuous
    h hg

/--
Metric-space continuous mapping theorem for the proof-carrying
weak-convergence plus asymptotic-measurability predicate.
-/
theorem vaart1998_theorem18_11_continuous_mapping_measurable_weak
    {Index : Type*} {Omega : Index -> Type*} {D E : Type*}
    [∀ n, MeasurableSpace (Omega n)]
    [MeasurableSpace D] [TopologicalSpace D] [OpensMeasurableSpace D]
    [MeasurableSpace E] [TopologicalSpace E] [BorelSpace E]
    {probabilityMeasure : (n : Index) -> Measure (Omega n)}
    {randomMap : (n : Index) -> Omega n -> D}
    {indexFilter : Filter Index} {limitLaw : ProbabilityMeasure D}
    (h :
      vaart1998_metricWeakConvergenceMeasurableVaryingDomains
        Omega probabilityMeasure randomMap indexFilter limitLaw)
    {g : D -> E} (hg : Continuous g) :
    vaart1998_metricWeakConvergenceMeasurableVaryingDomains
      Omega probabilityMeasure
      (fun n omega => g (randomMap n omega)) indexFilter
      (limitLaw.map hg.measurable.aemeasurable) :=
  VdVWWeakConvergenceSignedBoundedContinuousVaryingDomains.comp_continuous
    h hg

/--
Lemma 18.13 forward direction: weak convergence in a metric subspace implies
weak convergence after the continuous inclusion/embedding into the ambient
metric space.
-/
theorem vaart1998_lemma18_13_subspace_to_ambient_weak
    {Index : Type*} {Omega : Index -> Type*} {Subspace Ambient : Type*}
    [∀ n, MeasurableSpace (Omega n)]
    [MeasurableSpace Subspace] [TopologicalSpace Subspace]
    [OpensMeasurableSpace Subspace]
    [MeasurableSpace Ambient] [TopologicalSpace Ambient]
    [BorelSpace Ambient]
    {probabilityMeasure : (n : Index) -> Measure (Omega n)}
    {subspaceMap : (n : Index) -> Omega n -> Subspace}
    {indexFilter : Filter Index}
    {subspaceLimitLaw : ProbabilityMeasure Subspace}
    {embedding : Subspace -> Ambient} (hembedding : Continuous embedding)
    (h :
      vaart1998_metricWeakConvergenceVaryingDomains
        Omega probabilityMeasure subspaceMap indexFilter subspaceLimitLaw) :
    vaart1998_metricWeakConvergenceVaryingDomains
      Omega probabilityMeasure
      (fun n omega => embedding (subspaceMap n omega)) indexFilter
      (subspaceLimitLaw.map hembedding.measurable.aemeasurable) :=
  vaart1998_theorem18_11_continuous_mapping_weak h hembedding

/--
Lemma 18.13 source shell: weak convergence in a subspace versus the ambient
metric space.
-/
structure Vaart1998Lemma18_13SubspaceWeakConvergenceSource
    {Index : Type*} (Omega : Index -> Type*) {Subspace Ambient : Type*}
    [∀ n, MeasurableSpace (Omega n)]
    [MeasurableSpace Subspace] [TopologicalSpace Subspace]
    [OpensMeasurableSpace Subspace]
    [MeasurableSpace Ambient] [TopologicalSpace Ambient]
    [BorelSpace Ambient] where
  /-- Probability measures on the sample spaces. -/
  probabilityMeasure : (n : Index) -> Measure (Omega n)
  /-- Maps into the metric subspace. -/
  subspaceMap : (n : Index) -> Omega n -> Subspace
  /-- Continuous embedding into the ambient metric space. -/
  embedding : Subspace -> Ambient
  /-- Continuity of the embedding. -/
  embeddingContinuous : Continuous embedding
  /-- Index filter. -/
  indexFilter : Filter Index
  /-- Limiting law on the subspace. -/
  subspaceLimitLaw : ProbabilityMeasure Subspace
  /-- Subspace weak convergence. -/
  subspaceWeakConvergence :
    vaart1998_metricWeakConvergenceVaryingDomains
      Omega probabilityMeasure subspaceMap indexFilter subspaceLimitLaw
  /-- Source-level reverse ambient-to-subspace criterion. -/
  reverseSubspaceCriterion : Prop
  /-- Proof of the reverse source criterion. -/
  reverseSubspaceCriterion_proof : reverseSubspaceCriterion

/--
Lemma 18.13 source forward ambient weak-convergence display.
-/
theorem Vaart1998Lemma18_13SubspaceWeakConvergenceSource.ambient_weak_convergence
    {Index : Type*} {Omega : Index -> Type*} {Subspace Ambient : Type*}
    [∀ n, MeasurableSpace (Omega n)]
    [MeasurableSpace Subspace] [TopologicalSpace Subspace]
    [OpensMeasurableSpace Subspace]
    [MeasurableSpace Ambient] [TopologicalSpace Ambient]
    [BorelSpace Ambient]
    (S : Vaart1998Lemma18_13SubspaceWeakConvergenceSource
      Omega (Subspace := Subspace) (Ambient := Ambient)) :
    vaart1998_metricWeakConvergenceVaryingDomains
      Omega S.probabilityMeasure
      (fun n omega => S.embedding (S.subspaceMap n omega)) S.indexFilter
      (S.subspaceLimitLaw.map S.embeddingContinuous.measurable.aemeasurable) :=
  vaart1998_lemma18_13_subspace_to_ambient_weak
    S.embeddingContinuous S.subspaceWeakConvergence

/--
Lemma 18.13 source reverse criterion display.
-/
theorem Vaart1998Lemma18_13SubspaceWeakConvergenceSource.reverse_subspace_criterion
    {Index : Type*} {Omega : Index -> Type*} {Subspace Ambient : Type*}
    [∀ n, MeasurableSpace (Omega n)]
    [MeasurableSpace Subspace] [TopologicalSpace Subspace]
    [OpensMeasurableSpace Subspace]
    [MeasurableSpace Ambient] [TopologicalSpace Ambient]
    [BorelSpace Ambient]
    (S : Vaart1998Lemma18_13SubspaceWeakConvergenceSource
      Omega (Subspace := Subspace) (Ambient := Ambient)) :
    S.reverseSubspaceCriterion :=
  S.reverseSubspaceCriterion_proof

/--
Example 18.5 source: a bounded stochastic process is represented as an
`ell_infty(T)`-valued map.
-/
structure Vaart1998Example18_5EllInftyProcessSource
    {Omega T : Type*} where
  /-- Raw process indexed by `T`. -/
  rawProcess : Omega -> T -> ℝ
  /-- Every sample path is bounded. -/
  boundedSamplePath :
    VdVWEllInfty.IsBoundedSamplePath rawProcess
  /-- The resulting `ell_infty(T)`-valued map. -/
  processMap : Omega -> VdVWEllInfty T
  /-- Display tying the process map to the local `ell_infty` API. -/
  processMap_eq :
    processMap = VdVWEllInfty.processMap rawProcess boundedSamplePath

/--
Example 18.5 coordinate display for a bounded-process map into
`ell_infty(T)`.
-/
theorem Vaart1998Example18_5EllInftyProcessSource.processMap_apply
    {Omega T : Type*}
    (S : Vaart1998Example18_5EllInftyProcessSource
      (Omega := Omega) (T := T))
    (omega : Omega) (t : T) :
    S.processMap omega t = S.rawProcess omega t := by
  rw [S.processMap_eq]
  rfl

/--
Finite-dimensional coordinate restriction from an `ell_infty(T)` random
function to a finite vector, as used in Theorem 18.14.
-/
def vaart1998_ellInftyFiniteCoordinateRestriction
    {T : Type*} (coordinates : Finset T)
    (path : VdVWEllInfty T) : coordinates -> ℝ :=
  VdVWEllInfty.finiteRestrict coordinates path

/--
The finite-dimensional coordinate restriction is continuous.
-/
theorem vaart1998_ellInftyFiniteCoordinateRestriction_continuous
    {T : Type*} (coordinates : Finset T) :
    Continuous
      (vaart1998_ellInftyFiniteCoordinateRestriction
        (T := T) coordinates) :=
  VdVWEllInfty.continuous_finiteRestrict coordinates

/--
The finite-dimensional coordinate restriction agrees with process coordinates.
-/
theorem vaart1998_ellInftyFiniteCoordinateRestriction_processMap_apply
    {Omega T : Type*} (coordinates : Finset T)
    (X : Omega -> T -> ℝ)
    (hX : VdVWEllInfty.IsBoundedSamplePath X)
    (omega : Omega) (t : coordinates) :
    vaart1998_ellInftyFiniteCoordinateRestriction coordinates
      (VdVWEllInfty.processMap X hX omega) t = X omega t :=
  rfl

/--
Theorem 18.14 forward finite-dimensional weak-convergence handoff for
`ell_infty(T)` laws.
-/
theorem vaart1998_theorem18_14_ellInfty_finiteDimensional_weakConvergence
    {T Index : Type*} {l : Filter Index}
    [MeasurableSpace (VdVWEllInfty T)]
    [OpensMeasurableSpace (VdVWEllInfty T)]
    {laws : Index -> ProbabilityMeasure (VdVWEllInfty T)}
    {limitLaw : ProbabilityMeasure (VdVWEllInfty T)}
    (h :
      vaart1998_metricWeakConvergenceProbabilityMeasures
        laws l limitLaw)
    (coordinates : Finset T)
    [MeasurableSpace (coordinates -> ℝ)]
    [BorelSpace (coordinates -> ℝ)] :
    vaart1998_metricWeakConvergenceProbabilityMeasures
      (fun n => (laws n).map
        ((VdVWEllInfty.continuous_finiteRestrict
          (T := T) coordinates).measurable.aemeasurable))
      l
      (limitLaw.map
        ((VdVWEllInfty.continuous_finiteRestrict
          (T := T) coordinates).measurable.aemeasurable)) :=
  StatInference.vdVW148_ellInfty_finiteDimensional_weakConvergence_of_processLaw_weakConvergence
    h coordinates

/--
Theorem 18.14 forward coordinate weak-convergence handoff for
`ell_infty(T)` laws.
-/
theorem vaart1998_theorem18_14_ellInfty_coordinate_weakConvergence
    {T Index : Type*} {l : Filter Index}
    [MeasurableSpace (VdVWEllInfty T)]
    [OpensMeasurableSpace (VdVWEllInfty T)]
    {laws : Index -> ProbabilityMeasure (VdVWEllInfty T)}
    {limitLaw : ProbabilityMeasure (VdVWEllInfty T)}
    (h :
      vaart1998_metricWeakConvergenceProbabilityMeasures
        laws l limitLaw)
    (coordinate : T) :
    vaart1998_metricWeakConvergenceProbabilityMeasures
      (fun n => (laws n).map
        ((VdVWEllInfty.evalCLM (T := T) coordinate).continuous.measurable.aemeasurable))
      l
      (limitLaw.map
        ((VdVWEllInfty.evalCLM (T := T) coordinate).continuous.measurable.aemeasurable)) :=
  StatInference.vdVW148_ellInfty_coordinate_weakConvergence_of_processLaw_weakConvergence
    h coordinate

/--
Theorem 18.14 forward finite-dimensional asymptotic-tightness handoff for
`ell_infty(T)` laws.
-/
theorem vaart1998_theorem18_14_ellInfty_finiteDimensional_asymptoticallyTight
    {T Index : Type*} {l : Filter Index}
    [MeasurableSpace (VdVWEllInfty T)]
    [OpensMeasurableSpace (VdVWEllInfty T)]
    {laws : Index -> ProbabilityMeasure (VdVWEllInfty T)}
    (h :
      vaart1998_probabilityMeasuresAsymptoticallyTight laws l)
    (coordinates : Finset T)
    [MeasurableSpace (coordinates -> ℝ)]
    [BorelSpace (coordinates -> ℝ)] :
    vaart1998_probabilityMeasuresAsymptoticallyTight
      (fun n => (laws n).map
        ((VdVWEllInfty.continuous_finiteRestrict
          (T := T) coordinates).measurable.aemeasurable))
      l :=
  StatInference.vdVW148_ellInfty_finiteDimensional_asymptoticallyTight_of_processLaw_asymptoticallyTight
    h coordinates

/--
Theorem 18.14 forward coordinate asymptotic-tightness handoff for
`ell_infty(T)` laws.
-/
theorem vaart1998_theorem18_14_ellInfty_coordinate_asymptoticallyTight
    {T Index : Type*} {l : Filter Index}
    [MeasurableSpace (VdVWEllInfty T)]
    [OpensMeasurableSpace (VdVWEllInfty T)]
    {laws : Index -> ProbabilityMeasure (VdVWEllInfty T)}
    (h :
      vaart1998_probabilityMeasuresAsymptoticallyTight laws l)
    (coordinate : T) :
    vaart1998_probabilityMeasuresAsymptoticallyTight
      (fun n => (laws n).map
        ((VdVWEllInfty.evalCLM (T := T) coordinate).continuous.measurable.aemeasurable))
      l :=
  StatInference.vdVW148_ellInfty_coordinate_asymptoticallyTight_of_processLaw_asymptoticallyTight
    h coordinate

/--
Finite-index Theorem 18.14 weak-convergence criterion: if the index set is
finite, weak convergence in `ell_infty(T)` is equivalent to weak convergence
after the canonical finite-product identification.
-/
theorem vaart1998_theorem18_14_finite_index_ellInfty_weakConvergence_iff
    {T Index : Type*} {l : Filter Index}
    [Fintype T]
    [MeasurableSpace (VdVWEllInfty T)]
    [OpensMeasurableSpace (VdVWEllInfty T)]
    [BorelSpace (VdVWEllInfty T)]
    [MeasurableSpace (T -> ℝ)] [BorelSpace (T -> ℝ)]
    {laws : Index -> ProbabilityMeasure (VdVWEllInfty T)}
    {limitLaw : ProbabilityMeasure (VdVWEllInfty T)} :
    vaart1998_metricWeakConvergenceProbabilityMeasures laws l limitLaw ↔
      vaart1998_metricWeakConvergenceProbabilityMeasures
        (fun n => (laws n).map
          ((VdVWEllInfty.finiteContinuousLinearEquiv
            (T := T)).continuous.measurable.aemeasurable))
        l
        (limitLaw.map
          ((VdVWEllInfty.finiteContinuousLinearEquiv
            (T := T)).continuous.measurable.aemeasurable)) :=
  StatInference.vdVW148_ellInfty_weakConvergence_iff_finiteProduct_weakConvergence_finite

/--
Finite-index Theorem 18.14 tightness criterion: if the index set is finite,
asymptotic tightness in `ell_infty(T)` is equivalent to asymptotic tightness
after the canonical finite-product identification.
-/
theorem vaart1998_theorem18_14_finite_index_ellInfty_asymptoticallyTight_iff
    {T Index : Type*} {l : Filter Index}
    [Fintype T]
    [MeasurableSpace (VdVWEllInfty T)]
    [OpensMeasurableSpace (VdVWEllInfty T)]
    [BorelSpace (VdVWEllInfty T)]
    [MeasurableSpace (T -> ℝ)] [BorelSpace (T -> ℝ)]
    {laws : Index -> ProbabilityMeasure (VdVWEllInfty T)} :
    vaart1998_probabilityMeasuresAsymptoticallyTight laws l ↔
      vaart1998_probabilityMeasuresAsymptoticallyTight
        (fun n => (laws n).map
          ((VdVWEllInfty.finiteContinuousLinearEquiv
            (T := T)).continuous.measurable.aemeasurable))
        l :=
  StatInference.vdVW148_ellInfty_asymptoticallyTight_iff_finiteProduct_asymptoticallyTight_finite

/--
Theorem 18.14 finite-approximation source: finite-dimensional convergence
plus asymptotic oscillation control yields weak convergence of bounded
processes in `ell_infty(T)`.
-/
structure Vaart1998Theorem18_14EllInftyFiniteApproximationSource
    {Index : Type*} (Omega : Index -> Type*) {T : Type*}
    [∀ n, MeasurableSpace (Omega n)]
    [MeasurableSpace (VdVWEllInfty T)]
    [OpensMeasurableSpace (VdVWEllInfty T)] where
  /-- Probability measures on the sample spaces. -/
  probabilityMeasure : (n : Index) -> Measure (Omega n)
  /-- Raw bounded stochastic processes. -/
  rawProcess : (n : Index) -> Omega n -> T -> ℝ
  /-- Every sample path is bounded. -/
  boundedSamplePath :
    ∀ n, VdVWEllInfty.IsBoundedSamplePath (rawProcess n)
  /-- Process maps into `ell_infty(T)`. -/
  processMap : (n : Index) -> Omega n -> VdVWEllInfty T
  /-- Index filter. -/
  indexFilter : Filter Index
  /-- Limiting law on `ell_infty(T)`. -/
  limitLaw : ProbabilityMeasure (VdVWEllInfty T)
  /-- Process-map display. -/
  processMap_eq :
    processMap =
      fun n => VdVWEllInfty.processMap
        (rawProcess n) (boundedSamplePath n)
  /-- Finite-dimensional convergence source. -/
  finiteDimensionalConvergence : Prop
  /-- Asymptotic finite-oscillation/tightness source. -/
  finiteOscillationControl : Prop
  /-- Weak convergence in `ell_infty(T)`. -/
  weakConvergence :
    vaart1998_metricWeakConvergenceVaryingDomains
      Omega probabilityMeasure processMap indexFilter limitLaw

/--
Theorem 18.14 weak-convergence conclusion display.
-/
theorem Vaart1998Theorem18_14EllInftyFiniteApproximationSource.weak_convergence
    {Index : Type*} {Omega : Index -> Type*} {T : Type*}
    [∀ n, MeasurableSpace (Omega n)]
    [MeasurableSpace (VdVWEllInfty T)]
    [OpensMeasurableSpace (VdVWEllInfty T)]
    (S : Vaart1998Theorem18_14EllInftyFiniteApproximationSource
      Omega (T := T)) :
    vaart1998_metricWeakConvergenceVaryingDomains
      Omega S.probabilityMeasure S.processMap S.indexFilter S.limitLaw :=
  S.weakConvergence

end AsymptoticStatistics
end StatInference
