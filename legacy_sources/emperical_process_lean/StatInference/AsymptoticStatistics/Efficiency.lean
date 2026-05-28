import StatInference.AsymptoticStatistics.LAN

/-!
# van der Vaart 1998 Chapter 8 efficiency interfaces

This module opens the Chapter 8 lane with source-shaped regular-estimator
interfaces over the compiled Chapter 7 normalized concrete LAN source.

The first layer keeps the analytic efficiency theorem obligations explicit:
callers supply a local asymptotic distribution for the scaled estimator under
the local alternatives, while the LAN certificate supplies contiguity and the
local probability-measure instances.  Later convolution and minimax lower-bound
packets can consume this regular-estimator source without reopening the
square-root-density LAN construction.
-/

noncomputable section

namespace StatInference
namespace AsymptoticStatistics

open Filter MeasureTheory ProbabilityTheory
open scoped ENNReal ProbabilityTheory Topology

/--
Chapter 8 local asymptotic distribution source for a scaled estimator at one
fixed local parameter direction.

The statistic `estimatorError n` is intentionally abstract: in concrete
callers it will usually be the scaled centered estimator
`r_n • (T_n - θ_{n,h})`.  The source records the local direction together with
weak convergence of this statistic under the local laws.
-/
structure Vaart1998RegularEstimatorLocalAsymptoticDistributionSource
    {Ω Ω' Θ : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    (P : ℕ -> Measure Ω) (LimitLaw : Measure Ω')
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw] where
  /-- The fixed local parameter direction attached to this local experiment. -/
  localParameter : Θ
  /-- The scaled centered estimator error under the local alternatives. -/
  estimatorError : ℕ -> Ω -> Θ
  /-- The limiting estimator error in the local limit experiment. -/
  estimatorLimit : Ω' -> Θ
  /-- Local weak convergence of the scaled estimator error. -/
  estimatorError_tendstoInDistribution :
    TendstoInDistribution estimatorError atTop estimatorLimit P LimitLaw

/--
The local asymptotic distribution is invariant under a.e.-equal versions of
the scaled estimator error.
-/
def Vaart1998RegularEstimatorLocalAsymptoticDistributionSource.congrEstimatorError
    {Ω Ω' Θ : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {P : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998RegularEstimatorLocalAsymptoticDistributionSource
      (Θ := Θ) P LimitLaw)
    {estimatorError' : ℕ -> Ω -> Θ}
    (hEq : ∀ n : ℕ, S.estimatorError n =ᵐ[P n] estimatorError' n) :
    Vaart1998RegularEstimatorLocalAsymptoticDistributionSource
      (Θ := Θ) P LimitLaw :=
  { localParameter := S.localParameter
    estimatorError := estimatorError'
    estimatorLimit := S.estimatorLimit
    estimatorError_tendstoInDistribution :=
      TendstoInDistribution.congr hEq Filter.EventuallyEq.rfl
        S.estimatorError_tendstoInDistribution }

/--
A local asymptotic distribution gives stochastic boundedness of the scaled
estimator error under the local laws.
-/
theorem Vaart1998RegularEstimatorLocalAsymptoticDistributionSource.estimatorError_stochasticallyBounded
    {Ω Ω' Θ : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
    [NormedAddCommGroup Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    [SecondCountableTopology Θ] [CompleteSpace Θ]
    {P : ℕ -> Measure Ω} {LimitLaw : Measure Ω'}
    [∀ n : ℕ, IsProbabilityMeasure (P n)] [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998RegularEstimatorLocalAsymptoticDistributionSource
      (Θ := Θ) P LimitLaw) :
    Vaart1998MeasureSeqStochasticBounded P S.estimatorError :=
  vaart1998_measureSeqStochasticBounded_of_tendstoInDistribution
    S.estimatorError_tendstoInDistribution

/--
Chapter 8 regular-estimator source over a normalized concrete LAN experiment.

This is the first efficiency-facing bridge from Chapter 7: the normalized LAN
source supplies the local alternatives and the contiguity handoff, while the
new estimator fields record the regular estimator's local asymptotic law.
-/
structure Vaart1998LANRegularEstimatorSource
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    (dominatingMeasure : Measure Ω) (baseSqrtDensity : Ω -> ℝ)
    (localSqrtDensity : ℕ -> Ω -> ℝ)
    (ScoreLimitLaw : Measure ΩScore) (EstimatorLimitLaw : Measure ΩEstimator)
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw] where
  /-- The normalized concrete Hellinger LAN source for the local experiment. -/
  lanSource :
    Vaart1998LANHellingerNormalizedConcreteSqrtDensitySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity
      ScoreLimitLaw
  /-- The fixed local parameter direction attached to this source. -/
  localParameter : Θ
  /-- The scaled centered estimator error under the local alternatives. -/
  estimatorError : ℕ -> Ω -> Θ
  /-- The limiting estimator error in the estimator limit experiment. -/
  estimatorLimit : ΩEstimator -> Θ
  /-- Local weak convergence of the scaled estimator error. -/
  estimatorError_tendstoInDistribution :
    letI : ∀ n : ℕ, IsProbabilityMeasure
        (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
          localSqrtDensity n) :=
      lanSource.localMeasure_isProbabilityMeasure
    TendstoInDistribution estimatorError atTop estimatorLimit
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      EstimatorLimitLaw

/--
The normalized concrete LAN certificate carried by a Chapter 8 regular
estimator source.
-/
def Vaart1998LANRegularEstimatorSource.normalizedLANSource
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity localSqrtDensity
      ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998LANHellingerNormalizedConcreteSqrtDensitySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity
      ScoreLimitLaw :=
  S.lanSource

/--
A Chapter 8 regular-estimator source exposes the Chapter 8 local asymptotic
distribution source for its scaled estimator.
-/
def Vaart1998LANRegularEstimatorSource.localAsymptoticDistributionSource
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity localSqrtDensity
      ScoreLimitLaw EstimatorLimitLaw) :
    letI : ∀ n : ℕ, IsProbabilityMeasure
        (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
          localSqrtDensity n) :=
      S.lanSource.localMeasure_isProbabilityMeasure
    Vaart1998RegularEstimatorLocalAsymptoticDistributionSource
      (Θ := Θ)
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      EstimatorLimitLaw := by
  letI : ∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity n) :=
    S.lanSource.localMeasure_isProbabilityMeasure
  exact
    { localParameter := S.localParameter
      estimatorError := S.estimatorError
      estimatorLimit := S.estimatorLimit
      estimatorError_tendstoInDistribution :=
        S.estimatorError_tendstoInDistribution }

/--
A Chapter 8 regular-estimator source is invariant under a.e.-equal versions
of the scaled estimator error under the local laws.
-/
def Vaart1998LANRegularEstimatorSource.congrEstimatorError
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity localSqrtDensity
      ScoreLimitLaw EstimatorLimitLaw)
    {estimatorError' : ℕ -> Ω -> Θ}
    (hEq : ∀ n : ℕ,
      S.estimatorError n =ᵐ[
        vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
          localSqrtDensity n]
        estimatorError' n) :
    Vaart1998LANRegularEstimatorSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity localSqrtDensity
      ScoreLimitLaw EstimatorLimitLaw := by
  letI : ∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity n) :=
    S.lanSource.localMeasure_isProbabilityMeasure
  exact
    { lanSource := S.lanSource
      localParameter := S.localParameter
      estimatorError := estimatorError'
      estimatorLimit := S.estimatorLimit
      estimatorError_tendstoInDistribution :=
        TendstoInDistribution.congr hEq Filter.EventuallyEq.rfl
          S.estimatorError_tendstoInDistribution }

/--
A Chapter 8 regular-estimator source supplies the concrete square-root-density
LAN source from Chapter 7.
-/
def Vaart1998LANRegularEstimatorSource.concreteSqrtDensitySource
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity localSqrtDensity
      ScoreLimitLaw EstimatorLimitLaw) :
    letI : ∀ n : ℕ, IsProbabilityMeasure
        (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
          localSqrtDensity n) :=
      S.lanSource.localMeasure_isProbabilityMeasure
    letI : ∀ n : ℕ, IsProbabilityMeasure
        (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
          baseSqrtDensity n) :=
      S.lanSource.baseMeasure_isProbabilityMeasure
    Vaart1998LANHellingerConcreteSqrtDensitySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity
      ScoreLimitLaw := by
  letI : ∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity n) :=
    S.lanSource.localMeasure_isProbabilityMeasure
  letI : ∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity n) :=
    S.lanSource.baseMeasure_isProbabilityMeasure
  exact S.lanSource.concreteSqrtDensitySource

/--
A Chapter 8 regular-estimator source supplies the real-measurable
common-`withDensity` LAN source from Chapter 7.
-/
def Vaart1998LANRegularEstimatorSource.measurableWithDensitySource
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity localSqrtDensity
      ScoreLimitLaw EstimatorLimitLaw) :
    letI : ∀ n : ℕ, IsProbabilityMeasure
        (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
          localSqrtDensity n) :=
      S.lanSource.localMeasure_isProbabilityMeasure
    letI : ∀ n : ℕ, IsProbabilityMeasure
        (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
          baseSqrtDensity n) :=
      S.lanSource.baseMeasure_isProbabilityMeasure
    Vaart1998LANHellingerMeasurableWithDensitySource (E := E)
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity)
      ScoreLimitLaw := by
  letI : ∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity n) :=
    S.lanSource.localMeasure_isProbabilityMeasure
  letI : ∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity n) :=
    S.lanSource.baseMeasure_isProbabilityMeasure
  exact S.lanSource.measurableWithDensitySource

/--
A Chapter 8 regular-estimator source supplies one-sided contiguity of the
local alternatives with respect to the baseline laws.
-/
theorem Vaart1998LANRegularEstimatorSource.contiguitySource
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity localSqrtDensity
      ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998ContiguitySource
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity) :=
  S.lanSource.contiguitySource

/--
The scaled estimator error in a Chapter 8 regular-estimator source is
stochastically bounded under the local laws.
-/
theorem Vaart1998LANRegularEstimatorSource.estimatorError_stochasticallyBounded
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    [SecondCountableTopology Θ] [CompleteSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity localSqrtDensity
      ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998MeasureSeqStochasticBounded
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      S.estimatorError := by
  letI : ∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity n) :=
    S.lanSource.localMeasure_isProbabilityMeasure
  exact
    vaart1998_measureSeqStochasticBounded_of_tendstoInDistribution
      S.estimatorError_tendstoInDistribution

/--
Chapter 8 convolution-theorem display for the local estimator limit.

The full convolution theorem will later add the analytic hypotheses proving
that the second summand is independent noise.  This display is the compiled
source shape consumed by the next efficiency layer: an estimator limit is
represented as an efficient part plus a residual noise part.
-/
def vaart1998_convolutionLimitDisplay
    {Ω' Θ : Type*} [Add Θ]
    (efficientLimit convolutionNoise : Ω' -> Θ) : Ω' -> Θ :=
  fun ω => efficientLimit ω + convolutionNoise ω

/--
Chapter 8 convolution source over a normalized concrete LAN regular-estimator
source.

This source packages the regular-estimator LAN certificate together with the
convolution display of the estimator's local limit.  The display is stated as
an a.e. identity under the estimator limit law, which is the form needed to
replace the limiting random variable in the local asymptotic distribution.
-/
structure Vaart1998LANRegularEstimatorConvolutionSource
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    (dominatingMeasure : Measure Ω) (baseSqrtDensity : Ω -> ℝ)
    (localSqrtDensity : ℕ -> Ω -> ℝ)
    (ScoreLimitLaw : Measure ΩScore) (EstimatorLimitLaw : Measure ΩEstimator)
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw] where
  /-- The underlying regular-estimator source over the normalized LAN experiment. -/
  regularEstimatorSource :
    Vaart1998LANRegularEstimatorSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw
  /-- The efficient component of the local estimator limit. -/
  efficientLimit : ΩEstimator -> Θ
  /-- The residual convolution-noise component of the local estimator limit. -/
  convolutionNoise : ΩEstimator -> Θ
  /-- The estimator limit is the efficient component plus residual noise. -/
  estimatorLimit_convolution_ae :
    regularEstimatorSource.estimatorLimit =ᵐ[EstimatorLimitLaw]
      vaart1998_convolutionLimitDisplay efficientLimit convolutionNoise

/--
The regular-estimator source carried by a Chapter 8 convolution source.
-/
def Vaart1998LANRegularEstimatorConvolutionSource.regularSource
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorConvolutionSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998LANRegularEstimatorSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw :=
  S.regularEstimatorSource

/--
A Chapter 8 convolution source exposes the normalized concrete LAN source.
-/
def Vaart1998LANRegularEstimatorConvolutionSource.normalizedLANSource
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorConvolutionSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998LANHellingerNormalizedConcreteSqrtDensitySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity
      ScoreLimitLaw :=
  S.regularEstimatorSource.normalizedLANSource

/--
A Chapter 8 convolution source exposes the original local asymptotic
distribution source for its estimator.
-/
def Vaart1998LANRegularEstimatorConvolutionSource.localAsymptoticDistributionSource
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorConvolutionSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    letI : ∀ n : ℕ, IsProbabilityMeasure
        (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
          localSqrtDensity n) :=
      S.regularEstimatorSource.lanSource.localMeasure_isProbabilityMeasure
    Vaart1998RegularEstimatorLocalAsymptoticDistributionSource
      (Θ := Θ)
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      EstimatorLimitLaw := by
  letI : ∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity n) :=
    S.regularEstimatorSource.lanSource.localMeasure_isProbabilityMeasure
  exact S.regularEstimatorSource.localAsymptoticDistributionSource

