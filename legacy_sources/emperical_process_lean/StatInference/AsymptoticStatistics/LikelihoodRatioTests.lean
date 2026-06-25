import StatInference.AsymptoticStatistics.Contiguity
import StatInference.AsymptoticStatistics.EfficientTests

/-!
# van der Vaart 1998 Chapter 16 likelihood-ratio test interfaces

This module opens the Chapter 16 lane.  It records the likelihood-ratio
statistics, Taylor/LAN Gaussian-limit displays, chi-square distance source,
local-power source, Bartlett correction, and Bahadur-efficiency source used
by van der Vaart's likelihood-ratio test chapter.
-/

noncomputable section

namespace StatInference
namespace AsymptoticStatistics

open Filter MeasureTheory ProbabilityTheory
open scoped ENNReal ProbabilityTheory Topology

/--
The log-likelihood-ratio statistic for a simple alternative against a simple
null, using the Chapter 6 `llr` notation.
-/
noncomputable def vaart1998_simpleLogLikelihoodRatioStatistic
    {Omega : Type*} [MeasurableSpace Omega]
    (alternativeLaw nullLaw : Measure Omega) : Omega -> Real :=
  vaart1998_logLikelihoodRatio alternativeLaw nullLaw

/--
The simple log-likelihood-ratio statistic is the real logarithm of the
Radon-Nikodym likelihood ratio.
-/
theorem vaart1998_simpleLogLikelihoodRatioStatistic_eq_log_likelihoodRatio_toReal
    {Omega : Type*} [MeasurableSpace Omega]
    (alternativeLaw nullLaw : Measure Omega) :
    vaart1998_simpleLogLikelihoodRatioStatistic alternativeLaw nullLaw =
      fun omega =>
        Real.log
          ((vaart1998_likelihoodRatio alternativeLaw nullLaw omega).toReal) := by
  simpa [vaart1998_simpleLogLikelihoodRatioStatistic] using
    vaart1998_logLikelihoodRatio_eq_log_likelihoodRatio_toReal
      alternativeLaw nullLaw

/--
The simple log-likelihood-ratio statistic is measurable.
-/
theorem vaart1998_simpleLogLikelihoodRatioStatistic_measurable
    {Omega : Type*} [MeasurableSpace Omega]
    (alternativeLaw nullLaw : Measure Omega) :
    Measurable
      (vaart1998_simpleLogLikelihoodRatioStatistic alternativeLaw nullLaw) := by
  change Measurable (MeasureTheory.llr alternativeLaw nullLaw)
  exact MeasureTheory.measurable_llr alternativeLaw nullLaw

/--
The Chapter 16 likelihood-ratio statistic in log-supremum form:
`2 (sup log L_full - sup log L_null)`.
-/
def vaart1998_likelihoodRatioStatisticFromLogSup
    (fullLogLikelihoodSup nullLogLikelihoodSup : Real) : Real :=
  2 * (fullLogLikelihoodSup - nullLogLikelihoodSup)

/--
The equivalent likelihood-supremum display
`2 log (sup L_full / sup L_null)`.
-/
def vaart1998_likelihoodRatioStatisticFromLikelihoodSup
    (fullLikelihoodSup nullLikelihoodSup : Real) : Real :=
  2 * Real.log (fullLikelihoodSup / nullLikelihoodSup)

/--
The local LAN likelihood-ratio statistic written as the difference of two
suprema of a local log-likelihood-ratio process.
-/
def vaart1998_localLikelihoodRatioStatisticFromProcess
    {H : Type*} (logLikelihoodRatioProcess : H -> Real)
    (fullLocalSet nullLocalSet : Set H) : Real :=
  2 *
    (sSup (logLikelihoodRatioProcess '' fullLocalSet) -
      sSup (logLikelihoodRatioProcess '' nullLocalSet))

/--
Local parameter spaces `H_n = r_n (Theta - theta0)`, expressed by the
equivalent membership condition `theta0 + r_n^{-1} h in Theta`.
-/
def vaart1998_localParameterSet
    {E : Type*} [AddCommGroup E] [Module Real E]
    (rate : Real) (theta0 : E) (thetaSet : Set E) : Set E :=
  {h | theta0 + rate⁻¹ • h ∈ thetaSet}

