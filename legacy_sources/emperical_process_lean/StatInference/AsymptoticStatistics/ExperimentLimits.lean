import Mathlib.Probability.Kernel.Composition.MeasureComp
import StatInference.AsymptoticStatistics.LAN

/-!
# van der Vaart 1998 Chapter 9 experiment-limit interfaces

This module opens the Chapter 9 lane with source-shaped experiment-limit
interfaces over the Chapter 7 normalized LAN frontier.  The first layer keeps
experiment convergence in the weak-statistic form already used throughout the
Vaart lane: for each parameter in a recorded set, a statistic under the
finite-sample experiment converges in distribution to the corresponding
statistic in the limit experiment.
-/

noncomputable section

namespace StatInference
namespace AsymptoticStatistics

open Filter MeasureTheory ProbabilityTheory
open scoped ENNReal ProbabilityTheory Topology

/--
Chapter 9 indexed experiment-limit source.

For finite-sample experiments `P_{θ,n}`, limit experiments `Q_θ`, statistics
`T_n`, and limit statistic `T`, this records the textbook weak experiment
limit display `T_n under P_{θ,n} ⇒ T under Q_θ` for every parameter in a
specified parameter set.
-/
structure Vaart1998ExperimentLimitSource
    {Ω ΩLimit Θ Z : Type*} [MeasurableSpace Ω]
    [MeasurableSpace ΩLimit]
    [TopologicalSpace Z] [MeasurableSpace Z] [OpensMeasurableSpace Z]
    (P : Θ -> ℕ -> Measure Ω) (Q : Θ -> Measure ΩLimit)
    [∀ θ n, IsProbabilityMeasure (P θ n)]
    [∀ θ, IsProbabilityMeasure (Q θ)] where
  /-- The parameter set on which the experiment-limit assertion is recorded. -/
  parameterSet : Set Θ
  /-- The finite-sample statistic that represents the experiment. -/
  statistic : ℕ -> Ω -> Z
  /-- The statistic in the limit experiment. -/
  limitStatistic : ΩLimit -> Z
  /-- Weak convergence of finite-sample experiment observations. -/
  statistic_tendstoInDistribution :
    ∀ θ ∈ parameterSet,
      TendstoInDistribution statistic atTop limitStatistic (P θ) (Q θ)

/--
The weak experiment-limit certificate at a parameter in the recorded set.
-/
theorem Vaart1998ExperimentLimitSource.tendstoInDistribution
    {Ω ΩLimit Θ Z : Type*} [MeasurableSpace Ω]
    [MeasurableSpace ΩLimit]
    [TopologicalSpace Z] [MeasurableSpace Z] [OpensMeasurableSpace Z]
    {P : Θ -> ℕ -> Measure Ω} {Q : Θ -> Measure ΩLimit}
    [∀ θ n, IsProbabilityMeasure (P θ n)]
    [∀ θ, IsProbabilityMeasure (Q θ)]
    (S : Vaart1998ExperimentLimitSource (Z := Z) P Q)
    {θ : Θ} (hθ : θ ∈ S.parameterSet) :
    TendstoInDistribution S.statistic atTop S.limitStatistic (P θ) (Q θ) :=
  S.statistic_tendstoInDistribution θ hθ

/--
Restrict an experiment-limit source to a smaller parameter set.
-/
def Vaart1998ExperimentLimitSource.restrictParameterSet
    {Ω ΩLimit Θ Z : Type*} [MeasurableSpace Ω]
    [MeasurableSpace ΩLimit]
    [TopologicalSpace Z] [MeasurableSpace Z] [OpensMeasurableSpace Z]
    {P : Θ -> ℕ -> Measure Ω} {Q : Θ -> Measure ΩLimit}
    [∀ θ n, IsProbabilityMeasure (P θ n)]
    [∀ θ, IsProbabilityMeasure (Q θ)]
    (S : Vaart1998ExperimentLimitSource (Z := Z) P Q)
    (parameterSet' : Set Θ) (hsubset : parameterSet' ⊆ S.parameterSet) :
    Vaart1998ExperimentLimitSource (Z := Z) P Q :=
  { parameterSet := parameterSet'
    statistic := S.statistic
    limitStatistic := S.limitStatistic
    statistic_tendstoInDistribution := fun θ hθ =>
      S.statistic_tendstoInDistribution θ (hsubset hθ) }

/--
Post-process an experiment-limit source by a continuous statistic map.
-/
def Vaart1998ExperimentLimitSource.continuousMap
    {Ω ΩLimit Θ Z W : Type*} [MeasurableSpace Ω]
    [MeasurableSpace ΩLimit]
    [TopologicalSpace Z] [MeasurableSpace Z] [OpensMeasurableSpace Z]
    [TopologicalSpace W] [MeasurableSpace W] [BorelSpace W]
    [OpensMeasurableSpace W]
    {P : Θ -> ℕ -> Measure Ω} {Q : Θ -> Measure ΩLimit}
    [∀ θ n, IsProbabilityMeasure (P θ n)]
    [∀ θ, IsProbabilityMeasure (Q θ)]
    (S : Vaart1998ExperimentLimitSource (Z := Z) P Q)
    (g : Z -> W) (hg : Continuous g) :
    Vaart1998ExperimentLimitSource (Z := W) P Q :=
  { parameterSet := S.parameterSet
    statistic := fun n => g ∘ S.statistic n
    limitStatistic := g ∘ S.limitStatistic
    statistic_tendstoInDistribution := fun θ hθ =>
      TendstoInDistribution.continuous_comp hg
        (S.statistic_tendstoInDistribution θ hθ) }

/--
The finite-sample laws after applying a Markov randomization kernel.
-/
def vaart1998_randomizedExperimentMeasureSeq
    {Ω Θ W : Type*} [MeasurableSpace Ω] [MeasurableSpace W]
    (P : Θ -> ℕ -> Measure Ω)
    (randomizationKernel : Θ -> ℕ -> Kernel Ω W) :
    Θ -> ℕ -> Measure W :=
  fun θ n => randomizationKernel θ n ∘ₘ P θ n

/--
The limit laws after applying a Markov randomization kernel.
-/
def vaart1998_randomizedLimitExperimentMeasure
    {ΩLimit Θ W : Type*} [MeasurableSpace ΩLimit] [MeasurableSpace W]
    (Q : Θ -> Measure ΩLimit)
    (limitRandomizationKernel : Θ -> Kernel ΩLimit W) :
    Θ -> Measure W :=
  fun θ => limitRandomizationKernel θ ∘ₘ Q θ

/--
A Markov randomization of probability finite-sample laws is again a
probability-measure sequence.
-/
@[reducible]
def vaart1998_randomizedExperimentMeasureSeq_isProbabilityMeasure
    {Ω Θ W : Type*} [MeasurableSpace Ω] [MeasurableSpace W]
    {P : Θ -> ℕ -> Measure Ω}
    {randomizationKernel : Θ -> ℕ -> Kernel Ω W}
    [∀ θ n, IsProbabilityMeasure (P θ n)]
    (hK : ∀ θ n, IsMarkovKernel (randomizationKernel θ n)) :
    ∀ θ n, IsProbabilityMeasure
      (vaart1998_randomizedExperimentMeasureSeq P randomizationKernel θ n) := by
  intro θ n
  letI : IsMarkovKernel (randomizationKernel θ n) := hK θ n
  change IsProbabilityMeasure (randomizationKernel θ n ∘ₘ P θ n)
  infer_instance

/--
A Markov randomization of probability limit laws is again a probability
measure.
-/
@[reducible]
def vaart1998_randomizedLimitExperimentMeasure_isProbabilityMeasure
    {ΩLimit Θ W : Type*} [MeasurableSpace ΩLimit] [MeasurableSpace W]
    {Q : Θ -> Measure ΩLimit}
    {limitRandomizationKernel : Θ -> Kernel ΩLimit W}
    [∀ θ, IsProbabilityMeasure (Q θ)]
    (hK : ∀ θ, IsMarkovKernel (limitRandomizationKernel θ)) :
    ∀ θ, IsProbabilityMeasure
      (vaart1998_randomizedLimitExperimentMeasure Q
        limitRandomizationKernel θ) := by
  intro θ
  letI : IsMarkovKernel (limitRandomizationKernel θ) := hK θ
  change IsProbabilityMeasure (limitRandomizationKernel θ ∘ₘ Q θ)
  infer_instance

