import StatInference.AsymptoticStatistics.Testing
import StatInference.AsymptoticStatistics.ExperimentLimits
import StatInference.AsymptoticStatistics.Efficiency

/-!
# van der Vaart 1998 Chapter 15 efficient-test interfaces

This module opens the Chapter 15 lane.  It packages the asymptotic
representation theorem for power functions, the Gaussian one-sided testing
envelope, LAN efficient-test bounds, Wald-test handoffs, and the one-sample
and two-sample source shapes used later by signed-rank, Wilcoxon, and
log-rank examples.
-/

noncomputable section

namespace StatInference
namespace AsymptoticStatistics

open Filter MeasureTheory ProbabilityTheory
open scoped ENNReal ProbabilityTheory Topology

/--
The Gaussian one-sided normal-mean power envelope from Proposition 15.2:
`1 - Phi(z_alpha - signal / sqrt(variance))`.
-/
def vaart1998_normalMeanOneSidedPowerEnvelope
    (normalUpperTail : Real -> Real) (zAlpha signal variance : Real) :
    Real :=
  normalUpperTail (zAlpha - signal / Real.sqrt variance)

/--
The critical threshold `z_alpha * sqrt(variance)` for the scalar projection
`c^T X` in Proposition 15.2.
-/
def vaart1998_normalMeanOneSidedCriticalValue
    (zAlpha variance : Real) : Real :=
  zAlpha * Real.sqrt variance

/--
Theorem 15.1 source: a pointwise limit of power functions along a convergent
sequence of experiments is represented by a test in the dominated limit
experiment.
-/
structure Vaart1998Theorem15_1AsymptoticRepresentationSource
    {Omega OmegaLimit H Z : Type*} [MeasurableSpace Omega]
    [MeasurableSpace OmegaLimit]
    [TopologicalSpace Z] [MeasurableSpace Z] [OpensMeasurableSpace Z]
    (P : H -> Nat -> Measure Omega) (Q : H -> Measure OmegaLimit)
    [∀ h n, IsProbabilityMeasure (P h n)]
    [∀ h, IsProbabilityMeasure (Q h)] where
  /-- Chapter 9 experiment convergence source reused by the testing theorem. -/
  experimentLimitSource :
    Vaart1998ExperimentLimitSource (Z := Z) P Q
  /-- The limit experiment is dominated. -/
  dominatedLimitExperiment : Prop
  /-- Finite-sample randomized tests. -/
  finiteTest : Nat -> Omega -> Real
  /-- Finite-sample power functions. -/
  finitePower : Nat -> H -> Real
  /-- Pointwise limiting power function. -/
  limitingPower : H -> Real
  /-- Test in the limit experiment. -/
  limitTest : OmegaLimit -> Real
  /-- Finite-sample powers are expectations of the finite tests. -/
  finitePower_eq_integral :
    ∀ n h, finitePower n h = ∫ x, finiteTest n x ∂(P h n)
  /-- The limiting power is represented by the limit-experiment test. -/
  limitingPower_eq_integral :
    ∀ h, limitingPower h = ∫ x, limitTest x ∂(Q h)
  /-- Finite tests take values in `[0,1]`. -/
  finiteTest_range :
    ∀ n x, finiteTest n x ∈ Set.Icc (0 : Real) 1
  /-- The limit test takes values in `[0,1]`. -/
  limitTest_range :
    ∀ x, limitTest x ∈ Set.Icc (0 : Real) 1
  /-- Pointwise convergence of the finite power functions. -/
  finitePower_tendsto :
    ∀ h, Tendsto (fun n => finitePower n h) atTop (𝓝 (limitingPower h))
  /-- Source proof that the limit experiment is dominated. -/
  dominatedLimitExperiment_proof :
    dominatedLimitExperiment

/--
The Chapter 9 experiment-limit certificate carried by Theorem 15.1.
-/
theorem Vaart1998Theorem15_1AsymptoticRepresentationSource.experiment_tendstoInDistribution
    {Omega OmegaLimit H Z : Type*} [MeasurableSpace Omega]
    [MeasurableSpace OmegaLimit]
    [TopologicalSpace Z] [MeasurableSpace Z] [OpensMeasurableSpace Z]
    {P : H -> Nat -> Measure Omega} {Q : H -> Measure OmegaLimit}
    [∀ h n, IsProbabilityMeasure (P h n)]
    [∀ h, IsProbabilityMeasure (Q h)]
    (S :
      Vaart1998Theorem15_1AsymptoticRepresentationSource (Z := Z) P Q)
    {h : H} (hh : h ∈ S.experimentLimitSource.parameterSet) :
    TendstoInDistribution S.experimentLimitSource.statistic atTop
      S.experimentLimitSource.limitStatistic (P h) (Q h) :=
  S.experimentLimitSource.tendstoInDistribution hh