/--
The Kuratowski-style set convergence described before Theorem 16.7: every
point of the limit is reached by a convergent sequence from the moving sets,
and every convergent sequence from the moving sets has its limit in the
limit set.
-/
def vaart1998_localSetConvergence
    {H : Type*} [TopologicalSpace H]
    (sets : Nat -> Set H) (limitSet : Set H) : Prop :=
  (∀ h ∈ limitSet,
      ∃ seq : Nat -> H,
        (∀ n, seq n ∈ sets n) ∧ Tendsto seq atTop (𝓝 h)) ∧
    (∀ seq : Nat -> H,
      (∀ n, seq n ∈ sets n) ->
        ∀ h, Tendsto seq atTop (𝓝 h) -> h ∈ limitSet)

/--
Section 16.1 source: the composite likelihood-ratio statistic is the
difference between unrestricted and null restricted log-likelihood suprema.
-/
structure Vaart1998Section16_1LikelihoodRatioStatisticSource where
  /-- Supremum of the full log likelihood. -/
  fullLogLikelihoodSup : Real
  /-- Supremum of the null-restricted log likelihood. -/
  nullLogLikelihoodSup : Real
  /-- Supremum of the full likelihood. -/
  fullLikelihoodSup : Real
  /-- Supremum of the null-restricted likelihood. -/
  nullLikelihoodSup : Real
  /-- The likelihood-ratio statistic. -/
  statistic : Real
  /-- Log-supremum display of the statistic. -/
  statistic_eq_logSup :
    statistic =
      vaart1998_likelihoodRatioStatisticFromLogSup
        fullLogLikelihoodSup nullLogLikelihoodSup
  /-- Likelihood-supremum display of the statistic. -/
  statistic_eq_likelihoodSup :
    statistic =
      vaart1998_likelihoodRatioStatisticFromLikelihoodSup
        fullLikelihoodSup nullLikelihoodSup

/--
Section 16.1 log-supremum display.
-/
theorem Vaart1998Section16_1LikelihoodRatioStatisticSource.logSup_display
    (S : Vaart1998Section16_1LikelihoodRatioStatisticSource) :
    S.statistic =
      vaart1998_likelihoodRatioStatisticFromLogSup
        S.fullLogLikelihoodSup S.nullLogLikelihoodSup :=
  S.statistic_eq_logSup

/--
Section 16.1 likelihood-supremum display.
-/
theorem Vaart1998Section16_1LikelihoodRatioStatisticSource.likelihoodSup_display
    (S : Vaart1998Section16_1LikelihoodRatioStatisticSource) :
    S.statistic =
      vaart1998_likelihoodRatioStatisticFromLikelihoodSup
        S.fullLikelihoodSup S.nullLikelihoodSup :=
  S.statistic_eq_likelihoodSup

/--
Example 16.1 multinomial likelihood-ratio statistic display, abstracting the
null-set divergence as `K(phat, P0)`: `2 n K(phat, P0)`.
-/
def vaart1998_multinomialLikelihoodRatioStatistic
    (sampleSize divergenceToNull : Real) : Real :=
  2 * sampleSize * divergenceToNull

/--
Example 16.1 source: after sufficiency reduction, the multinomial likelihood
ratio has the same statistic as the product observation model.
-/
structure Vaart1998Example16_1MultinomialLikelihoodRatioSource where
  /-- Sample size. -/
  sampleSize : Real
  /-- Divergence from the empirical probability vector to the null set. -/
  divergenceToNull : Real
  /-- Likelihood-ratio statistic. -/
  statistic : Real
  /-- Sufficiency reduction from individual observations to counts. -/
  sufficiencyReduction : Prop
  /-- Display `2 n K(phat, P0)`. -/
  statistic_eq :
    statistic =
      vaart1998_multinomialLikelihoodRatioStatistic
        sampleSize divergenceToNull
  /-- Source proof of the sufficiency reduction. -/
  sufficiencyReduction_proof :
    sufficiencyReduction