/--
Chapter 9 randomization-kernel experiment-limit source.

This is the Markov-kernel analogue of `continuousMap`: callers provide
finite-sample and limit randomization kernels and the weak convergence of the
randomized laws.  The constructor below repackages those randomized laws as a
standard experiment-limit source with identity statistics.
-/
structure Vaart1998ExperimentRandomizationKernelSource
    {Ω ΩLimit Θ W : Type*} [MeasurableSpace Ω]
    [MeasurableSpace ΩLimit]
    [TopologicalSpace W] [MeasurableSpace W] [OpensMeasurableSpace W]
    (P : Θ -> ℕ -> Measure Ω) (Q : Θ -> Measure ΩLimit)
    [∀ θ n, IsProbabilityMeasure (P θ n)]
    [∀ θ, IsProbabilityMeasure (Q θ)] where
  /-- The parameter set on which the randomized experiment-limit assertion is recorded. -/
  parameterSet : Set Θ
  /-- Randomization kernels applied to the finite-sample experiments. -/
  randomizationKernel : Θ -> ℕ -> Kernel Ω W
  /-- Randomization kernels applied to the limit experiments. -/
  limitRandomizationKernel : Θ -> Kernel ΩLimit W
  /-- The finite-sample randomization kernels are Markov kernels. -/
  randomizationKernel_isMarkov :
    ∀ θ n, IsMarkovKernel (randomizationKernel θ n)
  /-- The limit randomization kernels are Markov kernels. -/
  limitRandomizationKernel_isMarkov :
    ∀ θ, IsMarkovKernel (limitRandomizationKernel θ)
  /-- Weak convergence of the randomized experiments. -/
  randomized_tendstoInDistribution :
    ∀ θ ∈ parameterSet,
      letI : ∀ n, IsMarkovKernel (randomizationKernel θ n) :=
        randomizationKernel_isMarkov θ
      letI : IsMarkovKernel (limitRandomizationKernel θ) :=
        limitRandomizationKernel_isMarkov θ
      letI : ∀ n, IsProbabilityMeasure
          (vaart1998_randomizedExperimentMeasureSeq P
            randomizationKernel θ n) :=
        fun n =>
          vaart1998_randomizedExperimentMeasureSeq_isProbabilityMeasure
            (P := P) (randomizationKernel := randomizationKernel)
            randomizationKernel_isMarkov θ n
      letI : IsProbabilityMeasure
          (vaart1998_randomizedLimitExperimentMeasure Q
            limitRandomizationKernel θ) :=
        vaart1998_randomizedLimitExperimentMeasure_isProbabilityMeasure
          (Q := Q) (limitRandomizationKernel := limitRandomizationKernel)
          limitRandomizationKernel_isMarkov θ
      TendstoInDistribution (fun _ : ℕ => id) atTop id
        (vaart1998_randomizedExperimentMeasureSeq P
          randomizationKernel θ)
        (vaart1998_randomizedLimitExperimentMeasure Q
          limitRandomizationKernel θ)

/--
The weak convergence certificate carried by a randomization-kernel source.
-/
theorem Vaart1998ExperimentRandomizationKernelSource.tendstoInDistribution
    {Ω ΩLimit Θ W : Type*} [MeasurableSpace Ω]
    [MeasurableSpace ΩLimit]
    [TopologicalSpace W] [MeasurableSpace W] [OpensMeasurableSpace W]
    {P : Θ -> ℕ -> Measure Ω} {Q : Θ -> Measure ΩLimit}
    [∀ θ n, IsProbabilityMeasure (P θ n)]
    [∀ θ, IsProbabilityMeasure (Q θ)]
    (S : Vaart1998ExperimentRandomizationKernelSource (W := W) P Q)
    {θ : Θ} (hθ : θ ∈ S.parameterSet) :
    letI : ∀ n, IsMarkovKernel (S.randomizationKernel θ n) :=
      S.randomizationKernel_isMarkov θ
    letI : IsMarkovKernel (S.limitRandomizationKernel θ) :=
      S.limitRandomizationKernel_isMarkov θ
    letI : ∀ n, IsProbabilityMeasure
        (vaart1998_randomizedExperimentMeasureSeq P
          S.randomizationKernel θ n) :=
      fun n =>
        vaart1998_randomizedExperimentMeasureSeq_isProbabilityMeasure
          (P := P) (randomizationKernel := S.randomizationKernel)
          S.randomizationKernel_isMarkov θ n
    letI : IsProbabilityMeasure
        (vaart1998_randomizedLimitExperimentMeasure Q
          S.limitRandomizationKernel θ) :=
      vaart1998_randomizedLimitExperimentMeasure_isProbabilityMeasure
        (Q := Q) (limitRandomizationKernel := S.limitRandomizationKernel)
        S.limitRandomizationKernel_isMarkov θ
    TendstoInDistribution (fun _ : ℕ => id) atTop id
      (vaart1998_randomizedExperimentMeasureSeq P
        S.randomizationKernel θ)
      (vaart1998_randomizedLimitExperimentMeasure Q
        S.limitRandomizationKernel θ) := by
  letI : ∀ n, IsMarkovKernel (S.randomizationKernel θ n) :=
    S.randomizationKernel_isMarkov θ
  letI : IsMarkovKernel (S.limitRandomizationKernel θ) :=
    S.limitRandomizationKernel_isMarkov θ
  letI : ∀ n, IsProbabilityMeasure
      (vaart1998_randomizedExperimentMeasureSeq P
        S.randomizationKernel θ n) :=
    fun n =>
      vaart1998_randomizedExperimentMeasureSeq_isProbabilityMeasure
        (P := P) (randomizationKernel := S.randomizationKernel)
        S.randomizationKernel_isMarkov θ n
  letI : IsProbabilityMeasure
      (vaart1998_randomizedLimitExperimentMeasure Q
        S.limitRandomizationKernel θ) :=
    vaart1998_randomizedLimitExperimentMeasure_isProbabilityMeasure
      (Q := Q) (limitRandomizationKernel := S.limitRandomizationKernel)
      S.limitRandomizationKernel_isMarkov θ
  exact S.randomized_tendstoInDistribution θ hθ

/--
A randomization-kernel source is a standard experiment-limit source for the
randomized finite-sample and limit laws.
-/
def Vaart1998ExperimentRandomizationKernelSource.experimentLimitSource
    {Ω ΩLimit Θ W : Type*} [MeasurableSpace Ω]
    [MeasurableSpace ΩLimit]
    [TopologicalSpace W] [MeasurableSpace W] [OpensMeasurableSpace W]
    {P : Θ -> ℕ -> Measure Ω} {Q : Θ -> Measure ΩLimit}
    [∀ θ n, IsProbabilityMeasure (P θ n)]
    [∀ θ, IsProbabilityMeasure (Q θ)]
    (S : Vaart1998ExperimentRandomizationKernelSource (W := W) P Q) :
    letI : ∀ θ n, IsMarkovKernel (S.randomizationKernel θ n) :=
      S.randomizationKernel_isMarkov
    letI : ∀ θ, IsMarkovKernel (S.limitRandomizationKernel θ) :=
      S.limitRandomizationKernel_isMarkov
    letI : ∀ θ n, IsProbabilityMeasure
        (vaart1998_randomizedExperimentMeasureSeq P
          S.randomizationKernel θ n) :=
      vaart1998_randomizedExperimentMeasureSeq_isProbabilityMeasure
        (P := P) (randomizationKernel := S.randomizationKernel)
        S.randomizationKernel_isMarkov
    letI : ∀ θ, IsProbabilityMeasure
        (vaart1998_randomizedLimitExperimentMeasure Q
          S.limitRandomizationKernel θ) :=
      vaart1998_randomizedLimitExperimentMeasure_isProbabilityMeasure
        (Q := Q) (limitRandomizationKernel := S.limitRandomizationKernel)
        S.limitRandomizationKernel_isMarkov
    Vaart1998ExperimentLimitSource
      (Ω := W) (ΩLimit := W) (Θ := Θ) (Z := W)
      (vaart1998_randomizedExperimentMeasureSeq P
        S.randomizationKernel)
      (vaart1998_randomizedLimitExperimentMeasure Q
        S.limitRandomizationKernel) := by
  letI : ∀ θ n, IsMarkovKernel (S.randomizationKernel θ n) :=
    S.randomizationKernel_isMarkov
  letI : ∀ θ, IsMarkovKernel (S.limitRandomizationKernel θ) :=
    S.limitRandomizationKernel_isMarkov
  letI : ∀ θ n, IsProbabilityMeasure
      (vaart1998_randomizedExperimentMeasureSeq P
        S.randomizationKernel θ n) :=
    vaart1998_randomizedExperimentMeasureSeq_isProbabilityMeasure
      (P := P) (randomizationKernel := S.randomizationKernel)
      S.randomizationKernel_isMarkov
  letI : ∀ θ, IsProbabilityMeasure
      (vaart1998_randomizedLimitExperimentMeasure Q
        S.limitRandomizationKernel θ) :=
    vaart1998_randomizedLimitExperimentMeasure_isProbabilityMeasure
      (Q := Q) (limitRandomizationKernel := S.limitRandomizationKernel)
      S.limitRandomizationKernel_isMarkov
  exact
    { parameterSet := S.parameterSet
      statistic := fun _ => id
      limitStatistic := id
      statistic_tendstoInDistribution := fun θ hθ =>
        S.tendstoInDistribution hθ }

