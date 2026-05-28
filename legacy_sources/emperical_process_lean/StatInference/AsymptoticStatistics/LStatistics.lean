import StatInference.AsymptoticStatistics.Quantiles

/-!
# van der Vaart 1998 Chapter 22 L-statistics

This module opens the Chapter 22 lane.  The first layer records the
finite-sample display for L-statistics, trimmed and Winsorized means, range
examples, the Hajek-projection weight appearing in Theorem 22.3, and the
delta-method quantile-functional display.
-/

noncomputable section

namespace StatInference
namespace AsymptoticStatistics

open Filter MeasureTheory ProbabilityTheory
open scoped BigOperators ENNReal ProbabilityTheory Topology

/-- Chapter 22 L-statistic display
`sum_{i=1}^n c_{n i} a(X_{n(i)})`. -/
def vaart1998_lStatistic
    {Ω : Type*} (orderStatistic : ℕ -> ℕ -> Ω -> ℝ)
    (coefficient : ℕ -> ℕ -> ℝ) (score : ℝ -> ℝ)
    (n : ℕ) (ω : Ω) : ℝ :=
  ∑ i ∈ Finset.Icc 1 n,
    coefficient n i * score (orderStatistic n i ω)

/-- Generated coefficients `c_{n i} = phi(i/(n+1))`. -/
def vaart1998_lStatisticGeneratedCoefficient
    (phi : ℝ -> ℝ) (n i : ℕ) : ℝ :=
  phi ((i : ℝ) / ((n : ℝ) + 1))

/-- The sample mean as the unweighted L-statistic over order statistics. -/
def vaart1998_orderStatisticSampleMean
    {Ω : Type*} (orderStatistic : ℕ -> ℕ -> Ω -> ℝ)
    (n : ℕ) (ω : Ω) : ℝ :=
  (n : ℝ)⁻¹ * ∑ i ∈ Finset.Icc 1 n, orderStatistic n i ω

/-- The alpha-trimmed mean display, parameterized by the integer trim count. -/
def vaart1998_trimmedMean
    {Ω : Type*} (orderStatistic : ℕ -> ℕ -> Ω -> ℝ)
    (trimCount : ℕ -> ℕ) (n : ℕ) (ω : Ω) : ℝ :=
  ((n - 2 * trimCount n : ℕ) : ℝ)⁻¹ *
    ∑ i ∈ Finset.Icc (trimCount n + 1) (n - trimCount n),
      orderStatistic n i ω

/-- The alpha-Winsorized mean display, parameterized by the integer trim count. -/
def vaart1998_winsorizedMean
    {Ω : Type*} (orderStatistic : ℕ -> ℕ -> Ω -> ℝ)
    (trimCount : ℕ -> ℕ) (n : ℕ) (ω : Ω) : ℝ :=
  (n : ℝ)⁻¹ *
    ((trimCount n : ℝ) * orderStatistic n (trimCount n) ω +
      (∑ i ∈ Finset.Icc (trimCount n + 1) (n - trimCount n),
        orderStatistic n i ω) +
      (trimCount n : ℝ) *
        orderStatistic n (n - trimCount n + 1) ω)

/-- Interquantile range display `X_{n(upper)} - X_{n(lower)}`. -/
def vaart1998_interquantileRange
    {Ω : Type*} (orderStatistic : ℕ -> ℕ -> Ω -> ℝ)
    (lowerIndex upperIndex : ℕ -> ℕ) (n : ℕ) (ω : Ω) : ℝ :=
  orderStatistic n (upperIndex n) ω -
    orderStatistic n (lowerIndex n) ω

/-- Sample range display `X_{n(n)} - X_{n(1)}`. -/
def vaart1998_sampleRange
    {Ω : Type*} (orderStatistic : ℕ -> ℕ -> Ω -> ℝ)
    (n : ℕ) (ω : Ω) : ℝ :=
  orderStatistic n n ω - orderStatistic n 1 ω

/-- Conditional CDF of `X_{n(i)}` given one observation `X_k = x`. -/
def vaart1998_orderStatisticConditionalCdfGivenObservation
    (orderStatisticCdf : ℕ -> ℕ -> ℝ -> ℝ)
    (n i : ℕ) (x y : ℝ) : ℝ :=
  if y < x then orderStatisticCdf (n - 1) i y
  else orderStatisticCdf (n - 1) (i - 1) y

/-- Binomial point mass `B_{n,p}(i)`. -/
def vaart1998_binomialMassDisplay (n : ℕ) (p : ℝ) (i : ℕ) : ℝ :=
  (Nat.choose n i : ℝ) * p ^ i * (1 - p) ^ (n - i)

/-- The weight `e_n(y)=sum_i c_{n i} B_{n-1,F(y)}(i-1)`. -/
def vaart1998_lStatisticProjectionWeight
    (coefficient : ℕ -> ℕ -> ℝ)
    (binomialMass : ℕ -> ℝ -> ℕ -> ℝ) (cdf : ℝ -> ℝ)
    (n : ℕ) (y : ℝ) : ℝ :=
  ∑ i ∈ Finset.Icc 1 n,
    coefficient n i * binomialMass (n - 1) (cdf y) (i - 1)

/-- Generated-weight form
`e_n(y)=E phi((B_n+1)/(n+1))`, kept as the finite binomial sum. -/
def vaart1998_lStatisticGeneratedProjectionWeight
    (phi : ℝ -> ℝ) (binomialMass : ℕ -> ℝ -> ℕ -> ℝ)
    (cdf : ℝ -> ℝ) (n : ℕ) (y : ℝ) : ℝ :=
  ∑ i ∈ Finset.Icc 1 n,
    vaart1998_lStatisticGeneratedCoefficient phi n i *
      binomialMass (n - 1) (cdf y) (i - 1)

/-- Limit projection weight `e(y)=phi(F(y))`. -/
def vaart1998_lStatisticLimitProjectionWeight
    (phi cdf : ℝ -> ℝ) (y : ℝ) : ℝ :=
  phi (cdf y)

/-- Projection integrand `n(F_n-F)(y) e_n(y)`. -/
def vaart1998_lStatisticProjectionIntegrand
    (empiricalCdf : ℕ -> ℝ -> ℝ) (cdf : ℝ -> ℝ)
    (projectionWeight : ℕ -> ℝ -> ℝ) (n : ℕ) (y : ℝ) : ℝ :=
  (n : ℝ) * (empiricalCdf n y - cdf y) * projectionWeight n y

/-- Centered Hajek projection display
`- int n(F_n-F)(y) e_n(y) dy`. -/
def vaart1998_lStatisticCenteredHajekProjection
    (integralFunctional : (ℝ -> ℝ) -> ℝ)
    (empiricalCdf : ℕ -> ℝ -> ℝ) (cdf : ℝ -> ℝ)
    (projectionWeight : ℕ -> ℝ -> ℝ) (n : ℕ) : ℝ :=
  - integralFunctional
      (fun y =>
        vaart1998_lStatisticProjectionIntegrand
          empiricalCdf cdf projectionWeight n y)

/-- The Theorem 22.3 variance functional
`iint phi(F x) phi(F y) (F(x wedge y)-F x F y) dx dy`. -/
def vaart1998_lStatisticAsymptoticVariance
    (doubleIntegral : (ℝ -> ℝ -> ℝ) -> ℝ)
    (phi cdf : ℝ -> ℝ) : ℝ :=
  doubleIntegral
    (fun x y =>
      phi (cdf x) * phi (cdf y) *
        (cdf (min x y) - cdf x * cdf y))

/-- Projection-variance display with the finite `e_n` weights. -/
def vaart1998_lStatisticProjectionVariance
    (doubleIntegral : (ℝ -> ℝ -> ℝ) -> ℝ)
    (cdf : ℝ -> ℝ) (projectionWeight : ℕ -> ℝ -> ℝ)
    (n : ℕ) : ℝ :=
  doubleIntegral
    (fun x y =>
      (cdf (min x y) - cdf x * cdf y) *
        projectionWeight n x * projectionWeight n y)

/-- The covariance-kernel double sum `R_n(x,y)` from Theorem 22.3. -/
def vaart1998_lStatisticCovarianceKernel
    (coefficient : ℕ -> ℕ -> ℝ)
    (orderIndicatorCovariance : ℕ -> ℕ -> ℕ -> ℝ -> ℝ -> ℝ)
    (n : ℕ) (x y : ℝ) : ℝ :=
  (n : ℝ)⁻¹ *
    ∑ i ∈ Finset.Icc 1 n,
      ∑ j ∈ Finset.Icc 1 n,
        coefficient n i * coefficient n j *
          orderIndicatorCovariance n i j x y

/-- Hoeffding tail bound `2 exp(-2 n epsilon^2)` used in Theorem 22.3. -/
def vaart1998_lStatisticHoeffdingTailBound
    (n : ℕ) (epsilon : ℝ) : ℝ :=
  2 * Real.exp (-(2 * (n : ℝ) * epsilon ^ 2))

/-- Delta-method functional `F -> int_0^1 a(F^{-1}) dK`. -/
def vaart1998_lStatisticQuantileFunctional
    (signedMeasureIntegral : (ℝ -> ℝ) -> ℝ)
    (score quantile : ℝ -> ℝ) : ℝ :=
  signedMeasureIntegral (fun s => score (quantile s))

/-- Generated-measure coefficients `c_{n i}=K((i-1)/n, i/n]` from (22.4). -/
def vaart1998_lStatisticGeneratedMeasureCoefficient
    (KIntervalMass : ℝ -> ℝ -> ℝ) (n i : ℕ) : ℝ :=
  KIntervalMass (((i : ℝ) - 1) / (n : ℝ)) ((i : ℝ) / (n : ℝ))

/-- Equation (22.4), displayed as an L-statistic generated by an interval
mass functional for the signed measure `K`. -/
def vaart1998_lStatisticGeneratedMeasureDisplay
    {Ω : Type*} (orderStatistic : ℕ -> ℕ -> Ω -> ℝ)
    (KIntervalMass : ℝ -> ℝ -> ℝ) (score : ℝ -> ℝ)
    (n : ℕ) (ω : Ω) : ℝ :=
  ∑ i ∈ Finset.Icc 1 n,
    vaart1998_lStatisticGeneratedMeasureCoefficient KIntervalMass n i *
      score (orderStatistic n i ω)