/--
A Chapter 8 convolution source replaces the estimator-limit random variable
by the efficient-plus-noise convolution display.
-/
def Vaart1998LANRegularEstimatorConvolutionSource.convolvedLocalAsymptoticDistributionSource
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorConvolutionSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    letI : ∀ n : ℕ, IsProbabilityMeasure
        (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
          localSqrtDensity n) :=
      S.regularEstimatorSource.lanSource.localMeasure_isProbabilityMeasure
    Vaart1998RegularEstimatorLocalAsymptoticDistributionSource
      (Θ := Θ)
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      EstimatorLimitLaw := by
  letI : ∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity n) :=
    S.regularEstimatorSource.lanSource.localMeasure_isProbabilityMeasure
  exact
    { localParameter := S.regularEstimatorSource.localParameter
      estimatorError := S.regularEstimatorSource.estimatorError
      estimatorLimit :=
        vaart1998_convolutionLimitDisplay S.efficientLimit
          S.convolutionNoise
      estimatorError_tendstoInDistribution :=
        TendstoInDistribution.congr (fun _ => Filter.EventuallyEq.rfl)
          S.estimatorLimit_convolution_ae
          S.regularEstimatorSource.estimatorError_tendstoInDistribution }

/--
A Chapter 8 convolution source supplies the concrete square-root-density LAN
source from Chapter 7.
-/
def Vaart1998LANRegularEstimatorConvolutionSource.concreteSqrtDensitySource
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorConvolutionSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    letI : ∀ n : ℕ, IsProbabilityMeasure
        (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
          localSqrtDensity n) :=
      S.regularEstimatorSource.lanSource.localMeasure_isProbabilityMeasure
    letI : ∀ n : ℕ, IsProbabilityMeasure
        (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
          baseSqrtDensity n) :=
      S.regularEstimatorSource.lanSource.baseMeasure_isProbabilityMeasure
    Vaart1998LANHellingerConcreteSqrtDensitySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity
      ScoreLimitLaw := by
  letI : ∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity n) :=
    S.regularEstimatorSource.lanSource.localMeasure_isProbabilityMeasure
  letI : ∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity n) :=
    S.regularEstimatorSource.lanSource.baseMeasure_isProbabilityMeasure
  exact S.regularEstimatorSource.concreteSqrtDensitySource

/--
A Chapter 8 convolution source supplies one-sided contiguity of the local
alternatives with respect to the baseline laws.
-/
theorem Vaart1998LANRegularEstimatorConvolutionSource.contiguitySource
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorConvolutionSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998ContiguitySource
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity) :=
  S.regularEstimatorSource.contiguitySource

/--
The scaled estimator error in a Chapter 8 convolution source is
stochastically bounded under the local laws.
-/
theorem Vaart1998LANRegularEstimatorConvolutionSource.estimatorError_stochasticallyBounded
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    [SecondCountableTopology Θ] [CompleteSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorConvolutionSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998MeasureSeqStochasticBounded
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      S.regularEstimatorSource.estimatorError :=
  S.regularEstimatorSource.estimatorError_stochasticallyBounded

/--
The convolved local asymptotic distribution source also yields stochastic
boundedness of the scaled estimator error.
-/
theorem Vaart1998LANRegularEstimatorConvolutionSource.convolvedEstimatorError_stochasticallyBounded
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    [SecondCountableTopology Θ] [CompleteSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorConvolutionSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998MeasureSeqStochasticBounded
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      S.regularEstimatorSource.estimatorError := by
  letI : ∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity n) :=
    S.regularEstimatorSource.lanSource.localMeasure_isProbabilityMeasure
  exact
    (S.convolvedLocalAsymptoticDistributionSource)
      |>.estimatorError_stochasticallyBounded

/--
Chapter 8 convolution-theorem source over a normalized concrete LAN
regular-estimator source.

This layer adds the analytic ingredients missing from the pure convolution
display: the efficient component is Gaussian, the residual noise is
measurable, and the two components are independent under the estimator limit
law.  Later minimax and efficiency statements can depend on this source
without reopening the LAN and contiguity construction.
-/
structure Vaart1998LANRegularEstimatorConvolutionTheoremSource
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    (dominatingMeasure : Measure Ω) (baseSqrtDensity : Ω -> ℝ)
    (localSqrtDensity : ℕ -> Ω -> ℝ)
    (ScoreLimitLaw : Measure ΩScore) (EstimatorLimitLaw : Measure ΩEstimator)
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw] where
  /-- The convolution-display source from the previous Chapter 8 layer. -/
  convolutionSource :
    Vaart1998LANRegularEstimatorConvolutionSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw
  /-- The efficient component is Gaussian in the estimator limit experiment. -/
  efficientLimit_gaussian :
    HasGaussianLaw convolutionSource.efficientLimit EstimatorLimitLaw
  /-- The residual convolution noise is measurable. -/
  convolutionNoise_aemeasurable :
    AEMeasurable convolutionSource.convolutionNoise EstimatorLimitLaw
  /-- The efficient component and residual noise are independent. -/
  efficientLimit_indep_convolutionNoise :
    _root_.ProbabilityTheory.IndepFun convolutionSource.efficientLimit
      convolutionSource.convolutionNoise EstimatorLimitLaw

/--
The convolution-display source carried by a Chapter 8 convolution-theorem
source.
-/
def Vaart1998LANRegularEstimatorConvolutionTheoremSource.convolutionDisplaySource
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorConvolutionTheoremSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998LANRegularEstimatorConvolutionSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw :=
  S.convolutionSource

/--
A Chapter 8 convolution-theorem source exposes the underlying regular
estimator source.
-/
def Vaart1998LANRegularEstimatorConvolutionTheoremSource.regularSource
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorConvolutionTheoremSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998LANRegularEstimatorSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw :=
  S.convolutionSource.regularSource

/--
A Chapter 8 convolution-theorem source exposes the normalized concrete LAN
source.
-/
def Vaart1998LANRegularEstimatorConvolutionTheoremSource.normalizedLANSource
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorConvolutionTheoremSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998LANHellingerNormalizedConcreteSqrtDensitySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity
      ScoreLimitLaw :=
  S.convolutionSource.normalizedLANSource

/--
The efficient component of a Chapter 8 convolution-theorem source is
almost-everywhere measurable.
-/
theorem Vaart1998LANRegularEstimatorConvolutionTheoremSource.efficientLimit_aemeasurable
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorConvolutionTheoremSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    AEMeasurable S.convolutionSource.efficientLimit EstimatorLimitLaw :=
  S.efficientLimit_gaussian.aemeasurable

/--
The efficient-plus-noise convolution display is almost-everywhere measurable.
-/
theorem Vaart1998LANRegularEstimatorConvolutionTheoremSource.convolutionDisplay_aemeasurable
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    [MeasurableAdd₂ Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorConvolutionTheoremSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    AEMeasurable
      (vaart1998_convolutionLimitDisplay S.convolutionSource.efficientLimit
        S.convolutionSource.convolutionNoise)
      EstimatorLimitLaw := by
  simpa [vaart1998_convolutionLimitDisplay] using
    S.efficientLimit_aemeasurable.add S.convolutionNoise_aemeasurable

/--
A Chapter 8 convolution-theorem source exposes the convolved local
asymptotic distribution source.
-/
def Vaart1998LANRegularEstimatorConvolutionTheoremSource.convolvedLocalAsymptoticDistributionSource
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorConvolutionTheoremSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    letI : ∀ n : ℕ, IsProbabilityMeasure
        (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
          localSqrtDensity n) :=
      S.convolutionSource.regularEstimatorSource.lanSource.localMeasure_isProbabilityMeasure
    Vaart1998RegularEstimatorLocalAsymptoticDistributionSource
      (Θ := Θ)
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      EstimatorLimitLaw := by
  letI : ∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity n) :=
    S.convolutionSource.regularEstimatorSource.lanSource.localMeasure_isProbabilityMeasure
  exact S.convolutionSource.convolvedLocalAsymptoticDistributionSource

/--
A Chapter 8 convolution-theorem source supplies one-sided contiguity of the
local alternatives with respect to the baseline laws.
-/
theorem Vaart1998LANRegularEstimatorConvolutionTheoremSource.contiguitySource
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorConvolutionTheoremSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998ContiguitySource
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity) :=
  S.convolutionSource.contiguitySource

/--
The scaled estimator error in a Chapter 8 convolution-theorem source is
stochastically bounded under the local laws.
-/
theorem Vaart1998LANRegularEstimatorConvolutionTheoremSource.estimatorError_stochasticallyBounded
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    [SecondCountableTopology Θ] [CompleteSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorConvolutionTheoremSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998MeasureSeqStochasticBounded
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      S.convolutionSource.regularEstimatorSource.estimatorError :=
  S.convolutionSource.convolvedEstimatorError_stochasticallyBounded

/--
Chapter 8 asymptotic lower-bound predicate for a real-valued risk sequence.

`Vaart1998AsymptoticRiskLowerBound risk bound` says that the eventual
liminf of `risk_n` is at least `bound`, in the epsilon form used by
minimax lower-bound arguments.
-/
def Vaart1998AsymptoticRiskLowerBound (risk : ℕ -> ℝ) (bound : ℝ) : Prop :=
  ∀ ε : ℝ, 0 < ε -> ∀ᶠ n in atTop, bound - ε ≤ risk n

/--
An eventual pointwise lower bound gives the asymptotic risk lower bound.
-/
theorem vaart1998_asymptoticRiskLowerBound_of_eventually_ge
    {risk : ℕ -> ℝ} {bound : ℝ}
    (h : ∀ᶠ n in atTop, bound ≤ risk n) :
    Vaart1998AsymptoticRiskLowerBound risk bound := by
  intro ε hε
  filter_upwards [h] with n hn
  linarith

/--
Convergence of risks to a limit above the benchmark gives the asymptotic
risk lower bound.
-/
theorem vaart1998_asymptoticRiskLowerBound_of_tendsto_ge
    {risk : ℕ -> ℝ} {limitRisk bound : ℝ}
    (hrisk : Tendsto risk atTop (𝓝 limitRisk))
    (hbound : bound ≤ limitRisk) :
    Vaart1998AsymptoticRiskLowerBound risk bound := by
  intro ε hε
  have hlt : bound - ε < limitRisk := by linarith
  have hnhds : Set.Ioi (bound - ε) ∈ 𝓝 limitRisk := Ioi_mem_nhds hlt
  filter_upwards [hrisk hnhds] with n hn
  exact le_of_lt hn

/--
Asymptotic lower bounds are monotone under eventual domination of risk
displays.
-/
theorem vaart1998_asymptoticRiskLowerBound_of_eventually_le
    {lowerRisk upperRisk : ℕ -> ℝ} {bound : ℝ}
    (hlower : Vaart1998AsymptoticRiskLowerBound lowerRisk bound)
    (hdom : ∀ᶠ n in atTop, lowerRisk n ≤ upperRisk n) :
    Vaart1998AsymptoticRiskLowerBound upperRisk bound := by
  intro ε hε
  filter_upwards [hlower ε hε, hdom] with n hn hle
  exact hn.trans hle

/--
Chapter 8 minimax/risk lower-bound source over a convolution-theorem source.

The source keeps the risk side abstract enough for later loss-specific
packets: `risk n` may be a local risk, a finite-local-parameter supremum, or
another source-shaped minimax risk display.  The compiled obligation is the
epsilon-form asymptotic lower bound against `benchmarkRisk`, while the
convolution theorem source keeps all LAN, contiguity, and local-distribution
handoffs available.
-/
structure Vaart1998LANRegularEstimatorMinimaxRiskLowerBoundSource
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    (dominatingMeasure : Measure Ω) (baseSqrtDensity : Ω -> ℝ)
    (localSqrtDensity : ℕ -> Ω -> ℝ)
    (ScoreLimitLaw : Measure ΩScore) (EstimatorLimitLaw : Measure ΩEstimator)
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw] where
  /-- The Chapter 8 convolution-theorem source. -/
  convolutionTheoremSource :
    Vaart1998LANRegularEstimatorConvolutionTheoremSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw
  /-- The real-valued risk sequence for the estimator procedure. -/
  risk : ℕ -> ℝ
  /-- The benchmark risk appearing in the minimax lower bound. -/
  benchmarkRisk : ℝ
  /-- The asymptotic minimax/risk lower-bound certificate. -/
  risk_lower_bound : Vaart1998AsymptoticRiskLowerBound risk benchmarkRisk

