import StatInference.AsymptoticStatistics.LikelihoodRatioTests

/-!
# van der Vaart 1998 Chapter 17 chi-square test interfaces

This module opens the Chapter 17 lane.  It records Pearson and modified
Pearson statistics, minimum chi-square statistics, their likelihood-ratio
handoffs, multinomial and independence degrees of freedom, goodness-of-fit
interfaces, random-partition stability, and Bahadur-efficiency displays.
-/

noncomputable section

namespace StatInference
namespace AsymptoticStatistics

open Filter MeasureTheory ProbabilityTheory
open scoped ENNReal ProbabilityTheory Topology BigOperators

/--
The generic weighted quadratic form `sum_i lambda_i z_i^2` from Lemma 17.1.
-/
def vaart1998_weightedChiSquareQuadraticForm
    {Cell : Type*} [Fintype Cell]
    (eigenvalue coordinate : Cell -> Real) : Real :=
  ∑ i, eigenvalue i * coordinate i ^ 2

/--
Pearson's statistic for observed and expected cell counts.
-/
def vaart1998_pearsonStatistic
    {Cell : Type*} [Fintype Cell]
    (observed expected : Cell -> Real) : Real :=
  ∑ i, (observed i - expected i) ^ 2 / expected i

/--
Pearson's multinomial statistic
`sum_i (X_i - n a_i)^2 / (n a_i)`.
-/
def vaart1998_multinomialPearsonStatistic
    {Cell : Type*} [Fintype Cell]
    (sampleSize : Real) (count nullProbability : Cell -> Real) : Real :=
  vaart1998_pearsonStatistic count (fun i => sampleSize * nullProbability i)

/--
The modified Pearson statistic with an estimated null probability vector.
-/
def vaart1998_modifiedPearsonStatistic
    {Cell : Type*} [Fintype Cell]
    (sampleSize : Real) (count estimatedProbability : Cell -> Real) :
    Real :=
  vaart1998_pearsonStatistic count
    (fun i => sampleSize * estimatedProbability i)

/--
The Hellinger symmetrization of Pearson's statistic from Section 17.2:
`4 sum_i (sqrt X_i - sqrt(n a_i))^2`.
-/
def vaart1998_hellingerChiSquareStatistic
    {Cell : Type*} [Fintype Cell]
    (sampleSize : Real) (count nullProbability : Cell -> Real) : Real :=
  4 * ∑ i, (Real.sqrt (count i) -
    Real.sqrt (sampleSize * nullProbability i)) ^ 2

/--
The minimum chi-square statistic: infimum over a null set of probability
vectors of the Pearson statistic.
-/
def vaart1998_minimumChiSquareStatistic
    {Cell : Type*} [Fintype Cell]
    (sampleSize : Real) (count : Cell -> Real)
    (nullSet : Set (Cell -> Real)) : Real :=
  sInf ((fun p =>
    vaart1998_multinomialPearsonStatistic sampleSize count p) '' nullSet)

/--
The multinomial likelihood-ratio statistic in Chapter 17:
`2 sum_i X_i log (X_i / (n p_i))`.
-/
def vaart1998_multinomialLikelihoodRatioCellStatistic
    {Cell : Type*} [Fintype Cell]
    (sampleSize : Real) (count probability : Cell -> Real) : Real :=
  2 * ∑ i, count i * Real.log (count i / (sampleSize * probability i))

/--
Degrees of freedom for Pearson's simple multinomial statistic: `k - 1`.
-/
def vaart1998_pearsonSimpleDegreesOfFreedom
    (cellCount : Nat) : Nat :=
  cellCount - 1

/--
Degrees of freedom after estimating an `l`-dimensional parameter:
`k - 1 - l`.
-/
def vaart1998_estimatedParameterChiSquareDegreesOfFreedom
    (cellCount parameterDimension : Nat) : Nat :=
  cellCount - 1 - parameterDimension

/--
Degrees of freedom for independence in a `k x r` contingency table:
`(k - 1)(r - 1)`.
-/
def vaart1998_independenceTableDegreesOfFreedom
    (rowCount columnCount : Nat) : Nat :=
  (rowCount - 1) * (columnCount - 1)

/--
The grouped empirical cell vector used in goodness-of-fit tests.
-/
def vaart1998_groupedEmpiricalCellVector
    {Omega Cell : Type*}
    (empiricalMeasure : Set Omega -> Real)
    (cells : Cell -> Set Omega) : Cell -> Real :=
  fun i => empiricalMeasure (cells i)

/--
The chi-square divergence map `C(p,a) = sum_i (p_i-a_i)^2/a_i` used for
Bahadur slopes in Section 17.6.
-/
def vaart1998_chiSquareDivergence
    {Cell : Type*} [Fintype Cell]
    (p a : Cell -> Real) : Real :=
  ∑ i, (p i - a i) ^ 2 / a i

/--
The finite Kullback-Leibler divergence map
`K(p,a) = sum_i p_i log(p_i/a_i)` used in Section 17.6.
-/
def vaart1998_discreteKLDivergence
    {Cell : Type*} [Fintype Cell]
    (p a : Cell -> Real) : Real :=
  ∑ i, p i * Real.log (p i / a i)

