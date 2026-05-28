import StatInference.AsymptoticStatistics.RankStatistics

/-!
# van der Vaart 1998 Chapter 14 testing interfaces

This module opens the Chapter 14 lane.  It records source-shaped interfaces
for local asymptotic power, Pitman slopes, consistency of large-value tests,
Pitman relative efficiency, and the first sign-test/Mann-Whitney examples
that consume the Chapter 12 `U`-statistic and Chapter 13 rank-statistic
frontier.
-/

noncomputable section

namespace StatInference
namespace AsymptoticStatistics

open Filter MeasureTheory ProbabilityTheory
open scoped BigOperators ENNReal ProbabilityTheory Topology

/--
Local alternatives of the form `h / sqrt n` used throughout Chapter 14.
-/
def vaart1998_localAlternative (h : ℝ) : ℕ -> ℝ :=
  fun n => h / Real.sqrt (n : ℝ)

/--
Centered and locally standardized statistic in display (14.4):
`sqrt n (T_n - mu(theta_n)) / sigma(theta_n)`.
-/
def vaart1998_localStandardizedStatistic
    {Ω : Type*} (statistic : ℕ -> Ω -> ℝ)
    (mu sigma : ℝ -> ℝ) (theta : ℕ -> ℝ) :
    ℕ -> Ω -> ℝ :=
  fun n ω =>
    Real.sqrt (n : ℝ) * (statistic n ω - mu (theta n)) /
      sigma (theta n)

/--
The large-value rejection region
`sqrt n (T_n - center) > critical`.
-/
def vaart1998_largeValueRejectionRegion
    {Ω : Type*} (statistic : ℕ -> Ω -> ℝ)
    (center critical : ℝ) : ℕ -> Set Ω :=
  fun n => {ω | critical < Real.sqrt (n : ℝ) * (statistic n ω - center)}

/--
Power of a rejection region under a sequence of laws.
-/
def vaart1998_powerFunction
    {Ω Θ : Type*} [MeasurableSpace Ω]
    (P : Θ -> ℕ -> Measure Ω) (rejectionRegion : ℕ -> Set Ω) :
    ℕ -> Θ -> ℝ :=
  fun n θ => (P θ n).real (rejectionRegion n)

/--
Local power along alternatives `h / sqrt n`.
-/
def vaart1998_localPowerFunction
    (power : ℕ -> ℝ -> ℝ) (h : ℝ) : ℕ -> ℝ :=
  fun n => power n (vaart1998_localAlternative h n)

/--
Asymptotic level at the null parameter.
-/
def Vaart1998AsymptoticLevelAt
    (power : ℕ -> ℝ -> ℝ) (alpha : ℝ) : Prop :=
  Tendsto (fun n => power n 0) atTop (𝓝 alpha)

/--
Consistency against a fixed alternative.
-/
def Vaart1998ConsistentAtAlternative
    (power : ℕ -> ℝ -> ℝ) (theta : ℝ) : Prop :=
  Tendsto (fun n => power n theta) atTop (𝓝 1)

/--
Pitman slope `mu'(0) / sigma(0)`.
-/
def vaart1998_pitmanSlope
    (muDerivativeAtZero sigmaAtZero : ℝ) : ℝ :=
  muDerivativeAtZero / sigmaAtZero

/--
The limiting local power display in (14.6):
`1 - Phi(z_alpha - h * slope)`.  The normal upper-tail function is supplied
by the caller, keeping this interface independent of a concrete normal-CDF
API.
-/
def vaart1998_localPowerLimitDisplay
    (normalUpperTail : ℝ -> ℝ) (zAlpha h slope : ℝ) : ℝ :=
  normalUpperTail (zAlpha - h * slope)

/--
Theorem 14.7 source: local asymptotic normality (14.4), differentiability of
`mu`, continuity of `sigma`, and the null critical value yield the local
power display (14.6).
-/
structure Vaart1998Theorem14_7LocalPowerSource
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    (P : ℝ -> ℕ -> Measure Ω)
    [∀ h n, IsProbabilityMeasure (P h n)]
    (LimitLaw : Measure ΩLimit) [IsProbabilityMeasure LimitLaw] where
  /-- Test statistic `T_n`. -/
  statistic : ℕ -> Ω -> ℝ
  /-- Asymptotic centering function `mu(theta)`. -/
  mu : ℝ -> ℝ
  /-- Asymptotic scale function `sigma(theta)`. -/
  sigma : ℝ -> ℝ
  /-- Derivative `mu'(0)`. -/
  muDerivativeAtZero : ℝ
  /-- Null scale `sigma(0)`. -/
  sigmaAtZero : ℝ
  /-- Critical quantile `z_alpha`. -/
  zAlpha : ℝ
  /-- Target asymptotic level. -/
  alpha : ℝ
  /-- Upper tail of the standard normal law. -/
  normalUpperTail : ℝ -> ℝ
  /-- Standard-normal limit statistic. -/
  standardNormalStatistic : ΩLimit -> ℝ
  /-- Standardized statistic for local alternative `h / sqrt n`. -/
  standardizedStatistic : ℝ -> ℕ -> Ω -> ℝ
  /-- Large-value rejection region. -/
  rejectionRegion : ℕ -> Set Ω
  /-- Power functions of the tests along arbitrary parameter values. -/
  power : ℕ -> ℝ -> ℝ
  /-- Local power along `h / sqrt n`. -/
  localPower : ℕ -> ℝ -> ℝ
  /-- Slope of the sequence of tests. -/
  slope : ℝ
  /-- Identification of the standardized statistic display. -/
  standardizedStatistic_eq :
    ∀ h,
      standardizedStatistic h =
        vaart1998_localStandardizedStatistic
          statistic mu sigma (vaart1998_localAlternative h)
  /-- Identification of the large-value rejection region. -/
  rejectionRegion_eq :
    rejectionRegion =
      vaart1998_largeValueRejectionRegion
        statistic (mu 0) (sigmaAtZero * zAlpha)
  /-- Identification of local power from the ordinary power function. -/
  localPower_eq :
    ∀ h,
      (fun n => localPower n h) =
        vaart1998_localPowerFunction power h
  /-- Null level convergence. -/
  level_tendsto_alpha :
    Vaart1998AsymptoticLevelAt power alpha
  /-- Local asymptotic normality assumption (14.4). -/
  localAsymptoticNormality :
    ∀ h,
      TendstoInDistribution (standardizedStatistic h) atTop
        standardNormalStatistic (P h) LimitLaw
  /-- Differentiability of `mu` at zero, recorded source-shaped. -/
  mu_differentiableAtZero : Prop
  /-- Continuity of `sigma` at zero, recorded source-shaped. -/
  sigma_continuousAtZero : Prop
  /-- Identification `sigmaAtZero = sigma 0`. -/
  sigmaAtZero_eq :
    sigmaAtZero = sigma 0
  /-- Slope display `mu'(0) / sigma(0)`. -/
  slope_eq :
    slope = vaart1998_pitmanSlope muDerivativeAtZero sigmaAtZero
  /-- The local power conclusion (14.6). -/
  localPower_tendsto :
    ∀ h,
      Tendsto (fun n => localPower n h) atTop
        (𝓝 (vaart1998_localPowerLimitDisplay
          normalUpperTail zAlpha h slope))
  /-- Source proof of differentiability. -/
  mu_differentiableAtZero_proof :
    mu_differentiableAtZero
  /-- Source proof of continuity. -/
  sigma_continuousAtZero_proof :
    sigma_continuousAtZero