/-- Example 22.5 trimmed-mean functional generated by uniform mass on
`(alpha, 1-alpha)`, with the interval integral supplied abstractly. -/
def vaart1998_trimmedMeanGeneratedFunctional
    (alpha : ℝ) (middleIntegral : (ℝ -> ℝ) -> ℝ)
    (quantile : ℝ -> ℝ) : ℝ :=
  (1 - 2 * alpha)⁻¹ * middleIntegral quantile

/-- Example 22.5 finite generated trimmed-mean display with ceiling endpoint
weights. -/
def vaart1998_trimmedMeanGeneratedOrderStatisticDisplay
    {Ω : Type*} (orderStatistic : ℕ -> ℕ -> Ω -> ℝ)
    (alpha : ℝ) (ceilingAlphaN : ℕ -> ℕ) (n : ℕ) (ω : Ω) : ℝ :=
  ((n : ℝ) - 2 * alpha * (n : ℝ))⁻¹ *
    (((ceilingAlphaN n : ℝ) - alpha * (n : ℝ)) *
        orderStatistic n (ceilingAlphaN n) ω +
      (∑ i ∈ Finset.Icc (ceilingAlphaN n + 1) (n - ceilingAlphaN n),
        orderStatistic n i ω) +
      ((ceilingAlphaN n : ℝ) - alpha * (n : ℝ)) *
        orderStatistic n (n - ceilingAlphaN n + 1) ω)

/-- Example 22.5 Winsorized functional: middle Lebesgue mass plus point masses
`alpha` at `alpha` and `1-alpha`. -/
def vaart1998_winsorizedMeanGeneratedFunctional
    (alpha : ℝ) (middleIntegral : (ℝ -> ℝ) -> ℝ)
    (quantile : ℝ -> ℝ) : ℝ :=
  middleIntegral quantile + alpha * quantile alpha +
    alpha * quantile (1 - alpha)

/-- Signed two-point quantile functional used for interquantile ranges. -/
def vaart1998_signedTwoPointQuantileFunctional
    (lower upper lowerMass upperMass : ℝ) (quantile : ℝ -> ℝ) : ℝ :=
  lowerMass * quantile lower + upperMass * quantile upper

/-- The usual positive interquartile range `Q(3/4)-Q(1/4)`. -/
def vaart1998_interquartileRangeGeneratedFunctional
    (quantile : ℝ -> ℝ) : ℝ :=
  vaart1998_signedTwoPointQuantileFunctional
    (1 / 4) (3 / 4) (-1) 1 quantile

/-- Quantile influence kernel from Example 20.5 as used in (22.6). -/
def vaart1998_quantileInfluenceKernel
    (quantile density : ℝ -> ℝ) (x u : ℝ) : ℝ :=
  ((if x ≤ quantile u then (1 : ℝ) else 0) - u) /
    density (quantile u)

/-- Formula (22.6): influence function through the empirical quantile map. -/
def vaart1998_lStatisticInfluenceFunction22_6
    (signedMeasureIntegral : (ℝ -> ℝ) -> ℝ)
    (scoreDerivative quantile density : ℝ -> ℝ) (x : ℝ) : ℝ :=
  - signedMeasureIntegral
      (fun u =>
        scoreDerivative (quantile u) *
          vaart1998_quantileInfluenceKernel quantile density x u)

/-- The second line of (22.6), after the quantile transformation. -/
def vaart1998_lStatisticInfluenceFunction22_6Transformed
    (pushforwardIntegral : (ℝ -> ℝ) -> ℝ)
    (scoreDerivative cdf density : ℝ -> ℝ) (x : ℝ) : ℝ :=
  - pushforwardIntegral
      (fun y =>
        scoreDerivative y *
          (((if x ≤ y then (1 : ℝ) else 0) - cdf y) / density y))

/-- Formula (22.7), represented with the two partial-integration integrals
supplied abstractly. -/
def vaart1998_lStatisticPartialIntegrationFunctional
    (positiveTailIntegral nonpositiveIntegral : (ℝ -> ℝ) -> ℝ)
    (composedLeftTail composedSurvival : ℝ -> ℝ) : ℝ :=
  positiveTailIntegral composedSurvival -
    nonpositiveIntegral composedLeftTail

/-- Formula (22.8): influence function through a smooth generating measure
`K`, with the `da` integration supplied abstractly. -/
def vaart1998_lStatisticInfluenceFunction22_8
    (scoreMeasureIntegral : (ℝ -> ℝ) -> ℝ)
    (KDerivative cdf : ℝ -> ℝ) (x : ℝ) : ℝ :=
  - scoreMeasureIntegral
      (fun y =>
        KDerivative (cdf y) *
          ((if x ≤ y then (1 : ℝ) else 0) - cdf y))

/-- Lemma 22.9 quantile-functional map `Q ↦ ∫ a(Q) dK`. -/
def vaart1998_lStatisticQuantileMap
    (signedMeasureIntegral : (ℝ -> ℝ) -> ℝ)
    (score : ℝ -> ℝ) (Q : ℝ -> ℝ) : ℝ :=
  vaart1998_lStatisticQuantileFunctional signedMeasureIntegral score Q

/-- Lemma 22.9 derivative display `H ↦ ∫ a'(Q) H dK`. -/
def vaart1998_lStatisticQuantileDerivative
    (signedMeasureIntegral : (ℝ -> ℝ) -> ℝ)
    (scoreDerivative Q H : ℝ -> ℝ) : ℝ :=
  signedMeasureIntegral (fun u => scoreDerivative (Q u) * H u)

/-- Lemma 22.10 functional, viewed on distribution functions:
`F ↦ ∫ a(F^{-1}) dK`. -/
def vaart1998_lStatisticDistributionFunctional
    {DistFunc : Type*} (signedMeasureIntegral : (ℝ -> ℝ) -> ℝ)
    (score : ℝ -> ℝ) (quantileOfCdf : DistFunc -> ℝ -> ℝ)
    (F : DistFunc) : ℝ :=
  signedMeasureIntegral (fun u => score (quantileOfCdf F u))

/-- Perturbation path `F_t = F + t H_t` from the proof of Lemma 22.10. -/
def vaart1998_distributionFunctionPerturbation
    (cdf perturbation : ℝ -> ℝ) (t : ℝ) : ℝ -> ℝ :=
  fun x => cdf x + t * perturbation x

/-- The difference quotient integrand in the proof of Lemma 22.10. -/
def vaart1998_smoothGeneratingMeasureDifferenceQuotient
    (K cdfLeft perturbationLeft : ℝ -> ℝ) (t : ℝ) : ℝ -> ℝ :=
  fun y => (K (cdfLeft y + t * perturbationLeft y) - K (cdfLeft y)) / t

/-- Lemma 22.10 derivative display
`H ↦ -∫ (K' ∘ F_-) H da`. -/
def vaart1998_lStatisticSmoothKDerivative
    (scoreMeasureIntegral : (ℝ -> ℝ) -> ℝ)
    (KDerivative cdfLeft perturbation : ℝ -> ℝ) : ℝ :=
  - scoreMeasureIntegral (fun y => KDerivative (cdfLeft y) * perturbation y)

/-- Asymptotic linearity as a centered-scaled statistic minus its linear
influence approximation being `o_P(1)`. -/
def vaart1998_asymptoticallyLinearWithInfluence
    {Ω : Type*} [MeasurableSpace Ω]
    (P : ℕ -> Measure Ω) (statistic linearTerm : ℕ -> Ω -> ℝ) : Prop :=
  Vaart1998MeasureSeqConvergesInProbabilityToZero P
    (fun n ω => statistic n ω - linearTerm n ω)

/-- Example 22.11 trimmed-mean influence function from (22.8). -/
def vaart1998_trimmedMeanInfluenceFunction22_11
    (intervalIntegral : (ℝ -> ℝ) -> ℝ) (cdf : ℝ -> ℝ) (x : ℝ) : ℝ :=
  - intervalIntegral (fun y => (if x ≤ y then (1 : ℝ) else 0) - cdf y)

/-- Example 22.11 asymptotic variance display over the central quantile
interval, with the interval restriction supplied by `doubleIntegral`. -/
def vaart1998_trimmedMeanAsymptoticVariance22_11
    (doubleIntegral : (ℝ -> ℝ -> ℝ) -> ℝ) (cdf : ℝ -> ℝ) : ℝ :=
  doubleIntegral (fun x y => cdf (min x y) - cdf x * cdf y)

/-- Example 22.12 discrete point-mass part of the Winsorized functional. -/
def vaart1998_winsorizedMeanDiscretePart
    (alpha : ℝ) (quantile : ℝ -> ℝ) : ℝ :=
  alpha * quantile alpha + alpha * quantile (1 - alpha)

/-- Example 22.12 continuous middle part of the Winsorized functional. -/
def vaart1998_winsorizedMeanContinuousPart
    (middleIntegral : (ℝ -> ℝ) -> ℝ) (quantile : ℝ -> ℝ) : ℝ :=
  middleIntegral quantile

/-- Example 22.12 decomposition into discrete endpoint and continuous middle
parts. -/
def vaart1998_winsorizedMeanDecomposition
    (alpha : ℝ) (middleIntegral : (ℝ -> ℝ) -> ℝ)
    (quantile : ℝ -> ℝ) : ℝ :=
  vaart1998_winsorizedMeanContinuousPart middleIntegral quantile +
    vaart1998_winsorizedMeanDiscretePart alpha quantile

/-- Section 22.4 location family density `f(x - theta)`. -/
def vaart1998_locationFamilyDensity
    (baseDensity : ℝ -> ℝ) (theta x : ℝ) : ℝ :=
  baseDensity (x - theta)

/-- Section 22.4 centered and scaled location estimator. -/
def vaart1998_locationCenteredScaledEstimator
    {Ω : Type*} (estimator : ℕ -> Ω -> ℝ) (theta : ℝ) :
    ℕ -> Ω -> ℝ :=
  fun n ω => √(n : ℝ) * (estimator n ω - theta)