/--
Example 16.1 statistic display.
-/
theorem Vaart1998Example16_1MultinomialLikelihoodRatioSource.statistic_display
    (S : Vaart1998Example16_1MultinomialLikelihoodRatioSource) :
    S.statistic =
      vaart1998_multinomialLikelihoodRatioStatistic
        S.sampleSize S.divergenceToNull :=
  S.statistic_eq

/--
Example 16.2 exponential-family likelihood-ratio statistic display:
`2 n K(thetaHat, Theta0)`.
-/
def vaart1998_exponentialFamilyLikelihoodRatioStatistic
    (sampleSize divergenceToNull : Real) : Real :=
  2 * sampleSize * divergenceToNull

/--
Example 16.2 source: in a regular exponential family, the likelihood-ratio
statistic is `2 n K(thetaHat, Theta0)`.
-/
structure Vaart1998Example16_2ExponentialFamilyLikelihoodRatioSource where
  /-- Sample size. -/
  sampleSize : Real
  /-- Infimum of the exponential-family divergence over the null set. -/
  divergenceToNull : Real
  /-- Likelihood-ratio statistic. -/
  statistic : Real
  /-- Moment-equation characterization of the unrestricted MLE. -/
  unrestrictedMLEMomentEquation : Prop
  /-- Null-restricted MLE source. -/
  nullRestrictedMLESource : Prop
  /-- Display `2 n K(thetaHat, Theta0)`. -/
  statistic_eq :
    statistic =
      vaart1998_exponentialFamilyLikelihoodRatioStatistic
        sampleSize divergenceToNull
  /-- Source proof of the unrestricted MLE moment equation. -/
  unrestrictedMLEMomentEquation_proof :
    unrestrictedMLEMomentEquation
  /-- Source proof of the null restricted MLE source. -/
  nullRestrictedMLESource_proof :
    nullRestrictedMLESource

/--
Example 16.2 statistic display.
-/
theorem Vaart1998Example16_2ExponentialFamilyLikelihoodRatioSource.statistic_display
    (S : Vaart1998Example16_2ExponentialFamilyLikelihoodRatioSource) :
    S.statistic =
      vaart1998_exponentialFamilyLikelihoodRatioStatistic
        S.sampleSize S.divergenceToNull :=
  S.statistic_eq

/--
Quadratic approximation from the Taylor expansion around the true parameter.
The function `informationQuadratic` represents
`v^T I_theta v`.
-/
def vaart1998_likelihoodRatioQuadraticApproximation
    {E : Type*} (informationQuadratic : E -> Real)
    (scaledEstimatorDifference : E) : Real :=
  informationQuadratic scaledEstimatorDifference

/--
Section 16.2 source: Taylor expansion reduces the likelihood-ratio statistic
to the Fisher-information quadratic form in the difference of the unrestricted
and null-restricted MLEs.
-/
structure Vaart1998Section16_2TaylorExpansionSource
    {E : Type*} where
  /-- Fisher-information quadratic form. -/
  informationQuadratic : E -> Real
  /-- Scaled difference between unrestricted and null-restricted MLEs. -/
  scaledEstimatorDifference : Nat -> E
  /-- Likelihood-ratio statistics. -/
  statistic : Nat -> Real
  /-- Quadratic approximation. -/
  quadraticApproximation : Nat -> Real
  /-- Remainder term. -/
  remainder : Nat -> Real
  /-- Quadratic approximation display. -/
  quadraticApproximation_eq :
    quadraticApproximation =
      fun n =>
        vaart1998_likelihoodRatioQuadraticApproximation
          informationQuadratic (scaledEstimatorDifference n)
  /-- Statistic equals approximation plus remainder. -/
  statistic_eq_quadratic_plus_remainder :
    statistic = fun n => quadraticApproximation n + remainder n
  /-- Source assertion that the remainder is `o_P(1)`. -/
  remainder_op_one : Prop
  /-- Consistency of both MLEs under the true parameter. -/
  mleConsistency : Prop
  /-- Source proof of the remainder assertion. -/
  remainder_op_one_proof :
    remainder_op_one
  /-- Source proof of MLE consistency. -/
  mleConsistency_proof :
    mleConsistency