/--
Theorem 14.7 local power display.
-/
theorem Vaart1998Theorem14_7LocalPowerSource.local_power_limit
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℝ -> ℕ -> Measure Ω}
    [∀ h n, IsProbabilityMeasure (P h n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Theorem14_7LocalPowerSource P LimitLaw)
    (h : ℝ) :
    Tendsto (fun n => S.localPower n h) atTop
      (𝓝 (vaart1998_localPowerLimitDisplay
        S.normalUpperTail S.zAlpha h S.slope)) :=
  S.localPower_tendsto h

/--
Theorem 14.7 slope display.
-/
theorem Vaart1998Theorem14_7LocalPowerSource.slope_display
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℝ -> ℕ -> Measure Ω}
    [∀ h n, IsProbabilityMeasure (P h n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Theorem14_7LocalPowerSource P LimitLaw) :
    S.slope =
      vaart1998_pitmanSlope S.muDerivativeAtZero S.sigmaAtZero :=
  S.slope_eq

/--
The sign-test slope from Example 14.8: `2 f(0)`.
-/
def vaart1998_signTestSlope (densityAtZero : ℝ) : ℝ :=
  2 * densityAtZero

/--
The one-sample `t`-test slope from Example 14.9: `1 / sigma`.
-/
def vaart1998_tTestSlope (sigma : ℝ) : ℝ :=
  sigma⁻¹

/--
Relative efficiency of the sign test with respect to the one-sample `t`-test
for a symmetric density: `4 f(0)^2 Var(X)`.
-/
def vaart1998_signVsTTestEfficiency
    (densityAtZero secondMoment : ℝ) : ℝ :=
  4 * densityAtZero ^ 2 * secondMoment

/--
Example 14.8 source: the sign test has slope `2 f(0)`.
-/
structure Vaart1998Example14_8SignTestSlopeSource
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    (P : ℝ -> ℕ -> Measure Ω)
    [∀ h n, IsProbabilityMeasure (P h n)]
    (LimitLaw : Measure ΩLimit) [IsProbabilityMeasure LimitLaw] where
  /-- Sign statistic source from Chapter 13. -/
  signStatistic : ℕ -> Ω -> ℝ
  /-- Density value `f(0)`. -/
  densityAtZero : ℝ
  /-- Theorem 14.7 local-power source for the sign statistic. -/
  localPowerSource :
    Vaart1998Theorem14_7LocalPowerSource P LimitLaw
  /-- Alignment with the statistic in Theorem 14.7. -/
  localPowerSource_statistic_eq :
    localPowerSource.statistic = signStatistic
  /-- Slope of the sign test. -/
  signSlope : ℝ
  /-- Example 14.8 slope display. -/
  signSlope_eq :
    signSlope = vaart1998_signTestSlope densityAtZero
  /-- Alignment with Theorem 14.7's slope. -/
  localPowerSource_slope_eq :
    localPowerSource.slope = signSlope

/--
Example 14.8 sign-test slope.
-/
theorem Vaart1998Example14_8SignTestSlopeSource.slope_display
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℝ -> ℕ -> Measure Ω}
    [∀ h n, IsProbabilityMeasure (P h n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Example14_8SignTestSlopeSource P LimitLaw) :
    S.signSlope = vaart1998_signTestSlope S.densityAtZero :=
  S.signSlope_eq

/--
The local power limit for the sign test, inherited from Theorem 14.7.
-/
theorem Vaart1998Example14_8SignTestSlopeSource.local_power_limit
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℝ -> ℕ -> Measure Ω}
    [∀ h n, IsProbabilityMeasure (P h n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Example14_8SignTestSlopeSource P LimitLaw)
    (h : ℝ) :
    Tendsto (fun n => S.localPowerSource.localPower n h) atTop
      (𝓝 (vaart1998_localPowerLimitDisplay
        S.localPowerSource.normalUpperTail S.localPowerSource.zAlpha
        h S.signSlope)) := by
  have hlim := S.localPowerSource.local_power_limit h
  simpa [S.localPowerSource_slope_eq] using hlim

/--
Example 14.10 source: comparison of sign and `t` slopes.
-/
structure Vaart1998Example14_10SignVsTSource where
  /-- Density value `f(0)`. -/
  densityAtZero : ℝ
  /-- Second moment `int x^2 f(x) dx`. -/
  secondMoment : ℝ
  /-- Sign-test slope. -/
  signSlope : ℝ
  /-- `t`-test slope. -/
  tSlope : ℝ
  /-- Relative efficiency sign/`t`. -/
  relativeEfficiency : ℝ
  /-- Sign slope display. -/
  signSlope_eq :
    signSlope = vaart1998_signTestSlope densityAtZero
  /-- `t` slope display. -/
  tSlope_eq :
    tSlope = vaart1998_tTestSlope (Real.sqrt secondMoment)
  /-- Relative-efficiency display from Example 14.10. -/
  relativeEfficiency_eq :
    relativeEfficiency =
      vaart1998_signVsTTestEfficiency densityAtZero secondMoment

/--
Example 14.10 relative-efficiency display.
-/
theorem Vaart1998Example14_10SignVsTSource.relative_efficiency_display
    (S : Vaart1998Example14_10SignVsTSource) :
    S.relativeEfficiency =
      vaart1998_signVsTTestEfficiency
        S.densityAtZero S.secondMoment :=
  S.relativeEfficiency_eq

/--
Mann-Whitney slope from Example 14.11:
`int g dF / sigma(0)`.
-/
def vaart1998_mannWhitneySlope
    (integral_g_dF sigmaAtZero : ℝ) : ℝ :=
  integral_g_dF / sigmaAtZero

/--
Asymptotic variance display for the Mann-Whitney statistic in Example 14.11:
`Var G(X - theta) / lambda + Var F(Y) / (1 - lambda)`.
-/
def vaart1998_mannWhitneyAsymptoticVariance
    (lambda varGX varFY : ℝ) : ℝ :=
  varGX / lambda + varFY / (1 - lambda)

/--
Relative efficiency of Mann-Whitney with respect to the two-sample `t`-test
from Example 14.13.
-/
def vaart1998_mannWhitneyVsTwoSampleTEfficiency
    (lambda varX varY varGofX varFofY integral_g_dF : ℝ) : ℝ :=
  (((1 - lambda) * varX + lambda * varY) * integral_g_dF ^ 2) /
    ((1 - lambda) * varGofX + lambda * varFofY)

/--
Equal-distribution simplification in Example 14.13:
`12 Var(X) (int f^2)^2`.
-/
def vaart1998_mannWhitneyVsTwoSampleTEfficiencyIdentical
    (variance integral_f_sq : ℝ) : ℝ :=
  12 * variance * integral_f_sq ^ 2

/--
Example 14.11 source: the Mann-Whitney test slope is inherited from the
Chapter 12 two-sample `U`-statistic theorem.
-/
structure Vaart1998Example14_11MannWhitneySlopeSource
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    (P : ℕ -> Measure Ω) [∀ n, IsProbabilityMeasure (P n)]
    (LimitLaw : Measure ΩLimit) [IsProbabilityMeasure LimitLaw] where
  /-- Chapter 12 two-sample `U`-statistic projection source. -/
  twoSampleUSource :
    Vaart1998Theorem12_6TwoSampleProjectionMethodSource P LimitLaw
  /-- Chapter 13 Wilcoxon/Mann-Whitney asymptotic-normality bridge. -/
  wilcoxonBridge :
    Vaart1998WilcoxonAsymptoticNormalitySource P LimitLaw
  /-- Alignment of the bridge with the two-sample `U`-statistic source. -/
  wilcoxonBridge_source_eq :
    wilcoxonBridge.mannWhitneyProjectionSource = twoSampleUSource
  /-- Sample-share limit `lambda`. -/
  lambda : ℝ
  /-- Variance of `G(X - theta)` at the relevant parameter. -/
  varGX : ℝ
  /-- Variance of `F(Y)`. -/
  varFY : ℝ
  /-- Displayed `int g dF`. -/
  integral_g_dF : ℝ
  /-- Null standard deviation `sigma(0)`. -/
  sigmaAtZero : ℝ
  /-- Mann-Whitney slope. -/
  slope : ℝ
  /-- Variance display from Example 14.11. -/
  sigmaSq_eq :
    sigmaAtZero ^ 2 =
      vaart1998_mannWhitneyAsymptoticVariance lambda varGX varFY
  /-- Slope display from Example 14.11. -/
  slope_eq :
    slope =
      vaart1998_mannWhitneySlope integral_g_dF sigmaAtZero
  /-- Local asymptotic normality under `theta_N = h / sqrt N`. -/
  localAsymptoticNormality : Prop
  /-- Source proof of local asymptotic normality. -/
  localAsymptoticNormality_proof :
    localAsymptoticNormality

/--
Example 14.11 Mann-Whitney slope display.
-/
theorem Vaart1998Example14_11MannWhitneySlopeSource.slope_display
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Example14_11MannWhitneySlopeSource P LimitLaw) :
    S.slope =
      vaart1998_mannWhitneySlope S.integral_g_dF S.sigmaAtZero :=
  S.slope_eq