/--
A risk source can be built from convergence of the risk display to a limiting
risk above the benchmark.
-/
def Vaart1998LANRegularEstimatorMinimaxRiskLowerBoundSource.of_tendsto_ge
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorConvolutionTheoremSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw)
    (risk : ℕ -> ℝ) {limitRisk benchmarkRisk : ℝ}
    (hrisk : Tendsto risk atTop (𝓝 limitRisk))
    (hbenchmark : benchmarkRisk ≤ limitRisk) :
    Vaart1998LANRegularEstimatorMinimaxRiskLowerBoundSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw :=
  { convolutionTheoremSource := S
    risk := risk
    benchmarkRisk := benchmarkRisk
    risk_lower_bound :=
      vaart1998_asymptoticRiskLowerBound_of_tendsto_ge hrisk hbenchmark }

/--
The convolution-theorem source carried by a minimax/risk lower-bound source.
-/
def Vaart1998LANRegularEstimatorMinimaxRiskLowerBoundSource.convolutionTheorem
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorMinimaxRiskLowerBoundSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998LANRegularEstimatorConvolutionTheoremSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw :=
  S.convolutionTheoremSource

/--
A minimax/risk source exposes the normalized concrete LAN source.
-/
def Vaart1998LANRegularEstimatorMinimaxRiskLowerBoundSource.normalizedLANSource
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorMinimaxRiskLowerBoundSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998LANHellingerNormalizedConcreteSqrtDensitySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity
      ScoreLimitLaw :=
  S.convolutionTheoremSource.normalizedLANSource

/--
A minimax/risk source exposes the convolved local asymptotic distribution
source.
-/
def Vaart1998LANRegularEstimatorMinimaxRiskLowerBoundSource.convolvedLocalAsymptoticDistributionSource
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorMinimaxRiskLowerBoundSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    letI : ∀ n : ℕ, IsProbabilityMeasure
        (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
          localSqrtDensity n) :=
      S.convolutionTheoremSource.convolutionSource.regularEstimatorSource
        |>.lanSource.localMeasure_isProbabilityMeasure
    Vaart1998RegularEstimatorLocalAsymptoticDistributionSource
      (Θ := Θ)
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      EstimatorLimitLaw := by
  letI : ∀ n : ℕ, IsProbabilityMeasure
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity n) :=
    S.convolutionTheoremSource.convolutionSource.regularEstimatorSource
      |>.lanSource.localMeasure_isProbabilityMeasure
  exact S.convolutionTheoremSource.convolvedLocalAsymptoticDistributionSource

/--
A minimax/risk source supplies one-sided contiguity of the local alternatives
with respect to the baseline laws.
-/
theorem Vaart1998LANRegularEstimatorMinimaxRiskLowerBoundSource.contiguitySource
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorMinimaxRiskLowerBoundSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998ContiguitySource
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity) :=
  S.convolutionTheoremSource.contiguitySource

/--
A minimax/risk source supplies stochastic boundedness of the scaled estimator
error under the local laws.
-/
theorem Vaart1998LANRegularEstimatorMinimaxRiskLowerBoundSource.estimatorError_stochasticallyBounded
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    [SecondCountableTopology Θ] [CompleteSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorMinimaxRiskLowerBoundSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998MeasureSeqStochasticBounded
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      S.convolutionTheoremSource.convolutionSource.regularEstimatorSource.estimatorError :=
  S.convolutionTheoremSource.estimatorError_stochasticallyBounded

/--
The asymptotic minimax/risk lower-bound certificate carried by the source.
-/
theorem Vaart1998LANRegularEstimatorMinimaxRiskLowerBoundSource.asymptoticRiskLowerBound
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorMinimaxRiskLowerBoundSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998AsymptoticRiskLowerBound S.risk S.benchmarkRisk :=
  S.risk_lower_bound

/--
Chapter 8 local loss-risk display for a scaled estimator error.

For a local experiment `P_n`, scaled estimator error `Z_n`, and real-valued
loss `ℓ`, this is the risk display `E_{P_n}[ℓ(Z_n)]` used by the
loss-specific minimax layer.
-/
noncomputable def vaart1998_localEstimatorLossRisk
    {Ω Θ : Type*} [MeasurableSpace Ω]
    (P : ℕ -> Measure Ω) (estimatorError : ℕ -> Ω -> Θ)
    (loss : Θ -> ℝ) : ℕ -> ℝ :=
  fun n => ∫ ω, loss (estimatorError n ω) ∂(P n)

/--
Chapter 8 loss-risk lower-bound source over a convolution-theorem source.

This specializes the abstract minimax/risk source to the usual local
estimator-risk display `E_{P_n}[loss(estimatorError_n)]`, while preserving
the convolution theorem, LAN, contiguity, and stochastic-boundedness handoffs.
-/
structure Vaart1998LANRegularEstimatorLossRiskLowerBoundSource
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    (dominatingMeasure : Measure Ω) (baseSqrtDensity : Ω -> ℝ)
    (localSqrtDensity : ℕ -> Ω -> ℝ)
    (ScoreLimitLaw : Measure ΩScore) (EstimatorLimitLaw : Measure ΩEstimator)
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw] where
  /-- The Chapter 8 convolution-theorem source. -/
  convolutionTheoremSource :
    Vaart1998LANRegularEstimatorConvolutionTheoremSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw
  /-- The real-valued loss evaluated on scaled estimator errors. -/
  loss : Θ -> ℝ
  /-- The benchmark risk appearing in the lower bound. -/
  benchmarkRisk : ℝ
  /-- The local loss-risk display has the Chapter 8 lower bound. -/
  risk_lower_bound :
    Vaart1998AsymptoticRiskLowerBound
      (vaart1998_localEstimatorLossRisk
        (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
          localSqrtDensity)
        convolutionTheoremSource.convolutionSource.regularEstimatorSource.estimatorError
        loss)
      benchmarkRisk

/--
A loss-risk lower-bound source can be built from convergence of the local
loss-risk display to a limiting risk above the benchmark.
-/
def Vaart1998LANRegularEstimatorLossRiskLowerBoundSource.of_tendsto_ge
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorConvolutionTheoremSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw)
    (loss : Θ -> ℝ) {limitRisk benchmarkRisk : ℝ}
    (hrisk : Tendsto
      (vaart1998_localEstimatorLossRisk
        (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
          localSqrtDensity)
        S.convolutionSource.regularEstimatorSource.estimatorError
        loss)
      atTop (𝓝 limitRisk))
    (hbenchmark : benchmarkRisk ≤ limitRisk) :
    Vaart1998LANRegularEstimatorLossRiskLowerBoundSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw :=
  { convolutionTheoremSource := S
    loss := loss
    benchmarkRisk := benchmarkRisk
    risk_lower_bound :=
      vaart1998_asymptoticRiskLowerBound_of_tendsto_ge hrisk hbenchmark }

/--
The abstract minimax/risk lower-bound source induced by a loss-risk
lower-bound source.
-/
def Vaart1998LANRegularEstimatorLossRiskLowerBoundSource.minimaxRiskLowerBoundSource
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorLossRiskLowerBoundSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998LANRegularEstimatorMinimaxRiskLowerBoundSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw :=
  { convolutionTheoremSource := S.convolutionTheoremSource
    risk :=
      vaart1998_localEstimatorLossRisk
        (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
          localSqrtDensity)
        S.convolutionTheoremSource.convolutionSource.regularEstimatorSource.estimatorError
        S.loss
    benchmarkRisk := S.benchmarkRisk
    risk_lower_bound := S.risk_lower_bound }

/--
A loss-risk lower-bound source exposes the normalized concrete LAN source.
-/
def Vaart1998LANRegularEstimatorLossRiskLowerBoundSource.normalizedLANSource
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorLossRiskLowerBoundSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998LANHellingerNormalizedConcreteSqrtDensitySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity
      ScoreLimitLaw :=
  S.minimaxRiskLowerBoundSource.normalizedLANSource

/--
A loss-risk lower-bound source supplies one-sided contiguity of the local
alternatives with respect to the baseline laws.
-/
theorem Vaart1998LANRegularEstimatorLossRiskLowerBoundSource.contiguitySource
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorLossRiskLowerBoundSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998ContiguitySource
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity) :=
  S.minimaxRiskLowerBoundSource.contiguitySource

/--
The asymptotic loss-risk lower-bound certificate carried by the source.
-/
theorem Vaart1998LANRegularEstimatorLossRiskLowerBoundSource.asymptoticLossRiskLowerBound
    {Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorLossRiskLowerBoundSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998AsymptoticRiskLowerBound
      (vaart1998_localEstimatorLossRisk
        (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
          localSqrtDensity)
        S.convolutionTheoremSource.convolutionSource.regularEstimatorSource.estimatorError
        S.loss)
      S.benchmarkRisk :=
  S.risk_lower_bound

/--
Chapter 8 finite-local-parameter supremum risk.

For a finite nonempty local-parameter set `H` and risks `R_h,n`, this is
`max_{h in H} R_h,n`.  It is the finite version of the local minimax
supremum used before passing to larger neighborhoods.
-/
noncomputable def vaart1998_finiteLocalSupRisk {ι : Type*}
    (localParameters : Finset ι) (hne : localParameters.Nonempty)
    (risk : ι -> ℕ -> ℝ) : ℕ -> ℝ := by
  classical
  exact fun n =>
    (localParameters.image (fun h => risk h n)).max' (by
      rcases hne with ⟨h, hh⟩
      exact ⟨risk h n, Finset.mem_image.mpr ⟨h, hh, rfl⟩⟩)

/--
Each member risk is bounded above by the finite local supremum risk.
-/
theorem vaart1998_finiteLocalSupRisk_ge_member {ι : Type*}
    {localParameters : Finset ι} (hne : localParameters.Nonempty)
    {risk : ι -> ℕ -> ℝ} {h : ι} (hh : h ∈ localParameters)
    (n : ℕ) :
    risk h n ≤ vaart1998_finiteLocalSupRisk localParameters hne risk n := by
  classical
  unfold vaart1998_finiteLocalSupRisk
  have hmem : risk h n ∈ localParameters.image (fun k => risk k n) :=
    Finset.mem_image.mpr ⟨h, hh, rfl⟩
  simpa using
    (Finset.le_max'
      (s := localParameters.image (fun k => risk k n))
      (risk h n) hmem)

/--
A lower bound for one local member risk transfers to the finite local
supremum risk.
-/
theorem vaart1998_asymptoticRiskLowerBound_finiteLocalSup_of_member
    {ι : Type*}
    {localParameters : Finset ι} (hne : localParameters.Nonempty)
    {risk : ι -> ℕ -> ℝ} {h : ι} (hh : h ∈ localParameters)
    {bound : ℝ}
    (hlower : Vaart1998AsymptoticRiskLowerBound (risk h) bound) :
    Vaart1998AsymptoticRiskLowerBound
      (vaart1998_finiteLocalSupRisk localParameters hne risk) bound := by
  intro ε hε
  filter_upwards [hlower ε hε] with n hn
  exact hn.trans (vaart1998_finiteLocalSupRisk_ge_member hne hh n)