/--
Theorem 15.1 limiting-power representation display.
-/
theorem Vaart1998Theorem15_1AsymptoticRepresentationSource.limiting_power_display
    {Omega OmegaLimit H Z : Type*} [MeasurableSpace Omega]
    [MeasurableSpace OmegaLimit]
    [TopologicalSpace Z] [MeasurableSpace Z] [OpensMeasurableSpace Z]
    {P : H -> Nat -> Measure Omega} {Q : H -> Measure OmegaLimit}
    [∀ h n, IsProbabilityMeasure (P h n)]
    [∀ h, IsProbabilityMeasure (Q h)]
    (S :
      Vaart1998Theorem15_1AsymptoticRepresentationSource (Z := Z) P Q)
    (h : H) :
    S.limitingPower h = ∫ x, S.limitTest x ∂(Q h) :=
  S.limitingPower_eq_integral h

/--
Theorem 15.1 pointwise convergence of finite power functions.
-/
theorem Vaart1998Theorem15_1AsymptoticRepresentationSource.finite_power_tendsto
    {Omega OmegaLimit H Z : Type*} [MeasurableSpace Omega]
    [MeasurableSpace OmegaLimit]
    [TopologicalSpace Z] [MeasurableSpace Z] [OpensMeasurableSpace Z]
    {P : H -> Nat -> Measure Omega} {Q : H -> Measure OmegaLimit}
    [∀ h n, IsProbabilityMeasure (P h n)]
    [∀ h, IsProbabilityMeasure (Q h)]
    (S :
      Vaart1998Theorem15_1AsymptoticRepresentationSource (Z := Z) P Q)
    (h : H) :
    Tendsto (fun n => S.finitePower n h) atTop
      (𝓝 (S.limitingPower h)) :=
  S.finitePower_tendsto h

/--
Proposition 15.2 source: the projected normal-mean test is uniformly most
powerful among level-alpha tests for a one-sided linear alternative.
-/
structure Vaart1998Proposition15_2GaussianOneSidedUMPSource where
  /-- Upper tail of the standard normal law. -/
  normalUpperTail : Real -> Real
  /-- Level. -/
  alpha : Real
  /-- Standard-normal upper-tail critical point. -/
  zAlpha : Real
  /-- Scalar signal `c^T h`. -/
  signal : Real
  /-- Projection variance `c^T Sigma c`. -/
  variance : Real
  /-- Positivity assumption on the projection variance. -/
  variance_pos : 0 < variance
  /-- Critical value for rejecting on large projected observations. -/
  criticalValue : Real
  /-- Power envelope at the supplied signal. -/
  powerEnvelope : Real
  /-- Level-alpha side condition. -/
  levelAlpha : Prop
  /-- Uniform-most-powerful assertion. -/
  uniformlyMostPowerful : Prop
  /-- Critical-value display. -/
  criticalValue_eq :
    criticalValue =
      vaart1998_normalMeanOneSidedCriticalValue zAlpha variance
  /-- Power-envelope display. -/
  powerEnvelope_eq :
    powerEnvelope =
      vaart1998_normalMeanOneSidedPowerEnvelope
        normalUpperTail zAlpha signal variance
  /-- Source proof of level control. -/
  levelAlpha_proof :
    levelAlpha
  /-- Source proof of uniform most-powerful optimality. -/
  uniformlyMostPowerful_proof :
    uniformlyMostPowerful

/--
Proposition 15.2 critical-value display.
-/
theorem Vaart1998Proposition15_2GaussianOneSidedUMPSource.critical_value_display
    (S : Vaart1998Proposition15_2GaussianOneSidedUMPSource) :
    S.criticalValue =
      vaart1998_normalMeanOneSidedCriticalValue S.zAlpha S.variance :=
  S.criticalValue_eq

/--
Proposition 15.2 power-envelope display.
-/
theorem Vaart1998Proposition15_2GaussianOneSidedUMPSource.power_envelope_display
    (S : Vaart1998Proposition15_2GaussianOneSidedUMPSource) :
    S.powerEnvelope =
      vaart1998_normalMeanOneSidedPowerEnvelope
        S.normalUpperTail S.zAlpha S.signal S.variance :=
  S.powerEnvelope_eq

/--
The one-dimensional LAN efficient slope: `sqrt(I_theta0)`.
-/
def vaart1998_lanOneDimensionalEfficientSlope
    (fisherInformation : Real) : Real :=
  Real.sqrt fisherInformation