/--
The Mann-Whitney statistic inherits the Chapter 12/13 weak limit bridge.
-/
theorem Vaart1998Example14_11MannWhitneySlopeSource.mannWhitney_limit
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Example14_11MannWhitneySlopeSource P LimitLaw) :
    TendstoInDistribution S.wilcoxonBridge.scaledMannWhitneyStatistic atTop
      S.twoSampleUSource.projectionMethodSource.limitStatistic
      P LimitLaw := by
  have hlim := S.wilcoxonBridge.mannWhitney_tendstoInDistribution
  simpa [S.wilcoxonBridge_source_eq] using hlim

/--
Example 14.13 source: relative efficiency of Mann-Whitney versus the
two-sample `t`-test.
-/
structure Vaart1998Example14_13MannWhitneyVsTSource where
  /-- Sample-share limit `lambda`. -/
  lambda : ℝ
  /-- Variance of the first sample. -/
  varX : ℝ
  /-- Variance of the second sample. -/
  varY : ℝ
  /-- Variance of `G(X)`. -/
  varGofX : ℝ
  /-- Variance of `F(Y)`. -/
  varFofY : ℝ
  /-- Displayed `int g dF`. -/
  integral_g_dF : ℝ
  /-- Mann-Whitney slope. -/
  mannWhitneySlope : ℝ
  /-- Two-sample `t` slope. -/
  twoSampleTSlope : ℝ
  /-- Relative efficiency Mann-Whitney/`t`. -/
  relativeEfficiency : ℝ
  /-- Slope comparison source. -/
  slopeComparison : Prop
  /-- Relative-efficiency display from Example 14.13. -/
  relativeEfficiency_eq :
    relativeEfficiency =
      vaart1998_mannWhitneyVsTwoSampleTEfficiency
        lambda varX varY varGofX varFofY integral_g_dF
  /-- Source proof of the slope comparison. -/
  slopeComparison_proof :
    slopeComparison

/--
Example 14.13 relative-efficiency display.
-/
theorem Vaart1998Example14_13MannWhitneyVsTSource.relative_efficiency_display
    (S : Vaart1998Example14_13MannWhitneyVsTSource) :
    S.relativeEfficiency =
      vaart1998_mannWhitneyVsTwoSampleTEfficiency
        S.lambda S.varX S.varY S.varGofX S.varFofY
        S.integral_g_dF :=
  S.relativeEfficiency_eq

/--
Lemma 14.15 source: convergence in probability of a statistic to a separated
limit implies consistency of large-value tests.
-/
structure Vaart1998Lemma14_15ConsistencySource where
  /-- Power functions of the tests. -/
  power : ℕ -> ℝ -> ℝ
  /-- Limiting statistic mean/target. -/
  mu : ℝ -> ℝ
  /-- Alternative parameter. -/
  theta : ℝ
  /-- Target asymptotic level. -/
  alpha : ℝ
  /-- The tests are asymptotically of level `alpha`. -/
  level_at_null :
    Vaart1998AsymptoticLevelAt power alpha
  /-- Statistic convergence under each fixed parameter. -/
  statistic_tendsto_mu : Prop
  /-- Separation `mu(theta) > mu(0)`. -/
  separated_mean :
    mu 0 < mu theta
  /-- Consistency conclusion. -/
  consistent :
    Vaart1998ConsistentAtAlternative power theta

/--
Lemma 14.15 consistency conclusion.
-/
theorem Vaart1998Lemma14_15ConsistencySource.consistent_at_alternative
    (S : Vaart1998Lemma14_15ConsistencySource) :
    Vaart1998ConsistentAtAlternative S.power S.theta :=
  S.consistent