/--
Pearson Bahadur slope at an alternative `q`:
`2 inf_{p : C(p,a) >= C(q,a)} K(p,a)`.
-/
def vaart1998_pearsonBahadurSlope
    {Cell : Type*} [Fintype Cell]
    (a q : Cell -> Real) : Real :=
  2 * sInf {r : Real | ∃ p : Cell -> Real,
    vaart1998_chiSquareDivergence p a >=
      vaart1998_chiSquareDivergence q a ∧
    r = vaart1998_discreteKLDivergence p a}

/--
Likelihood-ratio Bahadur slope at an alternative `q`: `2 K(q,a)`.
-/
def vaart1998_likelihoodRatioDiscreteBahadurSlope
    {Cell : Type*} [Fintype Cell]
    (q a : Cell -> Real) : Real :=
  2 * vaart1998_discreteKLDivergence q a

/--
Lemma 17.1 source: the norm of a zero-mean normal vector is distributed as a
weighted sum of independent squared standard normals with weights equal to the
covariance eigenvalues.
-/
structure Vaart1998Lemma17_1QuadraticNormalSource
    {Cell : Type*} [Fintype Cell] where
  /-- Covariance eigenvalues. -/
  eigenvalue : Cell -> Real
  /-- Standard-normal coordinates in an eigenbasis. -/
  standardNormalCoordinate : Cell -> Real
  /-- Norm-square statistic of the original normal vector. -/
  normSquareStatistic : Real
  /-- Weighted chi-square representation. -/
  weightedStatistic : Real
  /-- Source assertion that the vector is centered normal. -/
  centeredNormalSource : Prop
  /-- Source assertion for the spectral/eigenbasis representation. -/
  spectralRepresentation : Prop
  /-- Distributional equality assertion. -/
  distributionalEquality : Prop
  /-- Weighted-sum display. -/
  weightedStatistic_eq :
    weightedStatistic =
      vaart1998_weightedChiSquareQuadraticForm
        eigenvalue standardNormalCoordinate
  /-- Norm-square distribution display. -/
  normSquare_eq_weightedStatistic :
    normSquareStatistic = weightedStatistic
  /-- Source proof of centered normality. -/
  centeredNormalSource_proof :
    centeredNormalSource
  /-- Source proof of the spectral representation. -/
  spectralRepresentation_proof :
    spectralRepresentation
  /-- Source proof of the distributional equality. -/
  distributionalEquality_proof :
    distributionalEquality

/--
Lemma 17.1 weighted chi-square display.
-/
theorem Vaart1998Lemma17_1QuadraticNormalSource.weighted_statistic_display
    {Cell : Type*} [Fintype Cell]
    (S : Vaart1998Lemma17_1QuadraticNormalSource (Cell := Cell)) :
    S.weightedStatistic =
      vaart1998_weightedChiSquareQuadraticForm
        S.eigenvalue S.standardNormalCoordinate :=
  S.weightedStatistic_eq

/--
Lemma 17.1 norm-square distribution display.
-/
theorem Vaart1998Lemma17_1QuadraticNormalSource.norm_square_display
    {Cell : Type*} [Fintype Cell]
    (S : Vaart1998Lemma17_1QuadraticNormalSource (Cell := Cell)) :
    S.normSquareStatistic = S.weightedStatistic :=
  S.normSquare_eq_weightedStatistic

/--
Theorem 17.2 source: Pearson's statistic for a multinomial vector with
positive null cell probabilities converges to `chi^2_{k-1}`.
-/
structure Vaart1998Theorem17_2PearsonStatisticSource
    {Cell : Type*} [Fintype Cell] where
  /-- Sample size. -/
  sampleSize : Nat -> Real
  /-- Multinomial cell counts. -/
  count : Nat -> Cell -> Real
  /-- Null cell probabilities `a_i`. -/
  nullProbability : Cell -> Real
  /-- Pearson statistic. -/
  statistic : Nat -> Real
  /-- Degrees of freedom. -/
  degreesOfFreedom : Nat
  /-- Positivity of null cell probabilities. -/
  nullProbability_pos : Prop
  /-- Multinomial source hypothesis. -/
  multinomialSource : Prop
  /-- CLT source for standardized cell counts. -/
  standardizedCLTSource : Prop
  /-- Chapter 16/Lemma 17.1 chi-square distance source. -/
  chiSquareDistanceSource :
    Vaart1998Lemma16_6NormalDistanceChiSquareSource
  /-- Pearson statistic display. -/
  statistic_eq :
    statistic =
      fun n =>
        vaart1998_multinomialPearsonStatistic
          (sampleSize n) (count n) nullProbability
  /-- Degrees-of-freedom display. -/
  degreesOfFreedom_eq :
    degreesOfFreedom =
      vaart1998_pearsonSimpleDegreesOfFreedom (Fintype.card Cell)
  /-- Asymptotic chi-square convergence assertion. -/
  statistic_tendsto_chiSquare : Prop
  /-- Source proof of positive null cell probabilities. -/
  nullProbability_pos_proof :
    nullProbability_pos
  /-- Source proof of the multinomial input. -/
  multinomialSource_proof :
    multinomialSource
  /-- Source proof of the standardized CLT input. -/
  standardizedCLTSource_proof :
    standardizedCLTSource
  /-- Source proof of the asymptotic chi-square convergence. -/
  statistic_tendsto_chiSquare_proof :
    statistic_tendsto_chiSquare

