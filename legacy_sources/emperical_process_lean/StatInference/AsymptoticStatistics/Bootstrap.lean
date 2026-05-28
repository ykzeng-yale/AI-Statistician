import StatInference.AsymptoticStatistics.LStatistics
import StatInference.AsymptoticStatistics.SampleMean

/-!
# van der Vaart 1998 Chapter 23 bootstrap

This module opens the Chapter 23 lane of A. W. van der Vaart,
*Asymptotic Statistics* (1998).  The first source layer records the
introductory bootstrap notation: confidence intervals from upper quantiles,
normal approximation intervals, plug-in bootstrap laws, bootstrap
studentized statistics, bootstrap quantiles (23.1), percentile-t and
percentile intervals, Efron's percentile interval, and empirical/parametric
bootstrap sampling-law displays.
-/

noncomputable section

namespace StatInference
namespace AsymptoticStatistics

open Filter MeasureTheory ProbabilityTheory
open scoped BigOperators ENNReal ProbabilityTheory Topology

/-- Studentized statistic `(thetaHat - theta) / sigmaHat`. -/
def vaart1998_studentizedEstimator
    {Ω : Type*} (estimator scaleEstimator : ℕ -> Ω -> ℝ)
    (theta : ℝ) (n : ℕ) (ω : Ω) : ℝ :=
  (estimator n ω - theta) / scaleEstimator n ω

/-- Bootstrap studentized statistic
`(thetaHat^* - thetaHat) / sigmaHat^*`, evaluated conditionally on the
original sample. -/
def vaart1998_bootstrapStudentizedEstimator
    {Ω ΩBootstrap : Type*}
    (bootstrapEstimator : ℕ -> Ω -> ΩBootstrap -> ℝ)
    (estimator : ℕ -> Ω -> ℝ)
    (bootstrapScaleEstimator : ℕ -> Ω -> ΩBootstrap -> ℝ)
    (n : ℕ) (ω : Ω) (ωBootstrap : ΩBootstrap) : ℝ :=
  (bootstrapEstimator n ω ωBootstrap - estimator n ω) /
    bootstrapScaleEstimator n ω ωBootstrap

/-- Confidence interval event based on two upper quantiles of the
studentized statistic:
`thetaHat - xi_beta sigmaHat <= theta <= thetaHat - xi_{1-alpha} sigmaHat`. -/
def vaart1998_quantileConfidenceIntervalEvent
    {Ω : Type*} (estimator scaleEstimator : ℕ -> Ω -> ℝ)
    (theta xiBeta xiOneMinusAlpha : ℝ) (n : ℕ) : Set Ω :=
  {ω |
    estimator n ω - xiBeta * scaleEstimator n ω ≤ theta ∧
      theta ≤ estimator n ω - xiOneMinusAlpha * scaleEstimator n ω}

/-- Normal-approximation confidence interval event obtained by substituting
standard-normal critical values for the unknown quantiles. -/
def vaart1998_normalApproximationIntervalEvent
    {Ω : Type*} (estimator scaleEstimator : ℕ -> Ω -> ℝ)
    (theta zBeta zOneMinusAlpha : ℝ) (n : ℕ) : Set Ω :=
  vaart1998_quantileConfidenceIntervalEvent
    estimator scaleEstimator theta zBeta zOneMinusAlpha n

/-- The bootstrap plug-in law: substitute an estimated distribution for the
unknown data-generating distribution. -/
def vaart1998_bootstrapPluginDistribution
    {Ω SampleSpace : Type*} [MeasurableSpace SampleSpace]
    (estimatedDistribution : ℕ -> Ω -> Measure SampleSpace)
    (n : ℕ) (ω : Ω) : Measure SampleSpace :=
  estimatedDistribution n ω

/-- Empirical bootstrap sampling law `n^{-1} sum_i delta_{X_i}`. -/
def vaart1998_empiricalBootstrapDistribution
    {Ω SampleSpace : Type*} [MeasurableSpace SampleSpace]
    (observation : ℕ -> ℕ -> Ω -> SampleSpace)
    (n : ℕ) (ω : Ω) : Measure SampleSpace :=
  ((n : ℝ≥0∞)⁻¹) •
    ∑ i ∈ Finset.Icc 1 n, Measure.dirac (observation n i ω)

/-- Parametric bootstrap sampling law `P_{thetaHat}`. -/
def vaart1998_parametricBootstrapDistribution
    {Ω SampleSpace Parameter : Type*} [MeasurableSpace SampleSpace]
    (model : Parameter -> Measure SampleSpace)
    (estimator : ℕ -> Ω -> Parameter) (n : ℕ) (ω : Ω) :
    Measure SampleSpace :=
  model (estimator n ω)

/-- Bootstrap CDF condition in display (23.1):
`P(((thetaHat^* - thetaHat) / sigmaHat^*) <= x | P_hat) >= 1 - alpha`. -/
def vaart1998_bootstrapQuantileCondition
    (bootstrapCdf : ℕ -> Ω -> ℝ -> ℝ)
    (alpha x : ℝ) (n : ℕ) (ω : Ω) : Prop :=
  1 - alpha ≤ bootstrapCdf n ω x

/-- The displayed bootstrap quantile estimator: the smallest value satisfying
the bootstrap CDF condition (23.1). -/
def vaart1998_isBootstrapQuantile
    (bootstrapCdf : ℕ -> Ω -> ℝ -> ℝ)
    (alpha x : ℝ) (n : ℕ) (ω : Ω) : Prop :=
  vaart1998_bootstrapQuantileCondition bootstrapCdf alpha x n ω ∧
    ∀ y : ℝ,
      vaart1998_bootstrapQuantileCondition bootstrapCdf alpha y n ω ->
        x ≤ y

/-- Percentile-t interval event using bootstrap quantile estimators. -/
def vaart1998_percentileTIntervalEvent
    {Ω : Type*} (estimator scaleEstimator : ℕ -> Ω -> ℝ)
    (theta : ℝ)
    (bootstrapQuantileBeta bootstrapQuantileOneMinusAlpha :
      ℕ -> Ω -> ℝ)
    (n : ℕ) : Set Ω :=
  {ω |
    estimator n ω - bootstrapQuantileBeta n ω * scaleEstimator n ω ≤
        theta ∧
      theta ≤
        estimator n ω -
          bootstrapQuantileOneMinusAlpha n ω * scaleEstimator n ω}

/-- Percentile interval event, the special case with unit scale. -/
def vaart1998_percentileIntervalEvent
    {Ω : Type*} (estimator : ℕ -> Ω -> ℝ) (theta : ℝ)
    (bootstrapCenteredQuantileBeta bootstrapCenteredQuantileOneMinusAlpha :
      ℕ -> Ω -> ℝ)
    (n : ℕ) : Set Ω :=
  {ω |
    estimator n ω - bootstrapCenteredQuantileBeta n ω ≤ theta ∧
      theta ≤ estimator n ω - bootstrapCenteredQuantileOneMinusAlpha n ω}

/-- Efron's percentile interval event based on quantiles of `thetaHat^*`. -/
def vaart1998_efronPercentileIntervalEvent
    {Ω : Type*} (theta : ℝ)
    (bootstrapEstimatorQuantileOneMinusBeta bootstrapEstimatorQuantileAlpha :
      ℕ -> Ω -> ℝ)
    (n : ℕ) : Set Ω :=
  {ω |
    bootstrapEstimatorQuantileOneMinusBeta n ω ≤ theta ∧
      theta ≤ bootstrapEstimatorQuantileAlpha n ω}

/-- Efron's interval rewritten through centered bootstrap quantiles:
`[thetaHat + xi_{1-beta}, thetaHat + xi_alpha]`. -/
def vaart1998_efronIntervalFromCenteredQuantilesEvent
    {Ω : Type*} (estimator : ℕ -> Ω -> ℝ) (theta : ℝ)
    (centeredQuantileOneMinusBeta centeredQuantileAlpha :
      ℕ -> Ω -> ℝ)
    (n : ℕ) : Set Ω :=
  {ω |
    estimator n ω + centeredQuantileOneMinusBeta n ω ≤ theta ∧
      theta ≤ estimator n ω + centeredQuantileAlpha n ω}

/-- Symmetric percentile-t interval using an upper quantile of the absolute
studentized bootstrap statistic. -/
def vaart1998_symmetricPercentileTIntervalEvent
    {Ω : Type*} (estimator scaleEstimator : ℕ -> Ω -> ℝ)
    (theta : ℝ) (absoluteBootstrapQuantile : ℕ -> Ω -> ℝ)
    (n : ℕ) : Set Ω :=
  {ω |
    estimator n ω - absoluteBootstrapQuantile n ω * scaleEstimator n ω ≤
        theta ∧
      theta ≤
        estimator n ω + absoluteBootstrapQuantile n ω * scaleEstimator n ω}

theorem vaart1998_studentizedEstimator_apply
    {Ω : Type*} (estimator scaleEstimator : ℕ -> Ω -> ℝ)
    (theta : ℝ) (n : ℕ) (ω : Ω) :
    vaart1998_studentizedEstimator estimator scaleEstimator theta n ω =
      (estimator n ω - theta) / scaleEstimator n ω :=
  rfl

theorem vaart1998_bootstrapStudentizedEstimator_apply
    {Ω ΩBootstrap : Type*}
    (bootstrapEstimator : ℕ -> Ω -> ΩBootstrap -> ℝ)
    (estimator : ℕ -> Ω -> ℝ)
    (bootstrapScaleEstimator : ℕ -> Ω -> ΩBootstrap -> ℝ)
    (n : ℕ) (ω : Ω) (ωBootstrap : ΩBootstrap) :
    vaart1998_bootstrapStudentizedEstimator
        bootstrapEstimator estimator bootstrapScaleEstimator
        n ω ωBootstrap =
      (bootstrapEstimator n ω ωBootstrap - estimator n ω) /
        bootstrapScaleEstimator n ω ωBootstrap :=
  rfl

theorem vaart1998_bootstrapPluginDistribution_apply
    {Ω SampleSpace : Type*} [MeasurableSpace SampleSpace]
    (estimatedDistribution : ℕ -> Ω -> Measure SampleSpace)
    (n : ℕ) (ω : Ω) :
    vaart1998_bootstrapPluginDistribution estimatedDistribution n ω =
      estimatedDistribution n ω :=
  rfl

theorem vaart1998_parametricBootstrapDistribution_apply
    {Ω SampleSpace Parameter : Type*} [MeasurableSpace SampleSpace]
    (model : Parameter -> Measure SampleSpace)
    (estimator : ℕ -> Ω -> Parameter) (n : ℕ) (ω : Ω) :
    vaart1998_parametricBootstrapDistribution model estimator n ω =
      model (estimator n ω) :=
  rfl

/-- Source package for Chapter 23.1's bootstrap introduction. -/
structure Vaart1998Chapter23_1BootstrapIntroductionSource
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    (P : ℕ -> Measure Ω) [∀ n : ℕ, IsProbabilityMeasure (P n)]
    (LimitLaw : Measure ΩLimit) [IsProbabilityMeasure LimitLaw] where
  theta : ℝ
  alpha : ℝ
  beta : ℝ
  estimator : ℕ -> Ω -> ℝ
  scaleEstimator : ℕ -> Ω -> ℝ
  trueStudentizedStatistic : ℕ -> Ω -> ℝ
  normalLimitStatistic : ΩLimit -> ℝ
  trueUpperQuantile : ℝ -> ℝ
  normalUpperQuantile : ℝ -> ℝ
  bootstrapEstimator : ℕ -> Ω -> ΩBootstrap -> ℝ
  bootstrapScaleEstimator : ℕ -> Ω -> ΩBootstrap -> ℝ
  bootstrapStudentizedStatistic : ℕ -> Ω -> ΩBootstrap -> ℝ
  bootstrapCdf : ℕ -> Ω -> ℝ -> ℝ
  bootstrapQuantile : ℝ -> ℕ -> Ω -> ℝ
  estimatedDistribution : ℕ -> Ω -> Measure SampleSpace
  observation : ℕ -> ℕ -> Ω -> SampleSpace
  parametricModel : Parameter -> Measure SampleSpace
  parameterEstimator : ℕ -> Ω -> Parameter
  confidenceIntervalEvent : ℕ -> Set Ω
  normalApproximationEvent : ℕ -> Set Ω
  percentileTEvent : ℕ -> Set Ω
  percentileEvent : ℕ -> Set Ω
  efronPercentileEvent : ℕ -> Set Ω
  symmetricPercentileTEvent : ℕ -> Set Ω
  coverageProbability : ℕ -> ℝ
  normalCoverageProbability : ℕ -> ℝ
  bootstrapCoverageProbability : ℕ -> ℝ
  trueStudentizedStatistic_eq :
    trueStudentizedStatistic =
      vaart1998_studentizedEstimator estimator scaleEstimator theta
  bootstrapStudentizedStatistic_eq :
    ∀ n ω ωBootstrap,
      bootstrapStudentizedStatistic n ω ωBootstrap =
        vaart1998_bootstrapStudentizedEstimator
          bootstrapEstimator estimator bootstrapScaleEstimator
          n ω ωBootstrap
  confidenceIntervalEvent_eq :
    ∀ n,
      confidenceIntervalEvent n =
        vaart1998_quantileConfidenceIntervalEvent
          estimator scaleEstimator theta
          (trueUpperQuantile beta) (trueUpperQuantile (1 - alpha)) n
  normalApproximationEvent_eq :
    ∀ n,
      normalApproximationEvent n =
        vaart1998_normalApproximationIntervalEvent
          estimator scaleEstimator theta
          (normalUpperQuantile beta) (normalUpperQuantile (1 - alpha)) n
  bootstrapQuantile_condition :
    ∀ gamma n ω,
      vaart1998_isBootstrapQuantile
        bootstrapCdf gamma (bootstrapQuantile gamma n ω) n ω
  percentileTEvent_eq :
    ∀ n,
      percentileTEvent n =
        vaart1998_percentileTIntervalEvent
          estimator scaleEstimator theta
          (bootstrapQuantile beta)
          (bootstrapQuantile (1 - alpha)) n
  percentileEvent_eq :
    ∀ n,
      percentileEvent n =
        vaart1998_percentileIntervalEvent
          estimator theta
          (bootstrapQuantile beta)
          (bootstrapQuantile (1 - alpha)) n
  efronPercentileEvent_eq :
    ∀ n,
      efronPercentileEvent n =
        vaart1998_efronPercentileIntervalEvent
          theta
          (fun m ω => estimator m ω + bootstrapQuantile (1 - beta) m ω)
          (fun m ω => estimator m ω + bootstrapQuantile alpha m ω) n
  symmetricPercentileTEvent_eq :
    ∀ n,
      symmetricPercentileTEvent n =
        vaart1998_symmetricPercentileTIntervalEvent
          estimator scaleEstimator theta
          (bootstrapQuantile (alpha + beta)) n
  weakLimit_normal_statement : Prop
  weakLimit_normal : weakLimit_normal_statement
  trueStudentized_tendsto :
    TendstoInDistribution trueStudentizedStatistic atTop
      normalLimitStatistic P LimitLaw
  normalApproximation_asymptoticCoverage :
    Tendsto normalCoverageProbability atTop (𝓝 (1 - alpha - beta))
  plugin_distribution_eq :
    ∀ n ω,
      vaart1998_bootstrapPluginDistribution estimatedDistribution n ω =
        estimatedDistribution n ω
  empiricalBootstrap_statement : Prop
  empiricalBootstrap : empiricalBootstrap_statement
  parametricBootstrap_eq :
    ∀ n ω,
      vaart1998_parametricBootstrapDistribution
        parametricModel parameterEstimator n ω =
        parametricModel (parameterEstimator n ω)
  bootstrapQuantiles_consistent_statement : Prop
  bootstrapQuantiles_consistent : bootstrapQuantiles_consistent_statement
  bootstrapConfidence_asymptoticCoverage :
    Tendsto bootstrapCoverageProbability atTop (𝓝 (1 - alpha - beta))
  percentileT_more_accurate_statement : Prop
  percentileT_more_accurate : percentileT_more_accurate_statement
  efron_invariant_statement : Prop
  efron_invariant : efron_invariant_statement

namespace Vaart1998Chapter23_1BootstrapIntroductionSource

theorem true_studentized_display
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S :
      Vaart1998Chapter23_1BootstrapIntroductionSource
        (ΩBootstrap := ΩBootstrap)
        (SampleSpace := SampleSpace) (Parameter := Parameter)
        P LimitLaw) :
    S.trueStudentizedStatistic =
      vaart1998_studentizedEstimator
        S.estimator S.scaleEstimator S.theta :=
  S.trueStudentizedStatistic_eq

theorem bootstrap_studentized_display
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S :
      Vaart1998Chapter23_1BootstrapIntroductionSource
        (ΩBootstrap := ΩBootstrap)
        (SampleSpace := SampleSpace) (Parameter := Parameter)
        P LimitLaw)
    (n : ℕ) (ω : Ω) (ωBootstrap : ΩBootstrap) :
    S.bootstrapStudentizedStatistic n ω ωBootstrap =
      vaart1998_bootstrapStudentizedEstimator
        S.bootstrapEstimator S.estimator S.bootstrapScaleEstimator
        n ω ωBootstrap :=
  S.bootstrapStudentizedStatistic_eq n ω ωBootstrap

theorem confidence_interval_display
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S :
      Vaart1998Chapter23_1BootstrapIntroductionSource
        (ΩBootstrap := ΩBootstrap)
        (SampleSpace := SampleSpace) (Parameter := Parameter)
        P LimitLaw)
    (n : ℕ) :
    S.confidenceIntervalEvent n =
      vaart1998_quantileConfidenceIntervalEvent
        S.estimator S.scaleEstimator S.theta
        (S.trueUpperQuantile S.beta)
        (S.trueUpperQuantile (1 - S.alpha)) n :=
  S.confidenceIntervalEvent_eq n

theorem normal_interval_display
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S :
      Vaart1998Chapter23_1BootstrapIntroductionSource
        (ΩBootstrap := ΩBootstrap)
        (SampleSpace := SampleSpace) (Parameter := Parameter)
        P LimitLaw)
    (n : ℕ) :
    S.normalApproximationEvent n =
      vaart1998_normalApproximationIntervalEvent
        S.estimator S.scaleEstimator S.theta
        (S.normalUpperQuantile S.beta)
        (S.normalUpperQuantile (1 - S.alpha)) n :=
  S.normalApproximationEvent_eq n

theorem bootstrap_quantile_condition
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S :
      Vaart1998Chapter23_1BootstrapIntroductionSource
        (ΩBootstrap := ΩBootstrap)
        (SampleSpace := SampleSpace) (Parameter := Parameter)
        P LimitLaw)
    (gamma : ℝ) (n : ℕ) (ω : Ω) :
    vaart1998_isBootstrapQuantile
      S.bootstrapCdf gamma (S.bootstrapQuantile gamma n ω) n ω :=
  S.bootstrapQuantile_condition gamma n ω

theorem percentile_t_interval_display
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S :
      Vaart1998Chapter23_1BootstrapIntroductionSource
        (ΩBootstrap := ΩBootstrap)
        (SampleSpace := SampleSpace) (Parameter := Parameter)
        P LimitLaw)
    (n : ℕ) :
    S.percentileTEvent n =
      vaart1998_percentileTIntervalEvent
        S.estimator S.scaleEstimator S.theta
        (S.bootstrapQuantile S.beta)
        (S.bootstrapQuantile (1 - S.alpha)) n :=
  S.percentileTEvent_eq n

theorem percentile_interval_display
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S :
      Vaart1998Chapter23_1BootstrapIntroductionSource
        (ΩBootstrap := ΩBootstrap)
        (SampleSpace := SampleSpace) (Parameter := Parameter)
        P LimitLaw)
    (n : ℕ) :
    S.percentileEvent n =
      vaart1998_percentileIntervalEvent
        S.estimator S.theta
        (S.bootstrapQuantile S.beta)
        (S.bootstrapQuantile (1 - S.alpha)) n :=
  S.percentileEvent_eq n

theorem efron_interval_display
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S :
      Vaart1998Chapter23_1BootstrapIntroductionSource
        (ΩBootstrap := ΩBootstrap)
        (SampleSpace := SampleSpace) (Parameter := Parameter)
        P LimitLaw)
    (n : ℕ) :
    S.efronPercentileEvent n =
      vaart1998_efronPercentileIntervalEvent
        S.theta
        (fun m ω => S.estimator m ω + S.bootstrapQuantile (1 - S.beta) m ω)
        (fun m ω => S.estimator m ω + S.bootstrapQuantile S.alpha m ω) n :=
  S.efronPercentileEvent_eq n

theorem true_studentized_tendsto
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S :
      Vaart1998Chapter23_1BootstrapIntroductionSource
        (ΩBootstrap := ΩBootstrap)
        (SampleSpace := SampleSpace) (Parameter := Parameter)
        P LimitLaw) :
    TendstoInDistribution S.trueStudentizedStatistic atTop
      S.normalLimitStatistic P LimitLaw :=
  S.trueStudentized_tendsto

theorem normal_asymptotic_coverage
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S :
      Vaart1998Chapter23_1BootstrapIntroductionSource
        (ΩBootstrap := ΩBootstrap)
        (SampleSpace := SampleSpace) (Parameter := Parameter)
        P LimitLaw) :
    Tendsto S.normalCoverageProbability atTop
      (𝓝 (1 - S.alpha - S.beta)) :=
  S.normalApproximation_asymptoticCoverage

theorem bootstrap_asymptotic_coverage
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S :
      Vaart1998Chapter23_1BootstrapIntroductionSource
        (ΩBootstrap := ΩBootstrap)
        (SampleSpace := SampleSpace) (Parameter := Parameter)
        P LimitLaw) :
    Tendsto S.bootstrapCoverageProbability atTop
      (𝓝 (1 - S.alpha - S.beta)) :=
  S.bootstrapConfidence_asymptoticCoverage

theorem empirical_bootstrap_source
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S :
      Vaart1998Chapter23_1BootstrapIntroductionSource
        (ΩBootstrap := ΩBootstrap)
        (SampleSpace := SampleSpace) (Parameter := Parameter)
        P LimitLaw) :
    S.empiricalBootstrap_statement :=
  S.empiricalBootstrap

theorem efron_invariance_source
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S :
      Vaart1998Chapter23_1BootstrapIntroductionSource
        (ΩBootstrap := ΩBootstrap)
        (SampleSpace := SampleSpace) (Parameter := Parameter)
        P LimitLaw) :
    S.efron_invariant_statement :=
  S.efron_invariant

end Vaart1998Chapter23_1BootstrapIntroductionSource

/-- Coverage event for an arbitrary real confidence interval
`[lower_n, upper_n]` covering the scalar target `theta`. -/
def vaart1998_confidenceIntervalCoverageEvent
    {Ω : Type*} (lowerEndpoint upperEndpoint : ℕ -> Ω -> ℝ)
    (theta : ℝ) (n : ℕ) : Set Ω :=
  {ω | lowerEndpoint n ω ≤ theta ∧ theta ≤ upperEndpoint n ω}

/-- Conservative asymptotic coverage at a requested level, written in the
`liminf >= level` form used in Section 23.2. -/
def vaart1998_asymptoticallyConservativeAtLevel
    (coverageProbability : ℕ -> ℝ) (level : ℝ) : Prop :=
  ∀ ε : ℝ, 0 < ε ->
    ∀ᶠ n in atTop, level - ε ≤ coverageProbability n

/-- Asymptotic consistency of confidence intervals at a scalar level. -/
def vaart1998_confidenceIntervalAsymptoticConsistency
    {Ω : Type*} [MeasurableSpace Ω] (P : ℕ -> Measure Ω)
    (lowerEndpoint upperEndpoint : ℕ -> Ω -> ℝ)
    (theta level : ℝ) : Prop :=
  vaart1998_asymptoticallyConservativeAtLevel
    (fun n => (P n).real
      (vaart1998_confidenceIntervalCoverageEvent
        lowerEndpoint upperEndpoint theta n))
    level

/-- Kolmogorov-Smirnov distance between two scalar distribution functions. -/
def vaart1998_kolmogorovSmirnovDistance
    (cdfA cdfB : ℝ -> ℝ) : ℝ :=
  sSup ((fun x : ℝ => |cdfA x - cdfB x|) '' Set.univ)

/-- Random bootstrap Kolmogorov-Smirnov distance between the law of the true
studentized statistic and the conditional bootstrap law. -/
def vaart1998_bootstrapKolmogorovSmirnovDistance
    {Ω : Type*} (trueCdf : ℕ -> ℝ -> ℝ)
    (bootstrapCdf : ℕ -> Ω -> ℝ -> ℝ)
    (n : ℕ) (ω : Ω) : ℝ :=
  vaart1998_kolmogorovSmirnovDistance
    (trueCdf n) (bootstrapCdf n ω)

/-- Bootstrap consistency relative to Kolmogorov-Smirnov distance. -/
def vaart1998_bootstrapKolmogorovSmirnovConsistent
    {Ω : Type*} [MeasurableSpace Ω] (P : ℕ -> Measure Ω)
    (trueCdf : ℕ -> ℝ -> ℝ)
    (bootstrapCdf : ℕ -> Ω -> ℝ -> ℝ) : Prop :=
  Vaart1998MeasureSeqConvergesInProbabilityToZero P
    (vaart1998_bootstrapKolmogorovSmirnovDistance trueCdf bootstrapCdf)

/-- Pointwise CDF version of (23.2): the true CDF converges to `F`, and the
conditional bootstrap CDF converges to the same `F` in probability. -/
def vaart1998_bootstrapPointwiseCdfConsistency
    {Ω : Type*} [MeasurableSpace Ω] (P : ℕ -> Measure Ω)
    (trueCdf : ℕ -> ℝ -> ℝ)
    (bootstrapCdf : ℕ -> Ω -> ℝ -> ℝ)
    (limitCdf : ℝ -> ℝ) : Prop :=
  ∀ x : ℝ,
    Tendsto (fun n : ℕ => trueCdf n x) atTop (𝓝 (limitCdf x)) ∧
      Vaart1998MeasureSeqConvergesInProbabilityToZero P
        (fun n ω => bootstrapCdf n ω x - limitCdf x)

/-- Upper-tail quantile convention used in Chapter 23:
`xi_alpha = F^{-1}(1-alpha)`. -/
def vaart1998_upperQuantileFromCdf
    (cdf : ℝ -> ℝ) (alpha : ℝ) : ℝ :=
  vaart1998_quantileFunction cdf (1 - alpha)

/-- Bootstrap quantile convergence in probability to the corresponding
upper-tail quantile of the limiting distribution. -/
def vaart1998_bootstrapQuantileConvergesInProbability
    {Ω : Type*} [MeasurableSpace Ω] (P : ℕ -> Measure Ω)
    (bootstrapQuantile : ℝ -> ℕ -> Ω -> ℝ)
    (limitCdf : ℝ -> ℝ) (alpha : ℝ) : Prop :=
  Vaart1998MeasureSeqConvergesInProbabilityToZero P
    (fun n ω =>
      bootstrapQuantile alpha n ω -
        vaart1998_upperQuantileFromCdf limitCdf alpha)

/-- Lower endpoint of the percentile-t interval. -/
def vaart1998_percentileTLowerEndpoint
    {Ω : Type*} (estimator scaleEstimator : ℕ -> Ω -> ℝ)
    (bootstrapQuantile : ℝ -> ℕ -> Ω -> ℝ)
    (beta : ℝ) (n : ℕ) (ω : Ω) : ℝ :=
  estimator n ω - bootstrapQuantile beta n ω * scaleEstimator n ω

/-- Upper endpoint of the percentile-t interval. -/
def vaart1998_percentileTUpperEndpoint
    {Ω : Type*} (estimator scaleEstimator : ℕ -> Ω -> ℝ)
    (bootstrapQuantile : ℝ -> ℕ -> Ω -> ℝ)
    (oneMinusAlpha : ℝ) (n : ℕ) (ω : Ω) : ℝ :=
  estimator n ω -
    bootstrapQuantile oneMinusAlpha n ω * scaleEstimator n ω

/-- Lower endpoint of Efron's percentile interval. -/
def vaart1998_efronLowerEndpointFromCenteredQuantile
    {Ω : Type*} (estimator : ℕ -> Ω -> ℝ)
    (bootstrapQuantile : ℝ -> ℕ -> Ω -> ℝ)
    (beta : ℝ) (n : ℕ) (ω : Ω) : ℝ :=
  estimator n ω + bootstrapQuantile (1 - beta) n ω

/-- Upper endpoint of Efron's percentile interval. -/
def vaart1998_efronUpperEndpointFromCenteredQuantile
    {Ω : Type*} (estimator : ℕ -> Ω -> ℝ)
    (bootstrapQuantile : ℝ -> ℕ -> Ω -> ℝ)
    (alpha : ℝ) (n : ℕ) (ω : Ω) : ℝ :=
  estimator n ω + bootstrapQuantile alpha n ω

theorem vaart1998_confidenceIntervalCoverageEvent_percentileT
    {Ω : Type*} (estimator scaleEstimator : ℕ -> Ω -> ℝ)
    (theta : ℝ) (bootstrapQuantile : ℝ -> ℕ -> Ω -> ℝ)
    (beta oneMinusAlpha : ℝ) (n : ℕ) :
    vaart1998_confidenceIntervalCoverageEvent
        (vaart1998_percentileTLowerEndpoint
          estimator scaleEstimator bootstrapQuantile beta)
        (vaart1998_percentileTUpperEndpoint
          estimator scaleEstimator bootstrapQuantile oneMinusAlpha)
        theta n =
      vaart1998_percentileTIntervalEvent
        estimator scaleEstimator theta
        (bootstrapQuantile beta) (bootstrapQuantile oneMinusAlpha) n :=
  rfl

theorem vaart1998_confidenceIntervalCoverageEvent_efron
    {Ω : Type*} (estimator : ℕ -> Ω -> ℝ)
    (theta : ℝ) (bootstrapQuantile : ℝ -> ℕ -> Ω -> ℝ)
    (alpha beta : ℝ) (n : ℕ) :
    vaart1998_confidenceIntervalCoverageEvent
        (vaart1998_efronLowerEndpointFromCenteredQuantile
          estimator bootstrapQuantile beta)
        (vaart1998_efronUpperEndpointFromCenteredQuantile
          estimator bootstrapQuantile alpha)
        theta n =
      vaart1998_efronIntervalFromCenteredQuantilesEvent
        estimator theta
        (bootstrapQuantile (1 - beta)) (bootstrapQuantile alpha) n :=
  rfl

/-- Section 23.2 source package: consistency of bootstrap distribution
estimators, the Kolmogorov-Smirnov criterion, the pointwise CDF form (23.2),
and the conservative confidence-interval coverage definition. -/
structure Vaart1998Section23_2BootstrapConsistencySource
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    (P : ℕ -> Measure Ω) [∀ n : ℕ, IsProbabilityMeasure (P n)]
    (LimitLaw : Measure ΩLimit) [IsProbabilityMeasure LimitLaw] where
  intro :
    Vaart1998Chapter23_1BootstrapIntroductionSource
      (ΩBootstrap := ΩBootstrap)
      (SampleSpace := SampleSpace) (Parameter := Parameter)
      P LimitLaw
  trueStudentizedCdf : ℕ -> ℝ -> ℝ
  bootstrapStudentizedCdf : ℕ -> Ω -> ℝ -> ℝ
  limitCdf : ℝ -> ℝ
  limitQuantile : ℝ -> ℝ
  lowerEndpoint : ℕ -> Ω -> ℝ
  upperEndpoint : ℕ -> Ω -> ℝ
  coverageProbability : ℕ -> ℝ
  kolmogorovSmirnovDistance : ℕ -> Ω -> ℝ
  consistencyLevel : ℝ
  consistencyLevel_eq :
    consistencyLevel = 1 - intro.alpha - intro.beta
  limitQuantile_eq :
    limitQuantile = vaart1998_quantileFunction limitCdf
  limitCdf_continuous_statement : Prop
  limitCdf_continuous : limitCdf_continuous_statement
  coverageProbability_eq :
    ∀ n,
      coverageProbability n =
        (P n).real
          (vaart1998_confidenceIntervalCoverageEvent
            lowerEndpoint upperEndpoint intro.theta n)
  conservativeCoverage :
    vaart1998_asymptoticallyConservativeAtLevel
      coverageProbability consistencyLevel
  confidenceIntervalConsistency :
    vaart1998_confidenceIntervalAsymptoticConsistency
      P lowerEndpoint upperEndpoint intro.theta consistencyLevel
  kolmogorovSmirnovDistance_eq :
    ∀ n ω,
      kolmogorovSmirnovDistance n ω =
        vaart1998_bootstrapKolmogorovSmirnovDistance
          trueStudentizedCdf bootstrapStudentizedCdf n ω
  kolmogorovSmirnovConsistency :
    Vaart1998MeasureSeqConvergesInProbabilityToZero
      P kolmogorovSmirnovDistance
  pointwiseCdfConsistency :
    vaart1998_bootstrapPointwiseCdfConsistency
      P trueStudentizedCdf bootstrapStudentizedCdf limitCdf
  kolmogorovSmirnov_iff_pointwise_statement : Prop
  kolmogorovSmirnov_iff_pointwise :
    kolmogorovSmirnov_iff_pointwise_statement
  equation23_2_statement : Prop
  equation23_2 : equation23_2_statement

namespace Vaart1998Section23_2BootstrapConsistencySource

theorem coverage_probability_display
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S :
      Vaart1998Section23_2BootstrapConsistencySource
        (ΩBootstrap := ΩBootstrap)
        (SampleSpace := SampleSpace) (Parameter := Parameter)
        P LimitLaw)
    (n : ℕ) :
    S.coverageProbability n =
      (P n).real
        (vaart1998_confidenceIntervalCoverageEvent
          S.lowerEndpoint S.upperEndpoint S.intro.theta n) :=
  S.coverageProbability_eq n

theorem conservative_coverage
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S :
      Vaart1998Section23_2BootstrapConsistencySource
        (ΩBootstrap := ΩBootstrap)
        (SampleSpace := SampleSpace) (Parameter := Parameter)
        P LimitLaw) :
    vaart1998_asymptoticallyConservativeAtLevel
      S.coverageProbability S.consistencyLevel :=
  S.conservativeCoverage