/--
The finite parameter image generated by a finite local-parameter grid.
-/
def vaart1998_finiteExperimentParameterSet
    {ι Θ : Type*} (localParameters : Finset ι)
    (localParameterMap : ι -> Θ) : Set Θ :=
  {θ | ∃ h ∈ localParameters, localParameterMap h = θ}

/--
Each finite local parameter maps into the finite experiment-parameter set.
-/
theorem vaart1998_mem_finiteExperimentParameterSet
    {ι Θ : Type*} {localParameters : Finset ι}
    {localParameterMap : ι -> Θ} {h : ι}
    (hh : h ∈ localParameters) :
    localParameterMap h ∈
      vaart1998_finiteExperimentParameterSet localParameters
        localParameterMap :=
  ⟨h, hh, rfl⟩

/--
Chapter 9 finite experiment-family source.

This bundles a generic experiment-limit source with a finite grid of local
parameters embedded into the source's parameter set.  It is the experiment-
limit analogue of the finite-local grids used in the Chapter 8 efficiency
lower-bound layer.
-/
structure Vaart1998FiniteExperimentLimitFamilySource
    {ι Ω ΩLimit Θ Z : Type*} [MeasurableSpace Ω]
    [MeasurableSpace ΩLimit]
    [TopologicalSpace Z] [MeasurableSpace Z] [OpensMeasurableSpace Z]
    (P : Θ -> ℕ -> Measure Ω) (Q : Θ -> Measure ΩLimit)
    [∀ θ n, IsProbabilityMeasure (P θ n)]
    [∀ θ, IsProbabilityMeasure (Q θ)] where
  /-- The ambient indexed experiment-limit source. -/
  experimentLimitSource : Vaart1998ExperimentLimitSource (Z := Z) P Q
  /-- The finite local-parameter grid. -/
  localParameters : Finset ι
  /-- The finite local-parameter grid is nonempty. -/
  localParameters_nonempty : localParameters.Nonempty
  /-- The map embedding finite local parameters into the experiment parameter space. -/
  localParameterMap : ι -> Θ
  /-- Every finite local parameter lands inside the ambient parameter set. -/
  localParameters_subset_parameterSet :
    ∀ h ∈ localParameters,
      localParameterMap h ∈ experimentLimitSource.parameterSet

/--
The finite image of the local-parameter grid carried by a finite
experiment-family source.
-/
def Vaart1998FiniteExperimentLimitFamilySource.finiteParameterSet
    {ι Ω ΩLimit Θ Z : Type*} [MeasurableSpace Ω]
    [MeasurableSpace ΩLimit]
    [TopologicalSpace Z] [MeasurableSpace Z] [OpensMeasurableSpace Z]
    {P : Θ -> ℕ -> Measure Ω} {Q : Θ -> Measure ΩLimit}
    [∀ θ n, IsProbabilityMeasure (P θ n)]
    [∀ θ, IsProbabilityMeasure (Q θ)]
    (S : Vaart1998FiniteExperimentLimitFamilySource
      (ι := ι) (Z := Z) P Q) :
    Set Θ :=
  vaart1998_finiteExperimentParameterSet S.localParameters
    S.localParameterMap

/--
The finite experiment-parameter set is nonempty.
-/
theorem Vaart1998FiniteExperimentLimitFamilySource.finiteParameterSet_nonempty
    {ι Ω ΩLimit Θ Z : Type*} [MeasurableSpace Ω]
    [MeasurableSpace ΩLimit]
    [TopologicalSpace Z] [MeasurableSpace Z] [OpensMeasurableSpace Z]
    {P : Θ -> ℕ -> Measure Ω} {Q : Θ -> Measure ΩLimit}
    [∀ θ n, IsProbabilityMeasure (P θ n)]
    [∀ θ, IsProbabilityMeasure (Q θ)]
    (S : Vaart1998FiniteExperimentLimitFamilySource
      (ι := ι) (Z := Z) P Q) :
    S.finiteParameterSet.Nonempty := by
  rcases S.localParameters_nonempty with ⟨h, hh⟩
  exact ⟨S.localParameterMap h,
    vaart1998_mem_finiteExperimentParameterSet hh⟩

/--
The finite experiment-parameter set lies inside the ambient experiment-limit
parameter set.
-/
theorem Vaart1998FiniteExperimentLimitFamilySource.finiteParameterSet_subset_parameterSet
    {ι Ω ΩLimit Θ Z : Type*} [MeasurableSpace Ω]
    [MeasurableSpace ΩLimit]
    [TopologicalSpace Z] [MeasurableSpace Z] [OpensMeasurableSpace Z]
    {P : Θ -> ℕ -> Measure Ω} {Q : Θ -> Measure ΩLimit}
    [∀ θ n, IsProbabilityMeasure (P θ n)]
    [∀ θ, IsProbabilityMeasure (Q θ)]
    (S : Vaart1998FiniteExperimentLimitFamilySource
      (ι := ι) (Z := Z) P Q) :
    S.finiteParameterSet ⊆ S.experimentLimitSource.parameterSet := by
  intro θ hθ
  rcases hθ with ⟨h, hh, rfl⟩
  exact S.localParameters_subset_parameterSet h hh

/--
The experiment-limit source restricted to the finite experiment-parameter
image.
-/
def Vaart1998FiniteExperimentLimitFamilySource.restrictedExperimentLimitSource
    {ι Ω ΩLimit Θ Z : Type*} [MeasurableSpace Ω]
    [MeasurableSpace ΩLimit]
    [TopologicalSpace Z] [MeasurableSpace Z] [OpensMeasurableSpace Z]
    {P : Θ -> ℕ -> Measure Ω} {Q : Θ -> Measure ΩLimit}
    [∀ θ n, IsProbabilityMeasure (P θ n)]
    [∀ θ, IsProbabilityMeasure (Q θ)]
    (S : Vaart1998FiniteExperimentLimitFamilySource
      (ι := ι) (Z := Z) P Q) :
    Vaart1998ExperimentLimitSource (Z := Z) P Q :=
  S.experimentLimitSource.restrictParameterSet S.finiteParameterSet
    S.finiteParameterSet_subset_parameterSet