/--
Section 16.2 quadratic approximation display.
-/
theorem Vaart1998Section16_2TaylorExpansionSource.quadratic_approximation_display
    {E : Type*} (S : Vaart1998Section16_2TaylorExpansionSource (E := E)) :
    S.quadraticApproximation =
      fun n =>
        vaart1998_likelihoodRatioQuadraticApproximation
          S.informationQuadratic (S.scaledEstimatorDifference n) :=
  S.quadraticApproximation_eq

/--
Gaussian-limit likelihood-ratio statistic (16.5): squared distance to the
null local parameter set minus squared distance to the full local set after
the information-square-root transform.
-/
def vaart1998_gaussianLikelihoodRatioLimit
    {E : Type*} (informationSqrt : E -> E)
    (squaredDistance : E -> Set E -> Real)
    (observation : E) (nullLimitSet fullLimitSet : Set E) : Real :=
  squaredDistance (informationSqrt observation) (informationSqrt '' nullLimitSet) -
    squaredDistance (informationSqrt observation) (informationSqrt '' fullLimitSet)

/--
Degrees of freedom in Lemma 16.6: `k - l`.
-/
def vaart1998_chiSquareDegreesOfDistance
    (ambientDimension subspaceDimension : Nat) : Nat :=
  ambientDimension - subspaceDimension

/--
Lemma 16.6 source: squared distance from a standard normal vector to an
`l`-dimensional linear subspace of `R^k` is chi-square with `k-l` degrees of
freedom.
-/
structure Vaart1998Lemma16_6NormalDistanceChiSquareSource where
  /-- Ambient dimension `k`. -/
  ambientDimension : Nat
  /-- Subspace dimension `l`. -/
  subspaceDimension : Nat
  /-- Squared-distance statistic. -/
  squaredDistanceStatistic : Real
  /-- Degrees of freedom. -/
  degreesOfFreedom : Nat
  /-- Standard-normal source. -/
  standardNormalVectorSource : Prop
  /-- Linear-subspace source. -/
  linearSubspaceSource : Prop
  /-- Chi-square law assertion. -/
  chiSquareLaw : Prop
  /-- Degrees-of-freedom display. -/
  degreesOfFreedom_eq :
    degreesOfFreedom =
      vaart1998_chiSquareDegreesOfDistance
        ambientDimension subspaceDimension
  /-- Source proof that the vector is standard normal. -/
  standardNormalVectorSource_proof :
    standardNormalVectorSource
  /-- Source proof that the target is an `l`-dimensional linear subspace. -/
  linearSubspaceSource_proof :
    linearSubspaceSource
  /-- Source proof of the chi-square law. -/
  chiSquareLaw_proof :
    chiSquareLaw

/--
Lemma 16.6 degrees-of-freedom display.
-/
theorem Vaart1998Lemma16_6NormalDistanceChiSquareSource.degrees_of_freedom_display
    (S : Vaart1998Lemma16_6NormalDistanceChiSquareSource) :
    S.degreesOfFreedom =
      vaart1998_chiSquareDegreesOfDistance
        S.ambientDimension S.subspaceDimension :=
  S.degreesOfFreedom_eq