theorem confidence_interval_consistency
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S :
      Vaart1998Section23_2BootstrapConsistencySource
        (ΩBootstrap := ΩBootstrap)
        (SampleSpace := SampleSpace) (Parameter := Parameter)
        P LimitLaw) :
    vaart1998_confidenceIntervalAsymptoticConsistency
      P S.lowerEndpoint S.upperEndpoint S.intro.theta
      S.consistencyLevel :=
  S.confidenceIntervalConsistency

theorem kolmogorov_smirnov_distance_display
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S :
      Vaart1998Section23_2BootstrapConsistencySource
        (ΩBootstrap := ΩBootstrap)
        (SampleSpace := SampleSpace) (Parameter := Parameter)
        P LimitLaw)
    (n : ℕ) (ω : Ω) :
    S.kolmogorovSmirnovDistance n ω =
      vaart1998_bootstrapKolmogorovSmirnovDistance
        S.trueStudentizedCdf S.bootstrapStudentizedCdf n ω :=
  S.kolmogorovSmirnovDistance_eq n ω

theorem kolmogorov_smirnov_consistency
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S :
      Vaart1998Section23_2BootstrapConsistencySource
        (ΩBootstrap := ΩBootstrap)
        (SampleSpace := SampleSpace) (Parameter := Parameter)
        P LimitLaw) :
    Vaart1998MeasureSeqConvergesInProbabilityToZero
      P S.kolmogorovSmirnovDistance :=
  S.kolmogorovSmirnovConsistency

theorem true_cdf_tendsto
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S :
      Vaart1998Section23_2BootstrapConsistencySource
        (ΩBootstrap := ΩBootstrap)
        (SampleSpace := SampleSpace) (Parameter := Parameter)
        P LimitLaw)
    (x : ℝ) :
    Tendsto (fun n : ℕ => S.trueStudentizedCdf n x) atTop
      (𝓝 (S.limitCdf x)) :=
  (S.pointwiseCdfConsistency x).1

theorem bootstrap_cdf_tendsto_in_probability
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S :
      Vaart1998Section23_2BootstrapConsistencySource
        (ΩBootstrap := ΩBootstrap)
        (SampleSpace := SampleSpace) (Parameter := Parameter)
        P LimitLaw)
    (x : ℝ) :
    Vaart1998MeasureSeqConvergesInProbabilityToZero P
      (fun n ω => S.bootstrapStudentizedCdf n ω x - S.limitCdf x) :=
  (S.pointwiseCdfConsistency x).2

theorem equation23_2_source
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S :
      Vaart1998Section23_2BootstrapConsistencySource
        (ΩBootstrap := ΩBootstrap)
        (SampleSpace := SampleSpace) (Parameter := Parameter)
        P LimitLaw) :
    S.equation23_2_statement :=
  S.equation23_2

end Vaart1998Section23_2BootstrapConsistencySource

/-- Lemma 23.3 source package: conditional weak convergence of the bootstrap
studentized statistic to the same continuous limit gives asymptotic
consistency of percentile-t intervals, and under common nonrandom scale plus
symmetry gives Efron's percentile consistency. -/
structure Vaart1998Lemma23_3BootstrapConfidenceConsistencySource
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    (P : ℕ -> Measure Ω) [∀ n : ℕ, IsProbabilityMeasure (P n)]
    (LimitLaw : Measure ΩLimit) [IsProbabilityMeasure LimitLaw] where
  section23_2 :
    Vaart1998Section23_2BootstrapConsistencySource
      (ΩBootstrap := ΩBootstrap)
      (SampleSpace := SampleSpace) (Parameter := Parameter)
      P LimitLaw
  limitStatistic : ΩLimit -> ℝ
  limitCdf_eq :
    section23_2.limitCdf =
      ProbabilityTheory.cdf (Measure.map limitStatistic LimitLaw)
  trueStudentizedWeakLimit :
    TendstoInDistribution
      section23_2.intro.trueStudentizedStatistic atTop
      limitStatistic P LimitLaw
  conditionalBootstrapWeakLimit_statement : Prop
  conditionalBootstrapWeakLimit :
    conditionalBootstrapWeakLimit_statement
  subsequenceAlmostSureConditionalWeakLimit_statement : Prop
  subsequenceAlmostSureConditionalWeakLimit :
    subsequenceAlmostSureConditionalWeakLimit_statement
  quantileContinuity_alpha :
    ContinuousAt section23_2.limitQuantile (1 - section23_2.intro.alpha)
  quantileContinuity_beta :
    ContinuousAt section23_2.limitQuantile (1 - section23_2.intro.beta)
  lemma21_2_quantile_handoff_statement : Prop
  lemma21_2_quantile_handoff :
    lemma21_2_quantile_handoff_statement
  bootstrapQuantile_alpha_tendsto :
    vaart1998_bootstrapQuantileConvergesInProbability
      P section23_2.intro.bootstrapQuantile
      section23_2.limitCdf section23_2.intro.alpha
  bootstrapQuantile_beta_tendsto :
    vaart1998_bootstrapQuantileConvergesInProbability
      P section23_2.intro.bootstrapQuantile
      section23_2.limitCdf section23_2.intro.beta
  quantileSlutsky_alpha_statement : Prop
  quantileSlutsky_alpha : quantileSlutsky_alpha_statement
  quantileSlutsky_beta_statement : Prop
  quantileSlutsky_beta : quantileSlutsky_beta_statement
  oneSidedCoverage_alpha :
    Tendsto
      (fun n : ℕ =>
        (P n).real
          {ω |
            section23_2.intro.theta ≤
              vaart1998_percentileTUpperEndpoint
                section23_2.intro.estimator
                section23_2.intro.scaleEstimator
                section23_2.intro.bootstrapQuantile
                (1 - section23_2.intro.alpha) n ω})
      atTop (𝓝 (1 - section23_2.intro.alpha))
  oneSidedCoverage_beta :
    Tendsto
      (fun n : ℕ =>
        (P n).real
          {ω |
            vaart1998_percentileTLowerEndpoint
                section23_2.intro.estimator
                section23_2.intro.scaleEstimator
                section23_2.intro.bootstrapQuantile
                section23_2.intro.beta n ω ≤
              section23_2.intro.theta})
      atTop (𝓝 (1 - section23_2.intro.beta))
  percentileTConsistency :
    vaart1998_confidenceIntervalAsymptoticConsistency
      P
      (vaart1998_percentileTLowerEndpoint
        section23_2.intro.estimator
        section23_2.intro.scaleEstimator
        section23_2.intro.bootstrapQuantile
        section23_2.intro.beta)
      (vaart1998_percentileTUpperEndpoint
        section23_2.intro.estimator
        section23_2.intro.scaleEstimator
        section23_2.intro.bootstrapQuantile
        (1 - section23_2.intro.alpha))
      section23_2.intro.theta
      (1 - section23_2.intro.alpha - section23_2.intro.beta)
  nonrandomCommonScale_statement : Prop
  nonrandomCommonScale : nonrandomCommonScale_statement
  limitSymmetricAboutZero_statement : Prop
  limitSymmetricAboutZero : limitSymmetricAboutZero_statement
  efronOneSidedCoverage_statement : Prop
  efronOneSidedCoverage : efronOneSidedCoverage_statement
  efronPercentileConsistency :
    vaart1998_confidenceIntervalAsymptoticConsistency
      P
      (vaart1998_efronLowerEndpointFromCenteredQuantile
        section23_2.intro.estimator section23_2.intro.bootstrapQuantile
        section23_2.intro.beta)
      (vaart1998_efronUpperEndpointFromCenteredQuantile
        section23_2.intro.estimator section23_2.intro.bootstrapQuantile
        section23_2.intro.alpha)
      section23_2.intro.theta
      (1 - section23_2.intro.alpha - section23_2.intro.beta)

namespace Vaart1998Lemma23_3BootstrapConfidenceConsistencySource

theorem true_studentized_weak_limit
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S :
      Vaart1998Lemma23_3BootstrapConfidenceConsistencySource
        (ΩBootstrap := ΩBootstrap)
        (SampleSpace := SampleSpace) (Parameter := Parameter)
        P LimitLaw) :
    TendstoInDistribution
      S.section23_2.intro.trueStudentizedStatistic atTop
      S.limitStatistic P LimitLaw :=
  S.trueStudentizedWeakLimit

theorem conditional_bootstrap_weak_limit
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S :
      Vaart1998Lemma23_3BootstrapConfidenceConsistencySource
        (ΩBootstrap := ΩBootstrap)
        (SampleSpace := SampleSpace) (Parameter := Parameter)
        P LimitLaw) :
    S.conditionalBootstrapWeakLimit_statement :=
  S.conditionalBootstrapWeakLimit

theorem bootstrap_quantile_alpha_tendsto
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S :
      Vaart1998Lemma23_3BootstrapConfidenceConsistencySource
        (ΩBootstrap := ΩBootstrap)
        (SampleSpace := SampleSpace) (Parameter := Parameter)
        P LimitLaw) :
    vaart1998_bootstrapQuantileConvergesInProbability
      P S.section23_2.intro.bootstrapQuantile
      S.section23_2.limitCdf S.section23_2.intro.alpha :=
  S.bootstrapQuantile_alpha_tendsto

theorem bootstrap_quantile_beta_tendsto
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S :
      Vaart1998Lemma23_3BootstrapConfidenceConsistencySource
        (ΩBootstrap := ΩBootstrap)
        (SampleSpace := SampleSpace) (Parameter := Parameter)
        P LimitLaw) :
    vaart1998_bootstrapQuantileConvergesInProbability
      P S.section23_2.intro.bootstrapQuantile
      S.section23_2.limitCdf S.section23_2.intro.beta :=
  S.bootstrapQuantile_beta_tendsto

theorem percentile_t_consistency
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S :
      Vaart1998Lemma23_3BootstrapConfidenceConsistencySource
        (ΩBootstrap := ΩBootstrap)
        (SampleSpace := SampleSpace) (Parameter := Parameter)
        P LimitLaw) :
    vaart1998_confidenceIntervalAsymptoticConsistency
      P
      (vaart1998_percentileTLowerEndpoint
        S.section23_2.intro.estimator
        S.section23_2.intro.scaleEstimator
        S.section23_2.intro.bootstrapQuantile
        S.section23_2.intro.beta)
      (vaart1998_percentileTUpperEndpoint
        S.section23_2.intro.estimator
        S.section23_2.intro.scaleEstimator
        S.section23_2.intro.bootstrapQuantile
        (1 - S.section23_2.intro.alpha))
      S.section23_2.intro.theta
      (1 - S.section23_2.intro.alpha -
        S.section23_2.intro.beta) :=
  S.percentileTConsistency

theorem efron_percentile_consistency
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S :
      Vaart1998Lemma23_3BootstrapConfidenceConsistencySource
        (ΩBootstrap := ΩBootstrap)
        (SampleSpace := SampleSpace) (Parameter := Parameter)
        P LimitLaw) :
    vaart1998_confidenceIntervalAsymptoticConsistency
      P
      (vaart1998_efronLowerEndpointFromCenteredQuantile
        S.section23_2.intro.estimator
        S.section23_2.intro.bootstrapQuantile
        S.section23_2.intro.beta)
      (vaart1998_efronUpperEndpointFromCenteredQuantile
        S.section23_2.intro.estimator
        S.section23_2.intro.bootstrapQuantile
        S.section23_2.intro.alpha)
      S.section23_2.intro.theta
      (1 - S.section23_2.intro.alpha -
        S.section23_2.intro.beta) :=
  S.efronPercentileConsistency

end Vaart1998Lemma23_3BootstrapConfidenceConsistencySource

/-- Vector sample mean `n⁻¹ ∑ᵢ X_i`, coordinate by coordinate. -/
def vaart1998_vectorSampleMean
    {Ω Coordinate : Type*}
    (observation : ℕ -> Ω -> Coordinate -> ℝ)
    (n : ℕ) (ω : Ω) : Coordinate -> ℝ :=
  fun coordinate =>
    (n : ℝ)⁻¹ *
      ∑ i ∈ Finset.Icc 1 n, observation i ω coordinate

/-- Bootstrap vector sample mean `n⁻¹ ∑ᵢ X_i^*`, conditional on the
original observation sequence. -/
def vaart1998_bootstrapVectorSampleMean
    {Ω ΩBootstrap Coordinate : Type*}
    (bootstrapObservation :
      ℕ -> ℕ -> Ω -> ΩBootstrap -> Coordinate -> ℝ)
    (n : ℕ) (ω : Ω) (ωBootstrap : ΩBootstrap) :
    Coordinate -> ℝ :=
  fun coordinate =>
    (n : ℝ)⁻¹ *
      ∑ i ∈ Finset.Icc 1 n,
        bootstrapObservation n i ω ωBootstrap coordinate

/-- Centered and `√n`-scaled vector sample mean. -/
def vaart1998_centeredScaledVectorSampleMean
    {Ω Coordinate : Type*}
    (sampleMean : ℕ -> Ω -> Coordinate -> ℝ)
    (populationMean : Coordinate -> ℝ)
    (n : ℕ) (ω : Ω) : Coordinate -> ℝ :=
  fun coordinate =>
    √(n : ℝ) * (sampleMean n ω coordinate - populationMean coordinate)

/-- Centered and `√n`-scaled bootstrap vector sample mean. -/
def vaart1998_centeredScaledBootstrapVectorSampleMean
    {Ω ΩBootstrap Coordinate : Type*}
    (bootstrapSampleMean : ℕ -> Ω -> ΩBootstrap -> Coordinate -> ℝ)
    (sampleMean : ℕ -> Ω -> Coordinate -> ℝ)
    (n : ℕ) (ω : Ω) (ωBootstrap : ΩBootstrap) :
    Coordinate -> ℝ :=
  fun coordinate =>
    √(n : ℝ) *
      (bootstrapSampleMean n ω ωBootstrap coordinate -
        sampleMean n ω coordinate)

/-- Empirical centered second-moment matrix
`n⁻¹ ∑ᵢ (X_i - \bar X_n)(X_i - \bar X_n)ᵀ`. -/
def vaart1998_empiricalCenteredOuterProductMean
    {Ω Coordinate : Type*}
    (observation : ℕ -> Ω -> Coordinate -> ℝ)
    (sampleMean : ℕ -> Ω -> Coordinate -> ℝ)
    (n : ℕ) (ω : Ω) (j k : Coordinate) : ℝ :=
  (n : ℝ)⁻¹ *
    ∑ i ∈ Finset.Icc 1 n,
      (observation i ω j - sampleMean n ω j) *
        (observation i ω k - sampleMean n ω k)

/-- Empirical covariance display
`\overline{X_n X_nᵀ} - \bar X_n \bar X_nᵀ`. -/
def vaart1998_empiricalSecondMomentMinusMeanOuter
    {Ω Coordinate : Type*}
    (observation : ℕ -> Ω -> Coordinate -> ℝ)
    (sampleMean : ℕ -> Ω -> Coordinate -> ℝ)
    (n : ℕ) (ω : Ω) (j k : Coordinate) : ℝ :=
  (n : ℝ)⁻¹ *
      ∑ i ∈ Finset.Icc 1 n,
        observation i ω j * observation i ω k -
    sampleMean n ω j * sampleMean n ω k

/-- Lindeberg tail term for the bootstrap sample-mean triangular-array CLT. -/
def vaart1998_bootstrapLindebergTerm
    {Ω Vector : Type*} [Norm Vector]
    (observation : ℕ -> Ω -> Vector)
    (epsilon : ℝ) (n : ℕ) (ω : Ω) : ℝ :=
  (n : ℝ)⁻¹ *
    ∑ i ∈ Finset.Icc 1 n,
      if ‖observation i ω‖ > epsilon * √(n : ℝ) then
        ‖observation i ω‖ ^ 2
      else
        0

/-- Fixed-threshold tail average dominating the Lindeberg term once
`epsilon * √n ≥ M`. -/
def vaart1998_bootstrapFixedTailAverage
    {Ω Vector : Type*} [Norm Vector]
    (observation : ℕ -> Ω -> Vector)
    (M : ℝ) (n : ℕ) (ω : Ω) : ℝ :=
  (n : ℝ)⁻¹ *
    ∑ i ∈ Finset.Icc 1 n,
      if ‖observation i ω‖ > M then
        ‖observation i ω‖ ^ 2
      else
        0

/--
Source package for van der Vaart 1998, Theorem 23.4, the empirical
bootstrap consistency of the sample mean.

The package deliberately reuses the Chapter 4 finite-coordinate sample-mean
Gaussian source and records the new bootstrap-specific obligations:
conditional mean/covariance of the resampled observations, the strong-law
covariance limit, the triangular-array CLT handoff, and the Lindeberg
tail-average argument.
-/
structure Vaart1998Theorem23_4SampleMeanBootstrapSource
    {Ω ΩBootstrap ΩLimit Coordinate : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit]
    [Fintype Coordinate] [Norm (Coordinate -> ℝ)]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    (P : ℕ -> Measure Ω) [∀ n : ℕ, IsProbabilityMeasure (P n)]
    (LimitLaw : Measure ΩLimit) [IsProbabilityMeasure LimitLaw]
    (observationLaw : Measure (Coordinate -> ℝ))
    [IsProbabilityMeasure observationLaw] where
  /-- The population mean vector `μ`. -/
  populationMean : Coordinate -> ℝ
  /-- The covariance matrix `Σ`. -/
  covarianceMatrix : Coordinate -> Coordinate -> ℝ
  /-- Original observations `X_i`. -/
  observation : ℕ -> Ω -> Coordinate -> ℝ
  /-- Bootstrap observations `X_i^*`, sampled from the empirical law. -/
  bootstrapObservation :
    ℕ -> ℕ -> Ω -> ΩBootstrap -> Coordinate -> ℝ
  /-- Original sample mean `\bar X_n`. -/
  sampleMean : ℕ -> Ω -> Coordinate -> ℝ
  /-- Bootstrap sample mean `\bar X_n^*`. -/
  bootstrapSampleMean : ℕ -> Ω -> ΩBootstrap -> Coordinate -> ℝ
  /-- `√n(\bar X_n - μ)`. -/
  centeredScaledSampleMean : ℕ -> Ω -> Coordinate -> ℝ
  /-- `√n(\bar X_n^* - \bar X_n)`. -/
  centeredScaledBootstrapSampleMean :
    ℕ -> Ω -> ΩBootstrap -> Coordinate -> ℝ
  /-- The Gaussian limit vector `N(0, Σ)`. -/
  gaussianLimit : ΩLimit -> Coordinate -> ℝ
  /-- Reuse hook to the already-opened Chapter 4 sample-mean CLT source. -/
  chapter4SampleMeanSource :
    Vaart1998SampleMeanChapter4CanonicalSource
      (Q := LimitLaw) (observationLaw := observationLaw)
      (theta0 := populationMean) (Z := gaussianLimit)
  sampleMean_eq :
    sampleMean = vaart1998_vectorSampleMean observation
  bootstrapSampleMean_eq :
    bootstrapSampleMean =
      vaart1998_bootstrapVectorSampleMean bootstrapObservation
  centeredScaledSampleMean_eq :
    centeredScaledSampleMean =
      vaart1998_centeredScaledVectorSampleMean
        sampleMean populationMean
  centeredScaledBootstrapSampleMean_eq :
    centeredScaledBootstrapSampleMean =
      vaart1998_centeredScaledBootstrapVectorSampleMean
        bootstrapSampleMean sampleMean
  /-- Empirical bootstrap law `P_n = n⁻¹ ∑ᵢ δ_{X_i}`. -/
  empiricalBootstrapLaw : ℕ -> Ω -> Measure (Coordinate -> ℝ)
  empiricalBootstrapLaw_eq :
    ∀ n ω,
      empiricalBootstrapLaw n ω =
        vaart1998_empiricalBootstrapDistribution
          (fun _ i ω => observation i ω) n ω
  /-- Conditional mean of a bootstrap draw from the empirical law. -/
  conditionalMean : ℕ -> Ω -> Coordinate -> ℝ
  conditionalMean_eq_sampleMean :
    ∀ n ω, conditionalMean n ω = sampleMean n ω
  /-- Conditional covariance matrix of a bootstrap draw from the empirical law. -/
  conditionalCovariance :
    ℕ -> Ω -> Coordinate -> Coordinate -> ℝ
  conditionalCovariance_eq_centeredOuter :
    ∀ n ω j k,
      conditionalCovariance n ω j k =
        vaart1998_empiricalCenteredOuterProductMean
          observation sampleMean n ω j k
  conditionalCovariance_eq_secondMomentMinusMeanOuter :
    ∀ n ω j k,
      conditionalCovariance n ω j k =
        vaart1998_empiricalSecondMomentMinusMeanOuter
          observation sampleMean n ω j k
  conditionalCovariance_strongLaw_statement : Prop
  conditionalCovariance_strongLaw :
    conditionalCovariance_strongLaw_statement
  /-- Ordinary multivariate CLT for `√n(\bar X_n - μ)`. -/
  ordinaryCenteredSampleMean_clt :
    TendstoInDistribution
      centeredScaledSampleMean atTop gaussianLimit P LimitLaw
  triangularArrayCLT_statement : Prop
  triangularArrayCLT : triangularArrayCLT_statement
  /-- The displayed Lindeberg tail term. -/
  lindebergTerm : ℝ -> ℕ -> Ω -> ℝ
  lindebergTerm_eq :
    ∀ epsilon n ω,
      lindebergTerm epsilon n ω =
        vaart1998_bootstrapLindebergTerm observation epsilon n ω
  /-- Fixed-threshold tail average used to dominate the Lindeberg term. -/
  fixedTailAverage : ℝ -> ℕ -> Ω -> ℝ
  fixedTailAverage_eq :
    ∀ M n ω,
      fixedTailAverage M n ω =
        vaart1998_bootstrapFixedTailAverage observation M n ω
  lindeberg_tail_bound_statement : Prop
  lindeberg_tail_bound : lindeberg_tail_bound_statement
  strongLaw_tailAverage_statement : Prop
  strongLaw_tailAverage : strongLaw_tailAverage_statement
  lindeberg_condition_almostSure_statement : Prop
  lindeberg_condition_almostSure :
    lindeberg_condition_almostSure_statement
  conditionalBootstrapWeakLimit_statement : Prop
  conditionalBootstrapWeakLimit :
    conditionalBootstrapWeakLimit_statement
  /-- Handoff back to the pointwise bootstrap-CDF consistency display (23.2). -/
  section23_2_handoff_statement : Prop
  section23_2_handoff : section23_2_handoff_statement

namespace Vaart1998Theorem23_4SampleMeanBootstrapSource