/--
The weak experiment-limit certificate at a finite local-parameter grid point.
-/
theorem Vaart1998FiniteExperimentLimitFamilySource.tendstoInDistribution
    {ι Ω ΩLimit Θ Z : Type*} [MeasurableSpace Ω]
    [MeasurableSpace ΩLimit]
    [TopologicalSpace Z] [MeasurableSpace Z] [OpensMeasurableSpace Z]
    {P : Θ -> ℕ -> Measure Ω} {Q : Θ -> Measure ΩLimit}
    [∀ θ n, IsProbabilityMeasure (P θ n)]
    [∀ θ, IsProbabilityMeasure (Q θ)]
    (S : Vaart1998FiniteExperimentLimitFamilySource
      (ι := ι) (Z := Z) P Q)
    {h : ι} (hh : h ∈ S.localParameters) :
    TendstoInDistribution S.experimentLimitSource.statistic atTop
      S.experimentLimitSource.limitStatistic
      (P (S.localParameterMap h)) (Q (S.localParameterMap h)) :=
  S.experimentLimitSource.tendstoInDistribution
    (S.localParameters_subset_parameterSet h hh)

/--
Post-process a finite experiment-family source by a continuous statistic map.
-/
def Vaart1998FiniteExperimentLimitFamilySource.continuousMap
    {ι Ω ΩLimit Θ Z W : Type*} [MeasurableSpace Ω]
    [MeasurableSpace ΩLimit]
    [TopologicalSpace Z] [MeasurableSpace Z] [OpensMeasurableSpace Z]
    [TopologicalSpace W] [MeasurableSpace W] [BorelSpace W]
    [OpensMeasurableSpace W]
    {P : Θ -> ℕ -> Measure Ω} {Q : Θ -> Measure ΩLimit}
    [∀ θ n, IsProbabilityMeasure (P θ n)]
    [∀ θ, IsProbabilityMeasure (Q θ)]
    (S : Vaart1998FiniteExperimentLimitFamilySource
      (ι := ι) (Z := Z) P Q)
    (g : Z -> W) (hg : Continuous g) :
    Vaart1998FiniteExperimentLimitFamilySource
      (ι := ι) (Z := W) P Q :=
  { experimentLimitSource :=
      S.experimentLimitSource.continuousMap g hg
    localParameters := S.localParameters
    localParameters_nonempty := S.localParameters_nonempty
    localParameterMap := S.localParameterMap
    localParameters_subset_parameterSet := by
      intro h hh
      exact S.localParameters_subset_parameterSet h hh }

/--
Finite local-parameter wrapper for a randomization-kernel experiment-limit
source.
-/
structure Vaart1998FiniteExperimentRandomizationKernelSource
    {ι Ω ΩLimit Θ W : Type*} [MeasurableSpace Ω]
    [MeasurableSpace ΩLimit]
    [TopologicalSpace W] [MeasurableSpace W] [OpensMeasurableSpace W]
    (P : Θ -> ℕ -> Measure Ω) (Q : Θ -> Measure ΩLimit)
    [∀ θ n, IsProbabilityMeasure (P θ n)]
    [∀ θ, IsProbabilityMeasure (Q θ)] where
  /-- The ambient randomization-kernel source. -/
  randomizationSource :
    Vaart1998ExperimentRandomizationKernelSource (W := W) P Q
  /-- The finite local-parameter grid. -/
  localParameters : Finset ι
  /-- The finite local-parameter grid is nonempty. -/
  localParameters_nonempty : localParameters.Nonempty
  /-- The map embedding finite local parameters into the experiment parameter space. -/
  localParameterMap : ι -> Θ
  /-- Every finite local parameter lands inside the randomized source parameter set. -/
  localParameters_subset_parameterSet :
    ∀ h ∈ localParameters,
      localParameterMap h ∈ randomizationSource.parameterSet

/--
A finite randomization-kernel source supplies the generic finite
experiment-family source for the randomized laws.
-/
def Vaart1998FiniteExperimentRandomizationKernelSource.finiteExperimentLimitFamilySource
    {ι Ω ΩLimit Θ W : Type*} [MeasurableSpace Ω]
    [MeasurableSpace ΩLimit]
    [TopologicalSpace W] [MeasurableSpace W] [OpensMeasurableSpace W]
    {P : Θ -> ℕ -> Measure Ω} {Q : Θ -> Measure ΩLimit}
    [∀ θ n, IsProbabilityMeasure (P θ n)]
    [∀ θ, IsProbabilityMeasure (Q θ)]
    (S : Vaart1998FiniteExperimentRandomizationKernelSource
      (ι := ι) (W := W) P Q) :
    letI : ∀ θ n,
        IsMarkovKernel (S.randomizationSource.randomizationKernel θ n) :=
      S.randomizationSource.randomizationKernel_isMarkov
    letI : ∀ θ,
        IsMarkovKernel (S.randomizationSource.limitRandomizationKernel θ) :=
      S.randomizationSource.limitRandomizationKernel_isMarkov
    letI : ∀ θ n, IsProbabilityMeasure
        (vaart1998_randomizedExperimentMeasureSeq P
          S.randomizationSource.randomizationKernel θ n) :=
      vaart1998_randomizedExperimentMeasureSeq_isProbabilityMeasure
        (P := P)
        (randomizationKernel := S.randomizationSource.randomizationKernel)
        S.randomizationSource.randomizationKernel_isMarkov
    letI : ∀ θ, IsProbabilityMeasure
        (vaart1998_randomizedLimitExperimentMeasure Q
          S.randomizationSource.limitRandomizationKernel θ) :=
      vaart1998_randomizedLimitExperimentMeasure_isProbabilityMeasure
        (Q := Q)
        (limitRandomizationKernel :=
          S.randomizationSource.limitRandomizationKernel)
        S.randomizationSource.limitRandomizationKernel_isMarkov
    Vaart1998FiniteExperimentLimitFamilySource
      (ι := ι) (Ω := W) (ΩLimit := W) (Θ := Θ) (Z := W)
      (vaart1998_randomizedExperimentMeasureSeq P
        S.randomizationSource.randomizationKernel)
      (vaart1998_randomizedLimitExperimentMeasure Q
        S.randomizationSource.limitRandomizationKernel) := by
  letI : ∀ θ n,
      IsMarkovKernel (S.randomizationSource.randomizationKernel θ n) :=
    S.randomizationSource.randomizationKernel_isMarkov
  letI : ∀ θ,
      IsMarkovKernel (S.randomizationSource.limitRandomizationKernel θ) :=
    S.randomizationSource.limitRandomizationKernel_isMarkov
  letI : ∀ θ n, IsProbabilityMeasure
      (vaart1998_randomizedExperimentMeasureSeq P
        S.randomizationSource.randomizationKernel θ n) :=
    vaart1998_randomizedExperimentMeasureSeq_isProbabilityMeasure
      (P := P)
      (randomizationKernel := S.randomizationSource.randomizationKernel)
      S.randomizationSource.randomizationKernel_isMarkov
  letI : ∀ θ, IsProbabilityMeasure
      (vaart1998_randomizedLimitExperimentMeasure Q
        S.randomizationSource.limitRandomizationKernel θ) :=
    vaart1998_randomizedLimitExperimentMeasure_isProbabilityMeasure
      (Q := Q)
      (limitRandomizationKernel :=
        S.randomizationSource.limitRandomizationKernel)
      S.randomizationSource.limitRandomizationKernel_isMarkov
  exact
    { experimentLimitSource :=
        S.randomizationSource.experimentLimitSource
      localParameters := S.localParameters
      localParameters_nonempty := S.localParameters_nonempty
      localParameterMap := S.localParameterMap
      localParameters_subset_parameterSet :=
        S.localParameters_subset_parameterSet }