/--
Theorem 16.7 source: under DQM, consistency of restricted and unrestricted
MLEs, local set convergence, and LAN, the likelihood-ratio statistic converges
to the Gaussian likelihood-ratio statistic (16.5).
-/
structure Vaart1998Theorem16_7LikelihoodRatioLimitSource
    {Omega OmegaLimit H : Type*} [MeasurableSpace Omega]
    [MeasurableSpace OmegaLimit] [TopologicalSpace H]
    (P : H -> Nat -> Measure Omega) (Q : H -> Measure OmegaLimit)
    [∀ h n, IsProbabilityMeasure (P h n)]
    [∀ h, IsProbabilityMeasure (Q h)] where
  /-- Finite-sample likelihood-ratio statistics. -/
  likelihoodRatioStatistic : Nat -> Omega -> Real
  /-- Gaussian likelihood-ratio statistic (16.5). -/
  gaussianLimitStatistic : OmegaLimit -> Real
  /-- Chapter 9 experiment-limit source for the statistic. -/
  experimentLimitSource :
    Vaart1998ExperimentLimitSource (Z := Real) P Q
  /-- Local full parameter sets. -/
  fullLocalSet : Nat -> Set H
  /-- Limiting full local parameter set. -/
  fullLimitSet : Set H
  /-- Local null parameter sets. -/
  nullLocalSet : Nat -> Set H
  /-- Limiting null local parameter set. -/
  nullLimitSet : Set H
  /-- Finite statistic is the statistic in the experiment-limit source. -/
  likelihoodRatioStatistic_eq :
    likelihoodRatioStatistic = experimentLimitSource.statistic
  /-- Limit statistic is the statistic in the experiment-limit source. -/
  gaussianLimitStatistic_eq :
    gaussianLimitStatistic = experimentLimitSource.limitStatistic
  /-- DQM/LAN regularity source. -/
  dqmAndLANSource : Prop
  /-- Local Lipschitz log-likelihood source condition before Theorem 16.7. -/
  localLogLikelihoodLipschitz : Prop
  /-- Restricted and unrestricted MLE consistency. -/
  mleConsistency : Prop
  /-- Full local parameter sets converge. -/
  fullLocalSet_converges :
    vaart1998_localSetConvergence fullLocalSet fullLimitSet
  /-- Null local parameter sets converge. -/
  nullLocalSet_converges :
    vaart1998_localSetConvergence nullLocalSet nullLimitSet
  /-- Source proof of DQM/LAN regularity. -/
  dqmAndLANSource_proof :
    dqmAndLANSource
  /-- Source proof of the local Lipschitz log-likelihood condition. -/
  localLogLikelihoodLipschitz_proof :
    localLogLikelihoodLipschitz
  /-- Source proof of MLE consistency. -/
  mleConsistency_proof :
    mleConsistency

/--
Theorem 16.7 likelihood-ratio convergence in distribution.
-/
theorem Vaart1998Theorem16_7LikelihoodRatioLimitSource.likelihoodRatio_tendstoInDistribution
    {Omega OmegaLimit H : Type*} [MeasurableSpace Omega]
    [MeasurableSpace OmegaLimit] [TopologicalSpace H]
    {P : H -> Nat -> Measure Omega} {Q : H -> Measure OmegaLimit}
    [∀ h n, IsProbabilityMeasure (P h n)]
    [∀ h, IsProbabilityMeasure (Q h)]
    (S : Vaart1998Theorem16_7LikelihoodRatioLimitSource P Q)
    {h : H} (hh : h ∈ S.experimentLimitSource.parameterSet) :
    TendstoInDistribution S.likelihoodRatioStatistic atTop
      S.gaussianLimitStatistic (P h) (Q h) := by
  simpa [S.likelihoodRatioStatistic_eq, S.gaussianLimitStatistic_eq] using
    S.experimentLimitSource.tendstoInDistribution hh

/--
Theorem 16.7 packaged as a Chapter 9 experiment-limit source for the
likelihood-ratio statistic.
-/
def Vaart1998Theorem16_7LikelihoodRatioLimitSource.experimentLimit
    {Omega OmegaLimit H : Type*} [MeasurableSpace Omega]
    [MeasurableSpace OmegaLimit] [TopologicalSpace H]
    {P : H -> Nat -> Measure Omega} {Q : H -> Measure OmegaLimit}
    [∀ h n, IsProbabilityMeasure (P h n)]
    [∀ h, IsProbabilityMeasure (Q h)]
    (S : Vaart1998Theorem16_7LikelihoodRatioLimitSource P Q) :
    Vaart1998ExperimentLimitSource (Z := Real) P Q :=
  { parameterSet := S.experimentLimitSource.parameterSet
    statistic := S.likelihoodRatioStatistic
    limitStatistic := S.gaussianLimitStatistic
    statistic_tendstoInDistribution := fun _ hh =>
      S.likelihoodRatio_tendstoInDistribution hh }