/--
Theorem 17.2 Pearson statistic display.
-/
theorem Vaart1998Theorem17_2PearsonStatisticSource.statistic_display
    {Cell : Type*} [Fintype Cell]
    (S : Vaart1998Theorem17_2PearsonStatisticSource (Cell := Cell)) :
    S.statistic =
      fun n =>
        vaart1998_multinomialPearsonStatistic
          (S.sampleSize n) (S.count n) S.nullProbability :=
  S.statistic_eq

/--
Theorem 17.2 degrees-of-freedom display.
-/
theorem Vaart1998Theorem17_2PearsonStatisticSource.degrees_of_freedom_display
    {Cell : Type*} [Fintype Cell]
    (S : Vaart1998Theorem17_2PearsonStatisticSource (Cell := Cell)) :
    S.degreesOfFreedom =
      vaart1998_pearsonSimpleDegreesOfFreedom (Fintype.card Cell) :=
  S.degreesOfFreedom_eq

/--
Theorem 17.2 asymptotic chi-square conclusion.
-/
theorem Vaart1998Theorem17_2PearsonStatisticSource.asymptotic_chi_square
    {Cell : Type*} [Fintype Cell]
    (S : Vaart1998Theorem17_2PearsonStatisticSource (Cell := Cell)) :
    S.statistic_tendsto_chiSquare :=
  S.statistic_tendsto_chiSquare_proof

/--
Section 17.2 source: the Hellinger statistic is asymptotically equivalent to
the Pearson statistic when empirical cell probabilities converge to the null.
-/
structure Vaart1998Section17_2HellingerStatisticSource
    {Cell : Type*} [Fintype Cell] where
  /-- Sample size. -/
  sampleSize : Nat -> Real
  /-- Cell counts. -/
  count : Nat -> Cell -> Real
  /-- Null probabilities. -/
  nullProbability : Cell -> Real
  /-- Pearson statistic. -/
  pearsonStatistic : Nat -> Real
  /-- Hellinger statistic. -/
  hellingerStatistic : Nat -> Real
  /-- Pearson display. -/
  pearsonStatistic_eq :
    pearsonStatistic =
      fun n =>
        vaart1998_multinomialPearsonStatistic
          (sampleSize n) (count n) nullProbability
  /-- Hellinger display. -/
  hellingerStatistic_eq :
    hellingerStatistic =
      fun n =>
        vaart1998_hellingerChiSquareStatistic
          (sampleSize n) (count n) nullProbability
  /-- Empirical cell probabilities converge to the null vector. -/
  empiricalConvergence : Prop
  /-- Asymptotic equivalence assertion. -/
  asymptoticEquivalence : Prop
  /-- Source proof of empirical convergence. -/
  empiricalConvergence_proof :
    empiricalConvergence
  /-- Source proof of asymptotic equivalence. -/
  asymptoticEquivalence_proof :
    asymptoticEquivalence

/--
Section 17.2 Hellinger statistic display.
-/
theorem Vaart1998Section17_2HellingerStatisticSource.hellinger_statistic_display
    {Cell : Type*} [Fintype Cell]
    (S : Vaart1998Section17_2HellingerStatisticSource (Cell := Cell)) :
    S.hellingerStatistic =
      fun n =>
        vaart1998_hellingerChiSquareStatistic
          (S.sampleSize n) (S.count n) S.nullProbability :=
  S.hellingerStatistic_eq

/--
Section 17.3 source: the modified Pearson statistic with an estimated null
probability vector.
-/
structure Vaart1998Section17_3EstimatedParameterPearsonSource
    {Cell : Type*} [Fintype Cell] where
  /-- Sample size. -/
  sampleSize : Nat -> Real
  /-- Cell counts. -/
  count : Nat -> Cell -> Real
  /-- Estimated null probabilities. -/
  estimatedProbability : Nat -> Cell -> Real
  /-- Modified Pearson statistic. -/
  modifiedStatistic : Nat -> Real
  /-- Modified Pearson display. -/
  modifiedStatistic_eq :
    modifiedStatistic =
      fun n =>
        vaart1998_modifiedPearsonStatistic
          (sampleSize n) (count n) (estimatedProbability n)
  /-- Estimator is suitable under the null. -/
  estimatorSource : Prop
  /-- Quadratic-normal limit source. -/
  quadraticNormalLimitSource :
    Vaart1998Lemma17_1QuadraticNormalSource (Cell := Cell)
  /-- Source proof for the estimator. -/
  estimatorSource_proof :
    estimatorSource

/--
Section 17.3 modified Pearson display.
-/
theorem Vaart1998Section17_3EstimatedParameterPearsonSource.modified_statistic_display
    {Cell : Type*} [Fintype Cell]
    (S : Vaart1998Section17_3EstimatedParameterPearsonSource
      (Cell := Cell)) :
    S.modifiedStatistic =
      fun n =>
        vaart1998_modifiedPearsonStatistic
          (S.sampleSize n) (S.count n) (S.estimatedProbability n) :=
  S.modifiedStatistic_eq