/--
The randomized weak experiment-limit certificate at a finite local-parameter
grid point.
-/
theorem Vaart1998FiniteExperimentRandomizationKernelSource.tendstoInDistribution
    {ι Ω ΩLimit Θ W : Type*} [MeasurableSpace Ω]
    [MeasurableSpace ΩLimit]
    [TopologicalSpace W] [MeasurableSpace W] [OpensMeasurableSpace W]
    {P : Θ -> ℕ -> Measure Ω} {Q : Θ -> Measure ΩLimit}
    [∀ θ n, IsProbabilityMeasure (P θ n)]
    [∀ θ, IsProbabilityMeasure (Q θ)]
    (S : Vaart1998FiniteExperimentRandomizationKernelSource
      (ι := ι) (W := W) P Q)
    {h : ι} (hh : h ∈ S.localParameters) :
    letI : ∀ n,
        IsMarkovKernel
          (S.randomizationSource.randomizationKernel
            (S.localParameterMap h) n) :=
      S.randomizationSource.randomizationKernel_isMarkov
        (S.localParameterMap h)
    letI : IsMarkovKernel
        (S.randomizationSource.limitRandomizationKernel
          (S.localParameterMap h)) :=
      S.randomizationSource.limitRandomizationKernel_isMarkov
        (S.localParameterMap h)
    letI : ∀ n, IsProbabilityMeasure
        (vaart1998_randomizedExperimentMeasureSeq P
          S.randomizationSource.randomizationKernel
          (S.localParameterMap h) n) :=
      fun n =>
        vaart1998_randomizedExperimentMeasureSeq_isProbabilityMeasure
          (P := P)
          (randomizationKernel := S.randomizationSource.randomizationKernel)
          S.randomizationSource.randomizationKernel_isMarkov
          (S.localParameterMap h) n
    letI : IsProbabilityMeasure
        (vaart1998_randomizedLimitExperimentMeasure Q
          S.randomizationSource.limitRandomizationKernel
          (S.localParameterMap h)) :=
      vaart1998_randomizedLimitExperimentMeasure_isProbabilityMeasure
        (Q := Q)
        (limitRandomizationKernel :=
          S.randomizationSource.limitRandomizationKernel)
        S.randomizationSource.limitRandomizationKernel_isMarkov
        (S.localParameterMap h)
    TendstoInDistribution (fun _ : ℕ => id) atTop id
      (vaart1998_randomizedExperimentMeasureSeq P
        S.randomizationSource.randomizationKernel
        (S.localParameterMap h))
      (vaart1998_randomizedLimitExperimentMeasure Q
        S.randomizationSource.limitRandomizationKernel
        (S.localParameterMap h)) := by
  letI : ∀ n,
      IsMarkovKernel
        (S.randomizationSource.randomizationKernel
          (S.localParameterMap h) n) :=
    S.randomizationSource.randomizationKernel_isMarkov
      (S.localParameterMap h)
  letI : IsMarkovKernel
      (S.randomizationSource.limitRandomizationKernel
        (S.localParameterMap h)) :=
    S.randomizationSource.limitRandomizationKernel_isMarkov
      (S.localParameterMap h)
  letI : ∀ n, IsProbabilityMeasure
      (vaart1998_randomizedExperimentMeasureSeq P
        S.randomizationSource.randomizationKernel
        (S.localParameterMap h) n) :=
    fun n =>
      vaart1998_randomizedExperimentMeasureSeq_isProbabilityMeasure
        (P := P)
        (randomizationKernel := S.randomizationSource.randomizationKernel)
        S.randomizationSource.randomizationKernel_isMarkov
        (S.localParameterMap h) n
  letI : IsProbabilityMeasure
      (vaart1998_randomizedLimitExperimentMeasure Q
        S.randomizationSource.limitRandomizationKernel
        (S.localParameterMap h)) :=
    vaart1998_randomizedLimitExperimentMeasure_isProbabilityMeasure
      (Q := Q)
      (limitRandomizationKernel :=
        S.randomizationSource.limitRandomizationKernel)
      S.randomizationSource.limitRandomizationKernel_isMarkov
      (S.localParameterMap h)
  exact S.randomizationSource.tendstoInDistribution
    (S.localParameters_subset_parameterSet h hh)

/--
Chapter 9 local experiment-limit source over a normalized Chapter 7 LAN
experiment.

This specializes the generic experiment-limit interface to the local
square-root-density experiment carried by
`Vaart1998LANHellingerNormalizedConcreteSqrtDensitySource`.
-/
structure Vaart1998LANLocalExperimentLimitSource
    {Ω ΩScore ΩLimit E Z : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩLimit]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [TopologicalSpace Z] [MeasurableSpace Z] [OpensMeasurableSpace Z]
    (dominatingMeasure : Measure Ω) (baseSqrtDensity : Ω -> ℝ)
    (localSqrtDensity : ℕ -> Ω -> ℝ)
    (ScoreLimitLaw : Measure ΩScore) (LimitExperimentLaw : Measure ΩLimit)
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure LimitExperimentLaw] where
  /-- The normalized concrete LAN source for the local experiment. -/
  lanSource :
    Vaart1998LANHellingerNormalizedConcreteSqrtDensitySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity
      ScoreLimitLaw
  /-- The statistic observed in the local finite-sample experiment. -/
  experimentStatistic : ℕ -> Ω -> Z
  /-- The statistic observed in the limit experiment. -/
  limitStatistic : ΩLimit -> Z
  /-- Weak convergence of the local experiment statistic. -/
  statistic_tendstoInDistribution :
    letI : ∀ n : ℕ, IsProbabilityMeasure
        (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
          localSqrtDensity n) :=
      lanSource.localMeasure_isProbabilityMeasure
    TendstoInDistribution experimentStatistic atTop limitStatistic
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      LimitExperimentLaw

/--
The normalized concrete LAN source carried by a Chapter 9 local
experiment-limit source.
-/
def Vaart1998LANLocalExperimentLimitSource.normalizedLANSource
    {Ω ΩScore ΩLimit E Z : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩLimit]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [TopologicalSpace Z] [MeasurableSpace Z] [OpensMeasurableSpace Z]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {LimitExperimentLaw : Measure ΩLimit}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure LimitExperimentLaw]
    (S : Vaart1998LANLocalExperimentLimitSource
      (E := E) (Z := Z) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw LimitExperimentLaw) :
    Vaart1998LANHellingerNormalizedConcreteSqrtDensitySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity
      ScoreLimitLaw :=
  S.lanSource

/--
The weak convergence certificate carried by a Chapter 9 LAN local
experiment-limit source.
-/
theorem Vaart1998LANLocalExperimentLimitSource.tendstoInDistribution
    {Ω ΩScore ΩLimit E Z : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩLimit]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [TopologicalSpace Z] [MeasurableSpace Z] [OpensMeasurableSpace Z]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {LimitExperimentLaw : Measure ΩLimit}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure LimitExperimentLaw]
    (S : Vaart1998LANLocalExperimentLimitSource
      (E := E) (Z := Z) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw LimitExperimentLaw) :
    letI : ∀ n : ℕ, IsProbabilityMeasure
        (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
          localSqrtDensity n) :=
      S.lanSource.localMeasure_isProbabilityMeasure
    TendstoInDistribution S.experimentStatistic atTop S.limitStatistic
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      LimitExperimentLaw := by
  letI : ∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity n) :=
    S.lanSource.localMeasure_isProbabilityMeasure
  exact S.statistic_tendstoInDistribution

/--
A Chapter 9 LAN local experiment-limit source supplies one-sided contiguity of
the local finite-sample experiment with respect to the baseline laws.
-/
theorem Vaart1998LANLocalExperimentLimitSource.contiguitySource
    {Ω ΩScore ΩLimit E Z : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩLimit]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [TopologicalSpace Z] [MeasurableSpace Z] [OpensMeasurableSpace Z]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {LimitExperimentLaw : Measure ΩLimit}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure LimitExperimentLaw]
    (S : Vaart1998LANLocalExperimentLimitSource
      (E := E) (Z := Z) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw LimitExperimentLaw) :
    Vaart1998ContiguitySource
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity) :=
  S.lanSource.contiguitySource