/--
Lemma 14.16 source: monotone power plus the local-power theorem yields
consistency and the two extreme local-rate conclusions.
-/
structure Vaart1998Lemma14_16MonotonePowerConsistencySource where
  /-- Power functions of the tests. -/
  power : ℕ -> ℝ -> ℝ
  /-- Target level. -/
  alpha : ℝ
  /-- Alternative parameter. -/
  theta : ℝ
  /-- Pitman slope. -/
  slope : ℝ
  /-- Positive slope side condition. -/
  slope_pos : 0 < slope
  /-- Monotonicity of the power functions in the parameter. -/
  nondecreasingPower : Prop
  /-- Local asymptotic power display from Theorem 14.7. -/
  localPowerLimit : Prop
  /-- Asymptotic level at zero. -/
  level_at_null :
    Vaart1998AsymptoticLevelAt power alpha
  /-- Consistency at every fixed positive alternative. -/
  consistent :
    0 < theta -> Vaart1998ConsistentAtAlternative power theta
  /-- If `sqrt n theta_n -> 0`, power tends to level. -/
  smallLocalAlternatives_tendsto_level : Prop
  /-- If `sqrt n theta_n -> infinity`, power tends to one. -/
  largeLocalAlternatives_tendsto_one : Prop
  /-- Source proof of monotonicity. -/
  nondecreasingPower_proof :
    nondecreasingPower
  /-- Source proof of the local-power limit. -/
  localPowerLimit_proof :
    localPowerLimit
  /-- Source proof for the small-local-alternative conclusion. -/
  smallLocalAlternatives_tendsto_level_proof :
    smallLocalAlternatives_tendsto_level
  /-- Source proof for the large-local-alternative conclusion. -/
  largeLocalAlternatives_tendsto_one_proof :
    largeLocalAlternatives_tendsto_one

/--
Lemma 14.16 consistency at fixed positive alternatives.
-/
theorem Vaart1998Lemma14_16MonotonePowerConsistencySource.consistent_at_positive
    (S : Vaart1998Lemma14_16MonotonePowerConsistencySource)
    (hθ : 0 < S.theta) :
    Vaart1998ConsistentAtAlternative S.power S.theta :=
  S.consistent hθ

/--
Pitman relative efficiency: square of the quotient of slopes.
-/
def vaart1998_pitmanRelativeEfficiency
    (slope₁ slope₂ : ℝ) : ℝ :=
  (slope₁ / slope₂) ^ 2

/--
Theorem 14.19 source: under local asymptotic normality and regularity, the
Pitman relative efficiency is the square of the slope quotient.
-/
structure Vaart1998Theorem14_19PitmanEfficiencySource where
  /-- First test slope. -/
  slope₁ : ℝ
  /-- Second test slope. -/
  slope₂ : ℝ
  /-- Relative efficiency of test 1 with respect to test 2. -/
  relativeEfficiency : ℝ
  /-- Local total-variation collapse side condition. -/
  totalVariationLocalCollapse : Prop
  /-- Local asymptotic normality and differentiability for test 1. -/
  firstLocalAsymptoticNormality : Prop
  /-- Local asymptotic normality and differentiability for test 2. -/
  secondLocalAsymptoticNormality : Prop
  /-- Positive slopes side condition. -/
  positiveSlopes : 0 < slope₁ ∧ 0 < slope₂
  /-- Independence from `alpha`, `gamma`, and alternative sequence. -/
  independentOfLevelPowerAndAlternatives : Prop
  /-- Relative-efficiency display. -/
  relativeEfficiency_eq :
    relativeEfficiency =
      vaart1998_pitmanRelativeEfficiency slope₁ slope₂
  /-- Source proof of local total-variation collapse. -/
  totalVariationLocalCollapse_proof :
    totalVariationLocalCollapse
  /-- Source proof for test 1. -/
  firstLocalAsymptoticNormality_proof :
    firstLocalAsymptoticNormality
  /-- Source proof for test 2. -/
  secondLocalAsymptoticNormality_proof :
    secondLocalAsymptoticNormality
  /-- Source proof of independence from nuisance choices. -/
  independentOfLevelPowerAndAlternatives_proof :
    independentOfLevelPowerAndAlternatives

/--
Theorem 14.19 relative-efficiency display.
-/
theorem Vaart1998Theorem14_19PitmanEfficiencySource.relative_efficiency_display
    (S : Vaart1998Theorem14_19PitmanEfficiencySource) :
    S.relativeEfficiency =
      vaart1998_pitmanRelativeEfficiency S.slope₁ S.slope₂ :=
  S.relativeEfficiency_eq

/--
Observed-significance large-deviation exponent from (14.20).
-/
def vaart1998_bahadurTailExponent
    (tailProbability : ℕ -> ℝ) : ℕ -> ℝ :=
  fun n => - (2 / (n : ℝ)) * Real.log (tailProbability n)

/--
Bahadur relative efficiency: quotient of Bahadur slopes.
-/
def vaart1998_bahadurRelativeEfficiency
    (slope₁ slope₂ : ℝ) : ℝ :=
  slope₁ / slope₂

/--
Theorem 14.22 source: large-deviation tail exponents plus LLN limits yield
Bahadur relative efficiency as a quotient of slopes.
-/
structure Vaart1998Theorem14_22BahadurEfficiencySource where
  /-- First Bahadur slope `e_1(mu_1(theta))`. -/
  bahadurSlope₁ : ℝ
  /-- Second Bahadur slope `e_2(mu_2(theta))`. -/
  bahadurSlope₂ : ℝ
  /-- Bahadur relative efficiency. -/
  relativeEfficiency : ℝ
  /-- Large-deviation display (14.20) for the first statistic. -/
  firstLargeDeviation : Prop
  /-- Large-deviation display (14.20) for the second statistic. -/
  secondLargeDeviation : Prop
  /-- LLN display (14.21) for the first statistic. -/
  firstLawOfLargeNumbers : Prop
  /-- LLN display (14.21) for the second statistic. -/
  secondLawOfLargeNumbers : Prop
  /-- Continuity of the two exponent functions at their alternative limits. -/
  exponentContinuity : Prop
  /-- Relative-efficiency display. -/
  relativeEfficiency_eq :
    relativeEfficiency =
      vaart1998_bahadurRelativeEfficiency bahadurSlope₁ bahadurSlope₂
  /-- Source proof of the first large-deviation display. -/
  firstLargeDeviation_proof :
    firstLargeDeviation
  /-- Source proof of the second large-deviation display. -/
  secondLargeDeviation_proof :
    secondLargeDeviation
  /-- Source proof of the first LLN display. -/
  firstLawOfLargeNumbers_proof :
    firstLawOfLargeNumbers
  /-- Source proof of the second LLN display. -/
  secondLawOfLargeNumbers_proof :
    secondLawOfLargeNumbers
  /-- Source proof of exponent continuity. -/
  exponentContinuity_proof :
    exponentContinuity

/--
Theorem 14.22 Bahadur relative-efficiency display.
-/
theorem Vaart1998Theorem14_22BahadurEfficiencySource.relative_efficiency_display
    (S : Vaart1998Theorem14_22BahadurEfficiencySource) :
    S.relativeEfficiency =
      vaart1998_bahadurRelativeEfficiency
        S.bahadurSlope₁ S.bahadurSlope₂ :=
  S.relativeEfficiency_eq