/--
Finite-local-parameter supremum of the concrete Chapter 8 local loss-risk
displays.
-/
noncomputable def vaart1998_finiteLocalSupLossRisk
    {ι Ω Θ : Type*} [MeasurableSpace Ω]
    (localParameters : Finset ι) (hne : localParameters.Nonempty)
    (P : ι -> ℕ -> Measure Ω)
    (estimatorError : ι -> ℕ -> Ω -> Θ)
    (loss : ι -> Θ -> ℝ) : ℕ -> ℝ :=
  vaart1998_finiteLocalSupRisk localParameters hne
    (fun h =>
      vaart1998_localEstimatorLossRisk (P h) (estimatorError h) (loss h))

/--
A lower bound for one concrete local loss-risk display transfers to the
finite-local-parameter loss-risk supremum.
-/
theorem vaart1998_asymptoticRiskLowerBound_finiteLocalSupLossRisk_of_member
    {ι Ω Θ : Type*} [MeasurableSpace Ω]
    {localParameters : Finset ι} (hne : localParameters.Nonempty)
    {P : ι -> ℕ -> Measure Ω}
    {estimatorError : ι -> ℕ -> Ω -> Θ}
    {loss : ι -> Θ -> ℝ} {h : ι} (hh : h ∈ localParameters)
    {bound : ℝ}
    (hlower : Vaart1998AsymptoticRiskLowerBound
      (vaart1998_localEstimatorLossRisk (P h) (estimatorError h) (loss h))
      bound) :
    Vaart1998AsymptoticRiskLowerBound
      (vaart1998_finiteLocalSupLossRisk localParameters hne P estimatorError loss)
      bound := by
  exact vaart1998_asymptoticRiskLowerBound_finiteLocalSup_of_member
    (localParameters := localParameters) hne hh hlower

/--
Chapter 8 finite-local-parameter supremum source over a selected local
loss-risk lower-bound source.

The selected local point supplies the lower bound, while `localRisk` records
the finite family whose supremum is used for the minimax display.  The field
`selected_risk_eq_loss_risk` connects the selected member of the finite family
to the concrete local loss-risk display certified by `selectedLossRiskSource`.
-/
structure Vaart1998LANRegularEstimatorFiniteLocalSupLossRiskLowerBoundSource
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    (dominatingMeasure : Measure Ω) (baseSqrtDensity : Ω -> ℝ)
    (localSqrtDensity : ℕ -> Ω -> ℝ)
    (ScoreLimitLaw : Measure ΩScore) (EstimatorLimitLaw : Measure ΩEstimator)
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw] where
  /-- The finite local-parameter set used in the supremum. -/
  localParameters : Finset ι
  /-- The finite local-parameter set is nonempty. -/
  localParameters_nonempty : localParameters.Nonempty
  /-- The selected local parameter carrying the proven lower bound. -/
  selectedLocalParameter : ι
  /-- The selected local parameter belongs to the finite set. -/
  selectedLocalParameter_mem : selectedLocalParameter ∈ localParameters
  /-- The selected local loss-risk lower-bound source. -/
  selectedLossRiskSource :
    Vaart1998LANRegularEstimatorLossRiskLowerBoundSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw
  /-- The finite family of local risks whose pointwise supremum is used. -/
  localRisk : ι -> ℕ -> ℝ
  /-- The selected risk is the certified concrete local loss-risk display. -/
  selected_risk_eq_loss_risk :
    localRisk selectedLocalParameter =
      vaart1998_localEstimatorLossRisk
        (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
          localSqrtDensity)
        selectedLossRiskSource.convolutionTheoremSource.convolutionSource.regularEstimatorSource.estimatorError
        selectedLossRiskSource.loss

/--
The finite local supremum risk carried by a finite-local source.
-/
noncomputable def
    Vaart1998LANRegularEstimatorFiniteLocalSupLossRiskLowerBoundSource.finiteLocalSupRisk
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorFiniteLocalSupLossRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) : ℕ -> ℝ :=
  vaart1998_finiteLocalSupRisk S.localParameters
    S.localParameters_nonempty S.localRisk

/--
The selected local loss-risk lower bound carried by a finite-local source.
-/
theorem
    Vaart1998LANRegularEstimatorFiniteLocalSupLossRiskLowerBoundSource.selectedAsymptoticLossRiskLowerBound
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorFiniteLocalSupLossRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998AsymptoticRiskLowerBound
      (S.localRisk S.selectedLocalParameter)
      S.selectedLossRiskSource.benchmarkRisk := by
  simpa [S.selected_risk_eq_loss_risk] using
    S.selectedLossRiskSource.asymptoticLossRiskLowerBound

/--
The asymptotic finite-local-supremum lower bound carried by the source.
-/
theorem
    Vaart1998LANRegularEstimatorFiniteLocalSupLossRiskLowerBoundSource.asymptoticFiniteLocalSupLossRiskLowerBound
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorFiniteLocalSupLossRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998AsymptoticRiskLowerBound
      S.finiteLocalSupRisk S.selectedLossRiskSource.benchmarkRisk := by
  exact vaart1998_asymptoticRiskLowerBound_finiteLocalSup_of_member
    (localParameters := S.localParameters)
    S.localParameters_nonempty S.selectedLocalParameter_mem
    S.selectedAsymptoticLossRiskLowerBound

/--
The abstract minimax/risk lower-bound source induced by a finite-local
supremum loss-risk source.
-/
def
    Vaart1998LANRegularEstimatorFiniteLocalSupLossRiskLowerBoundSource.minimaxRiskLowerBoundSource
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorFiniteLocalSupLossRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998LANRegularEstimatorMinimaxRiskLowerBoundSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw :=
  { convolutionTheoremSource := S.selectedLossRiskSource.convolutionTheoremSource
    risk := S.finiteLocalSupRisk
    benchmarkRisk := S.selectedLossRiskSource.benchmarkRisk
    risk_lower_bound := S.asymptoticFiniteLocalSupLossRiskLowerBound }

/--
A finite-local source exposes the normalized concrete LAN source of its
selected local experiment.
-/
def
    Vaart1998LANRegularEstimatorFiniteLocalSupLossRiskLowerBoundSource.normalizedLANSource
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorFiniteLocalSupLossRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998LANHellingerNormalizedConcreteSqrtDensitySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity
      ScoreLimitLaw :=
  S.minimaxRiskLowerBoundSource.normalizedLANSource

/--
A finite-local source supplies one-sided contiguity of the selected local
alternatives with respect to the baseline laws.
-/
theorem
    Vaart1998LANRegularEstimatorFiniteLocalSupLossRiskLowerBoundSource.contiguitySource
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorFiniteLocalSupLossRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998ContiguitySource
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity) :=
  S.minimaxRiskLowerBoundSource.contiguitySource

/--
Chapter 8 neighborhood minimax-risk source induced by a finite-local
supremum source.

The finite source supplies a lower bound over finitely many local alternatives.
This source records a genuine parameter neighborhood containing those local
alternatives, together with a neighborhood/minimax risk display that
eventually dominates the finite-local supremum.  The resulting lower bound is
then available through the abstract minimax/risk source interface.
-/
structure Vaart1998LANRegularEstimatorNeighborhoodMinimaxRiskLowerBoundSource
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    (dominatingMeasure : Measure Ω) (baseSqrtDensity : Ω -> ℝ)
    (localSqrtDensity : ℕ -> Ω -> ℝ)
    (ScoreLimitLaw : Measure ΩScore) (EstimatorLimitLaw : Measure ΩEstimator)
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw] where
  /-- The finite-local lower-bound source embedded in the neighborhood. -/
  finiteLocalSupSource :
    Vaart1998LANRegularEstimatorFiniteLocalSupLossRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw
  /-- The center of the parameter neighborhood. -/
  neighborhoodCenter : Θ
  /-- The parameter neighborhood for the local minimax display. -/
  parameterNeighborhood : Set Θ
  /-- The parameter set is a neighborhood of `neighborhoodCenter`. -/
  parameterNeighborhood_mem_nhds :
    parameterNeighborhood ∈ 𝓝 neighborhoodCenter
  /-- The map placing finite local alternatives into parameter space. -/
  localParameterMap : ι -> Θ
  /-- The finite local alternatives all lie in the parameter neighborhood. -/
  localParameters_subset_neighborhood :
    ∀ h ∈ finiteLocalSupSource.localParameters,
      localParameterMap h ∈ parameterNeighborhood
  /-- The neighborhood/minimax risk display. -/
  neighborhoodMinimaxRisk : ℕ -> ℝ
  /-- The neighborhood risk eventually dominates the finite-local supremum. -/
  finiteLocalSup_le_neighborhoodMinimaxRisk :
    ∀ᶠ n in atTop,
      finiteLocalSupSource.finiteLocalSupRisk n ≤ neighborhoodMinimaxRisk n

/--
The selected finite-local parameter belongs to the recorded parameter
neighborhood.
-/
theorem
    Vaart1998LANRegularEstimatorNeighborhoodMinimaxRiskLowerBoundSource.selectedLocalParameter_mem_neighborhood
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorNeighborhoodMinimaxRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    S.localParameterMap S.finiteLocalSupSource.selectedLocalParameter ∈
      S.parameterNeighborhood :=
  S.localParameters_subset_neighborhood
    S.finiteLocalSupSource.selectedLocalParameter
    S.finiteLocalSupSource.selectedLocalParameter_mem

/--
The asymptotic neighborhood/minimax risk lower bound carried by the source.
-/
theorem
    Vaart1998LANRegularEstimatorNeighborhoodMinimaxRiskLowerBoundSource.asymptoticNeighborhoodMinimaxRiskLowerBound
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorNeighborhoodMinimaxRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998AsymptoticRiskLowerBound S.neighborhoodMinimaxRisk
      S.finiteLocalSupSource.selectedLossRiskSource.benchmarkRisk :=
  vaart1998_asymptoticRiskLowerBound_of_eventually_le
    S.finiteLocalSupSource.asymptoticFiniteLocalSupLossRiskLowerBound
    S.finiteLocalSup_le_neighborhoodMinimaxRisk

/--
The abstract minimax/risk lower-bound source induced by a neighborhood
minimax-risk source.
-/
def
    Vaart1998LANRegularEstimatorNeighborhoodMinimaxRiskLowerBoundSource.minimaxRiskLowerBoundSource
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorNeighborhoodMinimaxRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998LANRegularEstimatorMinimaxRiskLowerBoundSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw :=
  { convolutionTheoremSource :=
      S.finiteLocalSupSource.selectedLossRiskSource.convolutionTheoremSource
    risk := S.neighborhoodMinimaxRisk
    benchmarkRisk := S.finiteLocalSupSource.selectedLossRiskSource.benchmarkRisk
    risk_lower_bound := S.asymptoticNeighborhoodMinimaxRiskLowerBound }

/--
A neighborhood minimax-risk source exposes the selected normalized concrete
LAN source.
-/
def
    Vaart1998LANRegularEstimatorNeighborhoodMinimaxRiskLowerBoundSource.normalizedLANSource
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorNeighborhoodMinimaxRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998LANHellingerNormalizedConcreteSqrtDensitySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity
      ScoreLimitLaw :=
  S.minimaxRiskLowerBoundSource.normalizedLANSource

/--
A neighborhood minimax-risk source supplies one-sided contiguity of the
selected local alternatives with respect to the baseline laws.
-/
theorem
    Vaart1998LANRegularEstimatorNeighborhoodMinimaxRiskLowerBoundSource.contiguitySource
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorNeighborhoodMinimaxRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998ContiguitySource
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity) :=
  S.minimaxRiskLowerBoundSource.contiguitySource

/--
Chapter 8 local-neighborhood supremum risk display.

For a parameter neighborhood `U` and local risk family `R_θ,n`, this is
`sup_{θ in U} R_θ,n` in the conditionally complete order on `ℝ`.  Callers
supply boundedness when using the usual upper-bound property of this display.
-/
noncomputable def vaart1998_localNeighborhoodSupRisk {Θ : Type*}
    (parameterNeighborhood : Set Θ) (risk : Θ -> ℕ -> ℝ) : ℕ -> ℝ :=
  fun n => sSup ((fun θ => risk θ n) '' parameterNeighborhood)