/-- Chapter 8 efficient influence function for location:
`- I_f^{-1} (f'/f)(x-theta)`. -/
def vaart1998_locationEfficientInfluence
    (fisherInformation : ℝ) (logDensityDerivative : ℝ -> ℝ)
    (theta x : ℝ) : ℝ :=
  - fisherInformation⁻¹ * logDensityDerivative (x - theta)

/-- Section 22.4 efficient linear term
`- n^{-1/2} sum_i I_f^{-1} (f'/f)(X_i-theta)`. -/
def vaart1998_locationEfficientLinearTerm
    {Ω : Type*} (observation : ℕ -> ℕ -> Ω -> ℝ)
    (fisherInformation : ℝ) (logDensityDerivative : ℝ -> ℝ)
    (theta : ℝ) (n : ℕ) (ω : Ω) : ℝ :=
  - (√(n : ℝ))⁻¹ *
    ∑ i ∈ Finset.Icc 1 n,
      fisherInformation⁻¹ *
        logDensityDerivative (observation n i ω - theta)

/-- Left side of the Section 22.4 matching equation:
`K'(F(x-theta)) a'(x)`. -/
def vaart1998_locationLEstimatorMatchingLeft
    (KDerivative cdf transformDerivative : ℝ -> ℝ)
    (theta x : ℝ) : ℝ :=
  KDerivative (cdf (x - theta)) * transformDerivative x

/-- Right side of the Section 22.4 matching equation:
`- ((1/I_f) (f'/f)(x-theta))'`. -/
def vaart1998_locationLEstimatorMatchingRight
    (fisherInformation : ℝ) (logDensityDerivativeDerivative : ℝ -> ℝ)
    (theta x : ℝ) : ℝ :=
  - fisherInformation⁻¹ * logDensityDerivativeDerivative (x - theta)

/-- The special Section 22.4 choice with `a(x)=x`:
`K'(u) = - ((1/I_f)(f'/f))'(F^{-1}(u))`. -/
def vaart1998_locationEfficientGeneratingKDerivative
    (fisherInformation : ℝ)
    (logDensityDerivativeDerivative quantile : ℝ -> ℝ)
    (u : ℝ) : ℝ :=
  - fisherInformation⁻¹ * logDensityDerivativeDerivative (quantile u)

/-- Source display `n^{-1/2}(T_n - center_n)`. -/
def vaart1998_sqrtInvNCenteredStatisticSequence
    {Ω : Type*} (statistic : ℕ -> Ω -> ℝ) (center : ℕ -> ℝ) :
    ℕ -> Ω -> ℝ :=
  fun n ω => (√(n : ℝ))⁻¹ * (statistic n ω - center n)

theorem vaart1998_lStatistic_apply
    {Ω : Type*} (orderStatistic : ℕ -> ℕ -> Ω -> ℝ)
    (coefficient : ℕ -> ℕ -> ℝ) (score : ℝ -> ℝ)
    (n : ℕ) (ω : Ω) :
    vaart1998_lStatistic orderStatistic coefficient score n ω =
      ∑ i ∈ Finset.Icc 1 n,
        coefficient n i * score (orderStatistic n i ω) :=
  rfl

theorem vaart1998_trimmedMean_apply
    {Ω : Type*} (orderStatistic : ℕ -> ℕ -> Ω -> ℝ)
    (trimCount : ℕ -> ℕ) (n : ℕ) (ω : Ω) :
    vaart1998_trimmedMean orderStatistic trimCount n ω =
      ((n - 2 * trimCount n : ℕ) : ℝ)⁻¹ *
        ∑ i ∈ Finset.Icc (trimCount n + 1) (n - trimCount n),
          orderStatistic n i ω :=
  rfl

theorem vaart1998_winsorizedMean_apply
    {Ω : Type*} (orderStatistic : ℕ -> ℕ -> Ω -> ℝ)
    (trimCount : ℕ -> ℕ) (n : ℕ) (ω : Ω) :
    vaart1998_winsorizedMean orderStatistic trimCount n ω =
      (n : ℝ)⁻¹ *
        ((trimCount n : ℝ) * orderStatistic n (trimCount n) ω +
          (∑ i ∈ Finset.Icc (trimCount n + 1) (n - trimCount n),
            orderStatistic n i ω) +
          (trimCount n : ℝ) *
            orderStatistic n (n - trimCount n + 1) ω) :=
  rfl

theorem vaart1998_lStatisticGeneratedMeasureCoefficient_apply
    (KIntervalMass : ℝ -> ℝ -> ℝ) (n i : ℕ) :
    vaart1998_lStatisticGeneratedMeasureCoefficient KIntervalMass n i =
      KIntervalMass (((i : ℝ) - 1) / (n : ℝ))
        ((i : ℝ) / (n : ℝ)) :=
  rfl

theorem vaart1998_lStatisticGeneratedMeasureDisplay_apply
    {Ω : Type*} (orderStatistic : ℕ -> ℕ -> Ω -> ℝ)
    (KIntervalMass : ℝ -> ℝ -> ℝ) (score : ℝ -> ℝ)
    (n : ℕ) (ω : Ω) :
    vaart1998_lStatisticGeneratedMeasureDisplay
        orderStatistic KIntervalMass score n ω =
      ∑ i ∈ Finset.Icc 1 n,
        vaart1998_lStatisticGeneratedMeasureCoefficient KIntervalMass n i *
          score (orderStatistic n i ω) :=
  rfl

theorem vaart1998_lStatisticQuantileDerivative_apply
    (signedMeasureIntegral : (ℝ -> ℝ) -> ℝ)
    (scoreDerivative Q H : ℝ -> ℝ) :
    vaart1998_lStatisticQuantileDerivative
        signedMeasureIntegral scoreDerivative Q H =
      signedMeasureIntegral (fun u => scoreDerivative (Q u) * H u) :=
  rfl

theorem vaart1998_lStatisticDistributionFunctional_apply
    {DistFunc : Type*} (signedMeasureIntegral : (ℝ -> ℝ) -> ℝ)
    (score : ℝ -> ℝ) (quantileOfCdf : DistFunc -> ℝ -> ℝ)
    (F : DistFunc) :
    vaart1998_lStatisticDistributionFunctional
        signedMeasureIntegral score quantileOfCdf F =
      signedMeasureIntegral (fun u => score (quantileOfCdf F u)) :=
  rfl

theorem vaart1998_lStatisticSmoothKDerivative_apply
    (scoreMeasureIntegral : (ℝ -> ℝ) -> ℝ)
    (KDerivative cdfLeft perturbation : ℝ -> ℝ) :
    vaart1998_lStatisticSmoothKDerivative
        scoreMeasureIntegral KDerivative cdfLeft perturbation =
      - scoreMeasureIntegral
          (fun y => KDerivative (cdfLeft y) * perturbation y) :=
  rfl

theorem vaart1998_winsorizedMeanDecomposition_eq_generated
    (alpha : ℝ) (middleIntegral : (ℝ -> ℝ) -> ℝ)
    (quantile : ℝ -> ℝ) :
    vaart1998_winsorizedMeanDecomposition
        alpha middleIntegral quantile =
      vaart1998_winsorizedMeanGeneratedFunctional
        alpha middleIntegral quantile := by
  unfold vaart1998_winsorizedMeanDecomposition
    vaart1998_winsorizedMeanContinuousPart
    vaart1998_winsorizedMeanDiscretePart
    vaart1998_winsorizedMeanGeneratedFunctional
  ring

theorem vaart1998_locationFamilyDensity_apply
    (baseDensity : ℝ -> ℝ) (theta x : ℝ) :
    vaart1998_locationFamilyDensity baseDensity theta x =
      baseDensity (x - theta) :=
  rfl

theorem vaart1998_locationEfficientLinearTerm_apply
    {Ω : Type*} (observation : ℕ -> ℕ -> Ω -> ℝ)
    (fisherInformation : ℝ) (logDensityDerivative : ℝ -> ℝ)
    (theta : ℝ) (n : ℕ) (ω : Ω) :
    vaart1998_locationEfficientLinearTerm
        observation fisherInformation logDensityDerivative theta n ω =
      - (√(n : ℝ))⁻¹ *
        ∑ i ∈ Finset.Icc 1 n,
          fisherInformation⁻¹ *
            logDensityDerivative (observation n i ω - theta) :=
  rfl

theorem vaart1998_locationEfficientGeneratingKDerivative_apply
    (fisherInformation : ℝ)
    (logDensityDerivativeDerivative quantile : ℝ -> ℝ)
    (u : ℝ) :
    vaart1998_locationEfficientGeneratingKDerivative
        fisherInformation logDensityDerivativeDerivative quantile u =
      - fisherInformation⁻¹ * logDensityDerivativeDerivative (quantile u) :=
  rfl

/-- Source package for Chapter 22.1 and Examples 22.1-22.2. -/
structure Vaart1998Chapter22OpeningSource
    {Ω : Type*} where
  orderStatistic : ℕ -> ℕ -> Ω -> ℝ
  coefficient : ℕ -> ℕ -> ℝ
  score : ℝ -> ℝ
  trimCount : ℕ -> ℕ
  lowerQuartileIndex : ℕ -> ℕ
  upperQuartileIndex : ℕ -> ℕ
  lStatistic : ℕ -> Ω -> ℝ
  sampleMean : ℕ -> Ω -> ℝ
  trimmedMean : ℕ -> Ω -> ℝ
  winsorizedMean : ℕ -> Ω -> ℝ
  interquartileRange : ℕ -> Ω -> ℝ
  sampleRange : ℕ -> Ω -> ℝ
  lStatistic_eq :
    ∀ n ω,
      lStatistic n ω =
        vaart1998_lStatistic orderStatistic coefficient score n ω
  sampleMean_eq :
    ∀ n ω,
      sampleMean n ω =
        vaart1998_orderStatisticSampleMean orderStatistic n ω
  trimmedMean_eq :
    ∀ n ω,
      trimmedMean n ω =
        vaart1998_trimmedMean orderStatistic trimCount n ω
  winsorizedMean_eq :
    ∀ n ω,
      winsorizedMean n ω =
        vaart1998_winsorizedMean orderStatistic trimCount n ω
  interquartileRange_eq :
    ∀ n ω,
      interquartileRange n ω =
        vaart1998_interquantileRange
          orderStatistic lowerQuartileIndex upperQuartileIndex n ω
  sampleRange_eq :
    ∀ n ω,
      sampleRange n ω =
        vaart1998_sampleRange orderStatistic n ω
  monotone_score_reduction_statement : Prop
  monotone_score_reduction : monotone_score_reduction_statement
  bounded_variation_score_split_statement : Prop
  bounded_variation_score_split : bounded_variation_score_split_statement
  projection_method_route_statement : Prop
  projection_method_route : projection_method_route_statement
  delta_method_route_statement : Prop
  delta_method_route : delta_method_route_statement
  trimmed_winsorized_robust_location_statement : Prop
  trimmed_winsorized_robust_location :
    trimmed_winsorized_robust_location_statement
  range_not_normal_scope_statement : Prop
  range_not_normal_scope : range_not_normal_scope_statement