/--
The one-dimensional LAN power envelope:
`1 - Phi(z_alpha - h * sqrt(I_theta0))`.
-/
def vaart1998_lanOneDimensionalPowerEnvelope
    (normalUpperTail : Real -> Real) (zAlpha h fisherInformation : Real) :
    Real :=
  normalUpperTail
    (zAlpha - h * vaart1998_lanOneDimensionalEfficientSlope fisherInformation)

/--
The observation-ratio relative efficiency of the best test versus a test with
slope `s`: `I / s^2`.
-/
def vaart1998_bestTestObservationRatio
    (fisherInformation slope : Real) : Real :=
  fisherInformation / slope ^ 2

/--
Section 15.3 source: a Chapter 14 local-power source whose slope is the LAN
efficient slope realizes the one-dimensional Chapter 15 envelope.
-/
structure Vaart1998Section15_3OneDimensionalLANPowerBoundSource
    {Omega OmegaLimit : Type*} [MeasurableSpace Omega]
    [MeasurableSpace OmegaLimit]
    (P : Real -> Nat -> Measure Omega)
    [∀ h n, IsProbabilityMeasure (P h n)]
    (LimitLaw : Measure OmegaLimit) [IsProbabilityMeasure LimitLaw] where
  /-- The Chapter 14 local-power source for the sequence of tests. -/
  localPowerSource :
    Vaart1998Theorem14_7LocalPowerSource P LimitLaw
  /-- Fisher information at the boundary point. -/
  fisherInformation : Real
  /-- Positivity of Fisher information. -/
  fisherInformation_pos : 0 < fisherInformation
  /-- Efficient slope in the Gaussian limit. -/
  efficientSlope : Real
  /-- The local-power source has the efficient slope. -/
  slope_eq_efficientSlope :
    localPowerSource.slope = efficientSlope
  /-- Efficient-slope display. -/
  efficientSlope_eq :
    efficientSlope =
      vaart1998_lanOneDimensionalEfficientSlope fisherInformation
  /-- Proposition 15.2 supplies the Gaussian upper bound. -/
  gaussianUMPSource :
    Vaart1998Proposition15_2GaussianOneSidedUMPSource
  /-- The local Gaussian UMP argument bounds all level-alpha limits. -/
  upperBoundForLevelAlpha : Prop
  /-- Source proof of the upper-bound argument. -/
  upperBoundForLevelAlpha_proof :
    upperBoundForLevelAlpha

/--
Section 15.3 local-power limit specialized to the LAN efficient envelope.
-/
theorem Vaart1998Section15_3OneDimensionalLANPowerBoundSource.local_power_limit_envelope
    {Omega OmegaLimit : Type*} [MeasurableSpace Omega]
    [MeasurableSpace OmegaLimit]
    {P : Real -> Nat -> Measure Omega}
    [∀ h n, IsProbabilityMeasure (P h n)]
    {LimitLaw : Measure OmegaLimit} [IsProbabilityMeasure LimitLaw]
    (S :
      Vaart1998Section15_3OneDimensionalLANPowerBoundSource P LimitLaw)
    (h : Real) :
    Tendsto (fun n => S.localPowerSource.localPower n h) atTop
      (𝓝 (vaart1998_lanOneDimensionalPowerEnvelope
        S.localPowerSource.normalUpperTail S.localPowerSource.zAlpha h
        S.fisherInformation)) := by
  simpa [vaart1998_lanOneDimensionalPowerEnvelope,
    vaart1998_lanOneDimensionalEfficientSlope,
    vaart1998_localPowerLimitDisplay,
    S.slope_eq_efficientSlope, S.efficientSlope_eq]
    using S.localPowerSource.local_power_limit h

/--
Section 15.3 observation-ratio display.
-/
theorem Vaart1998Section15_3OneDimensionalLANPowerBoundSource.best_test_observation_ratio_display
    (fisherInformation slope : Real) :
    vaart1998_bestTestObservationRatio fisherInformation slope =
      fisherInformation / slope ^ 2 :=
  rfl

/--
The general LAN half-space efficient-test power envelope from Theorem 15.4:
`1 - Phi(z_alpha - directionalDerivative / sqrt(efficientVariance))`.
-/
def vaart1998_lanEfficientPowerEnvelope
    (normalUpperTail : Real -> Real) (zAlpha directionalDerivative
      efficientVariance : Real) :
    Real :=
  normalUpperTail
    (zAlpha - directionalDerivative / Real.sqrt efficientVariance)

/--
The efficient projection of the central sequence in Addendum 15.5.
-/
def vaart1998_lanEfficientCentralSequenceProjection
    (directionalCentralSequence efficientVariance : Real) : Real :=
  directionalCentralSequence / Real.sqrt efficientVariance