/--
Local likelihood-ratio power envelope, parameterized by a noncentral
chi-square upper-tail function.
-/
def vaart1998_likelihoodRatioLocalPowerEnvelope
    (noncentralChiSquareUpperTail : Nat -> Real -> Real -> Real)
    (degreesOfFreedom : Nat) (criticalValue noncentrality : Real) :
    Real :=
  noncentralChiSquareUpperTail degreesOfFreedom criticalValue noncentrality

/--
Simple-null noncentrality along an eigen-direction:
`sqrt(lambda_e) * mu`.
-/
def vaart1998_simpleNullEigenDirectionNoncentrality
    (eigenvalue localMagnitude : Real) : Real :=
  Real.sqrt eigenvalue * localMagnitude

/--
Section 16.4 source: local powers of likelihood-ratio tests converge to the
noncentral chi-square power function determined by the Gaussian limit
experiment.
-/
structure Vaart1998Section16_4LikelihoodRatioPowerSource where
  /-- Noncentral chi-square upper-tail function. -/
  noncentralChiSquareUpperTail : Nat -> Real -> Real -> Real
  /-- Degrees of freedom. -/
  degreesOfFreedom : Nat
  /-- Critical value. -/
  criticalValue : Real
  /-- Noncentrality parameter. -/
  noncentrality : Real
  /-- Local power sequence. -/
  localPower : Nat -> Real
  /-- Limiting power. -/
  limitingPower : Real
  /-- Theorem 16.7 convergence source. -/
  likelihoodRatioLimitSource : Prop
  /-- Optional Chapter 15 half-space/hyperplane optimality source. -/
  efficientTestEnvelopeSource :
    Option Vaart1998Theorem15_4LANPowerUpperBoundSource
  /-- Limiting-power display. -/
  limitingPower_eq :
    limitingPower =
      vaart1998_likelihoodRatioLocalPowerEnvelope
        noncentralChiSquareUpperTail degreesOfFreedom criticalValue
        noncentrality
  /-- Local powers converge to the limiting power. -/
  localPower_tendsto :
    Tendsto localPower atTop (𝓝 limitingPower)
  /-- Source proof of the Theorem 16.7 convergence input. -/
  likelihoodRatioLimitSource_proof :
    likelihoodRatioLimitSource

/--
Section 16.4 local-power display.
-/
theorem Vaart1998Section16_4LikelihoodRatioPowerSource.local_power_tendsto
    (S : Vaart1998Section16_4LikelihoodRatioPowerSource) :
    Tendsto S.localPower atTop
      (𝓝 (vaart1998_likelihoodRatioLocalPowerEnvelope
        S.noncentralChiSquareUpperTail S.degreesOfFreedom S.criticalValue
        S.noncentrality)) := by
  simpa [S.limitingPower_eq] using S.localPower_tendsto

/--
Bartlett-corrected likelihood-ratio statistic:
`r Lambda_n / (1 + b_hat_n / n)`.
-/
def vaart1998_bartlettCorrectedLikelihoodRatio
    (degrees statistic correction sampleSize : Real) : Real :=
  degrees * statistic / (1 + correction / sampleSize)

/--
Section 16.5 source: Bartlett correction improves the chi-square
approximation by correcting the mean of the likelihood-ratio statistic.
-/
structure Vaart1998Section16_5BartlettCorrectionSource where
  /-- Degrees of freedom `r`. -/
  degrees : Real
  /-- Original likelihood-ratio statistic. -/
  statistic : Nat -> Real
  /-- Estimated Bartlett correction `b_hat_n`. -/
  correction : Nat -> Real
  /-- Sample size as a real number. -/
  sampleSize : Nat -> Real
  /-- Corrected statistic. -/
  correctedStatistic : Nat -> Real
  /-- Mean expansion source. -/
  meanExpansion : Prop
  /-- Corrected-statistic display. -/
  correctedStatistic_eq :
    correctedStatistic =
      fun n =>
        vaart1998_bartlettCorrectedLikelihoodRatio
          degrees (statistic n) (correction n) (sampleSize n)
  /-- Source proof of the mean expansion. -/
  meanExpansion_proof :
    meanExpansion