/--
Every risk indexed by a parameter in the neighborhood is bounded above by the
local-neighborhood supremum risk, provided the displayed risk set is bounded
above.
-/
theorem vaart1998_localNeighborhoodSupRisk_ge_mem {Θ : Type*}
    {parameterNeighborhood : Set Θ} {risk : Θ -> ℕ -> ℝ}
    {θ : Θ} (hθ : θ ∈ parameterNeighborhood) (n : ℕ)
    (hbdd : BddAbove ((fun θ => risk θ n) '' parameterNeighborhood)) :
    risk θ n ≤ vaart1998_localNeighborhoodSupRisk parameterNeighborhood risk n := by
  have hmem : risk θ n ∈ (fun θ => risk θ n) '' parameterNeighborhood :=
    ⟨θ, hθ, rfl⟩
  simpa [vaart1998_localNeighborhoodSupRisk] using le_csSup hbdd hmem

/--
A finite local supremum is bounded by a local-neighborhood supremum when the
finite local risks are pointwise dominated by the neighborhood-indexed risks.
-/
theorem vaart1998_finiteLocalSupRisk_le_localNeighborhoodSupRisk
    {ι Θ : Type*}
    {localParameters : Finset ι} (hne : localParameters.Nonempty)
    {localRisk : ι -> ℕ -> ℝ}
    {parameterNeighborhood : Set Θ}
    {neighborhoodRisk : Θ -> ℕ -> ℝ}
    {localParameterMap : ι -> Θ}
    (hsubset : ∀ h ∈ localParameters,
      localParameterMap h ∈ parameterNeighborhood)
    {n : ℕ}
    (hpoint : ∀ h ∈ localParameters,
      localRisk h n ≤ neighborhoodRisk (localParameterMap h) n)
    (hbdd : BddAbove
      ((fun θ => neighborhoodRisk θ n) '' parameterNeighborhood)) :
    vaart1998_finiteLocalSupRisk localParameters hne localRisk n ≤
      vaart1998_localNeighborhoodSupRisk parameterNeighborhood
        neighborhoodRisk n := by
  classical
  unfold vaart1998_finiteLocalSupRisk
  rw [Finset.max'_le_iff]
  intro y hy
  rcases Finset.mem_image.mp hy with ⟨h, hh, rfl⟩
  exact (hpoint h hh).trans
    (vaart1998_localNeighborhoodSupRisk_ge_mem (hsubset h hh) n hbdd)

/--
The asymptotic finite-local lower bound lifts to a local-neighborhood
supremum risk when the finite risks are eventually dominated by the
neighborhood-indexed risk family.
-/
theorem vaart1998_asymptoticRiskLowerBound_localNeighborhoodSup_of_finiteLocalSup
    {ι Θ : Type*}
    {localParameters : Finset ι} (hne : localParameters.Nonempty)
    {localRisk : ι -> ℕ -> ℝ}
    {parameterNeighborhood : Set Θ}
    {neighborhoodRisk : Θ -> ℕ -> ℝ}
    {localParameterMap : ι -> Θ}
    (hsubset : ∀ h ∈ localParameters,
      localParameterMap h ∈ parameterNeighborhood)
    (hpoint : ∀ᶠ n in atTop, ∀ h ∈ localParameters,
      localRisk h n ≤ neighborhoodRisk (localParameterMap h) n)
    (hbdd : ∀ᶠ n in atTop,
      BddAbove ((fun θ => neighborhoodRisk θ n) ''
        parameterNeighborhood))
    {bound : ℝ}
    (hlower : Vaart1998AsymptoticRiskLowerBound
      (vaart1998_finiteLocalSupRisk localParameters hne localRisk) bound) :
    Vaart1998AsymptoticRiskLowerBound
      (vaart1998_localNeighborhoodSupRisk parameterNeighborhood
        neighborhoodRisk) bound := by
  refine vaart1998_asymptoticRiskLowerBound_of_eventually_le hlower ?_
  filter_upwards [hpoint, hbdd] with n hpoint_n hbdd_n
  exact vaart1998_finiteLocalSupRisk_le_localNeighborhoodSupRisk
    hne hsubset hpoint_n hbdd_n

/--
Chapter 8 local-neighborhood supremum source over a finite-local lower-bound
source.

This specializes the abstract neighborhood minimax-risk source to the
concrete display `sup_{θ in U} R_{θ,n}`.  The source records boundedness of
the displayed neighborhood risk set and eventual pointwise domination of the
finite local risks by their neighborhood-indexed counterparts.
-/
structure Vaart1998LANRegularEstimatorLocalNeighborhoodSupRiskLowerBoundSource
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    (dominatingMeasure : Measure Ω) (baseSqrtDensity : Ω -> ℝ)
    (localSqrtDensity : ℕ -> Ω -> ℝ)
    (ScoreLimitLaw : Measure ΩScore) (EstimatorLimitLaw : Measure ΩEstimator)
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw] where
  /-- The finite-local lower-bound source embedded in the neighborhood. -/
  finiteLocalSupSource :
    Vaart1998LANRegularEstimatorFiniteLocalSupLossRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw
  /-- The center of the parameter neighborhood. -/
  neighborhoodCenter : Θ
  /-- The parameter neighborhood for the local supremum display. -/
  parameterNeighborhood : Set Θ
  /-- The parameter set is a neighborhood of `neighborhoodCenter`. -/
  parameterNeighborhood_mem_nhds :
    parameterNeighborhood ∈ 𝓝 neighborhoodCenter
  /-- The map placing finite local alternatives into parameter space. -/
  localParameterMap : ι -> Θ
  /-- The finite local alternatives all lie in the parameter neighborhood. -/
  localParameters_subset_neighborhood :
    ∀ h ∈ finiteLocalSupSource.localParameters,
      localParameterMap h ∈ parameterNeighborhood
  /-- The neighborhood-indexed risk family. -/
  neighborhoodRisk : Θ -> ℕ -> ℝ
  /-- The local-neighborhood risk display is bounded above eventually. -/
  neighborhoodRisk_bddAbove :
    ∀ᶠ n in atTop,
      BddAbove ((fun θ => neighborhoodRisk θ n) ''
        parameterNeighborhood)
  /-- The finite local risks are eventually dominated by neighborhood risks. -/
  finiteLocalRisk_le_neighborhoodRisk :
    ∀ᶠ n in atTop, ∀ h ∈ finiteLocalSupSource.localParameters,
      finiteLocalSupSource.localRisk h n ≤
        neighborhoodRisk (localParameterMap h) n

/--
The local-neighborhood supremum risk carried by the source.
-/
noncomputable def
    Vaart1998LANRegularEstimatorLocalNeighborhoodSupRiskLowerBoundSource.localNeighborhoodSupRisk
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorLocalNeighborhoodSupRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) : ℕ -> ℝ :=
  vaart1998_localNeighborhoodSupRisk S.parameterNeighborhood
    S.neighborhoodRisk

/--
The finite local supremum risk is eventually dominated by the concrete
local-neighborhood supremum risk.
-/
theorem
    Vaart1998LANRegularEstimatorLocalNeighborhoodSupRiskLowerBoundSource.finiteLocalSup_le_localNeighborhoodSupRisk
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorLocalNeighborhoodSupRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    ∀ᶠ n in atTop,
      S.finiteLocalSupSource.finiteLocalSupRisk n ≤
        S.localNeighborhoodSupRisk n := by
  filter_upwards [S.finiteLocalRisk_le_neighborhoodRisk,
    S.neighborhoodRisk_bddAbove] with n hpoint hbdd
  exact vaart1998_finiteLocalSupRisk_le_localNeighborhoodSupRisk
    S.finiteLocalSupSource.localParameters_nonempty
    S.localParameters_subset_neighborhood hpoint hbdd

/--
The neighborhood minimax-risk lower-bound source induced by a concrete
local-neighborhood supremum source.
-/
def
    Vaart1998LANRegularEstimatorLocalNeighborhoodSupRiskLowerBoundSource.neighborhoodMinimaxRiskLowerBoundSource
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorLocalNeighborhoodSupRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998LANRegularEstimatorNeighborhoodMinimaxRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw :=
  { finiteLocalSupSource := S.finiteLocalSupSource
    neighborhoodCenter := S.neighborhoodCenter
    parameterNeighborhood := S.parameterNeighborhood
    parameterNeighborhood_mem_nhds := S.parameterNeighborhood_mem_nhds
    localParameterMap := S.localParameterMap
    localParameters_subset_neighborhood :=
      S.localParameters_subset_neighborhood
    neighborhoodMinimaxRisk := S.localNeighborhoodSupRisk
    finiteLocalSup_le_neighborhoodMinimaxRisk :=
      S.finiteLocalSup_le_localNeighborhoodSupRisk }

/--
The asymptotic lower bound for the concrete local-neighborhood supremum risk.
-/
theorem
    Vaart1998LANRegularEstimatorLocalNeighborhoodSupRiskLowerBoundSource.asymptoticLocalNeighborhoodSupRiskLowerBound
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorLocalNeighborhoodSupRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998AsymptoticRiskLowerBound S.localNeighborhoodSupRisk
      S.finiteLocalSupSource.selectedLossRiskSource.benchmarkRisk :=
  S.neighborhoodMinimaxRiskLowerBoundSource
    |>.asymptoticNeighborhoodMinimaxRiskLowerBound

/--
The abstract minimax/risk lower-bound source induced by a concrete
local-neighborhood supremum source.
-/
def
    Vaart1998LANRegularEstimatorLocalNeighborhoodSupRiskLowerBoundSource.minimaxRiskLowerBoundSource
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorLocalNeighborhoodSupRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998LANRegularEstimatorMinimaxRiskLowerBoundSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw :=
  S.neighborhoodMinimaxRiskLowerBoundSource.minimaxRiskLowerBoundSource

/--
A concrete local-neighborhood supremum source exposes the selected normalized
concrete LAN source.
-/
def
    Vaart1998LANRegularEstimatorLocalNeighborhoodSupRiskLowerBoundSource.normalizedLANSource
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorLocalNeighborhoodSupRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998LANHellingerNormalizedConcreteSqrtDensitySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity
      ScoreLimitLaw :=
  S.neighborhoodMinimaxRiskLowerBoundSource.normalizedLANSource

/--
A concrete local-neighborhood supremum source supplies one-sided contiguity
of the selected local alternatives with respect to the baseline laws.
-/
theorem
    Vaart1998LANRegularEstimatorLocalNeighborhoodSupRiskLowerBoundSource.contiguitySource
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorLocalNeighborhoodSupRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998ContiguitySource
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity) :=
  S.neighborhoodMinimaxRiskLowerBoundSource.contiguitySource

/--
Chapter 8 concrete local-neighborhood loss-risk supremum display.

For a parameter neighborhood `U`, parameter-indexed local experiments
`P_{θ,n}`, estimator errors, and losses, this is the neighborhood risk
`sup_{θ in U} E_{P_{θ,n}}[loss_θ(error_{θ,n})]`.
-/
noncomputable def vaart1998_localNeighborhoodEstimatorLossRisk
    {Ω Θ : Type*} [MeasurableSpace Ω]
    (parameterNeighborhood : Set Θ)
    (P : Θ -> ℕ -> Measure Ω)
    (estimatorError : Θ -> ℕ -> Ω -> Θ)
    (loss : Θ -> Θ -> ℝ) : ℕ -> ℝ :=
  vaart1998_localNeighborhoodSupRisk parameterNeighborhood
    (fun θ =>
      vaart1998_localEstimatorLossRisk (P θ) (estimatorError θ)
        (loss θ))