/--
Theorem 15.4 source: the LAN Gaussian limit and Proposition 15.2 yield an
absolute upper bound for local asymptotic powers of level-alpha tests.
-/
structure Vaart1998Theorem15_4LANPowerUpperBoundSource where
  /-- Upper tail of the standard normal law. -/
  normalUpperTail : Real -> Real
  /-- Level. -/
  alpha : Real
  /-- Standard-normal critical point. -/
  zAlpha : Real
  /-- Directional derivative `dot psi_theta0 h`. -/
  directionalDerivative : Real
  /-- Efficient variance `dot psi I^{-1} dot psi^T`. -/
  efficientVariance : Real
  /-- Positive-alternative side condition. -/
  directionalDerivative_pos : 0 < directionalDerivative
  /-- Positive efficient-variance side condition. -/
  efficientVariance_pos : 0 < efficientVariance
  /-- Recorded local limsup power. -/
  localPowerLimsup : Real
  /-- Power envelope supplied by the Gaussian limit experiment. -/
  powerEnvelope : Real
  /-- LAN source used to identify the Gaussian limit experiment. -/
  lanExperimentLimit : Prop
  /-- Theorem 15.1 representation step for subsequential power limits. -/
  asymptoticRepresentation : Prop
  /-- Proposition 15.2 Gaussian UMP source. -/
  gaussianUMPSource :
    Vaart1998Proposition15_2GaussianOneSidedUMPSource
  /-- Level-alpha source condition. -/
  levelAlpha : Prop
  /-- Power-envelope display. -/
  powerEnvelope_eq :
    powerEnvelope =
      vaart1998_lanEfficientPowerEnvelope
        normalUpperTail zAlpha directionalDerivative efficientVariance
  /-- Local power is bounded by the Gaussian envelope. -/
  localPower_limsup_le :
    localPowerLimsup <= powerEnvelope
  /-- Source proof of the LAN limit step. -/
  lanExperimentLimit_proof :
    lanExperimentLimit
  /-- Source proof of the asymptotic representation step. -/
  asymptoticRepresentation_proof :
    asymptoticRepresentation
  /-- Source proof of level control. -/
  levelAlpha_proof :
    levelAlpha

/--
Theorem 15.4 local asymptotic power upper bound.
-/
theorem Vaart1998Theorem15_4LANPowerUpperBoundSource.local_power_upper_bound
    (S : Vaart1998Theorem15_4LANPowerUpperBoundSource) :
    S.localPowerLimsup <=
      vaart1998_lanEfficientPowerEnvelope
        S.normalUpperTail S.zAlpha S.directionalDerivative
        S.efficientVariance := by
  simpa [S.powerEnvelope_eq] using S.localPower_limsup_le

/--
Addendum 15.5 source: a statistic with the efficient central-sequence
projection attains the Theorem 15.4 upper bound.
-/
structure Vaart1998Addendum15_5OptimalTestSource where
  /-- Upper tail of the standard normal law. -/
  normalUpperTail : Real -> Real
  /-- Standard-normal critical point. -/
  zAlpha : Real
  /-- Directional derivative for the local alternative. -/
  directionalDerivative : Real
  /-- Efficient variance. -/
  efficientVariance : Real
  /-- Efficient projected central sequence. -/
  projectedCentralSequence : Nat -> Real
  /-- Test statistics. -/
  statistic : Nat -> Real
  /-- Local power sequence. -/
  localPower : Nat -> Real
  /-- Envelope value. -/
  powerEnvelope : Real
  /-- Statistic representation as efficient projection plus `o_P(1)`. -/
  statisticRepresentation : Prop
  /-- Rejection rule `T_n >= z_alpha`. -/
  rejectionRule : Prop
  /-- Power-envelope display. -/
  powerEnvelope_eq :
    powerEnvelope =
      vaart1998_lanEfficientPowerEnvelope
        normalUpperTail zAlpha directionalDerivative efficientVariance
  /-- Local powers converge to the envelope. -/
  localPower_tendsto :
    Tendsto localPower atTop (𝓝 powerEnvelope)
  /-- Source proof of the statistic representation. -/
  statisticRepresentation_proof :
    statisticRepresentation
  /-- Source proof of the rejection rule. -/
  rejectionRule_proof :
    rejectionRule

/--
Addendum 15.5 optimal-power convergence.
-/
theorem Vaart1998Addendum15_5OptimalTestSource.local_power_tendsto_envelope
    (S : Vaart1998Addendum15_5OptimalTestSource) :
    Tendsto S.localPower atTop
      (𝓝 (vaart1998_lanEfficientPowerEnvelope
        S.normalUpperTail S.zAlpha S.directionalDerivative
        S.efficientVariance)) := by
  simpa [S.powerEnvelope_eq] using S.localPower_tendsto