/-- Source package for Theorem 22.3, the projection-method asymptotic-normality
route for generated L-statistic coefficients. -/
structure Vaart1998Theorem22_3GeneratedLStatisticProjectionSource
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    (P : ℕ -> Measure Ω) [∀ n : ℕ, IsProbabilityMeasure (P n)]
    (LimitLaw : Measure ΩLimit) [IsProbabilityMeasure LimitLaw] where
  theorem11_2 :
    Vaart1998Theorem11_2ProjectionAsymptoticEquivalenceSource P LimitLaw
  cdf : ℝ -> ℝ
  phi : ℝ -> ℝ
  coefficient : ℕ -> ℕ -> ℝ
  score : ℝ -> ℝ
  orderStatistic : ℕ -> ℕ -> Ω -> ℝ
  empiricalCdf : ℕ -> ℝ -> ℝ
  binomialMass : ℕ -> ℝ -> ℕ -> ℝ
  integralFunctional : (ℝ -> ℝ) -> ℝ
  doubleIntegral : (ℝ -> ℝ -> ℝ) -> ℝ
  orderIndicatorCovariance : ℕ -> ℕ -> ℕ -> ℝ -> ℝ -> ℝ
  lStatistic : ℕ -> Ω -> ℝ
  statisticCenter : ℕ -> ℝ
  hajekProjection : ℕ -> Ω -> ℝ
  projectionCenter : ℕ -> ℝ
  centeredScaledLStatistic : ℕ -> Ω -> ℝ
  centeredScaledProjection : ℕ -> Ω -> ℝ
  projectionResidual : ℕ -> Ω -> ℝ
  projectionWeight : ℕ -> ℝ -> ℝ
  limitWeight : ℝ -> ℝ
  asymptoticVariance : ℝ
  projectionVariance : ℕ -> ℝ
  statisticVariance : ℕ -> ℝ
  covarianceKernel : ℕ -> ℝ -> ℝ -> ℝ
  limitStatistic : ΩLimit -> ℝ
  generated_coefficient_eq :
    ∀ n i,
      coefficient n i =
        vaart1998_lStatisticGeneratedCoefficient phi n i
  lStatistic_eq :
    ∀ n ω,
      lStatistic n ω =
        vaart1998_lStatistic orderStatistic coefficient score n ω
  centeredScaledLStatistic_eq :
    centeredScaledLStatistic =
      vaart1998_sqrtInvNCenteredStatisticSequence
        lStatistic statisticCenter
  centeredScaledProjection_eq :
    centeredScaledProjection =
      vaart1998_sqrtInvNCenteredStatisticSequence
        hajekProjection projectionCenter
  projectionResidual_display :
    ∀ n ω,
      projectionResidual n ω =
        centeredScaledLStatistic n ω - centeredScaledProjection n ω
  projectionWeight_eq :
    ∀ n y,
      projectionWeight n y =
        vaart1998_lStatisticProjectionWeight
          coefficient binomialMass cdf n y
  generatedProjectionWeight_eq :
    ∀ n y,
      projectionWeight n y =
        vaart1998_lStatisticGeneratedProjectionWeight
          phi binomialMass cdf n y
  limitWeight_eq :
    ∀ y,
      limitWeight y =
        vaart1998_lStatisticLimitProjectionWeight phi cdf y
  centeredHajekProjection_eq :
    ∀ n,
      projectionCenter n =
        vaart1998_lStatisticCenteredHajekProjection
          integralFunctional empiricalCdf cdf projectionWeight n
  asymptoticVariance_eq :
    asymptoticVariance =
      vaart1998_lStatisticAsymptoticVariance doubleIntegral phi cdf
  projectionVariance_eq :
    ∀ n,
      projectionVariance n =
        vaart1998_lStatisticProjectionVariance
          doubleIntegral cdf projectionWeight n
  covarianceKernel_eq :
    ∀ n x y,
      covarianceKernel n x y =
        vaart1998_lStatisticCovarianceKernel
          coefficient orderIndicatorCovariance n x y
  standardizedStatistic_eq :
    theorem11_2.standardizedStatistic = centeredScaledLStatistic
  standardizedProjection_eq :
    theorem11_2.standardizedProjection = centeredScaledProjection
  standardizedResidual_eq :
    theorem11_2.standardizedDifference = projectionResidual
  limitStatistic_eq :
    theorem11_2.limitStatistic = limitStatistic
  square_integrable_observation_statement : Prop
  square_integrable_observation : square_integrable_observation_statement
  phi_bounded_statement : Prop
  phi_bounded : phi_bounded_statement
  phi_continuous_ae_cdf_statement : Prop
  phi_continuous_ae_cdf : phi_continuous_ae_cdf_statement
  projection_weight_tendsto_statement : Prop
  projection_weight_tendsto : projection_weight_tendsto_statement
  projection_variance_tendsto :
    Tendsto projectionVariance atTop (𝓝 asymptoticVariance)
  statistic_variance_tendsto :
    Tendsto statisticVariance atTop (𝓝 asymptoticVariance)
  order_indicator_covariance_nonnegative_statement : Prop
  order_indicator_covariance_nonnegative :
    order_indicator_covariance_nonnegative_statement
  hoeffding_tail_bound_statement : Prop
  hoeffding_tail_bound : hoeffding_tail_bound_statement
  covariance_kernel_pointwise_tendsto_statement : Prop
  covariance_kernel_pointwise_tendsto :
    covariance_kernel_pointwise_tendsto_statement
  dominated_convergence_variance_statement : Prop
  dominated_convergence_variance : dominated_convergence_variance_statement
  projection_clt :
    TendstoInDistribution centeredScaledProjection atTop
      limitStatistic P LimitLaw
  normalLimitWithVariance : ℝ -> Prop
  normalLimit_display : normalLimitWithVariance asymptoticVariance
  delta_method_quantile_route_statement : Prop
  delta_method_quantile_route : delta_method_quantile_route_statement

/-- Source package for equation (22.4): generated-measure L-statistics with
coefficients `K((i-1)/n, i/n]`. -/
structure Vaart1998Equation22_4GeneratedMeasureLStatisticSource
    {Ω : Type*} where
  orderStatistic : ℕ -> ℕ -> Ω -> ℝ
  score : ℝ -> ℝ
  KIntervalMass : ℝ -> ℝ -> ℝ
  signedMeasureIntegral : (ℝ -> ℝ) -> ℝ
  quantile : ℝ -> ℝ
  empiricalQuantile : ℕ -> Ω -> ℝ -> ℝ
  generatedCoefficient : ℕ -> ℕ -> ℝ
  generatedLStatistic : ℕ -> Ω -> ℝ
  quantileFunctional : ℝ
  empiricalQuantileFunctional : ℕ -> Ω -> ℝ
  generatedCoefficient_eq :
    ∀ n i,
      generatedCoefficient n i =
        vaart1998_lStatisticGeneratedMeasureCoefficient KIntervalMass n i
  generatedLStatistic_eq :
    ∀ n ω,
      generatedLStatistic n ω =
        vaart1998_lStatisticGeneratedMeasureDisplay
          orderStatistic KIntervalMass score n ω
  quantileFunctional_eq :
    quantileFunctional =
      vaart1998_lStatisticQuantileFunctional
        signedMeasureIntegral score quantile
  empiricalQuantileFunctional_eq :
    ∀ n ω,
      empiricalQuantileFunctional n ω =
        vaart1998_lStatisticQuantileFunctional
          signedMeasureIntegral score (empiricalQuantile n ω)
  plug_in_equals_generated_lStatistic_statement : Prop
  plug_in_equals_generated_lStatistic :
    plug_in_equals_generated_lStatistic_statement
  generated_coefficients_generality_statement : Prop
  generated_coefficients_generality : generated_coefficients_generality_statement
  von_mises_route_statement : Prop
  von_mises_route : von_mises_route_statement

/-- Source package for Example 22.5: trimmed, Winsorized, and interquartile
examples generated by measures on the quantile scale. -/
structure Vaart1998Example22_5GeneratedExamplesSource
    {Ω : Type*} where
  orderStatistic : ℕ -> ℕ -> Ω -> ℝ
  alpha : ℝ
  ceilingAlphaN : ℕ -> ℕ
  quantile : ℝ -> ℝ
  middleIntegral : (ℝ -> ℝ) -> ℝ
  trimmedFunctional : ℝ
  trimmedOrderStatisticGenerated : ℕ -> Ω -> ℝ
  winsorizedFunctional : ℝ
  interquartileRangeFunctional : ℝ
  signedTwoPointFunctional : ℝ
  trimmedFunctional_eq :
    trimmedFunctional =
      vaart1998_trimmedMeanGeneratedFunctional
        alpha middleIntegral quantile
  trimmedOrderStatisticGenerated_eq :
    ∀ n ω,
      trimmedOrderStatisticGenerated n ω =
        vaart1998_trimmedMeanGeneratedOrderStatisticDisplay
          orderStatistic alpha ceilingAlphaN n ω
  winsorizedFunctional_eq :
    winsorizedFunctional =
      vaart1998_winsorizedMeanGeneratedFunctional
        alpha middleIntegral quantile
  interquartileRangeFunctional_eq :
    interquartileRangeFunctional =
      vaart1998_interquartileRangeGeneratedFunctional quantile
  signedTwoPointFunctional_eq :
    signedTwoPointFunctional =
      vaart1998_signedTwoPointQuantileFunctional
        (1 / 4) (3 / 4) (-1) 1 quantile
  trimmed_order_statistic_consistency_statement : Prop
  trimmed_order_statistic_consistency :
    trimmed_order_statistic_consistency_statement
  trimmed_difference_negligible_statement : Prop
  trimmed_difference_negligible : trimmed_difference_negligible_statement
  winsorized_difference_negligible_statement : Prop
  winsorized_difference_negligible :
    winsorized_difference_negligible_statement
  robust_l_statistics_statement : Prop
  robust_l_statistics : robust_l_statistics_statement