/--
The minimum chi-square estimator source: it attains the Pearson infimum over
the null probability set.
-/
structure Vaart1998MinimumChiSquareEstimatorSource
    {Cell : Type*} [Fintype Cell] where
  /-- Sample size. -/
  sampleSize : Nat -> Real
  /-- Cell counts. -/
  count : Nat -> Cell -> Real
  /-- Null probability set. -/
  nullSet : Set (Cell -> Real)
  /-- Minimum chi-square estimator. -/
  estimator : Nat -> Cell -> Real
  /-- Minimum chi-square statistic. -/
  minimumStatistic : Nat -> Real
  /-- Estimator belongs to the null set. -/
  estimator_mem_nullSet :
    ∀ n, estimator n ∈ nullSet
  /-- Minimum statistic display. -/
  minimumStatistic_eq :
    minimumStatistic =
      fun n =>
        vaart1998_minimumChiSquareStatistic
          (sampleSize n) (count n) nullSet
  /-- Attainment/source assertion for the infimum. -/
  infimumAttained : Prop
  /-- Source proof of infimum attainment. -/
  infimumAttained_proof :
    infimumAttained

/--
Minimum chi-square statistic display.
-/
theorem Vaart1998MinimumChiSquareEstimatorSource.minimum_statistic_display
    {Cell : Type*} [Fintype Cell]
    (S : Vaart1998MinimumChiSquareEstimatorSource (Cell := Cell)) :
    S.minimumStatistic =
      fun n =>
        vaart1998_minimumChiSquareStatistic
          (S.sampleSize n) (S.count n) S.nullSet :=
  S.minimumStatistic_eq

/--
Lemma 17.3 source: minimum chi-square, modified Pearson at the MLE, and the
multinomial likelihood-ratio statistic are asymptotically equivalent.
-/
structure Vaart1998Lemma17_3MinimumChiSquareLikelihoodSource where
  /-- Minimum chi-square statistic. -/
  minimumChiSquareStatistic : Nat -> Real
  /-- Modified Pearson statistic at the null MLE. -/
  modifiedPearsonStatistic : Nat -> Real
  /-- Multinomial likelihood-ratio statistic. -/
  likelihoodRatioStatistic : Nat -> Real
  /-- Maximum likelihood estimator is `sqrt n`-consistent. -/
  mleRootNConsistent : Prop
  /-- Minimum chi-square estimator is `sqrt n`-consistent. -/
  minimumChiSquareRootNConsistent : Prop
  /-- Taylor expansion of the log likelihood ratio. -/
  logTaylorExpansion : Prop
  /-- Minimum chi-square equals modified Pearson up to `o_P(1)`. -/
  minimum_eq_modifiedPearson_op :
    Prop
  /-- Modified Pearson equals likelihood-ratio statistic up to `o_P(1)`. -/
  modifiedPearson_eq_likelihoodRatio_op :
    Prop
  /-- Source proof of MLE root-n consistency. -/
  mleRootNConsistent_proof :
    mleRootNConsistent
  /-- Source proof of minimum-chi-square root-n consistency. -/
  minimumChiSquareRootNConsistent_proof :
    minimumChiSquareRootNConsistent
  /-- Source proof of the Taylor expansion. -/
  logTaylorExpansion_proof :
    logTaylorExpansion
  /-- Source proof of minimum chi-square/modified Pearson equivalence. -/
  minimum_eq_modifiedPearson_op_proof :
    minimum_eq_modifiedPearson_op
  /-- Source proof of modified Pearson/likelihood-ratio equivalence. -/
  modifiedPearson_eq_likelihoodRatio_op_proof :
    modifiedPearson_eq_likelihoodRatio_op

/--
Lemma 17.3 minimum chi-square/modified Pearson equivalence.
-/
theorem Vaart1998Lemma17_3MinimumChiSquareLikelihoodSource.minimum_eq_modifiedPearson
    (S : Vaart1998Lemma17_3MinimumChiSquareLikelihoodSource) :
    S.minimum_eq_modifiedPearson_op :=
  S.minimum_eq_modifiedPearson_op_proof

/--
Lemma 17.3 modified Pearson/likelihood-ratio equivalence.
-/
theorem Vaart1998Lemma17_3MinimumChiSquareLikelihoodSource.modifiedPearson_eq_likelihoodRatio
    (S : Vaart1998Lemma17_3MinimumChiSquareLikelihoodSource) :
    S.modifiedPearson_eq_likelihoodRatio_op :=
  S.modifiedPearson_eq_likelihoodRatio_op_proof