/--
Wald statistic display from Example 15.6.
-/
def vaart1998_waldStatisticDisplay
    (rate psiValue efficientVariance : Real) : Real :=
  rate * psiValue / Real.sqrt efficientVariance

/--
Example 15.6 source: efficient estimators combined with the delta method and
Slutsky yield asymptotically efficient Wald tests.
-/
structure Vaart1998Example15_6WaldTestSource where
  /-- Rate, usually `sqrt n` in the iid case. -/
  rate : Nat -> Real
  /-- Constraint value at the estimator. -/
  psiEstimatorValue : Nat -> Real
  /-- Estimated efficient variance. -/
  estimatedEfficientVariance : Nat -> Real
  /-- Wald statistics. -/
  waldStatistic : Nat -> Real
  /-- Efficient-estimator source from Chapter 8. -/
  efficientEstimatorSource : Prop
  /-- Delta-method source for `psi`. -/
  deltaMethodSource : Prop
  /-- Continuity of the Fisher-information/gradient variance display. -/
  informationContinuity : Prop
  /-- Addendum 15.5 optimal-test source supplied by the Wald statistic. -/
  optimalTestSource :
    Vaart1998Addendum15_5OptimalTestSource
  /-- Consistency at fixed positive alternatives. -/
  consistentAtPositiveAlternative : Prop
  /-- Wald-statistic display. -/
  waldStatistic_eq :
    waldStatistic =
      fun n =>
        vaart1998_waldStatisticDisplay
          (rate n) (psiEstimatorValue n) (estimatedEfficientVariance n)
  /-- Source proof of estimator efficiency. -/
  efficientEstimatorSource_proof :
    efficientEstimatorSource
  /-- Source proof of the delta-method step. -/
  deltaMethodSource_proof :
    deltaMethodSource
  /-- Source proof of information continuity. -/
  informationContinuity_proof :
    informationContinuity
  /-- Source proof of consistency at positive alternatives. -/
  consistentAtPositiveAlternative_proof :
    consistentAtPositiveAlternative

/--
Example 15.6 Wald tests attain the Addendum 15.5 envelope.
-/
theorem Vaart1998Example15_6WaldTestSource.asymptotically_optimal
    (S : Vaart1998Example15_6WaldTestSource) :
    Tendsto S.optimalTestSource.localPower atTop
      (𝓝 (vaart1998_lanEfficientPowerEnvelope
        S.optimalTestSource.normalUpperTail S.optimalTestSource.zAlpha
        S.optimalTestSource.directionalDerivative
        S.optimalTestSource.efficientVariance)) :=
  S.optimalTestSource.local_power_tendsto_envelope

/--
One-sample location efficient-score statistic display (15.7).  The
`sampleScale` argument records the `1 / sqrt n` normalization.
-/
def vaart1998_oneSampleLocationScoreStatisticDisplay
    (sampleScale fisherInformation scoreSum : Real) : Real :=
  - sampleScale * scoreSum / Real.sqrt fisherInformation

/--
One-sample location power envelope:
`1 - Phi(z_alpha - h * sqrt(I_f))`.
-/
def vaart1998_oneSampleLocationPowerEnvelope
    (normalUpperTail : Real -> Real) (zAlpha h fisherInformation : Real) :
    Real :=
  vaart1998_lanOneDimensionalPowerEnvelope
    normalUpperTail zAlpha h fisherInformation

/--
Section 15.4 source: statistics satisfying display (15.7) attain the
one-sample location power envelope.
-/
structure Vaart1998OneSampleLocationEfficientScoreSource where
  /-- Upper tail of the standard normal law. -/
  normalUpperTail : Real -> Real
  /-- Standard-normal critical point. -/
  zAlpha : Real
  /-- Local shift. -/
  localShift : Real
  /-- Fisher information for location. -/
  fisherInformation : Real
  /-- Positive information. -/
  fisherInformation_pos : 0 < fisherInformation
  /-- Statistic satisfying (15.7). -/
  statistic : Nat -> Real
  /-- Score sums in (15.7). -/
  scoreSum : Nat -> Real
  /-- Normalizing scale, usually `1 / sqrt n`. -/
  sampleScale : Nat -> Real
  /-- Power envelope. -/
  powerEnvelope : Real
  /-- Addendum 15.5 source proving optimality. -/
  optimalTestSource :
    Vaart1998Addendum15_5OptimalTestSource
  /-- Display (15.7). -/
  statistic_eq :
    statistic =
      fun n =>
        vaart1998_oneSampleLocationScoreStatisticDisplay
          (sampleScale n) fisherInformation (scoreSum n)
  /-- Power-envelope display. -/
  powerEnvelope_eq :
    powerEnvelope =
      vaart1998_oneSampleLocationPowerEnvelope
        normalUpperTail zAlpha localShift fisherInformation
  /-- Statistic representation source for the `o_P(1)` remainder. -/
  statisticRepresentation : Prop
  /-- Source proof of the statistic representation. -/
  statisticRepresentation_proof :
    statisticRepresentation