/-- Source package for the informal influence formulas (22.6), (22.7), and
(22.8), keeping the two different regularity routes explicit. -/
structure Vaart1998InfluenceFormula22_6Source where
  scoreDerivative : ℝ -> ℝ
  cdf : ℝ -> ℝ
  quantile : ℝ -> ℝ
  density : ℝ -> ℝ
  KDerivative : ℝ -> ℝ
  signedMeasureIntegral : (ℝ -> ℝ) -> ℝ
  pushforwardIntegral : (ℝ -> ℝ) -> ℝ
  scoreMeasureIntegral : (ℝ -> ℝ) -> ℝ
  positiveTailIntegral : (ℝ -> ℝ) -> ℝ
  nonpositiveIntegral : (ℝ -> ℝ) -> ℝ
  composedLeftTail : ℝ -> ℝ
  composedSurvival : ℝ -> ℝ
  influenceFunction22_6 : ℝ -> ℝ
  transformedInfluenceFunction22_6 : ℝ -> ℝ
  partialIntegrationFunctional : ℝ
  influenceFunction22_8 : ℝ -> ℝ
  influenceFunction22_6_eq :
    ∀ x,
      influenceFunction22_6 x =
        vaart1998_lStatisticInfluenceFunction22_6
          signedMeasureIntegral scoreDerivative quantile density x
  transformedInfluenceFunction22_6_eq :
    ∀ x,
      transformedInfluenceFunction22_6 x =
        vaart1998_lStatisticInfluenceFunction22_6Transformed
          pushforwardIntegral scoreDerivative cdf density x
  partialIntegrationFunctional_eq :
    partialIntegrationFunctional =
      vaart1998_lStatisticPartialIntegrationFunctional
        positiveTailIntegral nonpositiveIntegral
        composedLeftTail composedSurvival
  influenceFunction22_8_eq :
    ∀ x,
      influenceFunction22_8 x =
        vaart1998_lStatisticInfluenceFunction22_8
          scoreMeasureIntegral KDerivative cdf x
  example20_5_quantile_influence_statement : Prop
  example20_5_quantile_influence :
    example20_5_quantile_influence_statement
  quantile_transformation_statement : Prop
  quantile_transformation : quantile_transformation_statement
  regularity_for_22_6_statement : Prop
  regularity_for_22_6 : regularity_for_22_6_statement
  regularity_for_22_8_statement : Prop
  regularity_for_22_8 : regularity_for_22_8_statement
  nonoverlapping_routes_statement : Prop
  nonoverlapping_routes : nonoverlapping_routes_statement

/-- Source package for Lemma 22.9, the Hadamard differentiability of
`Q ↦ ∫ a(Q) dK` on `ell_infty(alpha,beta)`. -/
structure Vaart1998Lemma22_9QuantileFunctionalHadamardSource
    (QuantileFunc : Type*) [NormedAddCommGroup QuantileFunc]
    [NormedSpace ℝ QuantileFunc] where
  signedMeasureIntegral : (ℝ -> ℝ) -> ℝ
  score : ℝ -> ℝ
  scoreDerivative : ℝ -> ℝ
  quantileMap : QuantileFunc -> ℝ
  derivative : QuantileFunc →L[ℝ] ℝ
  domain : Set QuantileFunc
  tangentSet : Set QuantileFunc
  baseQ : QuantileFunc
  alpha : ℝ
  beta : ℝ
  quantileMap_display_statement : Prop
  quantileMap_display : quantileMap_display_statement
  derivative_display_statement : Prop
  derivative_display : derivative_display_statement
  support_subset_open_interval_statement : Prop
  support_subset_open_interval : support_subset_open_interval_statement
  score_continuously_differentiable_statement : Prop
  score_continuously_differentiable :
    score_continuously_differentiable_statement
  scoreDerivative_bounded_statement : Prop
  scoreDerivative_bounded : scoreDerivative_bounded_statement
  dominated_convergence_bound_statement : Prop
  dominated_convergence_bound : dominated_convergence_bound_statement
  hadamardDifferentiable :
    vaart1998_HadamardDifferentiableAtTangentially
      quantileMap domain tangentSet baseQ derivative

/-- Source package for Lemma 22.10: the smooth-generating-measure
Hadamard-differentiability route for
`F ↦ ∫ a(F^{-1}) dK`, with derivative
`H ↦ -∫ (K' ∘ F_-) H da`. -/
structure Vaart1998Lemma22_10SmoothGeneratingMeasureHadamardSource
    (DistFunc : Type*) [NormedAddCommGroup DistFunc]
    [NormedSpace ℝ DistFunc] where
  signedMeasureIntegral : (ℝ -> ℝ) -> ℝ
  scoreMeasureIntegral : (ℝ -> ℝ) -> ℝ
  variationIntegral : (ℝ -> ℝ) -> ℝ
  score : ℝ -> ℝ
  KDistribution : ℝ -> ℝ
  KDerivative : ℝ -> ℝ
  M : ℝ -> ℝ
  cdfLeft : ℝ -> ℝ
  quantileOfCdf : DistFunc -> ℝ -> ℝ
  processEval : DistFunc -> ℝ -> ℝ
  distributionFunctional : DistFunc -> ℝ
  derivative : DistFunc →L[ℝ] ℝ
  domain : Set DistFunc
  tangentSet : Set DistFunc
  baseF : DistFunc
  distributionFunctional_eq :
    ∀ F,
      distributionFunctional F =
        vaart1998_lStatisticDistributionFunctional
          signedMeasureIntegral score quantileOfCdf F
  derivative_eq :
    ∀ H,
      derivative H =
        vaart1998_lStatisticSmoothKDerivative
          scoreMeasureIntegral KDerivative cdfLeft (processEval H)
  score_zero : score 0 = 0
  score_boundedVariationOnBoundedIntervals_statement : Prop
  score_boundedVariationOnBoundedIntervals :
    score_boundedVariationOnBoundedIntervals_statement
  score_integrable_composed_measure_statement : Prop
  score_integrable_composed_measure :
    score_integrable_composed_measure_statement
  K_differentiable_ae_statement : Prop
  K_differentiable_ae : K_differentiable_ae_statement
  K_local_lipschitz_bound_statement : Prop
  K_local_lipschitz_bound : K_local_lipschitz_bound_statement
  M_integrable_statement : Prop
  M_integrable : M_integrable_statement
  partial_integration_rewrite_statement : Prop
  partial_integration_rewrite : partial_integration_rewrite_statement
  endpoint_constant_statement : Prop
  endpoint_constant : endpoint_constant_statement
  difference_rewrite_statement : Prop
  difference_rewrite : difference_rewrite_statement
  dominated_convergence_bound_statement : Prop
  dominated_convergence_bound : dominated_convergence_bound_statement
  hadamardDifferentiable :
    vaart1998_HadamardDifferentiableAtTangentially
      distributionFunctional domain tangentSet baseF derivative

/-- Source package for Example 22.11, the trimmed mean via Lemma 22.10. -/
structure Vaart1998Example22_11TrimmedMeanSource
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    (P : ℕ -> Measure Ω) [∀ n : ℕ, IsProbabilityMeasure (P n)]
    (LimitLaw : Measure ΩLimit) [IsProbabilityMeasure LimitLaw]
    (DistFunc : Type*) [NormedAddCommGroup DistFunc]
    [NormedSpace ℝ DistFunc] where
  lemma22_10 :
    Vaart1998Lemma22_10SmoothGeneratingMeasureHadamardSource DistFunc
  theorem19_3 : Vaart1998Theorem19_3EmpiricalCDFDonskerSource
  alpha : ℝ
  cdf : ℝ -> ℝ
  intervalIntegral : (ℝ -> ℝ) -> ℝ
  doubleIntegral : (ℝ -> ℝ -> ℝ) -> ℝ
  empiricalCdf : ℕ -> Ω -> DistFunc
  trimmedFunctional : DistFunc -> ℝ
  empiricalTrimmedMean : ℕ -> Ω -> ℝ
  centeredScaledTrimmedMean : ℕ -> Ω -> ℝ
  linearTerm : ℕ -> Ω -> ℝ
  limitingNormalStatistic : ΩLimit -> ℝ
  influenceFunction : ℝ -> ℝ
  asymptoticVariance : ℝ
  trimmedFunctional_eq :
    ∀ F,
      trimmedFunctional F =
        vaart1998_trimmedMeanGeneratedFunctional
          alpha intervalIntegral (lemma22_10.quantileOfCdf F)
  empiricalTrimmedMean_eq :
    ∀ n ω, empiricalTrimmedMean n ω = trimmedFunctional (empiricalCdf n ω)
  centeredScaledTrimmedMean_eq :
    centeredScaledTrimmedMean =
      vaart1998_sqrtInvNCenteredStatisticSequence
        empiricalTrimmedMean (fun _ => trimmedFunctional lemma22_10.baseF)
  influenceFunction_eq :
    ∀ x,
      influenceFunction x =
        vaart1998_trimmedMeanInfluenceFunction22_11
          intervalIntegral cdf x
  asymptoticVariance_eq :
    asymptoticVariance =
      vaart1998_trimmedMeanAsymptoticVariance22_11 doubleIntegral cdf
  uniform_K_lipschitz_statement : Prop
  uniform_K_lipschitz : uniform_K_lipschitz_statement
  K_nondifferentiable_only_endpoints_statement : Prop
  K_nondifferentiable_only_endpoints :
    K_nondifferentiable_only_endpoints_statement
  no_flat_at_alpha_statement : Prop
  no_flat_at_alpha : no_flat_at_alpha_statement
  no_flat_at_one_sub_alpha_statement : Prop
  no_flat_at_one_sub_alpha : no_flat_at_one_sub_alpha_statement
  asymptoticallyLinear :
    vaart1998_asymptoticallyLinearWithInfluence
      P centeredScaledTrimmedMean linearTerm
  asymptoticNormal :
    TendstoInDistribution centeredScaledTrimmedMean atTop
      limitingNormalStatistic P LimitLaw