theorem sample_mean_display
    {Ω ΩBootstrap ΩLimit Coordinate : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit]
    [Fintype Coordinate] [Norm (Coordinate -> ℝ)]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    {observationLaw : Measure (Coordinate -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    (S :
      Vaart1998Theorem23_4SampleMeanBootstrapSource
        (ΩBootstrap := ΩBootstrap)
        (Coordinate := Coordinate)
        P LimitLaw observationLaw) :
    S.sampleMean = vaart1998_vectorSampleMean S.observation :=
  S.sampleMean_eq

theorem bootstrap_sample_mean_display
    {Ω ΩBootstrap ΩLimit Coordinate : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit]
    [Fintype Coordinate] [Norm (Coordinate -> ℝ)]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    {observationLaw : Measure (Coordinate -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    (S :
      Vaart1998Theorem23_4SampleMeanBootstrapSource
        (ΩBootstrap := ΩBootstrap)
        (Coordinate := Coordinate)
        P LimitLaw observationLaw) :
    S.bootstrapSampleMean =
      vaart1998_bootstrapVectorSampleMean S.bootstrapObservation :=
  S.bootstrapSampleMean_eq

theorem centered_scaled_bootstrap_sample_mean_display
    {Ω ΩBootstrap ΩLimit Coordinate : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit]
    [Fintype Coordinate] [Norm (Coordinate -> ℝ)]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    {observationLaw : Measure (Coordinate -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    (S :
      Vaart1998Theorem23_4SampleMeanBootstrapSource
        (ΩBootstrap := ΩBootstrap)
        (Coordinate := Coordinate)
        P LimitLaw observationLaw) :
    S.centeredScaledBootstrapSampleMean =
      vaart1998_centeredScaledBootstrapVectorSampleMean
        S.bootstrapSampleMean S.sampleMean :=
  S.centeredScaledBootstrapSampleMean_eq

theorem empirical_bootstrap_law_display
    {Ω ΩBootstrap ΩLimit Coordinate : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit]
    [Fintype Coordinate] [Norm (Coordinate -> ℝ)]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    {observationLaw : Measure (Coordinate -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    (S :
      Vaart1998Theorem23_4SampleMeanBootstrapSource
        (ΩBootstrap := ΩBootstrap)
        (Coordinate := Coordinate)
        P LimitLaw observationLaw)
    (n : ℕ) (ω : Ω) :
    S.empiricalBootstrapLaw n ω =
      vaart1998_empiricalBootstrapDistribution
        (fun _ i ω => S.observation i ω) n ω :=
  S.empiricalBootstrapLaw_eq n ω

theorem conditional_mean_display
    {Ω ΩBootstrap ΩLimit Coordinate : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit]
    [Fintype Coordinate] [Norm (Coordinate -> ℝ)]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    {observationLaw : Measure (Coordinate -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    (S :
      Vaart1998Theorem23_4SampleMeanBootstrapSource
        (ΩBootstrap := ΩBootstrap)
        (Coordinate := Coordinate)
        P LimitLaw observationLaw)
    (n : ℕ) (ω : Ω) :
    S.conditionalMean n ω = S.sampleMean n ω :=
  S.conditionalMean_eq_sampleMean n ω

theorem conditional_covariance_centered_outer_display
    {Ω ΩBootstrap ΩLimit Coordinate : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit]
    [Fintype Coordinate] [Norm (Coordinate -> ℝ)]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    {observationLaw : Measure (Coordinate -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    (S :
      Vaart1998Theorem23_4SampleMeanBootstrapSource
        (ΩBootstrap := ΩBootstrap)
        (Coordinate := Coordinate)
        P LimitLaw observationLaw)
    (n : ℕ) (ω : Ω) (j k : Coordinate) :
    S.conditionalCovariance n ω j k =
      vaart1998_empiricalCenteredOuterProductMean
        S.observation S.sampleMean n ω j k :=
  S.conditionalCovariance_eq_centeredOuter n ω j k

theorem conditional_covariance_second_moment_display
    {Ω ΩBootstrap ΩLimit Coordinate : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit]
    [Fintype Coordinate] [Norm (Coordinate -> ℝ)]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    {observationLaw : Measure (Coordinate -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    (S :
      Vaart1998Theorem23_4SampleMeanBootstrapSource
        (ΩBootstrap := ΩBootstrap)
        (Coordinate := Coordinate)
        P LimitLaw observationLaw)
    (n : ℕ) (ω : Ω) (j k : Coordinate) :
    S.conditionalCovariance n ω j k =
      vaart1998_empiricalSecondMomentMinusMeanOuter
        S.observation S.sampleMean n ω j k :=
  S.conditionalCovariance_eq_secondMomentMinusMeanOuter n ω j k

theorem ordinary_sample_mean_clt
    {Ω ΩBootstrap ΩLimit Coordinate : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit]
    [Fintype Coordinate] [Norm (Coordinate -> ℝ)]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    {observationLaw : Measure (Coordinate -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    (S :
      Vaart1998Theorem23_4SampleMeanBootstrapSource
        (ΩBootstrap := ΩBootstrap)
        (Coordinate := Coordinate)
        P LimitLaw observationLaw) :
    TendstoInDistribution
      S.centeredScaledSampleMean atTop S.gaussianLimit P LimitLaw :=
  S.ordinaryCenteredSampleMean_clt

theorem lindeberg_term_display
    {Ω ΩBootstrap ΩLimit Coordinate : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit]
    [Fintype Coordinate] [Norm (Coordinate -> ℝ)]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    {observationLaw : Measure (Coordinate -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    (S :
      Vaart1998Theorem23_4SampleMeanBootstrapSource
        (ΩBootstrap := ΩBootstrap)
        (Coordinate := Coordinate)
        P LimitLaw observationLaw)
    (epsilon : ℝ) (n : ℕ) (ω : Ω) :
    S.lindebergTerm epsilon n ω =
      vaart1998_bootstrapLindebergTerm S.observation epsilon n ω :=
  S.lindebergTerm_eq epsilon n ω

theorem fixed_tail_average_display
    {Ω ΩBootstrap ΩLimit Coordinate : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit]
    [Fintype Coordinate] [Norm (Coordinate -> ℝ)]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    {observationLaw : Measure (Coordinate -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    (S :
      Vaart1998Theorem23_4SampleMeanBootstrapSource
        (ΩBootstrap := ΩBootstrap)
        (Coordinate := Coordinate)
        P LimitLaw observationLaw)
    (M : ℝ) (n : ℕ) (ω : Ω) :
    S.fixedTailAverage M n ω =
      vaart1998_bootstrapFixedTailAverage S.observation M n ω :=
  S.fixedTailAverage_eq M n ω

theorem lindeberg_condition_almostSure_source
    {Ω ΩBootstrap ΩLimit Coordinate : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit]
    [Fintype Coordinate] [Norm (Coordinate -> ℝ)]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    {observationLaw : Measure (Coordinate -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    (S :
      Vaart1998Theorem23_4SampleMeanBootstrapSource
        (ΩBootstrap := ΩBootstrap)
        (Coordinate := Coordinate)
        P LimitLaw observationLaw) :
    S.lindeberg_condition_almostSure_statement :=
  S.lindeberg_condition_almostSure

theorem conditional_bootstrap_weak_limit_source
    {Ω ΩBootstrap ΩLimit Coordinate : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit]
    [Fintype Coordinate] [Norm (Coordinate -> ℝ)]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    {observationLaw : Measure (Coordinate -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    (S :
      Vaart1998Theorem23_4SampleMeanBootstrapSource
        (ΩBootstrap := ΩBootstrap)
        (Coordinate := Coordinate)
        P LimitLaw observationLaw) :
    S.conditionalBootstrapWeakLimit_statement :=
  S.conditionalBootstrapWeakLimit

theorem section23_2_handoff_source
    {Ω ΩBootstrap ΩLimit Coordinate : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit]
    [Fintype Coordinate] [Norm (Coordinate -> ℝ)]
    [MeasurableSpace (Coordinate -> ℝ)]
    [PseudoMetricSpace (Coordinate -> ℝ)]
    [SecondCountableTopology (Coordinate -> ℝ)]
    [BorelSpace (Coordinate -> ℝ)]
    [OpensMeasurableSpace (Coordinate -> ℝ)]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    {observationLaw : Measure (Coordinate -> ℝ)}
    [IsProbabilityMeasure observationLaw]
    (S :
      Vaart1998Theorem23_4SampleMeanBootstrapSource
        (ΩBootstrap := ΩBootstrap)
        (Coordinate := Coordinate)
        P LimitLaw observationLaw) :
    S.section23_2_handoff_statement :=
  S.section23_2_handoff

end Vaart1998Theorem23_4SampleMeanBootstrapSource

/-- Delta-method transformed statistic `r_n (phi(T_n) - phi(theta))`. -/
def vaart1998_deltaTransformedStatistic
    {Ω D E : Type*} [Sub E] [SMul ℝ E]
    (phi : D -> E) (statistic : ℕ -> Ω -> D)
    (theta : D) (rate : ℕ -> ℝ) (n : ℕ) (ω : Ω) : E :=
  rate n • (phi (statistic n ω) - phi theta)

/-- Bootstrap delta-method transformed statistic
`r_n (phi(T_n^*) - phi(T_n))`. -/
def vaart1998_bootstrapDeltaTransformedStatistic
    {Ω ΩBootstrap D E : Type*} [Sub E] [SMul ℝ E]
    (phi : D -> E)
    (bootstrapStatistic : ℕ -> Ω -> ΩBootstrap -> D)
    (statistic : ℕ -> Ω -> D)
    (rate : ℕ -> ℝ) (n : ℕ) (ω : Ω)
    (ωBootstrap : ΩBootstrap) : E :=
  rate n •
    (phi (bootstrapStatistic n ω ωBootstrap) - phi (statistic n ω))

/-- Bootstrap delta-method input `r_n (T_n^* - T_n)`. -/
def vaart1998_bootstrapDeltaScaledInput
    {Ω ΩBootstrap D : Type*} [Sub D] [SMul ℝ D]
    (bootstrapStatistic : ℕ -> Ω -> ΩBootstrap -> D)
    (statistic : ℕ -> Ω -> D)
    (rate : ℕ -> ℝ) (n : ℕ) (ω : Ω)
    (ωBootstrap : ΩBootstrap) : D :=
  rate n • (bootstrapStatistic n ω ωBootstrap - statistic n ω)

/-- Linearized bootstrap delta-method statistic
`phi'_theta (r_n (T_n^* - T_n))`. -/
def vaart1998_bootstrapDeltaLinearizedStatistic
    {Ω ΩBootstrap D E : Type*} [NormedAddCommGroup D]
    [NormedSpace ℝ D] [NormedAddCommGroup E] [NormedSpace ℝ E]
    (derivative : D →L[ℝ] E)
    (bootstrapStatistic : ℕ -> Ω -> ΩBootstrap -> D)
    (statistic : ℕ -> Ω -> D)
    (rate : ℕ -> ℝ) (n : ℕ) (ω : Ω)
    (ωBootstrap : ΩBootstrap) : E :=
  derivative
    (vaart1998_bootstrapDeltaScaledInput
      bootstrapStatistic statistic rate n ω ωBootstrap)

/-- Bootstrap delta-method remainder after subtracting the linearized term. -/
def vaart1998_bootstrapDeltaRemainder
    {Ω ΩBootstrap D E : Type*} [NormedAddCommGroup D]
    [NormedSpace ℝ D] [NormedAddCommGroup E] [NormedSpace ℝ E]
    (phi : D -> E) (derivative : D →L[ℝ] E)
    (bootstrapStatistic : ℕ -> Ω -> ΩBootstrap -> D)
    (statistic : ℕ -> Ω -> D)
    (rate : ℕ -> ℝ) (n : ℕ) (ω : Ω)
    (ωBootstrap : ΩBootstrap) : E :=
  rate n •
    (phi (bootstrapStatistic n ω ωBootstrap) - phi (statistic n ω) -
      derivative (bootstrapStatistic n ω ωBootstrap - statistic n ω))

/-- Bootstrap remainder tail event `{R_n > epsilon}`. -/
def vaart1998_bootstrapDeltaRemainderTailEvent
    {Ω ΩBootstrap E : Type*} [Norm E]
    (remainder : ℕ -> Ω -> ΩBootstrap -> E)
    (epsilon : ℝ) (n : ℕ) (ω : Ω) : Set ΩBootstrap :=
  {ωBootstrap | epsilon < ‖remainder n ω ωBootstrap‖}

/-- Bootstrap scaled-input tail event `{r_n ||T_n^* - T_n|| > M}`. -/
def vaart1998_bootstrapDeltaInputTailEvent
    {Ω ΩBootstrap D : Type*} [Norm D]
    (scaledInput : ℕ -> Ω -> ΩBootstrap -> D)
    (M : ℝ) (n : ℕ) (ω : Ω) : Set ΩBootstrap :=
  {ωBootstrap | M < ‖scaledInput n ω ωBootstrap‖}

/-- Original statistic outside a `delta`-neighborhood of `theta`. -/
def vaart1998_deltaEstimatorOutsideNeighborhoodEvent
    {Ω D : Type*} [Sub D] [Norm D]
    (statistic : ℕ -> Ω -> D) (theta : D)
    (delta : ℝ) (n : ℕ) : Set Ω :=
  {ω | delta < ‖statistic n ω - theta‖}

/-- Conditional real probability under a bootstrap law. -/
def vaart1998_bootstrapConditionalRealProbability
    {Ω ΩBootstrap : Type*} [MeasurableSpace ΩBootstrap]
    (bootstrapLaw : ℕ -> Ω -> Measure ΩBootstrap)
    (event : ℕ -> Ω -> Set ΩBootstrap)
    (n : ℕ) (ω : Ω) : ℝ :=
  (bootstrapLaw n ω).real (event n ω)

/--
Source package for van der Vaart 1998, Theorem 23.5, the delta method for
bootstrap.

The ordinary transformed weak limit reuses the compiled Chapter 20
Fréchet-delta source.  The bootstrap half records the conditional weak-limit
assumption, the mean-value/local-derivative remainder control, the conditional
Slutsky handoff, and the final conditional transformed weak limit.
-/
structure Vaart1998Theorem23_5BootstrapDeltaMethodSource
    {Ω ΩBootstrap ΩLimit D E : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit]
    [NormedAddCommGroup D] [NormedSpace ℝ D]
    [MeasurableSpace D] [SecondCountableTopology D] [BorelSpace D]
    [OpensMeasurableSpace D] [CompleteSpace D]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    (P : Measure Ω) [IsProbabilityMeasure P]
    (LimitLaw : Measure ΩLimit) [IsProbabilityMeasure LimitLaw] where
  /-- The differentiable map `phi`. -/
  phi : D -> E
  /-- The centering point `theta`. -/
  theta : D
  /-- The derivative `phi'_theta`. -/
  derivative : D →L[ℝ] E
  /-- Original statistic `thetaHat_n`. -/
  statistic : ℕ -> Ω -> D
  /-- Bootstrap statistic `thetaHat_n^*`. -/
  bootstrapStatistic : ℕ -> Ω -> ΩBootstrap -> D
  /-- Limit random element `T`. -/
  limitProcess : ΩLimit -> D
  /-- Rate, equal to `√n` in the displayed theorem. -/
  rate : ℕ -> ℝ
  /-- Conditional bootstrap law given the original observations. -/
  bootstrapLaw : ℕ -> Ω -> Measure ΩBootstrap
  /-- Original transformed statistic `r_n(phi(thetaHat_n)-phi(theta))`. -/
  transformedStatistic : ℕ -> Ω -> E
  /-- Bootstrap transformed statistic
  `r_n(phi(thetaHat_n^*)-phi(thetaHat_n))`. -/
  bootstrapTransformedStatistic : ℕ -> Ω -> ΩBootstrap -> E
  /-- Bootstrap input `r_n(thetaHat_n^* - thetaHat_n)`. -/
  bootstrapScaledInput : ℕ -> Ω -> ΩBootstrap -> D
  /-- Linearized bootstrap statistic `phi'_theta(r_n(thetaHat_n^*-thetaHat_n))`. -/
  bootstrapLinearizedStatistic : ℕ -> Ω -> ΩBootstrap -> E
  /-- Bootstrap delta-method remainder. -/
  bootstrapRemainder : ℕ -> Ω -> ΩBootstrap -> E
  transformedStatistic_eq :
    transformedStatistic =
      vaart1998_deltaTransformedStatistic
        (Ω := Ω) (D := D) (E := E) phi statistic theta rate
  bootstrapTransformedStatistic_eq :
    bootstrapTransformedStatistic =
      vaart1998_bootstrapDeltaTransformedStatistic
        (Ω := Ω) (ΩBootstrap := ΩBootstrap) (D := D) (E := E)
        phi bootstrapStatistic statistic rate
  bootstrapScaledInput_eq :
    bootstrapScaledInput =
      vaart1998_bootstrapDeltaScaledInput
        (Ω := Ω) (ΩBootstrap := ΩBootstrap) (D := D)
        bootstrapStatistic statistic rate
  bootstrapLinearizedStatistic_eq :
    bootstrapLinearizedStatistic =
      vaart1998_bootstrapDeltaLinearizedStatistic
        (Ω := Ω) (ΩBootstrap := ΩBootstrap) (D := D) (E := E)
        derivative bootstrapStatistic statistic rate
  bootstrapRemainder_eq :
    bootstrapRemainder =
      vaart1998_bootstrapDeltaRemainder
        (Ω := Ω) (ΩBootstrap := ΩBootstrap) (D := D) (E := E)
        phi derivative bootstrapStatistic statistic rate
  /-- Compiled ordinary delta-method source from Chapter 20. -/
  ordinaryDeltaMethodSource :
    Vaart1998Theorem20_8FrechetDeltaSource
      (Ω := Ω) (Ω' := ΩLimit) (D := D) (E := E)
      (P := P) (Q := LimitLaw)
  ordinaryDeltaMethodSource_phi_eq :
    ordinaryDeltaMethodSource.phi = phi
  ordinaryDeltaMethodSource_theta_eq :
    ordinaryDeltaMethodSource.theta = theta
  ordinaryDeltaMethodSource_derivative_eq :
    ordinaryDeltaMethodSource.derivative = derivative
  ordinaryDeltaMethodSource_statistic_eq :
    ordinaryDeltaMethodSource.statistic = statistic
  ordinaryDeltaMethodSource_limitProcess_eq :
    ordinaryDeltaMethodSource.limitProcess = limitProcess
  ordinaryDeltaMethodSource_rate_eq :
    ordinaryDeltaMethodSource.rate = rate
  /-- Ordinary delta-method conclusion. -/
  ordinaryTransformedWeakLimit :
    TendstoInDistribution
      transformedStatistic atTop
      (fun ω => derivative (limitProcess ω))
      (fun _ : ℕ => P) LimitLaw
  /-- The bootstrap input has the same conditional weak limit `T`. -/
  conditionalBootstrapInputWeakLimit_statement : Prop
  conditionalBootstrapInputWeakLimit :
    conditionalBootstrapInputWeakLimit_statement
  /-- `thetaHat_n -> theta` almost surely. -/
  statisticAlmostSureConverges_statement : Prop
  statisticAlmostSureConverges :
    statisticAlmostSureConverges_statement
  /-- The map is continuously differentiable in a neighborhood of `theta`. -/
  continuouslyDifferentiableNeighborhood_statement : Prop
  continuouslyDifferentiableNeighborhood :
    continuouslyDifferentiableNeighborhood_statement
  /-- Mean-value expansion along the segment from `thetaHat_n` to
  `thetaHat_n^*`. -/
  meanValueExpansion_statement : Prop
  meanValueExpansion : meanValueExpansion_statement
  /-- Local derivative-continuity bound used in the proof. -/
  derivativeContinuityBound_statement : Prop
  derivativeContinuityBound : derivativeContinuityBound_statement
  /-- On the local/tight event, the bootstrap remainder is at most `eta * M`. -/
  remainderBoundOnLocalTightEvent_statement : Prop
  remainderBoundOnLocalTightEvent :
    remainderBoundOnLocalTightEvent_statement
  /-- Conditional tail bound for the bootstrap remainder by the tightness and
  consistency tails. -/
  conditionalRemainderTailBound_statement : Prop
  conditionalRemainderTailBound :
    conditionalRemainderTailBound_statement
  /-- The conditional bootstrap input is tight. -/
  conditionalBootstrapInputTight_statement : Prop
  conditionalBootstrapInputTight :
    conditionalBootstrapInputTight_statement
  /-- The large-`M` limit tail of `||T||` can be made arbitrarily small. -/
  limitTailSmall_largeM_statement : Prop
  limitTailSmall_largeM : limitTailSmall_largeM_statement
  /-- The bootstrap remainder is conditionally negligible. -/
  bootstrapRemainderConditionallyNegligible_statement : Prop
  bootstrapRemainderConditionallyNegligible :
    bootstrapRemainderConditionallyNegligible_statement
  /-- Conditional weak convergence of the linearized bootstrap statistic. -/
  bootstrapLinearizedWeakLimit_statement : Prop
  bootstrapLinearizedWeakLimit :
    bootstrapLinearizedWeakLimit_statement
  /-- Conditional Slutsky handoff from linearized statistic plus negligible
  remainder to the transformed bootstrap statistic. -/
  conditionalSlutskyHandoff_statement : Prop
  conditionalSlutskyHandoff : conditionalSlutskyHandoff_statement
  /-- Final conditional bootstrap delta-method conclusion. -/
  bootstrapTransformedWeakLimit_statement : Prop
  bootstrapTransformedWeakLimit :
    bootstrapTransformedWeakLimit_statement
  /-- Handoff back to Section 23.2 consistency for transformed statistics. -/
  section23_2_handoff_statement : Prop
  section23_2_handoff : section23_2_handoff_statement

namespace Vaart1998Theorem23_5BootstrapDeltaMethodSource

section

variable {Ω ΩBootstrap ΩLimit D E : Type*}
variable [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
variable [MeasurableSpace ΩLimit]
variable [NormedAddCommGroup D] [NormedSpace ℝ D]
variable [MeasurableSpace D] [SecondCountableTopology D] [BorelSpace D]
variable [OpensMeasurableSpace D] [CompleteSpace D]
variable [NormedAddCommGroup E] [NormedSpace ℝ E]
variable [MeasurableSpace E] [SecondCountableTopology E] [BorelSpace E]
variable [OpensMeasurableSpace E]
variable {P : Measure Ω} [IsProbabilityMeasure P]
variable {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
variable (S :
  Vaart1998Theorem23_5BootstrapDeltaMethodSource
    (Ω := Ω) (ΩBootstrap := ΩBootstrap) (ΩLimit := ΩLimit)
    (D := D) (E := E) P LimitLaw)

theorem transformed_statistic_display :
    S.transformedStatistic =
      vaart1998_deltaTransformedStatistic
        (Ω := Ω) (D := D) (E := E)
        S.phi S.statistic S.theta S.rate :=
  S.transformedStatistic_eq

theorem bootstrap_transformed_statistic_display :
    S.bootstrapTransformedStatistic =
      vaart1998_bootstrapDeltaTransformedStatistic
        (Ω := Ω) (ΩBootstrap := ΩBootstrap) (D := D) (E := E)
        S.phi S.bootstrapStatistic S.statistic S.rate :=
  S.bootstrapTransformedStatistic_eq

theorem bootstrap_scaled_input_display :
    S.bootstrapScaledInput =
      vaart1998_bootstrapDeltaScaledInput
        (Ω := Ω) (ΩBootstrap := ΩBootstrap) (D := D)
        S.bootstrapStatistic S.statistic S.rate :=
  S.bootstrapScaledInput_eq

theorem bootstrap_linearized_statistic_display :
    S.bootstrapLinearizedStatistic =
      vaart1998_bootstrapDeltaLinearizedStatistic
        (Ω := Ω) (ΩBootstrap := ΩBootstrap) (D := D) (E := E)
        S.derivative S.bootstrapStatistic S.statistic S.rate :=
  S.bootstrapLinearizedStatistic_eq

theorem bootstrap_remainder_display :
    S.bootstrapRemainder =
      vaart1998_bootstrapDeltaRemainder
        (Ω := Ω) (ΩBootstrap := ΩBootstrap) (D := D) (E := E)
        S.phi S.derivative S.bootstrapStatistic S.statistic S.rate :=
  S.bootstrapRemainder_eq

def ordinary_delta_method_source :
    Vaart1998Theorem20_8FrechetDeltaSource
      (Ω := Ω) (Ω' := ΩLimit) (D := D) (E := E)
      (P := P) (Q := LimitLaw) :=
  S.ordinaryDeltaMethodSource

theorem ordinary_transformed_weak_limit :
    TendstoInDistribution
      S.transformedStatistic atTop
      (fun ω => S.derivative (S.limitProcess ω))
      (fun _ : ℕ => P) LimitLaw :=
  S.ordinaryTransformedWeakLimit

theorem conditional_bootstrap_input_weak_limit :
    S.conditionalBootstrapInputWeakLimit_statement :=
  S.conditionalBootstrapInputWeakLimit

theorem statistic_almost_sure_converges :
    S.statisticAlmostSureConverges_statement :=
  S.statisticAlmostSureConverges

theorem derivative_continuity_bound :
    S.derivativeContinuityBound_statement :=
  S.derivativeContinuityBound

theorem conditional_remainder_tail_bound :
    S.conditionalRemainderTailBound_statement :=
  S.conditionalRemainderTailBound

theorem bootstrap_remainder_conditionally_negligible :
    S.bootstrapRemainderConditionallyNegligible_statement :=
  S.bootstrapRemainderConditionallyNegligible

theorem bootstrap_linearized_weak_limit :
    S.bootstrapLinearizedWeakLimit_statement :=
  S.bootstrapLinearizedWeakLimit

theorem conditional_slutsky_handoff :
    S.conditionalSlutskyHandoff_statement :=
  S.conditionalSlutskyHandoff

theorem bootstrap_transformed_weak_limit :
    S.bootstrapTransformedWeakLimit_statement :=
  S.bootstrapTransformedWeakLimit

theorem section23_2_handoff_source :
    S.section23_2_handoff_statement :=
  S.section23_2_handoff

end

end Vaart1998Theorem23_5BootstrapDeltaMethodSource

/-- Scalar sample mean `n⁻¹ ∑ᵢ X_i`. -/
def vaart1998_scalarSampleMean
    {Ω : Type*} (observation : ℕ -> Ω -> ℝ)
    (n : ℕ) (ω : Ω) : ℝ :=
  (n : ℝ)⁻¹ * ∑ i ∈ Finset.Icc 1 n, observation i ω

/-- Scalar empirical second moment `n⁻¹ ∑ᵢ X_i^2`. -/
def vaart1998_scalarEmpiricalSecondMoment
    {Ω : Type*} (observation : ℕ -> Ω -> ℝ)
    (n : ℕ) (ω : Ω) : ℝ :=
  (n : ℝ)⁻¹ * ∑ i ∈ Finset.Icc 1 n, (observation i ω) ^ 2

/-- Biased sample variance `S_n^2 = n⁻¹ ∑ᵢ (X_i - \bar X_n)^2`. -/
def vaart1998_biasedSampleVariance
    {Ω : Type*} (observation sampleMean : ℕ -> Ω -> ℝ)
    (n : ℕ) (ω : Ω) : ℝ :=
  (n : ℝ)⁻¹ *
    ∑ i ∈ Finset.Icc 1 n, (observation i ω - sampleMean n ω) ^ 2

/-- Bootstrap scalar sample mean `n⁻¹ ∑ᵢ X_i^*`. -/
def vaart1998_bootstrapScalarSampleMean
    {Ω ΩBootstrap : Type*}
    (bootstrapObservation : ℕ -> ℕ -> Ω -> ΩBootstrap -> ℝ)
    (n : ℕ) (ω : Ω) (ωBootstrap : ΩBootstrap) : ℝ :=
  (n : ℝ)⁻¹ *
    ∑ i ∈ Finset.Icc 1 n,
      bootstrapObservation n i ω ωBootstrap

/-- Bootstrap scalar empirical second moment `n⁻¹ ∑ᵢ (X_i^*)^2`. -/
def vaart1998_bootstrapScalarEmpiricalSecondMoment
    {Ω ΩBootstrap : Type*}
    (bootstrapObservation : ℕ -> ℕ -> Ω -> ΩBootstrap -> ℝ)
    (n : ℕ) (ω : Ω) (ωBootstrap : ΩBootstrap) : ℝ :=
  (n : ℝ)⁻¹ *
    ∑ i ∈ Finset.Icc 1 n,
      (bootstrapObservation n i ω ωBootstrap) ^ 2

/-- Bootstrap biased sample variance
`S_n^{*2} = n⁻¹ ∑ᵢ (X_i^* - \bar X_n^*)^2`. -/
def vaart1998_bootstrapBiasedSampleVariance
    {Ω ΩBootstrap : Type*}
    (bootstrapObservation : ℕ -> ℕ -> Ω -> ΩBootstrap -> ℝ)
    (bootstrapSampleMean : ℕ -> Ω -> ΩBootstrap -> ℝ)
    (n : ℕ) (ω : Ω) (ωBootstrap : ΩBootstrap) : ℝ :=
  (n : ℝ)⁻¹ *
    ∑ i ∈ Finset.Icc 1 n,
      (bootstrapObservation n i ω ωBootstrap -
        bootstrapSampleMean n ω ωBootstrap) ^ 2

/-- Moment pair `(bar X_n, overline{X_n^2})`. -/
def vaart1998_sampleVarianceMomentPair
    {Ω : Type*} (sampleMean secondMoment : ℕ -> Ω -> ℝ)
    (n : ℕ) (ω : Ω) : ℝ × ℝ :=
  (sampleMean n ω, secondMoment n ω)

/-- Bootstrap moment pair `(bar X_n^*, overline{(X_n^*)^2})`. -/
def vaart1998_bootstrapSampleVarianceMomentPair
    {Ω ΩBootstrap : Type*}
    (bootstrapSampleMean bootstrapSecondMoment :
      ℕ -> Ω -> ΩBootstrap -> ℝ)
    (n : ℕ) (ω : Ω) (ωBootstrap : ΩBootstrap) : ℝ × ℝ :=
  (bootstrapSampleMean n ω ωBootstrap,
    bootstrapSecondMoment n ω ωBootstrap)

/-- Delta map for the biased sample variance:
`phi(x, y) = y - x^2`. -/
def vaart1998_sampleVarianceDeltaMap (z : ℝ × ℝ) : ℝ :=
  z.2 - z.1 ^ 2

/-- Derivative of the sample-variance delta map at first moment `alpha1`:
`(h₁, h₂) ↦ h₂ - 2 alpha1 h₁`. -/
def vaart1998_sampleVarianceDeltaDerivative
    (alpha1 : ℝ) : ℝ × ℝ →L[ℝ] ℝ :=
  ContinuousLinearMap.snd ℝ ℝ ℝ -
    (2 * alpha1) • ContinuousLinearMap.fst ℝ ℝ ℝ

/-- Displayed asymptotic-variance estimator `S_n^4 (k_n + 2)`, where the
input sample variance is the value denoted `S_n^2` in the text. -/
def vaart1998_sampleVarianceAsymptoticVarianceEstimator
    {Ω : Type*} (sampleVariance sampleKurtosis : ℕ -> Ω -> ℝ)
    (n : ℕ) (ω : Ω) : ℝ :=
  (sampleVariance n ω) ^ 2 * (sampleKurtosis n ω + 2)

/-- Bootstrap counterpart of the displayed variance estimator. -/
def vaart1998_bootstrapSampleVarianceAsymptoticVarianceEstimator
    {Ω ΩBootstrap : Type*}
    (bootstrapSampleVariance bootstrapSampleKurtosis :
      ℕ -> Ω -> ΩBootstrap -> ℝ)
    (n : ℕ) (ω : Ω) (ωBootstrap : ΩBootstrap) : ℝ :=
  (bootstrapSampleVariance n ω ωBootstrap) ^ 2 *
    (bootstrapSampleKurtosis n ω ωBootstrap + 2)

/-- Studentized sample-variance statistic from Example 23.6. -/
def vaart1998_sampleVarianceStudentizedStatistic
    {Ω : Type*} (sampleVariance sampleKurtosis : ℕ -> Ω -> ℝ)
    (sigmaSq : ℝ) (n : ℕ) (ω : Ω) : ℝ :=
  (sampleVariance n ω - sigmaSq) /
    (sampleVariance n ω * √(sampleKurtosis n ω + 1))

/-- Bootstrap studentized sample-variance statistic. -/
def vaart1998_bootstrapSampleVarianceStudentizedStatistic
    {Ω ΩBootstrap : Type*}
    (bootstrapSampleVariance : ℕ -> Ω -> ΩBootstrap -> ℝ)
    (sampleVariance : ℕ -> Ω -> ℝ)
    (bootstrapSampleKurtosis : ℕ -> Ω -> ΩBootstrap -> ℝ)
    (n : ℕ) (ω : Ω) (ωBootstrap : ΩBootstrap) : ℝ :=
  (bootstrapSampleVariance n ω ωBootstrap - sampleVariance n ω) /
    (bootstrapSampleVariance n ω ωBootstrap *
      √(bootstrapSampleKurtosis n ω ωBootstrap + 1))

/--
Source package for van der Vaart 1998, Example 23.6, sample variance.

The package records the identity
`S_n^2 = phi(\bar X_n, \overline{X_n^2})` with
`phi(x, y) = y - x^2`, the Theorem 23.4 bootstrap source for the two-moment
vector, the Theorem 23.5 bootstrap delta-method handoff, and the displayed
studentized variance-estimator route.
-/
structure Vaart1998Example23_6SampleVarianceBootstrapSource
    {Ω ΩBootstrap ΩMomentLimit ΩDeltaLimit : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩMomentLimit] [MeasurableSpace ΩDeltaLimit]
    (P : Measure Ω) [IsProbabilityMeasure P]
    (MomentLimitLaw : Measure ΩMomentLimit)
    [IsProbabilityMeasure MomentLimitLaw]
    (DeltaLimitLaw : Measure ΩDeltaLimit)
    [IsProbabilityMeasure DeltaLimitLaw]
    (momentObservationLaw : Measure (Fin 2 -> ℝ))
    [IsProbabilityMeasure momentObservationLaw] where
  /-- Original scalar observations `X_i`. -/
  observation : ℕ -> Ω -> ℝ
  /-- Bootstrap scalar observations `X_i^*`. -/
  bootstrapObservation : ℕ -> ℕ -> Ω -> ΩBootstrap -> ℝ
  /-- Original sample mean `\bar X_n`. -/
  sampleMean : ℕ -> Ω -> ℝ
  /-- Original empirical second moment `\overline{X_n^2}`. -/
  sampleSecondMoment : ℕ -> Ω -> ℝ
  /-- Biased sample variance `S_n^2`. -/
  sampleVariance : ℕ -> Ω -> ℝ
  /-- Bootstrap sample mean `\bar X_n^*`. -/
  bootstrapSampleMean : ℕ -> Ω -> ΩBootstrap -> ℝ
  /-- Bootstrap empirical second moment `\overline{(X_n^*)^2}`. -/
  bootstrapSecondMoment : ℕ -> Ω -> ΩBootstrap -> ℝ
  /-- Bootstrap biased sample variance `S_n^{*2}`. -/
  bootstrapSampleVariance : ℕ -> Ω -> ΩBootstrap -> ℝ
  /-- Moment vector for Theorem 23.4, indexed by `0` for `X` and `1` for `X^2`. -/
  momentVectorObservation : ℕ -> Ω -> Fin 2 -> ℝ
  /-- Bootstrap moment vector counterpart. -/
  bootstrapMomentVectorObservation :
    ℕ -> ℕ -> Ω -> ΩBootstrap -> Fin 2 -> ℝ
  /-- Moment-pair statistic used by the delta method. -/
  momentPair : ℕ -> Ω -> ℝ × ℝ
  /-- Bootstrap moment-pair statistic. -/
  bootstrapMomentPair : ℕ -> Ω -> ΩBootstrap -> ℝ × ℝ
  /-- First population moment `alpha_1`. -/
  alpha1 : ℝ
  /-- Second population moment `alpha_2`. -/
  alpha2 : ℝ
  /-- Population variance `sigma^2 = alpha_2 - alpha_1^2`. -/
  sigmaSq : ℝ
  /-- The delta map `phi(x, y) = y - x^2`. -/
  deltaMap : ℝ × ℝ -> ℝ
  /-- The derivative `(h₁, h₂) ↦ h₂ - 2 alpha_1 h₁`. -/
  deltaDerivative : ℝ × ℝ →L[ℝ] ℝ
  /-- Rate `√n` from the display. -/
  rate : ℕ -> ℝ
  /-- Original transformed variance statistic. -/
  transformedVarianceStatistic : ℕ -> Ω -> ℝ
  /-- Bootstrap transformed variance statistic. -/
  bootstrapTransformedVarianceStatistic :
    ℕ -> Ω -> ΩBootstrap -> ℝ
  /-- Sample kurtosis `k_n`. -/
  sampleKurtosis : ℕ -> Ω -> ℝ
  /-- Bootstrap sample kurtosis. -/
  bootstrapSampleKurtosis : ℕ -> Ω -> ΩBootstrap -> ℝ
  /-- Displayed estimator `S_n^4(k_n + 2)`. -/
  asymptoticVarianceEstimator : ℕ -> Ω -> ℝ
  /-- Bootstrap displayed variance estimator. -/
  bootstrapAsymptoticVarianceEstimator :
    ℕ -> Ω -> ΩBootstrap -> ℝ
  /-- Studentized statistic. -/
  studentizedStatistic : ℕ -> Ω -> ℝ
  /-- Bootstrap studentized statistic. -/
  bootstrapStudentizedStatistic :
    ℕ -> Ω -> ΩBootstrap -> ℝ
  sampleMean_eq :
    sampleMean = vaart1998_scalarSampleMean observation
  sampleSecondMoment_eq :
    sampleSecondMoment =
      vaart1998_scalarEmpiricalSecondMoment observation
  sampleVariance_eq :
    sampleVariance =
      vaart1998_biasedSampleVariance observation sampleMean
  bootstrapSampleMean_eq :
    bootstrapSampleMean =
      vaart1998_bootstrapScalarSampleMean bootstrapObservation
  bootstrapSecondMoment_eq :
    bootstrapSecondMoment =
      vaart1998_bootstrapScalarEmpiricalSecondMoment
        bootstrapObservation
  bootstrapSampleVariance_eq :
    bootstrapSampleVariance =
      vaart1998_bootstrapBiasedSampleVariance
        bootstrapObservation bootstrapSampleMean
  momentPair_eq :
    momentPair =
      vaart1998_sampleVarianceMomentPair
        sampleMean sampleSecondMoment
  bootstrapMomentPair_eq :
    bootstrapMomentPair =
      vaart1998_bootstrapSampleVarianceMomentPair
        bootstrapSampleMean bootstrapSecondMoment
  deltaMap_eq :
    deltaMap = vaart1998_sampleVarianceDeltaMap
  deltaDerivative_eq :
    deltaDerivative =
      vaart1998_sampleVarianceDeltaDerivative alpha1
  sigmaSq_eq :
    sigmaSq = deltaMap (alpha1, alpha2)
  sampleVariance_eq_deltaMap :
    ∀ n ω, sampleVariance n ω = deltaMap (momentPair n ω)
  bootstrapSampleVariance_eq_deltaMap :
    ∀ n ω ωBootstrap,
      bootstrapSampleVariance n ω ωBootstrap =
        deltaMap (bootstrapMomentPair n ω ωBootstrap)
  transformedVarianceStatistic_eq :
    transformedVarianceStatistic =
      vaart1998_deltaTransformedStatistic
        (Ω := Ω) (D := ℝ × ℝ) (E := ℝ)
        deltaMap momentPair (alpha1, alpha2) rate
  bootstrapTransformedVarianceStatistic_eq :
    bootstrapTransformedVarianceStatistic =
      vaart1998_bootstrapDeltaTransformedStatistic
        (Ω := Ω) (ΩBootstrap := ΩBootstrap) (D := ℝ × ℝ) (E := ℝ)
        deltaMap bootstrapMomentPair momentPair rate
  asymptoticVarianceEstimator_eq :
    asymptoticVarianceEstimator =
      vaart1998_sampleVarianceAsymptoticVarianceEstimator
        sampleVariance sampleKurtosis
  bootstrapAsymptoticVarianceEstimator_eq :
    bootstrapAsymptoticVarianceEstimator =
      vaart1998_bootstrapSampleVarianceAsymptoticVarianceEstimator
        bootstrapSampleVariance bootstrapSampleKurtosis
  studentizedStatistic_eq :
    studentizedStatistic =
      vaart1998_sampleVarianceStudentizedStatistic
        sampleVariance sampleKurtosis sigmaSq
  bootstrapStudentizedStatistic_eq :
    bootstrapStudentizedStatistic =
      vaart1998_bootstrapSampleVarianceStudentizedStatistic
        bootstrapSampleVariance sampleVariance bootstrapSampleKurtosis
  /-- The fourth-moment assumption needed for the two-moment CLT/bootstrap source. -/
  fourthMomentFinite_statement : Prop
  fourthMomentFinite : fourthMomentFinite_statement
  /-- Theorem 23.4 source applied to `(X, X^2)`. -/
  momentVectorBootstrapSource :
    Vaart1998Theorem23_4SampleMeanBootstrapSource
      (Ω := Ω) (ΩBootstrap := ΩBootstrap)
      (ΩLimit := ΩMomentLimit) (Coordinate := Fin 2)
      (fun _ : ℕ => P) MomentLimitLaw momentObservationLaw
  momentVectorBootstrapSource_observation_eq :
    momentVectorBootstrapSource.observation = momentVectorObservation
  momentVectorBootstrapSource_bootstrapObservation_eq :
    momentVectorBootstrapSource.bootstrapObservation =
      bootstrapMomentVectorObservation
  /-- Theorem 23.5 source applied to `phi(x, y) = y - x^2`. -/
  deltaMethodSource :
    Vaart1998Theorem23_5BootstrapDeltaMethodSource
      (Ω := Ω) (ΩBootstrap := ΩBootstrap)
      (ΩLimit := ΩDeltaLimit) (D := ℝ × ℝ) (E := ℝ)
      P DeltaLimitLaw
  deltaMethodSource_phi_eq :
    deltaMethodSource.phi = deltaMap
  deltaMethodSource_theta_eq :
    deltaMethodSource.theta = (alpha1, alpha2)
  deltaMethodSource_derivative_eq :
    deltaMethodSource.derivative = deltaDerivative
  deltaMethodSource_statistic_eq :
    deltaMethodSource.statistic = momentPair
  deltaMethodSource_bootstrapStatistic_eq :
    deltaMethodSource.bootstrapStatistic = bootstrapMomentPair
  deltaMethodSource_transformedStatistic_eq :
    deltaMethodSource.transformedStatistic =
      transformedVarianceStatistic
  deltaMethodSource_bootstrapTransformedStatistic_eq :
    deltaMethodSource.bootstrapTransformedStatistic =
      bootstrapTransformedVarianceStatistic
  /-- Empirical bootstrap consistency for `√n(S_n^{*2}-S_n^2)`. -/
  sampleVarianceBootstrapConsistency_statement : Prop
  sampleVarianceBootstrapConsistency :
    sampleVarianceBootstrapConsistency_statement
  /-- Kolmogorov display in Example 23.6. -/
  kolmogorovConsistency_statement : Prop
  kolmogorovConsistency : kolmogorovConsistency_statement
  /-- LLN consistency of `S_n^4(k_n + 2)`. -/
  asymptoticVarianceEstimator_consistent_statement : Prop
  asymptoticVarianceEstimator_consistent :
    asymptoticVarianceEstimator_consistent_statement
  /-- Bootstrap consistency of the variance estimator for a.e. original sequences. -/
  bootstrapAsymptoticVarianceEstimator_consistent_statement : Prop
  bootstrapAsymptoticVarianceEstimator_consistent :
    bootstrapAsymptoticVarianceEstimator_consistent_statement
  /-- Consistency of the studentized sample-variance bootstrap statistic. -/
  studentizedConsistency_statement : Prop
  studentizedConsistency : studentizedConsistency_statement

namespace Vaart1998Example23_6SampleVarianceBootstrapSource

section

variable {Ω ΩBootstrap ΩMomentLimit ΩDeltaLimit : Type*}
variable [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
variable [MeasurableSpace ΩMomentLimit] [MeasurableSpace ΩDeltaLimit]
variable {P : Measure Ω} [IsProbabilityMeasure P]
variable {MomentLimitLaw : Measure ΩMomentLimit}
variable [IsProbabilityMeasure MomentLimitLaw]
variable {DeltaLimitLaw : Measure ΩDeltaLimit}
variable [IsProbabilityMeasure DeltaLimitLaw]
variable {momentObservationLaw : Measure (Fin 2 -> ℝ)}
variable [IsProbabilityMeasure momentObservationLaw]
variable (S :
  Vaart1998Example23_6SampleVarianceBootstrapSource
    (Ω := Ω) (ΩBootstrap := ΩBootstrap)
    (ΩMomentLimit := ΩMomentLimit) (ΩDeltaLimit := ΩDeltaLimit)
    P MomentLimitLaw DeltaLimitLaw momentObservationLaw)

theorem sample_mean_display :
    S.sampleMean = vaart1998_scalarSampleMean S.observation :=
  S.sampleMean_eq

theorem sample_second_moment_display :
    S.sampleSecondMoment =
      vaart1998_scalarEmpiricalSecondMoment S.observation :=
  S.sampleSecondMoment_eq

theorem sample_variance_display :
    S.sampleVariance =
      vaart1998_biasedSampleVariance S.observation S.sampleMean :=
  S.sampleVariance_eq

theorem bootstrap_sample_variance_display :
    S.bootstrapSampleVariance =
      vaart1998_bootstrapBiasedSampleVariance
        S.bootstrapObservation S.bootstrapSampleMean :=
  S.bootstrapSampleVariance_eq

theorem moment_pair_display :
    S.momentPair =
      vaart1998_sampleVarianceMomentPair
        S.sampleMean S.sampleSecondMoment :=
  S.momentPair_eq

theorem bootstrap_moment_pair_display :
    S.bootstrapMomentPair =
      vaart1998_bootstrapSampleVarianceMomentPair
        S.bootstrapSampleMean S.bootstrapSecondMoment :=
  S.bootstrapMomentPair_eq

theorem delta_map_display :
    S.deltaMap = vaart1998_sampleVarianceDeltaMap :=
  S.deltaMap_eq

theorem sample_variance_delta_display
    (n : ℕ) (ω : Ω) :
    S.sampleVariance n ω = S.deltaMap (S.momentPair n ω) :=
  S.sampleVariance_eq_deltaMap n ω

theorem bootstrap_sample_variance_delta_display
    (n : ℕ) (ω : Ω) (ωBootstrap : ΩBootstrap) :
    S.bootstrapSampleVariance n ω ωBootstrap =
      S.deltaMap (S.bootstrapMomentPair n ω ωBootstrap) :=
  S.bootstrapSampleVariance_eq_deltaMap n ω ωBootstrap

def moment_vector_bootstrap_source :
    Vaart1998Theorem23_4SampleMeanBootstrapSource
      (Ω := Ω) (ΩBootstrap := ΩBootstrap)
      (ΩLimit := ΩMomentLimit) (Coordinate := Fin 2)
      (fun _ : ℕ => P) MomentLimitLaw momentObservationLaw :=
  S.momentVectorBootstrapSource

def delta_method_source :
    Vaart1998Theorem23_5BootstrapDeltaMethodSource
      (Ω := Ω) (ΩBootstrap := ΩBootstrap)
      (ΩLimit := ΩDeltaLimit) (D := ℝ × ℝ) (E := ℝ)
      P DeltaLimitLaw :=
  S.deltaMethodSource

theorem delta_method_bootstrap_consistency :
    S.deltaMethodSource.bootstrapTransformedWeakLimit_statement :=
  S.deltaMethodSource.bootstrapTransformedWeakLimit

theorem sample_variance_bootstrap_consistency :
    S.sampleVarianceBootstrapConsistency_statement :=
  S.sampleVarianceBootstrapConsistency

theorem kolmogorov_consistency :
    S.kolmogorovConsistency_statement :=
  S.kolmogorovConsistency

theorem asymptotic_variance_estimator_display :
    S.asymptoticVarianceEstimator =
      vaart1998_sampleVarianceAsymptoticVarianceEstimator
        S.sampleVariance S.sampleKurtosis :=
  S.asymptoticVarianceEstimator_eq

theorem studentized_statistic_display :
    S.studentizedStatistic =
      vaart1998_sampleVarianceStudentizedStatistic
        S.sampleVariance S.sampleKurtosis S.sigmaSq :=
  S.studentizedStatistic_eq

theorem studentized_consistency_source :
    S.studentizedConsistency_statement :=
  S.studentizedConsistency

end

end Vaart1998Example23_6SampleVarianceBootstrapSource

/-- Empirical law `P_n = n⁻¹ ∑ᵢ δ_{X_i}` from original observations. -/
def vaart1998_empiricalDistributionFromObservations
    {Ω Observation : Type*} [MeasurableSpace Observation]
    (observation : ℕ -> Ω -> Observation)
    (n : ℕ) (ω : Ω) : Measure Observation :=
  ((n : ℝ≥0∞)⁻¹) •
    ∑ i ∈ Finset.Icc 1 n, Measure.dirac (observation i ω)

/-- Bootstrap empirical law `P_n^* = n⁻¹ ∑ᵢ δ_{X_i^*}`. -/
def vaart1998_bootstrapEmpiricalDistributionFromObservations
    {Ω ΩBootstrap Observation : Type*} [MeasurableSpace Observation]
    (bootstrapObservation : ℕ -> ℕ -> Ω -> ΩBootstrap -> Observation)
    (n : ℕ) (ω : Ω) (ωBootstrap : ΩBootstrap) : Measure Observation :=
  ((n : ℝ≥0∞)⁻¹) •
    ∑ i ∈ Finset.Icc 1 n,
      Measure.dirac (bootstrapObservation n i ω ωBootstrap)

/-- Empirical class averages `P_n f`. -/
def vaart1998_empiricalClassAverageFromObservations
    {Ω Observation FunctionIndex : Type*}
    (observation : ℕ -> Ω -> Observation)
    (classFun : FunctionIndex -> Observation -> ℝ)
    (n : ℕ) (ω : Ω) (index : FunctionIndex) : ℝ :=
  (n : ℝ)⁻¹ *
    ∑ i ∈ Finset.Icc 1 n, classFun index (observation i ω)

/-- Bootstrap empirical class averages `P_n^* f`. -/
def vaart1998_bootstrapClassAverageFromObservations
    {Ω ΩBootstrap Observation FunctionIndex : Type*}
    (bootstrapObservation : ℕ -> ℕ -> Ω -> ΩBootstrap -> Observation)
    (classFun : FunctionIndex -> Observation -> ℝ)
    (n : ℕ) (ω : Ω) (ωBootstrap : ΩBootstrap)
    (index : FunctionIndex) : ℝ :=
  (n : ℝ)⁻¹ *
    ∑ i ∈ Finset.Icc 1 n,
      classFun index (bootstrapObservation n i ω ωBootstrap)

/-- Original empirical process `G_n f = sqrt n (P_n - P)f`. -/
def vaart1998_empiricalProcessFromClassAverages
    {Ω FunctionIndex : Type*}
    (empiricalAverage : ℕ -> Ω -> FunctionIndex -> ℝ)
    (populationAverage : FunctionIndex -> ℝ)
    (n : ℕ) (ω : Ω) (index : FunctionIndex) : ℝ :=
  √(n : ℝ) * (empiricalAverage n ω index - populationAverage index)

/-- Bootstrap empirical process `G_n^* f = sqrt n (P_n^* - P_n)f`. -/
def vaart1998_bootstrapEmpiricalProcessFromAverages
    {Ω ΩBootstrap FunctionIndex : Type*}
    (bootstrapAverage : ℕ -> Ω -> ΩBootstrap -> FunctionIndex -> ℝ)
    (empiricalAverage : ℕ -> Ω -> FunctionIndex -> ℝ)
    (n : ℕ) (ω : Ω) (ωBootstrap : ΩBootstrap)
    (index : FunctionIndex) : ℝ :=
  √(n : ℝ) *
    (bootstrapAverage n ω ωBootstrap index -
      empiricalAverage n ω index)

/-- Count-vector display
`G_n^* f = n^{-1/2} sum_i (M_{ni}-1) f(X_i)`. -/
def vaart1998_bootstrapEmpiricalProcessFromCounts
    {Ω ΩBootstrap Observation FunctionIndex : Type*}
    (observation : ℕ -> Ω -> Observation)
    (redrawCount : ℕ -> ℕ -> Ω -> ΩBootstrap -> ℝ)
    (classFun : FunctionIndex -> Observation -> ℝ)
    (n : ℕ) (ω : Ω) (ωBootstrap : ΩBootstrap)
    (index : FunctionIndex) : ℝ :=
  (√(n : ℝ))⁻¹ *
    ∑ i ∈ Finset.Icc 1 n,
      (redrawCount n i ω ωBootstrap - 1) *
        classFun index (observation i ω)

/-- Conditional expectation of a bootstrap process test function. -/
def vaart1998_conditionalBootstrapProcessTestExpectation
    {Ω ΩBootstrap Process : Type*} [MeasurableSpace ΩBootstrap]
    (bootstrapLaw : ℕ -> Ω -> Measure ΩBootstrap)
    (bootstrapProcess : ℕ -> Ω -> ΩBootstrap -> Process)
    (testFunction : Process -> ℝ)
    (n : ℕ) (ω : Ω) : ℝ :=
  ∫ ωBootstrap,
    testFunction (bootstrapProcess n ω ωBootstrap) ∂bootstrapLaw n ω

/-- Limit expectation of a process test function. -/
def vaart1998_limitProcessTestExpectation
    {ΩLimit Process : Type*} [MeasurableSpace ΩLimit]
    (LimitLaw : Measure ΩLimit)
    (limitProcess : ΩLimit -> Process)
    (testFunction : Process -> ℝ) : ℝ :=
  ∫ ω, testFunction (limitProcess ω) ∂LimitLaw

/-- Bounded-Lipschitz discrepancy used for conditional bootstrap convergence. -/
noncomputable def vaart1998_bootstrapBoundedLipschitzDiscrepancy
    {Ω Process : Type*}
    (boundedLipschitzClass : Set (Process -> ℝ))
    (conditionalExpectation : (Process -> ℝ) -> ℕ -> Ω -> ℝ)
    (limitExpectation : (Process -> ℝ) -> ℝ)
    (n : ℕ) (ω : Ω) : ℝ :=
  sSup
    ((fun testFunction : Process -> ℝ =>
      |conditionalExpectation testFunction n ω -
        limitExpectation testFunction|) '' boundedLipschitzClass)

/-- The BL discrepancy converges in probability to zero under the original law. -/
def vaart1998_bootstrapBoundedLipschitzConvergesInProbability
    {Ω : Type*} [MeasurableSpace Ω]
    (P : Measure Ω) [IsProbabilityMeasure P]
    (discrepancy : ℕ -> Ω -> ℝ) : Prop :=
  Vaart1998MeasureSeqConvergesInProbabilityToZero
    (fun _ : ℕ => P) discrepancy

/--
Source package for van der Vaart 1998, Theorem 23.7, the empirical bootstrap
for Donsker classes.

The package records the empirical-bootstrap law, the bootstrap empirical
process both as `sqrt n (P_n^*-P_n)` and through multinomial redraw counts,
the bounded-Lipschitz conditional convergence display, asymptotic
measurability, and the outer-a.s. strengthening under square-integrable
envelope assumptions.  The class-level Donsker input is tied back to the
Chapter 19 `DonskerBridgeCertificate`.
-/
structure Vaart1998Theorem23_7EmpiricalBootstrapSource
    {Ω ΩBootstrap ΩLimit Observation FunctionIndex : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace Observation]
    (P : Measure Ω) [IsProbabilityMeasure P]
    (LimitLaw : Measure ΩLimit) [IsProbabilityMeasure LimitLaw] where
  /-- Population law on the observation space. -/
  populationLaw : Measure Observation
  /-- Donsker function class. -/
  indexClass : Set FunctionIndex
  /-- Class functions `f : X -> R`. -/
  classFun : FunctionIndex -> Observation -> ℝ
  /-- Finite envelope function `F`. -/
  envelope : Observation -> ℝ
  /-- Original observations `X_i`. -/
  observation : ℕ -> Ω -> Observation
  /-- Bootstrap observations `X_i^*`. -/
  bootstrapObservation :
    ℕ -> ℕ -> Ω -> ΩBootstrap -> Observation
  /-- Multinomial redraw counts `M_{ni}`. -/
  redrawCount : ℕ -> ℕ -> Ω -> ΩBootstrap -> ℝ
  /-- Deterministic sample family used by the Chapter 19 Donsker bridge. -/
  samples : ∀ sampleSize, SampleAt Observation sampleSize
  /-- Original empirical law `P_n`. -/
  empiricalLaw : ℕ -> Ω -> Measure Observation
  /-- Bootstrap empirical law `P_n^*`. -/
  bootstrapEmpiricalLaw :
    ℕ -> Ω -> ΩBootstrap -> Measure Observation
  /-- Population class means `P f`. -/
  populationAverage : FunctionIndex -> ℝ
  /-- Original empirical class means `P_n f`. -/
  empiricalAverage : ℕ -> Ω -> FunctionIndex -> ℝ
  /-- Bootstrap empirical class means `P_n^* f`. -/
  bootstrapAverage :
    ℕ -> Ω -> ΩBootstrap -> FunctionIndex -> ℝ
  /-- Original empirical process `G_n`. -/
  empiricalProcess : ℕ -> Ω -> FunctionIndex -> ℝ
  /-- Bootstrap empirical process `G_n^*`. -/
  bootstrapEmpiricalProcess :
    ℕ -> Ω -> ΩBootstrap -> FunctionIndex -> ℝ
  /-- Count-vector display of `G_n^*`. -/
  countBootstrapEmpiricalProcess :
    ℕ -> Ω -> ΩBootstrap -> FunctionIndex -> ℝ
  /-- Brownian bridge limit `G_P`. -/
  brownianBridgeLimit : ΩLimit -> FunctionIndex -> ℝ
  /-- Conditional law for the bootstrap randomness. -/
  bootstrapLaw : ℕ -> Ω -> Measure ΩBootstrap
  /-- Bounded-Lipschitz unit ball on the process space. -/
  boundedLipschitzClass :
    Set ((FunctionIndex -> ℝ) -> ℝ)
  /-- Conditional expectation `E_M h(G_n^*)`. -/
  conditionalTestExpectation :
    ((FunctionIndex -> ℝ) -> ℝ) -> ℕ -> Ω -> ℝ
  /-- Limit expectation `E h(G_P)`. -/
  limitTestExpectation : ((FunctionIndex -> ℝ) -> ℝ) -> ℝ
  /-- Supremum over the bounded-Lipschitz unit ball. -/
  boundedLipschitzDiscrepancy : ℕ -> Ω -> ℝ
  empiricalLaw_eq :
    empiricalLaw =
      vaart1998_empiricalDistributionFromObservations observation
  bootstrapEmpiricalLaw_eq :
    bootstrapEmpiricalLaw =
      vaart1998_bootstrapEmpiricalDistributionFromObservations
        bootstrapObservation
  populationAverage_eq :
    populationAverage =
      vaart1998_populationClassMean populationLaw classFun
  empiricalAverage_eq :
    empiricalAverage =
      vaart1998_empiricalClassAverageFromObservations
        observation classFun
  bootstrapAverage_eq :
    bootstrapAverage =
      vaart1998_bootstrapClassAverageFromObservations
        bootstrapObservation classFun
  empiricalProcess_eq :
    empiricalProcess =
      vaart1998_empiricalProcessFromClassAverages
        empiricalAverage populationAverage
  bootstrapEmpiricalProcess_eq :
    bootstrapEmpiricalProcess =
      vaart1998_bootstrapEmpiricalProcessFromAverages
        bootstrapAverage empiricalAverage
  countBootstrapEmpiricalProcess_eq :
    countBootstrapEmpiricalProcess =
      vaart1998_bootstrapEmpiricalProcessFromCounts
        observation redrawCount classFun
  bootstrapEmpiricalProcess_eq_count :
    ∀ n ω ωBootstrap,
      bootstrapEmpiricalProcess n ω ωBootstrap =
        countBootstrapEmpiricalProcess n ω ωBootstrap
  conditionalTestExpectation_eq :
    conditionalTestExpectation =
      vaart1998_conditionalBootstrapProcessTestExpectation
        bootstrapLaw bootstrapEmpiricalProcess
  limitTestExpectation_eq :
    limitTestExpectation =
      vaart1998_limitProcessTestExpectation
        LimitLaw brownianBridgeLimit
  boundedLipschitzDiscrepancy_eq :
    boundedLipschitzDiscrepancy =
      vaart1998_bootstrapBoundedLipschitzDiscrepancy
        boundedLipschitzClass
        conditionalTestExpectation limitTestExpectation
  /-- The class has a finite envelope. -/
  finiteEnvelope_statement : Prop
  finiteEnvelope : finiteEnvelope_statement
  /-- Chapter 19 Donsker-class source. -/
  chapter19DonskerBridge :
    DonskerBridgeCertificate indexClass
      (vaart1998_populationClassMean populationLaw classFun)
      (vaart1998_empiricalClassMeanSequence samples classFun)
  /-- Conditional weak convergence route before taking BL suprema. -/
  conditionalWeakConvergence_statement : Prop
  conditionalWeakConvergence : conditionalWeakConvergence_statement
  /-- The displayed BL convergence in probability. -/
  boundedLipschitzConvergenceInProbability :
    vaart1998_bootstrapBoundedLipschitzConvergesInProbability
      P boundedLipschitzDiscrepancy
  /-- Asymptotic measurability of the bootstrap empirical process. -/
  asymptoticMeasurable_statement : Prop
  asymptoticMeasurable : asymptoticMeasurable_statement
  /-- The stronger `P^* F^2 < ∞` envelope assumption. -/
  squareIntegrableEnvelope_statement : Prop
  squareIntegrableEnvelope : squareIntegrableEnvelope_statement
  /-- Outer-a.s. strengthening under `P^* F^2 < ∞`. -/
  outerAlmostSureConvergence_statement : Prop
  outerAlmostSureConvergence : outerAlmostSureConvergence_statement

namespace Vaart1998Theorem23_7EmpiricalBootstrapSource

section

variable {Ω ΩBootstrap ΩLimit Observation FunctionIndex : Type*}
variable [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
variable [MeasurableSpace ΩLimit] [MeasurableSpace Observation]
variable {P : Measure Ω} [IsProbabilityMeasure P]
variable {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
variable (S :
  Vaart1998Theorem23_7EmpiricalBootstrapSource
    (Ω := Ω) (ΩBootstrap := ΩBootstrap) (ΩLimit := ΩLimit)
    (Observation := Observation) (FunctionIndex := FunctionIndex)
    P LimitLaw)

theorem empirical_law_display :
    S.empiricalLaw =
      vaart1998_empiricalDistributionFromObservations S.observation :=
  S.empiricalLaw_eq

theorem bootstrap_empirical_law_display :
    S.bootstrapEmpiricalLaw =
      vaart1998_bootstrapEmpiricalDistributionFromObservations
        S.bootstrapObservation :=
  S.bootstrapEmpiricalLaw_eq

theorem empirical_process_display :
    S.empiricalProcess =
      vaart1998_empiricalProcessFromClassAverages
        S.empiricalAverage S.populationAverage :=
  S.empiricalProcess_eq

theorem bootstrap_empirical_process_display :
    S.bootstrapEmpiricalProcess =
      vaart1998_bootstrapEmpiricalProcessFromAverages
        S.bootstrapAverage S.empiricalAverage :=
  S.bootstrapEmpiricalProcess_eq

theorem count_bootstrap_empirical_process_display :
    S.countBootstrapEmpiricalProcess =
      vaart1998_bootstrapEmpiricalProcessFromCounts
        S.observation S.redrawCount S.classFun :=
  S.countBootstrapEmpiricalProcess_eq

theorem bootstrap_empirical_process_eq_count
    (n : ℕ) (ω : Ω) (ωBootstrap : ΩBootstrap) :
    S.bootstrapEmpiricalProcess n ω ωBootstrap =
      S.countBootstrapEmpiricalProcess n ω ωBootstrap :=
  S.bootstrapEmpiricalProcess_eq_count n ω ωBootstrap

def chapter19_donsker_bridge :
    DonskerBridgeCertificate S.indexClass
      (vaart1998_populationClassMean S.populationLaw S.classFun)
      (vaart1998_empiricalClassMeanSequence S.samples S.classFun) :=
  S.chapter19DonskerBridge

theorem chapter19_donsker_weak_convergence :
    S.chapter19DonskerBridge.donsker.weak_convergence_statement :=
  DonskerBridgeCertificate.weakConvergence S.chapter19DonskerBridge

theorem conditional_expectation_display :
    S.conditionalTestExpectation =
      vaart1998_conditionalBootstrapProcessTestExpectation
        S.bootstrapLaw S.bootstrapEmpiricalProcess :=
  S.conditionalTestExpectation_eq

theorem bounded_lipschitz_discrepancy_display :
    S.boundedLipschitzDiscrepancy =
      vaart1998_bootstrapBoundedLipschitzDiscrepancy
        S.boundedLipschitzClass
        S.conditionalTestExpectation S.limitTestExpectation :=
  S.boundedLipschitzDiscrepancy_eq

theorem conditional_weak_convergence_source :
    S.conditionalWeakConvergence_statement :=
  S.conditionalWeakConvergence

theorem bounded_lipschitz_convergence_in_probability :
    vaart1998_bootstrapBoundedLipschitzConvergesInProbability
      P S.boundedLipschitzDiscrepancy :=
  S.boundedLipschitzConvergenceInProbability

theorem asymptotic_measurability :
    S.asymptoticMeasurable_statement :=
  S.asymptoticMeasurable

theorem outer_almost_sure_convergence :
    S.outerAlmostSureConvergence_statement :=
  S.outerAlmostSureConvergence

end

end Vaart1998Theorem23_7EmpiricalBootstrapSource

/-- Condition (23.8): conditional bounded-Lipschitz convergence in probability. -/
def vaart1998_bootstrapDeltaCondition23_8
    {Ω Process : Type*} [MeasurableSpace Ω]
    (P : Measure Ω) [IsProbabilityMeasure P]
    (boundedLipschitzClass : Set (Process -> ℝ))
    (conditionalExpectation : (Process -> ℝ) -> ℕ -> Ω -> ℝ)
    (limitExpectation : (Process -> ℝ) -> ℝ) : Prop :=
  vaart1998_bootstrapBoundedLipschitzConvergesInProbability P
    (vaart1998_bootstrapBoundedLipschitzDiscrepancy
      boundedLipschitzClass conditionalExpectation limitExpectation)

/-- Bootstrap statistic centered at the true parameter:
`r_n (thetaHat_n^* - theta)`. -/
def vaart1998_bootstrapDeltaScaledAroundTheta
    {Ω ΩBootstrap D : Type*} [Sub D] [SMul ℝ D]
    (bootstrapStatistic : ℕ -> Ω -> ΩBootstrap -> D)
    (theta : D) (rate : ℕ -> ℝ) (n : ℕ) (ω : Ω)
    (ωBootstrap : ΩBootstrap) : D :=
  rate n • (bootstrapStatistic n ω ωBootstrap - theta)

/-- Bootstrap transformed statistic centered at the true parameter:
`r_n (phi(thetaHat_n^*) - phi(theta))`. -/
def vaart1998_bootstrapDeltaCenteredTransformedStatistic
    {Ω ΩBootstrap D E : Type*} [Sub E] [SMul ℝ E]
    (phi : D -> E)
    (bootstrapStatistic : ℕ -> Ω -> ΩBootstrap -> D)
    (theta : D) (rate : ℕ -> ℝ) (n : ℕ) (ω : Ω)
    (ωBootstrap : ΩBootstrap) : E :=
  rate n • (phi (bootstrapStatistic n ω ωBootstrap) - phi theta)

/-- Linearized bootstrap statistic centered at the true parameter. -/
def vaart1998_bootstrapDeltaCenteredLinearizedStatistic
    {Ω ΩBootstrap D E : Type*} [NormedAddCommGroup D]
    [NormedSpace ℝ D] [NormedAddCommGroup E] [NormedSpace ℝ E]
    (derivative : D →L[ℝ] E)
    (bootstrapStatistic : ℕ -> Ω -> ΩBootstrap -> D)
    (theta : D) (rate : ℕ -> ℝ) (n : ℕ) (ω : Ω)
    (ωBootstrap : ΩBootstrap) : E :=
  derivative
    (vaart1998_bootstrapDeltaScaledAroundTheta
      bootstrapStatistic theta rate n ω ωBootstrap)

/-- Centered bootstrap delta-method remainder from Theorem 20.8. -/
def vaart1998_bootstrapDeltaCenteredRemainder
    {Ω ΩBootstrap D E : Type*} [NormedAddCommGroup D]
    [NormedSpace ℝ D] [NormedAddCommGroup E] [NormedSpace ℝ E]
    (phi : D -> E) (derivative : D →L[ℝ] E)
    (bootstrapStatistic : ℕ -> Ω -> ΩBootstrap -> D)
    (theta : D) (rate : ℕ -> ℝ) (n : ℕ) (ω : Ω)
    (ωBootstrap : ΩBootstrap) : E :=
  rate n •
    (phi (bootstrapStatistic n ω ωBootstrap) - phi theta -
      derivative (bootstrapStatistic n ω ωBootstrap - theta))

/-- Compose a bounded-Lipschitz test with the derivative `phi'_theta`. -/
def vaart1998_boundedLipschitzTestAfterDerivative
    {D E : Type*} [NormedAddCommGroup D] [NormedSpace ℝ D]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    (derivative : D →L[ℝ] E) (testFunction : E -> ℝ) : D -> ℝ :=
  fun x => testFunction (derivative x)

/-- The BL comparison discrepancy between two bootstrap `E`-valued statistics. -/
noncomputable def vaart1998_bootstrapFunctionalDeltaComparisonDiscrepancy
    {Ω ΩBootstrap E : Type*} [MeasurableSpace ΩBootstrap]
    (bootstrapLaw : ℕ -> Ω -> Measure ΩBootstrap)
    (boundedLipschitzClass : Set (E -> ℝ))
    (left right : ℕ -> Ω -> ΩBootstrap -> E)
    (n : ℕ) (ω : Ω) : ℝ :=
  sSup
    ((fun testFunction : E -> ℝ =>
      |(∫ ωBootstrap,
          testFunction (left n ω ωBootstrap) ∂bootstrapLaw n ω) -
        (∫ ωBootstrap,
          testFunction (right n ω ωBootstrap) ∂bootstrapLaw n ω)|) ''
      boundedLipschitzClass)

/-- Conditional probability of the event in the right side of (23.10). -/
def vaart1998_bootstrapFunctionalDeltaComparisonTailProbability
    {Ω ΩBootstrap E : Type*} [MeasurableSpace ΩBootstrap] [Sub E]
    [Norm E]
    (bootstrapLaw : ℕ -> Ω -> Measure ΩBootstrap)
    (left right : ℕ -> Ω -> ΩBootstrap -> E)
    (epsilon : ℝ) (n : ℕ) (ω : Ω) : ℝ :=
  vaart1998_bootstrapConditionalRealProbability bootstrapLaw
    (fun n ω =>
      {ωBootstrap |
        epsilon < ‖left n ω ωBootstrap - right n ω ωBootstrap‖})
    n ω

/-- The comparison inequality displayed as (23.10). -/
def vaart1998_bootstrapFunctionalDeltaComparisonBound23_10
    {Ω : Type*}
    (comparisonDiscrepancy : ℕ -> Ω -> ℝ)
    (tailProbability : ℝ -> ℕ -> Ω -> ℝ)
    (epsilon : ℝ) : Prop :=
  ∀ n ω, comparisonDiscrepancy n ω ≤
    epsilon + 2 * tailProbability epsilon n ω

/--
Source package for van der Vaart 1998, Theorem 23.9, the functional delta
method for the bootstrap.

The package records condition (23.8), the Hadamard-differentiability input,
the linearized conditional weak-limit route obtained by composing
bounded-Lipschitz tests with `phi'_theta`, the comparison inequality (23.10),
the two centered Theorem 20.8 expansions, and the final conditional bootstrap
functional-delta conclusion.
-/
structure Vaart1998Theorem23_9BootstrapFunctionalDeltaSource
    {Ω ΩBootstrap ΩLimit D E : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit]
    [NormedAddCommGroup D] [NormedSpace ℝ D]
    [MeasurableSpace D] [SecondCountableTopology D] [BorelSpace D]
    [OpensMeasurableSpace D] [CompleteSpace D]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    (P : Measure Ω) [IsProbabilityMeasure P]
    (LimitLaw : Measure ΩLimit) [IsProbabilityMeasure LimitLaw] where
  /-- Domain `D_phi` of the map. -/
  domain : Set D
  /-- Tangent subspace `D_0`. -/
  tangentSubspace : Submodule ℝ D
  /-- Tangent set used by the Chapter 20 Hadamard predicate. -/
  tangentSet : Set D
  tangentSet_eq : tangentSet = tangentSubspace
  /-- Functional map `phi`. -/
  phi : D -> E
  /-- Base point `theta`. -/
  theta : D
  /-- Hadamard derivative, extended to the whole space by Hahn-Banach. -/
  derivative : D →L[ℝ] E
  /-- Original maps `thetaHat_n`. -/
  statistic : ℕ -> Ω -> D
  /-- Bootstrap maps `thetaHat_n^*`. -/
  bootstrapStatistic : ℕ -> Ω -> ΩBootstrap -> D
  /-- Limit random element `T`. -/
  limitProcess : ΩLimit -> D
  /-- Rate, displayed as `sqrt n` in Theorem 23.9. -/
  rate : ℕ -> ℝ
  rate_eq_sqrt : rate = fun n : ℕ => √(n : ℝ)
  /-- Conditional bootstrap law given the original data. -/
  bootstrapLaw : ℕ -> Ω -> Measure ΩBootstrap
  /-- Unit bounded-Lipschitz class on `D`. -/
  boundedLipschitzClassD : Set (D -> ℝ)
  /-- Unit bounded-Lipschitz class on the target space. -/
  boundedLipschitzClassE : Set (E -> ℝ)
  /-- Original scaled statistic `sqrt n (thetaHat_n - theta)`. -/
  originalScaledStatistic : ℕ -> Ω -> D
  /-- Bootstrap input in condition (23.8). -/
  bootstrapScaledInput : ℕ -> Ω -> ΩBootstrap -> D
  /-- Bootstrap statistic centered at the true parameter. -/
  bootstrapCenteredScaledStatistic : ℕ -> Ω -> ΩBootstrap -> D
  /-- Original transformed statistic centered at `theta`. -/
  transformedStatistic : ℕ -> Ω -> E
  /-- Bootstrap transformed statistic centered at `thetaHat_n`. -/
  bootstrapTransformedStatistic : ℕ -> Ω -> ΩBootstrap -> E
  /-- Bootstrap transformed statistic centered at `theta`. -/
  bootstrapCenteredTransformedStatistic : ℕ -> Ω -> ΩBootstrap -> E
  /-- Linearized bootstrap statistic in the final conclusion. -/
  bootstrapLinearizedStatistic : ℕ -> Ω -> ΩBootstrap -> E
  /-- Linearized centered bootstrap statistic. -/
  bootstrapCenteredLinearizedStatistic : ℕ -> Ω -> ΩBootstrap -> E
  /-- Difference between transformed and linearized bootstrap statistics. -/
  bootstrapRemainder : ℕ -> Ω -> ΩBootstrap -> E
  /-- Centered Theorem 20.8 bootstrap remainder. -/
  bootstrapCenteredRemainder : ℕ -> Ω -> ΩBootstrap -> E
  originalScaledStatistic_eq :
    originalScaledStatistic =
      fun n ω =>
        vaart1998_chapter20ScaledDifference
          (rate n) (statistic n ω) theta
  bootstrapScaledInput_eq :
    bootstrapScaledInput =
      vaart1998_bootstrapDeltaScaledInput
        (Ω := Ω) (ΩBootstrap := ΩBootstrap) (D := D)
        bootstrapStatistic statistic rate
  bootstrapCenteredScaledStatistic_eq :
    bootstrapCenteredScaledStatistic =
      vaart1998_bootstrapDeltaScaledAroundTheta
        (Ω := Ω) (ΩBootstrap := ΩBootstrap) (D := D)
        bootstrapStatistic theta rate
  transformedStatistic_eq :
    transformedStatistic =
      vaart1998_deltaTransformedStatistic
        (Ω := Ω) (D := D) (E := E) phi statistic theta rate
  bootstrapTransformedStatistic_eq :
    bootstrapTransformedStatistic =
      vaart1998_bootstrapDeltaTransformedStatistic
        (Ω := Ω) (ΩBootstrap := ΩBootstrap) (D := D) (E := E)
        phi bootstrapStatistic statistic rate
  bootstrapCenteredTransformedStatistic_eq :
    bootstrapCenteredTransformedStatistic =
      vaart1998_bootstrapDeltaCenteredTransformedStatistic
        (Ω := Ω) (ΩBootstrap := ΩBootstrap) (D := D) (E := E)
        phi bootstrapStatistic theta rate
  bootstrapLinearizedStatistic_eq :
    bootstrapLinearizedStatistic =
      vaart1998_bootstrapDeltaLinearizedStatistic
        (Ω := Ω) (ΩBootstrap := ΩBootstrap) (D := D) (E := E)
        derivative bootstrapStatistic statistic rate
  bootstrapCenteredLinearizedStatistic_eq :
    bootstrapCenteredLinearizedStatistic =
      vaart1998_bootstrapDeltaCenteredLinearizedStatistic
        (Ω := Ω) (ΩBootstrap := ΩBootstrap) (D := D) (E := E)
        derivative bootstrapStatistic theta rate
  bootstrapRemainder_eq :
    bootstrapRemainder =
      vaart1998_bootstrapDeltaRemainder
        (Ω := Ω) (ΩBootstrap := ΩBootstrap) (D := D) (E := E)
        phi derivative bootstrapStatistic statistic rate
  bootstrapCenteredRemainder_eq :
    bootstrapCenteredRemainder =
      vaart1998_bootstrapDeltaCenteredRemainder
        (Ω := Ω) (ΩBootstrap := ΩBootstrap) (D := D) (E := E)
        phi derivative bootstrapStatistic theta rate
  /-- Conditional expectations for the input BL display in (23.8). -/
  inputConditionalExpectation : (D -> ℝ) -> ℕ -> Ω -> ℝ
  inputLimitExpectation : (D -> ℝ) -> ℝ
  inputBoundedLipschitzDiscrepancy : ℕ -> Ω -> ℝ
  inputConditionalExpectation_eq :
    inputConditionalExpectation =
      vaart1998_conditionalBootstrapProcessTestExpectation
        bootstrapLaw bootstrapScaledInput
  inputLimitExpectation_eq :
    inputLimitExpectation =
      vaart1998_limitProcessTestExpectation LimitLaw limitProcess
  inputBoundedLipschitzDiscrepancy_eq :
    inputBoundedLipschitzDiscrepancy =
      vaart1998_bootstrapBoundedLipschitzDiscrepancy
        boundedLipschitzClassD
        inputConditionalExpectation inputLimitExpectation
  /-- Conditional expectations after applying `phi'_theta`. -/
  linearizedConditionalExpectation : (E -> ℝ) -> ℕ -> Ω -> ℝ
  linearizedLimitExpectation : (E -> ℝ) -> ℝ
  linearizedBoundedLipschitzDiscrepancy : ℕ -> Ω -> ℝ
  linearizedConditionalExpectation_eq :
    linearizedConditionalExpectation =
      vaart1998_conditionalBootstrapProcessTestExpectation
        bootstrapLaw bootstrapLinearizedStatistic
  linearizedLimitExpectation_eq :
    linearizedLimitExpectation =
      vaart1998_limitProcessTestExpectation
        LimitLaw (fun ω => derivative (limitProcess ω))
  linearizedBoundedLipschitzDiscrepancy_eq :
    linearizedBoundedLipschitzDiscrepancy =
      vaart1998_bootstrapBoundedLipschitzDiscrepancy
        boundedLipschitzClassE
        linearizedConditionalExpectation linearizedLimitExpectation
  /-- Conditional expectations for the transformed bootstrap statistic. -/
  transformedConditionalExpectation : (E -> ℝ) -> ℕ -> Ω -> ℝ
  transformedLimitExpectation : (E -> ℝ) -> ℝ
  transformedBoundedLipschitzDiscrepancy : ℕ -> Ω -> ℝ
  transformedConditionalExpectation_eq :
    transformedConditionalExpectation =
      vaart1998_conditionalBootstrapProcessTestExpectation
        bootstrapLaw bootstrapTransformedStatistic
  transformedLimitExpectation_eq :
    transformedLimitExpectation = linearizedLimitExpectation
  transformedBoundedLipschitzDiscrepancy_eq :
    transformedBoundedLipschitzDiscrepancy =
      vaart1998_bootstrapBoundedLipschitzDiscrepancy
        boundedLipschitzClassE
        transformedConditionalExpectation transformedLimitExpectation
  /-- The left side of the comparison in (23.10). -/
  comparisonDiscrepancy : ℕ -> Ω -> ℝ
  /-- The conditional probability on the right side of (23.10). -/
  comparisonTailProbability : ℝ -> ℕ -> Ω -> ℝ
  comparisonDiscrepancy_eq :
    comparisonDiscrepancy =
      vaart1998_bootstrapFunctionalDeltaComparisonDiscrepancy
        bootstrapLaw boundedLipschitzClassE
        bootstrapTransformedStatistic bootstrapLinearizedStatistic
  comparisonTailProbability_eq :
    comparisonTailProbability =
      vaart1998_bootstrapFunctionalDeltaComparisonTailProbability
        bootstrapLaw bootstrapTransformedStatistic bootstrapLinearizedStatistic
  /-- Chapter 20 functional delta-method source for the original statistic. -/
  chapter20FunctionalDeltaSource :
    Vaart1998Theorem20_8FunctionalDeltaMethodSource
      (Ω := Ω) (Ω' := ΩLimit) (D := D) (E := E)
      (P := P) (Q := LimitLaw)
  chapter20FunctionalDeltaSource_phi_eq :
    chapter20FunctionalDeltaSource.phi = phi
  chapter20FunctionalDeltaSource_theta_eq :
    chapter20FunctionalDeltaSource.theta = theta
  chapter20FunctionalDeltaSource_derivative_eq :
    chapter20FunctionalDeltaSource.derivative = derivative
  chapter20FunctionalDeltaSource_statistic_eq :
    chapter20FunctionalDeltaSource.statistic = statistic
  chapter20FunctionalDeltaSource_limitProcess_eq :
    chapter20FunctionalDeltaSource.limitProcess = limitProcess
  chapter20FunctionalDeltaSource_rate_eq :
    chapter20FunctionalDeltaSource.rate = rate
  /-- The maps take values in the domain. -/
  statisticInDomain : ∀ n, ∀ᵐ ω ∂P, statistic n ω ∈ domain
  bootstrapStatisticInDomain_statement : Prop
  bootstrapStatisticInDomain : bootstrapStatisticInDomain_statement
  /-- Hadamard differentiability tangentially to `D_0`. -/
  hadamardDifferentiable :
    vaart1998_HadamardDifferentiableAtTangentially
      phi domain tangentSet theta derivative
  /-- Unconditional weak convergence of `sqrt n(thetaHat_n-theta)`. -/
  scaledStatisticWeakLimit :
    TendstoInDistribution
      originalScaledStatistic atTop limitProcess
      (fun _ : ℕ => P) LimitLaw
  /-- Condition (23.8). -/
  condition23_8 :
    vaart1998_bootstrapBoundedLipschitzConvergesInProbability
      P inputBoundedLipschitzDiscrepancy
  /-- The bootstrap input in (23.8) is asymptotically measurable. -/
  bootstrapScaledInputAsymptoticMeasurable_statement : Prop
  bootstrapScaledInputAsymptoticMeasurable :
    bootstrapScaledInputAsymptoticMeasurable_statement
  /-- The limit `T` is tight. -/
  limitTight_statement : Prop
  limitTight : limitTight_statement
  /-- The limit takes values in the tangent subspace. -/
  limitTakesValuesInTangentSet :
    ∀ᵐ ω ∂LimitLaw, limitProcess ω ∈ tangentSet
  /-- Hahn-Banach extension step for the derivative. -/
  hahnBanachDerivativeExtension_statement : Prop
  hahnBanachDerivativeExtension : hahnBanachDerivativeExtension_statement
  /-- `h ∘ phi'_theta` is a BL test on `D` with derivative-scaled norm. -/
  derivativeCompositionBoundedLipschitz_statement : Prop
  derivativeCompositionBoundedLipschitz :
    derivativeCompositionBoundedLipschitz_statement
  /-- Conditional weak convergence of the linearized bootstrap statistic. -/
  linearizedConditionalWeakLimit_statement : Prop
  linearizedConditionalWeakLimit :
    linearizedConditionalWeakLimit_statement
  /-- The displayed inequality (23.10). -/
  comparisonBound23_10 :
    ∀ epsilon, 0 < epsilon ->
      vaart1998_bootstrapFunctionalDeltaComparisonBound23_10
        comparisonDiscrepancy comparisonTailProbability epsilon
  /-- Joint convergence to two independent copies of `T`. -/
  jointConvergenceIndependentCopies_statement : Prop
  jointConvergenceIndependentCopies :
    jointConvergenceIndependentCopies_statement
  /-- Continuous-mapping handoff for the centered sequences. -/
  continuousMappingCenteredSequences_statement : Prop
  continuousMappingCenteredSequences :
    continuousMappingCenteredSequences_statement
  /-- Theorem 20.8 expansion for the bootstrap statistic centered at `theta`. -/
  centeredBootstrapExpansion_statement : Prop
  centeredBootstrapExpansion : centeredBootstrapExpansion_statement
  /-- Theorem 20.8 expansion for the original statistic centered at `theta`. -/
  centeredOriginalExpansion_statement : Prop
  centeredOriginalExpansion : centeredOriginalExpansion_statement
  /-- Subtracting the centered expansions gives unconditional outer-probability
  negligibility of the final bootstrap remainder. -/
  subtractedRemainderOuterProbability_statement : Prop
  subtractedRemainderOuterProbability :
    subtractedRemainderOuterProbability_statement
  /-- Conditional probability on the right of (23.10) goes to zero in outer
  probability. -/
  conditionalRemainderTailOuterProbability_statement : Prop
  conditionalRemainderTailOuterProbability :
    conditionalRemainderTailOuterProbability_statement
  /-- The same conditional probability goes to zero in outer mean. -/
  conditionalRemainderTailOuterMean_statement : Prop
  conditionalRemainderTailOuterMean :
    conditionalRemainderTailOuterMean_statement
  /-- Conditional Slutsky/BL handoff from linearized to transformed statistic. -/
  conditionalSlutskyHandoff_statement : Prop
  conditionalSlutskyHandoff : conditionalSlutskyHandoff_statement
  /-- Final Theorem 23.9 conclusion. -/
  bootstrapFunctionalDeltaConclusion_statement : Prop
  bootstrapFunctionalDeltaConclusion :
    bootstrapFunctionalDeltaConclusion_statement

namespace Vaart1998Theorem23_9BootstrapFunctionalDeltaSource

section

variable {Ω ΩBootstrap ΩLimit D E : Type*}
variable [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
variable [MeasurableSpace ΩLimit]
variable [NormedAddCommGroup D] [NormedSpace ℝ D]
variable [MeasurableSpace D] [SecondCountableTopology D] [BorelSpace D]
variable [OpensMeasurableSpace D] [CompleteSpace D]
variable [NormedAddCommGroup E] [NormedSpace ℝ E]
variable [MeasurableSpace E] [SecondCountableTopology E] [BorelSpace E]
variable [OpensMeasurableSpace E]
variable {P : Measure Ω} [IsProbabilityMeasure P]
variable {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
variable (S :
  Vaart1998Theorem23_9BootstrapFunctionalDeltaSource
    (Ω := Ω) (ΩBootstrap := ΩBootstrap) (ΩLimit := ΩLimit)
    (D := D) (E := E) P LimitLaw)

theorem tangent_set_display :
    S.tangentSet = S.tangentSubspace :=
  S.tangentSet_eq

theorem original_scaled_statistic_display :
    S.originalScaledStatistic =
      fun n ω =>
        vaart1998_chapter20ScaledDifference
          (S.rate n) (S.statistic n ω) S.theta :=
  S.originalScaledStatistic_eq

theorem bootstrap_scaled_input_display :
    S.bootstrapScaledInput =
      vaart1998_bootstrapDeltaScaledInput
        (Ω := Ω) (ΩBootstrap := ΩBootstrap) (D := D)
        S.bootstrapStatistic S.statistic S.rate :=
  S.bootstrapScaledInput_eq

theorem bootstrap_centered_scaled_statistic_display :
    S.bootstrapCenteredScaledStatistic =
      vaart1998_bootstrapDeltaScaledAroundTheta
        (Ω := Ω) (ΩBootstrap := ΩBootstrap) (D := D)
        S.bootstrapStatistic S.theta S.rate :=
  S.bootstrapCenteredScaledStatistic_eq

theorem transformed_statistic_display :
    S.transformedStatistic =
      vaart1998_deltaTransformedStatistic
        (Ω := Ω) (D := D) (E := E)
        S.phi S.statistic S.theta S.rate :=
  S.transformedStatistic_eq

theorem bootstrap_transformed_statistic_display :
    S.bootstrapTransformedStatistic =
      vaart1998_bootstrapDeltaTransformedStatistic
        (Ω := Ω) (ΩBootstrap := ΩBootstrap) (D := D) (E := E)
        S.phi S.bootstrapStatistic S.statistic S.rate :=
  S.bootstrapTransformedStatistic_eq

theorem bootstrap_centered_transformed_statistic_display :
    S.bootstrapCenteredTransformedStatistic =
      vaart1998_bootstrapDeltaCenteredTransformedStatistic
        (Ω := Ω) (ΩBootstrap := ΩBootstrap) (D := D) (E := E)
        S.phi S.bootstrapStatistic S.theta S.rate :=
  S.bootstrapCenteredTransformedStatistic_eq

theorem bootstrap_linearized_statistic_display :
    S.bootstrapLinearizedStatistic =
      vaart1998_bootstrapDeltaLinearizedStatistic
        (Ω := Ω) (ΩBootstrap := ΩBootstrap) (D := D) (E := E)
        S.derivative S.bootstrapStatistic S.statistic S.rate :=
  S.bootstrapLinearizedStatistic_eq

theorem bootstrap_remainder_display :
    S.bootstrapRemainder =
      vaart1998_bootstrapDeltaRemainder
        (Ω := Ω) (ΩBootstrap := ΩBootstrap) (D := D) (E := E)
        S.phi S.derivative S.bootstrapStatistic S.statistic S.rate :=
  S.bootstrapRemainder_eq

theorem input_condition23_8_discrepancy_display :
    S.inputBoundedLipschitzDiscrepancy =
      vaart1998_bootstrapBoundedLipschitzDiscrepancy
        S.boundedLipschitzClassD
        S.inputConditionalExpectation S.inputLimitExpectation :=
  S.inputBoundedLipschitzDiscrepancy_eq

theorem condition23_8_convergence :
    vaart1998_bootstrapBoundedLipschitzConvergesInProbability
      P S.inputBoundedLipschitzDiscrepancy :=
  S.condition23_8

theorem condition23_8_via_displayed_expectations :
    vaart1998_bootstrapDeltaCondition23_8
      P S.boundedLipschitzClassD
      S.inputConditionalExpectation S.inputLimitExpectation := by
  change vaart1998_bootstrapBoundedLipschitzConvergesInProbability P
    (vaart1998_bootstrapBoundedLipschitzDiscrepancy
      S.boundedLipschitzClassD
      S.inputConditionalExpectation S.inputLimitExpectation)
  rw [← S.inputBoundedLipschitzDiscrepancy_eq]
  exact S.condition23_8

theorem linearized_expectation_display :
    S.linearizedConditionalExpectation =
      vaart1998_conditionalBootstrapProcessTestExpectation
        S.bootstrapLaw S.bootstrapLinearizedStatistic :=
  S.linearizedConditionalExpectation_eq

theorem transformed_expectation_display :
    S.transformedConditionalExpectation =
      vaart1998_conditionalBootstrapProcessTestExpectation
        S.bootstrapLaw S.bootstrapTransformedStatistic :=
  S.transformedConditionalExpectation_eq

theorem comparison_discrepancy_display :
    S.comparisonDiscrepancy =
      vaart1998_bootstrapFunctionalDeltaComparisonDiscrepancy
        S.bootstrapLaw S.boundedLipschitzClassE
        S.bootstrapTransformedStatistic S.bootstrapLinearizedStatistic :=
  S.comparisonDiscrepancy_eq

theorem comparison_tail_probability_display :
    S.comparisonTailProbability =
      vaart1998_bootstrapFunctionalDeltaComparisonTailProbability
        S.bootstrapLaw
        S.bootstrapTransformedStatistic S.bootstrapLinearizedStatistic :=
  S.comparisonTailProbability_eq

def chapter20_functional_delta_source :
    Vaart1998Theorem20_8FunctionalDeltaMethodSource
      (Ω := Ω) (Ω' := ΩLimit) (D := D) (E := E)
      (P := P) (Q := LimitLaw) :=
  S.chapter20FunctionalDeltaSource

theorem chapter20_functional_delta_method :
    TendstoInDistribution
      (fun n ω =>
        S.chapter20FunctionalDeltaSource.rate n •
          (S.chapter20FunctionalDeltaSource.phi
              (S.chapter20FunctionalDeltaSource.statistic n ω) -
            S.chapter20FunctionalDeltaSource.phi
              S.chapter20FunctionalDeltaSource.theta))
      atTop
      (fun ω =>
        S.chapter20FunctionalDeltaSource.derivative
          (S.chapter20FunctionalDeltaSource.limitProcess ω))
      (fun _ : ℕ => P) LimitLaw :=
  Vaart1998Theorem20_8FunctionalDeltaMethodSource.functional_delta_method
    S.chapter20FunctionalDeltaSource

theorem chapter20_linearization_remainder :
    TendstoInMeasure P
      (fun n ω =>
        S.chapter20FunctionalDeltaSource.rate n •
          (S.chapter20FunctionalDeltaSource.phi
              (S.chapter20FunctionalDeltaSource.statistic n ω) -
            S.chapter20FunctionalDeltaSource.phi
              S.chapter20FunctionalDeltaSource.theta -
            S.chapter20FunctionalDeltaSource.derivative
              (S.chapter20FunctionalDeltaSource.statistic n ω -
                S.chapter20FunctionalDeltaSource.theta)))
      atTop (0 : Ω -> E) :=
  Vaart1998Theorem20_8FunctionalDeltaMethodSource.linearization_remainder_converges
    S.chapter20FunctionalDeltaSource

theorem hadamard_differentiable :
    vaart1998_HadamardDifferentiableAtTangentially
      S.phi S.domain S.tangentSet S.theta S.derivative :=
  S.hadamardDifferentiable

theorem scaled_statistic_weak_limit :
    TendstoInDistribution
      S.originalScaledStatistic atTop S.limitProcess
      (fun _ : ℕ => P) LimitLaw :=
  S.scaledStatisticWeakLimit

theorem bootstrap_scaled_input_asymptotic_measurable :
    S.bootstrapScaledInputAsymptoticMeasurable_statement :=
  S.bootstrapScaledInputAsymptoticMeasurable

theorem limit_takes_values_in_tangent_set :
    ∀ᵐ ω ∂LimitLaw, S.limitProcess ω ∈ S.tangentSet :=
  S.limitTakesValuesInTangentSet

theorem derivative_composition_bounded_lipschitz :
    S.derivativeCompositionBoundedLipschitz_statement :=
  S.derivativeCompositionBoundedLipschitz

theorem linearized_conditional_weak_limit :
    S.linearizedConditionalWeakLimit_statement :=
  S.linearizedConditionalWeakLimit

theorem comparison_bound23_10 (epsilon : ℝ) (hε : 0 < epsilon) :
    vaart1998_bootstrapFunctionalDeltaComparisonBound23_10
      S.comparisonDiscrepancy S.comparisonTailProbability epsilon :=
  S.comparisonBound23_10 epsilon hε

theorem centered_bootstrap_expansion :
    S.centeredBootstrapExpansion_statement :=
  S.centeredBootstrapExpansion

theorem centered_original_expansion :
    S.centeredOriginalExpansion_statement :=
  S.centeredOriginalExpansion

theorem subtracted_remainder_outer_probability :
    S.subtractedRemainderOuterProbability_statement :=
  S.subtractedRemainderOuterProbability

theorem conditional_remainder_tail_outer_probability :
    S.conditionalRemainderTailOuterProbability_statement :=
  S.conditionalRemainderTailOuterProbability

theorem conditional_remainder_tail_outer_mean :
    S.conditionalRemainderTailOuterMean_statement :=
  S.conditionalRemainderTailOuterMean

theorem conditional_slutsky_handoff :
    S.conditionalSlutskyHandoff_statement :=
  S.conditionalSlutskyHandoff

theorem bootstrap_functional_delta_conclusion :
    S.bootstrapFunctionalDeltaConclusion_statement :=
  S.bootstrapFunctionalDeltaConclusion

end

end Vaart1998Theorem23_9BootstrapFunctionalDeltaSource

/-- Indicator of the closed halfline `(-infinity, t]`. -/
def vaart1998_realClosedHalflineIndicator (t x : ℝ) : ℝ :=
  if x ≤ t then 1 else 0

/-- The index class of closed real halflines, represented by their endpoint. -/
def vaart1998_realClosedHalflineIndexClass : Set ℝ :=
  Set.univ

/-- Empirical distribution function `F_n(t)` from real observations. -/
def vaart1998_empiricalDistributionFunctionFromRealObservations
    {Ω : Type*} (observation : ℕ -> Ω -> ℝ)
    (n : ℕ) (ω : Ω) (t : ℝ) : ℝ :=
  (n : ℝ)⁻¹ *
    ∑ i ∈ Finset.Icc 1 n,
      vaart1998_realClosedHalflineIndicator t (observation i ω)

/-- Bootstrap empirical distribution function `F_n^*(t)`. -/
def vaart1998_bootstrapEmpiricalDistributionFunctionFromRealObservations
    {Ω ΩBootstrap : Type*}
    (bootstrapObservation : ℕ -> ℕ -> Ω -> ΩBootstrap -> ℝ)
    (n : ℕ) (ω : Ω) (ωBootstrap : ΩBootstrap) (t : ℝ) : ℝ :=
  (n : ℝ)⁻¹ *
    ∑ i ∈ Finset.Icc 1 n,
      vaart1998_realClosedHalflineIndicator t
        (bootstrapObservation n i ω ωBootstrap)

/-- Embed a raw real CDF into the chosen function-space model. -/
def vaart1998_empiricalDistributionFunctionMap
    {DistFunc : Type*} (cdfEmbedding : (ℝ -> ℝ) -> DistFunc)
    (rawCdf : ℝ -> ℝ) : DistFunc :=
  cdfEmbedding rawCdf

/--
Source package for van der Vaart 1998, Example 23.11, empirical distribution
functions as an application of the bootstrap functional delta method.

The package records that closed real halflines form the Donsker class for the
empirical CDF, that Theorem 23.7 supplies condition (23.8), and that Theorem
23.9 transfers the bootstrap convergence through any Hadamard-differentiable
functional.  The final fields retain the textbook examples: quantiles and
trimmed means via Lemmas 21.3, 22.9, and 22.10.
-/
structure Vaart1998Example23_11EmpiricalDistributionFunctionBootstrapSource
    {Ω ΩBootstrap ΩLimit DistFunc E : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit]
    [NormedAddCommGroup DistFunc] [NormedSpace ℝ DistFunc]
    [MeasurableSpace DistFunc] [SecondCountableTopology DistFunc]
    [BorelSpace DistFunc] [OpensMeasurableSpace DistFunc]
    [CompleteSpace DistFunc]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    [MeasurableSpace E] [SecondCountableTopology E] [BorelSpace E]
    [OpensMeasurableSpace E]
    (P : Measure Ω) [IsProbabilityMeasure P]
    (LimitLaw : Measure ΩLimit) [IsProbabilityMeasure LimitLaw] where
  /-- Original real-valued observations. -/
  observation : ℕ -> Ω -> ℝ
  /-- Bootstrap real-valued observations. -/
  bootstrapObservation : ℕ -> ℕ -> Ω -> ΩBootstrap -> ℝ
  /-- Population law of the observations. -/
  populationLaw : Measure ℝ
  /-- Population distribution function `F`. -/
  distributionFunction : ℝ -> ℝ
  /-- Raw empirical CDF `F_n`. -/
  empiricalCdfRaw : ℕ -> Ω -> ℝ -> ℝ
  /-- Raw bootstrap empirical CDF `F_n^*`. -/
  bootstrapEmpiricalCdfRaw : ℕ -> Ω -> ΩBootstrap -> ℝ -> ℝ
  /-- Embedding of raw CDF functions into the chosen normed function space. -/
  cdfEmbedding : (ℝ -> ℝ) -> DistFunc
  /-- Population CDF as an element of the chosen function space. -/
  populationCdf : DistFunc
  /-- Empirical CDF as a function-space statistic. -/
  empiricalCdf : ℕ -> Ω -> DistFunc
  /-- Bootstrap empirical CDF as a function-space statistic. -/
  bootstrapEmpiricalCdf : ℕ -> Ω -> ΩBootstrap -> DistFunc
  /-- Brownian-bridge limit as raw coordinates. -/
  brownianBridgeRaw : ΩLimit -> ℝ -> ℝ
  /-- Brownian-bridge limit in the chosen function space. -/
  limitProcess : ΩLimit -> DistFunc
  /-- Hadamard-differentiable functional applied to the empirical CDF. -/
  functional : DistFunc -> E
  /-- Derivative of the functional at `F`. -/
  derivative : DistFunc →L[ℝ] E
  /-- Conditional bootstrap law. -/
  bootstrapLaw : ℕ -> Ω -> Measure ΩBootstrap
  /-- Unit bounded-Lipschitz class on the function space. -/
  boundedLipschitzClassDist : Set (DistFunc -> ℝ)
  /-- Unit bounded-Lipschitz class on the functional target. -/
  boundedLipschitzClassTarget : Set (E -> ℝ)
  /-- Rate `sqrt n`. -/
  rate : ℕ -> ℝ
  empiricalCdfRaw_eq :
    empiricalCdfRaw =
      vaart1998_empiricalDistributionFunctionFromRealObservations
        observation
  bootstrapEmpiricalCdfRaw_eq :
    bootstrapEmpiricalCdfRaw =
      vaart1998_bootstrapEmpiricalDistributionFunctionFromRealObservations
        bootstrapObservation
  populationCdf_eq :
    populationCdf =
      vaart1998_empiricalDistributionFunctionMap
        cdfEmbedding distributionFunction
  empiricalCdf_eq :
    empiricalCdf =
      fun n ω =>
        vaart1998_empiricalDistributionFunctionMap
          cdfEmbedding (empiricalCdfRaw n ω)
  bootstrapEmpiricalCdf_eq :
    bootstrapEmpiricalCdf =
      fun n ω ωBootstrap =>
        vaart1998_empiricalDistributionFunctionMap
          cdfEmbedding (bootstrapEmpiricalCdfRaw n ω ωBootstrap)
  limitProcess_eq :
    limitProcess =
      fun ω =>
        vaart1998_empiricalDistributionFunctionMap
          cdfEmbedding (brownianBridgeRaw ω)
  rate_eq_sqrt : rate = fun n : ℕ => √(n : ℝ)
  /-- Chapter 19 empirical-CDF Donsker source for closed halflines. -/
  theorem19_3Source : Vaart1998Theorem19_3EmpiricalCDFDonskerSource
  theorem19_3_distributionFunction_eq :
    theorem19_3Source.distributionFunction = distributionFunction
  theorem19_3_empiricalProcess_represents_cdf_statement : Prop
  theorem19_3_empiricalProcess_represents_cdf :
    theorem19_3_empiricalProcess_represents_cdf_statement
  theorem19_3_brownianBridge_represents_limit_statement : Prop
  theorem19_3_brownianBridge_represents_limit :
    theorem19_3_brownianBridge_represents_limit_statement
  /-- Theorem 23.7 empirical-bootstrap source for the halfline class. -/
  empiricalBootstrapSource :
    Vaart1998Theorem23_7EmpiricalBootstrapSource
      (Ω := Ω) (ΩBootstrap := ΩBootstrap) (ΩLimit := ΩLimit)
      (Observation := ℝ) (FunctionIndex := ℝ) P LimitLaw
  empiricalBootstrapSource_populationLaw_eq :
    empiricalBootstrapSource.populationLaw = populationLaw
  empiricalBootstrapSource_indexClass_eq :
    empiricalBootstrapSource.indexClass =
      vaart1998_realClosedHalflineIndexClass
  empiricalBootstrapSource_classFun_eq :
    empiricalBootstrapSource.classFun =
      vaart1998_realClosedHalflineIndicator
  empiricalBootstrapSource_observation_eq :
    empiricalBootstrapSource.observation = observation
  empiricalBootstrapSource_bootstrapObservation_eq :
    empiricalBootstrapSource.bootstrapObservation = bootstrapObservation
  empiricalBootstrapSource_brownianBridge_eq :
    empiricalBootstrapSource.brownianBridgeLimit = brownianBridgeRaw
  /-- Theorem 23.9 functional delta-method source applied to the CDF statistic. -/
  bootstrapFunctionalDeltaSource :
    Vaart1998Theorem23_9BootstrapFunctionalDeltaSource
      (Ω := Ω) (ΩBootstrap := ΩBootstrap) (ΩLimit := ΩLimit)
      (D := DistFunc) (E := E) P LimitLaw
  bootstrapFunctionalDeltaSource_phi_eq :
    bootstrapFunctionalDeltaSource.phi = functional
  bootstrapFunctionalDeltaSource_theta_eq :
    bootstrapFunctionalDeltaSource.theta = populationCdf
  bootstrapFunctionalDeltaSource_derivative_eq :
    bootstrapFunctionalDeltaSource.derivative = derivative
  bootstrapFunctionalDeltaSource_statistic_eq :
    bootstrapFunctionalDeltaSource.statistic = empiricalCdf
  bootstrapFunctionalDeltaSource_bootstrapStatistic_eq :
    bootstrapFunctionalDeltaSource.bootstrapStatistic = bootstrapEmpiricalCdf
  bootstrapFunctionalDeltaSource_limitProcess_eq :
    bootstrapFunctionalDeltaSource.limitProcess = limitProcess
  bootstrapFunctionalDeltaSource_rate_eq :
    bootstrapFunctionalDeltaSource.rate = rate
  /-- Theorem 23.7 supplies condition (23.8) for the empirical CDF. -/
  condition23_8_from_empirical_bootstrap_statement : Prop
  condition23_8_from_empirical_bootstrap :
    condition23_8_from_empirical_bootstrap_statement
  /-- The condition (23.8) display matches the Theorem 23.9 input. -/
  condition23_8_matches_functional_delta_statement : Prop
  condition23_8_matches_functional_delta :
    condition23_8_matches_functional_delta_statement
  /-- The original transformed statistic has the same derivative limit. -/
  originalFunctionalDeltaLimit_statement : Prop
  originalFunctionalDeltaLimit : originalFunctionalDeltaLimit_statement
  /-- The bootstrap transformed statistic has the same limiting law as the
  original transformed statistic. -/
  bootstrapSameLimitAsOriginal_statement : Prop
  bootstrapSameLimitAsOriginal : bootstrapSameLimitAsOriginal_statement
  /-- Single-quantile Hadamard source from Lemma 21.3. -/
  singleQuantileHadamardSource :
    Vaart1998Lemma21_3SingleQuantileHadamardSource (Func := DistFunc)
  /-- Quantile-functional Hadamard source from Lemma 22.9. -/
  quantileFunctionalHadamardSource :
    Vaart1998Lemma22_9QuantileFunctionalHadamardSource DistFunc
  /-- Smooth generated-measure Hadamard source from Lemma 22.10. -/
  smoothGeneratingMeasureHadamardSource :
    Vaart1998Lemma22_10SmoothGeneratingMeasureHadamardSource DistFunc
  /-- Bootstrap conclusion for empirical quantiles under Lemma 21.3 hypotheses. -/
  quantileBootstrapConclusion_statement : Prop
  quantileBootstrapConclusion : quantileBootstrapConclusion_statement
  /-- Bootstrap conclusion for generated quantile functionals under Lemma 22.9. -/
  quantileFunctionalBootstrapConclusion_statement : Prop
  quantileFunctionalBootstrapConclusion :
    quantileFunctionalBootstrapConclusion_statement
  /-- Bootstrap conclusion for trimmed/smooth generated means under Lemma 22.10. -/
  trimmedMeanBootstrapConclusion_statement : Prop
  trimmedMeanBootstrapConclusion :
    trimmedMeanBootstrapConclusion_statement

namespace Vaart1998Example23_11EmpiricalDistributionFunctionBootstrapSource

section

variable {Ω ΩBootstrap ΩLimit DistFunc E : Type*}
variable [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
variable [MeasurableSpace ΩLimit]
variable [NormedAddCommGroup DistFunc] [NormedSpace ℝ DistFunc]
variable [MeasurableSpace DistFunc] [SecondCountableTopology DistFunc]
variable [BorelSpace DistFunc] [OpensMeasurableSpace DistFunc]
variable [CompleteSpace DistFunc]
variable [NormedAddCommGroup E] [NormedSpace ℝ E]
variable [MeasurableSpace E] [SecondCountableTopology E] [BorelSpace E]
variable [OpensMeasurableSpace E]
variable {P : Measure Ω} [IsProbabilityMeasure P]
variable {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
variable (S :
  Vaart1998Example23_11EmpiricalDistributionFunctionBootstrapSource
    (Ω := Ω) (ΩBootstrap := ΩBootstrap) (ΩLimit := ΩLimit)
    (DistFunc := DistFunc) (E := E) P LimitLaw)

theorem empirical_cdf_raw_display :
    S.empiricalCdfRaw =
      vaart1998_empiricalDistributionFunctionFromRealObservations
        S.observation :=
  S.empiricalCdfRaw_eq

theorem bootstrap_empirical_cdf_raw_display :
    S.bootstrapEmpiricalCdfRaw =
      vaart1998_bootstrapEmpiricalDistributionFunctionFromRealObservations
        S.bootstrapObservation :=
  S.bootstrapEmpiricalCdfRaw_eq

theorem empirical_cdf_display :
    S.empiricalCdf =
      fun n ω =>
        vaart1998_empiricalDistributionFunctionMap
          S.cdfEmbedding (S.empiricalCdfRaw n ω) :=
  S.empiricalCdf_eq

theorem bootstrap_empirical_cdf_display :
    S.bootstrapEmpiricalCdf =
      fun n ω ωBootstrap =>
        vaart1998_empiricalDistributionFunctionMap
          S.cdfEmbedding (S.bootstrapEmpiricalCdfRaw n ω ωBootstrap) :=
  S.bootstrapEmpiricalCdf_eq

theorem population_cdf_display :
    S.populationCdf =
      vaart1998_empiricalDistributionFunctionMap
        S.cdfEmbedding S.distributionFunction :=
  S.populationCdf_eq

theorem theorem19_3_weak_convergence :
    S.theorem19_3Source.weakConvergence_statement :=
  Vaart1998Theorem19_3EmpiricalCDFDonskerSource.weak_convergence
    S.theorem19_3Source

def empirical_bootstrap_source :
    Vaart1998Theorem23_7EmpiricalBootstrapSource
      (Ω := Ω) (ΩBootstrap := ΩBootstrap) (ΩLimit := ΩLimit)
      (Observation := ℝ) (FunctionIndex := ℝ) P LimitLaw :=
  S.empiricalBootstrapSource

theorem empirical_bootstrap_class_display :
    S.empiricalBootstrapSource.classFun =
      vaart1998_realClosedHalflineIndicator :=
  S.empiricalBootstrapSource_classFun_eq

theorem empirical_bootstrap_condition23_8_source :
    vaart1998_bootstrapBoundedLipschitzConvergesInProbability
      P S.empiricalBootstrapSource.boundedLipschitzDiscrepancy :=
  Vaart1998Theorem23_7EmpiricalBootstrapSource.bounded_lipschitz_convergence_in_probability
    S.empiricalBootstrapSource

def bootstrap_functional_delta_source :
    Vaart1998Theorem23_9BootstrapFunctionalDeltaSource
      (Ω := Ω) (ΩBootstrap := ΩBootstrap) (ΩLimit := ΩLimit)
      (D := DistFunc) (E := E) P LimitLaw :=
  S.bootstrapFunctionalDeltaSource

theorem bootstrap_functional_delta_statistic_display :
    S.bootstrapFunctionalDeltaSource.statistic = S.empiricalCdf :=
  S.bootstrapFunctionalDeltaSource_statistic_eq

theorem bootstrap_functional_delta_bootstrap_statistic_display :
    S.bootstrapFunctionalDeltaSource.bootstrapStatistic =
      S.bootstrapEmpiricalCdf :=
  S.bootstrapFunctionalDeltaSource_bootstrapStatistic_eq

theorem bootstrap_functional_delta_condition23_8 :
    vaart1998_bootstrapBoundedLipschitzConvergesInProbability
      P S.bootstrapFunctionalDeltaSource.inputBoundedLipschitzDiscrepancy :=
  Vaart1998Theorem23_9BootstrapFunctionalDeltaSource.condition23_8_convergence
    S.bootstrapFunctionalDeltaSource

theorem condition23_8_from_empirical_bootstrap_source :
    S.condition23_8_from_empirical_bootstrap_statement :=
  S.condition23_8_from_empirical_bootstrap

theorem condition23_8_matches_functional_delta_source :
    S.condition23_8_matches_functional_delta_statement :=
  S.condition23_8_matches_functional_delta

theorem original_functional_delta_limit :
    S.originalFunctionalDeltaLimit_statement :=
  S.originalFunctionalDeltaLimit

theorem bootstrap_same_limit_as_original :
    S.bootstrapSameLimitAsOriginal_statement :=
  S.bootstrapSameLimitAsOriginal

theorem bootstrap_functional_delta_conclusion :
    S.bootstrapFunctionalDeltaSource.bootstrapFunctionalDeltaConclusion_statement :=
  Vaart1998Theorem23_9BootstrapFunctionalDeltaSource.bootstrap_functional_delta_conclusion
    S.bootstrapFunctionalDeltaSource

theorem single_quantile_hadamard :
    vaart1998_HadamardDifferentiableAtTangentially
      S.singleQuantileHadamardSource.phi
      S.singleQuantileHadamardSource.domain
      S.singleQuantileHadamardSource.tangentSet
      S.singleQuantileHadamardSource.baseF
      S.singleQuantileHadamardSource.derivative :=
  Vaart1998Lemma21_3SingleQuantileHadamardSource.hadamard_differentiable
    S.singleQuantileHadamardSource

theorem quantile_functional_hadamard :
    vaart1998_HadamardDifferentiableAtTangentially
      S.quantileFunctionalHadamardSource.quantileMap
      S.quantileFunctionalHadamardSource.domain
      S.quantileFunctionalHadamardSource.tangentSet
      S.quantileFunctionalHadamardSource.baseQ
      S.quantileFunctionalHadamardSource.derivative :=
  Vaart1998Lemma22_9QuantileFunctionalHadamardSource.hadamard_differentiable
    S.quantileFunctionalHadamardSource

theorem smooth_generating_measure_hadamard :
    vaart1998_HadamardDifferentiableAtTangentially
      S.smoothGeneratingMeasureHadamardSource.distributionFunctional
      S.smoothGeneratingMeasureHadamardSource.domain
      S.smoothGeneratingMeasureHadamardSource.tangentSet
      S.smoothGeneratingMeasureHadamardSource.baseF
      S.smoothGeneratingMeasureHadamardSource.derivative :=
  Vaart1998Lemma22_10SmoothGeneratingMeasureHadamardSource.hadamard_differentiable
    S.smoothGeneratingMeasureHadamardSource

theorem quantile_bootstrap_conclusion :
    S.quantileBootstrapConclusion_statement :=
  S.quantileBootstrapConclusion

theorem quantile_functional_bootstrap_conclusion :
    S.quantileFunctionalBootstrapConclusion_statement :=
  S.quantileFunctionalBootstrapConclusion

theorem trimmed_mean_bootstrap_conclusion :
    S.trimmedMeanBootstrapConclusion_statement :=
  S.trimmedMeanBootstrapConclusion

end

end Vaart1998Example23_11EmpiricalDistributionFunctionBootstrapSource

/-- Deterministic rate `n^{-k}` used in the higher-order correctness section. -/
def vaart1998_inversePowerRate (k n : ℕ) : ℝ :=
  ((n : ℝ) ^ k)⁻¹

/-- Deterministic rate `n^{-1/2}`. -/
def vaart1998_inverseSqrtRate (n : ℕ) : ℝ :=
  (√(n : ℝ))⁻¹

/--
Conservative confidence-interval correctness at level `1 - alpha - beta` up
to deterministic order `O(n^{-k})`.
-/
def vaart1998_confidenceIntervalCorrectUpToOrder
    {Ω : Type*} [MeasurableSpace Ω] (P : ℕ -> Measure Ω)
    (lowerEndpoint upperEndpoint : ℕ -> Ω -> ℝ)
    (theta alpha beta : ℝ) (k : ℕ) : Prop :=
  ∃ C : ℝ, 0 ≤ C ∧
    ∀ᶠ n in atTop,
      1 - alpha - beta - C * vaart1998_inversePowerRate k n ≤
        (P n).real
          (vaart1998_confidenceIntervalCoverageEvent
            lowerEndpoint upperEndpoint theta n)

/--
Conservative confidence-interval correctness at level `1 - alpha - beta`
for an arbitrary deterministic rate.
-/
def vaart1998_confidenceIntervalCorrectAtRate
    {Ω : Type*} [MeasurableSpace Ω] (P : ℕ -> Measure Ω)
    (lowerEndpoint upperEndpoint : ℕ -> Ω -> ℝ)
    (theta alpha beta : ℝ) (rate : ℕ -> ℝ) : Prop :=
  ∃ C : ℝ, 0 ≤ C ∧
    ∀ᶠ n in atTop,
      1 - alpha - beta - C * rate n ≤
        (P n).real
          (vaart1998_confidenceIntervalCoverageEvent
            lowerEndpoint upperEndpoint theta n)

/-- `O_P(rate n)` for triangular arrays, stated as stochastic boundedness
after division by the proposed deterministic rate. -/
def vaart1998_stochasticOrderAtRate
    {Ω : Type*} [MeasurableSpace Ω] (P : ℕ -> Measure Ω)
    (X : ℕ -> Ω -> ℝ) (rate : ℕ -> ℝ) : Prop :=
  Vaart1998MeasureSeqStochasticBounded P
    (fun n ω => X n ω / rate n)

/-- `o_P(rate n)` for triangular arrays. -/
def vaart1998_stochasticLittleOAtRate
    {Ω : Type*} [MeasurableSpace Ω] (P : ℕ -> Measure Ω)
    (X : ℕ -> Ω -> ℝ) (rate : ℕ -> ℝ) : Prop :=
  Vaart1998MeasureSeqConvergesInProbabilityToZero P
    (fun n ω => X n ω / rate n)

/-- Kolmogorov-Smirnov bootstrap correctness at a supplied stochastic rate. -/
def vaart1998_bootstrapKolmogorovSmirnovCorrectAtRate
    {Ω : Type*} [MeasurableSpace Ω] (P : ℕ -> Measure Ω)
    (trueCdf : ℕ -> ℝ -> ℝ)
    (bootstrapCdf : ℕ -> Ω -> ℝ -> ℝ)
    (rate : ℕ -> ℝ) : Prop :=
  vaart1998_stochasticOrderAtRate P
    (vaart1998_bootstrapKolmogorovSmirnovDistance trueCdf bootstrapCdf)
    rate

/-- Two-term Edgeworth display (23.12), with the remainder supplied
separately. -/
def vaart1998_edgeworthExpansion23_12
    (normalCdf normalDensity p1 p2 : ℝ -> ℝ)
    (remainder : ℕ -> ℝ -> ℝ) (n : ℕ) (x : ℝ) : ℝ :=
  normalCdf x +
    p1 x * vaart1998_inverseSqrtRate n * normalDensity x +
    p2 x * vaart1998_inversePowerRate 1 n * normalDensity x +
    remainder n x

/-- Standardized sample mean `(bar X_n - mu) / (sigma / sqrt n)`. -/
def vaart1998_standardizedSampleMeanStatistic
    {Ω : Type*} (sampleMean : ℕ -> Ω -> ℝ)
    (mu sigma : ℝ) (n : ℕ) (ω : Ω) : ℝ :=
  (sampleMean n ω - mu) / (sigma / √(n : ℝ))

/-- Studentized sample mean `(bar X_n - mu) / (S_n / sqrt n)`. -/
def vaart1998_studentizedSampleMeanStatistic
    {Ω : Type*} (sampleMean sampleStdDev : ℕ -> Ω -> ℝ)
    (mu : ℝ) (n : ℕ) (ω : Ω) : ℝ :=
  (sampleMean n ω - mu) / (sampleStdDev n ω / √(n : ℝ))

/-- First Edgeworth polynomial for the standardized sample mean. -/
def vaart1998_sampleMeanEdgeworthP1
    (skewness : ℝ) (x : ℝ) : ℝ :=
  - skewness * (x ^ 2 - 1) / 6

/-- Second Edgeworth polynomial for the standardized sample mean. -/
def vaart1998_sampleMeanEdgeworthP2
    (skewness kurtosis : ℝ) (x : ℝ) : ℝ :=
  - (3 * kurtosis * (x ^ 3 - 3 * x) +
      skewness ^ 2 * (x ^ 5 - 10 * x ^ 3 + 15 * x)) / 72

/-- First Edgeworth polynomial for the studentized sample mean. -/
def vaart1998_studentizedSampleMeanEdgeworthP1
    (skewness : ℝ) (x : ℝ) : ℝ :=
  skewness * (2 * x ^ 2 + 1) / 6

/-- Second Edgeworth polynomial for the studentized sample mean. -/
def vaart1998_studentizedSampleMeanEdgeworthP2
    (skewness kurtosis : ℝ) (x : ℝ) : ℝ :=
  (3 * kurtosis * (x ^ 3 - 3 * x) -
      2 * skewness ^ 2 * (x ^ 5 + 2 * x ^ 3 - 3 * x) -
      9 * (x ^ 3 + 3 * x)) / 36

/--
Source package for van der Vaart 1998, Section 23.3 and Example 23.13.

The package records higher-order correctness, rate statements for the
Kolmogorov-Smirnov bootstrap error, the Edgeworth display (23.12), and the
concrete sample-mean and `t`-statistic Edgeworth polynomials.
-/
structure Vaart1998Section23_3HigherOrderSampleMeanEdgeworthSource
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    (P : ℕ -> Measure Ω) [∀ n : ℕ, IsProbabilityMeasure (P n)]
    (LimitLaw : Measure ΩLimit) [IsProbabilityMeasure LimitLaw] where
  /-- Reuse of the Section 23.2 bootstrap-consistency source layer. -/
  section23_2 :
    Vaart1998Section23_2BootstrapConsistencySource
      (ΩBootstrap := ΩBootstrap)
      (SampleSpace := SampleSpace) (Parameter := Parameter)
      P LimitLaw
  /-- Lower endpoint for the higher-order confidence-interval display. -/
  lowerEndpoint : ℕ -> Ω -> ℝ
  /-- Upper endpoint for the higher-order confidence-interval display. -/
  upperEndpoint : ℕ -> Ω -> ℝ
  /-- Coverage probability of the interval. -/
  coverageProbability : ℕ -> ℝ
  /-- Order of correctness `n^{-k}`. -/
  correctnessOrder : ℕ
  coverageProbability_eq :
    ∀ n,
      coverageProbability n =
        (P n).real
          (vaart1998_confidenceIntervalCoverageEvent
            lowerEndpoint upperEndpoint section23_2.intro.theta n)
  confidenceIntervalCorrectUpToOrder :
    vaart1998_confidenceIntervalCorrectUpToOrder
      P lowerEndpoint upperEndpoint section23_2.intro.theta
      section23_2.intro.alpha section23_2.intro.beta correctnessOrder
  /-- Unstudentized CDFs used for the percentile-method comparison. -/
  unstudentizedTrueCdf : ℕ -> ℝ -> ℝ
  unstudentizedBootstrapCdf : ℕ -> Ω -> ℝ -> ℝ
  /-- Percentile-`t` KS error is typically `O_P(n^{-1})`. -/
  percentileTKolmogorovRate :
    vaart1998_bootstrapKolmogorovSmirnovCorrectAtRate
      P section23_2.trueStudentizedCdf section23_2.bootstrapStudentizedCdf
      (vaart1998_inversePowerRate 1)
  /-- Percentile-method KS error is typically `O_P(n^{-1/2})`. -/
  percentileKolmogorovRate :
    vaart1998_bootstrapKolmogorovSmirnovCorrectAtRate
      P unstudentizedTrueCdf unstudentizedBootstrapCdf
      vaart1998_inverseSqrtRate
  oneTailedOrdersFromKSRates_statement : Prop
  oneTailedOrdersFromKSRates : oneTailedOrdersFromKSRates_statement
  twoTailedCancellation_statement : Prop
  twoTailedCancellation : twoTailedCancellation_statement
  intervalLengthTradeoff_statement : Prop
  intervalLengthTradeoff : intervalLengthTradeoff_statement
  /-- Standard normal distribution function `Phi`. -/
  normalCdf : ℝ -> ℝ
  /-- Standard normal density `phi`. -/
  normalDensity : ℝ -> ℝ
  /-- First polynomial `p_1` in (23.12). -/
  p1 : ℝ -> ℝ
  /-- Second polynomial `p_2` in (23.12). -/
  p2 : ℝ -> ℝ
  /-- Remainder in (23.12). -/
  remainder23_12 : ℕ -> ℝ -> ℝ
  /-- Right side of the Edgeworth expansion. -/
  edgeworthApproximation23_12 : ℕ -> ℝ -> ℝ
  edgeworthApproximation23_12_eq :
    edgeworthApproximation23_12 =
      vaart1998_edgeworthExpansion23_12
        normalCdf normalDensity p1 p2 remainder23_12
  edgeworthExpansion23_12_statement : Prop
  edgeworthExpansion23_12 : edgeworthExpansion23_12_statement
  edgeworthRemainderUniform_statement : Prop
  edgeworthRemainderUniform : edgeworthRemainderUniform_statement
  /-- Original observations in Example 23.13. -/
  observation : ℕ -> Ω -> ℝ
  /-- Population mean `mu`. -/
  populationMean : ℝ
  /-- Population variance `sigma^2`. -/
  populationVariance : ℝ
  /-- Population standard deviation `sigma`. -/
  populationStdDev : ℝ
  /-- Skewness `lambda`. -/
  skewness : ℝ
  /-- Kurtosis `kappa`. -/
  kurtosis : ℝ
  /-- Scalar sample mean `bar X_n`. -/
  sampleMean : ℕ -> Ω -> ℝ
  /-- Biased sample variance `S_n^2`. -/
  sampleVariance : ℕ -> Ω -> ℝ
  /-- Sample standard deviation `S_n`. -/
  sampleStdDev : ℕ -> Ω -> ℝ
  /-- Standardized sample-mean statistic. -/
  standardizedSampleMeanStatistic : ℕ -> Ω -> ℝ
  /-- Studentized sample-mean statistic. -/
  studentizedSampleMeanStatistic : ℕ -> Ω -> ℝ
  sampleMean_eq :
    sampleMean = vaart1998_scalarSampleMean observation
  sampleVariance_eq :
    sampleVariance =
      vaart1998_biasedSampleVariance observation sampleMean
  sampleStdDev_sq_eq :
    ∀ n ω, sampleStdDev n ω ^ 2 = sampleVariance n ω
  standardizedSampleMeanStatistic_eq :
    standardizedSampleMeanStatistic =
      vaart1998_standardizedSampleMeanStatistic
        sampleMean populationMean populationStdDev
  studentizedSampleMeanStatistic_eq :
    studentizedSampleMeanStatistic =
      vaart1998_studentizedSampleMeanStatistic
        sampleMean sampleStdDev populationMean
  standardizedP1 : ℝ -> ℝ
  standardizedP2 : ℝ -> ℝ
  studentizedP1 : ℝ -> ℝ
  studentizedP2 : ℝ -> ℝ
  standardizedP1_eq :
    standardizedP1 = vaart1998_sampleMeanEdgeworthP1 skewness
  standardizedP2_eq :
    standardizedP2 = vaart1998_sampleMeanEdgeworthP2 skewness kurtosis
  studentizedP1_eq :
    studentizedP1 = vaart1998_studentizedSampleMeanEdgeworthP1 skewness
  studentizedP2_eq :
    studentizedP2 =
      vaart1998_studentizedSampleMeanEdgeworthP2 skewness kurtosis
  standardizedRemainder : ℕ -> ℝ -> ℝ
  studentizedRemainder : ℕ -> ℝ -> ℝ
  standardizedEdgeworthApproximation : ℕ -> ℝ -> ℝ
  studentizedEdgeworthApproximation : ℕ -> ℝ -> ℝ
  standardizedEdgeworthApproximation_eq :
    standardizedEdgeworthApproximation =
      vaart1998_edgeworthExpansion23_12
        normalCdf normalDensity standardizedP1 standardizedP2
        standardizedRemainder
  studentizedEdgeworthApproximation_eq :
    studentizedEdgeworthApproximation =
      vaart1998_edgeworthExpansion23_12
        normalCdf normalDensity studentizedP1 studentizedP2
        studentizedRemainder
  standardizedEdgeworthExpansion_statement : Prop
  standardizedEdgeworthExpansion : standardizedEdgeworthExpansion_statement
  studentizedEdgeworthExpansion_statement : Prop
  studentizedEdgeworthExpansion : studentizedEdgeworthExpansion_statement
  firstPolynomialEven_statement : Prop
  firstPolynomialEven : firstPolynomialEven_statement
  cramerCondition_statement : Prop
  cramerCondition : cramerCondition_statement
  sufficientMoments_statement : Prop
  sufficientMoments : sufficientMoments_statement
  discreteFailureWarning_statement : Prop
  discreteFailureWarning : discreteFailureWarning_statement

namespace Vaart1998Section23_3HigherOrderSampleMeanEdgeworthSource

section

variable {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
variable [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
variable [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
variable {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
variable {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
variable (S :
  Vaart1998Section23_3HigherOrderSampleMeanEdgeworthSource
    (ΩBootstrap := ΩBootstrap)
    (SampleSpace := SampleSpace) (Parameter := Parameter)
    P LimitLaw)

theorem coverage_probability_display (n : ℕ) :
    S.coverageProbability n =
      (P n).real
        (vaart1998_confidenceIntervalCoverageEvent
          S.lowerEndpoint S.upperEndpoint S.section23_2.intro.theta n) :=
  S.coverageProbability_eq n

theorem confidence_interval_correct_up_to_order :
    vaart1998_confidenceIntervalCorrectUpToOrder
      P S.lowerEndpoint S.upperEndpoint S.section23_2.intro.theta
      S.section23_2.intro.alpha S.section23_2.intro.beta
      S.correctnessOrder :=
  S.confidenceIntervalCorrectUpToOrder

theorem percentile_t_kolmogorov_rate :
    vaart1998_bootstrapKolmogorovSmirnovCorrectAtRate
      P S.section23_2.trueStudentizedCdf
      S.section23_2.bootstrapStudentizedCdf
      (vaart1998_inversePowerRate 1) :=
  S.percentileTKolmogorovRate

theorem percentile_kolmogorov_rate :
    vaart1998_bootstrapKolmogorovSmirnovCorrectAtRate
      P S.unstudentizedTrueCdf S.unstudentizedBootstrapCdf
      vaart1998_inverseSqrtRate :=
  S.percentileKolmogorovRate

theorem edgeworth_approximation23_12_display :
    S.edgeworthApproximation23_12 =
      vaart1998_edgeworthExpansion23_12
        S.normalCdf S.normalDensity S.p1 S.p2 S.remainder23_12 :=
  S.edgeworthApproximation23_12_eq

theorem edgeworth_expansion23_12_source :
    S.edgeworthExpansion23_12_statement :=
  S.edgeworthExpansion23_12

theorem sample_mean_display :
    S.sampleMean = vaart1998_scalarSampleMean S.observation :=
  S.sampleMean_eq

theorem sample_variance_display :
    S.sampleVariance =
      vaart1998_biasedSampleVariance S.observation S.sampleMean :=
  S.sampleVariance_eq

theorem standardized_sample_mean_statistic_display :
    S.standardizedSampleMeanStatistic =
      vaart1998_standardizedSampleMeanStatistic
        S.sampleMean S.populationMean S.populationStdDev :=
  S.standardizedSampleMeanStatistic_eq

theorem studentized_sample_mean_statistic_display :
    S.studentizedSampleMeanStatistic =
      vaart1998_studentizedSampleMeanStatistic
        S.sampleMean S.sampleStdDev S.populationMean :=
  S.studentizedSampleMeanStatistic_eq

theorem standardized_p1_display :
    S.standardizedP1 =
      vaart1998_sampleMeanEdgeworthP1 S.skewness :=
  S.standardizedP1_eq

theorem standardized_p2_display :
    S.standardizedP2 =
      vaart1998_sampleMeanEdgeworthP2 S.skewness S.kurtosis :=
  S.standardizedP2_eq

theorem studentized_p1_display :
    S.studentizedP1 =
      vaart1998_studentizedSampleMeanEdgeworthP1 S.skewness :=
  S.studentizedP1_eq

theorem studentized_p2_display :
    S.studentizedP2 =
      vaart1998_studentizedSampleMeanEdgeworthP2
        S.skewness S.kurtosis :=
  S.studentizedP2_eq

theorem standardized_edgeworth_approximation_display :
    S.standardizedEdgeworthApproximation =
      vaart1998_edgeworthExpansion23_12
        S.normalCdf S.normalDensity S.standardizedP1
        S.standardizedP2 S.standardizedRemainder :=
  S.standardizedEdgeworthApproximation_eq

theorem studentized_edgeworth_approximation_display :
    S.studentizedEdgeworthApproximation =
      vaart1998_edgeworthExpansion23_12
        S.normalCdf S.normalDensity S.studentizedP1
        S.studentizedP2 S.studentizedRemainder :=
  S.studentizedEdgeworthApproximation_eq

theorem standardized_edgeworth_expansion :
    S.standardizedEdgeworthExpansion_statement :=
  S.standardizedEdgeworthExpansion

theorem studentized_edgeworth_expansion :
    S.studentizedEdgeworthExpansion_statement :=
  S.studentizedEdgeworthExpansion

theorem first_polynomial_even_source :
    S.firstPolynomialEven_statement :=
  S.firstPolynomialEven

theorem cramer_condition_source :
    S.cramerCondition_statement :=
  S.cramerCondition

theorem sufficient_moments_source :
    S.sufficientMoments_statement :=
  S.sufficientMoments

theorem discrete_failure_warning_source :
    S.discreteFailureWarning_statement :=
  S.discreteFailureWarning

end

end Vaart1998Section23_3HigherOrderSampleMeanEdgeworthSource

/-- Deterministic rate `n^{-3/4}`, represented without real powers. -/
def vaart1998_inverseThreeQuarterRate (n : ℕ) : ℝ :=
  (√(√((n : ℝ) ^ 3)))⁻¹

/-- Deterministic rate `n^{-3/2}` as `n^{-1} n^{-1/2}`. -/
def vaart1998_inverseThreeHalvesRate (n : ℕ) : ℝ :=
  vaart1998_inversePowerRate 1 n * vaart1998_inverseSqrtRate n

/-- Mean-square-error display for the empirical `p`th quantile in Example
23.14.  The integral over `[0,1]` is supplied as a functional so the packet can
record the textbook formula without committing to one interval-integral API. -/
def vaart1998_studentizedQuantileMeanSquareErrorDisplay
    (populationQuantile : ℝ -> ℝ) (p : ℝ)
    (unitIntervalIntegral : (ℝ -> ℝ) -> ℝ)
    (n r : ℕ) : ℝ :=
  (r : ℝ) * (Nat.choose n r : ℝ) *
    unitIntervalIntegral
      (fun u =>
        (populationQuantile u - populationQuantile p) ^ 2 *
          u ^ (r - 1) * (1 - u) ^ (n - r))

/-- Empirical version of the quantile MSE display, obtained by replacing
`F` by the empirical distribution function. -/
def vaart1998_empiricalStudentizedQuantileMeanSquareErrorEstimator
    {Ω : Type*} (empiricalQuantile : ℕ -> Ω -> ℝ -> ℝ)
    (p : ℝ) (unitIntervalIntegral : (ℝ -> ℝ) -> ℝ)
    (n r : ℕ) (ω : Ω) : ℝ :=
  (r : ℝ) * (Nat.choose n r : ℝ) *
    unitIntervalIntegral
      (fun u =>
        (empiricalQuantile n ω u - empiricalQuantile n ω p) ^ 2 *
          u ^ (r - 1) * (1 - u) ^ (n - r))

/-- Studentized empirical quantile statistic from Example 23.14. -/
def vaart1998_studentizedEmpiricalQuantileStatistic
    {Ω : Type*} (empiricalQuantile : ℕ -> Ω -> ℝ -> ℝ)
    (populationQuantile : ℝ -> ℝ) (standardErrorEstimator : ℕ -> Ω -> ℝ)
    (p : ℝ) (n : ℕ) (ω : Ω) : ℝ :=
  (empiricalQuantile n ω p - populationQuantile p) /
    standardErrorEstimator n ω

/-- Density-derivative ratio in the first studentized-quantile Edgeworth
polynomial: `(f' / f^2)(F^{-1}(p))`. -/
def vaart1998_studentizedQuantileDensityDerivativeRatio
    (populationQuantile density densityDerivative : ℝ -> ℝ) (p : ℝ) : ℝ :=
  densityDerivative (populationQuantile p) /
    (density (populationQuantile p)) ^ 2

/-- Numerator of the degree-three polynomial in Example 23.14. -/
def vaart1998_studentizedQuantileEdgeworthP1Numerator
    (p densityDerivativeRatio : ℝ) (n r : ℕ) (x : ℝ) : ℝ :=
  (3 / √Real.pi) * x ^ 3 +
    (2 - 10 * p - 12 * p * (1 - p) * densityDerivativeRatio) *
      x ^ 2 +
    ((3 + 6 * √(2 : ℝ)) / √Real.pi) * x -
    8 + 4 * p - 12 * ((r : ℝ) - (n : ℝ) * p)

/-- First Edgeworth polynomial for studentized empirical quantiles, normalized
by `12 sqrt(p(1-p))`. -/
def vaart1998_studentizedQuantileEdgeworthP1
    (p densityDerivativeRatio : ℝ) (n r : ℕ) (x : ℝ) : ℝ :=
  vaart1998_studentizedQuantileEdgeworthP1Numerator
      p densityDerivativeRatio n r x /
    (12 * √(p * (1 - p)))

/-- One-term Edgeworth expansion for a studentized empirical quantile. -/
def vaart1998_studentizedQuantileEdgeworthExpansion
    (normalCdf normalDensity : ℝ -> ℝ)
    (p1 : ℕ -> ℝ -> ℝ)
    (remainder : ℕ -> ℝ -> ℝ)
    (n : ℕ) (x : ℝ) : ℝ :=
  normalCdf x +
    p1 n x * vaart1998_inverseSqrtRate n * normalDensity x +
    remainder n x

/--
Source package for van der Vaart 1998, Example 23.14, studentized empirical
quantiles.  It records the MSE integral, empirical standard-error replacement,
the first Edgeworth polynomial of degree three, the `O(n^{-3/4})` remainder,
and the reason empirical bootstrap procedures do not gain higher-order
correctness for sample quantiles.
-/
structure Vaart1998Example23_14StudentizedQuantileSource
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    (P : ℕ -> Measure Ω) [∀ n : ℕ, IsProbabilityMeasure (P n)]
    (LimitLaw : Measure ΩLimit) [IsProbabilityMeasure LimitLaw] where
  /-- Reuse of the just-opened higher-order Edgeworth source layer. -/
  section23_3 :
    Vaart1998Section23_3HigherOrderSampleMeanEdgeworthSource
      (ΩBootstrap := ΩBootstrap)
      (SampleSpace := SampleSpace) (Parameter := Parameter)
      P LimitLaw
  /-- Quantile level `p`. -/
  p : ℝ
  /-- Distribution function `F`. -/
  populationCdf : ℝ -> ℝ
  /-- Population quantile function `F^{-1}`. -/
  populationQuantile : ℝ -> ℝ
  /-- Empirical distribution function `F_n`. -/
  empiricalCdf : ℕ -> Ω -> ℝ -> ℝ
  /-- Empirical quantile function `F_n^{-1}`. -/
  empiricalQuantile : ℕ -> Ω -> ℝ -> ℝ
  /-- Order statistic display. -/
  orderStatistic : ℕ -> ℕ -> Ω -> ℝ
  /-- Rank `r = floor(n p)`, kept as a natural-valued display. -/
  rankIndex : ℕ -> ℕ
  rankIndex_floor_statement : Prop
  rankIndex_floor : rankIndex_floor_statement
  empiricalQuantile_eq_orderStatistic :
    ∀ n ω, empiricalQuantile n ω p = orderStatistic n (rankIndex n) ω
  /-- Integral over `[0,1]` used in the MSE display. -/
  unitIntervalIntegral : (ℝ -> ℝ) -> ℝ
  /-- Mean square error of the empirical quantile. -/
  meanSquareError : ℕ -> ℝ
  meanSquareError_eq :
    ∀ n,
      meanSquareError n =
        vaart1998_studentizedQuantileMeanSquareErrorDisplay
          populationQuantile p unitIntervalIntegral n (rankIndex n)
  /-- Empirical plug-in estimator of the MSE. -/
  empiricalMeanSquareErrorEstimator : ℕ -> Ω -> ℝ
  empiricalMeanSquareErrorEstimator_eq :
    ∀ n ω,
      empiricalMeanSquareErrorEstimator n ω =
        vaart1998_empiricalStudentizedQuantileMeanSquareErrorEstimator
          empiricalQuantile p unitIntervalIntegral n (rankIndex n) ω
  /-- Empirical standard-error estimator `\hat sigma_n`. -/
  standardErrorEstimator : ℕ -> Ω -> ℝ
  standardErrorEstimator_sq_eq :
    ∀ n ω, standardErrorEstimator n ω ^ 2 =
      empiricalMeanSquareErrorEstimator n ω
  /-- Studentized quantile statistic. -/
  studentizedQuantileStatistic : ℕ -> Ω -> ℝ
  studentizedQuantileStatistic_eq :
    studentizedQuantileStatistic =
      vaart1998_studentizedEmpiricalQuantileStatistic
        empiricalQuantile populationQuantile standardErrorEstimator p
  /-- Differentiable density `f`. -/
  density : ℝ -> ℝ
  /-- Derivative `f'`. -/
  densityDerivative : ℝ -> ℝ
  differentiableDensity_statement : Prop
  differentiableDensity : differentiableDensity_statement
  densityDerivativeRatio : ℝ
  densityDerivativeRatio_eq :
    densityDerivativeRatio =
      vaart1998_studentizedQuantileDensityDerivativeRatio
        populationQuantile density densityDerivative p
  /-- Standard normal distribution function `Phi`. -/
  normalCdf : ℝ -> ℝ
  /-- Standard normal density `phi`. -/
  normalDensity : ℝ -> ℝ
  /-- Numerator of the first Edgeworth polynomial. -/
  firstPolynomialNumerator : ℕ -> ℝ -> ℝ
  firstPolynomialNumerator_eq :
    firstPolynomialNumerator =
      fun n x =>
        vaart1998_studentizedQuantileEdgeworthP1Numerator
          p densityDerivativeRatio n (rankIndex n) x
  /-- First Edgeworth polynomial. -/
  firstPolynomial : ℕ -> ℝ -> ℝ
  firstPolynomial_eq :
    firstPolynomial =
      fun n x =>
        vaart1998_studentizedQuantileEdgeworthP1
          p densityDerivativeRatio n (rankIndex n) x
  /-- Remainder in the quantile Edgeworth expansion. -/
  quantileRemainder : ℕ -> ℝ -> ℝ
  /-- Right side of the one-term Edgeworth expansion. -/
  edgeworthApproximation : ℕ -> ℝ -> ℝ
  edgeworthApproximation_eq :
    edgeworthApproximation =
      vaart1998_studentizedQuantileEdgeworthExpansion
        normalCdf normalDensity firstPolynomial quantileRemainder
  edgeworthExpansion_statement : Prop
  edgeworthExpansion : edgeworthExpansion_statement
  remainderThreeQuarter_statement : Prop
  remainderThreeQuarter : remainderThreeQuarter_statement
  firstPolynomialDegreeThree_statement : Prop
  firstPolynomialDegreeThree : firstPolynomialDegreeThree_statement
  firstPolynomialNotEven_statement : Prop
  firstPolynomialNotEven : firstPolynomialNotEven_statement
  /-- True and bootstrap CDFs for the studentized quantile statistic. -/
  trueStudentizedQuantileCdf : ℕ -> ℝ -> ℝ
  bootstrapStudentizedQuantileCdf : ℕ -> Ω -> ℝ -> ℝ
  /-- Empirical bootstrap procedures are only `O_P(n^{-1/2})` here. -/
  empiricalBootstrapFirstOrderRate :
    vaart1998_bootstrapKolmogorovSmirnovCorrectAtRate
      P trueStudentizedQuantileCdf bootstrapStudentizedQuantileCdf
      vaart1998_inverseSqrtRate
  empiricalBootstrapNoHigherOrder_statement : Prop
  empiricalBootstrapNoHigherOrder : empiricalBootstrapNoHigherOrder_statement
  /-- Smoothed-bootstrap handoff to the Chapter 24 density-estimation lane. -/
  smoothedBootstrapChapter24Handoff_statement : Prop
  smoothedBootstrapChapter24Handoff :
    smoothedBootstrapChapter24Handoff_statement

namespace Vaart1998Example23_14StudentizedQuantileSource

section

variable {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
variable [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
variable [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
variable {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
variable {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
variable (S :
  Vaart1998Example23_14StudentizedQuantileSource
    (ΩBootstrap := ΩBootstrap)
    (SampleSpace := SampleSpace) (Parameter := Parameter)
    P LimitLaw)

theorem empirical_quantile_order_statistic_display (n : ℕ) (ω : Ω) :
    S.empiricalQuantile n ω S.p =
      S.orderStatistic n (S.rankIndex n) ω :=
  S.empiricalQuantile_eq_orderStatistic n ω

theorem mean_square_error_display (n : ℕ) :
    S.meanSquareError n =
      vaart1998_studentizedQuantileMeanSquareErrorDisplay
        S.populationQuantile S.p S.unitIntervalIntegral
        n (S.rankIndex n) :=
  S.meanSquareError_eq n

theorem empirical_mean_square_error_estimator_display
    (n : ℕ) (ω : Ω) :
    S.empiricalMeanSquareErrorEstimator n ω =
      vaart1998_empiricalStudentizedQuantileMeanSquareErrorEstimator
        S.empiricalQuantile S.p S.unitIntervalIntegral
        n (S.rankIndex n) ω :=
  S.empiricalMeanSquareErrorEstimator_eq n ω

theorem studentized_quantile_statistic_display :
    S.studentizedQuantileStatistic =
      vaart1998_studentizedEmpiricalQuantileStatistic
        S.empiricalQuantile S.populationQuantile
        S.standardErrorEstimator S.p :=
  S.studentizedQuantileStatistic_eq

theorem density_derivative_ratio_display :
    S.densityDerivativeRatio =
      vaart1998_studentizedQuantileDensityDerivativeRatio
        S.populationQuantile S.density S.densityDerivative S.p :=
  S.densityDerivativeRatio_eq

theorem first_polynomial_numerator_display :
    S.firstPolynomialNumerator =
      fun n x =>
        vaart1998_studentizedQuantileEdgeworthP1Numerator
          S.p S.densityDerivativeRatio n (S.rankIndex n) x :=
  S.firstPolynomialNumerator_eq

theorem first_polynomial_display :
    S.firstPolynomial =
      fun n x =>
        vaart1998_studentizedQuantileEdgeworthP1
          S.p S.densityDerivativeRatio n (S.rankIndex n) x :=
  S.firstPolynomial_eq

theorem edgeworth_approximation_display :
    S.edgeworthApproximation =
      vaart1998_studentizedQuantileEdgeworthExpansion
        S.normalCdf S.normalDensity
        S.firstPolynomial S.quantileRemainder :=
  S.edgeworthApproximation_eq

theorem edgeworth_expansion_source :
    S.edgeworthExpansion_statement :=
  S.edgeworthExpansion

theorem remainder_three_quarter_source :
    S.remainderThreeQuarter_statement :=
  S.remainderThreeQuarter

theorem first_polynomial_degree_three_source :
    S.firstPolynomialDegreeThree_statement :=
  S.firstPolynomialDegreeThree

theorem first_polynomial_not_even_source :
    S.firstPolynomialNotEven_statement :=
  S.firstPolynomialNotEven

theorem empirical_bootstrap_first_order_rate :
    vaart1998_bootstrapKolmogorovSmirnovCorrectAtRate
      P S.trueStudentizedQuantileCdf
      S.bootstrapStudentizedQuantileCdf
      vaart1998_inverseSqrtRate :=
  S.empiricalBootstrapFirstOrderRate

theorem empirical_bootstrap_no_higher_order_source :
    S.empiricalBootstrapNoHigherOrder_statement :=
  S.empiricalBootstrapNoHigherOrder

theorem smoothed_bootstrap_chapter24_handoff :
    S.smoothedBootstrapChapter24Handoff_statement :=
  S.smoothedBootstrapChapter24Handoff

end

end Vaart1998Example23_14StudentizedQuantileSource

/--
The first-order Edgeworth correction to the normal-approximation coverage
probability obtained by evaluating (23.12) at the two normal quantiles.
-/
def vaart1998_normalApproximationCoverageEdgeworthCorrection
    (normalDensity p1 : ℝ -> ℝ) (zBeta zOneMinusAlpha : ℝ) : ℝ :=
  p1 zBeta * normalDensity zBeta -
    p1 zOneMinusAlpha * normalDensity zOneMinusAlpha

/-- Coverage expansion for the normal interval after evaluating (23.12). -/
def vaart1998_normalApproximationCoverageExpansion
    (alpha beta : ℝ) (normalDensity p1 : ℝ -> ℝ)
    (zBeta zOneMinusAlpha : ℝ)
    (remainder : ℕ -> ℝ) (n : ℕ) : ℝ :=
  1 - alpha - beta +
    vaart1998_normalApproximationCoverageEdgeworthCorrection
      normalDensity p1 zBeta zOneMinusAlpha *
      vaart1998_inverseSqrtRate n +
    remainder n

/-- Symmetric two-tailed normal interval after the `n^{-1/2}` terms cancel. -/
def vaart1998_symmetricNormalIntervalCoverageExpansion
    (alpha : ℝ) (remainder : ℕ -> ℝ) (n : ℕ) : ℝ :=
  1 - 2 * alpha + remainder n

/-- The widened normal level `alpha_n = alpha - M / n`. -/
def vaart1998_widenedNormalAlpha (alpha M : ℝ) (n : ℕ) : ℝ :=
  alpha - M * vaart1998_inversePowerRate 1 n

/-- Coverage expansion for the widened symmetric normal interval. -/
def vaart1998_widenedNormalIntervalCoverageExpansion
    (alphaN remainder : ℕ -> ℝ) (n : ℕ) : ℝ :=
  1 - 2 * alphaN n + remainder n

/-- Extra length from replacing `z_alpha` by `z_alphaN`. -/
def vaart1998_widenedNormalIntervalExtraLength
    {Ω : Type*} (normalQuantile : ℝ -> ℝ)
    (scaleEstimator : ℕ -> Ω -> ℝ) (alpha : ℝ)
    (alphaN : ℕ -> ℝ) (n : ℕ) (ω : Ω) : ℝ :=
  2 * (normalQuantile (alphaN n) - normalQuantile alpha) *
    scaleEstimator n ω

theorem vaart1998_normalApproximationCoverageEdgeworthCorrection_cancel
    (normalDensity p1 : ℝ -> ℝ) (z : ℝ)
    (hp1_even_at_z : p1 (-z) = p1 z)
    (hphi_even_at_z : normalDensity (-z) = normalDensity z) :
    vaart1998_normalApproximationCoverageEdgeworthCorrection
      normalDensity p1 (-z) z = 0 := by
  simp [vaart1998_normalApproximationCoverageEdgeworthCorrection,
    hp1_even_at_z, hphi_even_at_z]

theorem vaart1998_normalApproximationCoverageExpansion_of_zero_correction
    (alpha beta : ℝ) (normalDensity p1 : ℝ -> ℝ)
    (zBeta zOneMinusAlpha : ℝ) (remainder : ℕ -> ℝ) (n : ℕ)
    (hcorrection :
      vaart1998_normalApproximationCoverageEdgeworthCorrection
        normalDensity p1 zBeta zOneMinusAlpha = 0) :
    vaart1998_normalApproximationCoverageExpansion
      alpha beta normalDensity p1 zBeta zOneMinusAlpha remainder n =
        1 - alpha - beta + remainder n := by
  simp [vaart1998_normalApproximationCoverageExpansion, hcorrection]

/--
Source package for van der Vaart 1998, Section 23.3's normal-approximation
coverage expansion, symmetric cancellation, and slight interval widening.
-/
structure Vaart1998Section23_3NormalApproximationCoverageSource
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    (P : ℕ -> Measure Ω) [∀ n : ℕ, IsProbabilityMeasure (P n)]
    (LimitLaw : Measure ΩLimit) [IsProbabilityMeasure LimitLaw] where
  /-- Reuse of the Example 23.14 studentized-quantile source layer. -/
  example23_14 :
    Vaart1998Example23_14StudentizedQuantileSource
      (ΩBootstrap := ΩBootstrap)
      (SampleSpace := SampleSpace) (Parameter := Parameter)
      P LimitLaw
  /-- Estimator `\hat theta_n`. -/
  estimator : ℕ -> Ω -> ℝ
  /-- Scale estimator `\hat sigma_n`. -/
  scaleEstimator : ℕ -> Ω -> ℝ
  /-- Target parameter. -/
  theta : ℝ
  /-- Left-tail error level. -/
  alpha : ℝ
  /-- Right-tail error level. -/
  beta : ℝ
  /-- Standard-normal quantile function. -/
  normalQuantile : ℝ -> ℝ
  /-- Standard-normal density `phi`. -/
  normalDensity : ℝ -> ℝ
  /-- First Edgeworth polynomial `p_1`. -/
  p1 : ℝ -> ℝ
  /-- Normal quantile `z_beta`. -/
  zBeta : ℝ
  /-- Normal quantile `z_{1-alpha}`. -/
  zOneMinusAlpha : ℝ
  zBeta_eq : zBeta = normalQuantile beta
  zOneMinusAlpha_eq : zOneMinusAlpha = normalQuantile (1 - alpha)
  /-- `O(n^{-1})` remainder in the two-quantile expansion. -/
  normalRemainder : ℕ -> ℝ
  normalRemainderOrderOne_statement : Prop
  normalRemainderOrderOne : normalRemainderOrderOne_statement
  /-- Lower endpoint `\hat theta_n - z_beta \hat sigma_n`. -/
  normalLowerEndpoint : ℕ -> Ω -> ℝ
  /-- Upper endpoint `\hat theta_n - z_{1-alpha} \hat sigma_n`. -/
  normalUpperEndpoint : ℕ -> Ω -> ℝ
  normalLowerEndpoint_eq :
    normalLowerEndpoint =
      fun n ω => estimator n ω - zBeta * scaleEstimator n ω
  normalUpperEndpoint_eq :
    normalUpperEndpoint =
      fun n ω => estimator n ω - zOneMinusAlpha * scaleEstimator n ω
  /-- Coverage probability of the normal interval. -/
  normalCoverageProbability : ℕ -> ℝ
  normalCoverageProbability_eq :
    ∀ n,
      normalCoverageProbability n =
        (P n).real
          (vaart1998_confidenceIntervalCoverageEvent
            normalLowerEndpoint normalUpperEndpoint theta n)
  normalCoverageExpansion :
    ∀ n,
      normalCoverageProbability n =
        vaart1998_normalApproximationCoverageExpansion
          alpha beta normalDensity p1 zBeta zOneMinusAlpha
          normalRemainder n
  normalApproxCorrectSqrtRate :
    vaart1998_confidenceIntervalCorrectAtRate
      P normalLowerEndpoint normalUpperEndpoint theta alpha beta
      vaart1998_inverseSqrtRate
  /-- Symmetric level `alpha = beta`. -/
  symmetricAlpha : ℝ
  symmetricAlpha_eq_alpha : symmetricAlpha = alpha
  symmetricBeta_eq_alpha : beta = symmetricAlpha
  /-- Symmetric quantile relation `z_alpha = -z_{1-alpha}`. -/
  symmetricQuantileRelation_statement : Prop
  symmetricQuantileRelation : symmetricQuantileRelation_statement
  /-- Evenness of `p_1`, the condition cancelling the `n^{-1/2}` term. -/
  p1Even_statement : Prop
  p1Even : p1Even_statement
  symmetricEdgeworthCorrectionCancel :
    vaart1998_normalApproximationCoverageEdgeworthCorrection
      normalDensity p1 zBeta zOneMinusAlpha = 0
  /-- Remainder after symmetric cancellation. -/
  symmetricRemainder : ℕ -> ℝ
  symmetricRemainderOrderOne_statement : Prop
  symmetricRemainderOrderOne : symmetricRemainderOrderOne_statement
  symmetricCoverageProbability : ℕ -> ℝ
  symmetricCoverageExpansion :
    ∀ n,
      symmetricCoverageProbability n =
        vaart1998_symmetricNormalIntervalCoverageExpansion
          symmetricAlpha symmetricRemainder n
  symmetricCorrectOrderOne :
    vaart1998_confidenceIntervalCorrectAtRate
      P normalLowerEndpoint normalUpperEndpoint theta
      symmetricAlpha symmetricAlpha (vaart1998_inversePowerRate 1)
  /-- Widened levels `alpha_n < alpha`. -/
  alphaN : ℕ -> ℝ
  wideningConstant : ℝ
  alphaN_eq :
    ∀ n, alphaN n =
      vaart1998_widenedNormalAlpha symmetricAlpha wideningConstant n
  alphaN_lt_alpha_eventually_statement : Prop
  alphaN_lt_alpha_eventually : alphaN_lt_alpha_eventually_statement
  widenedLowerEndpoint : ℕ -> Ω -> ℝ
  widenedUpperEndpoint : ℕ -> Ω -> ℝ
  widenedLowerEndpoint_eq :
    widenedLowerEndpoint =
      fun n ω =>
        estimator n ω - normalQuantile (alphaN n) * scaleEstimator n ω
  widenedUpperEndpoint_eq :
    widenedUpperEndpoint =
      fun n ω =>
        estimator n ω - normalQuantile (1 - alphaN n) * scaleEstimator n ω
  widenedCoverageProbability : ℕ -> ℝ
  widenedCoverageProbability_eq :
    ∀ n,
      widenedCoverageProbability n =
        (P n).real
          (vaart1998_confidenceIntervalCoverageEvent
            widenedLowerEndpoint widenedUpperEndpoint theta n)
  widenedRemainder : ℕ -> ℝ
  widenedRemainderOrderOne_statement : Prop
  widenedRemainderOrderOne : widenedRemainderOrderOne_statement
  widenedCoverageExpansion :
    ∀ n,
      widenedCoverageProbability n =
        vaart1998_widenedNormalIntervalCoverageExpansion
          alphaN widenedRemainder n
  widenedConservativeAnyOrder_statement : Prop
  widenedConservativeAnyOrder : widenedConservativeAnyOrder_statement
  scaleEstimatorHalfRate :
    vaart1998_stochasticOrderAtRate P scaleEstimator
      vaart1998_inverseSqrtRate
  widenedExtraLength : ℕ -> Ω -> ℝ
  widenedExtraLength_eq :
    widenedExtraLength =
      vaart1998_widenedNormalIntervalExtraLength
        normalQuantile scaleEstimator symmetricAlpha alphaN
  widenedExtraLengthRate :
    vaart1998_stochasticOrderAtRate P widenedExtraLength
      vaart1998_inverseThreeHalvesRate
  normalIntervalLengthRate_statement : Prop
  normalIntervalLengthRate : normalIntervalLengthRate_statement
  scaleChoiceDominatesWidening_statement : Prop
  scaleChoiceDominatesWidening : scaleChoiceDominatesWidening_statement

namespace Vaart1998Section23_3NormalApproximationCoverageSource

section

variable {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
variable [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
variable [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
variable {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
variable {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
variable (S :
  Vaart1998Section23_3NormalApproximationCoverageSource
    (ΩBootstrap := ΩBootstrap)
    (SampleSpace := SampleSpace) (Parameter := Parameter)
    P LimitLaw)

theorem normal_lower_endpoint_display :
    S.normalLowerEndpoint =
      fun n ω => S.estimator n ω - S.zBeta * S.scaleEstimator n ω :=
  S.normalLowerEndpoint_eq

theorem normal_upper_endpoint_display :
    S.normalUpperEndpoint =
      fun n ω =>
        S.estimator n ω - S.zOneMinusAlpha * S.scaleEstimator n ω :=
  S.normalUpperEndpoint_eq

theorem normal_coverage_probability_display (n : ℕ) :
    S.normalCoverageProbability n =
      (P n).real
        (vaart1998_confidenceIntervalCoverageEvent
          S.normalLowerEndpoint S.normalUpperEndpoint S.theta n) :=
  S.normalCoverageProbability_eq n

theorem normal_coverage_expansion (n : ℕ) :
    S.normalCoverageProbability n =
      vaart1998_normalApproximationCoverageExpansion
        S.alpha S.beta S.normalDensity S.p1
        S.zBeta S.zOneMinusAlpha S.normalRemainder n :=
  S.normalCoverageExpansion n

theorem normal_approximation_correct_sqrt_rate :
    vaart1998_confidenceIntervalCorrectAtRate
      P S.normalLowerEndpoint S.normalUpperEndpoint S.theta
      S.alpha S.beta vaart1998_inverseSqrtRate :=
  S.normalApproxCorrectSqrtRate

theorem symmetric_correction_cancel :
    vaart1998_normalApproximationCoverageEdgeworthCorrection
      S.normalDensity S.p1 S.zBeta S.zOneMinusAlpha = 0 :=
  S.symmetricEdgeworthCorrectionCancel

theorem symmetric_coverage_expansion (n : ℕ) :
    S.symmetricCoverageProbability n =
      vaart1998_symmetricNormalIntervalCoverageExpansion
        S.symmetricAlpha S.symmetricRemainder n :=
  S.symmetricCoverageExpansion n

theorem symmetric_correct_order_one :
    vaart1998_confidenceIntervalCorrectAtRate
      P S.normalLowerEndpoint S.normalUpperEndpoint S.theta
      S.symmetricAlpha S.symmetricAlpha (vaart1998_inversePowerRate 1) :=
  S.symmetricCorrectOrderOne

theorem widened_alpha_display (n : ℕ) :
    S.alphaN n =
      vaart1998_widenedNormalAlpha
        S.symmetricAlpha S.wideningConstant n :=
  S.alphaN_eq n

theorem widened_lower_endpoint_display :
    S.widenedLowerEndpoint =
      fun n ω =>
        S.estimator n ω -
          S.normalQuantile (S.alphaN n) * S.scaleEstimator n ω :=
  S.widenedLowerEndpoint_eq

theorem widened_upper_endpoint_display :
    S.widenedUpperEndpoint =
      fun n ω =>
        S.estimator n ω -
          S.normalQuantile (1 - S.alphaN n) *
            S.scaleEstimator n ω :=
  S.widenedUpperEndpoint_eq

theorem widened_coverage_probability_display (n : ℕ) :
    S.widenedCoverageProbability n =
      (P n).real
        (vaart1998_confidenceIntervalCoverageEvent
          S.widenedLowerEndpoint S.widenedUpperEndpoint S.theta n) :=
  S.widenedCoverageProbability_eq n

theorem widened_coverage_expansion (n : ℕ) :
    S.widenedCoverageProbability n =
      vaart1998_widenedNormalIntervalCoverageExpansion
        S.alphaN S.widenedRemainder n :=
  S.widenedCoverageExpansion n

theorem widened_conservative_any_order_source :
    S.widenedConservativeAnyOrder_statement :=
  S.widenedConservativeAnyOrder

theorem scale_estimator_half_rate :
    vaart1998_stochasticOrderAtRate P S.scaleEstimator
      vaart1998_inverseSqrtRate :=
  S.scaleEstimatorHalfRate

theorem widened_extra_length_display :
    S.widenedExtraLength =
      vaart1998_widenedNormalIntervalExtraLength
        S.normalQuantile S.scaleEstimator S.symmetricAlpha S.alphaN :=
  S.widenedExtraLength_eq

theorem widened_extra_length_rate :
    vaart1998_stochasticOrderAtRate P S.widenedExtraLength
      vaart1998_inverseThreeHalvesRate :=
  S.widenedExtraLengthRate

theorem normal_interval_length_rate_source :
    S.normalIntervalLengthRate_statement :=
  S.normalIntervalLengthRate

theorem scale_choice_dominates_widening_source :
    S.scaleChoiceDominatesWidening_statement :=
  S.scaleChoiceDominatesWidening

end

end Vaart1998Section23_3NormalApproximationCoverageSource

/-- Conditional bootstrap version of the two-term Edgeworth display (23.12). -/
def vaart1998_bootstrapEdgeworthExpansion23_12
    {Ω : Type*} (normalCdf normalDensity : ℝ -> ℝ)
    (p1Bootstrap p2Bootstrap : ℕ -> Ω -> ℝ -> ℝ)
    (remainder : ℕ -> Ω -> ℝ -> ℝ) (n : ℕ) (ω : Ω) (x : ℝ) : ℝ :=
  normalCdf x +
    p1Bootstrap n ω x * vaart1998_inverseSqrtRate n * normalDensity x +
    p2Bootstrap n ω x * vaart1998_inversePowerRate 1 n * normalDensity x +
    remainder n ω x

/--
Pointwise polynomial part of the bound obtained by subtracting the bootstrap
Edgeworth expansion from the unconditional expansion.
-/
def vaart1998_bootstrapEdgeworthSubtractionPolynomialTerm
    {Ω : Type*} (normalDensity p1True p2True : ℝ -> ℝ)
    (p1Bootstrap p2Bootstrap : ℕ -> Ω -> ℝ -> ℝ)
    (n : ℕ) (ω : Ω) (x : ℝ) : ℝ :=
  |(p1True x - p1Bootstrap n ω x) * vaart1998_inverseSqrtRate n +
    (p2True x - p2Bootstrap n ω x) *
      vaart1998_inversePowerRate 1 n| * normalDensity x

/-- Uniform-in-`x` polynomial part of the bootstrap Edgeworth subtraction. -/
def vaart1998_bootstrapEdgeworthSubtractionPolynomialSup
    {Ω : Type*} (normalDensity p1True p2True : ℝ -> ℝ)
    (p1Bootstrap p2Bootstrap : ℕ -> Ω -> ℝ -> ℝ)
    (n : ℕ) (ω : Ω) : ℝ :=
  sSup
    ((fun x : ℝ =>
      vaart1998_bootstrapEdgeworthSubtractionPolynomialTerm
        normalDensity p1True p2True p1Bootstrap p2Bootstrap n ω x) ''
      Set.univ)

/-- Uniform absolute size of a random Edgeworth remainder. -/
def vaart1998_randomEdgeworthRemainderUniformSup
    {Ω : Type*} (remainder : ℕ -> Ω -> ℝ -> ℝ)
    (n : ℕ) (ω : Ω) : ℝ :=
  sSup ((fun x : ℝ => |remainder n ω x|) '' Set.univ)

theorem vaart1998_bootstrapEdgeworthSubtractionPolynomialTerm_zero
    {Ω : Type*} (normalDensity p1True p2True : ℝ -> ℝ)
    (p1Bootstrap p2Bootstrap : ℕ -> Ω -> ℝ -> ℝ)
    (n : ℕ) (ω : Ω) (x : ℝ)
    (hp1 : p1Bootstrap n ω x = p1True x)
    (hp2 : p2Bootstrap n ω x = p2True x) :
    vaart1998_bootstrapEdgeworthSubtractionPolynomialTerm
      normalDensity p1True p2True p1Bootstrap p2Bootstrap n ω x = 0 := by
  simp [vaart1998_bootstrapEdgeworthSubtractionPolynomialTerm, hp1, hp2]

/--
Source package for van der Vaart 1998, Section 23.3's conditional bootstrap
Edgeworth expansion and the subtraction bound leading to the `O_P(n^{-1})`
percentile-`t` Kolmogorov-Smirnov rate.
-/
structure Vaart1998Section23_3BootstrapEdgeworthSubtractionSource
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    (P : ℕ -> Measure Ω) [∀ n : ℕ, IsProbabilityMeasure (P n)]
    (LimitLaw : Measure ΩLimit) [IsProbabilityMeasure LimitLaw] where
  /-- Reuse of the normal-coverage source layer. -/
  normalCoverage :
    Vaart1998Section23_3NormalApproximationCoverageSource
      (ΩBootstrap := ΩBootstrap)
      (SampleSpace := SampleSpace) (Parameter := Parameter)
      P LimitLaw
  /-- True CDF of the studentized statistic. -/
  trueStudentizedCdf : ℕ -> ℝ -> ℝ
  /-- Conditional bootstrap CDF of the studentized statistic. -/
  bootstrapStudentizedCdf : ℕ -> Ω -> ℝ -> ℝ
  /-- Standard normal distribution function. -/
  normalCdf : ℝ -> ℝ
  /-- Standard normal density. -/
  normalDensity : ℝ -> ℝ
  /-- True first Edgeworth polynomial `p_1(· | P)`. -/
  p1True : ℝ -> ℝ
  /-- True second Edgeworth polynomial `p_2(· | P)`. -/
  p2True : ℝ -> ℝ
  /-- Bootstrap first Edgeworth polynomial `p_1(· | \hat P_n)`. -/
  p1Bootstrap : ℕ -> Ω -> ℝ -> ℝ
  /-- Bootstrap second Edgeworth polynomial `p_2(· | \hat P_n)`. -/
  p2Bootstrap : ℕ -> Ω -> ℝ -> ℝ
  /-- Remainder in the unconditional Edgeworth expansion. -/
  trueRemainder : ℕ -> ℝ -> ℝ
  /-- Random remainder in the conditional bootstrap Edgeworth expansion. -/
  bootstrapRemainder : ℕ -> Ω -> ℝ -> ℝ
  normalCdf_eq :
    normalCdf =
      normalCoverage.example23_14.section23_3.normalCdf
  normalDensity_eq :
    normalDensity =
      normalCoverage.example23_14.section23_3.normalDensity
  p1True_eq :
    p1True =
      normalCoverage.example23_14.section23_3.p1
  p2True_eq :
    p2True =
      normalCoverage.example23_14.section23_3.p2
  /-- Unconditional Edgeworth right-hand side (23.12). -/
  trueEdgeworthApproximation : ℕ -> ℝ -> ℝ
  trueEdgeworthApproximation_eq :
    trueEdgeworthApproximation =
      vaart1998_edgeworthExpansion23_12
        normalCdf normalDensity p1True p2True trueRemainder
  /-- Conditional bootstrap Edgeworth right-hand side. -/
  bootstrapEdgeworthApproximation : ℕ -> Ω -> ℝ -> ℝ
  bootstrapEdgeworthApproximation_eq :
    bootstrapEdgeworthApproximation =
      vaart1998_bootstrapEdgeworthExpansion23_12
        normalCdf normalDensity p1Bootstrap p2Bootstrap
        bootstrapRemainder
  trueCdfEdgeworthExpansion :
    ∀ n x, trueStudentizedCdf n x = trueEdgeworthApproximation n x
  bootstrapCdfEdgeworthExpansion :
    ∀ n ω x,
      bootstrapStudentizedCdf n ω x =
        bootstrapEdgeworthApproximation n ω x
  /-- Uniform true-remainder display. -/
  trueRemainderUniformSup : ℕ -> ℝ
  trueRemainderUniformSup_statement : Prop
  trueRemainderUniformSup_source : trueRemainderUniformSup_statement
  /-- Uniform random bootstrap remainder display. -/
  bootstrapRemainderUniformSup : ℕ -> Ω -> ℝ
  bootstrapRemainderUniformSup_eq :
    bootstrapRemainderUniformSup =
      vaart1998_randomEdgeworthRemainderUniformSup bootstrapRemainder
  bootstrapRemainderLittleOOrderOne :
    vaart1998_stochasticLittleOAtRate P bootstrapRemainderUniformSup
      (vaart1998_inversePowerRate 1)
  /-- Polynomial-difference part in the displayed subtraction bound. -/
  polynomialDifferenceSup : ℕ -> Ω -> ℝ
  polynomialDifferenceSup_eq :
    polynomialDifferenceSup =
      vaart1998_bootstrapEdgeworthSubtractionPolynomialSup
        normalDensity p1True p2True p1Bootstrap p2Bootstrap
  /-- Remainder term in the final subtraction bound. -/
  subtractionRemainder : ℕ -> Ω -> ℝ
  subtractionRemainderLittleOOrderOne :
    vaart1998_stochasticLittleOAtRate P subtractionRemainder
      (vaart1998_inversePowerRate 1)
  /-- Supremum subtraction inequality displayed after (23.12). -/
  edgeworthSubtractionBound :
    ∀ n ω,
      vaart1998_bootstrapKolmogorovSmirnovDistance
        trueStudentizedCdf bootstrapStudentizedCdf n ω ≤
        polynomialDifferenceSup n ω + subtractionRemainder n ω
  /-- Smooth dependence of `p_i(· | P)` on the underlying distribution. -/
  edgeworthPolynomialSmoothDependence_statement : Prop
  edgeworthPolynomialSmoothDependence :
    edgeworthPolynomialSmoothDependence_statement
  /-- Size of the empirical distribution perturbation `\hat P_n - P`. -/
  distributionEstimatorDistance : ℕ -> Ω -> ℝ
  distributionEstimatorHalfRate :
    vaart1998_stochasticOrderAtRate P distributionEstimatorDistance
      vaart1998_inverseSqrtRate
  polynomialDifferenceOrderOne :
    vaart1998_stochasticOrderAtRate P polynomialDifferenceSup
      (vaart1998_inversePowerRate 1)
  percentileTBootstrapKSErrorOrderOne :
    vaart1998_bootstrapKolmogorovSmirnovCorrectAtRate
      P trueStudentizedCdf bootstrapStudentizedCdf
      (vaart1998_inversePowerRate 1)

namespace Vaart1998Section23_3BootstrapEdgeworthSubtractionSource

section

variable {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
variable [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
variable [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
variable {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
variable {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
variable (S :
  Vaart1998Section23_3BootstrapEdgeworthSubtractionSource
    (ΩBootstrap := ΩBootstrap)
    (SampleSpace := SampleSpace) (Parameter := Parameter)
    P LimitLaw)

theorem true_edgeworth_approximation_display :
    S.trueEdgeworthApproximation =
      vaart1998_edgeworthExpansion23_12
        S.normalCdf S.normalDensity S.p1True S.p2True
        S.trueRemainder :=
  S.trueEdgeworthApproximation_eq

theorem bootstrap_edgeworth_approximation_display :
    S.bootstrapEdgeworthApproximation =
      vaart1998_bootstrapEdgeworthExpansion23_12
        S.normalCdf S.normalDensity S.p1Bootstrap S.p2Bootstrap
        S.bootstrapRemainder :=
  S.bootstrapEdgeworthApproximation_eq

theorem true_cdf_edgeworth_expansion (n : ℕ) (x : ℝ) :
    S.trueStudentizedCdf n x = S.trueEdgeworthApproximation n x :=
  S.trueCdfEdgeworthExpansion n x

theorem bootstrap_cdf_edgeworth_expansion
    (n : ℕ) (ω : Ω) (x : ℝ) :
    S.bootstrapStudentizedCdf n ω x =
      S.bootstrapEdgeworthApproximation n ω x :=
  S.bootstrapCdfEdgeworthExpansion n ω x

theorem bootstrap_remainder_uniform_sup_display :
    S.bootstrapRemainderUniformSup =
      vaart1998_randomEdgeworthRemainderUniformSup S.bootstrapRemainder :=
  S.bootstrapRemainderUniformSup_eq

theorem bootstrap_remainder_little_o_order_one :
    vaart1998_stochasticLittleOAtRate P S.bootstrapRemainderUniformSup
      (vaart1998_inversePowerRate 1) :=
  S.bootstrapRemainderLittleOOrderOne

theorem polynomial_difference_sup_display :
    S.polynomialDifferenceSup =
      vaart1998_bootstrapEdgeworthSubtractionPolynomialSup
        S.normalDensity S.p1True S.p2True
        S.p1Bootstrap S.p2Bootstrap :=
  S.polynomialDifferenceSup_eq

theorem subtraction_remainder_little_o_order_one :
    vaart1998_stochasticLittleOAtRate P S.subtractionRemainder
      (vaart1998_inversePowerRate 1) :=
  S.subtractionRemainderLittleOOrderOne

theorem edgeworth_subtraction_bound (n : ℕ) (ω : Ω) :
    vaart1998_bootstrapKolmogorovSmirnovDistance
      S.trueStudentizedCdf S.bootstrapStudentizedCdf n ω ≤
      S.polynomialDifferenceSup n ω + S.subtractionRemainder n ω :=
  S.edgeworthSubtractionBound n ω

theorem edgeworth_polynomial_smooth_dependence_source :
    S.edgeworthPolynomialSmoothDependence_statement :=
  S.edgeworthPolynomialSmoothDependence

theorem distribution_estimator_half_rate :
    vaart1998_stochasticOrderAtRate P S.distributionEstimatorDistance
      vaart1998_inverseSqrtRate :=
  S.distributionEstimatorHalfRate

theorem polynomial_difference_order_one :
    vaart1998_stochasticOrderAtRate P S.polynomialDifferenceSup
      (vaart1998_inversePowerRate 1) :=
  S.polynomialDifferenceOrderOne

theorem percentile_t_bootstrap_ks_error_order_one :
    vaart1998_bootstrapKolmogorovSmirnovCorrectAtRate
      P S.trueStudentizedCdf S.bootstrapStudentizedCdf
      (vaart1998_inversePowerRate 1) :=
  S.percentileTBootstrapKSErrorOrderOne

end

end Vaart1998Section23_3BootstrapEdgeworthSubtractionSource

/-- Leading normal term in the unstudentized Edgeworth expansion. -/
def vaart1998_unstudentizedNormalLeadingTerm
    (normalCdf : ℝ -> ℝ) (scale : ℕ -> ℝ) (n : ℕ) (x : ℝ) : ℝ :=
  normalCdf (x / scale n)

/-- Leading normal term in the bootstrap unstudentized Edgeworth expansion. -/
def vaart1998_bootstrapUnstudentizedNormalLeadingTerm
    {Ω : Type*} (normalCdf : ℝ -> ℝ)
    (scaleEstimator : ℕ -> Ω -> ℝ) (n : ℕ) (ω : Ω) (x : ℝ) : ℝ :=
  normalCdf (x / scaleEstimator n ω)

/-- Unstudentized Edgeworth expansion with leading scale `sigma_n`. -/
def vaart1998_unstudentizedEdgeworthExpansion
    (normalCdf normalDensity : ℝ -> ℝ)
    (q1 q2 : ℝ -> ℝ) (scale : ℕ -> ℝ)
    (remainder : ℕ -> ℝ -> ℝ) (n : ℕ) (x : ℝ) : ℝ :=
  normalCdf (x / scale n) +
    q1 (x / scale n) * vaart1998_inverseSqrtRate n *
      normalDensity (x / scale n) +
    q2 (x / scale n) * vaart1998_inversePowerRate 1 n *
      normalDensity (x / scale n) +
    remainder n x

/-- Bootstrap unstudentized Edgeworth expansion with scale `hat sigma_n`. -/
def vaart1998_bootstrapUnstudentizedEdgeworthExpansion
    {Ω : Type*} (normalCdf normalDensity : ℝ -> ℝ)
    (q1Bootstrap q2Bootstrap : ℕ -> Ω -> ℝ -> ℝ)
    (scaleEstimator : ℕ -> Ω -> ℝ)
    (remainder : ℕ -> Ω -> ℝ -> ℝ)
    (n : ℕ) (ω : Ω) (x : ℝ) : ℝ :=
  normalCdf (x / scaleEstimator n ω) +
    q1Bootstrap n ω (x / scaleEstimator n ω) *
      vaart1998_inverseSqrtRate n *
      normalDensity (x / scaleEstimator n ω) +
    q2Bootstrap n ω (x / scaleEstimator n ω) *
      vaart1998_inversePowerRate 1 n *
      normalDensity (x / scaleEstimator n ω) +
    remainder n ω x

/--
The displayed leading-term difference governing the percentile method:
`sup_x |Phi (x / sigma_n) - Phi (x / hat sigma_n)|`.
-/
def vaart1998_unstudentizedLeadingNormalTermDifferenceSup
    {Ω : Type*} (normalCdf : ℝ -> ℝ) (scale : ℕ -> ℝ)
    (scaleEstimator : ℕ -> Ω -> ℝ) (n : ℕ) (ω : Ω) : ℝ :=
  sSup
    ((fun x : ℝ =>
      |vaart1998_unstudentizedNormalLeadingTerm normalCdf scale n x -
        vaart1998_bootstrapUnstudentizedNormalLeadingTerm
          normalCdf scaleEstimator n ω x|) '' Set.univ)

theorem vaart1998_unstudentizedNormalLeadingTerm_eq_of_scale_eq
    {Ω : Type*} (normalCdf : ℝ -> ℝ) (scale : ℕ -> ℝ)
    (scaleEstimator : ℕ -> Ω -> ℝ) (n : ℕ) (ω : Ω)
    (hscale : scaleEstimator n ω = scale n) (x : ℝ) :
    vaart1998_bootstrapUnstudentizedNormalLeadingTerm
      normalCdf scaleEstimator n ω x =
      vaart1998_unstudentizedNormalLeadingTerm normalCdf scale n x := by
  simp [vaart1998_bootstrapUnstudentizedNormalLeadingTerm,
    vaart1998_unstudentizedNormalLeadingTerm, hscale]

/--
Source package for van der Vaart 1998, Section 23.3's comparison between the
unstudentized percentile method and the percentile-`t` method.
-/
structure Vaart1998Section23_3PercentileMethodUnstudentizedSource
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    (P : ℕ -> Measure Ω) [∀ n : ℕ, IsProbabilityMeasure (P n)]
    (LimitLaw : Measure ΩLimit) [IsProbabilityMeasure LimitLaw] where
  /-- Reuse of the just-opened bootstrap Edgeworth-subtraction layer. -/
  edgeworthSubtraction :
    Vaart1998Section23_3BootstrapEdgeworthSubtractionSource
      (ΩBootstrap := ΩBootstrap)
      (SampleSpace := SampleSpace) (Parameter := Parameter)
      P LimitLaw
  /-- CDF of the unstudentized statistic `hat theta_n - theta`. -/
  trueUnstudentizedCdf : ℕ -> ℝ -> ℝ
  /-- Conditional bootstrap CDF of `hat theta_n^* - hat theta_n`. -/
  bootstrapUnstudentizedCdf : ℕ -> Ω -> ℝ -> ℝ
  /-- Standard normal distribution function. -/
  normalCdf : ℝ -> ℝ
  /-- Standard normal density. -/
  normalDensity : ℝ -> ℝ
  normalCdf_eq :
    normalCdf = edgeworthSubtraction.normalCdf
  normalDensity_eq :
    normalDensity = edgeworthSubtraction.normalDensity
  /-- True asymptotic scale `sigma_n`. -/
  scale : ℕ -> ℝ
  /-- Bootstrap scale estimator `hat sigma_n`. -/
  scaleEstimator : ℕ -> Ω -> ℝ
  /-- True unstudentized Edgeworth polynomials `q_1`, `q_2`. -/
  q1True : ℝ -> ℝ
  q2True : ℝ -> ℝ
  /-- Bootstrap unstudentized Edgeworth polynomials. -/
  q1Bootstrap : ℕ -> Ω -> ℝ -> ℝ
  q2Bootstrap : ℕ -> Ω -> ℝ -> ℝ
  /-- These `q_i` are generally not the studentized `p_i`. -/
  qPolynomialsDifferFromStudentized_statement : Prop
  qPolynomialsDifferFromStudentized :
    qPolynomialsDifferFromStudentized_statement
  /-- Remainders in the true/bootstrap unstudentized expansions. -/
  trueRemainder : ℕ -> ℝ -> ℝ
  bootstrapRemainder : ℕ -> Ω -> ℝ -> ℝ
  /-- True unstudentized Edgeworth right-hand side. -/
  trueUnstudentizedEdgeworthApproximation : ℕ -> ℝ -> ℝ
  trueUnstudentizedEdgeworthApproximation_eq :
    trueUnstudentizedEdgeworthApproximation =
      vaart1998_unstudentizedEdgeworthExpansion
        normalCdf normalDensity q1True q2True scale trueRemainder
  /-- Bootstrap unstudentized Edgeworth right-hand side. -/
  bootstrapUnstudentizedEdgeworthApproximation :
    ℕ -> Ω -> ℝ -> ℝ
  bootstrapUnstudentizedEdgeworthApproximation_eq :
    bootstrapUnstudentizedEdgeworthApproximation =
      vaart1998_bootstrapUnstudentizedEdgeworthExpansion
        normalCdf normalDensity q1Bootstrap q2Bootstrap
        scaleEstimator bootstrapRemainder
  trueUnstudentizedCdfExpansion :
    ∀ n x,
      trueUnstudentizedCdf n x =
        trueUnstudentizedEdgeworthApproximation n x
  bootstrapUnstudentizedCdfExpansion :
    ∀ n ω x,
      bootstrapUnstudentizedCdf n ω x =
        bootstrapUnstudentizedEdgeworthApproximation n ω x
  /-- Difference between the leading normal terms. -/
  leadingNormalTermDifference : ℕ -> Ω -> ℝ
  leadingNormalTermDifference_eq :
    leadingNormalTermDifference =
      vaart1998_unstudentizedLeadingNormalTermDifferenceSup
        normalCdf scale scaleEstimator
  /-- Scale-estimator error `hat sigma_n - sigma_n` in source notation. -/
  scaleEstimatorDistance : ℕ -> Ω -> ℝ
  scaleEstimatorDistance_eq_statement : Prop
  scaleEstimatorDistance_eq : scaleEstimatorDistance_eq_statement
  scaleEstimatorHalfRate :
    vaart1998_stochasticOrderAtRate P scaleEstimatorDistance
      vaart1998_inverseSqrtRate
  /-- The leading-term difference is generally controlled only at first order. -/
  leadingNormalTermDifferenceHalfRate :
    vaart1998_stochasticOrderAtRate P leadingNormalTermDifference
      vaart1998_inverseSqrtRate
  percentileMethodFirstOrderCeiling_statement : Prop
  percentileMethodFirstOrderCeiling :
    percentileMethodFirstOrderCeiling_statement
  percentileBootstrapKSErrorSqrt :
    vaart1998_bootstrapKolmogorovSmirnovCorrectAtRate
      P trueUnstudentizedCdf bootstrapUnstudentizedCdf
      vaart1998_inverseSqrtRate
  /-- Reuse of the preceding percentile-`t` `O_P(n^{-1})` rate. -/
  percentileTBootstrapKSErrorOrderOne :
    vaart1998_bootstrapKolmogorovSmirnovCorrectAtRate
      P edgeworthSubtraction.trueStudentizedCdf
      edgeworthSubtraction.bootstrapStudentizedCdf
      (vaart1998_inversePowerRate 1)
  oneSidedCorrectnessMatchesDistributionRate_statement : Prop
  oneSidedCorrectnessMatchesDistributionRate :
    oneSidedCorrectnessMatchesDistributionRate_statement
  equalTailedCancellationOrderOne_statement : Prop
  equalTailedCancellationOrderOne :
    equalTailedCancellationOrderOne_statement

namespace Vaart1998Section23_3PercentileMethodUnstudentizedSource

section

variable {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
variable [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
variable [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
variable {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
variable {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
variable (S :
  Vaart1998Section23_3PercentileMethodUnstudentizedSource
    (ΩBootstrap := ΩBootstrap)
    (SampleSpace := SampleSpace) (Parameter := Parameter)
    P LimitLaw)

theorem true_unstudentized_edgeworth_display :
    S.trueUnstudentizedEdgeworthApproximation =
      vaart1998_unstudentizedEdgeworthExpansion
        S.normalCdf S.normalDensity S.q1True S.q2True
        S.scale S.trueRemainder :=
  S.trueUnstudentizedEdgeworthApproximation_eq

theorem bootstrap_unstudentized_edgeworth_display :
    S.bootstrapUnstudentizedEdgeworthApproximation =
      vaart1998_bootstrapUnstudentizedEdgeworthExpansion
        S.normalCdf S.normalDensity S.q1Bootstrap S.q2Bootstrap
        S.scaleEstimator S.bootstrapRemainder :=
  S.bootstrapUnstudentizedEdgeworthApproximation_eq

theorem true_unstudentized_cdf_expansion (n : ℕ) (x : ℝ) :
    S.trueUnstudentizedCdf n x =
      S.trueUnstudentizedEdgeworthApproximation n x :=
  S.trueUnstudentizedCdfExpansion n x

theorem bootstrap_unstudentized_cdf_expansion
    (n : ℕ) (ω : Ω) (x : ℝ) :
    S.bootstrapUnstudentizedCdf n ω x =
      S.bootstrapUnstudentizedEdgeworthApproximation n ω x :=
  S.bootstrapUnstudentizedCdfExpansion n ω x

theorem q_polynomials_differ_from_studentized_source :
    S.qPolynomialsDifferFromStudentized_statement :=
  S.qPolynomialsDifferFromStudentized

theorem leading_normal_term_difference_display :
    S.leadingNormalTermDifference =
      vaart1998_unstudentizedLeadingNormalTermDifferenceSup
        S.normalCdf S.scale S.scaleEstimator :=
  S.leadingNormalTermDifference_eq

theorem scale_estimator_half_rate :
    vaart1998_stochasticOrderAtRate P S.scaleEstimatorDistance
      vaart1998_inverseSqrtRate :=
  S.scaleEstimatorHalfRate

theorem leading_normal_term_difference_half_rate :
    vaart1998_stochasticOrderAtRate P S.leadingNormalTermDifference
      vaart1998_inverseSqrtRate :=
  S.leadingNormalTermDifferenceHalfRate

theorem percentile_method_first_order_ceiling_source :
    S.percentileMethodFirstOrderCeiling_statement :=
  S.percentileMethodFirstOrderCeiling

theorem percentile_bootstrap_ks_error_sqrt :
    vaart1998_bootstrapKolmogorovSmirnovCorrectAtRate
      P S.trueUnstudentizedCdf S.bootstrapUnstudentizedCdf
      vaart1998_inverseSqrtRate :=
  S.percentileBootstrapKSErrorSqrt

theorem percentile_t_bootstrap_ks_error_order_one :
    vaart1998_bootstrapKolmogorovSmirnovCorrectAtRate
      P S.edgeworthSubtraction.trueStudentizedCdf
      S.edgeworthSubtraction.bootstrapStudentizedCdf
      (vaart1998_inversePowerRate 1) :=
  S.percentileTBootstrapKSErrorOrderOne

theorem one_sided_correctness_matches_distribution_rate_source :
    S.oneSidedCorrectnessMatchesDistributionRate_statement :=
  S.oneSidedCorrectnessMatchesDistributionRate

theorem equal_tailed_cancellation_order_one_source :
    S.equalTailedCancellationOrderOne_statement :=
  S.equalTailedCancellationOrderOne

end

end Vaart1998Section23_3PercentileMethodUnstudentizedSource

/--
Right side of the Edgeworth expansion evaluated at the bootstrap
studentized upper quantile `hat xi_{n,alpha}`.
-/
def vaart1998_percentileTBootstrapQuantileEquationRHS
    {Ω : Type*} (normalCdf normalDensity : ℝ -> ℝ)
    (p1Bootstrap : ℕ -> Ω -> ℝ -> ℝ)
    (bootstrapUpperQuantile : ℕ -> Ω -> ℝ)
    (remainder : ℕ -> Ω -> ℝ) (n : ℕ) (ω : Ω) : ℝ :=
  normalCdf (bootstrapUpperQuantile n ω) +
    p1Bootstrap n ω (bootstrapUpperQuantile n ω) *
      vaart1998_inverseSqrtRate n *
      normalDensity (bootstrapUpperQuantile n ω) +
    remainder n ω

/--
Conditional Cornish-Fisher approximation for the percentile-`t` bootstrap
upper quantile.
-/
def vaart1998_percentileTCornishFisherQuantileExpansion
    {Ω : Type*} (p1True : ℝ -> ℝ) (zAlpha : ℝ)
    (remainder : ℕ -> Ω -> ℝ) (n : ℕ) (ω : Ω) : ℝ :=
  zAlpha - p1True zAlpha * vaart1998_inverseSqrtRate n +
    remainder n ω

/-- Deterministic threshold obtained by dropping the `O_P(n^{-1})` term. -/
def vaart1998_percentileTAdjustedQuantileThreshold
    (p1True : ℝ -> ℝ) (zAlpha : ℝ) (n : ℕ) : ℝ :=
  zAlpha - p1True zAlpha * vaart1998_inverseSqrtRate n

/-- Studentized statistic shifted by the `O_P(n^{-1})` Cornish-Fisher term. -/
def vaart1998_percentileTShiftedStudentizedStatistic
    {Ω : Type*} (studentizedStatistic orderOneShift : ℕ -> Ω -> ℝ)
    (n : ℕ) (ω : Ω) : ℝ :=
  studentizedStatistic n ω - orderOneShift n ω

/--
One-term Edgeworth display after substituting the Cornish-Fisher threshold.
The final remainder absorbs the rigorous `O(n^{-1})` terms.
-/
def vaart1998_percentileTCoverageTaylorDisplay
    (normalCdf normalDensity p1True : ℝ -> ℝ)
    (zAlpha : ℝ) (remainder : ℕ -> ℝ) (n : ℕ) : ℝ :=
  let shifted :=
    vaart1998_percentileTAdjustedQuantileThreshold p1True zAlpha n
  normalCdf shifted +
    p1True shifted * vaart1998_inverseSqrtRate n *
      normalDensity shifted +
    remainder n

theorem vaart1998_percentileTCornishFisherQuantileExpansion_zero_remainder
    {Ω : Type*} (p1True : ℝ -> ℝ) (zAlpha : ℝ)
    (remainder : ℕ -> Ω -> ℝ) (n : ℕ) (ω : Ω)
    (hremainder : remainder n ω = 0) :
    vaart1998_percentileTCornishFisherQuantileExpansion
      p1True zAlpha remainder n ω =
      vaart1998_percentileTAdjustedQuantileThreshold p1True zAlpha n := by
  simp [vaart1998_percentileTCornishFisherQuantileExpansion,
    vaart1998_percentileTAdjustedQuantileThreshold, hremainder]

/--
Source package for van der Vaart 1998, Section 23.3's percentile-`t`
Cornish-Fisher quantile expansion and the Taylor cancellation giving
coverage error of order `O(n^{-1})`.
-/
structure Vaart1998Section23_3PercentileTCornishFisherSource
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    (P : ℕ -> Measure Ω) [∀ n : ℕ, IsProbabilityMeasure (P n)]
    (LimitLaw : Measure ΩLimit) [IsProbabilityMeasure LimitLaw] where
  /-- Reuse of the percentile-method comparison layer. -/
  percentileMethod :
    Vaart1998Section23_3PercentileMethodUnstudentizedSource
      (ΩBootstrap := ΩBootstrap)
      (SampleSpace := SampleSpace) (Parameter := Parameter)
      P LimitLaw
  /-- Nominal upper-tail level. -/
  alpha : ℝ
  /-- Standard-normal upper quantile `z_alpha`. -/
  zAlpha : ℝ
  zAlpha_eq :
    zAlpha =
      percentileMethod.edgeworthSubtraction.normalCoverage.normalQuantile
        alpha
  /-- Bootstrap upper quantile `hat xi_{n,alpha}`. -/
  bootstrapUpperQuantile : ℕ -> Ω -> ℝ
  bootstrapUpperQuantileImplicit_statement : Prop
  bootstrapUpperQuantileImplicit : bootstrapUpperQuantileImplicit_statement
  /-- Remainder in the evaluated bootstrap Edgeworth quantile equation. -/
  bootstrapQuantileEquationRemainder : ℕ -> Ω -> ℝ
  bootstrapQuantileEquationRemainderLittleOOrderOne :
    vaart1998_stochasticLittleOAtRate P
      bootstrapQuantileEquationRemainder (vaart1998_inversePowerRate 1)
  bootstrapQuantileEquation :
    ∀ n ω,
      1 - alpha =
        vaart1998_percentileTBootstrapQuantileEquationRHS
          percentileMethod.normalCdf percentileMethod.normalDensity
          percentileMethod.edgeworthSubtraction.p1Bootstrap
          bootstrapUpperQuantile bootstrapQuantileEquationRemainder n ω
  /-- Taylor expansion around `z_alpha` used before inversion. -/
  taylorExpansionAroundZAlpha_statement : Prop
  taylorExpansionAroundZAlpha : taylorExpansionAroundZAlpha_statement
  /-- Remainder in the conditional Cornish-Fisher expansion. -/
  cornishFisherRemainder : ℕ -> Ω -> ℝ
  cornishFisherRemainderLittleOOrderOne :
    vaart1998_stochasticLittleOAtRate P cornishFisherRemainder
      (vaart1998_inversePowerRate 1)
  cornishFisherExpansion :
    ∀ n ω,
      bootstrapUpperQuantile n ω =
        vaart1998_percentileTCornishFisherQuantileExpansion
          percentileMethod.edgeworthSubtraction.p1True
          zAlpha cornishFisherRemainder n ω
  /-- Studentized statistic `(hat theta_n - theta) / hat sigma_n`. -/
  studentizedStatistic : ℕ -> Ω -> ℝ
  /-- Random `O_P(n^{-1})` shift in the rewritten coverage probability. -/
  coverageOrderOneShift : ℕ -> Ω -> ℝ
  coverageOrderOneShiftRate :
    vaart1998_stochasticOrderAtRate P coverageOrderOneShift
      (vaart1998_inversePowerRate 1)
  shiftedStudentizedStatistic : ℕ -> Ω -> ℝ
  shiftedStudentizedStatistic_eq :
    shiftedStudentizedStatistic =
      vaart1998_percentileTShiftedStudentizedStatistic
        studentizedStatistic coverageOrderOneShift
  /-- Deterministic first-order Cornish-Fisher threshold. -/
  adjustedThreshold : ℕ -> ℝ
  adjustedThreshold_eq :
    adjustedThreshold =
      vaart1998_percentileTAdjustedQuantileThreshold
        percentileMethod.edgeworthSubtraction.p1True zAlpha
  rewrittenCoverageProbability_statement : Prop
  rewrittenCoverageProbability : rewrittenCoverageProbability_statement
  /-- One-term expansion after substituting the Cornish-Fisher threshold. -/
  coverageExpansionRemainder : ℕ -> ℝ
  coverageExpansion : ℕ -> ℝ
  coverageExpansion_eq :
    coverageExpansion =
      vaart1998_percentileTCoverageTaylorDisplay
        percentileMethod.normalCdf percentileMethod.normalDensity
        percentileMethod.edgeworthSubtraction.p1True zAlpha
        coverageExpansionRemainder
  /-- The Taylor-linear term of `Phi` cancels the leading middle term. -/
  taylorLinearCancellation_statement : Prop
  taylorLinearCancellation : taylorLinearCancellation_statement
  /-- The display equals `1 - alpha` up to order `O(n^{-1})`. -/
  coverageExpansionOrderOne_statement : Prop
  coverageExpansionOrderOne : coverageExpansionOrderOne_statement
  /-- Source conclusion: percentile-`t` coverage error is `O(n^{-1})`. -/
  percentileTConfidenceIntervalCoverageErrorOrderOne_statement : Prop
  percentileTConfidenceIntervalCoverageErrorOrderOne :
    percentileTConfidenceIntervalCoverageErrorOrderOne_statement

namespace Vaart1998Section23_3PercentileTCornishFisherSource

section

variable {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
variable [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
variable [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
variable {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
variable {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
variable (S :
  Vaart1998Section23_3PercentileTCornishFisherSource
    (ΩBootstrap := ΩBootstrap)
    (SampleSpace := SampleSpace) (Parameter := Parameter)
    P LimitLaw)

theorem bootstrap_quantile_equation (n : ℕ) (ω : Ω) :
    1 - S.alpha =
      vaart1998_percentileTBootstrapQuantileEquationRHS
        S.percentileMethod.normalCdf S.percentileMethod.normalDensity
        S.percentileMethod.edgeworthSubtraction.p1Bootstrap
        S.bootstrapUpperQuantile S.bootstrapQuantileEquationRemainder
        n ω :=
  S.bootstrapQuantileEquation n ω

theorem bootstrap_quantile_equation_remainder_little_o_order_one :
    vaart1998_stochasticLittleOAtRate P
      S.bootstrapQuantileEquationRemainder
      (vaart1998_inversePowerRate 1) :=
  S.bootstrapQuantileEquationRemainderLittleOOrderOne

theorem cornish_fisher_expansion (n : ℕ) (ω : Ω) :
    S.bootstrapUpperQuantile n ω =
      vaart1998_percentileTCornishFisherQuantileExpansion
        S.percentileMethod.edgeworthSubtraction.p1True
        S.zAlpha S.cornishFisherRemainder n ω :=
  S.cornishFisherExpansion n ω

theorem cornish_fisher_remainder_little_o_order_one :
    vaart1998_stochasticLittleOAtRate P S.cornishFisherRemainder
      (vaart1998_inversePowerRate 1) :=
  S.cornishFisherRemainderLittleOOrderOne

theorem shifted_studentized_statistic_display :
    S.shiftedStudentizedStatistic =
      vaart1998_percentileTShiftedStudentizedStatistic
        S.studentizedStatistic S.coverageOrderOneShift :=
  S.shiftedStudentizedStatistic_eq

theorem coverage_order_one_shift_rate :
    vaart1998_stochasticOrderAtRate P S.coverageOrderOneShift
      (vaart1998_inversePowerRate 1) :=
  S.coverageOrderOneShiftRate

theorem adjusted_threshold_display :
    S.adjustedThreshold =
      vaart1998_percentileTAdjustedQuantileThreshold
        S.percentileMethod.edgeworthSubtraction.p1True S.zAlpha :=
  S.adjustedThreshold_eq

theorem rewritten_coverage_probability_source :
    S.rewrittenCoverageProbability_statement :=
  S.rewrittenCoverageProbability

theorem coverage_expansion_display :
    S.coverageExpansion =
      vaart1998_percentileTCoverageTaylorDisplay
        S.percentileMethod.normalCdf S.percentileMethod.normalDensity
        S.percentileMethod.edgeworthSubtraction.p1True S.zAlpha
        S.coverageExpansionRemainder :=
  S.coverageExpansion_eq

theorem taylor_expansion_around_z_alpha_source :
    S.taylorExpansionAroundZAlpha_statement :=
  S.taylorExpansionAroundZAlpha

theorem taylor_linear_cancellation_source :
    S.taylorLinearCancellation_statement :=
  S.taylorLinearCancellation

theorem coverage_expansion_order_one_source :
    S.coverageExpansionOrderOne_statement :=
  S.coverageExpansionOrderOne

theorem percentile_t_confidence_interval_coverage_error_order_one_source :
    S.percentileTConfidenceIntervalCoverageErrorOrderOne_statement :=
  S.percentileTConfidenceIntervalCoverageErrorOrderOne

end

end Vaart1998Section23_3PercentileTCornishFisherSource

/-- Scalar coverage-error order for one-sided and two-sided displays. -/
def vaart1998_coverageErrorAtRate
    (coverage : ℕ -> ℝ) (target : ℝ) (rate : ℕ -> ℝ) : Prop :=
  ∃ C : ℝ, 0 ≤ C ∧
    ∀ᶠ n in atTop, |coverage n - target| ≤ C * rate n

/--
Conditional Cornish-Fisher expansion for the unstudentized percentile
quantile after scaling by `hat sigma_n`.
-/
def vaart1998_percentileCornishFisherScaledQuantileExpansion
    {Ω : Type*} (q1Bootstrap : ℕ -> Ω -> ℝ -> ℝ)
    (zAlpha : ℝ) (remainder : ℕ -> Ω -> ℝ)
    (n : ℕ) (ω : Ω) : ℝ :=
  zAlpha - q1Bootstrap n ω zAlpha * vaart1998_inverseSqrtRate n +
    remainder n ω

/-- Deterministic first-order threshold for percentile intervals. -/
def vaart1998_percentileAdjustedQuantileThreshold
    (q1True : ℝ -> ℝ) (zAlpha : ℝ) (n : ℕ) : ℝ :=
  zAlpha - q1True zAlpha * vaart1998_inverseSqrtRate n

/--
One-term Edgeworth display for the percentile method after substituting the
unstudentized Cornish-Fisher threshold.
-/
def vaart1998_percentileCoverageTaylorDisplay
    (normalCdf normalDensity p1True q1True : ℝ -> ℝ)
    (zAlpha : ℝ) (remainder : ℕ -> ℝ) (n : ℕ) : ℝ :=
  let shifted :=
    vaart1998_percentileAdjustedQuantileThreshold q1True zAlpha n
  normalCdf shifted +
    p1True shifted * vaart1998_inverseSqrtRate n *
      normalDensity shifted +
    remainder n

/--
Equal-tailed percentile display as the difference of two one-sided
Cornish-Fisher/Edgeworth displays.
-/
def vaart1998_percentileSymmetricCoverageTaylorDifference
    (normalCdf normalDensity p1True q1True : ℝ -> ℝ)
    (zAlpha zOneMinusAlpha : ℝ) (remainder : ℕ -> ℝ) (n : ℕ) :
    ℝ :=
  vaart1998_percentileCoverageTaylorDisplay
      normalCdf normalDensity p1True q1True zAlpha remainder n -
    vaart1998_percentileCoverageTaylorDisplay
      normalCdf normalDensity p1True q1True zOneMinusAlpha remainder n

/--
Source package for van der Vaart 1998, Section 23.3's percentile interval
Cornish-Fisher expansion and the asymmetric/symmetric coverage comparison.
-/
structure Vaart1998Section23_3PercentileIntervalCornishFisherSource
    {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
    [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
    [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
    (P : ℕ -> Measure Ω) [∀ n : ℕ, IsProbabilityMeasure (P n)]
    (LimitLaw : Measure ΩLimit) [IsProbabilityMeasure LimitLaw] where
  /-- Reuse of the percentile-`t` Cornish-Fisher layer. -/
  percentileT :
    Vaart1998Section23_3PercentileTCornishFisherSource
      (ΩBootstrap := ΩBootstrap)
      (SampleSpace := SampleSpace) (Parameter := Parameter)
      P LimitLaw
  /-- Nominal tail level. -/
  alpha : ℝ
  /-- Normal quantile `z_alpha`. -/
  zAlpha : ℝ
  /-- Opposite-tail quantile `z_{1-alpha}`. -/
  zOneMinusAlpha : ℝ
  zAlpha_eq : zAlpha = percentileT.zAlpha
  zOneMinusAlpha_eq :
    zOneMinusAlpha =
      percentileT.percentileMethod.edgeworthSubtraction.normalCoverage.normalQuantile
        (1 - alpha)
  /-- Unstudentized percentile bootstrap quantile `hat xi_{n,alpha}`. -/
  percentileUpperQuantile : ℕ -> Ω -> ℝ
  /-- Scaled quantile `hat xi_{n,alpha} / hat sigma_n`. -/
  scaledPercentileUpperQuantile : ℕ -> Ω -> ℝ
  scaledPercentileUpperQuantile_eq :
    scaledPercentileUpperQuantile =
      fun n ω =>
        percentileUpperQuantile n ω /
          percentileT.percentileMethod.scaleEstimator n ω
  /-- Remainder in the percentile Cornish-Fisher expansion. -/
  percentileCornishFisherRemainder : ℕ -> Ω -> ℝ
  percentileCornishFisherRemainderLittleOOrderOne :
    vaart1998_stochasticLittleOAtRate P
      percentileCornishFisherRemainder (vaart1998_inversePowerRate 1)
  percentileCornishFisherExpansion :
    ∀ n ω,
      scaledPercentileUpperQuantile n ω =
        vaart1998_percentileCornishFisherScaledQuantileExpansion
          percentileT.percentileMethod.q1Bootstrap zAlpha
          percentileCornishFisherRemainder n ω
  /-- Coverage probability `P(hat theta_n - theta <= hat xi_{n,alpha})`. -/
  percentileCoverageProbability : ℕ -> ℝ
  percentileCoverageRewrite_statement : Prop
  percentileCoverageRewrite : percentileCoverageRewrite_statement
  /-- Coverage expansion after inserting the percentile Cornish-Fisher term. -/
  percentileCoverageRemainder : ℕ -> ℝ
  percentileCoverageExpansion : ℕ -> ℝ
  percentileCoverageExpansion_eq :
    percentileCoverageExpansion =
      vaart1998_percentileCoverageTaylorDisplay
        percentileT.percentileMethod.normalCdf
        percentileT.percentileMethod.normalDensity
        percentileT.percentileMethod.edgeworthSubtraction.p1True
        percentileT.percentileMethod.q1True zAlpha
        percentileCoverageRemainder
  /-- Source statement that `p_1` and `q_1` are generally different. -/
  p1q1Different_statement : Prop
  p1q1Different : p1q1Different_statement
  /-- The percentile method lacks the percentile-`t` first-order cancellation. -/
  noFirstOrderCancellation_statement : Prop
  noFirstOrderCancellation : noFirstOrderCancellation_statement
  asymmetricPercentileCoverageErrorSqrt :
    vaart1998_coverageErrorAtRate percentileCoverageProbability
      (1 - alpha) vaart1998_inverseSqrtRate
  /-- Equal-tailed percentile interval coverage probability. -/
  symmetricPercentileCoverageProbability : ℕ -> ℝ
  symmetricCoverageRemainder : ℕ -> ℝ
  symmetricCoverageExpansion : ℕ -> ℝ
  symmetricCoverageExpansion_eq :
    symmetricCoverageExpansion =
      vaart1998_percentileSymmetricCoverageTaylorDifference
        percentileT.percentileMethod.normalCdf
        percentileT.percentileMethod.normalDensity
        percentileT.percentileMethod.edgeworthSubtraction.p1True
        percentileT.percentileMethod.q1True zAlpha zOneMinusAlpha
        symmetricCoverageRemainder
  p1Even_statement : Prop
  p1Even : p1Even_statement
  q1Even_statement : Prop
  q1Even : q1Even_statement
  /-- Evenness cancels the `n^{-1/2}` terms in the symmetric difference. -/
  symmetricFirstOrderCancellation_statement : Prop
  symmetricFirstOrderCancellation : symmetricFirstOrderCancellation_statement
  symmetricPercentileCoverageErrorOrderOne :
    vaart1998_coverageErrorAtRate symmetricPercentileCoverageProbability
      (1 - 2 * alpha) (vaart1998_inversePowerRate 1)
  sameOrderAsSymmetricNormalAndPercentileT_statement : Prop
  sameOrderAsSymmetricNormalAndPercentileT :
    sameOrderAsSymmetricNormalAndPercentileT_statement

namespace Vaart1998Section23_3PercentileIntervalCornishFisherSource

section

variable {Ω ΩBootstrap ΩLimit SampleSpace Parameter : Type*}
variable [MeasurableSpace Ω] [MeasurableSpace ΩBootstrap]
variable [MeasurableSpace ΩLimit] [MeasurableSpace SampleSpace]
variable {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
variable {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
variable (S :
  Vaart1998Section23_3PercentileIntervalCornishFisherSource
    (ΩBootstrap := ΩBootstrap)
    (SampleSpace := SampleSpace) (Parameter := Parameter)
    P LimitLaw)

theorem scaled_percentile_upper_quantile_display :
    S.scaledPercentileUpperQuantile =
      fun n ω =>
        S.percentileUpperQuantile n ω /
          S.percentileT.percentileMethod.scaleEstimator n ω :=
  S.scaledPercentileUpperQuantile_eq

theorem percentile_cornish_fisher_expansion (n : ℕ) (ω : Ω) :
    S.scaledPercentileUpperQuantile n ω =
      vaart1998_percentileCornishFisherScaledQuantileExpansion
        S.percentileT.percentileMethod.q1Bootstrap S.zAlpha
        S.percentileCornishFisherRemainder n ω :=
  S.percentileCornishFisherExpansion n ω

theorem percentile_cornish_fisher_remainder_little_o_order_one :
    vaart1998_stochasticLittleOAtRate P
      S.percentileCornishFisherRemainder
      (vaart1998_inversePowerRate 1) :=
  S.percentileCornishFisherRemainderLittleOOrderOne

theorem percentile_coverage_rewrite_source :
    S.percentileCoverageRewrite_statement :=
  S.percentileCoverageRewrite

theorem percentile_coverage_expansion_display :
    S.percentileCoverageExpansion =
      vaart1998_percentileCoverageTaylorDisplay
        S.percentileT.percentileMethod.normalCdf
        S.percentileT.percentileMethod.normalDensity
        S.percentileT.percentileMethod.edgeworthSubtraction.p1True
        S.percentileT.percentileMethod.q1True S.zAlpha
        S.percentileCoverageRemainder :=
  S.percentileCoverageExpansion_eq

theorem p1q1_different_source :
    S.p1q1Different_statement :=
  S.p1q1Different

theorem no_first_order_cancellation_source :
    S.noFirstOrderCancellation_statement :=
  S.noFirstOrderCancellation

theorem asymmetric_percentile_coverage_error_sqrt :
    vaart1998_coverageErrorAtRate S.percentileCoverageProbability
      (1 - S.alpha) vaart1998_inverseSqrtRate :=
  S.asymmetricPercentileCoverageErrorSqrt

theorem symmetric_coverage_expansion_display :
    S.symmetricCoverageExpansion =
      vaart1998_percentileSymmetricCoverageTaylorDifference
        S.percentileT.percentileMethod.normalCdf
        S.percentileT.percentileMethod.normalDensity
        S.percentileT.percentileMethod.edgeworthSubtraction.p1True
        S.percentileT.percentileMethod.q1True
        S.zAlpha S.zOneMinusAlpha S.symmetricCoverageRemainder :=
  S.symmetricCoverageExpansion_eq

theorem p1_even_source :
    S.p1Even_statement :=
  S.p1Even

theorem q1_even_source :
    S.q1Even_statement :=
  S.q1Even

theorem symmetric_first_order_cancellation_source :
    S.symmetricFirstOrderCancellation_statement :=
  S.symmetricFirstOrderCancellation

theorem symmetric_percentile_coverage_error_order_one :
    vaart1998_coverageErrorAtRate S.symmetricPercentileCoverageProbability
      (1 - 2 * S.alpha) (vaart1998_inversePowerRate 1) :=
  S.symmetricPercentileCoverageErrorOrderOne

theorem same_order_as_symmetric_normal_and_percentile_t_source :
    S.sameOrderAsSymmetricNormalAndPercentileT_statement :=
  S.sameOrderAsSymmetricNormalAndPercentileT

end

end Vaart1998Section23_3PercentileIntervalCornishFisherSource

end AsymptoticStatistics
end StatInference