/--
Theorem 17.4 source: local convergence of the null probability set gives the
minimum chi-square limit as a squared distance to the limiting set; the
likelihood-ratio limit source from Chapter 16 is recorded as a reusable route.
-/
structure Vaart1998Theorem17_4MinimumChiSquareLimitSource
    {Cell H : Type*} [Fintype Cell] [TopologicalSpace H] where
  /-- Sample size. -/
  sampleSize : Nat -> Real
  /-- Cell counts. -/
  count : Nat -> Cell -> Real
  /-- Null probability set. -/
  nullSet : Set (Cell -> Real)
  /-- Moving local null sets. -/
  localNullSet : Nat -> Set H
  /-- Limiting local null set. -/
  limitNullSet : Set H
  /-- Minimum chi-square statistic. -/
  minimumStatistic : Nat -> Real
  /-- Limiting squared-distance statistic. -/
  limitStatistic : Real
  /-- Minimum chi-square statistic display. -/
  minimumStatistic_eq :
    minimumStatistic =
      fun n =>
        vaart1998_minimumChiSquareStatistic
          (sampleSize n) (count n) nullSet
  /-- Local set convergence, reusing Chapter 16's set-convergence notion. -/
  localNullSet_converges :
    vaart1998_localSetConvergence localNullSet limitNullSet
  /-- Multinomial CLT source for the standardized cell vector. -/
  multinomialCLTSource : Prop
  /-- Chapter 16 likelihood-ratio limit route. -/
  likelihoodRatioLimitSource : Prop
  /-- Minimum chi-square convergence assertion. -/
  minimumStatistic_tendsto_limit : Prop
  /-- Source proof of the multinomial CLT input. -/
  multinomialCLTSource_proof :
    multinomialCLTSource
  /-- Source proof of the likelihood-ratio handoff. -/
  likelihoodRatioLimitSource_proof :
    likelihoodRatioLimitSource
  /-- Source proof of minimum chi-square convergence. -/
  minimumStatistic_tendsto_limit_proof :
    minimumStatistic_tendsto_limit

/--
Theorem 17.4 minimum chi-square statistic display.
-/
theorem Vaart1998Theorem17_4MinimumChiSquareLimitSource.minimum_statistic_display
    {Cell H : Type*} [Fintype Cell] [TopologicalSpace H]
    (S : Vaart1998Theorem17_4MinimumChiSquareLimitSource
      (Cell := Cell) (H := H)) :
    S.minimumStatistic =
      fun n =>
        vaart1998_minimumChiSquareStatistic
          (S.sampleSize n) (S.count n) S.nullSet :=
  S.minimumStatistic_eq

/--
Theorem 17.4 minimum chi-square convergence conclusion.
-/
theorem Vaart1998Theorem17_4MinimumChiSquareLimitSource.minimum_statistic_tendsto_limit
    {Cell H : Type*} [Fintype Cell] [TopologicalSpace H]
    (S : Vaart1998Theorem17_4MinimumChiSquareLimitSource
      (Cell := Cell) (H := H)) :
    S.minimumStatistic_tendsto_limit :=
  S.minimumStatistic_tendsto_limit_proof

/--
Corollary 17.5 source: if the limiting null set is an `l`-dimensional linear
subspace, the minimum chi-square and modified Pearson statistics converge to
`chi^2_{k-1-l}`.
-/
structure Vaart1998Corollary17_5EstimatedParameterChiSquareSource
    {Cell : Type*} [Fintype Cell] where
  /-- Parameter dimension `l`. -/
  parameterDimension : Nat
  /-- Degrees of freedom `k - 1 - l`. -/
  degreesOfFreedom : Nat
  /-- Theorem 17.4 source. -/
  minimumChiSquareLimitSource : Prop
  /-- Lemma 16.6 chi-square distance source. -/
  chiSquareDistanceSource :
    Vaart1998Lemma16_6NormalDistanceChiSquareSource
  /-- Modified Pearson convergence source. -/
  modifiedPearsonLimitSource : Prop
  /-- Degrees-of-freedom display. -/
  degreesOfFreedom_eq :
    degreesOfFreedom =
      vaart1998_estimatedParameterChiSquareDegreesOfFreedom
        (Fintype.card Cell) parameterDimension
  /-- Source proof of Theorem 17.4 input. -/
  minimumChiSquareLimitSource_proof :
    minimumChiSquareLimitSource
  /-- Source proof of modified Pearson convergence. -/
  modifiedPearsonLimitSource_proof :
    modifiedPearsonLimitSource

/--
Corollary 17.5 degrees-of-freedom display.
-/
theorem Vaart1998Corollary17_5EstimatedParameterChiSquareSource.degrees_of_freedom_display
    {Cell : Type*} [Fintype Cell]
    (S : Vaart1998Corollary17_5EstimatedParameterChiSquareSource
      (Cell := Cell)) :
    S.degreesOfFreedom =
      vaart1998_estimatedParameterChiSquareDegreesOfFreedom
        (Fintype.card Cell) S.parameterDimension :=
  S.degreesOfFreedom_eq

/--
Example 17.6 source: a full-rank `l`-dimensional parametric null family in
the simplex gives a `chi^2_{k-l-1}` limit.
-/
structure Vaart1998Example17_6ParametricModelChiSquareSource
    {Cell : Type*} [Fintype Cell] where
  /-- Parameter dimension. -/
  parameterDimension : Nat
  /-- Differentiable full-rank probability map source. -/
  fullRankDifferentiableMap : Prop
  /-- Corollary 17.5 source. -/
  estimatedParameterSource :
    Vaart1998Corollary17_5EstimatedParameterChiSquareSource
      (Cell := Cell)
  /-- The displayed parameter dimension agrees with Corollary 17.5's dimension. -/
  estimatedParameterSource_parameterDimension_eq :
    estimatedParameterSource.parameterDimension = parameterDimension
  /-- Source proof of the full-rank differentiability input. -/
  fullRankDifferentiableMap_proof :
    fullRankDifferentiableMap