/--
Section 16.5 Bartlett-correction display.
-/
theorem Vaart1998Section16_5BartlettCorrectionSource.corrected_statistic_display
    (S : Vaart1998Section16_5BartlettCorrectionSource) :
    S.correctedStatistic =
      fun n =>
        vaart1998_bartlettCorrectedLikelihoodRatio
          S.degrees (S.statistic n) (S.correction n) (S.sampleSize n) :=
  S.correctedStatistic_eq

/--
The Bahadur slope upper bound for a simple alternative against a composite
null, written as `2 * inf_P Q log(q / p)`.
-/
def vaart1998_likelihoodRatioBahadurSlopeBound
    (nullKLDivergenceInf : Real) : Real :=
  2 * nullKLDivergenceInf

/--
Finite-hypothesis log-likelihood-ratio statistic used in Section 16.6:
`log (sup_Q L_Q / sup_P L_P)`.
-/
def vaart1998_finiteHypothesisLogLikelihoodRatioStatistic
    (alternativeLikelihoodSup nullLikelihoodSup : Real) : Real :=
  Real.log (alternativeLikelihoodSup / nullLikelihoodSup)

/--
Theorem 16.12 source: no test has Bahadur slope exceeding the simple
alternative bound, and finite-hypothesis likelihood-ratio tests attain the
bound for every alternative in the finite alternative set.
-/
structure Vaart1998Theorem16_12BahadurOptimalitySource where
  /-- Infimum of `Q log(q / p)` over the null set. -/
  nullKLDivergenceInf : Real
  /-- Upper bound for arbitrary-test Bahadur slopes. -/
  bahadurUpperBound : Real
  /-- Bahadur slope of an arbitrary sequence of tests. -/
  arbitraryTestSlope : Real
  /-- Bahadur slope of the finite-hypothesis likelihood-ratio statistic. -/
  likelihoodRatioSlope : Real
  /-- Finite null hypothesis source. -/
  finiteNullHypothesis : Prop
  /-- Finite alternative hypothesis source. -/
  finiteAlternativeHypothesis : Prop
  /-- Observed-level source for the tested statistics. -/
  observedLevelSource : Prop
  /-- Upper-bound display. -/
  bahadurUpperBound_eq :
    bahadurUpperBound =
      vaart1998_likelihoodRatioBahadurSlopeBound nullKLDivergenceInf
  /-- Any test slope is bounded above. -/
  arbitraryTestSlope_le :
    arbitraryTestSlope <= bahadurUpperBound
  /-- Likelihood-ratio statistic attains the bound. -/
  likelihoodRatioSlope_eq :
    likelihoodRatioSlope = bahadurUpperBound
  /-- Source proof of the finite null hypothesis. -/
  finiteNullHypothesis_proof :
    finiteNullHypothesis
  /-- Source proof of the finite alternative hypothesis. -/
  finiteAlternativeHypothesis_proof :
    finiteAlternativeHypothesis
  /-- Source proof of the observed-level construction. -/
  observedLevelSource_proof :
    observedLevelSource

/--
Theorem 16.12 arbitrary-test upper bound.
-/
theorem Vaart1998Theorem16_12BahadurOptimalitySource.arbitrary_test_slope_upper_bound
    (S : Vaart1998Theorem16_12BahadurOptimalitySource) :
    S.arbitraryTestSlope <=
      vaart1998_likelihoodRatioBahadurSlopeBound
        S.nullKLDivergenceInf := by
  simpa [S.bahadurUpperBound_eq] using S.arbitraryTestSlope_le

/--
Theorem 16.12 likelihood-ratio Bahadur optimality display.
-/
theorem Vaart1998Theorem16_12BahadurOptimalitySource.likelihood_ratio_attains_bound
    (S : Vaart1998Theorem16_12BahadurOptimalitySource) :
    S.likelihoodRatioSlope =
      vaart1998_likelihoodRatioBahadurSlopeBound
        S.nullKLDivergenceInf := by
  simpa [S.bahadurUpperBound_eq] using S.likelihoodRatioSlope_eq

end AsymptoticStatistics
end StatInference