/--
Each concrete local loss-risk indexed by a parameter in the neighborhood is
bounded by the local-neighborhood loss-risk supremum, assuming the displayed
loss-risk set is bounded above.
-/
theorem vaart1998_localNeighborhoodEstimatorLossRisk_ge_mem
    {Ω Θ : Type*} [MeasurableSpace Ω]
    {parameterNeighborhood : Set Θ}
    {P : Θ -> ℕ -> Measure Ω}
    {estimatorError : Θ -> ℕ -> Ω -> Θ}
    {loss : Θ -> Θ -> ℝ}
    {θ : Θ} (hθ : θ ∈ parameterNeighborhood) (n : ℕ)
    (hbdd : BddAbove
      ((fun θ =>
        vaart1998_localEstimatorLossRisk (P θ) (estimatorError θ)
          (loss θ) n) '' parameterNeighborhood)) :
    vaart1998_localEstimatorLossRisk (P θ) (estimatorError θ)
        (loss θ) n ≤
      vaart1998_localNeighborhoodEstimatorLossRisk parameterNeighborhood P
        estimatorError loss n :=
  vaart1998_localNeighborhoodSupRisk_ge_mem hθ n hbdd

/--
A finite-local concrete loss-risk supremum is bounded by a concrete
local-neighborhood loss-risk display when each finite local experiment is
dominated by its mapped neighborhood experiment.
-/
theorem
    vaart1998_finiteLocalSupLossRisk_le_localNeighborhoodEstimatorLossRisk
    {ι Ω Θ : Type*} [MeasurableSpace Ω]
    {localParameters : Finset ι} (hne : localParameters.Nonempty)
    {P : ι -> ℕ -> Measure Ω}
    {estimatorError : ι -> ℕ -> Ω -> Θ}
    {loss : ι -> Θ -> ℝ}
    {parameterNeighborhood : Set Θ}
    {neighborhoodMeasure : Θ -> ℕ -> Measure Ω}
    {neighborhoodEstimatorError : Θ -> ℕ -> Ω -> Θ}
    {neighborhoodLoss : Θ -> Θ -> ℝ}
    {localParameterMap : ι -> Θ}
    (hsubset : ∀ h ∈ localParameters,
      localParameterMap h ∈ parameterNeighborhood)
    {n : ℕ}
    (hpoint : ∀ h ∈ localParameters,
      vaart1998_localEstimatorLossRisk (P h) (estimatorError h)
          (loss h) n ≤
        vaart1998_localEstimatorLossRisk
          (neighborhoodMeasure (localParameterMap h))
          (neighborhoodEstimatorError (localParameterMap h))
          (neighborhoodLoss (localParameterMap h)) n)
    (hbdd : BddAbove
      ((fun θ =>
        vaart1998_localEstimatorLossRisk (neighborhoodMeasure θ)
          (neighborhoodEstimatorError θ) (neighborhoodLoss θ) n) ''
        parameterNeighborhood)) :
    vaart1998_finiteLocalSupLossRisk localParameters hne P
        estimatorError loss n ≤
      vaart1998_localNeighborhoodEstimatorLossRisk parameterNeighborhood
        neighborhoodMeasure neighborhoodEstimatorError neighborhoodLoss n := by
  simpa [vaart1998_finiteLocalSupLossRisk,
    vaart1998_localNeighborhoodEstimatorLossRisk] using
    vaart1998_finiteLocalSupRisk_le_localNeighborhoodSupRisk
      (localParameters := localParameters) hne
      (localRisk := fun h =>
        vaart1998_localEstimatorLossRisk (P h) (estimatorError h)
          (loss h))
      (parameterNeighborhood := parameterNeighborhood)
      (neighborhoodRisk := fun θ =>
        vaart1998_localEstimatorLossRisk (neighborhoodMeasure θ)
          (neighborhoodEstimatorError θ) (neighborhoodLoss θ))
      (localParameterMap := localParameterMap)
      hsubset hpoint hbdd

/--
The asymptotic finite-local concrete loss-risk lower bound lifts to a
concrete local-neighborhood loss-risk display under eventual mapped
domination and boundedness of the neighborhood display.
-/
theorem
    vaart1998_asymptoticRiskLowerBound_localNeighborhoodEstimatorLossRisk_of_finiteLocalSupLossRisk
    {ι Ω Θ : Type*} [MeasurableSpace Ω]
    {localParameters : Finset ι} (hne : localParameters.Nonempty)
    {P : ι -> ℕ -> Measure Ω}
    {estimatorError : ι -> ℕ -> Ω -> Θ}
    {loss : ι -> Θ -> ℝ}
    {parameterNeighborhood : Set Θ}
    {neighborhoodMeasure : Θ -> ℕ -> Measure Ω}
    {neighborhoodEstimatorError : Θ -> ℕ -> Ω -> Θ}
    {neighborhoodLoss : Θ -> Θ -> ℝ}
    {localParameterMap : ι -> Θ}
    (hsubset : ∀ h ∈ localParameters,
      localParameterMap h ∈ parameterNeighborhood)
    (hpoint : ∀ᶠ n in atTop, ∀ h ∈ localParameters,
      vaart1998_localEstimatorLossRisk (P h) (estimatorError h)
          (loss h) n ≤
        vaart1998_localEstimatorLossRisk
          (neighborhoodMeasure (localParameterMap h))
          (neighborhoodEstimatorError (localParameterMap h))
          (neighborhoodLoss (localParameterMap h)) n)
    (hbdd : ∀ᶠ n in atTop,
      BddAbove
        ((fun θ =>
          vaart1998_localEstimatorLossRisk (neighborhoodMeasure θ)
            (neighborhoodEstimatorError θ) (neighborhoodLoss θ) n) ''
          parameterNeighborhood))
    {bound : ℝ}
    (hlower : Vaart1998AsymptoticRiskLowerBound
      (vaart1998_finiteLocalSupLossRisk localParameters hne P
        estimatorError loss)
      bound) :
    Vaart1998AsymptoticRiskLowerBound
      (vaart1998_localNeighborhoodEstimatorLossRisk parameterNeighborhood
        neighborhoodMeasure neighborhoodEstimatorError neighborhoodLoss)
      bound := by
  refine vaart1998_asymptoticRiskLowerBound_of_eventually_le hlower ?_
  filter_upwards [hpoint, hbdd] with n hpoint_n hbdd_n
  exact
    vaart1998_finiteLocalSupLossRisk_le_localNeighborhoodEstimatorLossRisk
      (localParameters := localParameters) hne hsubset hpoint_n hbdd_n

/--
Chapter 8 concrete local-neighborhood loss-risk source over a finite-local
lower-bound source.

This specializes the local-neighborhood supremum source to the display
`sup_{θ in U} E_{P_{θ,n}}[loss_θ(error_{θ,n})]`, while preserving the
finite-local, neighborhood-minimax, abstract minimax, LAN, and contiguity
handoffs.
-/
structure Vaart1998LANRegularEstimatorLocalNeighborhoodLossRiskLowerBoundSource
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    (dominatingMeasure : Measure Ω) (baseSqrtDensity : Ω -> ℝ)
    (localSqrtDensity : ℕ -> Ω -> ℝ)
    (ScoreLimitLaw : Measure ΩScore) (EstimatorLimitLaw : Measure ΩEstimator)
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw] where
  /-- The finite-local lower-bound source embedded in the neighborhood. -/
  finiteLocalSupSource :
    Vaart1998LANRegularEstimatorFiniteLocalSupLossRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw
  /-- The center of the parameter neighborhood. -/
  neighborhoodCenter : Θ
  /-- The parameter neighborhood for the concrete local loss-risk display. -/
  parameterNeighborhood : Set Θ
  /-- The parameter set is a neighborhood of `neighborhoodCenter`. -/
  parameterNeighborhood_mem_nhds :
    parameterNeighborhood ∈ 𝓝 neighborhoodCenter
  /-- The map placing finite local alternatives into parameter space. -/
  localParameterMap : ι -> Θ
  /-- The finite local alternatives all lie in the parameter neighborhood. -/
  localParameters_subset_neighborhood :
    ∀ h ∈ finiteLocalSupSource.localParameters,
      localParameterMap h ∈ parameterNeighborhood
  /-- The parameter-indexed neighborhood local experiments. -/
  neighborhoodMeasure : Θ -> ℕ -> Measure Ω
  /-- The parameter-indexed estimator errors. -/
  neighborhoodEstimatorError : Θ -> ℕ -> Ω -> Θ
  /-- The parameter-indexed losses. -/
  neighborhoodLoss : Θ -> Θ -> ℝ
  /-- The displayed neighborhood loss-risk set is bounded above eventually. -/
  neighborhoodLossRisk_bddAbove :
    ∀ᶠ n in atTop,
      BddAbove ((fun θ =>
        vaart1998_localEstimatorLossRisk (neighborhoodMeasure θ)
          (neighborhoodEstimatorError θ) (neighborhoodLoss θ) n) ''
        parameterNeighborhood)
  /--
  The finite local risks are eventually dominated by their mapped
  neighborhood loss risks.
  -/
  finiteLocalRisk_le_neighborhoodLossRisk :
    ∀ᶠ n in atTop, ∀ h ∈ finiteLocalSupSource.localParameters,
      finiteLocalSupSource.localRisk h n ≤
        vaart1998_localEstimatorLossRisk
          (neighborhoodMeasure (localParameterMap h))
          (neighborhoodEstimatorError (localParameterMap h))
          (neighborhoodLoss (localParameterMap h)) n

/--
The concrete local-neighborhood loss-risk display carried by the source.
-/
noncomputable def
    Vaart1998LANRegularEstimatorLocalNeighborhoodLossRiskLowerBoundSource.localNeighborhoodLossRisk
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorLocalNeighborhoodLossRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) : ℕ -> ℝ :=
  vaart1998_localNeighborhoodEstimatorLossRisk S.parameterNeighborhood
    S.neighborhoodMeasure S.neighborhoodEstimatorError S.neighborhoodLoss

/--
The selected finite-local parameter belongs to the concrete loss-risk
neighborhood.
-/
theorem
    Vaart1998LANRegularEstimatorLocalNeighborhoodLossRiskLowerBoundSource.selectedLocalParameter_mem_neighborhood
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorLocalNeighborhoodLossRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    S.localParameterMap S.finiteLocalSupSource.selectedLocalParameter ∈
      S.parameterNeighborhood :=
  S.localParameters_subset_neighborhood
    S.finiteLocalSupSource.selectedLocalParameter
    S.finiteLocalSupSource.selectedLocalParameter_mem

/--
Each mapped finite local alternative's concrete neighborhood loss risk is
eventually bounded by the local-neighborhood loss-risk display.
-/
theorem
    Vaart1998LANRegularEstimatorLocalNeighborhoodLossRiskLowerBoundSource.mappedLocalLossRisk_le_localNeighborhoodLossRisk
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorLocalNeighborhoodLossRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw)
    {h : ι} (hh : h ∈ S.finiteLocalSupSource.localParameters) :
    ∀ᶠ n in atTop,
      vaart1998_localEstimatorLossRisk
          (S.neighborhoodMeasure (S.localParameterMap h))
          (S.neighborhoodEstimatorError (S.localParameterMap h))
          (S.neighborhoodLoss (S.localParameterMap h)) n ≤
        S.localNeighborhoodLossRisk n := by
  filter_upwards [S.neighborhoodLossRisk_bddAbove] with n hbdd
  exact vaart1998_localNeighborhoodEstimatorLossRisk_ge_mem
    (S.localParameters_subset_neighborhood h hh) n hbdd

/--
Each finite local risk in the embedded finite source is eventually bounded by
the concrete local-neighborhood loss-risk display.
-/
theorem
    Vaart1998LANRegularEstimatorLocalNeighborhoodLossRiskLowerBoundSource.finiteLocalRisk_le_localNeighborhoodLossRisk
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorLocalNeighborhoodLossRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw)
    {h : ι} (hh : h ∈ S.finiteLocalSupSource.localParameters) :
    ∀ᶠ n in atTop,
      S.finiteLocalSupSource.localRisk h n ≤
        S.localNeighborhoodLossRisk n := by
  filter_upwards [S.finiteLocalRisk_le_neighborhoodLossRisk,
    S.mappedLocalLossRisk_le_localNeighborhoodLossRisk hh] with n hfinite hsup
  exact (hfinite h hh).trans hsup

/--
The selected finite local risk is eventually bounded by the concrete
local-neighborhood loss-risk display.
-/
theorem
    Vaart1998LANRegularEstimatorLocalNeighborhoodLossRiskLowerBoundSource.selectedLocalRisk_le_localNeighborhoodLossRisk
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorLocalNeighborhoodLossRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    ∀ᶠ n in atTop,
      S.finiteLocalSupSource.localRisk
          S.finiteLocalSupSource.selectedLocalParameter n ≤
        S.localNeighborhoodLossRisk n :=
  S.finiteLocalRisk_le_localNeighborhoodLossRisk
    S.finiteLocalSupSource.selectedLocalParameter_mem