/--
Example 17.6 degrees-of-freedom display.
-/
theorem Vaart1998Example17_6ParametricModelChiSquareSource.degrees_of_freedom_display
    {Cell : Type*} [Fintype Cell]
    (S : Vaart1998Example17_6ParametricModelChiSquareSource
      (Cell := Cell)) :
    S.estimatedParameterSource.degreesOfFreedom =
      vaart1998_estimatedParameterChiSquareDegreesOfFreedom
        (Fintype.card Cell) S.parameterDimension :=
  calc
    S.estimatedParameterSource.degreesOfFreedom =
        vaart1998_estimatedParameterChiSquareDegreesOfFreedom
          (Fintype.card Cell)
          S.estimatedParameterSource.parameterDimension :=
      S.estimatedParameterSource.degrees_of_freedom_display
    _ =
        vaart1998_estimatedParameterChiSquareDegreesOfFreedom
          (Fintype.card Cell) S.parameterDimension := by
      rw [S.estimatedParameterSource_parameterDimension_eq]

/--
Corollary 17.7 source: independence testing in a `k x r` contingency table
has `chi^2_{(k-1)(r-1)}` null limit.
-/
structure Vaart1998Corollary17_7IndependenceTableSource where
  /-- Number of row levels. -/
  rowCount : Nat
  /-- Number of column levels. -/
  columnCount : Nat
  /-- Degrees of freedom. -/
  degreesOfFreedom : Nat
  /-- Multinomial table source. -/
  multinomialTableSource : Prop
  /-- Product-probability null source. -/
  productProbabilityNullSource : Prop
  /-- Modified Pearson statistic source. -/
  modifiedPearsonSource : Prop
  /-- Degrees-of-freedom display. -/
  degreesOfFreedom_eq :
    degreesOfFreedom =
      vaart1998_independenceTableDegreesOfFreedom rowCount columnCount
  /-- Source proof of the multinomial table input. -/
  multinomialTableSource_proof :
    multinomialTableSource
  /-- Source proof of the product-probability null. -/
  productProbabilityNullSource_proof :
    productProbabilityNullSource
  /-- Source proof of the modified Pearson statistic input. -/
  modifiedPearsonSource_proof :
    modifiedPearsonSource

/--
Corollary 17.7 degrees-of-freedom display.
-/
theorem Vaart1998Corollary17_7IndependenceTableSource.degrees_of_freedom_display
    (S : Vaart1998Corollary17_7IndependenceTableSource) :
    S.degreesOfFreedom =
      vaart1998_independenceTableDegreesOfFreedom
        S.rowCount S.columnCount :=
  S.degreesOfFreedom_eq

/--
Section 17.5 goodness-of-fit grouping source: grouping raw observations into
finitely many cells gives a multinomial vector and a modified Pearson
statistic.
-/
structure Vaart1998Section17_5GoodnessOfFitGroupingSource
    {Omega Cell : Type*} [Fintype Cell] where
  /-- Empirical measure of the raw sample. -/
  empiricalMeasure : Nat -> Set Omega -> Real
  /-- Partition cells. -/
  cells : Cell -> Set Omega
  /-- Estimated null cell probabilities. -/
  estimatedCellProbability : Nat -> Cell -> Real
  /-- Grouped empirical cell vector. -/
  groupedCellVector : Nat -> Cell -> Real
  /-- Grouped chi-square statistic. -/
  statistic : Nat -> Real
  /-- The cells form a finite partition, recorded source-shaped. -/
  finitePartitionSource : Prop
  /-- Grouped vector display. -/
  groupedCellVector_eq :
    groupedCellVector =
      fun n =>
        vaart1998_groupedEmpiricalCellVector
          (empiricalMeasure n) cells
  /-- Grouped statistic display. -/
  statistic_eq :
    statistic =
      fun n =>
        vaart1998_modifiedPearsonStatistic
          1 (groupedCellVector n) (estimatedCellProbability n)
  /-- Multinomial reduction source. -/
  multinomialReductionSource : Prop
  /-- Source proof of the finite partition. -/
  finitePartitionSource_proof :
    finitePartitionSource
  /-- Source proof of the multinomial reduction. -/
  multinomialReductionSource_proof :
    multinomialReductionSource

/--
Section 17.5 grouped cell-vector display.
-/
theorem Vaart1998Section17_5GoodnessOfFitGroupingSource.grouped_cell_vector_display
    {Omega Cell : Type*} [Fintype Cell]
    (S : Vaart1998Section17_5GoodnessOfFitGroupingSource
      (Omega := Omega) (Cell := Cell)) :
    S.groupedCellVector =
      fun n =>
        vaart1998_groupedEmpiricalCellVector
          (S.empiricalMeasure n) S.cells :=
  S.groupedCellVector_eq