/--
Cumulant-generating function used in the Cramer-Chernoff theorem.
-/
def vaart1998_cumulantGeneratingFunction
    {Ω : Type*} [MeasurableSpace Ω] (P : Measure Ω) (Y : Ω -> ℝ)
    (u : ℝ) : ℝ :=
  Real.log (∫ ω, Real.exp (u * Y ω) ∂P)

/--
The Cramer-Chernoff rate display
`inf_{u >= 0} (K(u) - t u)` from Theorem 14.23.
-/
def vaart1998_cramerChernoffRate
    (K : ℝ -> ℝ) (t : ℝ) : ℝ :=
  sInf {r : ℝ | ∃ u : ℝ, 0 ≤ u ∧ r = K u - t * u}

/--
Logarithmic tail scale in Theorem 14.23.
-/
def vaart1998_cramerChernoffExponent
    (tailProbability : ℕ -> ℝ) : ℕ -> ℝ :=
  fun n => (n : ℝ)⁻¹ * Real.log (tailProbability n)

/--
Theorem 14.23 source: Cramer-Chernoff large deviations for sample means.
-/
structure Vaart1998Theorem14_23CramerChernoffSource where
  /-- Cumulant-generating function `K`. -/
  cumulantGeneratingFunction : ℝ -> ℝ
  /-- Threshold `t`. -/
  threshold : ℝ
  /-- Tail probabilities `P(\bar Y_n >= t)`. -/
  tailProbability : ℕ -> ℝ
  /-- Rate `inf_{u >= 0} (K(u) - t u)`. -/
  rate : ℝ
  /-- Logarithmic exponent sequence. -/
  exponent : ℕ -> ℝ
  /-- Identification of the displayed rate. -/
  rate_eq :
    rate =
      vaart1998_cramerChernoffRate cumulantGeneratingFunction threshold
  /-- Identification of the logarithmic tail scale. -/
  exponent_eq :
    exponent = vaart1998_cramerChernoffExponent tailProbability
  /-- The Cramer-Chernoff logarithmic limit. -/
  tail_log_tendsto_rate :
    Tendsto exponent atTop (𝓝 rate)

/--
Theorem 14.23 logarithmic tail limit.
-/
theorem Vaart1998Theorem14_23CramerChernoffSource.tail_log_limit
    (S : Vaart1998Theorem14_23CramerChernoffSource) :
    Tendsto S.exponent atTop (𝓝 S.rate) :=
  S.tail_log_tendsto_rate

/--
Theorem 14.23 rate display.
-/
theorem Vaart1998Theorem14_23CramerChernoffSource.rate_display
    (S : Vaart1998Theorem14_23CramerChernoffSource) :
    S.rate =
      vaart1998_cramerChernoffRate
        S.cumulantGeneratingFunction S.threshold :=
  S.rate_eq

/--
Example 14.24 sign-statistic Bahadur exponent.  The hyperbolic cosine and
inverse hyperbolic tangent are supplied by the caller so the source can reuse
whichever concrete API the eventual distribution instance imports.
-/
def vaart1998_signBahadurExponent
    (cosh atanh : ℝ -> ℝ) (t : ℝ) : ℝ :=
  -2 * Real.log (cosh (atanh t)) + 2 * t * (atanh t)

/--
Example 14.24 source: the sign-statistic large-deviation calculation.
-/
structure Vaart1998Example14_24SignBahadurSource where
  /-- Chosen hyperbolic-cosine function. -/
  cosh : ℝ -> ℝ
  /-- Chosen inverse hyperbolic tangent. -/
  atanh : ℝ -> ℝ
  /-- Sign-statistic threshold. -/
  threshold : ℝ
  /-- Tail probabilities of the sign statistic. -/
  tailProbability : ℕ -> ℝ
  /-- Bahadur exponent for the sign statistic. -/
  exponent : ℝ
  /-- Cramer-Chernoff source used to derive the exponent. -/
  cramerChernoffSource :
    Vaart1998Theorem14_23CramerChernoffSource
  /-- Bahadur-efficiency source consuming the exponent. -/
  bahadurSource :
    Vaart1998Theorem14_22BahadurEfficiencySource
  /-- Exponent display from Example 14.24. -/
  exponent_eq :
    exponent =
      vaart1998_signBahadurExponent cosh atanh threshold

/--
Example 14.24 exponent display.
-/
theorem Vaart1998Example14_24SignBahadurSource.exponent_display
    (S : Vaart1998Example14_24SignBahadurSource) :
    S.exponent =
      vaart1998_signBahadurExponent S.cosh S.atanh S.threshold :=
  S.exponent_eq

/--
Bahadur slope of the sample mean in Example 14.25.
-/
def vaart1998_normalMeanBahadurSlope
    (mu sigma : ℝ) : ℝ :=
  mu ^ 2 / sigma ^ 2

/--
Bahadur slope of Student's statistic in Example 14.25.
-/
def vaart1998_studentBahadurSlope
    (mu sigma : ℝ) : ℝ :=
  Real.log (1 + mu ^ 2 / sigma ^ 2)

/--
Example 14.25 source: Bahadur slopes for the sample mean and Student statistic.
-/
structure Vaart1998Example14_25StudentBahadurSource where
  /-- Mean shift under the alternative. -/
  mu : ℝ
  /-- Standard deviation under the alternative. -/
  sigma : ℝ
  /-- Sample-mean Bahadur slope. -/
  sampleMeanSlope : ℝ
  /-- Student-statistic Bahadur slope. -/
  studentSlope : ℝ
  /-- Sample-mean large-deviation source. -/
  sampleMeanLargeDeviation :
    Vaart1998Theorem14_23CramerChernoffSource
  /-- Student-statistic large-deviation source. -/
  studentLargeDeviation :
    Vaart1998Theorem14_23CramerChernoffSource
  /-- Sample-mean slope display. -/
  sampleMeanSlope_eq :
    sampleMeanSlope = vaart1998_normalMeanBahadurSlope mu sigma
  /-- Student-statistic slope display. -/
  studentSlope_eq :
    studentSlope = vaart1998_studentBahadurSlope mu sigma

/--
Example 14.25 Student-statistic slope display.
-/
theorem Vaart1998Example14_25StudentBahadurSource.student_slope_display
    (S : Vaart1998Example14_25StudentBahadurSource) :
    S.studentSlope =
      vaart1998_studentBahadurSlope S.mu S.sigma :=
  S.studentSlope_eq

/--
Bahadur slope of the Neyman-Pearson statistic in Example 14.26:
twice the Kullback-Leibler divergence.
-/
def vaart1998_neymanPearsonBahadurSlope
    (kullbackLeiblerDivergence : ℝ) : ℝ :=
  2 * kullbackLeiblerDivergence