/--
The concrete local-neighborhood supremum source induced by a concrete
local-neighborhood loss-risk source.
-/
def
    Vaart1998LANRegularEstimatorLocalNeighborhoodLossRiskLowerBoundSource.localNeighborhoodSupRiskLowerBoundSource
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorLocalNeighborhoodLossRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998LANRegularEstimatorLocalNeighborhoodSupRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw :=
  { finiteLocalSupSource := S.finiteLocalSupSource
    neighborhoodCenter := S.neighborhoodCenter
    parameterNeighborhood := S.parameterNeighborhood
    parameterNeighborhood_mem_nhds := S.parameterNeighborhood_mem_nhds
    localParameterMap := S.localParameterMap
    localParameters_subset_neighborhood :=
      S.localParameters_subset_neighborhood
    neighborhoodRisk := fun θ =>
      vaart1998_localEstimatorLossRisk (S.neighborhoodMeasure θ)
        (S.neighborhoodEstimatorError θ) (S.neighborhoodLoss θ)
    neighborhoodRisk_bddAbove := S.neighborhoodLossRisk_bddAbove
    finiteLocalRisk_le_neighborhoodRisk :=
      S.finiteLocalRisk_le_neighborhoodLossRisk }

/--
The asymptotic lower bound for the concrete local-neighborhood loss-risk
display.
-/
theorem
    Vaart1998LANRegularEstimatorLocalNeighborhoodLossRiskLowerBoundSource.asymptoticLocalNeighborhoodLossRiskLowerBound
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorLocalNeighborhoodLossRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998AsymptoticRiskLowerBound S.localNeighborhoodLossRisk
      S.finiteLocalSupSource.selectedLossRiskSource.benchmarkRisk := by
  change Vaart1998AsymptoticRiskLowerBound
    S.localNeighborhoodSupRiskLowerBoundSource.localNeighborhoodSupRisk
    S.finiteLocalSupSource.selectedLossRiskSource.benchmarkRisk
  exact
    S.localNeighborhoodSupRiskLowerBoundSource
      |>.asymptoticLocalNeighborhoodSupRiskLowerBound

/--
The neighborhood minimax-risk source induced by a concrete local-neighborhood
loss-risk source.
-/
def
    Vaart1998LANRegularEstimatorLocalNeighborhoodLossRiskLowerBoundSource.neighborhoodMinimaxRiskLowerBoundSource
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorLocalNeighborhoodLossRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998LANRegularEstimatorNeighborhoodMinimaxRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw :=
  S.localNeighborhoodSupRiskLowerBoundSource
    |>.neighborhoodMinimaxRiskLowerBoundSource

/--
The abstract minimax/risk lower-bound source induced by a concrete
local-neighborhood loss-risk source.
-/
def
    Vaart1998LANRegularEstimatorLocalNeighborhoodLossRiskLowerBoundSource.minimaxRiskLowerBoundSource
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorLocalNeighborhoodLossRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998LANRegularEstimatorMinimaxRiskLowerBoundSource
      (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw :=
  S.localNeighborhoodSupRiskLowerBoundSource.minimaxRiskLowerBoundSource

/--
A concrete local-neighborhood loss-risk source exposes the selected
normalized concrete LAN source.
-/
def
    Vaart1998LANRegularEstimatorLocalNeighborhoodLossRiskLowerBoundSource.normalizedLANSource
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorLocalNeighborhoodLossRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998LANHellingerNormalizedConcreteSqrtDensitySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity
      ScoreLimitLaw :=
  S.localNeighborhoodSupRiskLowerBoundSource.normalizedLANSource

/--
A concrete local-neighborhood loss-risk source supplies one-sided contiguity
of the selected local alternatives with respect to the baseline laws.
-/
theorem
    Vaart1998LANRegularEstimatorLocalNeighborhoodLossRiskLowerBoundSource.contiguitySource
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S : Vaart1998LANRegularEstimatorLocalNeighborhoodLossRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998ContiguitySource
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity) :=
  S.localNeighborhoodSupRiskLowerBoundSource.contiguitySource

/--
Chapter 8 source recording that the selected finite-local loss-risk display
is exactly the loss-risk display of its mapped neighborhood alternative.

The previous neighborhood source only needs eventual domination of finite
local risks by mapped neighborhood risks.  This refined source records the
common textbook situation where the selected finite local experiment, error,
and loss are definitionally identified with the selected mapped
neighborhood experiment.
-/
structure Vaart1998LANRegularEstimatorSelectedMappedNeighborhoodLossRiskIdentitySource
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    (dominatingMeasure : Measure Ω) (baseSqrtDensity : Ω -> ℝ)
    (localSqrtDensity : ℕ -> Ω -> ℝ)
    (ScoreLimitLaw : Measure ΩScore) (EstimatorLimitLaw : Measure ΩEstimator)
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw] where
  /-- The concrete local-neighborhood loss-risk source. -/
  lossRiskSource :
    Vaart1998LANRegularEstimatorLocalNeighborhoodLossRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw
  /-- The mapped selected neighborhood experiment is the selected local law. -/
  selected_neighborhoodMeasure_eq :
    lossRiskSource.neighborhoodMeasure
        (lossRiskSource.localParameterMap
          lossRiskSource.finiteLocalSupSource.selectedLocalParameter) =
      vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity
  /-- The mapped selected neighborhood estimator error is the selected error. -/
  selected_neighborhoodEstimatorError_eq :
    lossRiskSource.neighborhoodEstimatorError
        (lossRiskSource.localParameterMap
          lossRiskSource.finiteLocalSupSource.selectedLocalParameter) =
      (lossRiskSource.finiteLocalSupSource.selectedLossRiskSource).convolutionTheoremSource.convolutionSource.regularEstimatorSource.estimatorError
  /-- The mapped selected neighborhood loss is the selected loss. -/
  selected_neighborhoodLoss_eq :
    lossRiskSource.neighborhoodLoss
        (lossRiskSource.localParameterMap
          lossRiskSource.finiteLocalSupSource.selectedLocalParameter) =
      lossRiskSource.finiteLocalSupSource.selectedLossRiskSource.loss

/--
The concrete local-neighborhood loss-risk source carried by a selected
mapped-neighborhood identity source.
-/
def
    Vaart1998LANRegularEstimatorSelectedMappedNeighborhoodLossRiskIdentitySource.localNeighborhoodLossRiskLowerBoundSource
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S :
      Vaart1998LANRegularEstimatorSelectedMappedNeighborhoodLossRiskIdentitySource
        (ι := ι) (E := E) (Θ := Θ) dominatingMeasure
        baseSqrtDensity localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998LANRegularEstimatorLocalNeighborhoodLossRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw :=
  S.lossRiskSource

/--
The selected mapped neighborhood loss-risk display is the selected local
loss-risk display from the embedded finite-local source.
-/
theorem
    Vaart1998LANRegularEstimatorSelectedMappedNeighborhoodLossRiskIdentitySource.selectedMappedLossRisk_eq_selectedLossRisk
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S :
      Vaart1998LANRegularEstimatorSelectedMappedNeighborhoodLossRiskIdentitySource
        (ι := ι) (E := E) (Θ := Θ) dominatingMeasure
        baseSqrtDensity localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    vaart1998_localEstimatorLossRisk
        (S.lossRiskSource.neighborhoodMeasure
          (S.lossRiskSource.localParameterMap
            S.lossRiskSource.finiteLocalSupSource.selectedLocalParameter))
        (S.lossRiskSource.neighborhoodEstimatorError
          (S.lossRiskSource.localParameterMap
            S.lossRiskSource.finiteLocalSupSource.selectedLocalParameter))
        (S.lossRiskSource.neighborhoodLoss
          (S.lossRiskSource.localParameterMap
            S.lossRiskSource.finiteLocalSupSource.selectedLocalParameter)) =
      vaart1998_localEstimatorLossRisk
        (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
          localSqrtDensity)
        (S.lossRiskSource.finiteLocalSupSource.selectedLossRiskSource).convolutionTheoremSource.convolutionSource.regularEstimatorSource.estimatorError
        S.lossRiskSource.finiteLocalSupSource.selectedLossRiskSource.loss := by
  rw [S.selected_neighborhoodMeasure_eq,
    S.selected_neighborhoodEstimatorError_eq,
    S.selected_neighborhoodLoss_eq]

/--
The selected finite-local risk is exactly the selected mapped neighborhood
loss-risk display.
-/
theorem
    Vaart1998LANRegularEstimatorSelectedMappedNeighborhoodLossRiskIdentitySource.selectedLocalRisk_eq_mappedNeighborhoodLossRisk
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S :
      Vaart1998LANRegularEstimatorSelectedMappedNeighborhoodLossRiskIdentitySource
        (ι := ι) (E := E) (Θ := Θ) dominatingMeasure
        baseSqrtDensity localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    S.lossRiskSource.finiteLocalSupSource.localRisk
        S.lossRiskSource.finiteLocalSupSource.selectedLocalParameter =
      vaart1998_localEstimatorLossRisk
        (S.lossRiskSource.neighborhoodMeasure
          (S.lossRiskSource.localParameterMap
            S.lossRiskSource.finiteLocalSupSource.selectedLocalParameter))
        (S.lossRiskSource.neighborhoodEstimatorError
          (S.lossRiskSource.localParameterMap
            S.lossRiskSource.finiteLocalSupSource.selectedLocalParameter))
        (S.lossRiskSource.neighborhoodLoss
          (S.lossRiskSource.localParameterMap
            S.lossRiskSource.finiteLocalSupSource.selectedLocalParameter)) := by
  calc
    S.lossRiskSource.finiteLocalSupSource.localRisk
        S.lossRiskSource.finiteLocalSupSource.selectedLocalParameter =
      vaart1998_localEstimatorLossRisk
        (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
          localSqrtDensity)
        (S.lossRiskSource.finiteLocalSupSource.selectedLossRiskSource).convolutionTheoremSource.convolutionSource.regularEstimatorSource.estimatorError
        S.lossRiskSource.finiteLocalSupSource.selectedLossRiskSource.loss :=
          S.lossRiskSource.finiteLocalSupSource.selected_risk_eq_loss_risk
    _ =
      vaart1998_localEstimatorLossRisk
        (S.lossRiskSource.neighborhoodMeasure
          (S.lossRiskSource.localParameterMap
            S.lossRiskSource.finiteLocalSupSource.selectedLocalParameter))
        (S.lossRiskSource.neighborhoodEstimatorError
          (S.lossRiskSource.localParameterMap
            S.lossRiskSource.finiteLocalSupSource.selectedLocalParameter))
        (S.lossRiskSource.neighborhoodLoss
          (S.lossRiskSource.localParameterMap
            S.lossRiskSource.finiteLocalSupSource.selectedLocalParameter)) :=
          S.selectedMappedLossRisk_eq_selectedLossRisk.symm

/--
The selected concrete local loss-risk display is eventually bounded by the
concrete local-neighborhood loss-risk display.
-/
theorem
    Vaart1998LANRegularEstimatorSelectedMappedNeighborhoodLossRiskIdentitySource.selectedLossRisk_le_localNeighborhoodLossRisk
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S :
      Vaart1998LANRegularEstimatorSelectedMappedNeighborhoodLossRiskIdentitySource
        (ι := ι) (E := E) (Θ := Θ) dominatingMeasure
        baseSqrtDensity localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    ∀ᶠ n in atTop,
      vaart1998_localEstimatorLossRisk
          (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
            localSqrtDensity)
          (S.lossRiskSource.finiteLocalSupSource.selectedLossRiskSource).convolutionTheoremSource.convolutionSource.regularEstimatorSource.estimatorError
          S.lossRiskSource.finiteLocalSupSource.selectedLossRiskSource.loss n ≤
        S.lossRiskSource.localNeighborhoodLossRisk n := by
  have hselected :
      S.lossRiskSource.finiteLocalSupSource.selectedLocalParameter ∈
        S.lossRiskSource.finiteLocalSupSource.localParameters :=
    S.lossRiskSource.finiteLocalSupSource.selectedLocalParameter_mem
  filter_upwards
    [S.lossRiskSource.mappedLocalLossRisk_le_localNeighborhoodLossRisk
      hselected] with n hn
  simpa [S.selectedMappedLossRisk_eq_selectedLossRisk] using hn