/-- Source package for Example 22.12, the Winsorized mean split into the
Lemma 22.9 discrete quantile part and the Lemma 22.10 smooth middle part. -/
structure Vaart1998Example22_12WinsorizedMeanSource
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    (P : ℕ -> Measure Ω) [∀ n : ℕ, IsProbabilityMeasure (P n)]
    (LimitLaw : Measure ΩLimit) [IsProbabilityMeasure LimitLaw]
    (QuantileFunc DistFunc : Type*) [NormedAddCommGroup QuantileFunc]
    [NormedSpace ℝ QuantileFunc] [NormedAddCommGroup DistFunc]
    [NormedSpace ℝ DistFunc] where
  lemma22_9_discrete :
    Vaart1998Lemma22_9QuantileFunctionalHadamardSource QuantileFunc
  lemma22_10_continuous :
    Vaart1998Lemma22_10SmoothGeneratingMeasureHadamardSource DistFunc
  theorem19_3 : Vaart1998Theorem19_3EmpiricalCDFDonskerSource
  alpha : ℝ
  quantile : ℝ -> ℝ
  middleIntegral : (ℝ -> ℝ) -> ℝ
  winsorizedFunctional : ℝ
  discretePart : ℝ
  continuousPart : ℝ
  centeredScaledWinsorizedMean : ℕ -> Ω -> ℝ
  linearTerm : ℕ -> Ω -> ℝ
  limitingNormalStatistic : ΩLimit -> ℝ
  discretePart_eq :
    discretePart =
      vaart1998_winsorizedMeanDiscretePart alpha quantile
  continuousPart_eq :
    continuousPart =
      vaart1998_winsorizedMeanContinuousPart middleIntegral quantile
  winsorizedFunctional_eq :
    winsorizedFunctional =
      vaart1998_winsorizedMeanGeneratedFunctional
        alpha middleIntegral quantile
  decomposition_eq :
    winsorizedFunctional = continuousPart + discretePart
  positive_derivative_lower_quantile_statement : Prop
  positive_derivative_lower_quantile :
    positive_derivative_lower_quantile_statement
  positive_derivative_upper_quantile_statement : Prop
  positive_derivative_upper_quantile :
    positive_derivative_upper_quantile_statement
  lemma21_3_endpoint_route_statement : Prop
  lemma21_3_endpoint_route : lemma21_3_endpoint_route_statement
  discrete_asymptotically_linear_statement : Prop
  discrete_asymptotically_linear :
    discrete_asymptotically_linear_statement
  continuous_asymptotically_linear_statement : Prop
  continuous_asymptotically_linear :
    continuous_asymptotically_linear_statement
  asymptoticallyLinear :
    vaart1998_asymptoticallyLinearWithInfluence
      P centeredScaledWinsorizedMean linearTerm
  asymptoticNormal :
    TendstoInDistribution centeredScaledWinsorizedMean atTop
      limitingNormalStatistic P LimitLaw

/-- Source package for Section 22.4, L-estimators for location.  It records
the Chapter 8 efficient location expansion and the matching condition which
chooses `K` and `a` so that the L-statistic has the efficient influence
function. -/
structure Vaart1998Section22_4LocationLEstimatorSource
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    (P : ℕ -> Measure Ω) [∀ n : ℕ, IsProbabilityMeasure (P n)]
    (LimitLaw : Measure ΩLimit) [IsProbabilityMeasure LimitLaw] where
  baseDensity : ℝ -> ℝ
  cdf : ℝ -> ℝ
  quantile : ℝ -> ℝ
  KDerivative : ℝ -> ℝ
  transform : ℝ -> ℝ
  transformDerivative : ℝ -> ℝ
  logDensityDerivative : ℝ -> ℝ
  logDensityDerivativeDerivative : ℝ -> ℝ
  fisherInformation : ℝ
  theta : ℝ
  observation : ℕ -> ℕ -> Ω -> ℝ
  estimator : ℕ -> Ω -> ℝ
  centeredScaledEstimator : ℕ -> Ω -> ℝ
  efficientLinearTerm : ℕ -> Ω -> ℝ
  efficientInfluence : ℝ -> ℝ
  generatedKDerivative : ℝ -> ℝ
  limitingNormalStatistic : ΩLimit -> ℝ
  locationFamilyDensity_eq :
    ∀ theta x,
      vaart1998_locationFamilyDensity baseDensity theta x =
        baseDensity (x - theta)
  centeredScaledEstimator_eq :
    centeredScaledEstimator =
      vaart1998_locationCenteredScaledEstimator estimator theta
  efficientLinearTerm_eq :
    ∀ n ω,
      efficientLinearTerm n ω =
        vaart1998_locationEfficientLinearTerm
          observation fisherInformation logDensityDerivative theta n ω
  efficientInfluence_eq :
    ∀ x,
      efficientInfluence x =
        vaart1998_locationEfficientInfluence
          fisherInformation logDensityDerivative theta x
  matchingEquation :
    ∀ x,
      vaart1998_locationLEstimatorMatchingLeft
          KDerivative cdf transformDerivative theta x =
        vaart1998_locationLEstimatorMatchingRight
          fisherInformation logDensityDerivativeDerivative theta x
  identity_transform_statement : Prop
  identity_transform : identity_transform_statement
  generatedKDerivative_eq :
    ∀ u,
      generatedKDerivative u =
        vaart1998_locationEfficientGeneratingKDerivative
          fisherInformation logDensityDerivativeDerivative quantile u
  finite_fisher_information_statement : Prop
  finite_fisher_information : finite_fisher_information_statement
  chapter8_optimality_statement : Prop
  chapter8_optimality : chapter8_optimality_statement
  lStatistic_influence_matches_optimal_statement : Prop
  lStatistic_influence_matches_optimal :
    lStatistic_influence_matches_optimal_statement
  lStatistic_class_large_enough_statement : Prop
  lStatistic_class_large_enough : lStatistic_class_large_enough_statement
  asymptoticallyLinearEfficient :
    vaart1998_asymptoticallyLinearWithInfluence
      P centeredScaledEstimator efficientLinearTerm
  asymptoticNormal :
    TendstoInDistribution centeredScaledEstimator atTop
      limitingNormalStatistic P LimitLaw

namespace Vaart1998Chapter22OpeningSource

theorem lStatistic_display
    {Ω : Type*} (S : Vaart1998Chapter22OpeningSource (Ω := Ω))
    (n : ℕ) (ω : Ω) :
    S.lStatistic n ω =
      vaart1998_lStatistic S.orderStatistic S.coefficient S.score n ω :=
  S.lStatistic_eq n ω

theorem trimmedMean_display
    {Ω : Type*} (S : Vaart1998Chapter22OpeningSource (Ω := Ω))
    (n : ℕ) (ω : Ω) :
    S.trimmedMean n ω =
      vaart1998_trimmedMean S.orderStatistic S.trimCount n ω :=
  S.trimmedMean_eq n ω

theorem winsorizedMean_display
    {Ω : Type*} (S : Vaart1998Chapter22OpeningSource (Ω := Ω))
    (n : ℕ) (ω : Ω) :
    S.winsorizedMean n ω =
      vaart1998_winsorizedMean S.orderStatistic S.trimCount n ω :=
  S.winsorizedMean_eq n ω

theorem interquartileRange_display
    {Ω : Type*} (S : Vaart1998Chapter22OpeningSource (Ω := Ω))
    (n : ℕ) (ω : Ω) :
    S.interquartileRange n ω =
      vaart1998_interquantileRange
        S.orderStatistic S.lowerQuartileIndex S.upperQuartileIndex n ω :=
  S.interquartileRange_eq n ω

theorem sampleRange_display
    {Ω : Type*} (S : Vaart1998Chapter22OpeningSource (Ω := Ω))
    (n : ℕ) (ω : Ω) :
    S.sampleRange n ω =
      vaart1998_sampleRange S.orderStatistic n ω :=
  S.sampleRange_eq n ω

theorem projection_method_route_source
    {Ω : Type*} (S : Vaart1998Chapter22OpeningSource (Ω := Ω)) :
    S.projection_method_route_statement :=
  S.projection_method_route

theorem delta_method_route_source
    {Ω : Type*} (S : Vaart1998Chapter22OpeningSource (Ω := Ω)) :
    S.delta_method_route_statement :=
  S.delta_method_route

end Vaart1998Chapter22OpeningSource

namespace Vaart1998Theorem22_3GeneratedLStatisticProjectionSource

theorem generated_coefficient_display
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Theorem22_3GeneratedLStatisticProjectionSource
      P LimitLaw)
    (n i : ℕ) :
    S.coefficient n i =
      vaart1998_lStatisticGeneratedCoefficient S.phi n i :=
  S.generated_coefficient_eq n i

theorem lStatistic_display
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Theorem22_3GeneratedLStatisticProjectionSource
      P LimitLaw)
    (n : ℕ) (ω : Ω) :
    S.lStatistic n ω =
      vaart1998_lStatistic
        S.orderStatistic S.coefficient S.score n ω :=
  S.lStatistic_eq n ω

theorem projection_weight_display
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Theorem22_3GeneratedLStatisticProjectionSource
      P LimitLaw)
    (n : ℕ) (y : ℝ) :
    S.projectionWeight n y =
      vaart1998_lStatisticProjectionWeight
        S.coefficient S.binomialMass S.cdf n y :=
  S.projectionWeight_eq n y