/--
Example 17.8 source: efficient raw-data parameter estimators generally lead
to a Gaussian quadratic-form limit rather than a standard chi-square limit.
-/
structure Vaart1998Example17_8RawDataEstimatorGoodnessOfFitSource
    {Cell : Type*} [Fintype Cell] where
  /-- Cell probability vector under the parametric null. -/
  cellProbability : Cell -> Real
  /-- Score/cell derivative matrix source. -/
  derivativeMatrixSource : Prop
  /-- Efficient estimator source. -/
  efficientEstimatorSource : Prop
  /-- Quadratic-normal limit source from Lemma 17.1. -/
  quadraticNormalSource :
    Vaart1998Lemma17_1QuadraticNormalSource (Cell := Cell)
  /-- Source assertion that the limit is not generally standard chi-square. -/
  nonstandardLimitSource : Prop
  /-- Source proof of the derivative matrix input. -/
  derivativeMatrixSource_proof :
    derivativeMatrixSource
  /-- Source proof of estimator efficiency. -/
  efficientEstimatorSource_proof :
    efficientEstimatorSource
  /-- Source proof of the nonstandard-limit assertion. -/
  nonstandardLimitSource_proof :
    nonstandardLimitSource

/--
Rao-Robson-Nikulin squared-norm statistic after applying a covariance
standardization transform.
-/
def vaart1998_raoRobsonNikulinStatistic
    {Cell : Type*} [Fintype Cell]
    (standardizedResidual : Cell -> Real) : Real :=
  ∑ i, standardizedResidual i ^ 2

/--
Rao-Robson-Nikulin source: standardizing the residual vector restores a
`chi^2_{k-1}` limit.
-/
structure Vaart1998RaoRobsonNikulinStatisticSource
    {Cell : Type*} [Fintype Cell] where
  /-- Standardized residual vector. -/
  standardizedResidual : Nat -> Cell -> Real
  /-- Statistic. -/
  statistic : Nat -> Real
  /-- Degrees of freedom. -/
  degreesOfFreedom : Nat
  /-- Standardization source. -/
  standardizationSource : Prop
  /-- Statistic display. -/
  statistic_eq :
    statistic =
      fun n => vaart1998_raoRobsonNikulinStatistic
        (standardizedResidual n)
  /-- Degrees-of-freedom display. -/
  degreesOfFreedom_eq :
    degreesOfFreedom =
      vaart1998_pearsonSimpleDegreesOfFreedom (Fintype.card Cell)
  /-- Source proof of standardization. -/
  standardizationSource_proof :
    standardizationSource

/--
Rao-Robson-Nikulin statistic display.
-/
theorem Vaart1998RaoRobsonNikulinStatisticSource.statistic_display
    {Cell : Type*} [Fintype Cell]
    (S : Vaart1998RaoRobsonNikulinStatisticSource (Cell := Cell)) :
    S.statistic =
      fun n => vaart1998_raoRobsonNikulinStatistic
        (S.standardizedResidual n) :=
  S.statistic_eq

/--
Theorem 17.9 source: random partitions settling to fixed cells give the same
modified Pearson statistic up to `o_P(1)`.
-/
structure Vaart1998Theorem17_9RandomPartitionSource
    {Omega Cell : Type*} [Fintype Cell] where
  /-- Random partition cells. -/
  randomCells : Nat -> Cell -> Set Omega
  /-- Fixed limiting cells. -/
  fixedCells : Cell -> Set Omega
  /-- Random-cell statistic. -/
  randomPartitionStatistic : Nat -> Real
  /-- Fixed-cell statistic. -/
  fixedPartitionStatistic : Nat -> Real
  /-- Donsker-class source. -/
  donskerClassSource : Prop
  /-- Symmetric-difference convergence source. -/
  symmetricDifferenceConvergence : Prop
  /-- Root-n consistency of the parameter estimator. -/
  estimatorRootNConsistent : Prop
  /-- Differentiability of the model map into `ell_infty(C)`. -/
  modelMapDifferentiable : Prop
  /-- Asymptotic equivalence of random and fixed partition statistics. -/
  random_eq_fixed_op : Prop
  /-- Source proof of the Donsker-class input. -/
  donskerClassSource_proof :
    donskerClassSource
  /-- Source proof of symmetric-difference convergence. -/
  symmetricDifferenceConvergence_proof :
    symmetricDifferenceConvergence
  /-- Source proof of root-n consistency. -/
  estimatorRootNConsistent_proof :
    estimatorRootNConsistent
  /-- Source proof of differentiability. -/
  modelMapDifferentiable_proof :
    modelMapDifferentiable
  /-- Source proof of random/fixed statistic equivalence. -/
  random_eq_fixed_op_proof :
    random_eq_fixed_op

/--
Theorem 17.9 random/fixed partition equivalence conclusion.
-/
theorem Vaart1998Theorem17_9RandomPartitionSource.random_eq_fixed
    {Omega Cell : Type*} [Fintype Cell]
    (S : Vaart1998Theorem17_9RandomPartitionSource
      (Omega := Omega) (Cell := Cell)) :
    S.random_eq_fixed_op :=
  S.random_eq_fixed_op_proof