/--
Section 15.4 one-sample efficient-score optimality.
-/
theorem Vaart1998OneSampleLocationEfficientScoreSource.local_power_tendsto_envelope
    (S : Vaart1998OneSampleLocationEfficientScoreSource) :
    Tendsto S.optimalTestSource.localPower atTop
      (𝓝 (vaart1998_lanEfficientPowerEnvelope
        S.optimalTestSource.normalUpperTail S.optimalTestSource.zAlpha
        S.optimalTestSource.directionalDerivative
        S.optimalTestSource.efficientVariance)) :=
  S.optimalTestSource.local_power_tendsto_envelope

/--
Signed-rank efficient score generator (15.9).
-/
def vaart1998_signedRankEfficientScoreFunction
    (sqrtInformation : Real) (locationScore absoluteQuantile : Real -> Real)
    (u : Real) : Real :=
  - locationScore (absoluteQuantile u) / sqrtInformation

/--
Corollary 15.10 source: locally most-powerful signed-rank scores satisfy
display (15.7), hence the signed-rank tests are asymptotically optimal.
-/
structure Vaart1998Corollary15_10SignedRankOptimalSource where
  /-- Square root of Fisher information. -/
  sqrtInformation : Real
  /-- Location score `f' / f`. -/
  locationScore : Real -> Real
  /-- Quantile of the absolute-value distribution. -/
  absoluteQuantile : Real -> Real
  /-- Score generator from (15.9). -/
  scoreFunction : Real -> Real
  /-- Chapter 13 signed-rank source. -/
  signedRankSource : Prop
  /-- The Section 15.4 efficient-score source. -/
  efficientScoreSource :
    Vaart1998OneSampleLocationEfficientScoreSource
  /-- Score-function display. -/
  scoreFunction_eq :
    scoreFunction =
      vaart1998_signedRankEfficientScoreFunction
        sqrtInformation locationScore absoluteQuantile
  /-- Source proof of the Chapter 13 signed-rank approximation. -/
  signedRankSource_proof :
    signedRankSource

/--
Corollary 15.10 signed-rank optimality handoff.
-/
theorem Vaart1998Corollary15_10SignedRankOptimalSource.asymptotically_optimal
    (S : Vaart1998Corollary15_10SignedRankOptimalSource) :
    Tendsto S.efficientScoreSource.optimalTestSource.localPower atTop
      (𝓝 (vaart1998_lanEfficientPowerEnvelope
        S.efficientScoreSource.optimalTestSource.normalUpperTail
        S.efficientScoreSource.optimalTestSource.zAlpha
        S.efficientScoreSource.optimalTestSource.directionalDerivative
        S.efficientScoreSource.optimalTestSource.efficientVariance)) :=
  S.efficientScoreSource.local_power_tendsto_envelope

/--
Example 15.11 source: for the Laplace density, the sign statistic satisfies
the efficient one-sample display.
-/
structure Vaart1998Example15_11LaplaceSignOptimalSource where
  /-- Sign statistic source. -/
  signStatisticSource : Prop
  /-- Efficient one-sample source. -/
  efficientScoreSource :
    Vaart1998OneSampleLocationEfficientScoreSource
  /-- Source proof for the sign statistic. -/
  signStatisticSource_proof :
    signStatisticSource

/--
Example 15.11 sign-test optimality.
-/
theorem Vaart1998Example15_11LaplaceSignOptimalSource.asymptotically_optimal
    (S : Vaart1998Example15_11LaplaceSignOptimalSource) :
    Tendsto S.efficientScoreSource.optimalTestSource.localPower atTop
      (𝓝 (vaart1998_lanEfficientPowerEnvelope
        S.efficientScoreSource.optimalTestSource.normalUpperTail
        S.efficientScoreSource.optimalTestSource.zAlpha
        S.efficientScoreSource.optimalTestSource.directionalDerivative
        S.efficientScoreSource.optimalTestSource.efficientVariance)) :=
  S.efficientScoreSource.local_power_tendsto_envelope

/--
Example 15.12 normal-score signed-rank score display.
-/
def vaart1998_normalScoreSignedRankDisplay
    (normalQuantile : Real -> Real) (u : Real) : Real :=
  normalQuantile ((u + 1) / 2)