theorem generated_projection_weight_display
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Theorem22_3GeneratedLStatisticProjectionSource
      P LimitLaw)
    (n : ℕ) (y : ℝ) :
    S.projectionWeight n y =
      vaart1998_lStatisticGeneratedProjectionWeight
        S.phi S.binomialMass S.cdf n y :=
  S.generatedProjectionWeight_eq n y

theorem asymptotic_variance_display
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Theorem22_3GeneratedLStatisticProjectionSource
      P LimitLaw) :
    S.asymptoticVariance =
      vaart1998_lStatisticAsymptoticVariance
        S.doubleIntegral S.phi S.cdf :=
  S.asymptoticVariance_eq

theorem covariance_kernel_display
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Theorem22_3GeneratedLStatisticProjectionSource
      P LimitLaw)
    (n : ℕ) (x y : ℝ) :
    S.covarianceKernel n x y =
      vaart1998_lStatisticCovarianceKernel
        S.coefficient S.orderIndicatorCovariance n x y :=
  S.covarianceKernel_eq n x y

theorem projection_residual_oP
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Theorem22_3GeneratedLStatisticProjectionSource
      P LimitLaw) :
    Vaart1998MeasureSeqConvergesInProbabilityToZero P
      S.projectionResidual := by
  have h :=
    Vaart1998Theorem11_2ProjectionAsymptoticEquivalenceSource.standardizedDifference_oP
      S.theorem11_2
  simpa [S.standardizedResidual_eq] using h

theorem projection_convergence
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Theorem22_3GeneratedLStatisticProjectionSource
      P LimitLaw) :
    TendstoInDistribution S.centeredScaledProjection atTop
      S.limitStatistic P LimitLaw := by
  simpa [S.standardizedProjection_eq, S.limitStatistic_eq] using
    S.theorem11_2.projection_tendstoInDistribution

theorem lStatistic_convergence
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Theorem22_3GeneratedLStatisticProjectionSource
      P LimitLaw) :
    TendstoInDistribution S.centeredScaledLStatistic atTop
      S.limitStatistic P LimitLaw := by
  have h :=
    Vaart1998Theorem11_2ProjectionAsymptoticEquivalenceSource.statistic_tendstoInDistribution
      S.theorem11_2
  simpa [S.standardizedStatistic_eq, S.limitStatistic_eq] using h

theorem normal_limit_variance_source
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Theorem22_3GeneratedLStatisticProjectionSource
      P LimitLaw) :
    S.normalLimitWithVariance S.asymptoticVariance :=
  S.normalLimit_display

theorem delta_method_quantile_route_source
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Theorem22_3GeneratedLStatisticProjectionSource
      P LimitLaw) :
    S.delta_method_quantile_route_statement :=
  S.delta_method_quantile_route

end Vaart1998Theorem22_3GeneratedLStatisticProjectionSource

namespace Vaart1998Equation22_4GeneratedMeasureLStatisticSource

theorem generated_coefficient_display
    {Ω : Type*}
    (S : Vaart1998Equation22_4GeneratedMeasureLStatisticSource (Ω := Ω))
    (n i : ℕ) :
    S.generatedCoefficient n i =
      vaart1998_lStatisticGeneratedMeasureCoefficient
        S.KIntervalMass n i :=
  S.generatedCoefficient_eq n i

theorem generated_lStatistic_display
    {Ω : Type*}
    (S : Vaart1998Equation22_4GeneratedMeasureLStatisticSource (Ω := Ω))
    (n : ℕ) (ω : Ω) :
    S.generatedLStatistic n ω =
      vaart1998_lStatisticGeneratedMeasureDisplay
        S.orderStatistic S.KIntervalMass S.score n ω :=
  S.generatedLStatistic_eq n ω

theorem quantile_functional_display
    {Ω : Type*}
    (S : Vaart1998Equation22_4GeneratedMeasureLStatisticSource (Ω := Ω)) :
    S.quantileFunctional =
      vaart1998_lStatisticQuantileFunctional
        S.signedMeasureIntegral S.score S.quantile :=
  S.quantileFunctional_eq

theorem empirical_quantile_functional_display
    {Ω : Type*}
    (S : Vaart1998Equation22_4GeneratedMeasureLStatisticSource (Ω := Ω))
    (n : ℕ) (ω : Ω) :
    S.empiricalQuantileFunctional n ω =
      vaart1998_lStatisticQuantileFunctional
        S.signedMeasureIntegral S.score (S.empiricalQuantile n ω) :=
  S.empiricalQuantileFunctional_eq n ω

theorem von_mises_route_source
    {Ω : Type*}
    (S : Vaart1998Equation22_4GeneratedMeasureLStatisticSource (Ω := Ω)) :
    S.von_mises_route_statement :=
  S.von_mises_route

end Vaart1998Equation22_4GeneratedMeasureLStatisticSource

namespace Vaart1998Example22_5GeneratedExamplesSource

theorem trimmed_functional_display
    {Ω : Type*}
    (S : Vaart1998Example22_5GeneratedExamplesSource (Ω := Ω)) :
    S.trimmedFunctional =
      vaart1998_trimmedMeanGeneratedFunctional
        S.alpha S.middleIntegral S.quantile :=
  S.trimmedFunctional_eq

theorem trimmed_order_statistic_generated_display
    {Ω : Type*}
    (S : Vaart1998Example22_5GeneratedExamplesSource (Ω := Ω))
    (n : ℕ) (ω : Ω) :
    S.trimmedOrderStatisticGenerated n ω =
      vaart1998_trimmedMeanGeneratedOrderStatisticDisplay
        S.orderStatistic S.alpha S.ceilingAlphaN n ω :=
  S.trimmedOrderStatisticGenerated_eq n ω

theorem winsorized_functional_display
    {Ω : Type*}
    (S : Vaart1998Example22_5GeneratedExamplesSource (Ω := Ω)) :
    S.winsorizedFunctional =
      vaart1998_winsorizedMeanGeneratedFunctional
        S.alpha S.middleIntegral S.quantile :=
  S.winsorizedFunctional_eq

theorem interquartile_range_functional_display
    {Ω : Type*}
    (S : Vaart1998Example22_5GeneratedExamplesSource (Ω := Ω)) :
    S.interquartileRangeFunctional =
      vaart1998_interquartileRangeGeneratedFunctional S.quantile :=
  S.interquartileRangeFunctional_eq

theorem trimmed_difference_negligible_source
    {Ω : Type*}
    (S : Vaart1998Example22_5GeneratedExamplesSource (Ω := Ω)) :
    S.trimmed_difference_negligible_statement :=
  S.trimmed_difference_negligible

theorem winsorized_difference_negligible_source
    {Ω : Type*}
    (S : Vaart1998Example22_5GeneratedExamplesSource (Ω := Ω)) :
    S.winsorized_difference_negligible_statement :=
  S.winsorized_difference_negligible

end Vaart1998Example22_5GeneratedExamplesSource

namespace Vaart1998InfluenceFormula22_6Source

theorem influence22_6_display
    (S : Vaart1998InfluenceFormula22_6Source) (x : ℝ) :
    S.influenceFunction22_6 x =
      vaart1998_lStatisticInfluenceFunction22_6
        S.signedMeasureIntegral S.scoreDerivative S.quantile S.density x :=
  S.influenceFunction22_6_eq x

theorem transformed_influence22_6_display
    (S : Vaart1998InfluenceFormula22_6Source) (x : ℝ) :
    S.transformedInfluenceFunction22_6 x =
      vaart1998_lStatisticInfluenceFunction22_6Transformed
        S.pushforwardIntegral S.scoreDerivative S.cdf S.density x :=
  S.transformedInfluenceFunction22_6_eq x

theorem partial_integration_display
    (S : Vaart1998InfluenceFormula22_6Source) :
    S.partialIntegrationFunctional =
      vaart1998_lStatisticPartialIntegrationFunctional
        S.positiveTailIntegral S.nonpositiveIntegral
        S.composedLeftTail S.composedSurvival :=
  S.partialIntegrationFunctional_eq

theorem influence22_8_display
    (S : Vaart1998InfluenceFormula22_6Source) (x : ℝ) :
    S.influenceFunction22_8 x =
      vaart1998_lStatisticInfluenceFunction22_8
        S.scoreMeasureIntegral S.KDerivative S.cdf x :=
  S.influenceFunction22_8_eq x

theorem quantile_transformation_source
    (S : Vaart1998InfluenceFormula22_6Source) :
    S.quantile_transformation_statement :=
  S.quantile_transformation

theorem nonoverlapping_routes_source
    (S : Vaart1998InfluenceFormula22_6Source) :
    S.nonoverlapping_routes_statement :=
  S.nonoverlapping_routes

end Vaart1998InfluenceFormula22_6Source

namespace Vaart1998Lemma22_9QuantileFunctionalHadamardSource

theorem hadamard_differentiable
    {QuantileFunc : Type*} [NormedAddCommGroup QuantileFunc]
    [NormedSpace ℝ QuantileFunc]
    (S : Vaart1998Lemma22_9QuantileFunctionalHadamardSource
      QuantileFunc) :
    vaart1998_HadamardDifferentiableAtTangentially
      S.quantileMap S.domain S.tangentSet S.baseQ S.derivative :=
  S.hadamardDifferentiable

theorem derivative_display_source
    {QuantileFunc : Type*} [NormedAddCommGroup QuantileFunc]
    [NormedSpace ℝ QuantileFunc]
    (S : Vaart1998Lemma22_9QuantileFunctionalHadamardSource
      QuantileFunc) :
    S.derivative_display_statement :=
  S.derivative_display

theorem dominated_convergence_bound_source
    {QuantileFunc : Type*} [NormedAddCommGroup QuantileFunc]
    [NormedSpace ℝ QuantileFunc]
    (S : Vaart1998Lemma22_9QuantileFunctionalHadamardSource
      QuantileFunc) :
    S.dominated_convergence_bound_statement :=
  S.dominated_convergence_bound

end Vaart1998Lemma22_9QuantileFunctionalHadamardSource