/--
The asymptotic lower bound for the concrete local-neighborhood loss-risk
display carried through the selected mapped-neighborhood identity source.
-/
theorem
    Vaart1998LANRegularEstimatorSelectedMappedNeighborhoodLossRiskIdentitySource.asymptoticLocalNeighborhoodLossRiskLowerBound
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S :
      Vaart1998LANRegularEstimatorSelectedMappedNeighborhoodLossRiskIdentitySource
        (ι := ι) (E := E) (Θ := Θ) dominatingMeasure
        baseSqrtDensity localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998AsymptoticRiskLowerBound
      S.lossRiskSource.localNeighborhoodLossRisk
      S.lossRiskSource.finiteLocalSupSource.selectedLossRiskSource.benchmarkRisk :=
  S.lossRiskSource.asymptoticLocalNeighborhoodLossRiskLowerBound

/--
A selected mapped-neighborhood identity source exposes the selected
normalized concrete LAN source.
-/
def
    Vaart1998LANRegularEstimatorSelectedMappedNeighborhoodLossRiskIdentitySource.normalizedLANSource
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S :
      Vaart1998LANRegularEstimatorSelectedMappedNeighborhoodLossRiskIdentitySource
        (ι := ι) (E := E) (Θ := Θ) dominatingMeasure
        baseSqrtDensity localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998LANHellingerNormalizedConcreteSqrtDensitySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity
      ScoreLimitLaw :=
  S.lossRiskSource.normalizedLANSource

/--
A selected mapped-neighborhood identity source supplies one-sided contiguity
of the selected local alternatives with respect to the baseline laws.
-/
theorem
    Vaart1998LANRegularEstimatorSelectedMappedNeighborhoodLossRiskIdentitySource.contiguitySource
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S :
      Vaart1998LANRegularEstimatorSelectedMappedNeighborhoodLossRiskIdentitySource
        (ι := ι) (E := E) (Θ := Θ) dominatingMeasure
        baseSqrtDensity localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998ContiguitySource
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity) :=
  S.lossRiskSource.contiguitySource

/--
Chapter 8 source recording that every finite-local risk in the finite family
is exactly its mapped neighborhood loss-risk display.

This is the all-finite-local analogue of the selected mapped-neighborhood
identity source.  It is useful once a finite grid of local alternatives has
been embedded into a parameter neighborhood and each finite risk display has
been identified with the corresponding neighborhood experiment.
-/
structure Vaart1998LANRegularEstimatorFiniteMappedNeighborhoodLossRiskIdentitySource
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    (dominatingMeasure : Measure Ω) (baseSqrtDensity : Ω -> ℝ)
    (localSqrtDensity : ℕ -> Ω -> ℝ)
    (ScoreLimitLaw : Measure ΩScore) (EstimatorLimitLaw : Measure ΩEstimator)
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw] where
  /-- The concrete local-neighborhood loss-risk source. -/
  lossRiskSource :
    Vaart1998LANRegularEstimatorLocalNeighborhoodLossRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw
  /--
  Every finite local risk equals the loss risk of its mapped neighborhood
  alternative.
  -/
  finiteLocalRisk_eq_mappedNeighborhoodLossRisk :
    ∀ h ∈ lossRiskSource.finiteLocalSupSource.localParameters,
      lossRiskSource.finiteLocalSupSource.localRisk h =
        vaart1998_localEstimatorLossRisk
          (lossRiskSource.neighborhoodMeasure
            (lossRiskSource.localParameterMap h))
          (lossRiskSource.neighborhoodEstimatorError
            (lossRiskSource.localParameterMap h))
          (lossRiskSource.neighborhoodLoss
            (lossRiskSource.localParameterMap h))

/--
The concrete local-neighborhood loss-risk source carried by an all-finite
mapped-neighborhood identity source.
-/
def
    Vaart1998LANRegularEstimatorFiniteMappedNeighborhoodLossRiskIdentitySource.localNeighborhoodLossRiskLowerBoundSource
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S :
      Vaart1998LANRegularEstimatorFiniteMappedNeighborhoodLossRiskIdentitySource
        (ι := ι) (E := E) (Θ := Θ) dominatingMeasure
        baseSqrtDensity localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998LANRegularEstimatorLocalNeighborhoodLossRiskLowerBoundSource
      (ι := ι) (E := E) (Θ := Θ) dominatingMeasure baseSqrtDensity
      localSqrtDensity ScoreLimitLaw EstimatorLimitLaw :=
  S.lossRiskSource

/--
Each mapped neighborhood loss-risk display equals its finite-local risk.
-/
theorem
    Vaart1998LANRegularEstimatorFiniteMappedNeighborhoodLossRiskIdentitySource.mappedNeighborhoodLossRisk_eq_finiteLocalRisk
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S :
      Vaart1998LANRegularEstimatorFiniteMappedNeighborhoodLossRiskIdentitySource
        (ι := ι) (E := E) (Θ := Θ) dominatingMeasure
        baseSqrtDensity localSqrtDensity ScoreLimitLaw EstimatorLimitLaw)
    {h : ι} (hh : h ∈ S.lossRiskSource.finiteLocalSupSource.localParameters) :
    vaart1998_localEstimatorLossRisk
        (S.lossRiskSource.neighborhoodMeasure
          (S.lossRiskSource.localParameterMap h))
        (S.lossRiskSource.neighborhoodEstimatorError
          (S.lossRiskSource.localParameterMap h))
        (S.lossRiskSource.neighborhoodLoss
          (S.lossRiskSource.localParameterMap h)) =
      S.lossRiskSource.finiteLocalSupSource.localRisk h :=
  (S.finiteLocalRisk_eq_mappedNeighborhoodLossRisk h hh).symm

/--
Every finite local risk in the family is eventually bounded by the concrete
local-neighborhood loss-risk display.
-/
theorem
    Vaart1998LANRegularEstimatorFiniteMappedNeighborhoodLossRiskIdentitySource.finiteLocalRisk_le_localNeighborhoodLossRisk
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S :
      Vaart1998LANRegularEstimatorFiniteMappedNeighborhoodLossRiskIdentitySource
        (ι := ι) (E := E) (Θ := Θ) dominatingMeasure
        baseSqrtDensity localSqrtDensity ScoreLimitLaw EstimatorLimitLaw)
    {h : ι} (hh : h ∈ S.lossRiskSource.finiteLocalSupSource.localParameters) :
    ∀ᶠ n in atTop,
      S.lossRiskSource.finiteLocalSupSource.localRisk h n ≤
        S.lossRiskSource.localNeighborhoodLossRisk n := by
  filter_upwards
    [S.lossRiskSource.mappedLocalLossRisk_le_localNeighborhoodLossRisk hh]
      with n hn
  have heq :=
    congrFun (S.finiteLocalRisk_eq_mappedNeighborhoodLossRisk h hh) n
  simpa [heq] using hn

/--
The finite-local supremum risk is eventually bounded by the concrete
local-neighborhood loss-risk display.
-/
theorem
    Vaart1998LANRegularEstimatorFiniteMappedNeighborhoodLossRiskIdentitySource.finiteLocalSupRisk_le_localNeighborhoodLossRisk
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S :
      Vaart1998LANRegularEstimatorFiniteMappedNeighborhoodLossRiskIdentitySource
        (ι := ι) (E := E) (Θ := Θ) dominatingMeasure
        baseSqrtDensity localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    ∀ᶠ n in atTop,
      S.lossRiskSource.finiteLocalSupSource.finiteLocalSupRisk n ≤
        S.lossRiskSource.localNeighborhoodLossRisk n := by
  filter_upwards [S.lossRiskSource.neighborhoodLossRisk_bddAbove] with n hbdd
  have hpoint :
      ∀ h ∈ S.lossRiskSource.finiteLocalSupSource.localParameters,
        S.lossRiskSource.finiteLocalSupSource.localRisk h n ≤
          vaart1998_localEstimatorLossRisk
            (S.lossRiskSource.neighborhoodMeasure
              (S.lossRiskSource.localParameterMap h))
            (S.lossRiskSource.neighborhoodEstimatorError
              (S.lossRiskSource.localParameterMap h))
            (S.lossRiskSource.neighborhoodLoss
              (S.lossRiskSource.localParameterMap h)) n := by
    intro h hh
    exact le_of_eq
      (congrFun (S.finiteLocalRisk_eq_mappedNeighborhoodLossRisk h hh) n)
  simpa [
    Vaart1998LANRegularEstimatorFiniteLocalSupLossRiskLowerBoundSource.finiteLocalSupRisk,
    Vaart1998LANRegularEstimatorLocalNeighborhoodLossRiskLowerBoundSource.localNeighborhoodLossRisk,
    vaart1998_localNeighborhoodEstimatorLossRisk] using
      vaart1998_finiteLocalSupRisk_le_localNeighborhoodSupRisk
        S.lossRiskSource.finiteLocalSupSource.localParameters_nonempty
        S.lossRiskSource.localParameters_subset_neighborhood hpoint hbdd

/--
The asymptotic lower bound for the concrete local-neighborhood loss-risk
display carried through the all-finite mapped-neighborhood identity source.
-/
theorem
    Vaart1998LANRegularEstimatorFiniteMappedNeighborhoodLossRiskIdentitySource.asymptoticLocalNeighborhoodLossRiskLowerBound
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S :
      Vaart1998LANRegularEstimatorFiniteMappedNeighborhoodLossRiskIdentitySource
        (ι := ι) (E := E) (Θ := Θ) dominatingMeasure
        baseSqrtDensity localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998AsymptoticRiskLowerBound
      S.lossRiskSource.localNeighborhoodLossRisk
      S.lossRiskSource.finiteLocalSupSource.selectedLossRiskSource.benchmarkRisk :=
  S.lossRiskSource.asymptoticLocalNeighborhoodLossRiskLowerBound

/--
An all-finite mapped-neighborhood identity source exposes the selected
normalized concrete LAN source.
-/
def
    Vaart1998LANRegularEstimatorFiniteMappedNeighborhoodLossRiskIdentitySource.normalizedLANSource
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S :
      Vaart1998LANRegularEstimatorFiniteMappedNeighborhoodLossRiskIdentitySource
        (ι := ι) (E := E) (Θ := Θ) dominatingMeasure
        baseSqrtDensity localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998LANHellingerNormalizedConcreteSqrtDensitySource
      (E := E) dominatingMeasure baseSqrtDensity localSqrtDensity
      ScoreLimitLaw :=
  S.lossRiskSource.normalizedLANSource

/--
An all-finite mapped-neighborhood identity source supplies one-sided
contiguity of the selected local alternatives with respect to the baseline
laws.
-/
theorem
    Vaart1998LANRegularEstimatorFiniteMappedNeighborhoodLossRiskIdentitySource.contiguitySource
    {ι Ω ΩScore ΩEstimator E Θ : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩScore]
    [MeasurableSpace ΩEstimator]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [BorelSpace E] [OpensMeasurableSpace E]
    [NormedAddCommGroup Θ] [NormedSpace ℝ Θ]
    [MeasurableSpace Θ] [BorelSpace Θ] [OpensMeasurableSpace Θ]
    {dominatingMeasure : Measure Ω} {baseSqrtDensity : Ω -> ℝ}
    {localSqrtDensity : ℕ -> Ω -> ℝ}
    {ScoreLimitLaw : Measure ΩScore}
    {EstimatorLimitLaw : Measure ΩEstimator}
    [IsProbabilityMeasure ScoreLimitLaw]
    [IsProbabilityMeasure EstimatorLimitLaw]
    (S :
      Vaart1998LANRegularEstimatorFiniteMappedNeighborhoodLossRiskIdentitySource
        (ι := ι) (E := E) (Θ := Θ) dominatingMeasure
        baseSqrtDensity localSqrtDensity ScoreLimitLaw EstimatorLimitLaw) :
    Vaart1998ContiguitySource
      (vaart1998_localSqrtDensityMeasureSeq dominatingMeasure
        localSqrtDensity)
      (vaart1998_baseSqrtDensityMeasureSeq dominatingMeasure
        baseSqrtDensity) :=
  S.lossRiskSource.contiguitySource

end AsymptoticStatistics
end StatInference