/--
Example 15.12 source: normal-score signed-rank tests have the same asymptotic
slope as the one-sample `t` test under normality.
-/
structure Vaart1998Example15_12NormalSignedRankSource where
  /-- Normal score generator. -/
  normalQuantile : Real -> Real
  /-- Score function used by the signed-rank statistic. -/
  scoreFunction : Real -> Real
  /-- One-sample `t`-test slope. -/
  tTestSlope : Real
  /-- Signed-rank slope. -/
  signedRankSlope : Real
  /-- Score display. -/
  scoreFunction_eq :
    scoreFunction =
      vaart1998_normalScoreSignedRankDisplay normalQuantile
  /-- Same asymptotic slope as the `t` test. -/
  signedRankSlope_eq_tTestSlope :
    signedRankSlope = tTestSlope

/--
Example 15.12 same-slope display.
-/
theorem Vaart1998Example15_12NormalSignedRankSource.same_slope_as_t_test
    (S : Vaart1998Example15_12NormalSignedRankSource) :
    S.signedRankSlope = S.tTestSlope :=
  S.signedRankSlope_eq_tTestSlope

/--
Two-sample optimal slope from Corollary 15.14.
-/
def vaart1998_twoSampleOptimalSlope
    (lambda informationP informationQ : Real) : Real :=
  Real.sqrt
    (lambda * (1 - lambda) * informationP * informationQ /
      (lambda * informationP + (1 - lambda) * informationQ))

/--
Two-sample power envelope from Corollary 15.14.
-/
def vaart1998_twoSamplePowerEnvelope
    (normalUpperTail : Real -> Real) (zAlpha lambda informationP
      informationQ g h : Real) :
    Real :=
  normalUpperTail
    (zAlpha - (h - g) *
      vaart1998_twoSampleOptimalSlope lambda informationP informationQ)

/--
Corollary 15.14 source: the two-sample LAN bound for local alternatives
`(mu + g / sqrt N, mu + h / sqrt N)`.
-/
structure Vaart1998Corollary15_14TwoSamplePowerBoundSource where
  /-- Upper tail of the standard normal law. -/
  normalUpperTail : Real -> Real
  /-- Level. -/
  alpha : Real
  /-- Standard-normal critical point. -/
  zAlpha : Real
  /-- Sampling fraction limit. -/
  lambda : Real
  /-- Fisher information for the first model. -/
  informationP : Real
  /-- Fisher information for the second model. -/
  informationQ : Real
  /-- First local coordinate. -/
  g : Real
  /-- Second local coordinate. -/
  h : Real
  /-- Alternative-side condition `h > g`. -/
  h_gt_g : h > g
  /-- Sampling fraction side condition. -/
  lambda_mem_unit : lambda ∈ Set.Ioo (0 : Real) 1
  /-- Positive first information. -/
  informationP_pos : 0 < informationP
  /-- Positive second information. -/
  informationQ_pos : 0 < informationQ
  /-- Local limsup power. -/
  localPowerLimsup : Real
  /-- Optimal slope. -/
  optimalSlope : Real
  /-- Power envelope. -/
  powerEnvelope : Real
  /-- Two-sample LAN source. -/
  twoSampleLANSource : Prop
  /-- Theorem 15.4 source specialized to `psi(mu,nu)=nu-mu`. -/
  theorem15_4Source :
    Vaart1998Theorem15_4LANPowerUpperBoundSource
  /-- Optimal-slope display. -/
  optimalSlope_eq :
    optimalSlope =
      vaart1998_twoSampleOptimalSlope lambda informationP informationQ
  /-- Power-envelope display. -/
  powerEnvelope_eq :
    powerEnvelope =
      vaart1998_twoSamplePowerEnvelope
        normalUpperTail zAlpha lambda informationP informationQ g h
  /-- Local power is bounded by the envelope. -/
  localPower_limsup_le :
    localPowerLimsup <= powerEnvelope
  /-- Source proof of the two-sample LAN display. -/
  twoSampleLANSource_proof :
    twoSampleLANSource

/--
Corollary 15.14 local two-sample power bound.
-/
theorem Vaart1998Corollary15_14TwoSamplePowerBoundSource.local_power_upper_bound
    (S : Vaart1998Corollary15_14TwoSamplePowerBoundSource) :
    S.localPowerLimsup <=
      vaart1998_twoSamplePowerEnvelope
        S.normalUpperTail S.zAlpha S.lambda S.informationP S.informationQ
        S.g S.h := by
  simpa [S.powerEnvelope_eq] using S.localPower_limsup_le

/--
Two-sample optimal statistic display following Corollary 15.14.
-/
def vaart1998_twoSampleOptimalStatisticDisplay
    (optimalSlope lambda informationP informationQ firstScore secondScore :
      Real) :
    Real :=
  optimalSlope *
    (secondScore / (Real.sqrt (1 - lambda) * informationQ) -
      firstScore / (Real.sqrt lambda * informationP))