namespace Vaart1998Lemma22_10SmoothGeneratingMeasureHadamardSource

theorem distribution_functional_display
    {DistFunc : Type*} [NormedAddCommGroup DistFunc]
    [NormedSpace ℝ DistFunc]
    (S : Vaart1998Lemma22_10SmoothGeneratingMeasureHadamardSource
      DistFunc)
    (F : DistFunc) :
    S.distributionFunctional F =
      vaart1998_lStatisticDistributionFunctional
        S.signedMeasureIntegral S.score S.quantileOfCdf F :=
  S.distributionFunctional_eq F

theorem derivative_display
    {DistFunc : Type*} [NormedAddCommGroup DistFunc]
    [NormedSpace ℝ DistFunc]
    (S : Vaart1998Lemma22_10SmoothGeneratingMeasureHadamardSource
      DistFunc)
    (H : DistFunc) :
    S.derivative H =
      vaart1998_lStatisticSmoothKDerivative
        S.scoreMeasureIntegral S.KDerivative S.cdfLeft (S.processEval H) :=
  S.derivative_eq H

theorem hadamard_differentiable
    {DistFunc : Type*} [NormedAddCommGroup DistFunc]
    [NormedSpace ℝ DistFunc]
    (S : Vaart1998Lemma22_10SmoothGeneratingMeasureHadamardSource
      DistFunc) :
    vaart1998_HadamardDifferentiableAtTangentially
      S.distributionFunctional S.domain S.tangentSet S.baseF
      S.derivative :=
  S.hadamardDifferentiable

theorem dominated_convergence_bound_source
    {DistFunc : Type*} [NormedAddCommGroup DistFunc]
    [NormedSpace ℝ DistFunc]
    (S : Vaart1998Lemma22_10SmoothGeneratingMeasureHadamardSource
      DistFunc) :
    S.dominated_convergence_bound_statement :=
  S.dominated_convergence_bound

end Vaart1998Lemma22_10SmoothGeneratingMeasureHadamardSource

namespace Vaart1998Example22_11TrimmedMeanSource

theorem trimmed_functional_display
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    {DistFunc : Type*} [NormedAddCommGroup DistFunc]
    [NormedSpace ℝ DistFunc]
    (S : Vaart1998Example22_11TrimmedMeanSource
      P LimitLaw DistFunc)
    (F : DistFunc) :
    S.trimmedFunctional F =
      vaart1998_trimmedMeanGeneratedFunctional
        S.alpha S.intervalIntegral (S.lemma22_10.quantileOfCdf F) :=
  S.trimmedFunctional_eq F

theorem influence_function_display
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    {DistFunc : Type*} [NormedAddCommGroup DistFunc]
    [NormedSpace ℝ DistFunc]
    (S : Vaart1998Example22_11TrimmedMeanSource
      P LimitLaw DistFunc)
    (x : ℝ) :
    S.influenceFunction x =
      vaart1998_trimmedMeanInfluenceFunction22_11
        S.intervalIntegral S.cdf x :=
  S.influenceFunction_eq x

theorem asymptotic_variance_display
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    {DistFunc : Type*} [NormedAddCommGroup DistFunc]
    [NormedSpace ℝ DistFunc]
    (S : Vaart1998Example22_11TrimmedMeanSource
      P LimitLaw DistFunc) :
    S.asymptoticVariance =
      vaart1998_trimmedMeanAsymptoticVariance22_11
        S.doubleIntegral S.cdf :=
  S.asymptoticVariance_eq

theorem asymptotically_linear
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    {DistFunc : Type*} [NormedAddCommGroup DistFunc]
    [NormedSpace ℝ DistFunc]
    (S : Vaart1998Example22_11TrimmedMeanSource
      P LimitLaw DistFunc) :
    vaart1998_asymptoticallyLinearWithInfluence
      P S.centeredScaledTrimmedMean S.linearTerm :=
  S.asymptoticallyLinear

theorem asymptotic_normal
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    {DistFunc : Type*} [NormedAddCommGroup DistFunc]
    [NormedSpace ℝ DistFunc]
    (S : Vaart1998Example22_11TrimmedMeanSource
      P LimitLaw DistFunc) :
    TendstoInDistribution S.centeredScaledTrimmedMean atTop
      S.limitingNormalStatistic P LimitLaw :=
  S.asymptoticNormal

end Vaart1998Example22_11TrimmedMeanSource

namespace Vaart1998Example22_12WinsorizedMeanSource

theorem discrete_part_display
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    {QuantileFunc DistFunc : Type*} [NormedAddCommGroup QuantileFunc]
    [NormedSpace ℝ QuantileFunc] [NormedAddCommGroup DistFunc]
    [NormedSpace ℝ DistFunc]
    (S : Vaart1998Example22_12WinsorizedMeanSource
      P LimitLaw QuantileFunc DistFunc) :
    S.discretePart =
      vaart1998_winsorizedMeanDiscretePart S.alpha S.quantile :=
  S.discretePart_eq

theorem continuous_part_display
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    {QuantileFunc DistFunc : Type*} [NormedAddCommGroup QuantileFunc]
    [NormedSpace ℝ QuantileFunc] [NormedAddCommGroup DistFunc]
    [NormedSpace ℝ DistFunc]
    (S : Vaart1998Example22_12WinsorizedMeanSource
      P LimitLaw QuantileFunc DistFunc) :
    S.continuousPart =
      vaart1998_winsorizedMeanContinuousPart
        S.middleIntegral S.quantile :=
  S.continuousPart_eq

theorem winsorized_functional_display
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    {QuantileFunc DistFunc : Type*} [NormedAddCommGroup QuantileFunc]
    [NormedSpace ℝ QuantileFunc] [NormedAddCommGroup DistFunc]
    [NormedSpace ℝ DistFunc]
    (S : Vaart1998Example22_12WinsorizedMeanSource
      P LimitLaw QuantileFunc DistFunc) :
    S.winsorizedFunctional =
      vaart1998_winsorizedMeanGeneratedFunctional
        S.alpha S.middleIntegral S.quantile :=
  S.winsorizedFunctional_eq

theorem asymptotically_linear
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    {QuantileFunc DistFunc : Type*} [NormedAddCommGroup QuantileFunc]
    [NormedSpace ℝ QuantileFunc] [NormedAddCommGroup DistFunc]
    [NormedSpace ℝ DistFunc]
    (S : Vaart1998Example22_12WinsorizedMeanSource
      P LimitLaw QuantileFunc DistFunc) :
    vaart1998_asymptoticallyLinearWithInfluence
      P S.centeredScaledWinsorizedMean S.linearTerm :=
  S.asymptoticallyLinear

theorem asymptotic_normal
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    {QuantileFunc DistFunc : Type*} [NormedAddCommGroup QuantileFunc]
    [NormedSpace ℝ QuantileFunc] [NormedAddCommGroup DistFunc]
    [NormedSpace ℝ DistFunc]
    (S : Vaart1998Example22_12WinsorizedMeanSource
      P LimitLaw QuantileFunc DistFunc) :
    TendstoInDistribution S.centeredScaledWinsorizedMean atTop
      S.limitingNormalStatistic P LimitLaw :=
  S.asymptoticNormal

end Vaart1998Example22_12WinsorizedMeanSource

namespace Vaart1998Section22_4LocationLEstimatorSource

theorem centered_scaled_estimator_display
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Section22_4LocationLEstimatorSource P LimitLaw) :
    S.centeredScaledEstimator =
      vaart1998_locationCenteredScaledEstimator S.estimator S.theta :=
  S.centeredScaledEstimator_eq

theorem efficient_linear_term_display
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Section22_4LocationLEstimatorSource P LimitLaw)
    (n : ℕ) (ω : Ω) :
    S.efficientLinearTerm n ω =
      vaart1998_locationEfficientLinearTerm
        S.observation S.fisherInformation S.logDensityDerivative
        S.theta n ω :=
  S.efficientLinearTerm_eq n ω

theorem efficient_influence_display
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Section22_4LocationLEstimatorSource P LimitLaw)
    (x : ℝ) :
    S.efficientInfluence x =
      vaart1998_locationEfficientInfluence
        S.fisherInformation S.logDensityDerivative S.theta x :=
  S.efficientInfluence_eq x

theorem matching_equation_display
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Section22_4LocationLEstimatorSource P LimitLaw)
    (x : ℝ) :
    vaart1998_locationLEstimatorMatchingLeft
        S.KDerivative S.cdf S.transformDerivative S.theta x =
      vaart1998_locationLEstimatorMatchingRight
        S.fisherInformation S.logDensityDerivativeDerivative S.theta x :=
  S.matchingEquation x

theorem generated_K_derivative_display
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Section22_4LocationLEstimatorSource P LimitLaw)
    (u : ℝ) :
    S.generatedKDerivative u =
      vaart1998_locationEfficientGeneratingKDerivative
        S.fisherInformation S.logDensityDerivativeDerivative
        S.quantile u :=
  S.generatedKDerivative_eq u

theorem asymptotically_linear_efficient
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Section22_4LocationLEstimatorSource P LimitLaw) :
    vaart1998_asymptoticallyLinearWithInfluence
      P S.centeredScaledEstimator S.efficientLinearTerm :=
  S.asymptoticallyLinearEfficient

theorem asymptotic_normal
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Section22_4LocationLEstimatorSource P LimitLaw) :
    TendstoInDistribution S.centeredScaledEstimator atTop
      S.limitingNormalStatistic P LimitLaw :=
  S.asymptoticNormal

theorem lStatistic_class_large_enough_source
    {Ω ΩLimit : Type*} [MeasurableSpace Ω] [MeasurableSpace ΩLimit]
    {P : ℕ -> Measure Ω} [∀ n : ℕ, IsProbabilityMeasure (P n)]
    {LimitLaw : Measure ΩLimit} [IsProbabilityMeasure LimitLaw]
    (S : Vaart1998Section22_4LocationLEstimatorSource P LimitLaw) :
    S.lStatistic_class_large_enough_statement :=
  S.lStatistic_class_large_enough

end Vaart1998Section22_4LocationLEstimatorSource

end AsymptoticStatistics
end StatInference