/--
Example 14.26 source: the Neyman-Pearson statistic has Bahadur slope
`2 * KL(P_theta, P_theta0)`.
-/
structure Vaart1998Example14_26NeymanPearsonBahadurSource where
  /-- Kullback-Leibler divergence from the alternative to the null. -/
  kullbackLeiblerDivergence : ℝ
  /-- Neyman-Pearson Bahadur slope. -/
  bahadurSlope : ℝ
  /-- Likelihood-ratio source display. -/
  likelihoodRatioSource : Prop
  /-- Bahadur-efficiency source. -/
  bahadurSource :
    Vaart1998Theorem14_22BahadurEfficiencySource
  /-- Bahadur slope display. -/
  bahadurSlope_eq :
    bahadurSlope =
      vaart1998_neymanPearsonBahadurSlope kullbackLeiblerDivergence
  /-- Source proof of the likelihood-ratio display. -/
  likelihoodRatioSource_proof :
    likelihoodRatioSource

/--
Example 14.26 Bahadur-slope display.
-/
theorem Vaart1998Example14_26NeymanPearsonBahadurSource.slope_display
    (S : Vaart1998Example14_26NeymanPearsonBahadurSource) :
    S.bahadurSlope =
      vaart1998_neymanPearsonBahadurSlope
        S.kullbackLeiblerDivergence :=
  S.bahadurSlope_eq

/--
Infimum of a rate function over a set, used in the large-deviation
contraction lemma.
-/
def vaart1998_rateInf
    {D : Type*} (rate : D -> ℝ) (A : Set D) : ℝ :=
  sInf (rate '' A)

/--
The transformed exponent in Lemma 14.27:
`2 * inf {I(y) : phi(y) >= t}`.
-/
def vaart1998_largeDeviationTransformExponent
    {D : Type*} (rate : D -> ℝ) (phi : D -> ℝ) (t : ℝ) : ℝ :=
  2 * vaart1998_rateInf rate {y | t ≤ phi y}

/--
Source-shaped large-deviation principle with closed-set upper and open-set
lower bounds.  The two bounds are kept as reusable proposition-valued fields
so later packets can instantiate them with whichever topology and
probability-of-set API is available.
-/
structure Vaart1998LargeDeviationPrincipleSource
    {Ω D : Type*} [MeasurableSpace Ω] [TopologicalSpace D]
    (P : ℕ -> Measure Ω) (X : ℕ -> Ω -> D) (rate : D -> ℝ) where
  /-- Closed-set upper bound of the LDP. -/
  closedUpperBound : ∀ F : Set D, IsClosed F -> Prop
  /-- Open-set lower bound of the LDP. -/
  openLowerBound : ∀ G : Set D, IsOpen G -> Prop
  /-- Source proof of the closed-set upper bound. -/
  closedUpperBound_proof :
    ∀ F hF, closedUpperBound F hF
  /-- Source proof of the open-set lower bound. -/
  openLowerBound_proof :
    ∀ G hG, openLowerBound G hG

/--
Lemma 14.27 source: continuous maps transport an LDP to a one-dimensional
large-deviation exponent for tail probabilities.
-/
structure Vaart1998Lemma14_27LargeDeviationTransformSource
    {Ω D : Type*} [MeasurableSpace Ω] [TopologicalSpace D]
    (P : ℕ -> Measure Ω) (X : ℕ -> Ω -> D) where
  /-- Rate function `I`. -/
  rate : D -> ℝ
  /-- Continuous functional `phi`. -/
  statisticMap : D -> ℝ
  /-- Threshold `t`. -/
  threshold : ℝ
  /-- Transformed statistic `phi(X_n)`. -/
  transformedStatistic : ℕ -> Ω -> ℝ
  /-- Tail probabilities for `phi(X_n)`. -/
  tailProbability : ℕ -> ℝ
  /-- Logarithmic Bahadur exponent sequence. -/
  tailExponent : ℕ -> ℝ
  /-- Limit exponent. -/
  exponentLimit : ℝ
  /-- LDP source for `X_n`. -/
  ldpSource :
    Vaart1998LargeDeviationPrincipleSource P X rate
  /-- Identification of the transformed statistic. -/
  transformedStatistic_eq :
    transformedStatistic = fun n ω => statisticMap (X n ω)
  /-- Continuity of `phi` at finite-rate points. -/
  continuousAtFiniteRatePoints : Prop
  /-- Boundary equality assumption in Lemma 14.27. -/
  boundaryInfEquality : Prop
  /-- Good-rate side condition for continuity of `e` at `t`. -/
  goodRateFunction : Prop
  /-- Identification of the exponent limit. -/
  exponentLimit_eq :
    exponentLimit =
      vaart1998_largeDeviationTransformExponent
        rate statisticMap threshold
  /-- Tail-exponent convergence. -/
  tailExponent_tendsto :
    Tendsto tailExponent atTop (𝓝 exponentLimit)
  /-- Continuity of the resulting exponent at the threshold. -/
  exponent_continuous_at_threshold : Prop
  /-- Source proof of continuity at finite-rate points. -/
  continuousAtFiniteRatePoints_proof :
    continuousAtFiniteRatePoints
  /-- Source proof of boundary equality. -/
  boundaryInfEquality_proof :
    boundaryInfEquality
  /-- Source proof of good-rate side condition. -/
  goodRateFunction_proof :
    goodRateFunction
  /-- Source proof of exponent continuity at the threshold. -/
  exponent_continuous_at_threshold_proof :
    exponent_continuous_at_threshold

/--
Lemma 14.27 tail-exponent convergence.
-/
theorem Vaart1998Lemma14_27LargeDeviationTransformSource.tail_exponent_tendsto
    {Ω D : Type*} [MeasurableSpace Ω] [TopologicalSpace D]
    {P : ℕ -> Measure Ω} {X : ℕ -> Ω -> D}
    (S : Vaart1998Lemma14_27LargeDeviationTransformSource P X) :
    Tendsto S.tailExponent atTop (𝓝 S.exponentLimit) :=
  S.tailExponent_tendsto

/--
Theorem 14.28 source: Sanov's theorem for empirical measures in the
`tau`-topology with relative-entropy rate.
-/
structure Vaart1998Theorem14_28SanovSource
    {Sample EmpiricalLaw : Type*} [MeasurableSpace Sample]
    [TopologicalSpace EmpiricalLaw] where
  /-- Laws of the sample vectors. -/
  sampleLaws : ℕ -> Measure Sample
  /-- Empirical-measure map. -/
  empiricalMeasure : ℕ -> Sample -> EmpiricalLaw
  /-- Relative-entropy rate function. -/
  relativeEntropyRate : EmpiricalLaw -> ℝ
  /-- Source record that the topology is the `tau`-topology. -/
  tauTopologySource : Prop
  /-- Good-rate-function source proof. -/
  goodRateFunction : Prop
  /-- LDP source supplied by Sanov's theorem. -/
  ldpSource :
    Vaart1998LargeDeviationPrincipleSource
      sampleLaws empiricalMeasure relativeEntropyRate
  /-- Source proof of the `tau`-topology identification. -/
  tauTopologySource_proof :
    tauTopologySource
  /-- Source proof that the relative-entropy rate is good. -/
  goodRateFunction_proof :
    goodRateFunction