/--
Post-process a Chapter 9 LAN local experiment-limit source by a continuous
statistic map.
-/
def Vaart1998LANLocalExperimentLimitSource.continuousMap
    {Ω ΩScore ΩLimit E Z W : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩLimit]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [TopologicalSpace Z] [MeasurableSpace Z] [OpensMeasurableSpace Z]
    [TopologicalSpace W] [MeasurableSpace W] [BorelSpace W]
    [OpensMeasurableSpace W]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {LimitExperimentLaw : Measure ΩLimit}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure LimitExperimentLaw]
    (S : Vaart1998LANLocalExperimentLimitSource
      (E := E) (Z := Z) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw LimitExperimentLaw)
    (g : Z -> W) (hg : Continuous g) :
    Vaart1998LANLocalExperimentLimitSource
      (E := E) (Z := W) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw LimitExperimentLaw := by
  letI : ∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity n) :=
    S.lanSource.localMeasure_isProbabilityMeasure
  exact
    { lanSource := S.lanSource
      experimentStatistic := fun n => g ∘ S.experimentStatistic n
      limitStatistic := g ∘ S.limitStatistic
      statistic_tendstoInDistribution :=
        TendstoInDistribution.continuous_comp hg
          S.statistic_tendstoInDistribution }

/--
The indexed finite-sample laws generated by a finite family of normalized LAN
square-root-density experiments.
-/
def vaart1998_lanFiniteExperimentMeasureSeq
    {ι Ω : Type*} [MeasurableSpace Ω]
    (dominatingMeasure : ι -> Measure Ω)
    (localSqrtDensity : ι -> ℕ -> Ω -> ℝ) :
    ι -> ℕ -> Measure Ω :=
  fun h =>
    vaart1998_localSqrtDensityMeasureSeq (dominatingMeasure h)
      (localSqrtDensity h)

/--
The indexed baseline laws paired with a finite family of normalized LAN
square-root-density experiments.
-/
def vaart1998_lanFiniteExperimentBaseMeasureSeq
    {ι Ω : Type*} [MeasurableSpace Ω]
    (dominatingMeasure : ι -> Measure Ω)
    (baseSqrtDensity : ι -> Ω -> ℝ) :
    ι -> ℕ -> Measure Ω :=
  fun h =>
    vaart1998_baseSqrtDensityMeasureSeq (dominatingMeasure h)
      (baseSqrtDensity h)

/--
Chapter 9 finite experiment-limit family generated by indexed normalized LAN
local experiments.

The statistic and limit statistic are common across the finite local grid,
while the finite-sample and limit laws vary with the local index.
-/
structure Vaart1998LANFiniteExperimentLimitFamilySource
    {ι Ω ΩScore ΩLimit E Z : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩLimit]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [TopologicalSpace Z] [MeasurableSpace Z] [OpensMeasurableSpace Z]
    (dominatingMeasure : ι -> Measure Ω)
    (baseSqrtDensity : ι -> Ω -> ℝ)
    (localSqrtDensity : ι -> ℕ -> Ω -> ℝ)
    (ScoreLimitLaw : ι -> Measure ΩScore)
    (LimitExperimentLaw : ι -> Measure ΩLimit)
    [∀ h, IsProbabilityMeasure (ScoreLimitLaw h)]
    [∀ h, IsProbabilityMeasure (LimitExperimentLaw h)] where
  /-- The finite local-parameter grid. -/
  localParameters : Finset ι
  /-- The finite local-parameter grid is nonempty. -/
  localParameters_nonempty : localParameters.Nonempty
  /-- The normalized concrete LAN source at each local parameter. -/
  lanSource : ∀ h : ι,
    Vaart1998LANHellingerNormalizedConcreteSqrtDensitySource
      (E := E) (dominatingMeasure h) (baseSqrtDensity h)
      (localSqrtDensity h) (ScoreLimitLaw h)
  /-- The statistic observed in each finite-sample local experiment. -/
  experimentStatistic : ℕ -> Ω -> Z
  /-- The statistic observed in each limit experiment. -/
  limitStatistic : ΩLimit -> Z
  /-- Weak convergence of the statistic at every local parameter. -/
  statistic_tendstoInDistribution :
    ∀ h : ι,
      letI : ∀ n : ℕ, IsProbabilityMeasure
          (vaart1998_lanFiniteExperimentMeasureSeq
            dominatingMeasure localSqrtDensity h n) :=
        (lanSource h).localMeasure_isProbabilityMeasure
      TendstoInDistribution experimentStatistic atTop limitStatistic
        (vaart1998_lanFiniteExperimentMeasureSeq
          dominatingMeasure localSqrtDensity h)
        (LimitExperimentLaw h)

/--
Extract the Chapter 9 LAN local experiment-limit source at one local
parameter from a finite LAN experiment family.
-/
def Vaart1998LANFiniteExperimentLimitFamilySource.localExperimentLimitSource
    {ι Ω ΩScore ΩLimit E Z : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩLimit]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [TopologicalSpace Z] [MeasurableSpace Z] [OpensMeasurableSpace Z]
    {dominatingMeasure : ι -> Measure Ω}
    {baseSqrtDensity : ι -> Ω -> ℝ}
    {localSqrtDensity : ι -> ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : ι -> Measure ΩScore}
    {LimitExperimentLaw : ι -> Measure ΩLimit}
    [∀ h, IsProbabilityMeasure (ScoreLimitLaw h)]
    [∀ h, IsProbabilityMeasure (LimitExperimentLaw h)]
    (S : Vaart1998LANFiniteExperimentLimitFamilySource
      (E := E) (Z := Z) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw LimitExperimentLaw)
    (h : ι) :
    Vaart1998LANLocalExperimentLimitSource
      (E := E) (Z := Z) (dominatingMeasure h) (baseSqrtDensity h)
      (localSqrtDensity h) (ScoreLimitLaw h) (LimitExperimentLaw h) := by
  letI : ∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_lanFiniteExperimentMeasureSeq
        dominatingMeasure localSqrtDensity h n) :=
    (S.lanSource h).localMeasure_isProbabilityMeasure
  exact
    { lanSource := S.lanSource h
      experimentStatistic := S.experimentStatistic
      limitStatistic := S.limitStatistic
      statistic_tendstoInDistribution :=
        S.statistic_tendstoInDistribution h }

/--
An indexed finite LAN family supplies the generic Chapter 9 indexed
experiment-limit source over all local parameters.
-/
def Vaart1998LANFiniteExperimentLimitFamilySource.experimentLimitSource
    {ι Ω ΩScore ΩLimit E Z : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩLimit]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [TopologicalSpace Z] [MeasurableSpace Z] [OpensMeasurableSpace Z]
    {dominatingMeasure : ι -> Measure Ω}
    {baseSqrtDensity : ι -> Ω -> ℝ}
    {localSqrtDensity : ι -> ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : ι -> Measure ΩScore}
    {LimitExperimentLaw : ι -> Measure ΩLimit}
    [∀ h, IsProbabilityMeasure (ScoreLimitLaw h)]
    [∀ h, IsProbabilityMeasure (LimitExperimentLaw h)]
    (S : Vaart1998LANFiniteExperimentLimitFamilySource
      (E := E) (Z := Z) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw LimitExperimentLaw) :
    letI : ∀ h n, IsProbabilityMeasure
        (vaart1998_lanFiniteExperimentMeasureSeq
          dominatingMeasure localSqrtDensity h n) :=
      fun h => (S.lanSource h).localMeasure_isProbabilityMeasure
    Vaart1998ExperimentLimitSource (Z := Z)
      (vaart1998_lanFiniteExperimentMeasureSeq
        dominatingMeasure localSqrtDensity)
      LimitExperimentLaw := by
  letI : ∀ h n, IsProbabilityMeasure
      (vaart1998_lanFiniteExperimentMeasureSeq
        dominatingMeasure localSqrtDensity h n) :=
    fun h => (S.lanSource h).localMeasure_isProbabilityMeasure
  exact
    { parameterSet := Set.univ
      statistic := S.experimentStatistic
      limitStatistic := S.limitStatistic
      statistic_tendstoInDistribution := fun h _ =>
        S.statistic_tendstoInDistribution h }