/--
Watson-Roy statistic with fixed null cell probabilities and random cells.
-/
def vaart1998_watsonRoyStatistic
    {Cell : Type*} [Fintype Cell]
    (sampleSize : Real) (randomCellEmpiricalProbability nullProbability :
      Cell -> Real) : Real :=
  ∑ i,
    sampleSize *
      (randomCellEmpiricalProbability i - nullProbability i) ^ 2 /
        nullProbability i

/--
Example 17.10 source: in a location-scale model with transformed cells, the
estimated location and scale cancel from the null probabilities.
-/
structure Vaart1998Example17_10LocationScaleRandomPartitionSource
    {Cell : Type*} [Fintype Cell] where
  /-- Fixed cell probabilities under the reference distribution. -/
  fixedNullProbability : Cell -> Real
  /-- Random-cell empirical probabilities. -/
  randomCellEmpiricalProbability : Nat -> Cell -> Real
  /-- Watson-Roy statistic. -/
  statistic : Nat -> Real
  /-- Location-scale partition source. -/
  locationScalePartitionSource : Prop
  /-- Cancellation of estimated parameters in the null probabilities. -/
  nullProbabilityCancellation : Prop
  /-- Statistic display. -/
  statistic_eq :
    statistic =
      fun n =>
        vaart1998_watsonRoyStatistic
          1 (randomCellEmpiricalProbability n) fixedNullProbability
  /-- Source proof of the location-scale partition construction. -/
  locationScalePartitionSource_proof :
    locationScalePartitionSource
  /-- Source proof of null-probability cancellation. -/
  nullProbabilityCancellation_proof :
    nullProbabilityCancellation

/--
Example 17.10 Watson-Roy statistic display.
-/
theorem Vaart1998Example17_10LocationScaleRandomPartitionSource.statistic_display
    {Cell : Type*} [Fintype Cell]
    (S : Vaart1998Example17_10LocationScaleRandomPartitionSource
      (Cell := Cell)) :
    S.statistic =
      fun n =>
        vaart1998_watsonRoyStatistic
          1 (S.randomCellEmpiricalProbability n) S.fixedNullProbability :=
  S.statistic_eq

/--
Section 17.6 source: Sanov's theorem gives Bahadur slopes for Pearson and
likelihood-ratio multinomial tests, and the likelihood-ratio slope dominates.
-/
structure Vaart1998Section17_6BahadurEfficiencySource
    {Cell : Type*} [Fintype Cell] where
  /-- Null probability vector. -/
  nullProbability : Cell -> Real
  /-- Alternative probability vector. -/
  alternativeProbability : Cell -> Real
  /-- Pearson Bahadur slope. -/
  pearsonSlope : Real
  /-- Likelihood-ratio Bahadur slope. -/
  likelihoodRatioSlope : Real
  /-- Sanov source for empirical measures. -/
  sanovSource : Prop
  /-- Continuity/regularity of the level sets. -/
  levelSetRegularity : Prop
  /-- Pearson slope display. -/
  pearsonSlope_eq :
    pearsonSlope =
      vaart1998_pearsonBahadurSlope
        nullProbability alternativeProbability
  /-- Likelihood-ratio slope display. -/
  likelihoodRatioSlope_eq :
    likelihoodRatioSlope =
      vaart1998_likelihoodRatioDiscreteBahadurSlope
        alternativeProbability nullProbability
  /-- Likelihood-ratio slope dominates Pearson slope. -/
  pearsonSlope_le_likelihoodRatioSlope :
    pearsonSlope <= likelihoodRatioSlope
  /-- Source proof of Sanov input. -/
  sanovSource_proof :
    sanovSource
  /-- Source proof of level-set regularity. -/
  levelSetRegularity_proof :
    levelSetRegularity

/--
Section 17.6 Pearson Bahadur slope display.
-/
theorem Vaart1998Section17_6BahadurEfficiencySource.pearson_slope_display
    {Cell : Type*} [Fintype Cell]
    (S : Vaart1998Section17_6BahadurEfficiencySource (Cell := Cell)) :
    S.pearsonSlope =
      vaart1998_pearsonBahadurSlope
        S.nullProbability S.alternativeProbability :=
  S.pearsonSlope_eq

/--
Section 17.6 likelihood-ratio Bahadur slope display.
-/
theorem Vaart1998Section17_6BahadurEfficiencySource.likelihood_ratio_slope_display
    {Cell : Type*} [Fintype Cell]
    (S : Vaart1998Section17_6BahadurEfficiencySource (Cell := Cell)) :
    S.likelihoodRatioSlope =
      vaart1998_likelihoodRatioDiscreteBahadurSlope
        S.alternativeProbability S.nullProbability :=
  S.likelihoodRatioSlope_eq

/--
Section 17.6 likelihood-ratio slope dominance.
-/
theorem Vaart1998Section17_6BahadurEfficiencySource.pearson_slope_le_likelihood_ratio_slope
    {Cell : Type*} [Fintype Cell]
    (S : Vaart1998Section17_6BahadurEfficiencySource (Cell := Cell)) :
    S.pearsonSlope <= S.likelihoodRatioSlope :=
  S.pearsonSlope_le_likelihoodRatioSlope

end AsymptoticStatistics
end StatInference