/--
Two-sample optimal statistic source after Corollary 15.14.
-/
structure Vaart1998TwoSampleOptimalStatisticSource where
  /-- Optimal slope. -/
  optimalSlope : Real
  /-- Sampling fraction. -/
  lambda : Real
  /-- First Fisher information. -/
  informationP : Real
  /-- Second Fisher information. -/
  informationQ : Real
  /-- First score-sum normalization. -/
  firstScore : Nat -> Real
  /-- Second score-sum normalization. -/
  secondScore : Nat -> Real
  /-- Statistic sequence. -/
  statistic : Nat -> Real
  /-- Addendum 15.5 optimal-test source. -/
  optimalTestSource :
    Vaart1998Addendum15_5OptimalTestSource
  /-- Statistic display. -/
  statistic_eq :
    statistic =
      fun n =>
        vaart1998_twoSampleOptimalStatisticDisplay
          optimalSlope lambda informationP informationQ
          (firstScore n) (secondScore n)
  /-- Source proof that this display has unit limiting variance. -/
  unitLimitVariance : Prop
  /-- Source proof of the unit-variance display. -/
  unitLimitVariance_proof :
    unitLimitVariance

/--
Two-sample optimal statistic attains the Addendum 15.5 envelope.
-/
theorem Vaart1998TwoSampleOptimalStatisticSource.asymptotically_optimal
    (S : Vaart1998TwoSampleOptimalStatisticSource) :
    Tendsto S.optimalTestSource.localPower atTop
      (𝓝 (vaart1998_lanEfficientPowerEnvelope
        S.optimalTestSource.normalUpperTail S.optimalTestSource.zAlpha
        S.optimalTestSource.directionalDerivative
        S.optimalTestSource.efficientVariance)) :=
  S.optimalTestSource.local_power_tendsto_envelope

/--
Example 15.15 source: Wilcoxon/Mann-Whitney is asymptotically UMP for
logistic two-sample location alternatives.
-/
structure Vaart1998Example15_15WilcoxonLogisticOptimalSource where
  /-- Chapter 13 Wilcoxon/Mann-Whitney source. -/
  wilcoxonRankSource : Prop
  /-- Two-sample optimal statistic source. -/
  twoSampleOptimalSource :
    Vaart1998TwoSampleOptimalStatisticSource
  /-- Source proof identifying logistic scores with Wilcoxon scores. -/
  wilcoxonRankSource_proof :
    wilcoxonRankSource

/--
Example 15.15 Wilcoxon optimality handoff.
-/
theorem Vaart1998Example15_15WilcoxonLogisticOptimalSource.asymptotically_optimal
    (S : Vaart1998Example15_15WilcoxonLogisticOptimalSource) :
    Tendsto S.twoSampleOptimalSource.optimalTestSource.localPower atTop
      (𝓝 (vaart1998_lanEfficientPowerEnvelope
        S.twoSampleOptimalSource.optimalTestSource.normalUpperTail
        S.twoSampleOptimalSource.optimalTestSource.zAlpha
        S.twoSampleOptimalSource.optimalTestSource.directionalDerivative
        S.twoSampleOptimalSource.optimalTestSource.efficientVariance)) :=
  S.twoSampleOptimalSource.asymptotically_optimal

/--
Example 15.16 source: the log-rank test is asymptotically optimal for
proportional-hazard alternatives.
-/
structure Vaart1998Example15_16LogRankOptimalSource where
  /-- Log-rank statistic source. -/
  logRankSource : Prop
  /-- Two-sample optimal statistic source. -/
  twoSampleOptimalSource :
    Vaart1998TwoSampleOptimalStatisticSource
  /-- Source proof identifying log-rank scores with the efficient scores. -/
  logRankSource_proof :
    logRankSource

/--
Example 15.16 log-rank optimality handoff.
-/
theorem Vaart1998Example15_16LogRankOptimalSource.asymptotically_optimal
    (S : Vaart1998Example15_16LogRankOptimalSource) :
    Tendsto S.twoSampleOptimalSource.optimalTestSource.localPower atTop
      (𝓝 (vaart1998_lanEfficientPowerEnvelope
        S.twoSampleOptimalSource.optimalTestSource.normalUpperTail
        S.twoSampleOptimalSource.optimalTestSource.zAlpha
        S.twoSampleOptimalSource.optimalTestSource.directionalDerivative
        S.twoSampleOptimalSource.optimalTestSource.efficientVariance)) :=
  S.twoSampleOptimalSource.asymptotically_optimal

end AsymptoticStatistics
end StatInference