/--
An indexed finite LAN family supplies the finite experiment-family source
using the identity embedding of local parameters.
-/
def Vaart1998LANFiniteExperimentLimitFamilySource.finiteExperimentLimitFamilySource
    {ι Ω ΩScore ΩLimit E Z : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩLimit]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [TopologicalSpace Z] [MeasurableSpace Z] [OpensMeasurableSpace Z]
    {dominatingMeasure : ι -> Measure Ω}
    {baseSqrtDensity : ι -> Ω -> ℝ}
    {localSqrtDensity : ι -> ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : ι -> Measure ΩScore}
    {LimitExperimentLaw : ι -> Measure ΩLimit}
    [∀ h, IsProbabilityMeasure (ScoreLimitLaw h)]
    [∀ h, IsProbabilityMeasure (LimitExperimentLaw h)]
    (S : Vaart1998LANFiniteExperimentLimitFamilySource
      (E := E) (Z := Z) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw LimitExperimentLaw) :
    letI : ∀ h n, IsProbabilityMeasure
        (vaart1998_lanFiniteExperimentMeasureSeq
          dominatingMeasure localSqrtDensity h n) :=
      fun h => (S.lanSource h).localMeasure_isProbabilityMeasure
    Vaart1998FiniteExperimentLimitFamilySource
      (ι := ι) (Θ := ι) (Z := Z)
      (vaart1998_lanFiniteExperimentMeasureSeq
        dominatingMeasure localSqrtDensity)
      LimitExperimentLaw := by
  letI : ∀ h n, IsProbabilityMeasure
      (vaart1998_lanFiniteExperimentMeasureSeq
        dominatingMeasure localSqrtDensity h n) :=
    fun h => (S.lanSource h).localMeasure_isProbabilityMeasure
  exact
    { experimentLimitSource := S.experimentLimitSource
      localParameters := S.localParameters
      localParameters_nonempty := S.localParameters_nonempty
      localParameterMap := fun h => h
      localParameters_subset_parameterSet := by
        intro h _hh
        trivial }

/--
The weak experiment-limit certificate at a finite local parameter in an
indexed LAN finite experiment family.
-/
theorem Vaart1998LANFiniteExperimentLimitFamilySource.tendstoInDistribution
    {ι Ω ΩScore ΩLimit E Z : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩLimit]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [TopologicalSpace Z] [MeasurableSpace Z] [OpensMeasurableSpace Z]
    {dominatingMeasure : ι -> Measure Ω}
    {baseSqrtDensity : ι -> Ω -> ℝ}
    {localSqrtDensity : ι -> ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : ι -> Measure ΩScore}
    {LimitExperimentLaw : ι -> Measure ΩLimit}
    [∀ h, IsProbabilityMeasure (ScoreLimitLaw h)]
    [∀ h, IsProbabilityMeasure (LimitExperimentLaw h)]
    (S : Vaart1998LANFiniteExperimentLimitFamilySource
      (E := E) (Z := Z) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw LimitExperimentLaw)
    {h : ι} (_hh : h ∈ S.localParameters) :
    letI : ∀ n : ℕ, IsProbabilityMeasure
        (vaart1998_lanFiniteExperimentMeasureSeq
          dominatingMeasure localSqrtDensity h n) :=
      (S.lanSource h).localMeasure_isProbabilityMeasure
    TendstoInDistribution S.experimentStatistic atTop S.limitStatistic
      (vaart1998_lanFiniteExperimentMeasureSeq
        dominatingMeasure localSqrtDensity h)
      (LimitExperimentLaw h) := by
  letI : ∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_lanFiniteExperimentMeasureSeq
        dominatingMeasure localSqrtDensity h n) :=
    (S.lanSource h).localMeasure_isProbabilityMeasure
  exact S.statistic_tendstoInDistribution h

/--
An indexed LAN finite experiment family supplies one-sided contiguity at each
finite local parameter.
-/
theorem Vaart1998LANFiniteExperimentLimitFamilySource.contiguitySource
    {ι Ω ΩScore ΩLimit E Z : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩLimit]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [TopologicalSpace Z] [MeasurableSpace Z] [OpensMeasurableSpace Z]
    {dominatingMeasure : ι -> Measure Ω}
    {baseSqrtDensity : ι -> Ω -> ℝ}
    {localSqrtDensity : ι -> ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : ι -> Measure ΩScore}
    {LimitExperimentLaw : ι -> Measure ΩLimit}
    [∀ h, IsProbabilityMeasure (ScoreLimitLaw h)]
    [∀ h, IsProbabilityMeasure (LimitExperimentLaw h)]
    (S : Vaart1998LANFiniteExperimentLimitFamilySource
      (E := E) (Z := Z) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw LimitExperimentLaw)
    {h : ι} (_hh : h ∈ S.localParameters) :
    Vaart1998ContiguitySource
      (vaart1998_lanFiniteExperimentMeasureSeq
        dominatingMeasure localSqrtDensity h)
      (vaart1998_lanFiniteExperimentBaseMeasureSeq
        dominatingMeasure baseSqrtDensity h) :=
  (S.lanSource h).contiguitySource

/--
Chapter 9 finite experiment-limit family generated by common Hellinger score
statistics from indexed normalized LAN local experiments.

The equalities record the common-score case needed by the generic
experiment-limit interface, whose statistic is shared across parameters.
-/
structure Vaart1998LANHellingerScoreFiniteExperimentLimitFamilySource
    {ι Ω ΩScore E : Type*} [MeasurableSpace Ω]
    [MeasurableSpace ΩScore]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    (dominatingMeasure : ι -> Measure Ω)
    (baseSqrtDensity : ι -> Ω -> ℝ)
    (localSqrtDensity : ι -> ℕ -> Ω -> ℝ)
    (ScoreLimitLaw : ι -> Measure ΩScore)
    [∀ h, IsProbabilityMeasure (ScoreLimitLaw h)] where
  /-- The finite local-parameter grid. -/
  localParameters : Finset ι
  /-- The finite local-parameter grid is nonempty. -/
  localParameters_nonempty : localParameters.Nonempty
  /-- The normalized concrete LAN source at each local parameter. -/
  lanSource : ∀ h : ι,
    Vaart1998LANHellingerNormalizedConcreteSqrtDensitySource
      (E := E) (dominatingMeasure h) (baseSqrtDensity h)
      (localSqrtDensity h) (ScoreLimitLaw h)
  /-- The common Hellinger score statistic across the finite local grid. -/
  hellingerScoreVector : ℕ -> Ω -> E
  /-- The common Hellinger score limit statistic across the finite local grid. -/
  hellingerScoreLimit : ΩScore -> E
  /-- Each LAN source uses the common Hellinger score statistic. -/
  hellingerScoreVector_eq :
    ∀ h : ι, (lanSource h).hellingerScoreVector = hellingerScoreVector
  /-- Each LAN source uses the common Hellinger score limit statistic. -/
  hellingerScoreLimit_eq :
    ∀ h : ι, (lanSource h).hellingerScoreLimit = hellingerScoreLimit

/--
Extract the Chapter 9 local score experiment-limit source at one local
parameter from a common-score finite LAN family.
-/
def Vaart1998LANHellingerScoreFiniteExperimentLimitFamilySource.localScoreExperimentLimitSource
    {ι Ω ΩScore E : Type*} [MeasurableSpace Ω]
    [MeasurableSpace ΩScore]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {dominatingMeasure : ι -> Measure Ω}
    {baseSqrtDensity : ι -> Ω -> ℝ}
    {localSqrtDensity : ι -> ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : ι -> Measure ΩScore}
    [∀ h, IsProbabilityMeasure (ScoreLimitLaw h)]
    (S : Vaart1998LANHellingerScoreFiniteExperimentLimitFamilySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity
      ScoreLimitLaw)
    (h : ι) :
    Vaart1998LANLocalExperimentLimitSource
      (E := E) (Z := E) (dominatingMeasure h) (baseSqrtDensity h)
      (localSqrtDensity h) (ScoreLimitLaw h) (ScoreLimitLaw h) := by
  letI : ∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_localSqrtDensityMeasureSeq (dominatingMeasure h)
        (localSqrtDensity h) n) :=
    (S.lanSource h).localMeasure_isProbabilityMeasure
  exact
    { lanSource := S.lanSource h
      experimentStatistic := S.hellingerScoreVector
      limitStatistic := S.hellingerScoreLimit
      statistic_tendstoInDistribution := by
        simpa [S.hellingerScoreVector_eq h, S.hellingerScoreLimit_eq h]
          using (S.lanSource h).hellingerScoreVector_tendstoInDistribution }