/--
Theorem 14.28 large-deviation source.
-/
def Vaart1998Theorem14_28SanovSource.large_deviation_source
    {Sample EmpiricalLaw : Type*} [MeasurableSpace Sample]
    [TopologicalSpace EmpiricalLaw]
    (S : Vaart1998Theorem14_28SanovSource
      (Sample := Sample) (EmpiricalLaw := EmpiricalLaw)) :
    Vaart1998LargeDeviationPrincipleSource
      S.sampleLaws S.empiricalMeasure S.relativeEntropyRate :=
  S.ldpSource

/--
Example 14.29 source: trimmed means as continuous transforms of empirical
measures, using Sanov plus Lemma 14.27.
-/
structure Vaart1998Example14_29TrimmedMeanBahadurSource
    {Sample EmpiricalLaw : Type*} [MeasurableSpace Sample]
    [TopologicalSpace EmpiricalLaw] where
  /-- Laws of the sample vectors. -/
  sampleLaws : ℕ -> Measure Sample
  /-- Empirical-measure map. -/
  empiricalMeasure : ℕ -> Sample -> EmpiricalLaw
  /-- Trimmed-mean functional. -/
  trimmedMeanFunctional : EmpiricalLaw -> ℝ
  /-- Threshold. -/
  threshold : ℝ
  /-- Tail-exponent limit. -/
  bahadurExponent : ℝ
  /-- Sanov source. -/
  sanovSource :
    Vaart1998Theorem14_28SanovSource
      (Sample := Sample) (EmpiricalLaw := EmpiricalLaw)
  /-- Lemma 14.27 transform source. -/
  transformSource :
    Vaart1998Lemma14_27LargeDeviationTransformSource
      sampleLaws empiricalMeasure
  /-- Identification of the transform map. -/
  transformMap_eq :
    transformSource.statisticMap = trimmedMeanFunctional
  /-- Identification of the threshold. -/
  transformThreshold_eq :
    transformSource.threshold = threshold
  /-- Identification of the Bahadur exponent. -/
  bahadurExponent_eq :
    bahadurExponent = transformSource.exponentLimit

/--
Example 14.29 Bahadur-exponent display for trimmed means.
-/
theorem Vaart1998Example14_29TrimmedMeanBahadurSource.exponent_display
    {Sample EmpiricalLaw : Type*} [MeasurableSpace Sample]
    [TopologicalSpace EmpiricalLaw]
    (S : Vaart1998Example14_29TrimmedMeanBahadurSource
      (Sample := Sample) (EmpiricalLaw := EmpiricalLaw)) :
    S.bahadurExponent = S.transformSource.exponentLimit :=
  S.bahadurExponent_eq

/--
Total-variation distance when both laws are represented by densities with
respect to a common dominating measure, using van der Vaart's Chapter 14
normalization.
-/
def vaart1998_totalVariationFromDensity
    {Ω : Type*} [MeasurableSpace Ω] (μ : Measure Ω)
    (p q : Ω -> ℝ) : ℝ :=
  ∫ ω, |p ω - q ω| ∂μ

/--
Hellinger affinity from square-root densities.
-/
def vaart1998_hellingerAffinityFromSqrtDensities
    {Ω : Type*} [MeasurableSpace Ω] (μ : Measure Ω)
    (sqrtP sqrtQ : Ω -> ℝ) : ℝ :=
  ∫ ω, sqrtP ω * sqrtQ ω ∂μ

/--
Squared Hellinger distance from affinity:
`H^2(P,Q) = 2 - 2 A(P,Q)`.
-/
def vaart1998_squaredHellingerFromAffinity
    (affinity : ℝ) : ℝ :=
  2 - 2 * affinity

/--
Product formula for squared Hellinger distance:
`H^2(P^n,Q^n) = 2 - 2 * (1 - H^2(P,Q) / 2)^n`.
-/
def vaart1998_squaredHellingerProduct
    (n : ℕ) (singleSquaredHellinger : ℝ) : ℝ :=
  2 - 2 * (1 - singleSquaredHellinger / 2) ^ n

/--
Lemma 14.30 source: the difference between powers is bounded by one half of
the total-variation distance, and equality is attainable by a suitable test.
-/
structure Vaart1998Lemma14_30TotalVariationPowerSource where
  /-- Power functions. -/
  power : ℕ -> ℝ -> ℝ
  /-- Sample size. -/
  sampleSize : ℕ
  /-- Alternative parameter. -/
  theta : ℝ
  /-- Null parameter. -/
  theta0 : ℝ
  /-- Total-variation distance between the two laws. -/
  totalVariation : ℝ
  /-- Power-difference bound. -/
  powerDifferenceBound :
    power sampleSize theta - power sampleSize theta0 ≤
      totalVariation / 2
  /-- Existence of an attaining test. -/
  attainingTestExists : Prop
  /-- Source proof that the attaining test exists. -/
  attainingTestExists_proof :
    attainingTestExists

/--
Lemma 14.30 total-variation power bound.
-/
theorem Vaart1998Lemma14_30TotalVariationPowerSource.power_difference_bound
    (S : Vaart1998Lemma14_30TotalVariationPowerSource) :
    S.power S.sampleSize S.theta - S.power S.sampleSize S.theta0 ≤
      S.totalVariation / 2 :=
  S.powerDifferenceBound

/--
Source for the product formula connecting affinity and Hellinger distance.
-/
structure Vaart1998HellingerProductFormulaSource where
  /-- One-sample Hellinger affinity. -/
  singleAffinity : ℝ
  /-- One-sample squared Hellinger distance. -/
  singleSquaredHellinger : ℝ
  /-- Sample size. -/
  sampleSize : ℕ
  /-- Product squared Hellinger distance. -/
  productSquaredHellinger : ℝ
  /-- One-sample identity `H^2 = 2 - 2A`. -/
  singleSquaredHellinger_eq :
    singleSquaredHellinger =
      vaart1998_squaredHellingerFromAffinity singleAffinity
  /-- Product formula. -/
  productSquaredHellinger_eq :
    productSquaredHellinger =
      vaart1998_squaredHellingerProduct
        sampleSize singleSquaredHellinger

/--
Hellinger product formula display.
-/
theorem Vaart1998HellingerProductFormulaSource.product_display
    (S : Vaart1998HellingerProductFormulaSource) :
    S.productSquaredHellinger =
      vaart1998_squaredHellingerProduct
        S.sampleSize S.singleSquaredHellinger :=
  S.productSquaredHellinger_eq