/--
A common-score finite LAN family supplies the indexed LAN finite experiment
family source with score laws as the limit experiment laws.
-/
def Vaart1998LANHellingerScoreFiniteExperimentLimitFamilySource.lanFiniteExperimentLimitFamilySource
    {ι Ω ΩScore E : Type*} [MeasurableSpace Ω]
    [MeasurableSpace ΩScore]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {dominatingMeasure : ι -> Measure Ω}
    {baseSqrtDensity : ι -> Ω -> ℝ}
    {localSqrtDensity : ι -> ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : ι -> Measure ΩScore}
    [∀ h, IsProbabilityMeasure (ScoreLimitLaw h)]
    (S : Vaart1998LANHellingerScoreFiniteExperimentLimitFamilySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity
      ScoreLimitLaw) :
    Vaart1998LANFiniteExperimentLimitFamilySource
      (E := E) (Z := E) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw ScoreLimitLaw :=
  { localParameters := S.localParameters
    localParameters_nonempty := S.localParameters_nonempty
    lanSource := S.lanSource
    experimentStatistic := S.hellingerScoreVector
    limitStatistic := S.hellingerScoreLimit
    statistic_tendstoInDistribution := by
      intro h
      letI : ∀ n : ℕ, IsProbabilityMeasure
          (vaart1998_lanFiniteExperimentMeasureSeq
            dominatingMeasure localSqrtDensity h n) :=
        (S.lanSource h).localMeasure_isProbabilityMeasure
      simpa [vaart1998_lanFiniteExperimentMeasureSeq,
        S.hellingerScoreVector_eq h, S.hellingerScoreLimit_eq h]
        using (S.lanSource h).hellingerScoreVector_tendstoInDistribution }

/--
A common-score finite LAN family supplies the generic finite experiment-family
source for Hellinger score limits.
-/
def Vaart1998LANHellingerScoreFiniteExperimentLimitFamilySource.finiteExperimentLimitFamilySource
    {ι Ω ΩScore E : Type*} [MeasurableSpace Ω]
    [MeasurableSpace ΩScore]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {dominatingMeasure : ι -> Measure Ω}
    {baseSqrtDensity : ι -> Ω -> ℝ}
    {localSqrtDensity : ι -> ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : ι -> Measure ΩScore}
    [∀ h, IsProbabilityMeasure (ScoreLimitLaw h)]
    (S : Vaart1998LANHellingerScoreFiniteExperimentLimitFamilySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity
      ScoreLimitLaw) :
    letI : ∀ h n, IsProbabilityMeasure
        (vaart1998_lanFiniteExperimentMeasureSeq
          dominatingMeasure localSqrtDensity h n) :=
      fun h => (S.lanSource h).localMeasure_isProbabilityMeasure
    Vaart1998FiniteExperimentLimitFamilySource
      (ι := ι) (Θ := ι) (Z := E)
      (vaart1998_lanFiniteExperimentMeasureSeq
        dominatingMeasure localSqrtDensity)
      ScoreLimitLaw := by
  letI : ∀ h n, IsProbabilityMeasure
      (vaart1998_lanFiniteExperimentMeasureSeq
        dominatingMeasure localSqrtDensity h n) :=
    fun h => (S.lanSource h).localMeasure_isProbabilityMeasure
  exact S.lanFiniteExperimentLimitFamilySource.finiteExperimentLimitFamilySource

/--
The weak Hellinger-score experiment-limit certificate at a finite local
parameter in a common-score finite LAN family.
-/
theorem Vaart1998LANHellingerScoreFiniteExperimentLimitFamilySource.tendstoInDistribution
    {ι Ω ΩScore E : Type*} [MeasurableSpace Ω]
    [MeasurableSpace ΩScore]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {dominatingMeasure : ι -> Measure Ω}
    {baseSqrtDensity : ι -> Ω -> ℝ}
    {localSqrtDensity : ι -> ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : ι -> Measure ΩScore}
    [∀ h, IsProbabilityMeasure (ScoreLimitLaw h)]
    (S : Vaart1998LANHellingerScoreFiniteExperimentLimitFamilySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity
      ScoreLimitLaw)
    {h : ι} (_hh : h ∈ S.localParameters) :
    letI : ∀ n : ℕ, IsProbabilityMeasure
        (vaart1998_lanFiniteExperimentMeasureSeq
          dominatingMeasure localSqrtDensity h n) :=
      (S.lanSource h).localMeasure_isProbabilityMeasure
    TendstoInDistribution S.hellingerScoreVector atTop
      S.hellingerScoreLimit
      (vaart1998_lanFiniteExperimentMeasureSeq
        dominatingMeasure localSqrtDensity h)
      (ScoreLimitLaw h) := by
  letI : ∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_lanFiniteExperimentMeasureSeq
        dominatingMeasure localSqrtDensity h n) :=
    (S.lanSource h).localMeasure_isProbabilityMeasure
  simpa [vaart1998_lanFiniteExperimentMeasureSeq,
    S.hellingerScoreVector_eq h, S.hellingerScoreLimit_eq h]
    using (S.lanSource h).hellingerScoreVector_tendstoInDistribution

/--
The common Hellinger score limit is Gaussian under each finite local
score-limit law.
-/
theorem Vaart1998LANHellingerScoreFiniteExperimentLimitFamilySource.hellingerScoreLimit_gaussian
    {ι Ω ΩScore E : Type*} [MeasurableSpace Ω]
    [MeasurableSpace ΩScore]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {dominatingMeasure : ι -> Measure Ω}
    {baseSqrtDensity : ι -> Ω -> ℝ}
    {localSqrtDensity : ι -> ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : ι -> Measure ΩScore}
    [∀ h, IsProbabilityMeasure (ScoreLimitLaw h)]
    (S : Vaart1998LANHellingerScoreFiniteExperimentLimitFamilySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity
      ScoreLimitLaw)
    (h : ι) :
    HasGaussianLaw S.hellingerScoreLimit (ScoreLimitLaw h) := by
  simpa [S.hellingerScoreLimit_eq h]
    using (S.lanSource h).hellingerScoreLimit_gaussian

/--
A common-score finite LAN family supplies one-sided contiguity at each finite
local parameter.
-/
theorem Vaart1998LANHellingerScoreFiniteExperimentLimitFamilySource.contiguitySource
    {ι Ω ΩScore E : Type*} [MeasurableSpace Ω]
    [MeasurableSpace ΩScore]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {dominatingMeasure : ι -> Measure Ω}
    {baseSqrtDensity : ι -> Ω -> ℝ}
    {localSqrtDensity : ι -> ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : ι -> Measure ΩScore}
    [∀ h, IsProbabilityMeasure (ScoreLimitLaw h)]
    (S : Vaart1998LANHellingerScoreFiniteExperimentLimitFamilySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity
      ScoreLimitLaw)
    {h : ι} (_hh : h ∈ S.localParameters) :
    Vaart1998ContiguitySource
      (vaart1998_lanFiniteExperimentMeasureSeq
        dominatingMeasure localSqrtDensity h)
      (vaart1998_lanFiniteExperimentBaseMeasureSeq
        dominatingMeasure baseSqrtDensity h) :=
  (S.lanSource h).contiguitySource

/--
The Hellinger score convergence already present in the normalized LAN source
is a Chapter 9 local experiment-limit source.
-/
def Vaart1998LANHellingerNormalizedConcreteSqrtDensitySource.scoreExperimentLimitSource
    {Ω ΩScore E : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    [IsProbabilityMeasure ScoreLimitLaw]
    (S : Vaart1998LANHellingerNormalizedConcreteSqrtDensitySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity
      ScoreLimitLaw) :
    Vaart1998LANLocalExperimentLimitSource
      (E := E) (Z := E) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw ScoreLimitLaw := by
  letI : ∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity n) :=
    S.localMeasure_isProbabilityMeasure
  exact
    { lanSource := S
      experimentStatistic := S.hellingerScoreVector
      limitStatistic := S.hellingerScoreLimit
      statistic_tendstoInDistribution :=
        S.hellingerScoreVector_tendstoInDistribution }

end AsymptoticStatistics
end StatInference