/--
Lemma 14.31 source: the three testing regimes are determined by the size of
`n * H^2(P_{theta_n}, P_{theta0})`.
-/
structure Vaart1998Lemma14_31HellingerRescalingSource where
  /-- One-observation squared Hellinger distances along alternatives. -/
  singleSquaredHellinger : ℕ -> ℝ
  /-- Product squared Hellinger distances. -/
  productSquaredHellinger : ℕ -> ℝ
  /-- The product formula for each `n`. -/
  productFormula :
    ∀ n,
      productSquaredHellinger n =
        vaart1998_squaredHellingerProduct n
          (singleSquaredHellinger n)
  /-- Divergent `n H^2` regime gives asymptotically perfect tests. -/
  divergentRegimePerfectTests : Prop
  /-- Vanishing `n H^2` regime gives asymptotically powerless tests. -/
  vanishingRegimeWorthlessTests : Prop
  /-- Bounded-away/intermediate `n H^2` regime. -/
  intermediateRegime : Prop
  /-- Order source `H^2(P_theta,P_theta0) = O(|theta-theta0|^alpha)`. -/
  hellingerOrder : Prop
  /-- Rate exponent `alpha`. -/
  rateExponent : ℝ
  /-- Intermediate rate, typically `n^(1/alpha) |theta_n-theta0|`. -/
  intermediateRate : ℕ -> ℝ
  /-- Source proof for the divergent regime. -/
  divergentRegimePerfectTests_proof :
    divergentRegimePerfectTests
  /-- Source proof for the vanishing regime. -/
  vanishingRegimeWorthlessTests_proof :
    vanishingRegimeWorthlessTests
  /-- Source proof for the intermediate regime. -/
  intermediateRegime_proof :
    intermediateRegime
  /-- Source proof of the order display. -/
  hellingerOrder_proof :
    hellingerOrder

/--
Lemma 14.31 product formula along alternatives.
-/
theorem Vaart1998Lemma14_31HellingerRescalingSource.product_formula
    (S : Vaart1998Lemma14_31HellingerRescalingSource) (n : ℕ) :
    S.productSquaredHellinger n =
      vaart1998_squaredHellingerProduct n
        (S.singleSquaredHellinger n) :=
  S.productFormula n

/--
Smooth-model intermediate rate from Example 14.32.
-/
def vaart1998_smoothModelIntermediateRate (n : ℕ) : ℝ :=
  Real.sqrt (n : ℝ)

/--
Uniform-law intermediate rate from Example 14.33.
-/
def vaart1998_uniformLawIntermediateRate (n : ℕ) : ℝ :=
  n

/--
Triangular-law intermediate rate from Example 14.34.
-/
def vaart1998_triangularLawIntermediateRate (n : ℕ) : ℝ :=
  Real.sqrt ((n : ℝ) * Real.log (n : ℝ))

/--
Branching-process exponential intermediate rate from Example 14.35.
-/
def vaart1998_branchingIntermediateRate (meanOffspring : ℝ) (n : ℕ) : ℝ :=
  meanOffspring ^ n

/--
Example 14.32 source: smooth DQM models have squared Hellinger distance of
quadratic order and hence `sqrt n` intermediate rate.
-/
structure Vaart1998Example14_32SmoothModelRateSource where
  /-- Squared Hellinger distance as a function of parameter displacement. -/
  squaredHellinger : ℝ -> ℝ
  /-- Differentiability in quadratic mean source. -/
  differentiabilityInQuadraticMean : Prop
  /-- Quadratic Hellinger order source. -/
  quadraticHellingerOrder : Prop
  /-- Intermediate rate. -/
  intermediateRate : ℕ -> ℝ
  /-- Rate display. -/
  intermediateRate_eq :
    intermediateRate = vaart1998_smoothModelIntermediateRate
  /-- Source proof of differentiability in quadratic mean. -/
  differentiabilityInQuadraticMean_proof :
    differentiabilityInQuadraticMean
  /-- Source proof of the quadratic Hellinger order. -/
  quadraticHellingerOrder_proof :
    quadraticHellingerOrder

/--
Example 14.32 rate display.
-/
theorem Vaart1998Example14_32SmoothModelRateSource.rate_display
    (S : Vaart1998Example14_32SmoothModelRateSource) :
    S.intermediateRate = vaart1998_smoothModelIntermediateRate :=
  S.intermediateRate_eq

/--
Example 14.33 source: the uniform law has linear Hellinger order and hence
rate `n`.
-/
structure Vaart1998Example14_33UniformLawRateSource where
  /-- Squared Hellinger distance as a function of parameter displacement. -/
  squaredHellinger : ℝ -> ℝ
  /-- Linear Hellinger order source. -/
  linearHellingerOrder : Prop
  /-- Intermediate rate. -/
  intermediateRate : ℕ -> ℝ
  /-- Rate display. -/
  intermediateRate_eq :
    intermediateRate = vaart1998_uniformLawIntermediateRate
  /-- Source proof of the linear Hellinger order. -/
  linearHellingerOrder_proof :
    linearHellingerOrder

/--
Example 14.33 rate display.
-/
theorem Vaart1998Example14_33UniformLawRateSource.rate_display
    (S : Vaart1998Example14_33UniformLawRateSource) :
    S.intermediateRate = vaart1998_uniformLawIntermediateRate :=
  S.intermediateRate_eq

/--
Example 14.34 source: the triangular law has `theta^2 log(1/theta)` Hellinger
order and hence `sqrt(n log n)` rate.
-/
structure Vaart1998Example14_34TriangularLawRateSource where
  /-- Squared Hellinger distance as a function of parameter displacement. -/
  squaredHellinger : ℝ -> ℝ
  /-- Logarithmic Hellinger order source. -/
  logarithmicHellingerOrder : Prop
  /-- Intermediate rate. -/
  intermediateRate : ℕ -> ℝ
  /-- Rate display. -/
  intermediateRate_eq :
    intermediateRate = vaart1998_triangularLawIntermediateRate
  /-- Source proof of the logarithmic Hellinger order. -/
  logarithmicHellingerOrder_proof :
    logarithmicHellingerOrder

/--
Example 14.34 rate display.
-/
theorem Vaart1998Example14_34TriangularLawRateSource.rate_display
    (S : Vaart1998Example14_34TriangularLawRateSource) :
    S.intermediateRate = vaart1998_triangularLawIntermediateRate :=
  S.intermediateRate_eq

/--
Example 14.35 source: branching-process tests can have exponential rescaling
rates governed by the offspring mean.
-/
structure Vaart1998Example14_35BranchingRateSource where
  /-- Offspring mean under the parameter. -/
  meanOffspring : ℝ
  /-- Hellinger or likelihood-ratio branching source. -/
  branchingSource : Prop
  /-- Intermediate rate. -/
  intermediateRate : ℕ -> ℝ
  /-- Rate display. -/
  intermediateRate_eq :
    intermediateRate = vaart1998_branchingIntermediateRate meanOffspring
  /-- Source proof for the branching calculation. -/
  branchingSource_proof :
    branchingSource

/--
Example 14.35 rate display.
-/
theorem Vaart1998Example14_35BranchingRateSource.rate_display
    (S : Vaart1998Example14_35BranchingRateSource) :
    S.intermediateRate =
      vaart1998_branchingIntermediateRate S.meanOffspring :=
  S.intermediateRate_eq

end AsymptoticStatistics
end StatInference
